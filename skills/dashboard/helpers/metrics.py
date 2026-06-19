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


import re

_FIRE_RE = re.compile(r"^\s*(revert|rollback|hotfix)\b|^\s*fix!", re.IGNORECASE)
_CONV_RE = re.compile(
    r"^(feat|fix|docs|chore|build|ci|style|refactor|perf|test)(\(.+\))?!?:", re.IGNORECASE)
_WIP_RE = re.compile(r"^\s*(wip\b|fixup!|squash!|\.+$)", re.IGNORECASE)


# ── Health ──────────────────────────────────────────────────────────────

def firefighting_rate(commits: list[dict], now_ts: int, days: int = 30) -> float:
    window = _within(commits, now_ts, 0, days)
    if not window:
        return 0.0
    fires = sum(1 for c in window if _FIRE_RE.search(c["subject"]))
    return round(fires / len(window), 4)


def churn_hotspots(file_change_counts: dict[str, int], top: int = 5) -> list[dict]:
    ranked = sorted(file_change_counts.items(), key=lambda kv: kv[1], reverse=True)
    return [{"file": f, "changes": n} for f, n in ranked[:top]]


def stale_branches(branches: list[dict], now_ts: int, idle_days: int = 30) -> list[dict]:
    out = []
    for b in branches:
        idle = (now_ts - b["last_ts"]) // DAY
        if idle > idle_days:
            out.append({"name": b["name"], "idle_days": idle})
    return sorted(out, key=lambda x: x["idle_days"], reverse=True)


def commit_message_hygiene(commits: list[dict]) -> dict:
    if not commits:
        return {"conventional_pct": 0.0, "wip_pct": 0.0}
    conv = sum(1 for c in commits if _CONV_RE.match(c["subject"]))
    wip = sum(1 for c in commits if _WIP_RE.match(c["subject"]))
    n = len(commits)
    return {"conventional_pct": round(conv / n, 4), "wip_pct": round(wip / n, 4)}


from collections import Counter


# ── Team ────────────────────────────────────────────────────────────────

def bus_factor(commits: list[dict], now_ts: int, days: int = 90, share: float = 0.5) -> dict:
    window = _within(commits, now_ts, 0, days)
    if not window:
        return {"count": 0, "top_author": None, "top_share": 0.0}
    counts = Counter(c["author"] for c in window)
    total = sum(counts.values())
    ranked = counts.most_common()
    cumulative = 0
    count = 0
    for _, n in ranked:
        cumulative += n
        count += 1
        if cumulative / total > share:
            break
    top_author, top_n = ranked[0]
    return {"count": count, "top_author": top_author,
            "top_share": round(top_n / total, 4)}


def active_authors(commits: list[dict], now_ts: int, days: int = 30) -> int:
    return len({c["author"] for c in _within(commits, now_ts, 0, days)})


def contribution_distribution(commits: list[dict], now_ts: int, days: int = 90) -> dict:
    window = _within(commits, now_ts, 0, days)
    counts = Counter(c["author"] for c in window)
    authors = [{"author": a, "commits": n} for a, n in counts.most_common()]
    return {"authors": authors, "gini": _gini([n for _, n in counts.most_common()])}


def _gini(values: list[int]) -> float:
    if not values or sum(values) == 0:
        return 0.0
    xs = sorted(values)
    n = len(xs)
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return round((2 * cum) / (n * sum(xs)) - (n + 1) / n, 4)


def dormant_authors(commits: list[dict], now_ts: int, silent_days: int = 90) -> dict:
    last_seen: dict[str, int] = {}
    first_seen: dict[str, int] = {}
    for c in commits:
        a = c["author"]
        last_seen[a] = max(last_seen.get(a, 0), c["ts"])
        first_seen[a] = min(first_seen.get(a, c["ts"]), c["ts"])
    gone = [a for a, ts in last_seen.items() if (now_ts - ts) // DAY > silent_days]
    newly = [a for a, ts in first_seen.items() if (now_ts - ts) // DAY <= 30]
    return {"gone_quiet": sorted(gone), "newly_active": sorted(newly)}


def off_hours_pct(commits: list[dict], now_ts: int, days: int = 30) -> float:
    import time
    window = _within(commits, now_ts, 0, days)
    if not window:
        return 0.0
    off = 0
    for c in window:
        tm = time.gmtime(c["ts"])
        if tm.tm_wday >= 5 or tm.tm_hour < 8 or tm.tm_hour >= 19:
            off += 1
    return round(off / len(window), 4)


def is_solo(commits: list[dict]) -> bool:
    return len({c["author"] for c in commits}) <= 2
