#!/usr/bin/env python3
"""Track deterministic state for iterative spec and plan review."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = 1
MAX_ITERATIONS = 20
SEVERITIES = {"P0", "P1", "P2", "P3", "P4"}
VERDICTS = {"accepted", "rejected", "needs-user-decision"}


class StateError(ValueError):
    """Raised when review state is malformed or unsafe."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_git(repo: Path, *args: str, text: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=True,
        text=text,
    )
    return result.stdout


def resolve_repo(repo: Path) -> Path:
    output = str(
        run_git(repo.resolve(), "rev-parse", "--show-toplevel", text=True)
    ).strip()
    return Path(output).resolve()


def resolve_documents(repo: Path, documents: Iterable[Path]) -> list[Path]:
    resolved = [path.resolve() for path in documents]
    if not 1 <= len(resolved) <= 2:
        raise StateError("plan review requires one or two documents")
    for path in resolved:
        if not path.is_file():
            raise StateError(f"document is missing or unreadable: {path}")
        if not path.is_relative_to(repo):
            raise StateError(f"document must be inside repository: {path}")
    if len(set(resolved)) != len(resolved):
        raise StateError("review documents must be distinct")
    return resolved


def _relative_paths(repo: Path, documents: Iterable[Path]) -> list[str]:
    return [path.relative_to(repo).as_posix() for path in documents]


def _untracked_hashes(repo: Path, excluded: set[str]) -> dict[str, str]:
    raw = bytes(
        run_git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    )
    paths = sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in raw.split(b"\0")
        if item
    )
    hashes: dict[str, str] = {}
    for relative in paths:
        if relative in excluded:
            continue
        path = repo / relative
        hashes[relative] = sha256_file(path) if path.is_file() else "missing"
    return hashes


def capture_non_target_state(
    repo: Path,
    document_paths: Iterable[str],
) -> dict[str, Any]:
    repo = resolve_repo(repo)
    excluded = set(document_paths)
    pathspecs = [".", *(f":(exclude){path}" for path in sorted(excluded))]
    tracked_paths = str(
        run_git(
            repo,
            "diff",
            "--name-only",
            "HEAD",
            "--",
            *pathspecs,
            text=True,
        )
    ).splitlines()
    path_fingerprints = {
        relative: sha256_bytes(
            bytes(run_git(repo, "diff", "--binary", "HEAD", "--", relative))
        )
        for relative in tracked_paths
    }
    path_fingerprints.update(_untracked_hashes(repo, excluded))
    payload = json.dumps(
        path_fingerprints,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "fingerprint": sha256_bytes(payload),
        "paths": sorted(path_fingerprints),
        "path_fingerprints": path_fingerprints,
    }


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def create_ledger(
    repo: Path,
    documents: Iterable[Path],
    *,
    max_iterations: int = MAX_ITERATIONS,
) -> tuple[Path, dict[str, Any]]:
    if not 1 <= max_iterations <= MAX_ITERATIONS:
        raise StateError("max_iterations must be between 1 and 20")
    root = resolve_repo(repo)
    resolved_documents = resolve_documents(root, documents)
    relative_documents = _relative_paths(root, resolved_documents)
    non_target = capture_non_target_state(root, relative_documents)
    ledger: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "repo_root": str(root),
        "documents": relative_documents,
        "max_iterations": max_iterations,
        "baseline": {
            "document_hashes": {
                relative: sha256_file(root / relative)
                for relative in relative_documents
            },
            "document_contents": {
                relative: (root / relative).read_text(encoding="utf-8")
                for relative in relative_documents
            },
            "non_target_fingerprint": non_target["fingerprint"],
            "non_target_paths": non_target["paths"],
            "non_target_files": non_target["path_fingerprints"],
        },
        "iterations": [],
    }
    descriptor, raw_path = tempfile.mkstemp(
        prefix="plan-review-",
        suffix=".json",
    )
    os.close(descriptor)
    ledger_path = Path(raw_path).resolve()
    _atomic_write(ledger_path, ledger)
    return ledger_path, ledger


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StateError(f"cannot read plan-review ledger: {error}") from error
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise StateError("unsupported plan-review ledger schema")
    return payload


