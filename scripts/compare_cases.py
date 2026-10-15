"""Before -> after for a chosen group of cases across saved runs (Project 4: the backlog fixes).

    python scripts/compare_cases.py --runs RUN_A RUN_B --ids a01 a02 ... --metric answer_accuracy

Prints one line per run: passed/total, rate and the failing cases. Recorded runs only, no API.
"""

import argparse
import json
from pathlib import Path

from hoteleval.scoring import verdicts_for

ROOT = Path(__file__).resolve().parent.parent


def load(run_id: str) -> tuple[list[dict], str]:
    meta = json.loads((ROOT / "runs" / f"{run_id}.meta.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (ROOT / "runs" / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()]
    return rows, meta["project"]


def compare(run_id: str, ids: set[str], metric: str) -> dict:
    outputs, project = load(run_id)
    outputs = [o for o in outputs if o["case_id"] in ids]
    verdicts, _ = verdicts_for(outputs, project)
    scored = [v["metrics"] | {"case_id": v["case_id"]} for v in verdicts if v["metrics"].get(metric) is not None]
    passed = sum(1 for v in scored if v[metric])
    failing = sorted({v["case_id"] for v in scored if not v[metric]})
    return {"run": run_id, "passed": passed, "total": len(scored), "failing": failing}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--ids", nargs="+", required=True)
    parser.add_argument("--metric", required=True)
    args = parser.parse_args(argv)
    for run in args.runs:
        r = compare(run, set(args.ids), args.metric)
        rate = f"{r['passed'] / r['total']:.0%}" if r["total"] else "n/a"
        print(
            f"{r['run']}: {args.metric} {r['passed']}/{r['total']} ({rate}) failing: {', '.join(r['failing']) or '-'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
