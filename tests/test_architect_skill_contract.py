"""Prompt-as-code contracts for the architect skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "architect"
CANONICAL_DIR = REPO_ROOT / "skills" / SKILL_NAME
CODEX_DIR = REPO_ROOT / "codex-skills" / SKILL_NAME
CANDIDATE_BRIEF = Path("references") / "candidate-brief.md"
RED_FLAGS = Path("references") / "design-red-flags.md"
DESIGN_PACKAGE = Path("references") / "design-package.md"
RED_FLAG_HEADINGS = (
    "## Shallow module",
    "## Information leakage",
    "## Split by time",
    "## Pass-through method",
    "## Split ownership",
    "## Two ways to do one task",
    "## Importable internals",
    "## Hand-synced list",
)
PACKAGE_SECTIONS = (
    "## Problem",
    "## Usage (caller's view)",
    "## Shape",
    "## How the candidates were merged",
    "## Trade-offs accepted",
    "## Alternatives considered",
    "## Open questions and risks",
    "## First step to build",
    "## When to throw this design away",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.split())


def skills() -> tuple[str, str]:
    paths = (CANONICAL_DIR / "SKILL.md", CODEX_DIR / "SKILL.md")
    missing = [str(path.relative_to(REPO_ROOT)) for path in paths if not path.is_file()]
    assert not missing, f"Missing skill files: {', '.join(missing)}"
    return read(paths[0]), read(paths[1])


def test_skill_is_discoverable_on_both_hosts() -> None:
    canonical, codex = skills()

    for skill in (canonical, codex):
        frontmatter = skill.split("---", 2)[1]
        assert f"name: {SKILL_NAME}" in frontmatter
        assert "design the shape of new code before anyone writes it" in frontmatter
        assert "building is a separate request" in frontmatter

    assert "`/architect <what to design>`" in canonical
    assert "`$architect <what to design>`" in codex
    assert "/architect <what to design>" not in codex


def test_skill_designs_and_stops() -> None:
    # The source skill goes on to implement the design, with no checkpoint
    # by default. joesys rule: approval of a plan is not approval to build.
    for skill in skills():
        normalized = compact(skill)
        assert "writes no code file in the project" in normalized
        assert "does not implement the design, commit, push, or open a pull request" in normalized
        assert "Approval of a design is not approval to build it" in normalized
        assert "Then stop. Do not start to build." in normalized
        for phase in ("Phase D", "Implement against the sketch", "No human checkpoint"):
            assert phase not in skill, phase


def test_at_least_two_candidates_differ_in_their_whole_shape() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "at least two candidates that differ in their whole shape" in normalized
        assert "One candidate is not a comparison" in normalized
        assert "| **Host candidate** | Always |" in skill
        assert "| **Other models** | Unless `--local` |" in skill
        assert "Let every subagent inherit the parent model and reasoning effort" in normalized


def test_other_models_are_called_the_way_the_review_skill_calls_them() -> None:
    # The source skill gets its candidates from a multi-model skill that this
    # collection does not have. The candidates are text, so the read-only
    # dispatch of /codereview can produce them.
    canonical, codex = skills()
    assert "`shared/cross-model-dispatch.md`" in canonical
    assert "`../shared/cross-model-dispatch.md`" in codex

    for skill in (canonical, codex):
        normalized = compact(skill)
        assert "150,000 bytes" in normalized
        assert "Let the shell append" in normalized
        assert "Never put a secret" in normalized

    for shared in (REPO_ROOT / "shared", REPO_ROOT / "codex-skills" / "shared"):
        assert "architect" in read(shared / "cross-model-dispatch.md"), shared
        assert "architect" in read(shared / "model-defaults.md"), shared


def test_rubric_is_hidden_and_the_host_family_gets_no_bonus() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "Candidates do not see it" in normalized
        assert "criterion by criterion" in normalized
        assert "Do not favour the candidate from your own model family" in normalized


def test_candidate_brief_puts_the_caller_first_and_returns_text_only() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        brief = compact(read(folder / CANDIDATE_BRIEF))
        assert "**Caller's usage first.**" in brief
        assert "**Data structures first.**" in brief
        assert "`not implemented`" in brief
        assert "Return text only" in brief
        assert "Do not aim for a safe middle" in brief
        assert brief.index("**Caller's usage first.**") < brief.index("**Data structures first.**")


def test_red_flags_are_the_eight_of_the_source() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        flags = read(folder / RED_FLAGS)
        for heading in RED_FLAG_HEADINGS:
            assert heading in flags, (folder, heading)


def test_design_package_has_nine_sections_in_order() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        package = read(folder / DESIGN_PACKAGE)
        positions = [package.index(section) for section in PACKAGE_SECTIONS]
        assert positions == sorted(positions), folder

    for skill in skills():
        assert "`references/design-package.md`" in skill


def test_sibling_skills_are_options_not_steps() -> None:
    canonical, _ = skills()
    normalized = compact(canonical)
    assert "`/explain <path>` is an option" in normalized
    assert "`/why <target>` is an option" in normalized


def test_skill_names_nothing_of_the_source_host() -> None:
    banned = ("arena", "pstack-models", ".cursor", "grok-", "claude-opus", "interrogate")
    for folder in (CANONICAL_DIR, CODEX_DIR):
        paths = sorted(folder.rglob("*.md"))
        assert paths, folder
        for path in paths:
            if path.name == "NOTICE.md":
                continue
            text = read(path)
            for word in banned:
                assert word not in text, (path, word)


def test_skill_carries_the_license_notice_of_its_source() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        notice = read(folder / "NOTICE.md")
        assert "Copyright (c) 2026 Lauren Tan" in notice
        assert "Permission is hereby granted, free of charge" in notice
        assert "NOTICE.md" in read(folder / "SKILL.md")


def test_readme_and_interfaces_list_the_skill() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert "| Design | [`architect`](#architect) |" in readme
    assert "### architect" in readme

    interfaces = read(REPO_ROOT / "shared" / "skill-interfaces.md")
    assert "## Architect Interface" in interfaces
