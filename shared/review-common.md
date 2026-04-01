# Shared Review Infrastructure

Reference file for code-review and quick-review skills. Read this file
during Phase 1 (Scope Resolution) — it contains the shared logic for
base branch detection, file gathering, and target language detection.

## Base Branch Detection

Determine where the current branch diverged. Check candidates in order:

1. The upstream tracking branch (e.g., `origin/feature-x` tracks `origin/main`)
2. `main`
3. `master`

If none exist or the result is ambiguous, ask the user: "Which branch should I compare against?"

Compute the fork point:

```bash
git merge-base <base-branch> HEAD
```

## File Gathering

Gather the list of files to review based on the resolved mode:

| Mode | Command |
|---|---|
| Branch diff | `git diff --name-only <base>...HEAD` |
| Directory scan | All files recursively in the specified directory, respecting `.gitignore` |
| Single file | The specified file path |
| PR review | `gh pr diff <number> --name-only` |
| Commit review | `git diff --name-only <commit>^..<commit>` |

## Target Language Detection

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

If the changeset is polyglot, note all languages and instruct each subagent to use the correct language per file. Subagents must **never** emit before/after examples in a language other than the target file's language.

## Static Analysis Tooling — Detection Protocol

Read the shared tooling registry and per-language profiles:
- `shared/tooling-registry.md` — for detection protocol and safety rules
- `shared/tooling/{language}.md` — for each detected language
- `shared/tooling/general.md` — for cross-language tools

Follow the detection flow:

1. **Detect config files**: Glob for each tool's detection markers.
2. **Check availability**: Run `which`/`where` for each tool's binary.
3. **Classify**: Mark each tool as `available`, `configured-but-unavailable`, or `absent`.

Steps 4+ diverge per skill — see skill-specific SKILL.md for execution,
safety gates, and TOOLING_CONTEXT assembly.

For large output (>50 findings from a single tool): summarize as "{tool} reported N violations: X errors, Y warnings", include top 3 most severe, tell user: "Run `{exact command}` for full results."

If a tool fails (crash, not a findings exit code): report error, skip tool, continue.

## Shared Error Handling

| Error | Action |
|---|---|
| No changed files found | "No changes detected on this branch vs. `<base>`. Try specifying a file or directory." |
| Base branch detection fails | Ask: "Which branch should I compare against?" |
| PR number not found | "PR #N not found. Check the number and try again." |
| Commit hash not found | "Commit `<hash>` not found. Check the hash and try again." |
| File not found (single file mode) | "File `<path>` not found. Check the path and try again." |
| No violations found | "No violations detected. Code looks solid." (code-review) / "No bugs or security issues found. Code looks solid." (quick-review) |
| Too many files (>100) | Warn the user about scope size, suggest narrowing with `--file` or a subdirectory, proceed if confirmed. |
| Tool binary not found | Classify as `configured-but-unavailable`, skip, continue review |
| Tool crashes or times out | Report error, skip tool, continue with remaining tools |
| Tool output unparseable | Include raw summary in report, skip structured merge |
