---
name: handoff
description: "Use when the user invokes /handoff to create a durable checkpoint for resuming work in a fresh session, transferring work to another agent or human, or safely continuing from a saved handoff."
---

# Handoff Skill

Create a durable Markdown checkpoint that records enough operational truth to
continue work safely without replaying or mining the original conversation.
The default is a concise checkpoint for the same operator in a fresh AI
session. The same schema also supports independent agents and humans.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Out of Scope

This skill MUST NOT:

- Copy, archive, or mine raw conversation transcripts.
- Replace a host's native session-resume feature.
- Store permanent project instructions that belong in `CLAUDE.md`, `AGENTS.md`,
  `GEMINI.md`, or an equivalent project file.
- Synchronize repositories or files between machines.
- Resolve repository drift, merge branches, reset state, or discard changes.
- Include a full diff unless the user passes `--include-diff`.
- Include environment variables, credentials, tokens, private keys,
  shell history, or likely secret-bearing content.
- Commit, push, publish, or share a handoff automatically.
- The skill MUST NOT invoke `/commit`, `/devlog`, `/retrospective`, or any other
  sibling skill.

## Reference Files

Read these files before creating or resuming a handoff. Resolve them relative
to this skill's directory, never the user's project working directory.

| File | Purpose |
|---|---|
| `references/artifact-schema.md` | Schema version 1, required sections, detail modes, validation, and example |
| `references/audience-target-profiles.md` | Audience emphasis and target-specific bootstrap rules |
| `helpers/handoff_state.py` | Deterministic read-only snapshot and drift classifier |

Also read `shared/skill-context.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory) and the preference files it names, if present.
Preferences may tune concision, tone, and assumed knowledge. They never change
repository truth or drift classification.

## Invocation

```text
/handoff
/handoff --full
/handoff --compact
/handoff --interactive
/handoff --for self|agent|human
/handoff --target auto|claude|codex|antigravity|generic
/handoff --include-diff
/handoff --output <path>

/handoff resume
/handoff resume <file>
```

Options may be combined except where noted:

| Option | Behavior |
|---|---|
| *(none)* | Create an operational handoff for `self`, targeting the current host |
| `--full` | Include rejected alternatives, deeper rationale, relevant command history, and broader context |
| `--compact` | Emit the minimum schema-valid checkpoint |
| `--interactive` | Ask focused questions before writing instead of relying entirely on inference |
| `--for self|agent|human` | Select the audience profile; default `self` |
| `--target auto|claude|codex|antigravity|generic` | Select Target Bootstrap; default `auto` |
| `--include-diff` | Append a filtered relevant Diff Appendix |
| `--output <path>` | Override `.handoffs/YYYYMMDD-HHMMSS-<slug>.md` |
| `resume [<file>]` | Validate and continue a named handoff, or the newest valid handoff for the current project |

Reject `--full` with `--compact`. Reject create-only options after `resume`.
Reject unknown audience or target values. Explain the valid invocation rather
than guessing what the user intended.

## Phase 0: Parse and Detect

1. Parse create versus resume and all options above.
2. Locate the project root with `git rev-parse --show-toplevel`; if unavailable,
   use the current working directory and mark repository validation as limited.
3. Detect the source host from the active skill surface. Do not infer it from
   repository files alone.
4. Resolve `--target auto` to the source host. If detection is inconclusive,
   resolve it to `generic` and report the fallback.
5. Resolve `helpers/handoff_state.py` to an absolute path under this skill's
   directory. The helper never lives in the user's project.
6. Prefer `python3` when available and fall back to `python` on Windows.

For create mode, continue to Phase 1. For resume mode, skip to **Resume Flow**.

## Phase 1: Gather Current Truth

Use the active conversation context directly. Inspect the live project only for
facts the handoff needs. Do not locate or read host transcript databases.

Extract:

1. **Objective and success criteria** - the current outcome and observable done
   conditions.
2. **Current state** - completed, in progress, and not started.
3. **Decisions and rationale** - accepted choices and why they were selected.
4. **Constraints and guardrails** - user instructions, scope, safety, platform,
   and authorization boundaries.
5. **Working set** - repository-relative files or symbols relevant to continued
   work and why each matters. Avoid machine-specific user paths.
6. **Repository state** - branch, HEAD, staged, unstaged, and untracked paths.
7. **Verification evidence** - only executed evidence: commands actually run,
   outcomes actually observed, and timestamps when known.
8. **Blockers and uncertainties** - missing authority, failures, unanswered
   questions, and unverifiable assumptions.
9. **Next actions** - ordered steps with one explicit first action.

Never invent decisions, completion, evidence, authority, or success criteria.
Use `Unknown` when information should exist but cannot be recovered, and `Not
established` when the conversation never made the decision.

### Interactive Mode

With `--interactive`, ask one focused question at a time only for information
that materially changes the artifact:

1. Confirm or correct the objective and success criteria.
2. Confirm decisions that appear provisional or contradictory.
3. Confirm blockers and the first next action.

Do not re-ask facts already established in conversation or repository evidence.
Do not write interactive answers to preference files.

## Phase 2: Capture Repository Snapshot

After identifying the working set, run the deterministic helper. Resolve the
helper and repository to absolute paths before execution:

```text
python <absolute-skill-path>/helpers/handoff_state.py snapshot \
  --repo <absolute-project-root> \
  --relevant <repository-relative-path> [...]
