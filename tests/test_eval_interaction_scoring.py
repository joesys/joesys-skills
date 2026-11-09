"""Tests for the interaction-review eval fixture and scorer (evals/interaction_scoring.py)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals"))

import interaction_scoring  # noqa: E402

FIXTURE = REPO_ROOT / "evals" / "fixtures" / "interaction-session"
KEY = json.loads((FIXTURE / "answer-key.json").read_text())
LINES = [json.loads(line) for line in (FIXTURE / "session.jsonl").read_text().splitlines()]


def blocks(kind):
    for line in LINES:
        content = line.get("message", {}).get("content")
        if isinstance(content, list):
            for block in content:
                if block.get("type") == kind:
                    yield line, block


def human_prompts():
    return [line["message"]["content"] for line in LINES
            if line.get("type") == "user" and isinstance(line["message"]["content"], str)]


# --- The fixture follows the Claude Code log schema ----------------------


def test_every_line_belongs_to_one_session():
    assert len({line["sessionId"] for line in LINES}) == 1
    assert LINES[0]["type"] == "user"
    assert all("timestamp" in line for line in LINES if line["type"] in ("user", "assistant"))


def test_parent_links_form_one_chain():
    seen = set()
    for line in LINES:
        if "uuid" not in line:
            continue
        assert line["parentUuid"] is None or line["parentUuid"] in seen
        seen.add(line["uuid"])


def test_every_tool_use_has_a_matching_tool_result():
    used = {block["id"] for _, block in blocks("tool_use")}
    answered = {block["tool_use_id"] for _, block in blocks("tool_result")}
    assert used and used == answered


# --- The designed issues are really in the transcript --------------------


def test_first_prompt_is_vague_and_a_later_one_is_precise():
    prompts = human_prompts()
    assert prompts[0].startswith("fix the thing in the api")
    assert any("average_price" in p and "Do not change any other file" in p for p in prompts)


def test_user_corrects_the_agent_twice_before_the_good_prompt():
    prompts = human_prompts()
    good = next(i for i, p in enumerate(prompts) if "average_price" in p)
    assert good == 3
    assert prompts[1].startswith("no,") and prompts[2].startswith("NO.")


def test_agent_edits_the_wrong_file_first():
    edits = [block["input"]["file_path"] for _, block in blocks("tool_use") if block["name"] == "Edit"]
    assert edits[0].endswith("api/users.py")


def test_same_failing_command_runs_at_least_three_times():
    commands = [block["input"]["command"] for _, block in blocks("tool_use") if block["name"] == "Bash"]
    failing = [b for _, b in blocks("tool_result") if b.get("is_error")]
    assert commands.count("pytest tests/test_orders.py") >= 4
    assert len(failing) >= 3


def test_files_are_read_one_by_one_without_search_or_subagents():
    names = [block["name"] for _, block in blocks("tool_use")]
    assert names.count("Read") >= 4
    assert not {"Grep", "Glob", "Agent", "Task"} & set(names)


def test_fixture_project_has_no_instruction_file():
    assert not (FIXTURE / "CLAUDE.md").exists()
    assert not (FIXTURE / "AGENTS.md").exists()


def test_answer_key_covers_every_lens_and_issue_kind():
    assert set(KEY["lenses"]) == set(interaction_scoring.LENSES) | {"overall"}
    for band in KEY["lenses"].values():
        low, high = band["band"]
        assert 0 <= low < high <= 100
    kinds = {issue["kind"] for issue in KEY["issues"]}
    assert kinds == {"problem", "strength"}
    assert all(issue["keywords"] for issue in KEY["issues"])


# --- Scoring a report ------------------------------------------------------

REPORT = """---
title: "Interaction Review — 2026-11-09"
generated_by: "/interaction-review"
rubric_version: 2
rubric_date: "2026-11-09"
sessions_analyzed: 1
---

# Interaction Review

| Lens | Score | Grade | Trend |
|---|---|---|---|
| Prompt Craft | 58 | F | new |
| Workflow Efficiency | 45 [Coach: +5, fewer loops than drafted] | F | new |
| Agentic Leverage | 85 | B | new |
| Error Recovery & Adaptation | 40 | F | new |
| Context & Instruction | 30 | F | new |
| **Overall** | **53** | **F** | **new** |

The first prompt, "fix the thing in the api", was vague.
There is no CLAUDE.md in the project.
Your fourth prompt was precise and well-scoped.

| Lens | Previous | Current | Delta |
|---|---|---|---|
| Prompt Craft | 90 | 58 | -32 |
"""


def test_reads_front_matter_and_scorecard():
    result = interaction_scoring.score_interaction(REPORT, KEY)
    assert result["rubric_version"] == "2"
    assert result["lens_scores"] == {
        "prompt_craft": 58, "workflow_efficiency": 45, "agentic_leverage": 85,
        "error_recovery": 40, "context_instruction": 30,
    }
    assert result["overall_score"] == 53
    assert result["overall_grade"] == "F"


def test_checks_each_lens_against_its_band():
    result = interaction_scoring.score_interaction(REPORT, KEY)
    assert result["in_band"]["prompt_craft"] is True
    assert result["in_band"]["agentic_leverage"] is False
    assert result["in_band"]["overall"] is True
    assert result["out_of_band"] == ["agentic_leverage"]


def test_lists_designed_issues_the_report_mentions():
    result = interaction_scoring.score_interaction(REPORT, KEY)
    assert "vague-first-prompt" in result["issues_found"]
    assert "no-instruction-file" in result["issues_found"]
    assert "precise-follow-up" in result["issues_found"]
    assert "repeated-failing-command" in result["issues_missed"]
    problems = [i for i in KEY["issues"] if i["kind"] == "problem"]
    assert result["problem_recall"] == round(2 / len(problems), 3)
    assert result["strength_found"] is True


def test_empty_report_scores_nothing():
    result = interaction_scoring.score_interaction("", KEY)
    assert result["rubric_version"] is None
    assert result["lens_scores"] == {}
    assert all(value is None for value in result["in_band"].values())
    assert result["issues_found"] == []


def test_scorecard_reads_the_score_column_when_a_weight_column_comes_first():
    report = """
| Lens | Weight | Score | Grade | Trend |
|---|---|---|---|---|
| Prompt Craft | 30% | 58 | F | new |
| Workflow Efficiency | 25% | 52 | F | new |
| Agentic Leverage | 20% | 60 | D- | new |
| Error Recovery | 15% | 68 | D+ | new |
| Context & Instruction | 10% | 47 | F | new |
| **Overall** | | **57** | **F** | **new** |
"""
    card = interaction_scoring.read_scorecard(report)
    assert card["prompt_craft"] == (58, "F")
    assert card["error_recovery"] == (68, "D+")
    assert card["overall"] == (57, "F")
