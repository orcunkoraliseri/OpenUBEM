# MEASUREMENT — OPEN-55 acceptance test, attempt 4 (2026-08-19)

**Executor.** Fresh Sonnet session, `implemenation/previous/PLAN_close-all-2026-08-19.md`, T01–T02.
**Result in one line: the acceptance test RAN, completed, and PASSED all three pre-registered
controls — 0 divergences against a pre-fix baseline of 71.**

---

## 1. What ran

Launcher: `scripts/validation/open48_t02_attempt4.py` (copy of `open48_t02_attempt3.py`,
`NEW_SUBDIR = "open48_refleet3_t02a4"`, run dir `%LOCALAPPDATA%\Temp\open48_t02_attempt4`).

Preflight, all confirmed before the run:
- Frozen source GDF `%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet3\nyc_suburban\01_buildings.gpkg`
  present, MD5 `1198ed01bfd3b4463e50da0ae39d8e27` — matches the expected value and run-2/run-3's
  original, byte-identical.
- Seeded copy at `...open48_refleet3_t02a4\nyc_suburban\01_buildings.gpkg` re-verified same MD5
  post-copy.
- Local subdir `open48_refleet3_t02a4` and remote fleet dir
  `/speed-scratch/o_iseri/fleets/open48_refleet3_t02a4_nyc_suburban` both confirmed **absent**
  before launch (remote checked via `_ssh`), so no stale directory from attempts 1–3 could be
  scored as this run's output.

Run, foreground, `run_cell('nyc_suburban', output_subdir='open48_refleet3_t02a4')`:
1. Local: cached GDF load (no OSM re-fetch), classify, enrich, IDF generation —
   **1,589/1,589 IDFs in 295.0 s**.
