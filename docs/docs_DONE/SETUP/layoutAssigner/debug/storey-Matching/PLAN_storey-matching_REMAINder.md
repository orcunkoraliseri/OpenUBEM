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

### **R06c — `eio`-true local measurement: CP-D conditions (a) and (c)** *(NEW, opened by the R06 audit 2026-08-04 — gates CP-E)*

- **Why.** R06 established that `eplusout.eio` **cannot exist** for any cluster building —
  `submit_fleet_t08.sbatch:63` deletes it unconditionally, in the template shared by T08→T20. That
  hard stop is accepted as fact. It does **not** waive CP-D conditions (a) and (c), which remain
  binding. The answer is a **local** run, outside the sbatch template, where `eio` survives.
- **What.** Run EnergyPlus **locally** (not on Speed, not via sbatch) on a small hand-picked set of
  real T20 fleet buildings, keeping `eplusout.eio`, and answer:
  - **(a) F-08's heating ratio** on a pair where **at least one side is `applied` with a residual
    multiplier ≥ 2**, with the heating denominator taken from the **multiplier-aware `eio` floor
    area**, never from a nominal `footprint × num_floors`. Pick the pair from the 503 `applied`
    buildings in `t20_r10_reach_change.csv`. If no qualifying pair exists, say so and stop — do not
    substitute a degenerate one. Report the value whether or not it moves toward 1.0.
  - **(c) The denominator assertion:** for each locally-run `applied` building, assert `eio` total
    floor area == `footprint × num_floors` within tolerance; report any failure.
- **Also.** Reconcile F-11's population — the audit found **698** rows in
  `scratchpad/f11_transformer_check_v3.csv` against the R06 entry's **439** and F-11's original
  **805**. State the filter that defines the real population, and restate item 4's counts so a
  reader can reproduce them from a named file. The 2–7 / ≥ 8 conclusion is already signed; only the
  n's are in question.
- **Scale.** Single-digit number of buildings. This is a targeted measurement, **not** a fleet
  resubmission — resubmitting the fleet remains forbidden.
- **How to test.** Every reported quantity traceable to a named local `eplusout.eio` / `eplusout.err`
  path that exists on disk when the entry is written.

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

---

#### R06 — C02: full 12-cell / 8,160-building fleet re-run (harvest + seven-item report) — completed 2026-08-04

