"""Copy the metric code the harness reuses from Projects 1 and 2 at their pinned commits.

    python scripts/sync_vendor.py           # (re)write src/hoteleval/vendor/*.py and SOURCE.json
    python scripts/sync_vendor.py --check   # fail if a vendored file differs from the pinned source (needs repos)

Each file is the project's file byte for byte, except for the import lines listed in EDITS (the project's `src.` and
`eval.` packages become `hoteleval.vendor.`). The sha256 in SOURCE.json is of the original file at the pin, so the
copy can always be traced back to the exact code that produced the published numbers.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "src" / "hoteleval" / "vendor"
sys.path.insert(0, str(ROOT / "src"))

from hoteleval.pins import PINS  # noqa: E402

P1, P2 = "hotel-ops-assistant", "guest-request-agent"
FILES = {
    "grounding.py": (P1, "src/grounding.py", []),
    "p1_grade.py": (P1, "eval/metrics.py", [("from src.grounding import", "from hoteleval.vendor.grounding import")]),
    "p1_visitor.py": (P1, "eval/visitor_metrics.py", []),
    "guards.py": (P2, "src/guards.py", []),
    "triage.py": (P2, "src/triage.py", []),
    "p2_metrics.py": (
        P2,
        "eval/metrics.py",
        [
            ("from src.guards import", "from hoteleval.vendor.guards import"),
            ("from src.triage import", "from hoteleval.vendor.triage import"),
        ],
    ),
    "p2_visitor.py": (
        P2,
        "eval/visitor_metrics.py",
        [("from eval.metrics import", "from hoteleval.vendor.p2_metrics import")],
    ),
}


def original(project: str, path: str) -> bytes:
    repo = ROOT.parent / project
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{PINS[project]}:{path}"], capture_output=True, check=True
    ).stdout


def patched(text: bytes, edits) -> bytes:
    out = text.decode("utf-8")
    for old, new in edits:
        if old not in out:
            raise SystemExit(f"edit not applicable: {old!r}")
        out = out.replace(old, new)
    return out.encode("utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    source, stale = {}, []
    for name, (project, path, edits) in FILES.items():
        raw = original(project, path)
        body = patched(raw, edits)
        source[name] = {
            "repo": f"vamsialladev/{project}",
            "commit": PINS[project],
            "path": path,
            "sha256_original": hashlib.sha256(raw).hexdigest(),
            "edits": [f"{a} -> {b}" for a, b in edits],
        }
        target = VENDOR / name
        if args.check:
            if not target.exists() or target.read_bytes() != body:
                stale.append(name)
        else:
            target.write_bytes(body)
    meta = json.dumps(source, indent=2) + "\n"
    if args.check:
        if (VENDOR / "SOURCE.json").read_text(encoding="utf-8") != meta:
            stale.append("SOURCE.json")
        if stale:
            print(f"FAIL: {', '.join(stale)} differ from the pinned sources")
            return 1
        print(f"vendor OK: {len(FILES)} files match the pinned commits")
        return 0
    (VENDOR / "SOURCE.json").write_text(meta, encoding="utf-8", newline="\n")
    (VENDOR / "__init__.py").write_text(
        '"""Metric code copied from Projects 1 and 2 at pinned commits (see SOURCE.json). Do not edit by hand."""\n',
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {len(FILES)} vendored files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
