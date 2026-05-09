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


# ── transform_mermaid_blocks ────────────────────────────────────────


class TestTransformMermaidBlocks:
    def test_wraps_mermaid_block_in_pre_tag(self):
        markdown = (
            "Before.\n\n"
            "```mermaid\n"
            "graph TD\n"
            "  A --> B\n"
            "```\n\n"
            "After.\n"
        )
        result = html_render.transform_mermaid_blocks(markdown)
        # Mermaid block must be replaced with a fenced HTML block (Pandoc raw HTML).
        assert "```mermaid" not in result
        assert '<pre class="mermaid">' in result
        assert "graph TD" in result
        assert "A --> B" in result
        # Surrounding prose preserved.
        assert "Before." in result
        assert "After." in result

    def test_preserves_indentation_in_diagram(self):
        markdown = "```mermaid\ngraph TD\n    A --> B\n```\n"
        result = html_render.transform_mermaid_blocks(markdown)
        assert "    A --> B" in result

    def test_handles_multiple_mermaid_blocks(self):
        markdown = (
            "```mermaid\ngraph TD\nA --> B\n```\n\n"
            "Middle\n\n"
            "```mermaid\nsequenceDiagram\nAlice->>Bob: Hi\n```\n"
        )
        result = html_render.transform_mermaid_blocks(markdown)
        assert result.count('<pre class="mermaid">') == 2
        assert "A --> B" in result
        assert "Alice->>Bob: Hi" in result

    def test_leaves_non_mermaid_code_blocks_alone(self):
        markdown = "```python\nprint('hi')\n```\n"
        result = html_render.transform_mermaid_blocks(markdown)
        assert "```python" in result
        assert "<pre class=\"mermaid\">" not in result


# ── parse_frontmatter ───────────────────────────────────────────────


class TestParseFrontmatter:
    def test_extracts_yaml_block_at_start(self):
        markdown = (
            "---\n"
            "title: Hello\n"
            "scope: src/auth/\n"
            "---\n\n"
            "# Body\n"
        )
        meta, body = html_render.parse_frontmatter(markdown)
        assert meta == {"title": "Hello", "scope": "src/auth/"}
        assert body.startswith("# Body")

    def test_returns_empty_dict_when_no_frontmatter(self):
        markdown = "# Just body\n\nText.\n"
        meta, body = html_render.parse_frontmatter(markdown)
        assert meta == {}
        assert body == markdown

    def test_handles_quoted_values(self):
        markdown = (
            "---\n"
            'title: "Quoted: title"\n'
            "---\n\n"
            "Body.\n"
        )
        meta, body = html_render.parse_frontmatter(markdown)
        assert meta["title"] == "Quoted: title"

    def test_strips_only_first_yaml_block(self):
        markdown = (
            "---\n"
            "title: A\n"
            "---\n\n"
            "Body with another --- divider.\n"
            "\n---\n\n"
            "After.\n"
        )
        meta, body = html_render.parse_frontmatter(markdown)
        assert meta == {"title": "A"}
        assert "After." in body


# ── compute_assets_relpath ──────────────────────────────────────────


class TestComputeAssetsRelpath:
    def test_one_level_deep(self, tmp_path):
        assets = tmp_path / "docs" / ".assets" / "report-lib"
        output = tmp_path / "docs" / "explain" / "report.html"
        rel = html_render.compute_assets_relpath(assets, output)
        # POSIX paths only — HTML uses forward slashes regardless of OS.
        assert rel == "../.assets/report-lib"

    def test_two_levels_deep(self, tmp_path):
        assets = tmp_path / "docs" / ".assets" / "report-lib"
        output = tmp_path / "docs" / "devlog" / "20260509-x" / "post.html"
        rel = html_render.compute_assets_relpath(assets, output)
        assert rel == "../../.assets/report-lib"

    def test_handles_windows_paths_correctly(self, tmp_path):
        # On Windows, paths use backslashes natively. Output must still be
        # forward-slash for HTML.
        assets = tmp_path / "docs" / ".assets" / "report-lib"
        output = tmp_path / "docs" / "code-review" / "2026-05-09T14.html"
        rel = html_render.compute_assets_relpath(assets, output)
        assert "\\" not in rel
        assert rel.startswith("../")


# ── render_html ─────────────────────────────────────────────────────


class TestRenderHtml:
    def test_renders_basic_markdown_to_html(self, tmp_path):
        # Create a fake repo with assets dir
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        repo = tmp_path
        assets = repo / "docs" / ".assets" / "report-lib"
        assets.mkdir(parents=True)
        # Write a stub base.css so the report has *something* to link to
        (assets / "report-base.css").write_text("/* test */")

        input_md = repo / "docs" / "explain" / "test.md"
        input_md.parent.mkdir(parents=True)
        input_md.write_text("# Hello\n\nWorld.\n")

        output = repo / "docs" / "explain" / "test.html"
        html_render.render_html(
            input_md=input_md,
            output_html=output,
            assets_dir=assets,
            template_path=html_render.TEMPLATE_PATH,
        )

        assert output.exists()
        html = output.read_text(encoding="utf-8")
        assert "<h1" in html and "Hello" in html
        assert "World." in html
        # Asset references use the correct relative path
        assert 'href="../.assets/report-lib/report-base.css"' in html

    def test_renders_mermaid_block_into_pre(self, tmp_path):
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        repo = tmp_path
        assets = repo / "docs" / ".assets" / "report-lib"
        assets.mkdir(parents=True)
        (assets / "report-base.css").write_text("/* test */")

        input_md = repo / "docs" / "explain" / "test.md"
        input_md.parent.mkdir(parents=True)
        input_md.write_text(
            "# Test\n\n"
            "```mermaid\n"
            "graph TD\nA --> B\n"
            "```\n"
        )

        output = repo / "docs" / "explain" / "test.html"
        html_render.render_html(
            input_md=input_md,
            output_html=output,
            assets_dir=assets,
            template_path=html_render.TEMPLATE_PATH,
        )

        html = output.read_text(encoding="utf-8")
        assert '<pre class="mermaid">' in html
        assert "A --&gt; B" in html or "A --> B" in html

    def test_uses_frontmatter_title(self, tmp_path):
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        repo = tmp_path
        assets = repo / "docs" / ".assets" / "report-lib"
        assets.mkdir(parents=True)
        (assets / "report-base.css").write_text("/* test */")

        input_md = repo / "docs" / "explain" / "test.md"
        input_md.parent.mkdir(parents=True)
        input_md.write_text(
            "---\n"
            "title: Custom Page Title\n"
            "---\n\n"
            "# Body\n"
        )

        output = repo / "docs" / "explain" / "test.html"
        html_render.render_html(
            input_md=input_md,
            output_html=output,
            assets_dir=assets,
            template_path=html_render.TEMPLATE_PATH,
        )

        html = output.read_text(encoding="utf-8")
        assert "<title>Custom Page Title</title>" in html
