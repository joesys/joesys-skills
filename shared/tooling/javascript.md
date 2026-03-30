# JavaScript Tooling Profile

Per-language static analysis tools for JavaScript projects. Read this file alongside `shared/tooling/general.md`. All tools follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

---

## 1. Tools

### ESLint

> ⚠️ **DANGER: auto-modifies** — ESLint's `--fix` flag rewrites source files in place. NEVER pass `--fix`. Always use `--no-fix` explicitly.

| Field | Value |
|:--|:--|
| **Category** | Linter |
| **Tier** | 2 |
| **Detection** | `eslint.config.js`, `.eslintrc`, `.eslintrc.js`, `.eslintrc.cjs`, `.eslintrc.yaml`, `.eslintrc.yml`, `.eslintrc.json`, `eslintConfig` key in `package.json` |
| **Availability** | `which eslint` (Unix) / `where eslint` (Windows); also `npx eslint --version` |
| **Report-only invocation** | `npx eslint --no-fix --format json {source_paths}` |
| **Scope-to-files** | Pass file paths or glob patterns as positional arguments (e.g., `src/` or `src/**/*.js`). Multiple paths are space-separated. |
| **Output format** | JSON array of file result objects. Each object has a `messages` array with `ruleId`, `severity` (1=warn, 2=error), `message`, `line`, and `column`. |
| **Recommendation** | Best-in-class JavaScript linter. Highly configurable via plugins (e.g., `eslint-plugin-react`, `eslint-plugin-security`). The de-facto standard for JS/TS linting. |

---

### Biome

| Field | Value |
|:--|:--|
| **Category** | Linter + Formatter |
| **Tier** | 2 (lint) / 3 (format) |
| **Detection** | `biome.json`, `biome.jsonc` |
| **Availability** | `which biome` (Unix) / `where biome` (Windows); also `npx @biomejs/biome --version` |
| **Report-only invocation** | See commands below |
| **Scope-to-files** | Pass file paths or glob patterns as positional arguments after flags. Multiple paths are space-separated. |
| **Output format** | JSON object with a `diagnostics` array. Each diagnostic has `category`, `severity`, `location` (file, line, column), and `message`. |
| **Recommendation** | Popular OSS unified linter and formatter in one tool. Rust-based, extremely fast. Good ESLint + Prettier replacement for greenfield projects. |

**Lint (report-only):**

```
npx @biomejs/biome lint --no-errors-on-unmatched {source_paths}
```

**Format check (report-only):**

> ⚠️ **DANGER: auto-modifies** — Biome's `--write` flag rewrites source files in place. NEVER pass `--write`. Always use `--no-errors-on-unmatched` without `--write` for report-only format checking.

```
npx @biomejs/biome format --no-errors-on-unmatched {source_paths}
```

| Flag | Purpose |
|:--|:--|
| `--no-errors-on-unmatched` | Prevents non-zero exit when no matching files are found — avoids false failures |

---

### Prettier

> ⚠️ **DANGER: auto-modifies** — Prettier's `--write` flag rewrites source files in place. NEVER pass `--write`. Always use `--check` for report-only mode.

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | `.prettierrc`, `.prettierrc.js`, `.prettierrc.cjs`, `.prettierrc.mjs`, `.prettierrc.json`, `.prettierrc.json5`, `.prettierrc.yaml`, `.prettierrc.yml`, `.prettierrc.toml`, `prettier.config.js`, `prettier.config.cjs`, `prettier.config.mjs`, `prettier` key in `package.json` |
| **Availability** | `which prettier` (Unix) / `where prettier` (Windows); also `npx prettier --version` |
| **Report-only invocation** | `npx prettier --check {source_paths}` |
| **Scope-to-files** | Pass file paths or glob patterns as positional arguments (e.g., `"src/**/*.js"`). Quote glob patterns to prevent shell expansion. |
| **Output format** | Human-readable text. Lists files that differ from Prettier's formatting with one line per file. Exits non-zero if any file would be changed. No structured JSON output available. |
| **Recommendation** | Best-in-class opinionated formatter. Eliminates formatting debates — pairs naturally with ESLint. Standard in the JS ecosystem. |

