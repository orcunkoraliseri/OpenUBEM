# MEASUREMENT — OPEN-19 T10: is LA low because of its buildings or its climate? (2026-08-21 night)

> Executes T10 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md`.
> Measurement only. No re-simulation, no remedy proposed.
> Script: `scripts/analysis/open19_t10_shift_share_2026-08-21b.py`
> CSV: `openubem/outputs/comparisons/open19_t10_shift_share_2026-08-21b.csv`

## Scope note — this is not the historic +38.8 %

This task decomposes the fleet-scale **simulated-vs-simulated** city gap from F13
(`MEASUREMENT_open-19_city-offset-fleet-scale.md`). It has no relationship to the historic
"+38.8 %" LA simulated-vs-measured figure and does not touch it.

## C20 — reproduction

Recomputed directly from `05_results.csv` per cell (`simulation_status == 'success'`, Σ energy ÷
Σ area): **austin 161.00 (n=1,520), la 128.13 (n=2,330), nyc 165.27 (n=4,303)** — exact match to
F13.

## Method

Shift-share on the 15-archetype matched set already built for OPEN-19
(`openubem/outputs/comparisons/open19_city_offset_2026-08-21.csv`, `level == archetype_matched`,
45 rows). Share-weighted reconstruction on this set reproduces F13 §3's matched-subset numbers
exactly: austin 154.94, la 129.09, nyc 172.77 — confirming the decomposition basis before
decomposing anything.

For each city pair, with `base` and `comp` cities, archetype shares `share_a` (matched-set floor
area of archetype `a` ÷ matched-set total for that city) and intensities `intensity_a` (pooled
`total_eui_kwh_m2` for archetype `a` in that city):

- **mix effect** = Σ (`share_comp,a` − `share_base,a`) × `intensity_base,a`
- **intensity effect** = Σ `share_comp,a` × (`intensity_comp,a` − `intensity_base,a`)

This is an exact algebraic identity: mix + intensity = `matched_pooled_comp` − `matched_pooled_base`
by construction, with base intensities carrying the mix term and comparison shares carrying the
intensity term.

## C21 — decomposition, with residual stated

**LA vs Austin** (base=austin, comp=la): gap = **−25.8507** kWh/m² (matched basis). Mix effect =
**−7.3716** (28.5 % of gap). Intensity effect = **−18.4792** (71.5 % of gap). Mix + intensity =
−25.8507. **Residual = −0.000000** (exact by construction, floating-point noise only).

**LA vs NYC** (base=nyc, comp=la): gap = **−43.6760** kWh/m² (matched basis). Mix effect =
**−6.6899** (15.3 % of gap). Intensity effect = **−36.9861** (84.7 % of gap). Mix + intensity =
−43.6760. **Residual = −0.000000** (exact by construction, floating-point noise only).

In both comparisons the identity closes exactly — the decomposition is complete, nothing is left
unassigned.

## Heating/cooling, top 4 archetypes by combined matched-set floor area

| archetype | combined area m² | austin heat/cool | la heat/cool | nyc heat/cool |
|---|---:|---:|---:|---:|
| LargeOffice | 4,952,607 | 9.86 / 29.38 | 4.50 / 21.55 | 42.49 / 17.53 |
| TallBuilding | 4,162,733 | 1.03 / 24.40 | 0.73 / 19.02 | 12.32 / 15.91 |
| MidriseApartment | 2,202,178 | 9.03 / 15.52 | 5.43 / 5.60 | 40.70 / 5.94 |
| MediumOffice | 1,753,403 | 12.18 / 27.34 | 10.30 / 17.46 | 48.26 / 12.36 |

In every one of the four largest archetypes, LA's heating **and** cooling EUI are both lower than
Austin's, and NYC's heating is far higher than both (driven by NYC's colder climate zones, 4A/6A,
vs LA's uniform 3B and Austin's 2A), while NYC's cooling is lower than Austin's and mixed against
LA's. **LA being lower in both heating and cooling relative to Austin, in the same direction, in
every one of the four largest archetypes, is not the fingerprint a climate-only story would leave**
— a colder-designed climate would be expected to raise one load while lowering the other, not lower
both uniformly.

## EPW / climate manifest

One EPW file per cell, all twelve confirmed unique-and-singular in `02a_climate_epw.parquet`:
`austin_centre`/`austin_urban` → `USA_TX_Austin-Camp.Mabry.ANGB.722544_TMYx...`; `austin_rural` →
`USA_TX_Horseshoe.Bay.Resort.AP.720639...`; `austin_suburban` → `USA_TX_Austin.Exec.AP.720648...`;
`la_centre`/`la_urban` → `USA_CA_Los.Angeles.Downtown-USC.Campus.722874...`; `la_rural` →
`USA_CA_Lancaster-Fox.Field.723816...`; `la_suburban` →
`USA_CA_Torrance.Muni.AP-Zamperini.Field.722955...`; `nyc_centre`/`nyc_urban` →
`USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053...`; `nyc_rural` →
`USA_NY_Hudson.River.Reserve.997991...`; `nyc_suburban` → `USA_NY_Uniondale-Mitchel.AFB.749105...`.

**No heating/cooling degree-day proxy is present.** `02a_climate_epw.parquet`'s columns are
`osm_id, climate_zone, climate_zone_method, county_geoid, state, epw_path,
provenance_climate_zone` — no HDD/CDD or degree-day field anywhere in the file. Per the plan's
instruction, none was computed.

## C22

**The decomposition points at intensity, not mix.** Within-archetype intensity accounts for 71.5 %
of the LA-vs-Austin gap and 84.7 % of the LA-vs-NYC gap; archetype mix accounts for the remaining
28.5 % and 15.3 %. Whatever is driving LA's lower EUI, it is overwhelmingly a **same-archetype,
different-energy-outcome** effect, not a **different-building-mix** effect. No remedy is proposed
by this task, and this finding is not a restatement or a validation of the historic +38.8 %
sim-vs-measured figure — it answers a different, fleet-scale sim-vs-sim question (§0).

## Test status

- **C20 — pass.** Exact reproduction of 161.00 / 128.13 / 165.27.
- **C21 — pass.** Both decompositions close exactly (residual 0, to floating-point precision),
  stated explicitly above.
- **C22 — reported above as the doc's headline sentence, no remedy proposed, no conflation with
  the historic +38.8 % stated explicitly.**

## Remedy shape (NOT applied)

None proposed. Whether the intensity gap points at HVAC systems, internal loads, schedules, or
another per-archetype input is the user's next question, not this task's.
