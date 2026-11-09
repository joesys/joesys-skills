# Consistency

## Definition

Consistency measures the degree to which the codebase follows uniform patterns, conventions, and idioms throughout.

## Signals to Look For

- A formatter and linter configured and enforced.
- Mixed naming styles within one language.
- More than one error-handling approach (return values, exceptions, callbacks).
- The same operation done differently in different modules (for example, three ways to read config).

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Naming convention adherence | Sample files and check for consistent casing | Quality agent |
| Import ordering consistency | Compare import blocks across files | Quality agent |
| Error handling pattern variety | Categorize error handling approaches across modules | Quality agent |
| Formatter/linter config presence | Check for .prettierrc, .eslintrc, pyproject.toml [tool.black], etc. | Architecture agent |
| Code style uniformity | Check for consistent indentation, line length, spacing | Quality agent |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Enforced formatter + linter, uniform naming, consistent patterns throughout, zero style violations |
| A | Formatter configured, mostly uniform naming, consistent major patterns |
| B | Some formatting enforcement, minor inconsistencies in naming or patterns |
| C | Inconsistent patterns — some conventions exist but not uniformly followed |
| D | Multiple competing conventions, no formatter, inconsistent error handling |
| F | No discernible conventions, every file follows different patterns |

## Language-Aware Notes

- **Go:** gofmt is universal — formatting consistency is essentially guaranteed. Focus on naming conventions (exported vs unexported) and error handling patterns.
- **Python:** Check for Black/isort/ruff in pyproject.toml. PEP 8 compliance. Multiple docstring styles (Google, NumPy, Sphinx) should not coexist.
- **Rust:** rustfmt + clippy handle most consistency. Focus on error handling patterns (anyhow vs thiserror vs custom) and naming conventions.
- **TypeScript:** ESLint + Prettier combination. Check tsconfig strictness consistency across packages in monorepos.
- **C++:** No universal formatter — check for .clang-format. Naming conventions vary widely (Google style, LLVM style, etc.). Consistency within the project is what matters.
