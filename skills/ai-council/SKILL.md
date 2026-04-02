---
name: ai-council
version: "1.0.0"
description: "Use when the user invokes /ai-council to consult three frontier AI models (Claude, GPT, Gemini) in parallel and synthesize their responses into a consensus analysis"
---

# AI Council Skill

Dispatch the same question to three frontier AI models (Claude, GPT via Codex, Gemini) in parallel, then synthesize their responses into a structured analysis highlighting consensus and tensions.

## Terminology

- **Leg** — a dispatch+response unit (Claude leg, Codex leg, Gemini leg)
- **Council** — the collective of all three legs

## Invocation

Parse the user's `/ai-council` arguments:

- `--no-save` — opts out of writing output files (saving is **on** by default)
- `--path <dir>` — overrides the default save location (default: `docs/ai-council/`). Relative paths resolve from the current working directory.
- Remaining text is the question/prompt

If the question is empty or unintelligible, use `AskUserQuestion` to ask the user to clarify.

## Phase 0: Load User Preferences

Read `shared/skill-context.md` for the full protocol. In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. No skill-specific preferences file for ai-council — shared preferences are sufficient.

**How preferences shape this skill:**

| Preference | Effect on AI Council |
|---|---|
| Detail level | Controls how verbose the synthesis is |
| Assumed knowledge | Shapes the synthesis voice — beginner gets more explanation of model disagreements |
| Tone | Formal synthesis vs. conversational comparison |

Pass the user's communication style preferences to the synthesis phase (Phase 4). The individual model legs receive the user's raw question, not preferences — each model should respond naturally.

---

## Phase 1: Context Gathering

Automatically gather relevant context before dispatching. No user approval needed.

1. **Analyze the question** — determine what context would be useful:
   - Project-related question → read relevant files, git state
   - General technology question → WebSearch for recent info, benchmarks, comparisons (skip if WebSearch is unavailable)
   - Design decision → read existing architecture, dependencies, constraints
2. **Gather context** — run appropriate tools (Read, Grep, Glob, WebSearch where available)
3. **Assemble context bundle** — a single block that all three legs receive identically. If context is large, summarize rather than passing raw content.

If context gathering partially fails (e.g., a file is unreadable or WebSearch is unavailable), proceed with whatever context was successfully gathered.

## Phase 2: Prompt Construction

Construct the prompt in four parts:

### Part 1: Role Preamble (leg-specific)

> "You are the [Claude/GPT/Gemini] representative on a multi-model AI council. Give your independent analysis. Be explicit about your confidence level and reasoning. State your position clearly."

### Part 2: Context Bundle (identical across all three)

The gathered context from Phase 1.

### Part 3: Refined Question (identical across all three)

Reword the user's question into a clear, logical form with explicit framing (constraints, goals, scope). The refinement should clarify, not alter. Add explicit constraints and scope that are implied by context, but do not change the user's intent. When in doubt, use the original wording.

### Part 4: Original Prompt (identical, for reference)

> "Original question from the user: [verbatim user input]"

### Prompt Size Safety

Read `shared/delegation-common.md` § Prompt Delivery and `shared/model-defaults.md` for the standard prompt delivery pattern and current CLI command templates.

**Always** write prompts to temporary files using `mktemp` and pipe them to CLI tools. Use single-quoted heredoc delimiters to prevent shell expansion:

```bash
CODEX_PROMPT=$(mktemp /tmp/council-codex-XXXXXX.txt)
GEMINI_PROMPT=$(mktemp /tmp/council-gemini-XXXXXX.txt)
CLAUDE_PROMPT=$(mktemp /tmp/council-claude-XXXXXX.txt)

cat > "$CODEX_PROMPT" << 'PROMPT_EOF'
<prompt content>
PROMPT_EOF
# (repeat for each leg with leg-specific preamble)
```

Then pipe to each tool using the CLI templates from `shared/model-defaults.md`:
- **Codex:** `cat "$CODEX_PROMPT" | codex exec --model gpt-5.4 -c model_reasoning_effort="xhigh" --sandbox read-only --skip-git-repo-check 2>/dev/null`
- **Gemini:** `cat "$GEMINI_PROMPT" | gemini -m gemini-3.1-pro-preview --approval-mode plan -p "" 2>/dev/null`
- **Claude CLI:** `cat "$CLAUDE_PROMPT" | claude --model opus --effort high --permission-mode plan --name "council-<topic>" -p "" 2>/dev/null`

Clean up temporary files after all legs complete: `rm -f "$CODEX_PROMPT" "$GEMINI_PROMPT" "$CLAUDE_PROMPT"`

## Phase 3: Parallel Dispatch

Launch all three legs simultaneously in a single response (three parallel tool invocations).

### Codex Leg (Bash, 600000ms timeout)

**Always deliver the prompt via stdin pipe** (see Prompt Size Safety).

```bash
cat "$CODEX_PROMPT" | codex exec --model gpt-5.4 -c model_reasoning_effort="xhigh" \
  --sandbox read-only --skip-git-repo-check 2>/dev/null
```

### Gemini Leg (Bash, 600000ms timeout)

The `-p` flag is mandatory for non-interactive execution. Without it, Gemini enters interactive mode and hangs. **Always deliver the prompt via stdin pipe** — never pass long prompts as a direct `-p` argument (shell metacharacters break argument passing).

