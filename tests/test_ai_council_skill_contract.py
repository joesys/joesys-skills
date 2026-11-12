"""Prompt-as-code contracts for the ai-council skill."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "ai-council"
CANONICAL = REPO_ROOT / "skills" / SKILL_NAME / "SKILL.md"
CODEX = REPO_ROOT / "codex-skills" / SKILL_NAME / "SKILL.md"
GROK_RUN_LINE = '<GROK_CMD> --session-id "$SESSION_ID" 2><RUN_DIR>/grok.log'


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.split())


def skills() -> tuple[str, str]:
    return read(CANONICAL), read(CODEX)


def grok_block(skill: str) -> str:
    blocks = re.findall(r"```bash\n(.*?)```", skill, re.S)
    found = [block for block in blocks if "<GROK_CMD>" in block]
    assert len(found) == 1, "the council must run Grok in exactly one shell block"
    return found[0]


# First live council with four members: 2026-11-12, in Claude Code, with
# grok 1.0.77, on a general question and with `--no-save`. All four legs
# answered. Grok's error output was empty, and its session ID was printed.
# The tests below pin the text that this run followed.


def test_council_has_four_members() -> None:
    # joesys decision (2026-11-12): Grok joins Claude, GPT and Antigravity.
    for skill in skills():
        frontmatter = skill.split("---", 2)[1]
        assert "four frontier AI models (Claude, GPT, Antigravity, Grok)" in frontmatter

        normalized = compact(skill)
        assert "(Claude leg, Codex leg, Antigravity leg, Grok leg)" in normalized
        assert "The **council** is all four" in normalized
        assert "[Claude/GPT/Antigravity/Grok]" in normalized
        assert "Launch all four legs in a single response" in normalized
        assert "columns are Claude, GPT, Antigravity, and Grok" in normalized
        # No sentence still counts three members.
        assert "three" not in skill.lower()


def test_failure_limits_fit_four_members() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "if two or more legs failed, warn that the council is degraded" in normalized
        assert "If all four fail" in normalized


def test_grok_leg_uses_the_one_read_only_template() -> None:
    # shared/model-defaults.md holds the only Grok command. Its flags keep
    # Grok from writing files. A second copy here could lose one of them.
    for skill in skills():
        lines = skill.splitlines()
        assert not [line for line in lines if line.startswith("grok ")]
        runs = [line for line in lines if line.startswith("<GROK_CMD>")]
        assert runs == [GROK_RUN_LINE]
        assert "Do not change the template" in compact(skill)

    canonical, codex = skills()
    assert "`shared/model-defaults.md` § Grok" in canonical
    assert "`../shared/model-defaults.md` Section Grok" in codex


def test_grok_leg_runs_in_one_shell_call() -> None:
    # Grok does not read the prompt from stdin, and a shell variable is gone
    # by the next call. So the prompt path, the session ID, the run, and the
    # log all sit in one block.
    for skill in skills():
        block = grok_block(skill)
        order = [
            "PROMPT_FILE=<RUN_DIR>/grok.txt",
            "SESSION_ID=$(python3 -c 'import uuid; print(uuid.uuid4())')",
            GROK_RUN_LINE,
            'echo "session id: $SESSION_ID"',
            "cat <RUN_DIR>/grok.log",
        ]
        positions = [block.index(part) for part in order]
        assert positions == sorted(positions)


def test_grok_answer_that_was_cut_short_is_a_partial_leg() -> None:
    # Checked with live runs of grok 1.0.77 on 2026-11-12: when Grok needs an
    # approval that nobody can give, it stops with exit code 0. One stderr
    # line is the only sign.
    for skill in skills():
        normalized = compact(skill)
        assert "Never discard Grok's stderr" in normalized
        assert "`permission required:`" in normalized
        assert "that leg is partial" in normalized
        for line in skill.splitlines():
            if "GROK_CMD" in line:
                assert "2>/dev/null" not in line


def test_grok_prompt_starts_with_the_role_line() -> None:
    # Grok reads a prompt that starts with `/` as one of its own commands.
    for skill in skills():
        assert "Keep the role preamble as the first line" in compact(skill)


def test_grok_files_keep_their_paths_in_the_codex_copy() -> None:
    # The Codex copy once turned `<RUN_DIR>/codex.txt` into
    # `<RUN_DIR>$codex.txt`. The Grok files must not go the same way.
    for skill in skills():
        assert "cat > <RUN_DIR>/grok.txt << 'PROMPT_EOF'" in skill
        assert "2><RUN_DIR>/grok.log" in skill
        assert "<RUN_DIR>$" not in skill


def test_grok_leg_can_be_resumed_and_is_saved() -> None:
    canonical, codex = skills()
    assert "`/grok resume <SESSION_ID>`" in canonical
    assert "`$grok resume <SESSION_ID>`" in codex
    for skill in (canonical, codex):
        assert "grok.md" in skill


def test_readme_interfaces_and_defaults_name_the_fourth_member() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert "Ask Claude, Codex, Antigravity, and Grok, then synthesize their views" in readme
    assert "Consult Claude, Codex, Antigravity, and Grok in parallel" in readme

    interfaces = compact(read(REPO_ROOT / "shared" / "skill-interfaces.md"))
    assert "item 1 (Codex, Antigravity, Claude, and Grok)" in interfaces
    assert "Grok resume has no caller" not in interfaces

    defaults = read(REPO_ROOT / "shared" / "model-defaults.md")
    assert "| xAI (Grok CLI) | *(managed by grok)* | `/grok`, `/ai-council` |" in defaults
