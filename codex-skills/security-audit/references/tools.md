# Scanner tools

Three tools find what a model reads past: known-bad code patterns, secrets,
and libraries with published security notices. They are a help, not a
need. The audit runs without them, and the report then says which tool did
not run.

The general safety rules for tools are in `../shared/tooling-registry.md`. A
language may have more security tools. See the Tier 4 entries of
`../shared/tooling/<language>.md` and use the ones that are installed.

## The rules

1. **The skill never installs a tool.** It shows the user the command, and
   the user runs it.
2. **Ask once, in the start notice.** For each missing tool, the user
   chooses: install it first, or proceed without it.
3. **Report only.** Use the commands below. Never pass a flag that repairs
   or rewrites files.
4. **Say what leaves the machine.** Each tool below has a line for it. Put
   those lines into the start notice.
5. **Write the tool's output into the run folder**, never into the project.
6. **A tool result is a candidate.** Check it against the code like any
   other candidate.

## Which tools are installed

```bash
for tool in semgrep gitleaks osv-scanner; do
  command -v "$tool" >/dev/null 2>&1 && echo "installed: $tool" || echo "missing: $tool"
done
```

On Windows, use `where <tool>`.

## Semgrep: code patterns

Finds known risky patterns in many languages.

```bash
semgrep scan --config p/default --metrics=off --no-autofix --quiet \
  --json --output="$RUN_DIR/semgrep.json" <SCOPE_PATH>
```

- **Leaves the machine:** the tool downloads the rule pack `p/default` from
  the Semgrep registry. With `--metrics=off` it sends no usage data. The
  Semgrep documents say that source code never leaves the machine.
- Use the rule pack by name, never `--config auto`: that option sends the
  project's address to the registry.
- If the command fails because metrics are off, tell the user and stop this
  tool. Do not switch metrics on without asking.
- Read `results[]`: `check_id`, `path`, `start.line`, `extra.severity`,
  `extra.message`.
- Read `errors[]` too, and summarise them under "What was not checked", by
  kind and count, with the main folders. In the live run of 2026-11-22,
  `p/default` on a large repository gave 102 errors: `PartialParsing` on
  `.mjs` files, and timeouts on large vendored JavaScript files. A file
  with an error was checked in part or not at all.

| System | Install command |
|---|---|
| Linux, macOS | `uv tool install semgrep` or `pipx install semgrep` |
| macOS with Homebrew | `brew install semgrep` |
| Windows (beta) | Install Python, then `pipx install semgrep` or `uv tool install semgrep`. See the Semgrep documents for the one environment setting that Windows needs. |

If the install stops while it builds a package, the default Python of the
system is too new for Semgrep. Name an older one:
`uv tool install --python 3.13 semgrep`. This happened in a test on
2026-11-21, where the default Python was 3.14.

## Gitleaks: secrets in files and in the git history

Finds keys, tokens and passwords, also in old commits.

```bash
gitleaks git --redact --no-banner --report-format json \
  --report-path "$RUN_DIR/gitleaks.json" <REPO>
EXPORT="$(mktemp -d)"
git -C <REPO> archive HEAD -- <SCOPE_PATH> | tar -x -C "$EXPORT"
(cd "$EXPORT" && gitleaks dir --redact --no-banner --report-format json \
  --report-path "$RUN_DIR/gitleaks-files.json" .)
rm -rf "$EXPORT"
```

- `gitleaks git` reads the history. `gitleaks dir` reads the files of a
  folder. Exit code 1 means that it found something, or that it failed:
  read the report file to tell which.
- **Scan a clean copy of the commit, never the working folder.** `gitleaks
  dir` also reads every file that git ignores. In the live run of
  2026-11-22, a scan of the working folder read `.env` files, which breaks
  the rule that a secret file stays closed, and about 1,200 hits came from
  build output such as `cdk.out/` and `.next/`. `git archive` copies only
  the tracked files of the commit into a temporary folder outside the
  project. Delete that folder when the scan has ended. For the whole
  repository, leave out `-- <SCOPE_PATH>`. The `File` of each hit is then
  the path in the repository.
- The copy holds the commit, not the uncommitted changes. When the working
  folder has uncommitted changes, say under "What was not checked" that the
  secret scan did not cover them.
- **Leaves the machine:** nothing is documented. The scan reads local files
  and the local history.
- **Read only these fields of a report:** `RuleID`, `File`, `StartLine`,
  `Commit`, `Date`. Never read, copy or print `Secret` or `Match`. With
  gitleaks 8.30.1 on 2026-11-22, `--redact` replaced the value with
  `REDACTED` in the report file too. The Gitleaks documents do not promise
  that, so the rule stays. Delete both report files when the candidates are
  written down.
- A hit in the history means that the value was once committed. It may
  still be valid. The finding asks a person to check and to replace it.
