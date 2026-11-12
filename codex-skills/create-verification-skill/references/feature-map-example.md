# Feature Map Example

The generated skill keeps its feature map in a `features/` folder. This file
shows the two kinds of file in that folder. The app is made up: `tally`, a
command-line tool that stores expenses in a local file. Copy the shape, not
the content.

## The index: `features/README.md`

```markdown
# Tally verification map

Read this index before you drive the app. Then follow the file for the
feature you need.

## Baseline

- Build once with `make build`. The binary is `./bin/tally`.
- Every run uses its own data folder: `TALLY_HOME=/tmp/tally-verify-$RUN_ID`.
- Seed two expenses with `helpers/seed.sh`.
- Run `helpers/doctor.sh` first. It prints the binary version and the data
  folder, and it exits with 0 when both are the expected ones.

## Proof rules

- Capture the command, stdout, stderr, and the exit code.
- After a change, read the stored value back with a second command.
- Save every artifact under `artifacts/<feature-id>/`.
- Outside services: none. `tally` works offline, so no proof needs a `live`
  or `fake` label.
- Report a path that you could not reach, with the command you tried and what
  was missing. Do not report it as proven through another path.

## Features

- [Add an expense](./add-expense.md): add, reject bad input, read back.
- [Monthly report](./monthly-report.md): totals by category, empty month.
```

## One feature: `features/add-expense.md`

```markdown
# Add an expense

A user records one expense with an amount, a category, and a date. The
expense then appears in the list and in the monthly report.

## Sub-features

- `add-basic` stores an expense and prints its ID.
- `add-reject` refuses a negative amount and stores nothing.
- `add-default-date` uses today when the user gives no date.

## How to get to it (user POV)

- Run `tally add <amount> <category>` in a terminal.
- Run `tally add` with no arguments and answer the prompts.

## Driving it with helpers/drive.sh

Preconditions:

- `helpers/doctor.sh` exits with 0.
- The data folder holds the two seeded expenses.

- **Add.** Run `helpers/drive.sh -- tally add 12.50 food`. The exit code is
  0, and stdout is `added #3`.
- **Read back.** Run `helpers/drive.sh -- tally list --format json`. The
  output holds three expenses. The last one has amount `12.50` and category
  `food`.
- **Reject.** Run `helpers/drive.sh -- tally add -5 food`. The exit code is
  2, and stderr says `amount must be positive`. A second `tally list` still
  shows three expenses.
- **Proof.** `helpers/drive.sh` saves each transcript under
  `artifacts/add-expense/`.

## Gotchas

- `tally list` prints a table by default. Use `--format json` for checks.
- The prompt form reads from the terminal. Drive it in a terminal session,
  not through a pipe.
- An expense with a future date is stored, but the monthly report leaves it
  out.
```
