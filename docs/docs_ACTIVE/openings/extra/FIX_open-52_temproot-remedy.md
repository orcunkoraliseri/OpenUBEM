# FIX — OPEN-52 temp-root remedy (ruling `3a`)

> **Slug:** `open-52_temproot-remedy` · **Date:** 2026-08-18 · **Register item:** OPEN-52
> **Task:** T01 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`.

---

## 1. Verdict

**OPEN-52 CLOSES.** Ruling `3a` (§4.1 of the plan) — move pytest's temp root inside the repository
and let pytest number it per session, via `PYTEST_DEBUG_TEMPROOT`, rather than a fixed
`--basetemp` — was implemented exactly as specified. All four required verifications (A–D) passed
with real output, including a negative control that reproduced the original collision before the
fix and confirmed its absence after.

---

## 2. The two file changes

**`pyproject.toml`** — one line deleted, nothing else touched:

```diff
 [tool.pytest.ini_options]
 testpaths = ["tests"]
 tmp_path_retention_policy = "failed"
 tmp_path_retention_count = 3
-addopts = "--basetemp=.pytest_tmp"
 markers = [
     "slow: marks tests as slow (integration / live-network)",
     "energyplus: marks tests that require the EnergyPlus 23.1 binary",
 ]
```

Pre-task hash: `8d0ff72a5a2bb7ffb82cef0dd58caa9138ba339106d81235494ded43b7b973ed`.
Post-task hash: `b73222eb41419d847db5d6c8d77f1c211073f6feb788e8b16e4ccedb89530e84`.

**`conftest.py`** — new file at the repository root, the only file this plan authorises there:

```python
import os
from pathlib import Path

_TEMPROOT = Path(__file__).resolve().parent / ".pytest_tmp"
_TEMPROOT.mkdir(exist_ok=True)
os.environ["PYTEST_DEBUG_TEMPROOT"] = str(_TEMPROOT)
```

Hash: `deafcdae13e69c1d077e268f7e2c98e8f15e4bc072442bc63c770ecf9eb35448`.

`conftest.py` is imported by pytest during collection, well before any test's first call to
`getbasetemp()` — confirmed by reading `_pytest/tmpdir.py` directly (pytest 9.0.3, lines 140-218):
`PYTEST_DEBUG_TEMPROOT` is read lazily, only inside `getbasetemp()`, only on the branch taken when
`_given_basetemp is None` (i.e. no explicit `--basetemp`). Setting the env var at conftest import
time is early enough — verified empirically in Verification A, not assumed.

---

## 3. Verification A — the root actually moved

Ran one small, self-contained test file that uses `tmp_path`:

```
$ .venv/Scripts/python.exe -m pytest -q tests/test_results_denominator.py
.......                                                                  [100%]
7 passed in 0.68s
```

Directory census immediately after (files under 2 minutes old):

```
.pytest_tmp
.pytest_tmp/pytest-of-o_iseri
.pytest_tmp/pytest-of-o_iseri/pytest-0
.pytest_tmp/pytest-of-o_iseri/pytest-0/test_well_formed_eio_changes_e0
```

Resolved absolute path: `C:\Users\o_iseri\Desktop\OpenUBEM\.pytest_tmp\pytest-of-o_iseri\pytest-0\`
— matches `<repo>/.pytest_tmp/pytest-of-<user>/pytest-<n>/` exactly, as the ruling specified.

---

## 4. Verification B — the locked directory is never touched

`%LOCALAPPDATA%\Temp\pytest-of-o_iseri` exists on this machine (it predates this task and is the
access-denied directory named in `extra/FIX_open-52_pytest-basetemp.md`):

```
$ powershell -Command "Test-Path 'C:\Users\o_iseri\AppData\Local\Temp\pytest-of-o_iseri'"
True
```

Its `LastWriteTime`, checked immediately after Verification A's run:

```
$ powershell -Command "(Get-Item '...\pytest-of-o_iseri').LastWriteTime; Get-Date"
April 1, 2026 10:21:05 AM
August 18, 2026 2:40:56 PM
```

The directory's last write predates today's run by over four months. Confirmed unmodified: the fix
never causes pytest to reach this path (the `PYTEST_DEBUG_TEMPROOT` env var short-circuits the
`tempfile.gettempdir()` fallback that would otherwise resolve here).

---

## 5. Verification C — the collision is gone (with a real "before")

Reproduced the predecessor's Design-3 busy-loop test (`extra/FIX_open-52_pytest-basetemp.md` §3):
continuous writes into a `tmp_path` subdirectory for 15s, no sleep, session B started 3s after
session A. Placed at `scratchpad/open52/test_collision.py` (gitignored, same location the
predecessor used) so pytest's rootdir/config discovery finds `pyproject.toml` correctly — an
initial attempt from outside the repo tree picked the wrong rootdir and had to be redone.

This experiment was run twice. The first pass (before Verification D) produced the same evidence
described below, but `tmp_path_retention_policy = "failed"` cleaned up its passed-test numbered
directories once the full-suite run (Verification D) allocated and finished its own session
directories — by the time D completed, `.pytest_tmp/pytest-of-o_iseri/` held no numbered
directories at all. The experiment was **redone after D**, with nothing else using pytest, and it
is this second run's output that is quoted below — captured immediately, before anything else could
touch `.pytest_tmp` again.

**Negative control — old config, reproduced.** `addopts = "--basetemp=.pytest_tmp"` was
temporarily restored (`pyproject.toml` hash back to `8d0ff72a...`), `.pytest_tmp` cleared, then two
concurrent sessions run, session B started 3s after session A:

```
Session A: 1 passed in 17.22s

