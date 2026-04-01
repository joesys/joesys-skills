# Static Analysis Tooling Registry

**codebase-audit**, **code-review**, and **quick-review** all reference this file as the single source of truth for discovering, classifying, and safely executing static analysis tools. Per-language tool profiles live in `shared/tooling/<language>.md`; this file defines the shared protocol that governs all of them.

---

## 1. Safety Rules (Non-Negotiable)

These rules are absolute and apply to every tool, every language, every run.

1. **NEVER** run any tool without its report-only / dry-run / check-only flags.
2. **NEVER** install, update, upgrade, or remove any tool or dependency.
3. **NEVER** modify source files, configuration files, or the working tree.
4. **ALWAYS** present tool commands in the **Live Command Safety Gate** before execution — the human must see and approve every command. **Exception:** quick-review auto-runs read-only tools (linters, type checkers, SAST) without a safety gate for speed. It still skips tools marked `⚠️ DANGER: auto-modifies`. This exception is intentional — quick-review trades the gate for faster turnaround on tools that cannot modify files.
5. Tools that auto-modify by default are marked with `⚠️ DANGER: auto-modifies` in per-language profile files — **double-check report-only flags** before queuing these tools.

---

## 2. Tool Tiers

| Tier | Category | What It Catches | Quality Criteria Served |
|------|----------|----------------|------------------------|
| **Tier 1** | Static Analyzers | Bugs, type errors, undefined behavior | Correctness, Maintainability |
| **Tier 2** | Linters | Code quality, style violations, common mistakes | Consistency, Readability, Maintainability |
| **Tier 3** | Formatters | Consistency checking (report-only) | Consistency |
| **Tier 4** | Security Scanners | Security pattern matching, known vulnerabilities | Security |

Tools are executed in tier order. Higher tiers (lower numbers) take precedence when findings overlap.

---

## 3. Detection Flow

The orchestrator follows this 7-step protocol to discover and classify tools before any execution occurs.

### Step 1 — Load Tool Profiles

Read the per-language profile (`shared/tooling/<language>.md`) and the general profile (`shared/tooling/general.md`) to build the candidate tool list. Each profile declares tool names, config file markers, binary names, and report-only flags.

### Step 2 — Detect Config Files

Glob the repository for each tool's known config file markers (e.g., `.eslintrc.*`, `pyproject.toml`, `rustfmt.toml`). Record which tools have project-level configuration present.

### Step 3 — Check Binary Availability

For each candidate tool, run `which <binary>` (Unix) or `where <binary>` (Windows) to determine whether the binary is available on the system PATH.

### Step 4 — Classify Each Tool

Apply this 4-state classification model:

| Config Present | Binary Available | Classification |
|:-:|:-:|:--|
| Yes | Yes | `available` |
| Yes | No  | `configured-but-unavailable` |
| No  | Yes | `available` (system-wide install) |
| No  | No  | `absent` |

Only `available` tools proceed to execution. `configured-but-unavailable` tools are reported as gaps. `absent` tools are silently skipped unless the audit requests gap recommendations.

### Step 5 — Detect Build-Integrated Analysis

Grep build files (e.g., `Makefile`, `package.json` scripts, `Cargo.toml`, CI configs) for patterns that indicate static analysis is already integrated into the build pipeline (e.g., `lint`, `check`, `analyze`, `clippy`, `mypy`). Record these as build-integrated tools — they inform grading but are not re-executed.

### Step 6 — Queue Available Tools for Safety Gate

For each `available` tool, assemble the full command with report-only flags and present it in the **Live Command Safety Gate**. The human approves, rejects, or modifies each command before execution.

### Step 7 — Execute Approved Tools

Run each approved command, capture stdout/stderr, and feed results into the TOOLING_CONTEXT block.

---

## 4. Execution Protocol

### Timeouts

- If the audit/review configuration (`audit.yaml` or equivalent) specifies `testing.timeout`, respect that value.
- Otherwise, apply adaptive timeouts based on repository size:

| Repository Size | Timeout Per Tool |
|:--|:--|
| < 10k LOC | 30 seconds |
| 10k – 100k LOC | 60 seconds |
| > 100k LOC | 120 seconds |

