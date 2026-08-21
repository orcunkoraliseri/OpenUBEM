# MEASUREMENT — OPEN-53: what would a meter-only EUI actually cost?

**Date:** 2026-08-21
**Task:** T02, `PLAN_ten-live-items-2026-08-21.md`
**Script:** `scripts/analysis/open53_meter_only_eui_2026-08-21.py`
**Output:** `openubem/outputs/comparisons/open53_meter_only_eui_2026-08-21.csv` (8,153 rows)

## Method

Population: all 8,160 `<cell>_auto` harvest directories (T01 showed all 8,160 have a readable
`.sql`). Joined by normalised stem (`osm_id` lowercased, `/` -> `_`) to
`evidence/open48_refleet4/<cell>/results/05_results.csv`. Kept rows with
`simulation_status == 'success'`, non-null `total_eui_kwh_m2`, `floor_area_m2 > 0` -> **8,153
eligible** (matches the adopted run's known population). For each, summed every Run-Period
`*:Facility` meter in `ReportData`/`ReportDataDictionary`, converted J -> kWh, divided by the
**adopted run's** `floor_area_m2` (denominator held fixed, per the plan — OPEN-01 is settled and this
task isolates the numerator only).

## Results

- **n compared: 8,153** (100 % of the eligible population; join lost 0 buildings — see C4).
- **Meters found, fleet-wide: only two** — `Electricity:Facility` and `NaturalGas:Facility`, each
  present in 8,148/8,153 buildings (5 buildings have only one of the two, presumably all-electric or
  gas-free). **No district-heating or district-cooling `*:Facility` meter was found anywhere in the
  auto arm.**
- **Median `pct_diff`: ~0.00 %. IQR: −2.29 % to 0.00 %.** The bulk of the fleet is very close — more
  than half the buildings show effectively no gap between meter-only and published EUI.
- **Pooled figure (Σ energy ÷ Σ area, both ways):**
  - meter-only: **151.28 kWh/m²**
  - published (recomputed here from the same 8,153-row join): **153.83 kWh/m²** — matches the
    register's adopted **153.8231** to within 0.005 % (153.8304 vs 153.8231; the residual is
    floating-point summation order, not a population mismatch).
  - **Gap: −2.55 kWh/m², about −1.66 %,** meter-only reads low against published, pooled.
- **|pct_diff| > 10 %: 548 buildings (6.7 % of the population).** These are not evenly spread — the
  worst outliers (−98 % to +476 %) are concentrated in the `OpenUBEMUnknown` archetype and in a long
  tail of individual `MidriseApartment`/office buildings, not a systematic archetype-wide bias. Full
  identity list is in the CSV (`meter_only_eui`, `published_eui`, `pct_diff`, `meters_used` per
  building); 548 is too long to print here, first 60 were inspected and are dominated by `austin_*`
  and `la_suburban` stems.
- **Per-archetype median `pct_diff`:** effectively 0 % for `SmallOffice` (n=3,497),
  `RetailStandalone`, `Courthouse`, `QuickServiceRestaurant`, `FullServiceRestaurant`, `Warehouse`,
  `SuperMarket`, `PrimarySchool`; small and consistent negative for `MidriseApartment` (n=2,818,
  −2.39 %), `MediumOffice` (−2.35 %), `LargeOffice` (−4.11 %), `HighriseApartment` (−2.96 %),
  `LargeHotel` (−3.20 %). **The one archetype that stands out is `OpenUBEMUnknown` (n=650, median
  +33.9 %)** — the fallback/unclassified archetype bucket is where meter-only diverges hardest from
  published, in both directions (it contains the largest positive outliers).

## Verdict

The meter-only fallback would cost the pooled fleet EUI about **1.7 % low**, would leave the median
building essentially unchanged, but would materially mis-measure a **6.7 % tail** — concentrated in
the unclassified-archetype bucket and in a scatter of individual buildings, not a whole archetype
family. **Whether that trade is acceptable for `parse_building()`'s fallback is the user's call — this
task only supplies the size of the trade, not a recommendation.**

