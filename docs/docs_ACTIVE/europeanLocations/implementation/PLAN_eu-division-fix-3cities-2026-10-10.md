# PLAN — Helsinki, Vienna, Budapest: put the dry-run fixes into the pipeline and rerun the left-out homes

## 1. Header

- Slug: `eu-division-fix-3cities`. Date: 2026-10-10. Manager: OpenUBEM manager session.
- Requests (owner, verbatim): "try more please at least 95% or aroung" (Helsinki, 2026-10-09); "yes please" (Vienna joins); "yes if possible push budapest to 95%" (2026-10-09); "lets go to the end".
- Predecessor: `PLAN_eu-helsinki-division-2026-10-09.md` §8 (T01–T02, T01V–T02V, T01B–T02B, the diagnosis and dry runs). This plan applies what the dry runs found.
- Where each city stands: all three stopped at S5 (`PLAN_eu-new-city-{FI-helsinki,AT-vienna,HU-budapest}-2026-10-08.md`, T04 STOP). After this plan each city plan resumes at its T05 (S6 plan pages) on the new `_2026-10-10` trees.
- Targets (correctly divided = OK + V3): Helsinki ≥ 551 of 580 (today 458), Vienna ≥ 509 of 536 (today 448), Budapest ≥ 765 of 805 (today 609). Dry-run projections with a 10-minute limit: 518, 499, 660. The gap is almost all homes that ran out of time (Helsinki 64, Vienna 41, Budapest 142): deep plates with many flats per floor.

## 2. Hard rules for the executor

1. Every new switch is OFF by default. With the switches off, every existing tree, side-car, IDF and score must come out byte-identical; the four first cities (Madrid, Lyon, London, Bologna) and Cape Town, Yerevan, Montréal are never rerun. Bologna is FROZEN.
2. Never rewrite a delivered tree. New output goes only to `*_2026-10-10` folders and `division_fix_2026-10-10/`.
3. Local: at most 8 worker processes in total (count real `python` processes first; the machine limit is 10). No EnergyPlus run. No compute on the Speed login node; Speed jobs are submitted by the manager (T05 stops before any `sbatch`).
4. Never touch 4J/5J files, jobs or folders, nor another project's Speed jobs.
5. No code comments. Cap command output (`| head -30`, counts not listings). `python -I -X utf8`.
6. Every solved error gets one bullet in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (house format).
7. Stop and quote on any conflict with this plan.

## 3. File layout

| Path | Status | Task |
|---|---|---|
| `scripts/eu22/acquire_helsinki.py` (`:113-115`) | edit: split the building's flat count over its parts | T01 |
| `tests/eu22/test_acquire_helsinki.py` | edit: part-split test | T01 |
| `openubem/outputs/eu02/FI-HEL-KALLIO/` manifests | regenerate (same file names; keep the old pair as `*_2026-10-09.gpkg` copies first) | T01 |
| `openubem/geometry/european_nocore.py` | edit: opt-in wide sweep (`OPENUBEM_NOCORE_SWEEP`) | T02 |
| `scripts/run_eu_s2_district_campaign.py` | edit: opt-in one-flat-less retry for area-imputed counts (`OPENUBEM_NOCORE_KMINUS1`) | T02 |
| `scripts/eu22/score_division.py` (`:250`) | edit: `--floors-decide` flag | T03 |
| `tests/eu22/test_nocore_sweep.py` | new | T02 |
| `openubem/geometry/european_residential.py` (`_nocore_cut_with_guard`, `:1354`) | edit: one switch-gated acceptance (T02 amendment) | T02 |
| `scripts/emit_eu11_layout_sidecars.py` | edit: same one-flat-less call, switch-gated (T02 amendment) | T02 |
| `tests/eu22/test_score_division.py` | edit | T03 |
| `scripts/cluster/eu22_fix_env.sbatch`, `scripts/cluster/eu22_fix_array.sbatch`, `scripts/cluster/stage_eu22_fix.sh` | new | T04 |
| `openubem/outputs/eu_evidence/EU-11/division_fix_2026-10-10/` | new: id lists, run tables, `summary.md` | T04–T06 |
| `openubem/outputs/eu_evidence/EU-11/<SITE>_dw_2026-10-10/`, `<SITE>_win_2026-10-10/` | new trees | T06 |

