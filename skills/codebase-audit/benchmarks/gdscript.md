# GDScript Benchmarks

GDScript-specific quality thresholds for Godot Engine projects.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤10 | Good | General benchmark adapted [^1] |
| Cyclomatic complexity (max) | ≤20 | Acceptable | GDScript convention |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Function length (median) | ≤40 lines | Good | GDScript style guide [^2] |
| File length | ≤500 lines | Good | Node-per-script convention [^3] |
| Nesting depth | ≤4 | Good | General benchmark [^1] |
| Line length | ≤100 chars | Good | GDScript style guide [^2] |

## Structure

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| class_name declarations | Present on all scripts | Expected | GDScript style guide [^2] |
| Signal usage (vs direct calls) | Signals for cross-node communication | Good | Godot best practices [^3] |
| Type hints | ≥70% of function signatures | Good | GDScript 2.0 best practice [^2] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test framework | gdUnit4 or GUT | Standard | Godot community [^4] |
| Test-to-source ratio | ≥0.3 | Acceptable | Adjusted for game development [^4] |

## Story Readability

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Weighted story score | ≥ 88 | Good (A) | Calibrated to shared/story-readability.md |
| Weighted story score | ≥ 72 | Acceptable (B) | Calibrated to shared/story-readability.md |
| Signal naming clarity | verb_noun pattern | Good | Godot style guide |

## References

[^1]: Carnegie Mellon SEI — adapted general benchmarks
[^2]: Godot Engine, "GDScript Style Guide," docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html
[^3]: Godot Engine, "Best Practices," docs.godotengine.org/en/stable/tutorials/best_practices/
[^4]: gdUnit4, "GDScript Unit Testing," github.com/MikeSchulze/gdUnit4
