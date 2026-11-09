# Retrospective — Output Format Templates

Templates for every output file of a retrospective.

## 00-carry-forward.md

Created in Phase 0. Reviews previous retro's action items.

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

**Staleness rule:** an item carried forward for 3+ consecutive retros gets a `[STALE]` flag. A stale item forces a decision: do it, retire it, or escalate to the human.

Carry forward from the immediately previous retro only; it already holds the older items.

---

## 01-digest.md

Created after the Phase 1 agents return. Keep each channel's findings under its own heading, after a facilitator preamble:
- **Period**: start → end (with dates)
- **Key metrics**: commits, files changed, tests delta (pulled from channel findings)
- **Narrative arc**: one-sentence story of the period ("from X to Y")

---

## 02-topic-discussions.md

Created incrementally during Phase 2. Each topic is appended after the human's reaction.

```yaml
---
status: in-progress
topics_completed: 0
topics_total: <N>
---
```

```markdown
# Retrospective — Topic Discussions

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

## 03-retro-summary.md

Created in Phase 3a. Consolidates all topic discussions.

```markdown
# Retrospective — <narrative arc summary>

**Period:** <start date/ref> → <end date/ref>
**Date:** YYYY-MM-DD

## Metrics
- Commits: X
- Files changed: X (+N new, -N deleted)
- Tests: +N added, -N removed (X total passing, X failing)
- Insertions/Deletions: +X / -X

## Narrative Arc
[One-sentence story of the period — from the digest]

## Notable Human Corrections
[Explicitly listed — where the human overruled the analysis and why. These are the highest-signal moments in the retro.]
- **[Topic Name]**: [What the analysis got wrong] → [What's actually true]

## Topic Insights

### 1. [Topic Name]
**Key Insights:** [2-3 sentences on what we learned]
**Human's Perspective:** [What the human added]
- Start: [items]
- Stop: [items]
- Continue: [items]

[...repeated for each topic...]

## Top Takeaways
[3-5 most impactful learnings from the entire retro, ranked by impact on future work]
1. [Takeaway] — [Why it matters]
2. [Takeaway] — [Why it matters]
3. [Takeaway] — [Why it matters]
```

---

## 03-action-items.md

Created in Phase 3b. Extracted from all topic discussions.

```markdown
# Retrospective Action Items — YYYY-MM-DD

## [Category]
- [ ] [Specific, actionable item] — [Why, referencing topic] — Priority: high/medium/low

## [Category]
- [ ] [Item] — [Why] — Priority: high/medium/low

## Deferred / Watch List
- [Items noted but not actionable yet — revisit next retro]
```

Use whichever categories fit the actual items (for example Workflow Changes, Tooling, Testing, Documentation, Technical Debt).

Every action item must be **specific and verifiable**. "Improve testing" is not an action. "Add integration tests for the payment API endpoint" is.

---

## 03-improvements.md

Created in Phase 3c. Concrete proposals for process and skill changes.

```markdown
# Retrospective — Improvement Proposals

## Process Improvements

### Proposal 1: [Brief Description]
**Target:** [What to change — CLAUDE.md, .gitignore, hook, CI config, etc.]
**Change:** [Specific change to make]
**Why:** [Grounded in retro evidence — reference the topic and finding]
**Status:** Proposed

### Proposal 2: [Brief Description]
[...repeat...]

## Skill Improvements

### Proposal N: [Skill Name] — [Brief Description]
**Skill:** [Skill name or path]
**Change:** [What specifically to add/remove/modify]
**Why:** [Grounded in retro evidence — reference the topic and finding]
**Status:** Proposed
```

After the Phase 3c review gate, set each status to Approved, Rejected, or Modified.

---

## 04-retro-narrative.md

Created by the Phase 4 narrative agent. Prose format — no headers, bullet points, or structured formatting. See `references/agent-prompts.md` for the narrative agent prompt and writing rules.
