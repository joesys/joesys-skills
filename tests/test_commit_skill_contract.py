"""Prompt-as-code contracts for the commit skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL = REPO_ROOT / "skills" / "commit" / "SKILL.md"
CODEX_SKILL = REPO_ROOT / "codex-skills" / "commit" / "SKILL.md"
README = REPO_ROOT / "README.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.replace("\n>", "\n").split())


def commit_skills() -> list[str]:
    return [read(CANONICAL_SKILL), read(CODEX_SKILL)]


def test_commit_skill_defines_the_durable_reader() -> None:
    for skill in commit_skills():
        normalized = compact(skill)
        assert "## Plain-Language Standard" in skill
        assert "author returning years later" in normalized
        assert "issue tracker or session history" in normalized
        assert "explain it on first use" in normalized
        assert "Metaphors, slogans, ceremonial language" in normalized


def test_commit_skill_applies_plain_language_to_every_section() -> None:
    for skill in commit_skills():
        normalized = compact(skill)
        assert "name the concrete outcome" in normalized
        assert "problem or need, the outcome, and why it matters" in normalized
        assert "observable outcomes and important technical decisions" in normalized
        assert "direct, ordinary language" in normalized
        assert "include line numbers when relevant" not in skill
        assert (
            "understand every substantive change without reading the diff"
            not in skill
        )


def test_commit_skill_includes_a_real_before_and_after_example() -> None:
    for skill in commit_skills():
        normalized = compact(skill)
        assert (
            "feat(research): record the July 13 development data snapshot"
            in skill
        )
        assert "snapshot-generation script" in normalized
        assert "initially overwrote the July 12 snapshot" in normalized


def test_commit_skill_requires_a_final_readability_check() -> None:
    expected = (
        "Could a teammate unfamiliar with this task, or the author returning "
        "years later, understand why this commit exists, what changed, and "
        "what still needs attention without the issue tracker or session "
        "history?"
    )

    for skill in commit_skills():
        normalized = compact(skill)
        assert expected in normalized
        assert "rewrite the message before creating the commit" in normalized


def test_readme_promises_plain_language_commit_messages() -> None:
    readme = compact(read(README)).lower()
    assert "plain language" in readme
    assert "without current-task context" in readme


RESTRUCTURE_SKILL = REPO_ROOT / "skills" / "restructure-commit" / "SKILL.md"
CODEX_RESTRUCTURE_SKILL = REPO_ROOT / "codex-skills" / "restructure-commit" / "SKILL.md"


def test_commit_never_rewrites_existing_history() -> None:
    for skill in commit_skills():
        assert "git reset --hard" not in skill
        assert "git cherry-pick" not in skill
        assert "A force push will be used when needed" not in skill


def test_commit_keeps_oneflow_bubbles_without_single_commit_bubbles() -> None:
    for skill in commit_skills():
        normalized = compact(skill)
        assert "OneFlow Option 3" in skill
        assert "git merge --no-ff" in skill
        assert "fast-forward" in normalized


def test_commit_points_to_restructure_without_waiting() -> None:
    canonical, codex = commit_skills()
    assert "/restructure-commit" in canonical
    assert "$restructure-commit" in codex
    assert "do not wait" in compact(canonical).lower()


def test_restructure_owns_the_history_rewrite_safely() -> None:
    for skill, commit_ref in (
        (read(RESTRUCTURE_SKILL), "skills/commit/SKILL.md"),
        (read(CODEX_RESTRUCTURE_SKILL), "../commit/SKILL.md"),
    ):
        normalized = compact(skill)
        assert commit_ref in skill
        assert "git cherry-pick" in skill
        assert "git reset --hard" in skill
        # A backup branch is created before history is rewritten.
        assert normalized.index("git branch restructure-backup") < normalized.index(
            "git reset --hard"
        )
        assert "MUST wait" in skill
        assert "git push" in skill and "express" in normalized


def test_resign_recipe_keeps_merge_bubbles() -> None:
    for skill in commit_skills():
        assert "git rebase --rebase-merges --exec" in skill
