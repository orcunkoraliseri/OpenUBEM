# MEASUREMENT — end-use decomposition of the 48 (T01) and the OPEN-59 four-column bounds screen (T02)

**Slug:** `gap-decomposition` · **Date:** 2026-08-19 · **Plan:** `implemenation/previous/PLAN_gap-decomposition-2026-08-19.md`, T01-T02, CP-1.
**Scope:** measurement only. Nothing opened, closed, struck or retired. Recommendations only.

---

## 1. T01 — end-use decomposition of the 48 `layout_assign` `.sql` files

### 1.1 Reconciliation check — FAILS. The decomposition against `total_eui_kwh_m2` is not usable.

Per building: `Total End Uses` (EnergyPlus ABUPS table, all fuels, GJ -> kWh at x277.7778) vs
`total_eui_kwh_m2 x floor_area_m2` from `openubem/outputs/comparisons/open03_untrimmed_sample_join.csv`.

- **6 / 48 (12.5 %) reconcile within 2 %.**
- Error distribution across all 48: median **4.71 %**, mean **17.56 %**, worst **192.28 %**
  (`la_centre / way/427817563`).
- This is not an extraction bug. It is a real, diagnosed mismatch between two different
  production quantities.

**Mechanism, confirmed component-by-component on `la_centre/way/427817563`** (3 zones, 4 levels,
Zone Multiplier = 4.0, confirmed by direct query of the `Zones` table):

| end use | source in `total_eui_kwh_m2` (`openubem/results/parser.py:398-505`) | matches ABUPS? |
|---|---|---|
| cooling, heating, fans, pumps, DHW | RunPeriod **meters** (`Cooling:Electricity`, etc.) — multiplier-aware | yes, to <0.01 % |
| lighting, equipment | **hourly zone variables** (`Zone Lights/Equipment Electricity Energy`) — **not** multiplier-aware | **no — off by exactly the zone multiplier (4.00x here)** |

`floor_area_m2` (from `resolve_simulated_floor_area`) **is** multiplier-aware, so dividing an
unmultiplied lighting/equipment kWh sum by a multiplier-aware area silently undercounts those two
end uses by the multiplier factor whenever `num_zones < levels` (a shape zoned once, then repeated
via multiplier for upper floors — the `layout_assign` norm). 42/48 buildings in this sample use a
multiplier (`num_zones < levels`); the 6 that reconcile are exactly the 6 with `num_zones >= levels`
(no multiplier used).

**This is a known, already-implemented check that was not applied to this sample.**
`openubem.results.parser.check_building_integrity()` (`parser.py:602-646`) already performs an
ABUPS-vs-hourly cross-check for lighting+equipment and returns `abups_ok=False` for exactly this
kind of building — verified directly: `check_building_integrity()` on `way/427817563` returns
`{'abups_ok': False, 'meter_ok': False, 'gas_zero': False}`. The T01/join-CSV sampling pipeline
(`scripts/analysis/open03_untrimmed_layout_assign_sample_2026-08-19.py`) calls `parse_building()`
only, not `check_building_integrity()`, so this defect was silently present and unflagged in the
join CSV.

**Consequence, per the plan's own stop rule:** the `total_eui_kwh_m2` / `gap_pct` figures in the
join CSV understate lighting+equipment for 42 of the 48 buildings, so **the decomposition cannot be
used to test OPEN-03's attribution by comparing against `total_eui_kwh_m2` or `gap_pct`.** No
further conclusion is drawn from that comparison.

🔴 **New, larger-scope implication, flagged but not investigated further (out of this task's
scope):** the published **-25 %** `layout_assign`-vs-`auto` gap
(`extra/MEASUREMENT_open-03-18_untrimmed-sample.md` SS4) was itself computed from
`total_eui_kwh_m2` on the `layout_assign` side. If `layout_assign` builds disproportionately use
zone multipliers (87.5 % of this sample does) and `auto` builds do not, part of that -25 % gap
could be this same multiplier artifact rather than a real geometry/loads difference. This is a
hypothesis, not a finding — it needs `auto`'s zoning strategy checked, which this task did not do.

### 1.2 The ABUPS split itself is still valid (self-consistent, correctly multiplier-scaled)

The mismatch above is between `total_eui_kwh_m2` and the ABUPS total — **not** an error inside the
ABUPS extraction, which reads a single production table directly and needs no cross-reference to be
internally consistent. Reported below as descriptive-only, **not** tied to `gap_pct` or
`total_eui_kwh_m2`.

**Sample-wide split, all 48, kWh (state n on every line):**

| end use | share of total (n=48) |
|---|---:|
| Interior Equipment | 32.45 % |
| Fans | 21.17 % |
| Cooling | 15.63 % |
| Interior Lighting | 13.86 % |
| Heating | 9.09 % |
| Water Systems | 7.08 % |
| Pumps | 0.73 % |

Lighting + Equipment = **46.31 %** of total site energy across all 48.

**MidriseApartment (n=9, smallest observed gap, -12.6 %) vs Office = Small+Medium+Large (n=31,
largest observed gap, -34.9 %):**

| end use | MidriseApartment (n=9) | Office (n=31) |
|---|---:|---:|
| Interior Equipment | 36.29 % | 49.83 % |
| Water Systems | 37.93 % | 5.37 % |
| Fans | 7.48 % | 12.64 % |
| Cooling | 9.08 % | 14.54 % |
| Interior Lighting | 4.92 % | 7.47 % |
| Heating | 4.30 % | 8.47 % |
| Pumps | 0.00 % | 1.69 % |
| **Lighting + Equipment** | **41.21 %** | **57.30 %** |

Office buildings run far more equipment- and lighting-heavy; MidriseApartment is dominated by Water
Systems (DHW), which is a materially different mechanism from OPEN-03's vintage-loads claim.

