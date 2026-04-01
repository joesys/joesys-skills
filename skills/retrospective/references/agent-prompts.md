# Retrospective — Agent Prompts

Full prompt templates for the 5 channel agents (Phase 1) and the narrative agent (Phase 4). Each channel agent receives the retro time boundary, carry-forward context, and the Guiding Principles block.

## Table of Contents

- [Guiding Principles](#guiding-principles)
- [Agent 1: Git History](#agent-1-git-history)
- [Agent 2: Conversation History](#agent-2-conversation-history)
- [Agent 3: Code Quality Delta](#agent-3-code-quality-delta)
- [Agent 4: Planning vs. Reality](#agent-4-planning-vs-reality)
- [Agent 5: Testing & Reliability](#agent-5-testing--reliability)
- [Phase 4: Narrative Agent](#phase-4-narrative-agent)

---

## Guiding Principles

Prepend to every channel agent prompt:

1. **Evidence over guesswork.** Every claim must reference a specific commit, conversation exchange, file, or timestamp. No vague assertions.
2. **Flag uncertainty.** Distinguish what definitely happened vs. what seems likely vs. what is unclear. Uncertainty is valid output — say "unclear" rather than speculate.
3. **Focus on friction and surprise.** The goal is to find moments where something didn't go as expected, where the developer changed direction, or where a process broke down. Routine work is not interesting for a retrospective.
4. **Quantify when possible.** Prefer "12 commits touched auth/ in 3 days" over "lots of churn in the auth module."
5. **Infer reasoning, but mark it.** When you infer *why* something happened, explicitly label it: "Likely because..." or "This suggests..."

### Context Budgets

Each agent operates within a **~4,000 line read budget** to prevent context exhaustion. Prioritize breadth within the budget rather than exhaustive depth on one area.

---

## Agent 1: Git History

```
<GUIDING_PRINCIPLES>

You are analyzing git history for a retrospective. Your job is to extract the timeline, patterns, and notable events from the commit history.

## Instructions
1. Analyze the git history within the specified time boundary.
2. If commit messages follow Conventional Commits with structured bodies (intent paragraph, changes changelog, AI review), mine the intent paragraphs and AI review sections — they contain reasoning and critical assessment.
3. Stay within the ~4,000 line read budget.

## Time Boundary
<START_REF> to <END_REF>

## Commands to Run
- `git log --oneline --since="<start>" --until="<end>"` for the full timeline
- `git shortlog -sn --since="<start>" --until="<end>"` for contributor breakdown
- `git diff --stat <start-ref>...<end-ref>` for overall change volume (if refs are available)
- `git log --diff-filter=A --name-only --since="<start>"` for new files
- `git log --diff-filter=D --name-only --since="<start>"` for deleted files

## Carry-Forward Context (if provided)
<CARRY_FORWARD_SUMMARY or "None — this is the first retrospective.">

## Extract and Organize

- **Timeline**: chronological narrative of what happened (first X, then Y, finally Z)
- **Velocity metrics**: total commits, files changed, insertions/deletions, new files created, files deleted
- **Hotspots**: files/directories with the most churn (modified in 3+ commits)
- **Commit patterns**: burst vs. steady work, time-of-day patterns if visible, large commits that may indicate code dumps
- **Notable commits**: commits that introduced new approaches, reverted work, or stand out as pivots
- **Dependency changes**: new dependencies added, removed, or upgraded (look at lockfile/manifest changes)

## Output Format

Return structured markdown with clear section headers for each category above. Include specific commit hashes for notable items.
```

---

## Agent 2: Conversation History

```
<GUIDING_PRINCIPLES>

You are reading Claude Code conversation transcripts to find moments of human correction, decision-making, and friction for a retrospective.

## Instructions
1. Read the specified JSONL session files.
2. Focus on user and assistant messages (type: "user" and "assistant"). Skip tool results, file-history-snapshots, and progress messages — they are bulk data that obscures the thinking.
3. Stay within the ~4,000 line read budget. Scan all sessions but read deeply only the most signal-rich exchanges.

## Session Resolution
Determine the active project's session files:
1. The project directory is derived from the current working directory with path separators replaced by `--` (e.g., `D:\joesys\Projects\my-project` becomes `D--joesys-Projects-my-project`).
2. Session JSONL files are at `~/.claude/projects/<project-dir>/<sessionId>.jsonl`
3. Filter sessions to those with timestamps within the retro time boundary. Check the first entry's `timestamp` field in each JSONL file.

## Time Boundary
<START_DATE> to <END_DATE>

## What to Look For

- **Human corrections**: moments where the user said "no", "not that", "actually", "stop", or redirected the AI — these reveal what the human knew that the AI didn't
- **Pivots**: points where the conversation changed direction — the user abandoned one approach for another
- **Repeated friction**: the same kind of problem or miscommunication happening across multiple sessions
- **AI failures**: questions the AI couldn't answer, wrong suggestions that had to be corrected, hallucinated solutions
- **Workflow bottlenecks**: long conversations that should have been short, indicating process friction
- **Successful patterns**: approaches that worked well and should be continued

## Output Format

Return structured markdown with:
- Summary statistics: sessions analyzed, total exchanges, correction count
- Highlighted key exchanges (quote the actual messages, attributed to "Developer" and "AI")
- Patterns observed across sessions (not just individual moments)
- Specific friction points with session references
```

---

## Agent 3: Code Quality Delta

```
<GUIDING_PRINCIPLES>

You are analyzing how the codebase's structural quality changed during the retro period.

## Instructions
1. Compare the codebase structure at the start vs. end of the retro period.
2. Focus on structural indicators, not code content.
3. Stay within the ~4,000 line read budget.

## Time Boundary
<START_REF> to <END_REF>

## Baseline (if available)
<CODEBASE_AUDIT_METRICS_JSON or "No previous codebase audit available — estimate from git history.">

If a `/codebase-audit` metrics.json exists from before the retro period, use it as a baseline. Otherwise, estimate the delta from git history (files added/removed, test files added/removed).

## Analyze

- **File count delta**: source files, test files, config files — created vs. deleted
- **Test-to-production ratio**: ratio of test code added vs. production code added
- **Complexity indicators**: large files that grew larger, new files that are already large (>300 lines), deeply nested directory structures created
- **Dependency changes**: new dependencies added to manifests/lockfiles, dependencies removed or upgraded
- **Tech debt signals**: TODO/FIXME/HACK comments added vs. removed (use `git log -p --since="<start>" | grep -c "^\+.*TODO\|FIXME\|HACK"` and similar for removals)
- **What got better**: tests added, large files split, dead code removed, types added
- **What got worse**: new dependencies without justification, growing god files, test coverage gaps in high-churn areas

## Output Format

Return structured markdown with quantified deltas where possible. Use "+N" / "-N" notation for changes.
```

---

## Agent 4: Planning vs. Reality

```
<GUIDING_PRINCIPLES>

You are comparing what was planned against what was actually delivered during the retro period.

## Instructions
1. Read plan and spec documents that fall within the retro period.
2. Cross-reference against the git history to determine what was actually implemented.
3. Stay within the ~4,000 line read budget.

## Time Boundary
<START_DATE> to <END_DATE>

## Where to Find Plans
Check these locations for plan and spec documents (date-filtered to the retro period):
- `docs/superpowers/plans/` — implementation plans
- `docs/superpowers/specs/` — design specs
- Any other planning directories discovered in the project

Use file modification dates and git log to filter to the retro period.

## Analyze

- **Plans completed**: which plans were fully implemented (all checkboxes checked or equivalent)
- **Plans partially completed**: which plans were started but not finished — what remains
- **Plans abandoned**: which plans were created but never started or explicitly abandoned
- **Unplanned work**: significant commits or features that don't trace to any plan — these represent reactive or emergent work
- **Scope drift**: where implementation diverged from the plan — features added, features cut, approach changed mid-implementation
- **Estimate accuracy**: if plans have time estimates, compare against actual (infer from commit timestamps)

## Output Format

Return structured markdown. For each plan found, state: title, status (complete/partial/abandoned), and notable divergences. End with an "Unplanned Work" section listing significant work that wasn't in any plan.
```

---

## Agent 5: Testing & Reliability

```
<GUIDING_PRINCIPLES>

You are analyzing the health and trajectory of the project's test suite during the retro period.

## Instructions
1. Analyze test file changes during the retro period.
2. If possible, run the test suite to get current pass/fail status.
3. Stay within the ~4,000 line read budget.

## Time Boundary
<START_REF> to <END_REF>

## Analyze

- **Test suite status**: attempt to run the project's test suite. Common commands to try:
  - `npm test`, `npx jest`, `npx vitest` (JavaScript/TypeScript)
  - `pytest`, `python -m pytest` (Python)
  - `go test ./...` (Go)
  - `cargo test` (Rust)
  - `dotnet test` (C#)
  If the test command is documented in `package.json`, `Makefile`, `pyproject.toml`, or similar, use that. If tests can't be run, note why and proceed with static analysis.
- **Test file changes**: new test files created, test files modified, test files deleted during the period
- **Test-to-production ratio**: for files changed in the period, how many had corresponding test changes
- **Flaky test indicators**: test files with high churn (modified 3+ times), tests that were added then quickly modified
- **Coverage gaps**: production files with high churn during the period that have no corresponding test file
- **Testing patterns**: what testing conventions emerged or were followed (naming, structure, assertion style)

## Output Format

Return structured markdown with:
- Current test suite status (if runnable): total, passing, failing, skipped
- Test delta during retro period: tests added, modified, deleted
- Coverage gap analysis: high-churn production files without tests
- Notable testing patterns or anti-patterns observed
```

---

## Phase 4: Narrative Agent

This phase always runs in a fresh context agent (`subagent_type: "general-purpose"`, `model: "opus"`). The analytical phases load the context with structured data — creative writing quality degrades in that environment.

### Agent Receives

1. `<retro-dir>/03-retro-summary.md` — the synthesized summary
2. `<retro-dir>/02-topic-discussions.md` — the raw discussions for detail and texture
3. The writing rules below (include verbatim)

### Narrative Prompt

```
You are writing a retrospective narrative — a readable, engaging account of a development period. You are NOT reformatting a summary into prose. You are telling the story of what happened.

## Source Material
Read the two files provided:
1. The retrospective summary — for the arc, metrics, and takeaways
2. The topic discussions — for the detail, tensions, and human corrections

## Writing Rules

- Write in third person or neutral voice — no fictional characters, no personas
- Short paragraphs, punchy sentences — like a good blog post, not a report
- Ground every point in specifics from the retro — no generic advice or platitudes
- Highlight tension and surprise over agreement and success — friction is interesting, smooth sailing is not
- Human corrections and judgment calls get prominent placement — these are the moments where the human's expertise was most visible
- Open with the narrative arc — set the scene for what this period was about
- End with forward tension — what's the challenge going forward? Don't tie a neat bow.
- Target length: 500-1000 words
- Do NOT include headers, bullet points, or structured formatting — this is prose

## Save To
<RETRO_DIR>/04-retro-narrative.md
```
