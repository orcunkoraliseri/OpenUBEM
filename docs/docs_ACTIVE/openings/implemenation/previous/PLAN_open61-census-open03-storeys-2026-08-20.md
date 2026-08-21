# PLAN — OPEN-61 fleet census, and OPEN-03's storey-count disagreement

> **Slug:** `open61-census-open03-storeys` · **Date:** 2026-08-20 · **Author:** manager session
> **Authorised by the user 2026-08-20**, both arcs, in answer to a direct question.
> **Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` §6 (OPEN-61,
> OPEN-03) · **predecessor plan:** `PLAN_five-items-2026-08-20-late.md` §6b/§6c (facts D8–D12).
> **DESIGN pointers:** `docs/docs_main/docs_step5/` (results parsing) and
> `docs/docs_main/docs_step3/` (geometry build). **Neither is edited by this plan.**
> **Status:** ✅ **CLOSED 2026-08-21.** All tasks complete — T01–T05; CP-1, CP-2, CP-3 and CP-4
> all audited and signed 2026-08-20. Arc A delivered the fleet district-heating number
> (19.4707 kWh/m² over n = 8,144, §6e); Arc B closed at CP-4. T02 has no separate progress-log
> entry by design — its record is CP-2 in §6d (see the note in §8).
> **Archived to `implemenation/previous/` on 2026-08-21.**

---

## 1. What this plan is for, in two sentences

**Arc A (OPEN-61)** replaces an estimate with a measurement. The predecessor plan established that
every building in the fleet spends service-hot-water energy through a channel the parser never reads,
and sized the loss at **an estimated 8.7–20.2 kWh/m², 6–13 % of the adopted 153.8231** — a range built
by transferring a 60-building ratio onto 8,153 buildings. That range is a size, not a correction, and
**this plan exists to make it a real number.**

**Arc B (OPEN-03)** measures the defect that survived the retraction. The item's stated mechanism
("`layout_assign` builds 44 % less wall on the same floor plate") reproduces on exactly one building
and was withdrawn. What replaced it is a **storey-count disagreement**: 28 of 48 sampled pairs build a
different number of storeys from a bit-identical footprint. Arc B is a census of that, and it needs
**no simulation at all.**

---

## 2. Hard rules for the executor

1. **You execute this plan. You do not propose alternatives.** If the plan is ambiguous or conflicts
   with a DESIGN doc, **STOP and quote the conflict**. Do not invent a resolution.
2. **Never block waiting to be woken.** Three of four executors on the previous plan stalled by
   backgrounding a job and reporting "waiting for the monitor". **A waiting agent is never woken.**
   If you start something long, poll its own disk artifact yourself in a bounded loop
   (`ls`, `wc -l`, `tail -3`) and continue when the artifact says it is done.
3. **No compute on the cluster login node.** If Arc A runs on Speed: `sbatch --array` only,
   fire-and-forget, then read the output file. Login node is for `mkdir`, `scp`, `tar`, `squeue`,
   `sacct` and nothing else. Remote shell is **tcsh** — wrap every command via the `_ssh()` helper at
   `scripts/cluster/t08_harvest_results.py:104`, never send a bare command string.
4. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first.**
   After solving any error, **register it there before closing the task.** Not optional.
5. **This plan measures. It does not remediate.** Do not change how `parse_building()` computes an
   EUI, do not add a meter to the production IDF builder, and do not restate the adopted
   **153.8231 kWh/m²**. Instrumentation added for measurement is scratch-only and named as such.
6. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, or anything under `docs/docs_main/`.
7. **No `.py` files under `docs/`, ever.** All figures/`.png` go to `openubem/outputs/` flat.
8. **Append to §8 of this doc, one entry per completed task, at end of file.** Re-read the file
   immediately before appending. Never rewrite or reorder someone else's entry.
9. **Report the number you measured, not the number you expected.** If a control fails, say so and
   stop at the checkpoint. A failed control is a result.

---

## 3. File layout

| Path | Role |
|---|---|
| `scripts/analysis/open61_census_read_2026-08-20.py` | T01 — the district-heating reader + its verification |
| `scripts/analysis/open61_census_build_2026-08-20.py` | T02 — rebuild harness + stratified pilot |
| `scripts/analysis/open61_census_run_2026-08-20.py` | T03 — full-fleet execution + harvest |
| `scripts/analysis/open61_census_report_2026-08-20.py` | T04 — fleet arithmetic |
| `scripts/analysis/open03_storey_census_2026-08-20.py` | T05 — storey-disagreement census |
| `openubem/outputs/comparisons/open61_census_*.csv` | all Arc A outputs |
| `openubem/outputs/comparisons/open03_storey_census*.csv` | all Arc B outputs |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_fleet-census.md` | Arc A report |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_storey-census.md` | Arc B report |
| scratch simulation output | **outside the repo tree**, under the session scratchpad or `evidence/` |

`evidence/` is gitignored (commit `64cb61b`). Nothing this plan produces is committed by the
executor — **git is handled externally; never run `git commit`.**

---

## 4. Dependency decisions — pinned, do not revisit

- **Python:** `py -3` on Windows. A bare `python` hits the Store shim and fails silently.
- **EnergyPlus:** `23.1.0-87ed9199d4`, the same build as run 4. **Do not upgrade mid-census** — a
  version change would confound the comparison against the recorded fleet.
- **Large shell heredocs are unreliable in this environment.** Write a script file, then run it.
- **`trim_outputs=False` is mandatory for every rebuild.** `BuildingIDF.__init__` takes
  `trim_outputs: bool = False` (`openubem/idf/builder.py:219,227`) and passes it to
  `write_outputs(self.idf, trim_hourly=self.trim_outputs)` (`:516`, `:638`). With `True`, the per-zone
  `Output:Variable` block is stripped and the parser's own gate `_check_zone_integrity`
  (`openubem/results/parser.py:203`, called at `:772-774`) rejects the result. **This is the exact
  trap that cost the 2026-08-19 arc three separate measurements.**
- **Cluster vs local is T02's decision, made on T02's measured pilot rate, not now.** Both are viable
  (see §5, fact F4) and the plan does not pre-empt it.

---

## 5. Facts this plan stands on — each with its citation

| # | Fact | Source |
|---|---|---|
| **F1** | `METER_QUERY` selects ten meters by name and **none of them is a district-heating meter**, so `total_eui_kwh_m2` cannot include the term. | `openubem/results/parser.py:42`, names at `:48-54` — director-verified at HEAD 2026-08-20 |
| **F2** | `dhw_kwh = _m("WaterSystems:NaturalGas") + _m("WaterSystems:Electricity")` — the recorded DHW figure, and the denominator of the ratio the estimate was built from. | `openubem/results/parser.py:469` |
| **F3** | The discriminator is exact on 108 buildings: District Heating > 0 **iff** a `DHW_WaterUse_*` object exists **and** no `PlantLoop` does. **All 16,336 production IDFs match the affected pattern; 0 have a `PlantLoop`.** 60 of 60 re-simulated production buildings carry the term. | `PLAN_five-items-2026-08-20-late.md` §6b facts D8/D9, §6c |
| **F4** | **Run 4 is on disk but its `.sql` files were discarded** — 8,160 buildings each keep only `eplusout.eio`, `.end`, `.err`. Measured on a 400-building sample: **median 14.2 s, mean 52.5 s, max 1,280.3 s** per building ⇒ the full fleet is **≈119 CPU-hours**. | director-measured 2026-08-20 from `evidence/open48_refleet4/*/sim_out/*/eplusout.end` |
| **F5** | The estimate to be replaced: fleet-mean unreported term **8.7 / 17.2 / 20.2 kWh/m²** at the ratio IQR floor / median / ceiling (dh ÷ dhw_eui median **0.714**, IQR **0.362–0.840**). `MidriseApartment` is **2,818 of 8,160** (34.5 %). | `PLAN_five-items-2026-08-20-late.md` §6c fact D11/D12 |
| **F6** | OPEN-03: control C7 excluded **40 of 48 pairs** because the arms do not build the same floor plate; **28 of those are storey-count driven**. Where storeys agree, roof and ground ratios are **exactly 1.0000**. | `openubem/outputs/comparisons/open03_envelope_decomposition.csv` (has a `storey_count` column per arm) |
| **F7** | 2 of 48 `layout_assign` IDFs use `Zone.Multiplier` > 1; **0 of 48** `auto` IDFs do — the OPEN-60 link. | same CSV, T03 of the predecessor plan |
| **F8** | The adopted figure is **153.8231 kWh/m² pooled over 8,153**. It is **not volume-correct** and OPEN-56's ≈+1.0 is not in it. **This plan does not restate it.** | register book II §1 |

---

## 6. Task list

### T01 — Establish how the district-heating term is read from a `.sql`, and prove the read twice

**What.** Write `scripts/analysis/open61_census_read_2026-08-20.py` exposing one function that takes
an `eplusout.sql` path and returns the district-heating total in GJ and in kWh. Prove it on the
**five known-positive buildings** from the predecessor's 48-building sample and on five known-negative
ones.

**Why.** The whole census is this one read repeated 8,160 times. If the read is wrong, every number
downstream is wrong, and it will be wrong in a way that looks plausible. **F1 tells us the meter route
the parser uses does not carry this term** — so the read is almost certainly the ABUPS tabular report,
not `ReportData`.

**How.** Read it **two independent ways** and require agreement:
(a) the ABUPS "End Uses" table via `TabularDataWithStrings`, District Heating column;
(b) a `DistrictHeating:Facility` (or equivalently named) row in `ReportData` **if one exists** — and
if none exists, say so explicitly rather than silently falling back to (a).
If (b) is unavailable, note in the report that the census rests on a **single** read path and add a
third check instead: the ABUPS **total** row must reconcile with the sum of its columns.

**How to test.** The five known-positives must return non-zero and the five known-negatives exactly
0.00. Re-derive the T01 experiment: on the scratch IDF where the orphan pair was deleted, the reader
must return **0.00 GJ**, and on the untouched one **0.72 GJ**, with Water Systems Natural Gas
**11.68 GJ unchanged in both**.

---

### T02 — Build the rebuild harness and run a stratified pilot of 200

**What.** Regenerate IDFs at HEAD for a **stratified sample of 200 buildings** — stratified by
archetype first (every archetype present in the fleet, `MidriseApartment` deliberately not
over-weighted) and by cell second — simulate them with `trim_outputs=False`, and read both the
district-heating term (T01's reader) and the full parser EUI.

**Why.** Three things have to be true before spending 119 CPU-hours, and none of them is known yet:
that a HEAD rebuild reproduces run 4's numbers, that the per-building rate matches F4, and that the
discriminator still holds outside the 60 buildings that established it.

**How.** Reuse `run_ep_isolated()` (`scripts/analysis/open35_storey_intervention_2026-08-19.py:95`) —
**note its relative-path trap is already in the debug reference, chapter 13; read that entry before
you start.** Write per-building rows to `open61_census_pilot.csv`.

**How to test — pre-registered controls, all four stated before the run:**
- **C1** — the rebuilt EUI reproduces the recorded `05_results.csv` EUI to machine precision on at
  least 190 of 200. *(This is the strong control: `manifest_row` supplies only the geometry inputs;
  the EUI itself is recomputed by `parse_building()` from the newly simulated `.sql`.)*
- **C2** — district heating is **non-zero on all 200**. F3 predicts this. **If any building returns
  0.00, the discriminator is broken and you stop at CP-2 rather than proceeding.**
- **C3** — the measured mean seconds/building is within 3× of F4's 52.5 s.
- **C4** — every archetype in the fleet appears at least once in the 200. Report the count.

**Then decide the host and say why:** at the measured rate, local at `n_jobs ≤ 10` versus Speed via
`sbatch --array`. State the projected wall-clock for each. **This is your decision to make and to
justify at CP-2; it is not pre-empted here.**

---

### T03 — Run the census over all 8,160 and harvest it

**What.** The same pipeline as T02, over the whole fleet. Output
`open61_census_fleet.csv`: one row per building — cell, osm_id, archetype, floor area,
district-heating kWh, recorded EUI, recorded `dhw_eui_kwh_m2`, and the ratio.

**Why.** This is the deliverable. Everything before it is instrumentation.

**How.** Whichever host T02 justified. **Fire-and-forget, then poll your own output file** — do not
wait to be woken (hard rule 2). Write rows incrementally so a partial run is still readable.

**How to test.** Row count **8,160**, no duplicate osm_id, and floor area summing to the fleet total
already recorded. Report failures as a count with their cell breakdown, and **do not silently drop
them** — a building that fails to simulate is a row with a null and a reason, not a missing row.

---

### T04 — Compute the fleet number, and say plainly how it compares to the estimate

**What.** From `open61_census_fleet.csv`, compute the unreported district-heating term as
**a pooled figure — total unreported energy ÷ total floor area** — over the 8,153-building population
the adopted figure uses, plus per-cell and per-archetype breakdowns.

**Why.** To replace F5's estimate with a measurement, and to record by how much the estimate was off.

**How.** Pooled, never a mean of per-cell means (§5 of the register: the headline is always the pooled
statistic, and per-cell results are never merged into one number). Report the per-cell figures **as
twelve numbers**, not as one.

**How to test — pre-registered:**
- **C5** — the measured fleet figure is compared against **8.7 / 17.2 / 20.2**. Whether it lands
  inside that band or outside it, **state which, and by how much.** Landing outside is a legitimate
  result and is not a reason to re-run anything.
- **C6** — re-derive the ratio statistics on 8,160 and compare to the 60-building IQR
  (**0.362–0.840**, median **0.714**). Report whether the small sample was representative.
- **C7** — the archetype concentration: report the `MidriseApartment` figure against the fleet
  figure, given they are **2,818 of 8,160**.

⚠️ **What you may not do in T04:** produce a corrected fleet EUI. The measurement tells us the size of
what is missing; **what the model *should* have done with that energy is a design question and is not
in this plan.** Write the number, name the design question, stop.

---

### T05 — Census the storey disagreement across the fleet (Arc B, no simulation)

**What.** For every building in the fleet, record three storey counts side by side: what the source
data says, what `auto` builds, and what `layout_assign` builds. Output
`open03_storey_census.csv`.

**Why.** F6: 28 of 48 sampled pairs disagree, and where they agree the envelope matches **exactly**.
That makes storey count — not wall construction — the live defect behind OPEN-03. Nobody has ever
counted it beyond 48 buildings.

**How.** From the IDFs and manifests. **No simulation is required and none should be run.** If a
storey count is only obtainable by parsing IDF geometry, reuse the vertex-parsing code — and read the
debug reference chapter 16 entry on the **object-boundary bug** and the **Attic-zone floor
double-count** first; both were registered on 2026-08-20 and both will bite you here.

**How to test — pre-registered:**
- **C8** — row count is **8,160** and the per-cell n sums to 8,160.
- **C9** — on the 48 buildings already in `open03_envelope_decomposition.csv`, the storey counts
  reproduce **exactly**. A mismatch means the census disagrees with the measurement that motivated it
  — stop and report, do not reconcile silently.
- **C10** — report the disagreement rate fleet-wide, the **direction** (which arm builds taller, and
  how often), and the breakdown by archetype and cell.
- **C11** — count `Zone.Multiplier` > 1 usage in both arms fleet-wide, extending F7's 2-of-48 vs
  0-of-48. This is the OPEN-60 link and it has never been counted at scale.

---

## 6b. ✅ CP-1 — AUDITED AND SIGNED, 2026-08-20

**T01 passes. Every claim below was re-derived by the director directly, not accepted on report.**

**D13 — the missing read path is genuinely missing, not merely unfound.** Director query on a known
positive: `select count(*) from ReportDataDictionary where Name like '%istrict%'` returns **0**. The
executor's path-(b) absence is confirmed independently and is exactly what **F1** predicts — the
parser asks for ten meters by name and EnergyPlus was never asked for a district-heating meter either.
⚠️ **The census therefore rests on ONE read path.** That is a real risk and is recorded as one.

**D14 — the risk is smaller than it looks, because ABUPS carries its own second opinion, and the
executor did not report this.** Director-derived on both positives: the District Heating column is
non-zero on **exactly two rows, and they are equal** —
`way_1008727470`: Water Systems **0.72**, Total End Uses **0.72**;
`way_425993511`: Water Systems **576.02**, Total End Uses **576.02**; a negative (`way_328529693`)
has **no** non-zero row at all. **The entire district-heating total is the service-hot-water row and
nothing else.** This is a free within-table cross-check *and* it is the mechanism itself, visible in
the output: the orphan `DHW_WaterUse_*` load, and only that load, lands in the district column.

**➕ NEW CONTROL for T02/T03, added at CP-1 — C2b.** For every building in the pilot and the census,
assert **District-Heating "Water Systems" == District-Heating "Total End Uses"**. If any building
shows a non-zero district term on any *other* end-use row, the mechanism is not what D14 says and the
building must be reported individually, not aggregated. This costs nothing — the reader already
loads the column.

**Verification, re-counted by the director from
`openubem/outputs/comparisons/open61_census_read_verification.csv`:** 108 rows (48 + 60),
`agree` **True on 108/108**, `reader_b_gj` **empty on 108/108** (consistent with D13),
`a_reconciles_with_own_sum` **True on 108/108**, non-zero recorded **65** (5 from the 48-sample +
60 from production), and **0 rows** differ from the recorded value by more than 0.005 GJ.

**Control 4 passed on the original artifact, not a rebuild** — `scratchpad/open61_c2_experiment/`
baseline **0.72 GJ**, treated **0.00 GJ**, Water Systems Natural Gas **11.68 GJ unchanged in both**.
The mechanism experiment stands.

🔴 **D15 — the recorded "16,336 production IDFs" is a COUNT ERROR, and the director found it while
scoping T05.** A recursive `**` glob over `evidence/open48_refleet4/` returns ~490 paths for a
directory holding **245** real files, roughly doubling every count taken that way. Globbing the twelve
`<cell>/fleet_staging/idfs/` directories **directly** gives **8,160 IDFs — one per building**, which is
the fleet.

**The conclusion of D9 is untouched; only its denominator was wrong.** Director re-ran the
discriminator over all 8,160 directly: **8,160 contain a `DHW_WaterUse_*` object, 0 contain a
`PlantLoop`.** That is **100.00 %**, exactly as D9 claimed — measured now against the right
denominator. **Cite 8,160, never 16,336.**

⚠️ **The lesson generalises past this number.** This is the fourth arithmetic slip this arc has caught
in a figure that had already been written down and quoted, and it is the same shape as the others: a
plausible number nobody re-derived. The register's standing suggestion — a reconciliation check
*inside* `parse_building()` rather than in whichever task happens to look — would not have caught this
one, because this one is in a **script's own glob**, not in the parser. **Any count that will be
published gets re-derived a second way before it is written down.**

**Scope discipline:** no simulation was run, no production code touched, one script and one CSV
written where the plan said they would be. No error was hit, so no debug-reference entry was owed.

✅ **T02 is authorised to proceed.** It remains gated: **the 119 CPU-hours of T03 are not spent
until CP-2 is signed.**

---

## 6c. ✅ CP-4 — AUDITED AND SIGNED, 2026-08-20 (Arc B closes)

**T05 passes. Every control below was re-derived by the director directly against
`open03_storey_census.csv`, not accepted on the executor's report.** The executor took Route 1
(derivation, no build) — justified, because `match_storeys()` only ever writes `Zone.Multiplier` and
`scale_baseline_idf()` scales X/Y with Z untouched, so the `layout_assign` arm's *geometric* storey
count cannot vary per building within an archetype. That justification is sound and the census
confirms it empirically (see **D17**).

| Control | Verdict | Director's own re-derivation |
|---|---|---|
| **C8** | ✅ | 8,160 rows, 12 cells, per-cell n sums to 8,160. |
| **C9** | ✅ | **96/96 exact, 0 mismatches** — 48 buildings × 2 arms against `open03_envelope_decomposition.csv`. Keys need normalising (`way/NNN` in the census vs `way_NNN` in the envelope CSV); a naive join returns 96 *missing*, not 96 matches, and would read as a pass to nobody but looks like a crash. |
| **C10** | ✅ | 4,914/8,160 = **60.2 %** disagree; **95.2 %** of disagreements are `layout_assign` **shorter**; mean −3.07, median −2, range −104…+5. |
| **C11** | ✅ | `auto` **0**/8,160, `layout_assign` **434**/8,160 (5.3 %). Consistent with F7's 0-of-48 vs 2-of-48 (4.2 %) — the direction holds and the rate scales. |

**F6 reproduces exactly.** Restricted to the same 48 buildings, the fleet census returns **28
disagreements of 48** — the predecessor's number to the unit. The census is measuring the same thing
at 170× the scale.

---

### D16 — the executor's `Z_Origin` parsing gap is real, correctly registered, and does **not** drive the headline

The wall-min-Z storey-count method never adds a zone's own `Z_Origin` under Relative coordinates, so
it under-reads for 6 archetypes (**2,983 buildings, 36.6 % of the fleet**). The executor found this
while validating, did **not** silently fix it (fixing it would have changed what C9 must reproduce),
registered it `[OPEN]` in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16, and flagged it
per row as `layout_assign_z_origin_collapse_risk`. That is the correct handling of a mid-task
discovery and it is recorded here as such.

✅ **Director's check that it does not contaminate C10:** splitting the fleet on the flag gives
**60.8 %** disagreement on the 5,177 clean rows and **59.2 %** on the 2,983 at-risk rows. The
headline is **not** an artifact of the parsing gap — it survives excluding every affected building.
What the gap does bound is the *per-archetype magnitude* for those 6, not the fleet-wide rate.

---

### D17 — director's own finding: `layout_assign_storey_count` is a **per-archetype constant**, and that sharpens what OPEN-03 actually is

Not in the executor's report; derived by the director from the CSV. For **18 of the 20 archetypes the
column takes exactly one value across every building of that archetype** — `SmallOffice` = 1 against
12 distinct `auto` values, `MidriseApartment` = 1 against 9, `TallBuilding` = 1 against 19,
`LargeOffice` = 4 against 20. Only `OpenUBEMUnknown` and `Courthouse` vary, and those are exactly the
two no-baseline archetypes (650 + 68 = **718** = the `no_baseline_fallback_auto` count) where the
value is copied from `auto`.

🔴 **So "60.2 % disagree" is not "the two arms build different storey counts for the same
building" — it is "the real building's storey count differs from its prototype's."** Stated that way
the number is close to expected-by-construction and is the weaker of the two available readings.
**The stronger reading, which is the one that answers OPEN-03, is the match-status breakdown:**

| Does `layout_assign` represent the building's real storey count? | n | share |
|---|---|---|
| `no_baseline_fallback_auto` — inherits `auto`, so yes | 718 | |
| `identity` — n_real == n_proto, so yes | 1,226 | |
| `applied` — matched via `Zone.Multiplier` | 502 | |
| **✅ TOTAL MATCHED** | **2,446** | **30.0 %** |
| `fallback_shorter` — keeps the prototype | 3,707 | |
| `fallback_not_expressible` — keeps the prototype | 2,007 | |
| **❌ TOTAL UNMATCHED** | **5,714** | **70.0 %** |

For those **5,714 buildings the arm builds the prototype's storeys regardless of the real building**:
their true storey counts average **3.12** and reach **105**, and they are rendered with an average of
**1.21** geometric storeys, never more than **6**. That is the defect, in one line, and it is worse
than "60 % disagree" makes it sound.

⚠️ **Do not quote the two numbers as if they measured the same thing.** 60.2 % is a disagreement
rate between a per-building count and a per-archetype constant. **30.0 % / 70.0 % is the coverage
statement**, and it is the one to carry forward.

---

### D18 — the `auto` arm reproduces the source storey count 8,153 times in 8,160

**99.9 %.** The 7 exceptions all have a stated `levels` of **1** while `auto` builds 3, 6 or 19:
five `Warehouse` in `la_rural`, one `Warehouse` in `la_urban`, one `LargeHotel` in `nyc_centre`
(stated 1 storey, built 19). The shape points at an OSM `building:levels` data gap rather than a
builder defect, but it has not been run down and is **not** load-bearing for anything here.

~~⚠️ **An arithmetic coincidence that must not be mistaken for a fact:** 8,160 − 7 = **8,153**, which
is also the denominator of the adopted **153.8231 kWh/m² pooled over 8,153**. **These are almost
certainly not the same seven buildings** — the baseline's exclusions are simulation-status
exclusions, not storey-parse exclusions. Nobody has checked. **Do not cite the two 8,153s as
related until someone has intersected the two lists.**~~

🔴 **CORRECTED the same day — the director intersected the two lists rather than leaving the
caution standing, and the guess above was WRONG. They are the SAME SEVEN BUILDINGS, exactly.**
Reading `simulation_status` from all twelve `evidence/open48_refleet4/<cell>/results/05_results.csv`
gives **7 non-success rows, every one of them `not_simulated`** — `la_rural/way_472960972`,
`way_472961034`, `way_472961088`, `way_472961091`, `way_472961171`, `la_urban/way_402215469` (all
`Warehouse`) and `nyc_centre/way_266034056` (`LargeHotel`). **Intersection with the 7 storey-mismatch
buildings: 7 of 7.**

✅ **So 8,153 is not an arbitrary denominator, and the two facts are one fact.** The buildings the
adopted fleet figure drops are precisely the buildings whose storey count the builder could not
reproduce from source — each states `levels = 1` and each was built at 3, 6 or 19 storeys. The storey
mismatch and the simulation failure are the same event, not two coincidental sevens. **This is a lead,
not a defect** — nobody has traced why `not_simulated` and the storey over-read travel together, and
this plan does not. ⚠️ **Method note worth keeping:** the caution was right to demand the check and
wrong in its guess. **One command settled it. Run the check instead of publishing the hedge.**

---

### CP-4 ruling on new item IDs — **proposed to the user, none opened**

The executor proposed two candidates and correctly opened neither. The director's recommendation:

1. **The storey-coverage finding does NOT need a new ID — it belongs to OPEN-03.** OPEN-03 exists to
   hold exactly this; D17 gives it its number (**70.0 % unmatched**) and its severity, which is what
   the item was missing. Opening a second ID would split one defect across two rows.
2. **The `Z_Origin` parsing gap DOES warrant one** — it is a distinct defect, in a different place
   (a measurement method, not the builder), with a different fix and a different owner. It is
   currently tracked only as an `[OPEN]` bullet in the debug reference, which is not a register.
   **Recommended: grant one ID, `OPEN-62`, for the `Z_Origin` under-read.**

🟡 **Neither is opened. A new ID is the user's to grant.**

✅ **Arc B is complete. T05 is signed off. Nothing in Arc B is blocked on Arc A.**

---

## 6d. ✅ CP-2 — AUDITED AND SIGNED, 2026-08-20 (T02 passes, T03 authorised)

**T02 passes on all five controls. Every number below was re-derived by the director directly from
`openubem/outputs/comparisons/open61_census_pilot.csv` (200 rows, 200 unique `osm_id`,
`status=ok` on 200/200), not accepted on the executor's report.**

| Control | Threshold stated before the run | Measured | Verdict |
|---|---|---|---|
| **C1** | rebuilt EUI reproduces `05_results.csv` on ≥ 190/200 | **200/200** within the harness tolerance (0.01 kWh/m², `open61_census_build_2026-08-20.py:106`); largest absolute difference anywhere **1.49 × 10⁻⁴ kWh/m²**; only **3 rows** differ by more than 10⁻⁶ | ✅ pass, with margin |
| **C2** | district heating non-zero on all 200 | **200/200 non-zero**; min **0.09 GJ**, max **19,234 GJ** | ✅ pass |
| **C2b** | District-Heating "Water Systems" == "Total End Uses" on every building | **200/200**; largest `dh_other_rows_sum_gj` in the whole pilot is **0.000000 GJ** | ✅ pass — D14's mechanism holds outside the two buildings that suggested it |
| **C3** | mean s/building within 3× of F4's 52.5 s (band 17.5–157.5) | **mean 47.70 s**, median 10.65 s, p90 81.10 s, max 1,471.3 s | ✅ pass |
| **C4** | every fleet archetype appears at least once | **20 of 20** | ✅ pass |

`dh_a_reconciles` is **True on 200/200** and `dh_b_available` is **False on 200/200** — the second
read path is still absent everywhere, exactly as **D13** said. The census still rests on one read
path; that risk is unchanged, and it is not new information.

### D19 — the cost of T03, measured two ways, and a director estimate withdrawn

The naive projection (pilot mean × 8,153) gives **108 CPU-hours**. It is the wrong arithmetic: the
pilot is stratified, so rare heavy archetypes are over-represented relative to the fleet. Weighting
each archetype's measured mean by its **fleet** count gives the honest figure:

**97.2 CPU-hours**, ≈ **8.1 h wall at 12 concurrent workers**.

The cost is dominated by a heavy tail, not by the median building: `MidriseApartment` (21.3 CPU-h)
and `SmallOffice` (14.8) lead on count, but `LargeOffice` (13.8), `LargeHotel` (13.5),
`MediumOffice` (10.1), `TallBuilding` (8.4) and `SuperTallBuilding` (6.1) together account for
**52 CPU-hours from 797 buildings** — 9.8 % of the fleet buying 53 % of the compute. ⚠️ Three of
those projections rest on **a single sampled building** (`LargeHotel` n=1 at 1,471 s,
`SuperTallBuilding` n=1 at 910 s, `HighriseApartment` n=1 at 345 s), so ±30 % on the total is the
right confidence, not ±5 %.

🔴 **A director estimate is withdrawn.** Between CP-1 and CP-2 the director projected **33.1
CPU-hours** from the 109-building read-verification timings. That was wrong by a factor of three,
and wrong for a knowable reason: the read-verification sample was drawn from buildings that had
already been read cheaply, and contained none of the heavy tail. **F4's original 119 CPU-hours,
taken from run 4's own `.end` files, was the better estimate all along** — measured 97.2 sits within
19 % of it and nowhere near 33. The lesson is the same one CP-1 recorded under D15: an estimate
drawn from a convenient sample is not a measurement, and the director is not exempt from that rule.

### Host decision — **local, 12 workers**, and why not Speed

At 97 CPU-hours the two hosts are ~8 h wall locally against ~1–2 h on Speed. Speed is **not** worth
it here, and the reason is not the compute:

- The harness reproduces run 4 to 10⁻⁴ **at HEAD on this machine** (C1, 200/200). None of that
  evidence transfers to a cluster port.
- A Speed run needs the fleet's IDF generation stage, an EnergyPlus module, a staging copy of twelve
  cells' inputs and a harvest step — four new failure surfaces, each historically worth days, to save
  six hours of unattended wall-clock.
- T03 is fire-and-forget either way, and nothing downstream is waiting on it tonight.

**Deviation recorded:** the plan framed local as `n_jobs ≤ 10`. This host has **20 cores**; 12
workers leaves 8 free for interactive use and takes the projection from 9.7 h to 8.1 h. Recorded
here rather than taken silently.

### Three further deviations, recorded before T03 runs

1. **Output filename.** The harness hardcodes `PILOT_CSV` and exposes no `--out`. Rather than edit a
   script whose outputs have just been audited, T03 runs through a scratchpad driver
   (`t03_fleet.py`) that imports the harness and repoints `PILOT_CSV` / `SELECTION_CSV` / `WORK`.
   **Zero change to the audited harness**, and `open61_census_pilot.csv` — CP-2's evidence — is left
   untouched on disk.
2. **Population is 8,153, not 8,160.** `load_population()` keeps `simulation_status == "success"`.
   The 7 excluded buildings are exactly the seven **D18** identified: six `Warehouse` and one
   `LargeHotel`, all `not_simulated`, none of which has a `.sql` to read. T03's deliverable therefore
   carries **8,153 measured rows plus 7 rows carrying `not_simulated` as the reason** — a reason, not
   a silent gap, as the task requires.
3. **Work directories are deleted per building on success.** The pilot's work tree is **5.1 GB for
   200 buildings**; unchanged, the fleet run would need **≈208 GB** against **517 GB free**. The
   driver removes each `status=ok` work directory after its row is written and **keeps** the
   directory of any building that fails, so failures stay diagnosable.

### One reading that is NOT a result — stated so it is not quoted later

The pilot's pooled district-heating figure is **23.87 kWh/m²**, and its ratio statistics are
**median 0.644, IQR 0.310–0.935** against the 60-building **median 0.714, IQR 0.362–0.840**.
⚠️ **Neither is a fleet number and neither may be cited as one.** The pilot is stratified by
archetype, not proportional to the fleet, so it over-weights exactly the large buildings that carry
the most service hot water. The comparison against **8.7 / 17.2 / 20.2** is C5's job in T04, on the
proportional census, and nowhere else.

✅ **T03 is authorised.** Launched local, 12 workers, fire-and-forget, output
`openubem/outputs/comparisons/open61_census_fleet.csv`.

---

## 6e. ✅ CP-3 — AUDITED AND SIGNED, 2026-08-20

**The question:** *does the measured fleet number stand, and how far off was the estimate?*

**It stands.** The headline was re-derived by the director directly from
`open61_census_fleet.csv`, not taken from the executor: **19.470690 kWh/m² over n = 8,144**, matching
the executor's 19.4707 to every digit reported. The population reconciles to 8,160 with every excluded
building carrying a named reason. The sensitivity test (H) shows it is independent of the floor-area
column, and the two known anomalies cannot move it past the third decimal.

**How far off was the estimate — the honest answer is "further than C5 suggests."** Against the
literal published band the measurement is inside it, 3.6 % under the ceiling. But F5's *method*,
re-run against the fleet's own measured DHW base, tops out at 17.43 kWh/m² — the measurement is
**11.7 % above what that method could have produced at any point in its IQR**. The sampling was fine
(C6, corrected: the 60-building ratio distribution matches the fleet's). The error was applying a
per-building median ratio to a pooled quantity, which understates by the 44 % median-to-pooled gap.

**One executor finding was overturned, not accepted.** C6 was answered with the wrong denominator and
returned the opposite verdict, together with a false claim that the denominator matched the pilot's.
The director re-derived it, rewrote the report section and patched the script. Recorded here because
the plan's audit rule requires a DESIGN/plan citation for any unplanned decision, and because "the
60-building sample was unrepresentative" would have entered the register as a fact had it not been
checked.

**What is NOT ruled here.** No corrected fleet EUI, and no change to the adopted **153.8 kWh/m²**.
The census measures the size of what is missing; whether and how 470.8 GWh should enter the reported
total is a design question, and §C6b's concentration result means it cannot be answered by adding a
flat offset. **Carried to the user, not decided.**

---

## 7. Stop-and-report points

| | After | What the director rules on |
|---|---|---|
| **CP-1** | T01 | Is the read path sound, and is it proven twice or once? **Nothing is simulated before this is signed.** |
| **CP-2** | T02 | Do C1–C4 pass? Is the host choice justified by the measured rate? **119 CPU-hours are not spent before this is signed.** |
| **CP-3** | T04 | Does the measured fleet number stand, and how far off was the estimate? |
| **CP-4** | T05 | Does the storey census stand, and does it warrant its own item ID? *(A new ID is the user's to grant — propose, never open.)* |

---

## 8. Progress log

*(one entry per completed task, appended by the executor at end of file, in the house format:)*

```
#### TXX — <title> — completed YYYY-MM-DD
**Artifacts:** …
**Deviations:** …
**Test status:** …
**Notes:** …
```

*(no entries yet — this plan has not been started)*

#### T01 — Establish how the district-heating term is read from a `.sql`, and prove the read twice — completed 2026-08-20
**Artifacts:**
- `scripts/analysis/open61_census_read_2026-08-20.py` — `read_district_heating(sql_path)`, reads
  ABUPS "End Uses" / District Heating / "Total End Uses" via `TabularDataWithStrings`.
- `openubem/outputs/comparisons/open61_census_read_verification.csv` — 108 rows (48-sample +
  60-sample), recorded vs reader value per building, agreement flag.
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_fleet-census.md` — T01 section.

