# MEASUREMENT — the ten-task pass, 2026-08-18 (night)

**Slug:** `MEASUREMENT_ten-tasks-2026-08-18-night`
**Date:** 2026-08-18 (night)
**Plan:** `implemenation/previous/PLAN_ten-tasks-2026-08-18-night.md`
**Executed by:** the director personally.

---

## 0. The one-paragraph answer

**OPEN-56 is proved by intervention, and OPEN-42 is solved.** Writing **one field** — the zone air
volume — into the six buildings that have been failing since 11 August makes **all six complete
successfully with zero severe errors**. The control holds exactly: 16 of 16 baseline runs carry the
`Indicated Zone Volume <= 0.0` warning, **0 of 16 treated runs do**. And the cost of the defect on
buildings that *do* run is now a number rather than a risk: **+0.75 % mean, +0.67 % median, range
−0.07 % to +1.67 %** — small, but **systematically positive**, meaning **the stub understates energy**.
Beyond that: the winding is localised to `geomeppy`, the project's **first fleet-wide error taxonomy**
exists, **OPEN-09's premise is half-right and half-wrong**, and **two of the register's oldest input
figures reproduce to the unit.**

---

## 1. W01–W04 — the OPEN-56 experiment

`scripts/analysis/open56_zone_volume_experiment.py` →
`openubem/outputs/comparisons/open56_zone_volume_experiment.csv`

**Design, as pre-registered in the plan.** Treatment = write `Zone.Volume = floor_area × height` into
a **copy** of each IDF. Both arms re-run from the same IDF in the same session — **the existing
`sim_out` results were deliberately not used as the baseline**, because they were produced days ago in
a different process and would confound the treatment with everything else that has changed. Sample
chosen before any result was seen: all six OPEN-42 failures plus ten successful buildings.

### 1.1 W01 — the diff is exactly one field

Object-by-object comparison, asserted before either arm ran, on all 16 buildings:
**`OK n zones, field 9 only`** every time. No other object, field or vertex differs.

### 1.2 W03 — the control, which decides whether anything else is reportable

| | runs carrying `Indicated Zone Volume <= 0.0` |
|---|---|
| baseline | **16 / 16** |
| treated | **0 / 16** |

✅ **The treatment does exactly what it claims and nothing else.** Everything below is reportable.

### 1.3 🔵 W03 — the mechanism, proved by intervention

| building | baseline | treated |
|---|---|---|
| `la_rural/way_472960972` | ❌ failed, **11 severe** | ✅ **completed, 0 severe** |
| `la_rural/way_472961034` | ❌ failed, **25 severe** | ✅ **completed, 0 severe** |
| `la_rural/way_472961088` | ❌ failed, **25 severe** | ✅ **completed, 0 severe** |
| `la_rural/way_472961091` | ❌ failed, **9 severe** | ✅ **completed, 0 severe** |
| `la_rural/way_472961171` | ❌ failed, **21 severe** | ✅ **completed, 0 severe** |
| `la_urban/way_402215469` | ❌ failed, **39 severe** | ✅ **completed, 0 severe** |

🔴 **Six for six. One field. Zero severe errors.** This is no longer an association read off a
census — it is an intervention with a control, and it answers the question OPEN-42 has carried since
11 August: *what is wrong with these six buildings?* **Nothing is wrong with these six buildings.**
They are the six on which a fleet-wide defect happens to tip over.

### 1.4 W04 — what the stub costs on buildings that do run

| cell | building | baseline EUI | treated EUI | Δ | % |
|---|---|---:|---:|---:|---:|
| `la_rural` | `way_222366800` | 118.55 | 119.12 | +0.57 | **+0.48** |
| `la_rural` | `way_472960895` | 193.77 | 194.28 | +0.51 | **+0.26** |
| `la_rural` | `way_472960930` | 51.71 | 52.35 | +0.64 | **+1.23** |
| `la_rural` | `way_472960931` | 44.11 | 44.75 | +0.65 | **+1.47** |
| `la_rural` | `way_472960932` | 41.36 | 42.05 | +0.69 | **+1.67** |
| `nyc_rural` | `way_1055839510` | 121.90 | 123.20 | +1.30 | **+1.07** |
| `nyc_rural` | `way_1103897140` | 149.23 | 150.49 | +1.27 | **+0.85** |
| `nyc_rural` | `way_1103897841` | 214.08 | 213.94 | −0.14 | **−0.07** |
| `nyc_rural` | `way_1103897842` | 290.80 | 291.70 | +0.90 | **+0.31** |
| `nyc_rural` | `way_1103897844` | 523.87 | 525.14 | +1.26 | **+0.24** |