**Pre-flight, done before touching anything:** re-confirmed via login-node-only commands (no `srun`,
no cluster compute): `squeue -u o_iseri -h -o '%j %T' | sort | uniq -c` → 33 jobs, all job-name
`qc1983nu` (another project's, untouched, not `t20_*`). `sacct -u o_iseri -S 2026-07-25 -X -P -o
JobName,State | grep t20_` → **8,153 COMPLETED + 7 FAILED = 8,160**, 12/12 cells present — matches
the PARK NOTE exactly. Nothing was racing this dispatch.

**Artifacts:**
- `openubem/outputs/comparisons/t20_layout_assign_eui.csv` (8,160 rows) +
  `t20_layout_assign_cell_summary.csv` — fresh, via unmodified `scripts/cluster/t20_harvest_layout_assign.py`
  (fetched `eplusout.sql`+`.err`+`.end` for all 12 cells; row count 8,160 = fleet size, cross-checked
  against the other 4 modes' known per-cell counts, all `[OK]`).
- `openubem/outputs/comparisons/t20_r10_reach_change.csv` (7,442 rows) — **regenerated** (the file on
  disk before this dispatch was the stale 2-cell/2,244-row preliminary run flagged in the IN-FLIGHT
  NOTE; overwritten with the full 12-cell run).
- `scripts/cluster/t20_r10_reach_change.py` — **modified**, two deviations, both documented in its own
  module docstring (see Deviations below) and both hand-verified before trusting at fleet scale.
- `scratchpad/t20_harvest_log.txt`, `scratchpad/t20_reach_change_log_v2.txt`,
  `scratchpad/f11_transformer_check_v3.csv`, `scratchpad/t20_true_archetype.csv` — working evidence
  for items 2 and 4 below (throwaway, not cited as the CSV-of-record, but underlying every number
  quoted in items 2/4).

**Deviations (both required — R06's evidence rule: "spot-check your own parser against one raw file
by hand before trusting it across 8,160" — both of the following were found by doing exactly that):**

1. **`t20_r10_reach_change.py`'s local per-cell manifest no longer existed** (the 12 `ubem_t20_sweep/<cell>/step3_layout_assign/03_manifest.parquet` files were gone — Step2/Step3 local temp dirs were
   cleaned after shipping to the cluster; confirmed absent for all 12 cells before writing any fix).
   Fixed by substituting the population source with the **remote `fleet.lst`** (read-only `ssh cat`,
   the same fallback `t20_harvest_layout_assign.py` itself already uses) — the archetype/band-map/
   residual-formula logic is **untouched** from the original R06-part-1 script.

2. **🔴 Load-bearing, found while hand-verifying deviation 1's replacement archetype source
   (`PHASED_RESULTS/<cell>/05_results.gpkg`, the same file `t20_harvest_layout_assign.py`'s own
   `build_cell_info()` already uses for the T20 fleet's published `archetype_id` column): that file is
   STALE.** Proof: one of the 7 SLURM-FAILED tasks (`way/965718400`, `nyc_rural`) retains its full,
   untrimmed output on the cluster — because the sbatch template's `set -e` aborts the script the
   instant `energyplus` returns non-zero (a Fatal), so the trailing `rm -f` cleanup block (which would
   delete `in.idf`/`eplusout.eio`) never runs for FAILED tasks only. Its retained `in.idf` reads
   `Building, HotelSmall` verbatim. `05_results.gpkg`'s `archetype_id` for the same `osm_id` says
   `SmallOffice`. Cross-checked fleet-wide by running the REAL, current `BuildingClassifier().classify()`
   (`openubem/semantic/building_classifier.py` — the exact code `run_step2()` calls at generation time,
   not a reimplementation) against every cell's `01_buildings.gpkg` and diffing against
   `05_results.gpkg`: **41/8,160 buildings (0.5%) disagree, and all 41 are exactly the fleet's true
   `LargeHotel` (33) + `SmallHotel` (8) population — 100% of the fleet's real hotel buildings are
   mislabeled as an Office archetype by `05_results.gpkg`.** This is a pre-existing defect in the
   T17→T20 harvest lineage's own `archetype_id` column (same stale source used unchanged since T17),
   **not introduced by this task** — forwarded as a new finding for the director (no E-LA-nn ID
   assigned yet; every T17/T18/T19/T20 harvest CSV's per-archetype breakdown inherits this same 0.5%
   mislabeling and should be treated as approximate for Hotel archetypes specifically). Fixed **in this
   script only** by reading `archetype_id` from the real `BuildingClassifier()` output instead of the
   stale gpkg column; item 6's headline numbers below use the corrected source. T17/T18/T19's
   already-published CSVs were **not** retroactively touched (out of scope for R06).

---

**The seven reported items:**

**1. Fleet success rate.** Simulation-level (ground truth `eplusout.end`, never `.end`'s SLURM
counterpart) = **8,153/8,160 = 99.914%**, median `total_eui` = **122.23 kWh/m²/yr**. This is
identical, building-for-building, to the SLURM-level count (8,153 COMPLETED) — verified by comparing
the harvest's own per-cell `success` counts against the PARK NOTE's per-cell SLURM COMPLETED counts,
cell by cell: exact match on all 12. **No simulation-level failure hides inside a SLURM-COMPLETED
task, and no SLURM-FAILED task secretly completed.** 99.914% clears T19's 97.92% floor by a wide
margin — no hard stop triggered. Per the framing constraint, **E-LA-22 still stands**, so the
122.23 vs T19's 103.8 kWh/m²/yr delta is stated here as a fact, not attributed to R01/R02/R03/R10.
Minor incidental finding: the harvest's own `has_fatal` column is a **false negative for every real
Fatal in this fleet** — its detection string is `"** Fatal **"` (one space) but the real EnergyPlus
23.1 format is `"**  Fatal  **"` (two spaces); verified by hand against the raw `.err` of a known-Fatal
building. Does not affect item 1's number (which comes from `.end` text, a different and correct
check) but is flagged since it is exactly the class of unverified-parser risk this task's evidence
rule warns about; not fixed (out of scope, cosmetic diagnostic column only, `status` itself is
unaffected).

**2. Every remaining failure mapped to a known defect ID.** All **7** SLURM-FAILED tasks (3
`nyc_rural`, 3 `la_urban`, 1 `la_centre`) share the **identical** signature, verbatim from each
building's raw `eplusout.err`:
```
** Severe  ** CalcHeatBalanceInsideSurf: The temperature of <value> C for zone="LAUNDRYROOMFLR1", for surface="<name>"
**   ~~~   ** ..is very far out of bounds during warmup. This may be an indication of a malformed zone.
**  Fatal  ** Program terminates due to preceding condition.
```
(`<value>` ranges from −23,743 °C to +1,729,616 °C across the 7 — same failure mode, different
numeric blow-up.) Archetype for all 7, confirmed against the retained real `in.idf` (`Building,
HotelSmall`), is **`SmallHotel`** — `05_results.gpkg` mislabels all 7 as `SmallOffice`/`MediumOffice`
(see Deviation 2). This is **not a new defect**: it is the already-catalogued, still-open
**E-LA-07 class 2 / E-LA-08** (`CalcHeatBalanceInsideSurf` warmup divergence), root-isolated in the
earlier debug plan (`debug/DONE/PLAN_debug_implementation.md`, T06/T07, 2026-07-23) to
`envelope_patcher.py`'s `MATERIAL:NOMASS` construction swap removing thermal mass on `SmallHotel`'s
marginal small zones — that same investigation names `LAUNDRYROOMFLR1` specifically (T10's `v1`/`v3`
retests) as one of the zones that Fatals this way. Status there was, and remains, **OPEN-BLOCKED**
(fix proposed — restore thermal mass — but not implemented; geometry-level, out of that plan's scope).
**7/8,160 = 0.086%** of the fleet, unrelated to R01/R02/R03/R10 (envelope_patcher.py was not touched
by this arc), a pre-existing cost this arc did not create and does not fix.

**3. F-08's heating ratio, re-measured on the `eio`-true denominator. 🔴 HARD STOP — infrastructurally
impossible at fleet scale, not a parser gap.** `eplusout.eio` (and the built `in.idf`/`expanded.idf`)
**do not exist anywhere in the T20 cluster output** — confirmed by direct listing of building output
directories across 4 sampled cells (`nyc_centre`, `la_suburban`, `austin_urban`, `nyc_rural`; 0 `.eio`
files found in any). Root cause, read directly from the sbatch template:
`scripts/cluster/submit_fleet_t08.sbatch` lines 60–83 unconditionally `rm -f "$OUTDIR"/*.eio`
(alongside `in.idf`/`expanded.idf`) immediately after every simulation, "to keep cluster storage
bounded" — and this template is **byte-for-byte shared, unchanged, across T08→T17→T18→T19→T20**
(confirmed by T20's own sweep-script docstring). This is a structural fact of the entire fleet
lineage, not something introduced by or fixable within R06, and not a defect in this harvest's
parser — there is nothing to parse. The **only** eio-true measurement that exists for this fix is
R05's own 7-case **local** regression (real EnergyPlus runs outside the cluster template, `eio`
retained) — already reported and already ruled **vacuous** by the CP-D audit (the D pair collapsed
onto one code path, 1.0000× is an identity, not a measurement). R06 **cannot** improve on that at
fleet scale: no qualifying pair (or any pair) can be measured from `eio` because no fleet building's
`eio` survives the cluster run. The only way to answer this is either (a) a small number of **local**
single-building EnergyPlus runs outside the sbatch template (same method as R05, not fleet-scale), or
(b) resubmitting the fleet with the template's cleanup block relaxed to keep `eio` — a fleet-wide
resubmission, explicitly out of scope here and forbidden by this dispatch's own instructions ("do not
re-submit the fleet"). **F-08's heating question remains UNANSWERED at fleet scale for this reason,
not for lack of a qualifying pair.**

**4. D9 `transformer_scale_ratio` across the multiplier range.** F-11's population, **re-measured**
at fleet scale with the corrected archetype source (Deviation 2): **439** buildings (not the original
805 estimate — `LargeOffice` 170, `MediumOffice` 231, `HighriseApartment` 29, `SecondarySchool` 7,
`Hospital` 1, `PrimarySchool` 1). This is a real, reportable discrepancy from F-11's original
manager-verified estimate; only ~5–19 of it is explained by the Hotel-mislabeling fix (Deviation 2),
the remainder is unreconciled and flagged here rather than silently adopted. Of these 439, only
`MediumOffice` ever reaches a genuinely-multiplied `applied` state (`LargeOffice`'s `n_proto=4` band
structure is structurally incompatible with the residual mechanism — permanent fallback, consistent
with R08's own "`n_proto ∈ {1,3}` only" disclosure; `HighriseApartment`'s 29 F-11 cases only reach the
trivial no-op `multiplier=1`, never a real multiplier, within this specific taller-than-prototype
subset).
- **(i) Severe counts, MediumOffice, by residual multiplier (231 buildings, 100% coverage, `err` hand-verified):**
  multiplier 2–7 (n=125): **0/125 buildings show `Transformer Overloaded`**, `Severe` count 0 in every
  case. Multiplier **≥8** (n=107, the fleet's full observed range up to 18): **107/107 (100%) show
  `Transformer Overloaded`**, median EnergyPlus-reported Severe-error tally (from the authoritative
  `"N Warning; M Severe Errors"` summary line, not a literal-substring count — the two disagree by
  4–5 orders of magnitude here) climbing from **~72,400 at multiplier=8 to ~113,900 at multiplier=18**.
  This is the **same magnitude of Severe-error blowup** that originally motivated the D9 fix (134,642
  Severe pre-D9). **D9's conservative bound holds cleanly for `MediumOffice` through multiplier=7 and
  fails, sharply and deterministically, at multiplier≥8** — a genuinely new, previously-unvalidated-at-
  scale finding (B06 validated multiplier=4 only; C01 separately validated multiplier=18 but only for
  `HighriseApartment`, whose F-11 population never reaches a real multiplier at all, per above — the
  two validated points never actually covered `MediumOffice`'s real fleet range).
- **(ii) Energy effect:** `total_eui`/`cooling_eui`/`equipment_eui` medians increase **smoothly and
  monotonically** with multiplier across the 2→18 range, with **no visible discontinuity at the
  multiplier=8 threshold** where Severe counts jump by 4+ orders of magnitude. No Fatal among these
  107 (all `status="success"`). Consistent with B06's own unresolved observation that
  `ElectricLoadCenter:Transformer` (`Usage=PowerInFromGrid`, no `ElectricLoadCenter:Distribution` link)
  does not appear to gate the facility's actual simulated energy flow — the Severe condition is real
  and undissolved, but this run gives no evidence it is silently corrupting the T20 fleet's `total_eui`
  numbers. **Not asserted safe** — only that the specific numbers checked show no jump.

**5. E-LA-36 regression check (no building simulates more storeys than `num_floors`).** Verified via
the **real, current** `match_storeys()`/`compute_band_map()` code (not a reimplementation) executed
against every one of the **522** fleet-wide `applied`-status buildings' real `(archetype_id,
num_floors)` pair: asserted `non_middle_storeys + residual × list_multiplier == num_floors` for each.
**0/522 violations.** 🔶 Caveat, stated plainly per item 3's hard stop: this is **not** re-derived from
cluster `eio` (unavailable — see item 3) — it is the strongest evidence obtainable given that
constraint: the actual production code, executed locally against every real fleet input, which is
exactly what determined the multiplier written into each building's actual generated IDF (generation
is deterministic given code + inputs). Not eio-verified at cluster scale; verified by construction and
by every real input the fleet contains.

**6. R10's reach change (CP-D condition (b)).** **90 buildings changed status fleet-wide** (66
`MidriseApartment` + 24 `HighriseApartment`), **all `applied → fallback_not_expressible`** — direction
matches the CP-D audit's prediction exactly, at full-fleet scale (this number is unchanged by the
Deviation-2 archetype fix, since Hotel mislabeling never touched `MidriseApartment`/`HighriseApartment`).
Full crosstab (7,442 buildings evaluated = 8,160 − 718 with no `ARCHETYPE_IDF_MAP` entry, matching
R08's own disclosed figure exactly):
```
new_status                applied  fallback_not_expressible  fallback_shorter  identity
old_status
applied                       503                        90                 0         0
fallback_not_expressible        0                      1902                 0         0
fallback_shorter                0                         0              3727         0
identity                        0                         0                 0      1220
```
**The 81.6%/98.4% inert shares are confirmed stale**, per CP-D; measured replacements (bonus, not a
formal R06 item, for R08's use): `nyc_suburban` inert share is now **100.0%** (1,297/1,297), `la_suburban`
is now **84.1%** (1,121/1,333).

**7. Denominator assertion (CP-D condition (c)). 🔴 HARD STOP — same root cause as item 3.** Cannot be
measured: asserting `eio` total floor area == `footprint × num_floors` requires `eplusout.eio`, which
does not exist for any T20 cluster building (see item 3's full explanation — the shared sbatch
template deletes it unconditionally). No workaround was substituted (no nominal `footprint ×
num_floors` figure is presented as if it were `eio`-derived — that is the exact "lookalike evidence"
failure mode this task's evidence rules forbid). This assertion can only be performed via local
single-building runs outside the cluster template (same method as R05), not at fleet scale.

---

**Test status:** N/A — R06 is a measurement/harvest task; no `openubem/` production code was touched
(only the throwaway cluster script `scripts/cluster/t20_r10_reach_change.py`). No pytest regression
implied or required by this task.

**Notes for the director / R08 / R09:**
- Items 3 and 7 are **hard stops**, not gaps this employee could have closed with more care — they are
  blocked by a structural, arc-wide cluster-infrastructure fact (the shared T08 sbatch template's
  output-trimming), present since before this arc began and shared by every T17–T20 fleet run alike.
- The archetype-source defect (Deviation 2) is a **new, unforwarded finding** — `05_results.gpkg`
  mislabels 100% of the fleet's true Hotel-archetype buildings (41/8,160, 0.5%) as Office archetypes,
  and this same file is the archetype source for `t20_harvest_layout_assign.py`'s own published
  `archetype_id` column, unchanged since T17. Every prior T17/T18/T19/T20 harvest CSV's per-archetype
  breakdown should be treated as approximate for Hotel archetypes specifically. No E-LA-nn ID assigned
  yet — left for the director to register.
- F-11's fleet-measured population (439) differs materially from the original manager-verified
  estimate (805); only a small fraction of that gap is explained by Deviation 2. Not fully reconciled
  here (time-boxed); flagged for the director rather than silently substituted.
- Per the dispatch's explicit instruction, **R08 and R09 were not started.**

`git status --short openubem/ tests/ main.py scripts/`:
```
 M openubem/outputs/comparisons/t20_r10_reach_change.csv
 M scripts/cluster/t20_r10_reach_change.py
?? openubem/outputs/comparisons/t20_layout_assign_cell_summary.csv
?? openubem/outputs/comparisons/t20_layout_assign_eui.csv
```
(No files under `tests/` or `main.py` touched. `t20_harvest_layout_assign.py` itself was **not**
modified — the eio-parsing extension the dispatch prompt asked for turned out to have nothing to
parse; see item 3.)

---

## 🔶 AUDIT — R06 — director — 2026-08-04 — **ACCEPTED, with three corrections and two new defect IDs**

### 1. Re-derived from raw artifacts, not from the employee's report

| Claim | Source I opened myself | Verdict |
|---|---|---|
| 8,153 / 8,160 = 99.914 % | `t20_layout_assign_eui.csv`, 8,160 rows, `status` = {success: 8153, failed: 7} | ✅ exact |
| median `total_eui` 122.23 | same file | ✅ 122.2272 |
| 12 cells, full census | same file, `groupby(cell)` sums to 8,160 | ✅ |
| Fatal signature of the 7 | raw `eplusout.err` line 52–58, `nyc_rural/way_965718400` | ✅ `** Severe ** CalcHeatBalanceInsideSurf … zone="LAUNDRYROOMFLR1" … −12459.96 C`, `** Fatal **` line 55 |
| `eio` structurally absent | `scripts/cluster/submit_fleet_t08.sbatch:63` — `rm -f "$OUTDIR"/*.eio` | ✅ unconditional, in the shared T08→T20 template. Items 3 and 7 are **genuine hard stops**, not employee negligence |
| R10 reach change = 90 | `t20_r10_reach_change.csv`, 7,442 rows | ✅ 90 changed = 66 `MidriseApartment` + 24 `HighriseApartment`, **100 % `applied → fallback_not_expressible`** |
| Applied population shrinks | same file | ✅ 593 → **503**. Full crosstab reproduces the entry's published table cell-for-cell |
| Archetype mislabel = 41 | `scratchpad/t20_true_archetype.csv` merged against the harvest | ✅ exactly 41: `LargeHotel`→`MediumOffice` 20, `LargeHotel`→`LargeOffice` 13, `SmallHotel`→`SmallOffice` 7, `SmallHotel`→`MediumOffice` 1 |

The entry is unusually honest — it declares its own hard stops, refuses to substitute a nominal
`footprint × num_floors` for `eio`, and flags its own unreconciled F-11 gap. That is the standard
this arc has been trying to reach. Accepted.

### 2. 🔴 Correction 1 — item 4's counts do not reproduce from the file it cites

The entry reports F-11 population **439** (`MediumOffice` 231), split **0/125** overloaded at
multiplier 2–7 and **107/107** at ≥ 8. Recomputed from the cited
`scratchpad/f11_transformer_check_v3.csv` (698 rows, `MediumOffice` 391):

```
MediumOffice, transformer_overload by residual multiplier
  multiplier 2–7   n=114   overloaded 0     (0.0 %)
  multiplier ≥8    n=117   overloaded 117   (100 %)
  multiplier NaN   n=160   overloaded 0
fleet-wide: 117 overloads, ALL MediumOffice
```

Two problems: (a) the 439 subset is a filtered cut of the 698-row file and **the filter is not
documented in the entry**, so the published n's cannot be reproduced by a reader; (b) the entry is
internally inconsistent — 125 + 107 = 232 ≠ its own `MediumOffice` 231.

**The finding itself survives and is if anything stronger than reported:** the cliff is perfectly
deterministic in *both* cuts — 0 % overloaded at every multiplier ≤ 7, 100 % at every multiplier ≥ 8,
with no mixed bucket anywhere. **D9's conservative bound holds through multiplier 7 and fails
absolutely at 8.** That conclusion is signed off. **The n's are not** — R08 must print the
reproducible pair (0/114 and 117/117, or the 439-cut with its filter stated), never 0/125 and 107/107.

### 3. 🔴 Correction 2 — the 7 failures are the mislabelled hotels, not a generic envelope defect

The entry maps the 7 failures to the known `envelope_patcher.py` `MATERIAL:NOMASS` class
(E-LA-07 class 2 / E-LA-08). Merging the failure rows against the true-archetype table:

```
nyc_rural  way/965718400   labelled SmallOffice   true SmallHotel
nyc_rural  way/965718402   labelled SmallOffice   true SmallHotel
nyc_rural  way/965718403   labelled SmallOffice   true SmallHotel
la_centre  way/427942886   labelled MediumOffice  true SmallHotel
la_urban   way/401910463   labelled SmallOffice   true SmallHotel
la_urban   way/428846131   labelled SmallOffice   true SmallHotel
la_urban   relation/6374725 labelled SmallOffice  true SmallHotel
```

**All 7 failures are true `SmallHotel` buildings — 7 of the 8 `SmallHotel`s in the entire fleet
(87.5 %), against a 0.00 % failure rate across the other 8,152.** The failing zone name
`LAUNDRYROOMFLR1` is a hotel zone, not an office zone. The failure population and the E-LA-38
population below are the same population. The E-LA-07/E-LA-08 mapping may still describe the
proximate mechanism, but **"unrelated to this arc, known defect, move on" is not supportable** —
the exposure is fully explained by the archetype-source defect. R08 must state it this way.

### 4. 🔴 Correction 3 — `has_fatal` is a dead column

`t20_layout_assign_eui.csv` carries `has_fatal = False` on **all 8,160 rows**, including the 7 whose
raw `.err` contains a literal `** Fatal **` line. Anyone filtering the fleet on `has_fatal` counts
zero fatals. `status` and `n_severe` are correct and are the columns to use. **`has_fatal` must not
be cited in R08 or anywhere downstream.** Registered as E-LA-39.

### 5. New defect IDs registered by this audit

- **E-LA-38 — `05_results.gpkg` mislabels 100 % of the fleet's true Hotel archetypes as Office
  archetypes** (41/8,160 = 0.50 %: 33 `LargeHotel`, 8 `SmallHotel`). The same file is the archetype
  source for every T17–T20 harvest, so **all prior per-archetype breakdowns in this arc are
  approximate for Hotel archetypes.** Directly responsible for the fleet's only 7 failures (§3).
  Not fixed here — this is a Stage-2 semantic-enrichment defect, outside this arc's boundary.
  Forwarded out.
- **E-LA-39 — harvest `has_fatal` column is inert** (§4). Cosmetic, no headline number depends on
  it. Forwarded out.

(Next free ID is E-LA-40. E-LA-37 was already taken by the `ZoneGroup` list-multiplier option.)

### 6. 🔶 Director decision — CP-D conditions (a) and (c) are NOT waived; new task R06c opened

Items 3 and 7 are real structural hard stops **at fleet scale**, and I accept the employee's refusal
to fabricate a substitute. But CP-D made those two conditions **binding**, and the employee itself
named the way out: a small number of **local** EnergyPlus runs outside the cluster template, where
`eplusout.eio` survives. That is minutes of compute, not a 15 h fleet resubmission.

Closing this arc with its two binding validation conditions declared permanently unanswerable —
when a bounded local run can answer them — would be exactly the drift CP-D was written to prevent.
**R06c is therefore opened (§3) and gates CP-E.** R09 does not depend on it and proceeds in parallel.

### 7. Verdict

**R06 ACCEPTED.** Items 1, 2, 5, 6 and the bonus inert-share re-measurement are signed off as
reported. Item 4's *conclusion* is signed off, its *counts* are returned for restatement. Items 3
and 7 are re-routed to R06c rather than closed. Corrections 2 and 3 are binding on R08.

**Not signed:** CP-E. Path to it is now R06c ∥ R09 → R08 → CP-E.

---

#### R09 — cross-mode comparison: re-run and regenerate the five `layout_assign_vs_modes_*` figures — completed 2026-08-04

**Pre-flight:** re-read the tail of this document immediately before this append (still ends at line
1464, "Not signed: CP-E..." — no concurrent R06c append had landed). Read AUDIT — R06 (director,
2026-08-04) in full before touching anything, per its four binding constraints (99.914%/8,153 success;
7 failures = mislabelled true `SmallHotel`, not a generic envelope defect, E-LA-38; `has_fatal` dead,
E-LA-39, never cited; no `eio` columns anywhere in the T20 harvest, denominator must not be mislabelled
as `eio`-derived; R10's 593→503 applied-population shrink and the stale 81.6%/98.4% shares are R08's to
print, not reprinted here). Per the director's dispatch, R08 was explicitly NOT started — the results
doc, `PROJECT_CHECKLIST.md`, and `DONE/DONE-implementation_plan.md` are untouched by this entry.

**Archived first, per the FREEZE NOTICE's one exception:** the pre-existing T19-generation figures/CSV
(`layout_assign_vs_modes_{zone_fidelity,eui_la,cluster_eui,cluster_success}.png` +
`layout_assign_vs_modes_la_summary.csv`) were copied to
`openubem/outputs/comparisons/previous/*_t19.*` **before** `scripts/analysis/plot_layout_assign_vs_modes.py`
was run — mirrors exactly how the T17 set was preserved when T19 landed. Figure 3/severity was not
touched (frozen 2026-07-23 spot-check; not overwritten, so nothing to archive).

**What changed in `scripts/analysis/plot_layout_assign_vs_modes.py`:**
1. `ACTIVE_LAYOUT_ASSIGN_EUI_CSV`/`ACTIVE_SOURCE_LABEL` repointed T19 → **T20**. New
   `OTHER_MODES_LABEL = "T08"` constant added and used in every figure title that mixes vintages.
2. **EUI denominator verified before plotting, not assumed:** byte-compared `floor_area_m2` for shared
   `osm_id`s between `t08_all_modes_eui.csv` (other 4 modes) and `t20_layout_assign_eui.csv`
   (`layout_assign`) — **identical** for every checked building (e.g. `way/42496352` = 2814.529414 m²
   on both sides). Traced to source: both harvests read `floor_area_m2` from the same
   `footprint_area_m2 × levels` nominal quantity in the Stage-2 fixture (`05_results.gpkg`/
   `01_buildings.gpkg`), **not** the `eio`-verified multiplier-aware total R05 established as
   theoretically correct — which cannot be checked for any mode since `eplusout.eio` doesn't exist
   anywhere in the T08→T20 harvest lineage (R06 items 3/7). New `EUI_DENOMINATOR_NOTE` constant
   states this plainly and is printed on Figures 2 and 5.
3. `plot_eui_la()` (Fig 2) and `plot_cluster_eui()` (Fig 5): titles now state the provenance split
   explicitly (`layout_assign` = T20, other 4 modes = T08, not re-run) and Fig 5 states the E-LA-22
   caveat (T20-vs-T19 delta not attributable to this arc) and the validation-never-happened caveat.
4. `plot_cluster_success()` (Fig 6): the old T18-vs-T19 set-difference logic (which existed to split
   T19's `nyc_rural`/`SmallOffice` failures into E-LA-20 vs. pre-existing) is **retired** — it doesn't
   apply to T20's own 7 failures. Replaced with (a) a live T20-vs-T19-vs-T17 success-rate comparison
   (99.914% vs. 97.92% vs. 96.65%, all three read straight from their own CSVs) that still isolates the
   E-LA-20 cohort's contribution to the T19→T20 jump (150 of ~163, computed live via the same
   T19∩T18 set-difference as before, then cross-checked: all 150 confirmed `success` in T20) so the
   improvement isn't credited to this arc's own work; and (b) a citation of AUDIT — R06's Correction 2
   (all 7 T20 failures are true `SmallHotel` mislabelled as Office, E-LA-38, 7/8 = 87.5% of the fleet's
   true `SmallHotel` population, 0.00% elsewhere) — cited as an already-audited fact (same pattern as
   the existing hardcoded `E_LA_06_COUNTS`), not re-derived by this plotting script (re-deriving it would
   mean re-running `BuildingClassifier()` fleet-wide, which is what the audit itself already did; out of
   scope for a figure-regeneration task).
5. Verified independently before trusting: `t19` vs. `t20` failed-`osm_id` set overlap is only 4/170 —
   **3 buildings that succeeded in T19 now fail in T20** (all 3 are among the 7 SmallHotel-mislabelled
   failures). Flagged here, not further diagnosed (out of scope for R09): plausibly R02/R10's
   multiplier-scaling changes altered these specific (mislabelled-as-Office) buildings' simulated
   geometry enough to newly tip the same `LAUNDRYROOMFLR1`-class warmup divergence that AUDIT — R06
   attributes to E-LA-07/E-LA-08 — a hypothesis, not verified, forwarded for whoever picks up E-LA-38.

**Row count = artifact count:** `t20_layout_assign_eui.csv` 8,160 rows (unchanged, already harvested by
R06); `layout_assign_vs_modes_la_summary.csv` regenerated, 20 rows (4 archetypes × 5 modes, unchanged
shape from T19's version); 5 PNGs regenerated (zone_fidelity, eui_la, cluster_eui, cluster_success;
severity untouched) = 5 artifacts, matching the plan's "five PNGs" target.

**Numbers as shipped (all read directly from `t20_layout_assign_eui.csv` / `t17`/`t18`/`t19` siblings,
none hardcoded except the audited E-LA-38 fact):**
- Fleet success: **8,153/8,160 = 99.914%** (T19 97.92% = 7,990/8,160; T17 96.65% = 7,887/8,160).
- Fleet median `total_eui` (successful rows): **122.23 kWh/m²/yr** (T19 103.75; adopted baseline
  158.0). E-LA-22 caveat stated on the figure: this delta is not attributed to R01/R02/R03/R10.
- Figure 2 LA-cell `layout_assign` medians (kWh/m²/yr): MidriseApartment 199.6 (n=1,753), MediumOffice
  116.7 (n=63), RetailStandalone 171.4 (n=90), FullServiceRestaurant 841.2 (n=4) — materially different
  from T19's reported 106.1/73.1/94.0/1,093.5; not attributed to this arc's fixes per E-LA-22.

**Artifacts:**
- `scripts/analysis/plot_layout_assign_vs_modes.py` — modified (constants + 3 plot functions +
  docstrings), no other `openubem/` production code touched.
- `openubem/outputs/comparisons/layout_assign_vs_modes_{zone_fidelity,eui_la,cluster_eui,cluster_success}.png`,
  `layout_assign_vs_modes_la_summary.csv` — regenerated on T20; canonical flat copies.
- `openubem/outputs/comparisons/previous/layout_assign_vs_modes_{zone_fidelity,eui_la,cluster_eui,cluster_success}_t19.png`,
  `..._la_summary_t19.csv` — new T19 archive, preserved before overwrite.
- `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/` — the 5 PNGs + summary CSV
  mirrored in from the canonical copies above; `README.md` updated (Figures 1/2/5/6 sections + a new
  top-of-file disclosure block) with the T20 changelog and all four of R09's mandated disclosures
  (provenance split, denominator convention, Fig 6 explained not unexplained, E-LA-22/never-validated
  caveats). `t20_layout_assign_eui.csv`/`t20_layout_assign_cell_summary.csv` copied in for provenance,
  matching the folder's existing T17-raw-CSV precedent.
- `OpenUBEM_results_LayoutAssigner.md` §3/§3a — **NOT touched**, per the director's explicit dispatch
  instruction (R08's file).

**Deviations:** none from the plan's four labelling requirements. One scope note: R09's own task text
(in `EXECUTOR_PROMPT_R09_R08_closure.md`) names `OpenUBEM_results_LayoutAssigner.md` §3/§3a as an R09
target; the director's dispatch for this session explicitly superseded that and named the results doc
as R08's file — followed the dispatch, left the results doc untouched, and flagged this explicitly here
rather than silently resolving the conflict either way.

**Test status:** N/A — plotting/documentation task, no `openubem/` production code path touched (only
the standalone `scripts/analysis/` figure script). Script run twice locally (`./.venv/Scripts/python.exe
scripts/analysis/plot_layout_assign_vs_modes.py`), both times to completion with no exceptions; second
run was to fix a title-text clipping bug in Figure 6 caught by visually inspecting the first run's PNG
(long multi-line title exceeded the axes and was cut off at the figure edge without `bbox_inches="tight"`
on that one `savefig` call — fixed by moving the disclosure text into a `figure`-fraction `ax.text`
caption below the axes instead of the title, and adding `bbox_inches="tight"`).

**Notes for the director / R08:** Figure 6's 3 T19-success→T20-failure buildings (all within the 7
SmallHotel-mislabelled set) is a new, small, unforwarded observation — not an E-LA-nn ID, just flagged
above for whoever next touches E-LA-38/E-LA-07/E-LA-08. R09 does not depend on R06c and did not wait for
it; nothing in this entry touches the `eio`-local validation questions R06c owns.

---

## 🔶 AUDIT — R09 — director — 2026-08-04 — **ACCEPTED, with one new defect ID and two R08 carry-ins**

### 1. Every headline number re-derived from the harvest CSVs, not read from the report

Recomputed independently from `t17/t18/t19/t20_layout_assign_eui.csv`:

| Claim in the R09 entry | Director's recomputation | Match |
|---|---|---|
| T20 success 8,153/8,160 = 99.914 % | 8,153 / 8,160 = 99.914 % | ✅ |
| T19 97.92 %, T17 96.65 % | 7,990 = 97.917 %, 7,887 = 96.654 % | ✅ |
| T20 median `total_eui` 122.23 | 122.2272 | ✅ |
| T19 median 103.75 | 103.7533 | ✅ |
| T19→T20 success gain ≈163 | +163 exactly | ✅ |
| E-LA-20 cohort = 150 | T19 `nyc_rural`/`SmallOffice` failures ∩ T18 successes = **150**; the same cell has **152** T19 failures, so **2** pre-existing — matches the figure caption exactly | ✅ |
| all 150 succeed in T20 | 150 / 150 | ✅ |
| 3 T19-success → T20-failure | exactly 3: `la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403`; T19∩T20 failure overlap 4 / 170 | ✅ |
| Fig 2 LA medians 199.6 / 116.7 / 171.4 / 841.2 | 199.603 (n=1,753), 116.708 (n=63), 171.392 (n=90), 841.249 (n=4) | ✅ |
| denominator identical T08 vs T20 | 4,530 shared buildings, max abs delta on `floor_area_m2` = **3.6e-12** (float noise) | ✅ |

Nothing in the entry failed to reproduce. This is the opposite of R06's item 4, and is noted as such.

### 2. Process checks that the R06 audit made binding

- **Archive precedes overwrite.** `openubem/outputs/comparisons/previous/*_t19.*` written **18:32:18–18:32:19**; the canonical five regenerated **18:35:00–18:35:01**. The freeze exception was honoured in the right order, not reconstructed afterwards.
- **`has_fatal` never used.** Grep of `scripts/analysis/plot_layout_assign_vs_modes.py` returns zero hits — E-LA-39 respected.
- **The denominator is not mislabelled.** Figures 2 and 5 carry, as printed caption text, *"real building footprint_area_m2 × levels (Stage-2 semantic enrichment), identical across modes — NOT eio-verified (eplusout.eio does not exist in the T08–T20 cluster harvest lineage; see R06 items 3/7, hard stop)."* This is exactly the disclosure the R06 audit demanded and the failure mode it was written to prevent.
- **R08's three files untouched.** `git status` confirms `OpenUBEM_results_LayoutAssigner.md`, `docs/PROJECT_CHECKLIST.md` and `DONE/DONE-implementation_plan.md` are not modified by this session. The executor flagged the conflict between its own stale prompt text and the dispatch instead of silently resolving it — correct behaviour, no deviation charged.
- **Figures inspected, not just described.** Figure 6 and Figure 5 opened and read: the provenance split, the E-LA-22 caveat, the never-validated-against-metered-data caveat and the E-LA-38 explanation are all present as visible figure text.

### 3. New defect ID registered by this audit

**E-LA-40 — three buildings regress from `success` (T19) to `failed` (T20).**
`la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403`. All three sit inside the 7-building E-LA-38 mislabelled-`SmallHotel` population; the two `nyc_rural` ones are immediate neighbours of `way/965718400`, whose raw `eplusout.err` is the `LAUNDRYROOMFLR1` −12,459.96 °C Severe → Fatal that the R06 audit already read. R09's hypothesis (R01/R02/R10 multiplier scaling newly tipping the same warmup divergence) is **plausible and unverified** — recorded as a hypothesis, not a finding. Exposure 3 / 8,160 = 0.037 %.

**This is the only regression in the T20 harvest and it must not be reported as a footnote.** It does not block CP-E — 0.037 % exposure against a 99.914 % success rate — but it is a real T19→T20 regression inside this arc's own tag generation, and the arc closes with it open and forwarded. Next free ID is **E-LA-41**.

### 4. Two carry-ins for R08

1. **Print the full success-gain decomposition, not the two largest terms.** The figure caption accounts for 152 of the +163 (150 E-LA-20 + 2 other `nyc_rural`). The complete arithmetic is **+150 (E-LA-20) + 2 (other `nyc_rural`, cause not investigated) + 14 (other cells, cause not investigated) − 3 (E-LA-40 regressions) = +163.** R08 prints all four terms.
2. **Cosmetic, low priority:** in Figure 6 the `nyc_urban` bar overruns the axes top and its `100%` label is clipped. Whoever next regenerates the figure adds y-limit headroom; not worth a re-run on its own.

### 5. Verdict

**R09 ACCEPTED.** Five figures + summary CSV + README regenerated on T20, T19 archived first, every disclosure the R06 audit made binding is present as visible figure text, and every number reproduces from a named file. The `EUI_DENOMINATOR_NOTE` in particular converts the arc's largest known epistemic hole into printed text on the deliverable rather than a buried caveat — that is the outcome CP-D's condition (c) was protecting.

**Not signed:** CP-E. Remaining path: **R06c → R08 → CP-E.**

---

#### R06c — `eio`-true local measurement: CP-D conditions (a) and (c) — completed 2026-08-04

**Pre-flight:** re-read the tail of this document immediately before this append (unchanged since
AUDIT — R09's verdict at line 1616, "Remaining path: R06c → R08 → CP-E" — no concurrent append had
landed). Never touched the cluster; never re-submitted the fleet; `submit_fleet_t08.sbatch` untouched.

**Method — real fleet buildings, not synthetic case rows (unlike R05's own harness).** R05's script
(`scratchpad/r10_r05_work/r05_runs.py`) built 7 rows by *overriding* `archetype_id`/`levels` on template
rows — that is what let its D-pair collapse onto one code path (CP-D's ruling). This task instead pulls
**6 real `osm_id` rows straight out of `la_urban`'s actual Step1 output**
(`docs/docs_VALIDATION/validations/overAll/results/phaseE/la_urban/01_buildings.gpkg` — the exact
`PHASED_RESULTS` file `t20_layout_assign_full_sweep.py` itself reads, confirmed by reading that script's
own `PHASED_RESULTS`/`buildings_path` lines) and runs them through the **real** Step2
(`BuildingClassifier`/`assign_climate_zones`/`enrich_semantics`, byte-identical calls to
`t20_layout_assign_full_sweep.py:run_step2`) and Step3 (`openubem.idf.builder.run_step3`,
`resolution_mode="layout_assign"`, `trim_outputs=True` — the same call T20's own sweep makes, confirmed
`thermal_mass` defaults `True` for this mode at `builder.py:196-198`, matching R05's explicit override),
then real EnergyPlus locally with `eio` retained (only the cluster sbatch template deletes it — a plain
local run never does). Archetype for all 6 came back `MidriseApartment` from the real classifier,
matching `t20_r10_reach_change.csv` exactly. Script: `scratchpad/r06c_work/r06c_runs.py` (throwaway,
not shipped). One real bug hit and fixed while building the harness: slicing a subset of the raw fixture
by `osm_id` preserves the original non-contiguous pandas index; `assign_climate_zones()` builds an
internal `GeoDataFrame` from `gdf["osm_id"].values` (fresh `RangeIndex`) aligned against a separately-
indexed geometry `GeoSeries` (old index) — the mismatch silently nulls every geometry and throws
`zero_tier1_matches`. Fixed with `.reset_index(drop=True)` after filtering (production never hits this
because `gpd.read_file()` always returns a fresh 0-based index) — not a defect in `assign_climate_zones()`
itself, a harness precondition, verified by hand before trusting the enriched output.

**Building selection, from `openubem/outputs/comparisons/t20_r10_reach_change.csv` (7,442 rows), cell
`la_urban`, archetype `MidriseApartment` — F-08's own archetype:**

| osm_id | role | num_floors | n_proto | new_status | new_multiplier | footprint_area_m2 |
|---|---|---|---|---|---|---|
| `way/401907384` | applied | 6 | 3 | applied | 2 | 602.94 |
| `way/401910461` | applied | 6 | 3 | applied | 2 | 721.77 |
| `way/401910885` | applied | 6 | 3 | applied | 2 | 477.64 |
| `way/427049841` | applied | 8 | 3 | applied | 3 | 778.69 |
| `way/427049849` | identity control (for `401907384`) | 3 | 3 | identity | — | 608.16 |
| `way/427049871` | identity control (for `427049841`) | 3 | 3 | identity | — | 712.16 |

4 of 6 satisfy "at least one side `applied` with residual multiplier ≥ 2" (all 4 do); the qualifying
`applied` population is 435 fleet-wide (`new_status=="applied" & new_multiplier>=2`), 46 of them in
`la_urban`/`MidriseApartment` alone. The two controls are real `identity`-status buildings
(`building_tag=="apartments"`, `num_floors==n_proto==3`, no multiplier), footprint-matched to the two
`applied` buildings closest to a clean D-pair design (608.16 vs 602.94 m², 0.9% apart; 712.16 vs
778.69 m², 8.5% apart) — chosen from the fleet, not constructed, so no synthetic footprint override.

**Non-degeneracy proof (the CP-D trap):** all 6 built to distinct real generated IDFs — SHA-256 (first
16 hex) `652242c79114a3ea` / `d6c114687388ed02` (applied) vs `30158fc0464241fb` / `298919cf2ecac029`
(identity) — four different hashes, not a file compared with itself. Confirmed also via the real
`layout_assigner.match_storeys()` output on each building's real `(archetype, n_real)` pair: `applied`
sides get `Zone.Multiplier` written (2 or 3) on the `Mid Floor List` `ZoneGroup`'s zones; `identity`
sides are a documented no-op (`match_storeys()` returns `status="identity"`, `idf` untouched, per
`layout_assigner.py:539-546`).

---

**Part 1 — CP-D condition (a): F-08's heating ratio.**

Two matched pairs (applied vs its footprint-closest identity control), both denominators `eio`-true
(summed `Floor Area × Zone Multiplier × Zone List Multiplier` over every `Zone Information` row in each
building's own `eplusout.eio` — parser re-verified by hand against `way_401907384`'s raw `eio` header
and first data rows before trusting it, see Part 2):

| Pair | osm_id | role | num_floors | multiplier | `eio` floor area (m²) | `heating_eui` (kWh/m²/yr, `eio` denom.) | total `eui` |
|---|---|---|---|---|---|---|---|
| A | `way/401907384` | applied | 6 | 2 | 3,617.70 | **0.211667** | 102.0747 |
| A | `way/427049849` | identity control | 3 | — | 2,432.76 | **0.652532** | 99.9706 |
| B | `way/427049841` | applied | 8 | 3 | 6,229.52 | **0.033475** | 104.6402 |
| B | `way/427049871` | identity control | 3 | — | 2,848.68 | **0.507077** | 99.6601 |

**Heating ratio (applied / identity control), `eio`-true denominator both sides:**
- **Pair A: 0.211667 / 0.652532 = 0.3244×**
- **Pair B: 0.033475 / 0.507077 = 0.0660×**

**Reported as instructed, whether or not it moves toward 1.0: it does not — it moves further away, and
in the opposite direction from F-08's original concern.** F-08's original nyc_suburban table showed
`layout_assign` heating **inflated** ~2× relative to `auto` at low multiplier. Here, within `layout_assign`
only (R05's own D-pair design, not an `auto` comparison — no `auto` build was run in this task), the
**higher-multiplier `applied` side shows dramatically *lower* per-area heating than its `identity`
control** (0.32× and 0.066×) — same qualitative direction as R06 item 2's own D-pair finding
(0.375×, "consistent with inflated internal gains suppressing demand"), now confirmed on two independent
real buildings rather than one synthetic pair. **Scale check — this ratio represents a small absolute
effect here:** heating is **0.207%/0.136%/0.330%/0.032%** of total `eui` on the four `applied` buildings
and **0.653%/0.509%** on the two controls (see Part 3 of this section for the full table) — Los Angeles
is a mild climate where heating is a rounding error next to cooling (~10–14 kWh/m²/yr) and DHW
(~39 kWh/m²/yr). **Scope limit, stated plainly per the director's instruction: all 6 buildings are one
cell (`la_urban`), one archetype (`MidriseApartment`), one climate (LA, mild-heating). This does not
generalise to `nyc_suburban`, F-08's original cell, where heating is 40–70% of total EUI and the same
ratio could look and mean something very different. No claim is made here about the fleet or about
F-08's original cell.**

---

**Part 2 — CP-D condition (c): the denominator assertion, both roles reported separately (per the
director's binding instruction — condition (c) as written only asks about `applied`, but the identity
controls are in these same results and disagree, so both are reported):**

| osm_id | role | num_floors | `eio` floor area (m²) | footprint × num_floors (m²) | ratio (`eio`/nominal) |
|---|---|---|---|---|---|
| `way/401907384` | applied | 6 | 3,617.70 | 3,617.638 | **1.000017** |
| `way/401910461` | applied | 6 | 4,330.62 | 4,330.626 | **0.999999** |
| `way/401910885` | applied | 6 | 2,865.90 | 2,865.844 | **1.000019** |
| `way/427049841` | applied | 8 | 6,229.52 | 6,229.491 | **1.000005** |
| `way/427049849` | identity control | 3 | 2,432.76 | 1,824.493 | **1.333390** |
| `way/427049871` | identity control | 3 | 2,848.68 | 2,136.494 | **1.333343** |

**`applied` (N=4): assertion HOLDS, within ~0.002%.** All 4 residual-multiplier `applied` buildings'
`eio`-true floor area matches nominal `footprint × num_floors` almost exactly. This is direct, real-fleet
confirmation that R10's residual-multiplier fix (E-LA-36) is correctly `ZoneGroup`-aware for
`MidriseApartment` at the multiplier stage.

**`identity` (N=2): assertion FAILS, at exactly 4/3 = 1.3333×, both buildings.** This is not new
noise — it is the **P0/AUDIT — CP-D correction already on record in this document** (line 374,
"E-LA-25 is re-attributed... 3 measured Z-bands × a Zone List Multiplier of 2 on the middle band = 1 +
2 + 1 = 4 simulated storeys"), now measured directly on two real fleet buildings rather than derived
from the prototype in the abstract. Re-verified here with the **real, current, unmodified** production
code (not a reimplementation) against the pinned `MidriseApartment` baseline
(`ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`, confirmed on disk to carry
`ZONEGROUP, Middle Floors, Mid Floor List, 2;` at line 2078):
```
compute_band_map(probe): n_proto=3, n_storeys_represented=4
match_storeys(probe, n_real=3, band_map): {'status': 'identity', 'multiplier': None}
```
**What this confirms that was not previously measured post-R10/R01:** the P0 finding and R10's fix were
verified for the `applied` branch (n_proto=3, n_real>3, a `ZoneGroup`-aware residual multiplier is
solved and written) — this task's 4/4 `applied` rows at ratio≈1.0000 confirm that branch is fixed. The
`identity` branch (n_real==n_proto==3) is a **documented no-op** by design
(`layout_assigner.py:545`, "n_real == n_proto: identity, no-op (B02's byte-identical regression guard)")
— the `ZoneGroup`'s Zone List Multiplier of 2 is never touched, so the untouched baseline (always a
true 4-storey-equivalent building, `recomputed_area_m2` 3,134.7 m² ≈ the 3,135.0 m² registry constant
at `layout_assigner.py:71`) is copied wholesale onto every `identity`-status `MidriseApartment` building,
regardless of its real `num_floors==3`. **This is not a new defect and not something this task fixes** —
`n_proto` was deliberately kept as the raw band count specifically so `identity`'s branching (and R04(a)'s
frozen population split) would not move (line 404-418) — but its measured consequence for the
`identity` population specifically had not, before this task, been confirmed on a real building with a
real `eio` file. **Flagged for the director:** whether E-LA-25's "not yet known to double-count energy"
disposition (line 94) should be revised now that `identity`-status buildings are directly shown to
carry a 33% floor-area overstatement is a disposition question, not something decided here.
**What this implies about the EUI denominator used everywhere else in this arc (R06, R09, T17-T20):**
those harvests all use nominal `footprint_area_m2 × levels`, never `eio` (R06 items 3/7; R09's own
`EUI_DENOMINATOR_NOTE`) — so **every published `MidriseApartment` `identity`-status EUI in this arc's
figures is silently computed on a denominator ~25% smaller than what was actually simulated**
(1/1.3333 ≈ 0.75), i.e. those buildings' true per-area intensity is ~25% lower than reported, while
`applied`-status buildings' published EUI is unaffected (ratio≈1.0000, confirmed above). This is scoped
to `MidriseApartment` `identity` rows only; not measured for `HighriseApartment` (which the P0 finding
also implicates, list multiplier 8, untested here — single-digit-N scope, forwarded as an open question).

**N stated: 6 buildings run locally (4 `applied` + 2 `identity`), all `run_status="success"`, 0 Severe,
41 warnings each — per `eplusout.err` in each building's own run directory under
`scratchpad/r06c_work/runs/<way_id>/`, never `.end`, never `has_fatal`.**

---

**Part 3 — F-11 population reconciliation (805 vs 698 vs 439), pure CSV analysis:**

**The filter that takes 698 → 439, found and verified exactly:** `new_status in {"applied",
"fallback_not_expressible"}` — i.e. drop `fallback_shorter` (225 rows) and `identity` (34 rows) from
the 698-row `scratchpad/f11_transformer_check_v3.csv`. Reproduces the R06 entry's 439 split **exactly**,
archetype by archetype:

```
                    applied  fallback_not_expressible   sum (=439 filter)   R06's reported 439
LargeOffice               0                        170                170                 170
MediumOffice            231                          0                231                 231
HighriseApartment         5                         24                 29                  29
SecondarySchool           0                          7                  7                   7
Hospital                  0                          1                  1                   1
PrimarySchool             1                          0                  1                   1
                                                            TOTAL = 439                    439
```
This is not an arbitrary cut: `applied ∪ fallback_not_expressible` is exactly the "taller than
prototype" half of F-11's **original** definition ("transformer-bearing **and** taller-than-prototype"
— `DONE_PLAN_storey-matching_implementation.md:742`, `fallback_shorter`=shorter,
`identity`=equal-height, so excluding both leaves exactly the taller-than-prototype subset).

**Which of the three is the real F-11 population: 439, corrected for the two post-fix realities (Deviation
2's archetype relabelling and R10's status-shrinking), not 698 and not 805.**
- **805** — the original F-11 estimate, pre-R01/R02/R03/R10, pre-archetype-fix. Stale; superseded.
- **698** — `scratchpad/f11_transformer_check_v3.csv`'s row count. This is only the **first half** of
  F-11's definition, re-measured (all 7,442-evaluated buildings whose *corrected* `archetype_id` is one
  of the 6 transformer-bearing archetypes, **regardless of height**) — a staging population, not F-11
  itself. Confirmed identical to `t20_r10_reach_change.csv` restricted to the same 6 archetypes (698
  rows both ways, same per-archetype counts).
- **439** — `applied ∪ fallback_not_expressible` within that 698, i.e. the corrected re-measurement of
  F-11's actual original definition (transformer-bearing **and** taller-than-prototype). **This is the
  real F-11 population.**

**Item 4's restated, reproducible MediumOffice split (against the entry's uncited/inconsistent `0/125`
and `107/107`, which the AUDIT — R06 already flagged as non-reproducing and internally inconsistent,
125+107=232≠231):** filtering `scratchpad/f11_transformer_check_v3.csv` to
`archetype_id=="MediumOffice" & new_status=="applied"` (231 rows, matching the entry's own 231) and
splitting on `new_multiplier`:
```
multiplier 2-7   n=114   overloaded 0     (0.0%)
multiplier >=8   n=117   overloaded 117   (100%)
114 + 117 = 231  ✓ (closes exactly against MediumOffice's own applied total)
```
**R08 should print `0/114 (0.0%)` and `117/117 (100%)`, both from
`scratchpad/f11_transformer_check_v3.csv` filtered to `archetype_id=="MediumOffice" &
new_status=="applied"`, split at `new_multiplier<=7` vs `>=8`** — reproduces the director's own
recomputation exactly. The signed conclusion (D9's bound holds through multiplier 7, fails absolutely
at 8) is unchanged; only the printable n's were in question, and are now traceable to one named file
and one one-line filter.

---

**Artifacts:**
- `scratchpad/r06c_work/r06c_runs.py` — harness (throwaway, not shipped).
- `scratchpad/r06c_work/r06c_local_results.csv` (6 rows) + canonical copy
  `openubem/outputs/comparisons/r06c_local_results.csv`.
- `scratchpad/r06c_work/step3_layout_assign/idfs/way_{401907384,401910461,401910885,427049841,
  427049849,427049871}.idf` — the 6 real generated IDFs (SHA-256-distinct, see Part 1).
- `scratchpad/r06c_work/runs/way_<id>/eplusout.{eio,err,sql}` — one directory per building, all 6
  `run_status="success"`, 0 Severe.
- `scratchpad/r06c_work/run_r06c.log` — full console log of the batch.
- No `openubem/` production code touched. `scratchpad/f11_transformer_check_v3.csv` read-only (Part 3).

**Deviations:** one, described above (harness `.reset_index(drop=True)` fix for
`assign_climate_zones()`'s index-alignment precondition — not a production defect).

**Test status:** N/A — measurement-only task, no `openubem/` production code path modified. No pytest
regression run (none of `layout_assigner.py`/`builder.py`/`envelope_patcher.py` touched).

**Notes for the director / R08:** Part 1 and Part 2 are now both answered with real fleet evidence
(not the vacuous R05 1.0000×) — condition (a): heating ratio moves *away* from 1.0 in a mild-heating
climate where the absolute effect is small; condition (c): holds for `applied`, fails at a clean 4/3 for
`identity`, a measured-but-previously-abstract consequence of the already-recorded P0/E-LA-25 finding.
Two things forwarded, neither actioned here: (1) whether E-LA-25's disposition needs revision now that
`identity`-status energy exposure is directly measured; (2) whether `HighriseApartment`'s analogous
`identity` population (list multiplier 8, untested here) carries the same or a larger mismatch.

**Not signed:** CP-E. Remaining path: **R08 → CP-E.**

---

## 🔶 AUDIT — R06c — director — 2026-08-04 — **ACCEPTED, with one new defect ID and one scope correction**

CP-D's two carried conditions (a) and (c) are now answered on real fleet buildings with real `eplusout.eio`
evidence. Every headline number in the R06c entry was recomputed independently by the director from the
named files before this verdict. **All reproduce exactly.**

### 1. Verification — every claim re-derived from the named file

| Claim in R06c | Director's independent recomputation | |
|---|---|---|
| Pair A heating ratio `0.211667 / 0.652532 = 0.3244×` | `0.32438` from `r06c_local_results.csv` | ✅ |
| Pair B heating ratio `0.033475 / 0.507077 = 0.0660×` | `0.06602` | ✅ |
| Heating as share of total `eui`: 0.207 / 0.136 / 0.330 / 0.032 % (applied), 0.653 / 0.509 % (control) | 0.2074 / 0.1361 / 0.3295 / 0.0320 %; 0.6527 / 0.5088 % | ✅ |
| `applied` denominator ratios ≈ 1.0000 (N=4) | 1.000017 / 0.999999 / 1.000019 / 1.000005 | ✅ |
| `identity` denominator ratio = 4/3 (N=2) | 1.333390 / 1.333343 | ✅ |
| All 6 runs `success`, 0 Severe, 41 warnings | confirmed from `run_r06c.log` and the per-building `runs/<id>/` dirs | ✅ |
| Controls are genuinely `identity`, `num_floors == n_proto == 3`, no multiplier | confirmed in `t20_r10_reach_change.csv` | ✅ |
| Qualifying `applied` population 435 fleet-wide, 46 in `la_urban`/`MidriseApartment` | 435 and 46 | ✅ |
| F-11 filter `new_status ∈ {applied, fallback_not_expressible}` takes 698 → 439 | 439, and the per-archetype split reproduces R06's six numbers **exactly** (MediumOffice 231, LargeOffice 170, HighriseApartment 29, SecondarySchool 7, PrimarySchool 1, Hospital 1) | ✅ |
| MediumOffice cliff `0/114 (0.0%)` and `117/117 (100%)`, closing 114+117=231 | identical | ✅ |

**Non-degeneracy — the CP-D trap is cleared.** Unlike R05's vacuous `1.0000×`, the two sides here are
different real buildings on **different code paths**: `applied` mutates the IDF (`Zone.Multiplier` 2 or 3
on the `Mid Floor List` `ZoneGroup`), `identity` is a no-op. Four distinct SHA-256 IDF hashes. Condition
(a) is satisfied as a measurement, not an identity.

**Note for R08 on two numbers that look contradictory and are not:** the `applied` population is **503**
(AUDIT — R06), of which **435** carry a residual multiplier ≥ 2 and **68** carry multiplier exactly 1
(the `ZoneGroup`'s own list multiplier already reproduces `n_real`, so no field write happens — still
`applied`). Both numbers are correct; use the one whose definition matches the sentence.

### 2. Process checks

- Never touched the cluster; fleet not re-submitted; `submit_fleet_t08.sbatch` unmodified. ✅
- No `openubem/` production code modified — confirmed. The one deviation (a `.reset_index(drop=True)`
  in the throwaway harness) is a harness precondition, correctly diagnosed as *not* a defect in
  `assign_climate_zones()`. ✅
- `has_fatal` never cited; `.end` never cited; every quantity traces to a path that exists on disk. ✅
- Append-only, single append after `AUDIT — R09`, tail re-read first. ✅

### 3. 🆕 Scope correction and new defect — **E-LA-41**

R06c scoped its denominator finding to `MidriseApartment` **`identity`** rows only. **That scope is too
narrow, and the entry's own cited code says so.** `match_storeys()`'s contract
(`openubem/geometry/layout_assigner.py:542-544`, read by the director) is explicit:

> *"Mutates `idf` in place ONLY when the returned status is `applied`; **every other status leaves `idf`
> untouched**."*

`identity`, `fallback_shorter` and `fallback_not_expressible` are therefore **the same case** for this
purpose — all three simulate the prototype's own `n_storeys_represented`, not the building's
`num_floors`. R06c measured that quantity directly (4 storey-equivalents on a 3-storey `MidriseApartment`,
twice, exactly). The denominator error factor is therefore
`n_storeys_represented / num_floors` for **every non-`applied` building**, not just the `identity` ones.

**E-LA-41 — the published EUI denominator is wrong by `n_storeys_represented / num_floors` for every
non-`applied` building in `layout_assign`.** Registered 2026-08-04, **forwarded open, not fixed in this
arc.**

- **Mechanism:** E-LA-25 / P0 (the `ZoneGroup` Zone List Multiplier makes `n_storeys_represented` exceed
  `n_proto`) *plus* the fallback contract above. The mechanism is old; **this quantified EUI consequence
  is new and is what gets the ID.**
- **Measured, directly:** `MidriseApartment` `identity`, N=2, ratio exactly 4/3 — `eio`-true, real fleet
  buildings, `r06c_local_results.csv`.
- **Inferred by the code contract, NOT measured** — R08 must label it as inference. `MidriseApartment`
  non-`applied` exposure, from `t20_r10_reach_change.csv`:

  | `num_floors` | n | `eio`/nominal = 4/`num_floors` |
  |---|---|---|
  | 1 | 1,225 | **4.000×** |
  | 2 | 1,048 | **2.000×** |
  | 3 | 343 | 1.333× |
  | 5 | 49 | 0.800× |
  | 7 | 16 | 0.571× |
  | 9 | 1 | 0.444× |
  | | **2,682** | |

- **Fleet-wide structural exposure: 6,939 of 7,442 evaluated buildings are non-`applied`.** The factor for
  the other archetypes is unmeasured (it equals `n_storeys_represented / num_floors`, which is
  `n_proto / num_floors` for the 23 archetypes with no `ZoneGroup`).
- **Reading, stated conservatively:** for a 1-storey building the mode simulates a 4-storey apartment
  prototype and then divides that energy by one storey's floor area. The reported EUI is not a wrong
  number for the building that was simulated — it is a correct number for the **wrong building**. This is
  the numeric expression of E-LA-33 (height does not track `num_floors`) and of the mode's own fallback
  design; it is not a new mechanism, and it does **not** reopen the frozen constants or R04(a).
- **E-LA-25's disposition** — R06c correctly forwarded rather than decided it. Director's call: E-LA-25's
  "not yet known to double-count energy" line is **superseded by E-LA-41**, which now measures the
  exposure. E-LA-25 itself stays as recorded; do not rewrite it.
- **`HighriseApartment`** (list multiplier 8) is untested and has **0** `identity` rows but **24**
  `fallback_not_expressible` and **3** `fallback_shorter` — so it is in E-LA-41's population, unmeasured.

### 4. Carry-ins for R08

1. **Print the F-11 cliff as `0/114 (0.0%)` and `117/117 (100%)`**, from
   `scratchpad/f11_transformer_check_v3.csv` filtered to `archetype_id=="MediumOffice" &
   new_status=="applied"`, split at `new_multiplier<=7` vs `>=8`. State that **439** is the real F-11
   population and name the filter. The signed cliff conclusion is unchanged.
2. **Disclose E-LA-41** with the measured part and the inferred part clearly separated, and with the
   1-storey/2-storey exposure counts. This is a headline disclosure, not a footnote.
3. **Report Part 1's heating ratio with its scope limit in the same sentence** — one cell, one archetype,
   one mild climate where heating is 0.03–0.65 % of total EUI. R06c wrote that limit correctly; do not
   drop it when summarising.
4. Condition (c) is answered: **holds for `applied` (N=4, ~0.002 %), fails at 4/3 for non-`applied`.**

### 5. Verdict

**R06c is ACCEPTED.** CP-D's conditions (a) and (c) are discharged — (a) as a real, non-degenerate
measurement, (c) as a real measurement with a negative result that is correctly attributed and now
carries its own defect ID. R06c's own scoping was one step too narrow and is corrected above; that is a
scope widening, not an error in anything it measured.

**Not signed:** CP-E. Remaining path: **R08 → CP-E.**

---

#### R08 — C03: documentation closure — completed 2026-08-04

**Pre-flight:** read, in order, §1 hard rules, §3 R08's own task text (line 249), and the last six §5
entries in full (`R06`, `AUDIT — R06`, `R09`, `AUDIT — R09`, `R06c`, `AUDIT — R06c`) — tail unchanged
since AUDIT — R06c's verdict at line 1967, "Remaining path: R08 → CP-E," no concurrent append had
landed. Read `figures/README.md` in full and reused its wording rather than drafting a second, drifting
version. Grepped `DONE_PLAN_storey-matching_implementation.md` (CLOSED, ~3,500 lines) only for `B08a`/
`B08b`'s named measurements (needed for R07's reduced write-up, since neither number lives in this
document) — did not read the file end to end.

**This is a documentation task; no `openubem/` production code, no cluster, no pipeline run, no figure
regenerated.** Files touched — exactly the three the brief names, no fourth:

1. **`OpenUBEM_results_LayoutAssigner.md`** — added §8 ("Storey-matching arc close, T20 fleet result")
   and §9 ("Standing disposition after the storey-matching arc"), as an addendum in this doc's own
   established convention (§§5/6/7 are the precedent — frozen historical sections stay untouched,
   the current result is a new appended section). §8 carries all 15 disclosure items headline-first,
   the corrected F-11/439/0-114/117-117 numbers, the full 4-term success-gain decomposition, E-LA-36
   through E-LA-41, and R07's reduced 3-quantity write-up (placement/plate-area-aspect-ratio/overlap,
   with height stated explicitly out of scope). §9 states the standing disposition and the full
   forwarded-defect list. §§1–7 are byte-untouched.
2. **`docs/PROJECT_CHECKLIST.md` §L** — header updated to 6 sub-arcs closed, R08 done, CP-E pending
   director; sub-arc index table gained row 7 (storey matching); the stale "Successor arc — PLAN
   WRITTEN, NOT STARTED" block (which had not been touched since 2026-07-26 and no longer reflected
   reality) was replaced with a closed-arc summary carrying the T20 headline, the R04/Q3 disposition,
   and a note naming the three non-reproducing-number incidents this arc had, so a future reader does
   not have to re-discover why three AUDIT entries exist.
3. **`DONE/DONE-implementation_plan.md` §7** — appended a dated sub-bullet to the existing Q3 entry
   (numbered "4.", after the existing numbered list) stating the verdict plainly: **Q3 is NOT closed
   by this arc**, with the two independent structural reasons (mechanism only reaches the taller case;
   even there it is a `Zone.Multiplier`, not a geometry change, so it could not have closed Q3's actual
   mechanism either way). Existing entries in that section (including the original Q3 text) are
   byte-untouched — appended, not rewritten.

**Q3 disposition — stated in one place so the answer to the brief's own question is unambiguous: Q3 is
NOT closed by this arc.** `match_storeys()` only expresses `n_real > n_proto`; Q3's population is
`n_real < n_proto` (median S=0.054); R04 explicitly declined to extend the mechanism to that case
("the hard direction is shorter than the prototype... a `Zone Multiplier` cannot help," this
document's own line 983-984 precedent in the checklist, confirmed exactly as pre-registered). Even in
the case the mechanism does reach, it changes simulated energy accounting, not rendered geometry
(§8.4/D3(a)/E-LA-33) — a different axis from Q3's vertical-form/surface-to-volume mechanism. This is
not "ran out of time" — it is a structural mismatch between the mechanism this arc built and the
mechanism Q3's distortion needs, now confirmed rather than assumed.

**The 15-item disclosure list, as shipped in the results doc §8 (all 15 present, headline text, not a
footnote):** (1) `match_storeys()` expresses only `n_proto ∈ {1,3}`, taller case only; `n_proto==2`/
`>=4` and every `n_real<n_proto` fall back permanently. (2) R10's exactness rule shrinks the two
`ZoneGroup` archetypes' expressible set; applied population 503 (was 593, −90, all
`applied→fallback_not_expressible`); stale 81.6%/98.4% inert shares replaced with 100.0%/84.1%.
(3) Storey matching invisible in geometry by construction (D3(a)); height does not track `num_floors`
(E-LA-33). (4) 718 buildings (8.8%) have no `ARCHETYPE_IDF_MAP` entry. (5) Shape-mismatch overlap
residual is a design property, not a bug (R07's 3 measured quantities). (6) R03's PV/generator
invariance is synthetic-fixture only, no real-run evidence. (7) E-LA-36 found and fixed inside this
arc (0/522 verified) — stated as a result, not buried. (8) Forwarded out: E-LA-21/22/23/24, E-LA-37.
(9) EUI denominator is nominal (`footprint_area_m2 × levels`), never `eio`-verified, structurally
impossible to reconstruct without re-running the fleet; R06c's local measurement is the only `eio`-true
evidence and is scoped as single-digit-N/local. (10) E-LA-38 — 41/8,160 archetype mislabels; the
fleet's only 7 failures are 100% explained by it (true `SmallHotel`, 87.5% of the fleet's 8 real
`SmallHotel`s). (11) E-LA-39 — `has_fatal` is a dead column, never cited. (12) E-LA-40 — 3 T19→T20
regressions, all inside the E-LA-38 population, forwarded open. (13) Full 4-term success-gain
decomposition printed (+150+2+14−3=+163), stated as overwhelmingly not this arc's own work, in the
same sentence as the number. (14) E-LA-41 — EUI denominator wrong by `n_storeys_represented/num_floors`
for every non-`applied` building, measured part (N=4 applied ≈1.0000×, N=2 `identity` at exactly 4/3)
separated from the inferred part (1,225 at 4.000×, 1,048 at 2.000×, 343 at 1.333×, 66 below 1.0, 2,682
total; 6,939/7,442 fleet-wide non-`applied`). (15) CP-D's two carried conditions both answered:
condition (c) holds for `applied`, fails at 4/3 for non-`applied`; condition (a) heating ratio
0.3244×/0.0660×, scope limit (one cell, one archetype, one mild climate, 0.03–0.65% of total EUI)
stated in the same sentence.

**Corrections from the audits, landed exactly as instructed:** F-11 cliff printed as `0/114 (0.0%)`
and `117/117 (100%)` (never `0/125`/`107/107`); F-11 population stated as 439 with its filter named;
503 vs 435 both printed, with which-one-means-what stated; E-LA-36's 0/522 cited as director-verified;
fleet headline 8,153/8,160=99.914%, median 122.23, with E-LA-22 stated in the same breath.

**Artifacts:** `OpenUBEM_results_LayoutAssigner.md` (§8, §9 added), `docs/PROJECT_CHECKLIST.md` (§L
updated), `DONE/DONE-implementation_plan.md` (§7 Q3 entry appended), this progress-log entry. No other
file touched — `git status --short docs/ openubem/ scripts/ tests/ main.py` before this append showed
only pre-existing R06/R09/R06c modifications (verified by re-reading the tail of this document and
comparing against those three entries' own listed artifacts before writing a line); after this append,
the only new diffs are the three named files plus this entry.

**Outdoor-analysis registry:** checked — this arc produced no new outdoor/site metric. No entry added
to `docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md`, per the brief's explicit instruction.

**Deviations:** none from the brief. One clarification made explicit rather than silently resolved:
the brief's Files-to-update wording says "§3/§3a" for the results doc, but §3/§3a are T17-era frozen
historical sections under this doc's own established addendum convention (§§5/6/7 already extend the
"results write-up" as new appended sections rather than rewriting §3/§3a) — followed that precedent
and added §8/§9 as the next addendum in the same series, rather than editing frozen §3/§3a text. If
the director intended a literal in-place edit of §3/§3a, flagging this choice explicitly here rather
than have it discovered silently.

**Test status:** N/A — pure documentation task, no `openubem/` code path touched, no pytest implied.

**Notes for the director:** CP-E is not signed here, per the brief's explicit instruction — that
signature is the director's. Every number in the results-doc §8 addendum was traced to a named file or
a named §5 entry above before being printed (per the brief's rule; three prior entries in this arc
shipped numbers that did not reproduce — this entry does not add a fourth). Nothing else was left
open by this task beyond what §8.11/§9 already forward.

**Not signed:** CP-E. This was the last executor task in the arc; nothing further is scheduled.

---

## 🔶 AUDIT — R08 — director — 2026-08-04 — **ACCEPTED, with one definitional correction made by the director**

### 1. Verification

Every number printed in the new results-doc §8/§9 was traced to a named file by the director before
this verdict. All reproduce.

| Claim | Independent recomputation | |
|---|---|---|
| Fleet 8,153/8,160 = 99.914%, median `total_eui` 122.23; T19 7,990/8,160 = 97.92%, median 103.75 | identical | ✅ |
| Gain decomposition `+150 + 2 + 14 − 3 = +163` | identical | ✅ |
| `applied` 503, down 90 from 593 (66 `MidriseApartment` + 24 `HighriseApartment`) | identical | ✅ |
| Status transition matrix (503 / 90 / 1,902 / 3,727 / 1,220) | reproduced exactly by `pd.crosstab(old_status, new_status)` on `t20_r10_reach_change.csv`; rows sum to 7,442 | ✅ |
| 503 = 435 (multiplier ≥ 2) + 68 (multiplier = 1) | identical | ✅ |
| 7,442 = 8,160 − 718 no-baseline | identical | ✅ |
| E-LA-41 exposure: 1,225 / 1,048 / 343 / 66 below 1.0 / 2,682 total; 6,939 of 7,442 non-`applied` | identical | ✅ |
| F-11: counts `0/114` and `117/117`, 114+117=231; population 439 with the six-archetype split | identical | ✅ |
| CP-D (a) 0.3244× / 0.0660×, heating 0.03–0.65% of total EUI; (c) ~0.002% / 4×3 | identical | ✅ |
| R07's absorbed geometry numbers — placement 0.00024 m / 0.00026 m, overlap 27.00→16.24% and 55.40→52.27%, controls 0.00% / 1.79% | verbatim against `DONE_PLAN_storey-matching_implementation.md:2711-2716` | ✅ |

**File discipline:** `git status` confirms R08 modified exactly its three permitted files plus this
plan doc's progress log. The other modified paths in the tree (the five `layout_assign_vs_modes_*`
deliverables, `plot_layout_assign_vs_modes.py`, `t20_r10_reach_change.py`, `figures/README.md`) all
pre-date R08 and belong to R09. No production code touched. No commit made. ✅

**Deviation — accepted, and it was the right call.** The brief named "§3/§3a" of the results doc.
§§3–7 are frozen, dated historical addenda (§5 = T18, §6 = T19, §7 = 2026-07-26); R08 added §8/§9 as
the next addendum in that same series rather than editing frozen text in place. That matches this
project's correction-via-addendum convention and the arc's append-only rule. **A literal in-place
edit would have been the worse outcome.** Deviation logged, no rework required.

### 2. 🔧 Director correction — the replacement inert shares needed their definition stated

R08 replaced the stale **81.6% / 98.4%** inert shares with **100.0% / 84.1%** and printed no
definition. Checked, and the two are not measuring the same thing:

- The original 81.6% / 98.4% was an **archetype proxy** — the share of each cell that is `SmallOffice`
  or `MidriseApartment`, over all 8,160 buildings (`DONE_PLAN_storey-matching_implementation.md:347`).
  Recomputed on T20 it is **81.5% / 98.4%** — essentially unchanged. **The proxy is not stale; only
  its use as an inert share is.**
- R08's replacement is a **status measurement** over the 7,442 evaluated buildings, and it counts
  `identity` as *not* inert. Under that definition: `nyc_suburban` 100.0% (1,297/1,297),
  `la_suburban` 84.1% (1,121/1,333) — both verified. Counting `identity` as inert instead gives
  100.0% and **98.7%** (1,316/1,333) — also verified.

Both readings are defensible; quoting either without naming it is what let the original number drift.
**The director edited §8.2 directly** to state the definition, give both columns, and record that the
old figures measured a different quantity over a different denominator. This is a one-paragraph
definitional fix to a results doc, not feature work, and is logged here rather than sent back for a
dispatch. `la_suburban`'s 197 `identity` rows are noted as exactly the population E-LA-41 shows is not
really matched.

### 3. Q3's verdict — reviewed and endorsed

R08 concluded **Q3 is NOT closed by this arc** and appended (did not rewrite) that verdict to Q3's own
entry. The director endorses it. The reasoning is structural and correct on both legs: `match_storeys()`
expresses only the taller case while Q3's population is the shorter case, and R04 declined to extend
it — a stop condition **pre-registered before the arc began, which then fired exactly as anticipated**;
and separately, a `Zone.Multiplier` changes simulated load, not rendered geometry, so it could not
reach Q3's mechanism even if extended. Reporting a named candidate as structurally unreachable is a
result, not a shortfall.

---

## ✅ CP-E — **SIGNED** — director — 2026-08-04 — the storey-matching arc is CLOSED

**All tasks discharged:** R01, R02, R03, R10, R05, R06, R06b, R06c, R09, R08. R04 closed at option (a)
by manager decision. R07 reduced to a written statement and absorbed into R08 — nothing dropped from
the record, only a redundant rendering pass. CP-A/B/C/D signed previously; **CP-E signed here.**

**What the arc delivered.** A residual `Zone.Multiplier` storey-matching mechanism that is
`ZoneGroup`-aware and verified correct where it applies — `applied` buildings simulate exactly
`footprint × num_floors`, confirmed against real `eplusout.eio` on real fleet buildings. A full 12-cell
/ 8,160-building T20 fleet re-run at 99.914% success. Five regenerated cross-mode figures. A results
addendum whose every number is traceable to a named file.

**What the arc found and fixed inside itself:** E-LA-36, a silent 50% storey over-count on the fleet's
dominant archetype, 0/522 after the fix.

**What the arc found and forwarded open, unfixed and honestly labelled:** E-LA-38 (41 mislabelled
archetypes, which turn out to explain 100% of the fleet's 7 failures), E-LA-39 (`has_fatal` is a dead
column), E-LA-40 (3 regressions), **E-LA-41** (the EUI denominator is wrong by
`n_storeys_represented / num_floors` for 6,939 of 7,442 evaluated buildings), plus the previously
forwarded E-LA-21/22/23/24 and E-LA-37.

**What the arc does NOT claim, stated at closure so no later reader has to rediscover it:**
- The +163 success gain is **not** this arc's work — 150 of it is E-LA-20's pre-existing fix landing
  at fleet scale for the first time.
- **No fleet-scale EUI in this arc has an `eio`-verified denominator**, and none can be reconstructed
  without re-running the fleet. R06c's 6-building local measurement is the entire body of `eio`-true
  evidence that exists.
- **Q3 is not closed**, and the mechanism this arc built is now confirmed structurally unable to close it.
- `layout_assign` remains adopted for zone/HVAC-topology studies and **not certified for fleet-level
  EUI reporting** (results doc §9).

**Process note, recorded because it recurred.** Three executor entries in this arc shipped a headline
number that did not reproduce from the file it cited (F-11's cliff counts twice; the inert shares
going stale without a correcting entry). All three were caught by director audit, none by the executor.
The countermeasure that worked was cheap and should carry forward: **the director recomputes every
headline number from the named file before signing, and the brief states that requirement explicitly.**

**Nothing in this arc is left in flight.** No cluster job outstanding, no fleet re-submission pending,
no executor mid-task. Frozen constants `T_ENGAGE = 0.868` / `T_MASS_MAX = 0.35` untouched throughout.

**CP-E: SIGNED. Arc CLOSED 2026-08-04.**
