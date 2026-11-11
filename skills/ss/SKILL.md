---
name: ss
description: "Use when the user invokes /ss to grab recent screenshots from a configured folder, analyze visual content, and act on them — explaining, fixing errors, creating outputs, or routing to sibling skills based on the user's intent."
---

# Screenshot Skill

Let the user talk to you with screenshots. Grab the newest screenshots from the configured folder, read them, work out what the user wants, and either do it or suggest a sibling skill.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`.

## Rules

- **Do not invent unclear content.** If an image is blurry, cut off, or too small to read, say so.
- **Warn before saving secrets seen in a screenshot.** Passwords, API keys, and tokens must not go into files or commits without the user's go-ahead.
- **Confirm before modifying.** Read-only work (explain, describe, compare) happens right away. Before you change code, files, or designs, state what you would do and wait for a yes.
- **Suggest sibling skills; never chain silently.** The user decides whether to hand off. `/ss huh` does not start `/explain` on its own.

## Invocation

```
/ss [count] [action...]
```

If the first word after `/ss` is a positive integer, it is the count (default 1). Everything after it is the action.

| Invocation | Meaning |
|---|---|
| `/ss` | Latest screenshot; guess the intent from context |
| `/ss huh` | Latest screenshot; explain it |
| `/ss 2 fix` | Two latest; cross-check the errors, then fix |
| `/ss 3 make infographic plz` | Three latest; use them as input for a new output |

Read `.claude/skill-context/preferences.md` if present and let it set the detail level and how much to explain.

## Screenshot Folder

The folder path lives in `.claude/skill-context/ss.md`:

```markdown
## Screenshot Skill Config
- **Screenshot folder:** <path>
```

Use the saved path without asking. If no folder is configured, or the saved folder no longer exists, ask the user once for the path, check that it exists, and save it to `ss.md` (create `.claude/skill-context/` if needed).

## Finding the Screenshots

- **Images (read and analyze):** `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.webp`
- **Videos (list only):** `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`

Take the newest *N* files by modification time.

- No files: ask whether the user saved them somewhere else.
- Fewer files than requested: use what is there and say how many you found.
- In a batch, if one file is clearly older than the rest, ask whether to include it.
- Videos: list them and say that video analysis is not supported. If every file is a video, offer to look further back for images.
- If an image cannot be read, name the file and the reason, and continue with the rest. If none can be read, say so and suggest checking file permissions or format.

## Acting on the Request

Combine the action text, the screenshot content, and the conversation so far.

- **No action given:** infer the intent. Mid-debugging usually means "fix this error"; mid-design usually means "give feedback on this layout"; with no context, describe what you see. If the best guess is read-only, do it. Confirm only before changing things.
- **Action given:** read it naturally. `huh` or `explain` means explain now. `fix` means find the error, propose the change, and apply it after the user agrees. `do this` means learn from the screenshot and adapt the project after confirming.
- **Ambiguous action:** offer 2-3 readings and let the user pick.

When a sibling skill fits better, suggest it from the current skill list instead of a memorized roster. For example, a screenshot of changes ready to commit fits `/commit`, and this project's code or UI fits a review skill.

## Output

Scale the output to the request. For a batch, first list the files you loaded (name, age, image or video), then the analysis, then what you will do or the question you need answered.
