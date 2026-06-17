#!/usr/bin/env python3
"""agy_adapter.py - capture Google Antigravity CLI (`agy`) replies.

WHY THIS EXISTS
---------------
`agy` (Antigravity CLI) is a bubbletea terminal-UI app. In print mode (`-p`),
v1.0.9 renders the model's reply ONLY to an interactive terminal. When stdout is
a pipe or file (e.g. captured by an agent's shell tool), `agy` writes 0 bytes -
even though the model answered and the process exits 0. The reply is, however,
persisted to a local SQLite conversation store. This adapter runs `agy`, then
recovers the reply from that store and prints it to stdout, restoring the
"pipe the prompt in, capture the answer on stdout" contract the skills rely on.

It also guards a second `agy` quirk: print mode hangs forever if its stdin never
reaches EOF. The adapter always feeds the prompt via stdin (closing it) and wraps
the run in a timeout that kills the whole process tree, so no `agy` strays linger.

CONVERSATION STORE SCHEMA (reverse-engineered, verified against agy v1.0.9)
--------------------------------------------------------------------------
Dir : ~/.gemini/antigravity-cli/conversations/<conversation-id>.db   (SQLite)
Table `steps`:
  idx           INTEGER  step order
  step_type     INTEGER  14=user prompt, 15=assistant reply, 23=auto title, ...
  step_payload  BLOB     protobuf wire-format message
Inside a step_type=15 step_payload, top-level field 20 is the assistant message
sub-message, whose sub-fields are:
  20.1  the final assistant answer, plain text   <- what we want
  20.3  the model's internal "thinking"          (exclude)
  20.6  bot id, e.g. "bot-<uuid>"                (exclude)
  20.8  duplicate of 20.1                        (fallback)

Field numbers are version-specific. If a future `agy` changes them, this adapter
must be updated; it fails loudly (non-zero exit + stderr) rather than emitting
garbage, and forwards `agy`'s own stdout first in case a future version writes
the reply to a non-TTY stdout directly.

USAGE
-----
The prompt is read from stdin; all CLI args are forwarded to `agy`, then `-p ""`
is appended (so callers must NOT pass `-p` themselves):

    cat prompt.txt | python scripts/agy_adapter.py --sandbox          # fresh
    cat prompt.txt | python scripts/agy_adapter.py -c                 # resume latest
    cat prompt.txt | python scripts/agy_adapter.py --conversation ID  # resume by id

Environment overrides:
    AGY_BIN             agy executable (default "agy")
    AGY_CONV_DIR        conversation store dir (default ~/.gemini/antigravity-cli/conversations)
    AGY_ADAPTER_TIMEOUT seconds before the agy run is killed (default 240)
"""

from __future__ import annotations

import os
import re
import signal
import sqlite3
import subprocess
import sys
from pathlib import Path

DEFAULT_CONV_DIR = "~/.gemini/antigravity-cli/conversations"
DEFAULT_TIMEOUT = 240.0

# Field numbers inside a step_type=15 assistant message (top-level field 20).
_MSG_FIELD = 20
_ANSWER_SUBFIELDS = (1, 8)  # 20.1 primary, 20.8 fallback; never 20.3 (thinking)/20.6 (id)
_ASSISTANT_STEP_TYPE = 15

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class ProtoError(ValueError):
    """Raised when a buffer is not valid protobuf wire format."""


# --------------------------------------------------------------------------- #
# Protobuf wire-format decoding (decode-only; just enough to read the store).
# --------------------------------------------------------------------------- #
def _read_varint(data: bytes, i: int) -> tuple[int, int]:
    shift = 0
    result = 0
    while True:
        if i >= len(data):
            raise ProtoError("truncated varint")
        byte = data[i]
        i += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, i
        shift += 7
        if shift > 63:
            raise ProtoError("varint too long")


def parse_message(data: bytes) -> dict[int, list]:
    """Parse protobuf wire format into {field_number: [values]}.

    Length-delimited fields -> bytes, varints -> int, 32/64-bit -> bytes.
    Raises ProtoError on malformed/truncated input.
    """
    fields: dict[int, list] = {}
    i = 0
    n = len(data)
    while i < n:
        tag, i = _read_varint(data, i)
        field_num = tag >> 3
        wire = tag & 0x07
        if field_num == 0:
            raise ProtoError("field number 0")
        if wire == 0:  # varint
            val, i = _read_varint(data, i)
        elif wire == 1:  # 64-bit
            val = data[i : i + 8]
            i += 8
            if len(val) != 8:
                raise ProtoError("truncated 64-bit field")
        elif wire == 2:  # length-delimited
            length, i = _read_varint(data, i)
            val = data[i : i + length]
            i += length
            if len(val) != length:
                raise ProtoError("truncated length-delimited field")
        elif wire == 5:  # 32-bit
            val = data[i : i + 4]
            i += 4
            if len(val) != 4:
                raise ProtoError("truncated 32-bit field")
        else:
            raise ProtoError(f"unsupported wire type {wire}")
        fields.setdefault(field_num, []).append(val)
    return fields


def _as_text(val) -> str | None:
    if not isinstance(val, (bytes, bytearray)):
        return None
    try:
        text = bytes(val).decode("utf-8")
    except UnicodeDecodeError:
        return None
    text = text.strip()
    return text or None


