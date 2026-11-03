"""Requirements, category targets, coverage and the stop rule."""
import re

from qtc_kg import page_entities, search
from qtc_text import (PREVENTION_RE, REQUIRES_PREVENTION_RE, WEAK_PREVENTION_RE, content_tokens, is_negative,
                      norm_label, tokens)

CATEGORIES = ["Positive", "Negative", "Edge", "Regression", "Integration", "Security", "Accessibility"]
BASE_WEIGHTS = {"Positive": .35, "Negative": .25, "Edge": .15, "Regression": .10,
                "Integration": .10, "Security": 0.0, "Accessibility": .05}
# Ticket shape → extra weight. A ticket can have several shapes.
SHAPES = {
    "security": (r"\b(auth\w*|log ?in|sign ?in|password|permission|role|token|session|access|sso|mfa|2fa)\b",
                 {"Security": .12, "Negative": .05}),
    "api": (r"\b(api|endpoint|request|response|webhook|integration|sync\w*|import|export)\b", {"Integration": .08}),
    "form": (r"\b(form|field|input|validat\w*|required|format|max(imum)?|min(imum)?|length)\b",
             {"Negative": .05, "Edge": .06}),
    "ui": (r"\b(button|modal|dialog|screen|layout|sidebar|menu|tab|responsive|mobile)\b", {"Accessibility": .05}),
    "money": (r"\b(payment|checkout|invoice|refund|price|billing|card|currency)\b",
              {"Negative": .05, "Security": .05, "Edge": .05}),
}

BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)]|\[[ xX]\]|AC\s*\d+\s*[:.)-]?)\s*")
SCENARIO_RE = re.compile(r"^\s*(case|scenario|example|flow)\s*\d*\s*:", re.I)
GWT_START_RE = re.compile(r"^\s*given\b", re.I)
GWT_CONT_RE = re.compile(r"^\s*(when|then|and|but)\b", re.I)
IMPL_RE = re.compile(r"(->|=>|`|\w\(\)|^use\s+\S+$|\bprops?\b|\bfeature flag\b)", re.I)
OPTIONAL_RE = re.compile(r"\b(optional(ly)?|nice to have|if possible|could|may)\b|\(optional\)", re.I)
AMBIGUOUS_RE = re.compile(r"\b(etc|appropriate(ly)?|as needed|tbd|tbc|user[- ]friendly|fast|quickly|properly|"
                          r"correctly|reasonable|intuitive|seamless(ly)?)\b|\?\s*$", re.I)
CLAIM_RE = re.compile(r"\b(should|must|shall|will|can|cannot|can't|able to|allow\w*|display\w*|show\w*)\b", re.I)


def build_requirements(ticket: dict) -> list:
    """Atomic obligations from the acceptance criteria, or claim-like description lines."""
    ac = str(ticket.get("acceptanceCriteria") or "")
    lines = ac.splitlines() if ac.strip() else [
        ln for ln in str(ticket.get("description") or "").splitlines()
        if CLAIM_RE.search(ln) or GWT_START_RE.match(ln) or GWT_CONT_RE.match(ln)]
    items = []
    for raw in lines:
        text = BULLET_RE.sub("", raw).strip()
        if not text:
            continue
        if GWT_CONT_RE.match(text) and items and items[-1].lower().startswith("given"):
            items[-1] += " " + text  # keep one Given/When/Then scenario together
        else:
            items.append(text)
    reqs = []
    for i, text in enumerate(items, 1):
        if SCENARIO_RE.match(text):
            status = "scenario_header"
        elif IMPL_RE.search(text):
            status = "implementation_note"
        elif OPTIONAL_RE.search(text):
            status = "optional"
        else:
            status = "mandatory"
        reqs.append({"id": f"R{i:02d}", "text": text, "status": status,
                     "negative": is_negative(text), "ambiguous": bool(AMBIGUOUS_RE.search(text))})
    return reqs


