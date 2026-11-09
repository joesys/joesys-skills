# Codebase Audit — Output Schemas

JSON schemas, output file templates, and directory structure for audit artifacts.

## Output Directory Structure

```
docs/reports/codebase-audit/
└── YYYYMMDD/
    ├── metrics.json                # Machine-readable metrics
    ├── metrics.md                  # Human-readable metrics table
    └── analysis.md                 # Full qualitative report
```

User context is now stored in the shared preferences system:
```
.claude/skill-context/
├── preferences.md                  # Shared preferences (project phase, team size, priority)
└── codebase-audit.md               # Audit-specific (trade-offs, cadence, history)
```

Date-stamped directories. If today's directory exists, append suffix: `YYYYMMDD-2`.

---

## metrics.json Schema

```json
{
  "version": 1,
  "date": "{YYYY-MM-DD}",
  "branch": "{branch}",
  "commit": "{short_hash}",
  "languages": {"primary": "{lang}", "additional": ["typescript"]},
  "domain": "{domain_summary}",
  "overall_grade": "B",
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
        {"id": 1, "text": "<source name, year>", "url": null}
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

### Schema Notes

- `rank` and `weight` are `null` in metrics-only mode; populated after Phase 4.
- `confidence` per criterion: `"high"`, `"medium"`, or `"low"`.
- `by_language` inside metric objects is present only for polyglot repos. For single-language repos, omit it.
- `audit_scope` captures what was measured and how — used for delta comparability checks.
- After Phase 4 completes: **rewrite metrics.json and metrics.md** with final ranks, weights, and adjusted overall grade.
- `story_readability` criterion uses dimension-specific metrics: `narrative_flow`, `naming_as_intent`, `cognitive_chunking`, `abstraction_consistency`, `function_focus`, `structural_clarity`, `documentation_quality`, `no_clever_tricks` — each with `value` (1-10), `weight` (percentage), and `assessment`. The `weighted_score` field holds the composite 0-100 score.

---

## metrics.md Template

Pure data, no commentary. Dynamically generated from `metrics.json`:

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

---

## Audit Preferences Template

Audit context lives in `.claude/skill-context/codebase-audit.md`. Shared
project facts (phase, team size, business priority) may also come from the
user's `.claude/skill-context/preferences.md` if it exists. See
`shared/skill-context.md` for the shared format.

### codebase-audit.md Preferences Template

```markdown
# Codebase Audit Preferences

Last updated: {DATE}

## Audit-Specific Context
- **Project phase:** {phase}
- **Team size:** {team_size}
- **Business priority:** {priority}
- **Deployment cadence:** {cadence}
- **Domain:** {domain_summary}

## Known Trade-offs
{user_provided_trade_offs}

## Audit History
- {DATE}: {mode} audit ({grade})

## Overrides (optional)
- **large_tier_threshold_files:** {default 1000} — source file count that triggers large-tier decomposition
```

---

## Execution Flows

### `/codebase-audit analysis`

1. Find most recent `metrics.json` in `docs/reports/codebase-audit/*/`
2. If not found: "No previous metrics found. Run `/codebase-audit` first."
3. Parse metrics.json
4. Run Phase 3 (user context)
5. Run Phase 4 (analysis writing)
6. Rewrite metrics.json and metrics.md with final ranks/weights
7. Write analysis.md into the same directory

### `/codebase-audit delta`

1. Find two most recent `metrics.json` files
2. If <2 found: "Need at least 2 audits for delta comparison. Found {N}."
3. **Comparability check** on `audit_scope`:
   - **Fully compatible** (same `criteria_measured`, `source_paths`, `test_paths`, `exclude_patterns`, `branch`) → full delta with overall grade
   - **Partially compatible** → compare the overlap. Warn which `audit_scope` fields differ and what that makes non-comparable:
     - Different `criteria_measured`: compare only overlapping criteria and suppress the overall grade delta.
     - Different `source_paths`, `test_paths`, or `exclude_patterns`: structural and churn metrics may not be directly comparable.
     - Different `branch`: name both branches.
     - Different `static_only` or confidence: the audit conditions differ, so the whole delta may not be directly comparable.
   - **No overlap** → "These audits share no common criteria and cannot be compared."
4. Display the delta table on the console, with the direction of each change (improved / declined / stable)
5. Ask if user wants narrative delta analysis
