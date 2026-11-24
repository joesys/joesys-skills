---
date: 2026-11-09
topic: fake-tests-hid-broken-agy
project: joesys-skills
session: unknown
status: unwritten
---

## Situation
A usage review of all 23 skills in joesys-skills checked each skill against real prompt history and real tool runs, not just the code. It found that the Antigravity integration (`scripts/agy_adapter.py`, used by /antigravity, /ai-council, and /codereview) had been broken in real use, while its test suite stayed green the whole time.

## Key Moments
1. **Green tests, broken product** — The adapter's 15 tests all passed, but joesys's real `/antigravity` run on Nov 1 failed with "flag needs an argument: -p". The tests used a fake `agy` that still accepted a bare `-p`; the real CLI had changed. Alternative was to trust the suite. The review instead treated "code correct", "live integration works", and "skill is useful" as three separate questions, which is what exposed it.
2. **Making the fake honest first** — Before fixing the adapter, the fake `agy` was changed to behave like the real 1.5.3 CLI, so 6 tests went red with the same error as the real failure. Only then was the adapter fixed. Alternative was to fix the adapter and add new tests afterwards, which would leave the fake as wrong as before.
3. **A second bug only a live probe could find** — Switching to stream-json input removed the command-line size limit, so large prompts looked safe. A live test with a 208 KB prompt showed agy silently kept only the first 187,648 bytes and still returned success. No fake would have shown this. The fix was a hard 150,000-byte limit with a clear error.
4. **Same lesson for "read-only"** — The docs said `--sandbox` made agy read-only. A live probe showed agy still wrote a file with `--sandbox` alone; `--mode plan` was needed.
5. **Side insight: size matters most for the skills agents call** — /commit was loaded about 230 times a month, mostly by agents. Splitting the rarely used history-rewrite part into /restructure-commit cut it from 3,960 to 2,219 words.

## The Insight (Inferred)
A fake external tool only proves your code matches your *belief* about the tool. When the real tool changes, the fake keeps your tests green while users hit errors. Check integrations with one cheap live call, and when a live run disagrees with the fake, fix the fake first so the tests fail for the real reason.

## Supporting Evidence
- **Commits:** `709f8b8` fix(delegation): repair Antigravity calls and update the default GPT model; `70d5e82` feat(commit)!: move history restructuring into a separate /restructure-commit skill; merge `7d09b6d`.
- **Conversation exchanges:**
  - AI (agent report): "With `--sandbox` alone, the agent wrote `probe.txt` into a scratch folder. With `--mode plan --sandbox`, the same request wrote nothing."
  - AI (agent report): "I tested a 208 KB prompt ... `agy` silently dropped everything after 187,648 bytes."
  - joesys's global rule: "Passing tests with fake providers does not prove that a live integration works or that the product is useful."
- **Code snippets:**
  ```python
  # Before
  cmd = [agy_bin, *argv, "-p"]           # prompt on stdin
  # After
  cmd = [agy_bin, *argv, "--input-format", "stream-json", "--output-format", "stream-json"]
  MAX_PROMPT_BYTES = 150_000             # agy drops the end of larger prompts silently
  ```

## Open Questions
- How long was Antigravity broken before the Nov 1 failure was noticed? Did ai-council runs quietly fall back to two models?
- Would a scheduled "one live call per provider" check be worth it, or is checking during reviews enough?
- Is the stream-json input format (not in `agy --help`) a risk joesys is comfortable with?
