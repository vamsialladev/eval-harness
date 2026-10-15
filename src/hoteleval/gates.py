"""Regression gates: compare a candidate run with the saved baseline. Pure functions over two scored summaries.

A gated metric fails when (on the cases both runs share):
1. hard gate: it is below 100% (escalation, prompt injection, forbidden promises);
2. floor: it is below its floor;
3. interval: it dropped below the lower end of the baseline's 95% interval;
4. stable flip: a case passed in every baseline run and failed in every candidate run. A pure interval check missed a
   real two-case retrieval regression (top-k 5 -> 2: 98% -> 93% stays inside the interval for 45 cases), so a
   consistent flip counts as a regression on its own (decision 7).
Floors apply only to groups of at least MIN_FLOOR_CASES cases. Re-running Project 2's unchanged code put held-out
key facts at 8 of 9 outputs (3 cases), under the 90% floor: a false alarm from one model miss (decision 15). Small
groups stay covered by the hard gates, the interval and stable flips.
A metric the candidate didn't record (for example retrieval in a format without passages) is reported as skipped.
"""

import tomllib
from pathlib import Path

from hoteleval.metrics import metric_info
from hoteleval.stats import by_case, wilson

GATES_FILE = Path(__file__).resolve().parent / "data" / "gates.toml"
MIN_FLOOR_CASES = 10


def load_gates(path: Path = GATES_FILE) -> dict:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def _rate(per_case: dict[str, list[bool]]) -> float | None:
    values = [v for vs in per_case.values() for v in vs]
    return sum(values) / len(values) if values else None


def _pct(x) -> str:
    return "–" if x is None else f"{x:.0%}"


def _ids(cases) -> str:
    cases = sorted(cases)
    return ", ".join(cases[:8]) + (f" and {len(cases) - 8} more" if len(cases) > 8 else "")


def check_metric(name: str, split: str, base: dict, cand: dict, hard: bool, floor: float | None) -> dict:
    """base/cand: {case_id: [verdict per run]} for one metric and split."""
    common = sorted(set(base) & set(cand))
    b = {c: base[c] for c in common}
    k = {c: cand[c] for c in common}
    base_rate, cand_rate = _rate(b), _rate(k)
    ci = wilson(base_rate * len(b), len(b)) if base_rate is not None else None
    failing = sorted(c for c, vs in k.items() if not all(vs))
    flips = sorted(c for c in common if all(b[c]) and not any(k[c]))
    check = {
        "metric": name,
        "split": split,
        "kind": "hard" if hard else "regression",
        "cases": len(common),
        "baseline": base_rate,
        "candidate": cand_rate,
        "ci": list(ci) if ci else None,
        "floor": 1.0 if hard else floor,
        "flipped": flips,
        "failing": failing,
        "reasons": [],
    }
    label = f"{metric_label(name)} ({split})"
    if not common:
        check["status"] = "skipped"
        check["reasons"].append(f"{label}: not recorded in the candidate run")
        return check
    if hard and cand_rate < 1.0:
        check["reasons"].append(f"{label} {_pct(cand_rate)} is below the 100% hard gate; failing: {_ids(failing)}")
    if not hard and floor is not None and len(common) >= MIN_FLOOR_CASES and cand_rate < floor:
        check["reasons"].append(f"{label} {_pct(cand_rate)} is below its {_pct(floor)} floor")
    if not hard and ci and cand_rate < ci[0] - 1e-9:
        check["reasons"].append(
            f"{label} dropped {_pct(base_rate)} → {_pct(cand_rate)}, below the baseline interval "
            f"({_pct(ci[0])}–{_pct(ci[1])})"
        )
    if flips:
        check["reasons"].append(
            f"{label}: {len(flips)} case(s) passed in every baseline run and now fail: {_ids(flips)}"
        )
    check["status"] = "fail" if check["reasons"] else "pass"
    return check


def metric_label(name: str) -> str:
    for project in ("hotel-ops-assistant", "guest-request-agent"):
        try:
            return metric_info(project, name).label
        except StopIteration:
            continue
    return name


def compare(baseline: dict, candidate: dict, gates: dict | None = None) -> dict:
    project = candidate["meta"]["project"]
    if baseline["meta"]["project"] != project:
        raise ValueError("baseline and candidate are for different projects")
    config = (gates or load_gates())[project]
    hard, floors = set(config.get("hard", [])), dict(config.get("floors", {}))
    checks = []
    for split in ("dev", "held-out", "visitor"):
        b_rows = [r for r in baseline["verdicts"] if r["split"] == split]
        c_rows = [r for r in candidate["verdicts"] if r["split"] == split]
        if not b_rows or not c_rows:
            continue
        b, c = by_case(b_rows), by_case(c_rows)
        for name in sorted(hard | set(floors)):
            if name not in b:
                continue
            checks.append(check_metric(name, split, b[name], c.get(name, {}), name in hard, floors.get(name)))
    failures = [r for ch in checks if ch["status"] == "fail" for r in ch["reasons"]]
    skipped = [r for ch in checks if ch["status"] == "skipped" for r in ch["reasons"]]
    return {
        "baseline": baseline["meta"]["run_id"],
        "candidate": candidate["meta"]["run_id"],
        "passed": not failures,
        "failures": failures,
        "skipped": skipped,
        "checks": checks,
    }


def summary_line(result: dict) -> str:
    if result["passed"]:
        n = sum(1 for c in result["checks"] if c["status"] == "pass")
        return f"PASS: {n} gated checks passed against baseline {result['baseline']}"
    return f"FAIL: {len(result['failures'])} gate failure(s) against baseline {result['baseline']}"
