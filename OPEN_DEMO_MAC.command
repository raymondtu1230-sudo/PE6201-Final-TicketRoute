#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "Opening TicketRoute. Recorded replay and keyword mode need no API key."
echo "Live mode costs one model call and requires a key entered in the browser."
python3 app.py --open-browser
read -r -p "Press Return to close."
