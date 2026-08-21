# MEASUREMENT — OPEN-14 T09: is the 87.6% extrapolation defensible? (2026-08-21 night)

> Executes T09 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md`.
> Measurement only. No fusion tier run, no fill applied, no config touched.
> Script: `scripts/analysis/open14_t09_extrapolation_check_2026-08-21b.py`
> CSVs: `openubem/outputs/comparisons/open14_t09_null_height_population_compare_2026-08-21b.csv`,
> `openubem/outputs/comparisons/open14_t09_distance_to_nyc_centre_2026-08-21b.csv`

## What this tests

`MEASUREMENT_open-14_null-height-by-cell.md` applies `nyc_centre`'s **measured** fusion-tier fill
rate (106/121 = 87.60 %) as a flat extrapolated bound to the other eleven cells' null-`height_m`
populations, producing "~2,352 of 2,685 would fill." That extrapolation assumes the other cells'
null-height populations resemble `nyc_centre`'s. This task checks that assumption directly, not the
fusion tier itself.

## C18 — reproduction

Fleet null-`height_m` total: **2,806** (F12 exact match). Three 100 %-null cells: `austin_rural`,
`nyc_rural`, `nyc_suburban` (F12 exact match). These three carry 72.4 % of the fleet gap.

## Method

For each cell's null-`height_m` subset (from `01_buildings.gpkg`, joined to `05_results.csv` on
`osm_id` only for `archetype_id`), compared against `nyc_centre`'s null-`height_m` subset on:
`footprint_area_m2` distribution (median, IQR), archetype mix (top-3 archetypes, Jaccard overlap
with `nyc_centre`'s top-3), `levels` availability (% of the null-height rows that have a non-null
`levels`), `data_quality_flag` mix (% carrying the `generic_tag` token, as a proxy for how degraded
the row is overall), and urban/rural class (from the cell name).

A composite distance-to-`nyc_centre` score was built from four normalised components: log-ratio of
median footprint area, difference in % levels-available, difference in % generic-tag, and
`1 − Jaccard(top-3 archetypes)`. This is a similarity heuristic for this task only, not a validated
metric — it is reported alongside its components so the reader can see which factor drives it.

## Result

`nyc_centre`'s null-height population: n=121, median footprint 1,384.5 m² (IQR 655–2,646), 11.6 %
also have `levels`, 54.5 % carry `generic_tag`, dominant archetype `LargeOffice` (39.7 %).

Ranked by composite distance to `nyc_centre` (lower = more similar), nearest to farthest of the
other 11 cells: `la_urban` (0.225) < `la_centre` (0.434) < `austin_centre` (0.497) <
`austin_urban` (0.593) < `austin_rural` (0.663) < `nyc_urban` (0.701) < `nyc_rural` (0.881) <
`la_suburban` (0.907) < `austin_suburban` (0.936) < `nyc_suburban` (0.972) < `la_rural` (1.140).

The three 100 %-null cells are not clustered at one end: `austin_rural` ranks 5th of 11 (moderately
close), but `nyc_rural` ranks 7th and `nyc_suburban` ranks 10th of 11 (among the most different).
`nyc_suburban` alone is 1,589 of the fleet's 2,806 null-height rows (56.6 %) and its profile is
sharply unlike `nyc_centre`'s: `nyc_suburban`'s dominant archetype is `MidriseApartment` (61.6 %)
against `nyc_centre`'s `LargeOffice` (39.7 %), its median footprint area is 100.0 m² against
`nyc_centre`'s 1,384.5 m² (14× smaller), and 0.0 % of its null-height rows have `levels` available
against `nyc_centre`'s 11.6 %.

## C19

**Mean composite distance for the three 100 %-null cells (0.839) is larger than the mean across all
eleven non-`nyc_centre` cells (0.723) — the three cells carrying 72.4 % of the gap are measurably
*less* like `nyc_centre` than the fleet average, not more.** This is in the direction the task's
`Why` section anticipated: the population the extrapolation leans on hardest is the population it
resembles least.

## Restatement of the ≈2,352 figure, with the caveat this task adds

The ≈2,352-of-2,685 extrapolated fill is **not withdrawn or replaced with a new point estimate** —
no fusion-tier run against any other cell exists on disk to compute one, and producing a substitute
number without running the tier would itself be an invented figure, which this task's own hard
rules forbid. What this task adds is the caveat the prior extrapolation lacked: **the 87.6 % rate is
measured on a population that is, on this task's similarity check, further from most of the cells
it is being applied to than those cells are from each other on average** — and the single largest
contributor, `nyc_suburban` (56.6 % of the null-height total), is the single most dissimilar cell in
the ranking. **≈2,352 should be read as an upper-bound-leaning extrapolation, not a central
estimate; a defensible range cannot be constructed from what is on disk without running the fusion
tier against at least `nyc_suburban` or `nyc_rural` directly** — that run is outside this task's
scope (same custody block `MEASUREMENT_open-14_null-height-by-cell.md` names).

## Test status

- **C18 — pass.** 2,806 total; `austin_rural`, `nyc_rural`, `nyc_suburban` reproduce as the
  three 100 %-null cells.
- **C19 — pass, stated as headline above.** The three 100 %-null cells are measurably less like
  `nyc_centre` than the fleet average (composite distance 0.839 vs 0.723).

## Remedy shape (NOT applied)

None proposed. Whether to run the fusion tier against `nyc_suburban`/`nyc_rural` directly to replace
the extrapolation with a measured figure is the user's decision, not this task's.
