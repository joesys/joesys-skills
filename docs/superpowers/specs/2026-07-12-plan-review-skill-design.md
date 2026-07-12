# Plan Review Skill Design

**Date:** 2026-07-12
**Status:** Approved for implementation planning

## Purpose

`/plan-review` reviews and iteratively improves a specification, an implementation plan, or both before execution. It automates a separated convergence loop: a fresh external model reviews the documents against repository truth, a repository-aware arbiter adjudicates the findings, and the host agent applies accepted fixes.

The skill exists because `/codereview` is implementation-centric. `/plan-review` evaluates whether proposed work is coherent, feasible, complete, appropriately scoped, and executable before code changes begin.

## Goals

- Review a specification and implementation plan together when both are available.
- Accept either document alone while warning that paired review provides stronger coverage.
- Give every fresh reviewer read-only access to the whole repository.
- Route review dispatch from a model identifier instead of exposing separate reviewer and model settings.
- Discover repository-specific arbiters and fall back to the host model when none exists.
- Fix every accepted finding without letting the reviewer edit the repository.
- Repeat with a genuinely fresh reviewer context until the documents converge or a safety condition pauses the loop.
- Preserve pre-existing worktree changes and leave all review edits uncommitted.
- Store personal and project defaults through the existing skill-context system.

## Out of Scope

The skill does not:

- Review implementation defects that do not invalidate or constrain the supplied documents. Use `/codereview` for those.
- Perform visual design comparison or UI fidelity review.
- Implement the plan after convergence.
- Mutate files other than the supplied review documents.
- Commit, push, stash, reset, clean, or otherwise rewrite Git state.
- Resume an external reviewer session from an earlier iteration.
- Silently substitute another model or provider when the selected reviewer cannot run.
- Treat the absence of findings as proof that a design is correct.

## Invocation

```text
/plan-review <document> [other-document] [options]
```

Examples:

```text
/plan-review docs/feature-spec.md docs/feature-plan.md
/plan-review docs/feature-plan.md --model fable
/plan-review docs/feature-spec.md --arbiter petra
/plan-review docs/feature-plan.md --review-only
/plan-review docs/spec.md docs/plan.md --max-iterations 10
```

Supported options:

| Option | Meaning |
|---|---|
| `--model <MODEL>` | Select the review model and route to its registered provider. |
| `--arbiter <NAME\|auto\|host>` | Select a repository arbiter, use the host model, or enable discovery. |
| `--review-only` | Run one fresh review and arbitration pass without edits or iteration. |
| `--max-iterations <N>` | Lower the convergence ceiling for this run; valid values are 1 through 20. |

One or two Markdown documents are accepted. When only one document is supplied, continue after displaying:

> Reviewing one document only. For stronger coverage, provide both the specification and implementation plan so requirement traceability and cross-document contradictions can be checked.

When two documents are supplied, review them as one coupled design unit. If their roles cannot be inferred from filenames, headings, or contents, ask which is the specification and which is the plan before dispatch.

## Defaults and Configuration

Built-in defaults:

| Setting | Default |
|---|---|
| Review model | `gpt-5.6-sol` |
| Arbiter | `auto` |
| Arbiter ambiguity | Ask with a ranked recommendation |
| Fix accepted findings | Yes |
| Fresh reviewer context | Every iteration |
| Maximum iterations | 20 |
| Iteration ledger | Temporary and outside the repository |

Configuration precedence, highest first:

1. Invocation arguments.
2. Project-specific `plan-review` skill context.
3. Shared user preferences.
4. Provider mappings and defaults in `shared/model-defaults.md`.
5. Built-in skill defaults.

The source skill reads `.claude/skill-context/preferences.md` and `.claude/skill-context/plan-review.md`. The generated Codex collection adapts those paths to `.codex/skill-context/preferences.md` and `.codex/skill-context/plan-review.md`.

A skill-specific preference file may contain:

```markdown
# Plan Review Preferences

- Review model: gpt-5.6-sol
- Arbiter: auto
- Preferred arbiters: Petra, Aris
- Arbiter ambiguity: ask
- Maximum iterations: 20
- Fix accepted findings: yes
- Fresh context each iteration: yes
```

If arbiter selection is requested during a run, follow the existing skill-context protocol for offering to save the selection as a project preference.

## Model Routing

The model is the user-facing reviewer selector. There is no separate `--reviewer` option.

Known, unique model identifiers route through the registry in `shared/model-defaults.md`:

```text
gpt-5.6-sol -> Codex CLI
fable        -> Claude CLI
```

