"""Tests for report_tools.py: code colours and checks for a finished report."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

HELPERS = Path(__file__).resolve().parent
TEMPLATE = HELPERS.parent / "references" / "report-template.html"
sys.path.insert(0, str(HELPERS))

import report_tools  # noqa: E402

SOURCE = "def load(email):\n    user = find(email)\n    return user\n"
VALUES = {
    "F_ID": "F-01",
    "F_SEVERITY": "high",
    "F_CONFIDENCE": "high",
    "LANGUAGE": "python",
    "FILE": "app.py",
    "LINES": "2-3",
    "QUOTED_CODE": "user = find(email)   # PROBLEM: searches all users\nreturn user",
    "F_FIX_DIFF": "--- a/app.py\n+++ b/app.py\n@@ -2 +2 @@\n-    user = find(email)\n+    user = find(email, owner)",
    "N_CRITICAL": "0", "N_HIGH": "1", "N_MEDIUM": "0", "N_LOW": "0", "N_INFO": "0",
}
FINDING = re.compile(r'<details class="finding".*?</details>', re.DOTALL)
TRIAGE_ITEM = re.compile(r'<li><a href="#F-\d+">.*?</li>', re.DOTALL)


def filled() -> str:
    """The shipped template with every placeholder filled and every guide removed."""
    text = TEMPLATE.read_text(encoding="utf-8")
    text = re.sub(r"<!-- GUIDE:.*?-->", "", text, flags=re.DOTALL)
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: VALUES.get(m.group(1), "text"), text)


def with_second_finding(text: str, severity: str) -> str:
    """Add finding F-02 with the given severity after F-01, and list it."""
    def clone(block: str) -> str:
        return block.replace("F-01", "F-02").replace('"high"', f'"{severity}"').replace("sev high", f"sev {severity}")

    first = FINDING.search(text).group(0)
    item = TRIAGE_ITEM.search(text).group(0)
    heading = f'<div class="group-head g-{severity}"><h3>text</h3><p>text</p></div>'
    text = text.replace(first, first + "\n" + heading + "\n" + clone(first))
    text = text.replace(item, item + "\n" + clone(item))
    return text.replace(f'data-count="{severity}">0<', f'data-count="{severity}">1<')


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")
    return tmp_path


def code_block(language: str, code: str) -> str:
    return f'<pre><code class="language-{language}">{code}</code></pre>'


# --- code colours ------------------------------------------------------------


def test_python_code_gets_keyword_string_comment_and_number_colours() -> None:
    out = report_tools.colour_code_blocks(code_block("python", "def f():\n    return 'x', 42  # why"))

    assert '<span class="tok-k">def</span>' in out
    assert '<span class="tok-k">return</span>' in out
    assert '<span class="tok-s">\'x\'</span>' in out
    assert '<span class="tok-n">42</span>' in out
    assert '<span class="tok-c"># why</span>' in out


@pytest.mark.parametrize(
    ("language", "line", "css"),
    [
        ("python", "x = a   # PROBLEM: no owner check", "tok-problem"),
        ("python", "x = a   # OK: id and owner", "tok-ok"),
        ("javascript", "let x = a;   // NEW: escapes the name", "tok-new"),
        ("html", "&lt;p&gt;x&lt;/p&gt;   &lt;!-- PROBLEM: not escaped --&gt;", "tok-problem"),
    ],
)
def test_a_note_comment_gets_its_own_colour(language: str, line: str, css: str) -> None:
    out = report_tools.colour_code_blocks(code_block(language, line))

    assert f'<span class="{css}">' in out


def test_colouring_twice_changes_nothing() -> None:
    once = report_tools.colour_code_blocks(code_block("python", "if a &lt; b:\n    return \"&amp;\"  # PROBLEM: x"))

    assert report_tools.colour_code_blocks(once) == once


def test_escaped_characters_stay_escaped() -> None:
    out = report_tools.colour_code_blocks(code_block("python", "if a &lt; b and c &gt; d:\n    s = '&amp;'"))

    assert "&lt;" in out and "&gt;" in out and "&amp;" in out
    assert not re.search(r"<(?!/?span|/?pre|/?code)", out)


def test_a_comment_sign_inside_a_string_is_not_a_comment() -> None:
    out = report_tools.colour_code_blocks(code_block("javascript", 'const url = "http://x/#a";  // real'))

    assert '<span class="tok-s">"http://x/#a"</span>' in out
    assert '<span class="tok-c">// real</span>' in out


def test_html_code_gets_tag_and_attribute_colours() -> None:
    out = report_tools.colour_code_blocks(code_block("html", '&lt;a href="/x"&gt;go&lt;/a&gt; {{ name }}'))

    assert '<span class="tok-t">&lt;a</span>' in out
    assert '<span class="tok-s">"/x"</span>' in out
    assert '<span class="tok-k">{{ name }}</span>' in out


def test_a_diff_gets_one_class_for_each_line() -> None:
    out = report_tools.colour_code_blocks(code_block("diff", VALUES["F_FIX_DIFF"]))

    assert '<span class="diff-line file">--- a/app.py</span>' in out
    assert '<span class="diff-line hunk">@@ -2 +2 @@</span>' in out
    assert '<span class="diff-line del">-    user = find(email)</span>' in out
    assert '<span class="diff-line add">+    user = find(email, owner)</span>' in out
    assert "\n" not in re.search(r"<code[^>]*>(.*)</code>", out, re.DOTALL).group(1)


@pytest.mark.parametrize("language", ["sql", "shell", "json", "yaml", "go", "java", "php", "ruby", "rust", "css"])
def test_other_languages_colour_without_losing_text(language: str) -> None:
    code = 'select "a" from t where x = 1 -- note\n# c\n{"k": true}\nkey: value\nfunc main() { return }'

    out = report_tools.colour_code_blocks(code_block(language, code))

    assert re.sub(r"<[^>]+>", "", out) == code
    assert "tok-" in out


def test_an_unknown_language_is_left_alone() -> None:
    block = code_block("brainfudge", "+++ &lt;x&gt;")

    assert report_tools.colour_code_blocks(block) == block


# --- page checks -------------------------------------------------------------


def test_the_filled_template_passes_every_check(repo: Path) -> None:
    text = report_tools.colour_code_blocks(filled())

    assert report_tools.check_page(text) == []
    assert report_tools.check_quotes(text, repo) == []


def test_the_empty_template_fails_only_on_placeholders_and_guide_comments() -> None:
    problems = report_tools.check_page(TEMPLATE.read_text(encoding="utf-8"))

    assert problems
    kinds = {"placeholder", "GUIDE comment", "F-NN", "data-severity", "data-confidence", "group heading"}
    for problem in problems:
        assert any(kind in problem for kind in kinds), problem


def test_a_report_with_no_finding_is_valid() -> None:
    text = FINDING.sub("", filled())
    text = TRIAGE_ITEM.sub("", text).replace('data-count="high">1<', 'data-count="high">0<')
    text = re.sub(r'<div class="group-head.*?</div>', "", text, flags=re.DOTALL)

    assert report_tools.check_page(text) == []


def test_two_findings_in_order_of_severity_pass() -> None:
    assert report_tools.check_page(with_second_finding(filled(), "low")) == []


BROKEN = [
    ("a script", lambda t: t.replace("</main>", "<script>alert(1)</script></main>"), "<script>"),
    ("an event handler", lambda t: t.replace('<p class="foot">', '<p class="foot" onclick="x()">'), "event handler"),
    ("a javascript link", lambda t: t.replace('href="#assessment"', 'href="javascript:void(0)"'), "javascript:"),
    ("an outside image", lambda t: t.replace("</main>", '<img src="https://example.com/a.png" alt=""></main>'), "outside resource"),
    ("an outside style sheet", lambda t: t.replace("</head>", '<link rel="stylesheet" href="https://example.com/a.css"></head>'), "outside resource"),
    ("an imported style sheet", lambda t: t.replace("<style>", "<style>@import url(https://example.com/a.css);"), "outside resource"),
    ("an iframe", lambda t: t.replace("</main>", '<iframe src="x.html"></iframe></main>'), "<iframe>"),
    ("a broken link", lambda t: t.replace('href="#basics"', 'href="#nowhere"'), "#nowhere"),
    ("a double id", lambda t: t.replace('<section id="safe">', '<section id="rejected">'), "more than once"),
    ("no viewport", lambda t: t.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', ""), "viewport"),
    ("a missing section", lambda t: t.replace('<section id="rejected">', "<section>"), '"rejected"'),
    ("a missing part", lambda t: t.replace(' data-part="reproduce"', ""), "reproduce"),
    ("a wrong severity", lambda t: t.replace('data-severity="high"', 'data-severity="urgent"'), "data-severity"),
    ("a wrong confidence", lambda t: t.replace('data-confidence="high"', 'data-confidence="sure"'), "data-confidence"),
    ("a wrong id", lambda t: t.replace("F-01", "finding-one"), "F-NN"),
    ("a label that differs", lambda t: FINDING.sub(lambda m: m.group(0).replace("sev high", "sev low"), t), "label"),
    ("a wrong count", lambda t: t.replace('data-count="high">1<', 'data-count="high">3<'), "count"),
    ("a finding that is not in the list", lambda t: TRIAGE_ITEM.sub("", t), "list"),
    ("no quote", lambda t: t.replace(' data-file="app.py" data-lines="2-3"', ""), "quote"),
    ("a tag inside code", lambda t: t.replace("return user</code>", "<b>return</b> user</code>"), "inside a code block"),
    ("code with no language", lambda t: t.replace('<code class="language-diff">', "<code>"), "language"),
    ("no group heading", lambda t: re.sub(r'<div class="group-head.*?</div>', "", t, flags=re.DOTALL), "group heading"),
]


@pytest.mark.parametrize(("name", "breaker", "message"), BROKEN, ids=[case[0] for case in BROKEN])
def test_a_broken_page_is_reported(name: str, breaker, message: str) -> None:
    good = filled()
    broken = breaker(good)
    assert broken != good, "the test did not change the page"

    problems = report_tools.check_page(broken)

    assert any(message in problem for problem in problems), problems


def test_parts_in_the_wrong_order_are_reported() -> None:
    text = filled()
    fix = re.search(r'<section data-part="fix">.*?</section>', text, re.DOTALL).group(0)
    prevent = re.search(r'<section data-part="prevent">.*?</section>', text, re.DOTALL).group(0)
    swapped = text.replace(fix, "@@").replace(prevent, fix).replace("@@", prevent)

    assert any("order" in problem for problem in report_tools.check_page(swapped))


def test_findings_out_of_severity_order_are_reported() -> None:
    text = with_second_finding(filled(), "critical")  # F-02 critical stands after F-01 high

    assert any("order of severity" in problem for problem in report_tools.check_page(text))


def test_a_list_in_another_order_than_the_findings_is_reported() -> None:
    text = with_second_finding(filled(), "low")
    items = TRIAGE_ITEM.findall(text)
    text = text.replace(items[0], "@@").replace(items[1], items[0]).replace("@@", items[1])

    assert any("list" in problem for problem in report_tools.check_page(text))


# --- quote checks ------------------------------------------------------------


def quote(lines: str, code: str, file: str = "app.py") -> str:
    return f'<pre class="quote" data-file="{file}" data-lines="{lines}"><code class="language-python">{code}</code></pre>'


def test_a_quote_with_notes_and_left_out_lines_matches(repo: Path) -> None:
    code = "def load(email):   # OK: the name is fine\n    ...\n    return user   # PROBLEM: no check"

    assert report_tools.check_quotes(quote("1-3", code), repo) == []


def test_a_changed_line_is_reported(repo: Path) -> None:
    problems = report_tools.check_quotes(quote("2-3", "user = find(email, owner)"), repo)

    assert len(problems) == 1
    assert "app.py" in problems[0] and "find(email, owner)" in problems[0]


def test_a_wrong_line_range_says_where_the_line_is(repo: Path) -> None:
    problems = report_tools.check_quotes(quote("1-1", "return user"), repo)

    assert "line 3" in problems[0]


def test_quoted_lines_must_keep_the_order_of_the_file(repo: Path) -> None:
    assert report_tools.check_quotes(quote("1-3", "return user\nuser = find(email)"), repo)


@pytest.mark.parametrize(
    ("file", "message"),
    [("missing.py", "cannot be read"), ("../app.py", "outside"), (".env", "secret"), ("keys/server.pem", "secret")],
)
def test_a_quote_from_a_bad_path_is_reported(repo: Path, file: str, message: str) -> None:
    (repo / ".env").write_text("KEY=1\n", encoding="utf-8")

    problems = report_tools.check_quotes(quote("1-1", "KEY=1", file), repo)

    assert message in problems[0]


def test_a_bad_line_range_is_reported(repo: Path) -> None:
    assert "data-lines" in report_tools.check_quotes(quote("two", "x"), repo)[0]


def test_quotes_can_be_checked_against_a_commit(repo: Path) -> None:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
            cwd=repo, check=True, capture_output=True, text=True,
        ).stdout.strip()

    git("init", "-q")
    git("add", "app.py")
    git("commit", "-q", "-m", "first")
    commit = git("rev-parse", "HEAD")
    (repo / "app.py").write_text("def load(email):\n    return None\n", encoding="utf-8")
    old_line = quote("2-2", "user = find(email)")

    assert report_tools.check_quotes(old_line, repo, commit) == []
    assert report_tools.check_quotes(old_line, repo) != []


# --- the command -------------------------------------------------------------


def test_finish_colours_the_file_and_passes(repo: Path, capsys) -> None:
    report = repo / "report.html"
    report.write_text(filled(), encoding="utf-8")

    code = report_tools.main(["finish", str(report), "--repo", str(repo)])

    assert code == 0
    assert "tok-problem" in report.read_text(encoding="utf-8")
    assert "No problems" in capsys.readouterr().out


def test_finish_lists_the_problems_and_fails(repo: Path, capsys) -> None:
    report = repo / "report.html"
    report.write_text(filled().replace("return user</code>", "return nobody</code>"), encoding="utf-8")

    code = report_tools.main(["finish", str(report), "--repo", str(repo)])

    assert code == 1
    assert "return nobody" in capsys.readouterr().out


def test_check_only_does_not_change_the_file(repo: Path) -> None:
    report = repo / "report.html"
    report.write_text(filled(), encoding="utf-8")

    report_tools.main(["finish", str(report), "--check-only"])

    assert report.read_text(encoding="utf-8") == filled()


# --- diff checks -------------------------------------------------------------
# First live run, 2026-11-21: the reviewer ran `git apply --check` on the
# diffs by hand, and one diff of the report did not apply.


@pytest.fixture
def git_repo(repo: Path) -> Path:
    for args in (["init", "-q"], ["add", "app.py"],
                 ["-c", "commit.gpgsign=false", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "first"]):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
    return repo


def finding_with_diff(diff: str) -> str:
    return f'<details class="finding" id="F-03"><pre><code class="language-diff">{diff}</code></pre></details>'


GOOD_DIFF = """--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
 def load(email):
