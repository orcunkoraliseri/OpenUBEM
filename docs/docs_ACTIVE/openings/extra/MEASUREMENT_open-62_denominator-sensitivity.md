# MEASUREMENT — OPEN-62: what each storey definition costs, in kWh/m² (2026-08-21 night)

> Executes T05 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md`.
> Script: `scripts/analysis/open62_denominator-sensitivity_2026-08-21b.py`
> CSV: `openubem/outputs/comparisons/open62_denominator-sensitivity_2026-08-21b.csv` (32,562 rows,
> one row per building per definition over the 8,153 successes)

## This is a denominator-only sensitivity, not a re-simulated result

**No IDF was rebuilt and no EnergyPlus run occurred.** Per-building energy is held fixed at the
adopted run's value (`total_eui_kwh_m2 × floor_area_m2` from `05_results.csv`, the published
floor area). Only the floor-area **denominator** is redefined as `footprint_area_m2 × storeys`
under each candidate storey-count definition, exactly as a definition change would move the
denominator without touching the simulated energy. Pooled EUI under each definition is
`Σ(total_eui × published_area) ÷ Σ(footprint_area_m2 × storeys)` over the 8,153
`simulation_status == success` rows, joined `open03_storey_census_zfix.csv` (8,160 rows) to
`05_results.csv` per cell.

## C10 — reproduce F10's agreement rates first

Reproduced exactly, in-script, before computing anything new: `layout_assign_storey_count`
vs `auto_storey_count` **2,372/8,160 = 29.07 %**; `_naive` **3,246/8,160 = 39.78 %**; `_floor`
**1,938/8,160 = 23.75 %**. No nulls in any of the four storey columns; all 8,160 keys unique;
census-to-results join is 8,160/8,160 with no missing rows.

## Results

| definition | n (of 8,153) | denominator (m²) | pooled EUI (kWh/m²) | Δ vs adopted 153.8231 | Δ denominator vs F6 24,333,586.4 m² |
|---|---:|---:|---:|---:|---:|
| `auto_storey_count` (baseline) | 8,153 | 24,320,581.9 | 153.9127 | +0.0896 | −0.053 % |
| `layout_assign_storey_count` | 8,153 | 12,634,619.6 | 296.2690 | +142.4459 | −48.077 % |
| `layout_assign_storey_count_naive` | 8,153 | 8,464,264.2 | 442.2412 | +288.4181 | −65.216 % |
| `layout_assign_storey_count_floor` | 8,153 | 15,841,047.7 | 236.3004 | +82.4773 | −34.900 % |

## C11 — baseline denominator against F6

`auto_storey_count` reconstructed as `footprint_area_m2 × storeys` gives a fleet denominator of
**24,320,581.9 m²**, against F6's published-area sum of **24,333,586.4 m²** — a gap of **−0.053 %**,
inside the 1 % test. The `footprint × storeys` reconstruction essentially reproduces the published
area for the baseline definition; both numbers are stated above.

## Reading the three `layout_assign_*` definitions

All three candidate definitions build a **much smaller** denominator than the published area —
48 to 65 % smaller — because they assign systematically fewer storeys than `auto_storey_count`
for most of the fleet (consistent with F10's low agreement rates: only 23.75–39.78 % of buildings
match `auto_storey_count` at all). Holding energy fixed and shrinking the denominator this much
inflates pooled EUI sharply: adopting `layout_assign_storey_count_naive` as the fleet definition
would move the headline from 153.82 to **442.24 kWh/m²**, a **+288 kWh/m² (+187 %)** move. This is
the direct kWh/m² consequence of each definition, stated without a recommendation.

## Test status

- **C10 — pass.** 29.07 / 39.78 / 23.75 % reproduced exactly.
- **C11 — pass.** Baseline denominator 24,320,581.9 m² vs F6's 24,333,586.4 m² is −0.053 %, inside
  1 %.
