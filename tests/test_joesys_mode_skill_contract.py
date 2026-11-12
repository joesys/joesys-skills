"""Prompt-as-code contracts for the joesys-mode skill."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = REPO_ROOT / "skills" / "joesys-mode"
CODEX_DIR = REPO_ROOT / "codex-skills" / "joesys-mode"

# joesys decision (2026-11-12): the mode carries all 24 poteto-mode principles
# and the 8 ub-mode sections, in ub-mode's three phases.
FIRST_MAKE_IT_WORK = (
    "Laziness Protocol",
    "Foundational Thinking",
    "TDD",
    "Redesign from First Principles",
    "Attack the Premise",
    "Subtract Before You Add",
    "Outcome-Oriented Execution",
    "Build the Lever",
    "Experience First",
    "Exhaust the Design Space",
    "Model the Domain",
    "Boundary Discipline",
    "Type System Discipline",
    "Make Operations Idempotent",
    "Separate Before Serializing Shared State",
    "Migrate Callers Then Delete Legacy APIs",
)
THEN_MAKE_IT_RIGHT = (
    "Fix Root Causes",
    "Sequence Work into Verifiable Units",
    "Test Behavior, Not Implementation",
    "Prove It Works",
    "Explain the Number",
    "Minimize Reader Load",
    "Crapper",
    "Dryer",
    "Mutator",
    "Refactoring",
)
PRACTICE = (
    "Keep a Log",
    "Guard the Context Window",
    "Never Block on the Human",
    "Encode Lessons in Structure",
    "Worktree Cleanup",
    "Commit Often, Never Push Unasked",
)
PRINCIPLES = FIRST_MAKE_IT_WORK + THEN_MAKE_IT_RIGHT + PRACTICE
STEP_LISTS = ("Investigation", "Bug fix", "Feature", "Refactoring")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.split())


def skills() -> tuple[str, str]:
    paths = (CANONICAL_DIR / "SKILL.md", CODEX_DIR / "SKILL.md")
    missing = [str(path.relative_to(REPO_ROOT)) for path in paths if not path.is_file()]
    assert not missing, f"Missing skill files: {', '.join(missing)}"
    return read(paths[0]), read(paths[1])


def section(skill: str, heading: str) -> str:
    """Return one `## ` section, without the sections after it."""
    start = skill.index(f"\n## {heading}\n")
    end = skill.find("\n## ", start + 1)
    return skill[start:] if end == -1 else skill[start:end]


def step_list(skill: str, name: str) -> str:
    lists = section(skill, "Step Lists")
    start = lists.index(f"\n### {name}\n")
    end = lists.find("\n### ", start + 1)
    return lists[start:] if end == -1 else lists[start:end]


def test_skill_is_discoverable_on_both_hosts() -> None:
    canonical, codex = skills()

    for skill in (canonical, codex):
        frontmatter = skill.split("---", 2)[1]
        assert "name: joesys-mode" in frontmatter
        assert "joesys-mode" in frontmatter.split("description:", 1)[1]

    assert "/joesys-mode <task>" in canonical
    assert "$joesys-mode <task>" in codex
    assert "/joesys-mode <task>" not in codex


def test_all_32_principles_are_present_in_their_three_phases() -> None:
    assert len(PRINCIPLES) == 32
    for skill in skills():
        principles = section(skill, "The Principles")
        work = principles.index("\n### First Make it Work\n")
        right = principles.index("\n### Then Make it Right\n")
        practice = principles.index("\n### Practice\n")
        assert work < right < practice

        positions = [principles.index(f"- **{name}.**") for name in PRINCIPLES]
        assert positions == sorted(positions), "principles are out of order"
        assert principles.count("\n- **") == 32

        for name in FIRST_MAKE_IT_WORK:
            assert work < principles.index(f"- **{name}.**") < right, name
        for name in THEN_MAKE_IT_RIGHT:
            assert right < principles.index(f"- **{name}.**") < practice, name
        for name in PRACTICE:
            assert practice < principles.index(f"- **{name}.**"), name


def test_principles_come_before_everything_that_uses_them() -> None:
    # joesys (2026-11-12): "don't let these principles get lost in the sea of
    # instructions". They come first, the file stays short, and nothing else
    # may grow in front of them.
    for skill in skills():
        principles = skill.index("\n## The Principles\n")
        for later in ("Step Lists", "Ask First", "The Reply", "Final Check"):
            assert principles < skill.index(f"\n## {later}\n"), later
        assert len(skill.splitlines()) <= 240
        principle_lines = len(section(skill, "The Principles").splitlines())
        assert principle_lines * 3 >= len(skill.splitlines()), (
            "the principles are less than a third of the file"
        )


def test_every_step_names_principles_and_every_list_ends_in_a_check() -> None:
    expected = {
        "Investigation": ("Prove It Works",),
        "Bug fix": ("Fix Root Causes", "Attack the Premise", "TDD"),
        "Feature": ("Model the Domain", "Subtract Before You Add", "TDD"),
        "Refactoring": (
            "Subtract Before You Add",
            "Migrate Callers Then Delete Legacy APIs",
            "Minimize Reader Load",
        ),
    }
    for skill in skills():
        for name in STEP_LISTS:
            numbered = re.findall(r"^\d+\. .*$", step_list(skill, name), re.MULTILINE)
            assert numbered, name
            assert numbered[-1].split(". ", 1)[1].startswith("**Check.**"), (
                name,
                "the last step must be the check",
            )
            # A long principle name may wrap over two lines.
            steps = compact(step_list(skill, name))
            for principle in expected[name]:
                assert principle in steps, (name, principle)
        assert "If none fits" in section(skill, "Step Lists")


def test_task_starts_with_the_goal_and_reply_names_the_principles_used() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "restate the user's goal in your own words" in normalized
        reply = compact(section(skill, "The Reply"))
        assert "Name each principle that changed a decision, and the choice it changed" in reply
        assert "Do not list a principle that changed nothing" in reply
        assert "measured, inferred, or guess" in reply
        assert '"No" is an acceptable answer' in reply


def test_project_rules_and_the_user_win_over_the_mode() -> None:
    for skill in skills():
        assert (
            "The project's own rules and the user's current message win over this mode"
            in compact(skill)
        )


def test_the_three_changes_from_the_sources_hold() -> None:
    # joesys approved these on 2026-11-12. poteto-mode proceeds without asking
    # and opens pull requests. ub-mode pushes to the main line and requires
    # three tools.
    for skill in skills():
        principles = compact(section(skill, "The Principles"))
        assert "do reversible local work without asking" in principles
        assert "This does not cover anything under Ask First" in principles
        assert "If a tool is not installed, say that you skipped it. Do not install it." in principles
        assert "Push to the main line" not in skill

        ask_first = compact(section(skill, "Ask First"))
        assert "Never push" in ask_first
        assert "never open a pull request" in ask_first
        assert "Approval of a plan is not approval to build it" in ask_first
        assert "Never read, print, or copy a secret value" in ask_first


def test_only_commit_is_run_and_other_siblings_are_options() -> None:
    canonical, codex = skills()
    assert "The only sibling skill this mode runs by itself is `/commit`" in compact(canonical)
    assert "The only sibling skill this mode runs by itself is `$commit`" in compact(codex)
    for option in ("/explain", "/create-verification-skill"):
        assert f"`{option}`" in canonical, option

    interfaces = read(REPO_ROOT / "shared" / "skill-interfaces.md")
    assert "## Joesys Mode Interface" in interfaces
    commit_interface = interfaces.split("## Commit Skill Interface", 1)[1].split("\n## ", 1)[0]
    assert "skills/joesys-mode/SKILL.md" in commit_interface


def test_skill_names_nothing_this_collection_lacks() -> None:
    # The source modes route to skills, agents and host features that do not
    # exist here.
    absent = (
        "poteto-agent",
        "Cursor",
        "Bugbot",
        "swarm",
        "arena",
        "interrogate",
        "unslop",
        "architect",
    )
    for skill in skills():
        for name in absent:
            assert name not in skill, name


def test_skill_carries_the_license_notices_of_both_sources() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        notice = read(folder / "NOTICE.md")
        assert "Copyright (c) 2026 Lauren Tan" in notice
        assert "Copyright (c) 2026 Robert C. Martin" in notice
        assert "Permission is hereby granted, free of charge" in notice
        assert "NOTICE.md" in read(folder / "SKILL.md")


def test_readme_lists_the_skill() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert "| Work | [`joesys-mode`](#joesys-mode) |" in readme
    assert "### joesys-mode" in readme
