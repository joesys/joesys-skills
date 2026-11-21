
# Rules for a finding

These rules decide what counts as a finding, how strong its evidence must
be, and which labels it gets. The finders, the writer and the reviewer all
use the same rules.

## The evidence

Nobody attacks the app in this audit. So the proof of a finding is the
path through the code, written so that a reader can follow it line by line.

A finding needs all of these:

1. **The place:** file and line range of the faulty code, and of every other
   place with the same flaw.
2. **The way in:** the entry point through which an attacker reaches the
   code, and what access the attacker needs first.
3. **The path:** each step from the entry point to the faulty line, with
   file and line.
4. **The missing or wrong defence:** what should stop the attacker, and the
   fact that it is absent, too late, or made for another case.
5. **Exact quotes:** the real lines of the file, with no change. A script
   compares every quote with the file.

State the kind of evidence:

| Kind | Meaning |
|---|---|
| Read from code | The whole path was read in the project's own code. |
| Version match | A locked library version matches a published security notice. Nobody read the library. |
| Tool report | A scanner reported it. Read the code and turn it into "Read from code", or reject it. |
| Verify first | The code shows the risk, but a fact outside the code decides whether it is real. Name the fact, how to check it, and what each answer means. |

## Try to prove it wrong

Before a candidate is reported, and again before it enters the report, ask
these questions. One "yes" is enough to reject it or to lower it.

1. Does every cited file, function and line exist, and does the quote match?
2. Can an attacker really control the input, or does it come only from a
   trusted place?
3. Is there a guard somewhere else that stops it: middleware, a decorator, a
   base class, a query filter, a framework default that is still switched
   on? Find it and cite it, or say that you looked and where.
4. Is the code reachable in production, or only from tests, samples and
   developer tools? Do not reject it because of a folder name alone: check
   whether production code calls it.
5. Does the claim need a caller to misuse a function that is safe as it is
   used today?
6. Does it need conditions that do not happen? A race that an attacker can
   repeat by script does happen.
7. Is a working defence already there, and the candidate only suggests a
   second one?
8. Does the attacker gain anything beyond what the same person may already
   do?
9. Is it the same flaw as another candidate, at the same place, with the
   same missing defence?

A flaw inside the project's own logic stays valid even when no caller uses
it today: a broken check, a fixed secret, a query built from strings. Say
that it is not reachable yet, and rate it low.

## Severity

Answer four questions in writing. The answers are the reason for the label.

1. **What does the attacker hold afterwards?** Name the real data or
   ability in this app, not the worst case of the class. Reading, changing
   and blocking are three different gains.
2. **What does the attacker need first?** Each need lowers the severity: an
   account, a role, an action by a victim, a setting that is not the
   default, luck with timing.
3. **How far does it reach?** One record, one account, one tenant, every
   tenant, the whole system. Count only what the code shows.
4. **What is it worth here?** Judge against what this app protects.

| Label | Meaning |
|---|---|
| Critical | Wide and direct harm with little or no access needed: control of accounts, of the system, or of the main data of many users. |
| High | Serious harm to real users or data, and the attacker needs only what a normal user can get. |
| Medium | Real harm, but limited: it stays inside one account or one tenant, or it needs a strong condition first. |
| Low | A real defect with a small effect, or one that needs unusual conditions. |
| Info | No direct harm. A weak habit or a missing safety net that the team should know. |

Rules for the label:

- Each step up needs a named fact from the code. Between two labels that
  both can be argued, choose the lower one.
- The reason must not contain the argument why the flaw does not matter. If
  it does, the label is too high.
- Do not count the harm of another, separate finding into this one. A chain
  is the exception: see "One flaw, one finding".
- **A finding that was only read from the code can be Critical.** The
  method that this skill builds on never gives Critical without a live
  proof. This skill reads source only, so it would never warn loudly enough.
  Give Critical when the whole path was read and the confidence is high.
  The confidence label carries the doubt, not the severity.
- **Small findings stay in the report.** A weak setting, an old library, a
  secret-like value in a tracked file, a log that keeps too much, a missing
  limit: report them as Low or Info. They teach, and some of them turn
  serious when a fact outside the code is known.

Upper limits, unless a named fact shows more:

| Case | Highest label |
|---|---|
| The attacker must already be an admin of the same scope | Medium |
| The harm stays inside the attacker's own account or tenant | Medium |
| It works only with a setting that is not the default | High, and mark it "Verify first" |
| Cross-site scripting with no shown path to another user's session or to an admin | Medium |
| A version match with no shown use of the faulty feature | Low |
| A version match where the app clearly uses the faulty feature | Medium, and mark it "Verify first" |
| Only a missing limit on size or rate | Low |

If nobody ends up with anything they should not have, and there is no habit
worth teaching, it is not a finding. Put it on the rejected list with the
reason.

## Confidence

| Label | Meaning |
|---|---|
| High | The whole path was read, no other guard was found, and the reach is clear. |
| Medium | The flaw is strongly indicated, but one real doubt is left: a helper that was not read, a branch that depends on data, a service outside the repository. |
| Low | The flaw is likely, but the story has a gap. |

When you are unsure between two levels, choose the lower one, and name the
doubt.

## One flaw, one finding

- The same flaw at several places is one finding. List every place.
- The same place with the same missing defence is one finding, even when
  two classes describe it.
- A different place with a different missing defence is a different finding.
- **A chain is one finding.** When an attacker must use several flaws one
  after the other to reach one harm, write one finding for the chain. List
  every link with its place. Rate the chain by the harm of the whole chain
  and by what the attacker needs for the first link. The fix must break the
  chain, and it is best to break it at every link. If a link is harmful by
  itself too, say what it gives alone.
- The title names the defect and where it is, in plain words. It does not
  name the consequence, and it does not hedge.

## Secrets

Report a secret by the file, the line and the name of the setting. Never
write the value, a part of it, or its length when the length helps to guess
it. To show that two values are the same, compare their hashes and say that
they match. Never quote from a secret file.

## Steps to reproduce

Write them as a check that a developer runs on a local or test copy. The
steps show the flaw in the code as it is today. A check of the fixed code
is a test idea, and it belongs under "how to avoid this next time".

- Use test accounts and made-up data: `admin@a.test`, `victim@b.test`.
- Use harmless test values that only show that the flaw exists: a bold tag
  in a name field, the formula `=1+1` in a CSV cell, the id of a second test
  record.
- After a step that shows the flaw, say what the reader will see.
- End with what a safe system would do at that step.
- Never give a step against a live system, a real account, or another
  company's server.

## The fix

- Give the smallest change that closes the flaw, as a diff against the
  present code, and say in words why it works.
- Say what the fix changes for normal users: a feature that goes away, a
  login that ends, an action that needs a new permission.
- A fix in this audit is a suggestion. Nobody applied it and nobody ran the
  tests on it. Say so.
