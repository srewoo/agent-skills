---
name: rag-debugger
description: Use when a RAG / retrieval-augmented system, document Q&A bot, "chat with your docs" feature or knowledge-base assistant gives wrong, irrelevant, outdated, incomplete or hallucinated answers, says "I don't know" when the answer is in the docs, cites the wrong source, or got worse after re-indexing, a new embedding model, or a chunking change. Phrases: "RAG is returning garbage", "retrieval isn't finding the doc", "why did it hallucinate", "vector search results are bad".
---

# RAG Debugger

## Overview

Every wrong RAG answer is either a **retrieval** failure (the right text never reached the model) or a **generation** failure (it reached the model and was ignored or misused). Decide which, with evidence from the actual retrieved chunks, before changing anything; then test one hypothesis at a time against a labelled query set.

## When to use

- Specific queries return wrong or missing answers and the content exists in the corpus.
- Quality dropped after an ingestion, chunking, embedding, index or prompt change.
- Answers cite sources that don't support them.

## When not to use

- No labelled examples exist and the question is "how good is our RAG overall": build a suite with `eval-builder`, then return here for the failures.
- Comparing two prompts or models on fixed contexts: use `prompt-regression`.
- The answer genuinely isn't in the corpus: that's a content gap; report it, don't tune retrieval.

## Inputs

| Input | Default if not given |
|---|---|
| Failing queries with the expected answer and where it lives (doc/page) | Ask; at least 5. If the user has one, find 4 similar ones from logs |
| Access to the pipeline code (ingest, chunk, embed, retrieve, rerank, prompt) | Search the codebase for the vector store client and the prompt template |
| Ability to run retrieval alone for a query | Write a small script calling the retriever function directly |
| Index metadata: embedding model, dimension, distance metric, build date | Read from ingestion config / index settings |

## Workflow

### 1. Reproduce and capture the full trace

For each failing query, record in one place: the raw user query, the rewritten query (if any), filters applied, the top-k chunk ids **with scores and full text**, the reranked order, the exact final prompt sent to the model (after truncation), and the answer. Turn on debug logging or add a temporary print at each stage; don't reason from code alone.
**Done when** every failing query has a trace file you can read top to bottom.

### 2. Split retrieval vs generation

