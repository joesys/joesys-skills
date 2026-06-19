# metrics.py
"""Pure metric functions over parsed git data. No subprocess, no clock.

Current time always enters via an explicit `now_ts` parameter.
"""
from __future__ import annotations
from typing import Optional

DAY = 86400


def _within(commits: list[dict], now_ts: int, lo_days: int, hi_days: int) -> list[dict]:
    lo = now_ts - hi_days * DAY
    hi = now_ts - lo_days * DAY
    return [c for c in commits if lo < c["ts"] <= hi]


# ── Delivery ────────────────────────────────────────────────────────────

def pulse(commits: list[dict], now_ts: int) -> dict:
    cur = len(_within(commits, now_ts, 0, 30))
    prev = len(_within(commits, now_ts, 30, 60))
    pct: Optional[float] = round((cur - prev) / prev, 4) if prev else None
    return {"count_30d": cur, "count_prev_30d": prev, "pct_change": pct}


def staleness_days(commits: list[dict], now_ts: int) -> Optional[int]:
    if not commits:
        return None
    latest = max(c["ts"] for c in commits)
    return max(0, (now_ts - latest) // DAY)


def weekly_cadence(commits: list[dict], now_ts: int, weeks: int = 26) -> list[int]:
    buckets = [0] * weeks
    for c in commits:
        wk = (now_ts - c["ts"]) // (7 * DAY)
        if 0 <= wk < weeks:
            buckets[weeks - 1 - wk] += 1  # oldest -> newest
    return buckets


def release_recency(tags: list[dict], now_ts: int) -> dict:
    if not tags:
        return {"has_tags": False, "days_since": None, "last_tag": None}
    newest = max(tags, key=lambda t: t["ts"])
    return {"has_tags": True,
            "days_since": max(0, (now_ts - newest["ts"]) // DAY),
            "last_tag": newest["name"]}


def throughput_per_week(commits: list[dict], now_ts: int, weeks: int = 12) -> float:
    merges = [c for c in _within(commits, now_ts, 0, weeks * 7) if c["is_merge"]]
    return round(len(merges) / weeks, 2) if weeks else 0.0


def when_we_work(commits: list[dict]) -> list[list[int]]:
    import time
    grid = [[0] * 24 for _ in range(7)]
    for c in commits:
        tm = time.gmtime(c["ts"])
        grid[tm.tm_wday][tm.tm_hour] += 1
    return grid
