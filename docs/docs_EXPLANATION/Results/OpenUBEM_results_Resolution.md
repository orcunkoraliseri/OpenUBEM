# OpenUBEM — Simulation-Resolution Results & Comparison

**What this document is:** a results report for the user-selectable thermal-zoning
`resolution_mode` feature. It presents the cross-mode simulation comparison over the full
12-cell / 8,160-building validation matrix, the load-conservation integrity check that gated
the feature, the AUTO-baseline fleet results, and the measured-data validation — with the
figures embedded. For the plain-language feature description see
[`OpenUBEM_fundamentals.md` §5.1](OpenUBEM_fundamentals.md); for the binding zoning rule see
[`SIMULATION_RESOLUTION_zoning_by_building.md`](../../docs_DONE/SETUP/Simulation_Resolution/resolution_sets/SIMULATION_RESOLUTION_zoning_by_building.md);
for the task/plan record see
[`PLAN_resolution_mode_switch.md`](../../docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md).

Data + figures presented here live under `openubem/outputs/comparisons/`,
`openubem/outputs/simulationResults/`, and `openubem/outputs/validaitonResults/`.

---

## 1. The resolution modes

OpenUBEM builds **one EnergyPlus IDF per building** on the building's **real footprint** and
simulates it for a full year (8,760 hourly steps). What changes between modes is only the
**thermal zoning** inside that single IDF. The EUI denominator is
`footprint_area_m2 × num_floors` in **every** mode, so a cross-mode difference is a genuine
physics difference, never a normalization artefact.

| Mode | Zoning applied to every building | Zones/building | Fidelity | Status |
|---|---|---|---|---|
| **`building`** | 1 zone for the whole building (full height) | 1 | lowest | ✅ validated |
| **`floor`** | 1 zone per floor, all archetypes | `num_floors` | medium | ✅ validated |
| **`fast_zone`** | core + perimeter per floor, **all** archetypes regardless of area | ~5 × `num_floors` | high | ✅ validated |
| **`auto`** *(default)* | adaptive — picks per building by the §1 rule | mixed | validated baseline | ✅ baseline |
| **`layout_assign`** *(added 2026-08-05)* | substitutes a scaled DOE/ASHRAE 90.1 prototype for the whole building, rather than zoning the building's own footprint | real DOE-prototype count (1–256, archetype-specific) | n/a — a different method, not a finer zoning tier | ⚠️ adopted for zone/HVAC-topology studies — **not certified for fleet-level EUI reporting**, see §10 |
| **`zone`** | `fast_zone` shape **plus** per-archetype load labelling | ~5 × `num_floors` | highest | ⏸ deferred |

> **Note, added 2026-08-05:** the `layout_assign` row above is an amendment. §§3–7 below remain the
> 2026-07-01 four-mode record (`auto`/`building`/`floor`/`fast_zone`) and are unchanged; `layout_assign`'s
> own structural comparison is new §10.

`building` and `floor` reuse the existing `single_zone` / `one_zone_per_floor` strategies;
`fast_zone` extends the core/perimeter slicing that `auto` already applies to large commercial
onto **all** archetypes. `zone` (per-archetype interior-load labelling) is deferred — deep
research (`deepResearch/layoutMapping/`) found that reproducing each prototype's exact zone
count changes annual EUI < 5% and is fragile on real footprints, so only the load-meaning
half is worth building later.

---

## 2. How the comparison was run

- **Matrix:** 3 cities × 4 urban-density cells = **12 cells**, **8,160 buildings**, each
  simulated under all four active modes (`auto`, `building`, `floor`, `fast_zone`).
- **Cities / climate zones:** Los Angeles (CZ 3B, cooling-led), Austin (CZ 2A, mixed), New
  York (CZ 4A, heating-led).
- **Input-invariant:** loads, schedules, envelope, HVAC and weather are held **bit-identical**
  across modes — only the zoning geometry varies — so the comparison isolates the zoning effect
  (the Step-3 guarantee proven by the load-conservation test).
