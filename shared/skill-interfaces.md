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

**Codex resume:** `/codex resume [prompt]` or `/codex resume <SESSION_ID> [prompt]`
**Antigravity resume:** `/antigravity resume [prompt]` or `/antigravity resume <ID> [prompt]`
**Claude resume:** `/claude resume [prompt]` or `/claude resume <name> [prompt]`
**Grok resume:** `/grok resume [prompt]` or `/grok resume <SESSION_ID> [prompt]`

**Callers:**
- `skills/ai-council/SKILL.md` — Post-Synthesis Options, item 1 (Codex, Antigravity, Claude, and Grok)


## Review Principles Interface

**Path:** `skills/codereview/principles/*.md`

**Files:** `correctness.md`, `security.md`, `architecture.md`, `clean-code.md`, `performance.md`, `reliability.md`

**Behavior contract:**
- Each file contains review principles for one domain
- Subagents read these files during analysis and use them as a lens, reporting only problems that matter in the change
- Files are short markdown lenses: principle names, heuristics tables, severity guidance, and when not to flag

**Callers:**
- `skills/codereview/SKILL.md` — Phase 2: each domain subagent reads its principle file (story readability reads `shared/story-readability.md`)
- `skills/quick-review/SKILL.md` — Phase 2: the correctness and security subagents read `correctness.md` and `security.md`

**Note:** Quick-review reaches into `skills/codereview/principles/` for its principle files. This is an intentional cross-skill dependency — the principles are shared content, not codereview-exclusive. If the principles directory is moved or restructured, both skills must be updated.

## Commit Skill Interface

**Invocation:** `/commit`

**Callers:**
- `skills/retrospective/SKILL.md` — Final Steps, step 2 (for committing approved improvements)
- `skills/devlog/references/write-mode.md` — publishing a post
- `skills/restructure-commit/SKILL.md` — reads the commit message format and the
  OneFlow Option 3 merge rules from `skills/commit/SKILL.md`
- `skills/joesys-mode/SKILL.md` — Ask First: every commit that the mode makes

## Restructure Commit Interface

**Invocation:** `/restructure-commit [<commit-range or hashes>]`

**Behavior contract:**
- Groups recent related commits, plus any new uncommitted work, into one
  OneFlow Option 3 merge bubble.
- Uses the message format from `skills/commit/SKILL.md`.
- Shows the plan and waits for approval before rewriting history.
- Never pushes. A force push after the rewrite needs its own explicit approval.

**Callers:**
- `skills/commit/SKILL.md` — suggests it in one line when recent commits look
  related; never invokes it automatically

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

## Handoff Skill Interface

**Invocation:** `/handoff [--full | --compact] [--interactive] [--for self|agent|human] [--target auto|claude|codex|antigravity|generic] [--include-diff] [--output <path>]`

**Resume:** `/handoff resume [<file>]`

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

## Create Verification Skill Interface

**Invocation:** `/create-verification-skill [<app or folder>]`

**Behavior contract:**
- Writes one project-local skill, `verify-<app>`, to the project skill folder
  that the running host reads.
- The generated skill has six sections (Launch, Doctor, Drive, Evidence,
  Cleanup, Helpers) and a feature map under `features/`.
- Runs the generated skill once before it reports. Without that run, it
  reports a draft.
- Labels every proof `live` or `fake` for each outside service.
- Never reads secrets, never changes product code, and never commits or pushes.

**Callers:**
- None currently — this skill is user-invoked only

## Create Formal Verification Skill Interface

**Invocation:** `/create-formal-verification-skill [<area, file, or bug>]`

**Behavior contract:**
- Verifies one property of the code with a model checker, a prover, or
  another verifier, and writes one project-local skill, `formal-<area>`, to
  the project skill folder that the running host reads.
- The `formal-` prefix keeps its output apart from the `verify-<app>` skills
  that `/create-verification-skill` writes.
- The generated check command fails when the covered code differs from the
  code at the recorded sync commit.
- Breaks the real code on purpose once, to show that the generated skill
  catches the break, and then restores the code.
- Asks before it installs a tool. Never changes product code unless asked,
  and never commits or pushes.

**Callers:**
- None currently — this skill is user-invoked only

## Joesys Mode Interface

**Invocation:** `/joesys-mode [<task>]`

**Behavior contract:**
- Restates the user's goal first, then follows one of four step lists
  (Investigation, Bug fix, Feature, Refactoring). Each list ends with a check.
- Holds 32 principles in three phases. They come before the step lists.
- The project's own rules and the user's current message win over the mode.
- Never pushes and never opens a pull request without approval in the current
  message.
- Runs `/commit` for every commit. Names `/explain` and
  `/create-verification-skill` as options and never runs them.

**Callers:**
- None currently — this skill is user-invoked only

---

**Rules:**
- Before changing any interface listed above, check all callers.
- If a caller uses "skip silently if skill unavailable," the interface
  is soft — breaking it won't cause errors, just lost functionality.
- If a caller depends on the result, the interface is hard — breaking
  it will cause visible failures.

## Why Interface

**Invocation:** `/why [<question, file, symbol, or line range>]`

