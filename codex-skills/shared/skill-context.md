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
├── codereview.md           # Skill-specific preferences (also used by quick-review)
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

---

## Context Loading Protocol

Every skill follows this protocol in its earliest phase. **No skill interviews the user about preferences.** Missing files are the normal case.

### Step 1: Load Shared Preferences

Read `.codex/skill-context/preferences.md`.

- **Found:** Load it and apply it.
- **Not found:** Use sensible defaults. Do not ask the user to set preferences, and do not mention that the file is missing.

### Step 2: Load Skill-Specific Preferences

Read `.codex/skill-context/<your-skill-name>.md`.

- **Found:** Load it and apply it alongside the shared preferences.
- **Not found:** Use sensible defaults.
- A skill MAY ask a question it needs to do the current task (for example, which folder holds screenshots). It MAY offer to save the answer to `.codex/skill-context/<your-skill-name>.md` so it does not ask again.

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
| Style: visual-with-diagrams | Include more diagrams (Mermaid where the output supports it), flow charts, dependency graphs |
| Assumed knowledge: beginner | Define terms, explain why not just what |
| Assumed knowledge: expert | Skip basics, focus on non-obvious insights, use precise terminology |
| Project phase: prototype | Lighter on process, heavier on "what to invest in first" |
| Project phase: mature | Heavier on consistency, modularity, onboarding friction |
| Business priority: speed-to-market | Frame recommendations as "do this now" vs. "before scaling" |
| Business priority: reliability | Emphasize testing, error handling, resilience patterns |

When passing preferences to subagents, include only the **relevant subset** — not the entire file. A review subagent needs severity preferences; an explanation subagent needs style and knowledge level.

---

## Discipline

- **MUST NOT ask** "has anything changed?" on every run.
- **MAY mention a mismatch once** if a skill notices one (for example, preferences say "solo" but git log shows 12 contributors). Say what the file says and what you see. The user can edit the file by hand.
- **MUST treat preferences as guidance, not laws.** A "concise" preference does not authorize removing critical security findings from a review.

---

## File Contract

- Shared preferences always at `.codex/skill-context/preferences.md`
- Skill-specific at `.codex/skill-context/<skill-name>.md`
- Files are plain markdown, human-readable and hand-editable. The user creates and edits them directly.
- Skills MUST handle missing files gracefully.
