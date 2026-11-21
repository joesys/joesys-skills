# Notice

The analysis method of this skill builds on ideas from Shannon by Keygraph
(https://github.com/KeygraphHQ/shannon), read at commit
d72c082dc873273cb99ea53bdec1c582c2493753 on 2026-11-21.

Shannon is published under the GNU Affero General Public License, version
3.0. This skill copies no file and no text from Shannon. Every file in this
folder was written new, in our own words, and is published under the MIT
License of this collection. The credit is given because the ideas are
theirs. This note states what was done. It is not legal advice.

## Ideas taken from Shannon

From its prompts for reading source code:

- Map the code before looking for flaws: entry points, roles, guards, data
  stores, and dangerous operations.
- Follow untrusted data from where it enters to where it is used, or back
  from the dangerous operation to where the data came from.
- A defence must fit the exact place where the data is used. A change to the
  data after the defence cancels the defence.
- For access control: a guard counts only when it runs before the effect it
  protects, on every path.
- A fixed list of checks for login, sessions, tokens and password recovery.
- A fixed list of checks for requests that the server sends to other hosts.
- Record what was found safe, and what could not be checked.
- When unsure about the confidence, choose the lower level.
- Reason about severity from what the attacker gains, what the attacker
  needs first, and how far the harm reaches.

Some of Shannon's static-analysis prompts derive from Mantis by Google
(https://github.com/google/mantis), published under the Apache License,
version 2.0. From that part come these ideas:

- Review each candidate as if it were false, and try to disprove it.
- A list of common reasons why a reported flaw is not real.
- Limits on severity when a strong condition is needed first.

## What this skill does differently

- It only reads source. Shannon's main rule is to report only what it has
  proven by an attack on a running app. Here every finding is labelled as
  read from the code, and a script checks every code quote.
- A finding that was only read from the code can be Critical.
- It covers more kinds of flaws, and it keeps small findings in the report.
- Two finder models search alone. A writer checks every candidate, and a
  second frontier model reviews the report.
- The report is written to teach a beginner, not only to list flaws.
