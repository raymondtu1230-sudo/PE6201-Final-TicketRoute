"""Local attempt ledger, conservative budget guard, and immutable evaluation lock."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()


class EvaluationStopped(RuntimeError):
    pass


class AttemptLedger:
    def __init__(self, path: Path, budget_usd: str = "7.00", reserve_usd: str = "0.05"):
        self.path = path
        self.budget = Decimal(str(budget_usd))
        self.reserve = Decimal(str(reserve_usd))
        if not self.budget.is_finite() or self.budget <= 0 or not self.reserve.is_finite() or self.reserve <= 0:
            raise ValueError("Budget and reserve must be positive finite amounts")
        self.events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []

    def summary(self) -> dict:
        attempts = [e for e in self.events if e.get("event") == "attempt"]
        known = [e for e in attempts if isinstance(e.get("usage"), dict) and e["usage"].get("cost_usd") is not None]
        total = sum((Decimal(str(e["usage"]["cost_usd"])) for e in known), Decimal("0"))
        return {"attempts": len(attempts), "known_cost_attempts": len(known), "unknown_cost_attempts": len(attempts)-len(known), "known_cost_usd": str(total), "budget_usd": str(self.budget)}

    def before_call(self) -> None:
        summary = self.summary()
        if summary["unknown_cost_attempts"]:
            raise EvaluationStopped("An earlier attempt has unknown cost. Preserve the ledger and reconcile it before another paid call; do not delete it or rerun that query blindly.")
        if Decimal(summary["known_cost_usd"]) + self.reserve > self.budget:
            raise EvaluationStopped("Project spending cap reached. All completed predictions are saved.")

    def record(self, event: dict) -> None:
        event = {"event": "attempt", "time_utc": timestamp(), **event}
        append_json(self.path, event)
        self.events.append(event)


def freeze_configuration(root: Path, model: str, prompt_version: str, messages: list, validation_rows: list) -> dict:
    configuration = {
        "project": "PE6201 individual Final Project TicketRoute",
        "model": model, "prompt_version": prompt_version,
        "max_tokens": 1200, "reasoning": {"effort": "low", "exclude": True},
        "provider": {"require_parameters": True},
        "messages_template": messages,
        "data_sha256": {name: hashlib.sha256((root / "data" / name).read_bytes()).hexdigest() for name in ("train.csv", "test.csv")},
        "validation_sha256": hashlib.sha256(json.dumps(validation_rows, sort_keys=True).encode()).hexdigest(),
        "primary_metric": "macro_f1_77_labels", "target_macro_f1": 0.80,
        "target_answered_accuracy": 0.85,
        "threshold_candidates": [round(i/100, 2) for i in range(50,96,5)],
        "threshold_selection": "lowest candidate meeting validation answered accuracy target; otherwise all human review",
    }
    digest = hashlib.sha256(json.dumps(configuration, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    path = root / "results" / "evaluation_lock.json"
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous.get("configuration_sha256") != digest:
            raise EvaluationStopped("Evaluation configuration changed after freezing. Use a new explicitly versioned experiment; do not mix caches.")
        return previous
    result = {"created_utc": timestamp(), "configuration_sha256": digest, "configuration": configuration}
    write_json(path, result)
    return result