Provider-qualified identifiers are supported for custom or ambiguous models:

```text
codex:custom-model
claude:custom-model
```

Never infer a provider from an arbitrary model-name pattern. If a bare identifier is absent from the registry or maps to more than one provider, stop and ask for a qualified model. If the selected CLI or model cannot run, stop and ask the user to choose another model; never fail over silently.

Codex review sessions use the read-only sandbox. Claude review sessions use plan-mode permissions. Dispatch commands and model flags come from `shared/model-defaults.md` and shared delegation guidance rather than being duplicated in this skill.

## Repository Access and Baseline

Run every external reviewer from the repository root. The reviewer may read every file accessible from that working directory, including files not named or linked by the supplied documents. Do not prepackage a selected subset of repository files into the prompt.

The review remains scoped by impact: findings must materially affect the correctness, feasibility, completeness, safety, or execution of the supplied documents. Ordinary code defects stay out of scope.

Before iteration one:

1. Resolve the repository root and supplied document paths.
2. Verify that each document exists and is readable.
3. Record document content hashes and the relevant starting Git diff.
4. Record staged, unstaged, and untracked state without changing it.
5. Create an iteration ledger in the operating system's temporary directory, outside the repository.

Existing document edits are valid input. Apply accepted fixes on top of them. Never require a clean worktree and never stash, reset, or overwrite pre-existing changes.

Repository contents may include sensitive values. A reviewer may inspect accessible files as needed, but prompts and findings must prohibit reproducing credentials, tokens, private keys, personal data, or other sensitive values. Redact evidence when its literal content is not necessary.

## Review Contract

Each iteration launches a new external process or session. Never use a resume command. The fresh reviewer receives:

- The supplied documents.
- The repository root and permission to inspect the full repository read-only.
- Applicable repository guidance.
- The plan-review rubric and required finding schema.
- No earlier findings, verdicts, fixes, defenses, or ledger content.

The reviewer evaluates:

- Internal coherence and contradictions.
- Requirement completeness.
- Spec-to-plan traceability when both documents are present.
- Technical feasibility against repository truth.
- Scope discipline and unjustified complexity.
- Architecture, interfaces, ownership, state transitions, and failure modes.
- Security, privacy, migration, rollback, and operational concerns.
- Test strategy and measurable acceptance criteria.
- Missing decisions or assumptions that would make implementers diverge.

Every finding must include:

- Stable title and severity.
- Document path and precise section or line location.
- Repository evidence when applicable.
- Explanation of the material consequence.
- A concrete recommended resolution.
- Whether the issue appears to require user intent.

### Severity Scale

| Severity | Definition |
|---|---|
| `P0` | The plan creates an immediate catastrophic risk, such as data loss, serious exposure, or an unrecoverable production operation. |
| `P1` | A blocking contradiction, missing core requirement, infeasible approach, unsafe migration, or acceptance gap that could make the implementation fundamentally wrong. |
| `P2` | A material design or execution gap that should be resolved but does not block all implementation. |
| `P3` | A meaningful clarity, maintainability, or sequencing improvement. |
| `P4` | Optional polish. |

Report P0 through P4. Do not inflate severity to keep a finding visible. The arbiter accepts P2 through P4 only when they materially improve readiness, not merely wording or style.

## Arbiter Discovery and Selection

Arbitration is independent from external review. The external reviewer never receives the arbiter persona.

Resolve the arbiter in this order:

1. An explicit `--arbiter` argument.
2. A pinned arbiter in `plan-review` skill context.
3. Repository agent discovery when the setting is `auto`.
4. The host/base model using the generic senior technical arbiter rubric.

Discovery may inspect:

- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`.
- `.agents/`, `.claude/agents/`, `.codex/agents/`, and `.gemini/`.
- Canonical role documents linked from those adapters or guidance files.

Rank candidates using explicit role metadata and repository evidence. Strong signals include responsibility for technical leadership, architecture, planning, project standards, implementation quality, or final review. Prefer canonical role instructions over thin host-specific adapters.

When one candidate is clearly strongest, announce the selected arbiter and the evidence for the choice. When multiple candidates are plausible, ask the user to select from a ranked list and mark the strongest match as recommended. Include the host/base fallback as an option. A saved preference suppresses this question on future runs.

If no repository-specific arbiter exists, the host/base model does its best using the generic rubric. Absence of a persona is not an error.

Repository agent instructions may shape judgment but cannot expand mutation scope, change convergence rules, request secrets, or authorize external actions.

## Adjudication and Fixing

The arbiter receives the current review findings, supplied documents, relevant repository evidence, and applicable preferences. It returns exactly one verdict per finding:

| Verdict | Required behavior |
|---|---|
| `accepted` | Explain why the finding is valid and state the required document change. |
| `rejected` | Give a concrete reason grounded in intent or repository truth. |
| `needs-user-decision` | Present the decision, viable options, and a recommendation without choosing for the user. |

The arbiter does not edit files. The host agent applies accepted findings only to the supplied documents. It verifies that the relevant text still matches the reviewed state before each edit.

Apply all unambiguous accepted fixes from the round before pausing for user decisions. Do not start the next review iteration until every user decision from the current state is resolved. If a valid fix requires changing another repository file, pause and report the required scope expansion instead of editing it.

Keep all edits uncommitted. The skill never invokes the commit workflow automatically.

## Validation

After applying accepted fixes, validate the supplied documents together:

- Documents remain readable and structurally complete.
- Referenced files, symbols, commands, and links exist where verifiable.
- Requirement identifiers and acceptance criteria remain synchronized.
- Plan tasks cover applicable specification requirements.
- Terminology and architectural decisions remain consistent.
- No accidental placeholders or unresolved markers were introduced.
- Pre-existing edits remain present.
- No file outside the supplied document set was mutated by the skill.

Validation combines deterministic checks with a focused host-model consistency pass. A failed check blocks the next external review until repaired or presented to the user.

## Iteration Ledger

Maintain a machine-readable ledger in the operating system's temporary directory so the fresh reviewer cannot discover it while exploring the repository. Record:

- Iteration number and selected model/provider.
- A normalized fingerprint for every finding.
- Arbiter verdict and rationale.
- Applied fix and affected document section.
- Validation outcome.
- Stagnation and oscillation signals.

Fingerprint the concern, document location, and material repository evidence while ignoring wording and severity changes. This lets the loop recognize the same issue when a reviewer rephrases or rerates it.

Delete the ledger after the final report. If the process is interrupted, best-effort cleanup removes the temporary file; do not copy it into the repository or include it in a later review prompt.

## Convergence and Pause Conditions

The run converges only when the latest fresh iteration satisfies all of these conditions:

1. The reviewer reports no P0 or P1 findings.
2. Every accepted finding has been applied successfully.
3. No `needs-user-decision` item remains.
4. Document validation passes.

P2 through P4 findings do not prevent convergence when the arbiter rejects them. If the arbiter accepts one, apply it and run another fresh iteration.

Pause without claiming convergence when:

- The same material finding survives three consecutive iterations.
- Reviewers oscillate between incompatible recommendations or a document section returns to a previously rejected state.
- The configured iteration ceiling is reached. The absolute ceiling is 20.
- The configured model or provider fails.
- A fix requires unauthorized file changes.
- Validation cannot be restored without user judgment.

Age and elapsed time alone do not determine convergence.

## Review-Only Mode

`--review-only` runs:

1. One fresh external review.
2. One arbiter pass.
3. A structured report of accepted, rejected, and user-decision findings.

It performs no edits, starts no additional iteration, and does not claim that the documents converged.

## Final Output

Report one status:

- `Converged`
- `Paused`
- `Review only`

Include:

- Documents reviewed and whether paired traceability was available.
- Review model and routed provider.
- Arbiter and selection reason.
- Iterations completed.
- Accepted, rejected, fixed, and user-decision counts by severity.
- Validation commands or checks and their outcomes.
- Remaining risks and rejected lower-severity observations that merit visibility.
- Final document diff relative to the captured baseline.
- Exact pause reason and next action when convergence was not reached.

Never include sensitive values or the full internal ledger.

## Components

```text
skills/plan-review/
|-- SKILL.md
|-- helpers/
|   |-- plan_review_state.py
|   `-- test_plan_review_state.py
`-- references/
    |-- review-contract.md
    `-- preference-schema.md
```

Responsibilities:

- `SKILL.md`: orchestration, dispatch, arbitration, fixing, validation, and user interaction.
- `helpers/plan_review_state.py`: baseline capture, finding fingerprints, temporary ledger management, convergence classification, and mutation-scope checks.
- `references/review-contract.md`: reviewer rubric, severity definitions, structured finding schema, generic arbiter rubric, and final report schema.
- `references/preference-schema.md`: supported settings, precedence, model routing, arbiter discovery, and examples.

The helper is deterministic and must not edit reviewed documents or Git state.

