# Golden archetype x end-use table (C04)

## Provenance

Computed 2026-09-18, TechTransfer block 6, Task C04 (`docs/docs_ACTIVE/TechTransfer/implementation/PLAN_techtransfer-block6-2026-09-18.md` §2a).

**Sample:** 20 buildings = 2 WWR variants (`wwr=0.30` and `wwr=0.45`, suffix `_V2` on the second
variant's `osm_id`) x the 10-archetype `tests/fixtures/synthetic_10_buildings.py` fixture
(`_build_rows()`), built and simulated through the real pipeline: `openubem.idf.builder.run_step3`
(resolution_mode="auto", default) -> `openubem.simulation.parallel.run_neighbourhood` -> per-building
`openubem.results.parser.parse_building`.

**EPW:** `USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw` (shipped with the EnergyPlus install, same EPW
used by `tests/test_sim_integration.py`). **EnergyPlus version:** 23.1.0. **Run:** local `loky` pool,
case count 20, parallel width 20 (CLAUDE.md cluster/parallel rule — stated before running).

**Outcome:** 20/20 IDFs generated (`generation_status=success`); 18/20 simulated successfully.
`way/R8` and `way/R8_V2` (archetype `Warehouse`, single_zone, 4900 m² 1-floor) both hit a
`** Fatal **` temperature-out-of-bounds error under `resolution_mode="auto"` — this is the
pre-existing, known, out-of-scope issue named in block6 §2 ("Warehouse `auto`-mode IDF failure —
Pre-existing, known, out of scope — Not part of this arc"), not a new defect; not registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` because it was not solved here (out of scope
per the plan). `Warehouse` is therefore absent from the golden table. The remaining 9 archetypes x
2 buildings each = 18 buildings, 9 archetypes, comfortably above the plan's >= 12 buildings / >= 4
archetypes minimum.

## Files

- `golden_table.csv` — mean per-archetype EUI (kWh/m²) for 11 end uses, indexed by `archetype_id`,
  with `n_buildings` (always 2 here). This is the comparison target.
- `per_building_raw.csv` — the 18 individual `parse_building()` output rows (osm_id, archetype_id,
  parse_status, all EUI columns) the golden table was averaged from; kept for traceability only, not
  read by the test.

## End uses covered

`heating`, `cooling`, `lighting`, `equipment`, `fans`, `pumps`, `dhw`, `cooking`, `refrigeration`,
`elevators`, `total` (all `*_eui_kwh_m2`, per `openubem/results/parser.py::_compute_eui`).
`cooking`/`refrigeration`/`elevators` read 0.0 for every archetype in this sample — none of the 10
synthetic-fixture archetypes carries a gas-cooking, refrigeration, or elevator meter; the column is
still compared (a future regression that turns one non-zero is still caught).

## Regenerating

Not automated (one-off golden-table generation, not part of the build path). To regenerate: rebuild
the same 20-building sample (`tests/fixtures/synthetic_10_buildings.py::_build_rows`, 2 variants as
above), run `run_step3` -> `run_neighbourhood` -> `parse_building` per success row, group by
`archetype_id`, mean the 11 `*_eui_kwh_m2` columns, round to 6 decimals.
