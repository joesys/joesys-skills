"""Prompt-as-code contracts for the maintain-verification-skill skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "maintain-verification-skill"
CANONICAL_DIR = REPO_ROOT / "skills" / SKILL_NAME
CODEX_DIR = REPO_ROOT / "codex-skills" / SKILL_NAME
CREATE_DIRS = (
    REPO_ROOT / "skills" / "create-verification-skill",
    REPO_ROOT / "codex-skills" / "create-verification-skill",
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
        assert "back in line with the app" in frontmatter
        assert "has no verification skill yet" in frontmatter

    assert "/maintain-verification-skill <skill name or folder>" in canonical
    assert "$maintain-verification-skill <skill name or folder>" in codex
    assert "/maintain-verification-skill <skill name" not in codex


def test_target_is_the_project_skill_folder_of_each_host() -> None:
    canonical, codex = skills()

    assert ".claude/skills/verify-*/" in canonical
    assert ".agents/skills/verify-*/" in codex
    assert ".claude/skills/" not in codex

    for skill in (canonical, codex):
        normalized = compact(skill)
        assert "stop and point to" in normalized
        assert "Do not invent a target" in normalized


def test_pass_has_one_of_three_outcomes_and_states_its_coverage() -> None:
    for skill in skills():
        for outcome in ("clean", "changed", "blocked"):
            assert f"- **{outcome}**" in skill, outcome
        normalized = compact(skill)
        assert "how many features were driven out of how many" in normalized
        assert "cannot be `clean`" in normalized


def test_corrections_stay_uncommitted() -> None:
    # The source skill ships its corrections as one pull request. joesys
    # rule: no commit, no push, and no pull request without approval.
    for skill in skills():
        normalized = compact(skill)
        assert "does not commit, push, or open a pull request" in normalized
        assert "leaves its corrections uncommitted and lists them" in normalized
        for word in ("one PR", "No branch, no PR"):
            assert word not in skill, word


def test_only_the_verification_skill_folder_is_edited() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "Edit only the verification skill's own folder" in normalized
        assert "Never edit product code" in normalized
        assert "do not hide it in the map" in normalized


def test_every_feature_is_read_from_source_and_driven_live() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "one read-only subagent for each feature file" in normalized
        assert "Let every subagent inherit the parent model and reasoning effort" in normalized
        assert "Required even when the source looks clean" in normalized
        assert "Correct only what a run proved" in normalized
        assert "drive it again" in normalized


def test_live_pass_keeps_three_rules() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "Run Doctor before the first drive" in normalized
        assert "again after any failed drive" in normalized
        assert "The evidence survives every cleanup" in normalized
        assert "Nothing that a drive started outlives the drive" in normalized


def test_paid_and_outside_calls_need_approval_and_a_label() -> None:
    # The generated feature files name each outside service in their first
    # precondition. The pass drives every feature, so it must ask first.
    for skill in skills():
        normalized = compact(skill)
        assert "Never read secrets" in normalized
        assert "Ask before a live call" in normalized
        assert "Ask once, before the live pass" in normalized
        assert "`live` or `fake`" in normalized
        assert "Never drive an instance that you did not start" in normalized
        assert "Never stop a process by name" in normalized


def test_index_marks_are_brought_up_to_date() -> None:
    # /create-verification-skill marks each feature `run` with a date, or
    # `not run`. After a pass, an old date would be a false mark.
    for skill in skills():
        normalized = compact(skill)
        assert "`run` with today's date" in normalized
        assert "`not run` with the reason" in normalized


def test_create_skill_points_at_the_maintenance_pass() -> None:
    for folder in CREATE_DIRS:
        create = compact(read(folder / "SKILL.md"))
        assert "maintain-verification-skill" in create, folder
        assert "after the app changes" in create, folder


def test_skill_names_no_other_host() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        paths = sorted(folder.rglob("*.md"))
        assert paths, folder
        for path in paths:
            if path.name == "NOTICE.md":
                continue
            assert ".cursor" not in read(path), path


def test_skill_carries_the_license_notice_of_its_source() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        notice = read(folder / "NOTICE.md")
        assert "Copyright (c) 2026 Lauren Tan" in notice
        assert "Permission is hereby granted, free of charge" in notice
        assert "NOTICE.md" in read(folder / "SKILL.md")


def test_readme_and_interfaces_list_the_skill() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert "| Verify | [`maintain-verification-skill`](#maintain-verification-skill) |" in readme
    assert "### maintain-verification-skill" in readme

    interfaces = read(REPO_ROOT / "shared" / "skill-interfaces.md")
    assert "## Maintain Verification Skill Interface" in interfaces


# --- Sample run, on an app made for the run, 2026-11-12 ----------------------
# Each test below pins one gap that the run showed in the skill text.


def test_a_feature_without_a_file_gets_one() -> None:
    # The sample app had a command that the map did not list. The text said
    # how to recognise a missing feature, and not what to do with it.
    for skill in skills():
        normalized = compact(skill)
        assert "| A user-facing feature has no file |" in normalized
        assert "Drive it first" in normalized
        assert "add it to the index" in normalized


def test_mark_says_when_a_drive_hit_a_product_problem() -> None:
    # One feature was driven and one of its steps failed because the app was
    # wrong. A bare `run` mark would have read as "works".
    for skill in skills():
        normalized = compact(skill)
        assert "name the step that fails in the mark" in normalized
        assert "The recipe itself stays as it is" in normalized
