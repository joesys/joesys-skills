"""Prompt-as-code contracts for the handoff skill."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "handoff"


def read(relative: str) -> str:
    return (SKILL_ROOT / relative).read_text(encoding="utf-8")


def test_handoff_references_exist() -> None:
    assert (SKILL_ROOT / "references" / "artifact-schema.md").is_file()
    assert (
        SKILL_ROOT / "references" / "audience-target-profiles.md"
    ).is_file()
    assert (SKILL_ROOT / "helpers" / "handoff_state.py").is_file()


def test_schema_defines_required_sections() -> None:
    schema = read("references/artifact-schema.md")
    for heading in [
        "Resume Directive",
        "Objective and Success Criteria",
        "Current State",
        "Decisions and Rationale",
        "Constraints and Guardrails",
        "Working Set",
        "Repository State",
        "Verification Evidence",
        "Blockers and Uncertainties",
        "Next Actions",
        "Audience Notes",
        "Target Bootstrap",
    ]:
        assert heading in schema
    assert "schema_version: 1" in schema
    assert "repository_snapshot:" in schema


def test_schema_defines_all_detail_modes() -> None:
    schema = read("references/artifact-schema.md")
    assert "operational" in schema
    assert "--full" in schema
    assert "--compact" in schema
    assert "--include-diff" in schema


def test_profiles_separate_audience_from_target() -> None:
    profiles = read("references/audience-target-profiles.md")
    for audience in ["self", "agent", "human"]:
        assert f"`{audience}`" in profiles
    for target in ["auto", "claude", "codex", "gemini", "generic"]:
        assert f"`{target}`" in profiles
    assert "authority" in profiles.lower()
    assert "report-back" in profiles.lower()
    assert "review" in profiles.lower()


def skill_text() -> str:
    return read("SKILL.md")


def test_skill_frontmatter_and_invocations() -> None:
    skill = skill_text()
    assert skill.startswith("---\nname: handoff\n")
    assert "description:" in skill.split("---", 2)[1]
    for invocation in [
        "/handoff",
        "--full",
        "--compact",
        "--interactive",
        "--for self|agent|human",
        "--target auto|claude|codex|gemini|generic",
        "--include-diff",
        "--output <path>",
        "/handoff resume",
    ]:
        assert invocation in skill


def test_skill_requires_deterministic_snapshot_and_compare() -> None:
    skill = skill_text()
    assert "handoff_state.py snapshot" in skill
    assert "handoff_state.py compare" in skill
    for state in ["exact", "advanced", "drifted", "unverifiable"]:
        assert f"`{state}`" in skill
    assert "continue automatically" in skill.lower()
    assert "must not continue" in skill.lower()
    assert "newest valid handoff" in skill.lower()
    assert "project identity" in skill.lower()


def test_skill_has_privacy_and_evidence_guards() -> None:
    skill = skill_text().lower()
    for phrase in [
        "raw conversation transcripts",
        "environment variables",
        "credentials",
        "shell history",
        "never invent",
        "executed evidence",
        "secret-bearing",
    ]:
        assert phrase in skill


def test_skill_preserves_files_and_avoids_sibling_dispatch() -> None:
    skill = skill_text().lower()
    assert "temporary file" in skill
    assert "rename" in skill
    assert "never overwrite" in skill
    assert "must not invoke" in skill
    for sibling in ["/commit", "/devlog", "/retrospective"]:
        assert sibling in skill


def test_skill_does_not_mine_host_transcript_paths() -> None:
    skill = skill_text()
    assert "~/.claude/projects" not in skill
    assert "~/.codex/sessions" not in skill
    assert "~/.gemini/tmp" not in skill
