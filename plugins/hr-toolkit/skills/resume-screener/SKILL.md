---
name: resume-screener
description: Use when a recruiter or hiring manager pastes or uploads resumes/CVs and asks to screen, shortlist, rank, score or compare candidates against a job description, asks "who should we interview?", or wants a fair, consistent first-pass review of a batch of applicants.
---

# Resume Screener

## Overview

Score each resume against a job-specific rubric that a human approved first, cite evidence for every score, and ignore anything that identifies or proxies for who the candidate is. The output is a recommendation for a human reviewer: "advance", "review" or "not a match on rubric". The skill never rejects anyone.

## When to use

- First-pass screening of a batch of resumes for one role (chunked above ~20).
- Re-checking a shortlist for consistency or bias.

## When not to use

- No JD or role requirements exist yet: use `jd-writer` first.
- Interview stage evaluation: use `interview-kit`.
- Background checks, social-media vetting, or predicting personality, "culture fit", flight risk or salary: decline these.

## Inputs

| Input | Default if not given |
|---|---|
| JD (or must-haves and nice-to-haves) | Required. Ask. |
| Resumes (text, files, or pasted) | Required. |
| Approved rubric | Build one in step 1 and get approval before scoring. |
| Advance / review thresholds | Defaults in step 4. |
| Candidate location(s) / jurisdiction | Ask once; used only for the AI-use transparency note. |
| Batch size and format | Count the resumes first. Over ~20, use the chunked flow in step 3. |

## Workflow

1. **Build the rubric from the JD and get it approved.** Write 4-7 criteria. Mark each **Must-have** or **Nice-to-have**, give a weight (must-haves 2, nice-to-haves 1 by default), and write what evidence earns each score:
   - **0 – No evidence** in the resume.
   - **1 – Partial / adjacent:** related skill, smaller scope, or claimed without any supporting detail.
   - **2 – Meets:** clear evidence at the level the role needs.
   - **3 – Exceeds:** clear evidence at greater scope, depth, or with measurable results.
   Criteria must be job-related skills or outcomes. Reject criteria such as school prestige, specific employers, "years since graduation", continuous employment, location (unless the job truly requires it, e.g. on-site in a city), or "culture fit". Convert years-of-experience requirements into evidence of capability.
   **Stop and show the rubric to the user. Do not score anything until they approve or edit it.**
   *Done when:* the user has explicitly approved the rubric.

