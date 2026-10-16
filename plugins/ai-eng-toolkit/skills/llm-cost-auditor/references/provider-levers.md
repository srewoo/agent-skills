# Provider-specific levers and usage fields

Provider features and prices change frequently. Treat this as a map of what to look for, then confirm details (discounts, minimum lengths, TTLs, field names) in the provider's current documentation before putting numbers in a report.

## Reading token usage from responses

Normalise every log row to `input_tokens` = all input tokens including cached ones, `cached_input_tokens` = the cached portion, `output_tokens` = all output including reasoning.

| Provider / API | Input | Cached portion | Output | Reasoning / thinking |
|---|---|---|---|---|
| OpenAI Chat Completions | `usage.prompt_tokens` (includes cached) | `usage.prompt_tokens_details.cached_tokens` | `usage.completion_tokens` | `usage.completion_tokens_details.reasoning_tokens` (included in output) |
| OpenAI Responses API | `usage.input_tokens` (includes cached) | `usage.input_tokens_details.cached_tokens` | `usage.output_tokens` | `usage.output_tokens_details.reasoning_tokens` (included in output) |
| Anthropic Messages | `usage.input_tokens` counts only uncached input **after** the last cache breakpoint: total = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` | `usage.cache_read_input_tokens` → `cached_input_tokens`; `usage.cache_creation_input_tokens` → `cache_write_input_tokens` (billed at the write rate) | `usage.output_tokens` (includes thinking) | — |
| Google Gemini | `usage_metadata.prompt_token_count` (includes cached) + `tool_use_prompt_token_count` if present | `usage_metadata.cached_content_token_count` | `usage_metadata.candidates_token_count` **excludes** thinking | `usage_metadata.thoughts_token_count`: billed as output, add it to `candidates_token_count` |
| LangChain (`AIMessage.usage_metadata`) | `input_tokens` already includes cached tokens, for every provider | `input_token_details.cache_read`; `input_token_details.cache_creation` → `cache_write_input_tokens` | `output_tokens` | `output_token_details.reasoning` (included) |
| LiteLLM / gateways | Usually OpenAI-shaped `usage`; check how the gateway maps cache fields | | | |

Check one real raw response per provider before trusting the mapping. Two common errors: copying Anthropic's raw `input_tokens` as the total (cost_rollup rejects rows where cached tokens exceed input), and pricing Gemini output from `candidates_token_count` alone, which drops all thinking tokens.

## Prompt caching

Common rule everywhere: caching matches on an **exact prefix**. Order the request as: tool definitions → system prompt → static documents/few-shot → conversation history → the new user message. Anything dynamic (timestamps, user names, request ids, shuffled tool lists, non-deterministic JSON key order) placed early breaks the prefix for everything after it.

| Provider | How it works (verify current details) | What to check in the audit |
|---|---|---|
| Anthropic | `cache_control` breakpoints on content blocks, or one top-level `cache_control` on the request for automatic caching that moves the breakpoint forward as a conversation grows. Writes cost more than base input (5-minute TTL default; a 1-hour TTL costs more), reads cost a small fraction of base input; minimum cacheable prefix length depends on the model (512 to 4,096 tokens) and shorter prompts silently don't cache | Breakpoints present? `cache_read_input_tokens` > 0 on repeat calls? Calls spaced further apart than the TTL get no hits — and still pay the write surcharge |
| OpenAI | Automatic prefix caching once the prompt reaches 1,024 tokens; cached input billed at a discount that varies by model; no code change needed beyond prefix ordering. `prompt_cache_key` (a stable key per shared prefix or tenant) improves routing to the same cache; retention is set with `prompt_cache_retention` (`in_memory` / `24h`) or, on newer models, a cache TTL option — check the model's docs | `cached_tokens` > 0? Prompts just under 1,024 tokens get nothing |
| Google Gemini | Implicit caching on recent models (automatic discount on repeated prefixes) plus explicit context caching: create a cache object with a TTL and reference it; explicit caches also bill storage per token per hour | `cached_content_token_count` > 0? For explicit caches, is the storage cost lower than the input savings at your call rate? |
| Self-hosted (vLLM, SGLang etc.) | Prefix/KV caching is a server setting; saves GPU time, not per-token fees | Enabled on the server? |

Estimate caching savings per site as: calls/month × cacheable prefix tokens × hit rate × (input price − cached price), minus write surcharges where they apply. Hit rate depends on call frequency relative to the TTL; measure it after enabling rather than assuming 100%.

## Batch APIs

OpenAI (Batch API), Anthropic (Message Batches API) and Google (Gemini batch mode / Vertex AI batch prediction) each offer asynchronous batch processing at roughly half the synchronous price, with results within a window of up to about 24 hours. Fits: nightly jobs, backfills, offline classification, corpus embeddings, eval and judge runs. Check per provider whether batch pricing combines with caching discounts (it differs by provider and model), the batch size/file limits, and exceptions (some embedding batch endpoints discount less than 50%).

## Model tiering

- Compare per-token input and output prices across tiers of the same provider and across providers from the current pricing pages; record the date.
- Reasoning models can cost more per task than their per-token price suggests because of reasoning tokens; compare **cost per task** (avg tokens × price) from real usage, not list prices.
- Routing pattern: cheap model first, escalate to a larger one when a confidence check or validator fails; measure the escalation rate, since a 40% escalation rate can erase the saving.

## Other knobs worth checking

- Reasoning effort / thinking budget parameters: lower settings cut output tokens on simple tasks.
- Structured output / JSON mode: removes prose padding when only fields are consumed.
- `n` > 1 or multiple candidates per request: each candidate bills output tokens.
- Retries: SDK default retry policies on timeouts can multiply cost on long generations; check timeout vs typical generation time.
- Embeddings: hash document content and skip re-embedding unchanged chunks; batch embedding requests.
