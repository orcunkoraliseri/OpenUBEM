# FIX — open-52 pytest --basetemp

> **Slug:** `open-52_pytest-basetemp` · **Date:** 2026-08-18 · **Register item:** OPEN-52
> **Task:** T01 of `implemenation/PLAN_five-items-2026-08-18.md`.

---

## 1. Verdict

**OPEN-52 does NOT close and the remedy specified by the plan (delete `addopts`) was applied,
tested, and then reverted, because it broke the mandatory regression check on this machine.**

The collision mechanism is real and was reproduced directly (§3). But this session also discovered a
second, independent, currently-active fact that the plan did not anticipate: on this machine, right now,
pytest's own default per-session temp root — `C:\Users\o_iseri\AppData\Local\Temp\pytest-of-o_iseri` —
is itself inaccessible (`PermissionError: [WinError 5] Access is denied`, confirmed even to `icacls`
run directly against it). Deleting the `addopts` line trades the two-session collision risk for total
breakage of every test that uses `tmp_path`, because pytest's fallback default cannot be reached at all
(§4). `pyproject.toml` has been restored to its original state; **no net code change was made.**

This is not a documentary-reasoning question (§2 found no written reason for the pin) — it is a live,
reproducible fact about this machine's temp directory, discovered only because the remedy was actually
tested rather than assumed safe.

---

## 2. Step 1 — was there a documented reason for the pin?

`git show fe05509 -- pyproject.toml` shows the `[tool.pytest.ini_options]` block, including
`addopts = "--basetemp=.pytest_tmp"`, added in one hunk alongside unrelated dependency and
package-data changes. The commit message is a generic feature-commit summary
(*"feat: implement climate zone assignment, building attribute enrichment, parallel EnergyPlus runner,
and results parsing/carbon components"*) with **no line naming `basetemp` or explaining it.**

`docs/docs_main/docs_step-2-1/PLAN_step-2-1-implementation.md:263` (T11's progress-log entry, same
day, 2026-06-10) lists the artifact — *"`pyproject.toml` (pytest ini: addopts --basetemp,
package-data *.csv added)"* — with no justification either.

Repo-wide search (code, scripts, `.gitignore`, `docs_DONE` included) for `.pytest_tmp` and `basetemp`
turned up: `.gitignore:50` ignoring `.pytest_tmp/` (a consequence of the pin, not a reason for it), and
otherwise only documentation/register prose about this exact defect (all written 2026-08-13 or later,
i.e. after the collision was already diagnosed). **No script, test, CI config, or fixture reads from or
depends on the literal path `.pytest_tmp`.** No documentary reason for the pin survives in the repo.

---

## 3. Step 2 — reproduce the collision (before leg)

Three test designs were tried, in the session scratchpad
(`C:\Users\...\scratchpad\open52\test_collision.py`), against `.venv/Scripts/python.exe -m pytest
<file> --basetemp=.pytest_tmp -v` run twice concurrently from the repo root, session B started 3 s
after session A.

**Design 1** (write one file, sleep 15 s, assert it still exists) — **both sessions: 2 passed.** Did
not fail, but directory census proved the wipe fired anyway: only one `test_slow_writer0` numbered
directory existed after the run (not two, one per session), meaning session B's first `tmp_path` call
deleted session A's entire basetemp tree — the assertion just didn't catch it, because pytest's
subdirectory numbering is deterministic and B silently repopulated the same path before A's check ran.

**Design 2** (write to a nested `step3/` dir at t=0, sleep 8 s, write again at t=8, assert both exist)
— **both sessions: 2 passed** again, same masking effect.

**Design 3** (busy-loop writing `f{i}.txt` into `step3/` continuously for 15 s, no sleep, catching
`OSError`/`AssertionError` per iteration) — **this caught it.** Raw output, session B (the later
starter):

```
ERROR at setup of test_slow_writer
...
E   FileExistsError: [WinError 183] Cannot create a file when that file already exists: 'C:\\Users\\o_iseri\\Desktop\\OpenUBEM\\.pytest_tmp'
...
PytestWarning: (rm_rf) error removing \\?\C:\Users\o_iseri\Desktop\OpenUBEM\.pytest_tmp\test_slow_writer0\step3
  <class 'OSError'>: [WinError 145] The directory is not empty: '...\.pytest_tmp\test_slow_writer0\step3'
PytestWarning: (rm_rf) error removing \\?\C:\Users\o_iseri\Desktop\OpenUBEM\.pytest_tmp\test_slow_writer0
  <class 'OSError'>: [WinError 145] The directory is not empty: '...\.pytest_tmp\test_slow_writer0'
PytestWarning: (rm_rf) error removing \\?\C:\Users\o_iseri\Desktop\OpenUBEM\.pytest_tmp
  <class 'OSError'>: [WinError 145] The directory is not empty: '...\.pytest_tmp'
======================== 6 warnings, 2 errors in 1.13s ========================
```