**mean +0.75 % · median +0.67 % · sd 0.59 · min −0.07 % · max +1.67 %**

🔵 **Two things matter here, and the second matters more than the first.**

1. **The magnitude is small.** Under 2 % on every building, under 1 % on most. **This is not a reason
   to withdraw or restate `157.1`.**
2. 🔴 **The sign is not random.** **Nine of ten move the same way**, and the tenth moves −0.07 %,
   which is inside run-to-run noise. **The stub systematically *understates* energy**, because a zone
   with almost no air capacitance rides its setpoints more easily than a real one. A defect with a
   consistent direction is a **bias**, not scatter, and the absolute Δ is strikingly uniform
   (+0.51 to +1.30 kWh/m² across buildings whose EUI spans 41 to 524) — consistent with a fixed
   per-zone effect rather than a proportional one.

⚠️ **What is NOT claimed.** **n = 10, two cells, both rural.** This is a bound and a sign, **not a
fleet estimate**. Extrapolating +0.75 % to `157.1` would give ≈ +1.2 kWh/m², and that arithmetic is
**deliberately not performed as a correction** — a ten-building sample from two rural cells does not
license a fleet number. What it does license: **the risk OPEN-56 was registered with is now bounded
at order 1 %, one-directional, and it is smaller than the Unknown-path bias (+4.06) already reported
beside the published figure.**

---

## 2. W05 — where the reversed winding comes from

**Not from OpenUBEM.** No module in `openubem/` sets floor or ceiling vertex order. The order is
produced by **`geomeppy/geom/polygons.py:573-611`** — `normalize_coords` → `set_entry_direction`,
which orients each polygon against an "outside point" derived from `GlobalGeometryRules`. Our IDFs
declare `UpperLeftCorner / Counterclockwise / Relative`.

🔴 **OpenUBEM has a detector for exactly this signal and deliberately does not apply it.**
`openubem/idf/surfaces.py:223`, `_coreperim_has_inverted_winding`, computes the negative-signed-area
test. Its caller at `:671-681` excludes it, in writing:

> *"`_coreperim_has_inverted_winding` is intentionally excluded — EnergyPlus convention always uses
> negative signed-area (CW winding) for floor surfaces; checking sign would produce false positives on
> healthy buildings."*

**That sentence is why nobody looked.** It says the signal is expected, so seeing it means nothing.
⚠️ **It is not being declared wrong here:** 2-D signed area is projection-dependent, and the
observable defect is the **negative volume**, not the sign. But the two statements now sit against
each other, and one of them has to give. **Naming the tension is this task's result; resolving it is a
code change and is not made here.**

---

## 3. W06 — the fleet error taxonomy

`openubem/outputs/comparisons/open09_fleet_err_taxonomy.csv` (123 families) ·
`open09_fleet_err_perbuilding.csv` (8,160 rows)

Every previous fleet error census in this project ran against the E02 harvest, which an external sweep
emptied on 2026-08-17. **This one runs on a corpus that is still on disk and whose inputs are frozen,
so it is re-derivable and re-runnable.**

**Nine families are universal — all 8,160 buildings.** Two are OPEN-56's:
`GetVertices: Floor is upside down!` (44,455 occurrences) and `GetVertices: Roof/Ceiling is upside
down!` (44,433).

✅ **An independent re-derivation of OPEN-56's 100 %.** The `Indicated Zone Volume <= 0.0` families sum
to **exactly 8,160 buildings** — 7,673 `_WHOLE` + 385 `_PERIM` + 98 + 2 + 2. The first census counted
a log literal; this one partitions by zone-name pattern. **Two methods, same total.**

### ⚠️ One alarming-looking family, checked and cleared

`Output:Meter: invalid Key Name` fires **52,932 times across all 8,160 buildings** — every building
requests meters EnergyPlus does not have. **Control over 1,935 buildings in four cells:**

| | elevator meter present | `ELEVATORS:...` reported invalid |
|---|---:|---:|
| building has elevator energy | **1,358** | **0** |
| building has no elevator energy | **0** | **577** |

**Perfect separation, in the reassuring direction.** The warnings are EnergyPlus correctly reporting
meters with no contributing objects. **Nothing here — and it corroborates OPEN-46's closure from a
direction that item never used.**

