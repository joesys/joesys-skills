# Readability

## Definition

Readability measures how easily a developer can understand the code's purpose, logic, and intent by reading it. Readable code minimizes the cognitive effort required to comprehend what the code does and why, reducing onboarding time and review effort.

## Concrete Signals

**Positive signals:**
- Self-documenting code — function and variable names express intent
- Consistent naming conventions across the codebase
- SLAP — functions operate at a single level of abstraction
- Appropriate documentation — public APIs documented, complex algorithms explained
- Clean formatting — consistent indentation, whitespace, line length
- Small functions focused on a single task

**Negative signals:**
- Cryptic abbreviations and single-letter variable names (outside loop indices)
- Inconsistent naming (camelCase mixed with snake_case without convention)
- Functions doing multiple things at different abstraction levels
- Missing documentation on public APIs or complex algorithms
- Clever/tricky code that sacrifices clarity for brevity
- Deep nesting making control flow hard to follow
- Over-commenting (restating what code does instead of explaining why)

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Naming convention adherence | Check for consistent case conventions per language | Agent qualitative |
| Comment density | comment_lines / total_lines (target 10-20%) | `compute_structure.py` |
| Average function length | Shorter functions are generally more readable | `compute_structure.py` |
| Nesting depth | Deep nesting hinders readability | `compute_structure.py` |
| Documentation presence | Check for docstrings/JSDoc on public functions | Agent qualitative |
| Single-letter variable usage | Grep for single-letter names outside standard patterns | Agent qualitative |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Self-documenting names, consistent conventions, appropriate docs, comment density 10-20%, median function ≤15 lines |
| A | Good naming, mostly consistent, public APIs documented |
| B | Generally readable, minor inconsistencies, some documentation gaps |
| C | Mixed readability — some modules clear, others confusing |
| D | Poor naming, inconsistent conventions, minimal documentation |
| F | Cryptic names throughout, no documentation, deeply nested logic |

## Language-Aware Notes

- **Python:** PEP 8 is the universal standard. Check for Black/isort/ruff configuration. Docstring conventions (Google, NumPy, Sphinx) should be consistent.
- **Go:** gofmt enforces formatting. Readability focuses on naming (short names for short scopes) and GoDoc comments on exported symbols.
- **Rust:** rustfmt enforces style. `///` doc comments on public items are the standard. Lifetime annotations can hurt readability — note excessive lifetime complexity.
- **TypeScript:** ESLint + Prettier configuration signals style discipline. Check for consistent use of types vs `any`.
- **C++:** No universal formatter — check for clang-format config. Header organization and include guards affect readability.
