"""Prompt-as-code contracts for the benchmark-checklist skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "benchmark-checklist"
CANONICAL_DIR = REPO_ROOT / "skills" / SKILL_NAME
CODEX_DIR = REPO_ROOT / "codex-skills" / SKILL_NAME
QUESTIONS = (
    "Why not double?",
    "Was it tuned?",
    "Did it break limits?",
    "Did it error?",
    "Does it reproduce?",
    "Does it matter?",
    "Did it even happen?",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.split())


def skills() -> tuple[str, str]:
    paths = (CANONICAL_DIR / "SKILL.md", CODEX_DIR / "SKILL.md")
    missing = [str(path.relative_to(REPO_ROOT)) for path in paths if not path.is_file()]
    assert not missing, f"Missing skill files: {', '.join(missing)}"
    return read(paths[0]), read(paths[1])


def test_skill_is_discoverable_on_both_hosts() -> None:
    canonical, codex = skills()

    for skill in (canonical, codex):
        frontmatter = skill.split("---", 2)[1]
        assert f"name: {SKILL_NAME}" in frontmatter
        assert "a performance number" in frontmatter
        assert "about to be reported or used for a decision" in frontmatter

    assert "/benchmark-checklist <claim, script, or two options>" in canonical
    assert "$benchmark-checklist <claim, script, or two options>" in codex
    assert "/benchmark-checklist <claim" not in codex


def test_seven_questions_come_in_order() -> None:
    for skill in skills():
        positions = [skill.index(f"**{question}**") for question in QUESTIONS]
        assert positions == sorted(positions)
        assert "evidence from a run, not with a guess about the code" in compact(skill)


def test_verdict_is_one_of_four_words() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "faster, slower, no measurable difference, or inconclusive" in normalized
        assert "cannot name what limits the number" in normalized
        assert "one side ran untuned" in normalized


def test_a_number_carries_its_run_count_and_range() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "at least 5 times" in normalized
        assert "the median and the range" in normalized
        assert "Never report a number without its run count" in normalized


def test_a_quick_estimate_still_checks_errors_and_that_the_work_ran() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "Still answer questions 4 and 7" in normalized
        assert "A choice between two options is never a rough number" in normalized


def test_skill_protects_product_code_tools_and_shared_services() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "changes no product code" in normalized
        assert "Ask before you install a tool" in normalized
        assert "Ask before you put load on a service" in normalized
        assert "Never read secrets" in normalized


def test_skill_points_at_nothing_this_collection_lacks() -> None:
    # The source skill sends the reader to three playbooks of its own mode
    # skill. This collection has none of them. The source example also
    # writes a change as "41 ms -> 33 ms" with an arrow, which the report
    # style of this collection does not use.
    for folder in (CANONICAL_DIR, CODEX_DIR):
        paths = sorted(folder.rglob("*.md"))
        assert paths, folder
        for path in paths:
            if path.name == "NOTICE.md":
                continue
            text = read(path)
            for word in ("playbook", "Hillclimb", "Opening a PR", ".cursor", "→", "->"):
                assert word not in text, (path, word)


def test_skill_carries_the_license_notice_of_its_source() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        notice = read(folder / "NOTICE.md")
        assert "Copyright (c) 2026 Lauren Tan" in notice
        assert "Permission is hereby granted, free of charge" in notice
        assert "NOTICE.md" in read(folder / "SKILL.md")


def test_readme_and_interfaces_list_the_skill() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert "| Verify | [`benchmark-checklist`](#benchmark-checklist) |" in readme
    assert "### benchmark-checklist" in readme

    interfaces = read(REPO_ROOT / "shared" / "skill-interfaces.md")
    assert "## Benchmark Checklist Interface" in interfaces
