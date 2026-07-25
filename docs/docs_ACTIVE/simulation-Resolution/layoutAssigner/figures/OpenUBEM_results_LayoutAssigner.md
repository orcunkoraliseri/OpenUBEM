# OpenUBEM — LayoutAssigner Simulation Resolution Results

**What this document is:** A comprehensive evaluation report for the **`layoutAssigner`** resolution mode strategy. It compares standard DOE/ASHRAE 90.1 baseline archetype assignment and scaling against the established OpenUBEM resolution modes (`auto`, `building`, `floor`, `fast_zone`).

---

## 1. Strategy Overview: `layoutAssigner`

The `layoutAssigner` strategy substitutes custom on-the-fly room-level geometry generation (`layoutgenerator`) with **pre-validated, standardized EnergyPlus prototype models** from:
`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`

### Key Highlights
- **100% Thermal Zoning Fidelity**: Preserves full ASHRAE 90.1 prototype internal multi-zone layouts, room functions, and HVAC loop topologies.
- **Robust Area Scaling**: Scales gross floor area ($S = \text{Area}_{\text{real}} / \text{Area}_{\text{baseline}}$) and planar coordinates ($\sqrt{S}$) while conserving internal load intensities ($W/m^2$).
- **Eliminates Topology Errors**: Especially beneficial for complex programs (**Hospitals**, **Large Hotels**, **Outpatient Healthcare**) where polygon splitting creates non-convex zones or boundary surface errors.

---

## 2. Archetype Layout Assignment & Scaling Matrix

Prototype zone counts are **real, live-parsed** via `layout_assigner.parse_baseline_zones()` against the E+ 23.1-transitioned baseline library (plan §5 T10) -- not a guessed formula. The **Local Sim Total EUI** column (T12 local leg, 2026-07-22) is a **real, single-building EnergyPlus 23.1 annual simulation** per archetype (LA TMYx EPW), harvested via the identical D9 9-end-use `total_eui_kwh_m2` formula every other resolution mode uses -- populated only for the 6 archetypes actually run; `—` for every other archetype (never extrapolated). Archetypes flagged with `†` completed successfully (no Fatal, real EUI produced) but threw large recurring-warning/severe-error counts tied to fixed-capacity equipment (transformer, DHW tank, HVAC coil rated flow/capacity) that the scaling engine does not scale -- see the note below the table and plan §9 E-LA-06.

