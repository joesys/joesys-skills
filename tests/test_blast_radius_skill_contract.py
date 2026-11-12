"""Prompt-as-code contracts for the blast-radius skill."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "blast-radius"
CANONICAL_DIR = REPO_ROOT / "skills" / SKILL_NAME
CODEX_DIR = REPO_ROOT / "codex-skills" / SKILL_NAME
PROOF_LEVELS = ("Said", "Pointed", "Walked", "Ran", "Reproduced")


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
        assert "what a change could break somewhere else" in frontmatter
        assert "by running real code" in frontmatter

    assert "`/blast-radius --commit abc123`" in canonical
    assert "`$blast-radius --commit abc123`" in codex
    assert "/blast-radius --commit" not in codex


def test_proof_has_five_levels_in_order() -> None:
    for skill in skills():
        positions = [skill.index(f"**{level}.**") for level in PROOF_LEVELS]
        assert positions == sorted(positions)
        assert "say where you stopped" in compact(skill)


def test_the_one_fact_is_proven_or_called_unproven() -> None:
    # A blast-radius write-up reads as convincing whether or not it is true.
    # So the reply must carry a run, or the word "unproven".
    for skill in skills():
        normalized = compact(skill)
        assert "Find the one fact" in normalized
        assert "paste the output" in normalized
        assert "write `unproven`" in normalized


def test_skill_looks_where_a_search_stops() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "A list of callers is not the answer" in normalized
        for place in ("pinned version", "a database column", "a feature flag", "generated"):
            assert place in normalized, place


def test_skill_protects_product_code_secrets_and_live_services() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "changes no product code" in normalized
        assert "does not commit, push, or open a pull request" in normalized
        assert "Never read secrets" in normalized
        assert "Ask before a live call" in normalized
        assert "say `fake` in the proof" in normalized
        assert "Never make up a caller" in normalized


def test_proof_script_stays_out_of_the_way() -> None:
    for skill in skills():
        normalized = compact(skill)
        assert "scratch folder outside the project" in normalized
        assert "leave it uncommitted and name it in the reply" in normalized


def test_sibling_skills_are_options_not_steps() -> None:
    # The source skill runs one of its steps "as an arena" and borrows a step
    # of another skill by number. This collection has neither link.
    canonical, codex = skills()
    assert "`/codex`, `/antigravity`, or `/ai-council`" in compact(canonical)
    assert "`$codex`, `$antigravity`, or `$ai-council`" in compact(codex)

    for folder in (CANONICAL_DIR, CODEX_DIR):
        paths = sorted(folder.rglob("*.md"))
        assert paths, folder
        for path in paths:
            if path.name == "NOTICE.md":
                continue
            text = read(path)
            for word in ("arena", "unslop", "Solid", ".cursor", "why` step"):
                assert word not in text, (path, word)


def test_skill_carries_the_license_notice_of_its_source() -> None:
    for folder in (CANONICAL_DIR, CODEX_DIR):
        notice = read(folder / "NOTICE.md")
        assert "Copyright (c) 2026 Lauren Tan" in notice
        assert "Permission is hereby granted, free of charge" in notice
        assert "NOTICE.md" in read(folder / "SKILL.md")


def test_readme_and_interfaces_list_the_skill() -> None:
    readme = compact(read(REPO_ROOT / "README.md"))
    assert "| Review | [`blast-radius`](#blast-radius) |" in readme
    assert "### blast-radius" in readme

    interfaces = read(REPO_ROOT / "shared" / "skill-interfaces.md")
    assert "## Blast Radius Interface" in interfaces
