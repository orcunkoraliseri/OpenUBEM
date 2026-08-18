# MEASUREMENT — OPEN-38: is `LAUNDRYROOMFLR1` the same defect as OPEN-42?

**Date:** 2026-08-18 · **Task:** T04 of `PLAN_four-items-2026-08-18.md`

Script: `scripts/analysis/open38_laundryroom_signature.py`. Output: `openubem/outputs/comparisons/open38_laundryroom_signature.csv` (7 rows, one per re-derived `LAUNDRYROOMFLR1` fatal run, joined to its `.eio` zone geometry and T03's orientation-warning counts).

## Verdict, up front

**Two mechanisms, not one.** Every axis measured separates the two populations cleanly: different EnergyPlus internal check (`CalcHeatBalanceInsideSurf` vs. `Temperature (low/high) out of bounds`), different zone position by geometry (bottommost storey vs. topmost storey), different geometry origin (substituted DOE prototype vs. OSM-extruded shape), and disjoint modes (`layout_assign` only vs. `auto`/`fast_zone`/`floor` only, never both). This is a recommendation; the director rules on the register.

## 0. Population re-derivation (obligatory — do not carry "seven" from the register)

Scanned all **8,160** `layout_assign` run directories in `HARVEST_ROOT` directly (12 cells × up to ~1,780 buildings each). For each, ran the project's own whitespace-tolerant `FATAL_RE`/`SEVERE_RE` matchers (`openubem/results/err_parse.py`) and took the nearest preceding `** Severe **` line before the `** Fatal **` marker (same method as `open42_failure_causes.py`), then filtered to runs whose severe line names `zone="LAUNDRYROOMFLR1"`.

```
Scanned 8160 layout_assign run directories (expected 8160).
RE-DERIVED POPULATION: 7 layout_assign runs fatal with nearest-preceding-Severe naming zone='LAUNDRYROOMFLR1'.
```

**Population = 7, confirmed from raw `.err`, independent of the register.** No STOP triggered.

| cell | stem | temperature (°C) |
|---|---|---|
| `la_centre` | `way_427942886` | −12,901.09 |
| `la_urban` | `relation_6374725` | −23,743.03 |
| `la_urban` | `way_401910463` | +182,399.27 |
| `la_urban` | `way_428846131` | −59,865.37 |
| `nyc_rural` | `way_965718400` | −12,459.96 |
| `nyc_rural` | `way_965718402` | −11,949.70 |
| `nyc_rural` | `way_965718403` | −15,490.64 |

All 7 have `n_severe_total = 1` — the fatal fires on the **first** severe error logged, no accumulation.

## 1. Non-vacuity control (reused from T03, re-run here independently)

```
ZERO case la_rural_building/way_472960972/eplusout.err: parser=0, grep -c 'upside down'=0, agree=True
MANY case la_rural_auto/way_472960972/eplusout.err: parser=144, grep -c 'upside down'=144, agree=True
NON-VACUITY CONTROL: PASS
```

## 2. Zone position — from `.eio` geometry, not from the zone name

The director's brief for this task required the zone's position to be answered from z-coordinates / ceiling height / multiplier, never from the name. Read directly from each run's own `eplusout.eio` `Zone Information` records:

| cell/stem | n zones in building | `LAUNDRYROOMFLR1` z-range | building's full z-range | topmost by geometry? | bottommost by geometry? |
|---|---|---|---|---|---|
| `la_centre/way_427942886` | 67 | 0.00 – 3.35 m | 0.00 – 11.58 m | **No** | **Yes** |
| `la_urban/relation_6374725` | 67 | 0.00 – 3.35 m | 0.00 – 11.58 m | **No** | **Yes** |
| `la_urban/way_401910463` | 67 | 0.00 – 3.35 m | 0.00 – 11.58 m | **No** | **Yes** |
| `la_urban/way_428846131` | 67 | 0.00 – 3.35 m | 0.00 – 11.58 m | **No** | **Yes** |
| `nyc_rural/way_965718400` | 67 | 0.00 – 3.35 m | 0.00 – 11.58 m | **No** | **Yes** |
| `nyc_rural/way_965718402` | 67 | 0.00 – 3.35 m | 0.00 – 11.58 m | **No** | **Yes** |
| `nyc_rural/way_965718403` | 67 | 0.00 – 3.35 m | 0.00 – 11.58 m | **No** | **Yes** |

**All 7 of 7 sit at the building's bottommost z-extent (floor 1 of 4), zone multiplier 1, invariant across all 7 buildings.** This is the exact opposite of OPEN-42's signature, where 15/16 fatal zones sit on the building's **topmost** storey (T03's CP-2 finding). The 67-zone count and identical z-breakpoints (0.00/3.35/6.10/8.84/11.58 m) across all 7 buildings confirm the geometry is the same substituted prototype template in every case, not independently derived per building.

