"""Judge calibration: the LLM judge against the owner's hand labels, round by round. Shown once calibration exists."""

import streamlit as st

from views import components as ui

ui.header(
    "Can the judge be trusted?",
    "An LLM judge rates completeness, tone and clarity, the qualities code can't check. Before any of its numbers "
    "count, it is compared with labels made by hand. A judge metric is trusted only at Cohen's kappa ≥ 0.6 on all "
    "labels, and it is never a release gate: the hard gates stay deterministic.",
    "Judge calibration",
)
cal = ui.calibration()
current = next(v for v in cal["versions"] if v["version"] == cal["current"])
o = current["overall"]
ENRICHED = "Round 2 was enriched with failures on purpose, so its kappa is not what random traffic would give."


def kappa(x) -> str:
    return "undefined" if x is None else f"{x:.2f}"


def trust_badge(trusted: bool) -> str:
    return ui.badge("pass").replace("Pass", "Trusted") if trusted else ui.badge("fail").replace("Fail", "Not trusted")


ui.tiles(
    [
        (str(cal["labels"]), "Hand labels", f"by {cal['labeler']}, one quality per item"),
        (ui.pct(o["agreement"]), "Agreement, all labels", f"95% interval {ui.interval(o['agreement_ci'])}"),
        (kappa(o["kappa"]), "Cohen's kappa, all labels", "agreement beyond chance; trusted at ≥ 0.6"),
        (cal["current"], "Rubric in use", f"{len(cal['versions'])} version(s) measured"),
    ]
)
for text in (cal.get("rounds") or {}).values():
    st.caption(f"{text}.")
if "round 2" in (cal.get("rounds") or {}):
    st.caption(ENRICHED)

st.subheader("Which judge metrics are trusted (rubric " + cal["current"] + ", all labels)")
rows = []
for dim, s in current["per_dimension"].items():
    by_round = " · ".join(
        f"{name} {kappa(r['per_dimension'][dim]['kappa'])}" for name, r in (current.get("rounds") or {}).items()
    )
    rows.append(
        [
            dim.capitalize(),
            s["n"],
            ui.pct(s["agreement"]),
            kappa(s["kappa"]),
            by_round or "–",
            f"{s.get('human_fail', 0)} / {s.get('judge_fail', 0)}",
            trust_badge(s["trusted"]),
        ]
    )
ui.table(
    ["Judge metric", "Items", "Agreement", "Kappa (all)", "Kappa by round", "Fails: human / judge", "Status"],
    rows,
    raw_cols=(6,),
    caption="Per-metric calibration",
)
st.caption("Only trusted metrics may be reported as judge scores, and none is ever a gate.")

st.subheader("Confusion matrices (rubric " + cal["current"] + ")")
blocks = [("All labels", o)] + [(name.capitalize(), r["overall"]) for name, r in (current.get("rounds") or {}).items()]
cols = st.columns(len(blocks))
for col, (name, stats) in zip(cols, blocks, strict=True):
    with col:
        c = stats["confusion"]
        ui.table(
            ["", "Judge: fail", "Judge: pass"],
            [["Human: fail", c["tp"], c["fn"]], ["Human: pass", c["fp"], c["tn"]]],
            caption=f"{name}: kappa {kappa(stats['kappa'])}, n={stats['n']}",
        )
        st.caption(
            f"Precision (fail) {ui.pct(stats['precision_fail'])} · recall (fail) {ui.pct(stats['recall_fail'])} · "
            f"agreement {ui.pct(stats['agreement'])}"
        )
st.caption(
    '"Fail" is the class that matters: precision is the share of judge fails the human also failed; recall is the '
    "share of human fails the judge caught. " + ENRICHED
)

st.subheader("Rubric versions")
ui.table(
    ["Version", "What changed", "Kappa (all)", "Kappa by round", "Precision (fail)", "Recall (fail)", "Trusted"],
    [
        [
            v["version"],
            v.get("change") or "first version",
            kappa(v["overall"]["kappa"]),
            " · ".join(f"{n} {kappa(r['overall']['kappa'])}" for n, r in (v.get("rounds") or {}).items()) or "–",
            ui.pct(v["overall"]["precision_fail"]),
            ui.pct(v["overall"]["recall_fail"]),
            ", ".join(d for d, t in v["trusted"].items() if t) or "none",
        ]
        for v in cal["versions"]
    ],
    caption="Every rubric version, re-scored on the same recorded replies",
)
st.caption(
    "Revisions were scored against the same labels they were revised on, so later versions' numbers are optimistic. "
    "Fresh labels are the next step."
)

cons = cal.get("consistency")
if cons:
    st.subheader("The judge against itself")
    changed = ", ".join(cons["changed"]) or "none"
    st.markdown(
        f"The same round-1 prompts judged {cons['passes']} times with rubric {cons.get('version', cal['current'])}: "
        f"**{cons['same_every_pass']} of {cons['items']}** got the same verdict every time "
        f"(changed: {ui.esc(changed)}). A disagreement that comes and goes on identical input is noise."
    )

if cal.get("runs"):
    trusted = [d for d, t in cal["trusted"].items() if t]
    st.subheader("Judge pass rates on the latest runs")
    headers = ["Run"] + [d.capitalize() for d in ("completeness", "tone", "clarity")]
    ui.table(
        headers,
        [
            [run]
            + [ui.pct(r[d]) + ("" if d in trusted else " (not trusted)") for d in ("completeness", "tone", "clarity")]
            for run, r in cal["runs"].items()
        ],
        caption="Judge pass rates, run 1 of each run, model-written replies only",
    )
    st.caption("Information only: never a gate. Untrusted metrics are marked.")

st.subheader("Where the judge and the human disagree")
dis = [r for r in current["rows"] if r["human"] != r["judge"]]
if not dis:
    st.markdown("No disagreements with this rubric.")
for r in dis:
    with st.expander(f"{r['item_id']} · {r['dimension']} · human {r['human']}, judge {r['judge']}"):
        st.markdown(f"**Human's reason:** {ui.esc(r['human_reason'] or '(none given)')}")
        st.markdown(f"**Judge's reason:** {ui.esc(r['judge_reason'])}")
ui.footer()
