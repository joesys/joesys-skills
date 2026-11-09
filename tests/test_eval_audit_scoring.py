"""Tests for the codebase-audit eval scorer (evals/audit_scoring.py)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals"))

import audit_scoring  # noqa: E402

METRICS = {
    "overall_grade": "C~",
    "overall_confidence": "low",
    "criteria": {
        "maintainability": {"grade": "B", "confidence": "high"},
        "security": {"grade": "D", "confidence": "medium"},
        "testability": {"grade": "Not measured", "confidence": "low"},
        "story_readability": {"grade": "B~", "confidence": "low"},
        "operability": {"grade": None},
    },
    "risk_heat_map": [
        {"file": "src/orders.py", "complexity": 9, "churn_30d": 3, "quadrant": "danger_zone"},
        {"file": "src/cache.go", "complexity": 4, "churn_30d": 1, "quadrant": "stable"},
    ],
}

ANALYSIS = """# Codebase Audit

**Overall grade: C (confidence: low)**

## Risk Heat Map

**Danger Zone files:** `src/orders.py`

## 1. Security — Grade: D

Tokens are decoded without a signature check.

## 2. Maintainability — Grade: B

Short functions.
"""


def write_report(root: Path, metrics=METRICS, analysis=ANALYSIS) -> Path:
    folder = root / "20261109"
    folder.mkdir(parents=True)
    if metrics is not None:
        (folder / "metrics.json").write_text(json.dumps(metrics))
    if analysis is not None:
        (folder / "analysis.md").write_text(analysis)
    (folder / "metrics.md").write_text("# Codebase Metrics\n")
    return root


def test_reads_overall_and_per_criterion_grades_from_metrics_json(tmp_path):
    result = audit_scoring.score_audit(write_report(tmp_path))
    assert result["grade_source"] == "metrics.json"
    assert result["overall_grade"] == "C~"
    assert result["grades"]["maintainability"] == "B"
    assert result["grades"]["security"] == "D"
    assert result["grades"]["story_readability"] == "B~"


def test_lists_criteria_that_were_not_measured_or_left_out(tmp_path):
    result = audit_scoring.score_audit(write_report(tmp_path))
    assert result["not_measured"] == ["operability", "testability"]
    assert "correctness" in result["missing"]
    assert "security" not in result["missing"]
    assert "velocity" not in result["missing"]


def test_records_heat_map_danger_zone_and_analysis_size(tmp_path):
    result = audit_scoring.score_audit(write_report(tmp_path))
    assert result["heat_map"] is True
    assert result["danger_zone_files"] == ["src/orders.py"]
    assert result["analysis_mentions_danger_zone"] is True
    assert result["analysis_words"] == len(ANALYSIS.split())
    assert sorted(result["files"]) == ["analysis.md", "metrics.json", "metrics.md"]


def test_falls_back_to_analysis_headings_without_metrics_json(tmp_path):
    result = audit_scoring.score_audit(write_report(tmp_path, metrics=None))
    assert result["grade_source"] == "analysis.md"
    assert result["overall_grade"] == "C"
    assert result["grades"] == {"security": "D", "maintainability": "B"}
    assert result["heat_map"] is False


def test_missing_report_folder_is_an_empty_result(tmp_path):
    result = audit_scoring.score_audit(None)
    assert result["grade_source"] is None
    assert result["overall_grade"] is None
    assert result["grades"] == {}
    assert result["analysis_words"] == 0


def run(version, overall, **grades):
    return {"version": version, "overall_grade": overall, "grades": grades}


def test_compare_finds_no_change_when_grades_match():
    old = [run("old", "C", security="D", maintainability="B")]
    new = [run("new", "C~", security="D", maintainability="B")]
    comparison = audit_scoring.compare_grades(old, new)
    assert comparison["stable"] is True
    assert comparison["changed"] == []


def test_compare_lists_moved_grades_with_step_size():
    old = [run("old", "C", security="D", maintainability="B")]
    new = [run("new", "B", security="B", maintainability="B")]
    comparison = audit_scoring.compare_grades(old, new)
    assert comparison["stable"] is False
    changed = {row["criterion"]: row for row in comparison["changed"]}
    assert set(changed) == {"overall", "security"}
    assert changed["security"]["old"] == ["D"]
    assert changed["security"]["new"] == ["B"]
    assert changed["security"]["steps"] == 2


def test_compare_flags_a_criterion_that_became_not_measured():
    old = [run("old", "C", testability="D")]
    new = [run("new", "C", testability="Not measured")]
    changed = audit_scoring.compare_grades(old, new)["changed"]
    assert [row["criterion"] for row in changed] == ["testability"]
    assert changed[0]["steps"] is None


def test_compare_accepts_mixed_results_from_one_summary():
    results = [run("old", "C", security="D"), run("new", "C", security="D")]
    old, new = audit_scoring.split_by_version(results)
    assert audit_scoring.compare_grades(old, new)["stable"] is True
