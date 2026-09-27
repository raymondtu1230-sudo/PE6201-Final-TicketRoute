#!/usr/bin/env python3
"""Download and verify BANKING77 data."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ticketroute.data import download_data, load_dataset  # noqa: E402


def main() -> None:
    data_dir = ROOT / "data"
    download_data(data_dir)
    train, test = load_dataset(data_dir)
    print(f"Verified {len(train):,} training and {len(test):,} test rows in {data_dir}")


if __name__ == "__main__":
    main()

