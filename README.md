# TicketRoute

**PE6201 Individual Final Project — Tu Weikang, Section C.**

TicketRoute suggests one of 77 English banking-support intents or human review.
It is independent of the insurance-claims AR/A2 assignment. See
[PROJECT_BOUNDARY.md](PROJECT_BOUNDARY.md).

## Current evidence

The preserved 23 August pilot contains 100 validation queries: accuracy **87%**,
historical observed-label macro-F1 **0.8611**, and 48 true intents represented.
At threshold 0.70, 97 are accepted, 3 deferred, and 11 accepted predictions are
wrong. This is a pilot, **not the 3,080-query official LLM test**. Actual historical
API charges are unknown because the original client did not record usage.

Preparation on 27 September restored all 100 cached predictions, passed 27
offline tests and recomputed the baselines. Full validation and final LLM test
require the course OpenRouter key. The working UI supports honest historical
replay, a keyword mode and a separately labelled live mode.

## Quick start

Python **3.10 or newer** is the only runtime requirement. No pip packages, model
weights, database or web framework are needed. Bundled public data works offline.

On a Mac, read [START_HERE_CN.md](START_HERE_CN.md):

- `START_HERE_MAC.command`: checks, full validation, threshold freeze, final test,
  report draft and `TicketRoute_Results.zip` in one workflow.
- `OPEN_DEMO_MAC.command`: opens the local interface, initially without paid calls.
- `CHECK_OFFLINE_MAC.command`: verifies the existing evidence without an API key.

From a terminal on macOS, Linux or Windows with Python available:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_project.py --offline
python3 app.py --open-browser
```

For the full evaluation, in a separate terminal:

```bash
python3 scripts/run_project.py --prompt-for-key
```

Enter the API key only into the hidden local prompt. Do not put it in source
files, screenshots, chat, commits or the report. An existing
`OPENROUTER_API_KEY` environment variable is also supported. To resume ordinary
completed/partial work, run the same command in the **same folder**.

A local US$12 new-evaluation spending stop excludes historical pilot charges.
It checks recorded charges plus a US$0.05 reserve before the next call. This is
not a provider-side account cap, and missing charges stop the run for inspection.
There are no automatic service retries. A provider error, unknown charge or
schema failure during the initial five new calls can stop the workflow; preserve
and return the generated results ZIP. Live UI calls have a separate US$1 local
stop and separate ledger. The key is never persisted by this program.

## Evaluation design

- Source: official BANKING77, 10,003 train rows and 3,080 test rows, 77 intents.
- Stratified validation: seed 42, 1,998 rows. Train core: 8,004 rows after removing
  one text-overlapping row. Prompt: two core examples for each intent.
- No prompt examples occur in validation or test. The original source still
  contains six train/test shared texts, one of them in validation; validation
  has 1,997 unique texts, test 3,079. Duplicates have consistent labels.
- Preserve all official test rows as the primary benchmark. Report a secondary
  sensitivity score on unique test texts absent from the entire original train
  file. Neither source CSV is silently changed.
- Fixed prompt `contrastive_taxonomy_v3`, `openai/gpt-5-mini`, low reasoning,
  1,200 maximum completion tokens, strict JSON schema and fixed-label validation.
- Main metric: macro-F1 over all 77 intents, zero F1 for a zero denominator;
  target ≥0.80. Historical pilot used observed-label macro and remains labelled
  accordingly. Full scoring includes invalid-output failures as wrong.
- Threshold: lowest of 0.50, 0.55, …, 0.95 meeting validation answered accuracy
  ≥85%; if none qualifies, all cases require review. This is the project's chosen
  operating rule, not a teacher-specified target or a guarantee on new data.
- The official LLM test starts only after full validation and a frozen threshold.
  No prompt or threshold tuning uses test outcomes. The keyword-only test score
  was already measured during development.
- Caches are versioned and validated. A duplicate source text reuses one result
  within its split but remains counted as a benchmark row. Starting from the
  preserved pilot requires at most 4,976 new unique inference calls.

The full pipeline writes `evaluation_lock.json`, `calibrated_threshold.json`,
`test_lock.json`, row-level CSVs, caches, `api_attempts.jsonl`, full reports,
per-intent scores, error CSVs, a duplicate-sensitive test report and a report
draft. Model IDs, usage, cost and request hashes are retained for new calls.
The returned model alias may not identify an immutable historical backend.

Keyword baseline on all 3,080 test rows: accuracy **0.380844**, macro-F1
**0.378621**. Majority baseline: accuracy **0.012987**, macro-F1 **0.000333**.
Both use training-core label frequencies. The baselines and LLM must be compared
on the same split and with the same metric definition.

## Files and reproducibility

| Path | Purpose |
| --- | --- |
| `app.py` | Local browser interface, port 8765, loopback by default |
| `ticketroute/` | Rules, fixed prompt, client, metrics, calibration and audit |
| `scripts/run_project.py` | Sequential frozen evaluation and export |
| `scripts/restore_pilot.py` | Hash-check and recover all 100 historical rows |
| `scripts/finalise_outputs.py` | Evidence-based report draft and handback ZIP |
| `data/` | Original CSVs with SHA-256 verification |
| `evidence/pilot_2026-08-23/` | Untouched completed pilot CSV and JSON |
| `results/` | Earlier iteration evidence and newly generated evaluation |
| `submission/` | Draft report, word count and generated error analysis |
| `tests/` | Offline functional and regression tests with synthetic API fixtures |

`results/llm_openai_gpt-5-mini_validation_100.json` and the unversioned old cache
are the earlier v1 experiment. They must not be mistaken for v3 or final-test
results. The authoritative v3 pilot is under `evidence/pilot_2026-08-23/`.
`analysis/pilot_error_analysis.ipynb` is retained as historical development work.
Read `analysis/CURRENT_ERROR_ANALYSIS.md` for the current pilot interpretation.

The independent repository is [https://github.com/raymondtu1230-sudo/PE6201-Final-TicketRoute](https://github.com/raymondtu1230-sudo/PE6201-Final-TicketRoute). It was created as a private
repository on 27 September 2026. Confirm instructor access before submission.
Teacher PDFs and credentials are excluded from this source repository.

## Scope and limits

This is a student prototype, not a banking service. It offers no advice, account
access, financial decisions, claims processing or automatic customer action.
Confidence is self-reported and does not eliminate confident errors. Human review
is a suggestion in this local interface, not a staffed production queue. PII
masking, production access controls, drift monitoring and random audit scheduling
are future requirements, not completed features. See `AI_ASSISTANCE.md`.

## Sources and licences

- [PolyAI official BANKING77 source](https://github.com/PolyAI-LDN/task-specific-datasets/tree/57ec275d8078af65b7731c2a98be812d844a6d6b/banking_data)
- [PolyAI dataset card](https://huggingface.co/datasets/PolyAI/banking77)
- [OpenRouter GPT-5 mini](https://openrouter.ai/openai/gpt-5-mini)
- [OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting)
- [Zendesk Intelligent Triage overview](https://support.zendesk.com/hc/en-us/articles/4964463770650-About-intelligent-triage)

Data is CC BY 4.0; see `DATA_LICENSE.md`. Code licence is in `LICENSE`. OpenRouter
pricing and usage documentation were checked on 27 September 2026. Current usage
is returned automatically; no deprecated `usage.include` parameter is added.