def derive_targets(ticket: dict, count: int, only=None) -> dict:
    text = " ".join(str(ticket.get(k) or "") for k in ("summary", "description", "acceptanceCriteria")).lower()
    weights, shapes = dict(BASE_WEIGHTS), []
    for shape, (pattern, extra) in SHAPES.items():
        if re.search(pattern, text):
            shapes.append(shape)
            for cat, w in extra.items():
                weights[cat] += w
    if only:
        weights = {c: (w or .05) for c, w in weights.items() if c in only}
    total = sum(weights.values()) or 1.0
    raw = {c: count * w / total for c, w in weights.items() if w > 0}
    targets = {c: int(v) for c, v in raw.items()}
    for c in sorted(raw, key=lambda c: raw[c] - int(raw[c]), reverse=True)[: count - sum(targets.values())]:
        targets[c] += 1  # largest remainder, so targets sum to count exactly
    return {"shapes": shapes, "targets": {c: n for c, n in targets.items() if n > 0}}


def test_text(t: dict) -> str:
    steps = " ".join(t.get("steps") or [])
    return " ".join([t.get("title", ""), t.get("preconditions", ""), steps, t.get("expected_result", "")])


def distinctive_words(reqs: list) -> dict:
    """Per requirement, the words no other requirement uses ("role" in "...choose a role...")."""
    words = {r["id"]: set(content_tokens(r["text"])) for r in reqs}
    return {rid: w - set().union(*(o for oid, o in words.items() if oid != rid)) for rid, w in words.items()}


def coverage_of(req: dict, t: dict, distinct=None) -> str:
    """'covers' | 'contradicts' | ''.

    Undeclared: half the requirement's words and a third of its distinctive words, so a test
    sharing only "invite admin user" does not cover "admin can choose a role". Declared in
    requirementIds: a quarter is enough. A contradiction needs a declared id or a 75% match, so a
    positive admin test does not "contradict" a negative viewer rule because both say "invite".
    """
    rt = set(content_tokens(req["text"]))
    if not rt:
        return ""
    tt = set(content_tokens(test_text(t)))
    declared = req["id"] in (t.get("requirementIds") or [])
    hit = len(rt & tt) / len(rt)
    if hit < (0.25 if declared else 0.5):
        return ""
    if not declared and distinct and len(distinct & tt) / len(distinct) < 1 / 3:
        return ""  # one incidental word ("dialog") is not evidence of the criterion
    claim = t.get("title", "") + " " + t.get("expected_result", "")
    agrees = polarity_agrees(req, claim)
    if agrees is None:
        return ""  # e.g. only "an error is shown" for a "cannot" rule: neither proof nor contradiction
    if not agrees:
        return "contradicts" if declared or hit >= 0.75 else ""
    return "covers"


def polarity_agrees(req: dict, claim: str):
    """True / False / None (undecided).

    "Cannot" criterion: met by a negation or a prevented state ("the button is disabled"); an error
    message alone is undecided. "Must" criterion: contradicted by a negation, or by a prevented state
    the criterion does not itself ask for ("Send invites is disabled" vs "admins can invite").
    """
    neg, prevented = is_negative(claim), bool(PREVENTION_RE.search(claim))
    if req["negative"]:
        if neg or prevented:
            return True
        return None if WEAK_PREVENTION_RE.search(claim) else False
    if neg:
        return False
    return not prevented or bool(REQUIRES_PREVENTION_RE.search(req["text"]))


