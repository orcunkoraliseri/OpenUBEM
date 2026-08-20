# MEASUREMENT — open-01-denominator-factors

> **Slug:** `open-01-denominator-factors` · **Date:** 2026-08-05 · **Register item:** OPEN-01
> **Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_published-numbers.md`, task M01.
> **This is a measurement-only report.** No remediation was performed or proposed. The only writes
> this task made are this file and `openubem/outputs/comparisons/open01_denominator_factors.csv`.

---

## 1. Method

**Per-archetype recomputation.** For each of the **25** `.idf` files in `config.BASELINE_IDF_DIR`
(`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`, verified present and
exactly 25 files by directory listing), the file was loaded with `geomeppy.IDF` (IDD pinned to
`config.ENERGYPLUS_IDD_PATH`, EnergyPlus 23.1) and passed, **unmodified and unscaled**, to
`openubem.geometry.layout_assigner.compute_band_map()`. `n_proto`, `n_storeys_represented`,
`plate_proto_m2` and `recomputed_area_m2` were read from its return dict. No hand-rolled IDF text
parsing was used (§4 pinned decision).

`layout_assigner.ARCHETYPE_IDF_MAP` (27 keys → but 28 rows below; see §2 note) was used to map each
filename to its archetype token(s) — three tokens (`LargeOfficeDetailed`, `MediumOfficeDetailed`,
`SmallOfficeDetailed`) reuse the same `.idf` file as their non-`Detailed` counterpart, so the 25 files
produce **28** archetype rows. This is a byte-identical duplication (same band map re-used, not
recomputed differently), not a discrepancy.

**Fleet join.** `openubem/outputs/comparisons/t20_r10_reach_change.csv` (7,442 rows) was read and
restricted to rows where `new_status != "applied"` (the `new_status` column is the R10/HEAD status,
confirmed by reproducing the plan's own cited fact: `new_status != "applied"` gives exactly **6,939**
rows against 7,442 total, matching PLAN_published-numbers.md §6 M01 "Why" verbatim). Each row's
`archetype_id` was joined to the per-archetype `n_storeys_represented` computed above; the row's
`error_factor = n_storeys_represented / num_floors`. `num_floors` is the real building's floor count
already present in the fleet CSV.

**Not used as a source:** `openubem/outputs/comparisons/a1_prototype_storey_structure.csv`, per §5.6/§2
rule 12 of the plan. It is used only in §4 below, as a comparison target for the required divergence
list, never as an input to the factor table or the fleet counts.

**Reproduction command** (from repo root, `./.venv/Scripts/python.exe`):
```
python <scratchpad>/m01_band_map.py   # writes m01_band_map_raw.csv, prints the cross-check
python <scratchpad>/m01_join.py       # reads m01_band_map_raw.csv + the two named fleet CSVs,
                                       # writes openubem/outputs/comparisons/open01_denominator_factors.csv
