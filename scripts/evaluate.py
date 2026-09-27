#!/usr/bin/env python3
"""Evaluate the keyword baseline or GPT-5 mini on BANKING77."""

from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ticketroute.data import get_labels, load_dataset  # noqa: E402
from ticketroute.evaluation import (  # noqa: E402
    evaluate_llm_rows,
    keyword_report,
    write_predictions,
)
from ticketroute.openrouter_client import (  # noqa: E402
    DEFAULT_MODEL,
    OpenRouterClient,
    OpenRouterError,
)
from ticketroute.metrics import choose_threshold  # noqa: E402
from ticketroute.prompting import (  # noqa: E402
    PROMPT_VERSION,
    select_benchmark_examples,
    split_train_validation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["keyword", "llm"], default="keyword")
    parser.add_argument("--split", choices=["validation", "test"], default="test")
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Rows to evaluate; 0 means the complete split.",
    )
    parser.add_argument(
        "--threshold",
        default="0.70",
        help="Confidence threshold from 0 to 1, or 'auto' to use saved validation calibration.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--prompt-for-key", action="store_true")
    return parser.parse_args()


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value)


def resolve_threshold(
    value: str,
    model: str,
    calibration_path: Path | None = None,
    prompt_version: str = PROMPT_VERSION,
) -> float | None:
    if value.lower() != "auto":
        try:
            threshold = float(value)
        except ValueError as exc:
            raise SystemExit("Threshold must be a number from 0 to 1, or 'auto'.") from exc
        if not 0 <= threshold <= 1:
            raise SystemExit("Threshold must be between 0 and 1.")
        return threshold

    path = calibration_path or ROOT / "results" / "calibrated_threshold.json"
    if not path.exists():
        raise SystemExit(
            "No saved validation threshold. Use START_HERE_MAC.command choice 2 to finish validation first."
        )
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("model") != model:
            raise ValueError("saved model does not match")
        if saved.get("prompt_version") != prompt_version:
            raise ValueError("saved prompt version does not match")
        if saved["threshold"] is None:
            return None
        threshold = float(saved["threshold"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit("The saved validation threshold is invalid for this model.") from exc
    if not 0 <= threshold <= 1:
        raise SystemExit("The saved validation threshold is outside 0 to 1.")
    print(f"Using validation-calibrated threshold: {threshold:.2f}")
    return threshold


def stratified_validation(
    rows: list[dict[str, str]], fraction: float = 0.20, seed: int = 42
) -> list[dict[str, str]]:
    return split_train_validation(rows, fraction=fraction, seed=seed)[1]


def main() -> None:
    """Compatibility entrypoint; the audited workflow owns all paid calls."""
    args = parse_args()
    from scripts.run_project import main as workflow_main
    if args.model != DEFAULT_MODEL:
        raise SystemExit("This frozen experiment uses openai/gpt-5-mini. Create a separately versioned experiment for another model.")
    if args.mode == "keyword" or (args.split == "validation" and args.limit == 100):
        forwarded = ["--offline"]
    else:
        if args.limit != 0:
            raise SystemExit("Use --limit 0 for the full frozen evaluation, or run START_HERE_MAC.command.")
        if args.split == "test" and args.threshold != "auto":
            raise SystemExit("Official test requires --threshold auto from full validation.")
        forwarded = ["--stage", args.split]
        if args.prompt_for_key:
            forwarded.append("--prompt-for-key")
    sys.argv = ["run_project.py", *forwarded]
    raise SystemExit(workflow_main())


if __name__ == "__main__":
    main()
