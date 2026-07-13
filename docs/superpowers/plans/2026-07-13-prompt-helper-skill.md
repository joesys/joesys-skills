# Prompt Helper Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a general-purpose `/prompt` skill that turns stream-of-consciousness input into a copy-ready prompt and explains the improvements.

**Architecture:** Keep the feature as one high-freedom canonical Markdown skill under `skills/prompt/`. Protect its behavioral contract with focused pytest assertions, generate the Codex copy through the existing adapter, document it in the README, and publish the collection as `18.0.0`.

**Tech Stack:** Agent Skills Markdown, Python 3, pytest, JSON plugin manifests, and `scripts/codex_adapter.py`.

**Repository execution constraint:** The repository instructions require sequential work in the main thread. Use `superpowers:executing-plans` for implementation and do not dispatch subagents.

---

## Verified Baseline

- Branch: `feat/prompt-helper-skill`
- Worktree: `.worktrees/prompt-helper-skill`
- Design commit: `fa5a84e docs(prompt): define adaptive prompt helper`
- Baseline command: `python -m pytest tests skills -q`
- Baseline result: `280 passed, 1 skipped`

## File Map

### Create

- `skills/prompt/SKILL.md` - canonical prompt-rewriting workflow and output contract.
- `tests/test_prompt_skill_contract.py` - prompt-as-code behavioral contract for canonical, generated, and README surfaces.
- `codex-skills/prompt/SKILL.md` - generated Codex-compatible skill; never edit by hand.

### Modify

- `README.md` - collection count, skill chooser row, and user-facing `prompt` section.
- `tests/test_codex_adapter.py` - published skill inventory, Codex invocation adaptation, and `18.0.0` release contract.
- `.claude-plugin/plugin.json` - `18.0.0`, prompt-writing description, and keywords.
- `.claude-plugin/marketplace.json` - `18.0.0`, prompt-writing description, and tags.
- `.codex-plugin/plugin.json` - `18.0.0` and prompt-writing interface text.
- `codex-skills/_manifest.json` - generated skill inventory and source version.

### Inspect but leave unchanged

- `.agents/plugins/marketplace.json` - this local source registry has no version or skill-description fields; release metadata belongs in the Claude and Codex plugin manifests.
- Existing files under `docs/devlog/.scraps/` - user-owned untracked files in the main checkout.

## Task 1: Add the Adaptive Prompt Skill

**Files:**

- Create: `tests/test_prompt_skill_contract.py`
- Create: `skills/prompt/SKILL.md`
- Create by generation: `codex-skills/prompt/SKILL.md`
- Modify by generation: `codex-skills/_manifest.json`
- Modify: `README.md:3-68`

- [ ] **Step 1: Write the failing prompt-skill contract**

Create `tests/test_prompt_skill_contract.py` with this complete content:

```python
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
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m pytest tests/test_prompt_skill_contract.py -q
```

Expected: `8 failed`. The skill tests must fail with `Missing prompt skill files`, and the README test must fail because the collection still advertises 21 skills.

If the test errors during collection or fails for a typo, fix the test and rerun until it fails only because the feature is missing.

- [ ] **Step 3: Initialize the skill directory**

Run the required skill-creator scaffold:

```powershell
python C:/Users/Joe/.codex/skills/.system/skill-creator/scripts/init_skill.py prompt --path skills
```

Expected: the command creates `skills/prompt/SKILL.md` and `skills/prompt/agents/openai.yaml`.

The collection does not publish per-skill `agents/openai.yaml` files. Delete `skills/prompt/agents/openai.yaml` with `apply_patch`, leaving no bundled resources or metadata files. The empty `agents/` directory does not need to be retained.

- [ ] **Step 4: Replace the scaffold with the canonical skill**

Replace `skills/prompt/SKILL.md` with this complete content:

