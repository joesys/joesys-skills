# Handoff Skill Design

**Date:** 2026-07-12
**Status:** Approved
**Skill:** `handoff`

## Purpose

`handoff` creates a durable, host-neutral checkpoint that lets work continue in a fresh AI session without re-discovering goals, decisions, repository state, verification evidence, and next actions. Its primary use case is the same operator resuming work in a new session, while also supporting delegation to another agent and transfer to another human.

The skill is an explicit semantic checkpoint, not a replacement for the native conversation-resume features in Claude Code, Codex, or Gemini CLI. Native resume restores a conversation; `handoff` records the minimum operational truth needed to continue safely, including across clients.

## Goals

- Resume work in a fresh session with minimal re-discovery.
- Support transfers to independent agents and humans without separate schemas.
- Detect material repository drift before continuing recorded work.
- Keep handoffs readable as Markdown and reliable enough for automated resume behavior.
- Remain host-neutral at the core while providing a small target-specific bootstrap.
- Preserve executed verification evidence without turning inference into evidence.

## Out of Scope

The skill does not:

- Copy or archive raw conversation transcripts.
- Replace native Claude Code, Codex, or Gemini session resume.
- Persist general project instructions that belong in `CLAUDE.md`, `AGENTS.md`, or `GEMINI.md`.
- Synchronize files between machines or repositories.
- Include full diffs unless explicitly requested.
- Resolve repository divergence automatically.
- Commit, push, publish, or otherwise distribute a handoff automatically.
- Store credentials, environment variables, shell history, or likely secret-bearing content.

## Invocation

```text
/handoff
/handoff --full
/handoff --compact
/handoff --interactive
/handoff --for self|agent|human
/handoff --target auto|claude|codex|gemini|generic
/handoff --include-diff
/handoff --output <path>

/handoff resume
/handoff resume <file>
```

The Codex adapter rewrites `/handoff` to `$handoff` in the generated collection.

### Defaults

| Setting | Default |
|---|---|
| Audience | `self` |
| Target | `auto`, resolved to the current host |
| Detail | Operational brief |
| Interaction | Automatic; no interview or save confirmation |
| Storage | `.handoffs/YYYYMMDD-HHMMSS-<slug>.md` |
| Diff handling | Summarized, not embedded |
| Resume selection | Newest valid handoff for the current project |

`--interactive` asks about goals, decisions, blockers, and next actions before writing. `--full` and `--compact` are mutually exclusive. `--output` overrides the default directory and filename. The skill may suggest adding `.handoffs/` to `.gitignore`, but it never edits `.gitignore` automatically.

## Audience and Target

Audience and runtime target are separate dimensions.

### Audience Profiles

| Audience | Primary reader | Emphasis |
|---|---|---|
| `self` | Same operator in a fresh AI session | Concise operational continuity; assumes the same project and user preferences |
| `agent` | Independent agent with no hidden context | Authority, allowed mutations, constraints, inputs, deliverable, completion criteria, and report-back format |
| `human` | Another person | Rationale, orientation, review points, ownership, and decisions requiring judgment |

### Target Profiles

`--target` changes only a short **Target Bootstrap** section. The canonical schema and core content remain identical.

| Target | Bootstrap behavior |
|---|---|
| `auto` | Detect the current host; fall back to `generic` if detection is inconclusive |
| `claude` | Use Claude Code invocation terminology and point to applicable `CLAUDE.md` guidance |
| `codex` | Use Codex skill terminology, point to applicable `AGENTS.md`, and respect active sandbox and approval policy |
| `gemini` | Use Gemini-compatible terminology and point to applicable `GEMINI.md` guidance |
| `generic` | Avoid client-specific commands, tools, memory paths, and capability assumptions |

The runtime bootstrap must remain small. It must not duplicate detailed capability tables that will become stale.

## Artifact Format

Every handoff is a Markdown file with YAML frontmatter and stable sections.

### Frontmatter

```yaml
---
schema_version: 1
created_at: 2026-07-12T14:30:00+08:00
audience: self
detail: operational
project: joesys-skills
source_host: claude
target_host: codex
branch: master
head: 3897f99
working_tree: dirty
---
```

Additional repository snapshot data may be recorded in frontmatter when available. Paths inside the repository are repository-relative.

