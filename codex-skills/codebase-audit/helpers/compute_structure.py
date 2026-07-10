#!/usr/bin/env python3
"""Structural metrics analysis: LOC, function lengths, nesting depth,
comment density, type annotation coverage.

Supports indent-based (Python, GDScript) and brace-based (JS/TS, Rust,
Go, C++, C#) languages.  Outputs JSON to stdout for deterministic agent
consumption.

Usage:
    python compute_structure.py --lang python --source DIR [--exclude PATTERNS]
"""
import argparse
import json
import os
import re
import statistics
import sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

# ── Language profiles ─────────────────────────────────────────────

LANGUAGE_PROFILES: dict[str, dict] = {
    "python": {
        "extensions": [".py"],
        "mode": "indent",
        "comment_pattern": r"^\s*#",
        "function_pattern": r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(",
        "type_annotation_pattern": r"^\s*(?:async\s+)?def\s+\w+\s*\([^)]*:.*\)|^\s*(?:async\s+)?def\s+\w+\s*\(.*\)\s*->",
        "nesting_keywords": ["if", "elif", "else", "for", "while", "with", "try", "except", "finally"],
        "typed": "optional",
    },
    "gdscript": {
        "extensions": [".gd"],
        "mode": "indent",
        "comment_pattern": r"^\s*#",
        "function_pattern": r"^(\s*)(?:static\s+)?func\s+(\w+)\s*\(",
        "type_annotation_pattern": r"^\s*(?:static\s+)?func\s+\w+\s*\([^)]*:.*\)|^\s*(?:static\s+)?func\s+\w+\s*\(.*\)\s*->",
        "nesting_keywords": ["if", "elif", "else", "for", "while", "match"],
        "typed": "optional",
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "mode": "brace",
        "comment_pattern": r"^\s*(?://|/\*|\*)",
        "function_pattern": (
            r"(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\("
            r"|(?:^|\s)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]*)=>"
            r"|(?:^|\s)(?:public|private|protected|static|async|readonly|\s)*(\w+)\s*\([^)]*\)\s*(?::\s*\w[^{]*)?\s*\{"
        ),
        "type_annotation_pattern": r":\s*\w+",
        "nesting_keywords": ["if", "else", "for", "while", "switch", "try", "catch", "finally"],
        "typed": "optional",
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".mjs", ".cjs"],
        "mode": "brace",
        "comment_pattern": r"^\s*(?://|/\*|\*)",
        "function_pattern": (
            r"(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("
            r"|(?:^|\s)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]*)=>"
            r"|(?:^|\s)(?:public|private|protected|static|async|readonly|\s)*(\w+)\s*\([^)]*\)\s*\{"
        ),
        "type_annotation_pattern": None,
        "nesting_keywords": ["if", "else", "for", "while", "switch", "try", "catch", "finally"],
        "typed": "none",
    },
    "rust": {
        "extensions": [".rs"],
        "mode": "brace",
        "comment_pattern": r"^\s*(?://|/\*|\*)",
        "function_pattern": r"(?:^|\s)(?:pub\s+)?(?:async\s+)?fn\s+(\w+)",
        "type_annotation_pattern": None,
        "nesting_keywords": ["if", "else", "for", "while", "loop", "match"],
        "typed": "always",
    },
    "go": {
        "extensions": [".go"],
        "mode": "brace",
        "comment_pattern": r"^\s*(?://|/\*|\*)",
        "function_pattern": r"(?:^|\s)func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(",
        "type_annotation_pattern": None,
        "nesting_keywords": ["if", "else", "for", "switch", "select"],
        "typed": "always",
    },
    "cpp": {
        "extensions": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx"],
        "mode": "brace",
        "comment_pattern": r"^\s*(?://|/\*|\*)",
        "function_pattern": (
            r"(?:^|\s)(?:[\w:*&<>,\s]+\s+)?(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:override\s*)?(?:noexcept\s*)?\{"
        ),
        "type_annotation_pattern": None,
        "nesting_keywords": ["if", "else", "for", "while", "do", "switch", "try", "catch"],
        "typed": "always",
    },
    "csharp": {
        "extensions": [".cs"],
        "mode": "brace",
        "comment_pattern": r"^\s*(?://|/\*|\*)",
        "function_pattern": (
            r"(?:^|\s)(?:public|private|protected|internal|static|async|virtual|override|abstract|sealed|\s)+\s+"
            r"(?:[\w<>\[\]?,\s]+\s+)?(\w+)\s*\([^)]*\)\s*\{"
        ),
        "type_annotation_pattern": None,
        "nesting_keywords": ["if", "else", "for", "foreach", "while", "do", "switch", "try", "catch", "finally"],
        "typed": "always",
    },
}


