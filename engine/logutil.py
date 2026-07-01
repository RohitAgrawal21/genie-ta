"""Tiny logging helper: writes to logs/engine.log AND stdout. UTF-8 safe."""
from __future__ import annotations
import logging
import sys
from . import paths

_configured = False


def get_logger(name: str = "engine") -> logging.Logger:
    global _configured
    paths.ensure_dirs()
    logger = logging.getLogger(name)
    if not _configured:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s",
                                "%Y-%m-%d %H:%M:%S")
        fh = logging.FileHandler(paths.LOG_DIR / "engine.log", encoding="utf-8")
        fh.setFormatter(fmt)
        # UTF-8 stream so Windows console never crashes on a stray glyph
        try:
            stream = open(sys.stdout.fileno(), mode="w", encoding="utf-8",
                          buffering=1, errors="replace")
        except Exception:
            stream = sys.stdout
        sh = logging.StreamHandler(stream)
        sh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(sh)
        logger.propagate = False
        _configured = True
    return logger
