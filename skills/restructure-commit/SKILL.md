---
name: restructure-commit
description: "Use when the user invokes /restructure-commit or asks to group recent commits into one merge bubble, or to restructure a feature or phase branch into a book Table of Contents of chapters and sub-chapters without squashing atomic commits — rewrites local history with OneFlow Option 3, only after the user approves the plan."
---

# Restructure Commit Skill

Restructure existing local history using OneFlow Option 3 merge bubbles — without ever squashing small single-unit-of-work commits. Because this rewrites history, the skill always shows the full plan, waits for explicit approval, verifies zero file changes against a backup branch, and keeps the backup branch until you agree to delete it.

Two modes are supported:
- **Mode A — Tip Regrouping:** bundle one continuous run of loose unmerged commits at `HEAD` (plus optional uncommitted work) into one `--no-ff` bubble.
- **Mode B — Branch Table of Contents (`--branch` / `--toc`):** rebuild a long-lived feature or phase branch (`<base>..<branch>`) into a uniform **3-level Book Table of Contents** (Chapters -> Semantic Sub-Chapters -> every original atomic commit preserved 1-to-1 verbatim).

For ordinary new commits, use `/commit`. This skill is only for reorganizing commits that already exist.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`.

## Reference Files

Resolve these paths under this skill's folder, never under the user's project working directory:

| File | Contents | When to use |
|---|---|---|
| `references/book-toc-examples.md` | 4-layout case study (Anti-Patterns vs. Target 3-level Book-TOC), sample `plan.json`, and `{{SUB_COMMITS}}` merge template | Read before designing any Mode B plan |
| `helpers/dag_rewrap.py` | Deterministic helper (`inspect`, `validate`, `build`) for trivial-merge auditing, lossless `git commit-tree` bottom-up DAG rebuilds, and 6-point self-verification | Run during Mode B (prefer `python3`, fall back to `python` on Windows) |

## Rules Shared with /commit

Read `skills/commit/SKILL.md`. Apply these sections from it exactly:

- **Preflight: Never `git push` Without Express Authorization**
- **Convention**, **Plain-Language Standard**, **Body**, **Durable-reader check** — every new commit and every Chapter / Sub-Chapter merge commit uses this message format.
- **Signing Failure Recovery** — also applies to `git cherry-pick`, `git merge --no-ff`, `git rebase --rebase-merges`, and `git commit-tree -S` here.
- **Branching Strategy (OneFlow Option 3)** — 1 single unit of work per atomic commit, multi-level nested bubbles (3+ levels) are desirable, minimum bubble size is 2 entries at every level (fast-forward a group of 1), cascading merge rule, and rebasing onto the parent tip with `git rebase --rebase-merges <parent-branch>` before `--no-ff` whenever the parent moved ahead (never plain `git rebase`, which flattens inner bubbles).
- **Post-Commit: Devlog Scrap Capture** — run it at most once after the entire restructure finishes, for the restructure as a whole.

## Out of Scope

This skill MUST NOT:
- Run `git push` in any form without an express, current-turn instruction for that specific push. Plan approval is NOT push approval.
- Rewrite anything before the user approves the plan.
- **Squash, combine, or drop existing single-unit-of-work commits (Mistake 1).** Never use `git read-tree` squashing, `git merge --squash`, or soft-reset collapsing to fold multiple atomic commits into one bigger commit. Every original atomic commit must stay 1-to-1 verbatim. If the user explicitly asks to squash or edit commits interactively, warn that it discards atomic history and suggest `git rebase -i` instead.
- **Dump raw dev-time history straight under a Chapter merge without semantic Sub-Chapters (Mistake 2).** In Mode B, do not wrap flat multi-dozen-commit walls, noisy review/fix micro-merges, or stray loose commits directly under a Chapter bubble when the chapter breaks cleanly into 2–4 semantic Sub-Chapters.
- **In Mode A (Tip Regrouping):** regroup commits that are already inside a merge bubble, or regroup merge commits.
- **In Mode B (Branch Table of Contents):** silently flatten any non-trivial merge (`merge^{tree} != p2^{tree}`, earlier branch fork, or mid-branch sync merge from `main`), or rewrite anything at or before `<base>`. Mode B may replace trivial dev-time merges (`merge^{tree} == p2^{tree}` with a clean fork from `p1`) with clean Chapter and Sub-Chapter `--no-ff` bubbles **only** inside `<base>..<branch>` and **only** after explicit plan approval.
- Run `git rebase -i` (it needs an interactive editor). Suggest it to the user instead.
- Delete the backup branch without the user's agreement.

## Modes and Trigger Criteria

| Trigger | Mode | Behavior |
|---|---|---|
| `/restructure-commit <range>` or `/restructure-commit <hash1> <hash2> ...` (no merges inside) | **Mode A** | Bundle that continuous run at `HEAD` (+ optional uncommitted work) into 1 merge bubble |
| `/restructure-commit --branch [<base>]` or `/restructure-commit --toc [<base>]` | **Mode B** | Lossless 3-level Book-TOC rebuild of `<base>..<branch>` |
| Natural-language request to organize a whole branch into chapters / sub-chapters / a table of contents | **Mode B** | Lossless 3-level Book-TOC rebuild of `<base>..<branch>` |
| Bare `/restructure-commit` when recent commits at `HEAD` are a clean unmerged run | **Mode A** | Propose grouping the related unmerged run at `HEAD` |
| Bare `/restructure-commit` on a non-default branch whose history since `<base>` already has merge commits or bubbles | **Ask first** | Never switch silently — offer Mode A (only loose commits after the latest merge, if any), Mode B (full `<base>..<branch>` Book-TOC), or Cancel |

**Mode B preconditions:**
- **Default-branch guard:** Mode B targets feature or phase branches (`<base>..<branch>`). If the current branch is `main` or `master` (or already merged into `<base>`), stop and warn before proposing a rewrite; continue only if the user explicitly names `<base>` and confirms rewriting that branch.
- **Clean working tree:** `git status --porcelain` must be empty before Mode B begins. If uncommitted changes exist, stop and offer to `/commit` them first (so they join the backup branch) or stash them outside the rewrite.
- If `<base>` is omitted, infer it from `main` or `master` with `git merge-base` and show `<base>` clearly in the plan.

### Anti-Patterns vs. Target (Mode B)

| Layout | Shape | Verdict |
|---|---|---|
| **Mistake 1: Over-Squashing** | Chapters -> squashed multi-change commits (`0` atomic commits left) | **Forbidden** — loses single-unit commits, `git blame`, and bisectability |
| **Mistake 2: Raw Dev-Time Wrapping** | Chapters -> flat 29-commit walls, noisy micro-merges, stray loose commits | **Forbidden** — expanding a chapter still shows dev-time plumbing |
| **Target: Lossless 3-Level Book-TOC** | Chapters (`--no-ff`) -> 2–4 Semantic Sub-Chapters (`--no-ff`, or 1 commit with no redundant sub-bubble) -> 100% of original atomic commits verbatim | **Required** — reads like a book at every zoom level (`main` adds Level 0 when the branch merges via `--no-ff`) |

Read `references/book-toc-examples.md` for the full concrete 4-layout case study before designing a Mode B plan.

---

## Mode A — Tip Regrouping (Single Bubble at HEAD)

### Step A1 — Gather context

Run in parallel:
- `git status`
- `git diff HEAD`
- `git log --oneline --graph -20`
- `git log --oneline @{upstream}..HEAD` (commits not yet pushed; if there is no upstream, all commits are local)

### Step A2 — Choose the group

- **Arguments given** (`/restructure-commit HEAD~4..HEAD` or a list of hashes): use those commits.
- **No arguments:** find recent commits that share one theme — same scope or feature, or steps toward one goal. Ignore commits that are merely next to each other in time.

The group must be a **continuous run of commits ending at `HEAD`**, with no merge commits inside it. If an unrelated commit sits between grouped commits, offer two choices: include it in the group, or regroup only the commits after it. Never leave a commit out of the replayed history.

The **base commit** is the parent of the oldest grouped commit. The **parent branch** is the current branch.

### Step A3 — Present the plan and wait

Show:
- the commits to group (hash and subject), oldest first
- whether uncommitted work will join them as new atomic commit(s)
- the temporary branch name (`<type>/<short-description>`)
- whether any grouped commit is already pushed — if so, say that a force push will be needed later and that it needs its own approval
- the option to cancel

**MUST wait** for the user's answer. Do nothing else until they approve.

### Step A4 — Make a backup

```bash
git branch restructure-backup-<YYYYMMDD-HHMMSS> HEAD
```

This keeps the original history reachable. If anything goes wrong, `git reset --hard restructure-backup-<...>` on the parent branch restores it.

### Step A5 — Build the grouped branch

```bash
git stash push --include-untracked     # only if there is uncommitted work
git checkout -b <type>/<short-description> <base-commit>
git cherry-pick <oldest-hash>^..<newest-hash>
```

If a cherry-pick conflicts:
1. Report the conflicting files.
2. Resolve only trivial conflicts (whitespace, obvious merges) yourself. Ask before resolving any conflict that needs judgment.
3. After resolving: `git cherry-pick --continue`.
4. If the user wants to stop: `git cherry-pick --abort`, return to the parent branch, and drop the temporary branch. The parent branch was never changed, so nothing is lost.

If you stashed work, restore it and commit it as small atomic commit(s) with the `/commit` message format (split into several commits if it holds several logical units):

```bash
git stash pop
```

If `git stash pop` conflicts, the stash is kept. Report the files, resolve, then `git stash drop`. If you cannot resolve it, stop and ask the user.

### Step A6 — Check, then rewrite the parent branch

Show the user the new branch's commits:

```bash
git log --oneline <base-commit>..<type>/<short-description>
```

Then move the parent branch and merge:

```bash
git checkout <parent-branch>
git reset --hard <base-commit>
git rev-list --count <base-commit>..<type>/<short-description>
```

If `<parent-branch>` somehow moved ahead of the temporary branch base, rebase the temporary branch onto `<parent-branch>` first using `git rebase --rebase-merges <parent-branch>` (OneFlow Option 3, without squashing). Merge exactly as in `/commit` Path B, step 3: `--no-ff` with the merge-commit template for 2 or more commits, fast-forward for 1. In the merge commit's `[--- Changes ---]` list, mark each sub-commit `(regrouped)` or `(new)`.

### Step A7 — Verify nothing was lost

```bash
git diff restructure-backup-<...> HEAD --stat
```

The only differences should be the new work that was uncommitted at the start. If there was no new work, the diff must be empty. If anything else differs, stop and report it — the backup branch still holds the original history.

Delete `<type>/<short-description>` (`git branch -d <type>/<short-description>`), then continue to **Shared Final Steps**.

---

## Mode B — Branch Table of Contents (Lossless 3-Level Nested Bubbles)

### Step B1 — Inspect branch and check merge triviality

Check the Mode B preconditions (clean working tree, non-default branch) and read `references/book-toc-examples.md`.

Resolve `helpers/dag_rewrap.py` to an absolute path under this skill's directory, and run in parallel:
- `python3 <helper-path> inspect <base> HEAD` (fall back to `python` on Windows)
- `git log --oneline @{upstream}..HEAD` (pushed status; if there is no upstream, all commits are local)

Review the `inspect` JSON carefully:
- Confirm `non_trivial_merges` is empty (`merge^{tree} == p2^{tree}` and clean fork from `p1` for every dev-time merge).
- If any non-trivial merge is reported: **stop and flag it to the user before designing a plan.** For a self-contained conflict merge (`preservable: true`), ask whether to preserve that merge subgraph intact via `preserve_merges`; for a mid-branch sync merge from `main` or earlier cross-branch fork (`preservable: false`), suggest starting `<base>` after the sync merge or fixing the branch topology first. Never silently flatten a non-trivial merge.

### Step B2 — Design Chapters and Sub-Chapters, then validate

Partition the ordered `atomic_commits` stream from `inspect` into:
- **Level 1 — Chapters:** major milestones or coherent themes (typically 3–10 chapters).
- **Level 2 — Semantic Sub-Chapters:** 2–4 clean, focused sub-chapters inside each Chapter, using inclusive `"start"` / `"end"` commit ranges (or explicit `"commits"` lists) that cover 100% of `atomic_commits` in exact chronological order.
- **Level 3 — Atomic Commits:** every original single-unit commit stays untouched and unsquashed.

Follow OneFlow Option 3's **minimum bubble size = 2 at every level**:
- A Sub-Chapter with **2 or more** atomic commits becomes a `--no-ff` Sub-Chapter merge bubble (with a `/commit` Path B merge message containing `{{SUB_COMMITS}}`).
- A Sub-Chapter with **1** atomic commit goes directly inside the Chapter with **no** redundant 1-commit sub-bubble.
- A Chapter with **2 or more** Sub-Chapters becomes a `--no-ff` Chapter merge bubble (with a `/commit` Path B merge message containing `{{SUB_COMMITS}}`).
- A Chapter with **1** Sub-Chapter is not double-wrapped.

Write `plan.json` to an OS temp directory (never inside the repository working tree) and run:

```bash
python3 <helper-path> validate <temp-dir>/plan.json
```

Confirm `"valid": true` (`0` missing atomics, `0` duplicate atomics, `0` cross-chapter or cross-subchapter parent edges, `0` unhandled non-trivial merges) before presenting the plan.

### Step B3 — Present the 3-level plan and wait

**Plan-presentation guardrail:** before asking for approval, ALWAYS show:
1. **Summary counts:** `<base>..<branch>`, original commit count -> rebuilt commit count (`X` Chapters + `Y` Sub-Chapter merges + `Z` atomic commits preserved **1-to-1, 0 squashed**), non-trivial merge audit, current unsigned count, and pushed status.
2. **Level 1 (Chapters) + Level 2 (Sub-Chapters with exact atomic commit counts):** every Chapter title and every Sub-Chapter under it with its atomic count (noting any 1-commit sub-chapters that skip a sub-bubble).
3. **Level 3 sample:** a concrete slice of preserved original atomic commits inside at least one Chapter/Sub-Chapter so the user can see immediately that small single-unit commits remain intact.
4. **Signing choice** (when `commit.gpgsign=true`, noting that changing parent hashes invalidates prior signatures on re-parented commits):
   - **Option S1 — Re-sign all rebuilt commits (`--sign all`, Recommended):** signs every rebuilt atomic commit and every new Sub-Chapter/Chapter merge via `git commit-tree -S`, with per-commit Signing Failure Recovery (`--no-gpg-sign` fallback only if 1Password fails, logging every unsigned hash). Warn about elapsed signing time if hundreds of commits will be signed.
   - **Option S2 — Sign new outer merges only (`--sign outer`):** fast for very large branches; inner re-parented atomic commits stay unsigned.
5. **Force-push impact** (if any commit in `<base>..<branch>` was pushed, state that `git push --force-with-lease` will need its own approval later) and the option to **Cancel**.

**MUST wait** for the user's approval of both the 3-level layout and the signing choice. Do nothing until they approve.

### Step B4 — Create backup and build on an isolated temp branch

Create the backup branch first (leaving `<target-branch>` untouched throughout the build):

```bash
git branch restructure-backup-<YYYYMMDD-HHMMSS> HEAD
python3 <helper-path> build <temp-dir>/plan.json --target-tmp restructure-toc-tmp-<YYYYMMDD-HHMMSS> --sign <all|outer|none>
```

`helpers/dag_rewrap.py build` constructs the entire 3-level DAG bottom-up with `git commit-tree` purely in Git's object store — preserving every atomic commit's exact tree, raw message, author/committer name, email, and timestamps, substituting the **actual new abbreviated hashes** into `{{SUB_COMMITS}}`, and running all 6 verification checks before creating `restructure-toc-tmp-<YYYYMMDD-HHMMSS>`.

### Step B5 — Verify 6 invariants BEFORE touching `<target-branch>`

Confirm all 6 checks on `restructure-toc-tmp-<YYYYMMDD-HHMMSS>` (from the `build` JSON report and live git checks):
1. **Byte-identical final tree:** `git diff restructure-backup-<...> restructure-toc-tmp-<...>` is completely empty (`orig_tree == new_tree`).
2. **Endpoint tree identity:** every Chapter and Sub-Chapter merge commit tree matches its original boundary atomic commit's tree.
3. **Zero squashing & exact counts:** `rebuilt_atomic == original_atomic` (`0` missing, `0` duplicate) and `rebuilt_total == original_atomic + sub_chapter_merges + chapter_merges`.
4. **Atomic diff identity:** every atomic commit's tree and parent tree match its original tree and parent tree.
5. **Clean 3-level TOC:** run `git log --first-parent --reverse --oneline <base>..restructure-toc-tmp-<...>` (Level 1 Chapters) and spot-check a Chapter expansion `git log --first-parent --reverse <prev-ch>..<ch>^2` (Level 2 Sub-Chapters) to confirm zero 1-commit wrapper bubbles.
6. **Signature audit:** report exact signed vs. unsigned counts (and any `unsigned_fallback_commits` hashes with `/commit`'s `--rebase-merges` re-sign recipe).

If ANY check fails: **STOP immediately**, delete `restructure-toc-tmp-<...>` (`git branch -D ...`) and remove `<temp-dir>/plan.json`, and report the failure. `<target-branch>` was never modified.

### Step B6 — Atomic swap of `<target-branch>`

Only after all 6 checks pass:

```bash
git checkout <target-branch>
git reset --hard restructure-toc-tmp-<YYYYMMDD-HHMMSS>
git branch -d restructure-toc-tmp-<YYYYMMDD-HHMMSS>
git diff restructure-backup-<YYYYMMDD-HHMMSS> HEAD --stat
```

Delete `<temp-dir>/plan.json`. Confirm `git diff restructure-backup-<...> HEAD --stat` is completely empty and `git status` is clean.

*(Later, when merging `<target-branch>` into `main`, follow OneFlow Option 3: if `main` moved ahead, rebase `<target-branch>` onto `main` using `git rebase --rebase-merges main` so all 3 nested levels stay intact, then merge into `main` with `git merge --no-ff`.)*

---

## Shared Final Steps (Mode A and Mode B)

### Push decision

If any rewritten commit was already pushed, the remote is now out of sync. Explain that history on the branch was rewritten, show the exact command (`git push --force-with-lease`), and ask whether to push to origin.

Wait for an express, push-specific answer in the current turn. If the user declines or does not answer, leave the remote as it is. Skip this step if no rewritten commit was pushed.

### Clean up and report

```bash
git status
git log --oneline --graph -10   # Mode A, or git log --first-parent --reverse --oneline <base>..HEAD for Mode B
```

Report:
- the new merge commit (Mode A) or the full Level-1 Book TOC with Chapter / Sub-Chapter / Atomic / Signature counts (Mode B)
- the backup branch name (`restructure-backup-<YYYYMMDD-HHMMSS>`)
- the push status

Ask whether to delete the backup branch (`git branch -D restructure-backup-<...>`). Keep it if the user does not answer. Run `/commit`'s Post-Commit Devlog Scrap check at most once for the restructure as a whole.
