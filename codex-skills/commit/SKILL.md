---
name: commit
description: "Use when the user invokes $commit or any git commit is about to be created \u2014 applies Conventional Commits, the structured body format, and OneFlow Option 3 merge bubbles for multi-commit changes."
---

# Commit Skill

Create git commits with clear, structured messages (Conventional Commits plus a fixed body format). When one change splits into several logical commits, put them on a short-lived branch and merge it back with `--no-ff` (OneFlow Option 3), so the group shows as one merge bubble.

This skill only adds new commits. It never rewrites existing history. To group commits that already exist, use `$restructure-commit`.

## Write for Humans

Everything a person reads from this skill - the commit body prose (intent paragraph, `[--- Changes ---]` bullets, `[--- AI Review ---]` assessment) and conversation replies - MUST use plain language that a non-native English reader can follow. The Conventional Commits header keeps its own format; this rule shapes the prose, not the structure. Before writing a commit body or a long reply, read `../shared/report-style.md` (resolve against the collection root (one level above this SKILL.md) - never the project's working directory) and follow it. In short: short sentences, everyday words, jargon explained on first use, the point stated first. Simplify the language, never the facts - paths, line numbers, and claims stay exact.

## Out of Scope

This skill MUST NOT:
- Run `git push` in any form without express current-turn authorization (see Preflight).
- Rewrite existing commits: no hard resets, no cherry-picking, no rebasing of published work. Regrouping existing commits belongs to `$restructure-commit`.
- Use `--amend` on commits already pushed to a remote.
- Commit secrets, credentials, API keys, or `.env` files. **MUST check** staged files first. If a file looks suspicious, ask.
- Bundle unrelated changes into one commit just to be quick. Propose a split instead.
- Add a `Co-Authored-By` trailer. The `[--- AI Review ---]` header already names the model.
- Skip the body format. Every commit has the intent paragraph, `[--- Changes ---]`, and `[--- AI Review ---]`.
- Soften the AI Review to be flattering. "Looks good!" is not a review.

## Preflight: Never `git push` Without Express Authorization

**Absolute rule:** Do NOT run `git push` in any form - normal, `--force`, `--force-with-lease`, tag push, branch push - unless the user's **current-turn** message contains a direct, unambiguous instruction to push **this specific push**. This rule overrides every other instruction in this skill.

**Plan approval != push approval.** If a plan or prior turn listed a push as a step and the user said "proceed" / "go ahead" / "do it" / "yes" to that plan, that is **NOT** push authorization. Those words authorize non-push work only. At the push step: STOP, present the exact `git push ...` command, ask `"push to origin? yes/no"`, and wait for a push-specific answer.

**Express orders that DO authorize a push:** "push it", "push now", "push to origin", "send it", "publish", or equivalent current-turn directive naming the push action.

**Auto mode does NOT relax this rule. Solo-developer branches do NOT relax this rule. A rewrite that "needs" a force push does NOT relax this rule** - the need for the push is a reason to ask, not a reason to proceed.

If unsure whether something counts as an express order, assume it does **NOT**. Ask.

**Incident of record:** 2026-04-20 - a force-push landed during auto-mode execution before the user could intervene. The user's stated expectation: *"I DON'T WANT THIS TO EVER HAPPENED AGAIN."* This rule exists to prevent a recurrence.

## User Preferences

Read `../shared/skill-context.md` (resolve `../shared/...` against the collection root (one level above this SKILL.md) - never the project's working directory). Load `.codex/skill-context/preferences.md` and `.codex/skill-context/commit.md` if they exist. Never interview the user about preferences - commits are fast, transactional operations. If no preferences exist, use sensible defaults. The user can create `.codex/skill-context/commit.md` by hand.

| Preference | Effect |
|---|---|
| Detail level: concise / detailed | Shorter or richer intent paragraph and changes section |
| Max subject length | Overrides the ~72 character guideline |
| Always include scope | Never write a scopeless subject |
| Custom scopes | Pick scopes from the project's list |
| `auto-devlog scrap: off` | Skip the Post-Commit devlog scrap step (default is on) |

## Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for the subject line:

```
type(scope): description
```

- **Common types:** `docs`, `fix`, `feat`, `refactor`, `build`, `test`, `chore`, `ci`, `style`, `perf`
- Make the description name the concrete outcome in plain language. Do not lead with an internal process label, evidence identifier, metaphor, or ceremony.
- Use an em dash (-) only when a short elaboration makes the outcome clearer.
- Pick the most specific scope that fits. If changes span multiple areas, use the primary one.
- Derive scopes from the project's own directory structure and domain concepts.

### Examples

```
feat(auth): add JWT refresh token rotation - prevent stale session hijack
refactor(api): make route handlers async - replace blocking calls with awaited promises
docs(readme): update setup instructions - add Docker prerequisites
chore(config): make paths portable - relative refs from project root
build(deps): add zod v3.22 - runtime schema validation for API inputs
```

## Plain-Language Standard

Write every commit message for a durable reader: either a teammate who
understands the project in general but does not know today's task, internal
shorthand, or recent session history, or the author returning years later.

- Prefer ordinary words, short sentences, and active voice.
- State the concrete outcome before supporting evidence or implementation detail.
- When an acronym, gate name, code name, identifier, statistic, or specialized term is necessary, explain it on first use and say why it matters.
- Include hashes, counts, paths, and symbols only when they provide useful evidence or traceability. Do not make the reader decode raw inventory.
- Metaphors, slogans, ceremonial language, and dramatic descriptions MUST NOT replace concrete actions and outcomes.

Plain language does not mean removing technical accuracy. Keep the technical
details that help a future reader understand the decision, verify important
evidence, or recognize a risk; translate or omit details that only make sense
inside the current session.

### Before and after

```text
Before: feat(research): the Gate-6 development-vintage mint - fingerprint 14d908e0
After:  feat(research): record the July 13 development data snapshot
```

The body should preserve the important incident and remaining risk without
requiring the reader to know the project's shorthand:

```text
The snapshot-generation script still uses a manually updated output date. It
initially overwrote the July 12 snapshot, which was restored exactly before the
new snapshot was saved under July 13. The date handling should be fixed before
this becomes a routine process.
```

## Body

After the subject line, the body has three parts:

**1. Intent paragraph (2-3 sentences, no header)**
Explain the problem or need, the outcome, and why it matters. Give enough context for a reader who was not part of the current task. Start immediately after the blank line following the subject.

**2. `[--- Changes ---]`**
Summarize observable outcomes and important technical decisions. Organize by file or category when that helps, but do not inventory every edited line or repeat the diff. Include counts, paths, symbols, and hashes only when they provide useful evidence or traceability, and explain their significance.

**3. `[--- AI Review (<model name>) ---]`**
Give an honest assessment in direct, ordinary language. Use your current model name in the header (for example, `[--- AI Review (<model name>) ---]` with the real name filled in). State meaningful strengths, risks, trade-offs, and follow-up work without promotional, theatrical, or self-congratulatory prose.

### Durable-reader check

Before creating the commit, reread the complete message and ask:

> Could a teammate unfamiliar with this task, or the author returning years later, understand why this commit exists, what changed, and what still needs attention without the issue tracker or session history?

If the answer is no, rewrite the message before creating the commit.

## Signing Failure Recovery

If a `git commit` (or `git merge --no-ff`, or `git commit --amend`) fails with `error: 1Password: failed to fill whole buffer` or similar 1Password SSH signing errors, **retry the same command** with `-c commit.gpgsign=false` to bypass signing. Do not ask the user - they may be away. Log a note after the commit so the user knows it is unsigned:

> **Note:** Commit `<hash>` is unsigned - 1Password SSH agent was unresponsive. Re-sign later with:
> `git rebase --exec "git commit --amend --no-edit" <parent-hash>`

This applies to every commit and to `git merge --no-ff` commands.

## Branching Strategy (OneFlow Option 3)

[OneFlow](https://www.endoflineblog.com/oneflow-a-git-branching-model-and-workflow) keeps one long-lived branch. Work happens on short-lived branches that merge back. **Option 3** merges with `--no-ff`, which creates a merge commit around the branch's commits - a visible "bubble". `git log --oneline` still reads almost linearly, `git log --graph` shows the groups, and a whole group can be reverted with `git revert -m 1 <merge-commit>`.

Rules:
- **Use a branch only when the change splits into 2 or more commits.** A single commit goes directly on the current branch.
- **Minimum bubble size is 2 commits.** If the branch ends up with 1 commit, fast-forward merge instead of `--no-ff`. A bubble around one commit adds noise.
- **Cascading merge rule:** always merge back into the branch you started from (the **parent branch**). If you are on `feat/auth` and create `feat/auth-tests`, merge back into `feat/auth`, not `main`.
- **Branch name:** `<type>/<short-description>` in kebab-case, from the overall theme. Examples: `feat/jwt-refresh-rotation`, `refactor/async-route-handlers`.

## Workflow

### Step 1 - Gather context

Run in parallel:
- `git status`
- `git diff HEAD` (all staged and unstaged changes against the last commit)
- `git log --oneline -10`

### Step 2 - Decomposition analysis

Decide whether the uncommitted work holds more than one logical unit. A unit is a set of changes that serves one purpose.

**Signs of several units:** changes span unrelated scopes; refactoring is mixed with new behavior; files serve clearly different purposes.

**Keep together (do NOT split):** code and its tests; a spec and its implementation plan.

- **One unit** -> Path A.
- **Several units** -> present the proposed split: each sub-commit with type/scope, one-line description, and files, in commit order (foundations first). Give the branch name and the option to commit everything as one. **MUST wait** for the user's choice. Accepted -> Path B. Declined -> Path A.

### Step 3 - Related recent commits (hint only)

If some of the last 10 commits clearly share a theme with this change and are not already inside a merge bubble, add one line to your final report:

> Recent commits `<hash>`, `<hash>` look related to this change. Run `$restructure-commit` if you want them grouped into one bubble.

Do not wait for an answer and do not regroup anything. If nothing looks related, say nothing.

---

### Path A - Single Commit

**A1.** Draft the message following the convention and body format above.

**A2.** Stage the relevant files by name (prefer specific files over `git add .`).

**A3.** Commit with HEREDOC syntax:

```bash
git commit -m "$(cat <<'EOF'
type(scope): description

Intent paragraph here - 2-3 sentences on why.

[--- Changes ---]

- file.md: description of what changed

[--- AI Review (<model name>) ---]

Honest assessment of the commit.
EOF
)"
```

**A4.** Run `git status` to confirm the commit succeeded.

---

### Path B - Several commits in one bubble (OneFlow Option 3)

**B1.** Note the current branch - the **parent branch**. Create the temporary branch:

```bash
git checkout -b <type>/<short-description>
```

**B2.** For each sub-commit in order: stage only its files, then commit with the same HEREDOC format as Path A.

**B3.** Switch back and count the branch's commits:

```bash
git checkout <parent-branch>
git rev-list --count <parent-branch>..<type>/<short-description>
```

- **2 or more commits** - merge with `--no-ff` to create the bubble:

```bash
git merge --no-ff <type>/<short-description> -m "$(cat <<'EOF'
<type>(<scope>): <summary of the whole change>

Intent paragraph - what these commits achieve together.

[--- Changes ---]

- Sub-commits included:
  - <hash-abbrev> <subject line>
  - <hash-abbrev> <subject line>

[--- AI Review (<model name>) ---]

Assessment of the change as a whole.
EOF
)"
```

- **1 commit** - fast-forward merge, no bubble:

```bash
git merge <type>/<short-description>
```

**B4.** Delete the temporary branch and verify:

```bash
git branch -d <type>/<short-description>
git status
git log --oneline --graph -10
```

Never run `git rebase -i` yourself - it needs an interactive editor. If the branch needs cleanup, suggest the command to the user.

---

## Post-Commit: Devlog Scrap Capture

After a successful commit, decide whether it is worth a devlog scrap. Skip this section if `.codex/skill-context/commit.md` sets `auto-devlog scrap: off`.

**Capture only if ALL are true:**

1. **Significant type:** `feat`, `fix`, `refactor`, or a `--no-ff` merge commit. Other types only when they record a real decision or pivot.
2. **A real insight exists.** Apply the capture bar in the "What's Worth Capturing" section of the devlog skill (`../devlog/SKILL.md`). Complete the sentence *"The interesting thing about this commit is ___"* with something specific. If you can't, or the answer is generic ("we added a feature"), skip. **MUST bias toward NO when uncertain.**
3. **Not already devlog content:** the commit does not touch `docs/devlog/.scraps/*` or `docs/devlog/*/`.

If all three hold, invoke `$devlog scrap --from-context` without asking. `--from-context` builds the scrap from the current conversation instead of re-mining history. If `$devlog` is not available, skip silently.
