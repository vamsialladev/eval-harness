"""How it works, in plain language."""

import streamlit as st

from hoteleval.cases import load_cases
from views import components as ui

ui.header(
    "How it works",
    "One harness evaluates both assistants the same way, so a prompt, model or retrieval change can't lower quality "
    "without a red check.",
    "Under the hood",
)
st.graphviz_chart(
    """
digraph {
  rankdir=LR; bgcolor="transparent"; node [shape=box, style="rounded,filled", fillcolor="#E6EEEA", color="#1E4636",
  fontname="Helvetica", fontsize=11]; edge [color="#5B625E"];
  cases [label="Case bank\\none schema, both projects\\ndev · held-out · visitor"];
  runners [label="Runners\\nrecorded outputs (default)\\nor live at a pinned commit"];
  metrics [label="Deterministic metrics\\nfacts · grounding · citations\\nescalation · injection · promises"];
  judge [label="LLM judge\\ncompleteness · tone · clarity\\ncalibrated on human labels"];
  stats [label="Statistics\\nWilson intervals · runs\\nflaky cases · categories"];
  gates [label="Regression gates\\nhard 100% · floors\\ninterval · stable flips", fillcolor="#F5EBD7", color="#94702C"];
  out [label="Reports · CI checks\\n· this dashboard"];
  cases -> runners -> metrics -> stats -> gates -> out; runners -> judge -> stats;
}
""",
    use_container_width=True,
)
p1 = len(load_cases("hotel-ops-assistant"))
p2 = len(load_cases("guest-request-agent"))
st.markdown(
    f"""
**1. One case bank.** {p1 + p2} labelled cases: {p1} for Project 1 (staff policy questions) and {p2} for Project 2
(guest emails). Each project's own cases were imported without changing what they test; a few cases were added
where coverage was thin and are marked "added in Project 3". Every case is in one of three splits: **dev** (used
while building), **held-out** (written last, never tuned on) and **visitor** (typed the way a first-time visitor
types).

**2. Recorded first.** Each project's pipeline can be run live at a pinned git commit, but the default is to
re-score saved outputs. That is what CI does: no API calls, no cost, the same result every time.

**3. Deterministic metrics before any AI judge.** Required facts, numbers traceable to a source, the right
document or policy section cited, escalations, prompt-injection resistance and no promised refunds or upgrades
are all checked by code, reusing each project's own metric code at the pinned commit, so the harness reproduces
their published numbers from the same recordings.

**4. A judge only where code can't judge.** Claude Haiku 5.5 rates completeness, tone and clarity against a
versioned rubric. It is compared with labels the owner made by hand; a judge metric counts as trusted only when
Cohen's kappa is at least 0.6, and it never gates a release otherwise.

**5. Honest statistics.** Every rate has a 95% Wilson interval over distinct cases, runs are repeated to find
flaky cases, and results are broken down by category.

**6. Gates.** A candidate run fails if a hard gate (escalation, prompt injection, forbidden promises) drops
below 100%, a metric falls below its floor or below the baseline's interval, or a case that always passed now
always fails. The failure message names the cases that flipped.
"""
)
ui.footer()
