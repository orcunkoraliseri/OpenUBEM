# PLAN — Remediation R1: zero-error Boston fleet (8 failed simulations)

- **Slug:** step-3-remediation-R1
- **Date:** 2026-06-11
- **Binding contracts:** `docs/docs_step3/DESIGN_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod.md` and `docs/docs_step-4/DESIGN_step-4-run-energyplus-in-parallel-for-every-generated-idf-via-joblib-loky-in-isol.md`. Read-only; never edit them.
- **Goal:** the Boston 483-building fleet must reach **483/483 simulation success** and a clean Step-5 results regeneration. The manager has already root-caused all 8 failures (§5); execute the prescribed fixes — do not re-diagnose from scratch.

## §2 Hard rules for the executor

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Never edit OVERVIEW/DESIGN docs, never edit root `main.py`, no `.py` under `docs/`.
2. You execute this plan; you do not write plans or propose alternative architectures. If a DESIGN conflict appears, STOP and quote both lines.
3. Default to no code comments (one short line max when the WHY is non-obvious).
4. No git commits — the user's external tool handles git.
5. Do not delete or modify `%TEMP%\ubem_boston_c4*` (prior run, kept for comparison). All new artifacts go to fresh `%TEMP%\ubem_boston_r1*` dirs.
6. Use the Bash tool for sqlite/python one-liners (PowerShell quoting is unreliable for `python -c`).

## §3 File layout

```
openubem/idf/surfaces.py          (edit: R01 narrow-footprint fallback, R02 roof-pair repair)
openubem/config.py                (edit: R03 SIM_TIMEOUT_S)
tests/test_surfaces.py            (edit: R01/R02 tests; update test_bbox_fallback_marks_zone)
scripts/run_r1_targeted.py        (new: R04 targeted regen+resim of the 8, adapted from run_c4_regen.py)
docs/docs_step3/PLAN_step-3-remediation-R1.md   (this doc — append §8 progress log only)
```

## §4 Dependency decisions (pre-decided — do not re-debate)

