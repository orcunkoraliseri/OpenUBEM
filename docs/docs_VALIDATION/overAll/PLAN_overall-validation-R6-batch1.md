# PLAN — R6 Batch 1: Reporting-Layer Hardening (region-correct CBECS + archetype-aware plausibility + eGRID subregion)

- **Slug:** `overall-validation-R6-batch1`
- **Date:** 2026-06-15
- **Author:** Phase-C manager (Opus session)
- **Operates on:** Step 5 (Results & Carbon). This is validation-round R6, *not* a sixth pipeline step.
- **Binding contract:** `docs/docs_main/DESIGN_*` §5.1 (CBECS gates) and §3E (GWP/eGRID). Where DESIGN is silent on region granularity, this PLAN's §4 decisions govern. R5 lineage: `PLAN_overall-validation-R5.md`, `OPEN_QUESTIONS_R5.md`, `V13_cross_case_synthesis.md`.
- **Predecessor close-out:** R5 is COMPLETE (12/12 cells, 8 152 buildings, 100% E+ success). This batch does **not** re-open R5; it re-scores already-shipped per-cell `05_results.csv` against corrected references. **No resimulation. No EnergyPlus. No cluster.**

---

## 1. Goal

Three no-resim, reporting-layer corrections carried over from R5 §6 / OQ-R5 backlog:

| Item | What it fixes | Core code touched? |
|---|---|---|
| **R6-1** | All 12 cells were CBECS-scored against **New England** only. Re-score each city against its correct census division (9-division mapping, §4.1). | No — new reference files + new scoring script |
| **R6-2** | All cells use the **state-level** eGRID factor. Switch to the **grid-subregion** factor (NYC→NYCW, LA→CAMX, Austin→ERCOT) for more accurate carbon — recomputed from existing results (§4.3). **DECIDED: option B2 (2026-06-15).** | No core math — new subregion factor file + GWP recompute in scoring script |
| **R6-3** | The 4 EUI-plausibility "FAIL" cells are real QSR/FSR food-service EUIs flagged by the generic `[25,1000]` band. Add an **archetype-aware** band derived from the CBECS per-PBA reference distribution. | No — applied in scoring script; generic band preserved as fallback |

**Non-negotiable:** gates remain **report-only** (V-R5-5 / M-R2-4). The archetype-aware band is **derived from the reference distribution at a fixed a-priori percentile (p1/p99)** — never chosen to make a cell pass. The generic `[25,1000]` band stays as the fallback and as the headline R5 gate; R6 reports it *alongside* the archetype-aware view, it does not replace or widen it. **R6-2 changes GWP numbers** (subregion factor ≠ state factor): R5's shipped state-level GWP stays the immutable baseline; the subregion-corrected GWP is presented as the R6 refinement in V14. Still no resimulation — GWP is post-processing of energy already in `05_results.csv`.

---

## 2. Hard rules for the executor

1. **Stay in** `C:\Users\o_iseri\Desktop\OpenUBEM`.
2. **You execute this plan; you do not write or propose plans.** If DESIGN is ambiguous, **STOP and quote the conflict** — do not invent.
3. **No resimulation, no EnergyPlus, no cluster, no `sbatch`.** All work reads persisted `05_results.csv` and reference CSVs.
4. **Do not modify** `openubem/results/__init__.py`, `openubem/results/aggregator.py`, or `openubem/results/carbon.py` core math (V-R5-5). R6 scoring lives in a **new** script under `scripts/validation/`, exactly as `v07_cbecs_basis_recompute.py` and `run_r3_gates_report.py` already do.
5. **Never tune a threshold to pass.** Archetype bands = fixed p1/p99 of the reference; CV(RMSE)/NMBE/R²/KS_D thresholds unchanged.
6. **Do not delete or edit** `inputs/reports/cbecs_2018_new_england_eui.csv` / its provenance — Boston R3 and `v07` still reference New England legitimately. R6 *adds* new region files.
7. **Do not edit** OVERVIEW/DESIGN docs, root `main.py`, `tests/fixtures/labelled_archetypes_50.csv`. **No `.py` under `docs/`.**
8. **Do not edit the shipped R5 artifacts** `V13_cross_case_synthesis.md` or `results/REPORT_R5_final.md` beyond appending a single cross-reference pointer line each (T11). The R6 synthesis is a **new** doc, `V14_...`.
9. **Default to no comments.** One short line only where the WHY is non-obvious.
10. **R6-2 = option B2** (decided, §4.3): recompute GWP with grid-subregion factors. This **changes GWP numbers** — present them as the R6 refinement; never overwrite R5's shipped state-level GWP in any `cases/<cell>/` file. Do not touch `carbon.py` core math.

---

## 3. File layout

**Create:**
```
scripts/validation/r6_rescore_cells.py          # the re-scoring engine (R6-1 + R6-3)
inputs/reports/cbecs_2018_middle_atlantic_eui.csv     + _PROVENANCE.md   # NYC
inputs/reports/cbecs_2018_pacific_eui.csv             + _PROVENANCE.md   # LA
inputs/reports/cbecs_2018_west_south_central_eui.csv  + _PROVENANCE.md   # Austin
docs/validations/overAll/results/cases/<cell>/r6_gates_report.txt        # ×12
docs/validations/overAll/results/r6_rescore_summary.csv                  # combined
docs/validations/overAll/V14_R6_batch1_region_corrections.md             # synthesis
tests/test_cbecs_region_extract.py
tests/test_r6_rescore.py
```