For each failing query, find the chunk that contains the answer by searching the chunk store for a distinctive phrase from the expected answer (e.g. SQL-backed stores: `SELECT id, left(content, 200) FROM chunks WHERE content ILIKE '%40/user/month%';` ; Elasticsearch/OpenSearch: `{"query": {"match_phrase": {"content": "40/user/month"}}}` against the chunk index; otherwise the store's keyword/metadata query or an export of all chunks plus `grep`). If the phrase lives in a table, also try a single cell value, since flattened tables rarely keep the phrase intact. Then:

| Answer-bearing chunk… | Failure class | Go to |
|---|---|---|
| does not exist in the chunk store | Ingestion / parsing | Taxonomy A |
| exists but text is garbled, split mid-fact, or missing its heading/context | Chunking / parsing | A, B |
| exists, clean, not in the retrieved top-k | Retrieval ranking | C-G |
| retrieved but dropped by reranker, filter, or truncation before the prompt | Post-retrieval | F, G, H |
| present in the final prompt, answer still wrong | Generation | I |

**Done when** each failing query has one class and the evidence (chunk id, rank, score) written next to it.

### 3. Walk the failure taxonomy for that class

Short form below; checks and fixes with commands are in [references/failure-taxonomy.md](references/failure-taxonomy.md).

| # | Class | Typical symptom | First check |
|---|---|---|---|
| A | Ingestion / parsing | Tables, scanned PDFs, headers/footers, multi-column layouts produce junk or nothing | Print the extracted text of the source doc; diff against what a human sees |
| B | Chunking | Fact split across chunks; chunk lacks the entity it talks about ("it costs $40") | Inspect the neighbours of the answer chunk; check size/overlap/boundary rules |
| C | Embeddings | Semantically obvious match ranks low; non-English queries fail | Same model + version + prefixes for queries and docs? Vectors normalised for the metric? |
| D | Lexical gap / fusion | Exact codes, SKUs, error strings, names not found | Does a keyword search (BM25 / full-text) find it? If yes, add hybrid search; if hybrid is on, rank the answer chunk in each leg before fusion |
| E | Index / ANN params | Results differ from brute-force search on the same vectors | Compare ANN top-k vs exact kNN; check `ef_search` / `nprobe` / `num_candidates`, top-k |
| F | Metadata filters | Right doc never returned for some users/tenants/dates | Rerun with filters removed; inspect the doc's metadata values |
| G | Reranking | Answer chunk retrieved at rank 3, reranked out | Log scores before and after rerank |
| H | Query rewriting / context assembly | Rewrite drops key terms; prompt truncated; answer chunk mid-context | Compare raw vs rewritten query; count prompt tokens vs budget; note position of answer chunk |
| I | Generation | Context contains the answer, model ignores it, contradicts it, or invents a source | Rerun the exact prompt; check instructions, conflicting chunks, citation format |
| J | Staleness | Old answer for updated doc; deleted doc still cited | Compare doc `updated_at` vs index build time; check for duplicate versions in the index |

**Done when** each failing query has at least one hypothesis with a concrete check you can run.

### 4. Measure before fixing

Label 20-50 queries (the failing ones plus representative passing ones) with their relevant chunk ids, dump what the retriever returns (ranked ids, at the stage you are testing: raw retrieval or post-rerank), and run this skill's stdlib script [scripts/retrieval_metrics.py](scripts/retrieval_metrics.py) (Python 3.9+):

```bash
python3 <this-skill>/scripts/retrieval_metrics.py retrieval_dump.jsonl --k 1,3,5,10
# line: {"id": "q1", "query": "...", "relevant": ["policy.pdf#12"], "retrieved": ["faq.md#3", "policy.pdf#12", ...]}
```

Chunk ids change when chunking changes. For chunking or parsing experiments, label at document level (map retrieved chunks to their doc id; the script keeps each id's first rank) or mark a retrieved chunk relevant when it contains the answer string, so before/after numbers stay comparable.

Metrics to track:

| Metric | Measures | Rough healthy range |
|---|---|---|
| recall@k (k = the number of chunks you put in the prompt) | Did the answer reach the model? | ≥ 0.85 for Q&A over curated docs |
| MRR | How high the first relevant chunk ranks | ≥ 0.6 |
| Context precision | Share of prompt chunks that are relevant (noise) | Higher is better; low precision + long contexts hurt generation |
| Faithfulness | Share of answer claims supported by the context | ≥ 0.9; below means generation failure (I) |

Context precision and faithfulness need an LLM judge or human labels (Ragas, DeepEval and similar libraries implement them); calibrate any judge as described in `eval-builder`. Ranges are starting points, not standards; set targets from your baseline.
**Done when** a baseline row of numbers exists for the current config.

### 5. Run one-variable experiments

For each hypothesis, change exactly one thing, rebuild only what that change requires, and re-measure on the same labelled set:

```text
H1 chunk size 1200→500 tokens, overlap 0→15%   recall@5 0.62 → 0.78   keep
H2 add BM25 hybrid (RRF fusion)                 recall@5 0.78 → 0.86   keep
H3 reranker top-n 3→8                           recall@5 0.86 → 0.86   discard
```

Never change chunking and embedding model in the same experiment. Re-embedding the corpus is costly: test on a sample index of the affected documents first. After retrieval fixes, confirm end-to-end answers with `prompt-regression`-style per-case comparison.
**Done when** each hypothesis is marked confirmed / rejected with its numbers.

### 6. Write the diagnosis report

Use the template below. Recommend fixes in order of evidence strength and cost.

## Output

```markdown
## RAG diagnosis: <system>, <date>
Scope: <n> failing queries, labelled set of <m> queries. Index: <embedding model+version>, <metric>, built <date>.

### Summary
<2-3 sentences: dominant failure class, top fix, expected effect>

### Per-query classification
| Query | Expected source | Answer chunk rank (pre/post rerank) | In final prompt? | Class | Evidence |
|---|---|---|---|---|---|
| "refund for annual plan?" | policy.pdf p.12 | not in store | no | A: table parsed as empty | extracted text of p.12 is blank |

### Hypotheses and experiments
| # | Hypothesis | Experiment (one variable) | Before → after | Status |

### Baseline vs best config
| Metric | Baseline | Best | Config change |

### Recommended fixes (ordered)
1. <fix> — evidence: <experiment #> — cost: <re-index? latency?> — risk
### Not the cause (ruled out, with evidence)
### Open questions / content gaps
```

## Guardrails

- Don't re-index, delete or overwrite a production index or vector collection; build a parallel one and ask before switching.
- Don't print or commit sensitive document contents or user queries in the report beyond the excerpt needed as evidence; redact PII.
- Don't declare a root cause without the trace evidence from step 1; "probably the embeddings" is a hypothesis, not a finding.
- Keep the labelled query set; it becomes the regression suite (hand it to `eval-builder`).

## Common mistakes

| Mistake | Fix |
|---|---|
| Tweaking the prompt when the answer chunk never reached it | Split retrieval vs generation first (step 2) |
| Raising top-k to 50 to "fix" recall | Fixes recall, hurts precision, cost and lost-in-the-middle; fix ranking or add a reranker |
| Judging retrieval by eyeballing 3 queries | recall@k / MRR on 20-50 labelled queries |
| Changing chunking and embedding model together | One variable per experiment |
| Query embedded with a different model or missing the query prefix the model requires | Same model/version both sides; apply the documented query/document prefixes |
| Assuming the PDF parser worked | Print the extracted text for the failing page |
| Filters tested only with an admin account | Reproduce with the failing user's tenant/permissions |

## Example

Users report the bot says "no information" for plan pricing. Trace: the pricing doc's chunks are in the store, but the answer chunk ("Pro: $40/user/month") ranks 37th for "how much is Pro". Neighbour inspection shows the table was flattened into rows without the header, so the chunk never says "price". Class B (chunking) with A (table parsing). Experiment 1: table-aware parsing that repeats column headers per row, 40 labelled queries: recall@5 0.55 → 0.83. Experiment 2: add BM25 hybrid for plan names: 0.83 → 0.90. Faithfulness unchanged at 0.94, so generation is not implicated. Report recommends both, with a parallel index built for review.
