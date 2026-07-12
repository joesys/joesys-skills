# joesys-skills

Custom Claude Code skills and Codex-installable skills.

## Installation

### Claude Code

```
/plugin marketplace add joesys/joesys-skills
/plugin install joesys-skills
```

### Codex

Install as a Codex plugin (the repo doubles as a Codex plugin marketplace via
`.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json`):

```
codex plugin marketplace add joesys/joesys-skills
codex plugin add joesys-skills@joesys-skills
```

To pick up new releases:

```
codex plugin marketplace upgrade
```

Codex has no slash commands for skills — invoke them with `$name` mentions
(`$commit`, `$codereview`, ...) or let Codex match the task against each
skill's description.

The plugin serves the Codex-adapted copies committed under `codex-skills/`.
That directory is generated — never edit it by hand. After changing source
skills, regenerate it:

```powershell
python scripts\codex_adapter.py codex-skills --force
```

A pytest guard (`test_committed_codex_skills_match_fresh_build`) fails when
`codex-skills/` is stale.

Alternatively, for a plugin-less install into `%USERPROFILE%\.codex\skills`
(or `%CODEX_HOME%\skills`):

```powershell
python scripts\install_codex_skills.py
```

To reinstall both hosts from a clean state:

```powershell
.\scripts\reinstall-plugin.ps1            # Claude Code + Codex
.\scripts\reinstall-plugin.ps1 -Target codex
```

To validate the adapter without installing:

```powershell
pytest tests\test_codex_adapter.py -q
```

## Available Skills

---

### Part I: AI Council

Multi-model consultation — ask one model or all three in parallel. Default model identifiers and CLI flags for the delegation skills (`/claude`, `/codex`, `/antigravity`, `/ai-council`) are defined in [`shared/model-defaults.md`](shared/model-defaults.md).

#### ai-council

Consult three frontier AI models (Claude, GPT, Antigravity) in parallel on the same question. Automatically gathers relevant context, dispatches to all three, then synthesizes a structured analysis with consensus points, tensions, and a confidence matrix. Saves results by default.

```
/ai-council "Should we use PostgreSQL or MongoDB for our user data?"
/ai-council --no-save "Quick question about caching strategies"
/ai-council --path ./notes "Compare REST vs GraphQL for this use case"
```

#### claude

Delegate prompts to Anthropic's Claude Code CLI for code analysis, refactoring, and automated editing. Critically evaluates Claude's output with special attention to shared blind spots (Claude evaluating Claude). Supports named session resume.

```
/claude "explain the auth flow in this repo"
/claude --model sonnet "quick analysis of this function"
/claude --permission-mode acceptEdits "fix the lint errors"
/claude --effort max "deep analysis of the architecture"
/claude --bare "analyze without plugins or hooks"
/claude resume "follow up on that"
/claude resume my-review "continue from that session"
```

#### codex

Delegate prompts to OpenAI's Codex CLI for code analysis, refactoring, and automated editing. Critically evaluates Codex's output and supports session resume.

```
/codex "explain the auth flow in this repo"
/codex --model gpt-5.3 "analyze this function"
/codex --sandbox workspace-write "fix the lint errors"
/codex resume "follow up on that"
```

#### antigravity

Delegate prompts to Google's Antigravity CLI (`agy`) for code analysis, refactoring, and automated editing. Critically evaluates Antigravity's output and supports session resume.

```
/antigravity "explain the auth flow in this repo"
/antigravity resume "follow up on that"
/antigravity resume <ID> "continue from that session"
```

---

### Part II: Code Review

Automated code analysis — from quick bug scans to full quality audits.

#### codereview

Dispatch 7 parallel domain-expert subagents to analyze code for violations across correctness, clean code, architecture, reliability, security, performance, and story readability. Produces a severity-grouped report (P0-P4) with concrete before/after fixes in the target language. Supports branch diffs, directory scans, single files, PR reviews, and commit reviews.

| Domain | Focus |
|---|---|
| Correctness | Actual bugs — wrong logic, off-by-one, null dereferences, race conditions |
| Clean Code | Naming, DRY (Rule of Three), nesting depth, function length, KISS/YAGNI |
| Architecture | Coupling, cohesion, layering violations, dependency direction, god classes |
| Reliability | Error handling, silent failures, resource leaks, missing validation |
| Security | Injection, hardcoded secrets, auth gaps, input sanitization, data exposure |
| Performance | Algorithmic complexity, N+1 queries, missing caching, unnecessary allocations |
| Story Readability | 8-dimension story-readability scoring (rolled into P2-P4 findings) |

