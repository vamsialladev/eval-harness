# Resume bullets (Project 3)

Honest, measured; the value figure is labelled a projection. Don't edit the resume PDF; use these when updating it.

- Built an installable evaluation harness for two production-style LLM apps (RAG assistant, tool-using email
  agent): 181 labelled cases in one schema, the apps' own metrics at pinned commits, Wilson intervals and regression
  gates in both repos' CI; it reproduced both apps' published numbers and caught a realistic top-k 5→2 regression
  (strict retrieval 98% → 93%, inside the interval) by flagging the two questions that flipped.
- Calibrated an LLM-as-judge (Claude Haiku 5.5, versioned rubric, structured output) against 40 hand labels:
  95% agreement but Cohen's kappa 0.00, so no judge metric was trusted or gated; found and fixed four grader bugs and
  two gate-design flaws, for $0.38 of total API spend (simulated client engagement, synthetic data; projected
  value $26K/yr base, range $1.5K–$68K).
