# MEASUREMENT — the ten-item pass, 2026-08-18 (late)

**Slug:** `MEASUREMENT_ten-items-2026-08-18-late`
**Date:** 2026-08-18 (late)
**Plan:** `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`
**Executed by:** the director personally, on the user's instruction to select ten open items, plan
them, and carry the execution to the end.

---

## 0. The one-paragraph answer

**One task found something the register did not know, and it is larger than the item it was looking
at.** Every building in the fleet — **8,160 of 8,160, 100.00 %** — simulates with its zone air volume
replaced by a **10 m³ stub**, because EnergyPlus computes a **negative** volume from the geometry we
hand it and substitutes a placeholder. OPEN-42's six unexplained failures are the extreme tail of that
one defect, and the mechanism it has been chasing since 11 August is now identified. Registered as
**OPEN-56**. Beyond that: **OPEN-54's guard is implemented and tested** (T02); **OPEN-07's three
buildings all succeed at HEAD** with zero severe errors, on artifacts the item says do not exist
(T05); and **five of the ten selected tasks were already done** — a selection error of mine, described
in §7 rather than buried.

---

## 1. What was selected, and what each task actually returned

| task | item | outcome |
|---|---|---|
| T01 | OPEN-48 | ✅ **CLOSED** — its blocker was discharged by the run that ended the same evening |
| T02 | OPEN-54 | ✅ **remedy implemented and tested** — `_ssh` now raises; the false-success poll path is gone |
| T03 | OPEN-11 | ✅ identity with OPEN-42 confirmed exactly; already "connected" in the register, now **re-derived** |
| T04 | OPEN-42 | 🔵 **the mechanism is found** — and it is fleet-wide, not six buildings. **→ OPEN-56** |
| T05 | OPEN-07 | 🟢 **closeable** — all three succeed at HEAD, 0 severe, no `LAUNDRYROOMFLR1` |
| T06 | OPEN-38 | ⚠️ **superseded** — `MEASUREMENT_open-38_laundryroom.md` (2026-08-18) already answers it. One new hypothesis added, §5 |
| T07 | OPEN-53 | ⚠️ **superseded** — cause answered and item correctly re-parked as a custody risk. One live consequence added, §6 |
| T08 | OPEN-29 | ⚠️ **superseded** — `MEASUREMENT_open-29_status-retrace.md` did the 13-row re-trace and its amendment is already in the register. Method lesson kept, §7.2 |
| T09 | OPEN-13 | ⚠️ **superseded** — `MEASUREMENT_open-13_eutci12-residual.md` (2026-08-18) |
| T10 | OPEN-12 | ⚠️ **superseded** — `MEASUREMENT_open-12_height-residual-retrace.md` (2026-08-18) |

---

## 2. 🔴 T04 — the finding: every building in the fleet runs on a 10 m³ zone

### 2.1 How it was reached

The register's own ruling of 2026-08-18 closed OPEN-42's investigation with:

> *"the E02 IDF corpus that could show the actual per-surface geometry no longer exists on disk"* …
> *"any next step needs either a fresh EnergyPlus run (compute, not authorised here) or a user
> decision to close the question without a mechanism."*

🔴 **That premise is false, and checking it took one directory listing.** Run 2 (`open48_refleet`,
13 August) rebuilt all six buildings, kept their IDFs, kept their `eplusout.err`/`.end`/`.sql`, and
**reproduced the identical thermal-runaway failure**. The artifact the item needed was on disk the
whole time, one run newer than the one that was deleted.

### 2.2 What the IDFs say — the geometry hypothesis dies

`scripts/analysis/open42_run2_fatal_zone_geometry.py` →
`openubem/outputs/comparisons/open42_run2_fatal_zone_geometry.csv`

**Q1 — is the fatal zone the topmost storey?** The register records this as holding *"without
exception"* on the E02 corpus. **In run 2 it fails: 4 of 6, not 6 of 6.**

