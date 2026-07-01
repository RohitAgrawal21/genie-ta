"""Central path resolution. Everything is relative to the project root so the
engine runs identically regardless of the current working directory."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Inputs
CONFIG_FILE = ROOT / "config.json"
UNIVERSE_FILE = ROOT / "universe.txt"
HOLIDAYS_FILE = ROOT / "holidays.txt"
STRATEGY_FILE = ROOT / "strategy" / "STRATEGY.md"

# State / outputs (created on demand)
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
STATE_DIR = ROOT / "state"
LOG_DIR = ROOT / "logs"

SIGNALS_FILE = STATE_DIR / "signals.json"
PORTFOLIO_FILE = STATE_DIR / "portfolio.json"
PERFORMANCE_FILE = STATE_DIR / "performance.csv"
CACHE_META_FILE = CACHE_DIR / "_meta.json"


def ensure_dirs() -> None:
    for d in (DATA_DIR, CACHE_DIR, STATE_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)
