"""Stage 9, registered with its own verdicts (decision 26): cases load, the run gates, a regression is caught."""

import copy

from hoteleval import gates
from hoteleval.cases import load_cases
from hoteleval.cli import baseline_for
from hoteleval.metrics import metrics_for, score
from hoteleval.scoring import score_run
from hoteleval.store import load_run

P9 = "loyalty-support-modernization"
RUN = "p9-arm-c-live-2026-11-07"


def test_stage_9s_cases_load_and_keep_their_labels():
    cases = load_cases(P9)
    assert len(cases) == 180
    assert {c.split for c in cases} == {"dev", "held-out"}
    assert len([c for c in cases if c.split == "held-out"]) == 80
    assert all(c.uid.startswith("p9/") and "SYNTHETIC" in c.notes for c in cases)
    assert all("expected_final_points" in c.expected for c in cases)


def test_a_stage_9_verdict_is_read_from_the_run_not_recomputed():
    case = load_cases(P9)[0]
    out = {"scored": {"case_success": False, "no_false_approval": True}}
    verdicts = score(case, out)
    assert verdicts["case_success"] is False and verdicts["no_false_approval"] is True
    assert verdicts["ledger_correct"] is None
    assert len(metrics_for(P9)) == 7


def _summary():
    outputs, meta = load_run(RUN)
    return outputs, meta, score_run(outputs, meta)


def test_the_saved_run_passes_its_own_baseline_with_budgets():
    _outputs, _meta, summary = _summary()
    result = gates.compare(baseline_for(P9), summary)
    assert result["passed"], result["failures"]
    budget = [c for c in result["checks"] if c["kind"] == "budget"]
    assert {c["status"] for c in budget} == {"pass"}


def test_one_over_credit_fails_the_hard_gate():
    outputs, meta = load_run(RUN)
    broken = copy.deepcopy(outputs)
    target = next(o for o in broken if o["case_id"].startswith("HO-"))
    target["scored"]["no_false_approval"] = False
    result = gates.compare(baseline_for(P9), score_run(broken, meta))
    assert not result["passed"]
    assert any("No over-credit" in f and "100% hard gate" in f for f in result["failures"])


def test_a_case_that_always_passed_and_now_always_fails_is_a_flip():
    outputs, meta = load_run(RUN)
    broken = copy.deepcopy(outputs)
    for o in broken:
        if o["case_id"] == "HO-001":
            o["scored"]["case_success"] = False
    result = gates.compare(baseline_for(P9), score_run(broken, meta))
    assert any("HO-001" in f for f in result["failures"])
