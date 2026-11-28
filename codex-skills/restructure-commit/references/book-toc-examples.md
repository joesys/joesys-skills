# Book Table of Contents Examples: Anti-Patterns vs. Target

This concrete 4-layout case study comes from restructuring a real 417-commit feature branch (`main..phase/1-core-engine`). All four layouts produce the **exact same final file tree** (zero bytes of code difference), yet only Layout 3 reads like a book while preserving every atomic single-unit commit.

Read this guide before designing a Mode B (`$restructure-commit --toc`) plan so you avoid both Mistake 1 and Mistake 2.

---

## 0. Original Dev-Time Layout — 417 commits (72 first-parent entries)

Normal day-to-day work produces a flat mix of large bubbles, small review-fix bubbles, and loose single commits (`361` atomic commits + `56` trivial dev-time merges):

```text
git log --first-parent --reverse main..a184ad1   # 72 mixed entries — hard to scan
  8867047 (merge, 29 commits) build(workspace): add the Day-1 scaffold and local check suite
  deee3ef (merge)             feat(core): lock the leaf-layer foundation...
  7533a08 (merge)             feat(core): add the layered pack loader...
  f304d0b (merge)             feat(core): add the closed-catalog expression parser...
  1c80a1e (loose 1-commit)    docs(agents): rebase parallel worktree branches...
  d1d1a2b (merge)             fix(core): apply the first independent review...
  ... (60 more mixed merges and loose commits) ...
  55a7f86 (loose 1-commit)    docs: point stale references at rules.rs...
  a8acb8e (loose 1-commit)    docs(agents): clarify how budget caps weigh clarity...
  edec171 (loose 1-commit)    docs(agents): record frontier-model preference...
  c876051 (merge, 3 commits)  fix(core): resolve P1 privacy and Feint findings...
  832af68 (loose 1-commit)    style(core,ci): format review-fix files...
  a184ad1 (loose 1-commit)    docs(adr): mark ADRs 0012 and 0013 accepted
```

---

## Mistake 1 (FORBIDDEN): Over-Squashing into Sub-Chapter Commits — 30 commits

Looks tidy at Level 1 (`8` Chapters) and Level 2 (`22` Sub-Chapters), **but squashes all `361` single-unit commits into `22` giant multi-change commits** (e.g., via `git read-tree` squashing or `--squash`):

```text
# Chapter 1 (BAD — 29 atomic commits squashed into 2 giant commits!)
* 06b12c9 build(workspace): Milestone 1 — Day-1 Cargo workspace, budgets, and local CI
|\
| * 1c8e289 ci: add local hygiene, budget, telemetry, and schema-drift scripts   <-- 24 commits squashed!
| * 8f60149 build(workspace): add Cargo workspace, crate skeletons, and budgets  <-- 5 commits squashed!
|/

# Chapter 8 (BAD — 8 atomic commits squashed into 3!)
* 26538fd fix(core,docs): Post-Gate-1 cleanup 3 — governance, review P1 fixes, ADRs
|\
| * 8681e8f docs(adr): mark ADRs 0012 and 0013 accepted
| * 85cde84 fix(core,ci): close frontier-review P1 leaks, Feint bug, nits        <-- 4 commits squashed!
| * 7e61a4c docs(agents): record budget-cap rule, review lesson, rules.rs        <-- 3 commits squashed!
|/
```

**Why this fails:** Every atomic commit must stay **1 single unit of work** so `git blame`, `git bisect`, and step-by-step history stay useful. Never squash atomic commits to make a Table of Contents.

---

## Mistake 2 (FORBIDDEN): Wrapping Raw Dev-Time History Inside Chapters — 424 commits

Preserves all `361` atomic commits verbatim, **but naively wraps the raw dev-time graph inside 8 outer chapter merges** instead of reorganizing each chapter's insides into clean semantic Sub-Chapters:

