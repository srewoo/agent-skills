# Channel specs and templates

Limits below were checked against platform help pages and 2026 third-party guides in October 2026. Platforms change them without notice, so tell the user to check before publishing anything that sits near a limit. "Working target" figures are conventions, not platform rules.

## Quick reference

| Channel | Hard limit | Working target | Notes |
|---|---|---|---|
| LinkedIn post | 3,000 characters (spaces, line breaks, hashtags and mentions count) | 900-1,800 | Feed cuts to "…see more" after about 3 lines; the cut isn't fixed, roughly 140-210 characters on mobile and more on desktop. Blank lines use up those 3 lines |
| X post | 280 weighted characters (free accounts) | ≤ 260 per post | Each URL counts as 23 (t.co wrapping), whatever its length. Most emoji and CJK characters count as 2; mentions and hashtags count in full; attached media counts 0. Premium accounts can post up to 25,000, but the timeline shows only the first 280 before "Show more", so write to 280 |
| X thread | 280 per post | 5-10 posts | The "1/" numbering counts toward the limit |
| Newsletter section | None | 150-300 words | Subject line: aim ≤ 50 characters (mobile clients truncate around 35-60). Preview text: 40-100 characters |
| Short video (TikTok, Reels, Shorts) | All accept 60+ seconds (YouTube Shorts up to 3 minutes; Reels and TikTok allow longer, and change often) | 20-60 seconds = 50-150 spoken words | Hook in the first 3 seconds ≈ 6-9 spoken words at ~150 words per minute |
| Carousel | LinkedIn: one PDF/PPT/DOC document per post, up to 300 pages and 100 MB. Instagram: up to 20 slides in the app, but only 10 through the API that scheduling tools use | 6-10 slides, ≤ 30 words each | Portrait 1080×1350 (4:5) or square 1080×1080. LinkedIn carousel *ads* are a different format (2-10 cards) |
| Pull-quote | None | ≤ 200 characters | Must fit on a quote card and in a post with attribution |
| Threads / Bluesky / Instagram caption | 500 characters / 300 graphemes / 2,200 characters | | Only if the user asks for these channels. Threads also allows an optional text attachment of up to 10,000 characters below the post. Bluesky doesn't shorten links, so a pasted URL counts in full |

## LinkedIn post

```
<Hook line 1: the most surprising fact, result or tension from the source. ≤ 140 characters on its own>
<Hook line 2 (optional): the stake or the twist>

<Body: 3-6 short paragraphs of 1-3 lines, blank line between them. One idea, developed. Concrete numbers from the source.>

<Takeaway: one line the reader can act on.>

<CTA: a question to invite comments, or "Full write-up: <link>" (some writers put links in the first comment; reach effects vary, so follow the user's practice)>

<0-3 relevant hashtags, optional>
```

- The hook must make sense without the body and must not be a question you then answer ("Ever wondered…?").
- First person if the author is posting; company "we" if it's a company page.
- Plain text only: LinkedIn doesn't render markdown, so `**bold**` shows as asterisks.

## X thread

```
1/ <Hook: the claim or result + why it matters. Stands alone; most people only read this post.>
2/ <Context: the problem in one sentence.>
3/ … one idea per post, each understandable on its own if quote-posted …
n-1/ <The single most useful takeaway.>
n/ <CTA + source link + credit: "Full post by @author: <link>">
```

- One idea per post. If a post needs "and also", split it.
- Put the link in the last post, not the hook, unless the user wants traffic over reach.
- Numbering: "1/" format. Don't write "1/n" totals before the thread is final.
- Standalone X post: same hook rules, ≤ 260 characters, one link at most.

## Newsletter section

```
Subject line (if this is the lead item): <≤ 50 characters, specific, no clickbait>
Preview text: <40-100 characters that add to the subject, not repeat it>

### <Section headline: the takeaway, not the topic>
<Opening sentence: why this matters to this list's reader now.>
<2-3 short paragraphs: the key point, one supporting example or number from the source, what to do with it.>
<CTA: "Read the full <post/report/talk> →" with link, or a reply prompt: "Reply and tell me…">
```

- Newsletter readers have opted in: you can be more conversational than on LinkedIn and assume more context.
- If several sections go into one issue, give each a different angle; don't repeat the same summary.

## Short-video script and hooks

Write 3 hook options, then one full script for the strongest.

```
Hook options (first 3 seconds, ≤ 9 spoken words each):
A. <Result-first: "We cut onboarding from 9 days to 2.">
B. <Contrarian, only if the source argues it: "Long onboarding emails don't work. Here's the proof.">
C. <Visual/pattern-break: "[holds up 900-word email] Nobody read this.">

Script (<n> seconds, ~<words> words):
| Time | Spoken (voice-over / to camera) | On-screen text | Visual |
| 0-3s | <hook> | <≤ 6 words> | <shot> |
| 3-15s | <setup> | | |
| 15-45s | <2-3 points, one sentence each> | | |
| 45-60s | <payoff + CTA: "Link in bio" / "Full post in comments"> | | |
```

- Spoken words: count about 2.5 per second. A 30-second script is about 75 words.
- On-screen text: keep it out of the bottom ~20% and the right edge, where app buttons and captions sit.
- Each hook must be true to the source. A contrarian hook is only allowed if the source actually argues against the common view.

## Carousel outline

```
Slide 1 (cover): <promise or result, ≤ 10 words> + author/brand name
Slide 2: <the problem or the "before">
Slides 3-8: <one point per slide: headline ≤ 8 words + ≤ 25 words of support>
Slide 9: <summary or checklist slide people will save>
Slide 10: <CTA + credit: "From <source title> by <author>">
Caption: <a LinkedIn-style post, 300-800 characters, that works without opening the carousel>
```

- One idea per slide. If a slide needs more than ~30 words, split it.
- Supply the outline and copy only; say that the user's designer or template sets visuals and fonts.

## Pull-quotes

```
"<verbatim sentence from the source, ≤ 200 characters>"
— <Speaker name>, <role/title if in source>, <source title> (<para / timestamp>)
```

- Verbatim only. You may cut words from the start or end of a sentence. Mark internal cuts with "…" and only when the meaning is unchanged. Remove "um", "you know" and false starts from transcripts the same way.
- Pick lines that make a claim or a surprising number, not generic lines ("Innovation matters").
- 3-5 quotes, ranked by how well each stands alone.