`````markdown
---
name: prompt
description: "Use when the user invokes /prompt or asks to rewrite, improve, or turn rough, fragmented, or stream-of-consciousness thoughts into a prompt for another AI."
---

# Prompt Skill

## Purpose

Turn rough input into a clear, ready-to-copy prompt, then explain the meaningful changes so the operator learns how to write better prompts.

**Boundary:** Do not execute the generated prompt or begin the task it describes. This skill writes the prompt and stops.

## Invocation

```text
/prompt <request>
```

Treat all text after `/prompt` as the operator's source request. For an empty invocation, ask what they want turned into a prompt.

## Workflow

### 1. Recover the intent

Identify what the operator actually wants. Separate the goal from repetition, side comments, uncertainty, and conversational filler. Preserve the operator's intent, priorities, and meaningful voice.

The rewrite must not invent facts, deadlines, technologies, permissions, preferences, or requirements. It must not silently replace the requested task with a supposedly better task.

### 2. Decide whether to clarify

Material ambiguity changes the task, scope, permission, deliverable, or success criteria.

- If information is materially missing, ask one focused clarification at a time and wait for the answer. Do not generate the prompt yet.
- If uncertainty is minor, make a conservative assumption and disclose it in the explanation.
- If requirements conflict, ask the operator to resolve the conflict rather than choosing silently.
- Do not turn optional details into an interview.

### 3. Choose the target

Write a portable prompt by default. Tailor it to a named AI, coding agent, image generator, or other tool only when the operator names that target or the target materially changes the instructions.

Do not add provider-specific syntax to an otherwise portable prompt.

### 4. Build the smallest useful prompt

Create the smallest prompt that expresses the request clearly and completely. Consider:

- desired outcome;
- relevant context or source material;
- scope and boundaries;
- important constraints;
- requested deliverable and format;
- audience, tone, or detail level when relevant;
- success or verification criteria; and
- how the receiving AI should handle uncertainty.

Include only components that improve this request. Keep a simple task as a short paragraph. Use headings, bullets, delimiters, or ordered steps when complexity makes them useful.

### 5. Check and render

Run the Final Check, present the prompt first, explain the meaningful edits, and stop.

## Prompt-Writing Standard

- Put the task and desired outcome in clear, direct language.
- Include relevant context and remove unrelated detail.
- Prefer positive instructions that say what to do. Keep negative constraints when they define a real boundary.
- Define the output when format, audience, tone, length, or completeness matters.
- Add examples only when they communicate the expected format, style, or quality more clearly than prose.
- Use a functional role only when it adds relevant expertise, perspective, or tone. Do not add decorative claims such as "world-class expert."
- Put important instructions where they are easy to find and use consistent structure.
- Avoid repeating a requirement in several forms.

## Coding Requests

For software work, first distinguish diagnosis, implementation, review, or explanation. Add engineering details only when relevant:

- repository, file, feature, or branch scope;
- whether changes are authorized;
- interfaces, dependencies, or existing behavior to preserve;
- the required deliverable;
- how the result should be tested or otherwise verified; and
- how to report missing evidence instead of guessing.

Do not infer permission for destructive actions, pushes, external messages, or deployments. If that authority materially affects the request, clarify it.

## Output Format

Use this normal structure:

````text
## Prompt

```text
<ready-to-copy prompt>
```

## Why this prompt is stronger

- **Added:** <meaningful addition and why it helps>
- **Removed or simplified:** <removed material and why>
- **Reorganized:** <structural change and why>
- **Assumptions:** <conservative assumption and why it was safe>
- **Already strong:** <useful part of the original that was preserved>
````

Include only explanation labels that apply. Do not narrate every edit. Teach a reusable principle behind each meaningful change.

Keep the prompt copy-friendly. If it contains embedded code fences, use a longer outer fence so the entire prompt remains intact.

## Example

Input:

```text
/prompt can you check the auth thing, login sometimes hangs, don't change anything yet just tell me why and maybe what fix should be
```

Output:

````text
## Prompt

```text
Diagnose why login sometimes hangs in the current repository. Inspect the authentication flow and relevant logs or tests, but do not modify files.

Report:
- the most likely root cause with supporting evidence;
- other plausible causes you ruled out;
- the smallest recommended fix; and
- tests that would prove the fix.