### Required Sections

1. **Resume Directive** - the first safe action for the next session.
2. **Objective and Success Criteria**
3. **Current State** - completed, in progress, and not started.
4. **Decisions and Rationale**
5. **Constraints and Guardrails**
6. **Working Set** - relevant files or symbols and why they matter.
7. **Repository State** - branch, HEAD, staged, unstaged, and untracked summary.
8. **Verification Evidence** - commands, outcomes, and execution time when known.
9. **Blockers and Uncertainties**
10. **Next Actions** - ordered, executable steps with an explicit first action.
11. **Audience Notes**
12. **Target Bootstrap**

### Detail Modes

- **Operational default:** Usually one to three pages. Includes every required section without broad history.
- **`--full`:** Adds discarded alternatives, deeper reasoning, important command history, and broader context.
- **`--compact`:** Keeps the resume directive, objective, current state, blockers, and next actions, plus the minimum metadata needed for drift validation.
- **`--include-diff`:** Adds a Diff Appendix after the required sections. It is independent of detail mode.

Unknown information is labeled `Unknown` or `Not established`; the skill never invents decisions, completion status, or evidence to fill a section.

## Creation Flow

1. Parse audience, target, detail, output, interaction, and diff options.
2. Detect the project root, repository state, source host, and target host.
3. Gather context from the active conversation and live project. Do not scrape host-specific transcript databases.
4. Extract the objective, success criteria, decisions, constraints, working set, verification evidence, blockers, and next actions.
5. If `--interactive` is present, ask focused questions before synthesis. Otherwise proceed automatically and flag uncertainty in the artifact.
6. Apply the selected audience emphasis and target bootstrap.
7. Validate required metadata and sections against schema version 1.
8. Write the artifact atomically. If a timestamped name collides, append a numeric suffix rather than overwrite.
9. Report the saved path, one-sentence checkpoint summary, and exact resume invocation.

## Repository Snapshot and Drift Detection

For Git repositories, creation records:

- Repository identity, preferring normalized remote URL and falling back to root name.
- Branch and HEAD.
- Staged, unstaged, and untracked paths.
- A fingerprint of the dirty patch.
- Content hashes for relevant untracked files.

Fingerprints are drift detectors, not security guarantees.

The deterministic helper uses Git-native commands where possible so behavior remains consistent across platforms. It must not mutate repository state.

## Resume Flow

1. Resolve the named artifact. Without a path, select the newest schema-valid handoff matching the current project.
2. Validate schema version and project identity.
3. Capture the live repository snapshot.
4. Compare live state with the recorded snapshot.
5. Classify the result and display a compact resume banner.
6. Continue the first recorded next action automatically only when the state is compatible.

### Drift Classifications

| State | Definition | Behavior |
|---|---|---|
| `exact` | Branch, HEAD, and relevant working-tree fingerprints match | Continue automatically |
| `advanced` | Recorded HEAD is an ancestor on the same line of work and relevant changes remain compatible | Explain advancement, then continue automatically |
| `drifted` | Branch diverged, relevant files changed incompatibly, or recorded files disappeared | Stop and present the material differences |
| `unverifiable` | Repository metadata is unavailable or insufficient | Warn, inspect referenced files, and continue only when no material conflict is visible |

Example banner:

```text
Resuming: handoff skill design
State: advanced - 2 commits since checkpoint, no relevant conflicts
Next: finalize error handling and test design
```

Age alone never blocks resumption, but an old handoff receives a staleness warning.

## Components

```text
skills/handoff/
|-- SKILL.md
|-- helpers/
|   |-- handoff_state.py
|   `-- test_handoff_state.py
`-- references/
    |-- artifact-schema.md
    `-- audience-target-profiles.md
