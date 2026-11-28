#!/usr/bin/env python3
"""Lossless 3-level Book-TOC DAG re-parenting helper for restructure-commit.

Inspects a branch range (<base>..<head>), verifies that flattened dev-time
merges are trivial (merge^{tree} == p2^{tree} and clean fork from p1), validates
a Chapter -> Sub-Chapter -> Atomic commit partition, and rebuilds the branch
bottom-up using `git commit-tree` onto an isolated temporary branch.

Never squashes atomic commits, never mutates the target branch or working tree,
and verifies tree identity, diff identity, and lossless commit counts before
creating the temporary branch ref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SIGN_MODES = ("all", "outer", "none")
SUB_COMMITS_TOKEN = "{{SUB_COMMITS}}"


class DagRewrapError(RuntimeError):
    """Raised when git inspection, validation, or rebuild fails."""


@dataclass(frozen=True)
class CommitMeta:
    sha: str
    abbrev: str
    tree: str
    parents: tuple[str, ...]
    author_name: str
    author_email: str
    author_date: str
    committer_name: str
    committer_email: str
    committer_date: str
    sig_status: str
    subject: str
    raw_message: bytes


@dataclass(frozen=True)
class AtomicUnit:
    """One indivisible unit in the extracted stream.

    Normal units are single atomic commits (kind == "atomic").
    If a self-contained non-trivial merge is explicitly preserved, its entire
    subgraph becomes one unit (kind == "preserved_merge").
    """

    kind: str
    sha: str
    abbrev: str
    tree: str
    orig_parent: str
    orig_parent_tree: str
    subject: str
    sig_status: str
    orig_bubble: str | None = None
    subgraph_shas: tuple[str, ...] = ()


def run_git(
    repo: Path,
    *args: str,
    input_bytes: bytes | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        env=run_env,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        detail = stderr or stdout or f"git {' '.join(args)} failed (rc={result.returncode})"
        raise DagRewrapError(detail)
    return result


def rev_parse(repo: Path, ref: str) -> str:
    out = run_git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").stdout
    return out.decode("utf-8").strip()


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = run_git(
        repo,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        check=False,
    )
    return result.returncode == 0


def merge_base(repo: Path, a: str, b: str) -> str | None:
    result = run_git(repo, "merge-base", a, b, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8").strip() or None


def branch_exists(repo: Path, branch: str) -> bool:
    result = run_git(
        repo,
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/heads/{branch}",
        check=False,
    )
    return result.returncode == 0


def read_signing_config(repo: Path) -> bool:
    result = run_git(
        repo,
        "config",
        "--bool",
        "--get",
        "commit.gpgsign",
        check=False,
    )
    if result.returncode != 0:
        return False
    return result.stdout.decode("utf-8", errors="replace").strip().lower() == "true"


def _parse_commit_records(raw: bytes) -> list[CommitMeta]:
    commits: list[CommitMeta] = []
    if not raw:
        return commits
    for record in raw.split(b"\x00"):
        if not record:
            continue
        fields = record.split(b"\x1f", 12)
        if len(fields) != 13:
            raise DagRewrapError(f"Unexpected git log record shape ({len(fields)} fields)")
        (
            sha_b,
            abbrev_b,
            tree_b,
            parents_b,
            author_name_b,
            author_email_b,
            author_date_b,
            committer_name_b,
            committer_email_b,
            committer_date_b,
            sig_b,
            subject_b,
            raw_msg_b,
        ) = fields
        parents_str = parents_b.decode("utf-8").strip()
        parents = tuple(parents_str.split()) if parents_str else ()
        commits.append(
            CommitMeta(
                sha=sha_b.decode("utf-8").strip(),
                abbrev=abbrev_b.decode("utf-8").strip(),
                tree=tree_b.decode("utf-8").strip(),
                parents=parents,
                author_name=author_name_b.decode("utf-8", errors="surrogateescape"),
                author_email=author_email_b.decode("utf-8", errors="surrogateescape"),
                author_date=author_date_b.decode("utf-8"),
                committer_name=committer_name_b.decode("utf-8", errors="surrogateescape"),
                committer_email=committer_email_b.decode("utf-8", errors="surrogateescape"),
                committer_date=committer_date_b.decode("utf-8"),
                sig_status=sig_b.decode("utf-8").strip() or "N",
                subject=subject_b.decode("utf-8", errors="replace"),
                raw_message=raw_msg_b,
            )
        )
    return commits


_LOG_FORMAT = (
    "%H%x1f%h%x1f%T%x1f%P%x1f%an%x1f%ae%x1f%ad%x1f%cn%x1f%ce%x1f%cd%x1f%G?%x1f%s%x1f%B"
)


def load_commit(repo: Path, sha: str) -> CommitMeta:
    raw = run_git(
        repo,
        "log",
        "-1",
        "-z",
        "--date=raw",
        f"--format={_LOG_FORMAT}",
        sha,
    ).stdout
    records = _parse_commit_records(raw)
    if len(records) != 1:
        raise DagRewrapError(f"Could not load commit metadata for {sha}")
    return records[0]


def load_range_commits(repo: Path, base: str, head: str) -> dict[str, CommitMeta]:
    raw = run_git(
        repo,
        "log",
        "-z",
        "--topo-order",
        "--reverse",
        "--date=raw",
        f"--format={_LOG_FORMAT}",
        f"{base}..{head}",
    ).stdout
    return {c.sha: c for c in _parse_commit_records(raw)}


def rev_list_topo(repo: Path, start_exclusive: str, end_inclusive: str) -> list[str]:
    out = run_git(
        repo,
        "rev-list",
        "--topo-order",
        "--reverse",
        f"{start_exclusive}..{end_inclusive}",
    ).stdout
    text = out.decode("utf-8").strip()
    return text.splitlines() if text else []


def _check_merge_triviality(
    repo: Path,
    merge_commit: CommitMeta,
    p1: str,
    p2: str,
    commits_by_sha: dict[str, CommitMeta],
    base_sha: str,
    base_tree: str,
) -> tuple[bool, list[str], list[str]]:
    """Return (is_trivial, reasons, side_branch_shas)."""
    reasons: list[str] = []
    if p2 not in commits_by_sha:
        reasons.append("external_p2_outside_range")
        return False, reasons, []

    p2_meta = commits_by_sha[p2]
    if merge_commit.tree != p2_meta.tree:
        reasons.append("tree_differs_from_p2")

    mb = merge_base(repo, p1, p2)
    if mb != p1:
        reasons.append("forked_before_p1")

    side_shas = rev_list_topo(repo, p1, p2)
    side_set = set(side_shas)
    for sha in side_shas:
        meta = commits_by_sha.get(sha)
        if meta is None:
            reasons.append("side_commit_outside_range")
            break
        for parent in meta.parents:
            if parent != p1 and parent not in side_set:
                reasons.append("cross_edge_in_side_branch")
                break
        if "cross_edge_in_side_branch" in reasons:
            break

    # Sanity: if p1 == base_sha we already know base_tree exists.
    _ = base_sha, base_tree
    return len(reasons) == 0, reasons, side_shas


def inspect_range(
    repo: Path,
    base_ref: str,
    head_ref: str,
    preserve_merges: set[str] | None = None,
) -> dict[str, Any]:
    """Inspect <base>..<head> and extract the ordered atomic stream."""
    base = rev_parse(repo, base_ref)
    head = rev_parse(repo, head_ref)
    if base == head:
        raise DagRewrapError("Base and head resolve to the same commit; nothing to restructure.")
    if not is_ancestor(repo, base, head):
        raise DagRewrapError(f"Base {base_ref} ({base[:7]}) is not an ancestor of {head_ref} ({head[:7]}).")

    base_meta = load_commit(repo, base)
    commits_by_sha = load_range_commits(repo, base, head)
    if head not in commits_by_sha:
        raise DagRewrapError(f"Head commit {head[:7]} is missing from {base[:7]}..{head[:7]}.")

    preserve_set: set[str] = set()
    if preserve_merges:
        for ref in preserve_merges:
            preserve_set.add(rev_parse(repo, ref))

    def tree_of(sha: str) -> str:
        if sha == base:
            return base_meta.tree
        return commits_by_sha[sha].tree

    units: list[AtomicUnit] = []
    non_trivial_merges: list[dict[str, Any]] = []
    trivial_merge_shas: list[str] = []
    visited_shas: set[str] = set()

    def walk_linear(
        start_excl: str,
        end_incl: str,
        enclosing_bubble: str | None,
    ) -> None:
        # Walk first-parent spine backward from end_incl to start_excl.
        spine: list[CommitMeta] = []
        cursor = end_incl
        seen_on_spine: set[str] = set()
        while cursor != start_excl:
            if cursor in seen_on_spine:
                raise DagRewrapError(f"Cycle detected while walking from {end_incl[:7]} to {start_excl[:7]}")
            seen_on_spine.add(cursor)
            meta = commits_by_sha.get(cursor)
            if meta is None:
                raise DagRewrapError(
                    f"Commit {cursor[:7]} falls outside {base[:7]}..{head[:7]} before reaching {start_excl[:7]}."
                )
            spine.append(meta)
            if not meta.parents:
                raise DagRewrapError(
                    f"Reached root commit {cursor[:7]} before reaching boundary {start_excl[:7]}."
                )
            cursor = meta.parents[0]

        spine.reverse()
        prev = start_excl
        for meta in spine:
            if len(meta.parents) == 1:
                if meta.parents[0] != prev:
                    raise DagRewrapError(
                        f"Commit {meta.abbrev} parent {meta.parents[0][:7]} != expected {prev[:7]}."
                    )
                visited_shas.add(meta.sha)
                units.append(
                    AtomicUnit(
                        kind="atomic",
                        sha=meta.sha,
                        abbrev=meta.abbrev,
                        tree=meta.tree,
                        orig_parent=prev,
                        orig_parent_tree=tree_of(prev),
                        subject=meta.subject,
                        sig_status=meta.sig_status,
                        orig_bubble=enclosing_bubble,
                    )
                )
                prev = meta.sha
                continue

            if len(meta.parents) > 2:
                non_trivial_merges.append(
                    {
                        "sha": meta.sha,
                        "abbrev": meta.abbrev,
                        "subject": meta.subject,
                        "parents": list(meta.parents),
                        "reasons": ["octopus_merge"],
                        "preservable": False,
                    }
                )
                prev = meta.sha
                continue

            # Two-parent merge commit.
            p1, p2 = meta.parents
            if p1 != prev:
                raise DagRewrapError(
                    f"Merge {meta.abbrev} first parent {p1[:7]} != expected {prev[:7]}."
                )

            is_trivial, reasons, side_shas = _check_merge_triviality(
                repo,
                meta,
                p1,
                p2,
                commits_by_sha,
                base,
                base_meta.tree,
            )

            if is_trivial and meta.sha not in preserve_set:
                trivial_merge_shas.append(meta.sha)
                visited_shas.add(meta.sha)
                walk_linear(p1, p2, meta.subject)
                prev = meta.sha
                continue

            # Non-trivial (or explicitly preserved) merge.
            preservable = (
                "external_p2_outside_range" not in reasons
                and "forked_before_p1" not in reasons
                and "cross_edge_in_side_branch" not in reasons
                and "side_commit_outside_range" not in reasons
            )
            if not is_trivial:
                non_trivial_merges.append(
                    {
                        "sha": meta.sha,
                        "abbrev": meta.abbrev,
                        "subject": meta.subject,
                        "parents": [p1, p2],
                        "reasons": reasons,
                        "preservable": preservable,
                        "preserved": meta.sha in preserve_set and preservable,
                    }
                )

            if meta.sha in preserve_set and preservable:
                subgraph = tuple(side_shas) + (meta.sha,)
                visited_shas.update(subgraph)
                units.append(
                    AtomicUnit(
                        kind="preserved_merge",
                        sha=meta.sha,
                        abbrev=meta.abbrev,
                        tree=meta.tree,
                        orig_parent=prev,
                        orig_parent_tree=tree_of(prev),
                        subject=meta.subject,
                        sig_status=meta.sig_status,
                        orig_bubble=enclosing_bubble,
                        subgraph_shas=subgraph,
                    )
                )
            else:
                # Still mark reachable side commits visited so diagnostics stay accurate.
                visited_shas.add(meta.sha)
                visited_shas.update(side_shas)
            prev = meta.sha

    walk_linear(base, head, None)

    unvisited = [sha for sha in commits_by_sha if sha not in visited_shas]
    all_merges = [c for c in commits_by_sha.values() if len(c.parents) >= 2]
    unsigned_count = sum(1 for c in commits_by_sha.values() if c.sig_status == "N")

    return {
        "base": base,
        "base_abbrev": base_meta.abbrev,
        "base_tree": base_meta.tree,
        "head": head,
        "head_abbrev": commits_by_sha[head].abbrev,
        "head_tree": commits_by_sha[head].tree,
        "signing_enabled": read_signing_config(repo),
        "total_commits": len(commits_by_sha),
        "atomic_count": sum(1 for u in units if u.kind == "atomic"),
        "preserved_merge_units": sum(1 for u in units if u.kind == "preserved_merge"),
        "unit_count": len(units),
        "dev_merge_count": len(all_merges),
        "trivial_merge_count": len(trivial_merge_shas),
        "non_trivial_merges": non_trivial_merges,
        "unvisited_commits": unvisited,
        "unsigned_count": unsigned_count,
        "atomic_commits": [
            {
                "index": idx,
                "kind": u.kind,
                "sha": u.sha,
                "abbrev": u.abbrev,
                "tree": u.tree,
                "subject": u.subject,
                "sig_status": u.sig_status,
                "orig_bubble": u.orig_bubble,
                **({"subgraph_size": len(u.subgraph_shas)} if u.subgraph_shas else {}),
            }
            for idx, u in enumerate(units)
        ],
        "_units": units,
        "_commits_by_sha": commits_by_sha,
        "_base_meta": base_meta,
    }


def _resolve_unit_index(
    ref: str,
    units: list[AtomicUnit],
    sha_to_idx: dict[str, int],
    repo: Path,
) -> int:
    if ref in sha_to_idx:
        return sha_to_idx[ref]
    matches = [idx for sha, idx in sha_to_idx.items() if sha.startswith(ref)]
    if len(matches) == 1:
        return matches[0]
    full = rev_parse(repo, ref)
    if full in sha_to_idx:
        return sha_to_idx[full]
    raise DagRewrapError(
        f"Commit '{ref}' is not an atomic unit in the extracted stream for this branch."
    )


def validate_plan(repo: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Validate a 3-level Chapter -> Sub-Chapter -> Atomic plan against git history."""
    base_ref = plan.get("base")
    head_ref = plan.get("head")
    chapters_raw = plan.get("chapters")
    if not base_ref or not head_ref:
        raise DagRewrapError("Plan must define 'base' and 'head'.")
    if not isinstance(chapters_raw, list) or not chapters_raw:
        raise DagRewrapError("Plan must define a non-empty 'chapters' list.")

    preserve_merges = set(plan.get("preserve_merges") or [])
    inspection = inspect_range(repo, base_ref, head_ref, preserve_merges=preserve_merges)
    units: list[AtomicUnit] = inspection["_units"]

    errors: list[str] = []
    warnings: list[str] = []

    unhandled_non_trivial = [
        m for m in inspection["non_trivial_merges"] if not m.get("preserved")
    ]
    if unhandled_non_trivial:
        for m in unhandled_non_trivial:
            reasons = ", ".join(m["reasons"])
            hint = (
                "Add its hash to 'preserve_merges' to keep its subgraph intact."
                if m.get("preservable")
                else "Move 'base' past this merge or resolve the branch topology first."
            )
            errors.append(
                f"Non-trivial merge {m['abbrev']} ({m['subject']}): {reasons}. {hint}"
            )

    if inspection["unvisited_commits"]:
        errors.append(
            f"{len(inspection['unvisited_commits'])} commits in base..head were not reachable "
            f"via clean first-parent extraction."
        )

    sha_to_idx = {u.sha: idx for idx, u in enumerate(units)}
    seen_indices: set[int] = set()
    expected_next = 0
    resolved_chapters: list[dict[str, Any]] = []
    predicted_sub_merges = 0
    predicted_chapter_merges = 0

    for ch_idx, chapter in enumerate(chapters_raw, start=1):
        ch_title = (chapter.get("title") or "").strip()
        ch_msg = (chapter.get("message") or "").strip()
        sub_chapters_raw = chapter.get("sub_chapters")
        if not isinstance(sub_chapters_raw, list) or not sub_chapters_raw:
            errors.append(f"Chapter {ch_idx} must define a non-empty 'sub_chapters' list.")
            continue

        resolved_subs: list[dict[str, Any]] = []
        ch_unit_count = 0

        for sub_idx, sub in enumerate(sub_chapters_raw, start=1):
            sub_title = (sub.get("title") or "").strip()
            sub_msg = (sub.get("message") or "").strip()
            has_commits = "commits" in sub and sub["commits"] is not None
            has_range = "start" in sub or "end" in sub

            if has_commits and has_range:
                errors.append(
                    f"Chapter {ch_idx}.{sub_idx}: specify either 'commits' or 'start'/'end', not both."
                )
                continue
            if not has_commits and not has_range:
                errors.append(
                    f"Chapter {ch_idx}.{sub_idx}: must specify 'commits' or 'start' and 'end'."
                )
                continue

            sub_indices: list[int] = []
            try:
                if has_commits:
                    if not isinstance(sub["commits"], list) or not sub["commits"]:
                        raise DagRewrapError(
                            f"Chapter {ch_idx}.{sub_idx}: 'commits' must be a non-empty list."
                        )
                    for ref in sub["commits"]:
                        sub_indices.append(_resolve_unit_index(str(ref), units, sha_to_idx, repo))
                else:
                    if not sub.get("start") or not sub.get("end"):
                        raise DagRewrapError(
                            f"Chapter {ch_idx}.{sub_idx}: both 'start' and 'end' are required."
                        )
                    start_i = _resolve_unit_index(str(sub["start"]), units, sha_to_idx, repo)
                    end_i = _resolve_unit_index(str(sub["end"]), units, sha_to_idx, repo)
                    if start_i > end_i:
                        raise DagRewrapError(
                            f"Chapter {ch_idx}.{sub_idx}: 'start' ({sub['start']}) comes after 'end' ({sub['end']})."
                        )
                    sub_indices = list(range(start_i, end_i + 1))
            except DagRewrapError as exc:
                errors.append(str(exc))
                continue

            # Check duplicates and strict contiguous ordering.
            for idx in sub_indices:
                if idx in seen_indices:
                    errors.append(
                        f"Chapter {ch_idx}.{sub_idx}: duplicate atomic commit {units[idx].abbrev}."
                    )
                seen_indices.add(idx)

            expected_slice = list(range(expected_next, expected_next + len(sub_indices)))
            if sub_indices != expected_slice:
                errors.append(
                    f"Chapter {ch_idx}.{sub_idx}: commits are out of order or skip commits "
                    f"(expected indices {expected_slice[:3]}..{expected_slice[-1]}, "
                    f"got {sub_indices[:3]}..{sub_indices[-1]})."
                )
            expected_next = max(sub_indices) + 1

            sub_units = [units[i] for i in sub_indices]
            will_wrap_sub = len(sub_units) >= 2
            if will_wrap_sub:
                predicted_sub_merges += 1
                if not sub_msg:
                    errors.append(
                        f"Chapter {ch_idx}.{sub_idx} ({sub_title or 'untitled'}) has "
                        f"{len(sub_units)} commits and requires a merge 'message'."
                    )
            else:
                if sub_msg:
                    warnings.append(
                        f"Chapter {ch_idx}.{sub_idx} has 1 commit; minimum bubble size is 2, "
                        f"so no sub-chapter merge bubble will be created."
                    )

            sample = [
                {"abbrev": u.abbrev, "subject": u.subject}
                for u in (sub_units[:2] + (sub_units[-1:] if len(sub_units) > 2 else []))
            ]
            resolved_subs.append(
                {
                    "id": f"{ch_idx}.{sub_idx}",
                    "title": sub_title or sub_units[-1].subject,
                    "message": sub_msg,
                    "unit_indices": sub_indices,
                    "atomic_count": len(sub_units),
                    "first_abbrev": sub_units[0].abbrev,
                    "last_abbrev": sub_units[-1].abbrev,
                    "end_tree": sub_units[-1].tree,
                    "creates_bubble": will_wrap_sub,
                    "sample_commits": sample,
                }
            )
            ch_unit_count += len(sub_units)

        will_wrap_chapter = len(resolved_subs) >= 2
        if will_wrap_chapter:
            predicted_chapter_merges += 1
            if not ch_msg:
                errors.append(
                    f"Chapter {ch_idx} ({ch_title or 'untitled'}) has {len(resolved_subs)} "
                    f"sub-chapters and requires a chapter merge 'message'."
                )
        elif len(resolved_subs) == 1:
            warnings.append(
                f"Chapter {ch_idx} ({ch_title or 'untitled'}) has only 1 sub-chapter; "
                f"minimum bubble size is 2, so no outer chapter double-wrap will be added."
            )

        resolved_chapters.append(
            {
                "index": ch_idx,
                "title": ch_title or (ch_msg.splitlines()[0] if ch_msg else f"Chapter {ch_idx}"),
                "message": ch_msg,
                "sub_chapters": resolved_subs,
                "sub_chapter_count": len(resolved_subs),
                "atomic_count": ch_unit_count,
                "creates_bubble": will_wrap_chapter,
                "end_tree": resolved_subs[-1]["end_tree"] if resolved_subs else None,
            }
        )

    missing_indices = [i for i in range(len(units)) if i not in seen_indices]
    if missing_indices:
        missing_abbrevs = ", ".join(units[i].abbrev for i in missing_indices[:5])
        suffix = "..." if len(missing_indices) > 5 else ""
        errors.append(
            f"{len(missing_indices)} atomic commits are missing from the plan: {missing_abbrevs}{suffix}"
        )

    preserved_inner_commits = sum(
        len(u.subgraph_shas) if u.kind == "preserved_merge" else 1 for u in units
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "base": inspection["base"],
        "head": inspection["head"],
        "head_tree": inspection["head_tree"],
        "original_total_commits": inspection["total_commits"],
        "original_atomic_commits": inspection["atomic_count"],
        "preserved_merge_units": inspection["preserved_merge_units"],
        "non_trivial_merges": inspection["non_trivial_merges"],
        "unsigned_count": inspection["unsigned_count"],
        "signing_enabled": inspection["signing_enabled"],
        "predicted_chapter_merges": predicted_chapter_merges,
        "predicted_sub_chapter_merges": predicted_sub_merges,
        "predicted_total_commits": (
            preserved_inner_commits + predicted_sub_merges + predicted_chapter_merges
        ),
        "toc": resolved_chapters,
        "_inspection": inspection,
    }


