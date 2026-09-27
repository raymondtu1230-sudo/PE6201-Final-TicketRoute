#!/usr/bin/env python3
"""Turn saved evidence into an honest report draft and a credential-free handback."""
from __future__ import annotations
import csv
from decimal import Decimal
import hashlib
import html
import json
from pathlib import Path
import re
import zipfile


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


def pct(value):
    return 'not available' if value is None else f'{100*value:.1f}%'


def per_label_rows(records, labels):
    for label in labels:
        tp=sum(r['truth']==label and r['prediction']==label for r in records)
        fp=sum(r['truth']!=label and r['prediction']==label for r in records)
        fn=sum(r['truth']==label and r['prediction']!=label for r in records)
        yield [label,tp+fn,tp/(tp+fp) if tp+fp else 0,tp/(tp+fn) if tp+fn else 0,2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0]


def analyse_split(root, split):
    path=root/'results'/f'{split}_full_predictions.csv'
    if not path.exists(): return
    from ticketroute.taxonomy import INTENT_GUIDE
    with path.open(encoding='utf-8',newline='') as handle: records=list(csv.DictReader(handle))
    out=root/'submission'/f'{split}_per_intent.csv'
    with out.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.writer(handle); writer.writerow(['intent','support','precision','recall','f1'])
        writer.writerows(per_label_rows(records,sorted(INTENT_GUIDE)))
    with (root/'submission'/f'{split}_errors.csv').open('w',encoding='utf-8',newline='') as handle:
        fields=['text','truth','prediction','confidence','reason','status']
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore'); writer.writeheader()
        writer.writerows(r for r in records if r['truth']!=r['prediction'])


