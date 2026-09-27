#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "TicketRoute — small cost check for the individual Final Project"
if [ ! -f scripts/run_project.py ] || [ ! -f app.py ]; then
  echo "Move CHECK_COST_MAC.command into your existing TicketRoute folder, next to app.py."
  read -r -p "Press Return to close."
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
  echo "Python 3.10 or newer is needed: https://www.python.org/downloads/macos/"
  read -r -p "Press Return to close."
  exit 1
fi
echo "Checking the project without paid model calls..."
if ! python3 -m unittest discover -s tests; then
  echo "An offline check failed. Send the error screenshot before proceeding."
  read -r -p "Press Return to close."
  exit 1
fi
echo
echo "This small validation batch uses a US\$0.10 program spending stop."
echo "The US\$0.05 request reserve normally stops it earlier. This is not an account-level cap."
echo "Any previously recorded evaluation spend is included; its ledger is not reset."
echo "Enter the course OpenRouter key only at the hidden prompt below."
python3 scripts/run_project.py --prompt-for-key --stage validation --budget-usd 0.10
result_code=$?
echo
echo "For this cost check, STOPPED: Project spending cap reached is an expected checkpoint."
echo "Other errors need review; do not repeatedly rerun the program."
echo "Send TicketRoute_Results.zip from this same folder back to ChatGPT."
echo "Keep the folder and results intact so paid predictions can be reused."
read -r -p "Press Return to close."
exit "$result_code"
