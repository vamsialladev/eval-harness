# Resume bullets (Project 3)

Honest and measured. Don't edit the resume PDF; use these when updating it.

- Built an installable evaluation harness for two production-style LLM apps (RAG assistant, tool-using email
  agent): 181 labelled cases in one schema, the apps' own metrics at pinned commits, Wilson intervals and regression
  gates in both repos' CI; it reproduced both apps' published numbers and caught a realistic top-k 5→2 regression
  (strict retrieval 98% → 93%, inside the interval) by flagging the two questions that flipped.
- Calibrated an LLM-as-judge (Claude Haiku 5.5, versioned rubric, structured output) against 70 blind hand labels in
  two rounds, the second enriched with real and synthetic failures: best Cohen's kappa 0.29, so no judge metric was
  trusted, reported or used as a gate; found and fixed four grader bugs and two gate-design flaws for $0.41 of total
  API spend (simulated client engagement, synthetic data).
