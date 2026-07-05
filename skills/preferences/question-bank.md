# Skill-Specific Question Bank

Questions for the Skill-Specific interview (`/preferences <skill-name>`, Step 3). For any skill not listed here, derive 1–3 questions from the target skill's "How preferences shape this skill" table in its SKILL.md.

## explain

> How do you prefer explanations structured?
> - Top-down (big picture first, then details)
> - Bottom-up (start with specifics, build to the whole)
> - Workflow-driven (follow the data/request through the system)
>
> Any areas you want the explanation to emphasize or skip?

## codereview

> What matters most in code reviews?
> - Rank by priority: Security, Correctness, Performance, Architecture, Clean Code, Reliability
> - Should I include minor style findings (P3/P4), or focus on real bugs and security issues only?
> - Prefer before/after code examples, or just descriptions?

## quick-review

> Same as codereview — read and reuse codereview preferences if they exist.
> Only ask if codereview preferences are missing.

## readability-review

> Any custom weights for the readability dimensions?
> (overrides the defaults in `shared/story-readability.md`)
>
> What minimum score should be reported when `--min-score` isn't passed?

## codebase-audit

> Any known trade-offs I should be aware of?
> (intentional debt, upcoming migrations, things that look bad but are deliberate)
>
> What deployment cadence does this project use?
> (Continuous / Weekly / Monthly / Release-based / Not yet)

## commit

> Any commit message preferences beyond Conventional Commits?
> - Max subject line length?
> - Always include scope?
> - Any specific scopes this project uses?
> - Should commits automatically capture devlog scraps for interesting
>   changes? (on by default — turn off if you don't use the devlog skill
>   or prefer manual capture)

## devlog

> Who's the target audience for your devlog?
> (Fellow engineers / General tech audience / Personal notes / Company-internal / Blog readers)
>
> What tone should devlog entries use?
> (Technical and precise / Conversational / Narrative storytelling)

## retrospective

> How formal should retrospectives be?
> (Casual team reflection / Structured process review / Formal with action items and owners)

## export

> Any default export preferences?
> - Preferred format: PDF / HTML / PNG
> - Theme: light / dark
> - Include table of contents?

## ss

> Where do you store your screenshots? (full path — saved to `.claude/skill-context/ss.md`)
>
> Analysis depth and explanation style follow your shared preferences — no other ss-specific questions.

## interaction-review

> How strict should scoring be?
> (Lenient / Standard / Strict)
>
> Any lenses to prioritize or reweight? (default weights are 30/25/20/15/10)

## human-review-guide

> How aggressive should SKIP triage be?
> (Conservative / Balanced / Aggressive)
>
> Should triage weight toward specific concerns? (security, architecture, etc.)

This skill runs its own first-run calibration — read and update `.claude/skill-context/human-review-guide.md` if it already exists rather than re-asking.

## handbook

> Who is the handbook's primary reader?
> (Beginners needing a guided walkthrough / Intermediate engineers needing a reference / Both)
>
> Prefer more diagrams, or more annotated code walkthroughs?

## dashboard

> The dashboard is configured via `.claude/dashboard.yaml`, not skill-context preferences —
> want help creating or updating it? (thresholds, module list, off-hours window, host mode)

## ai-council, claude, codex, antigravity

> These delegation skills use shared communication preferences.
> No additional questions needed — they read your shared preferences.
> [Skip to save]
