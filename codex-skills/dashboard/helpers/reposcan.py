# reposcan.py
"""Filesystem + repo-state scans (tracked files, modules, debt, hygiene)."""
from __future__ import annotations
import os
import subprocess

_IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "vendor", "dist",
                "build", "__pycache__", ".next", "coverage", "target"}
_LOCKFILES = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
              "Pipfile.lock", "go.sum", "Cargo.lock", "composer.lock"]


def _run(repo: str, args: list[str]) -> str:
    r = subprocess.run(["git"] + args, cwd=repo, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _tracked_files(repo: str) -> list[str]:
    return [f for f in _run(repo, ["ls-files"]).splitlines() if f]


def detect_modules(repo: str) -> list[str]:
    tops: set[str] = set()
    for f in _tracked_files(repo):
        head = f.split("/", 1)
        if len(head) == 2:
            top = head[0]
            if not top.startswith(".") and top not in _IGNORE_DIRS:
                tops.add(top)
    return sorted(tops)


def debt_markers(repo: str) -> dict:
    out = {"todo": 0, "fixme": 0, "hack": 0, "total": 0}
    for kind in ("TODO", "FIXME", "HACK"):
        raw = _run(repo, ["grep", "-I", "-o", "-w", kind])
        n = len([l for l in raw.splitlines() if l.strip()])
        out[kind.lower()] = n
        out["total"] += n
    return out


def hygiene(repo: str) -> dict:
    files = set(_tracked_files(repo))
    ci = any(f.startswith(".github/workflows/") for f in files) \
        or ".gitlab-ci.yml" in files or "Jenkinsfile" in files \
        or any(f.endswith((".circleci/config.yml",)) for f in files)
    lockfile = any(lf in files for lf in _LOCKFILES)
    env_ignored = False
    gi = os.path.join(repo, ".gitignore")
    if os.path.isfile(gi):
        with open(gi, "r", encoding="utf-8", errors="ignore") as fh:
            env_ignored = any(line.strip().lstrip("/").startswith(".env")
                              for line in fh)
    tests = any("test" in f.lower() or "spec" in f.lower() for f in files)
    return {"ci": ci, "lockfile": lockfile, "env_gitignored": env_ignored, "tests": tests}


def project_size(repo: str) -> dict:
    files = _tracked_files(repo)
    langs: dict[str, int] = {}
    for f in files:
        ext = f.rsplit(".", 1)[-1] if "." in os.path.basename(f) else ""
        if ext:
            langs[ext] = langs.get(ext, 0) + 1
    return {"files": len(files), "languages": langs}
