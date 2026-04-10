---
name: ss
version: "1.0.0"
description: "Use when the user invokes /ss to grab recent screenshots from a configured folder, analyze their visual content, and act on them — explaining, fixing errors, creating outputs, or routing to sibling skills based on the user's intent."
---

# Screenshot Skill

Visual communication bridge — the primary way the user speaks to Claude visually. Grabs recent screenshots from a configured folder, analyzes their content, interprets what the user wants, and either acts directly or suggests a sibling skill.

## Invocation

Parse the user's `/ss` arguments to determine screenshot count and action:

```
/ss [count] [action...]
```

**Parsing rule:** If the first token after `ss` is a positive integer, it's the count. Everything after the count (or after `ss` if no count) is the action string.

| Invocation | Count | Action | Behavior |
|---|---|---|---|
| `/ss` | 1 | *(none)* | Grab latest, analyze, guess intent from context |
| `/ss 4` | 4 | *(none)* | Grab 4 latest, analyze, guess intent |
| `/ss huh` | 1 | `huh` | Grab latest, explain content |
| `/ss 3 make infographic plz` | 3 | `make infographic plz` | Grab 3 latest, create infographic |
| `/ss fix` | 1 | `fix` | Grab latest, identify error, fix code |
| `/ss do this` | 1 | `do this` | Grab latest, learn from it, adapt for user |
| `/ss 2 fix` | 2 | `fix` | Grab 2 latest, cross-reference errors, fix |

## User Preferences

