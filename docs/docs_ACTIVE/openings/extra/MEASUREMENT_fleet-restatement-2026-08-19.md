# MEASUREMENT — Fleet EUI restatement after the run-4 twelve-cell re-run

> **Slug:** `fleet-restatement-2026-08-19` · **Date:** 2026-08-19 · **Author:** director session
> **Plan:** `implemenation/previous/PLAN_close-all-2026-08-19.md`, T04–T05 (CP-2)
> **Status:** MEASUREMENT. States a number and its derivation. Opens no item and applies no fix.

---

## 1. Headline

| | pooled EUI (kWh/m²) | buildings | floor area (m²) |
|---|---:|---:|---:|
| Adopted baseline (`phaseE_elevrb`, OPEN-43, 2026-08-12) | **157.0552** | 8,154 | 23,545,868 |
| Run 4 (`open48_refleet4`, 2026-08-19) | **153.8231** | 8,153 | 24,320,582 |
| **Delta** | **−3.2321** | −1 | +774,714 |

**−2.06 %.** Twelve cells on both sides, same building set on both sides (the osm_id sets are
identical in every cell — verified by symmetric difference, zero rows either way). The one-building
difference is a simulation drop, not a population change; §5 names it.

Pooled means Σ(EUI × floor area) ÷ Σ(floor area) over `simulation_status == success`, never a mean
of cell means — OPEN-43's ruling. The baseline side of this table was recomputed from
`phaseE_elevrb`'s own twelve `05_results.csv` files by the same code path as the run-4 side and
reproduces the published **157.0552** exactly, so the two columns are comparable.

## 2. Per-cell

| cell | n (base) | n (run 4) | fail (base) | fail (run 4) | base EUI | run 4 EUI | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| austin_centre | 413 | 413 | 0 | 0 | 168.77 | 158.16 | −6.29 % |
| austin_rural | 245 | 245 | 0 | 0 | 157.14 | 154.42 | −1.73 % |
| austin_suburban | 437 | 437 | 0 | 0 | 171.50 | 159.20 | −7.17 % |
| austin_urban | 425 | 425 | 0 | 0 | 177.14 | 173.62 | −1.99 % |
| la_centre | 226 | 226 | 0 | 0 | 132.89 | 129.73 | −2.38 % |
| la_rural | 144 | 144 | 5 | 5 | 121.46 | 121.51 | +0.04 % |
| la_suburban | 1343 | 1343 | 0 | 0 | 108.44 | 108.42 | −0.02 % |
| la_urban | 617 | 617 | 1 | 1 | 130.00 | 130.59 | +0.45 % |
| nyc_centre | 738 | 737 | 0 | **1** | 168.11 | 166.57 | −0.92 % |
| nyc_rural | 198 | 198 | 0 | 0 | 234.90 | 233.63 | −0.54 % |
| nyc_suburban | 1589 | 1589 | 0 | 0 | 198.56 | 188.66 | −4.98 % |
| nyc_urban | 1779 | 1779 | 0 | 0 | 152.28 | 148.21 | −2.67 % |

Six of the seven run-4 failures are the same six buildings that failed in the baseline
(la_rural 5, la_urban 1 — all pre-existing temperature-out-of-bounds drops, unchanged in both runs).
The seventh is new and is the subject of §5.

## 3. Attribution — one change accounts for the restatement

Splitting the fleet by whether a building carries the `OpenUBEMUnknown` archetype in either run:

| population | n | base | run 4 | Δ | share of fleet floor area |
|---|---:|---:|---:|---:|---:|
| **Unknown** | 650 | **223.44** | **107.22** | **−52.01 %** | 3.7 % |
| non-Unknown | 7,504 | 154.51 | 155.55 | +0.68 % | 96.3 % |

Counterfactual, holding the Unknown population at its baseline values and taking run 4 everywhere
else, gives **157.9836**. Therefore:

- the **Unknown population contributes −4.1606 kWh/m²** of the fleet delta;
- **everything else contributes +0.9285 kWh/m²**.

The net −3.2321 is the sum of a large downward move on 3.7 % of the fleet's floor area and a small
upward move on the other 96.3 %. The heaviest individual movers are all Unknown buildings falling
from the 450–580 kWh/m² band into the 80–160 band:

| cell | osm_id | base | run 4 |
|---|---|---:|---:|
| nyc_centre | way/265320169 | 576.5 | 92.0 |
| austin_centre | way/967757079 | 561.2 | 138.0 |
| austin_suburban | way/221888647 | 527.4 | 165.6 |
| austin_centre | way/328839208 | 520.7 | 91.0 |
| nyc_centre | way/266149330 | 516.8 | 80.4 |

