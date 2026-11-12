---
name: benchmark-checklist
description: "Use when the user invokes /benchmark-checklist, or when a performance number that you measured is about to be reported or used for a decision: a speedup, a regression, a throughput, a latency, or a choice between two options. Seven questions test whether the number measured the work you think it measured. SKIP if nothing was measured yet and the user wants a slow path found — that is an investigation, not a check."
---

# Benchmark Checklist Skill

A performance number is easy to get and easy to get wrong. It can measure
the load tool, a cache, an error path, or work that never ran. This skill
tests a number with seven questions before anyone reports it or acts on it.
Answer each question with evidence from a run, not with a guess about the
code.

**Boundary:** This skill checks a measurement. It does not make the code
faster, and it changes no product code.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`.

## Invocation

```text
/benchmark-checklist
/benchmark-checklist <claim, script, or two options>
```

With no argument, check the number that was just measured in this
conversation.

**A rough number.** When the user asked only for a quick estimate, one run
is enough. Still answer questions 4 and 7, and say that it is one run. Skip
the other questions unless that run looks wrong. A choice between two
options is never a rough number.

## Rules

1. **Leave product code alone.** You may add counts to the measurement
   script, such as a count of errors or of units of work. Say that you did.
2. **Ask before you install a tool.** Use the profilers and system tools
   that the machine already has.
3. **Ask before you put load on a service** that other people use, or that
   costs money for each call.
4. **Never read secrets.** Do not open, print, or copy a `.env` file, a
   credential file, or a secret value.
5. **Never report a number without its run count.**

## Before You Measure

- Write the claim that you expect to make, in the words that you would
  publish: "export is 30% faster at the median on the 60,000-row data set".
  The questions test that sentence.
- Read the measurement script. Note what it times, what it counts, and what
  it ignores.
- Check how busy the machine is and how many cores it has. On Linux and
  macOS, `uptime` shows the load. If the machine is busy, find out what is
  running. If you cannot stop it, alternate the two sides so that both see
  the same noise, and say so in the report.

## The Seven Questions

1. **Why not double?** Name what limits the number. Profile in a run that
   you do not report, because a profiler slows the work down. Look at the
   processor time of each process, at a profile of the runtime, at time
   spent waiting on disk or network, and at system calls. Then find the hot
   spot in the source. Watch the load tool too: if it reaches its limit
   first, you measured the load tool. If a change did not move the number,
   the limit explains why. Find it before you call the change useless.
2. **Was it tuned?** Run each side the way production runs it: a release
   build, the production settings, the same versions and data, and caches as
   warm or as cold as production has them. If one side runs on defaults, you
   compared two configurations, not two implementations. When the limit is a
   setting, such as a debug build, one commit for each row, or a missing
   index, that side is untuned. Tune it and measure again before you choose
   a winner. If you cannot tune it, do not choose a winner from that run.
3. **Did it break limits?** Do the arithmetic. Compare bytes per second
   with the speed of the disk and the network. Compare operations per second
   with what the cores can do. Compare the time saved with the time that the
   changed part took. Removing a part that takes 10% of the run makes the
   run at most about 11% faster. A result beyond a limit measured something
   other than the work: a cache, a step that does nothing, or a bug.
4. **Did it error?** Count the failures and the responses that are not a
   success. Check that the output is correct, not only that it exists. A
   rejection is often fast, and a timeout or a retry is slow. If the script
   does not count errors, add the count.
5. **Does it reproduce?** Run each side at least 5 times, and alternate
   them: A, B, A, B. Then warm-up, caches, and drift favor neither side.
   Report the median and the range. A gap smaller than the variation between
   runs is no measurable difference.
6. **Does it matter?** Next to a result for one small part, measure the
   whole path that a user waits on, with realistic data sizes. Report the
   small result as a share of the whole. A helper that takes 1% of a request
   can make the request at most 1% faster.
7. **Did it even happen?** Confirm that the work ran inside the timed
   region: the request reached the server, the rows were written, the bytes
   were read, and the code used the result. Lazy code and timeouts produce
   numbers for work that never happened. Make the script print a count of
   the work that it did.

## Report

- Start with the verdict: faster, slower, no measurable difference, or
  inconclusive.
- Give one main number first, with its unit, the run count, the range, and
  what limits it. Example: "The median went from 41 ms to 33 ms, over 7 runs
  on each side. The range after the change is 32 to 35 ms. JSON parsing on
  one core limits it."
- Call the verdict inconclusive when you claim a difference but cannot name
  what limits the number, when one side ran untuned, or when you could not
  answer questions 4 and 7. Name the gap.
- After the main number, list the answer to each question, and say which
  questions you did not check.

## Final Check

Before replying, check these four things:

- Each of the seven questions has an answer from a run, or the report says
  that it was not checked.
- The main number has its unit, its run count, and its range.
- The verdict is one of the four words.
- No product code changed.

## Credit

Adapted from the `benchmark-checklist` skill in pstack by Lauren Tan (MIT
License). The license notice is in `NOTICE.md` in this skill's folder.
