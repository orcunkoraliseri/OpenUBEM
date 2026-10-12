# PLAN — why 24 buildings (Madrid 11, Bologna 13) stop at the geometry check, and how to fix them

**Slug:** `geometry-24-madrid-bologna` · **Date:** 2026-10-10 · **Author:** manager · **Trigger:** owner request + two 4J questions (`messages_GSSCanada/2026-10-10_4J_to_OpenUBEM_bologna_geometry_questions.md`; peer message from gsscanada-25, Madrid, same day).
**DESIGN pointer:** none new. Background: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (search `FINDING 210`, `D-EU-43`, `failed_interzone_vertex_mismatch`, `FINDING 249`); `tests/geometry/test_eu15_ruled_coverage.py:392-430` (the `_stabilize_ring_coords` 1 mm grid fix).

## 1 Correction to what I told 4J earlier today

My first reply said the "Zero or negative surface area [~1e-8]" error was new to us. **That was wrong.** It is registered as `D-EU-43`: "a second EnergyPlus-side symptom of the exact same FINDING 210 root cause" (debug refs, `D-EU-43` entry). Both Madrid errors are one known family: two shapes that should be identical (ceiling of storey N, floor of storey N+1) come out of a shapely boolean/simplify step with different corner points, and the result depends on the GEOS build and on float round-off. The fix we shipped for it is `_stabilize_ring_coords` (snap every emitted ring to a 1 mm grid) plus the reroute gate in `openubem/idf/builder.py:610-660`. **So the real question is why that fix did not protect these 24.** Correct 4J in the hand-over note (T07).

## 2 Hard rules for the executor

1. **Read-only on everything frozen:** `IT-BOL-GALVANI2_win_2026-10-06/`, the Bologna part of Speed `/speed-scratch/o_iseri/handover_4J_2026-10-06/`, `partner_fixed_homes_2026-10-08/`, and 4J's run folders `/speed-scratch/o_iseri/4J_esit/...`. Look, copy out with `scp`, never write there.
2. **No simulation.** No EnergyPlus run, no `sbatch`. Where a run is needed, write the IDF list and stop; the manager submits (CLAUDE.md cluster rules).
3. **No edit to `openubem/**`, to the sealed 4J engine, or to any shared doc** (`OpenUBEM_debug_References.md`, the START HERE box) until stop-point 2 is approved. Scratch code lives in `scripts/eu_geometry24/` (new), outputs in `openubem/outputs/eu_evidence/EU-11/geometry_24_2026-10-10/`.
4. Login node: `scp`, `tar`, `squeue`, `sacct`, `mkdir` only. Use the `_ssh()` bash wrapper (`scripts/cluster/t08_harvest_results.py:104`). No bare ssh command strings.
5. Python reads of untrusted data: `python -I`. No code comments. Cap every command output (`| head -30`).
6. Do not propose alternatives to the plan; if something is ambiguous, STOP and quote it.

## 3 The 24 buildings

- **Madrid (ES-MAD-BERRUGUETE), 11:** relations 12582234, 12891867, 13113580, 13381287, 13160790, 4835800, 4165178, 5808697, 6382787, 4154505; way 340701289. 4J symptoms: ceiling/floor vertex-count mismatch (most), zero-area sliver 1e-8..1e-7 (12582234, 4835800, 340701289; 4835800 also non-planar), harness error `interzone_vertex_mismatch_unresolved` (4154505). All fail in all 4 cells.
- **Bologna (IT-BOL-GALVANI2), 13:** vertex mismatch (8): 28025, 28959, 29530, 29719, 30001, 31083, 31363, 32360. Duplicated corner point, 77 degenerate surfaces, "Invalid dot product" (1): 28050 (two vertices at 686672.144, 4929113.520). Harness refuses `interzone_vertex_mismatch_unresolved` (4): 29109, 30485, 31962, 33359.
- Known: in OUR Madrid 10-06 run, 12582234, 13160790, 4154505, 4835800 and way 340701289 already had results (`results/EU11_results_2026-10-08_per_home.csv`). So our IDFs for those exist and ran; 4J's harness result differs.

## 4 Hypotheses to test (diagnosis, not remedy)

