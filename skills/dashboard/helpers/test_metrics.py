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


def test_pulse_no_double_count_at_30day_boundary():
    # a commit exactly 30 days ago belongs to the prior window only
    commits = [c(0), c(30), c(45)]
    p = metrics.pulse(commits, NOW)
    assert p["count_30d"] == 1          # only c(0)
    assert p["count_prev_30d"] == 2     # c(30) and c(45)
    # the two windows never count the same commit twice
    assert p["count_30d"] + p["count_prev_30d"] == 3


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


def test_firefighting_excludes_plain_fix():
    commits = [
        c(1, subject="revert: bad change"),
        c(1, subject="hotfix: prod down"),
        c(1, subject="fix: normal bug"),     # excluded
        c(1, subject="feat: thing"),
    ]
    rate = metrics.firefighting_rate(commits, NOW)
    assert round(rate, 3) == 0.5  # 2 of 4


def test_churn_hotspots_sorted():
    counts = {"a.py": 10, "b.py": 3, "c.py": 7}
    hs = metrics.churn_hotspots(counts, top=2)
    assert [h["file"] for h in hs] == ["a.py", "c.py"]
    assert hs[0]["changes"] == 10


def test_stale_branches_filters_and_sorts():
    branches = [
        {"name": "old", "last_ts": NOW - 100 * DAY},
        {"name": "fresh", "last_ts": NOW - 5 * DAY},
        {"name": "older", "last_ts": NOW - 200 * DAY},
    ]
    sb = metrics.stale_branches(branches, NOW, idle_days=30)
    assert [b["name"] for b in sb] == ["older", "old"]
    assert sb[0]["idle_days"] == 200


def test_commit_message_hygiene():
    commits = [c(1, subject="feat: a"), c(1, subject="fix: b"),
               c(1, subject="WIP"), c(1, subject="random text")]
    h = metrics.commit_message_hygiene(commits)
    assert round(h["conventional_pct"], 2) == 0.5
    assert round(h["wip_pct"], 2) == 0.25