```
Both scripts are throwaway and live only in the session scratchpad (not under `docs/`, not committed
into `openubem/`), per plan §2 rule 11/§3.

---

## 2. Cross-check — MidriseApartment must return 4

**Result: PASS.** `compute_band_map()` on the raw, unscaled
`ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` returns `n_proto = 3` (the G/M/T band count — matches
`a1_prototype_storey_structure.csv`'s `num_modelled_storeys = 3` for this archetype) and
**`n_storeys_represented = 4`**, from `bands[i]["storeys_in_band"] = [1.0, 2.0, 1.0]` — the middle band
carries a `ZoneGroup` "Zone List Multiplier" of 2, exactly as documented at
`openubem/geometry/layout_assigner.py:396-397` and measured in R10/E-LA-36
(`layout_assigner.py:565-578`, *"MidriseApartment n_real=4 produced 6 simulated storeys, not 4"*). The
method was not adjusted to reach this number — it is the first and only run of the script.

Source: `<scratchpad>/m01_band_map_raw.csv`, row `archetype_id == "MidriseApartment"` →
`n_storeys_represented = 4`.

---

## 3. Per-archetype denominator table (all 28 archetype tokens / 25 baseline files)

Source: `<scratchpad>/m01_band_map_raw.csv`, direct `compute_band_map()` output, no fleet join.

| archetype_id | idf_filename | n_proto (band count) | n_storeys_represented | band storeys_in_band |
|---|---|---:|---:|---|
| College | College_90.1-2019_6A_Buffalo_v221.idf | 4 | 4 | 1,1,1,1 |
| FullServiceRestaurant | ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf | 2 | 2 | 1,1 |
| **HighriseApartment** | ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf | 3 | **10** | 1,8,1 |
| Hospital | ASHRAE901_Hospital_STD2022_Buffalo.idf | 6 | 6 | 1,1,1,1,1,1 |
| Laboratory | Laboratory_90.1-2019_6A_Buffalo_v221.idf | 6 | 6 | 1,1,1,1,1,1 |
| LargeDataCenterHighITE | ASHRAE901_DataCenterLargeHighITE_STD2019.idf | 1 | 1 | 1 |
| LargeDataCenterLowITE | ASHRAE901_DataCenterLargeLowITE_STD2019.idf | 1 | 1 | 1 |
| LargeHotel | ASHRAE901_HotelLarge_STD2022_Buffalo.idf | 4 | 4 | 1,1,1,1 |
| LargeOffice | ASHRAE901_OfficeLarge_STD2022_Buffalo.idf | 4 | 4 | 1,1,1,1 |
| LargeOfficeDetailed | ASHRAE901_OfficeLarge_STD2022_Buffalo.idf | 4 | 4 | 1,1,1,1 |
| MediumOffice | ASHRAE901_OfficeMedium_STD2022_Buffalo.idf | 3 | 3 | 1,1,1 |
| MediumOfficeDetailed | ASHRAE901_OfficeMedium_STD2022_Buffalo.idf | 3 | 3 | 1,1,1 |
| **MidriseApartment** | ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf | 3 | **4** | 1,2,1 |
| Outpatient | ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf | 3 | 3 | 1,1,1 |
| PrimarySchool | ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf | 1 | 1 | 1 |
| QuickServiceRestaurant | ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf | 2 | 2 | 1,1 |
| RetailStandalone | ASHRAE901_RetailStandalone_STD2022_Buffalo.idf | 1 | 1 | 1 |
| RetailStripmall | ASHRAE901_RetailStripmall_STD2022_Buffalo.idf | 1 | 1 | 1 |
| SecondarySchool | ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf | 2 | 2 | 1,1 |
| SmallDataCenterHighITE | SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf | 1 | 1 | 1 |
| SmallDataCenterLowITE | SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf | 1 | 1 | 1 |
| SmallHotel | ASHRAE901_HotelSmall_STD2022_Buffalo.idf | 4 | 4 | 1,1,1,1 |
| SmallOffice | ASHRAE901_OfficeSmall_STD2022_Buffalo.idf | 2 | 2 | 1,1 |
| SmallOfficeDetailed | ASHRAE901_OfficeSmall_STD2022_Buffalo.idf | 2 | 2 | 1,1 |
| SuperMarket | Supermarket_V22.1.idf | 1 | 1 | 1 |
| SuperTallBuilding | SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf | 30 | 30 | 30×1 |
| TallBuilding | TallBuilding_90.1-2019_6A_Buffalo_v221.idf | 20 | 20 | 20×1 |
| Warehouse | ASHRAE901_Warehouse_STD2022_Buffalo.idf | 1 | 1 | 1 |

**No archetype returned `n_proto == 0` or `n_storeys_represented == 0`, and `compute_band_map()` raised
no exception on any of the 25 files.** Only two archetypes carry a `ZoneGroup`-driven
`n_storeys_represented > n_proto`: **MidriseApartment** (3 → 4, list mult 2) and **HighriseApartment**
(3 → 10, list mult 8) — exactly the two files the module docstring names
(`layout_assigner.py:395-399`). All 23 other archetypes have `n_storeys_represented == n_proto`.

---

## 4. Divergence from `a1_prototype_storey_structure.csv`'s `num_modelled_storeys` (required deliverable)

`a1_prototype_storey_structure.csv` has 25 rows, one per `.idf` file, keyed by `primary_archetype`
(no separate rows for the 3 `*Detailed` archetype tokens, since those share a file with their
non-`Detailed` counterpart). Comparing its `num_modelled_storeys` column to this task's
`n_storeys_represented`:

| archetype_id | my n_proto | my n_storeys_represented | a1 num_modelled_storeys | divergence |
|---|---:|---:|---:|---|
| **HighriseApartment** | 3 | **10** | 3 | **real: −7 (a1 undercounts by the ×8 ZoneGroup mult)** |
| **MidriseApartment** | 3 | **4** | 3 | **real: −1 (a1 undercounts by the ×2 ZoneGroup mult)** |
| LargeOfficeDetailed | 4 | 4 | *(no row — shares file with LargeOffice)* | not a value mismatch, a missing key |
| MediumOfficeDetailed | 3 | 3 | *(no row — shares file with MediumOffice)* | not a value mismatch, a missing key |
| SmallOfficeDetailed | 2 | 2 | *(no row — shares file with SmallOffice)* | not a value mismatch, a missing key |

**Two genuine value divergences**, both on the two archetypes with a `ZoneGroup`. This directly
reproduces the finding the plan pre-registered at §5.6: `a1`'s `num_modelled_storeys` is the **band
count** (`n_proto`), not the multiplier-aware storey count, and its own `has_multiplier_gt_1` column
reads `False` for both `MidriseApartment` and `HighriseApartment` — confirmed again here — because
that flag tests `Zone.Multiplier` only and is blind to `ZoneGroup`'s "Zone List Multiplier". The other
23 archetypes agree exactly (`n_proto == n_storeys_represented` in both files, where a1 has a row).

The three remaining rows are not divergences in the same sense — `a1_prototype_storey_structure.csv`
never had a row for the `Detailed` tokens to begin with (it is keyed by file, not by every archetype
token that maps to that file), so there is nothing to disagree with. None of the three fleet-relevant
issue: the real fleet (`t20_r10_reach_change.csv`) contains **zero** rows with `archetype_id` in
`{LargeOfficeDetailed, MediumOfficeDetailed, SmallOfficeDetailed, College, Laboratory, RetailStripmall,
LargeDataCenterHighITE, LargeDataCenterLowITE, SmallDataCenterHighITE, SmallDataCenterLowITE}` — the
fleet only uses 18 of the 28 mapped archetype tokens (§5 table covers all 28 for completeness; §5's
fleet table covers only the 18 actually present).

---

## 5. Fleet join — per-archetype error factor table (non-`applied` rows only)

**Row-count reconciliation (required test).** `t20_r10_reach_change.csv` has 7,442 rows total.
`new_status == "applied"`: 503. `new_status != "applied"` ("non-applied"): **6,939**. Every one of the
6,939 non-applied rows' `archetype_id` matched an entry in the §3 table (0 unmatched rows) — sum of
matched + unmatched = 6,939 = non-applied count exactly, difference = 0.

`error_factor = n_storeys_represented / num_floors`, computed per row, `num_floors` from the fleet CSV.

| archetype_id | n buildings (non-applied) | n_storeys_represented | num_floors [min, median, max] | error_factor [min, median, max] |
|---|---:|---:|---|---|
| SmallOffice | 3,497 | 2 | 1, 2, 17 | 0.118, **1.000**, 2.00 |
| MidriseApartment | 2,682 | 4 | 1, 2, 9 | 0.444, **2.000**, 4.00 |
| LargeOffice | 257 | 4 | 1, 8, 20 | 0.200, **0.500**, 4.00 |
| MediumOffice | 160 | 3 | 1, 1, 3 | 1.000, **3.000**, 3.00 |
| TallBuilding | 92 | 20 | 20, 24, 39 | 0.513, **0.833**, 1.00 |
| QuickServiceRestaurant | 50 | 2 | 1, 1, 5 | 0.400, **2.000**, 2.00 |
| RetailStandalone | 47 | 1 | 1, 1, 1 | 1.000, **1.000**, 1.00 |
| FullServiceRestaurant | 33 | 2 | 1, 1, 12 | 0.167, **2.000**, 2.00 |
| LargeHotel | 33 | 4 | 1, 9, 19 | 0.211, **0.444**, 4.00 |
| HighriseApartment | 27 | 10 | 1, 16, 56 | 0.179, **0.625**, 10.00 |
| SuperTallBuilding | 24 | 30 | 40, 47.5, 105 | 0.286, **0.632**, 0.75 |
| SecondarySchool | 11 | 2 | 1, 4, 13 | 0.154, **0.500**, 2.00 |
| SmallHotel | 8 | 4 | 1, 1.5, 4 | 1.000, **3.000**, 4.00 |
| Hospital | 5 | 6 | 1, 6, 7 | 0.857, **1.000**, 6.00 |
| Outpatient | 5 | 3 | 1, 1, 3 | 1.000, **3.000**, 3.00 |
| Warehouse | 4 | 1 | 1, 1, 1 | 1.000, **1.000**, 1.00 |
| SuperMarket | 3 | 1 | 1, 1, 1 | 1.000, **1.000**, 1.00 |
| PrimarySchool | 1 | 1 | 1, 1, 1 | 1.000, **1.000**, 1.00 |

**Full distribution across all 6,939 matched rows** (plan §4: no single mean allowed as a summary):

```
count    6939.000000
mean        1.831979
std         1.230847
min         0.117647
25%         0.666667
50%         2.000000   <- median
75%         2.000000
max        10.000000
```

Full per-distinct-factor CSV is in the artifact (`open01_denominator_factors.csv`); the report body
here gives the top mass. **Building count at the most populous distinct error factors, fleet-wide:**

| error_factor | n buildings (fleet-wide) | archetypes present |
|---:|---:|---|
| 2.000000 | 2,263 | FullServiceRestaurant, LargeOffice, MidriseApartment, QuickServiceRestaurant, SecondarySchool, SmallHotel, SmallOffice |
| 4.000000 | 1,316 | LargeHotel, LargeOffice, MidriseApartment, SmallHotel |
| 0.666667 | 1,031 | LargeHotel, LargeOffice, QuickServiceRestaurant, SecondarySchool, SmallOffice, SuperTallBuilding, TallBuilding |
| 1.000000 | 877 | FullServiceRestaurant, Hospital, LargeOffice, MediumOffice, Outpatient, PrimarySchool, QuickServiceRestaurant, RetailStandalone, SmallHotel, SmallOffice, SuperMarket, TallBuilding, Warehouse |
| 1.333333 | 348 | LargeOffice, MidriseApartment, SmallHotel |
| 0.500000 | 346 | FullServiceRestaurant, LargeHotel, LargeOffice, QuickServiceRestaurant, SecondarySchool, SmallOffice |
| 0.400000 | 156 | FullServiceRestaurant, HighriseApartment, LargeHotel, LargeOffice, QuickServiceRestaurant, SecondarySchool, SmallOffice |
| 3.000000 | 124 | MediumOffice, Outpatient |
| (remaining 53 distinct factor values, 1–71 buildings each) | 1,478 | see CSV |

Only **877 of 6,939** non-`applied` buildings (12.6%) sit at `error_factor == 1.0` (denominator not
distorted). The remainder — 87.4% — have a published-EUI denominator that is systematically wrong by
a factor other than 1, ranging from ×0.118 (denominator far too small relative to the simulated
storeys, i.e. EUI overstated) to ×10.0 (`HighriseApartment`, denominator far too large relative to
simulated storeys, i.e. EUI understated). This is a report of measured fact, not a remediation
recommendation — no fix is proposed here (plan §2 rule 2).

Full row-level `error_factor` per building is in `openubem/outputs/comparisons/open01_denominator_factors.csv`.

---

## 6. The 6 locally-run buildings — the only rows with a simulation-verified denominator

Source: `openubem/outputs/comparisons/r06c_local_results.csv` (6 rows, all `MidriseApartment`,
`archetype_id` column, `run_status == "success"` for all 6). These are reported **separately** and are
**not** part of the 6,939-row fleet count above — they are the only rows in the entire project where
the denominator was checked against a real `eplusout.eio`, not recomputed statically.

| osm_id | role | num_floors | footprint_area_m2 | eio_true_floor_area_m2 | total_eui_eio (kWh/m²) |
|---|---|---:|---:|---:|---:|
| way/401907384 | applied | 6 | 602.94 | 3,617.70 | 102.07 |
| way/401910461 | applied | 6 | 721.77 | 4,330.62 | 101.94 |
| way/401910885 | applied | 6 | 477.64 | 2,865.90 | 102.14 |
| way/427049841 | applied | 8 | 778.69 | 6,229.52 | 104.64 |
| way/427049849 | identity_control | 3 | 608.16 | 2,432.76 | 99.97 |
| way/427049871 | identity_control | 3 | 712.16 | 2,848.68 | 99.66 |

For the 4 `applied` rows, `eio_true_floor_area_m2 / footprint_area_m2` ≈ `num_floors` exactly (e.g.
row 1: 3617.70 / 602.94 = 6.00 = `num_floors`), confirming `match_storeys()`'s `applied` contract holds
on real simulation output for this small sample. The 2 `identity_control` rows instead show
`eio_true_floor_area_m2 / footprint_area_m2 ≈ 4.0` (e.g. 2432.76/608.16 = 4.00) while `num_floors = 3`
for both — this reproduces **this task's own `n_storeys_represented = 4` for MidriseApartment**
(§2), not `num_floors`. That is exactly the `identity` branch's documented contract (§5.2:
`idf` untouched on non-`applied` statuses): the raw, unmatched prototype already bakes in the
`ZoneGroup` list multiplier, so it simulates 4 physical floors' worth of area regardless of the real
building's 3. Recorded as observed, real-simulation confirmation of §2/§3; not interpreted further
(out of scope for M01, which is about the non-`applied`, statically-recomputed fleet population).

---

## 7. Artifacts

- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-factors.md` — this file.
- `openubem/outputs/comparisons/open01_denominator_factors.csv` — 6,939 rows, one per non-`applied`
  fleet building, columns: `cell, osm_id, archetype_id, num_floors, n_proto_fleet_col,
  n_proto_recomputed, n_proto_mismatch, n_storeys_represented_recomputed, error_factor, old_status,
  new_status, changed`. `n_proto_mismatch` is `False` on all 6,939 rows — this task's recomputed
  `n_proto` agrees with the fleet CSV's own `n_proto` column on every row, an internal consistency
  check that was not required by the plan but is reported because it came free from the join.

---

## 8. Summary for CP-M1

- **MidriseApartment cross-check: PASS (4).**
- **6,939 of 7,442** fleet rows are non-`applied` (93.2%), reproducing the plan's pre-stated figure.
- Only **2 of 28** archetype tokens carry a `ZoneGroup` multiplier (`MidriseApartment`,
  `HighriseApartment`); the other 26 have `n_storeys_represented == n_proto`.
- **`a1_prototype_storey_structure.csv` is confirmed wrong** for exactly those same 2 archetypes — it
  reports the band count, not the multiplier-aware storey count, for `MidriseApartment` (3 vs. real 4)
  and `HighriseApartment` (3 vs. real 10). Both discrepancies were independently re-derived here, not
  taken from the plan's citation.
- The fleet-wide error factor is **not** a small rounding effect: only 12.6% of non-`applied` buildings
  have `error_factor == 1.0`; the median across all 6,939 is 2.0, and the range spans ×0.118 to ×10.0.
  This bears on the OPEN-01 remedy choice (fix denominator / fix simulation / stop publishing
  per-building EUI) but no remedy is chosen or proposed in this document.
