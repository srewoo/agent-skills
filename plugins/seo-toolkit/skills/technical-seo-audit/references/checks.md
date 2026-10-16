# Technical SEO checks: detection, fix, verification

Load this when writing findings. Each block: **Detect** (from crawl columns or a command), **Fix**, **Verify**. Thresholds marked *heuristic* are conventions, not search-engine rules.

## Crawlability

**robots.txt**
- Detect: `Disallow` rules covering pages that should rank, or `/*.js` / `/*.css` / asset folders (Google needs them to render). `blocked_by_robots` rows in the crawl. A staging robots.txt (`Disallow: /`) shipped to production.
- Know: robots.txt controls crawling, not indexing. A blocked URL can still be indexed from links ("Indexed, though blocked by robots.txt" in Search Console) and its `noindex` is never seen. Google has ignored `noindex` inside robots.txt since September 2019. 4xx other than 429 is treated as "no robots.txt" (crawl everything). On 429 or 5xx Google stops crawling the site for 12 hours, then uses the last good copy for up to 30 days (no copy = no restrictions); after that it behaves as if there is no robots.txt if the site is otherwise available. Google follows at least 5 redirect hops for robots.txt itself.
- Fix: remove the over-broad rule; use `noindex` for pages that must stay out of the index.
- Verify: Search Console robots.txt report; re-crawl shows no `blocked_by_robots` on wanted pages.

**XML sitemaps**
- Detect: sitemap URLs with status ≠ 200, `noindex`, canonical pointing elsewhere, or a different host/protocol; indexable 200 pages missing from the sitemap; files > 50,000 URLs or > 50 MB uncompressed (split and use a sitemap index).
- Know: Google ignores `<priority>` and `<changefreq>` and uses `<lastmod>` only when it is consistently accurate.
- Fix: generate the sitemap from the same source as canonical, indexable URLs; list it in robots.txt (`Sitemap: https://…`) and submit it in Search Console.
- Verify: re-crawl with `--sitemap`; every `in_sitemap` row is 200, indexable and self-canonical.

**Status codes**
- Detect: 4xx/5xx with `inlinks` > 0 or `in_sitemap` true; `error` column (timeouts, DNS, TLS); soft 404s = 200 pages whose content says "not found" or is empty (low `word_count`, generic title). Spot-check soft 404s by viewing.
- Fix: restore, 301 to the closest equivalent, or return 404/410 and remove internal links. Fix 5xx at the server; persistent 5xx reduces crawl rate.
- Verify: re-crawl; Search Console Page indexing "Not found (404)", "Server error (5xx)", "Soft 404" trend down.

**Redirects**
- Detect: chains (A → B → C), loops, internal links to any 3xx, 302/307 for permanent moves, redirects to the homepage for removed deep pages (often treated as soft 404s).
- Know: Googlebot follows up to 10 hops, but each hop costs crawl time and risks failure; aim for one hop. 301/308 = permanent; 302/307 = temporary (Google treats long-lived temporary redirects as permanent eventually, but say what you mean).
- Fix: point every source straight at the final URL; update internal links, canonicals, hreflang and sitemaps to the final URL.
- Verify: `curl -sSIL URL | grep -iE "^(HTTP|location)"` shows one hop; re-crawl finds no internal links to 3xx.

**Orphan pages**
- Detect: `in_sitemap` true and `depth` empty; also Search Console or analytics landing pages missing from the crawl.
- Fix: link from relevant hub/category pages and related content, or retire the page if it has no purpose.
- Verify: re-crawl; page has `depth` and `inlinks` > 0.

**Internal linking depth**
- Detect: priority pages at `depth` > 3 (*heuristic*); pages with `inlinks` = 1; important pages linked only from paginated archives.
- Fix: hub pages, breadcrumbs, related links, HTML sitemaps for large catalogues.
- Verify: re-crawl depth distribution.

## Indexability

**Meta robots / X-Robots-Tag**
- Detect: `noindex` in `meta_robots` or `x_robots_tag` on wanted pages; `nofollow` on whole templates; `X-Robots-Tag: noindex` sent sitewide by a CDN or staging config (`curl -sSI`). Both a `robots` and a `googlebot` meta can exist; the most restrictive applies.
- Fix: remove from wanted pages; use X-Robots-Tag for PDFs and other non-HTML files.
- Verify: URL Inspection shows "Indexing allowed"; re-crawl.

