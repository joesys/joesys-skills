# Codebase Quality Audit — {PROJECT_NAME}

**Date:** {DATE}
**Auditor:** Senior {LANGUAGE} engineer · {DOMAIN} specialist
**Branch:** `{BRANCH}` @ commit `{COMMIT}`
**Engine:** {ENGINE_OR_OMIT}
**Project phase:** {PHASE} (from user context)
**Team:** {TEAM_SIZE}
**Previous audit:** {PREVIOUS_AUDIT_REFERENCE}

---

## Executive Summary

2-3 paragraphs. Headline finding. Overall grade. Top risk. Top strength.
Non-engineers should understand this section.

**Overall grade: {GRADE} (confidence: {CONFIDENCE})**

---

## Criteria Priority Rationale

Based on analysis as a senior {LANGUAGE} engineer specializing in {DOMAIN}:

| Rank | Criterion | Weight | Rationale |
|---|---|---|---|
| #1 | {Criterion} | High | {Why this matters most for this language + domain} |
| #2 | {Criterion} | High | {Rationale} |
| ... | ... | ... | ... |
| #11 | {Criterion} | Low | {Rationale} |
| #12 | {Criterion} | Low | {Rationale} |

---

## Industry Context & Benchmarks

Frame the audit by comparing against industry norms for {LANGUAGE} {DOMAIN} projects.

| Metric | This Project | Industry Benchmark | Source | Assessment |
|---|---|---|---|---|
| {Metric} | {Value} | {Benchmark} | {Citation} | Good / Watch / Action needed |
| ... | ... | ... | ... | ... |

---

## Risk Heat Map

Complexity × churn cross-reference. High-complexity + high-churn files are the highest-risk targets.

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

**Danger Zone files:**
| File | Complexity (CC avg) | Churn (30d changes) |
|---|---|---|
| {path} | {CC} | {changes} |

---

## {RANK}. {CRITERION_NAME} — Grade: {GRADE}

**#{RANK} priority — Weight: {WEIGHT}.** {ONE_LINE_RATIONALE}

### What This Measures

1-3 sentences. Plain language explanation of what this criterion assesses.

### Objective Metrics

| Metric | Measured | Benchmark | Source | Assessment |
|---|---|---|---|---|
| {Metric name} | {Measured value} | {Benchmark threshold} | {Citation} | Good / Watch / Action needed |

*{Plain-language gloss for non-technical readers}*

### Why These Metrics

Brief explanation of why these specific metrics matter for this criterion in this context.

### Qualitative Analysis

**Strengths:**
- {Specific strength with file:line reference}

**Concerns:**
- {Specific concern with file:line reference}

### Actionable Improvements

*(Omit this section if the criterion scores A+ with no meaningful improvements.)*

**{Timeline tag: Immediate / Near-term / Future}:** {Description}
- Affected criteria: {list}
- Effort: {estimate based on codebase size and team}
- Risk of inaction: {what happens if this isn't addressed}

---

*(Repeated for all measured criteria, ordered by priority rank)*

---

## Development Velocity Analysis

Current velocity metrics, industry comparison, and quality-velocity relationship assessment.

| Metric | Value |
|---|---|
| Lines added (30d) | {N} |
| Lines deleted (30d) | {N} |
| Net change | {N} |
| Files changed | {N} |
| Most-churned file | {path} ({N} changes) |

---

## Knowledge Concentration

Bus factor analysis. Per-module ownership and single-contributor file risks.

| Module | Primary contributor | % of commits | Bus factor risk |
|---|---|---|---|
| {module} | {contributor} | {pct}% | High / Medium / Low |

---

## Recommended Actions

### Immediate

Each action includes: affected criteria, description, risk of inaction, effort estimate.

**{N}. {Action title}** *({Criteria})*
{Description with specific files/modules referenced.}
**Risk of inaction:** {What happens without this.}
**Effort:** {Time estimate} ({role})

### Near-Term

...

### Future

...

---

## Delta from Previous Audit

*(Omit if no previous audit.)*

| Criterion | Previous | Current | Delta |
|---|---|---|---|
| {Criterion} | {Grade} | {Grade} | ▲ improved / ▼ declined / ● stable |

{Narrative explaining what changed and why.}

---

## Conclusion

{2-3 paragraphs summarizing the audit, key takeaways, and recommended next steps.}

---

## Methodology Notes

### Measurement Commands

| Agent / Tool | Command | Status |
|---|---|---|
| {Agent} | {Command} | success / failed / declined / skipped / not-installed |

### Audit Metadata

- **Analysis model:** Claude Opus
- **Collection agents:** {N} dispatched, {N} succeeded
- **Config source:** {.claude/audit.yaml or auto-detected}
- **Benchmarks source:** {cached / cached + web-searched}
- **User context source:** {new interview / confirmed profile from YYYY-MM-DD}
- **Static analysis tools:** {N} detected, {N} available, {N} executed

### Benchmark Sources

{Numbered footnotes with full citations.}

---

## Footnotes

[^1]: {CITATION}
