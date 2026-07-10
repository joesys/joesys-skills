#!/usr/bin/env python3
"""Per-function cyclomatic complexity analysis.

Supports indent-based (Python, GDScript) and brace-based (JS/TS, Rust,
Go, C++, C#) languages.  Outputs JSON to stdout for deterministic agent
consumption.

Usage:
    python compute_complexity.py --lang python --source DIR [--exclude PATTERNS]
"""
import argparse
import json
import os
import re
import sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

# ── Language profiles ─────────────────────────────────────────────

LANGUAGE_PROFILES: dict[str, dict] = {
    "python": {
        "extensions": [".py"],
        "mode": "indent",
        "function_pattern": r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(",
        "branch_keywords": ["if", "elif", "for", "while", "except", "and", "or"],
    },
    "gdscript": {
        "extensions": [".gd"],
        "mode": "indent",
        "function_pattern": r"^(\s*)(?:static\s+)?func\s+(\w+)\s*\(",
        "branch_keywords": ["if", "elif", "for", "while", "and", "or"],
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "mode": "brace",
        "function_pattern": (
            r"(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\("
            r"|(?:^|\s)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]*)=>"
            r"|(?:^|\s)(?:public|private|protected|static|async|readonly|\s)*(\w+)\s*\([^)]*\)\s*(?::\s*\w[^{]*)?\s*\{"
        ),
        "branch_keywords": ["if", "else if", "for", "while", "catch", "case", "&&", "||"],
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".mjs", ".cjs"],
        "mode": "brace",
        "function_pattern": (
            r"(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("
            r"|(?:^|\s)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]*)=>"
            r"|(?:^|\s)(?:public|private|protected|static|async|readonly|\s)*(\w+)\s*\([^)]*\)\s*\{"
        ),
        "branch_keywords": ["if", "else if", "for", "while", "catch", "case", "&&", "||"],
    },
    "rust": {
        "extensions": [".rs"],
        "mode": "brace",
        "function_pattern": (
            r"(?:^|\s)(?:pub\s+)?(?:async\s+)?fn\s+(\w+)"
        ),
        "branch_keywords": ["if", "else if", "for", "while", "match", "&&", "||"],
    },
    "go": {
        "extensions": [".go"],
        "mode": "brace",
        "function_pattern": r"(?:^|\s)func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(",
        "branch_keywords": ["if", "else if", "for", "case", "select", "&&", "||"],
    },
    "cpp": {
        "extensions": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx"],
        "mode": "brace",
        "function_pattern": (
            r"(?:^|\s)(?:[\w:*&<>,\s]+\s+)?(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:override\s*)?(?:noexcept\s*)?\{"
        ),
        "branch_keywords": ["if", "else if", "for", "while", "do", "catch", "case", "&&", "||"],
    },
    "csharp": {
        "extensions": [".cs"],
        "mode": "brace",
        "function_pattern": (
            r"(?:^|\s)(?:public|private|protected|internal|static|async|virtual|override|abstract|sealed|\s)+\s+"
            r"(?:[\w<>\[\]?,\s]+\s+)?(\w+)\s*\([^)]*\)\s*\{"
        ),
        "branch_keywords": ["if", "else if", "for", "foreach", "while", "do", "catch", "case", "&&", "||"],
    },
}


# ── CLI ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute per-function cyclomatic complexity")
    parser.add_argument(
        "--lang", required=True,
        choices=list(LANGUAGE_PROFILES.keys()),
        help="Language to analyse",
    )
    parser.add_argument("--source", required=True, help="Root directory to scan")
    parser.add_argument("--exclude", default="", help="Comma-separated glob patterns to exclude")
    return parser.parse_args()


# ── File discovery ────────────────────────────────────────────────

def is_excluded(filepath: str, patterns: list[str]) -> bool:
    """Check if *filepath* (relative to --source) matches any exclusion glob."""
    for pattern in patterns:
        if fnmatch(filepath, pattern):
            return True
        parts = PurePosixPath(filepath).parts
        for part in parts:
            if fnmatch(part, pattern.rstrip("/")):
                return True
    return False


