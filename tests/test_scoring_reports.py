import json

import pytest

from hoteleval import cli, report, store
from hoteleval.adapters import from_p1, output, p1_refused
from hoteleval.scoring import cost_per_1000, score_run
from tests.conftest import p1_out

REAL_RUNS = store.ROOT / "runs"


def test_p1_refusal_rule_matches_project_1():
    nf = "I couldn't find this in the hotel's documents. Please check with a manager."
    assert p1_refused({"answer": nf, "cited": []})
    assert p1_refused({"answer": "anything", "pre_api": True})
    assert not p1_refused({"answer": nf + " But the pool opens at 7 [1].", "cited": ["x.md"]})


def test_from_p1_uses_extras_and_recorded_flags():
    out = from_p1(
        {"run": 2, "id": "q01", "answer": "Yes [1].", "cited": ["a.md"], "pre_api": False, "grounded": True},
        "r",
        {"escalation_rules": ["safety"], "latency_s": 1.2},
    )
    assert out["run"] == 2 and out["escalated"] and out["latency_s"] == 1.2 and out["recorded"] == {"grounded": True}
    with pytest.raises(KeyError):
        output("hotel-ops-assistant", "r", "q", 1, bogus=1)


def test_cost_needs_prices_and_tokens():
    outs = [{"tokens_in": 1000, "tokens_out": 100}] * 2
    assert cost_per_1000(outs, 0.10, 0.50) == pytest.approx(0.15)
    assert cost_per_1000(outs, None, 0.5) is None
    assert cost_per_1000([{"tokens_in": 0, "tokens_out": 0}], 0.1, 0.5) is None


def test_score_run_and_report_on_saved_baseline():
    outputs, meta = store.load_run("p1-published-2026-10-10")
    summary = score_run(outputs, meta)
    dev = summary["splits"]["dev"]
    assert dev["cases"] == 54 and dev["runs"] == 3
    text = report.render(
        {**summary, "gate": {"baseline": "b", "passed": False, "failures": ["x dropped"], "skipped": ["y"]}}
    )
    assert "| Answer accuracy | 98% |" in text and "**FAILED**" in text and "skipped: y" in text


def test_unknown_cases_are_reported(tmp_store):
    outs = [{**p1_out(), "case_id": "q01"}, {**p1_out(), "case_id": "zz99"}]
    summary = score_run(outs, {"project": "hotel-ops-assistant", "run_id": "t"})
    assert summary["unknown_cases"] == ["zz99"]
    assert "unknown cases" in report.render({**summary, "meta": {**summary["meta"], "mode": "test"}})


def test_store_roundtrip_and_index(tmp_store):
    outs, meta = store.load_run("p2-published-2026-10-14", REAL_RUNS)
    meta = {**meta, "run_id": "t-run"}
    store.save_run(outs[:5], meta)
    back, m2 = store.load_run("t-run")
    assert len(back) == 5 and m2["run_id"] == "t-run"
    summary = score_run(back, m2)
    store.write_json(store.REPORTS / "t-run.json", summary)
    (store.REPORTS / "notes.json").write_text("{}", encoding="utf-8")
    entries = store.rebuild_index()
    assert [e["run_id"] for e in entries] == ["t-run"]


def native_p2_rows(n=None):
    outs, _ = store.load_run("p2-published-2026-10-14", REAL_RUNS)
    rows = [{"run": o["run"], "case_id": o["case_id"], "record": o["native"]} for o in outs]
    return rows[:n] if n else rows


def test_cli_gate_pass_and_fail(tmp_path, capsys):
    good = tmp_path / "good.jsonl"
    store.write_jsonl(good, native_p2_rows())
    assert cli.main(["gate", "--project", "guest-request-agent", "--recorded", str(good)]) == 0
    assert "PASS" in capsys.readouterr().out
    rows = native_p2_rows()
    for r in rows:
        if r["case_id"] in ("E05", "E06"):
            r["record"] = {**r["record"], "escalate": False}
    bad = tmp_path / "bad.jsonl"
    store.write_jsonl(bad, rows)
    assert cli.main(["gate", "--project", "guest-request-agent", "--recorded", str(bad)]) == 1
    out = capsys.readouterr().out
    assert "Escalation recall (dev)" in out and "hard gate" in out


def test_cli_import_score_baseline_index(tmp_store, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(store, "BASELINES", tmp_path / "baselines")
    native = tmp_path / "p2.jsonl"
    store.write_jsonl(native, native_p2_rows(40))
    args = [
        "import-run",
        "--project",
        "guest-request-agent",
        "--native",
        str(native),
        "--run-id",
        "t1",
        "--kind",
        "baseline",
        "--price-in",
        "0.1",
        "--price-out",
        "0.5",
        "--published",
        "p95_s=8.4",
    ]
    assert cli.main(args) == 0
    assert cli.main(["score", "--run-id", "t1"]) == 0
    assert cli.main(["baseline", "--run-id", "t1"]) == 0
    assert (tmp_path / "baselines" / "guest-request-agent.json").exists()
    assert cli.main(["score", "--run-id", "t1", "--baseline", "t1"]) == 0
    assert cli.main(["index"]) == 0
    meta = json.loads((tmp_store / "runs" / "t1.meta.json").read_text(encoding="utf-8"))
    assert meta["published"] == {"p95_s": "8.4"} and meta["ref"]


def test_cli_p1_import_without_project_tree(tmp_store, tmp_path):
    native = tmp_path / "p1.jsonl"
    native.write_text(
        json.dumps(
            {
                "run": 1,
                "id": "q01",
                "answer": "Dogs up to 40 lbs [1].",
                "cited": ["beach-resort/policies.md"],
                "pre_api": False,
                "grounded": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    settings, outs = cli.build_outputs("hotel-ops-assistant", [native], "t", None, None, tmp_path / ".work")
    assert settings == {} and outs[0]["retrieved"] is None and outs[0]["recorded"]["grounded"] is True