If the repository does not contain enough evidence, state what information is missing instead of guessing.
```

## Why this prompt is stronger

- **Added:** A concrete diagnostic deliverable and evidence standard so the response can be checked.
- **Reorganized:** The request now separates the investigation boundary from the requested report.
- **Already strong:** The original "don't change anything yet" instruction was preserved as an explicit read-only boundary.
````

## Edge Cases

| Situation | Response |
|---|---|
| Empty invocation | Ask what the operator wants turned into a prompt. |
| Material ambiguity | Ask one focused question and wait. |
| Minor uncertainty | Use and disclose a conservative assumption. |
| Already-strong prompt | Make only worthwhile edits and explain what was already effective. |
| Contradictory requirements | Ask the operator to resolve the conflict. |
| Named target | Apply relevant target-specific conventions. |
| Embedded code fences | Preserve them with a longer outer fence. |
| Unsafe or disallowed request | Follow the host's safety rules; rewriting is not a bypass. |

## Final Check

Before returning the result, verify:

- Does the prompt preserve the operator's intent?
- Is the outcome clear without unnecessary detail?
- Are material gaps resolved and minor assumptions disclosed?
- Are there contradictory instructions?
- Did the rewrite invent facts, constraints, or authority?
- Is the structure proportionate to the task?
- Is the prompt shown before the teaching explanation?
- Did this skill stop without executing the generated prompt?

If any answer reveals a problem, revise before responding.
`````

- [ ] **Step 5: Update the README**

Make these exact README changes:

1. Replace lines 3-5 with:

```markdown
A collection of 22 agent skills for Claude Code and Codex: turn rough ideas
into reusable prompts, consult other AI models, review code and plans,
understand projects, improve engineering workflows, and preserve or publish
development work.
```

2. Add this row at the top of the `Choose a Skill` table, before the model-consulting rows:

```markdown
| Write prompts | [`prompt`](#prompt) | Turn rough thoughts into a copy-ready prompt and explain the improvements |
```

3. Insert this section between the chooser table and `## Consult Other AI Models`:

````markdown
## Write Better Prompts

### prompt

Turn rough, fragmented, or stream-of-consciousness input into a portable,
ready-to-copy prompt. The skill asks a focused question only when missing
information would materially change the result. It then explains what was
added, removed, reorganized, or assumed so the operator learns better prompting
habits over time.

```text
/prompt i need to explain our API migration to nontechnical managers, keep it short
/prompt login sometimes hangs, diagnose it but do not change anything
```

The skill writes the prompt and stops; it does not execute the generated task.
````

- [ ] **Step 6: Generate the Codex collection**

Run:

```powershell
python scripts/codex_adapter.py codex-skills --force
```

Expected: `codex-skills/prompt/SKILL.md` is created, `/prompt` becomes `$prompt` in that generated file, and `codex-skills/_manifest.json` lists `prompt` while the source version remains `17.1.0` until Task 2.

- [ ] **Step 7: Validate both skill packages**

Run:

```powershell
python C:/Users/Joe/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/prompt
python C:/Users/Joe/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-skills/prompt
```

Expected for each command: `Skill is valid!`

- [ ] **Step 8: Run the focused contract and verify GREEN**

Run:

```powershell
python -m pytest tests/test_prompt_skill_contract.py -q
```

Expected: `8 passed`.

If an assertion fails, fix the canonical skill or README, regenerate `codex-skills/`, and rerun. Do not edit the generated copy directly.

- [ ] **Step 9: Inspect and commit the feature**

Stage the canonical files and the complete generated tree so Git normalizes the adapter's LF output:

```powershell
git add -- tests/test_prompt_skill_contract.py skills/prompt README.md codex-skills
git diff --cached --check
git diff --cached --name-only -- codex-skills
```

Expected generated paths:

```text
codex-skills/_manifest.json
codex-skills/prompt/SKILL.md
```

Do not commit if other generated files have semantic diffs. Inspect with `git diff --cached -- <path>` and correct the cause first.

Commit with the repository's `/commit` workflow and this plain-language message:

```text
feat(prompt): turn rough ideas into reusable prompts

Add a general prompt-writing helper that preserves the operator's intent, asks only material questions, and teaches why its rewrite is stronger. The same behavior is published for Claude Code and Codex.

[--- Changes ---]

- Add the canonical prompt skill, focused behavior contracts, README guidance, and the generated Codex copy.
- Keep prompts portable by default while adding relevant coding and named-target instructions.

[--- AI Review (GPT-5) ---]

The workflow is deliberately adaptive rather than template-driven, which keeps small requests concise. Its quality still depends on judgment about material ambiguity, so the contract and examples make that boundary explicit.
```

