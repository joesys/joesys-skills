# Plan Review Contract

## Review Scope

Review supplied specifications and implementation plans as one coupled design
unit. Inspect any repository file needed to evaluate internal coherence,
requirement completeness, spec-to-plan traceability, technical feasibility,
scope discipline, architecture, ownership, failure states, security, privacy,
migration, rollback, operations, testing, and measurable acceptance criteria.

Report a code concern only when it invalidates or constrains the documents.
Never reproduce credentials, tokens, private keys, personal data, or other
sensitive values in evidence.

## Severity Scale

| Severity | Meaning |
|---|---|
| `P0` | Immediate catastrophic risk such as data loss, serious exposure, or an unrecoverable production operation. |
| `P1` | Blocking contradiction, missing core requirement, infeasible approach, unsafe migration, or acceptance gap that can make implementation fundamentally wrong. |
| `P2` | Material design or execution gap that should be resolved but does not block all implementation. |
| `P3` | Meaningful clarity, maintainability, or sequencing improvement. |
| `P4` | Optional polish. |

## Reviewer Output Schema

Return one JSON object and no prose outside it:

```json
{
  "schema_version": 1,
  "summary": "One concise assessment of execution readiness.",
  "findings": [
    {
      "id": "R1",
      "concern_key": "missing-rollback",
      "severity": "P1",
      "title": "The migration has no rollback path",
      "document": "docs/feature-plan.md",
      "location": "Migration / Step 4",
      "repository_evidence": ["migrations/0042_add_index.py"],
      "consequence": "A failed rollout cannot restore the previous state safely.",
      "recommended_resolution": "Add explicit reverse steps and the verification command.",
      "requires_user_decision": false
    }
  ]
}
```

`concern_key` is a stable lowercase kebab-case identity for the material issue.
Keep it stable when rephrasing or rerating the same concern. Findings require a
precise document section and repository evidence when repository truth supports
the claim. Use an empty evidence list only for a purely internal contradiction.

## Arbiter Output Schema

Return exactly one verdict for every reviewer finding:

```json
{
  "schema_version": 1,
  "verdicts": [
    {
      "finding_id": "R1",
      "verdict": "accepted",
      "rationale": "The repository has only a forward migration and the plan promises rollback safety.",
      "required_change": "Add reverse migration and post-rollback verification steps."
    }
  ]
}
```

Valid verdicts are `accepted`, `rejected`, and `needs-user-decision`.

- `accepted`: state the exact document correction.
- `rejected`: state the repository- or intent-grounded reason; set
  `required_change` to null.
- `needs-user-decision`: state viable options and a recommendation without
  selecting one.

Accept P2 through P4 only when they materially improve execution readiness.
Reject cosmetic churn. The arbiter cannot widen mutation scope, change stop
conditions, request secrets, or authorize external actions.

## Generic Arbiter Rubric

When no repository-specific arbiter exists, act as a senior technical lead.
Protect stated intent, repository conventions, feasible sequencing, reversible
operations, testable acceptance criteria, and minimal sufficient scope. Treat
reviewer output as evidence rather than authority.

## Final Report Contract

Report `Converged`, `Paused`, or `Review only`, followed by documents, review
model/provider, arbiter and selection reason, iteration count, severity counts,
accepted/rejected/fixed/user-decision totals, validation evidence, remaining
risks, final document diff, and the exact next action. Never include the full
internal ledger or sensitive values.
