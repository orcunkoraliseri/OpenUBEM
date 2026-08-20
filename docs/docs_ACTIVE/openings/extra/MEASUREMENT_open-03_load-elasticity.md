# MEASUREMENT — OPEN-03: does internal-load elasticity support "roughly half the gap"?

> Executes T02-T04 of `docs/docs_ACTIVE/openings/implemenation/PLAN_vintage-elasticity-2026-08-19.md`.
> T01 (runner build, CP-1 control) completed separately; see that plan's §9 for the T01 entry.
> Measurement only. No `openubem/` code touched. No register edits.

---

## Verdict

> **Still inconclusive — and here is exactly what would settle it.**

Two things are true at once. First, the mechanism this plan tests (scaling
`row["lighting_w_m2"]`/`row["equipment_w_m2"]` before `run_step3`) **only reaches the simulated
model for 4 of the 20 buildings** — the other 16 are on `layout_assign`'s baseline-IDF path, where
internal loads are the ASHRAE `STD2022` prototype's own hardcoded values and never touch the row.
Second, **for the 4 buildings it does reach**, the measured elasticity implies a load-density
multiple of **1.4-2.1x** would be needed to close even half the pooled gap — large, and from a
sample too small and archetypally unrepresentative (3 `OpenUBEMUnknown` fallbacks + 1 `Courthouse`,
none of them the office/retail/warehouse archetypes that dominate the fleet) to generalize. Neither
half of the sample supports calling this "supported" or "refuted." See "What this does and does not
settle," below, for the experiment that would close it.

---

## What was run

T02: `scripts/analysis/open03_load_elasticity_2026-08-19.py --scale 0.7` and `--scale 1.3`, each
over the same 20 buildings as T01's CP-1 sample. Outputs under
`openubem/outputs/open03_elasticity/0.7/` and `openubem/outputs/open03_elasticity/1.3/`.
**40/40 buildings reached `parse_status=success`. Zero failures, no error text to report.**

T03: `scripts/analysis/open03_elasticity_analysis_2026-08-19.py` (new file) joins those two
variants against the existing scale-1.0 baseline (`openubem/outputs/comparisons/
open03_enduse_by_building.csv`, re-extracted from `scratchpad/open03-untrimmed-sample/…/eplusout.sql`
with a corrected 14-row ABUPS end-use set — see "Deviations"), computes EUI as
ABUPS `Total End Uses` ÷ multiplier-aware simulated floor area (never `total_eui_kwh_m2`, OPEN-60),
and writes:

- `openubem/outputs/comparisons/open03_load_elasticity.csv` — 60 rows (20 buildings x 3 scales)
- `openubem/outputs/comparisons/open03_elasticity_summary.csv` — 2 rows (one per variant)

## The 20 osm_ids

`austin_centre/way/1008727470`, `austin_centre/way/328529693`, `austin_rural/way/1165379866`,
`austin_rural/way/1480414338`, `austin_rural/way/762128912`, `austin_rural/way/1450171441`,
`austin_suburban/way/382992872`, `austin_urban/way/381810583`, `la_centre/way/905248736`,
`la_centre/way/427817563`, `la_rural/way/472961221`, `nyc_centre/way/265424467`,
`nyc_rural/way/772627016`, `nyc_rural/way/772627029`, `nyc_rural/way/270445757`,
`nyc_rural/way/772627043`, `nyc_suburban/way/846412106`, `nyc_suburban/way/815835776`,
`nyc_suburban/way/610017070`, `nyc_urban/way/241862488`.

## The scale-reaches-the-model gate

Plan-mandated single-building control (`nyc_suburban/way/846412106`, `--scale 0.7`): ABUPS End
Uses, `RowName='Interior Lighting'`, Electricity = **2.05 GJ**, against an expected 0.70 x 2.93 =
2.05 GJ (accept band 2.03-2.07). **Gate passed.**