**Behavior contract:**
- Answers why code is built the way it is, with a citation and one of five
  confidence tiers (Stated, Supported, Inferred, Guess, Unknown) on every
  claim. The answer comes first.
- Always searches two sources: the version control history, and the
  project's own written record. Searches an outside source only when the
  host already has a connector for it.
- Reports each search that found nothing, including a repository without
  pull requests.
- Reads only. Changes no file in the project and never writes to an outside
  service.

**Callers:**
- None currently — this skill is user-invoked only

## Blast Radius Interface

**Invocation:** `/blast-radius [--commit <hash> | --pr <number> | <description>]`

**Behavior contract:**
- Finds what a change could break outside its own diff, and the one fact
  that the change is safe because of.
- Proves that fact with a script or a test that runs the real code, or
  writes `unproven`. Every fact carries one of five proof levels: Said,
  Pointed, Walked, Ran, Reproduced.
- Names `/why`, `/codex`, `/antigravity` and `/ai-council` as options. It
  runs none of them by itself.
- Changes no product code. Leaves its proof script uncommitted and names it
  in the reply. Never commits or pushes.

**Callers:**
- None currently — this skill is user-invoked only

## Benchmark Checklist Interface

**Invocation:** `/benchmark-checklist [<claim, script, or two options>]`

**Behavior contract:**
- Tests a measured performance number with seven questions, each answered
  from a run: the limit, the tuning, the arithmetic, the errors, the
  repeat runs, the share of the whole, and whether the work ran at all.
- The verdict is one of four words: faster, slower, no measurable
  difference, or inconclusive. Every number carries its run count and its
  range.
- A rough number needs one run, and still answers the questions about
  errors and about whether the work ran.
- Changes no product code. Asks before it installs a tool, and before it
  puts load on a shared or paid service.

**Callers:**
- None currently — this skill is user-invoked, or loaded when a measured
  number is about to be reported

## Maintain Verification Skill Interface

**Invocation:** `/maintain-verification-skill [<skill name or folder>]`

**Behavior contract:**
- Works on a project-local `verify-<app>` skill that
  `/create-verification-skill` wrote, or on any project skill with launch
  and drive sections and a feature map. Without one, it stops and points to
  `/create-verification-skill`.
- Reads the source of every feature and drives every feature once in the
  real app. Corrects only what a run proved.
- Ends with one outcome: `clean`, `changed`, or `blocked`, and says how
  many features it drove out of how many.
- Updates the `run` and `not run` marks in the feature map index.
- Edits only the verification skill's own folder. Never edits product
  code, and never commits or pushes.

**Callers:**
- `skills/create-verification-skill/SKILL.md` — Step 5 report (a pointer
  only; it does not run this skill)

## Architect Interface

**Invocation:** `/architect [--local] [--save [--path <folder>]] <what to design>`

**Behavior contract:**
- Produces one design package for new code: the caller's usage, a type
  sketch with `not implemented` bodies, the module map, and the reasons.
  The package has the nine sections of
  `skills/architect/references/design-package.md`.
- Compares at least two candidates that differ in their whole shape. One
  comes from a subagent of the host. The others come from other models
  through `shared/cross-model-dispatch.md`, unless `--local` is set.
- Designs and stops. Writes no code file in the project, and never
  implements, commits, or pushes. `--save` writes the package to
  `docs/architect/<short-name>.md`.
- Names `/explain`, `/why`, `/codex`, `/antigravity` and `/ai-council` as
  options. It runs none of them by itself.

**Callers:**
- None currently — this skill is user-invoked only

## Security Audit Interface

**Invocation:** `/security-audit [<path>] [--include <ignored path>] [--out <folder>]`

**Behavior contract:**
- Audits a codebase for security flaws by reading its source. It sends no
  request to a running app, changes no file in the project, applies no fix,
  and never commits or pushes.
- Uses four models in the roles of `shared/model-defaults.md` § Security
  Audit Roles: two finders that work alone, the host as the writer that
  checks every candidate against the code, and a reviewer from the other
  provider. Writer and reviewer exchange at most two rounds. What is still
  open is printed as two views. An optional third finder (Grok), a manual
  run in the interactive Codex program, and two fallback reviewers are
  described in `skills/security-audit/references/extra-runs.md`.
- Runs the other models in the background with no time limit, through
  `skills/security-audit/helpers/finder_runs.py`, which also reports
  whether each run is working, idle, crashed, or ended without a complete
  answer, and why: an error event, a refusal, or a step that needed
  approval. It takes the answer from an answer file, from the last `result`
  event (`--stream-result`), from Grok's `text` events (`--grok-result`), or
  from the whole output (`--stdout-result`).
- Writes one self-contained HTML report with no script into
  `.security-audit/<date>-<commit>/report.html`, from
  `skills/security-audit/references/report-template.html`. The folder holds
  a `.gitignore` file so that git ignores it.
  `skills/security-audit/helpers/report_tools.py` colours the code blocks,
  fills the navigation and the pictures from labels on each finding, and
  checks the page and every code quote. Next to the page it writes
  `report.sarif` (SARIF 2.1.0, for GitHub code scanning). The skill never
  uploads it.
- Never opens a secret file and never prints a secret value. Offers three
  scanner tools and never installs one.

**Callers:**
- None currently — this skill is user-invoked only

