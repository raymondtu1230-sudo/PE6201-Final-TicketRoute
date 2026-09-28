# TicketRoute final error analysis

The fixed v3 prompt was evaluated on all 3,080 official test queries after validation selected threshold 0.60. There are 2,625 correct predictions and 455 classification errors. Every error is retained in `submission/test_errors.csv`; per-intent scores are in `submission/test_per_intent.csv`.

## Review policy

The rule accepts 3,049 predictions and defers 31. Of the deferred predictions, 19 would be wrong. However, 436 of the 455 total errors remain accepted. Coverage is 98.99% and accepted accuracy is 85.70%. The rule catches 4.18% of classification errors, so it should not be presented as a strong error detector or a production safety guarantee.

## Recurring boundaries

| True intent | Predicted intent | Test errors |
| --- | --- | --- |
| direct_debit_payment_not_recognised | card_payment_not_recognised | 17 |
| declined_transfer | declined_card_payment | 12 |
| pending_transfer | transfer_timing | 12 |
| beneficiary_not_allowed | failed_transfer | 12 |
| top_up_by_bank_transfer_charge | transfer_fee_charged | 11 |
| topping_up_by_card | receiving_money | 11 |
| compromised_card | card_payment_not_recognised | 11 |

The weakest intent F1 values are top_up_by_bank_transfer_charge (0.4231), topping_up_by_card (0.4516), beneficiary_not_allowed (0.4615), pending_transfer (0.5974), and declined_transfer (0.6301). Each official-test intent has 40 true examples. Aggregate performance therefore hides meaningful differences between queues.

These results suggest future investigation of channel, direction and transaction-state distinctions. They have not been used to modify the completed experiment. A new development set and fresh holdout would be needed for subsequent tuning.

## Source limitations

The official dataset contains six train/test shared texts and one repeated test text. The strict subset retains 3,073 unique test texts absent from the original training data. Its macro-F1 is 0.8490 versus the official 0.8489. No selected prompt example overlaps validation or test. Historical pilot scores cover only 48 true classes and should not be compared directly with full-test macro-F1.
