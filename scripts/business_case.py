"""Projected value of the eval harness for the hotel group's AI assistants. A projection from stated assumptions, not
a measured saving. Only the API cost of a run is measured (reports in this repo).

    python scripts/business_case.py               # base case
    python scripts/business_case.py --scenarios   # pessimistic / base / optimistic table
"""

import argparse
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Assumptions:
    assistants: int = 2  # Projects 1 and 2
    releases_per_month: float = 4  # prompt, model, retrieval or dependency changes per assistant
    manual_hours_per_release: float = 3.0  # re-run evals by hand, read outputs, compare with last time
    harness_hours_per_release: float = 0.5  # read the CI gate result and any flipped cases
    engineer_cost_per_hour: float = 90.0
    regressions_shipped_per_year_without: float = 4  # quality drops that reach staff or guests unnoticed
    share_caught_by_gates: float = 0.75
    cost_per_regression: float = 3000.0  # staff time, guest recovery (comps), manager escalations, rework
    live_runs_per_month: float = 2  # full live re-runs (both projects, 3 runs each)
    api_cost_per_live_run: float = 0.29  # measured: one harness live run of both projects, 3 runs each ($0.06 + $0.23)
    maintenance_hours_per_month: float = 4.0  # new cases, label refreshes, rubric reviews


def yearly(a: Assumptions) -> dict:
    release_hours = (
        a.assistants * a.releases_per_month * 12 * (a.manual_hours_per_release - a.harness_hours_per_release)
    )
    time_value = release_hours * a.engineer_cost_per_hour
    avoided = a.regressions_shipped_per_year_without * a.share_caught_by_gates * a.cost_per_regression
    api = a.live_runs_per_month * 12 * a.api_cost_per_live_run
    maintenance = a.maintenance_hours_per_month * 12 * a.engineer_cost_per_hour
    return {
        "engineer hours saved": release_hours,
        "value of time saved": time_value,
        "regressions avoided (value)": avoided,
        "API cost": -api,
        "maintenance": -maintenance,
        "net value": time_value + avoided - api - maintenance,
    }


SCENARIOS = {
    "pessimistic": replace(
        Assumptions(),
        releases_per_month=2,
        manual_hours_per_release=2.0,
        regressions_shipped_per_year_without=2,
        share_caught_by_gates=0.5,
        cost_per_regression=1500.0,
        maintenance_hours_per_month=6.0,
    ),
    "base": Assumptions(),
    "optimistic": replace(
        Assumptions(),
        releases_per_month=6,
        manual_hours_per_release=4.0,
        regressions_shipped_per_year_without=6,
        share_caught_by_gates=0.85,
        cost_per_regression=5000.0,
        maintenance_hours_per_month=3.0,
    ),
}


def money(x: float) -> str:
    return f"-${-x:,.0f}" if x < 0 else f"${x:,.0f}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenarios", action="store_true")
    args = parser.parse_args(argv)
    if not args.scenarios:
        for k, v in yearly(Assumptions()).items():
            print(f"{k:<30} {v:,.0f}" if "hours" in k else f"{k:<30} {money(v)}")
        return 0
    results = {name: yearly(a) for name, a in SCENARIOS.items()}
    print(f"{'Per year (projection)':<30}" + "".join(f"{n:>14}" for n in results))
    for key in results["base"]:
        cells = [f"{r[key]:,.0f}" if "hours" in key else money(r[key]) for r in results.values()]
        print(f"{key:<30}" + "".join(f"{c:>14}" for c in cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