# ── CLI ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute structural metrics")
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


# ── Relative path helper ─────────────────────────────────────────

def _relative_path(filepath: str, source_root: str) -> str:
    """Return *filepath* relative to *source_root* using forward slashes."""
    try:
        return str(Path(filepath).relative_to(Path(source_root).resolve()).as_posix())
    except ValueError:
        return filepath


# ── Statistics helpers ────────────────────────────────────────────

def _compute_stats(values: list[int]) -> dict:
    """Compute max, median, and p90 for a list of integers."""
    if not values:
        return {"max": 0, "median": 0, "p90": 0}
    sorted_vals = sorted(values)
    p90_idx = int(len(sorted_vals) * 0.9)
    # Clamp to valid index range
    p90_idx = min(p90_idx, len(sorted_vals) - 1)
    return {
        "max": max(sorted_vals),
        "median": statistics.median(sorted_vals),
        "p90": sorted_vals[p90_idx],
    }


# ── Line counting ────────────────────────────────────────────────

def _count_lines(lines: list[str], comment_re: re.Pattern) -> tuple[int, int, int]:
    """Count total LOC, blank lines, and comment lines.

    Returns (total_loc, blank_lines, comment_lines).
    total_loc = number of non-blank lines.
    """
    blank = 0
    comment = 0
    for line in lines:
        if line.strip() == "":
            blank += 1
        elif comment_re.match(line):
            comment += 1
    total_loc = len(lines) - blank
    return total_loc, blank, comment


# ── Indent-based function parsing (Python, GDScript) ─────────────

def _parse_functions_indent(lines: list[str], profile: dict, filepath: str, source_root: str) -> list[dict]:
    """Extract functions, their lengths, and max nesting depth from indent-based source."""
    functions: list[dict] = []
    func_re = re.compile(profile["function_pattern"])
    type_re = re.compile(profile["type_annotation_pattern"]) if profile.get("type_annotation_pattern") else None

    i = 0
    while i < len(lines):
        m = func_re.match(lines[i])
        if m:
            indent = m.group(1)
            func_name = m.group(2)
            func_line = i + 1  # 1-indexed
            base_indent_len = len(indent)

            # Check type annotation on the definition line
            has_annotation = False
            if type_re and type_re.match(lines[i]):
                has_annotation = True

            # Collect body lines
            body_start = i + 1
            body_lines: list[str] = []
            max_nesting = 0

            j = body_start
            while j < len(lines):
                raw_line = lines[j]
                if raw_line.strip() == "":
                    body_lines.append("")
                    j += 1
                    continue
                cur_indent = len(raw_line) - len(raw_line.lstrip())
                if cur_indent > base_indent_len:
                    body_lines.append(raw_line)
                    # Compute nesting depth relative to function base
                    depth = (cur_indent - base_indent_len - 4) // 4  # -4 for function body base
                    if depth > 0:
                        max_nesting = max(max_nesting, depth)
                    j += 1
                else:
                    break

            func_length = len(body_lines)
            rel_path = _relative_path(filepath, source_root)
            functions.append({
                "name": func_name,
                "file": rel_path,
                "line": func_line,
                "length": func_length,
                "max_nesting": max_nesting,
                "has_annotation": has_annotation,
            })
            i = j
        else:
            i += 1

    return functions


# ── Brace-based function parsing (JS/TS, Rust, Go, C++, C#) ──────

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
    return len(source) - 1


def _line_number(source: str, char_pos: int) -> int:
    """Return 1-indexed line number for *char_pos* in *source*."""
    return source[:char_pos].count("\n") + 1


def _max_brace_depth(body: str) -> int:
    """Count max ``{`` nesting depth within a function body."""
    depth = 0
    max_depth = 0
    for ch in body:
        if ch == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == "}":
            depth -= 1
    return max_depth


def _strip_strings_and_comments_brace(source: str) -> str:
    """Remove string literals and comments from brace-based source."""
    source = re.sub(r"/\*[\s\S]*?\*/", "", source)
    source = re.sub(r"//.*$", "", source, flags=re.MULTILINE)
    source = re.sub(r"`(?:[^`\\]|\\.)*`", '""', source)
    source = re.sub(r'"(?:[^"\\]|\\.)*"', '""', source)
    source = re.sub(r"'(?:[^'\\]|\\.)*'", "''", source)
    return source


