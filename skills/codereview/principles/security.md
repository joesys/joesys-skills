# Security Principles

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| API key, token, or password hardcoded in source | Hardcoded Secrets |
| User input concatenated into SQL, shell command, or HTML | Injection (SQL/Command/XSS) |
| No validation on file paths, URLs, sizes, or types from users | Input Sanitization |
| Rolling custom crypto, storing plaintext passwords, predictable tokens | Authentication & Session Management |
| Secrets visible in logs, error messages, or API responses | Sensitive Data Exposure |
| Pinned to known-vulnerable package versions, no lockfile | Dependency Security |
| User-supplied filename used directly in `open()` or `os.path.join()` | Path Traversal |
| `DEBUG=True` in production, `CORS: *`, no TLS enforcement | Insecure Defaults |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **Security vs. Developer Experience** | Strict security controls (rotating secrets, MFA, short token TTLs) slow developers down. Use generous timeouts and relaxed policies in local dev; enforce strict policies in staging and production. Never compromise production security for convenience. |
| **Input Sanitization vs. Usability** | Overly strict validation rejects legitimate input and frustrates users. Validate structure and type strictly, but be lenient with formatting (trim whitespace, normalize case). Reject what is dangerous, not what is unusual. |
| **Sensitive Data Exposure vs. Observability** | Logging is essential for debugging, but logs are a prime target for credential leaks. Log request IDs, status codes, and timing — never tokens, passwords, or PII. Use structured logging with explicit field allowlists. |
| **Dependency Security vs. Stability** | Updating dependencies can introduce regressions. Pin exact versions in lockfiles for reproducibility, but run automated audit tools (`pip-audit`, `npm audit`) on every CI build. Update proactively, not reactively after a CVE hits production. |
| **Hardcoded Secrets vs. Configuration Complexity** | Externalizing every secret adds infrastructure overhead (vaults, env management). The overhead is always justified — a leaked secret in a public repo is an instant, irreversible breach. Start with environment variables; graduate to a secrets manager as scale demands. |
| **Insecure Defaults vs. Quick Prototyping** | Secure defaults can make initial development feel sluggish (TLS setup, CORS restrictions). Prototype behind `--dev` flags with relaxed settings, but ensure production builds fail if insecure overrides are still active. |

---

## 1. Hardcoded Secrets — Never Embed Credentials in Source Code

API keys, database passwords, tokens, and encryption keys must never appear as string
literals in source files. Source code is stored in version control, copied to CI runners,
bundled into containers, and often pushed to public repositories. A single committed secret
can compromise an entire system within minutes of exposure.

### ❌ Wrong

```python
import requests

# Secret embedded directly in source — visible in git history forever
API_KEY = "sk-proj-4f8b2c1d9e7a3f6b5c8d2e1a0f9b7c4d"
DATABASE_URL = "postgresql://admin:SuperSecret123@prod-db.example.com:5432/myapp"

def get_weather(city: str) -> dict:
    response = requests.get(
        "https://api.weather.com/v1/forecast",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"city": city},
    )
    return response.json()
```

### ✅ Correct

```python
import os
import requests

# Secrets loaded from environment — never committed to source
API_KEY = os.environ["WEATHER_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

def get_weather(city: str) -> dict:
    response = requests.get(
        "https://api.weather.com/v1/forecast",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"city": city},
    )
    return response.json()
```

Ensure `.env` is listed in `.gitignore`:

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

**Detection guidance:** Scan for regex patterns that match common secret formats:

| Pattern | Catches |
|---|---|
| `(?i)(api_key\|secret\|token\|password)\s*=\s*["'][^"']{8,}` | Generic hardcoded credentials |
| `sk-[a-zA-Z0-9]{20,}` | OpenAI-style API keys |
| `ghp_[a-zA-Z0-9]{36}` | GitHub personal access tokens |
| `AKIA[0-9A-Z]{16}` | AWS access key IDs |
| `(?i)-----BEGIN (RSA\|EC\|DSA) PRIVATE KEY-----` | Private key files |

Use pre-commit hooks like `detect-secrets` or `gitleaks` to catch secrets before they reach version control.

