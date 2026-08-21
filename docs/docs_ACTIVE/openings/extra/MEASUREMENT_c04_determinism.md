# MEASUREMENT — the C04 leftover: drift or non-determinism?

**Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`, T10.
**Register item:** `INVESTIGATION_open-items-register-II.md:196`, "C04 leftover".
**Script:** `scripts/analysis/c04_same_head_double_run_2026-08-20.py`.
**CSV:** `openubem/outputs/comparisons/c04_same_head_double_run_2026-08-20.csv`.
**Population/denominator (D5):** one building, `nyc_centre`/`way/266034056`, run twice; 33 columns compared.

## Building identified

`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_twentysix-simulation-columns.md:230` —
`nyc_centre`/`way/266034056`: the single `simulation_status` flip (`success` fixture ->
`not_simulated` re-run) out of 8,160, carried alongside the `iod` movement (same doc, line 214,
227-228: "re-run the same HEAD build of one building twice and check whether `iod` is bit-stable
run-to-run" — the source of T10's method).

## Method

`SimTask`-equivalent built for `osm_id=way/266034056`, `idf_path=<D1 corpus>/nyc_centre/
fleet_staging/idfs/way_266034056.idf`, `epw_path=<D1 corpus>/nyc_centre/fleet_staging/weather/
USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053_TMYx.2011-2025.epw` (D1's pinned
`fleet_staging/idfs/<stem>.idf` layout). Run twice via `openubem.simulation.runner.
run_energyplus` (which passes `cwd=task.work_dir` explicitly at `runner.py:66` — OPEN-58 defect
(a)) in two separate directories under the session scratchpad (`c04_a/`, `c04_b/`), classified
with `classify_outcome`, and parsed with `openubem.results.parser.parse_building` (D3) using one
fixed `manifest_row` (identical for both runs, so any difference can only come from the
simulation itself, not from manifest construction). `manifest_row` fields verified directly from
the D1 corpus for this `osm_id`: `num_zones=133`, `resolution_mode='auto'`,
`data_quality_flag='no_floors,no_height'` (`step3/03_idf_manifest.parquet`);
`footprint_area_m2=2932.4636722561927`, `levels`/`height_m` both NaN (`01_buildings.gpkg`).

## Result

Both runs terminated `failed_fatal` (returncode 1) with the identical severe error:
`CalcHeatBalanceInsideSurf: The temperature of 1940305.55 C for zone="WAY/266034056_F0_CORE" ...`
— a malformed-zone geometry defect in the `fleet_staging` IDF, unrelated to non-determinism.
All 33 compared columns (10 EUI + 10 GWP + `iod` + `simulation_status` + `error_summary` +
`floor_area_m2` + `floor_area_provenance` + `osm_id` + 3 raw diagnostic columns) are **equal**
between run A and run B. 0 differ.

`git rev-parse HEAD` before: `3860f62b3ba8fbf4c68b5e056083f5ea5999e9a0`. After: same. **HEAD
stable — the test is valid** (C26).

**Verdict (C27):** identical -> the historical difference was code drift.

**C28:** 0 columns differ; `iod` and `simulation_status` are both among the (empty) diff set —
i.e. neither differs. `iod` is blank in both runs (the simulation never reached the point of
computing it — fatal at warmup); `simulation_status` is `failed_fatal` in both.

## Note — two IDFs exist for this building, only one tested

`nyc_centre/step3/idfs/way_266034056.idf` (2026-08-19 19:42, 550,260 B) is a **later, repaired**
version of `nyc_centre/fleet_staging/idfs/way_266034056.idf` (2026-08-19 16:37, 2,569,123 B) — the
`osm_id` appears in both `step3/repair_fleet.lst` and `step3/reroute_fleet.lst`, and
`04_simulation_manifest.parquet` (the manifest actually harvested for the adopted run) points at
`step3/idfs`, not `fleet_staging/idfs`, with its own (different) fatal severe error at a different
zone (`WAY/266034056_F0_WHOLE`, temperature 20,368,972.40 C). D1 pins the corpus layout as
`<cell>/fleet_staging/idfs/<stem>.idf`, so that is the file this measurement used, per the
plan's explicit, do-not-revisit decision. Both IDFs for this building are independently
malformed; this measurement does not establish whether `step3/idfs` is also deterministic, only
that `fleet_staging/idfs` is. The determinism question T10 asks (same HEAD, same input, two
runs) is answered either way — a repeat of this method against `step3/idfs` would settle the
`step3` variant too, if wanted.

## Test status

- C26 — pass (HEAD identical before/after).
- C27 — pass (one-sentence verdict stated: identical -> code drift).
- C28 — pass (0 differing columns; `iod` and `simulation_status` explicitly checked, neither differs).

---

# T11 — finish T10's job: prove determinism on a run that COMPLETES

**Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`, T11.
**Script:** `scripts/analysis/c04_determinism_completing_2026-08-20.py` (reuses T10's script above
as structural template, per the plan).
**CSV:** `openubem/outputs/comparisons/c04_determinism_completing_2026-08-20.csv`.
**Population/denominator (D5):** part (a) one building (`austin_rural`/`way/1480414365`), run
twice, 28 columns compared, 23 non-null in both arms; part (b) one building
(`nyc_centre`/`way/266034056`), its two on-disk IDFs each run once.

T10 (above) proved the *failure* path is deterministic — both arms of its double run terminated
`failed_fatal` at warmup, so every EUI column was `NaN` in both and `NaN == NaN` counted as
agreement. T11 repeats the method on a building that actually completes, and separately tests
whether the C04 building's two on-disk IDFs disagree.

