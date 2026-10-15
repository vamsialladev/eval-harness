"""Markdown report for one scored run (the JSON next to it holds everything, including every verdict)."""

from hoteleval.gates import metric_label
from hoteleval.metrics import metrics_for

SPLIT_NAMES = {"dev": "Dev set", "held-out": "Held-out set", "visitor": "Visitor set"}


def pct(x) -> str:
    return "–" if x is None else f"{x:.0%}"


def interval(ci) -> str:
    return "–" if not ci else f"{ci[0]:.0%}–{ci[1]:.0%}"


def secs(x) -> str:
    return "–" if x is None else f"{x:.2f} s"


def money(x) -> str:
    return "–" if x is None else f"${x:.2f}"


def runs_range(m: dict) -> str:
    if m["min"] is None or m["min"] == m["max"]:
        return ""
    return f"{m['min']:.0%}–{m['max']:.0%}"


def render(summary: dict) -> str:
    meta = summary["meta"]
    project = meta["project"]
    lines = [
        f"# Eval report: {meta['run_id']}",
        "",
        f"- Project: `{project}` · Mode: {meta.get('mode')} · Date: {meta.get('date')} · "
        f"Model: {meta.get('model') or '–'}",
        f"- Source: {meta.get('source', '–')}",
    ]
    if meta.get("settings"):
        lines.append("- Settings: " + ", ".join(f"{k}={v}" for k, v in meta["settings"].items()))
    if meta.get("price_in") is not None:
        lines.append(f"- Prices: ${meta['price_in']} / ${meta['price_out']} per million input / output tokens")
    if meta.get("description"):
        lines.append(f"- {meta['description']}")
    lines += [
        "- Synthetic data: a simulated hotel group and fictional guests. Intervals are 95% Wilson intervals over "
        "distinct cases.",
        "",
    ]
    gate = summary.get("gate")
    if gate:
        lines += [f"## Gate against `{gate['baseline']}`", ""]
        lines += ["**PASSED**" if gate["passed"] else "**FAILED**", ""]
        lines += [f"- {f}" for f in gate["failures"]] + [f"- skipped: {s}" for s in gate["skipped"]]
        lines.append("")
    order = [m.name for m in metrics_for(project)]
    for split, s in summary["splits"].items():
        lines += [
            f"## {SPLIT_NAMES[split]}: {s['cases']} cases × {s['runs']} run(s)",
            "",
            "| Metric | Rate | 95% interval | Range over runs | Passed | Failing cases |",
            "|---|---|---|---|---|---|",
        ]
        for name in [n for n in order if n in s["metrics"]]:
            m = s["metrics"][name]
            failing = ", ".join(m["failing_cases"][:10]) + (" …" if len(m["failing_cases"]) > 10 else "")
            lines.append(
                f"| {metric_label(name)} | {pct(m['rate'])} | {interval(m['ci'])} | {runs_range(m)} | "
                f"{m['passed']}/{m['total']} | {failing} |"
            )
        lat = s["latency"]
        cons = s["consistency"]
        lines += [
            "",
            f"- Latency (full answer): p50 {secs(lat['p50_s'])}, p95 {secs(lat['p95_s'])}"
            + (f" · first word p50 {secs(lat['ttft_p50_s'])}" if lat["ttft_p50_s"] is not None else "")
            + (f" ({lat['timed']} timed outputs)" if lat["timed"] else " (not recorded)"),
            f"- Cost per 1,000 requests: {money(s['cost_per_1000'])}",
        ]
        if cons["consistent"] is not None:
            flaky = ", ".join(cons["flaky"]) or "none"
            lines.append(
                f"- Same verdict on every metric in all {cons['runs']} runs: {pct(cons['consistent'])} (flaky: {flaky})"
            )
        lines += ["", "<details><summary>By category</summary>", ""]
        names = [n for n in order if n in s["metrics"]]
        lines += ["| Category | " + " | ".join(metric_label(n) for n in names) + " |"]
        lines += ["|---|" + "---|" * len(names)]
        for cat, rates in s["categories"].items():
            lines.append(f"| {cat} | " + " | ".join(pct(rates.get(n)) for n in names) + " |")
        lines += ["", "</details>", ""]
    if summary.get("unknown_cases"):
        lines += [f"Outputs for unknown cases (ignored): {', '.join(summary['unknown_cases'])}", ""]
    return "\n".join(lines).rstrip() + "\n"
