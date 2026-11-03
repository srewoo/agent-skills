"""Acceptance gate: every proposed test must pass schema, grounding, relevance and de-duplication.

ponytail: grounding and dedup are lexical (regex references, difflib, token Jaccard). A
paraphrased duplicate with no shared words gets through; add an embedding model if that bites.
"""
import difflib
import re

from qtc_kg import lookup, urlsplit
from qtc_plan import CATEGORIES, test_text
from qtc_text import is_negative, jaccard, norm_label, tokens

Q = '["“”]'  # double quotes, straight or curly
NQ = '[^"“”]'
# A quoted value followed by "in/from the ... dropdown" is an option, not a control.
OPTION_RE = re.compile(rf"\b(?:select|choose|pick)\s+(?:the\s+)?{Q}({NQ}{{1,60}}){Q}\s+(?:option\s+)?(?:in|from)\s+"
                       rf"the\s+{Q}?([^\"“”]{{1,40}}?){Q}?\s+(?:dropdown|select|list|menu|combobox|field)\b", re.I)
CONTROL_RES = [
    re.compile(rf"\b(?:click|clicks|clicking|press|tap|select|choose|open|toggle|check|uncheck)\s+(?:on\s+)?"
               rf"(?:the\s+)?{Q}({NQ}{{1,60}}){Q}(?!\s+(?:option\s+)?(?:in|from)\s)", re.I),
    re.compile(rf"{Q}({NQ}{{1,60}}){Q}\s+(?:button|link|tab|menu item|menu|option|icon)\b", re.I),
]
FIELD_RES = [
    re.compile(rf"{Q}({NQ}{{1,60}}){Q}\s+(?:field|input|textbox|text box|dropdown|select|checkbox|toggle|"
               rf"radio(?: button)?|textarea|combobox)\b", re.I),
    re.compile(r"\bthe\s+([a-z][a-z0-9 _-]{1,30}?)\s+(?:field|input|textbox|text box|dropdown|checkbox|textarea)\b",
               re.I),
]
API_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s,;)\"'`]*)")
URL_RE = re.compile(r"https?://[^\s\"'<>)`]+")
GENERIC = {"same", "next", "previous", "first", "last", "required", "above", "below", "following", "other",
           "this", "that", "any", "each", "relevant", "corresponding", "empty", "new", "search"}
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
NUMBER_WORDS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                "sixteen seventeen eighteen nineteen twenty").split()
NUMBER_WORD_RE = re.compile(r"\b(" + "|".join(NUMBER_WORDS) + r")\b")
STATE_WORDS = set(tokens("enabled disabled hidden visible empty expired locked unlocked active inactive readonly "
                         "read-only offline"))
DISTINCT_WORDS = set(tokens(
    "admin administrator owner editor viewer guest member manager anonymous visitor customer agent superuser "
    "enabled disabled hidden visible empty full expired locked unlocked active inactive readonly read-only "
    "first last maximum minimum max min over under above below exceeds mobile desktop tablet offline"))
# HTTP status codes and quoted messages in an expected result are facts the ticket must state.
STATUS_RE = re.compile(r"\b(?:status|code|returns?|responds?|with|http)\s+(?:code\s+)?([1-5]\d\d)\b", re.I)
QUOTED_RE = re.compile(rf"{Q}({NQ}{{3,120}}){Q}")
# Words every test uses; they say nothing about relevance.
TEST_VERBS = set(tokens("open navigate go type enter fill submit observe expect result appear message button "
                        "field page screen form input value step load wait return see confirm "
                        "positive negative edge regression integration security accessibility scenario case"))


