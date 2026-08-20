# PLAN — ten tasks, 2026-08-18 (night)

**Slug:** `PLAN_ten-tasks-2026-08-18-night`
**Date:** 2026-08-18 (late)
**Register:** `INVESTIGATION_open-items-register.md` → OPEN-56
**Predecessor:** `PLAN_ten-items-2026-08-18-late.md` — complete; this is the first measurement that
plan named as OPEN-56's next step.
**Executed by:** the director personally, on the user's instruction: *"si des taches sont completes,
choisir des nouvelles 10 taches ouverts, creer d'un plan d'implementation et continuer avec
l'execution, chaque etape, veuillez mettre a jour [the director prompt] pour des sessions demaines."*

🔵 **Selection rule applied for the first time, and it is the rule the last pass had to learn the hard
way:** every candidate was checked against `docs/docs_ACTIVE/openings/extra/` and
`openubem/outputs/comparisons/` **before** selection, not after. Five of the previous pass's ten were
already answered; **none of these ten is.** Where an item already had a measurement, the task here is
the step that measurement explicitly did **not** take.

**The ten:**

| # | item | the undone step |
|---|---|---|
| W01 | **OPEN-56** | build treated IDFs; prove the diff is exactly one field |
| W02 | **OPEN-56** | run both arms locally, 16 buildings × 2 |
| W03 | **OPEN-56** | the control, then the mechanism answer: do the six survive? |
| W04 | **OPEN-56** | the cost answer: what the stub does to annual EUI |
| W05 | **OPEN-56** | localise the writer — is the reversed winding ours or `geomeppy`'s? |
| W06 | **fleet `.err` taxonomy** | run 2 left **8,160 fresh `.err` files on local disk** — no pass has ever censused them. First fleet-wide error taxonomy from a run this project can re-open |
| W07 | **OPEN-09** | warmup / heat-balance non-convergence rate at HEAD, from W06's census — the item's "cosmetic" claim has never been tested fleet-wide on a local run |
| W08 | **OPEN-35** | re-derive the 2,611-building `levels = 1.0` population on run 2; the 2026-08-05 census predates three code changes |
| W09 | **OPEN-12 / OPEN-14** | re-derive `height_m` coverage on run 2's own Stage-1 inputs; the 34.39 % fleet figure predates the same changes |
| W10 | **records** | register, checklist, **director prompt**, plan log, progress board |

⚠️ **W06–W09 are re-derivations by design.** Each has an existing measurement taken on a *different*
corpus — the E02 harvest or the pre-Phase-E fleet — and this is the first time the same question can
be asked of a fleet that still exists on disk and can be re-run. **If a figure reproduces, that is a
result and is reported as one.**

---

## 1. The question, and why it must be answered before anything is fixed

OPEN-56 records that **8,160 of 8,160 buildings** simulate with their zone air volume replaced by a
**10 m³ stub**, because EnergyPlus computes a negative volume from our geometry. The item was
deliberately registered with its blast radius **unmeasured**:

> *"The effect on annual EUI is unmeasured, in either direction, and must not be assumed."*

**That is the gap this plan closes.** A defect present in 100 % of the fleet is either a footnote or a
reason to restate a published number, and nothing in the register currently says which. **Measuring it
is cheap; guessing it is not allowed.**

🔴 **Two outcomes are equally acceptable and both must be reportable.** If the EUI difference is
negligible, OPEN-56 is a robustness defect that explains six crashes and touches no published figure.
If it is material, `157.1` needs a stated caveat. **The plan is written so that neither result is
easier to produce than the other.**

---

## 2. Hard rules

1. **Local EnergyPlus only.** `C:\EnergyPlusV23-1-0`, version 23.1 — the same version every run in
   this comparison used (`ep_version` column, run 2). **No cluster, no login node, no network.**
2. **No production code is changed.** The volume field is written into a *copy* of each IDF, in a
   scratch directory. `openubem/` and `scripts/validation/` are untouched by this plan.
3. **Both arms re-run from the same IDF, in the same session.** The existing `sim_out` results are
   **not** used as the baseline — they were produced days ago, in a different process. Using them
   would confound the treatment with everything else that has changed.
4. **The treatment is one field.** Only `Zone.Volume` is written. No other object, field or vertex is
   touched, and the diff is asserted before either arm runs.
5. **A non-vacuity control is obligatory.** If the treatment does not remove the
   `Indicated Zone Volume <= 0.0` warning, the experiment has not done what it claims and **no EUI
   number from it may be reported.**