---

## 4. W07 — OPEN-09, and the answer is half the item's premise

**Heat-balance non-convergence is rare: 16 of 8,160 = 0.20 %**, all in LA cells, every one with
**exactly 15 warnings** (sd 0 — a capped report).

🔴 **The contingency is perfect.**

| | succeeded | failed |
|---|---:|---:|
| no non-convergence warning | **8,144** | **0** |
| ≥ 1 non-convergence warning | 10 | **6** |

**Non-convergence is a necessary condition for failure in this fleet and not a sufficient one** — 10
of the 16 survive it. With §1 that completes the two-stage picture the arc has been missing:

> **the 10 m³ stub is universal** (necessary, nowhere near sufficient) → **non-convergence is rare and
> contains every failure** → **six tip over.**

**OPEN-09's *"cosmetic"* verdict survives as a statement about prevalence and fails as a statement
about consequence.** 0.20 % of the fleet is not a widespread problem; but every single fleet failure
lives inside it. ⚠️ **No causal claim is made from a contingency table** — this is where to look, not
what happened.

---

## 5. W08 / W09 — two of the register's oldest figures, re-derived

`scripts/analysis/open35_open12_input_recensus.py` →
`openubem/outputs/comparisons/open35_open12_input_recensus.csv`

| figure | register (2026-08-06) | re-derived on run 2 | |
|---|---|---|---|
| **OPEN-35** — neither `levels` nor `height_m` | 2,611 / 8,160 = 32.00 % | **2,611 / 8,160 = 32.00 %** | ✅ **exact** |
| **OPEN-12 / OPEN-14** — `height_m` null | 2,806 / 8,160 = 34.39 % | **2,806 / 8,160 = 34.39 %** | ✅ **exact** |

**OPEN-35's mechanism holds at 100 %:** all 2,611 reach the results file persisted at `levels = 1.0`.
**OPEN-12's three 100 % cells reproduce exactly:** `nyc_suburban` 1,589/1,589, `nyc_rural` 198/198,
`austin_rural` 245/245. **Zero buildings fleet-wide carry a present-but-zero height**, so the
"0 means missing" ambiguity remains absent.

🔵 **Why re-deriving a figure that reproduces is worth the run.** Both originals were measured on the
pre-Phase-E fleet, and their corpus is gone. **Both items may now cite a corpus that still exists and
can be re-run** — which matters directly to OPEN-53's custody condition.

---

## 6. What each item takes from this pass

| item | effect |
|---|---|
| **OPEN-56** | 🔵 **Proved by intervention.** Control passed; six of six failures fixed by one field; cost bounded at ≈ +0.75 % and one-directional. **Remedy is now a small, specified code change.** |
| **OPEN-42** | 🟢 **Solved. Closure recommended.** Its question is answered and the answer is that nothing is wrong with its six buildings. |
| **OPEN-11** | 🟢 **Closure recommended** — same six, and its per-building remedy is superseded. |
| **OPEN-09** | 🔵 **Sharpened, not closed.** Prevalence 0.20 %; but it contains 6 of 6 failures. |
| **OPEN-35** | ✅ Figure re-derived exactly on a live corpus. Still open on the DESIGN question, untouched. |
| **OPEN-12 / OPEN-14** | ✅ Figures re-derived exactly on a live corpus. |
| **OPEN-46** | ✅ Corroborated from a new direction (§3). No change. |
| **OPEN-53** | ✅ Its "regenerate in a durable location" condition gains a concrete argument — three items now cite run 2. |

---

## 7. Artifacts

| path | what |
|---|---|
| `scripts/analysis/open56_zone_volume_experiment.py` | W01–W04, the intervention |
| `scripts/analysis/open09_fleet_err_taxonomy.py` | W06/W07 |
| `scripts/analysis/open35_open12_input_recensus.py` | W08/W09 |
| `openubem/outputs/comparisons/open56_zone_volume_experiment.csv` | 16 buildings × 2 arms |
| `openubem/outputs/comparisons/open09_fleet_err_taxonomy.csv` | 123 families |
| `openubem/outputs/comparisons/open09_fleet_err_perbuilding.csv` | 8,160 rows |
| `openubem/outputs/comparisons/open35_open12_input_recensus.csv` | 12 cells |

⚠️ **`%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/` is load-bearing for all of it and is not
durable** — see OPEN-53.