```text
# Chapter 1 (BAD — 29 flat commits with ZERO sub-chapters!)
* (Chapter 1 merge) build(workspace): Milestone 1 — Day-1 Cargo workspace, budgets, and local CI
|\
| * 2b42d36 docs(agents): prefer small commits merged back as one bubble
| * c756b0f chore(git): ignore personal VS Code settings
| * c002358 build: add the Cargo workspace and crate skeleton
| * ... (26 more flat commits — workspace scaffold and CI mashed into one flat wall!)
|/

# Chapter 8 (BAD — loose commits scattered around one partial dev-time bubble!)
* 0d383ce fix(core,docs): Post-Gate-1 cleanup 3 — governance, review P1 fixes, ADRs
|\
| * 251510d docs(adr): mark ADRs 0012 and 0013 accepted
| * b3d65ba style(core,ci): format review-fix files...          <-- dangling outside the fix bubble!
| *   17c8d68 fix(core): resolve P1 privacy and Feint findings  <-- only 3 of the 4 fix commits!
| |\
| | * b2b4b60 ...
| | * c318982 ...
| | * 442d621 ...
| |/
| * 8c269cf docs(agents): record frontier-model preference...   <-- 3 loose ungrouped doc commits!
| * 0cb0e72 docs(agents): clarify how budget caps weigh clarity...
| * 63b6684 docs: point stale references at rules.rs...
|/
```

**Why this fails:** Expanding a Chapter still dumps noisy dev-time plumbing (flat 29-commit walls, messy review micro-merges, and stray loose commits) instead of clean semantic Sub-Chapters.

---

## 3. Target Layout (REQUIRED): Uniform Lossless 3-Level Book-TOC — 389 commits

**8 Chapters -> 22 Semantic Sub-Chapters (`20` `--no-ff` sub-bubbles + `2` single-commit sections) -> all `361` original atomic commits preserved 1-to-1 verbatim** (becomes 4 levels when merged into `main` with `--no-ff`):

```text
# LEVEL 1 — 8-line Book TOC (git log --first-parent --reverse main..HEAD)
be5158c build(workspace): Milestone 1 — Day-1 Cargo workspace, structural budgets, and local CI suite
dc1ef39 feat(core): Milestone 2 — leaf layer for IDs, tags, Cards, expressions, packs, and load-time validation
4d0f888 feat(core,content): Milestone 3 — runtime state, pipelines, and Gate 1 SRD & house-rule content
7d1e4fb feat(core,cli): Milestone 4 — 14 step verbs, Engine facade, strict saves, privacy views, and CLI runner
ba6d6ee test(scenarios): Milestone 5 & Gate 1 close-out — 52 scenarios, exit review fixes, and owner sign-offs
a27089b refactor(core): Post-Gate-1 cleanup 1 — Design Goals and core deduplication
4f90319 feat(core,content): Post-Gate-1 cleanup 2 — wire explainability and waterbed vocabulary fixes
774bd5a fix(core,docs): Post-Gate-1 cleanup 3 — governance rules, frontier review P1 fixes, and ADR sign-offs

# LEVEL 2 + LEVEL 3 — Chapter 1 (2 clean Sub-Chapters holding all 29 original atomic commits):
*   be5158c build(workspace): Milestone 1 — Day-1 Cargo workspace, structural budgets, and local CI suite
|\
| *   2f119e1 ci: add local hygiene, budget, telemetry, and schema-drift check scripts
| |\
| | * 4a518f2 ... (24 original atomic commits, untouched and unsquashed) ... 8fd10ea
| |/
| *   f3c770c build(workspace): add the Cargo workspace, crate skeletons, and structural budgets
| |\
| | * 8e722ad ... (5 original atomic commits, untouched and unsquashed) ... d0315a1
| |/
|/

# LEVEL 2 + LEVEL 3 — Chapter 8 (3 clean Sub-Chapters: 8.1 [3], 8.2 [4], 8.3 [1]):
*   774bd5a (HEAD -> phase/1-core-engine) fix(core,docs): Post-Gate-1 cleanup 3 — governance, review P1 fixes, ADRs
|\
| * a57f452 docs(adr): mark ADRs 0012 and 0013 accepted                                 <-- 8.3 (1 commit, no sub-bubble)
| *   6f873a3 fix(core,ci): close frontier-review P1 privacy leaks, Feint bug, nits     <-- 8.2 (4 atomic commits grouped)
| |\
| | * caa9bcf style(core,ci): format review-fix files and skip pack fixtures in scenario count
| | * eb7275d fix(validate,ci): tighten aim_after_move validation, CI guards, and stale doc note
| | * b513c97 fix(core): spend condition-derived limited uses even when out-stacked
| | * f62fe35 fix(privacy): close breakdown, secret-reapply, and through_effect privacy leaks
| |/
| *   905cc99 docs(agents): record budget-cap clarity/reuse rule, lesson, rules.rs      <-- 8.1 (3 atomic commits grouped)
| |\
| | * 270aa16 docs(agents): record frontier-model preference for P0/P1 reviews
| | * 295debb docs(agents): clarify how budget caps weigh clarity and reuse
| | * 5d1d47d docs: point stale references at rules.rs and the renamed statistic body
| |/
|/
```