```

### Responsibilities

- `SKILL.md`: invocation parsing, context synthesis, creation, resume orchestration, safety rules, and user-facing output.
- `artifact-schema.md`: metadata, required sections, detail modes, schema-version rules, and examples.
- `audience-target-profiles.md`: controlled differences between audience and target profiles.
- `handoff_state.py`: standard-library-only repository snapshot, fingerprint, identity, ancestry, and drift classification.

Critical drift decisions must come from the deterministic helper, not free-form model judgment alone. The model explains the helper result and handles non-Git contextual checks.

## Error Handling

| Condition | Behavior |
|---|---|
| Not a Git repository | Create the artifact with `unverifiable` state and referenced-file checks |
| Insufficient conversation context | Record unknowns explicitly and preserve what can be verified from the project |
| No matching handoff | List the newest available artifacts, if any, and stop |
| Malformed artifact | Report the failing field or section and stop without partial interpretation |
| Newer unsupported schema | Report the supported version and stop |
| Different clone path, same remote | Accept as the same project |
| Different project identity | Stop before executing any recorded action |
| Relevant fingerprint changed | Classify as `drifted` and require reconciliation |
| Unsupported target host | Fall back to `generic` and report the fallback |
| Output collision | Add a numeric suffix; never overwrite an existing handoff |
| Write failure | Return the complete artifact in the response so the checkpoint is not lost |
| Potential secret in requested diff | Omit the affected content and identify the excluded path |

## Safety and Privacy

- Never include raw transcripts, environment variables, credentials, private keys, tokens, or shell history.
- Use repository-relative paths where possible and avoid embedding machine-specific user paths.
- Summarize diffs by default.
- Treat `--include-diff` as permission to include ordinary patch content, not secret-bearing files.
- Record only commands relevant to verification or the next action; do not reproduce general command history.
- Label inferred state separately from executed evidence.
- Do not commit, push, or share the artifact automatically.
- On `drifted` state, do not attempt merges, resets, checkouts, or conflict resolution automatically.

## Cross-Skill Interfaces

The stable `handoff` interface is documented in `shared/skill-interfaces.md`.

Potential consumers may read a handoff as supplementary context, but version 1 has no automatic outbound invocation of other skills. In particular, `handoff` does not invoke `commit`, `devlog`, `retrospective`, or `design-review`.

## Testing Strategy

### Deterministic Helper Tests

- Snapshot clean, staged, unstaged, mixed, and untracked repositories.
- Produce stable dirty-patch fingerprints.
- Hash relevant untracked files.
- Normalize repository identity across equivalent remote URL forms.
- Detect recorded-HEAD ancestry.
- Classify `exact`, `advanced`, `drifted`, and `unverifiable` states.
- Cover renamed, deleted, and missing relevant files.
- Prove all helper commands are read-only.

### Schema and Profile Tests

- Validate operational, full, and compact fixtures.
- Reject missing required metadata and unsupported schema versions.
- Ensure `agent` handoffs contain authority, mutation, deliverable, and report-back boundaries.
- Ensure `human` handoffs contain rationale and review context without agent-execution instructions.
- Ensure every target profile changes only the Target Bootstrap section.
- Ensure generic output contains no host-specific paths or commands.

### Integration Tests

- Create and resume a handoff without Git.
- Create and resume in an unchanged repository.
- Advance the same branch and classify it as `advanced`.
- Diverge the branch or alter a relevant dirty file and classify it as `drifted`.
- Resume from a different clone of the same remote.
- Select the newest matching artifact without crossing project identities.
- Verify write collisions preserve existing files.
- Verify likely secret-bearing diff content is excluded.

### Distribution Tests

- Add `handoff` to the expected skill set.
- Verify Claude invocation remains `/handoff` and the Codex adapter produces `$handoff`.
- Verify Codex output contains no unsupported Claude-only execution primitives.
- Verify README, plugin manifests, cross-skill interfaces, and committed `codex-skills/` remain synchronized.

## Acceptance Criteria

The design is satisfied when:

1. `/handoff` automatically creates a schema-valid operational artifact in `.handoffs/`.
2. `--full`, `--compact`, `--interactive`, `--for`, `--target`, `--include-diff`, and `--output` behave as specified.
3. `/handoff resume` selects the newest valid matching artifact and never crosses project identity silently.
4. Exact and safely advanced states continue the first next action automatically.
5. Drifted states stop before mutation and explain the relevant differences.
6. The same canonical artifact remains readable by self, an independent agent, and a human.
7. Target-specific content is confined to a small bootstrap section.
8. Sensitive content is excluded even when full diff inclusion is requested.
9. The deterministic helper and integration matrix pass on supported Windows and POSIX environments.
10. The generated Codex collection is fresh and behaviorally compatible with the supported Codex workflow.
