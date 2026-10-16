---
name: keyword-cluster
description: Use when the user has a keyword list or export (Ahrefs, Semrush, Search Console, Keyword Planner) and asks to cluster or group keywords, classify search intent, pick a primary keyword per page, build a keyword-to-URL map or content architecture, or check keyword cannibalisation (several of their pages competing for the same queries). Not for finding topics competitors cover that the site lacks.
---

# Keyword Cluster

## Overview

A cluster is the set of keywords one page can rank for. Search results are the ground truth: keywords whose top-10 results share 3-4+ URLs belong on the same page; keywords that only look alike may not. Group by intent first, then topic; give each cluster one primary keyword and one URL, and flag clusters where several of the site's URLs compete.

## When to use / When not to use

- Use for: turning a raw keyword export into a page plan, intent labelling, mapping keywords to existing URLs, cannibalisation checks, site-architecture planning.
- Not for: finding topics competitors rank for and the site doesn't (use `content-gap`); technical duplicate-URL problems such as parameters or canonicals (use `technical-seo-audit`); writing the content itself.

## Inputs

Ask once, in one message, only for what has no default.

| Input | Default if not given |
|---|---|
| Keyword list (file or pasted) | **Required.** Ask. |
| Site URL / list of existing pages | Ranking URLs in the export; else the site's sitemap; else map to "new page" only |
| SERP data (top-10 URLs per keyword) | None: fall back to lexical + semantic clustering and say so |
| Brand terms | Domain name without TLD (for navigational intent) |
| Market and language | The export's database/country; all keywords must share one |
| Scope | All keywords; drop rows with no volume/impressions only if the user agrees |

### Accepted exports

| Source | Export | Columns used |
|---|---|---|
| Ahrefs | Site Explorer > Organic keywords | Keyword, Volume, KD, Current position, Current URL |
| Ahrefs | Keywords Explorer | Keyword, Volume, Difficulty, Parent Topic (SERP-based grouping hint; the CSV header may read "Parent Keyword"), Intents |
| Semrush | Organic Research > Positions | Keyword, Position, Search Volume, Keyword Difficulty, URL |
| Semrush | Keyword Magic Tool | Keyword, Intent (may be several labels, e.g. "Commercial, Transactional"), Volume, Keyword Difficulty |
| Search Console | Performance > Export (zip): `Queries.csv` | Top queries, Impressions (demand proxy), Position. No URL: get query + page pairs from the Search Console API, Looker Studio or the BigQuery bulk export |
| Google Ads | Keyword Planner | Keyword, Avg. monthly searches (often a range like "1K - 10K"). "Competition" is ad competition, not SEO difficulty |
| Anything else | CSV/TSV | Any column named like keyword/query plus optional volume, KD, position, URL |

Exports with a keyword appearing on several rows with different URLs are kept: that is the cannibalisation signal.

## Workflow

### 1. Load and clean

With a shell, run the script (Python 3.9+, no packages; `py` on Windows):

```sh
python3 scripts/cluster.py keywords.csv --brand acme --output clusters.csv
python3 scripts/cluster.py keywords.csv --brand acme --level keyword --output keyword_map.csv
```

Read the stderr line (`N keywords -> M clusters ... Columns: keyword='Keyword', volume='Search Volume', ...`) and confirm the right columns were detected. If not, pass `--map volume='Exact Header'` (fields: keyword, volume, kd, position, url, intent). A tool `Intent`/`Intents` column is copied to `tool_intent` in the `--level keyword` output. UTF-16 and tab-separated files and Keyword Planner's title lines are handled.

Remove off-topic and out-of-market keywords before trusting clusters; list what you removed.
**Done when** the detected columns are correct and the keyword count matches the file minus duplicates and removals.

**No shell (plain chat):** read the pasted rows, normalise case and whitespace, merge duplicates (keep max volume, best position, all URLs), and continue with the same rules by hand. Above ~300 keywords, ask for the file in batches by topic, or recommend running the script.

### 2. Choose the clustering method

1. **SERP overlap (gold standard).** For each keyword, collect the top-10 organic URLs for the target market and device. Two keywords belong together when they share **≥ 3** URLs (loose; good for broad topics) or **≥ 4** (strict; good for sites that want fewer, tighter pages). Sources: a SERP API, a rank tracker's SERP export, Semrush's or Ahrefs' SERP overviews, or a manual incognito check for the top 20-50 keywords by volume. Save as `keyword,url,position` rows and run:
   ```sh
   python3 scripts/cluster.py keywords.csv --serp serp.csv --min-overlap 3 --output clusters.csv
   ```
   Keywords without SERP rows fall back to lexical clustering in the same run (`method` column says which).
2. **Lexical + semantic (fallback when there is no SERP data).** The script groups keywords whose stemmed content words overlap (Jaccard ≥ `--threshold`, default 0.6; 0.5 merges "mens running shoes" with "trail running shoes") and whose intents are compatible. It cannot see synonyms ("cv" / "resume", "affordable" / "cheap") or different meanings of the same word ("jaguar price" / "jaguar habitat"). Review its output and merge or split by meaning yourself. Label the result "semantic, not SERP-validated".

If the export has an `Intent`/`Intents` column (`tool_intent`) or Ahrefs' `Parent Topic`, use them as a second opinion: both come from SERP data. A keyword with several tool intents is mixed; check its SERP before assigning a page type.
**Done when** every keyword has a cluster and the method used is recorded per cluster.

### 3. Validate intent