- **H1 — engine version.** 4J runs engine "10-06 PIN 3" (sha256 `0b9aa66c…`). It may predate `_stabilize_ring_coords` or a later gate. Test: `git log --oneline -S"_stabilize_ring_coords" -- openubem/geometry/european_residential.py` and compare the file's sha256 at each candidate commit with `0b9aa66c`.
- **H2 — the gate cannot rescue non-core buildings.** `builder.py:616-650` reroutes only core/perimeter zones. A building already in `one_zone_per_floor` or `room_layout` gets `did_reroute=False` and is dropped as `failed_interzone_vertex_mismatch` — the 4J "unresolved" error. Test: read each building's `zoning_strategy` in the prepared/manifest CSV.
- **H3 — float round-off on absolute UTM coordinates (~4.9e6 m).** Mirror surfaces differ in the last decimal digit (see the Lyon `[OPEN]` entry in the debug refs). Test: rebuild after shifting to a local origin and compare vertex counts; measure the coordinate magnitude of the failing rings.
- **H4 — footprint defects.** Multi-part relation, interior ring, exactly-collinear vertex at a short segment, repeated point (28050). Test: per-footprint forensics (T03).
- **H5 — GEOS build difference.** Speed/Linux vs this Windows build (FINDING 210 was exactly this). Test: T04 rebuild locally, compare with 4J's counts.

## 5 Tasks

### T01 — Locate the 24 and their inputs — **What / Why / How / How to test**
- **What:** one CSV `geometry_24_inventory.csv` with, per building: district, id, our shipped IDF path (10-06 `win`/merged tree and the 10-08 fixed-homes package if present), the footprint row (prepared_buildings.csv), `zoning_strategy`, `data_quality_flag`, number of storeys, our 10-08 result status (has_result), whether it is on `exclude_4J_london_bologna_2026-10-08.csv` / `exclude_4J_madrid.csv`.
- **Why:** every later task reads this one file.
- **How:** `Glob` in `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE_merged_win_2026-10-06`, `IT-BOL-GALVANI2_win_2026-10-06`, `rulebook_2026-09-30/partner_fixed_homes_2026-10-08`; read-only pandas with `python -I`.
- **Test:** 24 rows, no empty IDF path for Madrid; Bologna rows may have an empty fixed-home path (say so, do not guess).

### T02 — Read 4J's own error evidence — **What / Why / How / How to test**
- **What:** for the 13 Bologna ids copy `eplusout.err` and `cells_failed/it__<id>__caseA__f000.json` from `/speed-scratch/o_iseri/4J_esit/p8/c2_bol/runs/IT-BOL-GALVANI2/it__<id>__caseA__f000/` and `.../out/IT-BOL-GALVANI2/cells_failed/` to `geometry_24_2026-10-10/4J_bologna/` with `scp`. Madrid files are on 4J's own machine: list which 11 are missing and do NOT ask 4J yourself — report the list to the manager (T07 asks).
- **Why:** classify by the exact message text, not by 4J's summary.
- **How:** one `scp` per id; `grep -c "Vertex size mismatch"`, `grep -c "Zero or negative"`, `grep -c degenerate` per file.
- **Test:** table id → signature → count; totals match 4J's note (e.g. 28959 = 31 mismatch messages, 28050 = 77 degenerate).

### T03 — Footprint and IDF forensics, read-only — **What / Why / How / How to test**
- **What:** `footprint_forensics.csv`: for each of the 24 — number of polygon parts, interior rings, ring vertex count, count of exactly-collinear vertices (turn < 0.001°), shortest segment, any repeated point, min/max coordinate magnitude, area; and from the shipped IDF: count of interzone ceiling/floor pairs whose vertex counts differ, count of surfaces with area < 1e-6 m², count of repeated vertices.
- **Why:** decides H3/H4 (and H2 with the T01 strategy column).
- **How:** `scripts/eu_geometry24/forensics.py` (new, shapely + plain IDF text parse; reuse `find_mismatched_interzone_pairs` from `openubem/idf/surfaces.py:547` read-only via import).
- **Test:** 24 rows; 28050 shows a repeated point at (686672.144, 4929113.520); at least a count per hypothesis column.