🔴 **The gate does not generalize, and T03 found out why.** `way/846412106`'s archetype is
`OpenUBEMUnknown` — one of the 4 buildings in this sample with no registered `layout_assign`
baseline IDF. For the other 16 (archetypes `SmallOffice` x13, `MediumOffice` x1, `RetailStandalone`
x1, `Warehouse` x1), every ABUPS end-use value is **bit-identical across scale=0.7, 1.0 and 1.3** —
confirmed independently at the `.idf` text level: `way/328529693`'s `Core_ZN` `LIGHTS` object reads
`Watts_per_Zone_Floor_Area = 6.181254` in both the 0.7-scale and 1.3-scale generated IDFs, unscaled.

This is not a newly-introduced defect in this runner — it reproduces a fact this same arc already
established architecturally in `docs/docs_ACTIVE/openings/extra/
MEASUREMENT_open-03_loads-vintage-split.md` (Part a, §2 and §4, citing
`docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:148-159,494`): `layout_assign`
buildings with a registered `STD2022` baseline **never call `assign_*()`** — their internal loads
are "already in baseline," scaled only by the footprint area ratio, never by
`row["lighting_w_m2"]`/`row["equipment_w_m2"]`. T02/T03 is the first **simulated, per-building**
confirmation of that fact (the prior doc established it by static IDF-field comparison, not by
running EnergyPlus). `openubem/idf/builder.py:69-79` (`_layout_assign_baseline_path`) is the gate;
`layout_assigner.get_registry().get_baseline_idf(archetype_id)` returns a non-`None`
`ASHRAE901_*_STD2022_*.idf` path for `SmallOffice`/`MediumOffice`/`RetailStandalone`/`Warehouse`
and `None` for `OpenUBEMUnknown`/`Courthouse` — verified directly against the registry for exactly
the 6 archetypes in this sample.

**loads_reach_model: True for 4/20, False for 16/20.**

## Reconciliation control (mandatory, both variants)

**40/40 buildings reconcile within 2%** (sum of the 14 ABUPS `End Uses` RowNames vs the ABUPS
`Total End Uses` row) — worst error 0.0729%, `scale_0.7/austin_suburban/way/382992872`.

Deviation from the predecessor's 7-row extraction: the predecessor script
(`scripts/analysis/open03_enduse_decomposition_2026-08-19.py`) uses a 7-row `END_USE_ROWS` list
(Heating, Cooling, Interior Lighting, Interior Equipment, Water Systems, Fans, Pumps) that
under-reconciles specifically for `STD2022` baseline-path archetypes, because those prototypes
carry a nonzero `Exterior Lighting` row (parking-lot/facade lighting, ~4.6% of total for
`way/328529693`) that the fallback-template archetypes do not. This script's `END_USE_ROWS` uses
the full 14-row ABUPS set (adds Exterior Lighting, Exterior Equipment, Heat Rejection,
Humidification, Heat Recovery, Refrigeration, Generators). With the full set, reconciliation is
clean for every building — not a defect in the earlier script's 48-building result, just a set that
happened not to be exercised by this sample's archetype mix.

## Elasticity table

| basis | n | elasticity at -30% | elasticity at +30% | agree (<=1.5x)? |
|---|---|---|---|---|
| pooled, all 20 (Sigma energy / Sigma area) | 20 | 0.2132 | 0.2179 | yes, ratio 1.02 |
| mean of per-building | 20 | 0.0534 | 0.0549 | yes |
| median of per-building | 20 | 0.0 | 0.0 | — (16/20 are exactly 0) |
| pooled, reachable-only | 4 | 0.2856 | 0.2918 | yes, ratio 1.02 |

Elasticity = (% change in ABUPS total EUI) / (% change in load scale). **The two arms agree closely
at every level of pooling** — this sample shows no sign of nonlinearity over ±30%, so the inversion
below is reported as a point estimate at each basis, not a range, on linearity grounds alone (the
range that does exist comes from *which subset* is pooled, not from -30%-vs-+30% disagreement).

