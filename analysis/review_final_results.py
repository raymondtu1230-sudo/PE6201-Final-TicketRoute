#!/usr/bin/env python3
"""Audit a completed TicketRoute handback without network access or model calls."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime
from decimal import Decimal
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ticketroute.data import load_dataset, get_labels
from ticketroute.prompting import split_train_validation, select_benchmark_examples, PROMPT_VERSION
from ticketroute.openrouter_client import build_messages, DEFAULT_MODEL, _schema


def digest(value):
    return hashlib.sha256(value).hexdigest()


def score(records, labels, threshold):
    truth = Counter(r['truth'] for r in records)
    pred = Counter(r['prediction'] for r in records)
    right = Counter(r['truth'] for r in records if r['truth'] == r['prediction'])
    accepted = [r for r in records if threshold is not None and r['confidence'] >= threshold]
    deferred = [r for r in records if threshold is None or r['confidence'] < threshold]
    f1 = [2 * right[l] / (truth[l] + pred[l]) if truth[l] + pred[l] else 0 for l in labels]
    return {
        'n': len(records), 'correct': sum(right.values()),
        'errors': len(records) - sum(right.values()),
        'accuracy': sum(right.values()) / len(records),
        'macro_f1': sum(f1) / len(labels),
        'answered_count': len(accepted), 'abstained_count': len(deferred),
        'coverage': len(accepted) / len(records),
        'answered_accuracy': sum(r['truth'] == r['prediction'] for r in accepted) / len(accepted) if accepted else None,
        'accepted_errors': sum(r['truth'] != r['prediction'] for r in accepted),
        'deferred_errors': sum(r['truth'] != r['prediction'] for r in deferred),
        'abstained_would_be_error_rate': sum(r['truth'] != r['prediction'] for r in deferred) / len(deferred) if deferred else None,
        'latency_ms_median': statistics.median(r['latency_ms'] for r in records),
        'latency_ms_p95': sorted(r['latency_ms'] for r in records)[math.ceil(.95 * len(records)) - 1],
    }


def matches(actual, expected):
    if isinstance(expected, float):
        assert math.isclose(actual, expected, abs_tol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def audit(archive, previous_probe=None):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, 'ZIP integrity error'
        names = z.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP paths'
        assert all(n.startswith('TicketRoute/') and '..' not in PurePosixPath(n).parts for n in names)
        raw = {n.removeprefix('TicketRoute/'): z.read(n) for n in names}
    manifest = json.loads(raw['HAND_BACK_SHA256.json'])
    assert set(raw) == set(manifest) | {'HAND_BACK_SHA256.json'}
    assert all(digest(raw[n]) == sha for n, sha in manifest.items()), 'Manifest mismatch'
    for n in manifest:
        assert b'sk-or-v1-' not in raw[n], 'Unexpected credential-like value'
    read = lambda n: json.loads(raw['results/' + n])
    train, test = load_dataset(ROOT / 'data')
    core, validation = split_train_validation(train)
    labels = get_labels(train)
    examples = select_benchmark_examples(core, labels)
    lock = read('evaluation_lock.json')
    config = lock['configuration']
    assert digest(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()) == lock['configuration_sha256']
    assert config['model'] == DEFAULT_MODEL and config['prompt_version'] == PROMPT_VERSION
    assert config['messages_template'] == build_messages('<QUERY>', labels, examples)
    assert config['validation_sha256'] == digest(json.dumps(validation, sort_keys=True).encode())
    for name, sha in config['data_sha256'].items():
        assert digest((ROOT / 'data' / name).read_bytes()) == sha
    assert not {t for _, t in examples} & {r['text'] for r in validation + test}
    original_pilot = ROOT / 'evidence' / 'pilot_2026-08-23'
    for p in original_pilot.iterdir():
        if p.name in {'TicketRoute_v3_validation_100_predictions.csv', 'TicketRoute_v3_validation_100_report.json'}:
            assert raw['evidence/pilot_2026-08-23/' + p.name] == p.read_bytes()
    pilot_rows = list(csv.DictReader(io.StringIO(raw['evidence/pilot_2026-08-23/TicketRoute_v3_validation_100_predictions.csv'].decode())))
    calibration = read('calibrated_threshold.json')
    test_lock = read('test_lock.json')
    threshold = calibration['threshold']
    assert calibration['configuration_sha256'] == test_lock['configuration_sha256'] == lock['configuration_sha256']
    assert test_lock['calibration_sha256'] == digest(raw['results/calibrated_threshold.json'])
    assert test_lock['threshold'] == threshold and test_lock['rows'] == 3080
    records_by_split, cache_by_split, calculated = {}, {}, {}
    for split, rows in [('validation', validation), ('test', test)]:
        records = list(csv.DictReader(io.StringIO(raw[f'results/{split}_full_predictions.csv'].decode())))
        assert len(records) == len(rows)
        cached = [json.loads(line) for line in raw[f'results/cache_openai_gpt-5-mini_{split}_{PROMPT_VERSION}.jsonl'].decode().splitlines() if line.strip()]
        cache = {r['text']: r for r in cached}
        assert len(cache) == len(cached) == len({r['text'] for r in rows})
        for index, (record, source) in enumerate(zip(records, rows)):
            assert record['text'] == source['text'] and record['truth'] == source['category']
            record['confidence'] = float(record['confidence'])
            record['latency_ms'] = float(record['latency_ms'])
            record['usage'] = json.loads(record['usage'])
            for field, value in record.items():
                expected = cache[record['text']].get(field)
                if expected is None and value == '':
                    value = None
                matches(value, expected)
            assert record['prediction'] in labels and 0 <= record['confidence'] <= 1
            assert record['model'] == DEFAULT_MODEL and record['prompt_version'] == PROMPT_VERSION
            if record['usage'] is None:
                assert split == 'validation' and index < 100
                assert record['status'] in ('', 'ok')
            else:
                assert record['status'] == 'ok'
        report = read(f'{split}_full_report.json')
        calculated[split] = score(records, labels, threshold)
        for key in ['n', 'accuracy', 'macro_f1', 'latency_ms_median', 'latency_ms_p95']:
            matches(calculated[split][key], report[key])
        for key in ['answered_count', 'abstained_count', 'coverage', 'answered_accuracy', 'abstained_would_be_error_rate']:
            matches(calculated[split][key], report['abstention'][key])
        assert report['metric_label_count'] == report['truth_label_count'] == 77
        assert report['configuration_sha256'] == lock['configuration_sha256']
        assert report['model_output_failures'] == 0
        records_by_split[split], cache_by_split[split] = records, cached
    for current, original in zip(records_by_split['validation'][:100], pilot_rows):
        for key, value in original.items():
            matches(current[key], float(value) if key in ('confidence', 'latency_ms') else value)
    table = [score(records_by_split['validation'], labels, t) for t in config['threshold_candidates']]
    eligible = [t for t, s in zip(config['threshold_candidates'], table) if s['answered_accuracy'] is not None and s['answered_accuracy'] >= config['target_answered_accuracy']]
    assert threshold == (min(eligible) if eligible else None)
    for saved, recomputed in zip(calibration['threshold_table'], table):
        for key in ['answered_count', 'abstained_count', 'coverage', 'answered_accuracy', 'abstained_would_be_error_rate']:
            matches(recomputed[key], saved[key])
    training_texts = {r['text'] for r in train}
    seen, strict = set(), []
    for r in records_by_split['test']:
        if r['text'] not in training_texts and r['text'] not in seen:
            strict.append(r)
            seen.add(r['text'])
    calculated['strict_test'] = score(strict, labels, threshold)
    for key in ['n', 'accuracy', 'macro_f1']:
        matches(calculated['strict_test'][key], read('test_sensitivity_report.json')[key])
    baseline = read('baselines_core.json')['splits']['test']
    baseline_rows = list(csv.DictReader(io.StringIO(raw['results/baseline_test_predictions.csv'].decode())))
    assert [(r['text'], r['truth']) for r in baseline_rows] == [(r['text'], r['category']) for r in test]
    for method in ('keyword', 'majority'):
        rows = [{'truth':r['truth'], 'prediction':r[method], 'confidence':1, 'latency_ms':0} for r in baseline_rows]
        computed = score(rows, labels, 0)
        for key in ('n', 'accuracy', 'macro_f1'):
            matches(computed[key], baseline[method][key])
    attempts = [json.loads(line) for line in raw['results/api_attempts.jsonl'].decode().splitlines() if line.strip()]
    new_cache = [r for split in cache_by_split.values() for r in split if r.get('usage') is not None]
    assert len(attempts) == len(new_cache) == 4976
    by_id = {r['generation_id']:r for r in new_cache}
    assert len(by_id) == len(set(r['generation_id'] for r in attempts)) == len(attempts)
    total = Decimal(0)
    for event in attempts:
        assert event['event'] == 'attempt' and event['outcome'] == 'ok'
        cached = by_id[event['generation_id']]
        assert event['query_sha256'] == digest(cached['text'].encode())
        payload = {
            'model':DEFAULT_MODEL, 'messages':build_messages(cached['text'].strip(), labels, examples),
            'response_format':{'type':'json_schema','json_schema':{'name':'ticket_route','strict':True,'schema':_schema(labels)}},
            'max_tokens':1200, 'reasoning':{'effort':'low','exclude':True},
            'provider':{'require_parameters':True},
        }
        assert event['request_hash'] == digest(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode())
        for key in ['model', 'prompt_version', 'usage', 'returned_model', 'provider', 'finish_reason', 'request_hash']:
            assert event[key] == cached[key], key
        usage = event['usage']
        assert usage['total_tokens'] == usage['prompt_tokens'] + usage['completion_tokens']
        cost = Decimal(str(usage['cost_usd']))
        assert cost.is_finite() and cost >= 0
        total += cost
    expected_order = [r['generation_id'] for s in ('validation', 'test') for r in cache_by_split[s] if r.get('usage') is not None]
    assert [r['generation_id'] for r in attempts] == expected_order
    times = [datetime.fromisoformat(r['time_utc']) for r in attempts]
    assert times == sorted(times) and datetime.fromisoformat(lock['created_utc']) < times[0]
    assert str(total) == read('test_full_report.json')['new_call_ledger']['known_cost_usd']
    assert read('run_status.json')['state'] == 'evaluation_complete'
    probe_preserved = None
    if previous_probe and previous_probe.exists():
        with zipfile.ZipFile(previous_probe) as z:
            old = z.read('TicketRoute/results/api_attempts.jsonl')
            assert raw['results/api_attempts.jsonl'].startswith(old)
            old_cache = z.read(f'TicketRoute/results/cache_openai_gpt-5-mini_validation_{PROMPT_VERSION}.jsonl')
            assert raw[f'results/cache_openai_gpt-5-mini_validation_{PROMPT_VERSION}.jsonl'].startswith(old_cache)
            assert z.read('TicketRoute/results/evaluation_lock.json') == raw['results/evaluation_lock.json']
            probe_preserved = len(old.decode().splitlines())
    summary = {
        'archive_sha256':digest(archive.read_bytes()), 'archive_bytes':archive.stat().st_size,
        'manifest_files_verified':len(manifest), 'completed_utc':read('run_status.json')['updated_utc'],
        'configuration_sha256':lock['configuration_sha256'], 'threshold':threshold,
        'metrics':calculated, 'official_test_baselines':baseline,
        'new_attempts':len(attempts), 'unknown_cost_attempts':0, 'model_output_failures':0,
        'recorded_cost_usd':str(total), 'mean_new_call_cost_usd':str(total / len(attempts)),
        'historical_pilot_cost':'unknown', 'prior_probe_attempts_preserved':probe_preserved,
        'returned_models':dict(Counter(e['returned_model'] for e in attempts)),
        'providers':dict(Counter(e['provider'] for e in attempts)),
        'prompt_tokens':sum(e['usage']['prompt_tokens'] for e in attempts),
        'cached_prompt_tokens':sum(e['usage'].get('prompt_tokens_details',{}).get('cached_tokens',0) for e in attempts),
        'completion_tokens':sum(e['usage']['completion_tokens'] for e in attempts),
        'network_calls_during_audit':0,
        'checks':['ZIP CRC and manifest', 'original pilot unchanged', 'pinned dataset and fixed prompt',
                  'row order and truth labels', 'CSV and cache match', 'independent metrics',
                  'validation-only threshold selection', 'test configuration lock', 'strict sensitivity set',
                  'baseline scores', 'ledger and cache reconciliation', 'all new request hashes reconstructed',
                  'validation then test ledger order'],
    }
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--previous-probe', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.archive, args.previous_probe)
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text)
