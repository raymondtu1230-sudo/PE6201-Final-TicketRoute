#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "TicketRoute — PE6201 individual Final Project"
echo "This folder is separate from the insurance-claims AR/A2 assignment."
echo
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
  echo "Python 3.10 or newer is needed. Install Python 3 from https://www.python.org/downloads/macos/"
  echo "Then open this same file again. No other packages are needed."
  read -r -p "Press Return to close."
  exit 1
fi
echo "Checking the project before any paid call..."
if ! python3 -m unittest discover -s tests; then
  echo "A check failed. Take a screenshot of this window and send it back."
  read -r -p "Press Return to close."
  exit 1
fi
echo
echo "The next step uses the course OpenRouter API key. Input is hidden and not saved."
echo "The program resumes 100 old results, completes validation, freezes its rule, then runs the test."
echo "New evaluation has a local US\$12 spending stop. Provider account limits are separate."
echo "Keep this window open and the Mac awake. This may take several hours."
python3 scripts/run_project.py --prompt-for-key
result_code=$?
echo
if [ "$result_code" -eq 0 ]; then
  echo "Finished. Send TicketRoute_Results.zip from this folder back to ChatGPT."
else
  echo "The run stopped and saved its evidence. Send TicketRoute_Results.zip back to ChatGPT."
  echo "Do not delete the results folder or change the prompt to fix a score."
fi
read -r -p "Press Return to close."
