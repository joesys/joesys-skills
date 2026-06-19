from __future__ import annotations
import json
from pathlib import Path
import collect_audit as ca


def _audit(dirpath: Path, date: str, grade: str):
    d = dirpath / "docs" / "reports" / "codebase-audit" / date
    d.mkdir(parents=True)
    (d / "metrics.json").write_text(json.dumps({
        "date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "commit": "abc1234",
        "overall_grade": grade,
        "criteria": {"correctness": {"grade": "A+"}, "security": {"grade": grade}},
    }))


def test_unavailable_when_no_report(tmp_path, monkeypatch):
    monkeypatch.setattr(ca, "_commits_behind", lambda repo, commit: 0)
    assert ca.collect(str(tmp_path), 0)["available"] is False


def test_reads_newest_report_and_criteria(tmp_path, monkeypatch):
    _audit(tmp_path, "20260101", "B")
    _audit(tmp_path, "20260618", "A+")
    monkeypatch.setattr(ca, "_commits_behind", lambda repo, commit: 5)
    out = ca.collect(str(tmp_path), 0)
    assert out["available"] is True
    assert out["overall_grade"] == "A+"          # newest wins
    assert out["criteria"]["correctness"] == "A+"
    assert out["commits_behind"] == 5
    assert len(out["trend"]) == 2                 # both reports in trend


def test_stale_flag(tmp_path, monkeypatch):
    _audit(tmp_path, "20260618", "A")
    monkeypatch.setattr(ca, "_commits_behind", lambda repo, commit: 999)
    out = ca.collect(str(tmp_path), 0, stale_after_commits=50)
    assert out["stale"] is True
