"""hoteleval command line. Recorded mode is the default; only `run-live` and `judge --live` call the API.

hoteleval gate --project guest-request-agent --recorded eval/recorded/main-final.jsonl   # in a project's CI
hoteleval import-run --project hotel-ops-assistant --native X.jsonl --run-id ID --repo ../hotel-ops-assistant
hoteleval run-live --project hotel-ops-assistant --repo ../hotel-ops-assistant --ref 5f9cd91 --runs 3 --run-id ID
hoteleval score --run-id ID --baseline BASE_ID
hoteleval baseline --run-id ID          # bundle a scored run as the project's baseline
hoteleval index                         # rebuild reports/index.json for the dashboard
"""

import argparse
import sys
import tempfile
from datetime import date
from pathlib import Path

from hoteleval import gates, report, runner, store
from hoteleval.adapters import from_p2
from hoteleval.pins import PINS
from hoteleval.scoring import score_run

PROJECTS = ("hotel-ops-assistant", "guest-request-agent")


def _p1_rows(native: list[Path], project_root: Path | None, python: Path | None, ref: str | None, work: Path):
    """Project 1 native answer rows, with retrieval and escalation recomputed by Project 1's own code when a
    project tree is available (no API)."""
    tmp = Path(tempfile.mkdtemp(prefix="hoteleval-", dir=work if work.exists() else None))
    answers = tmp / "answers.jsonl"
    answers.write_text("".join(Path(p).read_text(encoding="utf-8") for p in native), encoding="utf-8")
    if project_root is None:
        rows = [{"row": r, "extras": {}} for r in store.read_jsonl(answers)]
        return {}, rows
    tree = runner.export(project_root, ref, work) if ref else project_root
    python = python or (runner.project_python(project_root) if ref else Path(sys.executable))
    env = runner.child_env(None)
    if ref:
        runner.setup("hotel-ops-assistant", tree, python, env)
    elif not (tree / "data" / "index" / "chunks.json").exists():
        runner.setup("hotel-ops-assistant", tree, python, env)
    cases = tmp / "cases.jsonl"
    runner.write_cases(cases, "hotel-ops-assistant", splits=("dev", "held-out"))
    out = tmp / "driver.jsonl"
    runner.run_driver(
        "hotel-ops-assistant",
        tree,
        python,
        ["--cases", str(cases), "--out", str(out), "--answers-from", str(answers)],
        env,
    )
    return runner.read_driver_output(out)


def build_outputs(project: str, native: list[Path], run_id: str, project_root=None, ref=None, work=None):
    work = work or store.ROOT / ".work"
    if project == "hotel-ops-assistant":
        settings, rows = _p1_rows(native, project_root, None, ref, work)
        return settings, runner.convert(project, rows, run_id)
    rows = [r for p in native for r in store.read_jsonl(p)]
    return {}, [from_p2(r, run_id) for r in rows]


def cmd_import_run(args) -> int:
    root = Path(args.repo).resolve() if args.repo else None
    settings, outputs = build_outputs(args.project, args.native, args.run_id, root, args.ref)
    meta = _meta(args, "imported", settings)
    meta["source"] = ", ".join(f"`{Path(p).as_posix()}`" for p in args.native) + (
        f" @ {args.ref[:7]}" if args.ref else ""
    )
    path = store.save_run(outputs, meta)
    print(f"saved {len(outputs)} outputs to runs/{path.name}")
    return 0


def _meta(args, mode: str, settings: dict) -> dict:
    meta = {
        "run_id": args.run_id,
        "project": args.project,
        "label": args.label or args.run_id,
        "date": args.date or date.today().isoformat(),
        "mode": mode,
        "kind": args.kind,
        "model": settings.get("model") or args.model,
        "settings": {k: v for k, v in settings.items() if k != "model"},
        "price_in": args.price_in,
        "price_out": args.price_out,
        "description": args.description,
        "ref": getattr(args, "ref", None),
    }
    if getattr(args, "published", None):
        meta["published"] = dict(kv.split("=", 1) for kv in args.published)
    return meta


def cmd_run_live(args) -> int:
    repo = Path(args.repo).resolve()
    work = store.ROOT / ".work"
    tree = runner.export(repo, args.ref, work)
    python = runner.project_python(repo)
    env = runner.child_env(Path(args.env))
    if "ANTHROPIC_API_KEY" not in env:
        print("ANTHROPIC_API_KEY is not set in the .env file (the key is never printed).")
        return 2
    runner.setup(args.project, tree, python, env)
    tmp = Path(tempfile.mkdtemp(prefix="hoteleval-", dir=work))
    cases = runner.write_cases(tmp / "cases.jsonl", args.project, splits=args.splits, ids=args.ids)
    out = tmp / "driver.jsonl"
    driver_args = ["--cases", str(tmp / "cases.jsonl"), "--out", str(out), "--runs", str(args.runs)]
    if args.project == "hotel-ops-assistant":
        driver_args.append("--live")
    else:
        driver_args += ["--label", args.run_id]
    print(f"running {len(cases)} cases x {args.runs} run(s) at {runner.resolve(repo, args.ref)[:7]}")
    runner.run_driver(args.project, tree, python, driver_args, env)
    settings, rows = runner.read_driver_output(out)
    outputs = runner.convert(args.project, rows, args.run_id)
    meta = _meta(args, "live", settings)
    meta["source"] = f"live run of {repo.name} @ {runner.resolve(repo, args.ref)[:7]}"
    meta["ref"] = runner.resolve(repo, args.ref)
    path = store.save_run(outputs, meta)
    print(f"saved {len(outputs)} outputs to runs/{path.name}")
    return 0


