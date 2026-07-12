# joesys-skills

A collection of 21 agent skills for Claude Code and Codex: consult other AI
models, review code and plans, understand projects, improve engineering
workflows, and preserve or publish development work.

The repository is both a Claude Code plugin and a Codex plugin marketplace.
Canonical skills live under `skills/`; Codex-compatible copies are generated
under `codex-skills/`.

## Quick Start

| Host | Invoke a skill | Example |
|---|---|---|
| Claude Code | `/skill-name` | `/codereview --file src/main.py` |
| Codex | `$skill-name` | `$codereview --file src/main.py` |

The detailed examples below use Claude Code's `/skill-name` syntax. In Codex,
replace the leading `/` with `$`. Both hosts can also select a skill
automatically when the request matches its description.

### Claude Code

```text
/plugin marketplace add joesys/joesys-skills
/plugin install joesys-skills
```

### Codex

```powershell
codex plugin marketplace add joesys/joesys-skills
codex plugin add joesys-skills@joesys-skills
```

To pick up a new Codex release:

```powershell
codex plugin marketplace upgrade
```

## Choose a Skill

| Goal | Skill | What it does |
|---|---|---|
| Consult models | [`ai-council`](#ai-council) | Ask Claude, Codex, and Antigravity, then synthesize their views |
| Consult models | [`claude`](#claude) | Delegate a prompt to a separate Claude CLI session |
| Consult models | [`codex`](#codex) | Delegate a prompt to a separate Codex CLI session |
| Consult models | [`antigravity`](#antigravity) | Delegate a prompt to Google's Antigravity CLI |
| Review | [`codereview`](#codereview) | Run a comprehensive multi-domain code review |
| Review | [`quick-review`](#quick-review) | Scan quickly for P0-P2 correctness and security bugs |
| Review | [`readability-review`](#readability-review) | Grade how well code reads as a story |
| Review | [`human-review-guide`](#human-review-guide) | Build a decision-focused human reading order |
| Review | [`codebase-audit`](#codebase-audit) | Grade whole-codebase quality and velocity |
| Review | [`plan-review`](#plan-review) | Iteratively stress-test specs and implementation plans |
| Understand | [`explain`](#explain) | Explain a project, file, symbol, or feature in layers |
| Understand | [`handbook`](#handbook) | Generate a self-contained project handbook |
| Improve | [`dashboard`](#dashboard) | Build a deterministic project-health dashboard |
| Improve | [`retrospective`](#retrospective) | Facilitate an evidence-based development retrospective |
| Improve | [`interaction-review`](#interaction-review) | Grade human-AI collaboration and coach improvements |
| Improve | [`preferences`](#preferences) | Save shared and skill-specific personal preferences |
| Preserve and publish | [`handoff`](#handoff) | Create or resume a drift-aware semantic checkpoint |
| Preserve and publish | [`devlog`](#devlog) | Capture insights as scraps or development posts |
| Preserve and publish | [`export`](#export) | Convert Markdown, text, or code to PDF, HTML, or PNG |
| Preserve and publish | [`commit`](#commit) | Create structured Conventional Commits and OneFlow histories |
| Preserve and publish | [`ss`](#ss) | Turn recent screenshots into actionable context |

## Consult Other AI Models

Default model identifiers and CLI flags are centralized in
[`shared/model-defaults.md`](shared/model-defaults.md).

### ai-council

Consult Claude, Codex, and Antigravity in parallel on the same question, then
synthesize consensus, disagreements, and confidence. Results are saved by
default.

```text
/ai-council "Should we use PostgreSQL or MongoDB for user data?"
/ai-council --no-save "Quick question about caching strategies"
/ai-council --path ./notes "Compare REST and GraphQL for this use case"
```

### claude

Delegate code analysis, refactoring, or automated editing to Anthropic's Claude
Code CLI. The host presents Claude's response, evaluates it critically, and
supports latest or named-session resume.

```text
/claude "explain the auth flow in this repo"
/claude --model sonnet "analyze this function"
/claude --permission-mode acceptEdits "fix the lint errors"
/claude --effort max "analyze the architecture deeply"
/claude --bare "analyze without plugins or hooks"
/claude resume "follow up on that"
/claude resume my-review "continue that named session"
```

### codex

Delegate code analysis, refactoring, or automated editing to OpenAI's Codex
CLI. The skill captures the session identifier when available, evaluates the
response, and supports reliable session resume. The current default model is
`gpt-5.6-sol`.

```text
/codex "explain the auth flow in this repo"
/codex --model gpt-5.6-sol "analyze this function"
/codex --sandbox workspace-write "fix the lint errors"
/codex resume "follow up on the latest session"
/codex resume <SESSION_ID> "continue this specific session"
```

### antigravity

Delegate prompts to Google's Antigravity CLI (`agy`) and critically evaluate
the result. The included adapter forwards output from current `agy` releases
and retains compatibility recovery for affected older releases.

```text
/antigravity "explain the auth flow in this repo"
/antigravity resume "follow up on the latest session"
/antigravity resume <ID> "continue this specific session"
```

## Review Code and Plans

### codereview

Run parallel domain reviews across correctness, clean code, architecture,
reliability, security, performance, and story readability. Findings are grouped
from P0 to P4 and include concrete before-and-after fixes in the target
language.

| Domain | Focus |
|---|---|
| Correctness | Wrong logic, edge cases, null handling, races |
| Clean Code | Naming, duplication, nesting, focus, KISS/YAGNI |
| Architecture | Coupling, cohesion, layering, dependency direction |
| Reliability | Error handling, validation, resource safety |
| Security | Injection, secrets, authorization, data exposure |
| Performance | Complexity, N+1 queries, caching, allocation |
| Story Readability | Narrative flow and maintainable intent |

```text
/codereview                          # Current branch diff against its base
/codereview src/                     # Directory scan
/codereview --file src/main.py       # Single file
/codereview --pr 123                 # GitHub pull request
/codereview --commit abc123          # Specific commit
/codereview --min-severity P1        # Only P0-P1 findings
```

### quick-review

Run a fast correctness-and-security review using diff context and the host
model. It reports only P0-P2 findings, with no style nits or architecture
suggestions.

```text
/quick-review
/quick-review src/utils/
/quick-review --file src/main.py
/quick-review --pr 123
/quick-review --commit abc123
```

### readability-review

Grade code from 0 to 100 across eight weighted story-readability dimensions,
then provide thematic findings and concrete refactoring suggestions.

| Dimension | Weight |
|---|---:|
| Narrative Flow | 20% |
| Naming as Intent | 15% |
| Cognitive Chunking | 15% |
| Abstraction Consistency | 14% |
| Function Focus | 10% |
| Structural Clarity | 10% |
| Documentation Quality | 10% |
| No Clever Tricks | 6% |

```text
/readability-review
/readability-review src/
/readability-review --file src/main.py
/readability-review --pr 123
/readability-review --commit abc123
/readability-review --min-score 70
```

### human-review-guide

Turn a diff, PR, spec, configuration, or other artifact into a guided human
reading order. Content is classified as `DECIDE`, `READ`, `SKIM`, or `SKIP` so
the reviewer can spend judgment where it matters.

```text
/human-review-guide
/human-review-guide PR#123
/human-review-guide docs/spec.md
/human-review-guide --with-review     # Consume existing codereview findings
/human-review-guide --calibrate       # Re-run calibration questions
```

`--with-review` uses findings already present in the session; it does not
automatically invoke `codereview`.

### codebase-audit

Run a language-agnostic audit covering up to 12 quality criteria plus
development velocity. It combines parallel measurement agents, deterministic
metrics, industry benchmarks, letter grades, and actionable recommendations.

| Category | Criteria |
|---|---|
| Code quality | Maintainability, readability, consistency |
| Architecture | Modularity, evolvability, reliability |
| Engineering | Correctness, testability, performance |
| Operations | Operability, security |
| Readability | Story readability |
| Velocity | Commits, churn, throughput |

```text
/codebase-audit
/codebase-audit metrics
/codebase-audit analysis
/codebase-audit delta
/codebase-audit maintainability performance
/codebase-audit --static-only
```

### plan-review

Review a specification, implementation plan, or paired documents before
implementation. Each iteration uses a fresh read-only external reviewer, a
repository-aware arbiter, host-applied document fixes, and deterministic loop
state until the documents converge or a bounded pause condition is reached.

```text
/plan-review docs/feature-spec.md docs/feature-plan.md
/plan-review docs/feature-plan.md --model fable
/plan-review docs/feature-spec.md --arbiter petra
/plan-review docs/feature-plan.md --review-only
/plan-review docs/spec.md docs/plan.md --max-iterations 10
```

| Option | Behavior |
|---|---|
| `--model <MODEL>` | Select a registered or provider-qualified review model |
| `--arbiter <NAME\|auto\|host>` | Select the arbiter or its discovery mode |
| `--review-only` | Run one non-mutating review and arbitration pass |
| `--max-iterations <1-20>` | Lower the bounded iteration ceiling |

Plan review edits only the supplied Markdown documents. It does not implement
the plan or commit, push, stash, reset, or clean repository state.

## Understand and Document Projects

### explain

Analyze a project through five lenses: structure, behavior, domain and data,
external dependencies, and health and risk. The report progresses from a
30-second overview to deep traces and a fastest path to competence.

```text
/explain
/explain src/auth/
/explain src/auth/oauth.ts
/explain MyClassName
/explain "how does payment work?"
/explain --save
/explain src/api/ --save --path docs/
```

### handbook

Generate a self-contained project handbook for two audiences: an intermediate
programmer who needs a reference and a beginner who needs a guided walkthrough.
The workflow analyzes the project, interviews the user, writes the chapters,
and produces Markdown plus HTML under `docs/handbook/`.

```text
/handbook
/handbook src/auth
```

## Track Health and Improve Workflows

### dashboard

Build a self-contained HTML project-health dashboard for PMs and engineering
managers. Deterministic local-git metrics drive traffic lights across delivery,
health, and team lenses. Optional GitHub enrichment uses `gh`; GitLab remotes
degrade gracefully because GitLab enrichment is not implemented in v1. An
optional LLM narrative explains the lights but never changes them.

```text
/dashboard
/dashboard src/api
/dashboard --no-llm
/dashboard --no-host
/dashboard --no-llm --no-host
```

### retrospective

Facilitate an evidence-based retrospective with human check-ins. The workflow
mines git history, available conversation records, code quality, planning
documents, and tests, then produces discussion topics, actions, and a narrative.

```text
/retrospective
/retrospective --since 2026-03-15
/retrospective --since v1.0
/retrospective --since v1.0..v1.1
/retrospective --output docs/sprints/3/
/retrospective continue
```

### interaction-review

Analyze Claude Code JSONL conversation transcripts across prompt craft,
workflow efficiency, agentic leverage, error recovery, and context management.
The skill produces Markdown and HTML report cards with a prioritized coaching
roadmap and trend history.

```text
/interaction-review
/interaction-review session <uuid>
/interaction-review since 2026-05-01
/interaction-review trend
```

This skill specifically depends on Claude Code transcript storage even when the
collection itself is installed for both hosts.

### preferences

Capture shared communication, explanation, experience, and project preferences
plus skill-specific settings. Other skills can request first-contact setup when
preferences are absent; transactional workflows such as `commit` and `handoff`
use silent defaults instead of interrupting work.

```text
/preferences
/preferences show
/preferences reset
/preferences codereview
/preferences plan-review
```

## Capture, Transfer, and Publish Work

### handoff

Create a durable, host-neutral Markdown checkpoint for a fresh session, an
independent agent, or another human. Handoffs capture live repository state,
decisions, constraints, verification evidence, and one explicit next action
without copying raw conversation transcripts.

```text
/handoff
/handoff --full
/handoff --compact
/handoff --interactive
/handoff --for self --target codex
/handoff --for agent --target gemini
/handoff --for human --include-diff
/handoff --output notes/my-handoff.md
/handoff resume
/handoff resume .handoffs/<file>.md
```

| Setting | Values and behavior |
|---|---|
| Audience | `self`, `agent`, or `human`; default `self` |
| Target | `auto`, `claude`, `codex`, `gemini`, or `generic`; default `auto` |
| Detail | Operational by default, or `--full` / `--compact` |
| Drift | Resume classifies state as `exact`, `advanced`, `drifted`, or `unverifiable` |
| Output | `.handoffs/YYYYMMDD-HHMMSS-<slug>.md` unless overridden |

`--full` and `--compact` cannot be combined. The skill never commits, pushes,
publishes, or shares a checkpoint automatically, and it stops before mutation
when repository state has drifted.

### devlog

Capture development insights for budding programmers. Write mode reconstructs
the reasoning behind a topic, scrap mode records an insight quickly, and list
mode shows the backlog and published posts.

```text
/devlog "the recursive clone bug"
/devlog --since yesterday
/devlog --from-scrap recursive-fix
/devlog scrap "signing workaround"
/devlog scrap
/devlog scrap --from-context "adapter lesson"
/devlog list
```

### export

Convert Markdown, text, or code into PDF, HTML, PNG, or all three. Choose a
content scope (`full`, `summary`, or `1pager`) and a theme (`minimal`, `modern`,
or `dark`). PDF generation uses Pandoc and LuaLaTeX; PNG uses headless Chromium.

```text
/export report.md
/export report.md --format png --theme dark
/export report.md --scope summary --format all
/export utils.py --format html --theme dark
/export report.md --scope 1pager
/export report.md --orientation landscape
/export report.md --output ./out/
```

### commit

Create a Conventional Commit with an intent paragraph, per-file or per-category
change summary, and candid AI review. The workflow can decompose multi-unit
changes into a OneFlow Option 3 branch, group related recent commits with user
approval, and recover from an unresponsive 1Password signing agent by creating
an explicitly reported unsigned commit.

```text
/commit
```

The skill never pushes without express push-specific authorization.

### ss

Grab recent screenshots from a configured folder, infer intent, explain what is
shown, fix visible errors, adapt a project to a reference, or route the request
to a better-matched sibling skill.

```text
/ss
/ss huh
/ss fix
/ss 3
/ss 2 fix
/ss do this
/ss 3 make infographic plz
```

## Installation and Maintenance

### Standalone Codex Installation

To install the generated skills without the plugin marketplace into
`%USERPROFILE%\.codex\skills` or `%CODEX_HOME%\skills`:

```powershell
python scripts\install_codex_skills.py
```

### Clean Reinstall

```powershell
.\scripts\reinstall-plugin.ps1                 # Claude Code and Codex
.\scripts\reinstall-plugin.ps1 -Target codex   # Codex only
```

## Contributing Skills

Add or edit canonical skills under `skills/<skill-name>/`. Shared contracts and
resources belong under `shared/`.

```text
skills/
└── <skill-name>/
    ├── SKILL.md
    ├── references/     # Optional
    ├── helpers/        # Optional
    └── templates/      # Optional
```

Do not edit `codex-skills/` by hand. It is committed generated output served by
`.codex-plugin/plugin.json`. After changing canonical skills or shared files,
regenerate it:

```powershell
python scripts\codex_adapter.py codex-skills --force
```

Validate the adapter and committed generated tree:

```powershell
python -m pytest tests\test_codex_adapter.py -q
```

The `test_committed_codex_skills_match_fresh_build` guard fails when generated
output is stale. To run the complete collection checks:

```powershell
python -m pytest tests skills -q
```

## License

MIT
