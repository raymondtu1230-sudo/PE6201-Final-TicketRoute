import unittest
from pathlib import Path

from ticketroute.data import load_dataset
from ticketroute.evaluation import keyword_report


ROOT = Path(__file__).resolve().parents[1]


class BaselineTests(unittest.TestCase):
    def test_keyword_baseline_is_reproducible(self):
        train, test = load_dataset(ROOT / "data")
        report, predictions = keyword_report(train, test)
        self.assertEqual(len(predictions), 3080)
        self.assertTrue(0.378 < float(report["macro_f1"]) < 0.380)
        self.assertTrue(0.380 < float(report["accuracy"]) < 0.382)


if __name__ == "__main__":
    unittest.main()

