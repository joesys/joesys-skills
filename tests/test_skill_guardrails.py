"""Guardrails found in the November 2026 skill review.

Each test pins one defect so it cannot come back: a skill that interviews the
user on first run, a reference file that tells a subagent to run a network
command without approval, or rules that contradict each other.
"""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = REPO_ROOT / "skills"


def read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.split())


def test_no_skill_runs_a_first_run_preference_interview() -> None:
    for skill_md in SKILLS.glob("*/SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        assert "First-Run Calibration" not in text, skill_md
        assert "First Run Behavior" not in text, skill_md


def test_review_principles_do_not_run_audit_tools_outside_the_safety_gate() -> None:
    text = read("skills/codereview/principles/security.md")
    assert not re.search(r"Run `(pip-audit|npm audit|cargo audit)`", text)


def test_extraction_rule_is_reuse_or_readability() -> None:
    # joesys decision (2026-11-09): split out a function when it is reused OR
    # when it makes the code read better. Either condition is enough.
    clean_code = compact(read("skills/codereview/principles/clean-code.md"))
    assert "Extract only when" not in clean_code
    assert "either" in clean_code.lower()


def test_quick_review_reports_only_p0_and_p1() -> None:
    skill = read("skills/quick-review/SKILL.md")
    readme = read("README.md")
    for text in (skill, readme):
        assert not re.search(r"P0[-–]P2", text)
    assert re.search(r"P0[-–]P1", skill)
    assert re.search(r"P0[-–]P1", readme)


def test_quick_review_fixes_code_when_explicitly_asked() -> None:
    skill = compact(read("skills/quick-review/SKILL.md"))
    assert "even when the user asks for them inline" not in skill
    assert "explicitly asks" in skill


def test_codebase_audit_large_tier_only_names_real_agents() -> None:
    skill = read("skills/codebase-audit/SKILL.md")
    roster = set(re.findall(r"^\| \d+ \| ([A-Za-z/]+) \|", skill, re.MULTILINE))
    named = re.search(r"qualitative agents\*\* \(([^)]*)\)", skill)
    assert roster
    if named:
        for name in re.split(r",\s*", named.group(1)):
            assert name.strip() in roster, name


def test_interaction_review_rubric_accepts_codex_instruction_files() -> None:
    rubric = read("skills/interaction-review/principles/context-instruction.md")
    assert "AGENTS.md" in rubric


def test_explain_unknown_flag_error_lists_every_flag() -> None:
    skill = read("skills/explain/SKILL.md")
    lines = [line for line in skill.splitlines() if "Unrecognized flag" in line]
    assert lines
    for line in lines:
        assert "--no-html" in line, line


def test_commit_example_uses_a_model_placeholder() -> None:
    assert "Opus 4.7" not in read("skills/commit/SKILL.md")


def test_html_report_snippet_uses_python3() -> None:
    assert '["python", ' not in read("shared/html-reports.md")
