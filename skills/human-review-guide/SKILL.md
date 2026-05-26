---
name: human-review-guide
version: "1.0.0"
description: "Use when the user invokes /human-review-guide to generate a personalized reading guide for human review — triages changes into attention tiers (DECIDE/READ/SKIM/SKIP), analyzes decision-heavy sections, and produces a guided reading order focused on decisions requiring human judgment."
---

# Human Review Guide Skill

Generate a personalized reading guide for human review. Analyze a change set or artifact, classify every section by how much human attention it needs, then produce a guided reading order focused on decisions that require human judgment. The guide tells the reviewer what to read carefully, what to skim, and what to skip — saving time by directing attention where it matters.

The existing review skills (`/code-review`, `/quick-review`, `/readability-review`) have the AI do the review. This skill is different — it helps the *human* review more effectively.

## Out of Scope

This skill MUST NOT:
- Perform the review itself. It produces a reading guide, not findings or bug reports. Code quality, correctness, and security analysis are the domain of `/code-review` and `/quick-review`.
- Modify source code. The guide is read-only output — no fixes, no edits.
- Auto-trigger `/code-review`. When `--with-review` is used and no findings exist, prompt the user to run `/code-review` first — never invoke it automatically.
- Make final decisions for the reviewer. `DECIDE` chunks surface the decision and alternatives; the human makes the call.
- Over-classify as SKIP. When in doubt, escalate one tier up (SKIP→SKIM, SKIM→READ, READ→DECIDE). Conservative triage is a feature, not a bug.
- Inflate the decision count. Mechanical choices (variable names, formatting, import order) are not decisions. Reserve `DECIDE` for genuine trade-offs and judgment calls.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Triage agent and deep analysis agent prompt templates | Before dispatching agents in Phase 1 and Phase 2 |
| `references/output-formats.md` | Terminal markdown and HTML report format templates | Before writing output in Phase 3 |

## Invocation

Parse the user's `/human-review-guide` arguments:

| Invocation | Mode | Description |
|---|---|---|
| `/human-review-guide` | Branch diff (default) | Guide for current branch diff vs. base |
| `/human-review-guide PR#<number>` | PR review | Guide for a specific GitHub PR |
| `/human-review-guide <path>` | Artifact review | Guide for reviewing a file or directory |
| `/human-review-guide --with-review` | Enriched | Incorporate existing `/code-review` findings from this session |
| `/human-review-guide --calibrate` | Recalibrate | Re-run first-run calibration questions |

Arguments are combinable. Examples:
- `/human-review-guide --with-review` — branch diff guide enriched with `/code-review` findings
- `/human-review-guide PR#42 --with-review` — PR guide with code review findings
- `/human-review-guide docs/spec.md` — guide for reviewing a non-code artifact

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Setup

### 0.1 Load User Preferences

Read `shared/skill-context.md` for the full protocol. In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/human-review-guide.md` (if it exists) for skill-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Human Review Guide |
|---|---|
| Detail level: concise | Shorter analysis per chunk, tighter executive summary |
| Detail level: detailed | Richer alternative analysis, more consequence detail |
| Assumed knowledge: beginner | Lower SKIP threshold, explain more context in READ chunks |
| Assumed knowledge: expert | Higher SKIP threshold, focus on non-obvious decisions |
| Skill-specific: skip tolerance | Conservative / balanced / aggressive triage thresholds |
| Skill-specific: review focus | Weight triage toward specific concerns (security, architecture, etc.) |
| Skill-specific: verbosity | Concise pointers / moderate explanation / detailed rationale |

### 0.2 First-Run Calibration

If no skill-specific context exists at `.claude/skill-context/human-review-guide.md`, ask calibration questions using `AskUserQuestion`:

1. **Role/expertise** — "What's your background?" with options: Backend developer, Frontend developer, Full-stack developer, DevOps/Infra, PM/Non-technical reviewer, Other
2. **Review focus** — "What do you care most about when reviewing?" with options: Correctness & edge cases, Architecture & design decisions, Security implications, Maintainability & tech debt
3. **Verbosity preference** — "How detailed should the guide be?" with options: Concise (just pointers), Moderate (brief explanations), Detailed (full rationale)
4. **Skip tolerance** — "How aggressively should I mark things as skippable?" with options: Conservative (surface more, miss nothing), Balanced, Aggressive (only flag critical decisions)

Save answers to `.claude/skill-context/human-review-guide.md`:

```markdown
# Human Review Guide Preferences

Last updated: {DATE}

## Calibration
- **Role:** {answer}
- **Review focus:** {answer}
- **Verbosity:** {concise | moderate | detailed}
- **Skip tolerance:** {conservative | balanced | aggressive}
```

If `--calibrate` flag is set, re-run calibration even if the file exists.

### 0.3 Resolve `--with-review`

If `--with-review` is specified:

1. Check the current conversation context for `/code-review` output (look for the structured findings report with severity-grouped findings).
2. **Found:** Extract findings, noting file paths, severities, and descriptions. Hold for Phase 2 enrichment.
3. **Not found:** Display: "No `/code-review` output found in this session. Run `/code-review` first, then re-run `/human-review-guide --with-review`. Or drop `--with-review` to generate the guide without it." Exit.

### 0.4 Determine Mode

Based on the invocation arguments, set the `mode` variable:

| Argument | Mode | Chunking strategy |
|---|---|---|
| *(none)* or branch diff | `code-diff` | Per-file for ≤15 files, per-hunk for >15 files |
| `PR#<number>` | `code-diff` | Same as branch diff, using PR diff |
| `<path>` to a code file | `code-diff` | Per-hunk within the file |
| `<path>` to a non-code file | `artifact` | Per-section/heading |
| `<path>` to a directory | Mixed | Detect per-file: code files → `code-diff`, non-code → `artifact` |

The `mode` variable is passed to the agent prompts to adjust framing.
