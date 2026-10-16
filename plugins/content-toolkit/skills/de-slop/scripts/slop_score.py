#!/usr/bin/env python3
"""Count AI-writing tells in a draft and report a 0-100 density score.

Usage:
  python3 slop_score.py draft.md          # human-readable report
  cat draft.md | python3 slop_score.py -  # read stdin
  python3 slop_score.py draft.md --json   # machine-readable

Score = weighted tells per 100 words x 20, capped at 100.
  0-15 clean | 16-40 some tells | 41-70 heavy | 71-100 saturated.
A hit is a candidate, not proof: "leverage" in a finance piece is correct.
Em dashes, bold and "X, Y and Z" triads score only above a density threshold;
the first question-opener paragraph is free.
Standard library only; Python 3.9+. Fenced code blocks and `inline code` are skipped.
"""
import argparse
import json
import re
import statistics
import sys

# (category, weight, regex). Matched case-insensitively, line by line.
PATTERNS = [
    ("vocabulary", 1.0, r"\bdelv(e|es|ed|ing)\b"),
    ("vocabulary", 1.0, r"\btapestr(y|ies)\b"),
    ("vocabulary", 1.0, r"\b(a|is a|stands as a) testament to\b"),
    ("vocabulary", 1.0, r"\bnavigat(e|es|ing) the [\w\s-]{0,20}(landscape|waters|complexities|world)\b"),
    ("vocabulary", 0.5, r"\b(ever-evolving|ever-changing|evolving|digital|business|competitive) landscape\b"),
    ("vocabulary", 1.0, r"\bleverag(e|es|ed|ing)\b"),
    ("vocabulary", 1.0, r"\brobust\b(?!\s+(against|to|regression|estimat\w*|statistics?|standard errors?|optimi[sz]ation|control))"),
    ("vocabulary", 1.0, r"\bseamless(ly)?\b"),
    # Narrowed to the marketing sense: "elevated privileges", "unlock the device" are not tells.
    ("vocabulary", 1.0, r"\belevat(e|es|ed|ing)\b(?!\s+(privileges?|permissions?|access|rights|risks?|levels?|temperatures?|blood|pressure|mode|shell|prompt))"),
    ("vocabulary", 1.0, r"\bunlock(s|ed|ing)?\s+(?:(?:the|your|its|their|our|new|full|hidden|true|real)\s+)*(potential|value|growth|power|insights?|opportunit\w*|success|productivity|revenue|possibilit\w*|levels?|benefits?|secrets?|creativity|innovation)\b"),
    ("vocabulary", 2.0, r"\bin today'?s (fast-paced|ever-changing|digital|modern|rapidly evolving)[\w\s-]{0,15}(world|age|era|landscape)\b"),
    ("vocabulary", 1.0, r"\b(realm|embark(s|ed|ing)?|game-?chang(er|ing)|cutting-edge|pivotal|holistic|synerg(y|ies)|paradigm shift)\b"),
    ("vocabulary", 1.0, r"\b(foster(s|ed|ing)?|underscor(e|es|ed|ing)|showcas(e|es|ed|ing)|empower(s|ed|ing)?)\b"),
    ("vocabulary", 1.0, r"\bharness(es|ed|ing)?\s+(the|its|their|our|your|this)\b"),  # verb only; "test harness" is fine
    ("vocabulary", 1.0, r"\b(revolutioni[sz](e|es|ed|ing)|transformative|meticulous(ly)?|intricate|bustling|vibrant|treasure trove|unparalleled)\b"),
    ("structure", 1.5, r"\b(it'?s|this is|that'?s|it is)\s+not\s+(just|only|merely|about)?\s*[^.?!;]{1,50}[,;:—–]\s*(it'?s|it is|but)\b"),
    ("structure", 1.5, r"\bnot (just|only|merely) [^.?!]{1,50},? but (also )?\b"),
    ("structure", 1.5, r"\b(here'?s the thing|here'?s the kicker|here'?s why|here'?s what|the truth is|let'?s be honest|let'?s face it)\b"),
    ("structure", 1.5, r"\bthe (answer|result|secret|kicker|catch|truth|reality|twist|best part|bottom line)\s*\?"),
    ("structure", 1.0, r"\b(the (answer|secret|key|truth|reality) is simple|the bottom line|spoiler)\s*:"),
    ("structure", 1.5, r"\b(let'?s dive (in|into|deeper)|let'?s (explore|unpack|break (it|this) down)|without further ado|buckle up|in this (article|post|guide|blog),? (we|i)('ll| will)?)\b"),
    ("structure", 1.5, r"^\W*(in conclusion|in summary|to sum (it )?up|all in all|at the end of the day|ultimately,)"),
    ("hedging", 1.0, r"\b(it'?s|it is) (worth|important to) (noting|note|mentioning|remember(ing)?)\b"),
    ("hedging", 1.0, r"\b(arguably|generally speaking|in many ways|to some extent|it can be said|needless to say)\b"),
    ("hedging", 1.0, r"\b(may|might|could) potentially\b"),
    ("hedging", 0.5, r"\b(when it comes to|in order to|the fact that|a (wide|vast|diverse) (range|variety|array) of|a myriad of)\b"),
    ("hedging", 1.0, r"\bplays? an? (crucial|vital|key|pivotal|significant|important) role\b"),
    ("sycophancy", 2.0, r"\b(great question|what a (great|fantastic|wonderful)|you'?re absolutely right|i hope this helps|hope this helps|happy to help|i'?d be (happy|glad) to|feel free to (reach out|ask)|let (me|us) know if you|as an ai)\b"),
    ("sycophancy", 2.0, r"^\W*(absolutely|certainly|of course|sure)!"),
    ("generic-example", 1.0, r"\b(imagine|picture) (a|an|this|that)\b"),
    ("generic-example", 1.0, r"\b(company|business|brand|person|user) [XYZ]\b|\b(john|jane) doe\b|\bacme (corp|inc|co)\b"),  # bare ACME is a protocol
]
COMPILED = [(c, w, re.compile(p, re.IGNORECASE)) for c, w, p in PATTERNS]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅]")
EMOJI_BULLET = re.compile("^\\s*(?:[-*]\\s*)?[\U0001F300-\U0001FAFF☀-➿⭐✅]")
EM_DASH = re.compile("—| -- ")
BOLD = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
TRIAD = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? and [\w'-]+", re.IGNORECASE)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
INLINE_CODE = re.compile(r"`[^`\n]*`")


def strip_code(lines):
    """Yield (line_no, text) for prose lines, skipping fenced code blocks."""
    fenced = False
    for no, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield no, INLINE_CODE.sub("", line)


def rhetorical_openers(prose):
    """Paragraphs whose first sentence is a question."""
    hits, start = [], True
    for no, line in prose:
        text = line.strip()
        if not text:
            start = True
            continue
        if start and not text.startswith(("#", ">", "|")):
            first = SENTENCE_SPLIT.split(text)[0]
            if first.endswith("?") and len(first.split()) >= 4:
                hits.append((no, first[:60]))
        start = False
    return hits


def burstiness(text):
    """Coefficient of variation of sentence length in words (None if < 8 sentences)."""
    flat = re.sub(r"^\s*([-*#>]|\d+\.)\s*", "", text, flags=re.MULTILINE)
    sentences = [s for s in SENTENCE_SPLIT.split(flat.replace("\n", " ")) if len(s.split()) >= 3]
    if len(sentences) < 8:
        return None, len(sentences)
    lengths = [len(s.split()) for s in sentences]
    return statistics.pstdev(lengths) / statistics.mean(lengths), len(sentences)


def analyse(text):
    prose = list(strip_code(text.splitlines()))
    words = sum(len(line.split()) for _, line in prose)
    hits = {}  # category -> list of (line, match)
    points = 0.0

    def add(cat, no, snippet, weight):
        nonlocal points
        hits.setdefault(cat, []).append((no, snippet))
        points += weight

    for no, line in prose:
        for cat, weight, rx in COMPILED:
            for m in rx.finditer(line):
                add(cat, no, m.group(0), weight)
        for m in TRIAD.finditer(line):
            add("rule-of-three", no, m.group(0), 0.0)  # weighted below by density
        if EMOJI_BULLET.match(line):
            add("punctuation", no, "emoji bullet", 1.0)
        for _ in EM_DASH.finditer(line):
            add("punctuation", no, "em dash", 0.0)  # weighted below by density
        for m in BOLD.finditer(line):
            add("punctuation", no, "bold: " + m.group(0)[:30], 0.0)

    # The first question opener is free: one per piece is normal writing.
    for i, (no, snippet) in enumerate(rhetorical_openers(prose)):
        add("structure", no, "question opener: " + snippet, 1.0 if i else 0.0)

    # Em dashes and bold are normal in moderation: score only the excess.
    per100 = max(words, 1) / 100
    dashes = sum(1 for _, s in hits.get("punctuation", []) if s == "em dash")
    bolds = sum(1 for _, s in hits.get("punctuation", []) if s.startswith("bold:"))
    points += max(0.0, dashes - per100 * 0.5)  # >1 per 200 words is excess
    points += max(0.0, bolds - per100 * 1.0) * 0.5  # >1 per 100 words is excess
    triads = len(hits.get("rule-of-three", []))
    points += max(0.0, triads - max(1.0, per100 * 0.5)) * 0.5  # first one free, then >1 per 200 words

    cv, n_sent = burstiness("\n".join(line for _, line in prose))
    flat = cv is not None and cv < 0.35
    if flat:
        points += per100  # adds a flat 20 to the score, whatever the length

    density = points / per100 if words else 0.0
    score = min(100, round(density * 20))
    return {
        "words": words,
        "sentences": n_sent,
        "sentence_length_cv": None if cv is None else round(cv, 2),
        "uniform_sentence_length": flat,
        "emoji_count": len(EMOJI.findall(text)),
        "em_dashes": dashes,
        "bold_spans": bolds,
        "points": round(points, 1),
        "score": score,
        "band": band(score),
        "hits": {k: [{"line": n, "match": s} for n, s in sorted(v, key=lambda h: h[0])] for k, v in sorted(hits.items())},
    }


def band(score):
    if score <= 15:
        return "clean"
    if score <= 40:
        return "some tells"
    if score <= 70:
        return "heavy"
    return "saturated"


def render(r):
    out = [
        "Slop score: %d/100 (%s)" % (r["score"], r["band"]),
        "Words: %d | weighted points: %s | em dashes: %d | bold spans: %d | emoji: %d"
        % (r["words"], r["points"], r["em_dashes"], r["bold_spans"], r["emoji_count"]),
    ]
    if 0 < r["words"] < 150:
        out.append("Short text: one tell moves the score by 13+ points; read the hits, not just the band")
    if r["sentence_length_cv"] is None:
        out.append("Sentence rhythm: too few sentences to judge (%d)" % r["sentences"])
    else:
        out.append("Sentence rhythm: CV %.2f over %d sentences%s" % (
            r["sentence_length_cv"], r["sentences"],
            " -> UNIFORM, vary lengths" if r["uniform_sentence_length"] else " (ok)"))
    for cat, items in r["hits"].items():
        out.append("\n[%s] %d" % (cat, len(items)))
        for h in items:
            out.append("  L%d: %s" % (h["line"], h["match"]))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="path to a text/markdown file, or - for stdin")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a report")
    args = ap.parse_args(argv)
    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as fh:
                text = fh.read()
    except OSError as exc:
        sys.exit("error: cannot read %s: %s" % (args.file, exc))
    result = analyse(text)
    print(json.dumps(result, indent=2) if args.json else render(result))


if __name__ == "__main__":
    main()
