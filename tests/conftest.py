import pytest

from hoteleval import store
from hoteleval.adapters import output
from hoteleval.schema import validate


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    """Point runs/ and reports/ at a temp folder."""
    monkeypatch.setattr(store, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(store, "REPORTS", tmp_path / "reports")
    return tmp_path


def p1_case(**over):
    data = {
        "id": "t01",
        "project": "hotel-ops-assistant",
        "property": "beach-resort",
        "category": "property_rule",
        "split": "dev",
        "input": {"question": "Can a guest bring their dog?"},
        "expected": {
            "behaviour": "answer",
            "expected_source": "beach-resort/policies.md",
            "must_contain": ["40"],
            "expected_text": "up to 40 lbs",
        },
        "tags": [],
    }
    data.update(over)
    return validate(data)


def p1_out(text="Dogs up to 40 lbs are welcome [1].", **over):
    fields = {
        "kind": "answer",
        "text": text,
        "citations": ["beach-resort/policies.md"],
        "cited_texts": [{"source": "beach-resort/policies.md", "text": "Dogs are welcome up to 40 lbs."}],
        "retrieved": [
            {"source": "beach-resort/policies.md", "section": "Pets", "text": "Dogs are welcome up to 40 lbs."}
        ],
        "escalation_rules": [],
        "api_calls": 1,
    }
    fields.update(over)
    return output("hotel-ops-assistant", "r", "t01", 1, **fields)


def p2_case(**over):
    data = {
        "id": "E99",
        "project": "guest-request-agent",
        "property": "beach-resort",
        "category": "policy",
        "categories": ["policy"],
        "split": "dev",
        "input": {
            "email": {"from": "a@example.com", "name": "A", "subject": "Parking", "body": "How much is parking?"}
        },
        "expected": {
            "behaviour": "answer",
            "expect_escalate": False,
            "expected_requests": [{"topic": ["parking"]}],
            "expected_tools": ["search_policy"],
            "expected_tasks": [],
            "optional_tasks": [],
            "expected_actions": [],
            "expected_sections": ["Parking"],
            "expected_facts": ["$45"],
            "protected_facts": [],
            "must_not_contain": [],
            "must_not_match": [],
            "language": "en",
        },
        "tags": [],
    }
    data.update(over)
    return validate(data)


def p2_record(draft="Valet parking is $45 per night [P1].", **over):
    rec = {
        "outcome": "drafted",
        "escalate": False,
        "raw_draft": draft,
        "draft": draft,
        "requests": [{"summary": "Parking price"}],
        "steps": [{"kind": "tool", "tool": "search_policy", "ok": True}],
        "tasks": [],
        "actions": [],
        "citations": [{"title": "Beach Resort policies", "section": "Parking"}],
        "checks": {},
        "sources": ["Valet parking is $45 per night."],
        "email": {"body": "How much is parking?", "subject": "Parking"},
        "api_calls": 2,
        "latency_s": 3.0,
        "tokens_in": 1000,
        "tokens_out": 100,
    }
    rec.update(over)
    return rec


def p2_out(rec=None, run=1, case_id="E99"):
    from hoteleval.adapters import from_p2

    return from_p2({"run": run, "case_id": case_id, "record": rec or p2_record()}, "r")
