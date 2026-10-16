---
name: technical-seo-audit
description: Use when the user asks for a technical SEO audit, site health check, SEO crawl or indexing review, or reports symptoms like pages missing from Google, "Crawled/Discovered - currently not indexed" in Search Console, traffic drops after a migration or redesign, redirect chains, duplicate or canonical problems, hreflang errors, broken structured data, or poor Core Web Vitals. Not for keyword research or content planning.
---

# Technical SEO Audit

## Overview

Find what stops search engines from crawling, rendering, indexing and understanding a site, then rank fixes by **impact × pages affected**. Every finding carries evidence (a count and example URLs) and a way to verify the fix. Length guidance for titles and descriptions is a heuristic, never a rule.

## When to use / When not to use

- Use for: full-site or section audits, pre/post-migration checks, "why isn't this page indexed", Core Web Vitals triage, launch readiness.
- Not for: grouping keywords or mapping them to pages (use `keyword-cluster`), finding topics competitors cover (use `content-gap`), copywriting or link building.

## Inputs

Ask once, in one message, only for what has no default.

| Input | Default if not given |
|---|---|
| Site URL (start page) | **Required.** Ask. Confirm the user owns it or may crawl it. |
| Page budget | `--max-pages 200`; raise to 1,000-5,000 for a full audit of a larger site |
| Sitemap URL | `Sitemap:` lines in robots.txt, else `/sitemap.xml` |
| Priority pages/templates | Homepage + one URL per template found (category, product, article) |
| Search Console exports | Optional but strongly preferred: Page indexing report, Core Web Vitals report, Performance (pages) |
| Existing crawl | Optional: a Screaming Frog / Sitebulb / other crawler export replaces step 3 |

**No shell (plain chat):** ask the user to paste robots.txt, the sitemap (or URL count), a crawler export (CSV), raw HTML and response headers of 3-5 key template pages, and PageSpeed Insights results. Run steps 4-8 on what they paste and list what could not be checked.

## Workflow

### 1. Fix the scope

Write down: host(s) in scope (www vs non-www, subdomains, http vs https), page budget, environment (production vs staging), and which data sources you have.
**Done when** scope and data sources are stated in one short block at the top of your notes.

### 2. Read robots.txt and sitemaps

```sh
curl -sS -A "Mozilla/5.0 (compatible; seo-audit)" https://www.example.com/robots.txt
curl -sS https://www.example.com/sitemap.xml | head -50
curl -sS https://www.example.com/sitemap.xml | grep -o "<loc>[^<]*</loc>" | wc -l   # URL count (or child sitemaps for an index)
for u in http://example.com/ http://www.example.com/ https://example.com/; do curl -sS -o /dev/null -w "%{http_code} %{redirect_url}\n" "$u"; done
```

Check: important paths not disallowed; CSS/JS not blocked; `Sitemap:` lines present; sitemap files ≤ 50,000 URLs and ≤ 50 MB uncompressed; every host/protocol variant 301s to one canonical origin in one hop.
**Done when** you have recorded the disallow rules, sitemap URL count and the canonical origin.

### 3. Crawl

```sh
python3 scripts/crawl.py https://www.example.com/ \
  --sitemap https://www.example.com/sitemap.xml \
  --max-pages 500 --delay 1 --output crawl.csv
```

(`py` instead of `python3` on Windows; needs Python 3.9+, no packages.) The crawler stays on the start host, obeys robots.txt the way Google reads it (`*`/`$` wildcards, longest rule wins) plus its Crawl-delay, records every redirect hop as its own row, and crawls sitemap URLs that links never reached last, leaving their `depth` empty. Columns: `url, status, redirect_target, content_type, title, meta_description, canonical, meta_robots, x_robots_tag, h1_count, word_count, internal_links, inlinks, depth, in_sitemap, hreflang_count, img_missing_alt, jsonld_count, jsonld_errors, mixed_content, has_viewport, error`.