def normalise(c: dict, category: str):
    """Coerce one candidate to the canonical shape, or return an error string."""
    if not isinstance(c, dict):
        return None, "not an object"
    steps = c.get("steps") or []
    if isinstance(steps, str):
        steps = [s.strip() for s in steps.splitlines() if s.strip()]
    t = {"title": str(c.get("title") or "").strip(),
         "category": c.get("category") or category or "",
         "priority": c.get("priority") or "P2",
         "description": str(c.get("description") or ""),
         "preconditions": str(c.get("preconditions") or ""),
         "steps": [str(s) for s in steps],
         "expected_result": str(c.get("expected_result") or c.get("expectedResult") or "").strip(),
         "test_data": c.get("test_data") if isinstance(c.get("test_data"), str) else str(c.get("test_data") or ""),
         "requirementIds": list(c.get("requirementIds") or [])}
    for k in ("historicalReference", "rationale"):
        if c.get(k):
            t[k] = str(c[k])
    if t["category"] not in CATEGORIES:
        return None, f"category must be one of {', '.join(CATEGORIES)}"
    if not t["title"] or not t["steps"] or not t["expected_result"]:
        return None, "title, steps and expected_result are required"
    return t, None


def action_text(t: dict) -> str:
    """What the test does and checks. Preconditions are set-up, so they neither ground nor make relevant."""
    return " ".join([t["title"], " ".join(t["steps"]), t["expected_result"]])


def extract_refs(text: str, app_host: str) -> list:
    refs = [("options", f"{m.group(1).strip()}\x00{m.group(2).strip()}") for m in OPTION_RE.finditer(text)]
    for rx in CONTROL_RES:
        refs += [("controls", m.group(1).strip()) for m in rx.finditer(text)]
    for rx in FIELD_RES:
        for m in rx.finditer(text):
            label = m.group(1).strip()
            if norm_label(label) not in GENERIC:
                refs.append(("fields", label))
    refs += [("apis", f"{m.group(1)} {m.group(2)}") for m in API_RE.finditer(text)]
    for m in URL_RE.finditer(text):
        parts = urlsplit(m.group(0).rstrip(".,"))
        if not app_host or parts.netloc == app_host:
            refs.append(("routes", parts.path or "/"))
    seen, out = set(), []
    for kind, label in refs:
        if (kind, norm_label(label)) not in seen:
            seen.add((kind, norm_label(label)))
            out.append((kind, label))
    return out


def ground(t: dict, idx: dict, ticket_text: str, app_host: str) -> dict:
    """Verify references; repair near-misses in place. Returns {'ok', 'status', 'reason', 'refs', 'repairs'}."""
    if not any(idx.values()):
        return {"ok": True, "status": "unverified", "refs": [], "repairs": []}
    refs = extract_refs(test_text(t), app_host)
    if not extract_refs(action_text(t), app_host):
        return {"ok": False, "reason": "names no concrete field, control, API or URL from the crawled app - "
                                       "too vague to ground"}
    matched, repairs, spec = [], [], []
    ticket_norm = norm_label(ticket_text)
    for kind, label in refs:
        if kind == "options":
            value, _, field = label.partition("\x00")
            choices = idx.get("options", {}).get(norm_label(field))
            if not choices:
                continue  # no option list recorded for that dropdown (e.g. a custom one): can't check
            if not difflib.get_close_matches(norm_label(value), [norm_label(c) for c in choices], n=1, cutoff=0.82):
                return {"ok": False, "reason": f'option "{value}" is not in the "{field}" dropdown '
                                               f'(it has: {", ".join(choices[:10])})'}
            matched.append(value)
            continue
        alt = {"controls": "fields", "fields": "controls"}.get(kind)
        how, real = lookup(idx, kind, label)
        if not how and alt:
            how, real = lookup(idx, alt, label)
        # Rewrite to the app's own label ("Sign-in" → "Sign In"); case-only differences are left alone.
        if how and real.lower() != label.lower() and kind not in ("apis", "routes"):
            repairs.append({"from": label, "to": real})
            _replace(t, label, real)
        if how:
            matched.append(real)
        elif norm_label(label) and norm_label(label) in ticket_norm:
            spec.append(label)  # the ticket introduces it; the app does not have it yet
        else:
            noun = {"controls": "control", "fields": "field", "apis": "API", "routes": "page"}[kind]
            return {"ok": False, "reason": f'{noun} "{label}" does not exist on any crawled page'}
    return {"ok": True, "status": "specification" if spec and not matched else "verified",
            "refs": matched + spec, "repairs": repairs, "specification": spec}


