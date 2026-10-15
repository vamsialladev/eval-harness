# Eval report: p1-demo-topk2-live

- Project: `hotel-ops-assistant` · Mode: live · Date: 2026-10-14 · Model: claude-haiku-5-5
- Source: live run of hotel-ops-assistant @ ba49394
- Settings: top_k=2, retrieval=keyword, effort=default
- Prices: $0.1 / $0.5 per million input / output tokens
- DEMO, never merged: a throwaway branch lowered top-k from 5 to 2. Live mode: Project 1's real pipeline on that branch, 54 questions x 3 runs.
- Synthetic data: a simulated hotel group and fictional guests. Intervals are 95% Wilson intervals over distinct cases.

## Gate against `p1-published-2026-10-10`

**FAILED**

- Answer accuracy (dev): 2 case(s) passed in every baseline run and now fail: q13, q35
- Citation accuracy (dev): 1 case(s) passed in every baseline run and now fail: q13
- Numeric grounding (dev): 1 case(s) passed in every baseline run and now fail: q13
- Strict retrieval (dev): 2 case(s) passed in every baseline run and now fail: q13, q35

## Dev set: 54 cases × 3 run(s)

| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |
|---|---|---|---|---|---|
| Answer accuracy | 94% | 84%–98% | 93%–94% | 152/162 | q13, q35, q37, q51 |
| Strict retrieval | 93% | 82%–98% |  | 126/135 | q13, q35, q37 |
| Citation accuracy | 96% | 85%–99% |  | 129/135 | q13, q37 |
| Numeric grounding | 95% | 84%–98% | 93%–96% | 128/135 | q13, q21, q37 |
| Correct refusals | 96% | 65%–100% | 89%–100% | 26/27 | q51 |
| Escalation rules | 100% | 93%–100% |  | 162/162 |  |
| Injection resistance | 100% | 21%–100% |  | 3/3 |  |
| No forbidden promises | 100% | 93%–100% |  | 153/153 |  |

- Latency (full answer): p50 1.37 s, p95 3.14 s · first word p50 1.13 s (153 timed outputs)
- Cost per 1,000 requests: $0.15
- Same verdict on every metric in all 3 runs: 96% (flaky: q21, q51)

<details><summary>By category</summary>

| Category | Answer accuracy | Strict retrieval | Citation accuracy | Numeric grounding | Correct refusals | Escalation rules | Injection resistance | No forbidden promises |
|---|---|---|---|---|---|---|---|---|
| adversarial | 100% | 100% | 100% | 100% | – | 100% | 100% | 100% |
| brand_rule | 100% | 100% | 100% | 89% | – | 100% | – | 100% |
| cross_property | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| escalation | 94% | 100% | 100% | 100% | 67% | 100% | – | 100% |
| messy_notes | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| multi_part | 50% | 50% | 100% | 100% | – | 100% | – | 100% |
| multilingual | 0% | 0% | 0% | 0% | – | 100% | – | – |
| off_topic | 100% | – | – | – | 100% | 100% | – | 100% |
| override | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| pdf | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| property_rule | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| should_refuse | 100% | – | – | – | 100% | 100% | – | 100% |
| synonym | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| table | 75% | 75% | 75% | 75% | – | 100% | – | 100% |
| typo | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| wrong_premise | 100% | 100% | 100% | 100% | – | 100% | – | 100% |

</details>
