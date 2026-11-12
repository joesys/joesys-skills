"""Tests for building the Codex plugin copy of the joesys skills."""

import json
import os
import re
import sys
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import codex_adapter
import install_codex_skills


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {
    "ai-council",
    "antigravity",
    "benchmark-checklist",
    "blast-radius",
    "claude",
    "codebase-audit",
    "codereview",
    "codex",
    "commit",
    "create-formal-verification-skill",
    "create-verification-skill",
    "devlog",
    "explain",
    "grok",
    "handoff",
    "huh",
    "human-review-guide",
    "interaction-review",
    "joesys-mode",
    "prompt",
    "quick-review",
    "readability-review",
    "restructure-commit",
    "retrospective",
    "ss",
    "why",
}

SAME_PLATFORM_SUBAGENT_SKILLS = {
    "codebase-audit",
    "codereview",
    "devlog",
    "explain",
    "human-review-guide",
    "interaction-review",
    "quick-review",
    "readability-review",
    "retrospective",
    "why",
}

PINNED_SUBAGENT_MODEL = re.compile(
    r'(?:\bmodel:\s*|\|\s*Model\s*\|\s*)'
    r'`?["\']?(?:opus|fable|sonnet|haiku|gpt-[\w.-]+)',
    re.IGNORECASE,
)

ALLOWED_EXPLICIT_MODEL_DOCS = {
    Path("ai-council/SKILL.md"),
}


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    """Map of relative posix path -> newline-normalized bytes for comparison."""
    snapshot = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[path.relative_to(root).as_posix()] = (
                path.read_bytes().replace(b"\r\n", b"\n")
            )
    return snapshot


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


