# MEASUREMENT — ten open items, overnight pass 2026-08-18

> **Plan:** `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md` (X01–X10)
> **Register:** `INVESTIGATION_open-items-register.md`
> **Corpus:** `open48_refleet` (run 2), 12 cells / 8,160 buildings, verified present at start of pass.
> **Nothing here closes an item.** Closures are recommendations; the user rules.

---

## Headline

**Four register figures were re-derived exactly, one of them after being declared not
re-derivable — and two blockers that have stood for weeks turned out to be stale.**

| # | result | |
|---|---|---|
| X08 | **OPEN-10's "90 buildings" re-derived exactly: 66 `MidriseApartment` + 24 `HighriseApartment`** | ✅ |
| X08 | …and given a denominator for the first time: **90 of 1,992** `fallback_not_expressible` = **4.5 %** | 🔵 |
| X05 | **OPEN-08's vintage half is measured at last: 0.0368 % (3 / 8,160)**, archetype control **0.0000 %** | ✅ |
| X04 | OPEN-35's 1,031 re-derived exactly — and its **fleet-level +48 % EUI gap is composition, not effect** | 🔴 |
| X09 | **OPEN-14 settled: the fusion tier fired zero times on 8,160 buildings**, including where a slice exists | ✅ |
| X07 | **Four of the eight OPEN-29 defects have no signature anywhere in the fleet**; a fifth is 1 building | 🔵 |
| X06 | Custody exposure quantified: **152 GB across three corpora, 95 % of it `.sql`** | ⚠️ |

---

## X04 — OPEN-35: what building 2,611 buildings as one storey actually costs

**Population re-derived, exactly.** 2,611 / 8,160 = **32.00 %** with neither `levels` nor
`height_m`; **all 2,611** persisted at `levels = 1.0`. Of those, **1,031** carry an apartment
archetype — **the register's own figure, reproduced to the unit.** Widening the definition to every
mid-/high-rise archetype (adding `LargeOffice` 77, `LargeHotel` 10, `Hospital` 1) gives **1,119**;
both counts are reported because the register's 1,031 uses the narrower definition.

**The naive fleet gap is enormous — and it is almost entirely an artifact.**

| | n | mean | median | p25 | p75 |
|---|---:|---:|---:|---:|---:|
| affected (`neither`) | 2,611 | 235.60 | **191.97** | 130.84 | 220.92 |
| rest of fleet | 5,543 | 150.88 | **129.78** | 108.21 | 150.85 |

That is **+62.20 kWh/m² on the median, +47.9 %**. 🔴 **Do not quote it.** The confound was declared
before the measurement and it turned out to be the whole story: **`nyc_suburban` contributes 1,589 of
the 2,611 and has no unaffected buildings at all** (nor does `nyc_rural`, 198), so the comparison is
mostly between cells, not within them.

**Within cells the direction is not even consistent** — four cells run *lower*, four run *higher*:

| cell | unaffected median | affected median | |
|---|---:|---:|---|
| `austin_centre` | 153.07 | **119.13** | lower |
| `la_centre` | 139.35 | **103.21** | lower |
| `nyc_centre` | 154.89 | **125.15** | lower |
| `la_urban` | 105.96 | **101.45** | lower |
| `austin_suburban` | 112.09 | **161.57** | higher |
| `austin_urban` | 112.46 | **140.80** | higher |
| `la_suburban` | 109.69 | **123.37** | higher |
| `austin_rural` | 89.45 | **106.22** | higher |
| `nyc_suburban`, `nyc_rural` | — | 208.43 / 141.69 | **no comparison group exists** |

**Conclusion, stated conservatively:** OPEN-35's mechanism is proved and its population is exact, but
**this measurement does not establish a fleet EUI consequence**, and the large number a careless
reading would produce is a composition artifact. What the item costs cannot be settled by a
cross-sectional comparison on a population that is missing by construction. **It needs the same
treatment OPEN-56 got: an intervention with a control** — rebuild a sample at a corrected storey
count and re-run both arms. That is named here and **not done**.

