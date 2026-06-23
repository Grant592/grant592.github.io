"""Shared config + path helpers used by every module."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@lru_cache(maxsize=1)
def load_config() -> dict:
    """Load config.yaml once and cache it."""
    with open(ROOT / "config.yaml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def output_dir() -> Path:
    """Return (and create) the output directory."""
    cfg = load_config()
    out = ROOT / cfg.get("output_dir", "out")
    out.mkdir(parents=True, exist_ok=True)
    return out


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)
