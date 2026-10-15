"""Load the case bank shipped with the package (so a project's CI can install the harness and use it as is)."""

import json
from functools import lru_cache
from pathlib import Path

from hoteleval.schema import Case, check_unique, validate

CASES_DIR = Path(__file__).resolve().parent / "data" / "cases"
FILES = ("p1.jsonl", "p2.jsonl", "added.jsonl")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


@lru_cache(maxsize=1)
def _all() -> tuple[Case, ...]:
    cases = []
    for name in FILES:
        path = CASES_DIR / name
        if path.exists():
            cases += [validate(row) for row in read_jsonl(path)]
    check_unique(cases)
    return tuple(cases)


def load_cases(project: str | None = None, split: str | None = None) -> list[Case]:
    return [c for c in _all() if (project is None or c.project == project) and (split is None or c.split == split)]


def by_id(project: str) -> dict[str, Case]:
    return {c.id: c for c in load_cases(project)}
