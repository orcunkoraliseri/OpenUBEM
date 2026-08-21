# MEASUREMENT — OPEN-61 fleet census

> Plan: `docs/docs_ACTIVE/openings/implemenation/PLAN_open61-census-open03-storeys-2026-08-20.md`
> Predecessor: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md`

## T01 — the district-heating read path

**Read path.** `scripts/analysis/open61_census_read_2026-08-20.py`, function
`read_district_heating(sql_path)`. It reads the ABUPS "End Uses" table via the
`TabularDataWithStrings` view (`ReportName='AnnualBuildingUtilityPerformanceSummary'`,
`TableName='End Uses'`, `ColumnName='District Heating'`, `RowName='Total End Uses'`) — this is
path (a).

**Path (b) does not exist.** For every `.sql` inspected (the 5 known-positive/43 known-negative
buildings in `open61_district_source.csv`, all 60 in `open61_production_sample.csv`, and both
scratch control buildings), `ReportDataDictionary` carries **no meter or variable whose name
contains "District" at all** — confirmed table-wide with
`select distinct Name from ReportDataDictionary where Name like '%Heating%'`, which returns only
`Heating:NaturalGas` and `Heating:Electricity`. This matches F1 (the plan): `METER_QUERY`
requests ten meters and none of them is district heating, so no `DistrictHeating:Facility`-style
row is ever written to `ReportData`. **The census therefore rests on a single independent read
path (a), not two.**

**Third check used instead (per the plan's fallback).** For every row read, the ABUPS
`Total End Uses` value for the District Heating column is checked against the sum of that
column's 14 named end-use rows (Heating, Cooling, Interior Lighting, Exterior Lighting, Interior
Equipment, Exterior Equipment, Fans, Pumps, Heat Rejection, Humidification, Heat Recovery, Water
Systems, Refrigeration, Generators). This reconciled on every row tested (108/108). It is a
self-consistency check on path (a), not a second independent source, and is reported as such.

**Verification counts.**
- 5 known-positive buildings: **5/5** non-zero and match the recorded `dh_total_gj` to 2 decimals
  (way_1008727470 = 0.72, way_425993511 = 576.02, way_265424467 = 134.49, way_846412106 = 0.34,
  way_241862488 = 0.77).
- 43 known-negative buildings in the 48-sample: **43/43** read exactly 0.00.
- Full 48-row sample (`open61_district_source.csv`) against its own `dh_total_gj` column:
  **48/48**.
- 60-row production sample (`open61_production_sample.csv`) against its own `dh_total_gj`
  column: **60/60**.

**T01 experiment control (re-derived).** Scratch artifact found at
`scratchpad/open61_c2_experiment/{baseline,treated}/out/eplusout.sql` (per the predecessor
report). Re-running the new reader on both:

| | baseline | treated (orphan `DHW_WaterUse_*` pair deleted) |
|---|---|---|
| District Heating, Total End Uses | **0.72 GJ** | **0.00 GJ** |
| Water Systems, Natural Gas | 11.68 GJ | 11.68 GJ (unchanged) |

Matches the predecessor's recorded result exactly. Control passes.

**Deliverable CSV.** `openubem/outputs/comparisons/open61_census_read_verification.csv` — 108
rows (48 + 60), one row per verified building: sample, cell, osm_id, recorded `dh_total_gj`,
reader value (a), reader value (b) (blank — not available), self-reconciliation flag, agreement
flag.

**Conclusion.** The read path is sound and reproduces every recorded value exactly, but it is
proven **once**, not twice — path (b) is structurally absent from this fleet's `.sql` files, and
the plan's own fallback (ABUPS internal reconciliation) was substituted and passed on all 108
rows tested.
