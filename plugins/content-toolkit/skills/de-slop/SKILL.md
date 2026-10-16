---
name: de-slop
description: Use when a draft "sounds like AI", "sounds like ChatGPT", reads generic, robotic or corporate, or the user asks to humanise, de-slop, de-AI, make it sound human, or remove words like delve, leverage, seamless, tapestry, or overused em dashes, emoji bullets and "It's not X, it's Y" lines from a blog post, email, LinkedIn post, landing page or newsletter. Also when asked to score or audit a text for AI tells.
---

# De-slop

## Overview

Remove the patterns that make writing read as machine-generated, and keep everything else: the facts, the meaning, the technical terms and the author's own voice. Diagnose first, then rewrite, then measure again. A cleaner draft that adds a claim or loses a fact has failed.

## When to use

- A draft (yours, a colleague's or a model's) reads as AI-written and needs to sound like a person.
- The user wants an audit only: "how AI does this sound?", "score this".
- Before publishing copy produced by any generator.

## When not to use

- Matching a specific company or author voice from samples: use `brand-voice` (run de-slop first, then brand-voice).
- Turning one piece into channel posts: use `repurposer`.
- Fact-checking or line-editing for grammar alone. De-slop doesn't verify claims; say so if the user seems to expect it.
- Detecting whether a text *was* written by AI for academic or HR decisions. Tell counts are style signals, not evidence of authorship.

## Inputs

| Input | Default if not given |
|---|---|
| The draft (pasted text or a file) | Required. Ask for it if missing |
| Audience and channel | Infer from the text (blog, email, LinkedIn…) |
| Length target | Within ±15% of the original word count |
| Author samples or known habits to keep | None. Without samples or the user's word, treat em dashes, emoji and bold as candidate tells, like everything else |
| Mode | Rewrite + report. "Audit only" if the user asks for a score or review |

Only ask about the draft itself. Everything else has a safe default; state the defaults you used in the summary.

## Workflow

### 1. Read and note what must survive

Read the whole draft once. Write down, for yourself:

