"""Load the pinned BANKING77 source files with integrity checks.

Missing CSVs can be downloaded from the fixed upstream commit. Bundled files
are checked against expected SHA-256 hashes, row counts and field structure.
Source files stay unchanged; loaded text/category fields have surrounding
whitespace stripped. Splitting and prompt-example selection are handled
separately by prompting.py.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


SOURCE_COMMIT = "57ec275d8078af65b7731c2a98be812d844a6d6b"
BASE_URL = (
    "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/"
    f"{SOURCE_COMMIT}/banking_data"
)
FILES = {
    "train.csv": {
        "url": f"{BASE_URL}/train.csv",
        "sha256": "b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b",
        "rows": 10003,
    },
    "test.csv": {
        "url": f"{BASE_URL}/test.csv",
        "sha256": "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
        "rows": 3080,
    },
}


class DataIntegrityError(RuntimeError):
    """Raised when downloaded or bundled data fails validation."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_data(data_dir: Path, overwrite: bool = False) -> None:
    """Download the two author-released CSV files and verify their hashes."""
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename, metadata in FILES.items():
        destination = data_dir / filename
        if destination.exists() and not overwrite:
            verify_file(destination, filename)
            continue
        request = Request(metadata["url"], headers={"User-Agent": "TicketRoute/0.1"})
        with urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())
        verify_file(destination, filename)


def verify_file(path: Path, filename: str | None = None) -> None:
    name = filename or path.name
    if name not in FILES:
        raise DataIntegrityError(f"No manifest entry for {name}")
    actual = sha256_file(path)
    expected = str(FILES[name]["sha256"])
    if actual != expected:
        raise DataIntegrityError(
            f"SHA-256 mismatch for {path}: expected {expected}, got {actual}"
        )


def read_split(path: Path, verify: bool = True) -> list[dict[str, str]]:
    if verify:
        verify_file(path)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["text", "category"]:
            raise DataIntegrityError(
                f"Unexpected columns in {path}: {reader.fieldnames!r}"
            )
        rows = [
            {"text": row["text"].strip(), "category": row["category"].strip()}
            for row in reader
        ]
    expected_rows = int(FILES[path.name]["rows"])
    if len(rows) != expected_rows:
        raise DataIntegrityError(
            f"Unexpected row count in {path}: expected {expected_rows}, got {len(rows)}"
        )
    return rows


def load_dataset(data_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return official train and test rows, downloading them if needed."""
    if not all((data_dir / filename).exists() for filename in FILES):
        download_data(data_dir)
    return read_split(data_dir / "train.csv"), read_split(data_dir / "test.csv")


def get_labels(rows: Iterable[dict[str, str]]) -> list[str]:
    labels = sorted({row["category"] for row in rows})
    if len(labels) != 77:
        raise DataIntegrityError(f"Expected 77 labels, found {len(labels)}")
    return labels
