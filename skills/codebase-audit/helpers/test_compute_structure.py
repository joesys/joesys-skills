"""Tests for compute_structure.py — structural metrics analysis."""
import json
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent / "compute_structure.py")


def _run(args: list[str], cwd: str | None = None) -> dict:
    """Run compute_structure.py and parse JSON output."""
    result = subprocess.run(
        ["python", SCRIPT] + args,
        capture_output=True, text=True, cwd=cwd,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


def _write_file(tmp_path: Path, rel_path: str, content: str) -> Path:
    """Write a file relative to tmp_path, creating dirs as needed."""
    fpath = tmp_path / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(textwrap.dedent(content))
    return fpath


class TestComputeStructure:
    # ── 1. Output structure ──────────────────────────────────────────
    def test_output_structure(self, tmp_path):
        """Verify all required JSON fields present with correct types."""
        _write_file(tmp_path, "src/example.py", """\
            # A comment
            def foo():
                return 1

            def bar(x: int) -> int:
                return x + 1
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        # Required top-level fields
        assert data["language"] == "python"
        assert isinstance(data["total_files"], int)
        assert isinstance(data["total_loc"], int)
        assert isinstance(data["blank_lines"], int)
        assert isinstance(data["comment_lines"], int)
        assert isinstance(data["comment_density"], float)

        # Stat objects
        for key in ("file_lengths", "function_lengths", "nesting_depth"):
            assert key in data, f"Missing key: {key}"
            obj = data[key]
            assert "max" in obj
            assert "median" in obj
            assert "p90" in obj

        assert isinstance(data["type_annotation_coverage"], float)
        assert isinstance(data["files_over_500_lines"], list)
        assert isinstance(data["functions_over_50_lines"], list)

    # ── 2. LOC counting ─────────────────────────────────────────────
    def test_loc_counting(self, tmp_path):
        """File with comments, code, blanks → verify counts."""
        _write_file(tmp_path, "src/mixed.py", """\
            # This is a comment
            # Another comment

            def hello():
                # inline comment
                return "world"

            x = 1
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        # The dedented file has 8 lines total:
        # Line 1: "# This is a comment"       → comment
        # Line 2: "# Another comment"          → comment
        # Line 3: ""                            → blank
        # Line 4: "def hello():"               → code
        # Line 5: "    # inline comment"        → comment
        # Line 6: '    return "world"'          → code
        # Line 7: ""                            → blank
        # Line 8: "x = 1"                       → code
        assert data["total_files"] == 1
        assert data["total_loc"] == 6  # 8 lines - 2 blank = 6 non-blank
        assert data["blank_lines"] == 2
        assert data["comment_lines"] == 3

    # ── 3. Function length measurement ───────────────────────────────
    def test_function_length_measurement(self, tmp_path):
        """Two functions of different lengths → verify max is at least the longer one."""
        short_body = "    x = 1\n" * 5
        long_body = "    x = 1\n" * 20
        content = f"def short_func():\n{short_body}\ndef long_func():\n{long_body}"
        _write_file(tmp_path, "src/funcs.py", content)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        assert data["function_lengths"]["max"] >= 20

    # ── 4. Nesting depth ────────────────────────────────────────────
    def test_nesting_depth(self, tmp_path):
        """Deeply nested function (4+ levels) → verify max nesting depth."""
        _write_file(tmp_path, "src/nested.py", """\
            def deeply_nested():
                if True:
                    for x in range(10):
                        while x > 0:
                            if x == 5:
                                print("deep")
                            x -= 1
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        # 4 levels of nesting inside the function
        assert data["nesting_depth"]["max"] >= 4

    # ── 5. Type annotation coverage ──────────────────────────────────
    def test_type_annotation_coverage(self, tmp_path):
        """Mix of annotated and unannotated functions → verify coverage between 0 and 1."""
        _write_file(tmp_path, "src/types.py", """\
            def annotated(x: int) -> int:
                return x + 1

            def also_annotated(y: str) -> str:
                return y

            def not_annotated(z):
                return z

            def also_not(a, b):
                return a + b
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        cov = data["type_annotation_coverage"]
        assert 0.0 < cov < 1.0
        # 2 annotated out of 4 = 0.5
        assert cov == pytest.approx(0.5, abs=0.01)

    # ── 6. Files over threshold ──────────────────────────────────────
    def test_files_over_threshold(self, tmp_path):
        """One file >500 lines, one small → verify only the big one appears."""
        big_content = "\n".join([f"x_{i} = {i}" for i in range(510)])
        _write_file(tmp_path, "src/big.py", big_content)
        _write_file(tmp_path, "src/small.py", """\
            x = 1
            y = 2
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        assert len(data["files_over_500_lines"]) == 1
        assert "big.py" in data["files_over_500_lines"][0]

    # ── 7. Exclude patterns ──────────────────────────────────────────
    def test_exclude_patterns(self, tmp_path):
        """vendor/ directory excluded → verify total_files counts only non-excluded."""
        _write_file(tmp_path, "src/main.py", """\
            def main():
                return 1
        """)
        _write_file(tmp_path, "src/vendor/lib.py", """\
            def vendored():
                return 2
        """)
        _write_file(tmp_path, "src/utils.py", """\
            def helper():
                return 3
        """)
        data = _run([
            "--lang", "python",
            "--source", str(tmp_path / "src"),
            "--exclude", "vendor/*",
        ])

        assert data["total_files"] == 2  # main.py + utils.py, not vendor/lib.py
