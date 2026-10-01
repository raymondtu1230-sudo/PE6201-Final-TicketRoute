# Data guide

## Source and purpose

TicketRoute uses BANKING77 for English banking-support intent classification.
Each query has one author-provided label from a fixed set of 77 intents. This
evaluates routing into that taxonomy; it does not evaluate banking advice,
account actions or measured customer-service outcomes.

The original CSV files are bundled unchanged from the
[PolyAI source at commit 57ec275](https://github.com/PolyAI-LDN/task-specific-datasets/tree/57ec275d8078af65b7731c2a98be812d844a6d6b/banking_data).
The dataset is CC BY 4.0. Author attribution, the full source commit and licence
link are in [DATA_LICENSE.md](../DATA_LICENSE.md). No private bank tickets or
model-generated benchmark labels were added.

## Files and fields

| File | Rows | Purpose |
| --- | ---: | --- |
| `train.csv` | 10,003 | Source of the training core and validation split. |
| `test.csv` | 3,080 | Official held-out benchmark; all rows retained for the primary result. |

Both files are UTF-8 CSV with a header and two fields:

| Field | Meaning | Example |
| --- | --- | --- |
| `text` | Customer query supplied to the classifier. | `How do I locate my card?` |
| `category` | Author-provided reference intent used for scoring. | `card_arrival` |

The example above is the first test row. Its reference label is not supplied
with the query during inference. The model does receive the fixed list of
allowed labels and separate training examples. Exact label spelling and
punctuation are retained, including `reverted_card_payment?`. The loader strips
surrounding whitespace from fields in memory; it does not rewrite the CSVs.

## Split and prompt construction

`ticketroute/prompting.py` builds the split in memory. It groups original
training rows by label, shuffles with seed 42 and assigns approximately 20% of
each label to validation using the code's rounding rule. It preserves the
historical validation order so the original pilot can be reused.

| Derived set | Rows | Use |
| --- | ---: | --- |
| Validation | 1,998 | Select the review threshold after fixing the model and prompt. |
| Training core | 8,004 | Prompt examples and baseline frequencies; one core row matching a validation text is removed. |
| Prompt examples | 154 | Two distinct, deterministically selected core examples for each of 77 intents. |
| Historical pilot | 100 | First 100 validation rows, preserved from 23 August and reused in the full validation run. |

No selected prompt example occurs in validation or test, and there is no
training-core/validation text overlap. The core is used for examples and rule
frequencies; GPT-5 mini is not fine-tuned. The unchanged original files remain
the source of truth, rather than separate edited copies of each derived split.

## Duplicates and limits

The source contains six texts shared between original training and test,
including one in validation. Validation has 1,997 unique texts across 1,998
rows; test has 3,079 unique texts across 3,080 rows. These are disclosed in
[`results/data_audit.json`](../results/data_audit.json).

The primary result includes every official test row. A separate sensitivity
analysis excludes texts appearing anywhere in the original training file and
retains each remaining test text once. This yields 3,073 rows, macro-F1 0.8490
and accuracy 85.23%. It is an additional check, not a replacement test set.

The data is a public English benchmark. Its labels and language distribution
do not establish reliability for a particular bank, multilingual messages,
out-of-domain requests or changing support policies.

## Verify the bundled data

From the repository root, run this offline check:

```bash
python3 -m unittest discover -s tests -p test_data.py -v
```

It checks source-file hashes, counts, label coverage and prompt/split separation.
`ticketroute/data.py` verifies the following SHA-256 values and can download
missing files from the pinned source. Keep CSV line endings unchanged.

| File | SHA-256 |
| --- | --- |
| `train.csv` | `b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b` |
| `test.csv` | `d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d` |

For predictions, metric definitions and the evaluation sequence, see the
[evaluation guide](../results/README.md).