**Deviations:** Path (b) (`DistrictHeating:Facility` or equivalent row in `ReportData`) does not
exist anywhere in this fleet's `.sql` files — `ReportDataDictionary` has no meter/variable whose
name contains "District", confirmed on all 108 buildings tested and consistent with F1
(`METER_QUERY` requests ten meters, none of them district heating). Per the plan's own T01 "How"
fallback, substituted the third check: ABUPS `Total End Uses` reconciles with the sum of its own
14 per-end-use rows for the District Heating column. This reconciled on 108/108 rows. **The
census therefore stands on one proven read path, not two — reported explicitly, not silently.**

**Test status:**
- 5 known-positives: **5/5** non-zero, match recorded `dh_total_gj` to 2 decimals.
- 43 known-negatives (48-sample): **43/43** read exactly 0.00.
- Full 48-row sample vs its own `dh_total_gj`: **48/48**.
- 60-row production sample vs its own `dh_total_gj`: **60/60**.
- T01 experiment control, re-derived on `scratchpad/open61_c2_experiment/{baseline,treated}/out/eplusout.sql`
  (found, not rebuilt): baseline **0.72 GJ**, treated **0.00 GJ**, Water Systems Natural Gas
  **11.68 GJ unchanged in both**. PASS.

**Notes:** No error was hit during T01 (reader matched on first run against all 108 rows plus
both controls), so no new entry was added to `OpenUBEM_debug_References.md` — nothing to
register. No simulation was run; this task read only pre-existing `.sql` files.

