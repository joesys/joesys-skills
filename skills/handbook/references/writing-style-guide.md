# Writing Style Guide — /handbook

Injected into every chapter writer prompt to ensure consistent voice and formatting across the handbook.

---

## Voice & Tone

- **Direct and practical.** Write as if explaining to a colleague sitting next to you. No academic formality, no marketing language.
- **Second person.** Address the reader as "you" — "You'll find the route handlers in `src/routes/`."
- **Present tense.** "The server starts on port 3000" not "The server will start."
- **Confident but honest.** State facts directly. When uncertain, say so explicitly with *[Inferred — not confirmed by code]*.
- **No filler.** Cut "basically," "essentially," "it should be noted that," "in order to."

## Formatting Rules

### Headings
- H2 (`##`) for major sections within a chapter
- H3 (`###`) for subsections
- H4 (`####`) only when H3 subsections need further breakdown
- Never skip heading levels (no H2 → H4)

### Code References
- Inline code for file paths, function names, variable names: `` `src/auth/jwt.ts` ``
- Always include the file path when referencing code: "`validateToken()` in `src/auth/jwt.ts:42`"
- Code blocks for multi-line snippets, always with language tag

### Source Links
- Use relative paths from `docs/handbook/`: `[source](../../src/auth/jwt.ts#L42)`
- Link text should be "source" or the filename: `[src/auth/jwt.ts](../../src/auth/jwt.ts#L42)`

### Tables
- Use markdown tables for structured data (env vars, dependencies, recipes)
- Keep tables under 6 columns for readability
- Align columns left

### Lists
- Numbered lists for sequential steps (setup, workflows)
- Bullet lists for unordered items (features, options)
- Keep list items to 1-2 sentences

### Diagrams
- Use Mermaid syntax for all diagrams
- Keep diagrams under 20 nodes for readability
- Add a title above each diagram as a bold paragraph: **Figure: Module Dependencies**

### Callouts
- Info: `> ℹ️ **Note:** ...`
- Warning: `> ⚠️ **Warning:** ...`
- Danger: `> ⚠️ **Danger Zone: `filename`** ...`
- Tip: `> 💡 **Tip:** ...`

## Audience Awareness

The handbook serves two audiences. Most chapters serve both, but some sections lean toward one:

- **Beginner-focused sections** (Getting Started, Code Walkthroughs, Troubleshooting): Explain concepts before using them. Don't assume familiarity with the tech stack. Show expected output for every command.
- **Reference sections** (Architecture, Module Deep Dives, Design Rationale): Can assume programming competence. Focus on "what" and "why," not "how to write code."

When a section serves both audiences, lead with the high-level explanation (serves beginners) then provide detail (serves reference readers).

## Length Guidelines

- Chapter introduction: 2-3 sentences max
- Section: 100-300 words of prose (tables and code blocks are additional)
- Code snippets in walkthroughs: ≤30 lines with annotations
- Glossary entries: 1-2 sentences per term
