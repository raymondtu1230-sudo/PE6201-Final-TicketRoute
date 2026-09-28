#!/usr/bin/env python3
"""Export per-intent scores, error tables and an archive of evaluation evidence."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import zipfile


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


def export_outputs(root: Path):
    directory=root/'submission'; directory.mkdir(exist_ok=True)
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