### Large Output Handling

When a tool produces **more than 50 findings**:

1. **Summarize**: total count by severity (error / warning / style).
2. **Highlight**: the top 3 most severe findings with file, line, and explanation.
3. **Tell the user**: the exact command they can run themselves to see the full output.

Do not dump 50+ findings into the report — it overwhelms the signal.

### Tool Failure

If a tool errors out (non-zero exit unrelated to findings, crash, timeout):

1. **Report** the error concisely (tool name, exit code, first line of stderr).
2. **Skip** the tool — do not retry.
3. **Do not fail** the audit or review because of a tool failure. Continue with remaining tools.

---

## 5. TOOLING_CONTEXT Block

The TOOLING_CONTEXT block is the structured output that feeds into the audit or review report. Two versions exist depending on the consumer.

### Full Version (codebase-audit)

```
### TOOLING_CONTEXT

#### Tools Detected
| Tool | Tier | Classification | Findings |
|------|------|----------------|----------|
| ...  | ...  | ...            | ...      |

#### Top Findings
**{tool_name}**
- [{severity}] {file}:{line} — {message}
- ...

**{tool_name}**
- ...

#### Build-Integrated Analysis
- {tool_or_script}: detected in {location} ({description})
- ...

#### Gap Recommendations
- {language} projects typically use {tool} for {purpose} — not detected in this repo
- ...
```

### Slim Version (code-review, quick-review)

```
### TOOLING_CONTEXT

#### Tools Detected
| Tool | Tier | Classification | Findings |
|------|------|----------------|----------|
| ...  | ...  | ...            | ...      |

#### Top Findings
**{tool_name}**
- [{severity}] {file}:{line} — {message}
- ...
```

The slim version omits **Gap Recommendations** and **Build-Integrated Analysis** — code-review is scoped to the diff, not the whole repository's tooling posture.

---

## 6. Grading Guidance (codebase-audit only)

Tooling results influence the audit grade through two mechanisms: criteria impact and classification impact.

### Criteria Impact

| Criterion | Positive Signal | Negative Signal |
|:--|:--|:--|
| **Security** | Security scanner runs clean | Security scanner finds vulnerabilities; no scanner available |
| **Consistency** | Formatter check passes; linter style rules clean | Formatter deviations; inconsistent style findings |
| **Operability** | Build-integrated analysis present in CI | No automated checks in build pipeline |
| **Maintainability** | Static analyzer clean; linter clean | High count of analyzer warnings; ignored lint rules |
| **Correctness** | Type checker / static analyzer finds zero bugs | Type errors, undefined behavior, null-safety violations |

### Classification Impact

| Classification | Grading Effect |
|:--|:--|
| `available` + clean (0 findings) | Positive signal — tools are present and passing |
| `available` + findings | Neutral to negative — tools exist but surface issues; severity matters |
| `configured-but-unavailable` | Minor negative — intent to use tooling exists but execution is broken |
| `absent` | Negative for criteria the tool would serve — no automated quality gate |
| Build-integrated | Positive for Operability — analysis is part of the development workflow |

---

## 7. Review Merge Rules

When both AI analysis and tool output identify issues in the same diff, apply these merge rules. Both code-review and quick-review use these rules, with quick-review applying a wider ±5 line tolerance for deduplication (because cross-model reviewers working from diff-only context may report slightly different line numbers) and discarding findings below P2.

### Overlapping Findings (same file, within 3 lines)

When the AI reviewer and a tool flag the same (or nearly the same) issue:

- **Merge** into a single finding.
- **Keep** the AI's explanation (richer context, understands intent).
- **Add** a `Confirmed by: {tool_name}` annotation to increase confidence.

### Tool-Only Findings

When a tool finds something the AI did not flag:

- **Include** the finding with a `[{tool_name}]` prefix.
- **Map severity** to the review's priority scale:

| Tool Severity | Review Priority |
|:--|:--|
| error | **P1** (or **P0** if security-related) |
| warning | **P2** |
| style / info | **P3** |

### AI-Only Findings

When the AI flags something no tool detected:

- **No change** — present the finding as-is. AI analysis stands on its own; tools are supplementary, not gatekeepers.
