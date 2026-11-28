"""Integration tests for skills/restructure-commit/helpers/dag_rewrap.py.

Every test builds a real temporary git repository in tmp_path so git plumbing,
merge topologies, tree identity, metadata fidelity, and error paths are verified
against real git behavior.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


HELPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HELPER_DIR))

import dag_rewrap  # noqa: E402


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    run_env = os.environ.copy()
    run_env.setdefault("GIT_AUTHOR_NAME", "Joe Tester")
    run_env.setdefault("GIT_AUTHOR_EMAIL", "joe@example.com")
    run_env.setdefault("GIT_COMMITTER_NAME", "Joe Tester")
    run_env.setdefault("GIT_COMMITTER_EMAIL", "joe@example.com")
    if env:
        run_env.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=run_env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Joe Tester")
    _git(repo, "config", "user.email", "joe@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(
        repo,
        "commit",
        "-m",
        "chore: initial commit",
        env={
            "GIT_AUTHOR_DATE": "1795000000 +0800",
            "GIT_COMMITTER_DATE": "1795000000 +0800",
        },
    )
    return repo


def _commit_file(
    repo: Path,
    rel_path: str,
    content: str,
    message: str,
    ts: int,
    *,
    author_name: str = "Joe Tester",
    author_email: str = "joe@example.com",
) -> str:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    _git(repo, "add", rel_path)
    _git(
        repo,
        "commit",
        "-m",
        message,
        env={
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_AUTHOR_DATE": f"{ts} +0800",
            "GIT_COMMITTER_NAME": "Joe Committer",
            "GIT_COMMITTER_EMAIL": "committer@example.com",
            "GIT_COMMITTER_DATE": f"{ts + 5} +0800",
        },
    )
    return _git(repo, "rev-parse", "HEAD")


def _build_waymark_shaped_branch(repo: Path) -> dict[str, object]:
    """Build a realistic messy dev-time phase branch:
    - Dev bubble 1: 5 atomic commits (2 workspace + 3 CI) merged as one flat bubble
    - Loose doc commit + dev review bubble (2 commits) + loose style + loose ADR commit
    Total: 10 atomic commits, 2 dev-time merges (12 commits in main..phase/1).
    """
    base = _git(repo, "rev-parse", "main")
    _git(repo, "checkout", "-b", "phase/1")
    atomics: list[str] = []

    # Dev bubble 1 (5 atomic commits in one flat bubble, like Waymark M1)
    _git(repo, "checkout", "-b", "dev/m1-all")
    atomics.append(_commit_file(repo, "Cargo.toml", "[workspace]\n", "build: add workspace\n\nBody 1 — unicode café", 1795000100))
    atomics.append(_commit_file(repo, "budgets.toml", "max=100\n", "build: add budgets", 1795000200))
    atomics.append(_commit_file(repo, "ci/hygiene.py", "print('ok')\n", "ci: add hygiene script", 1795000300))
    atomics.append(_commit_file(repo, "ci/budgets.py", "print('ok')\n", "ci: add budget script", 1795000400))
    atomics.append(_commit_file(repo, "ci/all.py", "print('all')\n", "ci: add check_all runner", 1795000500))
    _git(repo, "checkout", "phase/1")
    _git(repo, "merge", "--no-ff", "dev/m1-all", "-m", "build(workspace): dev bubble M1")
    _git(repo, "branch", "-d", "dev/m1-all")

    # Loose docs commits (2 commits, ungrouped)
    atomics.append(_commit_file(repo, "AGENTS.md", "rule 1\n", "docs(agents): clarify clarity rule", 1795000600, author_name="Alice Dev", author_email="alice@example.com"))
    atomics.append(_commit_file(repo, "AGENTS.md", "rule 1\nrule 2\n", "docs(agents): record frontier model note", 1795000700))

    # Partial review-fix dev bubble (2 commits) + dangling style commit outside it
    _git(repo, "checkout", "-b", "dev/review-fix")
    atomics.append(_commit_file(repo, "src/view.rs", "fn view() {}\n", "fix(privacy): close view leak", 1795000800))
    atomics.append(_commit_file(repo, "src/rules.rs", "fn rules() {}\n", "fix(core): fix limited use spend", 1795000900))
    _git(repo, "checkout", "phase/1")
    _git(repo, "merge", "--no-ff", "dev/review-fix", "-m", "fix(core): partial review fixes")
    _git(repo, "branch", "-d", "dev/review-fix")

    atomics.append(_commit_file(repo, "src/rules.rs", "fn rules() {}\n// fmt\n", "style(core): format review fix files", 1795001000))
    atomics.append(_commit_file(repo, "docs/adr/0012.md", "Accepted\n", "docs(adr): accept ADR 0012", 1795001100))

    head = _git(repo, "rev-parse", "HEAD")
    return {"base": base, "head": head, "atomics": atomics}


def test_inspect_extracts_ordered_atomics_and_verifies_trivial_merges(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    fixture = _build_waymark_shaped_branch(repo)

    info = dag_rewrap.inspect_range(repo, "main", "HEAD")

    assert info["total_commits"] == 13
    assert info["atomic_count"] == 11
    assert info["dev_merge_count"] == 2
    assert info["trivial_merge_count"] == 2
    assert info["non_trivial_merges"] == []
    assert info["unvisited_commits"] == []
    assert [c["sha"] for c in info["atomic_commits"]] == fixture["atomics"]


def test_build_creates_uniform_3_level_book_toc_without_squashing(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    fixture = _build_waymark_shaped_branch(repo)
    atomics: list[str] = fixture["atomics"]  # type: ignore[assignment]
    orig_head: str = fixture["head"]  # type: ignore[assignment]

    # Target Book-TOC:
    # Chapter 1 (2 sub-chapters): 1.1 workspace (2 atomic), 1.2 CI (3 atomic)
    # Chapter 2 (3 sub-chapters): 2.1 docs (2 atomic), 2.2 review+fmt (3 atomic), 2.3 ADR (1 atomic, no sub-bubble!)
    # Expected total: 10 atomic + 4 sub-chapter merges + 2 chapter merges = 16 commits!
    plan = {
        "base": "main",
        "head": orig_head,
        "chapters": [
            {
                "title": "build(workspace): Milestone 1 — Workspace and local CI",
                "message": (
                    "build(workspace): Milestone 1 — Workspace and local CI\n\n"
                    "Intent.\n\n[--- Changes ---]\n\n- Sub-chapters included:\n"
                    "{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nClean."
                ),
                "sub_chapters": [
                    {
                        "title": "build(workspace): workspace and budgets",
                        "message": (
                            "build(workspace): workspace and budgets\n\n"
                            "Intent.\n\n[--- Changes ---]\n\n- Sub-commits included:\n"
                            "{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nClean."
                        ),
                        "start": atomics[0],
                        "end": atomics[1],
                    },
                    {
                        "title": "ci: local check scripts",
                        "message": (
                            "ci: local check scripts\n\n"
                            "Intent.\n\n[--- Changes ---]\n\n- Sub-commits included:\n"
                            "{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nClean."
                        ),
                        "start": atomics[2],
                        "end": atomics[4],
                    },
                ],
            },
            {
                "title": "fix(core,docs): Post-Gate-1 cleanup",
                "message": (
                    "fix(core,docs): Post-Gate-1 cleanup\n\n"
                    "Intent.\n\n[--- Changes ---]\n\n- Sub-chapters included:\n"
                    "{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nClean."
                ),
                "sub_chapters": [
                    {
                        "title": "docs(agents): governance rules",
                        "message": (
                            "docs(agents): governance rules\n\n"
                            "Intent.\n\n[--- Changes ---]\n\n- Sub-commits included:\n"
                            "{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nClean."
                        ),
                        "commits": [atomics[5], atomics[6]],
                    },
                    {
                        "title": "fix(core): review fixes and formatting",
                        "message": (
                            "fix(core): review fixes and formatting\n\n"
                            "Intent.\n\n[--- Changes ---]\n\n- Sub-commits included:\n"
                            "{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nClean."
                        ),
                        "start": atomics[7],
                        "end": atomics[9],
                    },
                    {
                        "title": "docs(adr): accept ADR 0012",
                        "commits": [atomics[9]],  # Intentionally tested below? Wait: index 9 is style; 10 doesn't exist!
                    },
                ],
            },
        ],
    }
    # Fix sub-chapter 2.2 vs 2.3 indices: 7..9 = [7, 8, 9] (3 commits), wait: atomics has 10 items (0..9)!
    # Let's check: 0..1 (2), 2..4 (3), 5..6 (2), 7..8 (2), 9..9 (1) -> Wait:
    # Actually let's check atomics:
    # 0 Cargo.toml, 1 budgets.toml, 2 hygiene, 3 budgets, 4 all,
    # 5 AGENTS 1, 6 AGENTS 2, 7 view.rs, 8 rules.rs, 9 rules fmt, 10 ADR!
    # That's 11 atomics! Let's assert len(atomics) == 11 and slice cleanly.
    assert len(atomics) == 11
    plan["chapters"][1]["sub_chapters"][2]["commits"] = [atomics[10]]

    result = dag_rewrap.build_toc_branch(
        repo,
        plan,
        target_tmp="restructure-toc-tmp-test",
        sign_mode="none",
    )

    # Target branch phase/1 was NEVER touched!
    assert _git(repo, "rev-parse", "phase/1") == orig_head

    # Exact lossless counts: 11 atomic + 4 sub-merges + 2 chapter merges = 17 commits.
    assert result["counts"]["original_atomic"] == 11
    assert result["counts"]["rebuilt_atomic"] == 11
    assert result["counts"]["sub_chapter_merges"] == 4
    assert result["counts"]["chapter_merges"] == 2
    assert result["counts"]["rebuilt_total"] == 17

    # Byte-identical final tree & empty diff.
    assert _git(repo, "diff", "phase/1", "restructure-toc-tmp-test") == ""

    # Level 1 TOC shows exactly 2 chapters.
    l1 = _git(repo, "log", "--first-parent", "--reverse", "--format=%s", "main..restructure-toc-tmp-test").splitlines()
    assert l1 == [
        "build(workspace): Milestone 1 — Workspace and local CI",
        "fix(core,docs): Post-Gate-1 cleanup",
    ]

    # Chapter 2 Level 2 shows 3 entries: 2 sub-bubbles + 1 single atomic commit (no redundant 1-commit bubble!).
    ch1_sha = result["toc"][0]["sha"]
    ch2_sha = result["toc"][1]["sha"]
    l2_ch2 = _git(repo, "log", "--first-parent", "--reverse", "--format=%P|%s", f"{ch1_sha}..{ch2_sha}^2").splitlines()
    assert len(l2_ch2) == 3
    assert len(l2_ch2[0].split("|")[0].split()) == 2  # 2.1 sub-bubble (2 parents)
    assert len(l2_ch2[1].split("|")[0].split()) == 2  # 2.2 sub-bubble (2 parents)
    assert len(l2_ch2[2].split("|")[0].split()) == 1  # 2.3 single commit (1 parent, NO 1-commit bubble!)
    assert l2_ch2[2].endswith("|docs(adr): accept ADR 0012")

    # {{SUB_COMMITS}} was replaced with the ACTUAL NEW hashes, not stale pre-rewrite hashes!
    ch2_body = _git(repo, "log", "-1", "--format=%B", ch2_sha)
    assert "{{SUB_COMMITS}}" not in ch2_body
    for sub in result["toc"][1]["sub_chapters"]:
        assert sub["abbrev"] in ch2_body

    # Original author, committer, timestamps, and UTF-8 multi-line message preserved verbatim!
    sub1_1_sha = result["toc"][0]["sub_chapters"][0]["sha"]
    rebuilt_first_atomic = _git(repo, "rev-list", "--reverse", f"main..{sub1_1_sha}^2").splitlines()[0]
    assert _git(repo, "log", "-1", "--format=%B", rebuilt_first_atomic) == "build: add workspace\n\nBody 1 — unicode café"
    assert _git(repo, "log", "-1", "--date=raw", "--format=%ad|%cd", rebuilt_first_atomic) == "1795000100 +0800|1795000105 +0800"

    sub2_1_sha = result["toc"][1]["sub_chapters"][0]["sha"]
    rebuilt_alice = _git(repo, "rev-list", "--reverse", f"{ch1_sha}..{sub2_1_sha}^2").splitlines()[0]
    assert _git(repo, "log", "-1", "--format=%an|%ae", rebuilt_alice) == "Alice Dev|alice@example.com"


def test_validate_rejects_missing_or_duplicate_atomic_commits(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    fixture = _build_waymark_shaped_branch(repo)
    atomics: list[str] = fixture["atomics"]  # type: ignore[assignment]

    # Omit the last commit (atomics[10]) -> must fail validation!
    missing_plan = {
        "base": "main",
        "head": fixture["head"],
        "chapters": [
            {
                "title": "Chapter 1",
                "message": "feat: ch1",
                "sub_chapters": [
                    {"title": "sub 1", "message": "feat: s1", "start": atomics[0], "end": atomics[4]},
                    {"title": "sub 2", "message": "feat: s2", "start": atomics[5], "end": atomics[9]},
                ],
            }
        ],
    }
    report = dag_rewrap.validate_plan(repo, missing_plan)
    assert not report["valid"]
    assert any("missing" in err.lower() for err in report["errors"])

    # Overlapping slices (duplicate atomics[4]) -> must fail validation!
    dup_plan = {
        "base": "main",
        "head": fixture["head"],
        "chapters": [
            {
                "title": "Chapter 1",
                "message": "feat: ch1",
                "sub_chapters": [
                    {"title": "sub 1", "message": "feat: s1", "start": atomics[0], "end": atomics[4]},
                    {"title": "sub 2", "message": "feat: s2", "start": atomics[4], "end": atomics[10]},
                ],
            }
        ],
    }
    dup_report = dag_rewrap.validate_plan(repo, dup_plan)
    assert not dup_report["valid"]
    assert any("duplicate" in err.lower() for err in dup_report["errors"])


def test_build_refuses_existing_target_tmp_branch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-b", "phase/dup-tmp")
    a1 = _commit_file(repo, "a.txt", "1\n", "feat: a1", 1795000100)
    a2 = _commit_file(repo, "b.txt", "2\n", "feat: a2", 1795000200)
    _git(repo, "branch", "existing-tmp", "main")

    plan = {
        "base": "main",
        "head": a2,
        "chapters": [
            {
                "title": "ch1",
                "sub_chapters": [
                    {"title": "s1", "message": "feat: s1\n\n{{SUB_COMMITS}}", "start": a1, "end": a2}
                ],
            }
        ],
    }
    with pytest.raises(dag_rewrap.DagRewrapError, match="already exists"):
        dag_rewrap.build_toc_branch(repo, plan, target_tmp="existing-tmp", sign_mode="none")


def test_preserve_merges_keeps_self_contained_nontrivial_merge_intact(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-b", "phase/evil-merge")
    a1 = _commit_file(repo, "a.txt", "1\n", "feat: a1", 1795000100)

    # Create a side branch from a1, then amend the merge commit with an extra file (tree != p2^{tree}).
    _git(repo, "checkout", "-b", "side/edit")
    _commit_file(repo, "b.txt", "2\n", "feat: b2", 1795000200)
    _git(repo, "checkout", "phase/evil-merge")
    _git(repo, "merge", "--no-ff", "--no-commit", "side/edit")
    (repo / "merge_only.txt").write_text("resolved\n", encoding="utf-8")
    _git(repo, "add", "merge_only.txt")
    _git(repo, "commit", "-m", "merge: side/edit with merge-only edit")
    evil_merge = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "-d", "side/edit")

    a3 = _commit_file(repo, "c.txt", "3\n", "feat: c3", 1795000300)

    # Without preserve_merges, inspect flags it as non-trivial & preservable.
    raw_info = dag_rewrap.inspect_range(repo, "main", "HEAD")
    assert len(raw_info["non_trivial_merges"]) == 1
    assert raw_info["non_trivial_merges"][0]["preservable"] is True

    # With preserve_merges, build succeeds losslessly and keeps merge_only.txt intact!
    plan = {
        "base": "main",
        "head": a3,
        "preserve_merges": [evil_merge],
        "chapters": [
            {
                "title": "feat: ch1",
                "message": "feat: ch1\n\n{{SUB_COMMITS}}",
                "sub_chapters": [
                    {"title": "s1", "message": "feat: s1\n\n{{SUB_COMMITS}}", "commits": [a1, evil_merge]},
                    {"title": "s2", "commits": [a3]},
                ],
            }
        ],
    }
    res = dag_rewrap.build_toc_branch(repo, plan, target_tmp="restructure-toc-tmp-preserved", sign_mode="none")
    assert res["status"] == "verified"
    assert _git(repo, "diff", "phase/evil-merge", "restructure-toc-tmp-preserved") == ""
    assert _git(repo, "show", "restructure-toc-tmp-preserved:merge_only.txt") == "resolved"


def test_inspect_flags_non_trivial_conflict_merge_and_validate_refuses_silent_flatten(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-b", "phase/conflict")
    c1 = _commit_file(repo, "shared.txt", "line1\n", "feat: add shared.txt", 1795000100)

    # Fork side branch from c1, advance phase/conflict concurrently, then merge with resolution!
    _git(repo, "checkout", "-b", "side/a", c1)
    _commit_file(repo, "shared.txt", "line1\nside-a\n", "feat: side a edit", 1795000200)
    _git(repo, "checkout", "phase/conflict")
    _commit_file(repo, "other.txt", "other\n", "feat: concurrent edit on phase", 1795000300)
    _git(repo, "merge", "--no-ff", "side/a", "-m", "merge: combine side/a and other.txt")
    _commit_file(repo, "after.txt", "after\n", "feat: after merge", 1795000400)

    info = dag_rewrap.inspect_range(repo, "main", "HEAD")
    assert len(info["non_trivial_merges"]) == 1
    nt = info["non_trivial_merges"][0]
    assert "tree_differs_from_p2" in nt["reasons"]
    assert "forked_before_p1" in nt["reasons"]

    # Validate must refuse to silently flatten it.
    plan = {
        "base": "main",
        "head": info["head"],
        "chapters": [
            {
                "title": "Chapter 1",
                "message": "feat: ch1",
                "sub_chapters": [
                    {"title": "sub 1", "message": "feat: s1", "commits": [c1]},
                ],
            }
        ],
    }
    report = dag_rewrap.validate_plan(repo, plan)
    assert not report["valid"]
    assert any("Non-trivial merge" in err for err in report["errors"])


def test_inspect_flags_external_sync_merge_from_main(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-b", "phase/sync")
    _commit_file(repo, "feat.txt", "v1\n", "feat: start feature", 1795000100)

    # Advance main and merge main into phase/sync mid-branch!
    _git(repo, "checkout", "main")
    _commit_file(repo, "main_hotfix.txt", "hotfix\n", "fix: hotfix on main", 1795000200)
    _git(repo, "checkout", "phase/sync")
    _git(repo, "merge", "--no-ff", "main", "-m", "chore: sync main into phase/sync")
    _commit_file(repo, "feat.txt", "v2\n", "feat: finish feature", 1795000300)

    base = _git(repo, "merge-base", "main", "phase/sync")
    # Use the original fork point (main~1) so the sync merge sits inside base..HEAD.
    orig_fork = _git(repo, "rev-parse", "main~1")
    assert base != orig_fork
    info = dag_rewrap.inspect_range(repo, orig_fork, "HEAD")
    assert len(info["non_trivial_merges"]) == 1
    assert "tree_differs_from_p2" in info["non_trivial_merges"][0]["reasons"]


def test_signing_failure_falls_back_cleanly_and_reports_unsigned_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-b", "phase/sign-test")
    a1 = _commit_file(repo, "a.txt", "1\n", "feat: a1", 1795000100)
    a2 = _commit_file(repo, "b.txt", "2\n", "feat: a2", 1795000200)
    a3 = _commit_file(repo, "c.txt", "3\n", "feat: a3", 1795000300)
    a4 = _commit_file(repo, "d.txt", "4\n", "feat: a4", 1795000400)

    real_run_git = dag_rewrap.run_git

    def fake_run_git(r: Path, *args: str, **kwargs):
        if "commit-tree" in args and "-S" in args:
            return subprocess.CompletedProcess(
                args=["git", *args],
                returncode=128,
                stdout=b"",
                stderr=b"error: 1Password: failed to fill whole buffer",
            )
        return real_run_git(r, *args, **kwargs)

    monkeypatch.setattr(dag_rewrap, "run_git", fake_run_git)

    plan = {
        "base": "main",
        "head": a4,
        "chapters": [
            {
                "title": "feat: ch1",
                "message": "feat: ch1\n\nIntent.\n\n[--- Changes ---]\n\n{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nOk.",
                "sub_chapters": [
                    {
                        "title": "feat: sub1",
                        "message": "feat: sub1\n\nIntent.\n\n[--- Changes ---]\n\n{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nOk.",
                        "start": a1,
                        "end": a2,
                    },
                    {
                        "title": "feat: sub2",
                        "message": "feat: sub2\n\nIntent.\n\n[--- Changes ---]\n\n{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nOk.",
                        "start": a3,
                        "end": a4,
                    },
                ],
            }
        ],
    }

    result = dag_rewrap.build_toc_branch(
        repo,
        plan,
        target_tmp="restructure-toc-tmp-sign",
        sign_mode="outer",
    )
    assert result["status"] == "verified"
    # Outer merges (2 sub-merges + 1 chapter merge = 3) fell back cleanly and were all logged!
    assert len(result["unsigned_fallback_commits"]) == 3
    assert all("1Password" in item["error"] for item in result["unsigned_fallback_commits"])
    assert _git(repo, "diff", "phase/sign-test", "restructure-toc-tmp-sign") == ""


def test_single_subchapter_chapter_does_not_double_wrap(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-b", "phase/single-sub")
    a1 = _commit_file(repo, "a.txt", "1\n", "feat: a1", 1795000100)
    a2 = _commit_file(repo, "b.txt", "2\n", "feat: a2", 1795000200)

    plan = {
        "base": "main",
        "head": a2,
        "chapters": [
            {
                "title": "feat: only chapter",
                "sub_chapters": [
                    {
                        "title": "feat: only sub-chapter",
                        "message": "feat: only sub-chapter\n\nIntent.\n\n[--- Changes ---]\n\n{{SUB_COMMITS}}\n\n[--- AI Review (test) ---]\n\nOk.",
                        "start": a1,
                        "end": a2,
                    }
                ],
            }
        ],
    }
    val = dag_rewrap.validate_plan(repo, plan)
    assert val["valid"]
    assert any("minimum bubble size is 2" in w for w in val["warnings"])

    result = dag_rewrap.build_toc_branch(repo, plan, target_tmp="restructure-toc-tmp-1sub", sign_mode="none")
    # 2 atomic + 1 sub-merge + 0 outer double-wrap = 3 commits!
    assert result["counts"]["rebuilt_total"] == 3
    assert result["counts"]["chapter_merges"] == 0
    assert result["counts"]["sub_chapter_merges"] == 1


def test_cli_inspect_validate_build_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _init_repo(tmp_path)
    fixture = _build_waymark_shaped_branch(repo)
    atomics: list[str] = fixture["atomics"]  # type: ignore[assignment]

    assert dag_rewrap.main(["--repo", str(repo), "inspect", "main", "HEAD"]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["atomic_count"] == 11

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "base": "main",
                "head": fixture["head"],
                "chapters": [
                    {
                        "title": "Chapter 1",
                        "message": "build: ch1\n\n{{SUB_COMMITS}}",
                        "sub_chapters": [
                            {"title": "s1", "message": "build: s1\n\n{{SUB_COMMITS}}", "start": atomics[0], "end": atomics[1]},
                            {"title": "s2", "message": "ci: s2\n\n{{SUB_COMMITS}}", "start": atomics[2], "end": atomics[4]},
                        ],
                    },
                    {
                        "title": "Chapter 2",
                        "message": "fix: ch2\n\n{{SUB_COMMITS}}",
                        "sub_chapters": [
                            {"title": "s3", "message": "docs: s3\n\n{{SUB_COMMITS}}", "start": atomics[5], "end": atomics[6]},
                            {"title": "s4", "message": "fix: s4\n\n{{SUB_COMMITS}}", "start": atomics[7], "end": atomics[9]},
                            {"title": "s5", "commits": [atomics[10]]},
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert dag_rewrap.main(["--repo", str(repo), "validate", str(plan_path)]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["valid"] is True

    assert (
        dag_rewrap.main(
            ["--repo", str(repo), "build", str(plan_path), "--target-tmp", "restructure-toc-tmp-cli", "--sign", "none"]
        )
        == 0
    )
    built = json.loads(capsys.readouterr().out)
    assert built["status"] == "verified"
    assert built["counts"]["rebuilt_total"] == 17