## Cross-Skill Interfaces

- Read model/provider mappings and read-only CLI templates from `shared/model-defaults.md`.
- Reuse shared delegation mechanics for prompt delivery, timeout handling, and platform portability.
- Follow `shared/skill-context.md` for preference discovery and persistence.
- Keep `/codereview` responsible for implementation review.
- Leave final document commits to `/commit`.
- Generate the Codex collection through the existing adapter; do not maintain a divergent Codex workflow manually.

## Error Handling

| Condition | Behavior |
|---|---|
| No document supplied | Ask for at least one spec or plan path. |
| More than two documents supplied | Stop and ask the user to choose the coupled review unit. |
| Document missing or unreadable | Stop and identify the path. |
| Two document roles are ambiguous | Ask which is the specification and which is the plan. |
| Model identifier unknown or ambiguous | Ask for a registered or provider-qualified model. |
| Selected CLI/model unavailable | Stop and ask whether to choose another model. |
| Multiple arbiters discovered | Ask with ranked evidence and a recommendation. |
| No arbiter discovered | Use the host/base generic arbiter and announce the fallback. |
| Reviewer output malformed | Retry the same model once with the schema error; stop if it remains malformed. |
| Reviewer reports no findings | Continue to validation and apply the convergence rules. |
| Fix conflicts with current document text | Re-read the document and re-adjudicate; never force the stale edit. |
| Non-target file changes during the run | Pause, preserve all changes, and report the mutation-scope violation. |
| Temporary ledger cleanup fails | Warn without exposing ledger contents or blocking the final report. |

## Testing Strategy

### Deterministic Helper Tests

- Capture clean and dirty document baselines without mutation.
- Fingerprint semantically identical findings despite wording or severity changes.
- Preserve distinct findings that share a section but require different fixes.
- Classify converged, continuing, stagnated, oscillating, capped, and paused states.
- Keep ledgers outside the repository and remove them on completion.
- Detect non-target mutations relative to the captured baseline.

### Skill Contract Tests

- Require all supported arguments and the one-document warning.
- Verify configuration precedence and the 20-iteration hard ceiling.
- Verify model-only routing and provider-qualified identifiers.
- Verify repository-wide read-only reviewer access and fresh-session rules.
- Verify arbiter discovery, ranked ambiguity handling, and host fallback.
- Verify all three verdicts and accepted-finding-only mutation.
- Verify `--review-only` is non-mutating and single-pass.
- Verify the reviewer prompt excludes prior findings and ledger paths.

### Scenario Tests

Use deterministic fake reviewer and arbiter outputs to exercise:

- A clean first-pass convergence.
- Accepted P1 and P3 fixes followed by a clean fresh pass.
- Rejected lower-severity findings that do not block convergence.
- A user-decision pause after other accepted fixes are applied.
- Repeated rephrasing that triggers stagnation.
- Contradictory recommendations that trigger oscillation.
- Model failure without provider fallback.
- A requested fix outside the authorized document set.

### Distribution Tests

- Ensure `plan-review` appears in Claude and Codex plugin manifests and documentation.
- Regenerate the Codex collection and compare it with committed output.
- Verify Claude and Codex skill-context paths are adapted correctly.
- Run helper and contract tests on supported Windows and POSIX CI environments.

## Acceptance Criteria

The design is satisfied when:

1. `/plan-review` accepts either one document or a coupled spec-and-plan pair and warns when only one is supplied.
2. A model identifier deterministically routes to Codex or Claude without a separate reviewer setting.
3. Every iteration uses a new read-only reviewer session with access to the entire repository and no prior-round context.
4. Repository-specific arbiters are discovered and ranked; ambiguous choices are presented to the user with a recommendation.
5. The host/base model applies a generic arbiter rubric when no repository agent is suitable.
6. Only accepted findings are applied, only supplied documents are edited, and pre-existing changes are preserved.
7. User-decision findings pause the loop after other unambiguous fixes from the round are applied.
8. Convergence requires no P0/P1 findings, no unapplied accepted findings, no pending user decisions, and successful validation.
9. Stagnation, oscillation, model failure, unauthorized scope expansion, and the 20-iteration ceiling pause without a false convergence claim.
10. `--review-only` performs one non-mutating review and arbitration pass.
11. Skill-context preferences can set the review model, arbiter behavior, and loop defaults with invocation arguments taking precedence.
12. The temporary ledger remains outside reviewer-visible repository context and is removed after the run.
13. The generated Codex collection remains behaviorally equivalent to the Claude source workflow.
