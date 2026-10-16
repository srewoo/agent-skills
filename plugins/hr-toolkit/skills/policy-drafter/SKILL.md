---
name: policy-drafter
description: Use when someone asks to draft, write, update or review a workplace or HR policy (leave, parental leave, remote or hybrid work, expenses, travel, code of conduct, anti-harassment, grievance, disciplinary, data or device use, AI use at work) or an employee handbook section, often from a short brief like "we need a WFH policy".
---

# Policy Drafter

## Overview

A good policy tells employees, in plain language, what they can do, what they must do, and who to ask. This skill turns a short brief into a structured, versioned draft and a clear list of items legal must verify. Employment law differs by country, state and sometimes city, so the draft is never final until a qualified person in each jurisdiction has reviewed it.

## When to use

- New policy from a brief ("draft a hybrid work policy for 120 staff in the UK and India").
- Rewriting an existing policy for clarity, structure or a scope change.
- Reviewing a policy for gaps against the standard structure.

## When not to use

- Individual employee cases (a specific disciplinary, a specific leave request): those need HR and legal advice on the facts.
- Employment contracts, settlement agreements or works-council/union agreements: legal documents outside this skill's scope.
- Onboarding plans: use `onboarding-plan`.

## Inputs

Ask the upfront questions in one message. Don't draft until you have at least the first three answers, or the user says "use defaults".

| Question | Why | Default if user says "use defaults" |
|---|---|---|
| 1. Which policy, and what problem prompted it? | Sets purpose and scope | Standard policy for the type |
| 2. Countries / states / provinces where covered people work (incl. remote workers) | Statutory minimums, required clauses | Draft jurisdiction-neutral; every legal point becomes a "verify" item |
| 3. Who is covered? (employees, contractors, interns, all levels?) | Scope | All employees |
| 4. Organisation size and any union, works council or collective agreement | Some rules depend on headcount; consultation duties | Unknown: flag |
| 5. Existing related policies and HR systems | Cross-references | Placeholders |
| 6. Decisions already made (e.g. "3 office days", "16 weeks paid leave") | The company's choices, not yours | Mark as `[DECISION NEEDED]` |
| 7. Owner, approver, effective date, review cycle | Version table | Owner: HR; review in 12 months |
| 8. Tone (formal / friendly) and reading level | Plain language | Friendly-plain, second person |

## Workflow

1. **Collect answers and list the jurisdiction issues.** For the policy type, open `references/policy-checklists.md` and copy its "verify with legal" items for this policy into a working list. Add any jurisdiction-specific items you know apply to the locations given, phrased as questions ("Confirm the statutory minimum paid leave in [country]") rather than stated as law.
   *Done when:* every location given has at least one verify item, or the list states that none apply and why.

2. **Separate company choices from legal requirements.** For each rule in the policy, label it internally as either *company choice* (benefit levels above minimum, office days, approval limits) or *legal requirement* (statutory minimums, mandatory procedures). Company choices the user hasn't made become `[DECISION NEEDED: ...]` with 2-3 common options. Legal requirements become verify items; never fill in a number from memory as if settled.
   *Done when:* no number or rule in the draft lacks either a user decision or a verify flag.

3. **Draft in the standard structure** (see Output). Writing rules:
   - Second person ("you", "we"), active voice, sentences ≤ 25 words, average ~15-20.
   - "Must" for requirements, "may" for permissions, "should" only for recommendations. Never "shall".
   - Define every term that changes who is covered or what counts (e.g. "dependant", "business travel", "remote location").
   - Procedures are numbered steps with who, what, and by when.
   - Use gender-neutral language and inclusive definitions (e.g. parental leave for all parents, including adoptive, surrogacy and same-sex parents, subject to legal check).
   - Name roles, not people ("your manager", "the People team").
   - Keep it under ~4 pages for most policies; move forms, rate tables and FAQs to appendices.
   *Done when:* every section in the template is filled or explicitly "Not applicable".

