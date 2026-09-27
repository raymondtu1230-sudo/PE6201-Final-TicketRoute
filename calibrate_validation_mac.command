#!/bin/bash
cd "$(dirname "$0")" || exit 1
python3 scripts/run_project.py --stage validation --prompt-for-key
read -r -p "Press Return to close."
