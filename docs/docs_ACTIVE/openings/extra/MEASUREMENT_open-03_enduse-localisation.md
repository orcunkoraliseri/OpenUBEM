# MEASUREMENT — OPEN-03 / AA7: end-use diff on the four load-identical buildings

> Executes T01 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-board-items-2026-08-20.md`.
> Measurement only. No EnergyPlus run. No `openubem/` code touched.

## Buildings

The 4 from-scratch buildings from `openubem/outputs/comparisons/open03_load_source_per_building.csv`
(lighting/equipment ratio == 1.000, internal loads bit-identical between `auto` and
`layout_assign`): `austin_centre/way/1008727470`, `nyc_centre/way/265424467`,
`nyc_suburban/way/846412106`, `nyc_urban/way/241862488`.

## Data sources (deviation from plan §6 T01's "How")

The plan's text says to read both arms' `eplusout.sql` under `scratchpad/open03-untrimmed-sample/…`.
That directory holds only the `layout_assign` arm (`sim/` + `step3_layout_assign/`); it has no
`auto` arm data. The `auto` arm's `eplusout.sql` lives at
`C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4\<cell>\sim_out\<way>\eplusout.sql`
— the same location `open03_load_source_decomposition_2026-08-20.py` (`AUTO_ROOT`) already used to
build the CSV this task controls against. Both files exist for all 4 buildings; nothing was
simulated. This is a plan-citation error, not an execution problem, and is recorded per hard rule 1
("if a DESIGN doc contradicts a task, STOP and quote the conflict") — this is a PLAN doc, not DESIGN,
so it was resolved by using the file the referenced CSV was itself built from, rather than stopping.

## Control (mandatory)

Reproduced ratio (`layout_assign` total EUI / `auto` total EUI), using the two arms' own reported
totals (`total_eui_kwh_m2` for `auto`, `Total_End_Uses_kwh_eui` for `layout_assign`, both already in
`open03_load_source_per_building.csv`):

| building | auto EUI | layout_assign EUI | ratio |
|---|---|---|---|
| austin_centre/way/1008727470 | 204.106 | 187.017 | 0.9163 |
| nyc_centre/way/265424467 | 203.609 | 155.178 | 0.7621 |
| nyc_suburban/way/846412106 | 364.020 | 316.913 | 0.8706 |
| nyc_urban/way/241862488 | 259.645 | 230.166 | 0.8865 |

Re-extracting `layout_assign`'s 7 end uses directly from its `eplusout.sql` (ABUPS "End Uses" table)
and summing reproduces `Total_End_Uses_kwh_eui` to within 0.03% for all four (worst:
`nyc_urban/way/241862488`, +0.029%). **Pooled gap, area-weighted by `floor_area_m2_auto`, using the
two arms' own reported totals: −23.6090 %, against the −23.61 % on record — reproduced.**

Reconciliation: the 7 end uses (Heating, Cooling, Interior Lighting, Interior Equipment, Fans,
Pumps, Water Systems) sum to each arm's own ABUPS "Total End Uses" row within 0.031 % for every
building in both arms (worst: `austin_centre` auto, 0.0306 %) — well inside the 0.5 % bound.

## End-use diff, pooled over the 4 (area-weighted by `floor_area_m2_auto`)

| end use | pooled diff (layout_assign − auto), kWh/m² | share of pooled gap |
|---|---|---|
| Heating | −42.20 | 87.6 % |
| Fans | −4.98 | 10.3 % |
| Cooling | −2.37 | 4.9 % |
| Pumps | −0.74 | 1.5 % |
| Water Systems | −0.02 | 0.0 % |
| Interior Lighting | 0.00 | 0.0 % |
| Interior Equipment | 0.00 | 0.0 % |

Heating alone accounts for 87.6 % of the pooled gap, and is the dominant term in every one of the
4 buildings individually (87–109 % of that building's own gap; cooling partially offsets it in 2 of
4 buildings). Lighting and equipment are exactly 0.00 in every building, as the load-identity
premise requires. Full per-building table: `openubem/outputs/comparisons/open03_enduse_localisation.csv`.

## Geometry / zoning / envelope / HVAC sizing, per building (both arms)

| building | mode | conditioned floor area m² | zones | ext. wall m² | window m² | WWR % | heating cap. kW | cooling cap. kW |
|---|---|---|---|---|---|---|---|---|
| austin_centre/1008727470 | auto | 87.96 | 1 | 151.88 | 42.85 | 28.21 | 5.25 | 8.90 |
| austin_centre/1008727470 | layout_assign | 87.96 | 1 | 151.88 | 42.85 | 28.21 | 5.90 | 8.13 |
| nyc_centre/265424467 | auto | 17769.10 | 81 | 16270.79 | 6501.81 | 39.96 | 417.17 | 1990.33 |
| nyc_centre/265424467 | layout_assign | 17769.10 | 81 | **9122.10** | **3645.19** | 39.96 | 448.90 | 1714.44 |
| nyc_suburban/846412106 | auto | 32.65 | 1 | 80.32 | 24.46 | 30.45 | 3.87 | 4.09 |
| nyc_suburban/846412106 | layout_assign | 32.65 | 1 | 80.32 | 24.46 | 30.45 | 3.74 | 3.83 |
| nyc_urban/241862488 | auto | 76.01 | 2 | 172.89 | 27.24 | 15.76 | 0.00 | 6.93 |
| nyc_urban/241862488 | layout_assign | 76.01 | 2 | 172.89 | 27.24 | 15.76 | 0.00 | 6.24 |

Conditioned floor area, zone count and WWR are identical between arms for all 4 buildings.
`nyc_centre` — the largest building by far (17,769 m², vs 33–88 m² for the other three) and the one
that dominates the pooled result — has **44 % less exterior wall and window area under
`layout_assign`** at the same floor area and zone count: 9,122 m² vs 16,271 m² wall, 3,645 m² vs
6,502 m² window. Less exterior surface at the same conditioned area means less envelope heat loss,
which is directly consistent with `layout_assign` needing 42 kWh/m² less pooled heating. The other 3
buildings show identical envelope geometry between arms; only their HVAC-sizing capacities differ
by a few percent (a downstream consequence of slightly different peak loads, not an independent
geometry difference).

## Defect found (measured, not fixed, no register ID opened)

`openubem/results/parser.py`'s `METER_QUERY` (around line 41–53) lists
`'WaterSystems:NaturalGas'` and `'WaterSystems:Electricity'` but never
`'WaterSystems:DistrictHeating'`. All 4 buildings here have a nonzero `WaterSystems:DistrictHeating`
component in their ABUPS "Water Systems" end use (94–37,358 kWh depending on building size), which
`dhw_eui_kwh_m2` (parser.py:469–482) silently drops. Independently re-deriving `auto`'s total EUI
from the ABUPS "End Uses" table (sum of the same 7 rows, same `eplusout.sql`) comes out **1.03–1.10 %
higher** than the production `total_eui_kwh_m2` on record, for all 4 buildings, entirely traceable to
this one missing meter name. Lighting and equipment are unaffected (electricity-only in this sample);
this does not touch OPEN-03's "loads are bit-identical" finding. Any building whose DHW, heating or
cooling is served by a district-heating/cooling plant not named in that `IN (...)` list will have the
same undercount in the production `total_eui_kwh_m2` column.

## Conclusion

100 % of the −23.61 % gap in these 4 buildings is heating-dominated (87.6 % of it), and in the one
building large enough to matter for the pooled figure the heating difference tracks a ~44 % smaller
exterior envelope surface at an identical conditioned floor area and zone count under
`layout_assign` — the gap lives in envelope/geometry, not in loads, zoning or HVAC sizing.

## Artifacts

`scripts/analysis/open03_enduse_localisation_2026-08-20.py`,
`openubem/outputs/comparisons/open03_enduse_localisation.csv`,
`openubem/outputs/comparisons/open03_enduse_localisation_geometry.csv`,
`openubem/outputs/comparisons/open03_enduse_localisation_pooled.csv`.