#### T03 — Run the census over all 8,160 and harvest it — completed 2026-08-20

**Artifacts:**
- `openubem/outputs/comparisons/open61_census_fleet.csv` — **8,160 rows, 8,160 unique `osm_id`, 41
  columns.** One row per fleet building, no building missing, every non-`ok` row carrying a reason.
- Census work tree (`.sql` corpus): `<scratchpad>/open61_census_fleet_work/<cell>/<stem>/sim_out/eplusout.sql`
  — **7,861 directories**, preserved under ruling R6 and still to be moved by
  `PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` T07.
- Backups kept: `open61_census_fleet.pre-retry.csv`, `open61_census_fleet.csv.pre-statusfix`.

**Note on T02's record:** T02's pilot was audited and signed in **§6d (CP-2)** of this plan, which
carries its numbers and its three deviations. No separate `#### T02` progress-log entry was written.
Recorded here so the gap is not read later as an unexecuted task.

**Outcome, by status (all 8,160):**

| status | n | meaning |
|---|---|---|
| `ok` | **8,152** | simulated and harvested |
| `not_simulated_upstream_excluded_from_census_population` | **7** | never simulated upstream; appended as reason-rows, not re-run |
| `failed_energyplus_oom_crash_no_fatal_no_end` | **1** | `nyc_centre way/266170763`, 43-storey LargeHotel |

