"""Project 1 driver. Runs INSIDE a Project 1 tree (cwd) with Project 1's own Python, so the real pipeline at the
pinned commit produces the outputs. Standalone on purpose: it imports only Project 1 code and the stdlib.

    python p1_driver.py --cases cases.jsonl --out out.jsonl --runs 3 --live      # real answers (API)
    python p1_driver.py --cases cases.jsonl --out out.jsonl --answers-from x.jsonl   # recorded answers, no API

Retrieval, the scope check and the escalation rules are deterministic and always recomputed here (free).
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.getcwd())

from src.config import LLM_EFFORT, LLM_MODEL, TOP_K  # noqa: E402
from src.escalation import escalation_ids  # noqa: E402
from src.retrieve import Retriever  # noqa: E402
from src.service import blocked_result, prepare  # noqa: E402


def passage(c: dict) -> dict:
    return {"source": c["source"], "section": c.get("section", ""), "text": c["text"]}


def deterministic(retriever, case: dict) -> dict:
    q, prop = case["input"]["question"], case["property"]
    hits = retriever.search(q, prop, k=TOP_K)
    prep = prepare(retriever, q, prop)
    return {"retrieved": [passage(h) for h in hits], "escalation_rules": escalation_ids(q, prop), "prep": prep}


def live_question(case: dict, prep: dict) -> tuple[dict, dict]:
    from src.generate import AnswerStream

    q, prop = case["input"]["question"], case["property"]
    if prep["blocked"]:
        try:  # Project 1 >= 1.6.0 answers the scope message in the question's language
            result = blocked_result(q)
        except TypeError:
            result = blocked_result()
        ttft, total, calls = 0.0, 0.0, 0
    else:
        stream = AnswerStream(q, prop, prep["hits"])
        try:
            result = stream.run()
            ttft, total, calls = stream.time_to_first_token, stream.total_time, 1
        except Exception as exc:  # noqa: BLE001 - a failed call is a failed answer, never a crashed run (Project 4)
            print(f"  call failed: {type(exc).__name__}", flush=True)
            result = {"answer": "", "found": True, "citations": [], "usage": {"input_tokens": 0, "output_tokens": 0}}
            ttft, total, calls = None, None, 1
    row = {
        "answer": result["answer"],
        "cited": [c["source"] for c in result["citations"]],
        "pre_api": prep["blocked"],
    }
    extras = {
        "cited_texts": [passage(c) for c in result["citations"]],
        "latency_s": total,
        "ttft_s": ttft,
        "tokens_in": result["usage"]["input_tokens"],
        "tokens_out": result["usage"]["output_tokens"],
        "api_calls": calls,
    }
    return row, extras


def live_visitor(retriever, case: dict) -> tuple[dict, dict]:
    from src.assist import respond

    q, prop = case["input"]["question"], case["property"]
    start = time.perf_counter()
    out = respond(retriever, q, prop, use_api=True)
    total = time.perf_counter() - start
    called = out["kind"] in ("answer", "refusal")
    usage = out.get("usage") or {"input_tokens": 0, "output_tokens": 0}
    row = {
        "answer": out.get("answer", ""),
        "cited": [c["source"] for c in out.get("citations", [])],
        "pre_api": not called,
    }
    extras = {
        "kind": out["kind"],
        "suggestions": len(out.get("suggestions", [])),
        "cited_texts": [passage(c) for c in out.get("citations", [])],
        "latency_s": total if called else None,
        "tokens_in": usage["input_tokens"],
        "tokens_out": usage["output_tokens"],
        "api_calls": 1 if called else 0,
    }
    return row, extras


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--answers-from")
    args = parser.parse_args(argv)

    cases = [json.loads(line) for line in open(args.cases, encoding="utf-8") if line.strip()]
    retriever = Retriever(use_embeddings=False)
    det = {c["id"]: deterministic(retriever, c) for c in cases if c["split"] != "visitor"}
    recorded = {}
    if args.answers_from:
        for line in open(args.answers_from, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                recorded[(r["run"], r["id"])] = r
    settings = {"top_k": TOP_K, "retrieval": retriever.mode, "model": LLM_MODEL, "effort": LLM_EFFORT or "default"}
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"settings": settings}) + "\n")
        runs = sorted({r for r, _ in recorded}) if recorded else range(1, args.runs + 1)
        for run in runs:
            for case in cases:
                d = det.get(case["id"], {})
                extras = {k: d[k] for k in ("retrieved", "escalation_rules") if k in d}
                if recorded:
                    row = recorded.get((run, case["id"]))
                    if row is None:
                        continue
                elif args.live and case["split"] == "visitor":
                    row, more = live_visitor(retriever, case)
                    extras.update(more)
                elif args.live:
                    row, more = live_question(case, d["prep"])
                    extras.update(more)
                else:
                    continue
                row = {**row, "run": run, "id": case["id"]}
                f.write(json.dumps({"row": row, "extras": extras}, ensure_ascii=False) + "\n")
                f.flush()
                if args.live:
                    print(
                        f"run {run} {case['id']}: {extras.get('kind') or ('scope' if row['pre_api'] else 'api')}",
                        flush=True,
                    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
