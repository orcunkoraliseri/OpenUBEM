**Task:** T01 + T01b, `PLAN_open61-dh-remedy-2026-08-22.md`. **Item:** OPEN-61 (T01b tracked as
OPEN-64). **Status:** done.

## 1. What changed

`total_eui_kwh_m2` was silently dropping the District Heating component of Water Systems, because
`METER_QUERY` (`openubem/results/parser.py`) names ten meters and none of them is district heating,
and no such meter exists in any `.sql` on disk (plan F1). The fix (remedy shape (b), adopted in the
plan's §6) reads the value from ABUPS instead of a meter, and folds it into DHW.

`openubem/results/parser.py`:

1. `_DISTRICT_HEATING_KEY = "WaterSystems:DistrictHeating"` — a **pseudo-meter key**, not an
   EnergyPlus meter name (no such meter exists, F1). Declared next to `_ELEVATOR_METER`.
2. `_read_abups_district_heating(conn) -> float` — reads `TabularDataWithStrings`,
   `ReportName='AnnualBuildingUtilityPerformanceSummary'`, `TableName='End Uses'`,
   `ColumnName='District Heating'`, `RowName='Water Systems'` (T01b, F11 — **not**
   `'Total End Uses'`, which is what T01 originally read verbatim per plan F2; see §5), value in
   GJ, converted to kWh via `× 1,000,000 / 3600`. Missing row, `None`, or blank string → 0.0.
3. `_parse_meters_sql`: `_DISTRICT_HEATING_KEY: 0.0` seeded in the zeros dict; the ABUPS reader is
   called on the connection already open, **after** the real meter-rows loop and inside its own
   `try/except` (see Guard 4 below for why the ordering matters).
4. `_compute_eui`: `dh_kwh = _m(_DISTRICT_HEATING_KEY)`; new column
   `eui["dhw_district_eui_kwh_m2"] = dh_kwh / floor_area`; `dh_kwh` is added into `dhw_kwh` alongside
   the gas and electric DHW terms, so it flows into `dhw_eui_kwh_m2` and thence into `total_eui_kwh_m2`
   through the existing D9 sum — **no eleventh term was added to the total expression**, which would
   have double-counted it.
5. `openubem/results/aggregator.py`: `"dhw_district_eui_kwh_m2"` added to `_STEP5_COLS`, immediately
   after `"dhw_elec_eui_kwh_m2"`; column-count comment updated (28 → 29).
6. `carbon.py` **not touched** — see §4.

## 2. The four guards (plan F5's missing-value contract, extended)

1. **Missing ABUPS row / `None` / blank string** → `_read_abups_district_heating` returns 0.0
   directly (no exception).
2. **Non-existent or unreadable `.sql` path** → `sqlite3.connect(..., mode=ro)` raises inside
   `_parse_meters_sql`'s outer `try`, caught by the pre-existing swallow-all `except Exception: pass`
   → the whole `meters` dict, district heating included, stays at its zeroed defaults. Unchanged
   pre-existing behaviour for a corrupt file.
3. **`TabularDataWithStrings` table absent entirely** (a `.sql` shape that does not occur in the real
   fleet — every production file carries it, per `check_building_integrity()`'s own existing ABUPS
   query — but occurs in several pre-existing minimal test fixtures) → `_read_abups_district_heating`
   raises `OperationalError`. **This must not zero the other nine real meters.**
4. **Guard 3 was originally implemented wrong and caught by the full suite, not by the new unit
   tests.** The ABUPS call was first placed inside the connection's `try` block *before* the
   `for name, value_j in rows:` loop that applies the real `METER_QUERY` rows. A missing
   `TabularDataWithStrings` table then raised *before* that loop ran, so the whole `meters` dict fell
   through to the outer `except Exception: pass` — silently zeroing `Cooling:Electricity`,
   `Elevators:InteriorEquipment:Electricity`, and every other real meter, not just the district-heating
   one. Caught by three previously-passing tests going red on the first full-suite run:
   `test_reads_all_four_meters`, `test_missing_meter_returns_zero`
   (`tests/test_parser_hvac_metered.py`), `test_elevator_meter_read`
   (`tests/test_parser_elevators.py`). **Fix:** the ABUPS read now runs *after* the meter-rows loop,
   wrapped in its own inner `try/except`, so a failure there defaults only
   `_DISTRICT_HEATING_KEY` to 0.0 and leaves the other nine meters exactly as read. Registered in
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 8.

## 3. The D9 invariant

`total_eui_kwh_m2` is still exactly the sum of the ten reported end-use columns (cooling, heating,
lighting, equipment, fans, pumps, `dhw_eui_kwh_m2`, cooking, refrigeration, elevators).
District heating is folded **inside** `dhw_eui_kwh_m2` (`dhw_eui_kwh_m2 = dhw_gas + dhw_elec +
dhw_district`), not appended as an eleventh summand, so the invariant holds unchanged and no double
counting occurs. `tests/test_parser_open61_district_heating.py::TestD9InvariantWithDistrictHeating`
asserts this directly, and the backwards-compatibility test asserts `total_eui_kwh_m2` is
bit-identical to the literal the pre-OPEN-61 parser produced for a `.sql` carrying no District
Heating row.

## 4. 🔴 F10 — carbon does not follow, and this fix does not make it follow

`carbon.py:106` builds `gwp_dhw = dhw_gas_eui * f_gas + dhw_elec_eui * f_elec` from the two fuel
columns only, never from `dhw_eui_kwh_m2` — `dhw_district_eui_kwh_m2` is never read by `carbon.py`.
`openubem/config.py` defines exactly one relevant factor, `GWP_NATURAL_GAS_KGCO2_KWH`; there is no
district-heating emission factor anywhere in the codebase. After this fix, `total_eui_kwh_m2` rises
by the district-heating term for any building that has one, and `gwp_total_kgco2_m2` **does not
move**, leaving the two inconsistent for those buildings. This is a real, pre-existing defect —
carbon has been missing this energy all along; T01 only makes it visible — and it is deliberately
left open. Choosing a district-heating carbon factor is a literature decision, not a coding one, and
is not made by this task. Opened as **OPEN-63** (T04).

## 5. 🔴 T01b — `Total End Uses` ≠ `Water Systems`, and CP-1 caught the difference

T01 as originally written (plan F2, verbatim) read `RowName='Total End Uses'`. On all 8,152 fleet
census rows this is identical to `RowName='Water Systems'` (F11: max per-building difference 0.0),
so F3's "100.00% of fleet district heating is Water Systems" holds — but the golden fixtures
`tests/fixtures/golden_sql/r1_single_zone.sql`, `r2_one_zone_per_floor.sql`, `r6_perimeter_core.sql`
(pre-Phase-D, Ideal-Loads-style HVAC) put **100% of their District Heating column under the `Heating`
row, 0.00 under `Water Systems`** — the mirror image of the fleet. Reading the total therefore folded
148.24 / 709.99 / 1,646.86 GJ of real space-heating energy into `dhw_eui_kwh_m2`, inflating
`total_eui_kwh_m2` by 105.05 / 78.89 / 101.66 kWh/m² and failing
`TestEuiGolden::test_r{1,2,6}_total_eui` (`heating_eui_kwh_m2` itself was untouched and its own
golden tests kept passing — the signature of energy being *added*, not a component being
recomputed). This blocked CP-1 and was logged `[OPEN]` pending a ruling.

**The fix (director, 2026-08-22):** change the query's `RowName` to `'Water Systems'`. Nothing else
changes — same table, column, GJ→kWh factor, and all four guards. This changes no fleet number (F11)
and makes all three golden tests pass again with no fixture or expected-value edit. New guard test:
`tests/test_parser_open61_district_heating.py::TestDistrictHeatingServingSpaceHeatingNotFoldedIn`,
using `r1_single_zone.sql` directly — asserts `dhw_district_eui_kwh_m2 == 0.0` and
`total_eui_kwh_m2` matches `golden_expected.json`'s pre-OPEN-61 R1 total.

The general case — a building whose district heating serves a non-DHW end use — is tracked as
**OPEN-64**.

## 6. Tests

`tests/test_parser_open61_district_heating.py`, 9 cases across 4 classes: the positive ABUPS read
(GJ→kWh conversion) and `dhw_eui_kwh_m2 == gas + elec + district`; the backwards-compatibility
load-bearing case (a `.sql` whose ABUPS table exists but carries no District Heating row →
`dhw_district_eui_kwh_m2 == 0.0` and `total_eui_kwh_m2` bit-identical to a hand-computed literal) plus
a second sub-case for a table present with unrelated rows; the no-raise guards (non-existent path,
blank string, `None`, and the reader called directly on an open connection); and the D9 invariant with
a non-zero district-heating value folded in and not double-counted.

Two pre-existing test files needed a mechanical fixture update because `_STEP5_COLS` grew by one
column (the same pattern already used when `elevators_eui_kwh_m2` was added for OPEN-46):
`tests/test_results_aggregator.py`'s `_make_metrics_df` now includes
`"dhw_district_eui_kwh_m2"` in both its failed-row (`nan`) and success-row (`0.0`) dicts.

Full suite run in the foreground: `pytest -q tests/`.
