"""Optional GitHub/GitLab enrichment via gh/glab CLIs. Degrades gracefully.

Usage:
    python collect_host.py --repo . [--out host.json]
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import time


def _run(repo: str, args: list[str]) -> str:
    r = subprocess.run(args, cwd=repo, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _remote_host(repo: str):
    url = _run(repo, ["git", "remote", "get-url", "origin"]).strip()
    if "github.com" in url:
        return "github"
    if "gitlab" in url:
        return "gitlab"
    return None


def _cli_ready(host: str) -> bool:
    cli = "gh" if host == "github" else "glab"
    if not shutil.which(cli):
        return False
    r = subprocess.run([cli, "auth", "status"], capture_output=True, text=True)
    return r.returncode == 0


def _gh_json(repo: str, args: list[str]):
    out = _run(repo, ["gh"] + args)
    try:
        return json.loads(out) if out else None
    except json.JSONDecodeError:
        return None


def _open_prs(repo: str) -> dict:
    data = _gh_json(repo, ["pr", "list", "--state", "open", "--json", "createdAt", "--limit", "200"])
    if not data:
        return {"count": 0, "median_age_days": None}
    now = time.time()
    ages = []
    for pr in data:
        # createdAt like 2026-06-01T10:00:00Z
        ts = time.mktime(time.strptime(pr["createdAt"], "%Y-%m-%dT%H:%M:%SZ"))
        ages.append((now - ts) / 86400)
    ages.sort()
    median = round(ages[len(ages) // 2], 1) if ages else None
    return {"count": len(data), "median_age_days": median}


def _open_issues(repo: str) -> int:
    data = _gh_json(repo, ["issue", "list", "--state", "open", "--json", "number", "--limit", "500"])
    return len(data) if data else 0


def _ci_pass_rate(repo: str):
    data = _gh_json(repo, ["run", "list", "--json", "conclusion", "--limit", "30"])
    if not data:
        return None
    done = [r for r in data if r.get("conclusion")]
    if not done:
        return None
    ok = sum(1 for r in done if r["conclusion"] == "success")
    return round(ok / len(done), 3)


def collect(repo: str) -> dict:
    host = _remote_host(repo)
    if not host:
        return {"available": False, "reason": "no github/gitlab remote detected"}
    if not _cli_ready(host):
        cli = "gh" if host == "github" else "glab"
        return {"available": False, "reason": f"{cli} not installed or not authenticated"}
    if host == "gitlab":
        return {"available": False, "reason": "gitlab enrichment not implemented in v1"}
    prs = _open_prs(repo)
    return {"available": True, "host": host, "open_prs": prs["count"],
            "pr_median_age_days": prs["median_age_days"],
            "ci_pass_rate": _ci_pass_rate(repo), "open_issues": _open_issues(repo)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Optional host (GitHub/GitLab) enrichment")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    data = collect(args.repo)
    text = json.dumps(data, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
