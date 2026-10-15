"""Statistics: Wilson intervals, percentiles, run-to-run consistency, flaky cases and Cohen's kappa. Pure functions.

Intervals use the number of distinct cases, not cases x runs: running the same question three times doesn't give
three independent samples of the questions guests might ask (decision 6).
"""

import math
import statistics
from collections import defaultdict

Z95 = 1.959964


def wilson(successes: float, n: int, z: float = Z95) -> tuple[float, float] | None:
    """95% Wilson score interval for a rate. `successes` may be fractional (a mean over runs times n)."""
    if n <= 0:
        return None
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def percentile(values, p: float) -> float | None:
    """Inclusive percentile (Project 2's definition): p in 0..100."""
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[int(p) - 1]


def by_case(verdicts: list[dict]) -> dict[str, dict[str, list]]:
    """[{case_id, run, metrics: {name: v}}] -> {metric: {case_id: [v per run, in run order]}} (None dropped)."""
    out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for row in sorted(verdicts, key=lambda r: (r["run"], r["case_id"])):
        for name, v in row["metrics"].items():
            if v is not None:
                out[name][row["case_id"]].append(bool(v))
    return {m: dict(c) for m, c in out.items()}


def summarize_metric(per_case: dict[str, list[bool]], runs: list[int], verdicts: list[dict], name: str) -> dict:
    """Pooled rate over runs, interval over distinct cases, per-run rates and flaky cases for one metric."""
    n_cases = len(per_case)
    values = [v for vs in per_case.values() for v in vs]
    rate = sum(values) / len(values) if values else None
    per_run = []
    for r in runs:
        vs = [row["metrics"][name] for row in verdicts if row["run"] == r and row["metrics"].get(name) is not None]
        per_run.append(sum(map(bool, vs)) / len(vs) if vs else None)
    ci = wilson(rate * n_cases, n_cases) if rate is not None else None
    return {
        "rate": rate,
        "passed": sum(values),
        "total": len(values),
        "cases": n_cases,
        "ci": list(ci) if ci else None,
        "per_run": per_run,
        "min": min((x for x in per_run if x is not None), default=None),
        "max": max((x for x in per_run if x is not None), default=None),
        "failing_cases": sorted(c for c, vs in per_case.items() if not all(vs)),
        "flaky_cases": sorted(c for c, vs in per_case.items() if len(set(vs)) > 1),
    }


def consistency(verdicts: list[dict]) -> dict:
    """Share of cases whose verdict on every metric was the same in every run, and which cases changed."""
    runs = sorted({r["run"] for r in verdicts})
    cases: dict[str, list] = defaultdict(list)
    for row in sorted(verdicts, key=lambda r: r["run"]):
        cases[row["case_id"]].append(tuple(sorted((k, v) for k, v in row["metrics"].items() if v is not None)))
    if len(runs) < 2:
        return {"runs": len(runs), "consistent": None, "flaky": []}
    flaky = sorted(c for c, vs in cases.items() if len(set(vs)) > 1)
    return {"runs": len(runs), "consistent": 1 - len(flaky) / len(cases) if cases else None, "flaky": flaky}


def cohen_kappa(a: list, b: list) -> float | None:
    """Cohen's kappa for two raters over the same items. None when undefined (both raters constant and equal)."""
    if len(a) != len(b) or not a:
        raise ValueError("kappa needs two equal, non-empty label lists")
    n = len(a)
    labels = sorted(set(a) | set(b))
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    expected = sum((a.count(lab) / n) * (b.count(lab) / n) for lab in labels)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)
