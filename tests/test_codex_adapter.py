"""Tests for building and installing Codex-ready joesys skills."""

import json
import os
import sys
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import codex_adapter
import install_codex_skills


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {
    "ai-council",
    "antigravity",
    "claude",
    "codebase-audit",
    "codereview",
    "codex",
    "commit",
    "dashboard",
    "devlog",
    "explain",
    "export",
    "handbook",
    "human-review-guide",
    "interaction-review",
    "preferences",
    "quick-review",
    "readability-review",
    "retrospective",
    "ss",
}


def test_build_collection_generates_all_skills_without_touching_source(tmp_path):
    source_skill = REPO_ROOT / "skills" / "codereview" / "SKILL.md"
    before = source_skill.read_bytes()

    output = tmp_path / "joesys-skills"
    manifest = codex_adapter.build_collection(REPO_ROOT, output)

    assert source_skill.read_bytes() == before
    assert set(manifest["installed_skills"]) == EXPECTED_SKILLS
    for skill_name in EXPECTED_SKILLS:
        assert (output / skill_name / "SKILL.md").is_file()


def test_generated_skill_frontmatter_is_valid_for_codex(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    skill_text = (output / "codereview" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1]

    assert "name: codereview" in frontmatter
    assert "description:" in frontmatter
    assert "version:" not in frontmatter
    assert "runtime:" not in frontmatter
    assert "/joesys-codereview" in frontmatter


def test_generated_skills_reference_installed_collection_resources(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    code_review = (output / "codereview" / "SKILL.md").read_text(encoding="utf-8")
    export = (output / "export" / "SKILL.md").read_text(encoding="utf-8")

    assert "~/.codex/skills/joesys-skills/shared/review-common.md" in code_review
    assert "~/.codex/skills/joesys-skills/codereview/principles/clean-code.md" in code_review
    assert "~/.codex/skills/joesys-skills/scripts/md_export.py" in export
    assert (output / "shared" / "review-common.md").is_file()
    assert (output / "scripts" / "md_export.py").is_file()


def test_generated_skill_markdown_is_ascii_for_windows_validator(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    for skill_md in output.glob("*/SKILL.md"):
        skill_md.read_text(encoding="ascii")


def test_generated_package_does_not_bundle_installer_tools(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    assert not (output / "scripts" / "codex_adapter.py").exists()
    assert not (output / "scripts" / "install_codex_skills.py").exists()
    assert not list(output.glob("**/test_*.py"))


def test_install_script_writes_collection_to_custom_destination(tmp_path):
    destination = tmp_path / "codex-home" / "skills" / "joesys-skills"

    exit_code = install_codex_skills.main([
        "--source",
        str(REPO_ROOT),
        "--dest",
        str(destination),
    ])

    manifest_path = destination / "_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert set(manifest["installed_skills"]) == EXPECTED_SKILLS
    assert (destination / "commit" / "SKILL.md").is_file()
    assert (destination / "shared" / "skill-context.md").is_file()


def test_codex_package_is_not_a_tracked_source_artifact():
    assert not (REPO_ROOT / ".codex-plugin" / "plugin.json").exists()
