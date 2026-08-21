# MEASUREMENT — OPEN-19: does the LA offset survive at 8,160, and is a code-year field even carriable?

**Date:** 2026-08-21 · **Task:** T09 of `PLAN_ten-live-items-2026-08-21.md` · **Item:** OPEN-19
**Script:** `scripts/analysis/open19_city_offset_2026-08-21.py`
**Output:** `openubem/outputs/comparisons/open19_city_offset_2026-08-21.csv` (60 rows: 3 city, 12
cell, 45 archetype-matched)

## 0. Scope note — this is NOT a re-derivation of the +38.8% figure

The historic "~+40%" ("+38.8%" exact, per `MEASUREMENT_open-19_la-standard-basis.md` §3) is **LA
simulated vs LA measured/benchmark consumption**, n=2,314, from `V19_phaseC_rescore.md`. **No measured
benchmark data exists in this corpus** — `05_results.csv` has no such column. This task cannot and
does not recompute that figure. What it does instead, per the plan: restate a **simulated-vs-simulated
city comparison** at full fleet scale (LA vs Austin vs NYC, all `auto`-mode `success` rows), and
inventory whether the codebase could carry a code-year/climate switch at all. These are two different
questions and the answer to the second does not validate or refute the first.

## 1. Control C20 — reproduction of the adopted figure

Fleet-wide pooled EUI (Σ energy ÷ Σ area, `simulation_status == 'success'`), all 12 cells,
`05_results.csv` read directly from `evidence/open48_refleet4/<cell>/results/`:

**153.8304 kWh/m² over n = 8,153, floor area 24,333,586 m².**

Adopted figure: **153.8231 kWh/m² over 8,153, 24,320,582 m²**
(`MEASUREMENT_fleet-restatement-2026-08-19.md:14`).

**n matches exactly (8,153). The pooled figure matches to within 0.0047 % relative (0.0073 kWh/m²
absolute) — not bit-for-bit.** Per hard rule 3, this is reported rather than smoothed: cross-checking
against the fleet-restatement doc's own per-cell table (`:28-36`) shows most cells match to the last
reported digit (`la_suburban` 108.42/108.42, `nyc_rural` 233.63/233.63, `nyc_suburban`
188.66/188.66), but a few do not — `austin_suburban` 159.02 here vs **159.20** there (the largest gap,
0.18 kWh/m², 0.11 % relative), `la_rural` 121.46 vs 121.51, `nyc_centre` 166.59 vs 166.57, `nyc_urban`
148.19 vs 148.21, `austin_urban` 173.60 vs 173.62. The per-cell area, n and `simulation_status`
counts in the raw `05_results.csv` files (unchanged on disk since 2026-08-19 20:20, confirmed by file
mtime — `evidence/` is untracked by git so there is no commit history to check) match the doc's `n`
column exactly in every cell. **The cause of the per-cell gaps is not identified within this task**
— both computations use the identical Σ(EUI × floor_area) ÷ Σ(floor_area) definition (OPEN-43's
ruling) over the same files; the gaps do not correspond to any alternate weighting tried (mean of
per-building EUI, footprint-area weighting). This is flagged, not adjusted, and does not on its own
look large enough to be "a bigger finding than OPEN-19" (fleet aggregate is 0.005 % off), but it is
an unresolved discrepancy and is recorded as one.

## 2. City-level pooled comparison (mix included)

| city | n | pooled total EUI | pooled heating EUI | pooled cooling EUI | floor area m² |
|---|---:|---:|---:|---:|---:|
| austin | 1,520 | 161.00 | 5.97 | 28.82 | 5,896,955 |
| **la** | **2,330** | **128.13** | 5.38 | 17.04 | 6,815,439 |
| nyc | 4,303 | 165.27 | 23.74 | 15.80 | 11,621,192 |

**LA is the lowest of the three, not the highest**: LA vs Austin = **−20.41 %**, LA vs NYC =
**−22.47 %**. This is the opposite direction from a "LA runs hot" story, when the comparison is
simulated-vs-simulated across cities rather than simulated-vs-measured within LA (§0). Archetype mix
differs sharply by city (LA is 75 % `MidriseApartment` by count), so §3 repeats the comparison
holding archetype fixed.

## 3. Archetype-matched comparison (mix-free-ish)

15 archetypes are present in all three cities: `Courthouse, FullServiceRestaurant,
HighriseApartment, LargeHotel, LargeOffice, MediumOffice, MidriseApartment, OpenUBEMUnknown,
Outpatient, QuickServiceRestaurant, RetailStandalone, SecondarySchool, SmallOffice, SuperMarket,
TallBuilding`. Pooling only rows in these 15 archetypes, by city:

| city | n | pooled total EUI | floor area m² |
|---|---:|---:|---:|
| austin | 1,513 | 154.94 | 4,879,377 |
| **la** | **2,293** | **129.09** | 6,734,216 |
| nyc | 4,276 | 172.77 | 7,647,116 |