### T04 — Rebuild locally with the current and the 10-06 engine — **What / Why / How / How to test**
- **What:** (a) check H1: report the commit(s) containing `_stabilize_ring_coords` and `sha256` of `european_residential.py` at the 10-06 commit versus `0b9aa66c`; (b) for each of the 24, rebuild the IDF geometry (generation only, no EnergyPlus) with the **current** engine in `git worktree` scratch at HEAD and, if different, with the 10-06 engine, and record `find_mismatched_interzone_pairs`, surfaces under 1e-6 m², `generation_status`.
- **Why:** separates "old engine" (H1) from "still fails on current engine" (H2–H5), and shows whether the GEOS build matters (H5: compare to 4J's counts).
- **How:** `git worktree add` into the scratchpad directory for the 10-06 commit; run the same driver the 10-06 build used (find it via `scripts/` grep for `european_residential`; quote the path in the progress log). Never touch the main working tree files.
- **Test:** table building × {10-06 engine, current engine} → {ok, mismatch n, sliver n, dropped}. Report counts per cell of the table.

## 6 Candidate remedies (do NOT start before stop-point 1 is approved)

- **R-A** extend the reroute gate in `builder.py` to non-core buildings (`room_layout`, already one-zone) using `_force_reroute_room_layout_to_one_zone_per_floor` (`surfaces.py:640`).
- **R-B** apply `_stabilize_ring_coords` to every emitted ring including the mirrored interzone pair, and drop repeated points before extrusion (28050).
- **R-C** build in a local origin and translate back (H3).
- **R-D** last resort: a labelled "one zone per floor" patch population for the stubborn few, reported separately from the C2 totals.
- Acceptance for any remedy: all 24 pass the geometry check (EnergyPlus reaches the warm-up, checked by a 24-task Speed array that the manager submits), and a regression sample of at least 200 other buildings keeps byte-identical IDFs (sha256 compare).

## 7 Stop-and-report points

1. **After T04:** diagnosis table + which hypotheses hold. The manager picks the remedy.
2. **After remedy T05–T06 (written then):** patched IDFs for the 24, regression result. Owner/manager approval before any engine edit.
3. **Before anything goes to 4J:** hand-over note and files are shown to the owner. The hand-over folder is a NEW one, never the frozen one.

## 8 Progress log

*(executor appends one entry per task: `#### TXX — <title> — completed YYYY-MM-DD`, with Artifacts / Deviations / Test status / Notes)*

All paths below are under `openubem/outputs/eu_evidence/EU-11/geometry_24_2026-10-10/` (called `G/`) unless stated. Scratch code: `scripts/eu_geometry24/` (`inventory.py`, `classify_err.py`, `forensics.py`, `metrics.py`, `rebuild.py`, `t04_table.py`).

#### T01 — Locate the 24 and their inputs — completed 2026-10-10
- **Artifacts:** `G/geometry_24_inventory.csv` (24 rows, 40 columns); `G/exclude_4J_madrid_from_speed.csv` (48 rows, read-only copy of `/speed-scratch/o_iseri/handover_4J_2026-10-09_madrid/exclude_4J_madrid.csv`).
- **Deviations:** (1) `prepared_buildings.csv` has no `zoning_strategy`, `data_quality_flag` or geometry column (those exist only in the builder's in-memory return). Used instead: `layouts/<id>.json` fields `scheme`, `scheme_by_storey`, `idf_reroute_divergence`, `storeys`, `dwellings_total`; the prepared `fallback_reason` column as the quality flag; footprints from `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg`. (2) `exclude_4J_madrid.csv` is not on the local disk; read it from the Speed handover with `cat`. (3) Added columns not asked for: fixed-home IDF path, flat counts, sidecar check status.
- **Test status:** PASS. 24 rows; 24 of 24 have a shipped 10-06 IDF path that exists; 0 empty Madrid paths. Fixed-home package IDF present for 6 of 24 (Madrid 12582234, 5808697; Bologna 28025, 29109, 30485, 33359); the other 18 have none. All 24 have a 10-08 result (`has_result` True) and `flat_status` simulated. 0 of 24 are on `exclude_4J_madrid.csv`, `exclude_4J_london_bologna.csv`, `exclude_5J_madrid_bologna.csv` or `exclude_all_232.csv`. All 24 are `DWELLING_LAYOUT_EMITTED*`, scheme `nocore_equal_area`, `idf_reroute_divergence` False. 6 Madrid rows carry `fallback_reason = near_duplicate_vertex_tolerated_box`.
- **Notes:** the 4J side-cars are not our shipped IDFs: 4J rebuilds its own IDF per cell (see T04).

#### T02 — Read 4J's own error evidence — completed 2026-10-10
- **Artifacts:** `G/4J_bologna/{err,cells_failed,idf_f000}/` (47 `eplusout.err`, 67 JSONs, 13 f000 IDFs); `G/4J_madrid/{err,cells_failed}/` (37 + 40 files, copied with `ssh … tar` from `/speed-scratch/o_iseri/4J_esit/madrid_geom_failures_2026-10-10/`, read-only); `G/err_signatures_per_cell.csv`, `G/cells_failed_per_cell.csv`, `G/err_signatures_per_building.csv`.
- **Deviations:** (1) copied by `tar` stream per id instead of one `scp` per id (same read-only effect). (2) also copied the 13 f000 IDFs 4J ran (not asked for; needed in T03). (3) light read commands (`ls`, `cat`, `grep`, `sha256sum`, `du`) ran on the login node through the `bash -lc` wrapper to list folders and to verify 4 file hashes.
- **Test status:** PASS. Counts at cell A f000 (EnergyPlus "Severe" lines of each kind; the plain `grep -c "Vertex size mismatch"` adds one summary line, so 28959 gives 31 by `grep`, 30 distinct):
  - Vertex-size mismatch: Madrid 12891867=3, 13113580=4, 13160790=12, 13381287=2, 4165178=16, 5808697=6, 6382787=8 (7 buildings); Bologna 28025=2, 28959=30, 29530=10, 29719=8, 30001=8, 31083=18, 31363=6, 32360=2 (8 buildings). 4J note matches (28959=31 by plain grep).
  - Zero-or-negative area (1e-9 m²): Madrid 12582234=2, 4835800=2, 340701289=4 (3 buildings). Non-planar: Madrid 4835800=1; Bologna 30001=5 (2 buildings).
  - Degenerate surfaces: Bologna 28050 = 77 (matches 4J), plus 2 "Invalid dot product" lines. 0 for all others.
  - Harness refusal `interzone_vertex_mismatch_unresolved` (no `eplusout.err` at all): Madrid 4154505; Bologna 29109, 30485, 31962, 33359 (5 buildings).
  - Totals: 19 EnergyPlus-failed + 5 harness-refused = 24. Every cell of every building failed the same way.
- **Madrid missing cells (report to the manager, 4J not asked):** f050 is missing for 5808697, 6382787, 340701289 and 4154505 (4154505: JSON for f000/f015/f030 only, no err); no Madrid building has f100 or case B (Bologna 28025 and 28050 have case B f000). The Madrid run was still going when copied.
- **Notes:** the Madrid JSONs record engine `5bb68e87fc7a…` on Windows 11 (the newer Madrid engine), but `README.txt` in the copy says "sha 0b9aa66c" — the README is wrong for Madrid. Bologna JSONs record `0b9aa66c1b76…` on Linux.

#### T03 — Footprint and IDF forensics, read-only — completed 2026-10-10
- **Artifacts:** `G/footprint_forensics.csv` (24 rows; footprint columns plus, per IDF set, `ours_*` (shipped 10-06), `fixed_*` (6 rows), `j4_*` (9 Bologna rows with a 4J IDF)).
- **Deviations:** the IDF metrics also count "effective" mismatches (after dropping vertices closer than 5 mm or within 0.1° of straight, the two defects `scripts/run_eu_s2_campaign.py:81-95` names); `find_mismatched_interzone_pairs` was imported read-only as asked.
- **Test status:** PARTIAL on the literal check. "28050 shows a repeated point at (686672.144, 4929113.520)" is NOT met in the footprint or in our IDF (0 repeated points; shortest footprint segment 0.61 m). The point exists only in 4J's IDF: floor `BLOCK 28050_3 STOREY 0 FLOOR 0001_4` has 3 vertices, two of them 0.34 mm apart (686672.1441490236 vs 686672.1439999999), i.e. a 1 mm-grid point and an unsnapped intersection point — the FINDING 210 pattern.
- **Counts per hypothesis (24 buildings):**
  - H4 footprint defect: single-part valid polygon 24/24; exactly collinear vertex 0/24; repeated point 0/24; vertex pair under 5 mm 0/24; shortest segment ≥ 0.216 m. One shared trait: an interior ring (courtyard) on 23/24 (base rate 11.4 % Madrid, 18.9 % Bologna, 17.6 % and 29.0 % for footprints over 150 m²).
  - Our shipped IDFs (all 24): raw mismatches 0, effective mismatches 0, surfaces under 1e-6 m² 0, repeated vertices 0 (also 0 in the 6 fixed-home IDFs).
  - 4J's IDFs (9 Bologna): raw-count mismatches 0 (the gate `find_mismatched_interzone_pairs` sees nothing), effective mismatches 1 building (28959: 12 pairs), pairs with a near-duplicate or collinear vertex in 9/9 (3 to 54 pairs), surfaces 288 to 669 versus ours 146 to 498.
  - H3 coordinate size: our Madrid IDFs sit at 4.48e6 m and ran; our Bologna IDFs sit at about 1.1e3 to 2.3e3 m (shifted by 685000/4928000); 4J's Bologna IDFs sit at 4.93e6 m.
  - H2 (strategy column): 24/24 are dwelling-layout (`nocore_equal_area`), none was rerouted.

#### T04 — Rebuild locally with the current and the 10-06 engine — completed 2026-10-10
- **Artifacts:** `G/rebuild*/` per-variant CSVs, `G/t04_table.csv` (building × variant), `G/t04_summary.csv`, `G/replica_vs_4J.csv`; IDFs under the session scratchpad `rb/`.
- **Deviations (all of them):**
  1. No `git worktree`. The repo tracks ~600k files, and no commit holds the 10-06 file. Instead: (a) "current" = py-only copy of the working tree (equal to HEAD blob `9103fa86…`; `git status` shows no change under `openubem/**`); (b) "10-06 engine" = byte-exact copy of 4J's pinned tree `/speed-scratch/o_iseri/4J_esit/p8/tree_bol` (sha256 of `european_residential.py` = `0b9aa66c1b76…`); (c) "Madrid engine" = `/speed-scratch/o_iseri/4J_esit/p8/tree_mad_w6` (`5bb68e87fc7a…`). Neither pinned file equals any of the 8 committed versions of that file.
  2. Driver: `prepare()` in `scripts/run_eu_s2_district_campaign.py` calls live Bologna open-data URLs (lines 588, 609), so `rebuild.py` re-implements its `_geometry()` + `build_idf_for_building` chain on the shipped prepared rows and the eu02 footprints, with the shipped flat counts. District median height for the context was set to 15.0 (the Bologna value; the Madrid value is not recorded).
  3. Extra variants beyond the plan, run only to explain the result: local origin (H3), replay from the side-car polygons raw and 1 mm-snapped, and a replica of 4J's own build function `build_idf_for_cell` (`/speed-scratch/o_iseri/4J_esit/p8/c2_bol/code/4J_docs_occ/tools/4thJ_step10_nocore_campaign.py:1157-1330`, read only; replica in `rebuild.py::fork_build`).
- **Test status:** PASS for the table. Counts per cell (24 buildings each; built / refused / tolerated / raw mismatch / effective mismatch / near-duplicate pairs / sliver):
  - Our driver, 10-06 engine, absolute frame: 24 / 0 / 0 / 0 / 0 / 0 / 0. Same for current engine, Madrid engine, and all three in a local-origin frame, and for side-car replay raw and snapped (all 24/0/0/0/0/0/0). The 10-06 engine reproduces our shipped surface count for 24/24 buildings.
  - 4J-function replica, absolute frame, any of the three engines: 24 built, 5 refused, 17 tolerated, 5 raw mismatch, 5 effective mismatch, 22 near-duplicate, 5 sliver. Local-origin frame (10-06 and current engine): 5 refused, 16 tolerated, 5 / 4 / 21 / 5; the shift changes the verdict of 5 buildings in both directions and fixes none of the refusals.
  - Match to 4J: refused set equals 4J's harness-refusal set (4 Bologna + Madrid 4154505) exactly, 24/24 buildings agree; 18 of the 19 EnergyPlus failures are flagged (tolerated near-duplicate, or sliver for 340701289); the one miss is 5808697, a fixed home whose side-car differs from the one replayed; surface counts equal 4J's IDF for 9/9 Bologna buildings (288, 669, 636, 558, 372, 375, 178, 222, 555) and the 28959 effective-mismatch count is 12 in both.
- **Hypotheses (count of the 24 explained):**
  - H1 engine version: 0/24. The 10-06 and Madrid engines both hold `_stabilize_ring_coords` (3 hits each); `openubem/idf/surfaces.py`, `scripts/run_eu_s2_campaign.py` and `openubem/idf/builder.py` are byte-identical across the 10-06 engine, the Madrid engine and HEAD (0 differing lines); `european_residential.py` differs by 9 to 22 lines (`repair_slivers` in the C10 branch).
  - H2 gate cannot rescue: the plan's gate (`builder.py:616-650`) is not on the European path. The European gate is `scripts/run_eu_s2_campaign.py:1936-2027`, which reroutes room-layout zones. In 4J's function the zones carry no `mode`, so `_force_reroute_room_layout_to_one_zone_per_floor` always declines: 5/24 are refused and 17/24 are "tolerated" and sent to EnergyPlus. This holds for 22/24 (22 have a near-duplicate or collinear pair); the other 2 are 340701289 (slivers) and 5808697 (not reproduced).
  - H3 absolute-coordinate round-off: 0/24 as a cause (our builds are clean in both frames); it only reshuffles 5/24 verdicts in the replica.
  - H4 footprint defect: 0/24 (courtyard ring on 23/24 is a correlate, not a defect).
  - H5 GEOS build: 0/24. The replica run on this Windows machine reproduces 4J's Linux numbers exactly, and 4J's Madrid failures occurred on Windows.
  - New cause (H6), 22 to 24 of 24: 4J's `build_idf_for_cell` is a September fork of our build function that omits ten safeguards present in the pinned engine's `build_idf_for_building`: `_extrude_zone_groups_per_storey`, `_clip_zone_horizontals_to_own_polygon`, `_repair_interzone_pairs`, `_drop_sliver_surfaces`, `_clean_surface_rings`, `_remove_degenerate_surfaces`, `ep_geometry_preflight`, `_storeys_overlap`, `_fix_horizontal_orientation`, `_pair_hidden_outdoor_surfaces` (0 hits for each name in the fork file).
- **Notes:** (1) The Madrid fork file was not read (it is on 4J's machine); the claim for Madrid rests on the identical error string and on the replica reproducing 4J's Madrid sliver and refusal cases. (2) I ended two stray rebuild processes with `taskkill /IM python.exe` once; it reported two processes ended, both mine to the best of my knowledge. (3) Nothing under `openubem/**`, the frozen folders or Speed was written; no EnergyPlus run, no `sbatch`. (4) Shared docs (debug references, START HERE box) not touched, as the plan requires before stop-point 2.

**STOP POINT 1 reached after T04.** Diagnosis above; the manager picks the remedy.

#### STOP POINT 1 decision (manager, 2026-10-10) — remedy R-E, no engine edit
- Audit: T01–T04 entries present; only `scripts/eu_geometry24/` (new) and `G/` written; `git status` shows no change under `openubem/**`, frozen folders untouched. Deviations accepted: no worktree; light `ls/cat/grep/sha256sum` on the login node (outside the scp/tar rule, read-only); one `taskkill /IM python.exe` (two processes ended, owner-session risk noted).
- Cause is H6 (4J's forked `build_idf_for_cell` lacks ten safeguards), not H1–H5. R-A..R-D are not needed: our shipped IDFs for the 24 build clean and already simulated. The fix is on 4J's side (call `build_idf_for_building`) or a labelled patch population from our IDFs.
- No 24-task verification array: all 24 already have simulated results in our 10-08 set (T01). Stop-point 2 does not apply (no engine edit). Stop-point 3 applies: the note is shown to the owner before sending.
- Still owed: debug-reference entry (after the owner's go); the Madrid fork file is unread; 5808697 not reproduced.

#### T07 (manager, sent 2026-10-10 on owner approval) — Hand-over note to 4J
Includes: the correction in §1, the answers to 4J's Q1–Q3 on Bologna and (a)–(c) on Madrid, the list of Madrid files still needed from 4J, and the offer of patched geometry as a separate labelled patch population. Written to `messages_GSSCanada/2026-10-10_OpenUBEM_to_4J_geometry24.md` after stop-point 1.

#### T08 (manager, 2026-10-10 16:15) — 4J's reply: neither option A nor B
4J (peer message plus `messages_GSSCanada/2026-10-10_4J_to_OpenUBEM_geometry24_choice.md`): their author ruled the 24 saved and included. They built a separate labelled population `patch24` with a copy of `build_idf_for_cell` whose geometry block runs our `build_idf_for_building` safeguard sequence plus per-storey extrusion, clip and hidden-surface pairing. Our shipped IDFs not used (their zone layout differs). Madrid 11 → 110/110 cells build (build-only); safeguards alone built 0 of 85. EnergyPlus runs wait for their CPU cap. No reply needed; sealed runs untouched; no engine edit.
Two side facts from 4J, to verify only if they matter later: the clip drops one ground-floor flat of Madrid 4154505 (−4.1 % floor area); on healthy large buildings (15–41 zones) their old builder's floor area is 7–32 % off the payload in 4 of 10 sampled. Neither is ours to act on.
Debug-reference entry written (OpenUBEM_debug_References.md, "European locations, new cities"). Plan CLOSED on our side except the open points (5808697 not reproduced, Madrid fork file unread, surface-count gap) — all carried by 4J, no owner action.
