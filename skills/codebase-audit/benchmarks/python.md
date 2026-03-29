# Python Benchmarks

Python-specific quality thresholds. These override general benchmarks where they differ.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤8 | Good | Radon tool defaults [^1] |
| Cyclomatic complexity (max) | ≤15 | Acceptable | Radon tool defaults [^1] |
| Comprehension complexity | ≤2 conditions | Good | PEP 8 consensus [^2] |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Line length | ≤88 chars | Good | Black formatter default [^3] |
| Function length (median) | ≤30 lines | Good | PEP 8 consensus [^2] |
| File length | ≤500 lines | Good | Django style guide [^4] |
| Nesting depth | ≤4 | Good | Pylint defaults [^5] |

## Type Annotations

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Type annotation coverage | ≥90% | Excellent | MyPy strict mode [^6] |
| Type annotation coverage | ≥70% | Good | Industry trend [^7] |
| Type annotation coverage | ≥40% | Acceptable | Gradual typing practice [^6] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test runner | pytest | Standard | Python Developers Survey 2024 [^7] |
| Test-to-source ratio | ≥0.8 | Good | Industry standard |
| Coverage (line) | ≥80% | Good | Coverage.py convention [^8] |

## Dependencies

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| pip-audit clean | 0 vulnerabilities | Required | pip-audit / safety [^9] |
| Lock file present | poetry.lock or requirements.txt pinned | Good | PEP 665 [^10] |

## References

[^1]: Radon, "Cyclomatic Complexity," radon.readthedocs.io
[^2]: PEP 8, "Style Guide for Python Code," peps.python.org/pep-0008/
[^3]: Black, "The Uncompromising Code Formatter," black.readthedocs.io
[^4]: Django, "Coding Style," docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/
[^5]: Pylint, "Messages Overview," pylint.readthedocs.io
[^6]: MyPy, "Type Checking Python," mypy.readthedocs.io
[^7]: JetBrains, "Python Developers Survey 2024," jetbrains.com/lp/python-developers-survey-2024/
[^8]: Coverage.py, "Coverage.py Documentation," coverage.readthedocs.io
[^9]: pip-audit, "Auditing Python Dependencies," pypi.org/project/pip-audit/
[^10]: PEP 665, "A file format to record Python dependencies," peps.python.org/pep-0665/
