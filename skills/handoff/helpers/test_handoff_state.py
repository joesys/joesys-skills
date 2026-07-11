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
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "initial")
    if remote:
        git(tmp_path, "remote", "add", "origin", remote)
    return tmp_path


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
