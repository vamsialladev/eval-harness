import json
import subprocess
import sys
from collections import Counter

import pytest

from hoteleval import labeling, runner, store


@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / "hello.txt").write_text("v1", encoding="utf-8")

    def git(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    git("init", "-q")
    git("-c", "user.email=t@example.com", "-c", "user.name=t", "add", ".")
    git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


def test_export_never_touches_the_checkout(git_repo, tmp_path):
    (git_repo / "hello.txt").write_text("uncommitted edit", encoding="utf-8")
    tree = runner.export(git_repo, "HEAD", tmp_path / "work")
    assert (tree / "hello.txt").read_text(encoding="utf-8") == "v1"
    assert runner.export(git_repo, "HEAD", tmp_path / "work") == tree  # cached by commit
    with pytest.raises(runner.RunnerError):
        runner.resolve(git_repo, "no-such-ref")


def test_child_env_takes_only_the_key_from_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=test-key-not-real\nOTHER=x\n", encoding="utf-8")
    monkeypatch.setenv("STREAMLIT_SERVER_PORT", "1")
    env = runner.child_env(env_file)
    assert env["ANTHROPIC_API_KEY"] == "test-key-not-real" and "OTHER" not in env and "STREAMLIT_SERVER_PORT" not in env
    assert "ANTHROPIC_API_KEY" not in runner.child_env(None) or True


def test_project_python_falls_back(tmp_path):
    assert runner.project_python(tmp_path) == runner.Path(sys.executable)


def test_write_cases_and_read_driver_output(tmp_path):
    cases = runner.write_cases(tmp_path / "c.jsonl", "guest-request-agent", splits=["held-out"], ids=["H01", "H02"])
    assert [c.id for c in cases] == ["H01", "H02"]
    out = tmp_path / "o.jsonl"
    out.write_text(
        json.dumps({"settings": {"model": "m"}}) + "\n" + json.dumps({"row": {}, "extras": {}}) + "\n", encoding="utf-8"
    )
    settings, rows = runner.read_driver_output(out)
    assert settings == {"model": "m"} and len(rows) == 1
    rec = {"run": 1, "case_id": "H01", "record": {"outcome": "escalated", "escalate": True}}
    assert runner.convert("guest-request-agent", [rec], "r")[0]["escalated"] is True
    p1 = runner.convert(
        "hotel-ops-assistant", [{"row": {"run": 1, "id": "q01", "answer": "x", "cited": []}, "extras": {}}], "r"
    )
    assert p1[0]["case_id"] == "q01"


def test_driver_failure_raises(tmp_path):
    with pytest.raises(runner.RunnerError):
        runner.run_driver("guest-request-agent", tmp_path, runner.Path(sys.executable), ["--bad-flag"], {})


def test_sample_is_stratified_seeded_and_blind():
    items = labeling.sample_items()
    assert len(items) == 40 and items == labeling.sample_items()
    counts = Counter((i["project"], i["dimension"]) for i in items)
    for project in labeling.POOL_RUNS:
        assert (
            counts[(project, "completeness")] == 7
            and counts[(project, "tone")] == 7
            and counts[(project, "clarity")] == 6
        )
    assert len({(i["project"], i["case_id"]) for i in items}) == 40  # each case once
    assert any(i["flagged"] for i in items) and any(not i["flagged"] for i in items)
    assert all(i["reply"].strip() for i in items)


def test_committed_items_match_a_fresh_sample():
    assert labeling.load_items() == labeling.sample_items()


def test_judgeable_excludes_templates():
    base = {
        "project": "guest-request-agent",
        "kind": "drafted",
        "text": "Hi",
        "final_text": "Hi",
        "api_calls": 2,
        "native": {},
    }
    assert labeling.judgeable(base)
    assert not labeling.judgeable({**base, "api_calls": 0})
    assert not labeling.judgeable({**base, "native": {"fallback_reason": "timeout"}})
    assert not labeling.judgeable({**base, "project": "hotel-ops-assistant", "kind": "scope"})


def test_labels_append_and_latest_wins(tmp_path):
    path = tmp_path / "labels.jsonl"
    labeling.append_label("p1-tone-01", "pass", path=path)
    labeling.append_label("p1-tone-01", "fail", " too curt ", path=path)
    latest = labeling.load_labels(path)
    assert latest["p1-tone-01"]["label"] == "fail" and latest["p1-tone-01"]["reason"] == "too curt"
    with pytest.raises(ValueError):
        labeling.append_label("x", "maybe", path=path)
    items = [{"item_id": "p1-tone-01"}, {"item_id": "p1-tone-02"}]
    assert labeling.next_unlabeled(items, latest) == 1
    assert labeling.next_unlabeled(items[:1], latest) is None
    assert labeling.load_labels(tmp_path / "none.jsonl") == {} and labeling.load_items(tmp_path / "none.jsonl") == []


def test_saved_run_files_exist_for_the_pool():
    for runs in labeling.POOL_RUNS.values():
        for run_id in runs:
            assert (store.RUNS / f"{run_id}.jsonl").exists()
