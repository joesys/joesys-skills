# test_collect_git.py
from __future__ import annotations
import json, subprocess
from pathlib import Path
import pytest

SCRIPT = str(Path(__file__).parent / "collect_git.py")


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    d = str(tmp_path)
    _git(["init", "-b", "main"], d)
    _git(["config", "user.email", "a@x.com"], d)
    _git(["config", "user.name", "Alice"], d)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x=1\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "feat: init"], d)
    return d


def _run(repo, extra=None):
    r = subprocess.run(["python", SCRIPT, "--repo", repo, "--now", "9999999999"] + (extra or []),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_output_has_required_top_level_keys(repo):
    data = _run(repo)
    for k in ("schema", "repo", "kpis", "lenses", "overall", "flags", "repo_state"):
        assert k in data
    for lens in ("delivery", "health", "team"):
        assert data["lenses"][lens]["light"] in ("green", "yellow", "red", "na")
    assert data["overall"]["light"] in ("green", "yellow", "red", "na")


def test_solo_flag_and_team_not_forced_red(repo):
    data = _run(repo)
    assert data["flags"]["solo"] is True
    # solo override: a 1-author repo must NOT be red on bus factor
    assert data["lenses"]["team"]["light"] != "red"


def test_writes_file_with_out(repo, tmp_path):
    out = str(tmp_path / "dash.json")
    subprocess.run(["python", SCRIPT, "--repo", repo, "--now", "9999999999", "--out", out],
                   capture_output=True, text=True, check=True)
    assert Path(out).exists()
    assert json.loads(Path(out).read_text())["schema"] == 1


def test_not_a_repo_errors(tmp_path):
    r = subprocess.run(["python", SCRIPT, "--repo", str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode != 0
    assert "not a git repo" in r.stderr.lower()
