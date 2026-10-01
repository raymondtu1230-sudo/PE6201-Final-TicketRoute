"""Check that offline preparation preserves completed evaluation evidence.

The real CLI and independent audit run against a temporary copy of the bundled
results. No model calls are made, and the original project is left untouched.
"""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OfflinePreservationTests(unittest.TestCase):
    def test_offline_check_preserves_completed_evidence_and_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory)
            for folder in ('data', 'evidence', 'results', 'scripts', 'ticketroute', 'analysis', 'submission'):
                shutil.copytree(ROOT / folder, copied / folder,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            status_path = copied / 'results' / 'run_status.json'
            self.assertEqual(json.loads(status_path.read_text())['state'], 'evaluation_complete')
            original_status = status_path.read_bytes()
            evidence = {
                path.relative_to(copied): hashlib.sha256(path.read_bytes()).hexdigest()
                for folder in ('data', 'evidence', 'results')
                for path in (copied / folder).rglob('*') if path.is_file()
            }
            checked = subprocess.run(
                [sys.executable, 'scripts/run_project.py', '--offline'],
                cwd=copied, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(status_path.read_bytes(), original_status)
            for relative, digest in evidence.items():
                self.assertEqual(hashlib.sha256((copied / relative).read_bytes()).hexdigest(),
                                 digest, str(relative))
            audited = subprocess.run(
                [sys.executable, 'analysis/review_final_results.py', 'TicketRoute_Results.zip'],
                cwd=copied, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
            summary = json.loads(audited.stdout)
            self.assertEqual(summary['network_calls_during_audit'], 0)
            self.assertEqual(summary['new_attempts'], 4976)
            self.assertEqual(summary['metrics']['test']['correct'], 2625)


if __name__ == '__main__':
    unittest.main()
