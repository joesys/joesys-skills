# Model Defaults

Single source of truth for default model identifiers and CLI flags used across skills. When a model version changes, update this file — all skills that reference it will pick up the new defaults.

**Consumers:** codex, antigravity, claude, ai-council, codereview, quick-review

---

## Model Identifiers

| Provider | Model ID | Used In |
|---|---|---|
| OpenAI (Codex CLI) | `gpt-5.6-sol` | `/codex`, `/ai-council`, `/codereview`, `/quick-review` |
| Google (Antigravity CLI) | *(managed by agy)* | `/antigravity`, `/ai-council`, `/codereview` |
| Anthropic (Claude CLI) | `opus` | `/claude`, `/codereview`, `/quick-review` |
| Anthropic (Claude CLI) | `fable` | `/ai-council` (Claude leg) |

## Default CLI Command Templates

### Codex

```bash
codex exec --model gpt-5.6-sol -c model_reasoning_effort="xhigh" \
  --sandbox read-only --skip-git-repo-check 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `--model gpt-5.6-sol` | Model selection |
| `-c model_reasoning_effort="xhigh"` | Maximum reasoning depth |
| `--sandbox read-only` | Safety: no file writes |
| `--skip-git-repo-check` | Required for piped input |
| `2>/dev/null` | Suppress progress/ANSI noise on stderr — but see Resume: capture to a file instead when resume matters |

#### Codex Resume

```bash
codex exec resume <SESSION_ID> --skip-git-repo-check "<PROMPT>" 2>/dev/null   # by session id (preferred)
codex exec resume --last --skip-git-repo-check "<PROMPT>" 2>/dev/null         # most recent session
```

| Rule | Detail |
|---|---|
| Session ID capture | `codex exec` prints `session id: <UUID>` on **stderr** — dispatch with `2>"$CODEX_LOG"` and `grep -m1 "session id:"` it; a discarded banner leaves only `--last` resume |
| Flag order | `--skip-git-repo-check` goes after `resume`, not between `exec` and `resume` |
| Not accepted on resume | `--sandbox`, `--full-auto` |
| Write access on resume | `-c sandbox_mode="workspace-write"` |
| Inheritance | Resumed sessions keep model, reasoning effort, and sandbox from the original run |

### Antigravity

Dispatch through the adapter, **not** `agy` directly. `<ADAPTER>` is the **absolute path** to `scripts/agy_adapter.py` under the plugin root (the directory containing this file's parent, `shared/`) — resolve it before running; the project's working directory does not contain the adapter:

```bash
python <ADAPTER> --sandbox
```

Invoke the adapter with `python3` where present, falling back to `python` on Windows — stock macOS/Linux expose only `python3`, so a bare `python` fails there even when Python 3 is installed. The resume commands below take the same interpreter.

| Part | Purpose |
|---|---|
| `<ADAPTER>` (`scripts/agy_adapter.py`) | Recovers the reply `agy` writes only to a TTY (see below) |
| `--sandbox` | Safety: read-only (forwarded to `agy`) |

The prompt is delivered on **stdin** — the adapter forwards its own args to `agy`
and appends `-p ""`, so callers must **not** pass `-p`. For session resume, replace
`--sandbox` with `-c` (latest session) or `--conversation <ID>`.

**Why the adapter?** `agy` v1.0.9 is a terminal-UI app whose print mode renders the
model's reply only to an interactive terminal; piped/captured stdout receives
**0 bytes**. The adapter runs `agy`, recovers the reply from agy's local conversation
store, and prints it to stdout — restoring stdout capture. It also bounds the run with
a timeout (killing any stray `agy` process) and exits non-zero with a clear message if
no reply can be recovered. Env overrides (`AGY_BIN`, `AGY_CONV_DIR`,
`AGY_ADAPTER_TIMEOUT`) and the recovery mechanism are documented in
`scripts/agy_adapter.py`.

### Claude CLI

```bash
claude --model opus --effort high --permission-mode plan -p "" 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `--model opus` | Model selection — `/ai-council`'s Claude leg substitutes `--model fable` |
| `--effort high` | Reasoning effort level |
| `--permission-mode plan` | Safety: read-only |
| `-p ""` | Non-interactive mode (stdin provides the prompt) |
| `2>/dev/null` | Suppress progress/ANSI noise on stderr |

#### Claude CLI Resume

```bash
claude -c -p "<PROMPT>" 2>/dev/null                  # most recent session
claude --resume "<NAME>" -p "<PROMPT>" 2>/dev/null   # named session (set at dispatch via --name)
```

## Agent Tool (Subagent) Model

Skills that spawn subagents via the Agent tool pin an explicit model alias. Two tiers are in use:

| Model | Skills |
|---|---|
| `fable` | `/ai-council`, `/explain`, `/readability-review`, `/codebase-audit` |
| `opus` | all other subagent-spawning skills (`/codereview`, `/quick-review`, `/devlog`, `/retrospective`, `/interaction-review`, `/human-review-guide`, `/handbook`) |

This section is the single source of truth for that choice: if a skill's default subagent model changes, update this table and the inline literals (`grep -rn 'model: "' skills/`).

## Why `2>/dev/null`

CLI tools emit progress indicators, ANSI escape codes, and status messages on stderr. These are useful interactively but pollute captured output when running programmatically. Suppressing stderr keeps the response clean while stdout carries the actual model output. **Exception:** Codex prints its `session id:` banner on stderr — when resume matters, capture stderr to a temp file instead (see § Codex Resume).

## Standard Timeout

All CLI dispatches use **600000ms** (10 minutes) on the Bash tool. This accommodates long-running analysis tasks while preventing indefinite hangs.
