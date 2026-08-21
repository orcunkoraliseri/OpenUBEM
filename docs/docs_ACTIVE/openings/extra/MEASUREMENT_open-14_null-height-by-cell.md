# MEASUREMENT — OPEN-14: null-`height_m` hole across all twelve cells (2026-08-21)

> Executes T04 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21.md`.
> Measurement/sizing only. No slice fetched, no fusion tier run, no config touched.
> Script: `scripts/analysis/open14_null_height_by_cell_2026-08-21.py`
> CSV: `openubem/outputs/comparisons/open14_null_height_by_cell_2026-08-21.csv`

## What this is and is not

This sizes the null-`height_m` hole in all twelve cells directly from `01_buildings.gpkg`, then
applies `nyc_centre`'s **measured** fusion-tier fill rate (106/121, from
`extra/MEASUREMENT_open-14_fusion-yield.md`) as a labelled **extrapolation**, not a re-run. No cell
other than `nyc_centre` has had the fusion tier actually run against it in this task or its
predecessor.

## Per-cell result

| cell | n_buildings | n_null_height | pct_null_height | of which also null `levels` | pct |
|---|---:|---:|---:|---:|---:|
| austin_rural | 245 | 245 | 100.00 % | 244 | 99.6 % |
| nyc_rural | 198 | 198 | 100.00 % | 198 | 100.0 % |
| nyc_suburban | 1,589 | 1,589 | 100.00 % | 1,589 | 100.0 % |
| austin_centre | 413 | 349 | 84.50 % | 247 | 70.8 % |
| la_centre | 226 | 45 | 19.91 % | 31 | 68.9 % |
| nyc_centre | 738 | 121 | 16.40 % | 107 | 88.4 % |
| austin_suburban | 437 | 114 | 26.09 % | 74 | 64.9 % |
| austin_urban | 425 | 47 | 11.06 % | 43 | 91.5 % |
| la_urban | 618 | 42 | 6.80 % | 29 | 69.0 % |
| nyc_urban | 1,779 | 40 | 2.25 % | 34 | 85.0 % |
| la_suburban | 1,343 | 15 | 1.12 % | 15 | 100.0 % |
| la_rural | 149 | 1 | 0.67 % | 0 | 0.0 % |
| **fleet** | **8,160** | **2,806** | **34.39 %** | — | — |

**C9 — pass.** `nyc_centre`'s null-`height_m` count reproduces **121** exactly (the fusion-yield
doc's own population). The extrapolation below is not void.

## The hole is concentrated, not spread

Three cells — `austin_rural`, `nyc_rural`, `nyc_suburban` — are **100 % null `height_m`**. Together
they carry **2,032 of the 2,806 fleet-wide nulls (72.4 %)**. `nyc_suburban` alone is **1,589 of
2,806 (56.6 %)** — more than every other cell combined. A partial acquisition targeting just these
three cells (and `nyc_suburban` in particular) would close most of the fleet-wide hole; the
remaining eight cells range from 0.7 % to 84.5 % and contribute the rest more thinly.

`height_m` and `levels` are null together at a high rate everywhere the hole is large (≥85 % overlap
in every cell above 25 % null except `austin_centre` and `austin_suburban`, both ~65–71 %). This is
the direct link to OPEN-35 (T05, same pass): a large share of these rows are exactly the population
that would fall to `derive_num_floors`'s branch 3 or 4 if `height_m` stayed unfilled.

## Extrapolation (labelled, not a measurement)

Applying the **measured** `nyc_centre` fusion-tier fill rate — 106/121 = **87.60 %** — as a flat
bound to the other eleven cells' null counts:

- Eleven-cell (excluding `nyc_centre`) null-`height_m` total: **2,685**.
- **Extrapolated** fill at the `nyc_centre` rate: **~2,352 of 2,685** (extrapolated, not measured).
- **Extrapolated** remaining null after fill: **~333 of 2,685** (extrapolated, not measured).

This is a flat-rate bound only. It assumes every other cell's Overture-slice coverage and building
mix behaves like `nyc_centre`'s — an assumption the task does not test, because testing it means
running the fusion tier against the other eleven slices, which requires the custody OPEN-14 is
waiting on. Full per-cell extrapolated figures are in the CSV
(`extrapolated_fill_at_nyc_centre_rate`, `extrapolated_remaining_null_after_fill` columns).

## Test status

- **C9 — pass.** 121, exact.
- **C10 — pass.** Every extrapolated figure in this doc is stated with "extrapolated" in the same
  sentence; none is presented as measured.

## Remedy shape (NOT applied)

Not this task's call — acquisition of the eleven missing Overture slices, or a different tier, or
neither. The sizing above (concentrated in 3 of 12 cells, dominated by `nyc_suburban`) is offered as
the input to that decision, not a recommendation.
