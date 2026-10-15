"""Judge and calibration commands (registered on the main CLI).

hoteleval sample-labels                     # rebuild labels/items.jsonl (seeded, same result every time)
hoteleval judge --rubric v1 --live          # judge the 40 calibration items (API, cached by input hash)
hoteleval judge --rubric v1 --run RUN_ID --live   # judge run 1 of a saved run (reported, never a gate)
hoteleval calibrate                         # judge vs your labels for every rubric version judged (free)
"""

from pathlib import Path

from hoteleval import labeling, store
from hoteleval.calibration import TRUST_KAPPA, calibrate
from hoteleval.judge import JUDGE_DIR, Cache, JudgeError, cost, judge
from hoteleval.labeling import input_text, judgeable, load_items, load_labels, reply_text, sample_items
from hoteleval.rubric import DIMENSIONS, load_rubric, versions

CACHE_FILE = JUDGE_DIR / "cache.jsonl"


def client_from_env(env_file: Path):
    import anthropic
    from dotenv import dotenv_values

    key = dotenv_values(env_file).get("ANTHROPIC_API_KEY")
    if not key:
        raise JudgeError("ANTHROPIC_API_KEY is not set in .env (the key is never printed)")
    return anthropic.Anthropic(api_key=key, max_retries=3)


def run_items(version: str, items: list[dict], live: bool, env: Path, repeat: int = 0) -> tuple[dict, list[dict]]:
    cache = Cache(CACHE_FILE)
    client = client_from_env(env) if live else None
    verdicts, rows, missing = {}, [], 0
    for item in items:
        row = judge(item, version, cache, client, live, repeat)
        if row is None:
            missing += 1
            continue
        verdicts[item["ref"]] = row["verdicts"]
        rows.append(row)
    if missing:
        print(f"{missing} item(s) not in the cache; run with --live to judge them (uses the API)")
    return verdicts, rows


def cmd_sample(args) -> int:
    items = sample_items()
    store.write_jsonl(labeling.ITEMS_FILE, items)
    print(f"wrote {len(items)} items to labels/{labeling.ITEMS_FILE.name}")
    return 0


def cmd_judge(args) -> int:
    load_rubric(args.rubric)
    env = Path(args.env)
    if args.run:
        outputs, meta = store.load_run(args.run)
        from hoteleval.cases import by_id

        cases = by_id(meta["project"])
        items = [
            {
                "ref": o["case_id"],
                "project": o["project"],
                "input": input_text(cases[o["case_id"]], o),
                "reply": reply_text(o),
            }
            for o in outputs
            if o["run"] == 1 and judgeable(o) and o["case_id"] in cases
        ]
        verdicts, rows = run_items(args.rubric, items, args.live, env)
        rates = {d: _rate([v[d]["verdict"] for v in verdicts.values()]) for d in DIMENSIONS}
        store.write_json(
            JUDGE_DIR / f"run-{args.run}-{args.rubric}.json",
            {
                "run_id": args.run,
                "rubric": args.rubric,
                "outputs": len(items),
                "pass_rates": rates,
                "verdicts": verdicts,
            },
        )
        print(
            f"judged {len(verdicts)}/{len(items)} outputs of {args.run}: "
            + ", ".join(f"{d} {r:.0%}" for d, r in rates.items() if r is not None)
        )
    else:
        items_file, _ = round_files(args.round)
        items = [{**i, "ref": i["item_id"]} for i in load_items(items_file)]
        verdicts, rows = run_items(args.rubric, items, args.live, env, args.repeat)
        suffix = ("" if args.round == 1 else f"-round{args.round}") + (f"-repeat{args.repeat}" if args.repeat else "")
        store.write_json(JUDGE_DIR / f"items-{args.rubric}{suffix}.json", verdicts)
        print(f"judged {len(verdicts)}/{len(items)} round-{args.round} calibration items with rubric {args.rubric}")
    print(f"judge tokens for these items: ${cost(rows):.4f} at $0.10/$0.50 per million (cached calls cost nothing now)")
    return 0


def _rate(labels: list[str]) -> float | None:
    return sum(x == "pass" for x in labels) / len(labels) if labels else None


def consistency(items: list[dict], version: str) -> dict | None:
    """The judge against itself: the same prompt judged again (--repeat). Items whose verdict changed are noise."""
    passes = [JUDGE_DIR / f"items-{version}.json"] + sorted(JUDGE_DIR.glob(f"items-{version}-repeat*.json"))
    passes = [store.read_json(p) for p in passes if p.exists()]
    if len(passes) < 2:
        return None
    verdicts = {
        i["item_id"]: [p[i["item_id"]][i["dimension"]]["verdict"] for p in passes if i["item_id"] in p] for i in items
    }
    changed = sorted(k for k, v in verdicts.items() if len(set(v)) > 1)
    return {
        "passes": len(passes),
        "items": len(verdicts),
        "same_every_pass": len(verdicts) - len(changed),
        "changed": changed,
    }


