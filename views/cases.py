"""Cases: a filterable table of every case in a run; select a row for the case, expected behaviour, the recorded
output and each metric's verdict per run."""

import json

import pandas as pd
import streamlit as st

from hoteleval.dashboard_data import SPLIT_LABEL, case_rows, latest, verdict_table
from views import components as ui

ui.header(
    "Cases",
    "Every labelled case in a run. Filter, then select a row to see what was asked, what was expected, what the "
    "assistant actually wrote (from the recording) and how each metric judged it.",
    "Drill down",
)
idx = ui.index()
c1, c2 = st.columns([1, 2])
project = c1.selectbox("Project", list(ui.PROJECT_NAMES), format_func=lambda p: ui.SHORT_NAMES[p])
runs = [
    e for e in sorted(idx, key=lambda e: (e.get("date") or "", e["run_id"]), reverse=True) if e["project"] == project
]
if not runs:
    st.info("No saved runs for this project.")
    st.stop()
default = runs.index(latest(idx, project)) if latest(idx, project) in runs else 0
run_id = c2.selectbox("Run", [e["run_id"] for e in runs], index=default)
summary = ui.report(run_id)
cases = ui.cases(project)
df = pd.DataFrame(case_rows(summary, cases))

f1, f2, f3, f4 = st.columns(4)
splits = f1.multiselect("Split", sorted(df["split"].unique()))
cats = f2.multiselect("Category", sorted(df["category"].unique()))
result = f3.multiselect("Result", ["pass", "fail", "mixed"])
flaky_only = f4.toggle("Flaky only", help="Cases whose verdict changed between runs")
view = df
if splits:
    view = view[view["split"].isin(splits)]
if cats:
    view = view[view["category"].isin(cats)]
if result:
    view = view[view["result"].isin(result)]
if flaky_only:
    view = view[view["flaky"]]
st.caption(f"{len(view)} of {len(df)} cases · select a row for details")
event = st.dataframe(
    view[["case", "split", "category", "result", "flaky", "failed metrics", "input"]],
    hide_index=True,
    use_container_width=True,
    on_select="rerun",
    selection_mode="single-row",
    key=f"cases_{run_id}",
)
picked = event.selection.rows if event and event.selection else []
if not picked:
    ui.footer()
    st.stop()

cid = view.iloc[picked[0]]["case"]
case = cases[cid]
st.subheader(f"Case {cid} · {case.category}")
meta = [f"Split: {SPLIT_LABEL[case.split]}", f"Property: {case.property}", f"Expected: {case.behaviour}"]
if case.tags:
    meta.append("Tags: " + ", ".join(case.tags))
if case.added:
    meta.append("added in Project 3")
st.caption(" · ".join(meta))
left, right = st.columns(2)
with left:
    st.markdown("**What was asked**")
    st.code(case.text(), language=None, wrap_lines=True)
    st.markdown("**Expected (the labelled fields)**")
    st.code(
        json.dumps({k: v for k, v in case.expected.items() if v not in ([], "", None)}, ensure_ascii=False, indent=1),
        language="json",
        wrap_lines=True,
    )
with right:
    outs = sorted((o for o in ui.outputs(run_id) if o["case_id"] == cid), key=lambda o: o["run"])
    for o in outs:
        st.markdown(f"**Recorded output, run {o['run']}** · {o.get('kind') or ''}")
        st.code(o.get("final_text") or o.get("text") or "(no text)", language=None, wrap_lines=True)
        if o.get("citations"):
            st.caption("Cited: " + "; ".join(o["citations"]))
st.markdown("**Each metric's verdict**")
vt = verdict_table(summary, cid)
headers = list(vt[0].keys()) if vt else ["metric"]
marks = {True: ui.badge("pass"), False: ui.badge("fail"), None: "–"}
ui.table(
    [h.capitalize() for h in headers],
    [[r["metric"]] + [marks[r[h]] for h in headers[1:]] for r in vt],
    raw_cols=tuple(range(1, len(headers))),
    caption=f"Verdicts for {cid}",
)
ui.footer()
