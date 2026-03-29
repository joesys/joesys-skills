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