Per-building elasticity is exactly 0 (to double-precision noise, ~1e-16) for all 16 non-reachable
buildings and strictly positive (0.147-0.463 at -30%; 0.153-0.475 at +30%) for the 4 reachable ones.
Full table: `openubem/outputs/comparisons/open03_load_elasticity.csv`, columns
`elasticity_minus30`/`elasticity_plus30`/`loads_reach_model`.

## The inversion

Target: close **half** (11.965 pp) and **all** (23.93 pp) of the plan's stated pooled gap
(`-23.93%`, `PLAN_vintage-elasticity-2026-08-19.md` §1/§6), using `k = 1 + (target_pct / elasticity) / 100`.

| basis | k (half the gap) | k (all the gap) |
|---|---|---|
| pooled, all 20 (diluted by the 16 non-reachable) | 1.55-1.56x | 2.10-2.12x |
| pooled, reachable-only (n=4) | 1.41-1.42x | 1.82-1.84x |

Both bases land in the same range because the "all 20" pooled figure is *not* simply diluted to
zero — non-reachable buildings still contribute (unchanged) energy and area to both the numerator
and denominator of the pooled ratio, which shifts it, but the 4 reachable buildings still supply
100% of the actual response. Read either row the same way: **lighting and equipment across this
sample would have to be roughly 1.4-1.6x today's density to close half the gap, and roughly 1.8-2.1x
to close all of it.** That is a large multiple — plausible in isolation for lighting alone (older
fluorescent/incandescent stock can run 2-3x a 2022 LED code density) but a much bigger ask for
equipment, where plug-load density has generally *risen*, not fallen, with building age.

## The heating/cooling counter-movement

Pooled over the 4 reachable buildings (this is the entire pooled effect — the 16 non-reachable
buildings' end-use deltas are all exactly 0, so "pooled over 20" and "pooled over the 4" give the
same deltas):

| variant | dHeating (kWh) | dCooling (kWh) | dFans (kWh) | dLighting+Equipment (kWh, gross) | dTotal (kWh) |
|---|---|---|---|---|---|
| scale_0.7 (-30%) | +77,958 | -33,594 | -26,253 | -259,228 | -240,025 |
| scale_1.3 (+30%) | -80,042 | +34,458 | +31,519 | +259,231 | +245,250 |

Heating and cooling together offset **17.1% (-30%) / 17.6% (+30%)** of the gross lighting+equipment
change, in the opposing direction — this is the counter-movement the plan's arithmetic bound (T01
of the predecessor plan) ignored entirely, and it is real: dropping loads by 30% does *not* drop
total energy by 30% of the loads' share, it drops it by less, because heating rises as the internal
heat gain that used to warm the building for free goes away. Fans move *with* the direct effect
(reinforcing it, -26,253 kWh at -30%, because lower internal+cooling load needs less supply air),
so the two HVAC feedback channels partially cancel: net effect on `dTotal` is a **7.4% dampening**
relative to the gross `dLighting+Equipment` change (`-240,025` vs `-259,228`), not an amplification.

## What this does and does not settle about OPEN-03

**Settles:** the ±30% row-level load scale is now confirmed, by direct simulation (not just static
IDF inspection), to reach only 4 of 20 buildings under `layout_assign` — exactly the buildings
without a registered `STD2022` baseline. For the 16 that are on the baseline path, **no row-level
"vintage-correct the loads" fix — this one or any other built the same way — can ever change their
simulated energy**, because `assign_loads()`'s output never appears in their final `.idf`. Any
future vintage-correction attempt for those buildings must edit the baseline `STD2022` `.idf`'s own
`LIGHTS`/`ELECTRICEQUIPMENT` objects directly (the same class of intervention `envelope_patcher.py`
already performs for envelope U-values), not scale a dataframe column.