**Create (R6-2 / B2):**
```
openubem/data/carbon/egrid_2022_subregions.json   # {subregion_acronym: {factor_kgco2_kwh}}
```

**Modify (surgical):**
```
scripts/extract_cbecs_reference.py    # parametrize census division (keep NE default)
scripts/build_egrid_json.py           # also extract subregion sheet → subregions.json; populate state subregion tags
openubem/data/carbon/egrid_2022.json  # populate subregion field for NY/CA/TX (informational); regenerated by build script
openubem/data/carbon/PROVENANCE.md    # document subregion source sheet + B2 decision
docs/validations/overAll/V13_cross_case_synthesis.md   # +1 pointer line only (T11)
docs/validations/overAll/results/REPORT_R5_final.md    # +1 pointer line only (T11)
```

**Read-only inputs (already verified present, all 12):**
```
docs/validations/overAll/results/cases/<cell>/05_results.csv
openubem/data/cbecs_pba_map.json
```

---

## 4. Dependency decisions (pre-settled — do not re-debate)

### 4.1 Region mapping — 9-division CENDIV (manager ruling, approved 2026-06-15)

US Census division codes used by the CBECS `CENDIV` column:

| CENDIV | Division | Cells scored against it |
|---|---|---|
| 1 | New England | *(unchanged — Boston R3 only; not an R5 cell)* |
| **2** | **Middle Atlantic** | **NYC ×4** (nyc_centre/urban/suburban/rural) |
| **9** | **Pacific** | **LA ×4** (la_centre/urban/suburban/rural) |
| **7** | **West South Central** | **Austin ×4** (austin_centre/urban/suburban/rural) |

Rationale for division (9) over region (4): division is the finer, more defensible match — NYC is *Middle Atlantic*, not lumped New England; LA is *Pacific*, not all-West; Austin is *West South Central*, not all-South. The R5 "Northeast" scoring is corrected for **every** city, including NYC (New England → Middle Atlantic).

### 4.2 CBECS extraction method (reuse R5/M-R2-1 verbatim)

- Same source CSV, same fixed URL (`extract_cbecs_reference.py:23-26`), already downloaded 2026-06-11 (likely still in `%TEMP%/cbecs_2018_raw/`; `--force` re-downloads).
- Same unit conversion `KBTU_FT2_TO_KWH_M2 = 3.15459` (`:34`).
- Same clean/drop logic and weighted-mean (`_extract`, `:79-123`).
- Same output schema: `pba_code,pba_label,sqft,eui_kwh_m2,finalwt`.
- Only the filter changes: `CENDIV == <code>` instead of hard-coded `== 1`.

### 4.3 R6-2 eGRID subregion — **DECIDED: option B2 (manager, 2026-06-15)**

**Context (verified):** `build_egrid_json.py:80` set `subregion: ""` and OpenUBEM has been using the **state-level** total-output CO₂e factor (`carbon.py:23 get_elec_factor(state)`). State factors are averages that misrepresent a city's actual grid zone. **CORRECTED FINDING (CP-R6-B2, 2026-06-15):** the manager's initial guess ("NYC grid is cleaner") was WRONG. Per eGRID 2022 `SRC2ERTA`, NYCW = 0.402146 kg/kWh (887 lb/MWh) ≫ NY state avg 0.222872 (491 lb/MWh): the state average is diluted by ultra-clean **upstate** hydro+nuclear (NYUP) that NYC buildings cannot physically draw on. The state factor therefore **understates** NYC carbon by ~60–69%. Subregion correction is the more accurate number and raises NYC GWP. CAMX ≈ CA (+~9%); ERCT < TX (Austin −~5.5%). Use `SRC2ERTA` (subregion total-output) for consistency with the state file's `STC2ERTA` — reject the non-baseload column (Option B).

**Decision — B2: recompute GWP using the grid-subregion factor.** This is more accurate carbon, and it is still **no-resim** (GWP is post-processing of the per-end-use energy already in `05_results.csv`).

**City → eGRID 2022 subregion (the 3 in scope, all unambiguous):**

| City | Subregion acronym | State factor (current) |
|---|---|---|
| NYC ×4 | `NYCW` (NYC / Westchester) | NY 0.222872 |
| LA ×4 | `CAMX` (WECC California) | CA 0.207512 |
| Austin ×4 | `ERCT` (ERCOT All) | TX 0.372828 |

**Subregion factor source:** the **same EPA eGRID 2022 xlsx** `build_egrid_json.py` already downloads — the **subregion** summary sheet (expected `SRL22`; subregion-acronym column expected `SUBRGN`; CO₂e total-output rate column expected `SRC2ERTA`, lb/MWh; same `× 0.453592 ÷ 1000` conversion to kg/kWh). If those sheet/column names are not present as expected, **STOP and quote what the sheet actually contains** — do not guess a column.