Session B:
  PytestWarning: (rm_rf) error removing ...\.pytest_tmp\test_busy_writer0\step3
    OSError: [WinError 145] The directory is not empty
  PytestWarning: (rm_rf) error removing ...\.pytest_tmp\test_busy_writer0
    OSError: [WinError 145] The directory is not empty
  PytestWarning: (rm_rf) error removing ...\.pytest_tmp
    OSError: [WinError 145] The directory is not empty
  ERROR scratchpad/open52/test_collision.py::test_busy_writer - FileExistsError...
  3 warnings, 1 error in 0.89s
```

Same failure signature as the predecessor's original finding (`FileExistsError [WinError 183]`
cascading from `rm_rf`'s `OSError [WinError 145]`), and identical to this task's own first attempt
at this control. **Collision reproduced twice — the "before" is real, not assumed.**

**After leg — fix restored.** `addopts` removed again (`pyproject.toml` hash back to
`b73222eb...`, confirmed on disk), `.pytest_tmp` cleared, same two-session design re-run
immediately. The test writes its own resolved `tmp_path` to a durable, pid-tagged log file (outside
the numbered directory that `tmp_path_retention_policy = "failed"` would otherwise clean up on a
pass), so the two sessions' destinations could be read straight off disk right after both completed
— before any later pytest invocation could clean them up:

```
Session A: 1 passed in 17.67s
Session B: 1 passed in 17.71s

pid13588_basetemp_log.txt -> ...\.pytest_tmp\pytest-of-o_iseri\pytest-1\test_busy_writer0
pid38108_basetemp_log.txt -> ...\.pytest_tmp\pytest-of-o_iseri\pytest-0\test_busy_writer0
```

Both sessions passed. Each landed in its own numbered directory (`pytest-0` vs `pytest-1`) with no
error, no warning, no collision. **The fix is confirmed, not just theorised — before and after both
measured on the same machine, same test design, with the "after" evidence read directly off disk
immediately after the run.**

---

## 6. Verification D — nothing regressed

Full suite, run alone, in the foreground, to completion (no other pytest process running,
confirmed via `tasklist` immediately before):

```
$ .venv/Scripts/python.exe -m pytest -q tests/
1875 passed, 55 skipped, 11 warnings in 1079.75s (0:17:59)
```

Matches the pinned baseline (§4.2 of the plan) exactly: `1875 passed, 55 skipped`, 0 failed,
0 errors. The tool's 10-minute per-call timeout was exceeded (run took ~18 min); the process
continued running to completion in the background under the harness's own supervision — not
deliberately backgrounded, and no conclusion was written until the real final line was read from
the completed run's output.

---

## 7. Two alternatives, rejected — recorded per the plan so nobody re-proposes them

- **(a) Delete `addopts` and change nothing else.** Proven blocked on this machine independently
  by this task's own negative-control setup (§5) and previously by
  `extra/FIX_open-52_pytest-basetemp.md` (`tests/test_sim_integration.py` gave `1 passed, 6 errors`,
  all `PermissionError [WinError 5]` on the locked `pytest-of-o_iseri`).
- **(b) Repair the ACL on `pytest-of-o_iseri`.** Rejected: needs administrator rights this session
  does not have; is machine-state living outside the repository, so a clean checkout inherits none
  of it; and `icacls` run directly against that directory is itself access-denied, so there is no
  evidence the repair would even succeed.

---

## 8. Net effect on the repository

- `pyproject.toml`: `addopts = "--basetemp=.pytest_tmp"` removed. `testpaths`,
  `tmp_path_retention_policy`, `tmp_path_retention_count` unchanged.
- New file `conftest.py` at the repository root (§2).
- `.pytest_tmp/` remains the temp root, now per-session-numbered rather than fixed and wiped.
  Already gitignored (`.gitignore:50`) — no new git-visible artifact.
- No other file touched. No production code changed.

---

## 9. Discipline note

Per hard rule 6, only one pytest session ran at a time throughout this task, with the sole,
authorised exception of Verification C's deliberate two-session experiments (both legs), each run
only against the scratchpad test file and both torn down before the next step began.
