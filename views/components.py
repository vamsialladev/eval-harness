"""Shared dashboard building blocks: cached data loaders, header, tiles, tables, badges and footer.

Read-only: nothing here accepts user text or calls an API. Values placed inside HTML always go through `esc`.
"""

import html
import tomllib
from pathlib import Path

import streamlit as st

from hoteleval import store
from hoteleval.cases import by_id

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).parent
DEMO_LABEL = "Demo · synthetic data · no live API calls"
PROJECT_NAMES = {
    "hotel-ops-assistant": "Project 1 · Hotel Operations Knowledge Assistant",
    "guest-request-agent": "Project 2 · Guest Request Agent",
}
SHORT_NAMES = {"hotel-ops-assistant": "Project 1 · policy assistant", "guest-request-agent": "Project 2 · email agent"}


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def _mtime(path: Path) -> int:
    return path.stat().st_mtime_ns if path.exists() else 0


def brand() -> dict:
    return _brand(_mtime(ROOT / "branding.toml"))


@st.cache_resource(show_spinner=False)
def _brand(mtime: int) -> dict:
    try:
        return tomllib.loads((ROOT / "branding.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {"product": {"name": "Eval Harness"}, "links": {}}


def index() -> list[dict]:
    return _index(_mtime(store.REPORTS / "index.json"))


@st.cache_data(show_spinner=False)
def _index(mtime: int) -> list[dict]:
    path = store.REPORTS / "index.json"
    return store.read_json(path) if path.exists() else []


def report(run_id: str) -> dict:
    return _report(run_id, _mtime(store.REPORTS / f"{run_id}.json"))


@st.cache_data(show_spinner=False)
def _report(run_id: str, mtime: int) -> dict:
    return store.read_json(store.REPORTS / f"{run_id}.json")


def outputs(run_id: str) -> list[dict]:
    return _outputs(run_id, _mtime(store.RUNS / f"{run_id}.jsonl"))


@st.cache_data(show_spinner=False)
def _outputs(run_id: str, mtime: int) -> list[dict]:
    path = store.RUNS / f"{run_id}.jsonl"
    return store.read_jsonl(path) if path.exists() else []


@st.cache_resource(show_spinner=False)
def cases(project: str) -> dict:
    return by_id(project)


def calibration() -> dict | None:
    path = ROOT / "judge" / "calibration.json"
    return _calibration(_mtime(path))


@st.cache_data(show_spinner=False)
def _calibration(mtime: int) -> dict | None:
    path = ROOT / "judge" / "calibration.json"
    return store.read_json(path) if path.exists() else None


def inject_css():
    st.html(f"<style>{(HERE / 'style.css').read_text(encoding='utf-8')}</style>")


def header(title: str, subtitle: str = "", eyebrow: str = ""):
    parts = [f'<div class="gra-banner" role="note">{esc(DEMO_LABEL)}</div>']
    if eyebrow:
        parts.append(f'<p class="gra-eyebrow">{esc(eyebrow)}</p>')
    parts.append(f'<h1 class="gra-title">{esc(title)}</h1>')
    if subtitle:
        parts.append(f'<p class="gra-subtitle">{esc(subtitle)}</p>')
    st.html("".join(parts))


def tiles(items: list[tuple[str, str, str]]):
    cells = "".join(
        f'<div class="gra-tile"><div class="gra-tile-value">{esc(v)}</div>'
        f'<div class="gra-tile-label">{esc(label)}</div>'
        + (f'<div class="gra-tile-help">{esc(h)}</div>' if h else "")
        + "</div>"
        for v, label, h in items
    )
    st.html(f'<div class="gra-tiles">{cells}</div>')


BADGE = {
    "pass": ("ok", "Pass"),
    "fail": ("error", "Fail"),
    "skipped": ("muted", "Not recorded"),
    "mixed": ("warn", "Mixed"),
    "reported": ("muted", "Reported, not gated"),
}


def badge(status: str) -> str:
    cls, text = BADGE.get(status, ("muted", status))
    return f'<span class="gra-badge gra-badge-{cls}">{esc(text)}</span>'


def table(headers: list[str], rows: list[list], raw_cols: tuple = (), caption: str = ""):
    """Escaped HTML table in a keyboard-focusable, labelled scroll region."""
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{c if i in raw_cols else esc(c)}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows
    )
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    label = esc(caption or "Table")
    st.html(
        f'<div class="gra-table-wrap" tabindex="0" role="region" aria-label="{label}">'
        f'<table class="gra-table">{cap}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    )


def pct(x) -> str:
    return "–" if x is None else f"{x:.0%}"


def interval(ci) -> str:
    return "–" if not ci else f"{ci[0]:.0%}–{ci[1]:.0%}"


def secs(x) -> str:
    return "–" if x is None else f"{x:.1f} s"


def money(x) -> str:
    return "–" if x is None else f"${x:.2f}"


def link_row() -> str:
    links = brand().get("links", {})
    items = [
        ("case_study", "Case study"),
        ("github", "GitHub"),
        ("project1", "Project 1 app"),
        ("project2", "Project 2 app"),
        ("linkedin", "LinkedIn"),
    ]
    return " · ".join(
        f'<a href="{esc(links[k])}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
        for k, label in items
        if links.get(k)
    )


def footer():
    author = brand().get("links", {}).get("author", "Vamsi Alla")
    st.html(
        '<footer class="gra-footer">'
        f"<p>Built by {esc(author)} · Simulated client engagement for a fictional hotel group, with synthetic data. "
        "This dashboard only reads saved results: it accepts no input and makes no API calls.</p>"
        f"<p>{link_row()}</p></footer>"
    )
    st.page_link("views/about.py", label="Disclaimer", icon=":material/policy:")
