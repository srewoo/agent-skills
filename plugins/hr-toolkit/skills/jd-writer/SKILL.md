---
name: jd-writer
description: Use when someone asks to write, draft, rewrite, review or "fix" a job description, job ad, job posting or role profile, wants it more inclusive or gender-neutral, says a posting gets few or narrow applicants, asks what to put under requirements vs nice-to-haves, or needs to add a salary range or EEO statement to an opening.
---

# JD Writer

## Overview

A job description is a filter: every requirement, adjective and acronym decides who applies. Write for outcomes the hire will deliver, keep hard requirements few and real, and use plain, gender-balanced language so qualified people don't screen themselves out. The hiring manager owns the final content; legal or HR confirms anything jurisdiction-specific.

## When to use

- Drafting a new JD from a role brief, intake notes or an old posting.
- Rewriting an existing JD for inclusion, clarity, length or accuracy.
- Reviewing a JD and reporting problems without rewriting it.

## When not to use

- Building interview questions or scorecards from the JD: use `interview-kit`.
- Screening applicants against the JD: use `resume-screener`.
- Setting the salary band itself (compensation benchmarking): the skill only places a range the user supplies.

## Inputs

Ask for all missing inputs in one message. If the user says "just draft it", proceed with the defaults below and mark every guess `[CONFIRM]`.

| Input | Default if not given |
|---|---|
| Role title and level | Required. Ask. |
| What the person must achieve in the first 6-12 months | Required. Ask; this drives the whole JD. |
| Existing JD or intake notes | None: draft from scratch. |
| Work location(s) and arrangement (on-site / hybrid / remote, and from which countries or states) | Required: it decides which pay-transparency and EEO rules apply. |
| Salary range and other pay (bonus, equity) | Leave a `[SALARY RANGE: required in some locations, see note]` placeholder. |
| Team, reporting line, company one-liner | Placeholders. |
| House style / tone | Plain, warm, second person ("you will"). |

## Workflow

1. **Establish what the job is for.** Write 3-5 outcomes as "In your first 6 months you will..." / "By 12 months you will...". Each outcome names a result, not a task ("cut month-end close from 10 to 6 days", not "own the close process"). If the user can't give outcomes, propose ones from the brief and mark them `[CONFIRM]`.
   *Done when:* every outcome is a result someone could check.

2. **Separate must-haves from nice-to-haves.** For each requirement in the brief, ask: "Would we reject an otherwise excellent candidate who lacks this?" Only a yes makes it a must-have.
   - Cap must-haves at **5-6**. Move the rest to nice-to-haves (cap ~5) or delete them.
   - Long requirement lists are widely reported to put off qualified applicants who read every bullet as mandatory; this is often said to affect women and under-represented groups more, though the evidence is mixed. Keep the list short either way and add: "If you meet most of this but not all, we'd still like to hear from you."
   - Express requirements as **skills or evidence**, not proxies. Replace "5+ years of X" with what those years should have produced ("has run X end to end in production"). Keep a years figure only if the user insists or regulation requires it, and never above what the level actually needs.
   - Remove degree requirements unless the job legally or genuinely requires one (licensed professions, regulated roles); otherwise write "degree or equivalent experience".
   - Never include requirements that act as proxies for protected characteristics: age ("digital native", "recent graduate", "young team"), physical ability not essential to the job ("must be able to stand all day" for a desk role), native-speaker requirements (use "fluent / professional proficiency in X"), nationality (use "authorised to work in [country]" only if true and permitted), "cultural fit".
   *Done when:* must-haves ≤ 6, each one passes the rejection test, and none is a proxy.

3. **Write responsibilities as ongoing work.** 5-8 bullets, verb-first, concrete, no duplicates of the outcomes.
   *Done when:* a candidate could describe a typical week from them.

4. **Run the language pass.** Check every sentence against:
   - **Gender-coded words**: use `references/gender-coded-words.md`. Aim for balance, not a ban; swap heavily skewed terms ("dominant", "rockstar", "ninja", "aggressive") for neutral ones. Use "you" and "they", never "he/she" or "he".
   - **Hype and jargon**: delete "rockstar", "ninja", "guru", "wizard", "work hard play hard", "family", "fast-paced" (unless explained), "self-starter", and internal acronyms. Expand any acronym the reader may not know.
   - **Reading level**: sentences ≤ 25 words, average ~15-20; aim for roughly a school grade 8-10 reading level (Flesch Reading Ease ≥ 50 if the user has a tool to measure it). Prefer common words ("use" not "leverage", "help" not "facilitate").
   - **Accessibility**: describe physical demands only if they are essential and say adjustments are available; mention flexible or part-time options if they exist; include how to request adjustments in the hiring process.
   - **Length**: aim for 300-700 words of body text.
   *Done when:* the gender-coded scan is recorded in the change log (or review notes) and no flagged hype words remain.

5. **Place pay and legal text.**
   - **Pay**: if the user gave a range, show it with currency and period. If not, insert the placeholder and add a note: a growing number of places require pay ranges in job postings or before the interview, e.g. several US states and cities (such as Colorado, California, Washington, New York, Illinois), some Canadian provinces, and EU countries under the EU Pay Transparency Directive (the June 2026 transposition deadline passed with most Member States late, so national rules and start dates differ; it also bars asking candidates about pay history). Tell the user to confirm the rules for every location the job is advertised to or can be done from, including remote roles open to those places. Never invent a range.
   - **EEO / equal opportunity statement**: insert `[EQUAL OPPORTUNITY STATEMENT: approved wording from HR/legal for each jurisdiction]` plus a neutral draft if asked. Do not claim the draft satisfies any specific law.
   - **Adjustments line**: "If you need adjustments or accommodations during the hiring process, contact [contact]."
   *Done when:* pay, EEO and adjustments each appear as text or a labelled placeholder.

