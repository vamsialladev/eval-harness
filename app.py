"""Public, read-only dashboard:  streamlit run app.py

It reads the saved reports in reports/ and runs/ (and judge/ once calibrated). No input, no API calls, no secrets,
so it has no admin page and no request log (decision 12).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st  # noqa: E402

from views import components as ui  # noqa: E402

name = ui.brand().get("product", {}).get("name", "Eval Harness")
st.set_page_config(page_title=name, page_icon=str(ROOT / "assets" / "favicon.png"), layout="wide")
ui.inject_css()
st.logo(str(ROOT / "assets" / "logo.svg"), icon_image=str(ROOT / "assets" / "logo-icon.svg"), size="large")

pages = [
    st.Page("views/overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("views/runs.py", title="Runs over time", icon=":material/show_chart:", url_path="runs"),
    st.Page("views/cases.py", title="Cases", icon=":material/table_rows:", url_path="cases"),
]
if ui.calibration():
    pages.append(
        st.Page("views/calibration.py", title="Judge calibration", icon=":material/balance:", url_path="judge")
    )
pages += [
    st.Page("views/how_it_works.py", title="How it works", icon=":material/schema:", url_path="how-it-works"),
    st.Page("views/about.py", title="Disclaimer", icon=":material/policy:", url_path="disclaimer"),
]
page = st.navigation(pages)
ui.sidebar_links()
try:
    page.run()
except Exception:  # never show a traceback to a visitor
    st.error("This page couldn't load its saved results. Try another page; the owner can check the app logs.")
