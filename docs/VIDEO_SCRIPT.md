# Video script: Eval Harness (about 80 seconds)

I record this myself, in my own voice, over a screen recording of the live dashboard. No AI voice. Setup and tips:
`RECORDING_GUIDE.md` in my portfolio folder. Read it twice, then talk from the bullets. `/` marks a natural pause.
Aim for 140–160 words a minute.

Before recording: open https://eval-harness.streamlit.app two minutes early so it's awake, browser zoom 125%. The
dashboard is read-only and makes no API calls, so nothing here costs anything.

This is an eval tool, not a chatbot, so the shots are adapted: the "action" is a gate catching a bad change, the
"documents" shot is a case's expected passage, and the "follow-up" is drilling into the case that failed.

## Shot list

| Time | On screen | What I say |
|---|---|---|
| 0–10 s | Overview page | I had two AI assistants for a hotel group, / and nothing told me when a change made either one worse. / So I built one eval harness for both. Simulated client, synthetic data. |
| 10–30 s | **Runs over time**: pick the regression demo run; the gate shows FAIL with its reasons | Here's a real bad change I made on purpose. / I cut the search from five passages to two. / The average barely moved, / but the gate failed, and it names the cases that broke. |
| 30–45 s | **Cases**: filter to the demo run, open q13; the expected passage and the answers | This is one of them. / The question needs a passage the smaller search no longer finds. / You can see the expected policy text, and the three answers, all wrong the same way. |
| 45–60 s | Switch the same case to the release run; it passes | Then I ask the obvious next question: / is it the change, or just noise? / Same case on the release run passes three times out of three. / So it's the change. |
| 60–75 s | **Judge calibration** | I also tried an AI judge. / It agreed with my own labels with a kappa of about point three. / That's not good enough, so nothing is gated on it. |
| 75–85 s | New tab: type the URL, the dashboard loads | It's live and read-only. / eval-harness dot streamlit dot app. |

## Exact inputs

| # | Page | Do exactly |
|---|---|---|
| 1 | Runs over time | Choose the regression demo run (top-k 5 → 2) |
| 2 | Cases | Filter to that run, open **q13** |
| 3 | Cases | Switch the run to the P1 v1.6.0 release run, same case |
| 4 | Judge calibration | Scroll to the agreement table |

Tested 2026-10-24: the live dashboard answered (Streamlit status: up). The pages and runs above are saved data, so
they don't change; check them once before recording.

Proof points from the saved reports: the regression demo failed its gate in recorded and live mode (q13, q35 stable
flips); judge vs 70 hand labels, best kappa 0.29.

## LinkedIn caption (one sentence)

I built one eval harness for two AI assistants, and the most useful thing it did was fail a change whose average
score looked fine.
