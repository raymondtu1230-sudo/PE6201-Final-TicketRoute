#!/bin/bash
cd "$(dirname "$0")" || exit 1
python3 scripts/run_project.py --offline
echo "The historical 100-row pilot has been restored. No paid call is needed."
read -r -p "Press Return to close."
