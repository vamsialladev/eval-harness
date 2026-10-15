# Demo script (about 90 seconds, live dashboard)

Recorded by `python scripts/record_demo.py` from https://eval-harness.streamlit.app (read-only, no API calls).
Narration: an AI voice (Piper `en_US-lessac-high`, open source, offline), labelled "Narration: AI voice".

| Time | Screen | Narration |
|---|---|---|
| 0:00 | Title card | Eval Harness: a simulated client project, part three of five. |
| 0:04 | Overview | One harness now checks both of the hotel group's assistants the same way: the same cases, metrics and gates, with ninety-five percent intervals on every rate. |
| 0:17 | Overview, gated metrics | It reproduces both projects' published numbers from their own recordings, and fresh re-runs at the pinned versions pass every gate. |
| 0:28 | Runs over time, demo marked | Then I made a realistic bad change on a throwaway branch: two passages instead of five, to save tokens. Retrieval only fell from ninety-eight to ninety-three percent, inside the interval. |
| 0:42 | Run list, failure reasons | The gate still failed, because two questions that always passed now always fail. The message names them. The branch was never merged. |
| 0:52 | Cases, q13 drill-down | Here is one: the spa age question. The right passage dropped out, and every metric shows it. |
| 1:02 | Judge calibration | An AI judge rates tone and clarity. I labelled forty replies by hand. It agreed ninety-five percent of the time, but kappa was zero: my labels had no failures, so agreement proved nothing. No judge score is trusted, and none is a gate. |
| 1:20 | End card | The code, the reports and every decision are linked on screen. |