**Mechanism, cited.** `openubem/semantic/__init__.py`, OPEN-55 ruling B+: `_build_unknown_loads`
now draws each Unknown building's PDE parameters from bounds computed on a *screened* donor pool,
`_UNKNOWN_DONOR_EXCLUDE` removing `SmallDataCenterLowITE`, `SmallDataCenterHighITE`,
`LargeDataCenterLowITE`, `LargeDataCenterHighITE`, `Laboratory`, `FullServiceRestaurant`,
`QuickServiceRestaurant` (plus `Warehouse` for the occupancy column). The excluded archetypes were
the high end of the `lighting_w_m2` and `equipment_w_m2` ranges, so the uniform draw's upper bound
falls and every Unknown building's expected EUI falls with it. A 450–580 kWh/m² unnamed building
was an unnamed building that had drawn data-centre equipment loads.

**Structural changes are a secondary, opposite-signed effect.** Holding the 35 structurally changed
buildings (20 floor-count corrections, 16 archetype flips, 1 drop) at baseline and taking run 4's
draws elsewhere isolates them at **+0.6551 kWh/m²**; the draw-side change is **−3.8872**.

## 4. OPEN-35 verification — 20 of 21, and why

The Scope-B fix selected 21 buildings (`MEASUREMENT_open-35_fallback-agreement.md`, addendum:
austin_centre 5, la_urban 3, nyc_centre 8, nyc_urban 5). Run 4's results carry **20** floor-count
changes: austin_centre 5, la_urban 3, **nyc_centre 7**, nyc_urban 5.

Every one is an upward correction from a bogus `levels = 1.0` to a real storey count — 5 and 45
(austin_centre), 7 (la_urban), 19 (nyc_centre), 6 (nyc_urban). None moved a building the wrong way.
The fleet's floor area rises 774,714 m² (+3.3 %) as a direct consequence, which is why these
corrections raise those buildings' EUI by 45.94 % as a group yet move the pooled fleet number by
only +0.66: they add denominator as fast as they add numerator.

The twenty-first building is **`nyc_centre / way/266034056`** and it is missing from the count
because it did not finish simulating. §5.

## 5. The one new failure is caused by the OPEN-35 fix

`nyc_centre / way/266034056` — a `LargeHotel`, one of the 21 Scope-B buildings, imputed from 1 to 19
storeys. Baseline: 1 storey, footprint 2,933.77 m², `single_zone`, simulated successfully,
307.23 kWh/m². Run 4: dropped.

Chain, from artifacts:

1. The run-4 IDF (`nyc_centre/step3/idfs/way_266034056.idf`, 550 KB, 20 zones) carries
   `Storey 0` … `Storey 18` — 19 storeys, exactly the OPEN-35 imputation.
2. EnergyPlus diverges: `** Severe ** CalcHeatBalanceInsideSurf: The temperature of 1940305.55 C
   for zone="WAY/266034056_F0_CORE"`.
3. The pipeline's own repairs run and fail — zero-area surfaces stripped, then zoning rerouted to
   `one_zone_per_floor`; the retry diverges harder (`20368972.40 C` for
   `zone="WAY/266034056_F0_WHOLE"`).
4. `1 building(s) still failed after reroute (deferred to B2 drop tolerance)`. The row is written
   with the standard dropped-building placeholders — `footprint_area_m2 = 200.0`, `levels = 1.0`,
   empty EUI columns (`v12_cell_pipeline.py:659`, overwritten on success only at `:664`).

**This is a regression introduced by the OPEN-35 fix**, on 1 of the 21 buildings it touches. It is
not a pre-existing degenerate footprint and the `200.0` is a symptom of the drop, not its cause.
Several of its 19-storey siblings (`way/260180778`, `way/266170756`, `way/288448678`) also required
repair before completing, so the fix's interaction with tall imputed geometry is marginal across
that group rather than broken on one building only.

Fleet-EUI cost of the drop: the building contributed 307.23 kWh/m² to the baseline over a
1-storey, 2,933.77 m² floor area. Removing it is a rounding-level effect on 23.5 M m² and is
already inside the −3.2321 above.

## 6. Unknown-archetype population — counts hold

| cell | n | Unknown (base) | Unknown (run 4) | run 4 % |
|---|---:|---:|---:|---:|
| austin_centre | 413 | 37 | 37 | 9.0 % |
| austin_rural | 245 | 7 | 7 | 2.9 % |
| austin_suburban | 437 | 24 | 24 | 5.5 % |
| austin_urban | 425 | 5 | 5 | 1.2 % |
| la_centre | 226 | 15 | 15 | 6.6 % |
| la_rural | 149 | 0 | 0 | 0.0 % |
| la_suburban | 1343 | 2 | 2 | 0.1 % |
| la_urban | 618 | 2 | 2 | 0.3 % |
| nyc_centre | 738 | 31 | **35** | 4.7 % |
| nyc_rural | 198 | 5 | 5 | 2.5 % |
| nyc_suburban | 1589 | 290 | 290 | **18.3 %** |
| nyc_urban | 1779 | 228 | 228 | 12.8 % |

