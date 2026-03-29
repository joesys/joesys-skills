# JavaScript Benchmarks

JavaScript-specific quality thresholds. Shares many metrics with TypeScript but lacks type safety metrics.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤10 | Good | ESLint complexity rule [^1] |
| Cyclomatic complexity (max) | ≤20 | Acceptable | SonarQube JS plugin [^2] |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Line length | ≤100 chars | Good | Prettier default [^3] |
| Function length (median) | ≤30 lines | Good | ESLint max-lines-per-function [^1] |
| File length | ≤400 lines | Good | Airbnb style guide [^4] |
| Nesting depth | ≤4 | Good | SonarQube defaults [^2] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test runner | Jest, Vitest, or Mocha | Standard | State of JS Survey [^5] |
| Test-to-source ratio | ≥0.8 | Good | Industry standard |

## Dependencies

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| npm audit clean | 0 high/critical | Required | npm audit [^6] |
| Lock file present | package-lock.json or yarn.lock | Required | npm docs [^6] |

## Quality Signals

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| ESLint configured | .eslintrc or eslint.config present | Expected | Airbnb style guide [^4] |
| `"use strict"` or ESM | Module system defined | Expected | Node.js best practice [^7] |

## References

[^1]: ESLint, "Rules Reference," eslint.org/docs/latest/rules/
[^2]: SonarQube, "JavaScript Analysis," sonarqube.org
[^3]: Prettier, "Options," prettier.io/docs/en/options.html
[^4]: Airbnb, "JavaScript Style Guide," github.com/airbnb/javascript
[^5]: State of JS Survey, stateofjs.com
[^6]: npm, "npm audit," docs.npmjs.com/cli/audit
[^7]: Node.js, "Best Practices," nodejs.org/en/docs/guides/
