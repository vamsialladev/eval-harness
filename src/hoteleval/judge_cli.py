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
        items = [{**i, "ref": i["item_id"]} for i in load_items()]
        verdicts, rows = run_items(args.rubric, items, args.live, env, args.repeat)
        suffix = f"-repeat{args.repeat}" if args.repeat else ""
        store.write_json(JUDGE_DIR / f"items-{args.rubric}{suffix}.json", verdicts)
        print(f"judged {len(verdicts)}/{len(items)} calibration items with rubric {args.rubric}")
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


def cmd_calibrate(args) -> int:
    items, labels = load_items(), load_labels()
    labelled = sum(1 for i in items if i["item_id"] in labels)
    if not labelled:
        print("No human labels yet: run the labeling page first (make label).")
        return 2
    results = []
    for version in versions():
        path = JUDGE_DIR / f"items-{version}.json"
        if not path.exists():
            continue
        cal = calibrate(items, labels, store.read_json(path))
        rubric = load_rubric(version)
        results.append({"version": version, "change": rubric.get("change", ""), **cal})
        o = cal["overall"]
        kappa = "undefined" if o["kappa"] is None else f"{o['kappa']:.2f}"
        print(
            f"{version}: n={o['n']} agreement {o['agreement']:.0%} kappa {kappa} · trusted: "
            + (", ".join(d for d, t in cal["trusted"].items() if t) or "none")
        )
    if not results:
        print("No judge verdicts yet: run `hoteleval judge --rubric v1 --live`.")
        return 2
    current = results[-1]
    data = {
        "labels": labelled,
        "items": len(items),
        "labeler": "Vamsi Alla",
        "trust_rule": f"kappa >= {TRUST_KAPPA}",
        "current": current["version"],
        "trusted": current["trusted"],
        "versions": results,
        "consistency": consistency(items, current["version"]),
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
    p.add_argument("--live", action="store_true", help="call the API for items not in the cache")
    p.add_argument("--env", default=".env")
    p.set_defaults(fn=cmd_judge)

    p = sub.add_parser("calibrate", help="judge vs human labels for every judged rubric version")
    p.set_defaults(fn=cmd_calibrate)
