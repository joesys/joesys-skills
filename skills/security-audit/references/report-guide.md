# Write the report

The report is one HTML file. You write it yourself, inside
`report-template.html`. The template fixes the sections, their order and
the look, so that every audit gives a report with the same structure. Then
`helpers/report_tools.py` adds the code colours and checks the page.

## The reader

The reader is a beginner programmer who uses English as a second language.
This reader can read code, but has never learned security. The reader wants
to triage first, then repair, and wants to learn why each flaw happened.

**The report teaches as much as it reports.** A reader who has worked
through one finding must be able to see the same mistake in other code, and
to avoid it in new code.

## The language

Follow `shared/report-style.md`. On top of it:

- One idea in each sentence. Everyday words.
- Explain each security word the first time it appears, in the same
  sentence, and put it in the word list at the end.
- Use one word for one thing in the whole report. If the app says
  "merchant", do not also say "tenant" and "customer".
- Use the names of the app: its roles, its screens, its settings. Say "a
  merchant admin", not "a privileged principal".
- Say who does what: "The view checks the permission. It does not check
  the owner."
- Keep paths, line numbers, names and values exact.
- No short forms such as arrows and symbols between steps. Write the
  sentence.

## The rules of the page

- **Keep the template.** Keep every section, the order, the ids, the
  `data-` attributes and the style block. Add nothing that loads from
  outside the file: no script, no image, no font, no style sheet.
- **Replace every placeholder** in double curly brackets, and delete every
  GUIDE comment.
- **In code blocks**, write `&` as `&amp;`, `<` as `&lt;` and `>` as `&gt;`.
  Name the language in the class of the code tag, such as `language-python`,
  `language-javascript`, `language-html`, `language-sql`, `language-shell`,
  `language-diff` or `language-text`.
- **Write no colour tags.** The script adds them.
- **Links to other parts of the page** use the ids: a finding is `#F-01`,
  the basics are `#basics`.

## Section by section

1. **Overall assessment.** One verdict sentence with the risk level and the
   main reason. Then what the app does, where it is strong, and where it is
   weak. Fill the table with the count for each severity. Under "What is
   good", name the protections that the code already has, with the file or
   the setting. A beginner must learn what to keep.
2. **The main themes.** Two to five themes. A theme is one cause behind
   several findings, such as "the code checks the permission but not the
   owner". Name the habit that prevents it. This section is where the
   reader learns the most, so write it with care.
3. **What to do first.** The checks that need no code change, each with the
   exact command or question and what each answer means. Then the repair
   order, in a few steps.
4. **All findings, by priority.** One line for each finding, with the same
   labels as in the finding.
5. **The findings in detail.** One block for each finding. See the next
   part.
6. **Before you apply a fix.** The fixed warnings of the template, and any
   warning that holds for several fixes of this audit.
7. **What was checked and found safe.** The area, what was checked, and the
   code that gives the protection.
8. **What was not checked.** Always: that nobody attacked a running app;
   the ignored files that stayed closed; each class that no finder covered;
   each scanner that did not run; each model that failed.
9. **Candidates that were rejected.** Each with who reported it and why it
   fell. This shows the reader how a claim is tested.
10. **How this report was made.** The models and their roles, how the
    candidates were checked, the review rounds, who found what, where the
    models still differ, the reviewer's closing statement word for word,
    and the tools that ran.
11. **The basics.** The few ideas that the findings use, each in two to four
    sentences with an example from this codebase, numbered. Then the word
    list.

## One finding, part by part

Each finding has nine parts, in this order. The name in code font is the
value of `data-part` in the template.

| Part | What it holds |
|---|---|
| `short` | The brief description. Two sentences at most: what is wrong, and what an attacker can do. A reader who reads only this must know whether to open the finding. |
| `context` | The background. What this part of the app does and who uses it. Enough for a new team member to follow the rest. |
| `code` | The real lines, with file and line range. Mark the faulty line with a `PROBLEM:` note. When a correct version exists in the same codebase, quote it too, with an `OK:` note. Comparing the two teaches more than any explanation. |
| `explanation` | The full description: the idea behind the bug. Say which check is there and which is missing. Lead the reader through the code, step by step. |
| `reproduce` | Numbered steps on a local or test copy, with test accounts and harmless values. After a step that shows the flaw: "You will see: ...". Then what a safe system would do. |
| `priority` | Why this severity: what the attacker gains, and what the attacker needs first. Why this confidence: what was read, and what was not. |
| `consequences` | What can happen if nobody fixes it, as concrete events in this app, not as a class name. |
| `fix` | The fix in words, the change as a diff, why the fix works, and what the fix changes for users. |
| `prevent` | How to avoid this mistake next time: one rule to remember, what to look for in a code review, and a test to write first. |

Three more parts are used only when they apply:

| Part | When |
|---|---|
| `verify` | A fact outside the code decides the real risk. Give the fact, the check, and what to do for each answer. |
| `used` | For a Critical or High finding whose past misuse would leave traces. Give read-only checks of data or logs. A fix does not undo an old break-in. |
| `views` | The two frontier models still differ after two rounds. Print each view in that model's own words. |

### The code quotes

A quote is a `pre` block with `data-file` and `data-lines`. The script
compares each quoted line with the file, so:

- Copy the lines exactly. Do not tidy them and do not shorten a line.
- A note stands at the end of a line, after the comment sign of the
  language, and starts with `PROBLEM:`, `OK:` or `NEW:`. The script ignores
  the note when it compares.
- Where you leave a few lines out, write `...` alone on a line. When two
  parts are far apart, make two quotes, each with its own range.
- `data-lines` is the range in the file that holds all quoted lines.
- A code block with no `data-file` is an example or a fix. The script does
  not compare it. Every finding needs at least one real quote.
- Never quote from a secret file, and never show a secret value.

### The fix

Show the change as a diff in a `language-diff` block: a line that starts
with `-` goes away, a line that starts with `+` is new. Keep two or three
lines around the change, so the reader finds the place.

Prefer a real diff, with the line numbers in its `@@` lines. The finishing
script asks git whether such a diff applies to the code, and reports it when
it does not. A diff with no line numbers in its `@@` lines is a sketch. The
script does not check a sketch, so check its names and its lines yourself. Then say why it
works, in the words of the explanation above it. Under "What the fix
changes for users", say what a normal user will notice, or that nothing
changes.

Some findings have no small code change, such as one that needs a new flow
or a decision by the team. Then say so, describe the change in words, and
delete the diff block. Do not invent a diff to fill the place. A diff must
fit the code as it is: use only names that exist in the project.

### The labels on a finding

In the title line: the severity, the confidence, the kind of evidence, and
who found it. Add "Verify first" and "Two views" where they apply.

A finding that is added after the review has started gets the next free
number, and it stands at the place of its severity. So the numbers need not
be in order. The number of a finding that was removed is not used again.

When the two frontier models still differ on the severity, the finding is
sorted and counted under the higher label, so that nobody overlooks it. Set
`data-severity` to the higher label. In the title line and in the list, show
both labels, the higher one first, each with the name of its role, such as
"Reviewer: Low" and "Writer: Info". In the
line at the foot of the finding, give the CWE number and name, and who
found it.

## Before you run the script

Read the page once as the reader would. Check three things that the script
cannot check:

- Does the verdict in section 1 still fit the findings after the checks?
- Does every count, and every sentence that says "none" or "all", still
  hold?
- Could a beginner follow the first finding without help?
