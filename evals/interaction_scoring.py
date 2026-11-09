"""Score an /interaction-review report against the synthetic session's answer key.

The report is markdown with YAML front-matter. The scorer reads:

- `rubric_version` from the front-matter,
- the per-lens scores and the overall score from the first scorecard table,
- which designed issues the report mentions (any keyword, case-insensitive,
  the same loose match that scoring.py uses for review findings).

It then checks each score against the band in the answer key. Bands are wide on
purpose: the question is "did this lens land low, as designed?", not an exact
number.
"""

from __future__ import annotations

import re

LENSES = ["prompt_craft", "workflow_efficiency", "agentic_leverage",
          "error_recovery", "context_instruction"]

# The first words of a scorecard row name the lens. Later tables (for example
# the Progress Tracker) repeat the names, so only the first row per lens counts.
ROW_PREFIXES = {
    "prompt craft": "prompt_craft",
    "workflow efficiency": "workflow_efficiency",
    "agentic leverage": "agentic_leverage",
    "error recovery": "error_recovery",
    "context": "context_instruction",
    "overall": "overall",
}
NUMBER = re.compile(r"\d+")
GRADE = re.compile(r"^[A-F][+-]?$")


def read_front_matter(report: str) -> dict:
    """Simple `key: value` lines between the first two `---` lines."""
    lines = report.lstrip().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields


def read_scorecard(report: str) -> dict[str, tuple[int, str | None]]:
    """Map lens -> (score, grade) from the first table row that names each lens.

    Some report versions put a Weight column before the Score column, so the
    columns are located from the table's header row when it has one.
    """
    found = {}
    score_col, grade_col = 1, 2
    for line in report.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.replace("*", "").strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        headers = [cell.lower() for cell in cells]
        if "score" in headers:
            score_col = headers.index("score")
            grade_col = headers.index("grade") if "grade" in headers else score_col + 1
            continue
        lens = next((key for prefix, key in ROW_PREFIXES.items()
                     if cells[0].lower().startswith(prefix)), None)
        if lens is None or lens in found or len(cells) <= score_col:
            continue
        score = NUMBER.search(cells[score_col])
        if score is None:
            continue
        grade = cells[grade_col] if len(cells) > grade_col and GRADE.match(cells[grade_col]) else None
        found[lens] = (int(score.group()), grade)
    return found


def score_interaction(report: str, key: dict) -> dict:
    scorecard = read_scorecard(report)
    lens_scores = {lens: scorecard[lens][0] for lens in LENSES if lens in scorecard}
    overall = scorecard.get("overall", (None, None))

    in_band = {}
    for lens, expected in key["lenses"].items():
        value = overall[0] if lens == "overall" else lens_scores.get(lens)
        low, high = expected["band"]
        in_band[lens] = None if value is None else low <= value <= high

    text = report.lower()
    found = [issue["id"] for issue in key["issues"]
             if any(word.lower() in text for word in issue["keywords"])]
    problems = [issue["id"] for issue in key["issues"] if issue["kind"] == "problem"]
    strengths = [issue["id"] for issue in key["issues"] if issue["kind"] == "strength"]

    return {
        "skill": "interaction-review",
        "rubric_version": read_front_matter(report).get("rubric_version"),
        "lens_scores": lens_scores,
        "overall_score": overall[0],
        "overall_grade": overall[1],
        "in_band": in_band,
        "out_of_band": [lens for lens, ok in in_band.items() if ok is False],
        "issues_found": found,
        "issues_missed": [i for i in problems + strengths if i not in found],
        "problem_recall": round(sum(i in found for i in problems) / len(problems), 3) if problems else 0.0,
        "strength_found": any(i in found for i in strengths),
    }