def save_ledger(path: Path, ledger: Mapping[str, Any]) -> None:
    _atomic_write(path, ledger)


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def finding_fingerprint(finding: Mapping[str, Any]) -> str:
    concern_key = str(finding.get("concern_key", "")).strip()
    document = str(finding.get("document", "")).strip()
    location = str(finding.get("location", "")).strip()
    evidence = finding.get("repository_evidence", [])
    if not concern_key or not document or not location:
        raise StateError(
            "finding requires concern_key, document, and location"
        )
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) for item in evidence
    ):
        raise StateError("repository_evidence must be a list of strings")
    identity = {
        "concern_key": _normalized_text(concern_key),
        "document": Path(document).as_posix().casefold(),
        "location": _normalized_text(location),
        "repository_evidence": sorted(
            _normalized_text(item) for item in evidence
        ),
    }
    return sha256_bytes(
        json.dumps(
            identity,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _validate_iteration(
    iteration: Mapping[str, Any],
) -> tuple[list[dict], dict[str, dict]]:
    review = iteration.get("review")
    if not isinstance(review, Mapping) or review.get("schema_version") != 1:
        raise StateError("review must use schema_version 1")
    findings = review.get("findings")
    if not isinstance(findings, list):
        raise StateError("review findings must be a list")
    finding_ids: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise StateError("each finding must be an object")
        finding_id = str(finding.get("id", ""))
        if not finding_id or finding_id in finding_ids:
            raise StateError("finding ids must be non-empty and unique")
        if finding.get("severity") not in SEVERITIES:
            raise StateError(f"invalid severity for {finding_id}")
        finding_fingerprint(finding)
        finding_ids.add(finding_id)

    verdict_list = iteration.get("verdicts")
    if not isinstance(verdict_list, list):
        raise StateError("verdicts must be a list")
    verdicts: dict[str, dict] = {}
    for verdict in verdict_list:
        if not isinstance(verdict, dict):
            raise StateError("each verdict must be an object")
        finding_id = str(verdict.get("finding_id", ""))
        if finding_id not in finding_ids or finding_id in verdicts:
            raise StateError("verdicts must match findings one-to-one")
        if verdict.get("verdict") not in VERDICTS:
            raise StateError(f"invalid verdict for {finding_id}")
        if not str(verdict.get("rationale", "")).strip():
            raise StateError(f"verdict rationale is required for {finding_id}")
        if verdict["verdict"] != "rejected" and not str(
            verdict.get("required_change", "")
        ).strip():
            raise StateError(
                f"required_change is required for {finding_id}"
            )
        verdicts[finding_id] = verdict
    if set(verdicts) != finding_ids:
        raise StateError("every finding requires exactly one verdict")
    return findings, verdicts


def _document_hashes(ledger: Mapping[str, Any]) -> dict[str, str]:
    repo = Path(str(ledger["repo_root"]))
    return {
        relative: sha256_file(repo / relative)
        for relative in ledger["documents"]
    }


def _surviving_fingerprints(entry: Mapping[str, Any]) -> set[str]:
    return {
        item["fingerprint"]
        for item in entry["findings"]
        if item["severity"] in {"P0", "P1"}
        or item["verdict"] != "rejected"
    }


def _is_stagnated(iterations: list[dict]) -> bool:
    if len(iterations) < 3:
        return False
    recent = [_surviving_fingerprints(item) for item in iterations[-3:]]
    return bool(set.intersection(*recent))


def _is_oscillating(iterations: list[dict]) -> bool:
    if len(iterations) < 3:
        return False
    first, middle, latest = iterations[-3:]
    return (
        latest["document_hashes"] == first["document_hashes"]
        and latest["document_hashes"] != middle["document_hashes"]
        and any(
            item["verdict"] == "accepted"
            for item in latest["findings"]
        )
    )


def record_iteration(
    ledger_path: Path,
    iteration: Mapping[str, Any],
) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    findings, verdicts = _validate_iteration(iteration)
    applied = set(iteration.get("applied_finding_ids", []))
    accepted = {
        finding_id
        for finding_id, verdict in verdicts.items()
        if verdict["verdict"] == "accepted"
    }
    decisions = {
        finding_id
        for finding_id, verdict in verdicts.items()
        if verdict["verdict"] == "needs-user-decision"
    }
    validation = iteration.get("validation")
    if not isinstance(validation, Mapping):
        raise StateError("validation must be an object")

    repo = Path(str(ledger["repo_root"]))
    non_target = capture_non_target_state(repo, ledger["documents"])
    entry = {
        "number": len(ledger["iterations"]) + 1,
        "findings": [
            {
                "id": finding["id"],
                "concern_key": finding["concern_key"],
                "severity": finding["severity"],
                "document": finding["document"],
                "location": finding["location"],
                "fingerprint": finding_fingerprint(finding),
                "verdict": verdicts[finding["id"]]["verdict"],
                "rationale": verdicts[finding["id"]]["rationale"],
                "required_change": verdicts[finding["id"]].get(
                    "required_change"
                ),
            }
            for finding in findings
        ],
        "applied_finding_ids": sorted(applied),
        "validation": dict(validation),
        "document_hashes": _document_hashes(ledger),
        "non_target_fingerprint": non_target["fingerprint"],
    }
    ledger["iterations"].append(entry)
    save_ledger(ledger_path, ledger)

    if non_target["fingerprint"] != ledger["baseline"][
        "non_target_fingerprint"
    ]:
        baseline_files = ledger["baseline"]["non_target_files"]
        current_files = non_target["path_fingerprints"]
        changed_paths = sorted(
            path
            for path in set(baseline_files) | set(current_files)
            if baseline_files.get(path) != current_files.get(path)
        )
        return {
            "state": "paused",
            "reason": "non-target repository state changed",
            "paths": changed_paths,
        }
    if not validation.get("passed"):
        return {"state": "paused", "reason": "validation failed"}
    if accepted - applied:
        return {
            "state": "paused",
            "reason": "accepted findings remain unapplied",
        }
    if decisions:
        return {"state": "paused", "reason": "user decision required"}
    if _is_stagnated(ledger["iterations"]):
        return {
            "state": "paused",
            "reason": "same material finding survived three iterations",
        }
    if _is_oscillating(ledger["iterations"]):
        return {"state": "paused", "reason": "document state oscillated"}

    blocking = any(item["severity"] in {"P0", "P1"} for item in findings)
    if not blocking and not accepted:
        return {"state": "converged", "reason": "clean fresh review"}
    if entry["number"] >= ledger["max_iterations"]:
        return {"state": "paused", "reason": "maximum iterations reached"}
    if blocking:
        return {
            "state": "continue",
            "reason": "fresh reviewer reported P0 or P1",
        }
    return {
        "state": "continue",
        "reason": "accepted findings require a fresh review",
    }


def finish_ledger(path: Path) -> None:
    path.unlink(missing_ok=True)
    path.with_suffix(path.suffix + ".tmp").unlink(missing_ok=True)


def document_diff(path: Path) -> str:
    ledger = load_ledger(path)
    repo = Path(str(ledger["repo_root"]))
    chunks: list[str] = []
    for relative in ledger["documents"]:
        before = ledger["baseline"]["document_contents"][relative]
        after = (repo / relative).read_text(encoding="utf-8")
        chunks.extend(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"baseline/{relative}",
                tofile=f"current/{relative}",
            )
        )
    return "".join(chunks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    start = commands.add_parser("start")
    start.add_argument("--repo", type=Path, required=True)
    start.add_argument(
        "--document",
        type=Path,
        action="append",
        required=True,
    )
    start.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
    )

    finish = commands.add_parser("finish")
    finish.add_argument("--ledger", type=Path, required=True)

    diff = commands.add_parser("diff")
    diff.add_argument("--ledger", type=Path, required=True)

    record = commands.add_parser("record")
    record.add_argument("--ledger", type=Path, required=True)
    record.add_argument("--iteration", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "start":
            ledger_path, ledger = create_ledger(
                args.repo,
                args.document,
                max_iterations=args.max_iterations,
            )
            print(
                json.dumps(
                    {
                        "ledger_path": str(ledger_path),
                        "baseline": {
                            key: value
                            for key, value in ledger["baseline"].items()
                            if key != "document_contents"
                        },
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "diff":
            print(document_diff(args.ledger), end="")
            return 0
        if args.command == "record":
            iteration_payload = json.loads(
                args.iteration.read_text(encoding="utf-8")
            )
            print(
                json.dumps(
                    record_iteration(args.ledger, iteration_payload),
                    sort_keys=True,
                )
            )
            return 0
        finish_ledger(args.ledger)
        return 0
    except (
        StateError,
        OSError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"plan-review state error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
