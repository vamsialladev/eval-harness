"""Judge calibration: the LLM judge against the owner's 40 hand labels. Shown only once calibration exists."""

import streamlit as st

from views import components as ui

ui.header(
    "Can the judge be trusted?",
    "An LLM judge rates completeness, tone and clarity, the qualities code can't check. Before any of its numbers "
    "count, it is compared with labels made by hand. A judge metric is trusted only at Cohen's kappa ≥ 0.6, and it "
    "is never a release gate otherwise.",
    "Judge calibration",
)
cal = ui.calibration()
current = next(v for v in cal["versions"] if v["version"] == cal["current"])
o = current["overall"]


def kappa(x) -> str:
    return "undefined" if x is None else f"{x:.2f}"


ui.tiles(
    [
        (str(cal["labels"]), "Hand labels", f"by {cal['labeler']}, one quality per item"),
        (ui.pct(o["agreement"]), "Judge agrees with the labels", f"95% interval {ui.interval(o['agreement_ci'])}"),
        (kappa(o["kappa"]), "Cohen's kappa (all items)", "agreement beyond chance; trusted at ≥ 0.6"),
        (cal["current"], "Rubric in use", f"{len(cal['versions'])} version(s) measured"),
    ]
)

st.subheader("Confusion matrix (all items, rubric " + cal["current"] + ")")
c = o["confusion"]
ui.table(
    ["", "Judge: fail", "Judge: pass"],
    [["Human: fail", c["tp"], c["fn"]], ["Human: pass", c["fp"], c["tn"]]],
    caption="Judge verdicts against human labels",
)
st.caption(
    f'"Fail" is the class that matters: precision {ui.pct(o["precision_fail"])} (of the replies the judge failed, '
    f"the share the human also failed), recall {ui.pct(o['recall_fail'])} (of the replies the human failed, the "
    "share the judge caught)."
)

st.subheader("Which judge metrics are trusted")
rows = []
for dim, s in current["per_dimension"].items():
    status = (
        ui.badge("pass").replace("Pass", "Trusted") if s["trusted"] else ui.badge("fail").replace("Fail", "Not trusted")
    )
    rows.append(
        [
            dim.capitalize(),
            s["n"],
            ui.pct(s["agreement"]),
            kappa(s["kappa"]),
            f"{s.get('human_fail', 0)} / {s.get('judge_fail', 0)}",
            status,
        ]
    )
ui.table(
    ["Judge metric", "Items", "Agreement", "Kappa", "Fails: human / judge", "Status"],
    rows,
    raw_cols=(5,),
    caption="Per-metric calibration",
)
st.caption(
    "About 13 items per metric is a small sample: a kappa from 13 items moves a lot with one disagreement. "
    "Untrusted metrics are reported for information only."
)

st.subheader("Rubric versions")
ui.table(
    ["Version", "What changed", "Agreement", "Kappa", "Precision (fail)", "Recall (fail)", "Trusted metrics"],
    [
        [
            v["version"],
            v.get("change") or "first version",
            ui.pct(v["overall"]["agreement"]),
            kappa(v["overall"]["kappa"]),
            ui.pct(v["overall"]["precision_fail"]),
            ui.pct(v["overall"]["recall_fail"]),
            ", ".join(d for d, t in v["trusted"].items() if t) or "none",
        ]
        for v in cal["versions"]
    ],
    caption="Every rubric version, re-scored on the same recorded replies",
)
st.caption(
    "Each revision was scored against the same 40 labels it was revised on, so later versions' agreement is an "
    "optimistic estimate. Fresh labels are the next step."
)

cons = cal.get("consistency")
if cons:
    st.subheader("The judge against itself")
    changed = ", ".join(cons["changed"]) or "none"
    st.markdown(
        f"The same 40 prompts judged {cons['passes']} times with rubric {cal['current']}: "
        f"**{cons['same_every_pass']} of {cons['items']}** got the same verdict every time "
        f"(changed: {ui.esc(changed)}). "
        "A disagreement that comes and goes on identical input is noise, not a rubric problem."
    )

if cal.get("runs"):
    st.subheader("Judge pass rates on the latest runs (not trusted, information only)")
    ui.table(
        ["Run", "Completeness", "Tone", "Clarity"],
        [[run, ui.pct(r["completeness"]), ui.pct(r["tone"]), ui.pct(r["clarity"])] for run, r in cal["runs"].items()],
        caption="Judge pass rates, run 1 of each run, model-written replies only",
    )
    st.caption(
        "Not trusted, so never a gate. The judge fails more replies on clarity than the human labels did; with no "
        "human failures in the calibration sample, there is no way yet to say which of the two is right."
    )

st.subheader("Where the judge and the human disagree")
dis = [r for r in current["rows"] if r["human"] != r["judge"]]
if not dis:
    st.markdown("No disagreements with this rubric.")
for r in dis:
    with st.expander(f"{r['item_id']} · {r['dimension']} · human {r['human']}, judge {r['judge']}"):
        st.markdown(f"**Human's reason:** {ui.esc(r['human_reason'] or '(none given)')}")
        st.markdown(f"**Judge's reason:** {ui.esc(r['judge_reason'])}")
ui.footer()
