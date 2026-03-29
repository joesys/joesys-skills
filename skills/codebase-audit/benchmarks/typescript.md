# TypeScript Benchmarks

TypeScript-specific quality thresholds.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤10 | Good | ESLint complexity rule default [^1] |
| Cyclomatic complexity (max) | ≤20 | Acceptable | SonarQube TS plugin [^2] |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Line length | ≤100 chars | Good | Prettier default [^3] |
| Function length (median) | ≤30 lines | Good | ESLint max-lines-per-function [^1] |
| File length | ≤400 lines | Good | Angular style guide [^4] |
| Nesting depth | ≤4 | Good | SonarQube defaults [^2] |

## Type Safety

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| `strict: true` in tsconfig | Enabled | Required | TypeScript best practice [^5] |
| `any` usage | <5% of type annotations | Good | TypeScript ESLint [^6] |
| `noUncheckedIndexedAccess` | Enabled | Recommended | TypeScript 4.1+ [^5] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test runner | Jest or Vitest | Standard | State of JS Survey [^7] |
| Test-to-source ratio | ≥0.8 | Good | Industry standard |

## Dependencies

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| npm audit clean | 0 high/critical | Required | npm audit [^8] |
| Lock file present | package-lock.json or pnpm-lock.yaml | Required | npm documentation [^8] |

## References

[^1]: ESLint, "Rules Reference," eslint.org/docs/latest/rules/
[^2]: SonarQube, "TypeScript Analysis," sonarqube.org
[^3]: Prettier, "Options," prettier.io/docs/en/options.html
[^4]: Angular, "Style Guide," angular.io/guide/styleguide
[^5]: TypeScript, "TSConfig Reference," typescriptlang.org/tsconfig
[^6]: typescript-eslint, "Rules," typescript-eslint.io/rules/
[^7]: State of JS Survey, stateofjs.com
[^8]: npm, "npm audit," docs.npmjs.com/cli/audit