**Canonicals**
- Detect, for indexable 200 pages: missing canonical; canonical → non-200, redirect, `noindex` page, other host, or `http://` on an https site; canonical chains (A → B, B → C); relative canonical resolving to the wrong URL; more than one canonical (Google may ignore all of them); canonical placed in `<body>` (ignored); canonical changed by JavaScript; paginated pages all canonicalised to page 1 (hides items on later pages); conflict with hreflang, sitemap or internal links.
- Know: canonical is a hint. Google weighs it against redirects, internal links, sitemaps and hreflang; consistent signals win. Search Console "Duplicate, Google chose different canonical than user" means the signals disagree.
- Fix: self-referencing absolute canonical on every indexable page; duplicates canonicalise to the preferred URL; all other signals point to the same URL.
- Verify: re-crawl; URL Inspection "Google-selected canonical" equals "User-declared canonical".

**AI Overviews and AI Mode**
- Know: Google's eligibility rule is simply indexed and eligible for a snippet; no special markup, schema type or file is required, and Google Search does not use `llms.txt`. `nosnippet`, `data-nosnippet`, `max-snippet` and `noindex` limit what is shown; the `Google-Extended` robots token governs use in other Google AI systems, not Search. Search Console counts AI feature traffic inside Performance > Web.
- Detect: only what blocks normal indexing or snippets (robots, noindex, `nosnippet` set by accident). Do not invent "AI SEO" checks.

**noindex in sitemap**
- Detect: `in_sitemap` true and `noindex` present. Mixed signal: remove from the sitemap or remove the `noindex`.

## Duplicate content

- Detect: identical `title` + `meta_description` (and similar `word_count`) across URLs; URL variants returning 200: trailing slash, upper/lower case, `index.html`, `?utm_*`, sort/filter/session parameters, http/https, www/non-www, print pages.
- Know: ordinary duplication is not penalised; the cost is split signals, wasted crawl and Google choosing a different URL. Search Console's URL Parameters tool was retired in 2022.
- Fix: 301 host/protocol/slash/case variants; canonical for parameter variants; don't link internally to parameter URLs; consolidate or differentiate genuinely overlapping pages.
- Verify: re-crawl; duplicates resolve to one 200 URL.

## Faceted navigation

- Detect: crawl stats per parameter (count URLs by `?param=`); thousands of 200 filter/sort combinations linked with plain `<a href>`; empty filter combinations returning 200 (soft 404s); parameters in inconsistent order or with duplicate keys; Search Console Crawl stats dominated by parameter URLs.
- Know: Google's faceted navigation guidance (December 2024): if filtered URLs need not be indexed, disallow them in robots.txt or use URL fragments (`#`), which Google ignores for crawling; if some facets should rank (e.g. "red running shoes" with real demand), give them clean, stable URLs, consistent parameter order with `&`, and return 404 for empty combinations. `rel="canonical"` and `nofollow` reduce crawling of facets only slowly and inconsistently.
- Fix: decide which facets have search demand (use `keyword-cluster`/`content-gap` data) and make those indexable landing pages; block or fragment the rest. If facets are already indexed and you want them out, `noindex` first, then disallow once they drop.
- Verify: re-crawl count of parameter URLs; Search Console Crawl stats share of requests to parameter URLs falls.

## Titles, meta descriptions, headings

- Detect: missing or empty; duplicated across URLs; boilerplate-only ("Home", "Untitled"); titles longer than ~60 characters or descriptions longer than ~160 (*heuristic*: Google truncates by pixel width and frequently rewrites both).
- Fix: unique title per indexable page with the main topic first and the brand last; descriptions that summarise the page and give a reason to click.
- Headings: `h1_count` 0 on content templates means the main heading is missing or styled as a `div`. Multiple H1s are valid HTML and not a Google problem; flag only if the template is meant to have one. Heading levels should follow the outline, not styling.
- Verify: re-crawl; Search Console Performance CTR for affected pages (lagging indicator).

## hreflang

