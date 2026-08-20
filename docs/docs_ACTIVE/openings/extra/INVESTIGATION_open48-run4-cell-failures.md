# INVESTIGATION — two solo SSH transport drops during the OPEN-48 fourth fleet run

**Slug:** `open48-run4-cell-failures`
**Opened:** 2026-08-19, during the OPEN-48 fourth fleet re-run (`open48_fleet_run4.py`, T03/T04 of
`PLAN_close-all-2026-08-19.md`)
**Status:** post-mortem only — both cells recovered on a single solo retry; no live remedy applied
**Scope:** T-C only, per director instruction 2026-08-19 20:33/20:52. T-D (way/266034056,
levels/archetype diffs, area==200.0 signature) was completed by the director directly and is not
repeated here.

---

## 1. Summary

Two of the twelve cells — `la_rural` and `austin_urban` — died `rc=1` under the main driver
(`open48_fleet_run4.py`, `MAX_PARALLEL=4`) with the identical transport-level signature:

```
stderr: Connection closed by 132.205.2.12 port 22
```

`132.205.2.12` is `speed.encs.concordia.ca` (`REMOTE_HOST`, `v12_cell_pipeline.py:40`). Both failures
are OpenSSH reporting that the remote sshd closed the connection — not a remote command returning a
non-zero exit, but the transport itself dropping mid-command. Both cells were re-run solo (single
`run_cell()` call, no other work queued in that process) and both succeeded on the first solo attempt.
No manual remote cleanup was needed in either case.

| cell | failed at (mtime) | v12_cell_pipeline.py site | stage | remote job existed? | harvestable? | retry result |
|---|---|---|---|---|---|---|
| `la_rural` | 19:42:28 | `:337`, `ship_to_cluster` | shipping — first remote touch | no | no | 144/149 success (job 1283145 + repair 1283440) |
| `austin_urban` | 19:57:30 | `:1042`, `_remote_results_complete` | resumability probe — first remote touch | no | no | 425/425 success (job 1284163) |

---

## 2. `la_rural` — full detail

**Local work before the failure.** Step 1 loaded the seeded cache (no OSM re-fetch). Step 2 classified
149 buildings, 0 Unknown. Step 3 generated 149/149 IDFs in 48.2 s. Both LIVE_SMOKE gates passed
(generation 100.0%, Unknown 0.0%). The failure happened immediately after: `[la_rural] Shipping fleet
to /speed-scratch/o_iseri/fleets/open48_refleet4_la_rural ... fleet size: 149 buildings`, then the
traceback — no `uploading IDFs (tar stream)` line was ever printed, so the tar-stream upload never
started.

**Exact traceback:**

```
File "v12_cell_pipeline.py", line 1115, in run_cell
    ship_to_cluster(idf_manifest, epw_path, remote_fleet_dir, work_base)
File "v12_cell_pipeline.py", line 337, in ship_to_cluster
    _ssh(f"mkdir -p {remote_fleet_dir}/idfs {remote_fleet_dir}/weather {remote_fleet_dir}/out")
File "v12_cell_pipeline.py", line 174, in _ssh
    raise RemoteCommandError(...)
scripts.validation.v12_cell_pipeline.RemoteCommandError: remote command exited 255: mkdir -p /speed-scratch/o_iseri/fleets/open48_refleet4_la_rural/idfs /speed-scratch/o_iseri/fleets/open48_refleet4_la_rural/weather /speed-scratch/o_iseri/fleets/open48_refleet4_la_rural/out
stdout:
stderr: Connection closed by 132.205.2.12 port 22
```

Exit code **255** is `ssh`'s own protocol-level exit for a dropped connection, not an exit code
returned by `mkdir` — the remote command's actual result is unknown; the connection closed before it
could be reported.

**Stage.** This is the very first line of `ship_to_cluster` (`:337`) — before the `fleet.lst`/EPW `scp`
calls, before the IDF tar-stream upload, before `sbatch`. It runs *after* the resumability probe
(`_remote_results_complete`, called at `:1110` just before this branch) had already returned `False`
(0/149 complete — correctly, since nothing had been shipped for this cell yet in this run).

**Remote job status.** None. `sbatch` was never reached. Whether the `mkdir` itself landed
server-side before the connection dropped is unknown and unrecoverable — `_ssh` (per its own
docstring, `:127-147`) discards remote stderr detail beyond what the closed connection reported, and
in this failure mode there is no remote-side log to inspect because no job was ever submitted under
this fleet dir for this attempt.