def _commit_tree(
    repo: Path,
    *,
    tree: str,
    parents: list[str],
    message: bytes,
    env: dict[str, str],
    sign: bool,
    role: str,
    old_sha: str | None,
    subject: str,
    fallback_log: list[dict[str, Any]],
) -> tuple[str, bool]:
    """Run `git commit-tree`, falling back to `--no-gpg-sign` on signing failure."""
    base_args = ["commit-tree", tree]
    for parent in parents:
        base_args.extend(["-p", parent])

    if sign:
        result = run_git(
            repo,
            *base_args,
            "-S",
            input_bytes=message,
            env=env,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8").strip(), True
        err_text = result.stderr.decode("utf-8", errors="replace").strip()
        fallback = run_git(
            repo,
            *base_args,
            "--no-gpg-sign",
            input_bytes=message,
            env=env,
            check=True,
        )
        new_sha = fallback.stdout.decode("utf-8").strip()
        fallback_log.append(
            {
                "role": role,
                "old_sha": old_sha,
                "new_sha": new_sha,
                "subject": subject,
                "error": err_text or "signing failed",
            }
        )
        return new_sha, False

    result = run_git(
        repo,
        *base_args,
        "--no-gpg-sign",
        input_bytes=message,
        env=env,
        check=True,
    )
    return result.stdout.decode("utf-8").strip(), False


def _render_merge_message(template: str, entries: list[tuple[str, str]]) -> bytes:
    lines = "\n".join(f"  - {sha[:7]} {subject}" for sha, subject in entries)
    rendered = template.replace(SUB_COMMITS_TOKEN, lines)
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered.encode("utf-8")


def _commit_env(meta: CommitMeta) -> dict[str, str]:
    return {
        "GIT_AUTHOR_NAME": meta.author_name,
        "GIT_AUTHOR_EMAIL": meta.author_email,
        "GIT_AUTHOR_DATE": meta.author_date,
        "GIT_COMMITTER_NAME": meta.committer_name,
        "GIT_COMMITTER_EMAIL": meta.committer_email,
        "GIT_COMMITTER_DATE": meta.committer_date,
    }


def build_toc_branch(
    repo: Path,
    plan: dict[str, Any],
    *,
    target_tmp: str,
    sign_mode: str = "all",
) -> dict[str, Any]:
    """Rebuild the branch bottom-up on an isolated temp branch and verify 6 invariants."""
    if sign_mode not in SIGN_MODES:
        raise DagRewrapError(f"Unsupported sign mode '{sign_mode}'. Choose from {SIGN_MODES}.")
    if branch_exists(repo, target_tmp):
        raise DagRewrapError(
            f"Temporary branch '{target_tmp}' already exists. Choose a fresh branch name."
        )

    validation = validate_plan(repo, plan)
    if not validation["valid"]:
        raise DagRewrapError(
            "Plan validation failed:\n- " + "\n- ".join(validation["errors"])
        )

    inspection = validation["_inspection"]
    units: list[AtomicUnit] = inspection["_units"]
    commits_by_sha: dict[str, CommitMeta] = inspection["_commits_by_sha"]
    base_sha: str = inspection["base"]
    orig_head: str = inspection["head"]
    orig_head_tree: str = inspection["head_tree"]

    fallback_log: list[dict[str, Any]] = []
    emitted_atomic_checks: list[tuple[AtomicUnit, str, str]] = []
    chapter_merges_created: list[dict[str, Any]] = []
    sub_merges_created: list[dict[str, Any]] = []
    reused_count = 0

    def emit_unit(unit: AtomicUnit, parent_sha: str) -> tuple[str, str]:
        nonlocal reused_count
        if unit.kind == "atomic":
            meta = commits_by_sha[unit.sha]
            can_reuse = (
                meta.parents == (parent_sha,)
                and (sign_mode != "all" or meta.sig_status != "N")
            )
            if can_reuse:
                reused_count += 1
                new_sha = meta.sha
            else:
                new_sha, _ = _commit_tree(
                    repo,
                    tree=meta.tree,
                    parents=[parent_sha],
                    message=meta.raw_message,
                    env=_commit_env(meta),
                    sign=(sign_mode == "all"),
                    role="atomic",
                    old_sha=meta.sha,
                    subject=meta.subject,
                    fallback_log=fallback_log,
                )
            emitted_atomic_checks.append((unit, new_sha, parent_sha))
            return new_sha, meta.subject

        # Preserved non-trivial merge subgraph: re-parent every commit inside
        # unit.subgraph_shas verbatim onto parent_sha.
        local_map: dict[str, str] = {unit.orig_parent: parent_sha}
        for old_sha in unit.subgraph_shas:
            meta = commits_by_sha[old_sha]
            new_parents = [local_map[p] for p in meta.parents]
            can_reuse = (
                tuple(new_parents) == meta.parents
                and (sign_mode != "all" or meta.sig_status != "N")
            )
            if can_reuse:
                reused_count += 1
                new_sha = meta.sha
            else:
                new_sha, _ = _commit_tree(
                    repo,
                    tree=meta.tree,
                    parents=new_parents,
                    message=meta.raw_message,
                    env=_commit_env(meta),
                    sign=(sign_mode == "all"),
                    role="preserved_merge_node",
                    old_sha=meta.sha,
                    subject=meta.subject,
                    fallback_log=fallback_log,
                )
            local_map[old_sha] = new_sha
        final_merge_sha = local_map[unit.sha]
        emitted_atomic_checks.append((unit, final_merge_sha, parent_sha))
        return final_merge_sha, unit.subject

    chapter_spine = base_sha
    built_toc: list[dict[str, Any]] = []

    for chapter in validation["toc"]:
        sub_spine = chapter_spine
        chapter_sub_entries: list[tuple[str, str]] = []
        built_subs: list[dict[str, Any]] = []

        for sub in chapter["sub_chapters"]:
            sub_units = [units[i] for i in sub["unit_indices"]]
            if len(sub_units) == 1:
                new_sha, subject = emit_unit(sub_units[0], sub_spine)
                sub_spine = new_sha
                chapter_sub_entries.append((new_sha, subject))
                built_subs.append(
                    {
                        "id": sub["id"],
                        "sha": new_sha,
                        "abbrev": new_sha[:7],
                        "title": subject,
                        "atomic_count": 1,
                        "is_bubble": False,
                        "expected_tree": sub["end_tree"],
                    }
                )
            else:
                side_tip = sub_spine
                atomic_entries: list[tuple[str, str]] = []
                for unit in sub_units:
                    side_tip, subject = emit_unit(unit, side_tip)
                    atomic_entries.append((side_tip, subject))

                sub_msg_bytes = _render_merge_message(sub["message"], atomic_entries)
                sub_subject = sub["message"].splitlines()[0].strip()
                sub_merge_sha, _ = _commit_tree(
                    repo,
                    tree=sub["end_tree"],
                    parents=[sub_spine, side_tip],
                    message=sub_msg_bytes,
                    env={},
                    sign=(sign_mode in ("all", "outer")),
                    role="sub_chapter_merge",
                    old_sha=None,
                    subject=sub_subject,
                    fallback_log=fallback_log,
                )
                sub_spine = sub_merge_sha
                chapter_sub_entries.append((sub_merge_sha, sub_subject))
                sub_info = {
                    "id": sub["id"],
                    "sha": sub_merge_sha,
                    "abbrev": sub_merge_sha[:7],
                    "title": sub_subject,
                    "atomic_count": len(sub_units),
                    "is_bubble": True,
                    "expected_tree": sub["end_tree"],
                }
                sub_merges_created.append(sub_info)
                built_subs.append(sub_info)

        if len(chapter_sub_entries) >= 2:
            ch_msg_bytes = _render_merge_message(chapter["message"], chapter_sub_entries)
            ch_subject = chapter["message"].splitlines()[0].strip()
            ch_merge_sha, _ = _commit_tree(
                repo,
                tree=chapter["end_tree"],
                parents=[chapter_spine, sub_spine],
                message=ch_msg_bytes,
                env={},
                sign=(sign_mode in ("all", "outer")),
                role="chapter_merge",
                old_sha=None,
                subject=ch_subject,
                fallback_log=fallback_log,
            )
            chapter_spine = ch_merge_sha
            ch_info = {
                "index": chapter["index"],
                "sha": ch_merge_sha,
                "abbrev": ch_merge_sha[:7],
                "title": ch_subject,
                "is_bubble": True,
                "expected_tree": chapter["end_tree"],
                "sub_chapters": built_subs,
            }
            chapter_merges_created.append(ch_info)
            built_toc.append(ch_info)
        else:
            chapter_spine = sub_spine
            built_toc.append(
                {
                    "index": chapter["index"],
                    "sha": chapter_spine,
                    "abbrev": chapter_spine[:7],
                    "title": chapter_sub_entries[0][1],
                    "is_bubble": built_subs[0]["is_bubble"],
                    "expected_tree": chapter["end_tree"],
                    "sub_chapters": built_subs,
                }
            )

    final_sha = chapter_spine

    # --- 6-Point Self-Verification BEFORE Creating Temporary Branch Ref ---
    # 1. Final tree identity & empty diff against original head.
    final_meta = load_commit(repo, final_sha)
    if final_meta.tree != orig_head_tree:
        raise DagRewrapError(
            f"Verification failed: final tree {final_meta.tree} != original tree {orig_head_tree}."
        )
    diff_out = run_git(repo, "diff", orig_head, final_sha).stdout
    if diff_out:
        raise DagRewrapError("Verification failed: non-empty git diff between original HEAD and rebuilt tip.")

    # 2. Every Chapter & Sub-Chapter endpoint tree matches its original boundary tree.
    new_commits_map = load_range_commits(repo, base_sha, final_sha)
    for ch in built_toc:
        if new_commits_map[ch["sha"]].tree != ch["expected_tree"]:
            raise DagRewrapError(
                f"Verification failed: chapter {ch['index']} tree mismatch ({ch['abbrev']})."
            )
        for sub in ch["sub_chapters"]:
            if new_commits_map[sub["sha"]].tree != sub["expected_tree"]:
                raise DagRewrapError(
                    f"Verification failed: sub-chapter {sub['id']} tree mismatch ({sub['abbrev']})."
                )

    # 3. Exact lossless commit count (zero squashing, zero dropped commits).
    expected_total = validation["predicted_total_commits"]
    if len(new_commits_map) != expected_total:
        raise DagRewrapError(
            f"Verification failed: expected {expected_total} total commits, built {len(new_commits_map)}."
        )
    if len(emitted_atomic_checks) != len(units):
        raise DagRewrapError(
            f"Verification failed: emitted {len(emitted_atomic_checks)} units != {len(units)} original units."
        )

    # 4. Atomic diff identity (every unit tree & parent tree match original).
    base_tree = inspection["base_tree"]
    for unit, new_sha, new_parent_sha in emitted_atomic_checks:
        new_meta = new_commits_map[new_sha]
        new_parent_tree = base_tree if new_parent_sha == base_sha else new_commits_map[new_parent_sha].tree
        if new_meta.tree != unit.tree:
            raise DagRewrapError(
                f"Verification failed: atomic commit {unit.abbrev} -> {new_sha[:7]} tree changed."
            )
        if new_parent_tree != unit.orig_parent_tree:
            raise DagRewrapError(
                f"Verification failed: atomic commit {unit.abbrev} -> {new_sha[:7]} parent tree changed."
            )

    # 5. Clean Level-1 and Level-2 --first-parent TOC topology.
    l1_shas = run_git(
        repo,
        "rev-list",
        "--first-parent",
        "--reverse",
        f"{base_sha}..{final_sha}",
    ).stdout.decode("utf-8").strip().splitlines()
    expected_l1 = [ch["sha"] for ch in built_toc]
    if l1_shas != expected_l1:
        raise DagRewrapError(
            f"Verification failed: Level-1 TOC mismatch ({len(l1_shas)} != {len(expected_l1)})."
        )

    prev_ch_sha = base_sha
    for ch in built_toc:
        if ch["is_bubble"] and len(ch["sub_chapters"]) >= 2:
            ch_p2 = new_commits_map[ch["sha"]].parents[1]
            l2_shas = run_git(
                repo,
                "rev-list",
                "--first-parent",
                "--reverse",
                f"{prev_ch_sha}..{ch_p2}",
            ).stdout.decode("utf-8").strip().splitlines()
            expected_l2 = [sub["sha"] for sub in ch["sub_chapters"]]
            if l2_shas != expected_l2:
                raise DagRewrapError(
                    f"Verification failed: Chapter {ch['index']} Level-2 sub-chapters mismatch."
                )
        prev_ch_sha = ch["sha"]

    # 6. Signature audit.
    sig_counts: dict[str, int] = {}
    unsigned_shas: list[str] = []
    for sha, meta in new_commits_map.items():
        sig_counts[meta.sig_status] = sig_counts.get(meta.sig_status, 0) + 1
        if meta.sig_status == "N":
            unsigned_shas.append(sha)

    # All 6 checks passed — create ONLY the isolated temporary branch ref.
    run_git(repo, "branch", target_tmp, final_sha)

    return {
        "status": "verified",
        "target_tmp_branch": target_tmp,
        "final_sha": final_sha,
        "final_abbrev": final_sha[:7],
        "final_tree": final_meta.tree,
        "base": base_sha,
        "orig_head": orig_head,
        "sign_mode": sign_mode,
        "reused_prefix_commits": reused_count,
        "counts": {
            "original_total": inspection["total_commits"],
            "original_atomic": inspection["atomic_count"],
            "rebuilt_total": len(new_commits_map),
            "rebuilt_atomic": inspection["atomic_count"],
            "chapter_merges": len(chapter_merges_created),
            "sub_chapter_merges": len(sub_merges_created),
            "signed_commits": len(new_commits_map) - len(unsigned_shas),
            "unsigned_commits": len(unsigned_shas),
        },
        "signature_statuses": sig_counts,
        "unsigned_fallback_commits": fallback_log,
        "toc": built_toc,
    }


def _strip_internal(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if not k.startswith("_")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect, validate, and build lossless 3-level Book-TOC git histories.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to the git repository (defaults to current working directory).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_p = subparsers.add_parser(
        "inspect",
        help="Inspect <base>..<head>, audit merge triviality, and list ordered atomic commits.",
    )
    inspect_p.add_argument("base", help="Base commit/branch ref (exclusive).")
    inspect_p.add_argument("head", nargs="?", default="HEAD", help="Head commit/branch ref (inclusive).")
    inspect_p.add_argument(
        "--preserve-merge",
        action="append",
        default=[],
        help="Optional non-trivial merge SHA to keep intact as an indivisible unit.",
    )

    validate_p = subparsers.add_parser(
        "validate",
        help="Validate a JSON Chapter -> Sub-Chapter -> Atomic plan without modifying git.",
    )
    validate_p.add_argument("plan", type=Path, help="Path to plan JSON file.")

    build_p = subparsers.add_parser(
        "build",
        help="Build the validated Book-TOC DAG on an isolated temp branch and verify 6 invariants.",
    )
    build_p.add_argument("plan", type=Path, help="Path to plan JSON file.")
    build_p.add_argument(
        "--target-tmp",
        required=True,
        help="New temporary branch name (must not already exist; target branch is never touched).",
    )
    build_p.add_argument(
        "--sign",
        choices=SIGN_MODES,
        default="all",
        help="Signing mode: all (sign every rebuilt commit), outer (new merges only), or none.",
    )

    args = parser.parse_args(argv)
    repo = args.repo.resolve()

    try:
        if args.command == "inspect":
            result = _strip_internal(
                inspect_range(repo, args.base, args.head, preserve_merges=set(args.preserve_merge))
            )
            print(json.dumps(result, indent=2))
            return 0

        plan_data = json.loads(args.plan.read_text(encoding="utf-8"))
        if args.command == "validate":
            result = _strip_internal(validate_plan(repo, plan_data))
            print(json.dumps(result, indent=2))
            return 0 if result["valid"] else 1

        if args.command == "build":
            result = build_toc_branch(
                repo,
                plan_data,
                target_tmp=args.target_tmp,
                sign_mode=args.sign,
            )
            print(json.dumps(result, indent=2))
            return 0
    except (DagRewrapError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
