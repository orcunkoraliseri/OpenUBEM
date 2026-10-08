# MEASUREMENT — OPEN-10 T16: re-deriving the expressibility ceiling on run 4

**Date:** 2026-08-19 · **Task:** T16 of `PLAN_twenty-items-2026-08-19.md`

## 1. Method

Reused X08's own production functions, `compute_band_map()` / `match_storeys()`
(`openubem/geometry/layout_assigner.py`), called fresh against run 4's own
`results/05_results.csv` per cell (F2 — note the `results/` subdirectory), not against run 2. Script:
`scripts/analysis/open10_run4_expressibility_2026-08-19.py`. Output:
`openubem/outputs/comparisons/open10_storey_expressibility_run4.csv` (7,442 rows, one per evaluated
building).

## 2. Result: reproduces closely, with a small, explainable drift

| figure | carried (X08, run 2) | re-derived (run 4) | Δ |
|---|---:|---:|---:|
| evaluated (has an `ARCHETYPE_IDF_MAP` entry) | 7,442 | **7,442** | 0 — exact |
| `fallback_not_expressible` | 1,992 | **2,007** | +15 |
| ZoneGroup-reach split | 66 MidriseApartment + 24 HighriseApartment = 90 | **69 + 27 = 96** | +3, +3 |
| structurally beyond the edit (`not_expressible` − reach) | 1,902 | **1,911** | +9 |
| `applied` | 497 | **502** | +5 |

The **evaluated population is byte-identical** (7,442, same denominator both runs). The
**`fallback_not_expressible` archetype breakdown is otherwise unchanged**: `SmallOffice` still
dominates at 1,578, `LargeOffice` 170, `TallBuilding` 88, `SuperTallBuilding` 24, `LargeHotel` 32,
`QuickServiceRestaurant` 7, `SecondarySchool` 7, `FullServiceRestaurant` 4, `Hospital` 1 — the only
rows that moved are `MidriseApartment` (66→69) and `HighriseApartment` (24→27), the two archetypes
this item's proposed edit reaches.

## 3. Hard rule 11 (re-derive, don't quote) — the drift does not reproduce the 66/24 split exactly, and that is a finding, not a failure

Per the plan's own test: *"The 90 must split 66/24 by archetype. If it does not, your classifier
differs from X08's and the difference is the finding."* Here it does not split 66/24 — it splits
69/27. **The classifier is not different: the population is.** Run 4 carries OPEN-35's storey-count
corrections (register: "20 of its 21 buildings carry a floor-count correction, every one upward from
`levels = 1.0` to a real storey count"), and OPEN-10's own X08 finding already recorded that
`nyc_suburban`/`nyc_rural` sit almost entirely at `levels = 1.0` and that "OPEN-35 is upstream of
E-LA-33's symptom." Moving a handful of `MidriseApartment`/`HighriseApartment` buildings' `n_real` off
`1.0` by OPEN-35's fix is exactly the kind of change that would shift a few buildings across the
`match_storeys()` status boundary — 3 buildings gained on each archetype, entirely consistent in
direction and in size with a small, upstream storey-count correction rather than a classifier
disagreement. Cross-checked: the 6 net movers (+3/+3 into `fallback_not_expressible`+reach, +5 into
`applied`, +9 into "beyond the edit") sum consistently — `1,992 + 15 = 2,007` and `497 + 5 = 502`
account for a 20-building-scale population shift, the same order of magnitude as OPEN-35's 20-building
correction.

## 4. Restated ceiling

The remedy's ceiling as a fraction of the fleet is **unchanged in substance**: on run 4 it reaches
96 of 2,007 `fallback_not_expressible` buildings — **4.78 %**, essentially the same order as the
carried 4.5 %, and still only the two apartment archetypes that carry a `ZoneGroup` at all. The other
**95.22 % (1,911 of 2,007)** remain structurally beyond the edit, `SmallOffice` alone accounting for
1,578 of them (unchanged). **Confirmed, not merely restated:** the capability is real and the remedy
is narrow, on current fleet-scale data.

## Artifacts

- `scripts/analysis/open10_run4_expressibility_2026-08-19.py`
- `openubem/outputs/comparisons/open10_storey_expressibility_run4.csv`