def claim_text(t: dict) -> str:
    """Title and expected result minus quoted labels, URLs and API paths: what the test asserts.
    Naming real controls must not make an unrelated assertion look relevant."""
    text = t["title"] + " " + t["expected_result"]
    for rx in (re.compile(rf"{Q}{NQ}*{Q}"), URL_RE, API_RE):
        text = rx.sub(" ", text)
    return text


def relevance(t: dict, ticket_vocab: set, app_vocab: set) -> float:
    words = set(tokens(claim_text(t))) - TEST_VERBS
    if not words:
        return 0.0
    on_ticket = len(words & ticket_vocab)
    on_app = len((words & app_vocab) - ticket_vocab)
    return round((2 * on_ticket + on_app) / (2 * len(words)), 3)


def distinguishers(t: dict) -> set:
    """Numbers, personas and UI states named in the claim. Two tests of the same flow that differ in
    any of these (3 rows vs 500 rows, admin vs viewer, enabled vs disabled) are different tests."""
    text = STATUS_RE.sub(" ", t["title"] + " " + t["expected_result"]).lower()  # "returns 201" is detail, not scenario
    text = NUMBER_WORD_RE.sub(lambda m: str(NUMBER_WORDS.index(m.group(0))), text)  # "three" → "3"
    return set(NUMBER_RE.findall(text)) | (set(tokens(text)) & DISTINCT_WORDS)


def _distinct(m1: set, m2: set) -> bool:
    """Different scenarios when each names a number/persona/state the other lacks (3 vs 4 rows,
    admin vs viewer), or when one adds a UI state ("... is disabled"). A one-sided extra persona
    or number ("Admin ... (as owner)") is a relabelled copy, not a new test."""
    only1, only2 = m1 - m2, m2 - m1
    return bool(only1 and only2) or bool((only1 | only2) & STATE_WORDS)


def duplicate_of(t: dict, accepted: list, threshold: float):
    words = tokens(test_text(t))
    neg = is_negative(t["title"] + " " + t["expected_result"])
    marks = distinguishers(t)
    for a in accepted:
        if neg != is_negative(a["title"] + " " + a["expected_result"]):
            continue  # "is accepted" and "is rejected" are different tests
        sim = jaccard(words, tokens(test_text(a)))
        title_sim = difflib.SequenceMatcher(None, norm_label(t["title"]), norm_label(a["title"])).ratio()
        if _distinct(marks, distinguishers(a)):
            continue
        if sim >= threshold or (title_sim >= 0.9 and sim >= 0.5):
            return a["id"], round(max(sim, title_sim), 2)
    return None, 0.0


def _replace(t: dict, old: str, new: str) -> None:
    rx = re.compile(re.escape(old), re.I)
    for k in ("title", "preconditions", "expected_result"):
        t[k] = rx.sub(new, t[k])
    t["steps"] = [rx.sub(new, s) for s in t["steps"]]


def assertion_warnings(t: dict, ticket_text: str, idx: dict) -> list:
    """Specifics the expected result asserts but neither the ticket nor the app supplies."""
    ticket = ticket_text.lower()
    known = {k for table in idx.values() for k in table}
    out = [f"asserts status {c}, which the ticket doesn't state" for c in STATUS_RE.findall(t["expected_result"])
           if c not in ticket]
    out += [f'asserts the exact text "{q}", which the ticket doesn\'t state' for q in QUOTED_RE.findall(t["expected_result"])
            if q.lower() not in ticket and norm_label(q) not in known]
    return out
