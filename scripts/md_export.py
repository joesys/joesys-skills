#!/usr/bin/env python3
"""md_export.py — Convert markdown/text/code files to polished PDF, HTML, PNG.

Usage:
    python md_export.py <input> [options]

Options:
    --format    pdf|html|png|all   Output format (default: pdf)
    --theme     minimal|modern|dark  CSS theme (default: minimal)
    --orientation  portrait|landscape  Page orientation (default: portrait)
    --output    <path>             Custom output path (single format only)
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

THEMES_DIR = Path(__file__).parent / "themes"

HIGHLIGHT_STYLES = {
    "minimal": "pygments",
    "modern": "tango",
    "dark": "breezedark",
}

CODE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".cpp": "cpp",
    ".c": "c",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".cs": "csharp",
    ".sh": "bash",
    ".ps1": "powershell",
    ".rb": "ruby",
    ".lua": "lua",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
}

# ── Input Detection ────────────────────────────────────────────────────────────


def detect_input_type(filepath: str) -> str:
    """Return 'code' if the file is a known code extension, else 'markdown'."""
    ext = Path(filepath).suffix.lower()
    if ext in CODE_EXTENSIONS:
        return "code"
    return "markdown"


def get_language_tag(filepath: str) -> str:
    """Return the Pandoc-compatible language tag for syntax highlighting."""
    ext = Path(filepath).suffix.lower()
    return CODE_EXTENSIONS.get(ext, "text")


def wrap_code_file(filename: str, content: str) -> str:
    """Wrap source code content in a markdown fenced code block with heading."""
    lang = get_language_tag(filename)
    return f"# {filename}\n\n```{lang}\n{content}\n```\n"


def prepare_content(filepath: str) -> str:
    """Read the input file and prepare markdown content for Pandoc."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if detect_input_type(filepath) == "code":
        filename = Path(filepath).name
        return wrap_code_file(filename, content)

    return content


# ── Dependency Detection ───────────────────────────────────────────────────────


def find_pandoc() -> str | None:
    """Return the path to pandoc, or None if not found."""
    return shutil.which("pandoc")


def find_browser() -> str | None:
    """Find a Chromium-based browser. Returns path or None."""
    system = platform.system()

    if system == "Windows":
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path

    elif system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path

    else:  # Linux
        for name in ["chromium-browser", "google-chrome", "chromium", "chrome"]:
            path = shutil.which(name)
            if path:
                return path

    return None


# ── Pandoc Conversion ──────────────────────────────────────────────────────────


