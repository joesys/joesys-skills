# Cross-Model Dispatch Protocol

How to send a prompt to a different AI model through its CLI. `/codereview` uses it to get an independent second opinion from a model outside the host. `/architect` uses it to get design candidates from other models. `/security-audit` calls other models too, but its runs take hours, so it has its own launcher with no time limit (`skills/security-audit/helpers/finder_runs.py`) and its own commands (`shared/model-defaults.md` § Security Audit Roles).

Current model identifiers and CLI command templates are in `shared/model-defaults.md`.

---

## Rules

- Run every cross-model dispatch in read-only or plan mode. Cross-model reviewers think; they never write.
- Write each prompt to a temp file and pipe it on stdin, with a 10-minute (600000 ms) Bash timeout. The pattern is in `shared/delegation-common.md` § Prompt Delivery. Delete the temp files afterwards.
- Run the dispatches in parallel with the host's own subagents, in a single response. Running them one after another loses the speedup.

---

## Host Detection

Choose the cross-model CLI based on which host you are:

| You Are | Dispatch To | Command |
|---|---|---|
| Claude | Both Codex + Antigravity | Two parallel dispatches |
| Codex | Antigravity | `python <ADAPTER> --mode plan --sandbox` (absolute path to `scripts/agy_adapter.py` under the plugin root — see `shared/model-defaults.md` § Antigravity) |
| Antigravity | Codex | `codex exec` |
| Unknown | Both Codex + Claude | Two parallel dispatches |

---

## Dispatch Commands

Replace `<CODEX_CMD>`, `<CLAUDE_CMD>`, and `<AGY_CMD>` with the current templates from `shared/model-defaults.md` (§ Codex, § Claude CLI, § Antigravity).

```bash
cat "$PROMPT_FILE" | <CODEX_CMD>
cat "$PROMPT_FILE" | <CLAUDE_CMD> --name "<review-name>"   # --name makes it resumable
cat "$PROMPT_FILE" | <AGY_CMD>
```

---

## Failure Handling

If a cross-model dispatch fails or times out, the review continues with the remaining sources. Add a note to the report:

- **One cross-model fails:** continue with the other one's results and note "Cross-model review from [model] unavailable ([reason])."
- **All cross-model dispatches fail:** continue with the host's subagents only, and note this in the report header.
