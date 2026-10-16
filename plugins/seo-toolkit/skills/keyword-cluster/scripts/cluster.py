#!/usr/bin/env python3
"""Cluster a keyword export by topic and intent (standard library only).

Input: a CSV/TSV keyword export (Ahrefs, Semrush, Google Search Console, Keyword
Planner, or any file with a keyword column). Header names are matched
case-insensitively; override with --map field=Header.
  keyword   keyword, query, top queries, search term
  volume    volume, search volume, avg. monthly searches, impressions (GSC proxy)
  kd        kd, keyword difficulty, difficulty
  position  position, current position, avg. position, rank
  url       url, current url, ranking url, landing page, page
  intent    intent, intents (the tool's own label; copied to tool_intent at --level keyword)

Methods:
  serp     (--serp FILE, rows of keyword,url[,position]) keywords join a cluster when
           they share >= --min-overlap of their top-10 URLs with the cluster's seed.
  lexical  fallback without SERP data: Jaccard of stemmed tokens (stop/question/modifier
           words removed) >= --threshold (default 0.6), and compatible intent.
Seeds go in descending volume (primary = highest-volume member). Intent is a guess; check the SERP.

Examples:
  python3 cluster.py keywords.csv --serp serp.csv --min-overlap 4 --brand acme --output clusters.csv
  python3 cluster.py gsc_queries.csv --level keyword --output kw_map.csv
"""
import argparse
import csv
import io
import math
import re
import sys
from collections import Counter, defaultdict

ALIASES = {
    "keyword": ["keyword", "keywords", "query", "queries", "top queries", "search term", "search query"],
    "volume": ["volume", "search volume", "avg monthly searches", "monthly searches", "sv", "impressions"],
    "kd": ["kd", "keyword difficulty", "difficulty"],
    "position": ["position", "current position", "pos", "avg position", "average position", "rank"],
    "url": ["url", "current url", "ranking url", "landing page", "page", "top pages", "address"],
    "intent": ["intent", "intents"],  # the tool's own SERP-based label (Semrush, Ahrefs): passed through
}
STOP = set("a an the of for to in on at by with and or from your my our is are be can do does i you it this "
           "that as into about".split())
QUESTION = set("how what why when where who which whose is are can does do should".split())
INTENT_WORDS = [  # checked in this order; first hit wins (after question words)
    ("navigational", {"login", "signin", "portal"}, {"log in", "sign in", "sign up"}),
    ("transactional", {"buy", "price", "prices", "pricing", "cost", "cheap", "discount", "coupon", "deal",
                       "deals", "order", "purchase", "sale", "hire", "quote", "subscription", "trial",
                       "download", "shop", "booking"}, {"near me", "for sale"}),
    ("commercial", {"best", "top", "vs", "versus", "review", "reviews", "compare", "comparison",
                    "alternative", "alternatives", "rated"}, set()),
    ("informational", {"guide", "tutorial", "examples", "example", "ideas", "tips", "meaning",
                       "definition", "define", "learn", "steps"}, set()),
]
# Commercial/informational modifiers don't change the topic ("best crm" ~ "crm"); transactional and
# navigational words do ("crm pricing" is a pricing page, not the "crm" page), so they stay in the tokens.
MODIFIERS = set().union(*(words for label, words, _ in INTENT_WORDS if label in ("commercial", "informational")))


def norm_header(h):
    h = re.sub(r"\(.*?\)", "", h.lower())
    return " ".join(re.findall(r"[a-z0-9]+", h))


def read_table(path):
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        raise SystemExit(f"cannot read {path}: {e.strerror}")
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16")  # Ahrefs offers UTF-16 tab-separated exports
    else:
        text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    keyword_names = set(ALIASES["keyword"])
    # Keyword Planner exports start with title/date lines: begin at the first line that looks like a header
    start = next((i for i, line in enumerate(lines[:10])
                  if any(norm_header(c) in keyword_names for c in re.split(r"[,\t;]", line))), 0)
    body = "\n".join(lines[start:])
    try:
        dialect = csv.Sniffer().sniff(body[:4096], delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(body), dialect=dialect))


def find_columns(headers, overrides):
    lookup = {norm_header(h): h for h in headers}
    cols = {}
    for field, names in ALIASES.items():
        if field in overrides:
            if overrides[field] not in headers:
                raise SystemExit(f"--map {field}={overrides[field]}: no such column. Columns: {headers}")
            cols[field] = overrides[field]
            continue
        cols[field] = next((lookup[n] for n in names if n in lookup), None)
    if not cols["keyword"]:
        raise SystemExit(f"no keyword column found in {headers}; pass --map keyword=<Header>")
    return cols