## 4. Dependency decisions (pinned)

- **D-EU-166 — a home whose floors all pass decides by its floors (manager, 2026-10-10, under the owner's 95 % request).** Some homes carry the generator's "best effort" tag although every floor passes every check of the final ruleset (Helsinki 9, Vienna 11, Budapest 1). For these three cities only, the scorer runs with `--floors-decide`: such a home is scored on its floors (OK or V3), not on the tag. This applies the frozen final rules (D-EU-148) as written; it loosens no check. The other seven cities keep the default (off), so no published number changes.
- **D-EU-167 — one flat less only where the flat count was estimated (manager, 2026-10-10).** Lever L2 (k − 1 on a failing floor) runs only for homes whose `dwelling_count_source` is `area_imputed` (all of Vienna and Budapest; never Helsinki, whose counts are observed). Each removed flat is listed per home; the total goes in the summary.
- **Sweep = dry-run lever L1, unchanged.** Port the candidate search from `openubem/outputs/eu_evidence/EU-11/helsinki_division_2026-10-09/scratch/t02.py` (`THETAS` `:13`, `candidates` `:32`, `passes` `:85`, `search` `:90`, `_finish_candidate` use `:110`) into the engine: every cutter of `european_nocore.py` (`cut_nocore :689`, `cut_grid :707`, `cut_grid_snapped :724`, `cut_layered :765`, `cut_radial :887`, `cut_ring_bisect :973`, `cut_wingwise :1041`) at the seven `THETAS`, each through `_finish_candidate`, then `improve_cut_nocore` (`:2424`) on candidates that still fail, best plate score first; the first candidate that passes every gated check wins. It runs only on a floor that still fails after the existing passes (after `_wide_search_pass`, `:2402`). Per-floor time budget `OPENUBEM_NOCORE_SWEEP_S` (default 600); on time-out the floor keeps today's result.
- **Helsinki parts:** a building split into `_partN` rows gets its observed total split over its parts in proportion to part footprint area × storeys, largest remainder, each part at least 1 when the total allows. Today every part carries the whole building's count (`acquire_helsinki.py:113-115`; `875288_part0..3` get 39 flats per floor on 363–816 m² plates).
- **Where the long runs go: Speed.** One array task per home (`--only-ids` with one id), `--time=7-00:00:00`, budget 3,600 s per floor, our arrays together ≤ 32 CPUs. The Python environment is built by an `sbatch` job into `/speed-scratch/o_iseri/envs/openubem_eu22/` (new folder; never touch other folders under `envs/`).
- **Merge:** `scripts/eu22/merge_prepare_parts.py --parts … --out …` (`:165-166`), as Budapest T03s.

## 5. Facts with citations

- Dry-run numbers: `PLAN_eu-helsinki-division-2026-10-09.md:92-97` (Helsinki), `:106-111` (Vienna), `:113-118` (Budapest).
- Best-effort tag set at generation: `openubem/geometry/european_residential.py:1434-1440`; scorer reads it at `scripts/eu22/score_division.py:250` (`best_effort="BEST_EFFORT" in go`) into `_divided_result` (`:170`).
- Prepare by id: `scripts/run_eu_s2_district_campaign.py:1381-1386` (`--only-ids`, a CSV with a `building_id` column).
- Standard steps S4–S5: `PLAN_eu-new-cities-00-common-2026-10-08.md:249-251`; side-car step reads `--evidence-root SITE=<win tree>` after S8 (manager note at `:254`), but at S5 it takes `--population-manifest SITE=<dw>/prepared_buildings.csv` (Cape Town T04 deviation).

## 6. Tasks

### T01 — Helsinki: split the flat count over a building's parts
- What: fix `acquire_helsinki.py:113-115` per §4; regenerate the two Helsinki manifests from the saved raw files (no network; if the script cannot run offline, STOP).
- Why: 18 part rows carry the whole building's count; 10 of them are left out.
- How: copy the current manifests to `*_2026-10-09.gpkg` first; rerun; write `division_fix_2026-10-10/helsinki_parts.csv` (`building_id, base_id, old_count, new_count`).
- Test: unit test of the split (sum over parts = building total; every part ≥ 1; area weighting). Live: only `observed_dwellings` of `_partN` rows changes, every other column of every row is identical; sum of new counts per base id = the base total.

### T02 — Engine: opt-in wide sweep and one-flat-less retry
- What: the sweep of §4 behind `OPENUBEM_NOCORE_SWEEP=1` (budget `OPENUBEM_NOCORE_SWEEP_S`); in `run_eu_s2_district_campaign.py`, behind `OPENUBEM_NOCORE_KMINUS1=1`, a home with an `area_imputed` count whose layout still fails or is best-effort is retried floor by floor with k − 1 on each failing floor (as dry-run L2), recording `dwellings_removed` in `prepared_buildings.csv` (new column, empty when unused).
- Why: L1 recovered 46 + 43 + 51 homes in the dry runs without removing a flat; L2 recovered 8 more in Vienna.
- How: port, do not reinvent. Keep the dry-run order of candidates.
- Test (`tests/eu22/test_nocore_sweep.py`): (a) switches off: 20 random OK homes per city (seed 20261010) through `--only-ids` give side-car and IDF sha256 identical to the `_2026-10-09` trees; (b) sweep on, 10-min budget: 5 Vienna homes that L1 recovered in `vienna_division_2026-10-09/t02_dryrun.csv` now score OK or V3; (c) k−1 refuses to run on an `observed` count.
- **Manager amendment 2026-10-10 (after the T02 stop):** approved. (1) In `_nocore_cut_with_guard` (`european_residential.py:1354`), only when `OPENUBEM_NOCORE_SWEEP=1`: accept a cut that passes every gated check even if its bent-wall count (C13, not gated) rises; switch off = unchanged. (2) `emit_eu11_layout_sidecars.py` makes the same one-flat-less call behind `OPENUBEM_NOCORE_KMINUS1=1`, so side-cars draw the reduced count. (3) Test (b) passes at ≥ 4 of 5 (AT-VIE-5376819 is a known miss: the dry run cut each plate part separately; do not port that). Rerun test (a) with both changes in, switches off.

### T03 — Scorer flag `--floors-decide`
- What: D-EU-166 in `score_division.py`; default off.
- Test: default off on the Cape Town and Vienna `_2026-10-09` trees gives a `division_classes.csv` byte-identical to today's; on, on Vienna, exactly the 11 tag-only homes of T01V move to OK/V3 and nothing else changes.

### T04 — Id lists and Speed scripts (no submission)
- What: `division_fix_2026-10-10/ids_<SITE>.csv` = every left-out home of the `_2026-10-09` tree, plus for Helsinki every `_partN` home whose count changed in T01 (122 + changed parts; 88; 196). `stage_eu22_fix.sh` copies the repo code, the three sites' manifests and inputs, and the id lists to `/speed-scratch/o_iseri/eu22_fix_2026-10-10/` (`scp`/`tar` only). `eu22_fix_env.sbatch` builds the environment (§4) from the repo's pinned requirements and runs `python -c "import shapely, pandas, geopandas"` at the end. `eu22_fix_array.sbatch`: task i reads line i of a combined list (`site,building_id`), sets the three switches on (KMINUS1 only for Vienna/Budapest), `OPENUBEM_NOCORE_SWEEP_S=3600`, runs `run_eu_s2_district_campaign.py --district SITE --only-ids <one-id csv> --out parts/<SITE>/<i>/`.
- Test: one local dry run of the array script on 2 ids per site with a 60 s budget (6 processes at most), outputs merge with `merge_prepare_parts.py`. Report the combined list length.
- STOP: the manager stages, builds the environment and submits.

### T05 — Speed (manager)
- `bash scripts/cluster/stage_eu22_fix.sh`; `sbatch -p ps --time=7-00:00:00 eu22_fix_env.sbatch`; when it ends cleanly, `sbatch -p ps --time=7-00:00:00 --array=1-N%W eu22_fix_array.sbatch` with W = 32 minus our other running arrays. ETA from `sacct` once 32 tasks have ended. Pull `parts/` back with `scp`.

### T06 — Merge, finish the trees, score
- What: per site, merge the `_2026-10-09` dw tree minus the rerun ids with the Speed parts into `<SITE>_dw_2026-10-10/` (`merge_prepare_parts.py`); then S4 and S5 of the common plan on `DATE=2026-10-10`, with `score_division.py --floors-decide`.
- Test: per site, home count equals the 10-09 tree; every home not in the id list has an IDF sha256 equal to the 10-09 tree; class counts and correctly divided share; flats removed by k−1 (total and per home); homes still left out with their failing checks; integrity I1–I13 and `IDF_FALLBACK` as in S5. Write `division_fix_2026-10-10/summary.md` (≤ 40 lines).

## 7. Stop-and-report points

1. After T03: switches-off identity results and the three tests.
2. After T04: the Speed scripts and the local two-ids-per-site run; the manager submits.
3. After T06: shares per city against the targets. The manager audits, then each city plan resumes at T05 (S6 plan pages, owner sees them before runs).

## 8. Progress log

(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### T01 — Helsinki: split the flat count over a building's parts — completed 2026-10-10
- Artifacts: `scripts/eu22/acquire_helsinki.py` (new `split_counts`, `split_part_dwellings`, called from `attach_attributes`); `tests/eu22/test_acquire_helsinki.py` (+4 tests); `openubem/outputs/eu02/FI-HEL-KALLIO/02_residential_manifest.gpkg` and `02_excluded_manifest.gpkg` regenerated offline from the saved raw pages, old pair kept as `*_2026-10-09.gpkg`; `openubem/outputs/eu_evidence/EU-11/division_fix_2026-10-10/helsinki_parts.csv` (18 rows).
- Deviations: none. `acquisition_report.json` and `01_buildings_clean.*` were rewritten by the same script run with identical content (boundary files, schema, source and exclusion counts byte-equal; the clean gpkg equal in every column and geometry).
- Test status: unit tests 17 passed. Live: 588 rows before and after, same ids in the same order; only `observed_dwellings` differs, on exactly the 18 `_partN` rows (8 buildings); sum over parts equals the base total for all 8; no non-part row changed; excluded manifest unchanged. Example `875288`: 312 on every part -> 74 / 120 / 64 / 54.
- Notes: a part whose building total is below the number of parts would get 0 (shown as empty); no such case exists in the data.

#### T02 — Engine: opt-in wide sweep and one-flat-less retry — code and 3 of 4 tests done, test (b) BLOCKED — 2026-10-10
- Artifacts: `openubem/geometry/european_nocore.py` (`_sweep_pass`, `_sweep_candidates`, `_sweep_search`, memo, called after `_wide_search_pass` in `improve_cut_nocore`; switch `OPENUBEM_NOCORE_SWEEP=1`, budget `OPENUBEM_NOCORE_SWEEP_S`, default 600; skipped in the strict first phase of `_nocore_cut_with_guard`, which has the old 2.5 / 0.50 rules); `scripts/run_eu_s2_district_campaign.py` (`_layout_with_kminus1`, switch `OPENUBEM_NOCORE_KMINUS1=1`, column `dwellings_removed` written only when the switch is on, `_GeometryOutcome.dwellings_removed`); `tests/eu22/test_nocore_sweep.py` (new).
- Deviations: (1) the k-1 retry cannot see which floor failed from outside the layout builder, so it re-cuts each distinct floor count once (cost: a second cut of the failing counts, cheap because the sweep results are memoised per process). (2) Not done and not in the plan: `scripts/emit_eu11_layout_sidecars.py` re-derives layouts without the k-1 retry, so for a home with removed flats its side-car would still draw the full count; it needs the same one-line call before T06 (the sweep itself is picked up automatically when the same switches are set).
- Test status: (a) switches off, 20 random OK homes per city (seed 20261010; Helsinki non-part homes only): IDF sha256 and side-car bytes identical to the 2026-10-09 trees, 20/20 in each of Helsinki, Vienna, Budapest. (c) k-1 refuses `observed`, `observed_split`, `single`, `archetype_default`: pass (4 unit tests). (b) sweep on, 600 s: BLOCKED, see Notes. Fast tests 6 passed; (b) marked xfail with the reason.
- Notes (conflict, needs a manager ruling): the production cutter `_nocore_cut_with_guard` (`openubem/geometry/european_residential.py:1354-1391`) keeps its first (strict-rules) cut unless `_strictly_better` (`european_nocore.py:2099`) accepts the second one, and that function rejects a cut when the number of bent walls (C13, not a gated check) rises, even if the new cut passes every gated check and C12. Example AT-VIE-5403805: the final-rules cut passes (spread 0.9997, C13 = 1) but loses to the failing strict cut (C13 = 0), so the home keeps its best-effort tag with the sweep on or off. With the sweep on and the plan's switches only, test (b) failed (first run, 46 min, before the strict phase was skipped): 5285862 OK, 5351055, 5376819 and 5403805 still V1. Scratch prototype (not in the repo): accepting a cut that passes all gated checks and C12 when the old one does not (only when the sweep switch is on) gives 4 of 5 (2 OK, 2 V3); the 5th (AT-VIE-5376819, NOCORE_BEST_EFFORT_C10) was recovered in the dry run only because the dry run cut each part of the plate separately. Proposed ruling: allow that one switch-gated line in `_nocore_cut_with_guard` (a file not in the plan's layout) and decide about part-wise cutting. Nothing was changed in `european_residential.py`.

#### T03 — Scorer flag `--floors-decide` — completed 2026-10-10
- Artifacts: `scripts/eu22/score_division.py` (`--floors-decide`, argument `floors_decide` in `score()`, `_sidecar_home()`, 6th element of the job tuple; default off); `tests/eu22/test_score_division.py` (+4 tests, 3 marked slow).
- Deviations: none.
- Test status: default off on Vienna (`AT-VIE-RUDOLFSHEIM_win/dw_2026-10-09`, 536 homes) and Cape Town (`ZA-CPT-WOODSTOCK_win/dw_2026-10-09`, 525 homes): `division_classes.csv` and `left_out.csv` byte-identical to the trees' own files. Flag on, Vienna: 11 homes move (8 V1 -> V3, 3 V1 -> OK), the same 11 as the tag-only homes of the 2026-10-09 dry run; the other 525 rows are identical and only the `cls` column differs. Class counts on: OK 238, V3 221, V1 72, V2 2, U4 2, U1 1; left out 77 (was 88). Scorer tests: 9 fast passed, 3 slow passed.
- Notes: Cape Town must be scored with `--layout-tree` = its dw tree (its win tree holds one layout fewer).


#### T02 (amendment) — Engine: opt-in wide sweep and one-flat-less retry — completed 2026-10-10
- Artifacts: `openubem/geometry/european_residential.py` (new `_nocore_accepts`, used in `_nocore_cut_with_guard`; takes a cut that passes every gated check and C12 when the old one does not, even if C13 rises, only while `OPENUBEM_NOCORE_SWEEP=1`; imports `os` and `_GATED_CHECKS`); `scripts/emit_eu11_layout_sidecars.py` (calls `_layout_with_kminus1`, source from `used_map`, else `observed`/`other`; behind `OPENUBEM_NOCORE_KMINUS1=1` as the campaign); `tests/eu22/test_nocore_sweep.py` (test (b) rewritten: 5 homes in parallel, pass at >= 4 of 5, xfail removed); two bullets in `OpenUBEM_debug_References.md`.
- Deviations: none from the amendment. Part-wise cutting not ported, as ruled.
- Test status: (a) switches off, both changes in, 20 random OK homes per city (seed 20261010): IDF sha256, IDF files and side-car bytes identical to the 2026-10-09 trees, 3 of 3 sites pass. (b) sweep on, 600 s per floor, 5 Vienna homes: 5285862 OK, 5507071 OK, 5351055 V3, 5403805 V3, 5376819 V1 (the known miss) = 4 of 5, pass. (c) k-1 refuses non-`area_imputed`: pass. Whole test file: 10 of 10 pass (9 + 1 in two runs).
- Notes: another pytest run of `tests/eu22` (started 04:18, not mine) was already running its own copy of old test (b) when this work began; left alone. For T06: the 2026-10-09 `prepared_buildings.csv` files have no `dwellings_removed` column while Vienna and Budapest Speed parts do, so `merge_prepare_parts.py` will stop on "header differs"; add the empty column to the kept rows first.

#### T04 — Id lists and Speed scripts (no submission) — completed 2026-10-10
- Artifacts: `scripts/cluster/stage_eu22_fix.sh` (builds repo code without outputs, the three `eu02` site folders, one `acquisition_report.json` per site, id lists, both sbatch files and `requirements_eu22.txt` from `uv export --frozen --no-dev`; ships by `ssh`/`scp`/`tar` only; `--dry-run <dir>` unpacks locally, no ssh); `scripts/cluster/eu22_fix_env.sbatch` (venv in `/speed-scratch/o_iseri/envs/openubem_eu22`, stops if the folder exists or `PYBIN` is older than 3.10, ends with the `shapely, pandas, geopandas` import); `scripts/cluster/eu22_fix_array.sbatch` (task i reads data row i of `ids_combined.csv`, sets SWEEP=1, SWEEP_S=3600, KMINUS1=1 only for Vienna and Budapest, writes `parts/<SITE>/<i>/`); id lists in `openubem/outputs/eu_evidence/EU-11/division_fix_2026-10-10/`: `ids_FI-HEL-KALLIO.csv` 130 (122 left out + 8 changed parts not yet left out), `ids_AT-VIE-RUDOLFSHEIM.csv` 88, `ids_HU-BUD-ERZSEBETVAROS.csv` 196, `ids_combined.csv` 414 data rows (header `site,building_id`; order Helsinki, Vienna, Budapest). Array size N = 414.
- Deviations: (1) the Speed array script runs Python without `-I` and sets `PYTHONPATH` to the staged repo, because the new environment has no editable install of the project. (2) Id lists were written by a one-off inline script (rule: left-out ids of each `win_2026-10-09/left_out.csv`, plus Helsinki `_partN` ids whose count changed in `helsinki_parts.csv`); no script file kept. (3) The first staged copy missed `eu_evidence/EU-22/<site>/acquisition_report.json`; Vienna and Budapest homes were then all unmappable; fixed in the stage script and registered in the debug references.
- Test status: local run of the array script from the unpacked package, ids 1-6 = 2 per site, budget 60 s per floor, 6 processes at once: 6 of 6 tasks end with `PREPARED_FOR_SPEED`, one IDF each (Helsinki 2, Vienna 2, Budapest 2; Vienna and Budapest layouts `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`, `dwellings_removed` empty). `merge_prepare_parts.py` merges each site's 2 parts: 2 homes, 2 IDFs per site. Shell syntax of the three scripts checked with `bash -n`. Env sbatch and the real Speed run not tried (no cluster use).
- Notes: STOP point 2 reached. The manager runs `bash scripts/cluster/stage_eu22_fix.sh`, then `sbatch -p ps --time=7-00:00:00 eu22_fix_env.sbatch` (add `--export=ALL,PYBIN=<python >= 3.10>` if the default `python3` is too old; compute nodes need pip access for the build), then the array with `--array=1-414%W`. The per-floor budget of 3,600 s is per floor, so a 7-storey home can run for hours; this is why the walltime is 7 days.

#### T05 — Speed (manager) — submitted 2026-10-10
- **Artifacts:** `/speed-scratch/o_iseri/eu22_fix_2026-10-10/` (staged by `stage_eu22_fix.sh`); environment `/speed-scratch/o_iseri/envs/openubem_eu22/` built by job 1448039 with `PYBIN=/encs/pkg/python-3.12.0/root/bin/python3` (`ENV_OK` shapely 2.1.2, pandas 3.0.3, geopandas 1.1.3). Rerun array job 1448071, `--array=1-414%32 --time=7-00:00:00`.
- **Deviations:** the first array (1448040) wrote IDFs with eppy's bundled v8.0 IDD (`config.py` looks for the Windows EnergyPlus path); cancelled after ~15 min, its `parts/` deleted, logs kept in `logs/old_wrong_idd/`. Fix: the local EnergyPlus 23.1 `Energy+.idd` (md5 2f3e8a1b51a4c375c31a720ad6c39f58) copied to the package root and exported as `OPENUBEM_ENERGYPLUS_IDD_PATH` by `eu22_fix_array.sbatch`, which now fails if it is missing. `stage_eu22_fix.sh` does not copy the IDD yet; copy it by hand on any restage. Debug reference added.
- **Test status:** after resubmission, 17 task logs, 0 with the IDD warning; 1 shows the known handled `intersect_match raised ZeroDivisionError — purging and retrying` line.
- **Notes for T06 (manager):** the 2026-10-09 `prepared_buildings.csv` files have no `dwellings_removed` column; add it empty to the kept rows before `merge_prepare_parts.py`, or the merge stops on "header differs".
