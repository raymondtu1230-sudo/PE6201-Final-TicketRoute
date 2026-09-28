# TicketRoute

Tu Weikang · PE6201 Individual Final Project

TicketRoute classifies English digital-banking support messages into 77 intents,
with a human-review option. It uses GPT-5 mini through OpenRouter and compares
the results with keyword and majority baselines. It does not answer customers,
access accounts or carry out financial actions.

## Run the application

Python 3.10 or newer is required. No additional Python packages are needed.
From the project folder, run:

```bash
python3 app.py --open-browser
```

The application opens at http://127.0.0.1:8765. On Mac, the alternative is to
open `START_HERE_MAC.command` and choose **3**. Stop the server with Control+C.

Recorded replay and keyword modes work offline without an API key. Live mode
requires an OpenRouter key and makes a paid call. Replay examples come from the
August pilot and retain its 0.70 review threshold. The completed evaluation uses
a threshold of 0.60, selected on validation before the official test.

## Results

Evaluation completed on 28 September 2026: 1,998 validation queries followed by
3,080 official test queries. The model and prompt were fixed before completing
validation, and test outcomes were not used to tune the prompt or threshold.

| Method | Test macro-F1 | Test accuracy |
| --- | --- | --- |
| Majority rule | 0.0003 | 1.30% |
| Keyword overlap | 0.3786 | 38.08% |
| GPT-5 mini | 0.8489 | 85.23% |

The model correctly classifies 2,625 test queries. The review rule defers 31
predictions, of which 19 would be wrong. Another 436 errors remain among the
3,049 accepted predictions. Accepted accuracy is 85.70%, so the model-reported
confidence score is a limited safeguard.

The ledger records 4,976 new API calls costing US$2.381836, including the initial
cost probe. The historical pilot cost was not recorded. About 98% of input
tokens were cached; isolated requests may cost more. Median test latency was
2.19 seconds. All results and charges are retained in `results/`.

## Design choices and limitations

I built the interface, prompt, review policy, caching and evaluation in Python
and used a hosted model to avoid training and serving one locally. Python gives
direct control over data splits, schema checks and resumable runs. These needs
were the reason for choosing it over low-code. A fixed-label classifier does
not need an agent or retrieval system. My proposal estimated one day for the
first working slice and under five minutes for local launch with Python already
installed; these were planning estimates.

BANKING77 provides 10,003 training and 3,080 test queries. The deterministic
split uses seed 42 and selects two training-core examples per intent for the
prompt. No selected example occurs in validation or test. Six source texts
overlap training and test, and one test text is repeated. Excluding these gives
a 3,073-query subset with macro-F1 0.8490. The original data is retained.

The system validates labels and structured outputs, limits input length,
treats customer text as data, and escapes text displayed in the browser. These
provide partial controls for the OWASP Top 10 for LLM Applications (2025),
particularly LLM01 prompt injection and LLM05 improper output handling.
Adversarial robustness has not been measured. PII masking, production access
controls, drift monitoring and routine audits of accepted routes remain future
work. A supervised trial would be needed to measure staff time and performance
on current local tickets.

## Reproduce the checks

Run the offline tests:

```bash
python3 -m unittest discover -s tests -v
```

Export the saved results and recompute the evaluation audit:

```bash
python3 scripts/finalise_outputs.py
python3 analysis/review_final_results.py TicketRoute_Results.zip
```

These commands use the bundled data and predictions without model calls.
Synthetic responses are used only in software tests, not in reported benchmark
scores. The exporter writes per-intent and error tables plus an evidence ZIP.

For an explicit paid evaluation or resumption:

```bash
python3 scripts/run_project.py --prompt-for-key --stage validation --budget-usd 0.10
python3 scripts/run_project.py --prompt-for-key --budget-usd 7.00
```

The first command is a small cost probe; the second continues the full sequence.
Existing predictions and charges are reused. A hidden prompt accepts the key;
the application does not save it. Unknown billing or service failures stop the
run. The cumulative US$7 stop and US$0.05 reserve are local software controls.
Live calls from the browser have a separate US$1 local stop and ledger.

## Project files

| Location | Contents |
| --- | --- |
| `app.py`, `ticketroute/` | Interface, classification, review and evaluation logic |
| `scripts/` | Data preparation, evaluation and result export |
| `data/`, `DATA_LICENSE.md` | Pinned BANKING77 data and licence |
| `evidence/pilot_2026-08-23/` | Original 100-query pilot |
| `results/` | Predictions, cached responses, charges and frozen configuration |
| `analysis/` | Error analysis and reproducible result checks |
| `submission/` | Report text, per-intent scores and error tables |
| `tests/` | Offline software tests |

The submission package includes the report in Word and PDF under `01_Report/`,
the recorded demo and English captions under `02_Demo/`, and the original
problem statement under `03_Problem_Statement/`. The report contains 1,024 words
including headings, table and sources. The demo is approximately 3 minutes
21 seconds. AI use is described in [AI_ASSISTANCE.md](AI_ASSISTANCE.md).

The older files `results/llm_openai_gpt-5-mini_validation_100.json` and
`results/cache_openai_gpt-5-mini_validation.jsonl` belong to the earlier v1
experiment. The v3 pilot used here is under `evidence/pilot_2026-08-23/`.

## Sources and licences

- [PolyAI BANKING77 source](https://github.com/PolyAI-LDN/task-specific-datasets/tree/57ec275d8078af65b7731c2a98be812d844a6d6b/banking_data)
- [BANKING77 dataset card](https://huggingface.co/datasets/PolyAI/banking77)
- [OpenRouter GPT-5 mini](https://openrouter.ai/openai/gpt-5-mini)
- [OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting)
- [Zendesk Intelligent Triage](https://support.zendesk.com/hc/en-us/articles/4964463770650-About-intelligent-triage)
- [OWASP LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP LLM05 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/)

BANKING77 is CC BY 4.0. The code licence is in `LICENSE`. CSV line endings are
preserved so the source and historical-evidence hashes remain reproducible.
