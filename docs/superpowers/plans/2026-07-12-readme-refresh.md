# README Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Repository instructions require inline execution; do not dispatch subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an accurate, task-oriented README for the current 21-skill Claude Code and Codex collection.

**Architecture:** Keep one comprehensive `README.md`, front-load quick-start and skill selection, and retain detailed usage under five task-oriented groups. Reconcile every factual claim against canonical skill files, shared contracts, manifests, and maintenance scripts.

**Tech Stack:** Markdown, PowerShell, Python 3.13, pytest contract checks.

---

### Task 1: Rebuild README navigation and host guidance

**Files:**
- Modify: `README.md`

- [x] **Step 1: Replace the opening and installation-first layout**

Add a concise product overview, supported-host table, quick-start commands, and
an explicit invocation rule showing `/skill` for Claude Code and `$skill` for
Codex.

- [x] **Step 2: Add the complete skill index**

Create a compact table containing all 21 canonical skill names, their purpose,
and links to their detailed README sections.

- [x] **Step 3: Verify index coverage**

Compare the index names with the directory names returned by:

```powershell
Get-ChildItem skills -Directory | Sort-Object Name | Select-Object -ExpandProperty Name
```

Expected: the same 21 names appear with no omissions or extras.

### Task 2: Reconcile detailed skill documentation

**Files:**
- Modify: `README.md`
- Reference: `skills/*/SKILL.md`
- Reference: `shared/model-defaults.md`
- Reference: `shared/skill-interfaces.md`

- [x] **Step 1: Reorganize skills into five task groups**

Move each detailed skill entry into its approved task-oriented group while
preserving useful tables and avoiding duplicated descriptions.

- [x] **Step 2: Correct descriptions and examples**

Check every public invocation against its canonical skill. Replace the stale
Codex model example with `gpt-5.6-sol`, describe the Antigravity adapter's
current-output and legacy-fallback behavior accurately, and keep host syntax
consistent.

- [x] **Step 3: Expand the newest workflow contracts**

Document all public `plan-review` options and its document-only, no-implementation
safety boundary. Document all public `handoff` create and resume options,
audiences, targets, drift classes, default output, and no-automatic-sharing
boundary.

### Task 3: Consolidate lifecycle and contributor guidance

**Files:**
- Modify: `README.md`
- Reference: `.claude-plugin/plugin.json`
- Reference: `.agents/plugins/marketplace.json`
- Reference: `.codex-plugin/plugin.json`
- Reference: `scripts/codex_adapter.py`
- Reference: `scripts/install_codex_skills.py`
- Reference: `scripts/reinstall-plugin.ps1`

- [x] **Step 1: Consolidate install, upgrade, and reinstall instructions**

Place normal installation in Quick Start and maintenance commands in a later
section. Keep Claude Code, Codex plugin, standalone Codex, marketplace upgrade,
and clean reinstall paths distinct.

- [x] **Step 2: Expand contributor instructions**

State that `skills/` and `shared/` are canonical, `codex-skills/` is generated,
and regeneration uses:

```powershell
python scripts\codex_adapter.py codex-skills --force
```

Include focused adapter verification and the committed-tree freshness guard.

### Task 4: Verify the completed README

**Files:**
- Verify: `README.md`

- [x] **Step 1: Check skill coverage and stale claims**

Use PowerShell and `rg` to compare canonical skill names with README entries and
confirm stale identifiers such as `gpt-5.3` are absent.

- [x] **Step 2: Check local Markdown links**

Extract relative Markdown link targets and verify every referenced repository
path exists.

- [x] **Step 3: Run repository verification**

```powershell
python -m pytest tests/test_codex_adapter.py -q
git diff --check
git status --short
```

Expected: tests pass, whitespace checks pass, and changes are limited to the
README design, plan, and `README.md`; the five existing devlog scraps remain
unmodified and untracked.

- [x] **Step 4: Review the final diff**

Confirm the README is concise enough to scan, detailed enough to use without
opening each skill contract, and contains no claims unsupported by canonical
repository sources.