```
/codereview                          # Review current branch diff vs. base
/codereview src/                     # Scan all files in a directory
/codereview --file src/main.py       # Review a single file
/codereview --pr 123                 # Review files changed in a GitHub PR
/codereview --commit abc123          # Review files changed in a specific commit
/codereview --min-severity P1        # Only show P1+ findings (combinable with any mode)
```

#### quick-review

Fast, bug-focused code review that dispatches correctness and security subagents in parallel with streamlined static analysis. Reports only P0-P2 findings — no style nits, no architecture suggestions. Uses `git diff -U50` for context rather than loading full files, making it significantly faster than `/codereview`. No cross-model dispatch — uses the host model only for speed.

```
/quick-review                              # Review current branch diff vs. base
/quick-review src/utils/                   # Scan all files in a directory
/quick-review --file src/main.py           # Review a single file
/quick-review --pr 123                     # Review files changed in a GitHub PR
/quick-review --commit abc123              # Review files changed in a specific commit
```

#### readability-review

Grade code on how well it "reads like a story" using 8 weighted dimensions. Produces a numeric score (0-100) mapped to a letter grade, with thematic findings and file-by-file breakdown including concrete before/after refactoring suggestions.

| Dimension | Weight | Focus |
|---|---|---|
| Narrative Flow | 20% | Top-to-bottom readability, paragraph spacing, temporal ordering |
| Naming as Intent | 15% | Names reveal what and why without reading the body |
| Cognitive Chunking | 15% | Logical phases extracted into named steps, chapter visibility |
| Abstraction Consistency (SLAP) | 14% | Single level of abstraction per function |
| Function Focus | 10% | One function, one job, ~20 lines of logic |
| Structural Clarity | 10% | Flat control flow, guard clauses, minimal nesting |
| Documentation Quality | 10% | Comments explain why, not what; business rationale documented |
| No Clever Tricks | 6% | No dense one-liners, bitwise hacks, or ternary chains |

```
/readability-review                          # Review current branch diff vs. base
/readability-review src/                     # Scan all files in a directory
/readability-review --file src/main.py       # Review a single file
/readability-review --pr 123                 # Review files changed in a GitHub PR
/readability-review --commit abc123          # Review files changed in a specific commit
/readability-review --min-score 70           # Only show files scoring below threshold
```

#### human-review-guide

Generate a personalized reading guide for human review. Triages changes into attention tiers (DECIDE/READ/SKIM/SKIP), runs deep analysis on decision-heavy sections, and produces a guided reading order so reviewers know where to spend time and what to skip. Works on code diffs, PRs, specs, configs, and any AI-generated artifact.

| Tier | Meaning | Reviewer Action |
|---|---|---|
| DECIDE | Contains a decision requiring human judgment | Read carefully, form an opinion |
| READ | Non-trivial logic worth understanding | Read to build mental model |
| SKIM | Straightforward, follows from decisions elsewhere | Glance for context |
| SKIP | Mechanical/boilerplate | Safe to ignore |

```
/human-review-guide                        # Guide for current branch diff
/human-review-guide PR#123                 # Guide for a specific PR
/human-review-guide docs/spec.md           # Guide for reviewing an artifact
/human-review-guide --with-review          # Enrich with /codereview findings
/human-review-guide --calibrate            # Re-run calibration questions
```

#### codebase-audit

Comprehensive, language-agnostic codebase quality audit measuring up to 12 core quality criteria plus development velocity. Spawns 6 parallel collection agents, displays graded metrics (A+ through F) in a console summary table, and optionally writes a full analysis report with industry benchmarks and actionable recommendations.

| Category | Criteria |
|---|---|
| Code Quality | Maintainability, Readability, Consistency |
| Architecture | Modularity, Evolvability, Reliability |
| Engineering | Correctness, Testability, Performance |
| Operations | Operability, Security |
| Readability | Story Readability |
| Velocity | Development velocity (commits, churn, throughput) |

```
/codebase-audit                            # Full pipeline (all 12 criteria + velocity)
/codebase-audit metrics                    # Collect and display only
/codebase-audit analysis                   # Re-analyze from most recent metrics
/codebase-audit delta                      # Compare two most recent audits
/codebase-audit maintainability performance # Only specified criteria
/codebase-audit --static-only             # No live commands (no test run, no dep audit)
```

---

### Part III: Workflow & Utilities

Development workflow tools — writing, reviewing, exporting, and committing.

#### explain

