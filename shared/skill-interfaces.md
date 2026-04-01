# Cross-Skill Interface Contracts

Some skills auto-invoke or reference other skills. This file documents
the stable interfaces that callers depend on. If you modify these
interfaces, update all callers listed below.

## Devlog Scrap Interface

**Invocation:** `/devlog scrap --from-context [hint]`

**Behavior contract:**
- Captures a devlog scrap using only the current conversation context
- Does NOT dispatch subagents (no Phase 1/2 gathering)
- Writes to `docs/devlog/.scraps/YYYYMMDD-<topic>.md`
- Silently succeeds or fails — callers do not check the result
- If the `.scraps/` directory doesn't exist, creates it

**Callers:**
- `skills/commit/SKILL.md` — Post-Commit: Devlog Scrap Capture section
- `skills/retrospective/SKILL.md` — Final Steps, step 1
- `skills/ai-council/SKILL.md` — Post-Synthesis Options, item 3 (suggestion only)

## Delegation Skill Resume Interfaces

**Codex resume:** `/codex resume [prompt]`
**Gemini resume:** `/gemini resume [prompt]` or `/gemini resume <index> [prompt]`
**Claude resume:** `/claude resume [prompt]` or `/claude resume <name> [prompt]`

**Callers:**
- `skills/ai-council/SKILL.md` — Post-Synthesis Options, item 1

## Review Principles Interface

**Path:** `skills/code-review/principles/*.md`

**Files:** `correctness.md`, `security.md`, `architecture.md`, `clean-code.md`, `performance.md`, `reliability.md`

**Behavior contract:**
- Each file contains review principles for one domain
- Subagents read these files during analysis and evaluate code against every principle listed
- Files are structured as markdown with principle names, descriptions, and examples

**Callers:**
- `skills/code-review/SKILL.md` — Phase 2: all 6 domain subagents read their respective principle file
- `skills/quick-review/SKILL.md` — Phase 2, Track 2: correctness and security subagents read `correctness.md` and `security.md`

**Note:** Quick-review reaches into `skills/code-review/principles/` for its principle files. This is an intentional cross-skill dependency — the principles are shared content, not code-review-exclusive. If the principles directory is moved or restructured, both skills must be updated.

## Commit Skill Interface

**Invocation:** `/commit`

**Callers:**
- `skills/retrospective/SKILL.md` — Final Steps, step 2 (for committing approved improvements)

---

**Rules:**
- Before changing any interface listed above, check all callers.
- If a caller uses "skip silently if skill unavailable," the interface
  is soft — breaking it won't cause errors, just lost functionality.
- If a caller depends on the result, the interface is hard — breaking
  it will cause visible failures.