**Harvestable results.** None. No IDFs were uploaded, no array was submitted, so `out/` under
`/speed-scratch/o_iseri/fleets/open48_refleet4_la_rural` held nothing from this attempt.

**Retry.** Launched as a standalone `run_cell('la_rural', output_subdir='open48_refleet4')` call,
process-isolated from the main driver. *(Disclosure: at launch, three other cells — `austin_centre`,
`la_urban`, `nyc_centre` — were still active under the main driver; the retry was not run in isolation
from all cluster activity, only isolated from the driver's own retry logic. See §4.)* The
resumability probe correctly read 0/149 complete, shipped, `sbatch` job **1283145** submitted
(`array=1-149%32`), all tasks completed, fetched, 5 buildings dropped at the B2 zero-fail tolerance
(zero-area-surface geometry repair artifacts — `way/472960972`, `way/472961034`, `way/472961088`,
`way/472961091`, `way/472961171` — "Temperature out of bounds" EnergyPlus severes, an EnergyPlus-level
degenerate-geometry outcome unrelated to the SSH failure), repair job **1283440**/reroute job
**1283836** handled a further 7-building geometry-repair batch inside that same retry. Final: **144/149
simulated success**. Deliverables copied to
`docs/validations/overAll/results/open48_refleet4/la_rural/`.

---

## 3. `austin_urban` — full detail

**Local work before the failure.** Step 3 generated 425/425 IDFs. Both LIVE_SMOKE gates passed
(generation 100.0%, Unknown 1.2%). Log's last line before the traceback: `[austin_urban] LIVE_SMOKE:
both gates PASS. Proceeding to cluster ship.` — the failure happened in the very next call, which is
the resumability probe, not the shipping step itself.

**Exact traceback:**

```
File "v12_cell_pipeline.py", line 1110, in run_cell
    if _remote_results_complete(osm_ids, remote_fleet_dir):
File "v12_cell_pipeline.py", line 1042, in _remote_results_complete
    out = _ssh(probe, timeout=600, stdin_data="\n".join(osm_ids) + "\n")
File "v12_cell_pipeline.py", line 174, in _ssh
    raise RemoteCommandError(...)
scripts.validation.v12_cell_pipeline.RemoteCommandError: remote command exited 255: cd /speed-scratch/o_iseri/fleets/open48_refleet4_austin_urban/out 2>/dev/null || exit 0; n=0; while read o; do if [ -s "$o/eplusout.sql" ] && grep -q "EnergyPlus Completed Successfully" "$o/eplusout.end" 2>/dev/null; then n=$((n+1)); fi; done; echo COMPLETE=$n
stdout:
stderr: Connection closed by 132.205.2.12 port 22
```

Same signature as `la_rural`: exit 255, connection closed by the remote host, not a remote-command
error.

**Stage.** `_remote_results_complete` (`:1026-1044`) is the T17-H2 resumability check, called at
`:1110` — the *first* remote-touching call of `run_cell`'s cluster branch, reached immediately after
local IDF generation and before `ship_to_cluster` is ever invoked. This call sends the 425 osm_ids
over stdin (the OPEN-57 remedy) with a 600 s timeout; the connection was closed by the remote side
before the probe's `echo COMPLETE=$n` could be returned.

**Remote job status.** None. This was the first cluster interaction of this `run_cell` attempt for
`austin_urban` in `open48_refleet4` — `ship_to_cluster` and `sbatch` were never reached.

**Harvestable results.** None, for the same reason as `la_rural`: nothing had been shipped or
submitted yet under `/speed-scratch/o_iseri/fleets/open48_refleet4_austin_urban` at the time of the
drop.

**Retry.** Launched as a standalone `run_cell('austin_urban', output_subdir='open48_refleet4')` call.
*(Disclosure: at launch, `austin_centre` was still running under the main driver; the retry ran
concurrently with it for roughly the first six minutes before `austin_centre` finished. See §4.)* The
probe correctly read 0/425 complete, shipped, `sbatch` job **1284163** submitted (`array=1-425%32`),
all 425 tasks `COMPLETED`, fetched (9 batches), zero-fail. Final: **425/425 simulated success**.
Deliverables copied to `docs/validations/overAll/results/open48_refleet4/austin_urban/`.

---

## 4. Concurrency at time of failure and at time of retry — stated plainly

Both original failures happened while the main driver held **4 concurrent cells** (`MAX_PARALLEL=4`,
the value pinned by the run-4 launcher specifically because run 2's `MAX_PARALLEL=6` killed two cells
on `scp`/`squeue`). Four concurrent cells did not eliminate transport drops — it reduced their
observed frequency relative to run 2, and, distinctly, `poll_cluster`'s retry loop (§5) absorbed four
further drops of the identical signature without taking down a cell (18:37 on `nyc_centre`, 18:37 on
`la_centre` simultaneously, 19:07 on `la_urban`, 20:30 on the `austin_urban` retry) — see the raw
`squeue`/`sacct` poll lines in each cell's log, e.g. `austin_urban_retry.log:
[20:30:34] squeue count=1 (exit 0) sacct states: Connection closed by 132.205.2.12 port 22` followed by
a clean read on the next 90 s cycle.

Neither retry was run in strict isolation from all other cluster activity: the `la_rural` retry
overlapped with three still-running main-driver cells, and the `austin_urban` retry overlapped with
`austin_centre` for its first ~6 minutes. Both retries nonetheless succeeded on the first attempt — no
second solo attempt was needed for either cell. This document does not use that outcome to argue
concurrency is safe; it is recorded because the director's disposition on retry policy should be made
against what was actually run, not an idealized isolated retry.

---

## 5. Why one call site raised and another self-healed

`_ssh` (`:127-180`) raises `RemoteCommandError` on any non-zero remote exit or timeout unless the
caller passes `allow_fail=True`. Three call sites hit the identical `Connection closed by
132.205.2.12 port 22` signature during this run:

| site | `allow_fail` | wrapped in a retry loop? | outcome when hit |
|---|---|---|---|
| `ship_to_cluster`'s `mkdir -p` (`:337`) | `False` (default) | no — single call | **fatal**, `la_rural` |
| `_remote_results_complete`'s probe (`:1042`) | `False` (default) | no — single call | **fatal**, `austin_urban` |
| `poll_cluster`'s `squeue`/`sacct` polls (`:399`, `:414`) | `True` | yes — `while True`, 90 s cycle | **self-healed**, 4 occurrences, 0 cell losses |

`poll_cluster` already carries the OPEN-54 remedy (`allow_fail=True` plus a surrounding loop that
re-polls rather than concluding on an ambiguous read). `ship_to_cluster`'s initial `mkdir` and
`_remote_results_complete`'s probe do not: both are single-shot, un-retried calls, so an identical
transient transport drop is immediately fatal to the whole `run_cell()` invocation at those two sites,
discarding whatever local work preceded it (48.2 s of IDF generation for `la_rural`; several minutes
for `austin_urban`'s 425-building generation).

---

## 6. Recommendation on retry policy (not applied)

Per the director's instruction, this is a recommendation only — no code change is made or proposed to
raise parallelism, add keepalives, or otherwise touch `v12_cell_pipeline.py` inside this run.

The evidence supports a narrow, structural observation: the two call sites that failed are exactly the
two `_ssh` call sites in the cluster-submission path that (a) run before any remote job exists for
that attempt, and (b) lack the retry-loop pattern that `poll_cluster` already uses successfully. A
retry-wrapped `mkdir` and resumability probe — using the same `allow_fail` + bounded-retry shape already
proven at `poll_cluster` — is a plausible narrow fix, consistent with OPEN-54's original remedy
direction. This is named as a candidate only; the director's evidence review and disposition are
required before any such change is made, and it must not be made mid-fleet-run for the same
single-variable-comparison reason `INVESTIGATION_open-54_ssh-unchecked-exit.md` §6 gave for not
patching `v12_cell_pipeline.py` during run 3.

Both failures in this run were fully recoverable with a single solo retry, no orphaned remote state,
and no manual cleanup — the retry ceiling of "up to 3 attempts" specified by the director was not
needed; both cells recovered on attempt 1 of 3.

---

## 7. Disposition

- `la_rural`: 144/149 (5 dropped at B2 tolerance, cause unrelated to the SSH failure — see §2).
- `austin_urban`: 425/425.
- Both are recorded here as transport-layer post-mortems, not code defects requiring an in-run fix.
- Fleet-wide diff findings (levels, archetype flips, the area==200.0 signature, way/266034056) were
  produced directly by the director and are not restated in this document.
