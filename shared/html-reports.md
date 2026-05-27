# HTML Reports — Skill Author Protocol

Skills that produce human-readable reports emit a Markdown artifact and an HTML companion. The HTML rendering happens via `scripts/html_render.py`. This doc is the contract between report-producing skills and the renderer.

## When to call the renderer

Call the renderer **after** writing the canonical Markdown artifact. Never replace the Markdown — it stays the source of truth and is what other skills re-read (`/codebase-audit analysis`, `/devlog` mining).

```python
import subprocess, sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"  # path to plugin scripts/

# 1. Existing skill behavior — write the markdown.
report_path.write_text(report_markdown, encoding="utf-8")

# 2. New step — render HTML companion (best-effort, non-fatal).
try:
    subprocess.run(
        ["python", str(SCRIPTS_DIR / "html_render.py"),
         str(report_path),
         "--profile", "analytical"],
        check=True,
    )
except subprocess.CalledProcessError as e:
    print(f"⚠ HTML render failed (markdown still saved): {e}", file=sys.stderr)
```

The pattern: HTML rendering is **best-effort**. If it fails, the Markdown is still saved — users never lose content.

## Front-matter conventions

Skills can pass metadata to the renderer via YAML front-matter at the head of the markdown file. All keys are optional.

```markdown
---
title: "Authentication Module Analysis"
generated_by: "/explain"
generated_at: "2026-05-09T14:23:11Z"
scope: "src/auth/"
profile: "analytical"
---

# Body...
```

| Key | Used for |
|---|---|
| `title` | `<title>` tag and toolbar header |
| `generated_by` | Toolbar prefix (e.g., "/explain — src/auth/") |
| `generated_at` | Footer "Generated YYYY-MM-DD" line |
| `scope` | Toolbar suffix in `<code>` tags |
| `profile` | Currently informational — `--profile` CLI flag is authoritative |

If `title` is absent, the renderer falls back to the first H1 in the document, then to the filename stem.

## Enrichment blocks (Phase 1)

Phase 1 supports one enrichment block. Phase 2+ will add more.

### `mermaid` — Diagrams (REQUIRED for graphs)

**All diagrams in HTML companion reports MUST use Mermaid.** ASCII box-drawing is not permitted as a graph syntax. Use a fenced code block with the `mermaid` language tag — Mermaid supports flowchart (`graph TD` / `graph LR`), sequence (`sequenceDiagram`), state (`stateDiagram-v2`), class, ER, gantt, and more.

````markdown
```mermaid
graph TD
  A[routes/auth.ts] --> B[middleware/session]
  B --> C[providers/oauth]
```
````

The renderer wraps this in `<pre class="mermaid">`. The Mermaid library (vendored, loaded at page load) turns it into SVG client-side. The block degrades gracefully when the markdown is viewed in a non-rendering tool (just looks like a code block, with readable source).

**Why Mermaid over ASCII:** The HTML companion was always intended to render diagrams as SVG. ASCII box-drawing renders as a `<pre><code>` listing — a code block, not a diagram — defeating the purpose of the HTML view. Mermaid is rendered natively by GitHub, GitLab, VS Code (with the standard preview extension), Obsidian, and most modern markdown viewers. In raw `cat` view, Mermaid source (e.g., `A --> B`) remains legible.

**Tabular data → markdown tables, not ASCII boxes.** A scorecard or summary with rows and columns is not a graph. Use a real markdown table — it renders as a styled HTML table and is more readable in raw markdown than ASCII box-drawing.

**ASCII fallback escape hatch (opt-in, per-report):** Authors MAY wrap an equivalent ASCII version in a collapsible `<details>` block when a specific report is reviewed primarily through tools that don't render Mermaid (terminal-only workflows, custom viewers). This is *not* the default — protocol does not require dual output, and the drift cost is on the author who opts in.

````markdown
```mermaid
graph TD
  A --> B
```

<details>
<summary>ASCII fallback</summary>

```
[A] ──▶ [B]
```

</details>
````

## Opt-out flags

(Phase 1 ships with the renderer behavior controlled at the renderer CLI level. Per-skill `--no-html` flags will be added in each skill's SKILL.md as part of phase rollouts.)

## Output paths

Skills should let the renderer derive the output path automatically. The renderer writes `<input>.html` next to `<input>.md` by default. Override only when there's a specific reason (e.g., centralizing all rendered reports in a different directory).

## Handbook Profile (Portable)

The `handbook` profile produces a **self-contained HTML file** with all CSS and JS inlined. No external assets, no `docs/.assets/report-lib/` dependency.

**Invocation:**
```bash
python scripts/html_render.py <input.md> --profile handbook
```

**How it works:**
1. Reads the template skeleton from `scripts/templates/handbook.html`
2. Reads vendor CSS files (`report-base.css`, `prism-light.css`, `prism-dark.css`) and inlines them into the `/* INLINE_CSS */` placeholder
3. Reads vendor JS files (`prism.min.js`, `mermaid.min.js`, `report-init.js`) and inlines them into the `/* INLINE_JS */` placeholder
4. Renders through Pandoc with the assembled template
5. Output has zero external dependencies

**Differences from `analytical` profile:**
- Does NOT require a git repo (no `find_repo_root`)
- Does NOT bootstrap `docs/.assets/report-lib/`
- Does NOT use `$assets-rel$` template variable
- Output is larger (includes all CSS/JS) but fully portable

**Handbook-specific CSS additions** (in the template skeleton):
- Collapsible `<details>` styling for layered code walkthroughs
- Danger zone callout styling (red-bordered blockquotes)
- TL;DR hero section styling (first blockquote in main content)
- Print styles (hide sidebar, expand all details)

**Front-matter:** Same conventions as analytical. The `profile` field should be `"handbook"`.
