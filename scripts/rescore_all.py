"""Re-score every saved run with the current metric code (no API). Use after a metric fix, then
`python scripts/check_reports.py` in CI keeps them honest.

    python scripts/rescore_all.py

Each run is gated against the baseline its report was published with (so moving the bundled baseline never rewrites
an old report's verdict); runs without a report use their project's "baseline"-kind run. Finally the bundled
baselines (src/hoteleval/data/baselines/) are rebuilt from the runs they were made from, keeping `--exclude-added`
when the bundle had it (decision 24).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hoteleval import cli, store  # noqa: E402


def published_baseline(run_id: str) -> str | None:
    path = store.REPORTS / f"{run_id}.json"
    if not path.exists():
        return None
    gate = store.read_json(path).get("gate")
    return gate["baseline"] if gate else None


def main() -> int:
    metas = [store.read_json(p) for p in sorted(store.RUNS.glob("*.meta.json"))]
    kind_baselines = {m["project"]: m["run_id"] for m in metas if m.get("kind") == "baseline"}
    for m in sorted(metas, key=lambda m: m.get("kind") != "baseline"):
        args = ["score", "--run-id", m["run_id"]]
        if m.get("kind") != "baseline":
            base = published_baseline(m["run_id"]) or kind_baselines[m["project"]]
            args += ["--baseline", base, "--no-fail"]
        cli.main(args)
    for path in sorted(store.BASELINES.glob("*.json")):
        meta = store.read_json(path)["meta"]
        args = ["baseline", "--run-id", meta["run_id"]]
        if meta.get("baseline_excludes"):
            args.append("--exclude-added")
        cli.main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
