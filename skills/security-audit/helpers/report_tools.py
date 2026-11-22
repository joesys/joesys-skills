#!/usr/bin/env python3
"""Finish a security-audit report: colour its code, build its navigation, check it.

    report_tools.py finish REPORT.html [--repo DIR] [--commit SHA] [--check-only]

The report is one HTML file that a model wrote into the report template. This
script does the three jobs that a model does badly by hand:

1. It adds the syntax colours to every code block, at build time, so the page
   needs no script.
2. It fills every element with a data-gen attribute: the severity counts in
   the top bar, the index of findings, the jump bar and the links to the
   previous and next finding in each finding, and the entry counts of the
   closed parts. It gives each part of a finding an id for the jump bar.
3. It checks the page: no script, no outside resource, no broken link, the
   fixed sections, every part of every finding, and, with --repo, that every
   code quote matches the file it names and that every diff with line
   numbers applies to the code. The checks change no file of the project.

When the page has no problem, it also writes the findings as SARIF 2.1.0,
for GitHub code scanning, next to the page: report.sarif. It never uploads
the file.

The exit code is 0 when the page has no problem, and 1 when it has.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low", "info")
CONFIDENCES = ("high", "medium", "low")
REQUIRED_PARTS = ("short", "context", "code", "explanation", "reproduce", "priority", "consequences", "fix", "prevent")
OPTIONAL_PARTS = ("path", "verify", "used", "views")
REACH_LEVELS = {
    "anyone": "Anyone, no login", "user": "A logged-in user", "partner": "A partner or token holder",
    "admin": "An admin of one tenant", "insider": "Server, log or code access",
}
FIX_SIZES = {"small": "A few lines in one place", "medium": "Several places, or one new check", "large": "A new flow, or a team decision"}
PATH_STEPS = ("way-in", "step", "missing", "result")
REQUIRED_SECTIONS = (
    "read-first", "assessment", "themes", "today", "findings",
    "before-fix", "safe", "not-checked", "rejected", "method", "basics",
)

# A note that the writer adds at the end of a quoted line, after a comment sign.
NOTE_WORDS = {"PROBLEM": "problem", "OK": "ok", "NEW": "new"}
NOTE_IN_COMMENT = re.compile(r"^\W{1,4}\s*(PROBLEM|OK|NEW):")


# =============================================================================
# Part 1: code colours
# =============================================================================

CODE_BLOCK = re.compile(r"(<pre\b[^>]*>\s*<code\b[^>]*>)(.*?)(</code>\s*</pre>)", re.DOTALL)
LANGUAGE_CLASS = re.compile(r'class="[^"]*\b(?:language|lang)-([^\s"]+)')
DIFF_SPAN = re.compile(r'<span class="diff-line[^"]*">(.*?)</span>', re.DOTALL)
TOKEN_SPAN = re.compile(r'<span class="tok-[a-z]+">|</span>')


def colour_code_blocks(page: str) -> str:
    """Add colour spans to every code block that names a known language."""

    def colour(block: re.Match) -> str:
        opening, inner, closing = block.groups()
        language = LANGUAGE_CLASS.search(opening)
        lexer = LEXERS.get(language.group(1).lower()) if language else None
        plain = without_colours(inner)
        if lexer is None or "<" in plain:  # an unknown language, or a real tag: leave it
            return block.group(0)
        return opening + lexer(html.unescape(plain)) + closing

    return CODE_BLOCK.sub(colour, page)


def without_colours(inner: str) -> str:
    """Undo an earlier colouring, so that colouring twice changes nothing."""
    if DIFF_SPAN.search(inner):
        inner = DIFF_SPAN.sub(lambda line: line.group(1) + "\n", inner)
        inner = inner[:-1] if inner.endswith("\n") else inner
    return TOKEN_SPAN.sub("", inner)


def span(kind: str | None, text: str) -> str:
    escaped = html.escape(text, quote=False)
    return escaped if kind is None else f'<span class="tok-{kind}">{escaped}</span>'


def comment_kind(text: str) -> str:
    note = NOTE_IN_COMMENT.match(text)
    return NOTE_WORDS[note.group(1)] if note else "c"


@dataclass(frozen=True)
class Syntax:
    """What the general lexer must know about one language family."""

    keywords: frozenset[str] = frozenset()
    line_comments: tuple[str, ...] = ()
    block_comments: tuple[tuple[str, str], ...] = ()
    quotes: tuple[str, ...] = ('"', "'")
    long_quotes: tuple[str, ...] = ()  # strings that may run over several lines
    names: re.Pattern | None = None  # decorators, variables, keys: coloured as names
    ignore_case: bool = False
    key_strings: bool = False  # a string before a colon is a key (JSON)


WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
NUMBER = re.compile(r"0[xX][0-9a-fA-F_]+|\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?")
COLON_NEXT = re.compile(r"\s*:")


def lex_general(syntax: Syntax, text: str) -> str:
    out: list[str] = []
    plain: list[str] = []
    i, end = 0, len(text)

    def emit(kind: str | None, stop: int) -> None:
        nonlocal i
        if kind is None:
            plain.append(text[i:stop])
        else:
            out.append(span(None, "".join(plain)))
            plain.clear()
            out.append(span(kind, text[i:stop]))
        i = stop

    while i < end:
        opener = next((pair for pair in syntax.block_comments if text.startswith(pair[0], i)), None)
        if opener:
            close = text.find(opener[1], i + len(opener[0]))
            stop = end if close < 0 else close + len(opener[1])
            emit(comment_kind(text[i:stop]), stop)
        elif any(text.startswith(sign, i) for sign in syntax.line_comments):
            newline = text.find("\n", i)
            stop = end if newline < 0 else newline
            emit(comment_kind(text[i:stop]), stop)
        elif any(text.startswith(quote, i) for quote in syntax.long_quotes):
            quote = next(q for q in syntax.long_quotes if text.startswith(q, i))
            close = text.find(quote, i + len(quote))
            emit("s", end if close < 0 else close + len(quote))
        elif text[i] in syntax.quotes:
            stop = end_of_string(text, i)
            is_key = syntax.key_strings and COLON_NEXT.match(text, stop)
            emit("d" if is_key else "s", stop)
        elif syntax.names and (name := syntax.names.match(text, i)) and name.end() > i:
            emit("d", name.end())
        elif text[i].isdigit():
            emit("n", NUMBER.match(text, i).end())
        elif word := WORD.match(text, i):
            found = word.group(0).lower() if syntax.ignore_case else word.group(0)
            emit("k" if found in syntax.keywords else None, word.end())
        else:
            emit(None, i + 1)
    out.append(span(None, "".join(plain)))
    return "".join(out)


def end_of_string(text: str, start: int) -> int:
    """The index after a one-line string. A backslash keeps the next character."""
    quote, i = text[start], start + 1
    while i < len(text) and text[i] != "\n":
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    return min(i, len(text))


HTML_OUTSIDE = re.compile(
    r"(?P<comment><!--.*?-->)|(?P<template>\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})|(?P<tag></?[A-Za-z][\w:.-]*)",
    re.DOTALL,
)
HTML_INSIDE = re.compile(
    r"""(?P<string>"[^"]*"|'[^']*')|(?P<template>\{\{.*?\}\}|\{%.*?%\})|(?P<close>/?>)|(?P<name>[\w:@.-]+)""",
    re.DOTALL,
)


