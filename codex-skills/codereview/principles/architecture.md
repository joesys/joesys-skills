# Architecture Principles

Architecture asks: where does each piece of knowledge live, and what must change together? Use this file as a lens, not a checklist. Report only problems that cost something in this change: a bug, a rule that must be edited in several places, a test that cannot be written, or a change that ripples into unrelated code.

The most common mistake in this domain is noise: suggesting layers, interfaces, or patterns that the code does not need. **Do not add layers or abstractions for possible future features.** Do not suggest a repository, service, factory, or interface layer for code with one implementation and one caller. When code is already over-built for its one use, that is the finding: suggest the simpler shape.

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Duplicated logic scattered across modules | DRY |
| Same config value defined in multiple places | Single Source of Truth |
| Function mixes DB calls, business rules, and formatting | Separation of Concerns |
| Internal data structures leak through public API | Modularity / Encapsulation |
| Chained accessor calls (`a.b.c.d.do()`) | Law of Demeter |
| Changing one module forces changes in unrelated modules | Orthogonality |
| Hard to test because dependencies are created internally | Dependency Injection |
| Deep inheritance hierarchies with combinatorial explosion | Composition Over Inheritance |
| God class that handles everything | SOLID (SRP) |
| Sensible behavior requires pages of config boilerplate | Convention Over Configuration |
| Method both mutates state and returns a value | Command-Query Separation |
| "Reusable" utility used by exactly one caller | Code Reusability |
| Invalid data propagates far before crashing | Parse, Don't Validate |
| Debugging nightmares caused by mutated shared state | Immutability |
| Retrying an operation causes duplicates or corruption | Idempotency |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **DRY vs. Decoupling** | Merging similar-looking code into one shared function can couple unrelated domains. Prefer duplication over the wrong abstraction — if the code evolves for different reasons, it is not truly duplicated. |
| **Encapsulation vs. Testability** | Hiding everything behind private methods can make unit testing difficult. Expose seams through dependency injection rather than making internals public. |
| **Composition vs. Simplicity** | Composition is more flexible than inheritance but introduces more objects and wiring. For simple, stable hierarchies (e.g., `Exception` subclasses), inheritance is fine. |
| **Modularity vs. Performance** | Deep module boundaries may add overhead. Co-locate hot paths when profiling proves the boundary is the bottleneck — not before. |
| **Immutability vs. Practicality** | Full immutability takes discipline in most languages (frozen records, tuples, read-only types). Apply it where bugs are likely — shared state, concurrent access — not to every local variable. |
| **SOLID vs. KISS** | Blindly applying all five SOLID principles to a small script creates over-engineering. SOLID shines in large, long-lived codebases where change is frequent. |
| **Dependency Injection vs. Readability** | Injecting every dependency makes constructors noisy. Inject what varies (I/O, config, strategies); hard-code what is stable (standard-library utilities). |

## DRY and the Wrong Abstraction

DRY is about *knowledge*, not text. Every business rule, fact, or algorithm should have one authoritative home. Two blocks that look alike but change for different reasons are not duplication. Merging them creates the wrong abstraction.

- **Rule of Three.** Do not suggest a shared abstraction *to remove duplication* until the same pattern appears in three independent places. Two occurrences may be coincidence. This limit applies only to duplication. Extracting a function because it makes the code read better needs no second copy.
- **Facts that must agree.** Two copies of one fact or rule that must stay in sync (a size limit, a status list, a price rule) are a finding even at two copies. When one changes and the other does not, the system contradicts itself. This is Single Source of Truth.
- **The Wrong Abstraction (Sandi Metz).** Duplication is far cheaper than the wrong abstraction. If a shared function grows `if`/`else` branches or flags to serve its different callers, suggest inlining it back so each caller can evolve on its own.

## Principle Notes

| Principle | Flag When | Do Not Flag When |
|---|---|---|
| Single Source of Truth | One constant, limit, or rule is defined in two places that must agree. | Two values happen to be equal but mean different things. |
| Separation of Concerns | One function mixes I/O, business rules, and formatting, so a change to one risks the others, or the rule cannot be tested without the I/O. Prefer pulling the rule into a plain function over adding a layer. | A short script or handler where splitting adds files but no clarity. |
| Modularity | A module's interface is nearly as complex as what it hides (a shallow module), or internals leak through the public API. | A small module with a small job. |
| Encapsulation | Callers read an object's fields to make a decision that belongs to the object, so the rule is copied across callers ("tell, don't ask"). | Plain data records with no rules of their own. |
| Law of Demeter | A caller reaches through a chain of other objects' internals, so it breaks when that structure changes. | Fluent APIs, builders, and navigation of plain data. |
| Orthogonality | One change forces edits in unrelated modules (shotgun surgery). | Changes that are really one feature. |
| Dependency Injection | Code creates its own I/O dependency (database, network, clock, random source), so it cannot be tested or configured. Suggest passing the dependency in as a parameter or function. | Stable utilities. Do not suggest an interface for a dependency with one implementation. |
| Composition Over Inheritance | Inheritance used to mix independent behaviors (class explosion), or a subclass that overrides a method to disable it. | Simple, stable hierarchies. |
| SOLID | A class changes for unrelated reasons (SRP). A subtype throws "not implemented" or callers check for a specific subtype (LSP). Implementers stub out most of an interface (ISP). Domain logic imports a concrete database or HTTP driver (DIP). | Small programs. Do not suggest extension points that no current requirement uses. |
| Convention Over Configuration | The common case needs a lot of required configuration. | Configuration that is truly different per use. |
| Command-Query Separation | A method named like a query changes state, so reading a value has a hidden side effect. | Well-known combined operations: `pop`, `next`, compare-and-swap, a clearly named `get_or_create`. |
| Code Reusability | A "generic" utility, options object, or hook with one caller. Suggest the direct code. | Code that already has several real callers. |
| Parse, Don't Validate | The same check repeats across call sites ("shotgun parsing"), or raw unchecked data travels deep after one check. Suggest parsing once at the boundary into a type that cannot hold invalid data. | Internal data that never crosses a trust or format boundary. |
| Immutability | Shared or concurrently used state is changed in place, and another holder can see the change. | Local variables and builders used by one owner. |
| Idempotency | An operation that may be retried (HTTP handler, queue consumer, scheduled job, payment) can apply twice. The idempotency key must come from the caller and stay the same on every retry. A key made inside the retried function is new each time, so the check never matches. | Pure reads, and operations that are naturally idempotent (setting a value, deleting by ID). |

## Severity Guidance

- **P1** only when the structure causes a bug now: two sources of truth that already disagree, or a retried payment or write that can apply twice.
- **P2:** knowledge duplicated or coupled so that the next change will likely miss a place. Over-built code that makes this change harder to read.
- **P3:** local structure problems with a small cost.
- Architecture findings are almost never P0, unless they cause data loss or a security hole.
