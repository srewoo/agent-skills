---
name: repurposer
description: Use when the user wants to repurpose, atomise or turn one long piece (blog post, article, podcast or video transcript, webinar, whitepaper, report, conference talk) into social and channel content: a LinkedIn post, X/Twitter thread, newsletter blurb, Reels/TikTok/Shorts script or hooks, carousel slides, or pull-quotes. Phrases include "make posts from this", "content calendar from this article", "social snippets", "thread this".
---

# Repurposer

## Overview

Turn one long source into pieces that are native to each channel and stand alone, without adding anything the source doesn't say. Build a ledger of the source's facts and quotes first, write every piece from that ledger, then check each piece against its channel's limits and the ledger before returning it.

## When to use

- One long-form source needs to become posts for several channels.
- The user wants a specific subset ("just a thread and three quotes").
- A transcript needs to become shareable written content.

## When not to use

- Writing new content from a topic with no source: that's drafting, not repurposing.
- Making the pieces match a brand voice: run this skill, then `brand-voice` on the output (or pass the voice guide in as an input).
- Making a draft sound less AI-generated: use `de-slop`.
- Translating to another language. Repurpose first, then translate separately with a native reviewer.

## Inputs

| Input | Default if not given |
|---|---|
| Source (text, file or transcript) | Required. If given only a URL you can't fetch, or audio/video you can't transcribe, ask for the text or transcript |
| Channels | All six: LinkedIn post, X thread, newsletter section, short-video hooks + script, carousel outline, pull-quotes |
| Who is posting (person or company page) and their handle | Company "we"; credit the source author by name |
| Source link | `[SOURCE LINK]` placeholder |
| CTA goal (read the source, sign up, comment, book a demo) | Drive readers to the full source |
| Voice guide or banned words | None; plain, direct style |
| Audience | Infer from the source; state your inference |

Ask once, in one message, only if the source is missing or unreadable. Use defaults for everything else and list them at the top of the output.

## Workflow

### 1. Build the source ledger

Read the whole source. For transcripts, strip timestamps and filler first but keep speaker labels. Auto-transcripts mishear numbers ("fifteen" / "fifty", "sixty-two" / "62" / "6.2"): if a figure is garbled or implausible, log it as `F? "<as transcribed>" [VERIFY]` and keep it out of the pieces until the user confirms it. Then write a ledger:

```
Core message (one sentence): …
Author / speakers: … (role, as stated in the source)
Source title, date, link: …
Facts and numbers:   F1 "<claim>" (para 4 / 12:30) · F2 …
Quotable lines:      Q1 "<verbatim>" — <speaker> (para / timestamp) · Q2 …
Ideas (standalone):  I1 … I2 … (3-7 ideas, each one sentence)
Source's own CTA:    …
```

If the source contains no numbers or quotable lines, note that. Don't invent them later.

**Done when** the ledger has a core message, at least 3 ideas, and every number in the source appears as an F-item.

### 2. Plan the angle per channel

Give each channel a different entry point so the set doesn't read as one summary pasted six times. For example: the LinkedIn post leads with the personal lesson (I2), the thread walks through the steps (I1-I5), the video hook uses the most striking number (F3), and the newsletter explains why it matters this week.

**Done when** each requested channel has an assigned angle and the ledger items it will use.

### 3. Draft each piece

Use the templates and limits in [references/channel-specs.md](references/channel-specs.md). Rules for every piece:

- **Stands alone.** A reader who never sees the source or the other pieces understands it. No "as mentioned above", no "in this article". Define any term the piece relies on.
- **Ledger only.** Every fact, number and quote traces to a ledger item. No new statistics, examples, customer names or claims, and no rounding that changes meaning ("43%" may become "over 40%", never "half").
- **Attribution.** Quotes are verbatim and credited to the speaker. Credit the source author in at least the CTA or sign-off of each piece, unless the author is the poster.
- **Channel-native CTA.** LinkedIn: question or link. X: link in the final post. Newsletter: "read the full piece" link or a reply prompt. Video: "link in bio" / "full post in comments". Carousel: final slide.
- **Hook up front.** LinkedIn: the first ~140 characters carry the point. X: post 1 stands alone. Video: the first 3 seconds.
- **No markdown on social.** LinkedIn and X don't render `**bold**` or `#` headings. Use line breaks.

**Done when** every requested piece is drafted.

### 4. Check limits

If you can run Python 3.9+, put each channel's posts in a text file separated by lines containing only `---`, and run, from this skill's folder:

```
python3 scripts/char_count.py thread.txt --platform x          # 280, weighted; exit 1 if any post is over
python3 scripts/char_count.py linkedin.txt --platform linkedin  # 3,000, shows the "see more" preview
```

Before counting, swap `[SOURCE LINK]` for any URL (e.g. `https://example.com/x`): X counts every link as 23, but the placeholder is only 13.

