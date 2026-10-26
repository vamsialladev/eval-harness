# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow [Semantic Versioning](https://semver.org/).


## [1.3.0] - 2026-10-25
### Added
- Keep-awake visits (`?source=keepawake`, the shared check from
  [hotel-ai-platform](https://github.com/vamsialladev/hotel-ai-platform)) only load the page.
- The same structured JSON startup lines as every hotel app (app start with version, settings, dependencies).
- docs/RED_TEAM.md: why a red team doesn't apply to a read-only dashboard, and what does.

## [Unreleased]
### Changed
- README first screen: value line, demo video slot, "Try it live" with the wake note, At a glance with a cost row;
  new "Design at scale" section; Business value names who benefits and how a pilot would measure it; tests 92.
- `scripts/record_demo.py` records a captioned screen recording with no AI voice (decision 25); `piper-tts` removed.
- streamlit 1.66.1 with a Pillow 13 floor (pip-audit: 37 CVEs in Pillow 12.3).
### Added
- CI: lychee link check on the README and docs; gitleaks secret scan (CI and pre-commit).

## [1.2.0] - 2026-10-15
### Added
- **Project 4 cases:** 14 held-out cases committed before the fixes they measure (P1 a14–a21: Spanish questions,
  paraphrased and Spanish emergencies, a false-alarm check; P2 b08–b10: Spanish emails and a wrong-hotel email;
  b11–b13: injection phrasings, committed before the injection fix). 195 cases in total.
- **Budgets in the gate:** dev-set p95 latency and cost per 1,000 per project in `gates.toml` (P1 4.0 s / $0.50,
  P2 12.0 s / $2.00); skipped, never passed, when a run has no timing or prices.
- `hoteleval gate --run-file` (gate a saved run copied into a project repo) and `hoteleval baseline --exclude-added`.
- `scripts/compare_cases.py`: before → after for a group of cases across saved runs.
- Saved runs: before and after the Project 4 fixes, and the v1.6.0 / v1.1.0 release runs (3 runs each, live).

### Changed
- Pins moved to Project 1 v1.6.0 and Project 2 v1.1.0; vendored metric code re-synced (Project 2's promise guard and
  triage). Re-scoring every saved run changed no published number.
- Bundled baselines are the release runs, without added cases. CI gates the release runs and checks that the
  previous releases fail against the new baselines (q37, E12).
- Project 1 driver: a failed model call is a failed answer, not a crashed run.
- Held-out a01's label also accepts "has no" (a correct answer it failed).
- `rescore_all.py` keeps each report's original baseline and rebuilds the bundled baselines from their own runs.

### Measured (live, 3 runs, 2026-10-15)
- Project 1 v1.6.0: dev answer accuracy 98% → 100% (162/162); held-out (Project 3's 13) 67% → 85%; the 8 new cases
  62% → 100%; escalation rules on held-out 85% → 100%; p95 2.93 s; $0.18 per 1,000.
- Project 2 v1.1.0: hard gates 100%; correct tool use 96% → 100%; citations 94% → 100%; wrong-hotel cases 0/6 → 6/6;
  held-out injection resistance 100%; held-out key facts 80% (H03, reported); p95 8.33 s; $1.24 per 1,000.

## [1.1.0] - 2026-10-15

### Added
- Calibration round 2: 30 blind items enriched with failures (15 real replies the judge failed, 15 hand-written
  degraded variants), `scripts/build_round2.py`, the labeling page's `--round 2`, `hoteleval judge --round 2`.
- `hoteleval calibrate` reports each round and all labels together, per quality; trust is decided on all labels.
- Rubric v3 (higher bar for "fail"); the calibration page shows every round, confusion matrices and rubric versions.

### Changed
- Untrusted judge numbers are no longer shown as scores anywhere (the run pass-rate table is gone until a metric is
  trusted).
- Dependencies: ruff 0.17.0 (CI pinned to it), actions/checkout v7, actions/setup-python v7.

### Measured
- 70 owner labels (round 1: 40, all pass; round 2: 30, 6 fail). Kappa on all 70: v1 0.22, v2 0.20, v3 0.29 (tone 0.51,
  clarity 0.23, completeness 0.00); round 2 alone (enriched): 0.04, 0.00, 0.13. No judge metric trusted.

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

