# Skill Preferences

Preferences let a user tune how skills behave in a project. They are optional. Most projects have none, and every skill works well with its defaults.

## How skills use them

Early in the run, read these files if they exist and treat them as guidance, not law:

- `.codex/skill-context/preferences.md` — shared preferences for every skill
- `.codex/skill-context/<skill-name>.md` — preferences for one skill

In Antigravity, check `.agents/skill-context/` first and fall back to the paths above if a project already keeps preferences there.

If a file is missing, use sensible defaults and say nothing about it. Never interview the user about preferences. If the current task needs an answer only the user has (for example, which folder holds screenshots), ask that one question, and offer to save the answer to the skill's file so you do not ask again.

Pass subagents only the preferences that matter to their job. A preference never removes a critical finding: "concise" does not mean "hide the security bug". If a preference clearly contradicts what you see (it says "solo", but git shows 12 contributors), mention it once.

These files are personal. Suggest adding `.codex/skill-context/` (or `.agents/skill-context/` in Antigravity) to `.gitignore` unless the team wants shared preferences.

## File format

Both files are plain, hand-editable markdown. The shared file usually covers:

```markdown
# Skill Preferences

## Communication Style
- **Detail level:** {concise | balanced | detailed}
- **Tone:** {casual | professional | technical}

## Explanation Preferences
- **Style:** {analogy-heavy | technical-precise | visual-with-diagrams | example-driven}
- **Assumed knowledge:** {beginner | intermediate | advanced | expert}
- **Domain experience:** {free text}

## Project Context
- **Project phase:** {prototype | mvp | active-growth | mature | maintenance}
- **Team size:** {solo | 2-5 | 6-15 | 16+}
- **Deployment cadence:** {continuous | weekly | monthly | release-based | not-yet}
- **Business priority:** {speed-to-market | reliability | compliance | cost-reduction | feature-completeness}

## Additional Notes
{free text}
```

A skill file is free-form: `# <Skill> Preferences` followed by the settings that skill documents (for example, `codereview.md` holds review focus and batch limits, `ss.md` holds the screenshot folder). `quick-review` reads `codereview.md`.