def number(value):
    """'1,200' -> 1200, '1.2K' -> 1200, '1K - 10K' -> 1000 (lower bound), '' -> None."""
    m = re.search(r"(\d[\d,]*\.?\d*)\s*([kKmM]?)", value or "")
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    return n * {"k": 1e3, "m": 1e6}.get(m.group(2).lower(), 1)


def stem(tok):
    # ponytail: crude plural folding, not a real stemmer; swap in Snowball if a dependency is ever allowed
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def topic_tokens(kw):
    return frozenset(stem(t) for t in re.findall(r"\w+", kw) if t not in STOP | MODIFIERS | QUESTION)


def guess_intent(kw, brands):
    toks = re.findall(r"\w+", kw)
    padded = f" {' '.join(toks)} "
    if toks and toks[0] in QUESTION:
        return "informational"
    for label, words, phrases in INTENT_WORDS:
        if words & set(toks) or any(f" {p} " in padded for p in phrases):
            return label
    # a bare brand query is navigational; "brand pricing" / "brand review" keep their modifier's intent
    return "navigational" if any(f" {b} " in padded for b in brands) else "unclear"


def load_keywords(path, overrides, brands):
    rows = read_table(path)
    if not rows:
        raise SystemExit(f"{path}: no data rows")
    cols = find_columns(list(rows[0].keys()), overrides)
    if not any((r.get(cols["keyword"]) or "").strip() for r in rows):
        raise SystemExit(f"{path}: column {cols['keyword']!r} is empty in every row")
    kws = {}
    for r in rows:
        kw = " ".join((r.get(cols["keyword"]) or "").lower().split())
        if not kw:
            continue
        get = lambda f: number(r.get(cols[f])) if cols[f] else None  # noqa: E731
        k = kws.setdefault(kw, {"keyword": kw, "volume": 0, "kd": None, "position": None, "urls": set(),
                                "tool_intent": (r.get(cols["intent"]) or "").strip() if cols["intent"] else ""})
        k["volume"] = max(k["volume"], get("volume") or 0)
        k["kd"] = get("kd") if k["kd"] is None else k["kd"]
        pos = get("position")
        if pos is not None and (k["position"] is None or pos < k["position"]):
            k["position"] = pos
        if cols["url"] and (r.get(cols["url"]) or "").strip():
            k["urls"].add(r[cols["url"]].strip())
    for k in kws.values():
        k["intent"], k["tokens"] = guess_intent(k["keyword"], brands), topic_tokens(k["keyword"])
    return list(kws.values()), cols


def load_serps(path):
    rows = read_table(path)
    if not rows:
        return {}
    cols = find_columns(list(rows[0].keys()), {})
    if not cols["url"]:
        raise SystemExit(f"{path}: SERP file needs keyword and url columns")
    serps = defaultdict(set)
    for r in rows:
        pos = number(r.get(cols["position"])) if cols["position"] else None
        url = re.sub(r"^https?://(www\.)?", "", (r.get(cols["url"]) or "").strip().lower()).rstrip("/")
        if url and (pos is None or pos <= 10):
            serps[" ".join((r.get(cols["keyword"]) or "").lower().split())].add(url)
    return serps


def compatible(a, b):
    return a == b or "unclear" in (a, b)


def cluster(kws, serps, min_overlap, threshold):
    kws.sort(key=lambda k: (-k["volume"], k["keyword"]))
    clusters, assigned = [], set()
    with_serp = [k for k in kws if serps.get(k["keyword"])]
    by_url = defaultdict(list)
    for k in with_serp:
        for u in serps[k["keyword"]]:
            by_url[u].append(k)
    for seed in with_serp:  # SERP overlap first: the gold standard
        if seed["keyword"] in assigned:
            continue
        top = serps[seed["keyword"]]
        cands = {id(k): k for u in top for k in by_url[u]}.values()
        members = [seed] + sorted((k for k in cands if k is not seed and k["keyword"] not in assigned
                                   and len(top & serps[k["keyword"]]) >= min_overlap),
                                  key=lambda k: (-k["volume"], k["keyword"]))
        assigned.update(k["keyword"] for k in members)
        clusters.append(("serp", members))
    rest = [k for k in kws if k["keyword"] not in assigned]
    index = defaultdict(list)
    for k in rest:
        for t in k["tokens"]:
            index[t].append(k)
    for seed in rest:  # ponytail: greedy, compares each keyword to the seed only, not to the whole cluster
        if seed["keyword"] in assigned:
            continue
        # Prefix filter: Jaccard >= t needs >= ceil(t*|A|) shared tokens, so a match must contain one of the
        # |A| - ceil(t*|A|) + 1 rarest seed tokens. Skips the head term every keyword shares.
        toks = sorted(seed["tokens"], key=lambda t: (len(index[t]), t))
        prefix = toks[:len(toks) - math.ceil(threshold * len(toks)) + 1]
        cands = sorted((k for k in {id(k): k for t in prefix for k in index[t]}.values()
                        if k["keyword"] not in assigned and k is not seed
                        and len(seed["tokens"] & k["tokens"]) / len(seed["tokens"] | k["tokens"]) >= threshold),
                       key=lambda k: (-k["volume"], k["keyword"]))
        members, intent = [seed], seed["intent"]
        assigned.add(seed["keyword"])
        for k in cands:
            if compatible(intent, k["intent"]):
                members.append(k)
                assigned.add(k["keyword"])
                intent = k["intent"] if intent == "unclear" else intent  # first definite intent fixes the cluster
        clusters.append(("lexical", members))
    clusters.sort(key=lambda c: -sum(k["volume"] for k in c[1]))
    return clusters


