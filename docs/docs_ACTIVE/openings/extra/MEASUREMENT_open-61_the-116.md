# MEASUREMENT — OPEN-61 T04: what are the 116 buildings?

**Date:** 2026-08-21
**Input:** `openubem/outputs/comparisons/open61_census_fleet.csv` (8,160 rows)
**Script:** `scripts/analysis/open61_dh_concentration_2026-08-21.py`
**Output:** `openubem/outputs/comparisons/open61_dh_concentration_2026-08-21.csv`
**Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md`, T04

This is a measurement only. No remedy is proposed and no adopted number moves.

## 1. Concentration reproduces — 116 / 70.5 %

Analysable population (rows with non-null `dh_total_kwh`): **8,144** of 8,160, matching the prior
measurement's population exactly.

The 116 are **not** the top 116 buildings ranked by `dh_total_kwh` — a literal rank cut at 116
gives **77.7 %**, not 70.5 %. The 116/70.5 % figure is **archetype-defined**: it is the union of
the two tallest archetypes, `SuperTallBuilding` (n=24) and `TallBuilding` (n=92), 24+92 = **116**.

Two independent recomputations of that union's share, one via `groupby().agg()` and one via a
boolean mask summed directly, agree to machine precision:

| Method | n | Share of fleet DH |
|---|---|---|
| `groupby` + sort by share | 116 | 0.705499 (**70.5 %**) |
| boolean mask, direct sum | 116 | 0.705499 (**70.5 %**) |

**The carried figures reproduce exactly: 116 buildings, 70.5 %.**

## 2. One class, two archetype tiers, one dominant location

The 116 are **one coherent class**, split across two archetypes that are both "very tall
building": **`TallBuilding`** (n=92, lift **70.2×** vs its fleet share of 1.13 %) and
**`SuperTallBuilding`** (n=24, lift **70.2×** vs its fleet share of 0.29 %). Both archetypes are
100 % inside the 116 by construction — there is no dilution.

Cross-tabulated against other dimensions (lift = share of the 116 ÷ share of the fleet):

| Dimension | Dominant value | Fleet share | Share of the 116 | Lift |
|---|---|---|---|---|
| `cell` | `nyc_centre` | 8.96 % | 76.7 % (89/116) | **8.56×** |
| `cell` | `austin_centre` | 5.07 % | 17.2 % (20/116) | **3.40×** |
| `zoning_strategy` | `one_zone_per_floor` | 52.7 % | 100 % (116/116) | 1.90× |
| size (floor-area quartile) | Q4 (largest quartile) | 25.0 % | 100 % (116/116) | **4.00×** |
| `num_zones` | median 26, mean 32.1 (fleet: median 2, mean 5.6) | — | — | — |

**Reading:** the 116 are large, heavily-zoned, tall buildings, overwhelmingly in `nyc_centre`
(76.7 %) with a secondary cluster in `austin_centre` (17.2 %); the remaining five cells together
hold only 7 of the 116. `zoning_strategy` is not a distinguishing feature — `one_zone_per_floor`
already covers over half the fleet — but 100 % of the 116 sit in the largest floor-area quartile.
This is a **tall-residential phenomenon concentrated in one cell**, not a diffuse or accidental
spread across many building types.

## 3. Floor area and pooled EUI effect

- The 116 hold **8,962,794 m²** of the analysable fleet's 24,181,369 m² — **37.06 %** of fleet
  floor area, on **1.4 %** of the buildings. (Large buildings; population share and area share are
  very different numbers here.)
- Pooled total EUI over the 8,144-row analysable population, **without** DH: **152.3017 kWh/m²**.
- Pooled total EUI if DH is added **for the 116 only** (arithmetic on existing columns; nothing
  re-simulated): **166.0384 kWh/m²** — a rise of **+13.7366 kWh/m² (+9.02 %)**.

This is markedly less than the +19.4707 kWh/m² (+12.7 %) that the flat fleet-wide DH headline
would imply — consistent with §5 fact 8's statement that a flat offset is the wrong shape for this
term, since 29.5 % of the DH energy sits outside the 116 entirely, spread thinly across the rest of
the population.

## 4. Conclusion

The 116/70.5 % concentration reproduces exactly under two independent methods. It is **one class,
not several**: tall and super-tall buildings (`TallBuilding` + `SuperTallBuilding`), overwhelmingly
sited in `nyc_centre`, holding 37 % of fleet floor area on 1.4 % of the population. No remedy is
proposed here, per the plan's instruction.
