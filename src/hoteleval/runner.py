"""Run a project's real pipeline at a pinned git ref, or re-score its recorded outputs.

Live mode exports the ref with `git archive` into .work/ (the project checkout is never touched), runs the project's
setup (index, synthetic data), then runs a driver with the project's own virtualenv Python. The API key comes from
the harness .env and is passed only through the child's environment: never printed, logged or written.
"""

import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

from hoteleval.adapters import from_p1, from_p2
from hoteleval.cases import load_cases

DRIVERS = Path(__file__).resolve().parent / "drivers"
SETUP = {
    "hotel-ops-assistant": [["-m", "src.ingest", "--bm25-only"]],
    "guest-request-agent": [["scripts/make_data.py"], ["-m", "src.policy.ingest", "--bm25-only"]],
}


class RunnerError(RuntimeError):
    pass


def project_python(repo: Path) -> Path:
    for rel in (".venv/Scripts/python.exe", ".venv/bin/python"):
        if (repo / rel).exists():
            return repo / rel
    return Path(sys.executable)


def resolve(repo: Path, ref: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), "rev-parse", ref], capture_output=True, text=True)
    if out.returncode:
        raise RunnerError(f"unknown ref {ref!r} in {repo}")
    return out.stdout.strip()


def export(repo: Path, ref: str, work: Path) -> Path:
    sha = resolve(repo, ref)
    target = work / f"{repo.name}-{sha[:10]}"
    if not target.exists():
        data = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", sha], capture_output=True, check=True)
        target.mkdir(parents=True)
        with tarfile.open(fileobj=io.BytesIO(data.stdout)) as tar:
            tar.extractall(target, filter="data")
    return target


def child_env(env_file: Path | None) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("STREAMLIT_",))}
    if env_file and env_file.exists():
        from dotenv import dotenv_values

        key = dotenv_values(env_file).get("ANTHROPIC_API_KEY")
        if key:
            env["ANTHROPIC_API_KEY"] = key
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_driver(project: str, tree: Path, python: Path, args: list[str], env: dict) -> None:
    driver = DRIVERS / ("p1_driver.py" if project == "hotel-ops-assistant" else "p2_driver.py")
    proc = subprocess.run([str(python), str(driver), *args], cwd=tree, env=env)
    if proc.returncode:
        raise RunnerError(f"{project} driver failed with exit code {proc.returncode}")


def setup(project: str, tree: Path, python: Path, env: dict) -> None:
    for step in SETUP[project]:
        proc = subprocess.run([str(python), *step], cwd=tree, env=env, capture_output=True, text=True)
        if proc.returncode:
            raise RunnerError(f"setup step {' '.join(step)} failed: {proc.stderr[-500:]}")


def write_cases(path: Path, project: str, splits=None, ids=None) -> list:
    cases = [c for c in load_cases(project) if (not splits or c.split in splits) and (not ids or c.id in set(ids))]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(c.to_dict(), ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    return cases


def read_driver_output(path: Path) -> tuple[dict, list[dict]]:
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if lines and "settings" in lines[0]:
        return lines[0]["settings"], lines[1:]
    return {}, lines


def convert(project: str, rows: list[dict], run_id: str) -> list[dict]:
    if project == "hotel-ops-assistant":
        return [from_p1(r["row"], run_id, r["extras"]) for r in rows]
    return [from_p2(r, run_id) for r in rows]