def extract_message_text(step_payload: bytes) -> str | None:
    """Return the assistant's plain-text answer from a step_type=15 payload, or None.

    Navigates top-level field 20 (the message sub-message) -> sub-field 1 (answer),
    falling back to 20.8. Deliberately ignores 20.3 (thinking) and 20.6 (bot id).
    """
    try:
        top = parse_message(step_payload)
    except ProtoError:
        return None
    for container in top.get(_MSG_FIELD, []):
        try:
            sub = parse_message(bytes(container))
        except (ProtoError, TypeError):
            continue
        for subfield in _ANSWER_SUBFIELDS:
            for val in sub.get(subfield, []):
                text = _as_text(val)
                if text:
                    return text
    return None


# --------------------------------------------------------------------------- #
# Conversation store access.
# --------------------------------------------------------------------------- #
def _connect_ro(db_path) -> sqlite3.Connection:
    path = Path(db_path)
    try:
        return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    except (sqlite3.OperationalError, ValueError):
        return sqlite3.connect(str(path))


def extract_reply_from_db(db_path) -> str | None:
    """Return the last assistant reply (step_type=15) text from a conversation db."""
    try:
        con = _connect_ro(db_path)
    except sqlite3.Error:
        return None
    try:
        rows = con.execute(
            "SELECT step_payload FROM steps WHERE step_type = ? ORDER BY idx",
            (_ASSISTANT_STEP_TYPE,),
        ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        con.close()
    for (payload,) in reversed(rows):
        if not payload:
            continue
        text = extract_message_text(bytes(payload))
        if text:
            return text
    return None


def _max_step_idx(db_path) -> int:
    try:
        con = _connect_ro(db_path)
    except sqlite3.Error:
        return -1
    try:
        row = con.execute("SELECT MAX(idx) FROM steps").fetchone()
    except sqlite3.Error:
        return -1
    finally:
        con.close()
    return row[0] if row and row[0] is not None else -1


def snapshot_steps(conv_dir) -> dict[str, int]:
    """Map each conversation db path -> its max steps.idx (-1 if empty/unreadable)."""
    snapshot: dict[str, int] = {}
    directory = Path(conv_dir)
    if not directory.is_dir():
        return snapshot
    for db in directory.glob("*.db"):
        snapshot[str(db)] = _max_step_idx(db)
    return snapshot


def select_changed_db(before: dict[str, int], conv_dir) -> str | None:
    """Return the db that changed vs `before` (new path, or grown step count).

    If several changed, return the most recently modified.
    """
    after = snapshot_steps(conv_dir)
    changed = [
        path
        for path, max_idx in after.items()
        if path not in before or max_idx > before[path]
    ]
    if not changed:
        return None
    changed.sort(key=lambda p: Path(p).stat().st_mtime, reverse=True)
    return changed[0]


# --------------------------------------------------------------------------- #
# Running agy with a hard timeout + process-tree kill.
# --------------------------------------------------------------------------- #
def _kill_tree(proc: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def run_agy(cmd: list[str], prompt: bytes, timeout: float) -> tuple[bytes, bytes, bool]:
    """Run `cmd`, feeding `prompt` on stdin. Returns (stdout, stderr, timed_out)."""
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )
    try:
        out, err = proc.communicate(input=prompt, timeout=timeout)
        return out or b"", err or b"", False
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=10)
        except Exception:  # noqa: BLE001 - best effort cleanup
            out, err = b"", b""
        return out or b"", err or b"", True


def _clean_stdout(raw: bytes) -> str:
    return _ANSI_RE.sub("", raw.decode("utf-8", "replace")).strip()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    conv_dir = os.path.expanduser(os.environ.get("AGY_CONV_DIR", DEFAULT_CONV_DIR))
    agy_bin = os.environ.get("AGY_BIN", "agy")
    try:
        timeout = float(os.environ.get("AGY_ADAPTER_TIMEOUT", DEFAULT_TIMEOUT))
    except ValueError:
        timeout = DEFAULT_TIMEOUT

    prompt = sys.stdin.read()
    if not prompt.strip():
        print("agy_adapter: empty prompt on stdin", file=sys.stderr)
        return 2

    before = snapshot_steps(conv_dir)
    cmd = [agy_bin, *argv, "-p", ""]
    try:
        out, err, timed_out = run_agy(cmd, prompt.encode("utf-8"), timeout)
    except FileNotFoundError:
        print(
            f"agy_adapter: `{agy_bin}` not found. Install Antigravity CLI or set AGY_BIN.",
            file=sys.stderr,
        )
        return 3

    # Forward-compatible: if agy itself wrote the reply to stdout, trust it.
    direct = _clean_stdout(out)
    if direct:
        print(direct)
        return 0

    # Recover the reply from the conversation store.
    db = select_changed_db(before, conv_dir)
    if db is None:
        msg = "agy_adapter: agy produced no output and no conversation was updated"
        if timed_out:
            msg += f" (agy timed out after {timeout:.0f}s)"
        stderr_tail = err.decode("utf-8", "replace").strip()
        if stderr_tail:
            msg += "\n" + stderr_tail[:500]
        print(msg, file=sys.stderr)
        return 4

    reply = extract_reply_from_db(db)
    if not reply:
        print(
            f"agy_adapter: could not extract a reply from {db} "
            "(agy store schema may have changed; verified against v1.0.9)",
            file=sys.stderr,
        )
        return 5

    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
