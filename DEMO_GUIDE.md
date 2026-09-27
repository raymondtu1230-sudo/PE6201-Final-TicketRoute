# TicketRoute individual Final Project demo

This script belongs only to TicketRoute, not the insurance AR/A2 project.
Suggested duration: about four minutes, a planning choice rather than a located
course rule. Do not call a recorded replay a new live model call.

## Before recording

1. Finish full evaluation and review the actual final results. Until then, this
   is a pilot demonstration, not the final presentation.
2. Run `START_HERE_MAC.command` and choose `3`. Use a clean browser window; hide keys, terminal
   secrets, notifications and unrelated coursework.
3. Have the final report and independent GitHub URL ready. The evaluation page
   automatically shows saved official-test metrics when present.
4. For a genuinely live example, select Live mode and enter the key under its
   collapsed field **before recording** or launch with an environment key.
   Avoid opening that section on the recording. A live call is optional backup
   to the recorded evidence unless the teacher's final portal requires it.

## Narration and actions

| Time | Screen action | Suggested narration |
| --- | --- | --- |
| 0:00–0:35 | Show TicketRoute home page | “My individual Final Project is TicketRoute. Mei, a bank-support supervisor, needs to route English customer questions to the right team. I focus on one bounded task: one of 77 intents, or human review. Fifteen seconds per message is a planning assumption, not a measured saving.” |
| 0:35–1:10 | Select Keyword mode and classify the sample | “This is the transparent non-AI baseline. It matches words against intent names. I own the interface, fixed prompt, validation and evaluation code, while renting GPT-5 mini. I chose Python for reproducibility; this task needs neither an agent nor RAG.” |
| 1:10–1:45 | Click clear route, then human review | “These are explicitly labelled replays of real August pilot calls, not new responses. A valid intent is proposed when the operating threshold is met. Otherwise the supervisor receives HUMAN_REVIEW. The final live mode reads the rule frozen on full validation.” |
| 1:45–2:20 | Click confident error | “This real example shows the main silent failure: a high-confidence misroute. The original 100-row pilot still had 11 wrong predictions among 97 accepted routes. Confidence alone is not enough; operational spot checks would be necessary.” |
| 2:20–3:10 | Open Evaluation evidence and final report | “The model and prompt were frozen before full validation. The threshold was selected there and then frozen before the official test. Here are the actual macro-F1, accuracy, coverage, deferred error rate, latency and recorded cost. The original pilot cost is unknown. Source duplicates are disclosed, with a separate stricter test score.” Only say the first two sentences in past tense after the full run has actually completed. |
| 3:10–3:45 | Show Scope & safeguards | “This does not answer customers, access accounts or take financial actions. JSON checks, fixed labels and human review are implemented. PII masking, drift monitoring and production access controls are future work. Public benchmark accuracy does not establish real staff savings or production readiness.” |
| 3:45–4:00 | Show independent GitHub README | “The repository contains the code, public data, original evidence, offline checks and reproduction commands. The final target is 0.80 macro-F1. I report whether the untouched test meets it, without changing the prompt after seeing the result.” |

If full evaluation is pending, explicitly replace the results paragraph with:
“Only the 100-query validation pilot is complete. The final target and official
test outcome are not yet established.” Do not hide that limitation with a pilot
score or a screenshot labelled as final.

## Mac recording steps

1. Press Shift + Command + 5.
2. Choose “Record Selected Portion”; select only the browser and report area.
3. Under Options choose your microphone if narrating, and Desktop as save location.
4. Click Record. Follow the table; speak slowly and leave time for results to load.
5. Stop from the menu-bar stop button. Rename the file
   `TicketRoute_Final_Project_Demo.mov` after final evidence is ready.
6. Play the file once: check readable text, audible voice, no visible credentials,
   and that replay versus live is accurately described. Upload the video through
   the course's Final Project submission route, not the AR/A2 route.

## Questions to be ready to explain

- Why macro-F1? Each of 77 queues matters; frequent classes should not dominate.
- Why not train a model? Feasible future alternative; the prototype prioritises
  a small reproducible slice, not a claim that rented LLMs are always better.
- How is the threshold selected? Lowest predeclared candidate meeting 85%
  validation answered accuracy, otherwise all review; never chosen on the test.
- What did the pilot prove? End-to-end feasibility and concrete failure patterns,
  not full coverage, actual staff savings or production safety.
- What is measured cost? New provider charges are logged; historical charges are
  unknown, and proposal estimates are not substituted for actual measurements.
