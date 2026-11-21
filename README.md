# joesys-skills

A collection of 29 agent skills for Claude Code and Codex: turn rough ideas
into reusable prompts, consult other AI models, review code,
understand projects, improve engineering workflows, and preserve or publish
development work.

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
| Write prompts | [`prompt`](#prompt) | Turn rough thoughts into a copy-ready prompt and explain the improvements |
| Consult models | [`ai-council`](#ai-council) | Ask Claude, Codex, Antigravity, and Grok, then synthesize their views |
| Consult models | [`claude`](#claude) | Delegate a prompt to a separate Claude CLI session |
| Consult models | [`codex`](#codex) | Delegate a prompt to a separate Codex CLI session |
| Consult models | [`antigravity`](#antigravity) | Delegate a prompt to Google's Antigravity CLI |
| Consult models | [`grok`](#grok) | Delegate a prompt to xAI's Grok CLI |
| Review | [`codereview`](#codereview) | Run a comprehensive multi-domain code review |
| Review | [`quick-review`](#quick-review) | Scan quickly for P0-P1 correctness and security bugs |
| Review | [`readability-review`](#readability-review) | Grade how well code reads as a story |
| Review | [`human-review-guide`](#human-review-guide) | Build a decision-focused human reading order |
| Review | [`codebase-audit`](#codebase-audit) | Grade whole-codebase quality and velocity |
| Review | [`blast-radius`](#blast-radius) | Find what a change could break elsewhere, and prove the one fact that makes it safe |
| Review | [`security-audit`](#security-audit) | Find security flaws by reading the source, with four models, and teach the fix in one HTML report |
| Verify | [`create-verification-skill`](#create-verification-skill) | Generate a project skill that proves features in the running app |
| Verify | [`maintain-verification-skill`](#maintain-verification-skill) | Bring a `verify-<app>` skill and its feature map back in line with the app |
| Verify | [`create-formal-verification-skill`](#create-formal-verification-skill) | Check one promise of the code for every case in a stated scope |
| Verify | [`benchmark-checklist`](#benchmark-checklist) | Test a performance number with seven questions before you report it |
| Design | [`architect`](#architect) | Design the shape of new code from several candidates, then stop |
| Work | [`joesys-mode`](#joesys-mode) | Work on a coding task by 32 engineering principles and a step list |
| Understand | [`explain`](#explain) | Explain a project, file, symbol, or feature in layers |
| Understand | [`why`](#why) | Find why code is built the way it is, from the project's own record |
| Understand | [`huh`](#huh) | Re-explain the last answer in plain language with options, confidence, and unasked questions |
| Improve | [`retrospective`](#retrospective) | Facilitate an evidence-based development retrospective |
| Improve | [`interaction-review`](#interaction-review) | Grade human-AI collaboration and coach improvements |
| Preserve and publish | [`handoff`](#handoff) | Create or resume a drift-aware semantic checkpoint |
| Preserve and publish | [`devlog`](#devlog) | Capture insights as scraps or development posts |
| Preserve and publish | [`commit`](#commit) | Create structured Conventional Commits and OneFlow histories |
| Preserve and publish | [`restructure-commit`](#restructure-commit) | Group related recent commits into one OneFlow merge bubble |
| Preserve and publish | [`ss`](#ss) | Turn recent screenshots into actionable context |

## Write Better Prompts

### prompt

Turn rough, fragmented, or stream-of-consciousness input into a portable,
ready-to-copy prompt. The skill asks a focused question only when missing
information would materially change the result. It then explains what was
added, removed, reorganized, or assumed so the operator learns better prompting
habits over time.

```text
/prompt i need to explain our API migration to nontechnical managers, keep it short
/prompt login sometimes hangs, diagnose it but do not change anything
```

The skill writes the prompt and stops; it does not execute the generated task.

## Consult Other AI Models

Default model identifiers and CLI flags are centralized in
[`shared/model-defaults.md`](shared/model-defaults.md).

### ai-council

Consult Claude, Codex, Antigravity, and Grok in parallel on the same question,
then synthesize consensus, disagreements, and confidence. Results are saved
by default. Grok runs read-only, with the model from your own Grok settings.

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
`gpt-6.2-sol`.

```text
/codex "explain the auth flow in this repo"
/codex --model gpt-6.2-sol "analyze this function"
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

### grok

Delegate prompts to xAI's Grok CLI (`grok`) and critically evaluate the
result. Grok runs read-only in plan mode and uses the default model from
your own Grok settings. The skill chooses the session identifier before
the run, so resume is reliable, and it reports an answer that Grok cut
short.

```text
/grok "explain the auth flow in this repo"
/grok --model grok-4.7-build-fast "analyze this function"
/grok --effort high "review this design"
/grok resume "follow up on the last session"
/grok resume <SESSION_ID> "continue this specific session"
```

## Review Code

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
model. It reports only P0-P1 findings, with no style nits or architecture
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
/human-review-guide --calibrate       # Set your reviewer profile (role, focus, detail)
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

### blast-radius

Find what a change could break somewhere else, before it ships. A list of
callers is not the answer, because a search finds those in a second. The
skill looks where a search stops: the source of a library at its pinned
version, the moment when each piece runs, a database column, a file format,
a feature flag, generated copies of a file. Then it finds the one fact that
the change is safe because of, and proves it with a script that runs the
real code.

```text
/blast-radius                     # Current branch and uncommitted changes
/blast-radius --commit abc123     # One commit
/blast-radius --pr 123            # One pull request
/blast-radius drop the retry cap  # A change that is only planned
```

Every fact gets one of five proof levels: Said, Pointed, Walked, Ran, or
Reproduced. A reply without a run says `unproven`. The skill never changes
product code and never commits.

Adapted from pstack by Lauren Tan (MIT License).

### security-audit

Find the security flaws of a codebase by reading its source, and teach the
team how to stop making them. Four models take part. Two finders search
alone, and each may start helper agents of its own. The running model
checks every candidate against the code and writes the report. The other
frontier model reviews the report, and the two settle on a joint consensus
in at most two rounds. Where they still differ, the report prints both
views.

```text
/security-audit                          # The whole repository
/security-audit src/payments             # One folder
/security-audit --include config/local   # Also read a path that git ignores
/security-audit --out ~/audits/shop      # Save the run folder somewhere else
```

The result is one HTML file that works on a desktop and on a phone, with no
script. It is written for a beginner programmer who uses English as a
second language: an overall assessment, the main themes, a list by
priority, and for each finding the code, the explanation, the steps to
reproduce it, the fix as a diff, and how to avoid the mistake next time. A
script adds the code colours. It also checks that every code quote matches
the file it names, and that every diff with line numbers applies to the
code.

The skill only reads source. It sends no request to a running app, changes
no file in the project, and never opens a secret file. The other models run
in the background with no time limit, and a watch reports whether each one
is still working. A provider's safety filter can stop a model, and a model
can refuse the task. The skill then shows the message and does not retry by
itself. It continues with the other models, and the report names the model
that is missing. When both finders fail, the skill stops and writes no
report. Three scanner tools (Semgrep, Gitleaks, OSV-Scanner) are
used when they are installed. The skill shows how to install them and never
installs one. The report folder `.security-audit/` is kept out of git,
because it shows where the app is weak.

The method builds on ideas from Shannon by Keygraph. No text of Shannon is
copied.

## Verify Running Apps

### create-verification-skill

Generate a project-local skill, `verify-<app>`, that tells an agent how to
start the real app, use a feature the way a user does, and capture evidence.
The generated skill has six sections (Launch, Doctor, Drive, Evidence,
Cleanup, Helpers) and a feature map with one file per user-facing feature.

```text
/create-verification-skill
/create-verification-skill <app or folder>
```

The skill runs the generated skill once before it reports. Without that run,
it reports a draft. Every proof says `live` or `fake` for each outside
service it touched. The skill never reads secrets, never changes product
code, and never commits. In Claude Code the generated skill goes to
`.claude/skills/`; in Codex it goes to `.agents/skills/`.

Adapted from pstack by Lauren Tan (MIT License).

### maintain-verification-skill

Bring a `verify-<app>` skill and its feature map back in line with the app.
A feature map goes stale as soon as the app changes. The pass reads the
source of every feature, with one read-only helper agent for each feature
file. Then it drives every feature once in the real app, and it corrects
only what a run proved.

```text
/maintain-verification-skill
/maintain-verification-skill <skill name or folder>
```

The pass ends with one of three outcomes: `clean`, `changed`, or `blocked`.
It says how many features it drove out of how many. It edits only the
verification skill's own folder. A broken app is reported, never hidden in
the map. The corrections stay uncommitted. The skill asks once, before the
live pass, for every call that costs money.

Adapted from pstack by Lauren Tan (MIT License).

### create-formal-verification-skill

Check one promise of the code for every case in a stated scope, with a model
checker, a prover, or another verifier. A test checks the cases that someone
thought to write. This skill picks the place where a bug costs much and tests
rarely reach it: concurrency, retries, state machines, parsers, or unsafe
code. It verifies one property there and writes a project-local skill,
`formal-<area>`, that reruns the check when the code changes.

```text
/create-formal-verification-skill
/create-formal-verification-skill <area, file, or bug>
```

Each property must be seen to fail on a broken variant of the code. The check
command fails when the covered code changes, because a model checker reads
the model and not the code. Before it reports, the skill breaks the real code
on purpose, confirms that the generated skill catches the break, and restores
the code. It asks before it installs a tool, and it never changes product
code unless asked.

Adapted from pstack by Lauren Tan (MIT License).

### benchmark-checklist

Test a performance number before anyone reports it or acts on it. A number
can measure the load tool, a cache, an error path, or work that never ran.
The skill asks seven questions, and each answer must come from a run:

| # | Question | What it catches |
|---|---|---|
| 1 | Why not double? | A number with no known limit |
| 2 | Was it tuned? | Two configurations compared as two implementations |
| 3 | Did it break limits? | A result that the disk, the network, or the cores cannot give |
| 4 | Did it error? | Fast failures counted as fast work |
| 5 | Does it reproduce? | A gap smaller than the variation between runs |
| 6 | Does it matter? | A small part that is a tiny share of the whole |
| 7 | Did it even happen? | Work that never ran inside the timed region |

```text
/benchmark-checklist
/benchmark-checklist export is 30% faster on the large data set
```

The verdict is one of four words: faster, slower, no measurable difference,
or inconclusive. Every number carries its run count and its range. The skill
changes no product code and asks before it installs a tool.

Adapted from pstack by Lauren Tan (MIT License).

## Design Before Code

### architect

Design the shape of new code before anyone writes it: how a caller uses it,
the types, the function signatures, and the module boundaries. The first
design that comes to mind is rarely the best one. So the skill gets at least
two candidates that differ in their whole shape. One comes from a helper
agent of the host, and the others come from other models, called read-only
the way `/codereview` calls them. Each candidate works alone and writes the
caller's usage first. The skill checks each one against eight design red
flags, picks a base, and merges the best parts of the others into it.

```text
/architect a retry queue for failed webhook deliveries
/architect --local a plugin loader for report formats
/architect --save a cache for exchange rates
```

The result is a design package with nine sections, from the problem to the
first step to build. Then the skill stops. It writes no code file in the
project, and approval of a design is not approval to build it. `--local`
keeps every candidate on the host and calls no other model.

Adapted from pstack by Lauren Tan (MIT License).

## Work by Principles

### joesys-mode

A way of working for coding tasks. The agent restates the goal, follows a
short step list for the task (investigation, bug fix, feature, or
refactoring), and applies 32 engineering principles in three phases: first
make it work, then make it right, and practice. Every step list ends with a
check on the real thing. The reply names each principle that changed a
decision.

```text
/joesys-mode users get two notifications after a retry. reproduce it first, then fix it.
/joesys-mode
```

The mode never pushes and never opens a pull request without approval in the
current message. The project's own rules and the user's current message win
over the mode. It names sibling skills as options, and runs only `/commit` by
itself. Three quality tools (`crapper`, `dryer`, and `mutator`) are optional:
the mode uses a tool when it is installed and says when it skipped one.

The principles come from poteto-mode in pstack by Lauren Tan and from ub-mode
by Robert C. Martin (both MIT License).

## Understand Projects

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

### why

Find out why code is built the way it is: the reason for a design, a limit, a
guard, or a rule. Code shows what it does, not why it exists. The skill
builds an anchor from `git blame` and the commit messages. Then it searches
two sources every time: the version control history, and the project's own
written record (comments, tests, specs, devlog scraps, handoff files, and
saved council answers). The answer comes first. Every claim has a citation
and one of five confidence tiers: Stated, Supported, Inferred, Guess, or
Unknown.

```text
/why does the retry stop after 3 attempts?
/why src/auth/session.py:40-72
/why
```

The skill only reads. It never cites code as the reason for itself, and it
reports each search that found nothing. It searches an outside source, such
as tickets or team chat, only when the host already has a connector for it.
No run has used a connector yet.

Adapted from pstack by Lauren Tan (MIT License).

### huh

Re-explain the assistant's previous message in plain English that a non-native
reader can follow. When the message involves a problem or a decision, the
reply also covers the issue and its context, the options with pros and cons,
and a recommendation with its trade-off stated openly. Every reply closes
with two disclosures: where the answer is least confident, and the biggest
questions the operator has not asked yet.

```text
/huh
/huh what is a race condition here
```

The skill explains and stops; it never edits files or runs commands.

## Improve Workflows

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

Analyze Claude Code or Codex conversation transcripts across prompt craft,
workflow efficiency, agentic leverage, error recovery, and context management.
The skill produces Markdown and HTML report cards with a prioritized coaching
roadmap and trend history.

```text
/interaction-review
/interaction-review session <uuid>
/interaction-review since 2026-05-01
/interaction-review trend
```

The skill reads the session logs of the host it runs in: Claude Code
(`~/.claude/projects/`) or Codex (`~/.codex/sessions/`).

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
/handoff --for agent --target antigravity
/handoff --for human --include-diff
/handoff --output notes/my-handoff.md
/handoff resume
/handoff resume .handoffs/<file>.md
```

| Setting | Values and behavior |
|---|---|
| Audience | `self`, `agent`, or `human`; default `self` |
| Target | `auto`, `claude`, `codex`, `antigravity`, or `generic`; default `auto` |
| Detail | Operational by default, or `--full` / `--compact` |
| Drift | Resume classifies state as `exact`, `advanced`, `drifted`, or `unverifiable` |
| Output | `.handoffs/YYYYMMDD-HHMMSS-<slug>.md` unless overridden |

`--full` and `--compact` cannot be combined. The skill never commits, pushes,
publishes, or shares a checkpoint automatically, and it stops before mutation
when repository state has drifted.

### devlog

Capture development insights for budding programmers. Write mode reconstructs
the reasoning behind a topic, scrap mode records an insight quickly, and list
mode shows the backlog and published posts. `/commit` captures scraps
automatically after significant commits, so ideas pile up for later posts.

```text
/devlog "the recursive clone bug"
/devlog --since yesterday
/devlog --from-scrap recursive-fix
/devlog --from-scrap ~/Projects/moirai/docs/devlog/.scraps/<file>.md
/devlog scrap "signing workaround"
/devlog scrap
/devlog scrap --from-context "adapter lesson"
/devlog list
```

To see scraps from several projects in one list, add a `## Devlog repos`
section with one repo path per line to `~/.claude/skill-context/devlog.md`
(Codex: `~/.codex/skill-context/devlog.md`). `--from-scrap` with a path in
another repo prints the command to run from that repo, because the post and
its commit belong there.

### commit

Create a Conventional Commit in plain language for a reader without current-task
context. Every message retains an intent paragraph, meaningful change summary,
and candid AI review. When a change splits into several logical commits, the
skill puts them on a short-lived branch and merges it back with `--no-ff`
(OneFlow Option 3), so the group shows as one merge bubble. A group of one
commit is fast-forwarded instead. It also recovers from an unresponsive
1Password signing agent by creating an explicitly reported unsigned commit.

```text
/commit
```

`/commit` never rewrites existing history. When recent commits look related,
it suggests `/restructure-commit` in one line and carries on.

### restructure-commit

Restructure recent history: group related recent commits, plus any new
uncommitted work, into one OneFlow Option 3 merge bubble. The skill shows the
plan and waits for approval before it rewrites history. It uses the same
message format as `commit`.

```text
/restructure-commit
/restructure-commit HEAD~4..HEAD
/restructure-commit abc123 def456 789abc
```

Neither skill pushes without express push-specific authorization. A force push
after a rewrite needs its own approval.

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
