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
