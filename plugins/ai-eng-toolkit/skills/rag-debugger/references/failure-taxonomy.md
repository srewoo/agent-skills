# RAG failure taxonomy: checks and fixes

Each class: how to confirm it, then fixes in rough order of cost. Confirm before fixing.

## A. Ingestion / parsing

Checks:
- Print the extracted text for the failing page and compare with the rendered document. For PDFs: `pdftotext -layout file.pdf - | less` (poppler) or the project's own parser called directly.
- Scanned PDF? `pdffonts file.pdf` listing no fonts means no text layer: OCR is required.
- Tables: are rows/columns preserved, or flattened into a word soup? Are header rows attached to values?
- Repeated headers/footers, page numbers, cookie banners, nav menus polluting chunks.
- HTML: is the main content extracted, or only boilerplate? JS-rendered pages fetched without rendering are often empty.
- Silent failures: count documents in the source vs documents in the index. A parser exception that is caught and logged skips the whole doc.

Tables in search engines (Elasticsearch, OpenSearch, Solr): check the indexed text, not just the parser output, by fetching the stored document (`GET <index>/_doc/<id>`) and running `_analyze` on a table cell. Cells joined without separators ("Pro40usermonth") or a table stored in a non-indexed / `object` field make both the keyword and the vector leg miss it.

Fixes: a layout/table-aware parser for the doc types that fail; OCR for scanned docs (check OCR confidence); convert tables to one row per line with column headers repeated (`Plan: Pro | Price: $40/user/month`); strip boilerplate; alert on parse failures instead of swallowing them.

## B. Chunking

Checks:
- Open the answer chunk and its neighbours. Is the fact split across a boundary? Does the chunk name its subject, or only say "it" / "this plan"?
- Chunk size distribution: very large chunks (> ~1,000 tokens) dilute the embedding; very small ones (< ~100) lose context.
- Boundaries mid-sentence, mid-table, or mid-code-block.

Fixes: structure-aware splitting (headings, paragraphs, table/code boundaries) before size limits; start around 300-800 tokens with 10-20% overlap and tune on the labelled set; prepend document title and section path to each chunk's text before embedding; small-to-big / parent-document retrieval (match on small chunks, send the parent section to the model).

## C. Embeddings

Checks:
- Query and documents embedded with the **same model and version**? Index metadata vs the query-time config. A silent model upgrade on one side breaks retrieval while dimensions may still match.
- Model-specific input conventions applied on both sides, as documented for that model: e.g. E5 models expect `query: ` / `passage: ` prefixes, Nomic embed expects `search_query: ` / `search_document: `, and several hosted APIs take an input/task type (query vs document). Missing these degrades ranking quietly.
- Distance metric matches the model's intended use; with inner-product indexes, are vectors normalised? Unnormalised vectors let long/high-norm chunks dominate. If vectors were truncated to fewer dimensions (Matryoshka-style), re-normalise.
- Language: an English-only model on non-English queries or docs. Test: embed a translated query and see if ranking recovers.
- Direct test: compute similarity between the query and the answer chunk vs the current top-1. If the answer chunk scores lower even in exact search, it's an embedding/chunk-content problem, not the index.

Fixes: align model/version/prefixes and re-embed; pick a multilingual model for multilingual corpora; fine-tune or switch models only after A, B and D are ruled out.

## D. Lexical gap (needs hybrid search)

Checks: queries with product codes, SKUs, error messages, acronyms, person or part names. Run a plain keyword/BM25 search; if it finds the chunk and vector search doesn't, it's this class.

Hybrid already on? Run each leg alone (keyword only, vector only) for the failing queries and log the answer chunk's rank in each before fusion. If one leg finds it and the fused list doesn't, the fusion is the problem: weighted score fusion of raw BM25 scores (unbounded) with cosine similarities (0-1) lets one leg drown the other unless scores are normalised (min-max or L2), and RRF only sees each leg's top `rank_window_size`. Elasticsearch: `rrf` retriever (`rank_constant`, `rank_window_size`) or `linear` retriever with a `normalizer`; OpenSearch: a search pipeline with the normalization processor.

