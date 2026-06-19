# test_gitlog.py
from __future__ import annotations
import subprocess
from pathlib import Path
import pytest
import gitlog


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    d = str(tmp_path)
    _git(["init", "-b", "main"], d)
    _git(["config", "user.email", "a@x.com"], d)
    _git(["config", "user.name", "Alice"], d)
    (tmp_path / "f.txt").write_text("one\n")
    _git(["add", "."], d)
    _git(["commit", "-m", "feat: first"], d)
    (tmp_path / "f.txt").write_text("two\n")
    _git(["add", "."], d)
    _git(["commit", "-m", "fix: second"], d)
    _git(["tag", "v1.0.0"], d)
    return d


def test_is_git_repo(repo, tmp_path):
    assert gitlog.is_git_repo(repo) is True
    assert gitlog.is_git_repo(str(tmp_path.parent / "nope")) is False


def test_get_commits_parses_fields(repo):
    commits = gitlog.get_commits(repo)
    assert len(commits) == 2
    subjects = [c["subject"] for c in commits]
    assert "feat: first" in subjects and "fix: second" in subjects
    c = commits[0]
    assert set(c) >= {"hash", "author", "email", "ts", "parents", "is_merge", "subject"}
    assert c["author"] == "Alice"
    assert isinstance(c["ts"], int)
    assert c["is_merge"] is False


def test_get_tags(repo):
    tags = gitlog.get_tags(repo)
    assert [t["name"] for t in tags] == ["v1.0.0"]
    assert isinstance(tags[0]["ts"], int)


def test_count_commits(repo):
    assert gitlog.count_commits(repo) == 2


def test_default_branch_and_head(repo):
    assert gitlog.default_branch(repo) in ("main", "master")
    head = gitlog.repo_head(repo)
    assert head["branch"] == "main"
    assert len(head["commit"]) >= 7