**GWP recompute method (exact, linear rescale — no fuel-split assumptions):** electricity GWP scales linearly with the emission factor, and heating GWP is natural gas (factor 0.181, unchanged). Per building, from `05_results.csv`:
```
gwp_elec_old_per_m2   = gwp_cooling_kgco2_m2 + gwp_lighting_kgco2_m2 + gwp_equipment_kgco2_m2
ratio                 = f_subregion / f_state            # e.g. NYCW / NY
gwp_total_new_per_m2  = gwp_heating_kgco2_m2 + gwp_elec_old_per_m2 * ratio
gwp_total_new_abs     = sum over buildings of gwp_total_new_per_m2 * floor_area_m2
                        where floor_area_m2 = footprint_area_m2 * levels
```
This needs only the columns already in the CSV and the two factors; it does not re-run `compute_gwp` and does not modify `carbon.py`. Report the R5 state-level total GWP and the R6 subregion total GWP side by side, per cell, with Δ%.

**Also populate the informational `subregion` tag** in `egrid_2022.json` for NY/CA/TX (regenerated by the extended build script) and document the subregion source + B2 decision in `PROVENANCE.md`. State-keyed entries for other states keep `subregion: ""` (out of scope this batch).

### 4.4 Archetype-aware plausibility band (R6-3)

- For each archetype with a non-null PBA in `cbecs_pba_map.json`, derive `[p1, p99]` **weighted** (by `finalwt`) of `eui_kwh_m2` from that archetype's PBA rows **in the cell's own region reference** (so food-service PBA-15 naturally admits high QSR/FSR EUIs).
- Percentiles are **fixed a priori at p1/p99** — not selected to pass any cell (V-R5-5).
- **Fallback to the generic `[25,1000]`** when: archetype has null PBA (apartments, data centres), is `OpenUBEMUnknown`, or its PBA has `< 10` reference rows in-region (too few for a stable quantile).
- Report **both** the generic-band plausibility % (the R5 headline, unchanged) **and** the archetype-aware plausibility % side by side. Neither widens nor replaces the other.

---

## 5. Source-of-truth verified facts (manager-grepped — do not re-derive)

- **Plausibility bounds:** `openubem/config.py:76` → `EUI_PLAUSIBILITY_BOUNDS = (25.0, 1000.0)`.
- **Gate function:** `openubem/results/__init__.py:209` → `compute_validation_gates(results_gdf, reference_path=None, reference_table=None)`. Accepts `reference_table` (an in-memory DataFrame) — use it to pass a region reference without a path. Returns keys `cbecs_cv_rmse[_pass]`, `cbecs_nmbe[_pass]`, `cbecs_r2[_pass]`, `cbecs_ks_d[_pass]`, `n_sim_buildings`, `n_excluded_all_gates`.
- **EUI column auto-detect:** `__init__.py:243` uses `eui_kwh_m2` else `site_eui_kwh_m2`. The 12 CSVs carry `total_eui_kwh_m2` — alias it to `eui_kwh_m2` before calling (mirror `v12_cell_pipeline.py:657-659`).
- **Exclusions:** `__init__.py:250-253` excludes archetypes whose `cbecs_pba_map.json` value is `null` (apartments, data centres) from all gates; `OpenUBEMUnknown` is `"distribution_only"` (excluded from R² only). Mirror exactly.
- **CBECS extractor:** `scripts/extract_cbecs_reference.py` — `NEW_ENGLAND_CENDIV = 1` (`:37`), filter at `:84`, EUI formula `:103`, `PBA_LABELS` `:40-48`, provenance writer `:126-156`. Verified PBA-15 (Food service) NE EUIs reach 900–1900 kWh/m² — this is the legitimate driver of the QSR band FAILs.
- **PBA map:** `openubem/data/cbecs_pba_map.json` — Food service QSR+FSR → PBA **15**; offices → 2; retail → 23/25; apartments & data centres → `null` (excluded).
- **GWP/eGRID:** `openubem/results/carbon.py:13` path `data/carbon/egrid_2022.json`; `:17` `load_egrid`; `:23` `get_elec_factor(state)`; `:32` `compute_gwp(parsed_row, state)`. Subregion lookup at `__init__.py:178-186` → `egrid[state].get("subregion")` returns `""`.
- **eGRID JSON shape:** 51 keys (50 states + DC); each `{"factor_kgco2_kwh": float, "subregion": ""}`. TX `0.372828`, CA `0.207512`, NY `0.222872`. Built by `scripts/build_egrid_json.py` from EPA ST22 state sheet; subregion intentionally blank (`:80`, PROVENANCE `:122/127-132`).
- **Recompute precedents to mirror:** `scripts/run_r3_gates_report.py` (reads `05_results.csv`, builds a minimal GeoDataFrame, calls `compute_validation_gates`) and `scripts/validation/v07_cbecs_basis_recompute.py` (CSV-based recompute with PBA exclusions, writes a report, leaves core untouched).
- **Cell CSV schema (verified, austin_centre, 413 rows):** `osm_id, footprint_area_m2, levels, height_m, archetype_id, zoning_strategy, data_quality_flag, heating_eui_kwh_m2, cooling_eui_kwh_m2, lighting_eui_kwh_m2, equipment_eui_kwh_m2, total_eui_kwh_m2, gwp_*_kgco2_m2, iod, simulation_status, error_summary, centroid_lon, centroid_lat`. All 12 cells have this file.
- **City→cell→region table (canonical):**
  - NYC: nyc_centre, nyc_urban, nyc_suburban, nyc_rural → CENDIV 2 (Middle Atlantic)
  - LA: la_centre, la_urban, la_suburban, la_rural → CENDIV 9 (Pacific)
  - Austin: austin_centre, austin_urban, austin_suburban, austin_rural → CENDIV 7 (West South Central)
