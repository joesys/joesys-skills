#!/usr/bin/env python3
"""Finish a security-audit report: colour its code blocks and check the page.

    report_tools.py finish REPORT.html [--repo DIR] [--commit SHA] [--check-only]

The report is one HTML file that a model wrote into the report template. This
script does the two jobs that a model does badly by hand:

1. It adds the syntax colours to every code block, at build time, so the page
   needs no script.
2. It checks the page: no script, no outside resource, no broken link, the
   fixed sections, every part of every finding, and, with --repo, that every
   code quote matches the file it names.

The exit code is 0 when the page has no problem, and 1 when it has.
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low", "info")
CONFIDENCES = ("high", "medium", "low")
REQUIRED_PARTS = ("short", "context", "code", "explanation", "reproduce", "priority", "consequences", "fix", "prevent")
OPTIONAL_PARTS = ("verify", "used", "views")
REQUIRED_SECTIONS = (
    "read-first", "assessment", "themes", "today", "triage", "findings",
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
        self.triage_links: list[str] = []
        self.counts: dict[str, str] = {}
        self.group_heads: set[str] = set()
        self.has_viewport = self.has_charset = self.has_lang = False
        self.title = ""
        self.style = ""
        self._details: list[dict | None] = []  # one entry for each open <details>
        self._in_summary = False
        self._triage: tuple[str, int] | None = None  # the tag of the list, and its depth
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
            if self._triage:
                self.triage_links.append(attrs["href"][1:])

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

        if self._triage and tag == self._triage[0]:
            self._triage = (tag, self._triage[1] + 1)
        if attrs.get("id") == "triage":
            self._triage = (tag, 1)

        if tag == "details":
            finding = None
            if "finding" in classes:
                finding = {
                    "id": attrs.get("id", ""), "severity": attrs.get("data-severity", ""),
                    "confidence": attrs.get("data-confidence", ""), "parts": [], "label": None,
                    "quotes": 0, "line": line,
                }
                self.findings.append(finding)
            self._details.append(finding)
        finding = self._finding()
        if finding is None:
            return
        if tag == "summary":
            self._in_summary = True
        if self._in_summary and "sev" in classes and finding["label"] is None:
            finding["label"] = " ".join(name for name in classes if name != "sev")
        if "data-part" in attrs:
            finding["parts"].append(attrs["data-part"])
        if tag == "pre" and attrs.get("data-file") and attrs.get("data-lines"):
            finding["quotes"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "details" and self._details:
            self._details.pop()
        if tag == "summary":
            self._in_summary = False
        if self._triage and tag == self._triage[0]:
            depth = self._triage[1] - 1
            self._triage = (tag, depth) if depth else None
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

    # --- helpers ---

    def _finding(self) -> dict | None:
        return next((finding for finding in reversed(self._details) if finding), None)

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

    found = [finding["id"] for finding in parsed.findings]
    if parsed.triage_links != found:
        problems.append(
            f'The list of all findings (id "triage") does not match the findings. '
            f"The list has: {', '.join(parsed.triage_links) or 'nothing'}. The findings are: {', '.join(found) or 'none'}."
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
# The command
# =============================================================================


def finish(args: argparse.Namespace) -> int:
    report = Path(args.report)
    page = report.read_text(encoding="utf-8")
    if not args.check_only:
        coloured = colour_code_blocks(page)
        if coloured != page:
            report.write_text(coloured, encoding="utf-8")
            page = coloured

    problems = check_page(page)
    if args.repo:
        problems += check_quotes(page, Path(args.repo), args.commit)
    else:
        print("Note: the code quotes were not checked. Give --repo to check them.")

    if not problems:
        print(f"No problems. The report is ready: {report}")
        return 0
    print(f"{len(problems)} problem(s) in {report}:")
    for number, problem in enumerate(problems, 1):
        print(f"{number}. {problem}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="action", required=True)
    finish_parser = commands.add_parser("finish", help="colour the code blocks, then check the page")
    finish_parser.add_argument("report")
    finish_parser.add_argument("--repo", help="the audited repository, to check the code quotes against it")
    finish_parser.add_argument("--commit", help="read the quoted files from this commit, not from the folder")
    finish_parser.add_argument("--check-only", action="store_true", help="do not change the file")
    finish_parser.set_defaults(handler=finish)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
