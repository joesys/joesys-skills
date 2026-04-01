# Model Defaults

Single source of truth for default model identifiers and CLI flags used across skills. When a model version changes, update this file — all skills that reference it will pick up the new defaults.

**Consumers:** codex, gemini, claude, ai-council, code-review, quick-review

---

## Model Identifiers

| Provider | Model ID | Used In |
|---|---|---|
| OpenAI (Codex CLI) | `gpt-5.4` | `/codex`, `/ai-council`, `/code-review`, `/quick-review` |
| Google (Gemini CLI) | `gemini-3.1-pro-preview` | `/gemini`, `/ai-council`, `/code-review`, `/quick-review` |
| Anthropic (Claude CLI) | `opus` | `/claude`, `/ai-council`, `/code-review`, `/quick-review` |

## Default CLI Command Templates

### Codex

```bash
codex exec --model gpt-5.4 -c model_reasoning_effort="xhigh" \
  --sandbox read-only --skip-git-repo-check 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `--model gpt-5.4` | Model selection |
| `-c model_reasoning_effort="xhigh"` | Maximum reasoning depth |
| `--sandbox read-only` | Safety: no file writes |
| `--skip-git-repo-check` | Required for piped input |
| `2>/dev/null` | Suppress progress/ANSI noise on stderr |

### Gemini

```bash
gemini -m gemini-3.1-pro-preview --approval-mode plan -p "" 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `-m gemini-3.1-pro-preview` | Model selection |
| `--approval-mode plan` | Safety: read-only |
| `-p ""` | Non-interactive mode (stdin provides the prompt) |
| `2>/dev/null` | Suppress progress/ANSI noise on stderr |

### Claude CLI

```bash
claude --model opus --effort high --permission-mode plan -p "" 2>/dev/null
```

| Flag | Purpose |
|---|---|
| `--model opus` | Model selection |
| `--effort high` | Reasoning effort level |
| `--permission-mode plan` | Safety: read-only |
| `-p ""` | Non-interactive mode (stdin provides the prompt) |
| `2>/dev/null` | Suppress progress/ANSI noise on stderr |

## Why `2>/dev/null`

CLI tools emit progress indicators, ANSI escape codes, and status messages on stderr. These are useful interactively but pollute captured output when running programmatically. Suppressing stderr keeps the response clean while stdout carries the actual model output.

## Standard Timeout

All CLI dispatches use **600000ms** (10 minutes) on the Bash tool. This accommodates long-running analysis tasks while preventing indefinite hangs.