def lex_html(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        found = HTML_OUTSIDE.search(text, i)
        if not found:
            break
        out.append(span(None, text[i:found.start()]))
        i = found.end()
        if found.lastgroup == "comment":
            out.append(span(comment_kind(found.group(0)), found.group(0)))
        elif found.lastgroup == "template":
            out.append(span("k", found.group(0)))
        else:
            out.append(span("t", found.group(0)))
            i = lex_html_tag(text, i, out)
    out.append(span(None, text[i:]))
    return "".join(out)


def lex_html_tag(text: str, i: int, out: list[str]) -> int:
    """Colour the attributes of one tag. Return the index after its closing sign."""
    kinds = {"string": "s", "template": "k", "close": "t", "name": "n"}
    while i < len(text):
        found = HTML_INSIDE.search(text, i)
        if not found:
            break
        out.append(span(None, text[i:found.start()]))
        out.append(span(kinds[found.lastgroup], found.group(0)))
        i = found.end()
        if found.lastgroup == "close":
            break
    return i


def lex_diff(text: str) -> str:
    """One block-level span for each line. The spans carry the line breaks."""

    def kind(line: str) -> str:
        if line.startswith(("+++", "---", "diff ", "index ")):
            return "file"
        if line.startswith("@@"):
            return "hunk"
        if line.startswith("+"):
            return "add"
        if line.startswith("-"):
            return "del"
        return "ctx"

    return "".join(
        f'<span class="diff-line {kind(line)}">{html.escape(line, quote=False)}</span>' for line in text.split("\n")
    )


def words(text: str) -> frozenset[str]:
    return frozenset(text.split())


C_COMMENTS = {"line_comments": ("//",), "block_comments": (("/*", "*/"),)}
PYTHON = Syntax(
    keywords=words(
        "False None True and as assert async await break case class continue def del elif else except finally for "
        "from global if import in is lambda match nonlocal not or pass raise return self try while with yield"
    ),
    line_comments=("#",),
    long_quotes=('"""', "'''"),
    names=re.compile(r"@[\w.]+"),
)
JAVASCRIPT = Syntax(
    keywords=words(
        "abstract as async await break case catch class const continue debugger declare default delete do else enum "
        "export extends false finally for from function if implements import in instanceof interface let namespace "
        "new null of private protected public readonly return static super switch this throw true try type typeof "
        "undefined var void while with yield"
    ),
    long_quotes=("`",),
    names=re.compile(r"@[\w.]+"),
    **C_COMMENTS,
)
C_FAMILY = Syntax(
    keywords=words(
        "abstract assert async auto await bool boolean break byte case catch char class const continue data default "
        "do double else enum extends false final finally float for fun func goto guard if implements import init "
        "instanceof int interface internal let long namespace native new nil null nullptr object override package "
        "private protected public return self short static string struct super suspend switch synchronized template "
        "this throw throws true try typedef union unsigned using val var virtual void volatile when while"
    ),
    names=re.compile(r"@[\w.]+"),
    **C_COMMENTS,
)
GO = Syntax(
    keywords=words(
        "break case chan const continue default defer else fallthrough false for func go goto if import interface "
        "map nil package range return select struct switch true type var"
    ),
    long_quotes=("`",),
    **C_COMMENTS,
)
RUST = Syntax(
    keywords=words(
        "Self as async await break const continue crate dyn else enum extern false fn for if impl in let loop match "
        "mod move mut pub ref return self static struct super trait true type unsafe use where while"
    ),
    quotes=('"',),
    **C_COMMENTS,
)
PHP = Syntax(
    keywords=words(
        "abstract and array as break case catch class clone const continue declare default do echo else elseif empty "
        "extends false final finally fn for foreach function global if implements include include_once instanceof "
        "interface isset list namespace new null or print private protected public require require_once return "
        "static switch throw trait true try unset use var while yield"
    ),
    line_comments=("//", "#"),
    block_comments=(("/*", "*/"),),
    names=re.compile(r"\$\w+"),
)
RUBY = Syntax(
    keywords=words(
        "alias and begin break case class def do else elsif end ensure false for if in module next nil not or redo "
        "require rescue retry return self super then true undef unless until when while yield"
    ),
    line_comments=("#",),
    names=re.compile(r"@{1,2}\w+|:\w+"),
)
SHELL = Syntax(
    keywords=words(
        "case declare do done elif else esac exit export fi for function if in local readonly return set source then "
        "unset until while"
    ),
    line_comments=("#",),
    names=re.compile(r"\$\{[^}\n]*\}|\$\w+|\$[@#?*!$]"),
)
SQL = Syntax(
    keywords=words(
        "all alter and as between by case create default delete distinct drop else end exists foreign from group "
        "having in index inner insert into is join key left like limit not null offset on or order outer primary "
        "references returning right select set table then union update values when where with"
    ),
    line_comments=("--",),
    block_comments=(("/*", "*/"),),
    ignore_case=True,
)
JSON = Syntax(keywords=words("true false null"), quotes=('"',), key_strings=True)
YAML = Syntax(
    keywords=words("true false null yes no on off"),
    line_comments=("#",),
    names=re.compile(r"(?m)^[ \t]*(?:- )?[\w./-]+(?=\s*:)"),
)
CONFIG = Syntax(
    keywords=words("true false"),
    line_comments=("#", ";"),
    names=re.compile(r"(?m)^[ \t]*[\w.-]+(?=\s*=)|^\[[^\]\n]*\]+"),
)
CSS = Syntax(block_comments=(("/*", "*/"),), names=re.compile(r"@?[\w-]+(?=\s*:)"))


def general(syntax: Syntax):
    return lambda text: lex_general(syntax, text)


LEXERS = {
    **dict.fromkeys(("python", "py"), general(PYTHON)),
    **dict.fromkeys(("javascript", "js", "jsx", "mjs", "typescript", "ts", "tsx"), general(JAVASCRIPT)),
    **dict.fromkeys(
        ("java", "kotlin", "kt", "c", "cpp", "c++", "csharp", "cs", "swift", "dart", "scala", "objc"),
        general(C_FAMILY),
    ),
    **dict.fromkeys(("go", "golang"), general(GO)),
    **dict.fromkeys(("rust", "rs"), general(RUST)),
    "php": general(PHP),
    **dict.fromkeys(("ruby", "rb"), general(RUBY)),
    **dict.fromkeys(("shell", "sh", "bash", "zsh", "console"), general(SHELL)),
    "sql": general(SQL),
    "json": general(JSON),
    **dict.fromkeys(("yaml", "yml"), general(YAML)),
    **dict.fromkeys(("toml", "ini", "conf", "properties"), general(CONFIG)),
    "css": general(CSS),
    **dict.fromkeys(("html", "htm", "xml", "svg", "django", "jinja", "vue"), lex_html),
    **dict.fromkeys(("diff", "patch"), lex_diff),
    **dict.fromkeys(("text", "plain", "txt"), lambda text: span(None, text)),
}


# =============================================================================
# Part 2: page checks
# =============================================================================

BANNED_TAGS = {"script", "iframe", "frame", "object", "embed", "applet", "base"}
RESOURCE_TAGS = {"img", "source", "video", "audio", "track", "input"}
PLACEHOLDER = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
GUIDE_COMMENT = re.compile(r"<!--\s*GUIDE:")
FINDING_ID = re.compile(r"F-\d{2,}")
OUTSIDE_IN_CSS = re.compile(r"@import|url\(\s*['\"]?(?!data:|#)", re.IGNORECASE)


class Page(HTMLParser):
    """Collect what the checks need, in one pass over the page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.problems: list[str] = []
        self.ids: dict[str, int] = {}
        self.id_order: list[str] = []
        self.links: list[tuple[str, int]] = []
        self.findings: list[dict] = []
        self.slots: list[dict] = []  # every data-gen element, in page order
        self.part_tags: list[dict] = []  # every data-part element, in page order
        self.counts: dict[str, str] = {}
        self.group_heads: set[str] = set()
        self.has_viewport = self.has_charset = self.has_lang = False
        self.title = ""
        self.style = ""
        self._details: list[dict | None] = []  # one entry for each open <details>
        self._in_summary = False
        self._title_depth = 0  # the depth of open <span> tags inside the title of a finding
        self._row: dict | None = None  # the table row that is open inside a closed part
        self._short: list = []  # the tag of the "In short" part of a finding, and its depth
        self._pre: dict | None = None
        self._capture: tuple[str, str] | None = None  # the tag and the target of text being collected
        self._text = ""

    # --- what the parser calls ---

    def handle_starttag(self, tag: str, attr_list: list[tuple[str, str | None]]) -> None:
        attrs = {name: value or "" for name, value in attr_list}
        line = self.getpos()[0]
        classes = attrs.get("class", "").split()
        self._check_safety(tag, attrs, line)
        self._check_inside_pre(tag, attrs, classes, line)

        if "id" in attrs:
            self.ids[attrs["id"]] = self.ids.get(attrs["id"], 0) + 1
            self.id_order.append(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.links.append((attrs["href"][1:], line))

        if tag == "html" and attrs.get("lang"):
            self.has_lang = True
        if tag == "meta":
            self.has_viewport |= attrs.get("name") == "viewport"
            self.has_charset |= "charset" in attrs
            if attrs.get("http-equiv", "").lower() == "refresh":
                self.problems.append(f"A page that reloads or redirects by itself is not allowed (line {line}).")
        if tag in ("title", "style"):
            self._capture, self._text = (tag, tag), ""
        if "data-count" in attrs:
            self._capture, self._text = (tag, "count:" + attrs["data-count"]), ""
        if "group-head" in classes:
            self.group_heads.update(name[2:] for name in classes if name.startswith("g-"))

        if tag == "details":
            block = None
            if "finding" in classes:
                block = {
                    "kind": "finding", "id": attrs.get("id", ""), "severity": attrs.get("data-severity", ""),
                    "confidence": attrs.get("data-confidence", ""), "parts": [], "label": None,
                    "quotes": 0, "line": line, "title": "", "slots": [], "files": [], "steps": [],
                    "area": attrs.get("data-area"), "reach": attrs.get("data-reach"),
                    "reach_label": attrs.get("data-reach-label"), "fix_size": attrs.get("data-fix-size"),
                    "found_by": attrs.get("data-found-by"), "cwe": attrs.get("data-cwe"),
                    "places": [], "short": "",
                }
                self.findings.append(block)
            elif "appendix" in classes:
                block = {"kind": "appendix", "id": attrs.get("id", ""), "rows": 0, "items": 0}
            self._details.append(block)
        finding = self._finding()
        appendix = self._open("appendix")
        if appendix and "none" not in classes:
            if tag == "tr":
                self._row = appendix
            elif tag == "td" and self._row is appendix:
                appendix["rows"] += 1
                self._row = None
            elif tag == "li":
                appendix["items"] += 1
        if "data-gen" in attrs:
            slot = {"name": attrs["data-gen"], "finding": finding, "appendix": appendix, "attrs": attrs, "line": line}
            self.slots.append(slot)
            if finding is not None:
                finding["slots"].append(attrs["data-gen"])
        if "data-part" in attrs:
            self.part_tags.append({"finding": finding, "part": attrs["data-part"], "id": attrs.get("id", "")})
        if finding is None:
            return
        if tag == "summary":
            self._in_summary = True
        if self._in_summary and tag == "span":
            if self._title_depth:
                self._title_depth += 1
            elif "t" in classes and not finding["title"]:
                self._title_depth = 1
        if self._in_summary and "sev" in classes and finding["label"] is None:
            finding["label"] = " ".join(name for name in classes if name != "sev")
        if "data-part" in attrs:
            finding["parts"].append(attrs["data-part"])
        if tag == "pre" and attrs.get("data-file") and attrs.get("data-lines"):
            finding["quotes"] += 1
            if attrs["data-file"] not in finding["files"]:
                finding["files"].append(attrs["data-file"])
            finding["places"].append((attrs["data-file"], attrs["data-lines"]))
        if self._short and tag == self._short[0]:
            self._short[1] += 1
        if attrs.get("data-part") == "short" and not self._short:
            self._short = [tag, 1]
        if "data-step" in attrs:
            finding["steps"].append(attrs["data-step"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "details" and self._details:
            self._details.pop()
        if tag == "summary":
            self._in_summary = False
            self._title_depth = 0
        if tag == "span" and self._title_depth:
            self._title_depth -= 1
        if tag == "tr":
            self._row = None
        if self._short and tag == self._short[0]:
            self._short[1] -= 1
            if not self._short[1]:
                self._short = []
        if tag == "pre" and self._pre:
            if not self._pre["language"]:
                self.problems.append(
                    f"A code block has no language (line {self._pre['line']}). "
                    'Write <code class="language-...">, for example language-python or language-text.'
                )
            self._pre = None
        if self._capture and tag == self._capture[0]:
            target = self._capture[1]
            if target == "title":
                self.title = self._text.strip()
            elif target == "style":
                self.style += self._text
            else:
                self.counts[target.removeprefix("count:")] = self._text.strip()
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._text += data
        if self._title_depth and (finding := self._finding()):
            finding["title"] += data
        if self._short and (finding := self._finding()):
            finding["short"] += data

    # --- helpers ---

    def _finding(self) -> dict | None:
        return self._open("finding")

    def _open(self, kind: str) -> dict | None:
        return next((block for block in reversed(self._details) if block and block["kind"] == kind), None)

    def _check_safety(self, tag: str, attrs: dict[str, str], line: int) -> None:
        if tag in BANNED_TAGS:
            self.problems.append(f"A <{tag}> tag is not allowed (line {line}). The report must work with no script.")
        for name, value in attrs.items():
            if name.startswith("on"):
                self.problems.append(f'The event handler "{name}" is not allowed (line {line}).')
            if name in ("href", "src", "action") and value.strip().lower().startswith("javascript:"):
                self.problems.append(f'A "javascript:" address is not allowed (line {line}).')
            if name == "style" and OUTSIDE_IN_CSS.search(value):
                self.problems.append(f"A style attribute loads an outside resource (line {line}).")
        loads = tag == "link" or (
            tag in RESOURCE_TAGS and (attrs.get("src", "data:").strip()[:5].lower() != "data:" or "srcset" in attrs)
        )
        if loads:
            self.problems.append(
                f"A <{tag}> tag loads an outside resource (line {line}). The report must be one file with nothing to download."
            )

    def _check_inside_pre(self, tag: str, attrs: dict[str, str], classes: list[str], line: int) -> None:
        if tag == "pre":
            self._pre = {"line": line, "language": False}
            return
        if self._pre is None:
            return
        if tag == "code":
            self._pre["language"] = bool(LANGUAGE_CLASS.search(f'class="{attrs.get("class", "")}"'))
        elif not (tag == "span" and classes and (classes[0].startswith("tok-") or classes[0] == "diff-line")):
            self.problems.append(
                f"A <{tag}> tag stands inside a code block (line {line}). Inside code, write < as &lt; and > as &gt;."
            )


def check_page(page: str) -> list[str]:
    """Every problem of the page, in plain words. An empty list means the page is good."""
    parsed = Page()
    parsed.feed(page)
    parsed.close()
    problems = list(parsed.problems)

    problems += leftover_template_text(page)
    if OUTSIDE_IN_CSS.search(parsed.style):
        problems.append("The style sheet loads an outside resource (@import or url). Keep all styles inside the page.")
    if not parsed.has_viewport:
        problems.append('The <meta name="viewport"> tag is missing. Without it the page is hard to read on a phone.')
    if not parsed.has_charset:
        problems.append('The <meta charset="utf-8"> tag is missing.')
    if not parsed.has_lang:
        problems.append('The <html> tag has no lang attribute.')
    if not parsed.title:
        problems.append("The page has no <title>.")

    for name, count in parsed.ids.items():
        if count > 1:
            problems.append(f'The id "{name}" is used more than once ({count} times). Every id must be unique.')
    for target, line in parsed.links:
        if target not in parsed.ids:
            problems.append(f'The link "#{target}" points to no element (line {line}).')

    problems += check_sections(parsed)
    problems += check_findings(parsed)
    problems += check_labels(parsed)
    problems += unfilled_slots(page, parsed)
    return problems


def leftover_template_text(page: str) -> list[str]:
    problems = []
    for name in sorted(set(PLACEHOLDER.findall(page))):
        line = page[: page.index(name)].count("\n") + 1
        problems.append(f"The placeholder {name} is still in the page (first at line {line}). Replace it with real text.")
    guides = GUIDE_COMMENT.findall(page)
    if guides:
        line = page[: GUIDE_COMMENT.search(page).start()].count("\n") + 1
        problems.append(f"{len(guides)} GUIDE comment(s) are still in the page (first at line {line}). Delete them.")
    return problems


def check_sections(parsed: Page) -> list[str]:
    problems = [
        f'The section with the id "{name}" is missing. Keep every section of the template.'
        for name in REQUIRED_SECTIONS if name not in parsed.ids
    ]
    present = [name for name in parsed.id_order if name in REQUIRED_SECTIONS]
    expected = [name for name in REQUIRED_SECTIONS if name in present]
    if not problems and present != expected:
        problems.append(f"The sections are in the wrong order. The order of the template is: {', '.join(expected)}.")
    return problems


def check_findings(parsed: Page) -> list[str]:
    problems: list[str] = []
    ranked: list[tuple[str, int]] = []
    for finding in parsed.findings:
        name = finding["id"] or f"the finding at line {finding['line']}"
        if not FINDING_ID.fullmatch(finding["id"]):
            problems.append(f'The id of a finding must look like F-NN, for example F-01. Found "{finding["id"]}" (line {finding["line"]}).')
        valid_severity = finding["severity"] in SEVERITIES
        if not valid_severity:
            problems.append(f'data-severity of {name} is "{finding["severity"]}". Use one of: {", ".join(SEVERITIES)}.')
        if finding["confidence"] not in CONFIDENCES:
            problems.append(f'data-confidence of {name} is "{finding["confidence"]}". Use one of: {", ".join(CONFIDENCES)}.')
        problems += check_parts(name, finding["parts"])
        for slot in FINDING_SLOTS:
            if slot not in finding["slots"]:
                problems.append(
                    f'{name} has no empty element with data-gen="{slot}". Copy it from the template; the script fills it.'
                )
        if finding["quotes"] == 0:
            problems.append(
                f"{name} has no code quote. Give at least one <pre data-file=\"...\" data-lines=\"...\"> block with the real lines."
            )
        if valid_severity:
            ranked.append((name, SEVERITIES.index(finding["severity"])))
            if finding["label"] != finding["severity"]:
                problems.append(
                    f'The severity label in the title of {name} says "{finding["label"]}", but data-severity says "{finding["severity"]}".'
                )

    for (before, before_rank), (after, after_rank) in zip(ranked, ranked[1:]):
        if after_rank < before_rank:
            problems.append(
                f"{after} ({SEVERITIES[after_rank]}) stands after {before} ({SEVERITIES[before_rank]}). "
                "The findings are not in the order of severity."
            )

    used = {SEVERITIES[rank] for _, rank in ranked}
    for severity in SEVERITIES:
        real = sum(1 for finding in parsed.findings if finding["severity"] == severity)
        shown = parsed.counts.get(severity)
        if shown is None:
            problems.append(f'The table of the assessment has no count cell for "{severity}" (data-count="{severity}").')
        elif not PLACEHOLDER.search(shown) and shown != str(real):
            problems.append(f'The count for "{severity}" says {shown}, but the page has {real} such finding(s).')
        if severity in used and severity not in parsed.group_heads:
            problems.append(f'There is no group heading for the severity "{severity}" (class "group-head g-{severity}").')
        if severity in parsed.group_heads and severity not in used:
            problems.append(f'There is a group heading for "{severity}", but no finding has that severity. Delete the group heading.')
    return problems


def filled_in(value: str | None) -> bool:
    """False for a value that is still a template placeholder: the placeholder check reports it."""
    return value is None or "{{" not in value


def declared_areas(parsed: Page) -> list[str] | None:
    lists = [slot["attrs"].get("data-areas") for slot in parsed.slots if slot["name"] == "areas"]
    lists = [value for value in lists if value is not None]
    if not lists:
        return None
    return [area.strip() for area in lists[0].split("|") if area.strip()]


def check_labels(parsed: Page) -> list[str]:
    """The labels that the pictures are drawn from, and the finding ids that a picture names."""
    problems: list[str] = []
    areas = declared_areas(parsed)
    if parsed.findings and areas is None:
        problems.append(
            'The picture "Where the problems are" has no data-areas. List the parts of the app there, separated by "|".'
        )
    for finding in parsed.findings:
        name = finding["id"] or f"the finding at line {finding['line']}"
        area = finding["area"]
        if filled_in(area) and areas is not None and filled_in("|".join(areas)) and area not in areas:
            problems.append(f'data-area of {name} is "{area}". Use one of the parts in data-areas: {", ".join(areas)}.')
        if filled_in(finding["reach"]) and finding["reach"] not in REACH_LEVELS:
            problems.append(f'data-reach of {name} is "{finding["reach"]}". Use one of: {", ".join(REACH_LEVELS)}.')
        if filled_in(finding["reach_label"]) and not (finding["reach_label"] or "").strip():
            problems.append(f"data-reach-label of {name} is empty. Say in the app's words who can reach the flaw.")
        if filled_in(finding["fix_size"]) and finding["fix_size"] not in FIX_SIZES:
            problems.append(f'data-fix-size of {name} is "{finding["fix_size"]}". Use one of: {", ".join(FIX_SIZES)}.')
        if filled_in(finding["cwe"]) and not re.fullmatch(r"\d+(?: \d+)*", (finding["cwe"] or "").strip()):
            problems.append(f'data-cwe of {name} is "{finding["cwe"] or ""}". Give the CWE numbers only, the main one first, such as "639 640".')
        if filled_in(finding["found_by"]) and not (finding["found_by"] or "").split():
            problems.append(f'data-found-by of {name} is empty or missing. Name who found it, for example "finder-1 reviewer".')
        if finding["severity"] in ("critical", "high") and "path" not in finding["parts"]:
            problems.append(f'{name} is {finding["severity"]} and has no part "path" (data-part="path"). Draw the path through the code.')
        if "path" in finding["parts"]:
            wrong = [step for step in finding["steps"] if step not in PATH_STEPS]
            if wrong:
                problems.append(f'The path of {name} has the data-step "{wrong[0]}". Use one of: {", ".join(PATH_STEPS)}.')
            if "missing" not in finding["steps"]:
                problems.append(f'The path of {name} has no step with data-step="missing". Mark the check that is missing or wrong.')
    known = {finding["id"] for finding in parsed.findings}
    for slot in parsed.slots:
        named = slot["attrs"].get("data-findings")
        if not filled_in(named):
            continue
        for finding_id in (named or "").split():
            if finding_id not in known:
                problems.append(f'data-findings names {finding_id} (line {slot["line"]}), but the page has no such finding.')
    return problems


def check_parts(name: str, parts: list[str]) -> list[str]:
    problems = [f'{name} has the unknown part "{part}".' for part in parts if part not in REQUIRED_PARTS + OPTIONAL_PARTS]
    problems += [f'{name} has no part "{part}" (data-part="{part}").' for part in REQUIRED_PARTS if part not in parts]
    present = [part for part in parts if part in REQUIRED_PARTS]
    if not problems and present != list(REQUIRED_PARTS):
        problems.append(f"The parts of {name} are in the wrong order. The order is: {', '.join(REQUIRED_PARTS)}.")
    return problems


# =============================================================================
# Part 3: quote checks
# =============================================================================

QUOTE_BLOCK = re.compile(r"<pre\b([^>]*)>\s*<code\b[^>]*>(.*?)</code>\s*</pre>", re.DOTALL)
LINE_RANGE = re.compile(r"(\d+)(?:-(\d+))?")
NOTE_AT_LINE_END = re.compile(r"\s*(?:#|//|/\*|<!--|--|;|%|\{#)\s*(?:PROBLEM|OK|NEW):.*$")
LEFT_OUT = re.compile(r"\W*(?:\.\.\.|…)\W*")
SECRET_FILE = re.compile(
    r"(?:^|/)(?:\.env(?:\.(?!example$|sample$|template$|dist$)[^/]*)?|[^/]*\.(?:pem|key|p12|pfx|jks|keystore)"
    r"|id_(?:rsa|dsa|ecdsa|ed25519)|credentials(?:\.json)?|[^/]*service[-_]account[^/]*\.json"
    r"|\.netrc|\.npmrc|\.pypirc|secrets?\.(?:ya?ml|json|toml))$",
    re.IGNORECASE,
)


def check_quotes(page: str, repo: Path, commit: str | None = None) -> list[str]:
    """Compare every quote with the file it names. `commit` reads the file from git."""
    problems: list[str] = []
    for attrs, inner in QUOTE_BLOCK.findall(page):
        file, lines = attribute(attrs, "data-file"), attribute(attrs, "data-lines")
        if file is None and lines is None:
            continue  # an example or a fix, not a quote
        where = f"Quote from {file} lines {lines}"
        span_of_lines = LINE_RANGE.fullmatch(lines or "")
        if not file or not span_of_lines:
            problems.append(f'{where}: data-file and data-lines must both be set, and data-lines must look like 44-48.')
            continue
        if Path(file).is_absolute() or ".." in Path(file).parts:
            problems.append(f"{where}: the path points outside the repository. Use the path from the repository root.")
            continue
        if SECRET_FILE.search(file):
            problems.append(f"{where}: this looks like a secret file. Never quote it. Name the file and the setting only.")
            continue
        source = read_source(repo, file, commit)
        if source is None:
            problems.append(f"{where}: the file cannot be read{' at commit ' + commit if commit else ''}.")
            continue
        first = int(span_of_lines.group(1))
        last = int(span_of_lines.group(2) or first)
        quoted = html.unescape(re.sub(r"<[^>]+>", "", inner)).split("\n")
        problems += compare_quote(where, quoted, source, first, last)
    return problems


def attribute(attrs: str, name: str) -> str | None:
    found = re.search(rf'\b{name}="([^"]*)"', attrs)
    return found.group(1) if found else None


def read_source(repo: Path, file: str, commit: str | None) -> list[str] | None:
    if commit:
        shown = subprocess.run(
            ["git", "-C", str(repo), "show", f"{commit}:{file}"], capture_output=True, text=True, check=False
        )
        return shown.stdout.split("\n") if shown.returncode == 0 else None
    try:
        return (repo / file).read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return None


def squeeze(line: str) -> str:
    return " ".join(line.split())


def compare_quote(where: str, quoted: list[str], source: list[str], first: int, last: int) -> list[str]:
    """Every quoted line must stand in the named range, in the order of the file."""
    problems = []
    file_lines = [squeeze(line) for line in source]
    position = first - 1
    for raw in quoted:
        line = squeeze(NOTE_AT_LINE_END.sub("", raw))
        if not line or LEFT_OUT.fullmatch(line):
            continue
        try:
            position = file_lines.index(line, position, last) + 1
        except ValueError:
            elsewhere = [number for number, text in enumerate(file_lines, 1) if text == line]
            hint = f"the file has it at line {elsewhere[0]}" if elsewhere else "it is not in the file"
            problems.append(f'{where}: the line "{line}" does not match ({hint}). Quote the real line, and fix the range.')
    return problems


# =============================================================================
# Part 4: diff checks
# =============================================================================

DIFF_BLOCK = re.compile(
    r"<pre\b[^>]*>\s*<code\b[^>]*\blanguage-(?:diff|patch)\b[^>]*>(.*?)</code>\s*</pre>", re.DOTALL
)
FINDING_START = re.compile(r'<details\b[^>]*\bid="(F-\d+)"')
HUNK_HEADER = re.compile(r"^@@.*$", re.MULTILINE)
NUMBERED_HUNK = re.compile(r"@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")


def check_diffs(page: str, repo: Path) -> list[str]:
    """Ask git whether each suggested diff fits the code. Nothing is changed.

    Only a diff whose hunks all carry line numbers is checked. A diff without
    them is a sketch for the reader, and git cannot apply it.
    """
    if not (repo / ".git").exists():
        return []
    problems = []
    for block in DIFF_BLOCK.finditer(page):
        diff = html.unescape(without_colours(block.group(1)))
        hunks = HUNK_HEADER.findall(diff)
        if not hunks or not all(NUMBERED_HUNK.match(hunk) for hunk in hunks):
            continue
        result = subprocess.run(
            ["git", "-C", str(repo), "apply", "--check", "-"],
            input=diff + "\n", capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            findings = FINDING_START.findall(page[: block.start()])
            where = findings[-1] if findings else "the page"
            reason = (result.stderr.strip().splitlines() or ["no message"])[0]
            problems.append(
                f"The diff in {where} does not apply to the code (git says: {reason}). "
                "Repair the lines and the line numbers of the diff, or take the line numbers out of its "
                "@@ lines to mark it as a sketch."
            )
    return problems


# =============================================================================
# Part 5: generated navigation
# =============================================================================
# The writer leaves each element with a data-gen attribute empty. This part
# fills it between two markers, so that a second run replaces the first.

FINDING_SLOTS = ("jump", "facts", "pager")
SLOT_TAG = re.compile(r"""<[A-Za-z][\w-]*\b[^>]*?\sdata-gen=(?:"[^"]*"|'[^']*')[^>]*>(?:<!--gen-->.*?<!--/gen-->)?""", re.DOTALL)
PART_TAG = re.compile(r"""<[A-Za-z][\w-]*\b[^>]*?\sdata-part=(?:"[^"]*"|'[^']*')[^>]*>""")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
GENERATED_PART_ID = re.compile(r'\sid="F-\d+-[a-z]+"')
SEVERITY_LABELS = {severity: severity.capitalize() for severity in SEVERITIES}
PART_LABELS = {
    "context": "Background", "path": "Path", "code": "Code", "explanation": "What is wrong", "reproduce": "Steps",
    "priority": "Priority", "verify": "Verify first", "consequences": "If not fixed", "used": "Past misuse",
    "fix": "Fix", "prevent": "Prevent", "views": "Two views",
}
SECTION_LABELS = (
    ("assessment", "Assessment"), ("themes", "Themes"), ("today", "What to do first"), ("findings", "All findings"),
    ("before-fix", "Before you fix"), ("safe", "Found safe"), ("not-checked", "Not checked"),
    ("rejected", "Rejected"), ("method", "How it was made"), ("basics", "The basics"),
)