Per-cell n sums to 8,160 across all 12 cells (nyc_urban 1,779 · nyc_suburban 1,589 · la_suburban
1,343 · nyc_centre 738 · la_urban 618 · austin_suburban 437 · austin_urban 425 · austin_centre 413 ·
austin_rural 245 · la_centre 226 · nyc_rural 198 · la_rural 149).

**Of the 8,152 `ok` rows:** `parsed_parse_status` = success **8,146** / `failed_zone_mismatch` **6**
(all `nyc_centre`, five of them `LargeHotel`; same signature as OPEN-53, but here in a *local*
rebuild, which is the point). `dh_b_available` is **False on all 8,152** — route B is never
available, so the census stands entirely on route A, exactly as T01 predicted.
`dh_a_reconciles` **True on 8,144**, blank on 8. `c2b_pass` True 8,144 / False 8.

**The number T04 must pool over is 8,144, not 8,152.** Eight `ok` rows have a null `dh_total_kwh`:
the six `failed_zone_mismatch` rows, plus **two rows that parsed successfully and still produced no
DH term** — `la_rural way/472961047` (Warehouse) and `la_centre way/319507579` (SecondarySchool).
Those two are not explained by the parse failure and are handed to T04 as a named question, not a fix.

**`c1_pass` False on 9 of 8,152**: the six `failed_zone_mismatch` rows (no diff computable), plus
`la_rural way/472961092` (+2.93 kWh/m²), `la_rural way/472961047` (−9.71), and
`la_centre way/319507579` (**−116.59**). The last is large enough that T04 must name it rather than
average over it.

