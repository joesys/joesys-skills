# Evolvability

## Definition

Evolvability measures how easily the codebase can accommodate new requirements, features, or changes without extensive rewrites or cascading modifications. A highly evolvable codebase allows developers to add functionality by extending rather than modifying existing code.

## Concrete Signals

**Positive signals:**
- Single Responsibility Principle — each module/class has one reason to change
- Open/Closed Principle — behavior extensible via new types or strategies, not if/else chains
- Dependency Inversion — high-level modules depend on abstractions, not concrete implementations
- Composition over inheritance — behavior assembled from small pieces
- Orthogonality — changing one module does not require changes in unrelated modules
- Clear module boundaries with well-defined interfaces
- Low fan-out — each module depends on few others

**Negative signals:**
- God classes/modules with many responsibilities
- Shotgun surgery — one change requires edits across many files
- Feature envy — functions heavily accessing another module's data
- Deep inheritance hierarchies (>3 levels)
- Tight coupling via concrete class references instead of interfaces/protocols
- Circular dependencies between modules
- Switch/if-else chains that must be updated for every new type

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