def generate(page: str) -> str:
    """Fill every data-gen element and give each part of a finding an id. Running it twice changes nothing."""
    parsed = Page()
    parsed.feed(page)
    parsed.close()
    findings = [finding for finding in parsed.findings if FINDING_ID.fullmatch(finding["id"])]
    targets = part_targets(parsed)

    contents = [slot_content(slot, findings, targets, parsed) for slot in parsed.slots]
    page = replace_outside_comments(SLOT_TAG, page, contents, fill_slot)
    ids = [target for _, _, target in targets]
    return replace_outside_comments(PART_TAG, page, ids, set_part_id)


def part_targets(parsed: Page) -> list[tuple[dict | None, str, str | None]]:
    """For each data-part element: its finding, its part, and the id that the jump bar links to."""
    targets = []
    for tag in parsed.part_tags:
        finding, own_id = tag["finding"], tag["id"]
        if own_id and not GENERATED_PART_ID.fullmatch(f' id="{own_id}"'):
            target = own_id
        elif finding is not None and FINDING_ID.fullmatch(finding["id"]):
            target = f'{finding["id"]}-{tag["part"]}'
        else:
            target = None
        targets.append((finding, tag["part"], target))
    return targets


def outside_comments(pattern: re.Pattern, page: str) -> list[re.Match]:
    comments = [match.span() for match in COMMENT.finditer(page)]
    return [match for match in pattern.finditer(page) if not any(start <= match.start() < end for start, end in comments)]