Dispatch 5 parallel domain-lens subagents to analyze a codebase across structure, behavior, domain & data, external dependencies, and health & risk. Produces a layered report from TL;DR to deep understanding with an orientation cheat sheet and fastest-path-to-competence recommendations. Supports whole projects, directories, single files, symbols, and natural language feature traces.

| Lens | Focus |
|---|---|
| Structure & Entry Points | Module boundaries, organization pattern, entry points, dependency graph |
| Behavior — Key Workflows | End-to-end traces of the 3 most important workflows |
| Domain & Data | Data models, state transitions, domain glossary, storage mapping |
| External Dependencies | External services, infrastructure config, integration patterns |
| Health & Risk | Hotspots, churn, debt, test signals, git archaeology, onboarding path |

```
/explain                                  # Explain the whole project (default)
/explain src/auth/                        # Explain a directory/module
/explain src/auth/oauth.ts                # Explain a single file
/explain MyClassName                      # Explain a class/symbol
/explain "how does payment work?"         # Trace a feature across the codebase
/explain --save                           # Save report to docs/explain/
/explain src/api/ --save --path docs/     # Explain directory, save to custom path
```

#### handbook

Generate comprehensive project documentation as a single self-contained HTML file serving two audiences at once. Dispatches 6 parallel analysis agents, conducts a human interview between analysis and writing, then fans out 13-16 parallel chapter writers. Reads the previous handbook for continuity when regenerating.

| Audience | Content |
|---|---|
| Reference Handbook | Architecture, module walkthroughs, design rationale, dependencies, extension points |
| Newbie Guidebook | Setup guide, program-flow step-throughs with annotated code, common gotchas, troubleshooting |

```
/handbook                                  # Full handbook for the entire project
/handbook src/auth                         # Scope to a directory or module
```

#### dashboard

Generate a single self-contained HTML project-health dashboard aimed at PMs and EMs. Deterministic Python helpers read local git history and compute traffic-light metrics across three lenses — the same repo always produces the same dashboard, so it is runnable in CI. Optional enrichment pulls open PRs and CI status from GitHub (via `gh`) and borrows the latest `/codebase-audit` grade. An optional single-pass LLM narrative explains why each light is the colour it is — it never changes a light.

| Lens | Signals |
|---|---|
| Delivery | Commit cadence, throughput, release recency, module activity |
| Health | Firefighting rate, churn, borrowed `/codebase-audit` code-quality grade |
| Team | Bus factor, contributor concentration, off-hours activity |

```
/dashboard                                 # Whole-repo health dashboard
/dashboard src/api                         # Highlight a module in the summary
/dashboard --no-llm                        # Deterministic/CI mode — skip the narrative
/dashboard --no-host                       # Skip GitHub enrichment
/dashboard --no-llm --no-host              # Fully deterministic, fully local
```

#### handoff

Create a durable semantic checkpoint for continuing work in a fresh AI session, transferring it to an independent agent, or orienting another human. Handoffs use one host-neutral Markdown schema, capture deterministic repository state, and classify resume safety as `exact`, `advanced`, `drifted`, or `unverifiable` before continuing.

| Audience | Emphasis |
|---|---|
| Self | Concise operational continuity and the exact next action |
| Agent | Explicit authority, constraints, deliverable, completion criteria, and report-back |
| Human | Rationale, ownership, review points, and judgment calls |

```text
/handoff                                  # Save an operational checkpoint
/handoff --full                           # Include deeper reasoning and alternatives
/handoff --interactive                    # Interview before saving
/handoff --target codex                   # Prepare for a fresh Codex session
/handoff --for agent --target gemini      # Transfer to an independent Gemini agent
/handoff --for human                      # Prepare a human-readable transfer
/handoff resume                           # Validate and resume the newest checkpoint
/handoff resume .handoffs/<file>.md       # Resume a specific checkpoint
```

#### devlog

Capture development insights and turn them into devlog posts for budding programmers. Mines git history, Claude Code conversation transcripts, and content scraps to reconstruct your thinking, then brainstorms with you to find the real insight before drafting. Supports quick content scraps for when you're in the flow.

| Mode | Description |
|---|---|
| Write | Brainstorm and draft a full devlog post |
| Scrap | Auto-capture a rich content scrap (no questions asked) |
| List | Show scrap backlog and published posts |

```
/devlog "the recursive clone bug"            # Write a post about a topic
/devlog --since yesterday                    # Mine recent sessions for a post
/devlog --from-scrap recursive-fix           # Write from an existing scrap
/devlog scrap "signing workaround"           # Quick-capture a scrap
/devlog scrap                                # Auto-detect and capture a scrap
/devlog list                                 # Show scraps and published posts
```

