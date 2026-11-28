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
        assert "git commit-tree" not in skill
        assert "A force push will be used when needed" not in skill


def test_commit_enforces_one_unit_per_commit_book_bubbles_and_rebase_to_tip() -> None:
    for skill in commit_skills():
        normalized = compact(skill)
        assert "one single unit of work" in normalized
        assert "History reads like a book" in normalized
        assert "Multi-level nested bubbles (3+ levels) are desirable" in normalized
        assert "git rebase --rebase-merges <parent-branch>" in skill
        assert "plain `git rebase` flattens inner bubbles" in normalized


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


def test_restructure_forbids_squashing_and_raw_dev_wrapping() -> None:
    for skill in (read(RESTRUCTURE_SKILL), read(CODEX_RESTRUCTURE_SKILL)):
        normalized = compact(skill)
        assert "Mistake 1" in normalized
        assert "Mistake 2" in normalized
        assert "git read-tree" in skill and "git merge --squash" in skill
        assert "1-to-1 verbatim" in normalized
        # Mode A still forbids regrouping merge commits; Mode B audits triviality.
        assert "In Mode A (Tip Regrouping)" in normalized
        assert "merge^{tree} == p2^{tree}" in skill


def test_restructure_book_toc_mode_uses_lossless_helper_and_guards() -> None:
    for skill in (read(RESTRUCTURE_SKILL), read(CODEX_RESTRUCTURE_SKILL)):
        normalized = compact(skill)
        assert "--branch" in skill and "--toc" in skill
        assert "helpers/dag_rewrap.py" in skill
        assert "references/book-toc-examples.md" in skill
        assert "inspect" in skill and "validate" in skill and "build" in skill
        assert "git commit-tree" in skill
        assert "restructure-toc-tmp-" in skill
        assert "Default-branch guard" in normalized
        assert "Clean working tree" in normalized
        assert "Plan-presentation guardrail" in normalized
        assert "Level 1 (Chapters) + Level 2 (Sub-Chapters with exact atomic commit counts)" in normalized
        assert "Level 3 sample" in normalized
        assert "--sign all" in skill and "--sign outer" in skill
        assert "git rebase --rebase-merges" in skill


def test_restructure_examples_helper_and_docs_stay_aligned() -> None:
    for examples_path in (
        REPO_ROOT / "skills" / "restructure-commit" / "references" / "book-toc-examples.md",
        REPO_ROOT / "codex-skills" / "restructure-commit" / "references" / "book-toc-examples.md",
    ):
        examples = read(examples_path)
        assert "Mistake 1 (FORBIDDEN)" in examples
        assert "Mistake 2 (FORBIDDEN)" in examples
        assert "Target Layout (REQUIRED)" in examples
        assert "{{SUB_COMMITS}}" in examples

    assert (REPO_ROOT / "skills" / "restructure-commit" / "helpers" / "dag_rewrap.py").is_file()
    assert (REPO_ROOT / "codex-skills" / "restructure-commit" / "helpers" / "dag_rewrap.py").is_file()
    assert not (
        REPO_ROOT / "codex-skills" / "restructure-commit" / "helpers" / "test_dag_rewrap.py"
    ).exists()

    readme = compact(read(README))
    assert "--branch main" in readme and "--toc" in readme
    assert "git rebase --rebase-merges" in readme
    assert "one single unit of work" in readme

    interfaces = compact(read(REPO_ROOT / "shared" / "skill-interfaces.md"))
    assert "dag_rewrap.py" in interfaces
    assert "book-toc-examples.md" in interfaces
    assert "--branch [<base>] | --toc [<base>]" in interfaces


def test_resign_recipe_keeps_merge_bubbles() -> None:
    for skill in commit_skills():
        assert "git rebase --rebase-merges --exec" in skill
