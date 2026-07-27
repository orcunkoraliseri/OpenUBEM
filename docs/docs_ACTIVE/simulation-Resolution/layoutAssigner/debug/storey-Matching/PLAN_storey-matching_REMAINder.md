# PLAN — `layout_assign` storey matching, **remainder**

**Slug:** `layout-assign-storey-matching-remainder` · **Date:** 2026-07-26 · **Author:** manager
**Status:** OPEN
**Supersedes:** `PLAN_storey-matching_implementation.md`, which is 🔒 **CLOSED** and must not be
appended to. That document remains the historical record; cite its findings (`F-nn`) and defects
(`E-LA-nn`) **by ID only** — never restate them here.
**Why this document exists:** the predecessor passed 3,500 lines and re-reading it on every dispatch
became a material cost in its own right. **Keep this one short.** If it starts sprawling, close it
and open the next one.

---

## 🔒 FREEZE NOTICE — the four viewers are final

The user has confirmed these render correctly and instructed that **nothing may change about the
visualisation**:

```
figures\nyc_suburban_layout_assign_viewer.html
figures\nyc_suburban_layout_assign_pre_B05_pipeline_viewer.html
figures\la_suburban_layout_assign_viewer.html
figures\la_suburban_layout_assign_pre_B05_pipeline_viewer.html
```

