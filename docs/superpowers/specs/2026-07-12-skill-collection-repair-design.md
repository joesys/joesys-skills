# Skill Collection Repair Design

**Date:** 2026-07-12
**Status:** Awaiting implementation approval

## Purpose

Repair six confirmed behavioral defects shared between the canonical `skills/`
tree, the generated `codex-skills/` tree, and their adapter/runtime support.
The repair keeps `skills/` and `shared/` as the source of truth and continues to
generate `codex-skills/` deterministically.

## Scope

The implementation will fix exactly these findings:

1. `plan-review` cannot reliably resolve shared files or its state helper.
2. `agy_adapter.py` invokes current Antigravity CLI with an obsolete empty
   positional prompt and documents obsolete non-TTY behavior.
3. Generated resource paths are correct, but their path-depth explanations
   still describe the canonical layout.
4. Generated `$preferences <skill-name>` validates against the canonical
   `skills/<skill-name>/` layout instead of sibling generated skills.
5. ASCII normalization deletes meaningful section markers, operators, diagram
   characters, and status symbols.
6. Context-free `.claude` path replacement creates contradictory Codex prose.

The lower-priority dashboard namespace, Codex flag-description, and ignored
legacy-install observations from the audit are not part of these six repairs.

## Design

### Canonical skill corrections

`skills/plan-review/SKILL.md` will follow the repository's canonical resource
convention: shared files are named as `shared/...` and explicitly resolved from
the plugin root. Before any state-helper command, the host will resolve
`helpers/plan_review_state.py` from the plan-review skill directory to an
absolute path. Every example command will use a `<STATE_HELPER>` placeholder so
it remains valid when the skill runs from a user's project directory.

Platform-specific explanatory prose will be made host-neutral where the same
source sentence must serve both Claude and generated Codex documentation. The
canonical Claude behavior remains explicit where it is operationally required.

### Antigravity compatibility wrapper

The adapter remains as a compatibility wrapper because it can support both old
and current `agy` versions. It will invoke `agy ... -p` without appending an
empty positional prompt. The user's prompt remains on stdin:

- Current `agy` can emit the response directly; the wrapper forwards stdout.
- Older affected versions can still fall back to SQLite response recovery.
- Error text will describe the SQLite parser as a legacy fallback rather than
  claiming current `agy` always loses non-TTY output.

Tests will assert the exact subprocess argument vector and ensure no empty
prompt argument is introduced.

### Codex adapter corrections

The adapter will continue to generate an ASCII-only `SKILL.md`, but it will map
meaningful characters instead of silently deleting them. Required mappings
include:

| Source | ASCII output |
|---|---|
| `§` | `Section` |
| `±` | `+/-` |
| `·` | `*` |
| box-drawing lines and junctions | `-`, `|`, and `+` |
| warning/check/pause symbols | `WARNING`, `yes`, and `paused` |

Generated path guidance will describe the generated collection layout: sibling
resources are resolved relative to the skill directory, one level up at the
collection root. Canonical `skills/<skill-name>/SKILL.md` validation will become
`../<skill-name>/SKILL.md` in generated skills.

Cross-host prose that must preserve both Claude and Codex names will no longer
be passed through a blind `.claude/skill-context` replacement. Host-current
instructions will use neutral wording or an explicit adapter rule so generated
text never states that Claude reads `.codex/` paths.

### Generated artifacts

Only canonical sources, shared documents, adapter code, and tests are edited by
hand. `codex-skills/` is regenerated with:

```powershell
python scripts\codex_adapter.py codex-skills --force
```

No generated file receives a manual patch.

## Testing Strategy

Testing follows red-green-refactor:

1. Add failing contract tests for absolute plan-review helper resolution and
   canonical shared paths.
2. Add a failing Antigravity adapter test asserting `-p` is the final argument
   and `""` is absent.
3. Add failing Codex adapter tests for standalone resource depth, dynamic skill
   lookup, semantic ASCII mappings, and platform-label consistency.
4. Implement the smallest source and adapter changes that make those tests
   pass.
5. Regenerate `codex-skills/` and run focused tests.
6. Run `python -m pytest tests skills -q` and confirm the committed generated
   tree matches a fresh build.

The tests must validate behavior in a standalone generated collection, not only
inside this repository where canonical and generated resource trees coexist.

## Error Handling and Compatibility

- Missing plan-review assets stop with a clear path-resolution error before
  review dispatch.
- Antigravity direct stdout remains authoritative; SQLite parsing is attempted
  only when stdout is empty.
- ASCII conversion must never introduce non-ASCII output or erase an operator
  or section reference.
- Adapter rewrites remain deterministic and idempotent through fresh-build
  comparison tests.

## Non-Goals

- No changes to skill invocation names or frontmatter triggers.
- No dashboard configuration migration.
- No changes to Codex model defaults or repository-check policy.
- No deletion or migration of the ignored `codex/joesys-skills/` snapshot.
- No live paid model dispatch during automated verification.

## Acceptance Criteria

- All six findings have regression tests that fail before their fixes.
- `plan-review` resource and helper instructions work from an arbitrary project
  working directory.
- The Antigravity wrapper never supplies an empty positional prompt.
- Standalone Codex installs resolve sibling skills, shared files, and scripts
  without relying on the canonical repository tree.
- Generated `SKILL.md` files remain ASCII while preserving meaningful content.
- Generated documents contain no known Claude-to-Codex path contradictions.
- The focused and full test suites pass and the generated tree is fresh.
