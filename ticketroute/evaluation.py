"""Sequential, resumable evaluation with explicit model failures and cost evidence."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import statistics
import time
from pathlib import Path
from typing import Callable, Iterable
from .audit import AttemptLedger, EvaluationStopped, append_json
from .baseline import KeywordBaseline
from .metrics import abstention_metrics, classification_metrics, top_confusions
from .openrouter_client import ModelPrediction, OpenRouterError


def keyword_report(train_rows, test_rows):
    baseline = KeywordBaseline(train_rows)
    truth = [row['category'] for row in test_rows]
    predictions = baseline.predict_many(row['text'] for row in test_rows)
    report = classification_metrics(truth, predictions)
    report.update(model='literal_keyword_overlap', top_confusions=top_confusions(truth, predictions))
    return report, predictions


def load_cache(path: Path) -> dict[str, dict]:
    cache = {}
    if path.exists():
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                text = row['text']
            except (ValueError, KeyError, TypeError) as exc:
                raise EvaluationStopped(f'Damaged cache line {number}; preserve the file for repair') from exc
            prior = cache.get(text)
            if prior and prior.get('prompt_version') == row.get('prompt_version') and prior != row:
                raise EvaluationStopped('Conflicting duplicate cache records; preserve evidence for review')
            cache[text] = row
    return cache


def summarise_records(records: list[dict], threshold: float | None, labels=None) -> dict:
    if not records:
        raise ValueError('No records to summarise')
    truth = [str(r['truth']) for r in records]
    predictions = [str(r['prediction']) for r in records]
    confidences = [float(r['confidence']) for r in records]
    report = classification_metrics(truth, predictions, labels=labels)
    report.update({
        'metric_label_count': len(set(labels)) if labels is not None else len(set(truth)|set(predictions)),
        'truth_label_count': len(set(truth)),
        'abstention': abstention_metrics(truth, predictions, confidences, threshold),
        'top_confusions': top_confusions(truth, predictions),
        'model': records[0]['model'], 'prompt_version': records[0]['prompt_version'],
        'model_output_failures': sum(r.get('status') == 'model_failure' for r in records),
        'legacy_usage_missing_rows': sum(r.get('usage') is None and r.get('status', 'ok') == 'ok' for r in records),
        'latency_ms_median': statistics.median(float(r['latency_ms']) for r in records),
        'latency_ms_p95': sorted(float(r['latency_ms']) for r in records)[max(0, math.ceil(.95*len(records))-1)],
    })
    return report


def evaluate_llm_rows(rows: list[dict], classify: Callable[[str], ModelPrediction], cache_path: Path,
                      prompt_version: str, threshold: float | None, delay_seconds=0.0,
                      progress=None, *, labels=None, model=None, ledger: AttemptLedger | None = None):
    cache = {text:r for text,r in load_cache(cache_path).items() if r.get('prompt_version') == prompt_version}
    records = []
    for index, row in enumerate(rows, 1):
        cached = cache.get(row['text'])
        if cached is not None:
            if cached.get('truth') != row['category'] or (model and cached.get('model') != model):
                raise EvaluationStopped('Cached truth or model does not match this evaluation')
            if cached.get('status', 'ok') == 'ok':
                confidence = cached.get('confidence')
                if isinstance(confidence,bool) or not isinstance(confidence,(float,int)) or not math.isfinite(confidence) or not 0<=confidence<=1:
                    raise EvaluationStopped('Invalid cached confidence')
                if labels is not None and cached.get('prediction') not in labels:
                    raise EvaluationStopped('Invalid cached label')
            elif cached.get('status') != 'model_failure' or cached.get('prediction') != '__MODEL_FAILURE__' or cached.get('confidence') != 0:
                raise EvaluationStopped('Invalid cached failure record')
        else:
            if ledger:
                ledger.before_call()
            started = time.perf_counter()
            try:
                p = classify(row['text'])
                cached = {'text':row['text'], 'truth':row['category'], 'prediction':p.intent,
                    'confidence':p.confidence, 'reason':p.reason, 'model':p.model,
                    'latency_ms':p.latency_ms, 'prompt_version':prompt_version, 'status':'ok',
                    **{key:getattr(p,key,None) for key in ('usage','generation_id','returned_model','provider','finish_reason','request_hash')}}
            except KeyboardInterrupt:
                if ledger:
                    ledger.record({'query_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),
                        'model':model,'prompt_version':prompt_version,'outcome':'interrupted','usage':None})
                raise
            except OpenRouterError as exc:
                metadata = exc.metadata
                if ledger:
                    ledger.record({'query_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),
                        'model':model, 'prompt_version':prompt_version, 'outcome':exc.category,
                        'error':str(exc), **metadata})
                if exc.category != 'model_output':
                    raise EvaluationStopped(f'Service or protocol error: {exc}. Saved predictions remain intact.') from exc
                cached = {'text':row['text'], 'truth':row['category'], 'prediction':'__MODEL_FAILURE__',
                    'confidence':0.0, 'reason':str(exc), 'model':model or 'unknown',
                    'latency_ms':round((time.perf_counter()-started)*1000), 'prompt_version':prompt_version,
                    'status':'model_failure', **metadata}
                append_json(cache_path, cached)
                cache[row['text']] = cached
                if ledger and not cached.get('usage'):
                    raise EvaluationStopped('Output failure recorded, but billing is unknown. Stop and reconcile before continuing.') from exc
            else:
                if ledger:
                    ledger.record({'query_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),
                        'model':p.model, 'prompt_version':prompt_version, 'outcome':'ok',
                        **{key:cached[key] for key in ('usage','generation_id','returned_model','provider','finish_reason','request_hash')}})
                append_json(cache_path, cached)
                cache[row['text']] = cached
                if ledger and not p.usage:
                    raise EvaluationStopped('Prediction saved, but usage/cost is missing. Stop and reconcile before continuing.')
            if delay_seconds:
                time.sleep(delay_seconds)
        records.append(cached)
        if progress:
            progress(index, len(rows))
    report = summarise_records(records, threshold, labels=labels)
    if ledger:
        report['new_call_ledger'] = ledger.summary()
    return report, records


def write_predictions(path: Path, records: Iterable[dict]) -> None:
    rows = list(records)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ['text','truth','prediction','confidence','reason','model','latency_ms','prompt_version','status','usage','generation_id','returned_model','provider','finish_reason','request_hash']
    with path.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({**row,'usage':json.dumps(row.get('usage'),sort_keys=True)})
