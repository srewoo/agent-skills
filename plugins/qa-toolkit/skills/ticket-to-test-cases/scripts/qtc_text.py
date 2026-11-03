"""Text primitives shared by the ticket-to-test-cases scripts. Stdlib only (Python 3.9+)."""
import math
import re
from collections import Counter

STOPWORDS = set("""
a an the and or but if then else for to of in on at by with from into over under as is are was were be been being
do does did will would should could can may might must shall this that these those it its they them their there
user users system page click clicks enter verify check test tests case cases given when ensure displayed shown
correct able via also any all each every some such than so not no yes i we you our your he she his her has have had
""".split())

# Words that make a statement forbid an action. State words (hidden, disabled,
# error, read-only) are NOT here: "the Save button is disabled" asserts a
# required state, it does not negate the behaviour.
NEGATION_RE = re.compile(
    r"\b(cannot|can't|can not|must not|mustn't|should not|shouldn't|shall not|will not|won't|"
    r"may not|never|not (?:be )?(?:able|allowed|permitted)|is (?:denied|forbidden|prohibited)|"
    r"are (?:denied|forbidden|prohibited)|(?:is|are) blocked from|(?:is|are) prevented from|"
    r"unable to|disallow(?:ed|s)?)\b", re.I)

# A state that shows an action was prevented. It satisfies a "cannot" criterion, but it is not a
# negation on its own: "the sidebar is hidden" still agrees with "hide the sidebar".
PREVENTION_RE = re.compile(
    r"\b(disabled|hidden|greyed out|grayed out|read[- ]only|rejected|denied|blocked|forbidden|prevented|"
    r"unauthori[sz]ed|not (?:shown|visible|displayed|available|offered|listed))\b", re.I)

# A criterion that itself asks for a prevented state ("hide the sidebar", "the upload is rejected").
REQUIRES_PREVENTION_RE = re.compile(
    r"\b(hid(?:e|es|den|ing)|disabl\w*|reject\w*|block\w*|den(?:y|ies|ied)|prevent\w*|forbid\w*|"
    r"restrict\w*|read[- ]only|gr[ae]y(?:ed)? out|lock\w*)\b", re.I)
# Evidence too weak to settle a "cannot" criterion either way.
WEAK_PREVENTION_RE = re.compile(r"\b(error|warning|message|not allowed|permission)\b", re.I)

SYNONYMS = {
    "signin": "login", "log": "login", "logon": "login", "sign": "login",
    "signout": "logout", "logoff": "logout",
    "remove": "delete", "erase": "delete", "destroy": "delete",
    "add": "create", "new": "create", "make": "create",
    "edit": "update", "modify": "update", "change": "update",
    "show": "display", "view": "display", "see": "display", "visible": "display",
    "error": "error", "invalid": "invalid", "wrong": "invalid", "incorrect": "invalid",
    "pwd": "password", "passcode": "password",
    "e-mail": "email", "mail": "email",
}

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")


def stem(word: str) -> str:
    """Tiny suffix stripper: enough to match 'deleting'/'deleted'/'deletes'."""
    for suf in ("ations", "ation", "ings", "ing", "edly", "ed", "ies", "es", "s"):
        if suf == "s" and word.endswith(("ss", "us", "is")):
            break  # pass, status, analysis are not plurals
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            if suf == "es" and not word[:-2].endswith(("s", "x", "z", "ch", "sh")):
                suf = "s"  # invites → invite, but passes → pass, boxes → box
            word = word[: -len(suf)] + ("y" if suf == "ies" else "")
            if suf in ("ed", "ing") and word[-1] == word[-2] and word[-1] not in "lsz":
                word = word[:-1]  # logged → log, stopped → stop
            break
    # Drop a final "e" so invite / invites / invited / inviting all become "invit".
    return word[:-1] if word.endswith("e") and len(word) > 3 else word


def tokens(text: str, keep_stopwords: bool = False) -> list:
    out = []
    for w in _WORD_RE.findall(str(text or "").lower()):
        w = SYNONYMS.get(w, w)
        if not keep_stopwords and (w in STOPWORDS or (len(w) < 2 and not w.isdigit())):
            continue
        out.append(SYNONYMS.get(stem(w), stem(w)))
    return out


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a and b else 0.0


def content_tokens(text: str) -> list:
    """Tokens without the negation words, so "can invite" and "cannot invite" overlap fully and
    polarity is judged separately by is_negative()."""
    return tokens(NEGATION_RE.sub(" ", str(text or "")))


def is_negative(text: str) -> bool:
    return bool(NEGATION_RE.search(str(text or "")))


def norm_label(text: str) -> str:
    """Normalise a UI label for comparison: lowercase, no punctuation, single spaces."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", str(text or "").lower())).strip()


class BM25:
    """Okapi BM25 over a list of documents (each a string)."""

    def __init__(self, docs, k1: float = 1.5, b: float = 0.75):
        self.docs = [tokens(d) for d in docs]
        self.k1, self.b = k1, b
        self.avg = (sum(len(d) for d in self.docs) / len(self.docs)) if self.docs else 0.0
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list:
        q = tokens(query)
        out = []
        for d in self.docs:
            tf = Counter(d)
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * len(d) / (self.avg or 1)))
            out.append(s)
        return out

    def top(self, query: str, k: int = 5) -> list:
        """Indices of the k best-scoring documents with a score above zero."""
        ranked = sorted(enumerate(self.scores(query)), key=lambda x: -x[1])
        return [i for i, s in ranked[:k] if s > 0]
