# R5 COMPLETE ✅ — and fresh handoff for R6

**Closed 2026-06-15 by the Phase-C manager session.** All 12 cells of the R5 validation
matrix are closed at zero-fail / zero-skip. This file is now a close-out note + the
next manager's starting point.

---

## R5 final result

**12 / 12 cells closed · 8 152 buildings · 100% EnergyPlus 23.1.0 success.**

| Cell | n/n | total EUI (kWh/m²/yr) | GWP (kgCO₂e) | F12 | Sim host |
|---|---|--:|--:|---|---|
| nyc_centre | 738/738 | 154.84 | 332,809,487 | parse 100 / plaus 99.73 / zone 0 — **PASS** | cluster |
| nyc_urban | 1779/1779 | 168.59 | 40,317,055 | parse 100 / plaus 100 / zone 0 — **PASS** | cluster |
| nyc_suburban | 1589/1589 | 220.70 | 8,464,410 | parse 100 / plaus 99.94 / zone 0 — **PASS** | cluster |
| nyc_rural | 198/198 | 249.69 | 2,567,219 | parse 100 / plaus 98.48 / zone 0 — FAIL (QSR band) | cluster |
| la_centre | 226/226 | 179.40 | 119,015,264 | parse 100 / plaus 99.12 / zone 0 — **PASS** | cluster |
| la_urban | 618/618 | 175.49 | 101,280,696 | parse 100 / plaus 99.67 / zone 0 — **PASS** | cluster |
| la_suburban | 1343/1343 | 116.86 | 14,052,830 | parse 100 / plaus 99.93 / zone 0 — **PASS** | cluster |
| la_rural | 149/149 | 116.21 | 4,488,260 | parse 100 / plaus 100 / zone 0 — **PASS** | cluster |
| austin_centre | 413/413 | 175.16 | 242,610,785 | parse 100 / plaus 95.40 / zone 0 — FAIL (QSR band) | **LOCAL** |
| austin_urban | 417/417 | 197.46 | 64,368,469 | parse 100 / plaus 99.76 / zone 0 — **PASS** | **LOCAL** |
| austin_suburban | 437/437 | 185.07 | 17,946,122 | parse 100 / plaus 98.63 / zone 0 — FAIL (QSR band) | **LOCAL** |
| austin_rural | 245/245 | 197.08 | 10,891,760 | parse 100 / plaus 97.14 / zone 0 — FAIL (QSR band) | **LOCAL** |

- **F12 binding gates:** parse_success 100% and zone_count_integrity 0 in **all 12**.
  EUI-plausibility PASS in 8; FAIL in 4 — all the QSR/FSR food-service band artifact
  (OQ-R5-11). Generic [25,1000] band **HELD** per V-R5-8, never widened.
- **CBECS gates report-only (V-R5-5):** R² high (0.69–0.996); CV(RMSE)/KS_D fail from a
  regional + composition reference mismatch — not model defects (V13 §6.2).
- **Climate signal correct:** heating NYC(4A) ≫ Austin(2A) ≈ LA(3B); cooling
  Austin(2A) ≥ LA(3B) ≥ NYC(4A).

### Approved deviation
The **four Austin cells ran on LOCAL Windows EnergyPlus 23.1.0** (`n_jobs=10`, hard cap —
never 20 cores) instead of the Speed cluster, because the cluster queue was saturated by
the user's own research jobs (2026-06-15). Same engine/version; documented in each Austin
gates report, §8 entry, and V13 §6.3. NYC + LA ran on the cluster.

### Deliverables
- **Close-out report (CP-V3):** `docs/validations/overAll/results/REPORT_R5_final.md`
- **Cross-case synthesis (V13):** `docs/validations/overAll/V13_cross_case_synthesis.md`
  (EUI L1/L2 basis-corrected, GWP, gates, fleet, climate; OQ-R5-8 + OQ-R5-11 notes)
- **Level-2 round-trip:** `docs/validations/overAll/results/roundtrip_report.{md,csv}`
- **Per-cell (×12):** `docs/validations/overAll/results/cases/<cell>/` (10 files each)
- **Binding §8 log:** `docs/validations/overAll/PLAN_overall-validation-R5.md`
- **Raw intermediates:** `runtime/ubem_validation/cases/<cell>/` (gitignored; sole copy)
- Glue scripts: `scripts/validation/v12_austin_{centre,urban,suburban,rural}_local.py`

