# Evaluation guide

This directory contains the saved evidence for the completed TicketRoute
evaluation. The reported scores come from recorded model responses. The
synthetic responses used in `tests/` check software behaviour and are not part
of these benchmark results.

## Evaluation sequence

1. Preserve the 23 August 2026 pilot: 100 validation rows with the original
   0.70 review rule. Its original billing was not recorded.
2. Fix `openai/gpt-5-mini`, prompt `contrastive_taxonomy_v3`, the data hashes,
   prompt examples and metric/threshold policy in `evaluation_lock.json`.
3. Complete all 1,998 validation rows, reusing the pilot. Five early new
   predictions check provider, output and billing compatibility; they remain
   in validation even if incorrect.
4. Select the lowest threshold in 0.50, 0.55, ..., 0.95 attaining at least 85%
   accuracy among accepted validation predictions. This selects 0.60. If no
   candidate qualifies, the code requires human review for every query.
5. Save `calibrated_threshold.json` and `test_lock.json`, then evaluate all
   3,080 official test rows with the same prompt and frozen rule. The run
   completed on 28 September 2026, Singapore time. Test errors were not used
   to change the prompt or threshold. Keyword-only test results were already
   available during development.

Calls are sequential and resumable. Each split's cache is keyed by query text;
duplicate rows still contribute to the row-level score but reuse a prediction.
There are 5,078 evaluation rows, 100 reused pilot responses and two within-split
duplicate reuses, giving 4,976 new calls. All new calls have recorded charges.

## Metrics and interpretation

| Metric | Definition | Official test result |
| --- | --- | --- |
| Accuracy | Correct best-intent predictions divided by all rows, including rows later deferred. | 2,625 / 3,080 = 85.23% |
| Macro-F1 | Mean of per-intent F1 over the fixed 77 labels; a zero denominator contributes zero. | 0.8489; target at least 0.80 |
| Coverage | Accepted predictions divided by all rows. | 3,049 / 3,080 = 98.99% |
| Review rate | Deferred predictions divided by all rows. | 31 / 3,080 = 1.01% |
| Accepted accuracy | Correct predictions among those with confidence at least 0.60. | 2,613 / 3,049 = 85.70% |
| Deferred would-be error rate | Incorrect best intents among deferred rows, before any human correction. | 19 / 31 = 61.29% |

The JSON field `answered_accuracy` means accepted-route accuracy, not the
quality of a customer answer: TicketRoute only classifies. Invalid model
outputs are recorded as `__MODEL_FAILURE__`, count as errors and are deferred.
There were zero such failures in this completed evaluation.

Self-reported confidence is not calibrated. The rule catches only 19 of the
455 test errors; 436 wrong predictions still pass. The 85% validation selection
target is a project operating rule, not a production safety guarantee.

The keyword baseline scores macro-F1 0.3786 and accuracy 38.08%; the majority
baseline scores 0.0003 and 1.30%. Their frequencies and tie-breaks use only the
8,004-row training core. The stricter test sensitivity set has 3,073 rows,
macro-F1 0.8490 and accuracy 85.23%; exclusions are explained in the
[data guide](../data/README.md).

## Evidence map

Paths below are relative to the repository root.

| File or group | What it establishes |
| --- | --- |
| `results/test_full_report.json`, `results/validation_full_report.json` | Aggregate scores, review statistics, confusions and latency. |
| `results/test_full_predictions.csv`, `results/validation_full_predictions.csv` | Every evaluated row, reference label and prediction, including errors. |
| `results/cache_openai_gpt-5-mini_test_contrastive_taxonomy_v3.jsonl`, `results/cache_openai_gpt-5-mini_validation_contrastive_taxonomy_v3.jsonl` | Saved unique responses used for resumption; model, prompt and metadata accompany each prediction. |
| `results/evaluation_lock.json` | Frozen configuration, full prompt template, data hashes and selection policy. |
| `results/calibrated_threshold.json`, `results/test_lock.json` | Validation threshold sweep and the rule/configuration fixed for testing. |
| `results/baselines_core.json`, `results/baseline_*_predictions.csv` | Training-core keyword and majority comparisons for pilot, validation and test. |
| `results/data_audit.json`, `results/test_sensitivity_report.json` | Split counts, overlaps and the additional duplicate/overlap sensitivity analysis. |
| `results/api_attempts.jsonl`, `results/evaluation_budget.json` | New-call billing and the local evaluation spending control. |
| `evidence/pilot_2026-08-23/`, `results/pilot_provenance.json`, `results/pilot_comparison.json` | Unchanged pilot evidence, hashes and explanation of its different macro-F1 label policy. |
| `submission/test_per_intent.csv`, `submission/validation_per_intent.csv` | Per-intent support, precision, recall and F1. |
| `submission/test_errors.csv`, `submission/validation_errors.csv` | Misclassified rows for inspection. |
| `analysis/CURRENT_ERROR_ANALYSIS.md`, `analysis/review_final_results.py` | Interpretation of errors and an independent audit of the saved evidence. |

The older `llm_openai_gpt-5-mini_validation_100*` and
`cache_openai_gpt-5-mini_validation.jsonl` files belong to the earlier v1
experiment. The older `keyword_baseline*` files are also historical outputs.
Use the full reports, `baselines_core.json` and the v3 evidence above for the
final comparison. The pilot's original macro-F1 used observed labels, whereas
the final metric always averages across all 77 labels.

## Prediction and billing fields

The full prediction CSV files contain `text`, `truth`, `prediction`,
`confidence`, `reason`, `model`, `latency_ms`, `prompt_version`, `status`,
`usage`, `generation_id`, `returned_model`, `provider`, `finish_reason` and
`request_hash`. `truth` is the source `category`; `prediction` is the best
intent before applying the review rule. `usage` is JSON inside the CSV field.
The JSONL caches retain these values as JSON types, one record per line.

The attempt ledger records query hashes, outcomes, usage, generation IDs and
request hashes for new calls. Sum its `usage.cost_usd` values to obtain
US$2.381836; do not add costs from both CSVs and caches, which describe the same
calls. The test report's `new_call_ledger` is cumulative across the new
validation and test calls, not a test-only cost. Historical pilot charges are
unknown, so US$2.381836 is not total lifetime project expenditure.

About 98% of new input tokens were served from the provider's prompt cache;
isolated requests may cost more. Median test latency was 2.19 seconds and the
95th percentile was 3.696 seconds. These are observations from this run.

## Reproduce without paid calls

From the repository root, with the bundled data and evidence present:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/finalise_outputs.py
python3 analysis/review_final_results.py TicketRoute_Results.zip
```

The tests check routing, metrics, data separation, billing stops and resumable
execution. The exporter regenerates per-intent/error tables under `submission/`
and creates `TicketRoute_Results.zip` with an integrity manifest. It does not
rewrite the trade-off report. That ZIP is an evidence export, not the complete
submission package containing the report, demo and problem statement.

The independent audit checks the archive, original pilot, row order, truth
labels, cache/CSV agreement, baseline and model scores, threshold selection,
configuration locks, billing reconciliation and reconstructed request hashes.
It reads the saved results and makes no network or model calls.

Paid evaluation commands are documented separately in the
[main README](../README.md#reproduce-the-checks). Existing records are reused.
The runner stops on service errors or unknown billing and uses a cumulative
US$7 local stop with a US$0.05 reserve. This is a software control rather than
a provider account cap. Browser live calls use a separate US$1 local stop and
`demo_attempts.jsonl`; they do not change the completed benchmark evidence.
