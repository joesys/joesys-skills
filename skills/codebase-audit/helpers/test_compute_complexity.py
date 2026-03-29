"""Tests for compute_complexity.py — cyclomatic complexity analysis."""
import json
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent / "compute_complexity.py")


def _run(args: list[str], cwd: str | None = None) -> dict:
    """Run compute_complexity.py and parse JSON output."""
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


class TestComputeComplexity:
    # ── 1. Simple function CC=1 ───────────────────────────────────
    def test_simple_function_cc_1(self, tmp_path):
        _write_file(tmp_path, "src/simple.py", """\
            def hello():
                return "world"
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        assert data["total_functions"] == 1
        assert data["functions"][0]["complexity"] == 1
        assert data["functions"][0]["name"] == "hello"

    # ── 2. Function with branches ─────────────────────────────────
    def test_function_with_branches(self, tmp_path):
        _write_file(tmp_path, "src/branchy.py", """\
            def process(x):
                if x > 0:
                    if x > 10:
                        return "big"
                    return "small"
                elif x == 0:
                    return "zero"
                return "negative"
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        # CC = 1 + if + if + elif = 4
        assert data["functions"][0]["complexity"] == 4

    # ── 3. Loops and logic operators ──────────────────────────────
    def test_function_with_loops_and_logic(self, tmp_path):
        _write_file(tmp_path, "src/loopy.py", """\
            def search(items, target):
                for item in items:
                    if item == target and item > 0:
                        return True
                return False
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        # CC = 1 + for + if + and = 4
        assert data["functions"][0]["complexity"] == 4

    # ── 4. Multiple functions ─────────────────────────────────────
    def test_multiple_functions(self, tmp_path):
        _write_file(tmp_path, "src/multi.py", """\
            def simple():
                return 1

            def branchy(x):
                if x:
                    return True
                return False
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        assert data["total_functions"] == 2
        # simple=1, branchy=2 → avg = 1.5
        assert data["average_complexity"] == 1.5

    # ── 5. Output structure ───────────────────────────────────────
    def test_output_structure(self, tmp_path):
        _write_file(tmp_path, "src/example.py", """\
            def foo():
                pass
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        assert "language" in data
        assert "total_functions" in data
        assert "average_complexity" in data
        assert "max_complexity" in data
        assert "distribution" in data
        assert "functions" in data
        assert data["language"] == "python"

    # ── 6. Distribution buckets ───────────────────────────────────
    def test_distribution_buckets(self, tmp_path):
        _write_file(tmp_path, "src/dist.py", """\
            def foo():
                pass
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        dist = data["distribution"]
        assert "1-5" in dist
        assert "6-10" in dist
        assert "11-15" in dist
        assert "16-20" in dist
        assert "21+" in dist

    # ── 7. Async functions detected ───────────────────────────────
    def test_async_functions_detected(self, tmp_path):
        _write_file(tmp_path, "src/async_mod.py", """\
            async def fetch_data():
                return await get_stuff()

            async def process_data(data):
                if data:
                    return data
                return None
        """)
        data = _run(["--lang", "python", "--source", str(tmp_path / "src")])

        assert data["total_functions"] == 2
        names = [f["name"] for f in data["functions"]]
        assert "fetch_data" in names
        assert "process_data" in names

    # ── 8. Exclude patterns ───────────────────────────────────────
    def test_exclude_patterns(self, tmp_path):
        _write_file(tmp_path, "src/main.py", """\
            def main():
                return 1
        """)
        _write_file(tmp_path, "src/vendor/lib.py", """\
            def vendored():
                return 2
        """)
        _write_file(tmp_path, "src/test_foo.py", """\
            def test_something():
                pass
        """)
        data = _run([
            "--lang", "python",
            "--source", str(tmp_path / "src"),
            "--exclude", "vendor/*,test_*",
        ])

        names = [f["name"] for f in data["functions"]]
        assert "main" in names
        assert "vendored" not in names
        assert "test_something" not in names
        assert data["total_functions"] == 1

    # ── 9. Basic TypeScript function ──────────────────────────────
    def test_basic_ts_function(self, tmp_path):
        _write_file(tmp_path, "src/greet.ts", """\
            function greet(name: string): string {
                if (name === "") {
                    return "Hello, World!";
                }
                return `Hello, ${name}!`;
            }
        """)
        data = _run(["--lang", "typescript", "--source", str(tmp_path / "src")])

        assert data["total_functions"] == 1
        assert data["functions"][0]["name"] == "greet"
        assert data["functions"][0]["complexity"] == 2  # 1 + if

    # ── 10. Switch/case ───────────────────────────────────────────
    def test_switch_case(self, tmp_path):
        _write_file(tmp_path, "src/switcher.ts", """\
            function handleAction(action: string): void {
                switch (action) {
                    case "start":
                        console.log("starting");
                        break;
                    case "stop":
                        console.log("stopping");
                        break;
                    default:
                        console.log("unknown");
                }
            }
        """)
        data = _run(["--lang", "typescript", "--source", str(tmp_path / "src")])

        assert data["total_functions"] == 1
        # CC = 1 + case + case = 3
        assert data["functions"][0]["complexity"] == 3
