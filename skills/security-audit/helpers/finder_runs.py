#!/usr/bin/env python3
"""Run another model's command-line tool in the background, and watch it.

A security audit by one model can take hours, so the run cannot sit inside
one tool call. `start` launches the command detached from the caller. `status`
and `wait` then tell whether each run is still working, has gone quiet, has
crashed, or has ended, and whether its answer is complete.

    finder_runs.py start  --run-dir DIR --name NAME --cwd REPO --prompt FILE
                          [--stream-result] -- COMMAND [ARGS...]
    finder_runs.py status --run-dir DIR [--idle-seconds N] [--json]
    finder_runs.py wait   --run-dir DIR [--timeout N] [--idle-seconds N] [--json]
    finder_runs.py stop   --run-dir DIR --name NAME

The command reads the prompt file on stdin. In its arguments, the text
`{final}` is replaced by the path of the file that must hold the final answer.
With `--stream-result` the final answer is taken from the last JSON line of
the output whose `type` is `result`.

The watch never stops a run. Only `stop` does.

Files of one run, all in the run folder: NAME.run.json (what was started),
NAME.log (stdout), NAME.err (stderr), NAME.final.md (the final answer),
NAME.beat (touched while the command is alive), NAME.exit.json (how it ended).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

END_MARKER = "<<<END-OF-ANSWER>>>"
BEAT_SECONDS = float(os.environ.get("FINDER_RUNS_BEAT_SECONDS", "5"))
POLL_SECONDS = float(os.environ.get("FINDER_RUNS_POLL_SECONDS", "5"))
# A run whose heartbeat is this old has lost its runner process.
STALE_SECONDS = max(BEAT_SECONDS * 6, 3.0)
ENDED_STATES = {"finished", "unusable", "crashed", "stopped"}
SESSION_ID = re.compile(r'"(?:thread_id|session_id)"\s*:\s*"([^"]+)"')
REFUSAL = re.compile(r'"stop_reason"\s*:\s*"refusal"')


# --- start -------------------------------------------------------------------


def start(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.name):
        return fail(f"The name '{args.name}' must use only a-z, 0-9 and '-'.")
    if not args.command:
        return fail("Give the command after '--'.")
    record_file = run_dir / f"{args.name}.run.json"
    if record_file.exists():
        return fail(f"A run named '{args.name}' already exists in {run_dir}. Use a new name.")

    record = {
        "name": args.name,
        "cwd": str(Path(args.cwd).resolve()),
        "command": args.command,
        "prompt": str(Path(args.prompt).resolve()),
        "stream_result": args.stream_result,
        "started": time.time(),
        "pid": None,
    }
    record_file.write_text(json.dumps(record, indent=2), encoding="utf-8")

    runner = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "_run", "--run-dir", str(run_dir), "--name", args.name],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **detached(),
    )
    record["pid"] = runner.pid
    record_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Started '{args.name}'. Output goes to {run_dir / (args.name + '.log')}")
    return 0


def detached() -> dict:
    """Popen options that let the runner outlive the process that started it."""
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        return {"creationflags": flags}
    return {"start_new_session": True}


def run_command(args: argparse.Namespace) -> int:
    """The runner: start the command, keep the heartbeat, record how it ended."""
    run_dir = Path(args.run_dir)
    paths = RunPaths(run_dir, args.name)
    record = json.loads(paths.record.read_text(encoding="utf-8"))
    command = [part.replace("{final}", str(paths.final)) for part in record["command"]]

    with open(record["prompt"], "rb") as prompt, open(paths.log, "ab") as log, open(paths.err, "ab") as err:
        try:
            process = subprocess.Popen(command, cwd=record["cwd"], stdin=prompt, stdout=log, stderr=err)
        except OSError as error:
            write_exit(paths, code=127, error=f"The command could not start: {error}")
            return 0
        while process.poll() is None:
            paths.beat.touch()
            time.sleep(BEAT_SECONDS)

    if record["stream_result"] and not paths.final.exists():
        answer = result_event_text(paths.log)
        if answer is not None:
            paths.final.write_text(answer, encoding="utf-8")
    write_exit(paths, code=process.returncode)
    return 0


def result_event_text(log: Path) -> str | None:
    """The `result` field of the last JSON line whose `type` is `result`."""
    answer = None
    with open(log, encoding="utf-8", errors="replace") as lines:
        for line in lines:
            if '"result"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and event.get("type") == "result" and isinstance(event.get("result"), str):
                answer = event["result"]
    return answer


def write_exit(paths: "RunPaths", **fields: object) -> None:
    if paths.exit.exists():  # `stop` already wrote the record
        return
    paths.exit.write_text(json.dumps({"ended": time.time(), **fields}), encoding="utf-8")


# --- status ------------------------------------------------------------------


class RunPaths:
    def __init__(self, run_dir: Path, name: str) -> None:
        self.record = run_dir / f"{name}.run.json"
        self.log = run_dir / f"{name}.log"
        self.err = run_dir / f"{name}.err"
        self.final = run_dir / f"{name}.final.md"
        self.beat = run_dir / f"{name}.beat"
        self.exit = run_dir / f"{name}.exit.json"


def all_runs(run_dir: Path, idle_seconds: float) -> list[dict]:
    names = sorted(path.name[: -len(".run.json")] for path in run_dir.glob("*.run.json"))
    return [describe_run(run_dir, name, idle_seconds) for name in names]


def describe_run(run_dir: Path, name: str, idle_seconds: float) -> dict:
    paths = RunPaths(run_dir, name)
    record = json.loads(paths.record.read_text(encoding="utf-8"))
    now = time.time()
    quiet = now - max([record["started"], *(mtime(p) for p in (paths.log, paths.err, paths.final))])
    run = {
        "name": name,
        "state": "running",
        "detail": f"last output {age(quiet)} ago",
        "quiet_seconds": round(quiet),
        "exit_code": None,
        "final_file": str(paths.final),
        "log_file": str(paths.log),
        "session": session_id(paths.log),
    }

    if paths.exit.exists():
        ended = json.loads(paths.exit.read_text(encoding="utf-8"))
        run["exit_code"] = ended.get("code")
        run["state"], run["detail"] = ended_state(ended, paths)
    elif heartbeat_stopped(record, paths):
        run["state"] = "crashed"
        run["detail"] = "the run stopped without an exit record (its process is gone)"
    elif quiet > idle_seconds:
        run["state"] = "idle"
        run["detail"] = f"alive, but no output for {age(quiet)}"
    return run


def heartbeat_stopped(record: dict, paths: RunPaths) -> bool:
    """True when the runner no longer touches its heartbeat file.

    An old heartbeat gets a second look after a short wait. When a computer
    wakes from sleep, the heartbeat is old for a moment although the runner
    is alive. A run that is called crashed too early would be started twice.
    """
    def is_old() -> bool:
        return time.time() - max(record["started"], mtime(paths.beat)) > STALE_SECONDS

    if not is_old():
        return False
    time.sleep(BEAT_SECONDS * 2)
    return is_old() and not paths.exit.exists()


def ended_state(ended: dict, paths: RunPaths) -> tuple[str, str]:
    if ended.get("stopped"):
        return "stopped", "stopped on request"
    if ended.get("error"):
        return "crashed", ended["error"]
    said = stream_error(paths.log)
    if ended.get("code") != 0:
        reason = f"The tool said: {said}" if said else f"Last error line: {last_line(paths.err) or 'none'}"
        return "crashed", f"exit code {ended.get('code')}. {reason}"
    answer = paths.final.read_text(encoding="utf-8", errors="replace") if paths.final.exists() else ""
    if END_MARKER in answer:
        return "finished", f"answer in {paths.final}"
    why = f" The tool said: {said}" if said else ""
    if not answer.strip():
        return "unusable", "it ended with exit code 0 but left no answer, so there is no end marker." + why
    return "unusable", "the answer has no end marker, so it was cut short." + why


def stream_error(log: Path) -> str:
    """What the tool's own event stream says about a failure or a refusal.

    A provider's safety filter ends a run this way: the reason is an event on
    stdout, and stderr says nothing useful.
    """
    message, refused = "", False
    try:
        with open(log, encoding="utf-8", errors="replace") as lines:
            for line in lines:
                refused = refused or bool(REFUSAL.search(line))
                if '"error"' not in line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                kind = event.get("type")
                if kind == "error" and isinstance(event.get("message"), str):
                    message = event["message"]
                elif kind == "turn.failed" and isinstance(event.get("error"), dict):
                    message = str(event["error"].get("message", message))
                elif kind == "result" and event.get("is_error") and isinstance(event.get("result"), str):
                    message = event["result"]
    except OSError:
        return ""
    if refused and not message:
        message = "the model refused to continue (stop reason: refusal)"
    return message[:400]


def mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def age(seconds: float) -> str:
    return f"{round(seconds)} s" if seconds < 120 else f"{round(seconds / 60)} min"


def last_line(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    except OSError:
        return ""
    return lines[-1][:300] if lines else ""


def session_id(log: Path) -> str | None:
    """The session id that the tool printed, for a later resume."""
    try:
        with open(log, encoding="utf-8", errors="replace") as lines:
            for _, line in zip(range(200), lines):
                found = SESSION_ID.search(line)
                if found:
                    return found.group(1)
    except OSError:
        pass
    return None


def print_runs(runs: list[dict], as_json: bool) -> None:
    if as_json:
        print(json.dumps(runs, indent=2))
        return
    if not runs:
        print("No runs in this folder.")
    for run in runs:
        session = f"  session {run['session']}" if run["session"] else ""
        print(f"{run['name']:<16} {run['state']:<9} {run['detail']}{session}")


def status(args: argparse.Namespace) -> int:
    print_runs(all_runs(Path(args.run_dir), args.idle_seconds), args.json)
    return 0


# --- wait --------------------------------------------------------------------


def wait(args: argparse.Namespace) -> int:
    """Block until a run changes state, every run has ended, or the timeout."""
    run_dir = Path(args.run_dir)
    before = all_runs(run_dir, args.idle_seconds)
    runs = before
    deadline = time.time() + args.timeout
    reason = "Every run has ended."
    while any(run["state"] not in ENDED_STATES for run in runs):
        if state_names(runs) != state_names(before):
            reason = "A run changed its state."
            break
        if time.time() >= deadline:
            reason = f"No change in {round(args.timeout)} s. The runs are still going; wait again."
            break
        time.sleep(POLL_SECONDS)
        runs = all_runs(run_dir, args.idle_seconds)
    print_runs(runs, args.json)
    if not args.json:
        print(reason)
    return 0


def state_names(runs: list[dict]) -> dict[str, str]:
    return {run["name"]: run["state"] for run in runs}


# --- stop --------------------------------------------------------------------


def stop(args: argparse.Namespace) -> int:
    paths = RunPaths(Path(args.run_dir), args.name)
    if not paths.record.exists():
        return fail(f"No run named '{args.name}' in {args.run_dir}.")
    if paths.exit.exists():
        print(f"'{args.name}' has already ended.")
        return 0
    record = json.loads(paths.record.read_text(encoding="utf-8"))
    # Write the record first, so the runner does not overwrite it on its way out.
    paths.exit.write_text(json.dumps({"ended": time.time(), "code": None, "stopped": True}), encoding="utf-8")
    end_process_group(record["pid"])
    print(f"Stopped '{args.name}'.")
    return 0


def end_process_group(pid: int | None) -> None:
    """End the runner and the command it started."""
    if not pid:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass


# --- command line ------------------------------------------------------------


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="action", required=True)

    start_parser = commands.add_parser("start", help="start one run in the background")
    start_parser.add_argument("--run-dir", required=True)
    start_parser.add_argument("--name", required=True)
    start_parser.add_argument("--cwd", required=True, help="the folder the command runs in")
    start_parser.add_argument("--prompt", required=True, help="the file sent to the command on stdin")
    start_parser.add_argument("--stream-result", action="store_true",
                              help="take the final answer from the last 'result' JSON line of the output")
    start_parser.add_argument("command", nargs=argparse.REMAINDER)
    start_parser.set_defaults(handler=start)

    runner_parser = commands.add_parser("_run")  # used by `start` only
    runner_parser.add_argument("--run-dir", required=True)
    runner_parser.add_argument("--name", required=True)
    runner_parser.set_defaults(handler=run_command)

    for name, handler in (("status", status), ("wait", wait)):
        watch_parser = commands.add_parser(name)
        watch_parser.add_argument("--run-dir", required=True)
        watch_parser.add_argument("--idle-seconds", type=float, default=900,
                                  help="call a run idle after this many seconds without output")
        watch_parser.add_argument("--json", action="store_true")
        watch_parser.set_defaults(handler=handler)
        if name == "wait":
            watch_parser.add_argument("--timeout", type=float, default=540)

    stop_parser = commands.add_parser("stop", help="end one run")
    stop_parser.add_argument("--run-dir", required=True)
    stop_parser.add_argument("--name", required=True)
    stop_parser.set_defaults(handler=stop)

    args = parser.parse_args(argv)
    if args.action == "start" and args.command[:1] == ["--"]:
        args.command = args.command[1:]
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
