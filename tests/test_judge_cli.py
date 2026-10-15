"""Judge and calibration commands end to end with a fake model (no API), and the calibration page."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from hoteleval import cli, judge_cli, labeling, store
from hoteleval.judge import JudgeError
from tests.test_judge_calibration import fake_client

ROOT = Path(__file__).resolve().parent.parent


def verdict_json(fail_dim=None):
    return json.dumps(
        {
            d: {"verdict": "fail" if d == fail_dim else "pass", "reason": "r"}
            for d in ("completeness", "tone", "clarity")
        }
    )


@pytest.fixture
def judge_env(tmp_path, monkeypatch):
    monkeypatch.setattr(judge_cli, "JUDGE_DIR", tmp_path / "judge")
    monkeypatch.setattr(judge_cli, "CACHE_FILE", tmp_path / "judge" / "cache.jsonl")
    monkeypatch.setattr(labeling, "ITEMS_FILE", tmp_path / "labels" / "items.jsonl")
    monkeypatch.setattr(labeling, "LABELS_FILE", tmp_path / "labels" / "human-labels.jsonl")
    monkeypatch.setattr(labeling, "LABELS_DIR", tmp_path / "labels")  # never read the real round-2 labels
    client = fake_client(verdict_json("tone"))
    monkeypatch.setattr(judge_cli, "client_from_env", lambda env: client)
    return tmp_path


def test_sample_judge_calibrate_flow(judge_env, capsys):
    assert cli.main(["sample-labels"]) == 0
    items = labeling.load_items()
    assert len(items) == 40
    assert cli.main(["calibrate"]) == 2  # no labels yet
    assert cli.main(["judge", "--rubric", "v1"]) == 0  # not live: nothing judged
    assert "not in the cache" in capsys.readouterr().out
    assert cli.main(["judge", "--rubric", "v1", "--live"]) == 0
    verdicts = store.read_json(judge_env / "judge" / "items-v1.json")
    assert len(verdicts) == 40
    for item in items[:10]:
        labeling.append_label(item["item_id"], "fail" if item["dimension"] == "tone" else "pass")
    assert cli.main(["calibrate"]) == 0
    cal = store.read_json(judge_env / "judge" / "calibration.json")
    assert cal["labels"] == 10 and cal["current"] == "v1" and cal["versions"][0]["overall"]["n"] == 10
    assert cli.main(["judge", "--rubric", "v1", "--repeat", "1", "--live"]) == 0
    assert cli.main(["calibrate"]) == 0
    cal = store.read_json(judge_env / "judge" / "calibration.json")
    assert cal["consistency"]["passes"] == 2 and cal["consistency"]["changed"] == []
    tone = cal["versions"][0]["per_dimension"]["tone"]
    if tone["n"]:
        assert tone["agreement"] == 1.0  # the fake judge fails every tone item, as the fake labels do


def test_two_rounds_are_reported_separately_and_together(judge_env, monkeypatch):
    monkeypatch.setattr(labeling, "LABELS_DIR", judge_env / "labels")
    assert cli.main(["sample-labels"]) == 0
    r1 = labeling.load_items()
    r2 = [{**r1[i], "item_id": f"r2-{i:02d}", "origin": "synthetic degraded variant"} for i in range(4)]
    store.write_jsonl(judge_env / "labels" / "items-round2.jsonl", r2)
    for item in r1[:5]:
        labeling.append_label(item["item_id"], "pass")
    for item in r2:
        labeling.append_label(item["item_id"], "fail", path=judge_env / "labels" / "human-labels-round2.jsonl")
    assert cli.main(["judge", "--rubric", "v1", "--live"]) == 0
    assert cli.main(["calibrate"]) == 2  # round 2 is labelled but not judged yet
    assert cli.main(["judge", "--rubric", "v1", "--round", "2", "--live"]) == 0
    assert cli.main(["calibrate"]) == 0
    cal = store.read_json(judge_env / "judge" / "calibration.json")
    v1 = cal["versions"][0]
    assert set(v1["rounds"]) == {"round 1", "round 2"} and cal["labels"] == 9
    assert v1["rounds"]["round 2"]["overall"]["n"] == 4 and v1["overall"]["n"] == 9
    assert "round 2" in cal["rounds"] and "enriched" in cal["rounds"]["round 2"]


def test_judge_a_saved_run(judge_env, capsys):
    assert cli.main(["judge", "--rubric", "v1", "--run", "p2-published-2026-10-14", "--live"]) == 0
    data = store.read_json(judge_env / "judge" / "run-p2-published-2026-10-14-v1.json")
    assert data["outputs"] > 30 and data["pass_rates"]["tone"] == 0.0 and data["pass_rates"]["clarity"] == 1.0


def test_calibrate_without_judge_verdicts(judge_env):
    cli.main(["sample-labels"])
    labeling.append_label(labeling.load_items()[0]["item_id"], "pass")
    assert cli.main(["calibrate"]) == 2


def test_client_needs_a_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OTHER=1\n", encoding="utf-8")
    with pytest.raises(JudgeError, match="never printed"):
        judge_cli.client_from_env(env)


def test_calibration_page_renders(tmp_path, monkeypatch):
    from views import components

    cal = {
        "labels": 2,
        "items": 40,
        "labeler": "Vamsi Alla",
        "trust_rule": "kappa >= 0.6",
        "current": "v1",
        "trusted": {"completeness": False, "tone": True, "clarity": False},
        "consistency": {"passes": 3, "items": 40, "same_every_pass": 39, "changed": ["p1-clarity-04"]},
        "runs": {"p1-harness": {"completeness": 1.0, "tone": 0.97, "clarity": 0.87}},
        "versions": [
            {
                "version": "v1",
                "change": "",
                "overall": {
                    "n": 2,
                    "agreement": 0.5,
                    "agreement_ci": [0.1, 0.9],
                    "kappa": 0.0,
                    "precision_fail": None,
                    "recall_fail": 0.0,
                    "confusion": {"tp": 0, "fp": 0, "fn": 1, "tn": 1},
                },
                "per_dimension": {
                    d: {
                        "n": 1,
                        "agreement": 1.0,
                        "kappa": None,
                        "human_fail": 0,
                        "judge_fail": 0,
                        "trusted": d == "tone",
                    }
                    for d in ("completeness", "tone", "clarity")
                },
                "trusted": {"completeness": False, "tone": True, "clarity": False},
                "rows": [
                    {
                        "item_id": "p1-tone-01",
                        "project": "p",
                        "dimension": "tone",
                        "human": "fail",
                        "human_reason": "curt",
                        "judge": "pass",
                        "judge_reason": "fine",
                    }
                ],
            }
        ],
    }
    (tmp_path / "judge").mkdir()
    (tmp_path / "judge" / "calibration.json").write_text(json.dumps(cal), encoding="utf-8")
    monkeypatch.setattr(components, "ROOT", tmp_path)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    at.switch_page("views/calibration.py").run()
    assert not at.exception
    assert any("p1-tone-01" in e.label for e in at.expander)
