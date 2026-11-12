# Model Defaults

Single source of truth for default model identifiers and CLI flags used across skills. When a model version changes, update this file — all skills that reference it will pick up the new defaults.

**Consumers:** all skills that spawn same-platform subagents, plus codex, antigravity, claude, grok, ai-council, codereview, and quick-review

---

## Model Identifiers

| Provider | Model ID | Used In |
|---|---|---|
| OpenAI (Codex CLI) | `gpt-6.1-sol` | `/codex`, `/ai-council`, `/codereview` |
| Google (Antigravity CLI) | *(managed by agy)* | `/antigravity`, `/ai-council`, `/codereview` |
| Anthropic (Claude CLI) | `fable` | `/claude`, `/ai-council` (Claude leg) |
| xAI (Grok CLI) | *(managed by grok)* | `/grok` |

## Review Model Routing

Skills that let the user select one review model resolve the provider through
this registry:

| Model identifier | Provider | Command source |
|---|---|---|
| `gpt-6.1-sol` | Codex CLI | Codex template below |
| `fable` | Claude CLI | Claude template below |

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
| `2>/dev/null` | Suppress progress noise on stderr — but capture stderr to a file when resume matters (see Codex Resume) |

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

Dispatch through the adapter, not `agy` directly. `<ADAPTER>` is the **absolute path** to `scripts/agy_adapter.py` under the plugin root (the directory containing this file's parent, `shared/`) — resolve it before running; the project's working directory does not contain the adapter:

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

Why the adapter exists, its own 600-second timeout, and its environment overrides
(`AGY_BIN`, `AGY_CONV_DIR`, `AGY_ADAPTER_TIMEOUT`) are documented in
`scripts/agy_adapter.py`.

### Claude CLI

```bash
claude --model fable --effort high --permission-mode plan -p "" 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `--model fable` | Model selection |
| `--effort high` | Reasoning effort level |
| `--permission-mode plan` | Safety: read-only |
| `-p ""` | Non-interactive mode (stdin provides the prompt) |
| `2>/dev/null` | Suppress progress/ANSI noise on stderr |

#### Claude CLI Resume

```bash
claude -c -p "<PROMPT>" 2>/dev/null                  # most recent session
claude --resume "<NAME>" -p "<PROMPT>" 2>/dev/null   # named session (set at dispatch via --name)
```

### Grok

```bash
grok --permission-mode plan --deny "Bash(touch *)" --deny "Bash(mkdir *)" --prompt-file "$PROMPT_FILE"
```

| Flag | Purpose |
|---|---|
| `--permission-mode plan` | Safety: read-only. A non-interactive plan run refuses file edits. It also cannot approve anything else that needs approval, such as a command that changes something or a subagent, so those do not run. The flag replaces the permission mode from the user's own Grok settings |
| `--deny "Bash(touch *)" --deny "Bash(mkdir *)"` | Safety: Grok counts `touch` and `mkdir` as read-only and runs them without approval, even in plan mode. These two rules refuse them |
| `--prompt-file "$PROMPT_FILE"` | Non-interactive mode, with the prompt read from the temp file. Grok does not read the prompt from stdin |

This safety is a set of permission rules, not a sandbox. It depends on Grok asking for approval before a command that changes something, so never combine it with `--always-approve`. Grok's own guide says that its list of read-only commands is not a security boundary. Read-only commands such as `git log` still run. When Grok does need approval, it stops the run there: the exit code is still 0, the answer is cut short, and stderr has one line that starts with `permission required:`.

Three things are left out of the template on purpose:

- **Model and reasoning effort.** Grok uses the defaults from the user's own Grok settings. Pass `--model <MODEL>` or `--effort <LEVEL>` only when the user asks. The command `grok models` lists the model IDs.
- **`--sandbox read-only`.** In a live test on one Linux machine, grok 1.0.77 refused to start with this flag. Do not add it without a new live test.
- **`2>/dev/null`.** stderr is the only place where Grok reports an answer that was cut short. Send stderr to a file and show it. Only a `permission required:` line or an error message means trouble. Any other line is a note, such as `Session ... found locally` on a resume from another folder.

Plan mode may save a `plan.md` under `~/.grok/sessions/`. That is Grok's own data folder, not the project.

#### Grok Resume

A resume is the whole template above plus one flag, so it keeps every safety flag. `<GROK_CMD>` is that template.

```bash
<GROK_CMD> --resume <SESSION_ID>   # by session ID (preferred)
<GROK_CMD> -c                      # newest session in this folder
```

| Rule | Detail |
|---|---|
| Session ID | Chosen before the first run: pass `--session-id <UUID>` with a new UUID. A resume takes that ID with `--resume`. `--session-id` only names a new session |
| Safety flags on resume | Never shorten the template. A resumed session without `--permission-mode plan` follows the user's own Grok settings. In a live test with `always-approve` in those settings, it approved its own plan and wrote a file |
| `-c` | Continues the newest Grok session started in the current folder. That may be the user's own session, not this skill's |

These commands and rules were checked with live runs of grok 1.0.77 on 2026-11-12.

## Same-Platform Subagent Defaults

Skills that spawn subagents through the current host inherit the parent model and reasoning effort by default.

- **Claude Code:** omit the per-call `model` and `effort` fields. Claude Code treats an omitted model as `inherit`, so a Fable parent gets Fable subagents and an Opus parent gets Opus subagents.
- **Codex:** omit per-call model and reasoning-effort overrides. The subagent then follows the parent Codex model and reasoning effort.
- **Explicit overrides:** honor a model or effort override when the user specifically asks for one. Host-level settings deliberately configured by the user also count as overrides.
- **Cross-model work:** this rule does not apply when a skill intentionally calls another model or provider for independent evaluation or delegation. Those paths keep their explicit model selection.

Do not pin a same-platform subagent to `fable`, `opus`, a GPT model, or any other model alias inside a skill.
