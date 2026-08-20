# MEASUREMENT — OPEN-38 T15: what is `nyc_rural/way_965718401`'s published result worth?

**Date:** 2026-08-19 · **Task:** T15 of `PLAN_twenty-items-2026-08-19.md`

## 1. Confirmed at HEAD: this is the SmallHotel prototype, and it really does complete

Rebuilt through the real, unmodified pipeline (same fixture/method as OPEN-38 T05,
`%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/nyc_rural/01_buildings.gpkg`), because the
existing E02 harvest artifact for this building carries no `.idf` and its `.sql` lacks the hourly
report data the production parser needs (§3). `classify()` returns `archetype_id = SmallHotel`
(`scripts/analysis/open38_t15_malformed_publisher_rebuild_2026-08-19.py`), and the rebuilt IDF's
zone names (`215_218 PTAC`, `SAC_EXERCISECENTER`, `SAC_RESTROOM`, …) match the `SmallHotel` baseline's
own `ZoneHVAC:EquipmentConnections` zone list exactly. **EnergyPlus Completed Successfully —
58,101,663 Warning; 0 Severe Errors**, reproducing the register's own citation
(`58101662`, off by one — noise, not a discrepancy) to the exact same message shape. 0 Severe is
E+'s own count; a raw `grep -c Severe` returns 3 because the recurring-error summary text itself
contains the word "Severe" as a label, not a triggered error — checked directly, not assumed.

## 2. The malformed-door signature, re-verified

`openubem/outputs/comparisons/open38_subsurface_census.csv` records `nyc_rural/way_965718401`,
`n_occurrences=3`, `terminated=False` — matching the register's "3 doors that do not fit their walls,
0 Severe." T04's original finding (that the 3 named `CHKSBS` pairs sit on `RearStairs`/`Corridor`/
`FrontStairs`, not on the fatal `LaundryRoomFlr1` zone in the *fatal* buildings) is a different
building's geometry; this task does not re-open the fit-tolerance question for this specific
non-fatal building — out of scope for "what is the published result worth."

## 3. The published EUI cannot be independently quantified from what exists on disk — and why, precisely

Two separate blockers, both found directly, not assumed:

**(a) The building's own existing E02-harvest `.sql` cannot be parsed for EUI at all.**
`openubem.results.parser.parse_building()` returns `parse_status = failed_zone_mismatch`,
`error_summary = "layout_assign: zero zone-level keys found in SQL (corrupt/empty result)"`. Direct
inspection of the `.sql`'s `ReportDataDictionary` table confirms why: it is essentially empty (this
building's schema also lacks the newer `TabularDataWithStrings` view other harvested buildings carry
— a different SQLite output configuration than what the ad hoc EUI scripts in this arc assume).

**(b) A fresh rebuild at HEAD reproduces the identical parser failure — and this task traced it to
its root cause, which is general, not building-specific.** Rebuilding this exact building through the
real pipeline (with `run_step3(..., trim_outputs=True)`, the same flag every layout_assign rebuild in
this arc has used, including OPEN-38 T05) reproduces `parse_status = failed_zone_mismatch` again on
the fresh `.sql`. Direct inspection: the fresh SQL's `ReportDataDictionary` carries exactly **11
rows, all facility-level meters** (`Electricity:Facility`, `Heating:Electricity`,
`InteriorLights:Electricity`, …), **zero zone-level variables**. `openubem/idf/outputs.py:47-61`
(`write_outputs`) shows why: `trim_hourly=True` skips the entire `STANDARD_OUTPUTS` per-zone
`Output:Variable` block — which is what would emit `"Zone Lights Electricity Energy"`, the exact
variable `_check_zone_integrity`'s `layout_assign` branch (`openubem/results/parser.py:221-236`)
requires to find a zone key at all. **This task confirmed the fix directly**: rebuilding a different
small `layout_assign` building (`la_urban/relation_6356887`, 6 zones) with `trim_outputs=False`
makes `parse_building()` return `parse_status = success`, `total_eui_kwh_m2 = 68.28` — proving the
gate, not the geometry, is what blocks parsing (see `extra/MEASUREMENT_open-03_vintage-at-head.md`
§3 for the full trace, shared with T18).

**This is a general finding, not specific to the malformed-door defect**: no `layout_assign` build made
the way this arc has been making them (`trim_outputs=True`, matching the original E02 harvest's own
apparent SQL schema) can currently deliver a production-parser EUI, for any building. The malformed
door is incidental to why *this specific* building's number is unavailable.

## 4. What comparison numbers ARE available, and what they show

**Same osm_id, `auto` mode (production-certified, not `layout_assign`):**

| source | archetype | footprint_area_m2 | total_eui_kwh_m2 |
|---|---|---:|---:|
| baseline (`phaseE_elevrb`) | SmallHotel | 34.16 | 412.925728 |
| run 4 | SmallHotel | 34.16 | 412.935981 |

Essentially identical between generations (Δ 0.01, noise) — `auto` mode's own result for this
building is stable and untouched by the `layout_assign` malformed-door defect, because `auto` never
builds this zone or this geometry at all (§4 of the companion T14 report).

**The only pre-existing `layout_assign` figure anywhere on disk for this osm_id**,
`t20_layout_assign_eui.csv` (an older harvest generation, explicitly not HEAD-verified): `archetype_id
= SmallOffice`, `floor_area_m2 = 34.16`, `status = success`, `total_eui = 911.41`. **This number
cannot be trusted as a description of the malformed-door SmallHotel building**: its own
`archetype_id` label contradicts the building's real zone names (a fresh instance of OPEN-06's
already-documented archetype-label non-reproducibility across harvest generations — 67-zone
`SmallHotel`-shaped internals under a `SmallOffice` label). There are **zero** `SmallHotel` rows
anywhere in that same CSV, fleet-wide, so there is also no valid same-archetype peer distribution to
benchmark it against in that generation.

## 5. What this bounds, independent of the missing number

Regardless of what this building's own `layout_assign` EUI turns out to be, **it cannot touch any
adopted or published fleet figure**: `layout_assign` is not certified for fleet EUI (register,
multiple items) and OPEN-32 already established structurally and exhaustively that no adopted result
depends on `layout_assign` (0 of 16,320 adopted rows). This building's malformed geometry is real,
reproducible, and — per T04's disjointness finding, re-confirmed by T14's independent 40,800-file
grep (§4 of the companion report) — confined entirely to `layout_assign`, so its **size on any number
this project publishes is zero**, independent of the unresolved EUI question above.

## 6. What would quantify it

A `layout_assign` rebuild of this building (and, for a real peer comparison, its `SmallHotel`
siblings) with `trim_outputs=False` — the same fix this task verified works on a different building —
would let `openubem.results.parser.parse_building()` compute a real, production-consistent EUI, at a
one-time cost of retaining full hourly output for however many buildings are sampled.

## Artifacts

- `scripts/analysis/open38_t15_malformed_publisher_rebuild_2026-08-19.py`
- `scratchpad/open38-t15-rebuild/` (rebuilt IDF + EnergyPlus outputs, gitignored scratch)
- Shared root-cause trace: `extra/MEASUREMENT_open-03_vintage-at-head.md` §3
  (`scripts/analysis/open03_t18_trim_hypothesis_check_2026-08-19.py`,
  `scratchpad/open03-t18-trim-check/`)