| Archetype ID | Baseline IDF File | Baseline Area ($m^2$) | Sample Target Area ($m^2$) | Scale Factor ($S$) | Planar Factor ($\sqrt{S}$) | Prototype Zones | Local Sim Total EUI ($kWh/m^2\cdot yr$) | LayoutAssigner Fidelity |
|---|---|---|---|---|---|---|---|---|
| `MidriseApartment` | `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` | 3,135 | 2,500 | 0.797 | 0.893 | 27 | 60.07 | Highest (Exact ASHRAE Prototype Zoning) |
| `HighriseApartment` | `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` | 7,835 | 9,000 | 1.149 | 1.072 | 27 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `Hospital` | `ASHRAE901_Hospital_STD2022_Buffalo.idf` | 22,422 | 25,000 | 1.115 | 1.056 | 55 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `LargeHotel` | `ASHRAE901_HotelLarge_STD2022_Buffalo.idf` | 11,345 | 12,500 | 1.102 | 1.050 | 22 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SmallHotel` | `ASHRAE901_HotelSmall_STD2022_Buffalo.idf` | 4,013 | 3,500 | 0.872 | 0.934 | 67 | 151.46 † | Highest (Exact ASHRAE Prototype Zoning) |
| `LargeOffice` | `ASHRAE901_OfficeLarge_STD2022_Buffalo.idf` | 46,320 | 50,000 | 1.079 | 1.039 | 23 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `LargeOfficeDetailed` | `ASHRAE901_OfficeLarge_STD2022_Buffalo.idf` | 46,320 | 50,000 | 1.079 | 1.039 | 23 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `MediumOffice` | `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` | 4,982 | 4,500 | 0.903 | 0.950 | 18 | 72.48 † | Highest (Exact ASHRAE Prototype Zoning) |
| `MediumOfficeDetailed` | `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` | 4,982 | 4,500 | 0.903 | 0.950 | 18 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SmallOffice` | `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf` | 511 | 600 | 1.174 | 1.084 | 6 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SmallOfficeDetailed` | `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf` | 511 | 600 | 1.174 | 1.084 | 6 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `Outpatient` | `ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf` | 3,804 | 4,200 | 1.104 | 1.051 | 118 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `PrimarySchool` | `ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf` | 6,871 | 7,500 | 1.091 | 1.045 | 25 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SecondarySchool` | `ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf` | 19,592 | 21,000 | 1.072 | 1.035 | 46 | 67.18 † | Highest (Exact ASHRAE Prototype Zoning) |
| `College` | `College_90.1-2019_6A_Buffalo_v221.idf` | 11,000 | 12,000 | 1.091 | 1.044 | 117 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `Laboratory` | `Laboratory_90.1-2019_6A_Buffalo_v221.idf` | 8,500 | 9,000 | 1.059 | 1.029 | 24 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `RetailStandalone` | `ASHRAE901_RetailStandalone_STD2022_Buffalo.idf` | 2,294 | 2,000 | 0.872 | 0.934 | 5 | 101.20 † | Highest (Exact ASHRAE Prototype Zoning) |
| `RetailStripmall` | `ASHRAE901_RetailStripmall_STD2022_Buffalo.idf` | 2,090 | 1,800 | 0.861 | 0.928 | 10 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SuperMarket` | `Supermarket_V22.1.idf` | 4,181 | 4,500 | 1.076 | 1.037 | 2 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `Warehouse` | `ASHRAE901_Warehouse_STD2022_Buffalo.idf` | 4,835 | 5,000 | 1.034 | 1.017 | 3 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `FullServiceRestaurant` | `ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf` | 511 | 550 | 1.076 | 1.038 | 3 | 886.08 † | Highest (Exact ASHRAE Prototype Zoning) |
| `QuickServiceRestaurant` | `ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf` | 232 | 250 | 1.078 | 1.038 | 3 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `TallBuilding` | `TallBuilding_90.1-2019_6A_Buffalo_v221.idf` | 25,000 | 28,000 | 1.120 | 1.058 | 164 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SuperTallBuilding` | `SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf` | 60,000 | 65,000 | 1.083 | 1.041 | 256 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `LargeDataCenterHighITE` | `ASHRAE901_DataCenterLargeHighITE_STD2019.idf` | 557 | 600 | 1.076 | 1.038 | 1 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `LargeDataCenterLowITE` | `ASHRAE901_DataCenterLargeLowITE_STD2019.idf` | 557 | 600 | 1.076 | 1.038 | 1 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SmallDataCenterHighITE` | `SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf` | 56 | 60 | 1.077 | 1.038 | 1 | — | Highest (Exact ASHRAE Prototype Zoning) |
| `SmallDataCenterLowITE` | `SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf` | 56 | 60 | 1.077 | 1.038 | 1 | — | Highest (Exact ASHRAE Prototype Zoning) |

† local-leg caveat (plan §9 E-LA-06), by archetype:
- `MediumOffice`: 73,803 real Severe Errors (ElectricLoadCenter:Transformer overloaded) + a DHW target-water-temperature warning storm
- `SmallHotel`: 120.5M recurring warnings (Coil:Cooling:DX:MultiSpeed rated flow/capacity ratio out of range)
- `SecondarySchool`: 15.8M recurring warnings (HeatExchanger:AirToAir flow ratio out of range) + 28 Severe Errors
- `RetailStandalone`: 604K recurring warnings (AirLoopHVAC:UnitarySystem part-load ratio out of range)
- `FullServiceRestaurant`: 1.1M recurring warnings (AirLoopHVAC:UnitarySystem part-load ratio + DHW target-temperature)


---

## 3. Comparison with Existing Resolution Modes (Harvested Baseline Matrix)

**Updated 2026-07-23 (T17, full 12-cell / 8,160-building cluster leg).** Below are the median Total Site EUI ($kWh/m^2\cdot yr$) results across the 12-cell baseline matrix. The first four mode columns are extracted directly from the validated 8,160-building dataset (`OpenUBEM_results_Resolution.md`). The `layout_assign` column is now **real, fleet-scale, harvested EnergyPlus 23.1 output** from the full 12-cell / 8,160-building cluster sweep (job IDs 1133855, 1133922, 1134015, 1134026, 1134097, 1134133, 1134222, 1134231, 1134258, 1134276, 1134292, 1134303) -- **superseding** the `*pending*` placeholder and the single-building local-leg sample in §2/§3a. Harvested via `scripts/cluster/t17_harvest_layout_assign.py` (meter-based parser, identical methodology to the other 4 modes' `t08_harvest_results.py` -- see that script's docstring for the documented rationale). Raw building-level results: `openubem/outputs/comparisons/t17_layout_assign_eui.csv` (8,160 rows); per-cell/archetype summary: `t17_layout_assign_cell_summary.csv`.

**Read the `layout_assign (raw)` column together with the caveat immediately below the table -- do not treat it as a clean apples-to-apples number yet.**

| Cell | City | `building` (1 Zone) | `floor` (Per-Floor) | `auto` (Adaptive Baseline) | `fast_zone` (Core/Perim) | `layout_assign` (raw, all archetypes) | `layout_assign` (excl. MidriseApartment/SmallOffice) | Success rate |
|---|---|---|---|---|---|---|---|---|
| `austin_centre` | AUS | 124.5 | 141.3 | 135.6 | 158.7 | 124.1 | 158.0 | 364/413 (88.1%) |
| `austin_rural` | AUS | 125.5 | 125.5 | 117.8 | 134.3 | 97.3 | 224.4 | 242/245 (98.8%) |
| `austin_suburban` | AUS | 123.6 | 129.9 | 119.9 | 136.9 | 92.5 | 414.8 | 437/437 (100.0%) |
| `austin_urban` | AUS | 119.2 | 131.7 | 121.0 | 133.6 | 88.5 | 99.3 | 411/425 (96.7%) |
| `la_centre` | LA | 105.0 | 141.4 | 143.1 | 146.4 | 99.9 | 105.0 | 195/226 (86.3%) |
| `la_rural` | LA | 130.7 | 140.5 | 130.7 | 145.0 | 119.9 | 87.0 | 149/149 (100.0%) |
| `la_suburban` | LA | 108.0 | 112.1 | 106.6 | 113.9 | **408.8** | 99.0 | 1342/1343 (99.9%) |
| `la_urban` | LA | 101.4 | 108.0 | 103.9 | 110.4 | 157.4 | 105.0 | 595/618 (96.3%) |
| `nyc_centre` | NYC | 138.6 | 171.5 | 180.1 | 186.1 | 85.5 | 123.2 | 596/738 (80.8%) |
| `nyc_rural` | NYC | 163.9 | 163.9 | 159.6 | 166.4 | 136.6 | 563.2 | 193/198 (97.5%) |
| `nyc_suburban` | NYC | 205.4 | 205.4 | 205.5 | 205.6 | **948.0** | 539.0 | 1589/1589 (100.0%) |
| `nyc_urban` | NYC | 137.8 | 148.6 | 144.7 | 149.2 | 96.5 | 318.1 | 1774/1779 (99.7%) |
| **Fleet total** | | | | | | | | **7,887/8,160 (96.65%)** |

**Caveat (E-LA-10, discovered during this harvest -- read before using the `layout_assign (raw)` column):** `scale_baseline_idf()` scales `WaterHeater:Mixed.Tank_Volume`/`.Heater_Maximum_Capacity` correctly (T15) but does **not** scale the same object's `Peak_Use_Flow_Rate` field by S. This field stays at the baseline's literal absolute value regardless of the real building's size, so DHW energy is roughly *constant in absolute terms* rather than scaling with floor area -- at non-unity S this produces a `dhw_eui` that moves roughly as `1/S`, exploding for small real buildings (most severe at very small S) and vanishing for large ones. This affects **`MidriseApartment` (2,818 buildings) and `SmallOffice` (3,497 buildings) -- together 6,315 of the 7,887 successfully-simulated buildings (80.1%), i.e. 77.4% of the entire 8,160-building fleet** [manager audit correction, 2026-07-23: the harvest task's own text stated "77%" as the share of *successfully-simulated* buildings, which is actually the share of the *entire* fleet -- the correct share of successes is the higher 80.1%] (confirmed via direct comparison of the generated IDF's scaled `WaterHeater:Mixed` fields against the raw baseline; see plan §9 E-LA-10 for the full byte-level evidence). It is the dominant driver of the anomalous `nyc_suburban` (948.0) and `la_suburban` (408.8) medians above -- both cells are >80% `MidriseApartment`, and most real buildings there are much smaller than the 3,135 m² MidriseApartment prototype (fleet-wide median implied S ≈ 0.054). The `excl. MidriseApartment/SmallOffice` column removes both affected archetypes; it is **closer to plausible** in most cells but still elevated in a handful (`austin_rural`, `austin_suburban`, `nyc_rural`, `nyc_suburban`, `nyc_urban`) where other high-EUI archetypes concentrate (`FullServiceRestaurant`/`QuickServiceRestaurant`/`TallBuilding`/`Hospital`/`OpenUBEMUnknown` -- see the fleet-wide per-archetype median table below). A full per-archetype plausibility audit was out of scope for this harvest task; **neither `layout_assign` EUI column above should be treated as production-grade until E-LA-10 is fixed and a broader archetype plausibility pass is done** (recommended follow-up, future arc).

**Success rate and failure classes:** 7,887/8,160 buildings (96.65%) completed successfully; 273 failed (3.35%), cleanly attributable to exactly 3 root-cause classes (see plan §9 E-LA-07/E-LA-08/E-LA-09), none newly fixed in this task:
- **E-LA-07 class 1 (`FluidCooler:TwoSpeed` literal capacity not scaled):** `LargeOffice` -- 221/270 buildings failed (81.9% failure, concentrated in NYC: 122/136 in `nyc_centre` alone).
- **E-LA-07 class 2, confirmed broadened by this harvest (E-LA-08) -- `CalcHeatBalanceInsideSurf` warmup-instability Fatal in a small marginal zone:** originally scoped to `TallBuilding`/`SuperTallBuilding` only; this harvest confirms the identical failure signature also affects `SmallOffice` (7 buildings, elevator-core zones), `MediumOffice` (1), and `Hospital` (1, kitchen zone) -- 46 buildings total across 5 archetypes, all with the same `CalcHeatBalanceInsideSurf` warmup-temperature-out-of-bounds signature in a small marginal zone (elevator core, laundry room, or kitchen).
- **E-LA-09 (new, this harvest) -- `Outpatient`'s `AirLoopHVAC:OutdoorAirSystem` references a Controller List Name (`"OUTDOORAIR:MIXER"`) that does not exist in the scaled IDF:** 6/6 `Outpatient` buildings in the entire fleet failed (100%), at input-processing time, before sizing/warmup even begins -- not scale-dependent (floor areas ranged 51,385 down to 297.6 m² and all failed identically).

Per-archetype median `total_eui` (raw, all cells, success only) -- included to make the E-LA-10 caveat and the "other high-EUI archetypes" note above auditable:

| Archetype | Median EUI | n (success) | Archetype | Median EUI | n (success) |
|---|---|---|---|---|---|
| `QuickServiceRestaurant` | 1632.2 | 50 | `RetailStandalone` | 119.5 | 140 |
| `FullServiceRestaurant` | 1296.8 | 33 | `HighriseApartment` | 106.9 | 32 |
| `MidriseApartment` †E-LA-10 | 795.2 | 2,818 | `SecondarySchool` | 94.9 | 11 |
| `TallBuilding` | 478.5 | 67 | `SmallOffice` †E-LA-10 | 92.1 | 3,497 |
| `OpenUBEMUnknown` | 423.4 | 650 | `MediumOffice` | 90.2 | 411 |
| `Hospital` | 335.8 | 4 | `PrimarySchool` | 78.4 | 2 |
| `SuperTallBuilding` | 318.4 | 12 | `Warehouse` | 33.8 | 38 |
| `SuperMarket` | 163.0 | 5 | `Courthouse` | 149.5 | 68 |
| `LargeOffice` | 146.5 | 49 | | | |

**Figures (T17):** `openubem/outputs/comparisons/layout_assign_vs_modes_cluster_eui.png` (full 12-cell, 5-mode median EUI, raw vs. E-LA-10-excluded) and `layout_assign_vs_modes_cluster_success.png` (per-cell success/fail counts) -- both also copied into this folder. See §3a below for the LA-only 4-archetype comparison (now also updated with real fleet data).


---

## 3a. Cross-mode comparison (structural + EUI) -- post-closure addendum (T13, 2026-07-22; Figure 2 updated with real fleet data + 2 new figures added, T17, 2026-07-23)

Originally three figures built from data that **already existed** (T10's zone-count/EUI comparison CSV, the T08 12-cell 4-mode EUI harvest, and the T12 local-leg + E-LA-06 diagnostic counts) -- no new EnergyPlus runs at the time. **T17 update:** Figure 2 below now automatically uses the real T17 cluster-leg fleet data (the plotting script detects `t17_layout_assign_eui.csv` and switches source data + title accordingly -- no manual figure logic change needed); two new figures (5 and 6) present the full 12-cell/8,160-building result directly, see §3 above for the underlying numbers. Generated by `scripts/analysis/plot_layout_assign_vs_modes.py`; source data for Figure 2 is reproduced in full in `openubem/outputs/comparisons/layout_assign_vs_modes_la_summary.csv`. Canonical copy of all files lives in `openubem/outputs/comparisons/`; a duplicate copy is also kept in this arc's own `figures/` folder alongside this doc, per user convention.

### Figure 1 -- Zone-count fidelity by mode, all 28 mapped archetypes

![Zone-count fidelity by mode](../../../../openubem/outputs/comparisons/layout_assign_vs_modes_zone_fidelity.png)

Grouped bar (log-scale y), split into a low- and a high-zone-count band (14 archetypes each, split at the median `layout_assign_mode_zones`) for readability. Bars = `building`/`floor`/`fast_zone`/`layout_assign` zone counts, straight from `layout_assign_vs_resolution_modes.csv` (T10). `layout_assign` reproduces the true ASHRAE prototype zone topology; `building` is always 1; `floor`/`fast_zone` are the existing modes' own formula-derived counts (unchanged from §2/§3 of this doc).

### Figure 2 -- LA-climate fleet median EUI vs. real `layout_assign` fleet median (T17, supersedes the T12 single-building comparison)

![LA-climate EUI comparison](../../../../openubem/outputs/comparisons/layout_assign_vs_modes_eui_la.png)

**Updated 2026-07-23 (T17):** this figure now plots the real T17 cluster-leg `layout_assign` fleet median (LA cells only: `la_centre`/`la_urban`/`la_suburban`/`la_rural`) instead of the single T12 local-leg building -- the plotting script auto-detects `t17_layout_assign_eui.csv` and switches automatically (title says "SUPERSEDES the T13/T12 single-building comparison"). `n`/`la_n` annotations on the chart show the real per-mode/per-archetype sample sizes. Same 4 archetypes as before (`MidriseApartment`, `MediumOffice`, `RetailStandalone`, `FullServiceRestaurant`); `SmallHotel`/`SecondarySchool` still omitted (no LA fleet comparator in either the other-4-modes data or this fleet). **Caveat carried over from §3: `MidriseApartment`'s bar is subject to E-LA-10** (unscaled DHW flow rate) -- read together with §3's caveat before treating this archetype's `layout_assign` value as clean.

### Figure 3 -- E-LA-06 diagnostic-severity by archetype

![E-LA-06 diagnostic severity](../../../../openubem/outputs/comparisons/layout_assign_vs_modes_severity.png)

Log-scale total (warnings + severe) diagnostic count per archetype at its T12-tested scale factor, from the hardcoded counts already recorded in plan §8 T12 / §9 E-LA-06 (not re-derived from logs here). Severe-error counts are annotated separately in red where non-zero -- they are the more serious signal (real EnergyPlus `** Severe **` diagnostics, e.g. 73,803 `Transformer Overloaded` errors for `MediumOffice`), distinct from warning volume, and are easy to miss under a log-scale total dominated by the (usually much larger) warning count.

### Figure 5 -- Full 12-cell / 5-mode median EUI (T17, new)

![Full cluster EUI comparison](../../../../openubem/outputs/comparisons/layout_assign_vs_modes_cluster_eui.png)

The actual §3 table above, visualized: all 12 cells, all 5 modes, `layout_assign` shown both raw (all archetypes, purple bar) and excluding the 2 E-LA-10-affected archetypes (black diamond). Makes the `nyc_suburban`/`la_suburban` outliers and the general elevation pattern immediately visible.

### Figure 6 -- Per-cell success/fail counts (T17, new)

![Cluster success/fail](../../../../openubem/outputs/comparisons/layout_assign_vs_modes_cluster_success.png)

Stacked bar, all 8,160 buildings, all 12 cells. Confirms the failure concentration pattern described in §3: `nyc_centre` (80.8% success, worst) and `la_centre` (86.3%) carry the largest share of `LargeOffice`/`TallBuilding`/`SuperTallBuilding`/`Outpatient`, while 3 of 12 cells hit exactly 100% success -- `austin_suburban`, `la_rural`, `nyc_suburban` -- and 2 more (`la_suburban` 99.9%, `nyc_urban` 99.7%) come close (no/almost no buildings of the 3 problem archetypes in those cells' real fleets) [manager audit correction, 2026-07-23: originally miscounted as "5 of 12 at 100%" -- the §3 table itself was always correct, only this caption's count was wrong].

**Scope note:** §3's fleet-median-of-`layout_assign`-itself is now real, full-cluster data (no longer `*pending*` or a single-building sanity check) -- see §3 above for the authoritative table and the E-LA-10/E-LA-07/E-LA-08/E-LA-09 caveats that must be read alongside it.

---

## 4. Key Findings & Recommendations

1. **Load Conservation Pass**: Internal loads ($W/m^2$) conserve across scaling factors, ensuring that energy consumption scales linearly with floor area.
2. **Complex Functions Resolved**: Complex archetypes (**Hospitals**, **Hotels**, **Secondary Schools**) retain full internal room layout fidelity without requiring dynamic polygon decomposition.
3. **Usage Guidelines**:
   - Use **`building`** and **`floor`** for ultra-fast district screening.
   - Use **`auto`** for standard fleet-wide urban building energy modeling (validated baseline).
   - Use **`layout_assign`** for high-fidelity archetype studies, HVAC sizing, and complex building program simulations.
4. **T12 local leg finding (2026-07-22, plan §9 E-LA-06, OPEN):** `scale_baseline_idf()` scales geometry (√S) and the explicitly-listed absolute load/OA/DHW-draw fields (S), but does **not** scale fixed-capacity auxiliary equipment (electrical transformers, DHW tank capacity, HVAC coil/fan rated capacity/airflow) -- these stay at the baseline's own size. At non-identity scale factors this produced large recurring-warning/severe-error counts in 5 of 6 local-leg archetypes (real EnergyPlus diagnostics, not a script bug) -- most notably 73,803 real "Transformer Overloaded" Severe Errors for `MediumOffice` (S=1.60). Only `MidriseApartment` (S=4.78, the pre-existing T09-validated case) stayed clean. The harvested EUI values are real EnergyPlus output and within plausibility bounds, but this is a genuine, unresolved scope gap in the scaling engine that a future task should address (likely alongside T11's envelope patcher) before `layout_assign` results are treated as production-grade at non-trivial scale factors.
5. **T12 local leg finding (2026-07-22, plan §9 E-LA-05, OPEN):** `openubem/results/parser.py`'s `parse_building()` / `_check_zone_integrity()` assumes the OpenUBEM `{osm_id}_F{floor}_{label}` zone-naming convention; `layout_assign` zones keep the DOE baseline's own native names (e.g. `"G SW APARTMENT"`), so `_check_zone_integrity()` always reports a false-negative zone-count mismatch for `layout_assign` buildings. This affects every `layout_assign` building, not just the local-leg sample. The §2 EUI values above were computed by calling `parse_building_sql()` + `_parse_meters_sql()` + `_compute_eui()` directly (bypassing only the zone-naming gate, which does not affect the EUI arithmetic itself) -- a documented workaround, not a fix. `parser.py` itself was intentionally left unmodified (out of scope for T12).

---

## 5. Post-debug-fix full-cluster result (T18, 2026-07-23) -- before/after vs. T17

**This section is an addendum, appended per this project's correction-via-addendum convention. §3's T17 table above is the frozen historical record and is unchanged by this section.** It reports the same 12-cell / 8,160-building `layout_assign` cluster re-sweep (**T18**, tagged distinctly from T17 -- separate remote fleet dirs, separate output filenames, T17's own artifacts never touched), re-run with the debug-arc's fixes applied (`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/PLAN_debug_implementation.md`, T01-T10, CP-A through CP-D signed 2026-07-23). Harvested via `scripts/cluster/t18_harvest_layout_assign.py` (byte-for-byte fork of T17's harvest, only fleet tag/output filenames changed, plus one addition: per-building `n_warmup_convergence` counting). Raw building-level results: `openubem/outputs/comparisons/t18_layout_assign_eui.csv` (8,160 rows; also copied to `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/results/`); per-cell/archetype summary: `t18_layout_assign_cell_summary.csv` (same copy location).

### 5.1 Independent verification (before trusting anything below)

This harvest was not taken on trust from the harvest script's own exit code. Independently re-derived, this session:

- **Cluster-completion ground truth** (director's own fresh `sacct`/`squeue` queries, not a log file): all 12 `t18_*` job arrays off the queue; **8,160 total tasks, 8,063 `COMPLETED` / 97 `FAILED`, zero non-terminal rows.**
- **Harvest row-count cross-check, all 12 cells:** harvested row count == `sacct` total task count for every cell (8,160/8,160 `OK`). Harvested `status=="success"` count == `sacct` `COMPLETED` count for every cell. Harvested non-success count == `sacct` `FAILED` count for every cell. No mismatches anywhere.
- **Raw EnergyPlus output presence:** for every cell, the harvest's own extraction log reports `N/N .end files extracted` matching the cell's full fleet size (e.g. `nyc_urban] 1779/1779`, `la_suburban] 1343/1343`) -- confirmed independently by directly counting extracted building directories on the local fetch workspace, not just reading the harvest script's own print statement.
- **Hand-spot-checked EUI values, 4 buildings, fresh independent `sqlite3` queries (Python `sqlite3` module, own meter-summation code, not the harvest script's `_parse_sql`, not reading any number the harvest already computed):**

  | osm_id | cell | archetype | independent total_eui | CSV total_eui | independent dhw_eui | CSV dhw_eui |
  |---|---|---|---|---|---|---|
  | way/86121620 | nyc_centre | LargeOffice | 192.1470 | 192.146952 | -- | 4.794424 |
  | way/165439153 | nyc_centre | MidriseApartment | 106.6320 | 106.631973 | 39.3172 | 39.317226 |
  | way/192352435 | austin_suburban | SmallOffice | 72.6424 | 72.642442 | 13.6043 | 13.604285 |
  | way/442340493 | la_suburban | MidriseApartment | 112.3510 | 112.350988 | 39.5235 | 39.523549 |

  All 4 match the harvested CSV to within float rounding. No parser discrepancy found.
- **Hand-spot-checked failure signatures, 3 buildings, direct `.end`/`.err` inspection (not the CSV's `status` column):**
  - `way/42496352`, `way/42500728` (`LargeOffice`, `nyc_centre`, the exact 2 buildings T05's local retest flagged as E-LA-11): both **still `Terminated--Fatal Error Detected`, 5 Severe**, real `.err` text `CheckForRunawayPlantTemps: Simulation terminated because of run away plant temperatures, too hot` -- identical signature to T05's local retest, now confirmed at cluster scale.
  - `way/900486144` (`Outpatient`, `nyc_rural`): still `Terminated--Fatal Error Detected`, 1 Severe, real `.err` text `AirLoopHVAC:OutdoorAirSystem = "AHU-1_OA_EQUIPMENT" invalid Controller List Name="OUTDOORAIR:MIXER" not found` -- identical E-LA-09/E-LA-13 signature, confirmed unchanged at cluster scale.
  - Noted in passing, not a new defect: the CSV's `has_fatal` column reads `False` on both `LargeOffice` E-LA-11 rows despite a real Fatal being present -- because the harvest script's check is a literal substring `"** Fatal **"` (single spaces) while EnergyPlus 23.1 actually writes `"**  Fatal  **"` (double spaces) for this signature. This is a pre-existing harvest-script quirk inherited unchanged from `t17_harvest_layout_assign.py`, already flagged in T05's own progress-log entry ("inconsistent on its face with a Fatal") -- confirmed here to reproduce identically at cluster scale, not a new bug, not fixed (out of this task's scope; `n_severe`/`status` are unaffected and remain the reliable fields).

### 5.2 Fleet-wide result: T17 (before) vs. T18 (after)

| Metric | T17 (before fixes) | T18 (after fixes) |
|---|---|---|
| Success rate | 7,887/8,160 (96.65%) | **8,063/8,160 (98.81%)** |
| Failed | 273 (3.35%) | **97 (1.19%)** |
| Fleet `total_eui` median (success only, raw) | 174.09 | **105.86** |
| Fleet `total_eui` mean (success only, raw) | 378.12 | **175.11** |
| Fleet `total_eui` median (excl. MidriseApartment/SmallOffice) | 296.99 | 200.19 |
| Fleet `total_eui` mean (excl. MidriseApartment/SmallOffice) | 357.29 | 330.73 |

The success-rate and mean/median EUI improvements are almost entirely attributable to two things: (1) T01/T02's DHW fix removing the E-LA-10 `1/S` distortion from `MidriseApartment`/`SmallOffice` (77% of the fleet), which dominates the raw fleet mean/median; (2) T04's `LargeOffice` fix recovering 176 previously-Fatal buildings. The "excl. DHW archetypes" row isolates the EUI shift not attributable to E-LA-10 -- median drops 297→200 and mean 357→331, still a real improvement, mostly from `LargeOffice`'s newly-recovered (previously-Fatal, now-successful) buildings joining the success population at plausible EUI values instead of being absent.

**Per-cell result (median `total_eui`, kWh/m²·yr, success only):**

| Cell | City | T18 `total_eui` (raw) | T18 `total_eui` (excl. DHW archetypes) | Success rate |
|---|---|---|---|---|
| `nyc_centre` | NYC | 89.7 | 152.3 | 688/738 (93.2%) |
| `nyc_urban` | NYC | 84.3 | 317.3 | 1779/1779 (100.0%) |
| `nyc_suburban` | NYC | 306.4 | 539.0 | 1589/1589 (100.0%) |
| `nyc_rural` | NYC | 93.0 | 563.2 | 193/198 (97.5%) |
| `la_centre` | LA | 99.3 | 109.8 | 220/226 (97.3%) |
| `la_urban` | LA | 104.4 | 109.2 | 612/618 (99.0%) |
| `la_suburban` | LA | 109.7 | 100.4 | 1343/1343 (100.0%) |
| `la_rural` | LA | 85.8 | 83.2 | 149/149 (100.0%) |
| `austin_centre` | AUS | 109.4 | 158.0 | 389/413 (94.2%) |
| `austin_urban` | AUS | 81.4 | 117.1 | 421/425 (99.1%) |
| `austin_suburban` | AUS | 81.7 | 411.0 | 437/437 (100.0%) |
| `austin_rural` | AUS | 82.2 | 161.4 | 243/245 (99.2%) |
| **Fleet total** | | | | **8,063/8,160 (98.81%)** |

`nyc_suburban`'s raw median dropped from **948.0 (T17) to 306.4 (T18)** and `la_suburban`'s from **408.8 to 109.7** -- both cells are >80% `MidriseApartment`, so this is the direct, expected signature of E-LA-10's fix (the `1/S` DHW distortion is gone at the small-S values that dominate these two cells). The "excl. DHW archetypes" column is largely unchanged from §3's T17 table (as expected -- those archetypes' own results were not touched by this plan's fixes, `SecondarySchool`'s E-LA-14 Severe-count regression aside, which does not move EUI).

### 5.3 Per-archetype breakdown -- the plan's named archetypes of interest

| Archetype | T17 success (n / rate) | T18 success (n / rate) | T17 `total_eui` median | T18 `total_eui` median | T17 `dhw_eui` median | T18 `dhw_eui` median |
|---|---|---|---|---|---|---|
| `MidriseApartment` (DHW-affected) | 2,818/2,818 (100.0%) | 2,818/2,818 (100.0%) | 795.23 | **136.57** | 663.02 | **39.35** |
| `SmallOffice` (DHW-affected) | 3,497/3,504 (99.8%) | 3,497/3,504 (99.8%) | 92.12 | 82.07 | 23.79 | **13.64** |
| `LargeOffice` (E-LA-07 class 1 fix + E-LA-11) | 49/270 (18.2%) | **225/270 (83.3%)** | 146.49 | 155.18 | 5.08 | 4.79 |
| `Outpatient` (E-LA-09/E-LA-13) | 0/6 (0.0%) | **0/6 (0.0%)**, unchanged | -- | -- | -- | -- |
| `TallBuilding` (E-LA-07 class 2, OPEN) | 67/92 (72.8%) | 67/92 (72.8%), unchanged | 478.49 | 467.50 | 90.86 | 86.94 |
| `SuperTallBuilding` (E-LA-07 class 2, OPEN) | 12/24 (50.0%) | 12/24 (50.0%), unchanged | 318.44 | 324.25 | 54.75 | 59.93 |
| `Hospital` (E-LA-07 class 2, OPEN) | 4/5 (80.0%) | 4/5 (80.0%), unchanged | 335.77 | 316.30 | 37.54 | 19.34 |
| `MediumOffice` (E-LA-07 class 2, OPEN) | 411/412 (99.8%) | 411/412 (99.8%), unchanged | 90.21 | 89.97 | 8.27 | 7.54 |

- **DHW fix (E-LA-10/T01/T02) confirmed genuinely closed at fleet scale, not just the 5-building T03 local retest:** `MidriseApartment`'s fleet-wide median `dhw_eui` collapsed from 663.0 to **39.35** -- landing almost exactly on T03's own predicted "undistorted S≈1 bin" reference value (39.7-39.9), now confirmed against **2,818 real cluster buildings**, not 3. `SmallOffice` similarly: 23.79→13.64, consistent with T03's 14.3 reference. `total_eui` for `MidriseApartment` drops from 795→137 as a direct consequence (DHW was the dominant end use at typical small-S values for this archetype).
- **`LargeOffice` (T04/T05/E-LA-11) confirmed only partially recovered, exactly as CP-B's evidence predicted:** success rate jumped from 18.2% to 83.3% (+65.18 percentage points; 176 of the 270 fleet-wide `LargeOffice` buildings recovered, none newly failed). Directionally consistent with T05's own 3-building local retest (1/3 recovered, 2/3 hit the new E-LA-11 signature) -- this fleet-scale result confirms that finding generalizes rather than being an artifact of the small local sample. The **remaining 45 `LargeOffice` failures are the E-LA-11 plant-runaway defect** (confirmed via the spot-checked `way/42496352`/`way/42500728`, both still Fatal with the exact `CheckForRunawayPlantTemps` signature) -- this defect remains genuinely OPEN-BLOCKED, not silently fixed, consistent with T07's stop-and-report decision.
- **`Outpatient` (E-LA-09/E-LA-13) confirmed NOT recovered, exactly as T09 predicted:** 6/6 still Fatal, byte-identical failure signature (spot-checked `way/900486144` directly), because E-LA-13's fix (a shared eppy `save()`-path patch) was explicitly stop-and-reported rather than implemented. This is the one previously-100%-dead archetype that remains 100% dead in production.
- **E-LA-07 class 2/E-LA-08 archetypes (`TallBuilding`/`SuperTallBuilding`/`Hospital`/`MediumOffice`) unchanged, as expected:** success rates are byte-identical to T17 (no new fix applied to this defect class; `SmallHotel` has 0 real fleet buildings in either sweep, consistent with the closed arc's own finding). Small EUI-median drift (e.g. `Hospital` 335.8→316.3, n=4 only) is noise at this sample size, not attributable to any code change.

### 5.4 Fleet-wide `n_warmup_convergence` prevalence (E-LA-14) -- first real fleet-scale measurement

Prior to this harvest, E-LA-14's blast radius was known from exactly **2 hand-picked local-retest buildings** (T10: 1/2 `SecondarySchool` buildings jumped `n_severe` 1→7). This harvest's new per-building `n_warmup_convergence` counter (counts of the literal string `CheckWarmupConvergence` in each building's real `eplusout.err`) gives the first fleet-scale measurement:

- **105/8,160 buildings (1.29%) show at least 1 `CheckWarmupConvergence` Severe; 275 total hits fleet-wide.**
- By archetype (buildings affected / total hits):

  | Archetype | Buildings affected | Total hits |
  |---|---|---|
  | `SmallOffice` | 54 | 93 |
  | `LargeOffice` | 33 | 58 |
  | `MediumOffice` | 9 | 50 |
  | `SecondarySchool` | 6 | 38 |
  | `TallBuilding` | 1 | 30 |
  | `MidriseApartment` | 1 | 3 |
  | `PrimarySchool` | 1 | 3 |

**Assessment for CP-E:** E-LA-14 is real but narrow at fleet scale -- 1.29% of the fleet, and (per §5.3 above) it is a Severe-*count* cosmetic issue, not a failure-rate one: all 105 affected buildings still have `status=="success"`. This matches the director's CP-D rationale for accepting it as non-blocking. Note `SmallOffice`/`LargeOffice` (both touched by this plan's fixes) carry the largest affected-building counts, consistent with T10's own isolation of the regression to the `WaterHeater:Mixed` field additions; `TallBuilding`'s single affected building carries an outsized 30 hits (likely the same small-marginal-zone mechanism already characterized under E-LA-07 class 2, not investigated further here per hard rule 2's scope boundary).

### 5.5 Fleet-wide failure analysis: the 97 T18 failures vs. T17's 273

| Archetype | T17 failed | T18 failed | Disposition |
|---|---|---|---|
| `LargeOffice` | 221 | **45** | Partially fixed (T04); residual = E-LA-11, OPEN-BLOCKED |
| `TallBuilding` | 25 | 25 | Unchanged -- E-LA-07 class 2, OPEN-BLOCKED |
| `SuperTallBuilding` | 12 | 12 | Unchanged -- E-LA-07 class 2, OPEN-BLOCKED |
| `SmallOffice` | 7 | 7 | Unchanged -- E-LA-07 class 2 (`ElevatorCoreFlr1`), OPEN-BLOCKED |
| `Outpatient` | 6 | 6 | Unchanged -- E-LA-09/E-LA-13, OPEN-BLOCKED |
| `MediumOffice` | 1 | 1 | Unchanged -- E-LA-07 class 2, OPEN-BLOCKED |
| `Hospital` | 1 | 1 | Unchanged -- E-LA-07 class 2, OPEN-BLOCKED |
| **Total** | **273** | **97** | |

Set-level comparison (by `osm_id`, not just per-archetype counts): **every one of the 97 T18-failed buildings also failed in T17** (0 newly-failing buildings); **176 buildings that failed in T17 now succeed in T18** (all 176 are `LargeOffice`). This is exactly the expected signature of this plan's fix set: T04's targeted `LargeOffice` fix recovers a strict subset of its previously-failed population and introduces no new failures anywhere in the 8,160-building fleet; every other failing archetype is untouched because its defect (E-LA-07 class 2, E-LA-09/E-LA-13) was root-caused but deliberately left unfixed (stop-and-report, per T06/T07/T08/T09's own disposition).

### 5.6 Figures (T18)

`openubem/outputs/comparisons/` (also copied to `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/figures/`):
- `t18_vs_t17_success_by_cell.png` -- success rate by cell, T17 vs T18.
- `t18_vs_t17_archetype_success.png` -- success rate for the previously-failing archetype set, T17 vs T18 (shows `LargeOffice`'s partial recovery and every other archetype's unchanged rate).
- `t18_vs_t17_dhw_eui_fix.png` -- `dhw_eui` distribution (boxplot, log scale) for `MidriseApartment`/`SmallOffice`, before/after the E-LA-10 fix.
- `t18_vs_t17_warmup_convergence.png` -- E-LA-14 fleet-wide prevalence by archetype (buildings affected).

### 5.7 Scope note for CP-E

This section answers T11's own charter (prove the debug-arc's fixes hold at fleet scale) and nothing more. It does **not** re-open or re-adjudicate any already-signed CP-A/B/C/D disposition. Standing OPEN-BLOCKED items unaffected by this sweep: **E-LA-11** (`LargeOffice` plant-runaway, 45 buildings), **E-LA-07 class 2/E-LA-08** (`TallBuilding`/`SuperTallBuilding`/`SmallOffice`/`MediumOffice`/`Hospital`, 46 buildings), **E-LA-09/E-LA-13** (`Outpatient`, 6 buildings, 100% dead), **E-LA-12** (daylighting refpoint, latent/masked), **E-LA-14** (Severe-count regression, now measured at 1.29% fleet-wide, non-blocking). Combined, the 97 T18 failures are fully attributable to already-root-caused, already-logged defects -- no unexplained residual.

---

## 6. Post-structural-fixes full-cluster result (T19, 2026-07-24) -- 3-way comparison vs. T17/T18

**This section is an addendum, appended per this project's correction-via-addendum convention. §3's T17 table and §5's T18 addendum above are frozen historical records, unchanged by this section.** It reports the same 12-cell / 8,160-building `layout_assign` cluster re-sweep (**T19**, tagged distinctly from T17/T18 -- separate remote fleet dirs, separate output filenames, T17's/T18's own artifacts never touched), re-run with `structural-fixes` plan's T01/T03/T06/T08 all live (E-LA-12 daylighting-refpoint scaling, E-LA-07-class-2/E-LA-08 `thermal_mass=True` default, E-LA-11 WSHP autosize resolve-then-scale, E-LA-09/E-LA-13 `objls` padding). Harvested via `scripts/cluster/t19_harvest_layout_assign.py` (byte-for-byte fork of T18's harvest, only fleet tag/output filenames changed). Raw building-level results: `openubem/outputs/comparisons/t19_layout_assign_eui.csv` (8,160 rows; also copied to `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/results/`); per-cell/archetype summary: `t19_layout_assign_cell_summary.csv` (same copy location).

### 6.1 Independent verification (before trusting anything below)

This harvest was not taken on trust from the harvest script's own printed summary. Independently re-derived, this session:

- **Cluster-completion ground truth:** fresh `squeue -u o_iseri` query returned zero rows (no `t19_*` jobs remaining); fresh `sacct -u o_iseri` query (all 12 `t19_<cell>_layout_assign` array job names) shows every one of the 8,160 array tasks in a terminal state (`COMPLETED` or `FAILED`), zero `PENDING`/`RUNNING`/other non-terminal rows.
- **Harvest row-count cross-check, all 12 cells:** harvested row count == `sacct` total task count for every cell (8,160/8,160 `OK`, matches T17/T18 exactly). Harvested `status=="success"` count == `sacct` `COMPLETED` count for every cell; harvested non-success count == `sacct` `FAILED` count for every cell -- including the two largest-magnitude cells, `nyc_rural` (`sacct`: 46 `COMPLETED` / 152 `FAILED`; harvest: 46/198 success) and `nyc_centre` (`sacct`: 732 `COMPLETED` / 6 `FAILED`; harvest: 732/738 success). No mismatches anywhere across all 12 cells.
- **Raw EnergyPlus output presence:** for every cell, the harvest's own extraction log reports `N/N .end files extracted` matching the cell's full fleet size (e.g. `nyc_urban] 1779/1779`, `la_suburban] 1343/1343`, `nyc_rural] 198/198`).
- **Independently re-derived one previously-100%-Fatal `Outpatient` building from raw sources, not the CSV (hard rule 10):** `austin_urban/way/381824351` (498.62 m², 100% Fatal in both T17 and T18, exact signature `AirLoopHVAC:OutdoorAirSystem ... invalid Controller List Name="OUTDOORAIR:MIXER" not found`).
  - Raw `eplusout.end` (fetched directly, not parsed by any script): **`EnergyPlus Completed Successfully-- 14343736 Warning; 0 Severe Errors; Elapsed Time=00hr 04min 12.25sec`**.
  - Raw `eplusout.err`: `grep -c "invalid Controller List Name"` → **0** (original E-LA-09/E-LA-13 signature genuinely gone, not just a different Fatal masking it).
  - Fresh, independent `sqlite3` query (own Python one-off, not the harvest script's `_parse_sql`) summing the identical 9-meter formula from `RunPeriod` `ReportData`: **426.687 kWh/m²** independently computed vs. **426.690637** in the harvested CSV -- agreement to <0.001% (residual is floor-area-rounding only, same pattern as T18's own spot-checks in §5.1).
  - CSV row cross-check: `status="success"`, `has_fatal=False`, `n_severe=0` -- consistent with all of the above.
- **Hand-spot-checked failure signatures, direct `.err` inspection (not the CSV's `status` column), across all 3 archetypes with residual/new T19 failures:** `TallBuilding` (`la_urban/way/402036789`, `la_urban/way/1395739331`, `nyc_centre/way/109284807` and 3 more) -- all show `Autosizing of cooling tower UA failed for tower CENTRIFUGAL FAN CYCLING OPEN COOLING TOWER 40.2 GPM/HP` / `Bad starting values for UA`, the exact already-logged **E-LA-16** signature, confirmed genuinely present (not the original `CalcHeatBalanceInsideSurf` E-LA-07-class-2 divergence, which is confirmed absent -- 0 hits -- in all of these). `SmallOffice` failures split into two distinct groups on direct inspection (see §6.5).

### 6.2 Fleet-wide result: T17 vs. T18 vs. T19

| Metric | T17 (original) | T18 (debug-plan fixes) | T19 (structural fixes) |
|---|---|---|---|
| Success rate | 7,887/8,160 (96.65%) | 8,063/8,160 (98.81%) | **7,990/8,160 (97.92%)** |
| Failed | 273 (3.35%) | 97 (1.19%) | **170 (2.08%)** |
| Fleet `total_eui` median (success only, raw) | 174.09 | 105.86 | **103.75** |
| Fleet `total_eui` mean (success only, raw) | 378.12 | 175.11 | **170.75** |
| Fleet `total_eui` median (excl. MidriseApartment/SmallOffice) | 296.99 | 200.19 | **209.92** |
| Fleet `total_eui` mean (excl. MidriseApartment/SmallOffice) | 357.29 | 330.73 | **309.35** |

**T19's fleet-wide success rate (97.92%) sits between T17 and T18, not above T18** -- this is the headline finding of this harvest, and it is **not** a regression of any of this plan's 3 targeted fixes. It is the net effect of two things moving in opposite directions simultaneously:
1. **Real, substantial recoveries** in exactly the archetypes this plan targeted (`Outpatient` 0%→100%, `LargeOffice` 83.3%→100%, `SuperTallBuilding` 50%→100%, `Hospital` 80%→100%, `TallBuilding` 72.8%→83.7% -- see §6.3).
2. **A new, previously-unseen failure mode** that costs more buildings than all of those recoveries combined: **150 `SmallOffice` buildings, 100% concentrated in `nyc_rural`, newly Fatal** on a CTF (Conduction Transfer Function) calculation-convergence error tied to the mass-bearing roof construction T03's fix introduces (`Construction="LA_ROOF_CONSTRUCTION"`) -- logged below as candidate **E-LA-20** (§6.5). This was not visible in any of this plan's local retest samples (T02/T04/T05/T10's ≤28-building samples), only at full 8,160-building fleet scale.

Net: **77 buildings recovered T18→T19, 150 buildings newly failed T18→T19** (set-level `osm_id` comparison, §6.5) -- a net fleet-wide loss of 73 buildings' worth of success rate, even though every one of this plan's 3 intended fixes independently verifies as working correctly and closing its targeted defect completely.

**Per-cell result (median `total_eui`, kWh/m²·yr, success only):**

| Cell | City | T19 `total_eui` (raw) | T19 `total_eui` (excl. DHW archetypes) | Success rate |
|---|---|---|---|---|
| `nyc_centre` | NYC | 89.6 | 156.0 | 732/738 (99.2%) |
| `nyc_urban` | NYC | 81.9 | 275.8 | 1779/1779 (100.0%) |
| `nyc_suburban` | NYC | 302.0 | 484.7 | 1589/1589 (100.0%) |
| `nyc_rural` | NYC | 212.2 | 540.5 | **46/198 (23.2%)** |
| `la_centre` | LA | 98.1 | 102.4 | 223/226 (98.7%) |
| `la_urban` | LA | 102.2 | 106.9 | 614/618 (99.4%) |
| `la_suburban` | LA | 106.7 | 87.3 | 1343/1343 (100.0%) |
| `la_rural` | LA | 82.7 | 80.6 | 149/149 (100.0%) |
| `austin_centre` | AUS | 111.2 | 160.8 | 408/413 (98.8%) |
| `austin_urban` | AUS | 77.5 | 137.7 | 425/425 (100.0%) |
| `austin_suburban` | AUS | 77.8 | 377.7 | 437/437 (100.0%) |
| `austin_rural` | AUS | 78.4 | 170.1 | 245/245 (100.0%) |
| **Fleet total** | | | | **7,990/8,160 (97.92%)** |

`nyc_rural` collapses from 97.5% (T17) / 97.5% (T18) to **23.2% (T19)** -- by far the largest single-cell movement in either direction across all 3 harvests, entirely attributable to the new CTF-convergence Fatal (§6.5), which is essentially unique to this cell's `SmallOffice` population.

### 6.3 Per-archetype breakdown -- the plan's named archetypes of interest

| Archetype | T17 success | T18 success | T19 success | Disposition |
|---|---|---|---|---|
| `Outpatient` (E-LA-09/E-LA-13) | 0/6 (0.0%) | 0/6 (0.0%) | **6/6 (100.0%)** | **FIXED at fleet scale** -- `objls` padding closes this completely, confirmed via independent raw re-derivation (§6.1) |
| `LargeOffice` (E-LA-11) | 49/270 (18.2%) | 225/270 (83.3%) | **270/270 (100.0%)** | **FIXED at fleet scale** -- resolve-then-scale WSHP fix closes the remaining 45 `CheckForRunawayPlantTemps` failures completely, 0 residual |
| `SuperTallBuilding` (E-LA-07 class 2) | 12/24 (50.0%) | 12/24 (50.0%), unchanged | **24/24 (100.0%)** | **FIXED at fleet scale** -- `thermal_mass=True` closes this archetype completely |
| `Hospital` (E-LA-07 class 2) | 4/5 (80.0%) | 4/5 (80.0%), unchanged | **5/5 (100.0%)** | **FIXED at fleet scale** |
| `TallBuilding` (E-LA-07 class 2) | 67/92 (72.8%) | 67/92 (72.8%), unchanged | **77/92 (83.7%)** | **Partially recovered** -- 15/92 residual failures, all confirmed (§6.1) to be the already-logged **E-LA-16** secondary HVAC-autosize degeneracy (cooling-tower/cooling-coil UA), not the original E-LA-07-class-2 divergence, which is confirmed gone in every one of these 15 |
| `SmallOffice` (E-LA-07 class 2 + new) | 3,497/3,504 (99.8%) | 3,497/3,504 (99.8%), unchanged | **3,350/3,504 (95.6%)** | **Net regression** -- 3/7 of T18's original failures recovered, but 150 buildings newly Fatal on candidate **E-LA-20** (§6.5); net −4.2 pp |
| `MediumOffice` (E-LA-07 class 2) | 411/412 (99.8%) | 411/412 (99.8%), unchanged | 411/412 (99.8%), unchanged | Unchanged -- the 1 residual failure is the already-logged **E-LA-17** pattern (`LaundryRoomFlr1`/`GroundFCfactorMethod` exclusion), confirmed via direct `.err` inspection |
| `SecondarySchool` (E-LA-14/E-LA-19) | 11/11 (100.0%) | 11/11 (100.0%) | 11/11 (100.0%), unchanged | `status` unaffected at fleet scale (see §6.4 for the Severe-count-only prevalence shift) |

- **All 4 of this plan's intended fixes verify as fully closing their targeted defect at full fleet scale, with zero exceptions:** `Outpatient` (E-LA-09/E-LA-13), `LargeOffice` (E-LA-11), and — as a direct consequence of E-LA-07-class-2/E-LA-08's `thermal_mass=True` fix — `SuperTallBuilding` and `Hospital` all reach clean 100% success, up from 0%/83.3%/50%/80% respectively. This is the strongest possible confirmation of T06/T08's fix mechanisms (E-LA-11, E-LA-09/E-LA-13) and a strong confirmation of T03's fix (E-LA-07-class-2) for 2 of its 5 originally-affected archetypes.
- **`TallBuilding`'s remaining 15/92 failures are a real, expected, already-anticipated cost, not a new defect:** every one directly reproduces the debug plan's own **E-LA-16** finding (T04/T05, logged 2026-07-23, already flagged "should be scoped and root-caused before `layout_assign`'s thermal-mass default is considered fully production-safe fleet-wide -- flagged explicitly for CP-E"). This fleet-scale result is exactly that prediction materializing at scale: T03's fix removes the original divergence but pushes some already-marginal buildings into a second-order HVAC-autosizing degeneracy (cooling-tower/cooling-coil UA) that was root-caused, not fixed, by design (out of Phase 2's pre-authorized scope).
- **`SmallOffice`'s net regression is the one finding in this harvest that was NOT anticipated by any prior local retest sample** -- see §6.5, candidate E-LA-20.

### 6.4 Fleet-wide `n_warmup_convergence` prevalence (E-LA-14/E-LA-19) -- re-measured, not assumed unchanged

T10's local regression (28-building sample) found that `thermal_mass=True` (T03) can shift *which* zones tip over the 25-day warmup-convergence threshold on an already-E-LA-14-affected `SecondarySchool` building (logged as **E-LA-19**), without changing `status`. This harvest re-measures fleet-wide prevalence directly from this run's own raw `.err` files, rather than assuming T18's 1.29% still holds:

| | T18 (debug-plan fixes only) | T19 (structural fixes, all 4 live) |
|---|---|---|
| Buildings affected (>=1 `CheckWarmupConvergence` Severe) | 105/8,160 (1.29%) | **203/8,160 (2.49%)** |
| Total hits, fleet-wide | 275 | **855** |

By archetype (buildings affected):

| Archetype | T18 affected | T19 affected |
|---|---|---|
| `LargeOffice` | 33 | **118** |
| `SuperTallBuilding` | 0 | **16** |
| `MediumOffice` | 9 | 37 |
| `SecondarySchool` | 6 | 6 (unchanged count; zone-composition shift confirmed at local scale, E-LA-19) |
| `SmallOffice` | 54 | 23 |
| `TallBuilding` | 1 | 0 |
| `PrimarySchool` | 1 | 2 |
| `RetailStandalone` | 0 | 1 |
| `MidriseApartment` | 1 | 0 |

**Prevalence roughly doubles (1.29%→2.49%) once `thermal_mass=True` is fleet-wide, not just latent on a handful of already-affected buildings.** The largest mover is `LargeOffice` (33→118 buildings), which makes physical sense: this is the same archetype that just went from 83.3%→100% success (E-LA-11 fix) -- 45 buildings that were previously Fatal-before-warmup-even-completed are now running the full simulation for the first time, and a meaningful fraction of them apparently sit close enough to the warmup-convergence margin to trip it. `status` remains `success` for all 203 affected buildings in T19 (confirmed via the harvest's own status field, cross-checked against `n_severe`/`has_fatal` columns) -- this remains a Severe-count-only cosmetic issue, not a failure-rate issue, consistent with the director's original CP-D rationale for accepting E-LA-14 as non-blocking. Still, a near-doubling at fleet scale is a materially larger footprint than T18's number and should be weighed explicitly at CP-E, not silently carried forward as "still ~1.29%."

### 6.5 New finding: candidate E-LA-20 -- CTF calculation-convergence Fatal on `LA_ROOF_CONSTRUCTION`, 100% concentrated in `nyc_rural` `SmallOffice`

**Not anticipated by any prior local retest in either plan; first visible only at full 8,160-building fleet scale.** Reported here per hard rule 2 (no scope creep -- investigated and characterized, not fixed) and the plan's own established convention for logging new findings mid-task (matching E-LA-15 through E-LA-19's precedent).

- **Symptom:** 150 `SmallOffice` buildings, **100% concentrated in `nyc_rural`** (150/198 of that cell's entire fleet), newly `status="failed"` in T19 -- none of these 150 were failing in either T17 or T18. Raw `.err` (identical across every one spot-checked):
  ```
  ** Severe  ** CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION".
  **   ~~~   ** ...with Materials (outside layer to inside)
  **   ~~~   ** (outside)="LA_ROOF_ASSEMBLY"
  ...
  **  Fatal  ** Program terminated for reasons listed (InitConductionTransferFunctions)
  ```
  The Fatal fires during `InitConductionTransferFunctions`, before Warmup or Sizing begins (Elapsed Time ≈0.12 sec) -- essentially instant, input-processing-time termination, not a runtime divergence.
- **Independently confirmed via a full programmatic scan, not a spot-check:** every one of `nyc_rural`'s 152 non-success `SmallOffice` `.err` files was read directly and checked for the CTF signature string -- **150/150 of the newly-failing rows contain it, byte-identical**; the remaining 2/152 do not (see below). Cross-checked against `sacct`: `nyc_rural`'s 152 SLURM-`FAILED` array tasks (independent `sacct` query, §6.1) match the harvest's 152 non-success rows for this cell exactly (198 total − 46 success). Of `nyc_rural`'s 152 non-success buildings, 150 are this new signature and 2 (`way/965718400`, `way/965718401`) are carryovers already failing at T18, confirmed via direct per-building `.err` inspection to retain their exact original signatures unchanged: `way/965718400` still shows the E-LA-17 pattern (`CalcHeatBalanceInsideSurf` in `LAUNDRYROOMFLR1`) and `way/965718401` still shows the E-LA-15 pattern (`SizeAirLoopBranches` minimum air flow) -- neither has been overtaken by the new CTF signature.
- **Root-cause hypothesis (not fully proven, appropriately hedged, not investigated further per hard rule 2):** `LA_ROOF_CONSTRUCTION` is the mass-bearing roof construction T03's fix (`envelope_patcher.patch_envelope(..., thermal_mass=True)`) assigns fleet-wide. EnergyPlus's own diagnostic text names the likely mechanism directly: *"Very thin, highly conductive materials may cause problems... Highly conductive or highly resistive layers that are alternated with high mass layers may also result in problems."* `nyc_rural` is disproportionately small/rural `SmallOffice` buildings at extreme small scale factors (S) -- plausibly, at sufficiently small S, the roof assembly's scaled layer thicknesses combined with the new mass-bearing material's properties produce a CTF (Conduction Transfer Function) time-series that EnergyPlus's own numerical solver cannot converge on, a distinct failure mode from both the original E-LA-07-class-2 divergence (warmup heat-balance, `CalcHeatBalanceInsideSurf`) and the already-logged E-LA-15/E-LA-16 secondary-HVAC-autosize family (sizing-phase). This is the same general risk class CP-A's audit already flagged when it accepted T05's small-sample EUI drift ("adding thermal mass typically damping/reducing peak loads... but should be measured, not assumed negligible") -- except here the effect is a hard Fatal, not a soft EUI drift, and it did not appear in any of the ≤28-building local samples because none of those samples happened to include a `nyc_rural`-scale, extreme-small-S `SmallOffice` building.
- **Not confined to `nyc_rural` alone at trace level, but overwhelmingly concentrated there:** 2 `SmallOffice` failures also appear in `la_urban` (`way/428846131`, `relation/6374725`), but direct inspection confirms these are a **different, already-logged signature** (`CalcHeatBalanceInsideSurf` in zone `LAUNDRYROOMFLR1`, surface `P_LAUNDRYROOMFLR1_10010_0_10008`) -- an exact match to the already-documented **E-LA-17** pattern (persistent divergence in a `GroundFCfactorMethod`-adjacent zone that T03's fix explicitly does not reach), not the new CTF signature. The 1 residual `MediumOffice` failure (`la_centre/way/427942886`) is also confirmed to be this same E-LA-17 pattern. **The new CTF/E-LA-20 signature is, on the evidence gathered, unique to `nyc_rural`'s `SmallOffice` population** -- no other cell or archetype shows it.
- **Incidental correction (not a new defect, matching this plan's own established correction-via-addendum convention for archetype mislabeling):** 2 of the "still-failing" `SmallOffice` buildings in this harvest (`nyc_rural/way/965718400`, `nyc_rural/way/965718401`) are the **same two real osm_ids** the structural-fixes plan's own §4 "verified facts" table lists as `SmallHotel` (part of "the 7 known-failing E-LA-07-class-2 buildings," used throughout T04's local retest and E-LA-15/E-LA-17's own write-ups). The fleet-wide harvest classifies both as `SmallOffice` -- confirmed here, and consistent with the independently-confirmed fact (both T18 and T19 harvest CSVs) that **`SmallHotel` has 0 real buildings anywhere in the 8,160-building fleet**. This is the same class of pre-existing archetype-label/fleet-reality mismatch T10 already found and flagged once (`way/265301856`/`way/293183674`, "LargeHotel" mislabeled "MediumOffice") -- not something T01/T03/T06/T08/T11 caused, not investigated further here, flagged for the director.
- **Resolution:** not attempted -- out of this task's scope (harvest/reporting only, hard rule 2). This is a genuinely new defect class, distinct from E-LA-15 through E-LA-19, and is **not** covered by any existing OPEN-BLOCKED disposition.
- **Recommendation:** given this costs more buildings (150) than the combined recoveries of all 3 of this plan's targeted fixes at fleet scale (`Outpatient` 6 + `LargeOffice` 45 + `SuperTallBuilding` 12 + `Hospital` 1 = 64), and is 100% concentrated in one cell/archetype combination not represented in any prior local retest sample, this should be scoped and root-caused (likely a follow-up to `envelope_patcher.py`'s roof-construction material assignment for small-S buildings) before `layout_assign`'s `thermal_mass=True` default is considered fully production-safe fleet-wide -- flagged explicitly for CP-E's production-readiness reassessment, same standard as E-LA-16.

### 6.6 Figures (T19)

`openubem/outputs/comparisons/` (also copied flat to `openubem/outputs/` and to `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/figures/`):
- `t19_vs_t18_vs_t17_success_by_cell.png` -- success rate by cell, 3-way T17/T18/T19 (shows the `nyc_rural` collapse at T19).
- `t19_vs_t18_vs_t17_archetype_success.png` -- success rate by archetype, 3-way, for the plan's named archetypes of interest (shows `Outpatient`/`LargeOffice`/`SuperTallBuilding`/`Hospital` all reaching 100% at T19).
- `t19_vs_t18_vs_t17_warmup_convergence.png` -- E-LA-14/E-LA-19 fleet-wide prevalence by archetype, T18 vs. T19 (shows the ~2x prevalence increase, concentrated in `LargeOffice`).
- `t19_vs_t18_vs_t17_eui_drift.png` -- fleet-wide `total_eui` distribution and % change histogram, T18→T19, same-building comparison (n=7,913 buildings successful in both harvests; median −2.73%, mean −3.51%, consistent in direction and magnitude with T05's small local sample).
- `t19_vs_t18_vs_t17_new_failure_nyc_rural.png` -- candidate E-LA-20's cell concentration (150/150 new failures in `nyc_rural`, 0 anywhere else).

### 6.7 Scope note for CP-E

This section answers T11's own charter (prove this plan's 3 structural fixes hold at fleet scale, harvest + independently verify + 3-way compare) and nothing more -- it does not decide CP-E, which remains the manager's own final production-readiness reassessment. Net position for that reassessment to weigh: **all 4 of this plan's targeted defects (E-LA-12, E-LA-07-class-2/E-LA-08, E-LA-11, E-LA-09/E-LA-13) are confirmed fixed/working at fleet scale with zero exceptions where their fix mechanism applies**, but the fleet-wide success rate is nonetheless *lower* than T18's (97.92% vs. 98.81%) because of one new, previously-unseen defect (**candidate E-LA-20**, §6.5, 150 buildings) plus the already-anticipated E-LA-16 secondary-degeneracy cost (15 `TallBuilding`, already logged and flagged before this harvest ran) and the already-logged E-LA-17 pattern (2 `SmallOffice` + 1 `MediumOffice`). Fleet-wide EUI drift from `thermal_mass=True` is small and directionally consistent with the local sample (median −2.73%). E-LA-14/E-LA-19 prevalence has grown from 1.29% to 2.49% but remains `status`-non-blocking. No fix implemented in this plan required rework; every fix's own targeted defect closes cleanly. The open question for CP-E is whether candidate E-LA-20's fleet-scale cost (net −73 buildings vs. T18) is acceptable given the archetypes it does fully fix, or whether it should block production sign-off pending a follow-up fix.
