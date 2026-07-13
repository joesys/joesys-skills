# Plain-Language Commit Messages Design

**Date:** 2026-07-13
**Status:** Approved

## Purpose

Make `/commit` produce messages that a teammate can understand without the
current session, issue tracker, or recent project history. The author should
also be able to return years later and understand why the commit exists, what
changed, and what still needs attention.

The existing Conventional Commit subject and three-part body remain intact.
This change improves how each part is written rather than replacing the
structure.

## Problem

The current skill asks for enough per-file detail that a reader can understand
every substantive change without reading the diff. Combined with domain-heavy
source material, that instruction can produce accurate but reader-hostile
messages: internal gate names, ceremonial metaphors, hashes, counts, and code
identifiers appear before their meaning is explained.

The supplied failing example demonstrates the problem. Its facts are useful,
but phrases such as "development-vintage mint," "lifecycle deaths," and
"suspect fusion census" assume context that future readers will not have.

## Scope

The implementation will:

1. Add a plain-language writing standard to the canonical commit skill.
2. Apply that standard to the subject, intent paragraph, changes summary, and
   AI review.
3. Replace the expectation of near-exhaustive diff narration with selective,
   outcome-focused detail.
4. Add one before-and-after example based on the supplied real failure.
5. Add a final durable-reader check before a commit message is used.
6. Update the README description and regenerate the Codex skill collection.
7. Add contract tests for the new behavior.

## Design

### Preserve the existing structure

Commit messages continue to use:

```text
type(scope): description

Intent paragraph.

[--- Changes ---]

- Meaningful change summary.

[--- AI Review (<model name>) ---]

Plain assessment of risks, trade-offs, and remaining work.
```

Conventional Commit types and scopes remain unchanged. The fixed body retains
the reasoning and review information used by the repository's devlog,
retrospective, and handbook workflows.

### Write for a durable reader

The skill will define the reader as a teammate who understands the project in
general but does not know today's task, internal shorthand, or recent session
history. It will require ordinary language, active voice, and enough context to
make unfamiliar terms meaningful.

Technical terms are not forbidden. When a precise term, identifier, hash, or
statistic matters, the message will explain what it represents and why the
reader should care. Internal gate names, acronyms, and code names will be
expanded or explained on first use.

Metaphors, slogans, ceremonial language, and dramatic descriptions will not be
used in place of concrete actions and outcomes.

### Apply the standard to every section

The subject will name the concrete outcome. Evidence identifiers and internal
process labels belong in the body when they are useful, not at the expense of
an understandable summary.

The intent paragraph will explain:

- the problem or need;
- the outcome of the change; and
- why the change matters.

The changes section will summarize observable outcomes and important technical
decisions. It may be organized by file or category, but it will not inventory
every edited line or repeat the diff. Counts, paths, symbols, and hashes will
be included only when they provide useful evidence or traceability.

The AI review will state strengths, risks, trade-offs, and follow-up work
directly. It will avoid promotional, theatrical, or self-congratulatory prose.

### Add a durable-reader check

Before committing, the skill will require a final reread using this question:

> Could a teammate unfamiliar with this task, or the author returning years
> later, understand why this commit exists, what changed, and what still needs
> attention without the issue tracker or session history?

If the answer is no, the message must be rewritten before the commit is
created.

### Show one real before-and-after example

The skill will contrast the supplied reader-hostile subject with a concrete
alternative:

```text
Before: feat(research): the Gate-6 development-vintage mint — fingerprint 14d908e0
After:  feat(research): record the July 13 development data snapshot
```

The body example will preserve the important overwrite incident and remaining
risk in plain language:

```text
The snapshot-generation script still uses a manually updated output date. It
initially overwrote the July 12 snapshot, which was restored exactly before the
new snapshot was saved under July 13. The date handling should be fixed before
this becomes a routine process.
```

The example demonstrates translation, not information loss: the previous
record was protected, the new record was saved correctly, and the remaining
automation risk is explicit.

## Testing Strategy

The user's supplied commit message is the failing behavioral baseline. Before
editing the skill, a focused contract test will also fail because the current
skill does not define a durable reader, reject unexplained shorthand, or
require the final readability check.

Implementation will follow red-green-refactor:

1. Add `tests/test_commit_skill_contract.py` with focused assertions for the
   agreed writing contract.
2. Run it and confirm it fails for the missing plain-language behavior.
3. Make the smallest canonical skill and README changes that satisfy the
   contract.
4. Run the focused test again and confirm it passes.
5. Regenerate `codex-skills/` with
   `python scripts/codex_adapter.py codex-skills --force`.
6. Run the generated-tree freshness test and the full repository suite.
7. Inspect the generated commit skill to confirm the example and writing rules
   remain readable after ASCII adaptation.

The test will protect behavior without attempting to ban words through a
jargon dictionary. Mechanical jargon detection would reject legitimate domain
terms and would not prove that necessary context was explained.

## Files Expected to Change

- `skills/commit/SKILL.md`: canonical writing rules and example.
- `tests/test_commit_skill_contract.py`: plain-language behavior contract.
- `README.md`: user-facing description of the commit-message standard.
- `codex-skills/commit/SKILL.md`: regenerated Codex output.
- `docs/superpowers/specs/2026-07-13-plain-language-commit-messages-design.md`:
  this approved design.
- A later implementation plan under `docs/superpowers/plans/`.

## Non-Goals

- No change to Conventional Commit syntax or the three body sections.
- No change to decomposition, OneFlow grouping, retroactive grouping, or branch
  naming.
- No change to push authorization, signing recovery, or secret checks.
- No change to devlog scrap capture.
- No automated vocabulary blacklist or project-specific glossary.
- No manual edits to generated `codex-skills/` files.

## Acceptance Criteria

- The skill explicitly writes for teammates without current-task context and
  for authors returning years later.
- Unfamiliar acronyms, gate names, code names, identifiers, and statistics are
  explained when they are necessary.
- Subjects describe concrete outcomes instead of relying on metaphor or
  internal ceremony.
- The changes section prioritizes outcomes and decisions over exhaustive diff
  narration.
- The AI review states risks and follow-up work in direct, ordinary language.
- The durable-reader check runs before the commit is created.
- The real before-and-after example preserves important facts while becoming
  understandable without the original session.
- Focused tests, generated-tree freshness checks, and the full repository test
  suite pass.
- Unrelated untracked files remain untouched.
