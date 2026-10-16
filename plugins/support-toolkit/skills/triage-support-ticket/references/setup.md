# Company setup for triage-support-ticket

Fill this once per company and keep it next to the skill (or paste it into the chat with the ticket). The skill reads it at step 0. Anything left blank falls back to the generic behaviour and the related gate is marked `blocked` where a lookup is needed. Never put credentials or API keys in this file.

## 1. Data-source map

| Source | Tool / integration / URL the agent uses | Notes (auth, read-only account, rate limits) |
|---|---|---|
| Helpdesk (Zendesk, Freshdesk, Intercom, HubSpot, JSM, Help Scout, Salesforce Service Cloud, …) | | Which fields hold symptom, product area, severity, root cause |
| Ticket history for clustering / past resolutions (helpdesk search, warehouse table, export) | | Table/view name, freshness |
| KB / help centre | | Does the API return full article bodies? |
| Product docs / changelog | | |
| Bug tracker (Jira, Linear, GitHub Issues, GitLab, Azure DevOps) | | Projects to search |
| Status page / incident tool | | |
| Deploy / release log | | |
| Logging / APM (Datadog, Grafana/Loki, Splunk, Sentry, New Relic, …) | | Log label for service, per-region instances |
| Session replay / RUM | | Keyed on user id or email? |
| Account / tenant admin (admin console, internal API, data warehouse) | | User table, state values, config endpoint |
| CRM (account owner, plan) | | Owner field, placeholder values to treat as unknown |
| Code / config search | | |
| Call or chat transcripts | | |

## 2. Tenancy and region

- Tenant identifier and where it appears in a ticket: `e.g. subdomain of <tenant>.example.com; helpdesk org field "Account ID"`
- Vanity domains that must be mapped to the canonical id: `e.g. support.acme.com → acme`
- Regions / data residency and how to tell them apart: `e.g. hostname suffix .eu → EU logs and DB`
- User state values and what each means: `e.g. invited, active, suspended, deactivated, deleted`
- Login methods and where to read them per tenant:

## 3. Taxonomy

- Symptom values: (default list in gates.md)
- Product areas:
- Root-cause categories used on closed tickets:

## 4. Queues and routing

| Ticket is about | Goes to (queue / group / email) |
|---|---|
| Billing, invoices, refunds | |
| Sales, upgrades, pricing | |
| Legal, privacy (deletion / access requests), DPA | |
| Security vulnerability report | |
| Abuse / trust & safety | |
| Other product lines | |
| Engineering escalation (how to file: project, issue type, labels, required fields) | |

## 5. Standing authority rules

| Account / segment | Rule | Applies to |
|---|---|---|
| `e.g. Partner X end users` | `forward to the partner's help desk, do not answer the user` | `user requests only, not platform faults` |

## 6. SLA tiers and severity

| Tier / plan | First response | Update cadence | Escalation threshold |
|---|---|---|---|
| | | | |

Severity definitions (e.g. S1 = all users blocked, no workaround):

## 7. Tone and format

- Language(s) and locale for replies:
- Greeting and sign-off: `e.g. "Hi <first name>," / "Best regards,"`
- Voice: `e.g. plain, warm, no exclamation marks, no blame`
- Phrases to avoid: `e.g. "unfortunately", "as per", "working as intended"`
- Workarounds the agent may offer (backup login link, CSV export, manual sync):
- What may never be promised (dates, credits, roadmap):

## 8. Merge and duplicate policy

- Merge or link duplicates from the same account?
- Which ticket survives (oldest, the one with most context)?
- Merge note wording:

## 9. Tunable thresholds

The skill ships with these **starting defaults**. They are heuristics, not facts about your queue: a high-volume B2C desk and a 50-ticket-a-week B2B desk need different numbers. Check them against 20-30 of your own closed tickets and write your values in the third column; the skill uses yours when filled.

| Threshold | Default | Yours |
|---|---|---|
| Duplicate window: same requester, same ask | 7 days | |
| Cluster window around ticket time | ±7 days | |
| Cluster size (distinct requesters) | 3 | |
| Standing forwarding pattern: rate / minimum sample | 25% over ≥ 40 tickets | |
| "New user" age that overrides forwarding | 7 days | |
| Minimum comparable closed tickets before the modal root cause counts | 10 | |
| Incident / status / deploy check window | ticket time ± 24 h | |
| Log window | ticket time −2 h to +30 min | |
| Code/doc search reranker score: evidence / hint | ≥ 0.85 / 0.65-0.85 (tool-specific; calibrate) | |
