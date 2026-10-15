"""Shape saved reports for the dashboard. Pure functions over the run index and report JSON (no Streamlit, no API)."""

from hoteleval.gates import load_gates, metric_label
from hoteleval.schema import PROJECTS

SPLIT_LABEL = {"dev": "Dev", "held-out": "Held-out", "visitor": "Visitor"}


def latest(index: list[dict], project: str) -> dict | None:
    """The run that speaks for the project now: the newest gated candidate, or else the baseline. Ungated
    experiments (a model comparison) and the regression demo never count."""
    runs = [
        e
        for e in index
        if e["project"] == project and (e.get("kind") == "baseline" or (e.get("gate") and e.get("kind") == "candidate"))
    ]
    return max(runs, key=lambda e: (e.get("date") or "", bool(e.get("gate")), e["run_id"]), default=None)


def gate_status(name: str, rate, project: str, gate: dict | None, split: str, gates: dict | None = None) -> str:
    """pass | fail for one gated metric. With a gate result, its verdict, or "reported" when the gate didn't check
    it (a split with no baseline cases, such as the cases added in Project 3); without one (a baseline), the floor."""
    if gate:
        for ch in gate["checks"]:
            if ch["metric"] == name and ch["split"] == split:
                return ch["status"]
        return "reported"
    config = (gates or load_gates())[project]
    if rate is None:
        return "skipped"
    if name in config.get("hard", []):
        return "pass" if rate >= 1.0 else "fail"
    floor = config.get("floors", {}).get(name)
    return "pass" if floor is None or rate >= floor else "fail"


def gated_rows(summary: dict, gates: dict | None = None) -> list[dict]:
    project = summary["meta"]["project"]
    config = (gates or load_gates())[project]
    hard = config.get("hard", [])
    names = hard + [n for n in config.get("floors", {}) if n not in hard]
    rows = []
    for split, s in summary["splits"].items():
        for name in names:
            m = s["metrics"].get(name)
            if not m:
                continue
            rows.append(
                {
                    "split": split,
                    "metric": name,
                    "label": metric_label(name),
                    "kind": "hard 100%" if name in hard else f"floor {config['floors'][name]:.0%} + interval",
                    "rate": m["rate"],
                    "ci": m["ci"],
                    "passed": m["passed"],
                    "total": m["total"],
                    "status": gate_status(name, m["rate"], project, summary.get("gate"), split, gates),
                }
            )
    return rows


def trend_rows(index: list[dict], project: str, metric: str, split: str = "dev") -> list[dict]:
    rows = []
    for e in sorted((e for e in index if e["project"] == project), key=lambda e: (e.get("date") or "", e["run_id"])):
        m = (e["splits"].get(split) or {}).get("metrics", {}).get(metric)
        if not m or m["rate"] is None:
            continue
        rows.append(
            {
                "run": e["label"] or e["run_id"],
                "run_id": e["run_id"],
                "date": e.get("date"),
                "kind": e.get("kind") or "candidate",
                "rate": m["rate"],
                "low": m["ci"][0] if m["ci"] else None,
                "high": m["ci"][1] if m["ci"] else None,
            }
        )
    return rows


def case_rows(summary: dict, cases: dict) -> list[dict]:
    """One row per case in a run: result over all metrics and runs, flaky flag, which metrics failed."""
    by: dict[str, list[dict]] = {}
    for v in summary["verdicts"]:
        by.setdefault(v["case_id"], []).append(v)
    rows = []
    for cid, vs in sorted(by.items()):
        case = cases.get(cid)
        failed = sorted({k for v in vs for k, x in v["metrics"].items() if x is False})
        per_run = [all(x is not False for x in v["metrics"].values()) for v in vs]
        rows.append(
            {
                "case": cid,
                "project": PROJECTS[summary["meta"]["project"]]["short"].upper(),
                "split": SPLIT_LABEL.get(vs[0]["split"], vs[0]["split"]),
                "category": vs[0]["category"],
                "result": "pass" if all(per_run) else ("fail" if not any(per_run) else "mixed"),
                "flaky": len(set(per_run)) > 1 or any(len({v["metrics"].get(k) for v in vs}) > 1 for k in failed),
                "failed metrics": ", ".join(metric_label(k) for k in failed),
                "input": (case.text() if case else "")[:140],
                "added": bool(case and case.added),
            }
        )
    return rows


def verdict_table(summary: dict, case_id: str) -> list[dict]:
    """metric -> verdict per run for one case."""
    vs = sorted((v for v in summary["verdicts"] if v["case_id"] == case_id), key=lambda v: v["run"])
    names = []
    for v in vs:
        names += [k for k, x in v["metrics"].items() if x is not None and k not in names]
    return [{"metric": metric_label(n), **{f"run {v['run']}": v["metrics"].get(n) for v in vs}} for n in names]