def discover_files(source: str, extensions: list[str], exclude_patterns: list[str]) -> list[str]:
    """Walk *source* and return absolute paths of matching files."""
    results: list[str] = []
    source_path = Path(source).resolve()
    for root, _dirs, files in os.walk(source_path):
        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix not in extensions:
                continue
            rel = fpath.relative_to(source_path).as_posix()
            if exclude_patterns and is_excluded(rel, exclude_patterns):
                continue
            results.append(str(fpath))
    results.sort()
    return results


# ── Source cleaning ───────────────────────────────────────────────

def _strip_strings_and_comments_indent(source: str) -> str:
    """Remove string literals and comments from indent-based source."""
    # Remove triple-quoted strings first (docstrings)
    source = re.sub(r'"""[\s\S]*?"""', '""', source)
    source = re.sub(r"'''[\s\S]*?'''", "''", source)
    # Remove single-line strings
    source = re.sub(r'"(?:[^"\\]|\\.)*"', '""', source)
    source = re.sub(r"'(?:[^'\\]|\\.)*'", "''", source)
    # Remove comments
    source = re.sub(r"#.*$", "", source, flags=re.MULTILINE)
    return source


def _strip_strings_and_comments_brace(source: str) -> str:
    """Remove string literals and comments from brace-based source."""
    # Remove multi-line comments
    source = re.sub(r"/\*[\s\S]*?\*/", "", source)
    # Remove single-line comments
    source = re.sub(r"//.*$", "", source, flags=re.MULTILINE)
    # Remove template literals
    source = re.sub(r"`(?:[^`\\]|\\.)*`", '""', source)
    # Remove strings
    source = re.sub(r'"(?:[^"\\]|\\.)*"', '""', source)
    source = re.sub(r"'(?:[^'\\]|\\.)*'", "''", source)
    return source


# ── Branch counting ───────────────────────────────────────────────

def _count_branches(body: str, keywords: list[str]) -> int:
    """Count branch keyword occurrences in *body*.

    Multi-word keywords (``else if``) and operator keywords (``&&``,
    ``||``) are handled specially to avoid false positives.
    """
    count = 0
    for kw in keywords:
        if kw in ("&&", "||"):
            count += body.count(kw)
        elif " " in kw:
            # Multi-word keywords like "else if" — use regex for accuracy
            pattern = r"\b" + r"\s+".join(re.escape(w) for w in kw.split()) + r"\b"
            count += len(re.findall(pattern, body))
        else:
            # Single word keyword — match as whole word
            count += len(re.findall(r"\b" + re.escape(kw) + r"\b", body))
    return count


# ── Indent-based parsing (Python, GDScript) ───────────────────────

def _parse_indent_based(source: str, cleaned: str, profile: dict, filepath: str, source_root: str) -> list[dict]:
    """Extract functions and their complexity from indent-based source."""
    functions: list[dict] = []
    lines = source.splitlines()
    cleaned_lines = cleaned.splitlines()
    func_re = re.compile(profile["function_pattern"])

    i = 0
    while i < len(lines):
        m = func_re.match(lines[i])
        if m:
            indent = m.group(1)
            func_name = m.group(2)
            func_line = i + 1  # 1-indexed

            # Collect body: all subsequent lines with greater indentation
            body_start = i + 1
            body_lines: list[str] = []
            base_indent_len = len(indent)

            j = body_start
            while j < len(cleaned_lines):
                raw_line = lines[j]
                # Empty lines are part of the body (they don't end the function)
                if raw_line.strip() == "":
                    body_lines.append("")
                    j += 1
                    continue
                # Measure current indentation
                cur_indent = len(raw_line) - len(raw_line.lstrip())
                if cur_indent > base_indent_len:
                    body_lines.append(cleaned_lines[j] if j < len(cleaned_lines) else "")
                    j += 1
                else:
                    break
            else:
                pass  # reached end of file

            body = "\n".join(body_lines)
            cc = 1 + _count_branches(body, profile["branch_keywords"])

            rel_path = _relative_path(filepath, source_root)
            functions.append({
                "name": func_name,
                "file": rel_path,
                "line": func_line,
                "complexity": cc,
            })
            i = j  # skip past the body we already consumed
        else:
            i += 1

    return functions


# ── Brace-based parsing (JS/TS, Rust, Go, C++, C#) ───────────────

