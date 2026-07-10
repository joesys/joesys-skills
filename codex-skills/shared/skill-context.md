# Shared Skill Context Infrastructure

Reference file for **every skill** in this collection. Read this in your earliest phase (before dispatching agents or performing analysis) to load user preferences that shape your behavior.

---

## Why This Exists

Different people working on the same repository have different preferences — how they like explanations, what severity levels matter, whether they prefer concise or detailed output. Rather than each skill guessing or asking from scratch, this system captures preferences once and shares them across all skills.

## File Locations

All preference files live under `.codex/skill-context/` in the project root. This directory is per-user (each collaborator may have their own via `.gitignore`) and per-project.

```
.codex/skill-context/
├── preferences.md          # Shared preferences (every skill reads this)
├── codebase-audit.md       # Skill-specific preferences
├── explain.md              # Skill-specific preferences
├── codereview.md          # Skill-specific preferences (also used by quick-review)
├── ss.md                   # Skill-specific preferences
└── ...                     # One file per skill that needs customization
```

**Shared preference files:** Some skills share — for example, `quick-review` reads `codereview.md` rather than maintaining its own file, since both share the review domain (severity focus, priority domains, etc.).

**`.gitignore` note:** Because preferences are personal, add `.codex/skill-context/` to `.gitignore` unless the team explicitly wants shared preferences.

---

## Shared Preferences File Format

`preferences.md` captures cross-cutting preferences that benefit every skill:

```markdown
# Skill Preferences

Last updated: {DATE}

## Communication Style
- **Detail level:** {concise | balanced | detailed}
- **Tone:** {casual | professional | technical}
- **Formatting:** {prose | tables-and-lists | mixed}

## Explanation Preferences
- **Style:** {analogy-heavy | technical-precise | visual-with-diagrams | example-driven}
- **Assumed knowledge:** {beginner | intermediate | advanced | expert}
- **Domain experience:** {free text — e.g., "senior backend, new to frontend, familiar with DevOps"}

## Project Context
- **Project phase:** {prototype | mvp | active-growth | mature | maintenance}
- **Team size:** {solo | 2-5 | 6-15 | 16+}
- **Deployment cadence:** {continuous | weekly | monthly | release-based | not-yet}
- **Business priority:** {speed-to-market | reliability | compliance | cost-reduction | feature-completeness}

## Additional Notes
{free text — anything else the user wants skills to know}
```

## Skill-Specific Preferences File Format

Each `<skill-name>.md` file captures preferences unique to that skill:

```markdown
# {Skill Name} Preferences

Last updated: {DATE}

## Preferences
{skill-specific key-value pairs or free text}
```

Examples of skill-specific preferences:

| Skill | Example Preferences |
|---|---|
| `explain` | "Start with entry points", "Always include dependency graphs", "Top-down preferred" |
| `codereview` | "Care most about security and correctness", "Skip P3/P4 findings", "Always show before/after" |
| `codebase-audit` | Project phase, team size, known trade-offs |
| `commit` | "Keep messages under 72 chars", "Always include scope" |
| `devlog` | "Write for a technical blog audience", "Include code snippets" |
| `export` | "Default to dark theme", "Prefer PDF over HTML" |

---

## Context Loading Protocol

Every skill MUST follow this protocol in its earliest phase. Skills fall into three categories for handling missing preferences:

| Category | Skills | First-contact behavior |
|---|---|---|
| **Full interview** | `$explain`, `$codereview`, `$quick-review`, `$codebase-audit`, `$devlog`, `$retrospective`, `$ai-council` | Invoke `$preferences` (streamlined) if no shared preferences exist. |
| **Silent defaults** | `$commit`, `$export`, `$ss`, `$readability-review` | Load preferences if present; use sensible defaults otherwise. **MUST NOT interrupt** the workflow with an interview — these are fast, transactional operations. |
| **Minimal load** | `$claude`, `$codex`, `$antigravity` | Load preferences if present to shape critical-evaluation output. **MUST NOT interview** — delegation is a pass-through. |

### Step 1: Check for Shared Preferences

Read `.codex/skill-context/preferences.md`.

- **Found:** Load and proceed.
- **Not found, "full interview" skill:** This is the user's first interaction with any skill in this project. Invoke `$preferences` before continuing your own workflow. After `$preferences` completes, re-read the file and proceed.
- **Not found, "silent defaults" or "minimal load" skill:** Proceed with sensible defaults.

### Step 2: Check for Skill-Specific Preferences

Read `.codex/skill-context/<your-skill-name>.md`.

- **Found:** Load and apply alongside shared preferences.
- **Not found:** Either ask 1–2 skill-specific questions inline (only if your skill genuinely benefits from customization), or proceed with sensible defaults. If you ask, save the answers to `.codex/skill-context/<your-skill-name>.md`.

### Step 3: Proceed with Your Workflow

Pass relevant preferences to subagents, analysis phases, and output formatting. **MUST NOT re-ask** questions the user has already answered.

---

## How to Apply Preferences

Preferences are guidance, not rigid rules. Apply with judgment:

| Preference | How It Shapes Behavior |
|---|---|
| Detail level: concise | Shorter reports, skip minor findings, focus on top issues |
| Detail level: detailed | Include background context, explain reasoning, show alternatives |
| Style: analogy-heavy | Frame technical concepts via real-world parallels |
| Style: visual-with-diagrams | Include more ASCII diagrams, flow charts, dependency graphs |
| Assumed knowledge: beginner | Define terms, explain why not just what |
| Assumed knowledge: expert | Skip basics, focus on non-obvious insights, use precise terminology |
| Project phase: prototype | Lighter on process, heavier on "what to invest in first" |
| Project phase: mature | Heavier on consistency, modularity, onboarding friction |
| Business priority: speed-to-market | Frame recommendations as "do this now" vs. "before scaling" |
| Business priority: reliability | Emphasize testing, error handling, resilience patterns |

When passing preferences to subagents, include only the **relevant subset** — not the entire file. A review subagent needs severity preferences; an explanation subagent needs style and knowledge level.

---

## Discipline

- **MUST NOT proactively re-ask** "has anything changed?" on every run. The `$preferences` skill handles updates — users invoke it when they want to change something.
- **MAY mention discrepancy once** if a skill notices a significant mismatch (e.g., preferences say "solo" but git log shows 12 contributors): "Your preferences say solo, but I see multiple contributors — you can run `$preferences` to update."
- **MUST treat preferences as guidance, not laws.** A "concise" preference does not authorize stripping critical security findings from a review.

---

## Interface Contract

**Invocation:** `$preferences [skill-name]`

- `$preferences` — set or update shared preferences
- `$preferences explain` — set or update explain-specific preferences
- `$preferences show` — display current preferences without changing them
- `$preferences reset` — clear all preferences and start fresh

**File contract:**
- Shared preferences always at `.codex/skill-context/preferences.md`
- Skill-specific at `.codex/skill-context/<skill-name>.md`
- Files are plain markdown, human-readable and hand-editable
- Skills MUST handle missing files gracefully (first-run case)

**Callers:** All skills in this collection (see individual SKILL.md files for integration points).
