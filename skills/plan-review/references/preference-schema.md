# Plan Review Preferences

## Precedence

Resolve settings in this order:

1. Invocation arguments.
2. Project-specific plan-review skill context.
3. Shared preferences.
4. Provider defaults from `shared/model-defaults.md`.
5. Built-in defaults.

## Supported Settings

| Setting | Default | Rules |
|---|---|---|
| Review model | `gpt-5.6-sol` | A known model routes to its registered provider. Unknown or ambiguous bare names require qualification. |
| Arbiter | `auto` | A repository agent name, `auto`, or `host`. |
| Preferred arbiters | Empty | Ordered names used to rank discovered repository agents. |
| Arbiter ambiguity | `ask` | Present ranked candidates, mark one recommended, and wait. |
| Maximum iterations | `20` | Accept values 1 through 20; never raise the absolute ceiling. |
| Fix accepted findings | `yes` | `--review-only` overrides this to no. |
| Fresh context each iteration | `yes` | Never resume reviewer sessions. |

## Example File

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

Claude reads `.claude/skill-context/plan-review.md`. The generated Codex skill
reads `.codex/skill-context/plan-review.md`.

## Model Routing

Use the explicit registry in `shared/model-defaults.md`:

| Model | Provider |
|---|---|
| `gpt-5.6-sol` | Codex CLI |
| `fable` | Claude CLI |

There is no separate reviewer setting. For a custom or ambiguous model, use
`codex:custom-model` or `claude:custom-model`. Never guess a provider from an
arbitrary name pattern and never fail over silently.

## Arbiter Discovery

Inspect repository guidance, host-specific agent adapters, and linked canonical
role documents. Rank roles responsible for technical leadership, architecture,
planning, project standards, implementation quality, or final review. Prefer a
configured preferred arbiter and canonical role instructions over thin adapters.

When several candidates are plausible, ask with a ranked list, explain why the
first is recommended, and include the host/base fallback. When none exists, use
the host/base generic arbiter without treating the absence as an error.