LA vs Austin (archetype-matched) = **−16.68 %**. LA vs NYC (archetype-matched) = **−25.28 %**. **The
mix-free number still shows LA running colder than both other cities, not hotter** — narrower than
the mix-included Austin gap (−20.41 % → −16.68 %) but the same sign, and the NYC gap widens
(−22.47 % → −25.28 %). Per-archetype rows (all 45 city×archetype combinations) are in the CSV; e.g.
`MidriseApartment` (LA's dominant archetype, n=1,753 in LA): LA 99.09, Austin 110.65, NYC 140.20 —
LA lowest in its own dominant archetype too.

## 4. Heating/cooling split of the city-level offset

| city | heating share of total EUI | cooling share |
|---|---:|---:|
| austin | 3.7 % | 17.9 % |
| la | 4.2 % | 13.3 % |
| nyc | 14.4 % | 9.6 % |

LA's absolute heating (5.38) and cooling (17.04) pooled EUI are both **lower** than Austin's (5.97 /
28.82) and NYC's cooling is lower than LA's but its heating is far higher (23.74) — driven by NYC's
climate zones (4A/6A) needing far more heating than LA's uniform 3B. **Neither an envelope story (a
Title-24-vs-90.1 wall/window/infiltration difference, which would show up as an offset in both
heating and cooling in the same direction) nor a weather story alone explains this pattern in the
direction OPEN-19's hypothesis needs** — the fleet-scale, city-to-city read does not reproduce a
"LA hot" signature at all, whatever is true of the original vs-measured 38.8 % figure.

## 5. Code-year / climate-zone field inventory (independent re-grep)

`grep -rniE "STD2022|climate_zone|code_year|ashrae|title.?24" openubem --include="*.py"` →
**109 hits**, confirming — not merely repeating — `MEASUREMENT_open-19_title24-scoping.md`'s prior
"zero Title 24/CEC/CALGreen hits" finding (`grep -rin "title.?24\|CALGreen\|\bCEC\b"` still returns
**0** across `openubem/` and `scripts/`, re-run this task).

What does exist, each independently re-confirmed at HEAD:

- **`climate_zone` — per-building.** Computed by `assign_climate_zones()`
  (`openubem/acquisition/climate_zone.py:74-193`), attached at
  `openubem/acquisition/__init__.py:106-112`, asserted non-null at
  `openubem/semantic/__init__.py:98,107-109`. Reaches only two consumers downstream (below); never a
  code-year or jurisdiction switch by itself.
- **`ARCHETYPE_IDF_MAP` — per-archetype, one national standard only.** `openubem/geometry/
  layout_assigner.py:25-40`: every real archetype maps to one `..._STD2022_Buffalo.idf` prototype
  (ASHRAE zone 6A), selected by `archetype_id` alone — `climate_zone` is not a selection key.
- **`get_construction_set()` — per-archetype, climate-zone-keyed, but wired to one path only.**
  `openubem/semantic/construction_sets.py:266-355` looks up `(archetype_id, climate_zone)` in the
  bundled `openubem/data/construction/ashrae_90_1_2019.json` (one national table). Re-confirmed: this
  path is invoked from `_build_unknown_envelope()` (`openubem/semantic/__init__.py:203-372`), gated to
  the `OpenUBEMUnknown` synthetic-archetype population only — the 20 real archetype prototypes get
  their envelope baked into their `.idf` file, not from this table.
- **`economizer_db_limit_c` — per-archetype-and-climate-zone data, unread.** Re-confirmed present:
  `openubem/data/loads/hvac_systems_by_archetype.json:29,42,56,...` carries `{"4A": 18.3, "3B": 23.9,
  "2A": 18.3}` per archetype. `openubem/idf/hvac.py`'s 6 economizer call sites still hardcode
  `Economizer_Type = "DifferentialDryBulb"` with no dry-bulb setpoint keyed from this field — the
  data exists, the wiring to consume it does not.

**Conclusion, unchanged from the prior scoping and now independently re-verified: no code-year or
jurisdiction (Title 24 / CALGreen) switch exists anywhere in the codebase. One climate-zone-keyed data
path exists (`get_construction_set`) but reaches only the `OpenUBEMUnknown` synthetic population, and
one climate-zone-keyed data field exists (`economizer_db_limit_c`) but is dead — present in the JSON,
never read.**

## Remedy shape (NOT applied)

None proposed — this task restates and inventories, it does not remediate.

## How-to-test results

- **C20** — n reproduces exactly (8,153). Pooled figure reproduces to within 0.0047 % relative, not
  exactly; per-cell gaps up to 0.18 kWh/m² are reported, not adjusted (§1). Judged not to be "a bigger
  finding than OPEN-19" given the fleet-level closeness, but flagged as an open discrepancy.
- **C21** — archetype-matched comparison names its 15 archetypes and each city's n (§3; full
  per-archetype n in the CSV).
