# Evolvability

## Definition

Evolvability measures how easily the codebase can accommodate new requirements, features, or changes without extensive rewrites or cascading modifications.

## Signals to Look For

- God classes or modules with many responsibilities.
- Shotgun surgery — one change needs edits across many files.
- Switch or if/else chains that must change for every new type, instead of extension points.
- Tight coupling to concrete classes in key modules; inheritance deeper than 3 levels where composition would do.

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Fan-out per module (avg, max) | Count import targets per file | Agent import analysis |
| Fan-in per module (avg, max) | Count files importing each module | Agent import analysis |
| Circular dependency count | Detect cycles in import graph | Agent graph analysis |
| Inheritance depth (max) | Trace class hierarchies | Agent qualitative |
| Module boundary clarity | Assess public interface vs internal coupling | Agent qualitative |
| Dependency direction consistency | Check high-level → low-level dependency flow | Agent qualitative |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Fan-out avg ≤3, zero circular deps, clear abstractions, composition-first design |
| A | Fan-out avg ≤5, zero circular deps, mostly good boundaries |
| B | Fan-out avg ≤7, ≤2 circular deps, reasonable structure |
| C | Fan-out avg ≤10, or 3-5 circular deps, or tight coupling in key modules |
| D | Fan-out avg >10, or >5 circular deps, or god classes present |
| F | Pervasive tight coupling, no clear boundaries, circular deps widespread |

## Language-Aware Notes

- **Go:** Implicit interfaces make evolvability easier — any type satisfying an interface works without explicit declaration. Go codebases often score well here by default.
- **Rust:** Trait-based generics and the orphan rule enforce clean boundaries. Crate system naturally promotes modularity.
- **Python:** Duck typing hides coupling — code may depend on implicit interfaces that are fragile. Look at actual import graphs, not just class hierarchies.
- **TypeScript:** Interface and type system make dependencies explicit. Check for `any` usage which undermines type-based evolvability.
- **C++:** Header dependencies create coupling not visible in source files. Include-what-you-use analysis is critical.