**Key points:** Secrets in code are permanent — `git filter-branch` cannot reliably erase them from forks and mirrors. Treat any committed secret as compromised and rotate immediately. Environment variables are the simplest starting point; use a secrets manager (Vault, AWS Secrets Manager, 1Password) for production systems.

---

## 2. Injection — Never Interpolate Untrusted Data into Executable Contexts

Injection flaws occur when untrusted input is concatenated into a string that is later
interpreted as code — SQL, shell commands, HTML, or any other language. The attacker
breaks out of the data context and injects their own instructions.

### SQL Injection

### ❌ Wrong

```python
def get_user(cursor, user_id: str) -> dict:
    # Attacker sends user_id = "1; DROP TABLE users; --"
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
```

### ✅ Correct

```python
def get_user(cursor, user_id: str) -> dict:
    # Parameterized query — the database driver escapes the value
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()
```

### Command Injection

### ❌ Wrong

```python
import os

def convert_image(user_filename: str) -> None:
    # Attacker sends filename = "img.png; rm -rf /"
    os.system(f"convert {user_filename} output.png")
```

### ✅ Correct

```python
import subprocess

def convert_image(user_filename: str) -> None:
    # List form avoids shell interpretation — each element is a single argument
    subprocess.run(["convert", user_filename, "output.png"], check=True)
```

### Cross-Site Scripting (XSS)

### ❌ Wrong

```python
from flask import request

@app.route("/greet")
def greet():
    name = request.args.get("name", "")
    # Attacker sends name = "<script>steal_cookies()</script>"
    return f"<h1>Hello, {name}!</h1>"
```

### ✅ Correct

```python
from markupsafe import escape
from flask import request

@app.route("/greet")
def greet():
    name = escape(request.args.get("name", ""))
    return f"<h1>Hello, {name}!</h1>"

# Or use Jinja2 templates, which auto-escape by default:
# return render_template("greet.html", name=name)
```

**Detection guidance:** Look for string formatting (`f"..."`, `.format()`, `%`, `+`) that
builds SQL queries, shell commands, or HTML with user-supplied values. Safe alternatives:
parameterized queries for SQL, list-form `subprocess.run()` for commands, template engines
with auto-escaping for HTML.

**Key points:** Injection is consistently in the OWASP Top 10 because it is easy to introduce and devastating to exploit. The fix is always the same pattern: separate code from data. Never build executable strings from untrusted input.

---

## 3. Input Sanitization — Validate and Constrain All External Data

Every value that crosses a trust boundary — HTTP requests, file uploads, webhook payloads,
CLI arguments, environment variables — must be validated before use. Assume all external
input is malicious until proven otherwise.

### ❌ Wrong

```python
from flask import request

@app.route("/resize")
def resize_image():
    width = request.args.get("width")      # Could be "99999999" or "-1" or "abc"
    url = request.args.get("url")           # Could be "file:///etc/passwd"
    filename = request.args.get("name")     # Could be "../../../../etc/shadow"

    image = download_image(url)             # No URL scheme validation
    image.resize(int(width), int(width))    # No range check, crashes on "abc"
    image.save(f"uploads/{filename}")       # Path traversal
    return "OK"
```

### ✅ Correct

```python
from flask import request, abort
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
MAX_DIMENSION = 4096
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

@app.route("/resize")
def resize_image():
    # Validate width: type coercion + range check
    try:
        width = int(request.args.get("width", ""))
    except ValueError:
        abort(400, "width must be an integer")
    if not (1 <= width <= MAX_DIMENSION):
        abort(400, f"width must be between 1 and {MAX_DIMENSION}")

    # Validate URL: scheme allowlist
    url = request.args.get("url", "")
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        abort(400, "Only http and https URLs are allowed")

    # Validate filename: extension allowlist + sanitize
    filename = request.args.get("name", "")
    if not filename or not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        abort(400, "Invalid file extension")
    safe_name = secure_filename(filename)  # werkzeug utility

    image = download_image(url)
    image.resize(width, width)
    image.save(os.path.join("uploads", safe_name))
    return "OK"
```

**Detection guidance:** Look for external inputs used without validation. Common red flags:
direct `int()` / `float()` casts without `try/except`, no length limits on string fields,
URLs accepted without scheme checks, file sizes accepted without upper bounds, and
allowlists replaced by denylists (denylists always miss something).

