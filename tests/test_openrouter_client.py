import unittest
from unittest.mock import patch
import json

from ticketroute.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
    _parse_model_response,
    validate_model_payload,
)
from ticketroute.taxonomy import INTENT_GUIDE


LABELS = list(INTENT_GUIDE)
EXAMPLES = [
    (label, f"Training example {index} for {label}")
    for label in LABELS
    for index in (1, 2)
]


class OpenRouterClientTests(unittest.TestCase):
    def test_valid_structured_prediction_and_abstention(self):
        result = validate_model_payload(
            {"intent": LABELS[2], "confidence": 0.62, "reason": "Two intents overlap."},
            LABELS,
            "test-model",
            123,
        )
        self.assertEqual(result.intent, LABELS[2])
        self.assertEqual(result.decision(0.70), "HUMAN_REVIEW")
        self.assertEqual(result.decision(0.60), LABELS[2])

    def test_unknown_label_is_rejected(self):
        with self.assertRaises(OpenRouterError):
            validate_model_payload(
                {"intent": "invented", "confidence": 0.9, "reason": "Wrong."},
                LABELS,
                "test-model",
                10,
            )

    @patch("ticketroute.openrouter_client.urlopen")
    def test_client_parses_a_structured_response(self, mocked_urlopen):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                content = json.dumps(
                    {"intent": LABELS[5], "confidence": 0.91, "reason": "Best fit."}
                )
                return json.dumps(
                    {"choices": [{"message": {"content": content}}]}
                ).encode("utf-8")

        mocked_urlopen.return_value = FakeResponse()
        result = OpenRouterClient("secret-test-key").classify(
            "test query", LABELS, EXAMPLES
        )
        self.assertEqual(result.intent, LABELS[5])
        request = mocked_urlopen.call_args.args[0]
        sent = json.loads(request.data.decode("utf-8"))
        self.assertEqual(sent["response_format"]["type"], "json_schema")
        self.assertEqual(len(sent["response_format"]["json_schema"]["schema"]["properties"]["intent"]["enum"]), 77)
        self.assertIn(f"Training example 2 for {LABELS[5]}", sent["messages"][1]["content"])
        self.assertIn(INTENT_GUIDE[LABELS[5]], sent["messages"][1]["content"])
        self.assertEqual(sent["reasoning"]["effort"], "low")
        self.assertEqual(sent["max_tokens"], 1200)
        self.assertTrue(sent["provider"]["require_parameters"])

    def test_content_block_response_is_parsed(self):
        payload = {"intent": LABELS[1], "confidence": 0.88, "reason": "Clear fit."}
        body = json.dumps(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": [{"type": "output_text", "text": json.dumps(payload)}]
                        },
                    }
                ]
            }
        )
        parsed, finish_reason = _parse_model_response(body)
        self.assertEqual(parsed, payload)
        self.assertEqual(finish_reason, "stop")

    def test_truncated_response_reports_finish_reason(self):
        body = json.dumps(
            {
                "choices": [
                    {"finish_reason": "length", "message": {"content": ""}}
                ]
            }
        )
        with self.assertRaisesRegex(OpenRouterError, "finish_reason=length"):
            _parse_model_response(body)


if __name__ == "__main__":
    unittest.main()
