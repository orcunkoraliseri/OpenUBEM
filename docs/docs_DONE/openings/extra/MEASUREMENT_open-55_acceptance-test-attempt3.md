# OPEN-55 acceptance test on `nyc_suburban` — attempt 3 (instrumented) — 2026-08-19

## Result up front

**Buildings simulated under T01's code: 0.** The prediction (71 divergences → 0) is still neither
confirmed nor falsified. This attempt did not fail silently or ambiguously — it failed cleanly, with
a captured exit code and a verbatim remote error, on the **first-ever SSH call this run made**, to a
**brand-new remote fleet directory that had never been shipped to**. It is a **second, confirmed
occurrence of the `Unmatched '.` tcsh fault** first seen in attempt 1 on 2026-08-19, at the identical
code location (`_remote_results_complete` → `_ssh`, `scripts/validation/v12_cell_pipeline.py:1082` →
`:1014`), on a command built from the same 1,589-entry osm_id list, of near-identical length.

Per the dispatch's hard requirement 4, this is reported prominently and **no fourth attempt was
made**.

## What this attempt fixed relative to attempts 1 and 2

1. **Fresh output_subdir / fresh remote fleet dir.** `open48_refleet3_t02a3` (work base
   `%TEMP%/ubem_validation/open48_refleet3_t02a3/nyc_suburban`, remote fleet dir
   `/speed-scratch/o_iseri/fleets/open48_refleet3_t02a3_nyc_suburban`). Verified **absent** on the
   cluster before launch (`ls` returned "No such file or directory") and verified **still absent**
   after the crash — so the 1,589 stale `open48_refleet3_nyc_suburban/out/*` directories from
   2026-08-18 18:08 could not possibly be scored as this run's output, by construction, not by
   inspection after the fact.
2. **Frozen input re-verified and seeded by copy, not move.** Source
   `%TEMP%/ubem_validation/open48_refleet3/nyc_suburban/01_buildings.gpkg` MD5
   `1198ed01bfd3b4463e50da0ae39d8e27` (matches the value recorded in attempts 1/2). Copied into the
   new work base; copy's MD5 re-verified identical before proceeding. Confirmed from the run's own
   log: `Step 1: loading cached GDF from ...01_buildings.gpkg` — **no OSM fetch**.
3. **Instrumented launcher** (`scripts/validation/open48_t02_attempt3.py`, new file, harness-only —
   `openubem/` untouched):
   - Log opened in **append** mode only (`nyc_suburban.log`), never truncated.
   - Child's exit code captured the instant `Popen.poll()` returned non-`None` and written to a
     dedicated `nyc_suburban.EXITCODE` file (append mode).
   - Child launched as `python -u -c ...` (unbuffered), stdout+stderr both redirected to the same
     append-mode log.
   - A separate `nyc_suburban.heartbeat.log`, appended to every 60s while the child was alive
     (`alive pid=... elapsed=...min log_bytes=...`), plus explicit launch/exit lines.
   - Result: this attempt's failure is fully explained — no ambiguity like attempt 2's silent death.

## Timeline (all times 2026-08-19, from the run's own log/heartbeat)

