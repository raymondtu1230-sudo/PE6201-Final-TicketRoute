import unittest
from collections import Counter
from pathlib import Path

from ticketroute.data import get_labels, load_dataset
from ticketroute.prompting import (
    EXAMPLES_PER_LABEL,
    select_benchmark_examples,
    split_train_validation,
)
from ticketroute.taxonomy import INTENT_GUIDE


ROOT = Path(__file__).resolve().parents[1]


class DataTests(unittest.TestCase):
    def test_official_data_integrity_and_shape(self):
        train, test = load_dataset(ROOT / "data")
        self.assertEqual(len(train), 10003)
        self.assertEqual(len(test), 3080)
        self.assertEqual(len(get_labels(train)), 77)

    def test_validation_split_and_examples_do_not_leak(self):
        train, _ = load_dataset(ROOT / "data")
        core, validation = split_train_validation(train)
        self.assertEqual(len(core), 8004)
        self.assertEqual(len(validation), 1998)
        self.assertFalse({row["text"] for row in core} & {row["text"] for row in validation})
        examples = select_benchmark_examples(core, get_labels(train))
        self.assertEqual(set(INTENT_GUIDE), set(get_labels(train)))
        self.assertEqual(len(examples), 77 * EXAMPLES_PER_LABEL)
        self.assertEqual(len({label for label, _ in examples}), 77)
        self.assertEqual(
            Counter(label for label, _ in examples),
            Counter({label: EXAMPLES_PER_LABEL for label in get_labels(train)}),
        )
        self.assertEqual(len({text for _, text in examples}), len(examples))
        self.assertFalse(
            {text for _, text in examples} & {row["text"] for row in validation}
        )


if __name__ == "__main__":
    unittest.main()
