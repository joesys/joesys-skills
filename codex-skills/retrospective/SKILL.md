---
name: retrospective
description: "Use when the user invokes $retrospective to run a structured, discussion-driven retrospective of recent work that produces action items and process improvements."
---

# Retrospective Skill

Run a structured retrospective with the human. Five channel agents mine different data sources (git history, conversations, code quality, planning docs, tests) into a digest. Derive discussion topics from that data, walk through them with the human, and produce three output layers: action items, process improvements, and skill improvements. Finish with a readable narrative.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`.

## Out of Scope

This skill MUST NOT:
- Skip a human check-in. They happen after Phase 1 topic derivation, at every Phase 2 topic, at the Phase 3c review gate (which covers 3a-3c), and at the Phase 4 narrative review. Phase 0 runs without a pause.
- Manufacture consensus across the channels. If channels disagree, surface the tension.
- Use a templated topic list. Topics come from channel findings; if the data does not support a topic, drop it instead of padding.
- Re-mine source files, git logs, or session transcripts on session resume. Upstream phases are already distilled into saved files.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Guiding principles, the 5 channel agent prompts, the narrative agent prompt | Before dispatching agents in Phase 1 or Phase 4 |
| `references/output-formats.md` | Templates for all output files (carry-forward, digest, discussions, summary, action items, improvements, narrative) | Before writing output files |

## Invocation

| Invocation | Mode | Description |
|---|---|---|
| `$retrospective` | Chain (default) | From last retro to now (or beginning if first) |
| `$retrospective --since 2026-03-15` | Date-based | From a specific date to now |
| `$retrospective --since v1.0` | Tag-based | From a git tag to now |
| `$retrospective --since v1.0..v1.1` | Tag range | Between two tags |
| `$retrospective --output docs/sprints/3/` | Output override | Combinable with any mode |
| `$retrospective continue` | Resume | Resume an interrupted retro |

`--since` also accepts natural language (`yesterday`, `2 weeks ago`) and `beginning` (from the first commit).

### Time Boundary Resolution

1. If `--since` is provided, use it.
2. Otherwise, chain from the end date of the most recent retro directory in `docs/retros/`.
3. If no previous retro exists, ask the human whether to start from the beginning or from a point they name.
4. The end boundary is always HEAD / the current date.

### Output Directory

Default: `docs/retros/YYYY-MM-DD/` (retro execution date). Override with `--output <path>`.

---

## Phase 0a: Load Preferences (silent)

Read these files if they exist; use defaults for anything missing:

1. `.codex/skill-context/preferences.md` - shared preferences (detail level, tone, project phase).
2. `.codex/skill-context/retrospective.md` - retro-specific preferences: formality, and optional plan and spec folders for Channel 4.

Defaults: balanced detail, casual tone, structured review. Let detail level shape how many topics and how much digest context you surface, tone shape how you facilitate, and project phase shape the focus (prototype -> velocity, mature -> process). Pass project context and tone to all channel agents and to the narrative agent.

To point Channel 4 at the project's plans, add this to `.codex/skill-context/retrospective.md`:

```markdown
## Plan folders
- docs/plans
- docs/specs
```

---

## Phase 0b: Carry-Forward Check

Closes the feedback loop from the previous retro. On the first retro, skip silently - no file, no message.

Otherwise, read the previous retro's `03-action-items.md` and the Top Takeaways in its `03-retro-summary.md`. Mark each action item Completed (cite evidence: commit hash, file path, PR link), Incomplete (carry forward with its category), or Retired (give the reason). Apply the staleness rule in `references/output-formats.md`.

Save to `<retro-dir>/00-carry-forward.md`, then continue to Phase 1 without a pause.

---

## Phase 1: Mine via Parallel Channel Agents

Cover all five channels; run them in parallel. Read `references/agent-prompts.md` for the prompts and guiding principles.

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

Tell Channel 2 which host you are running in (Claude Code, Codex, or Antigravity), so it reads the matching session logs. Pass Channel 4 the plan folders from `retrospective.md`, if any.

| # | Channel | Data Source | Key Focus |
|---|---|---|---|
| 1 | Git History | Git log, diffs, contributors | Timeline, velocity, hotspots, pivots |
| 2 | Conversation History | The host's AI session logs (see Agent 2) | Corrections, friction, AI failures |
| 3 | Code Quality Delta | File structure, git diffs, audit metrics | What got better/worse structurally |
| 4 | Planning vs. Reality | Plan and spec folders | Completed, abandoned, unplanned work |
| 5 | Testing & Reliability | Test files, test runner, git diffs | Test health, coverage gaps, flakiness |

### Output Assembly

When all channels return, assemble their findings into `<retro-dir>/01-digest.md` with a facilitator preamble (period, key metrics, narrative arc).

### Topic Derivation

Derive as many discussion topics as the evidence supports - usually a handful. Group related findings, merge overlaps, and drop candidates with thin evidence. Rank by evidence strength and by how many channels flagged the theme. Give each topic a descriptive name and a one-line justification that names the channels behind it.

### Human Check-In

Present the narrative arc, key metrics, and proposed topics. Let the human approve, adjust the list, or add context before the discussion starts.

---

## Phase 2: Topic-by-Topic Discussion

Raw findings become insights through human judgment. Create `<retro-dir>/02-topic-discussions.md` with its YAML status header (see `references/output-formats.md`).

For each topic:

1. **Present findings** - what the data shows (with specific evidence), the patterns and tensions, and the blind spots only the human can fill.
2. **Ask the human to react** - agree, correct, add perspective, or skip.
3. **Capture the outcome** - key insights, the human's perspective, Start/Stop/Continue items.
4. **Save immediately** - append to `02-topic-discussions.md` and update the YAML header. After saving, keep only the Start/Stop/Continue items and a one-sentence insight in context; the full discussion is on disk.

When the human corrects the analysis, tag it `**[Human Correction]**`. Corrections show where the AI's model was wrong - the most valuable data in the retro. Surface them prominently in Phase 3. If no corrections came up, ask the human directly whether there were moments they corrected the AI during the period.

---

## Phase 3: Synthesize & Deliver

Read only `02-topic-discussions.md` - everything upstream is distilled there. Use the templates in `references/output-formats.md`. The synthesis must faithfully represent the discussions; do not contradict them.

### 3a: Retrospective Summary -> `03-retro-summary.md`

Metrics, narrative arc, human corrections, topic insights, and the top 3-5 takeaways.

### 3b: Action Items -> `03-action-items.md`

Turn the Start/Stop/Continue items into specific, verifiable action items, grouped by category with priorities.

### 3c: Improvement Proposals -> `03-improvements.md`

Draft process and skill improvement proposals. Each one must cite retro evidence.

### Human Review Gate

Present the proposals one by one. The human approves, rejects, or modifies each; record the status in the file. **Do not apply any change until the human explicitly approves it here.** "Proceed" earlier in the session is not approval.

---

## Phase 4: Retro Narrative

Run the narrative in a fresh-context agent (`subagent_type: "general-purpose"`). The analytical phases fill the context with structured data; writing from that context produces a reformatted summary instead of a story. Give the agent `03-retro-summary.md`, `02-topic-discussions.md`, and the narrative prompt in `references/agent-prompts.md`. It writes `<retro-dir>/04-retro-narrative.md`. Show the narrative to the human for review.

---

## Final Steps

After Phase 4 completes:

1. **Devlog scrap** - invoke `$devlog scrap --from-context` with the retro's most surprising insight. Skip silently if the skill is unavailable.

2. **Apply approved improvements** - implement the proposals approved in Phase 3c. Each change gets its own commit through the `$commit` skill.

3. **Commit retro artifacts** - if the project is a git repo, commit all output files through the `$commit` skill, suggesting the subject `docs(retro): add retrospective for <date range>`. If it is not a git repo (the conversation, planning, and testing channels still work), skip the commit and report that the artifacts are saved but uncommitted.

   Never run a raw `git commit`. If `$commit` is not available, do not commit: report which changes and artifacts are left uncommitted.

4. **Finish** by telling the human the retro is complete and where the artifacts are saved.

---

## Session Resumption

**Invocation:** `$retrospective continue`

1. Find today's retro directory in `docs/retros/`, or the most recent incomplete one (missing `04-retro-narrative.md`).

2. The files present decide the resume point:

| Files Found | Resume Point |
|---|---|
| No retro directory | Start from Phase 0b |
| `00-carry-forward.md` exists | Phase 1 |
| `01-digest.md` exists | Phase 2 |
| `02-topic-discussions.md` exists | Check YAML status (see below) |
| `03-retro-summary.md` exists | Phase 4 |
| `04-retro-narrative.md` exists | Final Steps only |

3. For a Phase 2 resume, read the YAML front matter: `status: complete` -> Phase 3; `topics_completed: N` -> resume at topic N+1.

4. Read only what the resume point needs:
   - Phase 1: `00-carry-forward.md` + the time boundary from the directory name
   - Phase 2: the YAML header + the topic list from the digest + the next topic's channel data
   - Phase 3: `02-topic-discussions.md`
   - Phase 4: `03-retro-summary.md` + `02-topic-discussions.md` (fresh agent)
