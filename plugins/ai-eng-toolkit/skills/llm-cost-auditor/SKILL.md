---
name: llm-cost-auditor
description: Use when someone says "our OpenAI / Anthropic / Gemini bill is too high", "cut LLM costs", "where are we spending tokens", "audit our LLM usage", "is prompt caching working", "should we use a cheaper model", or the LLM invoice jumped, token usage grows faster than traffic, or finance asks for cost per feature. Works on a codebase, usage logs, or provider billing exports.
---

# LLM Cost Auditor

## Overview

Most LLM spend sits in a few call sites. Find every call site, attach real volume and token counts to each, then apply savings levers in order of size — and ship none of them without an eval proving quality held. Prices change often: always look up current per-token prices; never rely on remembered numbers.

## When to use

- The LLM bill is high or rising and nobody knows which feature drives it.
- Planning a model migration or tiering strategy for cost reasons.
- Checking whether prompt caching, batching or output limits are actually in effect.

## When not to use

- Validating the quality of a specific change: use `prompt-regression` (this skill hands each proposed change to it).
- No eval suite exists for a call site you want to change: build one with `eval-builder` first, or mark that lever "blocked: no eval".
- Self-hosted GPU capacity planning: different problem (utilisation, batching servers, quantisation), not covered here.

## Inputs

| Input | Default if not given |
|---|---|
| Codebase | Current repository |
| Usage data: per-call logs, observability traces, or provider usage/billing export | Ask once. Without it, estimate volume from traffic metrics and say so in the report |
| Current provider prices for each model in use | Look up on the providers' official pricing pages; record the date |
| Quality bar per call site | "No regression on the existing eval suite"; flag sites with no suite |

## Workflow

### 1. Find every LLM call site

Search the codebase (exclude `node_modules`, `.venv`, `vendor`, `dist`):

```bash
rg -n --hidden -g '!{node_modules,.venv,venv,vendor,dist,build}/**' \
  -e 'chat\.completions\.create|responses\.create|messages\.create|generate_content|generateContent' \
  -e 'embeddings\.create|embed_content|embedContent|batches\.create' \
  -e 'litellm\.(a?completion|embedding)|ChatOpenAI|ChatAnthropic|ChatGoogleGenerativeAI|ChatVertexAI|AzureChatOpenAI|init_chat_model' \
  -e 'generateText|streamText|generateObject|invoke_model|converse(_stream)?\(' \
  -e 'from openai|import openai|from anthropic|import anthropic|google\.genai|@anthropic-ai/sdk|@google/genai|"openai"' .
# model ids hardcoded or in config:
rg -n -i --hidden -g '!{node_modules,.venv,venv,vendor,dist,build}/**' -g '*.{py,ts,js,go,java,kt,rb,cs,yaml,yml,json,toml}' -g '.env*' \
  -e '(gpt|o[1-9]|claude|gemini|llama|mistral)-[a-z0-9.\-]+' .
```

No `rg`? Use `grep -rnE '<same pattern>' --include='*.py' --include='*.ts' .` and so on. Also check for gateways/proxies (LiteLLM proxy, an internal "llm-service") where many features funnel through one client: the call site is then the caller of that wrapper, so trace one level up. In monorepos, run per package and label sites `package:file:function`.

For each site record: file:function, feature, model (resolved from config/env), streaming or not, whether it runs per user request / per background job / per document, and retry policy.
**Done when** a call-site list exists and every hardcoded model id found by the second search maps to a site.

### 2. Attach volume and tokens

Best to worst source:
1. **Per-call usage logs or traces** with token counts from the API's `usage` field. Convert them to the JSONL format in [scripts/cost_rollup.py](scripts/cost_rollup.py) (`--help`), noting provider-specific field quirks in [references/provider-levers.md](references/provider-levers.md).
2. **Provider usage export** (by model, sometimes by API key or project): gives totals; split across sites using request counts from app metrics.
3. **Estimate**: tokens from a sample of real prompts (provider token-counting endpoints or tokenizer libraries; ~4 characters per token for English as a last resort) × calls/month from traffic metrics.

Fill a prices file from the current pricing pages (USD per 1M tokens: `input`, `output`, optional `cached_input` and `cache_write`) and run:

```bash
python3 <this-skill>/scripts/cost_rollup.py usage.jsonl --prices prices.json --days 7
```

A site whose `p95 in` is several times its `avg in` has inputs that grow per call (typically full chat history resent every turn); a high `dupes` share means identical requests that a response cache or dedupe would remove. Reconcile: the summed estimate should be within ~20% of the actual invoice for the same period. If not, a call site is missing (embeddings, evals, batch jobs, a forgotten cron) — go back to step 1.
**Done when** each site has calls/month, avg input/output tokens and $/month, and the total reconciles or the gap is explained.

### 3. Apply levers, biggest first

Work top-down through the sites that make up ~80% of spend. For each, check the levers in this order (typical size of saving, largest first):

