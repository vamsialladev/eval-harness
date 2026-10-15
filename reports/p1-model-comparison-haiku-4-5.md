# Eval report: p1-model-comparison-haiku-4-5

- Project: `hotel-ops-assistant` · Mode: imported · Date: 2026-10-10 · Model: claude-haiku-4-5-20251001
- Source: `../hotel-ops-assistant/eval/reports/2026-10-10_2108_hybrid_answers_claude-haiku-4-5-20251001.jsonl` @ 5f9cd91
- Project 1's recorded model-comparison run (Haiku 4.5, hybrid retrieval, 3 runs). Retrieval not recomputed: hybrid needs embeddings.
- Synthetic data: a simulated hotel group and fictional guests. Intervals are 95% Wilson intervals over distinct cases.

## Dev set: 54 cases × 3 run(s)

| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |
|---|---|---|---|---|---|
| Answer accuracy | 98% | 89%–99% | 96%–98% | 158/162 | q37, q53 |
| Citation accuracy | 98% | 88%–100% |  | 132/135 | q37 |
| Numeric grounding | 98% | 88%–100% |  | 132/135 | q37 |
| Correct refusals | 100% | 70%–100% |  | 27/27 |  |
| Injection resistance | 100% | 21%–100% |  | 3/3 |  |
| No forbidden promises | 100% | 93%–100% |  | 156/156 |  |

- Latency (full answer): p50 –, p95 – (not recorded)
- Cost per 1,000 requests: –
- Same verdict on every metric in all 3 runs: 98% (flaky: q53)

<details><summary>By category</summary>

| Category | Answer accuracy | Citation accuracy | Numeric grounding | Correct refusals | Injection resistance | No forbidden promises |
|---|---|---|---|---|---|---|
| adversarial | 100% | 100% | 100% | – | 100% | 100% |
| brand_rule | 100% | 100% | 100% | – | – | 100% |
| cross_property | 100% | 100% | 100% | – | – | 100% |
| escalation | 94% | 100% | 100% | 100% | – | 100% |
| messy_notes | 100% | 100% | 100% | – | – | 100% |
| multi_part | 100% | 100% | 100% | – | – | 100% |
| multilingual | 0% | 0% | 0% | – | – | 100% |
| off_topic | 100% | – | – | 100% | – | 100% |
| override | 100% | 100% | 100% | – | – | 100% |
| pdf | 100% | 100% | 100% | – | – | 100% |
| property_rule | 100% | 100% | 100% | – | – | 100% |
| should_refuse | 100% | – | – | 100% | – | 100% |
| synonym | 100% | 100% | 100% | – | – | 100% |
| table | 100% | 100% | 100% | – | – | 100% |
| typo | 100% | 100% | 100% | – | – | 100% |
| wrong_premise | 100% | 100% | 100% | – | – | 100% |

</details>
