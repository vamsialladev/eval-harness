import pytest

from hoteleval.cases import load_cases
from hoteleval.importers import p1_question, p1_visitor, p2_email
from hoteleval.schema import CaseError, check_unique, validate
from tests.conftest import p1_case, p2_case


def test_valid_case_has_uid_text_and_native_view():
    c = p1_case()
    assert c.uid == "p1/t01"
    assert c.behaviour == "answer"
    assert c.text() == "Can a guest bring their dog?"
    native = c.native()
    assert native["question"] == c.text() and native["must_contain"] == ["40"] and "behaviour" not in native


def test_email_case_text_joins_subject_and_body():
    assert p2_case().text() == "Parking\nHow much is parking?"


@pytest.mark.parametrize(
    "change, message",
    [
        ({"split": "train"}, "split"),
        ({"project": "other"}, "unknown project"),
        ({"property": "city-hotel"}, "unknown property"),
        ({"expected": {"behaviour": "guess"}}, "behaviour"),
        ({"input": {"question": ""}}, "input"),
    ],
)
def test_invalid_cases_are_rejected(change, message):
    data = p1_case().to_dict()
    data.update(change)
    with pytest.raises(CaseError, match=message):
        validate(data)


def test_missing_fields_are_named():
    with pytest.raises(CaseError, match="missing split"):
        validate(
            {
                "id": "x",
                "project": "hotel-ops-assistant",
                "property": "beach-resort",
                "category": "c",
                "input": {},
                "expected": {},
            }
        )


def test_duplicate_ids_rejected():
    with pytest.raises(CaseError, match="duplicate"):
        check_unique([p1_case(), p1_case()])


def test_bank_counts_and_every_case_valid():
    p1, p2 = load_cases("hotel-ops-assistant"), load_cases("guest-request-agent")
    assert len([c for c in p1 if not c.added]) == 103  # 54 questions + 49 visitor questions
    assert len([c for c in p2 if not c.added]) == 58  # 40 + 8 held-out + 10 visitor emails
    assert len(p1) + len(p2) >= 100
    assert len([c for c in p1 + p2 if c.added]) == 31  # 20 added in Project 3 + 11 in Project 4
    assert len([c for c in p1 + p2 if c.origin.startswith("added in Project 4")]) == 11
    assert {c.split for c in p2} == {"dev", "held-out", "visitor"}


def test_import_keeps_every_labelled_field():
    item = {
        "id": "q99",
        "property": "beach-resort",
        "question": "Q?",
        "category": "adversarial",
        "expected_source": "x.md",
        "must_contain": ["50"],
        "must_not_contain": ["waived"],
        "expected_text": "$50",
    }
    c = p1_question(item, "test")
    assert c.expected["must_not_contain"] == ["waived"] and "prompt-injection" in c.tags
    refuse = p1_question({**item, "unanswerable": True, "escalate": ["safety"]}, "test")
    assert refuse.behaviour == "refuse" and {"must-refuse", "must-escalate"} <= set(refuse.tags)


def test_visitor_and_email_imports():
    v = p1_visitor({"id": "v1", "property": "mountain-lodge", "question": "hi", "expect": "greeting"}, "t")
    assert v.split == "visitor" and v.behaviour == "greeting"
    inbox = {"E1": {"id": "E1", "property": "beach-resort", "from": "a@x", "name": "A", "subject": "S", "body": "B"}}
    e = p2_email(
        {"id": "E1", "categories": ["must-escalate", "Spanish"], "inbox_id": "E1", "expect_escalate": True},
        inbox,
        "dev",
        "t",
    )
    assert e.behaviour == "escalate" and e.property == "beach-resort" and e.tags == ["multilingual", "must-escalate"]
    g = p2_email(
        {"id": "V1", "expect": "off_topic", "email": {"property": "beach-resort", "body": "x"}}, {}, "visitor", "t"
    )
    assert g.behaviour == "off_topic" and g.category == "visitor off_topic"
