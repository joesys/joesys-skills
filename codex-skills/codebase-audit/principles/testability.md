# Testability

## Definition

Testability measures how amenable the codebase is to automated testing.

## Signals to Look For

- Collaborators created inside business logic instead of injected (constructor or parameter injection).
- Business logic mixed with I/O (file, network, database) so it cannot run in isolation.
- Global or module-level mutable state read by business logic.
- Tests that need complex environment setup to run.

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Test-to-source ratio | test_file_count / source_file_count | Tests agent |
| Test type distribution | Categorize tests as unit/integration/e2e | Tests agent |
| DI pattern usage | Search for constructor injection, interface parameters | Agent qualitative |
| Mock/stub usage | Check for mock libraries in test files | Tests agent |
| Test quality signals | Assert count per test, behavior vs implementation testing | Tests agent |
| Global state reliance | Search for global/module-level mutable state | Agent qualitative |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Test ratio ≥1.0, DI pervasive, unit + integration + e2e tests present, high assertion density |
| A | Test ratio ≥0.8, DI common, multiple test types, good assertion density |
| B | Test ratio ≥0.5, some DI, mostly unit tests |
| C | Test ratio ≥0.3, minimal DI, basic tests present |
| D | Test ratio <0.3, no DI patterns, tests are shallow or flaky |
| F | No tests, or test infrastructure absent, or all tests are smoke tests only |

## Language-Aware Notes

- **Go:** Interface-based testing is idiomatic — check for interface definitions used for test doubles. Table-driven tests are the Go convention.
- **Python:** Monkey-patching (`unittest.mock.patch`) enables testing without formal DI. Its presence is a positive signal, though constructor injection is still preferred.
- **Rust:** The type system and trait system make testability more natural. `#[cfg(test)]` modules are the standard test convention.
- **JavaScript/TypeScript:** Jest mocking and dependency injection frameworks (like tsyringe) are common patterns to check for.
- **GDScript:** Godot's scene tree architecture makes unit testing difficult. Check for gdUnit4 or GUT framework usage.