**Key points:** Validate at the boundary, not deep inside business logic. Prefer allowlists
over denylists — explicitly state what is permitted rather than trying to enumerate what is
forbidden. Apply type coercion, range checks, and length limits to every external value.

---

## 4. Authentication & Session Management — Never Roll Your Own Crypto

Password hashing, token generation, and session management are solved problems with
well-tested libraries. Custom implementations almost always contain subtle vulnerabilities:
timing attacks, weak entropy, reversible hashing, or predictable session IDs.

### ❌ Wrong

```python
import hashlib
import time

def hash_password(password: str) -> str:
    # MD5 is broken; no salt means identical passwords produce identical hashes
    return hashlib.md5(password.encode()).hexdigest()

def create_session_token(user_id: int) -> str:
    # Predictable: attacker can guess other users' tokens
    return f"{user_id}-{int(time.time())}"

def verify_password(stored_hash: str, password: str) -> bool:
    # Vulnerable to timing attacks — string comparison short-circuits
    return stored_hash == hashlib.md5(password.encode()).hexdigest()
```

### ✅ Correct

```python
import secrets
import bcrypt

def hash_password(password: str) -> bytes:
    # bcrypt: adaptive cost factor, built-in salt, resistant to GPU attacks
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

def verify_password(stored_hash: bytes, password: str) -> bool:
    # bcrypt.checkpw uses constant-time comparison internally
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

def create_session_token() -> str:
    # 32 bytes of cryptographically secure randomness = 256 bits of entropy
    return secrets.token_urlsafe(32)

# Session configuration
SESSION_CONFIG = {
    "ttl_seconds": 3600,            # 1-hour expiry
    "refresh_threshold": 900,       # Refresh if < 15 min remaining
    "secure": True,                 # HTTPS only
    "httponly": True,               # Not accessible via JavaScript
    "samesite": "Lax",              # CSRF protection
}
```

**Detection guidance:** Look for `hashlib.md5` or `hashlib.sha1` used for passwords (these
are fast hashes, not password hashes). Check for `random.random()` or `time.time()` used in
token generation (predictable). Flag any manual string comparison of hashes (timing attack).
Verify session cookies have `Secure`, `HttpOnly`, and `SameSite` attributes.

**Key points:** Use `bcrypt`, `argon2-cffi`, or `scrypt` for password hashing — never MD5,
SHA-1, or SHA-256 alone. Use `secrets.token_urlsafe()` for tokens — never `random` or
timestamps. Keep session TTLs short (1-4 hours) and rotate tokens on privilege escalation
(login, password change).

---

## 5. Sensitive Data Exposure — Control What Leaves the System

Secrets leak through logs, error messages, API responses, and stack traces. A single
overly verbose log statement can expose database credentials, auth tokens, or personal
data to anyone with log access — which is often a much larger group than those with
production database access.

### ❌ Wrong

```python
import logging
import traceback

logger = logging.getLogger(__name__)

def handle_request(request):
    # Logs entire request including Authorization header and cookies
    logger.info(f"Incoming request: {request.headers}")
    logger.debug(f"Request body: {request.body}")

    try:
        result = process_payment(request)
    except Exception as e:
        # Stack trace may contain DB credentials from connection string
        logger.error(f"Payment failed: {traceback.format_exc()}")
        # Error detail sent to client — leaks internal architecture
        return {"error": str(e), "trace": traceback.format_exc()}

    return result
```

### ✅ Correct

```python
import logging
import uuid

logger = logging.getLogger(__name__)

REDACT_HEADERS = {"authorization", "cookie", "x-api-key"}

def sanitize_headers(headers: dict) -> dict:
    return {
        k: "***REDACTED***" if k.lower() in REDACT_HEADERS else v
        for k, v in headers.items()
    }

def handle_request(request):
    request_id = str(uuid.uuid4())
    logger.info(
        "Incoming request",
        extra={"request_id": request_id, "method": request.method, "path": request.path},
    )
    # Log only safe, selected headers
    logger.debug("Headers", extra={"headers": sanitize_headers(dict(request.headers))})

    try:
        result = process_payment(request)
    except Exception:
        # Log full trace server-side with request_id for correlation
        logger.exception("Payment failed", extra={"request_id": request_id})
        # Client gets generic message + correlation ID for support
        return {"error": "Payment processing failed", "request_id": request_id}

    return result
```