#### retrospective

Structured retrospective facilitated by AI, interleaved with human check-ins at every phase. Dispatches 5 parallel channel agents — each mining a different data source (git history, conversations, code quality, planning docs, tests) — to build a comprehensive digest. Derives discussion topics from the data, walks through them with the human, and produces action items, process improvements, and a readable narrative.

| Channel | Data Source |
|---|---|
| Git History | Commits, diffs, merge patterns, contributor activity |
| Conversations | Claude Code conversation transcripts and decisions |
| Code Quality | Quality deltas, complexity trends, debt movement |
| Planning vs. Reality | Plan documents compared against actual implementation |
| Testing & Reliability | Test coverage changes, failure patterns, flaky tests |

```
/retrospective                             # Chain mode (default), from last retro to now
/retrospective --since 2026-03-15          # From a specific date
/retrospective --since v1.0                # From a git tag
/retrospective --since v1.0..v1.1          # Between two tags
/retrospective --output docs/sprints/3/    # Custom output directory
/retrospective continue                    # Resume an interrupted retro
```

#### interaction-review

Analyze Claude Code conversation transcripts to grade how effectively you collaborate with the AI agent. Dispatches 5 parallel analysis subagents — each evaluating a dimension of interaction quality — followed by a coach re-review for quality and actionability. Produces a scored report card with a prioritized improvement roadmap tracking progress over time.

| Lens | Weight | Focus |
|---|---|---|
| Prompt Craft | 30% | Clarity, specificity, context-setting, constraint usage |
| Workflow Efficiency | 25% | Turn economy, correction loops, goal directness |
| Agentic Leverage | 20% | Skill/tool usage, autonomy, parallelism, delegation |
| Error Recovery | 15% | Detection speed, correction clarity, pivot decisiveness |
| Context & Instruction | 10% | CLAUDE.md, memory, session setup, reference management |

```
/interaction-review                        # Analyze sessions since last report
/interaction-review session <uuid>         # Deep-dive on one session
/interaction-review since 2026-05-01       # Analyze from a specific date
/interaction-review trend                  # Score progression across all reports
```

#### export

Convert markdown, text, and code files into polished, shareable formats. Supports PDF, HTML, and PNG output with three content scopes (full, summary, 1pager) and three CSS themes (minimal, modern, dark). Uses Pandoc with LuaLaTeX for PDF and headless Chromium for PNG.

```
/export report.md                          # Full file to PDF (default)
/export report.md --format png --theme dark   # Full PNG with dark theme
/export report.md --scope summary --format all # Summary in all 3 formats
/export utils.py --format html --theme dark   # Syntax-highlighted code export
/export report.md --scope 1pager           # Condensed ~500-600 word version
/export report.md --orientation landscape  # Landscape layout
/export report.md --output ./out/          # Custom output path
```

#### preferences

Capture and manage per-user preferences that shape how every skill in the collection behaves. Can be invoked directly or automatically by other skills on first contact. Covers communication style, explanation depth, experience level, and project context.

```
/preferences                               # Interactive setup
/preferences show                          # Display current preferences
/preferences reset                         # Clear all and start fresh
/preferences codereview                   # Set preferences for a specific skill
```

#### commit

Structured git commits following Conventional Commits with a three-part body (intent, changes, AI review). Supports OneFlow Option 3 branching for multi-commit changesets. Auto-recovers from 1Password signing failures.

```
/commit
```

#### ss

Visual communication bridge — grab recent screenshots, analyze them, and act. Supports natural language actions: explain (`huh`), fix errors (`fix`), learn and adapt (`do this`), or any freeform request. Intelligently suggests sibling skills when they fit. Configures the screenshot folder on first run and remembers it across projects.

| Action | Behavior |
|---|---|
| *(none)* | Analyze and guess intent from conversation context |
| `huh` | Explain what's in the screenshot |
| `fix` | Identify and fix the error shown |
| `do this` | Learn from the screenshot and adapt |
| *(freeform)* | Natural language — "make infographic", "review this", etc. |

```
/ss                                        # Grab latest screenshot, analyze + guess intent
/ss huh                                    # Explain what's in the latest screenshot
/ss fix                                    # Identify error in screenshot, fix the code
/ss 3                                      # Grab 3 latest, analyze all
/ss 2 fix                                  # Grab 2 latest, cross-reference errors, fix
/ss do this                                # Learn from screenshot, adapt for your project
/ss 3 make infographic plz                 # Grab 3 latest, create unified infographic
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
