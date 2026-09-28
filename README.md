# TicketRoute

**PE6201 Individual Final Project — Tu Weikang, Section C.**

TicketRoute suggests one of 77 English banking-support intents or human review.
It is independent of the insurance-claims AR/A2 assignment. See
[PROJECT_BOUNDARY.md](PROJECT_BOUNDARY.md).

## Current evidence

**Full evaluation completed locally on 28 September 2026 and independently
audited without new API calls.** All 1,998 validation rows and 3,080 official
test rows are present. Official-test macro-F1 is **0.8489** and accuracy is
**85.23%** (2,625/3,080), exceeding the proposal's macro-F1 target of 0.80.
The validation-selected threshold is **0.60**. It accepts 3,049 test predictions
at 85.70% accuracy and defers 31. There are still 436 accepted errors.
The stricter 3,073-query subset gives macro-F1 0.8490. All 4,976 new API calls
have reported charges totalling **US$2.381836**, including the initial probe.
The original pilot cost remains unknown.

Read [the final trade-off report](submission/TicketRoute_Tradeoff_Report.md),
[independent audit](analysis/FINAL_RESULTS_REVIEW_2026-09-28.md), and
[demo guide](DEMO_GUIDE.md). The final report has 1,024 words including headings,
table and sources. The recorded demo has been assembled from the student's
two original screen recordings and original narration, with English subtitles.
Final student playback, instructor access and portal submission remain. Completed evidence is bundled under `results/`; no API key is
needed to inspect it or open the replay demo.

### Historical pilot

The preserved 23 August pilot contains 100 validation queries: accuracy **87%**,
historical observed-label macro-F1 **0.8611**, and 48 true intents represented.
At threshold 0.70, 97 are accepted, 3 deferred, and 11 accepted predictions are
wrong. This is a pilot, **not the 3,080-query official LLM test**. Actual historical
API charges are unknown because the original client did not record usage.

Preparation on 27 September restored all 100 cached predictions, passed 27
offline tests and recomputed the baselines. The full paid evaluation then ran
on the student's Mac. The working UI supports honest historical
replay, a keyword mode and a separately labelled live mode.

## One starting point

**For this completed project, choose 3 to open the demo.** Keep the same local
folder. Do not replace it with an older download or restart the paid stages.
The first-run sequence below describes how the completed evidence was produced.

Download the complete package once and read [START_HERE_CN.md](START_HERE_CN.md).
The ZIP extracts to `TicketRoute_Start_Here`. Its only Mac launcher is
`START_HERE_MAC.command`, with these menu choices:

| Choice | Action | Local evaluation stop |
| --- | --- | --- |
| 1 — first run | Offline checks, small validation cost probe, result ZIP | US$0.10 cumulative |
| 2 — after reviewing probe evidence | Resume validation, freeze threshold, complete official test, export | US$7 cumulative, including probe charges |
| 3 — demo | Open the local browser interface in recorded replay mode | No API charge in replay/keyword modes |

Return `TicketRoute_Results.zip` after choices 1 and 2. Use the same folder
throughout; do not download a second launcher, overwrite results or reset its
ledger. The US$0.05 request reserve normally stops the first probe near US$0.05
recorded spend. A spending-cap stop is expected for choice 1. Review other errors
before resuming. These are software guards, not provider/account guarantees.
Completing all remaining 4,976 new calls within the reported US$8 balance is not
guaranteed. The frozen model, prompt, data splits and metrics are unchanged.

Python **3.10 or newer** is the only runtime requirement. No pip packages, model
weights, database or web framework are needed. Bundled public data works offline.
For Mac Terminal: type `caffeinate -i bash`, add a space, drag the launcher into
the window, press Return, then choose 1. Keep the lid open and power connected.
The repository retains old launcher names only as compatibility wrappers around
the same primary entry; the complete ZIP omits them to keep one visible entry.

## Command-line reproduction

From the project directory with Python available:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_project.py --offline
```

Start with the small cost probe:

```bash
python3 scripts/run_project.py --prompt-for-key --stage validation --budget-usd 0.10
```

After reviewing the probe, resume in the **same folder**:

```bash
python3 scripts/run_project.py --prompt-for-key --budget-usd 7.00
```

Enter the OpenRouter key only in the hidden local prompt. Never include it in
source files, screenshots, chat, commits or the report. An existing
`OPENROUTER_API_KEY` environment variable is also supported. The key is not
persisted by the application. Recorded evaluation charges accumulate across
restarts; historical pilot charges are unknown and not included. The runner's
default evaluation stop is also US$7, while menu choice 1 explicitly uses US$0.10.
Unknown charges stop the run. There are no automatic service retries. Preserve
the generated ZIP if a provider/schema error stops the initial compatibility check.

Open the demo with menu choice 3 or `python3 app.py --open-browser`. Replay and
keyword modes do not call the API. Live UI calls use a **separate** US$1 local
stop and ledger; those additional charges still reduce the same provider balance.

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
| `submission/` | Final report, archived automatic draft, word counts and error analysis |
| `tests/` | Offline functional and regression tests with synthetic API fixtures |

`results/llm_openai_gpt-5-mini_validation_100.json` and the unversioned old cache
are the earlier v1 experiment. They must not be mistaken for v3 or final-test
results. The authoritative v3 pilot is under `evidence/pilot_2026-08-23/`.
`analysis/pilot_error_analysis.ipynb` is retained as historical development work.
Read `analysis/CURRENT_ERROR_ANALYSIS.md` for the full-test interpretation.

To independently recalculate the final metrics without a key, export a local
handback and audit it. These commands use saved evidence and make no API calls:

```text
python3 scripts/finalise_outputs.py
python3 analysis/review_final_results.py TicketRoute_Results.zip
```

The first command regenerates the automatic `DRAFT` files and result ZIP. The
reviewed final report `submission/TicketRoute_Tradeoff_Report.md` is separate.

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

CSV files retain their original line endings. `.gitattributes` disables automatic
CSV newline conversion so source and historical-evidence byte hashes also verify
after a fresh checkout on another machine.
