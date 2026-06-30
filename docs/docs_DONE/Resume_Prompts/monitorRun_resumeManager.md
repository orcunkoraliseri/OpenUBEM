# LA BATCH COMPLETE — V12 LA cells closed (R5 overall validation)

**Closed 2026-06-12.** All four Los Angeles cells of the V12 case-study matrix are
finished to the zero-fail / zero-skip standard (n/n generation = simulation = Step-5
parse; all binding F12 gates PASS). This manager scope is DONE — nothing here is in
flight. The Phase-C manager (`docs\pahseC_resumeManager.md`) may now start Austin.

## Final per-cell numbers

| Cell | n/n | total_eui (kWh/m²/yr) | GWP (kgCO₂e) | F12 (parse / EUI-plaus / zone-int) | cluster jobs |
|---|---|---|---|---|---|
| la_centre   | 226/226   | 179.40 | 119,015,264 | 100% / 99.12% / 0 — PASS | 964556 + 964792 + 964804 |
| la_urban    | 614/614   | 175.49 | 101,280,696 | 100% / 99.67% / 0 — PASS | 964805 + 965457 |
| la_suburban | 1343/1343 | 116.86 | 14,052,830  | 100% / 99.93% / 0 — PASS | 965462 + 967407 + 967450 |
| la_rural    | 149/149   | 116.21 | 4,488,260   | 100% / 100% / 0 — PASS    | 967463 + 967614 |

(NYC batch — nyc_centre 738, nyc_urban 1779, nyc_suburban 1589, nyc_rural 198 — was
already closed before this batch. Together NYC+LA = 8 of the 12 V12 cells; Austin's 4
remain for the Phase-C manager.)

## Where everything lives

- **Source of truth:** `docs\validations\overAll\PLAN_overall-validation-R5.md` §8 —
  entries `V12.la_centre`, `V12.la_urban`, `V12.la_suburban`, `V12.la_rural` (full
  Artifacts / Deviations / Test-status / Notes per cell).
- **Deliverables (10 files/cell):** `docs\validations\overAll\results\cases\<cell>\`
  (04_simulation_manifest.parquet, 05_neighbourhood_summary.json, 05_results.{csv,
  geojson,gpkg,schema.json}, v12_<cell>_gates_report.txt, figures/).
- **Raw (gitignored, SOLE copy):** `runtime\ubem_validation\cases\<cell>\`
  (01_buildings.gpkg, 02a_climate_epw.parquet, step3\idfs + 03_idf_manifest.parquet,
  sim_out\ n×{sql,err,end}).
- **Reusable scripts:** `scripts\validation\v12_cell_pipeline.py` (Steps 1–3 → ship →
  array → poll → fetch → Step 5) and the per-cell repair glue under
  `scripts\validation\`.

## Notes for the Phase-C manager (carry-overs)

- **ONE cluster array at a time, globally** (across both manager sessions) still holds —
  cluster queue is currently EMPTY. Verify `squeue -u o_iseri` empty before submitting.
- CBECS 2018 NE gates are REPORT-ONLY (V-R5-5) and FAIL in every cell (residential-heavy
  fleets vs commercial CBECS strata); they do not block. F12 gates are the binding ones.
- **Hard-won executor lessons** (bake into every kickoff): demand fully-synchronous
  foreground execution (never "monitor later" — that killed ~6 executors); launch the
  driver exactly once (a double-launch spawned two duplicate la_suburban arrays);
  single_zone is the proven fix for perimeter_core geometry fails (vertex mismatch /
  non-planar / degenerate), repaired into the denominator (never dropped); verify every
  fetched SQL with `PRAGMA integrity_check` + Zones>0 (a truncated tar shipped 12 corrupt
  SQLs in la_suburban); fleet.lst = underscore stems, Unix LF via write_bytes, upload via
  `scp` (tcsh login silently drops `cat >` stdin pipes); E+ only via sbatch, login node
  SUBMIT-ONLY.
