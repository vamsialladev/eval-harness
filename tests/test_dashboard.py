"""Dashboard data shaping, and every page rendered with Streamlit's AppTest (no browser, no API)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from hoteleval import dashboard_data as D
from hoteleval import store
from hoteleval.cases import by_id

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def index():
    return store.read_json(store.REPORTS / "index.json")


def test_latest_prefers_gated_candidates_then_baseline(index):
    assert D.latest(index, "guest-request-agent")["kind"] in ("baseline", "candidate")
    fake = [
        {"project": "p", "run_id": "a", "kind": "baseline", "date": "2026-10-10", "gate": None},
        {"project": "p", "run_id": "b", "kind": "candidate", "date": "2026-10-15", "gate": {"passed": True}},
        {"project": "p", "run_id": "c", "kind": "demo", "date": "2026-10-16", "gate": {"passed": False}},
        {"project": "p", "run_id": "d", "kind": "history", "date": "2026-10-17", "gate": {"passed": False}},
    ]
    assert D.latest(fake, "p")["run_id"] == "b"
    assert D.latest([], "p") is None


def test_gated_rows_and_status():
    summary = store.read_json(store.REPORTS / "p2-dev-2026-10-14.json")
    rows = D.gated_rows(summary)
    assert any(r["status"] == "fail" for r in rows) and rows[0]["kind"] == "hard 100%"
    base = store.read_json(store.REPORTS / "p1-published-2026-10-10.json")
    assert all(r["status"] == "pass" for r in D.gated_rows(base))
    assert D.gate_status("answer_accuracy", 0.5, "hotel-ops-assistant", None, "dev") == "fail"
    assert D.gate_status("escalation_rules", 0.99, "hotel-ops-assistant", None, "dev") == "fail"
    assert D.gate_status("language", 0.1, "hotel-ops-assistant", None, "dev") == "pass"
    assert D.gate_status("answer_accuracy", None, "hotel-ops-assistant", None, "dev") == "skipped"
    gate = {"checks": [{"metric": "answer_accuracy", "split": "dev", "status": "pass"}]}
    assert D.gate_status("answer_accuracy", 0.67, "hotel-ops-assistant", gate, "held-out") == "reported"
    harness = store.read_json(store.REPORTS / "p1-harness-2026-10-14.json")
    held = [r for r in D.gated_rows(harness) if r["split"] == "held-out"]
    assert held and all(r["status"] == "reported" for r in held)  # added cases have no baseline: never "fail"


def test_trend_case_and_verdict_rows(index):
    rows = D.trend_rows(index, "guest-request-agent", "fact_grounding")
    assert len(rows) >= 3 and all(0 <= r["rate"] <= 1 for r in rows)
    summary = store.read_json(store.REPORTS / "p2-published-2026-10-14.json")
    cases = D.case_rows(summary, by_id("guest-request-agent"))
    e12 = next(r for r in cases if r["case"] == "E12")
    assert e12["result"] == "fail" and "Citation accuracy" in e12["failed metrics"]
    x08 = next(r for r in cases if r["case"] == "X08")
    assert x08["flaky"]
    vt = D.verdict_table(summary, "E12")
    assert vt[0]["metric"] and "run 1" in vt[0]


@pytest.mark.parametrize("page", ["overview", "runs", "cases", "how_it_works", "about"])
def test_every_page_renders(page):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception
    at.switch_page(f"views/{page}.py").run()
    assert not at.exception, page
    assert at.get("html") or at.markdown, page


def test_cases_page_filters_run():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    at.switch_page("views/cases.py").run()
    at.selectbox[0].set_value("guest-request-agent").run()
    at.multiselect[2].set_value(["fail"]).run()
    assert not at.exception
    assert any("cases · select a row" in c.value for c in at.caption)


def test_runs_page_switches_metric():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    at.switch_page("views/runs.py").run()
    at.selectbox[0].set_value("guest-request-agent").run()
    at.selectbox[2].set_value("visitor").run()
    assert not at.exception
