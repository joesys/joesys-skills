"""Prompt-as-code contracts for the create-formal-verification-skill skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "create-formal-verification-skill"
CANONICAL_DIR = REPO_ROOT / "skills" / SKILL_NAME
CODEX_DIR = REPO_ROOT / "codex-skills" / SKILL_NAME
QUALITIES = (
    "True to the code",
    "Able to fail",
    "Findings stay findings",
    "Honest about scope",
    "Readable without the tool",
    "Cheap to rerun",
    "Kept in step with the code",
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
        assert "every case in a stated scope" in frontmatter
        assert "model checker" in frontmatter

    assert "/create-formal-verification-skill <area, file, or bug>" in canonical
    assert "$create-formal-verification-skill <area, file, or bug>" in codex


def test_the_two_verification_skills_point_at_each_other() -> None:
    canonical, codex = skills()
    assert "/create-verification-skill" in canonical.split("---", 2)[1]
    assert "$create-verification-skill" in codex.split("---", 2)[1]

    other = read(REPO_ROOT / "skills" / "create-verification-skill" / "SKILL.md")
    assert "/create-formal-verification-skill" in other.split("---", 2)[1]


def test_generated_skill_has_its_own_prefix_and_folder_on_each_host() -> None:
    # `verify-<app>` already means the skill that drives the running app.
    # The formal skill writes `formal-<area>`, so the two never share a name.
    canonical, codex = skills()

    assert ".claude/skills/formal-<area>/" in canonical
    assert ".agents/skills/formal-<area>/" in codex
    for path in sorted(CODEX_DIR.rglob("*.md")):
        assert ".claude/skills/" not in read(path), path
    for skill in (canonical, codex):
        assert "say which folder you used" in compact(skill)
        assert ".claude/skills/verify-" not in skill
        assert ".agents/skills/verify-" not in skill


def test_the_seven_qualities_of_a_good_verification_are_named() -> None:
    for skill in skills():
        for quality in QUALITIES:
            assert f"**{quality}.**" in skill, quality


def test_a_check_must_be_seen_to_fail_and_to_reach_its_states() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "A check that you have never seen fail proves nothing" in normalized
        assert "Show that the check reaches the states it is about" in normalized


def test_a_code_change_makes_the_check_command_fail() -> None:
    # A model checker reads the model, not the code. Without this rule, a
    # changed function still passes, and the pass looks like a proof.
    for skill in skills():
        normalized = compact(skill)
        assert "sync commit" in normalized
        assert (
            "The check command itself fails when the covered code differs from the code at the sync commit"
            in normalized
        )
        assert "Move the sync commit forward only after" in normalized


def test_findings_are_reported_and_never_hidden() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "Do not weaken the property or the model until it passes" in normalized
        assert "Do not change product code unless the user asks" in normalized
        assert "does not commit, push, or open a pull request" in normalized


def test_skill_is_proven_on_a_real_break_before_hand_off() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "A verify skill that was never run is a draft" in normalized
        assert "a scratch change that breaks the property in the real code" in normalized
        assert "It must catch the break" in normalized
        assert "fix the skill or the verification, not the scratch change" in normalized
        assert "confirm that the working tree is as it was" in normalized


def test_target_is_the_strongest_one_and_the_runner_up_is_named() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "not the one that is easiest to verify" in normalized
        assert "name the runner-up" in normalized
        assert "Read the existing tests for the target" in normalized


def test_skill_asks_before_it_installs_a_tool() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "Ask before you install a tool" in normalized
        assert "the exact version and a checksum" in normalized


def test_skill_points_at_nothing_this_collection_lacks() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        for path in sorted(folder.rglob("*.md")):
            text = read(path)
            assert "statechart" not in text, path
            assert "maintain-formal-verification-skill" not in text, path
            assert ".cursor" not in text, path


def test_skill_carries_the_license_notice_of_its_source() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        notice = read(folder / "NOTICE.md")
        assert "Copyright (c) 2026 Lauren Tan" in notice
        assert "Permission is hereby granted, free of charge" in notice
        assert "NOTICE.md" in read(folder / "SKILL.md")


def test_readme_and_interfaces_list_the_skill() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert (
        "| Verify | [`create-formal-verification-skill`](#create-formal-verification-skill) |"
        in readme
    )
    assert "### create-formal-verification-skill" in readme

    interfaces = read(REPO_ROOT / "shared" / "skill-interfaces.md")
    assert "## Create Formal Verification Skill Interface" in interfaces


# --- First live run, on a real project, 2026-11-12 ---------------------------
# Each test below pins one gap that the run showed in the skill text.


def test_check_can_run_the_verification_alone_during_an_update() -> None:
    # The check fails as soon as the covered code changes. So during an
    # intended change, the second run could never reach the counterexample.
    for skill in skills():
        normalized = compact(skill)
        assert "a way to run the verification alone" in normalized
        assert "Use it only during an update" in normalized
        assert "Run the verification alone. It fails with a counterexample" in normalized


def test_tool_and_its_output_stay_out_of_version_control() -> None:
    # The model checker writes state folders and copies of its standard
    # modules. The downloaded tool itself is a 2 MB file.
    for skill in skills():
        normalized = compact(skill)
        assert "in its own folder that version control ignores" in normalized
        assert "The tool's own output files go to an ignored folder" in normalized


def test_one_promise_may_need_several_properties() -> None:
    # The first target made one promise in its doc comment. Checking it took
    # three rules.
    for skill in skills():
        assert "verifies one promise there, as one or more properties" in compact(skill)
