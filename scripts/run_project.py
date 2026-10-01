#!/usr/bin/env python3
"""Run the frozen validation-then-test evaluation and export its evidence.

Preparation verifies the pilot, data split, prompt and baseline comparisons.
Paid execution uses an exclusive run lock, sequential cached predictions and
a cumulative cost ledger. Validation selects the threshold before the test
lock is written. The offline option prepares local evidence without model
calls; completed runs retain the recorded configuration and decision rule.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import contextmanager
import csv
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_pilot import restore, cache_path
from scripts.finalise_outputs import export_outputs
from ticketroute.audit import AttemptLedger, EvaluationStopped, freeze_configuration, timestamp, write_json
from ticketroute.baseline import KeywordBaseline
from ticketroute.calibration import read_calibration
from ticketroute.data import load_dataset, get_labels
from ticketroute.evaluation import evaluate_llm_rows, write_predictions, summarise_records
from ticketroute.metrics import classification_metrics, choose_threshold, abstention_metrics
from ticketroute.openrouter_client import OpenRouterClient, DEFAULT_MODEL, build_messages
from ticketroute.prompting import PROMPT_VERSION, split_train_validation, select_benchmark_examples


@contextmanager
def single_run(root: Path):
    """OS releases the lock even after a crash; prevents two paid runs at once."""
    path = root / 'results' / 'evaluation.runlock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        try:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                if not handle.read(1):
                    handle.write(b'0'); handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise EvaluationStopped('Another evaluation is running. Keep its window open; do not start a second copy.') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def prepare(root: Path = ROOT):
    records = restore(root)
    train, test = load_dataset(root / 'data')
    core, validation = split_train_validation(train)
    labels = get_labels(train)
    examples = select_benchmark_examples(core, labels)
    prompt_texts = {text for _, text in examples}
    if prompt_texts & {r['text'] for r in validation + test}:
        raise EvaluationStopped('Prompt examples overlap validation/test data')
    lock = freeze_configuration(root, DEFAULT_MODEL, PROMPT_VERSION, build_messages('<QUERY>', labels, examples), validation)
    baseline = KeywordBaseline(core)
    # Both rules use training-core frequencies only, including their tie-breaks.
    baseline_reports = {'training_rows': len(core), 'majority_label': baseline.majority_label, 'label_policy': 'fixed 77; zero for zero denominator', 'splits': {}}
    for split, rows in [('pilot', validation[:100]), ('validation', validation), ('test', test)]:
        truth = [r['category'] for r in rows]
        predictions = baseline.predict_many(r['text'] for r in rows)
        baseline_reports['splits'][split] = {
            'keyword': classification_metrics(truth, predictions, labels),
            'majority': classification_metrics(truth, [baseline.majority_label]*len(rows), labels)}
        out = root / 'results' / f'baseline_{split}_predictions.csv'
        with out.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['text','truth','keyword','majority'])
            writer.writerows((r['text'],r['category'],p,baseline.majority_label) for r,p in zip(rows,predictions))
    write_json(root / 'results' / 'baselines_core.json', baseline_reports)
    write_json(root / 'results' / 'pilot_comparison.json', {
        'historical_observed_label_macro': summarise_records(records,.70),
        'fixed_77_label_macro': summarise_records(records,.70,labels),
        'warning': 'Only 48 truth labels appear in 100 pilot queries; neither pilot macro definition is the final test metric.'})
    write_json(root / 'results' / 'data_audit.json', {
        'train_rows':len(train),'train_core_rows':len(core),'validation_rows':len(validation),'test_rows':len(test),
        'prompt_examples':len(examples),'prompt_validation_overlap':0,'prompt_test_overlap':0,
        'validation_truth_labels':len({r['category'] for r in validation}),
        'test_truth_labels':len({r['category'] for r in test}),
        'train_validation_text_overlap':len({r['text'] for r in core}&{r['text'] for r in validation}),
        'validation_test_text_overlap':len({r['text'] for r in validation}&{r['text'] for r in test}),
        'train_test_text_overlap':len({r['text'] for r in train}&{r['text'] for r in test}),
        'validation_unique_texts':len({r['text'] for r in validation}),
        'test_unique_texts':len({r['text'] for r in test}),
        'historical_pilot_rows':100,'new_unique_calls_needed':len({r['text'] for r in validation})+len({r['text'] for r in test})-100,
        'sensitivity_policy':'Additionally score unique test texts absent from the entire original training file; preserve official test as primary.'})
    return labels, examples, validation, test, lock


def save_evaluation(root, split, rows, threshold, client, labels, examples, ledger, lock):
    print(f'\n{split}: {len(rows):,} queries. Cached predictions are reused.', flush=True)
    def progress(done, total):
        if done == total or done % 25 == 0:
            summary = ledger.summary()
            print(f'  {done:,}/{total:,} | new-run recorded cost US${summary["known_cost_usd"]}', flush=True)
    report, records = evaluate_llm_rows(rows, lambda text: client.classify(text, labels, examples),
        cache_path(root,split), PROMPT_VERSION, threshold, progress=progress,
        labels=labels, model=DEFAULT_MODEL, ledger=ledger)
    report.update(split=split, configuration_sha256=lock['configuration_sha256'], generated_utc=timestamp())
    write_json(root / 'results' / f'{split}_full_report.json',report)
    write_predictions(root / 'results' / f'{split}_full_predictions.csv',records)
    return report, records


def run_paid(root, key, budget, stage='all'):
    labels, examples, validation, test, lock = prepare(root)
    ledger = AttemptLedger(root / 'results' / 'api_attempts.jsonl',budget)
    write_json(root/'results'/'evaluation_budget.json',{'budget_usd':str(ledger.budget),'reserve_usd':str(ledger.reserve),'scope':'new evaluation attempts; original pilot cost unknown'})
    client = OpenRouterClient(key)
    # The first five new calls check current provider/schema/billing compatibility.
    # These are real validation rows, kept even if incorrect; no cherry-picking.
    if stage != 'test':
        for stop in (101,105):
            _, smoke_records = evaluate_llm_rows(validation[:stop],lambda text:client.classify(text,labels,examples),
                cache_path(root,'validation'),PROMPT_VERSION,.70,labels=labels,model=DEFAULT_MODEL,ledger=ledger)
            if any(r.get('status')=='model_failure' for r in smoke_records[100:]):
                raise EvaluationStopped('Provider check encountered a schema/output failure. Its result is preserved; inspect it before spending on the full run.')
        print('Provider check completed; its five predictions count toward full validation.',flush=True)
        _, records = save_evaluation(root,'validation',validation,.70,client,labels,examples,ledger,lock)
        truth,pred,scores = ([r['truth'] for r in records],[r['prediction'] for r in records],[r['confidence'] for r in records])
        threshold = choose_threshold(truth,pred,scores)
        calibration = {'model':DEFAULT_MODEL,'prompt_version':PROMPT_VERSION,'threshold':threshold,
            'validation_rows':len(records),'target_answered_accuracy':.85,
            'configuration_sha256':lock['configuration_sha256'],
            'source_report':'validation_full_report.json','selection_rule':lock['configuration']['threshold_selection'],
            'threshold_table':[abstention_metrics(truth,pred,scores,t) for t in lock['configuration']['threshold_candidates']]}
        saved_path = root / 'results' / 'calibrated_threshold.json'
        if saved_path.exists() and json.loads(saved_path.read_text(encoding='utf-8')) != calibration:
            raise EvaluationStopped('Frozen threshold changed. Do not overwrite a completed evaluation.')
        write_json(saved_path,calibration)
        calibrated_report = summarise_records(records,threshold,labels)
        calibrated_report.update(split='validation',configuration_sha256=lock['configuration_sha256'])
        write_json(root / 'results' / 'validation_full_report.json',calibrated_report)
        print('Validation complete. Decision rule frozen before official test.',flush=True)
    if stage != 'validation':
        calibration = read_calibration(root,required=True)
        test_lock_path = root / 'results' / 'test_lock.json'
        test_lock = {'configuration_sha256':lock['configuration_sha256'],
            'calibration_sha256':hashlib.sha256((root/'results'/'calibrated_threshold.json').read_bytes()).hexdigest(),
            'threshold':calibration['threshold'],'rows':len(test)}
        if test_lock_path.exists() and json.loads(test_lock_path.read_text(encoding='utf-8')) != test_lock:
            raise EvaluationStopped('Official-test lock changed. Test data must not be used for tuning.')
        write_json(test_lock_path,test_lock)
        save_evaluation(root,'test',test,calibration['threshold'],client,labels,examples,ledger,lock)
        from ticketroute.evaluation import load_cache
        train,_=load_dataset(root/'data')
        training_texts={r['text'] for r in train}
        all_cached=load_cache(cache_path(root,'test'))
        seen=set(); strict=[]
        for row in test:
            if row['text'] not in training_texts and row['text'] not in seen:
                strict.append(all_cached[row['text']]); seen.add(row['text'])
        sensitivity=summarise_records(strict,calibration['threshold'],labels)
        sensitivity.update(policy='unique test texts absent from original training file',configuration_sha256=lock['configuration_sha256'])
        write_json(root/'results'/'test_sensitivity_report.json',sensitivity)
        print('Official test complete. The prompt and threshold were not changed using test results.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true',help='Verify real pilot and baselines; no API calls')
    parser.add_argument('--prompt-for-key',action='store_true')
    parser.add_argument('--budget-usd',default='7.00',help='Local new-run spending stop, excluding unknown historical pilot costs')
    parser.add_argument('--stage',choices=['all','validation','test'],default='all')
    args=parser.parse_args()
    state='offline_prepared'; message='Offline checks completed with no new model calls. See the saved reports for evaluation progress.'
    code=0
    acquired=False
    try:
        with single_run(ROOT):
            acquired=True
            prepare(ROOT)
            if not args.offline:
                key=os.environ.get('OPENROUTER_API_KEY','').strip()
                if not key and args.prompt_for_key:
                    key=getpass.getpass('Paste the course OpenRouter key here (hidden; not saved): ').strip()
                if not key:
                    raise EvaluationStopped('No API key. Offline preparation is complete. Use --prompt-for-key or set OPENROUTER_API_KEY locally.')
                print(f'Local spending stop: US${args.budget_usd} for new evaluation attempts. Historical pilot cost is unknown.',flush=True)
                run_paid(ROOT,key,args.budget_usd,args.stage)
                state='evaluation_complete' if args.stage!='validation' else 'validation_complete'
                message='Evaluation complete. Results are saved under results/.'
    except (EvaluationStopped,OSError,ValueError) as exc:
        state='stopped'; message=str(exc); code=1
        print(f'\nSTOPPED: {message}',flush=True)
    except KeyboardInterrupt:
        state='interrupted'; message='Stopped by the user. Completed predictions were preserved.'; code=1
    finally:
        if acquired:
            status_path = ROOT / 'results' / 'run_status.json'
            preserve_completed = False
            if args.offline and code == 0 and status_path.exists():
                try:
                    preserve_completed = json.loads(status_path.read_text(encoding='utf-8')).get('state') == 'evaluation_complete'
                except (OSError, ValueError, AttributeError):
                    pass
            # Successful offline checks must preserve the completed run and its timestamp.
            if not preserve_completed:
                write_json(status_path,{'state':state,'message':message,'updated_utc':timestamp()})
            export_outputs(ROOT)
            print('\nResults exported to TicketRoute_Results.zip. API keys are not included.',flush=True)
    return code


if __name__=='__main__':
    raise SystemExit(main())
