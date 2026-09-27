# TicketRoute cost probe — reviewed 27 September 2026

The user's local Mac run returned 94 successful new API responses and preserved
the original 100 pilot predictions, for 194 cached validation rows. These rows
match the first 194 validation rows and pass the existing schema and label
checks. All 25 handback file hashes verify. Every new ledger entry reconciles
with its saved prediction and usage metadata. No missing charges or output
format failures were found. Successful API responses are not perfect accuracy:
80 of the 94 new predictions match their labels.

Actual recorded cost is US$0.05027785. With the US$0.05 request reserve, the next
request is correctly blocked by the US$0.10 probe stop. Reopening the same ledger
under US$7 passes its continuation check without clearing prior charges.

At the observed mean cost, the remaining 4,882 unique calls are estimated at
US$2.61, or US$2.66 including this probe. The last-25 and last-50-call averages
imply US$2.43 and US$2.40 remaining. These are scenarios, not confidence intervals.
91/94 calls had cached input tokens; 94.99% of input tokens were cached. Future
cache availability, output length and routing may change costs. The reported
approximately US$8 account balance was not independently verified.

Mean latency was 2.19 seconds per new call, implying about three more hours.
The user should continue in the same local folder with START_HERE_MAC.command
option 2, retain the cumulative US$7 program stop, keep the Mac powered and
awake, and return the refreshed TicketRoute_Results.zip on completion or any
unexpected stop. No new project download or runtime changes are needed.

The original upload is retained as libfile_d77ad6a386d88191bdbc51278b7cd20f.
Its SHA-256 is
268fea5300a09817ed13a59084abe736ca215a0616a64c58e8a79461e73f1d35.
Detailed review figures are in cost_probe_2026-09-27.json. Remaining cost is
calculated as (sum of 94 recorded charges / 94) * (4976 - 94). Remaining hours
are calculated as mean request latency in seconds * 4882 / 3600.

This is the independent individual Final Project. Insurance AR/A2 is excluded.
Full validation, frozen-threshold official test, final report and recorded demo
remain pending. No model API calls were made during this review.
