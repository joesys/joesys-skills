---
name: explain
description: "Use when the user invokes /explain to analyze a codebase, directory, file, symbol, or feature and produce a layered explanation report. SKIP if the user asks why code was built the way it is — that's /why."
---

# Explain Skill

Run five analysis subagents in parallel. Each one is a lens: structure, behavior, domain and data, external dependencies, and health and risk. Then combine their findings into one layered report that goes from a 30-second overview to deep understanding.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`.

## Out of Scope

This skill MUST NOT:
- Modify the code being explained, not even an obvious typo or a broken import. The skill describes. To fix code, the user runs `/codereview` or fixes it by hand.
- Run write-mode tools (formatter `--fix`, linter `--fix`, code generators). Use read-only commands only.
- Cite benchmarks, comparisons, or "industry standards" without naming the source. Unsourced numbers read as fabrication.
- Add a "fix this" or "improve this" step. If the user wants improvements after the report, they run `/codereview` or `/readability-review`.

## Invocation

| Invocation | Scope |
|---|---|
| `/explain` | Whole project (default) |
| `/explain src/auth/` | Directory/module |
| `/explain src/auth/oauth.ts` | Single file |
| `/explain MyClassName` | Class/symbol |
| `/explain "how does payment processing work?"` | Feature trace (natural language question) |
| `/explain --save` | Any of the above + write output to file |
| `/explain --save --no-html` | Save the markdown report only — skip HTML rendering for this run |
| `/explain --save --path docs/onboarding/` | Custom save location |

Arguments can be combined. Choose the scope mode from the argument: an existing file or directory path (search by name if there is no exact match), a single identifier for a symbol, a question or phrase for a feature trace, or nothing for the whole project. If an argument matches more than one file, directory, or symbol, list the matches and ask the user to choose. If the invocation is unclear, ask before you start.

---

## Phase 1: Preparation

### 1.1 Load User Preferences

Read `shared/skill-context.md` for the protocol. Read `.claude/skill-context/preferences.md` and `.claude/skill-context/explain.md` if they exist; otherwise use defaults.

Give each subagent only the preferences that affect its lens, as a `## User Preferences` section — for example detail level, explanation style, and assumed knowledge. A top-down or bottom-up preference in `explain.md` sets the order of the Structure lens.

### 1.2 File Gathering

For directory, single-file, and symbol scopes, resolve the file list once and pass it to every subagent. For whole-project and feature-trace scopes, the subagents explore on their own.

### 1.3 Scope Size

For very large scopes (roughly 500+ source files), tell the user the analysis may take several minutes and offer to narrow the scope before you start. Continue without asking if the user has already said to run the full scope.

---

## Phase 2: Parallel Analysis — 5 Lenses

Run the five lenses in parallel as subagents.

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

Each subagent prompt contains, in this order:
- The full Guiding Principles block below.
- The **absolute path** to `references/diagram-standards.md` in this skill's own folder (not the project's working directory), with one line that tells the subagent to read that file before it draws a diagram. Do not copy the file into the prompt. Read it yourself too: the Architecture Overview in Phase 3 follows it.
- The relevant user preferences.
- The lens template from `references/agent-prompts.md`, with `<SCOPE_DESCRIPTION>` filled in and `<FILE_LIST if applicable>` replaced by the file list (or the line removed when there is no list).

### Guiding Principles (included in every subagent prompt)

1. **Evidence over guesswork.** Tie every claim about what the code does to a specific file, function, or config.
2. **Flag uncertainty.** Separate what the code definitely does, what seems intended, and what is unclear. Saying "unclear" is valid output. Guessing confidently is not.
3. **Use LSP tools if available.** Otherwise search and read the code with the tools your host provides. Missing LSP is not a failure.
4. **Respect the scope.** Mention outside context where it helps ("this module is called from `src/api/routes.ts`"), but do not analyze unrelated modules.
5. **Point to code; don't copy it.** Use `file:line_number` references and only short snippets. The reader has the code and needs understanding, not a copy.
6. **Draw diagrams only in Mermaid**, following the Diagram Standards file named in this prompt.
7. **No value judgments outside Health & Risk.** Lenses 1–4 describe and explain; they never say "this is good" or "this is bad." Only the Health & Risk lens assesses quality and risk, and it reports facts — what is fragile, unclear, or risky to change — not whether the architecture is good.
8. **Write for humans.** The reader may use English as a second language. Use short sentences and everyday words, and explain jargon the first time. Simplify the language, never the facts.

### Subagent Roster

| # | Lens | Focus |
|---|---|---|
| 1 | Structure & Entry Points | Module boundaries, organization pattern, entry points, dependency graph, file conventions |
| 2 | Behavior — Key Workflows | Trace the workflows that best explain the system end-to-end |
| 3 | Domain & Data | Data models, state transitions, domain glossary, storage mapping |
| 4 | External Dependencies | External services, infrastructure, integration patterns |
| 5 | Health & Risk | Hotspots, churn, debt, test signals, git history, fastest path to competence |