2. LIVE_SMOKE gates: generation 100.0 % (≥95 % PASS), Unknown 18.3 % (<20 % PASS).
3. Remote completeness probe (the OPEN-57 fix's first real exercise on this fleet): read back
   correctly as `0/1589` (fresh dir, nothing to reuse) — **no `Unmatched '.` fault, no CRLF-zero
   fault.** This is the first time this probe has ever completed cleanly on a 1,589-id fleet.
4. Ship (tar stream), `sbatch --array=1-1589%32`, job **1274983**, polled every 90 s until all
   1,589 array tasks read `COMPLETED` in `sacct`.
5. Fetch: 1,589 `.end` files in 32 batches. `verify_and_repair`: **zero-fail — all 1,589
   buildings completed successfully** (no repair needed).
6. Simulation manifest: **1,589/1,589 success, 0 failed.**
7. Step 5 / gates report written to
   `docs/validations/overAll/results/open48_refleet3_t02a4/nyc_suburban/v12_nyc_suburban_gates_report.txt`
   (10 files copied there).

Total wall time: 32.0 min. Exit code **0**. No STOP was raised at any point — the remote probe did
not fault a second time, so §-condition 1 of the dispatch ("if it raises again, capture stderr and
STOP") does not apply; nothing to report there.

---

## 2. The three pre-registered controls

**Control 1 — classification unchanged by the screen.** The cell's archetype histogram, re-derived
independently on this run's own seeded input (not carried over from attempt 3):

```
MidriseApartment          979
SmallOffice               316
OpenUBEMUnknown           290
Courthouse                  2
QuickServiceRestaurant      1
MediumOffice                1
```

Bit-identical to the pre-registered baseline and to attempts 1 and 3. **PASS.** (Bit-identity is
the expected consequence of OPEN-49's per-building determinism, not evidence of a copied number —
this run drew from a freshly seeded, independently classified GDF.)

**Control 2 — the primary result: divergence count among the 290 Unknown buildings.**
Pre-fix baseline (run 3, original code): **71 of 290** Unknown buildings diverged
(`CalcHeatBalanceInsideSurf` temperature out of tolerance 16, `ZERO-FAIL: 71 failures exceed
tolerance ... STOP`).

This run, same 290 Unknown buildings, screened code: **0 failures, 0 divergences** —
`verify_and_repair` reported *"Zero-fail: all 1,589 buildings completed successfully"* and the
simulation manifest recorded **1,589/1,589 success, 0 failed**. Since 0 is a subset of "all
buildings", it is in particular 0 of the 290 Unknown buildings.

**71 → 0. PASS**, and not a marginal one — the prediction was "substantially below 71" and the
measured value is the floor of that range.

**Control 3 — no classified building regressed.** 1,299 classified buildings (1,589 − 290
Unknown) simulated. Total failures across the whole cell: **0**. Zero failures among the
classified subset. **PASS**, matching run 3's own zero-failure result for classified buildings.

---

## 3. Drawn equipment-density distribution, before and after the screen

**Before (unscreened, all 29 archetypes, run-3/OPEN-49 code — from
`extra/PROPOSAL_open-55_unknown-pde-bounds.md` §3, uniform draw over the full donor pool):**

| column | bound | median draw |
|---|---|---:|
| `equipment_w_m2` | `[2.58, 5381.96]` | **2,692.27 W/m²** |
| `occupant_m2_per_person` | `[4.65, 464.52]` | **234.6 m²/person** |

**After (B+ screen, this run's own actual draws — re-derived independently from the seeded
`01_buildings.gpkg` used in this run, same code path the cluster simulated):**

| column | bound | min | median | max |
|---|---|---:|---:|---:|
| `equipment_w_m2` | `[2.58, 16.15]` | 2.590187 | **9.152907** | 16.066840 |
| `occupant_m2_per_person` | `[4.65, 51.10]` | 4.743670 | 31.069510 | 51.049642 |
| `lighting_w_m2` | `[3.44, 18.30]` | 3.454098 | 10.869178 | 18.246370 |

0/290 Unknown buildings exceed the new equipment ceiling. Median equipment draw fell from
**2,692.27 W/m² to 9.15 W/m²** — a ~294× reduction, moving the typical Unknown building from
roughly 250× an ordinary commercial equipment load to inside the classified-archetype range
(`MediumOffice` reference: 10.76 W/m²). These "after" figures are bit-identical to attempt 3's own
Control-1 numbers, as expected under per-building determinism, and are independently re-derived
here rather than carried forward.

---

## 4. Supporting numbers (single-cell result, not a fleet restatement)

From this run's own gates report
(`docs/validations/overAll/results/open48_refleet3_t02a4/nyc_suburban/v12_nyc_suburban_gates_report.txt`):

- F12 gates: parse success 100.00 % (1589/1589, PASS); EUI plausibility 99.94 % (1588/1589, PASS,
  1 outlier at 1984.8 kWh/m²); zone mismatch 0 (PASS); IOD mean 0.1279, p95 0.2098.
- CBECS 2018 NE gates (report-only, not a closure condition of this item): CV(RMSE) 79.568 %
  (FAIL), NMBE 12.557 % (FAIL), R² 0.9999 (PASS), KS_D 0.3745 (FAIL).
- Headline: heating 85.39, cooling 7.64, lighting 12.86, equipment 38.62,
  **total 188.66 kWh/m²/yr**, GWP 6,962,564 kgCO₂e — for `nyc_suburban` only, this run's
  1,589 buildings. This is **not** the pooled fleet figure and is not being proposed as one; the
  fleet restatement is T03–T05 of the same plan, reserved for the director's decision at CP-1.
- Job ID **1274983**, all 1,589 array tasks `COMPLETED`.

---

## 5. Recommendation to the director

**OPEN-55.** The item's own closure condition — *"a cell with a high Unknown fraction
(`nyc_suburban`, 290) simulates with zero divergences"* — is now met, on real simulation output,
with independently re-derived controls, not carried-forward numbers. Recommend **CLOSE**.

**OPEN-49.** The register states the two items resolve together (*"OPEN-49 cannot close while
OPEN-55 stands"*). With OPEN-55's acceptance test now passed, recommend OPEN-49 **CLOSE** at the
same time, on the same evidence plus its own already-complete mechanism fix and per-building
determinism tests.

Neither closure is taken here — per plan §3 rule 6, the executor does not edit the register; this
is a recommendation for the director to act on at CP-1.

---

## 6. Artifacts

- Launcher: `scripts/validation/open48_t02_attempt4.py`
- Run log: `%LOCALAPPDATA%\Temp\open48_t02_attempt4\nyc_suburban.log`
- Heartbeat: `%LOCALAPPDATA%\Temp\open48_t02_attempt4\nyc_suburban.heartbeat.log`
- Exit code: `%LOCALAPPDATA%\Temp\open48_t02_attempt4\nyc_suburban.EXITCODE` = `0`
- Gates report + deliverables:
  `docs/validations/overAll/results/open48_refleet3_t02a4/nyc_suburban/`
- Remote fleet dir: `/speed-scratch/o_iseri/fleets/open48_refleet3_t02a4_nyc_suburban`
  (job 1274983)
