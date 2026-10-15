"""Files: recorded runs (runs/), reports (reports/) and the run index the dashboard reads. UTF-8, LF, stable order."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
BASELINES = Path(__file__).resolve().parent / "data" / "baselines"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_run(outputs: list[dict], meta: dict, runs_dir: Path | None = None) -> Path:
    runs_dir = runs_dir or RUNS
    path = runs_dir / f"{meta['run_id']}.jsonl"
    write_jsonl(path, sorted(outputs, key=lambda o: (o["run"], o["case_id"])))
    write_json(runs_dir / f"{meta['run_id']}.meta.json", meta)
    return path


def load_run(run_id: str, runs_dir: Path | None = None) -> tuple[list[dict], dict]:
    runs_dir = runs_dir or RUNS
    return read_jsonl(runs_dir / f"{run_id}.jsonl"), read_json(runs_dir / f"{run_id}.meta.json")


def index_entry(summary: dict) -> dict:
    meta = summary["meta"]
    entry = {k: meta.get(k) for k in ("run_id", "project", "label", "date", "mode", "kind", "model", "description")}
    entry["splits"] = {
        split: {
            "cases": s["cases"],
            "runs": s["runs"],
            "metrics": {name: {"rate": m["rate"], "ci": m["ci"]} for name, m in s["metrics"].items()},
            "p95_s": s["latency"]["p95_s"],
            "cost_per_1000": s["cost_per_1000"],
        }
        for split, s in summary["splits"].items()
    }
    gate = summary.get("gate")
    entry["gate"] = (
        {"baseline": gate["baseline"], "passed": gate["passed"], "failures": gate["failures"]} if gate else None
    )
    return entry


def rebuild_index(reports_dir: Path | None = None) -> list[dict]:
    reports_dir = reports_dir or REPORTS
    entries = []
    for path in sorted(reports_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        data = read_json(path)
        if "meta" in data and "splits" in data:
            entries.append(index_entry(data))
    entries.sort(key=lambda e: (e["project"], e["date"] or "", e["run_id"]))
    write_json(reports_dir / "index.json", entries)
    return entries
