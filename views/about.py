"""Disclaimer: synthetic data, labels, no live API calls, nothing collected."""

import streamlit as st

from views import components as ui

ui.header("Disclaimer", "What this dashboard is, and what it isn't.", "Read me")
st.markdown(
    """
- **Simulated client engagement.** The hotel group, its two properties, its policies, guests, bookings and emails
  are fictional and synthetic. No real hotel, guest or client is involved.
- **Saved results only.** Everything here is read from runs and reports saved in the
  [GitHub repo](https://github.com/vamsialladev/eval-harness). This dashboard makes **no API calls**, holds **no
  secrets** and **accepts no text** from visitors, so it has no admin page and keeps no request log.
- **Human labels are the owner's.** The calibration labels are made by hand by Vamsi Alla on a local labeling
  page and published in the repo unchanged. The judge's numbers are reported against them as measured, including
  when they are not good enough to trust.
- **Numbers are measured, not projected.** Rates come from saved runs, with 95% intervals. Small groups (for example
  six prompt-injection emails) give wide intervals, and the dashboard shows that instead of hiding it.
- **The regression demo is a demo.** The run labelled "regression demo" came from a deliberately bad change on a
  throwaway branch that was deleted and never merged. It exists to show the gate failing.
- **No tracking.** No analytics or cookies are added by this app. Streamlit Community Cloud hosts it; its own
  platform logs are outside this app's control.
"""
)
ui.footer()
