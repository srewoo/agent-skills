"""Self-check for qtc.py: python3 test_qtc.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from qtc_kg import parse_requests, template_path  # noqa: E402
from qtc_plan import build_requirements, derive_targets  # noqa: E402

TMP = Path(tempfile.mkdtemp())
RUN = str(TMP / "DEMO-42")


def qtc(*args, ok=True):
    r = subprocess.run([sys.executable, str(HERE / "qtc.py"), *args], capture_output=True, text=True)
    assert (r.returncode == 0) == ok, r.stderr + r.stdout
    return json.loads(r.stdout) if ok else r


def write(name, data):
    p = TMP / name
    p.write_text(data if isinstance(data, str) else json.dumps(data))
    return str(p)


TICKET = {"key": "DEMO-42", "summary": "Users can sign in with email and password",
          "description": "Login page for the web app.",
          "acceptanceCriteria": "- A user with valid credentials is signed in and lands on the dashboard\n"
                                "- An invalid password shows an error message\n"
                                "- The account must be locked after 5 consecutive failed attempts\n"
                                "- Case 1: returning users\n"
                                "- Optionally show a password strength hint"}
PAGE = {"url": "https://app.example.com/login", "title": "Sign in",
        "features": [{"type": "form", "name": "login", "submitText": "Sign In",
                      "fields": [{"name": "email", "label": "Email", "type": "email"},
                                 {"name": "password", "label": "Password", "type": "password"}]},
                     {"type": "button", "text": "Forgot password"},
                     {"type": "link", "text": "Dashboard", "href": "https://app.example.com/dashboard"}],
        "links": ["https://app.example.com/dashboard"]}
REQUESTS = "[POST] https://app.example.com/api/auth/login => [401]\n[GET] https://app.example.com/main.js => [200]\n" \
           "[GET] https://cdn.other.com/api/x => [200]"

# --- units -------------------------------------------------------------------------------------
assert template_path("/api/orders/8412/items") == "/api/orders/:id/items"
assert parse_requests(REQUESTS, PAGE["url"]) == [{"method": "POST", "endpoint": "/api/auth/login"}]
har = json.dumps({"log": {"entries": [{"request": {"method": "get", "url": "https://app.example.com/api/me"}}]}})
assert parse_requests(har, PAGE["url"]) == [{"method": "GET", "endpoint": "/api/me"}]
reqs = build_requirements(TICKET)
assert [r["status"] for r in reqs] == ["mandatory", "mandatory", "mandatory", "scenario_header", "optional"], reqs
assert reqs[2]["negative"] is False  # "must be locked" demands a state; it is not a prohibition
gwt = build_requirements({"acceptanceCriteria": "Given a user\nWhen they click Save\nThen it is saved\nUsers cannot delete"})
assert len(gwt) == 2 and gwt[0]["text"].startswith("Given a user When") and gwt[1]["negative"], gwt
t = derive_targets(TICKET, 12)
assert sum(t["targets"].values()) == 12 and "security" in t["shapes"] and t["targets"].get("Security"), t

# --- end to end: crawl → init → propose → coverage → finalize ---------------------------------
KG = str(TMP / "kg.json")
added = qtc("kg-add", "--kg", KG, "--page", write("page.json", PAGE), "--requests", write("req.txt", REQUESTS))
step2 = qtc("kg-add", "--kg", KG, "--page", write("page.json", PAGE), "--url", PAGE["url"] + "#step-2")
assert step2["pages"] == 2, step2  # a second dialog step at the same URL is kept, not overwritten
qtc("kg-add", "--kg", KG, "--page", write("page.json", PAGE), "--requests", write("req.txt", REQUESTS))
assert added["page"]["forms"] == 1 and added["page"]["apis"] == 1 and added["unvisitedLinks"], added
init = qtc("init", "--run", RUN, "--ticket", write("ticket.json", TICKET), "--kg", KG, "--count", "12")
assert "Email" in init["groundingContext"] and not init["degradations"], init
assert qtc("inspect", "--run", RUN, "--control", "Sign In")["exists"]
assert not qtc("inspect", "--run", RUN, "--field", "Remember me")["exists"]
assert PAGE["url"] in [p["url"] for p in qtc("search", "--run", RUN, "--query", "password login")["pages"]]

base = {"category": "Positive", "priority": "P1", "preconditions": "A registered user on https://app.example.com/login"}
batch = [
    dict(base, title="Valid credentials sign the user in", requirementIds=["R01"],
         steps=['Type a valid address in the email field', 'Type the matching password in the "Password" field',
                'Click "Sign-in"'],
         expected_result="The user is signed in and lands on the dashboard"),
    dict(base, title="Remember me keeps the session", steps=['Tick the "Remember me" checkbox', 'Click "Sign In"'],
         expected_result="The session survives a browser restart"),
    dict(base, title="Wrong password shows an error", category="Negative",
         steps=["Enter a wrong password", "Submit"], expected_result="An error message is shown"),
    dict(base, title="Valid credentials sign the user in", steps=['Fill the email field', 'Click "Sign In"'],
         expected_result="The user is signed in and lands on the dashboard"),
    dict(base, title="Quarterly revenue chart renders", steps=['Click "Forgot password"'],
         expected_result="Revenue bars for every quarter of the fiscal calendar appear in the analytics widget"),
    {"title": "missing steps", "category": "Positive", "expected_result": "x"},
]
res = qtc("propose", "--run", RUN, write("batch-1.json", batch), "--focus", "R01")
stages = [(r["status"], r.get("stage")) for r in res["results"]]
assert stages == [("accepted", None), ("rejected", "grounding"), ("rejected", "grounding"),
                  ("rejected", "duplicate"), ("rejected", "relevance"), ("rejected", "schema")], stages
first = res["results"][0]
assert first["repaired"] and first["repairs"] == [{"from": "Sign-in", "to": "Sign In"}], first
assert "Remember me" in res["results"][1]["reason"] and "too vague" in res["results"][2]["reason"]

cov = qtc("coverage", "--run", RUN)
assert cov["acCoverage"] == {"covered": 1, "total": 3, "perRequirement": cov["acCoverage"]["perRequirement"]}, cov
assert not cov["stop"]["stop"] and cov["recommendedNext"]["requirementId"] == "R02", cov

batch2 = [
    dict(base, title="A wrong password shows an error message", category="Negative", requirementIds=["R02"],
         steps=["Type a registered address in the email field", "Type a wrong password in the password field",
                'Click "Sign In"'], expected_result="An error message is shown and POST /api/auth/login returns 401"),
    dict(base, title="The account cannot be locked after 5 failed attempts", category="Security",
         requirementIds=["R03"], steps=["Type a wrong password in the password field", 'Click "Sign In" 5 times'],
         expected_result="The account is never locked after 5 consecutive failed attempts"),
    dict(base, title="Weather widget shows forecast", steps=['Click "Sign In"'],
         expected_result="Rain forecast shown for Paris tomorrow"),
]
res2 = qtc("propose", "--run", RUN, write("batch-2.json", batch2))
r2 = res2["results"]
assert [x.get("stage") for x in r2] == [None, "polarity", "relevance"], r2   # declared contradiction, off-topic
assert r2[0]["warnings"] == ["asserts status 401, which the ticket doesn't state"], r2[0]

# An undeclared but unmistakable contradiction is accepted and flagged by coverage, not silently counted.
contra = [dict(base, title="Account is never locked after 5 consecutive failed attempts", category="Security",
               steps=["Type a wrong password in the password field", 'Click "Sign In" 5 times'],
               expected_result="The account is never locked after 5 consecutive failed attempts")]
qtc("propose", "--run", RUN, write("batch-3.json", contra))
out = {o["id"]: o["problem"] for o in qtc("coverage", "--run", RUN)["outstandingObligations"]}
assert out == {"R03": "contradicted"}, out

fixed = [dict(base, title="The account is locked after 5 consecutive failed attempts", category="Security",
              requirementIds=["R03"], steps=["Type a wrong password in the password field 5 times",
                                             'Click "Sign In" after each'],
              expected_result="The account is locked and a locked-account message is shown"),
         dict(base, title="The account stays unlocked after 4 consecutive failed attempts", category="Edge",
              requirementIds=["R03"], steps=["Type a wrong password in the password field 4 times",
                                             'Click "Sign In" after each'],
              expected_result="The account stays unlocked and the user can still sign in")]
res4 = qtc("propose", "--run", RUN, write("batch-4.json", fixed))
assert res4["accepted"] == 2, res4  # a boundary that differs only in its number is not a duplicate
verdicts = write("verdicts.json", {"verdicts": [{"id": "T-03", "verdict": "contradictory", "issue": "asserts the opposite"}]})
fin = qtc("finalize", "--run", RUN, "--verdicts", verdicts, "--strict")
assert fin["tests"] == 4 and fin["coverage"] == "3/3", fin  # coverage recomputed without the dropped test
assert any("optional" in c for c in fin["clarifications"]), fin["clarifications"]
assert any("401" in c for c in fin["caveats"]), fin["caveats"]
md = Path(fin["files"][1]).read_text()
assert "### T-01 [Positive, P1]" in md and "grounding: verified" in md and "Sign In" in md

# --- re-running init must not wipe a run ------------------------------------------------------
assert qtc("init", "--run", RUN, "--ticket", write("ticket.json", TICKET), ok=False).returncode == 2

# --- budget, history and the extra gate rules --------------------------------------------------
run3 = str(TMP / "budget")
qtc("init", "--run", run3, "--ticket", write("ticket.json", TICKET), "--kg", KG, "--count", "1")
r3 = qtc("propose", "--run", run3, write("b3.json", [batch[0], batch2[0],
         dict(batch2[0], category="Regression", historicalReference="DEMO-7", title="Lockout regression")]))
assert [x["status"] for x in r3["results"]] == ["accepted", "rejected", "rejected"], r3
assert r3["results"][1]["stage"] == "budget", r3
run4 = str(TMP / "history")
qtc("init", "--run", run4, "--ticket", write("ticket.json", TICKET), "--kg", KG, "--count", "5")
reg = dict(batch2[0], category="Regression", title="Lockout counter regression", historicalReference="DEMO-7")
r4 = qtc("propose", "--run", run4, write("b4.json", [reg]))["results"][0]
assert r4["stage"] == "grounding" and "history" in r4["reason"], r4  # no stored history: cannot be cited
qtc("history", "--run", run4, write("issues.json", [{"key": "DEMO-7", "summary": "Lockout counter not reset after password reset"}]))
assert qtc("propose", "--run", run4, write("b4.json", [reg]))["accepted"] == 1

import qtc_gate as gate  # noqa: E402
from qtc_kg import index  # noqa: E402
from qtc_plan import coverage_of, distinctive_words  # noqa: E402
role_kg = {"pages": [{"url": "https://app.example.com/members", "features": [{"type": "form", "fields": [
    {"name": "role", "label": "Role", "options": ["Admin", "Editor", "Viewer"]}]},
    {"type": "button", "text": "Bulk invite"}]}]}
ridx = index(role_kg)
pick = lambda v: gate.normalise({"title": "t", "category": "Positive", "expected_result": "ok",  # noqa: E731
                                 "steps": [f'Select "{v}" in the "Role" dropdown', 'Click "Bulk invite"']}, None)[0]
assert gate.ground(pick("Editor"), ridx, "", "app.example.com")["ok"]
bad = gate.ground(pick("Owner"), ridx, "", "app.example.com")
assert not bad["ok"] and "not in the \"Role\" dropdown" in bad["reason"], bad
a = {"title": "Admin sees the Bulk invite button", "expected_result": "The Bulk invite button is shown", "steps": ["x"]}
v = {"title": "Viewer sees the Bulk invite button disabled", "expected_result": "The Bulk invite button is disabled",
     "steps": ["x"]}
assert gate.distinguishers(a) != gate.distinguishers(v)
three = {"title": "Admin invites three valid rows", "expected_result": "All rows are invited"}
assert gate.distinguishers(three) == gate.distinguishers(dict(three, title="Admin invites 3 valid rows"))
# Round-2 review repros: single digits, persona-prefixed copies, undeclared wrong polarity.
inv = {"id": "T-01", "title": "Admin bulk invites 3 valid rows", "category": "Positive",
       "steps": ['Click "Bulk invite"', 'Choose a CSV with 3 valid rows in the "CSV file" field', 'Click "Send invites"'],
       "expected_result": "All 3 rows are invited and a success summary is shown"}
four = dict(inv, title="Admin bulk invites 4 valid rows", expected_result="All 4 rows are invited and a success summary is shown",
            steps=[x.replace("3", "4") for x in inv["steps"]])
assert gate.duplicate_of(four, [inv], 0.68)[0] is None, "3 rows vs 4 rows are different boundaries"
owner = dict(inv, title="Admin bulk invites 3 valid rows (as owner)", steps=["Log in as an owner"] + inv["steps"])
assert gate.duplicate_of(owner, [inv], 0.68)[0] == "T-01", "a one-sided persona label is a relabelled copy"
viewer_rule = {"id": "R03", "text": "Viewers cannot invite users", "negative": True}
assert coverage_of(viewer_rule, {"title": "Viewer can invite users", "expected_result": "The invites are sent",
                                 "steps": ['Click "Bulk invite"'], "requirementIds": []}) == "contradicts"
assert coverage_of(viewer_rule, {"title": "Viewer sees the Bulk invite button disabled",
                                 "expected_result": "The Bulk invite button is disabled for viewers",
                                 "steps": ['Click "Bulk invite"'], "requirementIds": []}) == "covers"
admin_rule = {"id": "R01", "text": "Admins can invite users from a CSV", "negative": False}
blocked = {"title": "Admin bulk invite is disabled for a valid CSV", "steps": ['Click "Bulk invite"'],
           "expected_result": 'The "Send invites" button is disabled and the upload is blocked', "requirementIds": ["R01"]}
assert coverage_of(admin_rule, blocked) == "contradicts", "a prevented state does not satisfy a 'can' criterion"
hide_rule = {"id": "R09", "text": "Hide the sidebar on narrow screens", "negative": False}
assert coverage_of(hide_rule, {"title": "Sidebar is hidden on a narrow screen", "expected_result": "The sidebar is hidden",
                               "steps": ["Resize"], "requirementIds": ["R09"]}) == "covers"
assert coverage_of(viewer_rule, {"title": "Viewer is shown an error message on bulk invite",
                                 "expected_result": "An error message is shown", "steps": ['Click "Bulk invite"'],
                                 "requirementIds": []}) == "", "an error alone neither covers nor contradicts"
reqs5 = [{"id": "R01", "text": "Admins can invite users by CSV", "negative": False},
         {"id": "R05", "text": "The invite dialog should let the admin choose a role", "negative": False}]
t1 = {"id": "T-01", "title": "Admin invites users from a CSV", "expected_result": "Every user in the CSV is invited",
      "steps": ["Upload the CSV"], "requirementIds": []}
d5 = distinctive_words(reqs5)
assert coverage_of(reqs5[1], t1, d5["R05"]) == "", "sharing invite/admin must not cover the role criterion"
assert coverage_of(reqs5[0], t1, d5["R01"]) == "covers"

# --- no crawl: grounding off, honestly labelled -------------------------------------------------
run2 = str(TMP / "nocrawl")
init2 = qtc("init", "--run", run2, "--ticket", write("ticket.json", TICKET), "--count", "6", "--force")
assert init2["degradations"] and init2["groundingContext"] == ""
r = qtc("propose", "--run", run2, write("b.json", [batch[2]]))
assert r["results"][0]["grounding"] == "unverified", r
assert "No crawl" in qtc("finalize", "--run", run2)["caveats"][0]

# --- bad input ----------------------------------------------------------------------------------
assert qtc("coverage", "--run", str(TMP / "missing"), ok=False).returncode == 2
assert qtc("propose", "--run", RUN, write("bad.json", "{}"), ok=False).returncode == 2
print("ok")
