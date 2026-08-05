Note: these are **archived copies** of scripts used by the storey-matching arc, kept for the arc
record. They are not an import path — nothing under `openubem/` or the live `scripts/` tree imports
from here, and none of these copies should be executed from this location. The `.py` files under
`docs/` are an explicit user override of the normal "no `.py` under docs/" convention, for this
collection task only.

## Index

One row per collected script. "What it was for" and "which task/defect" are taken from the plan
doc's own progress-log entries (`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_implementation.md`,
§7 unless noted); nothing here is invented.

| file | original path | what it was for | which task/defect | lines | sha256 (first 12) |
|---|---|---|---|---|---|
| `a1_map_prototypes.py` | `scripts/analysis/a1_map_prototypes.py` | Maps the storey structure of all 25 baseline prototype IDFs — Z-clustering of FLOOR-surface elevations in world coordinates (0.2 m tolerance) to recover modelled storey count and per-storey plate area. Its method was later re-implemented in-memory inside `layout_assigner.compute_band_map()` (B01) so production never depends on this script's CSV output at runtime. | A1 | 201 | 1f20a4250fe3 |
| `a2_measure_multiplier.py` | `scripts/analysis/a2_measure_multiplier.py` | Harness for A2/A2-bis — builds and runs real EnergyPlus 23.1 MediumOffice models with/without a Zone Multiplier applied, to measure whether the multiplier mechanism actually reaches sizing/output. A2's first run was voided by CP-A audit (multiplier never took effect); A2-bis reused this harness with a verified applied multiplier and passed. | A2, A2-bis | 113 | 5221355a9f09 |
| `a4_bis_generate_layout_assign_viewer.py` | `scripts/analysis/a4_bis_generate_layout_assign_viewer.py` | Generates the `layout_assign`-mode 3D viewer export (side-by-side against real `auto` massing) for the CP-A "before" evidence panel — the honest before-code-change baseline that could only be produced while `layout_assigner.py` was still unmodified. Does not call the production pipeline directly. | A4-bis | 287 | c945ee129bab |
| `b00_coverage_census.py` | `scripts/analysis/b00_coverage_census.py` | Throwaway harness joining the phaseE fleet CSV against A1's prototype storey structure to classify every one of the 8,160 fleet buildings as taller/equal/shorter/no-baseline relative to its assigned prototype. Produced `b00_coverage_census.csv`, `..._registry_alt.csv`, `..._row_detail.csv`. Surfaced that `MidriseApartment` (the arc's motivating archetype) sits at only 7.16% taller fleet-wide and 0.00% under 500 m². | B00 | 204 | 164588619f51 |
| `b05e_measure_energy_delta.py` | `scripts/analysis/b05e_measure_energy_delta.py` | Throwaway harness building 10 real `nyc_suburban` buildings twice (pre-B05 monkeypatched replica vs real post-B05 function) through the production `BuildingIDF.build()` → real EnergyPlus path, to check whether the B05 Zone-Origin scaling bug/fix is visible in energy output. Result: no energy effect (deltas at floating-point noise level). | B05e | 242 | d035a049432b |
| `b05f_rebuild_layout_assign_viewers.py` | `scripts/analysis/b05f_rebuild_layout_assign_viewers.py` | Throwaway harness rebuilding both `layout_assign` viewer HTMLs from the real production Step-2/Step-3 pipeline (`t19_layout_assign_full_sweep.run_step2`/`run_step3_mode`), not from the void `fast_scale_idf_text()` generator. Also ran the pre-B05-pipeline overlap comparison later found void (monkeypatch never took effect on cluster workers) — superseded by E-LA-31 item 1's scratch-package method. | B05f | 175 | f76d54ad6cc4 |
| `b08a_placement_diagnosis.py` | `scripts/analysis/b08a_placement_diagnosis.py` | Throwaway, read-only measurement script for E-LA-31 item 2 — parses `predicted_offset` (local hull-centroid distance from the model's own origin, read from the saved post-B05 IDF) and `measured_offset` (world-frame hull centroid vs. `footprint_centroid_utm`, read from the rendered viewer scene) for all 2,630 real substituted buildings across both cells, to diagnose the residual cross-building placement/overlap defect. Fit: r = 0.99999999815, confirming a pure anchor-offset mechanism. | B08a (E-LA-31 item 2) | 247 | ce0b898c63df |
| `b08b_measure_energy_delta.py` | `scripts/analysis/b08b_measure_energy_delta.py` | Throwaway harness re-verifying the energy-null result after the B08b re-centring fix, on the same 10 `nyc_suburban` buildings B05e used. All 20 runs: 0 Severe, 0 Fatal, deltas at floating-point noise level — confirms translating a building in XY cannot change its energy under `layout_assign`. | B08b | 296 | 9c02df09ea02 |
| `b08b_rebuild_layout_assign_viewers.py` | `scripts/analysis/b08b_rebuild_layout_assign_viewers.py` | Rebuilds both `layout_assign` viewer HTMLs in place from real pipeline output after the B08b placement re-centring fix landed; adapted from `b05f_rebuild_layout_assign_viewers.py` minus its now-unneeded pre-B05 monkeypatch pass. Archives the pre-B08b copies to `figures/before_B08b/` before overwriting. | B08b | 104 | 8618c12c3294 |
| `c01_storey_matching_regression.py` | `scripts/analysis/c01_storey_matching_regression.py` | Local real-EnergyPlus regression harness — 7 real `BuildingIDF.build()` → EnergyPlus 23.1 runs (5 named storey cases + mandatory high-multiplier case D + a matched-plate S=1 control) exercising identity/taller/shorter/degenerate/fallback storey-matching paths. Its own energy-delta parsing (nominal-area EUI denominator) was later found by the manager's audit to understate a real double-counting defect — see E-LA-35. | C01 | 316 | 8ca58b1587a3 |
| `enrich_layout_assign_viewers.py` | `scripts/analysis/enrich_layout_assign_viewers.py` | 🔴 **FROZEN downstream artifact — do not run.** Post-processing-only script (no pipeline re-run) that edited the four target viewer HTMLs in place: joins basemap imagery from the `real_auto` donor scenes, adds `rendered_height_m` to the click-detail panel, switches default colour mode to archetype, and inserts a caption banner disclosing the substituted-massing/no-simulation-results caveats. This is the script that produced the four viewers the user has confirmed now render correctly and has explicitly frozen; it was **not executed** as part of this collection task, per the user's instruction. | E-LA-34 remediation | 249 | 07fb425bdec3 |
| `measure_layout_assign_overlap.py` | `scripts/analysis/measure_layout_assign_overlap.py` | Overlap-measurement script — given a viewer HTML scene, computes pairwise building-footprint overlap (pair count, buildings involved, % of buildings, hull-centroid-vs-`footprint_centroid_utm` offset). Run repeatedly across the arc: B05f (void pre/post-B05 comparison, later corrected by E-LA-31), E-LA-31 item 1 (genuine pre-B05 vs post-B05 vs real-auto control), and B08b (post-re-centring re-measurement, the binding ≤1 m gate). | B05f, E-LA-31 item 1, B08b | 200 | 1ca3d6518f68 |
| `measure_offset_by_archetype.py` | `scripts/analysis/measure_offset_by_archetype.py` | Per-archetype residual-offset measurement (hull-centroid vs `footprint_centroid_utm`), aggregated to archetype rather than per-building. Used in B08b to confirm every genuinely substituted archetype lands at sub-millimetre median/max offset after the re-centring fix, except the unmapped `Courthouse` fallback and one `PrimarySchool` outlier. | B08b | 99 | 8580069523cf |
| `t19_harvest_layout_assign.py` | `scripts/cluster/t19_harvest_layout_assign.py` | Pre-existing T19 fleet-sweep harvest module (not written for this arc). Reused directly — its `_parse_sql()` SQL-meter parser was imported (not reimplemented) by `b05e_measure_energy_delta.py` to parse EUI from `trim_outputs=True` runs, where `eplustbl.csv/.htm` do not exist. | Imported by B05e | 461 | b51194794cd1 |
| `t19_layout_assign_full_sweep.py` | `scripts/cluster/t19_layout_assign_full_sweep.py` | Pre-existing T19 fleet-sweep module (not written for this arc). Its `run_step2`/`run_step3_mode` functions — the actual production Step-2 enrichment / Step-3 IDF generation pipeline — were imported directly (not reimplemented) by `b05f_rebuild_layout_assign_viewers.py`, E-LA-31 item 1's scratch-package rebuild, and `b08b_rebuild_layout_assign_viewers.py`, so all three viewer rebuilds are provably built from the real pipeline rather than a standalone generator. | Imported by B05f, E-LA-31 item 1, B08b | 400 | 168206fc3f09 |
| `run_d_control.py` | `scratchpad/c01_work/run_d_control.py` | Throwaway script (explicitly "not under `docs/`" per the plan doc) that ran C01's 7th, manager-requested run — a matched-plate (350 m²) `S=1` identity control for the high-multiplier case D, needed to measure the transformer's energy effect without confounding by a different plate size. | C01 | 85 | 1a40062f6c66 |
| `diag_c01_floorarea.py` | `scratchpad/diag_c01_floorarea.py` | Throwaway, read-only diagnosis script for the E-LA-35 root-cause investigation — recomputed each C01 run's *true* EnergyPlus-simulated floor area from `eplusout.eio` Zone Information lines (multiplier-aware) against the harness's naive nominal denominator, to isolate how much of the D_HIGHMULT/D_control EUI-ratio mismatch was a harness artifact vs. real energy. | C01 EUI-mismatch diagnosis (E-LA-35) | 47 | 50c39846bb11 |
| `diag_c01_objects.py` | `scratchpad/diag_c01_objects.py` | Throwaway, read-only diagnosis script for the E-LA-35 root-cause investigation — compared individual IDF objects (`Lights`, `ElectricEquipment`, `WaterUse:Equipment`, `People`) between the D_HIGHMULT and D_control built IDFs by name, to isolate which absolute-load object classes are double-counted under `storeys_matched=True` (Cause B) versus which are correctly untouched. | C01 EUI-mismatch diagnosis (E-LA-35) | 56 | 59153fa553cb |

## Deliberately excluded

- **`/tmp/sweep_capacity.py`** (B01b's capacity-field sweep, grepping all 25 baselines for
  non-Zone-scoped literal-capacity fields) — still present on this machine at system `/tmp`, outside
  the git repository entirely. The plan doc itself labels it *"not checked in — throwaway"* (§7, B01b
  entry). Excluded as out-of-repo/ephemeral, not as "missed."
- **`step3_export_and_measure.py`** (E-LA-31 item 1's read-only viewer-export step, wrapping
  `openubem.viz.viewer_export.export_viewer` against the verified pre-B05 scratch-package IDF tree) —
  cited by name in the plan doc but no longer present anywhere in the repo. C01's own entry documents
  the arc's convention of deleting ephemeral harness scripts after their dispatch (referring to a
  different script, but the same convention applies here); this one could not be located to collect. **Missed, not "not used."**
