---
name: codebase-audit
description: "Use when the user invokes /codebase-audit to run a language-agnostic codebase quality audit measuring up to 11 quality criteria + development velocity with industry benchmarks, grading, and actionable recommendations."
---

# Codebase Audit Skill

Run a comprehensive, language-agnostic codebase quality audit. Measures up to 11 core quality criteria + development velocity across 6 parallel collection agents, displays graded metrics on console, and optionally writes a full analysis report with industry benchmarks and actionable recommendations.

## Invocation

Parse the user's `/codebase-audit` arguments:

| Invocation | Mode |
|---|---|
| `/codebase-audit` | Full pipeline (all 11 criteria + velocity) |
| `/codebase-audit metrics` | Collect + display only, write metrics.json + metrics.md |
| `/codebase-audit analysis` | Re-analyze from most recent metrics.json |
| `/codebase-audit delta` | Compare two most recent audits |
| `/codebase-audit maintainability performance` | Only specified criteria |
| `/codebase-audit velocity` | Just development velocity |
| `/codebase-audit --static-only` | No live commands (no test run, no dep audit) |

### Parsing Rules

- **Reserved phase words:** `metrics`, `analysis`, `delta`
- **Everything else:** Treated as criterion names, validated against the 12 valid names
- **Flags:** `--static-only` — skip all live commands
- **Invalid names:** Print error listing valid options, stop

### Valid Criterion Names

| Argument | Criterion | Category |
|---|---|---|
| `maintainability` | 1. Maintainability | Core |
| `evolvability` | 2. Evolvability | Core |
| `correctness` | 3. Correctness | Core |
| `testability` | 4. Testability | Core |
| `reliability` | 5. Reliability | Core |
| `performance` | 6. Performance | Core |
| `readability` | 7. Readability | Core |
| `modularity` | 8. Modularity | Core |
| `consistency` | 9. Consistency | Core |
| `operability` | 10. Operability | Core |
| `security` | 11. Security | Core |
| `velocity` | 12. Development Velocity | Extended |

---

## Phase 0 — Parse, Detect & Route

### Step 1: Parse Arguments

Parse invocation arguments per the rules above. Determine invocation mode: `full`, `metrics`, `analysis`, `delta`, or `scoped` (specific criteria).

### Step 2: Load Config

Read `.claude/audit.yaml` (or `.yml`) from project root. All fields are optional — auto-detected defaults fill gaps.

```yaml
# .claude/audit.yaml — all fields optional
project:
  name: "My Project"           # auto: from package.json, Cargo.toml, etc.
  engine: "Godot 4.6"          # auto: from project.godot, or omitted

paths:
  source:                      # auto: detected from project structure
    - "src/"
  tests:
    - "tests/"
  exclude:                     # globs to skip in all measurements
    - "vendor/"
    - "node_modules/"

language:
  primary: "python"            # auto: from dominant file extension
  additional: ["typescript"]   # auto: if >10% of source files
  extension: ".py"
  function_pattern: "^(def|async def) "
  class_pattern: "^class "

testing:
  runner: "pytest --tb=short"
  timeout: 60000

architecture:
  boundaries: []               # {name, pattern, path, expected} rules

criteria_priority: []          # pin top N criteria priorities
```

### Step 3: Auto-Detect Language

Check marker files in priority order:

| Marker | Language |
|---|---|
| `project.godot` | GDScript |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `*.sln` or `*.csproj` | C# |
| `CMakeLists.txt` + `.cpp`/`.cc`/`.h` files | C++ |
| `pyproject.toml` / `setup.py` / `requirements.txt` | Python |
| `package.json` (with `.ts` files) | TypeScript |
| `package.json` (without `.ts` files) | JavaScript |
| Fallback | Count file extensions, pick dominant |

### Step 4: Language Defaults

Apply per-language defaults for patterns, test runner, and file extension. These are overridden by config values where specified.

| Language | Extension | Test Runner | Function Pattern |
|---|---|---|---|
| Python | .py | pytest | `^(def\|async def) ` |
| TypeScript | .ts | jest/vitest | `^(export )?(async )?function` |
| JavaScript | .js | jest/vitest | `^(export )?(async )?function` |
| Rust | .rs | cargo test | `^(pub )?(async )?fn ` |
| Go | .go | go test ./... | `^func ` |
| C++ | .cpp | ctest/gtest | `^\w+.*\w+\s*\(` |
| C# | .cs | dotnet test | `(public\|private).*\w+\(` |
| GDScript | .gd | gdUnit4 | `^(static )?func ` |

### Step 5: Auto-Detect Paths

- **Source:** Check for `src/`, `lib/`, `app/` (use all found; project root if none). For monorepos: `packages/*/src/`, `backend/`, `frontend/`, `services/*/`.
- **Tests:** Check for `tests/`, `test/`, `__tests__/`, `spec/` (including within source roots).
- **Auto-excluded:** `vendor/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.git/`, `.gitignore` entries. Config exclusions extend these.

