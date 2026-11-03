"""finalize: apply assertion verdicts, then write test-cases.json and test-cases.md."""
import json
from pathlib import Path

VERDICTS = {"supported", "contradictory", "unverifiable", "unknown"}


def apply_verdicts(tests: list, verdicts: list, strict: bool):
    by_id = {t["id"]: t for t in tests}
    for v in verdicts:
        t = by_id.get(v.get("id")) or (tests[v["i"]] if isinstance(v.get("i"), int) and v["i"] < len(tests) else None)
        if t and v.get("verdict") in VERDICTS:
            t["_assertion"] = v["verdict"]
            if v.get("issue"):
                t["_assertionIssue"] = v["issue"]
    dropped = [t["id"] for t in tests if strict and t.get("_assertion") == "contradictory"]
    return [t for t in tests if t["id"] not in dropped], dropped


def caveats(state: dict, cov: dict, tests: list) -> list:
    out = []
    if not state.get("kgPath"):
        out.append("No crawl: every test is specification-level (grounding: unverified). Execute against the app "
                   "before trusting UI labels.")
    for o in cov["outstandingObligations"]:
        out.append(f'{o["id"]} {o["problem"]}: "{o["text"]}"')
    out += [f'{t["id"]} {w} - confirm it or soften the assertion' for t in tests for w in t.get("_warnings", [])]
    spec = sorted({s for t in tests for s in t.get("_specification", [])})
    if spec:
        out.append("Referenced but not in the app yet (taken from the ticket): " + ", ".join(spec))
    pct = cov["featureCoverage"].get("percent")
    if pct is not None and pct < state["coverageTarget"]:
        out.append(f"Feature coverage {pct}% is below the {state['coverageTarget']}% target.")
    if cov["stop"]["reason"].startswith(("stalled", "step budget")):
        out.append("Generation stopped early: " + cov["stop"]["reason"])
    return out


def clarifications(state: dict, tests: list) -> list:
    out = [f'{r["id"]} is ambiguous - what exactly counts as passing? "{r["text"]}"'
           for r in state["requirements"] if r["status"] == "mandatory" and r["ambiguous"]]
    out += [f'{r["id"]} is optional - in scope for this release? "{r["text"]}"'
            for r in state["requirements"] if r["status"] == "optional"]
    out += [f'{t["id"]} assertion is {t["_assertion"]}: {t.get("_assertionIssue", "")}'.rstrip(": ")
            for t in tests if t.get("_assertion") in ("contradictory", "unverifiable")]
    return out


def finalize(run: str, state: dict, cov: dict, dropped: list) -> dict:
    tests = state["accepted"]
    by_cat = {}
    for t in tests:
        by_cat[t["category"]] = by_cat.get(t["category"], 0) + 1
    rejected = {}
    for r in state["rejected"]:
        rejected[r["stage"]] = rejected.get(r["stage"], 0) + 1
    doc = {"ticket": {k: state["ticket"].get(k) for k in ("key", "summary")},
           "testCases": tests, "byCategory": by_cat, "droppedContradictory": dropped,
           "coverage": {"acceptanceCriteria": f'{cov["acCoverage"]["covered"]}/{cov["acCoverage"]["total"]}',
                        "feature": cov["featureCoverage"], "perRequirement": cov["acCoverage"]["perRequirement"]},
           "requirements": state["requirements"], "stopReason": cov["stop"]["reason"],
           "rejectedByStage": rejected, "proposals": state["steps"],
           "caveats": caveats(state, cov, tests), "clarifications": clarifications(state, tests)}
    out_json, out_md = Path(run) / "test-cases.json", Path(run) / "test-cases.md"
    out_json.write_text(json.dumps(doc, indent=2))
    out_md.write_text(markdown(doc))
    return {"tests": len(tests), "byCategory": by_cat, "coverage": doc["coverage"]["acceptanceCriteria"],
            "featureCoverage": cov["featureCoverage"].get("percent"), "stopReason": doc["stopReason"],
            "caveats": doc["caveats"], "clarifications": doc["clarifications"],
            "files": [str(out_json), str(out_md)]}


def markdown(doc: dict) -> str:
    key = doc["ticket"].get("key") or ""
    lines = [f'# Test cases: {key} {doc["ticket"].get("summary") or ""}'.rstrip(), ""]
    feat = doc["coverage"]["feature"].get("percent")
    lines += ["| Tests | Acceptance criteria covered | Feature coverage | Stopped because |", "|---|---|---|---|",
              f'| {len(doc["testCases"])} ({", ".join(f"{c} {n}" for c, n in doc["byCategory"].items())}) | '
              f'{doc["coverage"]["acceptanceCriteria"]} | {"n/a" if feat is None else str(feat) + "%"} | '
              f'{doc["stopReason"]} |', ""]
    for title, items in (("Caveats", doc["caveats"]), ("Questions for the product owner", doc["clarifications"])):
        if items:
            lines += [f"## {title}", ""] + [f"- {i}" for i in items] + [""]
    lines += ["## Tests", ""]
    for t in doc["testCases"]:
        lines += [f'### {t["id"]} [{t["category"]}, {t["priority"]}] {t["title"]}', ""]
        if t.get("preconditions"):
            lines += [f'**Preconditions:** {t["preconditions"]}', ""]
        lines += [f"{n}. {s}" for n, s in enumerate(t["steps"], 1)] + [""]
        lines += [f'**Expected:** {t["expected_result"]}', ""]
        meta = [f'grounding: {t.get("_grounding", "unverified")}']
        if t.get("test_data"):
            meta.insert(0, f'data: {t["test_data"]}')
        if t.get("requirementIds"):
            meta.append("covers " + ", ".join(t["requirementIds"]))
        if t.get("historicalReference"):
            meta.append("guards " + t["historicalReference"])
        lines += ["*" + " · ".join(meta) + "*", ""]
    return "\n".join(lines)
