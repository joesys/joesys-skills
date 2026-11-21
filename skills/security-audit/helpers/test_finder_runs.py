"""Tests for finder_runs.py: long background runs of other models, with a watch.

Every test uses a fake command (a short Python one-liner) in place of a real
model command-line tool. They prove the launcher and the watch. They do not
prove that a real model tool behaves the same way.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parent / "finder_runs.py"
MARKER = "<<<END-OF-ANSWER>>>"

# Short timings so the suite stays fast. Production uses the defaults.
FAST = {"FINDER_RUNS_BEAT_SECONDS": "0.1", "FINDER_RUNS_POLL_SECONDS": "0.1"}


def run_helper(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
        env={**os.environ, **FAST},
        check=check,
        timeout=60,
    )


def start(run_dir: Path, name: str, code: str, *extra: str) -> None:
    prompt = run_dir / f"{name}.prompt.txt"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt.write_text("the prompt text\n", encoding="utf-8")
    run_helper(
        "start",
        "--run-dir", str(run_dir),
        "--name", name,
        "--cwd", str(run_dir),
        "--prompt", str(prompt),
        *extra,
        "--",
        sys.executable, "-c", code, "{final}",
    )


def states(run_dir: Path, *extra: str) -> dict[str, dict]:
    result = run_helper("status", "--run-dir", str(run_dir), "--json", *extra)
    return {run["name"]: run for run in json.loads(result.stdout)}


def wait_for(run_dir: Path, name: str, wanted: str, *extra: str) -> dict:
    deadline = time.time() + 20
    while time.time() < deadline:
        run = states(run_dir, *extra)[name]
        if run["state"] == wanted:
            return run
        time.sleep(0.1)
    pytest.fail(f"{name} never reached {wanted}: {run}")


WRITES_FINAL = (
    "import sys; prompt = sys.stdin.read(); print('{\"type\": \"event\"}', flush=True); "
    "open(sys.argv[1], 'w').write('saw: ' + prompt + '%s')"
)


def test_a_run_that_ends_with_the_marker_is_finished(tmp_path: Path) -> None:
    start(tmp_path, "finder-a", WRITES_FINAL % MARKER)

    run = wait_for(tmp_path, "finder-a", "finished")

    assert run["exit_code"] == 0
    final = Path(run["final_file"]).read_text(encoding="utf-8")
    assert "saw: the prompt text" in final  # the prompt arrived on stdin
    assert MARKER in final
    assert (tmp_path / "finder-a.log").read_text(encoding="utf-8").strip() == '{"type": "event"}'


def test_an_answer_without_the_marker_is_unusable(tmp_path: Path) -> None:
    # A safety filter or a length limit can cut an answer short with exit
    # code 0. An earlier audit by this method was stopped that way once.
    start(tmp_path, "finder-a", WRITES_FINAL % "the answer stops here")

    run = wait_for(tmp_path, "finder-a", "unusable")

    assert run["exit_code"] == 0
    assert "end marker" in run["detail"]


def test_a_nonzero_exit_code_is_crashed(tmp_path: Path) -> None:
    start(tmp_path, "finder-a", "import sys; sys.stderr.write('boom: no such model\\n'); sys.exit(3)")

    run = wait_for(tmp_path, "finder-a", "crashed")

    assert run["exit_code"] == 3
    assert "boom: no such model" in run["detail"]


def test_a_command_that_cannot_start_is_crashed(tmp_path: Path) -> None:
    prompt = tmp_path / "p.txt"
    prompt.write_text("x", encoding="utf-8")
    run_helper(
        "start", "--run-dir", str(tmp_path), "--name", "finder-a", "--cwd", str(tmp_path),
        "--prompt", str(prompt), "--", "no-such-program-for-this-test",
    )

    run = wait_for(tmp_path, "finder-a", "crashed")

    assert "could not start" in run["detail"]


def test_the_final_answer_can_come_from_the_result_event_of_the_stream(tmp_path: Path) -> None:
    code = (
        "import json; print(json.dumps({'type': 'system', 'session_id': 'abc-123-def'})); "
        "print(json.dumps({'type': 'result', 'result': 'two findings\\n%s'}))" % MARKER
    )
    start(tmp_path, "finder-a", code, "--stream-result")

    run = wait_for(tmp_path, "finder-a", "finished")

    assert Path(run["final_file"]).read_text(encoding="utf-8") == f"two findings\n{MARKER}"
    assert run["session"] == "abc-123-def"


def test_the_session_id_of_a_thread_event_is_reported(tmp_path: Path) -> None:
    code = (
        "import sys, json; print(json.dumps({'type': 'thread.started', 'thread_id': '01a1fd4b-72b4'})); "
        "open(sys.argv[1], 'w').write('%s')" % MARKER
    )
    start(tmp_path, "finder-b", code)

    assert wait_for(tmp_path, "finder-b", "finished")["session"] == "01a1fd4b-72b4"


def test_a_quiet_run_is_idle_and_is_never_stopped_by_the_watch(tmp_path: Path) -> None:
    start(tmp_path, "finder-a", "import time; time.sleep(30)")

    run = wait_for(tmp_path, "finder-a", "idle", "--idle-seconds", "0.5")
    assert "no output" in run["detail"]

    # With the normal limit the same run counts as running: it is alive.
    assert states(tmp_path)["finder-a"]["state"] == "running"
    run_helper("stop", "--run-dir", str(tmp_path), "--name", "finder-a")


def test_stop_ends_a_run_and_records_that_it_was_stopped(tmp_path: Path) -> None:
    marker_file = tmp_path / "still-alive.txt"
    code = f"import time; time.sleep(3); open({str(marker_file)!r}, 'w').write('x')"
    start(tmp_path, "finder-a", code)
    wait_for(tmp_path, "finder-a", "running")

    run_helper("stop", "--run-dir", str(tmp_path), "--name", "finder-a")

    assert states(tmp_path)["finder-a"]["state"] == "stopped"
    time.sleep(3.5)
    assert not marker_file.exists()  # the model command itself was ended too


def test_a_run_that_vanished_without_an_exit_record_is_crashed(tmp_path: Path) -> None:
    record = {
        "name": "finder-a", "cwd": str(tmp_path), "command": ["x"], "prompt": "p",
        "stream_result": False, "started": time.time() - 3600, "pid": 999999,
    }
    (tmp_path / "finder-a.run.json").write_text(json.dumps(record), encoding="utf-8")

    run = states(tmp_path)["finder-a"]

    assert run["state"] == "crashed"
    assert "without an exit record" in run["detail"]


def test_wait_returns_when_a_state_changes(tmp_path: Path) -> None:
    start(tmp_path, "slow", "import time; time.sleep(30)")
    start(tmp_path, "quick", "import sys, time; time.sleep(1); open(sys.argv[1], 'w').write('%s')" % MARKER)
    wait_for(tmp_path, "slow", "running")

    began = time.time()
    result = run_helper("wait", "--run-dir", str(tmp_path), "--timeout", "20", "--json")

    assert time.time() - began < 15
    by_name = {run["name"]: run["state"] for run in json.loads(result.stdout)}
    assert by_name == {"quick": "finished", "slow": "running"}
    run_helper("stop", "--run-dir", str(tmp_path), "--name", "slow")


def test_wait_returns_at_once_when_every_run_has_ended(tmp_path: Path) -> None:
    start(tmp_path, "quick", WRITES_FINAL % MARKER)
    wait_for(tmp_path, "quick", "finished")

    began = time.time()
    run_helper("wait", "--run-dir", str(tmp_path), "--timeout", "20")

    assert time.time() - began < 5


def test_wait_gives_up_after_its_timeout_and_leaves_the_run_alone(tmp_path: Path) -> None:
    start(tmp_path, "slow", "import time; time.sleep(30)")
    wait_for(tmp_path, "slow", "running")

    result = run_helper("wait", "--run-dir", str(tmp_path), "--timeout", "1")

    assert "No change" in result.stdout
    assert states(tmp_path)["slow"]["state"] == "running"
    run_helper("stop", "--run-dir", str(tmp_path), "--name", "slow")


def test_a_name_cannot_be_started_twice(tmp_path: Path) -> None:
    start(tmp_path, "finder-a", WRITES_FINAL % MARKER)
    prompt = tmp_path / "finder-a.prompt.txt"

    again = run_helper(
        "start", "--run-dir", str(tmp_path), "--name", "finder-a", "--cwd", str(tmp_path),
        "--prompt", str(prompt), "--", sys.executable, "-c", "pass", check=False,
    )

    assert again.returncode != 0
    assert "already exists" in again.stderr


def test_the_status_text_names_every_run_and_its_state(tmp_path: Path) -> None:
    start(tmp_path, "finder-a", WRITES_FINAL % MARKER)
    wait_for(tmp_path, "finder-a", "finished")

    text = run_helper("status", "--run-dir", str(tmp_path)).stdout

    assert "finder-a" in text
    assert "finished" in text
    assert "finder-a.final.md" in text


# --- Live run, 2026-11-21 ----------------------------------------------------
# A provider's safety filter stopped one finder after four commands. The tool
# ended with exit code 1, and the reason stood only in its event stream. The
# status line showed the last line of stderr, which said nothing.

FLAGGED = "This content was flagged for possible cybersecurity risk."


def test_a_crash_shows_the_error_event_of_the_stream(tmp_path: Path) -> None:
    code = (
        "import json, sys; print(json.dumps({'type': 'thread.started', 'thread_id': 'abc'})); "
        "print(json.dumps({'type': 'error', 'message': %r})); "
        "print(json.dumps({'type': 'turn.failed', 'error': {'message': %r}})); "
        "sys.stderr.write('Reading prompt from stdin...\\n'); sys.exit(1)" % (FLAGGED, FLAGGED)
    )
    start(tmp_path, "finder-b", code)

    run = wait_for(tmp_path, "finder-b", "crashed")

    assert FLAGGED in run["detail"]
    assert run["exit_code"] == 1


def test_an_answer_that_ends_in_a_refusal_says_so(tmp_path: Path) -> None:
    code = (
        "import json; "
        "print(json.dumps({'type': 'assistant', 'message': {'stop_reason': 'refusal', 'content': []}})); "
        "print(json.dumps({'type': 'result', 'is_error': False, 'result': 'I cannot continue.'}))"
    )
    start(tmp_path, "finder-a", code, "--stream-result")

    run = wait_for(tmp_path, "finder-a", "unusable")

    assert "refus" in run["detail"]


def test_a_late_heartbeat_gets_a_second_look_before_the_run_counts_as_crashed(tmp_path: Path) -> None:
    # After a laptop wakes from sleep, the heartbeat is old for a moment
    # although the runner is alive. A run that is called crashed too early
    # would be started a second time, and two finders would run at once.
    record = {
        "name": "finder-a", "cwd": str(tmp_path), "command": ["x"], "prompt": "p",
        "stream_result": False, "started": time.time() - 3600, "pid": 999999,
    }
    (tmp_path / "finder-a.run.json").write_text(json.dumps(record), encoding="utf-8")
    (tmp_path / "finder-a.log").write_text("{}\n", encoding="utf-8")  # it wrote output just now
    beat = tmp_path / "finder-a.beat"
    beat.touch()
    old = time.time() - 600
    os.utime(beat, (old, old))
    # The runner "wakes up" and touches its heartbeat a moment later.
    waker = subprocess.Popen([sys.executable, "-c", f"import time, pathlib; time.sleep(0.05); pathlib.Path({str(beat)!r}).touch()"])

    run = states(tmp_path)["finder-a"]
    waker.wait()

    assert run["state"] == "running"

