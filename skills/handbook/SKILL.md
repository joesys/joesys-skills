---
name: handbook
description: "Use when the user invokes /handbook to generate comprehensive project documentation as a single self-contained HTML file — a reference handbook for intermediate programmers and a guided walkthrough for beginners."
---

# Handbook

Generate comprehensive, self-contained project documentation as a single HTML file. The handbook serves two audiences in one document:

1. **Reference Handbook** -- Architecture, module walkthroughs, design rationale, dependencies, extension points for intermediate programmers to get oriented quickly.
2. **Newbie Guidebook** -- Setup guide, program flow step-throughs with annotated code, common gotchas, troubleshooting for beginner programmers.

## Out of Scope

This skill MUST NOT:
- Generate API reference documentation (use TypeDoc, Sphinx, Swagger, etc.)
- Modify source code, README, CONTRIBUTING.md, or CHANGELOG
- Replace `/explain` -- `/handbook` documents for others; `/explain` analyzes for the person running it
- Keep docs updated automatically -- this is a one-shot generation skill
- Serve as an SRE runbook -- observability, incident response, and rollback procedures are out of scope unless the codebase explicitly contains them
- Call `/explain` internally -- `/handbook` dispatches its own analysis agents

## Reference Files

This skill uses progressive disclosure -- read reference files only when needed:

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Full prompt templates for 6 analysis agents, 13 core chapter writers, 3 conditional chapter writers, 1 review agent | Before dispatching agents in Phase 1 or Phase 3 |
| `references/output-schemas.md` | Structured output schemas for analysis agents and chapter writers | Before dispatching agents |
| `references/writing-style-guide.md` | Shared voice/tone/format instructions for chapter writers | Before dispatching Phase 3 writers |
| `templates/handbook-template.md` | Markdown template for Phase 4 assembly | During Phase 4 |

## Invocation

`/handbook` -- Full handbook for the entire project.
`/handbook <path>` -- Scoped to a specific directory or module.

### Argument Parsing

| Input | Scope |
|---|---|
| `/handbook` | Whole project (default) |
| `/handbook src/auth` | Directory scope -- handbook covers only the specified subtree |
| `/handbook packages/core` | Module scope -- handbook covers a specific package/module |

### Scope Detection Logic

1. If the argument matches an existing directory (exact match) -- **directory** scope
2. If the argument matches a package/workspace boundary (contains `package.json`, `Cargo.toml`, etc.) -- **module** scope (treated the same as directory but noted in context)
3. If no exact match, search via Glob (e.g., `**/<argument>/`). If a unique directory is found, use it. If multiple matches, list them and ask the user to clarify.
4. If no argument -- **whole project** scope
5. If the argument does not match any directory -- report: "Path not found: `<path>`. Check the path and try again."

When scoped, the handbook covers only the targeted subtree but still includes:
- How the scoped module connects to the rest of the project
- Setup instructions relevant to working on that module
- Dependencies the module relies on

---

## Phase 0 -- Context & Preparation

### Step 0.1: Load Preferences

