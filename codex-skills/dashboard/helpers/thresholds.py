# thresholds.py
"""Default thresholds and pure traffic-light classification.

Pure module: no subprocess, no filesystem (except optional config read in
load_config), no clock. Light values: "green" | "yellow" | "red" | "na".
"""
from __future__ import annotations
import os
from typing import Optional

DEFAULTS: dict = {
    "thresholds": {
        "staleness_days": {"green": 7, "yellow": 30},
        "bus_factor": {"yellow": 2, "red": 1},
        "firefighting_pct": {"green": 0.10, "red": 0.25},
        "stale_branch_days": 30,
        "stale_branch_count": {"green": 5, "yellow": 15},
        "release_recency_days": {"green": 30, "yellow": 90},
    },
    "host": "auto",
    "off_hours": "off",
    "audit_stale_after_days": 30,
    "modules": None,
}

_ORDER = {"na": -1, "green": 0, "yellow": 1, "red": 2}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(repo: str) -> dict:
    """Merge DEFAULTS with .claude/dashboard.yaml if PyYAML and the file exist."""
    path = os.path.join(repo, ".claude", "dashboard.yaml")
    if not os.path.isfile(path):
        return DEFAULTS
    try:
        import yaml  # optional dependency
    except ImportError:
        return DEFAULTS
    try:
        with open(path, "r", encoding="utf-8") as fh:
            user = yaml.safe_load(fh) or {}
    except Exception:
        return DEFAULTS
    return _deep_merge(DEFAULTS, user)


def worst(lights: list[str]) -> str:
    real = [l for l in lights if l != "na"]
    if not real:
        return "na"
    return max(real, key=lambda l: _ORDER[l])


def light_staleness(days: Optional[int], cfg: dict) -> str:
    if days is None:
        return "na"
    th = cfg["thresholds"]["staleness_days"]
    if days <= th["green"]:
        return "green"
    if days <= th["yellow"]:
        return "yellow"
    return "red"


def light_bus_factor(count: int, cfg: dict) -> str:
    th = cfg["thresholds"]["bus_factor"]
    if count <= th["red"]:
        return "red"
    if count <= th["yellow"]:
        return "yellow"
    return "green"


def light_firefighting(pct: float, cfg: dict) -> str:
    th = cfg["thresholds"]["firefighting_pct"]
    if pct < th["green"]:
        return "green"
    if pct <= th["red"]:
        return "yellow"
    return "red"


def light_stale_branches(n: int, cfg: dict) -> str:
    th = cfg["thresholds"]["stale_branch_count"]
    if n <= th["green"]:
        return "green"
    if n <= th["yellow"]:
        return "yellow"
    return "red"


def light_release(days: Optional[int], has_tags: bool, cfg: dict) -> str:
    if not has_tags or days is None:
        return "na"
    th = cfg["thresholds"]["release_recency_days"]
    if days <= th["green"]:
        return "green"
    if days <= th["yellow"]:
        return "yellow"
    return "red"
