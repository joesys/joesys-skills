# joesys-skills

Custom Claude Code skills and plugins.

## Installation

```
/plugin marketplace add joesys/joesys-skills
/plugin install joesys-skills
```

## Available Skills

### codex

Delegate prompts to OpenAI's Codex CLI for code analysis, refactoring, and automated editing. Critically evaluates Codex's output and supports session resume.

**Defaults:** `gpt-5.4` / `xhigh` reasoning / `read-only` sandbox

#### Usage

```
/codex "explain the auth flow in this repo"
/codex --model gpt-5.3 "analyze this function"
/codex --sandbox workspace-write "fix the lint errors"
/codex resume "follow up on that"
```

### gemini

Delegate prompts to Google's Gemini CLI for code analysis, refactoring, and automated editing. Critically evaluates Gemini's output and supports session resume with indexed session management.

**Defaults:** `gemini-3.1-pro-preview` / `plan` (read-only) approval mode

#### Usage

```
/gemini "explain the auth flow in this repo"
/gemini --model gemini-2.5-flash "quick analysis of this function"
/gemini --approval-mode yolo "fix the lint errors"
/gemini resume "follow up on that"
/gemini resume 3 "continue from that session"
/gemini sessions
```

### claude

Delegate prompts to Anthropic's Claude Code CLI for code analysis, refactoring, and automated editing. Critically evaluates Claude's output with special attention to shared blind spots (Claude evaluating Claude). Supports named session resume.

**Defaults:** `opus` / `high` effort / `plan` (read-only) permission mode

#### Usage

```
/claude "explain the auth flow in this repo"
/claude --model sonnet "quick analysis of this function"
/claude --permission-mode acceptEdits "fix the lint errors"
/claude --effort max "deep analysis of the architecture"
/claude --bare "analyze without plugins or hooks"
/claude resume "follow up on that"
/claude resume my-review "continue from that session"
```

### ai-council

Consult three frontier AI models (Claude, GPT, Gemini) in parallel on the same question. Automatically gathers relevant context, dispatches to all three, then synthesizes a structured analysis with consensus points, tensions, and a confidence matrix. Saves results by default.

#### Usage

```
/ai-council "Should we use PostgreSQL or MongoDB for our user data?"
/ai-council --no-save "Quick question about caching strategies"
/ai-council --path ./notes "Compare REST vs GraphQL for this use case"
```

### code-review

Dispatch 6 parallel domain-expert subagents to analyze code for violations across correctness, clean code, architecture, reliability, security, and performance. Produces a severity-grouped report (P0-P4) with concrete before/after fixes in the target language. Supports branch diffs, directory scans, single files, PR reviews, and commit reviews.

#### Analysis Domains

| Domain | Focus |
|---|---|
| Correctness | Actual bugs — wrong logic, off-by-one, null dereferences, race conditions |
| Clean Code | Naming, DRY (Rule of Three), nesting depth, function length, KISS/YAGNI |
| Architecture | Coupling, cohesion, layering violations, dependency direction, god classes |
| Reliability | Error handling, silent failures, resource leaks, missing validation |
| Security | Injection, hardcoded secrets, auth gaps, input sanitization, data exposure |
| Performance | Algorithmic complexity, N+1 queries, missing caching, unnecessary allocations |

#### Usage

```
/code-review                          # Review current branch diff vs. base
/code-review src/                     # Scan all files in a directory
/code-review --file src/main.py       # Review a single file
/code-review --pr 123                 # Review files changed in a GitHub PR
/code-review --commit abc123          # Review files changed in a specific commit
/code-review --min-severity P1        # Only show P1+ findings (combinable with any mode)
```

### explain

Dispatch 5 parallel domain-lens subagents to analyze a codebase across structure, behavior, domain & data, external dependencies, and health & risk. Produces a layered report from TL;DR to deep understanding with an orientation cheat sheet and fastest-path-to-competence recommendations. Supports whole projects, directories, single files, symbols, and natural language feature traces.

#### Analysis Lenses

| Lens | Focus |
|---|---|
| Structure & Entry Points | Module boundaries, organization pattern, entry points, dependency graph |
| Behavior — Key Workflows | End-to-end traces of the 3 most important workflows |
| Domain & Data | Data models, state transitions, domain glossary, storage mapping |
| External Dependencies | External services, infrastructure config, integration patterns |
| Health & Risk | Hotspots, churn, debt, test signals, git archaeology, onboarding path |

#### Usage

```
/explain                                  # Explain the whole project (default)
/explain src/auth/                        # Explain a directory/module
/explain src/auth/oauth.ts                # Explain a single file
/explain MyClassName                      # Explain a class/symbol
/explain "how does payment work?"         # Trace a feature across the codebase
/explain --save                           # Save report to docs/explain/
/explain src/api/ --save --path docs/     # Explain directory, save to custom path
```

### commit

Structured git commits following Conventional Commits with a three-part body (intent, changes, AI review). Supports OneFlow Option 3 branching for multi-commit changesets. Auto-recovers from 1Password signing failures.

#### Usage

```
/commit
```

## Adding More Skills

Add new skills under `skills/<skill-name>/` following the same structure:

```
skills/
└── <skill-name>/
    └── SKILL.md
```

## License

MIT
