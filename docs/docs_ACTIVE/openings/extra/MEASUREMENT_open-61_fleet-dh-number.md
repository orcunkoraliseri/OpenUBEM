# MEASUREMENT — OPEN-61 T04: the fleet district-heating number

**Date:** 2026-08-20
**Input:** `openubem/outputs/comparisons/open61_census_fleet.csv` (8,160 rows, 41 columns)
**Script:** `scripts/analysis/open61_fleet_dh_number_2026-08-20.py`
**Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open61-census-open03-storeys-2026-08-20.md`, T04 (lines 183–206)

This document reports a measurement only. Per the plan's hard prohibition, it does **not** produce a
corrected fleet EUI and does not state what the adopted 153.8 kWh/m² figure should become.

## A. Population accounting

| status | n | meaning |
|---|---|---|
| `ok` | 8,152 | simulated and harvested |
| `not_simulated_upstream_excluded_from_census_population` | 7 | never simulated upstream |
| `failed_energyplus_oom_crash_no_fatal_no_end` | 1 | `nyc_centre way/266170763`, 43-storey LargeHotel |
| **TOTAL** | **8,160** | |

- Total rows: **8,160**.
- `status != 'ok'`: **8** (7 `not_simulated_upstream_...` + 1 `failed_energyplus_oom_...`), matching the plan's expectation.
- Of the 8,152 `ok` rows, **8** have a null/empty `dh_total_kwh` (the six `failed_zone_mismatch` rows plus the two named anomalies in §I) and are excluded.
- **Analysable population: 8,144.** This matches the plan's pre-registered expectation exactly — no discrepancy, script did not stop.

## B. The headline

Pooled over the 8,144-building population:

- `sum(dh_total_kwh)` = 470,831,194.4 kWh
- `sum(parsed_floor_area_m2)` = 24,181,536.1 m²
- **HEADLINE = sum(dh_total_kwh) / sum(parsed_floor_area_m2) = 19.4707 kWh/m²** (n = 8,144)

This is the pooled statistic (`scripts/analysis/open61_fleet_dh_number_2026-08-20.py:49-51`) — total
unreported DH energy divided by total floor area — not a mean of per-building or per-cell ratios, per
the plan's instruction (T04 "How").

For reference only, **not the headline**: the mean of the per-building ratio is 14.3113 kWh/m², the
median is 2.4691 kWh/m² — both far below the pooled figure, because the distribution is dominated by
a small number of very large, DH-intensive buildings (see `TallBuilding`/`SuperTallBuilding` in §D).
This gap between pooled and per-building-mean/median is itself informative: it shows the fleet total
is concentrated in a minority of buildings, not spread evenly.

## C. Per-cell (12 numbers)

| cell | n | pooled kWh/m² | total kWh |
|---|---:|---:|---:|
| nyc_urban | 1,779 | 9.4502 | 11,638,566.7 |
| nyc_suburban | 1,589 | 23.3158 | 4,246,861.1 |
| la_suburban | 1,343 | 24.0372 | 14,262,777.8 |
| nyc_centre | 730 | 25.7512 | 258,504,275.0 |
| la_urban | 617 | 17.2754 | 50,512,591.7 |
| austin_suburban | 437 | 5.4626 | 1,520,452.8 |
| austin_urban | 425 | 3.2629 | 3,609,772.2 |
| austin_centre | 413 | 21.0274 | 91,624,288.9 |
| austin_rural | 245 | 4.6583 | 721,772.2 |
| la_centre | 225 | 10.5367 | 33,396,208.3 |
| nyc_rural | 198 | 11.6691 | 563,419.4 |
| la_rural | 143 | 2.3681 | 230,208.3 |

n sums to 8,144. `nyc_centre` alone carries 258.5M of the 470.8M kWh fleet total (55%) despite being
only 730 of 8,144 buildings (9%) — this cell holds the OOM LargeHotel exclusion and the
`failed_zone_mismatch` exclusions (5 of 6 were `nyc_centre` LargeHotels, per T03), and is also home to
the tall/super-tall archetypes.

## D. Per-archetype (sorted by n)

| archetype_id | n | pooled kWh/m² | total kWh |
|---|---:|---:|---:|
| SmallOffice | 3,497 | 1.3021 | 2,068,447.2 |
| MidriseApartment | 2,818 | 31.7641 | 69,950,133.3 |
| OpenUBEMUnknown | 650 | 2.3555 | 2,050,800.0 |
| MediumOffice | 391 | 2.6527 | 4,651,191.7 |
| LargeOffice | 257 | 1.7861 | 8,845,741.7 |
| RetailStandalone | 140 | 2.6115 | 1,267,963.9 |
| TallBuilding | 92 | 38.2697 | 159,306,433.3 |
| Courthouse | 68 | 1.7860 | 2,199,277.8 |
| QuickServiceRestaurant | 50 | 72.5573 | 1,452,094.4 |
| FullServiceRestaurant | 32 | 61.0125 | 908,769.4 |
| HighriseApartment | 32 | 21.1642 | 29,890,777.8 |
| Warehouse | 31 | 0.5168 | 31,702.8 |
| LargeHotel | 26 | 49.1928 | 11,633,019.4 |
| SuperTallBuilding | 24 | 36.0130 | 172,864,555.6 |
| SecondarySchool | 10 | 18.8038 | 1,666,827.8 |
| SmallHotel | 8 | 35.1252 | 369,833.3 |
| Outpatient | 6 | 5.7945 | 323,261.1 |
| Hospital | 5 | 6.4767 | 1,210,436.1 |
| SuperMarket | 5 | 2.5646 | 89,319.4 |
| PrimarySchool | 2 | 3.9853 | 50,608.3 |

n sums to 8,144. Note the two rarest-but-largest-per-building archetypes, `TallBuilding` (92
buildings, 159.3M kWh) and `SuperTallBuilding` (24 buildings, 172.9M kWh), together account for
70.6% of the fleet DH total from 1.4% of the population.

## C5 — comparison against the prior estimates (8.7 / 17.2 / 20.2 kWh/m²)

**VERDICT: the headline (19.4707 kWh/m²) lands INSIDE the 8.7–20.2 band.**

- vs. F5 low (8.7): +10.7707 kWh/m² (+123.80%)
- vs. F5 mid (17.2): +2.2707 kWh/m² (+13.20%)
- vs. F5 high (20.2): −0.7293 kWh/m² (−3.61%)

The measured figure sits close to the top of the prior band, 3.61% below its high end and 13.2%
above its midpoint.

## C6 — the ratio statistic (DH ÷ DHW end-use)

🔴 **This section was rewritten by the director, 2026-08-20. The executor answered C6 with the wrong
denominator and reported the verdict backwards.** The executor computed DH ÷ *total site energy* and
concluded NOT REPRESENTATIVE. The pre-registered ratio is **DH ÷ the DHW end-use** — the plan's own
fact F5 defines the estimate as "dh ÷ dhw_eui median 0.714, IQR 0.362–0.840"
(`PLAN_open61-census-open03-storeys-2026-08-20.md:101`). The executor's claim that "the denominator is
the same construction used for the pilot's C6 statistic" is false. Re-derived on the correct
denominator, the answer reverses.

Per building: `dh_total_kwh / (parsed_dhw_eui_kwh_m2 * parsed_floor_area_m2)`, n = **8,144**
(0 excluded — no building has a zero DHW end-use).

| statistic | fleet, n=8,144 | 60-building pilot | 200-building pilot |
|---|---|---|---|
| Q1 | **0.3117** | 0.362 | 0.310 |
| median | **0.6503** | 0.714 | 0.644 |
| Q3 | **0.8642** | 0.840 | 0.935 |
| min / max | 0.0153 / 3.2571 | — | — |

**VERDICT: the small sample was representative.** All three distributions sit on top of one another;
the 60-building median is about 10 % high and its Q1 about 16 % high, which for a 60-of-8,160 sample
is a good result. The 200-building pilot (median 0.644, `…:498`) is closer still — it brackets the
fleet median from below where the 60 bracketed it from above.

**But the estimator built on that ratio was structurally biased low, and this is the finding that
matters.** The per-building **median** ratio is 0.6503; the **pooled** ratio (Σ dh ÷ Σ dhw) is
**0.9382** — 44 % higher. Large buildings carry a much higher DH-to-DHW ratio than the median
building, so applying a median per-building ratio to a fleet-pooled quantity understates the result.
Reconstructing F5's own arithmetic against the fleet's measured pooled DHW of 20.75 kWh/m²:

| F5 input | reconstructed estimate | measured |
|---|---|---|
| ratio 0.362 (IQR floor) | 7.51 kWh/m² | |
| ratio 0.714 (median) | 14.82 kWh/m² | |
| ratio 0.840 (ceiling) | 17.43 kWh/m² | **19.47** |

The measurement lands **above F5's reconstructed ceiling**, not inside it. F5's published band
(8.7 / 17.2 / 20.2) only contains the answer because its DHW base differed from the fleet's; the
method itself, applied to the fleet's own DHW, could not have reached 19.47 at any point in its IQR.
**The sampling was fine; the median-ratio-applied-pooled step was not.**

## C6b — concentration: where the 470.8 GWh actually is *(director, not in the plan's control set)*

The pooled headline reads as if 19.47 kWh/m² were missing from every building. It is not.

| archetype | n | pooled kWh/m² | share of fleet DH |
|---|---|---|---|
| SuperTallBuilding | 24 | 36.01 | **36.7 %** |
| TallBuilding | 92 | 38.27 | **33.8 %** |
| MidriseApartment | 2,818 | 31.76 | 14.9 % |
| HighriseApartment | 32 | 21.16 | 6.3 % |
| LargeHotel | 26 | 49.19 | 2.5 % |
| LargeOffice | 257 | 1.79 | 1.9 % |
| MediumOffice | 391 | 2.65 | 1.0 % |
| Courthouse | 68 | 1.79 | 0.5 % |

**116 buildings — 1.4 % of the population — carry 70.5 % of the fleet's district heating.** Four
archetypes carry 91.8 %. Everything office-, retail- or shop-like sits at 1.3–2.7 kWh/m², i.e. near
zero. The DH term in this fleet is a **tall-residential phenomenon**, not a fleet-wide offset, and any
decision taken on the 19.47 figure is really a decision about roughly 3,000 residential buildings.

## C7 — MidriseApartment vs the fleet

- `MidriseApartment` n = 2,818 (34.6% of the 8,144 analysable population — the largest archetype)
- `MidriseApartment` pooled: **31.7641 kWh/m²**
- Fleet pooled: **19.4707 kWh/m²**
- Difference: **+12.2934 kWh/m²** — `MidriseApartment` runs 63% above the fleet headline.

Despite being over a third of the population by building count, `MidriseApartment`'s 69.95M kWh is
only 14.9% of the fleet's 470.8M kWh DH total — a much smaller share of energy than of building
count, because its per-building intensity (31.8 kWh/m²), while above the fleet average, is far below
the tall/super-tall archetypes that dominate the total.

## H. Sensitivity — floor-area column choice

Recomputed the headline using `recorded_floor_area_m2` in place of `parsed_floor_area_m2`, restricted
to the 8,144 rows where both columns are present and `recorded_floor_area_m2 > 0` (all 8,144 qualify):

- Headline, `parsed_floor_area_m2`: 19.4707 kWh/m²
- Headline, `recorded_floor_area_m2`: 19.4708 kWh/m²
- Difference: **+0.0001 kWh/m² (+0.00%)**

The headline is insensitive to which floor-area column is used — the two columns agree closely
across the fleet.

## I. Named anomalies from T03

- **`la_rural way/472961047` (Warehouse):** `status=ok`, `parsed_parse_status=success`,
  `dh_total_kwh` is null, `c1_diff_kwh_m2 = -9.71`, `parsed_floor_area_m2 = 1,686.6`. Parsed
  successfully yet produced no DH term.
- **`la_centre way/319507579` (SecondarySchool):** `status=ok`, `parsed_parse_status=success`,
  `dh_total_kwh` is null, `c1_diff_kwh_m2 = -116.59`, `parsed_floor_area_m2 = 30,910.4`. Parsed
  successfully yet produced no DH term; the c1 diff is the largest in the population.

**Materiality check** (`scripts/analysis/open61_fleet_dh_number_2026-08-20.py:216-232`): each building was
assigned a plausible `dh_total_kwh` equal to its own archetype's pooled kWh/m² rate times its own
floor area, then added to the population to see how much the headline would move.

- Warehouse anomaly: archetype pooled rate 0.5168 kWh/m² × 1,686.6 m² → plausible 871.6 kWh → headline shifts by **−0.00132 kWh/m²**.
- SecondarySchool anomaly: archetype pooled rate 18.8038 kWh/m² × 30,910.4 m² → plausible 581,234.0 kWh → headline shifts by **−0.00085 kWh/m²**.

**Neither anomaly would materially move the headline if included at a plausible value.** Both shifts
are three orders of magnitude smaller than the headline itself. This is expected given each is one
building out of 8,144.

## Design question left open (not answered here)

The measured fleet DH total is 470.8M kWh, unreported by whatever produced the adopted 153.8 kWh/m²
figure. Whether and how that energy should be folded into the fleet EUI adopted baseline — as an
addition, a re-weighted term, or something else — is a modelling/design decision outside this plan
and is not addressed by this measurement.
