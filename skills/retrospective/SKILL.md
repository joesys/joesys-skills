---
name: retrospective
version: "1.0.0"
description: "Use when the user invokes /retrospective to run a structured retrospective — mines git history, conversations, code quality, plans, and tests, then facilitates topic-by-topic discussion with the human to produce action items, process improvements, and a narrative summary."
---

# Retrospective Skill

Run a structured retrospective facilitated by AI, interleaved with human check-ins at every phase. Dispatch 5 parallel channel agents — each mining a different data source (git history, conversations, code quality, planning docs, tests) — to build a comprehensive digest. Derive discussion topics from the data, walk through them with the human, and produce three output layers: action items, process improvements, and skill improvements. Finish with a readable narrative written by a fresh-context agent.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Guiding principles, all 5 channel agent prompts, narrative agent prompt | Before dispatching agents in Phase 1 or Phase 4 |
| `references/output-formats.md` | Templates for all output files (carry-forward, digest, discussions, summary, action items, improvements, narrative) | Before writing output files in Phase 3 |

## Invocation

Parse the user's `/retrospective` arguments:

| Invocation | Mode | Description |
|---|---|---|
| `/retrospective` | Chain (default) | From last retro to now (or beginning if first) |
| `/retrospective --since 2026-03-15` | Date-based | From a specific date to now |
| `/retrospective --since v1.0` | Tag-based | From a git tag to now |
| `/retrospective --since v1.0..v1.1` | Tag range | Between two tags |
| `/retrospective --output docs/sprints/3/` | Output override | Combinable with any mode |
| `/retrospective continue` | Resume | Resume an interrupted retro |

The `--since` parameter accepts dates, natural language (`yesterday`, `2 weeks ago`), git tags, tag ranges, and `beginning` (from first commit).

### Time Boundary Resolution

1. If `--since` is provided, use it directly
2. If no `--since`, scan `docs/retros/` for the most recent retro directory. Chain from its end date.
3. If no previous retro exists, ask the human: **From beginning** or **Specify a start point**
4. End boundary is always HEAD / current date

### Output Directory

Default: `docs/retros/YYYY-MM-DD/` (retro execution date). Override with `--output <path>`.

---

## Phase 0: Carry-Forward Check

Closes the feedback loop from the previous retro. Read `references/output-formats.md` for the carry-forward format.

**First retro?** Skip silently — no output file, no message.

**Otherwise:** Read the most recent previous retro's `03-action-items.md` and `03-retro-summary.md` (Top Takeaways only). For each action item, determine status:
- **Completed** — cite evidence (commit hash, file path, PR link)
- **Incomplete** — carry forward with original category
- **Retired** — note the reason

Items carried forward for 3+ consecutive retros get a `[STALE]` flag — forces a decision: do it, retire it, or escalate.

Save to `<retro-dir>/00-carry-forward.md`. No checkpoint pause — feeds directly into Phase 1.

---

## Phase 1: Mine via Parallel Channel Agents

Dispatch **5 subagents simultaneously** — all 5 in a single response. Each uses `model: "opus"`. Read `references/agent-prompts.md` for full prompt templates and guiding principles.

### Agent Roster

| # | Channel | Data Source | Key Focus |
|---|---|---|---|
| 1 | Git History | `git log`, `git diff`, `git shortlog` | Timeline, velocity, hotspots, pivots |
| 2 | Conversation History | `~/.claude/projects/{project}/*.jsonl` | Corrections, friction, AI failures |
| 3 | Code Quality Delta | File structure, git diffs, audit metrics | What got better/worse structurally |
| 4 | Planning vs. Reality | `docs/superpowers/plans/`, `docs/superpowers/specs/` | Completed, abandoned, unplanned work |
| 5 | Testing & Reliability | Test files, test runner, git diffs | Test health, coverage gaps, flakiness |

### Output Assembly

After all 5 agents return, assemble findings into `<retro-dir>/01-digest.md` with a facilitator preamble (period, key metrics, narrative arc).

### Topic Derivation

Derive **4-7 discussion topics** from the channel findings:
1. Scan all findings for recurring themes, tensions, high-signal observations
2. Group related findings into candidates
3. Rank by signal strength (evidence count, number of channels that flagged it)
4. Drop candidates with thin evidence
5. Merge overlapping candidates

Each topic needs: a descriptive name and a one-line justification citing which channels surfaced evidence.

### Human Check-In

Present the narrative arc, key metrics, and proposed topic list. Ask using `AskUserQuestion`:
- **Proceed** — "Topics look good, start the discussion"
- **Adjust** — "I want to add/remove/reorder topics"
- **Add context** — "I have observations to include before we start"

---

## Phase 2: Topic-by-Topic Discussion

The core of the retrospective — raw findings become actionable insights through human judgment.

### Initialize

Create `<retro-dir>/02-topic-discussions.md` with YAML status header (`status: in-progress`, `topics_completed: 0`). Read `references/output-formats.md` for the format.

### For Each Topic

1. **Present findings** — synthesize what channel agents found. Include:
   - **What the data shows** — facts with specific evidence
   - **Patterns and tensions** — what's interesting, contradictory, or surprising
   - **Blind spots** — what only the human knows

2. **Ask the human to react** using `AskUserQuestion`:
   - **Agree** / **Correct something** / **Add perspective** / **Skip**

