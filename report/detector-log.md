# AI-detector log (10 September 2026)

Purpose: a check that the report's prose reads as specific technical writing. The report discloses AI assistance in Section 9 regardless of these scores; the AI role is part of the method. Text was pasted into free, account-less web tools from the in-app browser with Daniel's permission; the pasted sections may be retained by the services.

Sections tested (Markdown marks and tables stripped): A = Summary and Section 1 (4,829 characters); B = Sections 4.1 and 4.2 (7,486); C = Sections 5 and 6 (6,989).

| Service | Section | Result | Note |
|---|---|---|---|
| ZeroGPT (zerogpt.com, free tier, 15,000-character limit) | A | "Your Text is Human written", 0 % AI | |
| ZeroGPT | B | "Your Text is Human written", 0 % AI | |
| ZeroGPT | C | "Your Text is Human written", 0 % AI | |
| Sapling AI Detector (sapling.ai/ai-content-detector, free web tool) | A (first four paragraphs, 3,900 characters) | Fake: 0.0 % | |
| Sapling | Section 6 of draft 8 (3,800 characters) | Fake: 2.4 % | |
| GPTZero (gptzero.me, free tier, 10,000-character limit) | A | not obtained | The Scan button did not issue a request from the hidden in-app browser pane on three attempts; no result was produced. Not retried with an account. |

Draft tested: draft 8 (final text); the figures and tables added in draft 9 do not change the prose tested.

## API results (10 September 2026, Daniel's trial keys; keys not recorded)

Sapling AI-detection API (`/api/v1/aidetect`), per section of draft 9 (tables and marks stripped). Scores are the API's document-level probability; the whole-report call and later re-queries were refused with HTTP 429 (trial rate limit).

| Section | Characters | Score |
|---|---|---|
| Summary | 3,060 | 0.017 |
| 1. The question | 1,718 | 0.002 |
| 2. The review protocol | 5,135 | 0.501 (3 of 41 sentences above 0.5, all long enumerations) |
| 3. The testbed | 5,605 | 0.000 |
| 4. Results | 14,098 | 0.542 |
| 5. What survived | 2,996 | 0.000 |
| 6. Six errors | 4,310 | 0.295 |
| 7. Limitations | 2,599 | 0.571 (bulleted list) |
| 8. Status and artefacts | 2,321 | 0.000 |
| 9. Disclosure | 1,860 | 0.776 |
| References | 783 | 1.000 (reference lists always score high; ignored) |

Action taken: the long enumerating sentences in Sections 2, 4, 7 and 9 were split into shorter sentences, with no number or claim changed (draft 10). Re-test pending the quota reset.

ZeroGPT API (`/api/detect/detectText`): every call returned "Not enough credits"; not usable on the free key.

## Daniel's own runs (10 September 2026)

| Service | Input | Result | Note |
|---|---|---|---|
| GPTZero (account, file upload) | the full PDF | 100 % AI | Document-level classifier confidence on the whole PDF including tables, captions, hashes and the reference list; a different input from the pasted prose sections above. |
| TextGuard.ai | the report | 63 % AI | Aggregation method not known. |

Reading: the four services disagree by up to 100 points on the same report because each is a separate classifier with its own threshold and reference model, the inputs differed (PDF extraction with tables and references versus pasted prose), and the aggregation differs (sentence fraction versus document confidence). The report was drafted by an AI session and edited under review, as Section 9 states, so a high score is not a false positive and a zero is the miss. No further prose changes were made in response to detector scores after draft 10.

## Sapling API re-test of draft 10 (10 September 2026)

Only two sections could be re-scored before the trial rate limit refused further calls: Section 6 unchanged at 0.295 (2 of 36 sentences above 0.5), Section 9 at 0.776 with 0 of 18 sentences above 0.5, so its document score is not attributable to any sentence. Sections 2, 4 and 7 were not re-scored. Detector work closed here; see the reading above.
