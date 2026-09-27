# TicketRoute requirement check

Checked 27 September 2026 against the Final Project proposal watchouts,
assessment timeline and later Class 6 C3 slides. Insurance AR/A2 requirements
are not used for this check.

| Final Project requirement | Evidence or action | Status |
| --- | --- | --- |
| One bounded problem and named user | Mei; English banking intent routing; no account or financial actions | Implemented/documented |
| Explain significance with numbers | 15 seconds per message and 4.2 hours per 1,000 explicitly labelled assumptions | Drafted; not measured savings |
| Closest alternative and project gap | Zendesk named in the submitted proposal; narrower controlled benchmark | Drafted |
| Build/buy and technical trade-offs | Python-owned pipeline; rented model; supervised model and low-code alternatives discussed | Drafted |
| Named data, access and licence | BANKING77, CC BY 4.0, pinned source hashes, supplied CSVs | Verified |
| Real baseline | Keyword and majority rules on the same splits using training-core counts | Completed offline |
| Primary metric and target | Fixed-77-label macro-F1 ≥ 0.80; target set in proposal | Full-test outcome pending |
| Full validation/calibration | 1,998 rows; predeclared threshold rule; safe all-review fallback | Runner ready; API key required |
| Official final evaluation | 3,080 rows after frozen prompt and threshold | Runner ready; API key required |
| Abstention and would-be error | Preserved pilot 3% abstention and 2/3 would-be errors; full reports automated | Pilot complete; full pending |
| Duplicate-data limitations | 6 train/test text overlaps, 1 validation/test; extra strict test sensitivity score | Detected/disclosed; full score pending |
| Responsible use and silent failures | Fixed schema, input checks, human review; confident errors shown honestly | Implemented; operational audit remains proposed |
| Cost and latency | New usage/charge/ID ledger; old actual cost unknown; cached resume | Implemented; new measurements pending |
| Runs on another person's machine | Watchouts p.3 final check 4; bundled data, Python 3.10+, documented local startup | Local scripts checked; user-machine execution pending |
| Working GitHub repository | Private repository created: https://github.com/raymondtu1230-sudo/PE6201-Final-TicketRoute | 69 source/evidence files uploaded; instructor access still requires checking |
| Trade-off report ≤ 1,200 words | Evidence-backed draft plus automatic word count | Draft only until final results |
| Recorded demo | Working replay/keyword UI and complete script | Recording pending |
| Proposal milestone | 23 August submission recorded in preserved checkpoint | User's earlier submission record; receipt not reverified |
| Instructor feedback | Not found in available Final Project materials | Not assumed or invented |

Rubric emphasis from proposal watchouts: problem/significance 15%; business and
technical trade-offs 25%; implementation/data/evaluation 35%; demo/communication
25%. No fixed video duration or required video filename was located in these
Final Project materials. The suggested four-minute walkthrough is a planning
choice, not an imported AR/A2 rule.

Submission is **not yet complete**. The preparation work is ready for the paid
evaluation, followed by final report, independent GitHub publication and demo.

## Runtime requirement clarification — 27 September 2026

Watchouts p.3 explicitly says: "Your repository will run on someone else's machine."
The available Final Project documents do not require every evaluation to be
performed personally on the student's local computer. The user has nevertheless
chosen local execution. START_HERE_CN.md gives Mac and Windows steps, hidden
key entry, progress interpretation, error handling and the results ZIP handoff.
No cloud evaluation workflow has been published or started. The standalone
Project Rubric and personal instructor feedback remain unavailable; do not
claim that unseen requirements have been verified.
