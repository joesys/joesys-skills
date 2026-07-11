# Handoff Artifact Schema

This file defines schema version 1 for handoff artifacts. Every producer and
consumer uses this contract. A handoff is one human-readable Markdown file;
there is no sidecar state file.

## File Location and Naming

The default path is:

```text
.handoffs/YYYYMMDD-HHMMSS-<slug>.md
```

Use local time for the filename and an ISO 8601 timestamp with offset in
frontmatter. Derive `<slug>` from the objective using lowercase kebab-case.
If the final path exists, append `-2`, `-3`, and so on. Never overwrite an
existing handoff. `--output <path>` overrides the default.

## Frontmatter

Required fields:

```yaml
---
schema_version: 1
created_at: 2026-07-12T14:30:00+08:00
audience: self
detail: operational
project: example
source_host: claude
target_host: codex
branch: master
head: 0123456789abcdef0123456789abcdef01234567
working_tree: dirty
repository_snapshot: {"branch":"master","dirty_patch_sha256":"...","head":"0123456789abcdef0123456789abcdef01234567","kind":"git","project_identity":"github.com/joesys/example","relevant_files":{},"snapshot_version":1,"status":[]}
---
```

Field rules:

| Field | Allowed value |
|---|---|
| `schema_version` | Integer `1` |
| `created_at` | ISO 8601 timestamp with UTC offset |
| `audience` | `self`, `agent`, or `human` |
| `detail` | `operational`, `full`, or `compact` |
| `project` | Repository or project name, not an absolute path |
| `source_host` | `claude`, `codex`, `gemini`, or `generic` |
| `target_host` | `claude`, `codex`, `gemini`, or `generic` |
| `branch` | Git branch, or `null` when unavailable |
| `head` | Full Git object ID, or `null` when unavailable |
| `working_tree` | `clean`, `dirty`, or `unverifiable` |
| `repository_snapshot` | Compact JSON emitted by `handoff_state.py snapshot` |

Keep `repository_snapshot` on one line so the standard-library helper can
extract it without a YAML dependency. Do not edit its data manually.

## Required Sections

Sections appear in this order. Use `Unknown` when the information should exist
but cannot be recovered. Use `Not established` when the session never made the
decision.

### 1. Resume Directive

One imperative paragraph telling the next reader what to do first. It names the
first safe action and any condition that must be checked before acting.

### 2. Objective and Success Criteria

State the current goal and observable completion criteria. Do not substitute a
task title for the goal.

### 3. Current State

Separate work into `Completed`, `In progress`, and `Not started`. A claim is
completed only when supported by conversation or repository evidence.

### 4. Decisions and Rationale

Record accepted decisions and why they were chosen. In `--full` mode, also
record rejected alternatives and revisit triggers.

### 5. Constraints and Guardrails

Record scope boundaries, user instructions, safety rules, platform constraints,
and actions that require fresh authorization.

### 6. Working Set

Use a table of repository-relative files or symbols:

```markdown
| Path or symbol | State | Why it matters |
|---|---|---|
| `src/example.py` | Modified | Implements the active behavior |
```

### 7. Repository State

Summarize project identity, branch, HEAD, staged paths, unstaged paths, and
untracked paths. Do not duplicate the full JSON snapshot.

### 8. Verification Evidence

Use a table:

```markdown
| Command | Outcome | Executed |
|---|---|---|
| `python -m pytest tests/example.py -q` | 4 passed | 2026-07-12T14:25:00+08:00 |
```

Only commands actually run belong here. Predictions and inferred health are not
executed evidence and must be labeled separately.

### 9. Blockers and Uncertainties

List missing authority, failing checks, unanswered questions, unverifiable
state, and assumptions the next reader must not silently adopt.

### 10. Next Actions

Provide an ordered list. The first item must be directly executable or state the
single decision needed before execution. Include relevant verification after
each mutation step.

### 11. Audience Notes