**Deviations — five, all disclosed:**
1. **Killed and resumed.** The first census leg was stopped mid-flight and restarted against the
   partial CSV rather than from zero. The resume keys on `osm_id`, so no building was simulated twice
   into two rows — but the wall-clock figures below are per-leg, not one continuous run.
2. **Thread pool → process pool.** The original driver used a thread pool; it was replaced with
   `<scratchpad>/t03_fleet_mp.py`, a process-pool driver, after the thread arm proved to share a
   process cwd between workers (the same defect recorded against OPEN-58 defect (a)).
3. **Three collision rows stripped.** Three rows written by the thread arm under the shared-cwd
   defect were removed from the CSV before the resume, because their `sim_out` could not be attributed
   to the building named in the row. All three were re-simulated cleanly by the process arm.
4. **Four smoke rows merged.** Four rows produced by the earlier smoke test were merged in rather
   than re-run, after checking `osm_id`, archetype and column set matched `ROW_FIELDS` exactly.
5. **Two solo retries.** The final two buildings (a LargeOffice and a LargeHotel, both `nyc_centre`)
   were re-launched alone with `--workers 2` because they had been the two survivors of the main leg.
   One completed; the other is the OOM row above.

**Wall clock:** final process-pool leg **9,687 s**; solo retry leg **1,868.8 s**. Host: local, 12
workers, per the CP-2 host decision — not Speed.