def unfilled_slots(page: str, parsed: Page) -> list[str]:
    """The script fills nothing when it cannot match every slot or part. Say so."""
    problems = []
    if len(outside_comments(SLOT_TAG, page)) != len(parsed.slots):
        problems.append(
            "The script could not fill the data-gen elements, so the navigation and the pictures are empty. "
            'Write each one as data-gen="name", with quotes, and leave it empty.'
        )
    if len(outside_comments(PART_TAG, page)) != len(parsed.part_tags):
        problems.append(
            "The script could not give the parts of the findings their ids, so the jump bars do not work. "
            'Write each part as data-part="name", with quotes.'
        )
    return problems


def replace_outside_comments(pattern: re.Pattern, page: str, values: list, replace) -> str:
    """Replace the n-th match outside a comment with values[n]. If the counts differ, change nothing."""
    matches = outside_comments(pattern, page)
    if len(matches) != len(values):
        return page
    out, last = [], 0
    for match, value in zip(matches, values):
        out += [page[last:match.start()], replace(match, value)]
        last = match.end()
    return "".join(out) + page[last:]


def fill_slot(match: re.Match, content: str | None) -> str:
    opening = match.group(0).split("<!--gen-->", 1)[0]
    return opening if content is None else f"{opening}<!--gen-->{content}<!--/gen-->"


