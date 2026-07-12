# Skill Collection Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Repository instructions require inline execution; do not dispatch subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair six confirmed canonical-skill, Antigravity-wrapper, and Codex-adapter defects without changing skill scope or invocation names.

**Architecture:** Keep `skills/` and `shared/` canonical, implement behavior-preserving transformations in `scripts/codex_adapter.py`, and regenerate `codex-skills/` mechanically. Preserve the Antigravity wrapper as a current-stdout-first, legacy-SQLite-fallback compatibility layer.

**Tech Stack:** Markdown skill contracts, Python 3.13, pytest, deterministic filesystem generation.

---

### Task 1: Lock down plan-review resource resolution

**Files:**
- Modify: `tests/test_plan_review_skill_contract.py`
- Modify: `skills/plan-review/SKILL.md`

- [ ] **Step 1: Write failing contract tests**

Add assertions that the canonical skill names `shared/model-defaults.md`,
`shared/delegation-common.md`, and `shared/skill-context.md` without a leading
`../`, defines an absolute `<STATE_HELPER>` resolved from the skill directory,
and uses it for `start`, `record`, `diff`, and `finish`.

```python
def test_skill_resolves_shared_resources_from_plugin_root() -> None:
    skill = read("SKILL.md")
    assert "`shared/model-defaults.md`" in skill
    assert "`shared/delegation-common.md`" in skill
    assert "`shared/skill-context.md`" in skill
    assert "`../shared/" not in skill


def test_skill_resolves_state_helper_before_invocation() -> None:
    skill = read("SKILL.md")
    assert "absolute path" in skill
    assert "skill directory" in skill
    for command in ["start", "record", "diff", "finish"]:
        assert f"python <STATE_HELPER> {command}" in skill
```

- [ ] **Step 2: Verify the tests fail**

Run:

```powershell
python -m pytest tests/test_plan_review_skill_contract.py -q
```

Expected: the two new tests fail against the current relative paths.

- [ ] **Step 3: Correct the canonical skill**

Replace `../shared/...` with canonical `shared/...` references and add a
preflight instruction that resolves `helpers/plan_review_state.py` to an
absolute `<STATE_HELPER>` path under the plan-review skill directory. Replace
all four literal helper commands with `python <STATE_HELPER> ...`.

- [ ] **Step 4: Verify plan-review contracts pass**

Run the same pytest command. Expected: all plan-review contract tests pass.

### Task 2: Make the Antigravity wrapper compatible with current agy

**Files:**
- Modify: `tests/test_agy_adapter.py`
- Modify: `scripts/agy_adapter.py`
- Modify: `shared/model-defaults.md`

- [ ] **Step 1: Write the failing argument-vector test**

Capture the command passed to `run_agy` and assert it ends in `-p` with no empty
positional prompt:

```python
def test_main_enables_print_mode_without_empty_positional_prompt(
    tmp_path, monkeypatch
):
    conv = tmp_path / "conversations"
    conv.mkdir()
    monkeypatch.setenv("AGY_CONV_DIR", str(conv))
    captured = {}

    def fake_run_agy(cmd, prompt, timeout):
        captured["cmd"] = cmd
        return b"direct reply\n", b"", False

    monkeypatch.setattr(agy_adapter, "run_agy", fake_run_agy)
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello"))

    assert agy_adapter.main(["--sandbox"]) == 0
    assert captured["cmd"][-1] == "-p"
    assert "" not in captured["cmd"]
```

- [ ] **Step 2: Verify the new test fails**

Run:

```powershell
python -m pytest tests/test_agy_adapter.py::test_main_enables_print_mode_without_empty_positional_prompt -q
```

Expected: failure because the current command ends with `-p`, `""`.

- [ ] **Step 3: Implement the compatibility correction**

Change the command to `cmd = [agy_bin, *argv, "-p"]`. Update module and shared
documentation so current stdout is the primary path and SQLite extraction is a
legacy fallback for affected older releases. Retain the schema-version warning
only on the fallback extraction failure.

- [ ] **Step 4: Verify Antigravity tests pass**

Run:

```powershell
python -m pytest tests/test_agy_adapter.py -q
```

Expected: all adapter tests pass.

### Task 3: Preserve semantic content during ASCII adaptation

**Files:**
- Modify: `tests/test_codex_adapter.py`
- Modify: `scripts/codex_adapter.py`

- [ ] **Step 1: Write a failing normalization test**

Exercise `adapt_skill_markdown` with every meaningful character class:

```python
def test_ascii_normalization_preserves_semantic_markers():
    source = """---
name: sample
description: Use when testing adaptation
---
See § Prompt Delivery. Use ±5 and a · b. ┌─┬─┐ │ ✓ ⚠ ⏸
"""
    adapted = codex_adapter.adapt_skill_markdown(source, ["sample"])
    adapted.encode("ascii")
    assert "Section Prompt Delivery" in adapted
    assert "+/-5" in adapted
    assert "a * b" in adapted
    assert "WARNING" in adapted
    assert "yes" in adapted
    assert "paused" in adapted
    assert "+-+-+" in adapted
