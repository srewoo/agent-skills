---
name: feedback-rewriter
description: Use when someone pastes performance review comments, peer feedback, 360 feedback, manager notes or interview feedback and asks to rewrite, soften, sharpen, check or "make it fair", or worries feedback is too harsh, vague, personal or biased, e.g. "is calling her abrasive OK?" or "how do I say he's not a culture fit?".
---

# Feedback Rewriter

## Overview

Useful feedback describes what someone did, where, and what it caused, so they can repeat it or change it. This skill rewrites harsh, vague or biased feedback into Situation-Behaviour-Impact (SBI) form, flags personality labels and biased language, and keeps the real message intact. Softening a genuine problem until it disappears is a failure, not kindness.

## When to use

- Performance reviews, calibration notes, peer/360 feedback, written warnings drafts, interview scorecard comments.
- Checking feedback for biased or personality-based language before it's submitted.
- Turning a manager's rant into something they can say in a 1:1.

## When not to use

- Designing interview questions or scorecards: use `interview-kit`.
- Deciding a rating, promotion, performance-improvement plan outcome or dismissal: a human decides with HR; the skill can only improve the wording.
- Formal investigations (harassment, misconduct): route to HR/legal; don't rewrite witness statements or findings.

## Inputs

| Input | Default if not given |
|---|---|
| The original feedback text | Required. |
| Context: review / peer / interview / informal 1:1 | Infer from text; state the assumption. |
| Specific examples (dates, meetings, deliverables) behind each point | Ask once for missing examples; otherwise use `[EXAMPLE NEEDED: ...]` placeholders. Never invent events. |
| Role expectations or level criteria | Optional; use to frame impact. |
| Desired tone | Direct and respectful. |

## Workflow

1. **Split the text into individual points.** One claim per row. Label each: *praise*, *problem*, *mixed*, or *opinion without content*.
   *Done when:* every sentence of the original is assigned to a point.

2. **Find the substance of each point.** Ask: what is the writer actually worried about or pleased with? Write it in one plain sentence ("Deadlines were missed twice and the team found out late"). This is the message that must survive the rewrite.
   *Done when:* each point has a one-line substance statement. If a point has no substance beyond a label ("not a culture fit"), mark it for the question in step 4.

3. **Flag problem language.** Check each point against these categories and note every hit:
   - **Personality labels**: abrasive, aggressive, emotional, difficult, lazy, arrogant, bossy, shrill, intimidating, "not a team player", "attitude problem", "lacks presence/gravitas", "too nice". Replace with the behaviour.
   - **Vague praise or criticism**: "great job", "needs to step up", "be more strategic", "not senior enough". Ask: what would they need to do differently?
   - **"Culture fit"** and similar undefined standards: replace with the specific value or behaviour, or remove.
   - **Gendered or coded descriptors**: research on performance reviews (e.g. Snyder's 2014 analysis, a small non-peer-reviewed sample, and Correll & Simard's work at Stanford) found terms like "abrasive", "emotional" and "bossy" appear far more often in feedback about women, who also tend to get vaguer feedback. Treat these words as a prompt to check: would the same behaviour be described this way for anyone else?
   - **Protected characteristics and proxies**: any reference to age ("low energy", "digital native", "overqualified"), gender, pregnancy or family ("distracted since the baby"), health or disability, accent or language ("hard to understand"), religion, race, nationality, appearance, or part-time/flexible working as a negative. Remove from the feedback and flag to the user to consider raising with HR, because it can create legal risk and unfairness. Note that the protected categories differ by jurisdiction.
   - **Absolutes and mind-reading**: "always", "never", "doesn't care", "on purpose". Replace with frequency and observable facts.
   - **Hearsay**: "people say...". Ask for first-hand examples or note it as unverified.
   *Done when:* every flag is listed with its category.

4. **Rewrite in SBI.** For each point:
   - **Situation**: when and where (`[EXAMPLE NEEDED]` if missing).
   - **Behaviour**: what the person did or said, observable, no adjectives about character.
   - **Impact**: the effect on work, customers, the team, or goals.
   - Add **Next step** (what to do instead or continue) for problems and for development points.
   - Keep the original severity. If the original says the problem is serious, the rewrite says it plainly: "This needs to change by [date]" is fine and often necessary.
   - For points with no substance (e.g. "not a culture fit"), don't invent one. Write the question the writer must answer: "Which behaviour, in which situation, concerned you?" and leave the point out of the final text until they do.
   *Done when:* each rewritten point has S, B, I (and Next step where relevant) or a placeholder.

