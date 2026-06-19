from __future__ import annotations
import collect_host as ch


def test_detect_returns_unavailable_without_remote(monkeypatch):
    monkeypatch.setattr(ch, "_remote_host", lambda repo: None)
    out = ch.collect(".")
    assert out["available"] is False
    assert "reason" in out


def test_collect_unavailable_when_cli_missing(monkeypatch):
    monkeypatch.setattr(ch, "_remote_host", lambda repo: "github")
    monkeypatch.setattr(ch, "_cli_ready", lambda host: False)
    out = ch.collect(".")
    assert out["available"] is False
    assert "gh" in out["reason"].lower() or "auth" in out["reason"].lower()


def test_collect_aggregates_when_available(monkeypatch):
    monkeypatch.setattr(ch, "_remote_host", lambda repo: "github")
    monkeypatch.setattr(ch, "_cli_ready", lambda host: True)
    monkeypatch.setattr(ch, "_open_prs", lambda repo: {"count": 4, "median_age_days": 3.5})
    monkeypatch.setattr(ch, "_open_issues", lambda repo: 12)
    monkeypatch.setattr(ch, "_ci_pass_rate", lambda repo: 0.9)
    out = ch.collect(".")
    assert out == {"available": True, "host": "github", "open_prs": 4,
                   "pr_median_age_days": 3.5, "ci_pass_rate": 0.9, "open_issues": 12}