Do not push.

## Task 2: Publish Release 18.0.0

**Files:**

- Modify: `tests/test_codex_adapter.py:16-38,78-94,239-259,314-320`
- Modify: `.claude-plugin/plugin.json:3-84`
- Modify: `.claude-plugin/marketplace.json:4-54`
- Modify: `.codex-plugin/plugin.json:3-11`
- Modify by generation: `codex-skills/_manifest.json`

- [ ] **Step 1: Update release and inventory tests first**

Apply these exact changes to `tests/test_codex_adapter.py`:

1. Add `"prompt",` to `EXPECTED_SKILLS` between `"preferences",` and `"quick-review",`.
2. In `test_slash_commands_become_skill_mentions`, after the Codex review assertion, add:

```python
    prompt = (output / "prompt" / "SKILL.md").read_text(encoding="utf-8")
    assert "$prompt <request>" in prompt
    assert "/prompt <request>" not in prompt
```

3. Change the pinned version assertion to:

```python
    assert claude_plugin["version"] == "18.0.0"
```

4. Replace the release-inventory test with:

```python
def test_generated_manifest_publishes_release_18_with_22_skills(tmp_path):
    output = tmp_path / "joesys-skills"
    manifest = codex_adapter.build_collection(REPO_ROOT, output)

    assert manifest["source_version"] == "18.0.0"
    assert len(manifest["installed_skills"]) == 22
    assert "prompt" in manifest["installed_skills"]
```

- [ ] **Step 2: Run the release contract and verify RED**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py::test_plugin_versions_are_synchronized tests/test_codex_adapter.py::test_generated_manifest_publishes_release_18_with_22_skills -q
```

Expected: `2 failed` because the live plugin metadata and generated source version are still `17.1.0`. The skill count should already be 22.

- [ ] **Step 3: Update Claude plugin metadata**

In `.claude-plugin/plugin.json`:

- Set `"version"` to `"18.0.0"`.
- Change the description to:

```json
"description": "Custom Claude Code skills — prompt writing, multi-model AI delegation, structured git commits, cross-session handoffs, iterative spec and plan review, code review, quick review, readability review, human review guide, codebase explanation, project handbook generation, codebase quality audit, devlog writing, retrospectives, interaction review, markdown export, and screenshot analysis",
```

- Add these keywords after `"automation"`:

```json
"prompt",
"prompt-writing",
"prompt-engineering",
"prompt-coaching",
```

In `.claude-plugin/marketplace.json`:

- Set the plugin `"version"` to `"18.0.0"`.
- Change the root description to:

```json
"description": "Custom Claude Code skills and plugins for prompt writing, delegation, plan review, code review, and engineering workflows by joesys",
```

- Change the plugin description to the same prompt-writing description used in `.claude-plugin/plugin.json`.
- Add these tags after `"automation"`:

```json
"prompt",
"prompt-writing",
"prompt-engineering",
"prompt-coaching",
```

- [ ] **Step 4: Update Codex plugin metadata**

In `.codex-plugin/plugin.json`:

- Set `"version"` to `"18.0.0"`.
- Change the description to:

```json
"description": "Custom agent skills — prompt writing, multi-model AI delegation, structured git commits, cross-session handoffs, iterative spec and plan review, code review, quick review, readability review, human review guide, codebase explanation, project handbook generation, codebase quality audit, devlog writing, retrospectives, interaction review, markdown export, and screenshot analysis",
```

- Change `interface.shortDescription` to:

```json
"shortDescription": "Prompt writing, model delegation, plan review, handoffs, commits, audits, and docs skills"
```

Do not add a version to `.agents/plugins/marketplace.json`. That file registers a local source and intentionally delegates release identity to `.codex-plugin/plugin.json`.

- [ ] **Step 5: Regenerate the Codex collection**

Run:

```powershell
python scripts/codex_adapter.py codex-skills --force
```

Expected: `codex-skills/_manifest.json` now has `"source_version": "18.0.0"` and still lists 22 skills including `prompt`.

- [ ] **Step 6: Run the focused release and adapter tests**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py::test_plugin_versions_are_synchronized tests/test_codex_adapter.py::test_generated_manifest_publishes_release_18_with_22_skills -q
python -m pytest tests/test_codex_adapter.py -q
```

