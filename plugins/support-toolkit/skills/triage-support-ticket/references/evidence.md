# Evidence gates in detail: known defects, KB, past resolutions, deep investigation, timing

Reference for `triage-support-ticket`. Load it when you reach steps 6–9.

## Known defect, incident, outage (step 6)

**One search per ticket, on that ticket's own words.** Defect titles are written by engineers in product vocabulary; tickets are written by customers in symptom vocabulary. One batched query across several tickets matches none of them and reports "no known defect", which is worse than a blocked gate because it reads as a finding.

Run 2–3 searches with different vocabularies:
- the error string verbatim (`SESSION_NOT_ESTABLISHED`, `invalid_grant`)
- product area + symptom in engineering terms (`SAML callback redirect loop`, not `keeps bouncing me`)
- the feature name the customer used, if it is a real product noun

Examples:
- Jira: `text ~ "\"redirect loop\"" AND statusCategory != Done ORDER BY updated DESC`
- GitHub: `gh issue list --search "redirect loop in:title,body" --state open`
- Linear / Azure DevOps / GitLab: the equivalent full-text search over open issues

Do not bound by creation date: an open defect may predate the ticket by months. Search every project that could own it.

Also check, over ticket time ± 24 h: the public status page, the incident tool (PagerDuty, Opsgenie, incident.io, a status channel), and the deploy log for the suspected component.

Service-health dashboards: read the runtime signals (crash loops, OOM kills, error rate, health checks failing), not a summary "severity" badge, which can be driven by something unrelated to whether the service works.

"No defect found" in `WHY` must list the queries you ran. If you ran one, say one.

## KB and docs (step 7)

- Retrieve the full article body, not a snippet. Many KB APIs and search tools default to returning metadata or a snippet; ask for full content. Never cite an article you have not read.
- Articles are structured (tables of failure modes, per-plan steps). Picking the right row is the job. "Import fails only for files over the size limit" is a different answer from "check the file encoding", in the same article.
- A high retrieval score measures similarity to the words, not that the article applies to this user.
- **The enablement line.** Admin articles often say "contact your account manager to enable this feature". The steps exist only for tenants that have it. Before "you can do this yourself", confirm the flag from step 5; if you cannot, write "we can make this change for you, confirm and we'll action it" or put the check in `CHECK FIRST`. Right article, wrong actor still bounces.
- On an identity-shaped ticket, the KB answer is valid only if step 5 confirmed the account exists and is in the state the article assumes.

**Second source: code and config search.** If you can search the codebase or a code-knowledge tool (repo search, Sourcegraph, GitHub code search, an internal docs index), search the symptom in product terms. It is not time-bound: it answers as well on a six-week-old ticket as on a new one, and it finds rules the KB never documents (a timeout threshold, a default setting, a gating condition). With a reranked tool, a starting default is score ≥ 0.85 as evidence, 0.65–0.85 as a hint, < 0.65 as nothing; scores are not comparable across tools, so calibrate on a few known answers and record yours in setup.md §9. When code and KB disagree, prefer the one whose wording fits the ticket's specifics, and say which you built on. Never paste code, file paths or setting keys into the customer reply.

## Past resolutions (step 8)

The KB says what should work; closed tickets say what did. A matching past root cause outranks a KB article when they disagree.

```sql
SELECT id, account, root_cause_category, root_cause_detail, resolution_steps
FROM tickets
WHERE status IN ('solved', 'closed')
  AND coalesce(root_cause_detail, '') <> ''
  AND symptom = :symptom AND product_area = :product_area
  AND id <> :this_ticket          -- never read your own answer
ORDER BY created_at DESC
LIMIT 20;
```