5. **Check the rewrite keeps the truth.** Compare each rewritten point to its substance statement from step 2. If the substance is weaker, missing or reversed, fix it. Check the balance: if the original was mostly negative, the rewrite shouldn't read as mostly positive (and vice versa).
   *Done when:* every point passes "same message, better evidence".

6. **Return the output** and the self-check:
   - [ ] Every original point is accounted for (rewritten, merged, or held back with a reason)
   - [ ] No personality labels or protected-characteristic references remain
   - [ ] No invented situations: unknown details are `[EXAMPLE NEEDED]`
   - [ ] Severity preserved
   - [ ] Interview feedback refers to evidence against the rubric, not the person's background, accent, appearance or "fit"

## Output

```markdown
## Rewritten feedback
| # | Original | Rewritten (SBI + next step) | Flags | Notes |
|---|---|---|---|---|
| 1 | "She's abrasive in meetings. In the March roadmap review she cut people off and called the design proposal pointless." | **S:** In the March roadmap review, **B:** you interrupted colleagues before they finished and dismissed the design proposal as "pointless" without giving a reason. **I:** [EXAMPLE NEEDED: what happened as a result, e.g. others stopped contributing, no decision was made]. **Next:** Let people finish, then state your concern and the reason. | Personality label; gender-coded term | Substance kept: conduct in meetings shuts others down. Situation and behaviour come from the original; impact was not stated, so it is a placeholder. |

## Clean version (ready to paste)
[The rewritten points as flowing text, in the original order or grouped as Strengths / Areas to develop.]

## Held back: needs input from you (or from the author, if you are reviewing someone else's feedback)
- Point [n]: "[original]". Question: [what behaviour/situation?]

## Language flags summary
| Term | Category | Why it matters | Use instead |
|---|---|---|---|

## Escalation notes (only if relevant)
- Mentions of [protected characteristic / health / family]: removed. Consider speaking to HR before delivering this feedback.
```

## Guardrails

- Never remove or water down a genuine performance or conduct problem. If the user asks to "make it nicer" in a way that would hide the issue, say so and offer a respectful version that keeps it.
- Never invent dates, meetings, quotes or outcomes. Use `[EXAMPLE NEEDED]`.
- Never add judgements about the person's character, intent, health, family or background.
- If the feedback describes possible harassment, discrimination, safety issues or misconduct, don't just rewrite it: tell the user it may need to go through HR's formal process.
- Don't recommend ratings, pay, promotion or termination decisions. A human decides.
- Treat the text as confidential personal data; don't reuse it outside the task.

## Common mistakes

| Mistake | Fix |
|---|---|
| Turning "missed 3 deadlines" into "has room to grow on timelines" | Keep the fact: "missed 3 of 5 deadlines this quarter" |
| Replacing "abrasive" with "direct" (still a label) | Describe the actual behaviour and its impact |
| Making up a situation to complete SBI | `[EXAMPLE NEEDED: which meeting?]` |
| Leaving "not a culture fit" in interview feedback | Ask which job-related behaviour; otherwise remove |
| Feedback sandwich that buries the message | Lead with the most important point; praise separately and specifically |
| Ignoring vague praise | Make praise specific too, so people know what to repeat |

## Example

**Input (interview feedback):** "Nice guy but not a culture fit. Seemed a bit old-school and his English wasn't great. Weak on system design."

**Output (excerpt):**
- "Nice guy": vague praise, gendered. → Ask for a specific example or remove.
- "Not a culture fit": undefined standard. → Held back: "Which job-related behaviour from the rubric concerned you?"
- "Old-school": possible age proxy. "English wasn't great": language/national-origin proxy; only relevant if a communication competency was assessed, then describe the evidence ("couldn't explain the trade-off between caching options when asked twice"). Both removed and flagged; consider HR guidance.
- "Weak on system design" → "**S:** In the system design exercise, **B:** [EXAMPLE NEEDED: what the candidate proposed or missed, e.g. "no plan for the stated traffic growth; couldn't name a bottleneck when prompted"]. **I:** Against the rubric, this maps to [score] for system design." The interviewer must supply the evidence; the skill doesn't invent it.