def test_slash_commands_become_skill_mentions(tmp_path):
    output = tmp_path / "joesys-skills"
    manifest = codex_adapter.build_collection(REPO_ROOT, output)

    commit = (output / "commit" / "SKILL.md").read_text(encoding="utf-8")
    assert "$devlog" in commit
    assert "$restructure-commit" in commit
    assert "/restructure-commit" not in commit
    assert "/joesys-" not in commit

    codereview = (output / "codereview" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = codereview.split("---", 2)[1]
    assert "$codereview" in frontmatter

    prompt = (output / "prompt" / "SKILL.md").read_text(encoding="utf-8")
    assert "$prompt <request>" in prompt
    assert "/prompt <request>" not in prompt

    assert manifest["skill_mentions"] == sorted(
        f"${name}" for name in EXPECTED_SKILLS
    )
    assert "slash_commands" not in manifest


def test_generated_skills_reference_resources_relative_to_skill_dir(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    code_review = (output / "codereview" / "SKILL.md").read_text(encoding="utf-8")
    restructure = (output / "restructure-commit" / "SKILL.md").read_text(encoding="utf-8")

    assert "../shared/review-common.md" in code_review
    assert "`principles/clean-code.md`" in code_review
    assert "../commit/SKILL.md" in restructure
    assert "~/.codex/skills" not in code_review
    assert (output / "shared" / "review-common.md").is_file()
    assert (output / "scripts" / "html_render.py").is_file()
    assert not (output / "scripts" / "md_export.py").exists()


def test_generated_guidance_matches_standalone_layout(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    commit = (output / "commit" / "SKILL.md").read_text(encoding="utf-8")

    assert "## Collection Root" in commit
    assert "The collection root is the folder one level above this SKILL.md." in commit
    for skill_md in output.glob("*/SKILL.md"):
        skill = skill_md.read_text(encoding="utf-8")
        assert "two levels above this SKILL.md" not in skill, skill_md
        assert skill.count("## Collection Root") == 1, skill_md


def test_generated_files_never_name_the_claude_plugin_root(tmp_path):
    # Codex has no ${CLAUDE_PLUGIN_ROOT} variable and no plugin root: generated
    # skills sit side by side in one collection folder.
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    markdown_files = list(output.rglob("*.md"))
    assert markdown_files
    for markdown in markdown_files:
        text = markdown.read_text(encoding="utf-8")
        assert "CLAUDE_PLUGIN_ROOT" not in text, markdown
        assert "plugin root" not in text.lower(), markdown


def test_no_skill_mentions_a_removed_skill(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)
    removed = ["preferences", "handbook", "dashboard", "plan-review", "export"]
    mention = re.compile(
        r"(?<![\w/.~-])[/$](" + "|".join(map(re.escape, removed)) + r")(?![\w-])"
    )

    for collection in (REPO_ROOT / "skills", REPO_ROOT / "shared", output):
        for markdown in collection.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8")
            found = mention.search(text)
            assert not found, (markdown, found and found.group(0))


def test_shared_files_reference_siblings_in_place(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    dispatch = (output / "shared" / "cross-model-dispatch.md").read_text(
        encoding="utf-8"
    )
    assert "./model-defaults.md" in dispatch
    assert "~/.codex/skills" not in dispatch


def test_same_platform_subagents_inherit_parent_model(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    inheritance_rule = (
        "Let every subagent inherit the parent model and reasoning effort"
    )
    for collection in (REPO_ROOT / "skills", output):
        for skill_name in SAME_PLATFORM_SUBAGENT_SKILLS:
            skill_root = collection / skill_name
            skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
            assert inheritance_rule in skill, skill_root

        for markdown in collection.rglob("*.md"):
            relative_path = markdown.relative_to(collection)
            if relative_path in ALLOWED_EXPLICIT_MODEL_DOCS:
                continue
            text = markdown.read_text(encoding="utf-8")
            assert not PINNED_SUBAGENT_MODEL.search(text), markdown

    source_defaults = (REPO_ROOT / "shared" / "model-defaults.md").read_text(
        encoding="utf-8"
    )
    generated_defaults = (output / "shared" / "model-defaults.md").read_text(
        encoding="utf-8"
    )
    for defaults in (source_defaults, generated_defaults):
        assert "## Same-Platform Subagent Defaults" in defaults
        assert "omit the per-call `model` and `effort` fields" in defaults


def test_ai_council_keeps_its_cross_model_fable_exception(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    for skill_path in (
        REPO_ROOT / "skills" / "ai-council" / "SKILL.md",
        output / "ai-council" / "SKILL.md",
    ):
        skill = skill_path.read_text(encoding="utf-8")
        assert "intentional cross-model council leg" in skill
        assert 'model: "fable"' in skill
        assert "Use CLI** when the parent is not Claude Code" in skill


def test_generated_skill_markdown_is_ascii_for_windows_validator(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    for skill_md in output.glob("*/SKILL.md"):
        skill_md.read_text(encoding="ascii")


def test_ascii_normalization_preserves_semantic_markers():
    source = """---
name: sample
description: Use when testing adaptation
---
See § Prompt Delivery. Use ±5 and a · b. ┌─┬─┐ │ ✓ ⚠ ⏸
"""

    adapted = codex_adapter.adapt_skill_markdown(source, ["sample"])

    adapted.encode("ascii")
    assert "Section Prompt Delivery" in adapted
    assert "+/-5" in adapted
    assert "a * b" in adapted
    assert "+-+-+" in adapted
    assert "WARNING" in adapted
    assert "yes" in adapted
    assert "paused" in adapted


def test_generated_package_does_not_bundle_installer_tools(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    assert not (output / "scripts" / "codex_adapter.py").exists()
    assert not (output / "scripts" / "install_codex_skills.py").exists()
    assert not (output / "scripts" / "reinstall-plugin.ps1").exists()
    assert not list(output.glob("**/test_*.py"))


def test_build_is_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    codex_adapter.build_collection(REPO_ROOT, first)
    codex_adapter.build_collection(REPO_ROOT, second)

    assert _tree_snapshot(first) == _tree_snapshot(second)


def test_manifest_has_no_unstable_fields(tmp_path):
    output = tmp_path / "joesys-skills"
    manifest = codex_adapter.build_collection(REPO_ROOT, output)

    assert "installed_at" not in manifest
    assert "source_commit" not in manifest
    assert manifest["name"] == "joesys-skills"
    assert manifest["adapter_version"] == codex_adapter.ADAPTER_VERSION


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


def test_codex_plugin_manifest_is_tracked_and_version_synced():
    codex_plugin = json.loads(
        (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    claude_plugin = json.loads(
        (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
            encoding="utf-8"
        )
    )

    assert codex_plugin["name"] == "joesys-skills"
    assert codex_plugin["version"] == claude_plugin["version"]
    assert codex_plugin["skills"] == "./codex-skills/"
    assert any(
        plugin["name"] == "joesys-skills" for plugin in marketplace["plugins"]
    )


def test_plugin_versions_are_synchronized():
    claude_plugin = json.loads(
        (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    claude_marketplace = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(
            encoding="utf-8"
        )
    )
    codex_plugin = json.loads(
        (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace_version = next(
        plugin["version"]
        for plugin in claude_marketplace["plugins"]
        if plugin["name"] == "joesys-skills"
    )

    assert claude_plugin["version"] == "20.0.0"
    assert codex_plugin["version"] == claude_plugin["version"]
    assert marketplace_version == claude_plugin["version"]


def test_generated_handoff_uses_codex_invocation_and_keeps_helper(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    skill = (output / "handoff" / "SKILL.md").read_text(encoding="utf-8")
    assert "$handoff resume" in skill
    assert "/handoff resume" not in skill
    assert (output / "handoff" / "helpers" / "handoff_state.py").is_file()
    assert not (output / "handoff" / "helpers" / "test_handoff_state.py").exists()
    assert "~/.claude/projects" not in skill


def test_generated_docs_have_no_cross_host_path_contradictions(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(output.rglob("*.md"))
    )

    assert "Claude reads `.codex/" not in combined
    assert "Claude: `.codex/" not in combined
    assert "`.claude/` directory doesn't exist" not in combined


def test_generated_manifest_publishes_release_20_0_with_26_skills(tmp_path):
    output = tmp_path / "joesys-skills"
    manifest = codex_adapter.build_collection(REPO_ROOT, output)

    assert manifest["source_version"] == "20.0.0"
    assert len(manifest["installed_skills"]) == 26
    assert "prompt" in manifest["installed_skills"]


def test_generated_grok_command_keeps_its_permission_rules(tmp_path):
    # `Bash(...)` in a CLI permission rule is the CLI's own syntax, not the
    # name of the Claude Code tool. A rewritten rule is one Grok does not
    # honor, so `touch` and `mkdir` would run again in the Codex copy.
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    def grok_command(path: Path) -> str:
        lines = path.read_text(encoding="utf-8").splitlines()
        commands = [line for line in lines if line.startswith("grok ")]
        assert len(commands) == 1, path
        return commands[0]

    source = grok_command(REPO_ROOT / "shared" / "model-defaults.md")
    generated = grok_command(output / "shared" / "model-defaults.md")
    assert generated == source
    assert '--deny "Bash(touch *)" --deny "Bash(mkdir *)"' in generated

    adapted = codex_adapter.adapt_skill_markdown(
        '---\nname: x\ndescription: "d"\n---\n\n'
        "Run it with Bash. Deny rule: `Bash(rm *)`.\n",
        ["x"],
    )
    assert "Run it with shell." in adapted
    assert "`Bash(rm *)`" in adapted


def test_project_skill_folder_becomes_the_codex_one():
    # Claude Code reads project skills from `.claude/skills/`. Codex reads
    # them from `.agents/skills/` in the repository. A skill that writes a
    # project skill must name the folder its own host reads.
    adapted = codex_adapter.adapt_skill_markdown(
        '---\nname: x\ndescription: "d"\n---\n\n'
        "Write it to `.claude/skills/verify-<app>/SKILL.md`. "
        "Read `.claude/skill-context/x.md`.\n",
        ["x"],
    )
    assert "`.agents/skills/verify-<app>/SKILL.md`" in adapted
    assert ".claude/skills/" not in adapted
    assert "`.codex/skill-context/x.md`" in adapted


def test_committed_codex_skills_match_fresh_build(tmp_path):
    """codex-skills/ is generated output — regenerate it when source skills change."""
    fresh = tmp_path / "fresh"
    codex_adapter.build_collection(REPO_ROOT, fresh)

    committed = REPO_ROOT / "codex-skills"
    assert committed.is_dir(), (
        "codex-skills/ is missing — run: python scripts/codex_adapter.py codex-skills"
    )
    assert _tree_snapshot(committed) == _tree_snapshot(fresh), (
        "codex-skills/ is stale — run: python scripts/codex_adapter.py codex-skills --force"
    )
