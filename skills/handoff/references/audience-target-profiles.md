# Handoff Audience and Target Profiles

Audience answers **who needs the handoff**. Target answers **which runtime will
consume it**. They are independent selections applied to one canonical artifact
schema.

## Audience Profiles

| Audience | Assumptions | Required emphasis |
|---|---|---|
| `self` | Same operator, project, and preferences in a fresh AI session | Operational continuity, established shorthand, unresolved state, and the exact next action |
| `agent` | Independent agent with no hidden prior context | Authority, mutation scope, inputs, constraints, deliverable, completion criteria, and report-back format |
| `human` | Another person will orient, review, or continue the work | Rationale, ownership, review points, judgment calls, and the safest reading order |

### `self`

Default profile. Assume the operator understands project vocabulary, but do not
assume the fresh AI session has prior conversation context. Keep Audience Notes
short and focus on where to restart. It is acceptable to reference established
project instructions by relative path.

### `agent`

Treat the recipient as an independent worker. Audience Notes must state:

- What the agent is authorized to read, modify, or execute.
- What it must not modify or infer.
- The expected deliverable and completion criteria.
- Required verification evidence.
- The report-back format, including blockers and residual risk.
- Which actions still require direct human authorization.

Do not rely on the sending session's preferences, tool names, or implicit
authority.

### `human`

Optimize for orientation and judgment rather than autonomous execution. Explain
why the current approach was chosen, who owns unresolved decisions, what should
be reviewed carefully, and what may be skimmed. Replace agent execution language
with clear suggested actions. Preserve technical commands only when they help the
human verify state. The skill's Write for Humans rule applies to the whole
artifact.

## Target Profiles

| Target | Bootstrap-only differences |
|---|---|
| `auto` | Detect the current host and use it; fall back to `generic` when detection is inconclusive |
| `claude` | Use Claude Code terminology and point to applicable `CLAUDE.md` guidance |
| `codex` | Use Codex skill terminology, applicable `AGENTS.md`, and active sandbox and approval policy |
| `antigravity` | Use Antigravity terminology and point to applicable `AGENTS.md` or `GEMINI.md` guidance |
| `generic` | Use no client-specific commands, paths, tools, memory locations, or capability assumptions |

Target profiles may change only:

1. The `source_host` and `target_host` metadata values.
2. Invocation examples shown to the user.
3. The Target Bootstrap section.

They must not fork, reorder, add, or remove the canonical body sections.

### `auto`

Resolve to the current host when the runtime is evident. If detection is
uncertain, resolve to `generic` and say so in the save confirmation. Never guess
a named host from repository files alone.

### `claude`

- Refer to the skill as `/handoff`.
- Tell the reader to follow applicable `CLAUDE.md` instructions.
- Use host-native tools without embedding Claude transcript or memory paths.
- Do not assume a specific Claude model or subagent availability.

### `codex`

- Refer to the adapted skill as `$handoff`.
- Tell the reader to follow applicable `AGENTS.md` instructions.
- Respect the active sandbox and approval policy rather than prescribing one.
- Do not require Claude model aliases, Claude tool names, or unavailable
  per-agent model selection.

### `antigravity`

- Refer generically to activating the handoff skill unless the installed
  Antigravity surface provides a stable invocation alias.
- Tell the reader to follow applicable `AGENTS.md` or `GEMINI.md` instructions.
  Antigravity reads both.
- Do not depend on Antigravity conversation storage or transcript paths.
- Do not prescribe a model, approval mode, or subagent topology.

### `generic`

- Say "load this handoff" rather than naming a client command.
- Say "project instructions" rather than naming an instruction file.
- Describe actions and evidence without host-specific tool names.
- Treat runtime capabilities as unknown until inspected.

## Composition Examples

| Invocation intent | Audience | Target | Result |
|---|---|---|---|
| Default fresh session | `self` | `auto` | Concise checkpoint for the same operator on the current host |
| Move personal work from Claude to Codex | `self` | `codex` | Same-operator context with a Codex bootstrap |
| Delegate implementation to Antigravity | `agent` | `antigravity` | Explicit authority and report-back contract with an Antigravity bootstrap |
| Hand work to a teammate | `human` | `generic` | Rationale and review guidance without agent instructions |

## Stability Rule

Keep runtime bootstraps deliberately small. Host capabilities and commands
change faster than the handoff schema. Permanent client behavior belongs in the
client's own instructions or adapter, not in the artifact body.
