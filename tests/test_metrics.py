import unittest

from ticketroute.metrics import abstention_metrics, classification_metrics


class MetricsTests(unittest.TestCase):
    def test_classification_and_abstention_metrics(self):
        truth = ["a", "a", "b", "b"]
        pred = ["a", "b", "b", "a"]
        scores = [0.9, 0.4, 0.8, 0.3]
        summary = classification_metrics(truth, pred)
        abstention = abstention_metrics(truth, pred, scores, 0.7)
        self.assertEqual(summary["accuracy"], 0.5)
        self.assertEqual(abstention["coverage"], 0.5)
        self.assertEqual(abstention["answered_accuracy"], 1.0)
        self.assertEqual(abstention["abstained_would_be_error_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()

