# PLAN — V19 Phase-C Re-score vs V17 Measured Anchors

- **Slug:** `v19-phasec-rescore`
- **Date:** 2026-06-20
- **Author:** Manager (Opus session)
- **Binding contract:** the V17 document `docs/docs_VALIDATION/overAll/V17_external_measured_validation.md`
  defines the comparison basis (metric, statistic, anchors). This plan re-runs that exact comparison
  against the **fresh Phase-C results** (multi-floor zoning + DOE schedules + core/perimeter geometry fix).
- **Why this exists:** V17 found LA running **+39.6 % hot city-wide / +72 % on office**, but V18 showed that
  finding was *confounded* by the 1-floor-internal-loads ÷ n_floors zoning defect. Phase C re-simulated all
  12 cells with that defect fixed (12/12 clean, zero exclusions). V19 answers: **does the fix move the
  numbers, and is LA still hot?**
- **Division of labour:** **Sonnet executes Phase 1 (T01–T06)** — the mechanical data extraction,
  reconstruction, and comparison-table generation. **Manager (Opus) writes Phase 2** — the verdict doc
  `V19_phaseC_rescore.md` — from Sonnet's numbers. Sonnet does NOT write the verdict.

---

## 1. Hard rules for the executor

- **Stay in cwd** `C:\Users\o_iseri\Desktop\OpenUBEM`. No path escapes.
- **No plan-writing.** Execute T01–T06 in order; do not propose alternatives. If a fact below is wrong or
  the source data contradicts it, **STOP and quote the conflict** — do not invent a workaround.
