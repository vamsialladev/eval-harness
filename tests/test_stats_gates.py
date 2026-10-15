import pytest

from hoteleval import gates
from hoteleval.stats import by_case, cohen_kappa, consistency, percentile, summarize_metric, wilson


def test_wilson_known_values():
    lo, hi = wilson(44, 45)
    assert round(lo, 3) == 0.884 and round(hi, 3) == 0.996
    lo, hi = wilson(8, 8)
    assert hi == 1.0 and round(lo, 3) == 0.676
    assert wilson(0, 0) is None
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and hi < 0.31


def test_percentile_and_empty():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([5], 95) == 5
    assert percentile([None], 50) is None


def test_kappa_known_examples():
    # Textbook example: 50 items, agree 20 yes + 15 no; observed 0.7, expected by chance 0.5 -> kappa 0.4
    a = ["pass"] * 25 + ["fail"] * 25
    b = ["pass"] * 20 + ["fail"] * 5 + ["pass"] * 10 + ["fail"] * 15
    assert cohen_kappa(a, b) == pytest.approx(0.4)
    assert cohen_kappa(["pass", "fail"], ["pass", "fail"]) == pytest.approx(1.0)
    assert cohen_kappa(["pass", "pass"], ["pass", "pass"]) is None
    with pytest.raises(ValueError):
        cohen_kappa([], [])


def rows(spec):
    """spec: {case_id: [verdict per run]} for metric m."""
    out = []
    for cid, vs in spec.items():
        for run, v in enumerate(vs, 1):
            out.append({"case_id": cid, "run": run, "split": "dev", "category": "c", "metrics": {"m": v}})
    return out


def test_summarize_metric_rate_interval_flaky():
    r = rows({"a": [True, True], "b": [True, False], "c": [False, False]})
    s = summarize_metric(by_case(r)["m"], [1, 2], r, "m")
    assert s["rate"] == 0.5 and s["cases"] == 3 and s["per_run"] == [2 / 3, 1 / 3]
    assert s["failing_cases"] == ["b", "c"] and s["flaky_cases"] == ["b"]
    assert consistency(r)["flaky"] == ["b"] and consistency(rows({"a": [True]}))["consistent"] is None


def summary(spec, project="guest-request-agent", run_id="x"):
    verdicts = []
    for name, cases in spec.items():
        for cid, vs in cases.items():
            for run, v in enumerate(vs, 1):
                row = next((r for r in verdicts if r["case_id"] == cid and r["run"] == run), None)
                if row is None:
                    row = {"case_id": cid, "run": run, "split": "dev", "category": "c", "metrics": {}}
                    verdicts.append(row)
                row["metrics"][name] = v
    return {"meta": {"project": project, "run_id": run_id}, "verdicts": verdicts}


CONFIG = {"guest-request-agent": {"hard": ["escalation_recall"], "floors": {"task_routing": 0.5}}}


def test_gate_passes_when_nothing_dropped():
    base = summary({"escalation_recall": {"a": [True]}, "task_routing": {f"c{i}": [True] for i in range(20)}})
    result = gates.compare(base, base, CONFIG)
    assert result["passed"] and "PASS" in gates.summary_line(result)


def test_hard_gate_fails_below_100():
    base = summary({"escalation_recall": {"a": [True], "b": [True]}})
    cand = summary({"escalation_recall": {"a": [True], "b": [False]}})
    result = gates.compare(base, cand, CONFIG)
    assert not result["passed"] and "hard gate" in result["failures"][0] and "b" in result["failures"][0]
    assert "FAIL" in gates.summary_line(result)


def test_floor_and_interval_failures():
    base = summary({"task_routing": {f"c{i}": [True] for i in range(40)}})
    cand = summary({"task_routing": {f"c{i}": [i < 18] for i in range(40)}})
    msgs = " ".join(gates.compare(base, cand, CONFIG)["failures"])
    assert "below its 50% floor" in msgs and "below the baseline interval" in msgs and "now fail" in msgs


def test_stable_flip_alone_fails_inside_the_interval():
    base = summary({"task_routing": {f"c{i}": [True, True] for i in range(45)}})
    cand = summary({"task_routing": {f"c{i}": [i != 3, i != 3] for i in range(45)}})
    result = gates.compare(base, cand, CONFIG)
    check = result["checks"][0]
    assert check["candidate"] > check["ci"][0]  # inside the interval
    assert not result["passed"] and check["flipped"] == ["c3"]


def test_flaky_case_is_not_a_stable_flip():
    base = summary({"task_routing": {f"c{i}": [True, True] for i in range(45)}})
    cand = summary({"task_routing": {f"c{i}": [True, i != 3] for i in range(45)}})
    assert gates.compare(base, cand, CONFIG)["passed"]


def test_unrecorded_metric_is_skipped_not_passed():
    base = summary({"task_routing": {"a": [True]}})
    cand = summary({"escalation_recall": {"a": [True]}})
    result = gates.compare(base, cand, CONFIG)
    assert result["passed"] and result["skipped"] and result["checks"][0]["status"] == "skipped"


def test_projects_must_match():
    with pytest.raises(ValueError):
        gates.compare(summary({}, "hotel-ops-assistant"), summary({}), CONFIG)


def test_bundled_gate_config_has_hard_gates():
    config = gates.load_gates()
    assert set(config["guest-request-agent"]["hard"]) == {
        "escalation_recall",
        "injection_resistance",
        "no_forbidden_promises",
    }
    assert "escalation_rules" in config["hotel-ops-assistant"]["hard"]
    assert gates.metric_label("unknown_metric") == "unknown_metric"
