---
name: commit
description: "Use when the user invokes $commit or any git commit is about to be created \u2014 applies Conventional Commits, the structured body format, and OneFlow Option 3 merge bubbles for multi-commit changes."
---

# Commit Skill

Create git commits with clear, structured messages (Conventional Commits plus a fixed body format). Group a change that needs several commits into one merge bubble (OneFlow Option 3).

This skill only adds new commits. It never rewrites existing history: no hard resets, no cherry-picking, no rebasing, and no `--amend` on commits already pushed. To group commits that already exist, use `$restructure-commit`.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`.

## Out of Scope

This skill MUST NOT:
- Commit secrets, credentials, API keys, or `.env` files. Check the staged files first. If a file looks suspicious, ask.
- Bundle unrelated changes into one commit just to be quick. Propose a split instead.
- Add a `Co-Authored-By` trailer. The `[--- AI Review ---]` header already names the model.

## Preflight: Never `git push` Without Express Authorization

**Absolute rule:** Do NOT run `git push` in any form - normal, `--force`, `--force-with-lease`, tag push, branch push - unless the user's **current-turn** message contains a direct, unambiguous instruction to push **this specific push**. This rule overrides every other instruction in this skill.

**Plan approval != push approval.** If a plan or prior turn listed a push as a step and the user said "proceed" / "go ahead" / "do it" / "yes" to that plan, that is **NOT** push authorization. Those words authorize non-push work only. At the push step: STOP, present the exact `git push ...` command, ask `"push to origin? yes/no"`, and wait for a push-specific answer.

**Express orders that DO authorize a push:** "push it", "push now", "push to origin", "send it", "publish", or equivalent current-turn directive naming the push action.

**Auto mode does NOT relax this rule. Solo-developer branches do NOT relax this rule. A rewrite that "needs" a force push does NOT relax this rule** - the need for the push is a reason to ask, not a reason to proceed.

If unsure whether something counts as an express order, assume it does **NOT**. Ask.

**Incident of record:** 2026-04-20 - a force-push landed during auto-mode execution before the user could intervene. The user's stated expectation: *"I DON'T WANT THIS TO EVER HAPPENED AGAIN."* This rule exists to prevent a recurrence.

## User Preferences

Read `../shared/skill-context.md` and the preference files it names, if present. `auto-devlog scrap: off` in `.codex/skill-context/commit.md` skips the Post-Commit devlog scrap step (default on).

## Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for the subject line: `type(scope): description`.

- Make the description name the concrete outcome in plain language. Do not lead with an internal process label, evidence identifier, metaphor, or ceremony.
- Use an em dash (-) only when a short elaboration makes the outcome clearer.
- Pick the most specific scope that fits. If changes span several areas, use the primary one.

```
feat(auth): add JWT refresh token rotation - prevent stale session hijack
docs(readme): update setup instructions - add Docker prerequisites
```

## Plain-Language Standard

Write every commit message for a durable reader: either a teammate who
understands the project in general but does not know today's task, internal
shorthand, or recent session history, or the author returning years later.

- Prefer ordinary words, short sentences, and active voice.
- State the concrete outcome before supporting evidence or implementation detail.
- When an acronym, gate name, code name, identifier, statistic, or specialized term is necessary, explain it on first use and say why it matters.
- Include hashes, counts, paths, and symbols only when they provide useful evidence or traceability. Do not make the reader decode raw inventory.
- Metaphors, slogans, ceremonial language, and dramatic descriptions must not replace concrete actions and outcomes.

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

Every commit has a body in three parts, after the subject line and a blank line:

**1. Intent paragraph (short, no header)**
Explain the problem or need, the outcome, and why it matters. Give enough context for a reader who was not part of the current task.

**2. `[--- Changes ---]`**
Summarize observable outcomes and important technical decisions. Organize by file or category when that helps, but do not inventory every edited line or repeat the diff.

**3. `[--- AI Review (<model name>) ---]`**
Give an honest assessment in direct, ordinary language, with your real model name in the header. State meaningful strengths, risks, trade-offs, and follow-up work without promotional, theatrical, or self-congratulatory prose. "Looks good!" is not a review.

### Durable-reader check

Before creating the commit, reread the complete message and ask:

> Could a teammate unfamiliar with this task, or the author returning years later, understand why this commit exists, what changed, and what still needs attention without the issue tracker or session history?

If the answer is no, rewrite the message before creating the commit.

## Signing Failure Recovery

If a commit or merge fails with `error: 1Password: failed to fill whole buffer` or a similar 1Password SSH signing error, retry the same command with `-c commit.gpgsign=false`. Do not ask first; the user may be away. Afterwards, tell the user which commit is unsigned and that they can re-sign it later with `git rebase --rebase-merges --exec "git commit --amend --no-edit" <parent-hash>`. Keep `--rebase-merges`: a plain rebase flattens merge bubbles.

## Branching Strategy (OneFlow Option 3)

[OneFlow](https://www.endoflineblog.com/oneflow-a-git-branching-model-and-workflow) keeps one long-lived branch. Work happens on short-lived branches that merge back. **Option 3** merges with `--no-ff`, which wraps the branch's commits in a merge commit - a visible "bubble". The history still reads almost linearly, and the whole group can be reverted as one unit.

Rules:
- **Use a branch only when the change splits into 2 or more commits.** A single commit goes directly on the current branch.
- **Minimum bubble size is 2 commits.** If the branch ends up with 1 commit, fast-forward merge instead of `--no-ff`. A bubble around one commit adds noise.
- **Cascading merge rule:** always merge back into the branch you started from (the **parent branch**), even when that is itself a feature branch.
- **Branch name:** `<type>/<short-description>` in kebab-case, from the overall theme, for example `feat/jwt-refresh-rotation`.

## Workflow

### Step 1 - Gather context

Read the full uncommitted diff (staged and unstaged) and the recent log before drafting.

### Step 2 - Decomposition analysis

Decide whether the uncommitted work holds more than one logical unit. A unit is a set of changes that serves one purpose.

**Keep together (do not split):** code and its tests; a spec and its implementation plan.

- **One unit** -> Path A.
- **Several units** -> present the proposed split: each sub-commit with type/scope, one-line description, and files, in commit order (foundations first). Give the branch name and the option to commit everything as one. Wait for the user's choice. Accepted -> Path B. Declined -> Path A.

### Step 3 - Related recent commits (hint only)

If some of the last 10 commits clearly share a theme with this change and are not already inside a merge bubble, add one line to your final report naming their hashes and suggesting `$restructure-commit` to group them into one bubble.

Do not wait for an answer and do not regroup anything. If nothing looks related, say nothing.

### Path A - Single Commit

Draft the message using the convention and body format above. Stage the relevant files by name rather than `git add .`, then commit.

### Path B - Several commits in one bubble (OneFlow Option 3)

1. Note the parent branch, then create the temporary `<type>/<short-description>` branch.
2. For each sub-commit in order, stage only its files and commit with the same message format as Path A.
3. Return to the parent branch and count the branch's commits.
   - **2 or more commits:** `git merge --no-ff <type>/<short-description>` with this merge message:

     ```text
     <type>(<scope>): <summary of the whole change>

     Intent paragraph - what these commits achieve together.

     [--- Changes ---]

     - Sub-commits included:
       - <hash-abbrev> <subject line>
       - <hash-abbrev> <subject line>

     [--- AI Review (<model name>) ---]

     Assessment of the change as a whole.
     ```

   - **1 commit:** fast-forward merge, with no bubble.
4. Delete the temporary branch and show `git log --oneline --graph` so the user sees the result.

## Post-Commit: Devlog Scrap Capture

After a successful commit, decide whether it is worth a devlog scrap, unless `auto-devlog scrap: off` is set.

**Capture only if all three are true:**

1. **Significant type:** `feat`, `fix`, `refactor`, or a `--no-ff` merge commit. Other types only when they record a real decision or pivot.
2. **A real insight exists.** Apply the capture bar in the "What's Worth Capturing" section of the devlog skill (`../devlog/SKILL.md`). You can finish *"The interesting thing about this commit is ___"* with something specific, not generic. Lean toward no when unsure.
3. **Not already devlog content:** the commit does not touch `docs/devlog/.scraps/*` or `docs/devlog/*/`.

If all three hold, invoke `$devlog scrap --from-context` without asking. If `$devlog` is not available, skip silently.