3. **Capture outcome** — key insights, human's perspective, Start/Stop/Continue items

4. **Save immediately** — append to `02-topic-discussions.md`, update YAML header

5. **Context management** — after saving, retain only Start/Stop/Continue + one-sentence insight. Full discussion is on disk.

### Human Corrections Are Highest Signal

When the human corrects the analysis, tag with `**[Human Correction]**`. These reveal where the AI's model was wrong — the most valuable data in the entire retro. Surface prominently in Phase 3 summary.

---

## Phase 3: Synthesize & Deliver

Re-reads only `02-topic-discussions.md` — everything upstream is distilled there. Read `references/output-formats.md` for all output templates.

### 3a: Retrospective Summary → `03-retro-summary.md`

Consolidate topic discussions: metrics, narrative arc, human corrections, topic insights, top 3-5 takeaways.

### 3b: Action Items → `03-action-items.md`

Extract Start/Stop/Continue items into actionable changes grouped by category with priorities. Every item must be **specific and verifiable**.

### 3c: Improvement Proposals → `03-improvements.md`

Draft process and skill improvement proposals grounded in retro evidence.

### Human Review Gate

Present improvement proposals **one by one** using `AskUserQuestion`: Approve / Reject / Modify. Update status in the file. **Do NOT apply changes without explicit approval.**

---

## Phase 4: Retro Narrative

**Always runs in a fresh context agent** (`subagent_type: "general-purpose"`, `model: "opus"`). Read `references/agent-prompts.md` for the narrative agent prompt and writing rules.

The agent receives `03-retro-summary.md` and `02-topic-discussions.md`. Output: `<retro-dir>/04-retro-narrative.md` — engaging prose, not reformatted summary.

---

## Final Steps

After Phase 4 completes:

1. **Devlog scrap** — auto-invoke `/devlog scrap --from-context` with the retro's most surprising insight. Skip silently if skill unavailable.

2. **Apply approved improvements** — implement any approved proposals from Phase 3c. Each change gets its own commit via `/commit` (or standard Conventional Commits if unavailable).

3. **Commit retro artifacts** — commit all output files using Conventional Commits with the structured body format:
   ```
   docs(retro): add retrospective for <date range>

   Structured retrospective covering [N] topics with [N] action items.

   [--- Changes ---]

   - docs/retros/YYYY-MM-DD/: retrospective output files (carry-forward, digest, discussions, summary, action items, improvements, narrative)

   [--- AI Review (<model name>) ---]

   <Brief assessment of the retrospective quality.>
   ```

4. **End message:** `Retrospective complete. Artifacts saved to <retro-dir>/.`

---

## Session Resumption

**Invocation:** `/retrospective continue`

### Recovery Procedure

1. Find today's retro directory in `docs/retros/`, or the most recent incomplete one (missing `04-retro-narrative.md`).

2. File inventory determines resume point:

| Files Found | Resume Point |
|---|---|
| No retro directory | Start from Phase 0 |
| `00-carry-forward.md` exists | Phase 1 |
| `01-digest.md` exists | Phase 2 |
| `02-topic-discussions.md` exists | Check YAML status (see below) |
| `03-retro-summary.md` exists | Phase 4 |
| `04-retro-narrative.md` exists | Final Steps only |

3. For Phase 2 resume: read YAML front matter — `status: complete` → Phase 3; `topics_completed: N` → resume at topic N+1.

4. **What to read on resume:**
   - Phase 1 resume: `00-carry-forward.md` + time boundary from directory name
   - Phase 2 resume: YAML header + topic list from digest + next topic's channel data only
   - Phase 3 resume: `02-topic-discussions.md` only
   - Phase 4 resume: `03-retro-summary.md` + `02-topic-discussions.md` (fresh agent)

5. **Do NOT re-read** source files, git logs, or session transcripts already synthesized into the digest.

---

## Red Flags

Watch for these signs during the retrospective:

| Sign | Problem | Fix |
|---|---|---|
| All channels agree | Manufactured consensus | Re-examine for glossed-over tensions |
| No human corrections captured | Mining missed them, or unusually smooth period | Ask directly: "Were there moments where you corrected the AI?" |
| Vague action items | "Improve testing" is not an action | Rewrite with specifics |
| Ungrounded proposals | Must reference retro evidence | Go back and cite findings |
| Skipping human reaction | Human perspective is the most valuable input | Always use `AskUserQuestion` |
| Topic list feels templated | Topics emerge from data, not a template | Re-examine channel findings |
| Narrative reads like reformatted summary | Should be engaging prose | Fresh-context agent prevents this |
| Phase 3 contradicts Phase 2 | Synthesis must faithfully represent discussions | Re-read and fix contradictions |
| Empty topics | Drop topics with no evidence | Fewer, richer topics > padding |

---

## Context Management

| Phase | Budget / Strategy |
|---|---|
| Phase 1 agents | ~4,000 lines each. Prioritize breadth. |
| Phase 2 discussions | After saving to disk, retain only Start/Stop/Continue + one-sentence insight. |
| Phase 3 synthesis | Reads only `02-topic-discussions.md`. Everything upstream is distilled. |
| Phase 4 narrative | Fresh context agent. Never in same context as Phases 0-3. |
| Incremental saves | Every topic saved immediately — enables both context management and session resumption. |
