---
name: plan-review
description: "Use when the user wants to review, stress-test, or iteratively refine a specification, an implementation plan, or paired planning documents before implementation begins."
---

# Plan Review

Improve planning documents through a separated review, adjudication, fix, and
fresh-review loop grounded in the complete repository.

## Out of Scope

This skill MUST NOT:

- Review ordinary implementation defects; use `/codereview` for code findings
  that do not invalidate the documents.
- Perform visual-design fidelity review.
- Implement the reviewed plan.
- Edit any file other than the supplied documents.
- Commit, push, stash, reset, clean, or rewrite Git state.
- Resume a reviewer session or expose prior findings to a fresh reviewer.
- Silently replace an unavailable model or provider.
- Reproduce credentials, tokens, private keys, personal data, or sensitive
  values in prompts, findings, logs, or documents.

## Invocation

`/plan-review <document> [other-document] [options]`

Options:

- `--model <MODEL>` selects the review model and therefore its provider.
- `--arbiter <NAME|auto|host>` selects an arbiter or discovery behavior.
- `--review-only` runs one non-mutating review and arbitration pass.
- `--max-iterations <N>` lowers the ceiling; valid values are 1 through 20.

Accept one or two Markdown documents. When one is supplied, warn exactly:

> Reviewing one document only. For stronger coverage, provide both the
> specification and implementation plan so requirement traceability and
> cross-document contradictions can be checked.

Continue after the warning. With two documents, review them together. Infer
their roles from filenames, headings, and content; ask when the roles remain
ambiguous.

## Preflight

Before dispatch:

1. Read `references/review-contract.md` completely.
2. Read `references/preference-schema.md` completely.
3. Read `shared/model-defaults.md`, `shared/delegation-common.md`, and
   `shared/skill-context.md` completely, resolving each path from the plugin
   root.
4. Load shared and plan-review-specific preferences using the skill-context
   protocol. Invocation arguments override every saved setting.
5. Resolve the repository root and document paths; reject missing, duplicate,
   external, or more-than-two documents.
6. Resolve the model through the explicit registry. Ask for a provider-qualified
   identifier when a bare model is unknown or ambiguous.
7. Verify the configured CLI is available. If it is not, stop and ask whether
   the user wants another model; never fail over automatically.
8. Resolve `helpers/plan_review_state.py` from this skill directory to an
   absolute path and retain it as `<STATE_HELPER>`. The user's project working
   directory does not contain this helper.
9. Run the deterministic helper's `start` command and retain its ledger path
   only in host context:

```text
python <STATE_HELPER> start --repo <repository-root> --document <first-document> [--document <second-document>] --max-iterations <N>
```

The helper stores the ledger in the operating-system temporary directory,
outside the repository. Never include that path or ledger content in a reviewer
prompt.

## Model Routing

The model is the reviewer selector. There is no separate reviewer setting.
Resolve known models and provider-qualified custom models exactly as defined in
`references/preference-schema.md` and `shared/model-defaults.md`.

Layer the chosen model onto the provider's read-only command template:

- Codex CLI: use `--sandbox read-only`; start a new `codex exec` process.
- Claude CLI: use `--permission-mode plan`; start a new non-interactive process.

Use the platform-adaptive temp-file-and-stdin protocol from shared delegation
guidance with a 600000ms timeout. Do not request or capture a resumable session
for later use. Delete prompt and response temp files after the round is recorded.

## Fresh Reviewer Prompt

Every iteration starts a new process or session. Never resume. Construct the
prompt only from current repository state, supplied documents, applicable
repository guidance, and `references/review-contract.md`:

```text
You are an independent senior reviewer evaluating planning documents before
implementation. Review the supplied specification, implementation plan, or
paired documents as one execution design.

Run from the repository root in read-only mode. You may inspect any file in the
repository, including files not named or linked by the documents. Use repository
truth to test feasibility and consistency, but report only findings that
materially affect the supplied documents.

Evaluate internal coherence, requirement completeness, spec-to-plan
traceability when both documents exist, technical feasibility, scope discipline,
architecture, ownership, state and failure transitions, security, privacy,
migration, rollback, operations, testing, and measurable acceptance criteria.

Do not report ordinary code defects, edit files, or reproduce sensitive values.
Follow the Reviewer Output Schema in the supplied review contract. Return one
JSON object and no prose outside it.

Documents:
- resolved document paths are inserted here at runtime
```

MUST NOT include prior findings, arbiter verdicts, prior fixes, defenses,
iteration counts, ledger paths, or previous reviewer output. A malformed response
gets one new same-model retry that names only the schema validation error. If the
retry remains malformed, stop and ask the user whether to select another model.

## Arbiter Discovery

Resolve an arbiter in this order:

1. Explicit `--arbiter`.
2. Saved plan-review arbiter preference.
3. Repository discovery for `auto`.
4. Host/base model with the generic arbiter rubric.