- **`scripts/cluster/t17_harvest_layout_assign.py`, `t17_layout_assign_full_sweep.py`,
  `t18_harvest_layout_assign.py`, `t18_layout_assign_full_sweep.py`** — predecessor-arc fleet
  harvest/sweep scripts. The plan doc explicitly states *"`t17_`/`t18_`/`t19_` untouched"* when
  describing the planned (but withheld) C02 fleet run — t17/t18 belong to earlier arcs and are not
  part of storey-matching's own script set, unlike t19 which this arc's scripts import directly.
- **`scripts/cluster/t20_*`** — the plan doc names a fresh `t20_*` job/harvest set as C02's intended
  "What," but **C02's go was withheld** by the manager (E-LA-35 diagnosis pending); these scripts were
  never created. Nothing exists to collect.
- **`scripts/validation/v05b_fix_storeys.py`** — not mentioned anywhere in the storey-matching plan
  doc; belongs to a different arc.
- **`scripts/analysis/a2_parse_results.py`, `a3_enumerate_dangling_references.py`,
  `a3_measure_band_deletion.py`, `a3_update_summary.py`, `a4_generate_viewer_evidence.py`,
  `compare_layout_assign.py`, `plot_layout_assign_vs_modes.py`, `test_viewer_layout_assign.py`,
  `check_identical_shapes.py`, `diagnose_blank_viewer.py`, `headless_check_viewer.py`,
  `measure_raw_baseline_footprint.py`, `repro_legend_crash.mjs`, `test_idf_inspect.py`,
  `a1b_provenance.py`, `a1c_distribution.py`** — filenames overlap this arc's `a1`/`a2`/`a3`/`a4`/`b0`
  task-ID naming convention (or sit alongside it in `scripts/analysis/`) but are **not cited anywhere**
  in the storey-matching plan doc's text or progress log. These belong to earlier phases of the
  broader LayoutAssigner arc (E-LA-20 fix arc and prior debug rounds) that reused the same lettered
  task-ID convention before this arc existed. Excluded as out-of-scope, not missed.
- **Everything else under `scratchpad/`** not explicitly named above — per the task instructions,
  ignored as one-off scratch work not cited by the plan doc as a deliverable.