ROUNDS = {
    1: "Round 1: 40 stratified items (sampled from deterministic flags)",
    2: "Round 2: 30 items enriched with failures (15 judge-failed real replies + 15 synthetic degraded variants)",
}


def round_files(n: int) -> tuple:
    """(items file, labels file) for a calibration round."""
    if n == 1:
        return labeling.ITEMS_FILE, labeling.LABELS_FILE
    return labeling.LABELS_DIR / f"items-round{n}.jsonl", labeling.LABELS_DIR / f"human-labels-round{n}.jsonl"


def verdict_file(version: str, n: int):
    return JUDGE_DIR / (f"items-{version}.json" if n == 1 else f"items-{version}-round{n}.json")


def _kappa(x) -> str:
    return "undefined" if x is None else f"{x:.2f}"


def latest_consistency(items: list[dict], versions_measured: list[str]) -> dict | None:
    """Consistency for the newest rubric version that has repeat passes (repeats aren't re-run for every version)."""
    for version in reversed(versions_measured):
        found = consistency(items, version)
        if found:
            return {**found, "version": version}
    return None


def cmd_calibrate(args) -> int:
    """Per rubric version: each round on its own and all rounds together. Trust is decided on all labels together,
    per quality (decision 20); round 2 is enriched with failures, which every report says next to its kappa."""
    rounds = {}
    for n in ROUNDS:
        items_file, labels_file = round_files(n)
        items, labels = load_items(items_file), load_labels(labels_file)
        if items and any(i["item_id"] in labels for i in items):
            rounds[n] = (items, labels)
    if not rounds:
        print("No human labels yet: run the labeling page first (make label).")
        return 2
    results = []
    for version in versions():
        if not all(verdict_file(version, n).exists() for n in rounds):
            continue
        per_round, all_items, all_labels, all_verdicts = {}, [], {}, {}
        for n, (items, labels) in rounds.items():
            verdicts = store.read_json(verdict_file(version, n))
            per_round[f"round {n}"] = calibrate(items, labels, verdicts)
            all_items += items
            all_labels.update(labels)
            all_verdicts.update(verdicts)
        combined = calibrate(all_items, all_labels, all_verdicts)
        rubric = load_rubric(version)
        results.append({"version": version, "change": rubric.get("change", ""), **combined, "rounds": per_round})
        line = " · ".join(
            f"{name} n={c['overall']['n']} kappa {_kappa(c['overall']['kappa'])}" for name, c in per_round.items()
        )
        print(
            f"{version}: {line} · all n={combined['overall']['n']} agreement {combined['overall']['agreement']:.0%} "
            f"kappa {_kappa(combined['overall']['kappa'])} · trusted: "
            + (", ".join(d for d, t in combined["trusted"].items() if t) or "none")
        )
    if not results:
        print("No judge verdicts for every labelled round yet: run `hoteleval judge --rubric v1 --round N --live`.")
        return 2
    current = results[-1]
    items1 = rounds.get(1, ([], {}))[0]
    data = {
        "labels": sum(sum(1 for i in items if i["item_id"] in labels) for items, labels in rounds.values()),
        "items": sum(len(items) for items, _ in rounds.values()),
        "rounds": {f"round {n}": ROUNDS[n] for n in rounds},
        "labeler": "Vamsi Alla",
        "trust_rule": f"kappa >= {TRUST_KAPPA} on all labels together, per quality",
        "current": current["version"],
        "trusted": current["trusted"],
        "versions": results,
        "consistency": latest_consistency(items1, [v["version"] for v in results]) if items1 else None,
        "runs": {
            p.stem.removeprefix("run-").removesuffix(f"-{current['version']}"): store.read_json(p)["pass_rates"]
            for p in sorted(JUDGE_DIR.glob(f"run-*-{current['version']}.json"))
        },
    }
    store.write_json(JUDGE_DIR / "calibration.json", data)
    print(f"wrote judge/calibration.json (current rubric {current['version']})")
    return 0


def register(sub) -> None:
    p = sub.add_parser("sample-labels", help="rebuild the 40 stratified calibration items")
    p.set_defaults(fn=cmd_sample)

    p = sub.add_parser("judge", help="LLM judge on the calibration items or a saved run (cached)")
    p.add_argument("--rubric", default="v1")
    p.add_argument("--run", help="judge run 1 of this saved run instead of the calibration items")
    p.add_argument(
        "--repeat", type=int, default=0, help="a fresh, separately cached pass on the same items (consistency)"
    )
    p.add_argument("--round", type=int, default=1, choices=sorted(ROUNDS), help="which calibration round's items")
    p.add_argument("--live", action="store_true", help="call the API for items not in the cache")
    p.add_argument("--env", default=".env")
    p.set_defaults(fn=cmd_judge)

    p = sub.add_parser("calibrate", help="judge vs human labels for every judged rubric version")
    p.set_defaults(fn=cmd_calibrate)
