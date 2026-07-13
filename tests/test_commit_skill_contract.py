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
