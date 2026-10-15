# Eval report: p1-demo-topk2-recorded

- Project: `hotel-ops-assistant` · Mode: imported · Date: 2026-10-14 · Model: claude-haiku-5-5
- Source: `../hotel-ops-assistant/eval/reports/2026-10-10_2011_bm25_answers_claude-haiku-5-5.jsonl` @ demo/re
- Settings: top_k=2, retrieval=keyword, effort=default
- DEMO, never merged: a throwaway branch lowered top-k from 5 to 2. Recorded mode: the saved answers, with retrieval recomputed on the demo branch (no API).
- Synthetic data: a simulated hotel group and fictional guests. Intervals are 95% Wilson intervals over distinct cases.

## Gate against `p1-published-2026-10-10`

**FAILED**

- Strict retrieval (dev): 2 case(s) passed in every baseline run and now fail: q13, q35
- skipped: Budget Cost per 1,000 requests (dev): not measured in this run (no timing or prices)
- skipped: Budget p95 latency (dev): not measured in this run (no timing or prices)

## Dev set: 54 cases × 3 run(s)

| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |
|---|---|---|---|---|---|
| Answer accuracy | 98% | 90%–100% |  | 159/162 | q37 |
| Strict retrieval | 93% | 82%–98% |  | 126/135 | q13, q35, q37 |
| Citation accuracy | 98% | 88%–100% |  | 132/135 | q37 |
| Numeric grounding | 98% | 88%–100% |  | 132/135 | q37 |
| Correct refusals | 100% | 70%–100% |  | 27/27 |  |
| Escalation rules | 100% | 93%–100% |  | 162/162 |  |
| Injection resistance | 100% | 21%–100% |  | 3/3 |  |
| No forbidden promises | 100% | 93%–100% |  | 153/153 |  |

- Latency (full answer): p50 –, p95 – (not recorded)
- Cost per 1,000 requests: –
- Same verdict on every metric in all 3 runs: 100% (flaky: none)

<details><summary>By category</summary>

| Category | Answer accuracy | Strict retrieval | Citation accuracy | Numeric grounding | Correct refusals | Escalation rules | Injection resistance | No forbidden promises |
|---|---|---|---|---|---|---|---|---|
| adversarial | 100% | 100% | 100% | 100% | – | 100% | 100% | 100% |
| brand_rule | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| cross_property | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| escalation | 100% | 100% | 100% | 100% | 100% | 100% | – | 100% |
| messy_notes | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| multi_part | 100% | 50% | 100% | 100% | – | 100% | – | 100% |
| multilingual | 0% | 0% | 0% | 0% | – | 100% | – | – |
| off_topic | 100% | – | – | – | 100% | 100% | – | 100% |
| override | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| pdf | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| property_rule | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| should_refuse | 100% | – | – | – | 100% | 100% | – | 100% |
| synonym | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| table | 100% | 75% | 100% | 100% | – | 100% | – | 100% |
| typo | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| wrong_premise | 100% | 100% | 100% | 100% | – | 100% | – | 100% |

</details>
