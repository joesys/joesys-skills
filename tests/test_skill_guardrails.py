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


# --- Fable 5.2 review, 2026-11-10 -------------------------------------------
# Current models follow instructions more literally than the models these
# skills were first written for. Each test below pins one joesys decision.


def test_report_style_has_no_comma_counting_rule() -> None:
    # A hard style rule ("split at the second comma") makes prose choppy when
    # the model applies it to every sentence. The short-sentence rule stays.
    style = read("shared/report-style.md")
    assert "second comma" not in style
    assert "**Short sentences.** One idea per sentence." in style


def test_skills_do_not_name_host_specific_search_tools() -> None:
    # Glob and Grep are tool names in some hosts only. A skill should say
    # what to do ("search", "read"), so it works where those tools are absent.
    markdown_files = [*SKILLS.rglob("*.md"), *(REPO_ROOT / "shared").rglob("*.md")]
    assert markdown_files
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b(Glob|Grep)\b", text), path


def test_session_log_readers_state_a_goal_not_a_line_budget() -> None:
    # A fixed line budget forces sampling. The prompt states what to cover and
    # what to skip instead.
    interaction = compact(read("skills/interaction-review/references/agent-prompts.md"))
    assert "4,000" not in interaction
    assert "Cover every session" in interaction
    assert "Skip tool calls, tool output" in interaction

    retro = compact(read("skills/retrospective/references/agent-prompts.md"))
    assert "4,000" not in retro
    assert "Cover the whole retro period" in retro


def test_retro_narrative_prompt_uses_plain_wording() -> None:
    # The no-headers rule is a format contract (see output-formats.md), so it
    # stays, in normal case and with its reason. The word count goes.
    prompts = read("skills/retrospective/references/agent-prompts.md")
    assert "Target length" not in prompts
    assert "Do NOT" not in prompts
    assert "You are NOT" not in prompts
    assert "no headers, bullet points" in compact(prompts)


def test_claude_skill_lists_the_current_cli_flag_values() -> None:
    # Checked against `claude --help` on 2026-11-11.
    skill = read("skills/claude/SKILL.md")
    assert "(`manual`, `acceptEdits`, `auto`, `dontAsk`)" in skill
    assert "(`low`, `medium`, `high`, `xhigh`, `max`)" in skill


PLUGIN_ROOT_SECTION = (
    "## Plugin Root\n\n"
    "`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, "
    "your host did not fill it in; use the folder two levels above this SKILL.md "
    "instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill "
    "is under the plugin root, never under the project's working directory.\n"
)


def test_every_skill_states_the_plugin_root_once_with_a_host_neutral_fallback() -> None:
    # Claude Code fills in ${CLAUDE_PLUGIN_ROOT}. Other hosts do not, so the same
    # sentence must also say where the plugin root is without the variable.
    skill_files = sorted(SKILLS.glob("*/SKILL.md"))
    assert skill_files
    for skill_md in skill_files:
        text = skill_md.read_text(encoding="utf-8")
        assert text.count(PLUGIN_ROOT_SECTION) == 1, skill_md
        assert text.count("two levels above this SKILL.md") == 1, skill_md
        first_mention = text.index("plugin root")
        assert first_mention > text.index("## Plugin Root"), skill_md


def test_the_plugin_root_variable_stays_out_of_files_no_host_fills_in() -> None:
    # Claude Code replaces the variable only inside SKILL.md.
    other_files = [
        path
        for folder in (SKILLS, REPO_ROOT / "shared")
        for path in folder.rglob("*.md")
        if path.name != "SKILL.md"
    ]
    assert other_files
    for path in other_files:
        assert "CLAUDE_PLUGIN_ROOT" not in path.read_text(encoding="utf-8"), path


def test_review_prompts_point_at_the_code_instead_of_pasting_it() -> None:
    # A literal-minded model re-types every file into every reviewer prompt when
    # the template says to. Reviewers can read files and run git themselves.
    pasted_placeholders = (
        "<FILES_CONTENT>",
        "<DIFF_CONTENT",
        "<DIFF_U50>",
        "<DIFF_OR_CONTENT>",
        "<CHUNK_CONTENT_WITH_CONTEXT>",
    )
    for path in SKILLS.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for placeholder in pasted_placeholders:
            assert placeholder not in text, (path, placeholder)

    codereview = compact(read("skills/codereview/SKILL.md"))
    assert "Do not copy file contents or the diff into a prompt" in codereview
    assert codereview.count("<FILE_LIST>") >= 3
    assert codereview.count("<DIFF_COMMAND>") >= 3
    assert "git show <ref>:<path>" in codereview

    quick = compact(read("skills/quick-review/SKILL.md"))
    assert "<CODE_SOURCE>" in quick
    assert "Do not copy the diff or the files into the prompt" in quick

    readability = compact(read("skills/readability-review/SKILL.md"))
    assert "<FILE_LIST>" in readability
    assert "Do not copy file contents or the diff into the prompt" in readability

    guide = compact(read("skills/human-review-guide/SKILL.md"))
    assert "Do not copy the diff or the files into a prompt" in guide
    guide_prompts = read("skills/human-review-guide/references/agent-prompts.md")
    assert guide_prompts.count("<CONTENT_SOURCE>") == 2


def test_cross_model_prompt_gets_the_code_from_the_shell() -> None:
    # Codex and Antigravity run in a sandbox that may not read the project, so
    # their prompt file still holds the code. The shell appends it; the agent
    # does not type it.
    codereview = read("skills/codereview/SKILL.md")
    assert '>> "$PROMPT_FILE"' in codereview
    assert "Let the shell append" in compact(codereview)


def test_reviewers_read_the_reviewed_version_not_whatever_is_on_disk() -> None:
    # A pull request or an older commit may not be checked out. A reviewer that
    # reads files from disk would then judge the wrong version of the code.
    for relative in (
        "skills/codereview/SKILL.md",
        "skills/quick-review/SKILL.md",
        "skills/readability-review/SKILL.md",
        "skills/human-review-guide/SKILL.md",
    ):
        text = compact(read(relative))
        assert "git show <ref>:<path>" in text, relative
        assert "working tree does not hold the reviewed version" in text, relative
