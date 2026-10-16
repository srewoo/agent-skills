---
name: onboarding-plan
description: Use when a manager or HR person asks for an onboarding plan, 30/60/90-day plan, first-week schedule, new-starter or new-hire checklist, pre-boarding plan, or buddy programme for someone joining a team, including remote or hybrid joiners, or says "my new hire starts Monday, what should they do?".
---

# Onboarding Plan

## Overview

Good onboarding gets a new hire to clear, measurable early results while building the relationships and context they need. This skill produces a role-specific plan from pre-boarding through day 90, with a day-by-day first week, measurable 30/60/90 goals, named people to meet, and a manager checklist. The manager adapts it with the new hire; nothing in it is an assessment of the person.

## When to use

- A specific person is joining a specific role and the manager wants a plan.
- Creating a reusable onboarding template for a role or team.
- Adapting an office-based plan for a remote or hybrid joiner.

## When not to use

- Writing the job description: use `jd-writer`.
- Writing a company-wide onboarding or probation policy: use `policy-drafter`.
- Setting performance ratings or probation outcomes: those are manager and HR decisions on evidence, outside this plan.

## Inputs

Ask once for missing inputs.

| Input | Default if not given |
|---|---|
| Role, level, team | Required. Ask. |
| JD or the role's first-year outcomes | Use the JD's outcomes; if none, propose and mark `[CONFIRM]`. |
| Start date and time zone | `[Start date]`; Day 1 = Monday. |
| Working pattern: on-site / hybrid (which days) / remote (time-zone gap to the team) | Hybrid, 2-3 office days. Produce the variant notes for the other two. |
| Manager, buddy, key stakeholders (roles or names) | Role placeholders ("Product lead", "Buddy: peer in same team"). |
| Tools, systems and access the role needs | Generic list: email, chat, HR system, role tools `[CONFIRM]`. |
| Mandatory training (security, compliance, etc.) | `[Mandatory training per company policy]`. |
| Anything the new hire has shared about adjustments or preferences | None. Never ask the manager to guess; offer the new hire a chance to share in pre-boarding. |

## Workflow

1. **Anchor on outcomes.** Take 2-4 first-year outcomes from the JD. Work backwards: what must be true at day 90 for the hire to be on track? That becomes the 90-day goal set.
   *Done when:* each 90-day goal links to a role outcome.

2. **Write SMART-style 30/60/90 goals.** Three phases: **Learn** (30), **Contribute** (60), **Own** (90). Each goal must be measurable: a deliverable, a number, or an observable action ("ships first PR to production", "runs 5 customer calls with buddy shadowing, then 3 solo", "presents team process review with 3 recommendations"). 3-5 goals per phase. Avoid goals that depend on things the hire can't control; note dependencies. For roles with production access, on-call, money or customer data, stage it: read-only access and shadowing first, then reverse-shadow (hire leads, buddy backs up), then primary, with the dates `[CONFIRM]` by the manager; senior hires can move faster but still shadow before owning.
   *Done when:* every goal has a measure and a target date.

3. **Plan pre-boarding (offer accepted → day 1).** Equipment shipped and tested, accounts created, welcome message from manager, buddy introduced, first-week schedule sent, paperwork and any right-to-work or employment-eligibility checks through HR (deadlines vary by country: `[confirm for location]`), a question inviting the hire to share any adjustments or preferences (working hours, accessibility needs, how they like to receive feedback), with no obligation to disclose anything.
   *Done when:* every item has an owner (manager, HR, IT, buddy) and a "by" date.

4. **Build week 1 day by day.** Keep days to ~50-60% scheduled, leaving time to absorb. Default shape:
   - **Day 1:** welcome with manager (agenda: role, 30/60/90 plan, how we work), set-up with IT, buddy lunch/coffee, team intro, light reading. Finish with a 15-min check-in.
   - **Day 2:** product/service and customers overview; tools walkthrough; first meetings with 2 key stakeholders.
   - **Day 3:** shadow the team's core workflow; mandatory training block.
   - **Day 4:** first small, real task with buddy (a "first win" achievable in a day or two); stakeholder meetings.
   - **Day 5:** manager 1:1: what's clear, what's confusing, adjust the plan; demo or share the first small task.
   *Done when:* each day has morning/afternoon blocks with owner and purpose.

5. **List stakeholders and learning resources.** Stakeholder table: role, why they matter to this job, what to ask them, by when (most within the first 30 days). Learning resources: docs, recordings, courses, codebases or playbooks, each with a reason and target week. Use placeholders for links.
   *Done when:* 5-12 stakeholders and a learning list sequenced by week.

6. **Set the check-in cadence.** Default: daily 10-15 min check-ins in week 1; weekly 1:1s from week 2; buddy check-ins twice a week for month 1, then weekly; formal 30/60/90 reviews (30-45 min) where the manager and hire review goals together and adjust. Add a skip-level or HR check-in around day 45. Feedback goes both ways: ask the hire what's not working in onboarding.
   *Done when:* cadence table complete.

