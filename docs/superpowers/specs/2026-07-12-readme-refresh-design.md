# README Refresh Design

**Date:** 2026-07-12
**Status:** Approved

## Purpose

Rewrite `README.md` so it accurately documents the current 21-skill collection
for both Claude Code and Codex. The result should help a new user choose the
right skill quickly while retaining enough detail to install, invoke, update,
and contribute to the plugin safely.

## Information Architecture

The README will use a hybrid structure:

1. A concise overview and host support statement.
2. A quick start for Claude Code and Codex.
3. A compact index of all 21 skills.
4. Task-oriented skill groups rather than implementation-oriented parts.
5. Detailed descriptions and current examples for every skill.
6. Installation maintenance and contributor instructions near the end.

The task-oriented groups are:

- Consult other AI models.
- Review code and plans.
- Understand and document projects.
- Track health and improve workflows.
- Capture, transfer, and publish work.

## Content Rules

- Treat `skills/*/SKILL.md`, `shared/model-defaults.md`,
  `shared/skill-interfaces.md`, and plugin manifests as authoritative.
- Show Claude Code invocation as `/skill` and Codex invocation as `$skill`.
- Use Claude-style slash commands in detailed examples, with one prominent note
  explaining the direct Codex substitution.
- List every canonical skill exactly once in the index and once in its detailed
  task group.
- Correct stale model identifiers and CLI behavior.
- Give the recently added `plan-review` and `handoff` workflows complete option
  coverage and concise safety boundaries.
- Explain that `skills/` is canonical and `codex-skills/` is generated.
- Keep generated-file regeneration and freshness verification copy-pasteable on
  Windows PowerShell.
- Preserve useful tables and examples where they materially clarify behavior.

## Scope

The implementation edits `README.md` and adds only this design and its execution
plan. It does not change skill contracts, generated Codex skills, manifests,
versions, or runtime code. Existing untracked devlog scraps remain untouched.

## Acceptance Criteria

- The README names all 21 skills and no nonexistent skill.
- Installation and update instructions match current manifests and scripts.
- Claude Code and Codex invocation syntax is unambiguous.
- The documented default Codex model matches `shared/model-defaults.md`.
- `plan-review` and `handoff` examples cover their current public interfaces.
- Every relative Markdown link resolves to a tracked repository path.
- Contributor instructions identify canonical and generated sources correctly.
- Markdown formatting and repository checks pass with no unrelated changes.
