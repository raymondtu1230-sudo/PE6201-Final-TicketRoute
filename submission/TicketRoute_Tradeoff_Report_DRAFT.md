# TicketRoute

Tu Weikang · PE6201 individual Final Project · Section C

PRE-FINAL DRAFT — 100-query pilot only; full validation and official test are still pending

## Problem and intended value

Mei, an English-language digital-bank support supervisor, must assign incoming messages to specialist queues. I chose one bounded task: suggest one of 77 BANKING77 intent labels, or require human review. At an assumed 15 seconds per message, 1,000 messages require about 4.2 staff hours of manual triage. This is a planning assumption; I have not measured staff time savings. TicketRoute does not answer customers, access accounts or take financial actions.

## Business and technical choices

I own the browser interface, taxonomy, prompt, validation, review policy and evaluation pipeline, and rent GPT-5 mini through OpenRouter. This avoids training and hosting within the project period, while introducing network latency, recurring cost and provider dependence. A supervised intent model is a credible later alternative because labelled data exists; I have not tested one and cannot claim the rented model is superior. A keyword rule is the implemented non-AI comparator.

Zendesk Intelligent Triage is the commercial alternative identified in my proposal. TicketRoute is a narrow, student-controlled benchmark and review prototype; it does not replace an enterprise support platform. I chose Python's standard library over low-code to make data splits, schema checks and resumable evaluation inspectable. No agent or RAG is needed for a single fixed-label classification. The interface can replay verified historical examples without a key, with a visible replay label.

## Data and evaluation design

BANKING77 supplies 10,003 training and 3,080 official test queries across 77 English banking intents under CC BY 4.0. Source CSV hashes are checked. A fixed, stratified seed-42 split yields 1,998 validation rows; after removing an overlapping training-core row, 8,004 core rows remain. Two examples per intent come only from this core, with no prompt-example overlap with validation or test. The source itself contains six texts shared between train and test, including one in validation, plus within-split duplicates. I preserve the official benchmark and add a sensitivity score on unique test texts absent from all original training data. Both baselines use training-core frequencies.

The model and contrastive-taxonomy-v3 prompt are frozen before completing validation. I predeclare all-77-label macro-F1 of at least 0.80 as the primary target. Validation selects the lowest threshold from 0.50 to 0.95 in 0.05 increments attaining at least 85% accuracy on accepted predictions; if none qualifies, every query requires review. That 85% rule is my project choice, not an instructor requirement or safety guarantee. The official test uses the frozen prompt and validation threshold once, with cached resumption of interrupted work. It is not used to tune the model. The earlier keyword-only test result was already available during development.

## Evidence and limitations

The preserved 100-query validation pilot has 87 correct predictions, or 87.0% accuracy. Its historical macro-F1 is 0.8611 over the union of observed truth and prediction labels; only 48 of 77 true intents appear. That number cannot establish the all-77-label target. At the provisional 0.70 threshold, 97 queries are routed, three are deferred, and answered accuracy is 88.7%. Two of the three deferred predictions would have been wrong, but 11 wrong routes remain among the 97 accepted cases. This is direct evidence that self-reported confidence misses silent failures. The full 1,998-query validation run and 3,080-query official-test LLM run are not yet complete.

Comparable official-test scores below use the same fixed 77-label definition. The pilot keyword accuracy is 36.0%; its historical LLM score must not be compared directly with the full-test keyword score.

| Official test method | Macro-F1 / accuracy |
| --- | --- |
| Majority rule | 0.0003 / 1.3% |
| Keyword overlap | 0.3786 / 38.1% |
| GPT-5 mini | pending / pending |

The original 100-row evidence remains unchanged, and the pipeline recovers missing cached rows without buying those predictions again. Row-level outputs, failure counts, confusion pairs, per-intent results and latency summaries make later conclusions inspectable. The model alias may change behind the provider; new responses record the returned model identifier, so exact historical backend equivalence cannot be guaranteed.

## Cost and reliability

No new paid calls have been made in this preparation run. The original pilot client did not log token usage, generation IDs or charges, so its actual cost is unknown. The proposal estimated about US$7.75 for validation and test; that was a planning estimate, not measured expenditure. New calls retain provider usage and cost, returned model, request hash and generation ID. A local US$12.00 spending stop and a US$0.05 reserve per next call limit the run; this is not a provider-enforced account cap. Missing charges stop further paid calls rather than becoming zero. Transport failures stop the run, and completed predictions remain cached. Invalid model outputs count as failures rather than being silently retried until correct.

## Responsible use and conclusion

A confident wrong route is the main silent failure. Implemented controls include fixed labels, structured JSON, input length limits, a shared calibrated review policy and visible explanations. Untrusted query text is explicitly treated as data. A supervisor's random audit of accepted routes remains a proposed operational control, not an automated feature. Real deployment would also need PII masking, access control, drift checks and evaluation on current local tickets; these are not implemented.

Public English benchmark results cannot establish multilingual reliability, staff savings or production readiness. The appropriate next decision depends on the untouched-test evidence and manual-review workload, not on the pilot headline alone. I used AI assistance for implementation, checking and drafting; I remain responsible for reviewing and explaining the submitted work.

## Sources

1. PolyAI BANKING77; pinned source and licence in DATA_LICENSE.md.
2. OpenRouter GPT-5 mini model page and usage-accounting documentation, checked 27 September 2026; links in README.md.
3. Original 23 August 2026 pilot evidence; hashes in results/pilot_provenance.json.
