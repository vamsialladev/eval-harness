"""Overview: the latest run for each project, its gated metrics with intervals and pass/fail badges, cost, latency."""

import streamlit as st

from hoteleval.dashboard_data import SPLIT_LABEL, gated_rows, latest
from views import components as ui

ui.header(
    "Is quality holding?",
    "The latest evaluation of each assistant, scored the same way: gated metrics with 95% intervals, cost and "
    "latency. Every number comes from a saved run in the repo.",
    "Overview",
)
idx = ui.index()
if not idx:
    st.warning("No saved runs found.")
    st.stop()

for project, title in ui.PROJECT_NAMES.items():
    entry = latest(idx, project)
    if not entry:
        continue
    summary = ui.report(entry["run_id"])
    rows = gated_rows(summary)
    fails = sum(r["status"] == "fail" for r in rows)
    dev = summary["splits"].get("dev") or next(iter(summary["splits"].values()))
    st.subheader(title)
    gate = summary.get("gate")
    if gate:
        note = f"Gated against baseline `{gate['baseline']}`."
    elif entry.get("kind") == "baseline":
        note = "This run is the saved baseline the gates compare against."
    else:
        note = "Not gated."
    st.caption(f"Run `{entry['run_id']}` · {entry.get('date')} · {summary['meta'].get('mode')} · {note}")
    cases = sum(s["cases"] for s in summary["splits"].values())
    ui.tiles(
        [
            (f"{len(rows) - fails}/{len(rows)}", "Gated checks passing", "hard gates at 100% plus regression gates"),
            (
                str(cases),
                "Cases scored",
                " · ".join(f"{SPLIT_LABEL[k]} {v['cases']}" for k, v in summary["splits"].items()),
            ),
            (
                ui.secs(dev["latency"]["p95_s"]),
                "Latency p95 (dev)",
                "full answer" if dev["latency"]["timed"] else "not in this recording",
            ),
            (
                ui.money(dev["cost_per_1000"]),
                "Cost per 1,000 (dev)",
                "measured tokens × listed prices" if dev["cost_per_1000"] else "tokens not recorded",
            ),
        ]
    )
    pub = summary["meta"].get("published")
    if pub and not dev["latency"]["timed"]:
        words = {"p95_s": "full answer p95 {} s", "ttft_p50_s": "first word p50 {} s", "cost_per_1000": "${} per 1,000"}
        st.caption(
            "From Project 1's own report of this run: "
            + ", ".join(words.get(k, k + " {}").format(v) for k, v in pub.items())
            + " (its recording kept the answers but not per-answer timings or tokens)."
        )
    ui.table(
        ["Split", "Metric", "Gate", "Rate", "95% interval", "Passed", "Status"],
        [
            [
                SPLIT_LABEL[r["split"]],
                r["label"],
                r["kind"],
                ui.pct(r["rate"]),
                ui.interval(r["ci"]),
                f"{r['passed']}/{r['total']}",
                ui.badge(r["status"]),
            ]
            for r in rows
        ],
        raw_cols=(6,),
        caption=f"Gated metrics, {title}",
    )
st.caption(
    "Intervals are 95% Wilson intervals over distinct cases (repeat runs of the same case are not new evidence). "
    "Small groups give wide intervals; that's shown rather than hidden."
)
ui.footer()
