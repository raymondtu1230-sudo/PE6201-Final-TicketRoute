"""Evaluation helpers for classification and abstention."""

from __future__ import annotations

from collections import Counter
from typing import Sequence


def classification_metrics(
    y_true: Sequence[str], y_pred: Sequence[str], labels: Sequence[str] | None = None
) -> dict[str, float | int]:
    if len(y_true) != len(y_pred) or not y_true:
        raise ValueError("y_true and y_pred must be non-empty and equally sized")
    labels = sorted(set(labels)) if labels is not None else sorted(set(y_true) | set(y_pred))
    per_label_f1: list[float] = []
    for label in labels:
        true_positive = sum(
            truth == label and pred == label for truth, pred in zip(y_true, y_pred)
        )
        false_positive = sum(
            truth != label and pred == label for truth, pred in zip(y_true, y_pred)
        )
        false_negative = sum(
            truth == label and pred != label for truth, pred in zip(y_true, y_pred)
        )
        denominator = 2 * true_positive + false_positive + false_negative
        per_label_f1.append(2 * true_positive / denominator if denominator else 0.0)
    correct = sum(truth == pred for truth, pred in zip(y_true, y_pred))
    return {
        "n": len(y_true),
        "accuracy": correct / len(y_true),
        "macro_f1": sum(per_label_f1) / len(per_label_f1),
    }


def abstention_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    confidences: Sequence[float],
    threshold: float | None,
) -> dict[str, float | int | None]:
    if not (len(y_true) == len(y_pred) == len(confidences)) or not y_true:
        raise ValueError("Inputs must be non-empty and equally sized")
    answered = [threshold is not None and score >= threshold and pred != "__MODEL_FAILURE__" for score, pred in zip(confidences, y_pred)]
    answered_count = sum(answered)
    abstained_count = len(answered) - answered_count
    answered_correct = sum(
        pred == truth
        for truth, pred, is_answered in zip(y_true, y_pred, answered)
        if is_answered
    )
    abstained_wrong = sum(
        pred != truth
        for truth, pred, is_answered in zip(y_true, y_pred, answered)
        if not is_answered
    )
    return {
        "threshold": threshold,
        "answered_count": answered_count,
        "abstained_count": abstained_count,
        "coverage": answered_count / len(answered),
        "abstention_rate": abstained_count / len(answered),
        "answered_accuracy": (
            answered_correct / answered_count if answered_count else None
        ),
        "abstained_would_be_error_rate": (
            abstained_wrong / abstained_count if abstained_count else None
        ),
    }


def top_confusions(
    y_true: Sequence[str], y_pred: Sequence[str], limit: int = 10
) -> list[dict[str, str | int]]:
    mistakes = Counter(
        (truth, pred)
        for truth, pred in zip(y_true, y_pred)
        if truth != pred
    )
    return [
        {"true": truth, "predicted": pred, "count": count}
        for (truth, pred), count in mistakes.most_common(limit)
    ]


def choose_threshold(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    confidences: Sequence[float],
    target_answered_accuracy: float = 0.85,
) -> float | None:
    """Choose the lowest threshold meeting target accuracy, maximizing coverage."""
    candidates = [round(value / 100, 2) for value in range(50, 96, 5)]
    for threshold in candidates:
        metrics = abstention_metrics(y_true, y_pred, confidences, threshold)
        if (
            metrics["answered_count"]
            and metrics["answered_accuracy"] is not None
            and float(metrics["answered_accuracy"]) >= target_answered_accuracy
        ):
            return threshold
    # A default numeric threshold would falsely imply that the target was met.
    return None
