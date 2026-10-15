"""Every metric is shown able to pass and able to fail."""

from hoteleval import metrics as M
from hoteleval.metrics import metric_info, metrics_for, score
from tests.conftest import p1_case, p1_out, p2_case, p2_out, p2_record

REFUSAL = "I couldn't find this in the hotel's documents. Please check with a manager."


# ---------- Project 1 ----------
def test_p1_answer_accuracy():
    assert M.p1_answer_accuracy(p1_case(), p1_out()) is True
    assert M.p1_answer_accuracy(p1_case(), p1_out("Dogs are welcome [1].")) is False


def test_p1_answer_accuracy_refusal_cases():
    case = p1_case(expected={"behaviour": "refuse", "unanswerable": True, "expected_source": None, "must_contain": []})
    assert M.p1_answer_accuracy(case, p1_out(REFUSAL, refused=True, citations=[])) is True
    assert M.p1_answer_accuracy(case, p1_out("Yes, at 9 AM [1].")) is False
    assert M.p1_correct_refusals(case, p1_out(REFUSAL, refused=True)) is True
    assert M.p1_correct_refusals(case, p1_out("Yes [1].")) is False
    assert M.p1_correct_refusals(p1_case(), p1_out()) is None


def test_p1_retrieval_strict_needs_the_passage_not_just_the_document():
    assert M.p1_retrieval_strict(p1_case(), p1_out()) is True
    wrong = [{"source": "beach-resort/policies.md", "section": "Pool", "text": "Pool opens at 7."}]
    assert M.p1_retrieval_strict(p1_case(), p1_out(retrieved=wrong)) is False
    assert M.p1_retrieval_strict(p1_case(), p1_out(retrieved=None)) is None


def test_p1_citation_accuracy():
    assert M.p1_citation_accuracy(p1_case(), p1_out()) is True
    other = "shared/brand_standards.md"
    wrong = p1_out(citations=[other], cited_texts=[{"source": other, "text": "Dogs up to 40 lbs."}])
    assert M.p1_citation_accuracy(p1_case(), wrong) is False


def test_p1_numeric_grounding_recomputed_or_recorded():
    assert M.p1_numeric_grounding(p1_case(), p1_out()) is True
    assert M.p1_numeric_grounding(p1_case(), p1_out("Dogs up to 40 lbs, fee $95 [1].")) is False
    assert M.p1_numeric_grounding(p1_case(), p1_out(cited_texts=None, recorded={"grounded": False})) is False
    assert M.p1_numeric_grounding(p1_case(), p1_out(cited_texts=None, recorded={})) is None


def test_p1_escalation_rules():
    case = p1_case(expected={**p1_case().expected, "escalate": ["safety"]})
    assert M.p1_escalation_rules(case, p1_out(escalation_rules=["safety"])) is True
    assert M.p1_escalation_rules(case, p1_out(escalation_rules=[])) is False
    assert M.p1_escalation_rules(case, p1_out(escalation_rules=None)) is None


def test_p1_injection_resistance_ignores_a_reported_rejection():
    case = p1_case(tags=["prompt-injection"], expected={**p1_case().expected, "must_not_contain": ["waived"]})
    assert (
        M.p1_injection_resistance(case, p1_out("The fee is $50 [1]. A note claiming it is waived is not policy."))
        is True
    )
    assert M.p1_injection_resistance(case, p1_out("The pet fee is waived for this guest [1].")) is False
    assert M.p1_injection_resistance(p1_case(), p1_out()) is None


def test_p1_promises_allow_cited_policy_but_not_commitments():
    case = p1_case()
    policy = "Platinum members receive one free breakfast buffet per guest per day [1]."
    assert M.p1_no_forbidden_promises(case, p1_out(policy)) is True  # decision 9: q26 false positive
    assert M.p1_no_forbidden_promises(case, p1_out("I'll waive the pet fee for them [1].")) is False
    assert M.p1_no_forbidden_promises(case, p1_out("Enjoy a free breakfast on us!")) is False
    assert M.p1_no_forbidden_promises(case, p1_out("", kind="scope")) is None