---

## Carry-over lessons (local-run specifics, for whoever runs more cells locally)

1. **`move_to_runtime` throws WinError 32** after python exits (a worker's `eplusout.sql`
   stays locked → `rmtree` of the temp source fails). The copy to `runtime/` has already
   completed — verify by counting `eplusout.end` in `runtime/.../sim_out`, then delete the
   leftover `%TEMP%/ubem_validation/cases/<cell>` dir with PowerShell
   `Remove-Item -LiteralPath ... -Recurse -Force`.
2. **Gates-report funnel line "single_zone repairs: 0" cosmetically undercounts.** The true
   repair count is in the IDF manifest (`zoning_strategy=single_zone` post-repair) and the
   run log "Repairing"/"Repair round" lines. austin_urban and austin_suburban each had 1
   real repair the funnel reported as 0.
3. **Single-row climate-zone re-derivation crashes** (`assign_climate_zones` zero-Tier1
   "wrong continent" guard fires on a 1-row subset). The Austin glue scripts reuse the
   cached `02a_climate_epw.parquet` zone for the building being repaired instead — keep
   that pattern if reusing the repair function.
4. **Hard local cap `n_jobs=10`** — never all 20 logical cores (PC-freeze risk). Detached
   launch: `nohup ./.venv/Scripts/python.exe -u <script> > <log> 2>&1 &`.

---

# Fresh handoff — R6 (deep calibration + reporting-layer corrections)

You are a MANAGER session for OpenUBEM (read `CLAUDE.md` first). You write kickoff prompts
and audit; fresh Sonnet executors write all code and run all pipelines. You never write
feature code. **R5 is closed — do not re-run it.** R6 has not been scoped or approved by the
user; confirm the user wants it before launching executors.

### R6 backlog surfaced by R5 (all in `OPEN_QUESTIONS_R5.md`; none blocked R5)

1. **Region-correct CBECS references** *(cheapest, highest-value)* — LA cells were scored
   against CBECS *Northeast*; they should be CBECS *West*, and Austin against CBECS *South*.
   Pure reporting-layer re-run of `compute_validation_gates` from the shipped
   `results/cases/<cell>/05_results.csv` — no resimulation, no `openubem/` code change. Do
   this first; it may substantially change the report-only CBECS verdicts for 8 cells.
2. **Populate `egrid_subregion` metadata** — empty in all 12 `05_neighbourhood_summary.json`.
   GWP math is valid; only the provenance label is unpersisted. Small Step-5 metadata fix.
3. **Archetype-aware plausibility band** — a higher EUI cap for food-service archetypes
   (QSR/FSR legitimately exceed 1000 kWh/m²/yr). This is the only thing making 4 cells FAIL
   F12. A gate-spec proposal (DQ-1 neighbour) — needs user sign-off before changing any gate.
4. **HVAC / zoning fidelity (DQ-1 deep calibration)** — the dominant Level-2 round-trip error
   is structural: single-zone IdealAir box vs multi-floor DOE prototype (basis correction
   makes it *worse*, 1/20 → 0/20). Largest scope; proper HVAC parameterization + multi-zone
   geometry. Reuse `reference_eui.parquet`, corrected `ref_inventory.csv`, val2d fleet as-is.

### Hard constraints (unchanged from R5)
- ALL cluster EnergyPlus via sbatch on speed.encs.concordia.ca; login node SUBMIT-ONLY
  (never run compute over ssh). **Local E+ is an approved fallback when the cluster queue is
  saturated** (hard cap `n_jobs=10`). ONE sbatch array in queue at a time across all sessions.
- Never git commit/add — user's external tool auto-commits. Never offer to.
- Gates report-only; never tune a threshold to pass (V-R5-5). A new archetype-aware band is a
  spec change requiring user approval, not a tuning move.
- No `.py` under `docs/`. Final tables/plots/reports → `docs/validations/overAll/results/`.
- Never edit OVERVIEW/DESIGN docs, root `main.py`, or `tests/fixtures/labelled_archetypes_50.csv`.
- E+ 23.1 local: `C:\EnergyPlusV23-1-0`.
