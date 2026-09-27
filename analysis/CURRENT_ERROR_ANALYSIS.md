# Current pilot error analysis

Authoritative source: `evidence/pilot_2026-08-23/` (100 real v3 validation rows).
The notebook beside this file is retained historical development evidence.

At the original 0.70 threshold, 87 of 100 predictions are correct. Three queries
are deferred; two would be wrong. Eleven errors remain in 97 accepted routes.
Therefore confidence is useful for some ambiguity, but it does not reliably
identify all wrong predictions.

Two repeated confusion pairs each occur twice: exchange_via_app →
fiat_currency_support; beneficiary_not_allowed → declined_transfer. Other errors
include ATM cash withdrawal versus card payment, direct-debit versus card-payment
recognition, and refund status versus requesting a refund. These are semantic
boundary errors, not fabricated labels.

Do not repair the prompt by inspecting final-test errors. Preserve v3 for the
planned frozen evaluation; use resulting errors to describe future improvements.
The full runner exports error rows and per-intent metrics after each completed
split, including model-output failures rather than dropping them.

The source dataset contains six train/test text overlaps and within-split
repetition. No selected prompt example overlaps validation or test. The pipeline
preserves official scores and adds an extra unique-text, no-training-overlap test
sensitivity score. The 100-row pilot covers 48 true classes and used an observed-
label macro definition; its 0.8611 cannot establish the final all-77-label target.