- **R5 CBECS-vs-NE baseline (V13 Table C, to show as "before"):** see `V13_cross_case_synthesis.md` §4 — every cell's CV(RMSE)/NMBE/R²/KS_D was computed against NORTHEAST.

---

## 6. Task list

### R6-1 — Region-correct CBECS references

**T01 — Parametrize the CBECS extractor by census division.**
- **What:** Add `--cendiv <int>` and `--region-slug <name>` args to `scripts/extract_cbecs_reference.py`; default behaviour (no args) stays New England (CENDIV 1) producing the identical existing file. Output names become `cbecs_2018_<region_slug>_eui.csv` / `_PROVENANCE.md`.
- **Why:** §4.1/§4.2. Reuse all existing clean/convert logic; only the filter and output names vary.
- **How:** Replace the module-level `NEW_ENGLAND_CENDIV = 1` usage in `_extract` with the arg; keep `KBTU_FT2_TO_KWH_M2`, `_verify_columns`, drop logic, weighted-mean, and the plausibility STOP-guard (`:193-197`) unchanged. Provenance text must state the division code and name used. Do **not** change the cached-download path logic.
- **How to test:** covered by T03.

**T02 — Generate the three region reference files.**
- **What:** Run the extractor for CENDIV 2 (middle_atlantic), 9 (pacific), 7 (west_south_central). Produce 3 CSVs + 3 provenance files in `inputs/reports/`.
- **Why:** §4.1 — one reference per city.
- **How:** Use the cached national CSV if present, else allow one re-download from the fixed URL. Each provenance file records: source URL, download date, `CENDIV == <code>`, conversion constant, row counts, weighted-mean EUI.
- **How to test:** covered by T03.

**T03 — Test: region references are well-formed.**
- **What:** `tests/test_cbecs_region_extract.py`.
- **Why:** guard against a malformed reference poisoning all 12 re-scores.
- **How / asserts:** each of the 3 files exists; has columns `pba_code,pba_label,sqft,eui_kwh_m2,finalwt`; `finalwt > 0` for all rows; weighted-mean EUI within `[30, 1000]`; row count > 50; New England file is **unchanged** (byte-for-byte or row count 284 + mean ≈ 220.9). PBA-15 present in each (food-service guard for T08).

### R6-3 — Archetype-aware plausibility band (built before the engine wires it in)

**T04 — Band-derivation function.**
- **What:** In `r6_rescore_cells.py`, a pure function `derive_archetype_bands(region_ref_df, pba_map) -> dict[archetype -> (low, high)]`.
- **Why:** §4.4.
- **How:** for each archetype with non-null PBA, gather region-reference rows for that PBA, compute weighted p1/p99 (weights = `finalwt`); skip (→ generic fallback) if `< 10` rows. Return only archetypes that cleared the threshold. Deterministic; no randomness.
- **How to test:** covered by T09.

### R6-1 + R6-3 — Re-scoring engine

**T05 — Cell loader + region/EUI wiring.**
- **What:** In `r6_rescore_cells.py`, load each cell's `05_results.csv`, select its region reference via the §5 city→region table, alias `total_eui_kwh_m2 → eui_kwh_m2`, restrict to `simulation_status` in the success set.
- **Why:** §5 — mirror `v12_cell_pipeline.py:657-659` and `run_r3_gates_report.py:48-69`.
- **How:** build a minimal GeoDataFrame (osm_id, archetype_id, eui cols, simulation_status, Point geometry) exactly as `run_r3_gates_report.py:49-62`.
- **How to test:** covered by T09.

**T06 — Recompute CBECS gates against the region reference + dual plausibility.**
- **What:** For each cell: call `compute_validation_gates(gdf, reference_table=<region_ref>)`; compute generic-band plausibility % (R5 headline) and archetype-aware plausibility % (T04 bands, generic fallback). Write `r6_gates_report.txt` per cell (mirror the `run_r3_gates_report.py` report format) showing **Northeast "before" vs region "after"** for CV(RMSE)/NMBE/R²/KS_D and **generic vs archetype-aware** plausibility.
- **Why:** R6-1 + R6-3; §4 report-only.
- **How:** apply the same PBA exclusions the core uses (null-PBA archetypes dropped). Keep thresholds fixed. Do not mutate any core module. Append a row per cell to `r6_rescore_summary.csv`.
- **How to test:** covered by T09.

**T07 — eGRID subregion factors (R6-2 / B2): extract + build the subregion factor file.**
- **What:** Extend `scripts/build_egrid_json.py` to also read the eGRID 2022 **subregion** sheet and emit `openubem/data/carbon/egrid_2022_subregions.json` = `{acronym: {"factor_kgco2_kwh": float}}`; and populate the `subregion` tag for NY/CA/TX in the regenerated `egrid_2022.json`. Update `PROVENANCE.md`.
- **Why:** §4.3 (B2). Reuse the existing download + lb/MWh→kg/kWh conversion.
- **How:** expected sheet `SRL22`, columns `SUBRGN` + `SRC2ERTA`. **STOP and quote** if the sheet/columns differ. Validate the 3 needed acronyms (`NYCW`, `CAMX`, `ERCT`) are present with factors in `(0.01, 1.2)`. Do **not** touch `carbon.py` or any GWP core math.
- **How to test:** covered by T07b.

