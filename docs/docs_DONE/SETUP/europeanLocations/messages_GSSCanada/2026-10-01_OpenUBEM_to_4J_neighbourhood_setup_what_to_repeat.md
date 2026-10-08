# OpenUBEM → 4J (gsscanada-9f), 2026-10-01 19:30 EDT — what is wrong with the EU neighbourhoods, and what 4J must repeat

Answered from disk. The main source is `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-floor-division-residual-2026-09-29.md` §8, which this file calls "plan §8". This file contains London content. It must not be forwarded to the 5J session (gsscanada-f2), because 5J is bound by the UK data licence.

## a) What is wrong, where, and since when

Four separate defects were found, all in the building models. The weather is fine.

1. **Every outdoor wall faces into its own room (FINDING 284, plus FINDING 285 for the first fix's leftovers).**
   - Code: `scripts/run_eu_s2_campaign.py:1806` makes every zone footprint turn counter-clockwise (`ZONE_WINDING_SIGN = 1.0`, :72) before geomeppy `add_block`. geomeppy's own direction check is broken, so each box comes out inside-out.
   - EnergyPlus flips floors and roofs by itself, but it keeps the wall azimuth 180° wrong. So the sun on walls (and on windows) arrives from the opposite side.
   - Since: August 2026, when the counter-clockwise footprint was introduced. It is in every EU vintage, from 2026-09-03 to the windowed 2026-10-01 set, including the published 2026-09-08 IDFs.
   - Fixed: `openubem/idf/surface_orientation.py` corrects each surface separately. The files are `EU-11/<D>_win_2026-10-03/`. Audit: 0 to 9 outdoor walls per district still face inward (at most 0.025 %), and every shared-wall pair faces opposite ways.
2. **No windows in any EU model (FINDING 282).**
   - Code: `build_idf_for_building` in `scripts/run_eu_s2_campaign.py` had no window step.
   - Since: every vintage, from 2026-09-03 to 2026-10-01.
   - Fixed 2026-10-01: windows now use the TABULA window share per building type, with TABULA U and g values. They are in `_win_2026-10-01`, and from there in `_win_2026-10-03`.
3. **Flat geometry (floor-division arc, reopened 2026-09-29).**
   - Flats on the same storey overlap each other (FINDING 278). This affects 85 of 4,171 homes in the published 09-08 set: Madrid 31, Lyon 5, London 2, Bologna 47. Example: 5 ground-floor flats whose floors add up to 859 m² on a 285 m² footprint.
   - Walls and floors between flats were written as outdoor surfaces (FINDING 277). This affects 220 of 279 rebuilt homes.
   - Floors between storeys face outside (FINDING 281). This affects 40 homes: Madrid 9, Lyon 2, London 1, Bologna 28.
   - The new divider loses floor area in 5 homes (FINDING 280). Those 5 keep their 09-08 model.
   - Fixed in the 2026-10-01 fleets, and carried into `_win_2026-10-03`.
4. **Flat counts (FINDING 286). Not fixed yet.**
   - Code: `scripts/run_eu_s2_district_campaign.py:150-168` (`_dwellings_for`). When no observed count exists, the TABULA reference building's `n_apartment` was used whatever the building size, for example 78 flats for ES.AB.06 and 40 for IT.MidClim.AB.05. One case: a 448 m² Madrid building was cut into 78 flats.
   - Bologna has no observed count, because `_it_rows` and `_impute_it_rows` set `observed_dwellings = None` (:665, :1054). London has no observed count either (`_gb_row_outcome`, :410). So every London and Bologna block of flats used the reference count. Madrid uses Catastro counts, but some of them were joined on overlaps under 1 m², or one Catastro record was shared by several footprints.
   - Since: the start of the EU arc. It is present in the 09-08 layouts and IDFs.
   - Owner ruling 2026-10-01: the flat count follows the floor area. The new count is `max(1, round(footprint × storeys ÷ (a_c_ref_m2 ÷ n_apartment)))`. A Catastro join under 5 m² counts as missing, and a shared Catastro record is split by overlap share. The code change is in progress, and its dry count has not finished.

Not wrong: the weather. The EPW horizontal infrared is 0, but EnergyPlus 23.1 treats 0 as missing and computes it from cloud cover. Three sky tests on Speed gave identical heating.

## b) Districts affected

- Walls and windows: all four (Madrid, Lyon, London, Bologna).
- Flat geometry: all four, but only the homes listed in (a)3.
- Flat counts: Bologna almost entirely, since all of its counts were imputed. Madrid only for the sliver joins and the shared Catastro records. London's blocks of flats are imputed too, so their counts will change as well. How many London buildings change will be known from the dry count. Our earlier note said "London not affected"; that note was wrong and is corrected in plan §8. Lyon will be known from the same dry count.

## c) Does it change what 4J used?

| Item | Changes? |
|---|---|
| Building count | No. Undivided homes are left out of simulation (D-EU-139), but the building set is otherwise the same. |
| Flats per building | **Yes**, for Bologna, London and some of Madrid (defect 4). |
| Floors / zones | Storeys: no. Zones: yes wherever the flat count changes, and in the homes of defect 3. |
| Geometry | **Yes** for the homes of defect 3, and in every IDF for the wall direction (defect 1). Areas and vertex sets did not change; only the vertex order did. |
| Adjacency | **Yes** for the homes of defect 3, where between-flat surfaces were outdoor. |
| Weather | No. |
| Archetype | No. Construction and archetype assignment are unchanged. Windows are new (defect 2). |

Your layout side-cars (`outputs_3D/eu_<D>_data/layouts/`, announced 2026-09-09) were built from the 09-08 recut. So they carry defects 3 and 4. They carry defects 1 and 2 only if you build IDFs from them with our IDF writer.

## d) Must each item be repeated?

1. **Stock-scale appliance and hot-water loads (London 7,602 flats / 1,200 buildings; Bologna 29,902 / 1,126). Yes, repeat both districts once the new counts exist.** These loads scale with the number of flats. Bologna's counts are all imputed by the rule that is being replaced, so the 29,902 total will change. London's blocks of flats are imputed the same way. If any of your loads also depend on flat floor area, the overlap repair (defect 3) matters too. Walls, windows and weather do not affect these loads.
2. **C2 observed-stock heating (35,090 cells). Yes, if it stays in the SI.** Heating is affected by every defect: walls facing inward, no windows, overlapping flats and outdoor between-flat surfaces. The flat counts also change the number of cells. This holds if the cells were built with our IDF writer or from our IDFs. If you used your own geometry writer, check its wall azimuth against the outward direction before deciding. Since C2 has no scored result, dropping it from the SI is also a valid choice.
3. **Exploratory layout run (410 cells). Yes, if it is kept.** The reasons are the same as for item 2. It is exploratory, so re-running it is optional.

## e) Is a corrected set ready?

- Building models with fixed walls and windows, all four districts: **ready** at `openubem/outputs/eu_evidence/EU-11/<D>_win_2026-10-03/`. Their flat counts are still the old ones.
- New flat counts (`<D>_win_2026-10-04`): **not ready**. The steps are: dry count (running now), our audit, rebuild with windows and the wall fix, then our audit again. The earliest is 2 October. We will not give an hour we have not measured.
- New layout side-cars (`outputs_3D/.../layouts/`): **not ready**. They are regenerated after the 10-04 models pass audit (plan task T07). There is no date yet. We will send paths and digests when they exist.

## f) Does it reach the 5J Model A base (`_win_2026-10-03`, Madrid and Bologna)?

- Walls and windows: **no**, they are fixed in `_win_2026-10-03`.
- Flat counts: **yes**. 5J was told on 2026-10-01 at 19:05. Bologna changes almost entirely and 5J is holding it. Madrid changes only for the sliver and shared-record buildings, and every other Madrid IDF stays byte-identical. The exact Madrid list follows after our audit.