def fmt(n):
    return "" if n is None else (str(int(n)) if float(n).is_integer() else f"{n:.1f}")


def summarise(cid, method, members):
    intents = Counter(k["intent"] for k in members if k["intent"] != "unclear")
    intent = "unclear" if not intents else (intents.most_common(1)[0][0] if len(intents) == 1 else
                                            "mixed: " + "/".join(sorted(intents)))
    urls = sorted(set().union(*(k["urls"] for k in members)))
    kds = [k["kd"] for k in members if k["kd"] is not None]
    positions = [k["position"] for k in members if k["position"] is not None]
    if len(urls) > 1:
        action = f"CANNIBALISATION CHECK: {len(urls)} URLs rank"
    elif urls:
        action = "map to existing URL"
    else:
        action = "no ranking URL: map manually or new page"
    return {"cluster_id": cid, "primary_keyword": members[0]["keyword"], "keywords": len(members),
            "total_volume": fmt(sum(k["volume"] for k in members)), "intent": intent,
            "avg_kd": fmt(sum(kds) / len(kds)) if kds else "", "best_position": fmt(min(positions)) if positions else "",
            "urls": " | ".join(urls), "action": action, "method": method,
            "members": "; ".join(k["keyword"] for k in members)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keywords", help="CSV/TSV keyword export")
    ap.add_argument("--serp", help="CSV of keyword,url[,position] rows (top-10 results per keyword)")
    ap.add_argument("--min-overlap", type=int, default=3, help="shared top-10 URLs to join a SERP cluster (default 3)")
    ap.add_argument("--threshold", type=float, default=0.6,
                    help="lexical Jaccard threshold 0-1 (default 0.6; 0.5 merges 'mens shoes' with 'trail shoes')")
    ap.add_argument("--brand", action="append", default=[], help="brand term (navigational intent); repeatable")
    ap.add_argument("--map", action="append", default=[], metavar="FIELD=HEADER",
                    help="override column detection, e.g. --map volume='Avg. monthly searches'")
    ap.add_argument("--level", choices=["cluster", "keyword"], default="cluster", help="one row per cluster or keyword")
    ap.add_argument("--output", help="CSV file to write (default stdout)")
    args = ap.parse_args(argv)
    if not 0 < args.threshold <= 1 or args.min_overlap < 1:
        ap.error("--threshold must be in (0, 1] and --min-overlap >= 1")
    if any("=" not in m for m in args.map):
        ap.error("--map takes FIELD=HEADER, e.g. --map volume='Avg. monthly searches'")
    overrides = dict(m.split("=", 1) for m in args.map)
    if set(overrides) - set(ALIASES):
        ap.error(f"--map fields must be among {sorted(ALIASES)}")
    brands = [" ".join(re.findall(r"\w+", b.lower())) for b in args.brand]
    kws, cols = load_keywords(args.keywords, overrides, brands)
    serps = load_serps(args.serp) if args.serp else {}
    clusters = cluster(kws, serps, args.min_overlap, args.threshold)
    if args.level == "cluster":
        rows = [summarise(i, m, members) for i, (m, members) in enumerate(clusters, 1)]
    else:
        rows = [{"keyword": k["keyword"], "cluster_id": i, "primary_keyword": members[0]["keyword"],
                 "volume": fmt(k["volume"]), "kd": fmt(k["kd"]), "position": fmt(k["position"]),
                 "urls": " | ".join(sorted(k["urls"])), "intent_guess": k["intent"], "tool_intent": k["tool_intent"],
                 "method": m}
                for i, (m, members) in enumerate(clusters, 1) for k in members]
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        w = csv.DictWriter(out, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    finally:
        if out is not sys.stdout:
            out.close()
    detected = ", ".join(f"{f}={c!r}" for f, c in cols.items() if c)
    print(f"{len(kws)} keywords -> {len(clusters)} clusters ({len(serps)} with SERP data). Columns: {detected}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
