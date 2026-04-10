# Shared Skill Context Infrastructure

Reference file for all skills. Read this file during your earliest phase
(before dispatching agents or performing analysis) to load user preferences
that shape how you operate.

## Why This Exists

Different people working on the same repository have different preferences —
how they like explanations, what severity levels matter to them, whether they
prefer concise or detailed output. Rather than each skill guessing or asking
from scratch, this system captures those preferences once and shares them
across all skills in the collection.

## File Locations

All preference files live under `.claude/skill-context/` in the project root.
This directory is per-user (each collaborator may have their own via
`.gitignore`) and per-project.

```
.claude/skill-context/
├── preferences.md          # Shared preferences (all skills read this)
├── codebase-audit.md       # Skill-specific preferences
├── explain.md              # Skill-specific preferences
├── code-review.md          # Skill-specific preferences (also used by quick-review)
├── ss.md                   # Skill-specific preferences
└── ...                     # One file per skill that needs customization
```

**Note:** Some skills share preference files — for example, quick-review
reads `code-review.md` rather than maintaining its own file, since both
skills share the same review domain (severity focus, priority domains, etc.).

**`.gitignore` note:** Because preferences are personal, add
`.claude/skill-context/` to `.gitignore` unless the team explicitly wants
shared preferences.

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
| `explain` | "Start with entry points", "Always include dependency graphs", "I prefer top-down explanations" |
| `code-review` | "I care most about security and correctness", "Skip P3/P4 findings", "Always show before/after" |
| `codebase-audit` | Project phase, team size, known trade-offs (migrated from project-context.md) |
| `commit` | "Keep messages under 72 chars", "Always include scope" |
| `devlog` | "Write for a technical blog audience", "Include code snippets" |
| `export` | "Default to dark theme", "Prefer PDF over HTML" |

## Context Loading Protocol

Every skill should follow this protocol in its earliest phase. Skills fall
into three categories for how they handle missing preferences:

- **Full interview** (explain, code-review, quick-review, codebase-audit,
  devlog, retrospective, ai-council): Invoke `/preferences` if no shared
  preferences exist.
- **Silent defaults** (commit, export, ss): Load preferences if they exist,
  use sensible defaults if not. Never interrupt the workflow with an
  interview — these are fast, transactional operations.
- **Minimal load** (claude, codex, gemini): Load preferences if they exist
  to shape the critical evaluation output. No interview — delegation is
  a pass-through operation.

See individual SKILL.md files for skill-specific handling.

### Step 1: Check for Shared Preferences

```
Read .claude/skill-context/preferences.md
```

- **If found:** Load and proceed. The preferences shape your behavior (see
  "How to Apply Preferences" below).
- **If not found and your skill is in the "full interview" category:** This
  is the user's first interaction with any skill in this project. Invoke
  `/preferences` before continuing your own workflow. After `/preferences`
  completes, re-read the file and proceed.
- **If not found and your skill is "silent defaults" or "minimal load":**
  Proceed with sensible defaults.

### Step 2: Check for Skill-Specific Preferences

```
Read .claude/skill-context/<your-skill-name>.md
```

- **If found:** Load and apply alongside shared preferences.
- **If not found:** Either ask 1-2 skill-specific questions inline (if your
  skill benefits from customization), or proceed with sensible defaults.
  If you ask questions, save the answers to
  `.claude/skill-context/<your-skill-name>.md`.

### Step 3: Proceed with Your Workflow

Pass relevant preferences to subagents, analysis phases, and output
formatting. Do not re-ask questions the user has already answered.

## How to Apply Preferences

Preferences are guidance, not rigid rules. Apply them with judgment:

| Preference | How It Shapes Behavior |
|---|---|
| Detail level: concise | Shorter reports, skip minor findings, focus on top issues |
| Detail level: detailed | Include background context, explain reasoning, show alternatives |
| Style: analogy-heavy | Frame technical concepts using real-world parallels |
| Style: visual-with-diagrams | Include more ASCII diagrams, flow charts, dependency graphs |
| Assumed knowledge: beginner | Define terms, explain why not just what, link to concepts |
| Assumed knowledge: expert | Skip basics, focus on non-obvious insights, use precise terminology |
| Project phase: prototype | Lighter on process, heavier on "what to invest in first" |
| Project phase: mature | Heavier on consistency, modularity, onboarding friction |
| Business priority: speed-to-market | Frame recommendations as "do this now" vs. "before scaling" |
| Business priority: reliability | Emphasize testing, error handling, resilience patterns |

When passing preferences to subagents, include the relevant subset — not the
entire file. A review subagent needs severity preferences; an explanation
subagent needs style and knowledge level.

## Staleness & Updates

- Skills should **not** proactively ask "has anything changed?" on every run.
  That gets annoying fast.
- The `/preferences` skill handles updates — users invoke it when they want
  to change something.
- If a skill notices a significant mismatch (e.g., preferences say "solo
  developer" but git log shows 12 contributors), it may mention the
  discrepancy once: "Your preferences say solo, but I see multiple
  contributors — you can run `/preferences` to update."

## Interface Contract

**Invocation:** `/preferences [skill-name]`

- `/preferences` — set or update shared preferences
- `/preferences explain` — set or update explain-specific preferences
- `/preferences show` — display current preferences without changing them
- `/preferences reset` — clear all preferences and start fresh

**File contract:**
- Shared preferences always at `.claude/skill-context/preferences.md`
- Skill-specific at `.claude/skill-context/<skill-name>.md`
- Files are plain markdown, human-readable and hand-editable
- Skills must handle missing files gracefully (first-run case)

**Callers:** All skills in this collection (see individual SKILL.md files for
integration points).