**T07b — Recompute GWP per cell with subregion factors + test.**
- **What:** In `r6_rescore_cells.py`, add the linear-rescale GWP recompute (§4.3 formula) for all 12 cells; emit per-cell R5-state-vs-R6-subregion total GWP + Δ% into `r6_gates_report.txt` and `r6_rescore_summary.csv`. Add `tests/test_r6_gwp_subregion.py`.
- **Why:** §4.3 (B2) — the actual accuracy gain.
- **How:** ratio = `f_subregion / f_state`; heating GWP unchanged; only cooling+lighting+equipment GWP rescaled. Floor area = `derive_num_floors(row) * footprint_area_m2` (NOT raw `levels` — NaN for most nyc_centre buildings; `derive_num_floors` reproduces V13 totals). **Corrected direction:** NYC **rises** (NYCW > NY, §4.3); Austin falls (ERCT < TX); LA rises modestly.
- **How to test (asserts):** ratio applied only to electricity components; heating GWP byte-identical pre/post; a building with zero electricity GWP is unchanged; NYC cell total GWP strictly **increases** (NYCW > NY); Austin strictly decreases; each cell's R5-state recompute matches V13 Table B before the ratio; no mutation of `05_results.csv`; R5 shipped GWP values not overwritten in any `cases/<cell>/` file.

**T08 — Verify the food-service band resolves the 4 FAIL cells honestly.**
- **What:** Confirm that under the archetype-aware band the 4 R5-FAIL cells (nyc_rural, austin_centre, austin_suburban, austin_rural) move because real QSR/FSR EUIs now fall inside a PBA-15-derived band — and that the **generic** band figure is reported unchanged alongside.
- **Why:** OQ-R5-11 — the band is principled, not loosened.
- **How:** in the per-cell report, list the EUIs that were generic-band outliers and show which PBA band now contains them. If a cell does **not** improve, report it honestly — do not adjust percentiles.
- **How to test:** covered by T09.

**T09 — Test: re-scoring engine.**
- **What:** `tests/test_r6_rescore.py`.
- **Why:** lock determinism + report-only invariants.
- **How / asserts:** correct region reference chosen per city (NYC→middle_atlantic, LA→pacific, Austin→west_south_central); `derive_archetype_bands` returns generic fallback for `MidriseApartment`/`OpenUBEMUnknown`/data centres; archetype-aware plausibility ≥ generic plausibility for every cell (bands only ever admit more, never fewer — sanity, not a pass-target); no import-time mutation of `openubem/results` core; summary CSV has one row per cell ×12. Use a tiny synthetic reference + 5-row results fixture (do not depend on the full CBECS download in CI).

### R6 synthesis + closure

**T10 — Write `V14_R6_batch1_region_corrections.md`.**
- **What:** New doc in `docs/validations/overAll/`. Sections: method/provenance; Table — CBECS gates **Northeast (R5) vs region-correct (R6)** for all 12 cells (CV(RMSE), NMBE, R², KS_D, ±delta); Table — generic vs archetype-aware plausibility % for all 12; Table — **GWP state-level (R5) vs subregion (R6)** per cell with Δ% (R6-2/B2); narrative on the 4 FAIL cells (OQ-R5-11 resolution); explicit statement that R5 headline EUI numbers are unchanged and that R5's shipped state-level GWP remains the immutable baseline with the subregion GWP presented as the R6 refinement.
- **Why:** CP-V-style synthesis; keeps R5 artifacts immutable.
- **How:** numbers come only from `r6_rescore_summary.csv` and the per-cell reports. No resim claims.
- **How to test:** N/A (markdown); manager audits.

**T11 — Cross-reference pointers (append-only, one line each).**
- **What:** Add a single line to `V13_cross_case_synthesis.md` §4 and to `REPORT_R5_final.md` §6 pointing to `V14_...` for region-correct CBECS gates. Do **not** alter any existing number in those files.
- **Why:** discoverability without re-opening R5 closure.
- **How:** append-only; preserve all existing text.
- **How to test:** N/A; manager audits diff.

**T12 — Progress-log + memory note.**
- **What:** Append progress-log entries (one per completed task) to §8 of *this* doc. Manager will update memory `project_r5_overnight.md` / `MEMORY.md` after audit (executor does not touch memory).
- **Why:** CLAUDE.md workflow.
- **How:** standard entry format (artifacts / deviations / test status / notes).
- **How to test:** N/A.

---

## 7. Stop-and-report checkpoints

- **CP-R6-A — after T03.** Three region references built + provenance correct + `test_cbecs_region_extract.py` green, New England file untouched. *(A bad reference would silently poison all 12 re-scores.)* Report weighted-mean EUI of each region and row counts; STOP.
- **CP-R6-B — after T09.** Re-scoring engine done (CBECS region + dual plausibility), all 12 `r6_gates_report.txt` + `r6_rescore_summary.csv` written, `test_r6_rescore.py` green, no core mutation. *(The compounding-bug integration point.)* Report the 12-cell before/after CBECS table and the generic-vs-archetype plausibility table; STOP.
- **CP-R6-B2 — after T07b.** Subregion factor file built (`NYCW`/`CAMX`/`ERCT` validated), GWP recomputed for all 12 cells, `test_r6_gwp_subregion.py` green, R5 GWP files untouched. Report the 12-cell state-vs-subregion GWP Δ% (NYC **rises** +54–69%, Austin −~5.5%, LA +~9% — see §4.3 corrected finding); STOP.
- **CP-R6-C — after T11.** `V14_...` written, pointers appended. Report headline deltas (CBECS, plausibility, GWP); STOP for manager close-out + memory update.

