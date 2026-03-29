# Rust Benchmarks

Rust-specific quality thresholds. Rust's ownership model and type system shift some quality concerns to compile time.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤12 | Good | Adjusted for pattern matching [^1] |
| Cyclomatic complexity (max) | ≤25 | Acceptable | Clippy cognitive_complexity [^2] |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Function length (median) | ≤40 lines | Good | Rust API Guidelines [^3] |
| File length | ≤600 lines | Good | Rust community convention |
| Nesting depth | ≤5 | Good | Clippy defaults [^2] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test runner | `cargo test` | Standard | Built-in [^4] |
| Test-to-source ratio | ≥0.6 | Good | Adjusted for type safety [^1] |

## Dependencies

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| cargo audit clean | 0 vulnerabilities | Required | cargo-audit [^5] |
| Cargo.lock committed (binaries) | Present for binaries | Required | Cargo docs [^4] |

## References

[^1]: Rust compiler design — pattern matching and error handling inflate CC without indicating poor quality
[^2]: Clippy, "Lints," rust-lang.github.io/rust-clippy/
[^3]: Rust API Guidelines, rust-lang.github.io/api-guidelines/
[^4]: The Cargo Book, doc.rust-lang.org/cargo/
[^5]: cargo-audit, "Security Advisory Database," rustsec.org
