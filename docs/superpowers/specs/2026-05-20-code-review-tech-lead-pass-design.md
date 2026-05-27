# Code Review — Senior Tech Lead Re-review + Suggested Fix Field

**Status:** Spec (awaiting implementation plan)
**Skill affected:** `skills/codereview/SKILL.md` (and downstream consumers)
**Date:** 2026-05-20

---

## Problem

The `/codereview` skill dispatches 7 domain subagents + a cross-model reviewer in parallel, then synthesizes their findings. The current synthesis (Phase 3.1–3.6) is **mechanical**: collect → dedupe → severity filter → prioritize correctness → format. There is no judgment pass — no point where a senior engineer steps back and asks "do I actually agree with this list? Is this fix any good? Are we calling P0 things that aren't, and missing P0s that are?"

The result is that obvious misclassifications and weak fix suggestions reach the user unchallenged.

Additionally, per-finding fixes today live in a `**After**` code block. The block is the suggested fix, but it's not labeled as such, and there's no prose stating the **approach** of the fix — only the diff. That makes it hard for a re-reviewer (or the user) to evaluate whether the fix strategy is sound or just the literal change is.

## Goal

Add two enhancements to `/codereview`:

1. **Senior Tech Lead Re-review** — a final judgment pass over the synthesized findings, dispatched as one additional opus subagent. It can reject, reclassify, rewrite fixes, add missed findings, flag analysis gaps, and **produces the final report directly**.
2. **Explicit `**Suggested Fix:**` prose field** on every finding — 1–2 sentences stating the fix approach, sitting between `**Problem**` and `**Before**`. Gives the tech lead something judgment-evaluable beyond the diff.

## Non-Goals

- Adding more domain agents (the 7 + cross-model roster stays as-is).
- Changing the dedup / severity filter / correctness prioritization logic (Phase 3.1–3.6 logic is unchanged; tech lead operates on its output).
- Replacing the existing Before/After blocks. We **add** the prose field; we do not collapse Before/After into a single block.
- Changing `/quick-review`. Quick-review already uses `**Suggested Fix:**` in a leaner form and has no re-review concept.
- Re-reviewing the actual code edits that come out of Phase 4 (Fix Dispatch). Re-review evaluates findings + their proposed fixes; the Fix Dispatch then applies the tech-lead-approved fixes. Post-edit verification is out of scope.

---

## Design

### 1. Suggested Fix field (Phase 2 changes)

Every finding produced by every analyzer (7 domain agents, cross-model, large-tier cross-cluster synthesis) gains a `**Suggested Fix:**` field placed between `**Problem**` and `**Before**`.

New per-finding shape (additions in **bold**):

```
### [Principle Name] — [Specific Issue]
**Severity**: P0 | P1 | P2 | P3 | P4
**Location**: `file.ext:line_number`
**Problem**: What is wrong.
**Suggested Fix**: 1–2 sentences stating the fix approach — the WHY of the change,
                  the strategy that fixes the root cause, not just the diff.
**Before**:
```<target_language>
// the problematic code
```
**After**:
```<target_language>
// the corrected code matching the Suggested Fix
```
**Why**: What could go wrong if not fixed.
```

**Prompt-level rule:** subagents are explicitly instructed that **Suggested Fix and After must agree** — the prose states the strategy, the code shows it. If a subagent cannot articulate the strategy in prose, it likely has not understood the fix and should not emit the finding.

**Files touched in Phase 2:**
- `skills/codereview/SKILL.md` § Subagent Prompt Template (the template block in Phase 2)
- `skills/codereview/SKILL.md` § Cross-Model Prompt (the cross-model output format)
- `skills/codereview/SKILL.md` § Subagent Output Format (the documented shape)
- `skills/codereview/SKILL.md` § 3.1a Cross-Cluster Synthesis (large-tier synthesis agent output format)

### 2. Phase 3.7 — Tech Lead Re-review (new phase)

Inserted between current §3.6 (Output Format) and Phase 4 (Fix Dispatch). Always on by default; suppressed with `--no-re-review`.

#### Dispatch

One Agent call, `model: "opus"`. Sequential — runs after §3.6 produces the mechanically-synthesized report. Not parallelizable with the domain agents because it operates on their output.

#### Inputs to the tech lead subagent