- Detect: missing return links (A → B but not B → A); no self-reference; invalid codes (language is ISO 639-1 like `en`; region is ISO 3166-1 alpha-2 like `GB`; `en-UK` is invalid, `en-GB` is valid); hreflang URLs that redirect, 404, are `noindex` or are not canonical; hreflang on pages canonicalised to another locale; missing `x-default` where a language selector or global fallback exists.
- Fix: generate hreflang sets from one source (page head, HTTP header or sitemap: choose one method), each page listing itself and all alternates with absolute canonical URLs.
- Verify: crawl each locale and diff the hreflang sets; in Search Console, filter Performance by country and check the right locale URL ranks (the International Targeting report was retired in 2022).

## Structured data

- Detect: `jsonld_errors` > 0 (invalid JSON, so the block is ignored); missing required properties; markup describing content not visible on the page; types that no longer produce Google rich results (HowTo was removed in 2023; Course Info, Claim Review, Estimated Salary, Learning Video, Special Announcement and Vehicle Listing were phased out in 2025; Practice Problem in January 2026; FAQ rich results stopped appearing in May 2026; check Google's Search Gallery for the current list). Removed types do no harm and can stay if other consumers use them.
- Validate: Google Rich Results Test (https://search.google.com/test/rich-results) for Google eligibility; Schema Markup Validator (https://validator.schema.org) for schema.org syntax. Search Console enhancement reports show sitewide errors.
- Fix: JSON-LD in the template, generated from the same data that renders the page.
- Verify: Rich Results Test passes on one URL per template; enhancement report errors decline.

## Core Web Vitals

| Metric | Good (p75) | Poor | Typical causes |
|---|---|---|---|
| LCP | ≤ 2.5 s | > 4 s | slow server (TTFB), render-blocking CSS/JS, lazy-loaded or unoptimised hero image, client-side rendering |
| INP | ≤ 200 ms | > 500 ms | long main-thread tasks, heavy third-party scripts, large DOM, expensive event handlers |
| CLS | ≤ 0.1 | > 0.25 | images/iframes/ads without dimensions, late-injected banners, web-font swaps |

- INP replaced FID in March 2024. Field data: CrUX via PageSpeed Insights, the CrUX API or the Search Console CWV report (28-day rolling, mobile and desktop separately). Lab: Lighthouse (cannot measure INP; use Total Blocking Time as proxy).
- Fixes: preload or `fetchpriority="high"` on the LCP image and never lazy-load it; serve WebP/AVIF at the displayed size; inline critical CSS and defer non-critical JS; break up long tasks; reserve space with `width`/`height` or `aspect-ratio`; audit third-party tags.
- Verify: Lighthouse before/after for causes; field data needs up to 28 days to reflect a fix.

## Mobile

- Google indexes the mobile version (mobile-first indexing). The Mobile-Friendly Test and Search Console Mobile Usability report were retired in December 2023: use Lighthouse and a real device instead.
- Detect: `has_viewport` false; content, links, structured data or meta robots present on desktop but missing from the mobile render; tap targets and font sizes in Lighthouse.

## HTTPS and mixed content

- Detect: `http://` URLs returning 200 instead of 301; `mixed_content` > 0 (http subresources on https pages); certificate errors in the `error` column; no `Strict-Transport-Security` header.
- Fix: 301 all http to https; update hard-coded asset URLs; add HSTS (`max-age=31536000; includeSubDomains`) once https is stable everywhere.

## JavaScript rendering

- Detect: raw vs rendered HTML differ in title, canonical, meta robots, main text or links; links built with `onclick` or `<span>` instead of `<a href>`; content loaded only after scroll or click; routes that return 200 with an empty shell for missing pages (soft 404s); `#` fragment routing.
- Know: Google renders JavaScript, but rendering can lag crawling and other search engines and AI crawlers often do not render. Dynamic rendering is a workaround Google no longer recommends.
- Fix: server-side rendering or static generation for indexable routes; real `<a href>` links; return real 404 status codes from the server.
- Verify: URL Inspection > View crawled page shows content and links; crawl of rendered HTML (or a JS-capable crawler) matches.

## Images

- Detect: `img_missing_alt` > 0 on content templates; images over ~200 KB above the fold (*heuristic*); no `width`/`height`; important images as CSS backgrounds (not indexed as images); legacy formats where WebP/AVIF would do.
- Fix: descriptive alt for informative images, `alt=""` for decorative ones; responsive `srcset`; modern formats; lazy-load below the fold only.