| building | fatal zone | storey | of | topmost? |
|---|---|---:|---:|---|
| `way/472960972` | `_F1_whole` | 1 | 3 | ❌ **no — the middle storey** |
| `way/472961034` | `_F2_whole` | 2 | 3 | ✅ |
| `way/472961088` | `_F2_whole` | 2 | 3 | ✅ |
| `way/472961091` | `_F2_whole` | 2 | 3 | ✅ |
| `way/472961171` | `_F2_whole` | 2 | 3 | ✅ |
| `way/402215469` | `_F4_whole` | 4 | 6 | ❌ **no — fifth of six** |

**Q2 — is the fatal zone geometrically different from its siblings? No, in every measurable respect.**
`way/402215469` is the cleanest case: six storeys, and the one that blows up is a *middle* one.

| zone | fatal | surfaces | types | boundary conditions | surface area m² | height |
|---|---|---:|---|---|---:|---|
| `_F1_whole` | | 16 | ceiling 1 / floor 1 / wall 14 | Surface 2 / outdoors 14 | 2 869.58 | 3.5 |
| `_F2_whole` | | 16 | ceiling 1 / floor 1 / wall 14 | Surface 2 / outdoors 14 | 2 869.58 | 3.5 |
| `_F3_whole` | | 16 | ceiling 1 / floor 1 / wall 14 | Surface 2 / outdoors 14 | 2 869.58 | 3.5 |
| **`_F4_whole`** | 🔴 | **16** | **ceiling 1 / floor 1 / wall 14** | **Surface 2 / outdoors 14** | **2 869.58** | **3.5** |

Window-to-wall ratio is **0.100 on every zone of all six buildings**, per-surface and per-zone alike.
HVAC, thermostat, lights, people, equipment and infiltration objects are one per zone, six for six.

🔴 **So the fatal zone is indistinguishable from zones that are fine in the same building, in the same
run, in the same file. The zone-geometry line of inquiry is exhausted — and it is exhausted with a
negative answer, not with an artifact shortage.**

### 2.3 The mechanism, from EnergyPlus's own diagnostic

```
** Warning ** Indicated Zone Volume <= 0.0 for Zone=WAY/402215469_F0_WHOLE
**   ~~~   ** The calculated Zone Volume was=-1376.24
**   ~~~   ** The simulation will continue with the Zone Volume set to 10.0 m3.
```

The `Zone` objects declare `Volume` as `autocalculate`, so EnergyPlus derives it from the surfaces —
and gets a **negative** number, because the floor and ceiling surfaces are wound the wrong way round
(`GetVertices: Floor is upside down!`, `GetVertices: Roof/Ceiling is upside down!`, present in every
run). It then substitutes **10 m³**.

**A zone with 2 869 m² of surface and 10 m³ of air has almost no thermal capacitance.** Any
heat-balance residual moves its air temperature by hundreds of degrees inside one timestep. That is
exactly the observed failure — `Temperature (low|high) out of bounds`, −251 °C to +241 °C — and it is
why the runs are *numerically marginal* rather than *structurally broken*: which storey tips over
first is not stable, which is precisely why the fatal storey moved between E02 and run 2.

### 2.4 The census — and why it is not six buildings

`scripts/analysis/open42_zone_volume_census.py` →
`openubem/outputs/comparisons/open42_zone_volume_census.csv`