**Does not settle:** whether internal loads explain roughly half the gap, fleet-wide. The 4
reachable buildings give a real, roughly linear elasticity (~0.21-0.29 depending on pooling basis)
and an inversion multiple (k ~1.4-2.1x) that is large but not obviously implausible for lighting
alone — yet n=4 is dominated by non-representative archetypes (fallback/unclassified and one
Courthouse), none of them the `SmallOffice`/`MediumOffice`/`RetailStandalone`/`Warehouse` types that
make up 80% of this very sample and, per `MEASUREMENT_open-03_loads-vintage-split.md`, a large share
of the fleet. **What would settle it:** repeat this exact ±30% elasticity design, but with the
perturbation applied to the baseline `.idf`'s own `LIGHTS`/`ELECTRICEQUIPMENT` `Watts/Area` (or
`LightingLevel`/`EquipmentLevel`) fields per zone, for the 16 `STD2022`-baseline archetypes this run
could not touch. That measures the mechanism that actually governs those buildings' energy, instead
of a mechanism the architecture has never wired to them.

## Deviations

- `END_USE_ROWS` in the new analysis script uses the full 14-row ABUPS set instead of the
  predecessor decomposition script's 7-row set (see "Reconciliation control," above) — needed
  because this sample's baseline-path archetypes carry a nonzero Exterior Lighting end use the
  7-row set would silently drop from the reconciliation check §3 rule 4 requires.
- The scale=1.0 baseline row's end-use breakdown is re-extracted directly from
  `scratchpad/open03-untrimmed-sample/…/eplusout.sql` (same 14-row query) rather than read from
  `openubem/outputs/comparisons/open03_enduse_by_building.csv`'s own 7-row columns, for the same
  reason — floor_area_m2 and archetype_id still come from that CSV unchanged. No baseline
  simulation was re-run; this is a re-extraction from the existing `.sql` files only, consistent
  with plan §3 rule 6.
- T03(b)'s "range, not point" instruction is triggered by *which subset is pooled* (all-20 vs
  reachable-only), not by -30%-vs-+30% disagreement (both arms agree to within 2.2% of each other
  at every pooling basis) — reported as two rows in the inversion table above rather than a single
  range, since the two numbers have different meanings (diluted-pooled vs mechanism-only), not
  different measurements of the same quantity.