### Step 6: Polyglot Detection

Count file extensions across detected source paths. Any secondary language >10% of source files → add to `language.additional`.

For polyglot repos: helper scripts run once per language, benchmarks loaded for each language, metrics grouped by language where they differ.

### Step 7: Auto-Detect Test Runner

1. Check framework config: `pytest.ini`, `jest.config.*`, `vitest.config.*`, `.mocharc.*`, `phpunit.xml`
2. Check `package.json` → `scripts.test`
3. Fall back to language default
4. If ambiguous, ask user

### Step 8: Domain Inference

1. Read `README.md`, `package.json` description, `pyproject.toml` description
2. Scan key imports (e.g., `django` → web app, `numpy` → ML, `fastapi` → API service)
3. Check directory names (`models/`, `routes/`, `scenes/`, `strategies/`)
4. Synthesize domain summary: e.g., "Django REST API for e-commerce"
5. Use WebSearch for comparable projects and benchmarks (if available)

### Step 9: Prerequisites Check

Verify Python 3 is available:

```bash
python3 --version || python --version
```

If not available, warn:

> Python 3 is required for deterministic metrics (complexity, structure, churn analysis). Without it, the audit will use qualitative-only analysis. Proceed? (y/n)

### Step 10: Scope Size Check

Count source files. If >1000 files, warn:

> This project has ~{N} source files. A full audit may take several minutes. Proceed? (y/n)

### Step 11: Merge Config

`auto-detected defaults ← config overrides` — config always wins where specified.

### Output of Phase 0

A **project context block** (structured text) passed to all agents:

```
Language: {primary} (+{additional})
Source paths: {paths}
Test paths: {paths}
Exclude: {patterns}
Test runner: {runner}
Domain: {summary}
Engine: {if detected}
```

---

## Phase 1 — Parallel Collection

Spawn **6 measurement agents in parallel** via the Agent tool — all 6 in a single response. Each uses `model: "opus"`.

**For scoped invocations,** launch only the agents required by the requested criteria:

| Criterion | Required Agents |
|---|---|
| Maintainability | Structural, Quality |
| Evolvability | Structural, Architecture |
| Correctness | Tests, Structural |
| Testability | Tests, Structural, Architecture |
| Reliability | Architecture, Structural |
| Performance | Performance, Architecture |
| Readability | Structural, Quality |
| Modularity | Architecture |
| Consistency | Quality, Architecture |
| Operability | Architecture, Structural |
| Security | Architecture, Quality |
| Velocity | Git/Velocity |

### Live Command Safety Gate

Before dispatching agents, identify all live commands that will run and present them:

> **The following live commands will be executed during collection:**
> - `{test_runner}` (Tests agent — runs test suite)
> - `{audit_command}` (Architecture agent — checks dependencies)
>
> Options:
> 1. **Run all** — execute all listed commands
> 2. **Static only** — skip live commands, static analysis only
> 3. **Select** — choose which to allow

Commands NOT requiring the gate (read-only): helper scripts, `git log`, `git diff`, Glob/Grep/Read.

If `--static-only` was passed, skip the gate entirely.

### Agent 1: Structural

~~~
You are a structural metrics analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Principles
Read the following principle files before analysis:
- `skills/codebase-audit/principles/maintainability.md`
- `skills/codebase-audit/principles/readability.md`

## Benchmarks
Read the relevant benchmark file(s) from `skills/codebase-audit/benchmarks/`:
- `{language}.md` (language-specific)
- `general.md` (cross-language fallback)

## Your Task

1. Run the structure helper script:
```bash
python skills/codebase-audit/helpers/compute_structure.py --lang {language} --source {source_paths} --exclude {exclude_patterns}
```

2. Parse the JSON output and supplement with qualitative observations from reading the code.

3. For polyglot repos, run the helper once per language.

## Metrics to Collect

- LOC (total, per-file, per-function distributions)
- File length distribution (max, median, p90)
- Function length distribution (max, median, p90)
- Nesting depth (max, median, p90)
- Comment density (comment_lines / total_lines)
- Type annotation coverage
- Files over 500 lines (list them)
- Functions over 50 lines (list them)

## Output Format

Return JSON matching this structure:
```json
{
  "agent": "structural",
  "status": "success",
  "metrics": {
    "total_files": 0,
    "total_loc": 0,
    "blank_lines": 0,
    "comment_lines": 0,
    "comment_density": 0.0,
    "file_lengths": {"max": 0, "median": 0, "p90": 0},
    "function_lengths": {"max": 0, "median": 0, "p90": 0},
    "nesting_depth": {"max": 0, "median": 0, "p90": 0},
    "type_annotation_coverage": 0.0,
    "files_over_500_lines": [],
    "functions_over_50_lines": []
  },
  "by_language": {
    "python": {"total_files": 0, "total_loc": 0, "comment_density": 0.0, "type_annotation_coverage": 0.0},
    "typescript": {"total_files": 0, "total_loc": 0, "comment_density": 0.0, "type_annotation_coverage": 0.0}
  },
  "qualitative_notes": "Free text observations"
}
```

