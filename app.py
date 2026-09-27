"""Dependency-free local browser interface for TicketRoute."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import webbrowser
import threading
import hashlib

from ticketroute.baseline import KeywordBaseline
from ticketroute.data import get_labels, load_dataset
from ticketroute.evaluation import keyword_report
from ticketroute.audit import AttemptLedger, EvaluationStopped, append_json
from ticketroute.calibration import read_calibration
from scripts.restore_pilot import restore
from ticketroute.openrouter_client import DEFAULT_MODEL, OpenRouterClient, OpenRouterError
from ticketroute.prompting import (
    PROMPT_VERSION,
    select_benchmark_examples,
    split_train_validation,
)


ROOT = Path(__file__).resolve().parent
TRAIN_ROWS, TEST_ROWS = load_dataset(ROOT / "data")
LABELS = get_labels(TRAIN_ROWS)
TRAIN_CORE_ROWS, _ = split_train_validation(TRAIN_ROWS)
BENCHMARK_EXAMPLES = select_benchmark_examples(TRAIN_CORE_ROWS, LABELS)
BASELINE = KeywordBaseline(TRAIN_CORE_ROWS)
PILOT = restore(ROOT)
LIVE_LOCK = threading.Lock()


CSS = """
:root { color-scheme: light; --ink:#172033; --muted:#667085; --blue:#174ea6;
  --line:#d7deea; --surface:#f6f8fc; --good:#0b6b45; --warn:#9a5b00; }
* { box-sizing:border-box; }
body { margin:0; background:#edf2f8; color:var(--ink); font:16px/1.5 Arial,sans-serif; }
.shell { max-width:920px; margin:36px auto; padding:0 18px 48px; }
.hero,.card { background:white; border:1px solid var(--line); border-radius:16px;
  box-shadow:0 8px 24px rgba(22,34,58,.06); }
.hero { padding:28px 30px; margin-bottom:18px; }
.hero h1 { margin:0 0 4px; color:#173a70; font-size:34px; }
.hero p { margin:0; color:var(--muted); }
.nav { margin-top:18px; display:flex; gap:10px; flex-wrap:wrap; }
.nav a { color:var(--blue); text-decoration:none; font-weight:700; padding:7px 12px;
  border-radius:999px; background:#edf4ff; }
.card { padding:24px 26px; margin-top:18px; }
h2 { margin-top:0; font-size:22px; }
label { display:block; font-weight:700; margin:15px 0 6px; }
textarea,input,select { width:100%; border:1px solid #aeb9ca; border-radius:9px;
  padding:11px 12px; background:white; color:var(--ink); font:inherit; }
textarea { min-height:110px; resize:vertical; }
.row { display:grid; grid-template-columns:1fr 1fr; gap:15px; }
button { margin-top:18px; border:0; border-radius:9px; padding:11px 18px;
  background:var(--blue); color:white; font-weight:700; font-size:16px; cursor:pointer; }
.result { border-left:5px solid var(--good); background:#effaf5; padding:15px 17px;
  border-radius:8px; margin-top:18px; }
.result.warn { border-left-color:var(--warn); background:#fff7e8; }
.result.error { border-left-color:#b42318; background:#fff1f0; }
.metric-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:14px; }
.metric { background:var(--surface); border-radius:10px; padding:14px; }
.metric b { display:block; font-size:25px; color:#173a70; }
code { background:#eef1f6; padding:2px 5px; border-radius:4px; }
table { width:100%; border-collapse:collapse; margin-top:14px; font-size:14px; }
th,td { padding:8px 9px; border-bottom:1px solid var(--line); text-align:left; }
.small { color:var(--muted); font-size:14px; }
@media(max-width:650px){ .row,.metric-grid { grid-template-columns:1fr; } .hero,.card{padding:20px;} }
"""


def page(body: str, title: str = "TicketRoute") -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main class="shell">
<section class="hero"><h1>TicketRoute</h1><p>A human-in-the-loop classifier for English digital-banking support queries</p>
<nav class="nav"><a href="/">Route one query</a><a href="/evidence">Evaluation evidence</a><a href="/baseline">Keyword baseline</a><a href="/scope">Scope & safeguards</a></nav></section>
{body}</main></body></html>"""


def router_form(result_html: str = "", values: dict[str, str] | None = None) -> str:
    values = values or {}
    query = html.escape(values.get("query", PILOT[0]['text']))
    calibration = read_calibration(ROOT)
    choices = [('replay','Replay recorded pilot · no charge'),('keyword','Keyword rule · no AI'),('live','Live GPT-5 mini · one paid call')]
    options = ''.join(f'<option value="{name}"'+(' selected' if values.get('mode','replay')==name else '')+f'>{label}</option>' for name,label in choices)
    key_available = bool(os.getenv("OPENROUTER_API_KEY", "").strip())
    key_note = (
        "A key is already loaded from the launch script."
        if key_available
        else "Enter the course key below. It is used for this request only and is not stored."
    )
    return page(f"""
<section class="card"><h2>Route one customer query</h2>
<p class="small">{html.escape(calibration['description'])} Confidence is a model-reported score, not a calibrated probability.</p>
<form method="post" action="/classify">
<label for="query">Customer query</label><textarea id="query" name="query" maxlength="1000" required>{query}</textarea>
<label for="mode">Run mode</label><select id="mode" name="mode">{options}</select>
<details><summary>API key for live mode only</summary><label for="api_key">OpenRouter API key</label><input id="api_key" name="api_key" type="password" autocomplete="off" placeholder="{html.escape(key_note)}"></details>
<button type="submit">Classify query</button></form>{result_html}
<p>Recorded examples: <a href="/replay?case=correct">clear route</a> · <a href="/replay?case=review">human review</a> · <a href="/replay?case=error">confident error</a></p>
<p class="small">Dataset: {len(TRAIN_ROWS):,} train / {len(TEST_ROWS):,} test / {len(LABELS)} intents. Prompt: {PROMPT_VERSION}. The system routes only; it does not answer or access an account.</p></section>""")


def result_card(row: dict, threshold, source: str, show_truth=False) -> str:
    decision = row['prediction'] if threshold is not None and row['confidence'] >= threshold else 'HUMAN_REVIEW'
    rule = 'all human review' if threshold is None else f'{threshold:.0%}'
    truth = f"<p><b>Recorded true intent:</b> <code>{html.escape(row['truth'])}</code>. Prediction {'correct' if row['truth']==row['prediction'] else 'incorrect'}.</p>" if show_truth else ''
    return f'''<div class="result{' warn' if decision=='HUMAN_REVIEW' else ''}"><p class="small">{html.escape(source)}</p>
<h3>{'Decision: HUMAN_REVIEW' if decision=='HUMAN_REVIEW' else 'Suggested queue: '+html.escape(decision)}</h3>
<p><b>Best intent:</b> <code>{html.escape(row['prediction'])}</code></p>
<div class="metric-grid"><div class="metric"><span>Confidence score</span><b>{row['confidence']:.0%}</b></div><div class="metric"><span>Review threshold</span><b>{rule}</b></div><div class="metric"><span>Original latency</span><b>{row['latency_ms']:,} ms</b></div></div>
<p><b>Reason:</b> {html.escape(row['reason'])}</p>{truth}</div>'''


def evidence_page() -> str:
    pilot = json.loads((ROOT/'evidence'/'pilot_2026-08-23'/'TicketRoute_v3_validation_100_report.json').read_text())
    final_path=ROOT/'results'/'test_full_report.json'
    final=json.loads(final_path.read_text()) if final_path.exists() else None
    final_text=(f"Official test complete: {final['n']:,} queries, macro-F1 {final['macro_f1']:.4f}, accuracy {final['accuracy']:.1%}." if final else 'Full validation and official-test LLM results are pending. The pilot does not establish the final target.')
    a=pilot['abstention']
    return page(f'''<section class="card"><h2>What the evidence shows</h2><p>{final_text}</p>
<h3>Verified pilot · 23 August 2026</h3><p>100 validation queries covering 48 of 77 true intents. These are preserved historical results.</p>
<div class="metric-grid"><div class="metric"><span>Pilot accuracy</span><b>87.0%</b></div><div class="metric"><span>Human review</span><b>3 / 100</b></div><div class="metric"><span>Accepted accuracy</span><b>88.7%</b></div></div>
<p>At threshold 0.70, 2 of the 3 deferred predictions would have been wrong. But 11 wrong predictions still passed the threshold among 97 accepted routes.</p>
<p>The historical macro-F1 of 0.8611 averages over labels observed in this small sample. Final macro-F1 is evaluated across all 77 labels.</p>
<p><b>Measured pilot cost:</b> unknown. The original client did not log billing. The new evaluation records usage and cost and stops on missing billing.</p>
<p><b>Evaluation sequence:</b> freeze model and prompt → complete validation → freeze threshold → official test. Test outcomes do not change the prompt or threshold.</p></section>''','TicketRoute evidence')


def baseline_page() -> str:
    report, _ = keyword_report(TRAIN_CORE_ROWS, TEST_ROWS)
    rows = "".join(
        f"<tr><td>{html.escape(str(item['true']))}</td><td>{html.escape(str(item['predicted']))}</td><td>{item['count']}</td></tr>"
        for item in report["top_confusions"]
    )
    return page(f"""
<section class="card"><h2>Reproducible non-AI baseline</h2>
<p>The rule matches literal query words against words in the 77 intent names. Tie-breaks and fallback use training-core frequencies only. It uses no model and scores all 3,080 official test queries.</p>
<div class="metric-grid"><div class="metric"><span>Macro-F1</span><b>{float(report['macro_f1']):.3f}</b></div>
<div class="metric"><span>Accuracy</span><b>{float(report['accuracy']):.3f}</b></div><div class="metric"><span>Test rows</span><b>{int(report['n']):,}</b></div></div>
<h3>Most frequent confusions</h3><table><thead><tr><th>True intent</th><th>Predicted intent</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table></section>""", "TicketRoute baseline")


def scope_page() -> str:
    return page("""
<section class="card"><h2>Scope and safeguards</h2>
<p><b>Intended use:</b> suggest one BANKING77 routing label for an English, public-style support query.</p>
<p><b>Human control:</b> low-confidence cases require manual review. Random auditing of accepted routes is a proposed supervisor procedure, not an automated feature.</p>
<p><b>Explicit non-use:</b> no answer generation, account access, financial decision, automatic customer action, or production deployment.</p>
<p><b>Silent failure:</b> a confident wrong route. Controls include a fixed label whitelist, strict JSON, a confidence threshold, test logging, and human review.</p>
<p><b>Data boundary:</b> the prototype uses only the public BANKING77 text and labels. Real deployment would need PII masking, access control, drift monitoring, and new local evaluation.</p></section>""", "TicketRoute safeguards")


class TicketRouteHandler(BaseHTTPRequestHandler):
    def _send(self, content: str, status: int = 200) -> None:
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send(router_form())
        elif path == "/baseline":
            self._send(baseline_page())
        elif path == "/scope":
            self._send(scope_page())
        elif path == '/evidence':
            self._send(evidence_page())
        elif path == '/replay':
            case=parse_qs(urlparse(self.path).query).get('case',['correct'])[0]
            selected=next((r for r in PILOT if (r['confidence']<.70 if case=='review' else r['confidence']>=.70 and (r['truth']!=r['prediction'] if case=='error' else r['truth']==r['prediction']))),PILOT[0])
            result=result_card(selected,.70,'RECORDED PILOT REPLAY · original 0.70 rule · no new model call',True)
            self._send(router_form(result,{'query':selected['text'],'mode':'replay'}))
        elif path == "/health":
            body = json.dumps({"status": "ok", "labels": len(LABELS)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send(page("<section class='card'><h2>Not found</h2></section>"), 404)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/classify":
            self._send(page("<section class='card'><h2>Not found</h2></section>"), 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 20000:
                raise ValueError("Request is too large or empty")
            fields = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            values = {key: items[0] for key, items in fields.items()}
        except (ValueError, UnicodeError):
            self._send(page("<p>Invalid request.</p>"), 400)
            return
        api_key = values.pop("api_key", "").strip() or os.getenv("OPENROUTER_API_KEY", "").strip()
        query = values.get("query", "").strip()
        mode = values.get("mode", "replay")
        try:
            if not query or len(query)>1000:
                raise ValueError("Enter between 1 and 1,000 characters")
            if mode == "replay":
                row = next((r for r in PILOT if r['text']==query),None)
                if row is None:
                    raise ValueError("This text is not in the recorded pilot. Choose a recorded example below, keyword mode, or live mode.")
                result=result_card(row,.70,"RECORDED PILOT REPLAY · original 0.70 rule · no new model call",True)
            elif mode == "keyword":
                intent=BASELINE.predict(query)
                result=f"<div class='result'><h3>Keyword suggestion: {html.escape(intent)}</h3><p>Literal word matching; no model confidence and no API charge.</p></div>"
            elif mode == "live":
                if not api_key:
                    raise ValueError("Enter the course API key under 'API key for live mode only'. It is not saved.")
                if not LIVE_LOCK.acquire(blocking=False):
                    raise ValueError("A live request is already running. Wait for it to finish.")
                try:
                    ledger=AttemptLedger(ROOT/'results'/'demo_attempts.jsonl',budget_usd='1.00')
                    ledger.before_call()
                    calibration=read_calibration(ROOT)
                    try:
                        prediction=OpenRouterClient(api_key,model=DEFAULT_MODEL).classify(query,LABELS,BENCHMARK_EXAMPLES)
                    except OpenRouterError as exc:
                        ledger.record({'outcome':exc.category,'model':DEFAULT_MODEL,**exc.metadata})
                        raise
                    ledger.record({'outcome':'ok','model':prediction.model,'usage':prediction.usage,'generation_id':prediction.generation_id,'returned_model':prediction.returned_model})
                    if prediction.usage is None:
                        raise EvaluationStopped("The provider did not supply valid billing. Stop live calls and inspect the ledger.")
                    row={'prediction':prediction.intent,'confidence':prediction.confidence,'latency_ms':prediction.latency_ms,'reason':prediction.reason}
                    result=result_card(row,calibration['threshold'],'LIVE MODEL RESULT · one new call · '+calibration['description'])
                    result+=f"<p class='small'>Recorded API charge: US${html.escape(prediction.usage['cost_usd'])}</p>"
                finally:
                    LIVE_LOCK.release()
            else:
                raise ValueError("Unknown run mode")
        except (ValueError,OpenRouterError,EvaluationStopped) as exc:
            result=f"<div class='result error'><h3>Human review required</h3><p>{html.escape(str(exc))}</p></div>"
        self._send(router_form(result,values))

    def log_message(self, format: str, *args: object) -> None:
        print(f"TicketRoute: {format % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), TicketRouteHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"TicketRoute is running at {url}")
    print("Press Control-C in this window to stop it.")
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping TicketRoute.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
