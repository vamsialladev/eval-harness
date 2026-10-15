"""Project 4: latency and cost budgets are gated in CI, and the check can fail."""

from hoteleval.gates import check_budgets, compare, load_gates


def candidate(p95, cost, project="hotel-ops-assistant"):
    return {
        "meta": {"project": project, "run_id": "cand"},
        "splits": {"dev": {"cases": 54, "latency": {"p95_s": p95}, "cost_per_1000": cost}},
        "verdicts": [],
    }


def test_budgets_are_in_the_right_tables():
    gates = load_gates()
    assert gates["hotel-ops-assistant"]["budgets"] == {"p95_s": 4.0, "cost_per_1000": 0.5}
    assert gates["guest-request-agent"]["budgets"] == {"p95_s": 12.0, "cost_per_1000": 2.0}
    assert "budgets" not in gates["hotel-ops-assistant"]["floors"]  # a key in the wrong table once made v2 = v1


def test_within_budget_passes():
    checks = check_budgets(candidate(3.18, 0.18), {"p95_s": 4.0, "cost_per_1000": 0.5})
    assert [c["status"] for c in checks] == ["pass", "pass"]


def test_over_budget_fails_with_a_clear_reason():
    checks = check_budgets(candidate(4.5, 0.9), {"p95_s": 4.0, "cost_per_1000": 0.5})
    assert [c["status"] for c in checks] == ["fail", "fail"]
    reasons = [r for c in checks for r in c["reasons"]]
    assert "Budget Cost per 1,000 requests (dev) $0.90 is over $0.50" in reasons
    assert "Budget p95 latency (dev) 4.50 s is over 4.00 s" in reasons


def test_unmeasured_budgets_are_skipped_not_passed():
    checks = check_budgets(candidate(None, None), {"p95_s": 4.0, "cost_per_1000": 0.5})
    assert [c["status"] for c in checks] == ["skipped", "skipped"]


def test_compare_fails_the_gate_on_a_budget_alone():
    base = {"meta": {"project": "hotel-ops-assistant", "run_id": "base"}, "verdicts": []}
    result = compare(base, candidate(9.0, 0.1))
    assert not result["passed"] and any("p95 latency" in f for f in result["failures"])
    assert compare(base, candidate(1.0, 0.1))["passed"]