Read `shared/skill-context.md` for the full protocol (resolve `shared/...` against the plugin root — two levels above this SKILL.md — never the project's working directory). This skill is **full interview** category.

1. Check for `.claude/skill-context/preferences.md` -- if missing, invoke `/preferences` before proceeding.
2. Check for `.claude/skill-context/handbook.md` -- if found, load previous interview answers and context.

**How preferences shape this skill:**

| Preference | Effect on Handbook |
|---|---|
| Detail level: concise | Shorter chapter introductions, fewer inline examples, top-level content only |
| Detail level: detailed | Expanded sections, more code walkthroughs, richer design rationale |
| Style: visual-with-diagrams | More Mermaid diagrams, expanded dependency graphs, flow charts for every workflow |
| Style: example-driven | Code walkthroughs include more annotated snippets, change recipes expanded |
| Assumed knowledge: beginner | Heavier Getting Started, define terms, expand Troubleshooting |
| Assumed knowledge: expert | Lighter Getting Started, focus on architecture, design rationale, extension points |
| Project phase: prototype | Lighter on process, heavier on "how to extend" |
| Project phase: mature | Heavier on consistency, testing, onboarding friction, danger zones |

Pass the relevant subset of preferences to each agent prompt. Agents receive only the preferences that affect their domain.

### Step 0.2: Read Previous Context

1. If `docs/handbook/handbook.md` exists, read it -- chapter writers will receive their previous chapter for continuity.
2. If JSONL chat logs are available in `~/.claude/projects/<project-dir>/`, read them for development context (design discussions, rationale, decisions).
3. If a previous `/explain` report exists in `docs/explain/`, note its path -- analysis agents MAY read it as supplementary context.

### Step 0.3: Build File Inventory

Build the canonical file list. This is the **single source of truth** passed to all analysis agents -- agents do not independently rediscover project structure.

1. Run `git ls-files` to get all tracked files. If not a git repo, fall back to recursive glob excluding common ignore patterns (`.git`, `node_modules`, `__pycache__`, `.venv`, `vendor`, `dist`, `build`).
2. If scoped to a path, filter the inventory to only files under that path.
3. Classify each file into one of these categories:
   - **Source:** files matching language extensions under detected source paths
   - **Test:** files in test directories or matching test naming patterns (`test_*`, `*_test.*`, `*.spec.*`, `*.test.*`)
   - **Config:** `.env*`, `*.config.*`, `*.json`, `*.yaml`, `*.toml` in root or config directories
   - **Docs:** `*.md`, `*.rst`, `*.txt` in `docs/` or root
   - **Generated:** files in `dist/`, `build/`, `.next/`, `coverage/`, or with generated-file markers
   - **Vendor:** files in `vendor/`, `node_modules/`, `third_party/`
4. Skip binary files, minified files (`*.min.js`, `*.min.css`), and vendored dependencies.
5. Detect primary language from file extension distribution.
6. Emit file inventory summary: total files, files per category, primary language, detected frameworks.

### Step 0.4: Identify Logical Modules

For the scoped file set:
1. Identify top-level directories under source paths as candidate modules.
2. Detect package boundaries (`package.json`, `__init__.py`, `go.mod`, `Cargo.toml`, etc.).
3. For monorepos: identify workspace/package boundaries.
4. Emit module list with file counts per module.

### Step 0.5: Conditional Chapter Detection

Scan for evidence that triggers conditional chapters:

| Conditional Chapter | Evidence to Scan For |
|---|---|
| Data Model & Persistence | ORM configs (prisma, sqlalchemy, typeorm, etc.), migration directories, schema files, DB connection strings in config |
| Security & Permissions | Auth middleware files, role/permission models, JWT/OAuth configs, access control logic, security headers |
| Build, Deployment & Ops | CI/CD configs (`.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml`), Dockerfile, deployment scripts, monitoring configs, k8s manifests |

Record which conditional chapters are triggered. Pass this to Phase 3 dispatch logic.

### Step 0.6: Scope Size Check

For **whole project** and **directory** scopes, count the total source files in the inventory. If the count exceeds **5000 source files**, **MUST warn** the user:

> This scope contains ~[N] source files. Handbook generation will be thorough but may take several minutes and use significant tokens. Consider narrowing scope (e.g., `/handbook src/core/`). Proceed anyway? (y/n)

Proceed only after confirmation.

### Step 0.7: Emit Project Context Block

Assemble and display the context summary before proceeding:

```
Project: <name>
Language: <primary> (+ <secondary>)
Modules: <count> (<list>)
Files: <total> (source: N, test: N, config: N, docs: N)
Conditional chapters: <list or "none detected">
Previous handbook: <yes/no>
Previous interview context: <yes/no>
```

### Source Precedence Hierarchy

When sources conflict, higher rank wins. This applies to ALL phases:

1. Current source code and config files (highest authority)
2. Current test files
3. Git history and commit messages
4. Human interview answers
5. JSONL chat log context
6. Previous handbook content (lowest -- advisory only)

---

## Phase 1 -- Parallel Analysis

**MUST dispatch all 6 agents in a single message using the Agent tool.** All agents use `model: "opus"`. Sequential dispatch is a defect.

Read `references/agent-prompts.md` for the full prompt template for each agent. Read `references/output-schemas.md` for the output schema each agent must follow.

Each agent receives:
- The Guiding Principles block (prepended to every prompt)
- The file inventory from Phase 0 (file list, classifications, module boundaries)
- The project context block from Step 0.7
- Previous handbook chapter(s) relevant to their analysis domain (if previous handbook exists)
- Previous `/explain` report (if exists, as supplementary context)
- User preferences (relevant subset only -- append after Guiding Principles as a `## User Preferences` section)
- Their specific task instructions from `references/agent-prompts.md`

### Agent Roster

| # | Agent | Analysis Domain |
|---|---|---|
| 1 | Architecture Analyst | Module boundaries, dependency graph, layer structure, design patterns, Mermaid architecture diagram, folder structure map, naming conventions |
| 2 | Code Flow Tracer | Entry points, main execution path (start to finish), hot paths, request lifecycle, key workflows, background workers, scheduled tasks |
| 3 | Domain & Data Analyst | Data models, entity lifecycles, domain glossary, business invariants, state management, storage patterns, DB schema (if applicable), migrations |
| 4 | Dependency Analyst | Third-party libs with justification, APIs, external services, integration contracts, failure modes, retry behavior, config system |
| 5 | Git Archaeologist | Design evolution from commit history, major refactors, why patterns changed, contributor patterns, churn hotspots, fragile areas, technical debt signals |
| 6 | Beginner Path Scout | Setup requirements, build/run steps, first-contribution workflow, common gotchas, environment quirks, test running instructions, seed data, dev workflow |

### Guiding Principles (included in every agent prompt)

Prepend this block to every agent prompt (analysis agents and chapter writers):

1. **Evidence over guesswork.** Every claim must cite `file:line`. If you cannot find evidence, state: "Inferred -- not confirmed by code" with confidence: low.
2. **No fabrication.** Do not invent file paths, function names, or behaviors that do not exist in the codebase.
3. **Source precedence.** Current code > tests > git history > interview answers > chat logs > previous handbook.
4. **Mermaid for diagrams.** All visual representations use Mermaid syntax, never ASCII art.
5. **No secrets.** Never include env values, API keys, tokens, or passwords. Use placeholders: `<DATABASE_URL>`, `<API_KEY>`.
6. **Scope awareness.** Analyze only files within the scoped file inventory. Do not read files outside the scope.

### Agent Output Contract

Every agent MUST return a structured object following the schema in `references/output-schemas.md`. Required fields for all agents:

- `modules` -- list of module names this analysis touches
- `claims` -- list of factual claims, each with:
  - `text` -- the claim
  - `citation` -- `file:line` reference
  - `confidence` -- high / medium / low
- `diagrams` -- list of Mermaid diagram blocks with titles
- `unresolved` -- list of questions the agent could not answer from code alone (feeds Phase 2 interview)

Plus agent-specific fields defined in `references/output-schemas.md`.

### Failure Handling

Agent timeouts, malformed output, and total analysis failure are handled per the consolidated Error Handling table at the end of this document.

### Progress Indication

Before dispatch, print:

> Analyzing codebase across 6 lenses for handbook generation...

After all agents complete, print a brief summary of successes and failures before proceeding.

---

## Phase 2 -- Human Interview

After Phase 1, collect all `unresolved` questions from the 6 analysis agents. Deduplicate and prioritize by impact on handbook quality.

### Interview Protocol

1. If `.claude/skill-context/handbook.md` exists, check which questions have already been answered in previous runs. **Skip those** -- only ask about new gaps.
2. Present questions grouped by theme, one at a time, offering multiple-choice options where possible to reduce friction.
3. Focus on these categories:
   - **Design rationale:** "I see you chose X pattern -- what drove that decision?"
   - **Extension points:** "What features are planned next? Where would new functionality go?"
   - **Danger zones:** "Are there areas of the code that are fragile or should not be touched casually?"
   - **Tribal knowledge:** "What should a new developer know that isn't in the code?"
   - **Style/conventions:** "Are there unwritten coding conventions the team follows?"
   - **Corrections:** If previous handbook exists: "The previous handbook said Y about module Z -- still accurate?"
4. Save all answers to `.claude/skill-context/handbook.md` with timestamps.
5. If the user declines the interview (says "skip" or similar), proceed with AI-inferred content. Mark uncertain sections with visual indicators in the output.

### Context Persistence

All interview answers are persisted to `.claude/skill-context/handbook.md`. On subsequent runs:
- Already-answered questions are skipped
- Only new gaps from the latest analysis are asked
- Previous answers are passed to chapter writers alongside fresh analysis

### Interview Context File Format

`.claude/skill-context/handbook.md` is a bulleted markdown file: a `# Handbook Preferences` heading with a `Last updated: <DATE>` line, then one `##` section per question category (Design Rationale, Extension Points, Danger Zones, Tribal Knowledge, Style & Conventions, Corrections), each holding `- <question>: <answer>` bullets.

---

## Phase 3 -- Parallel Chapter Writers

**MUST dispatch all chapter writer agents in a single message using the Agent tool.** All agents use `model: "opus"`. Sequential dispatch is a defect.

Read `references/agent-prompts.md` for the full prompt template for each chapter writer. Read `references/writing-style-guide.md` and inject it into every writer prompt to ensure consistent voice.

Each writer receives:
- The Guiding Principles block (prepended to every prompt)
- All 6 analysis agent outputs (or the available subset if some analysis agents failed -- see Error Handling)
- Human interview answers from Phase 2
- The writing style guide from `references/writing-style-guide.md` (injected into prompt)
- Their previous chapter content (if previous handbook exists, for continuity)
- User preferences (detail level, explanation style -- relevant subset only)
- Their specific task instructions from `references/agent-prompts.md`

Dispatch all core chapter writers plus any triggered conditional chapter writers in a single message. The total agent count ranges from 13 (no conditional chapters) to 16 (all three conditional chapters triggered).

### Core Chapters (always dispatched -- 13 agents)

| # | Chapter | Writer Prompt Key |
|---|---|---|
| 1 | Overview & Architecture | `chapter-overview` |
| 2 | Repository Map & Navigation | `chapter-repo-map` |
| 3 | Domain Model & Core Concepts | `chapter-domain` |
| 4 | Module Deep Dives | `chapter-modules` |
| 5 | Code Walkthroughs & Execution Flow | `chapter-walkthroughs` |
| 6 | Dependencies & Integration | `chapter-dependencies` |
| 7 | Configuration & Environment | `chapter-config` |
| 8 | Getting Started | `chapter-getting-started` |
| 9 | Testing Guide | `chapter-testing` |
| 10 | Design Rationale | `chapter-rationale` |
| 11 | Extension Guide, Change Recipes & Style | `chapter-extension` |
| 12 | Troubleshooting, Danger Zones & FAQ | `chapter-troubleshooting` |
| 13 | Glossary & Quick Reference | `chapter-glossary` |

Each chapter's content requirements and primary analysis-agent sources are fully specified in its writer prompt in `references/agent-prompts.md`.

### Conditional Chapters (dispatched only if Phase 0 detected evidence)

| Chapter | Prompt Key |
|---|---|
| Data Model & Persistence | `chapter-data-model` |
| Security & Permissions | `chapter-security` |
| Build, Deployment & Ops | `chapter-build-deploy` |

Insertion points and renumbering are defined in Phase 4 under Chapter Numbering.

### Chapter Writer Output Contract

Each writer returns a structured object:
- `title` -- chapter title
- `content` -- full markdown content for the chapter (headings start at H2)
- `cross_references` -- list of `{target_chapter, anchor, context}` for cross-linking during assembly
- `diagrams` -- list of Mermaid blocks with titles

Per-chapter format specs -- the layered `<details>` walkthrough format (Chapter 5), change recipe tables (Chapter 11), and danger zone callouts (Chapter 12) -- live with their writer prompts in `references/agent-prompts.md`.

---

## Phase 4 -- Assembly

Stitch all chapter outputs into a single markdown document. This phase is NOT dispatched to a subagent -- the host agent performs it directly. Read `templates/handbook-template.md` for the structural template.

### Assembly Order

1. **YAML frontmatter:**
   ```yaml
   ---
   title: "<Project Name> Handbook"
   generated_by: "/handbook"
   generated_at: "<ISO 8601 timestamp>"
   scope: "<scope or 'full project'>"
   profile: "handbook"
   commit: "<current git commit hash>"
   ---
   ```

2. **TL;DR Summary** -- Project purpose (1-2 sentences), key stats (language, file count, module count), architecture one-liner, tech stack, quick-links to most-used chapters (Getting Started, Code Walkthroughs, Extension Guide, Troubleshooting).

3. **Chapter content** in order -- core chapters 1-13, with conditional chapters inserted and renumbered per Chapter Numbering below.

4. **Cross-references** -- Resolve all `cross_references` from chapter writers into markdown links: `[See Change Recipes](#extension-guide-change-recipes-style)`.

5. **Metadata footer:**
   ```markdown
   ---
   *Generated <timestamp> at commit `<hash>` by `/handbook` v1.0.0*
   ```

### Chapter Numbering

When conditional chapters are present, all chapters must be renumbered sequentially. The insertion points are fixed:

| Conditional Chapter | Inserted After |
|---|---|
| Data Model & Persistence | Module Deep Dives (core ch 4) |
| Security & Permissions | Configuration & Environment (core ch 7) |
| Build, Deployment & Ops | Testing Guide (core ch 9) |

Example with all three conditional chapters present: chapters 1-4 (core), 5 (Data Model), 6-8 (core 5-7), 9 (Security), 10 (core 8-9), 11 (Build/Deploy), 12-16 (core 10-13).

### Assembly Validation

Before proceeding to Phase 5:
- Verify all expected chapters are present (note missing ones from failed agents)
- Verify all cross-reference targets exist as headings in the assembled document
- Verify Mermaid blocks are valid fenced code blocks with a diagram type keyword
- Verify chapter numbering is sequential with no gaps

---

## Phase 5a -- Mechanical Validation

Automated checks run before the review agent. No LLM dispatch needed -- the host agent runs these checks directly.

### Checks

1. **Source path validation:** For every `file:line` citation and relative source link in the assembled markdown, verify the file exists in the file inventory from Phase 0. Collect broken references into a list.

2. **Anchor integrity:** Extract all internal links (`[text](#anchor)`) and all heading anchors in the document. Report any link whose target anchor does not exist.

3. **Secret scan:** Scan the assembled markdown for patterns matching:
   - API keys: `(sk|pk|api[_-]?key)[_-]?[a-zA-Z0-9]{20,}`
   - Tokens: `(token|secret|password)\s*[:=]\s*[^\s]{8,}`
   - Connection strings: `(mongodb|postgres|mysql|redis)://[^\s]+`
   - AWS keys: `AKIA[0-9A-Z]{16}`
   Flag any matches for removal by the review agent.

4. **Mermaid syntax check:** For each ` ```mermaid ` block, verify it starts with a valid diagram type keyword (`graph`, `flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram`, `erDiagram`, `gantt`, `pie`, `gitgraph`). Flag blocks that do not.

5. **Duplicate content detection:** Compare chapter pairs for high textual overlap. Specifically check Domain Model (ch 3) vs. Data Model (conditional) if both exist. Flag pairs with >30% shared sentences.

Emit the validation report as a structured checklist. Pass it to Phase 5b.

---

## Phase 5b -- Review & Polish Pass

Dispatch a single review agent (`model: "opus"`) with:
- The full assembled markdown from Phase 4
- The mechanical validation report from Phase 5a
- The writing style guide from `references/writing-style-guide.md`
- The project context block from Phase 0

### Review Agent Tasks

The review agent prompt is in `references/agent-prompts.md`. The agent performs these tasks in order:

1. **Fix all mechanical validation issues:**
   - Remove or correct broken source links
   - Fix broken internal cross-references
   - Remove any detected secrets (replace with `<REDACTED>`)
   - Fix or remove broken Mermaid blocks
   - Deduplicate overlapping content between chapters

2. **Style consistency:**
   - Ensure all chapters use the same voice and tone (per writing style guide)
   - Normalize heading levels (H1 for chapter titles, H2 for sections, H3 for subsections)
   - Ensure consistent formatting for code references, file paths, and technical terms

3. **Content quality:**
   - Add transition sentences between chapters where flow is abrupt
   - Verify the TL;DR summary accurately reflects the full handbook content -- update if stale
   - Flag any remaining uncertain or inferred claims with: `*[Inferred -- not confirmed by code]*`

4. **Return** the complete polished markdown. The review agent MUST NOT truncate or omit any chapter.

---

## Phase 6 -- HTML Rendering

### Output Files

| File | Description |
|---|---|
| `docs/handbook/handbook.md` | Source markdown -- the complete handbook in portable markdown format |
| `docs/handbook/handbook.html` | Self-contained HTML with Mermaid SVG, collapsible sections, TOC sidebar, syntax highlighting |
| `.claude/skill-context/handbook.md` | Persisted interview context for future runs |

### Step 6.1: Write Markdown

Write the polished markdown to `docs/handbook/handbook.md`. Create the directory if it does not exist.

### Step 6.2: Render Portable HTML

Call the renderer with the `handbook` profile. The renderer inlines all vendor CSS/JS into the template skeleton at render time, producing a single file with zero external dependencies. **Resolve `scripts/html_render.py` to its absolute path under the plugin root (two levels above this SKILL.md) before running** — the command executes in the user's project working directory, which does not contain the plugin's `scripts/` folder.

```bash
python scripts/html_render.py docs/handbook/handbook.md --profile handbook
```

The `handbook` profile differs from the `analytical` profile used by `/explain`:
- Does NOT require a git repo (no `find_repo_root`)
- Does NOT bootstrap `docs/.assets/report-lib/`
- Does NOT use `$assets-rel$` template variable
- Output is larger (includes all CSS/JS) but fully portable

This produces `docs/handbook/handbook.html` -- a single self-contained HTML file.

**Self-contained requirements:**
- All CSS inlined (report-base.css + Prism themes + handbook-specific styles)
- All JS inlined (Prism + Mermaid + report-init.js)
- No external fonts or CDN links
- Single file, sharable via email/Slack/etc.

**Layout and interactivity:** The TL;DR hero, sticky collapsible TOC sidebar, responsive and print styles, collapsible code walkthroughs, danger-zone callout styling, syntax highlighting, theme toggle, and footer are implemented by the `handbook` render profile and its template -- no additional layout work is needed. (Metadata footer content is set during Phase 4 assembly.)

### Step 6.3: Report Results

Display completion summary:

```
Handbook generated:
  Markdown: docs/handbook/handbook.md
  HTML:     docs/handbook/handbook.html (<size>)
  Chapters: <count> (<list conditional chapters if any>)
```

If HTML rendering fails, report the error but still deliver the markdown:

```
HTML render failed (markdown still saved): <error>
  Markdown: docs/handbook/handbook.md
```

---

## Agent Count Summary

| Phase | Agents | Notes |
|---|---|---|
| Phase 1 (Analysis) | 6 | All dispatched in single message, `model: "opus"` |
| Phase 3 (Chapter Writers) | 13-16 | 13 core + 0-3 conditional. All in single message, `model: "opus"` |
| Phase 5b (Review) | 1 | Single review agent, `model: "opus"` |
| **Total** | **20-23** | Depending on conditional chapters |

---

## Guardrails

1. **Evidence over guesswork** -- Every claim cites `file:line`. Uncertain inferences are marked: "*[Inferred -- not confirmed by code]*"
2. **No fabricated content** -- If a conditional chapter has insufficient evidence, skip it entirely rather than generating thin content.
3. **Relative links only** -- All source links use relative paths from `docs/handbook/` (e.g., `../../src/server.ts#L42`).
4. **No secrets in output** -- Agents must never include env values, API keys, tokens, or passwords. Config examples use placeholders (`<DATABASE_URL>`, `<API_KEY>`).
5. **Interview context is persistent** -- Answers saved to `.claude/skill-context/handbook.md` carry forward to future runs, preventing repeated questions.
6. **Previous handbook awareness** -- On subsequent runs, chapter writers receive previous chapter content to maintain continuity. Writers follow current codebase state -- previous content is advisory only.
7. **No code modification** -- The skill is read-only with respect to source code. No files outside `docs/handbook/` and `.claude/skill-context/handbook.md` are written.
8. **Change recipes reference real paths** -- Every file path in a change recipe table must be validated against the actual codebase file inventory.

---

## Error Handling

| Condition | Action |
|---|---|
| Scoped path does not exist | Report: "Path not found: `<path>`. Check the path and try again." |
| No source files found in scope | Report: "No source files found in `<scope>`. Check the path and try again." |
| Scope too large (>5000 source files) | Warn and ask for confirmation before proceeding (warning text in Step 0.6). |
| 1-2 analysis agents time out or fail | Synthesize from available agents. Note the missing analysis domain in affected chapters. Offer to retry. |
| All 6 analysis agents fail | Report: "Analysis failed -- cannot generate handbook. Try a narrower scope." |
| Agent returns malformed output | Use what is parseable from the agent, note the issue in the affected chapter. |
| All chapter writers fail | Report: "Chapter generation failed. Analysis data is available but could not be assembled into chapters." |
| User declines or cancels interview | Proceed with AI-inferred content. Mark uncertain sections with visual indicators. |
| JSONL chat logs unavailable | Proceed without conversation context -- interview covers the gap. |
| No tests/DB/CI in project | Conditional chapters do not appear. Testing Guide notes "no test infrastructure detected." |
| Previous handbook is stale | Chapter writers use it as reference but are not bound by it -- they follow current codebase state. |
| Previous handbook is corrupted/unparseable | Ignore previous handbook, proceed as fresh generation. Note in output. |
| `html_render.py` fails | Deliver markdown only. Report the error with the markdown path (report format in Step 6.3). |
| Pandoc not installed | Report: "pandoc is required for HTML rendering but was not found on PATH. Install: `choco install pandoc` / `brew install pandoc`. Markdown output is still available." |