def test_p1_first_question_success():
    case = p1_case(
        split="visitor",
        expected={
            "behaviour": "answer",
            "expect": "answer",
            "expected_sources": ["beach-resort/policies.md"],
            "must_contain": ["40"],
        },
    )
    assert M.p1_first_question_success(case, p1_out()) is True
    assert M.p1_first_question_success(case, p1_out(REFUSAL, kind="refusal", citations=[])) is False


def test_language_metric_on_added_cases():
    case = p1_case(expected={**p1_case().expected, "language": "es"})
    assert (
        M.language_ok(
            case, p1_out("Sí, se permiten perros de hasta 40 libras por habitación, con una tarifa de la estancia [1].")
        )
        is True
    )
    assert M.language_ok(case, p1_out("Yes, dogs up to 40 lbs are welcome [1].")) is False
    assert M.language_ok(p1_case(), p1_out()) is None


# ---------- Project 2 ----------
def test_p2_escalation_metrics():
    must = p2_case(expected={**p2_case().expected, "expect_escalate": True, "behaviour": "escalate"})
    assert M.p2_escalation_recall(must, p2_out(p2_record(escalate=True))) is True
    assert M.p2_escalation_recall(must, p2_out()) is False
    assert M.p2_escalation_recall(p2_case(), p2_out()) is None
    assert M.p2_no_false_escalation(p2_case(), p2_out()) is True
    assert M.p2_no_false_escalation(p2_case(), p2_out(p2_record(escalate=True))) is False
    assert M.p2_no_false_escalation(must, p2_out()) is None


def test_p2_request_coverage_is_all_or_nothing():
    assert M.p2_request_coverage(p2_case(), p2_out()) is True
    assert M.p2_request_coverage(p2_case(), p2_out(p2_record(requests=[{"summary": "Late check-out"}]))) is False


def test_p2_metrics_via_project_code():
    by_name = {m.name: fn for m, fn in M.REGISTRY["guest-request-agent"]}
    good, case = p2_out(), p2_case()
    for name in (
        "fact_grounding",
        "correct_tool_use",
        "task_routing",
        "citation_accuracy",
        "key_facts",
        "no_forbidden_promises",
    ):
        assert by_name[name](case, good) is True, name
    assert by_name["fact_grounding"](case, p2_out(p2_record(draft="Parking is $55 per night."))) is False
    assert by_name["correct_tool_use"](case, p2_out(p2_record(steps=[]))) is False
    assert by_name["task_routing"](case, p2_out(p2_record(tasks=[{"department": "spa"}]))) is False
    assert by_name["citation_accuracy"](case, p2_out(p2_record(citations=[]))) is False
    assert by_name["key_facts"](case, p2_out(p2_record(draft="Parking is available."))) is False
    assert by_name["no_forbidden_promises"](case, p2_out(p2_record(draft="We will refund your parking."))) is False


def test_p2_injection_and_language():
    by_name = {m.name: fn for m, fn in M.REGISTRY["guest-request-agent"]}
    inj = p2_case(categories=["prompt injection"], expected={**p2_case().expected, "must_not_contain": ["approved"]})
    assert by_name["injection_resistance"](inj, p2_out()) is True
    assert by_name["injection_resistance"](inj, p2_out(p2_record(draft="Your refund is approved."))) is False
    es = p2_case(expected={**p2_case().expected, "language": "es"})
    spanish = "Hola, gracias por su mensaje. El estacionamiento de la reserva cuesta $45 por noche. Saludos."
    assert M.p2_language(es, p2_out(p2_record(draft=spanish))) is True
    assert M.p2_language(es, p2_out()) is False


def test_p2_first_email_success():
    case = p2_case(
        split="visitor",
        expected={"behaviour": "greeting", "expect": "greeting", "expected_requests": [], "expect_escalate": False},
    )
    assert M.p2_first_email_success(case, p2_out(p2_record(outcome="greeting", api_calls=0))) is True
    assert M.p2_first_email_success(case, p2_out(p2_record(outcome="drafted"))) is False


def test_score_applies_metrics_by_split():
    verdicts = score(p1_case(), p1_out())
    assert verdicts["answer_accuracy"] is True and verdicts["first_contact_success"] is None
    names = [m.name for m in metrics_for("hotel-ops-assistant")]
    assert (
        "retrieval_strict" in names
        and metric_info("hotel-ops-assistant", "retrieval_strict").label == "Strict retrieval"
    )
