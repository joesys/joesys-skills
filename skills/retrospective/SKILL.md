---
name: retrospective
description: "Use when the user invokes /retrospective to run a structured retrospective — mines git history, conversations, code quality, plans, and tests, then facilitates topic-by-topic discussion with the human to produce action items, process improvements, and a narrative summary."
---

# Retrospective Skill

Run a structured retrospective facilitated by AI, interleaved with human check-ins at every phase. Dispatch 5 parallel channel agents — each mining a different data source (git history, conversations, code quality, planning docs, tests) — to build a comprehensive digest. Derive discussion topics from the data, walk through them with the human, and produce three output layers: action items, process improvements, and skill improvements. Finish with a readable narrative written by a fresh-context agent.

## Invocation

Parse the user's `/retrospective` arguments to determine mode and time boundary:

| Invocation | Mode | Description |
|---|---|---|
| `/retrospective` | Chain (default) | From last retro to now (or beginning if first) |
| `/retrospective --since 2026-03-15` | Date-based | From a specific date to now |
| `/retrospective --since v1.0` | Tag-based | From a git tag to now |
| `/retrospective --since v1.0..v1.1` | Tag range | Between two tags |
| `/retrospective --output docs/sprints/3/` | Output override | Combinable with any mode |
| `/retrospective continue` | Resume | Resume an interrupted retro |

Arguments are combinable. Examples:
- `/retrospective --since v2.0 --output docs/releases/v2.1/retro/` — retro from tag with custom output
- `/retrospective --since "2 weeks ago"` — natural language date

The `--since` parameter accepts dates (`2026-03-15`), natural language (`yesterday`, `2 weeks ago`), git tags (`v1.0`), tag ranges (`v1.0..v1.1`), and the special value `beginning` (from first commit).

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

### Time Boundary Resolution

1. If `--since` is provided, use it directly
2. If no `--since`, scan `docs/retros/` for existing retro directories (sorted by date). If found, chain from the most recent retro's date.
3. If no previous retro exists, ask the human:

   Use `AskUserQuestion`:
   - **From beginning** — "Run from the first commit (`<first commit date>`)"
   - **Specify a start point** — "I'll provide a date, tag, or commit"

4. If a `--since` value is ambiguous (could be a branch name or a date), ask.

The **end boundary** is always HEAD / current date.

### Output Directory

Default: `docs/retros/YYYY-MM-DD/` where the date is the retro execution date.

If `--output` is specified, use that path instead. Create the directory if it doesn't exist.

### Previous Retro Detection

To find the most recent previous retro:

```bash
ls -d docs/retros/*/  # list retro directories, sorted by name (dates sort naturally)
```

Take the last entry. Read its `03-retro-summary.md` to extract the period end date — this becomes the start boundary for the current retro.

---

## Phase 0: Carry-Forward Check

Before mining the current period, check whether the previous retro's action items were completed. This closes the feedback loop — without it, action items are write-only documents nobody reads.

**First retro?** If no previous retro directory exists in `docs/retros/`, skip this phase silently. No output file, no message.

**Otherwise:** Read the most recent previous retro's output directly (no agent spawn — these are small files):
- `<previous-retro-dir>/03-action-items.md`
- `<previous-retro-dir>/03-retro-summary.md` (Top Takeaways section only)

**For each action item, determine status:**
- **Completed** — evidence exists (committed code, updated config, merged PR). Cite the evidence with commit hash or file path.
- **Incomplete** — not done or partially done. Carry forward with its original category.
- **Retired** — no longer relevant. Note the reason.

**Staleness rule:** Items carried forward for 3+ consecutive retros get a `[STALE]` flag. Stale items force a decision: do it, retire it, or escalate to the human.

**Chain property:** Each retro carries forward from the immediately previous retro only. The previous retro already accumulated older items, so the chain is implicit — no need to walk the entire history.

**Output:** Save to `<retro-dir>/00-carry-forward.md`

**No checkpoint pause** — carry-forward is informational. Incomplete items and staleness flags feed directly into Phase 1 mining as additional context.

### Carry-Forward Format

```markdown
# Carry-Forward from <previous retro date>

## Completed Items
- [x] [Item] — [Evidence: commit hash, file path, or PR link]

## Incomplete Items

### [Category from original action items]
- [ ] [Item] — [Why incomplete]

## Retired Items
- [Item] — [Reason for retirement]

## Staleness Flags
- [STALE] [Item] — carried since <date> (3+ retros)

## Top Takeaways Still Relevant
- [From previous retro's top takeaways — which still apply?]
```

### Edge Cases
- **Incomplete previous retro:** If the previous retro directory exists but is missing `03-action-items.md`, warn: "Previous retro appears incomplete — no action items file found. Proceeding without carry-forward." Then skip to Phase 1.
- **Irrelevant items:** Items that no longer apply (e.g., related to a removed feature) should be retired with a reason, not silently dropped.

---

## Phase 1: Mine via Parallel Channel Agents

Dispatch **5 subagents simultaneously** via the Agent tool — all 5 in a single response (5 parallel Agent tool calls). Each agent mines a specific data source within the retro time boundary.

**IMPORTANT:** Every Agent tool call **must** use `model: "opus"` to ensure high-quality analysis.

Each subagent receives:
- The retro time boundary (start ref/date → end ref/date)
- The carry-forward findings from Phase 0 (if any)
- The Guiding Principles block (prepended to every prompt)
- Its specific mining instructions

### Guiding Principles (included in every subagent prompt)

