# Rust Tooling Profile

Tools for Rust projects. Read this file alongside `shared/tooling/general.md`. All tools follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

---

## 1. Tools

### clippy (Tier 1 / 2)

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer / Linter |
| **Tier** | 1 (bug-catching lints) / 2 (style lints) |
| **Detection** | Always available with the Rust toolchain. Config indicators: `[lints.clippy]` section in `Cargo.toml` (Rust 1.74+), `clippy.toml`, `.clippy.toml` |
| **Availability** | `rustup component list --installed \| grep clippy` or `cargo clippy --version` |
| **Report-only invocation** | `cargo clippy --message-format json -- -W clippy::all` |
| **Scope-to-files** | `--package {pkg}` to target a specific workspace crate. Clippy operates at the crate level — individual file scoping is not supported. |
| **Output format** | JSON lines (one object per diagnostic). Key fields: `message.level`, `message.message`, `message.spans[].file_name`, `message.spans[].line_start` |
| **Recommendation** | Best-in-class Rust linter. Bundled with the toolchain — no separate install needed. **NEVER pass `--fix`**: that flag auto-applies suggestions and modifies source files. |

---

### clippy pedantic (Tier 2)

| Field | Value |
|:--|:--|
| **Category** | Linter (stricter — opt-in only) |
| **Tier** | 2 |
| **Detection** | `#![warn(clippy::pedantic)]` or `#![deny(clippy::pedantic)]` in `lib.rs` / `main.rs`; or `pedantic` key in `clippy.toml` / `.clippy.toml`; or `pedantic = "warn"` under `[lints.clippy]` in `Cargo.toml` |
| **Availability** | Same as clippy — always available with the Rust toolchain |
| **Report-only invocation** | `cargo clippy --message-format json -- -W clippy::pedantic` |
| **Scope-to-files** | `--package {pkg}` for workspace packages |
| **Output format** | JSON lines, same schema as clippy above |
| **Recommendation** | Run only when the project has explicitly opted in (detection required before queuing). Pedantic lints are noisy by design; opt-in signals that the team accepts the stricter bar. |

---

### rustfmt (Tier 3)

> ⚠️ **DANGER: auto-modifies** — running `cargo fmt` WITHOUT `--check` rewrites ALL source files in place. ALWAYS use `--check` for report-only mode.

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | Always available with the Rust toolchain. Config indicators: `rustfmt.toml`, `.rustfmt.toml` |
| **Availability** | `rustup component list --installed \| grep rustfmt` or `cargo fmt --version` |
| **Report-only invocation** | `cargo fmt --check` |
| **Scope-to-files** | `--package {pkg}` to restrict to a workspace crate. No per-file scoping is available via `cargo fmt`. |
| **Output format** | Diff output to stdout; exits with code `1` if any file would be reformatted, `0` if everything is already formatted |
| **Recommendation** | Best-in-class Rust formatter. Bundled with the toolchain. Add `cargo fmt --check` to CI to enforce formatting without modifying files in the pipeline. |

---

### cargo-audit (Tier 4)

| Field | Value |
|:--|:--|
| **Category** | Security Scanner — dependency vulnerability auditing |
| **Tier** | 4 |
| **Detection** | `Cargo.lock` must exist (required for auditing). Also check for `cargo audit` in CI config files. |
| **Availability** | `cargo audit --version` (separate install via `cargo install cargo-audit`) |
| **Report-only invocation** | `cargo audit --json` |
| **Scope-to-files** | N/A — audits the full dependency tree declared in `Cargo.lock`; source-file scoping does not apply |
| **Output format** | JSON object with `vulnerabilities.found` (integer count) and `vulnerabilities.list` (array of advisory objects with `id`, `package`, `title`, `severity`) |
| **Recommendation** | Best-in-class for Rust dep vulnerability scanning — queries the RustSec Advisory Database. Requires `Cargo.lock` (always present for binaries; may be git-ignored for libraries). Does not modify anything. |

---

### cargo-deny (Tier 4)

| Field | Value |
|:--|:--|
| **Category** | Security Scanner — dependency policy enforcement |
| **Tier** | 4 |
| **Detection** | `deny.toml` in the project root |
| **Availability** | `cargo deny --version` (separate install via `cargo install cargo-deny`) |
| **Report-only invocation** | `cargo deny check --format json` |
| **Scope-to-files** | N/A — checks the full dependency graph; source-file scoping does not apply |
| **Output format** | JSON with results grouped by check type: `advisories` (known CVEs), `bans` (disallowed crates), `licenses` (license policy), `sources` (allowed registries/git sources) |
| **Recommendation** | Popular OSS complement to cargo-audit. Broader scope: enforces license compliance and bans unwanted crates in addition to CVE checking. Requires a `deny.toml` config; skip if absent. |

---

## 2. Build-Integrated Analysis Patterns

These patterns indicate that static analysis is already woven into the project's workflow. The orchestrator detects them during **Step 5 — Detect Build-Integrated Analysis** and records them for grading.

### Compiler-Level Lint Attributes

Look for these in `src/lib.rs` or `src/main.rs` (crate root):

| Pattern | Signal |
|:--|:--|
| `#![deny(clippy::all)]` | Clippy errors break the build |
| `#![warn(clippy::pedantic)]` | Pedantic lints opted in |
| `#![deny(warnings)]` | All compiler warnings are fatal |
| `#![deny(unsafe_code)]` | Unsafe code banned at the crate level |

### Cargo.toml Lint Configuration (Rust 1.74+)

`[lints.clippy]` section in `Cargo.toml` sets workspace-wide lint levels without requiring inline attributes.

### CI-Integrated Analysis

Look for these patterns in CI config files (`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, etc.):

| Pattern | Signal |
|:--|:--|
| `cargo clippy` in CI | Clippy runs in the pipeline |
| `cargo fmt --check` in CI | Formatting enforced in CI |
| `cargo audit` in CI | Vulnerability scanning in pipeline |
| `RUSTFLAGS="-D warnings"` | All warnings treated as errors |
| `cargo deny check` in CI | Dep policy enforced in pipeline |

---

## 3. Gap Analysis

When the orchestrator identifies missing tooling categories, recommend alternatives using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No linter / no clippy config | Add `#![warn(clippy::all)]` to crate root + `cargo clippy` to CI | — (clippy is built into the toolchain) |
| No formatter check | Add `cargo fmt --check` to CI | — (rustfmt is built into the toolchain) |
| No dependency vulnerability audit | **cargo-audit** — queries RustSec DB, simple setup | **cargo-deny** — broader: CVEs + license + bans |
| No unsafe code policy | Add `#![deny(unsafe_code)]` to crate root | **cargo geiger** — counts unsafe usage across the dep tree |
