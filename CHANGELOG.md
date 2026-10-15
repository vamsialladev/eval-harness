# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-15

First release. A simulated client engagement for a fictional hotel group, with synthetic data.

### Added
- `hoteleval` package: shared case schema, Project 1 and Project 2 case import at pinned commits, adapters for both
  projects' recorded outputs, deterministic metric registry reusing the projects' own metric code, Wilson
  intervals, run consistency and flaky cases, regression gates (hard 100%, floors, baseline interval, stable
  flips), markdown + JSON reports and a run index.
- Read-only Streamlit dashboard: Overview, Runs over time, Cases, How it works, Disclaimer.
- Local labeling page for judge calibration (40 stratified items).
- CI: ruff, pytest with a 90% coverage gate, pip-audit, recorded-mode gates, report re-scoring.
- 20 held-out cases added in Project 3; live runners for both projects at pinned commits (`git archive`).
- LLM judge (Claude Haiku 5.5, rubric v1 and v2, structured output, cached by input hash, `--repeat` passes) and
  calibration against 40 owner labels: agreement, Cohen's kappa, precision and recall for "fail", confusion matrix.
- Judge calibration dashboard page; 19 recorded decisions; README, architecture, business case, demo script.

### Measured
- Reproduces Project 1 (98% answer accuracy, 44/45 strict retrieval, 27/27 refusals, 54/54 escalation rules) and
  Project 2 (100% escalation, injection, no promises; routing 98%; citations 94%; $1.30 per 1,000) from their
  recordings. Fresh re-runs of both at the pins: gate PASS.
- Regression demo (top-k 5 → 2): FAIL in recorded mode (1 gate) and live mode (4 gates), q13 and q35.
- Judge vs 40 labels (all pass): agreement 95%, kappa 0.00; no metric trusted. API spend for the project: $0.38.

