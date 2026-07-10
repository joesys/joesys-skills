#!/usr/bin/env python3
"""Git churn analysis — 30-day window.

Measures code churn by parsing git log --numstat output.
Outputs JSON to stdout for deterministic agent consumption.

Usage:
    python compute_churn.py [--source DIR] [--exclude PATTERNS] [--days N]
"""
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import PurePosixPath


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute git churn metrics")
    parser.add_argument("--source", default=".", help="Source directory to analyze (default: .)")
    parser.add_argument("--exclude", default="", help="Comma-separated glob patterns to exclude")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back (default: 30)")
    return parser.parse_args()


def get_git_numstat(source: str, days: int) -> str:
    """Run git log --numstat and return raw output."""
    cmd = [
        "git", "log",
        f"--since={days} days ago",
        "--numstat",
        "--pretty=format:",
        "--", source,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(json.dumps({"error": f"git log failed: {result.stderr.strip()}"}), file=sys.stderr)
        sys.exit(1)
    return result.stdout


def is_excluded(filepath: str, patterns: list[str]) -> bool:
    """Check if a filepath matches any exclusion pattern."""
    for pattern in patterns:
        if fnmatch(filepath, pattern):
            return True
        # Check if any path component matches (handles directory patterns like "vendor/")
        parts = PurePosixPath(filepath).parts
        for part in parts:
            if fnmatch(part, pattern.rstrip("/")):
                return True
    return False


def parse_numstat(raw: str, exclude_patterns: list[str]) -> dict[str, dict]:
    """Parse git numstat output into per-file churn data."""
    files: dict[str, dict] = defaultdict(lambda: {"added": 0, "deleted": 0})

    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_str, deleted_str, filepath = parts

        # Skip binary files (shown as "-")
        if added_str == "-" or deleted_str == "-":
            continue

        if is_excluded(filepath, exclude_patterns):
            continue

        try:
            added = int(added_str)
            deleted = int(deleted_str)
        except ValueError:
            continue

        files[filepath]["added"] += added
        files[filepath]["deleted"] += deleted

    return dict(files)


def compute_churn(source: str, exclude: str, days: int) -> dict:
    """Compute churn metrics and return structured data."""
    exclude_patterns = [p.strip() for p in exclude.split(",") if p.strip()]

    raw = get_git_numstat(source, days)
    files = parse_numstat(raw, exclude_patterns)

    total_added = sum(f["added"] for f in files.values())
    total_deleted = sum(f["deleted"] for f in files.values())

    most_churned = sorted(
        [
            {
                "file": filepath,
                "added": data["added"],
                "deleted": data["deleted"],
                "total_churn": data["added"] + data["deleted"],
            }
            for filepath, data in files.items()
        ],
        key=lambda x: x["total_churn"],
        reverse=True,
    )

    return {
        "files_changed": len(files),
        "lines_added": total_added,
        "lines_deleted": total_deleted,
        "net_change": total_added - total_deleted,
        "most_churned_files": most_churned,
    }


def main():
    args = parse_args()
    result = compute_churn(args.source, args.exclude, args.days)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
