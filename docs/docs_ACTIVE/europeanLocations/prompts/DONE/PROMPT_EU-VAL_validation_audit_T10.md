# `EU-15`/`EU-16` — Executor prompt: independent validation audit (T10)

- **Arc**: European locations × Step 8. **Plan**: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- **Order**: **after T09's harvest.** Dispatch to a session that did **not** execute T01–T09 — the audit is
  worthless if the author checks their own work.
- **Executor**: fresh Sonnet session. **Paste everything below the rule.**
- **Date of prompt**: 2026-08-30. **Revised 2026-08-31.** **Authorisation**: read-and-measure only — this
  task fixes nothing. It carries **no** Speed authorisation: `D-EU-42` covers the T09 re-run wave only.

---

## Task (paste from here)

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu15-eu16-zoning-context-2026-08-30.md`,
`docs/docs_ACTIVE/europeanLocations/rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` and
`docs/docs_ACTIVE/europeanLocations/rules/RULES_context_geometry_simulation_2026-08-30.md`.
Execute **T10 only** and write
`docs/docs_ACTIVE/europeanLocations/validation/VALIDATION_EU-15_EU-16_zoning_context_2026-08-30.md`.

You are working in `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`** — never bare
`python`. Git is handled externally: **never commit, never stage**.

### Hard rules

1. 🔴 **Re-measure everything from the artefacts on disk. Never re-read a results table and never quote a
   number written by the executor you are auditing.** A criterion you cannot measure is reported
   **NOT SCOREABLE** — never PASS.
2. **This task fixes nothing.** If you find a defect, record it with a `file:line` and stop there. Do not
   repair, do not refactor, do not re-run a pipeline stage to "confirm".
3. **Create exactly one file** — the validation document named above. Nothing else.
4. No Speed, no `sbatch`, no login-node command. Local measurement only.
5. Do not edit root `main.py`, any OVERVIEW/DESIGN doc, the frozen `previous/` documents, or MVP Table 9.7
   (status cells only, and not from this task).

### The six measurements

- **(a) Ruled coverage.** Recount `scheme` across the side-cars in
  `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_*_data/layouts/` and report coverage **per district**
  against the **≥ 95 %** bar (`D-EU-39` §1). A fleet average is not an answer. Report the residual by
  `fallback_reason`, and confirm **0** side-cars carry `equal_strip_multi_angle_sweep` as an emitted success.
- **(b) The carved core.** `has_unconditioned_core` per district; dwellings + circulation = observed plate to
  **0.00 %**; `conditioned_floor_area_m2 < gross_footprint_area_m2` on exactly the buildings that carry a core;
  the core zone carries **no** `ZoneHVAC:IdealLoadsAirSystem`.
- **(c) Context and adiabatic.** Grep the emitted IDFs under `openubem/outputs/eu_evidence/EU-11/*/idfs/` for
  `Shading:` and `Adiabatic` and report the counts per district — the "before" is **0 of 2,516** for both.
  🔴 **Grep case-insensitively (`grep -i`)** — object names are written uppercase on disk
  (`SHADING:SITE:DETAILED`), and a case-sensitive grep silently returns zero. Verify on a sample that no
  context building was emitted as a `Zone`. Report the adiabatic coverage against the census expectation
  (Madrid 99.1 / Lyon 97.0 / London 92.8 / Bologna 88.5 %) — T08 measured 89.4 / 86.5 / 70.7 / 80.7 %, all
  below it; say whether that shortfall is explained anywhere on disk, and score it **NOT SCOREABLE** if not.
- **(d) The acceptance buildings.** The eight buildings of `EXAMPLE_dwelling_layout_validation_2026-08-28.md`
  §6, all five criteria each, including that **`relation/3730743` is refused**.
- **(e) Side-car ↔ IDF agreement.** On a **fresh** sample (not the executor's sample), every side-car's
  zone-name set equals its IDF's zone set — `D-EU-35`, the pop-up and the simulation must describe the same
  geometry.
- **(f) Dwelling conservation.** No dwelling count anywhere was reduced. The declared total was **28,189**
  before this work; report it now and explain any difference building by building.
- **(g) Simulation-failure accounting.** Every Speed task that did not produce a result must be present as a
  row with a blank `heating_kwh` and a named failure class — count them per district and prove **none was
  dropped and none was pooled into an average**. `FINDING 210` (circulation-ring vertex-size mismatch,
  `RoofCeiling:Detailed`) killed ~8 % of wave 1; report how many were recovered by the T09 fix and how many
  remain unsimulated. Also check the `D-EU-35` disclosure gap: the silent `one_zone_per_floor` reroute on an
  `intersect_match` exception still writes **no `geometry_outcome`** — confirm whether T09 closed it.

### The document

Short, one table per criterion (a)–(g), each row carrying the measured value, the threshold, and
**PASS / FAIL / NOT SCOREABLE**. It ends in **one verdict**: `PASS`, or a numbered defect list, each defect
with a `file:line`. Do not add recommendations, roadmaps or next steps.

### Report

Append the T10 progress-log entry to **§8 of the plan** and one row to
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`. Then report to the director: the
verdict, the seven criteria with their measured values, and the defect list if any — nothing else.
