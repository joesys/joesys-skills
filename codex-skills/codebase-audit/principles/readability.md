# Readability

## Definition

Readability measures how easily a developer can understand the code's purpose, logic, and intent by reading it.

## Signals to Look For

- Cryptic abbreviations and single-letter names (outside loop indices).
- Public APIs or complex algorithms without documentation.
- Comments that restate the code instead of explaining why.
- Clever, dense code that trades clarity for brevity.

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Naming convention adherence | Check for consistent case conventions per language | Agent qualitative |
| Comment density | comment_lines / total_lines (target 10-20%) | `compute_structure.py` |
| Average function length | Shorter functions are generally more readable | `compute_structure.py` |
| Nesting depth | Deep nesting hinders readability | `compute_structure.py` |
| Documentation presence | Check for docstrings/JSDoc on public functions | Agent qualitative |
| Single-letter variable usage | Search for single-letter names outside standard patterns | Agent qualitative |

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