Expected:

- First command: `2 passed`.
- Second command: `19 passed`.

- [ ] **Step 7: Inspect and commit the release**

Stage only the release contract, metadata, and generated tree:

```powershell
git add -- tests/test_codex_adapter.py .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json codex-skills
git diff --cached --check
git diff --cached --name-only
```

Expected semantic changes:

```text
.claude-plugin/marketplace.json
.claude-plugin/plugin.json
.codex-plugin/plugin.json
codex-skills/_manifest.json
tests/test_codex_adapter.py
```

The already-committed `codex-skills/prompt/SKILL.md` may be staged only as a line-ending stat refresh; verify it has no semantic diff.

Commit with the repository's `/commit` workflow and this plain-language message:

```text
chore(plugin): publish prompt helper as version 18.0.0

Publish the new prompt-writing skill as a major collection release. Keep Claude, Codex, marketplace, generated-manifest, and version-test metadata synchronized so users receive the same 22-skill package.

[--- Changes ---]

- Bump the published collection from 17.1.0 to 18.0.0.
- Register prompt in the adapter inventory and add prompt-writing descriptions and discovery terms.

[--- AI Review (GPT-5) ---]

The release changes are mechanical and protected by synchronized-version and generated-tree tests. The major version follows the user's release policy for adding a new skill rather than conventional backward-compatible feature semantics.
```

Do not push.

## Task 3: Review Behavior and Run the Final Gate

**Files:**

- Inspect: `skills/prompt/SKILL.md`
- Inspect: `codex-skills/prompt/SKILL.md`
- Inspect: all files changed since `da68610`

- [ ] **Step 1: Review representative behavior sequentially**

Project instructions disallow subagent dispatch. In the current main thread, walk the completed skill through each scenario and compare its prescribed response with this matrix:

| Input | Required behavior |
|---|---|
| `/prompt need a cheap 3 day vegetarian meal plan, no mushrooms, maybe a table` | Generate immediately; preserve the constraints and table preference; show the prompt before the teaching explanation. |
| `/prompt build an app` | Ask one focused material question and wait; do not generate or execute the app prompt yet. |
| `/prompt diagnose why login hangs in this repo, do not edit anything` | Produce a read-only diagnostic prompt with evidence, deliverable, and verification expectations; do not execute it. |
| `/prompt rewrite this for Claude: summarize the attached contracts` with no attachment | Ask one focused question for the missing source material because it changes whether the task can be completed. |
| A clear prompt that already states goal, context, constraints, and output | Keep it compact; explain what was already strong instead of adding boilerplate. |
| A request containing an inner triple-backtick code sample | Use a longer outer fence so the copied prompt remains intact. |

For each row, confirm:

- intent is preserved;
- no facts or authority are invented;
- clarification occurs only when material;
- the prompt remains proportionate to the request;
- explanation labels are included only when relevant; and
- the generated task is not executed.

If the skill text permits a wrong result, add the smallest explicit rule or example needed, regenerate `codex-skills/`, and rerun the focused contract before continuing.

- [ ] **Step 2: Validate canonical and generated skill structure**

Run:

```powershell
python C:/Users/Joe/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/prompt
python C:/Users/Joe/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-skills/prompt
```

Expected: `Skill is valid!` twice.

- [ ] **Step 3: Verify generated-tree freshness**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py::test_committed_codex_skills_match_fresh_build -q
```

Expected: `1 passed`.

- [ ] **Step 4: Run focused prompt contracts**

Run:

```powershell
python -m pytest tests/test_prompt_skill_contract.py -q
```

Expected: `8 passed`.

- [ ] **Step 5: Run the complete repository suite**

Run:

```powershell
python -m pytest tests skills -q
```

Expected: `288 passed, 1 skipped`.

- [ ] **Step 6: Verify the complete branch state**

Run:

```powershell
git diff --check da68610...HEAD
git status --short
git log --oneline --graph --decorate -8
```

Expected:

- No whitespace errors.
- The feature worktree has no tracked or untracked implementation files.
- The branch contains the design, implementation-plan, prompt-feature, and `18.0.0` release commits.
- Nothing has been pushed.

If any verification fails, fix the cause, rerun the narrowest failing check, and then rerun the complete repository suite before reporting completion.