### 1.3 Is lighting+equipment large enough for "roughly half the gap"? No — bounded well short.

Using the n=12-archetype vintage ratios already measured (`extra/MEASUREMENT_open-03_vintage-at-head.md`
SS5: lighting **1.722x**, equipment **1.064x**, occupancy **1.000x**), the maximum possible reduction
in *total* site energy from correcting lighting and equipment to real vintage — holding every other
end use fixed, i.e. the most generous case for OPEN-03's claim — is:

`L x (1 - 1/1.722) + E x (1 - 1/1.064)`, using each group's own ABUPS lighting/equipment shares:

| group | n | L share | E share | max total reduction if fully vintage-corrected |
|---|---:|---:|---:|---:|
| ALL 48 | 48 | 13.86 % | 32.45 % | **7.76 %** |
| MidriseApartment | 9 | 4.92 % | 36.29 % | **4.25 %** |
| Office | 31 | 7.47 % | 49.83 % | **6.13 %** |

"Roughly half" of a 25 % gap needs about 12.5 percentage points of reduction; half of the office
subsample's own -34.9 % gap needs about 17.5 points. **The best case here — Office, the highest-gap
group, with equipment at essentially half its total energy — tops out at 6.13 %, under half of what
"half the gap" requires and well under half of even the whole-sample 25 %.** This computation uses
only the internally-consistent ABUPS shares (SS1.2), not the unreliable `total_eui_kwh_m2`/`gap_pct`
comparison from SS1.1, so it is not contaminated by the reconciliation failure.

**This contradicts OPEN-03's "roughly half" attribution as stated.** Lighting and equipment are
large shares of total energy, but the *vintage-driven excess within them* is not large enough to
move a 25-35 % total gap by half, on this sample's own end-use mix.

**Artifact:** `openubem/outputs/comparisons/open03_enduse_by_building.csv` (one row per building,
end-use kWh + reconciliation columns; 48 rows, `extract_status=ok` for all 48).

---

## 2. T02 — the OPEN-59 four-column PDE bounds screen

Structurally copied from OPEN-55 SS3, extended from equipment alone to all four Unknown-building PDE
columns (`lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person`, `wwr`,
`openubem/semantic/__init__.py:256`). Regenerated the deterministic per-building draw for the same
290 `OpenUBEMUnknown` buildings in `nyc_suburban` (source: `03_idf_manifest.parquet` from the OPEN-55
acceptance-test run `open48_refleet3_t02a4`) using the production functions directly
(`_build_unknown_loads`, `_per_building_rng`, `_get_cross_archetype_loads`,
`openubem/semantic/__init__.py:223-321,490-493`) — no cluster, no re-simulation.

Cross-check: the regenerated equipment/occupancy/lighting draws are bit-identical to
`extra/MEASUREMENT_open-55_acceptance-test-attempt4.md` SS3 (e.g. equipment median
9.152907 W/m², occupancy median 31.069510 m2/person, lighting median 10.869178 W/m2) — confirms the
regeneration is correct.

| column | donor bound | drawn min / median / max | n | out of bounds |
|---|---|---|---:|---:|
| `lighting_w_m2` | [3.44, 18.30] | 3.4541 / 10.8692 / 18.2464 | 290 | **0** |
| `equipment_w_m2` | [2.58, 16.15] | 2.5902 / 9.1529 / 16.0668 | 290 | **0** |
| `occupant_m2_per_person` | [4.65, 51.10] | 4.7437 / 31.0695 / 51.0496 | 290 | **0** |
| `wwr` | [0.10, 0.40] | 0.1006 / 0.2427 / 0.4000 | 290 | **0** |

**0 of 4 columns show any out-of-bounds draw, across all 290 buildings.** All four columns draw
from the same screened donor pool (`_UNKNOWN_DONOR_EXCLUDE`, plus `Warehouse` for occupancy) —
confirmed by reading `_build_unknown_loads` (`openubem/semantic/__init__.py:270-276`): the screen was
never equipment-only at HEAD, it already applies uniformly to all four PDE columns.

**This directly answers OPEN-59's hypothesis 1 (sibling of the OPEN-55 widened-bounds defect,
column-by-column): refuted at HEAD.** No column is drawing from an unscreened pool. Per the plan's
own instruction, this is reported as a clean, decisive result favouring **hypothesis 2 — the Unknown
donor pool (post-screen `MediumOffice`-anchored cross-archetype table) is genuinely higher-intensity
than the buildings it stands in for, a calibration question, not a bounds defect.** No further
defect hunt was performed, per plan instruction.

**Artifact:** `openubem/outputs/comparisons/open59_pde_bounds_screen.csv` (one row per column).

---

## 3. Recommendations to the director (not acted on here)

- **T01:** the `total_eui_kwh_m2` metric undercounts lighting+equipment for any building simulated
  with a zone multiplier (`num_zones < levels`) — recommend the director decide whether
  `check_building_integrity()` should gate `parse_building()` output fleet-wide, and whether the
  published -25 % `layout_assign`-vs-`auto` gap needs the same multiplier check applied to rule the
  artifact in or out. Not investigated here — flagged only.
- **T01:** OPEN-03's "roughly half the gap" attribution is measurably too large a claim on this
  sample's own end-use mix (max 6.13-7.76 % of total, vs "half of 25-35 %" needing 12.5-17.5 points).
  Recommend the register capture this as a measured contradiction, not a resolved close.
- **T02:** OPEN-59 hypothesis 1 (partial/unscreened column screen) is refuted. Recommend the
  director route further OPEN-59 work toward hypothesis 2 (donor-pool calibration), not another
  bounds-screen fix.
