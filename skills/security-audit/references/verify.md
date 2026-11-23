# Check every candidate

You have the answers of the finders and the results of the scanner tools.
None of them is a fact yet. A candidate is not a finding until you have
checked it against the code yourself.

The rules for evidence, severity and confidence are in `finding-rules.md`.
The way to read code is in `method.md`.

## 1. Read everything first

Read each finder's answer from start to end, with its code map, its safe
list and its not-checked list. Turn each scanner result into a candidate.
Read only the place, the rule name and the commit of a secret scanner's
result. Never read or copy the secret value.

**An answer in another format.** A manual answer, or a model that wrote in
its own way, may lack parts of the brief's structure: the code map, the
"checked and found safe" list, the "not checked" list, or the end marker.
Use its candidates as from any finder, and check each one the same way.
Then:

- Write down which parts are missing.
- Without the end marker, you cannot tell whether the answer is complete.
  Without the "not checked" list, you cannot tell what the finder skipped.
  So do not count a class that it did not mention as covered. Compare its
  candidates with the coverage list yourself, as part 7 says.
- In "How this report was made", say how this answer was made (for
  example, by the user in the interactive Codex program) and which parts it
  lacked.

**A finder's word on secrets does not replace a scan.** In the live run of
2026-11-22, one finder wrote that the history held no secrets, and the
secret scanner found a key pair in it. When the secret scanner is
installed, run it, whatever the finders say.

## 2. Merge

Two candidates are one flaw when they name the same place and the same
missing defence. Merge them, keep the better write-up of each part, and
write down who found it: both finders, the first, the second, or a tool.

Do not merge two flaws that only share a class. Two missing owner checks in
two views are one finding only when one fix closes both.

Look for chains. A finder may report two links of one chain as two
candidates, each with a lower label than the chain deserves. Or one finder
reports only one link. When several flaws give one harm only together, make
them one finding, as `finding-rules.md` says, and rate the whole chain.

## 3. Check each candidate against the code

For each candidate, in this order:

1. **Open every cited file.** Does each line exist and say what the
   candidate claims? A wrong line number is repaired. A line that does not
   exist ends the candidate.
2. **Walk the path yourself**, from the entry point to the faulty line.
   Judge from the code, not from the finder's reasoning. A finder can be
   wrong about the code, and it can be right for the wrong reason.
3. **Open what the claim rests on.** When a candidate says what a page
   shows or hides, open the template. When it says what a setting is, open
   the settings file. A finder can describe a page that it never read.
4. **Try to prove it wrong** with the nine questions of `finding-rules.md`.
   Look for the guard in the middleware, the decorators, the base classes
   and the settings before you believe that it is missing.
5. **Search for the same flaw in other places**, if the finder did not.
6. **Decide:**

   | Verdict | When |
   |---|---|
   | Confirmed | You read the whole path and found no defence. |
   | Verify first | The code shows the risk, and a fact outside the code decides. Name the fact and how a person checks it. |
   | Rejected | A question of the list ended it. Write the reason in one or two sentences. |

If you are not sure, say so. Lower the confidence and name the doubt in the
finding. Do not round a doubt up to "confirmed", and do not drop a likely
flaw because a part of it is unknown.

## 4. Stay fair

- Do not favour the finder from your own model family. If you notice that
  you believe one finder more easily, check its candidates as hard as the
  other's.
- A candidate that both finders found is stronger evidence. It is still
  checked.
- A candidate that only one finder found is not weaker by that fact alone.
  In an earlier audit by this method, half of the final entries came from
  one model only, and the other model confirmed them later.

## 5. Set the labels

Set severity and confidence by `finding-rules.md`, in writing: the four
answers for the severity, and what was read for the confidence. Use your
own judgment, not the finder's label. When two finders gave different
labels, the code decides, and the finding says why. When your label differs
from the label of both finders, say that too in the finding, with your
reason. The reviewer will weigh it.

Then put the confirmed and the verify-first findings in order: by severity
first, and inside one severity by how urgent the repair is. Number them
F-01, F-02 and so on in that order.

## 6. Check the fixes

For each finding, check the suggested fix against the present code:

- Does it close the flaw at every place that the finding lists?
- Does it fit the code as it is now, with the real names and imports?
- Does it fit the code around it? When a fix writes data, find the code
  that reads this data, and use the shape that it expects. When a fix shows
  fewer choices in a form, check what saving the form does to the choices
  that are no longer shown.
- What does it change for normal users? A fix can remove a feature or end
  a login. Write that down for the report.

You do not apply a fix and you do not run the tests. Say so in the report.

## 7. Look at what nobody covered

Compare the code map and the coverage list with what the finders covered.

- An area or a class that no finder looked at goes under "What was not
  checked". If it is small and it matters, check it yourself, and mark what
  you find as found by the writer.
- A flaw that you find while checking, such as one more place of the same
  pattern, is a finding too. Mark it as found by the writer. The reviewer
  will check it.

## 8. Keep the record

For the report you now have:

- the findings, each with its verdict, labels, places, path, fix, and who
  found it;
- the finder's test in words for each finding. You write the steps to
  reproduce yourself, from the path that you walked, by the rules in
  `report-guide.md`;
- the rejected candidates, each with who reported it and why it fell;
- what was checked and found safe, with the code that gives the protection;
- what was not checked.