7. **Add the work-pattern variant** (remote/hybrid/on-site) and the manager checklist, then self-check:
   - [ ] Every 30/60/90 goal is measurable and dated
   - [ ] Pre-boarding items all have owners
   - [ ] Week 1 is day by day and not over-scheduled
   - [ ] Buddy named or placeholder, with responsibilities
   - [ ] Stakeholders and resources listed
   - [ ] Variant notes for the work pattern
   - [ ] Nothing in the plan relies on assumptions about the person's age, family, health, background or other personal characteristics

## Remote and hybrid variants

- **Remote:** ship equipment to arrive ≥ 3 working days before day 1 and test login on a call before start; book a video welcome at a time suitable for the hire's time zone; schedule virtual coffee chats (3-5 in week 1); give written versions of everything said in meetings; set core overlap hours explicitly; if the team is ≥ 4 hours apart, make the buddy someone in a nearer time zone or plan async handoffs; budget for an in-person meet-up in the first 90 days if the company does them.
- **Hybrid:** put day 1 and the first team meeting on an office day with the manager and buddy present; align the hire's office days with the buddy's for the first month; make sure meetings work for remote attendees (camera, shared docs).
- **On-site:** building access, desk, tour, safety induction and emergency procedures on day 1; still keep written notes for later reference.

## Output

```markdown
# Onboarding plan: [Name or "New hire"], [Role], starting [date]
Manager: [ ] · Buddy: [ ] · Work pattern: [on-site / hybrid (days) / remote (time zone)]

## Role outcomes this plan builds toward
1. ... (from JD)

## Pre-boarding
| Item | Owner | By |
|---|---|---|

## Week 1
| Day | Morning | Afternoon | Owner | Purpose |
|---|---|---|---|---|

## 30 / 60 / 90 goals
| Phase | Goal | Measure | Target date | Support / dependency |
|---|---|---|---|---|
| 30: Learn | | | | |
| 60: Contribute | | | | |
| 90: Own | | | | |

## People to meet
| Role / name | Why they matter | What to ask | By |
|---|---|---|---|

## Learning resources
| Resource | Why | Week |
|---|---|---|

## Check-in cadence
| Check-in | With | Frequency | Focus |
|---|---|---|---|

## Buddy responsibilities
- Daily availability in week 1; answers "how things really work" questions; pairs on first task; checks in twice a week for month 1.

## Manager checklist
- [ ] Before day 1: accounts, equipment, welcome message, schedule sent, buddy briefed
- [ ] Day 1: welcome 1:1, walk through this plan, agree communication preferences
- [ ] Week 1: daily check-ins, first small win, introduce to stakeholders
- [ ] Day 30/60/90: review goals together, adjust, record agreed changes
- [ ] Ongoing: ask for feedback on onboarding; remove blockers within 48 hours

## Work-pattern notes
[remote / hybrid / on-site specifics]
```

## Guardrails

- The plan supports the hire; it is not a performance or probation evaluation. Don't add ratings or "pass/fail" language. If the user wants probation criteria, point them to HR and their probation policy.
- Don't make assumptions about the hire based on personal characteristics (age, parental status, nationality, disability, etc.). Accommodate only what the hire shares, via the pre-boarding question.
- Don't include personal data beyond name, role and start date. Don't share the plan with anyone the user hasn't chosen.
- Mandatory legal or compliance training (e.g. health and safety, anti-harassment, data protection) varies by jurisdiction; list it as `[confirm mandatory training for location]`, don't assert which courses are legally required.

## Common mistakes

| Mistake | Fix |
|---|---|
| Goals like "understand the product" | Make it observable: "demo the 3 core workflows to the buddy" |
| Back-to-back meetings all of week 1 | ≤ 60% scheduled; leave absorbing time |
| Remote hire's laptop arrives on day 2 | Ship ≥ 3 working days early; test before start |
| Buddy is the manager | Buddy is a peer; the manager has a different role |
| 30/60/90 reviews only by the manager | Review together; ask the hire for feedback on onboarding |
| Same plan for every role | Anchor goals on this role's outcomes |

## Example

**Input:** "Plan for a remote mid-level Product Designer joining Monday, team is 5 hours ahead, first-year goal: redesign the checkout flow."

**Output (excerpt):** 30 (Learn): "Reviews 5 user-research recordings and shares a 1-page summary of top 3 checkout pain points by day 30." 60 (Contribute): "Ships 2 small UI improvements to production with engineering by day 60." 90 (Own): "Presents checkout redesign proposal with tested prototype (≥ 5 usability sessions) to product lead by day 90." Remote notes: equipment ships 5 working days before start; buddy chosen from the team member with the most overlap; daily async written update in week 1 instead of a late-evening call.
