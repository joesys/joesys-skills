# Plain-Language Commit Messages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/commit` preserve technical accuracy while writing messages that remain understandable without recent task context.

**Architecture:** Treat the skill as prompt-as-code. A focused pytest contract defines the durable-reader behavior, the canonical `skills/commit/SKILL.md` supplies that behavior, and the existing deterministic adapter publishes the same rules to `codex-skills/commit/SKILL.md`.

**Tech Stack:** Markdown skill instructions, Python 3, pytest, and the repository's Codex adapter.

---

### Task 1: Define the failing plain-language contract

**Files:**
- Create: `tests/test_commit_skill_contract.py`
- Test: `tests/test_commit_skill_contract.py`

- [ ] **Step 1: Write the failing contract test**

Create `tests/test_commit_skill_contract.py` with this content:

```python
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
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m pytest tests/test_commit_skill_contract.py -q
```

Expected: FAIL because the current skill has no `Plain-Language Standard`, no
durable-reader question, and the README does not promise plain-language output.
The failure must be an assertion failure caused by missing behavior, not a test
import or syntax error.

---

### Task 2: Implement the plain-language standard

**Files:**
- Modify: `skills/commit/SKILL.md:57-92`
- Modify: `README.md:422-434`
- Regenerate: `codex-skills/commit/SKILL.md`
- Test: `tests/test_commit_skill_contract.py`

- [ ] **Step 1: Make subjects describe concrete outcomes**

In `skills/commit/SKILL.md`, replace the current em-dash subject rule with:

```markdown
- Make the description name the concrete outcome in plain language. Do not lead with an internal process label, evidence identifier, metaphor, or ceremony.
- Use an em dash (—) only when a short elaboration makes the outcome clearer.
```

- [ ] **Step 2: Add the plain-language standard and real example**

Insert this section between the subject examples and `## Body`:

````markdown
## Plain-Language Standard

Write every commit message for a durable reader: either a teammate who understands the project in general but does not know today's task, internal shorthand, or recent session history, or the author returning years later.

- Prefer ordinary words, short sentences, and active voice.
- State the concrete outcome before supporting evidence or implementation detail.
- When an acronym, gate name, code name, identifier, statistic, or specialized term is necessary, explain it on first use and say why it matters.
- Include hashes, counts, paths, and symbols only when they provide useful evidence or traceability. Do not make the reader decode raw inventory.
- Metaphors, slogans, ceremonial language, and dramatic descriptions MUST NOT replace concrete actions and outcomes.

Plain language does not mean removing technical accuracy. Keep the technical details that help a future reader understand the decision, verify important evidence, or recognize a risk; translate or omit details that only make sense inside the current session.

### Before and after

```text
Before: feat(research): the Gate-6 development-vintage mint — fingerprint 14d908e0
After:  feat(research): record the July 13 development data snapshot
```

The body should preserve the important incident and remaining risk without requiring the reader to know the project's shorthand:

```text
The snapshot-generation script still uses a manually updated output date. It
initially overwrote the July 12 snapshot, which was restored exactly before the
new snapshot was saved under July 13. The date handling should be fixed before
this becomes a routine process.
```
````

- [ ] **Step 3: Rewrite the three body requirements**

Replace the three body descriptions with:

```markdown
**1. Intent paragraph (2–3 sentences, no header)**
Explain the problem or need, the outcome, and why it matters. Give enough context for a reader who was not part of the current task. Start immediately after the blank line following the subject.

**2. `[--- Changes ---]`**
Summarize observable outcomes and important technical decisions. Organize by file or category when that helps, but do not inventory every edited line or repeat the diff. Include counts, paths, symbols, and hashes only when they provide useful evidence or traceability, and explain their significance.

**3. `[--- AI Review (<model name>) ---]`**
Give an honest assessment in direct, ordinary language. Use your current model name in the header (e.g., `[--- AI Review (Claude Opus 4.7) ---]`). State meaningful strengths, risks, trade-offs, and follow-up work without promotional, theatrical, or self-congratulatory prose.

### Durable-reader check

Before creating the commit, reread the complete message and ask:

> Could a teammate unfamiliar with this task, or the author returning years later, understand why this commit exists, what changed, and what still needs attention without the issue tracker or session history?

If the answer is no, rewrite the message before creating the commit.
```

- [ ] **Step 4: Update the README description**

Replace `README.md:424-428` with:

```markdown
Create a Conventional Commit in plain language for a reader without current-task
context. Every message retains an intent paragraph, meaningful change summary,
and candid AI review. The workflow can decompose multi-unit changes into a
OneFlow Option 3 branch, group related recent commits with user approval, and
recover from an unresponsive 1Password signing agent by creating an explicitly
reported unsigned commit.
```

- [ ] **Step 5: Regenerate the Codex collection**

Run:

```powershell
python scripts/codex_adapter.py codex-skills --force
```

Expected: `Built joesys-skills with 21 skills at ...\codex-skills`. Do not edit
`codex-skills/commit/SKILL.md` manually.

- [ ] **Step 6: Run the focused test and verify GREEN**

Run:

```powershell
python -m pytest tests/test_commit_skill_contract.py -q
```

Expected: `5 passed`.

---

### Task 3: Verify and commit the implementation

**Files:**
- Verify: `skills/commit/SKILL.md`
- Verify: `codex-skills/commit/SKILL.md`
- Verify: `tests/test_commit_skill_contract.py`
- Verify: `README.md`

- [ ] **Step 1: Verify generated-tree freshness**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py::test_committed_codex_skills_match_fresh_build -q
```

Expected: `1 passed`.

- [ ] **Step 2: Run the full repository suite**

Run:

```powershell
python -m pytest tests skills -q
```

Expected: all tests pass. A pytest collection warning for an optional or
environment-specific dependency is acceptable only if it already exists on the
base branch; test failures are not acceptable.

- [ ] **Step 3: Inspect the final diff and generated wording**

Run:

```powershell
git diff --check
git diff --stat
git status --short
rg -n "Plain-Language Standard|Durable-reader check|record the July 13" skills/commit/SKILL.md codex-skills/commit/SKILL.md
```

Expected: no whitespace errors; only the four implementation files are changed
or added, alongside the user's pre-existing untracked devlog scraps; both skill
surfaces contain the new standard and example.

- [ ] **Step 4: Commit the verified implementation**

Stage only the implementation files:

```powershell
git add -- skills/commit/SKILL.md tests/test_commit_skill_contract.py README.md codex-skills/commit/SKILL.md
```

Commit with this plain-language message:

```text
feat(commit): make commit messages readable without recent context

Write commit messages for teammates who were not part of the current task and
for authors returning years later. Keep technical evidence when it helps, but
explain its meaning instead of relying on internal shorthand.

[--- Changes ---]

- Add a durable-reader standard and a real before-and-after example to the
  canonical commit skill.
- Replace exhaustive diff narration with outcome-focused summaries and direct
  risk explanations.
- Publish the same behavior through the generated Codex skill and document it
  in the README.
- Add contract tests for every message section and the final readability check.

[--- AI Review (GPT-5.6) ---]

The new rules directly address the failure that produced an accurate but
unreadable message. Clear writing still requires judgment, so the example and
final reader check are important alongside the automated contract tests.
```

- [ ] **Step 5: Verify the commit and branch state**

Run:

```powershell
git status --short
git log --oneline --decorate -3
git log --oneline master..HEAD
```

Expected: the implementation commit appears only on
`feat/plain-language-commit-messages`; `master` remains at `5c8d0f2`; the only
remaining worktree entries are the pre-existing untracked devlog scraps. Do not
push.
