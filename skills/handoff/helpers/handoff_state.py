#!/usr/bin/env python3
"""Capture and compare read-only repository state for handoff artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


SNAPSHOT_VERSION = 1
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}


class GitError(RuntimeError):
    """Raised when required Git state cannot be read."""


def run_git(
    repo: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return result


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_remote_url(raw: str) -> str:
    value = raw.strip().replace("\\", "/")
    scp_match = re.fullmatch(r"(?:[^@]+@)?([^:]+):(.+)", value)
    if scp_match and "://" not in value:
        host, path = scp_match.groups()
    else:
        parsed = urlparse(value if "://" in value else f"ssh://{value}")
        host = parsed.hostname or ""
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git").rstrip("/")
    return f"{host.lower()}/{path}" if host and path else value.removesuffix(".git")


def is_sensitive_path(value: str) -> bool:
    path = Path(value)
    lowered = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        name in SENSITIVE_NAMES
        or name.startswith(".env.")
        or path.suffix.lower() in SENSITIVE_SUFFIXES
        or bool(lowered & {"secrets", "credentials", ".ssh"})
    )


def parse_porcelain_z(raw: bytes) -> list[dict[str, str]]:
    tokens = raw.decode("utf-8", errors="surrogateescape").split("\0")
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        status = token[:2]
        path = token[3:]
        entry = {"status": status, "path": path.replace("\\", "/")}
        if "R" in status or "C" in status:
            if index < len(tokens) and tokens[index]:
                entry["original_path"] = tokens[index].replace("\\", "/")
                index += 1
        entries.append(entry)
    return sorted(entries, key=lambda item: item["path"])


def git_root(repo: Path) -> Path | None:
    result = run_git(repo, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        return None
    return Path(result.stdout.decode("utf-8", errors="surrogateescape").strip()).resolve()


def project_identity(root: Path) -> tuple[str, str | None]:
    remote = run_git(root, "config", "--get", "remote.origin.url", check=False)
    raw_remote = remote.stdout.decode("utf-8", errors="replace").strip()
    normalized = normalize_remote_url(raw_remote) if raw_remote else None
    return normalized or f"local:{root.name}", normalized


def file_record(
    root: Path,
    relative: str,
    tracked_paths: set[str],
) -> dict[str, object]:
    normalized = relative.replace("\\", "/")
    path = root / normalized
    if not path.is_file():
        return {
            "exists": False,
            "tracked": normalized in tracked_paths,
            "sha256": None,
        }
    return {
        "exists": True,
        "tracked": normalized in tracked_paths,
        "sha256": sha256_file(path),
        "sensitive": is_sensitive_path(normalized),
    }


def capture_snapshot(
    repo: Path,
    relevant_paths: list[str] | None = None,
) -> dict[str, object]:
    requested_root = repo.resolve()
    root = git_root(requested_root)
    relevant = sorted(
        {path.replace("\\", "/") for path in relevant_paths or []}
    )
    if root is None:
        return {
            "snapshot_version": SNAPSHOT_VERSION,
            "kind": "non_git",
            "project_identity": f"local:{requested_root.name}",
            "root_name": requested_root.name,
            "relevant_files": {
                path: file_record(requested_root, path, set()) for path in relevant
            },
        }

    identity, remote = project_identity(root)
    branch_result = run_git(root, "branch", "--show-current", check=False)
    head_result = run_git(root, "rev-parse", "HEAD", check=False)
    status = parse_porcelain_z(
        run_git(
            root,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ).stdout
    )
    tracked_raw = run_git(root, "ls-files", "-z").stdout.decode(
        "utf-8",
        errors="surrogateescape",
    )
    tracked = {item for item in tracked_raw.split("\0") if item}
    patch = run_git(
        root,
        "diff",
        "--binary",
        "HEAD",
        "--",
        ".",
        check=False,
    ).stdout
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "kind": "git",
        "project_identity": identity,
        "remote": remote,
        "root_name": root.name,
        "branch": branch_result.stdout.decode().strip() or None,
        "head": head_result.stdout.decode().strip() or None,
        "status": status,
        "dirty_patch_sha256": sha256_bytes(patch),
        "relevant_files": {
            path: file_record(root, path, tracked) for path in relevant
        },
        "sensitive_paths": sorted(
            item["path"] for item in status if is_sensitive_path(item["path"])
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot", help="Capture repository state")
    snapshot.add_argument("--repo", type=Path, default=Path("."))
    snapshot.add_argument("--relevant", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "snapshot":
        print(json.dumps(capture_snapshot(args.repo, args.relevant), sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
