---
name: export
description: "Use when the user invokes /export to convert markdown, text, or code files into polished PDF, HTML, or PNG with proper typography, syntax highlighting, and responsive layout."
---

# Export Skill

Convert markdown, text, and code files into polished, shareable formats. Supports three output formats (PDF, HTML, PNG), three content scopes (full, summary, 1pager), and three CSS themes (minimal, modern, dark).

## Invocation

Parse the user's `/export` arguments to determine input file and options:

| Invocation | Behavior |
|---|---|
| `/export <file>` | Full file → PDF, portrait, minimal theme |
| `/export <file> --format html\|pdf\|png\|all` | Specify output format |
| `/export <file> --scope full\|summary\|1pager` | Content scope |
| `/export <file> --orientation portrait\|landscape` | Page orientation |
| `/export <file> --theme minimal\|modern\|dark` | CSS theme |
| `/export <file> --output <path>` | Custom output path |

Arguments are combinable. Examples:
- `/export report.md --format png --theme dark` — full PNG with dark theme
- `/export report.md --scope summary --format all` — summary in all 3 formats
- `/export utils.py --format html --theme dark` — syntax-highlighted code export

### Defaults

| Option | Default |
|---|---|
| `--format` | `pdf` |
| `--scope` | `full` |
| `--orientation` | `portrait` |
| `--theme` | `minimal` |

If the invocation is ambiguous or the file path is unrecognizable, ask the user to clarify before proceeding.

## Process

### Step 1 — Validate Input

1. Confirm the input file exists. If not, ask the user for the correct path.
2. Parse all flags from the invocation.
3. If `--output` is used with `--format all`, warn the user that `--output` only works with a single format and ask them to choose.

### Step 2 — Content Preparation

Based on `--scope`:

**`full` (default):** No content modification. Pass the file directly to the rendering script.

**`summary`:** Read the input file and generate a condensed markdown summary:
- Extract and preserve the document title (first H1 or filename).
- Identify key sections, findings, and conclusions.
- Produce a focused summary — typically 30-50% of the original length.
- Preserve code blocks, tables, and other structured elements that are central to the document's message.
- Write the condensed markdown to a temporary file.

**`1pager`:** Read the input file and condense to approximately one A4 page worth of content (~500-600 words):
- Prioritize the most important information: conclusions, key findings, critical code.
- Use tighter prose — bullet points over paragraphs where appropriate.
- Omit secondary details, verbose explanations, and supporting examples.
- Write the condensed markdown to a temporary file.

For code files (`.py`, `.cpp`, etc.) with `summary` or `1pager` scope: extract the most important functions/classes, add brief descriptions. Do not attempt to summarize every line.

### Step 3 — Render

Invoke the rendering script:

```bash
python scripts/md_export.py <input_or_temp_file> \
  --format <format> \
  --theme <theme> \
  --orientation <orientation> \
  --scope <scope> \
  [--output <path>]
```

The script handles:
1. Input type detection (markdown, text, code)
2. Code file wrapping in fenced blocks with syntax highlighting
3. Pandoc conversion to self-contained HTML
4. Headless browser rendering to PDF/PNG (if needed)

### Step 4 — Report Results

After successful rendering, report:
- The output file path(s)
- The file size(s)
- A brief confirmation: "Exported `<file>` as `<format>` with `<theme>` theme."

If `--format all` was used, list all three output files.

If rendering fails, show the error from the script and suggest troubleshooting steps (check Pandoc installation, check browser availability).

### Step 5 — Cleanup

Remove any temporary files created during content preparation (summary/1pager temp markdown files).

## Output Naming Convention

| Scope | Example output |
|---|---|
| `full` | `report.pdf`, `report.html`, `report.png` |
| `summary` | `report-summary.pdf`, `report-summary.html`, `report-summary.png` |
| `1pager` | `report-1pager.pdf`, `report-1pager.html`, `report-1pager.png` |

Output is placed in the same directory as the input file by default. Use `--output` to override.

## Supported Input Types

| Extension | Treatment |
|---|---|
| `.md` | Render as markdown |
| `.txt` | Treat as markdown |
| Known code (`.py`, `.js`, `.ts`, `.cpp`, `.c`, `.rs`, `.go`, `.java`, `.cs`, `.sh`, `.ps1`, `.rb`, `.lua`, `.sql`, `.yaml`, `.json`, `.toml`, `.xml`, `.html`, `.css`) | Syntax-highlighted code with filename heading |
| Unknown extension | Treat as plain text / markdown |

## Themes

| Theme | Description |
|---|---|
| `minimal` (default) | Clean white, bold black headings, no accents. Content-first typography. |
| `modern` | Muted slate accents, structured layout with subtle top border. |
| `dark` | Deep navy background, purple accents. Good for screenshots and screen sharing. |

## Dependencies

The rendering script requires:
- **Pandoc** — for markdown → HTML conversion
- **A Chromium-based browser** (Edge, Chrome) — for HTML → PDF/PNG rendering

If either is missing, the script provides platform-specific install instructions.
