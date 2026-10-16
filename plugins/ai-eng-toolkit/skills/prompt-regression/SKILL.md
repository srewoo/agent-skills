---
name: prompt-regression
description: Use when someone asks "is the new prompt better", "can we ship this prompt change", "compare old vs new prompt", "we're switching models / upgrading model version / changing temperature — did anything break", "A/B these two prompts", or "the model upgrade changed outputs". Also use before merging any change to a system prompt, model id, sampling parameter or tool definition in an LLM feature.
---

# Prompt Regression

## Overview

Run the baseline and the candidate on the same frozen inputs, several samples each, and compare per case, not just in aggregate. A higher average can hide new hard failures; a ship decision needs the per-case diff, the regressions read by a human, and cost/latency deltas.

## When to use

- A prompt, system message, tool schema, model id/version, temperature, or reasoning setting is about to change.
- A provider is retiring a model version and you must move to a new one.

## When not to use

- There is no eval dataset yet: build one with `eval-builder` first (30+ cases), then come back.
- The goal is lowering spend: start with `llm-cost-auditor`, then use this skill to validate each change it proposes.
- Retrieval changes in a RAG system (chunking, embeddings, top-k): measure retrieval with `rag-debugger`'s metrics, then use this skill for the end-to-end answers.

## Inputs

| Input | Default if not given |
|---|---|
| Baseline config (prompt text, model id, params) | The version on the main branch / in production |
| Candidate config | The working-tree change |
| Dataset | `evals/cases.jsonl` in `eval-builder` format; otherwise ask |
| Samples per case | 3 (5 if temperature > 0.5, or for agents) |
| Allowed regressions | 0 on Must-criteria cases |

## Workflow

### 1. Freeze everything except the change

- Put both configs side by side in a table: prompt hash, model id **with dated version** (not a moving alias like `-latest`), temperature, top_p, max output tokens, tool definitions, retrieval settings. Exactly one row should differ (or one deliberate bundle, named as such).
- Freeze the inputs: for RAG, snapshot the retrieved context into the case (`"input": {"question": ..., "context": [...]}`) so index drift doesn't masquerade as a prompt effect. For agents, stub or record tool responses.
- Seeds: set one where the API offers a best-effort `seed` parameter; it reduces variance but never guarantees identical outputs, and some providers have none. Sampling multiple times is what makes the comparison valid.

**Done when** the config table shows a single intended difference and the dataset file's hash is recorded.

### 2. Run both variants on the same dataset

Use the harness from `eval-builder` (`evals/run_evals.py`), one wrapper per variant or one wrapper reading a variant env var:

```bash
VARIANT=baseline  python3 evals/run_evals.py --cases evals/cases.jsonl --cmd "python3 evals/run_app.py" --samples 3 --out evals/results/baseline.jsonl
VARIANT=candidate python3 evals/run_evals.py --cases evals/cases.jsonl --cmd "python3 evals/run_app.py" --samples 3 --out evals/results/candidate.jsonl
```

Run them close together in time (same day) so provider-side changes affect both. Make the wrapper emit `usage` so token deltas are measured, not estimated.
**Done when** both result files contain cases × samples rows and neither run has calls failing for infrastructure reasons (timeouts, rate limits — rerun those).

### 3. Diff per case and categorise

Copy [scripts/compare_runs.py](scripts/compare_runs.py) to `evals/` and run:

```bash
python3 evals/compare_runs.py --old evals/results/baseline.jsonl --new evals/results/candidate.jsonl --max-regressions 0
python3 evals/compare_runs.py --old ... --new ... --tag must    # gate only on Must-tagged cases
```

It labels every case:

| Category | Meaning | Action |
|---|---|---|
| `format_break` | Candidate fails a JSON/schema check that baseline passed | Blocker. Downstream parsers will crash |
| `regressed` | Baseline majority-pass, candidate majority-fail | Read every one |
| `improved` | Reverse | Spot-check 5 to confirm the grader isn't fooled |
| `unstable` | Mixed samples in either run | Raise samples to 5-10 for these cases before concluding |
| `neutral` | Same outcome, all samples agree | No action |

Then read the actual outputs side by side for every `regressed`, `format_break` and a sample of `neutral` cases (graders miss tone and subtle wrongness). Pull them from the two `--out` files by case id.
**Done when** every regressed case has a one-line explanation (real regression / grader too strict / acceptable trade-off).

### 4. Pairwise judge for criteria assertions can't capture