def report_text(root):
    from ticketroute.audit import AttemptLedger
    pilot=read_json(root/'evidence'/'pilot_2026-08-23'/'TicketRoute_v3_validation_100_report.json')
    baseline=read_json(root/'results'/'baselines_core.json')
    validation=read_json(root/'results'/'validation_full_report.json')
    test=read_json(root/'results'/'test_full_report.json')
    calibration=read_json(root/'results'/'calibrated_threshold.json')
    sensitivity=read_json(root/'results'/'test_sensitivity_report.json')
    if not pilot or not baseline:
        return '# TicketRoute evidence preparation stopped\n\nPreserve run_status.json and the original files for diagnosis. No final evaluation is claimed.\n'
    complete=bool(validation and test and validation['n']==1998 and test['n']==3080 and calibration)
    stage='EVALUATION COMPLETE — submission draft awaiting repository and recorded-demo verification' if complete else 'PRE-FINAL DRAFT — 100-query pilot only; full validation and official test are still pending'
    if complete:
        a=test['abstention']; v=validation['abstention']
        evaluation=f'''The official test covers all 3,080 queries and 77 intents. GPT-5 mini achieves macro-F1 {test['macro_f1']:.4f} and accuracy {pct(test['accuracy'])}. The predeclared 0.80 macro-F1 target is {'met' if test['macro_f1']>=.80 else 'not met'}. On validation, the frozen decision rule routes {pct(v['coverage'])} at {pct(v['answered_accuracy'])} answered accuracy. On test, it routes {a['answered_count']} queries, defers {a['abstained_count']} ({pct(a['abstention_rate'])}), and achieves {pct(a['answered_accuracy'])} answered accuracy. The would-be error rate among deferred test queries is {pct(a['abstained_would_be_error_rate'])}. These are empirical measurements, not a guarantee on new tickets. Model-output failures remain errors in the denominator and always require review.'''
        test_cell=f"{test['macro_f1']:.4f} / {pct(test['accuracy'])}"
        if sensitivity:
            evaluation+=f" Excluding training-overlap texts and duplicate test texts leaves {sensitivity['n']} queries: macro-F1 {sensitivity['macro_f1']:.4f}, accuracy {pct(sensitivity['accuracy'])}."
    else:
        evaluation='''The preserved 100-query validation pilot has 87 correct predictions, or 87.0% accuracy. Its historical macro-F1 is 0.8611 over the union of observed truth and prediction labels; only 48 of 77 true intents appear. That number cannot establish the all-77-label target. At the provisional 0.70 threshold, 97 queries are routed, three are deferred, and answered accuracy is 88.7%. Two of the three deferred predictions would have been wrong, but 11 wrong routes remain among the 97 accepted cases. This is direct evidence that self-reported confidence misses silent failures. The full 1,998-query validation run and 3,080-query official-test LLM run are not yet complete.'''
        test_cell='pending / pending'
    k=baseline['splits']['test']['keyword']; m=baseline['splits']['test']['majority']
    kp=baseline['splits']['pilot']['keyword']
    budget=read_json(root/'results'/'evaluation_budget.json') or {'budget_usd':'7.00','reserve_usd':'0.05'}
    ledger=AttemptLedger(root/'results'/'api_attempts.jsonl',budget['budget_usd']).summary()
    if ledger['attempts']:
        cost=f"The new-run ledger contains {ledger['attempts']} attempts, with US${ledger['known_cost_usd']} accounted for and {ledger['unknown_cost_attempts']} attempts of unknown cost. Original pilot costs and token counts were not logged, so a complete lifetime project cost cannot be calculated."
    else:
        cost='No new paid calls have been made in this preparation run. The original pilot client did not log token usage, generation IDs or charges, so its actual cost is unknown. The proposal estimated about US$7.75 for validation and test; that was a planning estimate, not measured expenditure.'
    return f'''# TicketRoute

Tu Weikang · PE6201 individual Final Project · Section C

{stage}

## Problem and intended value

Mei, an English-language digital-bank support supervisor, must assign incoming messages to specialist queues. I chose one bounded task: suggest one of 77 BANKING77 intent labels, or require human review. At an assumed 15 seconds per message, 1,000 messages require about 4.2 staff hours of manual triage. This is a planning assumption; I have not measured staff time savings. TicketRoute does not answer customers, access accounts or take financial actions.

## Business and technical choices

I own the browser interface, taxonomy, prompt, validation, review policy and evaluation pipeline, and rent GPT-5 mini through OpenRouter. This avoids training and hosting within the project period, while introducing network latency, recurring cost and provider dependence. A supervised intent model is a credible later alternative because labelled data exists; I have not tested one and cannot claim the rented model is superior. A keyword rule is the implemented non-AI comparator.

Zendesk Intelligent Triage is the commercial alternative identified in my proposal. TicketRoute is a narrow, student-controlled benchmark and review prototype; it does not replace an enterprise support platform. I chose Python's standard library over low-code to make data splits, schema checks and resumable evaluation inspectable. No agent or RAG is needed for a single fixed-label classification. The interface can replay verified historical examples without a key, with a visible replay label.

## Data and evaluation design

BANKING77 supplies 10,003 training and 3,080 official test queries across 77 English banking intents under CC BY 4.0. Source CSV hashes are checked. A fixed, stratified seed-42 split yields 1,998 validation rows; after removing an overlapping training-core row, 8,004 core rows remain. Two examples per intent come only from this core, with no prompt-example overlap with validation or test. The source itself contains six texts shared between train and test, including one in validation, plus within-split duplicates. I preserve the official benchmark and add a sensitivity score on unique test texts absent from all original training data. Both baselines use training-core frequencies.

The model and contrastive-taxonomy-v3 prompt are frozen before completing validation. I predeclare all-77-label macro-F1 of at least 0.80 as the primary target. Validation selects the lowest threshold from 0.50 to 0.95 in 0.05 increments attaining at least 85% accuracy on accepted predictions; if none qualifies, every query requires review. That 85% rule is my project choice, not an instructor requirement or safety guarantee. The official test uses the frozen prompt and validation threshold once, with cached resumption of interrupted work. It is not used to tune the model. The earlier keyword-only test result was already available during development.

## Evidence and limitations

{evaluation}

Comparable official-test scores below use the same fixed 77-label definition. The pilot keyword accuracy is {pct(kp['accuracy'])}; its historical LLM score must not be compared directly with the full-test keyword score.

| Official test method | Macro-F1 / accuracy |
| --- | --- |
| Majority rule | {m['macro_f1']:.4f} / {pct(m['accuracy'])} |
| Keyword overlap | {k['macro_f1']:.4f} / {pct(k['accuracy'])} |
| GPT-5 mini | {test_cell} |

The original 100-row evidence remains unchanged, and the pipeline recovers missing cached rows without buying those predictions again. Row-level outputs, failure counts, confusion pairs, per-intent results and latency summaries make later conclusions inspectable. The model alias may change behind the provider; new responses record the returned model identifier, so exact historical backend equivalence cannot be guaranteed.

## Cost and reliability

{cost} New calls retain provider usage and cost, returned model, request hash and generation ID. A local US${budget['budget_usd']} spending stop and a US${budget['reserve_usd']} reserve per next call limit the run; this is not a provider-enforced account cap. Missing charges stop further paid calls rather than becoming zero. Transport failures stop the run, and completed predictions remain cached. Invalid model outputs count as failures rather than being silently retried until correct.

## Responsible use and conclusion

A confident wrong route is the main silent failure. Implemented controls include fixed labels, structured JSON, input length limits, a shared calibrated review policy and visible explanations. Untrusted query text is explicitly treated as data. A supervisor's random audit of accepted routes remains a proposed operational control, not an automated feature. Real deployment would also need PII masking, access control, drift checks and evaluation on current local tickets; these are not implemented.

Public English benchmark results cannot establish multilingual reliability, staff savings or production readiness. The appropriate next decision depends on the untouched-test evidence and manual-review workload, not on the pilot headline alone. I used AI assistance for implementation, checking and drafting; I remain responsible for reviewing and explaining the submitted work.

## Sources

1. PolyAI BANKING77; pinned source and licence in DATA_LICENSE.md.
2. OpenRouter GPT-5 mini model page and usage-accounting documentation, checked 27 September 2026; links in README.md.
3. Original 23 August 2026 pilot evidence; hashes in results/pilot_provenance.json.
'''


