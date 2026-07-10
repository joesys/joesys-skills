# Consistency

## Definition

Consistency measures the degree to which the codebase follows uniform patterns, conventions, and idioms throughout. A consistent codebase is predictable — once you understand how one module works, you can navigate any other module using the same mental model.

## Concrete Signals

**Positive signals:**
- Uniform naming conventions (one casing style per language)
- Consistent import ordering (stdlib → third-party → local)
- Uniform error handling patterns across the codebase
- Consistent file/directory naming and organization
- Formatter/linter configuration enforced (Prettier, Black, gofmt, rustfmt)
- Consistent patterns for common operations (logging, config access, DB queries)

**Negative signals:**
- Mixed naming conventions (camelCase and snake_case in the same language)
- Inconsistent import ordering across files
- Multiple error handling approaches (some return errors, some throw, some use callbacks)
- Inconsistent file organization (some feature-based, some layer-based)
- No formatter/linter configuration
- Same operation done differently in different modules (3 ways to read config)

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
