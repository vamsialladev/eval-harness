"""Import Project 1's and Project 2's labelled cases at their pinned commits into the shared schema.

    python scripts/import_cases.py            # writes src/hoteleval/data/cases/p1.jsonl and p2.jsonl
    python scripts/import_cases.py --check    # fails if the committed files differ from a fresh import (needs repos)

Reads the files with `git show <commit>:<path>` from the sibling checkouts, so a later edit in a project repo can't
change what the harness evaluates until the pin is moved on purpose. Cases added in Project 3 live in added.jsonl
and are written by hand.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hoteleval.cases import CASES_DIR  # noqa: E402
from hoteleval.importers import p1_question, p1_visitor, p2_email  # noqa: E402
from hoteleval.pins import PINS  # noqa: E402


def git_show(project: str, path: str) -> str:
    pin = PINS[project]
    repo = ROOT.parent / project
    out = subprocess.run(["git", "-C", str(repo), "show", f"{pin}:{path}"], capture_output=True, check=True)
    return out.stdout.decode("utf-8")


def jsonl(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def build() -> dict[str, list[dict]]:
    p1, p2 = "hotel-ops-assistant", "guest-request-agent"
    o1 = f"Project 1 {{path}} @ {PINS[p1][:7]}"
    o2 = f"Project 2 {{path}} @ {PINS[p2][:7]}"
    cases1 = [
        p1_question(i, o1.format(path="eval/questions.jsonl")) for i in jsonl(git_show(p1, "eval/questions.jsonl"))
    ]
    cases1 += [
        p1_visitor(i, o1.format(path="eval/visitor_questions.jsonl"))
        for i in jsonl(git_show(p1, "eval/visitor_questions.jsonl"))
    ]
    inbox = {e["id"]: e for e in jsonl(git_show(p2, "data/inbox.jsonl"))}
    cases2 = []
    for path, split in (
        ("eval/cases.jsonl", "dev"),
        ("eval/heldout.jsonl", "held-out"),
        ("eval/visitor.jsonl", "visitor"),
    ):
        cases2 += [p2_email(i, inbox, split, o2.format(path=path)) for i in jsonl(git_show(p2, path))]
    return {"p1.jsonl": [c.to_dict() for c in cases1], "p2.jsonl": [c.to_dict() for c in cases2]}


def render(rows: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    built = build()
    stale = []
    for name, rows in built.items():
        path = CASES_DIR / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != render(rows):
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render(rows), encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(ROOT)}: {len(rows)} cases")
    if stale:
        print(f"FAIL: {', '.join(stale)} differ from a fresh import at the pinned commits")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
