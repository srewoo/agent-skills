---
name: interview-kit
description: Use when a hiring manager or recruiter asks for interview questions, an interview plan, interview loop, scorecard, scoring rubric or debrief template for a role, wants to make interviews more structured or consistent, or asks which interview questions are illegal or should be avoided.
---

# Interview Kit

## Overview

Structured interviews (same job-related questions, anchored rating scales, independent scoring) are among the most predictive and least biased selection methods in the research literature (e.g. Sackett et al., 2022 meta-analysis). This skill turns a job description into a complete kit: competencies, questions, anchored rubric, interviewer plan, scorecard and debrief rules. Interviewers and the hiring manager make every decision.

## When to use

- Preparing an interview loop for a new or existing role.
- Replacing unstructured "chat" interviews with a consistent kit.
- Checking a question list for illegal or discriminatory questions.

## When not to use

- The JD itself is vague or missing: run `jd-writer` first, then come back.
- Screening CVs before interviews: use `resume-screener`.
- Rewriting interviewers' written feedback after the fact: use `feedback-rewriter`.

## Inputs

Ask for all missing inputs in one message.

| Input | Default if not given |
|---|---|
| JD or role brief | Required. Ask. |
| Level / seniority | Infer from JD; mark `[CONFIRM]`. |
| Number of interview stages and interviewers | 4 interviews of 45-60 min (hiring manager, 2 skill interviews, 1 cross-functional). |
| Competencies the company already uses (values, framework) | Derive from the JD only. |
| Interview format | Video; note in-person variants where they differ. |
| Jurisdiction(s) of candidates | Ask: it changes the "questions to avoid" list. If unknown, use the broad list and flag it. |
| Work sample / take-home allowed? | Optional; if used, cap at 2-3 hours and say whether it's paid (check local norms). |

## Workflow

1. **Derive 4-6 competencies from the JD.** Each must trace to a must-have or outcome in the JD. Write each as: name, one-line definition, and the JD line it comes from. Drop any that can't be traced ("culture fit", "gravitas", "polish"). If the company has values, express them as observable behaviours ("raises risks early"), not fit.
   *Done when:* every competency cites a JD line and none is a personality trait.

2. **Write the question bank.** Per competency:
   - 2 **behavioural** questions ("Tell me about a time you...") with STAR follow-up probes (Situation, Task, Action, Result: "What did *you* do?", "What happened next?", "What would you do differently?").
   - 1 **situational** question ("Imagine... what would you do?") grounded in a real scenario from the role.
   - Optional: 1 technical or work-sample task when the competency is a hard skill.
   - Allow non-work examples (volunteering, study, caring roles) where the competency permits; this avoids penalising career changers and people with gaps.
   *Done when:* each competency has ≥ 3 questions, every question is open-ended, and none appears in the "questions to avoid" list.

3. **Build the anchored rubric (1-4 scale).** For each competency write a behavioural anchor for each level, specific to the role:
   - **1 – Not demonstrated:** no relevant example, or example shows the opposite behaviour.
   - **2 – Partially demonstrated:** relevant example but limited scope, heavy reliance on others, or vague on own actions.
   - **3 – Demonstrated (hiring bar):** clear example of own actions with a result at the scope the level needs.
   - **4 – Strongly demonstrated:** repeated or larger-scope evidence, measurable impact, and reflection on what they learned.
   Use an even scale so there is no neutral middle. State that "3" is the bar for the level.
   *Done when:* every competency has 4 anchors written in observable terms (what the candidate said or did), not adjectives like "great" or "weak".

4. **Assign interviewers.** Build a matrix: each competency is owned by exactly one interview (two only for the single most critical competency, to get a second signal). Each interviewer covers 1-3 competencies in 45-60 min. Note who must be trained on the kit and who is a shadow.
   *Done when:* no competency is uncovered and none is assessed by more than two interviewers.

5. **Write the scorecard and debrief rules** (see Output). Debrief rules:
   - Each interviewer submits scores and evidence **before** seeing others' scores or talking about the candidate.
   - Debrief order: go competency by competency, not interviewer by interviewer; the most junior interviewer speaks first; the hiring manager speaks last.
   - Discuss evidence, not impressions. Any comment without a quote or example is set aside.
   - Score changes after discussion are allowed only with a stated evidence reason, recorded on the scorecard.
   - The decision (hire / no hire / more information needed) is made by the named decision-maker against the bar, not by vote averaging alone.
   *Done when:* the scorecard has a free-text evidence field per competency and the rules above are in the kit.

6. **Add the "questions to avoid" section** for the jurisdictions given (see below), and add the AI-use note if any AI tool will score or transcribe interviews.
   *Done when:* the section is present and tailored, or flagged as generic.

7. **Self-check** against: competencies traced to JD; ≥ 3 questions each; 4 anchors each; matrix complete; independent scoring rule; avoid-list present; no question touches a protected characteristic.

## Questions to avoid

