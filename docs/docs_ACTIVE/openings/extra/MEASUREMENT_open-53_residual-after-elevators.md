# MEASUREMENT — OPEN-53: the residual that elevators do not explain

**Script:** `scripts/analysis/open53_residual-after-elevators_2026-08-21b.py`
**CSVs:** `openubem/outputs/comparisons/open53_residual-after-elevators_2026-08-21b.csv` (8,153 rows),
`openubem/outputs/comparisons/open53_residual-outliers_2026-08-21b.csv` (639 rows, `|resid| > 10`).

## C6 — F8 reproduced

Join of `open53_meter_only_eui_2026-08-21.csv` (8,153 rows) to `05_results.csv` (8,160 rows, all 12
cells) on `(cell, osm_id)`: **8,153 matched, 0 unmatched.**

- Pooled elevators: **2.2421** (matches F8's 2.2421).
- Pooled gap (`published − meter_only`): **2.5539** (matches F8's 2.5539).
- Exact match count (`gap == elevators` to 1e-6): **3,823 of 8,153** (matches F8's 3,823).

## C7 — the residual

`resid = gap − elevators`, pooled as `Σ(resid × floor_area) / Σ(floor_area)` over **n = 8,153**.

- **Pooled residual: +0.3118 kWh/m², positive.**
- Median residual: 0 (to 4 dp).
- Tail: min **−502.68**, max **+873.37** kWh/m².
- Single largest contributor by `|resid × area|`: **`relation/7480583`** (`austin_centre`),
  resid **+100.75 kWh/m²**, area 301,996.4 m², contribution **30,425,957** — this is the same
  building F9 names as 45-storey-assigned and 1.24 % of fleet floor area.

**Concentration.** Total `Σ|resid × area| = 295,217,251`. **9 of 8,153 buildings (0.11 %) carry 50 %**
of the absolute residual mass; **26 (0.32 %) carry 80 %**; **41 (0.50 %) carry 90 %**. The residual is
extremely concentrated — it is not a diffuse fleet-wide effect, it is a small number of buildings with
large per-building errors.

**Outliers (`|resid| > 10 kWh/m²`): 639 of 8,153 (7.84 %).**

Cross-tabs (outlier count / total count in that category):
- **`archetype_id`: dominated by `OpenUBEMUnknown` — 613 of 650 Unknown buildings are outliers
  (94.3 % of all Unknowns), against 26 outliers spread across every other archetype combined.**
  This is the single strongest signal in the cross-tab.
- **`cell`:** concentrated in `nyc_suburban` (287/1,589, 18.1 %) and `nyc_urban` (202/1,779, 11.4 %);
  the other ten cells are all under 6.6 %.
- **`zoning_strategy`:** `single_zone` 496/3,238 (15.3 %) vs `one_zone_per_floor` 130/4,295 (3.0 %) vs
  `perimeter_core` 13/620 (2.1 %) — `single_zone` buildings are ~5–7x more likely to be outliers.
- **`data_quality_flag`:** the two `VINTAGE_NAN_PERMISSIVE_DEFAULT` flags carry the heaviest outlier
  rates — `no_floors,no_height,no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT` 350/1,439 (24.3 %) and
  `no_floors,no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT` 205/286 (71.7 %).
- **`floor_area_provenance`: uninformative — all 8,153 rows carry `eio_simulated`,** so this column
  cannot discriminate outliers from non-outliers in this corpus.
- **T02's per-building zone-count output was not available** (T02 was not run in this pass); the
  cross-tab proceeds without it, per the plan's fallback instruction.

## Headline

The elevator adder explains F8's mean effect but not its tail. The post-elevator residual is small in
aggregate (**+0.31 kWh/m² pooled, ≈0.2 %**) but is carried almost entirely by a tiny minority of
buildings — half the absolute residual mass sits on 9 buildings, and the residual is strongly
associated with `OpenUBEMUnknown` archetype assignment, `single_zone` zoning, and the
`VINTAGE_NAN_PERMISSIVE_DEFAULT` data-quality path. This is a measurement of size and association
only; per §2 rule 1, no remedy is proposed.
