---
name: restructure-commit
description: "Use when the user invokes /restructure-commit or asks to group, bundle, or restructure recent commits into one merge bubble — rewrites local history with OneFlow Option 3, only after the user approves the plan."
---

# Restructure Commit Skill

Restructure recent history. Take related recent commits — plus any new uncommitted work — and put them inside one OneFlow Option 3 merge bubble (a `--no-ff` merge commit that groups them). This rewrites history, so the skill always shows the plan, waits for approval, and keeps a backup branch.

For ordinary new commits, use `/commit`. This skill is only for changing commits that already exist.

## Write for Humans

Everything a person reads from this skill — commit messages and replies — MUST use plain language that a non-native English reader can follow. Read `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory) and follow it.

## Rules Shared with /commit

Read `skills/commit/SKILL.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory). Apply these sections from it exactly:

- **Preflight: Never `git push` Without Express Authorization**
- **Convention**, **Plain-Language Standard**, **Body**, **Durable-reader check** — every new commit and the merge commit use this message format.
- **Signing Failure Recovery** — also applies to `git cherry-pick` and `git merge --no-ff` here.
- **Branching Strategy (OneFlow Option 3)** — minimum bubble size is 2 commits (fast-forward a group of 1), cascading merge rule, branch naming.
- **Post-Commit: Devlog Scrap Capture** — run it once after the merge, for the group as a whole.

## Out of Scope

This skill MUST NOT:
- Run `git push` in any form without an express, current-turn instruction for that specific push. Plan approval is NOT push approval.
- Rewrite anything before the user approves the plan.
- Regroup commits that are already inside a merge bubble, or regroup merge commits.
- Run `git rebase -i` (it needs an interactive editor). Suggest it to the user instead.
- Delete the backup branch without the user's agreement.

## Workflow

### Step 1 — Gather context

Run in parallel:
- `git status`
- `git diff HEAD`
- `git log --oneline --graph -20`
- `git log --oneline @{upstream}..HEAD` (commits not yet pushed; if there is no upstream, all commits are local)

### Step 2 — Choose the group

- **Arguments given** (`/restructure-commit HEAD~4..HEAD` or a list of hashes): use those commits.
- **No arguments:** find recent commits that share one theme — same scope or feature, or steps toward one goal. Ignore commits that are merely next to each other in time.

The group must be a **continuous run of commits ending at `HEAD`**, with no merge commits inside it. If an unrelated commit sits between grouped commits, offer two choices: include it in the group, or regroup only the commits after it. Never leave a commit out of the replayed history.

The **base commit** is the parent of the oldest grouped commit. The **parent branch** is the current branch.

### Step 3 — Present the plan and wait

Show:
- the commits to group (hash and subject), oldest first
- whether uncommitted work will join them as new commit(s)
- the temporary branch name (`<type>/<short-description>`)
- whether any grouped commit is already pushed — if so, say that a force push will be needed later and that it needs its own approval
- the option to cancel

**MUST wait** for the user's answer. Do nothing else until they approve.

### Step 4 — Make a backup

```bash
git branch restructure-backup-<YYYYMMDD-HHMMSS> HEAD
```

This keeps the original history reachable. If anything goes wrong, `git reset --hard restructure-backup-<...>` on the parent branch restores it.

### Step 5 — Build the grouped branch

```bash
git stash push --include-untracked     # only if there is uncommitted work
git checkout -b <type>/<short-description> <base-commit>
git cherry-pick <oldest-hash>^..<newest-hash>
```

If a cherry-pick conflicts:
1. Report the conflicting files.
2. Resolve only trivial conflicts (whitespace, obvious merges) yourself.
3. Otherwise ask: "Cherry-pick of `<hash>` conflicted in `<file>`. Should I resolve it, or will you?"
4. After resolving: `git cherry-pick --continue`.
5. If the user wants to stop: `git cherry-pick --abort`, return to the parent branch, and drop the temporary branch. The parent branch was never changed, so nothing is lost.

If you stashed work, restore it and commit it with the `/commit` message format (split into several commits if it holds several logical units):

```bash
git stash pop
```

If `git stash pop` conflicts, the stash is kept. Report the files, resolve, then `git stash drop`. If you cannot resolve it, stop and ask the user.

### Step 6 — Check, then rewrite the parent branch

Show the user the new branch's commits:

```bash
git log --oneline <base-commit>..<type>/<short-description>
```

Then move the parent branch:

```bash
git checkout <parent-branch>
git reset --hard <base-commit>
git rev-list --count <base-commit>..<type>/<short-description>
```

Merge exactly as in `/commit` Path B, step B3: `--no-ff` with the merge-commit template for 2 or more commits, fast-forward for 1. In the merge commit's `[--- Changes ---]` list, mark each sub-commit `(regrouped)` or `(new)`.

### Step 7 — Verify nothing was lost

```bash
git diff restructure-backup-<...> HEAD --stat
```

The only differences should be the new work that was uncommitted at the start. If there was no new work, the diff must be empty. If anything else differs, stop and report it — the backup branch still holds the original history.

### Step 8 — Push decision

If any grouped commit was already pushed, the remote is now out of sync. Show the exact command and ask:

> History on `<parent-branch>` was rewritten. To update the remote, a force push is needed:
>
> ```bash
> git push --force-with-lease
> ```
>
> Push to origin? (yes/no)

Wait for an express, push-specific answer in the current turn. If the user declines or does not answer, leave the remote as it is. Skip this step if no grouped commit was pushed.

### Step 9 — Clean up and report

```bash
git branch -d <type>/<short-description>
git status
git log --oneline --graph -10
```

Report the new merge commit, the backup branch name, and the push status. Ask whether to delete the backup branch (`git branch -D restructure-backup-<...>`). Keep it if the user does not answer.