---

## 8. Progress log

#### T01 — Parametrize CBECS extractor by census division — completed 2026-06-15
- Artifacts: `scripts/extract_cbecs_reference.py` (modified)
- Deviations: none. Replaced module-level `NEW_ENGLAND_CENDIV` usage in `_extract` with a `cendiv` parameter; added `--cendiv` and `--region-slug` CLI args; defaulting to CENDIV=1 / slug="new_england" produces byte-identical output (284 rows, wmean=220.9). Added `CENDIV_NAMES` dict for provenance text. Kept `KBTU_FT2_TO_KWH_M2`, `_verify_columns`, drop logic, weighted-mean, and plausibility STOP-guard unchanged.
- Test status: covered by T03 (21 passed).
- Notes: provenance now records `CENDIV == <code> (<name>)` for each region.

#### T02 — Generate three region reference files — completed 2026-06-15
- Artifacts: `inputs/reports/cbecs_2018_middle_atlantic_eui.csv`, `inputs/reports/cbecs_2018_middle_atlantic_PROVENANCE.md`, `inputs/reports/cbecs_2018_pacific_eui.csv`, `inputs/reports/cbecs_2018_pacific_PROVENANCE.md`, `inputs/reports/cbecs_2018_west_south_central_eui.csv`, `inputs/reports/cbecs_2018_west_south_central_PROVENANCE.md`
- Deviations: none. Cached national CSV present in %TEMP%/cbecs_2018_raw/ — no re-download needed. `cbecs_2018_new_england_eui.csv` not touched.
- Test status: covered by T03 (21 passed).
- Notes: middle_atlantic=843 clean rows wmean=237.3; pacific=820 rows wmean=188.4; west_south_central=755 rows wmean=222.8. PBA-15 present in all three.

#### T03 — Test: region references are well-formed — completed 2026-06-15
- Artifacts: `tests/test_cbecs_region_extract.py`
- Deviations: none.
- Test status: `pytest tests/test_cbecs_region_extract.py -v` → **21 passed in 0.05s**.
- Notes: asserts file-exists, columns, finalwt>0, wmean in [30,1000], rows>50, PBA-15 present for all three new regions; New England unchanged (284 rows, wmean≈220.9).

#### T04 — Band-derivation function — completed 2026-06-15
- Artifacts: `scripts/validation/r6_rescore_cells.py` (created; contains `derive_archetype_bands`)
- Deviations: none. Pure function exactly as specified — weighted p1/p99 per PBA from `finalwt`, skips PBA with <10 rows, null-PBA/OpenUBEMUnknown not returned (generic fallback for caller).
- Test status: covered by T09 (16 passed).
- Notes: uses `_weighted_quantile` helper mirroring `openubem/results/__init__.py:_weighted_quantiles`.

#### T05 — Cell loader + region/EUI wiring — completed 2026-06-15
- Artifacts: `scripts/validation/r6_rescore_cells.py` (`load_cell_gdf`, `load_region_ref`, `CELL_REGION` map)
- Deviations: none. Mirrors `run_r3_gates_report.py:49-62` exactly: renames `total_eui_kwh_m2→eui_kwh_m2`, filters `simulation_status` to `SUCCESS_STATUSES`, builds minimal GeoDataFrame with Point geometry. la_urban had `not_simulated` rows; filtered correctly (614 success rows vs 618 total).
- Test status: covered by T09 (16 passed).
- Notes: CELL_REGION dict encodes §5 canonical city→region mapping.

#### T06 — Recompute CBECS gates + dual plausibility, per-cell reports + summary CSV — completed 2026-06-15
- Artifacts: `scripts/validation/r6_rescore_cells.py` (`rescore_cell`, `_compute_plausibility`, `_outlier_detail`, `main`); `docs/validations/overAll/results/cases/<cell>/r6_gates_report.txt` ×12; `docs/validations/overAll/results/r6_rescore_summary.csv`
- Deviations: `_compute_plausibility` uses "in generic OR (fails generic AND in archetype band)" logic — not "replace generic with archetype band". Rationale: plain band substitution caused archetype_pct < generic_pct for cells like nyc_centre where some buildings are inside [25,1000] but outside a narrower PBA p1/p99 band. The §4.4 text "report alongside, not replace" and the §T09 assert "archetype ≥ generic" together require the additive interpretation. This was discovered by the T09 test and corrected before CP-R6-B.
- Test status: covered by T09 (16 passed); `r6_rescore_summary.csv` has 12 rows with all required columns.
- Notes: PBA exclusions (null-PBA archetypes) applied in `_compute_plausibility` consistent with `compute_validation_gates`. Thresholds unchanged. No core module touched.