def _parse_functions_brace(source: str, cleaned: str, profile: dict, filepath: str, source_root: str) -> list[dict]:
    """Extract functions, their lengths, and max nesting depth from brace-based source."""
    functions: list[dict] = []
    func_re = re.compile(profile["function_pattern"], re.MULTILINE)

    for m in func_re.finditer(source):
        func_name = None
        for g in m.groups():
            if g is not None:
                func_name = g
                break
        if func_name is None:
            continue

        if func_name in ("if", "else", "for", "while", "switch", "catch", "return", "new", "class"):
            continue

        search_start = m.end()
        brace_pos = source.find("{", search_start)
        if brace_pos == -1:
            continue
        if brace_pos - search_start > 200:
            continue
        if brace_pos >= len(cleaned):
            continue

        close_pos = _find_matching_brace(cleaned, brace_pos)
        body = cleaned[brace_pos + 1:close_pos]

        body_lines = body.split("\n")
        func_length = len([l for l in body_lines if l.strip() != ""])

        max_nesting = _max_brace_depth(body)

        func_line = _line_number(source, m.start())
        rel_path = _relative_path(filepath, source_root)

        # For brace-based: check type annotation on the matched signature
        has_annotation = True  # default for always-typed

        functions.append({
            "name": func_name,
            "file": rel_path,
            "line": func_line,
            "length": func_length,
            "max_nesting": max_nesting,
            "has_annotation": has_annotation,
        })

    return functions


# ── Type annotation coverage ──────────────────────────────────────

def _compute_type_coverage(functions: list[dict], typed_mode: str) -> float:
    """Compute type annotation coverage based on language mode.

    typed_mode:
        "always" → always 1.0 (Go, C++, C#, Rust)
        "none"   → always 0.0 (JavaScript)
        "optional" → ratio of annotated functions (Python, GDScript, TypeScript)
    """
    if typed_mode == "always":
        return 1.0
    if typed_mode == "none":
        return 0.0
    if not functions:
        return 0.0
    annotated = sum(1 for f in functions if f["has_annotation"])
    return round(annotated / len(functions), 2)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    profile = LANGUAGE_PROFILES[args.lang]
    exclude_patterns = [p.strip() for p in args.exclude.split(",") if p.strip()]

    files = discover_files(args.source, profile["extensions"], exclude_patterns)
    comment_re = re.compile(profile["comment_pattern"])

    total_loc = 0
    total_blank = 0
    total_comment = 0
    file_lengths: list[int] = []
    all_functions: list[dict] = []

    for fpath in files:
        try:
            raw = Path(fpath).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = raw.splitlines()
        total_lines = len(lines)
        file_lengths.append(total_lines)

        loc, blank, comment = _count_lines(lines, comment_re)
        total_loc += loc
        total_blank += blank
        total_comment += comment

        if profile["mode"] == "indent":
            funcs = _parse_functions_indent(lines, profile, fpath, args.source)
        else:
            cleaned = _strip_strings_and_comments_brace(raw)
            funcs = _parse_functions_brace(raw, cleaned, profile, fpath, args.source)

        all_functions.extend(funcs)

    # Compute derived metrics
    func_lengths = [f["length"] for f in all_functions]
    nesting_depths = [f["max_nesting"] for f in all_functions]
    comment_density = round(total_comment / total_loc, 2) if total_loc > 0 else 0.0
    type_coverage = _compute_type_coverage(all_functions, profile["typed"])

    files_over_500 = []
    for i, fpath in enumerate(files):
        if i < len(file_lengths) and file_lengths[i] > 500:
            files_over_500.append(_relative_path(fpath, args.source))

    functions_over_50 = [
        {"name": f["name"], "file": f["file"], "line": f["line"], "length": f["length"]}
        for f in all_functions if f["length"] > 50
    ]

    result = {
        "language": args.lang,
        "total_files": len(files),
        "total_loc": total_loc,
        "blank_lines": total_blank,
        "comment_lines": total_comment,
        "comment_density": comment_density,
        "file_lengths": _compute_stats(file_lengths),
        "function_lengths": _compute_stats(func_lengths),
        "nesting_depth": _compute_stats(nesting_depths),
        "type_annotation_coverage": type_coverage,
        "files_over_500_lines": files_over_500,
        "functions_over_50_lines": functions_over_50,
    }

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
