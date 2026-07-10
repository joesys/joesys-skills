# Testability

## Definition

Testability measures how amenable the codebase is to automated testing. A testable codebase has clear inputs and outputs, injectable dependencies, and minimal reliance on global state — making it possible to write fast, reliable, isolated tests.

## Concrete Signals

**Positive signals:**
- Dependency injection (constructor injection, parameter injection)
- Pure functions with no side effects where possible
- Separation of concerns — business logic separate from I/O
- Small, focused functions with clear contracts
- Interfaces/protocols for external dependencies
- Test fixtures and factories for data setup

**Negative signals:**
- Hard-coded dependencies (direct instantiation of collaborators)
- Global state accessed from business logic
- Functions with hidden side effects (file I/O, network, database mixed with logic)
- Tight coupling between modules making isolated testing impossible
- No test infrastructure (no test runner, no test directory)
- Tests that require complex environment setup

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Test-to-source ratio | test_file_count / source_file_count | Tests agent |
| Test type distribution | Categorize tests as unit/integration/e2e | Tests agent |
| DI pattern usage | Grep for constructor injection, interface parameters | Agent qualitative |
| Mock/stub usage | Check for mock libraries in test files | Tests agent |
| Test quality signals | Assert count per test, behavior vs implementation testing | Tests agent |
| Global state reliance | Grep for global/module-level mutable state | Agent qualitative |

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
