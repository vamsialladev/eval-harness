"""Every committed report re-scores to the same numbers from its saved run (no API). Run in CI.

    python scripts/check_reports.py

A report whose numbers can't be reproduced from runs/ by the current metric code fails the build, so a published
number can never drift away from the code and recording that produced it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hoteleval import gates, store  # noqa: E402
from hoteleval.scoring import score_run  # noqa: E402


def check(path: Path) -> list[str]:
    saved = store.read_json(path)
    run_id = saved["meta"]["run_id"]
    outputs, meta = store.load_run(run_id)
    fresh = score_run(outputs, meta)
    problems = []
    if fresh["splits"] != saved["splits"]:
        problems.append(f"{run_id}: metric summaries differ from a fresh re-score")
    if fresh["verdicts"] != saved["verdicts"]:
        problems.append(f"{run_id}: per-case verdicts differ from a fresh re-score")
    if saved.get("gate"):
        base = store.read_json(store.REPORTS / f"{saved['gate']['baseline']}.json")
        again = gates.compare(base, fresh)
        if (again["passed"], again["failures"]) != (saved["gate"]["passed"], saved["gate"]["failures"]):
            problems.append(f"{run_id}: gate result differs from a fresh comparison")
    return problems


def main() -> int:
    paths = [p for p in sorted(store.REPORTS.glob("*.json")) if p.name != "index.json"]
    problems = [msg for p in paths for msg in check(p)]
    for msg in problems:
        print(f"FAIL: {msg}")
    if not problems:
        print(f"reports OK: {len(paths)} saved reports re-score to the same numbers")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
