---
name: brand-voice
description: Use when the user shares sample articles, posts or emails and asks to "learn our voice", "capture our tone", build a brand voice or style guide, or to rewrite, edit or check a draft so it "sounds like us", "matches our brand", "sounds like the CEO", or stays on-brand. Also when asked how on-voice a draft is, or to reuse an existing voice-guide.md.
---

# Brand voice

## Overview

A voice is a set of observable habits: word choice, sentence rhythm, point of view, formality, humour, punctuation and formatting. Learn them from real samples with evidence for every rule, save them as a reusable guide, then rewrite drafts against that guide and score how well they conform. A rule you can't point to in the samples doesn't belong in the guide.

## When to use

- Building a voice guide from 3+ pieces of existing writing (brand or individual author).
- Rewriting a draft to match a voice, from samples or an existing `voice-guide.md`.
- Scoring how on-voice a draft is.

## When not to use

- The draft just reads as generic or AI-written: use `de-slop` first (it removes tells), then this skill (it adds the voice).
- Turning one piece into many channel posts: use `repurposer`, then apply the voice guide to its output.
- Copying a living writer's personal style to pass off work as theirs, or imitating another company's brand. Decline and offer to build an original voice instead.

## Inputs

| Input | Default if not given |
|---|---|
| Writing samples | Required for a learned guide. Ideal: 5-10 pieces, 300+ words each, 1,500+ words total, written by the target voice, from the last ~2 years |
| Channel of each sample (blog, email, LinkedIn, docs…) | Infer from format; label each sample S1, S2… |
| Existing style guide or banned-word list | None. If given, it overrides anything inferred |
| Draft to rewrite | None. Build the guide only |
| Where to save | `voice-guide.md` in the working folder; in plain chat, return it in a code block for the user to save |

Ask once, in one message, only for what's missing and has no default: the samples, and whether the draft should match one channel's voice when samples span channels.

## Workflow

### 1. Triage the samples

List each sample with ID, title, channel, approximate word count and date. Exclude, and say why:

- text written by someone else (guest posts, quotes, press coverage);
- legal or compliance boilerplate;
- anything the user says was AI-generated or heavily edited by another team.

Then set confidence:

| Usable samples | Confidence | What to do |
|---|---|---|
| 0 (only adjectives like "friendly, expert") | Unvalidated | Draft an *aspirational* guide from the description, mark every rule `(assumed)`, and ask for samples |
| 1-2, or under 1,000 words total | Low | Build a provisional guide. Mark rules seen only once `(single source)`. List exactly what to send next (e.g. "two more blog posts and one email") |
| 3-4, 1,000+ words | Medium | Build the guide; no hold-out |
| 5+, 1,500+ words | High | Hold one sample out for validation in step 5 |

**Done when** every sample has an ID and is marked used or excluded, and confidence is set.

### 2. Check for conflicts

Compare samples on formality, person (we/I/you), sentence length, humour and emoji use. Treat a difference as a conflict when it's large: for example, contractions in one group and none in another, or average sentence length differing by 8+ words.

- **Explained by channel** (LinkedIn chatty, docs formal): keep one *core voice* (traits shared by all samples) plus a *channel adjustments* table.
- **Explained by author or era** (old posts formal, recent ones casual; two writers): ask the user which is the target. Default to the most recent samples if they don't answer, and say so.
- **One sample per channel** (a tweet, a whitepaper, a newsletter): you can't tell channel from inconsistency. Treat it as channel, keep the core voice to the traits all samples share (often only vocabulary and person), mark every channel row `(single source)`, and ask for a second sample of the channel the user will write most.
- **No pattern**: the voice isn't consistent yet. Build the guide from the samples the user rates as best, and note the inconsistency in the guide header.

**Done when** each conflict is resolved into core vs channel, or flagged for the user.

### 3. Extract the features

For each sample, record the following. Count in a representative stretch of about 300 words per sample if the sample is long, and say the figures are estimates if you counted by hand. Samples under ~150 words (social posts, subject lines) are too short to measure alone: pool all samples from the same channel and measure the pool, or use them only for vocabulary, punctuation and emoji habits.