---

### Semgrep (JavaScript)

> ⚠️ **DANGER: auto-modifies** — Semgrep's `--autofix` flag rewrites source files in place. NEVER omit `--no-autofix`. Always pass `--no-autofix` explicitly.

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `.semgrep.yml`, `.semgrep/` directory, `semgrep` in CI config files |
| **Availability** | `which semgrep` (Unix) / `where semgrep` (Windows) |
| **Report-only invocation** | `semgrep scan --config auto --lang javascript --json --no-autofix --quiet {source_paths}` |
| **Scope-to-files** | Pass file paths or directories as positional arguments after flags. |
| **Output format** | JSON object with a `results` array. Each result contains `check_id` (rule), `path` (file), `start.line`, `extra.severity`, and `extra.message`. |
| **Recommendation** | Best-in-class for JavaScript security scanning. Covers XSS, injection, insecure deserialization, prototype pollution, and more via the `auto` ruleset. See also `shared/tooling/general.md` for the multi-language Semgrep profile. |

---

### njsscan

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `.njsscan` config file, or `njsscan` in CI config files |
| **Availability** | `which njsscan` (Unix) / `where njsscan` (Windows) |
| **Report-only invocation** | `njsscan --json {source_paths}` |
| **Scope-to-files** | Pass file paths or directories as positional arguments. Multiple paths are space-separated. |
| **Output format** | JSON object with findings grouped by rule name. Each rule entry contains `metadata` (description, severity, CWE, OWASP) and `files` array with `file_path`, `match_lines`, and `match_string`. |
| **Recommendation** | Popular OSS security scanner purpose-built for Node.js. Detects Node.js-specific vulnerabilities (e.g., `eval`, `child_process`, unsafe redirects, JWT issues). Complements Semgrep's broader ruleset. Does not modify source files. |

---

## 2. Build-Integrated Analysis Patterns

### Package Scripts

Look for these keys in the `scripts` section of `package.json`:

| Script Key | Signal |
|:--|:--|
| `"lint"` | ESLint or Biome lint wired into the project workflow |
| `"format"` | Prettier or Biome format wired into the project workflow |
| `"lint:check"` / `"format:check"` | Explicit check-only variants (good practice signal) |

### Pre-Commit Hooks

- **lint-staged** — Detection: `lint-staged` key in `package.json`, or `.lintstagedrc` / `lint-staged.config.js` file. Runs linters/formatters on staged files only.
- **Husky** — Detection: `.husky/` directory. Typically paired with lint-staged to enforce lint/format on commit.

### CI-Integrated Analysis

Look for `eslint`, `biome`, or `prettier --check` calls in CI workflow files (`.github/workflows/*.yml`, `.gitlab-ci.yml`, etc.).

### Type Checking in JavaScript

JavaScript projects can opt into lightweight type checking without migrating to TypeScript:

- **`// @ts-check`** at the top of a `.js` file — enables TypeScript's type checker for that file via JSDoc annotations.
- **`tsconfig.json` with `"checkJs": true`** — enables project-wide JS type checking via the TypeScript compiler (`tsc --noEmit`).

Detect these signals to record partial type-checking coverage even in non-TypeScript projects.

---

## 3. Gap Analysis

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No linter | **ESLint** — most configurable, widest plugin ecosystem, industry standard | **Biome** — unified linter + formatter, single tool, zero config |
| No formatter | **Prettier** — opinionated, battle-tested, integrates with ESLint | **Biome** — also handles formatting, faster than Prettier |
| No security scanner | **Semgrep** — broad JS security ruleset, multi-language | **njsscan** — Node.js-specific patterns, purpose-built, lightweight |
| No type checking | Consider **TypeScript migration** for long-term correctness; short-term: add `// @ts-check` + JSDoc annotations | Enable `"checkJs": true` in `tsconfig.json` for project-wide coverage without full TS migration |