def _find_matching_brace(source: str, open_pos: int) -> int:
    """Return index of the ``}`` that matches the ``{`` at *open_pos*."""
    depth = 0
    for idx in range(open_pos, len(source)):
        if source[idx] == "{":
            depth += 1
        elif source[idx] == "}":
            depth -= 1
            if depth == 0:
                return idx
    return len(source) - 1  # fallback: end of file


def _line_number(source: str, char_pos: int) -> int:
    """Return 1-indexed line number for *char_pos* in *source*."""
    return source[:char_pos].count("\n") + 1


def _parse_brace_based(source: str, cleaned: str, profile: dict, filepath: str, source_root: str) -> list[dict]:
    """Extract functions and their complexity from brace-based source."""
    functions: list[dict] = []
    func_re = re.compile(profile["function_pattern"], re.MULTILINE)

    for m in func_re.finditer(source):
        # Pick the first non-None captured group as the function name
        func_name = None
        for g in m.groups():
            if g is not None:
                func_name = g
                break
        if func_name is None:
            continue

        # Skip common false positives for brace-based patterns
        if func_name in ("if", "else", "for", "while", "switch", "catch", "return", "new", "class"):
            continue

        # Find the opening brace after this match
        search_start = m.end()
        brace_pos = source.find("{", search_start)
        if brace_pos == -1:
            continue

        # Only accept the brace if it's reasonably close (within next 200 chars
        # to handle type annotations, parameter lists, etc.)
        if brace_pos - search_start > 200:
            continue

        # Find matching closing brace in cleaned source for correct nesting
        # Map brace_pos from source to cleaned — use same position since cleaning
        # preserves structure (only replaces string *contents*)
        if brace_pos >= len(cleaned):
            continue
        close_pos = _find_matching_brace(cleaned, brace_pos)
        body = cleaned[brace_pos + 1:close_pos]

        cc = 1 + _count_branches(body, profile["branch_keywords"])

        func_line = _line_number(source, m.start())
        rel_path = _relative_path(filepath, source_root)
        functions.append({
            "name": func_name,
            "file": rel_path,
            "line": func_line,
            "complexity": cc,
        })

    return functions


# ── Helpers ───────────────────────────────────────────────────────

def _relative_path(filepath: str, source_root: str) -> str:
    """Return *filepath* relative to *source_root* using forward slashes."""
    try:
        return str(Path(filepath).relative_to(Path(source_root).resolve()).as_posix())
    except ValueError:
        return filepath


def _build_distribution(functions: list[dict]) -> dict[str, int]:
    """Bucket function complexities into distribution ranges."""
    dist = {"1-5": 0, "6-10": 0, "11-15": 0, "16-20": 0, "21+": 0}
    for f in functions:
        cc = f["complexity"]
        if cc <= 5:
            dist["1-5"] += 1
        elif cc <= 10:
            dist["6-10"] += 1
        elif cc <= 15:
            dist["11-15"] += 1
        elif cc <= 20:
            dist["16-20"] += 1
        else:
            dist["21+"] += 1
    return dist


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    profile = LANGUAGE_PROFILES[args.lang]
    exclude_patterns = [p.strip() for p in args.exclude.split(",") if p.strip()]

    files = discover_files(args.source, profile["extensions"], exclude_patterns)

    all_functions: list[dict] = []

    for fpath in files:
        try:
            raw = Path(fpath).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if profile["mode"] == "indent":
            cleaned = _strip_strings_and_comments_indent(raw)
            funcs = _parse_indent_based(raw, cleaned, profile, fpath, args.source)
        else:
            cleaned = _strip_strings_and_comments_brace(raw)
            funcs = _parse_brace_based(raw, cleaned, profile, fpath, args.source)

        all_functions.extend(funcs)

    # Sort by complexity descending
    all_functions.sort(key=lambda f: f["complexity"], reverse=True)

    total = len(all_functions)
    avg = round(sum(f["complexity"] for f in all_functions) / total, 1) if total else 0
    max_func = all_functions[0] if all_functions else None

    result = {
        "language": args.lang,
        "total_functions": total,
        "average_complexity": avg,
        "max_complexity": max_func,
        "distribution": _build_distribution(all_functions),
        "functions": all_functions,
    }

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
