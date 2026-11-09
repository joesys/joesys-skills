"""Score a review report against the answer key of planted defects.

A report is free-form markdown, and its layout changes between skill
versions, so the scorer does not parse findings. It looks for citations of
the form `file:line` or `file:start-end` and reads the text around each one.
A planted defect counts as found when some citation points inside its line
range (with a small tolerance) and the nearby text contains one of its
keywords.
"""

from __future__ import annotations

import re

LINE_TOLERANCE = 2
TEXT_BEFORE = 200   # a finding title usually sits just before its citation
TEXT_AFTER = 600

# A citation on a line with one of these phrases names something the report
# chose not to report (for example "lower severities are not shown"). It is
# not a finding.
LEFT_OUT = ("not shown", "leaves out", "left out", "out of scope", "excluded",
            "omitted", "not reported")

CITATION = re.compile(
    r"(?P<file>[\w./-]*?(?P<base>[\w-]+\.(?:py|ts|go)))"
    r"(?::|#L| line | lines? )(?P<start>\d+)(?:\s*[-–]\s*L?(?P<end>\d+))?"
)


def find_citations(report: str) -> list[dict]:
    """Every `file:line` citation, with the text a reader would see near it."""
    matches = [m for m in CITATION.finditer(report) if not _in_left_out_note(report, m.start())]
    citations = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(report)
        start_line = int(match.group("start"))
        end_line = int(match.group("end") or start_line)
        citations.append({
            "file": match.group("base"),
            "start": start_line,
            "end": max(start_line, end_line),
            "text": report[max(0, match.start() - TEXT_BEFORE):
                           min(next_start, match.end() + TEXT_AFTER)].lower(),
        })
    return citations


def _in_left_out_note(report: str, position: int) -> bool:
    line_start = report.rfind("\n", 0, position) + 1
    line_end = report.find("\n", position)
    line = report[line_start:line_end if line_end != -1 else len(report)].lower()
    return any(phrase in line for phrase in LEFT_OUT)


def _matches(citation: dict, target: dict, *, need_keyword: bool = True) -> bool:
    if citation["file"] != target["file"]:
        return False
    low, high = target["lines"]
    if citation["end"] < low - LINE_TOLERANCE or citation["start"] > high + LINE_TOLERANCE:
        return False
    if not need_keyword:
        return True
    return any(keyword.lower() in citation["text"] for keyword in target["keywords"])


def score(report: str, key: dict, *, skill: str) -> dict:
    citations = find_citations(report)
    used = set()

    def hits(target: dict) -> bool:
        found = [i for i, c in enumerate(citations) if _matches(c, target)]
        used.update(found)
        return bool(found)

    required = [bug for bug in key["bugs"] if skill in bug["required_by"]]
    found = [bug["id"] for bug in key["bugs"] if hits(bug)]
    missed = [bug["id"] for bug in required if bug["id"] not in found]

    out_of_scope, extra_found = [], []
    for item in key.get("out_of_scope", []):
        if hits(item):
            if skill in item.get("forbidden_for", []):
                out_of_scope.append(item["id"])
            else:
                extra_found.append(item["id"])

    false_alarms = [decoy["id"] for decoy in key.get("decoys", []) if hits(decoy)]
    other = len(citations) - len(used)

    return {
        "skill": skill,
        "found": found + extra_found,
        "missed": missed,
        "recall": round((len(required) - len(missed)) / len(required), 3) if required else 0.0,
        "false_alarms": false_alarms,
        "out_of_scope": out_of_scope,
        "other_citations": other,
    }
