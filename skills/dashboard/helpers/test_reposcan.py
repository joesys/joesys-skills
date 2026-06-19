# test_reposcan.py
from __future__ import annotations
import subprocess
from pathlib import Path
import pytest
import reposcan


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    d = str(tmp_path)
    _git(["init", "-b", "main"], d)
    _git(["config", "user.email", "a@x.com"], d)
    _git(["config", "user.name", "A"], d)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("# TODO: refactor\nx = 1  # FIXME\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_x():\n    assert True\n")
    (tmp_path / ".gitignore").write_text(".env\n")
    (tmp_path / "poetry.lock").write_text("")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("on: push\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "init"], d)
    return d


def test_detect_modules_lists_top_level_source_dirs(repo):
    mods = reposcan.detect_modules(repo)
    assert "src" in mods
    assert ".github" not in mods  # dot-dirs excluded


def test_debt_markers_counts(repo):
    d = reposcan.debt_markers(repo)
    assert d["todo"] == 1
    assert d["fixme"] == 1
    assert d["total"] == 2


def test_hygiene_checklist(repo):
    h = reposcan.hygiene(repo)
    assert h["ci"] is True
    assert h["lockfile"] is True
    assert h["env_gitignored"] is True
    assert h["tests"] is True


def test_project_size(repo):
    s = reposcan.project_size(repo)
    assert s["files"] >= 3
    assert s["languages"].get("py", 0) >= 2