def plain_html(markdown):
    blocks=[]; table=[]
    def flush_table():
        if table:
            rows=[]
            for i,line in enumerate(table):
                if i==1 and '---' in line: continue
                cell='th' if i==0 else 'td'
                rows.append('<tr>'+''.join(f'<{cell}>{html.escape(part.strip())}</{cell}>' for part in line.strip('|').split('|'))+'</tr>')
            blocks.append('<table>'+''.join(rows)+'</table>'); table.clear()
    for block in markdown.strip().split('\n\n'):
        if block.startswith('|'):
            table.extend(block.splitlines()); flush_table()
        elif block.startswith('## '): blocks.append('<h2>'+html.escape(block[3:])+'</h2>')
        elif block.startswith('# '): blocks.append('<h1>'+html.escape(block[2:])+'</h1>')
        else: blocks.append('<p>'+html.escape(block).replace('\n','<br>')+'</p>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>TicketRoute report draft</title><style>body{max-width:820px;margin:45px auto;padding:0 24px;color:#172033;font:16px/1.55 Georgia,serif}h1,h2{font-family:Arial,sans-serif}h2{font-size:20px;margin-top:28px}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #ccc;padding:10px;text-align:left}@media print{body{font-size:11pt;margin:0}h2{break-after:avoid}table{break-inside:avoid}}</style><body>'+''.join(blocks)+'</body></html>'


def export_outputs(root: Path):
    directory=root/'submission'; directory.mkdir(exist_ok=True)
    text=report_text(root)
    (directory/'TicketRoute_Tradeoff_Report_DRAFT.md').write_text(text,encoding='utf-8')
    (directory/'TicketRoute_Tradeoff_Report_DRAFT.html').write_text(plain_html(text),encoding='utf-8')
    count=len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",text))
    (directory/'report_word_count.txt').write_text(f'{count} words including headings, table and sources. Limit: 1200.\n',encoding='utf-8')
    for split in ('validation','test'): analyse_split(root,split)
    zip_path=root/'TicketRoute_Results.zip'
    entries=[]
    # Allow-list only: no environment files, keys, cookies, git metadata or browser state.
    for folder in ('results','evidence','submission'):
        entries.extend(p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in {'.json','.jsonl','.csv','.md','.html','.txt','.png','.pdf'})
    entries=[p for p in entries if p.name!='HAND_BACK_SHA256.txt']
    manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(entries)}
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(entries): archive.write(path,'TicketRoute/'+str(path.relative_to(root)))
        archive.writestr('TicketRoute/HAND_BACK_SHA256.json',json.dumps(manifest,indent=2))
    return zip_path


if __name__=='__main__':
    import sys
    root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root))
    print(export_outputs(root))