def convert_to_html(
    markdown_content: str, theme: str, title: str, output_path: str
) -> None:
    """Convert markdown content to a self-contained HTML file via Pandoc."""
    pandoc = find_pandoc()
    if not pandoc:
        print(
            "Error: Pandoc is required but not found.\n"
            "\n"
            "Install Pandoc:\n"
            "  Windows:  choco install pandoc   OR   winget install JohnMacFarlane.Pandoc\n"
            "  macOS:    brew install pandoc\n"
            "  Linux:    sudo apt install pandoc   OR   sudo pacman -S pandoc\n"
            "  All:      https://pandoc.org/installing.html",
            file=sys.stderr,
        )
        sys.exit(1)

    css_path = THEMES_DIR / f"{theme}.css"
    if not css_path.exists():
        print(f"Error: Theme '{theme}' not found at {css_path}", file=sys.stderr)
        sys.exit(2)

    highlight_style = HIGHLIGHT_STYLES.get(theme, "pygments")

    # Write content to temp file for Pandoc input
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(markdown_content)
        tmp_path = tmp.name

    try:
        cmd = [
            pandoc,
            "-f", "markdown+hard_line_breaks",
            "-t", "html5",
            "--standalone",
            "--embed-resources",
            f"--highlight-style={highlight_style}",
            f"--css={css_path}",
            f"--metadata=title:{title}",
            "-o", output_path,
            tmp_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Error: Pandoc failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(3)
    finally:
        os.unlink(tmp_path)


# ── Browser Rendering ──────────────────────────────────────────────────────────


def render_pdf(html_path: str, output_path: str, orientation: str) -> None:
    """Render HTML to PDF using a headless browser."""
    browser = find_browser()
    if not browser:
        _print_browser_error()
        sys.exit(1)

    file_url = Path(html_path).as_uri()

    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={output_path}",
        file_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0 and not os.path.isfile(output_path):
        print(f"Error: Browser PDF rendering failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(3)


def render_png(
    html_path: str, output_path: str, width: int, height: int | None
) -> None:
    """Render HTML to PNG using a headless browser."""
    browser = find_browser()
    if not browser:
        _print_browser_error()
        sys.exit(1)

    file_url = Path(html_path).as_uri()

    window_size = f"{width},{height}" if height else f"{width},900"
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--screenshot={output_path}",
        f"--window-size={window_size}",
        file_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0 and not os.path.isfile(output_path):
        print(f"Error: Browser PNG rendering failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(3)


def _print_browser_error() -> None:
    print(
        "Error: A Chromium-based browser is required but not found.\n"
        "\n"
        "Supported browsers (checked in order):\n"
        "  Windows:  Microsoft Edge (built-in), Google Chrome\n"
        "  macOS:    Google Chrome, Chromium, Microsoft Edge\n"
        "  Linux:    chromium-browser, google-chrome, chromium\n"
        "\n"
        "Install one:\n"
        "  Windows:  Chrome is at https://google.com/chrome (Edge is usually pre-installed)\n"
        "  macOS:    brew install --cask google-chrome\n"
        "  Linux:    sudo apt install chromium-browser   OR   sudo snap install chromium",
        file=sys.stderr,
    )


# ── PNG Sizing ─────────────────────────────────────────────────────────────────


def get_png_size(scope: str, orientation: str) -> tuple[int, int | None]:
    """Return (width, height) for PNG screenshot. None height = auto."""
    if scope == "1pager":
        if orientation == "landscape":
            return (1123, 794)
        return (794, 1123)
    # full / summary — mobile width, auto height
    return (430, None)


# ── Output Path Helpers ────────────────────────────────────────────────────────


def build_output_path(
    input_path: str, fmt: str, scope: str, custom_output: str | None
) -> str:
    """Build the output file path based on input, format, and scope."""
    if custom_output:
        return custom_output

    p = Path(input_path)
    suffix_map = {"pdf": ".pdf", "html": ".html", "png": ".png"}
    scope_infix = "" if scope == "full" else f"-{scope}"
    return str(p.parent / f"{p.stem}{scope_infix}{suffix_map[fmt]}")


# ── Main ───────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert markdown/text/code files to polished PDF, HTML, PNG."
    )
    parser.add_argument("input", help="Input file path")
    parser.add_argument(
        "--format",
        choices=["pdf", "html", "png", "all"],
        default="pdf",
        dest="fmt",
        help="Output format (default: pdf)",
    )
    parser.add_argument(
        "--theme",
        choices=["minimal", "modern", "dark"],
        default="minimal",
        help="CSS theme (default: minimal)",
    )
    parser.add_argument(
        "--orientation",
        choices=["portrait", "landscape"],
        default="portrait",
        help="Page orientation (default: portrait)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Custom output path (single format only)",
    )
    parser.add_argument(
        "--scope",
        choices=["full", "summary", "1pager"],
        default="full",
        help="Content scope — used for PNG sizing (default: full)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # Validate input
    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    if args.output and args.fmt == "all":
        print(
            "Error: --output cannot be used with --format all", file=sys.stderr
        )
        sys.exit(2)

    # Prepare content
    content = prepare_content(args.input)
    title = Path(args.input).stem

    # Determine formats to produce
    formats = ["pdf", "html", "png"] if args.fmt == "all" else [args.fmt]

    for fmt in formats:
        output_path = build_output_path(args.input, fmt, args.scope, args.output)

        if fmt == "html":
            convert_to_html(content, args.theme, title, output_path)
            print(f"Created: {output_path}")

        elif fmt == "pdf":
            with tempfile.NamedTemporaryFile(
                suffix=".html", delete=False
            ) as tmp:
                tmp_html = tmp.name
            try:
                convert_to_html(content, args.theme, title, tmp_html)
                render_pdf(tmp_html, output_path, args.orientation)
                print(f"Created: {output_path}")
            finally:
                if os.path.exists(tmp_html):
                    os.unlink(tmp_html)

        elif fmt == "png":
            width, height = get_png_size(args.scope, args.orientation)
            with tempfile.NamedTemporaryFile(
                suffix=".html", delete=False
            ) as tmp:
                tmp_html = tmp.name
            try:
                convert_to_html(content, args.theme, title, tmp_html)
                render_png(tmp_html, output_path, width, height)
                print(f"Created: {output_path}")
            finally:
                if os.path.exists(tmp_html):
                    os.unlink(tmp_html)


if __name__ == "__main__":
    main()
