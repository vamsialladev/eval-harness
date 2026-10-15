# Plan: Project 3, Eval Harness (`hoteleval`)

**Goal.** One evaluation system for both earlier projects, so a prompt, model or retrieval change can't lower quality
without a red CI check. Simulated client engagement for a fictional hotel group, synthetic data.

**Build order** (the essentials land first if a usage limit hits):

1. **Harness core.** One case schema; Project 1 (54 questions + 49 visitor questions) and Project 2 (40 + 8 held-out
   + 10 visitor emails) imported without changing their meaning, plus up to 20 new cases where coverage is thin.
   Adapters turn each project's recorded outputs into one output record. Deterministic metrics (copied from the
   projects at pinned commits, then unified), Wilson intervals, run-to-run consistency, flaky cases, regression
   gates against a saved baseline, markdown + JSON reports and a run index. CI: ruff, pytest ≥ 90% coverage,
   pip-audit, recorded-mode gates (no API).
2. **Judge + calibration.** A local labeling page (40 stratified items, one click each, resumable). An LLM judge
   (Claude Haiku 5.5, versioned rubric, structured output, cached by input hash) for completeness, tone and clarity
   only. Agreement, Cohen's kappa, precision/recall for "fail", confusion matrix; a judge metric is trusted only at
   kappa ≥ 0.6 and is never a gate otherwise. At most two rubric revisions, re-scored on recorded outputs.
3. **Dashboard.** Read-only Streamlit app (no API calls, no secrets, no user text): Overview, Runs over time, Cases,
   Judge calibration, How it works and Disclaimer. Deployed early on Streamlit Community Cloud.
4. **Regression demo.** On a throwaway Project 1 branch, lower top-k from 5 to 2 (a realistic token-saving change);
   run recorded + live; save the failing gate report; delete the branch, never merge.
5. **Connect + publish.** One CI job in each project repo that runs the harness gates at tag v1.0.0. Portfolio card,
   case study, video, posts, profile README, resume bullets, handoff.

**Defaults chosen (recorded in DECISIONS.md):** recorded mode is the default and what CI uses; pinned commits
(Project 1 `5f9cd91`, Project 2 `575a19f`) instead of new tags, so the project repos only get the CI job; a candidate
fails a gate on a hard floor, on a drop below the baseline's 95% interval, or on any stable flip (a case that passed
in every baseline run and fails in every candidate run).

**Budget:** under $3 of API spend, mostly judge calls; recorded outputs reused everywhere.
