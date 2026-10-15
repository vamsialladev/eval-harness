# Contributing

## Workflow
1. Create a branch from `main`: `feature/<short-name>`, `fix/<short-name>` or `docs/<short-name>`.
2. Make the change, with tests. A new metric needs a passing and a failing test.
3. Run the checks below locally.
4. Open a pull request. CI must pass before merging.

## Checks before every pull request
```bash
ruff check . && ruff format --check .
python -m pytest -q --cov
pip-audit -r requirements-judge.txt
python scripts/check_reports.py
hoteleval gate --saved p1-published-2026-10-10
hoteleval gate --saved p2-published-2026-10-14
```
A metric is code: when a result looks too good or too bad, check the metric before the model (Projects 1 and 2
found eight measurement bugs that way; this project's are in docs/DECISIONS.md).

## How to extend
- **A new case:** add a line to `src/hoteleval/data/cases/added.jsonl` with `origin: "added in Project 3"` (or the
  project's own name for later projects). Never edit an imported case; re-import with `scripts/import_cases.py`.
- **A new metric:** a function `(case, output) -> True | False | None` in `src/hoteleval/metrics.py`, an entry in
  `REGISTRY`, and tests in `tests/test_metrics.py` that show it pass and fail.
- **A new project:** an adapter in `src/hoteleval/adapters.py`, a driver in `src/hoteleval/drivers/`, a pin in
  `src/hoteleval/pins.py`, its cases and its gates in `src/hoteleval/data/gates.toml`.
- **A rubric change:** add `data/rubrics/judge-v<N+1>.toml`; never edit an old version. Re-score with recorded
  outputs and record the calibration numbers in docs/DECISIONS.md, good or bad.
- **Moving a pin:** update `pins.py`, re-run `scripts/sync_vendor.py` and `scripts/import_cases.py`, re-import the
  baseline and explain the change in a decision.

## Commit messages
Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for | Example |
|---|---|---|
| `feat:` | New behavior | `feat(gates): fail on stable flips` |
| `fix:` | Bug fix | `fix(metrics): cited policy descriptions are not promises` |
| `test:` | Tests or cases | `test(cases): add cross-property leak cases` |
| `docs:` | Documentation | `docs: record judge calibration v2` |
| `chore:` | Tooling, CI, dependencies | `chore(ci): re-score saved reports` |
| `refactor:` | No behavior change | `refactor(store): resolve folders at call time` |

Versions follow [Semantic Versioning](https://semver.org/); record changes in `CHANGELOG.md`.