For discovery, inspect `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/`,
`.claude/agents/`, `.codex/agents/`, `.gemini/`, and canonical role documents
linked from them. Rank roles with explicit responsibility for technical
leadership, architecture, planning, project standards, implementation quality,
or final review. Prefer configured names and canonical role instructions over
thin host adapters.

When one candidate is clearly strongest, announce its name and evidence. When
several are plausible, present a numbered ranked list, mark the strongest as
`(Recommended)`, include the host/base fallback, and wait for the user's
selection. Offer to save the selection through the skill-context protocol.

If none exists, announce that the host/base model will use the Generic Arbiter
Rubric. Absence of a repository agent is not an error.

## Arbitration

Give the selected arbiter the current reviewer JSON, current documents, relevant
repository evidence, applicable preferences, and the Arbiter Output Schema. Do
not give it authority to change loop policy or mutation scope.

The arbiter returns exactly one `accepted`, `rejected`, or
`needs-user-decision` verdict per finding with the required rationale and change.
The arbiter MUST NOT edit files.

Treat findings as evidence, not authority. Accept P2 through P4 only when they
materially improve correctness, feasibility, consistency, safety, or execution
clarity. Reject cosmetic churn.

## Applying Accepted Findings

The host applies every unambiguous accepted finding and only the supplied
documents may be edited. Before each edit, re-read the target section and verify
that it still matches the reviewed state. Preserve pre-existing edits.

Apply accepted findings before handling `needs-user-decision` items. Then pause,
present each decision with options and the arbiter recommendation, and wait. If
a valid fix requires another file, pause and request explicit scope expansion;
do not edit that file.

MUST NOT commit. MUST NOT push. MUST NOT stash, reset, clean, or overwrite
worktree state.

## Validation

After edits, verify:

- Documents are readable and structurally complete.
- Referenced files, symbols, commands, and links exist where verifiable.
- Requirement identifiers and acceptance criteria remain synchronized.
- Plan tasks cover applicable specification requirements.
- Terminology and architecture remain consistent.
- No accidental placeholders or unresolved markers were introduced.
- Pre-existing edits remain present.
- Only the supplied documents changed relative to the helper baseline.

Run deterministic checks first, then a focused host-model consistency pass. Do
not start another reviewer while validation is failing.

Write the current review, verdicts, applied finding ids, and validation result to
a temporary JSON file in the operating-system temporary directory outside the
repository. Record it through:

```text
python <STATE_HELPER> record --ledger <ledger-path> --iteration <iteration-json>
```

Follow the helper classification exactly:

- `continue`: delete round temp files and launch a completely fresh reviewer.
- `converged`: stop the loop and prepare the final report.
- `paused`: stop, preserve documents, and report the exact reason and next action.

Convergence requires a fresh review with no P0 or P1, no accepted findings remain
that require another pass, no pending user decision, and passing validation. Pause on
an unapplied accepted finding, three consecutive iterations of the same material
finding, oscillation, model failure, non-target mutation, validation failure, or
the 20-iteration absolute ceiling.

## Review-Only Mode

`--review-only` performs one fresh external review and one arbiter pass. It MUST
NOT edit files, record a fix iteration, or launch another reviewer. It MUST NOT
claim convergence. Report adjudicated findings and clean up temporary state.

## Final Report

Use the Final Report Contract. Report `Converged`, `Paused`, or `Review only`;
documents and paired-traceability status; model/provider; arbiter and selection
reason; iteration count; severity and verdict counts; validation evidence;
remaining risks; final diff relative to the baseline; and the exact next action.

Generate the final document diff before deleting the ledger:

```text
python <STATE_HELPER> diff --ledger <ledger-path>
```

In a `finally`-equivalent cleanup step, delete reviewer prompt/response files,
iteration JSON, and the ledger:

```text
python <STATE_HELPER> finish --ledger <ledger-path>
```

If cleanup fails, warn without printing ledger content. Never include sensitive
values or the full internal ledger in user output.

## Error Handling

| Condition | Action |
|---|---|
| No document | Ask for at least one spec or plan path. |
| Missing, duplicate, external, or more than two documents | Stop and identify the invalid input. |
| Ambiguous document roles | Ask which is the spec and which is the plan. |
| Unknown or ambiguous model | Ask for a registered or provider-qualified model. |
| CLI or model unavailable | Stop and ask whether to select another model. |
| Multiple plausible arbiters | Ask with ranked evidence and a recommendation. |
| No repository arbiter | Use host/base generic arbitration and announce it. |
| Malformed reviewer output twice | Stop and offer model selection. |
| Stale edit target | Re-read and re-adjudicate; never force the edit. |
| Non-target change | Pause, preserve all work, and report affected paths. |
| Ledger cleanup failure | Warn without exposing contents. |