```

- [ ] **Step 2: Verify it fails**

Run that single test. Expected: semantic tokens are absent.

- [ ] **Step 3: Add explicit ASCII mappings**

Extend `_ascii_normalize` with mappings for `§`, `±`, `·`, box-drawing
characters, warning/check/pause symbols, and the variation selector. Use words
or operators that preserve meaning.

- [ ] **Step 4: Verify normalization and ASCII tests pass**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py -k "ascii or semantic" -q
```

Expected: all selected tests pass.

### Task 4: Correct generated layout guidance and skill lookup

**Files:**
- Modify: `tests/test_codex_adapter.py`
- Modify: `scripts/codex_adapter.py`

- [ ] **Step 1: Write failing standalone-layout tests**

Build into `tmp_path` and assert generated skills describe the collection root
as one level above the skill directory, contain no stale two-level guidance,
and validate preferences through `../<skill-name>/SKILL.md`:

```python
def test_generated_guidance_matches_standalone_layout(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)
    export = (output / "export" / "SKILL.md").read_text(encoding="utf-8")
    preferences = (output / "preferences" / "SKILL.md").read_text(encoding="utf-8")
    assert "collection root (one level above this SKILL.md)" in export
    assert "two levels above this SKILL.md" not in export
    assert "../<skill-name>/SKILL.md" in preferences
    assert "skills/<skill-name>/SKILL.md" not in preferences
```

- [ ] **Step 2: Verify the tests fail**

Run the new test. Expected: stale depth and canonical lookup assertions fail.

- [ ] **Step 3: Implement contextual layout rewrites**

After resource-path adaptation, rewrite canonical depth explanations to the
generated collection-root wording. Add an explicit dynamic-path rewrite from
`skills/<skill-name>/SKILL.md` to `../<skill-name>/SKILL.md`.

- [ ] **Step 4: Verify standalone-layout tests pass**

Run the new test and existing resource-path tests. Expected: pass.

### Task 5: Remove platform-label contradictions

**Files:**
- Modify: `tests/test_codex_adapter.py`
- Modify: `skills/preferences/SKILL.md`
- Modify: `skills/plan-review/references/preference-schema.md`
- Modify: `shared/skill-interfaces.md`

- [ ] **Step 1: Write a failing contradiction test**

```python
def test_generated_docs_have_no_cross_host_path_contradictions(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)
    texts = {
        path.relative_to(output).as_posix(): path.read_text(encoding="utf-8")
        for path in output.rglob("*.md")
    }
    combined = "\n".join(texts.values())
    assert "Claude reads `.codex/" not in combined
    assert "Claude: `.codex/" not in combined
    assert "`.claude/` directory doesn't exist" not in combined
```

- [ ] **Step 2: Verify it fails**

Run the new test. Expected: all three known contradictions are present.

- [ ] **Step 3: Make shared prose host-neutral**

Replace the preferences error condition with “skill-context directory does not
exist,” describe plan-review preferences as the current host's skill-context
path, and collapse the two platform rows in `skill-interfaces.md` into one
host-specific path statement that the adapter can safely transform.

- [ ] **Step 4: Verify contradiction tests pass**

Run the new test and plan-review adapter test. Expected: pass.

### Task 6: Regenerate and verify the complete collection

**Files:**
- Regenerate: `codex-skills/**`
- Verify: `tests/test_agy_adapter.py`
- Verify: `tests/test_codex_adapter.py`
- Verify: `tests/test_plan_review_skill_contract.py`

- [ ] **Step 1: Run focused tests before generation**

```powershell
python -m pytest tests/test_agy_adapter.py tests/test_codex_adapter.py tests/test_plan_review_skill_contract.py -q
```

Expected: only the committed-tree freshness test may fail until regeneration.

- [ ] **Step 2: Regenerate the Codex tree**

```powershell
python scripts\codex_adapter.py codex-skills --force
```

Expected: reports 21 generated skills.

- [ ] **Step 3: Run focused verification**

Run the focused test command again. Expected: all pass.

- [ ] **Step 4: Run full verification**

```powershell
python -m pytest tests skills -q
```

Expected: zero failures; the environment-dependent test may remain skipped.

- [ ] **Step 5: Inspect final changes and worktree state**

Run `git diff --check`, `git diff --stat`, and `git status --short`. Confirm no
existing devlog scraps were modified and no unrelated files changed.