**One clean side result:** the affected buildings never fail — **0 failures in 2,611**, against 6 in
the other 5,549. Whatever the single-storey fallback does, it does not destabilise the simulation.

**Evidence:** `openubem/outputs/comparisons/open35_eui_consequence.csv`.

---

## X05 — OPEN-08: the vintage half, blocked since 2026-08-05, is measured

**🔴 The blocker was stale for the third time.** The item's standing reason for not measuring was
*"no prior-generation source carries `vintage_standard`"* — the only candidate being the E02
manifests, and E02 was assumed lost to the 2026-08-17 sweep. **It was not.** The sweep took the large
files; **61 manifest files survive across all twelve cells**, and `step3_auto/03_manifest.parquet`
carries `vintage_standard` (checked, not assumed).

Run 2 and run 3 do **not** carry it — not in `01_buildings.gpkg`, `03_idf_manifest.parquet`,
`04_simulation_manifest.parquet`, or `05_results.gpkg`. So the comparison is built the other way:
**E02's persisted label against a HEAD re-derivation** from the same buildings' `year_built`, using
production `resolve_vintage()`, mode held at `auto` on both sides.

| | disagreement |
|---|---:|
| **vintage** (E02 persisted vs HEAD re-derivation) | **3 / 8,160 = 0.0368 %** |
| **archetype**, same join, in-task control | **0 / 8,160 = 0.0000 %** |

All three disagreements are one bin apart (`DOERefPre1980` → `DOERef1980to2004`), in `la_centre` (1)
and `la_urban` (2). **Every other cell is exact.**

**The tier breakdown is the mechanism, and it also serves as the control that the re-derivation
matches production:**

| tier | n | agreement |
|---|---:|---:|
| `VINTAGE_NAN_PERMISSIVE_DEFAULT` | 4,256 | 100.00 % |
| `HOTDECK_NEIGHBOR_HIGH` | **90** | 100.00 % |
| `HOTDECK_NEIGHBOR_MED` | **46** | 100.00 % |
| `GROUPMODE_MED` | 1,521 | 99.93 % |
| `OBSERVED_YEAR` | 2,247 | 99.91 % |

The **90 / 46** reproduce run 2's own `data_quality_flag` census **exactly**; `GROUPMODE_MED` and the
tier-3 default land within 1–2 rows of it. That is what makes the 0.0368 % citable rather than
merely computed. ⚠️ **The 100 % on the tier-3 default is not evidence of anything** — it is a
constant, and a constant reproduces trivially.

🔴 **A method note that changed the answer by an order of magnitude.** The first run of this
comparison dropped the geometry column when loading, which silently disables `resolve_vintage`'s
tier-1 spatial donor — `knn_fill` degrades to the group mode without raising. That produced
**29 / 8,160 = 0.3554 %** and a tier table with **no `HOTDECK_*` rows at all**, which is what exposed
it. Geometry was restored and the measurement re-run **before any number was reported**. The absent
tier was the tell; had the tiers not been printed, a 10×-too-large figure would have been published.

**Standing:** the archetype half remains **13.40 % between T08 and T20**. This measurement does not
contradict that — it measures a *different pair of generations*. What it does establish is that
**between E02 and run 2 the archetype is perfectly reproducible and the vintage nearly so**, so the
cross-generation confound this item warns about is **not a property of the pipeline in general**; it
is a property of the specific old generations involved. **Closure recommended to the user**, on the
vintage half being measured and the archetype half being bounded and cell-attributed.

**Evidence:** `openubem/outputs/comparisons/open08_vintage_cross_generation.csv`.

---

## X06 — OPEN-53: the custody exposure, quantified

The item's original question (*why are the `.sql`/`.end` missing*) was answered on 2026-08-18; it
stays open on **custody**, with the register stating *"no local artifact is currently named as the
next step."* This names one.

