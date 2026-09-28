# TicketRoute final demo guide

This is the PE6201 individual Final Project. Suggested duration is about four minutes. No fixed video length was located in the available Final Project materials. Use the student's existing completed project folder.

## Preparation

Open `START_HERE_MAC.command` and enter `3`, even if the older local prompt still says to enter 1 for the first run. Open `http://127.0.0.1:8765` if the browser does not launch automatically. Keep the terminal open. Replay and keyword modes make no paid calls. Have the final report and independent GitHub README open in separate tabs. Do not expose the API key field.

## 1 Introduce the project

Screen: Route one query page, with the project title visible.

“My individual Final Project is TicketRoute. It helps a bank support supervisor suggest a queue for an English customer message. The scope is one of 77 banking intents, or human review. It does not answer customers or access their accounts. At an assumed fifteen seconds per message, manually sorting a thousand messages takes about four hours. This is a planning assumption. I have not measured actual staff savings.”

## 2 Show the baseline and real saved examples

Screen: Select `Keyword rule · no AI` under Run mode, then click `Classify query`. Next click the `clear route`, `human review` and `confident error` links, allowing time to read each result.

“The keyword mode is a simple comparator using words in intent names. For the model, I built the interface and evaluation code, and rented GPT-5 mini through OpenRouter. A fixed classification task does not need an agent or retrieval system.

“These three examples replay real calls from the earlier pilot. They are saved responses, not fresh model calls. The replay reproduces the original threshold of 0.70. The first example is a correct route, the next requires review, and the third demonstrates a confident error. Confidence can help flag ambiguity, but a high score does not guarantee a correct answer.”

## 3 Explain the full evaluation

Screen: Open `Evaluation evidence`, then the final report's Results and error analysis section. The page's large pilot figures are historical. Use the official-test sentence and final-report table for final scores.

“The complete evaluation uses 1,998 validation queries followed by 3,080 official test queries. Validation selected the final threshold of 0.60. I froze that rule before the official test and did not tune it using test errors.

“The final macro-F1 is 0.8489, meeting the proposed target of 0.80. Accuracy is 85.23 percent, compared with 38.08 percent for the keyword baseline. A stricter test subset excluding repeated texts and training overlaps gives almost the same result.

“The review rule defers 31 queries. Nineteen would have been wrong, but 436 errors still pass the threshold. This limits the case for autonomous routing. The largest confusion is between unrecognised direct-debit and card payments.”

## 4 Explain cost and limits

Screen: Final report's Cost latency and reliability section, then `Scope & safeguards` in the app.

“The 4,976 new API calls cost 2.38 US dollars, including the initial cost check. Earlier pilot charges were not recorded. Prompt caching kept the measured cost low, so isolated requests may cost more. Median test latency was 2.19 seconds.

“The program records charges, saves predictions and stops on service errors or unknown billing. Fixed labels, structured outputs and a review decision are implemented. PII masking, production access controls, drift monitoring and random audits remain future work. My recommendation is a supervised trial on current tickets, measuring corrected routes and staff time.”

## 5 Show reproducibility

Screen: Independent GitHub README, with the official-test results and files visible.

“The repository contains the code, public data, preserved pilot, complete final evidence and commands for checking the results without another model call. AI assistance supported development and drafting. I remain responsible for understanding and explaining the work.”

## Before submission

Read the report and adjust the narration to words you understand. Record your own explanation, with readable screens and audible speech. Play back the recording once. Keep historical replay separate from new live calls. Confirm that the instructor can access both the private GitHub repository and the recording. Submit through the Final Project route; the recording has not yet been produced or submitted.