def set_part_id(match: re.Match, target: str | None) -> str:
    tag = match.group(0)
    if target is None or re.search(rf'\sid="{re.escape(target)}"', tag):
        return tag
    tag = GENERATED_PART_ID.sub("", tag)
    name_end = re.match(r"<[A-Za-z][\w-]*", tag).end()
    return f'{tag[:name_end]} id="{target}"{tag[name_end:]}'


def slot_content(slot: dict, findings: list[dict], targets: list, parsed: Page) -> str | None:
    name, finding = slot["name"], slot["finding"]
    if name == "sevbar":
        return severity_bar(findings)
    if name == "index":
        return finding_index(findings, parsed)
    if name == "count" and slot["appendix"]:
        return entry_count(slot["appendix"])
    if name == "glance":
        return at_a_glance(findings)
    if name == "areas":
        return where_the_problems_are(findings, declared_areas(parsed) or [])
    if name == "chips":
        named = slot["attrs"].get("data-findings") or ""
        return finding_boxes([finding for finding_id in named.split() for finding in findings if finding["id"] == finding_id])
    if finding is None or finding not in findings:
        return None
    if name == "jump":
        links = "".join(
            f'<a href="#{target}">{PART_LABELS[part]}</a>'
            for owner, part, target in targets if owner is finding and target and part in PART_LABELS
        )
        return f'<b>{finding["id"]}</b>{links}'
    if name == "facts":
        return fact_strip(finding)
    if name == "pager":
        position = findings.index(finding)
        before = f'<a href="#{findings[position - 1]["id"]}">&larr; {findings[position - 1]["id"]}</a>' if position else "<span></span>"
        after = (
            f'<a href="#{findings[position + 1]["id"]}">{findings[position + 1]["id"]} &rarr;</a>'
            if position + 1 < len(findings) else "<span></span>"
        )
        return f'{before}<a href="#findings">All findings</a>{after}'
    return None


