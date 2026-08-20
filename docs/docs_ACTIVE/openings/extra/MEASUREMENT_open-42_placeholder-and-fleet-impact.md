# MEASUREMENT — OPEN-42: placeholder trace (T01) + fleet-EUI impact (T02)

> Plan: `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-item-sweep-2026-08-12.md`, T01+T02.
> Measurement only. Nothing fixed, nothing republished.

## T01 — where does `footprint_area_m2 == 200.0` come from

### Population re-derived

`openubem/outputs/comparisons/open01_denominator_audit.csv`, filtered to
`footprint_area_m2 == 200.0`: **30 rows**, but that is 6 unique buildings × 5 modes.
Unique stems: **exactly 6**, and they match the register's list exactly —

- `la_rural`: `way_472960972`, `way_472961034`, `way_472961088`, `way_472961091`, `way_472961171`
- `la_urban`: `way_402215469`

All `Warehouse`. Population check passes; no STOP triggered.

### The trace, stage by stage (full detail in `open42_placeholder_trace.csv`)

| Stage | File | footprint_area_m2 for the six |
|---|---|---|
| 1 — acquisition | `.../phaseE/<cell>/01_buildings.gpkg` | **real values**: 3,416.96 / 1,398.50 / 1,555.88 / 1,355.23 / 22,443.66 (la_rural); 1,173.37 (la_urban, `levels=6.0`) |
| 2/3 — enrichment/IDF | *no file on disk* | not persisted — runs in-memory inside the same script that writes stages 4/5 |
| 4 — sim manifest | `.../04_simulation_manifest.parquet` (phaseE **and** phaseE_elevrb) | column doesn't exist here; but `status=failed` for all six, `n_severe` 4–32 |
| 5 — results | `.../05_results.csv` (phaseE **and** phaseE_elevrb, the adopted baseline) | **200.0**, `simulation_status=not_simulated`, `total_eui_kwh_m2=NaN` |

**Stage 1 is clean.** `geometry.area` computed directly from the polygon (EPSG:32611, a
projected CRS) matches the stored `footprint_area_m2` exactly for all six buildings. The
source data is correct. The defect is a write, not a source, confirming the plan's hypothesis.

### The writer

**`scripts/validation/v12_cell_pipeline.py:659`**, function `_build_enriched_gdf`:

```python
footprint_area_m2 = 200.0
num_floors = 1.0
height_m = 3.5
centroid_x, centroid_y = 0.0, 0.0

if len(sim_row) > 0 and sim_row.iloc[0]["status"] == "success":
    # ... only here does footprint_area_m2 get overwritten from the EnergyPlus zone SQL ...
```

`200.0` is a **fallback default**, not a named constant (no `DEFAULT_FOOTPRINT` anywhere in
the tree). It is meant to be overwritten by a real value read back from the simulation's own
zone geometry — but only `if status == "success"`. All six buildings have
`status == "failed"` in `04_simulation_manifest.parquet` (in **both** the pre-elevator
`phaseE` and the adopted `phaseE_elevrb` runs, same `n_severe` counts in both — same failure,
reused geometry), so the `if` never fires and the default survives all the way to
`05_results.csv`, and from there into every downstream audit CSV that reads it.

This exact literal (`footprint_area_m2 = 200.0`) is repeated ad hoc in ~15 other
`scripts/validation/*.py` one-off cell/repair scripts — copy-pasted, not a shared constant.
It does **not** appear anywhere in the `openubem/` core package.

**This traces cleanly; nothing here is untraced.**

### Widen: the other 10 of the 16 Warehouses at ≤210 m²

10 of the 16 have genuine, distinct footprints (30.0–136.5 m², all different, none exactly
200.0) with `area_multiplier_aware_m2` roughly 2× the footprint (consistent with real 2-storey
small warehouses, `parse_status=ok`). They are **not** near-misses of this mechanism — they
are ordinary small buildings that simulated successfully. Only the 6 named buildings hit the
default-and-never-overwritten path.

---

## T02 — effect of the six on the adopted ~~158.0~~ **157.1 kWh/m²** fleet figure (pooled: total
simulated energy ÷ total simulated floor area; the struck figure was a count-weighted mean of the 12
cell means, superseded 2026-08-12, OPEN-43)

### Step 1: reproducing 158.0 (historical — this section reproduces the pre-OPEN-43 headline as it
stood at the time; see OPEN-43 for the now-adopted 157.1 pooled figure)

Adopted baseline artifacts: `docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/05_results.csv`,
12 cells, 8,160 rows total.

