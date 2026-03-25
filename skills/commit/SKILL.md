---
name: commit
description: "Create a git commit following Conventional Commits with a structured body format (intent paragraph, changes changelog, AI review). Uses OneFlow Option 3 (rebase + merge --no-ff) for decomposed multi-commit changesets."
---

# Commit Skill

## Purpose

Create git commits with consistent, well-structured commit messages following Conventional Commits and a structured body format. When a changeset decomposes into multiple commits, use a temporary branch merged with `--no-ff` (OneFlow Option 3) to preserve a clean, linear history with visible logical groupings.

## Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for the subject line:

```
type(scope): description
```

- **Common types**: `docs`, `fix`, `feat`, `refactor`, `build`, `test`, `chore`, `ci`, `style`, `perf`
- Use an em dash (—) in the description to separate the action from brief elaboration when needed
- Pick the most specific scope that fits. If changes span multiple areas, use the primary one.
- Derive scopes from the project's own directory structure and domain concepts.

### Examples

```
feat(auth): add JWT refresh token rotation — prevent stale session hijack
refactor(api): make route handlers async — replace blocking calls with awaited promises
docs(readme): update setup instructions — add Docker prerequisites
chore(config): make paths portable — relative refs from project root
build(deps): add zod v3.22 — runtime schema validation for API inputs
```

## Body

After the subject line, the body has three parts:

**1. Intent paragraph (2–3 sentences, no header)**
Why this change was made — motivation and context. Starts immediately after the blank line following the subject.

**2. `[--- Changes ---]`**
Per-file or per-category changelog. Group by file, include line numbers when relevant, describe what was added/removed/rewritten. This doesn't have to be exhaustive, but a reader should understand every substantive change without reading the diff.

**3. `[--- AI Review (<model name>) ---]`**
Your honest critical assessment of the commit. Use your current model name in the header (e.g., `[--- AI Review (Claude Opus 4.6) ---]`). Identify the strongest change, raise real concerns, flag what could be better. This section is evaluative, not promotional — say what you actually think.

## Overrides

- **Do NOT append a `Co-Authored-By` trailer.** The `[--- AI Review]` header already identifies the model. The trailer is redundant.

## Signing Failure Recovery

If a `git commit` (or `git merge --no-ff`, or `git commit --amend`) fails with `error: 1Password: failed to fill whole buffer` or similar 1Password SSH signing errors, **retry the same command** with `-c commit.gpgsign=false` to bypass signing. Do not ask the user — they may be away. Log a note after the commit so the user knows it is unsigned:

> **Note:** Commit `<hash>` is unsigned — 1Password SSH agent was unresponsive. Re-sign later with:
> `git rebase --exec "git commit --amend --no-edit" <parent-hash>`

This applies to all commit paths (A, B, C) and to `git merge --no-ff` commands.

## Branching Strategy (OneFlow Option 3)