def by_severity(findings: list[dict]) -> list[tuple[str, list[dict]]]:
    groups = [(severity, [finding for finding in findings if finding["severity"] == severity]) for severity in SEVERITIES]
    return [(severity, members) for severity, members in groups if members]


def severity_bar(findings: list[dict]) -> str:
    return "".join(
        f'<a class="{severity}" href="#{members[0]["id"]}">{len(members)} {SEVERITY_LABELS[severity]}</a>'
        for severity, members in by_severity(findings)
    )


def finding_index(findings: list[dict], parsed: Page) -> str:
    sections = "".join(f'<a href="#{target}">{label}</a>' for target, label in SECTION_LABELS if target in parsed.ids)
    groups = "".join(
        f"<h5>{SEVERITY_LABELS[severity]} &middot; {len(members)}</h5>"
        + "".join(
            f'<a class="{severity}" href="#{finding["id"]}" title="{html.escape(title(finding))}">'
            f'<b>{finding["id"]}</b> {html.escape(title(finding))}</a>'
            for finding in members
        )
        for severity, members in by_severity(findings)
    )
    return f"<div>{sections}</div>{groups}"



# --- the pictures -------------------------------------------------------------
# Each picture is drawn from the labels of the findings, so its numbers always
# match the page. Every mark keeps a text label: colour is never the only sign.


