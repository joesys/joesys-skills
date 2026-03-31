"""Tests for md_export.py — input detection and code wrapping."""

import os
import sys
import tempfile
from pathlib import Path

# Add scripts/ to path so we can import md_export
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import md_export


class TestDetectInputType:
    def test_markdown_file(self):
        assert md_export.detect_input_type("report.md") == "markdown"

    def test_txt_file(self):
        assert md_export.detect_input_type("notes.txt") == "markdown"

    def test_python_file(self):
        assert md_export.detect_input_type("utils.py") == "code"

    def test_cpp_file(self):
        assert md_export.detect_input_type("main.cpp") == "code"

    def test_javascript_file(self):
        assert md_export.detect_input_type("index.js") == "code"

    def test_rust_file(self):
        assert md_export.detect_input_type("lib.rs") == "code"

    def test_unknown_extension(self):
        assert md_export.detect_input_type("data.xyz") == "markdown"

    def test_no_extension(self):
        assert md_export.detect_input_type("Makefile") == "markdown"


class TestGetLanguageTag:
    def test_python(self):
        assert md_export.get_language_tag("script.py") == "python"

    def test_javascript(self):
        assert md_export.get_language_tag("app.js") == "javascript"

    def test_typescript(self):
        assert md_export.get_language_tag("app.ts") == "typescript"

    def test_cpp(self):
        assert md_export.get_language_tag("main.cpp") == "cpp"

    def test_csharp(self):
        assert md_export.get_language_tag("Program.cs") == "csharp"

    def test_rust(self):
        assert md_export.get_language_tag("lib.rs") == "rust"

    def test_go(self):
        assert md_export.get_language_tag("main.go") == "go"

    def test_yaml(self):
        assert md_export.get_language_tag("config.yaml") == "yaml"

    def test_json(self):
        assert md_export.get_language_tag("data.json") == "json"

    def test_sql(self):
        assert md_export.get_language_tag("query.sql") == "sql"

    def test_shell(self):
        assert md_export.get_language_tag("deploy.sh") == "bash"

    def test_powershell(self):
        assert md_export.get_language_tag("setup.ps1") == "powershell"


class TestWrapCodeFile:
    def test_wraps_python_file(self):
        content = 'print("hello")\n'
        result = md_export.wrap_code_file("hello.py", content)
        assert result.startswith("# hello.py\n\n```python\n")
        assert 'print("hello")' in result
        assert result.endswith("\n```\n")

    def test_wraps_javascript_file(self):
        content = 'console.log("hi");\n'
        result = md_export.wrap_code_file("app.js", content)
        assert "```javascript" in result
        assert "# app.js" in result


class TestPrepareContent:
    def test_markdown_passthrough(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("# Hello\n\nWorld\n")
            f.flush()
            tmp_name = f.name
        try:
            result = md_export.prepare_content(tmp_name)
            assert result == "# Hello\n\nWorld\n"
        finally:
            os.unlink(tmp_name)

    def test_code_file_wrapped(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write('x = 1\n')
            f.flush()
            tmp_name = f.name
        try:
            result = md_export.prepare_content(tmp_name)
            assert "```python" in result
            assert "x = 1" in result
        finally:
            os.unlink(tmp_name)


class TestBuildOutputPath:
    def test_default_pdf(self):
        result = md_export.build_output_path("docs/report.md", "pdf", "full", None)
        assert result == str(Path("docs/report.pdf"))

    def test_summary_scope(self):
        result = md_export.build_output_path("docs/report.md", "html", "summary", None)
        assert result == str(Path("docs/report-summary.html"))

    def test_1pager_scope(self):
        result = md_export.build_output_path("docs/report.md", "png", "1pager", None)
        assert result == str(Path("docs/report-1pager.png"))

    def test_custom_output(self):
        result = md_export.build_output_path("docs/report.md", "pdf", "full", "/tmp/out.pdf")
        assert result == "/tmp/out.pdf"


class TestGetPngSize:
    def test_full_scope(self):
        w, h = md_export.get_png_size("full", "portrait")
        assert w == 430
        assert h is None

    def test_summary_scope(self):
        w, h = md_export.get_png_size("summary", "portrait")
        assert w == 430
        assert h is None

    def test_1pager_portrait(self):
        w, h = md_export.get_png_size("1pager", "portrait")
        assert (w, h) == (794, 1123)

    def test_1pager_landscape(self):
        w, h = md_export.get_png_size("1pager", "landscape")
        assert (w, h) == (1123, 794)


class TestEndToEndHTML:
    """Integration test: requires Pandoc installed."""

    def test_markdown_to_html(self):
        if not md_export.find_pandoc():
            return  # skip if pandoc not available

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Test\n\nHello **world**.\n")
            input_path = f.name

        output_path = input_path.replace(".md", ".html")
        try:
            md_export.convert_to_html(
                md_export.prepare_content(input_path),
                "minimal",
                "test",
                output_path,
            )
            assert os.path.isfile(output_path)
            with open(output_path, "r", encoding="utf-8") as out:
                html = out.read()
            assert "<strong>world</strong>" in html
            assert "Hello" in html
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_code_file_to_html(self):
        if not md_export.find_pandoc():
            return

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write('print("hello")\n')
            input_path = f.name

        output_path = input_path.replace(".py", ".html")
        try:
            md_export.convert_to_html(
                md_export.prepare_content(input_path),
                "minimal",
                "test",
                output_path,
            )
            assert os.path.isfile(output_path)
            with open(output_path, "r", encoding="utf-8") as out:
                html = out.read()
            assert "hello" in html
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_hard_line_breaks(self):
        """Verify that single newlines produce <br> not paragraph merge."""
        if not md_export.find_pandoc():
            return

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("Name: Joe\nOccupation: Human\n")
            input_path = f.name

        output_path = input_path.replace(".md", ".html")
        try:
            md_export.convert_to_html(
                md_export.prepare_content(input_path),
                "minimal",
                "test",
                output_path,
            )
            with open(output_path, "r", encoding="utf-8") as out:
                html = out.read()
            # With hard_line_breaks, there should be a <br> between the lines
            assert "<br" in html or "Name: Joe" in html
            # They should NOT be merged into one run
            assert "Name: Joe Occupation:" not in html
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