Fixes: hybrid retrieval (BM25/full-text + vector) fused with Reciprocal Rank Fusion (score = Σ 1/(k + rank), k ≈ 60 is the common default) or a weighted score; most vector databases and search engines support hybrid natively.

## E. Index / ANN parameters

Checks:
- Compare approximate top-k against exact (brute-force) search on the same vectors for the labelled queries. If exact finds it and ANN doesn't, it's the index.
- HNSW: query-time `ef_search` (must be ≥ k; raise to 100-200 for better recall at some latency cost); build-time `M` and `ef_construction`. IVF: `nprobe`/`probes` too low.
- pgvector specifics: `SET hnsw.ef_search = 100;` (default 40) or `SET ivfflat.probes = 10;` (default 1). Filtered queries can return fewer than k rows because filtering happens after the index scan; pgvector 0.8.0+ adds iterative index scans (`SET hnsw.iterative_scan = relaxed_order;` or `strict_order`; `ivfflat.iterative_scan = relaxed_order`).
- Elasticsearch / OpenSearch kNN: `num_candidates` (per shard, must be ≥ `k`) plays the role of `ef_search`; raise it (e.g. 100-500) and compare with an exact `script_score` query on the same vectors. A `filter` inside the `knn` clause is applied during the search; a filter in an outer `bool` query is applied after, and can leave fewer than k hits.
- top-k simply too small for the corpus's redundancy (many near-duplicate chunks crowd out the answer). Check for duplicates.

Fixes: raise `ef_search`/`nprobe`; deduplicate near-identical chunks; retrieve more candidates (e.g. 30-50) and rerank down to the prompt budget.

## F. Metadata filters

Checks: rerun the failing query with all filters removed. If the answer appears, inspect that document's metadata: missing field on older docs, wrong type (string `"2024"` vs int), case mismatch, timezone in date filters, tenant/ACL id wrong, language tag wrong. Reproduce with the failing user's actual permissions, not an admin account.

Fixes: backfill metadata; normalise types at ingestion; add a test asserting every indexed doc has required metadata fields.

## G. Reranking

Checks: log candidate ranks and scores before and after reranking. Many cross-encoder rerankers truncate input (often 512 tokens): a long chunk with the answer near the end gets scored on its beginning only. Check the reranker gets the query, not the rewritten query, if the rewrite lost terms.

Fixes: rerank shorter chunks or the relevant window; raise the candidate pool; try without the reranker on the labelled set — sometimes it hurts.

## H. Query rewriting and context assembly

Checks:
- Multi-turn: a follow-up ("and for the Pro plan?") embedded on its own has no subject. Is conversation history condensed into a standalone query?
- Rewriting / HyDE / expansion output: does it drop or change key terms (codes, names)?
- Count tokens of the final prompt vs the model's context and the app's own budget; is anything truncated, and from which end?
- Position: models use information at the start and end of long contexts more reliably than the middle ("lost in the middle", Liu et al., 2023). Where does the answer chunk sit?

Fixes: standalone-question condensation; keep the raw query alongside the rewrite (retrieve on both); order chunks by relevance with the best at the start (or start and end); send fewer, better chunks.

## I. Generation

Checks (the answer chunk is in the final prompt):
- Rerun the exact final prompt several times; is the failure consistent?
- Does the prompt tell the model to answer only from the context and to say when the context lacks the answer? Is that instruction buried below the context?
- Conflicting chunks (old and new versions of a policy both retrieved)? The model may pick the wrong one.
- Citations: are chunk ids/titles in the context so the model can cite them? Validate cited ids exist in the provided context (code check).
- Too much context, or a model tier too small for the reasoning required.

Fixes: explicit grounding and abstention instructions; label each chunk with source and date; remove superseded versions at ingestion; post-check citations programmatically; measure faithfulness on the labelled set before and after.

## J. Staleness and caching

Checks: document `updated_at` vs index build/last-sync time; whether incremental sync handles deletes and updates (or only inserts, leaving old versions); multiple versions of the same doc in the index; a response or semantic cache in front of RAG serving answers from before the update.

Fixes: upsert by stable doc id and delete old chunks on update; scheduled full rebuild as a backstop; invalidate caches on doc updates; show source dates in answers.