Session A (the earlier starter, actively writing when B's wipe landed): **2 passed, 15.17s**,
unaffected. Mechanism: B's `rm_rf(.pytest_tmp)` walked the tree to delete it while A was actively
creating new files inside `step3/` — Windows' non-atomic recursive delete against a live writer failed
partway (`WinError 145`, directory not empty), leaving `.pytest_tmp` partially present, so B's
subsequent `os.mkdir(.pytest_tmp)` then failed with `FileExistsError [WinError 183]`. Different failure
signature from the register's original incident (`OSError: Cannot save file into a non-existent
directory`) but the same root cause: two sessions sharing one fixed, non-per-session basetemp.
**Collision reproduced.**

---

## 4. Step 3/4 — remedy applied, and what the after leg found

`addopts = "--basetemp=.pytest_tmp"` was deleted from `pyproject.toml` (both `tmp_path_retention_*`
keys kept), matching the plan's specified remedy exactly.

**Concurrency proof (after leg, workaround needed — see below):** re-running Design 3 concurrently
with no `--basetemp` flag against the real default temp root failed immediately, **both sessions**,
with:

```
E   PermissionError: [WinError 5] Access is denied: 'C:\\Users\\o_iseri\\AppData\\Local\\Temp\\pytest-of-o_iseri'
```

This directory predates this session (`ls -la` timestamp: **Apr 1**, months before OPEN-52 was ever
opened) and is inaccessible even to `icacls` run directly against it (`Access is denied` / `Get-Acl:
Attempted to perform an unauthorized operation`) — a Windows-level ACL lockout unrelated to this
plan's remedy, out of this plan's file layout, and not something this session has the rights to repair
(icacls itself was refused).

To still test the *causal claim* — that removing a **shared, fixed** basetemp stops the collision —
`TEMP`/`TMP` were redirected to an accessible scratchpad directory for the invocation only (this
changes where pytest's own default lands, it does not reintroduce `--basetemp`). Result:

```
Session A: 2 passed in 15.13s
Session B: 2 passed in 15.14s
```

and the temp tree shows pytest assigned each session its **own** numbered directory —
`pytest-of-o_iseri/pytest-0` and `pytest-of-o_iseri/pytest-1` — confirming pytest's default
per-session mechanism is genuinely collision-free once it can be reached. **The remedy is correct in
principle.**

**But the mandatory regression check fails without the redirect.** Per the plan's "How to test":
`.venv/Scripts/python.exe -m pytest tests/test_sim_integration.py` alone, with `addopts` removed and
no `TEMP` override (i.e. exactly what a normal invocation on this machine would do):

```
ERROR tests/test_sim_integration.py::test_synthetic_fleet_full_annual - PermissionError...
ERROR tests/test_sim_integration.py::test_adversarial_corrupted_idf_gives_failed_fatal
ERROR tests/test_sim_integration.py::test_adversarial_missing_epw_gives_valueerror
ERROR tests/test_sim_integration.py::test_adversarial_precompleted_work_dir_gives_success_cached
ERROR tests/test_sim_integration.py::test_adversarial_timeout_gives_failed_timeout
ERROR tests/test_sim_integration.py::test_determinism_same_host_reproducible
========================= 1 passed, 6 errors in 1.77s =========================
```

**1 passed, 6 errors — not the required 7 passed.** Every `tmp_path`-using test breaks, because the
fixed repo-relative basetemp was, on this machine, incidentally shielding every test run from an
unrelated, already-broken OS temp directory. Whatever the pin's original 2026-06-10 rationale was (§2
found none written down), this session has now observed a concrete, currently-active reason a
repo-relative fixed basetemp is useful on this box: it avoids a global Windows temp path that can
independently go bad.

**`pyproject.toml` was reverted to its original content** (the `addopts` line restored) as a direct
consequence of this finding — leaving the broken state in place would fail rule 7 (before/after
evidence: the after leg must actually pass) and would break every other task's test evidence on the
remainder of this plan.

**Confirmation the repo is back to its original, working state:**

```
$ .venv/Scripts/python.exe -m pytest tests/test_sim_integration.py -v
...
======================== 7 passed in 67.14s (0:01:07) =========================
```

Re-run once more for a second data point: `7 passed in 68.08s`. Both runs are in the 60-70s range
matching the register's four prior sequential director runs (66.38/65.99/66.57/66.68s), confirming the
file is still green and the wall-time signature (not the 12.67s flake shape) is intact. No stray
`.pytest_tmp` directory was left behind (`.pytest_tmp` removed after each experiment; current state:
absent, gitignored).

---

## 5. Net effect on the repository

**`pyproject.toml` is byte-identical to its state before this task.** The `addopts` line was removed,
tested, found to break the mandatory regression check on this machine, and restored. No file in the
plan's edit list carries a net diff from T01.

---

## 6. Can OPEN-52 close?

**No.** The collision is real (§3, reproduced directly with a hard filesystem error). The specified
remedy is mechanically correct (§4, proven via the TEMP-redirect experiment) but **cannot be safely
applied on this machine as a bare line deletion**, because doing so silently substitutes one failure
mode (shared-basetemp collision, only manifests under concurrent pytest, previously undetected for
months) for a worse one (total `tmp_path` breakage, manifests on every single-session run) due to an
unrelated, pre-existing Windows ACL lockout on `pytest-of-o_iseri`.

Register disposition for the director: this item now has **two open sub-questions**, not one —
(a) the original collision (still real, still worth fixing), and (b) the newly-discovered
`pytest-of-o_iseri` lockout, which is a prerequisite blocker for (a)'s remedy and needs either
administrative repair of that directory's ACL or a different remedy shape (e.g. a *per-session unique*
but still explicit basetemp, rather than deleting the flag outright) — a choice this session did not
make, since it is a design decision outside a measurement/config task's authority.

---

## 7. Discipline note

Per hard rule 3, only one pytest session ran at a time in this repo throughout this task, with the
sole exception of the deliberate two-session experiments in §3 and §4, both run against the scratchpad
test file only and both torn down (no session left alive) before the next step began.