`inlinks` = crawled pages linking to the URL; `internal_links` = internal links on the page. Start from the canonical origin found in step 2: the crawler does not leave the start host, so `https://example.com/` that 301s to `www` stops after one row (it warns).

**Faceted navigation / parameter URLs:** filter and sort combinations can fill the whole page budget. First crawl ~200 pages and count URLs per parameter (`?color=`, `&sort=`). Then re-run with `--exclude '[?&](color|size|sort)='` so the budget goes to real pages; excluded URLs are not fetched but still count in `inlinks`. Report the parameter counts as their own finding (see Faceted navigation in checks.md).

**Several locales:** the crawler reads hreflang only from `<link>` tags in HTML, not from sitemaps or HTTP headers, and does not leave the start host. Crawl each locale host (or `/xx-yy/` folder start page) separately.

It does **not** execute JavaScript. If it finds only a handful of URLs while the sitemap lists many, links are probably rendered client-side: keep `--sitemap` so listed URLs are still fetched, report "internal links not crawlable without JS" as a finding to confirm in step 5, and use a JS-rendering crawler if the user has one. If stderr says `stopped at --max-pages`, the crawl is a sample: say so and do not extrapolate counts.

Large CSVs: read them with a short script (Python's `csv` module) or a spreadsheet rather than by eye.
**Done when** stderr shows `crawled N URLs` and the CSV has N rows plus a header.

### 4. Detect issues from the crawl data

Load the CSV (or the user's export) and apply these rules. Count affected URLs and keep 3-5 examples per issue. Thresholds, fixes and edge cases are in [references/checks.md](references/checks.md).

| Area | Flag when |
|---|---|
| Status | `status` 4xx/5xx on URLs that are linked internally (`inlinks` > 0) or in the sitemap |
| Redirects | any internal link points at a 3xx; chain = a `redirect_target` that is itself 3xx; loop = a chain that revisits a URL; 302/307 used for a permanent move |
| Sitemap hygiene | `in_sitemap` is true and status ≠ 200, or noindex, or canonical points elsewhere |
| Orphans | `in_sitemap` true and `depth` empty (no internal link reaches it) |
| Indexability | `noindex` in `meta_robots` or `x_robots_tag` on a page that should rank; `blocked_by_robots` on a page that should rank |
| Canonicals | missing on indexable pages; points to a non-200, a redirect, a noindex URL, or another host; differs from the URL on pages that should rank; canonical chains |
| Duplicates | same `title` + `meta_description` across URLs; near-identical URLs (case, trailing slash, `?utm_`/sort/filter parameters) both returning 200 |
| Titles/descriptions | missing, duplicated, or far outside the heuristic (titles ~30-60 chars, descriptions ~70-160 chars) |
| Headings | `h1_count` 0 (or many on a template where one is expected) |
| Thin content | `word_count` well below the site's median for the same template (e.g. < 150 on article templates); confirm by viewing |
| Depth | important pages at `depth` > 3 |
| Mobile | `has_viewport` false |
| HTTPS | `mixed_content` > 0; any `http://` URL returning 200 |
| Structured data | `jsonld_errors` > 0 (invalid JSON); templates that should carry markup but have `jsonld_count` 0 |
| Images | `img_missing_alt` > 0 on content templates (`alt=""` is correct for decorative images and is not counted) |
| Faceted URLs | many 200 URLs that differ only by filter/sort parameters, crawlable and linked (count per parameter) |
| International | `hreflang_count` differs across pages of one locale set, or is 0 on a multi-locale site that does not declare hreflang in sitemaps or headers |

**Done when** every rule has a count (zero is a valid answer) and each non-zero issue has example URLs.

### 5. Spot-check what a crawl can't prove

Pick one URL per template plus every priority page.

```sh
curl -sSI https://www.example.com/page | grep -iE "^(HTTP|location|x-robots-tag|link|content-type|strict-transport|cache-control)"
# Raw vs rendered HTML: big differences in links, text or <head> tags mean the content depends on JavaScript
curl -sS https://www.example.com/page > raw.html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --dump-dom https://www.example.com/page > rendered.html   # Linux: google-chrome; Windows: chrome.exe
for f in raw.html rendered.html; do printf "%s links: " "$f"; grep -o "<a " "$f" | wc -l; done
```

- **JS rendering:** links must be `<a href>` in the rendered DOM; title, canonical, meta robots and main content should be in the raw HTML or at least identical after rendering. Confirm with Search Console URL Inspection > View crawled page.
- **Structured data:** validate a sample in Google's Rich Results Test (https://search.google.com/test/rich-results) for Google eligibility and the Schema Markup Validator (https://validator.schema.org) for general schema.org validity. Check Google's Search Gallery for which types still produce rich results.
- **hreflang:** for one URL per locale, confirm self-reference, return links from every alternate, valid codes (`en-GB`, not `en-UK`), absolute URLs that return 200 and are canonical, and an `x-default` where there is a selector or fallback page.
- **Search Console:** map Page indexing reasons ("Crawled - currently not indexed", "Duplicate, Google chose different canonical than user", "Soft 404", etc.) to the crawl findings.

**Done when** each template has a pass/fail for rendering, headers, structured data and (if relevant) hreflang.

### 6. Core Web Vitals

Field data (real users, 75th percentile) decides pass/fail; lab data explains why.

```sh
curl -sS "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https%3A%2F%2Fwww.example.com%2F&strategy=mobile&category=performance" -o psi.json
python3 -c "import json;d=json.load(open('psi.json'));le=d.get('loadingExperience') or {};m=le.get('metrics') or (d.get('originLoadingExperience') or {}).get('metrics') or {};print('field data:','none' if not m else 'origin' if not le.get('metrics') or le.get('origin_fallback') else 'URL');[print(k,v.get('percentile'),v.get('category')) for k,v in m.items()]"
# Lighthouse needs Node and Chrome; it emulates mobile by default (add --preset=desktop for desktop)
npx lighthouse https://www.example.com/ --only-categories=performance --output=json --output-path=lh.json --chrome-flags="--headless"
```

Good at p75: **LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1** (poor: LCP > 4 s, INP > 500 ms, CLS > 0.25). INP replaced FID as a Core Web Vital in March 2024. In the PSI API, `CUMULATIVE_LAYOUT_SHIFT_SCORE` is ×100 (10 = 0.10). No URL-level field data means low traffic: use origin data or the Search Console CWV report, which groups similar URLs. Lighthouse cannot measure INP; use Total Blocking Time as the lab proxy. Add `&key=API_KEY` for more than a handful of calls.
**Done when** each priority template has mobile field values (or "no field data") plus the top 1-3 Lighthouse opportunities.

### 7. Prioritise

Score each issue: **Priority = Impact (1-5) × Reach (1-4)**.

| Impact | Meaning |
|---|---|
| 5 | Blocks crawling or indexing of pages that matter (sitewide noindex, robots disallow, 5xx, broken canonical origin) |
| 4 | Sends signals to the wrong URL or wastes them (canonical conflicts, redirect chains/loops, hreflang errors, orphaned money pages, faceted URL crawl traps) |
| 3 | Degrades ranking or UX (poor CWV, duplicate/thin templates, JS-only links, depth > 3) |
| 2 | Hurts how results look or get clicked (missing/duplicate titles and descriptions, invalid structured data) |
| 1 | Hygiene (alt text on minor images, single-H1 style, sitemap lastmod) |

Reach: 1 = a few URLs, 2 = < 10 % of crawled URLs, 3 = 10-50 %, 4 = > 50 % or a whole template. Bump Reach by 1 (max 4) if any priority page is affected. **P1 ≥ 12, P2 6-11, P3 ≤ 5.**
**Done when** every issue has a score and the table is sorted by it.

### 8. Write the report and self-check

Fill the template below, then check: every issue has a count, examples and a verify step; heuristics are labelled as such; nothing is reported that only reflects crawler limits; sampled counts are labelled as samples; checks you could not run are listed.

## Output

```markdown
# Technical SEO audit: <host> (<date>)
**Scope:** <hosts, N URLs crawled of ~M known, sample or full> · **Data:** <crawl, GSC exports, PSI, ...>

## Summary
<3-5 sentences: the biggest risks, P1 count, what is healthy>

## Prioritised issues
| # | Priority | Issue | URLs affected | Examples | Why it matters | Fix | Verify by |
|---|---|---|---|---|---|---|---|
| 1 | P1 (5×4=20) | Product template canonical points to page 1 of category | 412 (38 %) | /p/a, /p/b | Google may index the category instead of products | Self-referencing canonical on product template | Re-crawl; canonical = URL on all 200 product pages; GSC "Duplicate, Google chose different canonical" falls |

## Core Web Vitals (mobile, p75 field data)
| Template | URL | LCP | INP | CLS | Status | Main lab cause |

## Checked and healthy
- <area>: <one line of evidence>

## Not checked / limits
- <e.g. JS-rendered links not crawled; no GSC access; sample of 500 URLs>
```

## Guardrails

- Crawl only sites the user owns or has permission to audit. Keep `--delay` ≥ 1 s on production unless the owner agrees otherwise; never bypass robots.txt or authentication.
- Recommend changes; do not edit robots.txt, redirects, canonicals or templates on a live site without explicit confirmation. A wrong robots.txt or noindex can deindex a site.
- Never recommend robots.txt `Disallow` to remove pages from the index: Google then cannot see the `noindex`. Use `noindex` (and keep the page crawlable) or remove the page with 404/410.
- Do not promise ranking or traffic gains. Say what a fix enables (crawling, consolidation, eligibility), not what it will earn.
- Do not report crawler artefacts as site faults: JS-only links, pages behind login, URLs beyond `--max-pages`, or hosts outside scope.
- Label length rules, word counts and depth limits as heuristics. Google publishes no title or description length limit.

## Common mistakes

| Mistake | Fix |
|---|---|
| Treating a 500-URL sample as the whole site | Say "in a sample of N"; give percentages, not totals |
| Calling every non-200 URL a problem | Only flag non-200 URLs that are linked internally, in the sitemap, or receive traffic |
| Treating `alt=""` as missing alt text | Empty alt is correct for decorative images; flag only missing attributes on content images |
| Using Lighthouse scores to say a page fails CWV | Pass/fail comes from field data (CrUX/Search Console) at p75; Lighthouse explains causes |
| Still reporting FID | INP replaced FID in March 2024 |
| Reporting "duplicate content penalty" | There is no penalty for ordinary duplication; the risk is split signals and the wrong URL being chosen |
| A canonical tag added to a page that also has noindex | Mixed signals: choose one (canonical to consolidate, noindex to exclude) |
| Fixing redirects but leaving internal links pointing at them | Update internal links to the final URL as well |

## Example

User: "Our blog traffic dropped after we moved to a new CMS. Can you audit https://www.example.com/blog?"

Agent: confirms permission and scope (`www`, `/blog` section, 1,000 pages), reads robots.txt (fine) and the sitemap (2,140 URLs, includes 310 old `/blog/?p=123` URLs), crawls with `--sitemap`, and finds: the article template's canonical points to `http://` URLs that 301 to `https://` (every post); 180 posts orphaned (in the sitemap, no internal link) because the new CMS dropped category archives; 310 old `?p=123` sitemap URLs 301 to new slugs, 96 via a 2-hop chain. Report: P1 canonical-to-redirect on the article template (4×4=16); P1 orphaned posts (4×3=12: 8 % of URLs is Reach 2, bumped to 3 because two priority guides are orphaned); P2 stale sitemap and redirect chains (4×2=8). Each row has examples, the fix, and "re-crawl and compare" as the verification step.
