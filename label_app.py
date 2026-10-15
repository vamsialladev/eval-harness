"""Local labeling page for judge calibration (never deployed: the public dashboard accepts no input).

    streamlit run label_app.py --server.port 8502

One click per item (Pass or Fail, optional reason). Every click is saved at once to labels/human-labels.jsonl, so you
can close the tab and come back later: it opens at the first item you haven't labelled. The page never shows the
judge's verdict or any metric, so the labels stay independent.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st  # noqa: E402

from hoteleval.labeling import append_label, load_items, load_labels, next_unlabeled  # noqa: E402
from hoteleval.rubric import load_rubric  # noqa: E402

st.set_page_config(page_title="Label replies · Eval Harness", page_icon=str(ROOT / "assets" / "favicon.png"))
st.html(f"<style>{(ROOT / 'views' / 'style.css').read_text(encoding='utf-8')}</style>")

PROJECT_NAMES = {
    "hotel-ops-assistant": "Project 1 · staff policy assistant",
    "guest-request-agent": "Project 2 · guest email agent",
}
items = load_items()
labels = load_labels()
rubric = load_rubric("v1")

if not items:
    st.error("No items to label. Run: python -m hoteleval.cli sample-labels")
    st.stop()

done = sum(1 for it in items if it["item_id"] in labels)
if "idx" not in st.session_state:
    first = next_unlabeled(items, labels)
    st.session_state.idx = first if first is not None else len(items) - 1

st.html('<p class="gra-eyebrow">Judge calibration · your labels</p><h1 class="gra-title">Label 40 replies</h1>')
st.progress(done / len(items), text=f"{done} of {len(items)} labelled · saved after every click")

if done == len(items) and st.session_state.get("finished"):
    st.success("All 40 labelled. Thank you! You can close this tab. Tell Claude: labels done.")
    st.stop()

i = st.session_state.idx
item = items[i]
dim = rubric["dimensions"][item["dimension"]]
audience = rubric["audience"][item["project"]]
current = labels.get(item["item_id"])

st.caption(f"Item {i + 1} of {len(items)} · {PROJECT_NAMES[item['project']]}")
st.subheader(f"{item['dimension'].capitalize()}: {dim['question']}")
st.markdown(f"**The reader is** {audience}.")
c1, c2 = st.columns(2)
c1.success(f"**Pass** — {dim['pass']}", icon=":material/check_circle:")
c2.error(f"**Fail** — {dim['fail']}", icon=":material/cancel:")
st.caption("Judge only this one quality. Facts, prices and citations are checked by other tests.")

st.markdown("**What was asked**")
st.code(item["input"], language=None, wrap_lines=True)
st.markdown("**The reply**")
st.code(item["reply"], language=None, wrap_lines=True)

if current:
    st.info(
        f"You labelled this **{current['label']}**"
        + (f": {current['reason']}" if current["reason"] else "")
        + ". Click again to change it."
    )

reason = st.text_input("Reason (optional, a few words)", key=f"reason_{item['item_id']}")


def advance():
    fresh = load_labels()
    nxt = next_unlabeled(items, fresh)
    if nxt is None:
        st.session_state.finished = True
        st.session_state.idx = i
    else:
        st.session_state.idx = nxt


b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
if b1.button("Pass", type="primary", icon=":material/check:", width="stretch"):
    append_label(item["item_id"], "pass", reason)
    advance()
    st.rerun()
if b2.button("Fail", icon=":material/close:", width="stretch"):
    append_label(item["item_id"], "fail", reason)
    advance()
    st.rerun()
if b3.button("Back", icon=":material/arrow_back:", width="stretch", disabled=i == 0):
    st.session_state.idx = i - 1
    st.rerun()
if b4.button("Skip for now", icon=":material/arrow_forward:", width="stretch", disabled=i == len(items) - 1):
    st.session_state.idx = i + 1
    st.rerun()
st.caption(
    "Synthetic data: a simulated hotel group and fictional guests. "
    "Your labels are published in the repo as the calibration ground truth."
)