Read `shared/skill-context.md` for the full protocol. In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, proceed with defaults (don't interrupt the workflow).
2. Read `.claude/skill-context/ss.md` for the screenshot folder path (see Configuration Bootstrap below).

**How preferences shape this skill:**

| Preference | Effect on Screenshot Skill |
|---|---|
| Detail level: concise | Shorter analysis, skip the screenshots-loaded table for single images |
| Detail level: detailed | Richer description, note composition and visual details |
| Assumed knowledge: beginner | Explain error messages and technical content in the screenshots more thoroughly |
| Assumed knowledge: expert | Focus on the actionable content, skip obvious descriptions |

Like commit and export, `/ss` is a **silent defaults** skill. It never invokes `/preferences` on first contact — screenshots are fast, transactional operations.

## Phase 1: Configuration Bootstrap

### 1.1 Check for Screenshot Folder

1. Read `.claude/skill-context/ss.md` in the current project.
   - **If found:** Extract the screenshot folder path. Verify the folder still exists.
     - If the folder no longer exists, tell the user and re-prompt for a new path.
   - **If missing:** Go to step 2.

2. Check the user's global auto-memory for a previously saved screenshot folder path.
   - Search the memory directory for a file about the screenshot folder path (e.g., `reference_screenshot_folder.md`).
   - **If found in memory:** Offer it as the default:
     > "Last time you used `<path>`. Use the same folder? (Y/n)"
   - **If the user confirms:** Use that path and proceed to step 3.
   - **If the user declines or no memory found:** Ask:
     > "Where do you store your screenshots? (full path)"

3. Validate the folder exists using the Bash tool (`ls "<path>"`). If invalid, tell the user and re-prompt.

4. Write the path to `.claude/skill-context/ss.md`:
   ```markdown
   ## Screenshot Skill Config
   - **Screenshot folder:** <path>
   ```

5. Save the path to the user's global auto-memory as a reference memory (e.g., `reference_screenshot_folder.md`) so future projects can pre-populate. If a memory file already exists for the screenshot folder, update it.

### 1.2 Subsequent Runs

On subsequent invocations, read `.claude/skill-context/ss.md` and verify the folder exists. If the folder is gone, re-prompt for a new path (re-enter the bootstrap flow at the global-memory check in step 2 above).

## Phase 2: File Discovery & Selection

### 2.1 Supported File Types

- **Images (analyzable):** `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.webp`
- **Videos (listed only):** `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`

### 2.2 List and Sort Files

Use the Bash tool to list all matching files sorted by modification time, newest first. Adapt the command to the platform — for example:

```bash
ls -1t "<screenshot_folder>"/*.{png,jpg,jpeg,bmp,gif,webp,mp4,mov,mkv,avi,webm} 2>/dev/null
```

On Windows, PowerShell may be more reliable:

```powershell
Get-ChildItem "<screenshot_folder>" -Include *.png,*.jpg,*.jpeg,*.bmp,*.gif,*.webp,*.mp4,*.mov,*.mkv,*.avi,*.webm | Sort-Object LastWriteTime -Descending
```

If no files are found:
> "No screenshots found in `<path>`. Did you save to a different location?"

### 2.3 Select Top N Files

Take the top *N* files from the sorted list, where N is the count argument (default 1).

If fewer files exist than requested, grab all available and note:
> "Found 2 screenshots (you requested 4)."

### 2.4 Time-Outlier Check (Batches Only)

Only when N > 1: Use the Bash tool to get modification timestamps for all selected files. Compare the age of each file. If any file is **more than 1 hour older** than the next-newest file in the batch, flag it:

> "Note: 2 screenshots are from ~1 hour ago, but `old_screenshot.png` is from 12 days ago. Include it?"

Wait for the user's response before proceeding. If they say no, drop the outlier and continue with the remaining files.

### 2.5 Read Images

For each selected file:
- **Image files:** Read using the Read tool. Claude will see and analyze the image visually.
  - If an image file fails to read, **tell the user** which file failed and why (if possible), then continue with the remaining files.
- **Video files:** Do NOT attempt to read. Instead, note in the output:
  > "Video file detected (`recording.mp4`, 3 min ago) — visual analysis not yet supported for video."

### Edge Cases

| Condition | Action |
|---|---|
| Screenshot folder doesn't exist | Re-prompt for path (Phase 1) |
| No files found | "No screenshots found in `<path>`. Did you save to a different location?" |
| Image file can't be read | Tell the user which file failed and why, continue with remaining |
| Fewer files than requested | Grab all available, note the shortfall |
| All requested files are videos | "All N recent files are videos. Video analysis isn't supported yet. Want me to look further back for images?" |

## Phase 3: Action Interpretation & Dispatch

### 3.1 Analyze Screenshot Content

After reading all images, analyze what's visible in each screenshot. This is the foundation for everything that follows.

### 3.2 Determine Action

Combine the action string (if provided) + screenshot content + conversation context to determine intent.

**If no action was provided (bare `/ss` or `/ss N`):**
1. Use conversation context to infer intent:
   - Mid-debugging → likely wants to fix an error
   - Mid-design → likely wants feedback on a layout
   - Cold start with no context → describe what's visible
2. Present your analysis and best guess:
   > "I see [description]. Based on [context], I think you want [guess]. Does that sound right?"
3. Wait for confirmation before acting.

**If an action was provided:**
Interpret the action using natural reasoning, guided by these common patterns:

| Action | Intent | Behavior |
|---|---|---|
| `huh` / `explain` / `what is this` | Explain what's in the screenshot | Act immediately — describe and explain |
| `fix` | Identify error/bug, fix it | Confirm understanding, then fix |
| `do this` | Learn from screenshot, adapt for user | Confirm understanding, then adapt |
| `review` / `review this` | Code visible → review it | Confirm, then review (may suggest skill) |
| `make infographic` / `export` | Create visual output from content | Act on the request |
| `commit` | Screenshot shows changes to commit | Confirm, then proceed |
| *(anything else)* | Freeform — interpret naturally | Use judgment on read-only vs. modify |

### 3.3 Read-Only vs. Modify Decision

- **Read-only actions** (explain, describe, compare): Act immediately, no confirmation needed.
- **Modify actions** (fix code, create something, change design): Always confirm understanding before proceeding:
  > "I see [description of what's in the screenshot]. Here's what I'd do: [proposed action]. Proceed?"

### 3.4 Skill Routing

When a sibling skill is a natural fit for the task, **suggest it** — never auto-invoke:

> "This looks like a code error. Want me to run `/systematic-debugging` on this, or just fix it directly?"

The user always decides whether to chain. Never silently hand off to another skill.

**Available skills in this plugin:**
- `/code-review` — deep code review (correctness, security, architecture)
- `/quick-review` — fast bug-focused review (P0-P2 only)
- `/readability-review` — story-readability grading (8 dimensions)
- `/explain` — layered codebase/symbol explanation
- `/export` — convert files to PDF/HTML/PNG
- `/commit` — conventional commit with structured body
- `/codebase-audit` — full codebase quality audit
- `/devlog` — capture development insights
- `/ai-council` — consult 3 AI models in parallel
- `/retrospective` — structured retrospective with action items

**Available superpowers skills:**
- `superpowers:systematic-debugging` — structured debugging workflow
- `superpowers:brainstorming` — explore ideas before implementation

## Output Format

Scale the output to the complexity of the request:

### Multi-Screenshot Batch (N > 1)

```
## Screenshots Loaded

| # | File | Age | Type |
|---|------|-----|------|
| 1 | screenshot_2026-04-10_14-23.png | 2 min ago | Image ✓ |
| 2 | recording_2026-04-10_14-20.mp4 | 5 min ago | Video ⏸ |

[Time-outlier warning, if applicable]

## Analysis

[Description of what's in each screenshot]

## Intent

[Context-aware interpretation + action or confirmation prompt]
```

### Single Screenshot + Clear Action

Collapse to minimal output — no table when there's one image and the intent is obvious. Jump straight to analysis and action.

### Bare `/ss` (No Action)

Show analysis, then present your best guess and ask for confirmation.

## Guardrails

1. **Never act destructively without confirmation** — `fix` always confirms understanding before editing code.
2. **Never fabricate screenshot content** — if the image is unclear or unreadable, say so.
3. **Always confirm before invoking a sibling skill** — suggest, don't auto-chain.
4. **Video files are listed but not analyzed** — until video support arrives.
5. **Respect conversation context** — mid-conversation, lean on what you already know; cold start, be more exploratory.
6. **Don't over-chain skills** — only suggest a sibling skill when it's clearly the right tool. `/ss huh` doesn't need `/explain`.
7. **Sensitive content** — if a screenshot contains passwords, API keys, or other secrets visible in the image, warn the user before proceeding with any action that would write that content to files or commits.
8. **Failed reads are reported** — if an image can't be read, tell the user which file failed and why, then continue with remaining files.

## Error Handling

| Condition | Action |
|---|---|
| Screenshot folder doesn't exist | Re-prompt for path |
| No files found | Ask if user saved to a different location |
| Image file can't be read | Report the failure, continue with remaining files |
| Count exceeds available files | Grab all available, note the shortfall |
| Action is ambiguous | Present 2-3 interpretations, ask user to pick |
| Video file encountered | List it, note video analysis is unsupported, continue |

## Graceful Degradation

| Scenario | Fallback |
|---|---|
| No skill-context directory exists | Create it during bootstrap |
| Global memory unavailable | Ask for screenshot folder from scratch |
| All images fail to read | Report all failures, suggest checking file permissions or format |
| Screenshot folder is empty | Ask if user saved to a different location |
| User provides ambiguous action | Present interpretations, ask for clarification |
