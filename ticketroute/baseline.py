"""Transparent non-AI keyword-overlap baseline."""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "been",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "please",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "why",
    "with",
    "would",
}


def tokenize(text: str) -> set[str]:
    normalized = text.lower().replace("_", " ")
    return {
        token
        for token in re.findall(r"[a-z]+", normalized)
        if token not in STOPWORDS
    }


class KeywordBaseline:
    """Match query tokens against the literal words in each intent name."""

    def __init__(self, training_rows: Iterable[dict[str, str]]) -> None:
        rows = list(training_rows)
        self.counts = Counter(row["category"] for row in rows)
        self.labels = sorted(self.counts)
        self.majority_label = self.counts.most_common(1)[0][0]
        self.label_tokens = {label: tokenize(label) for label in self.labels}

    def predict(self, query: str) -> str:
        query_tokens = tokenize(query)
        scored: list[tuple[int, float, int, str]] = []
        for label in self.labels:
            label_tokens = self.label_tokens[label]
            overlap = len(query_tokens & label_tokens)
            union = len(query_tokens | label_tokens) or 1
            scored.append(
                (overlap, overlap / union, self.counts[label], label)
            )
        best = max(scored)
        return best[3] if best[0] > 0 else self.majority_label

    def predict_many(self, queries: Iterable[str]) -> list[str]:
        return [self.predict(query) for query in queries]

