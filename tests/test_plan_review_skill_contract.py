from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "plan-review"


def read(relative: str) -> str:
    return (SKILL_ROOT / relative).read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.replace("\n>", "\n").split())


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


def test_skill_frontmatter_and_invocation_are_specific() -> None:
    skill = read("SKILL.md")
    frontmatter = skill.split("---", 2)[1]

    assert "name: plan-review" in frontmatter
    assert "specification" in frontmatter
    assert "implementation plan" in frontmatter
    assert "/plan-review <document> [other-document] [options]" in skill
    assert "--model <MODEL>" in skill
    assert "--arbiter <NAME|auto|host>" in skill
    assert "--review-only" in skill
    assert "--max-iterations <N>" in skill
    assert "--reviewer" not in skill


def test_skill_accepts_one_document_with_explicit_warning() -> None:
    skill = compact(read("SKILL.md"))

    assert "Reviewing one document only" in skill
    assert "provide both the specification and implementation plan" in skill
    assert "cross-document contradictions" in skill


def test_skill_gives_fresh_reviewer_full_read_only_repository_access() -> None:
    skill = read("SKILL.md").lower()

    assert "repository root" in skill
    assert "inspect any file" in skill
    assert "read-only" in skill
    assert "never resume" in skill
    assert "prior findings" in skill
    assert "ledger" in skill
    assert "must not" in skill


def test_skill_discovers_and_ranks_repository_arbiters() -> None:
    skill = compact(read("SKILL.md"))

    for path in [
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        ".agents/",
        ".claude/agents/",
        ".codex/agents/",
    ]:
        assert path in skill
    assert "Recommended" in skill
    assert "host/base" in skill
    assert "wait for the user's selection" in skill


def test_skill_separates_arbitration_from_fixing() -> None:
    skill = compact(read("SKILL.md"))

    assert "The arbiter MUST NOT edit files" in skill
    assert "The host applies" in skill
    assert "accepted" in skill
    assert "rejected" in skill
    assert "needs-user-decision" in skill
    assert "only the supplied documents" in skill


def test_skill_defines_convergence_and_pause_guards() -> None:
    skill = compact(read("SKILL.md"))

    assert "no P0 or P1" in skill
    assert "accepted findings remain" in skill
    assert "user decision" in skill
    assert "validation" in skill
    assert "three consecutive iterations" in skill
    assert "oscillat" in skill.lower()
    assert "20" in skill


def test_review_only_is_single_pass_and_non_mutating() -> None:
    skill = compact(read("SKILL.md"))
    review_only = skill.split("## Review-Only Mode", 1)[1]

    assert "one fresh external review" in review_only
    assert "one arbiter pass" in review_only
    assert "MUST NOT edit" in review_only
    assert "MUST NOT claim convergence" in review_only


def test_skill_uses_deterministic_helper_lifecycle() -> None:
    skill = read("SKILL.md")

    assert "helpers/plan_review_state.py" in skill
    assert "absolute path" in skill
    assert "skill directory" in skill
    for command in ["start", "record", "diff", "finish"]:
        assert f"python <STATE_HELPER> {command}" in skill
    assert "operating-system temporary directory" in skill


def test_skill_resolves_shared_resources_from_plugin_root() -> None:
    skill = read("SKILL.md")

    assert "`shared/model-defaults.md`" in skill
    assert "`shared/delegation-common.md`" in skill
    assert "`shared/skill-context.md`" in skill
    assert "`../shared/" not in skill


def test_skill_does_not_commit_push_or_expose_sensitive_values() -> None:
    skill = compact(read("SKILL.md")).lower()

    assert "must not commit" in skill
    assert "must not push" in skill
    assert "must not stash" in skill
    assert "credentials" in skill
    assert "private keys" in skill


def test_shared_model_defaults_register_plan_review_routing() -> None:
    defaults = (REPO_ROOT / "shared" / "model-defaults.md").read_text(
        encoding="utf-8"
    )

    assert "plan-review" in defaults
    assert "## Review Model Routing" in defaults
    assert "| `gpt-5.6-sol` | Codex CLI |" in defaults
    assert "| `fable` | Claude CLI |" in defaults
    assert "provider-qualified" in defaults
    assert "never fail over silently" in defaults.lower()


def test_shared_skill_context_registers_plan_review_preferences() -> None:
    context = (REPO_ROOT / "shared" / "skill-context.md").read_text(
        encoding="utf-8"
    )

    assert "plan-review.md" in context
    assert "`/plan-review`" in context
    assert "Full interview" in context


def test_preferences_question_bank_covers_plan_review_defaults() -> None:
    bank = (
        REPO_ROOT / "skills" / "preferences" / "question-bank.md"
    ).read_text(encoding="utf-8")
    section = bank.split("## plan-review", 1)[1].split("\n## ", 1)[0]

    assert "review model" in section.lower()
    assert "arbiter" in section.lower()
    assert "maximum iterations" in section.lower()
    assert "save" in section.lower()


def test_shared_interface_publishes_plan_review_contract() -> None:
    interfaces = (REPO_ROOT / "shared" / "skill-interfaces.md").read_text(
        encoding="utf-8"
    )
    section = interfaces.split("## Plan Review Skill Interface", 1)[1]

    assert "/plan-review <document>" in section
    assert "--model" in section
    assert "--arbiter" in section
    assert "--review-only" in section
    assert "accepted" in section
    assert "needs-user-decision" in section
    assert "20" in section