- One additional script was added beyond the plan's named file:
  `scripts/analysis/open03_elasticity_analysis_2026-08-19.py` (T03's analysis, per plan §7 T03's
  allowance to add "a second script under `scripts/analysis/` for the analysis if that is cleaner
  than extending the runner"). No file under `openubem/` was touched.

---

# CP-2 — director's sign-off, 2026-08-20

**The executor's verdict was "still inconclusive". I am overturning it to REFUTED, on the strength of
a control the experiment produced by accident and did not recognise.**

## 1. What the experiment actually revealed

The ±30 % perturbation reached only **4 of the 20** buildings. The executor reported this as a
limitation. It is not a limitation — **it is a natural experiment**, and it is the most informative
thing in this run.

`layout_assign` has two internal-load paths, decided by whether the archetype has a mapped DOE
prototype baseline IDF (`openubem/idf/builder.py:69-83`, `:228-236`):

| path | who takes it | where internal loads come from |
|---|---|---|
| **prototype baseline IDF** | archetypes with a mapped `STD2022` baseline — here `SmallOffice` (13), `MediumOffice`, `RetailStandalone`, `Warehouse` | the baseline IDF's **own native densities**, `assign_loads()` never runs |
| **from-scratch template** | archetypes with no mapped baseline — here `OpenUBEMUnknown` (3), `Courthouse` | the **archetype load table**, via `assign_loads()` — **identical to what `auto` uses** |

So the sample splits into 16 buildings where the two modes disagree about internal loads, and
**4 buildings where the two modes use provably identical internal loads.**

## 2. The control, and what it kills

Measured delivered energy, `layout_assign` ÷ `auto`, per building
(`openubem/outputs/comparisons/open03_load_source_per_building.csv`):

- **From-scratch buildings (n=4): lighting ratio 1.000, equipment ratio 1.000.** Identical, as the
  mechanism predicts.
- **Prototype-path buildings (n=16): lighting ratio 0.386** (median) — `layout_assign` delivers
  **barely over a third** of `auto`'s lighting energy — **equipment ratio 0.945**, near-identical.

Now the decisive number. Pooled by floor area
(`openubem/outputs/comparisons/open03_load_source_decomposition.csv`):

| subset | n | `auto` EUI | `layout_assign` EUI | gap | internal-load drop | share of gap explained |
|---|---|---|---|---|---|---|
| all 20 | 20 | 170.14 | 129.45 | **−23.91 %** | +3.52 kWh/m² | **8.0 %** |
| from-scratch | 4 | 204.14 | 155.94 | **−23.61 %** | **−0.00 kWh/m²** | **0.0 %** |
| prototype-path | 16 | 115.09 | 86.56 | −24.79 % | +9.23 kWh/m² | 29.9 % |

**The four buildings whose internal loads are bit-identical between the two modes still show a
−23.61 % gap** — statistically indistinguishable from the −24.79 % shown by the sixteen whose loads
differ by a factor of 2.6 on lighting. **Internal loads explain exactly zero percent of the gap in the
subset where they are the only thing held constant, and the gap does not shrink.**

The −23.91 % pooled figure over all 20 reproduces the independently established **−23.93 %** to two
decimal places, which is the control on this whole calculation.

## 3. Verdict on OPEN-03: REFUTED

OPEN-03 claimed *roughly half* the cross-mode gap comes from `layout_assign` applying vintage-blind
2022-code internal loads. Measured:

- **The load-source difference explains ≈8 % of the pooled gap**, and ≈30 % even among the buildings
  where it operates at all — **not half.** This is consistent with, and sharper than, the earlier
  arithmetic bound of 7.76 % that was withdrawn for being measured against the wrong denominator.
- **The premise is also wrong.** `auto` is not vintage-aware either — it reads one fixed pair per
  archetype from `doe_prototype_loads.json`, with no vintage key. **Both modes are equally
  vintage-blind.** They simply disagree: `auto` gives `SmallOffice` 10.76 W/m² of lighting where the
  `STD2022` baseline IDF's own area-weighted density delivers about a third of that. **The gap is a
  load-*source* disagreement, not a load-*vintage* one**, and no era table would close it.
- HVAC feedback is real but small and in the *damping* direction: heating rising as lighting falls
  offsets ~17 % of the gross internal-load change, net ~7.4 % on the total. It does not rescue the
  claim.

## 4. What OPEN-03 becomes

**The claim is closed as refuted. The gap is not.** ~92 % of a −23.9 % cross-mode difference remains
unexplained and is now known **not** to be internal loads. The from-scratch subset is the cheapest
place to attack it: those four buildings have identical loads, identical archetypes and identical
weather across modes, so the entire −23.61 % lives in geometry, zoning, envelope or HVAC sizing. **A
four-building end-use diff on that subset would localise it, with no new simulation** — the runs
already exist.

## 5. Corrections to the executor's report

1. **Verdict overturned** from "still inconclusive" to **refuted**, per §2-§3.
2. **The inversion (`k` ≈ 1.4–2.1×) should not be read as a live estimate.** It was computed on the
   4 from-scratch buildings — precisely the subset just shown to have **zero** load-driven gap — so
   it inverts a mechanism that is not operating there. The elasticity itself (0.21–0.29, linear over
   ±30 %) is sound and is what makes §2's damping factor trustworthy.
3. **The "gate passed" report was true but not meaningful.** The single building chosen for the gate
   happened to be one of the 4 reachable ones. Sixteen of twenty were bit-identical across all three
   scales. **A control on one building cannot establish that an intervention reached a population** —
   recorded as a method lesson, not as a fault of the executor, who found and reported the 16/20
   non-response unprompted and was right to continue.

**Artifacts.** `scripts/analysis/open03_load_source_decomposition_2026-08-20.py`,
`openubem/outputs/comparisons/open03_load_source_decomposition.csv`,
`openubem/outputs/comparisons/open03_load_source_per_building.csv`.
