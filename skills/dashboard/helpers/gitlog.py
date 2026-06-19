# gitlog.py
"""Local git access + parsing. The only metrics module that runs git.

Uses \\x1f field / \\x1e record separators so subjects with spaces parse cleanly.
"""
from __future__ import annotations
import subprocess
from typing import Optional

US = "\x1f"  # unit separator (between fields)
RS = "\x1e"  # record separator (between commits)


def _run(repo: str, args: list[str]) -> str:
    try:
        r = subprocess.run(["git"] + args, cwd=repo, capture_output=True, text=True)
    except OSError:
        # cwd missing/invalid (Windows raises before git runs) or git not found.
        return ""
    if r.returncode != 0:
        return ""
    return r.stdout


def is_git_repo(repo: str) -> bool:
    return _run(repo, ["rev-parse", "--is-inside-work-tree"]).strip() == "true"


def is_shallow(repo: str) -> bool:
    return _run(repo, ["rev-parse", "--is-shallow-repository"]).strip() == "true"


def get_commits(repo: str, since_days: Optional[int] = None) -> list[dict]:
    fmt = US.join(["%H", "%an", "%ae", "%at", "%P", "%s"]) + RS
    args = ["log", f"--pretty=format:{fmt}"]
    if since_days is not None:
        args.insert(1, f"--since={since_days} days ago")
    raw = _run(repo, args)
    out: list[dict] = []
    for rec in raw.split(RS):
        rec = rec.strip("\n")
        if not rec:
            continue
        parts = rec.split(US)
        if len(parts) < 6:
            continue
        h, an, ae, at, parents, subject = parts[:6]
        plist = parents.split() if parents.strip() else []
        out.append({
            "hash": h, "author": an, "email": ae, "ts": int(at),
            "parents": plist, "is_merge": len(plist) > 1, "subject": subject,
        })
    return out


def get_file_change_counts(repo: str, since_days: Optional[int] = None) -> dict[str, int]:
    args = ["log", "--name-only", "--pretty=format:"]
    if since_days is not None:
        args.insert(1, f"--since={since_days} days ago")
    raw = _run(repo, args)
    counts: dict[str, int] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        counts[line] = counts.get(line, 0) + 1
    return counts


def get_branches(repo: str) -> list[dict]:
    fmt = US.join(["%(refname:short)", "%(committerdate:unix)"])
    raw = _run(repo, ["for-each-ref", f"--format={fmt}", "refs/heads", "refs/remotes"])
    out: list[dict] = []
    for line in raw.splitlines():
        if US not in line:
            continue
        name, ts = line.split(US, 1)
        if name.endswith("/HEAD"):
            continue
        try:
            out.append({"name": name, "last_ts": int(ts)})
        except ValueError:
            continue
    return out


def get_tags(repo: str) -> list[dict]:
    fmt = US.join(["%(refname:short)", "%(creatordate:unix)"])
    raw = _run(repo, ["for-each-ref", "--sort=-creatordate", f"--format={fmt}", "refs/tags"])
    out: list[dict] = []
    for line in raw.splitlines():
        if US not in line:
            continue
        name, ts = line.split(US, 1)
        try:
            out.append({"name": name, "ts": int(ts)})
        except ValueError:
            continue
    return out


def count_commits(repo: str, since_days: Optional[int] = None, path: Optional[str] = None) -> int:
    args = ["rev-list", "--count", "HEAD"]
    if since_days is not None:
        args.insert(2, f"--since={since_days} days ago")
    if path:
        args += ["--", path]
    raw = _run(repo, args).strip()
    return int(raw) if raw.isdigit() else 0


def default_branch(repo: str) -> str:
    raw = _run(repo, ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"]).strip()
    if raw:
        return raw.split("/")[-1]
    for cand in ("main", "master"):
        if _run(repo, ["rev-parse", "--verify", cand]).strip():
            return cand
    return _run(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip() or "main"


def repo_head(repo: str) -> dict:
    return {
        "branch": _run(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip(),
        "commit": _run(repo, ["rev-parse", "--short", "HEAD"]).strip(),
    }
