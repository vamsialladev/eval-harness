# Eval report: p1-published-2026-10-10

- Project: `hotel-ops-assistant` · Mode: imported · Date: 2026-10-10 · Model: claude-haiku-5-5
- Source: `../hotel-ops-assistant/eval/reports/2026-10-10_2011_bm25_answers_claude-haiku-5-5.jsonl` @ 5f9cd91
- Settings: top_k=5, retrieval=keyword, effort=default
- Prices: $0.1 / $0.5 per million input / output tokens
- Project 1's own recorded 54-question run (3 runs) behind its published numbers; retrieval and escalation recomputed at the pin (no API).
- Synthetic data: a simulated hotel group and fictional guests. Intervals are 95% Wilson intervals over distinct cases.

## Dev set: 54 cases × 3 run(s)

| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |
|---|---|---|---|---|---|
| Answer accuracy | 98% | 90%–100% |  | 159/162 | q37 |
| Strict retrieval | 98% | 88%–100% |  | 132/135 | q37 |
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
| multi_part | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| multilingual | 0% | 0% | 0% | 0% | – | 100% | – | – |
| off_topic | 100% | – | – | – | 100% | 100% | – | 100% |
| override | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| pdf | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| property_rule | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| should_refuse | 100% | – | – | – | 100% | 100% | – | 100% |
| synonym | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| table | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| typo | 100% | 100% | 100% | 100% | – | 100% | – | 100% |
| wrong_premise | 100% | 100% | 100% | 100% | – | 100% | – | 100% |

</details>
