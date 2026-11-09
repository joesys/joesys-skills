# Devlog List Mode

Reference file for the devlog skill. Read it when the first argument is `list`. List mode reads files directly. It needs no subagents and asks no questions.

## Which Repos to Scan

1. Read `~/.claude/skill-context/devlog.md` (in the user's home folder, not the project). If it has a `## Devlog repos` section, scan every repo listed there, plus the current repo if it is not in the list.
2. If the file or the section is missing, scan only the current repo. After the output, add one line telling the user how to configure the list (see "Configuring Cross-Repo Listing").

Do not search the filesystem for other repos. Scan only the repos the user listed.

## Configuring Cross-Repo Listing

The repo list lives in one user-level file, so it works from any project:

```markdown
# Devlog Preferences

## Devlog repos
- ~/Projects/shop-api
- ~/Projects/game-engine
- ~/Projects/notes-app
```

This user-level file holds only the repo list. Tone and audience preferences stay in the project's `.claude/skill-context/devlog.md`.

One absolute path (or `~/` path) per line. If a listed path does not exist or has no `docs/devlog/`, show it under "Skipped repos" with the reason, and continue.

The hint line to show when no list is configured:

> Showing this repo only. To see scraps from all your repos, list them under `## Devlog repos` in `~/.claude/skill-context/devlog.md`, one path per line.

## Workflow

For each repo:

1. Scan `<repo>/docs/devlog/.scraps/*.md`. For each scrap, read the YAML frontmatter (`date`, `topic`, `status`) and the first sentence of the `## The Insight (Inferred)` section. Use that sentence as the title; cut it to about 70 characters. If the section is missing, use the topic as the title.
2. Scan `<repo>/docs/devlog/` for post directories (`YYYYMMDD-<topic>/`). Take the date and topic from the directory name.
3. Compute each scrap's age relative to today.

Then present one combined result. Use the repo folder name in the Repo column. Show the Repo column only when more than one repo was scanned.

```
Scraps (<N> unwritten across <M> repos):

  Age      Repo         Date        Title
  82 days  shop-api     2026-08-19  Convert currency at the edge, not deep inside the tax code ...
  12 days  game-engine  2026-10-28  A retry hid the real timeout; log the first failure ...
  today    notes-app    2026-11-09  ssh-signing-recovery

Posts (<N> published):

  Repo      Date        Topic                    Path
  shop-api  2026-03-25  oneflow-branching        ~/Projects/shop-api/docs/devlog/20260325-oneflow-branching/
```

- Scraps sorted by age (oldest first — nudge to write them before context fades).
- Posts sorted by date (most recent first).
- Under the scraps table, show how to start a post from one:
  - For a scrap in the current repo: `/devlog --from-scrap <filename stem>`.
  - For a scrap in another repo: open a session in that repo, then run `/devlog --from-scrap <filename stem>` there. The post, the scrap cleanup, and the commit all belong in the scrap's repo.
- If no scraps exist, show: "No scraps. Use `/devlog scrap` to capture insights for later."
- If no posts exist, show: "No published posts yet. Use `/devlog` to write your first one."
- If `docs/devlog/` does not exist in a repo, treat it as having no scraps and no posts.