- every fact: numbers, dates, names, quotes, claims, links, product and feature names;
- technical terms, even ones on the tell list ("robust regression", "financial leverage");
- deliberate style the user named or that shows up in author samples they supplied: a recurring sign-off, fragments used on purpose, a house style for headings;
- the word count (count it, or estimate from lines × words-per-line and say it's an estimate).

**Done when** you have a fact list and a word count.

### 2. Diagnose: count the tells

If you can run Python 3.9+, run the bundled scorer from this skill's folder:

```
python3 scripts/slop_score.py draft.md          # a file
python3 scripts/slop_score.py - < draft.txt     # or stdin
python3 scripts/slop_score.py draft.md --json   # machine-readable
```

It reports hits per category with line numbers, sentence-rhythm variation, and a 0-100 score.

If you can't run scripts (plain chat), score by hand with [references/tells.md](references/tells.md):

1. Go through the catalogue section by section and list each hit with a short quote.
2. Points: 1 per hit (1.5 for structure tells); 2 for each sycophantic line and each "In today's … world" opener. Free allowances: the first question-opener paragraph, the first "X, Y and Z" triad (then 0.5 per triad beyond 1 per 200 words), and em dashes up to 1 per 200 words.
3. Score = points ÷ (words ÷ 100) × 20, capped at 100. Add 20 if five consecutive sentences are all 12-25 words long (flat rhythm). This approximates the script; label it a manual estimate.

Bands: **0-15 clean · 16-40 some tells · 41-70 heavy · 71-100 saturated.**

Read the hits, not just the band. Under ~150 words a single tell moves the score 13+ points. In technical writing, check each vocabulary hit against "Leave these alone" in the catalogue before counting it ("leverage" a connection pool is plain engineering English). The script also misses idioms ("hit the ground running", "streamlined", "revamped"); catch those by reading.

If the score is 0-15 and the user didn't ask for edits, report that the draft is already clean, list any hits, and stop. Don't rewrite clean prose for the sake of it.

**Done when** you have a hit list grouped by category and a "before" score.

### 3. Rewrite

Work paragraph by paragraph, in this order, using the "Replace with" column of the catalogue:

1. **Delete** sycophantic openers and closers, signposting ("Let's dive in") and throat-clearing ("It's important to note").
2. **Replace** inflated vocabulary with the plain word, or better, the specific fact the vague word stood in for, as long as that fact is already in the draft.
3. **Restructure** contrast framing, colon reveals, question openers and recap conclusions into direct statements.
4. **Fix formatting**: cut bold to terms a skimmer must find, turn emoji bullets into plain bullets or prose, reduce em dashes to about 1 per 200 words (unless step 1 showed they're the author's habit).
5. **Vary rhythm**: in each paragraph, make sure at least one sentence is under 8 words or over 25, unless it's step-by-step instructions.
6. **Make examples specific** using details that exist in the draft. If an example is generic and nothing specific is available, either cut it or mark it `[EXAMPLE NEEDED: …]` for the author. Never invent a company, customer, quote or number.

Rules while rewriting:

- No new claims, statistics, sources, quotes or examples.
- Keep every item on the fact list from step 1, with its meaning unchanged. Softening "will" to "may" or hardening "may" to "will" changes meaning.
- Keep technical terms and proper nouns exactly.
- Keep the length within ±15% of the original unless the user asked for shorter. If you land more than 15% under, first restore any substance you cut. If the removed words were pure filler, don't pad: report the drop in the summary.
- Keep markdown structure (headings, links, lists the content needs) unless it's the tell itself.

**Done when** every flagged hit is either fixed or consciously kept with a reason.

### 4. Self-check

Run the scorer on the rewrite (or re-score by hand), then go through this checklist. Fix anything that fails and check again.

- [ ] After-score is in a lower band than before, or ≤ 15.
- [ ] Every fact on the step-1 list is present and unchanged. Numbers match digit for digit.
- [ ] No sentence states something the original didn't.
- [ ] Word count is within ±15% of the original (or the user's target).
- [ ] No new tells crept in. Watch for swapping one cliché for another ("leverage" → "harness").
- [ ] Deliberate author habits from step 1 are still there.
- [ ] Read the first and last paragraph aloud in your head. They should sound like a person talking to the reader, not announcing a topic.

**Done when** all boxes are ticked.

## Output

Return exactly these four parts, in this order:

```
## Cleaned draft

<the full rewritten text, in the original format>

## What changed

- <category>: <n> fixes, e.g. "Vocabulary: 9 (leverage→use ×3, seamless, robust, delve…)"
- <category>: …
- Kept on purpose: <tell + reason, e.g. "'robust' in the API section: technical term">
- Needs the author: <[EXAMPLE NEEDED] markers or facts you couldn't make specific>

## Score

| | Before | After |
|---|---|---|
| Slop score (0-100) | 64 (heavy) | 9 (clean) |
| Words | 412 | 371 (−10%) |
| Sentence-length variation (CV) | 0.28 | 0.51 |

Method: scripts/slop_score.py  ← or "manual estimate"
```

In audit-only mode, return the Score table (Before column only) and the hit list grouped by category with line numbers or quotes, then offer the rewrite.

## Guardrails

- Never add facts, statistics, testimonials, sources or named examples. If the draft is vague because the facts are missing, ask the author for them.
- Never change the meaning of a claim, including its certainty.
- Never present the score as proof that a human or an AI wrote something. It measures style patterns only. Don't use it to judge a student, candidate or employee.
- Don't strip a voice the user said is intentional. If the user says "I like my em dashes", exclude that category and say so in the summary.
- Quoted material, legal or regulated text (disclaimers, terms, medical or financial wording) stays verbatim. Flag tells inside it instead of editing.
- Text in another language: the catalogue and script are English-only. Say so, and only apply the punctuation, formatting and structure checks that carry over.

## Common mistakes

| Mistake | Fix |
|---|---|
| Swapping each flagged word for a thesaurus synonym ("leverage" → "harness") | Use the plain word, or the specific fact. If neither exists, cut the phrase |
| Rewriting a draft that already scored clean | Report the score and stop unless the user asked for edits |
| "Fixing" a vague claim by inventing a number or customer | Mark `[EXAMPLE NEEDED]` or `[DATA NEEDED]` and list it under "Needs the author" |
| Cutting 40% of the text and not saying so | Stay within ±15% where substance allows; if filler alone pushes it lower, report the drop instead of padding |
| Removing every em dash, question and triad | Remove the excess. One question opener in a 1,200-word post is fine |
| Treating script hits as certain | They're candidates. Read each one in context; "unlock your phone" is not a tell |
| Flattening the author's personality into neutral corporate prose | Keep the author's jokes, asides, fragments and odd word choices. Those are what make it human |

## Example

**Input (LinkedIn post, 103 words):**

> We've completely revamped our onboarding experience to help customers hit the ground running. 🚀 It's not just an update — it's a whole new way to get started.
>
> New accounts can now seamlessly import their contacts during sign-up instead of after. We've also streamlined the setup checklist from 14 steps to 5, and admins can leverage a new invite screen to bring their whole team on board from day one. Every new account also gets a sample pipeline to explore before real data arrives.
>
> The result? Customers are up and running in 2 days instead of 9. Let's dive into what changed! 👇

**Diagnosis:** script hits: contrast framing, "The result?", "Let's dive into", "seamlessly", "leverage", one em dash in 103 words. Read-through adds idioms the script doesn't catch: "completely revamped", "hit the ground running", "streamlined". Fact list: contact import moved into sign-up; checklist 14 → 5 steps; team invite screen; sample pipeline; 2 days, previously 9; details follow.

**Cleaned draft:**

> We rebuilt onboarding so new customers can start working sooner. Nearly every step of setup is new.
>
> New accounts now import their contacts during sign-up instead of after. The setup checklist went from 14 steps to 5, and admins can invite their whole team from a new screen on day one. Every new account also gets a sample pipeline to explore before real data arrives.
>
> Together, these changes mean customers are now up and running in 2 days, where it used to take 9.
>
> Each change is explained below. 👇

**What changed:** Structure 3 (contrast framing → "Nearly every step of setup is new"; "The result?" → plain sentence; "Let's dive into" cut). Vocabulary 5 (seamlessly cut, leverage → invite, revamped → rebuilt, streamlined → went from, hit the ground running → start working sooner). One emoji kept as LinkedIn's "read below" cue. Kept: all four changes and both numbers.

**Score:** before 100 (saturated), after 0 (clean). Words 103 → 90 (−13%).

Edge case: a draft that is mostly filler (say, "In today's fast-paced world…" plus one fact) can't stay within ±15%. Cut it anyway and report the drop; never pad to hit the band.
