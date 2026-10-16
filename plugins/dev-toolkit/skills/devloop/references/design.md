# Design — architecture & infra decisions

Read this during Phase 2b. It runs when the change plan does any of: adds a
module/service or a file that follows no existing pattern; adds or changes a
public contract (API, event, schema, CLI flags); adds a datastore, table,
cache, queue or key namespace; adds an env var, secret, config entry or
deploy-manifest change; calls a new external system; has a non-functional AC
(durability, latency, scale, security, "configurable without a code change");
or has two plausible homes.

The goal is not a clever design; it is that every decision the change forces is **written down, sourced, and either settled,
defaulted in the open, or asked** — never made silently.

## 1. Inventory (what exists — cite a source for every line)

| Area | What to find | Where to look |
|---|---|---|
| Runtime & deploy | where it runs, replica count/autoscaling, persistent vs ephemeral storage, restart behaviour | Helm charts, k8s manifests, Terraform/Pulumi, serverless config, Dockerfile — **including a deploy repo outside this checkout** (read-only) |
| Data & state | datastores, key namespaces, TTLs, capacity, eviction | client modules, chart values, migrations, ADRs |
| Messaging | queues/topics/events actually enabled per environment | env/config schema + deployed values |
| Config & secrets | which values come from config files vs a secret store, how a new key is added and who can write it | env schema, values files, secret-store references |
| External systems | every system the change calls; is a credential/app already provisioned | code search, config, secret references (names only, never values) |
| Observability | what is actually on in prod (logs, metrics, traces) | logger/metrics modules + deployed flags |
| Standards | org + repo rules that constrain the design (audit-event requirements, file-size limits, layering, branch rules) | `AGENTS.md`/`CLAUDE.md`/`CONTRIBUTING`, the user's own global agent instructions, ADR folder |
| Prior work | is the ask already (partly) built? | ADRs, search for the feature's nouns, recent PRs |

**Finding the deploy repo:** take the service name from the Dockerfile, CI
deploy job or README, then search your org's code host for it (a charts or
infra repo with a folder of that name). Not found → say so; don't guess.

**When sources disagree**, trust: values applied per environment (the deploy
repo's env values) → manifests in this repo → code defaults → docs and notes.
Note every stale source you override.

A recommendation that deviates from any standard (repo or the user's own
instructions) is an `ask`.

## 2. Decision checklist

For each row, decide whether the change forces a decision. Skip rows it
doesn't touch — don't invent decisions.

1. **Placement** — which module/service owns this code. Check the brief's Repo
   rules first: "don't grow file X, split instead" or "one export per file"
   rules options out before you weigh them.
2. **Contract** — new/changed API, event, schema, CLI flag; backwards compat.
   An existing field that keeps its type but changes meaning (a `skippedCount`
   that now also counts a new kind of skip) is a contract change — every reader
   is affected. Prefer a new field.
3. **Data & state** — store, durability across restarts, TTL, capacity, idempotency/dedup.
4. **Execution & failure** — sync vs async, timeouts, retries, behaviour when the dependency is down.
5. **Config & secrets** — source of each new value, who can change it, whether "configurable without a code change" holds for that source.
6. **Infra & deploy** — any manifest/values/secret change, which repo, who applies it.
7. **Rollout & rollback** — feature flag? reversible by config, or needs a revert/migration?
8. **Observability** — how success and failure are seen in prod, using what is actually enabled.
9. **Security** — trust boundaries, authn/authz, tenant isolation, PII in logs.
10. **Cost** — LLM tokens, storage, calls per request, third-party quotas.
11. **Standards compliance** — the recommendation satisfies every Standards row.

## 3. Options and classification

For each forced decision give 2–3 options. Option A is "reuse what exists / no
new infra" whenever it can meet the ACs. Recommend one; the reason cites an AC
or NFR and an inventory fact.

| Class | When | What you do |
|---|---|---|
| `settled` | the ticket, a review, an ADR or a repo standard decides it | cite the source; no question |
| `default` | one option is clearly best **and** cheap to reverse **and** changes no contract, data, infra, cost or standard | pick it; list it so the user can override |
| `ask` | it changes a contract, data shape/durability, infra or cost, or crosses a team/repo boundary; **or** is hard to reverse; **or** two options are close; **or** the recommendation deviates from a standard | ask (below) |

Anything you'd file under "decisions I made myself" that fits the `ask` row is
an `ask`. Redefining what an existing field, count or status means is `ask`, never `default`.

## 4. Asking

- All `ask` decisions in **one** message, up to 4 questions, ordered by how many
  ACs each blocks. More than 4 → ask the top 4, list the rest under Open
  questions, ask them after the answers.
- Each question: recommended option first, marked `(Recommended)`; each option
  states its trade-off in one line (cost, what breaks, how reversible). Show
  config/contract shapes side by side when comparing them.
- In the same message, list the `default`s one line each ("Defaulting: no retry
  — AC2 only forbids slowing the request; a lost notification is acceptable").
- Prerequisites that block an AC (credential not provisioned, app not created,
  another team must merge a chart change) are asked **now**, not left for the report.

## 5. Record

```
## Design                     (Phase 2b; or "not needed — <reason>")
Inventory: <one line per area touched, each with source>
| # | Decision | Chosen | Class (settled / default / ask→answered) | Source / why | Reversible? |
Prerequisites: <what, owner, blocks which AC>
Infra changes: <in this repo (in the diff) | in other repos/systems (listed, not done)>
ADR suggested: <yes/no — yes for a new datastore/service, public contract, or cross-team infra>
```

Hard-to-reverse decisions → suggest an ADR in the report; don't write it unless asked.