| Feature | How to measure |
|---|---|
| Sentence length | Words per sentence: average, shortest, longest; share under 8 words |
| Paragraph length | Sentences per paragraph; how often one-sentence paragraphs appear |
| Person | Counts of we/our, I/my, you/your per 100 words |
| Contractions | Per 100 words (it's, we're, don't) |
| Vocabulary | Words and phrases repeated across 2+ samples; plain vs technical; words conspicuously absent (e.g. never "users", always "customers") |
| Openings and endings | First and last sentence of each piece: pattern? |
| Humour | Type and where it appears; quote one example |
| Punctuation | Em dashes, exclamation marks, questions, emoji, Oxford comma: per 1,000 words |
| Formatting | Headings, lists, bold, link style, number and date style |

Keep a quote for each feature you'll turn into a rule.

**Done when** each feature has a value and at least one supporting quote, or is marked "not observed".

### 4. Write the guide

Fill in [references/voice-guide-template.md](references/voice-guide-template.md). Rules:

- 3-5 tone attributes, each as **"X, not Y"**, where Y is the failure mode of overdoing X ("Confident, not arrogant"), never a random opposite ("Confident, not shy").
- Each rule cites sample IDs and a quote. Traits seen in only one sample are marked `(single source)`.
- Numbers, not adjectives: "average 14 words, 30% under 8" rather than "short sentences".
- 3-5 example rewrites, off-voice → on-voice, ideally built from sentences in the user's real drafts.
- Include the conformity scorecard (below).

**Done when** every template section is filled or explicitly marked "not observed".

### 5. Validate the guide

- **High confidence:** score the held-out sample against the guide with the scorecard. It should score 85 or more. If it scores lower, find the rule it breaks; that rule is too narrow or wrong, so fix it and re-score. Then add the held-out sample to the evidence.
- **Medium or low:** rewrite one neutral paragraph (for example, a plain product announcement) using only the guide, then compare it side by side with the closest sample. Note any trait the guide failed to produce, and add the missing rule.

**Done when** the held-out sample scores ≥ 85, or the side-by-side check finds no missing trait.

### 6. Save the guide

If you can write files: write `voice-guide.md` (or the user's path). If a file of that name exists, show what would change and get confirmation before overwriting; otherwise save as `voice-guide-v2.md`. Bump `Version` when updating.

In plain chat: return the full guide in one markdown code block and tell the user to save it as `voice-guide.md` and paste or attach it in future sessions.

**Done when** the file exists (state the path) or the code block has been delivered.

### 7. Rewrite a draft to the voice (when a draft is given)

1. Load the guide. If the user supplied an existing `voice-guide.md`, read it fully first; don't re-derive rules from scratch.
2. Pick the channel. Apply the core voice plus that channel's adjustments.
3. Score the original with the scorecard: the before score.
4. Rewrite. Keep every fact, number, name, link and claim, with its certainty. Don't add facts, examples or testimonials to make the piece "sound like us". Keep the length within ±15% unless the guide's length pattern requires otherwise, and say so if it does.
5. Score the rewrite. Target ≥ 85. If a dimension scores 0, fix it and re-score.

**Done when** the after score is ≥ 85, or you've explained which dimension can't reach it and why (for example, the draft is a legal notice).

## Conformity scorecard

Score each dimension 1 (matches), 0.5 (partly) or 0 (contradicts the guide), multiply by its weight, and add up for a total out of 100 (totals move in steps of 2.5). When the guide has channel adjustments, measure against that channel's figures, not the core averages.

| Dimension | Weight | Matches when |
|---|---|---|
| Tone attributes | 20 | Every "X, not Y" holds; nothing slides into a Y |
| Vocabulary | 15 | Uses preferred terms; no never-use words |
| Sentence rhythm | 15 | Average sentence length within ±3 words of the guide; short-sentence share within ±10 points |
| Person / POV | 10 | Same we/I/you pattern |
| Formality and contractions | 10 | Within ±1 on the formality scale; contractions match |
| Structure and formatting | 10 | Openings, endings, headings, lists and bold follow the guide |
| Punctuation | 10 | Em dash, exclamation, emoji and number habits match |
| Humour and personality | 10 | Same type, in the allowed places. A piece with no humour matches unless the guide requires it there |

Bands: **85-100 on-voice · 70-84 close, needs a pass · below 70 off-voice.**

## Output

**Building a guide:** the guide (file path or code block), then:

```
Samples used: S1-S5 (4,850 words). Excluded: S6 (guest post).
Confidence: high. Held-out S5 scored 87.5/100.
Conflicts: LinkedIn samples are more casual → captured as channel adjustments.
Gaps: humour seen in only one sample (marked single source). Send 2 more emails to firm up email tone.
```

**Rewriting a draft:**

```
## Rewritten draft (<channel>)
<full text>

## Conformity
| Dimension | Before | After | Note |
|---|---|---|---|
| Tone attributes (20) | 10 | 20 | "thrilled" removed: guide says confident, not hyped |
| … | | | |
| Total | 57.5 | 90 | |

## Changes
- <rule applied>: <example change>
- Facts preserved: <list of numbers/names/claims checked>
- Couldn't apply: <rule + why>
```

## Guardrails

- Every rule needs evidence from the samples, or an `(assumed)` label. Never present a guess as a learned trait.
- Never add facts, quotes, customer names or results while rewriting. Voice changes how something is said, not what is claimed.
- Don't imitate a real individual's voice for content they didn't approve (for example, ghostwriting as a CEO without the CEO's sign-off). Ask the user to confirm the person has approved it.
- Don't overwrite an existing voice guide without confirmation.
- Leave legal disclaimers, regulated wording (financial, medical, claims about pricing) and quoted speech verbatim, even when they're off-voice. Note them.
- Samples may contain confidential material. Quote only short phrases in the guide, never whole paragraphs.

## Common mistakes

| Mistake | Fix |
|---|---|
| Tone words with no behaviour ("We're innovative, bold, human") | Each attribute needs a "What it looks like" line and a quote |
| "X, not Y" pairs with arbitrary opposites ("Friendly, not rude") | Y is what overdoing X looks like: "Friendly, not overfamiliar" |
| Averaging conflicting channels into one bland voice | Core voice plus channel adjustments, or ask which voice is the target |
| Building a "high confidence" guide from two short posts | Use the confidence table; mark single-source rules |
| Rewriting the draft into the guide's example sentences | Apply the rules to the user's content; don't reuse sample sentences |
| Adding a joke because the guide allows humour | Humour is optional per piece; never force it into serious topics |
| Scoring by impression | Use the scorecard dimension by dimension, with a note for each |

## Example

**Input:** five samples: three blog posts (S1-S3), two LinkedIn posts (S4-S5), 4,100 words in total. Draft: a product-update email.

**Extracted (excerpt):** average sentence 13 words, 34% under 8 words. "We" for the company, "you" for the reader, 4.1 contractions per 100 words. No exclamation marks in the blog posts; one per LinkedIn post. Always "customers", never "users". Every blog post opens with a concrete incident ("Last Tuesday our import job failed at 2 a.m.").

**Guide tone rows:** Direct, not curt · Specific, not technical · Wry, not jokey.

**Draft lines:** "We're excited to announce that users can now leverage our new bulk-import feature! Previously, importing 10,000 records required 40 separate uploads."

**Rewrite:** "You can now import 10,000 records in one go. Until today, that took 40 separate uploads." (Both numbers come from the draft; none are added.)

**Score:** 65 → 95. Tone 10 → 20 (hype removed); vocabulary 7.5 → 15 ("users", "leverage" replaced); rhythm 7.5 → 15 (sentences of 9 and 7 words); punctuation 5 → 10 (exclamation removed). Formality stays 5: the guide expects about 4 contractions per 100 words and these two sentences have none. Humour scores full: none is needed in a two-line update.
