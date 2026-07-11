#!/usr/bin/env python3
"""Capture and compare read-only repository state for handoff artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
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


def extract_snapshot(handoff: Path) -> dict[str, object]:
    text = handoff.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("handoff must start with YAML frontmatter")
    terminator = text.find("\n---\n", 4)
    if terminator == -1:
        raise ValueError("handoff frontmatter is not terminated")
    frontmatter = text[4:terminator]
    for line in frontmatter.splitlines():
        if not line.startswith("repository_snapshot:"):
            continue
        value = line.split(":", 1)[1].strip()
        snapshot = json.loads(value)
        if snapshot.get("snapshot_version") != SNAPSHOT_VERSION:
            raise ValueError(
                "unsupported repository snapshot version: "
                f"{snapshot.get('snapshot_version')}"
            )
        return snapshot
    raise ValueError("handoff has no repository_snapshot field")


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    result = run_git(
        repo,
        "merge-base",
        "--is-ancestor",
        older,
        newer,
        check=False,
    )
    return result.returncode == 0


def relevant_file_changes(
    recorded: dict[str, object],
    current: dict[str, object],
) -> list[str]:
    reasons: list[str] = []
    recorded_files = recorded.get("relevant_files", {})
    current_files = current.get("relevant_files", {})
    if not isinstance(recorded_files, dict) or not isinstance(current_files, dict):
        return ["relevant-file metadata is malformed"]
    for path, old_record in recorded_files.items():
        new_record = current_files.get(path)
        if not isinstance(old_record, dict):
            reasons.append(f"recorded metadata is malformed: {path}")
        elif not isinstance(new_record, dict):
            reasons.append(f"relevant path is no longer recorded: {path}")
        elif old_record.get("exists") and not new_record.get("exists"):
            reasons.append(f"relevant file disappeared: {path}")
        elif old_record.get("sha256") != new_record.get("sha256"):
            reasons.append(f"relevant file changed: {path}")
    return reasons


def compare_snapshot(
    repo: Path,
    recorded: dict[str, object],
) -> dict[str, object]:
    recorded_files = recorded.get("relevant_files", {})
    relevant = list(recorded_files.keys()) if isinstance(recorded_files, dict) else []
    current = capture_snapshot(repo, relevant)
    reasons: list[str] = []

    if recorded.get("kind") != "git" or current.get("kind") != "git":
        reasons.extend(relevant_file_changes(recorded, current))
        return {
            "classification": "unverifiable",
            "reasons": reasons or ["Git metadata is unavailable"],
            "recorded": recorded,
            "current": current,
        }

    if recorded.get("project_identity") != current.get("project_identity"):
        reasons.append("project identity differs")
    if recorded.get("branch") != current.get("branch"):
        reasons.append(
            f"branch differs: {recorded.get('branch')} -> {current.get('branch')}"
        )
    reasons.extend(relevant_file_changes(recorded, current))
    if recorded.get("dirty_patch_sha256") != current.get("dirty_patch_sha256"):
        reasons.append("working-tree patch fingerprint differs")

    recorded_head = recorded.get("head")
    current_head = current.get("head")
    if reasons:
        classification = "drifted"
    elif recorded_head == current_head:
        classification = "exact"
    elif (
        isinstance(recorded_head, str)
        and isinstance(current_head, str)
        and is_ancestor(repo, recorded_head, current_head)
    ):
        classification = "advanced"
    else:
        classification = "drifted"
        reasons.append("recorded HEAD is not an ancestor of current HEAD")

    return {
        "classification": classification,
        "reasons": reasons,
        "recorded": recorded,
        "current": current,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot", help="Capture repository state")
    snapshot.add_argument("--repo", type=Path, default=Path("."))
    snapshot.add_argument("--relevant", action="append", default=[])
    compare = subparsers.add_parser("compare", help="Compare a handoff with live state")
    compare.add_argument("--repo", type=Path, default=Path("."))
    compare.add_argument("--handoff", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "snapshot":
            payload = capture_snapshot(args.repo, args.relevant)
        elif args.command == "compare":
            payload = compare_snapshot(args.repo, extract_snapshot(args.handoff))
        else:
            return 2
        print(json.dumps(payload, sort_keys=True))
        return 0
    except (GitError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
