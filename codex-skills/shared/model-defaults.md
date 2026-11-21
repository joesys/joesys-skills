# Model Defaults

Single source of truth for default model identifiers and CLI flags used across skills. When a model version changes, update this file — all skills that reference it will pick up the new defaults.

**Consumers:** all skills that spawn same-platform subagents, plus codex, antigravity, claude, grok, ai-council, codereview, quick-review, architect, and security-audit

---

## Model Identifiers

| Provider | Model ID | Used In |
|---|---|---|
| OpenAI (Codex CLI) | `gpt-6.2-sol` | `$codex`, `$ai-council`, `$codereview`, `$architect`, `$security-audit` (finder) |
| OpenAI (Codex CLI) | `gpt-6.2-astra` | `$security-audit` (reviewer) |
| Google (Antigravity CLI) | *(managed by agy)* | `$antigravity`, `$ai-council`, `$codereview`, `$architect` |
| Anthropic (Claude CLI) | `fable` | `$claude`, `$ai-council` (Claude leg), `$security-audit` (reviewer) |
| xAI (Grok CLI) | *(managed by grok)* | `$grok`, `$ai-council` |

`fable` is a name that the Claude CLI resolves to its newest model of that line. The Codex CLI has no such names, so its identifiers are updated here by hand. The Codex identifiers were checked against the model list of the Codex CLI and with a live call on 2026-11-21.

## Review Model Routing

Skills that let the user select one review model resolve the provider through
this registry:

| Model identifier | Provider | Command source |
|---|---|---|
| `gpt-6.2-sol` | Codex CLI | Codex template below |
| `fable` | Claude CLI | Claude template below |

A known unique bare identifier routes to its registered provider. Custom or
ambiguous identifiers must be provider-qualified, such as
`codex:custom-model` or `claude:custom-model`. Never infer a provider from a
name pattern and never fail over silently when a configured model is
unavailable.

## Default CLI Command Templates

### Codex

```bash
codex exec --model gpt-6.2-sol -c model_reasoning_effort="xhigh" \
  --sandbox read-only --skip-git-repo-check 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `--model gpt-6.2-sol` | Model selection |
| `-c model_reasoning_effort="xhigh"` | Maximum reasoning depth |
| `--sandbox read-only` | Safety: no file writes |
| `--skip-git-repo-check` | Required for piped input |
| `2>/dev/null` | Suppress progress noise on stderr — but capture stderr to a file when resume matters (see Codex Resume) |

#### Codex Resume

```bash
# by session id (preferred)
codex exec resume <SESSION_ID> --model gpt-6.2-sol -c model_reasoning_effort="xhigh" \
  -c sandbox_mode="read-only" --skip-git-repo-check "<PROMPT>" 2>/dev/null
# most recent session
codex exec resume --last --model gpt-6.2-sol -c model_reasoning_effort="xhigh" \
  -c sandbox_mode="read-only" --skip-git-repo-check "<PROMPT>" 2>/dev/null
```

| Rule | Detail |
|---|---|
| Session ID capture | `codex exec` prints `session id: <UUID>` on **stderr** — dispatch with `2>"$CODEX_LOG"` and `grep -m1 "session id:"` it; a discarded banner leaves only `--last` resume. With `--json`, the first event on stdout carries it as `thread_id` |
| Flag order | `--skip-git-repo-check` goes after `resume`, not between `exec` and `resume` |
| Not accepted on resume | `--sandbox`, `--full-auto`. Set the sandbox with `-c sandbox_mode="read-only"` |
| Nothing is kept | A resumed session takes its model, its reasoning effort and its sandbox from the user's own Codex settings, not from the first run. Give all three again on every resume. Use the model and the effort of the first run |
| Write access on resume | `-c sandbox_mode="workspace-write"` in place of the read-only value, and only when the user asks for it |

Why "nothing is kept": in a live test with codex-cli 0.171.0 on 2026-11-21, a session was started with `--sandbox read-only` and one model. Resumed without flags, it ran with the model and the reasoning effort of the user's settings, with write access to the folder, and it wrote a file. Resumed with `-c sandbox_mode="read-only"`, it refused the write.

### Antigravity

Dispatch through the adapter, not `agy` directly. `<ADAPTER>` is the **absolute path** to `../scripts/agy_adapter.py` under the collection root (the directory containing this file's parent, `./`) — resolve it before running; the project's working directory does not contain the adapter:

```bash
python <ADAPTER> --mode plan --sandbox
```

Invoke the adapter with `python3` where present, falling back to `python` on Windows — stock macOS/Linux expose only `python3`, so a bare `python` fails there even when Python 3 is installed. The resume commands below take the same interpreter.

| Part | Purpose |
|---|---|
| `<ADAPTER>` (`../scripts/agy_adapter.py`) | Sends the prompt to `agy`, prints the final answer, and recovers replies from affected older releases |
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
`../scripts/agy_adapter.py`.

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
claude -c --permission-mode plan -p "<PROMPT>" 2>/dev/null                  # most recent session
claude --resume "<NAME>" --permission-mode plan -p "<PROMPT>" 2>/dev/null   # named session (set at dispatch via --name)
```

