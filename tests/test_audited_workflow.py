import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.restore_pilot import restore, cache_path
from ticketroute.audit import AttemptLedger, EvaluationStopped
from ticketroute.calibration import read_calibration
from ticketroute.evaluation import evaluate_llm_rows
from ticketroute.metrics import choose_threshold, abstention_metrics, classification_metrics
from ticketroute.openrouter_client import ModelPrediction, OpenRouterError, normalise_usage, OpenRouterClient
from ticketroute.prompting import PROMPT_VERSION
from ticketroute.taxonomy import INTENT_GUIDE

ROOT=Path(__file__).resolve().parents[1]
USAGE={'prompt_tokens':10,'completion_tokens':2,'total_tokens':12,'cost_usd':'0.003'}
ROW={'text':'sample','category':'a'}


class AuditedWorkflowTests(unittest.TestCase):
    def test_no_qualifying_threshold_means_all_human_review(self):
        threshold=choose_threshold(['a'],['b'],[.99])
        self.assertIsNone(threshold)
        result=abstention_metrics(['a'],['b'],[.99],threshold)
        self.assertEqual(result['answered_count'],0)
        self.assertEqual(result['abstained_would_be_error_rate'],1)
        self.assertEqual(ModelPrediction('b',.99,'reason','m',1).decision(threshold),'HUMAN_REVIEW')

    def test_fixed_label_macro_includes_unobserved_intents(self):
        self.assertEqual(classification_metrics(['a'],['a'],['a','b'])['macro_f1'],.5)
        self.assertEqual(classification_metrics(['a'],['__MODEL_FAILURE__'],['a','b'])['macro_f1'],0)

    def test_missing_or_invalid_billing_is_not_free(self):
        self.assertIsNone(normalise_usage(None))
        raw={'prompt_tokens':10,'completion_tokens':2,'total_tokens':12,'cost':.003}
        self.assertEqual(normalise_usage(raw)['cost_usd'],'0.003')
        for bad in (float('nan'),float('inf'),-1,True,'bad'):
            self.assertIsNone(normalise_usage({**raw,'cost':bad}))
        self.assertIsNone(normalise_usage({**raw,'prompt_tokens':True}))
        self.assertIsNone(normalise_usage({**raw,'total_tokens':99}))

    def test_budget_uses_decimal_and_blocks_unknown_charge(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=AttemptLedger(Path(d)/'ledger.jsonl',budget_usd='.053',reserve_usd='.05')
            ledger.record({'usage':USAGE})
            ledger.before_call()  # exactly .003 + .050, not a floating-point overflow
            ledger.record({'usage':None})
            with self.assertRaises(EvaluationStopped): ledger.before_call()
            self.assertEqual(ledger.summary()['unknown_cost_attempts'],1)

    def test_spending_stop_before_next_call(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=AttemptLedger(Path(d)/'ledger.jsonl',budget_usd='.051')
            ledger.record({'usage':USAGE})
            with self.assertRaises(EvaluationStopped): ledger.before_call()

    def test_model_failure_counts_and_is_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.jsonl'; ledger=AttemptLedger(Path(d)/'ledger.jsonl')
            def fail(text): raise OpenRouterError('Malformed output','model_output',{'usage':USAGE,'generation_id':'gen-1'})
            report,rows=evaluate_llm_rows([ROW],fail,path,'v',.7,labels=['a'],model='m',ledger=ledger)
            self.assertEqual(report['accuracy'],0)
            self.assertEqual(report['model_output_failures'],1)
            self.assertEqual(report['abstention']['abstained_count'],1)
            def must_not_call(text): self.fail('Failure was silently retried')
            again,_=evaluate_llm_rows([ROW],must_not_call,path,'v',.7,labels=['a'],model='m',ledger=ledger)
            self.assertEqual(again['n'],1)
            self.assertEqual(ledger.summary()['attempts'],1)

    def test_transport_failure_stops_without_inventing_a_prediction(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.jsonl'; ledger=AttemptLedger(Path(d)/'ledger.jsonl')
            def fail(text): raise OpenRouterError('HTTP 429','transport')
            with self.assertRaises(EvaluationStopped):
                evaluate_llm_rows([ROW],fail,path,'v',.7,labels=['a'],model='m',ledger=ledger)
            self.assertFalse(path.exists())
            self.assertEqual(ledger.summary()['unknown_cost_attempts'],1)

    def test_success_with_missing_usage_is_saved_but_stops_next_call(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.jsonl'; ledger=AttemptLedger(Path(d)/'ledger.jsonl')
            with self.assertRaises(EvaluationStopped):
                evaluate_llm_rows([ROW],lambda _:ModelPrediction('a',.9,'r','m',1),path,'v',.7,labels=['a'],model='m',ledger=ledger)
            self.assertEqual(len(path.read_text().splitlines()),1)
            with self.assertRaises(EvaluationStopped): ledger.before_call()

    def test_cache_from_another_model_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.jsonl'
            path.write_text(json.dumps({'text':'sample','truth':'a','prediction':'a','confidence':.9,'model':'wrong','prompt_version':'v'})+'\n')
            with self.assertRaises(EvaluationStopped):
                evaluate_llm_rows([ROW],lambda _:None,path,'v',.7,labels=['a'],model='m')

    def test_restore_100_real_rows_is_idempotent_and_requires_zero_calls(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            shutil.copytree(ROOT/'data',root/'data')
            shutil.copytree(ROOT/'evidence',root/'evidence')
            first=restore(root); path=cache_path(root,'validation'); before=path.read_bytes()
            second=restore(root)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(len(first),100)
            self.assertEqual(first,second)
            def must_not_call(_): self.fail('Restored pilot should not be purchased again')
            report,_=evaluate_llm_rows([{'text':r['text'],'category':r['truth']} for r in first],must_not_call,path,PROMPT_VERSION,.7)
            self.assertEqual(report['accuracy'],.87)
            self.assertAlmostEqual(report['macro_f1'],.861095238095238)

    def test_shared_calibration_supports_all_review_and_checks_lock(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'results').mkdir()
            (root/'results'/'evaluation_lock.json').write_text(json.dumps({'configuration_sha256':'abc'}))
            path=root/'results'/'calibrated_threshold.json'
            saved={'model':'openai/gpt-5-mini','prompt_version':PROMPT_VERSION,'validation_rows':1998,'configuration_sha256':'abc','threshold':None}
            path.write_text(json.dumps(saved))
            self.assertIsNone(read_calibration(root,required=True)['threshold'])
            path.write_text(json.dumps({**saved,'configuration_sha256':'wrong'}))
            with self.assertRaises(EvaluationStopped): read_calibration(root,required=True)

    @patch('ticketroute.openrouter_client.urlopen')
    def test_real_response_metadata_is_retained(self,mocked):
        labels=list(INTENT_GUIDE)
        examples=[(label,f'example {i} for {label}') for label in labels for i in (1,2)]
        response={'id':'gen-audit','model':'openai/gpt-5-mini','usage':{'prompt_tokens':10,'completion_tokens':2,'total_tokens':12,'cost':.003},'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'intent':labels[0],'confidence':.9,'reason':'Clear channel.'})}}]}
        mocked.return_value.__enter__.return_value.read.return_value=json.dumps(response).encode()
        prediction=OpenRouterClient('dummy-test-key').classify('query',labels,examples)
        self.assertEqual(prediction.generation_id,'gen-audit')
        self.assertEqual(prediction.usage,USAGE)
        self.assertEqual(len(prediction.request_hash),64)
        response['choices'][0]['message']['content']='incomplete'
        mocked.return_value.__enter__.return_value.read.return_value=json.dumps(response).encode()
        with self.assertRaises(OpenRouterError) as context:
            OpenRouterClient('dummy-test-key').classify('query',labels,examples)
        self.assertEqual(context.exception.metadata['usage'],USAGE)
        self.assertEqual(context.exception.category,'model_output')

    def test_entire_frozen_workflow_and_zero_call_resume_with_synthetic_client(self):
        # Synthetic outputs verify plumbing only, isolated from deliverable evidence.
        import contextlib
        import io
        from scripts.run_project import run_paid
        from ticketroute.data import load_dataset
        from scripts.finalise_outputs import export_outputs
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            shutil.copytree(ROOT/'data',root/'data')
            shutil.copytree(ROOT/'evidence',root/'evidence')
            train,test=load_dataset(root/'data')
            truth={r['text']:r['category'] for r in train+test}
            calls=[]
            class SyntheticClient:
                def __init__(self,key): pass
                def classify(self,text,labels,examples):
                    calls.append(text)
                    return ModelPrediction(truth[text],.90,'Synthetic unit-test fixture','openai/gpt-5-mini',1,
                        usage={**USAGE,'cost_usd':'0.0001'},generation_id=f'synthetic-{len(calls)}')
            with patch('scripts.run_project.OpenRouterClient',SyntheticClient),contextlib.redirect_stdout(io.StringIO()):
                run_paid(root,'dummy-test-key','12.00')
                first_count=len(calls)
                self.assertEqual(first_count,4976)
                threshold=(root/'results'/'calibrated_threshold.json').read_bytes()
                test_lock=(root/'results'/'test_lock.json').read_bytes()
                run_paid(root,'dummy-test-key','12.00')
            self.assertEqual(len(calls),first_count)
            self.assertEqual((root/'results'/'calibrated_threshold.json').read_bytes(),threshold)
            self.assertEqual((root/'results'/'test_lock.json').read_bytes(),test_lock)
            report=json.loads((root/'results'/'test_full_report.json').read_text())
            strict=json.loads((root/'results'/'test_sensitivity_report.json').read_text())
            self.assertEqual(report['n'],3080)
            self.assertEqual(strict['n'],3073)
            self.assertTrue(export_outputs(root).exists())


if __name__=='__main__': unittest.main()
