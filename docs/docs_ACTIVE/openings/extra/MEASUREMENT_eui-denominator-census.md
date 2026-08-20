# MEASUREMENT — the EUI denominator census, fleet-wide on run-4

> T05 of `implemenation/PLAN_twenty-items-2026-08-19.md`. Script:
> `scripts/analysis/open01_eui_denominator_census_2026-08-19.py`. Output:
> `openubem/outputs/comparisons/eio_area_vs_derived_fleet.csv` (8,153 rows).

## Method

For every run-4 success (`simulation_status == 'success'`, `floor_area_provenance ==
'eio_simulated'`), `ratio = floor_area_m2 / (footprint_area_m2 × levels)`. `floor_area_m2` is
already the multiplier-aware simulated area resolved from `eplusout.eio`
(`openubem/results/parser.py:264-390`, `resolve_simulated_floor_area()`); `footprint_area_m2 ×
levels` is the naive, non-multiplier-aware denominator this project moved away from at OPEN-01's
closure. All 8,153 successes (100 %) carry `floor_area_provenance == 'eio_simulated'` — none fell
back to the footprint denominator on run 4.

## Control

Required: reproduce OPEN-01's closure figure for `auto` mode (median error factor 1.0000, **99.63
% within ±1 %**) to within a few tenths of a percent.

**Measured on run 4: median ratio 1.000000, 99.74 % within ±1 %.** Δ = +0.11 percentage points —
within tolerance. Control passes.

## Distribution

| statistic | value |
|---|---|
| n | 8,153 |
| median | 1.000000 |
| mean | 1.000262 |
| std | 0.006712 |
| min | 0.999776 |
| max | 1.305716 |
| within ±1 % | 8,132 / 8,153 = **99.74 %** |
| within ±10 % | 8,146 / 8,153 = **99.91 %** |
| within 2× (0.5×–2.0×) | 8,153 / 8,153 = **100.00 %** |
| outside 2× | **0** |

**No building on run 4 has a denominator wrong by 2× or more.** The `auto`-mode denominator is
sound at fleet scale, consistent with (and marginally better than) OPEN-01's own closure figure.

## The 21 buildings outside ±1 %, and the 7 outside ±10 %: one clean pattern

**All 21 buildings outside ±1 % use `zoning_strategy == 'perimeter_core'`, with no exceptions.**
No other zoning strategy contributes an outlier. This is a real, structural — not random — effect
of core/perimeter zone construction (`openubem/geometry/zoning.py`, `core_poly =
footprint_poly.buffer(-perimeter_depth_m)`): splitting a footprint into a shrunk core plus a
perimeter ring and then extruding each separately does not reproduce `footprint_area × levels`
to machine precision, because the buffered core polygon's area is not exactly footprint area minus
the perimeter band's exact area once EnergyPlus's own zone-area accounting closes the loop. The 7
outside ±10 % (max 1.31×, `la_centre / way/423024468`, `RetailStandalone`) are all small
(2–7 storey) `perimeter_core` buildings where the relative geometry effect is largest as a
fraction of a small footprint. None reach 2×; none are named in any register item as a distinct
defect, and this task does not open one.

## The "single highest-yield unrun measurement" lead is now closed — as a false lead

T05's own framing carried forward a lead recorded in OPEN-56's §-section: *"On 1 of 60 buildings
(`nyc_centre/relation_3566904`) writing `Zone.Volume` also moved the reported Total Building Area
from 157,115 to 37,551 m² (÷4.18)"* — flagged as potentially reaching every published EUI's
denominator. **It does not, and the reason is now on record twice, independently.**

This census's own row for that building, taken directly from **production** run-4 data (not the
OPEN-56 side-experiment that raised the lead):

```
osm_id            footprint_area_m2  levels  floor_area_m2  derived_area_m2   ratio
relation/3566904  2682.228115        14.0    37551.22       37551.19          1.000001
```

**`relation_3566904`'s production denominator is internally consistent to 6 significant figures.**
There is no 157,115 m² reading anywhere in its production data — `footprint_area_m2` for this
building is 2,682.23 m², not the 157,115 m² the lead's baseline arm reported. That 157,115 m²
figure belongs to a **different building**, `relation/11171793` (confirmed in this task's own T01
output: `relation/11171793`, `nyc_centre`, 157,115.48 m² footprint). **This matches OPEN-58's own
finding exactly**: the OPEN-56 side-experiment's `relation_3566904` base arm was **contaminated**
by `relation_11171793`'s output (`run_ep()`'s shared-process-cwd defect, `open56_zone_volume_experiment.py`),
byte-identical to fifteen significant figures — not a real EnergyPlus area anomaly. **The lead is
resolved: it was OPEN-58's cross-contamination defect, already measured, not a live threat to the
production EUI denominator.** This census independently confirms that resolution from a second,
untouched dataset (production run-4, not the contaminated experiment).

## Conclusion

**The project's EUI denominator (EnergyPlus's own simulated floor area, via `.eio`) is sound
fleet-wide on run 4.** 99.74 % of buildings match the naive `footprint × levels` figure to within
1 %, reproducing OPEN-01's own closure control. The only outliers are a well-understood,
structural `perimeter_core`-zoning effect (21 buildings, max 1.31×, 0 buildings beyond 2×) — not a
new defect. The one lead that suggested a possible fleet-wide risk to the denominator
(`relation_3566904`'s ÷4.18 area shift) is now closed as a measurement artifact of a different,
already-identified defect (OPEN-58), not a property of the adopted `auto`-mode production data.
This does not reopen, change, or restate F1 (`153.8231 kWh/m²`).

## Output

This document; `openubem/outputs/comparisons/eio_area_vs_derived_fleet.csv` (8,153 rows: cell,
osm_id, archetype_id, zoning_strategy, footprint_area_m2, levels, floor_area_m2,
derived_area_m2, ratio).
