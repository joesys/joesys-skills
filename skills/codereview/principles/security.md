# Security Principles

Security asks: can someone outside the trust boundary make this code do something it should not? Use this file as a lens, not a checklist. Treat every value from outside as hostile: HTTP requests, uploaded files, webhooks, CLI arguments, environment variables, queue messages, and stored data that a user wrote earlier. When you cannot see where a value comes from, treat it as untrusted.

## Quick Diagnostic Guide

Use these names as the `[Principle Name]` in findings.

| Principle | Look For | Safe Pattern |
|---|---|---|
| Hardcoded Secrets | API keys, tokens, passwords, or private keys as string literals, including in config and sample files. Common shapes: `sk-...`, `ghp_...`, `AKIA...`, `-----BEGIN ... PRIVATE KEY-----`, or `password = "..."`. | Load from the environment or a secrets manager. Treat any committed secret as leaked: rotate it. Removing it from history is not enough. |
| Injection (SQL/Command/XSS) | Untrusted data built into SQL, shell commands, HTML, templates, or queries by concatenation, formatting, or interpolation. Unsafe deserialization of untrusted bytes (native object formats, unsafe YAML loaders). | Parameterized queries. Argument lists with no shell. Auto-escaping templates. Safe loaders. Hand-written escaping is not a fix. |
| Input Sanitization | External values used without type, range, length, or format checks. No size limit on uploads or strings. URLs fetched without checking scheme and host (server-side request forgery). Denylists. | Validate at the boundary. Prefer allowlists: state what is allowed. |
| Authentication & Session Management | Tokens (JWT and similar) decoded without verifying the signature, expiry, issuer, and audience, or with the algorithm taken from the token itself (`alg: none`). Passwords stored with fast hashes (MD5, SHA-1, SHA-256 alone). Tokens made from a non-cryptographic random source or a timestamp. Secrets compared with normal string equality (timing attack). A new endpoint or object lookup with no authorization check for the current user. Session cookies without `Secure`, `HttpOnly`, and `SameSite`. | A well-tested library with verification turned on. bcrypt, argon2, or scrypt for passwords. A cryptographic random source. Constant-time comparison. An ownership check on every object a user asks for. |
| Sensitive Data Exposure | Secrets or personal data in logs, error responses, stack traces sent to clients, or URLs. Logging whole request headers or bodies. | Log request IDs, status codes, and timing. Send clients a generic error with a correlation ID; keep details on the server. |
| Dependency Security | A missing lockfile, loose version ranges, a known-vulnerable version, or a new dependency with no sign of maintenance. | See § Dependency Security below. |
| Path Traversal | A user-supplied name used in a file path. Archive entries extracted without checking their paths ("zip slip"). | Resolve the path to its canonical form. Then confirm it is inside the base directory by comparing path components. A plain string prefix check is itself a bug: `/srv/uploads-evil` starts with `/srv/uploads`. |
| Insecure Defaults | Debug mode on, CORS `*` with credentials, TLS verification turned off, `ALLOWED_HOSTS = ["*"]`, a default secret key, `http://` in production config. | Secure by default. Require an explicit opt-out for development. Refuse to start in production with insecure settings. |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **Security vs. Developer Experience** | Strict security controls (rotating secrets, MFA, short token TTLs) slow developers down. Use generous timeouts and relaxed policies in local dev; enforce strict policies in staging and production. Never compromise production security for convenience. |
| **Input Sanitization vs. Usability** | Overly strict validation rejects legitimate input and frustrates users. Validate structure and type strictly, but be lenient with formatting (trim whitespace, normalize case). Reject what is dangerous, not what is unusual. |
| **Sensitive Data Exposure vs. Observability** | Logging is essential for debugging, but logs are a prime target for credential leaks. Log request IDs, status codes, and timing — never tokens, passwords, or PII. Use structured logging with explicit field allowlists. |
| **Dependency Security vs. Stability** | Updating dependencies can introduce regressions. Pin exact versions in lockfiles for reproducibility, but run automated audit tools (`pip-audit`, `npm audit`) on every CI build. Update proactively, not reactively after a CVE hits production. |
| **Hardcoded Secrets vs. Configuration Complexity** | Externalizing every secret adds infrastructure overhead (vaults, env management). The overhead is always justified — a leaked secret in a public repo is an instant, irreversible breach. Start with environment variables; graduate to a secrets manager as scale demands. |
| **Insecure Defaults vs. Quick Prototyping** | Secure defaults can make initial development feel sluggish (TLS setup, CORS restrictions). Prototype behind `--dev` flags with relaxed settings, but ensure production builds fail if insecure overrides are still active. |

## Dependency Security

Check for missing lockfiles (`requirements.lock`, `poetry.lock`, `package-lock.json`) and for dependencies without upper-bound version constraints. Use results from `pip-audit`, `npm audit`, or `cargo audit` only if the Safety Gate in `shared/tooling-registry.md` already approved and ran them. Otherwise, check lockfiles and version constraints statically. If release dates are available, flag dependencies that have not been updated in over a year.

## Severity Guidance

- **P0:** exploitable from outside with real impact. Examples: injection, an authentication or authorization bypass, a token accepted without signature checks, a live secret in source, path traversal that reads or writes arbitrary files, code execution through deserialization.
- **P1:** exploitable with some precondition, or a real leak. Examples: secrets or personal data in logs, weak password hashing, an insecure default that can reach production, a known-vulnerable dependency on a used code path.
- **P2:** a defense-in-depth gap, such as a missing lockfile or a missing cookie flag on a low-value cookie.

## When Not to Flag

- Obviously fake credentials in tests and fixtures.
- Development-only settings that cannot reach production. Say what keeps them out.
- Attacks that need someone who already controls the server or the build.
- Code outside the change, unless the change exposes it to new input.
