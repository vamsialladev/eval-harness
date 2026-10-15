# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `hoteleval` package: shared case schema, Project 1 and Project 2 case import at pinned commits, adapters for both
  projects' recorded outputs, deterministic metric registry reusing the projects' own metric code, Wilson
  intervals, run consistency and flaky cases, regression gates (hard 100%, floors, baseline interval, stable
  flips), markdown + JSON reports and a run index.
- Read-only Streamlit dashboard: Overview, Runs over time, Cases, How it works, Disclaimer.
- Local labeling page for judge calibration (40 stratified items).
- CI: ruff, pytest with a 90% coverage gate, pip-audit, recorded-mode gates, report re-scoring.
