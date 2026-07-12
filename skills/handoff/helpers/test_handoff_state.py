"""Tests for deterministic handoff repository state."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import handoff_state


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def make_repo(tmp_path: Path, *, remote: str | None = None) -> Path:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test User")
    git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "initial")
    if remote:
        git(tmp_path, "remote", "add", "origin", remote)
    return tmp_path


def test_make_repo_disables_inherited_commit_signing(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    result = git(repo, "config", "--get", "commit.gpgsign")

    assert result.stdout.strip() == "false"


def test_capture_clean_git_snapshot(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, remote="git@github.com:joesys/example.git")

    snapshot = handoff_state.capture_snapshot(repo, ["app.py"])

    assert snapshot["snapshot_version"] == 1
    assert snapshot["kind"] == "git"
    assert snapshot["project_identity"] == "github.com/joesys/example"
    assert snapshot["root_name"] == tmp_path.name
    assert snapshot["branch"] in {"main", "master"}
    assert len(snapshot["head"]) == 40
    assert snapshot["status"] == []
    assert snapshot["dirty_patch_sha256"] == handoff_state.EMPTY_SHA256
    assert snapshot["relevant_files"]["app.py"]["exists"] is True


def test_capture_dirty_and_untracked_files(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "notes.txt").write_text("next step\n", encoding="utf-8")

    snapshot = handoff_state.capture_snapshot(repo, ["app.py", "notes.txt"])

    assert {item["path"] for item in snapshot["status"]} == {
        "app.py",
        "notes.txt",
    }
    assert snapshot["dirty_patch_sha256"] != handoff_state.EMPTY_SHA256
    assert snapshot["relevant_files"]["app.py"]["sha256"]
    assert snapshot["relevant_files"]["notes.txt"]["tracked"] is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("git@github.com:Owner/Repo.git", "github.com/Owner/Repo"),
        ("https://github.com/Owner/Repo.git", "github.com/Owner/Repo"),
        ("ssh://git@github.com/Owner/Repo.git", "github.com/Owner/Repo"),
    ],
)
def test_normalize_remote_url(raw: str, expected: str) -> None:
    assert handoff_state.normalize_remote_url(raw) == expected


def test_sensitive_path_detection() -> None:
    assert handoff_state.is_sensitive_path(".env") is True
    assert handoff_state.is_sensitive_path(".env.production") is True
    assert handoff_state.is_sensitive_path("config/production.pem") is True
    assert handoff_state.is_sensitive_path("src/config.py") is False


def test_snapshot_cli_outputs_json(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path)

    exit_code = handoff_state.main(
        ["snapshot", "--repo", str(repo), "--relevant", "app.py"]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["kind"] == "git"


def write_handoff(path: Path, snapshot: dict[str, object]) -> None:
    compact = json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
    path.write_text(
        "---\n"
        "schema_version: 1\n"
        f"repository_snapshot: {compact}\n"
        "---\n\n"
        "# Checkpoint\n",
        encoding="utf-8",
    )


def test_extract_snapshot_from_handoff(tmp_path: Path) -> None:
    snapshot = {"snapshot_version": 1, "kind": "non_git"}
    artifact = tmp_path / "handoff.md"
    write_handoff(artifact, snapshot)

    assert handoff_state.extract_snapshot(artifact) == snapshot


def test_extract_snapshot_rejects_unterminated_frontmatter(tmp_path: Path) -> None:
    artifact = tmp_path / "broken.md"
    artifact.write_text(
        "---\nschema_version: 1\nrepository_snapshot: {}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not terminated"):
        handoff_state.extract_snapshot(artifact)


def test_extract_snapshot_rejects_newer_snapshot_version(tmp_path: Path) -> None:
    artifact = tmp_path / "future.md"
    write_handoff(artifact, {"snapshot_version": 2, "kind": "git"})

    with pytest.raises(ValueError, match="unsupported repository snapshot version"):
        handoff_state.extract_snapshot(artifact)


def test_compare_exact_state(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "exact"
    assert comparison["reasons"] == []


def test_compare_advanced_state_for_unrelated_commit(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    (repo / "unrelated.txt").write_text("new\n", encoding="utf-8")
    git(repo, "add", "unrelated.txt")
    git(repo, "commit", "-m", "advance unrelated file")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "advanced"


def test_compare_drifted_when_relevant_file_changes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    (repo / "app.py").write_text("VALUE = 99\n", encoding="utf-8")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert any("app.py" in reason for reason in comparison["reasons"])


def test_compare_drifted_when_relevant_file_is_renamed(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    git(repo, "mv", "app.py", "renamed.py")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert any("disappeared: app.py" in reason for reason in comparison["reasons"])
    rename = next(
        item for item in comparison["current"]["status"] if "R" in item["status"]
    )
    assert rename["path"] == "renamed.py"
    assert rename["original_path"] == "app.py"


def test_compare_drifted_after_branch_divergence(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    git(repo, "checkout", "-b", "other-work")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert any("branch" in reason.lower() for reason in comparison["reasons"])


def test_compare_accepts_different_clone_with_same_remote(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    source = make_repo(source, remote="git@github.com:joesys/example.git")
    recorded = handoff_state.capture_snapshot(source, ["app.py"])

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", str(source), str(clone)],
        capture_output=True,
        text=True,
        check=True,
    )
    git(
        clone,
        "remote",
        "set-url",
        "origin",
        "https://github.com/joesys/example.git",
    )

    comparison = handoff_state.compare_snapshot(clone, recorded)

    assert comparison["classification"] == "exact"


def test_compare_rejects_different_project_identity(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, remote="git@github.com:joesys/example.git")
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    git(repo, "remote", "set-url", "origin", "git@github.com:joesys/other.git")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert "project identity differs" in comparison["reasons"]


def test_compare_non_git_is_unverifiable(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("one\n", encoding="utf-8")
    recorded = handoff_state.capture_snapshot(tmp_path, ["notes.md"])

    comparison = handoff_state.compare_snapshot(tmp_path, recorded)

    assert comparison["classification"] == "unverifiable"


def test_compare_cli_reads_handoff(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path)
    artifact = tmp_path / "checkpoint.md"
    write_handoff(artifact, handoff_state.capture_snapshot(repo, ["app.py"]))

    exit_code = handoff_state.main(
        ["compare", "--repo", str(repo), "--handoff", str(artifact)]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["classification"] == "exact"


def test_compare_cli_reports_malformed_handoff(tmp_path: Path, capsys) -> None:
    artifact = tmp_path / "broken.md"
    artifact.write_text("not frontmatter\n", encoding="utf-8")

    exit_code = handoff_state.main(
        ["compare", "--repo", str(tmp_path), "--handoff", str(artifact)]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "must start with YAML frontmatter" in json.loads(captured.err)["error"]


def test_compare_drifted_when_dirty_patch_changes_during_advance(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    (repo / "unrelated.txt").write_text("new\n", encoding="utf-8")
    git(repo, "add", "unrelated.txt")
    git(repo, "commit", "-m", "advance")
    (repo / "app.py").write_text("VALUE = 3\n", encoding="utf-8")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