**nyc_suburban's Unknown count is 290 in both runs**, identical — T04's divergence question against
T01's `0/290` is answered: there is no divergence, run 4 reproduces the baseline count exactly. It
sits at 18.3 %, under the LIVE_SMOKE ceiling of 20 % but not by much; a cell that drifts two
percentage points would gate.

Only nyc_centre moves, 31 → 35, and those four are the archetype flips below.

## 7. Archetype flips

| n | base → run 4 | base floor area (m²) |
|---:|---|---:|
| 8 | `MidriseApartment` → `LargeOffice` | 211,412 |
| 4 | `Courthouse` → `OpenUBEMUnknown` | 477,804 |
| 2 | `SmallHotel` → `LargeHotel` | 14,868 |
| 2 | `MidriseApartment` → `MediumOffice` | 15,651 |

The `Courthouse` → `OpenUBEMUnknown` flips deserve naming. Four buildings, together 477,804 m² of
floor area — one of them 157,115 m², the heaviest building in `nyc_centre`. Fleet-wide the floor
area sitting in `OpenUBEMUnknown` rises from 392,848 m² to 870,652 m², a 2.2× increase, while the
building *count* rises only 646 → 650. **The screen is trading identified archetypes for `Unknown`
on some of the largest buildings in the fleet.** Whether that is the screen being correctly
conservative about implausible donors or over-rejecting a legitimate classification is a judgment
this measurement does not make. It is raised to the user in §9.

## 8. What this number still carries — stated without hedging

**The restated 153.8231 is not volume-correct.** OPEN-56 is open and unremedied: every building in
the fleet still simulates with its zone air volume replaced by a 10 m³ stub, 8,160/8,160, because
EnergyPlus computes a negative volume from the geometry it is handed. The fleet-scale cost of that
stub was measured on a 69-building control (X01/X02, 2026-08-19): a fixed per-building offset of
**≈ +1.0 kWh/m²** (mean +0.98 %, median +0.84 %, 65/69 same direction). That correction is **not**
applied here and is **not** inside 153.8231.

A volume-correct fleet on run-4 code would therefore be **≈ 154.8 kWh/m²**. That figure is not
adopted, because OPEN-56's remedy is unauthorised and unimplemented and the offset was measured on
69 buildings rather than 8,160. But the direction and the rough size are known, and 153.8231 should
be read as understating a volume-correct fleet by about that much.

## 9. Limits, and what is not established

1. **The attribution in §3 is a decomposition, not a controlled experiment.** Four code changes
   landed together (OPEN-35 geometry wiring, OPEN-49 `_per_building_rng`, OPEN-55 donor screen,
   OPEN-01/OPEN-56-adjacent reporting changes). §3 separates the Unknown population from the rest
   arithmetically and names OPEN-55's screened bounds as the mechanism with a code citation, but no
   run isolates one change with the other three reverted. The Unknown/non-Unknown split is clean
   enough that the conclusion is not in doubt; the exact split between OPEN-55 and OPEN-49 *within*
   the Unknown population is not measured.
2. **The 4 `Courthouse` → `Unknown` flips are unadjudicated** (§7) and are a director/user decision,
   not a measurement outcome.
3. **The OPEN-35 regression on `way/266034056` (§5) has no remedy here.** Its mechanism is
   established; whether the fix should be scoped to exclude it, or the tall-geometry path repaired,
   is not decided.
4. **Two earlier director claims made during this run are retracted**, recorded so they do not
   propagate: (a) a "null-island centroid" defect signature — `centroid_lat` is near zero for every
   building in every cell in both runs, so it is not a WGS84 latitude and near-zero is not a
   signature of anything; (b) the reading of `way/266034056` as a pre-existing degenerate footprint
   correctly excluded — it is a new drop caused by the OPEN-35 fix, per §5.

## 10. Provenance

- Baseline: `docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/05_results.csv`
  (twelve cells; note this layout has no `results/` subdirectory).
- Run 4: `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4/<cell>/results/05_results.csv`.
- Driver log and per-cell logs: `%LOCALAPPDATA%/Temp/open48_run4/`.
- `austin_urban` and `la_rural` each failed once on an SSH transport fault and were re-run solo;
  both returned complete results. Post-mortem: `INVESTIGATION_open48-run4-cell-failures.md`.
- Code under test: working-tree diff against HEAD of `openubem/geometry/footprint.py`,
  `openubem/idf/builder.py`, `openubem/results/{__init__,aggregator,parser}.py`,
  `openubem/semantic/__init__.py`, `scripts/validation/v12_cell_pipeline.py`.