In plain chat, count each post by hand and keep a safety margin: ≤ 260 for X posts and ≤ 2,800 for LinkedIn. Label hand counts "approx." in the output. Video scripts: count words (about 2.5 spoken words per second).

**Done when** every piece is within its limit, with the count shown.

### 5. Self-check every piece

- [ ] Every number and quote matches the ledger exactly (check digits and wording).
- [ ] No claim, example, statistic or name appears that isn't in the ledger.
- [ ] Each piece makes sense read alone, cold.
- [ ] Each quote is credited, and the source author is credited somewhere in each piece.
- [ ] Each piece has a CTA suited to its channel, and the CTAs aren't all identical.
- [ ] No two pieces open with the same hook.
- [ ] Hooks are true to the source: no contrarian framing, urgency or outcome the source doesn't support.
- [ ] Counts are shown and under the limits.

Fix and re-check anything that fails.

**Done when** all boxes are ticked for all pieces.

## Output

Start with a short header, then one section per channel, in this order, each with its count line:

```
Source: <title> by <author> · Core message: <one sentence>
Defaults used: <e.g. posting as company page; source link placeholder; all six channels>
Platform limits as of October 2026; platforms change them, so check before publishing.

## LinkedIn post  (1,214 / 3,000 characters · hook 128 characters)
<post>

## X thread  (7 posts · longest 251 / 280)
1/ … (212)
2/ … (198)

## Newsletter section  (214 words)
Subject: … (41 characters) · Preview: … (77 characters)
<section>

## Short video  (script 38 seconds · 96 words)
Hooks: A … B … C …   Recommended: A, because …
<script table>

## Carousel outline  (8 slides · caption 512 characters)
<slides>

## Pull-quotes
1. "…" — Speaker, Title (para / timestamp)  (118 characters)

## Trace
| Piece | Ledger items used |
|---|---|
| LinkedIn | F1, F3, Q2, I2 |
```

Mark counts "approx." when counted by hand. If the user asked for fewer channels, include only those sections, but keep the header and the Trace table.

## Guardrails

- Never add facts, figures, testimonials, customer names or results that aren't in the source. If a channel needs a number and the source has none, write without one.
- Never alter a quote's meaning or attribute words to the wrong speaker. Paraphrases go without quotation marks.
- Third-party material (a guest's words, a conference talk, someone else's article): remind the user to confirm they have the right to repurpose it, and always credit the original.
- Don't publish or schedule anything. Return drafts for the user to post.
- Regulated claims (financial returns, health outcomes, pricing, legal statements) are copied exactly with any qualifiers the source attaches, such as "results vary". Flag them for review.
- Source in a language other than the output language: ask which language the output should be in before writing.

## Common mistakes

| Mistake | Fix |
|---|---|
| The same summary trimmed to six lengths | Assign each channel a different angle in step 2 |
| Pieces that rely on the source ("In the article we explain…") | Each piece states its own point and context |
| Hook is a vague question ("Want better onboarding?") | Lead with the source's most concrete result or claim |
| A thread post that only works after reading the previous one | One full idea per post; repeat the subject noun instead of "this" or "it" |
| Rounding or "sharpening" numbers for punch | Copy figures as written; only round in a way that keeps meaning |
| Tidying a transcript quote until the speaker didn't say it | Drop "um", "you know" and false starts silently; mark any cut of real words with "…"; never reword |
| Markdown bold and headings pasted into LinkedIn | Use line breaks and plain text |
| Counting characters by eye with no margin | Run the script, or keep ≤ 260 / ≤ 2,800 and label "approx." |

## Example

**Source:** a 1,900-word blog post, "We rewrote our onboarding emails", by Dana Ortiz, Head of Lifecycle. Ledger: F1 emails were up to 900 words; F2 click rate rose from under 2% to 6.1% in the first month; F3 all five emails were changed at once; Q1 "We changed all five at once and can't say which change worked." (para 9). Core message: shorter, single-purpose onboarding emails lifted click rate from under 2% to 6.1%.

**X thread, post 1 (186 / 280, checked with the script):**

> 1/ Our onboarding emails ran up to 900 words. Click rate: under 2%.
>
> We rewrote them so each email does one job. First month: 6.1%.
>
> What changed, and the mistake we'd avoid next time 🧵

**Last post (152 / 280):**

> 7/ The mistake: we changed all five emails at once, so we can't say which change worked. Test one at a time.
>
> Full write-up by Dana Ortiz: [SOURCE LINK]

**Pull-quote:** "We changed all five at once and can't say which change worked." — Dana Ortiz, Head of Lifecycle (para 9) (64 characters including quotation marks)

Note what is absent: no "tripled revenue", no invented customer quote, and both figures appear exactly as the source states them.