[OneFlow](https://www.endoflineblog.com/oneflow-a-git-branching-model-and-workflow) is a git branching model built around a single long-lived branch (e.g., `main`). All work happens on short-lived feature branches that merge back into the main branch. It defines three options for finishing a feature branch — this skill uses **Option 3** (rebase + merge `--no-ff`): interactively rebase the feature branch to clean up its history, then merge with `--no-ff` to create a merge commit that groups the cleaned-up commits into a visible bubble. The result is a clean, almost-linear history where logical units are visually grouped, and any feature can be reverted with a single `git revert -m 1 <merge-commit>`.

A feature branch is used in two scenarios:

1. **Forward decomposition** — the current changeset splits into multiple sub-commits
2. **Retroactive grouping** — recent commits on the current branch (pushed or unpushed) share a logical theme with the new change and should be bundled together

**When either scenario applies:**

1. Note the current branch — this is the **parent branch** (the merge target)
2. Create a descriptive branch from the appropriate base point
3. Place all commits (new + retroactive if applicable) on that branch
4. *(Optional)* Clean up the commit sequence if needed (squash fixups, reorder)
5. Merge back into the **parent branch** with `--no-ff` to create a merge commit
6. Delete the temporary branch
7. Force push if the rewrite affected already-pushed commits

**Cascading merge rule:** Always merge back into the branch you branched off from — never skip levels. If you're on `feat/auth` and create `feat/auth-tests`, merge back into `feat/auth`, not `main`. This keeps the history cascading cleanly: each branch merges into its parent.

**When neither applies (single, standalone commit):** commit directly on the current branch — no branch needed.

### Branch Naming

Use a descriptive, kebab-case name derived from the overall theme of the changeset:

```
<type>/<short-description>
```

Examples: `feat/jwt-refresh-rotation`, `refactor/async-route-handlers`, `chore/portable-config-paths`

## Workflow

When this skill is invoked:

### Step 1 — Gather context

Run the following in parallel:
- `git status`
- `git diff HEAD` (shows all staged + unstaged changes combined against the last commit)
- `git log --oneline -10`
- `git log --oneline @{upstream}..HEAD` (identifies which commits have not been pushed yet; if no upstream is set, all commits on the branch are considered local — needed to determine whether a force push is required after retroactive grouping)

All recent commits — pushed or unpushed — are candidates for retroactive grouping. A force push will be used when needed.

### Step 2 — Retroactive grouping analysis

Examine the recent commits from step 1. Do any of them share a logical theme with the new change being committed?

**Heuristics for detecting a retroactive group:**
- Multiple recent commits touch the same scope/feature area as the new change
- A sequence of commits that incrementally build toward the same goal (e.g., three recent commits adding auth middleware, and the new change adds auth tests)
- Commits that would naturally be described under one feature branch name

**Do NOT retroactively group:**
- Commits that are already inside a merge bubble (already grouped)
- Unrelated commits that merely happen to be adjacent in time

**If a retroactive group is detected** → present the user with:
- Which existing commits would be included (hash + subject line)
- The new commit(s) that would join them
- The proposed branch name
- The option to skip grouping and just commit normally
- **Wait for the user's choice before doing anything else**

**If no retroactive group is detected** → proceed to step 3.

### Step 3 — Decomposition analysis

Analyze whether the current changeset (the uncommitted work) contains multiple logical units of work. A unit of work is a cohesive set of changes that serves a single purpose.

**Heuristics for detecting multi-unit changesets:**
- Changes span multiple unrelated scopes
- Refactoring mixed with new functionality
- Multiple files changed that serve clearly different purposes

**Keep together as one unit (do NOT split):**
- Implementation code + its tests — these are a single unit of work
- Spec/design document + its implementation plan — these are a single unit of work

**If the changeset looks like a single unit** → proceed to the **Single-Commit Path**.

**If the changeset looks decomposable** → present the user with:
- A proposed split: list each sub-commit with its type/scope, one-line description, and grouped files — in suggested commit order (foundations first, dependents later)
- The proposed branch name for the grouping
- The option to proceed as a single big commit instead ("Or commit everything together as one")
- **Wait for the user's choice before doing anything else**

### Decision tree

```
Step 2: retroactive group detected?
├─ YES → user accepts?
│  ├─ YES → Path C (retroactive grouping)
│  └─ NO  → proceed to Step 3
└─ NO  → proceed to Step 3

Step 3: changeset decomposable?
├─ YES → user accepts decomposition?
│  ├─ YES → Path B (decomposed multi-commit)
│  └─ NO  → Path A (single commit)
└─ NO  → Path A (single commit)
```

---

### Path A — Single Commit

Use when the changeset is a single logical unit and no retroactive grouping applies.

**A1.** Analyze all changes and draft a commit message following the convention above.

**A2.** Stage relevant files (prefer specific files over `git add .`).

**A3.** Create the commit using HEREDOC syntax:

```bash
git commit -m "$(cat <<'EOF'
type(scope): description

Intent paragraph here — 2-3 sentences on why.

[--- Changes ---]

- file.md: description of what changed

[--- AI Review (<model name>) ---]

Honest assessment of the commit.
EOF
)"
```

**A4.** Run `git status` after commit to verify success.

---

### Path B — Decomposed Multi-Commit (OneFlow Option 3)

Use when the user chooses to split the changeset into multiple sub-commits.

**B1.** Note the current branch name — this is the **parent branch** (e.g., `main`, `feat/auth`, or any branch you're currently on). Create and checkout the temporary branch:

```bash
git checkout -b <type>/<short-description>
```

**B2.** For each sub-commit, sequentially:
  - Stage only the files belonging to this sub-commit
  - Draft and create the commit using HEREDOC syntax (same body format as Path A)

**B3.** *(Optional)* Clean up the commit sequence before merging. Since the branch was just created from the parent's tip and commits were crafted individually in B2, this is almost always unnecessary. If cleanup is needed (e.g., squash a fixup), ask the user to run the interactive rebase themselves:

```
Suggest: git rebase -i <parent-branch>
```

> `git rebase -i` opens an editor and requires manual interaction — do not run it directly. Either skip this step (the default) or ask the user to run it.

**B4.** Switch back and merge with `--no-ff`:

```bash
git checkout <parent-branch>
git merge --no-ff <type>/<short-description> -m "$(cat <<'EOF'
<type>(<scope>): <merge description summarizing the overall change>

Intent paragraph — summarize the logical unit these commits form together.

[--- Changes ---]

- Sub-commits included:
  - <hash-abbrev> <subject line>
  - <hash-abbrev> <subject line>
  - ...

[--- AI Review (<model name>) ---]

Assessment of the feature as a whole.
EOF
)"
```

**B5.** Delete the temporary branch and verify:

```bash
git branch -d <type>/<short-description>
git status
git log --oneline --graph -10
```

---

### Path C — Retroactive Grouping (OneFlow Option 3)

Use when the user chooses to bundle existing commits with the new change into a feature branch.

**C1.** Identify the base commit — the parent of the oldest commit being grouped. Note the current branch name — this is the **parent branch** (the merge target). Record the hashes and messages of all commits being grouped (they will be cherry-picked later).

**C2.** Stash any uncommitted changes (the new work) so the working tree is clean:

```bash
git stash
```

**C3.** Create the temporary branch from the base commit:

```bash
git checkout -b <type>/<short-description> <base-commit-hash>
```

**C4.** Cherry-pick the existing commits onto the feature branch, preserving their original messages:

```bash
git cherry-pick <commit1> <commit2> <commit3>
```

**C5.** Restore the stashed changes and commit the new work using the standard body format. If the new changes contain multiple logical units, commit each sub-unit separately:

```bash
git stash pop
# stage and commit new change(s)
```

**C6.** *(Optional)* Clean up the commit sequence on the feature branch. Since commits were cherry-picked with their original messages and the new work was committed fresh, this is usually unnecessary. If cleanup is needed (e.g., squash a fixup), ask the user to run the interactive rebase themselves:

```
Suggest: git rebase -i <base-commit-hash>
```

> `git rebase -i` opens an editor and requires manual interaction — do not run it directly. Either skip this step (the default) or ask the user to run it.
>
> **Important:** The rebase target must be `<base-commit-hash>` (where the feature branch started), NOT `<parent-branch>`. The parent still has the original commits that were cherry-picked; rebasing onto it risks duplicate commits if patch-ids diverge.

**C7.** Switch back to the parent branch, reset it to the base commit, and merge with `--no-ff`:

```bash
git checkout <parent-branch>
git reset --hard <base-commit-hash>
git merge --no-ff <type>/<short-description> -m "$(cat <<'EOF'
<type>(<scope>): <merge description summarizing the logical unit>

Intent paragraph — why these commits belong together as one logical feature.

[--- Changes ---]

- Commits included:
  - <hash-abbrev> <subject line> (retroactive)
  - <hash-abbrev> <subject line> (retroactive)
  - <hash-abbrev> <subject line> (new)

[--- AI Review (<model name>) ---]

Assessment of the grouped feature as a whole.
EOF
)"
```

**C8.** If the branch has a remote upstream, force push to update the remote (retroactive grouping rewrites history):

```bash
git push --force-with-lease
```

Skip this step if the branch has no remote tracking (e.g., purely local work with no upstream set).

**C9.** Delete the temporary branch and verify:

```bash
git branch -d <type>/<short-description>
git status
git log --oneline --graph -10
```

---

The result across all paths is a clean history where `git log --oneline` reads linearly, but `git log --graph` shows merge bubbles grouping related commits together. Any grouped feature can be reverted with a single `git revert -m 1 <merge-commit>`.
