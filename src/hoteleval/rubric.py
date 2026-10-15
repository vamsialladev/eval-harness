"""Versioned judge rubrics (data/rubrics/judge-<version>.toml)."""

import tomllib
from pathlib import Path

RUBRICS = Path(__file__).resolve().parent / "data" / "rubrics"
DIMENSIONS = ("completeness", "tone", "clarity")


def load_rubric(version: str = "v1") -> dict:
    data = tomllib.loads((RUBRICS / f"judge-{version}.toml").read_text(encoding="utf-8"))
    missing = [d for d in DIMENSIONS if d not in data.get("dimensions", {})]
    if missing or data.get("version") != version:
        raise ValueError(f"rubric {version}: bad version or missing dimensions {missing}")
    return data


def versions() -> list[str]:
    return sorted(p.stem.removeprefix("judge-") for p in RUBRICS.glob("judge-v*.toml"))
