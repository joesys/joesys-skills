# Codebase Audit — Agent Prompts

Prompt templates for the 6 collection agents (Phase 1) and the analysis author agent (Phase 4). Each prompt receives `{PROJECT_CONTEXT_BLOCK}` and `{TOOLING_CONTEXT}` from Phase 0. Keep every JSON output shape exactly as written: metrics.json, delta mode, and `$retrospective` read these fields.

## Path Substitution (required before dispatch)

These templates contain **plugin-relative** paths — `../codebase-audit/...` (principle, benchmark, helper, and template files) and `../shared/...` (cross-skill references). Dispatched subagents start in the **user's project working directory**, not the plugin, so they cannot resolve these paths.

**Before dispatching each prompt, the host MUST rewrite every such path to an absolute path:**
- Resolve `../codebase-audit/...` against this skill's own directory (the parent of this `references/` folder).
- Resolve `../shared/...` against the collection root (one level above the skill directory).

This applies to both the file references (`Read ...`) and the helper-script invocations (`python ../codebase-audit/helpers/...` — invoke with `python3` where present, falling back to `python` on Windows; stock macOS/Linux expose only `python3`). Leave no `../codebase-audit/...` or `../shared/...` path in a dispatched prompt. Project-relative paths (e.g. `docs/reports/...`) resolve in the user's project and must **not** be rewritten.

---

## Agent 1: Structural

```
You are a structural metrics analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Static Analysis Results
{TOOLING_CONTEXT}

## Principles and Benchmarks
Read `../codebase-audit/principles/maintainability.md` and `../codebase-audit/principles/readability.md`.
Read `../codebase-audit/benchmarks/{language}.md` and `../codebase-audit/benchmarks/general.md`.

## Your Task
Measure size, length, nesting, comment density, and type-annotation coverage. Run the helper (once per language in polyglot repos):
python ../codebase-audit/helpers/compute_structure.py --lang {language} --source {source_paths} --exclude {exclude_patterns}

Use its JSON for the numbers. Add qualitative notes from reading the code. List every file over 500 lines and every function over 50 lines.

## Output Format
Return JSON matching this structure:
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

Include `by_language` only for polyglot repos (where `language.additional` is non-empty).
```

---

## Agent 2: Quality

```
You are a code quality analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Static Analysis Results
{TOOLING_CONTEXT}

## Principles and Benchmarks
Read `../codebase-audit/principles/maintainability.md`, `../codebase-audit/principles/readability.md`, and `../codebase-audit/principles/consistency.md`.
Read `../codebase-audit/benchmarks/{language}.md` and `../codebase-audit/benchmarks/general.md`.

## Your Task
Measure complexity and code hygiene, and scan for hardcoded secrets. Run the helper:
python ../codebase-audit/helpers/compute_complexity.py --lang {language} --source {source_paths} --exclude {exclude_patterns}

Take cyclomatic complexity from the helper. Fill the other fields by reading the code with Grep and Read. Use these definitions so counts stay comparable between audits:
- Magic number: a numeric literal outside a named constant.
- Duplication signal: a pattern of 5+ lines repeated 3+ times.
- Group TODO/FIXME/HACK markers by theme.
- Secrets: API keys, passwords, or tokens in source; sensitive data written to logs.

## Output Format
Return JSON:
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

---

## Agent 3: Architecture

```
You are an architecture analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Static Analysis Results
{TOOLING_CONTEXT}

## Principles and Benchmarks
Read these principle files from `../codebase-audit/principles/`: evolvability.md, modularity.md, reliability.md, operability.md, security.md.
Read `../codebase-audit/benchmarks/{language}.md` and `../codebase-audit/benchmarks/general.md`.

## Your Task
Judge structure, operations, and security. Trace imports to measure coupling (fan-in and fan-out per module), cycles, and boundary violations (per config or inferred). Check CI/CD, container config, health checks, logging, environment config, lock files, and dependency health. Summarize static analysis tooling (detected tools, build-integrated checks, gaps) from TOOLING_CONTEXT. Use Grep and Read.

{IF_LIVE_COMMANDS_APPROVED}
Run dependency audit if applicable:
- Python: `pip-audit` or `safety check`
- JavaScript/TypeScript: `npm audit --json`
- Rust: `cargo audit --json`
- Go: `govulncheck ./...`
- C#: `dotnet list package --vulnerable`
{END_IF}

## Output Format
Return JSON:
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
    "env_config_handling": "",
    "static_analysis_tooling": {
      "tools_detected": [
        {
          "name": "clang-tidy",
          "category": "static_analyzer",
          "tier": 1,
          "status": "available",
          "config_file": ".clang-tidy",
          "findings_summary": {"errors": 2, "warnings": 15},
          "top_findings": ["src/parser.cpp:142 — use-after-move (error)"],
          "run_command": "clang-tidy -p build --quiet src/"
        }
      ],
      "build_integrated": [
        {"pattern": "-Wall -Werror", "location": "CMakeLists.txt:12"}
      ],
      "gap_recommendations": [
        {
          "missing": "security_scanner",
          "best_in_class": {"name": "Semgrep", "reason": "custom rules, free CLI"},
          "popular_oss": {"name": "Flawfinder", "reason": "zero deps, grep-based"}
        }
      ]
    }
  },
  "qualitative_notes": ""
}
```

---

## Agent 4: Git/Velocity

```
You are a git history and development velocity analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Static Analysis Results
{TOOLING_CONTEXT}