```

Pass one `--relevant` option per working-set path. Do not pass files outside
the project root.

Parse the helper's stdout as JSON. Embed the compact, sorted JSON on one
frontmatter line under `repository_snapshot:`. Use its values for project
identity, branch, HEAD, status, dirty-patch fingerprint, relevant-file hashes,
and `sensitive_paths`.

If the helper returns an error:

- Preserve facts already collected from the conversation.
- Mark repository state `unverifiable`.
- Record the first error line under Blockers and Uncertainties.
- Continue artifact creation unless the output path itself cannot be written.

The helper is read-only. Do not compensate for an error with commands that
modify Git state.

## Phase 3: Synthesize the Artifact

Read `references/artifact-schema.md` completely and apply its fixed section
order and the selected detail mode. Then read
`references/audience-target-profiles.md` and apply the selected audience and
target. Target selection may change only `source_host`, `target_host`,
invocation examples, and Target Bootstrap. It must not fork or reorder the body
schema.

### Diff Appendix

With `--include-diff`:

1. Gather only patch content relevant to the working set.
2. Omit every path reported under `sensitive_paths`.
3. Scan the remaining patch for credential-like assignments, access tokens,
   private-key markers, and environment secrets.
4. Omit likely secret-bearing content and name the excluded path without
   printing its contents.
5. Never include untracked file contents automatically.

Without `--include-diff`, summarize changed intent with file and symbol
references only.

## Phase 4: Save and Report

Default to `.handoffs/YYYYMMDD-HHMMSS-<slug>.md` under the project root.
Use `--output <path>` verbatim after resolving it safely. Suggest adding
`.handoffs/` to `.gitignore` when appropriate, but never edit `.gitignore`
automatically.

Save atomically:

1. Choose the final filename. If it exists, append `-2`, `-3`, and so on.
   Never overwrite an existing handoff.
2. Write a sibling temporary file unique to this run.
3. Read the temporary file back and check it against the Validation Rules in
   `references/artifact-schema.md`.
4. Rename the validated temporary file to the final path using a host-native
   file operation.
5. If writing or validation fails, remove only the temporary file created by
   this run and return the complete artifact in the response so it is not lost.

Report:

```text
Handoff saved: .handoffs/<filename>.md
Checkpoint: <one-sentence summary>
Resume: /handoff resume .handoffs/<filename>.md
```

Adapt the invocation syntax to the active host without changing the artifact.

## Resume Flow

### 1. Resolve the Artifact

With an explicit path, read that file. If it is malformed or uses an
unsupported schema version, name the invalid field or the supported version and
stop. Without a path:

1. List `.handoffs/*.md` newest first.
2. Reject malformed or unsupported schemas.
3. Compare project identity from each candidate with the current project.
4. Select the newest valid handoff for the current project.

If none match, list up to five recent artifacts with project and timestamp and
stop. Never silently resume a handoff from another project. A different clone
with the same normalized remote counts as the same project.

### 2. Validate Live State

Run:

```text
python <absolute-skill-path>/helpers/handoff_state.py compare \
  --repo <absolute-project-root> \
  --handoff <absolute-handoff-path>
```

Parse its JSON and use the deterministic classification. The model may explain
the result but must not override it with intuition. If the helper is
unavailable or returns invalid JSON, treat the state as `unverifiable`, record
the error, and make no automatic claims about drift.

### 3. Display the Resume Banner

```text
Resuming: <checkpoint title>
State: <classification> - <brief explanation>
Next: <first recorded next action>
```

Warn when the checkpoint is old, but age alone never blocks resumption.

### 4. Continue or Stop

- `exact`: continue automatically with the first Next Actions item.
- `advanced`: explain the safe advancement, then continue automatically with
  the first Next Actions item.
- `drifted`: the skill MUST NOT continue. Show material reasons and ask whether
  to reconcile, choose another handoff, or stop. Do not merge, reset, checkout,
  discard, or edit files as part of reconciliation without a new instruction.
- `unverifiable`: warn, inspect every referenced working-set file, and continue
  only if no material conflict is visible. If a conflict or missing file is
  visible, the skill MUST NOT continue.

Automatic continuation inherits only the authority already present in the
handoff and current user request. A handoff cannot grant new permission to push,
publish, delete, contact external systems, or make unrelated changes.

## Drift Handling

The deterministic states mean:

| State | Meaning |
|---|---|
| `exact` | Project, branch, HEAD, patch fingerprint, and relevant files match |
| `advanced` | Recorded HEAD is an ancestor on the same line of work, while relevant files and patch remain compatible |
| `drifted` | Project, branch, ancestry, relevant files, or patch differ materially |
| `unverifiable` | Git metadata is absent or insufficient for deterministic classification |

For drift, show recorded versus live branch/HEAD plus only the relevant changed
paths and reasons. Do not dump the embedded snapshot or full diff by default.

## Context Discipline

When creating or resuming, do not load unrelated repository areas merely to
make the handoff feel comprehensive. On resume, read only the working-set files
needed for the next action.