def at_a_glance(findings: list[dict]) -> str:
    groups = by_severity(findings)
    strip = "".join(
        f'<span class="{severity}" style="flex: {len(members)}" title="{SEVERITY_LABELS[severity]}: {len(members)}"></span>'
        for severity, members in groups
    )
    legend = "".join(f'<span class="{severity}">{SEVERITY_LABELS[severity]}<b>{len(members)}</b></span>' for severity, members in groups)
    tiles = (
        (sum("verify" in finding["parts"] for finding in findings), "need a check outside the code first"),
        (sum(len(set((finding["found_by"] or "").split())) >= 2 for finding in findings), "found by two or more models or tools"),
        (sum("views" in finding["parts"] for finding in findings), "where the two models still differ"),
    )
    tile_html = "".join(f'<div class="tile"><b>{count}</b><span>{text}</span></div>' for count, text in tiles)
    label = ", ".join(f"{len(members)} {severity}" for severity, members in groups) or "no findings"
    return (
        f'<div class="strip" role="img" aria-label="{len(findings)} findings: {label}">{strip}</div>'
        f'<div class="legend">{legend}</div><div class="tiles">{tile_html}</div>'
    )


def where_the_problems_are(findings: list[dict], areas: list[str]) -> str:
    rows = [(area, [finding for finding in findings if finding["area"] == area]) for area in areas]
    rows = sorted((row for row in rows if row[1]), key=lambda row: -len(row[1]))  # a stable sort keeps the order of data-areas
    if not rows:
        return '<p class="small">No finding yet.</p>'
    most = max(len(members) for _, members in rows)
    html_rows = []
    for area, members in rows:
        bars = "".join(
            f'<span class="{severity}" style="width: {100 * len(group) / most:.2f}%" '
            f'title="{html.escape(area)}, {SEVERITY_LABELS[severity]}: {len(group)}"></span>'
            for severity, group in by_severity(members)
        )
        html_rows.append(
            f'<div class="arow"><span class="an">{html.escape(area)}</span><span class="ab">{bars}</span>'
            f'<span class="av">{len(members)}</span></div>'
        )
    return "".join(html_rows)


def finding_boxes(findings: list[dict]) -> str:
    return "".join(
        f'<a class="fc {finding["severity"]}" href="#{finding["id"]}" '
        f'title="{finding["id"]}, {SEVERITY_LABELS.get(finding["severity"], "")}: {html.escape(title(finding))}">{finding["id"]}</a>'
        for finding in findings
    )


def fact_strip(finding: dict) -> str:
    def marks(count: int, on: int) -> str:
        return "".join('<i class="on"></i>' if number < on else "<i></i>" for number in range(count))

    confidence = {"high": 3, "medium": 2, "low": 1}.get(finding["confidence"], 0)
    sizes = list(FIX_SIZES)
    size = sizes.index(finding["fix_size"]) + 1 if finding["fix_size"] in FIX_SIZES else 0
    ladder = "".join(
        f'<i class="on">{label}</i>' if level == finding["reach"] else f"<i>{label}</i>"
        for level, label in REACH_LEVELS.items()
    )
    files = len(finding["files"])
    where = f'{html.escape(finding["area"] or "")}, {files} file{"" if files == 1 else "s"}'
    return (
        f'<div><small>Confidence</small><span class="dots">{marks(3, confidence)}</span> {finding["confidence"].capitalize()}</div>'
        f'<div><small>Size of the fix</small><span class="meter">{marks(3, size)}</span>{FIX_SIZES.get(finding["fix_size"], "")}</div>'
        f"<div><small>Where</small>{where}</div>"
        f'<div class="wide"><small>Who can reach it</small><span class="ladder">{ladder}</span>'
        f'{html.escape(finding["reach_label"] or "")}</div>'
    )


def title(finding: dict) -> str:
    return " ".join(finding["title"].split())


