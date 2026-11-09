# Operability

## Definition

Operability measures how ready the codebase is for deployment, monitoring, and day-to-day operations.

## Signals to Look For

- A CI/CD pipeline.
- Containers or infrastructure-as-code for deployable services; a documented, not manual, deployment.
- Structured logging with levels.
- Configuration from the environment, not hard-coded values.
- Dependency lock files, and a database migration strategy where there is a database.

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| CI/CD config presence | Check for .github/workflows, .gitlab-ci.yml, Jenkinsfile | Architecture agent |
| Container config presence | Check for Dockerfile, docker-compose.yml | Architecture agent |
| Health check endpoints | Grep for /health, /ready, /status routes | Architecture agent |
| Logging patterns | Grep for logger/logging usage, check for structured logging | Structural agent |
| Environment config handling | Check for .env files, environment variable usage | Architecture agent |
| Lock file presence | Check for package-lock.json, poetry.lock, Cargo.lock, go.sum | Architecture agent |
| Dependency health | Run audit commands (npm audit, pip-audit, cargo audit) | Architecture agent (live) |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Full CI/CD + containerization + health checks + structured logging + IaC + dependency audit clean |
| A | CI/CD + container config + logging + lock files + env-based config |
| B | CI/CD present, basic logging, lock files present |
| C | Minimal CI or no CI, some logging, manual deployment |
| D | No CI/CD, inconsistent logging, hard-coded config |
| F | No automation, no logging, no deployment strategy, no lock files |

## Language-Aware Notes

- **Go:** Single binary deployment simplifies operability. Check for `Makefile` or `goreleaser` config. Built-in HTTP server makes health checks trivial.
- **Python:** Check for pyproject.toml, requirements.txt, or Poetry/Pipenv configuration. WSGI/ASGI server configuration (gunicorn, uvicorn) is an operability signal.
- **Rust:** Cargo.lock should be committed for binaries. Check for release profile optimization settings.
- **TypeScript/JavaScript:** Check for build scripts in package.json, bundler config. Node.js process management (PM2, systemd) is relevant for services.
- **C#:** Check for .csproj build targets, Dockerfile for ASP.NET Core. dotnet publish configuration.