| population | with a negative computed volume / 10 m³ stub |
|---|---|
| `la_rural` + `la_urban`, run 2 (the census's own scan) | **767 / 767** |
| **all twelve cells, run 2** | **8 160 / 8 160 — 100.00 %** |
| run 3, three cells re-checked | 198/198, 149/149, 245/245 |
| **control — DOE prototype geometry** (`scratchpad/e-la-20-investigation/i03/A_as_classified_today/`) | **0 / 2** |

**The control is what makes this a defect rather than a property of EnergyPlus.** Runs built from the
DOE prototype's own geometry produce **no** volume warning. Runs built from our extruded geometry
produce it **every time, in every cell, on every building.**

🔴 **The 10 m³ stub is not a property of the six. It is the state of every building the project has
ever simulated through this path.** A previous pass measured the stub, found it on succeeding
buildings too, and correctly concluded it did not separate failures from successes — but read that as
*"not the mechanism"* when the right reading was *"necessary, not sufficient."* **The magnitude
separates them:**

| | n | mean computed volume | min |
|---|---:|---:|---:|
| succeeded | 761 | **−683 m³** | −12 050 |
| **failed** | **6** | **−6 096 m³** | **−26 184** |

The six are the extreme tail — the buildings whose real volume is largest, and therefore whose
substitution error is largest.

### 2.5 What is **not** claimed

- **This is not a statement that the published 157.1 kWh/m² is wrong.** Zone volume drives air
  capacitance, not the envelope or the internal-load schedules. Infiltration is written as
  `Flow/ExteriorWallArea` (verified in the IDF), **not** air-changes-per-hour, so it is **not**
  scaled by the stubbed volume — the most obvious route from this defect to annual energy is closed.
  **The effect on annual EUI is unmeasured and is not assumed, in either direction.**
- **The adopted run cannot be checked.** Its per-building `.err` files no longer exist. The rate is
  measured on runs 2 and 3 and **inferred** for the adopted run from the shared code path.
- **The writer is not localised.** The geometry is produced through `geomeppy`'s block extrusion, not
  by a single OpenUBEM line, and this pass did not trace which step reverses the winding. **Naming a
  culprit without tracing it is what this register exists to prevent.**

---

## 3. T03 — the six-building identity

Predicted in the plan before measuring, and confirmed exactly: OPEN-11's six *"inverted-geometry"*
buildings and OPEN-42 face (ii)'s six placeholder-`200.0 m²` Warehouses are **the same six `osm_id`s**
— intersection 6, symmetric difference 0. They are also **exactly the fleet's six non-successes**:
`footprint_area_m2 == 200.0` selects 6 of 8 160 and `simulation_status != "success"` selects the same
6, with no false positive or negative either way.

**The `no_floors` flag does not do this.** It is carried by 7 719 of 8 160 buildings and catches 5 of
the 6. **The placeholder is a perfect classifier because it is a *consequence* of the failure**, not a
cause — `v12_cell_pipeline.py:659` initialises it and only overwrites it on success. That was already
traced on 2026-08-12; this pass re-derived it independently and it reproduces.

🔴 **What is new here is what it means for OPEN-11.** OPEN-11's subject is the Phase-E re-run's six
drops and an un-reapplied `10_fails_solution.md` remediation. Those six are now shown to be a
thermal-runaway population with a fleet-wide cause. **A per-building remediation cannot be the right
remedy for a defect that is present in all 8 160 buildings.** OPEN-11 should be folded into OPEN-56 or
closed against it — recorded as a recommendation, not applied.

Evidence: `scripts/analysis/open11_open42_six_building_identity.py`,
`openubem/outputs/comparisons/open11_open42_six_buildings.csv`.

---

## 4. T05 — OPEN-07's three buildings all succeed at HEAD

The item has stood since 2026-08-06 on three buildings that *"regressed from success to failure"*, and
since 2026-08-18 on the statement that `la_urban/way/401910463` *"still has no surviving IDF anywhere
under `scratchpad/`"*.

**All three have a surviving IDF, a surviving `.err` and a surviving `.sql` in run 2, and all three
completed successfully:**

| building | archetype | status | EUI | `eplusout.end` | `LAUNDRYROOMFLR1` |
|---|---|---|---:|---|---|
| `la_urban/way/401910463` | `SmallHotel` | **success** | 129.35 | `Completed Successfully — 28 Warning; 0 Severe` | 0 |
| `nyc_rural/way/965718402` | `SmallHotel` | **success** | 237.23 | `Completed Successfully — 387 Warning; 0 Severe` | 0 |
| `nyc_rural/way/965718403` | `SmallHotel` | **success** | 271.97 | `Completed Successfully — 517 Warning; 0 Severe` | 0 |

⚠️ **The one caveat, stated rather than smoothed:** the regression E-LA-40 recorded was in
`layout_assign`, and run 2 is the whole-storey (`auto`-family) path. **So this shows the regression
does not reproduce on the certified path, not that it is fixed in the mode where it was seen.** That
mode is `layout_assign`, which the LayoutAssigner arc closed as *not certified for fleet EUI*.
**Recommendation: OPEN-07 closes against the certified path, with the `layout_assign` caveat carried
into the closure note.** Not applied here — it is a closure the user may want to see first.

---

## 5. T06 — OPEN-38: one hypothesis added to an answered item

`MEASUREMENT_open-38_laundryroom.md` (2026-08-18) already re-derived the population from raw `.err`
(7 runs, confirmed) and ruled the two mechanisms distinct. Nothing here overturns it.

**What this pass adds, as a hypothesis and labelled as one:** the surviving DOE-prototype run shows
`LAUNDRYROOMFLR1` is the prototype's **smallest zone — an underground room of 5.11 m²**
(`BuildingSurface:Detailed="S_LAUNDRYROOMFLR1_0_0_0", underground Floor Area = 5.11`). `layout_assign`
scales prototype vertices in plan by **√S** (`layout_assigner.py:214,220`), and OPEN-18 records a
**median S of 0.054** for `MidriseApartment`. A 5.11 m² zone at √0.054 becomes **≈0.28 m²**.

🔴 **If that is the mechanism, OPEN-38 is a symptom of OPEN-18 — the √S vertical-form distortion, the
register's own "largest open modeling problem".** It is **not** tested here: the E02 `layout_assign`
IDFs were destroyed by the 2026-08-17 sweep, and the surviving prototype run is the unscaled A-side.
**Recorded as the next thing to test, not as a finding.**

---

## 6. T07 — OPEN-53: one live consequence

The item is correctly parked as a standing custody risk, with the closure condition *"E02 artifacts
required by open work are either regenerated inside a durable location or formally declared
expendable."*

🔵 **This pass discharges part of that condition by accident and creates new exposure by the same
stroke.** The artifacts OPEN-42 and OPEN-07 needed **were regenerated** — by runs 2 and 3, which
rebuilt every building's IDF and simulation output. **But they live in
`%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet{,3}\`, the same volatile class of location that
the 2026-08-17 sweep emptied**, and this pass's entire T04 finding rests on them.

**Consequence to record against OPEN-53:** the run-2/run-3 corpus is now load-bearing for OPEN-42,
OPEN-11, OPEN-07 and OPEN-56, and it is **not durable**. Whether to copy the six buildings' IDFs and
`.err` files somewhere durable is a user decision — it is a few megabytes.

---

## 7. What went wrong in this pass, stated plainly

### 7.1 🔴 Five of the ten tasks were already done

T06, T07, T08, T09 and T10 all had a completed measurement in
`docs/docs_ACTIVE/openings/extra/` — four of them dated **the same day** as this plan. I selected the
ten from the register's §1 table rows and item headlines, which in several cases still carried the
*original* framing (*"First measurement, not yet made"*, *"never made"*) with the answer recorded
further down the same section or in a separate document.

**This is a selection error and it is mine.** The correct procedure — and the one this register's own
`feedback_verify_artifact_provenance` rule already states — is to check `extra/` and
`openubem/outputs/comparisons/` for an existing artifact **before** selecting an item, not after
writing the plan. **Cost: roughly half the pass's task budget.**

🔵 **It also surfaces a real register-hygiene defect, which is worth more than the wasted effort:**
**the §1 summary table and the item headlines are not a reliable index of what has already been
measured.** They are amended when an item's *status* changes but not always when a *question* is
answered inside it. Anyone selecting work from this register can repeat exactly this mistake.
Recorded against OPEN-29's neighbourhood as a hygiene observation; **not opened as a new item** — one
new ID this pass is enough, and this one is a documentation practice, not a defect.

### 7.2 The T08 method does not work, and that is itself the result

The forward-citation sweep by "newest document mentioning the ID" returns, for every one of the twelve
candidates, a **roll-up document** — the register itself, the director prompt, `PROJECT_CHECKLIST.md`,
or this pass's own plan — because those are the most recently touched files and they list every ID
without adjudicating any. The first run of the sweep returned *"STILL OPEN"* for eight IDs on the
strength of **OPEN-29's own candidate list**, which is circular.

Two successive corrections were needed: exclude the self-referential documents by name, then prefer
the most recent document that **discusses** an ID (≥ 4 mentions in one file) over one that merely
lists it. Both exclusions are written into the script so they are auditable rather than silent.
**Even then the method is weaker than the hand re-trace already in
`MEASUREMENT_open-29_status-retrace.md`, and that document's answer stands.**

### 7.3 A syntax error I made and fixed

The first T02 patch wrote literal newlines into two f-strings instead of `\n` escapes, breaking
`v12_cell_pipeline.py`. Caught immediately by `ast.parse`, repaired, and the file re-verified before
any test ran. Noted because the same escape hazard has now bitten this arc twice.

---

## 8. T02 — the OPEN-54 remedy, in full

`scripts/validation/v12_cell_pipeline.py`, the only file this pass changed.

**1. `_ssh` raises.** A new `RemoteCommandError` is raised on a non-zero remote exit **and** on
`subprocess.TimeoutExpired`, with the command, the exit code and both streams in the message. An
`allow_fail=True` keyword restores the old behaviour where a non-zero exit is a legitimate answer; on
timeout it returns `""` so the caller re-polls rather than concluding.

**2. The false-success poll path is closed.** `squeue -j <id> | wc -l` returns `0` both when the array
has finished and when `squeue` itself failed with its stderr eaten by `2>/dev/null` — so a controller
hiccup used to read as *"array complete"*. The loop now captures `${PIPESTATUS[0]}`, and **concludes
completion only when `sacct` positively corroborates it**: no states returned → re-poll; any state in
`{PENDING, RUNNING, REQUEUED, RESIZING, SUSPENDED, CONFIGURING, COMPLETING}` → re-poll.

**3. Local tests, no cluster call.** `subprocess.run` is swapped for a stand-in that asserts the
argv still carries the `bash -lc` wrapper — the tcsh guard must survive any refactor of this function.

```
PASS success passthrough      PASS timeout raises         PASS empty sacct not complete
PASS nonzero raises           PASS timeout allow_fail     PASS active detected
PASS allow_fail passthrough   PASS sacct parse            PASS CANCELLED+ normalised
ALL PASS
```

**Closure condition, restated against what was delivered:** *"`_ssh` raises on remote failure by
default"* ✅; *"the three unguarded `mkdir` sites inherit that guard"* ✅ (they call `_ssh` with no
`allow_fail`, so they now raise); *"the `:325` false-success path is unreachable"* ✅ (completion
requires sacct corroboration). **OPEN-54's closure condition is met.**

---

## 9. Artifacts

| path | what |
|---|---|
| `scripts/validation/v12_cell_pipeline.py` | T02 — the only production file changed |
| `scripts/analysis/open11_open42_six_building_identity.py` | T03/T04 — the identity and the `no_floors` comparison |
| `scripts/analysis/open42_run2_fatal_zone_geometry.py` | T04 — fatal zone vs its siblings |
| `scripts/analysis/open42_zone_volume_census.py` | T04 — the census that found OPEN-56 |
| `scripts/analysis/open29_defect_status_sweep.py` | T08 — kept for its documented limitation |
| `openubem/outputs/comparisons/open11_open42_six_buildings.csv` | |
| `openubem/outputs/comparisons/open42_run2_fatal_zone_geometry.csv` | |
| `openubem/outputs/comparisons/open42_zone_volume_census.csv` | |
| `openubem/outputs/comparisons/open29_defect_status_sweep.csv` | |
| `%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet\` | 🔴 **load-bearing and not durable** — see §6 |