Apply the selected profile from `audience-target-profiles.md`. For `self`, keep
this short. For `agent`, define authority and report-back. For `human`, identify
review and judgment points.

### 12. Target Bootstrap

Apply only the selected target profile. Keep this section short and avoid
duplicating permanent project instructions.

## Detail Modes

### Operational Default

The default `operational` artifact is normally one to three pages. It includes
all required sections with only the context needed to resume safely.

### `--full`

Add:

- Rejected alternatives and their trade-offs.
- Deeper decision rationale.
- Important command history, limited to decisions and verification.
- Broader repository context that would otherwise need rediscovery.
- Revisit triggers for provisional decisions.

Never add raw conversation transcripts or general shell history.

### `--compact`

Keep:

- Frontmatter and repository snapshot.
- Resume Directive.
- Objective and Success Criteria.
- Current State.
- Blockers and Uncertainties.
- Next Actions.
- Minimal Audience Notes and Target Bootstrap.

Omitted required sections are represented by a one-line pointer such as
`No additional decisions recorded` rather than disappearing from the schema.

### `--include-diff`

Append `## Diff Appendix` after Target Bootstrap. Include only relevant patch
content. Omit paths reported under `sensitive_paths` and content that resembles
credentials, tokens, private keys, or environment secrets. Name each omitted
path without printing its contents. This option is independent of detail mode.

## Complete Operational Example

```markdown
---
schema_version: 1
created_at: 2026-07-12T14:30:00+08:00
audience: self
detail: operational
project: example
source_host: claude
target_host: codex
branch: feat/checkpoint
head: 0123456789abcdef0123456789abcdef01234567
working_tree: dirty
repository_snapshot: {"branch":"feat/checkpoint","dirty_patch_sha256":"abc123","head":"0123456789abcdef0123456789abcdef01234567","kind":"git","project_identity":"github.com/joesys/example","relevant_files":{"src/checkpoint.py":{"exists":true,"sensitive":false,"sha256":"def456","tracked":true}},"snapshot_version":1,"status":[{"path":"src/checkpoint.py","status":" M"}]}
---

# Checkpoint: add resumable state

## Resume Directive

Validate this checkpoint against the live repository, then add the pending
malformed-input regression test before changing parsing behavior.

## Objective and Success Criteria

Add resumable state that rejects malformed checkpoints and passes the focused
parser suite.

## Current State

### Completed
- Defined the checkpoint schema.

### In progress
- Parser implementation exists but lacks malformed-input coverage.

### Not started
- Distribution integration.

## Decisions and Rationale

- Store one Markdown artifact so humans and agents consume the same truth.

## Constraints and Guardrails

- Do not modify `main` directly.
- Do not claim test evidence without executing the command.

## Working Set

| Path or symbol | State | Why it matters |
|---|---|---|
| `src/checkpoint.py` | Modified | Contains the parser under test |

## Repository State

- Branch: `feat/checkpoint`
- HEAD: `01234567`
- Unstaged: `src/checkpoint.py`

## Verification Evidence

| Command | Outcome | Executed |
|---|---|---|
| `python -m pytest tests/test_checkpoint.py -q` | 3 passed | 2026-07-12T14:25:00+08:00 |

## Blockers and Uncertainties

- Malformed frontmatter behavior is not established.

## Next Actions

1. Write the malformed-frontmatter test and verify it fails.
2. Implement the minimal parser guard.
3. Re-run the focused suite.

## Audience Notes

This handoff is for the same operator in a fresh session; preserve the current
test-first sequence.

## Target Bootstrap

In Codex, read applicable `AGENTS.md` instructions, load this handoff, compare
live state, and continue only after the classifier accepts it.
```

## Validation Rules

- Reject missing or unsupported `schema_version` values.
- Reject missing or malformed `repository_snapshot` JSON.
- Reject unknown audience, detail, or target values.
- Require every canonical section in its fixed order.
- Never convert `Unknown` into a guessed fact during resume.
