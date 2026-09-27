#!/bin/bash
cd "$(dirname "$0")" || exit 1
python3 -m unittest discover -s tests && python3 scripts/run_project.py --offline
read -r -p "Press Return to close."