#### T08 — Verify food-service band resolves 4 R5-FAIL cells — completed 2026-06-15
- Artifacts: per-cell `r6_gates_report.txt` outlier sections; `r6_rescore_summary.csv` plausibility columns.
- Deviations: none.
- Test status: covered by T09 `TestArchetypeAwarePctGeqGeneric` (all 12 cells archetype ≥ generic).
- Notes: all 4 FAIL cells (nyc_rural, austin_centre, austin_suburban, austin_rural) move from generic FAIL to archetype PASS. All outlier buildings are QuickServiceRestaurant EUIs in 1077–1137 kWh/m² range, inside PBA-15 band. Generic band figures reported unchanged alongside. austin_centre archetype=100.00% (generic=95.31%), nyc_rural archetype=100.00% (generic=98.30%), austin_suburban archetype=100.00% (generic=98.62%), austin_rural archetype=100.00% (generic=96.92%).

#### T09 — Test: re-scoring engine — completed 2026-06-15
- Artifacts: `tests/test_r6_rescore.py`
- Deviations: none.
- Test status: `pytest tests/test_r6_rescore.py -v` → **16 passed in 0.08s**. Full suite: **568 passed, 3 warnings** (existing deprecation warnings only).
- Notes: 16 tests covering region mapping, band derivation, generic-fallback for null-PBA/OpenUBEMUnknown/data-centre archetypes, archetype_pct≥generic_pct for all 12 cells, summary CSV shape, and no-import-mutation of openubem.results core. Synthetic fixtures only; no full CBECS download in CI.

#### T06/T08 CORRECTION — generic plausibility denominator fix — 2026-06-15
- Artifacts: `scripts/validation/r6_rescore_cells.py` (`_compute_plausibility`, `_outlier_detail` methods modified); `tests/test_r6_rescore.py` (1 test replaced, 1 added → 17 total); all 12 `r6_gates_report.txt` regenerated; `r6_rescore_summary.csv` regenerated.
- What changed: `_compute_plausibility` was applying the CBECS PBA exclusion (null-PBA archetypes — apartments, data centres) to the denominator of the generic plausibility % before computing it. The R5 F12 EUI-plausibility gate runs on ALL parsed (success) buildings with non-null EUI with NO archetype exclusion. The fix: `valid` is now `gdf[gdf["eui_kwh_m2"].notna()]` with no archetype filter; null-PBA archetypes fall back to the generic `[25,1000]` band (no archetype_bands entry) just as they did before, but now they ARE counted in the denominator. The same fix was applied to `_outlier_detail`. The archetype-aware plausibility uses the same corrected denominator (same valid set), so `archetype_pct >= generic_pct` is still guaranteed. The CBECS distribution gates (`compute_validation_gates`) are unchanged — their null-PBA exclusion is correct and intentional.
- Why the bug mattered most for la_urban: 446/618 success buildings are MidriseApartment (null-PBA). Excluding them from the denominator gave 98.73% (168/170 non-apartment buildings in generic band) instead of the correct 99.67% (612/614 all buildings in generic band).
- Test update: `test_apartments_excluded_from_plausibility` (encoded buggy behavior) replaced by `test_apartments_included_in_generic_denominator` (asserts gen_pct=100% for 3 apartment EUIs in [25,1000]) and `test_generic_pct_unaffected_by_archetype_exclusion` (key regression test: 4 apartments@500 + 1 QSR@1500 → generic_pct=80% not 0%).
- Deviations from original plan: none — the bug was in the prior executor's implementation, not in the spec. §4.4 states "report alongside" and the correction is consistent with the binding description of the R5 F12 gate.
- Test status: `pytest tests/test_r6_rescore.py -v` → **17 passed in 0.08s**. Full suite: **569 passed, 3 warnings** (same 3 pre-existing deprecation warnings).
- Verification: all 5 manager-specified targets match V13 Table C §4 to 2 dp:
  - la_urban: 99.67% ✓ (V13: 99.67, computed 612/614)
  - nyc_rural: 98.48% ✓ (V13: 98.48, computed 195/198)
  - austin_centre: 95.40% ✓ (V13: 95.40, computed 394/413)
  - la_centre: 99.12% ✓ (V13: 99.12, computed 224/226)
  - nyc_centre: 99.73% ✓ (V13: 99.73, unchanged)

#### T10 — Write V14_R6_batch1_region_corrections.md — completed 2026-06-15
- Artifacts: `docs/validations/overAll/V14_R6_batch1_region_corrections.md` (NEW)
- Deviations: none. All numbers pulled directly from `r6_rescore_summary.csv` and the 12 per-cell `r6_gates_report.txt` files; no recomputation. GWP direction confirmed NYC-rises (+54–69%) consistent with the §4.3 corrected finding (NYCW 0.402146 > NY 0.222872). V14 §5 explicitly states the manager's initial "NYC cleaner" assumption was corrected by the data.
- Test status: N/A (markdown); no code written.
- Notes: V14 sections: 1 Method/provenance (region references, eGRID factors, GWP recompute method, archetype-aware semantics); 2 CBECS gates Tables 1–4 + narrative (CV(RMSE) improved all 12 but none reach <30%; R² fragility in la_suburban/la_rural noted); 3 Plausibility Table 5 (generic reproduces V13 Table C exactly); 4 OQ-R5-11 resolution narrative; 5 GWP Table 6 + narrative (NYC headline finding); 6 Conclusions; 7 Artifacts.