---

## Phase 3: Synthesis

After all subagents finish (or fail — see Graceful Degradation), combine their findings into the report.

### Synthesis Rules

1. **TL;DR:** At most 3 sentences, drawn from structure, behavior, and health.
2. **Orientation Cheat Sheet:** Take each answer from whichever lens found it. Write "unclear" when no lens could answer. Omit for single-file and symbol scopes.
3. **Deduplication:** When several lenses mention the same file or concept, put it in the most relevant section once.
4. **Keep uncertainty flags.** Never upgrade "seems like" to "definitely" during synthesis.
5. **Section order:** Use the fixed order below. It moves from overview to specifics to action.
6. **Architecture Overview:** Combine the Structure and External Dependencies graphs into one top-level graph. Show shared nodes (for example "Postgres") once, internal modules at the center, and external services at the edge. Keep each lens's own inline graphs as they are.

### Output Structure

~~~
## TL;DR
3 sentences. What it is, why it exists, how it's organized.

## Orientation Cheat Sheet
(omitted for single file and symbol scopes)

| Question | Answer |
|---|---|
| Tech stack | ... |
| Primary language / framework | ... |
| Where are the entry points? | path/to/file |
| Where is the business logic? | path/to/dir |
| Where is the data model? | path/to/file |
| Where are the tests? | path/to/dir |
| Where is the config / env? | path/to/file |
| Who are the active contributors? | names from git |
| What's the most fragile part? | from Health agent |
| What should I not touch without care? | from Health agent |

## Architecture Overview
(omitted for single file and symbol scopes)
[Composed from the Structure module graph + the External Dependencies integration map]

## Structure & Entry Points
[Agent 1 findings, edited for flow — includes the module dependency graph]

## Behavior — Key Workflows
[Agent 2 findings — traced flows with call chains and flow diagrams]

## Domain & Data
[Agent 3 findings — models, glossary, state transitions, state diagram if applicable]

## External Dependencies
[Agent 4 findings — includes the integration map]

## Health & Risk
[Agent 5 findings — hotspots, debt, uncertainty]

## Fastest Path to Competence
[From Agent 5]
- Files to read next, in order
- Workflows to trace next
- Areas to avoid touching without understanding first
~~~

Without `--save`, show the full report in the conversation.

---

## Phase 4: Save (optional)

Only when `--save` is present.

### Save location
Default: `docs/explain/<scope-name>.md`. `--path <dir>` replaces the directory; the file name stays the same. Create the directory if it does not exist.

Scope name:
- Whole project → `project.md`
- Directory `src/auth/` → `src-auth.md`
- Single file `src/auth/oauth.ts` → `src-auth-oauth-ts.md`
- Symbol `MyClassName` → `myclassname.md`
- Feature trace → 2–4 key nouns from the question in kebab-case (e.g., "how does payment processing work?" → `payment-processing.md`)

### Save behavior
1. Write the full report to the resolved path with this YAML front-matter at the top:
   ```markdown
   ---
   title: "<scope-derived title>"
   generated_by: "/explain"
   generated_at: "<ISO 8601 UTC timestamp>"
   scope: "<resolved scope>"
   profile: "analytical"
   ---
   ```
2. **Render the HTML companion** unless `--no-html` is present. This is best-effort: if it fails, warn and continue, because the markdown is already saved. **Resolve `scripts/html_render.py` to its absolute path under the plugin root before running** — the command runs in the user's project, which does not contain the plugin's `scripts/` folder (use `python3` where present, `python` on Windows):
   ```bash
   python scripts/html_render.py <report-path>.md --profile analytical
   ```
   The renderer writes `<report-path>.html` next to the markdown. See `shared/html-reports.md` for details.
3. In the conversation, show the TL;DR and Cheat Sheet, then the saved paths: always the `.md` path, plus the `.html` path only if rendering succeeded. If rendering failed, add a one-line warning.

---

## Graceful Degradation

| Situation | Behavior |
|---|---|
| Some subagents fail or time out | Synthesize from the rest. Name the missing lenses in the report and offer to retry them. |
| All subagents fail | Report the failure. Suggest retrying or narrowing the scope. |
| No git history | Health & Risk skips git history and says so. |
| Tiny repo (< 5 source files) | Skip the subagents and do one direct analysis. |
| Very large scope | Lenses focus on the most significant files and modules instead of full coverage. |
| Binary or generated files in scope | Skip them and note that they exist. |
| Unreadable files (permission denied) | Skip them and list them in the report as skipped. |

## Error Handling

| Error | Behavior |
|---|---|
| File, directory, or symbol not found | Say what was not found and stop. For a symbol, suggest a different name or a file path. |
| Symbol matches many results (>10) | Show the first 10 and ask the user to narrow the scope. |
| Unrecognized flag | Name the flag and list the supported flags: `--save`, `--path <dir>`, `--no-html`. |
| `--path` points to a file | Explain that `--path` must be a directory. |
| `--path` directory cannot be created | Report the error. |
