"""Project 2 driver. Runs INSIDE a Project 2 tree (cwd) with Project 2's own Python: the real agent at the pinned
commit, called exactly as Project 2's eval does (eval/run_eval.py run_live). Imports only Project 2 code and stdlib.

    python p2_driver.py --cases cases.jsonl --out out.jsonl --runs 3
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime

sys.path.insert(0, os.getcwd())

VISITOR_SENDER = "visitor@example.com"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--label", default="harness")
    args = parser.parse_args(argv)

    from src.agent import Email
    from src.config import LLM_EFFORT, LLM_MODEL
    from src.service import process

    from src import policy_search

    cases = [json.loads(line) for line in open(args.cases, encoding="utf-8") if line.strip()]
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"settings": {"model": LLM_MODEL, "effort": LLM_EFFORT}}) + "\n")
        for run in range(1, args.runs + 1):
            for case in cases:
                e, prop = case["input"]["email"], case["property"]
                email = Email(
                    sender=e.get("from") or VISITOR_SENDER,
                    subject=e.get("subject", ""),
                    body=e["body"],
                    sender_name=e.get("name", ""),
                )
                result, record = process(
                    email,
                    prop,
                    source="write" if case["split"] == "visitor" else "eval",
                    session_id=f"eval-{args.label}-{run}",
                    log=False,
                    email_id=case["id"],
                    keyword_matches=lambda text, p=prop: policy_search.keyword_matches(text, p),
                )
                record = {**record, "sources": result.sources}
                row = {
                    "set": case["split"],
                    "label": args.label,
                    "run": run,
                    "case_id": case["id"],
                    "record": record,
                    "time": datetime.now(UTC).isoformat(timespec="seconds"),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                print(f"run {run} {case['id']}: {record['outcome']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
