# Correctness

## Definition

Correctness measures the extent to which the code behaves as intended, handles edge cases properly, and is protected by automated tests. A correct codebase produces the right results for all valid inputs and fails gracefully for invalid ones.

## Concrete Signals

**Positive signals:**
- High test pass rate (100% target)
- Tests cover edge cases (empty inputs, zero, negative, boundary values)
- Explicit error handling with specific exception types
- Guard clauses validating inputs at function entry
- Null/undefined checks before attribute access
- EAFP (try/except) over LBYL (check-then-act) for race-condition-prone operations

**Negative signals:**
- Off-by-one errors in loop bounds or slice indices
- Missing null/undefined checks on optional values
- Boolean logic errors (De Morgan violations, precedence bugs)
- Unhandled edge cases (empty collections, zero division)
- Race conditions in concurrent/async code (TOCTOU patterns)
- Implicit None returns from functions missing return statements
- Bare except clauses swallowing exceptions silently
- State management bugs (mutable defaults, aliased mutation)

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Test pass rate | Run test suite, compute pass percentage | Tests agent (live) |
| Test count vs source count | test_files / source_files ratio | Tests agent (static) |
| Test execution time | Measure suite runtime | Tests agent (live) |
| Error handling patterns | Grep for bare except, broad catches | Agent qualitative |
| Null safety patterns | Check for unguarded attribute access | Agent qualitative |
| Assertion density in tests | assertions_per_test average | Tests agent (static) |
| Edge case coverage signals | Check for boundary value tests | Agent qualitative |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | 100% test pass, test ratio ≥0.8, edge cases covered, robust error handling throughout |
| A | 100% test pass, test ratio ≥0.6, good error handling |
| B | ≥95% test pass, test ratio ≥0.4, basic error handling |
| C | ≥90% test pass, or test ratio <0.4, or inconsistent error handling |
| D | <90% test pass, or minimal tests, or broad exception swallowing |
| F | No tests, or <80% pass rate, or pervasive unhandled errors |

## Language-Aware Notes

- **Rust:** The type system catches null errors and many state bugs at compile time. Correctness scoring should weight runtime behavior less and focus on logic errors and test coverage.
- **Go:** Explicit error returns can be silently ignored (`_ = someFunc()`). Grep for discarded errors as a correctness signal.
- **Python:** Dynamic typing means correctness relies heavily on tests. Weight test coverage higher for Python than for statically typed languages.
- **TypeScript:** `strict` mode and `noUncheckedIndexedAccess` dramatically improve correctness. Check tsconfig for strictness flags.
- **C#:** Nullable reference types (C# 8+) provide null safety. Check if the feature is enabled.