- **Engine:** EnergyPlus 23.1, annual 8,760-hour run, one IDF per building.
- **Data:** cluster-run cells (nyc_centre/urban/suburban/rural, la_centre) harvested from
  Concordia Speed; the remaining 7 cells run locally. Combined tables:
  `openubem/outputs/comparisons/t08_all_modes_eui.csv` (5 cluster cells × 4 modes) +
  `t08_local_remainder_eui.csv` (7 local cells × 4 modes).

---

## 3. Headline: internal loads conserve across modes

The first thing a resolution switch must guarantee is **energy conservation** — the same
building, simulated at any zoning resolution, must account for the same total floor area and
therefore not gain or lose internal load. A single-zone (`building`) model whose one zone
covered only the footprint (one floor) would under-count a multi-floor building's loads by
`1/num_floors`; catching and fixing that was the gating check for this feature (CP4).

**Conservation test — per-building matched ratio of `building`-mode to `floor`-mode total site
EUI** (a value near 1.0 = conserved; the old defect produced ~0.2 for a 5-floor building):

| Cell | N | median(building/floor) | median(building/auto) | Buildings below 0.35 |
|---|---|---|---|---|
| nyc_centre | 738 | 0.861 | 0.897 | 0 |
| nyc_urban | 1779 | 0.934 | 0.964 | 0 |
| nyc_suburban | 1589 | 1.000 | 1.002 | 0 |
| nyc_rural | 198 | 1.000 | 1.033 | 0 |
| la_centre | 225 | 0.955 | 0.950 | 0 |
| la_urban | 617 | 0.959 | 0.986 | 0 |
| la_suburban | 1343 | 0.964 | 1.014 | 0 |
| la_rural | 143 | 0.958 | 1.027 | 0 |
| austin_centre | 413 | 1.000 | 1.037 | 0 |
| austin_urban | 425 | 0.953 | 1.019 | 0 |
| austin_suburban | 437 | 0.954 | 1.026 | 0 |
| austin_rural | 245 | 1.000 | 1.070 | 0 |

**Result: PASS.** Every cell sits in the healthy 0.75–1.05 band, and **zero** of the 8,160
buildings show the `1/num_floors` under-count signature. The remaining sub-1.0 gap in the
dense/tall cells (nyc_centre 0.861) is **expected physics**, not lost energy — see §5.

---

## 4. Cross-mode EUI comparison

Because a handful of buildings in sparse rural cells carry very high absolute intensities, the
**median** is the robust cross-mode statistic (means are outlier-skewed — e.g. la_rural
`building` mean is inflated by a few units while its median, 130.7, equals the `auto` median).
Median total **site** EUI (kWh/m²·yr) by cell and mode:

| Cell | `auto` | `building` | `floor` | `fast_zone` |
|---|---|---|---|---|
| austin_centre | 135.6 | 124.5 | 141.3 | 158.7 |
| austin_urban | 121.0 | 119.2 | 131.7 | 133.6 |
| austin_suburban | 119.9 | 123.6 | 129.9 | 136.9 |
| austin_rural | 117.8 | 125.5 | 125.5 | 134.3 |
| la_centre | 143.1 | 105.0 | 141.4 | 146.4 |
| la_urban | 103.9 | 101.4 | 108.0 | 110.4 |
| la_suburban | 106.6 | 108.0 | 112.1 | 113.9 |
| la_rural | 130.7 | 130.7 | 140.5 | 145.0 |
| nyc_centre | 180.1 | 138.6 | 171.5 | 186.1 |
| nyc_urban | 144.7 | 137.8 | 148.6 | 149.2 |
| nyc_suburban | 205.5 | 205.4 | 205.4 | 205.6 |
| nyc_rural | 159.6 | 163.9 | 163.9 | 166.4 |

Three consistent patterns:

1. **Ordering `building` ≤ `auto`/`floor` ≤ `fast_zone`.** Finer zoning exposes more perimeter
   surface and prevents core/perimeter load cancellation, so it reports **higher** heating/cooling;
   the lumped single zone reports the least.
