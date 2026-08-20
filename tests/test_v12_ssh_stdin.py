"""Offline tests for OPEN-57's remedy in `scripts/validation/v12_cell_pipeline.py`.

Covers T05 of `docs/docs_ACTIVE/openings/implemenation/PLAN_open-57-and-58_2026-08-19.md`:
`_ssh` gains an optional `stdin_data` channel and `_remote_results_complete` sends its
id list over stdin instead of embedding it in the command string, so the probe's length
no longer depends on fleet size (the cause of OPEN-57's `Unmatched '.` fault).

No live SSH traffic here — every `subprocess.run` / `_ssh` call is monkeypatched. The
two live calls the plan's T05 also calls for (against the absent-directory target and
an existing small fleet) were run manually, outside the automated suite, per this
project's rule against live-network integration tests in the standard run; their
verbatim results are in the CP-2 report.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "validation"))

from scripts.validation import v12_cell_pipeline as v12


class _FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_stdin_none_preserves_prior_subprocess_call(monkeypatch):
    """Default `stdin_data=None` must produce a subprocess.run call identical to
    today's — same argv, same capture_output/text/timeout kwargs, and `input=None`
    (subprocess.run's own default, so behaviour is unaffected for every existing
    caller that never passes `stdin_data`)."""
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return _FakeCompletedProcess(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(v12.subprocess, "run", fake_run)

    out = v12._ssh("echo hi", timeout=42)

    assert captured["argv"] == ["ssh", v12.REMOTE_HOST, "bash -lc 'echo hi'"]
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["timeout"] == 42
    assert captured["kwargs"]["input"] is None
    assert out == "ok"


def test_remote_results_complete_sends_ids_on_stdin_not_in_command(monkeypatch):
    """`_remote_results_complete` must not embed the id list in the command string
    any more; it must be newline-separated on stdin instead, and every id must
    round-trip cleanly (no id split across lines, no extra/missing entries)."""
    osm_ids = [f"way_{600000000 + i}" for i in range(50)] + [
        f"relation_{700000000 + i}" for i in range(5)
    ]
    captured = {}

    def fake_ssh(cmd, timeout=120, allow_fail=False, stdin_data=None):
        captured["cmd"] = cmd
        captured["stdin_data"] = stdin_data
        return "COMPLETE=55"

    monkeypatch.setattr(v12, "_ssh", fake_ssh)

    result = v12._remote_results_complete(osm_ids, "/speed-scratch/o_iseri/fleets/x")

    assert result is True
    for oid in osm_ids:
        assert oid not in captured["cmd"], (
            f"id {oid!r} leaked into the command string; the whole point of the "
            "remedy is that the command no longer grows with fleet size"
        )

    stdin_lines = captured["stdin_data"].splitlines()
    assert stdin_lines == osm_ids
    assert captured["stdin_data"].endswith("\n"), (
        "must end with a trailing newline — bash's `while read o` silently drops "
        "the last id otherwise"
    )

    for ch in captured["stdin_data"]:
        assert ch.isalnum() or ch in "_\n", (
            f"unexpected shell metacharacter {ch!r} in the id stream"
        )

    assert "while read o" in captured["cmd"]
    assert 'grep -q "EnergyPlus Completed Successfully" "$o/eplusout.end"' in captured["cmd"]


@pytest.mark.parametrize("n_ids", [10, 1_000, 10_000])
def test_probe_command_length_is_flat_across_fleet_size(monkeypatch, n_ids):
    """The command sent to `_ssh` must be the same length regardless of fleet size
    — that independence from N is the entire fix for OPEN-57. Only `stdin_data`
    (which the remote reads a line at a time) is allowed to grow with N."""
    baseline_cmd_len = {}

    def fake_ssh(cmd, timeout=120, allow_fail=False, stdin_data=None):
        baseline_cmd_len["cmd_len"] = len(cmd)
        baseline_cmd_len["stdin_len"] = len(stdin_data) if stdin_data else 0
        return "COMPLETE=0"

    monkeypatch.setattr(v12, "_ssh", fake_ssh)

    osm_ids = [f"way_{600000000 + i}" for i in range(n_ids)]
    v12._remote_results_complete(osm_ids, "/speed-scratch/o_iseri/fleets/x")

    assert baseline_cmd_len["cmd_len"] < 400, (
        f"probe command grew with fleet size (n={n_ids}, "
        f"len={baseline_cmd_len['cmd_len']}) — the id list leaked back into cmd"
    )


def test_probe_command_length_identical_across_all_sizes(monkeypatch):
    """Stronger form of the flatness check: capture the exact command for 10, 1,000
    and 10,000 ids against the same remote dir and assert they are byte-identical —
    only stdin differs."""
    seen_cmds = {}

    def fake_ssh(cmd, timeout=120, allow_fail=False, stdin_data=None):
        seen_cmds[len(stdin_data.splitlines())] = cmd
        return "COMPLETE=0"

    monkeypatch.setattr(v12, "_ssh", fake_ssh)

    for n_ids in (10, 1_000, 10_000):
        osm_ids = [f"way_{600000000 + i}" for i in range(n_ids)]
        v12._remote_results_complete(osm_ids, "/speed-scratch/o_iseri/fleets/x")

    cmds = list(seen_cmds.values())
    assert len(set(cmds)) == 1, "the probe command differs across fleet sizes"


def test_remote_results_complete_empty_ids_short_circuits(monkeypatch):
    """No ids means no ssh call at all (pre-existing behaviour, unaffected)."""
    called = {"n": 0}

    def fake_ssh(*args, **kwargs):
        called["n"] += 1
        return "COMPLETE=0"

    monkeypatch.setattr(v12, "_ssh", fake_ssh)

    assert v12._remote_results_complete([], "/speed-scratch/o_iseri/fleets/x") is False
    assert called["n"] == 0


def test_remote_results_complete_fail_safe_default_preserved(monkeypatch):
    """A remote reply with no COMPLETE=N match must still fail-safe to 0 (OPEN-54's
    deliberate design), unaffected by the stdin change."""
    def fake_ssh(cmd, timeout=120, allow_fail=False, stdin_data=None):
        return "garbage, no match here"

    monkeypatch.setattr(v12, "_ssh", fake_ssh)

    result = v12._remote_results_complete(["way_1"], "/speed-scratch/o_iseri/fleets/x")
    assert result is False


def test_ssh_sends_stdin_as_raw_bytes_not_text_mode(monkeypatch):
    """OPEN-57's second cause: `subprocess.run(..., text=True, input=stdin_data)`
    wraps the child's stdin in a `TextIOWrapper(newline=None)`, which on Windows
    rewrites every LF to CRLF on write, so `way_123\n` arrives on the remote as
    `way_123\r` and every `[ -s "$o/..." ]` test silently fails. `_ssh` must send
    `stdin_data` as raw encoded bytes, with no `text=True` stdin translation in play,
    so this cannot happen. Pins the exact `input=` kwarg passed to subprocess.run."""
    captured = {}

    def fake_run(argv, **kwargs):
        captured["kwargs"] = kwargs
        return _FakeCompletedProcess(returncode=0, stdout=b"COMPLETE=1\n", stderr=b"")

    monkeypatch.setattr(v12.subprocess, "run", fake_run)

    out = v12._ssh("some cmd", stdin_data="way_1\nway_2\nway_3\n")

    sent_input = captured["kwargs"]["input"]
    assert isinstance(sent_input, bytes), (
        "stdin_data must be sent as bytes, not str -- a str `input` under "
        "text=True is exactly what triggers Windows' LF-to-CRLF rewrite"
    )
    assert sent_input == b"way_1\nway_2\nway_3\n"
    assert b"\r" not in sent_input
    assert captured["kwargs"].get("text") is not True, (
        "text=True must not be set on the stdin_data path -- that is the whole "
        "mechanism behind the CRLF corruption"
    )
    assert out == "COMPLETE=1\n"


def test_ssh_decodes_bytes_stdout_stderr_explicitly(monkeypatch):
    """Since the stdin_data path runs subprocess.run without text=True, stdout/stderr
    come back as bytes and `_ssh` must decode them itself before returning str."""
    def fake_run(argv, **kwargs):
        return _FakeCompletedProcess(
            returncode=0, stdout=b"COMPLETE=2\n", stderr=b"warning: some remote text\n"
        )

    monkeypatch.setattr(v12.subprocess, "run", fake_run)

    out = v12._ssh("some cmd", stdin_data="a\nb\n")
    assert out == "COMPLETE=2\nwarning: some remote text\n"
    assert isinstance(out, str)


def test_stdin_bytes_survive_a_real_local_subprocess_round_trip():
    """End-to-end proof, no network: pipe real bytes through a real child process
    exactly the way `_ssh` now does it (input=<bytes>, no text=True) and confirm no
    CRLF appears -- versus the same payload sent through `text=True`, which does
    corrupt it. This is exactly the director's local verification recipe: the child
    prints `repr()` of the raw bytes it received, so any corruption shows up as a
    literal `\r` in the child's own text output rather than being silently
    re-normalised by the parent's own text-mode read.
    """
    payload = "way_1\nway_2\nway_3\n"
    reader = "import sys; print(repr(sys.stdin.buffer.read()))"

    bytes_mode = subprocess.run(
        [sys.executable, "-c", reader],
        input=payload.encode("utf-8"), capture_output=True, timeout=30,
    )
    bytes_mode_stdout = bytes_mode.stdout.decode("utf-8").strip()
    assert bytes_mode_stdout == repr(payload.encode("utf-8")), (
        "raw bytes must survive the round trip unchanged -- no CR insertion"
    )

    text_mode = subprocess.run(
        [sys.executable, "-c", reader],
        input=payload, text=True, capture_output=True, timeout=30,
    )
    assert "\\r" in text_mode.stdout, (
        "sanity check on the bug itself: text=True input SHOULD still corrupt LF "
        "to CRLF on this platform -- if this fails, the underlying Windows "
        "behaviour changed and the whole premise of the fix needs re-checking"
    )