- **No scope creep.** You produce *numbers and tables only*. You do NOT write `V19_phaseC_rescore.md`
  (that is the manager's Phase 2). You do NOT re-simulate anything. You do NOT touch the R5 baseline
  (`runtime/ubem_validation/cases/`) or any IDF.
- **Reuse, do not reinvent.** The reconstruction math is already written and tested in
  `openubem/results/service_loads.py::reconstruct_frame`. Call it. Do NOT re-implement Table-4 splits.
- **Report-only.** This is diagnostic. Never tune anything to make a delta look better.
- **Default to no comments.** One short line max where the WHY is non-obvious.
- **No git.** The user's external tool commits.
- **Figures (if any) → `openubem/outputs/`** only. Never bury plots under `docs/.../figures/`.

---

## 2. File layout to create

```
scripts/
└── v19_rescore.py                 ← NEW: loader + reconstruction + comparison-table emitter (the only code)

docs/validations/overAll/results/
├── v19_phaseC_reconstructed.csv   ← NEW: all 12 cells, per-building, with reconstruction columns
└── v19_comparison_tables.md       ← NEW: the city + archetype comparison tables (manager's Phase-2 input)
└── v19_comparison.csv             ← NEW: same numbers, machine-readable

tests/
└── test_v19_rescore.py            ← NEW: asserts loader finds all 12 cells + reconstruction columns present
```

No other files. **No `.py` under `docs/`. No edits to `service_loads.py`** (reuse it as an import).

---

## 3. Dependency decisions (pre-decided — do not re-debate)

- Reconstruction core = `from openubem.results.service_loads import reconstruct_frame, load_coefficients`.
- Input per cell = the cell's **`05_results.gpkg`** (same artifact `reconstruct_cell` uses), read with
  geopandas, geometry dropped. Use `.gpkg` (carries `simulation_status`), NOT the `.csv`.
- pandas / geopandas only — both already in the env (used by `service_loads.py`).
- Output CSVs → `docs/validations/overAll/results/`. Verdict doc (manager) → `docs/docs_VALIDATION/overAll/`.

---

## 4. Source-of-truth verified facts (manager already grepped these)

**4.1 The 12 Phase-C cells live in TWO folders** (re-run cells landed in a different tree):
- 9 cells in `docs/docs_VALIDATION/overAll/results/phaseC/<cell>/05_results.gpkg`:
  `austin_centre, austin_rural, austin_suburban, la_rural, la_suburban, la_urban, nyc_rural, nyc_suburban, nyc_urban`
- 3 cells in `docs/validations/overAll/results/phaseC/<cell>/05_results.gpkg`:
  `austin_urban, la_centre, nyc_centre`
- **All 12 must be loaded.** Hardcode the two base dirs + the cell→folder mapping; assert exactly 12 gpkgs
  found before proceeding. If any is missing, STOP and report which.

**4.2 V17 comparison basis** (`V17_external_measured_validation.md` §1):
- Metric = annual **site** EUI, kWh/m²·yr. Statistic = **median** (+ p25/p75).
- Model number = **`total_eui_reconstructed_kwh_m2`** median (all 9 end-uses) — NOT the 4-end-use total.
  Also carry the 4-end-use `total_eui_kwh_m2` median as the structural lower bound (shown alongside).
- Reconstruction is a post-hoc multiplier off the 4-end-use base ⇒ both numbers move with the zoning fix.

**4.3 V17 measured anchors to compare against** (V17 §3 city, §4 archetype; kWh/m²·yr):

City scorecard — measured median | V17 *old-model* median (for movement Δ):
| City | Segment | Measured | V17 old model |
|---|---|---:|---:|
| NYC | Office | 183.9 | 183.3 |
| NYC | Multifamily | 226.2 | 302.0 |
| NYC | Overall | 219.2 | 246.9 |
| LA | Office | 121.5 | 208.9 |
| LA | Multifamily | 115.8 | 153.3 |
| LA | Warehouse | 33.9 | 64.1 |
| LA | Overall | 113.6 | 158.6 |
| Austin\* | Office | 162.3 | 187.6 |
| Austin\* | Overall | ~162 | 199.8 |

\* Austin = CBECS proxy, ESTIMATED — indicative only.

Per-archetype national (ESPM median | V17 old model):
| Archetype | ESPM | V17 old model |
|---|---:|---:|
| MediumOffice | 166.9 | 160.3 |
| SmallOffice | 166.9 | 190.3 |
| LargeOffice | 166.9 | 229.8 |
| MidriseApartment | 187.9 | 228.8 |
| RetailStandalone | 162.1 | 286.7 |
| Warehouse | 71.6 | 64.1 |
| SuperMarket | 618.3 | 631.5 |
| FullServiceRestaurant | 1027.2 | 2158.5 |
| QuickServiceRestaurant | 1270.3 | 3307.9 |
| PrimarySchool | 153.0 | 289.4 |

**4.4 Segment → archetype_id mapping** (archetype_ids verified present in results):
- **Office** = {`SmallOffice`, `MediumOffice`, `LargeOffice`}
- **Multifamily** = {`MidriseApartment`, `HighriseApartment`}
- **Warehouse** = {`Warehouse`}
- **Overall** = all rows in the city (exclude `OpenUBEMUnknown` from the Overall median — it is a
  classification gap, not a building type; report its count separately).
- City label = prefix of cell name (`nyc` / `la` / `austin`); density = suffix (`centre/urban/suburban/rural`).

**4.5 Field-norm yardstick** (V17 §2): aggregate city median within **±10–15 %** of measured = a *pass*.
LA was the only ❌ in V17. NYC office (−0.3 %) is the credibility anchor.

**4.6 Reconstruction passthrough rule** (already in `reconstruct_building`): non-success status or unmapped
archetype ⇒ reconstructed = sim total (no uplift). Expect `OpenUBEMUnknown`, `TallBuilding`,
`SuperTallBuilding`, `Courthouse`, etc. to passthrough. That is correct, not a bug.

---

## 5. Task list

### T01 — V19 loader: read all 12 Phase-C cells
- **What:** In `scripts/v19_rescore.py`, write a loader that reads the 12 `05_results.gpkg` from the two
  base dirs (§4.1), drops geometry, tags each row with `cell`, `city`, `density`, concatenates to one
  DataFrame. Assert exactly 12 cells loaded; if not, raise with the missing cell list.
- **Why:** §4.1 — the cells are split across two trees; V19 needs all 12 together.
- **How:** Hardcode `CELL_TO_BASE = {...}` (9 → docs_VALIDATION tree, 3 → validations tree). Use
  `geopandas.read_file`. Derive `city`/`density` from `cell.split("_")`. Keep success + non-success rows
  (reconstruction handles passthrough).
- **How to test:** `test_v19_rescore.py::test_loader_finds_all_12` — len of distinct `cell` == 12 and total
  rows > 8000 (V17 had 8,148 success; total incl. non-success is ≥ that).

### T02 — Apply service-load reconstruction
- **What:** Run `reconstruct_frame(combined, load_coefficients())`; write the full per-building result to
  `docs/validations/overAll/results/v19_phaseC_reconstructed.csv`.
- **Why:** §4.2 — V17 compares the reconstructed (9-end-use) total; the new sim base must be reconstructed
  the same way for apples-to-apples.
- **How:** Import from `openubem.results.service_loads`. Do NOT modify that module. After running, log:
  count `reconstruction_applied==True`, count passthrough among success rows, and the distinct unmapped
  archetype_ids (sanity — should match §4.6 expectations).
- **How to test:** reconstruction columns present in output (`total_eui_reconstructed_kwh_m2` etc.);
  covered by existing `tests/test_service_loads.py` for the math itself.

### T03 — City-level comparison table
- **What:** For each city (nyc/la/austin) and each segment (Office, Multifamily, Warehouse, Overall),
  compute the **median** of `total_eui_reconstructed_kwh_m2` (and the 4-end-use `total_eui_kwh_m2`),
  plus p25/p75, over **success rows**. Exclude `OpenUBEMUnknown` from Overall (report its n separately).
- **Why:** §4.3 / §4.4 — mirror V17 §3 exactly so deltas are comparable.
- **How:** Use the §4.4 mapping. Build a table with columns:
  `city, segment, n, model_recon_median, model_4eu_median, measured (§4.3), Δ_vs_measured_%,
  v17_old_model (§4.3), Δ_vs_v17old_%`. Δ_vs_measured = (model_recon − measured)/measured·100.
  Δ_vs_v17old = (model_recon − v17_old)/v17_old·100 (the "did the fix move it" signal).
- **How to test:** covered by T06 sanity checkpoint (manager reads the table).

### T04 — Per-archetype national comparison table
- **What:** Across all 12 cells (national pool, success rows), compute reconstructed-total median per
  archetype for the 10 archetypes in §4.3, with n. Build the same Δ_vs_ESPM_% and Δ_vs_v17old_% columns.
- **Why:** §4.3 archetype table — mirror V17 §4.
- **How:** Group by `archetype_id`. Flag archetypes with n < 12 (low-confidence, per V17 §6 provenance).

### T05 — Emit comparison artifacts
- **What:** Write `v19_comparison_tables.md` (human-readable: the two tables from T03/T04 as markdown,
  with a one-line note on which cells used the geometry fallback if that info is available, else omit) and
  `v19_comparison.csv` (machine-readable union of both tables). Both in
  `docs/validations/overAll/results/`.
- **Why:** these are the manager's Phase-2 input; the manager writes the verdict from them.
- **How:** No interpretation/verdict text — numbers + table only. The manager adds the analysis.
- **How to test:** files exist, non-empty, both tables present.

### T06 — Self-check + report
- **What:** Print to stdout: (a) the 12 cells loaded with row counts, (b) the LA Office and LA Overall
  reconstructed medians + their Δ_vs_measured and Δ_vs_v17old (the headline question), (c) NYC Office Δ
  (the anchor — should stay near 0 if nothing broke), (d) total passthrough count.
- **Why:** lets the manager audit the headline in one glance before writing Phase 2.
- **How:** plain prints; also append the §8 progress-log entries.
- **How to test:** the run completes rc=0 and `pytest tests/test_v19_rescore.py` passes.

---

## 6. Stop-and-report points

- **CP-1 (after T02):** loader finds all 12 cells AND reconstruction applied. Report the reconstruction-
  applied / passthrough counts and the distinct unmapped archetypes. STOP, report, wait for greenlight
  before computing comparisons. *(This is where a silent path/column bug would compound.)*
- **CP-2 (after T06):** all artifacts written, tests green. Report the headline numbers (LA Office, LA
  Overall, NYC Office Δ) and STOP. Manager writes Phase 2 from here.

---

## 7. Phase 2 — Manager (Opus) writes the verdict (NOT Sonnet)

After CP-2, the manager writes `docs/docs_VALIDATION/overAll/V19_phaseC_rescore.md`:
- Re-score city + archetype tables (from T05), V17-style.
- **The LA verdict** — is LA still hot? How much did the zoning fix move it? Tie back to V18 (was the V17
  +40 % an artifact?).
- NYC anchor sanity (did the fix preserve the −0.3 % office match?).
- Footnote the geometry-fallback cells using the RESULT_3 defensibility verdict (<0.1 % city impact).
- Updated calibration-target priority list (supersedes V17 §6 where the fix changed the picture).

---

## 8. Progress log

<!-- Sonnet appends one entry per completed task here. Format:
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + V17/DESIGN cite>
- Test status: <pytest summary>
- Notes: <auditor-relevant>
-->

#### T01 — V19 loader: read all 12 Phase-C cells — completed 2026-06-20
- Artifacts: `scripts/v19_rescore.py` (load_all_cells function), `tests/test_v19_rescore.py`
- Deviations: none
- Test status: `pytest tests/test_v19_rescore.py` — 1 passed in 0.21s
- Notes: All 12 gpkg files confirmed present before writing code. Cell row counts: austin_centre=413, austin_rural=245, austin_suburban=437, austin_urban=425, la_centre=226, la_rural=149, la_suburban=1343, la_urban=618, nyc_centre=738, nyc_rural=198, nyc_suburban=1589, nyc_urban=1779. Total=8160 rows.

#### T02 — Apply service-load reconstruction — completed 2026-06-20
- Artifacts: `docs/validations/overAll/results/v19_phaseC_reconstructed.csv` (8160 rows, 32 columns)
- Deviations: none; reconstruct_frame imported from openubem.results.service_loads, not modified
- Test status: reconstruction columns verified present (`total_eui_reconstructed_kwh_m2` etc.); math covered by existing `tests/test_service_loads.py`
- Notes: reconstruction_applied==True: 8156; passthrough among success rows: 0; distinct unmapped archetype_ids (success rows): none. The 4 passthrough rows are `not_simulated` buildings (2× LargeOffice, 2× MediumOffice) — correctly passthrough per §4.6 non-success rule. The `reconstruct_frame` module warning citing LargeOffice/MediumOffice fires because it does not filter by status before logging; the archetypes ARE mapped and reconstruct correctly when status=success.

#### T03 — City-level comparison table — completed 2026-06-20
- Artifacts: `scripts/v19_rescore.py` (build_city_table function); table printed to stdout
- Deviations: none; §4.3 measured and v17_old anchors transcribed verbatim; Austin Overall measured set to 162.0 (plan lists "~162")
- Test status: covered by T06 self-check and test_city_table_has_required_columns, test_city_table_has_la_office_and_overall
- Notes: 9 rows produced (nyc×3, la×4, austin×2); OpenUBEMUnknown excluded from Overall with n reported in segment label (nyc=558, la=19, austin=73); NYC Multifamily and Warehouse absent from CITY_ANCHORS (no measured anchor in §4.3) so correctly omitted per plan

#### T04 — Per-archetype national comparison table — completed 2026-06-20
- Artifacts: `scripts/v19_rescore.py` (build_archetype_table function); table printed to stdout
- Deviations: none; all 10 archetypes from §4.3 included; low_confidence flagged where n<12 (SuperMarket n=5, PrimarySchool n=11)
- Test status: test_archetype_table_has_all_10 passed
- Notes: FullServiceRestaurant and QuickServiceRestaurant show large negative delta_vs_v17old (~-53%, -57%) reflecting the restaurant service-load reconstruction correction from R6-batch1

#### T05 — Emit comparison artifacts — completed 2026-06-20
- Artifacts: `docs/validations/overAll/results/v19_comparison_tables.md`, `docs/validations/overAll/results/v19_comparison.csv`
- Deviations: none; numbers only, no verdict text; geometry-fallback cell info not available in results data so omitted per plan (§5 "if that info is available, else omit")
- Test status: test_artifacts_exist passed; both files non-empty
- Notes: CSV union tagged with "table" column (city_segment / archetype_national)

#### T06 — Self-check + report — completed 2026-06-20
- Artifacts: stdout printed; `tests/test_v19_rescore.py` extended to 5 tests
- Deviations: Δ symbol replaced with ASCII "delta" in print statements due to Windows cp1252 console encoding
- Test status: pytest tests/test_v19_rescore.py — 5 passed in 3.14s
- Notes: Total passthrough=4 (non-success rows); LA Office recon_median=216.73 delta_vs_measured=+78.4% delta_vs_v17old=+3.7%; LA Overall recon_median=157.65 delta_vs_measured=+38.8% delta_vs_v17old=-0.6%; NYC Office recon_median=251.37 delta_vs_measured=+36.7%

#### Phase 2 (manager) — V19 verdict written — completed 2026-06-20
- Artifacts: `docs/docs_VALIDATION/overAll/V19_phaseC_rescore.md`
- Deviations: none; verdict written from T03–T05 numbers, V17-style sections.
- Test status: n/a (analysis doc).
- Notes: Headline — fixes resolved V17's over-predictions (NYC MF +33.5→+0.7%, food-service +110/160→−1.6/+12%, NYC city +10.0% pass). V17 NYC-office anchor was a V18 artifact: office now +37% (NEW P1 systematic bias, all cities +30–52% vs ESPM). LA still hot +38.8% (unmoved −0.6%) → confirmed climate/HVAC problem, not zoning. Coherent mechanism: zoning fix pushes office loads UP, DOE schedules push dwelling/kitchen loads DOWN. Revised calibration priority supersedes V17 §6. STATUS hub + checklist + memory updated.
