from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "plan-review"


def read(relative: str) -> str:
    return (SKILL_ROOT / relative).read_text(encoding="utf-8")


def test_review_contract_defines_structured_reviewer_output() -> None:
    contract = read("references/review-contract.md")

    for field in [
        '"schema_version": 1',
        '"concern_key"',
        '"severity"',
        '"document"',
        '"location"',
        '"repository_evidence"',
        '"consequence"',
        '"recommended_resolution"',
        '"requires_user_decision"',
    ]:
        assert field in contract
    for severity in ["P0", "P1", "P2", "P3", "P4"]:
        assert f"`{severity}`" in contract


def test_review_contract_defines_all_arbiter_verdicts() -> None:
    contract = read("references/review-contract.md")

    assert '"finding_id"' in contract
    assert '"rationale"' in contract
    assert '"required_change"' in contract
    for verdict in ["accepted", "rejected", "needs-user-decision"]:
        assert f"`{verdict}`" in contract


def test_review_contract_covers_joint_document_analysis() -> None:
    contract = read("references/review-contract.md").lower()

    for concern in [
        "internal coherence",
        "requirement completeness",
        "spec-to-plan traceability",
        "technical feasibility",
        "scope discipline",
        "security",
        "rollback",
        "acceptance criteria",
    ]:
        assert concern in contract


def test_preference_schema_defines_defaults_and_precedence() -> None:
    preferences = read("references/preference-schema.md")

    for setting in [
        "Review model",
        "Arbiter",
        "Preferred arbiters",
        "Arbiter ambiguity",
        "Maximum iterations",
        "Fix accepted findings",
        "Fresh context each iteration",
    ]:
        assert setting in preferences
    assert "gpt-5.6-sol" in preferences
    assert "1 through 20" in preferences
    assert "Invocation arguments" in preferences
    assert "Project-specific" in preferences
    assert "Shared preferences" in preferences
    assert "Provider defaults" in preferences


def test_preference_schema_routes_models_without_reviewer_setting() -> None:
    preferences = read("references/preference-schema.md")

    assert "gpt-5.6-sol" in preferences
    assert "Codex CLI" in preferences
    assert "fable" in preferences
    assert "Claude CLI" in preferences
    assert "--reviewer" not in preferences
    assert "codex:custom-model" in preferences
    assert "claude:custom-model" in preferences


def test_preference_schema_defines_ranked_arbiter_ambiguity() -> None:
    preferences = read("references/preference-schema.md").lower()

    assert "rank" in preferences
    assert "recommended" in preferences
    assert "ask" in preferences
    assert "host/base" in preferences