A resumed session does not keep its permission mode. Give `--permission-mode plan` again on every resume. In a live test with Claude Code 2.1.330 on 2026-11-21, a session that was started in plan mode and resumed without the flag ran in the mode `default`. It kept its model. The reasoning effort was not tested, so give `--effort` again when it matters.

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
- **Cross-model work:** this rule does not apply when a skill intentionally calls another model or provider for independent evaluation or delegation. Those paths keep their explicit model selection. The finders and the reviewer of `$security-audit` are such paths: each one is a separate session of a command-line tool, with the model that § Security Audit Roles names.

Do not pin a same-platform subagent to `fable`, `opus`, a GPT model, or any other model alias inside a skill.

## Security Audit Roles

`$security-audit` uses four models. The skill names the roles. This table names the models.

| Role | Tool | Identifier | Reasoning effort |
|---|---|---|---|
| Finder 1 | Claude CLI | `opus` | high |
| Finder 2 | Codex CLI | `gpt-6.2-sol` | xhigh |
| Writer | the host | the model that runs the skill, usually `fable` or `gpt-6.2-astra` | as the user set it |
| Reviewer, when the writer is a Claude model | Codex CLI | `gpt-6.2-astra` | xhigh |
| Reviewer, when the writer is a GPT model | Claude CLI | `fable` | high |

`opus` and `fable` are names that the Claude CLI resolves to its newest model of that line. Finder 1 is the only place in this collection that asks for `opus`: the default for delegation to Claude stays `fable`.

The reviewer always comes from the other provider. When the writer is neither a Claude model nor a GPT model, use the Codex reviewer.

Every role runs as its own session of a command-line tool, read-only, through `../security-audit/helpers/finder_runs.py`. That launcher sends the prompt on stdin and has no time limit. So these commands have no prompt argument and no `2>/dev/null`: the launcher keeps stdout and stderr in files.

```bash
# Finder 1, and the Claude reviewer with its own identifier. Start it with --stream-result.
claude --model <IDENTIFIER> --effort high --permission-mode plan -p --output-format stream-json --verbose

# Finder 2, and the Codex reviewer with its own identifier. The launcher fills in {final}.
codex exec --model <IDENTIFIER> -c model_reasoning_effort="xhigh" --sandbox read-only \
  --skip-git-repo-check --json -o {final}
```

| Part | Purpose |
|---|---|
| `--permission-mode plan`, `--sandbox read-only` | Safety: the model reads and cannot write |
| `--output-format stream-json --verbose`, `--json` | The tool prints one event after another while it works. The watch reads this to tell a working run from a stuck one |
| `--stream-result` (launcher) | The Claude CLI gives its final answer as the last `result` event. The launcher copies it into the answer file |
| `-o {final}` | The Codex CLI writes its final answer into that file |

To resume one of these sessions, add the resume part and keep every other flag:

```bash
claude --resume <SESSION_ID> --model <IDENTIFIER> --effort high --permission-mode plan -p --output-format stream-json --verbose
codex exec resume <SESSION_ID> --model <IDENTIFIER> -c model_reasoning_effort="xhigh" -c sandbox_mode="read-only" \
  --skip-git-repo-check --json -o {final} -
```

The last `-` of the Codex command means "read the prompt from stdin". Without the model, the effort and the read-only flag, a resumed session falls back to the user's own settings (see § Codex Resume and § Claude CLI Resume).

These commands were checked with live runs on 2026-11-21 (Claude Code 2.1.330, codex-cli 0.171.0). In read-only mode both tools could start helper agents of their own, could read a file outside the project folder, and refused to write.