| # | Lever | Check | Typical saving | Quality risk |
|---|---|---|---|---|
| 1 | **Remove or dedupe calls** | Identical requests repeated (`dupes` column), calls whose output is unused, LLM doing what code can (regex, lookups, date parsing), retry storms, agent loops without an iteration cap | 100% of the removed calls | None to low |
| 2 | **Model tiering / routing** | Classification, extraction, routing, short rewrites on a frontier model; use a smaller tier, or route easy inputs to it and escalate on low confidence | Often large; price gaps between tiers of the same provider are commonly an order of magnitude — compute from current prices | Medium: must pass evals |
| 3 | **Prompt caching** | Large static prefix (system prompt, tool definitions, few-shot, documents) repeated across calls but placed after dynamic content, or cache usage fields at 0% | Large on input-heavy calls with a stable prefix | None if prefix unchanged |
| 4 | **Batch APIs** | Non-interactive work (nightly summaries, backfills, eval runs, embeddings of a corpus) sent through the synchronous API. Major providers price batch jobs at about 50% off with up to ~24h turnaround | ~50% of those calls | None; latency only |
| 5 | **Trim input** | Full chat history resent each turn (cap it: keep the last N turns or a token budget, e.g. LangChain `trim_messages`, and summarise older turns), unused tool definitions (they count as input tokens), oversized few-shot sets, whole documents where an excerpt suffices, retrieval top-k larger than needed | 20-70% of input | Medium: must pass evals |
| 6 | **Trim output** | Verbose prose where a label or JSON field is consumed; no output limit; reasoning effort/thinking budget higher than the task needs (reasoning tokens bill as output) | Varies; output tokens usually cost several times input per token | Low-medium |
| 7 | **Embeddings hygiene** | Re-embedding unchanged documents on every sync; embedding the same query repeatedly | Small to medium | None |

Notes that keep the audit correct:
- **Streaming does not reduce cost**; it changes latency perception only.
- A lower `max_tokens` saves money only on responses that would have exceeded it, and truncates them; prefer instructions and structured output that make responses short, then set the cap as a safety net.
- Caching rules differ by provider (explicit breakpoints vs automatic prefix caching vs separately created caches with storage cost, minimum prefix lengths, TTLs, write surcharges). Read [references/provider-levers.md](references/provider-levers.md) and confirm in the provider's current docs before estimating.
- Trimming history and caching interact: an append-only history keeps the cached prefix valid, while dropping the oldest turns every call changes the prefix and kills cache hits. Trim in steps (summarise every N turns) or measure cache hit rate before and after.
- Savings from different levers don't add up linearly: computing caching savings after tiering uses the new model's prices.

**Done when** each top site has its applicable levers with a $/month saving computed from its own tokens × current prices, and a risk rating.

### 4. Gate every change on evals

For each lever with quality risk above "None": name the eval suite that covers the call site and the `prompt-regression` comparison that must pass (baseline vs candidate on the same cases, ≥ 3 samples). No suite → the lever is "blocked: build eval first" in the report. Also verify zero-risk levers mechanically: caching shows non-zero cached-token counts in responses; batch jobs complete within the needed window.
**Done when** each recommendation states its validation method.

### 5. Report

Produce the output below, sorted by saving. Implement changes only if the user asks; each one as a separate, reversible change behind config or a flag where possible.

## Output

```markdown
## LLM cost audit: <system>, <date>
Data: <source, period>. Prices looked up <date> from provider pricing pages. Estimated total $<x>/month; invoice $<y> (gap <z>%: <explanation>).

| # | Call site | Model | Calls/mo | Avg in/out tok | Est. $/mo | Lever | Est. saving $/mo | Risk | Validation |
|---|---|---|---|---|---|---|---|---|---|
| 1 | support/answer.py:generate | large-tier | 210k | 6,000 / 400 | 5,040 | Move static policy text before user msg; enable caching | ~2,700 | None | cached tokens > 0 in logs |
| 2 | tagger/classify.ts:tag | large-tier | 600k | 900 / 5 | 1,665 | Small tier | ~1,500 | Medium | prompt-regression on tagger suite (80 cases) |
| 3 | jobs/nightly_summary.py | mid-tier | 9k | 12,000 / 800 | ... | Batch API | ~50% | None | job SLA 24h ok |

Total estimated saving: $<s>/month (<p>% of spend), not additive across levers on the same site — computed sequentially.

### Blocked / needs decision
- <site>: tiering blocked, no eval suite.
### Assumptions
- <volume estimates, token estimates, price date>
```

## Guardrails

- Never hardcode or quote per-token prices from memory; cite the pricing page and date.
- Never switch a model, shorten a prompt, or lower top-k in production without the eval gate in step 4.
- Don't log or paste full prompts containing user data into the report; use token counts and redacted excerpts.
- Ask before running anything that makes paid API calls at volume (token-counting thousands of prompts, eval runs).
- Recommendations that change user-visible latency (batching, smaller models) need product-owner sign-off; list them as decisions, not done deals.

## Common mistakes

| Mistake | Fix |
|---|---|
| Optimising the call site that is easiest to change, not the biggest | Sort by $/month; work the top ~80% |
| Counting only chat calls | Include embeddings, eval/judge runs, batch jobs, retries |
| "Turn on streaming to save money" | Streaming costs the same tokens |
| Dynamic content (timestamp, user name) at the top of the prompt | Static content first, dynamic last, or the prefix never caches |
| Claiming caching savings without checking usage fields | Verify cached-token counts in real responses |
| Summing savings from tiering + caching on the original price | Apply levers sequentially |
| Swapping to a cheaper model because it "looked fine" on 5 prompts | `prompt-regression` on the site's eval suite |

## Example

A SaaS support product: invoice $9.4k/month. Search finds 7 call sites; usage logs for 7 days cover 6 (the 7th, a nightly summary job, explains the 11% invoice gap). Top site, the support answer generator, puts the user's name and date in the first line of a 5k-token system prompt, so cached tokens read 0%; moving them to the end makes the prefix cacheable (est. −$2.7k). The ticket tagger outputs a 5-token label from a large model; a small tier passes the 80-case tagger suite with 0 regressions (est. −$1.5k). The nightly summaries move to the batch API (−50% on $900). Tiering for the answer generator is listed as blocked: no eval suite.
