# Security

## Definition

Security measures the codebase's resistance to common vulnerabilities and attacks. It covers static code patterns only (OWASP Top 10 and language-specific patterns), not penetration testing or dynamic analysis.

## Signals to Look For

- Hardcoded secrets (API keys, passwords, tokens) in source.
- Injection: SQL built by string concatenation or interpolation, command injection through unsanitized subprocess input, XSS through unescaped user content, path traversal through unsanitized file paths.
- Missing input validation at system boundaries such as API endpoints.
- Sensitive data (passwords, tokens, PII) written to logs.
- Weak authentication or session handling, and insecure defaults (debug mode in production, permissive CORS).
- Outdated dependencies with known CVEs.

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Hardcoded secrets | Search for API_KEY, password, secret, token patterns | Quality agent |
| SQL injection patterns | Search for string formatting in SQL queries | Architecture agent |
| Command injection patterns | Search for subprocess/exec with unsanitized input | Architecture agent |
| Dependency vulnerabilities | Run npm audit, pip-audit, cargo audit | Architecture agent (live) |
| Input validation presence | Check API endpoints for validation decorators/middleware | Architecture agent |
| Auth patterns | Check for authentication middleware, session management | Architecture agent |
| Sensitive data in logs | Search for logging of credentials, tokens, PII | Quality agent |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Zero secrets in code, no injection patterns, deps clean, input validation comprehensive, auth solid |
| A | No secrets, no injection, deps mostly clean, good input validation |
| B | No critical vulnerabilities, minor dependency issues, some validation gaps |
| C | Some security concerns (missing validation, outdated deps with medium CVEs) |
| D | Hardcoded secrets found, or injection patterns present, or critical CVEs in deps |
| F | Multiple critical vulnerabilities, secrets in code, no input validation, injection patterns |

## Language-Aware Notes

- **Rust:** Memory safety eliminates entire vulnerability classes (buffer overflow, use-after-free). Focus on logic-level security (auth, injection, secrets).
- **Python:** SQL injection via f-strings in queries is common. Check for ORM usage (SQLAlchemy, Django ORM) which provides parameterization by default. `pickle.loads()` on untrusted data is a critical vulnerability.
- **Go:** `html/template` auto-escapes. Check for `text/template` used for HTML (XSS risk). `os/exec` with user input needs scrutiny.
- **TypeScript/JavaScript:** XSS is the primary concern for web apps. Check for `dangerouslySetInnerHTML`, `eval()`, `innerHTML`. npm audit for dependency vulnerabilities.
- **C++:** Buffer overflows, use-after-free, format string vulnerabilities. Check for raw pointer usage vs smart pointers. Static analysis tools (clang-tidy, cppcheck) are critical.
- **C#:** Entity Framework provides parameterized queries. Check for raw SQL with string interpolation. ASP.NET Core has built-in protections — check they aren't disabled.