- The mechanically-synthesized findings from §3.1–§3.6 (post-dedup, post-severity-filter, post-correctness-prioritization)
- The full diff (`git diff <base>...HEAD`)
- Full file contents (same context the domain agents got)
- Static analysis findings (TOOLING_CONTEXT)
- Cluster manifest if large-tier (§1.4b)
- Whether `--min-severity` was applied (so the tech lead knows what's been filtered out)

#### Persona prompt

> You are a senior tech lead doing a final read of a code review report before it goes to the engineer. The 7 domain agents and the cross-model reviewer have produced findings. Your job is to apply judgment — accept, reject, reclassify, rewrite fixes, add what they missed, and flag gaps in the analysis. Your output IS the final report the engineer will read.

#### Authorities

| # | Authority | Effect |
|---|---|---|
| 1 | Reject a finding | False positive, out of scope, fixed elsewhere, etc. → moves to `## Rejected by Re-review` with reason |
| 2 | Change severity (up or down) | Inline annotation `[Tech Lead: P2→P0 — reason]` |
| 3 | Rewrite `**Suggested Fix**` + `**After**` | Inline annotation `[Tech Lead: fix rewritten — reason]` |
| 4 | Add findings the agents missed | Placed in appropriate severity group, tagged `[Added by Tech Lead]` |
| 5 | Reclassify / merge / split | Combine duplicates dedup missed; split conflated findings |
| 6 | Flag analysis gaps | E.g., "no agent reviewed the migration rollback path" → `## Tech Lead Notes` |
| 7 | Suggest other improvements | Architectural concerns spanning findings, test coverage observations → `## Tech Lead Notes` |

#### Output contract

The tech lead produces the **final markdown report**, structured identically to §3.6 (Summary, severity-grouped findings, Recommendations), plus three new sections:

- `## Rejected by Re-review` — rejected findings with reasons, only if there are any
- `## Tech Lead Notes` — analysis gaps + open-ended suggestions, only if there are any
- Header line gains a Re-review change-count summary (see §4 below)

Inline annotations appear **only on touched findings**. Findings the tech lead accepted as-is have no annotation. That's how the user can tell at a glance what the tech lead changed.

If the tech lead agrees with everything as-is, the output is the mechanical report unchanged with a one-line note: *"Tech Lead: no changes — all findings stand as reported."*

#### Guardrails (baked into the prompt)

- **MUST NOT** rewrite for style/wording alone — only when judgment changes the verdict (severity, fix, accept/reject).
- **MUST** cite a reason for every change. No silent edits.
- **MUST NOT** lower severity to manage volume — same discipline as the domain agents.
- **MUST NOT** add findings outside the resolved scope (same scope rule as the rest of the skill).

### 3. Report assembly + tier interactions

#### Tier behavior

| Tier | Re-review timing |
|---|---|
| Small (≤30 files) | Runs once after §3.6, on the full synthesized findings |
| Medium (file batching, 31–100 files) | Runs **once** after all batches are merged and synthesized — not per batch |
| Large (logical-cluster, >100 files or >5,000 LOC) | Runs **after** §3.1a cross-cluster synthesis. Order: cluster dispatches → cross-cluster synthesis agent → mechanical dedup/filter → Tech Lead re-review |

The tech lead is always the **last** judgment pass before presentation.

#### Header update

The header line in §3.6 gains a Tech Lead segment and a change-count summary:

> `Models: [host] + [cross-model] + Tech Lead | Domains: 7 | Static: [tools] | Re-review: 3 rejected, 2 severity changes, 4 fixes rewritten, 1 added, 2 notes`

When `--no-re-review` is used, the line keeps its current format (no Tech Lead segment).

#### Interaction with `--min-severity`

Tech lead receives **all** findings regardless of `--min-severity` so it can upgrade a misclassified P3 → P0. The filter is applied **after** the tech lead, so the tech lead's verdict determines what the user actually sees. If the tech lead downgrades something below the threshold, it drops out silently (same as if the domain agent had emitted at that severity).

#### Interaction with dual cross-model dispatch (Codex + Antigravity)

No change. Both cross-model sources' findings flow through the same dedup → tech lead path.

#### Fix Dispatch (Phase 4) impact

When the user approves fixes, the tech lead's **rewritten** Suggested Fix + After code is what fix agents apply — not the original. Findings added by the tech lead are eligible for Fix Dispatch like any other. Rejected findings are not eligible (they live in the appendix for reference only).

### 4. New invocation flag

| Invocation | Mode | Scope |
|---|---|---|
| `--no-re-review` | Suppress Phase 3.7 | Skip the Tech Lead pass, present mechanical §3.6 output directly |

Added to the §22 Invocation table. Combinable with every other flag.

### 5. Out of Scope additions

Two new bullets in the top-of-skill "Out of Scope" list:

- The tech lead **MUST NOT** rewrite findings for style/wording alone — only when judgment changes the verdict.
- The tech lead **MUST NOT** silently change findings — every modification carries a reason citation in the inline annotation.

### 6. Failure handling

If the tech lead subagent fails or times out:

- Fall back to the mechanical §3.6 output unchanged.
- Header line: `Models: [host] + [cross-model] | Tech Lead re-review: unavailable ([reason]) | …`
- Offer retry: *"Tech Lead re-review failed. Want to retry it? Or proceed with the synthesized findings as-is?"*

Added to the `## Error Handling` table.

---

## Files changed (summary)

| File | Change |
|---|---|
| `skills/codereview/SKILL.md` | All sections above — Phase 2 prompt templates, new Phase 3.7, header format, `--no-re-review` flag, Out of Scope, Error Handling |

No new files. No other skills modified. Quick-review and other consumers are untouched.

---

## Cost note

The re-review costs one additional opus subagent call per review:

- Small tier: roughly +20% wall time
- Medium tier: smaller percentage of total wall time (batches already dominate)
- Large tier: smallest percentage of total wall time (cluster dispatches + cross-cluster synthesis already dominate), but absolute token cost is highest because the tech lead processes the most findings

`--no-re-review` is the opt-out for users who want the previous behavior.

---

## Open questions

None.

---

## Acceptance criteria

1. Every finding in the final report has a `**Suggested Fix:**` prose field (unless suppressed by a guardrail).
2. The report header includes a Tech Lead segment with a change-count summary when re-review ran.
3. Findings the tech lead modified carry an inline `[Tech Lead: …]` annotation with a stated reason.
4. Rejected findings appear in `## Rejected by Re-review` with reasons, not in the active severity groups.
5. Tech Lead Notes section appears only when there's something to say.
6. `--no-re-review` produces the pre-enhancement output (no annotations, no extra sections, no Tech Lead in the header).
7. If the tech lead subagent fails, the mechanical synthesis output is still presented, with a header note and a retry offer.
8. Large-tier reviews run cross-cluster synthesis **before** the tech lead.
9. `--min-severity` is applied after the tech lead, not before.
10. Phase 4 Fix Dispatch uses the tech lead's rewritten fixes when present.
