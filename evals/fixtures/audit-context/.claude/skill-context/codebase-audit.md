# Codebase Audit Preferences

Last updated: 2026-11-01

## Audit-Specific Context
- **Project phase:** mvp
- **Team size:** 2-5
- **Business priority:** reliability
- **Deployment cadence:** weekly
- **Domain:** online shop backend (orders, login tokens, a small HTTP cache)

## Known Trade-offs
- There are no automated tests yet. The team tests by hand before each weekly release.
- There is no CI pipeline yet. It is planned after the MVP launch.
- The three languages (Python, TypeScript, Go) are intentional. Each part is owned by a different person.

## Audit History
- None yet. This is the first audit.
