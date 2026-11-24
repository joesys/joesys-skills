---
date: 2026-11-12
topic: grok-live-probes
project: joesys-skills
session: unknown
status: unwritten
---

## Situation
The collection had `/claude`, `/codex` and `/antigravity`, and joesys asked for a "simple" fourth one: `/grok`, to query xAI's Grok CLI. The skill is only about 70 lines of Markdown plus one command template in `shared/model-defaults.md`. Almost all the work was finding out which flags really keep Grok read-only, because the plan based on Grok's own guide was wrong several times.

## Key Moments
1. **"Default" wrote a file** — The guide says a non-interactive run refuses anything that needs approval. The first probe with no mode flag created the file anyway. The reason was `permission_mode = "always-approve"` in the user's own Grok settings. Alternative was to trust the documented default. The lesson taken: a default belongs to the user's machine, so the command must set the mode itself.
2. **The documented read-only sandbox did not start** — `--sandbox read-only` is the guide's recommended profile for code review. On the test machine grok 1.0.77 refused to start with it. Alternative was to ship it because the guide recommends it. It was left out, and the reason was written next to the template.
3. **Resume lost the safety** — A resume without `--permission-mode plan` answered "The plan is approved" and wrote the file. The fix was structural, not a reminder: the resume commands are now written as "the template plus one flag", and a test checks that only one full `grok` command exists.
4. **The consulted model found a real gap, and also a false one** — The first real `/grok` run asked Grok to review the new skill. It claimed `touch` and `mkdir` still run in plan mode. A probe confirmed it, so two `--deny` rules were added. It also claimed a resume must run in the same folder. A probe showed that was false. Alternative was to accept or reject the whole review. Each claim was tested on its own.
5. **Two fixes that did not work were not shipped** — When Grok tries a command that needs approval, the run stops with exit code 0 and only a stderr line says so. A `--rules` instruction and a follow-up "answer without commands" prompt were both tried. Each failed in at least one live run. The skill now only detects and reports the cut-short answer.
6. **The shipped copy was not the tested file** — The generator for the Codex copy replaces "Bash" with "shell". It turned `--deny "Bash(touch *)"` into `--deny "shell(touch *)"`, a rule Grok does not honor. The guardrail test read only the source file, so everything was green. A reviewer asked for a diff of the generated file, and that found it.

## The Insight (Inferred)
Test the exact thing that ships, on the path it ships through. Here that meant the literal command line, the resume form of it, and the generated copy, not the source text and not the documentation. A second, smaller lesson: when a fix cannot be shown to work, leave it out and report the limit honestly.

## Supporting Evidence
- **Commits:** `5978c41` feat(skills): add /grok to send a prompt to xAI's Grok CLI
- **Conversation exchanges:**
  - Developer: "Let's start with something simple. we have /claude /codex and /antigravity now. I want to add /grok skill to query grok code via cli."
  - AI (probe result): "a-default exit=0 probe.txt: WRITTEN (hello)"
  - Grok (resume without the plan flag): "The plan is approved. I'll create `resume.txt` with the word hello."
  - Grok (stderr, exit code 0): "permission required: Execute `python3 -c 'print(6*7)'` was not run, as a headless run cannot ask for approval"
- **Code snippets:**
  ```bash
  # Source template
  grok --permission-mode plan --deny "Bash(touch *)" --deny "Bash(mkdir *)" --prompt-file "$PROMPT_FILE"
  # Generated Codex copy, before the generator fix
  grok --permission-mode plan --deny "shell(touch *)" --deny "shell(mkdir *)" --prompt-file "$PROMPT_FILE"
  ```
  ```python
  # scripts/codex_adapter.py, before and after
  adapted = adapted.replace("Bash", "shell")
  adapted = re.sub(r"Bash(?!\()", "shell", adapted)
  ```

## Open Questions
- Did joesys expect "simple" to take about thirty live probes, and was that the right amount of checking for a 70-line skill?
- Is a skill whose answer is sometimes cut short good enough to use daily, or should Grok lose its shell tool so that it cannot be cut short?
- This is the second scrap in one week with the lesson "the live tool disagreed with the docs" (see `20261109-fake-tests-hid-broken-agy.md`). Should the two become one post?
- Should every generated file get a test that compares its commands with the source, not only this one?
