# Scanner tools

Three tools find what a model reads past: known-bad code patterns, secrets,
and libraries with published security notices. They are a help, not a
need. The audit runs without them, and the report then says which tool did
not run.

The general safety rules for tools are in `shared/tooling-registry.md`. A
language may have more security tools. See the Tier 4 entries of
`shared/tooling/<language>.md` and use the ones that are installed.

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

| System | Install command |
|---|---|
| Linux, macOS | `uv tool install semgrep` or `pipx install semgrep` |
| macOS with Homebrew | `brew install semgrep` |
| Windows (beta) | Install Python, then `pipx install semgrep` or `uv tool install semgrep`. See the Semgrep documents for the one environment setting that Windows needs. |

## Gitleaks: secrets in files and in the git history

Finds keys, tokens and passwords, also in old commits.

```bash
gitleaks git --redact --no-banner --report-format json \
  --report-path "$RUN_DIR/gitleaks.json" <REPO>
gitleaks dir --redact --no-banner --report-format json \
  --report-path "$RUN_DIR/gitleaks-files.json" <SCOPE_PATH>
```

- `gitleaks git` reads the history. `gitleaks dir` reads the files as they
  are now. Exit code 1 means that it found something, or that it failed:
  read the report file to tell which.
- **Leaves the machine:** nothing is documented. The scan reads local files
  and the local history.
- **The report file may hold secret values.** `--redact` hides them in the
  screen output. The Gitleaks documents do not promise the same for the
  report file. So read only these fields: `RuleID`, `File`, `StartLine`,
  `Commit`, `Date`. Never read, copy or print `Secret` or `Match`. Delete
  both report files when the candidates are written down.
- A hit in the history means that the value was once committed. It may
  still be valid. The finding asks a person to check and to replace it.
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
tools on 2026-11-21. None of the three tools was run for this check.