Per-cell aggregation (confirmed against `openubem/results/aggregator.py::compute_neighbourhood_summary`
and cross-checked to the elevator plan's own per-cell table, matches to 2 decimals for all 12
cells): `Σ(total_eui_kwh_m2 × floor_area) / Σ(floor_area)` over `simulation_status` = success
rows, where `floor_area = footprint_area_m2 × derive_num_floors(row)`.

The **fleet** headline is **not** the same formula pooled naively over all 8,154 successful
buildings (that gives 157.06 — off by ~1.0). It is the **weighted mean of the 12 per-cell
numbers, weighted by each cell's total building count** (`n_total`, matching the "n" column
in the elevator plan's published table, e.g. la_rural n=149 even though only 144 succeeded):

```
fleet = Σ(cell_weighted_eui × cell_n_total) / Σ(cell_n_total) = 158.0298
```

**158.0298 vs the then-adopted 158.03 / ~~158.0~~ 157.1 kWh/m² (pooled: total simulated energy ÷
total simulated floor area; the struck figure was a count-weighted mean of the 12 cell means,
superseded 2026-08-12, OPEN-43): reproduced to within 0.03.** Well inside the plan's
0.1 tolerance — no STOP.

### Step 2-4: the six buildings' actual effect

Checked the six stems directly in the adopted `phaseE_elevrb/<cell>/05_results.csv`:

| stem | cell | footprint_area_m2 | simulation_status | total_eui_kwh_m2 |
|---|---|---|---|---|
| way_472960972 | la_rural | 200.0 | not_simulated | NaN |
| way_472961034 | la_rural | 200.0 | not_simulated | NaN |
| way_472961088 | la_rural | 200.0 | not_simulated | NaN |
| way_472961091 | la_rural | 200.0 | not_simulated | NaN |
| way_472961171 | la_rural | 200.0 | not_simulated | NaN |
| way_402215469 | la_urban | 200.0 | not_simulated | NaN |

Fleet-wide, exactly **6 of 8,160** rows are non-success in the adopted baseline
(`8154 success + 6 not_simulated = 8160`), and those 6 are **exactly** the six OPEN-42 stems —
no other building in the adopted single-run baseline is excluded.

**This changes the shape of the question.** The plan's step-4 framing ("published EUIs that
are too high; correcting them moves the fleet figure down") assumed these six carry a
published EUI. They don't: `total_eui_kwh_m2` is `NaN` for all six in the adopted baseline,
and `compute_neighbourhood_summary` filters to success rows before summing both the numerator
(Σ kWh) and the denominator (Σ floor_area). **The six are already excluded from both sums.**
The "simulated areas 4,064–67,330 m²" cited in the register (and the up-to-336× error factor)
come from a **separate** diagnostic campaign — the 40,800-run E02 harvest
(`open01_denominator_audit.csv`, `auto` mode) — not from the adopted `phaseE_elevrb` run. In
that E02 harvest these buildings evidently ran far enough to write `.eio` zone geometry before
failing later; in the adopted baseline they carry no energy result at all.

**Measured impact on the published ~~158.0~~ 157.1 kWh/m² (pooled: total simulated energy ÷ total
simulated floor area; the struck figure was a count-weighted mean of the 12 cell means, superseded
2026-08-12, OPEN-43): 0.000 (0.00%), at every decimal place.**
Correcting only the declared denominator (200.0 → the E02-harvest simulated area) cannot move
a number these six buildings were never part of. This is a real, reproducible zero — not an
empty scan defaulting to 0 — and it is worth stating in one plain sentence: **the six wrong
200.0 m² denominators do not currently distort the adopted ~~158.0~~ 157.1 kWh/m² fleet figure
at all, because those six buildings never got included in it in the first place; the actual defect is
that they silently fell out of the fleet, carrying a placeholder value that would matter the
moment anyone tried to simulate them successfully or otherwise counted them in.**

### Deliverables

- `openubem/outputs/comparisons/open42_placeholder_trace.csv` — 42 rows, one per stem per
  stage per source file (T01).
- `openubem/outputs/comparisons/open42_fleet_eui_impact.csv` — 6 per-building rows +
  1 `FLEET_SUMMARY` row (T02); `eui_published`/`eui_corrected` are `NaN`/unchanged and
  `delta_kwh_m2 = 0.0` throughout, for the reason stated above.
- `openubem/outputs/comparisons/open42_t02_percell_repro.csv` — the 12-cell reproduction
  table used to confirm the aggregation formula.

### Scripts (throwaway, `scripts/analysis/`, not touched by anything downstream)

- `scripts/analysis/open42_t01_build_trace_csv.py`
- `scripts/analysis/open42_t02_reproduce_fleet_eui.py`
- `scripts/analysis/open42_t02_fleet_eui_impact.py`
