"""First-question success for the visitor question set (eval/visitor_questions.jsonl). Pure functions.

A visitor's first message succeeds when it gets a meaningful result:
- answer:   an in-scope question gets a correct answer that cites an expected document
- refuse:   bookings and guest records are refused, with at least 2 questions that work ("Did you mean")
- greeting: "hi", "help", "what can you do?" get a friendly reply with at least 3 questions that work
- offtopic: unrelated or gibberish input gets the scope message (never a made-up answer) with at least
            3 questions that work

Without `answers` (no API), only what retrieval and routing decide is graded: in-scope questions must
reach the expected document, greetings and off-topic input must be routed correctly. Model refusals
can't be graded without the model, so those items are skipped.
"""

MIN_SUGGESTIONS = {"refuse": 2, "greeting": 3, "offtopic": 3}
REFUSED_KINDS = {"refusal", "scope"}


def facts_present(item: dict, text: str) -> bool:
    lower = text.lower()
    required = all(s.lower() in lower for s in item.get("must_contain", []))
    any_of = item.get("must_contain_any", [])
    return required and (not any_of or any(s.lower() in lower for s in any_of))


def grade_visitor(item: dict, outcome: dict, answers: bool) -> dict:
    """`outcome`: kind (answer | refusal | scope | greeting | pending), answer, citations, hits, suggestions."""
    expect, kind = item["expect"], outcome["kind"]
    suggestions = len(outcome.get("suggestions", []))
    refused = kind in REFUSED_KINDS
    expected = set(item.get("expected_sources", []))

    if expect == "answer":
        if answers:
            cited = {c["source"] for c in outcome.get("citations", [])}
            success = kind == "answer" and bool(cited & expected) and facts_present(item, outcome.get("answer", ""))
        else:
            success = kind not in REFUSED_KINDS | {"greeting"} and any(
                h["source"] in expected for h in outcome.get("hits", [])
            )
        return {"success": success, "refused": refused, "suggestions": suggestions}

    if expect == "greeting":
        return {"success": kind == "greeting" and suggestions >= 3, "refused": False, "suggestions": suggestions}

    # refuse / offtopic
    if not answers and kind == "pending":  # went to the model: can't be graded without it
        return {"success": None, "refused": None, "suggestions": suggestions}
    if expect == "offtopic" and kind == "answer":
        refused = False
    success = refused and suggestions >= MIN_SUGGESTIONS[expect]
    return {"success": success, "refused": refused, "suggestions": suggestions}


def rate(values: list) -> float | None:
    graded = [v for v in values if v is not None]
    return round(sum(graded) / len(graded), 4) if graded else None


def summarize(items: list, grades: list) -> dict:
    by = {}
    for item, g in zip(items, grades, strict=True):
        by.setdefault(item["expect"], []).append(g)
    out_of_scope = by.get("refuse", []) + by.get("offtopic", [])
    return {
        "first_question_success": rate([g["success"] for g in grades]),
        "in_scope_answered": rate([g["success"] for g in by.get("answer", [])]),
        "out_of_scope_refused": rate([g["refused"] for g in out_of_scope]),
        "greetings_handled": rate([g["success"] for g in by.get("greeting", [])]),
        "off_topic_handled": rate([g["success"] for g in by.get("offtopic", [])]),
        "refusals_with_suggestions": rate([g["success"] for g in by.get("refuse", [])]),
        "counts": {k: len(v) for k, v in by.items()},
        "graded": sum(g["success"] is not None for g in grades),
    }