6. **Assemble and self-check** using the Output template and the checklist below. If rewriting, write the change log.
   *Done when:* every checklist item is ticked or listed under "Open items".

### Self-check (run before returning)

- [ ] 3-5 outcomes, each a checkable result
- [ ] Must-haves ≤ 6 and each passes the rejection test; nice-to-haves ≤ ~5
- [ ] No inflated or arbitrary years-of-experience; no unneeded degree requirement
- [ ] No age, nationality, native-speaker, physical or "culture fit" proxies
- [ ] Gender-coded scan done; no "rockstar/ninja/guru"; "you/they" throughout
- [ ] Sentences ≤ 25 words; acronyms expanded
- [ ] Salary range or placeholder + pay-transparency note
- [ ] EEO placeholder and adjustments line present
- [ ] Every assumption marked `[CONFIRM]`

## Output

```markdown
# [Job title] ([Level])
**Location:** [city/country or Remote: eligible countries/states] · **Arrangement:** [on-site/hybrid/remote] · **Type:** [full-time/part-time/contract]
**Pay:** [currency min-max per year/hour + bonus/equity] OR [SALARY RANGE: required in some locations, see note]

## About the role
[2-3 sentences: why the role exists and who it works with. No hype.]

## What you'll achieve
- In your first 6 months you will ...
- By 12 months you will ...

## What you'll do
- [verb-first ongoing responsibility] (5-8 bullets)

## What you'll need (must-haves)
- [skill or evidence, max 6]

## Nice to have
- [max ~5]

If you meet most of this but not all, we'd still like to hear from you.

## What we offer
[Benefits, flexibility, learning. Placeholders if unknown.]

## How to apply
[Process steps and rough timeline.] If you need adjustments or accommodations during the hiring process, contact [contact].

[EQUAL OPPORTUNITY STATEMENT: approved wording from HR/legal]
```

When rewriting, append:

```markdown
## Change log
| # | Original | Change | Why |
|---|---|---|---|
| 1 | "Rockstar engineer" | "Senior software engineer" | Hype term; gender-coded and unclear |
| 2 | 11 requirements | 5 must-haves, 4 nice-to-haves, 2 removed | Long lists deter qualified applicants |

## Gender-coded scan
Masculine-coded found: [words] → [replacements]. Feminine-coded found: [words]. Balance: [summary].

## Open items for the hiring manager / HR / legal
- [ ] Confirm salary range for [locations]
- [ ] Approve EEO statement wording
- [ ] Confirm [CONFIRM] items: ...
```

For review-only requests, return the change log, gender-coded scan and open items without the full rewrite.

## Guardrails

- Never invent salary figures, benefits, company facts or legal wording. Use labelled placeholders.
- Never state that a JD is "legally compliant". Say which items legal/HR must confirm and for which jurisdictions.
- Never add or keep requirements based on age, sex/gender, race, religion, disability, marital or family status, nationality or other protected characteristics, or obvious proxies for them.
- Keep the hiring manager's genuine must-haves even when trimming; if you demote one, list it in the change log so they can reverse it.
- If the brief describes a role that seems to need a licence, security clearance or right-to-work restriction, keep it but mark it `[CONFIRM legal basis]`.

## Common mistakes

| Mistake | Fix |
|---|---|
| Copying the old JD's 12-bullet requirement list | Apply the rejection test; cap at 5-6 must-haves |
| "10+ years" for a mid-level role | Describe the capability the years should prove |
| Swapping every masculine-coded word for a feminine-coded one | Aim for balance and neutral words, not the opposite skew |
| Responsibilities that read like a task dump | Lead with outcomes; keep 5-8 verb-first bullets |
| Hiding the pay range because "we don't usually publish it" | Placeholder + note on pay-transparency laws for each location |
| Treating a remote role as having no location | List eligible countries/states; they drive pay and EEO rules |

## Example

**Input:** "Rewrite: 'We're looking for a coding ninja to dominate our backend. 8+ yrs Java, CS degree from a top school, native English, thrives under pressure, young dynamic team. Must know Kafka, K8s, AWS, GCP, Terraform, Go, Python, React.' Remote, US and Canada."

**Output (excerpt):**
- Title: "Senior Backend Engineer (Java)"; outcome: "In your first 6 months you will move the order service onto the new event pipeline with no customer-facing downtime `[CONFIRM]`."
- Must-haves (5): production Java services; event-driven systems (e.g. Kafka); cloud infrastructure on AWS or GCP; infrastructure as code; written English at professional level.
- Nice to have: Go or Python; Kubernetes; React.
- Change log rows: "ninja/dominate" removed (hype, masculine-coded); "8+ yrs" → capability statement; "top school CS degree" → "degree or equivalent experience"; "native English" → "professional proficiency" (national-origin proxy); "young dynamic team" removed (age proxy); 8-tool list split into must/nice.
- Pay: `[SALARY RANGE]` + the step 5 note, scoped to US states and Canadian provinces the role is open to.
