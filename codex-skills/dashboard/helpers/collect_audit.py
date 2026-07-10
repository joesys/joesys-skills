"""Read-only consumption of the newest /codebase-audit metrics.json.

Never runs the audit. Stamps provenance + staleness so an old grade is never
read as current.

Usage:
    python collect_audit.py --repo . [--now TS] [--out audit.json]
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import subprocess
import sys
import time


def _commits_behind(repo: str, commit: str) -> int:
    r = subprocess.run(["git", "rev-list", "--count", f"{commit}..HEAD"],
                       cwd=repo, capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else 0


def _report_paths(repo: str) -> list[str]:
    base = os.path.join(repo, "docs", "reports", "codebase-audit")
    return sorted(glob.glob(os.path.join(base, "*", "metrics.json")))


def _load(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.loads(fh.read())
    except Exception:
        return None


def collect(repo: str, now_ts: int, stale_after_commits: int = 200) -> dict:
    reports = _report_paths(repo)
    trend = []
    newest = None
    newest_path = None
    for path in reports:
        j = _load(path)
        if j is None:
            continue  # skip corrupt/partial report; never crash
        trend.append({"date": j.get("date", ""), "grade": j.get("overall_grade", "?")})
        newest, newest_path = j, path  # sorted ascending -> last parseable is newest
    if newest is None:
        return {"available": False}
    criteria = {name: c.get("grade", "?") for name, c in (newest.get("criteria") or {}).items()}
    behind = _commits_behind(repo, newest.get("commit", "HEAD"))
    return {
        "available": True,
        "date": newest.get("date", ""),
        "commit": newest.get("commit", ""),
        "overall_grade": newest.get("overall_grade", "?"),
        "criteria": criteria,
        "commits_behind": behind,
        "stale": behind > stale_after_commits,
        "report_path": os.path.relpath(newest_path, repo),
        "trend": trend,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Read /codebase-audit report (read-only)")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--now", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    now_ts = args.now if args.now is not None else int(time.time())
    data = collect(args.repo, now_ts)
    text = json.dumps(data, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