```bash
cat "$GEMINI_PROMPT" | gemini -m gemini-3.1-pro-preview --approval-mode plan -p "" 2>/dev/null
```

### Claude Leg (Heuristic)

Choose the mechanism based on whether the prompt is self-contained:

**Use subagent (Agent tool)** when Phase 1 fully resolved all context the question needs. The prompt is self-contained and the Claude leg won't need to read additional files or search the web during execution. Spawn with `model: "opus"` and pass the full four-part prompt. Subagent is faster — no CLI startup overhead.

**Use CLI** when the question references specific files or codepaths that Phase 1 could not fully resolve, and the Claude leg would benefit from tool access to explore further. When using CLI, include `--name` for resumability:

```bash
cat "$CLAUDE_PROMPT" | claude --model opus --effort high --permission-mode plan \
  --name "council-<topic>" -p "" 2>/dev/null
```

### Fallback Behavior

| Condition | Action |
|---|---|
| 1 leg fails | Proceed with 2/3 responses, note unavailable leg in synthesis, offer retry after presenting |
| 2 legs fail | Proceed with 1/3, warn user council is degraded, offer retry |
| All 3 legs fail | Report failures, suggest checking CLI installations and auth setup |

When the user accepts a retry and it succeeds, update the synthesis and output files to incorporate the new response.

## Phase 4: Synthesis

Produce a structured synthesis with five fixed sections:

### 1. Summary

2-3 sentence overview of what the council was asked and the overall direction of responses.

### 2. Confidence Matrix

A table showing each leg's confidence level per topic/dimension.

| Topic | Claude | GPT | Gemini |
|---|---|---|---|
| Dimension A | High | High | High |
| Dimension B | Medium | High | Not addressed |

- **Dimensions** are extracted from the responses — the common themes and aspects the legs addressed
- **Confidence** is inferred from hedging language and stated certainty on a 3-level scale: **High**, **Medium**, **Low**
- If a leg does not address a dimension, the cell reads **Not addressed**

### 3. Consensus Points

Where all responding legs agree — stated clearly with supporting reasoning.

### 4. Tensions & Disagreements

Where legs diverge — each leg's position stated fairly, with the nature of the disagreement explained (e.g., "Claude and GPT favor X for reason A, while Gemini argues Y due to reason B").

### 5. Synthesized Recommendation

The parent's own recommendation, informed by all three but not just majority-rules. Weigh the quality of reasoning, not just the count.

## Post-Synthesis Options

After presenting the synthesis, always offer:

1. **Resume individual sessions** — "Would you like to continue the conversation with any of the models? Use `/codex resume`, `/gemini resume`, or `/claude resume` to explore their reasoning further."
   - Resume is only available for legs that used CLI (not subagent). If the Claude leg used a subagent, note that `/claude resume` is not available for this council run.
   - For Codex, resume is only reliable immediately after the council run (before other Codex sessions are started).
2. **Retry failed legs** (if applicable) — "Would you like to retry [failed leg]? I can rerun it and update the synthesis."

If the user resumes and gets new insight, they can invoke `/ai-council` again with a refined question. The skill does not auto-update from individual resume sessions.

3. **Devlog suggestion** (if noteworthy) — If the synthesis revealed something genuinely interesting — a surprising disagreement between models, a non-obvious consensus, a tension that changed the developer's thinking, or a recommendation that contradicts conventional wisdom — suggest capturing it as a devlog scrap:
   > "This council session surfaced [brief description of the noteworthy finding]. That might make a good devlog post. Want me to run `/devlog scrap --from-context` to capture it?"
   - Only suggest when the findings are genuinely insightful — not for routine confirmations or questions with obvious answers
   - Wait for the user's response. Do not auto-run.

## Phase 5: File Output

Saving is **on** by default. Files are written to `docs/ai-council/YYYYMMDD-<topic>/`:

```
docs/ai-council/20260325-postgresql-vs-mongodb/
├── claude.md
├── codex.md
├── gemini.md
└── synthesis.md
```

- `<topic>` is derived from the question (kebab-case, 3-5 words)
- Each individual file contains the leg's raw response with a header noting the model name, timestamp, and the prompt it received
- `synthesis.md` contains the full synthesis (all 5 sections from Phase 4)
- If a leg was unavailable, its file is not created
- If the user retries a failed leg and it succeeds, the new response file is written and `synthesis.md` is updated
- If the output directory already exists (same-day re-run on same topic), append a numeric suffix: `YYYYMMDD-<topic>-2/`, `YYYYMMDD-<topic>-3/`, etc.
- `--no-save` skips all file writing
- `--path <dir>` overrides `docs/ai-council/` (the `YYYYMMDD-<topic>/` subdirectory is still created inside)

## Error Handling

| Phase | Condition | Action |
|---|---|---|
| Phase 1 | WebSearch unavailable | Skip web context, proceed with file/project context only |
| Phase 1 | File read/glob fails | Proceed with whatever context was gathered |
| Phase 2 | Empty or unintelligible question | Use `AskUserQuestion` to ask the user to clarify |
| Phase 3 | Leg failure/timeout | See Fallback Behavior above |
| Phase 5 | Directory already exists | Append numeric suffix |
| Phase 5 | Disk write error | Warn user, present synthesis in terminal only |