The `by_language` field is only present for polyglot repos (where `language.additional` is non-empty). For single-language repos, omit it. Each key is a language name, and the value contains per-language breakdowns of metrics that differ significantly by language.
```
~~~

### Agent 2: Quality

~~~
You are a code quality analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Principles
Read these principle files before analysis:
- `skills/codebase-audit/principles/maintainability.md`
- `skills/codebase-audit/principles/readability.md`
- `skills/codebase-audit/principles/consistency.md`

## Benchmarks
Read: `skills/codebase-audit/benchmarks/{language}.md` and `skills/codebase-audit/benchmarks/general.md`

## Your Task

1. Run the complexity helper:
```bash
python skills/codebase-audit/helpers/compute_complexity.py --lang {language} --source {source_paths} --exclude {exclude_patterns}
```

2. Parse complexity JSON and supplement with qualitative analysis by reading code via Grep and Read.

## Metrics to Collect

- Cyclomatic complexity (avg, max, distribution) — from helper
- Naming convention violations — scan files for inconsistent casing
- Magic number density — grep for numeric literals outside constants
- Code duplication signals — look for 3+ repeated patterns of 5+ lines
- TODO/FIXME/HACK counts grouped by theme
- Commented-out code blocks
- Unused imports/exports
- Hardcoded secrets (API keys, passwords, tokens in source)
- Sensitive data in logs

## Output Format

Return JSON:
```json
{
  "agent": "quality",
  "status": "success",
  "metrics": {
    "cyclomatic_complexity": {
      "average": 0.0,
      "by_language": {"python": 7.1, "typescript": 9.8},
      "max": {"function": "", "file": "", "line": 0, "complexity": 0},
      "distribution": {"1-5": 0, "6-10": 0, "11-15": 0, "16-20": 0, "21+": 0}
    },
    "naming_violations": 0,
    "magic_numbers": 0,
    "duplication_signals": [],
    "todo_fixme_hack_count": 0,
    "todo_themes": [],
    "commented_out_blocks": 0,
    "hardcoded_secrets": [],
    "sensitive_data_in_logs": []
  },
  "qualitative_notes": ""
}
```
~~~

### Agent 3: Architecture

~~~
You are an architecture analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Principles
Read these principle files:
- `skills/codebase-audit/principles/evolvability.md`
- `skills/codebase-audit/principles/modularity.md`
- `skills/codebase-audit/principles/reliability.md`
- `skills/codebase-audit/principles/operability.md`
- `skills/codebase-audit/principles/security.md`

## Benchmarks
Read: `skills/codebase-audit/benchmarks/{language}.md` and `skills/codebase-audit/benchmarks/general.md`

## Your Task

Analyze the codebase architecture by reading imports, tracing dependencies, and checking infrastructure config. Use Grep and Read extensively.

{IF_LIVE_COMMANDS_APPROVED}
Run dependency audit if applicable:
- Python: `pip-audit` or `safety check`
- JavaScript/TypeScript: `npm audit --json`
- Rust: `cargo audit --json`
- Go: `govulncheck ./...`
- C#: `dotnet list package --vulnerable`
{END_IF}

## Metrics to Collect

- Module coupling: fan-in/fan-out per module
- Circular dependency detection
- Boundary violations (per config or inferred)
- Import graph analysis
- Separation of concerns assessment
- CI/CD presence and configuration
- Container config (Dockerfile, docker-compose)
- Health check endpoints
- Dependency health (lock file, audit results, outdated/vulnerable count)
- Environment config handling
- Logging patterns

## Output Format

Return JSON:
```json
{
  "agent": "architecture",
  "status": "success",
  "metrics": {
    "fan_out_avg": 0.0,
    "fan_out_max": {"module": "", "fan_out": 0},
    "circular_dependencies": [],
    "boundary_violations": [],
    "ci_cd_present": false,
    "ci_cd_config": "",
    "container_config": false,
    "health_checks": false,
    "lock_file_present": false,
    "dependency_vulnerabilities": {"high": 0, "medium": 0, "low": 0},
    "logging_present": false,
    "env_config_handling": ""
  },
  "qualitative_notes": ""
}
```
~~~

### Agent 4: Git/Velocity

~~~
You are a git history and development velocity analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Your Task

1. Run the churn helper:
```bash
python skills/codebase-audit/helpers/compute_churn.py --source {source_paths} --exclude {exclude_patterns}
```

2. Supplement with `git log` analysis for velocity trends and contributor patterns.

3. If a previous `metrics.json` exists at `docs/reports/codebase-audit/*/metrics.json`, read the most recent one for delta comparison.

## Metrics to Collect

- Code churn (30-day): lines added, deleted, net change, files changed
- Most-churned files (top 10)
- Commit frequency (total commits in 30 days)
- Contributor activity (unique contributors, commits per contributor)
- Knowledge concentration / bus factor: per-module, identify files with single contributor
- Commit size distribution (small/medium/large)
- Previous audit data (if metrics.json exists)

## Output Format

Return JSON:
```json
{
  "agent": "git_velocity",
  "status": "success",
  "metrics": {
    "churn": {
      "files_changed": 0,
      "lines_added": 0,
      "lines_deleted": 0,
      "net_change": 0,
      "most_churned_files": []
    },
    "commit_frequency_30d": 0,
    "contributors": [],
    "knowledge_concentration": [
      {"module": "src/example/", "primary_contributor": "alice", "commit_pct": 94, "bus_factor_risk": "high"}
    ],
    "commit_size_distribution": {"small": 0, "medium": 0, "large": 0}
  },
  "previous_audit": null,
  "qualitative_notes": ""
}
```

Each `knowledge_concentration` entry must have: `module` (path), `primary_contributor` (git author), `commit_pct` (percentage of commits by that author), `bus_factor_risk` ("high" if one person >80%, "medium" if >60%, "low" otherwise). Compute via `git shortlog -sn -- {module}`.
~~~

### Agent 5: Performance

~~~
You are a performance analyst for a codebase audit (static analysis only).

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Principles
Read: `skills/codebase-audit/principles/performance.md`

## Benchmarks
Read: `skills/codebase-audit/benchmarks/{language}.md` and `skills/codebase-audit/benchmarks/general.md`

## Your Task

Analyze the codebase for performance anti-patterns using Grep and Read. This is static analysis only — no profiling or benchmarking.

## Patterns to Detect

- Algorithm complexity issues (nested loops for lookup where set/dict would work)
- N+1 query patterns (DB queries inside loops)
- Blocking I/O in async contexts (sync calls in async functions)
- String concatenation in loops (quadratic allocation)
- Missing caching for repeated expensive operations
- Memory leak patterns (unbounded collections, unclosed resources)
- Lazy vs eager loading issues

## Output Format

Return JSON:
```json
{
  "agent": "performance",
  "status": "success",
  "metrics": {
    "algorithm_complexity_issues": [],
    "n_plus_1_patterns": [],
    "blocking_io_in_async": [],
    "string_concat_in_loops": [],
    "missing_caching": [],
    "memory_leak_patterns": [],
    "eager_loading_issues": []
  },
  "qualitative_notes": ""
}
```

Each issue entry: `{"file": "", "line": 0, "description": "", "severity": "high|medium|low"}`
~~~

### Agent 6: Tests

~~~
You are a test suite analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Principles
Read these principle files:
- `skills/codebase-audit/principles/testability.md`
- `skills/codebase-audit/principles/correctness.md`

## Benchmarks
Read: `skills/codebase-audit/benchmarks/{language}.md` and `skills/codebase-audit/benchmarks/general.md`

## Your Task

{IF_TEST_RUNNER_APPROVED}
1. Run the test suite with a timeout:
```bash
{test_runner}
```
Capture: pass count, fail count, execution time, failure details.
{END_IF}

2. Static analysis of test quality: read test files via Glob and Read.

## Metrics to Collect

- Test pass rate (if tests were run)
- Test execution time (if tests were run)
- Test failure details (if any)
- Test file count vs source file count ratio
- Test type distribution (unit / integration / e2e)
- Assertion density (assertions per test function)
- Test quality signals:
  - Testing behavior vs implementation details
  - Meaningful assertions vs smoke tests
  - Edge case coverage
  - Mock/stub usage patterns
- Coverage signals (if coverage report available)

## Output Format

Return JSON:
```json
{
  "agent": "tests",
  "status": "success",
  "metrics": {
    "test_pass_rate": null,
    "test_count": 0,
    "test_failures": [],
    "test_execution_time_ms": null,
    "test_file_count": 0,
    "source_file_count": 0,
    "test_to_source_ratio": 0.0,
    "test_type_distribution": {"unit": 0, "integration": 0, "e2e": 0},
    "assertion_density": 0.0,
    "test_runner_detected": "",
    "test_runner_status": "ran|skipped|not_found"
  },
  "qualitative_notes": ""
}
```
~~~

### Failure Handling

- **Agent timeout:** 60s default. If an agent times out, proceed with available data. Note the missing agent in output.
- **Partial failure:** Audit continues with successful agents. Missing data noted in display.
- **Helper script failure:** Agent falls back to qualitative-only. Metrics marked "Not measured."
- **No test runner:** Tests agent does static analysis only.
- **Live commands declined:** Agents fall back to static analysis. Metrics marked "Skipped (live commands declined)."

---

## Phase 2 — Display & Gate

### Step 1: Assemble Results

Collect structured JSON from each agent. For each criterion, compute a grade using the principle file rubric + benchmark data.

**Audit Confidence Model:**

Each criterion gets a confidence level:
- **high** — deterministic measurements from helpers + live commands
- **medium** — partial measurement (helper ran but live commands skipped)
- **low** — qualitative-only (helper failed or Python not available)

Overall audit confidence = lowest confidence among all measured criteria.

Display: append `~` to grades with low confidence (e.g., "B~" = approximate).

### Step 2: Risk Heat Map

Cross-reference complexity data (Quality agent) with churn data (Git/Velocity agent):

```
              High Churn
                  │
   ┌──────────────┼──────────────┐
   │  Refactor    │  Danger Zone │
   │  candidates  │  (act now)   │
   │              │              │
───┼──────────────┼──────────────┼─── High Complexity
   │              │              │
   │  Stable      │  Monitor     │
   │  (leave it)  │  (watch)     │
   │              │              │
   └──────────────┼──────────────┘
              Low Churn
```

"Danger Zone" files (high complexity + high churn) are named explicitly.

### Grading Scale

| Grade | Meaning |
|---|---|
| A+ | Exceeds industry best practice |
| A | Meets best practice |
| B | Acceptable, minor improvements possible |
| C | Below average, attention needed |
| D | Significant issues, action required |
| F | Critical deficiencies |

Grading is relative to resolved benchmarks (language-specific → general fallback).

In metrics-only mode, all criteria get equal weight. In full mode, preliminary equal-weight grades are computed for console display; the author may adjust in Phase 4.

### Step 3: Console Display

Print a summary table directly in the conversation:

```
╔══════════════════════════════════════════════════════════════╗
║  CODEBASE AUDIT — {Project Name}                           ║
║  {Domain Summary} · {Language} · {Date}                    ║
╠══════════════════════════════════════════════════════════════╣
║  Overall Grade: {GRADE} (confidence: {CONFIDENCE})         ║
╠══════════════════════════════════════════════════════════════╣
║  #  Criterion        Grade  Key Metric         Benchmark   ║
║  ── ──────────────── ────── ────────────────── ─────────── ║
║   1 Maintainability    B    CC avg: 8.2        ≤ 10        ║
║   2 Evolvability       B+   Fan-out avg: 3.1   ≤ 5         ║
║  ...                                                       ║
║  ── ──────────────── ────── ────────────────── ─────────── ║
║  12 Velocity           —    +2.1k lines/30d    —           ║
╠══════════════════════════════════════════════════════════════╣
║  Top Risk: {criterion} ({grade}) — {reason}                ║
║  Top Strength: {criterion} ({grade}) — {reason}            ║
║  Danger Zone: {file} (CC:{N}, {N} changes)                 ║
╚══════════════════════════════════════════════════════════════╝
```

Dynamically generated — only measured criteria appear. Failed/skipped agents show "—" with a note.

### Step 4: Gate

After displaying the table:

> **Metrics collected.** What would you like to do?
> 1. **Write both** — metrics.json + metrics.md + full analysis with benchmarks and recommendations
> 2. **Metrics only** — write metrics.json + metrics.md (numbers, no commentary)
> 3. **Done** — just the console display, no files

**Routing rules:**
- `/codebase-audit metrics` → skip gate, write metrics.json + metrics.md directly (no user context needed)
- `/codebase-audit analysis` → skip Phase 1, load most recent metrics.json, proceed to Phase 3
- User selects option 1 → proceed to Phase 3
- User selects option 2 → skip to Phase 5 (write metrics only, rank/weight = null)
- User selects option 3 → stop

---

## Phase 3 — User Context Interview

Gathers context the code alone can't reveal. Sits between collection and analysis.

### First Audit — Build the Profile

Ask 3-5 questions maximum:

1. **Project phase:** "What phase is this project in?"
   - Prototype / MVP / Active growth / Mature / Maintenance

2. **Team size:** "How many developers actively work on this?"
   - Solo / 2-5 / 6-15 / 16+

3. **Deployment cadence:** "How often do you deploy/release?"
   - Continuous / Weekly / Monthly / Release-based / Not yet deploying

4. **Business priority:** "What matters most right now?"
   - Speed to market / Reliability / Compliance / Cost reduction / Feature completeness

5. **Known trade-offs:** "Anything you'd like the audit to know? For example: intentional tech debt, upcoming migrations, constraints."
   - Free text

Also ask **informed questions** based on Phase 1 findings. For example, if the Tests agent found zero tests:

> "I noticed there are no tests. Is this intentional for now (prototype phase), or is it a gap you want highlighted?"

### Returning Audits — Confirm the Profile

Check for existing profile at `docs/reports/codebase-audit/project-context.md`. If found, read it and ask:

> "I found your project profile from the last audit ({DATE}). Here's what I have:
> - Phase: {PHASE} | Team: {TEAM} | Priority: {PRIORITY}
> - Known trade-off: {TRADE_OFF}
>
> Still accurate, or has anything changed?"

User confirms or updates. Quick on repeat audits.

### How User Context Shapes the Analysis

| User Context | Analysis Effect |
|---|---|
| Solo + Prototype | Lighter on process (CI/CD), heavier on "what to invest in first" |
| Team of 10 + Mature | Heavier on consistency, modularity, onboarding friction |
| "Speed to market" priority | Recommendations framed as "do this now" vs. "do this before scaling" |
| "Low test coverage intentional" | Testability acknowledges trade-off rather than flagging as surprise |
| "Migrating to Postgres soon" | Operability factors in upcoming migration |

---

## Phase 4 — Analysis Writing

A single author agent writes the full analysis in one pass. Uses `model: "opus"`.

### Dynamic Author Persona

Composed from Phase 0 detection:

> "You are a senior {language} engineer with deep knowledge of {language} idioms, ecosystem tooling, and community standards. You have extensive experience building {domain} systems and understand the specific quality trade-offs, failure modes, and performance characteristics of this domain."

### Dynamic Criteria Weighting

The author assigns a **priority rank** (1-11) and **weight** (High/Medium/Low) to each criterion based on language + domain expertise. This affects:

1. **Priority order** — criteria sections sorted by priority, not fixed 1-11
2. **Overall grade** — higher-weighted criteria influence overall grade more
3. **Analysis depth** — top 3-4 get deeper analysis
4. **Recommended actions** — higher-priority criteria surfaced first

Users can override via `criteria_priority` in `audit.yaml`.

### Author Agent Prompt

~~~
{DYNAMIC_AUTHOR_PERSONA}

You are writing a comprehensive codebase quality audit report.

## Inputs

1. **Metrics JSON** — all measured values from Phase 1 collection agents:
{ASSEMBLED_METRICS_JSON}

2. **Project Context:**
{PROJECT_CONTEXT_BLOCK}

3. **User Context:**
{USER_CONTEXT}

4. **Risk Heat Map — Danger Zone files:**
{DANGER_ZONE_LIST}

5. **Previous Audit:** {PREVIOUS_METRICS_JSON_OR_NULL}

## Principle Files
Read ALL 11 principle files from `skills/codebase-audit/principles/`:
maintainability.md, evolvability.md, correctness.md, testability.md, reliability.md,
performance.md, readability.md, modularity.md, consistency.md, operability.md, security.md

## Benchmark Files
Read: `skills/codebase-audit/benchmarks/{language}.md` and `skills/codebase-audit/benchmarks/general.md`

## Analysis Template
Read: `skills/codebase-audit/templates/analysis-template.md` — follow this structure exactly.

## Instructions

1. **Assign priority ranks and weights** to all 11 criteria based on your language + domain expertise. Show your reasoning in the "Criteria Priority Rationale" section.

2. **Write the full analysis report** following the template structure. For each criterion:
   - Grade it using the principle file's rubric + benchmark data
   - Include measured metrics with benchmarks and sources
   - Provide qualitative analysis referencing specific files
   - List actionable improvements with effort estimates (considering team size and codebase size)

3. **Benchmark integration** — for every metric, resolve benchmarks in priority order:
   Language + domain specific → Language specific → Domain specific → General.
   Every benchmark must have a source citation.

4. **Risk heat map** — include the complexity × churn cross-reference with Danger Zone files named.

5. **Recommended actions** — group by Immediate / Near-term / Future. Each includes: affected criteria, description, risk of inaction, effort estimate.

6. **Delta comparison** — if previous audit data is provided, include the delta section.

7. **Return two outputs:**
   a. The complete analysis report (markdown)
   b. The final priority rankings as JSON: `{"rankings": [{"criterion": "...", "rank": N, "weight": "high|medium|low"}], "overall_grade": "...", "overall_grade_rationale": "..."}`
~~~

### Transparency Requirements

- Show criteria priority rationale at the top of the report
- Every benchmark has a source citation in footnotes
- Every grade references at least one measured metric
- Effort estimates reference codebase size and team context
- User context trade-offs acknowledged in relevant sections

---

## Phase 5 — Write & Output

### Output Directory

```
docs/reports/codebase-audit/
├── project-context.md              # Persistent project profile
└── YYYYMMDD/
    ├── metrics.json                # Machine-readable metrics
    ├── metrics.md                  # Human-readable metrics table
    └── analysis.md                 # Full qualitative report
```

Date-stamped directories. If today's directory exists, append suffix: `YYYYMMDD-2`.

### metrics.json Structure

```json
{
  "version": 1,
  "date": "{YYYY-MM-DD}",
  "branch": "{branch}",
  "commit": "{short_hash}",
  "languages": {"primary": "{lang}", "additional": ["typescript"]},
  "domain": "{domain_summary}",
  "overall_grade": "B+",
  "overall_confidence": "high",
  "criteria": {
    "maintainability": {
      "rank": 1,
      "weight": "high",
      "confidence": "high",
      "grade": "B",
      "metrics": {
        "cyclomatic_complexity_avg": {
          "value": 8.2,
          "by_language": {"python": 7.1, "typescript": 9.8},
          "benchmark": 10,
          "source": "Carnegie Mellon SEI",
          "assessment": "good"
        },
        "function_length_median": {
          "value": 24,
          "benchmark": 50,
          "source": "Clean Code, Robert C. Martin",
          "assessment": "good"
        }
      }
    }
  },
  "risk_heat_map": [
    {"file": "src/payment/processor.py", "complexity": 18, "churn_30d": 23, "quadrant": "danger_zone"}
  ],
  "velocity": {
    "lines_added": 1200,
    "lines_deleted": 800,
    "net_change": 400,
    "files_changed": 42,
    "most_churned_files": [
      {"file": "src/main.py", "added": 150, "deleted": 80, "total_churn": 230}
    ]
  },
  "knowledge_concentration": [
    {"module": "src/payment/", "primary_contributor": "alice", "commit_pct": 94, "bus_factor_risk": "high"}
  ],
  "collection_metadata": {
    "agents_dispatched": 6,
    "agents_succeeded": 6,
    "config_source": "auto-detected",
    "benchmarks_source": "cached"
  },
  "methodology": {
    "commands_run": [
      {"agent": "structural", "command": "python helpers/compute_structure.py --lang python --source src/", "status": "success"},
      {"agent": "tests", "command": "pytest --tb=short", "status": "declined_by_user"}
    ],
    "commands_skipped": [],
    "benchmarks": {
      "sources": ["benchmarks/python.md", "benchmarks/general.md"],
      "web_searched": true,
      "citations": [
        {"id": 1, "text": "Carnegie Mellon SEI, 'Cyclomatic Complexity Thresholds', 2018", "url": null}
      ]
    },
    "python_available": true,
    "static_only": false
  },
  "audit_scope": {
    "branch": "main",
    "criteria_measured": ["maintainability", "evolvability", "correctness"],
    "source_paths": ["src/"],
    "test_paths": ["tests/"],
    "exclude_patterns": ["vendor/", "node_modules/"],
    "static_only": false,
    "invocation": "full"
  }
}
```

**Schema notes:**
- `rank` and `weight` are `null` in metrics-only mode; populated after Phase 4.
- `confidence` per criterion: `"high"`, `"medium"`, or `"low"`.
- `by_language` inside metric objects is present only for polyglot repos. For single-language repos, omit it.
- `audit_scope` captures what was measured and how — used for delta comparability checks.
- After Phase 4 completes: **rewrite metrics.json and metrics.md** with final ranks, weights, and adjusted overall grade.

### metrics.md

Pure data, no commentary. Dynamically generated from `metrics.json`. The following is the complete template:

```markdown
# Codebase Metrics — {Project Name}

**Date:** {DATE}
**Branch:** `{BRANCH}` @ `{COMMIT_SHORT}`
**Languages:** {Primary Language} (primary), {Additional Languages}
**Domain:** {Domain Summary}

## Overall Grade: {GRADE} (confidence: {CONFIDENCE})

## Criteria Summary

| Rank | Criterion | Grade | Weight | Key Metric | Measured | Benchmark | Source |
|---|---|---|---|---|---|---|---|
| #1 | {Criterion} | {Grade} | High | {Metric} | {Value} | {Benchmark} | {Source} |
| ... |

## Risk Heat Map

| File | Complexity (CC avg) | Churn (30d changes) | Quadrant |
|---|---|---|---|
| {path} | {CC} | {changes} | Danger Zone / Monitor / Refactor / Stable |

## Detailed Metrics

### {Criterion Name}

| Metric | Measured | Benchmark | Source | Assessment |
|---|---|---|---|---|
| {metric} | {value} | {benchmark} | {citation} | Good / Watch / Action needed |

*(repeated for each measured criterion)*

## Development Velocity

| Metric | Value |
|---|---|
| Lines added (30d) | {N} |
| Lines deleted (30d) | {N} |
| Net change | {N} |
| Files changed | {N} |
| Most-churned file | {path} ({N} changes) |

## Knowledge Concentration

| Module | Primary contributor | % of commits | Bus factor risk |
|---|---|---|---|
| {module} | {contributor} | {pct}% | High / Medium / Low |

## Collection Metadata

- **Agents dispatched:** {N}
- **Agents succeeded:** {N}
- **Language detected:** {Language}
- **Config source:** {.claude/audit.yaml | auto-detected}
- **Benchmarks source:** {cached | cached + web-searched}
```

Only include sections for which data was actually collected. Omit empty sections rather than showing "N/A."

### analysis.md

Written by the author agent per `templates/analysis-template.md`.

### project-context.md

Update/create the persistent profile:

```markdown
# Project Context — {Project Name}

Last updated: {DATE}

## Profile
- **Phase:** {phase}
- **Team:** {team_size}
- **Deployment:** {cadence}
- **Priority:** {priority}
- **Domain:** {domain_summary}

## Known Trade-offs
{user_provided_trade_offs}

## Audit History
- {DATE}: {mode} audit ({grade})
```

### Execution Flows

**`/codebase-audit analysis`:**
1. Find most recent `metrics.json` in `docs/reports/codebase-audit/*/`
2. If not found: "No previous metrics found. Run `/codebase-audit` first."
3. Parse metrics.json
4. Run Phase 3 (user context)
5. Run Phase 4 (analysis writing)
6. Rewrite metrics.json and metrics.md with final ranks/weights
7. Write analysis.md into the same directory

**`/codebase-audit delta`:**
1. Find two most recent `metrics.json` files
2. If <2 found: "Need at least 2 audits for delta comparison. Found {N}."
3. **Comparability check** on `audit_scope`:
   - **Fully compatible** (same `criteria_measured`, `source_paths`, `test_paths`, `exclude_patterns`, `branch`) → full delta with overall grade
   - **Partially compatible** — proceed with overlap, but display warnings:
     - Different `criteria_measured`: compare only overlapping criteria, suppress overall grade delta. Warn: "These audits measured different criteria. Comparing {N} overlapping criteria only."
     - Different `source_paths`/`test_paths`/`exclude_patterns`: compare but warn: "Source scope changed — structural/churn metrics may not be directly comparable."
     - Different `branch`: warn: "Audits are from different branches ({previous} vs {current})."
     - Different `static_only` or `confidence`: warn: "Audit conditions differ — previous was {full/static-only}; current is {full/static-only}. Delta may not be directly comparable."
   - **No overlap** → "These audits share no common criteria and cannot be compared."
4. Display delta table on console
5. Ask if user wants narrative delta analysis

### Cleanup

Remove any temp files. Report output paths:

> Audit complete.
> - Metrics: `docs/reports/codebase-audit/{DATE}/metrics.md`
> - Analysis: `docs/reports/codebase-audit/{DATE}/analysis.md`
> - Overall grade: **{GRADE}**

Notify completion:

```bash
powershell.exe -c "[Console]::Beep(800, 300)"
```

---

## Guardrails

1. **Never present a benchmark without a source citation.** Unsourced benchmarks look made up.
2. **Never grade a criterion without at least one measured metric.** Grades based on vibes are worthless.
3. **Never claim "no issues found" without having actually measured.** False confidence is worse than no audit.
4. **If a helper script fails, mark affected metrics as "Not measured" — not "Good."** Absence of evidence ≠ evidence of absence.
5. **Always show delta direction (improved/declined/stable) when comparing.** Raw numbers without trend are incomplete.
6. **Domain inference must be stated explicitly** so the user can challenge it.
7. **Criteria priority rationale must be shown in the report.** Weighting should be auditable.
8. **Effort estimates must reference codebase size and team context.** Generic "improve this" is not actionable.
9. **All Danger Zone files must be named explicitly.** Abstract risk warnings don't drive action.
10. **User context trade-offs must be acknowledged** in relevant criterion sections.

---

## Graceful Degradation

| Situation | Behavior |
|---|---|
| 1-2 agents fail or time out | Proceed with available data. Note missing agents. Offer to retry. |
| All agents fail | Report failure. Suggest retrying or narrowing scope. |
| No git history | Git/Velocity agent skips. Churn/bus factor marked "No git history." |
| No test runner detected | Tests agent does static analysis only. |
| Helper script fails | Agent falls back to qualitative-only. Metrics marked "Not measured." |
| No internet (WebSearch unavailable) | Use cached benchmarks. Note "cached benchmarks only" in methodology. |
| Unknown language | Use general benchmarks. Extension-count fallback. |
| Massive repo (1000+ files) | Warn user. Agents focus on most significant files. |
| No `.claude/audit.yaml` | Fully auto-detected. Note in methodology. |
| Python not available | Qualitative-only for helper-dependent metrics. |
| No previous audit for delta | "Need at least 2 audits for delta comparison." |
| Live commands declined | Static analysis fallback. Mark as "Skipped (live commands declined)." |

---

## Error Handling

| Error | Behavior |
|---|---|
| Invalid criterion name in arguments | Print valid names, stop |
| `.claude/audit.yaml` is malformed | Report parse error, proceed with auto-detection |
| No source files found | "No source files found in detected paths. Check project structure." |
| metrics.json not found for `analysis` mode | "No previous metrics found. Run `/codebase-audit` first." |
| <2 metrics.json for `delta` mode | "Need at least 2 audits for delta comparison. Found {N}." |
| Output directory creation fails | Report error, suggest alternative path |
| Agent returns malformed JSON | Use what's parseable, note the issue |
