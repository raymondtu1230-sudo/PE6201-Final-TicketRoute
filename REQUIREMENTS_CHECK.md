# TicketRoute requirement check

Updated 28 September 2026 against the Final Project proposal watchouts,
assessment timeline and later Class 6 C3 slides. Insurance AR/A2 requirements
are not used for this check.

| Final Project requirement | Evidence or action | Status |
| --- | --- | --- |
| One bounded problem and named user | Mei; English banking intent routing; no account or financial actions | Implemented/documented |
| Explain significance with numbers | 15 seconds per message and 4.2 hours per 1,000 explicitly labelled assumptions | Reported as assumptions, not measured savings |
| Closest alternative and project gap | Zendesk named in the submitted proposal; narrower controlled benchmark | Explained in final report |
| Build/buy and technical trade-offs | Python-owned pipeline; rented model; supervised model and low-code alternatives discussed | Explained in final report |
| Named data, access and licence | BANKING77, CC BY 4.0, pinned source hashes, supplied CSVs | Verified |
| Real baseline | Keyword and majority rules on the same splits using training-core counts | Completed offline |
| Primary metric and target | Official test macro-F1 0.8489 over 77 labels, target ≥ 0.80 | Met |
| Full validation/calibration | 1,998 rows; predeclared rule selected threshold 0.60 | Completed and independently checked |
| Official final evaluation | 3,080 rows; accuracy 85.23%, frozen prompt and threshold | Completed and independently checked |
| Abstention and would-be error | Test: 31 deferred, 19 would-be errors; 436 errors still accepted | Reported with limitations |
| Duplicate-data limitations | Strict subset n=3,073, macro-F1 0.8490 | Detected, disclosed and independently checked |
| Responsible use and silent failures | Fixed schema, input checks, human review; confident errors shown honestly | Implemented; operational audit remains proposed |
| Cost and latency | 4,976 new calls, US$2.381836, median test latency 2.19 s; old cost unknown | Measured and reconciled |
| Runs on another person's machine | Full workflow ran on the student's Mac; bundled data and Python 3.10+ | Demonstrated locally; instructor access remains to check |
| Working GitHub repository | Independent private repository: https://github.com/raymondtu1230-sudo/PE6201-Final-TicketRoute | Complete source and evidence in this repository; instructor access still needs confirmation |
| Trade-off report ≤ 1,200 words | Final report has 1,024 words including title, table and sources | Completed; student review still needed |
| Recorded demo | Existing replay/keyword UI and final-results narration | Assembled from original recordings and voice; final student playback pending |
| Proposal milestone | 23 August submission recorded in preserved checkpoint | User's earlier submission record; receipt not reverified |
| Instructor feedback | Not found in available Final Project materials | Not assumed or invented |

Rubric emphasis from proposal watchouts: problem/significance 15%; business and
technical trade-offs 25%; implementation/data/evaluation 35%; demo/communication
25%. No fixed video duration or required video filename was located in these
Final Project materials. The approximately 3 minute 21 second recording is the prepared demo,
not a duration requirement imported from AR/A2.

Submission is **not yet complete**. Evaluation and the report are complete.
The recorded demo is assembled. Final student playback, instructor access
and school-portal submission remain.

## Runtime requirement clarification — 27 September 2026

Watchouts p.3 explicitly says: "Your repository will run on someone else's machine."
The available Final Project documents do not require every evaluation to be
performed personally on the student's local computer. The user has nevertheless
chosen local execution. START_HERE_CN.md gives Mac and Windows steps, hidden
key entry, progress interpretation, error handling and the results ZIP handoff.
No cloud evaluation workflow has been published or started. The standalone
Project Rubric and personal instructor feedback remain unavailable; do not
claim that unseen requirements have been verified.