**Test status (plan-specified):**
- **"8,160 rows, one per building, a failure is a row with a null and a reason"** — PASS. 8,160 rows,
  8,160 unique `osm_id`, 0 missing buildings, 0 reasonless nulls.
- **Corpus preserved for R6** — PASS in kind, not in count. 7,861 `.sql` directories exist against
  8,152 `ok` rows. The gap is 291 buildings whose `sim_out` was reclaimed during the kill-and-resume.
  **R6 must therefore record 7,861 / 96.4%, not 100%** — stated here so T07 cannot inherit a wrong number.

**Notes:** The OOM row was diagnosed before being written off, not assumed: its `.err` shows **0
Severe / 0 Fatal** and ends mid-line inside a `SizeWaterCoil:` warning, there is no `.end` file, the
`.eso` reached 318 MB and the `.sql` 305 MB, and the `.sql` opens with 36 tables but **no
`TabularDataWithStrings`** — so nothing could be rescued from disk and a re-run would only repeat the
crash. This is the same silent `std::bad_alloc` signature already recorded for an 89-storey building,
at a different phase; the existing debug-reference entry (§1) was **extended** rather than duplicated,
per the house rule, and now carries the `TabularDataWithStrings` test that separates an OOM crash from
a controlled fatal. The row's `status` cell had been written by the driver as a truncated 200-character
`exception:Command '[...` string; it was replaced with the single token
`failed_energyplus_oom_crash_no_fatal_no_end` so the reason is legible in the CSV itself, with the
pre-edit file kept as `.pre-statusfix`.

