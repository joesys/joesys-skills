# Maintainability

## Definition

Maintainability measures how easily the codebase can be understood, modified, and corrected by developers who did not write the original code. It is the single largest factor in long-term development cost — every future change pays the tax of poor maintainability.

## Concrete Signals

**Positive signals:**
- Short, focused functions (≤25 lines typical)
- Low cyclomatic complexity (≤10 branches per function)
- Guard clauses that flatten nesting instead of deep if/else chains
- Meaningful, self-documenting variable and function names
- DRY — shared logic extracted, no copy-pasted blocks
- SLAP — each function operates at a single level of abstraction
- Type annotations on function signatures

**Negative signals:**
- Functions exceeding 50 lines
- Cyclomatic complexity >15 per function
- Nesting depth >4 levels
- Magic numbers and string literals without named constants
- Duplicated code blocks (3+ repeated patterns of 5+ lines)
- Mixed abstraction levels within a single function
- Commented-out code blocks retained in production code
- TODO/FIXME/HACK markers accumulating without resolution

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Cyclomatic complexity (avg, max, distribution) | Count branch keywords per function | `compute_complexity.py` |
| Function length (median, p90, max) | Count lines per function body | `compute_structure.py` |
| Nesting depth (median, p90, max) | Track max indent/brace depth per function | `compute_structure.py` |
| Comment density | comment_lines / total_lines | `compute_structure.py` |
| Type annotation coverage | annotated_functions / total_functions | `compute_structure.py` |
| Files over 500 lines | Count files exceeding threshold | `compute_structure.py` |
| Functions over 50 lines | Count functions exceeding threshold | `compute_structure.py` |
| TODO/FIXME/HACK count | Grep for markers, group by theme | Agent qualitative scan |
| Duplicated code signals | Look for 3+ repeated patterns | Agent qualitative scan |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | CC avg ≤5, median function ≤15 lines, max nesting ≤3, type coverage >80%, zero duplicates |
| A | CC avg ≤8, median function ≤20 lines, max nesting ≤4, type coverage >60% |
| B | CC avg ≤10, median function ≤30 lines, max nesting ≤5 |
| C | CC avg ≤15, median function ≤50 lines, or nesting ≤6 |
| D | CC avg ≤20, or functions >100 lines common, or deep nesting pervasive |
| F | CC avg >20, pervasive long functions, deep nesting, extensive duplication |

Grade = minimum across all measured metrics. One failing metric caps the criterion grade.

## Language-Aware Notes

- **Rust:** Pattern matching (`match` with multiple arms) inflates CC without indicating poor maintainability. Adjust CC baseline upward by ~20% for Rust. The ownership model adds apparent complexity that actually improves maintainability.
- **Python:** List comprehensions can pack significant complexity into one line. Flag comprehensions with >2 conditions or nested comprehensions as complexity signals even though they don't increase CC.
- **Go:** Idiomatic error handling (`if err != nil { return err }`) adds 2-3 CC points per function. Adjust baseline CC upward by +3 for Go. Focus on non-error-handling complexity.
- **GDScript:** `_ready()` and `_process()` lifecycle callbacks tend to be long by Godot convention. Weight function length less heavily for these specific functions.
- **C++:** Templates and operator overloading create hidden complexity not captured by CC. Header inclusion depth is an additional maintainability signal.
- **TypeScript:** Generics with complex type constraints increase cognitive load without affecting CC. Note heavily generic code as a maintainability concern.
