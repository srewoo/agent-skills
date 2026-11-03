#!/usr/bin/env python3
"""Deterministic half of ticket-to-test-cases: the agent authors tests, this gates and measures them.

Usage (every command prints one JSON object; --run DIR holds the state of one ticket):
  qtc.py kg-add   --kg KG --page page.json [--requests requests.txt|har.json] [--url KEY] [--all-origins]
  qtc.py kg-show  --kg KG
  qtc.py init     --run DIR --ticket ticket.json [--kg KG] [--count 30] [--coverage-target 80]
                  [--categories Positive,Negative,...] [--force]
  qtc.py search   --run DIR --query "feature words" [--topk 5]
  qtc.py inspect  --run DIR (--field LABEL | --control LABEL | --api "POST /path" | --route /path)
  qtc.py history  --run DIR issues.json
  qtc.py propose  --run DIR batch.json [--category C] [--focus "gap"]
  qtc.py coverage --run DIR
  qtc.py finalize --run DIR [--verdicts verdicts.json] [--strict]

Exit code 0 on success, 2 on bad input. Stdlib only (Python 3.9+). No network access.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qtc_gate as gate  # noqa: E402
import qtc_kg as kgm  # noqa: E402
import qtc_plan as plan  # noqa: E402
import qtc_report as report  # noqa: E402
from qtc_text import tokens  # noqa: E402

DEDUP, RELEVANCE = 0.68, 0.25
HELP = {
    "kg-add": "Merge one extracted page (and optionally its network requests) into the knowledge graph.",
    "kg-show": "List the crawled pages with their form, button, link and API counts.",
    "init": "Start a run for one ticket: requirements, category targets and grounding context.",
    "search": "Find the crawled pages most relevant to some words, with their fields, controls and APIs.",
    "inspect": "Check whether one field, control, API or route exists in the crawl.",
    "history": "Store past issues so Regression tests can cite them.",
    "propose": "Gate a batch of candidate tests: schema, grounding, relevance, duplicates, polarity, budget.",
    "coverage": "Acceptance-criteria and feature coverage, the stop verdict and the recommended next step.",
    "finalize": "Apply assertion verdicts and write test-cases.json and test-cases.md.",
}


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise SystemExit(_fail(f"cannot read JSON from {path}: {exc}"))


def _fail(msg):
    print(json.dumps({"error": msg}), file=sys.stderr)
    return 2


def load_state(run):
    p = Path(run) / "state.json"
    if not p.exists():
        raise SystemExit(_fail(f"no run at {run}; call init first"))
    return json.loads(p.read_text())


def save_state(run, state):
    Path(run).mkdir(parents=True, exist_ok=True)
    (Path(run) / "state.json").write_text(json.dumps(state, indent=2))


def ticket_text(t):
    return " ".join(str(t.get(k) or "") for k in ("summary", "description", "acceptanceCriteria"))


def cmd_kg_add(a):
    kg = kgm.load(a.kg)
    requests = Path(a.requests).read_text() if a.requests else ""
    page = read_json(a.page)
    if a.url:  # one URL, several states (steps of a dialog): record each under its own key
        page["url"] = a.url
    try:
        out = kgm.add_page(kg, page, requests, a.all_origins)
    except ValueError as exc:
        raise SystemExit(_fail(str(exc)))
    Path(a.kg).parent.mkdir(parents=True, exist_ok=True)
    Path(a.kg).write_text(json.dumps(kg, indent=2))
    return out


def cmd_kg_show(a):
    kg = kgm.load(a.kg)
    return {"appUrl": kg.get("appUrl"), "pages": [kgm.summarize(p) for p in kg["pages"]]}


def cmd_init(a):
    if (Path(a.run) / "state.json").exists() and not a.force:
        raise SystemExit(_fail(f"{a.run} already has a run; pass --force to start over (accepted tests are lost)"))
    ticket = read_json(a.ticket)
    kg = kgm.load(a.kg) if a.kg else {"pages": []}
    only = [c.strip() for c in a.categories.split(",")] if a.categories else None
    shape = plan.derive_targets(ticket, a.count, only)
    reqs = plan.build_requirements(ticket)
    state = {"ticket": ticket, "kgPath": str(Path(a.kg).resolve()) if a.kg else None, "count": a.count,
             "coverageTarget": a.coverage_target, "targets": shape["targets"], "requirements": reqs,
             "accepted": [], "rejected": [], "history": [], "steps": 0, "zeroStreak": 0,
             "maxSteps": max(8, a.count // 3 + 4)}
    save_state(a.run, state)
    degradations = []
    if not kg["pages"]:
        degradations.append("No crawl: grounding is off, tests are specification-level and marked unverified.")
    if not any(r["status"] == "mandatory" for r in reqs):
        degradations.append("No acceptance criteria found: coverage is judged against the description only.")
    return {"run": a.run, "shapes": shape["shapes"], "targets": shape["targets"], "requirements": reqs,
            "groundingContext": kgm.grounding_context(kg, ticket_text(ticket)) if kg["pages"] else "",
            "maxSteps": state["maxSteps"], "degradations": degradations}


def _kg(state):
    return kgm.load(state["kgPath"]) if state.get("kgPath") else {"pages": []}


def cmd_search(a):
    return {"pages": kgm.search(_kg(load_state(a.run)), a.query, a.topk)}


def cmd_inspect(a):
    idx = kgm.index(_kg(load_state(a.run)))
    kind, label = next((k, v) for k, v in (("fields", a.field), ("controls", a.control),
                                           ("apis", a.api), ("routes", a.route)) if v)
    how, real = kgm.lookup(idx, kind, label)
    return {"query": label, "kind": kind, "exists": bool(how), "match": real, "how": how}


def cmd_history(a):
    state = load_state(a.run)
    issues = read_json(a.file)
    state["history"] = [{"key": i.get("key"), "summary": i.get("summary", "")} for i in issues if i.get("key")]
    save_state(a.run, state)
    return {"stored": len(state["history"])}


def cmd_propose(a):
    state = load_state(a.run)
    kg = _kg(state)
    batch = read_json(a.file)
    if not isinstance(batch, list):
        raise SystemExit(_fail("batch must be a JSON array of test objects"))
    idx = kgm.index(kg)
    tt = ticket_text(state["ticket"])
    host = urlsplit(kg.get("appUrl") or (kg["pages"][0]["url"] if kg["pages"] else "")).netloc
    # Past issues are on-topic too: a Regression test is about the bug it guards.
    ticket_vocab = set(tokens(tt + " " + " ".join(h["summary"] for h in state["history"])))
    app_vocab = set(tokens(kgm.grounding_context(kg, tt))) if kg["pages"] else set()
    known = {h["key"] for h in state["history"]}
    results = []
    for c in batch:
        t, err = gate.normalise(c, a.category)
        if len(state["accepted"]) >= state["count"]:
            err = err or f"test budget of {state['count']} reached; drop weaker tests or start over with a larger --count"
            verdict = {"title": t and t["title"], "status": "rejected", "stage": "budget", "reason": err}
        else:
            verdict = _judge(t, err, state, idx, tt, host, ticket_vocab, app_vocab, known)
        results.append(verdict)
        if verdict["status"] == "accepted":
            state["accepted"].append(t)
        else:
            state["rejected"].append({"title": (c or {}).get("title") if isinstance(c, dict) else None,
                                      "stage": verdict["stage"], "reason": verdict["reason"]})
    accepted = sum(r["status"] == "accepted" for r in results)
    state["steps"] += 1
    state["zeroStreak"] = 0 if accepted else state["zeroStreak"] + 1
    save_state(a.run, state)
    reasons = {}
    for r in results:
        if r["status"] == "rejected":
            reasons[r["stage"]] = reasons.get(r["stage"], 0) + 1
    return {"proposed": len(batch), "accepted": accepted, "rejected": len(batch) - accepted,
            "rejectReasons": reasons, "focus": a.focus, "results": results, "totalAccepted": len(state["accepted"])}


def _judge(t, err, state, idx, tt, host, ticket_vocab, app_vocab, known):
    if err:
        return {"title": None, "status": "rejected", "stage": "schema", "reason": err}
    out = {"title": t["title"]}
    if t["category"] == "Regression":
        ref = t.get("historicalReference")
        if not ref and not t.get("rationale"):
            return dict(out, status="rejected", stage="schema",
                        reason="Regression tests need historicalReference or rationale")
        if ref and ref not in known:
            why = "is not in the stored history" if known else "cannot be checked: store past issues with `history` first"
            return dict(out, status="rejected", stage="grounding", reason=f"{ref} {why}")
    g = gate.ground(t, idx, tt, host)
    if not g["ok"]:
        return dict(out, status="rejected", stage="grounding", reason=g["reason"])
    score = gate.relevance(t, ticket_vocab, app_vocab)
    if score < RELEVANCE:
        return dict(out, status="rejected", stage="relevance", reason=f"relevance {score} < {RELEVANCE}: off-ticket")
    dup, sim = gate.duplicate_of(t, state["accepted"], DEDUP)
    if dup:
        return dict(out, status="rejected", stage="duplicate", reason=f"duplicates {dup} (similarity {sim})")
    reqs = {r["id"]: r for r in state["requirements"]}
    for rid in t["requirementIds"]:
        if rid in reqs and plan.coverage_of(reqs[rid], t) == "contradicts":
            want = "forbids" if reqs[rid]["negative"] else "requires"
            return dict(out, status="rejected", stage="polarity",
                        reason=f"{rid} {want} this behaviour but the test asserts the opposite: \"{reqs[rid]['text']}\"")
    warnings = gate.assertion_warnings(t, tt, idx)
    for r in state["requirements"]:  # an undeclared but unmistakable contradiction: accept, but say so now
        if r["status"] == "mandatory" and r["id"] not in t["requirementIds"] and plan.coverage_of(r, t) == "contradicts":
            warnings.append(f'contradicts {r["id"]} ("{r["text"]}") - fix the polarity or declare a different id')
    t.update(id=f"T-{len(state['accepted']) + 1:02d}", _grounding=g["status"], _refs=g["refs"],
             _relevance=score, _repairs=g["repairs"], _specification=g.get("specification", []),
             _warnings=warnings)
    return dict(out, status="accepted", id=t["id"], grounding=g["status"], repaired=bool(g["repairs"]),
                repairs=g["repairs"], relevance=score, warnings=warnings)


def cmd_coverage(a):
    state = load_state(a.run)
    return plan.coverage(state, _kg(state))


def cmd_finalize(a):
    state = load_state(a.run)
    verdicts = read_json(a.verdicts).get("verdicts", []) if a.verdicts else []
    kept, dropped = report.apply_verdicts([dict(t) for t in state["accepted"]], verdicts, a.strict)
    # Coverage of the suite actually delivered, not of everything ever accepted.
    final = dict(state, accepted=kept)
    return report.finalize(a.run, final, plan.coverage(final, _kg(state)), dropped)


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("kg-add", help=HELP["kg-add"], description=HELP["kg-add"])
    s.add_argument("--kg", required=True)
    s.add_argument("--page", required=True)
    s.add_argument("--requests")
    s.add_argument("--url", help="key to record the page under, e.g. https://app/x#invite-step-2")
    s.add_argument("--all-origins", action="store_true", help="keep API calls to other hosts")
    sub.add_parser("kg-show", help=HELP["kg-show"], description=HELP["kg-show"]).add_argument("--kg", required=True)
    s = sub.add_parser("init", help=HELP["init"], description=HELP["init"])
    s.add_argument("--run", required=True)
    s.add_argument("--ticket", required=True)
    s.add_argument("--kg")
    s.add_argument("--count", type=int, default=30)
    s.add_argument("--coverage-target", type=int, default=80)
    s.add_argument("--categories", help="comma-separated subset of the seven categories")
    s.add_argument("--force", action="store_true", help="replace an existing run in --run")
    for name in ("search", "inspect", "history", "propose", "coverage", "finalize"):
        s = sub.add_parser(name, help=HELP[name], description=HELP[name])
        s.add_argument("--run", required=True)
        if name == "search":
            s.add_argument("--query", required=True)
            s.add_argument("--topk", type=int, default=5)
        if name == "inspect":
            g = s.add_mutually_exclusive_group(required=True)
            for opt in ("--field", "--control", "--api", "--route"):
                g.add_argument(opt)
        if name in ("history", "propose"):
            s.add_argument("file")
        if name == "propose":
            s.add_argument("--category")
            s.add_argument("--focus", default="")
        if name == "finalize":
            s.add_argument("--verdicts")
            s.add_argument("--strict", action="store_true")
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    out = globals()["cmd_" + a.cmd.replace("-", "_")](a)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