Laws differ by country and state; confirm with HR/legal for each candidate location. As a broad rule, do not ask about, or let small talk drift into:

| Topic | Don't ask | Job-related alternative (where permitted) |
|---|---|---|
| Age | "When did you graduate?", "How old are you?" | "Are you over the minimum legal working age for this role?" only if legally required |
| Nationality, race, ethnicity, caste | "Where are you originally from?", "Is that your real name?" | "Are you legally authorised to work in [country]?" (check local rules on timing) |
| Religion | "Which holidays do you observe?" | State the schedule and ask if they can meet it |
| Sex, gender identity, sexual orientation | Any | None |
| Marital status, pregnancy, children, family plans, caring duties | "Do you have kids?", "Planning a family?" | State travel/hours and ask if they can meet them |
| Disability, health, medical history | "Do you have any health conditions?" | Describe essential duties; ask if they can perform them with or without adjustments |
| Salary history | "What do you earn now?" | "What are your pay expectations?" (salary-history questions are banned in many US states and cities, and under the EU Pay Transparency Directive as each country implements it) |
| Criminal record | Early-stage questions | Follow local "ban the box" / fair-chance rules; HR handles any check |
| Union membership, political views | Any | None |
| Appearance, accent | Any comment | None |

If a candidate volunteers protected information, don't follow up, don't record it, and don't let it affect scoring.

## AI in interviews

If an AI tool will record, transcribe, score or rank interviews, tell the user it may trigger legal duties, e.g. notice and consent (Illinois AI Video Interview Act), bias audits and notices (New York City Local Law 144), EU AI Act high-risk rules for recruitment (postponed to December 2027 at the earliest; check the current date), and data-protection rules on automated decisions (e.g. GDPR Article 22). Recommend legal review before use; a human makes every decision.

## Output

```markdown
# Interview kit: [Role] ([Level])
Hiring bar (default, [CONFIRM]): a "3" or higher on most competencies, including the critical one, and no "1". Decision-maker: [name/role]

## 1. Competencies
| # | Competency | Definition | From JD line |
|---|---|---|---|

## 2. Interview plan
| Interview | Interviewer(s) | Length | Competencies owned | Format |
|---|---|---|---|---|

## 3. Question bank and rubric (one block per competency)
### [Competency]
**Behavioural:** 1. ... (Probes: ...)  2. ...
**Situational:** 3. ...
| Score | Anchor |
|---|---|
| 1 | ... |
| 2 | ... |
| 3 (bar) | ... |
| 4 | ... |

## 4. Scorecard (one per interviewer, complete before debrief)
Candidate ID: ____  Interviewer: ____  Date: ____
| Competency | Score (1-4) | Evidence: what the candidate said/did (quotes) |
|---|---|---|
Overall recommendation: Strong yes / Yes / No / Strong no  ·  Reason tied to evidence: ____
Anything I couldn't assess: ____

## 5. Debrief rules
[the 5 rules from step 5]

## 6. Questions to avoid
[table tailored to jurisdictions, or "generic: confirm locally"]

## 7. Open items
- [ ] [CONFIRM] items · legal check for [jurisdictions] · interviewer training
```

## Guardrails

- The kit supports decisions; never output a hire/no-hire decision for a real candidate.
- Never include questions about protected characteristics or obvious proxies, even indirectly ("Where did you grow up?").
- Never present the avoid-list as complete legal advice; label it as a starting point to check with HR/legal.
- Don't assess "culture fit"; replace with named, observable behaviours.
- Brain-teasers and trick questions have little predictive value; don't include them.
- If asked to make one candidate's interview easier or harder than others', decline and explain that consistency is the point.

## Common mistakes

| Mistake | Fix |
|---|---|
| Every interviewer asks "tell me about yourself" and assesses everything | One owner per competency via the matrix |
| Rubric anchors are adjectives ("good communicator") | Write what the candidate says or does at each level |
| Debrief starts with the hiring manager's opinion | Independent scores first; manager speaks last |
| Hypothetical-only questions | Mix behavioural (past evidence) with situational |
| Rejecting answers drawn from non-work life | Accept any relevant example unless the competency needs work context |
| 5-point scale where everyone picks 3 | 1-4 scale with 3 as the bar |

## Example

**Input:** "Kit for a Customer Success Manager, mid-level. JD must-haves: manage a book of ~40 SMB accounts, drive renewals, run onboarding, spot churn risk from usage data, communicate clearly with execs."

**Output (excerpt):** Competencies: Account ownership; Renewal & commercial judgement; Onboarding delivery; Data-driven risk detection; Stakeholder communication. Matrix: hiring manager → Account ownership + Renewal; CS peer → Onboarding + Risk detection; Sales partner → Renewal (second signal) + Stakeholder communication.
*Risk detection, behavioural Q:* "Tell me about a time usage data told you an account was at risk before the customer did. What did you do?" Anchor 3: "Names the signal, the threshold they used, the action they took and the outcome." Anchor 1: "Can't name a signal or relied only on the customer raising issues."
