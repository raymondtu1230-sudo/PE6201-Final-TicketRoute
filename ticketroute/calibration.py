"""The CLI and browser share the same frozen validation decision rule."""
from __future__ import annotations
import json
import math
from pathlib import Path
from .audit import EvaluationStopped
from .openrouter_client import DEFAULT_MODEL
from .prompting import PROMPT_VERSION


def read_calibration(root: Path, *, required: bool = False) -> dict:
    path = root / 'results' / 'calibrated_threshold.json'
    if not path.exists():
        if required:
            raise EvaluationStopped('Full validation calibration is required before final test evaluation.')
        return {'threshold': 0.70, 'state': 'pilot', 'description': 'Pilot threshold 0.70. Full validation calibration is pending.'}
    try:
        saved = json.loads(path.read_text(encoding='utf-8'))
        lock = json.loads((root / 'results' / 'evaluation_lock.json').read_text(encoding='utf-8'))
        if saved['model'] != DEFAULT_MODEL or saved['prompt_version'] != PROMPT_VERSION or saved['validation_rows'] != 1998:
            raise ValueError('Wrong experiment or incomplete validation')
        if saved['configuration_sha256'] != lock['configuration_sha256']:
            raise ValueError('Configuration lock mismatch')
        threshold = saved['threshold']
        if threshold is not None and (isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not .50 <= threshold <= .95):
            raise ValueError('Invalid threshold')
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise EvaluationStopped('Saved calibration is inconsistent. Preserve results for review.') from exc
    saved['state'] = 'calibrated'
    saved['description'] = ('Full validation did not meet the routing accuracy target; all queries require human review.' if threshold is None else f'Frozen threshold {threshold:.2f}, selected on all 1,998 validation queries.')
    return saved
