# General Software Engineering Benchmarks

Cross-language industry benchmarks used as fallback when no language-specific data is available.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (per function avg) | ≤10 | Good | Carnegie Mellon SEI [^1] |
| Cyclomatic complexity (per function avg) | 11-20 | Moderate risk | Carnegie Mellon SEI [^1] |
| Cyclomatic complexity (per function avg) | >20 | High risk | Carnegie Mellon SEI [^1] |
| Cyclomatic complexity (per function max) | ≤15 | Good | SonarQube defaults [^2] |

## Size

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Function length (median) | ≤50 lines | Good | Clean Code, Robert C. Martin [^3] |
| Function length (p90) | ≤100 lines | Acceptable | CAST Research Labs [^4] |
| File length | ≤500 lines | Good | Clean Code [^3] |
| File length | ≤1000 lines | Acceptable | CAST Research Labs [^4] |

## Nesting & Structure

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Nesting depth (max) | ≤4 | Good | Linux kernel coding standard [^5] |
| Nesting depth (max) | ≤6 | Acceptable | MISRA C guidelines [^6] |
| Comment density | 10-20% | Good | CAST Research Labs [^4] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test pass rate | 100% | Required | Industry standard |
| Test-to-source file ratio | ≥0.8 | Good | Google Engineering Practices [^7] |
| Test-to-source file ratio | ≥0.5 | Acceptable | Industry median [^4] |

## Quality

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Duplicate code | <5% | Good | SonarQube defaults [^2] |
| Duplicate code | <10% | Acceptable | SonarQube defaults [^2] |
| Type annotation coverage | ≥80% | Good | Industry trend [^8] |

## Velocity

| Metric | Context | Source |
|---|---|---|
| Commit frequency | ≥1/day (active project) | DORA metrics [^9] |
| Bus factor | ≥2 per module | Best practice [^10] |

## Story Readability

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Weighted story score (8 dimensions) | ≥ 88 | Good (A) | Calibrated to shared/story-readability.md |
| Weighted story score (8 dimensions) | ≥ 72 | Acceptable (B) | Calibrated to shared/story-readability.md |
| Average function length (narrative proxy) | ≤ 20 lines | Good | Clean Code, Robert C. Martin [^3] |
| Max nesting depth (structural clarity proxy) | ≤ 3 | Good | Linux kernel coding standard [^5] |

## References

[^1]: Carnegie Mellon SEI, "A Complexity Measure," Thomas J. McCabe, IEEE Trans. Software Engineering, 1976
[^2]: SonarQube, "Metric Definitions," sonarqube.org/docs
[^3]: Robert C. Martin, "Clean Code: A Handbook of Agile Software Craftsmanship," Prentice Hall, 2008
[^4]: CAST Research Labs, "CRASH Report: Software Quality Norms," cast.com
[^5]: Linux Kernel Coding Style, kernel.org/doc/html/latest/process/coding-style.html
[^6]: MISRA C:2012, "Guidelines for the Use of the C Language in Critical Systems"
[^7]: Google Engineering Practices, google.github.io/eng-practices/
[^8]: MyPy adoption trends, Python Developer Survey, JetBrains 2024
[^9]: DORA, "Accelerate: State of DevOps," dora.dev
[^10]: "Assessing the Bus Factor of Git Repositories," Avelino et al., SANER 2016
