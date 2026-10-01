"""Check threshold loading and safe reuse of versioned prediction caches.

Temporary fixtures exercise model/prompt mismatch handling and confirm that
resumption calls a synthetic client only for uncached rows.
"""

import json
from pathlib import Path
import tempfile
import unittest

from scripts.evaluate import resolve_threshold
from ticketroute.evaluation import evaluate_llm_rows
from ticketroute.openrouter_client import ModelPrediction
from ticketroute.prompting import PROMPT_VERSION


class ThresholdResolutionTests(unittest.TestCase):
    def test_numeric_threshold(self) -> None:
        self.assertEqual(resolve_threshold("0.73", "openai/gpt-5-mini"), 0.73)

    def test_auto_threshold_matches_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibrated_threshold.json"
            path.write_text(
                json.dumps(
                    {
                        "model": "openai/gpt-5-mini",
                        "prompt_version": PROMPT_VERSION,
                        "threshold": 0.68,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                resolve_threshold("auto", "openai/gpt-5-mini", path), 0.68
            )

    def test_auto_threshold_rejects_other_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibrated_threshold.json"
            path.write_text(
                json.dumps(
                    {
                        "model": "another-model",
                        "prompt_version": PROMPT_VERSION,
                        "threshold": 0.68,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                resolve_threshold("auto", "openai/gpt-5-mini", path)

    def test_old_prompt_cache_is_not_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "text": "sample query",
                        "truth": "label_a",
                        "prediction": "wrong_old_label",
                        "confidence": 0.99,
                        "reason": "old prompt",
                        "model": "test-model",
                        "latency_ms": 1,
                        "prompt_version": "obsolete_prompt",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            calls: list[str] = []

            def classify(text: str) -> ModelPrediction:
                calls.append(text)
                return ModelPrediction("label_a", 0.91, "new prompt", "test-model", 2)

            report, records = evaluate_llm_rows(
                [{"text": "sample query", "category": "label_a"}],
                classify,
                path,
                prompt_version=PROMPT_VERSION,
                threshold=0.70,
            )
            self.assertEqual(calls, ["sample query"])
            self.assertEqual(records[0]["prompt_version"], PROMPT_VERSION)
            self.assertEqual(report["accuracy"], 1.0)

    def test_resume_calls_only_uncached_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.jsonl"
            cached_rows = [
                {
                    "text": f"query {index}",
                    "truth": "label_a",
                    "prediction": "label_a",
                    "confidence": 0.9,
                    "reason": "cached valid result",
                    "model": "test-model",
                    "latency_ms": 1,
                    "prompt_version": PROMPT_VERSION,
                }
                for index in range(75)
            ]
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in cached_rows),
                encoding="utf-8",
            )
            calls: list[str] = []

            def classify(text: str) -> ModelPrediction:
                calls.append(text)
                return ModelPrediction("label_a", 0.9, "new valid result", "test-model", 2)

            rows = [
                {"text": f"query {index}", "category": "label_a"}
                for index in range(100)
            ]
            _, records = evaluate_llm_rows(
                rows,
                classify,
                path,
                prompt_version=PROMPT_VERSION,
                threshold=0.70,
            )
            self.assertEqual(calls, [f"query {index}" for index in range(75, 100)])
            self.assertEqual(len(records), 100)
            self.assertEqual(
                path.read_text(encoding="utf-8").count("\n"),
                100,
            )


if __name__ == "__main__":
    unittest.main()