def baseline_for(project: str) -> dict:
    return store.read_json(store.BASELINES / f"{project}.json")


def cmd_score(args) -> int:
    outputs, meta = store.load_run(args.run_id)
    summary = score_run(outputs, meta)
    if args.baseline:
        base = store.read_json(store.REPORTS / f"{args.baseline}.json")
        summary["gate"] = gates.compare(base, summary)
    store.write_json(store.REPORTS / f"{args.run_id}.json", summary)
    (store.REPORTS / f"{args.run_id}.md").write_text(report.render(summary), encoding="utf-8", newline="\n")
    store.rebuild_index()
    print(f"report: reports/{args.run_id}.md")
    if summary.get("gate"):
        print(gates.summary_line(summary["gate"]))
        for f in summary["gate"]["failures"]:
            print(f"  - {f}")
        return 0 if summary["gate"]["passed"] or args.no_fail else 1
    return 0


def cmd_baseline(args) -> int:
    summary = store.read_json(store.REPORTS / f"{args.run_id}.json")
    summary.pop("gate", None)
    store.write_json(store.BASELINES / f"{summary['meta']['project']}.json", summary)
    print(f"baseline for {summary['meta']['project']}: {args.run_id}")
    return 0


def cmd_gate(args) -> int:
    """One shot for a project's CI: recorded outputs (the project's own format, or a run saved in this repo) ->
    score -> compare with the bundled baseline."""
    if args.saved:
        outputs, meta = store.load_run(args.saved)
        args.project = meta["project"]
        summary = score_run(outputs, meta)
    elif args.recorded and args.project:
        root = Path(args.project_root).resolve() if args.project_root else None
        run_id = args.run_id or "candidate"
        settings, outputs = build_outputs(args.project, [Path(p) for p in args.recorded], run_id, root, None)
        meta = {"run_id": run_id, "project": args.project, "mode": "replay", "date": date.today().isoformat()}
        summary = score_run(outputs, {**meta, "settings": settings})
    else:
        print("gate needs --saved RUN_ID, or --project with --recorded FILE")
        return 2
    result = gates.compare(baseline_for(args.project), summary)
    print(f"hoteleval gate · {args.project} · {len(outputs)} recorded outputs")
    for ch in result["checks"]:
        mark = {"pass": "ok  ", "fail": "FAIL", "skipped": "skip"}[ch["status"]]
        cand = "–" if ch["candidate"] is None else f"{ch['candidate']:.0%}"
        print(f"  {mark} {ch['split']:<8} {ch['metric']:<22} {cand:>5}  ({ch['cases']} cases)")
    print(gates.summary_line(result))
    for f in result["failures"]:
        print(f"  - {f}")
    return 0 if result["passed"] else 1


def cmd_index(args) -> int:
    entries = store.rebuild_index()
    print(f"index: {len(entries)} runs")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="hoteleval", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    def run_args(p):
        p.add_argument("--project", choices=PROJECTS, required=True)
        p.add_argument("--run-id", required=True)
        p.add_argument("--label")
        p.add_argument("--date")
        p.add_argument("--kind", default="candidate", choices=("baseline", "candidate", "history", "demo"))
        p.add_argument("--model")
        p.add_argument("--description")
        p.add_argument("--price-in", type=float, help="USD per million input tokens")
        p.add_argument("--price-out", type=float, help="USD per million output tokens")

    p = sub.add_parser("import-run", help="convert a project's recorded outputs into a harness run")
    run_args(p)
    p.add_argument("--native", nargs="+", type=Path, required=True)
    p.add_argument("--repo", help="project checkout (Project 1: recompute retrieval and escalation, no API)")
    p.add_argument("--ref", help="git ref to export from --repo (default: the pinned commit)")
    p.add_argument("--published", nargs="*", help="key=value numbers the project reported for this run")
    p.set_defaults(fn=cmd_import_run)

    p = sub.add_parser("run-live", help="run a project's real pipeline at a git ref (uses the API)")
    run_args(p)
    p.add_argument("--repo", required=True)
    p.add_argument("--ref")
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--splits", nargs="*")
    p.add_argument("--ids", nargs="*")
    p.add_argument("--env", default=".env")
    p.set_defaults(fn=cmd_run_live)

    p = sub.add_parser("score", help="score a saved run and write its report")
    p.add_argument("--run-id", required=True)
    p.add_argument("--baseline", help="run ID of the baseline to gate against")
    p.add_argument("--no-fail", action="store_true", help="exit 0 even when the gate fails (demo reports)")
    p.set_defaults(fn=cmd_score)

    p = sub.add_parser("baseline", help="bundle a scored run as its project's baseline")
    p.add_argument("--run-id", required=True)
    p.set_defaults(fn=cmd_baseline)

    p = sub.add_parser("gate", help="score recorded outputs and gate them against the bundled baseline")
    p.add_argument("--project", choices=PROJECTS)
    p.add_argument("--recorded", nargs="+", help="the project's own recorded outputs (JSONL)")
    p.add_argument("--saved", help="a run saved in this repo's runs/ folder")
    p.add_argument("--project-root", help="Project 1 tree: recompute retrieval and escalation (no API)")
    p.add_argument("--run-id")
    p.set_defaults(fn=cmd_gate)

    p = sub.add_parser("index", help="rebuild reports/index.json")
    p.set_defaults(fn=cmd_index)

    from hoteleval import judge_cli

    judge_cli.register(sub)

    args = parser.parse_args(argv)
    if getattr(args, "cmd", None) in ("import-run", "run-live") and not getattr(args, "ref", None):
        args.ref = PINS[args.project]
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
