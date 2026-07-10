# Modularity

## Definition

Modularity measures how well the codebase is divided into independent, composable units with clear boundaries. Good modularity means each module can be understood, modified, and tested in isolation without requiring knowledge of the entire system.

## Concrete Signals

**Positive signals:**
- Deep modules — simple interfaces hiding complex implementations
- Strong encapsulation — internal details not leaked through public APIs
- Law of Demeter observed — objects interact with immediate collaborators only
- Separation of concerns — each module owns one domain concept
- Single source of truth — data and logic not duplicated across modules
- Clear public API per module (index/barrel files, __init__.py exports)

**Negative signals:**
- Wide, shallow modules — large interfaces exposing implementation details
- Law of Demeter violations (long method chains: `a.b.c.d.doThing()`)
- Circular dependencies between modules
- Shared mutable state across module boundaries
- Feature envy — modules heavily accessing other modules' internals
- No clear boundary between public and private APIs

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Circular dependency count | Detect cycles in import/require graph | Architecture agent |
| Average module fan-out | Count import targets per module | Architecture agent |
| Import depth (max chain length) | Trace transitive dependency chains | Architecture agent |
| Encapsulation signals | Check for public vs private member exposure | Agent qualitative |
| Module size distribution | Files per module, LOC per module | Structural agent |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Zero circular deps, fan-out avg ≤3, clear encapsulation, deep modules throughout |
| A | Zero circular deps, fan-out avg ≤5, good encapsulation |
| B | ≤2 circular deps, fan-out avg ≤7, reasonable boundaries |
| C | 3-5 circular deps, or unclear module boundaries, or some god modules |
| D | >5 circular deps, or pervasive cross-module coupling |
| F | No discernible module structure, everything depends on everything |

## Language-Aware Notes

- **Go:** Package system naturally enforces modularity. Unexported (lowercase) symbols are private. Check for internal/ directories.
- **Rust:** Crate and module system with explicit `pub` visibility. Strong modularity by default.
- **Python:** Flexible import system allows deep coupling. Check for `__init__.py` controlling public exports. Watch for `from module import *`.
- **TypeScript:** Barrel files (index.ts) control public APIs. Check for path aliases vs relative import spaghetti.
- **C#:** Namespace and assembly boundaries. Check for `internal` vs `public` access modifiers.
