---
date: 2026-11-21
topic: reviewer-caught-unread-claim
project: joesys-skills
session: unknown
status: unwritten
---

## Situation

joesys asked for a new skill, `/security-audit`. It audits a codebase for
security flaws by reading its source. Two finder models search alone, the
running model checks every candidate and writes a report, and a second
frontier model reviews the report. The skill was built with tests first,
then run for the first time on one small folder of a private codebase.

## Key Moments

1. **A "checked" finding was not real.** One finder reported that a page
   hid a button from normal users, while the server allowed the action. The
   writer opened the view, saw the value that decides about the button, and
   confirmed the finding. The reviewer opened the template: no page ever
   read that value. The alternative was to trust the writer's check, because
   it had "opened the code". The writer had opened the code next to the
   claim, not the code that the claim was about. (Inference: the value had
   a name that said "show this button", and that name was convincing
   enough to stop looking.)

2. **A suggested fix would have broken a page.** The writer proposed a log
   entry that stored a list. The reviewer found that the log page reads an
   `old` and a `new` value from each entry. The fix was written from the
   place that writes the data, without a look at the place that reads it.

3. **A rule that three files repeated was false.** The model registry and
   two skills said that a resumed session keeps its read-only mode. The
   new skill's second review round needed a resume, so the resume was
   tried in a temp folder first. The resumed Codex session came back with
   write access and another model, and it created a file. The alternative
   was to copy the documented command, as the earlier skills did.

4. **The plan changed when a safety filter stopped one finder.** On the
   whole codebase, the provider's filter ended the second finder after four
   commands. The skill text, written an hour earlier, said to resume such a
   run. The choice was to not retry, to tell joesys, and to change the
   text. Then the full report was dropped: with half the planned input it
   would have been redone anyway.

5. **Two checks moved from a model to a script.** The reviewer compared
   every code quote with its file by hand, and ran `git apply --check` on
   the diffs. One diff did not apply. Both checks now run in the finishing
   script. The alternative was a line in the reviewer's instructions.

## The Insight (Inferred)

A second reader finds what the first reader believed without looking. The
writer's check and the reviewer's check had the same instructions. The
difference was what each one took as given. The writer took the finder's
description of the page as given and checked the rest. The reviewer took
nothing as given, because it had not read the finder's answer at all: it
saw only the report. That was a design choice of the skill, made for
another reason (to judge the report as its reader sees it), and it turned
out to be the reason the review worked.

The same pattern shows in moment 3. A sentence that stands in three files
looks checked. It was copied twice.

## Supporting Evidence

- **Commits:**
  - `abe73ed` fix(delegation): give a resumed Codex or Claude session its
    read-only flags again
  - `8337877` feat(skills): add /security-audit to find security flaws by
    reading the source
  - `f34cef6` fix(security-audit): close the gaps that the first live run
    showed
  - `aeaa27b` test(security-audit): record the run on a whole codebase, and
    use its numbers
- **Conversation exchanges:**
  - Reviewer, round 1, in short: the view computes the value that should
    hide the button, but the template never reads it, and the page shows
    the action to every editor.
  - Reviewer, round 1, in short: the proposed log entry stores a list, but
    the log page reads an old and a new value from each entry.
  - The session's own record of the resumed run: turn 1 `read-only`, turn 2
    `workspace-write` with another model.
- **Numbers:** first report 6 findings; after round 1, 10 findings and one
  finding removed; after round 2, three points printed as two views.

## Open Questions

- Would the review have worked as well if the reviewer had also read the
  finders' raw answers? The run cannot tell.
- The writer and the finder that made the false claim are from the same
  model family. Is that why the writer believed it? One case is too few.
- How often does the provider's safety filter stop a finder on a large
  codebase? It fired once in two tries.
- joesys has not yet decided what the second finder should be when the
  filter fires.
