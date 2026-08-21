# MEASUREMENT — OPEN-61 fleet restatement, 2026-08-22

**The adopted published fleet figure remains 153.8231 kWh/m² pooled over n = 8,153, unchanged.
This document proposes no replacement for it.** It produces a CANDIDATE restated figure, derived
from a different population, for CP-2's adoption question only. Nothing here is adopted by writing
it down.

**Source and method.** `scripts/analysis/open61_fleet_restatement_2026-08-22.py`, arithmetic only
over `openubem/outputs/comparisons/open61_census_fleet.csv`. No simulation, no `.sql` reads, no
corpus walk. Output: `openubem/outputs/comparisons/open61_fleet_restatement_2026-08-22.csv`.

⚠️ **152.3011 and 153.8231 are different populations and must never be differenced.** 152.3011 is
the census rebuild's pooled "before" figure over n = 8,144 (this document's population). 153.8231
is run 4's adopted figure over a different n = 8,153 population. Any apparent gap between them is
not a measurement of anything and is not reported here.

## Gates (pre-registered, plan §7 T03)

- **C4** — recomputed "before" pooled figure must reproduce 152.3011 kWh/m² within 0.001.
  **Result: 152.3011 kWh/m², |diff| = 0.000038. PASS.**
- **C5** — Σ`dh_total_kwh` must equal Σ`dh_water_systems_gj` × 277.7778 within 0.01 %.
  **Result: 470,831,194.4444 vs 470,831,194.4444, relative diff = 0.000000 %. PASS.**

Both gates pass; nothing was adjusted to make them fit.

## Fleet-level candidate

Over n = 8,144 rows (F7's population — every `ok` census row carrying both
`parsed_total_eui_kwh_m2` and `dh_total_kwh`), weighted by `parsed_floor_area_m2`:

| | pooled EUI (kWh/m²) | n |
|---|---|---|
| before | 152.3011 | 8,144 |
| after (candidate) | 171.7718 | 8,144 |
| delta | **+19.4707 (+12.78 %)** | |

This reproduces F7 exactly.

## Per-cell split (12 cells, sorted by absolute change)

| cell | n | before | after | delta |
|---|---|---|---|---|
| nyc_centre | 730 | 163.1933 | 188.9445 | +25.7512 |
| la_suburban | 1,343 | 108.4214 | 132.4586 | +24.0372 |
| nyc_suburban | 1,589 | 188.6648 | 211.9806 | +23.3158 |
| austin_centre | 413 | 158.1577 | 179.1851 | +21.0274 |
| la_urban | 617 | 130.5917 | 147.8671 | +17.2754 |
| nyc_rural | 198 | 233.6318 | 245.3010 | +11.6691 |
| la_centre | 225 | 129.0365 | 139.5733 | +10.5367 |
| nyc_urban | 1,779 | 148.1909 | 157.6411 | +9.4502 |
| austin_suburban | 437 | 159.0195 | 164.4821 | +5.4626 |
| austin_rural | 245 | 154.4247 | 159.0830 | +4.6583 |
| austin_urban | 425 | 173.5960 | 176.8590 | +3.2629 |
| la_rural | 143 | 122.9102 | 125.2783 | +2.3681 |

## Per-archetype split (sorted by absolute change)

| archetype | n | before | after | delta |
|---|---|---|---|---|
| QuickServiceRestaurant | 50 | 1469.7594 | 1542.3167 | +72.5573 |
| FullServiceRestaurant | 32 | 1077.8720 | 1138.8845 | +61.0125 |
| LargeHotel | 26 | 398.6952 | 447.8880 | +49.1928 |
| TallBuilding | 92 | 175.0431 | 213.3128 | +38.2697 |
| SuperTallBuilding | 24 | 151.1619 | 187.1749 | +36.0130 |
| SmallHotel | 8 | 121.0017 | 156.1269 | +35.1252 |
| MidriseApartment | 2,818 | 106.0622 | 137.8263 | +31.7641 |
| HighriseApartment | 32 | 106.0698 | 127.2340 | +21.1642 |
| SecondarySchool | 10 | 241.0240 | 259.8278 | +18.8038 |
| Hospital | 5 | 354.4701 | 360.9468 | +6.4767 |
| Outpatient | 6 | 202.5122 | 208.3067 | +5.7945 |
| PrimarySchool | 2 | 193.6555 | 197.6408 | +3.9853 |
| MediumOffice | 391 | 163.7880 | 166.4406 | +2.6527 |
| RetailStandalone | 140 | 155.7823 | 158.3938 | +2.6115 |
| SuperMarket | 5 | 323.1077 | 325.6723 | +2.5646 |
| OpenUBEMUnknown | 650 | 107.2170 | 109.5724 | +2.3555 |
| LargeOffice | 257 | 160.9662 | 162.7523 | +1.7861 |
| Courthouse | 68 | 126.3786 | 128.1646 | +1.7860 |
| SmallOffice | 3,497 | 114.2145 | 115.5166 | +1.3021 |
| Warehouse | 31 | 19.1983 | 19.7151 | +0.5168 |

Note: per-m² deltas are largest, in relative terms, on the two restaurant archetypes and the
tall-class buildings, but by building count the fleet-dominant classes (SmallOffice,
MidriseApartment) carry the bulk of the total energy shift.

## Tall class isolated (F6's 116 buildings — SuperTallBuilding 24 + TallBuilding 92)

| | n | before | after | delta |
|---|---|---|---|---|
| tall class | 116 | 162.2534 | 199.3145 | +37.0611 |
| excluding tall class | 8,028 | 146.4398 | 155.5510 | **+9.1111** |

The tall class carries **70.5 %** of Σ`dh_total_kwh` (matches F6). Excluding those 116 buildings
entirely, the remaining 8,028 still move by +9.1111 kWh/m² — the 29.5 % of the term that sits
outside the tall class is real and does not vanish when the tall class is set aside.

## Building-level distribution of the change (n = 8,144)

| statistic | value (kWh/m²) |
|---|---|
| median | 2.4691 |
| IQR | [1.3970, 32.2354] (width 30.8385) |
| p90 | 37.2753 |
| max | 89.1207 |
| buildings moving by exactly 0.0 | **0 / 8,144** |

No building in this population moves by exactly 0.0. This is consistent with T02's finding that
the sampled corpus population's minimum `dh_total_gj` is 0.06 GJ (≈16.67 kWh) — a floor above
zero, not a zero — so every one of the 8,144 buildings carries at least some district heating in
this population. The median move (2.4691) sits far below the mean move (19.4707), and the IQR
gap between Q1 (1.3970) and Q3 (32.2354) is itself evidence of the same bimodality F6 already
established: most buildings move a little, a concentrated minority move a lot.

## Artifacts

- `scripts/analysis/open61_fleet_restatement_2026-08-22.py`
- `openubem/outputs/comparisons/open61_fleet_restatement_2026-08-22.csv`
