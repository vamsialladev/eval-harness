"""Runs over time: one metric across every saved run (baseline vs candidates, demo runs labelled), and the run list."""

import altair as alt
import pandas as pd
import streamlit as st

from hoteleval.dashboard_data import SPLIT_LABEL, trend_rows
from hoteleval.gates import metric_label
from hoteleval.metrics import metrics_for
from views import components as ui

KINDS = {
    "baseline": "Baseline",
    "candidate": "Candidate",
    "history": "Earlier development run",
    "demo": "Regression demo (never merged)",
}

ui.header(
    "Runs over time",
    "Each point is one saved run; the bar is its 95% interval. Baselines, candidates and the deliberate "
    "regression demo are marked so a demo is never mistaken for a release.",
    "History",
)
idx = ui.index()
c1, c2, c3 = st.columns([2, 2, 1])
project = c1.selectbox("Project", list(ui.PROJECT_NAMES), format_func=lambda p: ui.SHORT_NAMES[p])
names = [m.name for m in metrics_for(project)]
default = names.index("answer_accuracy" if project == "hotel-ops-assistant" else "escalation_recall")
metric = c2.selectbox("Metric", names, index=default, format_func=metric_label)
split = c3.selectbox("Split", ["dev", "held-out", "visitor"], format_func=SPLIT_LABEL.get)

rows = trend_rows(idx, project, metric, split)
if not rows:
    st.info(f"No saved run measured {metric_label(metric)} on the {SPLIT_LABEL[split].lower()} split for this project.")
else:
    df = pd.DataFrame(rows)
    df["kind"] = df["kind"].map(KINDS)
    colors = alt.Scale(domain=list(KINDS.values()), range=["#1E4636", "#5E8C76", "#94702C", "#B42318"])
    base = alt.Chart(df).encode(x=alt.X("run:N", sort=None, title=None, axis=alt.Axis(labelAngle=-20, labelLimit=220)))
    bars = base.mark_rule(strokeWidth=2).encode(
        y=alt.Y("low:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%"), title=metric_label(metric)),
        y2="high:Q",
        color=alt.Color("kind:N", scale=colors, title=None, legend=alt.Legend(orient="bottom")),
    )
    points = base.mark_point(filled=True, size=90).encode(
        y="rate:Q",
        color=alt.Color("kind:N", scale=colors, title=None),
        tooltip=[
            alt.Tooltip("run:N", title="Run"),
            alt.Tooltip("date:N", title="Date"),
            alt.Tooltip("rate:Q", format=".0%", title="Rate"),
            alt.Tooltip("low:Q", format=".0%", title="Interval low"),
            alt.Tooltip("high:Q", format=".0%", title="Interval high"),
        ],
    )
    st.altair_chart((bars + points).properties(height=340), use_container_width=True)
    ui.table(
        ["Run", "Date", "Kind", "Rate", "95% interval"],
        [[r["run"], r["date"], r["kind"], ui.pct(r["rate"]), ui.interval([r["low"], r["high"]])] for r in rows],
        caption=f"{metric_label(metric)} by run",
    )

st.subheader("Every saved run")
listing = []
for e in sorted((e for e in idx if e["project"] == project), key=lambda e: (e.get("date") or "", e["run_id"])):
    gate = e.get("gate")
    status = "–" if not gate else (ui.badge("pass") if gate["passed"] else ui.badge("fail"))
    listing.append([e["run_id"], e.get("date"), e.get("kind"), e.get("mode"), e.get("description") or "", status])
ui.table(["Run", "Date", "Kind", "Mode", "What it is", "Gate"], listing, raw_cols=(5,), caption="Saved runs")
for e in idx:
    if e["project"] == project and e.get("gate") and not e["gate"]["passed"]:
        with st.expander(f"Why `{e['run_id']}` failed its gate"):
            for f in e["gate"]["failures"]:
                st.markdown(f"- {ui.esc(f)}")
ui.footer()