def entry_count(appendix: dict) -> str:
    count = appendix["rows"] or appendix["items"]
    return "none" if count == 0 else f"{count} entr{'y' if count == 1 else 'ies'}"



# =============================================================================
# Part 6: SARIF for GitHub code scanning
# =============================================================================
# One result for each finding. GitHub reads the severity score and the
# precision from the rule, so a rule is one CWE at one severity. The file holds
# places and labels, and no line of code.

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SECURITY_SEVERITY = {"critical": "9.5", "high": "8.0", "medium": "5.5", "low": "2.0"}
SARIF_LEVEL = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "note"}
PRECISION_ORDER = ("low", "medium", "high")


def build_sarif(page: str) -> dict:
    parsed = Page()
    parsed.feed(page)
    parsed.close()
    findings = [finding for finding in parsed.findings if FINDING_ID.fullmatch(finding["id"])]

    rules: list[dict] = []
    rule_index: dict[str, int] = {}
    results = []
    for finding in findings:
        cwes = (finding["cwe"] or "").split()
        main_cwe = cwes[0] if cwes else "0"
        rule_id = f"CWE-{main_cwe}-{finding['severity']}"
        if rule_id not in rule_index:
            rule_index[rule_id] = len(rules)
            rules.append(sarif_rule(rule_id, main_cwe, finding["severity"]))
        rule = rules[rule_index[rule_id]]
        rule["properties"]["precision"] = min(
            (rule["properties"].get("precision", "high"), finding["confidence"]),
            key=lambda value: PRECISION_ORDER.index(value) if value in PRECISION_ORDER else 0,
        )
        rule["help"]["markdown"] += f"\n- {finding['id']}: {title(finding)}"
        results.append(sarif_result(finding, rule_id, rule_index[rule_id], cwes))

    for rule in rules:
        rule["help"]["markdown"] += (
            "\n\nThe security-audit report (report.html) explains each finding: the path through the code, "
            "the steps to reproduce it on a test copy, the fix, and a test to write first."
        )
        rule["help"]["text"] = rule["help"]["markdown"].replace("**", "").replace("\n- ", "\n")
    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "security-audit",
                "informationUri": "https://cwe.mitre.org/",
                "rules": rules,
            }},
            "automationDetails": {"id": "security-audit/"},
            "results": results,
        }],
    }


def sarif_rule(rule_id: str, cwe: str, severity: str) -> dict:
    label = SEVERITY_LABELS.get(severity, severity)
    properties: dict = {"tags": ["security", f"external/cwe/cwe-{cwe}"]}
    if severity in SECURITY_SEVERITY:
        properties["security-severity"] = SECURITY_SEVERITY[severity]
    return {
        "id": rule_id,
        "name": f"Cwe{cwe}{label}",
        "shortDescription": {"text": f"CWE-{cwe}, severity {label}"},
        "fullDescription": {"text": f"Findings of the security audit with the main weakness CWE-{cwe} and the severity {label}."},
        "helpUri": f"https://cwe.mitre.org/data/definitions/{cwe}.html",
        "help": {"text": "", "markdown": f"**CWE-{cwe}, severity {label}.** Findings of this audit:\n"},
        "defaultConfiguration": {"level": SARIF_LEVEL.get(severity, "warning")},
        "properties": properties,
    }


def sarif_result(finding: dict, rule_id: str, index: int, cwes: list[str]) -> dict:
    places = [sarif_location(file, lines) for file, lines in finding["places"]]
    places = [place for place in places if place]
    short = " ".join(finding["short"].split()).removeprefix("In short:").strip()
    fingerprint = "|".join([rule_id.rsplit("-", 1)[0], *sorted(finding["files"]), title(finding).lower()])
    result = {
        "ruleId": rule_id,
        "ruleIndex": index,
        "level": SARIF_LEVEL.get(finding["severity"], "warning"),
        "message": {"text": f"{finding['id']}: {title(finding).rstrip('.')}. {short} See {finding['id']} in report.html."},
        "locations": places[:1],
        "partialFingerprints": {"securityAudit/v1": hashlib.sha256(fingerprint.encode()).hexdigest()[:32]},
        "properties": {
            "finding": finding["id"], "severity": finding["severity"], "confidence": finding["confidence"],
            "cwe": [f"CWE-{cwe}" for cwe in cwes], "area": finding["area"], "reach": finding["reach"],
            "reachLabel": finding["reach_label"], "fixSize": finding["fix_size"],
            "foundBy": (finding["found_by"] or "").split(),
            "verifyFirst": "verify" in finding["parts"], "twoViews": "views" in finding["parts"],
        },
    }
    if len(places) > 1:
        result["relatedLocations"] = [
            {"id": number, **place, "message": {"text": "Another place of this finding."}}
            for number, place in enumerate(places[1:], 1)
        ]
    return result


def sarif_location(file: str, lines: str) -> dict | None:
    span_of_lines = LINE_RANGE.fullmatch(lines or "")
    if not span_of_lines or Path(file).is_absolute() or ".." in Path(file).parts:
        return None
    first = int(span_of_lines.group(1))
    return {"physicalLocation": {
        "artifactLocation": {"uri": file, "uriBaseId": "%SRCROOT%"},
        "region": {"startLine": first, "endLine": int(span_of_lines.group(2) or first)},
    }}


# =============================================================================
# The command
# =============================================================================


def finish(args: argparse.Namespace) -> int:
    report = Path(args.report)
    written = report.read_text(encoding="utf-8")
    page = generate(colour_code_blocks(written))
    if not args.check_only and page != written:
        report.write_text(page, encoding="utf-8")

    problems = check_page(page)
    if args.repo:
        problems += check_quotes(page, Path(args.repo), args.commit)
        if not args.commit:  # a diff is checked against the folder as it is
            problems += check_diffs(page, Path(args.repo))
    else:
        print("Note: the code quotes were not checked. Give --repo to check them.")

    sarif_file = report.with_suffix(".sarif")
    if not problems:
        if not args.check_only:
            sarif_file.write_text(json.dumps(build_sarif(page), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"Wrote the findings for GitHub code scanning: {sarif_file}")
        print(f"No problems. The report is ready: {report}")
        return 0
    if not args.check_only and sarif_file.exists():
        sarif_file.unlink()  # an old file would not match the page any more
    print(f"{len(problems)} problem(s) in {report}:")
    for number, problem in enumerate(problems, 1):
        print(f"{number}. {problem}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="action", required=True)
    finish_parser = commands.add_parser("finish", help="colour the code, build the navigation, then check the page")
    finish_parser.add_argument("report")
    finish_parser.add_argument("--repo", help="the audited repository, to check the code quotes against it")
    finish_parser.add_argument("--commit", help="read the quoted files from this commit, not from the folder")
    finish_parser.add_argument("--check-only", action="store_true", help="do not change the file")
    finish_parser.set_defaults(handler=finish)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