- `09:09:15` — launcher starts, MD5 verified, GDF seeded, child launched (pid 45756).
- `09:09:15`–`09:12:30` — Step 1 (cache load, 1,589 buildings, no fetch), Step 2 (classify: 290
  Unknown; distribution `MidriseApartment 979 / SmallOffice 316 / OpenUBEMUnknown 290 / Courthouse 2 /
  QuickServiceRestaurant 1 / MediumOffice 1` — exact match to attempts 1/2 and the pre-registered
  baseline), Step 3 (**1,589/1,589 IDFs generated in 199.6 s**, faster than attempt 1's 239.6 s).
- `09:12:xx` — LIVE_SMOKE gates: generation 100.0% (≥95% PASS), Unknown 18.3% (<20% PASS). Both PASS,
  identical to attempt 1.
- `09:12:40` — crash: `RemoteCommandError` from `_remote_results_complete`'s `_ssh` probe call.
  `child exited rc=1 elapsed=3.4min`. `EXITCODE` file: `1`.
- Heartbeat log shows three clean `alive` lines (60s cadence) then the `EXITED` line — the
  instrumentation worked exactly as designed; there was no silent gap to bound.

## The fault, verbatim

**Exit code: 1** (captured in `nyc_suburban.EXITCODE`, written by the launcher the instant the child
process exited).

**Remote stderr (verbatim, complete):**
```
Unmatched '.
```
(a single line — no other stderr text, no stdout).

**Command that triggered it:** `_remote_results_complete`'s single-line probe —
```
cd /speed-scratch/o_iseri/fleets/open48_refleet3_t02a3_nyc_suburban/out 2>/dev/null || exit 0; n=0; for o in way_605951159 way_610017055 ... [1,589 space-separated osm_id tokens] ... way_1110654035; do if [ -s "$o/eplusout.sql" ] && grep -q "EnergyPlus Completed Successfully" "$o/eplusout.end" 2>/dev/null; then n=$((n+1)); fi; done; echo COMPLETE=$n
```
wrapped as `ssh o_iseri@speed.encs.concordia.ca "bash -lc '<probe>'"`.

**Exact command string length, measured programmatically from this run's own captured traceback**
(not estimated):
- probe body (the string passed to `_ssh`): **23,166 characters**
- `bash -lc '<probe>'` wrapper: **23,177 characters**
- full three-argument `ssh` argv, space-joined: **23,213 characters**

All well under Windows' `CreateProcess` ~32,767-character limit, and essentially identical to attempt
1's independently-measured 23,171-character probe on the identical 1,589-entry osm_id list against
the *original* `open48_refleet3_nyc_suburban` fleet dir. Same list, same code, same shape, two
different remote fleet-dir names, two failures with the identical error text. **This reads as a
transient or intermittent tcsh/SSH-session fault, not a static length or content bug** — the same
conclusion attempt 1 reached, now with a second independent data point.

## Why this rules out both of this attempt's own guard conditions

- **Not staleness:** the remote fleet dir `open48_refleet3_t02a3_nyc_suburban` was confirmed absent
  both before and after this run. Nothing was shipped, nothing was scored as a result. Zero risk of a
  stale zero being reported as a pass.
- **Not silent death:** exit code 1 was captured to disk within the same second the child exited;
  the heartbeat log independently corroborates the child was alive and progressing normally up to
  09:12:15, then gone by 09:12:40 with a clean traceback, not a hang.

## Control 1 (non-vacuity) — re-derived from this attempt's own artifacts, PASSED

Re-run directly against this run's own seeded copy of the GDF
(`open48_refleet3_t02a3/nyc_suburban/01_buildings.gpkg`), using the unmodified `step1_fetch` +
`step2_classify_enrich` (same functions the crashed run itself called; deterministic per OPEN-49's
per-building seed, so this reproduces exactly what was in memory when the run died — not a number
carried forward from attempt 1's write-up):

- 1,589 fetched, 290 classified `OpenUBEMUnknown` — exact match to the pre-registered baseline.
- `equipment_w_m2` (the 290 Unknown rows): min **2.590187**, median **9.152907**, max **16.066840**.
  **0/290 exceed the [2.58, 16.15] ceiling.**
- `occupant_m2_per_person`: min 4.743670, median 31.069510, max 51.049642 (inside [4.65, 51.10]).
- `lighting_w_m2`: min 3.454098, median 10.869178, max 18.246370 (inside [3.44, 18.30]).

These figures are bit-identical to attempt 1's independently-derived numbers (min 2.590 / median
9.153 / max 16.067), which is the expected and correct outcome of OPEN-49's per-building determinism —
not evidence of carrying the number forward, but evidence the screen's effect on the draws is stable
run to run. **Control 1 passes.**

## Control 2, primary divergence count, EUI movement — NOT EVALUABLE

No simulation ran (0 buildings), so:
- **Control 2** (classified/non-Unknown buildings unchanged vs run 3): not evaluable — no results to
  compare.
- **Primary** (divergence count, target 0/290): not evaluable. Divergence count **before** T01, from
  the original run-3 log, remains 71 (unchanged, not re-verified again in this attempt — already
  confirmed twice).
- **EUI movement**: not evaluable — no simulation output exists to compute an EUI from.

**Do not aggregate to a fleet figure. This entry does not restate 157.1 kWh/m².**

## What was NOT done (deliberately, per the hard rules)

- No fourth attempt. Hard requirement 4 and the plan's own stop-point rule both apply: a second
  occurrence of this exact fault is reported, not retried around.
- No workaround sent as a bare command, no code fix attempted on `_ssh` or `_remote_results_complete`
  — out of this task's scope (`openubem/` and the shared pipeline harness were both left untouched by
  design; only a new, additive launcher script was written).
- No register edit, no director-prompt edit, no `PROJECT_CHECKLIST.md` edit — another executor holds
  the register.
- No git write command.
- The pre-existing cluster job `1274884` (`4J_s4_le`, owned by this project's own user, presumably a
  concurrent task in this same multi-agent pass) was left untouched. Job `1266911`/`4J_s4_pe` was not
  present in `squeue` output for this account at the time of checking and was not touched.

## Artifacts

- `scripts/validation/open48_t02_attempt3.py` — new instrumented single-cell launcher (harness only,
  no `openubem/` changes).
- `C:\Users\o_iseri\AppData\Local\Temp\open48_t02_attempt3\nyc_suburban.log` — full run log, append
  mode, untouched by any truncation.
- `C:\Users\o_iseri\AppData\Local\Temp\open48_t02_attempt3\nyc_suburban.heartbeat.log` — 60s-cadence
  heartbeat, launch line, exit line.
- `C:\Users\o_iseri\AppData\Local\Temp\open48_t02_attempt3\nyc_suburban.EXITCODE` — contains `1`.
- `%TEMP%/ubem_validation/open48_refleet3_t02a3/nyc_suburban/01_buildings.gpkg` — this attempt's own
  seeded copy, MD5-verified `1198ed01bfd3b4463e50da0ae39d8e27`.
- `%TEMP%/ubem_validation/open48_refleet3_t02a3/nyc_suburban/step3/03_idf_manifest.parquet` —
  1,589/1,589 `generation_status == success`.

## Recommendation for the director (not acted on — director opens register IDs, not this task)

Two independent, reproducible occurrences of `_ssh` raising `Unmatched '.` on this specific
`_remote_results_complete` probe call, both on `nyc_suburban`'s 1,589-entry osm_id list, on two
different remote fleet-dir names, with near-identical command lengths (23,171 and 23,166/23,177/
23,213 chars depending on what is measured) — both well under the Windows argv cap. This is now a
**repeated, not one-off, fault**, and it sits directly in the only code path (`_remote_results_complete`
→ `_ssh`) that OPEN-55's own acceptance test must pass through before any simulation can occur.
Suggest a register entry for the tcsh/SSH-session-transient fault itself, independent of and prior to
any further OPEN-55 retry, since three attempts have now spent wall-clock time on local work
(IDF generation, ~3–4 min each) that is discarded every time this one remote call fails.