**Detection guidance:** Search for log statements that include `request.headers`,
`request.body`, `traceback.format_exc()`, or f-strings containing `password`, `token`,
`secret`, or `key`. Check error responses for raw exception messages or stack traces.
Verify that PII (email, SSN, phone) is not logged in plaintext.

**Key points:** Log the minimum needed for debugging: request IDs, status codes, timing,
and sanitized context. Never log authentication headers, request bodies, or full stack
traces that might contain connection strings. Return generic error messages to clients with
a correlation ID; keep the details server-side.

---

## 6. Dependency Security — Audit and Update Your Supply Chain

Modern applications inherit most of their code from third-party packages. A vulnerable
dependency is functionally equivalent to a vulnerability in your own code — attackers do
not distinguish between the two. Supply chain attacks are increasing in frequency and
sophistication.

### ❌ Wrong

```toml
# pyproject.toml — no lockfile, loose pins, known-vulnerable version
[project]
dependencies = [
    "requests",              # No version pin — any version, including broken ones
    "django==3.1.0",         # Known CVEs (e.g., CVE-2021-33203, CVE-2021-33571)
    "pyyaml>=5.0",           # yaml.load() without Loader is unsafe in < 5.4
    "cryptography>=2.0",     # Versions < 3.3 have multiple CVEs
]
```

```python
# No lockfile committed — builds are non-reproducible
# No audit step in CI — vulnerabilities ship to production silently
```

### ✅ Correct

```toml
# pyproject.toml — reasonably pinned
[project]
dependencies = [
    "requests>=2.31.0,<3",
    "django>=4.2,<5",
    "pyyaml>=6.0.1,<7",
    "cryptography>=41.0,<43",
]
```

```bash
# Generate and commit lockfile for reproducible builds
pip-compile --generate-hashes -o requirements.lock pyproject.toml

# CI pipeline: audit dependencies on every build
pip-audit -r requirements.lock --strict

# Automated update checks (e.g., Dependabot, Renovate)
# Configure to open PRs for security updates automatically
```

**Detection guidance:** Check for missing lockfiles (`requirements.lock`,
`poetry.lock`, `package-lock.json`). Look for dependencies without upper-bound version
constraints. Run `pip-audit`, `npm audit`, or `cargo audit` to identify known CVEs. Flag
dependencies that have not been updated in over a year.

**Key points:** Pin dependencies with upper bounds and commit lockfiles. Run audit tools
in CI — not just locally. Enable automated dependency update tools (Dependabot, Renovate)
and treat security update PRs as high priority. Review new dependencies before adding them:
check maintenance activity, download counts, and known vulnerabilities.

---

## 7. Path Traversal — Confine File Access to Intended Directories

Path traversal occurs when user-supplied input is used to construct file paths without
verifying that the resolved path stays within the intended directory. Attackers use
sequences like `../` to escape the upload directory and read or overwrite arbitrary files
on the system.

### ❌ Wrong

```python
from flask import request, send_file

@app.route("/download")
def download_file():
    filename = request.args.get("file", "")
    # Attacker sends file = "../../../../etc/passwd"
    return send_file(f"uploads/{filename}")

@app.route("/upload", methods=["POST"])
def upload_file():
    filename = request.form.get("filename", "")
    content = request.files["file"].read()
    # Attacker sends filename = "../../../app/config.py" to overwrite application code
    with open(f"uploads/{filename}", "wb") as f:
        f.write(content)
    return "OK"
```

### ✅ Correct

