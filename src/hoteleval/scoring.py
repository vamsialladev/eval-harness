"""Score a run (a list of output records) into a summary: per split, every metric with its interval, per-run
rates, failing and flaky cases, per-category rates, latency and cost. Pure: no I/O, no API.
"""

from collections import defaultdict

from hoteleval.cases import by_id
from hoteleval.metrics import metrics_for, score
from hoteleval.stats import by_case, consistency, percentile, summarize_metric


def verdicts_for(outputs: list[dict], project: str) -> tuple[list[dict], list[str]]:
    """[{case_id, run, split, category, metrics}] for every output whose case is in the bank, plus unknown IDs."""
    cases = by_id(project)
    rows, unknown = [], []
    for out in outputs:
        case = cases.get(out["case_id"])
        if case is None:
            unknown.append(out["case_id"])
            continue
        rows.append(
            {
                "case_id": case.id,
                "run": out["run"],
                "split": case.split,
                "category": case.category,
                "metrics": score(case, out),
            }
        )
    return rows, sorted(set(unknown))


def cost_per_1000(outputs: list[dict], price_in: float | None, price_out: float | None) -> float | None:
    if price_in is None or price_out is None or not outputs:
        return None
    tokens_in = sum(o.get("tokens_in") or 0 for o in outputs)
    tokens_out = sum(o.get("tokens_out") or 0 for o in outputs)
    if not tokens_in and not tokens_out:
        return None  # tokens not recorded: no cost, rather than a fake $0
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000 / len(outputs) * 1000


def summarize_split(rows: list[dict], outputs: list[dict], project: str, prices) -> dict:
    runs = sorted({r["run"] for r in rows})
    grouped = by_case(rows)
    metrics = {}
    for m in metrics_for(project):
        if m.name in grouped:
            metrics[m.name] = summarize_metric(grouped[m.name], runs, rows, m.name)
    categories: dict[str, dict] = defaultdict(dict)
    for cat in sorted({r["category"] for r in rows}):
        sub = [r for r in rows if r["category"] == cat]
        for name, cases in by_case(sub).items():
            vs = [v for vals in cases.values() for v in vals]
            categories[cat][name] = sum(vs) / len(vs) if vs else None
    timed = [o for o in outputs if o.get("api_calls") and o.get("latency_s") is not None]
    ttft = [o["ttft_s"] for o in timed if o.get("ttft_s") is not None]
    return {
        "cases": len({r["case_id"] for r in rows}),
        "runs": len(runs),
        "outputs": len(rows),
        "metrics": metrics,
        "categories": dict(categories),
        "consistency": consistency(rows),
        "latency": {
            "p50_s": percentile([o["latency_s"] for o in timed], 50),
            "p95_s": percentile([o["latency_s"] for o in timed], 95),
            "ttft_p50_s": percentile(ttft, 50),
            "ttft_p95_s": percentile(ttft, 95),
            "timed": len(timed),
        },
        "cost_per_1000": cost_per_1000(outputs, *prices),
        "tokens": {
            "in": sum(o.get("tokens_in") or 0 for o in outputs),
            "out": sum(o.get("tokens_out") or 0 for o in outputs),
        },
    }


def score_run(outputs: list[dict], meta: dict) -> dict:
    project = meta["project"]
    prices = (meta.get("price_in"), meta.get("price_out"))
    rows, unknown = verdicts_for(outputs, project)
    split_of = {r["case_id"]: r["split"] for r in rows}
    splits = {}
    for split in ("dev", "held-out", "visitor"):
        sub = [r for r in rows if r["split"] == split]
        if sub:
            outs = [o for o in outputs if split_of.get(o["case_id"]) == split]
            splits[split] = summarize_split(sub, outs, project, prices)
    return {"meta": meta, "splits": splits, "verdicts": rows, "unknown_cases": unknown}
