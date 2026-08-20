# MEASUREMENT — OPEN-59 at fleet scale (run 4, all twelve cells)

> T01 of `implemenation/PLAN_twenty-items-2026-08-19.md`. Script:
> `scripts/analysis/open59_fleet_scale_2026-08-19.py`. Output table:
> `openubem/outputs/comparisons/open59_unknown_gap_fleet.csv`. Data:
> `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4/<cell>/results/05_results.csv`
> (F2 — the `results/` subdirectory), all twelve cells, `simulation_status == 'success'` only.

## Controls (must pass before the finding is trusted)

| control | required | measured | pass |
|---|---|---|---|
| `nyc_suburban` Unknown / classified split | 290 / 1,299 | 290 / 1,299 | ✅ |
| Fleet Unknown count | 650 | 650 | ✅ |
| Fleet Unknown pooled total EUI | 107.22 ± 0.01 | 107.21696 | ✅ |
| OPEN-59's own `nyc_suburban` numbers (median per-building) | total 349.4/202.8, DHW 103.5/42.5, heating 140.1/99.0, lighting 26.7/4.0, cooling 25.0/4.5 | total 349.35/202.83, DHW 103.45/42.51, heating 140.11/99.01, lighting 26.73/3.97, cooling 25.01/4.52 | ✅ all reproduce to within rounding |

All controls reproduce. The join and extraction are trusted.

## Fleet-wide result

**650 Unknown buildings across the fleet, 3.7 % of floor area, matching F5.**

Two different statistics give opposite answers on whether Unknown runs hot:

| statistic | Unknown | classified | reading |
|---|---|---|---|
| **Pooled, floor-area weighted** (Σ EUI·area / Σ area) | **107.22** | **155.56** | Unknown is **31 % below** classified |
| **Median per-building** total EUI | **309.95** | **134.08** | Unknown is **2.31×** classified |

Both are reproducible (see controls) and both are computed on the same fleet-wide population from
the same file. **They disagree because they answer different questions, not because either is
wrong.** OPEN-59's own recorded 1.7× is a per-cell (`nyc_suburban`) median-per-building statistic;
F5's 107.22/155.55 is a fleet-wide pooled statistic. The item's §1 row currently states the 1.7×
finding without naming which statistic it is, and that ambiguity is what T01 was asked to resolve.

### Why they disagree: Unknown floor area is dominated by a handful of very large, moderate-EUI buildings

- Median floor area, Unknown buildings: **41.75 m²**. Median floor area, classified: **326.67 m².**
  Most Unknown buildings are small.
- Correlation between floor area and total EUI within the Unknown population: **r = −0.27** —
  larger Unknown buildings run *cooler*, not hotter.
- The **top 10 of 650** Unknown buildings by floor area hold **72.5 %** of all Unknown floor area,
  and their EUIs (74–159 kWh/m²) sit at or below the classified pooled figure of 155.56, not above
  it. Three of the ten are in `nyc_centre` alone (`way/265947358` 173,238 m² @ 90.4;
  `relation/11171793` 157,115 m² @ 74.4; `relation/11171765` 131,151 m² @ 80.4).
- So the pooled fleet statistic is set almost entirely by a small number of huge Unknown buildings
  that run at or below classified intensity, while the median statistic reflects the **typical**
  (small) Unknown building, which does run hot — consistent with OPEN-59's `nyc_suburban` measurement,
  where the Unknown population (n=290) is more homogeneous and dominated by small buildings.

### Per-cell breakdown

Full table in `openubem/outputs/comparisons/open59_unknown_gap_fleet.csv` (26 rows: unknown +
classified × 12 cells + 2 fleet rows). Headline: the pooled Unknown EUI is below classified in
10 of 12 cells that have any Unknown buildings (`la_rural` has zero Unknown buildings); the two
exceptions are `nyc_rural` (271.0 vs 233.4, n=5) and `nyc_suburban` (336.7 vs 179.9, n=290) — both
cells where Unknown floor area is a small fraction of the cell (0.6 % and 5.6 %) and not dominated
by a large building the way `nyc_centre`, `austin_centre` and `la_centre` are.

## Which statistic the item should carry

**Recommendation (not an action — T01 does not open, close or edit the register):** OPEN-59's §1
row should be read as a **median per-building** finding, which reproduces cleanly (2.31× fleet-wide,
up from the recorded 1.7× on `nyc_suburban` alone — the gap is larger, not smaller, at fleet scale
on this statistic). The pooled/floor-area figure (Unknown *below* classified) is a **separate,
real, and equally reproducible fact** driven by a small number of large Unknown buildings, and it
does not contradict the median finding — it describes a different population weighting. Both
belong in the item; neither supersedes the other. This does not touch F1 (153.8231 kWh/m² pooled,
`success` only) directly, since Unknown's 3.7 % floor-area share pooled at 107.22 vs classified's
155.56 is already the mechanism inside F1 that the restatement measured — this task confirms that
number and explains *why* it looks low despite typical Unknown buildings running hot.

## End-use breakdown, fleet-wide (median per-building, Unknown vs classified)

| end use | Unknown median | classified median | ratio |
|---|---|---|---|
| total | 309.95 | 134.08 | 2.31× |
| heating | 115.82 | 34.08 | 3.40× |
| cooling | 24.61 | 11.69 | 2.11× |
| lighting | 26.55 | 26.46 | 1.00× |
| equipment | 37.61 | 43.40 | 0.87× |
| dhw | 79.78 | 7.79 | 10.24× |
| fans | 16.76 | 10.13 | 1.65× |
| pumps | 0.00 | 0.00 | n/a |

Equipment stays cured fleet-wide (Unknown below classified, consistent with OPEN-55's screen
holding). DHW is fleet-wide the largest multiple (10.2×), ahead of heating (3.4×) — at fleet scale
DHW dominates the gap even more than the `nyc_suburban`-only measurement suggested. Lighting is
fleet-wide near parity (1.00×), unlike the 6.7× recorded on `nyc_suburban` alone — that ratio does
**not** generalise; it was a `nyc_suburban`-specific pattern, not a fleet-wide one. Cause is not
diagnosed by this task (T01 was scoped to measurement, not cause).
