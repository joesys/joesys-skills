# Cross-Skill Interface Contracts

Some skills auto-invoke or reference other skills. This file documents
the stable interfaces that callers depend on. If you modify these
interfaces, update all callers listed below.

## Devlog Scrap Interface

**Invocation:** `$devlog scrap --from-context [hint]`

**Behavior contract:**
- Captures a devlog scrap using only the current conversation context
- Does NOT dispatch subagents (no Phase 1/2 gathering)
- Writes to `docs/devlog/.scraps/YYYYMMDD-<topic>.md`
- Silently succeeds or fails — callers do not check the result
- If the `.scraps/` directory doesn't exist, creates it

**Callers:**
- `../commit/SKILL.md` — Post-Commit: Devlog Scrap Capture section
- `../retrospective/SKILL.md` — Final Steps, step 1
- `../ai-council/SKILL.md` — Post-Synthesis Options, item 3 (suggestion only)

## Delegation Skill Resume Interfaces

**Codex resume:** `$codex resume [prompt]` or `$codex resume <SESSION_ID> [prompt]`
**Antigravity resume:** `$antigravity resume [prompt]` or `$antigravity resume <ID> [prompt]`
**Claude resume:** `$claude resume [prompt]` or `$claude resume <name> [prompt]`
**Grok resume:** `$grok resume [prompt]` or `$grok resume <SESSION_ID> [prompt]`

**Callers:**
- `../ai-council/SKILL.md` — Post-Synthesis Options, item 1 (Codex, Antigravity, and Claude only)
- Grok resume has no caller — `$grok` is user-invoked only


## Review Principles Interface

**Path:** `../codereview/principles/*.md`

**Files:** `correctness.md`, `security.md`, `architecture.md`, `clean-code.md`, `performance.md`, `reliability.md`

**Behavior contract:**
- Each file contains review principles for one domain
- Subagents read these files during analysis and use them as a lens, reporting only problems that matter in the change
- Files are short markdown lenses: principle names, heuristics tables, severity guidance, and when not to flag

**Callers:**
- `../codereview/SKILL.md` — Phase 2: each domain subagent reads its principle file (story readability reads `./story-readability.md`)
- `../quick-review/SKILL.md` — Phase 2: the correctness and security subagents read `correctness.md` and `security.md`

**Note:** Quick-review reaches into `../codereview/principles/` for its principle files. This is an intentional cross-skill dependency — the principles are shared content, not codereview-exclusive. If the principles directory is moved or restructured, both skills must be updated.

## Commit Skill Interface

**Invocation:** `$commit`

**Callers:**
- `../retrospective/SKILL.md` — Final Steps, step 2 (for committing approved improvements)
- `../devlog/references/write-mode.md` — publishing a post
- `../restructure-commit/SKILL.md` — reads the commit message format and the
  OneFlow Option 3 merge rules from `../commit/SKILL.md`

## Restructure Commit Interface

**Invocation:** `$restructure-commit [<commit-range or hashes>]`

**Behavior contract:**
- Groups recent related commits, plus any new uncommitted work, into one
  OneFlow Option 3 merge bubble.
- Uses the message format from `../commit/SKILL.md`.
- Shows the plan and waits for approval before rewriting history.
- Never pushes. A force push after the rewrite needs its own explicit approval.

**Callers:**
- `../commit/SKILL.md` — suggests it in one line when recent commits look
  related; never invokes it automatically

## Interaction Review Interfaces

**Invocation:** `$interaction-review [session <id> | since YYYY-MM-DD | trend]`

**Behavior contract:**
- Analyzes JSONL session transcripts from `~/.claude/projects/<project-dir>/`
- Produces dual-format reports: `docs/interaction-review/YYYYMMDD-interaction-review.md` (and `.html`)
- Reads previous reports from `docs/interaction-review/` for continuity tracking
- Does NOT modify source code, CLAUDE.md, or memory — suggestions only

**Callers:**
- None currently — this skill is user-invoked only

**Outbound interfaces (soft):**
- Devlog scrap: offers `$devlog scrap --from-context interaction-review findings` after report generation
- Preferences: loads shared + skill-specific preferences in Phase 0
- HTML render: calls `../scripts/html_render.py` in Phase 4

## Human Review Guide Interface

**Invocation:** `$human-review-guide [PR#<number> | <path>] [--with-review] [--calibrate]`

**Behavior contract:**
- Analyzes diffs, files, or directories to produce a guided reading order for human reviewers
- Classifies chunks into 4 attention tiers: DECIDE, READ, SKIM, SKIP
- Deep analysis only on DECIDE and READ chunks
- `--with-review` checks the current session for `$codereview` output — never auto-triggers `$codereview`
- Produces terminal markdown (≤5 files and ≤200 lines) or HTML report (larger)
- Does NOT modify source code, does NOT perform code review, does NOT make decisions for the reviewer

**Callers:**
- None currently — this skill is user-invoked only

**Outbound interfaces (soft):**
- Preferences: loads shared + skill-specific preferences in Phase 0
- Code-review findings: optionally consumes `$codereview` output from session context (via `--with-review`)
- HTML render: calls `../scripts/html_render.py` in Phase 3.7

## Handoff Skill Interface

**Invocation:** `$handoff [--full | --compact] [--interactive] [--for self|agent|human] [--target auto|claude|codex|antigravity|generic] [--include-diff] [--output <path>]`

**Resume:** `$handoff resume [<file>]`

**Behavior contract:**
- Creates a schema-version-1 Markdown checkpoint under `.handoffs/` by default.
- Stores deterministic repository state as compact JSON in the
  `repository_snapshot` frontmatter field.
- Uses one canonical artifact schema for `self`, `agent`, and `human`
  audiences; target differences are confined to Target Bootstrap.
- Without a resume path, selects the newest valid handoff matching the current
  project identity.
- Continues the recorded next action automatically for `exact` and safely
  `advanced` repository states.
- MUST stop before mutation for `drifted` state.
- Treats `unverifiable` state as a warning that requires relevant-file
  inspection before continuation.
- Never overwrites an existing handoff and never edits `.gitignore`
  automatically.
- Does not auto-invoke sibling skills or commit, push, publish, or share the
  artifact.

**Stable enum values:**
- Audience: `self`, `agent`, `human`
- Target: `auto`, `claude`, `codex`, `antigravity`, `generic`
- Detail: `operational`, `full`, `compact`
- Drift: `exact`, `advanced`, `drifted`, `unverifiable`

**Callers:**
- None currently — this skill is user-invoked only

---

**Rules:**
- Before changing any interface listed above, check all callers.
- If a caller uses "skip silently if skill unavailable," the interface
  is soft — breaking it won't cause errors, just lost functionality.
- If a caller depends on the result, the interface is hard — breaking
  it will cause visible failures.
