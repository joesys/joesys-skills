"""Score a /codebase-audit run, and compare grades between the old and new skill.

The audit writes its results to `docs/reports/codebase-audit/YYYYMMDD/` in the
work dir. The runner copies that folder out before the temp dir is deleted, and
this module reads the copy. There is no answer key: the fixture code is the
same for both versions, so the main check is grade stability. A trimmed skill
must not move grades on the same code.

Compare two summaries from the command line:

    python3 evals/audit_scoring.py evals/results/<run>/summary.json [other/summary.json]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# The 12 graded criteria. Velocity has no grade, so it is not listed.
CRITERIA = [
    "maintainability", "evolvability", "correctness", "testability", "reliability",
    "performance", "readability", "modularity", "consistency", "operability",
    "security", "story_readability",
]
NOT_MEASURED = "Not measured"
# The skill's scale has no plus or minus grades except A+. Lower rank is better.
GRADE_RANK = {"A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}

OVERALL_LINE = re.compile(r"overall grade:?\**\s*\**\s*([A-F][+-]?~?)", re.IGNORECASE)
CRITERION_HEADING = re.compile(r"^##\s+\d+\.\s+(.+?)\s+[—-]+\s+Grade:\s*(\S.*?)\s*$", re.MULTILINE)


def criterion_key(name: str) -> str:
    """'Story Readability' and 'story-readability' both become 'story_readability'."""
    return re.sub(r"[^a-z]+", "_", name.lower()).strip("_")


def normalize_grade(grade) -> str:
    """Drop the low-confidence `~` and markdown, and map every 'no grade' form to one value."""
    text = str(grade or "").replace("*", "").replace("~", "").strip()
    if not text or text in {"—", "-", "–"} or "not measured" in text.lower() or text.lower() == "n/a":
        return NOT_MEASURED
    return text.upper()


def score_audit(report_dir: Path | None) -> dict:
    """Read the copied report folder and record grades, gaps, and report size."""
    result = {
        "grade_source": None, "overall_grade": None, "grades": {},
        "not_measured": [], "missing": [], "heat_map": False, "danger_zone_files": [],
        "analysis_mentions_danger_zone": False, "analysis_words": 0, "files": [],
    }
    if report_dir is None or not report_dir.is_dir():
        return result

    result["files"] = sorted(p.name for p in report_dir.rglob("*") if p.is_file())
    metrics = _newest(report_dir, "metrics.json")
    analysis = _newest(report_dir, "analysis.md")
    analysis_text = analysis.read_text(encoding="utf-8") if analysis else ""

    if metrics:
        data = json.loads(metrics.read_text(encoding="utf-8"))
        result["grade_source"] = "metrics.json"
        result["overall_grade"] = data.get("overall_grade")
        result["grades"] = {
            criterion_key(name): (entry or {}).get("grade")
            for name, entry in (data.get("criteria") or {}).items()
        }
        heat_map = data.get("risk_heat_map") or []
        result["heat_map"] = bool(heat_map)
        result["danger_zone_files"] = [
            row.get("file") for row in heat_map
            if criterion_key(str(row.get("quadrant", ""))) == "danger_zone"
        ]
    elif analysis_text:
        result["grade_source"] = "analysis.md"
        overall = OVERALL_LINE.search(analysis_text)
        result["overall_grade"] = overall.group(1) if overall else None
        result["grades"] = {
            criterion_key(name): grade for name, grade in CRITERION_HEADING.findall(analysis_text)
        }

    result["not_measured"] = sorted(
        name for name, grade in result["grades"].items() if normalize_grade(grade) == NOT_MEASURED
    )
    if result["grade_source"]:
        result["missing"] = [name for name in CRITERIA if name not in result["grades"]]
    result["analysis_mentions_danger_zone"] = "danger zone" in analysis_text.lower()
    result["analysis_words"] = len(analysis_text.split())
    return result


def _newest(folder: Path, name: str) -> Path | None:
    """The file from the latest dated subfolder (folder names sort by date)."""
    found = sorted(folder.rglob(name))
    return found[-1] if found else None


def split_by_version(results: list[dict]) -> tuple[list[dict], list[dict]]:
    old = [r for r in results if r.get("version") == "old"]
    new = [r for r in results if r.get("version") == "new"]
    return old, new


def compare_grades(old_results: list[dict], new_results: list[dict]) -> dict:
    """List every criterion whose grades differ between the old and new runs.

    With several runs per version, a criterion counts as changed when the set
    of grades differs (old gave {B, C}, new gave {B} is a change). `steps` is
    the largest distance on the grade scale between any old and any new grade.
    """
    names = {"overall"}
    for run in old_results + new_results:
        names.update(run.get("grades") or {})

    rows = []
    for name in ["overall"] + sorted(names - {"overall"}):
        old = [_grade_of(run, name) for run in old_results]
        new = [_grade_of(run, name) for run in new_results]
        rows.append({
            "criterion": name, "old": old, "new": new,
            "changed": set(map(normalize_grade, old)) != set(map(normalize_grade, new)),
            "steps": _max_steps(old, new),
        })
    changed = [row for row in rows if row["changed"]]
    return {"stable": not changed, "changed": changed, "rows": rows}


def _grade_of(run: dict, name: str):
    if name == "overall":
        return run.get("overall_grade")
    return (run.get("grades") or {}).get(name)


def _rank(grade) -> int | None:
    text = normalize_grade(grade)
    if text in GRADE_RANK:
        return GRADE_RANK[text]
    return GRADE_RANK.get(text[:1])  # "B+" is off-scale; treat it as "B"


def _max_steps(old: list, new: list) -> int | None:
    distances = [
        abs(a - b)
        for a in map(_rank, old) if a is not None
        for b in map(_rank, new) if b is not None
    ]
    return max(distances) if distances else None


def main(argv: list[str]) -> int:
    results = []
    for path in argv:
        results += json.loads(Path(path).read_text(encoding="utf-8"))["results"]
    old, new = split_by_version(results)
    comparison = compare_grades(old, new)
    for row in comparison["rows"]:
        mark = "CHANGED" if row["changed"] else "same"
        print(f"{row['criterion']:<20} old={row['old']} new={row['new']} {mark}"
              + (f" ({row['steps']} steps)" if row["changed"] and row["steps"] else ""))
    print("Grades are stable." if comparison["stable"] else
          f"{len(comparison['changed'])} grade(s) moved.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1:]))
