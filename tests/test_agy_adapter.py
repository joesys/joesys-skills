"""Tests for scripts/agy_adapter.py - capturing agy replies from its SQLite store.

No live `agy` is invoked. Synthetic conversation databases are built with a tiny
protobuf encoder that mirrors the wire format the adapter decodes, and the agy
subprocess is monkeypatched for the end-to-end ``main`` tests.
"""

import io
import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import agy_adapter


# --------------------------------------------------------------------------- #
# Tiny protobuf encoder (test-only) - mirrors agy_adapter's decoder.
# --------------------------------------------------------------------------- #
def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _ld_field(field_num: int, payload) -> bytes:
    """Encode one length-delimited (wire type 2) field."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    tag = (field_num << 3) | 2
    return _varint(tag) + _varint(len(payload)) + payload


def _msg(fields: dict) -> bytes:
    """Encode a message from {field_number: bytes_or_str}."""
    out = bytearray()
    for num, value in fields.items():
        out += _ld_field(num, value)
    return bytes(out)


def _assistant_payload(answer, *, thinking="(internal thinking)", bot_id="bot-abc123", dup=None):
    """A step_type=15 payload: field 20 = {1: answer, 3: thinking, 6: bot id, 8: dup}."""
    inner = _msg({1: answer, 3: thinking, 6: bot_id, 8: answer if dup is None else dup})
    return _msg({20: inner})


def _make_db(path, steps):
    """steps: list of (idx, step_type, payload_bytes)."""
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE steps (idx INTEGER, step_type INTEGER, step_payload BLOB)")
    con.executemany(
        "INSERT INTO steps (idx, step_type, step_payload) VALUES (?, ?, ?)", steps
    )
    con.commit()
    con.close()


# --------------------------------------------------------------------------- #
# extract_message_text
# --------------------------------------------------------------------------- #
def test_extract_message_text_returns_answer_excluding_thinking_and_id():
    payload = _assistant_payload(
        "The answer is 42.", thinking="I am pondering the question...", bot_id="bot-xyz"
    )
    assert agy_adapter.extract_message_text(payload) == "The answer is 42."


def test_extract_message_text_falls_back_to_field_8_when_field_1_absent():
    inner = _msg({3: "thinking", 6: "bot-x", 8: "fallback answer"})
    payload = _msg({20: inner})
    assert agy_adapter.extract_message_text(payload) == "fallback answer"


def test_extract_message_text_returns_none_when_only_thinking_present():
    inner = _msg({3: "only thinking, no answer", 6: "bot-x"})
    payload = _msg({20: inner})
    assert agy_adapter.extract_message_text(payload) is None


def test_extract_message_text_handles_non_protobuf_garbage():
    assert agy_adapter.extract_message_text(b"\xff\xff\xff not protobuf at all") is None


# --------------------------------------------------------------------------- #
# extract_reply_from_db
# --------------------------------------------------------------------------- #
def test_extract_reply_from_db_picks_last_assistant_step(tmp_path):
    db = tmp_path / "c.db"
    _make_db(
        db,
        [
            (0, 14, _msg({19: "the user prompt"})),
            (1, 15, _assistant_payload("first reply")),
            (2, 23, _msg({30: "Auto Generated Title"})),
            (3, 15, _assistant_payload("final reply")),
        ],
    )
    assert agy_adapter.extract_reply_from_db(db) == "final reply"


def test_extract_reply_from_db_ignores_user_and_title_steps(tmp_path):
    db = tmp_path / "c.db"
    _make_db(
        db,
        [
            (0, 14, _msg({19: "prompt only"})),
            (1, 23, _msg({30: "Title only"})),
        ],
    )
    assert agy_adapter.extract_reply_from_db(db) is None


# --------------------------------------------------------------------------- #
# snapshot_steps / select_changed_db
# --------------------------------------------------------------------------- #
def test_select_changed_db_detects_new_db(tmp_path):
    before = agy_adapter.snapshot_steps(tmp_path)  # empty dir
    db = tmp_path / "new.db"
    _make_db(db, [(0, 15, _assistant_payload("hi"))])
    assert agy_adapter.select_changed_db(before, tmp_path) == str(db)


def test_select_changed_db_detects_grown_db(tmp_path):
    db = tmp_path / "conv.db"
    _make_db(db, [(0, 14, _msg({19: "prompt"}))])
    before = agy_adapter.snapshot_steps(tmp_path)  # max idx == 0
    con = sqlite3.connect(str(db))
    con.execute(
        "INSERT INTO steps (idx, step_type, step_payload) VALUES (?, ?, ?)",
        (1, 15, _assistant_payload("resumed reply")),
    )
    con.commit()
    con.close()
    assert agy_adapter.select_changed_db(before, tmp_path) == str(db)


def test_select_changed_db_ignores_untouched_db(tmp_path):
    db = tmp_path / "conv.db"
    _make_db(db, [(0, 15, _assistant_payload("hi"))])
    before = agy_adapter.snapshot_steps(tmp_path)
    assert agy_adapter.select_changed_db(before, tmp_path) is None


# --------------------------------------------------------------------------- #
# protobuf walker robustness
# --------------------------------------------------------------------------- #
def test_parse_message_raises_on_truncated_length_delimited():
    bad = _varint((1 << 3) | 2) + _varint(10) + b"ab"  # claims 10 bytes, supplies 2
    with pytest.raises(agy_adapter.ProtoError):
        agy_adapter.parse_message(bad)


def test_parse_message_raises_on_truncated_varint():
    with pytest.raises(agy_adapter.ProtoError):
        agy_adapter.parse_message(b"\x80\x80")  # continuation bits but no terminator


# --------------------------------------------------------------------------- #
# main() end-to-end (agy subprocess monkeypatched)
# --------------------------------------------------------------------------- #
def test_main_recovers_reply_from_store(tmp_path, monkeypatch, capsys):
    conv = tmp_path / "conversations"
    conv.mkdir()
    monkeypatch.setenv("AGY_CONV_DIR", str(conv))

    def fake_run_agy(cmd, prompt, timeout):
        _make_db(
            conv / "abc.db",
            [
                (0, 14, _msg({19: prompt.decode("utf-8")})),
                (1, 15, _assistant_payload("captured answer")),
            ],
        )
        return b"", b"", False  # agy wrote nothing to stdout (the bug)

    monkeypatch.setattr(agy_adapter, "run_agy", fake_run_agy)
    monkeypatch.setattr(sys, "stdin", io.StringIO("Say something"))

    rc = agy_adapter.main(["--sandbox"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "captured answer"


def test_main_passes_through_direct_stdout(tmp_path, monkeypatch, capsys):
    conv = tmp_path / "conversations"
    conv.mkdir()
    monkeypatch.setenv("AGY_CONV_DIR", str(conv))
    monkeypatch.setattr(
        agy_adapter, "run_agy", lambda *a: (b"direct reply\n", b"", False)
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("hi"))

    rc = agy_adapter.main([])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "direct reply"


def test_main_empty_prompt_returns_2(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("   \n"))
    assert agy_adapter.main([]) == 2


def test_main_returns_4_when_no_output_and_no_db(tmp_path, monkeypatch, capsys):
    conv = tmp_path / "conversations"
    conv.mkdir()
    monkeypatch.setenv("AGY_CONV_DIR", str(conv))
    monkeypatch.setattr(
        agy_adapter, "run_agy", lambda *a: (b"", b"agy: some failure", False)
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("hi"))

    rc = agy_adapter.main([])
    assert rc == 4
    assert "no conversation was updated" in capsys.readouterr().err


def test_main_reports_missing_agy_binary(tmp_path, monkeypatch, capsys):
    conv = tmp_path / "conversations"
    conv.mkdir()
    monkeypatch.setenv("AGY_CONV_DIR", str(conv))

    def boom(*a):
        raise FileNotFoundError()

    monkeypatch.setattr(agy_adapter, "run_agy", boom)
    monkeypatch.setattr(sys, "stdin", io.StringIO("hi"))

    rc = agy_adapter.main([])
    assert rc == 3
    assert "not found" in capsys.readouterr().err