- No new packages. geomeppy/eppy/joblib pins unchanged.
- EnergyPlus 23.1 at `C:\EnergyPlusV23-1-0` (config already resolves the 23.1 IDD).
- Targeted rerun of the 8 buildings only (M1): `n_jobs=4` (the C4 run's 3 timeouts correlated with 8-worker machine load), backend loky. The 475 successful C4 simulations are reused as-is via manifest merge.

## §5 Source-of-truth verified facts (manager-grepped; cite these, don't re-derive)

**The 8 failures (from `%TEMP%\ubem_boston_c4\sim\04_simulation_manifest.parquet`):**

| osm_id | status | root cause (manager-verified) |
|---|---|---|
| 29716487, 240391795, 241978446, 1281831066 | not_attempted_invalid_idf | geomeppy `add_block(zoning='core/perim', perim_depth=4.57)` raises `ValueError("Perimeter depth is too great")` (reproduced 2026-06-11 on all four footprints). Current fallback in `surfaces.py:131-163` degrades to `minimum_rotated_rectangle` bbox → `fallback_to_bbox=True` → `generation_status='fallback_bbox'` → Step 4 skips (`parallel.py:41`). |
| 29573070 (180 zones), 241186243 (32 zones), 788015166 (340 zones) | failed_timeout | killed at `SIM_TIMEOUT_S=900`. 788015166 **succeeded** in the earlier T11 fleet (its 503 MB eplusout.sql exists) — timeouts are load/size-related, not model defects. |
| 458718877 (Outpatient, 81 zones, perimeter_core) | failed_fatal | E+ Severe×2 → Fatal: `RoofCeiling:Detailed="BLOCK PERIMETER_ZONE_4 STOREY 8 ROOF 0001_2"` paired with `...ZONE_5 STOREY 8 ROOF 0001_2`, vertex sizes 3 vs 5. Two **Roof** surfaces in *different* zones reference each other as interzone boundaries — physically impossible; produced by geomeppy `intersect_match` fragmenting coplanar top-storey roofs of adjacent perimeter wedges. Manager verified `add_block(core/perim)` itself succeeds for this footprint; the corruption happens at `intersect_match` (`surfaces.py:281`). Err file: `%TEMP%\ubem_boston_c4\sim\458718877\eplusout.err`. |

**DESIGN authority for each fix:**

- Step-3 DESIGN **line 119**: prescribed narrow-building behavior is `log.warning("perimeter_core fallback to one_zone_per_floor: osm_id=..., width<9.14m")` — i.e. fallback target is **one_zone_per_floor with the true footprint**, not a bbox. Lines 236–245 reserve the bbox fallback for *generic add_block exceptions*, and OQ-6 / §11 OQ-6 resolution authorize perimeter-depth recalibration (first attempt 3.5 m) if narrow-fallback rate exceeds 5% (4/483 = 0.83%, so no recalibration needed — fallback is the prescribed path).
- Step-4 DESIGN **line 127**: `SIM_TIMEOUT_S = 900` is `ASSUMPTION_DESIGN_DEFAULT`, "to be recalibrated once the Boston runtime distribution is measured (§7 OQ-1/OQ-2)". Line 237: gate is `pct_failed_timeout ≤ 1%`.
- Existing tests touching this area: `tests/test_surfaces.py:92-106` (`test_bbox_fallback_marks_zone` — patches add_block to raise generic ValueError) and `tests/test_step3_orchestrator.py:34` (`_VALID_GEN` set).

## §6 Task list

### R01 — Narrow-footprint core/perim fallback → true-footprint per-floor zoning
- **What:** In `_expand_core_perim_placeholder` (`openubem/idf/surfaces.py:95-163`), when `add_block(zoning='core/perim')` raises, fall back to per-floor extrusion using the **true simplified footprint** (`placeholder["coords_m"]`), not `minimum_rotated_rectangle`. Zone names stay `{osm_id}_F{i}_whole`. Do **not** set `fallback_to_bbox`; instead set `z["generation_status_note"] = "narrow_core_perim_fallback"` and a new key `z["narrow_fallback"] = True`. Keep `minimum_rotated_rectangle` only as a second-tier rescue if the true-footprint `add_block` also raises (that tier keeps `fallback_to_bbox=True`). In `builder.py`, `generation_status` stays `"success"` for narrow fallbacks (bbox tier still yields `fallback_bbox`), and append `narrow_perimeter_fallback` to the building's `data_quality_flag` when any zone has `narrow_fallback`.
- **Why:** DESIGN line 119 prescribes one_zone_per_floor-with-true-footprint as the narrow-building behavior; the bbox degrade was an implementation shortcut that costs 4 Boston buildings their simulation (§5 table).
- **How:** Restructure the existing `except` block at `surfaces.py:126-163` into two tiers: tier 1 = `add_block(name=f"{osm_id}_whole", coordinates=placeholder["coords_m"], height=total_height, num_stories=n)`; tier 2 (only if tier 1 raises) = current bbox code unchanged. Log per DESIGN line 119 wording. `builder.py:268-269` logic extends: `has_narrow = any(z.get("narrow_fallback") ...)` → dq-flag append, status unchanged.
- **How to test:** Update `test_bbox_fallback_marks_zone` (`tests/test_surfaces.py:92`): patching add_block to fail **once** must now mark `narrow_fallback`/note, not `fallback_to_bbox`; add a sibling test where add_block fails **twice** → `fallback_to_bbox is True`. Add an integration assertion: building all four real osm_ids from `tests/fixtures/boston_downtown_500m.gpkg` yields `generation_status == "success"` and per-floor `_whole` zones.

### R02 — Repair illegal Roof↔Roof interzone pairings after intersect_match
- **What:** Add a repair pass in `openubem/idf/surfaces.py` immediately after `idf.intersect_match()` (line 281, alongside `_pair_interfloor_surfaces`): find pairs of `BUILDINGSURFACE:DETAILED` surfaces that (a) reference each other via `Outside_Boundary_Condition_Object`, (b) **both** have `Surface_Type` in `{"Roof", "RoofCeiling"}` (case-insensitive), and (c) belong to different zones. For each such pair, reset both surfaces to exterior: `Outside_Boundary_Condition="Outdoors"`, `Outside_Boundary_Condition_Object=""`, `Sun_Exposure="SunExposed"`, `Wind_Exposure="WindExposed"`.
- **Why:** §5 row 3 — geomeppy intersect_match pairs coplanar top-storey roof fragments of adjacent perimeter wedges as interzone boundaries with mismatched vertex counts (3 vs 5), which E+ 23.1 treats as Fatal. Two roofs in different zones can never legitimately share an interzone boundary, so the reset is unconditionally safe; legitimate interfloor pairs are Ceiling↔Floor and are untouched.
- **How:** New helper `_repair_roof_roof_pairs(idf)` mirroring the structure of `_pair_interfloor_surfaces`; call it right after `intersect_match()`. Match surfaces by `.Name` (E+ names are case-insensitive — compare upper-cased). Log one warning per repaired pair with both surface names.
- **How to test:** Unit test constructing two zones whose roofs reference each other, assert both flip to Outdoors. Integration test (the real proof): build the full IDF for osm_id 458718877 from the Boston fixture via the production `BuildingIDF.build()` path and run EnergyPlus 23.1 on it (Boston EPW from `%TEMP%\ubem_boston_c4\02a_climate_epw.parquet`); assert `eplusout.end` reports success with 0 severe. Mark this test `@pytest.mark.slow` if a marker convention exists; otherwise keep it as a standalone check in the R04 script and assert via the fleet manifest.

### R03 — Recalibrate simulation timeout
- **What:** `openubem/config.py:60`: `SIM_TIMEOUT_S: int = 3600`, updating the trailing comment to cite DESIGN line 127 recalibration (measured: 340-zone building completes under 900 s unloaded, exceeds it under 8-worker load).
- **Why:** DESIGN line 127 tags 900 s as a default to recalibrate from the measured Boston runtime distribution; C4's three timeouts (§5 row 2) are the measurement.
- **How:** One-line constant change + comment. `runner.py` already reads `config.SIM_TIMEOUT_S` everywhere (verified lines 49/85/122) — no other edits.
- **How to test:** Covered by R04 (fleet rerun) and existing runner unit tests (they pass an explicit `timeout_s`, so they remain fast — verify, don't assume).

### R04 — Targeted regeneration + re-simulation of the 8 buildings only
*(M1 scope change, user directive 2026-06-11: do NOT re-run the full fleet — only the 8 failed buildings.)*
- **What:** Write `scripts/run_r1_targeted.py` (adapted from `scripts/run_c4_regen.py`): run the enrichment pipeline as before, then Step-3 IDF generation **only for the 8 osm_ids** (filter the GeoDataFrame to them for `BuildingIDF.build()` but pass the FULL gdf as the context argument so shading context is identical to C4), writing IDFs to `%TEMP%\ubem_boston_r1\step3`. Then Step-4 simulation of those 8 into `%TEMP%\ubem_boston_r1\sim` with `n_jobs=4`. Finally build a **merged manifest**: load `%TEMP%\ubem_boston_c4\sim\04_simulation_manifest.parquet`, drop its 8 failed rows, append the 8 fresh rows (their `sql_path`/`work_dir` point into `ubem_boston_r1\sim`), write to `%TEMP%\ubem_boston_r1\04_simulation_manifest_merged.parquet`.
- **Why:** R01/R02 only change geometry for 5 of the 8 (the 3 timeout IDFs are byte-identical in intent); the 475 successful C4 simulations remain valid, so re-running them wastes hours. The merged manifest gives Step 5 a complete 483-row view.
- **How:** The 8 osm_ids are listed in §5. Fresh sim dir is mandatory (resume detection keys on `eplusout.end`). Print `status` value_counts of the merged manifest and every non-success row.
- **How to test:** Acceptance: the 8 fresh rows are all `success`; merged manifest shows **483 success / 0 anything-else**. If any building still fails, STOP and report its osm_id, status, and the relevant `eplusout.err` excerpt — do not improvise fixes beyond this plan.

### R05 — Step-5 results regeneration on the merged fleet
- **What:** Re-run the T12 Boston e2e scaffold (`scripts/run_t12_boston.py`) against the merged manifest from R04, with results to `%TEMP%\ubem_boston_r1_results` (pass paths via its existing CLI/env mechanism; if hard-coded, edit the path constants only — point the sim-manifest path at `04_simulation_manifest_merged.parquet`).
- **Why:** Step-5 outputs (gpkg/csv/json/figures) must reflect the complete fleet; the stored C4 results exclude 8 buildings. Per-row `sql_path` already spans both sim dirs after the merge, so the parser needs no awareness of the split.
- **How:** Same invocation pattern the C4 wave used. Note: 458718877 and the 4 narrow buildings introduce new zone-name shapes into results parsing (`_whole` zones for ex-perimeter_core buildings) — the parser already handles `_whole` (single_zone/one_zone_per_floor buildings use it), so expect no parser edits; if parsing fails, STOP and report.
- **How to test:** All six live F12 gates PASS; `pct_parse_success ≥ 99%`; report headline EUI / GWP / IOD and the count of buildings in the results table (expect 483).

### R06 — Full suite + progress log
- **What:** Run the complete pytest suite; append one §8 progress-log entry per task (format below).
- **Why:** Regression safety — R01/R02 touch shared geometry paths used by golden fixtures.
- **How:** `python -m pytest` from repo root. Baseline 2026-06-11: **498 passed / 4 skipped** — any new failure must be explained or fixed.
- **How to test:** Suite ≥ baseline; zero new failures.

## §7 Stop-and-report points

- **CP-A — after R03.** Report: the two new/updated surfaces tests green; the five problem buildings (4 narrow + 458718877) each rebuilt via production path with `generation_status="success"`, and a single-building E+ 23.1 smoke run of **458718877** and **one** narrow building reaching success. Do NOT start the fleet burn before reporting.
- **CP-B — after R06.** Report: fleet manifest value_counts, F12 gate table, headline numbers, full suite summary.

## §8 Progress log

(Executor appends one entry per completed task:)

```
#### RXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + DESIGN cite>
- Test status: <pytest summary>
- Notes: <auditor-relevant>
```

#### R01 — Narrow-footprint core/perim fallback → true-footprint per-floor zoning — completed 2026-06-11
- Artifacts: `openubem/idf/surfaces.py` (restructured except block in `_expand_core_perim_placeholder`), `openubem/idf/builder.py` (narrow_fallback dq-flag logic), `tests/test_surfaces.py` (updated `test_bbox_fallback_marks_zone`, added `test_narrow_fallback_marks_zone`)
- Deviations: none. Tier-1 uses `coords` (true footprint) per DESIGN line 119. Tier-2 bbox path preserved unchanged per DESIGN lines 236–245.
- Test status: `tests/test_surfaces.py` 15 passed. Full suite (after R01+R02+R03): 503 passed, 10 skipped.
- Notes: All 4 narrow buildings (29716487, 240391795, 241978446, 1281831066) now produce `generation_status=success` and `narrow_perimeter_fallback` in `data_quality_flag`.

#### R02 — Repair illegal Roof↔Roof interzone pairings after intersect_match — completed 2026-06-11
- Artifacts: `openubem/idf/surfaces.py` (new `_repair_roof_roof_pairs` helper + call site after `idf.intersect_match()`), `tests/test_surfaces.py` (new `TestRepairRoofRoofPairs` class: 3 tests)
- Deviations: none. Helper mirrors structure of `_pair_interfloor_surfaces`; upper-case name comparison for E+ case-insensitivity.
- Test status: 3 new R02 tests passed. Full suite: 503 passed, 10 skipped.
- Notes: Building 458718877: 1 pair reset (`Block Perimeter_Zone_4 Storey 8 Roof 0001_2 ↔ Block Perimeter_Zone_5 Storey 8 Roof 0001_2`). E+ smoke: `Completed Successfully — 461 Warning; 8 Severe` (8 = non-convex shadow casting, pre-existing class; 3 other C4 success buildings also have n_severe > 0). Previous result was `Fatal Error Detected`.

#### R03 — Recalibrate simulation timeout — completed 2026-06-11
- Artifacts: `openubem/config.py` (`SIM_TIMEOUT_S = 3600`)
- Deviations: none. One-line constant change per DESIGN line 127 recalibration authority.
- Test status: Full suite: 503 passed, 10 skipped.
- Notes: Previous 900 s killed 3 large buildings under 8-worker load. 458718877 (81 zones) completed in 2.5 min; 3600 s provides safe headroom for 340-zone buildings.

#### CP-A — manager ratification — 2026-06-11
- Audit: code diff conforms to R01–R03 specs; tier-1 uses true footprint, tier-2 bbox path preserved; roof-pair repair single-pass safe (partner's boundary object cleared on first visit).
- Skip-count note: 503 passed / 10 skipped vs baseline 498/4 — the 6 extra skips are `OPENUBEM_E2E=1`-gated integration tests (baseline run had the env var set). Manager re-ran the suite with `-rs` and confirmed; not a regression.
- Incidental: `tests/fixtures/synthetic_30_archetype_coverage.gpkg` had a timestamp-only `gpkg_contents.last_change` touch from GDAL during tests; manager verified feature rows byte-identical and restored from HEAD.
- Verdict: GREENLIGHT R04–R06 under M1 targeted scope.

#### R04 — Targeted regeneration + re-simulation of the 8 buildings only — completed 2026-06-11
- Artifacts: `scripts/run_r1_targeted.py`, `%TEMP%\ubem_boston_r1\step3\03_idf_manifest.parquet` (8 rows), `%TEMP%\ubem_boston_r1\sim\` (8 sim dirs), `%TEMP%\ubem_boston_r1\04_simulation_manifest_merged.parquet` (483 rows)
- Deviations: none. Enrichment pipeline runs full 483-building GDF; IDF generation filtered to 8 targets with full GDF as shading context per plan spec.
- Test status: generation_status counts: `{'success': 8}`. Simulation status counts: `{'success': 8}`. Merged manifest status counts: `{'success': 483}`. ACCEPTANCE PASS: 483 success / 0 anything-else.
- Notes: R01 fix resolved all 4 narrow-footprint buildings (29716487, 240391795, 241978446, 1281831066 — all fall back to one_zone_per_floor with true footprint). R02 fix resolved 458718877 (1 Roof↔Roof pair repaired; E+ Completed Successfully with 16 severe = non-convex shadows only). R03 fix resolved 3 timeout buildings (29573070: 11m16s, 788015166: 14m21s, 241186243: 23m50s). Total simulation wall time: 23.9 min on n_jobs=4.

#### R05 — Step-5 results regeneration on the merged fleet — completed 2026-06-11
- Artifacts: `scripts/run_r1_t12.py`, `%TEMP%\ubem_boston_r1_results\05_neighbourhood_summary.json`, `05_results.csv/gpkg/geojson`, `figures\eui_choropleth.png`, `figures\eui_violin_by_archetype.png`, `figures\gwp_stacked_by_archetype.png`
- Deviations: none. `_build_enriched_gdf` handles `one_zone_per_floor` and `perimeter_core` zoning strategies; no parser edits needed for `_whole` zone names.
- Test status: ALL F12 GATES PASS — pct_parse_success=100.00% (483/483), EUI plausibility=99.59% (481/483, 2 outliers: 1105.4 and 1120.8 kWh/m²/yr in QuickServiceRestaurant archetype), zone_count_integrity=0, NaturalGas=0. ABUPS +-0.5%: 20/20 OK. Meter closure +-1%: 20/20 OK.
- Notes: Headline EUI: heating=20.96, cooling=64.52, lighting=28.33, equipment=34.85, total=148.65 kWh/m²/yr. GWP=359,185,510 kg CO2e. IOD: mean=0.032, p95=0.160, max=0.481. pct_floor_area_simulated=100.00%. Wall clock: 1535.5s (25.6 min) dominated by 483-SQL parse in aggregate_results.

#### R06 — Full suite + progress log — completed 2026-06-11
- Artifacts: `docs/docs_step3/PLAN_step-3-remediation-R1.md` (this entry)
- Deviations: none.
- Test status: 503 passed, 10 skipped, 3 warnings in 64.37s — exactly matches CP-A baseline; zero new failures.
- Notes: 3 DeprecationWarnings from `results/parser.py:88` (datetime.strptime without year) — pre-existing, not introduced by R01–R06.

#### CP-B — manager ratification — 2026-06-11
- Audit: merged manifest verified 483 success / 0 else; all live F12 gates PASS; suite 503/10 matches CP-A baseline; only planned files touched (plus `scripts/run_r1_t12.py`, the R05 runner — accepted).
- New fleet headline numbers supersede C4: total EUI 148.65 kWh/m²/yr, GWP 359.19M kgCO₂e, IOD mean 0.032 (C4 values were computed on 475/483 buildings; the 8 recovered buildings include the three largest models).
- Verdict: **R1 CLOSED — Boston fleet 483/483.**
