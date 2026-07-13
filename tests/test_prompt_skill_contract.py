"""Prompt-as-code contracts for the prompt helper skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL = REPO_ROOT / "skills" / "prompt" / "SKILL.md"
CODEX_SKILL = REPO_ROOT / "codex-skills" / "prompt" / "SKILL.md"
README = REPO_ROOT / "README.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.replace("\n>", "\n").split())


def prompt_skills() -> tuple[str, str]:
    missing = [
        str(path.relative_to(REPO_ROOT))
        for path in (CANONICAL_SKILL, CODEX_SKILL)
        if not path.is_file()
    ]
    assert not missing, f"Missing prompt skill files: {', '.join(missing)}"
    return read(CANONICAL_SKILL), read(CODEX_SKILL)


def test_prompt_skill_is_discoverable_on_both_hosts() -> None:
    canonical, codex = prompt_skills()

    for skill in (canonical, codex):
        frontmatter = skill.split("---", 2)[1]
        assert "name: prompt" in frontmatter
        assert "stream-of-consciousness" in frontmatter
        assert "prompt for another AI" in frontmatter

    assert "/prompt <request>" in canonical
    assert "$prompt <request>" in codex
    assert "/prompt <request>" not in codex


def test_prompt_skill_preserves_intent_and_never_executes() -> None:
    for skill in prompt_skills():
        normalized = compact(skill)
        assert "Do not execute the generated prompt" in normalized
        assert "Preserve the operator's intent" in normalized
        assert "must not invent facts, deadlines, technologies" in normalized
        assert "must not silently replace the requested task" in normalized


def test_prompt_skill_asks_only_for_material_clarification() -> None:
    for skill in prompt_skills():
        normalized = compact(skill)
        assert (
            "Material ambiguity changes the task, scope, permission, "
            "deliverable, or success criteria"
        ) in normalized
        assert "ask one focused clarification at a time" in normalized
        assert "make a conservative assumption and disclose it" in normalized
        assert "ask the operator to resolve the conflict" in normalized


def test_prompt_skill_builds_the_smallest_useful_prompt() -> None:
    for skill in prompt_skills():
        normalized = compact(skill)
        assert "Create the smallest prompt that expresses the request clearly" in normalized
        assert "Put the task and desired outcome in clear, direct language" in normalized
        assert "Prefer positive instructions" in normalized
        assert "Add examples only when" in normalized
        assert "Use a functional role only when" in normalized
        assert "portable prompt" in normalized
        assert "Tailor it to a named AI" in normalized


def test_prompt_skill_is_coding_aware_without_inventing_authority() -> None:
    for skill in prompt_skills():
        normalized = compact(skill)
        assert "## Coding Requests" in skill
        assert "diagnosis, implementation, review, or explanation" in normalized
        assert "whether changes are authorized" in normalized
        assert "how the result should be tested or otherwise verified" in normalized
        assert "destructive actions, pushes, external messages, or deployments" in normalized


def test_prompt_skill_teaches_why_the_rewrite_is_stronger() -> None:
    for skill in prompt_skills():
        assert "## Prompt" in skill
        assert "## Why this prompt is stronger" in skill
        for label in [
            "**Added:**",
            "**Removed or simplified:**",
            "**Reorganized:**",
            "**Assumptions:**",
            "**Already strong:**",
        ]:
            assert label in skill
        assert "Do not narrate every edit" in skill


def test_prompt_skill_handles_edge_cases_and_checks_its_work() -> None:
    for skill in prompt_skills():
        normalized = compact(skill)
        assert "Empty invocation" in normalized
        assert "Already-strong prompt" in normalized
        assert "Embedded code fences" in normalized
        assert "Unsafe or disallowed request" in normalized
        assert "safety rules" in normalized
        assert "use a longer outer fence" in normalized
        assert "## Final Check" in skill
        assert "contradictory instructions" in normalized
        assert "unnecessary detail" in normalized


def test_readme_documents_prompt_rewriting_and_teaching() -> None:
    readme = compact(read(README))

    assert "A collection of 22 agent skills" in readme
    assert "| Write prompts | [`prompt`](#prompt) |" in readme
    assert "### prompt" in readme
    assert "/prompt" in readme
    assert "what was added, removed, reorganized, or assumed" in readme