#### T04 — Compute the fleet number, and say plainly how it compares to the estimate — completed 2026-08-20

**Artifacts:**
- `scripts/analysis/open61_fleet_dh_number_2026-08-20.py`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_fleet-dh-number.md`

**THE NUMBER — pooled, n = 8,144:**

> **19.4707 kWh/m²** of district heating is present in the simulations and absent from the reported
> total. `Σ dh_total_kwh = 470,831,194.4 kWh ÷ Σ parsed_floor_area_m2 = 24,181,536.0 m².`

Independently re-derived by the director from the CSV, to 6 decimal places: **19.470690**. The
population is 8,144, exactly the figure T03 pre-committed — 8,160 rows, less 8 non-`ok`, less 8 `ok`
rows with a null DH term.

Reported alongside and explicitly **not** the headline: mean and median of the per-building ratio.
Per-cell reported as **twelve numbers**, never averaged; per-archetype as a full table.

**Test status:**
- **C5 — PASS, inside the band.** 19.47 against 8.7 / 17.2 / 20.2: **3.6 % below the ceiling**,
  13.2 % above the midpoint, 123.8 % above the floor. See the director's note below on what "inside
  the band" is actually worth.
- **C6 — 🔴 EXECUTOR WRONG, CORRECTED BY THE DIRECTOR; the verdict reverses.** The executor computed
  DH ÷ *total site energy* and returned **NOT REPRESENTATIVE** (fleet median 0.0133 vs pilot 0.714,
  "roughly 50× smaller"), asserting that its denominator "is the same construction used for the
  pilot's C6 statistic". That assertion is false: fact F5 (`§5`, line 101) defines the ratio as
  **dh ÷ dhw_eui**. Re-derived on the correct denominator, n = 8,144: fleet median **0.6503**, IQR
  **0.3117–0.8642**, against the 60-building pilot's 0.714 / 0.362–0.840 and the 200-building pilot's
  0.644 / 0.310–0.935. **The small sample was representative** — the 60-building median is ~10 % high,
  which for 60 of 8,160 is a good result. Both the report §C6 and the script's C6 block were rewritten;
  the script's own verdict now prints REPRESENTATIVE.
- **C7 — measured.** `MidriseApartment`, n = 2,818 (34.6 % of the population, the largest archetype):
  **31.76 kWh/m²** against the fleet's 19.47 — **63 % above** the fleet figure, yet only **14.9 %** of
  the fleet's total DH energy.
- **H (sensitivity) — PASS.** Swapping `parsed_floor_area_m2` for `recorded_floor_area_m2` (present on
  all 8,144) moves the headline by **+0.000135 kWh/m² (+0.0007 %)**. The number does not depend on
  which floor-area column is used.
- **I (T03's two anomalies) — immaterial.** Imputing `la_rural way/472961047` and
  `la_centre way/319507579` at their own archetypes' pooled rates moves the headline by −0.0013 and
  −0.0009 kWh/m². Neither is worth re-simulating for this number.

**Deviations:** The plan's §T04 prohibition was honoured — no corrected fleet EUI was produced, and the
report closes by naming the design question rather than answering it. Two director additions beyond the
executor's brief are marked as such in the report: the C6 correction above, and a new **§C6b** on
concentration.

**Notes — two things the plan did not ask for and that change how the number should be read:**

1. **The estimator was biased low by construction, and C5's "inside the band" hides it.** The
   per-building *median* ratio is 0.6503 but the *pooled* ratio (Σ dh ÷ Σ dhw) is **0.9382 — 44 %
   higher**, because large buildings carry a far higher DH-to-DHW ratio than the median building.
   Applying a median per-building ratio to a pooled quantity therefore understates the answer.
   Reconstructing F5's own arithmetic against the fleet's measured pooled DHW of 20.75 kWh/m² gives
   7.51 / 14.82 / **17.43** kWh/m² — so the measurement lands **above F5's reconstructed ceiling**.
   F5's published 20.2 ceiling contains the answer only because its DHW base differed from the fleet's.
   The sampling was sound; the median-ratio-applied-pooled step was not. **This, not C5, is the real
   verdict on the estimate.**
2. **The term is not a fleet-wide offset.** `SuperTallBuilding` (n=24) and `TallBuilding` (n=92) —
   **116 buildings, 1.4 % of the population — carry 70.5 % of the fleet's district heating**; four
   archetypes carry 91.8 %. Everything office-, retail- or shop-like sits at 1.3–2.7 kWh/m², i.e. near
   zero. The DH term is a **tall-residential phenomenon**. Any decision taken on 19.47 is really a
   decision about ~3,000 residential buildings, and applying it as a flat fleet offset would move
   energy onto ~5,000 buildings that do not have it.

---

#### T05 — Census the storey disagreement across the fleet (Arc B, no simulation) — completed 2026-08-20
**Artifacts:**
- `scripts/analysis/open03_storey_census_2026-08-20.py` — full derivation + census + C8-C11.
- `openubem/outputs/comparisons/open03_storey_census.csv` — 8,160 rows, one per building.
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_storey-census.md` — full report.
- New `[OPEN]` entry appended to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16.

