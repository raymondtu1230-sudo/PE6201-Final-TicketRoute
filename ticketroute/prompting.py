"""Deterministic validation split and contrastive benchmark examples."""

from __future__ import annotations

from collections import Counter, defaultdict
import random
import re
from typing import Sequence


PROMPT_VERSION = "contrastive_taxonomy_v3"
EXAMPLES_PER_LABEL = 2


def split_train_validation(
    rows: list[dict[str, str]], fraction: float = 0.20, seed: int = 42
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return train-core and validation rows without changing the v1 validation order."""
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)

    rng = random.Random(seed)
    train_core: list[dict[str, str]] = []
    validation: list[dict[str, str]] = []
    for label_rows in grouped.values():
        shuffled = list(label_rows)
        rng.shuffle(shuffled)
        count = max(1, round(len(shuffled) * fraction))
        validation.extend(shuffled[:count])
        train_core.extend(shuffled[count:])
    rng.shuffle(validation)
    validation_texts = {row["text"] for row in validation}
    train_core = [row for row in train_core if row["text"] not in validation_texts]
    random.Random(seed + 1).shuffle(train_core)
    return train_core, validation


def _terms(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower().replace("_", " ")))


def select_benchmark_examples(
    train_core: list[dict[str, str]], labels: Sequence[str]
) -> list[tuple[str, str]]:
    """Choose two clear, non-identical, training-only examples for every label."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in train_core:
        grouped[row["category"]].append(row["text"])

    examples: list[tuple[str, str]] = []
    for label in labels:
        candidates = grouped.get(label, [])
        if not candidates:
            raise ValueError(f"No train-core example is available for {label}")
        concise = [
            text
            for text in candidates
            if 5 <= len(re.findall(r"[a-z0-9]+", text.lower())) <= 24
        ]
        if len(concise) >= EXAMPLES_PER_LABEL:
            candidates = concise
        label_terms = _terms(label) - {
            "a",
            "after",
            "and",
            "by",
            "for",
            "my",
            "not",
            "of",
            "or",
            "the",
            "to",
            "up",
            "via",
        }

        def clarity(text: str) -> tuple[int, int, int, str]:
            words = re.findall(r"[a-z0-9]+", text.lower())
            overlap = len(label_terms & set(words))
            return overlap, -abs(len(words) - 10), -len(text), text

        ranked = sorted(candidates, key=clarity, reverse=True)
        first = ranked[0]
        first_terms = _terms(first)

        def second_score(text: str) -> tuple[int, int, int, int, str]:
            words = re.findall(r"[a-z0-9]+", text.lower())
            overlap = len(label_terms & set(words))
            novelty = len(_terms(text) - first_terms)
            return overlap, novelty, -abs(len(words) - 12), -len(text), text

        second = max((text for text in candidates if text != first), key=second_score)
        examples.extend(((label, first), (label, second)))

    counts = Counter(label for label, _ in examples)
    if counts != Counter({label: EXAMPLES_PER_LABEL for label in labels}):
        raise ValueError("Every label must have exactly two distinct examples")
    return examples
