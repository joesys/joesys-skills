# Story Readability

Story Readability measures how well code reads as a narrative: can a reader scan a function and follow its steps without reading the details? It is separate from Readability (criterion 7), which measures mechanical parsing ease.

Read `../shared/story-readability.md` for the 8 dimensions, their weights, the calibration examples, the scoring protocol, and the language-aware notes. This file adds only the audit's quantitative floor and grading rubric.

## Quantitative Floor

The Structural and Quality agent metrics constrain the qualitative scores:

| Quantitative Signal | Dimension Cap |
|---|---|
| Average function length > 50 lines | Function Focus capped at 4/10 |
| Max nesting depth > 6 | Structural Clarity capped at 4/10 |
| Comment density < 2% | Documentation Quality capped at 5/10 |
| Naming convention violations > 20% of identifiers | Naming as Intent capped at 5/10 |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Exemplary narrative quality. Functions read like well-written prose. Weighted score 95-100 (see `../shared/story-readability.md` § Grade Mapping). Calibration: comparable to the `process_dawn_phase` gold standard. |
| A | Strong narrative structure. Most functions tell clear stories. Minor rough spots in 1-2 dimensions. Weighted score 88-94. |
| B | Generally readable with identifiable narrative structure. Some functions mix abstraction levels or lack cognitive chunking. Weighted score 72-87. |
| C | Mixed quality. Some modules tell clear stories, others require effort to follow. Weighted score 56-71. |
| D | Poor narrative structure. Functions frequently mix concerns, naming is inconsistent, minimal chunking. Weighted score 45-55. |
| F | No discernible narrative structure. Dense, monolithic functions. Cryptic naming. No documentation. Weighted score below 45. |

The audit grading scale has no plus grades. A shared-scale B+ (80-87) grades as B here, and a shared-scale C+ (64-71) grades as C. The score bands above already include them.
