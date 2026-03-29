"""Tests for compute_churn.py — git churn analysis."""
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent / "compute_churn.py")


def _run(args: list[str], cwd: str) -> dict:
    """Run compute_churn.py and parse JSON output."""
    result = subprocess.run(
        ["python", SCRIPT] + args,
        capture_output=True, text=True, cwd=cwd,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


def _make_git_repo(tmp: str) -> str:
    """Create a git repo with some commits for testing."""
    subprocess.run(["git", "init"], cwd=tmp, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp, capture_output=True, check=True,
    )

    # Create src/ directory with files
    src = Path(tmp) / "src"
    src.mkdir()

    # First commit — create two files
    (src / "main.py").write_text("def main():\n    pass\n")
    (src / "utils.py").write_text("def helper():\n    return 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp, capture_output=True, check=True,
    )

    # Second commit — modify main.py (add 5 lines, delete 1)
    (src / "main.py").write_text(
        "def main():\n    x = 1\n    y = 2\n    z = 3\n    w = 4\n    return x + y\n"
    )
    subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "update main"],
        cwd=tmp, capture_output=True, check=True,
    )

    # Third commit — modify utils.py
    (src / "utils.py").write_text("def helper():\n    return 42\n\ndef extra():\n    pass\n")
    subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "update utils"],
        cwd=tmp, capture_output=True, check=True,
    )

    return tmp


class TestComputeChurn:
    def test_basic_churn_output_structure(self, tmp_path):
        repo = _make_git_repo(str(tmp_path))
        data = _run(["--source", "src/"], cwd=repo)

        assert "files_changed" in data
        assert "lines_added" in data
        assert "lines_deleted" in data
        assert "net_change" in data
        assert "most_churned_files" in data
        assert isinstance(data["most_churned_files"], list)

    def test_churn_counts_are_positive(self, tmp_path):
        repo = _make_git_repo(str(tmp_path))
        data = _run(["--source", "src/"], cwd=repo)

        assert data["files_changed"] >= 1
        assert data["lines_added"] >= 1
        assert data["net_change"] == data["lines_added"] - data["lines_deleted"]

    def test_most_churned_files_have_required_fields(self, tmp_path):
        repo = _make_git_repo(str(tmp_path))
        data = _run(["--source", "src/"], cwd=repo)

        for entry in data["most_churned_files"]:
            assert "file" in entry
            assert "added" in entry
            assert "deleted" in entry
            assert "total_churn" in entry
            assert entry["total_churn"] == entry["added"] + entry["deleted"]

    def test_most_churned_sorted_descending(self, tmp_path):
        repo = _make_git_repo(str(tmp_path))
        data = _run(["--source", "src/"], cwd=repo)

        churns = [f["total_churn"] for f in data["most_churned_files"]]
        assert churns == sorted(churns, reverse=True)

    def test_default_source_is_current_dir(self, tmp_path):
        repo = _make_git_repo(str(tmp_path))
        data = _run([], cwd=repo)

        # Should still find files (defaults to ".")
        assert data["files_changed"] >= 1

    def test_exclude_filters_files(self, tmp_path):
        repo = _make_git_repo(str(tmp_path))

        # Create a vendor file and commit it
        vendor = Path(repo) / "vendor"
        vendor.mkdir()
        (vendor / "lib.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add vendor"],
            cwd=repo, capture_output=True, check=True,
        )

        data = _run(["--exclude", "vendor/"], cwd=repo)
        vendor_files = [f["file"] for f in data["most_churned_files"] if "vendor" in f["file"]]
        assert len(vendor_files) == 0
