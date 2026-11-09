# Model Defaults

Single source of truth for default model identifiers and CLI flags used across skills. When a model version changes, update this file — all skills that reference it will pick up the new defaults.

**Consumers:** all skills that spawn same-platform subagents, plus codex, antigravity, claude, ai-council, codereview, and quick-review

---

## Model Identifiers

| Provider | Model ID | Used In |
|---|---|---|
| OpenAI (Codex CLI) | `gpt-6.1-sol` | `/codex`, `/ai-council`, `/codereview` |
| Google (Antigravity CLI) | *(managed by agy)* | `/antigravity`, `/ai-council`, `/codereview` |
| Anthropic (Claude CLI) | `opus` | `/claude` |
| Anthropic (Claude CLI) | `fable` | `/ai-council` (Claude leg) |

## Review Model Routing

Skills that let the user select one review model resolve the provider through
this registry:

| Model identifier | Provider | Command source |
|---|---|---|
| `gpt-6.1-sol` | Codex CLI | Codex template below |
| `fable` | Claude CLI | Claude template below with `--model fable` |

A known unique bare identifier routes to its registered provider. Custom or
ambiguous identifiers must be provider-qualified, such as
`codex:custom-model` or `claude:custom-model`. Never infer a provider from a
name pattern and never fail over silently when a configured model is
unavailable.

## Default CLI Command Templates

### Codex

```bash
codex exec --model gpt-6.1-sol -c model_reasoning_effort="xhigh" \
  --sandbox read-only --skip-git-repo-check 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `--model gpt-6.1-sol` | Model selection |
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
python <ADAPTER> --mode plan --sandbox
```

Invoke the adapter with `python3` where present, falling back to `python` on Windows — stock macOS/Linux expose only `python3`, so a bare `python` fails there even when Python 3 is installed. The resume commands below take the same interpreter.

| Part | Purpose |
|---|---|
| `<ADAPTER>` (`scripts/agy_adapter.py`) | Sends the prompt to `agy`, prints the final answer, and recovers replies from affected older releases |
| `--mode plan` | Safety: read-only. Plan mode blocks edits to the project (forwarded to `agy`) |
| `--sandbox` | Safety: restricts terminal commands only. It does **not** block file edits on its own (forwarded to `agy`) |

Plan mode may save an `implementation_plan.md` under
`~/.gemini/antigravity-cli/brain/<conversation-id>/`. That is `agy`'s own data
folder, not the project.

The prompt is delivered on **stdin** — the adapter forwards its own args to `agy`
and appends `--input-format stream-json --output-format stream-json`, so callers
must **not** pass `-p`, `--print`, or those format flags. For session resume, keep
`--mode plan --sandbox` and add `-c` (latest session) or `--conversation <ID>`.

The adapter rejects prompts larger than 150,000 bytes, because `agy` silently
drops the end of very large prompts. Shorten or split such prompts.

**Why the adapter?** Since `agy` 1.4.x a bare `-p` fails with `flag needs an
argument: -p`, and a prompt passed as an argument breaks above the Linux
per-argument limit (about 128 KB). The adapter sends the prompt on stdin as
stream-json instead and prints the answer from the final `result` event. Older
Windows releases could return empty non-TTY stdout after saving the reply
locally, so the adapter retains SQLite recovery as a compatibility fallback. It
also bounds the run with a 600-second timeout (killing any stray `agy` process)
and exits non-zero with a clear message if no reply can be recovered. Env
overrides (`AGY_BIN`, `AGY_CONV_DIR`, `AGY_ADAPTER_TIMEOUT`) and the recovery
mechanism are documented in `scripts/agy_adapter.py`.

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

## Same-Platform Subagent Defaults

Skills that spawn subagents through the current host MUST inherit the parent model and reasoning effort by default.

- **Claude Code:** omit the per-call `model` and `effort` fields. Claude Code treats an omitted model as `inherit`, so a Fable parent gets Fable subagents and an Opus parent gets Opus subagents.
- **Codex:** omit per-call model and reasoning-effort overrides. The subagent then follows the parent Codex model and reasoning effort.
- **Explicit overrides:** honor a model or effort override when the user specifically asks for one. Host-level settings deliberately configured by the user also count as overrides.
- **Cross-model work:** this rule does not apply when a skill intentionally calls another model or provider for independent evaluation or delegation. Those paths keep their explicit model selection.

Do not pin a same-platform subagent to `fable`, `opus`, a GPT model, or any other model alias inside a skill.

## Why `2>/dev/null`

CLI tools emit progress indicators, ANSI escape codes, and status messages on stderr. These are useful interactively but pollute captured output when running programmatically. Suppressing stderr keeps the response clean while stdout carries the actual model output. **Exception:** Codex prints its `session id:` banner on stderr — when resume matters, capture stderr to a temp file instead (see § Codex Resume).

## Standard Timeout

All CLI dispatches use **600000ms** (10 minutes) on the Bash tool. This accommodates long-running analysis tasks while preventing indefinite hangs.