## Part (a) — double run of a building that succeeds

**Building.** `austin_rural`/`way/1480414365`, archetype `SmallOffice`, 1 zone, IDF 48,100 B.
Picked as the first of 15 candidates sampled (`numpy`/`pandas` `random_state=42`) from
`openubem/outputs/comparisons/open61_census_fleet.csv` filtered to
`recorded_simulation_status == "success"`, `parsed_total_eui_kwh_m2` not null, and
`archetype_id` in `{SmallOffice, MidriseApartment}`. **It completed successfully on the first
try in both arms — 1 of 1 candidates tried, no fallback needed.**
`manifest_row` fields verified directly from the D1 corpus for this `osm_id`
(`austin_rural/step3/03_idf_manifest.parquet`, `austin_rural/01_buildings.gpkg`): `num_zones=1`,
`resolution_mode='auto'`, `data_quality_flag='generic_tag,no_floors,no_function,no_height,
no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT'`, `footprint_area_m2=287.0961565458416`, `levels`/
`height_m` both NaN. Two runs, same HEAD, separate working directories
(`c04b_completing_a/`, `c04b_completing_b/` under the session scratchpad), `cwd=` passed
explicitly (same `run_energyplus` path as T10, `runner.py:66`).

**Result.** Both runs: `simulation_status = success`, returncode 0, 0 severe, 37 warnings. 28
columns compared; **23 were non-null in both arms** (5 GWP placeholder columns are `NaN` in both
— GWP is filled by a separate carbon.py step this script does not invoke); **0 of those 23
differ**. `iod`: A=`0.0`, B=`0.0`, equal. `simulation_status`: A=`success`, B=`success`, equal.
`total_eui_kwh_m2`: A=`100.01588245660348`, B=`100.01588245660348`, equal.

`git rev-parse HEAD` before: `3860f62b3ba8fbf4c68b5e056083f5ea5999e9a0`. After: same.

**Verdict (C30, decisive):** identical on a COMPLETING building — 23 of 28 compared columns were
non-null in both arms, and 0 of those 23 differ. The pipeline is deterministic on a real (not
fatal-at-warmup) run, at the same HEAD.

## Part (b) — the two-IDF hypothesis

**Building.** `nyc_centre`/`way/266034056` (the C04 building, same as T10). Its two on-disk IDFs:
`fleet_staging/idfs/way_266034056.idf` (2,569,123 B, mtime 2026-08-19 16:37:47) and
`step3/idfs/way_266034056.idf` (550,260 B, mtime 2026-08-19 19:42:59). The `fleet_staging` arm's
result is T10's own already-completed run (read from `c04_same_head_double_run_2026-08-20.csv`
and from T10's own work dir `c04_a/eplusout.err`, not re-run, to avoid a redundant EnergyPlus
process). The `step3` IDF was run once, in a fresh work dir (`c04b_step3/`), same HEAD, `cwd=`
passed explicitly.

**Result (C32).**

| | `fleet_staging` IDF | `step3` IDF |
|---|---|---|
| `simulation_status` | `failed_fatal` | `failed_fatal` |
| `error_summary` (classify_outcome's FATAL_RE line) | `**  Fatal  ** Program terminates due to preceding condition.` | `**  Fatal  ** Program terminates due to preceding condition.` |
| first `** Severe **` line (200c) | `** Severe  ** CalcHeatBalanceInsideSurf: The temperature of 1940305.55 C for zone="WAY/266034056_F0_CORE", for surface="BLOCK CORE_ZONE STOREY 0 WALL 0006_1"` | `** Severe  ** CalcHeatBalanceInsideSurf: The temperature of 20368972.40 C for zone="WAY/266034056_F0_WHOLE", for surface="BLOCK WAY/266034056_WHOLE STOREY 0 WALL 0001"` |
| warnings / severe (from `eplusout.end`) | 362 / 1 | 75 / 1 |
| elapsed | 7.82 s | 0.83 s |

`classify_outcome`'s `error_summary` field captures only the first FATAL_RE-matching line in
`eplusout.err`, which is the generic trailer both arms share (F9: 43 of 44 fleet fatals carry
only this trailer) — it does **not** distinguish the two IDFs. The actual `** Severe **` cause
line, read directly from each arm's `eplusout.err`, does: **same `simulation_status`
(`failed_fatal`), different severe cause** — different zone (`F0_CORE` vs `F0_WHOLE`), different
runaway temperature, different warning count, different elapsed time. The two IDFs are two
independently malformed files that happen to land on the same status token; they are not proof
of, and do not require, non-determinism to explain a historical `simulation_status` flip — a run
pointed at a different file is a third, distinct explanation, but for *this* building it produces
the same terminal status either way, so it does not itself explain the C04 leftover's flip
to/from `success`.

## Test status (T11)

- **C29** — pass. Part (a)'s building completed (`success`) in both arms on the first candidate
  tried (1 of 1).
- **C30 (decisive)** — pass. 23 of 28 compared columns were non-null in both arms; 0 of those 23
  differ. Verdict: identical on a completing building.
- **C31** — pass. `iod` (A=`0.0`, B=`0.0`, equal) and `simulation_status` (A=`success`,
  B=`success`, equal) reported explicitly.
- **C32** — pass. `step3` vs `fleet_staging` reported as two statuses (`failed_fatal` /
  `failed_fatal`, equal) and two severe strings (200c, different — see table above), with both
  IDFs' file sizes and mtimes.

⚠️ Neither IDF was repaired; no choice between them was made — both are out of scope for this
plan (T11's stated constraint).
