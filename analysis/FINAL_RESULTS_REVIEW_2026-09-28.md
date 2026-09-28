# TicketRoute completed evaluation review

The received `TicketRoute_Results(1).zip` is the completed evaluation, not the earlier cost probe. Its SHA-256 is `d773ba5588250175f547932105415bacdb9a8973e75bfd177e64c64444151598`. The run completed at 01:33:02 on 28 September 2026 in Singapore.

All 37 manifest entries and the ZIP CRC passed. The original 100-query pilot files are unchanged. The earlier 94-call cost probe and its cache remain exact prefixes of the completed ledger and validation cache. Both source CSV hashes and the frozen configuration match the original experiment. All 4,976 new request hashes were reconstructed from the fixed prompt and parameters.

The independent audit checked each CSV against its cache and the original split order, recalculated the 77-label macro-F1 and accuracy, reproduced validation-only selection of threshold 0.60, checked the test lock, and reconciled every new attempt with its generation ID, metadata and charge. It made no model calls.

| Measure | Validation | Official test | Strict test subset |
| --- | --- | --- | --- |
| Rows | 1,998 | 3,080 | 3,073 |
| Correct predictions | 1,688 | 2,625 | 2,619 |
| Accuracy | 84.48% | 85.23% | 85.23% |
| Macro-F1 over 77 labels | 0.8485 | 0.8489 | 0.8490 |
| Accepted predictions | 1,975 | 3,049 | 3,042 |
| Accepted accuracy | 85.06% | 85.70% | 85.70% |
| Human review | 23 | 31 | 31 |

The predefined primary target of macro-F1 at least 0.80 is met. This is the project's performance target, not a guarantee of an assignment grade. Of 455 test errors, 19 are deferred and 436 remain accepted, so the review rule is insufficient for autonomous deployment. The strict subset removes repeated test texts and texts in the original training file.

The ledger contains 4,976 successful API responses, no recorded output failures, and no unknown new-call charges. Successful API responses do not mean correct classifications. Total recorded cost is US$2.381836, including the probe. Historical pilot cost is unknown. The provider is OpenAI and the returned model identifier is `openai/gpt-5-mini` for every new call. The alias does not guarantee an immutable backend.

Reproduce this audit from the original handback with:

```text
python3 analysis/review_final_results.py /path/to/TicketRoute_Results.zip
```

The source and evidence belong only to the PE6201 individual Final Project. Personal video recording, instructor repository/video access and the final school-portal submission still require completion. The separate full rubric and personal feedback were not available for review.