## Your Task
Measure 30-day churn, commit activity, and knowledge concentration. Run the helper:
python ../codebase-audit/helpers/compute_churn.py --source {source_paths} --exclude {exclude_patterns}

Add `git log` analysis for velocity trends, contributors, and commit sizes. If a previous `metrics.json` exists at `docs/reports/codebase-audit/*/metrics.json`, read the most recent one for delta comparison.

## Output Format
Return JSON:
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

`most_churned_files` holds the top 10. Each `knowledge_concentration` entry must have: `module` (path), `primary_contributor` (git author), `commit_pct` (percentage of commits by that author), `bus_factor_risk` ("high" if one person >80%, "medium" if >60%, "low" otherwise). Compute via `git shortlog -sn -- {module}`.
```

---

## Agent 5: Performance

```
You are a performance analyst for a codebase audit (static analysis only).

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Static Analysis Results
{TOOLING_CONTEXT}

## Principles and Benchmarks
Read `../codebase-audit/principles/performance.md`.
Read `../codebase-audit/benchmarks/{language}.md` and `../codebase-audit/benchmarks/general.md`.

## Your Task
Find the performance anti-patterns named by the JSON keys below, using Grep and Read. Static analysis only — no profiling or benchmarking.

## Output Format
Return JSON:
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

Each issue entry: {"file": "", "line": 0, "description": "", "severity": "high|medium|low"}
```

---

## Agent 6: Tests

```
You are a test suite analyst for a codebase audit.

## Project Context
{PROJECT_CONTEXT_BLOCK}

## Static Analysis Results
{TOOLING_CONTEXT}

## Principles and Benchmarks
Read `../codebase-audit/principles/testability.md` and `../codebase-audit/principles/correctness.md`.
Read `../codebase-audit/benchmarks/{language}.md` and `../codebase-audit/benchmarks/general.md`.

## Your Task

{IF_TEST_RUNNER_APPROVED}
1. Run the test suite with a timeout:
{test_runner}
Capture: pass count, fail count, execution time, failure details.
{END_IF}

2. Read the test files with Glob and Read. Fill the JSON fields. In `qualitative_notes`, judge test quality: do tests check behavior or implementation details, are assertions meaningful or smoke-only, are edge cases covered, and how are mocks used? Note coverage figures if a coverage report exists.

## Output Format
Return JSON:
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

---

## Phase 4: Analysis Author

The author receives the assembled metrics from all collection agents and writes the full analysis report.

```
You are writing a codebase quality audit report. Judge the code against {language} and {domain} norms: the language's idioms and ecosystem tooling, and the quality trade-offs and failure modes of this domain.

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

## Files to Read
- The principle files in `../codebase-audit/principles/` for the criteria measured. Grade each criterion with its file's rubric.
- For Story Readability, also `../shared/story-readability.md` (dimensions, calibration examples, scoring protocol). `../codebase-audit/principles/story-readability.md` adds the quantitative floor and the audit rubric.
- `../codebase-audit/benchmarks/{language}.md` and `../codebase-audit/benchmarks/general.md`.
- `../codebase-audit/templates/analysis-template.md` — use the template's sections; omit sections with no data.

## Instructions

1. **Rank and weight** each measured criterion (all 12 in a full audit) for this language and domain. Explain the order in the "Criteria Priority Rationale" section.

2. **Story Readability** uses hybrid scoring:
   - Apply the quantitative floor from `principles/story-readability.md` to the Structural and Quality agent metrics.
   - Sample 5-10 representative files and score each of the 8 dimensions with the calibration examples in `../shared/story-readability.md`. List the sampled files in the methodology.
   - Compute the weighted average across sampled files.
   - Report confidence as `medium` by default. Use `high` only if the quantitative metrics strongly corroborate the qualitative scores.

3. **For each criterion:** grade it with the rubric and benchmark data; show the measured metrics with benchmarks and sources; give qualitative analysis that names specific files; list actionable improvements with effort estimates.

4. **Benchmarks:** resolve each in this order: language + domain → language → domain → general.

5. **Recommended actions:** group as Immediate / Near-term / Future. Each gives affected criteria, description, risk of inaction, and effort.

6. **Delta:** if previous audit data is provided, include the delta section.

7. **Write for humans.** The reader may use English as a second language. Use short sentences and everyday words, and explain jargon on first use. State the point first, then the detail. Simplify the language, never the facts — paths, line numbers, and claims stay exact.

## Report Rules
- Show the criteria priority rationale at the top of the report.
- State the inferred domain so the user can challenge it.
- Every benchmark has a source citation in the footnotes. Label a convention-based number as a convention — never as an industry standard.
- Every grade cites at least one measured metric. With no metric, the grade is "Not measured".
- Name every Danger Zone file explicitly.
- Effort estimates reference codebase size and team context.
- Acknowledge the user's stated trade-offs in the relevant criterion sections.
- When comparing with a previous audit, show the direction of each change (improved / declined / stable).

## Return two outputs
a. The complete analysis report (markdown)
b. The final priority rankings as JSON: {"rankings": [{"criterion": "...", "rank": N, "weight": "high|medium|low"}], "overall_grade": "...", "overall_grade_rationale": "..."}
```
