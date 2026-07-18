"""Config + universe + holiday loaders. Writes defaults if config.json is absent."""
from __future__ import annotations
import json
from . import paths

DEFAULT_CONFIG = {
    "starting_capital": 500000,
    "max_positions": 20,
    "mode": "intraday",
    "poll_minutes": 15,
    "market_open": "09:15",
    "market_close": "15:30",
    "timezone": "Asia/Kolkata",
    "fill": "next_bar_open",
    "round_trip_cost_pct": 0.25,
    "benchmark": "^NSEI",
    "data": {
        "eod_period": "1y",
        "eod_interval": "1d",
        "intraday_period": "60d",
        "batch_size": 25,
        "max_retries": 4,
        "backoff_base_sec": 2,
        "request_pause_sec": 1.0,
    },
    "execution": {
        "entry_kinds": ["entry"],     # only these rule kinds may OPEN a trade
        "entry_min_rules": 3,         # require >= N distinct entry rules to agree
        "downtrend_blocks_buys": True,  # CAN SLIM M: no new longs in a downtrend
        "exit_on_opposing_min": 2,    # exit if >= N opposing signals fire
        "min_hold_days": 3,           # ignore exit signals before this (except stop)
        "use_ema_trail": True,        # exit on close below trailing 18-EMA
        "stop_loss_pct": 0.08,        # hard stop
        "disabled_rules": [],         # rule_ids pruned for poor backtest performance
    },
}


def load_config() -> dict:
    """Load config.json, creating it from defaults if missing. Shallow-merges
    defaults so a partial config still gets every key."""
    paths.ensure_dirs()
    if not paths.CONFIG_FILE.exists():
        paths.CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        return json.loads(json.dumps(DEFAULT_CONFIG))
    cfg = json.loads(paths.CONFIG_FILE.read_text(encoding="utf-8"))
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged.update(cfg)
    # one level deep for nested blocks so a partial override keeps every key
    for block in ("data", "execution"):
        if isinstance(cfg.get(block), dict):
            b = json.loads(json.dumps(DEFAULT_CONFIG[block]))
            b.update(cfg[block])
            merged[block] = b
    return merged


def load_universe() -> list[str]:
    """Read universe.txt -> list of bare symbols (no .NS). Dedupes, preserves order."""
    if not paths.UNIVERSE_FILE.exists():
        return []
    seen, out = set(), []
    for line in paths.UNIVERSE_FILE.read_text(encoding="utf-8").splitlines():
        s = line.split("#", 1)[0].strip().upper()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def load_holidays() -> set[str]:
    """Read holidays.txt -> set of 'YYYY-MM-DD' strings (inline # comments stripped)."""
    if not paths.HOLIDAYS_FILE.exists():
        return set()
    out = set()
    for line in paths.HOLIDAYS_FILE.read_text(encoding="utf-8").splitlines():
        s = line.split("#", 1)[0].strip()
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            out.add(s)
    return out
