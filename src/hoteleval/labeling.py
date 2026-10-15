"""Calibration items and human labels.

`sample_items` draws 40 stratified items: 20 per project; per project 7 completeness, 7 tone and 6 clarity items;
inside each cell about half are outputs a deterministic metric flagged (so real failures are in the sample) and half
are not. Only model-written text is sampled (no templates: scope messages, rule escalations, fallbacks). Each output
appears once. The sample is seeded, so `hoteleval sample-labels` rebuilds the same items.

Labels are the owner's: the labeling page appends one line per click to labels/human-labels.jsonl; the latest line per
item wins. Nothing here ever writes a label.
"""

import json
import random
from datetime import UTC, datetime
from pathlib import Path

from hoteleval import store
from hoteleval.cases import by_id
from hoteleval.metrics import score
from hoteleval.rubric import DIMENSIONS

LABELS_DIR = store.ROOT / "labels"
ITEMS_FILE = LABELS_DIR / "items.jsonl"
LABELS_FILE = LABELS_DIR / "human-labels.jsonl"
POOL_RUNS = {
    "hotel-ops-assistant": ["p1-published-2026-10-10", "p1-model-comparison-haiku-4-5"],
    "guest-request-agent": ["p2-published-2026-10-14", "p2-dev-2026-10-14", "p2-dev2-2026-10-14"],
}
PLAN = {"completeness": 7, "tone": 7, "clarity": 6}
SEED = 2026
SHORT = {"hotel-ops-assistant": "p1", "guest-request-agent": "p2"}


def reply_text(out: dict) -> str:
    return out.get("final_text") or out.get("text") or ""


def judgeable(out: dict) -> bool:
    """Model-written text only: no scope messages, greetings, rule escalations or fallback templates."""
    if not reply_text(out).strip() or not out.get("api_calls"):
        return False
    if out["project"] == "hotel-ops-assistant":
        return out["kind"] in ("answer", "refusal")
    native = out.get("native") or {}
    return out["kind"] in ("drafted", "escalated") and not native.get("fallback_reason")


def input_text(case, out: dict) -> str:
    if "question" in case.input:
        return case.input["question"]
    e = case.input["email"]
    sender = f"{e.get('name') or 'Guest'} <{e.get('from') or 'visitor@example.com'}>"
    return f"From: {sender}\nSubject: {e.get('subject') or '(none)'}\n\n{e['body']}"


def candidates(project: str, runs_dir: Path | None = None) -> list[dict]:
    cases = by_id(project)
    pool = []
    for run_id in POOL_RUNS[project]:
        outputs, _ = store.load_run(run_id, runs_dir)
        for out in outputs:
            case = cases.get(out["case_id"])
            if case is None or not judgeable(out):
                continue
            verdicts = score(case, out)
            pool.append({"out": out, "case": case, "flagged": any(v is False for v in verdicts.values())})
    return pool


def sample_items(runs_dir: Path | None = None, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    items = []
    for project in POOL_RUNS:
        pool = candidates(project, runs_dir)
        rng.shuffle(pool)
        used_cases: set[str] = set()
        for dim in DIMENSIONS:
            want = PLAN[dim]
            picked = []
            # about half flagged, then unflagged, then whatever is left if a group runs short
            for flagged, limit in ((True, (want + 1) // 2), (False, want), (True, want)):
                for c in pool:
                    if len(picked) >= limit:
                        break
                    if c["flagged"] == flagged and c["case"].id not in used_cases:
                        picked.append(c)
                        used_cases.add(c["case"].id)
            for n, c in enumerate(picked, 1):
                out, case = c["out"], c["case"]
                items.append(
                    {
                        "item_id": f"{SHORT[project]}-{dim}-{n:02d}",
                        "project": project,
                        "dimension": dim,
                        "run_id": out["run_id"],
                        "case_id": case.id,
                        "run": out["run"],
                        "property": case.property,
                        "input": input_text(case, out),
                        "reply": reply_text(out),
                        "flagged": c["flagged"],
                    }
                )
    rng.shuffle(items)  # mixed order on the labeling page, so dimensions and projects alternate
    return items


def load_items(path: Path = ITEMS_FILE) -> list[dict]:
    return store.read_jsonl(path) if Path(path).exists() else []


def load_labels(path: Path = LABELS_FILE) -> dict[str, dict]:
    """item_id -> latest label line."""
    latest: dict[str, dict] = {}
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                latest[row["item_id"]] = row
    return latest


def append_label(item_id: str, label: str, reason: str = "", path: Path = LABELS_FILE) -> dict:
    """Called only by the labeling page, on the owner's click."""
    if label not in ("pass", "fail"):
        raise ValueError("label must be pass or fail")
    row = {
        "item_id": item_id,
        "label": label,
        "reason": reason.strip(),
        "labeled_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "labeler": "Vamsi Alla",
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def next_unlabeled(items: list[dict], labels: dict) -> int | None:
    for i, item in enumerate(items):
        if item["item_id"] not in labels:
            return i
    return None
