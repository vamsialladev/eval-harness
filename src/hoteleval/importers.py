"""Convert each project's own labelled cases into the shared schema. Pure functions: nothing about a case's meaning
changes; every labelled field is kept under its original name in `expected`.
"""

from hoteleval.schema import Case, validate

P1 = "hotel-ops-assistant"
P2 = "guest-request-agent"
P1_TAGS = {
    "adversarial": "prompt-injection",
    "multilingual": "multilingual",
    "cross_property": "cross-property",
    "wrong_premise": "wrong-premise",
    "off_topic": "off-topic",
}
P2_TAGS = {
    "prompt injection": "prompt-injection",
    "must-escalate": "must-escalate",
    "Spanish": "multilingual",
    "wrong property": "cross-property",
}
VISITOR_BEHAVIOUR = {"answer": "answer", "refuse": "refuse", "greeting": "greeting", "offtopic": "off_topic"}


def p1_question(item: dict, origin: str, split: str = "dev") -> Case:
    expected = {k: v for k, v in item.items() if k not in ("id", "property", "question", "category")}
    expected["behaviour"] = "refuse" if item.get("unanswerable") else "answer"
    tags = [P1_TAGS[item["category"]]] if item["category"] in P1_TAGS else []
    if item.get("unanswerable"):
        tags.append("must-refuse")
    if item.get("escalate"):
        tags.append("must-escalate")
    return validate(
        {
            "id": item["id"],
            "project": P1,
            "property": item["property"],
            "category": item["category"],
            "categories": [item["category"]],
            "split": split,
            "input": {"question": item["question"]},
            "expected": expected,
            "tags": tags,
            "origin": origin,
        }
    )


def p1_visitor(item: dict, origin: str) -> Case:
    expected = {k: v for k, v in item.items() if k not in ("id", "property", "question")}
    expected["behaviour"] = VISITOR_BEHAVIOUR[item["expect"]]
    tags = ["must-refuse"] if item["expect"] in ("refuse", "offtopic") else []
    return validate(
        {
            "id": item["id"],
            "project": P1,
            "property": item["property"],
            "category": f"visitor {item['expect']}",
            "categories": [f"visitor {item['expect']}"],
            "split": "visitor",
            "input": {"question": item["question"]},
            "expected": expected,
            "tags": tags,
            "origin": origin,
        }
    )


def p2_email(item: dict, inbox: dict, split: str, origin: str) -> Case:
    email = dict(inbox[item["inbox_id"]]) if "inbox_id" in item else dict(item["email"])
    prop = email.pop("property")
    expected = {k: v for k, v in item.items() if k not in ("id", "categories", "inbox_id", "email", "notes")}
    expect = item.get("expect")
    if expect in ("greeting", "off_topic"):
        expected["behaviour"] = expect
    else:
        expected["behaviour"] = "escalate" if item.get("expect_escalate") else "answer"
    categories = item.get("categories") or [f"visitor {expect}"]
    tags = sorted({P2_TAGS[c] for c in categories if c in P2_TAGS})
    return validate(
        {
            "id": item["id"],
            "project": P2,
            "property": prop,
            "category": categories[0],
            "categories": categories,
            "split": split,
            "input": {"email": email},
            "expected": expected,
            "tags": tags,
            "origin": origin,
            "notes": item.get("notes", ""),
        }
    )