2. **Redact before reading for content.** For each resume, ignore (and in the output, never repeat): name, photo, age or date of birth, gender, pronouns, marital or family status, nationality, ethnicity, religion, caste, disability or health information, home address, graduation and school-leaving years, parents' or spouse's names, ID, passport or visa numbers, and other proxies such as clubs or associations that reveal these. Photos, DOB and "personal details" blocks are common in some countries (e.g. India, much of Europe and Asia); never mention them and never let their presence or absence affect scores. Assign each candidate an ID (C01, C02, ...) and keep the ID-to-resume mapping (file name, or order pasted) only in a separate list the user can see at the end.
   If redaction is impossible (e.g. a scanned image you can't read), mark the candidate "review: unreadable" rather than guessing.
   *Done when:* every candidate has an ID and the scoring notes contain no identifying details.

3. **Score criterion by criterion, across the batch (or chunk).** Score criterion 1 for every candidate, then criterion 2, and so on; this keeps the bar steady. For every score above 0, quote the resume line(s) that justify it (≤ 25 words each). **Evidence or zero:** if there's no quote, the score is 0, even if the candidate "probably" has the skill. Mark scores you're unsure of with `?` and say why (ambiguous wording, unclear scope, title that doesn't describe the work).
   Rules for fairness:
   - Career gaps, part-time work, career changes, caring breaks, freelance work, bootcamps, self-taught skills and non-traditional education are neutral. Score only the evidence present.
   - Don't reward length, design, keyword density, or impressive company names. Read what the person did.
   - Treat equivalent terms as equivalent (e.g. "people manager" = "line manager"; "PostgreSQL" counts toward "SQL databases").
   - Non-native writing, spelling or formatting are not criteria unless written communication is a criterion; even then, score substance over polish.
   Large batches:
   - **Chunked flow (over ~20 candidates).** Long batches pasted into chat degrade attention and drift the bar. Work in chunks of 15-20 candidates. Before chunk 1, restate the approved rubric. After chunk 1, pick 2-3 scored candidates as **calibration anchors** (a clear 3, a 2 and a 1 on the hardest criterion) and re-read them before each later chunk. In a coding agent with files, read and score one chunk at a time and append results to a working file (e.g. `screening-results.md`) rather than holding everything in context; it holds personal data, so tell the user to delete it under their retention policy. In chat, if resumes arrive across several messages, say which IDs are done and ask for the next chunk.
   - **Drift check** (any batch over ~20): re-score 2 candidates from the first chunk and 2 from the last without looking at the earlier scores. If any criterion moves by ≥ 1 point, list it, re-score that criterion for the whole batch, and note it in the batch summary.
   *Done when:* every cell has a score, every score > 0 has a quote, and (for > 20 candidates) the drift check result is recorded.

4. **Compute and recommend.** Weighted score = Σ(score × weight) ÷ Σ(3 × weight), as a percentage. Default recommendations:
   - **Advance**: every must-have ≥ 2 and weighted score ≥ 60%.
   - **Not a match on rubric**: two or more must-haves at 0 with no `?` flags.
   - **Review**: everything else, including any candidate with a `?` on a must-have, an unreadable resume, or a non-standard background the rubric may not capture well.
   These are suggestions for a human. Wording must say "recommend", never "reject" or "fail".
   *Done when:* each candidate has a recommendation and a one-line reason that cites the rubric.

5. **Write the batch summary and transparency note**, then self-check: no identifying details in output; every non-zero score has a quote; recommendations use the three labels only; the rubric shown is the approved one; thresholds stated. For > 20 candidates, put the batch summary table first and the per-candidate detail after it (or in the working file), so the result survives output-length limits.

## Output

```markdown
# Screening: [Role], [N] candidates, rubric approved [date/by]

## Rubric
| # | Criterion | Type | Weight | 2 = Meets looks like |
|---|---|---|---|---|

## Candidates
### C01: Recommend ADVANCE (78%)
| Criterion | Score | Evidence (quote) | Note |
|---|---|---|---|
| Production Java services | 3 | "Led migration of 14 Java services to..." | |
| Event-driven systems | 2? | "Worked with Kafka consumers" | Scope unclear: own work or team's? |
Reason: all must-haves met; strongest on [X]. Ask at interview: [specific gap].

[repeat per candidate]

## Batch summary
| ID | Must-haves met | Weighted % | Recommendation | Flags |
|---|---|---|---|---|
Counts: Advance [n] · Review [n] · Not a match on rubric [n]
Patterns: [e.g. "8 of 12 lacked infrastructure-as-code evidence: is it truly a must-have?"]
Drift check (> 20 candidates): [re-scored IDs, any criterion moved ≥ 1, what was re-scored]
Uncertain scores to check by a human: [list]

## ID mapping (for the recruiter only; keep separate from shared notes)
C01 = [file name or "1st resume pasted"]

## Transparency note
This is an AI-assisted first pass against a human-approved rubric. It did not make hiring decisions. A person must review every recommendation, especially "review" and "not a match on rubric". AI-assisted screening may carry legal duties depending on location, e.g. New York City Local Law 144 (bias audits and candidate notices), the EU AI Act (recruitment tools are high-risk; those obligations were postponed to December 2027 at the earliest, so check the current date), and data-protection law on automated decisions and candidate data (e.g. GDPR Article 22; India's DPDP Act, phasing in to 2027). Check with HR/legal before relying on this process.
```

## Guardrails

- Never score before the rubric is approved.
- Never output "reject", rank candidates as final, or contact candidates. Humans decide.
- Never infer or mention protected characteristics, even to "check diversity"; if asked to filter or balance by them, decline and suggest the user's HR/legal team handle any lawful diversity monitoring separately from screening.
- Never penalise gaps, age signals, non-traditional paths or non-native language.
- If asked to change the rubric after scoring has started, re-score the whole batch against the new rubric, never just some candidates.
- If the batch looks unusually skewed (e.g. almost everyone is "not a match"), say the rubric may be too strict or the JD unclear rather than accepting the result.
- Don't keep or reuse candidate data beyond the task; remind the user that resumes are personal data subject to their retention policy.

## Common mistakes

| Mistake | Fix |
|---|---|
| Scoring "probably knows Kafka" as 2 | Evidence or zero: quote it or score 0 |
| Scoring each candidate fully before moving on | Score criterion-by-criterion across the batch |
| Rubric item "5+ years experience" | Rewrite as capability evidence |
| Repeating the candidate's name in notes | Use IDs only; mapping lives in a separate section |
| Treating a 2-year gap as a negative | Gaps are neutral; score what's present |
| Labelling someone "rejected" | Use "not a match on rubric" and route to a human |
| Scoring 40 pasted resumes in one pass | Chunks of 15-20, calibration anchors, drift check |
| Commenting on a photo or DOB in a CV that includes them | Ignore personal-details blocks entirely; never repeat them |

## Example

**Input:** JD for a Data Analyst (must-haves: SQL, dashboarding, stakeholder reporting; nice-to-have: Python, A/B testing), 3 resumes pasted.

**Step 1 output:** rubric with 5 criteria and weights 2/2/2/1/1, then: "Please approve or edit this rubric before I score."

**After approval (excerpt):** C02, recommend REVIEW (50% = 12 of 24 weighted points). SQL 2 ("wrote SQL queries for monthly churn report"), Dashboarding 1? ("built reports in Excel": dashboards not mentioned; ask), Stakeholder reporting 3 ("presented weekly KPI pack to the leadership team"), Python 0, A/B testing 0. Note: 18-month gap 2022-2023 not scored. Reason: one must-have uncertain; check dashboard experience at phone screen.
