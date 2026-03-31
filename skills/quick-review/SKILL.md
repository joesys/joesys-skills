---
name: quick-review
description: "Use when the user invokes /quick-review for a fast bug-focused code review using cross-model parallel analysis (correctness + security, P0-P2 only)."
---

# Quick Review Skill

Fast, bug-focused code review. Dispatches correctness and security subagents alongside a cross-model reviewer (Codex↔Claude) in parallel, with streamlined static analysis. Reports only P0-P2 findings — no style nits, no architecture suggestions.

For comprehensive 6-domain reviews, use `/code-review` instead.

## Invocation

Parse the user's `/quick-review` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `/quick-review` | Branch diff (default) | Current branch vs. fork point |
| `/quick-review src/utils/` | Directory scan | All files recursively in specified directory |
| `/quick-review --file src/main.py` | Single file | One specific file |
| `/quick-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/quick-review --commit abc123` | Commit review | Files changed in a specific commit |
| `/quick-review --include-gemini` | Add Gemini | Combinable with any mode |

Arguments are combinable. Examples:
- `/quick-review --pr 42` — review PR #42
- `/quick-review --include-gemini` — add Gemini as a third reviewer
- `/quick-review --file src/main.py --include-gemini` — single file, three models

The `--include-gemini` flag affects Phase 2 dispatch only — Phase 1 scope resolution is identical regardless of this flag.

If the invocation is ambiguous or the argument is unrecognizable, ask the user to clarify before proceeding.

---

## Phase 1: Scope Resolution

### 1.1 Base Branch Detection

Determine where the current branch diverged. Check candidates in order:

1. The upstream tracking branch (e.g., `origin/feature-x` tracks `origin/main`)
2. `main`
3. `master`

If none exist or the result is ambiguous, ask the user: "Which branch should I compare against?"

Compute the fork point:

```bash
git merge-base <base-branch> HEAD
```

### 1.2 File Gathering

Gather the list of files to review based on the resolved mode:

| Mode | Command |
|---|---|
| Branch diff | `git diff --name-only <base>...HEAD` |
| Directory scan | All files recursively in the specified directory, respecting `.gitignore` |
| Single file | The specified file path |
| PR review | `gh pr diff <number> --name-only` |
| Commit review | `git diff --name-only <commit>^..<commit>` |

### 1.3 Context Loading

Unlike the full code-review skill (which loads entire files), quick-review loads only the diff with expanded context:

```bash
git diff -U50 <base>...HEAD
```

The `-U50` flag expands each hunk to include ~50 lines of surrounding context — enough for local scope, function signatures, variable declarations, and control flow, without loading entire files.

This is the primary time savings over the full code-review. Both host AI subagents and the cross-model dispatch receive the same context.

### 1.4 Target Language Detection

Infer the primary language from file extensions:

| Extension | Language |
|---|---|
| `.ts`, `.tsx` | TypeScript |
| `.js`, `.jsx` | JavaScript |
| `.py` | Python |
| `.rs` | Rust |
| `.go` | Go |
| `.java` | Java |
| `.cs` | C# |
| `.rb` | Ruby |
| `.php` | PHP |
| `.swift` | Swift |
| `.kt` | Kotlin |
| `.cpp`, `.cc`, `.h` | C++ |

If the changeset is polyglot, note all languages and instruct subagents to use the correct language per file.

### 1.5 Static Analysis (Streamlined)

Read the shared tooling registry and per-language profiles:
- `shared/tooling-registry.md` — for detection protocol
- `shared/tooling/{language}.md` — for each detected language
- `shared/tooling/general.md` — for cross-language tools

Follow a streamlined detection flow:

1. **Detect config files**: Glob for each tool's detection markers.
2. **Check availability**: Run `which`/`where` for each tool's binary.
3. **Classify**: Mark each tool as `available`, `configured-but-unavailable`, or `absent`.
4. **Build scoped commands**: For `available` tools, construct report-only commands targeting only the changed files.
5. **Auto-run read-only tools**: Linters, type checkers, and SAST tools are read-only — execute them without a safety gate. Tools marked with `⚠️ DANGER: auto-modifies` in per-language profiles are **skipped** (quick-review never runs auto-modifying tools).
6. **30-second timeout per tool**: Hard cap. If a tool exceeds 30 seconds, kill it and continue.
7. **Build TOOLING_CONTEXT**: Assemble the slim version (findings only — no gap analysis, no build-integrated detection). Same format as code-review's slim TOOLING_CONTEXT.

For large output (>50 findings from a single tool): summarize as "{tool} reported N violations: X errors, Y warnings", include top 3 most severe, tell user: "Run `{exact command}` for full results."

If a tool fails: report error, skip tool, continue.
