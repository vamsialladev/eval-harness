"""Re-score every saved run with the current metric code (no API): baselines first, then every other run gated
against its project's baseline. Use after a metric fix, then `python scripts/check_reports.py` in CI keeps them honest.

    python scripts/rescore_all.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hoteleval import cli, store  # noqa: E402


def main() -> int:
    metas = [store.read_json(p) for p in sorted(store.RUNS.glob("*.meta.json"))]
    baselines = {m["project"]: m["run_id"] for m in metas if m.get("kind") == "baseline"}
    for m in sorted(metas, key=lambda m: m.get("kind") != "baseline"):
        args = ["score", "--run-id", m["run_id"]]
        if m.get("kind") != "baseline":
            args += ["--baseline", baselines[m["project"]], "--no-fail"]
        cli.main(args)
    for run_id in baselines.values():
        cli.main(["baseline", "--run-id", run_id])
    return 0


if __name__ == "__main__":
    sys.exit(main())
