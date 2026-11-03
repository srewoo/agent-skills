"""Knowledge graph of the app under test: pages, their controls and the API calls they make.

Shape (kg.json): {"appUrl": str, "pages": [{"url", "title", "features": [...], "apis": [...], "links": [...]}]}
where a feature is {"type": "form", "name", "fields": [{"name","label","type",...}], "submitText"},
{"type": "button", "text"} or {"type": "link", "text", "href"}, and an api is {"method", "endpoint"}.
"""
import difflib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from qtc_text import BM25, norm_label

STATIC_RE = re.compile(r"\.(js|mjs|css|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot|map|mp4|webm|pdf)(\?|$)", re.I)
# "[GET] https://x/api/a => [200]", "GET https://x/api/a 200", "POST /api/a" ...
REQ_LINE_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\b\]?\s+(\S+)", re.I)
ID_SEG_RE = re.compile(r"^(\d+|[0-9a-f]{8,}|[0-9a-f]{8}-[0-9a-f-]{27,}|[A-Za-z0-9_-]{20,})$", re.I)


def load(path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"appUrl": "", "pages": []}
    kg = json.loads(p.read_text())
    pages = kg.get("pages") or []
    if isinstance(pages, dict):  # URL-keyed map → list
        pages = [dict(v, url=u) for u, v in pages.items()]
    kg["pages"] = pages
    return kg


def template_path(path: str) -> str:
    """/api/orders/8412/items → /api/orders/:id/items, so one endpoint matches every id."""
    segs = [(":id" if ID_SEG_RE.match(s) else s) for s in path.split("/")]
    return "/".join(segs).rstrip("/") or "/"


def parse_requests(text: str, page_url: str, all_origins: bool = False) -> list:
    """API calls from a browser tool's request log, a HAR file, or a JSON list of {method,url}."""
    origin = urlsplit(page_url).netloc if page_url else ""
    found = []

    def push(method, url):
        if not url or STATIC_RE.search(url):
            return
        parts = urlsplit(url)
        if parts.netloc and origin and parts.netloc != origin and not all_origins:
            return
        found.append({"method": str(method or "GET").upper(), "endpoint": template_path(parts.path or url)})

    raw = str(text or "").strip()
    if raw[:1] in "[{":
        try:
            data = json.loads(raw)
            entries = data.get("log", {}).get("entries") if isinstance(data, dict) else None
            items = [e.get("request", {}) for e in entries] if entries else (
                data if isinstance(data, list) else data.get("requests", []))
            for r in items:
                push(r.get("method"), r.get("url"))
            raw = ""
        except (ValueError, AttributeError):
            pass
    for line in raw.splitlines():
        m = REQ_LINE_RE.search(line)
        if m:
            push(m.group(1), m.group(2))
    seen, out = set(), []
    for a in found:
        key = (a["method"], a["endpoint"])
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


def add_page(kg: dict, page: dict, requests_text: str = "", all_origins: bool = False) -> dict:
    url = page.get("url")
    if not url:
        raise ValueError("page has no url")
    apis = parse_requests(requests_text, url, all_origins) if requests_text else page.get("apis", [])
    entry = {"url": url, "title": page.get("title", ""), "features": page.get("features") or [],
             "apis": apis, "links": page.get("links") or []}
    kg.setdefault("appUrl", url)
    kg["pages"] = [p for p in kg.get("pages", []) if p.get("url") != url] + [entry]
    visited = {p["url"] for p in kg["pages"]}
    return {"pages": len(kg["pages"]), "page": summarize(entry),
            "unvisitedLinks": [link for link in entry["links"] if link not in visited][:25]}


def summarize(p: dict) -> dict:
    feats = p.get("features") or []
    count = lambda t: sum(1 for f in feats if f.get("type") == t)  # noqa: E731
    return {"url": p.get("url"), "title": p.get("title"), "forms": count("form"),
            "buttons": count("button"), "links": count("link"), "apis": len(p.get("apis") or [])}


def page_entities(p: dict) -> dict:
    """Display labels of one page's fields, controls, APIs and routes."""
    fields, controls, apis = [], [], []
    for f in p.get("features") or []:
        if f.get("type") == "form":
            for fld in f.get("fields") or []:
                fields.append(fld.get("label") or fld.get("name") or "")
                for alt in (fld.get("name"), fld.get("placeholder"), fld.get("id")):
                    if alt:
                        fields.append(alt)
            if f.get("submitText"):
                controls.append(f["submitText"])
        elif f.get("type") in ("button", "link") and f.get("text"):
            controls.append(f["text"])
    for a in p.get("apis") or []:
        apis.append(f'{a.get("method", "GET").upper()} {template_path(a.get("endpoint", ""))}')
    route = template_path(urlsplit(p.get("url", "")).path)
    return {"fields": _uniq(fields), "controls": _uniq(controls), "apis": _uniq(apis), "routes": [route]}


def index(kg: dict) -> dict:
    """Normalised label → display label, per entity kind, across every page."""
    idx = {"fields": {}, "controls": {}, "apis": {}, "routes": {}, "options": {}}
    for p in kg.get("pages", []):
        for f in p.get("features") or []:
            for fld in (f.get("fields") or []) if f.get("type") == "form" else []:
                if fld.get("options"):  # dropdown label/name → its option texts
                    for key in (fld.get("label"), fld.get("name")):
                        if key:
                            idx["options"][norm_label(key)] = fld["options"]
        ents = page_entities(p)
        for kind, labels in ents.items():
            for label in labels:
                key = label.upper() if kind in ("apis",) else label if kind == "routes" else norm_label(label)
                if key:
                    idx[kind].setdefault(key, label)
        for link in p.get("links") or []:
            idx["routes"].setdefault(template_path(urlsplit(link).path), link)
    return idx


def lookup(idx: dict, kind: str, label: str, cutoff: float = 0.82):
    """('exact'|'repaired', display) when the label names a real entity, else (None, None)."""
    table = idx.get(kind, {})
    if kind == "apis":
        method, _, path = label.strip().partition(" ")
        key = f"{method.upper()} {template_path(path.strip())}".upper()
    elif kind == "routes":
        key = template_path(urlsplit(label).path or label)
    else:
        key = norm_label(label)
    if key in table:
        return "exact", table[key]
    close = difflib.get_close_matches(key, list(table), n=1, cutoff=cutoff)
    return ("repaired", table[close[0]]) if close else (None, None)


def page_doc(p: dict) -> str:
    e = page_entities(p)
    return " ".join([p.get("title", ""), p.get("url", "")] + e["fields"] + e["controls"] + e["apis"])


def search(kg: dict, query: str, k: int = 5) -> list:
    pages = kg.get("pages", [])
    if not pages:
        return []
    hits = BM25([page_doc(p) for p in pages]).top(query, k)
    return [dict(url=pages[i]["url"], title=pages[i].get("title", ""), **page_entities(pages[i])) for i in hits]


def grounding_context(kg: dict, query: str, k: int = 6) -> str:
    """The entities the author may reference, from the pages most relevant to the ticket."""
    rows = search(kg, query, k) or [dict(url=p["url"], **page_entities(p)) for p in kg.get("pages", [])[:k]]
    lines = []
    for r in rows:
        lines.append(f'Page {r["url"]}')
        for kind in ("fields", "controls", "apis"):
            if r[kind]:
                lines.append(f'  {kind}: ' + "; ".join(r[kind][:25]))
    return "\n".join(lines)


def _uniq(items) -> list:
    seen, out = set(), []
    for i in items:
        k = norm_label(i) or i
        if i and k not in seen:
            seen.add(k)
            out.append(i)
    return out
