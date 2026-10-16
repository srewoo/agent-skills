# Voice guide template

Copy this structure into `voice-guide.md`. Every rule cites evidence: a short quote from a sample, tagged with the sample ID (S1, S2…). A rule with no evidence is a guess, so either mark it `(assumed)` or drop it.

```markdown
# <Brand or author> voice guide

Version: 1.0 · Built: <YYYY-MM-DD> · Samples: <n> (<total words> words) · Confidence: <high | medium | low>
Sources: S1 <title, channel, date> · S2 … · Held out for validation: S<n>

## Voice in one sentence
<Who we sound like, talking to whom, e.g. "A senior engineer explaining a fix to a peer over coffee: direct, a bit dry, never selling.">

## Tone attributes
| We are | Not | What it looks like | Evidence |
|---|---|---|---|
| Direct | Blunt | Lead with the answer; soften with reasons, not hedges | S2: "Short answer: no. Here's why." |
| Warm | Gushing | Thank people for specifics, never generically | S1: "Thanks to Priya for the bug report that started this." |
| Confident | Arrogant | State results with numbers; admit what didn't work | S3: "Clicks tripled. Signups didn't move." |
<3-5 rows. Each "Not" is the failure mode a writer slides into when overdoing the "We are".>

## Vocabulary
| Use | Instead of | Evidence |
|---|---|---|
| customers | users, clients | S1, S2, S4 (no "users" in 3,200 words) |
| set up | onboard, implement | S2 |

Never use: <words absent from all samples or banned by the user, e.g. "synergy", "best-in-class", "delve">
Signature phrases (use sparingly, max once per piece): <e.g. "Short answer:", "The boring fix">
Jargon policy: <e.g. "Technical terms allowed; define on first use for marketing pages">

## Sentence and paragraph patterns
- Average sentence length: <n> words (range <a>-<b>). Share of sentences under 8 words: <x>%.
- Paragraphs: <n> sentences typical; one-sentence paragraphs <often | sometimes | never>.
- Openings: <how pieces start, e.g. "with a concrete event or number, never a question">.
- Endings: <e.g. "a single next step; no recap">.
- Structure: <e.g. "problem → what we tried → result → what's next">.

## Person and point of view
- We/I: <"we" for the company; "I" only in founder posts>
- Reader: <"you", addressed directly | third person "teams", "marketers">
- Contractions: <always | mostly | never> (measured: <x> per 100 words)

## Formality
<1-5 scale, 1 = text message, 5 = legal notice> : <n>. <One line on why, with evidence.>

## Humour
<none | dry understatement | playful | self-deprecating> . Where it's allowed: <e.g. "blog intros and newsletters, never in product docs or incident notes">. Evidence: <quote>.

## Punctuation habits
- Em dashes: <n per 1,000 words>. Exclamation marks: <n per 1,000 words>. Questions: <rare | common>.
- Oxford comma: <yes | no>. Emoji: <never | social only | allowed>. Ellipses: <…>.
- Numbers: <numerals always | words for one to nine>. Dates: <format>. Capitalisation of headings: <sentence case | title case>.

## Formatting habits
- Headings: <every ~n words | none in posts under 500 words>.
- Lists: <bullets for 3+ parallel items only | numbered for steps>.
- Bold: <for UI labels only | never for emphasis>.
- Links: <descriptive link text, never "click here">.

## Channel adjustments (only if samples span channels)
| Channel | Shift from core voice | Evidence |
|---|---|---|
| LinkedIn | Formality −1, first person "I", one emoji max | S4, S5 |
| Docs | Formality +1, no humour, imperative mood | S6 |

## Example rewrites
| Off-voice | On-voice | Rules applied |
|---|---|---|
| "We're thrilled to announce our innovative new dashboard!" | "The new dashboard is live. It loads in under a second, down from four." | Confident not arrogant; numbers over adjectives; no exclamation |
<3-5 rows, using sentences from real drafts where possible.>

## Conformity checklist
<Copy the scorecard from SKILL.md, with any brand-specific weights.>
```