---

## Sample `plan.json` for `helpers/dag_rewrap.py`

Write `plan.json` to an OS temp directory (never inside the repository). Use `"start"` and `"end"` (inclusive atomic commit hashes from `inspect`) or `"commits"` (explicit list). Place `{{SUB_COMMITS}}` inside each merge message so `build` fills in the **actual new abbreviated hashes** after re-parenting:

```json
{
  "base": "main",
  "head": "a184ad1",
  "chapters": [
    {
      "title": "build(workspace): Milestone 1 — Day-1 Cargo workspace and local CI",
      "message": "build(workspace): Milestone 1 — Day-1 Cargo workspace and local CI\n\nEstablish the workspace skeleton, budgets, and local CI scripts.\n\n[--- Changes ---]\n\n- Sub-chapters included:\n{{SUB_COMMITS}}\n\n[--- AI Review (<model name>) ---]\n\nClean separation between workspace setup and CI tooling.",
      "sub_chapters": [
        {
          "title": "build(workspace): add Cargo workspace, crate skeletons, and budgets",
          "message": "build(workspace): add Cargo workspace, crate skeletons, and budgets\n\nSet up the initial crates and structural budgets.\n\n[--- Changes ---]\n\n- Sub-commits included:\n{{SUB_COMMITS}}\n\n[--- AI Review (<model name>) ---]\n\nSmall focused setup commits preserved verbatim.",
          "start": "d0315a1",
          "end": "8e722ad"
        },
        {
          "title": "ci: add local hygiene, budget, telemetry, and schema-drift scripts",
          "message": "ci: add local hygiene, budget, telemetry, and schema-drift scripts\n\nAdd the local verification scripts run before merges.\n\n[--- Changes ---]\n\n- Sub-commits included:\n{{SUB_COMMITS}}\n\n[--- AI Review (<model name>) ---]\n\nEach check script and self-test remains its own atomic commit.",
          "start": "8fd10ea",
          "end": "4a518f2"
        }
      ]
    },
    {
      "title": "fix(core,docs): Post-Gate-1 cleanup 3 — governance, review P1 fixes, ADRs",
      "message": "fix(core,docs): Post-Gate-1 cleanup 3 — governance, review P1 fixes, ADRs\n\nClose final documentation updates, P1 review findings, and ADR sign-offs.\n\n[--- Changes ---]\n\n- Sub-chapters included:\n{{SUB_COMMITS}}\n\n[--- AI Review (<model name>) ---]\n\nSingle-commit ADR acceptance stays directly inside the chapter without a redundant sub-bubble.",
      "sub_chapters": [
        {
          "title": "docs(agents): record budget-cap rule, review lesson, and rules.rs paths",
          "message": "docs(agents): record budget-cap rule, review lesson, and rules.rs paths\n\n...\n\n[--- Changes ---]\n\n- Sub-commits included:\n{{SUB_COMMITS}}\n\n[--- AI Review (<model name>) ---]\n\n...",
          "commits": ["55a7f86", "a8acb8e", "edec171"]
        },
        {
          "title": "fix(core,ci): close frontier-review P1 leaks, Feint bug, and formatting",
          "message": "fix(core,ci): close frontier-review P1 leaks, Feint bug, and formatting\n\n...\n\n[--- Changes ---]\n\n- Sub-commits included:\n{{SUB_COMMITS}}\n\n[--- AI Review (<model name>) ---]\n\n...",
          "start": "f62fe35",
          "end": "832af68"
        },
        {
          "title": "docs(adr): mark ADRs 0012 and 0013 accepted",
          "commits": ["a184ad1"]
        }
      ]
    }
  ]
}
```