def coverage(state: dict, kg: dict) -> dict:
    accepted, reqs = state["accepted"], state["requirements"]
    mandatory = [r for r in reqs if r["status"] == "mandatory"]
    distinct = distinctive_words(mandatory)
    per_req, outstanding = [], []
    for r in mandatory:
        verdicts = {t["id"]: coverage_of(r, t, distinct[r["id"]]) for t in accepted}
        covers = [i for i, v in verdicts.items() if v == "covers"]
        against = [i for i, v in verdicts.items() if v == "contradicts"]
        per_req.append({"id": r["id"], "coveredBy": covers, "contradictedBy": against})
        if not covers or against:
            outstanding.append({"id": r["id"], "text": r["text"], "negative": r["negative"],
                                "problem": "contradicted" if against else "uncovered"})
    feature = feature_coverage(state, kg)
    counts = {c: sum(1 for t in accepted if t["category"] == c) for c in CATEGORIES}
    stop = stop_rule(state, outstanding, feature)
    return {"acCoverage": {"covered": len(mandatory) - len(outstanding), "total": len(mandatory),
                           "perRequirement": per_req},
            "outstandingObligations": outstanding, "featureCoverage": feature,
            "categoryCounts": {c: n for c, n in counts.items() if n or c in state["targets"]},
            "targets": state["targets"], "accepted": len(accepted), "budget": state["count"],
            "steps": state["steps"], "maxSteps": state["maxSteps"], "stop": stop,
            "recommendedNext": None if stop["stop"] else recommend(state, outstanding, feature, counts)}


def feature_coverage(state: dict, kg: dict) -> dict:
    """Share of the entities on the ticket's most relevant pages that some accepted test references."""
    if not kg.get("pages"):
        return {"percent": None, "note": "no crawl - feature coverage not measurable", "gaps": []}
    query = " ".join(str(state["ticket"].get(k) or "") for k in ("summary", "acceptanceCriteria", "description"))
    pages = search(kg, query, 3) or [dict(page_entities(kg["pages"][0]), url=kg["pages"][0]["url"])]
    entities = []
    for p in pages:
        entities += [("api", a) for a in p["apis"]] + [("field", f) for f in p["fields"][:15]] + \
                    [("control", c) for c in p["controls"][:15]]
    referenced = {norm_label(r) for t in state["accepted"] for r in t.get("_refs", [])}
    gaps = [f"{kind}: {label}" for kind, label in entities if norm_label(label) not in referenced]
    total = len(entities)
    pct = round(100 * (total - len(gaps)) / total) if total else None
    return {"percent": pct, "target": state["coverageTarget"], "pages": [p["url"] for p in pages], "gaps": gaps[:8]}


def stop_rule(state: dict, outstanding: list, feature: dict) -> dict:
    n = len(state["accepted"])
    if n >= state["count"]:
        return {"stop": True, "reason": f"test budget reached ({n})"}
    if state["steps"] >= state["maxSteps"]:
        return {"stop": True, "reason": f"step budget exhausted ({state['steps']} proposals)"}
    if state["zeroStreak"] >= 3:
        return {"stop": True, "reason": "stalled: last 3 proposals accepted nothing"}
    if outstanding:
        return {"stop": False, "reason": f"{len(outstanding)} acceptance criteria uncovered or contradicted"}
    pct = feature.get("percent")
    if pct is None or pct >= state["coverageTarget"]:
        return {"stop": True, "reason": "every mandatory criterion covered" +
                ("" if pct is None else f" and feature coverage {pct}% >= {state['coverageTarget']}%")}
    return {"stop": False, "reason": f"feature coverage {pct}% < target {state['coverageTarget']}%"}


def recommend(state: dict, outstanding: list, feature: dict, counts: dict) -> dict:
    if outstanding:
        r = outstanding[0]
        return {"action": "propose", "category": "Negative" if r["negative"] else "Positive",
                "focus": r["text"], "requirementId": r["id"], "why": f"{r['id']} is {r['problem']}"}
    under = sorted(state["targets"], key=lambda c: counts.get(c, 0) - state["targets"][c])
    category = under[0] if under else "Edge"
    gap = (feature.get("gaps") or [""])[0]
    return {"action": "propose", "category": category, "focus": gap or f"more {category} coverage",
            "why": "feature coverage below target" if gap else "category under target"}