4. **Check for fairness and unintended impact.** Ask: does any rule affect people with a protected characteristic more than others (e.g. office-presence rules and disabled staff or carers; dress codes and religious dress; on-call rules and caring duties)? Add an adjustments/exceptions route and flag each issue in the verify list.
   *Done when:* the exceptions section names a route and at least the obvious impact questions are flagged.

5. **Self-check and return.**
   - [ ] All 10 sections present
   - [ ] Every legal number or obligation is a verify item, not a stated fact
   - [ ] Every company choice is either decided by the user or `[DECISION NEEDED]`
   - [ ] Procedure steps have owner + timeframe
   - [ ] Version table and review date present
   - [ ] No reference to a specific law presented as definitely applicable without "verify"

## Output

```markdown
# [Policy name]
| Version | Date | Author | Approved by | Summary of changes |
|---|---|---|---|---|
| 0.1 DRAFT | [date] | [author] | Not yet approved | First draft |

**Owner:** [role] · **Effective date:** [date] · **Next review:** [date, default +12 months] · **Applies to:** [countries/entities]

## 1. Purpose
[2-3 sentences: why this policy exists, what it achieves.]

## 2. Scope
Who it covers, who it doesn't, which locations. Where local law or a collective agreement gives more favourable terms, those apply.

## 3. Definitions
| Term | Meaning in this policy |
|---|---|

## 4. Policy
[The rules. Short subsections. "You must... / You may... / We will..."]

## 5. Procedure
1. [Who] [does what] [by when / how].

## 6. Roles and responsibilities
| Role | Responsibilities |
|---|---|
| Employee | |
| Manager | |
| People/HR team | |

## 7. Exceptions and adjustments
How to ask for an exception or reasonable adjustment, who decides, how quickly.

## 8. Breaches
What happens if the policy isn't followed (link to disciplinary policy). Protection from retaliation for raising concerns.

## 9. Related policies and documents
- [Policy] [link placeholder]

## 10. Review
Reviewed every [12] months, or sooner if law or business needs change.

---
## Drafting notes (remove before publishing)
### Verify with legal (per jurisdiction)
| # | Item | Jurisdiction(s) | Why it matters |
|---|---|---|---|
### Decisions needed from the business
- [DECISION NEEDED: ...] Options: A / B / C
### Assumptions made
- ...
```

## Guardrails

- Never state that the policy is "compliant" or "legally sound". Always return the verify-with-legal list, even if short.
- Never invent statutory figures (leave days, notice periods, pay rates, thresholds). Put them in the verify list.
- Never draft provisions that discriminate, retaliate against people raising concerns, restrict lawful collective activity, or require disclosure of protected characteristics beyond what law requires.
- For monitoring, data or AI-use policies, flag data-protection and privacy review (e.g. GDPR or local equivalents, consultation duties) before rollout.
- Don't publish or circulate: the user decides when and how to roll out, and whether consultation with employee representatives is required first.

## Common mistakes

| Mistake | Fix |
|---|---|
| Writing "employees shall be entitled to 20 days" from memory | `[DECISION NEEDED]` for the company number + verify the statutory minimum |
| One policy silently applied to five countries | State the scope and add per-country verify items or local annexes |
| Procedure without an owner or timeframe | Each step: who, what, by when |
| Legalese ("hereinafter", "notwithstanding") | Plain words, second person |
| No route for exceptions | Section 7 always names the route and decision-maker |
| Forgetting contractors or remote workers abroad | Ask scope question 2 and 3 explicitly |

## Example

**Brief:** "Hybrid policy, 3 office days a week, staff in London and Bengaluru, ~200 people."

**Upfront questions sent:** who's covered (all employees? contractors?), any roles exempt, union or works council, how to handle requests for more home working, equipment and expenses support, owner and review date.

**Draft excerpt:** "4.1 You must work from your assigned office at least 3 days a week, averaged over a month `[CONFIRM averaging]`. 4.2 Your manager may agree a different pattern with you for business or personal reasons; see section 7." Verify items include: UK statutory right to request flexible working and the employer's response process and timelines; health-and-safety duties for home workers (UK and India); whether Karnataka Shops and Establishments rules, or India's new Labour Codes as their rules take effect, affect working hours or records; and tax/expense treatment of home-working allowances in both countries.
