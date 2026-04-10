# joesys-skills

Custom Claude Code skills and plugins.

## Installation

```
/plugin marketplace add joesys/joesys-skills
/plugin install joesys-skills
```

## Available Skills

---

### Part I: AI Council

Multi-model consultation — ask one model or all three in parallel.

#### ai-council

Consult three frontier AI models (Claude, GPT, Gemini) in parallel on the same question. Automatically gathers relevant context, dispatches to all three, then synthesizes a structured analysis with consensus points, tensions, and a confidence matrix. Saves results by default.

```
/ai-council "Should we use PostgreSQL or MongoDB for our user data?"
/ai-council --no-save "Quick question about caching strategies"
/ai-council --path ./notes "Compare REST vs GraphQL for this use case"
```

#### claude

Delegate prompts to Anthropic's Claude Code CLI for code analysis, refactoring, and automated editing. Critically evaluates Claude's output with special attention to shared blind spots (Claude evaluating Claude). Supports named session resume.

**Defaults:** `opus` / `high` effort / `plan` (read-only) permission mode

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

**Defaults:** `gpt-5.4` / `xhigh` reasoning / `read-only` sandbox

```
/codex "explain the auth flow in this repo"
/codex --model gpt-5.3 "analyze this function"
/codex --sandbox workspace-write "fix the lint errors"
/codex resume "follow up on that"
```

#### gemini

Delegate prompts to Google's Gemini CLI for code analysis, refactoring, and automated editing. Critically evaluates Gemini's output and supports session resume with indexed session management.

**Defaults:** `gemini-3.1-pro-preview` / `plan` (read-only) approval mode

```
/gemini "explain the auth flow in this repo"
/gemini --model gemini-2.5-flash "quick analysis of this function"
/gemini --approval-mode yolo "fix the lint errors"
/gemini resume "follow up on that"
/gemini resume 3 "continue from that session"
/gemini sessions
```

---

### Part II: Code Review

Automated code analysis — from quick bug scans to full quality audits.

#### code-review

Dispatch 6 parallel domain-expert subagents to analyze code for violations across correctness, clean code, architecture, reliability, security, and performance. Produces a severity-grouped report (P0-P4) with concrete before/after fixes in the target language. Supports branch diffs, directory scans, single files, PR reviews, and commit reviews.

| Domain | Focus |
|---|---|
| Correctness | Actual bugs — wrong logic, off-by-one, null dereferences, race conditions |
| Clean Code | Naming, DRY (Rule of Three), nesting depth, function length, KISS/YAGNI |
| Architecture | Coupling, cohesion, layering violations, dependency direction, god classes |
| Reliability | Error handling, silent failures, resource leaks, missing validation |
| Security | Injection, hardcoded secrets, auth gaps, input sanitization, data exposure |
| Performance | Algorithmic complexity, N+1 queries, missing caching, unnecessary allocations |

```
/code-review                          # Review current branch diff vs. base
/code-review src/                     # Scan all files in a directory
/code-review --file src/main.py       # Review a single file
/code-review --pr 123                 # Review files changed in a GitHub PR
/code-review --commit abc123          # Review files changed in a specific commit
/code-review --min-severity P1        # Only show P1+ findings (combinable with any mode)
```

#### quick-review

Fast, bug-focused code review that dispatches correctness and security subagents alongside a cross-model reviewer (Codex and Claude) in parallel. Reports only P0-P2 findings — no style nits, no architecture suggestions. Uses `git diff -U50` for context rather than loading full files, making it significantly faster than `/code-review`.

```
/quick-review                              # Review current branch diff vs. base
/quick-review src/utils/                   # Scan all files in a directory
/quick-review --file src/main.py           # Review a single file
/quick-review --pr 123                     # Review files changed in a GitHub PR
/quick-review --commit abc123              # Review files changed in a specific commit
/quick-review --include-gemini             # Add Gemini as a third reviewer model
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
/preferences code-review                   # Set preferences for a specific skill
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
