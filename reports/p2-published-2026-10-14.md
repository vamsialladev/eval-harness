# Eval report: p2-published-2026-10-14

- Project: `guest-request-agent` · Mode: imported · Date: 2026-10-14 · Model: claude-haiku-5-5
- Source: `../guest-request-agent/eval/recorded/main-final.jsonl`, `../guest-request-agent/eval/recorded/heldout-final.jsonl`, `../guest-request-agent/eval/recorded/visitor-before.jsonl` @ 575a19f
- Prices: $0.1 / $0.5 per million input / output tokens
- Project 2's own recorded final (40 emails x 3), held-out (8 x 1) and visitor (10 x 1) runs behind its published numbers.
- Synthetic data: a simulated hotel group and fictional guests. Intervals are 95% Wilson intervals over distinct cases.

## Dev set: 40 cases × 3 run(s)

| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |
|---|---|---|---|---|---|
| Escalation recall | 100% | 68%–100% |  | 24/24 |  |
| No false escalation | 100% | 89%–100% |  | 96/96 |  |
| Injection resistance | 100% | 61%–100% |  | 18/18 |  |
| No forbidden promises | 100% | 91%–100% |  | 120/120 |  |
| Request coverage | 100% | 91%–100% |  | 117/117 |  |
| Fact grounding | 100% | 91%–100% |  | 120/120 |  |
| Correct tool use | 96% | 82%–99% |  | 78/81 | E12 |
| Task routing | 98% | 87%–100% | 95%–100% | 117/120 | E18, X08 |
| Citation accuracy | 94% | 72%–99% |  | 45/48 | E12 |
| Key facts | 100% | 80%–100% |  | 45/45 |  |
| Answer language | 100% | 34%–100% |  | 6/6 |  |

- Latency (full answer): p50 4.60 s, p95 8.45 s (120 timed outputs)
- Cost per 1,000 requests: $1.30
- Same verdict on every metric in all 3 runs: 95% (flaky: E18, X08)

<details><summary>By category</summary>

| Category | Escalation recall | No false escalation | Injection resistance | No forbidden promises | Request coverage | Fact grounding | Correct tool use | Task routing | Citation accuracy | Key facts | Answer language |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Spanish | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| angry tone | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | – | – |
| availability | – | 100% | – | 100% | 100% | 100% | 100% | 100% | – | 100% | – |
| booking lookup | – | 100% | – | 100% | 100% | 100% | 100% | 100% | – | 100% | – |
| impossible | – | 100% | – | 100% | 100% | 100% | 100% | 100% | – | – | – |
| multi-request | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | – |
| must-escalate | 100% | – | – | 100% | 100% | 100% | – | 100% | – | – | – |
| policy | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | – |
| prompt injection | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| single | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | – |
| task routing | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | – |
| typos | – | 100% | – | 100% | 100% | 100% | 100% | 50% | 100% | 100% | – |
| unknown guest | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | – |
| wrong property | – | 100% | – | 100% | 100% | 100% | 0% | 100% | 0% | – | – |

</details>

## Held-out set: 8 cases × 1 run(s)

| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |
|---|---|---|---|---|---|
| Escalation recall | 100% | 34%–100% |  | 2/2 |  |
| No false escalation | 100% | 61%–100% |  | 6/6 |  |
| Injection resistance | 100% | 21%–100% |  | 1/1 |  |
| No forbidden promises | 100% | 68%–100% |  | 8/8 |  |
| Request coverage | 100% | 68%–100% |  | 8/8 |  |
| Fact grounding | 100% | 68%–100% |  | 8/8 |  |
| Correct tool use | 100% | 61%–100% |  | 6/6 |  |
| Task routing | 100% | 68%–100% |  | 8/8 |  |
| Citation accuracy | 100% | 34%–100% |  | 2/2 |  |
| Key facts | 100% | 44%–100% |  | 3/3 |  |
| Answer language | 100% | 21%–100% |  | 1/1 |  |

- Latency (full answer): p50 4.38 s, p95 7.50 s (8 timed outputs)
- Cost per 1,000 requests: $1.11

<details><summary>By category</summary>

| Category | Escalation recall | No false escalation | Injection resistance | No forbidden promises | Request coverage | Fact grounding | Correct tool use | Task routing | Citation accuracy | Key facts | Answer language |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Spanish | – | 100% | – | 100% | 100% | 100% | 100% | 100% | – | – | 100% |
| booking lookup | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | – | – |
| impossible | – | 100% | – | 100% | 100% | 100% | 100% | 100% | – | 100% | – |
| multi-request | – | 100% | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | – |
| must-escalate | 100% | – | – | 100% | 100% | 100% | – | 100% | – | – | – |
| prompt injection | – | 100% | 100% | 100% | 100% | 100% | 100% | 100% | – | 100% | – |
| task routing | – | 100% | – | 100% | 100% | 100% | 100% | 100% | – | – | – |

</details>

## Visitor set: 10 cases × 1 run(s)

| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |
|---|---|---|---|---|---|
| No forbidden promises | 100% | 72%–100% |  | 10/10 |  |
| First-question success | 100% | 72%–100% |  | 10/10 |  |

- Latency (full answer): p50 3.31 s, p95 4.63 s (8 timed outputs)
- Cost per 1,000 requests: $0.74

<details><summary>By category</summary>

| Category | No forbidden promises | First-question success |
|---|---|---|
| visitor email | 100% | 100% |
| visitor greeting | 100% | 100% |
| visitor off_topic | 100% | 100% |

</details>
