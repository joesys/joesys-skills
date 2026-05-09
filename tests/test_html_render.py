"""Tests for html_render.py — bootstrap, transforms, rendering."""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import html_render


# ── find_repo_root ──────────────────────────────────────────────────


class TestFindRepoRoot:
    def test_returns_repo_root_for_file_in_repo(self, tmp_path):
        # Create a fake git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        sub = tmp_path / "docs" / "explain"
        sub.mkdir(parents=True)
        (sub / "report.md").write_text("# test")

        result = html_render.find_repo_root(sub / "report.md")
        # Resolve both sides because Windows paths can differ in case/symlink form
        assert result.resolve() == tmp_path.resolve()

    def test_raises_when_not_in_repo(self, tmp_path):
        # tmp_path is not a git repo
        target = tmp_path / "loose.md"
        target.write_text("# test")
        with pytest.raises(html_render.NotInRepoError):
            html_render.find_repo_root(target)


# ── bootstrap_assets ────────────────────────────────────────────────


class TestBootstrapAssets:
    def test_copies_vendor_dir_when_missing(self, tmp_path):
        # Set up a fake plugin vendor dir
        vendor = tmp_path / "plugin" / "scripts" / "vendor"
        vendor.mkdir(parents=True)
        (vendor / "report-base.css").write_text("/* css */")
        (vendor / "fonts").mkdir()
        (vendor / "fonts" / "test.woff2").write_bytes(b"fake")

        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        dest = html_render.bootstrap_assets(repo_root, vendor_dir=vendor)
        assert dest == repo_root / "docs" / ".assets" / "report-lib"
        assert (dest / "report-base.css").read_text() == "/* css */"
        assert (dest / "fonts" / "test.woff2").read_bytes() == b"fake"

    def test_skips_when_already_exists(self, tmp_path):
        vendor = tmp_path / "plugin" / "scripts" / "vendor"
        vendor.mkdir(parents=True)
        (vendor / "report-base.css").write_text("/* new */")

        repo_root = tmp_path / "repo"
        existing = repo_root / "docs" / ".assets" / "report-lib"
        existing.mkdir(parents=True)
        (existing / "report-base.css").write_text("/* existing */")

        dest = html_render.bootstrap_assets(repo_root, vendor_dir=vendor)
        # Existing content untouched
        assert (dest / "report-base.css").read_text() == "/* existing */"

    def test_raises_when_vendor_dir_missing(self, tmp_path):
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        with pytest.raises(html_render.VendorMissingError):
            html_render.bootstrap_assets(repo_root, vendor_dir=tmp_path / "nope")