## Test results

- **C4** — join lost **0 buildings** (0.000 %) out of 8,160 in the auto population; every stem
  matched an `osm_id` in its cell's `05_results.csv`. PASS, well under the 5 % ceiling.
- **C5** — three buildings re-summed with a second, independently written query (per-dictionary-row
  `SUM(Value)` instead of a flat row scan): `austin_suburban/way_382991935`,
  `la_suburban/way_442624798`, `nyc_centre/way_265302125` — all three agreed to the full float
  precision printed (well past 6 significant figures). PASS.
- **C6** — pooled meter-only (**151.28 kWh/m²**) is **NOT** within 1 % of the adopted **153.8231
  kWh/m²** (actual gap 1.66 %). Stated plainly per the plan: **this is not, and would not have been, a
  validation of the census even if it had landed inside 1 % — both figures read the same simulations,
  the meter-only one just discards the zone-level detail.**

## Remedy shape (NOT applied)

Not applied. If a meter-only fallback for `parse_building()` were adopted for the 874 files that lack
`.sql`-derivable zone detail entirely (T01), the shape suggested by this measurement is: use it only
where zone-level parsing is unavailable, and flag `OpenUBEMUnknown`-archetype buildings specifically,
since that is where the fallback's error concentrates.

---

## Director addendum — 2026-08-21 (audit re-derivation, not executor work)

The task's own summary statistics (median `pct_diff` ~0 %, IQR −2.29 %…0 %, pooled gap −1.66 %)
describe the divergence as a smooth spread. Re-deriving the pooled numbers independently during the
CP-A audit shows it is not smooth — it is **deterministic and archetype-structured**, and the pooled
gap is **mostly the elevator adder**, which by construction is not an EnergyPlus meter.

Re-derived independently (audit script, scratchpad, same 8,153 rows):

- pooled meter-only **151.2765**, pooled published **153.8304** — reproduces the executor's numbers.
- per-building sign split: **3,810 exactly equal**, 3,618 meter < published, 725 meter > published.
  Roughly half the fleet's published EUI *is* the two facility meters, to full float precision.

The exact-match set is drawn on archetype lines, not scattered:

| Archetype | exact-match fraction | n |
|---|---|---|
| `SmallOffice` | 1.00 | 3,497 |
| `RetailStandalone`, `QuickServiceRestaurant` | 1.00 | 140, 50 |
| `FullServiceRestaurant` | 0.97 | 33 |
| `Courthouse` | 0.85 | 68 |
| `MidriseApartment`, `OpenUBEMUnknown`, `MediumOffice`, `LargeOffice`, `TallBuilding`, `LargeHotel`, `HighriseApartment` | 0.00 | 2,818 / 650 / 391 / 257 / 92 / 32 / 32 |

Testing `published_eui − meter_only_eui` against `elevators_eui_kwh_m2` from the same
`05_results.csv`:

- the gap equals the elevator EUI to 1e-6 for **3,823 of 8,153** buildings (3,867 at 1e-3);
- pooled elevator EUI **2.2421** vs pooled gap **2.5539** — the elevator adder accounts for
  **≈88 %** of the 1.66 % pooled gap;
- residual after removing elevators: pooled **0.31 kWh/m² (≈0.2 %)**, median 0.0000, but with a
  long two-sided tail on a minority (min −502.68, max +873.37 kWh/m²).

**What this changes.** C6's "not within 1 %" stands as written, but it should not be read as the cost
of a meter-only aggregation. Most of it is the Phase-E elevator post-processing addition, which no
meter can carry. The question OPEN-53 actually still faces is the **0.2 % pooled residual and its
tail** — a minority of buildings where meters and published totals disagree for a reason elevators do
not explain. Sizing that tail is the next measurement, not this one.

No remedy proposed and no number restated: the adopted fleet figure remains **153.8231 kWh/m² pooled
over 8,153** (`project_current_baseline`). The 153.8304 above is this audit's own recomputation over
the same rows and is not a restatement.
