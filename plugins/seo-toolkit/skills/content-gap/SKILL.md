---
name: content-gap
description: Use when the user wants a content gap or competitor content analysis, asks what topics or keywords competitors rank for that their site doesn't, where competitors' pages beat theirs, what content to create next to catch up, or has a Semrush Keyword Gap or Ahrefs Competitive Analysis (Content Gap report) export to turn into a plan. Not for clustering a keyword list they already have or fixing technical SEO issues.
---

# Content Gap

## Overview

Compare what 2-5 search competitors cover against the site, then separate **missing pages** (topic absent) from **thin sections** (page exists but covers the topic worse). Rank opportunities by **business relevance × demand × winnability** and turn the top ones into briefs. Competitors show *which topics* matter; the site's own expertise supplies *what to say*. Never copy competitor content.

## When to use / When not to use

- Use for: competitor topic coverage, keyword-gap exports, "what should we write next", planning a content refresh against competitors.
- Not for: grouping or mapping a keyword list you already have (use `keyword-cluster`); crawl, indexing or speed problems (use `technical-seo-audit`); writing the full article.

## Inputs

Ask once, in one message, only for what has no default.

| Input | Default if not given |
|---|---|
| Your site | **Required.** Ask. |
| Competitors (2-5) | Ask. If the user names none, propose the domains that most often rank top-10 for their 5-10 core keywords and confirm. Search competitors can differ from business competitors |
| What the business sells and to whom | Ask in one line; it drives relevance scoring |
| Market and language | One country/language per analysis; default to the site's main market |
| Data | Best: a keyword-gap export. Also useful: your Search Console queries + pages, competitor sitemaps. See step 2 |
| Brief count | Top 10 opportunities |