**Route taken (director's first-decision instruction, §T05):** Route 1 — derived without building
any IDF, not Route 2. `layout_assign`'s geometry-measured storey count is a pure function of
archetype (verified: `match_storeys()`, `openubem/geometry/layout_assigner.py:539-653`, only ever
writes `Zone.Multiplier`, confirmed the *only* such write anywhere in `openubem/geometry/*.py` /
`openubem/idf/*.py`; `scale_baseline_idf` scales X/Y only, Z unchanged), so it was looked up once per
archetype from the archetype's own baseline IDF (18 baseline-mapped archetypes) instead of generated
per building. For the 2 non-mapped archetypes (`Courthouse`, `OpenUBEMUnknown`), `layout_assign`
falls back to the exact `auto` pipeline on identical inputs (`openubem/idf/builder.py:468-475`) —
verified byte-equal on the 48-sample's 5 rows of those archetypes — so their `layout_assign` value is
just that building's own `auto` value. Zero simulations run; zero per-building `layout_assign` IDFs
generated. Total wall-clock for the whole derivation (18 baseline loads/saves + 8,160-file auto-arm
parse + assembly): **under 2 minutes.**

**Deviations:** None from the plan's task spec. One extra column beyond the plan's minimum ask was
added (`layout_assign_z_origin_collapse_risk`) to carry the caveat found in Notes below without
altering any of the plan-specified columns or values — judged necessary for C10's own "report the
number measured" obligation, not scope creep.

**Test status (pre-registered controls):**
- **C8** — PASS. 8,160 rows; per-cell n sums to 8,160.
- **C9** — PASS. 48/48 sample rows matched; 0 mismatches on `auto`, 0 mismatches on
  `layout_assign` (exact reproduction of `open03_envelope_decomposition.csv`).
- **C10** — measured. Fleet-wide disagreement **4,914/8,160 = 60.2%**. Direction: `auto` taller in
  57.3% of the fleet vs `layout_assign` taller in 2.9% (mean signed diff `layout_assign − auto` =
  **−1.85 storeys**). Full per-archetype and per-cell breakdown in the MEASUREMENT report §3.
- **C11** — measured. `auto`: **0/8,160** (structural — `Zone.Multiplier` is never written outside
  `layout_assigner.py`; also exact match to F7's 0/48). `layout_assign`: **434/8,160** (5.3%,
  computed via the production `match_storeys()` function itself, not a blind grep — a blind grep of
  the 48-sample found 6/48 because it also catches native, pre-existing prototype `Zone.Multiplier`
  values unrelated to storey-matching; using `match_storeys()`'s own return value reproduces F7's
  2/48 exactly).

**Notes:** A previously-unregistered parsing gap was found while validating the per-archetype lookup
values, NOT while reproducing C9 (C9 passed cleanly because both this census and the 48-sample use
the identical, equally-flawed method). The predecessor's wall-min-Z storey-count definition never
adds a zone's own `Z_Origin` when `GlobalGeometryRules` `Coordinate System == Relative`; measured
zone-by-zone against all 18 baseline files (not assumed), this is **severe** in `MidriseApartment`,
`HighriseApartment`, `TallBuilding`, `SuperTallBuilding`, `Outpatient`, `SecondarySchool` (2,983/8,160
buildings, 36.6% of the fleet — including the fleet's single largest archetype), **immaterial** in
`LargeOffice`/`QuickServiceRestaurant`/`FullServiceRestaurant`, and **absent** in the remaining 10
mapped archetypes. Registered `[OPEN]` in the debug reference (§16) per hard rule; NOT fixed here,
since fixing it would silently change what C9 must reproduce. Flagged per-row in the output CSV
(`layout_assign_z_origin_collapse_risk`) and quantified in the report §4. Restricting the headline
disagreement rate to the 10 unaffected archetypes gives 60.8% — nearly identical to the unrestricted
60.2% — so the broad finding (majority disagreement, `auto` almost always taller) is not an artifact
of this gap; only the 6 flagged archetypes' individual magnitudes are. Two candidate new item IDs are
proposed to the director in the report §6 (the storey disagreement itself; the parsing gap) — neither
opened here, per the plan's instruction that a new ID is the director's/user's to grant.