| corpus | files | size | largest class |
|---|---:|---:|---|
| `open48_refleet` (**run 2 — seven live items depend on it**) | 41,014 | **79.75 GB** | `.sql` **76.23 GB** (96 %) |
| `open48_refleet3` (run 3) | 43,162 | 45.73 GB | `.sql` 42.43 GB (93 %) |
| `open48_repeat` | 3,711 | 26.89 GB | `.sql` 26.03 GB (97 %) |
| **total in `%LOCALAPPDATA%\Temp\ubem_validation`** | 87,887 | **152.4 GB** | **145 GB of `.sql`** |

**Not yet swept:** directory mtimes across `nyc_centre`, `austin_suburban`, `la_rural` read
2026-08-12/13 with full entry counts — none carries the 2026-08-17 16:21 signature that emptied E02.

🔵 **The useful finding is how cheap the evidence is compared to the bait.** The sweep that took E02
targeted the largest files. In run 2 the material this arc actually cites is small:

- `.err` — **0.091 GB** (the fleet error taxonomy, OPEN-09, OPEN-56's control, OPEN-42)
- `.gpkg` + `.csv` + `.geojson` — **0.027 GB** (OPEN-35, OPEN-12, OPEN-08, OPEN-10)
- `.idf` — 3.36 GB (needed only to re-run an intervention)

**Under 0.12 GB preserves every published finding in this pass; 3.5 GB preserves the ability to
re-run one.** The other **76 GB of `.sql` is what attracts a sweep** and is re-derivable from the
IDFs. ⚠️ **Registered as an observation, not a remedy — no files were moved, copied or deleted.**

---

## X07 — OPEN-29: the adoption material

The item asks which of the defects it inherited this register should adopt. **This task did not
re-sweep** — the previous automated attempt was circular (it classified IDs from OPEN-29's own
candidate list). Its input is the eight hand-verified STILL-OPEN IDs; its new evidence is the fleet
error taxonomy built last pass, which none of these defects has ever been tested against.

| defect | what it names | signature in run 2 (8,160 buildings) | overlaps |
|---|---|---|---|
| **E-LA-06** (flow-balance half) | `scale_baseline_idf()` does not scale fixed-capacity auxiliary equipment | **32 buildings (0.39 %)** — water-to-air heat-pump air-mass-flow Warning | **OPEN-18** (same function) |
| **E-LA-15** | `SizeAirLoopBranches` minimum-air-flow **Fatal** at extreme small S | **0 families, 0 buildings** | OPEN-18's population |
| **E-LA-16** | cooling-coil / cooling-tower UA autosize failure | **3 families, max 1 building (0.01 %)**, all Warning — no Severe, no Fatal | OPEN-51 (naming, retired) |
| **E-LA-17** | zone divergence persists in a second zone | **16 buildings (0.20 %)** — *the identical population* as OPEN-09/OPEN-56 | 🔴 **OPEN-09 — same buildings** |
| **E-LA-18** | `CheckWarmupConvergence` Severe on `CORE_TOP`/`CORE_MID` | **0 families, 0 buildings** | OPEN-09 |
| **E-LA-19** | same, on `way/241836727` (`SecondarySchool`) | **that building is in run 2 and succeeds** — 0 non-convergence warnings, 0 severe lines | OPEN-09 |
| **E-LA-30** | viewer artifacts do not depict the real pipeline | no EnergyPlus signature — not testable this way | 3D-viz arc (closed) |
| **E-LA-33** | storey matching invisible in geometry, inert for **82–98 %** | 🔵 **re-derived: inert for 93.32 %** (497 applied of 7,442) — inside its own stated band | **OPEN-10** (X08) |

**What this gives the user, in one line each:** four of the eight (**E-LA-15, E-LA-18, E-LA-19,
E-LA-30**) have **no observable signature in a whole fleet** and are candidates for retirement on
evidence; **E-LA-16** is down to one building and no severity; **E-LA-17 is not a separate defect** —
it is OPEN-09's population exactly, and adopting it would double-count; **E-LA-06 and E-LA-33** are
real, sized, and already inside OPEN-18 and OPEN-10 respectively.

⚠️ **Limits stated.** Absence of a signature in `.err` is evidence about the `auto` fleet at HEAD, not
a proof of repair — three of these defects were raised under `layout_assign`, which run 2 does not
exercise. **E-LA-30 and E-LA-33 are viewer/geometry defects that `.err` cannot see**; E-LA-33 is
answered here only because X08 measures the same quantity by another route.

---

## X08 — OPEN-10: the "90 buildings" re-derived, and given a denominator

`MEASUREMENT_open-10_zonegroup-capability.md` §4 named the exact experiment that would settle this
figure and declined to run it, because that plan forbade CPU-bound work — *"NOT re-derived in this
task, and I did not attempt to."* **This plan does not carry that constraint. The experiment was
run, using production `compute_band_map()` / `match_storeys()`, not a re-implementation.**

**🔵 It reproduces exactly, split and all:**

| | historic figure (2026-08-05) | re-derived on run 2 |
|---|---|---|
| buildings the `ZoneGroup` overwrite would recover | **90** = 66 `MidriseApartment` + 24 `HighriseApartment` | **90** = **66** `MidriseApartment` + **24** `HighriseApartment` ✅ |

**And the denominator the item never had:**

| shipped-mechanism status | n | of 7,442 |
|---|---:|---:|
| `fallback_shorter` | 3,727 | 50.1 % |
| `fallback_not_expressible` | 1,992 | 26.8 % |
| `identity` | 1,226 | 16.5 % |
| **`applied`** | **497** | **6.7 %** |

Of the 1,992 `fallback_not_expressible`, the proposed edit reaches **90 (4.5 %)**. The other
**1,902 (95.5 %)** are structurally beyond it — **1,578 `SmallOffice`**, 170 `LargeOffice`, 88
`TallBuilding`, 24 `SuperTallBuilding`, 23 `LargeHotel`, and 19 others. Exactly **two** of the
eighteen archetypes present in the fleet carry a `ZoneGroup` at all
(`MidriseApartment`, `HighriseApartment`) — confirming N11's read directly against the fleet.

🔴 **The register's phrasing "restore exact expressibility" is now quantified and it is generous.**
The edit is real and it works, and it addresses **4.5 % of the problem it is named for**.

**A cross-item finding nobody was looking for.** `nyc_suburban` and `nyc_rural` have **zero**
`applied` buildings — every one is `fallback_shorter`, because every one sits at `levels = 1.0`.
**That is OPEN-35's population.** The missing storey count is *why* storey matching is inert in those
cells, which means **OPEN-35 is upstream of E-LA-33's symptom** and no `ZoneGroup` work would move
either. Stated as a mechanism found, not as a ruling.

**Evidence:** `openubem/outputs/comparisons/open10_storey_expressibility_fleet.csv`.

---

## X09 — OPEN-14: the step the item named, taken

The item's own text: *"proving it needs one more step — showing that the fleet's `01_buildings.gpkg`
was produced by a path that would have consumed the slice. **That step is a measurement nobody has
run, and it is the next thing on this item.**"*

**Three checks, and they agree.**

1. **`config.py:141` — `FUSION_SOURCES_BY_TARGET: dict = {}` at HEAD.** `_fusion_tier`
   (`openubem/semantic/imputation.py:627`) documents itself as *"a guaranteed no-op"* under this
   default: `precedence_for` returns `[]` and `fuse()` never calls out to any source.
2. **Fusion stamps a distinct provenance token** — `FUSED_<SOURCE>_HIGH` / `_MED`, per the same
   docstring (*"no value lands without a token"*).
3. 🔵 **Across all 8,160 buildings of run 2, the count of rows carrying any `FUSED` token is zero** —
   while the other imputation tiers fire and stamp normally in the same column
   (`VINTAGE_NAN_PERMISSIVE_DEFAULT` 4,255, `GROUPMODE_MED` 1,519, `HOTDECK_NEIGHBOR_HIGH` 90,
   `HOTDECK_NEIGHBOR_MED` 46). **The machinery ran; the fusion tier alone contributed nothing.**

**The control is the decisive part.** `nyc_centre` is the one cell with a **tracked** Overture slice
(`overture_nyc_centre_slice.parquet`, confirmed by `git ls-files`). It carries **no `FUSED` token
either**. So the path did not consume a slice **even where one exists**.

**Verdict.** The missing slices are a **real but non-operative** blocker: the config gate closes
before the slice is ever looked for. Two independent blockers stand between this project and a
reproducible height backfill, and **the one the item names is not the binding one.**

**Consequence for the OPEN-12 / OPEN-14 convergence** (four cells, found by two executors who did not
share notes): it can now be adjudicated. The backfill fills **nobody, in any cell** — so it cannot
explain why those four cells are short of `height_m`. **The convergence is a coincidence of coverage,
and OPEN-12's residual is a source-coverage gap in OSM itself, not this item.** That independently
confirms N15's refutation by a route N15 did not use.

---

## X01 / X02 / X03 — OPEN-56 at fleet scale, and OPEN-09's dependence on it

### The control, and the harness fault it caught

| check | result |
|---|---|
| one-field diff assertion (`OK n zones, field 9 only`) | **70 / 70** |
| `Indicated Zone Volume <= 0.0` in the **baseline** arm | **70 / 70** |
| …in the **treated** arm | **0 / 70** |
| completed, baseline / treated | **70 / 70** and **70 / 70** |

🔴 **The first pass did not look like that, and the difference was the harness, not the science.**
Running 140 EnergyPlus jobs through a 6-worker pool, **ten buildings produced a completely empty
output directory in the baseline arm** — no `eplusout.err` at all, no severe, no warning, nothing.
Taken at face value that would have reported the control as **60 / 70** and silently dropped ten
buildings, four of them the whole `nyc_centre` sample. Re-run **one at a time**, the identical
`baseline.idf` completes in **18 seconds with 0 severe errors**. It was a concurrency artifact.
The ten were re-run serially and merged (`scripts/analysis/open56_fleet_cost_repair.py`); the control
then came in whole. **An empty output directory is not a failed simulation, and treating it as one
would have corrupted both the control and the sample.**

### X01 — the fleet-scale cost

**69 buildings across all twelve cells**, both arms in-session, like-for-like denominators.

| | |
|---|---:|
| **mean** | **+0.98 %** |
| **median** | **+0.84 %** |
| sd | 0.75 |
| range | **−0.23 % to +3.25 %** |
| **same direction** | **65 / 69 positive (94.2 %)** |
| absolute Δ | mean **+1.00 kWh/m²**, median +0.90 |

**Against last pass's rural-only estimate of +0.75 % / +0.67 %, the fleet-stratified figure is
higher: +0.98 % / +0.84 %.** The sign is unchanged and firmer — **the stub understates energy.**

**Per cell, and the pattern is geographic rather than morphological:**

| cell | mean | | cell | mean |
|---|---:|---|---|---:|
| `la_centre` | **1.83** | | `austin_centre` | 0.50 |
| `la_rural` | **1.49** | | `nyc_rural` | 0.48 |
| `la_urban` | 1.26 | | `nyc_urban` | **0.38** |
| `austin_urban` | 1.02 | | `nyc_suburban` | 0.53 |
| `austin_suburban` | 1.00 | | `nyc_centre` | 0.92 |
| `austin_rural` | 0.99 | | `la_suburban` | 0.70 |

**LA highest, NYC lowest, Austin in between** — a climate ordering, not an urban-form one. Noted as
an observation; it is not pursued here, and it sits next to **OPEN-19** (LA runs ~+40 % hot).

### X02 — the pre-registered prediction, half held and half refuted

**Predicted before running:** *"mean stays positive and one-directional; magnitude rises with zone
count, so urban cells exceed +0.75 %."*

- ✅ **Positive and one-directional — held**, 94.2 % same-sign.
- 🔴 **"Rises with zone count" — refuted.** `corr(pct_change, n_zones) = +0.113`. Essentially nothing.
- 🔴 **"Urban cells exceed +0.75 %" — refuted.** The three lowest cells are `nyc_urban` (0.38),
  `nyc_rural` (0.48) and `nyc_suburban` (0.53); the two highest are `la_centre` and `la_rural`.

**What the cost actually scales with: almost nothing.** The absolute Δ is the *more* stable
normalisation, not the less — **cv 0.79 raw against 1.09 per zone**. Every covariate correlates
weakly: floor area +0.09, storeys +0.30, written volume +0.09, log-area +0.27. The only moderate
term, baseline EUI at **−0.478**, is arithmetic rather than physical: a near-constant absolute Δ over
a smaller denominator gives a larger percentage.

🔵 **So the honest model is a fixed per-BUILDING offset of ≈ +1.0 kWh/m², not a per-zone effect** —
which **directly refutes the "fixed per-zone effect" guess** the previous pass drew from ten points.
The earlier reading was reasonable on its evidence and is wrong on more of it.

⚠️ **Not extrapolated.** 5 buildings per cell is stratified, not population-weighted, and this plan
forbids converting it into a correction. **`157.1 kWh/m²` is not restated here.** What would settle
it is a population-weighted sample or a full re-run — both named, neither authorised.

### 🔴 X01 side-finding — on one building the volume field moved the DENOMINATOR

`nyc_centre / relation_3566904` (14 zones) was excluded from the cost statistic because its reported
**Total Building Area changed with the treatment: 157,115 m² → 37,551 m² (÷4.18)**. Its apparent
−47.8 % "cost" is therefore not a cost at all — the denominators are not comparable.

**59 of 60 buildings had identical areas to within 0.1 %**, so this is isolated, not systemic. But it
matters more than one building: **the project's EUI denominator is EnergyPlus's own simulated floor
area**, and this shows a case where the same broken geometry that stubs the volume also mis-reports
the area. **Registered as a lead, deliberately not generalised from n = 1.**

### X03 — is the heat-balance non-convergence downstream of the stub? No.

The ten buildings that carry a non-convergence warning **and still succeed**, both arms:

| | baseline | treated |
|---|---:|---:|
| non-convergence warnings, total | **150** | **150** |
| per building | 15 / 15 on all ten | 15 / 15 on all ten |

**Not one warning moved.** Writing the correct zone volume clears the volume warning completely
(0 / 70) and does not touch the non-convergence at all.

🔵 **This is a clean negative and it settles a question the arc has been circling.** OPEN-09 and
OPEN-56 are **independent defects that happen to overlap on the same 16 buildings**. The two-stage
picture from last pass survives — the stub is universal and necessary-not-sufficient, the
non-convergence is rare and contains every failure — but **the second stage is not caused by the
first**. Fixing OPEN-56 would not fix OPEN-09.

⚠️ **One nuance, stated rather than smoothed over.** The previous pass showed all six *failures* are
repaired by this same treatment. Both are true: the treatment rescues the six buildings that tip over,
and it leaves the non-convergence warnings themselves untouched in the ten that do not. The warnings
are a symptom of something else; the stub is what turns that something else fatal.

**Evidence:** `openubem/outputs/comparisons/open56_fleet_cost_stratified.csv`;
scripts `scripts/analysis/open56_fleet_cost_stratified.py`, `open56_fleet_cost_repair.py`.

---

## What this pass did NOT do

- **Closed nothing.** Three closures are recommended (**OPEN-08**, plus the two carried from last
  pass, **OPEN-42** and **OPEN-11**) and none is taken — that is the user's call.
- **Changed no production code.**
- **Did not restate `157.1 kWh/m²`**, and did not perform the +0.98 % arithmetic against it.
- **Did not act on OPEN-55**, whose ruling is still outstanding.
- **Did not move, copy or delete any corpus file**, including the 152 GB measured in X06.