**No shell (plain chat):** ask the user to paste the keyword-gap export (or each competitor's top-pages/organic-keywords export), their own ranking keywords or Search Console query export, and competitor sitemap URL lists or top-page lists. Without any data, you may draft a topic hypothesis from the user's description, but label every row "unvalidated: no demand data" and skip demand and winnability scores.

## Workflow

### 1. Fix the frame

Record: site, 2-5 competitors, market, the offer (products/services), and the audience. Exclude competitors that are marketplaces, forums or media giants unless the user wants them; their coverage isn't comparable.
**Done when** the frame fits in five lines and the user has confirmed the competitor list.

### 2. Collect evidence

Use what is available, best first:

1. **Keyword-gap export.** Semrush *Keyword Gap* (tabs: Missing = all competitors rank and you don't; Weak = you rank lower than all of them; Untapped = at least one ranks and you don't). Ahrefs *Competitive Analysis* tool > *Content Gap* report: by default, keywords at least one competitor ranks top-10 for while you are not in the top 100. Keep columns: keyword, volume, KD, each domain's position and URL.
2. **Your own rankings.** Search Console query + page data, or your Ahrefs/Semrush organic keywords export (needed to find thin sections).
3. **Competitor sitemaps.** URL inventory and how much each competitor publishes per section:
   ```sh
   curl -sS -A "Mozilla/5.0 (compatible; content-gap-research)" https://competitor.com/sitemap.xml \
     | grep -o "<loc>[^<]*</loc>" | sed -E 's#</?loc>##g' > competitor_urls.txt
   # A sitemap index lists child sitemaps: run the same command on each child file. For .xml.gz files, insert `| gunzip -c` after curl.
   cut -d/ -f4 competitor_urls.txt | sort | uniq -c | sort -rn | head -20   # pages per top-level section
   ```
4. **Headings of the competitor pages that rank** (read the competitor's robots.txt first and skip disallowed paths) for the biggest gap topics (subtopic coverage), at most ~5 pages per topic, one request every few seconds:
   ```sh
   python3 -c "import re,sys,urllib.request as u;h=u.urlopen(u.Request(sys.argv[1],headers={'User-Agent':'Mozilla/5.0'}),timeout=15).read().decode('utf-8','replace');[print(t.upper(),' '.join(re.sub(r'<[^>]+>',' ',x).split())) for t,x in re.findall(r'<(h[1-3])[^>]*>(.*?)</\1>',h,re.S|re.I)]" https://competitor.com/guide/topic
   ```
   (`py` on Windows.) Pages that render content with JavaScript return few headings; note that and skip them.
5. **SERP features** for the top gap keywords: featured snippet, People Also Ask, video, images, local pack, shopping, AI Overviews. They shape format and winnability. Take them from the tool's SERP-features column or a manual check.

**Done when** you have, per competitor, either gap keywords with positions or a URL inventory, plus your own ranking data, and you've listed which sources were missing.

### 3. Turn keywords and URLs into topics

- Group gap keywords into topics (one topic = one page's worth of intent). For more than ~200 keywords, cluster them first with the `keyword-cluster` approach (SERP overlap, else semantic).
- Map each competitor URL and each of your URLs to a topic by slug, title and headings.
- Drop topics outside the business frame from step 1 now, with a one-line reason.

**Done when** every remaining gap keyword belongs to a topic and each topic lists which competitors cover it (URL + position) and your best URL (or none).

### 4. Classify each topic

| Class | Rule |
|---|---|
| **Missing page** | You have no page on the topic, and ≥ 2 competitors rank top-20 with a dedicated page (1 competitor = "untapped", lower confidence) |
| **Thin section / weak page** | You have a relevant page, but it ranks below all competitors or beyond position 10 while ≥ 2 competitors rank top-10, **or** competitors' ranking pages cover subtopics (H2/H3s) yours lacks |
| **Parity / ahead** | You rank comparably or better: leave out of the plan |

**URL inventories only (no rankings):** classify by coverage instead: missing page = ≥ 2 competitors have a dedicated URL for the topic and you have none; thin section = you have a page but competitors have several pages (a cluster) on it. Label the class "coverage-based, rankings unknown".

For thin sections, name the missing subtopics (from step 2.4 headings and People Also Ask), not just "make it better". Check whether the right page ranks: a weak result can be cannibalisation or the wrong URL ranking, which is a `keyword-cluster` problem.
**Done when** each topic has exactly one class and, for thin sections, a list of missing subtopics.

### 5. Score

Score each topic 0-3 on three axes and multiply (max 27; any 0 drops it):

| Score | Business relevance | Demand (topic total volume or GSC impressions) | Winnability |
|---|---|---|---|
| 3 | Directly about what you sell; a reader could become a customer | Top third of topics in this dataset | Median KD of the topic ≤ median KD of keywords you already rank top-10 for, and the SERP has sites like yours |
| 2 | A problem your buyers have that your offer touches | Middle third | KD up to ~20 points above that median, or you already have a page to improve |
| 1 | Audience-adjacent, no product link | Bottom third | KD far above, or the SERP is dominated by big brands, marketplaces or forums |
| 0 | Irrelevant: drop | No measurable demand: drop unless strategic (say why) | Not realistically winnable |

Thin sections usually score higher on winnability than missing pages: the URL already has links and history. Demand terciles are relative to this dataset; say so.

No volume data (only competitor URLs): get volumes for the topic head terms from a free source such as Google Keyword Planner, or use **coverage as a demand proxy** (3 = all competitors have a page, 2 = two or more, 1 = one) and label the column "D (proxy)". Without your own ranking data, judge thin sections from heading coverage only and say so. Without KD or a SERP check, leave W blank, rank by R × D and label the score "R×D only (max 9)"; check the SERP manually for the top 10 before writing briefs.
**Done when** every topic has three scores, a product, and a one-line reason for its relevance score.

### 6. Write briefs for the top opportunities

Sort by score (ties: thin sections first, then higher demand). For the top N (default 10), write a brief:

- **Suggested title** (draft, under ~60 characters as a heuristic) and **page type** (guide, comparison, landing page, tool, template, glossary)
- **Intent** and **target cluster**: primary keyword + 3-8 secondary keywords with volumes
- **Target URL**: new slug, or the existing URL plus the section to add
- **Outline**: 5-10 H2/H3 bullets covering the subtopics searchers need (from the gap keywords, People Also Ask and the topic's common subtopics), written in your own words
- **Original angle**: what only this site can add (own data, product expertise, customer examples, original visuals). Required: a brief without one is not ready
- **SERP features to target** (e.g. answer the main question in 40-60 words for a snippet; video if the SERP shows video)
- **Internal links**: 2-3 existing pages to link from, and where this page should link to
- **Evidence**: competitor URLs and positions that show the gap

**Done when** each of the top N has every field filled, or a field marked "unknown" with the reason.

### 7. Self-check before returning

- Missing pages and thin sections are in separate tables.
- No outline line repeats a competitor's heading structure or wording; no competitor text is quoted beyond keyword phrases.
- Every score traces to data in the inputs; nothing is invented; unvalidated rows are labelled.
- Each brief has an original angle.
- Missing data sources are listed.

## Output

```markdown
# Content gap: <site> vs <competitors> (<market>, <date>)
**Data:** <exports, sitemaps, GSC> · **Not available:** <...>

## Summary
<3-5 sentences: biggest gaps, how many missing pages vs thin sections, quick wins>

## Missing pages
| # | Topic | Intent | Primary keyword | Topic volume | Competitors ranking (pos.) | R | D | W | Score |

## Thin sections on existing pages
| # | Your URL (pos.) | Topic | Missing subtopics | Competitors ranking (pos.) | R | D | W | Score |

## Prioritised briefs
### 1. <Suggested title> (Score 18, missing page)
- Page type · Intent · Target URL
- Target cluster: <primary (vol)>; <secondary (vol)>, ...
- Outline: <bullets>
- Original angle: <...>
- SERP features: <...> · Internal links: <from / to>
- Evidence: <competitor URL (pos.)>, ...

## Dropped topics
| Topic | Reason |
```

## Guardrails

- Never copy, paraphrase or "spin" competitor content, and never reuse their outline wholesale. Use competitors only as evidence that a topic has demand.
- Fetch competitor pages sparingly (sitemap plus a handful of pages, seconds apart), respect robots.txt, and never bypass logins or paywalls. Prefer tool exports over scraping.
- Don't invent search volumes, rankings or difficulty. When there is no data, say so and leave the score blank.
- Flag health, finance, legal and safety topics as needing a qualified expert to write or review.
- Recommend; don't publish, unpublish or redirect anything.

## Common mistakes

| Mistake | Fix |
|---|---|
| Using business rivals that don't rank for the same terms | Pick competitors that appear top-10 for the site's core keywords |
| One brief per gap keyword | Group keywords into topics first; one page per topic |
| Recommending a new page when one exists but is weak | Check your own URLs first: improve before creating (thin section) |
| Ranking by volume alone | Multiply relevance × demand × winnability; irrelevant traffic is worth nothing |
| Outline copied from the top-ranking competitor | Build from searcher questions and your own expertise; competitors only confirm coverage |
| Treating "Untapped" (one competitor ranks) like "Missing" | Lower confidence; check it is not a one-off |
| Mixing markets | One country and language per analysis |

## Example

User: "We sell payroll software for small businesses in the UK. Compare us with three competitors." They attach a Semrush Keyword Gap export (Missing + Weak tabs, 1,900 keywords) and a Search Console query export.

Agent confirms the market (UK), groups the gap keywords into 140 topics, drops 31 off-offer topics (e.g. "payroll jobs"), and classifies 64 as missing pages and 22 as thin sections. Top result: thin section, "/payroll-software/ ranks 14 for 'payroll for small business' while all three competitors rank top 5 with sections on pricing tiers, HMRC RTI submission and auto-enrolment that this page lacks" (R3 × D3 × W3 = 27). Second: missing page, "how to calculate holiday pay" (informational, two competitors rank top 5, R2 × D3 × W2 = 12). The output has both tables and 10 briefs, each with an original angle such as "anonymised payroll benchmarks from our customer base".