2. **Effect concentrates in tall/dense stock.** The centre cells (nyc_centre, la_centre) show
   the largest `building`-vs-finer gap (nyc_centre `building` 138.6 vs `fast_zone` 186.1); the
   low-rise cells (suburban/rural) are nearly mode-invariant (nyc_suburban ≈ 205 in all modes).
3. **`auto` tracks the mid-fidelity modes**, as designed — it applies core/perimeter only where
   it matters and single-zone/per-floor elsewhere.

![Median site EUI by cell and mode](../../openubem/outputs/comparisons/t08_mode_cell_median_eui.png)
*Median total site EUI per cell, one bar group per resolution mode.*

![Per-city per-mode EUI distributions](../../openubem/outputs/comparisons/t08_mode_city_eui_boxplots.png)
*Building-level EUI distribution by city and mode — spread narrows in low-density cells, widens
in dense centres where zoning resolution bites.*

![End-use breakdown by mode and city](../../openubem/outputs/comparisons/t08_enduse_by_mode_city.png)
*End-use decomposition by mode. The mode-sensitive components are heating, cooling and fans
(zoning-driven surface/airflow effects); lighting, equipment and the service loads
(DHW/cooking/refrigeration) are area-driven and conserve across modes.*

### 4.1 Per-mode spatial comparison

The tables and box-plots above compare the modes **statistically**; the maps below show them
**spatially** — the same building footprints, one panel per mode, on a shared color scale, so the
resolution effect is visible building-by-building. Only the **four simulated modes** appear:
`zone` is deferred (`NotImplementedError` in `zoning.py`) and was never run, so it has no data and
no panel — the comparison is 4 options, not 5.

![nyc_centre — EUI by resolution mode](../../openubem/outputs/comparisons/t08_modes_map_nyc_centre.png)
*NYC centre (CZ 4A, tallest stock) — `auto` | `building` | `floor` | `fast_zone`. The `building`
panel is visibly paler (lower EUI) than `fast_zone`; the effect is strongest on the tall towers —
the spatial signature of coarse-mode under-prediction.*

![la_centre — EUI by resolution mode](../../openubem/outputs/comparisons/t08_modes_map_la_centre.png)
*LA centre (CZ 3B) — same four modes, same buildings, shared scale.*

![austin_centre — EUI by resolution mode](../../openubem/outputs/comparisons/t08_modes_map_austin_centre.png)
*Austin centre (CZ 2A) — same four modes. (Scale is stretched by one very-high-EUI
QuickServiceRestaurant, the 98th-percentile anchor.)*

These are generated by `scripts/validation/t08_modes_map.py` from the per-mode CSVs joined to the
building footprints (≥ 99.6% osm_id match per cell). The three **centre** cells are shown because
resolution matters most in dense/tall stock; the low-density cells are near mode-invariant (see the
box-plots) and add little spatially.

---

## 5. Why the modes differ — expected physics, not error

The deep-research set (`RESULT_08/09/12/13`) predicts the direction and size of every effect
seen above; they are correct physics that must be read as expected, not "fixed":

- **Annual heating:** a single lumped zone lets core heating and perimeter cooling cancel, so
  `building` under-predicts heating ~10–26% vs finer zoning; expect `fast_zone ≥ floor ≥ building`.
- **Top-floor solar / cooling:** `building` averages shaded lower and unshaded upper walls,
  under-predicting upper-floor solar gain ~15–25% and shifting the cooling peak 1–2 h.
