# test_metrics.py
from __future__ import annotations
import metrics

DAY = 86400
NOW = 1_700_000_000  # frozen clock


def c(days_ago, author="Alice", subject="feat: x", is_merge=False):
    return {"hash": "h", "author": author, "email": author + "@x",
            "ts": NOW - days_ago * DAY, "parents": ["p1", "p2"] if is_merge else ["p1"],
            "is_merge": is_merge, "subject": subject}


def test_pulse_counts_and_pct():
    commits = [c(1), c(2), c(40), c(50)]  # 2 in last 30d, 2 in prior 30d
    p = metrics.pulse(commits, NOW)
    assert p["count_30d"] == 2
    assert p["count_prev_30d"] == 2
    assert p["pct_change"] == 0.0


def test_pulse_pct_none_when_no_prior():
    p = metrics.pulse([c(1), c(2)], NOW)
    assert p["count_30d"] == 2
    assert p["pct_change"] is None


def test_staleness_days():
    assert metrics.staleness_days([c(3), c(10)], NOW) == 3
    assert metrics.staleness_days([], NOW) is None


def test_weekly_cadence_length_and_order():
    cad = metrics.weekly_cadence([c(0), c(0), c(8)], NOW, weeks=4)
    assert len(cad) == 4
    assert cad[-1] == 2  # this week has 2
    assert cad[-2] == 1  # last week has 1


def test_release_recency():
    tags = [{"name": "v2", "ts": NOW - 5 * DAY}, {"name": "v1", "ts": NOW - 40 * DAY}]
    r = metrics.release_recency(tags, NOW)
    assert r["has_tags"] is True
    assert r["days_since"] == 5
    assert r["last_tag"] == "v2"
    assert metrics.release_recency([], NOW)["has_tags"] is False


def test_throughput_counts_only_merges():
    commits = [c(1, is_merge=True), c(2, is_merge=True), c(3)]
    tp = metrics.throughput_per_week(commits, NOW, weeks=1)
    assert tp == 2.0
