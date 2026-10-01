#!/usr/bin/env python3
"""Verify and restore the 100 recorded v3 pilot predictions without API calls.

Source hashes protect the original CSV and report. The restoration checks row
order and labels against the deterministic validation split, imports missing
cache entries idempotently, and records that historical billing is unknown.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ticketroute.audit import EvaluationStopped, append_json, write_json
from ticketroute.data import load_dataset, get_labels
from ticketroute.evaluation import load_cache, summarise_records
from ticketroute.openrouter_client import DEFAULT_MODEL
from ticketroute.prompting import PROMPT_VERSION, split_train_validation

REPORT = 'TicketRoute_v3_validation_100_report.json'
CSV = 'TicketRoute_v3_validation_100_predictions.csv'
HASHES = {REPORT: '38efd9bffdcdee5df1bab242e41ace3b7b9af8cefe05e883dee23f95227d1fb8', CSV: 'b3eae5dcfe837d058aee3d2b124811f462fb35af510d35141fc3e2f24100b14d'}


def cache_path(root: Path, split: str) -> Path:
    return root / 'results' / f'cache_openai_gpt-5-mini_{split}_{PROMPT_VERSION}.jsonl'


def restore(root: Path = ROOT) -> list[dict]:
    source = root / 'evidence' / 'pilot_2026-08-23'
    for name, digest in HASHES.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise EvaluationStopped(f'Historical source checksum mismatch: {name}')
    train, _ = load_dataset(root / 'data')
    labels = get_labels(train)
    _, validation = split_train_validation(train)
    with (source / CSV).open(encoding='utf-8', newline='') as handle:
        records = list(csv.DictReader(handle))
    if len(records) != 100 or len({r['text'] for r in records}) != 100:
        raise EvaluationStopped('The preserved pilot must contain 100 unique queries')
    for row, expected in zip(records, validation[:100]):
        row['confidence'] = float(row['confidence'])
        row['latency_ms'] = int(row['latency_ms'])
        if row['text'] != expected['text'] or row['truth'] != expected['category'] or row['model'] != DEFAULT_MODEL or row['prompt_version'] != PROMPT_VERSION or row['prediction'] not in labels or not 0 <= row['confidence'] <= 1:
            raise EvaluationStopped('Pilot rows do not match the documented experiment')
        row.update(status='ok', usage=None, provenance='Verified 2026-08-23 historical CSV; original client did not record tokens, cost, or generation IDs')
    recomputed = summarise_records(records, .70)
    original = json.loads((source / REPORT).read_text(encoding='utf-8'))
    for metric in ('n', 'accuracy', 'macro_f1', 'abstention'):
        if recomputed[metric] != original[metric]:
            raise EvaluationStopped(f'Pilot metric mismatch: {metric}')
    path = cache_path(root, 'validation')
    cache = load_cache(path)
    for row in records:
        old = cache.get(row['text'])
        if old:
            for key in ('truth', 'prediction', 'confidence', 'model', 'prompt_version'):
                if old.get(key) != row[key]:
                    raise EvaluationStopped(f'Pilot cache disagrees on {key}')
        else:
            append_json(path, row)
    # The manifest is stable on repeated runs and does not alter the original files.
    write_json(root / 'results' / 'pilot_provenance.json', {
        'source_sha256': HASHES, 'rows': 100, 'truth_labels': 48,
        'cached_for_resume': 100, 'original_cost_and_tokens': None,
        'original_macro_f1_label_policy': 'union of labels observed in pilot truth and predictions',
        'warning': 'Pilot evidence only; not an official-test score or proof of all-77-label target achievement.'})
    return records


if __name__ == '__main__':
    print(f'Verified and restored {len(restore())} historical predictions. No API calls.')