For "which answer is better" questions (helpfulness, tone), run a pairwise LLM judge (prompt rules in `eval-builder`'s `references/judge-prompt.md`):

1. Write a small script that joins the two `--out` files by case id and asks the judge to compare A and B on one stated criterion, allowing "tie".
2. Run each pair **twice with positions swapped**. Count a win only when both orders pick the same variant; otherwise it is a tie. Report the inconsistency rate; above ~20% the judge or criterion is too vague.
3. Significance: sign test on wins vs losses (ties dropped) — the same exact binomial `compare_runs.py` uses. With 40 decisive pairs you need roughly 27-13 or better for p < 0.05.

**Done when** win/tie/loss counts and the swap-inconsistency rate are recorded, or the step is explicitly skipped as not needed.

### 5. Statistics on small samples

- Paired data: use McNemar (printed by the script) on per-case majority pass/fail, not two independent pass rates. It counts every pass→fail flip, including `format_break` cases.
- Under 10 discordant cases the test can't detect anything; decide on the case list, not the p-value.
- Never claim "improved by 4 points" on 50 cases; say "no detectable difference" unless p < 0.05 or the regressed list is empty and improvements are clearly real.
- A Must-criterion regression on a single case can block shipping regardless of statistics.

### 6. Cost and latency deltas

From the script output: p50/p95 latency and mean input/output tokens per call. Convert tokens to money with the provider's **current** published price per model (look it up; prices change) × monthly call volume. Note reasoning/thinking tokens are billed as output on providers that report them. Flag p95 latency increases > 20% for user-facing paths.

### 7. Verdict

Write the report below. Verdicts:
- **SHIP**: no format breaks, no unexplained Must regressions, quality neutral or better, cost/latency within budget.
- **SHIP WITH FOLLOW-UP**: minor Should regressions accepted by the owner, each tracked.
- **NO-SHIP**: any format break, any unexplained Must regression, or a significant quality drop.
- **INCONCLUSIVE**: too many `unstable` cases or too few discordant cases; name the extra cases/samples needed.

## Output

```markdown
## Prompt regression: <change summary>, <date>
Verdict: **NO-SHIP**: 2 Must regressions (refund amounts), 1 format break.

| | Baseline | Candidate |
|---|---|---|
| Config | prompt v12, model-x-2026-03-01, temp 0.2 | prompt v13 (same model/params) |
| pass^3 (Must) | 52/60 | 50/60 |
| Mean pass rate | 91% | 90% |
| Latency p50 / p95 | 1.8s / 4.1s | 1.6s / 3.9s |
| Tokens in / out (mean) | 2,310 / 180 | 1,720 / 175 |
| Est. cost / month | $X (price looked up <date>) | $Y |

Categories: improved 4, regressed 3, format_break 1, unstable 2, neutral 50. McNemar p = 1.00.
Pairwise judge (helpfulness): 18 W / 30 T / 12 L, swap inconsistency 14%.

### Regressions (each read by hand)
| Case | Baseline output (excerpt) | Candidate output (excerpt) | Verdict |

### Follow-ups
```

## Guardrails

- Never change the dataset or graders in the same run as the candidate; that makes the comparison meaningless. Change them in a separate, earlier commit and re-run the baseline.
- Never declare SHIP from the aggregate alone; every regressed and format_break case must be read.
- Don't push, merge or deploy the candidate yourself; deliver the verdict and let the owner decide.
- Ask before runs that exceed ~1,000 paid calls (cases × samples × 2 variants × judge calls).

## Common mistakes

| Mistake | Fix |
|---|---|
| Comparing a run from last month against today's run | Rerun baseline now on the same dataset |
| Using `-latest` model aliases | Pin dated model versions in both configs |
| One sample per case at temperature > 0 | ≥ 3 samples; investigate `unstable` cases with more |
| Pairwise judge in one order only | Swap positions; count only consistent wins |
| "Mean went from 88% to 90%, ship it" | Look at regressed cases and McNemar; 2 points on 60 cases is noise |
| Ignoring output tokens | Longer outputs cost more and break length-limited UIs; compare means |
| Changing prompt and model together | One variable per comparison, or label the bundle explicitly |

## Example

Moving a classification prompt from one model version to its successor. Same prompt, temperature 0, 3 samples, 80 cases. Script: improved 2, regressed 5, unstable 3, neutral 70, McNemar p = 0.45. Reading the 5 regressions shows the new model outputs `"Billing"` instead of `"billing"`: a real format break the `equals` grader caught but labelled `regressed`. Fix: add "label must be lowercase" plus a normaliser in the parser, rerun: regressed 0, mean tokens out −12%. Verdict: SHIP.