`LAUNDRYROOMFLR1` itself carries **0/7** upside-down orientation warnings (T03's parser, re-run here on these same 7 `.err` files); no sibling zone in any of the 7 runs carries one either (`n_upside_down_total = 0` in every row of the CSV). The orientation signature that dominates OPEN-42's `auto` mode does not exist at all in `layout_assign` for this population — consistent with T03's fleet-wide finding that `layout_assign` carries the warning in only 3/8,160 runs fleet-wide, none of which are these 7.

## 3. Archetype — identified from the baseline-IDF library, not asserted from the name

`openubem/geometry/layout_assigner.py`'s `ARCHETYPE_IDF_MAP` names 27 archetype→baseline-IDF mappings. Scanning every mapped baseline IDF under `config.BASELINE_IDF_DIR` for a `Zone` object literally named `LaundryRoomFlr1` (case-insensitive):

```
BASELINE_IDF_DIR = C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231
Archetype(s) whose baseline IDF defines a Zone named 'LAUNDRYROOMFLR1': ['SmallHotel']
```

**All 7 fatal buildings were substituted with the `SmallHotel` DOE prototype** (`ASHRAE901_HotelSmall_STD2022_Buffalo.idf`) under `layout_assign`. This matches the register's own note that this is "the same zone token as OPEN-06's `SmallHotel` provenance defect." OPEN-42, by contrast, never substitutes a prototype — all 6 of its buildings keep their OSM-extruded geometry in the 3 failing modes (`auto`/`fast_zone`/`floor` all build zones from the building's own footprint; only `layout_assign` and `building` diverge from that, and both of those survive for OPEN-42's population).

## 4. Comparison table — OPEN-38 vs. OPEN-42, side by side

| dimension | **OPEN-38** (7 `layout_assign` fatals) | **OPEN-42** (16 fatal runs, 6 buildings × up to 5 modes) |
|---|---|---|
| Severe message class | `CalcHeatBalanceInsideSurf: The temperature of <N> C for zone="…"` | `Temperature (low\|high) out of bounds [<N>] for zone="…"` |
| n_severe before fatal | **1**, every run — immediate fatal on first severe | up to 24 (accumulates over the run before terminating) |
| Temperature range | −59,865.37 to +182,399.27 °C | −444.53 to +530.25 °C |
| Zone position (by `.eio` z-geometry) | **bottommost** storey (floor 1 of 4), 7/7 | **topmost** storey, 15/16 (director CP-2 finding) |
| Zone multiplier | 1 | not multiplier-driven (per OPEN-42's own T05 finding) |
| Geometry origin | substituted DOE prototype (`SmallHotel`), byte-identical z-breakpoints across all 7 buildings | building's own OSM-extruded footprint |
| Mode distribution | `layout_assign` **only** (0/8,160 in any other mode) | `auto`, `fast_zone`, `floor` — **never** `layout_assign` or `building` |
| Orientation warning (T03 parser) on the fatal zone | 0/7 | 1/16 (and that one case is the *sole* exception, `la_urban/way_402215469/auto`) |
| Co-occurs with "Base surface does not surround subsurface" | **yes, 7/7** (see §5) | not applicable — that warning is `layout_assign`-only, fleet-wide (register defect (ii)) |

No dimension is shared between the two populations except the superficial fact that both are "one zone, thermal runaway, read from `.err`." Every specific, measurable property — the EnergyPlus check that fires, the zone's position, the geometry's origin, and the mode — disagrees.

## 5. OPEN-38's second open question: unfitted subsurfaces below the warning threshold?

Re-grepped all 7 re-derived `LAUNDRYROOMFLR1`-fatal runs directly for `"Base surface does not surround subsurface"` and cross-checked against the existing `open38_subsurface_census.csv` (8 rows, built from a prior full-fleet `.err` scan):

| cell | stem | fresh grep count | census `n_occurrences` | census `terminated` |
|---|---|---|---|---|
| `la_centre` | `way_427942886` | 3 | 3 | True |
| `la_urban` | `relation_6374725` | 3 | 3 | True |
| `la_urban` | `way_401910463` | 3 | 3 | True |
| `la_urban` | `way_428846131` | 3 | 3 | True |
| `nyc_rural` | `way_965718400` | 3 | 3 | True |
| `nyc_rural` | `way_965718402` | 3 | 3 | True |
| `nyc_rural` | `way_965718403` | 3 | 3 | True |

Fresh grep agrees with the existing census on all 7 rows, exactly. **All 7 of the re-derived `LAUNDRYROOMFLR1` fatals also carry the subsurface warning; zero of the re-derived population falls outside the census.** The one census row not in this population, `nyc_rural/way_965718401` (`terminated=False`), is the census's own known non-fatal control — it carries the warning and survives, exactly as register defect (ii) already recorded.

**Answer: not determinable from `eplusout.err`.** `.err` can only report a malformed subsurface if EnergyPlus's own `CHKSBS` routine already crossed its internal fit-tolerance threshold and printed the Warning. A subsurface that is unfitted but stays inside that threshold produces no line anywhere in `.err` — there is nothing for any parser to find, regardless of how it is written. Answering this requires the IDF geometry itself (base-surface and subsurface vertex loops, checked independently of `CHKSBS`'s own threshold), and **that artifact does not currently exist on disk**: per this task's raw-data note, the entire E02 IDF corpus (`ubem_e02_fleet\<cell>\step3_<mode>\idfs\`) was emptied by the external disk sweep of 2026-08-17 (the same sweep OPEN-53's T02 audit already identified). Nothing is substituted for it here.

## 6. What this does and does not settle

**Settled:** the two failure populations are not one mechanism wearing two names — every measurable property disagrees. `LAUNDRYROOMFLR1`'s instability is not "the same defect as OPEN-42, just in a different mode."

**Not settled, and not claimed to be:** *why* the `SmallHotel` prototype's `LaundryRoomFlr1` zone specifically runs away when substituted via `layout_assign` — that is still open, and no local artifact was found in this task that answers it (the IDF corpus that would let anyone inspect the substituted geometry directly is gone). OPEN-38's own first open question (prototype-library defect vs. interaction with substituted target-building geometry) is therefore still unresolved; this task only establishes that it is a **different** open question from OPEN-42's.