1. **Evidence over guesswork.** Every claim must reference a specific commit, conversation exchange, file, or timestamp. No vague assertions.
2. **Flag uncertainty.** Distinguish what definitely happened vs. what seems likely vs. what is unclear. Uncertainty is valid output — say "unclear" rather than speculate.
3. **Focus on friction and surprise.** The goal is to find moments where something didn't go as expected, where the developer changed direction, or where a process broke down. Routine work is not interesting for a retrospective.
4. **Quantify when possible.** Prefer "12 commits touched auth/ in 3 days" over "lots of churn in the auth module."
5. **Infer reasoning, but mark it.** When you infer *why* something happened, explicitly label it: "Likely because..." or "This suggests..."

### Context Budgets

Each agent operates within a **~4,000 line read budget** to prevent context exhaustion. The budget guides how deep to go — agents should prioritize breadth of coverage within the budget rather than exhaustive depth on one area.

### Agent 1: Git History

~~~
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
~~~

### Agent 2: Conversation History

~~~
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
~~~

### Agent 3: Code Quality Delta

~~~
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
~~~

### Agent 4: Planning vs. Reality

~~~
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
~~~

### Agent 5: Testing & Reliability

~~~
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
~~~

### Output Assembly

After all 5 agents return, the facilitator (main agent) assembles their findings into a single consolidated file: `<retro-dir>/01-digest.md`

The digest preserves each channel's findings under its own heading, with a facilitator-written preamble that includes:
- **Period**: start → end (with dates)
- **Key metrics**: commits, files changed, tests delta (pulled from channel findings)
- **Narrative arc**: one-sentence story of the period ("from X to Y")

### Topic Derivation

After assembling the digest, **derive 4-7 discussion topics** from the channel findings. Topics are emergent from the data — not from a fixed template.

**How to derive topics:**
1. Scan all channel findings for recurring themes, tensions, and high-signal observations
2. Group related findings into candidate topics
3. Rank candidates by signal strength — how much evidence supports the topic, how many channels flagged it
4. Drop candidates with thin evidence (only one channel, one data point)
5. Merge overlapping candidates into a single topic
6. Aim for 4-7 topics — enough to cover the important themes, few enough to discuss each meaningfully

**Each topic needs:**
- A descriptive name (e.g., "Testing Gaps in High-Churn Code", "AI Workflow Friction", "Scope Drift from Original Plan")
- A one-line justification citing which channels surfaced evidence for it

### Human Check-In

Present to the human:
- The narrative arc
- Key metrics (commits, files, tests delta)
- The proposed topic list with one-line justifications

Ask using `AskUserQuestion`:
- **Proceed with these topics** — "Topics look good, start the discussion"
- **Adjust topics** — "I want to add/remove/reorder topics"
- **Add context** — "I have observations to include before we start"

If the human adjusts topics, update the list accordingly before proceeding to Phase 2.

---

## Phase 2: Topic-by-Topic Discussion with Human Interleave

This is the core of the retrospective — where raw findings become actionable insights through human judgment.

### Step 1: Initialize Discussion File

Create `<retro-dir>/02-topic-discussions.md` with a YAML status header:

```yaml
---
status: in-progress
topics_completed: 0
topics_total: <N>
---

# Retrospective — Topic Discussions
```

### Step 2: For Each Topic

Process topics in order. For each topic:

1. **Present findings.** Synthesize what the channel agents found about this topic. Do not dump raw data — the facilitator interprets and connects the findings into a coherent picture:
   - **What the data shows** — facts from the relevant channels, with specific evidence (commit hashes, session references, file paths, metrics)
   - **Patterns and tensions** — what's interesting, contradictory, or surprising about these findings
   - **Blind spots** — what the data can't tell us (only the human knows the context behind certain decisions)

2. **Ask the human to react** using `AskUserQuestion`:
   - **Agree** — "This captures it well"
   - **Correct something** — "The analysis missed or got something wrong"
   - **Add perspective** — "I have context that only I would know"
   - **Skip** — "Nothing interesting here, move on"

3. **Capture the discussion outcome.** After the human responds, synthesize the topic into:
   - Key insights (what we learned — 2-3 sentences)
   - Human's perspective (what the human added or corrected — if the human corrected the analysis, tag it explicitly as `**[Human Correction]**`)
   - **Start** items — things to begin doing
   - **Stop** items — things to stop doing
   - **Continue** items — things that are working

4. **Save immediately.** Append this topic's discussion to `02-topic-discussions.md` and update the YAML header (`topics_completed: N`). Do not wait until all topics are finished.

5. **Context management.** After saving a topic to disk, retain only its Start/Stop/Continue items and one-sentence key insight in working memory. The full discussion is on disk — do not keep it in context.

6. Move to the next topic.

### Human Corrections Are Highest Signal

When the human corrects the analysis ("no, that's not why we did that", "you're missing the real issue", "actually the problem was..."), these moments are the most valuable data in the entire retro. They reveal where the AI's model of the project was wrong. Tag every correction with `**[Human Correction]**` in the discussion file and surface them prominently in the Phase 3 summary.

### Topic Discussion Format

Each topic is appended to `02-topic-discussions.md` in this format:

```markdown
## N. [Topic Name]

### Channel Findings
[Synthesized findings from relevant channels — what the data shows, with specific evidence]

### Patterns & Tensions
[What's interesting, contradictory, or surprising]

### Human's Perspective
[What the human added/corrected]
**[Human Correction]** [If the human corrected the analysis, describe what was wrong and what's actually true]

### Start / Stop / Continue
- **Start:** [items]
- **Stop:** [items]
- **Continue:** [items]

---
```

When all topics are complete, update the status header to `status: complete`.

---
