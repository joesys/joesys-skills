# Shared Review Infrastructure

Reference file for `$codereview` and `$quick-review`. Read it during scope resolution. It holds the review rules, base branch detection, file gathering, the severity scale, and the shared error table.

---

## Cross-Skill Discipline (Read First)

These rules apply to every review skill that reads this file. Paste the block below, word for word, into the prompt of every subagent that reviews code. The block is short, and a rule inside the prompt is always in front of the reviewer. The orchestrator also follows `./report-style.md` for everything a person reads.

```
## Review Rules
1. Evidence: every finding cites a specific `file:line`. If you cannot point to the line, do not report it.
2. Be specific: state the problem and a concrete fix. "Consider refactoring" is not a finding.
3. Examples use the language of the file under review. Never switch to another language.
4. No over-engineering: do not suggest layers, interfaces, or patterns for code with one use. Build for today's need, not a possible future one.
5. Tests: repeated setup that keeps each test easy to read is fine (DAMP over DRY). Do not flag it.
6. Performance: flag clear algorithmic problems (N+1 queries, needless quadratic work, blocking calls in async code) on paths whose input can grow. Skip micro-optimizations that no measurement supports.
7. Duplication: suggest extracting shared code to remove duplication only at three or more copies (Rule of Three). Two copies of one fact or rule that must stay in sync are still a finding. Extracting a function because it makes the code read better needs no second copy.
8. Severity follows impact. Do not inflate severity to look thorough. Do not lower a real bug to keep the report short.
9. Write for humans: the reader may speak English as a second language. Use short sentences, everyday words, and explain jargon on first use. State the point first, then the detail. Simplify the language, never the facts — paths, line numbers, and claims stay exact.
```

---

## Base Branch Detection

Compare against the branch's upstream base if one is set, otherwise `main`, otherwise `master`. The fork point is `git merge-base <base-branch> HEAD`. If no candidate exists or the choice is unclear, ask: "Which branch should I compare against?"

---

## File Gathering

| Mode | Command |
|---|---|
| Branch diff | `git diff --name-only <base>...HEAD` |
| Directory scan | All files recursively in the specified directory, respecting `.gitignore` |
| Single file | The specified file path |
| PR review | `gh pr diff <number> --name-only` |
| Commit review | `git diff --name-only <commit>^..<commit>` |

---

## Target Language Detection

Infer each file's language from its extension. A change can mix languages. Every code example uses the language of the file it is about.

---

## Static Analysis Tooling — Detection Protocol

Read `./tooling-registry.md`, `./tooling/{language}.md` for each detected language, and `./tooling/general.md`. Profiles exist for TypeScript, JavaScript, Python, Rust, Go, C++, C#, and GDScript. Other languages use the general profile only. If a language has no usable profile, skip tool detection for it and say so in the report.

1. **Detect config files** — glob for each tool's detection markers.
2. **Check availability** — check that each tool's binary is on PATH.
3. **Classify** — mark each tool `available`, `configured-but-unavailable`, or `absent`.

Each skill defines what happens next. Running tools, large output, and tool failures follow `./tooling-registry.md` § 4.

---

## Severity Scale

Shared severity definitions (quick-review reports P0–P1 only; codereview reports P0–P4):

| Priority | Type | Examples | Fix When |
|---|---|---|---|
| P0: Critical | Security, data loss, bugs | Hardcoded secrets, SQL injection, off-by-one causing data corruption, null dereference, race conditions | Immediately |
| P1: High | Bugs waiting to happen | Missing error handling, silent failures, N+1 queries, incorrect boolean logic, unhandled edge cases | This PR |
| P2: Medium | Maintainability | DRY violations (3+), god classes, deep nesting, missing caching | When touching file |
| P3: Low | Polish | Magic numbers, naming, minor duplication | If time permits |
| P4: Optional | Style | Formatting, comment cleanup, micro-optimizations | Boy Scout Rule |

### Tool Severity Mapping

When a tool finding has no matching AI finding, map the tool's severity to the review scale:

| Tool Severity | Review Priority |
|---|---|
| error | **P1** (or **P0** if security-related) |
| warning | **P2** |
| style / info | **P3** |

Quick-review drops tool findings below P1.

### Severity Discipline

Review Rule 8 applies: do not inflate severity, and do not lower a real bug. P0 means a real bug or security hole; style polish is P3 or P4. Severity follows impact, not the source. Real bugs usually have high impact, so correctness findings are usually P0 or P1. Do not raise a finding's severity only because of which reviewer found it.

---

## Shared Error Handling

| Error | Action |
|---|---|
| No changed files found | "No changes detected on this branch vs. `<base>`. Try specifying a file or directory." |
| Base branch detection fails | Ask: "Which branch should I compare against?" |
| PR number not found | "PR #N not found. Check the number and try again." |
| Commit hash not found | "Commit `<hash>` not found. Check the hash and try again." |
| File not found (single file mode) | "File `<path>` not found. Check the path and try again." |
| Not a git repository | For git-based modes (branch/PR/commit): report "This isn't a git repository — try directory-scan or `--file` mode instead of asking for a base branch." Do not loop on base-branch selection. |
| `gh` missing or unauthenticated (PR mode) | Check `gh` availability before PR mode; if absent, report "PR mode needs the GitHub CLI — install it and run `gh auth login`, or use branch-diff / `--commit` mode." |
| No violations found | codereview: "No violations detected. Code looks solid." quick-review: "No bugs or security issues found. Code looks solid." |
| Too many files (>100) | codereview: split the change into clusters (codereview Phase 1.4) — no warning needed. quick-review: warn about scope size, suggest narrowing with `--file` or a subdirectory, proceed if confirmed. |
| Tool missing, crashing, timing out, or unparseable | Follow `./tooling-registry.md` § 4. Skip that tool and continue the review. |
