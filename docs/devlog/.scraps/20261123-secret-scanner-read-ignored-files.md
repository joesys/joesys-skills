---
date: 2026-11-23
topic: secret-scanner-read-ignored-files
project: joesys-skills
session: unknown
status: unwritten
---

## Situation
A real `/security-audit` run on 2026-11-22 audited a TypeScript monorepo of
about 600,000 lines. Afterwards the skill was updated with what that run
showed (merge `1fdb9ed`, version 22.3.0). One lesson was about the secret
scanner Gitleaks, the tool that was supposed to protect secrets.

## Key Moments
1. **The safety tool broke the safety rule** — `gitleaks dir` on the working
   folder also read every file that git ignores. It opened `.env` files,
   which the skill's rule says must stay closed, and about 1,200 of its
   hits came from build output such as `cdk.out/` and `.next/`. The
   alternative was an exclude list. The skill chose to scan a
   `git archive` copy of the audited commit in a temporary folder instead.
   Inferred reason: an exclude list must name every secret file and every
   build folder ahead of time, but a copy of the commit can only hold what
   was committed.
2. **"The history" was more than the audited commit** — `gitleaks git`
   scans every branch and tag. One hit was only on a pushed feature branch.
   The alternative was to drop such hits as out of scope. The skill keeps
   them, checks each one with `git merge-base --is-ancestor` and
   `git branch -r --contains`, and labels it "outside the audited commit".
   Inferred reason: a secret on a pushed branch is exposed just like one on
   the main branch.
3. **A model's "no secrets" was wrong** — one finder model wrote that the
   history held no secrets, and Gitleaks found a key pair. The scan is now
   required whenever the tool is installed, whatever the finders say.
4. **The documentation example was a trap** — one file held both the AWS
   example key ID `AKIAIOSFODNN7EXAMPLE` and a real-looking key. So a file
   is not dismissed because it holds the example. A small script compares
   key IDs with the example by hash and prints only counts, so the check
   itself never shows a secret.

## The Insight (Inferred)
Point a scanner at exactly the thing you are auditing, not at the folder
where that thing happens to live. The working folder holds more than the
commit (ignored files, build output), and `git` history holds more than the
commit's past (other branches). Both mistakes made the tool read too much:
in one case that broke a privacy rule, and in the other it hid where a
finding really was. A second idea also comes from this run: a tool that
handles secrets needs its own guard, such as comparing by hash and printing
counts, so that the check cannot leak what it checks.

## Supporting Evidence
- **Commits:**
  - `66aab51` feat(security-audit): handle a blocked Codex run, add Grok as a third finder, and scan secrets in a clean copy
  - `333da16` chore(plugin): publish the collection as version 22.3.0
  - `d8f6a69` fix(security-audit): give the manual Codex prompt that got past the filter, word for word
  - `1fdb9ed` merge into master
- **Conversation exchanges:**
  - Developer (from the live-run notes): "Scan a clean `git archive` export,
    not the working folder. `gitleaks git` scans all refs."
  - AI (live test, 2026-11-22): the export left out an ignored `.env` file,
    and the reachability check told a commit on another branch from one in
    the history.
- **Code snippets:**

  ```bash
  EXPORT="$(mktemp -d)"
  git -C <REPO> archive HEAD -- <SCOPE_PATH> | tar -x -C "$EXPORT"
  (cd "$EXPORT" && gitleaks dir --redact --no-banner --report-format json \
    --report-path "$RUN_DIR/gitleaks-files.json" .)
  rm -rf "$EXPORT"
  ```

## Open Questions
- How was the `.env` read noticed in the live run: from the report paths,
  or from the hit count?
- Did anyone consider `gitleaks git --log-opts` to limit the history to the
  audited commit, and why was a reachability label preferred?
- The copy leaves out uncommitted changes. How often does an audit run on a
  working folder with uncommitted work?
- Other lessons of the same run could be posts of their own: the Codex
  safety filter that blocked a defensive audit, and Grok runs that stopped
  silently with exit code 0.
