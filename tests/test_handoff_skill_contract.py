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