#### T11 — Cross-reference pointers appended to V13 + REPORT_R5_final — completed 2026-06-15
- Artifacts: `docs/validations/overAll/V13_cross_case_synthesis.md` (1 line appended to §4); `docs/validations/overAll/results/REPORT_R5_final.md` (1 line appended to §6)
- Deviations: none. Append-only; no existing number, sentence, or table altered in either file.
- Test status: N/A (markdown); manager audits diff.
- Notes: V13 pointer appended immediately after the §4 CBECS narrative paragraph, before the `---` separator. REPORT_R5_final pointer appended after item 4 of §6, before `## 7`.

#### T12 — Progress-log entries appended — completed 2026-06-15
- Artifacts: `docs/validations/overAll/PLAN_overall-validation-R6-batch1.md` §8 (this entry)
- Deviations: none.
- Test status: N/A.
- Notes: CP-R6-C stop point reached. Awaiting manager close-out and memory update.

#### T07 — eGRID subregion factors: extract + build subregion factor file — completed 2026-06-15
- Artifacts: `scripts/build_egrid_json.py` (extended); `openubem/data/carbon/egrid_2022_subregions.json` (NEW, 27 subregions); `openubem/data/carbon/egrid_2022.json` (regenerated, NY/CA/TX subregion tags populated); `openubem/data/carbon/PROVENANCE.md` (updated with subregion source + B2 decision note)
- Deviations: none. Sheet `SRL22` confirmed present. Columns `SUBRGN` (idx 1) and `SRC2ERTA` (idx 24) confirmed at exact expected names. 3 required acronyms present: NYCW=0.402146, CAMX=0.226469, ERCT=0.351215 kg/kWh — all in (0.01, 1.2). State JSON re-validated: 51 entries, all state factors unchanged, NY/CA/TX `subregion` tags populated as NYCW/CAMX/ERCT respectively.
- Test status: covered by T07b (11 passed); pre-existing suite stayed green: `pytest tests/test_cbecs_region_extract.py tests/test_r6_rescore.py` → 38 passed.
- Notes: One critical data-truth finding — NYCW (0.402146) is GREATER than NY state (0.222872), ratio=1.806. Plan §4.3 narrative said "NYC grid is much cleaner than upstate New York" and T07b test said "GWP strictly DECREASES". The data shows the opposite for the total-output CO2e rate (SRC2ERTA): NYC subregion is DIRTIER than the state average, while upstate NY (NYUP=0.124914) is far cleaner. This is flagged at CP-R6-B2; manager must decide whether B2 should use a different eGRID metric or accept the factual correction. ERCT (0.351215) < TX (0.372828) as expected — Austin does decrease.

#### T07b — GWP recompute with subregion factors + test — completed 2026-06-15
- Artifacts: `scripts/validation/r6_rescore_cells.py` (extended with `_load_egrid_factors`, `compute_gwp_subregion`, `load_cell_df_full`, `_cell_city`; `rescore_cell` accepts optional `state_factors`/`subregion_factors`; per-cell report extended with GWP section; `main` loads factors and passes them); `docs/validations/overAll/results/cases/<cell>/r6_gates_report.txt` ×12 (regenerated with GWP section); `docs/validations/overAll/results/r6_rescore_summary.csv` (regenerated with `gwp_r5_state_kgco2e`, `gwp_r6_subregion_kgco2e`, `gwp_delta_pct` columns); `tests/test_r6_gwp_subregion.py` (NEW, 11 tests)
- Deviations:
  1. CRITICAL — NYC GWP direction opposite to plan assertion: plan T07b says "NYC cell total GWP strictly DECREASES because NYCW<NY". eGRID 2022 SRC2ERTA data: NYCW=0.402146 > NY=0.222872 (ratio=1.806). NYC GWP INCREASES by +54–69%. The test `TestNYCCellGWPDirection` asserts the factually correct direction and documents the deviation. Manager must decide: (a) accept the data-truth correction (the plan narrative was wrong about NYCW's relative cleanliness at the total-output rate), or (b) switch to a different eGRID metric (e.g. non-baseload rate `SRC2ERA` instead of total-output `SRC2ERTA`).
  2. MINOR — floor area uses `derive_num_floors` (fallback to `height_m/3.5` for NaN levels) instead of raw `levels`. Plan formula says `footprint_area_m2 * levels` but this would silently drop 602/738 nyc_centre buildings (NaN levels). Using `derive_num_floors` reproduces V13 Table B totals exactly for all 12 cells (confirmed pre-T07b). No spec conflict — the plan's formula note references §4.3 which says "floor_area_m2 = footprint_area_m2 * levels" without addressing NaN levels; `derive_num_floors` is the correct aggregator-consistent approach (confirmed by `05_neighbourhood_summary.json` matching V13 to the cent).
- Test status: `pytest tests/test_r6_gwp_subregion.py -v` → **11 passed in 0.11s**. Full suite: **580 passed, 3 warnings** (same 3 pre-existing deprecation warnings).
- Notes: V13 recompute verification passed for all 12 cells (0.0000% diff). NYC INCREASES, LA INCREASES modestly, Austin DECREASES. 05_results.csv files untouched (mtime test passed). R5 neighbourhood_summary.json GWP values verified intact.
