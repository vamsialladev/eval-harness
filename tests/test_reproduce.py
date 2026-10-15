"""The harness reproduces each project's published numbers from the same recorded outputs (CLAUDE.md §13-14)."""

import pytest

from hoteleval import store
from hoteleval.scoring import score_run


@pytest.fixture(scope="module")
def p1():
    return score_run(*store.load_run("p1-published-2026-10-10"))["splits"]["dev"]["metrics"]


@pytest.fixture(scope="module")
def p2():
    return score_run(*store.load_run("p2-published-2026-10-14"))["splits"]


def test_project_1_published_numbers(p1):
    assert (p1["answer_accuracy"]["passed"], p1["answer_accuracy"]["total"]) == (159, 162)  # 98%
    assert (p1["retrieval_strict"]["passed"], p1["retrieval_strict"]["total"]) == (132, 135)  # 44/45 per run
    assert (p1["citation_accuracy"]["passed"], p1["citation_accuracy"]["total"]) == (132, 135)
    assert (p1["numeric_grounding"]["passed"], p1["numeric_grounding"]["total"]) == (132, 135)
    assert (p1["correct_refusals"]["passed"], p1["correct_refusals"]["total"]) == (27, 27)
    assert p1["escalation_rules"]["rate"] == 1.0  # 54/54


def test_project_2_published_numbers(p2):
    dev = p2["dev"]["metrics"]
    for name in (
        "escalation_recall",
        "injection_resistance",
        "no_forbidden_promises",
        "request_coverage",
        "fact_grounding",
    ):
        assert dev[name]["rate"] == 1.0, name
    assert round(dev["correct_tool_use"]["rate"], 2) == 0.96
    assert f"{dev['task_routing']['rate']:.0%}" == "98%" and dev["task_routing"]["min"] == 0.95
    assert round(dev["citation_accuracy"]["rate"], 2) == 0.94
    assert round(p2["dev"]["latency"]["p50_s"], 1) == 4.6
    assert round(p2["dev"]["cost_per_1000"], 2) == 1.30
    assert all(m["rate"] == 1.0 for m in p2["held-out"]["metrics"].values())