-    user = find(email)
+    user = find(email, owner)
     return user"""


def test_a_diff_with_line_numbers_that_applies_passes(git_repo: Path) -> None:
    page = report_tools.colour_code_blocks(finding_with_diff(GOOD_DIFF))

    assert report_tools.check_diffs(page, git_repo) == []
    assert (git_repo / "app.py").read_text(encoding="utf-8") == SOURCE  # the check changes no file


def test_a_diff_with_line_numbers_that_does_not_apply_is_reported(git_repo: Path) -> None:
    wrong = GOOD_DIFF.replace("-    user = find(email)", "-    user = lookup(email)")

    problems = report_tools.check_diffs(finding_with_diff(wrong), git_repo)

    assert len(problems) == 1
    assert "F-03" in problems[0] and "does not apply" in problems[0]


def test_a_diff_without_line_numbers_is_a_sketch_and_is_not_checked(git_repo: Path) -> None:
    sketch = "--- a/app.py\n+++ b/app.py\n@@ def load\n-    user = find(email)\n+    user = find(email, owner)"

    assert report_tools.check_diffs(finding_with_diff(sketch), git_repo) == []


def test_diffs_are_not_checked_outside_a_git_repository(repo: Path) -> None:
    wrong = GOOD_DIFF.replace("-    user = find(email)", "-    user = lookup(email)")

    assert report_tools.check_diffs(finding_with_diff(wrong), repo) == []


def test_finish_reports_a_diff_that_does_not_apply(git_repo: Path, capsys) -> None:
    report = git_repo / "report.html"
    bad = filled().replace("-    user = find(email)", "-    user = lookup(email)").replace("@@ -2 +2 @@", "@@ -2,1 +2,1 @@")
    report.write_text(bad, encoding="utf-8")

    code = report_tools.main(["finish", str(report), "--repo", str(git_repo)])

    assert code == 1
    assert "does not apply" in capsys.readouterr().out

