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
- **Leave every element with a `data-gen` attribute empty.** The script
  fills it: the severity counts in the top bar, the index of findings at
  the side, the jump bar and the links to the previous and next finding in
  each finding, and the entry counts of the closed parts. Each finding
  keeps its two empty elements from the template.
- **Links to other parts of the page** use the ids: a finding is `#F-01`,
  the list of findings is `#findings`, the basics are `#basics`.

## Section by section

1. **Overall assessment.** One verdict sentence with the risk level and the
   main reason. Then what the app does, where it is strong, and where it is
   weak. Fill the table with the count for each severity. In `data-areas`
   of "Where the problems are", list the parts of the app in its own
   words, separated by `|`, such as `Merchant API|Merchant dashboard|Public
   website|Settings and build`. Four to eight parts are enough. Under "What
   is good", name the protections that the code already has, with the file
   or the setting. A beginner must learn what to keep.
2. **The main themes.** Two to five themes. A theme is one cause behind
   several findings, such as "the code checks the permission but not the
   owner". Name the habit that prevents it. This section is where the
   reader learns the most, so write it with care. List the ids of its
   findings in `data-findings`, such as `F-01 F-03 F-10`.
3. **What to do first.** The checks that need no code change, each with the
   exact command or question and what each answer means. Then the repair
   order, in a few steps. Each step ends with an empty element that lists
   its findings in `data-findings`, as the template shows.
4. **The findings, by priority.** One block for each finding. Its title
   line is the line of the list: the reader sees all titles first and
   opens one. See the next part.
5. **Before you apply a fix.** The fixed warnings of the template, and any
   warning that holds for several fixes of this audit.

Sections 6 to 9 are reference material. They start closed, and the script
shows how many entries each one holds. A row or a list item that only says
"none" gets `class="none"`, so that it is not counted.

6. **What was checked and found safe.** The area, what was checked, and the
   code that gives the protection.
7. **What was not checked.** Always: that nobody attacked a running app;
   the ignored files that stayed closed; each class that no finder covered;
   each scanner that did not run; each model that failed.
8. **Candidates that were rejected.** Each with who reported it and why it
   fell. This shows the reader how a claim is tested.
9. **How this report was made.** The models and their roles, how the
   candidates were checked, the review rounds, who found what, where the
   models still differ, the reviewer's closing statement word for word,
   and the tools that ran.
10. **The basics.** The few ideas that the findings use, each in two to four
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

Four more parts are used only when they apply:

| Part | When |
|---|---|
| `path` | Required for a Critical or High finding, and welcome for the others. The path through the code as three to six boxes: the way in, the steps, the check that is missing or wrong, and the result. Mark exactly that check with `data-step="missing"`. A box may end with the file and the line. It stands right after "In short", so that the reader sees the whole flaw before the long text. |
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

The `details` tag of a finding carries five more labels. The script draws
the pictures of the report from them: the fact strip of the finding, "At a
glance" and "Where the problems are". The checker reports a label that is
missing or wrong.

| Label | Value |
|---|---|
| `data-area` | One part of the app from `data-areas`, where the way in is. |
| `data-reach` | The lowest access that is enough to reach the flaw: `anyone` (no login), `user` (a logged-in user), `partner` (a partner system or a token holder), `admin` (an admin of one tenant), or `insider` (access to servers, logs or the code). These are the attackers of the threat model in `method.md`. |
| `data-reach-label` | The same in the app's own words, such as "One merchant API token". |
| `data-fix-size` | `small` (a few lines in one place), `medium` (several places, or one new check), or `large` (a new flow, or a decision by the team). |
| `data-found-by` | Who found it, separated by spaces: `finder-1`, `finder-2`, `writer`, `reviewer`, `scanner`. Use one more name for each extra finder. |

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

## Steps to reproduce

You write the steps yourself. The finders give only a test in words. Write
the steps as a check that a developer runs on a local or test copy, from
the path that you walked in the code. The steps show the flaw in the code
as it is today. A check of the fixed code is a test idea, and it belongs
under "how to avoid this next time".

- Use test accounts and made-up data: `admin@a.test`, `victim@b.test`.
- Use harmless test values that only show that the flaw exists: a bold tag
  in a name field, the formula `=1+1` in a CSV cell, the id of a second test
  record.
- After a step that shows the flaw, say what the reader will see.
- End with what a safe system would do at that step.
- Never give a step against a live system, a real account, or another
  company's server.

## Before you run the script

Read the page once as the reader would. Check three things that the script
cannot check:

- Does the verdict in section 1 still fit the findings after the checks?
- Does every count, and every sentence that says "none" or "all", still
  hold?
- Could a beginner follow the first finding without help?