- **`gitleaks git` scans every branch and tag, not only the audited
  commit.** In the live run, one hit was only on a pushed feature branch.
  For each history hit, check where its commit is:

  ```bash
  git -C <REPO> merge-base --is-ancestor <COMMIT> <AUDITED_COMMIT> \
    && echo "in the history of the audited commit" || echo "outside the audited commit"
  git -C <REPO> branch -r --contains <COMMIT>   # the remote branches that hold it, as of the last fetch
  ```

  Label a hit outside the audited commit "outside the audited commit", and
  name the branches. A value on a pushed branch is exposed like one on the
  main branch.
- **AWS key IDs: compare with the documentation example by hash only.**
  AWS documents use the example key ID `AKIAIOSFODNN7EXAMPLE`. Gitleaks did
  not report it in a test on 2026-11-22. But in the live run, one file held
  both that example and a real-looking key ID with a secret key beside it.
  So do not dismiss a file because it holds the example. Check each hit
  line with this script. It prints counts, never a value:

  ```bash
  python3 - "<FILE>" <LINE> << 'PY'
  import hashlib, re, sys
  EXAMPLE = hashlib.sha256(b"AKIAIOSFODNN7EXAMPLE").hexdigest()
  lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
  found = re.findall(r"(?:AKIA|ASIA)[A-Z0-9]{16}", lines[int(sys.argv[2]) - 1])
  hashes = [hashlib.sha256(key.encode()).hexdigest() for key in found]
  print(f"line {sys.argv[2]}: {hashes.count(EXAMPLE)} documentation example, "
        f"{len(hashes) - hashes.count(EXAMPLE)} other key IDs")
  PY
  ```

  `<FILE>` is the tracked file in `<REPO>`. For a hit in the history, give
  the file of that commit with `<(git -C <REPO> show "<COMMIT>:<PATH>")` in
  place of `"<FILE>"`.
  A count of 0 and 0 means that the line holds no key ID: the hit is of
  another kind, such as a secret access key. It does not mean that the line
  is safe.
- **The scan is not optional when the tool is installed.** A finder may
  write that it found no secret in the history. In the live run, one finder
  did, and Gitleaks found a key pair. Run the scan whatever the finders say.
- If your version does not know `git` and `dir`, it is older than 8.19:
  tell the user to update it.

| System | Install command |
|---|---|
| Arch Linux | `pacman -S gitleaks` |
| macOS, Linux with Homebrew | `brew install gitleaks` |
| Any system | Download the program for your system from the releases page of the Gitleaks project on GitHub. |

## OSV-Scanner: libraries with published security notices

Compares the lock files of the project with the OSV database.

```bash
osv-scanner scan source -r --format json \
  --output-file "$RUN_DIR/osv.json" <SCOPE_PATH>
```

- Exit code 1 means that it found a notice. Exit code 128 means that it
  found no lock file.
- **Leaves the machine:** the names, the versions and the ecosystems of the
  project's libraries, and file hashes, go to the OSV service of Google.
  The OSV-Scanner documents say that no source code is sent.
- To send nothing, the user can download the database once and scan
  offline: add `--offline --download-offline-databases` to the command for
  the download, and `--offline` alone afterwards.
- Never run `osv-scanner fix`. It changes files.
- Each result is a version match: nobody has read the library. Rate it by
  the limits in `finding-rules.md`, and say whether the app uses the faulty
  feature.

| System | Install command |
|---|---|
| Arch Linux | `pacman -S osv-scanner` |
| macOS, Linux with Homebrew | `brew install osv-scanner` |
| Windows | `winget install Google.OSVScanner` or `scoop install osv-scanner` |
| Any system with Go | `go install github.com/google/osv-scanner/v2/cmd/osv-scanner@latest` |

## How to guide the user

Look at the user's system first: the operating system, and which of
`pacman`, `brew`, `winget`, `uv`, `pipx` and `go` are present. Then show
only the command that fits, one line for each missing tool. For example, on
Arch Linux with `uv`:

```text
Three scanner tools can help the audit. They are not installed:
  semgrep      uv tool install semgrep
  gitleaks     sudo pacman -S gitleaks
  osv-scanner  sudo pacman -S osv-scanner
Install them first, or proceed without them?
```

After the user says that a tool is installed, check again with
`command -v` before you use it.

## In the report

Under "How this report was made", list each tool: whether it ran, its
version, and how many of its results became findings. Under "What was not
checked", name each tool that did not run and what it would have covered.

These commands and facts were checked against the documents of the three
tools on 2026-11-21. The Semgrep command was also run that day, with Semgrep
1.186.0: it worked with metrics off, wrote the result file, and changed no
file. On 2026-11-22, Semgrep and Gitleaks ran in a live audit of a large
repository. The Gitleaks export, the reachability check and the AWS script
were also run that day on a test repository with a made-up key, with
gitleaks 8.30.1: the export left out an ignored `.env` file, the check told
a commit on another branch from one in the history, and the script told the
example from the made-up key. OSV-Scanner was not run for this check.
