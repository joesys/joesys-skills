# Static Analysis Tooling Registry

**codebase-audit**, **codereview**, and **quick-review** use this file to find, classify, and safely run static analysis tools. Per-language profiles live in `shared/tooling/<language>.md`. This file is the protocol for all of them.

---

## 1. Safety Rules (Non-Negotiable)

1. **NEVER** run any tool without its report-only / dry-run / check-only flags.
2. **NEVER** install, update, upgrade, or remove any tool or dependency.
3. **NEVER** modify source files or configuration files. Caches and build output that a tool writes for itself (for example `.mypy_cache/`, `.ruff_cache/`, or Rust's `target/`) are fine. They are not source changes.
4. **ALWAYS** show tool commands in the **Live Command Safety Gate** before running them. The human must see and approve every command. **Exception:** quick-review runs read-only tools (linters, type checkers, SAST) without the gate, for speed. It still never runs tools marked `⚠️ DANGER: auto-modifies`.
5. Profiles mark tools that change files by default with `⚠️ DANGER: auto-modifies`. Double-check the report-only flags before queuing them.

---

## 2. Tool Tiers

| Tier | Category | What It Catches | Quality Criteria Served |
|------|----------|----------------|------------------------|
| **Tier 1** | Static Analyzers | Bugs, type errors, undefined behavior | Correctness, Maintainability |
| **Tier 2** | Linters | Code quality, style violations, common mistakes | Consistency, Readability, Maintainability |
| **Tier 3** | Formatters | Consistency checking (report-only) | Consistency |
| **Tier 4** | Security Scanners | Security pattern matching, known vulnerabilities | Security |

---

## 3. Detection Flow

### Step 1 — Load Tool Profiles

Read the per-language profile (`shared/tooling/<language>.md`) and the general profile (`shared/tooling/general.md`). Each profile lists tool names, config markers, binary names, and report-only flags.

### Step 2 — Detect Config Files

Glob the repository for each tool's config markers (for example `.eslintrc.*`, `pyproject.toml`, `rustfmt.toml`).

### Step 3 — Check Binary Availability

Check whether each tool's binary is on PATH.

### Step 4 — Classify Each Tool

| Config Present | Binary Available | Classification |
|:-:|:-:|:--|
| Yes | Yes | `available` |
| Yes | No  | `configured-but-unavailable` |
| No  | Yes | `available` (system-wide install) |
| No  | No  | `absent` |

Only `available` tools run. Report `configured-but-unavailable` tools as gaps. Skip `absent` tools silently unless the audit asks for gap recommendations.

### Step 5 — Detect Build-Integrated Analysis

Grep build files (`Makefile`, `package.json` scripts, `Cargo.toml`, CI configs) for analysis already in the build (`lint`, `check`, `analyze`, `clippy`, `mypy`). Record these as build-integrated tools. They inform grading but are not re-run.

### Step 6 — Queue Available Tools for Safety Gate

For each `available` tool, build the full command with report-only flags and show it in the **Live Command Safety Gate**. The human approves, rejects, or edits each command.

### Step 7 — Execute Approved Tools

Run each approved command, capture its output, and feed the results into the TOOLING_CONTEXT block.

---

## 4. Execution Protocol

### Timeouts

Use `testing.timeout` from `audit.yaml` (or equivalent) if set. Otherwise scale by repository size:

| Repository Size | Timeout Per Tool |
|:--|:--|
| < 10k LOC | 30 seconds |
| 10k – 100k LOC | 60 seconds |
| > 100k LOC | 120 seconds |

### Large Output Handling

When a tool reports **more than 50 findings**, do not paste them all. Give the count by severity (error / warning / style), the 3 most severe findings with file and line, and the exact command the user can run to see the full output.

### Tool Failure

If a tool crashes, times out, exits non-zero for a reason other than findings, or prints output you cannot parse: report it briefly (tool name, exit code, first line of stderr), skip it without retrying, and continue. A missing binary means `configured-but-unavailable` or `absent` (Step 4). A tool failure never fails the audit or review.

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

### Slim Version (codereview, quick-review)

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

The slim version omits **Gap Recommendations** and **Build-Integrated Analysis** — codereview is scoped to the diff, not the whole repository's tooling posture.

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

codereview and quick-review both use these rules when AI findings and tool findings cover the same diff. quick-review also drops findings below P1.

- **Same problem at the same place** (AI and tool): merge into one finding. Keep the AI's explanation, because it understands intent. Add `Confirmed by: {tool_name}` to show that two independent sources agree.
- **Tool-only finding:** include it with a `[{tool_name}]` prefix. Map its severity with `shared/review-common.md` § Tool Severity Mapping.
- **AI-only finding:** present it as is. Tools support the review; they do not gate it.
