# Story Readability

## Definition

Story Readability measures how well code reads as a coherent narrative. It goes beyond mechanical readability (naming conventions, comment density, nesting depth) to assess whether a developer can scan a function and immediately understand its story — the beginning, middle, and end — without diving into implementation details.

This criterion is separate from Readability (criterion 7), which measures mechanical parsing ease. Story Readability measures narrative quality.

## Core Reference

Read `shared/story-readability.md` for the full dimension definitions, weights, calibration examples, and scoring protocol. This file adds audit-specific measurement guidance and grading rubric.

## Concrete Signals

**Positive signals:**
- Functions read as sequences of named, well-ordered steps
- Paragraph spacing separates logical phases
- Call sites are self-documenting (enums over bools, descriptive arguments)
- Logical phases are extracted into named chunks even without duplication
- Each function operates at a single level of abstraction
- Guard clauses and early returns keep the happy path flat
- Comments explain business rationale, not code mechanics

**Negative signals:**
- Functions mix high-level orchestration with low-level details
- No visual separation between logical phases
- Boolean blindness at call sites (`spawn(world, true, false, true)`)
- Long functions with multiple interleaved responsibilities
- Deep nesting burying the happy path
- Parrot comments that restate what the code does
- Dense one-liners, double negatives, chained ternaries

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Narrative flow score | Qualitative assessment of function-level story structure | Author agent + `shared/story-readability.md` calibration |
| Naming intent score | Check for boolean blindness, self-documenting call sites | Author agent qualitative |
| Cognitive chunking score | Check if multi-phase functions are extracted into named steps | Author agent qualitative |
| Abstraction consistency | Check for SLAP violations — mixed abstraction levels | Author agent qualitative |
| Average function length | Quantitative — shorter functions correlate with focus | `compute_structure.py` |
| Max nesting depth | Quantitative — deep nesting hurts structural clarity | `compute_structure.py` |
| Comment quality ratio | Qualitative — % of comments that explain "why" vs "what" | Author agent qualitative |

**Quantitative floor:** The Structural and Quality agent metrics constrain the qualitative scores:

| Quantitative Signal | Dimension Cap |
|---|---|
| Average function length > 50 lines | Function Focus capped at 4/10 |
| Max nesting depth > 6 | Structural Clarity capped at 4/10 |
| Comment density < 2% | Documentation Quality capped at 5/10 |
| Naming convention violations > 20% of identifiers | Naming as Intent capped at 5/10 |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Exemplary narrative quality. Functions read like well-written prose. All 8 dimensions score 9+. Calibration: comparable to the `process_dawn_phase` gold standard. |
| A | Strong narrative structure. Most functions tell clear stories. Minor rough spots in 1-2 dimensions. Weighted score 88-94. |
| B | Generally readable with identifiable narrative structure. Some functions mix abstraction levels or lack cognitive chunking. Weighted score 72-87. |
| C | Mixed quality. Some modules tell clear stories, others require effort to follow. Weighted score 56-71. |
| D | Poor narrative structure. Functions frequently mix concerns, naming is inconsistent, minimal chunking. Weighted score 45-55. |
| F | No discernible narrative structure. Dense, monolithic functions. Cryptic naming. No documentation. Weighted score below 45. |

## Language-Aware Notes

See `shared/story-readability.md` § Language-Aware Notes for per-language guidance on what's idiomatic vs. what's a narrative violation.
