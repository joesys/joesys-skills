# Modularity

## Definition

Modularity measures how well the codebase is divided into independent, composable units with clear boundaries.

## Signals to Look For

- Wide, shallow modules whose large interfaces expose internals; deep modules (small interface, large hidden implementation) are the positive signal.
- No clear boundary between public and private APIs.
- Shared mutable state across module boundaries.
- Long call chains that reach into other modules' internals (`a.b.c.d.doThing()`).

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