Without a structured root-cause field, read the last agent reply and internal notes of the 10–20 nearest closed tickets and write the cause yourself. Use full-text search (`to_tsvector`/`plainto_tsquery`, the helpdesk's search) rather than stacked `ILIKE` over the whole corpus, which times out.

### No warehouse: search the helpdesk itself

Search with the symptom's distinctive words (error string, feature name) plus a date floor, read the 10-20 nearest solved tickets, and write the cause yourself. Verified syntax (2026):

- **Zendesk**: `GET /api/v2/search.json?query=type:ticket status:solved created>2026-07-01 "redirect loop"`; add `organization:acme` for the account-scoped run. Same string works in the agent search box. Max 1,000 results, 100 per page.
- **Freshdesk**: the filter API `GET /api/v2/search/tickets?query="status:4 AND created_at:>'2026-07-01'"` (whole query in double quotes, URL-encoded; status 4 = Resolved, 5 = Closed) filters only on fields such as `status`, `priority`, `type`, `tag`, `group_id`, dates and custom fields, **not on subject or body text**. Use it with a symptom tag or custom field, or use the agent UI's keyword search for text. 30 per page, 10 pages max.
- **Intercom**: `POST /conversations/search` with `{"query":{"operator":"AND","value":[{"field":"source.body","operator":"~","value":"redirect"},{"field":"state","operator":"=","value":"closed"},{"field":"created_at","operator":">","value":"<unix ts>"}]}}`. `~` matches single words, not phrases.
- **HubSpot**: `POST /crm/v3/objects/tickets/search` with `"query":"redirect loop"` (searches `subject`, `content` and a few defaults) plus a `filterGroups` filter such as `{"propertyName":"createdate","operator":"GTE","value":"<epoch ms>"}`; closed is a pipeline stage id in your portal, so look it up first.
- **Jira Service Management**: JQL `project = SUP AND text ~ "redirect loop" AND statusCategory = Done AND created >= -90d`.

**Exclude this ticket and its merged children.** A closed ticket is the best text match for itself, so without the guard you "derive" the answer the human already wrote. This matters most when evaluating the skill on closed tickets, which is how anyone measures it; a leaking measurement is worse than none.

**Count before you read the mode.** Under 10 rows (default; tune in setup.md §9) is noise:

| Rows | Backend-fault routing? | Then |
|---|---|---|
| ≥ 10 | either | Use the modal category below |
| < 10 | yes | `escalate to engineering`; say the corpus is thin and give the count |
| < 10 | no | Reply from the KB if the hit is direct, at `CONFIDENCE: low` |

**Modal category → action:**

| Mode | Action |
|---|---|
| `customer_admin_action` | Forward to the customer's admin, unless the requester is the admin; then reply with the steps or do it for them |
| `user_error` | Reply: the fix is something the user does |
| `config` | Reply: support enables or changes it |
| `bug` | Escalate to engineering |
| `environment` (browser, device, network) | Weakest. Often where tickets land when nobody found the cause ("no root cause confirmed"). Look for direct evidence before repeating it |
| `known_issue` | Known issue reply + link |

**A prior is still a prior when it is well written.** Before drafting from a past root cause, it must pass all three:

| Question | Fails when |
|---|---|
| Does it name an artefact this ticket also names (page, integration, file, error string)? | It names a different one, or none |
| Would its mechanism produce this symptom, including scale, timing and who is affected? | The story only works for the other ticket's circumstances |
| Is there anything in this ticket it does not explain? | Yes, and you were about to skip it |

Failing any one: it goes in `WHY` as a candidate, not in the paste block as the cause. The action it implies can survive; the stated cause cannot. Same requester, same screen, same week can still be a different defect.

An account whose tickets are routinely forwarded has empty root causes: nothing was worked. Empty there is a signal, not a gap.

## Deep investigation (step 9)

**Routing.** Use the support team's own labels, not your guess: symptom in {error_or_broken, data_incorrect, data_missing, sync_failure, performance, unexpected_behavior}, or ticket type incident/problem/bug, or severity in your top three tiers, or an engineering-dependency field set. How-to, config, access and billing requests never enter.

**Every step runs on a routed ticket.** The first step that returns something always feels sufficient; that feeling is how wrong answers ship.

| Step | Sees | Blind to |
|---|---|---|
| Session replay / RUM by user id + time window | What the user's browser did: failed requests, console errors, the network (VPN, proxy) | Anything server-side |
| Service health now | Whether the component is unhealthy right now | The ticket's own window, if it was hours ago |
| Logs over the ticket window, right region | What the backend logged | Client-side code, config values, thresholds compiled into the frontend |
| Error tracker (Sentry, Rollbar, Bugsnag) | Grouped exceptions, first-seen time, release | Silent wrong results |
| Deploy / change log | A release just before onset | Whether that release is the cause |
| Code / config search | Rules, defaults, thresholds | Runtime behaviour |

Example queries, adapt names to your stack:
- Datadog logs: `service:auth env:prod-eu status:error @usr.id:<id>`, window = ticket time −2 h to +30 min.
- Grafana Loki: `{app="auth", env="eu"} |= "callback" |~ "(?i)error|denied"`.
- Splunk: `index=prod sourcetype=auth user_id=<id> earliest=-4h`.
- Sentry: issues filtered by `user.id:<id>` or the release before onset.

**Zero rows has two meanings.** The service logged nothing (evidence), or the service/label name is wrong (no evidence at all). Confirm the label or service exists (list label values, list services) before reporting a negative. Service names in a catalog, pod names and log labels often differ; resolve the label from the log tool itself.

**A client-side or config fault does not appear in server logs.** A clean backend log is exactly what you see while a frontend constant kills the user's session. Say logs were silent by design rather than implying nothing is wrong.

**Read the matched line, not the match count.** Short terms match inside random ids and hashes (`sso` inside a session id like `kXsso4`).

**Pick the region deliberately.** A thin result in one region means try the other before concluding, and anchor on something you recognise in the output (the tenant id, the customer domain).

**Inconclusive is a result.** Report it; do not retry until something sounds better.

## Timing: async tools

Most lookups take seconds. Some (warehouse queries via an async service, AI RCA tools, long log scans) take minutes.

1. Decide early which steps need a slow tool (identity via warehouse, deep RCA).
2. Submit it at once, before the cheap gates.
3. Run the fast gates while it works.
4. If the fast gates already fix the action beyond anything the slow result could change, you may abandon it; say so in `ALSO`. If it could contradict the draft, wait.
5. A pending result is neither an answer nor a failure. Judge by elapsed wall-clock time against the tool's own ceiling, not by how many times you polled. If you cannot wait inside one turn, end the turn and resume when it is ready.
6. A request that times out at the transport layer may still have been accepted. Look it up by its input before resubmitting, or you pay twice.

Past the tool's ceiling, it has failed: a failed gate is a blocked gate.