```python
import os
from flask import request, send_file, abort

UPLOAD_DIR = os.path.realpath("uploads")

def safe_path(base_dir: str, user_input: str) -> str:
    """Resolve the full path and verify it stays within the base directory."""
    requested = os.path.realpath(os.path.join(base_dir, user_input))
    if not requested.startswith(base_dir + os.sep) and requested != base_dir:
        raise ValueError(f"Path traversal blocked: {user_input!r}")
    return requested

@app.route("/download")
def download_file():
    filename = request.args.get("file", "")
    try:
        filepath = safe_path(UPLOAD_DIR, filename)
    except ValueError:
        abort(403, "Access denied")
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(filepath)

@app.route("/upload", methods=["POST"])
def upload_file():
    filename = request.form.get("filename", "")
    try:
        filepath = safe_path(UPLOAD_DIR, filename)
    except ValueError:
        abort(403, "Access denied")
    content = request.files["file"].read()
    with open(filepath, "wb") as f:
        f.write(content)
    return "OK"
```

**Detection guidance:** Search for `open()`, `send_file()`, `os.path.join()`, or
`pathlib.Path()` calls where the filename comes from user input (`request.args`,
`request.form`, `request.json`). Verify that the resolved path is validated against an
allowed base directory using `os.path.realpath()`. Flag any path construction that skips
this check.

**Key points:** Always resolve paths to their canonical form with `os.path.realpath()`
before use, then verify the result starts with the expected base directory prefix. Never
trust user-supplied filenames — strip directory components or use `werkzeug.utils.secure_filename()`.
Combine path validation with file extension allowlists for defense in depth.

---

## 8. Insecure Defaults — Ship Secure, Require Explicit Opt-Out

Production systems must be secure by default. Debug modes, permissive CORS policies,
disabled authentication, and unencrypted communication should never be the default state.
When an insecure option is needed for development, require the developer to explicitly
enable it — and make it impossible to accidentally deploy.

### ❌ Wrong

```python
# settings.py — insecure defaults that "someone will fix before prod"

DEBUG = True                                    # Stack traces visible to users
SECRET_KEY = "django-insecure-default-key"      # Predictable, exploitable
ALLOWED_HOSTS = ["*"]                           # Accepts any hostname
CORS_ALLOW_ALL_ORIGINS = True                   # Any site can make requests
SESSION_COOKIE_SECURE = False                   # Cookies sent over HTTP
CSRF_COOKIE_SECURE = False                      # CSRF token sent over HTTP
SECURE_SSL_REDIRECT = False                     # No HTTPS enforcement

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "PASSWORD": "admin123",                 # Hardcoded weak password
    }
}
```

### ✅ Correct

```python
import os

# settings.py — secure by default, explicit opt-out for development

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]    # Fails fast if missing
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "").split(",")

SESSION_COOKIE_SECURE = not DEBUG               # Secure in prod, relaxed in dev
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "PASSWORD": os.environ["DB_PASSWORD"],  # From environment
    }
}

# Fail-safe: refuse to start in production with debug enabled
if not DEBUG and SECRET_KEY.startswith("django-insecure"):
    raise RuntimeError("Insecure SECRET_KEY detected in production — aborting")
```

**Detection guidance:** Search for `DEBUG = True`, `CORS_ALLOW_ALL = True`,
`verify=False` (TLS verification disabled), `ALLOWED_HOSTS = ["*"]`, and
`SECRET_KEY = "..."` (hardcoded). Check for `http://` URLs in production config where
`https://` should be used. Verify that security-critical settings differ between
development and production configurations.

**Key points:** Default to the most restrictive setting. Debug mode, permissive CORS, and
disabled TLS verification should require an explicit flag to enable. Add startup checks
that refuse to run in production with insecure configuration. Tie security toggles to
`DEBUG` or environment detection so they cannot be accidentally left open.

---

## Summary: Security Review Checklist

| # | Principle | Key Question |
|---|---|---|
| 1 | Hardcoded Secrets | Are any credentials, keys, or tokens in source code? |
| 2 | Injection | Is untrusted input ever concatenated into SQL, commands, or HTML? |
| 3 | Input Sanitization | Is every external value validated for type, range, and format? |
| 4 | Authentication & Session | Are passwords hashed with bcrypt/argon2? Are tokens cryptographically random? |
| 5 | Sensitive Data Exposure | Could logs, errors, or API responses leak secrets or PII? |
| 6 | Dependency Security | Are dependencies pinned, locked, and audited for CVEs? |
| 7 | Path Traversal | Are file paths resolved and confined to the intended directory? |
| 8 | Insecure Defaults | Is the production configuration secure without manual hardening? |
