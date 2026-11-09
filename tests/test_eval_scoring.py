"""Tests for the review-skill eval scorer (evals/scoring.py)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals"))

import scoring  # noqa: E402

KEY = json.loads(
    (REPO_ROOT / "evals" / "fixtures" / "review-target" / "answer-key.json").read_text()
)


def test_answer_key_line_ranges_point_at_the_planted_code():
    src = REPO_ROOT / "evals" / "fixtures" / "review-target" / "src"
    anchors = {
        "sql-injection": "f\"SELECT",
        "page-off-by-one": "size - 1",
        "mutable-default": "cart: list = []",
        "jwt-decode-no-verify": "jwt.decode",
        "missing-await": "store.save(user)",
        "map-data-race": "c.items[u] = body",
        "response-body-leak": "http.Get",
        "ignored-persist-errors": "_ = os.WriteFile",
    }
    for bug in KEY["bugs"]:
        if bug["id"] not in anchors:
            continue
        lines = (src / bug["file"]).read_text().splitlines()
        start, end = bug["lines"]
        window = "\n".join(lines[start - 1:end])
        assert anchors[bug["id"]] in window, bug["id"]


def test_finding_with_file_line_and_keyword_counts_as_found():
    report = """
### P0: SQL injection in customer lookup
`src/orders.py:14` builds the query with an f-string. Use a placeholder.
"""
    result = scoring.score(report, KEY, skill="quick-review")
    assert "sql-injection" in result["found"]


def test_line_range_citations_match():
    report = "- **orders.py:24-26** — slice uses `size - 1`, so each page drops the last item."
    result = scoring.score(report, KEY, skill="codereview")
    assert "page-off-by-one" in result["found"]


def test_citation_without_keyword_does_not_count():
    report = "See `src/orders.py:14` for context on naming."
    result = scoring.score(report, KEY, skill="quick-review")
    assert "sql-injection" not in result["found"]
    assert "sql-injection" in result["missed"]


def test_missed_only_lists_bugs_required_for_that_skill():
    result = scoring.score("", KEY, skill="quick-review")
    assert "n-plus-one" not in result["missed"]
    assert "sql-injection" in result["missed"]
    result = scoring.score("", KEY, skill="codereview")
    assert "n-plus-one" in result["missed"]


def test_decoy_flagged_as_problem_is_a_false_alarm():
    report = "### P0: SQL injection\n`orders.py:20` passes order_id into the query; injection risk."
    result = scoring.score(report, KEY, skill="codereview")
    assert "parameterized-query" in result["false_alarms"]


def test_out_of_scope_finding_is_reported_for_quick_review():
    report = "### P2: Deep nesting\n`orders.py:62` nests five levels; use guard clauses."
    quick = scoring.score(report, KEY, skill="quick-review")
    review = scoring.score(report, KEY, skill="codereview")
    assert "deep-nesting" in quick["out_of_scope"]
    assert "deep-nesting" not in review["out_of_scope"]
    assert "deep-nesting" in review["found"]


def test_unmatched_citations_are_counted_as_other_findings():
    report = "`cache.go:12` struct field order.\n`orders.py:9` default path."
    result = scoring.score(report, KEY, skill="codereview")
    assert result["other_citations"] == 2


def test_summary_reports_recall():
    report = "`src/orders.py:14` SQL injection via f-string."
    result = scoring.score(report, KEY, skill="quick-review")
    required = [b for b in KEY["bugs"] if "quick-review" in b["required_by"]]
    assert result["recall"] == round(1 / len(required), 3)


def test_citation_in_a_left_out_note_is_not_a_finding():
    report = (
        "- **Lower severities are not shown.** Quick-review leaves out P2-P4 findings. "
        "One example is the deep nesting in `shipping_label` at `src/orders.py:60`."
    )
    result = scoring.score(report, KEY, skill="quick-review")
    assert result["out_of_scope"] == []
    assert result["other_citations"] == 0
