"""Turn each project's own recorded outputs into one output record the harness scores, shows and judges.

Project 1 rows (eval/reports/*_answers_*.jsonl) hold the answer, cited documents and Project 1's own verdicts.
Retrieval, the scope check and the escalation rules are deterministic, so `extras` (from the Project 1 driver, no API)
adds them back. Project 2 rows (eval/recorded/*.jsonl) hold the full request-log record, kept as `native`.
"""

P1_NOT_FOUND = "I couldn't find this in the hotel's documents. Please check with a manager."  # src/generate.py
P1, P2 = "hotel-ops-assistant", "guest-request-agent"


def output(project: str, run_id: str, case_id: str, run: int, **fields) -> dict:
    base = {
        "run_id": run_id,
        "project": project,
        "case_id": case_id,
        "run": run,
        "kind": None,
        "text": "",
        "final_text": None,
        "refused": False,
        "citations": [],
        "cited_texts": None,
        "retrieved": None,
        "escalated": None,
        "escalation_rules": None,
        "suggestions": None,
        "latency_s": None,
        "ttft_s": None,
        "tokens_in": 0,
        "tokens_out": 0,
        "api_calls": 0,
        "recorded": {},
        "native": None,
    }
    unknown = set(fields) - set(base)
    if unknown:
        raise KeyError(f"unknown output fields: {', '.join(sorted(unknown))}")
    return {**base, **fields}


def p1_refused(row: dict) -> bool:
    """Project 1's refusal rule: blocked before the API, or the fixed sentence with no citation (is_refusal)."""
    return bool(row.get("pre_api")) or (P1_NOT_FOUND in (row.get("answer") or "") and not row.get("cited"))


def from_p1(row: dict, run_id: str, extras: dict | None = None) -> dict:
    """One Project 1 answer row (+ deterministic extras for its case) -> output record."""
    extras = extras or {}
    refused = p1_refused(row)
    kind = extras.get("kind") or ("scope" if row.get("pre_api") else ("refusal" if refused else "answer"))
    return output(
        P1,
        run_id,
        row["id"],
        int(row.get("run", 1)),
        kind=kind,
        text=row.get("answer") or "",
        refused=refused,
        citations=list(row.get("cited") or []),
        cited_texts=extras.get("cited_texts"),
        retrieved=extras.get("retrieved"),
        escalation_rules=extras.get("escalation_rules"),
        escalated=bool(extras["escalation_rules"]) if extras.get("escalation_rules") is not None else None,
        suggestions=extras.get("suggestions"),
        latency_s=extras.get("latency_s"),
        ttft_s=extras.get("ttft_s"),
        tokens_in=extras.get("tokens_in", 0),
        tokens_out=extras.get("tokens_out", 0),
        api_calls=extras.get("api_calls", 0 if row.get("pre_api") else 1),
        recorded={k: row[k] for k in ("correct", "citation_ok", "grounded", "ungrounded") if k in row},
    )


def from_p2(row: dict, run_id: str) -> dict:
    """One Project 2 recorded row ({set, label, run, case_id, record}) -> output record."""
    rec = row["record"]
    outcome = rec.get("outcome")
    return output(
        P2,
        run_id,
        row["case_id"],
        int(row.get("run", 1)),
        kind=outcome,
        text=rec.get("raw_draft") or rec.get("draft") or rec.get("message") or "",
        final_text=rec.get("draft"),
        refused=outcome in ("greeting", "off_topic"),
        citations=[f"{c.get('title')} > {c.get('section')}" for c in rec.get("citations", [])],
        escalated=bool(rec.get("escalate")),
        latency_s=rec.get("latency_s"),
        tokens_in=rec.get("tokens_in", 0),
        tokens_out=rec.get("tokens_out", 0),
        api_calls=rec.get("api_calls", 0),
        native=rec,
    )