- **Peak / equipment sizing:** coarse modes can mis-size peak substantially — `building`/`floor`
  are for **energy screening and stock totals, not peak-demand or equipment-sizing studies**
  (that is the deferred `zone` mode's job).
- **District-scale wash-out:** the building-scale zoning effect (5–15%) shrinks to **< ~2.3%**
  once aggregated to city scale — resolution is a *secondary* EUI driver behind
  HVAC/occupancy/envelope (30–50%).

The external-literature envelopes that bracket these numbers are commissioned in the
`deepResearch/literatureValidation/` prompt set (V01–V06); the in/out-of-envelope comparison is
the planned follow-on.

---

## 6. The AUTO baseline — fleet results

`auto` is the validated production default that produced the 8,160-building benchmark. Its
per-cell fleet outputs (EUI maps, archetype breakdowns, rank curves, carbon) live in
`openubem/outputs/simulationResults/` — one set per cell. The city-wide spatial view (building
footprints on the CARTO basemap, all 12 cells, shared scale):

![Building total EUI — 12-cell overview grid (auto baseline)](../../openubem/outputs/comparisons/phaseE_overview_grid.png)
*AUTO-mode building total EUI across the full 3-city × 4-density matrix — the validated baseline.
Compare any cell here against its per-mode panel in §4.1.*

![NYC centre — EUI by archetype](../../openubem/outputs/simulationResults/nyc_centre__eui_violin_by_archetype.png)
*Site-EUI distribution by archetype — resolution-sensitive cohorts (offices, tall residential)
carry the widest spread.*

![Austin centre — carbon by archetype](../../openubem/outputs/simulationResults/austin_centre__gwp_stacked_by_archetype.png)
*Stacked global-warming-potential by archetype (Austin centre) — electricity end-uses × eGRID
2022, gas × 0.181 kg CO₂e/kWh.*

The full per-cell set (`<cell>__eui_map`, `__archetype_eui_bar`, `__eui_rank_curve`,
`__eui_violin_by_archetype`, `__gwp_stacked_by_archetype`) is available for all 12 cells.

---

## 7. Validation against measured data

The AUTO baseline is scored **report-only** (never tuned to pass) against city disclosure data
(NYC LL84, LA EBEWE), a CBECS-2018 regional proxy for Austin, and the national CBECS 2018
survey. Headline: city-overall EUI within **±9%** of measured in all three cities, with a
zero-fitted-parameter model — full record in [`OpenUBEM_fundamentals.md` §7.2](OpenUBEM_fundamentals.md)
and the validation docs. The validation diagnostics live in `openubem/outputs/validaitonResults/`:

![Round-trip scatter](../../openubem/outputs/validaitonResults/roundtrip_scatter.png)
*Modeled vs measured/reference EUI — the round-trip agreement scatter.*

![Gap decomposition](../../openubem/outputs/validaitonResults/gap_decomposition.png)
*Decomposition of the modeled-vs-measured gap into contributing sources.*

![Climate signal](../../openubem/outputs/validaitonResults/climate_signal.png)
*Climate response — EUI vs climate zone, confirming the physically-correct city ordering
(LA < Austin < NYC).*

![Ranked deviation](../../openubem/outputs/validaitonResults/dev_ranked_bar.png)
*Per-archetype ranked deviation from the measured/reference benchmark.*

> Note: because the zoning effect washes out to < ~2.3% at city scale (§5), the choice of
> resolution mode does **not** move the city-level validation verdict — the ±9% agreement holds
> under `auto`; the coarser modes are provided for screening speed, not for re-passing validation.

---

## 8. Reproducibility & provenance

| Artifact | Path |
|---|---|
| Cross-mode EUI, 5 cluster cells × 4 modes | `openubem/outputs/comparisons/t08_all_modes_eui.csv` |
| Cross-mode EUI, 7 local cells × 4 modes | `openubem/outputs/comparisons/t08_local_remainder_eui.csv` |
| Per-(cell,mode) mean/median summary | `openubem/outputs/comparisons/t08_mode_cell_summary.csv` |
| Cross-mode aggregate figures | `openubem/outputs/comparisons/t08_mode_cell_median_eui.png`, `t08_mode_city_eui_boxplots.png`, `t08_enduse_by_mode_city.png` |
| Per-mode spatial maps (§4.1) | `openubem/outputs/comparisons/t08_modes_map_{nyc_centre,la_centre,austin_centre}.png` — via `scripts/validation/t08_modes_map.py` |
| AUTO baseline overview grid | `openubem/outputs/comparisons/phaseE_overview_grid.png` — via `scripts/validation/phaseE_overview_grid.py` |
| AUTO fleet figures (per cell) | `openubem/outputs/simulationResults/` |
| Validation diagnostics | `openubem/outputs/validaitonResults/` |
| Zoning rule (binding spec) | `docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/SIMULATION_RESOLUTION_zoning_by_building.md` |
| Task/plan + progress log | `docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md` |
| `layout_assign` artifacts (added 2026-08-05, §10) | `openubem/outputs/comparisons/{layout_assign_vs_resolution_modes,t20_layout_assign_eui,t20_r10_reach_change,r06c_local_results}.csv`, `scratchpad/f11_transformer_check_v3.csv`, `docs/docs_DONE/SETUP/layoutAssigner/figures/` |

All modes were simulated from the same committed working tree; the load-conservation and
freshness checks in §3 were verified building-by-building at harvest (e.g. the 67-floor tower
way/265875648 reads InteriorLights 26.47 kWh/m² in `building` mode, matching the raw
EnergyPlus SQL exactly).

---

## 9. Where to go next

| You want… | Read |
|---|---|
| The plain-language feature description | `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §5.1 |
| The binding zoning rule | `docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/SIMULATION_RESOLUTION_zoning_by_building.md` |
| The task list + full progress log | `docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md` |
| The external-validation prompt set | `docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/deepResearch/literatureValidation/` |
| `layout_assign` structural comparison (added 2026-08-05) | §10 above, and the frozen arc record, `docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md` |
| Current project status | `docs/PROJECT_CHECKLIST.md` |

---

## 10. `layout_assign` — structural comparison (added 2026-08-05)

**This is an amendment, not a rewrite.** §§1–9 above remain the 2026-07-01 four-mode record
(`auto`/`building`/`floor`/`fast_zone`), unchanged. `layout_assign` was run separately, at full fleet
scale, by the storey-matching arc that closed 2026-08-04. Everything in this section is re-verified
directly from the named file before being printed here; the full derivation and every supporting
number live in the frozen arc record,
[`layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md`](../../docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md)
(§8/§9), which this section is kept consistent with rather than re-derived independently.

### 10.1 What it is and how it differs

**An analogy for the two similarly-named tools.** `layoutGenerator` is a tailor who measures the
building and cuts the cloth to its body — right shape by construction, but building that tailor
turned out to be hard, which is why it is parked. `layout_assign` (this section) instead takes a
beautifully made suit off the rack and alters it: the suit's interior is excellent — proper lining,
real construction, far better than the tailor could improvise — but it isn't the building's shape.
The wrong-floor-area problem (§10 below) is being charged for the whole size-4 suit's cloth while
measured against a size-1 body; the shape-distortion problem (Q3, OPEN-18) is an alteration that
takes in the width but not the length.

`layout_assign` is **not a fifth zoning strategy** — the other four modes (§1) all zone the
building's own real footprint, more or less finely. `layout_assign` instead **replaces the whole
building with a validated DOE/ASHRAE 90.1 reference prototype IDF** (E+ 23.1 library) for the
building's archetype, then scales that baseline to fit: plan geometry by `√S`, internal loads by
`S`, where `S` is the real building's floor area divided by the baseline's own. It shares almost
nothing structurally with the other four modes, so the comparison below is read as **method vs.
method**, not as another point on the zoning-fidelity spectrum.

### 10.2 Zone-count fidelity

This is the one comparison that *is* structurally sound across all five modes, because it compares
a fixed property (how many thermal zones a building gets) rather than an energy output. Re-derived
directly from `openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv`, column
`prototype_zones_count`, across the **28 mapped archetypes**: **n = 28, min = 1, max = 256.**

![Zone-count fidelity by mode, all 28 mapped archetypes, T20 harvest](../../docs_DONE/SETUP/layoutAssigner/figures/layout_assign_vs_modes_zone_fidelity.png)
*`building` / `floor` / `fast_zone` apply one generic rule to every building type; `layout_assign`
carries each building type's real, validated zone count instead — sometimes far more detailed (tall
towers, hospitals), sometimes less. The point is not "more zones is better"; it is that
`layout_assign` matches the reference reality instead of approximating it.*

### 10.3 Run success at fleet scale

`layout_assign` was run on the full 12-cell / 8,160-building matrix by the storey-matching arc's
**T20** harvest (`openubem/outputs/comparisons/t20_layout_assign_eui.csv`): **8,153/8,160 = 99.914%
success, median `total_eui` 122.23 kWh/m²/yr** (the prior harvest, T19, was 7,990/8,160 = 97.92%,
median 103.75).

**The improvement is not credited to the storey-matching arc.** The +163 additional passing
buildings decompose as:

```
+150  E-LA-20 fix (landed 2026-07-25, before this arc began)
+  2  other nyc_rural recoveries, cause not investigated
+ 14  other-cell recoveries, cause not investigated
-  3  E-LA-40 regressions
= +163
```

150 of the 163 — the overwhelming majority — is a pre-existing convergence fix surfacing at fleet
scale for the first time in this harvest, not the storey-matching mechanism itself.

![Full fleet: did the simulation even run? T20 harvest](../../docs_DONE/SETUP/layoutAssigner/figures/layout_assign_vs_modes_cluster_success.png)
*Out of 8,160 buildings, how many simulated successfully vs. crashed, per city zone, T20 harvest.
This figure shows only that the simulations complete — it is not a validation of the mode's energy
output (§10.5).*

### 10.4 Storey matching and its reach

The mechanism this arc built, `match_storeys()` (`openubem/geometry/layout_assigner.py`), sets a
residual `Zone.Multiplier` on the prototype's middle repeatable floor band so the total simulated
storeys equal the real building's `num_floors` — before it, every real building silently inherited
the prototype's own native storey count regardless of its real height.

**Its reach is narrow, by design, not by oversight.** It expresses only `n_proto ∈ {1, 3}`, and only
the **taller** case (`n_real > n_proto`). `n_proto == 2` (`SmallOffice`, 2,848 fleet buildings) and
every `n_proto ≥ 4` archetype fall back permanently, as does any building *shorter* than its
prototype — the common case at the fleet's median size. A later correctness fix (R10) narrowed the
taller case further still: `HighriseApartment` now matches only at `n_real ∈ {10, 18, 26, …}`;
`MidriseApartment` only at **even** `n_real ≥ 4`. Extending the mechanism to the shorter case was
considered and explicitly declined — a `Zone.Multiplier` changes simulated energy, never a vertex,
so extending it would perturb the thermal model of the majority of buildings that currently run
untouched, in exchange for reach rather than correctness.

### 10.5 Why there is no EUI column in §4

**§4's cross-mode EUI table does not carry a `layout_assign` column, and this is deliberate, not an
omission.**

Every EUI this mode has reported — every harvest, T08 through T20 — divides simulated energy by the
building's **nominal** floor area (`footprint_area_m2 × levels`, from Stage-2 semantic enrichment),
never by the floor area EnergyPlus actually simulated. The file EnergyPlus writes recording the
floor area it actually simulated, `eplusout.eio`, is deleted unconditionally by the shared cluster
template (`scripts/cluster/submit_fleet_t08.sbatch:63`, `rm -f "$OUTDIR"/*.eio`) — byte-identical
across every harvest from T08 to T20. **No fleet-scale EUI in this mode has a verified denominator,
and none can be reconstructed without re-running the fleet.**

**Measured** locally (`openubem/outputs/comparisons/r06c_local_results.csv`, 6 real fleet buildings
with `eio` retained — the only such evidence in the project): buildings where storey matching
actually applied (N=4) hold the nominal floor area to within **~0.002%** of the `eio`-true value;
`MidriseApartment` buildings it does not reach (N=2, `identity` status) are off by **exactly 4/3**.

**Inferred from the code contract, not measured:** of the 7,442 buildings evaluated fleet-wide,
**6,939** are non-`applied` — i.e. storey matching did not reach them, so their nominal and
simulated floor areas are not known to agree. For `MidriseApartment` specifically, the exposure
breaks down as **1,225 buildings at 4.000× (1-storey), 1,048 at 2.000× (2-storey), 343 at 1.333×
(3-storey), 66 below 1.0×, 2,682 total**; the factor for other archetypes is unmeasured.

**The plain-language reading:** for a one-storey building, the mode simulates a four-storey
apartment prototype and divides that energy by one storey's floor area — **a correct number for the
wrong building.** Publishing that number in §4 alongside the other four modes would put a number
already known to be wrong, for most of the fleet, into the reader-facing comparison table.

**Precision about the other four modes, because the difference is easy to overstate** *(director
correction, 2026-08-05)*: all five modes, `layout_assign` included, use the **same** nominal
denominator, and `eplusout.eio` is missing for all of them, so **no mode's denominator is
`eio`-verified at fleet scale** (`layoutAssigner/figures/README.md:9`). The difference is not that
the other four are verified and this one is not. It is that for the other four the nominal
denominator is **correct by construction** — they zone the real building's own footprint, so the
floor area simulated *is* `footprint_area_m2 × levels` — whereas `layout_assign` substitutes a
prototype of a different height, which breaks that identity. `layout_assign` is the only mode where
the nominal denominator is known to be wrong.

**The condition that restores the column:** a fleet re-run that retains `eplusout.eio`, giving a
verified, multiplier-aware denominator for every building rather than the 6-building local sample
above. This is tracked as register item **OPEN-01** in
[`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`](../../docs_ACTIVE/openings/INVESTIGATION_open-items-register.md).
Until that condition is met, `layout_assign` stays out of §4 by design.

### 10.6 The transformer cliff

Fixed-capacity auxiliary equipment (transformers, DHW tanks, HVAC coils) is not scaled with the
building — a known limitation (§10.4's mechanism does not touch it). Its failure mode is clean and
deterministic rather than random: on `MediumOffice` buildings with `applied` storey-matching status
(`scratchpad/f11_transformer_check_v3.csv`, filtered to `archetype_id=="MediumOffice" &
new_status=="applied"`, split at `new_multiplier<=7` vs. `>=8`), transformer overload is **0/114
(0.0%)** at every residual multiplier ≤ 7 and **117/117 (100%)** at every multiplier ≥ 8 — a
perfectly deterministic cliff. The population this result is measured over is **439** buildings
(`applied ∪ fallback_not_expressible`, the taller-than-prototype half of the transformer-bearing
staging population), not 698 (the full staging population regardless of height) and not 805 (a
stale pre-fix estimate).

### 10.7 Provenance

| Artifact | Path |
|---|---|
| Zone-count fidelity, 28 archetypes | `openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv` |
| T20 fleet EUI, 8,160 rows | `openubem/outputs/comparisons/t20_layout_assign_eui.csv` |
| T20 storey-matching reach/exposure, 7,442 evaluated buildings | `openubem/outputs/comparisons/t20_r10_reach_change.csv` |
| Denominator ground truth, 6 real buildings with `eplusout.eio` retained | `openubem/outputs/comparisons/r06c_local_results.csv` |
| Transformer-cliff staging population | `scratchpad/f11_transformer_check_v3.csv` |
| Zone-count fidelity figure (T20) | `docs/docs_DONE/SETUP/layoutAssigner/figures/layout_assign_vs_modes_zone_fidelity.png` |
| Fleet success/fail figure (T20) | `docs/docs_DONE/SETUP/layoutAssigner/figures/layout_assign_vs_modes_cluster_success.png` |
| Figure vintage/denominator disclosures | `docs/docs_DONE/SETUP/layoutAssigner/figures/README.md` |
| Frozen arc record (full derivation) | `docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md` §8/§9 |

---

*OpenUBEM — simulation-resolution results report. Figures generated from the T08 12-cell sweep
(EnergyPlus 23.1); the design/spec docs remain the binding source of truth. 2026-07-01
(§10 `layout_assign` structural comparison added 2026-08-05).*
