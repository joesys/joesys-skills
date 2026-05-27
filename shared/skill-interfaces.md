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
**Antigravity resume:** `/antigravity resume [prompt]` or `/antigravity resume <ID> [prompt]`
**Claude resume:** `/claude resume [prompt]` or `/claude resume <name> [prompt]`

**Callers:**
- `skills/ai-council/SKILL.md` — Post-Synthesis Options, item 1


## Review Principles Interface

**Path:** `skills/codereview/principles/*.md`

**Files:** `correctness.md`, `security.md`, `architecture.md`, `clean-code.md`, `performance.md`, `reliability.md`

**Behavior contract:**
- Each file contains review principles for one domain
- Subagents read these files during analysis and evaluate code against every principle listed
- Files are structured as markdown with principle names, descriptions, and examples

**Callers:**
- `skills/codereview/SKILL.md` — Phase 2: all 6 domain subagents read their respective principle file
- `skills/quick-review/SKILL.md` — Phase 2, Track 2: correctness and security subagents read `correctness.md` and `security.md`

**Note:** Quick-review reaches into `skills/codereview/principles/` for its principle files. This is an intentional cross-skill dependency — the principles are shared content, not codereview-exclusive. If the principles directory is moved or restructured, both skills must be updated.

## Preferences Skill Interface

**Invocation:** `/preferences [skill-name | show | reset]`

**Behavior contract:**
- `/preferences` — runs the shared interview, saves to `.claude/skill-context/preferences.md`
- `/preferences <skill-name>` — runs skill-specific interview, saves to `.claude/skill-context/<skill-name>.md`
- `/preferences show` — displays all current preferences
- `/preferences reset` — clears all preference files after confirmation
- When invoked by another skill (first-contact case): runs streamlined core interview only, skips skill-specific deep-dives, returns control to caller

**File contract:**
- Shared preferences: `.claude/skill-context/preferences.md`
- Skill-specific: `.claude/skill-context/<skill-name>.md`
- Files are plain markdown, human-readable and hand-editable
- Skills must handle missing files gracefully (first-run case)

**Callers:**
- All skills in this collection — each checks for shared preferences during their earliest phase and invokes `/preferences` if missing. See `shared/skill-context.md` for the full context-loading protocol.

## Commit Skill Interface

**Invocation:** `/commit`

**Callers:**
- `skills/retrospective/SKILL.md` — Final Steps, step 2 (for committing approved improvements)

## Interaction Review Interfaces

**Invocation:** `/interaction-review [session <id> | since YYYY-MM-DD | trend]`

**Behavior contract:**
- Analyzes JSONL session transcripts from `~/.claude/projects/<project-dir>/`
- Produces dual-format reports: `docs/interaction-review/YYYYMMDD-interaction-review.md` (and `.html`)
- Reads previous reports from `docs/interaction-review/` for continuity tracking
- Does NOT modify source code, CLAUDE.md, or memory — suggestions only

**Callers:**
- None currently — this skill is user-invoked only

**Outbound interfaces (soft):**
- Devlog scrap: offers `/devlog scrap --from-context interaction-review findings` after report generation
- Preferences: loads shared + skill-specific preferences in Phase 0
- HTML render: calls `scripts/html_render.py` in Phase 4

## Human Review Guide Interface

**Invocation:** `/human-review-guide [PR#<number> | <path>] [--with-review] [--calibrate]`

**Behavior contract:**
- Analyzes diffs, files, or directories to produce a guided reading order for human reviewers
- Classifies chunks into 4 attention tiers: DECIDE, READ, SKIM, SKIP
- Deep analysis only on DECIDE and READ chunks
- `--with-review` checks the current session for `/codereview` output — never auto-triggers `/codereview`
- Produces terminal markdown (≤5 files and ≤200 lines) or HTML report (larger)
- Does NOT modify source code, does NOT perform code review, does NOT make decisions for the reviewer

**Callers:**
- None currently — this skill is user-invoked only

**Outbound interfaces (soft):**
- Preferences: loads shared + skill-specific preferences in Phase 0
- Code-review findings: optionally consumes `/codereview` output from session context (via `--with-review`)
- HTML render: calls `scripts/html_render.py` in Phase 3.7

---

**Rules:**
- Before changing any interface listed above, check all callers.
- If a caller uses "skip silently if skill unavailable," the interface
  is soft — breaking it won't cause errors, just lost functionality.
- If a caller depends on the result, the interface is hard — breaking
  it will cause visible failures.