The script's intent is a rule-based guess from modifiers: informational (starts with how/what/why…, or guide, tips), navigational (login, sign in), transactional (buy, price, pricing, near me), commercial (best, top, vs, review, alternatives); a bare `--brand` query with no modifier is navigational ("acme pricing" stays transactional); else `unclear`. Confirm against the live SERP for every cluster with large volume, `unclear` intent, or a `mixed:` intent:

| SERP mostly shows | Intent | Page type |
|---|---|---|
| Guides, definitions, videos, People Also Ask | Informational | Article, guide, glossary |
| Listicles, comparisons, reviews | Commercial | Comparison, "best X", alternatives page |
| Product/category pages, prices, shopping results | Transactional | Product, category, pricing, service page |
| One brand's own pages | Navigational | That brand's page (yours, or not a target) |

Split a cluster when its keywords need different page types. A SERP that mixes types means Google is unsure: target the dominant type and note it.
**Done when** no cluster is `unclear` or `mixed` without a written decision.

### 4. Pick the primary keyword

Default: the highest-volume keyword whose intent matches the cluster (the script's `primary_keyword`). Without volume data the script falls back to alphabetical order, so choose the most general phrasing that still matches the page's intent. Override when a lower-volume variant is more specific to the page, converts better, or the head term's SERP has a different intent. Note KD only as a tie-breaker.
**Done when** each cluster has one primary keyword and 2-10 notable secondary keywords listed.

### 5. Map clusters to pages

For each cluster, in this order:

1. **One own URL ranks** (position ≤ 20 in the export): map to it.
2. **Several own URLs rank** (`action` says `CANNIBALISATION CHECK`): confirm in Search Console (Performance > filter by query > Pages tab). It is real cannibalisation when the URLs swap positions over time or split impressions with neither ranking well. It is fine when they target different intents or rank together near the top. Recommend one of: merge into the stronger URL and 301 the other; re-target the weaker page to a different cluster; differentiate titles/H1/content; point internal links with the primary keyword at the chosen URL. Canonical only when the pages are true duplicates.
3. **No URL ranks but an existing page is the obvious match** (by title/H1 from the sitemap or a crawl): map to it and mark "optimise".
4. **Nothing fits:** "new page", with the page type from step 3 and a suggested slug.

Also flag the reverse: one URL mapped to several clusters with different intents.
**Done when** every cluster has exactly one target URL or "new page", and every cannibalisation candidate has a recommendation.

### 6. Self-check before returning

- Every keyword appears in exactly one cluster; totals match the input.
- The method (SERP or semantic) and the overlap/threshold are stated.
- No two clusters map to the same URL unless intentionally merged.
- Volumes and positions come from the input; nothing is invented. Unknown values are blank.
- Intent labels that were not checked against a SERP are marked "guess".

## Output

```markdown
## Keyword clusters: <site>, <market> (<N> keywords → <M> clusters, method: SERP overlap ≥3 | semantic)

| # | Primary keyword | Intent | Keywords | Total volume | Avg KD | Best pos. | Target URL | Action |
|---|---|---|---|---|---|---|---|---|
| 1 | crm software | Commercial | 14 | 18,300 | 76 | 8 | /crm | Cannibalisation: /crm vs /features |
| 2 | how to choose a crm | Informational | 6 | 1,100 | 25 | 22 | /blog/choose-crm | Optimise |
| 3 | crm for real estate | Commercial | 5 | 900 | 31 | — | New page: /crm/real-estate | Create (landing page) |

## Page map
| Target URL | Cluster(s) | Primary keyword | Secondary keywords | Page type | Action |

## Cannibalisation
| Cluster | Competing URLs | Evidence | Recommendation |

## Notes
- Removed: <keywords and why> · Method limits: <e.g. semantic only for 120 keywords without SERP data>
```

Attach the script's CSV (`--level keyword`) as the full keyword-to-cluster mapping.

## Guardrails

- Never redirect, delete, merge or noindex pages yourself. Cannibalisation output is a recommendation; consolidation changes traffic and must be approved by the site owner.
- Don't invent search volume, difficulty or SERP data. If none is supplied, cluster without it and say so.
- Keep one market and language per run; volumes and SERPs differ by country.
- Treat competitor brand keywords as navigational for that competitor; target them only with genuine comparison or alternatives pages.
- Don't use Keyword Planner "Competition" as SEO difficulty.

## Common mistakes

| Mistake | Fix |
|---|---|
| Grouping by shared words only | Validate big clusters on the SERP; split when page types differ |
| One page per keyword | Keywords that share SERPs belong on one page; separate pages compete with each other |
| Calling any two ranking URLs cannibalisation | Check Search Console for position swapping or split impressions first |
| Primary keyword = highest volume, always | Choose the term whose SERP matches the page type and business goal |
| Mixing countries or devices in SERP data | Collect SERPs for one market and device |
| Dropping zero-volume keywords | Tool volumes undercount long-tail; keep Search Console queries with impressions |
| Comparing SERPs that include ads or features | Compare organic URLs only, normalised (no scheme, `www` or trailing slash) |

## Example

User pastes a Semrush Positions export (420 keywords, URL column) for a CRM vendor and asks for a content map.

Agent runs `cluster.py --brand acme`, confirms the detected columns, and removes 18 job-search keywords ("crm jobs"). The script returns 96 clusters; 3 are `mixed`. The agent checks the SERPs for the top 15 clusters, splits "crm pricing" (transactional, pricing page) from "crm software" (commercial, listicles dominate), and merges "customer database software" into "crm software" (same meaning; 4 shared top-10 URLs in a manual check). Output: 96 clusters, 69 mapped to existing URLs (6 of them cannibalisation candidates), and 27 new pages with page types and slugs. One cannibalisation case is /crm vs /features for "crm software", with a recommendation to differentiate /features and point "crm software" internal links at /crm.