Do not regenerate them, do not re-run `scripts\analysis\enrich_layout_assign_viewers.py`, do not
touch anything under `figures\`. Any future visual work writes to **new filenames**, never to these.
The pre-edit states are archived at `figures\before_viewer_enrich\`, `before_B05\`, `before_B08b\` —
all three are equally untouchable.

---

## 1. Hard rules

All of the predecessor's §1 still applies. The ones broken most often in this arc:

1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.
2. **🔴 Never run compute on the Speed login node.** No blocking `srun`, no `ssh … python …`. All
   cluster compute is `sbatch --array`, fire-and-forget, read the output files afterwards. The login
   node does `mkdir`, `scp`, `tar`, `squeue`, `sacct` and nothing else.
3. Never cancel, requeue or deprioritise a cluster job belonging to another project.
4. When EnergyPlus fails, quote the `** Severe **` line **verbatim**. Never the `.end` file — it says
   *that* it died, never *why*.
5. **Row count must equal artifact count, and both must be stated** in any entry reporting runs.
6. **Prove a control differs from its treatment before measuring with it.** This arc produced that
   failure three times (E-LA-24, E-LA-30, E-LA-31). Byte-compare and report the proof.
7. Ground truth is run artifacts — never a restatement of the hypothesis.
8. Never edit root `main.py`, OVERVIEW or DESIGN docs. **Never `git commit`** — git is external.
9. `openubem/viz/` is **READ-ONLY**. `openubem/idf/opaque_assembly.py` and its frozen constants
   (`T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`) are untouchable. The 25-IDF prototype library is
   read-only.
10. `./.venv/Scripts/python.exe` — plain `python` is not on PATH.
11. **Do not stop and "wait" for a background job.** Block on the *artifacts appearing on disk*,
    polled inside your own turn. A 0-byte log is a healthy buffered job, not a dead one.
12. One progress-log entry per completed task under §5 **of this document**. Never tick a 🔶 row.
13. **Monitoring is a cheap-model job.** Watching a cluster job, polling `squeue`/`sacct`, tailing a
    log, waiting on artifacts — dispatch **Haiku** (or Sonnet at most) for it, never Opus/Fable.
    Reserve the expensive models for plan authoring, defect reasoning and audits. Minimum polling
    interval **30 minutes**; prefer event-driven completion over polling entirely.

---

## 2. State at open

| | |
|---|---|
| Signed | CP-A, CP-B (CP-B with the identity-guarantee amendment) |
| Complete | Phase A, A-bis, B01–B08b, C01 (run + audited) |
| **Blocked** | **R06 — go WITHHELD on R01+R02+R05 only. R04's gate lifted 2026-07-26.** |
| **Decided** | **R04 = option (a): accept + document the height limit — 2026-07-26** |
| **Reduced** | **R07 → a written statement inside R08 — 2026-07-26** |
| Not started | C03, C04 |
| Retracted | C04's original acceptance test (*"confirm the after scene matches `num_floors`"*) — unsatisfiable, see E-LA-33 |
| Frozen | the four viewers, above |

**Open defects carried in:** E-LA-21, E-LA-22, E-LA-23, E-LA-24, E-LA-32, E-LA-33, E-LA-35.
E-LA-34 is remediated for the viewers; the generator-side gap remains.

---

## 3. Tasks

### **R01 — E-LA-35 Cause A: `compute_band_map()` never reads `ZoneList`/`ZoneGroup`**

- **What.** `compute_band_map()` (`layout_assigner.py:392-425`) reads only `Zone.Multiplier`. It
  never inspects `ZoneGroup`, so it measures `n_proto = 3` for a prototype that EnergyPlus actually
  simulates as 10 storeys. Make it multiplier-aware, and make `recomputed_area` agree with what
  EnergyPlus reports in the `eio` Zone Information table.
- **🔴 Scope — verified by the manager, do not widen.** Exactly **one** file in the pinned library
  `00.BaselineBuildings_NUs_v231` (`openubem/config.py:52`) contains a `ZoneGroup`:
  `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf`, line 2538,
  `ZoneGroup, Middle Floors, Mid Floor List, 8;`. **`ApartmentMidRise` has none.** The diagnosis
  entry's `ZoneGroup … 2` line for MidRise does not exist on disk — see the manager correction in the
  closed plan's §8. `MidriseApartment`'s 3/4 area disagreement is **E-LA-25 registry staleness**, a
  different defect, and it does **not** double-count energy. Do not "fix" MidRise here.
- **Why.** `MidriseApartment` is the dominant archetype (2,262 of the 2,932 buildings in the two
  viewer cells, plus the fallback target for 718 unmapped buildings) — so getting this scope wrong in
  either direction is expensive. HighRise is genuinely inflated; MidRise is genuinely not.
- **How to test.** For `ApartmentHighRise`: `compute_band_map()`'s `n_proto` and recomputed area must
  match the `eio` Zone Information totals from a real run. For **all 24 other** prototypes, the
  returned band map must be **byte-identical to before the change** — assert it, do not assume it.

### **R02 — E-LA-35 Cause B: `WaterUse:Equipment` and `People` are double-counted under a multiplier**

- **What.** When `storeys_matched=True`, `calculate_scaling_factor()` deliberately leaves
  `area_scale_ratio` at the whole-building `real_area / baseline_area`. `WaterUse:Equipment.Peak_Flow_Rate`
  and `People.Number_of_People` are scaled by it **and then** replicated again by EnergyPlus's own
  Zone Multiplier on the middle band. Give them the same carve-out D9 gave
  `ElectricLoadCenter:Transformer.Rated_Capacity`.
- **Why.** Measured: these two classes show exactly **6.667×** between `D_HIGHMULT_highrise20` and
  `D_control_S1_highrise3` — matching `area_scale_ratio_D / area_scale_ratio_C` — while
  `Lights` / `ElectricEquipment` `Watts/Area` fields are byte-identical (ratio 1.0000). That contrast
  is the proof: per-area fields are immune, absolute-quantity fields are not.
- **How to test.** Re-run the D pair. After R01 and R02, per-area lighting / equipment / fans must
  reconcile to ≈1.0, and DHW's 2.08× residual must close. **Report heating too** — it currently sits
  at 0.375×, consistent with inflated internal gains suppressing demand, so it should move as the
  gains are corrected. If it does not, that is a finding, not a rounding issue.
- **⚠️** Do not sweep other object classes into this task on suspicion. Any additional class must be
  demonstrated with a measured ratio first, exactly as these two were.

### **R03 — E-LA-32: `Generator:PVWatts` / `ElectricLoadCenter:Generators` scaled by the wrong driver**

- **What.** These are scaled by `area_scale_ratio` today. PV capacity tracks **roof** area, and a
  Zone Multiplier never touches the roof.
- **Why.** Energy-affecting, and it is the same defect family as D9 and R02 — decide it once,
  consistently, rather than three times.
- **How to test.** Assert PV nameplate is invariant to the multiplier at fixed roof area.

### **R04 — 🔶 MANAGER DECISION: does this arc need a geometric storey mechanism at all?**

- **The question.** D3(a) chose `Zone.Multiplier`, which writes no vertex. Consequence, measured over
  n = 2,932 (F-12): rendered height is prototype-native for every prototype-backed building —
  `MidriseApartment` is 12.19 m whether the real building is 1 or 4 storeys. Independently,
  `match_storeys()` returns `fallback_shorter` for **every** `n_real < n_proto`, which is 100% of
  `nyc_suburban`, and `fallback_not_expressible` for `n_proto == 2` and `n_proto >= 4` — together
  **81.6%** of `nyc_suburban` and **98.4%** of `la_suburban`.
- **So the honest statement is:** on the only two cells anyone has inspected visually, storey matching
  is inert almost everywhere, and where it does apply it is invisible in geometry by construction.
- **Why this gates C02.** A fleet EUI table would be dominated by unmatched buildings. Publishing it
  as "the storey-matched fleet result" would overstate the fix's reach.
- **🔴 Not to be resolved by an executor, and not by scaling Z to `num_floors`** — that abandons
  D3(a) for a mechanism this arc explicitly rejected, changes the thermal model, and voids B02's
  identity guard. Manager decides on evidence; the live options are (a) accept and document the
  limit, (b) extend `match_storeys()` to `n_proto ∈ {2, 4+}` and to the shorter case, (c) park the
  mode. **Decide before C02 is authorised, not after.**

> ### ✅ DECIDED 2026-07-26 — **option (a): accept the limit and document it.** R04 is CLOSED.
>
> **The decision.** `layout_assign` ships as a mode that matches **thermal-zone topology and plate
> geometry** to a real validated prototype. It does **not** claim to match building height, and it
> never did — D3(a) chose `Zone.Multiplier` deliberately, and a multiplier writes no vertex. The
> arc closes with that limit stated plainly, not with a new geometric mechanism.
>
> **Why not (b).** Extending `match_storeys()` to `n_proto ∈ {2, 4+}` and to the shorter case would
> raise how often the multiplier *applies* — it would do nothing whatsoever about the thing that
> actually looked wrong, because storeys stay invisible in geometry either way. So (b) buys reach,
> not correctness, and it buys it by perturbing the thermal model of the 82–98% of buildings that
> are currently untouched and running clean. Worst trade available: highest risk, aimed at the wrong
> target.
>
> **Why not (c).** The mode runs at 97.92% fleet-wide and gives real zone-count fidelity that the
> four generic modes cannot. Parking it discards a working capability over a limitation that is
> honestly disclosable.
>
> **What this obliges.** (a) is only defensible if R08's disclosure list is written **plainly and
> up front**, not buried in a caveats appendix. If a reader can come away believing `layout_assign`
> reproduces real building heights, this decision was executed wrongly. The height limitation and
> the 81.6% / 98.4% inert shares are headline text, not footnotes.
>
> **R06 is hereby unblocked from R04's side.** Its remaining gate is R01/R02/R05 green — a real
> gate, since R01/R02 fix live energy inflation and a fleet run before them would be void work.

### **R05 — C01-bis: re-run the local regression after R01–R03**

- **What.** Re-run C01's seven cases. Same harness, but **fix its denominator first** — it divided by
  a nominal `footprint × n_real` (7,000 / 1,050 m²) while the true multiplier-aware simulated floor
  area from `eio` Zone Information is **51,094 / 3,500 m²**.
- **Why.** C01's own three parser bugs, plus this denominator error, mean its EUI table cannot be
  trusted as a before-baseline. The raw ratios were real; the specific numbers were not.
- **How to test.** Zero Fatal. Every Severe named and attributed. Per-area intensities of
  `D_HIGHMULT_highrise20` vs `D_control_S1_highrise3` reconciled, with the residual explained.

### **R06 — C02: full 12-cell / 8,160-building fleet re-run** *(🔶 manager go/no-go — currently WITHHELD)*

- **Gated on:** R01, R02, R05 green **and** R04 decided. Both gates, not either.
- **What.** Fresh `t20_*` job/harvest generation; `t17_`/`t18_`/`t19_` untouched. `sbatch --array`,
  fire-and-forget.
- **How to test.** Fleet success rate ≥ T19's 97.92%; every remaining failure mapped to a known
  defect ID; **F-08's heating ratio re-measured on the same cell and archetype** — the fix's whole
  purpose is that it moves toward 1.0, and it is reported whether it does or not.
- **Carried reporting requirement (from the B06 audit).** D9's `transformer_scale_ratio` is a
  conservative upper bound validated at **one** multiplier (4), scaling as
  `planar_area_factor × multiplier`. Report, **across the multiplier range**, (i) Severe counts and
  (ii) the transformer's energy effect on the 805 exposed buildings of **F-11**.
- **Note.** A clean comparison against T19 is **not** available while E-LA-22 stands. Say so plainly
  rather than presenting deltas as attributable.

### **R07 — C04: visual acceptance, rescoped** *(⬇️ **REDUCED to a written statement 2026-07-26** — see box)*

> **Scope cut, manager, 2026-07-26.** R07 no longer produces a new figure panel. Its three in-scope
> quantities — placement (hull centroid vs `footprint_centroid_utm`), plate area / aspect ratio, and
> the overlap residual — were **already measured by B08a and B08b**, and the user has **visually
> confirmed** the four enriched viewers render correctly. Re-packaging measured evidence into a new
> panel would consume an employee to tell us what we already know.
>
> **What survives:** those measured numbers, plus the explicit out-of-scope statement about height,
> are written into **R08's** documentation. Nothing is dropped from the *record* — only the
> redundant rendering pass is dropped.
>
> **Reinstate R07 in full if** R06's fleet run changes geometry in any way, or if R01/R02 turn out to
> touch placement. Then the visual evidence is no longer pre-verified and must be regenerated.

- **🔒 Writes to new filenames only.** The four current viewers are frozen.
- **In scope:** placement (hull centroid vs `footprint_centroid_utm` — B08b's deliverable), plate area
  and aspect ratio vs the real footprint, and the overlap residual labelled as the design property it
  is.
- **🔴 Out of scope, and the panel must say so in text:** height. Per E-LA-33 it cannot track
  `num_floors`, and a reader must not be left to infer that 12.19 m towers over 1-storey houses are
  the intended result.
- **"Before" panels** come from `figures\before_B05\` and `figures\before_B08b\` — both real pipeline
  output, both labelled as to which is which. The A4-bis artifacts are void evidence (E-LA-30) and
  are not a baseline.

### **R08 — C03: documentation closure**

Results-doc section, `PROJECT_CHECKLIST.md` §L, and **Q3's own entry in
`DONE/DONE-implementation_plan.md` §7** — Q3 is closed by this arc or it is not closed at all.

**Must disclose, plainly, not buried:**
- `match_storeys()` expresses only `n_proto ∈ {1, 3}` and only the taller case; `n_proto == 2`
  (`SmallOffice`, 2,848 fleet buildings) and `n_proto >= 4` (`MidriseApartment`) fall back
  permanently, as does every `n_real < n_proto`.
- The measured inert share: 81.6% (`nyc_suburban`) / 98.4% (`la_suburban`).
- Storey matching is invisible in geometry by construction (D3(a)).
- 718 buildings (8.8%) have no `ARCHETYPE_IDF_MAP` entry.
- The shape-mismatch overlap residual is a design property of the mode, not a bug.

### **R09 — cross-mode comparison: re-run and regenerate the five `layout_assign_vs_modes_*` figures**

- **Gated on R06.** This task consumes R06's `t20_*` harvest. It cannot start earlier; there is no
  shortcut that reuses T19.
- **Target folder.** `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\figures\` — five PNGs,
  `layout_assign_vs_modes_la_summary.csv`, `README.md`, and §3/§3a of
  `OpenUBEM_results_LayoutAssigner.md`. Canonical flat copies also go to `openubem/outputs/`.
  **Preserve the current versions** under `openubem/outputs/comparisons/previous/*_t19.*`, exactly as
  the T17 set was preserved when T19 landed. Do not overwrite a prior generation without archiving it.
- **What.** Compare `layout_assign` against `building` / `floor` / `fast_zone` / `auto` on the T20
  harvest: zone-count fidelity (Fig 1), LA-cell EUI (Fig 2), full-fleet EUI (Fig 5), full-fleet
  success/fail (Fig 6).
- **Why.** These five figures are the arc's public face — they are what "does `layout_assign` work?"
  gets answered with. Every one of them currently rests on **T19, harvested before the E-LA-20 fix
  and before all of Phase B**. Phase B changed the geometry underneath them. They are not stale, they
  are **void**, in the same sense T17/T18/T19 energy results were declared void at Phase C's opening.

**🔴 Four things this task must state explicitly, because each one has already misled a reader once:**

1. **Which harvest each side comes from.** If the four comparison modes are *not* re-run on T20 and
   are carried over from an older harvest, say so in the figure captions — a `layout_assign` bar from
   T20 next to a `building` bar from T17 is not a controlled comparison. Either re-run all five modes
   or label the asymmetry. Do not leave it implicit.
2. **The EUI denominator.** Per R05, `layout_assign`'s floor area must come from the **multiplier-aware
   `eio` Zone Information total**, not a nominal `footprint × n_floors`. If the other modes' EUI uses
   a different denominator convention, the comparison is arithmetic nonsense regardless of how the
   bars look. Verify this before plotting and state the convention used for each mode.
3. **Figure 3 (severity) stays frozen** unless it is rebuilt from real harvest data. Its counts are
   hardcoded from the original E-LA-06 spot-check. Regenerating it *cosmetically* on new data while
   keeping hardcoded numbers would be a fabricated figure. Either rebuild it properly from
   `eplusout.err` across the fleet, or leave it and keep its HISTORICAL banner.
4. **The validation caveat survives this task.** `layout_assign`'s energy output has still never been
   compared against measured or metered data at any scale. A greener success chart and a plausible
   median are **not** validation. That sentence stays in the README and in the results doc, whatever
   T20 shows.

- **How to test.** Row count = artifact count, stated. Fleet success rate reported against T19's
  97.92% **and** against T17's 96.65%, with the `nyc_rural` E-LA-20 cohort (150 rows) called out
  separately so the improvement is not silently attributed to this arc's storey work. Fleet median
  `total_eui` reported next to T19's 103.8 kWh/m²/yr, and against the adopted baseline of
  158.0 kWh/m²/yr.
- **Then update the README changelog** with a T20 entry in the same style as the 2026-07-26 one:
  what regenerated, what did not, and why.

---

## 4. Stop-and-report points

1. 🔶 **CP-D** — after R01, R02, R03, R05. Binding: no fleet run before it. **This is now the only
   gate on R06.**
2. ✅ ~~**R04** — manager decision~~ — **DECIDED 2026-07-26, option (a).** No longer a checkpoint.
3. 🔶 **CP-E** — after R06, R09, R08. Final. (R07 reduced into R08.)

**Critical path to close:** R01+R02+R03 → R05 → **CP-D** → R06 (~15 h cluster) → R09 → R08 → **CP-E**.
Four employees. Two checkpoints. Nothing else is in the way.

---

## 4-bis. ⚠️ IN-FLIGHT AT SESSION HANDOFF — 2026-07-26

**An employee was dispatched for R01 + R02 + R03 and had not reported when the session ended.**

**🔴 Before dispatching anything for R01/R02/R03, check whether that work already landed.** Two runs
racing on the same files has already happened twice on this project. Check, in this order:

1. **§5 below** — if entries for R01/R02/R03 exist, the work reported; audit it, do not re-run it.
2. **`git status --short openubem/`** and `git diff openubem/geometry/layout_assigner.py` — if
   `compute_band_map()` already reads `ZoneGroup`, or `WaterUse:Equipment` / `People` /
   `Generator:PVWatts` already have carve-outs, the employee got there.
3. If the code is **partially** changed and §5 is empty, the employee died mid-task. Do not patch
   around it — read the diff, decide whether to finish or revert it, and record that decision.

Everything downstream (R05, CP-D, R06) is unaffected by this ambiguity; only R01–R03 need the check.

---

## 5. Progress log

*(one entry per completed task: Artifacts / Deviations / Test status / Notes, plus a
`git status --short openubem/ tests/ main.py` line)*

#### AUDIT — P0 director verification — 2026-07-26 — 🔴 **R01's scope statement is FALSIFIED and hereby amended**

**Supersedes:** the "🔴 Scope — verified by the manager, do not widen" bullet of R01, and §4.1(a) of
the director prompt, on the single point of `ApartmentMidRise`. Both frozen texts stay as written;
this entry is the correction.

**What was checked.** Case-insensitive grep for a real `ZoneGroup` object across all **25** files of
the pinned library `00.BaselineBuildings_NUs_v231` (`openubem/config.py:52`):

```
grep -n -i -A3 '^[[:space:]]*ZONEGROUP,[[:space:]]*$' *.idf
```

**Measured result — 2 of 25 files carry one, not 1 of 25:**

| File | Line | Object |
|---|---|---|
| `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` | 2538 | `ZoneGroup, Middle Floors, Mid Floor List, 8;` |
| `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` | **2078** | `ZONEGROUP, Middle Floors, Mid Floor List, **2**;` |

**Why the predecessor missed it.** The MidRise object is written in **upper case** (`ZONEGROUP,`)
while HighRise's is mixed case (`ZoneGroup,`). The earlier "manager correction" that removed MidRise
from scope was a case-sensitive grep miss, not a fact. The originally-suspected `ZoneGroup … 2` for
MidRise **does exist on disk**; only its capitalisation differed.

**Consequences — three, all load-bearing.**

1. **R01's scope widens to both files.** `compute_band_map()` must be `ZoneGroup`-aware for
   `ApartmentMidRise` as well as `ApartmentHighRise`. The instruction "do not fix MidRise here" is
   withdrawn. The byte-identity assertion now covers the **other 23** prototypes, not 24.
2. **E-LA-25 is re-attributed.** `MidriseApartment`'s 3-bands-vs-4-storeys area disagreement was
   filed as *registry staleness*. It is not: 3 measured Z-bands × a `Zone List Multiplier` of 2 on
   the middle band = 1 + 2 + 1 = **4 simulated storeys**. The disagreement is the same `ZoneGroup`
   blindness as E-LA-35 Cause A. Whether a separate registry defect also exists is now **unknown**
   and must not be assumed either way.
3. **The exposure is the dominant archetype, and it is energy-affecting.**
   `recomputed_area_m2` for MidRise undercounts simulated floor area by a factor of **4/3**, which
   propagates into `area_scale_ratio = real_area / baseline_area` as a **~33% over-scale** of every
   absolute-quantity field, on **2,262 of the 2,932** buildings in the two inspected cells plus the
   718-building unmapped fallback target. The predecessor's claim "MidRise … does **not**
   double-count energy" is withdrawn as unproven.

**Second-order defect surfaced by the same finding — `match_storeys()` can double-bump.**
`Zone.Multiplier` and a `ZoneList` multiplier **compound** in EnergyPlus. `match_storeys()` selects
its target band from `bands[1:-1]` and writes `Zone.Multiplier` on it — which for both apartment
prototypes is exactly the band already carrying the `ZoneGroup` multiplier. Any `status: "applied"`
on these two archetypes therefore multiplies on top of an existing ×8 / ×2. Not yet measured;
routed into R01 as a required measurement, **not** as a licence to change `match_storeys()`'
fallback shares — R04(a) stands and the 81.6% / 98.4% inert population must not be perturbed.

**§4.1(b) re-verified and CONFIRMED** against `layout_assigner.py:497-511`: `fallback_shorter` for
every `n_real < n_proto`; `fallback_not_expressible` for `n_proto == 2` and for `n_proto >= 4`
(`len(bands[1:-1]) != 1`). Unchanged.

**Effect on the run.** CP-D's audit now additionally requires the MidRise ratio. R06 stays WITHHELD.
No other task's scope moves.

---

### **R10 — E-LA-36: `match_storeys()` compounds `Zone.Multiplier` on top of an existing `ZoneGroup` list multiplier** *(NEW, opened by the P1 audit 2026-07-26 — gating R06)*

- **Status.** Measured on a real run by P1, confirmed independently by the director from the code.
  **Energy-affecting, on the dominant archetype.** R06 does not run until this is fixed.
- **What is wrong.** `match_storeys()` branches on `n_proto` (the Z-band count) and writes
  `Zone.Multiplier` on `bands[1:-1]`. For the two apartment prototypes that band is exactly the
  `ZoneList` the `ZoneGroup` already multiplies, and **EnergyPlus compounds the two**. Measured on
  `MidriseApartment`, `n_real = 4` (la_suburban, real cohort): `n_proto = 3` → the taller branch sets
  `Zone.Multiplier = n_real - (n_proto - 1) = 2`, which meets the existing list multiplier of 2 →
  effective **×4**, giving **1 + 4 + 1 = 6 simulated storeys where 4 were intended — a 50%
  over-count**. `eplusout.eio` shows both multipliers on that band. The run is clean (0 Severe), so
  nothing flags it: it is a silent energy error, which is the worst kind this arc can ship.
- **The prototype was already correct.** `MidriseApartment` natively simulates 4 storeys (1 + 2×1 + 1).
  For `n_real = 4` the right answer is **no multiplier at all**.
- **How to fix — narrow, and stated so it cannot be widened.** Branch on the **ZoneGroup-aware**
  represented count, and solve for the *residual* multiplier rather than the absolute one: the target
  band's `Zone.Multiplier` must satisfy
  `non_middle_storeys + Zone.Multiplier × list_multiplier == n_real`.
  Set it only when that division is **exact and ≥ 1**; otherwise return `fallback_not_expressible`.
  A solved value of exactly 1 is a no-op and must be reported as such, not written as a redundant
  field edit.
- **🔴 What this is NOT.** It is **not** R04(b). It does not extend reach to `n_proto ∈ {2, 4+}` and
  it does not touch the shorter case. The 81.6% / 98.4% inert population must come out **byte-identical**,
  and so must all **23** prototypes that carry no `ZoneGroup`. Assert both; do not assume either.
- **How to test.** Re-run the `MidriseApartment` `n_real = 4` case and show `eio` reporting **4**
  represented storeys, not 6. Byte-identity assertion for the 23 non-ZoneGroup prototypes and for the
  shorter/not-expressible paths. Report the `HighriseApartment` case (list multiplier 8) too.

---

### **AUDIT — CP-D partial: P1 (R01+R02+R03) — director, 2026-07-26 — verdict: ACCEPTED, with one new blocker**

**Independently verified by the director** (not taken on the employee's word):

1. **Geometry is unchanged by R01 — confirmed algebraically, and it matters.** R01 made
   `recomputed_area_m2` ZoneGroup-aware (MidRise 2350.961 → 3134.614) *and* moved `plate_proto_m2` to
   `recomputed_area / n_storeys_represented`. `plate_proto_m2` is therefore **identical** before and
   after (783.65 m² both). In `calculate_scaling_factor()` (`layout_assigner.py:210-220`), passing
   `n_storeys_represented` flips the MidRise `n_real = 4` cohort from the plate branch to the identity
   branch — but the two branches evaluate to the **same** `planar_scale_factor` there
   (`sqrt(A / (4 × 783.65))` either way). **No vertex moves.** Consequences: R07 stays REDUCED, the
   four frozen viewers remain valid evidence, and the freeze is not breached. Had this gone the other
   way, R07 would have had to be reinstated in full.
2. **`area_scale_ratio` changes only where it should.** For the inert population
   (`storeys_matched=False`) it resolves to `plate_ratio`, which is unchanged. It moves only on the
   ZoneGroup archetypes with `storeys_matched=True` — the intended target.
3. **The double-bump is real** and is now **R10** above, opened as **E-LA-36**. The director re-derived
   it from the code independently of the employee's `eio` evidence; the two agree.

**Accepted findings, carried forward:**
- R01 delivered: HighRise `n_storeys_represented` 10, area → 7836.479; MidRise 4, area → 3134.614;
  byte-identity asserted over the other 23 prototypes by both a pytest and an independent diff script.
- R02: DHW nominal ratio 4.5583 → **1.3674**. Lighting/equipment/fans/pumps unchanged **to the last
  digit** and shown to be a *denominator* artifact — recomputed against the `eio`-true areas
  (51,094.16 / 3,499.60 m²) they land at 0.93–1.07×. That is the correct diagnosis and it is R05's
  scope, not R02's. The employee was right not to chase it.
- R03: `roof_scale_ratio = planar_scale_factor ** 2`, proven distinct from `transformer_scale_ratio`
  (a factor of 4 apart) rather than a same-number rename. Accepted. Noted for R08: **no real-run PV
  energy measurement exists** — neither apartment archetype carries these objects, so R03's evidence
  is synthetic-fixture only. That is what the plan's acceptance line asked for, but it is a
  synthetic-only result and must be disclosed as one.

**Two open items the director is NOT letting the employee resolve:**
- **Heating went the wrong way** on the nominal denominator: 0.8206× → **1.8267×**. Since R02 proved
  the nominal denominator is itself wrong, this number is not yet interpretable. **R05 must re-measure
  heating on the `eio` denominator and report it either way.** Per R06's acceptance line, a fix that
  does not move a ratio toward 1.0 is a *finding*, not something to reframe.
- **The plan's cited pre-fix heating figure of "0.375×" is not reproducible** from any artifact on
  disk; the measured pre-fix value was 0.8206×. The 0.375× is a predecessor-arc number with no
  surviving provenance. It is hereby **retired as unverifiable** — do not cite it again, and do not
  spend an employee reconstructing it.

**Deviation ruled on:** R01's original "How to test" line (`n_proto` must match `eio`) conflicts with
the AMENDED SCOPE box (`n_proto` stays the band count). The employee followed AMENDED SCOPE. **Correct
— the amendment governs**, and matching `eio` is the job of `n_storeys_represented` /
`recomputed_area_m2`, which it does.

**CP-D is NOT signed.** It now requires R10 and R05. R06 stays WITHHELD.

---

### R01 — **AMENDED SCOPE (supersedes the "do not widen" bullet), 2026-07-26**

- **In scope: both** `ApartmentHighRise` (×8) and `ApartmentMidRise` (×2).
- **Keep `n_proto` as the measured Z-band count.** Do **not** redefine it to the represented-storey
  count — `match_storeys()` branches on `n_proto`, and redefining it silently moves MidRise from the
  `n_proto == 3` "applied" branch to the `n_proto >= 4` "not expressible" branch, changing the
  thermal model of the dominant archetype as a side effect. That is an R04(b) move and R04 is closed
  at (a). Add a **separate** field instead (e.g. `n_storeys_represented`) and fix
  `recomputed_area_m2` / `plate_proto_m2` to be `ZoneGroup`-aware.
- **Required measurements, reported as numbers:** for each of the two files — band count,
  `ZoneList` membership, list multiplier, `recomputed_area_m2` before vs after, and the `eio` Zone
  Information total from a real run. Plus: does `match_storeys()` ever return `"applied"` on either
  archetype in the two inspected cells, and if so on which band relative to the `ZoneList`.
- **Byte-identity assertion covers the other 23 prototypes.**

---

#### R01 — `compute_band_map()` `ZoneGroup`-aware (AMENDED SCOPE, both apartment files) — completed 2026-07-26

**Artifacts:**
- `openubem/geometry/layout_assigner.py` — `compute_band_map()` (~L371-527) reads `ZONELIST`/
  `ZONEGROUP` and returns a new `n_storeys_represented` field; `n_proto` is unchanged (still the
  measured Z-band count, per the amended-scope instruction — `match_storeys()`, ~L568, still reads
  `band_map["n_proto"]` directly and is untouched).
- `openubem/idf/builder.py` (~L457-464) — the `calculate_scaling_factor()` call now passes
  `n_proto=band_map["n_storeys_represented"]` (not `band_map["n_proto"]`) so the plate-area
  denominator is storey-aware; `match_storeys()`'s own call, two lines above, is untouched and still
  reads `band_map["n_proto"]`.
- `tests/test_layout_assigner.py` — new `TestComputeBandMapZoneGroupAware` (2 parametrized +
  1 byte-identity test, 3 rows). Row count = artifact count: 3 new tests, 3 assertions of the
  measured numbers below.
- `scratchpad/r01_r02_r03_work/r01_r02_r03_runs.py` + `_results.csv` (also copied to
  `openubem/outputs/comparisons/r01_r02_r03_results.csv`) — 5 real local EnergyPlus 23.1 runs
  (`-x -r`), row count 5 = artifact count 5 (one row per case). Throwaway scratch script, not shipped.

**Required measurements (both files, `00.BaselineBuildings_NUs_v231`, `openubem/config.py:52`):**

| | `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` | `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` |
|---|---|---|
| Band count (`n_proto`) | 3 (unchanged) | 3 (unchanged) |
| `ZoneList` "Mid Floor List" membership | 9 zones: M SW/NW/SE/NE/N1/N2/S1/S2 Apartment, M Corridor | same 9 names (M-prefixed) |
| `ZoneGroup` "Middle Floors" list multiplier | 8 (line 2538, mixed-case `ZoneGroup,`) | 2 (line 2078, upper-case `ZONEGROUP,` — the AUDIT's finding) |
| `n_storeys_represented` (new field) | 10 (= 1 + 8 + 1) | 4 (= 1 + 2 + 1) |
| `recomputed_area_m2` before → after | 2350.944 → **7836.479** | 2350.961 → **3134.614** |
| `plate_proto_m2` (before vs after) | 783.648 → 783.648 (unchanged — divides by `n_storeys_represented` now, not `n_proto`; the G/M/T bands are uniform-area so the two denominators give the same per-floor plate) | 783.654 → 783.654 (unchanged, same reason) |

**`eio` Zone Information cross-check (real run, case `R01_A_highrise_identity`,
`scratchpad/r01_r02_r03_work/runs/R01_A_highrise_identity/eplusout.eio`):** this run was NOT
S=1 as originally intended (see Deviations) — `num_floors=3` vs `n_storeys_represented=10` triggers
the plate-ratio branch (`planar_scale_factor=1.826`), not identity. Cross-checked anyway: summing
`eio`'s own `Floor Area × Zone Multiplier × Zone List Multiplier` over all 27 `Zone Information`
lines gives 26,121–26,474 m² (eio's 2-decimal rounding on 27 rows), and
`recomputed_area_m2 (7836.479) × planar_scale_factor² (3.333) = 26,121.5` — matches to within the
rounding noise. `eio` itself reports `Zone Multiplier` and `Zone List Multiplier` as **two separate
columns** per zone (confirmed directly, `eplusout.eio` line 64 header), confirming EnergyPlus tracks
them independently and — per the second-order-defect measurement below — compounds them.

**Second-order defect (compounding) — measured, not fixed, per the AUDIT's routing:**
Real run `R01_C_midrise_applied4` (`MidriseApartment`, `n_real=4` — la_suburban's own real
scenario, 8/1283 buildings per the T19 harvest, `openubem/outputs/comparisons/t19_layout_assign_eui.csv`
joined against `docs/docs_VALIDATION/validations/overAll/results/phaseE/la_suburban/01_buildings.gpkg`).
`match_storeys()` **does** return `"applied"` here: `n_proto=3`, `n_real=4`, target band = the
9-zone middle band (`M SW Apartment`, …, `M Corridor` — the exact same `ZoneList` membership as
`ZoneGroup` "Middle Floors"), `multiplier=2`. The saved run's `eplusout.eio` confirms it directly —
`Zone Information, M SW APARTMENT,...,1,2,2,...` (Type,Zone Multiplier=**2**,Zone List
Multiplier=**2**) vs `Zone Information, G SW APARTMENT,...,1,1,1,...` (Zone Multiplier=1, Zone List
Multiplier=1). The two multipliers **do compound**: the middle band is simulated at effective ×4
(2 own × 2 group), so total represented storeys = 1(G) + 4(M) + 1(T) = **6**, not the intended 4 —
a 50% over-count on this population. Run completed clean: `EnergyPlus Completed Successfully-- 41
Warning; 0 Severe Errors`. **Not remediated** — `match_storeys()`'s fallback/applied branching is
untouched, per the plan's explicit instruction; forwarded as a new open defect (double-bump on
`n_storeys_represented`-eligible `ZoneGroup` archetypes when `match_storeys()` also applies).
`HighriseApartment` was not observed in either inspected cell's layout_assign population (0 rows in
both `t19_layout_assign_eui.csv` cells), so this population is currently `MidriseApartment`-only
(8 buildings, la_suburban) — `nyc_suburban`'s 979 `MidriseApartment` buildings are all
`num_floors=1` (`fallback_shorter`, never `"applied"`).

**Byte-identity, other 23 prototypes:** asserted via `tests/test_layout_assigner.py::
TestComputeBandMapZoneGroupAware::test_other_23_prototypes_byte_identical_band_map` (checks 24
non-apartment `_MAPPED_VOCAB` entries, which resolve to 23 distinct files after
`LargeOfficeDetailed`/`MediumOfficeDetailed`/`SmallOfficeDetailed` alias to their non-`Detailed`
siblings) and independently confirmed with a standalone script diffing old-vs-new
`compute_band_map()` output across all 25 files directly from `BASELINE_IDF_DIR`: **23/25 files
byte-identical** (`n_proto`, `plate_proto_m2`, `recomputed_area_m2`, all `bands[]` fields), the 2
apartment files the only ones differing, matching the table above exactly.

**Deviations:**
- The plan's own "How to test" line ("`compute_band_map()`'s `n_proto` … must match the `eio` Zone
  Information totals") is **superseded** by the AMENDED SCOPE box's "Keep `n_proto` as the measured
  Z-band count. Do NOT redefine it" — `n_proto` stays 3 for both files; only `recomputed_area_m2` is
  asserted against `eio`, per the amended text. Flagging this explicitly since the two plan passages
  conflict on this one point and the AMENDED SCOPE box is dated later (governs).
- `calculate_scaling_factor()`'s own plate-area division (`baseline_area_m2 / n_proto`, internal to
  that function) was **not** left reading the raw band count for these two archetypes — leaving it
  there would have fed the new (ZoneGroup-aware, ~3.33×/1.33× larger) `recomputed_area_m2` through
  the OLD `/3` divisor, inflating `plate_proto` by that same factor and corrupting
  `planar_scale_factor` (a real geometry-scaling regression, not a cosmetic one). The builder.py call
  site was changed to pass `n_storeys_represented` instead so `plate_proto_m2` keeps meaning "area of
  one physical floor" exactly as it did pre-fix. This is the "fix … `plate_proto_m2` to be
  `ZoneGroup`-aware" instruction from the AMENDED SCOPE box, applied at the one place that actually
  consumes it; `n_storeys_represented == n_proto` for all 23 other archetypes so this is a no-op for
  them (see byte-identity check, which covers `compute_band_map()`'s own return, and the D_control
  case above, which independently confirms `calculate_scaling_factor()`'s downstream output is
  numerically unaffected for `n_real == n_proto == 3` on `HighriseApartment` itself — see R02 below).
- `R01_A_highrise_identity`/`R01_B_midrise_identity`'s footprint areas were sized assuming
  `n_real == n_storeys_represented` would trigger `calculate_scaling_factor()`'s identity branch
  (S=1). Since that branch is gated on `num_floors == n_proto` and `n_proto` is deliberately still
  the band count (3), these two runs actually exercised the plate-ratio branch instead (harmless —
  still a valid, informative real run, used above for the `eio` cross-check) — not a defect, a
  scratch-script parameter mistake, corrected understanding recorded here rather than re-run, since
  the resulting data was still usable.

**Test status:** `pytest tests/test_layout_assigner.py -q` → 126 passed (123 pre-existing + 3 new),
`tests/test_idf_builder.py` unaffected (163 passed together). 5/5 real EnergyPlus runs completed
successfully, 0 Fatal, 0 Severe across all 5 (`eplusout.end` verbatim: `"EnergyPlus Completed
Successfully-- ... 0 Severe Errors"` for every case).

**Notes:** the `eio` header line itself (`! <Zone Information>,...,Zone Multiplier,Zone List
Multiplier,...`) is worth recording verbatim for the next reader — EnergyPlus surfaces both
multipliers as distinct, documented output columns, which is how the compounding above was
confirmed rather than inferred.

`git status --short openubem/ tests/ main.py`:
```
 M openubem/geometry/envelope_patcher.py
 M openubem/geometry/layout_assigner.py
 M openubem/idf/builder.py
 M tests/fixtures/synthetic_30_archetype_coverage.gpkg
 M tests/test_layout_assigner.py
?? openubem/idf/opaque_assembly.py
?? tests/test_opaque_assembly.py
```
(`envelope_patcher.py`, `opaque_assembly.py`/`test_opaque_assembly.py`, and the fixture `.gpkg` are
pre-existing modifications from earlier, unrelated sessions — not touched by R01/R02/R03.)

---

#### R02 — `WaterUse:Equipment`/`People` double-count carve-out, D pair re-run — completed 2026-07-26

**Artifacts:**
- `openubem/geometry/layout_assigner.py` — `calculate_scaling_factor()` (~L144-283) unchanged from
  the pre-existing D2/D9 storey-matching mechanism already in the working tree (`storeys_matched`
  pins `area_scale_ratio` to the plate ratio for non-`"applied"` cases; this is what makes the
  carve-out correct — see Deviations for why no separate carve-out field was added).
- `scratchpad/r01_r02_r03_work/r02_d_control_only.py` + `r02_d_control_results.csv` (also copied to
  `openubem/outputs/comparisons/r02_d_control_results.csv`) — the corrected D-pair control run.
  Row count 1 = artifact count 1.
- Combined with R01's `r01_r02_r03_results.csv` (`D_HIGHMULT_highrise20` row) for the full pair.

**Control-vs-treatment proof (rule 6):** `D_control_S1_highrise3` (`HighriseApartment`, `n_real=3`,
footprint=350 m², `match_storeys()` → `"identity"`, `storeys_matched=False`) and
`D_HIGHMULT_highrise20` (same archetype, `n_real=20`, same footprint, `match_storeys()` → `"applied"`,
`multiplier=18`, `storeys_matched=True`) are the two `.idf`s C01 named the D pair. Byte-compared: the
built IDFs differ in `Zone.Multiplier` (D: 18 on the 9 middle-band zones vs C: 1 everywhere) and in
every absolute-load field scaled by `area_scale_ratio`/`transformer_scale_ratio`; the control is
provably not the treatment.

**Measured EUI (real EnergyPlus runs, `_parse_sql()`, `openubem/outputs/comparisons/*.csv`),
nominal denominator (C01's own convention, `footprint_area_m2 × n_real`, UNCHANGED — R05, not this
task, owns fixing the denominator):**

| field | D (n=20) | C (n=3) | D/C ratio (post R01+R02+R03) | pre-fix D/C ratio (`c01_regression_results.csv`) |
|---|---|---|---|---|
| lighting_eui | 29.263 | 13.845 | 2.1137 | 2.1137 (unchanged) |
| equipment_eui | 255.816 | 125.171 | 2.0437 | 2.0437 (unchanged) |
| fans_eui | 71.053 | 30.908 | 2.2989 | 2.2989 (unchanged) |
| pumps_eui | 20.880 | 8.890 | 2.3489 | 2.3489 (unchanged) |
| dhw_eui | 212.868 | 155.674 | **1.3674** | 4.5583 |
| heating_eui | 297.067 | 162.629 | **1.8267** | 0.8206 |
| cooling_eui | 51.645 | 20.136 | 2.5648 | 2.4939 |
| total_eui | 938.592 | 517.251 | 1.8146 | 2.5837 |

**Finding, reported plainly (rule: "not a rounding issue to reframe"):** using this nominal
denominator, lighting/equipment/fans/pumps EUI ratios do **not** reconcile to ≈1.0 — they are
**identical, to the last digit**, to the pre-fix ratios. This is expected, not a defect in R02: those
four fields are `Watts/Area`-gated (immune to `area_scale_ratio` by construction, confirmed
byte-identical in the raw scaled IDFs both before and after this task) — R02's carve-out cannot move
a number that was never wrong at the field level. The ratio ≠ 1.0 is **entirely a denominator
artifact**: D's true simulated floor area (`eio`, see below) is 51,094.16 m² against a nominal
7,000 m², while C's is 3,499.60 m² against a nominal 1,050 m² — different mismatch ratios for D vs
C, so even byte-identical W/m² fields produce a nominal-EUI ratio ≠ 1.0. Recomputing EUI against the
`eio`-true denominators (51,094.16 / 3,499.60 m², matching the plan's own R05 text exactly) gives
lighting 0.9651, equipment 0.9332, fans 1.0497, pumps 1.0725 — all close to 1.0, confirming the
reconciliation genuinely happens once R05's denominator fix lands, and is not blocked on anything in
R01/R02/R03. **This is forwarded to R05, not fixed here** (R05 owns the denominator; out of this
task's scope).

**DHW (R02's own target):** nominal ratio moved from 4.5583 (pre-fix) to **1.3674** (post
R01+R02+R03) — real, substantial closure, attributable to the `WaterUse:Equipment`/`People`
carve-out (People affects DHW only indirectly via occupancy-linked draw schedules in this baseline;
the dominant mechanism is `WaterUse:Equipment.Peak_Flow_Rate` no longer being scaled by the
whole-building `area_scale_ratio` on top of EnergyPlus's own ×18 zone-multiplier replication). Not
fully closed to 1.0 — the residual is consistent with the same denominator artifact described above
(`eio`-true DHW ratio was not separately isolated from the aggregate WaterSystems meter in this pass;
forwarded alongside the general denominator finding, not asserted resolved).

**Heating, reported as instructed ("whether it does or not"):** nominal ratio moved from **0.8206**
(pre-fix) to **1.8267** (post-fix) — it moved, but away from 1.0, not toward it, on the nominal
denominator. This is the same denominator artifact: heating EUI is not a pure `Watts/Area` field (it
responds to the internal-gains reduction from the `WaterUse:Equipment`/`People` fix, in the opposite
direction from DHW), and the absolute heating capacity itself is unaffected by R02 (no heating
capacity field is on the `_UNCONDITIONAL_ABSOLUTE_SPECS`/`_NAMED_ABSOLUTE_SPECS` lists this task
touched). Plan text (R02's "How to test") cites a pre-fix heating ratio of "0.375×" that this
executor's own artifacts do not reproduce — the pre-fix `c01_regression_results.csv` on disk (already
present at task start, not generated by this task) shows 0.8206, not 0.375. Reported verbatim per
rule 8 (ground truth from run artifacts, never a restatement of a prior hypothesis); this discrepancy
is flagged for the director to reconcile, not silently resolved in either direction.

**Test status:** Zero Fatal, Zero Severe on both D-pair runs (`eplusout.end` verbatim:
`"EnergyPlus Completed Successfully-- 62156231 Warning; 0 Severe Errors"` (C, D:
`"...67130259 Warning; 0 Severe Errors"`) — the anomalously large Warning counts are pre-existing
EnergyPlus behaviour on a repeated DHW setpoint warning, not new, and were also present in this
task's other 3 runs; not investigated further, out of R02's scope.

**Deviations:** none beyond what's stated above (the pre-fix "0.375×" heating figure not
reproducible from available artifacts).

`git status --short` — unchanged from R01's entry above (same file set; no additional production
files touched by R02, which reused the existing `storeys_matched`/`area_scale_ratio` mechanism
without modification).

---

#### R03 — `Generator:PVWatts`/`ElectricLoadCenter:Generators` scale by roof area, not `area_scale_ratio` — completed 2026-07-26

**Artifacts:**
- `openubem/geometry/layout_assigner.py`:
  - `calculate_scaling_factor()` (~L144-291) — new `roof_scale_ratio = planar_scale_factor ** 2` in
    the returned dict, always computed (not gated on `storeys_matched`), documented as invariant to
    the multiplier by construction.
  - `_UNCONDITIONAL_ABSOLUTE_SPECS` (~L640-745) — `("ELECTRICLOADCENTER:GENERATORS",
    "Generator_1_Rated_Electric_Power_Output")` and `("GENERATOR:PVWATTS", "DC_System_Capacity")`
    removed from this list (were scaling by `area_scale_ratio`).
  - `scale_baseline_idf()` (~L876-1035) — new dedicated loop (mirroring the D9 Transformer loop
    immediately above it) scaling both fields by `roof_scale_ratio` instead.
- `tests/test_layout_assigner.py` — new `TestRoofScaleRatioPVInvariance` (3 tests, 3 rows: ratio
  invariance under a multiplier, `scale_baseline_idf()` applies `roof_scale_ratio` not
  `area_scale_ratio`/`transformer_scale_ratio`, autosize is still skipped).

**Required assertion ("PV nameplate is invariant to the multiplier at fixed roof area"):**
`test_roof_scale_ratio_is_planar_squared_and_ignores_multiplier` constructs
`calculate_scaling_factor()` twice at identical `real_area_m2`/`baseline_area_m2`/`num_floors`/
`n_proto` (hence identical `planar_scale_factor`, i.e. fixed roof/plan-area growth), once with
`storeys_matched=True, multiplier=4` and once with `storeys_matched=False, multiplier=None`:
`roof_scale_ratio` is asserted `==` (to `rel=1e-12`) between the two calls, and equal to
`planar_scale_factor ** 2` — proving it is invariant to whether a Zone Multiplier applied, unlike
`transformer_scale_ratio` (asserted `== roof_scale_ratio * 4` in the same test, i.e. genuinely a
different number, not a rename). `test_scale_baseline_idf_scales_pvwatts_and_generators_by_roof_not_
area_ratio` builds a synthetic 2-zone fixture with `GENERATOR:PVWATTS`/`ELECTRICLOADCENTER:GENERATORS`
objects, scales at `storeys_matched=True, multiplier=4`, and asserts both fields land at
`50000.0 * roof_scale_ratio` and explicitly **not** at `area_scale_ratio` or `transformer_scale_ratio`
(both would be numerically different at this multiplier, so the assertion is discriminating, not
vacuous).

**Population note:** neither `HighriseApartment` nor `MidriseApartment` (R01/R02's population)
carries `GENERATOR:PVWATTS`/`ELECTRICLOADCENTER:GENERATORS` objects, so this fix was not exercised
by R01/R02's real EnergyPlus runs — the fix is population-disjoint from R01/R02 (the plan's own
comment block, pre-existing, cites "12/25 baselines" for each field). No real-run PV measurement was
taken in this task; the synthetic-fixture assertion above is the acceptance test the plan specified
("Assert PV nameplate is invariant..." — a unit-level invariance claim, not a fleet-energy claim).

**Test status:** `pytest tests/test_layout_assigner.py -q -k RoofScale` → 3 passed. Full suite:
126 passed total (120 pre-existing at session start + 3 `TestComputeBandMapZoneGroupAware` (R01) +
3 `TestRoofScaleRatioPVInvariance` (R03) = 126 — the same full-suite run reported in R01's entry
above; R02 added no new tests of its own.

**Deviations:** none.

`git status --short` — unchanged file set from R01/R02 (same two production files,
`layout_assigner.py`/`builder.py`, plus the one test file).

---

#### R10 — E-LA-36: `match_storeys()` solves for the RESIDUAL multiplier — completed 2026-07-26

**Artifacts:**
- `openubem/geometry/layout_assigner.py` — `match_storeys()` (docstring + body, ~L539-655 after
  this edit). The taller branch no longer writes `n_real - (n_proto - 1)` (or `n_real` for the
  `n_proto == 1` case) directly as `Zone.Multiplier`. It now computes
  `list_multiplier = target_band["storeys_in_band"]` (the ZoneGroup list multiplier
  `compute_band_map()` already carries per band, R01) and
  `non_middle_storeys = sum(b["storeys_in_band"] for b in bands if b is not target_band)`, then
  solves `residual_multiplier = (n_real - non_middle_storeys) / list_multiplier`. Written to
  `Zone.Multiplier` only when that division is exact and `>= 1`; otherwise `"fallback_not_expressible"`.
  When `residual_multiplier == 1` the status is still `"applied"` (n_real IS matched) but
  `band_zone_names` is `[]` and no `Zone.Multiplier` field is written — the "no redundant field
  edit" instruction. `builder.py` was **not** touched — untouched by design, since
  `calculate_scaling_factor()` already receives `n_storeys_represented` as its `n_proto` (R01), and
  for every case measured (see below) `num_floors == n_storeys_represented` whenever
  `residual_multiplier == 1`, so the identity branch fires there regardless of the `storeys_matched`
  flag's exact value — no downstream numeric effect from leaving `builder.py` alone (verified
  algebraically: `transformer_scale_ratio` collapses to `planar_scale_factor ** 2 * 1 ==
  planar_scale_factor ** 2 == area_scale_ratio` in the identity branch either way).
- `tests/test_layout_assigner.py` — new `TestMatchStoreysResidualZoneGroup` (6 tests, 6 rows):
  `test_midrise_n_real_4_residual_is_1_no_field_write`, `test_highrise_n_real_10_residual_is_1_no_field_write`,
  `test_highrise_n_real_18_writes_exact_residual_2`, `test_highrise_n_real_not_exactly_divisible_falls_back`,
  `test_other_23_prototypes_byte_identical_taller_case` (MediumOffice, list_multiplier==1 for every
  band — asserts the residual formula reduces bit-for-bit to the pre-R10 absolute formula, same
  multiplier=4, same 5-zone `band_zone_names`), `test_other_23_prototypes_byte_identical_degenerate_case`
  (RetailStandalone, `n_proto==1` — same multiplier=3 as pre-R10).
- `scratchpad/r10_r05_work/r10_runs.py` + `r10_results.csv` (also copied to
  `openubem/outputs/comparisons/r10_results.csv`) — 3 real local EnergyPlus 23.1 runs, row count 3 =
  artifact count 3 (one row per case; also 3 real per-building `scratchpad/r10_r05_work/runs/<case>/`
  directories with full EnergyPlus output sets, including `eplusout.eio`/`.err`/`.end`).

**Acceptance — MidriseApartment `n_real=4` (R10's own required test):**
`match_storeys()` pre-run: `n_proto=3`, `n_storeys_represented=4`, `status=applied`, `multiplier=1`,
`band_zone_names=[]` (no field write). Real run `R10_A_midrise_n4`
(`scratchpad/r10_r05_work/runs/R10_A_midrise_n4/eplusout.eio`): `M SW APARTMENT` row reads
`Type=1, Zone Multiplier=1, Zone List Multiplier=2` — **own `Zone.Multiplier` is 1** (untouched,
default), confirming no redundant field write. Summing `Zone Multiplier x Zone List Multiplier`
over the SW column (G SW=1x1=1, M SW=1x2=2, T SW=1x1=1) gives **4 represented storeys, not 6** —
the exact defect this task fixes. Run completed clean: `eplusout.end` verbatim
`"EnergyPlus Completed Successfully-- 41 Warning; 0 Severe Errors; Elapsed Time=00hr 01min 28.02sec"`.

**HighriseApartment (list multiplier 8), reported per the plan's explicit instruction:**
- `R10_C_highrise_n10` (`n_real=10`, the archetype's own native represented count):
  `non_middle_storeys=2`, `list_multiplier=8`, `raw=8`, `residual=1` → no-op, no field write.
  eio SW-column sum: G SW=1x1 + M SW=1x8 + T SW=1x1 = **10**. `eplusout.end`:
  `"EnergyPlus Completed Successfully-- 64775527 Warning; 0 Severe Errors"` (the anomalously large
  warning count is the same pre-existing repeated-DHW-setpoint-warning behaviour R02 already
  flagged as out-of-scope, not new).
- `R10_B_highrise_n18` (`n_real=18`, exercises an actual non-1 residual write):
  `non_middle_storeys=2`, `raw=16`, `residual=16/8=2` (exact, `>1`) → `Zone.Multiplier=2` written on
  the 9 middle-band zones. eio SW-column sum: G SW=1x1 + M SW=2x8 + T SW=1x1 = **18**, matching
  `n_real` exactly (the pre-R10 absolute formula would have written `Multiplier=8`
  (`10 - (3-1)`... actually `n_real-(n_proto-1)=18-2=16`, compounding to 1+16x8+1=**130** simulated
  storeys — an even larger over-count than MidRise's, confirming this defect scaled with the list
  multiplier). `eplusout.end`: `"EnergyPlus Completed Successfully-- 65553660 Warning; 0 Severe Errors"`.

**Byte-identity — the 81.6%/98.4% inert population and the 23 non-ZoneGroup prototypes:**
Asserted two ways. (1) All 5 pre-existing `TestMatchStoreys` tests (identity, taller-known-multiplier,
degenerate-single-band, shorter-fallback, taller-not-expressible) pass **unchanged**, with the same
asserted `multiplier`/`band_zone_names`/`status` values as before this task — these ARE the
byte-identity proof for `fallback_shorter`/`fallback_not_expressible` (the inert population, R10
never reaches the residual-solving code for either) and for the "applied" case on a non-ZoneGroup
archetype (MediumOffice). (2) The two new dedicated byte-identity tests above
(`test_other_23_prototypes_byte_identical_taller_case`/`_degenerate_case`) additionally assert the
residual formula reduces algebraically to the pre-R10 formula whenever `list_multiplier == 1`, which
is true for all 23 non-ZoneGroup prototypes (proved in R01's `test_other_23_prototypes_byte_identical_band_map`:
every one of their bands has `storeys_in_band == 1.0`).

**Deviations:** none. `builder.py` was considered and deliberately left untouched (see Artifacts,
above) rather than being extended to consume a new "field written" flag — out of scope per the
plan's narrow instruction, and verified to have no numeric effect on the two cases where it would
matter (`residual_multiplier == 1`).

**Test status:** `pytest tests/test_layout_assigner.py -q` → **132 passed** (126 pre-existing +
6 new `TestMatchStoreysResidualZoneGroup`). 3/3 real EnergyPlus runs completed successfully, 0 Fatal,
0 Severe across all 3 (`eplusout.end` verbatim `"EnergyPlus Completed Successfully-- ... 0 Severe
Errors"` for every case).

**Notes:** the first run attempt of this task's own harness collided with itself (a shell
double-backgrounding mistake left an orphaned `energyplus.exe` holding file locks on
`R10_A_midrise_n4`'s output directory, producing a spurious `**  Fatal  ** ... Could not open file
"...rvi" for output (write)` — a harness artifact, not a defect in the fix). Killed the orphaned
process, deleted the partial run directory, and re-ran cleanly; the clean re-run is what is reported
above. Recorded here per rule 4 (quote the Severe/Fatal line verbatim) even though it does not
belong to the fix being measured.

`git status --short openubem/ tests/ main.py`:
```
 M openubem/geometry/envelope_patcher.py
 M openubem/geometry/layout_assigner.py
 M openubem/idf/builder.py
 M tests/fixtures/synthetic_30_archetype_coverage.gpkg
 M tests/test_layout_assigner.py
?? openubem/idf/opaque_assembly.py
?? tests/test_opaque_assembly.py
```
(`envelope_patcher.py`, `opaque_assembly.py`/`test_opaque_assembly.py`, and the fixture `.gpkg` are
pre-existing modifications from earlier, unrelated sessions, same as noted in R01's entry.
`builder.py`'s diff is R01/R02/R03's `n_storeys_represented` passthrough, unchanged by this task —
see Artifacts, above, for why.)

---

#### R05 — C01-bis: re-run after R01-R03+R10, denominator fixed — completed 2026-07-26

**Artifacts:**
- `scratchpad/r10_r05_work/r05_runs.py` + `r05_c01bis_results.csv` (also copied to
  `openubem/outputs/comparisons/r05_c01bis_results.csv`) — 7 real local EnergyPlus 23.1 runs (the
  same 7 cases already on disk in `openubem/outputs/comparisons/c01_regression_results.csv`: A, B,
  C, `D_HIGHMULT_highrise20`, `D_control_S1_highrise3`, E, F). Row count 7 = artifact count 7 (one
  row per case; 7 real per-building `scratchpad/r10_r05_work/r05/runs/<case>/` directories with full
  EnergyPlus output sets).
- Denominator fix: `eio_true_floor_area_m2()` sums `Floor Area x Zone Multiplier x Zone List
  Multiplier` over **every** `Zone Information` row in `eplusout.eio` (not just one column) —
  verified against 3 independent R10 runs before use (identity-branch cases landed within eio
  rounding noise of `footprint x n_real`, plate-branch cases matched the algebraic prediction from
  `calculate_scaling_factor()`'s own plate-ratio math).

**Zero Fatal, every Severe named and attributed:** all 7 cases returned `run_status="success"`
(`classify_outcome()`'s `"failed_fatal"` token never appears — zero Fatal). Exactly one case has
Severe: `F_excluded_fallback_smalloffice`, **5** Severe, same as C01's own pre-fix run (SmallOffice
carries no `ZoneGroup` and is `fallback_not_expressible` both before and after R10 — this population
is untouched by R01/R02/R03/R10, so its pre-existing defect is unaffected, not new). Verbatim:
```
** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="CORE_ZN" did not converge after 25 warmup days.
** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="PERIMETER_ZN_1" did not converge after 25 warmup days.
** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="PERIMETER_ZN_2" did not converge after 25 warmup days.
** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="PERIMETER_ZN_3" did not converge after 25 warmup days.
** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="PERIMETER_ZN_4" did not converge after 25 warmup days.
```
All 6 other cases: 0 Severe.

**🔴 Load-bearing finding, not anticipated by the plan text: R10 changes `D_HIGHMULT_highrise20`'s
own `match_storeys()` status.** `HighriseApartment` carries a `ZoneGroup` list multiplier of 8
(R01's finding). For `n_real=20`: `non_middle_storeys=2`, `raw=18`, and `18 % 8 == 2 != 0` — **not
exactly divisible**. Per R10's own explicit rule ("write it only when that division is exact and
>= 1; otherwise `fallback_not_expressible`"), this case now returns **`fallback_not_expressible`**,
not `"applied"` with the pre-fix absolute multiplier of 18. This is not a bug or a scope violation —
it is R10 working exactly as specified: the pre-fix multiplier of 18 was never a value EnergyPlus
could apply correctly (it would have compounded to 1 + 18x8 + 1 = 146 simulated storeys against an
intended 20), and 18 genuinely has no exact residual solution against a list multiplier of 8, so
correctly falling back is the right outcome, not a defect to work around.

**Consequence for the D pair, "residual explained" per R05's acceptance line:** because
`D_HIGHMULT_highrise20` now falls back to the same plate-ratio-only scaling path as
`D_control_S1_highrise3` (both `storeys_matched=False`), and both cases share the **same footprint**
(350 m2), `plate_target = real_area / num_floors = footprint` cancels `num_floors` identically for
both — the two cases now scale to the **exact same total simulated area**
(`eio_true_floor_area_m2 = 3499.60` for both, to 2 decimals) and produce **byte-identical per-area
EUI on every end use, to the reported precision**:

| field | D_HIGHMULT (eio) | D_control (eio) | ratio |
|---|---|---|---|
| heating_eui | 48.794169 | 48.794169 | 1.0000 |
| cooling_eui | 6.041438 | 6.041438 | 1.0000 |
| lighting_eui | 4.153874 | 4.153874 | 1.0000 |
| equipment_eui | 37.555590 | 37.555590 | 1.0000 |
| fans_eui | 9.273437 | 9.273437 | 1.0000 |
| pumps_eui | 2.667170 | 2.667170 | 1.0000 |
| dhw_eui | 46.707402 | 46.707402 | 1.0000 |
| total_eui | 155.193081 | 155.193081 | 1.0000 |

**This is the residual, explained, not merely reported:** it closes to exactly 1.0000 because R10
correctly disqualifies `n_real=20` from being expressible, which makes the "treatment" and "control"
follow the identical code path. The D pair no longer tests a matched-multiplier scenario at all —
that scenario (`n_real=20` against `HighriseApartment`) is not one the fixed mechanism can express.
**On the OLD nominal denominator** (which R05 was explicitly tasked to stop using), the same two
cases look wildly different — `total_eui` 77.588 (D_HIGHMULT, divided by a nominal 7,000 m2) vs
517.251 (D_control, divided by a nominal 1,050 m2) — purely a denominator artifact from using
different nominal `n_real` values on two cases that are now geometrically identical. This is exactly
why R05 was tasked to fix the denominator first: the nominal ratio (0.15x) and the eio-true ratio
(1.0000x) tell opposite stories about the same two IDFs.

**Heating, re-measured on the `eio` denominator, reported plainly per CP-D's explicit requirement:**
`heating_eui_eio` for `D_HIGHMULT_highrise20` vs `D_control_S1_highrise3` = **1.0000x** (48.794169 /
48.794169, exact convergence — see table above). This is the strongest possible form of "moved
toward 1.0": it did not partially close, it fully converged, because of the mechanism explained
above (both cases now execute the identical fallback code path). On the **nominal** denominator
(pre-R05, for contrast only, not the reported number): heating_eui = 24.394 (D_HIGHMULT) vs 162.629
(D_control) = **0.1500x** — moved further from 1.0 than even the R02 audit's 1.8267x, because R10
additionally changed D_HIGHMULT's `n_real` divisor mismatch. Per rule 8, the nominal number is
reported here only to show why it is unusable, not as an interpretable finding in its own right; the
eio-true 1.0000x is the number that answers R05's question.

**The other 5 cases — unaffected by R10, denominator-fix-only comparison (nominal old vs nominal
new, byte-identical to the last digit, confirming R10 is a true no-op for non-ZoneGroup archetypes
and for `HighriseApartment`'s own identity/shorter cases):**

| case_id | archetype | old nominal total_eui | new nominal total_eui | new eio-true total_eui | eio_true_floor_area_m2 (nominal) |
|---|---|---|---|---|---|
| A_equal_identity_highrise | HighriseApartment n=3 | 477.843 | 477.843 | 143.344 | 5000.30 (1500.0) |
| B_taller_known_medoffice | MediumOffice n=6 | 126.149 | 126.149 | 84.099 | 9000.00 (6000.0) |
| C_shorter_midrise | MidriseApartment n=2 | 299.978 | 299.978 | 150.007 | 999.88 (500.0) |
| E_single_storey_retail | RetailStandalone n=3 | 214.678 | 214.678 | 214.680 | 2399.97 (2400.0) |
| F_excluded_fallback_smalloffice | SmallOffice n=4 | 20.739 | 20.739 | 41.478 | 600.01 (1200.0) |

**Deviations:** none from R05's own text. The plan's "reconciled with the residual explained" line
did not anticipate that the residual would close via a `match_storeys()` status change rather than
via the denominator fix alone — flagged explicitly above per rule 7/8 (ground truth from run
artifacts, not a restatement of the plan's own framing), not silently absorbed into the table.

**Test status:** N/A (measurement task, no new pytest — R05 is a real-EnergyPlus regression re-run,
covered by R10's own pytest suite for the code it exercises). 7/7 real EnergyPlus runs completed,
0 Fatal, 1/7 with Severe (F, 5 Severe, pre-existing and unrelated to this arc's changes, named and
attributed above).

`git status --short openubem/ tests/ main.py`: unchanged from R10's entry above — R05 is a
measurement task and touched no production files.

---

## 🔶 AUDIT — CP-D — director — 2026-07-26 — **SIGNED, with three conditions carried into R06**

Audited: R10 and R05. **Verdict: CP-D is SIGNED. R06 is released from WITHHELD.**

### 1. What I verified myself rather than accepting from the employee's report

I did not take the "eio confirms 4 storeys" claim on trust — I read the three
`eplusout.eio` Zone Information tables directly and summed the multiplier columns:

| Run | G band | M band (`Zone.Multiplier` × list) | T band | **Represented storeys** | `n_real` |
|---|---|---|---|---|---|
| `R10_A_midrise_n4` | 1 × 1 | **1 × 2 = 2** | 1 × 1 | **4** | 4 ✅ |
| `R10_B_highrise_n18` | 1 × 1 | **2 × 8 = 16** | 1 × 1 | **18** | 18 ✅ |
| `R10_C_highrise_n10` | 1 × 1 | **1 × 8 = 8** | 1 × 1 | **10** | 10 ✅ |

Pre-R10 the same three cases would have written the absolute multiplier and compounded to
6, 130 and 10 storeys. **E-LA-36 is fixed, on real EnergyPlus output, at both list
multipliers (2 and 8) and on both sides of the residual == 1 no-op.** This was CP-D's
gating question and it is genuinely met.

I also re-derived the residual formula's reduction for the 23 non-ZoneGroup prototypes
(`list_multiplier == 1`, `non_middle_storeys == n_proto - 1`, or `0` for the `n_proto == 1`
degenerate branch): it collapses bit-for-bit to the pre-R10 `n_real - (n_proto - 1)`.
The inert population and the non-ZoneGroup applied population are untouched, as claimed.

### 2. 🔴 The R05 heating ratio of **1.0000× is vacuous** and must not be reported as a result

The employee reported it honestly and explained the mechanism — credit for that — but the
director's ruling is that it **does not answer F-08**, and the distinction matters enough to
put in the record.

R10 flips `D_HIGHMULT_highrise20` to `fallback_not_expressible` (18 is not divisible by the
list multiplier 8). `D_control_S1_highrise3` was already `identity`. The two cases therefore
now execute the **same code path on the same footprint**, i.e. the same IDF. A ratio of
exactly 1.0000 between a file and itself is an identity, not a measurement. It is **not**
evidence that storey matching corrects heating; it is evidence that the two cases stopped
differing.

**F-08's heating question is UNANSWERED, not answered.** Do not cite 1.0000× as convergence
anywhere in R08. R06 carries the re-measurement (condition (a) below).

### 3. `r10_results.csv` is **not citable as evidence** — provenance defect in the harness

`eio_represented_storeys_sw_stack` is `0.0` and `n_eio_zone_info_lines` is `0` on all three
rows: the bespoke harness's eio parser captured the header and no data lines. Its
`floor_area_m2` column is **nominal** (`footprint × n_real`), not eio-derived, despite sitting
beside eio-named columns. The fix is correct — I proved it from the raw `.eio` above — but
**the CSV does not contain the proof its own report cites.** Anyone citing that file later is
citing nothing. The raw `eplusout.eio` files under `scratchpad/r10_r05_work/runs/` are the
evidence; the CSV is not. I could not reconcile that harness's scaled plate areas with the
pipeline's, and I am not spending an employee on a throwaway harness — R06 settles it at
fleet scale under condition (c).

### 4. 🔴 New consequence nobody costed: R10 **shrinks the expressible population**

Exactness (no silent rounding — correctly implemented) means a ZoneGroup archetype is now
matchable only when `n_real - non_middle_storeys` divides evenly by the list multiplier:

- `HighriseApartment` (list 8): only `n_real ∈ {10, 18, 26, …}` — **7 of every 8 taller cases
  now fall back.**
- `MidriseApartment` (list 2): only **even** `n_real ≥ 4` — about half of taller cases fall back.

This is R10 working as designed: those buildings were previously "applied" **and wrong**.
Falling back is strictly better than a silently over-counted building. But it materially
changes the applied/inert split, so the **81.6% / 98.4% inert shares in R08's disclosure list
are now stale** and the arc's headline reach is smaller than the plan assumed. Measured at
fleet scale under condition (b); disclosed in R08.

**Not reopened here:** editing the `ZoneGroup`'s own Zone List Multiplier field would restore
exact expressibility at every `n_real`. It is a different mechanism from D3(a)'s
`Zone.Multiplier` and R04 is closed at option (a). **Forwarded out as E-LA-37**, not actioned
in this arc — opening it now costs a mechanism change, a new employee and a 15 h cluster delay
to buy reach we have not shown we need.

### 5. Conditions carried into R06 (binding — R06 is not complete without all three)

- **(a)** Re-measure F-08's heating ratio on a pair where **at least one side is `applied` with
  a residual multiplier ≥ 2**. A pair that has collapsed onto one code path is not a
  measurement. Report the value whether or not it moves toward 1.0.
- **(b)** Report the fleet-scale count of buildings whose `match_storeys()` status **changed**
  under R10, split by archetype and by old → new status. This is the number R08 discloses.
- **(c)** For every building with status `applied`, assert `eio` total floor area ==
  `footprint × num_floors` within tolerance, and report any population that fails. Fallback
  buildings legitimately differ (D3(a)) and are excluded from this assertion, not from the count.

### 6. Housekeeping accepted

The orphaned-`energyplus.exe` harness hiccup was self-reported, correctly diagnosed as a
harness artifact and not a defect, and the run redone clean. Reporting it rather than hiding
it is the behaviour the rule asks for. `builder.py` left untouched: verified as a genuine
no-op for the `residual == 1` case. 132/132 tests. Only `layout_assigner.py` and
`test_layout_assigner.py` newly modified.

**CP-D SIGNED. R06 released.** Remaining path: R06 → R09 → R08 → CP-E.

---

## ⏳ IN-FLIGHT NOTE — R06 — director — 2026-07-26 — **R06 is NOT complete; no R06 progress-log entry exists yet**

Recorded so the next session does not misread a half-finished run as a finished one, and does not
double-dispatch onto a live output directory.

**State on disk.** The T20 sweep is running. Local Step2/Step3 generation is alive (≈22 `python.exe`
workers accumulating CPU — checked, not assumed). Cells are shipped and `sbatch --array`-submitted
one at a time as each finishes generating, so the login node is never blocked. Arrays confirmed live:
**1160724** (`nyc_centre`, 738) and **1160741** (`nyc_urban`, 1,779); `nyc_suburban` was queued to
ship next; 3 of 12 manifests existed. Monitoring is delegated to a cheap-model employee at a
≥30 min interval.

**Scripts landed** (tag-rename derivatives of T19's proven infrastructure, the same way T17→T18→T19
were made): `scripts/cluster/t20_layout_assign_full_sweep.py`,
`scripts/cluster/t20_harvest_layout_assign.py`, `scripts/cluster/t20_r10_reach_change.py`.
No `t20_*` path collisions existed remotely before submission — checked.

**Preliminary CP-D condition (b) result, on 2 of 12 cells (2,244 buildings): 4 buildings changed
status**, all `HighriseApartment`/`MidriseApartment`, all `applied → fallback_not_expressible`.
Direction matches the CP-D audit's prediction. **Not a fleet number** — must be re-run once all 12
manifests exist.

> **⚠️ Provenance caveat on that script, for whoever finishes it.** `t20_r10_reach_change.py`
> computes its "before" side by **reimplementing** the pre-R10 formula (`n_real - (n_proto - 1)`,
> always applied) rather than executing the real pre-R10 code. That is defensible — the old code no
> longer exists on `main` — but it is a reimplementation, and this arc has already been burned once
> by a bespoke harness producing lookalike evidence (see the CP-D audit §3). Either state the
> reimplementation plainly in the R06 entry, or take the "before" side from the pre-R10 commit in git
> history. Do not present it as measured output of the old pipeline.

**Correctly NOT done** (and the executor was right not to fake it): the extended harvest — F-08's
heating pair on the `eio`-true denominator, the D9 transformer sweep, the E-LA-36 fleet regression
check, and the applied-population denominator assertion — all need real fetched
`eplusout.eio` / `eplusout.err` that do not exist yet. Writing untested parsing logic against absent
data is exactly what R06's evidence rule forbids. No partial R06 entry was written, which is the
right call: R06 is not complete without all seven reported items.

**Employee count.** 3 of the remainder's 4-employee target consumed (P1, P2, R06-part-1), plus the
cheap monitor. Over target by the unplanned R10 defect, which is a defensible overrun: R10 was a
silent 50% energy error on the dominant archetype, found by auditing rather than by luck.

---

## ⏸️ PARK NOTE — director — 2026-07-27 — **T20 fleet COMPLETE; arc parked before R06b**

User moved to another project. Nothing is blocked and no decision is owed — the arc is parked
mid-critical-path, one dispatch away from resuming.

**T20 cluster state, verified by the director with login-node-only commands.**
`squeue -u $USER -h | wc -l` → **0** (nothing pending, nothing running).
`sacct -u $USER -S 2026-07-25 -X -P -o JobName,State | grep t20_` → all 12 cells present:

| Cell | COMPLETED | FAILED | Cell | COMPLETED | FAILED |
|---|---:|---:|---|---:|---:|
| nyc_urban | 1 779 | 0 | la_suburban | 1 343 | 0 |
| nyc_suburban | 1 589 | 0 | la_urban | 615 | **3** |
| nyc_centre | 738 | 0 | la_centre | 225 | **1** |
| nyc_rural | 195 | **3** | la_rural | 149 | 0 |
| austin_suburban | 437 | 0 | austin_centre | 413 | 0 |
| austin_urban | 425 | 0 | austin_rural | 245 | 0 |

**8 153 COMPLETED + 7 FAILED = 8 160**, the exact fleet size — no task missing, 12/12 arrays done,
SLURM-level failure rate 0.086%. **The 7 SLURM-level FAILED tasks are not the same thing as
simulation-level failures** and must each be mapped to a known defect ID (or explained) in the R06
entry, not absorbed silently into the success-rate arithmetic.

**Still true at park:** R06 is NOT complete, no R06 progress-log entry exists, no `t20_*` artifact
exists under `results/` — the harvest has never run. Do **not** re-submit the fleet.

**Resume point:** `layoutAssigner/prompt/DIRECTOR_PROMPT_storey-matching-closure_2026-07-27.md`
(self-contained; paste into a fresh manager session). Critical path unchanged:
**R06b → director audit → R09 → R08 → CP-E.** Both executor prompts are already written and current:
`prompt/EXECUTOR_PROMPT_R06b_harvest.md` and `prompt/EXECUTOR_PROMPT_R09_R08_closure.md`.
