#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "TicketRoute — continue after the cost-check evidence has been reviewed"
if [ ! -f scripts/run_project.py ] || [ ! -f app.py ]; then
  echo "Move this file into your existing TicketRoute folder, next to app.py."
  read -r -p "Press Return to close."
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
  echo "Python 3.10 or newer is needed: https://www.python.org/downloads/macos/"
  read -r -p "Press Return to close."
  exit 1
fi
if ! python3 -m unittest discover -s tests; then
  echo "An offline check failed. Send the error screenshot before proceeding."
  read -r -p "Press Return to close."
  exit 1
fi
echo "The US\$7 program stop includes the saved cost-check spend. It does not reset on resume."
echo "Cached predictions are reused. Keep this folder intact."
python3 scripts/run_project.py --prompt-for-key --budget-usd 7.00
result_code=$?
echo
echo "Send TicketRoute_Results.zip back for review, whether completed or stopped."
read -r -p "Press Return to close."
exit "$result_code"
