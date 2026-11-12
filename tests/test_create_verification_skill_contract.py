"""Prompt-as-code contracts for the create-verification-skill skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "create-verification-skill"
CANONICAL_DIR = REPO_ROOT / "skills" / SKILL_NAME
CODEX_DIR = REPO_ROOT / "codex-skills" / SKILL_NAME
FEATURE_MAP_EXAMPLE = Path("references") / "feature-map-example.md"
FEATURE_FILE_HEADINGS = (
    "## Sub-features",
    "## How to get to it (user POV)",
    "## Driving it with ",
    "## Gotchas",
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
        assert "uses it the way a user does" in frontmatter
        assert "captures proof" in frontmatter

    assert "/create-verification-skill <app or folder>" in canonical
    assert "$create-verification-skill <app or folder>" in codex
    assert "/create-verification-skill <app or folder>" not in codex


def test_generated_skill_goes_to_the_project_skill_folder_of_each_host() -> None:
    # Claude Code reads project skills from `.claude/skills/`. Codex reads them
    # from `.agents/skills/`. A Codex copy that names the Claude Code folder
    # writes a skill that Codex never finds.
    canonical, codex = skills()

    assert ".claude/skills/verify-<app>/" in canonical
    assert ".agents/skills/verify-<app>/" in codex
    for path in sorted(CODEX_DIR.rglob("*.md")):
        assert ".claude/skills/" not in read(path), path

    for skill in (canonical, codex):
        assert "say which folder you used" in compact(skill)


def test_generated_skill_has_the_six_sections() -> None:
    for skill in skills():
        for section in ("Launch", "Doctor", "Drive", "Evidence", "Cleanup", "Helpers"):
            assert f"| **{section}** |" in skill, section


def test_feature_map_uses_four_fixed_headings() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "features/README.md" in normalized
        for heading in FEATURE_FILE_HEADINGS:
            assert f"`{heading.removeprefix('## ').strip()}" in normalized, heading
        assert "Never weaken a journey to make it pass" in normalized

    for folder in (CANONICAL_DIR, CODEX_DIR):
        example = read(folder / FEATURE_MAP_EXAMPLE)
        for heading in FEATURE_FILE_HEADINGS:
            assert heading in example, (folder, heading)


def test_generated_skill_is_run_once_before_it_is_handed_over() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "A generated skill that was never run is a draft" in normalized
        assert "confirm that the evidence still exists" in normalized
        assert "Run the generated cleanup after every failed attempt" in normalized


def test_skill_protects_secrets_processes_and_product_code() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "Never read secrets" in normalized
        assert "Never stop a process by name" in normalized
        assert "does not change product code" in normalized
        assert "does not commit, push, or open a pull request" in normalized
        assert "Ask before a live call" in normalized


def test_every_proof_says_whether_a_service_was_live_or_fake() -> None:
    # joesys rule: passing with a fake provider does not prove that the live
    # integration works. The proof must say which one it used.
    for skill in skills():
        normalized = compact(skill)
        assert "Label every proof `live` or `fake`" in normalized
        assert "does not prove that the live service works" in normalized


def test_skill_points_at_nothing_this_collection_lacks() -> None:
    # The source skill names a maintenance skill and a Cursor folder. Neither
    # exists here, so a pointer to them would send the reader nowhere.
    for folder in (CANONICAL_DIR, CODEX_DIR):
        for path in sorted(folder.rglob("*.md")):
            text = read(path)
            assert "maintain-verification-skill" not in text, path
            assert ".cursor" not in text, path


def test_skill_carries_the_license_notice_of_its_source() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        notice = read(folder / "NOTICE.md")
        assert "Copyright (c) 2026 Lauren Tan" in notice
        assert "Permission is hereby granted, free of charge" in notice
        assert "NOTICE.md" in read(folder / "SKILL.md")


def test_readme_and_interfaces_list_the_skill() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert "A collection of 21 agent skills" in readme
    assert "| Verify | [`create-verification-skill`](#create-verification-skill) |" in readme
    assert "### create-verification-skill" in readme

    interfaces = read(REPO_ROOT / "shared" / "skill-interfaces.md")
    assert "## Create Verification Skill Interface" in interfaces