6. **Report the failures too.** The six OPEN-42 buildings are in the sample precisely because they
   crash; whether they survive with a correct volume is the mechanism test.

---

## 3. Method

**Sample.** Sixteen buildings from run 2 (`open48_refleet`), chosen before any result is seen:
- **all six** OPEN-42 buildings (`la_rural` ×5, `la_urban` ×1) — the mechanism arm;
- **ten** successful buildings spread across cells and sizes — the cost arm.

**Treatment.** For each `Zone` in the IDF, compute `Volume = floor_area × height` from the zone's own
floor surface (planar area by Newell's method) and its z-extent, and write it into the `Zone` object's
Volume field, replacing `autocalculate`.

**Arms.** `baseline` = the IDF exactly as the pipeline wrote it. `treated` = the same IDF with the one
field written. Both run through the same EnergyPlus binary, same EPW, same session.

**Read-out.** From each run: whether it completed, the `Indicated Zone Volume <= 0.0` warning count,
the severe/fatal counts, and **total site energy from `eplusout.sql`**, converted to kWh/m² on the
same floor area for both arms so the ratio is a pure treatment effect.

---

## 4. Tasks — W01…W05 (OPEN-56)

### W01 — Build the treated IDFs and prove the diff is one field
**How to test.** For each building, the treated and baseline IDFs differ **only** in `Zone` objects'
Volume field — asserted by object-by-object comparison, and the assertion is reported, not assumed.

### W02 — Run both arms
**How to test.** 32 runs complete or fail explicitly; no run is silently skipped.

### W03 — The control
**How to test.** `Indicated Zone Volume <= 0.0` count is **> 0 in every baseline run** and **0 in
every treated run**. 🔴 **If this fails, stop and report the failure; do not report EUI.**

### W04 — The two answers
**(a) Mechanism:** do the six failing buildings survive? **(b) Cost:** the distribution of the EUI
change across the ten successful buildings, reported with its sign and spread, not as a single mean.

### W05 — OPEN-56: localise the writer
**What.** Determine whether the reversed floor/ceiling winding originates in our code or in
`geomeppy`'s block extrusion.
**How to test.** The answer names a function and a line, or reports that it could not be localised —
**naming a culprit without tracing it is what this register exists to prevent.**

---

## 4b. Tasks — W06…W10

### W06 — The fleet `.err` taxonomy nobody has taken
**What.** Census every `** Warning **` / `** Severe **` family across all **8,160** run-2 `.err` files.
**Why.** Every previous error census ran against the E02 harvest, which the 2026-08-17 sweep gutted.
Run 2's outputs are on local disk **and its inputs are frozen**, so anything found here is
re-derivable and re-runnable — a first for this project.
**How to test.** Family counts sum to the raw line count; five files read by hand match their bucket.

### W07 — OPEN-09: is "cosmetic" still true, fleet-wide?
**What.** From W06's census, the rate of `Inside surface heat balance did not converge` and warmup
non-convergence across the fleet, and whether it correlates with anything.
**Why.** OPEN-09's *"cosmetic"* verdict rests on a 2026-08-06 test on a small population.
**How to test.** Rate reported per cell and fleet-wide; **no causal claim without a control.**

### W08 — OPEN-35: re-derive the storey-fallback population
**What.** Count buildings with neither `levels` nor `height_m` in run 2's Stage-1 inputs, and how many
persist at `levels = 1.0`.
**Why.** The 2,611 / 8,160 = 32.00 % figure is from 2026-08-05.
**How to test.** Reported against the original figure, whichever way it lands.

### W09 — OPEN-12 / OPEN-14: re-derive height coverage
**What.** `height_m` null fraction per cell in run 2's `01_buildings.gpkg`.
**Why.** The 2,806 / 8,160 = 34.39 % figure is from the same 2026-08-06 pass.
**How to test.** Per-cell table; both the fleet figure and the two cells OPEN-12 names.

### W10 — Records
Register, `docs/PROJECT_CHECKLIST.md`, **the director prompt — updated at each step, per the user's
standing instruction, so tomorrow's sessions inherit the state**, this plan's log, and the progress
board.

---

## 5. Stop-and-report points

- **CP-V1 — after W03.** The control decides whether any of this is reportable.
- **CP-V2 — after W10.** Final.

---

## 6. Progress log

#### W01–W04 — OPEN-56 proved by intervention — completed 2026-08-18 (night) — **CP-V1**

**Artifacts.** `scripts/analysis/open56_zone_volume_experiment.py`;
`openubem/outputs/comparisons/open56_zone_volume_experiment.csv`;
`extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §1.

**W01.** Diff asserted object-by-object before either arm ran: **`OK n zones, field 9 only`** on all
sixteen buildings. No other object, field or vertex differs.

**W03 control — CP-V1 signed.** `Indicated Zone Volume <= 0.0` present in **16 / 16** baseline runs
and **0 / 16** treated runs. The gate the plan set on itself is met, so the EUI numbers are
reportable.

**W03 mechanism — six of six.** Every OPEN-42 failure **completes successfully with zero severe
errors** after the single field is written: 11→0, 25→0, 25→0, 9→0, 21→0, 39→0 severes.

**W04 cost.** Ten successes, two cells: **mean +0.75 %, median +0.67 %, sd 0.59, range −0.07 % to
+1.67 %.** 🔴 **Nine of ten move the same way** — the stub *understates* energy — and the absolute Δ is
uniform (+0.51 to +1.30 kWh/m²) across buildings spanning 41 to 524, i.e. a fixed per-zone effect.
⚠️ **n = 10, two rural cells: a bound and a sign, not a fleet estimate. The +0.75 % → +1.2 kWh/m²
arithmetic is deliberately not performed as a correction.**

**Deviations.** The first run of the experiment **failed its own control** — 0 / 16 volume warnings in
*both* arms — because these IDFs use `HVACTemplate:*` objects and EnergyPlus refuses them outright
without `ExpandObjects`. Every run died at input processing with 1 severe, never reaching the volume
calculation. 🟢 **The control caught it, which is what it was written for**; `-x` added and the reason
recorded in the script. Separately, a first attempt to write the script through a shell heredoc broke
on quoting and was rewritten with the file-write tool — the third time this hazard has cost this arc
time.

**Test status.** Control passed. Non-vacuity: the treated runs of the six previously-failing buildings
produce real EUI values, so the pipeline is not returning empty.

#### W05–W09 — the four measurements — completed 2026-08-18 (night)

**W05 — the writer is localised, and it is not ours.** Floor and ceiling vertex order comes from
`geomeppy/geom/polygons.py:573-611`. 🔴 `openubem/idf/surfaces.py:223` has a detector for exactly this
signal, deliberately excluded at `:671-681` on the written reasoning that negative signed area is the
expected EnergyPlus floor convention. **Tension named, not resolved — resolving it is a code change.**

**W06 — the fleet's first error taxonomy.** 8,160 files, **123 families, 9 of them universal**,
including both `GetVertices: ... is upside down!` families. ✅ **OPEN-56's 100 % independently
re-derived by a second method** — the `Indicated Zone Volume` families sum to exactly 8,160.
⚠️ `Output:Meter: invalid Key Name` fires 52,932 times across every building; **controlled and
cleared** — 1,358 buildings with elevator energy all have their meter, 577 without it all carry the
warning, **no overlap**. EnergyPlus behaving correctly, and incidental corroboration of OPEN-46.

**W07 — OPEN-09.** Non-convergence is **16 / 8,160 = 0.20 %**, all LA, all with exactly 15 warnings.
🔴 **All six fleet failures are inside those 16; zero failures outside.** Necessary, not sufficient.
The item's *"cosmetic"* verdict survives on prevalence and fails on consequence.

**W08 / W09 — both figures reproduce exactly.** OPEN-35 **2,611 / 8,160 = 32.00 %** (and 100 % of them
persisted at `levels = 1.0`); OPEN-12/14 **2,806 / 8,160 = 34.39 %**, with all three 100 % cells one
for one. **Both items can now cite a corpus that still exists.**

#### W10 — records — completed 2026-08-18 (night) — **CP-V2**

Register amended on **OPEN-56, OPEN-42, OPEN-09, OPEN-35, OPEN-12**;
`extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` written; `docs/PROJECT_CHECKLIST.md`, the director
prompt and the progress board updated.

**No item was closed and the count is unchanged at 25 live / 31 struck, next free `OPEN-57`.**
🟢 **Two closures are recommended and not taken — OPEN-42 and OPEN-11** — because retiring an item by
absorbing it into another is the user's call. **Recording a recommendation is not the same as acting
on it, and the distinction is the point.**

**Plan status: all ten tasks discharged. CP-V1 and CP-V2 reported.**
