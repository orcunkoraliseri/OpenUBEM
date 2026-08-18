# INVESTIGATION — Register of everything open in OpenUBEM

> **Slug:** `open-items-register` · **Opened:** 2026-08-04 · **Author:** manager session
> **Status:** INVESTIGATION document. This is a **register and a diagnosis**, not a plan.
> **Successor:** execution plans (`PLAN_*.md`) are written *after* this document, one per item or
> per bundle the user selects. Nothing here is scheduled, scoped, costed, or approved.

---

## 0. What this document is, and what it is not

**Amended 2026-08-04:** OPEN-23 (`layoutGenerator`) **excluded by the user** — not an option being
continued. Recorded in §7.0, ID retired.

**Amended 2026-08-05:** OPEN-28 added (see §2). OPEN-21 (mixed-use classification key) **deferred by
the user** to `docs/docs_TODO/mixed_use_classification.md` — one function per building stands, the
question is closed to further asking, ID retired. Recorded in §6. **OPEN-05 CLOSED** — full defect-ID
sweep made, no further duplicates, ID retired (§3). **OPEN-29 added** — the same sweep exposed that
defects can be OPEN at their defining line yet absent from this register (§3). **OPEN-22's stated
premise verified FALSE at HEAD** and the item rewritten (§6). **26 items remain.**

**Amended 2026-08-05 (measurement pass, second amendment today):** the five Phase-1 measurements
M01–M05 (`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-0*.md`) re-verified OPEN-01, OPEN-02,
OPEN-03, OPEN-04, OPEN-08 and OPEN-28 — evidence marks upgraded in §1 and on each item's own heading.
**OPEN-01**'s inferred factor table is superseded by direct measurement of all 28 archetypes (kept,
marked, not deleted). **OPEN-03**'s line-179 "documented in results §7" claim is corrected (kept,
marked). **OPEN-04**'s Phase-D suspicion is **falsified**; the real cause is identified by bisect.
**OPEN-28**'s "layout_assign is T20" framing is corrected for the published −29.1% figure specifically
(kept, marked) — that figure's `layout_assign` side is actually **T19**. Three new items opened by the
measurements themselves: **OPEN-30, OPEN-31, OPEN-32** (§2). §9 pattern 1 rewritten (§9). **29 items
now open (OPEN-01 … OPEN-32; IDs 05, 21, 23 retired). Next free item ID: OPEN-33.**

**Amended 2026-08-06 (M06).** **OPEN-32's first measurement is made** and the answer is negative:
**no adopted result depends on `layout_assign`** — established structurally (`auto` cannot reach the
method) and exhaustively (all 16,320 adopted rows, plus 18,120 cross-mode rows, carry none). Report:
`extra/MEASUREMENT_open-32_adopted-dependency.md`. This **closes OPEN-01's "What is NOT known" item
3**, which was flagged load-bearing the day before. OPEN-01 and OPEN-03 keep their measured size but
their blast radius is now bounded to a method already labelled *not certified for fleet EUI*. One new
item opened by the same sweep: **OPEN-33** (§3, register hygiene). **30 items now open (OPEN-01 … OPEN-33; IDs 05, 21,
23 retired). Next free item ID: OPEN-34.**

**Amended 2026-08-06 (evening, E01c + the no-compute queue).** Two changes. **(1)** `building` mode —
the coarsest of the five resolution modes, one thermal zone per whole building — was **verified sound
at HEAD** (E01c, `PLAN_published-numbers.md` §8; manager-audited against the raw `.eio`/`.err`, not
against the report). It was the last unverified mode gating the five-mode re-run. **(2)** That audit
opened **OPEN-34** (§4): a 3-building local run at HEAD assigned `SuperTallBuilding` to two buildings
the adopted fleet calls `LargeOffice` — **the arc's own verification method is not
archetype-faithful**, mechanism identified the same evening by N05.

**Amended 2026-08-06 (late, the no-compute queue N01–N05 — all five landed and all five audited).**
OPEN-22, OPEN-29, OPEN-34 and OPEN-06/07/11 all have their first measurement made; **OPEN-25 is
CLOSED** (fixed 2026-06-10, the day after it was named, and carried on this register for eight weeks
afterwards); OPEN-24/26/27 re-checked at HEAD. **OPEN-35 opened** (§4) — two fallbacks invent the same
missing storey count and disagree, found while auditing N05's mechanism. **31 items now open
(OPEN-01 … OPEN-35; IDs 05, 21, 23, 25 retired). Next free item ID: OPEN-36.**

**Amended 2026-08-06 (round 2 of the no-compute queue, N06–N12 — `implemenation/PLAN_no-compute-queue-2.md`).**
Seven more first measurements, all read-only, all director-audited by independent re-derivation. **The
two that change how a published result must be read:**
- **OPEN-06 is no longer a labelling defect — it is a provenance defect.** N08 settled the
  `LAUNDRYROOMFLR1` contradiction from the T20 run's own artifacts: those buildings **were simulated
  as `SmallHotel`** while `05_results.gpkg` records `SmallOffice`. The physics was right; **the column
  that every per-archetype analysis groups by does not describe the run.**
- **OPEN-35's size is 2,611 of 8,160 — 32.00% of the fleet**, all persisted at `levels = 1.0`, of which
  **1,031 were given a mid- or high-rise archetype and built as a single storey.**

Also: **OPEN-12's recorded percentages do not reproduce** (36.4% → 100%, 19.2% → 100%, and a third
100% cell it never named); **OPEN-13's two forwarded defects were read for the first time and both
reproduce at HEAD** — one of them means `pytest` cannot collect the suite at all; **OPEN-14 confirmed
open** and ~~**converges with OPEN-12 on exactly the same four cells**, found by two executors who did
not share notes~~ — **that convergence was tested by N15 and is a coincidence; OPEN-12 and OPEN-14 are
two separate items and neither may be closed by fixing the other**; **OPEN-10 — the register's only ❓ — is answered from the EnergyPlus schema** (the
capability is real, the remedy narrower than claimed); **OPEN-19's hypothesis is not currently
representable** — no climate-zone or code-year switch exists and LA's HVAC comes from a **Buffalo**
prototype; and **OPEN-17 is not what this register said it was** — the draw tier is not "opt-in/OFF",
it is unreachable, because its router hook has never existed in any commit.

🔴 **Auditing that last one opened OPEN-36, and it is the most serious finding of the round.** A
progress-log entry marked *"completed 2026-07-16"*, naming artifacts and reporting 53 + 60 passing
tests, describes implementation code that **no commit on any branch has ever contained** — while
**its tests were committed**, which is precisely why `pytest` can no longer collect the suite. **A
completion record could not be trusted against the repository, and nobody had checked.**
**32 items now open (OPEN-01 … OPEN-36; IDs 05, 21, 23, 25 retired). Next free item ID: ~~OPEN-37~~
→ OPEN-37 was taken 2026-08-09 (the `.eio` fetch gap). **Next free item ID: OPEN-38.**

**Amended 2026-08-06 (round 3 of the no-compute queue, N13–N15 — `implemenation/PLAN_no-compute-queue-3.md`).**
Two landed so far. **N15** tested the OPEN-12/OPEN-14 convergence and refuted it (above). **N14**
answered OPEN-06's third open question: **`archetype_id` is not the only unreproducible column** —
`data_quality_flag` is too, on the same buildings, and what differs is *which imputation rule the
classifier says fired*. Its `archetype_id` control passes exactly against N04's population. Two
cautions the director added on audit: N14's "same 9 rows" claim is **wrong** and struck (26 vs 38 on
`nyc_centre`, the excess being a Stage-3 `narrow_perimeter_fallback` token from
`openubem/idf/builder.py:614`), and **26 of the 33 columns remain unchecked** because they are
Stage-3-or-later outputs that no no-CPU task can reach.

**Amended 2026-08-06, later (round 3 closed + round 4 — `implemenation/PLAN_no-compute-queue-4.md`).**
**N13 answered OPEN-36's question: T07 is the only one.** It swept the **full** population of **596**
progress-log entries across 59 documents — not a sample — and re-verified every mechanical hit by
hand: PRESENT 424, MOVED 6, NEVER-COMMITTED 14, UNCHECKABLE 152. Of the 14, **one** is a governance
gap (T07 itself), **twelve** are this arc's own untracked measurement CSVs, and **one** is a temp
script the entry itself declares deleted. Its raw-vs-corrected columns show **35 heuristic
misattributions caught before reporting** — the reason the number is 14 and not 49. The T07 control
was re-run by the director: `_draw_tier` exists in **no commit on any branch** and not in the working
tree, while its tests are committed. **N16 then closed OPEN-06's coverage gap on the whole fleet**
against a prediction written down before the measurement, and the prediction **held exactly** —
`archetype_id` differs on 2 / 4 / 5 rows in `austin_centre` / `la_centre` / `la_urban` and **zero** in
the other five, all 11 matching N04's population one-for-one. With N14's four cells that is
5,390 + 2,770 = **8,160 buildings, every cell, whole**. **The 41-building mislabel population is now
fully accounted for, and no third unreproducible column exists.** Two findings the director kept:
`data_quality_flag`'s 171 differences are **168 Stage-3 token artifacts and only 3 genuine provenance
divergences**, and those 3 are **not the same buildings** as the archetype failures — disjoint in
`la_urban`, absent in `la_centre` — so the two defects are independent in both directions.

**Also recorded 2026-08-06:** ~~the **five-mode local re-run (E02) is parked by user instruction** —
Speed's CPU allowance is consumed by another project and the user does not want CPU-bound work
scheduled meanwhile. It resumes when a machine is free; nothing about it is cancelled.~~
**Unparked 2026-08-06 — see the next amendment.** Work moved to
`implemenation/PLAN_no-compute-queue.md` (N01–N05), whose first measurements need no simulation.
**A prerequisite found while scoping it:** the local runner's `ALL_MODES`
(`scripts/cluster/t08_local_remainder.py:52`) is `["auto", "building", "floor", "fast_zone"]` —
**`layout_assign` is not among them**, so as it stands the local runner can only do four of the five
modes.

**Amended 2026-08-06 (the compute queue opens — `implemenation/PLAN_compute-queue.md`).**
**The user released the local workstation for simulation**, so every measurement the no-compute queue
could not reach is now schedulable. Six tasks are written (C01–C06); the plan also records, in §6,
the two items that compute **cannot** help — **OPEN-19** (no climate-zone or code-year switch exists,
so it needs code before it needs cycles) and **OPEN-11** (its precondition is met; what remains is a
remediation decision by the user, not a measurement).

🔴 **A second prerequisite was found opening that plan, and it had an attractive wrong answer.**
Beyond the missing `layout_assign` mode above, `LOCAL_CELLS`
(`scripts/cluster/t08_local_remainder.py:48-51`) held **only 7 of the 12 cells** — the LA/Austin
remainder. `nyc_centre`, `nyc_urban`, `nyc_suburban`, `nyc_rural` and `la_centre` had **no
`CELL_CONFIGS` and no `CITY_OF` entry at all**, and `CITY_OF` is read through a **silent fallback to
the cell name** (`:423`), so a missing entry would have quietly broken every city-level group-by
rather than raising. The runner is called `t08_local_remainder` because it was built to run the
*remainder* of the cluster's T08 — which invites reusing T08 for the other five cells. **Doing that
would rebuild OPEN-28**: T08 is five-week-old code and deleted every `.eio`, so it can serve neither
OPEN-02 nor a cross-mode delta that means the method rather than the calendar. **Decision pinned: all
twelve cells run locally, on one code generation.** C01 closed both gaps; CP-C1 was signed after the
director ran a bounded end-to-end smoke on a *new* cell (`nyc_rural`/`building`): **198/198 success,
0 fatal, `city` correctly `NYC`, 198 `.eio` retained, 0 `.eso` surviving.**

~~**E02 is running as of 2026-08-06**~~ — **SUPERSEDED the same day; see the closing amendment below.
E02 is halted and parked. Do not read this paragraph as a statement that anything is in flight.** What
remains true of it: the run is 12 cells × 5 modes × 8,160 buildings = **40,800 simulations**, 16
workers, `.eio` retained, and it is the only measurement in this project that closes **three** items at
once: **OPEN-01** (a verified multiplier-aware denominator for every building), **OPEN-02** (the `.eio`
that has never existed for any fleet building) and **OPEN-28** (all five modes on one generation).
Nothing here may be marked measured until CP-C2 confirms every (cell, mode) completed.

---

### ▶️ Resume amendment 2026-08-09 — **the pause is over, and one standing ruling has been given**

**The closing amendment below is superseded on two points only; everything else in it still holds and
is still the resume brief.**

1. **The arc is un-paused.** The user returned 2026-08-09. **Speed cluster resources are reported
   available**, and the user has authorised CPU-bound work again: *"maintenant des ressources de speed
   est disponible, nous pouvons utiliser avec des taches qui utilisent des ressources pour le
   computation."* Independent verification of the allowance was dispatched read-only before anything
   is submitted; **no job has been submitted and none may be until the four conditions below the
   closing amendment are discharged** — the `.eio`-deleting cluster template (condition 2) first.
2. **CP-M3 / OPEN-30 / OPEN-31 / OPEN-33 are RULED.** See each item's own section for the binding
   text. **The ruling is: all three closing steps become obligatory.** The user was given the three
   instances as one question and answered *"yes to all three — make them obligatory."*
3. **CP-C2's scheduling axis is RULED: measure first.** Speed was reconnoitred read-only the same day
   and **both gates that parked E02 are open** — account `chachemv`, `GrpTRES cpu=32`, **0 of 32 in
   use**, `squeue -A chachemv` empty; `/speed-scratch` quota **4.1 TB free** against a ~45 GB worst
   case. Options put: probe first / all five modes now / four modes with `fast_zone` queued after.
   **The user chose a bounded calibration probe**, then the fleet-scope decision against measured
   numbers. ~~**The fleet submission is still unauthorised** and CP-C2's own scope question is still
   owed.~~ **→ superseded the same day by item 5.** Execution: **`implemenation/PLAN_speed-resume.md`**
   (**R01–R06**, CP-R1 and CP-R2), which discharges conditions 1 and 2 of the closing amendment plus
   OPEN-30's new obligation before a single job is submitted. 🔴 **The 2026-08-06 descope options
   (a)–(d) stay spent and were not re-asked.** *(Task IDs were renamed `S0n` → `R0n` on 2026-08-09 —
   the progress board already used S01/S02/S04 for the arc's standing obligations. Same work, same
   order.)*
4. **OPEN-29 is RULED — RULING C: "fix the error check everywhere."** Task **R06**. See OPEN-29's own
   section for the binding text and for two corrections it forced: the bug is at **six** live sites,
   not the four recorded here, and the archived + diagnostics copies are a third occurrence class this
   register had never named. 🔴 **R06 corrects the future, not the record** — no harvest is re-run, so
   the standing rule *never use the `has_fatal` column* still binds every pre-2026-08-09 artifact.
5. **🔴 The user granted autonomous completion, and with it the fleet submission.** *"vas-y continuer
   jusqu'à la fin. et aussi commencer des runs sur le speed, des ressources sont disponibles, vas-y."*
   The director now **self-signs CP-R1 and CP-R2** and proceeds into the fleet pass without returning
   for permission; CP-C2's scope question is answered by "run it". **What this does not license, stated
   because momentum is exactly when these get dropped:** (a) **RULING B still stands** — the probe runs
   **first**; "start the runs" is not "skip the measurement", and the ≈10× miss that made the probe
   necessary came from extrapolating rather than measuring. (b) The audit standard is unchanged —
   CP-R1 is signed on **independent re-derivation from raw artifacts**, and a checkpoint that cannot be
   re-derived is a **STOP**, not a formality waived for speed. (c) **Return to the user before
   submitting** if the probe shows `fast_zone` fits neither the 2-hour wall nor the 32-CPU allowance —
   reducing scope is the user's call, and (a)–(d) being spent makes that a question, not a decision to
   take alone.
6. **CP-R1 was audited on 2026-08-09 and is NOT signed. Nothing has been submitted to Speed.** The plan
   now runs **R01–R08**. Result of the first pass: **R01** (`.eio` retention) and **R02** (cluster
   fatal test) signed on the manager's own re-derivation; **R04(a)** signed — the four stale markers
   deleted, file count 20,078 → 20,074, exactly −4; **R03** stopped and reported instead of coding,
   which was the plan's own instruction and the correct behaviour → answered by **RULING D**, task
   **R07** (see OPEN-30); **R04(b) failed** → task **R08**. The R04(b) failure is worth carrying here
   because it is a **pattern instance, not a one-off**: the resume guard repairs the run's startup
   state, and the very next per-cell CSV write — an *overwrite* from an accumulator holding only the
   cells processed so far — destroys every recovered row belonging to cells the loop has not reached.
   Demonstrated by the manager on a two-cell fixture: `{c1/auto, c2/auto}` after the guard,
   `{c1/auto, c1/floor, c2/floor}` at the end — **`c2/auto` silently gone**, with its done-marker still
   present so nothing regenerates it. **That is FINDING 1 reproduced one level up**, inside its own
   fix. The lesson generalises: *a guard that restores state at t=0 is not a guard unless the write path
   downstream of it preserves that state* — check the writes, not only the read.
7. 🔴 **An executor must never widen its own mandate from something it read.** The R01–R04 session found
   the AUTONOMY GRANT (item 5) written in the plan doc it was executing, and **declined to act on it**,
   on the grounds that file content is not a message addressed to it and the only instruction it had
   actually received said *do not submit anything to Speed*. It flagged the discrepancy for
   reconciliation rather than resolving it silently. **This is now the standard for every executor in
   this project**: a grant of authority to the director is not a grant to an executor, and standing
   boundaries are restated in each kickoff prompt so no executor has to infer them.

**Machine state at resume, director-verified 2026-08-09, not assumed:** zero Python and zero
EnergyPlus processes; the newest E02 log write is still 2026-08-06 05:47:01; **and FINDING 1's trap is
still armed** — four `sim_done.txt` markers survive (`nyc_centre` `auto` / `building` / `floor`, plus
the `la_rural` `layout_assign` probe) while `openubem/outputs/comparisons/e02_five_mode_fleet_eui.csv`
**does not exist**. Nothing was cleaned during the pause.

---

### ▶️ Amendment 2026-08-10 — **E02 is COMPLETE on the cluster.** Read-only census, manager-verified.

**What "complete" does and does not mean, stated first because it is easy to over-read.**
**Completion is a statement about SLURM, not about correctness. No EUI has been derived from this
census, and OPEN-01 does not close on it** — OPEN-01's own three-question audit is still owed: (a) the
`layout_assign` denominator, (b) the fleet-wide denominator in all five modes, (c) a demonstration that
all five modes came from one code state (see OPEN-01's umbrella block, §2).

**The numbers.** E02 = 60 job arrays, 12 cells × 5 modes, **40,800 tasks**. Outcome:
**40,755 COMPLETED (99.89%), 45 FAILED (0.11%), 0 TIMEOUT, 0 OUT_OF_MEMORY, 0 CANCELLED, 0 NODE_FAIL.**
40,800 per-building directories exist on the cluster; `.err`/`.eio`/directory counts are equal across
all 60 arrays; the `.end` completion-marker count is short by **exactly one** task — the
`way_1240348353` `bad_alloc` death recorded in the CP-R2 correction below. Remote root:
`/speed-scratch/o_iseri/fleets/e02_<cell>_<mode>/out/<stem>/`.

**Failures by array (45 total):** `nyc_centre/auto`=2, `nyc_centre/fast_zone`=9,
`nyc_rural/layout_assign`=3, `la_centre/auto`=1, `la_centre/floor`=1, `la_centre/layout_assign`=1,
`la_urban/auto`=1, `la_urban/layout_assign`=3, `la_rural/auto`=7, `la_rural/floor`=7,
`la_rural/fast_zone`=10.

**Determinism, established by an accident of records-keeping.** Eight arrays were submitted **twice**
(**OPEN-40**) and both runs produced identical task counts and identical failure counts, with the same
buildings failing both times. **The pipeline is deterministic, and the 45 failures are reproducible
properties of those buildings, not flaky infrastructure.**

**Three new items opened by this census, all Theme C:** **OPEN-38** (`layout_assign` subsurface
geometry fatal, 7 buildings across 3 cells), **OPEN-39** (`set -e` in the sbatch template silently
skips the trim step and the `task.rc` write on every failed task — `task.rc` must never be used as a
completion test), **OPEN-40** (eight arrays submitted a third time by a process no document explains —
the same duplication that proves the pipeline deterministic, above).

#### Correction to CP-R2's Risk-2 verdict (`PLAN_speed-resume.md`, "CP-R2 — SIGNED", 2026-08-09)

🔴 **Not a fourth open item — this is evidence attaching to an existing sign-off.** The register itself
never restated CP-R2's verdict text before this amendment, so there is nothing of this register's own
to strike; the claim being corrected is the one recorded in `PLAN_speed-resume.md` (not edited here —
out of scope for this pass), quoted exactly:

> ~~| **`--mem=6G`** | **CLEAN** | **Zero OOM.** Exit codes across all tasks are only `0:0` and `1:0` —
> no `137`/`125` kill signatures. All tasks ran at `ReqMem=6G`. |~~

**Correction, 2026-08-10, from the full 40,800-task E02 census (the R05 probe CP-R2 signed on covered
only 1,735 tasks):** `nyc_centre/fast_zone`'s task for stem **`way_1240348353`** — an 89-storey
building (`_F0`…`_F88`) — died on `terminate called after throwing an instance of 'std::bad_alloc'`,
SIGABRT, sacct `ExitCode=6:0`, with **no `Fatal` string anywhere in its `eplusout.err`** (the evidence
is in the array `.log`, not the `.err`). sacct's state stayed `FAILED` and was **never**
`OUT_OF_MEMORY` — this is also the one task missing an `.end` file, above. **"Zero OOM" is a statement
about SLURM's cgroup-kill classifier, not about memory sufficiency: a C++ allocation failure inside the
EnergyPlus process is not a cgroup OOM-kill, and `sacct` will not report it as one.** The claim to amend
is specifically the word "Zero" read as "memory was sufficient everywhere" — one task's memory was not.

**MaxRSS caution — cross-referenced, not duplicated.** `PLAN_speed-resume.md`'s own CP-R2 entry already
carries this warning in full (its correction to the R05 entry): the `MaxRSS` sacct column has a
**median of 0.3 MB** across the probe, with **three arrays reporting a 2.0 MB maximum** — both
physically impossible for a running EnergyPlus process, because `sacct`'s RSS poller undersamples short
tasks. **The column is a floor on peak memory, not the peak itself, and must not be read as one.** That
plan doc's own stated conclusion — "the load-bearing evidence for Risk 2 is the zero-OOM census … not
the RSS column" — is exactly the sentence the correction above narrows: the zero-OOM census was itself
reading a classifier that cannot see a `bad_alloc`.

---

### 🅿️ Closing amendment 2026-08-06 — **the arc is paused by the user; this is the resume brief**

**User instruction:** *"je vais me concentrer sur d'autres projets … dès que j'ai temps frais, je vais
retourner."* The user is moving to other projects and will return later. **Nothing is cancelled,
nothing is abandoned, and nothing is running.** This block exists so a returning session — theirs or a
fresh director's — does not have to reconstruct the state from the amendment history above.

**Machine state: idle.** No local run, no cluster job, no executor session. Any instruction to "check
on E02" is stale.

**What closed after the compute queue opened (both audited by independent re-derivation):**

| | |
|---|---|
| **C06** | **OPEN-09's "cosmetic" label is tested for the first time** and holds — 96.3% distribution overlap, residual ≈0.20 kWh/m² at a median EUI of 91.19, and the non-converged group's mean delta is *smaller* in magnitude, not larger. Zero EnergyPlus run; the 150-building matched control already existed on disk. **Consequence (a)** — the ≈3.66% fleet projection — **is untouched and still open.** |
| **C07** | **E-LA-21 fixed in the E02 runner** (`t08_local_remainder.py:430`), the fifth occurrence and the one generating today's results. Before/after shown on the same 2,422 `.err` files: 0 of 2 real fatals detected → 2 of 2. **Four other scripts still carry the bug by design** — that is a user decision under OPEN-29, not an oversight. |
| **Bookkeeping** | `extra/SCOPING_five-mode-rerun-cost.md` now carries **PART 3**, correcting its local wall-clock projection — measured wrong by **≈10×**. Parts 1 and 2 are left unedited so the failed prediction stays visible. **Part 1's *cluster* projection is not validated by that correction** and must be re-derived, not reused. |

🔴 **The four things a returning session must handle before any relaunch** — all four survive the pause
and none is discharged by it:

1. **The scope ruling (CP-C2) is still owed by the user.** E02 is parked to resume **on Speed when the
   cluster frees up**. Do **not** re-ask which of the four descope options (a)–(d) they want — that
   question is spent; the ruling came back on a different axis.
2. 🔴 **The stock cluster template deletes `.eio`.** `scripts/cluster/submit_fleet_t08.sbatch:63` is
   `rm -f "$OUTDIR"/*.eio`, byte-identical across T08→T20, and E01's retention fix is **local-only** —
   it lives in `t08_local_remainder.py`. **A cluster E02 on the unmodified template destroys the exact
   evidence OPEN-02 exists to obtain.** Highest-risk item in resuming on Speed.
3. **The silent resume data-loss trap (FINDING 1) is still un-cleaned.** `nyc_centre`'s three finished
   modes are marked done in `sim_done.txt` but their rows were never written to the output CSV. A naive
   relaunch produces a "fleet" CSV silently missing all 2,214 of those buildings — including `auto`,
   the mode OPEN-28's published comparison depends on. **Delete the `sim_done.txt` of any (cell, mode)
   whose rows are not already in the output CSV, before anything restarts, on any machine.**
4. **Do not concatenate the finished local pairs with cluster output** — that rebuilds OPEN-28.

**Where the remaining work stands.** The no-compute queue is empty: sixteen tasks across four rounds,
all landed, all audited. **Every remaining first measurement in the register needs either CPU we do not
currently have or a ruling from the user** — the open rulings being CP-M2, CP-M3 + OPEN-33 + OPEN-30
(one question, three instances), OPEN-22, OPEN-11's six inverted-geometry buildings, and OPEN-29's
four remaining E-LA-21 scripts. **Do not invent a seventeenth no-CPU task to keep busy.**

**Is:** a single place listing every item this project has left open, with — for each — what is
actually known, what is only believed, where the evidence lives, and **what single measurement would
have to be made before an execution plan could responsibly be written.**

**Is not:** a plan, a priority order, or a recommendation of what to do next. Item order inside each
theme is not a ranking. Sequencing is the user's call and is deliberately absent.

**Why it exists.** Open items in this project have been recorded in ~8 different places — arc plan
docs, `PROJECT_CHECKLIST.md`, defect logs, memory pointers, two audit docs from June — and several
have gone stale, been duplicated, or been rediscovered as "new". This session found one such
duplicate (see **OPEN-05**). A single register is the countermeasure.

### Where this arc's files go — **user instruction, 2026-08-05**

**`docs/docs_ACTIVE/openings/` stays clean.** It holds this register and `prompts/` only. **Every
supporting document an item produces — measurement reports, evidence dumps, per-item working notes —
goes in `docs/docs_ACTIVE/openings/extra/`.** The user does not want to open the arc folder and see a
pile of documents. Figures still follow the project rule: flat into `openubem/outputs/`.

### How to read the evidence column

Every claim below carries its verification state, because they are not equal:

| Mark | Meaning |
|---|---|
| ✅ **verified** | Re-derived from a raw artifact **in this session** — file named, recomputation run |
| 📄 **documented** | Recorded in a named plan/audit doc by a prior session; **not** re-verified here |
| ⚠️ **stale-risk** | Recorded ≥3 weeks ago against code or data that has since changed; treat as a lead, not a fact |
| ❓ **unmeasured** | Believed on reasoning, never measured — the belief itself is the open item |

**Rule for whoever writes the execution plans: never carry a 📄 or ⚠️ number into a plan without
re-deriving it first.** Three separate executor entries in the storey-matching arc alone shipped
headline numbers that did not reproduce from the file they cited, and one stale figure (the
81.6%/98.4% inert shares) survived four documents before being caught.

---

**Amended 2026-08-11 (the E02 audit and closure pass — `implemenation/PLAN_e02-audit-and-closure.md`,
T01–T06, all six landed, all three checkpoints director-signed by independent re-derivation).**

**Five items close and one opens: 35 tracked items → 31; 37 findings → 31.** The arithmetic is stated
in §1. Nothing here was closed on an executor's say-so — every headline number was recomputed by the
director from the named raw file, and two executor characterisations were corrected in the process.

**What closed, each with its evidence:**

- **OPEN-30 — CLOSED.** Its closure condition was written into this register verbatim and is now met:
  all **60 of 60** `03_manifest.parquet` files read, **40,800 rows, zero nulls, 5 distinct
  `vintage_standard` values**, `DOERefPre1980` at **93.44%** against the ≈92.9% expectation — not
  constant, not uniform. Director re-derived the whole distribution independently and it matched to the
  row. The `la_rural` cross-check against raw `year_built` reproduces R07 exactly: **zero crossover**,
  in all five modes.
- **OPEN-34 — CLOSED.** All **12 of 12** adopted cells are whole — each `phaseE/<cell>/05_results.csv`
  has exactly as many rows as its cell's `01_buildings.gpkg` has features, fleet total **8,160**. No
  published number was ever produced from a batch small enough for the batch-composition effect to
  fire. Director recounted two cells by hand (`nyc_centre` 738, `la_rural` 149) and the fleet total.
- **OPEN-39 — CLOSED.** The mechanism fires exactly as described and is now sized: the 45 failed E02
  tasks orphan **≈2.14 GB** (mean **48.6 MB**/dir) against **449 KB**/dir for successful ones — a
  ~111× ratio — and the failed directory has **no `task.rc`** while its successful array sibling does.
  Replicates outside E02 (`t17_austin_centre_layout_assign`). **Zero of the 15 `task.rc` references
  across 9 scripts uses its presence as a completion test** — every completion check keys on
  `eplusout.end` content. The standing rule is confirmed preventive, not corrective.
- **OPEN-40 — CLOSED as untraceable**, which the item's own text names as the answer. All 8 job IDs
  re-confirmed outside both waves by an independent from-scratch `sacct` reconstruction of all **68**
  `e02_*` submissions in the window (19 + 8 + 41 = 68, exact). Submitted 2026-08-09T23:08:58 →
  2026-08-10T00:04:49; `JobName`/`WorkDir`/`User` identical in form across all three waves, no
  discriminating signal; remote `.bash_history` predates the entire window (mtime 2026-04-27) and is
  silent for all three waves alike, so its silence is not selective evidence. **No story was
  reconstructed from timestamps.** The remedy this item already names — a submission log nobody can
  bypass — stands as the disposition.
- **OPEN-41 — CLOSED.** All **44** fatals now carry a recorded cause, and the concentration is
  explained. Causes: 25 *Temperature (low) out of bounds*, 17 `CalcHeatBalanceInsideSurf`, 1
  *Temperature (high)*, 1 `CheckForRunawayPlantTemps`. **All 44 are numerical thermal blow-ups —
  none is a syntax, missing-object or licensing failure.**

🔴 **OPEN-41's concentration is not the cell. It is the archetype.** This register recorded
`la_rural`'s 24-of-45 share as *"a hypothesis, not a measurement."* Measured: **`Warehouse` is 38 of
8,160 buildings (0.47% of the fleet) and carries 26 of the 44 fatals — 13.68% of Warehouse tasks fail
against 0.0443% of everything else, a relative risk of ≈309×.** All **11** `la_rural` failing
buildings are `Warehouse` with `no_floors`; that cell is Warehouse-dense (25 of 149), not special.
**36 of the 44 failures carry `no_floors`.** This is what opens OPEN-42.

**Two corrections the director made against executor reports — the raw files win:**

1. 🔴 **OPEN-38's stated premise is FALSE and the item is rewritten, not closed.** This register says
   7 tasks *"die on EnergyPlus severe `Base surface does not surround subsurface`."* Read from the
   files, that message is a **`** Warning **`**, not a Severe, at **all 8 sites** — including
   `nyc_rural/layout_assign/way_965718401`, which ends *"EnergyPlus Completed Successfully — 58101662
   Warning; 0 Severe Errors"* and publishes results from geometry carrying three unfitted doors.
   **It kills nothing.** What actually kills all seven is **thermal runaway in the zone
   `LAUNDRYROOMFLR1`** — the substituted prototype's laundry room, the same zone token as OPEN-06 — at
   −12,459 °C, −23,743 °C, −11,950 °C, −15,491 °C, −12,901 °C, −59,865 °C and +182,399 °C. **Zero of
   the other 37 fatals touch that zone, and zero `layout_assign` fatals have any other cause.**
2. 🔴 **`building` mode simulates exactly one storey, and its published denominator does not.** T04
   reported the mode's median error factor as 0.5000 without explaining it. Re-derived: **simulated
   area ÷ bare `footprint_area_m2` is median 1.000000 with 98.43% of the fleet inside ±1%.** The mode
   builds one zone of one storey; the denominator multiplies footprint by `levels`, whose fleet median
   is 2. **The 0.5 is the storey count, not noise.** Recorded under OPEN-01(b), which is the question
   it answers.

**Recorded, not opened as an item:** an `_ssh()` command string of **≥8,192 characters** fails on
Speed with `Unmatched '.` — a tcsh parse limit, reproduced with a quote-free payload (8,104 succeeds,
8,192 fails). Previously undocumented anywhere in this project. Nothing is open: the one script that
hit it now chunks under 7,500 chars and no other script builds commands that long. It is filed as a
**standing operational fact** in the director prompt's cluster section, where facts of that shape live.

**Amended 2026-08-12 (evening — the rulings-and-five-items sweep, `implemenation/PLAN_rulings-and-five-items-2026-08-12.md`, T01–T10, five parallel executors, every headline re-derived by the director from raw artifacts).**

**Count arithmetic: 32 − 3 closed (OPEN-43, OPEN-31, OPEN-04) + 3 opened (OPEN-45, OPEN-46, OPEN-47) = 32.** Findings 32 → 32. 🔴 **Three of the four rulings the user took today were closed out; three new items were opened, and all three came from auditing a result rather than from running a task.** That is now the dominant way this register grows, for the fifth consecutive pass.

**Rulings taken by the user 2026-08-12 and discharged the same day:**

1. 🔵 **OPEN-43 — RULED AND CLOSED. The published fleet EUI is `157.1 kWh/m²`, pooled: total simulated energy ÷ total simulated floor area over all 8,154 successful buildings.** The user delegated the choice ("*tu progress selon la plus bon precision*"); the director ruled pooled because it is the physical definition of an intensity, it is what a reader of "fleet EUI" assumes, and — unlike the mean-of-cell-means — **it does not change if the 12 cells are re-cut.** All four aggregations re-derived twice, independently, agreeing to 4 dp: **pooled 157.0552** · count-weighted **158.0298** (the struck figure) · success-weighted **158.0557** · unweighted **160.0993**; n_total 8,160, n_success 8,154, floor area 23,545,868.4 m². ~~158.0~~ restated with its definition beside it in **13 live files**; archived trees (`docs_DONE/`, `docs_main/`, `docs_VALIDATION/`) deliberately untouched as historical record. Reference implementation: `scripts/analysis/open43_fleet_aggregations.py`. Report: `extra/FIX_open-43_fleet-aggregation.md`. **ID retired.**
2. ✅ **OPEN-31 — CLOSED.** The CP-M3 before/after gate is now written in **two** places: a docstring block at the head of `openubem/semantic/building_classifier.py`, and the head section of `docs/PROJECT_CHECKLIST.md`. Director-verified that **both files' diffs are comment/docstring only — no executable line changed.** Report: `extra/FIX_open-31_classification-gate.md`. **ID retired.**
3. ✅ **OPEN-33 — CLOSED** (its last leg, written by the director): `CLAUDE.md` now carries an "Archiving an arc" section pointing at the full rule in `PROJECT_CHECKLIST.md`.
4. ✅ **OPEN-04 — CLOSED, hypothesis REFUTED.** The surviving explanation for the 92.0% → 88.0% accuracy drift was "tag coverage got worse, so more buildings fall back to size-guessing." **It is false. `FALLBACK_SIZE_DEFAULT` fires on exactly the same 17 of 50 rows at all four checkpoints (`7635ce2`, `67ede73`, `0df422e`, HEAD) — not one row ever crosses that boundary.** The drift is entirely within-rule reassignment from the E-R3-3 office/apartment tier rewrite plus one hotel-tier routing fix. 🔴 **One fact worth carrying forward: the historical 92.0% is not reproducible and never will be** — the harness reproduces 84.0/88.0/88.0 exactly but returns 66.0% at `7635ce2`, because **the very next commit (`67ede73`) rewrote 14 of the fixture's 50 answers in the same commit that changed the classifier.** A score graded against a since-rewritten answer key cannot be re-graded. Evidence: `openubem/outputs/comparisons/open04_ruletoken_by_commit.csv`; report `extra/MEASUREMENT_open-04_tag-coverage-hypothesis.md`. **ID retired.**

**Items that grew or advanced (all still open):**

- ⚠️ **OPEN-22 — the tag-rich fixture exists and it does what it was built to do.** `tests/fixtures/labelled_archetypes_tagrich_v2.csv`: 100 rows stratified from the director-verified 592-row tag-rich pool, seed `20260812`, **labelled from source tag evidence by a script that never imports the classifier** (director-verified: the builder does not import it; only the separate grader does), 2 rows marked `UNDETERMINED` and excluded. **Size-guessing fell from 34.0% (17/50) to 3.1% (3/98)** — the entire purpose of the rebuild. Accuracy **88.8%** overall, **91.6%** excluding fallback; the old fixture's 88.0% precondition reproduced first. Director re-graded both fixtures from scratch: **every figure matches exactly.** Still open: **no pytest test is wired to the new fixture** (deliberately deferred — `tests/` had a concurrent executor), and **the 0.70 gate in `test_fine_top1` is not transferable to a different exam — that threshold decision is owed to the user.** The 70 `building=roof` rows were kept in the pool and labelled `OpenUBEMUnknown`; see OPEN-47 for the external corroboration that `building=roof` means an open-sided canopy.
- 🔴 **OPEN-36 — the bound does not hold, and the item grows. 6 genuine governance gaps, not 1.** The re-sweep re-verified all 596 completion entries at HEAD (N13's own script did not survive, so it was rewritten: `scripts/analysis/open36_governance_resweep.py`). Gaps trace to **4 distinct incidents**: T07's known one, T09b, T11.8 and T11.8b (the `IMPUTE_DEBIAS_NEWERSKEW` / `_DEBIAS_NEWERSKEW_QMAP*` / `_DEBIAS_SKIPPED_THINSTRATUM` cluster), and two unrelated T04 entries. **Director-verified independently for the debias cluster: `openubem/config.py` contains no `IMPUTE_DEBIAS` attribute of any kind, on any branch — the only tree hits are the executors' own output files.** The re-sweep also found a **methodology bug in N13's own correction**: an unrestricted repo-wide `git log -S` that mistook a plan document's prose for committed code. Non-vacuity control passes (the sweep finds T07's known gap). **Failure rate is 6 of 444 checkable entries — 1.4%, not 0.2%. This changes OPEN-36 from "one bad record" to "completion records are unreliable as a class."** Report: `extra/MEASUREMENT_open-36_governance-resweep.md`.
- 🔴 **OPEN-44 — fully triaged, and it reads far better than "70 broken tests."** All 106 nodes classified, zero left `UNTRIAGED`: **65 `artifact-missing`** (a test asserting an output file exists on disk — fails on any machine where it was never regenerated), **21 `tests-for-code-that-never-existed`**, **17 `fixture-wiring`**, **2 `stale-expectation`**, and **exactly 1 `REAL-DEFECT`** — a `NameError` on an undefined `zones_found` at `scripts/analysis/test_viewer_layout_assign.py:24`, in a script, not in shipped code. Tree split confirmed: 61 in the archived elevators tree, 44 in `tests/`, 1 in `scripts/analysis/`. The `synthetic_10_gdf` errors are a **missing `conftest.py` in the archived tree**, not a missing fixture file. `tests/`-only run: **25 failed · 1,788 passed · 10 skipped · 19 errors, 18m14s.** Report: `extra/MEASUREMENT_open-44_test-triage.md`; row-level CSV `openubem/outputs/comparisons/open44_test_triage.csv`. **Nothing published is known to depend on any of the 106.**
- 🟡 **OPEN-13 — 43 innocent tests recovered.** The module-level skip on `tests/test_draw_methods.py` is replaced by a `_HAS_DRAW_TIER` guard; the single class-body-level reference to `imp._draw_tier` that aborted collection was moved inside its test method, and only `TestNoEUILeakage` is now skipped. Director re-ran both checks: **43 passed · 9 failed · 1 skipped**, and whole-repo collection **1,990 collected, exit 0** (up from 1,937). `_draw_tier` itself is still not implemented — that is OPEN-17, a DESIGN decision, and was deliberately not touched. Report: `extra/FIX_open-13_narrow-skip.md`.
- ⚠️ **OPEN-42 — the last unknown is answered, and the answer is "not locally recoverable."** The adopted run's own `eplusout.err`/`.end` for the six do not survive: **all six `work_dir`s exist and are empty (0 files)** — director-verified — and the six are absent from the T17–T20 harvest caches and from `cache/`. Per the plan's rule that is reported as a complete result, not backfilled with a hypothesis. The six re-derive exactly from the adopted manifests: **8,154 success / 6 failed**, `n_severe` 26/7/4/12/4/24, five in `la_rural` and one in `la_urban`. Corroborating traces from *other* campaigns (labelled as such, not conflated) reproduce the OPEN-11 stage-2 signature — and confirm the `thermal_mass=True` remediation was **never wired into `v12_cell_pipeline.py`** (grep: zero matches). Report: `extra/MEASUREMENT_open-42_six-failures.md`.

**Three new items, all opened by auditing:**

- 🔴 **OPEN-45** (§2) — the `Severe` marker is matched with **one** space, so **`error_summary` is empty for all 8,160 buildings**, not just the failures.
- 🔴 **OPEN-46** (§4) — **the elevator end-use breakout was never merged into the live tree**, and three of five archived test twins had the expectation removed rather than the feature added.
- 🔴 **OPEN-47** (§6) — **the office size-tier thresholds are untraced to any external source**, and this project's own deep-research document contains a **fabricated citation**.

---

**Amended again 2026-08-12 (night — the three-new-items sweep, `implemenation/PLAN_three-new-items-2026-08-12.md`, T01–T07, four executors, every headline re-derived by the director from raw artifacts).**

**Count arithmetic: 32 − 0 closed + 1 opened (OPEN-48) = 33.** Findings 32 → 33. 🔴 **None of the three items closed. One of them was materially reversed, and the audit of that reversal opened OPEN-48 — the sixth consecutive pass in which this register grew by checking a result rather than by running a task.**

🔴 **The headline correction of this pass, and it runs the opposite way to the fear it corrects.** OPEN-46 was opened on the belief that the elevator end-use breakout "was never merged into the live tree," with the reassurance attached that the fleet figure was nevertheless safe because elevator energy sat folded inside `equipment_eui_kwh_m2`. **The mechanical half of that was right and the conclusion drawn from it was wrong.** The adopted `phaseE_elevrb` outputs **already carry `elevators_eui_kwh_m2` and `gwp_elevators_kgco2_m2` columns**: across all 12 cells and 8,160 rows, **3,561 are non-zero, summing to 12,508.8 kWh/m²**, and in `nyc_urban` exactly **87** are non-zero — precisely the 87 elevator-eligible buildings. Against the pre-elevator `phaseE` run the **median** of `|Δtotal_eui − elevators_eui|` is **exactly 0**. ✅ **Elevator energy is in the adopted run and inside the published 157.1 kWh/m². Nothing is missing from the published number, and it was never folded into equipment — it was de-folded out of it, which is precisely why the check that looked at equipment saw nothing.**

🔴 **What is actually broken is larger: the adopted run cannot be reproduced from this repository.** Live `openubem/idf/builder.py` never calls `assign_elevators`; live `parser.py`, `outputs.py` and `carbon.py` have no elevator column, meter or GWP term — yet the adopted outputs carry all of it. The wiring existed in the working tree when the run was made and **was never committed**; commit `ef19141` added only the archived copies under `docs/docs_DONE/` plus three orphan live files. **Registered as OPEN-48.**

⚠️ **A method note that belongs in the register, not only in the plan.** The director's own first check reproduced the executor's wrong conclusion, by the same route: both measured change in `equipment_eui_kwh_m2`, the column the de-folding transform moves energy *out of*, where the effect is invisible by construction. **Check the invariant a transform preserves — here the total — not the column it moves energy between.**

**The other two items both advanced, and neither closed:**

- ⚠️ **OPEN-45 — fixed where it was authorised, and the underlying fact this project had been repeating turns out to be wrong.** A single whitespace-tolerant helper (`openubem/results/err_parse.py`, 16 tests) now backs `v12_cell_pipeline.py:625` and `make_manifest_from_cluster.py:47`; load-bearing one-space sites **2 → 0**. 🔴 **But the "two spaces" rule is only half right.** Director censused every marker in all 64 real `.err` files on this machine: **`** Warning **` one space both sides (4,881), `** Severe  **` one space before and two after (37), `**  Fatal  **` two both sides (1).** Consequence: **a literal written for two-spaces-both-sides misses `Severe` exactly as badly as the one-space literal did** — which is the live state of `tests/test_sim_integration.py:171`, matching **0 of the 37** real Severe lines. That site and `openubem/simulation/runner.py:140` were outside the executor's write-set, correctly flagged rather than edited, and **keep OPEN-45 open**.
- ⚠️ **OPEN-47 — the source exists, and the item stays open for a different reason than it was opened for.** The thresholds trace to **Chen, Hong & Piette (2017), *Applied Energy* 205, 323–335, Table 1** — director-verified by opening the PDF and finding `Small office (<2322 m2 and <= 3 floors)` / `Medium office* (2322 to 9290 m2, <= 5 floors)` / `Large office (>9290 m2 or >=6 Floors)` verbatim, and by Crossref-checking DOI `10.1016/j.apenergy.2017.07.128`. Hong et al. (2015), which the code and `RESULT_I02` both credited, contains **zero** occurrences of either number. Caveat that must travel with the finding: **it is CityBES's own case-study table, not a citation to an external standard.** 🔴 **A divergence found in the quoted text and not yet adjudicated: the source's rule is area AND floor count; `building_classifier.py:175-177` tests area only.** The citation audit also found **a second fabricated DOI** (Sun et al. 2021 given as `10.1016/j.enbuild.2020.110586` — director-checked, **HTTP 404**; the real one is `…110603`) and **a systemic wrong-locator pattern** across every Deru et al. (2011) row.

**One new item:**

- 🔴 **OPEN-48** (§7) — **the adopted baseline run cannot be reproduced from the current repository.** The elevator wiring that produced it was never committed.

---

**Amended 2026-08-13 (the three-rulings sweep's T04, `implemenation/PLAN_three-rulings-2026-08-12.md` §8 — the twelve-cell fleet re-run, its cause analysis, and the confirmatory repeat run; director-audited against the raw IDFs and `05_results.csv` on both sides).**

**Count arithmetic: 33 − 0 closed + 1 opened (OPEN-49) = 34.** Findings 33 → 34. 🔴 **The seventh consecutive pass in which this register grew by checking a result rather than by running a task** — the re-run was commissioned to restore elevator energy, and elevator energy reproduced exactly; what it found instead was a defect nobody was looking for.

✅ **OPEN-48's own question is answered and the reassurance leads: the repository now regenerates the elevator energy.** With the load wiring restored, the twelve-cell re-run reproduces the adopted run's `elevators_eui_kwh_m2` column **cell by cell — 3,561 non-zero rows on both sides**, same 8,160 buildings, same 6 known failures. **The published `157.1 kWh/m²` was never missing elevator energy and still is not.**

🔴 **What the re-run exposed instead.** The fleet lands at **159.2157 against the adopted 157.0552 (+2.16, +1.4%)**, and the gap is **not** elevators. Direct IDF comparison against the adopted run's own staged files, still on Speed: reproducing buildings differ in **6 cosmetic lines** (the order of three `Output:Meter` names); moving buildings differ in **hundreds of lines of window-vertex Z-coordinates**. The window head and sill shift, solar gain changes, and per-building EUI swings reach **±300 kWh/m²**. **Registered as OPEN-49.**

✅ **Nondeterminism is ruled out, at the stronger of the two available stages.** A repeat run on unchanged inputs (run-1's cached `01_buildings.gpkg` and EPW copied in, so step 1 loads the cache instead of re-fetching OSM) produced **738 of 738 IDFs byte-identical by MD5, `DIFFERING=0`** — the seeded generator reproduces bit-for-bit, random `wwr` included. The results stage agrees: **37 of 738 rows differ at all, largest difference 0.00836 kWh/m², cell EUI Δ = −2.8e-05**, confined to `cooling` and `fans` with `lighting` and `equipment` bit-identical — EnergyPlus float noise on an identical IDF, four orders of magnitude under the +2.16. **The adopted-vs-re-run difference is therefore in the INPUTS, not in the pipeline's randomness.**

⚠️ **What must not be asserted: *why* the classification drifted.** The re-run fetched OSM fresh and the adopted run fetched earlier; `Courthouse` → `OpenUBEMUnknown` is what upstream tag removal would look like. **But the adopted run's input `01_buildings.gpkg` no longer exists, so the two fetches cannot be diffed.** Leading hypothesis, not a measurement.

**One new item:**

- 🔴 **OPEN-49** (§10, immediately after OPEN-48) — **one reclassified building silently re-randomises the window-to-wall ratio of every unidentified building in the same cell.** The pipeline reproduces only while its inputs never move.

🟢 **RULED THE SAME DAY (2026-08-13), and this settles the headline: the published fleet EUI STAYS `157.1 kWh/m²` — pooled, total simulated energy ÷ total simulated floor area over all 8,154 successful buildings.** The user was given both sides and chose to keep it. **`159.2157` is NOT adopted, is not the fleet figure, and must not be restated as one in any document.** The reason is on the record: **159.2157 is not a better model — it is the same model run through OPEN-49's defect**, so adopting it would publish the bug and would move the headline again the next time OSM classification shifts. ⚠️ **The cost of keeping it is accepted, not waved away: the published figure remains one that HEAD cannot reproduce end to end, so OPEN-48's provenance caveat stays live until OPEN-49 is fixed and the fleet is re-run a third time.** The re-run's 159.2157 is retained as **evidence inside OPEN-49**, never as a published number.

**Later the same day — CP-1 of `PLAN_two-measurements-2026-08-13.md`, two measurements delivered and one new item opened. Signed by the director under the standing autonomy grant, after re-deriving both results from raw artifacts rather than reading the reports.**

- ✅ **OPEN-42's blocking unknown is answered.** All six failed warehouses died of the **same** cause — runaway zone temperatures (−444.53 °C to +530.25 °C), never a geometry or input error. 🔴 **And the failure is zoning-dependent, not building-dependent**: all six run clean under whole-building mode. The item stays open on a sharper question — why one zoning mode survives where another blows up.
- ✅ **OPEN-44's `tests/` triage is complete.** `26 failed · 1,857 passed · 10 skipped · 19 errors` at HEAD, **reproduced by the director in an independent 18-minute run down to the identical set of 45 node IDs**. **31 are missing disk artifacts; the other 14 are not stale tests — they are the last standing evidence that two built features were never wired**, and they route to **OPEN-17** (9) and **OPEN-36** (5). 🔴 **Zero real defects in shipped code.**
- 🔵 **OPEN-50 opened** (§10, at the end) — **running the test suite rewrites a checked-in fixture**, and one such rewrite is already in the history at `6aeebb0`. Feature data is provably untouched; only a timestamp field moves.

---

## 1. Summary — ~~**34 tracked items**~~ ~~**29 tracked items** *(2026-08-13, after `PLAN_five-items-2026-08-13.md`: −5 — **OPEN-26, OPEN-36, OPEN-44, OPEN-45, OPEN-50** all closed and retired; **nineteen IDs retired in all**. Table re-counted programmatically: **29 live rows, 20 struck.**)*~~ ~~**29 tracked items** *(2026-08-13, later, after `PLAN_five-more-items-2026-08-13.md`: **−2 closed** — **OPEN-24** and **OPEN-32**, both retired, **twenty-one IDs retired in all** — and **+2 opened**, **OPEN-51** and **OPEN-52**, both found by the director rather than by a task's stated question. **The count is flat, and that is the honest reading: this pass closed two items and discovered two more.** Table re-counted programmatically: **29 live rows, 23 struck — 52 total, exactly OPEN-01…OPEN-52 with no row missing and none duplicated.** ⚠️ The previous header's "20 struck" was a miscount in the prose; the table itself was complete at 21.)*~~ ~~**28 tracked items** *(2026-08-17, after T08 of `PLAN_open-49-and-open-01-2026-08-13.md`: **−1 closed** — **OPEN-01**, retired, its remedy implemented and its before/after reproduced on all five modes (see this item's own §1 row and §-section). **Twenty-two IDs retired in all.** Table re-counted programmatically: **28 live rows, 24 struck — 52 total, exactly OPEN-01…OPEN-52 with no row missing and none duplicated.** OPEN-49 is not counted in this closure — it stays live, marked mechanism-fixed/closure-blocked, in its own §-section.)*~~ **26 tracked items** *(2026-08-18, after T06 of `PLAN_five-items-2026-08-18.md`: **−2 net** — three closed and retired (**OPEN-06, OPEN-37, OPEN-51**) and one opened (**OPEN-53**, the E02 harvest `.sql`/`.end` shortfall found by T03's `.eio` census). **Twenty-five IDs retired in all.** Table re-counted **programmatically**, by a script over the §1 table body (`scripts` output quoted in this pass's plan doc §8, T06 progress-log entry): **26 live rows, 27 struck — 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated.** The reconciliation carries forward unchanged in kind, updated in number: **27 struck rows but 25 retired IDs; the difference of exactly 2 is still OPEN-02 and OPEN-28, folded under OPEN-01's umbrella and never independently tracked.**)* (OPEN-01 … **OPEN-52**; OPEN-23 excluded, OPEN-21 deferred, OPEN-05, OPEN-25, **OPEN-30, OPEN-33, OPEN-34, OPEN-39, OPEN-40 and OPEN-41** closed — all ten IDs retired; **OPEN-04, OPEN-31 and OPEN-43 closed 2026-08-12 and formally retired 2026-08-13 on ruling `2h`**; **OPEN-22 closed and retired 2026-08-13** — fourteen IDs retired in all; ~~**OPEN-01 closed and retired 2026-08-17** — fifteen IDs retired in all; **OPEN-02 and OPEN-28 folded into OPEN-01** on 2026-08-09 and **both discharged 2026-08-11**)~~ *(Corrected 2026-08-17, director audit: the trailing parenthetical above was stale — it stopped at fourteen after OPEN-22 and never picked up the five retirements from `PLAN_five-items-2026-08-13.md` (OPEN-26, OPEN-36, OPEN-44, OPEN-45, OPEN-50) or the two from `PLAN_five-more-items-2026-08-13.md` (OPEN-24, OPEN-32), so the executor's first pass at this line copied its stale "fourteen + 1" into "fifteen" instead of following the correct running total in the struck-header lineage on this same line, which already read twenty-one before today. The full retired-ID list, twenty-two in all: **OPEN-23** (excluded), **OPEN-21** (deferred), **OPEN-05, OPEN-25, OPEN-30, OPEN-33, OPEN-34, OPEN-39, OPEN-40, OPEN-41** (closed, ten so far), **OPEN-04, OPEN-31, OPEN-43** (2026-08-12/13, thirteen), **OPEN-22** (2026-08-13, fourteen), **OPEN-26, OPEN-36, OPEN-44, OPEN-45, OPEN-50** (2026-08-13, nineteen), **OPEN-24, OPEN-32** (2026-08-13, twenty-one), **OPEN-01** (2026-08-17, twenty-two). **OPEN-02 and OPEN-28 are folded into OPEN-01, not retired** — they were struck rows in the table (discharged 2026-08-11) but never independently-opened tracked IDs, which is exactly why the table carries **24 struck rows against only 22 retired IDs: the difference of 2 is OPEN-02 and OPEN-28**, and that is the reconciliation, not a miscount.)* *(Extended 2026-08-18, T06 of `PLAN_five-items-2026-08-18.md`: three more IDs retired — **OPEN-06** (classifier archaeology closed the item), **OPEN-37** (`.eio` fetch gap closed on all ten sites), **OPEN-51** (`E-LA-16` adjudicated) — **twenty-five IDs retired in all.** One new ID opened, **OPEN-53** (E02 harvest `.sql`/`.end` shortfall), not yet retired. The struck-vs-retired difference of 2 (OPEN-02, OPEN-28) is unchanged by this pass — all three closures this pass retired an ID that was also a struck row, one-for-one, so the gap neither widens nor narrows.)*

> ✅ **Census reconciled 2026-08-13 (ruling `2h`).** The table below now carries **34 live (non-struck)
> rows**, matching the header. Before today it carried 38 against a header of 35 — the five rows for
> `OPEN-45`…`OPEN-49` were missing, and three items the §0 arithmetic had already subtracted as closed
> (`OPEN-04`, `OPEN-31`, `OPEN-43`) were never struck or retired. **Both halves are now repaired: five
> rows written from their own §-sections, three closures written into their §-sections and struck here.**
> **The count is auditable against the table for the first time since 2026-08-12.**
>
> **Then 35 → 34 later the same day: OPEN-22 closed** when ruling `2a` was executed and the tag-rich
> exam was gated (CP-1 signed). **This is the count moving DOWN by finishing work, not by reclassifying
> it** — the distinction the 2026-08-12 arithmetic block below was written to protect.
>
> ✅ **Then 34 → 29 the same night: `PLAN_five-items-2026-08-13.md` closed all five it took on** —
> **OPEN-50** (fixture rewrite), **OPEN-44** (45 red tests), **OPEN-45** (matcher sweep), **OPEN-36**
> (false completion record), **OPEN-26** (two will-not-fix survivors). **Biggest single-pass reduction this
> arc has made, and every one was closed by measurement, not by reclassification.** The table was
> **re-counted programmatically** after the edits — **29 live rows, 20 struck** — so the header is
> auditable against the table, not asserted.
>
> 🔴 **Two of the five close with a debt attached, and the debt must not be lost with the ID.**
> **OPEN-44's** green suite is 45 skips, **14 of which exist only because OPEN-17 has not been ruled** —
> retiring the ID does not build the feature. **OPEN-50** needs the user to `git restore` the still-dirty
> fixture in the working copy; no session here may run git write commands.
>
> ⚠️ **A table defect noticed while re-counting and NOT fixed, so it is not silently inherited:** the
> **OPEN-46** row carries **8 pipes instead of 6** — a pre-existing column break, unrelated to today's
> edits, which will render that row wrong. **Recorded here rather than repaired blind.**

> **Count arithmetic for 2026-08-12 (the five-item sweep), stated so it can be checked.** **31 tracked
> items at the start, −1 closed** (OPEN-33), **+2 opened** (OPEN-43, **OPEN-44**) = **32**.
> Findings: **31 → 32** on the same arithmetic.
>
> 🔴 **The count went UP, and it went up for the right reason.** The user's standing goal is to
> reduce open items, and this pass **added one net**. Both new items were found by **auditing** —
> OPEN-43 by re-deriving the published headline a second way as a check nobody asked for, OPEN-44 by
> running the test suite that OPEN-13's own fix had just made runnable. **Neither was found by looking
> for it, and suppressing either to protect the count was forbidden by the plan and was not done.**
> Three further items moved without changing the count: **OPEN-26 went from 1 of 4 fixed to 2 of 4 with the
> remaining two downgraded to will-not-fix; OPEN-29's fatal-test class is finished on live code;
> OPEN-42 lost two of its four unknowns and had one of its headline claims retracted.**

> **Count arithmetic for 2026-08-11, stated so it can be checked.** **35 tracked items at the start,
> −5 closed** (OPEN-30, OPEN-34, OPEN-39, OPEN-40, OPEN-41), **+1 opened** (OPEN-42) = **31**.
> Findings: **37 at the start, −5** for the same closures, **−2** for OPEN-02 and OPEN-28 discharging
> (both were folded findings under OPEN-01 sharing one closure condition — the E02 fleet pass — which
> has now been made and read), **+1** for OPEN-42 = **31**. **Items and findings are equal again for
> the first time since 2026-08-09.**
>
> **The count went down, and it went down for the right reason.** The plan that produced this pass
> (`PLAN_e02-audit-and-closure.md` §0) projected 35 → 29–30 and it landed at **31**. The two-item
> shortfall is honest and is stated rather than smoothed: **OPEN-38 did not close** — its premise was
> falsified and the item was rewritten, which is more work than closing it would have been — and
> **OPEN-42 opened**, because the same measurement that closed OPEN-41 exposed a real defect in the
> `Warehouse` population. **Measuring opens items. Suppressing a finding to protect a count was
> forbidden by the plan and was not done.**
>
> 🔴 **OPEN-01 did not close, and must not be reported as closed.** Two of its three audit questions
> are now answered on all 40,800 runs — (a) the `layout_assign` denominator and (b) the fleet-wide
> denominator in all five modes. **(c) — that all five modes came from one code state — cannot be
> proved from the artifacts that exist**, and the reason is structural rather than fixable: **no commit
> hash or code-version stamp was recorded anywhere at generation time**, and 25 of the 60
> `(cell, mode)` pairs have no generation-summary JSON at all. The positive evidence is real but
> circumstantial — one schema across all 60 manifests, all 60 written inside one continuous 111-minute
> window (2026-08-09 21:03:01–22:54:38) with no gaps. **A ruling is now owed on whether that is
> sufficient, because if it is not, OPEN-01 can never close on this corpus.** Recorded in the director
> prompt's owed-rulings list.
>
> **Also corrected 2026-08-11:** the two `e02_run*.log` files, cited as code-state evidence in the
> plan and reachable from this register, **do not cover the audited corpus** — both are dated
> 2026-08-06, three days before the manifest-write window, reference `nyc_centre` only, and
> `e02_run_2.log` ends in an unhandled `MemoryError` inside a local `t08_local_remainder.py` attempt
> that was abandoned and superseded by the Speed-cluster build. **They carry no weight as fleet
> evidence. Do not cite them.**

> **+3 on 2026-08-10: OPEN-38, OPEN-39, OPEN-40**, all found by the manager's read-only E02 completion
> census (60 job arrays / 40,800 tasks, 40,755 COMPLETED / 45 FAILED — full numbers in §0's
> 2026-08-10 amendment and in each item's own section). Like OPEN-34–37 before them, none was found by
> running a task — all three were found by **auditing** the census against raw `sacct`/`.err` output.
> **36 findings, 34 things to track**, arithmetic: 33 findings / 31 things to track (below) **+3** items,
> **+0** foldings. ~~**Next free item ID: OPEN-41.**~~
>
> **Amended 2026-08-10 (later, after R10 landed): +1 — OPEN-41.** The E02 harvest completed (all 60
> arrays, 40,800 building dirs on disk) and its failure census reconciled **0/0 in both directions**
> against the 45 `sacct` FAILED tasks — but **43 of the 44 fatals carry only EnergyPlus's generic
> trailer**, so the *causes* are unrecorded. Found by **auditing R10's own output**, not by running a
> task. **37 findings, 35 things to track. Next free item ID: OPEN-42.**

> **Count deliberately unchanged on 2026-08-10 although OPEN-37's defect is fixed.** The code fix
> (R09) is verified, but the item also asserts that *every fleet harvested before 2026-08-10 lacks the
> file locally* — and no harvest was re-run, so that half is still true. **Closing it is a decision for
> the user, not a bookkeeping consequence of a merged fix.** Retiring an ID on the strength of a diff
> is exactly the records defect this arc keeps uncovering.

> **+1 on 2026-08-09 (late): OPEN-37**, found by the manager while auditing R05's CP-R2 readout — the
> harvest's tar list omits `*/eplusout.eio`, so simulated floor area can never come home. **33 findings,
> 31 things to track.** Like OPEN-34/35/36 before it, it was found by **auditing** a task rather than
> running one, and the task that produced it was not looking for it.

> **Count change, stated so it is not read as two items closing.** Nothing was closed and nothing was
> deleted. On 2026-08-09 the user directed that OPEN-02 and OPEN-28 be **merged into OPEN-01**, which
> they share a single closure condition with — the E02 fleet pass. **32 findings, 30 things to track**
> at that point.
> Both folded sections remain in full beneath their own headings, marked as evidence rather than as
> separate commitments. **OPEN-01 does not close until all three questions are answered** — see its
> umbrella block.

> **Count arithmetic for 2026-08-06 evening, stated so it can be checked:** 30 at the start of the
> evening, **+2** (OPEN-34 from the E01c audit; OPEN-35 from the N05 audit), **−1** (OPEN-25 closed —
> fixed 2026-06-10, the day after it was named) = **31**. Then round 2 of the no-compute queue,
> **+1** (OPEN-36 from the N10 audit) = **32**.
>
> **All three new items were found by auditing a task, not by running one.** OPEN-34 came from checking
> E01c's report against the raw files; OPEN-35 came from checking N05's stated mechanism against the
> source. **Neither task was looking for what it found**, and neither would have surfaced if the
> reports had been taken at their word. That is the case for auditing by re-derivation, made twice in
> one evening.
>
> **Measuring opens items; that is the process working** (director prompt §5, second corollary). The
> same evening also closed one item carried for eight weeks after it had been fixed, and resolved the
> first measurement on five others.

| ID | Item | Theme | Blast radius | Evidence |
|---|---|---|---|---|
| ~~OPEN-01~~ | ~~EUI denominator wrong for non-`applied` buildings (E-LA-41)~~ | **CLOSED 2026-08-17** — ruling 6's remedy (divide by the multiplier-aware simulated area from `eplusout.eio`) landed in `openubem/results/parser.py`/`aggregator.py` (T05 of `PLAN_open-49-and-open-01-2026-08-13.md`), regression-tested (T06, `tests/test_results_denominator.py`, 7 tests, non-vacuous), and measured before/after on all five modes and 40,800 rows (T07): `auto` 1.0000/99.63%, `floor` 1.0000/98.43%, `fast_zone` 1.0000/94.80%, `layout_assign` 0.9999/15.37%, `building` 0.5000/39.94% — every target reproduced exactly. `building` mode is now internally consistent, not physically representative (code comment at the site). **The published fleet figure `157.1 kWh/m²` pooled is unchanged** — `auto`'s error factor was already ≈1.0000. **ID retired.** Full record: this item's own section, `extra/MEASUREMENT_open-01_denominator-swap.md`. |
| ~~OPEN-02~~ | ~~No fleet-scale EUI has a simulation-verified denominator (`.eio` deleted)~~ | **DISCHARGED 2026-08-11** — a folded finding under OPEN-01 sharing its closure condition, the E02 fleet pass, which has now been made **and read**. **Every one of the five modes now has a simulation-verified denominator over all 8,160 buildings, parsed from 40,800 `.eio` files with 0 parse failures.** Evidence: `openubem/outputs/comparisons/e02_simulated_floor_area.csv`, `open01_denominator_audit.csv`. The finding it asserted — that no published fleet EUI had a verified denominator — was true when written and is no longer true. |
| OPEN-03 | `layout_assign` models all internal loads as 2022-code regardless of real vintage | Reported numbers | ~half of a −29% cross-mode gap | ✅ **measured** |
| ~~OPEN-04~~ | ~~Labelled-accuracy gate drifted 92.0% → 88.0%, root cause unconfirmed~~ | **CLOSED 2026-08-12, formally retired 2026-08-13 on ruling `2h`** — the drift is explained and the item's own question is answered. The suspected Phase-D fusion/crosswalk cause was **falsified** by M04's live before/after reproduction, and the real cause was identified by bisect; the gate still clears. ⚠️ **Two facts survive the closure and must travel with any accuracy figure:** **92.0% is unreproducible** for an unrelated reason (its answer key was rewritten in the next commit, T10), and **the old 50-row fixture must never be deleted or edited — this item's bisect depends on it.** **ID retired.** |
| ~~OPEN-05~~ | ~~`has_fatal` dead column logged twice~~ | **CLOSED 2026-08-05** — full ID sweep run, no further duplicates. See §3. ID retired. |
| ~~OPEN-06~~ | ~~Archetype labels wrong for 41 of 8,160 buildings~~ ~~**the column does not describe what was simulated**~~ (E-LA-38) ✅ **CLOSED + ID RETIRED 2026-08-18** — commit `67ede73` reproduces the committed `05_results.gpkg` archetype exactly for all 41 buildings; resolves N07's provenance gap | Simulation correctness → **provenance** | 41 buildings; 100% of failures; **every per-archetype grouping** | ✅ **source defect + provenance defect**; ✅ **N14/N16 swept, population fully accounted for**; ✅ **2026-08-18: code state identified (`67ede73`), remaining first measurement answered** |
| OPEN-07 | 3 buildings regressed success → failure (E-LA-40) — **all three were simulated as `SmallHotel`, not the `SmallOffice` the file records** | Simulation correctness | 3 / 8,160 | ✅ |
| OPEN-08 | Archetype/vintage not reproducible locally for data-poor buildings (E-LA-22) | Reproducibility | all cross-generation comparison | 📄 **partially quantified** |
| OPEN-09 | `thermal_mass=True` drives warmup non-convergence; "cosmetic" never tested (E-LA-23) | Simulation correctness | 64% vs 5.3% control | ✅ **C06: "cosmetic" tested and holds — 96.3% distribution overlap, small correctly-signed residual** (audited) |
| OPEN-10 | `ZoneGroup` list-multiplier edit would restore exact expressibility (E-LA-37) — **capability confirmed real from the schema; remedy narrower than claimed** | Capability | ~~90 buildings (**carried, not re-derivable without a fleet pass**)~~ **C03: 90 reproduces exactly — but that is 4.6% of the 1,976 inexpressible fleet-wide** + future | ✅ **measured + verified** |
| OPEN-11 | 6 inverted-geometry buildings need post-hoc remediation, not re-applied | Simulation correctness | 6 / 8,160 | ⚠️ |
| OPEN-12 | ~~Rural `height_m` residual — `nyc_rural` 36.4%, `austin_rural` 19.2%~~ **both re-derive at 100%; a third cell is at 100% and was never named**. **N15: genuinely a source-coverage gap — NOT a spillover from OPEN-14** | Data acquisition | **3 cells, 2,032 buildings; 2,806 / 8,160 fleet-wide** | ⚠️ **numbers do not reproduce** |
| OPEN-13 | E-UTCI-12 and E-UTCI-13, forwarded out of the UTCI arc — ~~both live at HEAD~~ **E-UTCI-13 fixed 2026-08-12; E-UTCI-12 contained only** | Data / Stage 6 | ~~the whole test suite cannot be collected~~ **collectable again (1937 tests, exit 0) — but 43 passing tests traded away**; cached re-read no longer nulls `levels`/`use_class` | 🟡 **1 of 2 fixed** |
| OPEN-14 | UTCI height backfill is not reproducible from a clean checkout — **confirmed; no Overture slice is tracked for any affected cell** | Reproducibility | Stage 6 inputs; ~~converges with OPEN-12 on the same 4 cells~~ **N15: coincidence — separate item** | ✅ **measured** |
| OPEN-15 | Imputation Phase E — documented-deferred, never executed — **no code path exists at all** | Imputation | fleet inputs | ✅ **measured** |
| OPEN-16 | `ml` imputation tier built but permanently off — **never reachable from the production pipeline, only from the validation entry point** | Imputation | opt-in only | ✅ **measured** |
| OPEN-17 | 6 variance-preserving draw-tier imputers built, ~~off, awaiting a promotion decision~~ — 🔴 **not "off": the tier is unreachable; its router hook has never existed in any commit** | Imputation | ~~opt-in only~~ **the decision's cost was understated** | ✅ **measured** |
| OPEN-18 | **Q3 — √S vertical-form distortion**, now confirmed unreachable by the mechanism built for it | Method | small buildings, cold cells | ✅ |
| OPEN-19 | LA runs ~+40% hot — Title 24 vs ASHRAE 90.1 — **not currently representable: no climate-zone or code-year switch exists; LA's HVAC comes from a Buffalo prototype** | Method | one whole city | ✅ **measured** |
| OPEN-20 | Wider validation matrix beyond 3 cities × 4 rings | Method | external validity | 📄 |
| ~~OPEN-21~~ | ~~Mixed-use classification key re-cut~~ | **DEFERRED to future by the user 2026-08-05** — one function per building stands; moved to `docs/docs_TODO/mixed_use_classification.md`. See §6. ID retired. |
| ~~OPEN-22~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | ✅ **The exam was rebuilt AND gated — ruling `2a` executed, CP-1 signed 2026-08-13.** Old `>= 0.70` gate untouched on the 50-row fixture; new `TestTagRichTop1Accuracy` gates the tag-rich fixture at **`>= 0.80`**, measuring **88.8% on 98 graded rows** (8.8 pts headroom), **re-derived two independent ways to four decimals** and **proved non-vacuous by hand** (threshold raised to 0.95 → failed → restored). Size-guessing **34.0% → 3.1%**. **Binding forward: every accuracy figure names its fixture; CP-M3 spans both exams; neither fixture is ever edited.** ⚠️ Coarse is **98/98 = 100%** against fine's 88.8% — **all 11 errors sit inside the correct coarse class**, which hands OPEN-47 its next measurement and argues against ever adding a coarse gate here. Evidence: `extra/FIX_open-22_tagrich-gate.md`. <br><br> ~~"Which exam does the answer key grade" — label-review basis undecided; measurement made 2026-08-06, ruling still owed~~ 🔴 **RULED 2026-08-12: REBUILD THE FIXTURE.** The user rejected both cheap options and declared the current 50-row exam the wrong one — a third of it is decided by the size-bucket fallback, even though that fallback was measured **not** to inflate the 88.0%. **Still open, now as work rather than as a decision.** Binding: historical accuracy numbers become non-comparable and every future figure must name its fixture; the old fixture is not deleted or edited; the ≥0.70 gate's threshold does not transfer. **Blocked on one question — who authors the new labels, and how many rows.** | ~~Decision owed~~ **Work owed** | accuracy metric itself; **every published accuracy figure's comparability** | ✅ **measured**; 🔴 **ruled 2026-08-12** |
| ~~OPEN-23~~ | ~~`layoutGenerator` production zone-mode~~ | **EXCLUDED by the user 2026-08-04** — see §7.0. ID retired, not reused. |
| ~~OPEN-24~~ | ~~LIVE_SMOKE gate still parked~~ **CLOSED 2026-08-13 — ID RETIRED.** Never parked on this machine; run alone 4× → `7 passed`, ~66s, EnergyPlus 23.1.0-87ed9199d4, no network | Test integrity | Stage 3 → 4 | 🟢 **closed** |
| ~~OPEN-25~~ | ~~Modules 04/05/06 bridge~~ | **FIXED 2026-06-10, the day after it was named; confirmed at HEAD 2026-08-06. Closes.** See §7. | — | ✅ |
| ~~OPEN-26~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | Manifest/provenance polish items — ~~**1 of 4 fixed, 3 survive**~~ **2026-08-12: 2 of 4 fixed.** The missing-EPW `Site:Location` case is fixed (`builder.py:213-218` now raises instead of silently simulating at latitude 0°/longitude 0°, the templates' `PLACEHOLDER` default; 187 tests pass). **The two survivors are both re-grepped-still-true and both deliberately will-not-fix**: `compute_form_factor` is dead code, and the neighbour-bbox recomputation is efficiency-only — **neither can move a published number.** ✅ **CLOSED 2026-08-13 (T05 of `PLAN_five-items-2026-08-13.md`, CP-2 signed): both survivors re-verified at HEAD by the director and both will-not-fix verdicts stand.** `compute_form_factor` is defined once (`footprint.py:66`) and **every** other reference in the tree is inside `tests/test_footprint.py` — zero call sites under `openubem/` or `scripts/`, dead in production. The neighbour-bbox recomputation (`context.py:24`) **is** production-reachable (`idf/builder.py:432` plus four `v12_*` runners), but `minimum_rotated_rectangle` is pure and deterministic, so repeating it **cannot** change the shading geometry — **it costs CPU, not correctness.** | Housekeeping | reporting only | ✅ **CLOSED — 2 fixed, 2 re-verified will-not-fix** |
| OPEN-27 | A DESIGN doc names an archetype that does not exist — **inside the coarse-metric definition**; fixable only at the external source | Housekeeping → **spec integrity** | the accuracy metric's own definition | ✅ **re-checked** |
| ~~OPEN-28~~ | ~~**Cross-mode comparisons mix two harvest generations**~~ | **DISCHARGED 2026-08-11** — the remedy it asked for is delivered: **E02 is all five modes on one generation**, so a cross-mode delta now means the method. The confound against the adopted 3rd-generation fixture is also **bounded rather than waved at**: `auto`'s `zoning_strategy` agrees with the adopted run at **100% in every cell** and its `archetype_id` at **96.5–100%**; the other four modes' zoning agreement is 7.6–52.5% **by design**, since those modes force a different zoning approach. 🔴 **Its rule survives the discharge and binds harder: every comparison must state which harvest generation each side came from — E02 is the fourth.** The separate question of what to do about the **already-published** confounded numbers is **CP-M2, an owed ruling**, not this item. |
| OPEN-29 | **Defects last recorded OPEN that this register never adopted** — **measured: 9 of 12 are genuinely still open**, now tracked inside this item. **2026-08-12: the malformed-fatal-test class R06 left behind is finished** — the three `scripts/diagnostics/` sites now use R06's regex, and the class is measured over all 40,800 corpus files: the malformed variants match **0** against ground truth **44**, so that test could never have fired. **No past diagnostic conclusion changes.** A **seventh site never before recorded**, `scripts/validation/phaseE_cpb_fixtures.py:176`, is reported (it can only over-count, and does not on real data). **The item stays open — the other eight defect IDs are untouched.** | Register hygiene | 9 defects; ~~E-LA-21 replicated across **4** harvest scripts~~ **7 known fatal-test sites in total** | ✅ **measured; fatal-test class now closed on live code** |
| ~~OPEN-30~~ | ~~Assigned vintage is never persisted by any harvest~~ | **CLOSED 2026-08-11** — demonstrated on 60/60 E02 manifests, 40,800 rows, 0 nulls, 5 distinct values, `DOERefPre1980` 93.44% vs the ≈92.9% expectation; `la_rural` cross-check vs raw `year_built` reproduces R07 with zero crossover in all five modes. Evidence: `openubem/outputs/comparisons/open30_vintage_distribution.csv`, `extra/MEASUREMENT_open-30-01c_vintage-and-code-state.md`. Director re-derived the full distribution independently. **ID retired.** |
| ~~OPEN-31~~ | ~~Ratified classification changes adopted without a before/after on the labelled fixture~~ | **CLOSED 2026-08-12, formally retired 2026-08-13 on ruling `2h`** — this was a *decision owed*, and the decision was taken: **CP-M3 was ruled obligatory on 2026-08-09**, so a ratified classification change must carry a before/after on the labelled fixture with both numbers recorded. No line of code was ever wrong here. 🔴 **The gate it created is live and is already binding on open work: OPEN-47's office-bin divergence cannot be changed without it**, and as of ruling `2a` (2026-08-13) the fixture side of that gate is **two exams, each with its own threshold** — the old 50-row fixture at ≥0.70 and the tag-rich `labelled_archetypes_tagrich_v2.csv` at its own mark. **Every accuracy figure must name its fixture.** **ID retired.** |
| ~~OPEN-32~~ | ~~the net is unmeasured~~ **CLOSED 2026-08-13 — ID RETIRED.** Net ≈1.12 at the median, but only 12.6% of buildings within ±10% of cancellation and `error_factor` quantized at powers of two — **quote the deciles, never the median** | Reported numbers | `layout_assign` EUI only — **adopted baseline confirmed clear 2026-08-06 (M06)** | 🟢 **closed** |
| ~~OPEN-33~~ | ~~**Archived arcs left 58 dead documentation paths** cited from 23 live documents~~ | **CLOSED 2026-08-12** — the closure condition set on 2026-08-09 was *"the rule is written where the next person archiving an arc will meet it"*, and it is met: the obligatory citation sweep, its resolve-**by-filename** requirement and reason, the three standing exclusions and the ~30-minute cost are now in the head section of `docs/PROJECT_CHECKLIST.md` (10 lines, no journal block touched). Re-sweep of **279** live citations finds **zero** genuine dead paths, and the scanner was **proved non-vacuous** by injecting a broken citation and watching it get caught. One weakness recorded, not smoothed over: **no artifact survives from the 2026-08-06 sweep**, so the 58-path baseline is not verifiable at row level and must be re-measured if ever needed. **Open question left to the user: whether the rule also belongs in `CLAUDE.md`** — until then a fresh session that never opens the checklist will not know it exists. **ID retired.** |
| ~~OPEN-34~~ | ~~**Classification depends on batch composition** — a 3-building run is not archetype-faithful~~ | **CLOSED 2026-08-11** — mechanism was already identified 2026-08-06; the remaining question (*did any published result come from a batch small enough to matter?*) is now **measured, not reasoned**: all 12 adopted cells are whole, `05_results.csv` rows = `01_buildings.gpkg` features in every cell, fleet 8,160. Evidence: `openubem/outputs/comparisons/open34_cell_population_check.csv`. Director recounted `nyc_centre` 738, `la_rural` 149 and the fleet total by hand. 🔴 **The standing consequence survives the closure: a verification run on a subset of a cell must use the whole cell, or state that its archetypes are not fleet-faithful.** **ID retired.** |
| OPEN-35 | **Two fallbacks invent the missing storey count and disagree** — archetype chosen at group-median storeys, geometry built at 1. **2026-08-11: the mechanism is now proved by direct `.eio` evidence, not inferred.** The 2,611-building subpopulation matches its own broken `levels = 1.0` denominator almost exactly in `auto`/`building`/`floor` (**100% within ±1%, by construction** — those modes build zones from `levels`) and **breaks sharply under `layout_assign` (mean 2.3728, only 17.92% within ±1%)**, which assigns storeys from the archetype instead. **The two paths disagree, measured, on 40,800 runs.** **Still open** — the intended-fallback question is a DESIGN decision, not a measurement. | Simulation correctness | **2,611 / 8,160 = 32.00% of the fleet**; 1,031 of them given a mid/high-rise archetype and built at one storey | ✅ **mechanism verified + size measured + simulation-boundary proof 2026-08-11** |
| ~~OPEN-36~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | ✅ **Corrected AT SOURCE — a dated ⚠️ CORRECTION banner now sits in the frozen record itself** (`IMPLEMENTATION_phaseC_ml_imputer.md:849`), on the user's ruling; the false half of the Artifacts line is struck, not rewritten. All five claims re-derived from git by the director. 🔴 **Sharper finding: the record is not wholly false — the 53 tests DID ship; the implementation never did.** ⚠️ **T09b and T11.8/T11.8b were NOT re-verified.** ~~🔴 **A signed completion record describes code that has never existed in any commit** — T07's tests were committed, its implementation never was~~ | Register hygiene → **record integrity** | ~~unmeasured~~ **measured (N13): 596 entries swept, 1 governance gap — T07, the known one**; directly causes E-UTCI-12 | ✅ **verified from git**; **scope now bounded** |
| ~~OPEN-37~~ | ~~**The harvest never fetches `.eio`, so simulated floor area cannot come home**~~ — the cluster keeps the file, the tar that retrieves results does not ask for it. ✅ FIXED 2026-08-10 (R09), five files, 149=149=149 verified. ✅ **CLOSED + ID RETIRED 2026-08-18** — remaining five sites fixed 2026-08-18 (T03), all ten fetch sites now request `.eio`; local E02 census: 40,800/40,800 `.eio` and `.err`, zero empty. `.sql`/`.end` shortfall (874/875) is out of scope, opened separately as **OPEN-53**. | Reported numbers | every fetched fleet, all modes; blocked the simulated-vs-declared floor-area check on **E02's 40,800 runs** — **unblocked before E02's first harvest** | ✅ **verified at the source line + on the cluster; fix manager-verified**; ✅ **2026-08-18: all ten sites fixed, census complete, zero `.eio` gaps** |
| OPEN-38 | ~~**`layout_assign` subsurface geometry defect** — 7 tasks die on EnergyPlus **severe** *"Base surface does not surround subsurface"*, escalating to a two-space fatal~~ 🔴 **PREMISE FALSIFIED 2026-08-11 — item rewritten, still open.** That message is a **`** Warning **`**, not a Severe, at all **8** sites, and **kills nothing**. The item is now two measured defects: **(i)** all 7 `layout_assign` fatals die on **thermal runaway in zone `LAUNDRYROOMFLR1`** (−12,459 / −23,743 / −11,950 / −15,491 / −12,901 / −59,865 / +182,399 °C) — the substituted prototype's laundry room, same zone token as OPEN-06, and **no other cause appears in that mode**; **(ii)** **8** buildings carry malformed door geometry, of which `nyc_rural/way_965718401` **completes successfully and publishes results** from it. All 8 are `layout_assign`; **zero in the other four modes**, verified across all 40,800 `.err` files. | Simulation correctness | (i) 7 fatals, one prototype zone; (ii) 8 buildings, 1 of them publishing | ✅ **both mechanisms measured; the register's stated cause was wrong** |
| ~~OPEN-39~~ | ~~**`set -e` in `submit_fleet_t08.sbatch` skips the trim step and the `task.rc` write on every failed task**~~ | **CLOSED 2026-08-11** — measured on the cluster, read-only: 45 failed E02 tasks orphan **≈2.14 GB** (mean **48.6 MB**/dir vs **449 KB** for successful, ~111×); failed dir has no `task.rc`, its successful array sibling does; replicates outside E02 (`t17_austin_centre_layout_assign`). **Zero of 15 `task.rc` references across 9 scripts uses it as a completion test** — all key on `eplusout.end`. Evidence: `extra/MEASUREMENT_open-39-40_cluster-records.md`. 🔴 **The standing rule survives the closure: never use `task.rc` presence as a completion test.** **ID retired.** |
| ~~OPEN-40~~ | ~~**Eight job arrays were submitted a third time by an unrecorded process**~~ | **CLOSED 2026-08-11 as untraceable — which this item's own text names as the answer.** Independent from-scratch `sacct` reconstruction of all **68** `e02_*` submissions in the window (19 + 8 + 41 = 68, exact) re-confirms the 8 IDs outside both waves; submitted 2026-08-09T23:08:58 → 2026-08-10T00:04:49; `JobName`/`WorkDir`/`User` carry no discriminating signal; remote `.bash_history` predates the whole window (mtime 2026-04-27) and is silent for all three waves alike. **No story was reconstructed from timestamps.** Disposition = the remedy the item already names: **a submission log nobody can bypass.** **ID retired.** |

| ~~OPEN-41~~ | ~~**43 of the 45 fleet failures have no recorded cause**~~ | **CLOSED 2026-08-11** — all **44** fatals now carry a recorded cause, captured from the `** Severe **` line preceding each fatal: 25 *Temperature (low) out of bounds*, 17 `CalcHeatBalanceInsideSurf`, 1 *Temperature (high)*, 1 `CheckForRunawayPlantTemps`. **Every one is a numerical thermal blow-up — none is a syntax, missing-object or licensing failure.** The 45th (`nyc_centre/fast_zone/way_1240348353`) is confirmed to contain no `Fatal` string at all, consistent with `std::bad_alloc`. 🔴 **The `la_rural` concentration is explained and it is not the cell — it is the archetype:** `Warehouse` is 38 of 8,160 buildings (0.47%) yet carries **26 of the 44** fatals, **13.68% vs 0.0443% ≈ 309× relative risk**; all 11 `la_rural` failing buildings are `Warehouse` with `no_floors`. Evidence: `openubem/outputs/comparisons/open41_failure_causes.csv`, `extra/MEASUREMENT_open-41-38_failure-causes.md`; director re-derived the archetype join and the two `la_rural` fatal counts independently. **The remedy question this exposed is OPEN-42, not this item.** **ID retired.** |
| **OPEN-42** | 🔴 **The `Warehouse` population is broken in two measured ways, and one of them reaches the adopted baseline.** **(i) It fails EnergyPlus at ≈309× the fleet rate** — 38 buildings (0.47% of the fleet) carry **26 of the 44** fatals; 13.68% of Warehouse tasks fail against 0.0443% of everything else; 13 distinct Warehouses fail in ≥1 mode; 36 of 44 failures carry `no_floors` and **37 of the 38 Warehouses do**. Failures split auto 8 / floor 8 / fast_zone 10, **zero in `layout_assign`**. **(ii) Six carry a placeholder `footprint_area_m2` of exactly 200.0 m²** (`la_rural` way_472960972/472961034/472961088/472961091/472961171, `la_urban` way_402215469), all flagged `no_floors`, against simulated areas of 4,064–67,330 m² — so **the adopted `auto` mode divides by a denominator wrong by 20.3× to 336.7× on real published buildings.** A widened scan found 16 Warehouses at ≤210 m² fleet-wide; 6 sit at the literal placeholder. **First measurement: made** (this is it). ~~**What is not known:** whether (i) and (ii) are one defect or two — they overlap on 5 buildings but neither contains the other — and whether the 200.0 m² value is a constant in the source data or injected by an imputation path.~~ 🔵 **MEASURED 2026-08-12 (five-item sweep T01–T02) — two of the four unknowns are answered and one published claim above is retracted.** The 200.0 is **not** source data and **not** imputed: it is a declared fallback written by one cited line, `scripts/validation/v12_cell_pipeline.py:659`, which line 664 overwrites **only** on `status == "success"`. Stage 1 is clean — the real footprints (1,173–22,444 m²) are in `01_buildings.gpkg` and match their own `geometry.area`. **Face (ii) is a strict subset of face (i)**: the six placeholder rows and the six failed rows are the same six rows, so this is one defect, and the placeholder is simply what a failure looks like after the reporting stage. 🔴 **Retraction: the claim that six sit "inside the adopted `auto` fleet EUI" is wrong.** All six are `not_simulated` with `total_eui_kwh_m2 = NaN` and are excluded from both sides of the aggregation; **measured impact on 158.0 kWh/m² is exactly 0.000 (0.00 %)** against a baseline reproduced to 158.0298. **OPEN-42 is a reporting defect, not a baseline defect.** **What is still not known, and now blocks closure:** why the six simulations failed — `error_summary` is the **empty string** for all six. | Reported numbers + simulation correctness | 38 buildings; ~~**6 of them inside the adopted `auto` fleet EUI**~~ **0 inside the fleet EUI; 6 published rows carry a false area** | ✅ **both faces measured on all 40,800 runs**; ✅ **placeholder traced; fleet impact measured at zero**; ~~❓ **why the six failed is unrecorded**~~ ✅ **2026-08-13: cause found — all six die of runaway zone temperatures, and all six run clean under whole-building zoning, so this is a zoning-method defect. Open only on *why one mode survives*.** ✅ **2026-08-18 (T05): `.eio` read — positional pattern confirmed (15/16 fail on topmost floor, geometry byte-identical to non-fatal siblings below); two candidate statistics killed by a required 20-building background control; "not determinable from `eplusout.eio`" for the deeper question. Sharpens, does not close.** |
| ~~**OPEN-43**~~ | **CLOSED 2026-08-12 on the user's ruling, formally retired 2026-08-13 on ruling `2h`. The headline is the POOLED figure — `157.1 kWh/m²` = total simulated energy ÷ total simulated floor area over all 8,154 successful buildings — and it must be restated with that definition every time. Do not re-ask which aggregation the headline uses.** Restated in 13 live files; archived trees left as record. ⚠️ **What the closure does NOT discharge, because it belongs to other items:** the published figure is still one HEAD cannot reproduce end to end (**OPEN-48**), and the re-run's **159.2157 is not a competing headline** — it is the same model run through **OPEN-49**'s `wwr` defect and survives only as evidence inside that item. ~~The original finding, kept for the record:~~ 🔵 ~~**The published fleet EUI is a mean of cell means, not a fleet mean.**~~ Found 2026-08-12 by the director while re-deriving the adopted headline two ways instead of one. Over the same 8,154 success rows: per-cell area-weighted means averaged across the 12 cells **weighted by building count** = **158.0298** — *this is the published 158.0*; weighted by success count = 158.0557; unweighted = 160.0993; **pooled `Σ(EUI × area) / Σ(area)` over all 8,154 at once = 157.0552.** The headline therefore sits **≈1.0 kWh/m² above** the pooled figure purely from the choice of aggregation, and the count-weights include the six buildings that produced no energy. Neither number is wrong — **but the published figure has never been described as a mean of cell means anywhere in this project**, and a reader will assume the pooled definition. `openubem/results/aggregator.py` is per-cell only, so the fleet roll-up lives outside it and its author and intent are untraced. **First measurement: made. Decision owed by the user: which definition the headline should use. Do not restate 158.0 before that ruling.** | Reported numbers | **every published fleet-level EUI figure**, including the headline and every board that quotes it | ✅ **all four aggregations computed on the full adopted run**; ❓ **intent untraced** |
| ~~OPEN-44~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | ✅ **0 failed · 1,859 passed · 55 skipped · 0 errors** (CP-1 signed). All 45 red nodes now skip with a reason naming their item; **passed did not move**, so nothing was deleted or downgraded. 🔴 **A skip is a debt, not a fix — the suite is honest, not more capable, and 14 of the 45 wait on OPEN-17.** ~~🔴 **The test suite has 70 failures and 36 errors, and this is the first time anyone could count them.**~~ Opened 2026-08-12 from the side effects of OPEN-13's fix. Full run: **70 failed / 1,822 passed / 10 skipped / 36 errors / exit 1 / 26m47s** — E-UTCI-12's collection abort had made this number unobtainable, so **every past claim that "tests pass" covered an unknown subset**. **61 of the 106 live in `docs/docs_DONE/…/elevators/scripts/tests/`** — `docs/` holds **30 `.py` files, 5 of them tests**, against the hard rule *no `.py` under `docs/`, ever*; two are byte-identical duplicates of `tests/` files and **three have drifted from their twins**. 🔴 **Roughly half the red is artifact-dependence, not broken logic**: **51 `FileNotFoundError`** from tests asserting an output file exists on disk, ~36 setup errors from a missing `synthetic_10_gdf` fixture, 5 `AttributeError` on a never-existent `config.IMPUTE_DEBIAS…`, 8 elevator-column `KeyError`s. **Do not report this as "70 broken tests."** ⚠️ The `IMPUTE_DEBIAS…` group is E-UTCI-12's shape a second time — **re-check OPEN-36's "one governance gap" bound before closing it.** **First measurement: made. Next step: triage the 44 `tests/` failures into real defects vs artifact-dependence — not yet done, and must not be guessed.** | Test integrity → **record integrity** | the whole suite; **every past "tests pass" claim**; ~~unknown overlap with shipped code~~ **measured overlap with shipped code: zero** | ✅ **counted and located**; ~~❓ **not triaged**~~ ✅ **2026-08-13: `tests/` fully triaged at HEAD and independently reproduced node-for-node — 26 failed / 1,857 passed / 10 skipped / 19 errors; 31 artifact-missing, 14 unfinished-wiring (→ OPEN-17, OPEN-36), 0 real defects** |
| ~~OPEN-45~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | ✅ **Sweep re-run, zero live defects, no code changed — the correct outcome, named in advance.** The only single-space literal left under `openubem/` is inside `err_parse.py`'s own docstring describing the bug. ⚠️ The CSV on disk was **stale** until regenerated. ~~🔴 **The pipeline matched `** Severe **` with one space, so `error_summary` was empty for all 8,160 buildings** — not only the failures. Opened 2026-08-12. ✅ **Fixed where authorised 2026-08-12 (night):** a shared whitespace-tolerant helper `openubem/results/err_parse.py` (`SEVERE_RE`/`FATAL_RE`/`WARNING_RE`, `first_severe`, `count_severe`, `has_fatal`, 16 tests) now backs `scripts/validation/v12_cell_pipeline.py:625` and `scripts/cluster/make_manifest_from_cluster.py:47`; **load-bearing one-space sites 2 → 0**, director-verified from both diffs. 25 sites classified in `openubem/outputs/comparisons/open45_severe_literal_sweep.csv` (15 spent one-off scripts, 8 already correct). 🔴 **This item also corrected a project-wide belief: the "two spaces" rule is half wrong.** Census of every marker in all **64** real `.err` files: `** Warning **` one space both sides (**4,881**), `** Severe  **` one before / two after (**37**), `**  Fatal  **` two both sides (**1**) — **a two-spaces-both-sides literal misses `Severe` exactly as badly as the one-space literal did.** 🔴 **Why it stays open — two live sites, both flagged rather than edited because they were outside the executor's write-set:** `tests/test_sim_integration.py:171` matches `"**  Severe  **"` and therefore **0 of the 37** real Severe lines; `openubem/simulation/runner.py:140` is a bare `"**  Fatal  **"` literal rather than the tolerant helper. ⚠️ **A further gap in `SEVERE_RE` itself was self-disclosed by the OPEN-42 executor on 2026-08-13, confirmed real on a live file by the director, and routed here rather than to a new ID.~~ ✅ **Both "two live sites unfixed" are fixed at HEAD — verified 2026-08-13: `runner.py` and `test_sim_integration.py` both import from `err_parse` now.** | Reported numbers → **failure diagnosis** | **all 8,160 buildings' `error_summary`**; every future `.err` scan | ✅ **CLOSED 2026-08-13 — zero live defects, director re-derived by direct grep of the live tree** |
| **OPEN-46** | ⚠️ **The elevator end-use breakout existed only in the archived arc's copy of the code, never in the live tree.** Opened 2026-08-12. 🔴 **The premise's alarming half was REVERSED on audit the same night — read this before quoting the item:** elevator energy **is** in the adopted run and **is** inside the published `157.1 kWh/m²`. All 12 `phaseE_elevrb/*/05_results.csv` already carry `elevators_eui_kwh_m2` and `gwp_elevators_kgco2_m2`; **3,561 of 8,160 rows non-zero, Σ = 12,508.8 kWh/m²**; in `nyc_urban` exactly **87** non-zero — precisely the 87 elevator-eligible buildings; against the pre-elevator `phaseE` run the **median of `|Δtotal_eui − elevators_eui|` is exactly 0**. ⚠️ **Why both the executor and the director first got this wrong, recorded because the lesson transfers:** both read a flat `equipment_eui_kwh_m2` as absence — **flat is what de-folding produces.** **Check the invariant a transform preserves (the total), not the column it moves energy between.** ✅ **The reporting path is now restored and gated in the live tree** (parser, outputs, carbon, aggregator; director re-derived the invariant on a different SQL than the executor used — 12 keys bit-identical, total unchanged). 🔴 **The genuinely broken part was larger than the item as opened and was split out as OPEN-48.** ⚠️ Three of five archived test twins had the expectation **removed** rather than the feature added. | Reported end-uses (**not physics**) | reporting only — **the published fleet figure is unaffected and was never missing elevator energy** | ✅ **premise measured and reversed; breakout implemented and gated; total proven invariant** |
| **OPEN-47** | ⚠️ **The office size-tier thresholds had no traceable external source, and this project's own deep-research document contains a fabricated citation.** Opened 2026-08-12. ✅ **The first half of the title is now wrong — a source WAS found:** the thresholds trace to **Chen, Hong & Piette (2017), *Applied Energy* 205, 323–335, Table 1** (DOI `10.1016/j.apenergy.2017.07.128`), **director-verified from the PDF itself** (pages 19–20 carry the three bins verbatim) and Crossref-checked, precisely because this task's predecessor fabricated exactly this kind of claim. **Hong et al. (2015) — credited by both the code comment and `RESULT_I02` — contains zero occurrences of either number**, 13 pages searched. ⚠️ **Caveat that must travel with the finding: Chen 2017's table is CityBES's own case-study classification, not a citation to an external standard** — it is not evidence of a DOE / PNNL / ASHRAE / CBECS lineage, and ASHRAE 90.1 is recorded as a **retrieval failure (paywalled), not** as "not found." 🔴 **Reason it stays open — a substantive divergence from the now-known source: the source's rule is area AND floor count** (`<2322 m² and ≤3 floors`, `2322–9290 m² and ≤5 floors`, `>9290 m² or ≥6 floors`) **while `openubem/semantic/building_classifier.py:175-177` tests area only.** Any change here is a classifier change and is therefore gated by CP-M3 (OPEN-31) — **and that gate depends on the unanswered fixture-threshold ruling 2a, so 2a probably has to be settled first.** ⚠️ The same citation audit found **a second fabricated DOI** (Sun et al. 2021 given as `10.1016/j.enbuild.2020.110586` — director-checked **HTTP 404**; the real one is `…110603`) and **a systemic wrong-locator pattern** across every Deru et al. (2011) row. | Classification correctness → **citation integrity** | the office bins for every classified building; **every citation in `RESULT_I02`** | ✅ **source found and director-verified from the PDF; divergence located at the line**; ❓ **divergence not adjudicated — needs a ruling, gated behind 2a** |
| **OPEN-48** | 🔴 **The adopted baseline run cannot be reproduced from this repository.** Opened 2026-08-12 by **auditing OPEN-46's reversal**, not by running a task — the sixth consecutive pass in which this register grew that way. The adopted `phaseE_elevrb` run was produced by code that is not in this repository: live `builder.py` never called `assign_elevators` (`git log --all -S` empty; the only commit ever to touch the string, `ef19141`, added the **archived** copies plus three orphan live files), and `parser.py` / `outputs.py` / `carbon.py` had no elevator column, meter or GWP term — **yet the adopted outputs carry all of it.** The wiring existed in the working tree at run time and **was never committed.** ✅ **State the reassurance first: this is a provenance defect, not a physics defect — `157.1 kWh/m²` is correct and complete, elevators included.** ✅ **Half of it is discharged 2026-08-13:** ruling 2d ("restore the wiring, re-run the fleet") was executed, and the twelve-cell re-run **regenerates the elevator column exactly — 3,561 non-zero rows on both sides, same 8,160 buildings, same 6 known failures.** 🔴 **Why it stays open:** the re-run lands at **159.2157 vs the adopted 157.0552**, and the gap is **not** elevators but **OPEN-49**'s `wwr` re-randomisation. The user ruled 2026-08-13 to **keep 157.1**, so **the published figure remains one HEAD cannot reproduce end to end, and this provenance caveat stays live until OPEN-49 is fixed and the fleet is re-run a third time.** | Reproducibility of **every published number** | the whole adopted baseline; **every figure this project publishes** | ✅ **measured on both sides of the tree; elevator half discharged by re-run**; ❓ **end-to-end reproduction blocked on OPEN-49** |
| **OPEN-49** | 🔴 **One reclassified building re-randomises the windows of every unidentified building in its cell.** Opened 2026-08-13 on the user's ruling (2f), found by the cause analysis of OPEN-48's re-run — **the seventh consecutive pass in which this register grew by checking a result rather than by running a task.** For buildings the classifier cannot identify, `wwr` is drawn **as one vectorised block sized by the count of unidentified buildings, with bounds taken from whichever archetypes happen to be present** (`openubem/semantic/__init__.py:229`, seeded by one RNG per run at `:297`). **`wwr` sets window head and sill height, which sets solar gain**, so buildings nobody touched — not reclassified, not re-fetched, not edited — move by up to **±300 kWh/m² individually**. 🔴 **The pipeline is reproducible only while its inputs never move** — a stronger and more damaging statement than OPEN-48's uncommitted wiring. **Measured on the twelve-cell re-run, not inferred:** all **4 of 12** cells whose `archetype_id` set changed **also moved in EUI** (`nyc_centre` +3.53, `austin_centre` +1.76, `la_centre` +1.60, `la_urban` +1.21); all **8** whose archetypes matched reproduced to **±0.07** or better; **0 cells on the wrong side of the split**. IDF diff: **6 cosmetic lines** for reproducing buildings vs **hundreds of window-vertex Z-coordinate lines** for moving ones. ✅ **Confirmed not to be nondeterminism** — a repeat run on unchanged inputs is byte-identical at the IDF stage and agrees to 0.00836 kWh/m² at the results stage. **Fleet effect: pooled 157.0552 → 159.2157 (+2.16, +1.4%)** — ⚠️ **retained as evidence inside this item only; 159.2157 is NOT the fleet figure and must never be restated as one.** | Simulation correctness → **reproducibility** | **every `OpenUBEMUnknown` building in any cell where any classification moves**; blocks OPEN-48 from closing | ✅ **mechanism located at the line; effect measured on all 12 cells; nondeterminism excluded**; ❓ **no remedy chosen** |
| ~~OPEN-51~~ | ~~🔴 **One defect ID, `E-LA-16`, is used for two different failure signatures.**~~ ✅ **ADJUDICATED + CLOSED + ID RETIRED 2026-08-18 (T02).** Verdict: `E-LA-16` names the cooling-coil-design-UA/cooling-tower-UA-autosize family (`PLAN_structural-fixes_implementation.md:279`), corroborated by raw `.err` evidence on the three named buildings in the current E02 harvest (23/21/16 true Severes, corrected from an initial miscounted 26/24/19). The code comment's `CheckWarmupConvergence` grouping was a documentation error, now corrected. Knock-on: OPEN-09's C06 "five inherited log entries" narrows to four (E-LA-14/18/19/23); OPEN-29 unaffected. | Register integrity → **evidence provenance** | 1 defect ID; **OPEN-29's closure**; the reach of OPEN-09's C06 finding | ✅ **collision located, all four sources cited**; ✅ **2026-08-18: adjudicated, code comment corrected, knock-ons recorded** |
| **OPEN-52** | 🔴 **A fixed `--basetemp` makes two concurrent pytest sessions delete each other's temp directories.** Opened 2026-08-13 by the director during T03, diagnosing a failure that would not reproduce. `pyproject.toml:54` pins `addopts = "--basetemp=.pytest_tmp"` — **fixed and repo-relative, not per-session** — and pytest clears that root at session start. **Observed, not theorised:** executor reported `1 failed, 6 passed in 12.67s` on `tests/test_sim_integration.py`; four sequential director runs gave **`7 passed` at 66.38 / 65.99 / 66.57 / 66.68s.** The failure was a vanished `step3` directory under `to_parquet` (`openubem/idf/builder.py:696-707`); three agents had been dispatched in parallel, all running pytest. The 12.67s-vs-66s gap corroborates it — the wall-time-dominant test never reached IDF generation. 🔴 **Recorded as a MANAGER error, not an executor error:** the report was accurate; the director parallelised over a configuration that cannot support it. **Mitigation in force is a discipline, not a fix** — every dispatch prompt now forbids concurrent pytest, which depends on the director remembering. ⚠️ **Anyone reading a non-reproducing test failure in this repo should check this item first.** **Bearing on any published number: NONE** — it corrupts test runs, never simulation output. | Test integrity → **trust in executor reports** | **every concurrent pytest session repo-wide**; every audit that reads a test result | ✅ **root cause at the line; non-reproduction measured 4× sequentially**; ❓ **no remedy chosen — why the path was pinned is unestablished**; 🔴 **2026-08-18 (T01): STAYS OPEN, sharpened to two sub-questions — (a) collision reproduced (real, remedy not yet applied), (b) a second, newly-found OS-level lockout on `pytest-of-o_iseri` blocks (a)'s specified remedy. Choosing a remedy shape is an owed user ruling, not a next measurement.** |
| **OPEN-53** | 🔴 **874/875 E02 harvest directories are missing `.sql`/`.end`, concentrated in two Austin sub-cells.** Opened 2026-08-18, found as a byproduct of T03's `.eio` census run for OPEN-37. Against **40,800** `n_building_dirs` and **40,800** `.eio`/`.err` (both exact, zero empty), `.sql` = **39,926** and `.end` = **39,925** — short by 874/875. Every short directory still carries its `.eio` and `.err`, so this is **not** OPEN-37's problem — it is an incomplete-simulation signature. **874 of 875 concentrate in `austin_suburban_fast_zone`/`austin_suburban_floor`; the remaining one is `nyc_centre_fast_zone`.** No `.err` content from these specific directories has been read yet. | Reported numbers → **run completeness** | up to 875 E02 harvest directories, two Austin sub-cells + one NYC directory | ✅ **census counted, location established**; ❓ **cause untraced — genuine failure vs harvest-timing artifact not distinguished** |
| ~~OPEN-50~~ ✅ **FIXED + ID RETIRED 2026-08-13** | ✅ **The fixture now writes to `tmp_path_factory`, not to `tests/fixtures/`.** Proved by hash + mtime taken either side of a **24-minute** full suite run — **neither moved.** 🔴 **One user action outstanding: `git restore` the still-dirty working copy of that fixture.** ~~🔵 **Running the test suite silently rewrites a checked-in fixture.**~~ Found 2026-08-13 by the director during the CP-1 `git status` audit — a sixth item found by auditing an output, not by a task that went looking. `tests/test_building_classifier.py` opens `tests/fixtures/synthetic_30_archetype_coverage.gpkg` read-write, so GDAL/SQLite stamps `last_change` on every run. **Reproduced in isolation from a clean tree** (restore → 131 tests pass → fixture dirty). ✅ **Scope proved by hashing every table's full row set on both copies: all tables identical except the 1-row `gpkg_contents`, and within it exactly one field — `last_change`.** The 11,400 differing bytes are SQLite page churn, not content. 🔴 **The real cost: one such rewrite is already committed — `6aeebb0` carries `Bin 106496 -> 106496` on this fixture, so a test artifact entered the history looking like a deliberate change.** ⚠️ **Standing consequence: a dirty copy of this fixture after a test run is expected and must never be read as an executor writing outside its authorised set — verify by row hash, not byte diff — and must not be committed.** | Repo + audit-trail hygiene | 1 fixture; **every future `git status` audit of an executor** | ✅ **reproduced in isolation; scope measured to one metadata field; prior accidental commit identified** |

**Next free defect ID: E-LA-42** (verified by full sweep 2026-08-05, OPEN-05). **Next free UTCI defect
ID: E-UTCI-17** (same sweep; stated in no other document). ~~**Next free item ID: OPEN-41.**~~
~~**Amended 2026-08-11: OPEN-41 was taken on 2026-08-10 (§1's later amendment) and its table row was
missing here — added above. Next free item ID: `OPEN-42`.**~~
**Amended 2026-08-11 (later, the E02 audit and closure pass): `OPEN-42` was taken by the `Warehouse`
population defect — row added above in the same edit that opened it, so the missing-row failure of
2026-08-10 is not repeated. Next free defect ID `E-LA-42` and next free UTCI defect ID `E-UTCI-17`
are both unchanged — this pass opened no defect ID, only an item.
~~**Next free item ID: `OPEN-43`.**~~****
~~**Amended 2026-08-12 (the five-item sweep, T02 audit): `OPEN-43` was taken by the fleet-aggregation
finding — row added below in the same edit that opened it. No defect ID was opened; `E-LA-42` and
`E-UTCI-17` are unchanged. Next free item ID: `OPEN-44`.**~~

**Amended again 2026-08-12 (later, T04 audit): `OPEN-44` was taken too** — the first complete run of
the test suite, which OPEN-13's own fix had just made possible, returned **70 failed / 1,822 passed /
36 errors**. **Two items opened in one day, both by auditing rather than by running a task.** No
defect ID was opened by either; `E-LA-42` and `E-UTCI-17` are unchanged.
~~**Next free item ID: `OPEN-49`.**~~ *(Corrected 2026-08-12 night: this line had gone stale at `OPEN-45` while the director prompt was already at `OPEN-48`. OPEN-45, OPEN-46 and OPEN-47 were opened on 2026-08-12 evening and OPEN-48 on 2026-08-12 night.)*

**Amended 2026-08-13 (T04 of the three-rulings sweep): `OPEN-49` was taken by the `wwr` re-randomisation defect — its §8 section was written in the same edit that opened it, on the user's ruling of 2026-08-13. No defect ID was opened; `E-LA-42` and `E-UTCI-17` are unchanged. ~~**Next free item ID: `OPEN-50`.**~~

🔴 **Register-hygiene defect found in the same CP-1 audit, recorded rather than quietly patched: the table above jumps from `OPEN-44` straight to `OPEN-50`. Rows for `OPEN-45`, `OPEN-46`, `OPEN-47`, `OPEN-48` and `OPEN-49` were never added when those items were opened, even though all five have full §-sections.** This is the same failure the 2026-08-11 amendment below says was "not repeated" — it was, five times. **The sections are the authority; the table is incomplete and must not be used as the item census until the five rows are written.** No content is lost.
>
> ✅ **REPAIRED 2026-08-13 (same day, director), on the user's instruction to continue.** All five rows
> — `OPEN-45`, `OPEN-46`, `OPEN-47`, `OPEN-48`, `OPEN-49` — are now written into the §1 table, in ID
> order between `OPEN-44` and `OPEN-50`, **each one composed from its own §-section rather than from
> any summary**, and each carrying the same five columns as every other row (item / theme / blast
> radius / evidence). 🔴 **Two things deliberately preserved rather than smoothed in the transfer:**
> OPEN-46's row leads with the **reversal** of its own title, not with the title, because the title's
> alarming half is false and the published figure was never missing elevator energy; and OPEN-49's row
> carries `159.2157` **only** as within-item evidence with the standing prohibition attached, never as
> a fleet figure. **The table and the sections now agree on OPEN-45 … OPEN-49.** No section text was edited.
>
> 🔴 **A SECOND census defect was exposed by the repair, and it is recorded here rather than patched,
> because patching it would mean retiring three IDs on the director's own authority.** With the five
> rows written, the §1 table now carries **38 live (non-struck) rows** — `OPEN-01, 03, 04, 06, 07, 08,
> 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 24, 26, 27, 29, 31, 32, 35, 36, 37, 38, 42, 43,
> 44, 45, 46, 47, 48, 49, 50` — against a §1 header that says **35 tracked items**. **The gap is
> exactly three: `OPEN-04`, `OPEN-31` and `OPEN-43`.** The 2026-08-12 count arithmetic in §0 states
> *"32 − 3 closed (OPEN-43, OPEN-31, OPEN-04) + 3 opened (OPEN-45, OPEN-46, OPEN-47) = 32"*, and every
> count since — 33, 34, **35** — is built on that subtraction. **But none of the three is marked closed
> anywhere else:** their §-sections are headed `✅ explained`, `✅` and `🔵 OPENED 2026-08-12`
> respectively, **not `CLOSED … ID retired`**; their table rows are not struck; and none of the three
> IDs appears in the §1 header's retired list. ⚠️ **So the published item count of 35 rests on a
> closure that only the arithmetic line records.** Each of the three has a plausible closure basis —
> OPEN-04's cause was falsified and re-explained, OPEN-31's CP-M3 decision was ruled obligatory
> 2026-08-09, OPEN-43's aggregation question was ruled 2026-08-12 (pooled, `157.1 kWh/m²`) — **but a
> plausible basis is not a recorded closure, and this register's own rule is that the sections are the
> authority.** ~~🔴 **Until this is settled, quote the table's 38 live rows and this note together;
> do not quote 35 as an audited census.** **Owed to the user as a small ruling: retire the three IDs
> formally, or reopen them in the count.** No content is lost either way.~~
>
> ✅ **RULED AND EXECUTED the same day (2026-08-13, ruling `2h`): retire the three formally.** The user
> was given both sides — retire (count stays 35) or reopen in the count (count becomes 38) — and chose
> to retire. **Executed in the same turn:** a closure block written into each of the three §-sections
> stating *why* it closes and *what survives* the closure, the three table rows struck with the same
> text, the three IDs added to the §1 header's retired list (ten → **thirteen**), and the live-row count
> re-counted from the table: **35, matching the header.** 🔴 **Three consequences were deliberately
> carried forward out of the closures rather than buried with them:** OPEN-04 leaves behind
> *`92.0%` is unreproducible* and *the old 50-row fixture is never edited*; OPEN-31 leaves behind
> *CP-M3 is obligatory and now spans two exams with two thresholds, so every accuracy figure must name
> its fixture*; OPEN-43 leaves behind *the headline is pooled `157.1 kWh/m²` and `159.2157` is never a
> fleet figure*. **A closed item's constraints do not close with it.**

**Amended 2026-08-13 (CP-1 of `PLAN_two-measurements-2026-08-13.md`): `OPEN-50` was taken by the test-suite fixture-mutation defect, found by the director during the CP-1 `git status` audit and opened with its §10 section in the same edit. No defect ID was opened; `E-LA-42` and `E-UTCI-17` are unchanged. ~~**Next free item ID: `OPEN-51`.**~~

**Amended 2026-08-13 (CP-2 of `PLAN_five-more-items-2026-08-13.md`): two items opened, both found by
the director rather than by a task's stated question. `OPEN-51` — the `E-LA-16` two-signatures-one-ID
collision, surfaced by T05. `OPEN-52` — the fixed-`--basetemp` concurrent-pytest hazard, surfaced by
T03 while diagnosing a failure that would not reproduce; **recorded as a manager error.** Both have
§10 sections. No defect ID was opened; `E-LA-42` and `E-UTCI-17` are unchanged.
~~**Next free item ID: `OPEN-53`.**~~

**Amended 2026-08-18 (T06 of `PLAN_five-items-2026-08-18.md`): `OPEN-53` was taken by the E02 harvest
`.sql`/`.end` shortfall, found as a byproduct of T03's `.eio` census and given its own §10 section in
the same edit. No defect ID was opened; `E-LA-42` and `E-UTCI-17` are unchanged.
**Next free item ID: `OPEN-54`.**

> **Amendment 2026-08-05.** OPEN-28 added, found while auditing the `layout_assign` documentation
> surfacing work (`layoutAssigner/PLAN_docs-explanation-surfacing.md`, closed the same day). It had
> existed only as a figure caption, never as a tracked item. **It bundles with OPEN-01 and OPEN-02 —
> see OPEN-28's own section: one fleet re-run closes all three.**

> **Amendment 2026-08-05 (measurement pass).** OPEN-30, OPEN-31 and OPEN-32 added, each surfaced by
> measurements M01–M05 while re-verifying OPEN-01–04 and OPEN-28 (see each item's own section and
> §9's rewritten pattern 1). **Next free item ID: OPEN-33.**

---

## 2. Theme A — Integrity of the numbers we publish

This theme is first because it is the only one that can make *already-published* results wrong rather
than merely incomplete.

### OPEN-01 — The EUI denominator is wrong for every non-`applied` building — ✅ **CLOSED 2026-08-17 — remedy implemented, all three ruling-6 deliverables landed**

> ✅ **CLOSED 2026-08-17.** T05–T07 of `PLAN_open-49-and-open-01-2026-08-13.md` delivered the three
> things ruling 6 named as owed to close this item: **(1)** a plan doc implementing the swap — this
> plan, T05; **(2)** a before/after per-building comparison for all five modes — T07, below; **(3)** the
> two ruling-6 corrections carried into the code that publishes EUI — the `building`-mode
> internally-consistent-not-representative comment and the floor_area-resolution comment, both at
> `openubem/results/parser.py::_compute_eui` (docstring, immediately above the `floor_area` parameter)
> and `openubem/results/aggregator.py::compute_neighbourhood_summary`.
>
> **The swap, as landed.** `openubem/results/parser.py`: new `resolve_simulated_floor_area(sql_path,
> footprint_area, num_floors)` returns `(floor_area_m2, provenance)` — `"eio_simulated"` (Σ `Floor Area
> × Zone Multiplier × Zone List Multiplier` from `sql_path.parent / "eplusout.eio"`, over zones with
> `Part of Total Building Area = Yes`) when that file parses to a well-formed, positive area;
> `"footprint_fallback"` (`footprint_area × num_floors`) otherwise — missing or malformed `.eio` never
> raises. `parse_eio_zone_area()` is lifted verbatim from `scripts/analysis/e02_t04_floor_area_audit.py:56`
> (a code comment says so) so the two can never silently disagree. `parse_building()` resolves this once
> per building, before any parse attempt, and carries `floor_area_m2`/`floor_area_provenance` through
> both the success and every failure return path — a failed-parse row still records which denominator
> would have applied. `_compute_eui()` takes an optional `floor_area` override (defaulting to the old
> footprint×floors computed from `row` when omitted) so all pre-existing direct tests of that function
> are unaffected — only `parse_building()`'s call site supplies the new value.
> `openubem/results/aggregator.py`: `compute_neighbourhood_summary()` now reads `floor_area_m2` from the
> joined results frame (added to `_STEP5_COLS`) instead of re-deriving `footprint_area_m2 ×
> derive_num_floors()` itself, falling back to that same computation per-row only where the column is
> absent or NaN (e.g. synthetic GeoDataFrames built directly in existing tests, never routed through
> `parse_building()` — this keeps every pre-existing aggregator test's expected numbers unchanged).
>
> **Reproduction (director's CP-2 spot-check, independently re-derived):** `la_urban/way_401904735`
> (`MidriseApartment`, 3 storeys) — `resolve_simulated_floor_area()` on the real harvested
> `eplusout.sql`/`.eio` returned **7,401.680000 m²** under `layout_assign` (`error_factor` =
> 7401.68 / 5,551.362295 = **1.333309**, matching the director's **1.33331 at 0.0018% off** and the
> existing `open01_denominator_audit.csv` row exactly) and **1,850.45 m²** under `building`
> (error_factor 0.333333, matching `4/3`⁻¹ / the audited 0.5000-median story). No disagreement between
> the lifted parser and the audit's parser was found; T05 did not STOP.
>
> **T06** (`tests/test_results_denominator.py`, 7 tests) pins the three named cases — `.eio` present and
> well-formed (multiplier-aware area used, `provenance="eio_simulated"`, and a cross-check that the
> reported EUI columns actually scale by the area ratio, not just the metadata column); `.eio` absent
> (fallback, `provenance="footprint_fallback"`, no exception); `.eio` present but malformed
> (`header_found_zero_rows` → fallback) — plus a failed-parse case and a `sql_path=None` case. All 7
> pass on current code; all 7 fail genuinely when every expected provenance string is mutated to a
> wrong value (non-vacuity proof, reverted after confirming).
>
> **T07's five-mode before/after** (`openubem/outputs/comparisons/open01_denominator_swap.csv`,
> 40,800 rows; `_summary.csv`, 5 rows; `extra/MEASUREMENT_open-01_denominator-swap.md`) reproduces every
> one of the five targets exactly:
>
> | mode | median error factor | % within ±1% | reproduced |
> |---|---:|---:|---|
> | `auto` | 1.0000 | 99.63% | yes |
> | `floor` | 1.0000 | 98.43% | yes |
> | `fast_zone` | 1.0000 | 94.80% | yes |
> | `layout_assign` | 0.9999 | 15.37% | yes |
> | `building` | 0.5000 | 39.94% | yes |
>
> Join: 8,160 matched / 0 unmatched (error factor) per mode; 8,154 buildings per mode have a real
> `total_eui_kwh_m2` to derive an EUI shift from (the standing fleet successful-building count). EUI
> shift is `new_eui = old_eui / error_factor` — exact arithmetic on the one measured EUI value
> (`auto`-mode), not a claim that the other four modes were re-parsed. **Deciles, not the median alone**
> (🔴 rule, since `error_factor` is quantised and log-symmetric): `auto`/`floor`/`fast_zone` sit within
> thousandths of a percent at every decile; `building` splits sharply — ~30% near 0% shift
> (single-storey buildings), the rest clustered near +100%/+200%/+400% (multi-storey `building`-mode
> buildings, matching "one simulated storey" exactly); `layout_assign` spreads from −75% to +217%,
> consistent with its 15.37% within-±1% figure. Full table in the `.md`.
>
> ⚠️ **The adopted baseline does not move.** `auto` measures 1.0000 median / 99.63% within ±1%, so **the
> published fleet EUI of `157.1 kWh/m²` pooled is unchanged by this remedy** — nothing in T05–T07
> restates or re-derives the fleet figure. And `building` mode is now **internally consistent with what
> it simulated, not physically representative** of the real multi-storey building (fact 8) — the code
> comment at `parser.py::_compute_eui` says so at the site that matters.
>
> **What this closure does not do.** It does not fix `building` mode's simulation (one storey only) —
> fixing the simulation was offered in ruling 6 and not taken; that door stays open, tracked nowhere by
> ID because no defect ticket was ever opened for it. It does not touch OPEN-48 (the fleet re-run to
> reproduce `157.1` end to end with any other change) — that is a separate item and ruling 4 declined a
> third fleet run in this plan specifically.



> **Amended 2026-08-11 (T03 + T04 of `PLAN_e02-audit-and-closure.md`; CP-2 director-signed by
> independent re-derivation). This item does NOT close. Do not report it as closed.**
>
> **The measurement this item has waited for since it was opened now exists.** All **40,800** `.eio`
> files parsed — **0 parse failures** — for the multiplier-aware simulated floor area
> (Σ `Floor Area × Zone Multiplier × Zone List Multiplier` over zones marked
> `Part of Total Building Area = Yes`), joined to the declared `footprint_area_m2 × levels`.
> **Join integrity: 8,160 matched, 0 unmatched in both directions, in every one of the five modes.**
>
> | mode | median error factor | mean | range | within ±1% |
> |---|---|---|---|---|
> | **`auto`** — the adopted baseline's mode | **1.0000** | 1.0592 | 0.9998–336.65 | **99.63%** |
> | `floor` | 1.0000 | 1.0593 | 0.4953–336.65 | 98.43% |
> | `fast_zone` | 1.0000 | 1.0631 | 0.8390–336.65 | 94.80% |
> | `layout_assign` | 0.9999 | 1.4977 | 0.0557–353.998 | **15.37%** |
> | 🔴 **`building`** | **0.5000** | 0.6287 | 0.0095–112.22 | **39.94%** |
>
> **(a) `layout_assign` non-`applied` (n=6,939):** median **0.9474**, range 0.0557–10.0008, **2.05%
> within ±1%**. ⚠️ **This does not reproduce `open01_denominator_factors.csv`'s inferred figures**
> (median 2.0, 12.6% correct). Both agree the defect is large and the assertion rarely holds; they
> **disagree on central tendency and shape**. The E02 figure is a direct measurement on 40,800 runs and
> the older one is an inference — but the disagreement is **recorded, not reconciled**, because
> reconciling would mean re-deriving one from the other. **The `applied` control holds at median
> 1.0000**, so the join is sound.
>
> **(b) fleet-wide, all five modes — and the answer is not the one this item predicted.** 🔴 **The
> adopted `auto` path divides by the right area: median 1.0000, 99.63% within ±1%.** But the audit
> found a *different* mode broken by construction: **`building` mode simulates exactly one storey.**
> Its simulated area ÷ **bare `footprint_area_m2`** (no `levels`) is **median 1.000000, 98.43% within
> ±1%** — the mode builds one zone of one storey while the published denominator multiplies footprint
> by `levels`, whose fleet median is 2. **The 0.5000 is the storey count, not noise.** This is the
> first fleet-scale denominator measurement any mode has ever had, and **one of the five is wrong for a
> reason nobody had looked for.** ⚠️ `building` mode was recorded *"verified sound at HEAD"* by E01c on
> 2026-08-06 — **that verification did not cover the denominator**, and the two statements must be read
> together.
>
> 🔴 **(c) — and this is why the item stays open. The one-code-state question cannot be proved from the
> artifacts that exist.** Positive evidence is real: one manifest schema across all 60 `(cell, mode)`
> pairs, and all 60 written inside a single continuous **111-minute** window
> (2026-08-09 21:03:01–22:54:38) with no gaps or out-of-order writes. But **no commit hash or
> code-version stamp was recorded anywhere at generation time**, and **25 of the 60 pairs** (`nyc_centre`,
> `nyc_urban`, `nyc_suburban`, `nyc_rural`, `la_centre`) have **no generation-summary JSON at all**.
> The honest verdict is *consistent with one code state, not proof of one* — and **no future reading of
> this corpus can improve it**, because the missing evidence was never written.
> ~~**A ruling is therefore owed:** accept the circumstantial evidence as sufficient for (c), or accept
> that **OPEN-01 can never close on this corpus.** Until that is ruled, this item stays open.~~
>
> ✅ **RULED 2026-08-13 (ruling 5) — THE CIRCUMSTANTIAL EVIDENCE IS ACCEPTED AS SUFFICIENT FOR (c).**
> The user's decision, taken on the framing above with both costs stated. **(c) is settled: the corpus is
> treated as one code state.** The basis is the single unbroken **111-minute** window and the one manifest
> schema across all 60 pairs, which together leave very little room for a code change mid-generation.
>
> 🔴 **What this ruling does NOT do, stated so it is never over-read.** It does **not** convert
> *consistent with one code state* into *proof of one*, and it does **not** retroactively create evidence
> that was never written. **It is a decision to stop paying for a question this corpus cannot answer** —
> the alternative was a full fleet re-run with a recorded commit stamp, for a question whose answer is
> very probably yes. **Any future document citing one-code-state must cite it as a ruled assumption, not
> as a measurement**, and must say so in the same sentence. If a cross-mode result ever turns on this
> assumption being exactly true, **that result needs the re-run, and this ruling does not cover it.**
>
> ⚠️ **OPEN-01 does not close on this ruling.** (a) and (b) are measured, (c) is now ruled — what remains
> is **the remedy**, which is ruling 6 and is still owed to the user. **The item stays open on the remedy
> alone.**
>
> ⚠️ **Two corrections to evidence this item's neighbourhood cites.** The two `e02_run*.log` files
> **do not cover the audited corpus** — dated 2026-08-06, three days before the manifest window,
> `nyc_centre` only, and one ends in a `MemoryError` inside an abandoned local attempt. **Do not cite
> them.** And a second, smaller finding: **24 `auto`-mode buildings outside ±1% all carry
> `perimeter_core` zoning** (+2% to +31%), while the 718 `single_zone`/`one_zone_per_floor` buildings in
> the same comparison are 100% inside ±1% — a geometry residual recorded here, not sized further.
>
> ~~🔴 **The remedy remains the user's ruling, unchanged and untouched by this measurement:** fix the
> denominator, fix the simulation, or stop publishing per-building EUI for the affected modes. **No
> remedy was chosen. The measuring task's job ended at the number.**~~
>
> ✅ **RULED 2026-08-13 (ruling 6) — THE REMEDY IS: DIVIDE BY THE SIMULATED AREA.** Per-building EUI is
> to be published against the **multiplier-aware floor area EnergyPlus actually simulated**, read per run
> from `eplusout.eio` (Σ `Floor Area × Zone Multiplier × Zone List Multiplier` over zones marked
> `Part of Total Building Area = Yes`) — **not** against `footprint_area_m2 × levels`. The user chose this
> over stopping publication, over fixing the simulation, and over documenting only.
>
> **Why it is cheap: the measurement already exists.** `e02_simulated_floor_area.csv` holds all **40,800**
> rows with **0 parse failures** and a **0-unmatched join in both directions in all five modes**. The
> remedy is therefore a **denominator swap in the reporting layer** — no re-simulation, no cluster work,
> no change to any `.idf`.
>
> 🔴 **What this ruling does NOT do.** It does **not** make `building` mode simulate the right building —
> that mode still builds one storey, and after the swap its EUI answers *energy per simulated m²*, which
> for a multi-storey building is **not the real building's area**. The number becomes **internally
> consistent, not physically representative**, and any document using it must say which of the two it
> means. Fixing the simulation was offered and **not** taken (it would supersede every result those modes
> ever produced); that door stays open and is not foreclosed by this ruling.
>
> ⚠️ **The adopted baseline does not move.** `auto` already measures 1.0000 median / 99.63% within ±1%,
> so **the published fleet EUI of 157.1 kWh/m² pooled is unchanged by this remedy** — anyone reading this
> ruling as a restatement of the fleet number has misread it.
>
> **What is now owed to close OPEN-01:** a plan doc implementing the swap, a before/after per-building
> comparison for all five modes, and the two corrections above carried into whatever publishes EUI. Until
> that lands, **OPEN-01 stays open — now on implementation, no longer on a ruling.**
>
> **Evidence:** `openubem/outputs/comparisons/e02_simulated_floor_area.csv` (40,800 rows),
> `open01_denominator_audit.csv` (40,800 rows), `open01c_code_state_evidence.csv`,
> `extra/MEASUREMENT_open-01_denominator-audit-e02.md`.
> **Director re-derivation (CP-2):** an independent `.eio` parser reproduced
> `la_urban/way_401904735` (`MidriseApartment`, 3 storeys) at **1.33331 vs 4/3 = 0.0018% off**, with
> `Zone List Multiplier = 2` and 27 zones under `layout_assign` against 3 under `auto` and **1** under
> `building`; declared area re-read by hand as 1850.454098 × 3.0 = **5,551.362295**. Every figure is
> byte-identical to the executor's CSV.


### 🔷 UMBRELLA — **OPEN-01 now carries OPEN-02 and OPEN-28** (user's instruction, 2026-08-09)

> **The user directed that the three be merged into OPEN-01 rather than tracked separately.** They share
> **one** closure condition — the E02 five-mode / twelve-cell / 40,800-simulation pass — and splitting a
> single measurement across three tracked items made the work look like three commitments when it is
> one. **OPEN-01 is the item to watch; it closes when E02's harvest is audited, and OPEN-02 and OPEN-28
> close with it.**
>
> **The three findings are kept distinct beneath this heading, and not deleted** — this register's rule
> is append-and-amend, and a merge that erased the separate findings would destroy the evidence that
> each was independently established. They are folded, not collapsed:
>
> | Folded item | The finding it contributes | Why it is not the same finding as OPEN-01 |
> |---|---|---|
> | **OPEN-02** | No fleet-scale EUI has a simulation-verified denominator, in **any** mode | OPEN-01 is a `layout_assign`-specific mutation defect; OPEN-02 is that **no** mode's denominator was ever checked against what EnergyPlus ran |
> | **OPEN-28** | Every cross-mode comparison mixes **two harvest generations**, so any reported difference may be the method or may be the generation | This survives even if every denominator were correct — it is a confound, not an arithmetic error |
>
> 🔴 **What the merge must not be allowed to hide.** One run discharging three findings means **one
> audit has to answer three questions**, and a harvest that satisfies the denominator questions says
> nothing about the confound. E02's closure therefore requires, separately and explicitly: (a) the
> multiplier-aware floor area read from `eplusout.eio` for `layout_assign`'s non-`applied` buildings;
> (b) the same for **all five** modes fleet-wide; (c) a demonstration that all five modes came from
> **one** code state. **Any one of the three unanswered leaves OPEN-01 open.**
>
> **Status, 2026-08-10: E02 is COMPLETE on the cluster** (§0's 2026-08-10 amendment — 40,755/40,800
> COMPLETED, 99.89%). **That is a SLURM statement, not a correctness one — none of (a)/(b)/(c) has been
> answered yet, no EUI has been derived, and OPEN-01 stays open.** The census also opened OPEN-38,
> OPEN-39 and OPEN-40 and produced a correction to CP-R2's Risk-2 verdict — all in §0/§4, none of it
> closing this item.

**What is known.** In `layout_assign`, `match_storeys()` mutates the prototype **only** when it
returns status `applied` — its own docstring is explicit
(`openubem/geometry/layout_assigner.py:542-544`: *"every other status leaves `idf` untouched"*). So
`identity`, `fallback_shorter` and `fallback_not_expressible` all simulate the **prototype's** storey
count. Energy per unit area is then published against the **real** building's
`footprint_area_m2 × levels`. The error factor is `n_storeys_represented / num_floors`.

**Measured, directly** (`openubem/outputs/comparisons/r06c_local_results.csv`, real fleet buildings,
real `eplusout.eio`): `applied` buildings hold the assertion to ~0.002% (N=4). `MidriseApartment`
`identity` buildings fail at **exactly 4/3** (N=2) — the untouched prototype is a 4-storey-equivalent
(3 Z-bands × a `ZoneGroup` list multiplier of 2) simulated for a 3-storey building.

**Inferred from the code contract, not measured** — `t20_r10_reach_change.csv`:

| `num_floors` | n | factor `4 / num_floors` |
|---|---|---|
| 1 | 1,225 | **4.000×** |
| 2 | 1,048 | **2.000×** |
| 3 | 343 | 1.333× |
| 5 / 7 / 9 | 49 / 16 / 1 | below 1.0× |
| | **2,682** | (`MidriseApartment` non-`applied`) |

Fleet-wide **6,939 of 7,442** evaluated buildings are non-`applied`. Factors for the other 17
archetypes are **unmeasured**.

**[Superseded 2026-08-05 — see "Amended 2026-08-05 (M01)" below.]** This table covered
`MidriseApartment` only and assumed a fixed `4 / num_floors` factor; it is replaced by direct
measurement of all 28 archetype tokens.

**The honest reading.** For a 1-storey building the mode simulates a 4-storey apartment prototype and
divides that energy by one storey's area. The published number is not wrong *for the building that was
simulated* — it is a correct number for the **wrong building**. This is the arithmetic expression of a
fallback design that was always documented (E-LA-33: height does not track `num_floors`), now
quantified for the first time.

**What is NOT known, and must be measured before any plan:**
1. `n_storeys_represented` per archetype — only `MidriseApartment` (=4) has been measured. This is a
   cheap read of the 25 baseline IDFs, no simulation. **[Closed 2026-08-05 — see "Amended 2026-08-05
   (M01)" below. All 28 archetypes now measured.]**
2. Whether the correct remedy is (a) fix the denominator to match what was simulated, (b) make the
   simulation match the building, or (c) declare the mode's outputs per-prototype and stop publishing
   per-building EUI. **These are different projects.** (a) is a reporting fix; (b) reopens the
   mechanism R04 closed; (c) is a scope decision.
3. Whether any *adopted* result depends on this. `layout_assign` is not the adopted baseline —
   confirm that before sizing anything. **[Closed 2026-08-06 — M06 confirmed it. `auto` cannot reach
   `layout_assign` (`zoning.py:36-42`), and all 16,320 adopted rows carry zero `layout_assign`. The
   belief was correct; it is now measured. Report:
   `extra/MEASUREMENT_open-32_adopted-dependency.md`. Item 3 was never a guess in need of rescue —
   but it was load-bearing, and unmeasured load-bearing beliefs are what this register exists to
   catch.]**

**Only item 2 remains open.** With items 1 and 3 both closed, the sole question left before a plan can
be written for OPEN-01 is *which remedy* — and that is a scope decision for the user, not a
measurement.

**Do not conflate with OPEN-02.** This is about the *numerator/denominator mismatch*; OPEN-02 is about
our inability to check it at scale.

**Amended 2026-08-05 (M01).** Report:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-factors.md`. **Measured directly, all
28 archetype tokens across the 25 baseline IDFs:** only **2 of 28** archetypes carry a `ZoneGroup` list
multiplier — `MidriseApartment` 3 Z-bands → **4** storeys (×2), `HighriseApartment` 3 bands → **10**
(×8). The other 26 have `n_storeys_represented == n_proto`.

**Fleet-wide, 6,939 non-`applied` rows:** only **877 (12.6%)** sit at error factor 1.0. Median **2.0**,
mean 1.83, range **0.118× – 10.0×**. Largest masses: ×2.0 (2,263), ×4.0 (1,316), ×0.667 (1,031).

**Correction to the record.** `openubem/outputs/comparisons/a1_prototype_storey_structure.csv` must not
be cited for this item. Its `num_modelled_storeys` is the **band count**, not the multiplier-aware
storey count, and its `has_multiplier_gt_1` flag reads `False` for both archetypes that actually carry
a multiplier — it tests `Zone.Multiplier` and is blind to `ZoneGroup`'s list multiplier. It understates
`MidriseApartment` by 1 and `HighriseApartment` by 7.

**Amended 2026-08-06 (C02 halted).** The five-mode twelve-cell fleet pass this item was waiting on
(E02, `PLAN_compute-queue.md` §8) **HALTED on 2026-08-06 with a `MemoryError`, after completing only
3 of 60 (cell, mode) pairs.** The CP-C2 scope ruling was put to the user and is **parked at their
instruction** — no relaunch is authorised yet. This item remains open.

**Ruled the same day (user).** E02 is **parked to resume on the Speed cluster once its resources free
up** — *not* descoped, and **none** of the four reduced-scope options was taken. Full ruling and the
four conditions on resuming: `PLAN_compute-queue.md` §8, "RULING — CP-C2 / E02". 🔴 **The condition a
reader of this item must not miss:** the stock cluster template deletes `.eio`
(`submit_fleet_t08.sbatch:63`) and the retention built in E01 is **local-only**, living in
`t08_local_remainder.py` — so a cluster E02 launched on the unmodified template would destroy the
exact evidence this re-run exists to obtain.

### ~~OPEN-02~~ — No fleet-scale EUI has a simulation-verified denominator — 🟢 **DISCHARGED 2026-08-11**

> **DISCHARGED 2026-08-11 (T04 of `PLAN_e02-audit-and-closure.md`).** Folded into OPEN-01 on 2026-08-09
> by user instruction, sharing one closure condition — the E02 fleet pass. **That pass has now been
> made and, more importantly, *read*.**
>
> **This finding asserted that no fleet EUI this project has ever published has a verified
> denominator.** That was true when written. **It is no longer true:** the simulated floor area now
> exists for **all 8,160 buildings in all five modes**, parsed from **40,800 `.eio` files with 0 parse
> failures**, and every mode's denominator has been measured against it (see OPEN-01's table).
>
> ⚠️ **Discharged is not the same as vindicated.** The measurement did not confirm that the published
> denominators were fine — it found `building` mode wrong by the storey count and `layout_assign` at
> 15.37% within tolerance. **What discharges is the *blindness*, not the error.** The errors it exposed
> live on in OPEN-01, OPEN-35 and OPEN-42.
>
> **Evidence:** `openubem/outputs/comparisons/e02_simulated_floor_area.csv`,
> `open01_denominator_audit.csv`, `extra/MEASUREMENT_open-01_denominator-audit-e02.md`.


> 🔷 **FOLDED INTO OPEN-01 on 2026-08-09 by the user's instruction.** Tracked there, closes there, with
> the same E02 pass. The finding below is **retained in full as evidence** and is not superseded — see
> the umbrella table under OPEN-01 for why it is a distinct finding. Do not count it as a separate open
> commitment.

**What is known.** Every EUI in every mode and every harvest T08→T20 divides by
`footprint_area_m2 × levels` from Stage-2 enrichment. The file that records what EnergyPlus actually
simulated, `eplusout.eio`, is deleted unconditionally by the shared cluster template —
**verified this session** at `scripts/cluster/submit_fleet_t08.sbatch:63`, `rm -f "$OUTDIR"/*.eio`,
inside a block whose stated purpose is disk economy (">800 GB untrimmed per city"). The template is
byte-identical across T08→T20.

**Consequence, stated plainly:** *no* fleet-scale EUI this project has ever published has a verified
denominator, and none can be reconstructed without re-running the fleet. The entire body of
verified evidence is 6 buildings run locally (OPEN-01).

**What must be decided before a plan:** whether to retain `.eio` on future runs. It is one line, but
the trade is real — the trimming exists because untrimmed output is >800 GB per city. Measure the
actual per-building `.eio` size first; it is a small text file and the fear may not survive contact
with the number. **That measurement is the whole of the investigation for this item.**

**Amended 2026-08-05 (M02).** Report:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-02_eio-disk-budget.md`. **Measured.**
`eplusout.eio` median **76,068 B** (n=881 local, min 6,736, max 1,092,989). Marginal cost of retaining
it, per run, against what the pipeline already keeps: **12.6%** (median of the per-run ratio; 2.4% by
aggregate bytes). One five-mode fleet pass: **1.3 GB** typical to **~43–45 GB** worst case, against
**8.1 TB** free on the shared filesystem — **0.5% at the absolute worst.**

**The register's own prediction is confirmed verbatim.** The line above said *"the fear may not survive
contact with the number."* It did not. The ">800 GB untrimmed per city" figure at
`submit_fleet_t08.sbatch:63` covers **eleven** file types deleted together; `.eio` alone was never the
cost.

**Stated limitation.** `fast_zone` has **zero** local `.eio` samples; its contribution is a bounded
estimate from zone-count ratios, not a measurement. Its worst-case bound is still negligible.

**Decision taken 2026-08-05 (CP-M1).** A five-mode re-run retaining `.eio` is **approved in principle**.
Execution moved off the Speed cluster at the user's instruction — its 32-CPU account cap is fully
occupied by an unrelated account (32 running / 675 pending, observed read-only). Local feasibility is
being costed; the pass is **not scoped, not submitted, and may yet be reduced in scope**.

**Amended 2026-08-06 (C02 halted).** The five-mode twelve-cell fleet pass this item was waiting on
(E02, `PLAN_compute-queue.md` §8) **HALTED on 2026-08-06 with a `MemoryError`, after completing only
3 of 60 (cell, mode) pairs.** The CP-C2 scope ruling was put to the user and is **parked at their
instruction** — no relaunch is authorised yet. This item remains open.

**Ruled the same day (user).** E02 is **parked to resume on the Speed cluster once its resources free
up** — *not* descoped, and **none** of the four reduced-scope options was taken. Full ruling and the
four conditions on resuming: `PLAN_compute-queue.md` §8, "RULING — CP-C2 / E02". 🔴 **The condition a
reader of this item must not miss:** the stock cluster template deletes `.eio`
(`submit_fleet_t08.sbatch:63`) and the retention built in E01 is **local-only**, living in
`t08_local_remainder.py` — so a cluster E02 launched on the unmodified template would destroy the
exact evidence this re-run exists to obtain.

### OPEN-03 — Internal loads are modelled as 2022-code construction regardless of real vintage ✅ **measured**

`layout_assign` runs ~29% below the other four resolution modes on median EUI. Roughly half of that
was traced at the 2026-07-26 close to a design property: internal loads come from
`ASHRAE901_*_STD2022` prototypes, so every building's lighting/equipment/occupancy is modelled as
2022-code **even though the envelope is re-patched to the building's real vintage and climate zone.**

**Status:** ~~documented in results §7, never actioned. Not re-verified this session.~~ **[Superseded
2026-08-05 — see "Amended 2026-08-05 (M03)" below. Results §7 is a post-hoc write-up, not a prior
specification, and its "not a defect" wording is a contradictory statement, not an adjudication.]**

**What to measure first:** whether the loads-vs-envelope vintage split is deliberate (a documented
approximation) or an oversight in the patching path. The answer changes whether this is a defect or a
disclosure.

**Amended 2026-08-05 (M03).** Report:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_loads-vintage-split.md`. **Verdict:
`undocumented but deliberate`** — traceable to a decision that was never written into any spec. Zero
matches for `layout_assign` / `resolution_mode` anywhere under `docs/docs_main`. The decision is real
and traceable to `docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:155` and `:494`,
the latter flagging the mechanism "for a future arc".

**Correction to the line above.** It reads *"documented in results §7."* That is misleading: results §7
(`OpenUBEM_results_LayoutAssigner.md:463`) is a **post-hoc write-up produced by the same session that
discovered the effect**, not a prior specification. Its wording — *"a direct consequence of prototype
substitution, not a defect"* — is recorded here as a **contradictory statement, not adjudicated**.

**Magnitude, static, no simulation (n=12 archetypes matched, 0 unmatched).** 2013-code vs 2022-code:
lighting power ratio median **1.722** (range 1.256–2.502); equipment **1.064**; occupancy **1.000**.
The two equipment ratios of exactly 1.000 were checked against raw IDF text and are genuine source
agreement, not a parsing artefact.

**The proxy understates the real error.** No canonical fleet-wide `vintage_standard` column exists (see
new item **OPEN-30**). The only fleet-wide sample available — a prior investigation's byproduct, cited
with a provenance caveat — puts **92.9%** of buildings at `DOERefPre1980`, far older than the 2013 code
used as the comparison floor.

### OPEN-04 — The labelled-accuracy gate drifted 92.0% → 88.0% ✅ **CLOSED 2026-08-12 — ID RETIRED 2026-08-13**

> ✅ **CLOSED. Retired formally on 2026-08-13 under ruling `2h`**, which existed only because this
> item had been subtracted from the register's count on 2026-08-12 without ever being marked closed
> in its own section. **The closure itself is not new; the record of it is.**
>
> **Why it closes.** The item asked what caused the drift. M04 answered it: the suspected cause —
> the already-in-tree Phase-D fusion/crosswalk work of 2026-07-13 — was **falsified by a live
> before/after reproduction**, and the real cause was identified by bisect. The gate still clears.
> **Nothing about the item is left unmeasured.**
>
> 🔴 **Two consequences survive the closure and bind future work:**
> **(1) `92.0%` is unreproducible** — its answer key was rewritten in the very next commit (T10), so
> that figure may be quoted as history but never as a comparison point.
> **(2) The old 50-row fixture is never deleted and never edited** — this item's bisect depends on it.
> That constraint is what forced ruling `2a` (2026-08-13) to add a **second** gate on the new tag-rich
> fixture rather than repoint the existing one.

Surfaced during the input-framework classification-fixes arc (closed 2026-07-21) and explicitly
flagged "for a future arc". Still clears its pass gates. **Proven unrelated** to that arc's own
changes by a live before/after reproduction. ~~Suspected but unconfirmed cause: the already-in-tree
Phase-D fusion/crosswalk work of 2026-07-13.~~ **[Superseded 2026-08-05 — FALSIFIED, see "Amended
2026-08-05 (M04)" below. The record of having suspected Phase-D stays; it was checked and ruled out.]**

**Why it matters more than 4 points suggests:** an accuracy gate that drifts without anyone noticing
is a broken instrument regardless of whether it still passes. The open item is *the unexplained
drift*, not the 88%.

**First measurement:** bisect the gate across the commits between the R3-era reference and now. This
is cheap and mechanical, and it either confirms the Phase-D suspicion or falsifies it.

**Amended 2026-08-05 (M04).** Report:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-04_accuracy-drift-bisect.md`.

**The 92.0/88.0 pair is `test_fine_top1` only** — cited at
`docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md:131,148` and
`docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md:84,140`.
`test_coarse_top1` was **100% at every commit tested** and never at risk. The apparent contradiction
(88% vs a 90% gate) dissolves: the fine gate is **0.70**. Verified live at HEAD — 3/3 pass.

**Bisect, read-only via disposable worktrees, main tree clean before and after:**

| commit | date | fine top-1 | role |
|---|---|---|---|
| `7635ce2` | 2026-06-12 | 92.0% | R3-era reference (CP-α) |
| `67ede73` | 2026-07-01 | **84.0%** | **first change** — E-R3-3 tier bins; 14 fixture rows relabelled + rules rewritten |
| `0df422e` | 2026-07-03 | **88.0%** | second change — partial recovery |
| `ef19141` | 2026-07-21 | 88.0% | contains Phase-D fusion/crosswalk — **no change** |
| `bca92d0` | 2026-08-05 | 88.0% | HEAD |

**Phase-D fusion/crosswalk hypothesis: FALSIFIED.** The drift completed 18 days before that work
landed, and `git diff` on every classifier/fixture/test file between `0df422e` and `ef19141` is empty.

**Reframe the item.** It is no longer *"an unexplained drift."* It is a **ratified change (E-R3-3)
whose effect on the labelled fixture was never compared against the prior baseline.** The line above —
*"an accuracy gate that drifts without anyone noticing is a broken instrument"* — is upheld in
substance but the instrument is not broken; the **review process** is the defect. Carried to §C /
new item **OPEN-31**.

### ~~OPEN-28~~ — Every cross-mode comparison mixes two harvest generations — 🟢 **DISCHARGED 2026-08-11**

> **DISCHARGED 2026-08-11 (T04 of `PLAN_e02-audit-and-closure.md`).** Folded into OPEN-01 on
> 2026-08-09; discharged on the same fleet pass.
>
> **The remedy this finding asked for is delivered: E02 is all five modes on one generation**, built in
> one 111-minute window from one build tree, so a cross-mode delta now means the method rather than the
> harvest. That was the whole ask.
>
> **The residual confound against the adopted 3rd-generation fixture is bounded rather than waved at.**
> Joining E02's own `03_manifest.parquet` against `05_results.csv` per cell: **`auto`'s
> `zoning_strategy` agrees at 100% in every cell** and its `archetype_id` at **96.5–100%**. The other
> four modes' zoning agreement falls to 7.6–52.5% — **expected and not a defect**, since those modes
> force a different zoning approach by construction.
>
> 🔴 **The rule this finding created survives its discharge, and binds harder than before: every
> comparison must state which harvest generation each side came from. E02 is the fourth.**
>
> ⚠️ **What is NOT discharged.** The **already-published** cross-mode numbers — the −29.1% figure whose
> `layout_assign` side is T19 and whose `auto` side is T08 — are still confounded, and deciding what to
> do about them is **CP-M2, an owed user ruling**. Discharging this finding does not retract a single
> published figure.


*Added 2026-08-05.*
> 🔷 **FOLDED INTO OPEN-01 on 2026-08-09 by the user's instruction.** Tracked there, closes there, with
> the same E02 pass. The finding below is **retained in full as evidence** and is not superseded — see
> the umbrella table under OPEN-01 for why it is a distinct finding. Do not count it as a separate open
> commitment.

**What is known, verified.** `layoutAssigner/figures/README.md:8`, written by the arc itself:

> **Provenance split.** Figures 2 and 5 mix two harvest vintages: the `layout_assign` bars/star are
> **T20** (2026-08-04); the `auto`/`building`/`floor`/`fast_zone` bars are still the **original T08
> harvest, never re-run on T20.** This is stated directly in both figure titles.

The same split runs through the prose. `docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` §4's
cross-mode EUI table is **T08 throughout** (2026-07-01); the new §10 is T20. Both are correctly
labelled in isolation. **Neither says that a comparison between them is not like-for-like.**

**Why this is an open item and not a caption.** Between T08 and T20 the codebase changed
substantially — E-LA-20's convergence fix alone recovered 150 buildings, and the storey-matching
arc's R01/R02/R03/R10 all landed. So any cross-mode difference currently reported is **the method
difference plus everything that changed in the code between July and August, with no way to separate
them.** The mode comparison is the thing the resolution-mode feature exists to support, so this is
not a peripheral defect.

**It is worse than "older code", because of OPEN-08.** E-LA-22 establishes that re-running a past
generation at current HEAD silently diverges in **archetype and vintage** for data-poor buildings. So
the two harvests may not even be describing the same buildings the same way. That confound is
**unquantified**. Read OPEN-28 and OPEN-08 together.

**The −29.1% figure inherits this.** The arc results doc §7.2 reports `layout_assign` running ~29%
below the other four modes on median EUI, and OPEN-03 attributes roughly half of it to the 2022-code
internal loads. **Which harvest each side of that −29.1% came from has not been established** — that
is part of the first measurement below, not an assumption to carry forward. **[Superseded 2026-08-05 —
now established, see "Amended 2026-08-05 (M05)" below. It is not T20 vs T08 as this item generally
frames it; for this specific figure it is T19 vs T08.]**

**The bundle — this is the operationally useful part.** One fleet re-run of **all five modes on one
harvest, retaining `eplusout.eio`**, closes three items at once:

| Item | What the re-run gives it |
|---|---|
| **OPEN-01** | a verified, multiplier-aware denominator for every building instead of a 6-building local sample |
| **OPEN-02** | the `.eio` file that has never existed for any fleet building |
| **OPEN-28** | all five modes on one generation, so a cross-mode delta means the method |

It requires one change to `scripts/cluster/submit_fleet_t08.sbatch:63` (stop deleting `*.eio`) and a
disk-budget check — the trim exists because untrimmed `fast_zone` city passes exceed 800 GB, so
**retaining `.eio` is a storage decision, not a one-line edit.** That check is the gate on the bundle.

**What is NOT known, and must be measured before any plan:**
1. **How many buildings are actually shared** between T08 and T20 with identical Stage-2 inputs, and
   whether their archetype/vintage agree. This is a table join, no simulation, and it directly
   quantifies the OPEN-08 confound.
2. **The `.eio` disk cost** for one full five-mode fleet pass. Needed before the bundle can be sized
   at all. A per-building `.eio` size × 8,160 × 5 estimate from any existing local run is enough.
3. Whether a **cheaper subset** suffices — one cell, or one archetype family, re-run across all five
   modes — to establish the harvest-generation effect without a full fleet pass. If the effect is
   small, the full bundle may not be justified; if it is large, no existing cross-mode number stands.

**Do not conflate with OPEN-02.** OPEN-02 is that we cannot verify a denominator at all. OPEN-28 is
that the five modes were not measured at the same time. They travel together operationally but they
are different defects, and OPEN-28 would remain even if every denominator were verified.

**Amended 2026-08-05 (M05).** Report:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-28_harvest-generation-join.md`.

**Join, `t08_all_modes_eui.csv` × `t20_layout_assign_eui.csv`:** shared **4,530**, T08-only **0**,
T20-only **3,630**, union **8,160**. T08 is a strict subset of T20.

**Archetype agreement 86.60%** (3,923/4,530) — **13.40% disagree.** Top pair
`MediumOffice → SmallOffice`, n=396. Root cause traced and reproduced from the historical blob: commit
**`0df422e`** (2026-07-03, "classification thresholds updates") changed the shared `05_results.gpkg`
fixture between the two harvests.

**Floor-area agreement 100%** (4,530/4,530 within 1%). Only the archetype drifted.

**Correction to this item's central claim.** The framing above is *"`layout_assign` is T20."* For the
**published −29.1% figure that specifically is wrong.** Per
`OpenUBEM_results_LayoutAssigner.md:422-423,449-458`, that figure's `layout_assign` side is **T19**,
not T20; the `auto` side is T08. The join above therefore **does not describe the population the
published −29.1% was computed over.** It is now established, and it is a third generation, not a
second.

**Convergence worth recording.** M04 and M05 were executed by separate agents with no shared context
and both independently identified commit `0df422e` — one as the point the accuracy metric settled, the
other as the cause of the fleet-scale reclassification. Neither knew of the other's finding.

**Amended 2026-08-06 (C02 halted).** The five-mode twelve-cell fleet pass this item was waiting on
(E02, `PLAN_compute-queue.md` §8) **HALTED on 2026-08-06 with a `MemoryError`, after completing only
3 of 60 (cell, mode) pairs.** The CP-C2 scope ruling was put to the user and is **parked at their
instruction** — no relaunch is authorised yet. This item remains open.

**Ruled the same day (user).** E02 is **parked to resume on the Speed cluster once its resources free
up** — *not* descoped, and **none** of the four reduced-scope options was taken. Full ruling and the
four conditions on resuming: `PLAN_compute-queue.md` §8, "RULING — CP-C2 / E02". 🔴 **The condition a
reader of this item must not miss:** the stock cluster template deletes `.eio`
(`submit_fleet_t08.sbatch:63`) and the retention built in E01 is **local-only**, living in
`t08_local_remainder.py` — so a cluster E02 launched on the unmodified template would destroy the
exact evidence this re-run exists to obtain.

### ~~OPEN-30~~ — Assigned vintage is never persisted by any harvest — 🟢 **CLOSED 2026-08-11**

> **CLOSED 2026-08-11 (T03 of `PLAN_e02-audit-and-closure.md`). ID retired.**
> This item's closure condition was written into this register verbatim: *"stays open until R07's value
> distribution is demonstrated against the fleet's known ≈92.9% `DOERefPre1980` composition; a column
> that comes out constant or uniform is a defect, not a pass."* **The demonstration has now been made.**
>
> **60 of 60** `03_manifest.parquet` files read — the persisted column, never `resolve_vintage()`
> (RULING D honoured). **40,800 rows, 0 nulls, 100% coverage.** Distribution: `DOERefPre1980` **38,125
> (93.44%)**, `DOERef1980to2004` 1,065 (2.61%), `90.1-2013` 890 (2.18%), `90.1-2007` 610 (1.50%),
> `90.1-2019` 110 (0.27%). **Five distinct values — not constant, not uniform** — and 93.44% sits just
> above the ≈92.9% figure this register predicted, which is the pass condition.
>
> **The independent control, which is the one that settles it:** `la_rural`'s manifest vintages checked
> against `year_built` in the raw `01_buildings.gpkg`, which the manifest join never touches. **Zero
> crossover**, in **all five modes** — every building with a known year falls inside its class's window
> (`90.1-2007` → 2005–2007; `DOERefPre1980` → 1920–1979). R07's finding reproduces exactly.
> *(The executor's first pass reported an apparent 12/14 and 113/135 mismatch, self-diagnosed it as its
> own bug — missing `year_built` scored as out-of-range rather than unknown — and re-ran. Recorded
> because a self-caught defect belongs in the record.)*
>
> **Director re-derivation:** the full 60-manifest distribution was recomputed independently and matched
> to the row.
> **Evidence:** `openubem/outputs/comparisons/open30_vintage_distribution.csv`,
> `open30_la_rural_year_built_crosscheck.csv`,
> `extra/MEASUREMENT_open-30-01c_vintage-and-code-state.md`.
>
> ⚠️ **What this closure does NOT say.** It says the vintage column is persisted and correct **in the
> E02 build tree**. It says nothing about harvests before 2026-08-09, and it does not answer OPEN-03,
> whose vintage bound it merely unblocks.


*Added 2026-08-05, from M05.*

Neither `t08_all_modes_eui.csv` nor `t20_layout_assign_eui.csv` — nor their shared provenance file
`05_results.gpkg` at either git state — carries a `vintage_standard` column. `resolve_vintage()`
(`openubem/semantic/construction_sets.py:126`) produces the token, `envelope_patcher` consumes it, and
it is then discarded.

**Consequence.** Vintage agreement between harvest generations cannot be checked now, and could not
have been checked at any past point either. This is not a gap in the comparison — it is a gap in what
was ever recorded. It also blocks OPEN-03 from being bounded against the fleet's real vintage
distribution rather than a proxy.

**First measurement:** none needed; the absence is verified. ~~**Decision owed:** whether to persist the
token on future runs — one column, and the re-run already approved in principle (OPEN-02) is the
natural place.~~

> **✅ RULED 2026-08-09 — persist it. Obligatory, not optional.** The user was given OPEN-30, OPEN-31
> and OPEN-33 as a single question — *what must a change carry before it counts as finished* — and
> ruled **all three obligatory**. For this item that means: **every harvest writes the assigned vintage
> token into its output**, so the value can be read back from the artifact instead of re-derived from
> whatever the code happens to be on the day someone asks.
>
> **Scope of the ruling, stated so no plan over-reads it:** it binds *future* runs. It does **not**
> retro-fit the token into artifacts already on disk — that is impossible, which is precisely OPEN-30's
> finding. The next fleet pass (E02, whichever machine runs it) is the natural first carrier, and the
> column must exist **before** it is submitted or the pass reproduces the gap it was meant to close.
> **Remains open until the column is built and demonstrated**; the ruling authorises the plan, it does
> not do the work.

> **⚠️ RULING D — 2026-08-09, the manager's answer to R03's STOP. The route is the manifest.**
> Task **R03** of `implemenation/PLAN_speed-resume.md` was written to add the column to both harvests,
> with an explicit instruction to trace first and **stop** if the token turned out not to be reachable.
> **It was not reachable, and the executor stopped correctly rather than choosing.** Independently
> confirmed by the manager: `vintage_standard` is written at `construction_sets.py:352` and is the
> **first** of the 28 appended envelope columns (`openubem/semantic/__init__.py:45-47`,
> `_F17_ENVELOPE_COLS`), but it lives only as a transient in-memory column on `gdf_57`. It is in no
> persisted artifact the cluster harvest can reach — the five real `03_manifest.parquet` files on disk
> carry **10 columns** and it is **not** among them, and `05_results.gpkg`, which is what `cell_info`
> is built from, does not carry it either.
>
> **The ruling: carry it in the per-building manifest.** `run_step3_mode()`
> (`scripts/cluster/t08_full_sweep.py:154-181`) is handed `gdf_57` itself and writes
> `03_manifest.parquet`; the manifest already carries `osm_id`; and **both** harvest paths already read
> that manifest (`t08_harvest_results.py:587,591,618`). So one left-join in one script gives both
> harvests the column with **no new file, no shipping change, and nothing recomputed**. Implemented as
> task **R07**.
>
> 🔴 **Why the route matters more than the column.** The alternative — calling `resolve_vintage()` again
> at harvest time — would have been quicker and would have produced a column that looked identical. It
> would also have been a script reimplementing pipeline logic, i.e. **lookalike evidence**, the exact
> failure this register names elsewhere (`a1_prototype_storey_structure.csv`) and the reason the
> evidence rules exist. Copying the value the builder was actually handed, in the same process and the
> same moment the IDF is generated, is provenance. Re-deriving it is reconstruction. **They are not
> interchangeable even when they agree.**
>
> **Manifests written before R07 do not get the column and must not be backfilled** — the empty string
> is the honest record of a run whose vintage was never captured. **OPEN-30 stays open** until R07's
> value distribution is demonstrated against the fleet's known ≈92.9% `DOERefPre1980` composition; a
> column that comes out constant or uniform is a defect, not a pass.

### OPEN-31 — Ratified changes are adopted without a before/after on the labelled fixture ✅ **CLOSED 2026-08-12 — ID RETIRED 2026-08-13**

> ✅ **CLOSED. Retired formally on 2026-08-13 under ruling `2h`**, for the same reason as OPEN-04: the
> count had already been reduced by it on 2026-08-12 while the section still carried no closure mark.
>
> **Why it closes.** This item was a **decision owed**, not a defect to fix — no line of code was ever
> wrong. **The decision was taken on 2026-08-09: CP-M3 is obligatory.** A ratified classification
> change must carry a before/after on the labelled fixture, with **both** numbers recorded. Once the
> ruling exists, the item has nothing left to hold.
>
> 🔴 **The gate it created is live and is already binding on open work.** **OPEN-47**'s office-bin
> divergence (the source's rule is area AND floor count; `building_classifier.py:175-177` tests area
> only) is a classifier change and therefore cannot be made without passing through this gate — which
> is precisely why that item had to wait on the fixture question.
>
> ⚠️ **The gate's own shape changed on 2026-08-13 under ruling `2a`, and anyone applying CP-M3 must
> use the new shape: there are now TWO exams, each with its own pass mark** — the old 50-row fixture at
> **≥0.70** (kept exactly as it is, because OPEN-04's bisect depends on it) and
> `tests/fixtures/labelled_archetypes_tagrich_v2.csv` at its own separately-set threshold.
> 🔴 **A CP-M3 before/after must therefore report both, and every accuracy figure must name its fixture.
> A bare percentage is no longer a meaningful number in this project.**
*Added 2026-08-05, from M04 + M05.*

E-R3-3 was ratified and adopted. It cost **4 points** of fine top-1 accuracy and reclassified **13.4%**
of the fleet's shared buildings, and neither effect was measured against its predecessor at adoption
time. Both surfaced weeks later, separately, in unrelated investigations.

**This is a process defect, not a code defect.** No line of code is wrong.

~~**Decision owed (CP-M3):** whether a ratified classification change must carry a before/after on the
50-row labelled fixture before adoption.~~

> **✅ CP-M3 RULED 2026-08-09 — yes, and it is obligatory.** Ruled together with OPEN-30 and OPEN-33
> as one question; the user's answer was *"yes to all three — make them obligatory."*
>
> **The rule, in the form it must be written into the plan doc:** no change that can move
> classification is adopted until the 50-row labelled fixture has been run on **both sides** of it and
> **both numbers are recorded**. A single "after" number does not satisfy it — the project's own
> evidence rule already says a before/after is not reportable until the before is shown to differ from
> the after (register §6).
>
> **What it would have caught, which is why it was ruled:** E-R3-3 cost **4 points** of fine top-1 and
> reclassified **13.4%** of the shared fleet, and neither number existed at adoption time. The drift
> `92.0 → 84.0 → 88.0` then took a five-commit bisection (M04) to attribute, six weeks late.
>
> **Two boundaries the ruling does not cross.** It does not re-open any adopted change retroactively —
> M04 already established the history and re-running it is forbidden (§6, "do not re-run M01–M05"). And
> the fixture's own fitness is a **separate, still-open question** (OPEN-22: a third of the exam is
> decided by size-bucketing rather than tag logic). **Making the exam obligatory does not certify the
> exam** — if OPEN-22 later changes the fixture, the gate follows it. **Item stays open until the gate
> is written down where an executor will meet it.**

### OPEN-32 — Two large `layout_assign` errors point in opposite directions; the net is unmeasured ✅
*Added 2026-08-05, from M01 + M03.*

OPEN-01 inflates the numerator relative to the denominator for 87.4% of buildings (median ×2.0).
OPEN-03 deflates the numerator by modelling loads at a code year newer than 92.9% of the fleet
(lighting ratio ≥1.72×). **They oppose each other, and their net effect has never been computed.**

A `layout_assign` EUI could be approximately correct while both of its inputs are substantially wrong
— which is a weaker footing than a number that is right component-wise, because the cancellation is
coincidental and will not hold under any change to either mechanism.

**Explicitly not claimed:** that the adopted fleet baseline (158.0 kWh/m²) is affected. OPEN-01 item 3
— *whether any adopted result depends on `layout_assign`* — is **still unmeasured**, and OPEN-01's own
"What is NOT known" item 3 (§2, above) requires it be confirmed rather than assumed. **That
confirmation is this item's first measurement**, and it is cheap.

> **✅ First measurement MADE — 2026-08-06 (M06).** Report:
> `extra/MEASUREMENT_open-32_adopted-dependency.md`. Read-only; no simulation, no cluster.
>
> **Answer: no adopted result depends on `layout_assign`.** Three independent lines:
>
> 1. **Structural — decisive, and a property of HEAD.** `decide_zoning_strategy()`
>    (`openubem/geometry/zoning.py:13-42`) can return only `single_zone`, `perimeter_core` or
>    `one_zone_per_floor` under `auto` (lines 36–42). **`auto` has no path to `layout_assign`**; the
>    strategy is reachable only by explicitly passing the mode. Prototype substitution — the carrier of
>    *both* OPEN-01's `ZoneGroup` multiplier and OPEN-03's 2022-code vintage — is entered solely through
>    `_layout_assign_baseline_path()` (`openubem/idf/builder.py:67-77`), which returns `None` for every
>    other mode at `:75-76`. No baseline IDF loads, so neither defect can fire.
> 2. **Artifact — exhaustive, not sampled.** `zoning_strategy` tallied over **all 8,160 rows** of the
>    adopted `phaseE_elevrb` tree (4,291 / 3,259 / 610) **and all 8,160** of its `phaseE_er33`
>    predecessor (4,282 / 3,259 / 619): **zero `layout_assign` rows in either**, and the only values
>    present are exactly the three `auto` can emit. `t08_all_modes_eui.csv` likewise carries
>    4 modes × 4,530 buildings with none — independently reproducing M05's shared count.
> 3. **Temporal — corroborating only.** The string `layout_assign` is absent from the tree at
>    `3a925f9^` and first appears 2026-07-25; the adopted artifacts were committed 2026-07-21 and
>    2026-07-02. *Weakened deliberately:* this history is 40 commits for ~2 months and is curated, so
>    this line supports the finding but does not carry it.
>
> **Consequence for this item.** OPEN-01 and OPEN-03 are **not** shrunk — they are exactly as large as
> M01 and M03 measured, and every published `layout_assign` number, **−29.1% included**, stays wrong.
> What changes is the radius: it stops at a method the project already labels *not certified for
> fleet-level EUI reporting*, and does not reach the adopted baseline. **The caveat the explanation
> docs already carry is now earned rather than merely prudent.**
>
> **Still open, unchanged:** the **net** of the two opposing errors. M06 answered the prior question
> (does it reach the adopted numbers — no), not this item's own question.

> **✅ SECOND AND FINAL MEASUREMENT MADE — 2026-08-13 (T04 of `implemenation/PLAN_five-more-items-2026-08-13.md`).**
> Report: `extra/MEASUREMENT_open-32_net-of-open01-open03.md`. Artifacts:
> `scripts/analysis/open32_layout_assign_net.py`, `openubem/outputs/comparisons/open32_layout_assign_net.csv`
> (8,153 rows × 20 columns). Read-only; no simulation, no cluster. **Every figure below was
> re-derived by the director from the delivered CSV, not read from the executor's report** — including
> the identity `net = f_loads / error_factor`, which holds to within 1e-9 on all 8,153 rows.
>
> **Answer: at the median the two errors nearly cancel — and the median is the most misleading
> possible summary of this population.**
>
> - **Net at the median: ≈1.12** (`net_med`), i.e. ~12% residual overstatement after both errors act.
> - **But only 12.6% of buildings** land within ±10% of true cancellation. `net_med` ranges
>   **0.0032 to 19.88** across the fleet.
> - **The denominator error is quantized at powers of two.** `error_factor` deciles:
>   **[0.316, 0.474, 1.000, 1.999, 4.000]**. 15.4% of buildings sit at ≈1.0, 12.7% at ≈2.0, 10.1% at
>   ≈0.5; 44.0% above 1 and 56.0% below. Powers of two are the signature of **multiplier / storey
>   arithmetic**, not of a continuous area discrepancy.
> - **The loads error was measured, not assumed.** The plan told the executor to *assume* a
>   lighting+equipment share; it found `t20_layout_assign_eui.csv` already carries per-building
>   end-use EUI and measured it: **median 39.9%, IQR [33%, 44%], n = 8,153.**
>
> **🔴 This resolves a conflict inside this register.** This item's own opening text says OPEN-01
> inflates by *"median ×2.0"*; the measured median `error_factor` is **0.9999**. **Both are true of
> different things.** The distribution is roughly log-symmetric about 1.0, so the median lands on 1.0
> while a large sub-population genuinely is off by ×2 (and a comparable one by ×0.5). Reporting the
> median alone — in either direction — would misrepresent the fleet. **Do not quote a single
> central figure for this error; quote the deciles.**
>
> **🔴 Two corrections the executor made to the manager's plan, both correct.** Recorded because the
> plan was wrong and the executor was right to check rather than obey:
> 1. The plan specified the denominator ratio as `area_multiplier_aware_m2 / area_plain_m2`. That
>    yields a median of exactly 1.0000 — a null result. The published EUI in fact divided by
>    **`declared_area_m2`** (footprint × levels), a column in **neither** file the plan named. The
>    executor established this from `scripts/cluster/t20_harvest_layout_assign.py:244,304` and
>    `scripts/analysis/e02_t04_floor_area_audit.py:209` and then **proved** it numerically against the
>    published per-building EUI (max difference 1.2e-10). Director re-derived both halves.
> 2. The plan's assumed loads share was replaced by a measurement (above).
>
> **This item is now ANSWERED.** Nothing further is measurable locally.

---

### OPEN-45 — The pipeline looks for `** Severe **` with one space, so no building in the fleet has a recorded error ✅ **CLOSED 2026-08-13 — zero live defects remain**

> ✅ **CLOSED 2026-08-13 (T03 of `PLAN_five-items-2026-08-13.md`; CP-2 director-signed).** The sweep was
> re-run and **found nothing left to fix — and no code was changed, which is the correct outcome**, named
> in advance in the plan so nobody would invent a fix to justify the task.
>
> **Result: 24 rows — `one-off 15 · already-correct 8 · UNCLASSIFIED 1`, non-vacuity control passed.**
> Director re-derivation, independent of the executor: a direct grep of the live tree for the broken
> single-space literal finds **exactly one occurrence anywhere under `openubem/`, and it is inside
> `err_parse.py`'s own docstring, where it appears as the thing being warned about.** `runner.py:141` uses
> `FATAL_RE.match`.
>
> The three named candidates, each read rather than taken on trust: the lone **UNCLASSIFIED** row
> (`scripts/analysis/open42_failure_causes.py:7`) is a **docstring** — line 27 imports `FATAL_RE, SEVERE_RE`
> from `err_parse`, no literal exists; `c01_storey_matching_regression.py:153-154` is a **comment**, and
> the function it documents already matches on the `"** Severe"` prefix, whitespace-tolerant by
> construction (a `_SEVERE_RE` at line 145 is defined and never used — **dead but correct**, left alone);
> and `docs/…/t19_harvest_layout_assign.py:259` is **frozen/archived** and structurally outside the
> sweep's `ROOTS`, deliberately untouched. The remaining 15 are spent one-off scripts from closed arcs.
>
> ⚠️ **A provenance gap, recorded because this project's rule is to record them.** The CSV **on disk before
> the re-run was stale** — it still listed `openubem/simulation/runner.py:140` and
> `tests/test_sim_integration.py:171` as unfixed, and both are fixed at HEAD. **Which earlier task fixed
> them and left the CSV unregenerated is not determinable from the artifacts.** Not blocking, but it means
> **anyone who read that CSV between the fix and 2026-08-13 was misled by it.**

> **Amended 2026-08-12 (night, T01–T02 of `PLAN_three-new-items-2026-08-12.md`). Advanced, not
> closed.** A shared whitespace-tolerant matcher — `openubem/results/err_parse.py`
> (`SEVERE_RE`/`FATAL_RE`/`WARNING_RE`, `first_severe`, `count_severe`, `has_fatal`) with 16 tests —
> now backs `scripts/validation/v12_cell_pipeline.py:625` and
> `scripts/cluster/make_manifest_from_cluster.py:47`. **Load-bearing one-space sites 2 → 0**,
> director-verified from both diffs. The sweep classified 25 sites in total
> (`openubem/outputs/comparisons/open45_severe_literal_sweep.csv`): 15 spent one-off repair or
> diagnostic scripts, listed and deliberately not edited, and 8 already correct.
>
> **Non-vacuity control, re-derived by the director on a real file rather than read from the report**
> (`docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/a2_run_multiplier/eplusout.err`,
> whose real line is `'   ** Severe  ** Transformer Overloaded'`): the old one-space check returns
> `[]`; `first_severe()` returns the line.
>
> 🔴 **A correction to this project's own stated fact.** Censusing every marker in all **64** real
> `.err` files on this machine gives: **`** Warning **`** one space both sides (**4,881**),
> **`** Severe  **`** one space before / two after (**37**), **`**  Fatal  **`** two both sides
> (**1**). **The "two spaces" rule we have been repeating is only half right, and a literal written
> for two-spaces-both-sides misses `Severe` exactly as badly as the one-space literal did.** This is
> why the helper tolerates any run of whitespace instead of enumerating spellings.
>
> 🔴 **Why it stays open — two live sites remain, both outside the executor's authorised write-set and
> correctly flagged rather than edited:** `tests/test_sim_integration.py:171` matches
> `"**  Severe  **"`, which matches **0 of the 37** real Severe lines — a live latent instance of the
> same bug; and `openubem/simulation/runner.py:140` matches `"**  Fatal  **"`, which does match the
> one real Fatal instance found but is a bare literal rather than the tolerant helper.
>
> **Leg B — the cause is not backfillable, and the scope is wider than the six failures.**
> Director-re-derived over all rows, not a sample: **12 adopted manifests, 8,160 rows, every
> `work_dir` exists and every one is empty — 8,160 empty, 0 with any file.** Reported as a complete
> result, not backfilled with a hypothesis. Report: `extra/FIX_open-45_severe-matcher.md`.

> **Amended 2026-08-13 (T01 of `PLAN_two-measurements-2026-08-13.md`, signed at CP-1). A fourth
> instance of the marker-matching family — this time inside the shared helper that was built to end
> the family.**
>
> 🔴 **`SEVERE_RE` in `openubem/results/err_parse.py` is anchored `^\s*\*\*\s+Severe\s+\*\*`, and
> EnergyPlus also writes severe errors in a *recurring* form that begins with a run of asterisks
> before the marker** — `   *************  ** Severe  ** …`. The `^\s*` anchor cannot match it, so
> `count_severe` **undercounts**. Director-verified on a real file rather than reasoned:
> `la_urban_fast_zone/way_402215469/eplusout.err` — line 69 is counted, line 87 (recurring form) is
> missed, and the file's own footer at line 109 says **`2 Severe Errors`** against the helper's **1**.
>
> ✅ **Scope, stated exactly: this affects the severe *count* column only. It changed no cause
> attribution** — every fatal in the OPEN-42 population is located by `FATAL_RE`, and the preceding
> `** Severe **` is found by backward scan from the fatal, both of which use the standard form.
> **The six-failure result is unaffected.**
>
> ⚠️ **Not fixed, deliberately.** Patching a shared helper is remediation and the task that found this
> was a measurement task. The item stays open with **three** live sites now, not two:
> `tests/test_sim_integration.py:171`, `openubem/simulation/runner.py:140`, and
> `openubem/results/err_parse.py`'s `SEVERE_RE` itself. 🔴 **A fix must sweep for the recurring form
> as well as for whitespace — the helper proved that fixing one spelling is not the same as fixing
> the family.**


**How it was found.** T07 (OPEN-42) was told to find out why the six failed buildings carry an empty `error_summary`. The answer turned out not to be about the six.

**The defect.** `scripts/validation/v12_cell_pipeline.py:625` collects error lines with `if "** Severe **" in l` — **one space each side.** EnergyPlus writes `** Severe  **` — **two spaces after "Severe".** The substring never matches. `error_summary` is therefore assigned `""` on every path.

**Measured, director-verified, not inferred:**
- The one-space literal is present at `:625`, read from the file.
- Real `.err` files in this repo contain `** Severe  **` (two spaces), confirmed byte-for-byte with `cat -A`.
- **Across all twelve adopted `04_simulation_manifest.parquet` files — 8,160 rows — the count of non-empty `error_summary` values is 0.**

**Why it matters, and why it is not an emergency.** `n_severe` and `n_warnings` are parsed by a *different* regex (`(\d+)\s+Warning;\s*(\d+)\s+Severe`) which **does** match, so the failure *counts* on which OPEN-41 and OPEN-42 rest are sound. What is lost is the **cause text** — which is exactly what T07 went looking for and could not find. **No published number is affected. The cost is diagnostic: every future failure will also arrive causeless until this is fixed.**

🔴 **This is the third instance of the same two-space bug in this codebase**, after the `has_fatal` column (measured wrong, never to be used) and the `** Fatal **` matcher. **A fix should sweep for the whole family, not patch line 625.** No fix was made inside a measurement task, by rule.

---

## 3. Theme B — Register hygiene

### ~~OPEN-05~~ — The same defect is logged twice, as E-LA-21 and E-LA-39 — **CLOSED 2026-08-05** ✅

**Disposition.** The item's required first measurement — sweep the full `E-LA-nn` and `E-UTCI-nn` ID
space for further duplicates — **has been made.** Report:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-05_defect-id-sweep.md`.

**Result: no further duplicates exist.** 41 logged `E-LA` IDs (01–41; `E-LA-42` appears only as a
"next free" marker, not a defect) and 16 logged `E-UTCI` IDs (01–16). **Both sequences are fully
dense — no gaps, so no lost records.** No ID carries two unrelated meanings. Three further candidate
pairs were examined and all three rejected with reasons (E-LA-06 vs the E-LA-14/16/18/19/23 lineage —
already self-corrected by the project at its own 2026-07-26 audit; E-LA-33 vs E-LA-34 — same origin,
different objects, one fix does not close both; E-LA-38 vs E-LA-40 — subset population but the causal
link is explicitly an unconfirmed hypothesis). **E-LA-21 = E-LA-39 remains the only true duplicate.**

**Director audit, 2026-08-05.** Both ID ranges were independently re-enumerated by the director from
the working tree; the inventory reproduces exactly. The sweep's method was validated by requiring it
to rediscover the known E-LA-21/E-LA-39 pair without being given it as an answer — it did, from the
raw content sweep. **Signed.**

**Standing consequence, carried forward:** treat **E-LA-39 as an alias of E-LA-21**. Neither frozen
progress-log entry is to be rewritten. **Next free IDs: `E-LA-42`, `E-UTCI-17`** — the latter was
derived here and appears in no other document.

*(Original entry preserved below, unedited.)*

### OPEN-05 — The same defect is logged twice, as E-LA-21 and E-LA-39 ✅

**Found while compiling this register.** Both describe the identical defect: the harvest scripts'
`has_fatal` column tests for `"** Fatal **"` (one space) against EnergyPlus's real `"**  Fatal  **"`
(two spaces), so it reads `False` on all 8,160 rows — including the 7 that carry a literal Fatal.

- **E-LA-21** — logged 2026-07-25, `e-la-20/PLAN_e-la-20_investigation.md:493`, carried OPEN through
  two subsequent plans as explicitly out of scope.
- **E-LA-39** — logged 2026-08-04 in the storey-matching arc, registered as a **new** finding.

**This is the failure mode the register is meant to prevent:** an open defect that stays open long
enough to be rediscovered, consuming a second ID and a second audit. **Neither entry should be
rewritten** (both are frozen progress-log records) — the correction belongs here and in whichever
plan next touches the harvest scripts. **Treat E-LA-39 as an alias of E-LA-21.**

**Before opening any work:** sweep the full `E-LA-nn` and `E-UTCI-nn` ranges for further duplicates.
One found by accident implies others found the same way.

### OPEN-29 — Defects whose last recorded status is OPEN, that this register never adopted ❓
*Added 2026-08-05, found by the OPEN-05 sweep — which was not looking for it.*

**How it was found.** The OPEN-05 sweep had to inventory every `E-LA-nn` ID with its status in order
to compare descriptions. That inventory (`extra/MEASUREMENT_open-05_defect-id-sweep.md` §2.1) shows roughly
**eight IDs whose last status word at their own defining site is OPEN, and which appear nowhere in
this register as an item.** Candidates, from the sweep's own status column: **E-LA-06** (the
flow-balance half, *"never revisited"*), **E-LA-11**, **E-LA-12** (*"OPEN, LATENT/MASKED IN
PRODUCTION"*), **E-LA-13**, **E-LA-15**, **E-LA-16**, **E-LA-17**, **E-LA-18**, **E-LA-19**,
**E-LA-30**, **E-LA-33**.

**And E-LA-21 itself.** Closing OPEN-05 closes the *duplication*, not the *defect*. The `has_fatal`
column is still dead fleet-wide and, with OPEN-05 struck, it is now tracked in this register **only**
inside a closed item's disposition. That is precisely how it got rediscovered as E-LA-39 in the first
place. It is named here so it cannot happen a third time.

**Why this is ❓ and not a finding.** A status word at a defect's *defining* line is not its current
status — several of these were very likely closed by later work whose closure note lives in a
different document. The sweep read defining sites, not closure trails, because that is what
deduplication required. **The candidate list above is unverified and must not be treated as a list of
live defects.**

**First measurement.** For each candidate ID, follow its citations forward to the latest document that
mentions it and record its *final* recorded status, with a `path:line`. Output: a two-column table —
genuinely-still-open vs closed-elsewhere. Cheap, mechanical, no simulation. Only the first column
becomes register items.

**Why it matters more than housekeeping.** The register's stated purpose is to be *the single place
open work is recorded*. If defects can be OPEN at their own defining line and absent from the register,
then the register is not yet that place, and its completeness claim (§0) is overstated. This item is
the register auditing itself.

**Amended 2026-08-06 (N01). The measurement is made, and the answer is: the completeness claim was
overstated. ✅** Report: `extra/MEASUREMENT_open-29_defect-status-trace.md` +
`openubem/outputs/comparisons/open29_defect_status_trace.csv`. All 12 candidates forward-traced to
their last-dated mention.

**Method validated before the results were accepted.** E-LA-20 — *not* a candidate, and a defect
whose closure lives in a different document from its defining line — was run blind through the
procedure and correctly returned `FIXED, verified 150/150`
(`docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:68`, CP-C signed
2026-07-25). Without that control the buckets below would not be trustworthy.

| Bucket | n | IDs |
|---|---|---|
| **CLOSED-ELSEWHERE** | 3 | E-LA-11, E-LA-12, E-LA-13 — all closed at the structural-fixes CP-B/CP-C (2026-07-23), reconfirmed 2026-07-25 |
| **STILL-OPEN** | 9 | E-LA-06 *(flow-balance half)*, E-LA-15, E-LA-16, E-LA-17, E-LA-18, E-LA-19, E-LA-21, E-LA-30, E-LA-33 |
| **SUPERSEDED** | 1 | E-LA-06 *(warmup half)* → folded into the E-LA-14/16/18/19/23 lineage |
| **NO-STATUS-EVER** | 0 | — |

*(13 rows / 12 IDs — E-LA-06 splits across two buckets, which is why it appears twice.)*

**🔴 These nine are now tracked here.** This item becomes their register home rather than minting nine
top-level `OPEN-nn` items — they are defect-level, not item-level, and nine new rows would make §1
unreadable without adding information. **The completeness claim in §0 is repaired by this paragraph,
not by the count.**

| ID | Why it is still open |
|---|---|
| **E-LA-06** | the `CheckAirLoopFlowBalance` half; never revisited since 2026-07-26 |
| **E-LA-15 / 16 / 17** | sizing / cooling-UA / persistent-divergence Fatals; last confirmed present 2026-07-24–25, **no fix ever claimed** |
| **E-LA-18 / 19** | the warmup lineage — and the *"cosmetic"* label on it has **explicitly never been tested**. Read with **OPEN-09**, which is the same unexamined claim. |
| **E-LA-21** | the dead `has_fatal` column — see the escalation below |
| **E-LA-30** | the underlying script was never fixed; the project simply stopped using it. **Limbo, not closure.** |
| **E-LA-33** | confirmed still open 2026-08-04 (`t20_layout_assign_full_sweep.py:31-32`) and again in this register 2026-08-05 |

**🔴 E-LA-21 is larger than one line, and the director found this while auditing N01.** N01 reports it
live at `scripts/cluster/t20_harvest_layout_assign.py:259`. **Independently verified, and it is not
one site — the same one-space `"** Fatal **"` test is replicated across at least four harvest
scripts:** `t20_harvest_layout_assign.py:259`, `t08_harvest_results.py:239`,
`t07_harvest_results.py:198`, `t07b_run_auto_refit_local.py:329`. Meanwhile
`scripts/analysis/a2_parse_results.py:99,106` and `a3_measure_band_deletion.py:117` use the **correct**
two-space form — so **the project already contains both the right and the wrong test, in different
files, and has done for months.** Every harvest generation this project has produced reports zero
fatals by construction. **This is the strongest candidate among the nine for promotion to a full
register item, and the manager has deliberately not promoted it without the user** — it is a
one-character fix whose consequence is that a fleet-wide correctness column has never worked.

**🔴 Escalated 2026-08-06** (`PLAN_compute-queue.md` §8, "AUDIT — C02 halted by `MemoryError`;
CP-C2 NOT signed", FINDING 2). **A fifth occurrence is now confirmed**, at
`scripts/cluster/t08_local_remainder.py:430` — **and this is the script generating results today.**
Demonstrated on raw artifacts, not inferred: of the **2,422** `eplusout.err` files the E02 run
produced before it halted, **2 contain a real fatal and both write it two-space**
(`**  Fatal  ** Program terminates due to preceding condition.`); the one-space test
**matches 0 of 2**. Stated precisely, because it cuts two different ways: **the failure *count* is
not affected** — `status` is derived from the process return code, not from `has_fatal`, and both
failures were correctly counted (736/738 in the harvest) — **but the `has_fatal` column and the
end-of-run `Fatal-free: YES` banner are worthless**, and would report a clean run over any number of
real fatals.

**✅ Amended 2026-08-06 (C07, manager-audited) — the fifth occurrence is FIXED; the other four are
not, and that is deliberate.** `t08_local_remainder.py:430` now tests `\*\*\s+Fatal\s+\*\*`. The
before/after was demonstrated on the same population rather than asserted: over the 2,422 `.err` files,
the old one-space test matched **0** and the new one matches **2** — `way_266149332`, `way_266170765`.
**Both negative controls are non-vacuous**: the decorative lines `************* Fatal error -- final
processing.` and `************* EnergyPlus Terminated--Fatal Error Detected.` are physically present in
those same two files, so a looser expression would have over-counted; this one does not match either.
`git diff --stat` confirms exactly one script touched.

**Three limits on that fix, stated so nobody over-reads it.** (1) It changes **no published number**
and **no failure count** — `status` was always derived from the process return code, which was right
all along. (2) `has_fatal` is computed at harvest time and never persisted, so nothing on disk is
stale and every future harvest is corrected automatically, `print_cp4_local_report()`'s `Fatal-free:`
banner included. (3) 🔴 **E-LA-21 is NOT discharged.** The four harvest scripts
(`t20_harvest_layout_assign.py:259`, `t08_harvest_results.py:239`, `t07_harvest_results.py:198`,
`t07b_run_auto_refit_local.py:329`) were left untouched **on purpose** — fixing them is the user's
decision under this item, not a side effect of a runner repair. **The standing rule "never use the
`has_fatal` column" remains in force for every pre-2026-08-06 artifact.**

**✅ RULED by the user 2026-08-09 — RULING C: fix it everywhere.** ~~fixing them is the user's
decision under this item~~ — the decision is now taken. The question put was whether to repair only
the script generating today's results (the C07 precedent) or every remaining occurrence; the answer
was *"fix the error check everywhere."* Implemented as **task R06** in
`implemenation/PLAN_speed-resume.md`. `t08_harvest_results.py` was repaired separately as R02 the
same day (verified by the manager at `:246`, `import re` at `:25`).

**🔴 The count in this item is wrong, and this is the correction.** A fresh grep on 2026-08-09 finds
the one-space test at **six** live sites, not four. The two this register never named are
`t17_harvest_layout_assign.py:254` and `t18_harvest_layout_assign.py:251`; line numbers have also
drifted (`t19`/`t20` at `:259`, `t08_harvest_results.py` was at `:245`, not `:239`). ~~replicated
across at least four harvest scripts~~ → **six**. The phrase "at least four" was doing real work and
was still an undercount; **the lesson is the register's own rule — a line-number citation is
evidence of a past reading, not of present state, and must be re-grepped before it is acted on.**

**Two further occurrence classes, recorded here so they are not rediscovered a fourth time.**
(1) `docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/scripts/t19_harvest_layout_assign.py:259`
— an archived copy inside a closed arc's evidence folder. **Deliberately not fixed:** editing archived
evidence falsifies the record of what that arc actually ran. (2) `scripts/diagnostics/`
`t01_reproduce_degenerate.py:108`, `t04_validate_way428643335.py:133`, `t06_validate_relation6374725.py:153`
test the variants `"**  Fatal **"` and `"** Fatal  **"` — **neither is the true two-space form, so these
are wrong too**, in a third way this register had not recorded. Out of scope for R06 (one-off
diagnostics from closed arcs whose conclusions are already written), but **their conclusions were
reached with a fatal test that could not fire**, and no one has asked what that implies. That question
is open and belongs to this item.

**✅ R06 is DONE and manager-audited the same day, 2026-08-09.** All six live sites now test
`\*\*\s+Fatal\s+\*\*`; `git diff --stat` shows `6 files changed, 12 insertions(+), 6 deletions(-)` —
one `import re` plus one substitution each, no reformatting — and all six compile. **The audit was an
independent re-derivation, not a reading of the report:** over the halted E02 run's **2,422**
`eplusout.err` files the old literal matches **0** and the new regex matches **2**
(`nyc_centre/sim_out_auto/way_266149332`, `way_266170765`). **Both non-vacuity conditions hold** — the
corpus contains real fatals, so "before" is *shown* to differ from "after" rather than asserted; and
the count is exactly 2, not 4 or 2,422, while the decorative lines `************* Fatal error -- final
processing.` and `************* EnergyPlus Terminated--Fatal Error Detected.` sit in those same two
files, so the new expression is not simply looser. These are the **same two stems C07 found on
2026-08-06 through an unrelated execution path**. **No one-space literal survives anywhere under
`scripts/` or `openubem/`.** Full audit table: `implemenation/PLAN_speed-resume.md` §8, "AUDIT — R06".
🔴 **E-LA-21 is now closed as a live code defect; OPEN-29 is NOT closed** — eight other defect IDs
remain live inside it.

**What R06 does NOT do.** It does not re-run any harvest, so no historical output is regenerated;
past tables keep whatever `has_fatal` they were written with. **The standing rule "never use the
`has_fatal` column" therefore still holds for every pre-2026-08-09 artifact** — the fix corrects the
future, not the record. Whether any published conclusion ever depended on that column is a **separate
unmeasured question** and is not settled by this ruling.

**The register's own framing was wrong about one candidate, in the instructive direction.** E-LA-11
was a candidate only because its *defining* line carries no status word — but two later documents
(2026-07-23, 2026-07-25) explicitly close it. That is the §5-corollary trap firing in reverse: not a
stale OPEN, but a **stale absence of a word**. Recorded because the next sweep will meet it again.

**Stated limitation of the reverse-direction check.** N01 also checked whether any register item names
an `E-LA` ID that is in fact closed; it found none. **But that check covered only the six items that
name a specific ID** (OPEN-01, 06, 07, 08, 09, 10), not the register as a whole. **The reverse
direction is therefore spot-checked, not swept** — do not cite it as an all-clear.

#### 🔵 2026-08-12 — the malformed-fatal-test class is finished, and measured against the corpus

Plan `implemenation/PLAN_five-item-sweep-2026-08-12.md` T06. R06 closed E-LA-21's *one-space* class in
the harvest scripts. This pass closes the **malformed-variant** class R06 left behind.

**Fixed:** `scripts/diagnostics/t01_reproduce_degenerate.py:108`,
`t04_validate_way428643335.py:133`, `t06_validate_relation6374725.py:153` now use R06's regex
`\*\*\s+Fatal\s+\*\*` instead of the literals `"**  Fatal **"` / `"** Fatal  **"`. Their `Severe`
checks were left untouched (out of scope). The archived copy at
`docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/scripts/t19_harvest_layout_assign.py:259` is
deliberately **not** fixed — `docs_DONE/` is frozen.

**🔴 A seventh site, which this register had never recorded**, found by the director while verifying
the citations before the plan was written: `scripts/validation/phaseE_cpb_fixtures.py:176` counts
`txt.count("** Fatal  **") + txt.count("**  Fatal  **")` — a union of a malformed form and the true
form, so unlike every other site its risk is **over**-counting, not under-counting. **Reported, not
fixed.**

**The measurement, over all 40,800 `eplusout.err` files of the E02 corpus — not sampled, and
re-derived independently by the director:**

| variant | files matched | vs ground truth **44** |
|---|---:|---:|
| `**  Fatal  **` (true two-space form) | **44** | 0 |
| `** Fatal **` (one space — the R06 class) | **0** | −44 |
| `**  Fatal **` (malformed, used by the three scripts) | **0** | −44 |
| `** Fatal  **` (malformed, used by the three scripts) | **0** | −44 |
| `\*\*\s+Fatal\s+\*\*` (R06 regex, now in all three) | **44** | 0 |
| `phaseE_cpb_fixtures.py:176` two-term union | **44** | 0 |

**The malformed variants match nothing whatsoever.** Not rarely — never. The test these three scripts
have run could not have fired on any file in the corpus, which is the non-vacuity proof this item
required and is decisive rather than suggestive. The seventh site's over-count risk is **real in
principle and never realised on real data**: its malformed term matches zero files, so the union
lands on exactly 44. It stays reported.

**Did any recorded conclusion change? No — checked per script, not assumed.** t01's own arc document
records that its building never produced a `Fatal` line at all; t04 never asserts on `severe_lines` in
the Fatal path; t06's single assertion on it was vacuously satisfied by a genuinely clean 0-Severe
run, so it passes identically either way. **No past diagnostic conclusion is retracted** — the broken
test was harmless where it sat and dangerous only for future use.

**No fifth malformed site exists** under `scripts/` or `openubem/` (re-grepped 2026-08-12).
**OPEN-29 is still NOT closed** — the eight other defect IDs it carries are untouched by this.
**Evidence:** `openubem/outputs/comparisons/open29_diagnostics_fatal_recheck.csv`,
`extra/FIX_open-26-29_polish-and-fatal-tests.md`.

#### ⏳ Amendment 2026-08-13 — **all eight re-checked against HEAD; all eight STILL-OPEN; the item cannot be closed on this machine**

*T05 of `implemenation/PLAN_five-more-items-2026-08-13.md`. Report:
`extra/MEASUREMENT_open-29_eight-defect-recheck.md` — carries a per-ID verdict table with a
file:line citation and a reproducing command for each. Measurement only; no code changed.*

Each of `E-LA-06` (flow-balance half), `E-LA-15`, `E-LA-16`, `E-LA-17`, `E-LA-18`, `E-LA-19`,
`E-LA-30`, `E-LA-33` was re-derived **from HEAD source**, not taken from the 2026-08-06 status trace.
**No verdict changed.** `git log --since="2026-08-06"` across every cited file shows only two touches
in the whole window, both R06's regex fatal-test fix — unrelated to all eight mechanisms.

**🔴 Two findings outrank the null result.**

**1. `E-LA-16` is one ID carrying two different failure signatures.** Its own defining text
(`docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:279`)
describes a **cooling-coil-design-UA / cooling-tower-UA-autosize** family. But
`implemenation/PLAN_compute-queue.md:343` and `extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md:116`
both file it in the **`CheckWarmupConvergence` "cosmetic"** lineage, and
`openubem/geometry/layout_assigner.py:863-865`'s live comment groups it the same (inconsistent) way.
Both readings are internally consistent with their own source. The executor correctly declined to
adjudicate it inside T05's scope and reported it instead. **Opened as `OPEN-51`.**

**2. Closing this item is cluster-only, and that is now established rather than assumed.** The
remaining measurement each of E-LA-15/16/17 needs is a fleet-wide re-count of its mechanism string in
the raw `eplusout.err` files of the 8,160-building T20 harvest — **those live only on Speed.** The
local `openubem/outputs/comparisons/t20_layout_assign_eui.csv` cannot substitute: it is dated
2026-08-04 (pre-R06), and its columns (`has_fatal`, `n_severe`, `n_warmup_convergence`) do not
separate these signature classes — `has_fatal` is independently disqualified as evidence for any
pre-2026-08-09 artifact under this register's own standing rule. The 948 local `.err` files under
`docs/docs_DONE/SETUP/layoutAssigner/debug/` are debug-leg runs, not a fleet sweep. Same for a
current fleet `CheckAirLoopFlowBalance` count (E-LA-06's half). **Out of local reach — not a
shortcut taken.**

**E-LA-18/E-LA-19 against OPEN-09's C06:** C06 discharges the *accuracy* question for exactly one
population (150 `nyc_rural`/`SmallOffice` buildings, 96.3% distribution overlap, residual ≈0.20
kWh/m² at the median) and **explicitly does not generalise**. The *mechanism* is unpatched at HEAD,
so the defect stands. **The item stays open, and the next move on it is a cluster job.**

### ~~OPEN-33~~ — Archiving an arc breaks every document that cites it ✅ **CLOSED 2026-08-12**
*Added 2026-08-06, from M06's §7 sweep. Measurement already made — this item is actionable on sight.*

**What happened.** As arcs close, their folders move from `docs/docs_ACTIVE/<arc>/` into
`docs/docs_DONE/<AREA>/<arc>/`. The citations pointing at them are never updated. `docs_ACTIVE/` now
holds only the `openings` arc; **every other `docs_ACTIVE/…` path in the repository is dead.**

**Measured, 2026-08-06:** **58 distinct dead paths**, cited from **23 live documents**, across
**8 arcs** (`simulation-Resolution` 28, `input` 9, `hvac-ServiceLoads` 5, `3D` 5,
`phaseC_combinedResim` 4, plus `UTCI`, `misclassification`, `layoutgenerator`). Resolution was
attempted for each: **all 58 resolve** — the material is intact, only its address changed. Four files
were additionally **renamed** by their move (`DONE_`/`DONE-` prefixes, re-nesting under `DONE/`), so a
prefix substitution alone will not find them.

**Why this is a register item and not a chore.** Two reasons.

1. **`docs/PROJECT_CHECKLIST.md` is the user's own monitoring surface**, and it carried **26** dead
   citations — including the layoutAssigner arc's completion report, all four of its plan docs, and
   both director prompts. Every route from the checklist into that arc's evidence was broken.
2. **This register's design depends on the opposite being true.** §0 promises each item records
   *"where the evidence lives"*. An evidence pointer that does not resolve is indistinguishable, to a
   fresh session, from evidence that does not exist — and a fresh session is exactly who reads it.
   Two published explanation documents were also rendering **three broken figures**.

**Fixed 2026-08-06 (partial, deliberately):**

| Surface | Action |
|---|---|
| `docs/docs_EXPLANATION/` (6 files) + `docs/docs_REPORTS/REPORT_phaseE_final.md` | **Repaired in place.** Every link re-verified to resolve; two pre-existing relative-depth bugs (`../` where `../../` was needed) fixed at the same time. Zero dead paths remain. |
| `docs/PROJECT_CHECKLIST.md` | **Migration map added at the head of the file**, not rewritten. Its journal blocks are append-only; rewriting paths inside frozen entries would violate that rule for a navigation gain the table delivers anyway — and the table covers all 8 arcs at once, not just the ones cited here. |
| `docs_DONE/` arc records (26 files), `docs_main/` specs, `docs_TODO/layoutgenerator/` | **Deliberately untouched** — frozen, read-only, and user-excluded respectively. Resolved via the map. |

**What remains open.** Only the *recurrence*, not the backlog. ~~**Decision owed:** whether archiving an
arc must include a citation sweep, in the same way OPEN-31 asks whether ratifying a classifier change
must include a fixture before/after.~~ **Both items are the same shape** — a step that is obviously
right, that nobody owns, discovered weeks later by someone else's investigation.

> **✅ RULED 2026-08-09 — the sweep is obligatory.** Ruled as one question with OPEN-30 and CP-M3;
> the user answered *"yes to all three — make them obligatory."* **Archiving an arc is not finished
> until the citations pointing into it have been swept and repaired.**
>
> **The measured shape of the work, so the rule is costed honestly rather than assumed cheap:** the one
> sweep ever run found **58 dead paths in 23 live documents across 8 arcs**, and **four files were
> renamed by their move**, so a prefix substitution alone does not find them — any tooling must resolve
> by filename, not by path rewriting. Estimated ~30 minutes per archive, mechanical.
>
> **The exclusions already established stay excluded:** `docs_DONE/` records, `docs_main/` specs and
> `docs_TODO/layoutgenerator/` are frozen / read-only / user-excluded and are resolved through
> `PROJECT_CHECKLIST.md`'s migration map, not by editing them. The sweep covers **live** documents.
> ~~**Item stays open until the rule is written where the next person archiving an arc will meet it.**~~

#### ✅ CLOSED 2026-08-12 — the rule is written, and the re-sweep is clean

Plan `implemenation/PLAN_five-item-sweep-2026-08-12.md` T07. **The closure condition set on 2026-08-09
was "the rule is written where the next person archiving an arc will meet it." It is now met.**

**Where it was written.** The head section of `docs/PROJECT_CHECKLIST.md`, directly beneath the
2026-08-06 migration-map table and before the closing `---` — not in a journal block, which is
append-only. Director verified the diff: **10 insertions, head section only, no journal entry
touched.** `CLAUDE.md` was deliberately **not** edited (see the question below). The text carries all
four things this item measured: the obligation itself, the **resolve-by-filename** requirement *with
its reason* (four of the 58 originals were renamed by their own move, so prefix substitution misses
them), the three standing exclusions, and the honest ~30-minute cost.

**Re-sweep, 2026-08-12: zero genuine dead paths** against the 58-path / 23-document / 8-arc baseline.
The sweep resolves **279** citations across the live document set. The unresolved rows are forward
references to this same plan's siblings — reports from tasks that had not finished writing them yet —
not citation rot; the count fell as those tasks landed.

**🔴 The scanner was proved non-vacuous by the director, not by the executor.** A zero from an
un-controlled scanner is worthless. A scratch document citing a deliberately nonexistent file was
injected; the dead count rose by exactly one and the scanner named the citing file, the target, and
`resolved_via=none`; the scratch file was removed and the count returned. **The zero is a real zero.**

**One honest weakness, recorded rather than smoothed over.** No CSV survives from the 2026-08-06
sweep — only prose counts in `PROJECT_CHECKLIST.md`. "New since baseline" was therefore re-derived
from git commit `9270ac7` rather than diffed row-by-row against a stored artifact. **The 58-path
baseline is not verifiable at row level.** It is not relied on by this closure (which measures the
current state directly), but anyone who later needs that baseline must re-measure it, not cite it.

**Evidence:** `openubem/outputs/comparisons/open33_dead_path_sweep_2026-08-12.csv` (279 rows),
`extra/MEASUREMENT_open-33_archiving-rule-and-resweep.md`,
scanner `scripts/analysis/open33_dead_path_sweep.py`.

**Question left for the user, not decided by the director:** the rule now lives in
`PROJECT_CHECKLIST.md`. **`CLAUDE.md` is the file every session reads at startup**, and it was left
untouched on purpose because editing it was outside T07's authority. Whether the archiving rule also
belongs there is the user's call. **Until it is answered, a fresh session that never opens the
checklist will not know the rule exists** — so this closure is complete on its own terms, but the
recurrence it was opened about is only partly guarded against. **ID retired.**

---

## 4. Theme C — Simulation correctness

### OPEN-06 — Archetype labels are wrong for 41 of 8,160 buildings (E-LA-38) 📄
33 `LargeHotel` + 8 `SmallHotel` are labelled as Office archetypes by `05_results.gpkg`, the archetype
source shared unchanged since T17. **All 7 of the T20 fleet's failures are true `SmallHotel`** — 7 of
the fleet's 8 (87.5%), against 0.00% failure everywhere else. The fleet's only failure population *is*
the mislabel population.

**First measurement:** whether the mislabel originates in `05_results.gpkg` itself or in a step that
writes it. Fixing the symptom in the harvest would leave the source wrong.

**Amended 2026-08-06 (N04). ✅ Verdict: SOURCE defect — the classifier is right and the file is
wrong.** Report: `extra/MEASUREMENT_open-06-07-11_failure-population.md` +
`openubem/outputs/comparisons/open06_mislabel_population.csv` (41 rows).

The 41 were **recomputed from scratch** — not carried from the register — and land at exactly
**41/8,160**, matching 33 `LargeHotel` + 8 `SmallHotel` with zero discrepancy. Three were spot-checked
against raw OSM tags: `hotel`, `hotel`, `motel` — one named *"Wilshire Serrano Motel"* and recorded as
an office. `building_classifier.py` is unchanged since `0df422e`, so the 2026-08-04 classifier run is
still valid at HEAD and no re-run was needed.

---

🔴 **Amended 2026-08-06 (N08). THIS ITEM IS NO LONGER A LABELLING DEFECT. IT IS A PROVENANCE DEFECT.**
Report: `extra/MEASUREMENT_open-06-07_simulated-archetype.md`.

**The archetype column does not describe what was simulated.** The `LAUNDRYROOMFLR1` contradiction —
recorded 2026-08-06 as unresolved and deliberately not explained away — is settled, and it settles
against the file:

| | Value |
|---|---|
| What `05_results.gpkg` records for the three OPEN-07 buildings | **`SmallOffice`** |
| What the T20 `layout_assign` run **actually built and simulated** | **`SmallHotel`** |
| Evidence | the T20 run's own `eplusout.sql` `Errors` table + `eplusout.err`, surviving locally for all three |

**Director-verified by independent re-derivation 2026-08-06**, from
`%LOCALAPPDATA%\Temp\ubem_t20_harvest\la_urban_layout_assign\way_401910463\`. The zone names in that
run are not ambiguous: `GUESTROOM101`, `FRONTLOUNGEFLR1`, `MEETINGROOMFLR1`, `RESTROOMFLR1`,
`REARSTAIRSFLR1`, `LAUNDRYROOMFLR1`. **An office prototype has none of these.** The prototype that owns
them is `ASHRAE901_HotelSmall_STD2022_Buffalo.idf`, mapped from `SmallHotel` at
`openubem/geometry/layout_assigner.py:31`. The Severe is at `eplusout.err:52` and the file's own
summary attributes it to **Sizing** (`:89`), not Warmup — confirming N04.

**Read the direction carefully, because it is the opposite of what "mislabelled" suggests.** The
**simulation used the right archetype**; the **results file records the wrong one**. So:
- ✅ No simulated building was built from the wrong prototype — the physics was not corrupted.
- 🔴 **Every analysis that groups by `archetype_id` has been grouping by a column that does not
  describe the run.** That includes the per-archetype breakdowns in the published set.
- 🔴 The fleet's failure population is now explained rather than merely correlated: those buildings
  **really were simulated as hotels**, and the hotel prototype is what fails. The failures are genuine
  hotel-prototype failures, not an artifact of a wrong label.

**What this changes about the item's remedy.** Fixing the label alone would make the column agree with
the simulation for these buildings — but **nothing currently verifies that agreement anywhere**, which
is the actual defect. This is now the same shape as OPEN-30 (a resolved value the pipeline never
persists) and OPEN-35 (two stages disagreeing with no record kept): **the pipeline knows the right
answer at the moment it acts on it, and writes down a different one.**

**Still not known:** whether all 41 were simulated from their true archetype or only these 3 — the
other 38 have no surviving local artifact. **That is a cluster fetch, not a measurement**, and it is
not authorised here.

---

🔴 **Amended 2026-08-06 (N07). The writer was traced end to end, and the answer is that no writer in
this repository produces the value the file holds.** Report:
`extra/MEASUREMENT_open-06_archetype-writer-trace.md`.

**All three hypotheses the task was built to separate are disproved, each with evidence:**

| Hypothesis | Verdict | Evidence |
|---|---|---|
| **Lossy mapping** (Hotel silently mapped to Office) | **DISPROVED** | `LargeHotel`/`SmallHotel` are valid live archetypes — `openstudio_archetypes.json:86,93`, `building_classifier.py:212,216`. No whitelist removes them. |
| **Overwrite** (a post-hoc patch script) | **DISPROVED** | The only script that hand-patches `05_results.*`, `scripts/validation/phaseE_recover_10.py:38-50`, targets a **disjoint** hard-coded set of 10 osm_ids — the OPEN-11 buildings — with **zero overlap** with the 41. |
| **Stale join** (a leftover artifact) | **DISPROVED at every cache point** | Step 1's cache holds frozen git-unchanged raw data; Step 2 has no cache; Step 3's manifest is **unconditionally deleted before every run** (`v12_cell_pipeline.py:986-990`), a guard in place since 2026-06-25 (`075934c2`) — i.e. already present when the Phase-E fleet ran. |

**One writer, not several** — only `v12_cell_pipeline.py`'s Step 2 → 3 → 5 chain writes this column
into the committed files.

**🔴 The finding, stated plainly.** The write path was not merely read — it was **re-executed against
the exact frozen inputs the committed file was built from**, and it produces `LargeHotel`/`SmallHotel`
at every stage. **Never Office.** Yet the committed file carries Office archetypes for these
buildings, with **real, successfully-simulated EUI values** — not NaN, not dropped rows.

**So: the current code, run on the current frozen inputs, cannot reproduce the value the committed
file holds.** N07 reached the plan's own STOP condition and reported rather than resolved, which is
exactly right.

**Director-verified 2026-08-06 at row level**, independently of the report: `austin_centre/way/231123149`
carries raw `building_tag = "hotel"` in `01_buildings.gpkg`, and `05_results.gpkg` records
**`LargeOffice`**.

**Read N07 and N08 together — that is where this item now stands.** Four independent sources agree the
building is a hotel: the raw tag, the classifier at HEAD, the re-executed write path, and **the
simulation that actually ran**. Exactly one artifact says office: **the committed results file.**
**The column is an orphan — no code in this repository can account for it.**

**This is the same shape as OPEN-36**, discovered the same evening by a different route: *the
repository cannot account for something the project treats as authoritative.* **Two instances in one
evening, found by two executors who never spoke, is a pattern and not a coincidence.**

**A merge that looks tempting and is wrong.** Both this item and OPEN-35 involve buildings with
missing inputs, so it is natural to suspect one causes the other. **Director-checked: of the 41, only
14 are also in OPEN-35's 2,611 — against 13.1 expected by chance.** **No association. Do not merge
them.**

**🔴 A documented mechanism exists, and the director verified the citation.** The T11 run that produced
this file **is on record as having executed code that was never committed as such.**
`docs_DONE/BUGS/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md:482` (T11 entry, 2026-07-01)
records a **one-line working-tree fix** to `v12_cell_pipeline.py:520` — the reroute lambda's signature
— *"applied to the working tree during the run"*, validated with `ast.parse`, and **described only in
the progress log**, not isolated as its own commit until folded into `03e2121`.

**So it is established, not speculated, that the code executing during the T11 window is not fully
captured by any single commit.** Whether a second, unrecorded edit touched *classification* during
that same window **cannot be determined from files on disk** — N07 reports this as an open provenance
gap and explicitly does **not** assert it as the cause. **That is the correct handling and the
register adopts it unchanged.**

**What is NOT known, and must be measured before any plan:**
1. **Which code state produced the committed column.** It is not HEAD and not the T11-era state. **The
   candidate measurement:** check out the classifier at successive commits around 2026-07-01…07-03 and
   find one that emits Office for these 41. If none does, the value did not come from this repository
   at all — **and that is the more important answer.**
2. Whether the other 38 were also simulated from their true archetype (needs a cluster fetch).
3. ~~**Whether any other column of `05_results.gpkg` is equally unreproducible.** Nobody has checked a
   single one. **This is a no-CPU measurement and it is the natural next task.**~~ **Measured
   2026-08-06 (N14) — see the amendment at the end of this item. Answer: no, `archetype_id` is not
   alone; `data_quality_flag` is unreproducible too, on the same buildings.**

**What is still not known, and the task says so plainly:** *which* pipeline step writes the wrong value
into `05_results.gpkg`. The classifier is exonerated; the writer is not identified. **That is the next
measurement for this item**, and it is what stands between here and a plan.

🔴 **A contradiction surfaced that nobody had recorded, and it is not resolved.** All three failing
buildings diverge in a zone named **`LAUNDRYROOMFLR1`** — a *hotel* zone. If these buildings were
simulated as the offices the table says they are, **that zone would not exist.** So either the
simulation used the classifier's `SmallHotel` answer while the harvest table recorded the gpkg's
`SmallOffice` one — meaning **the archetype column does not describe what was simulated** — or
something else is going on. **Recorded as an open question, not adjudicated.** It matters beyond these
41 buildings: any per-archetype analysis reads that column.

---

🔴 **Amended 2026-08-06 (N14). The third open question above is now measured: `archetype_id` is NOT
alone.** Report: `extra/MEASUREMENT_open-06_column-reproducibility.md` +
`openubem/outputs/comparisons/open06_column_reproducibility.csv` (132 rows) +
`..._diff_examples.csv` (18 rows).

Stage 2 was re-run at HEAD — the real `t08_full_sweep.run_step2()`, imported not reimplemented — over
four **whole** cells (`nyc_centre` 738, `nyc_rural` 198, `austin_rural` 245, `nyc_suburban` 1,589) and
every one of the committed file's 33 columns was bucketed. **The other 8 fleet cells were not covered
and nothing here is claimed to generalise to them.**

| cell | REPRODUCES | DIFFERS | STAGE-3-OR-LATER | ABSENT |
|---|---|---|---|---|
| `nyc_centre` | 2 | 2 | 29 | 0 |
| `nyc_rural` | 2 | 2 | 29 | 0 |
| `austin_rural` | 4 | 0 | 29 | 0 |
| `nyc_suburban` | 4 | 0 | 29 | 0 |

**The `archetype_id` control PASSES, and the director verified it independently.** N14's re-derived
per-cell differ counts are `nyc_centre` 26 and `nyc_rural` 4, with 0 in the two other cells. Read
straight out of N04's `open06_mislabel_population.csv` (41 rows), the per-cell distribution is
`nyc_centre` 26, `la_urban` 5, `la_centre` 4, `nyc_rural` 4, `austin_centre` 2 — **zero** in
`austin_rural`/`nyc_suburban`. Exact match, including the two zeroes. A DIFFERS count in a cell with
no known mislabel would have been a new divergence; there was none.

**The second unreproducible column is `data_quality_flag`** — and it is a *computed* column, not a raw
passthrough: `classify()` appends an imputation-provenance token after a `|`. On `nyc_rural` all 4
differing rows are the 4 archetype rows, and the difference is **which imputation rule fired**:
`VINTAGE_NAN_PERMISSIVE_DEFAULT` at HEAD vs. `GROUPMODE_MED` in the committed file; on `nyc_centre`,
`HOTDECK_NEIGHBOR_MED`/`HOTDECK_NEIGHBOR_HIGH` at HEAD vs. `GROUPMODE_MED` committed. **So it is not
only the archetype that HEAD cannot reproduce — it is the recorded reason for the archetype.** That
is consistent with N07's open provenance gap (an uncommitted mid-run edit during the T11 window) but
**does not prove it**; not adjudicated here.

🔴 **Director correction to N14's own write-up, 2026-08-06.** §4 of its report states that
`data_quality_flag` differs on *"the same 9 rows that `archetype_id` differs on, in both cells
(nowhere else)"*. **That claim is refuted by N14's own CSV and is struck.** For `nyc_centre` the
counts are `archetype_id` **26** and `data_quality_flag` **38** — 12 rows carry a flag difference with
**no** archetype difference. Those 12 are a different mechanism: the diff-examples file shows them
differing only by a trailing `narrow_perimeter_fallback` token, and **director-verified by
independent grep, that token is written by `openubem/idf/builder.py:614-615` — a Stage-3 module.**
Stage 2 can never emit it, so those rows are the same spurious-difference trap the plan warned about
for `levels`/`height_m`, not a reproducibility defect. **N14 caught that trap for `footprint_area_m2`
and missed it for `data_quality_flag`.** The verdict survives the correction on a narrower and
cleaner basis: the genuine unreproducibility is the **imputation-provenance token**, on the same
buildings as the archetype (exactly so on `nyc_rural`, 4 of 4).

**A third geometry-derived column was found, and this part is a real contribution.** `levels` and
`height_m` were already known to be Stage-3 re-derived rather than Stage-1 passthroughs; N14 shows
**`footprint_area_m2` is a third**, and proved it **without Stage-2 code in the loop at all** —
comparing `01_buildings.gpkg` against `05_results.gpkg` directly, 715 of 738 `nyc_centre` rows already
differ, one by 101,106 m². Nothing under `openubem/semantic/` ever assigns that column
(director-verified: only read, at `building_classifier.py:185,749`). **Anyone diffing these three
columns naively will report a defect that is not there.**

**What this does and does not settle.** The 24 EUI/GWP + `iod` + `simulation_status` +
`error_summary` columns and `zoning_strategy` are Stage-3-or-later outputs, **absent from the Stage-2
frame entirely** — so 26 of the 33 columns remain **unchecked**, and checking them needs compute this
plan does not authorise. **This item stays open.** Its remaining first measurement is unchanged:
*which code state produced the committed column*.

**Amended 2026-08-06 (N16, `implemenation/PLAN_no-compute-queue-4.md`, director-audited by
re-derivation).** N14 covered four cells and said plainly it could not speak for the other eight.
**N16 covered those eight, and the sweep was built to fail.** The prediction was written into the plan
*before* the measurement: `archetype_id` must differ on **exactly 2 rows in `austin_centre`, 4 in
`la_centre`, 5 in `la_urban`, and none at all** in `nyc_urban`, `la_suburban`, `la_rural`,
`austin_urban`, `austin_suburban`.

**It held, in both directions.** 2/413, 4/226, 5/618, and `n_differ = 0` in the other five. The
director re-joined all 11 rows to N04's population on `(cell, osm_id)`: **11 of 11 matched on both
values, zero extra, zero missing.** Coverage checks arithmetically — 5,390 buildings here plus N14's
2,770 is **8,160, the whole fleet, whole cells, no subsets.**

**Three things this settles.**
1. **The 41-building mislabel population is fully accounted for.** Every building whose committed
   `archetype_id` cannot be regenerated is one N04 already named; there is no unknown remainder.
2. **There is no third unreproducible column.** `archetype_id` and `data_quality_flag` are the only
   two in DIFFERS anywhere in twelve cells.
3. **`data_quality_flag` is far less broken than N14's raw count suggested.** Of its 171 differences,
   **168 are Stage-3 tokens Stage 2 cannot emit** and only **3 are genuine provenance divergence**.
   Getting that split right required a proper tokenizer: beyond `narrow_perimeter_fallback`, N16 found
   four more Stage-3 appenders — `multipolygon_coerced_to_largest_part` (`builder.py:145`),
   `layout_assign_fallback_auto` (`:439`), `storey_match_<status>` (`:473`), and `idf_dp_coarse` /
   `idf_hull_simplification` (`geometry/footprint.py:33,38`) — **the last two comma-separated, a
   different and undocumented convention.** All five citations were opened by the director.

**And one finding that outlives the prediction.** The 3 provenance divergences are **not the same
buildings** as the archetype failures. In `la_urban`, `way/1176846930` regenerates its archetype
perfectly yet its provenance token differs (`GROUPMODE_MED` at HEAD vs `HOTDECK_NEIGHBOR_HIGH`
committed). In `la_centre`, the reverse: four archetype failures with **no** provenance divergence at
all. **The two defects are independent in both directions** — which finishes off N14's struck "same
rows" claim rather than merely correcting its count. *(The progress-log entry's prose called this
"both empty in the other six cells"; it is five. The report's own §4.3 table is correct. Corrected on
audit, not deleted.)*

**Unchanged: this item stays open**, and its remaining first measurement is still *which code state
produced the committed column* — the 26 Stage-3-or-later columns cannot be reached without compute.

---

#### ✅ CLOSED 2026-08-18 — T04 of `implemenation/PLAN_five-items-2026-08-18.md`. The remaining first measurement is answered: commit `67ede73` produced the committed column.

**All six historical states of `building_classifier.py` were run over the 41-building population**
(read-only `git show <sha>:openubem/semantic/building_classifier.py`, never checked out). Control
first: HEAD's classifier reproduced N04 exactly (41/41, 33 `LargeHotel` + 8 `SmallHotel`) after
correcting the harness to classify each full cell before filtering to the population (an earlier
harness draft that filtered first changed 2/41 results via batch-dependent levels-imputation — caught
by the control failing, fixed, re-verified). All six commits loaded; zero `NOT_LOADABLE`.

**Decisive finding: commit `67ede73` (2026-07-01) reproduces the committed `05_results.gpkg`
archetype exactly for all 41 buildings** — not the Office family loosely, the exact
`SmallOffice`/`MediumOffice`/`LargeOffice` subtype per building, 41/41 exact match
(`LargeOffice` 13 / `MediumOffice` 21 / `SmallOffice` 7 on both sides, director re-derived
independently and matches exactly). **The mechanism:** the sole diff between `67ede73` and `0df422e`
(2026-07-03) on `building_classifier.py` is the Hotel rule `RULE_LODGING_TIER` gaining a
`building_tag` check it previously lacked — at `67ede73` it read `function_tag` only. All 41 buildings
carry `hotel`/`motel` in `building_tag` with `function_tag` blank, so at `67ede73` they fell through
to an Office rule. **Timing confirms the mechanism, not merely correlates with it:** the T11 fleet
fan-out that produced the committed file ran 2026-07-01 23:14 → 2026-07-02 22:07 — after `67ede73`
landed (07-01 20:14) and entirely before `0df422e` landed (07-03 10:53, >12h after the fan-out
finished). The fan-out necessarily ran under the pre-fix classifier; `0df422e`'s commit bundled the
fix together with promoting the already-generated (pre-fix) results.

**This closes OPEN-06 and resolves N07's open provenance gap** (§ above, *"which code state produced
the committed column"*): the value did come from this repository's own classifier, just from
`67ede73`, one commit earlier than the fix that N07 checked against. No unrecorded mid-run edit is
needed to explain it. N07's caution not to assert a cause without evidence was correct; this is the
evidence.

**Caveat, disclosed and scoped:** all six historical module versions resolve their data-file imports
(`osm_to_use_class.json`, `openstudio_archetypes.json`) against the **currently-installed** package
data rather than each commit's own data files. `git log` shows those two files were touched only at
`42f0c1d` and `67ede73`, so the three commits between them ran their era's code against post-`67ede73`
data. This does not affect the decisive finding, which rests on `67ede73` and `0df422e`, both
post-dating the last data-file change.

**Evidence:** `extra/MEASUREMENT_open-06_classifier-archaeology.md`;
`openubem/outputs/comparisons/open06_classifier_archaeology.csv` (246 rows: 41 buildings × 6 commits).

### OPEN-07 — Three buildings regressed from success to failure (E-LA-40) ✅
`la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403` — all inside the
E-LA-38 population above. 3/8,160 = 0.037%. A multiplier-scaling-tips-a-warmup-divergence mechanism
was proposed and is **a hypothesis, not a cause**. Likely closes as a side effect of OPEN-06; confirm
rather than assume.

**Amended 2026-08-06 (N04). ✅** All three are confirmed inside the 41. **Raw `eplusout.err` survives
locally for all three** (T20 harvest cache) — *director-verified on `way/401910463`: 1 `** Severe **`,
1 two-space `**  Fatal  **`, zone `LAUNDRYROOMFLR1`, surface `P_LAUNDRYROOMFLR1_10010_0_10008`.*

**The hypothesis is SILENT, not confirmed and not refuted.** No T20 IDF survives locally to diff a
multiplier against, and the T19 cache directory for `way/401910463` is empty — fetching more would
require the cluster, which is forbidden. **Silence is the honest result and is recorded as such.**

**One correction to the hypothesis's own wording.** Each file attributes its Severe to the **Sizing**
phase (`0` Severe in Warmup, `1` in Sizing), not to warmup divergence as the forwarded hypothesis
states. Same class of failure — a surface heat-balance runaway — but **the phase named in the record
is wrong**, and a plan built on "warmup" would look in the wrong place.

**Independent reproduction of the register's own claim:** exactly **7** of the 41 rows carry
`t20_status == failed`, and all 7 are `SmallHotel`→Office mismatches (the 3 regressions plus
`nyc_rural/way/965718400`, `la_centre/way/427942886`, `la_urban/relation/6374725`,
`la_urban/way/428846131`). **None of the 33 `LargeHotel` mismatches fail.**

🔴 **Incidental corroboration of E-LA-21 on a real building.** `way/401910463`'s `.err` contains a
genuine two-space `**  Fatal  **`. The harvest's `has_fatal` column tests the **one-space** form, so
this building — a real, terminated, fatal run — is recorded as `has_fatal = False`. **The dead column
is no longer only a code reading; it is demonstrated wrong on a named building.** See OPEN-29.

### OPEN-08 — Archetype and vintage are not reproducible locally for data-poor buildings (E-LA-22) 📄 **partially quantified**
Re-running a past fleet generation at current HEAD silently diverges in archetype *and* vintage for
buildings with missing inputs. Leading suspect: a semantic-imputation commit landing after the fleet
run. **This is the item that quietly limits every other item** — any cross-generation comparison
(T17 vs T20, before vs after) rests on it. Findings on well-tagged buildings survive it; findings that
span generations may not.

**First measurement:** pin the divergence to a commit. Until then, treat every cross-harvest delta in
this project as carrying an unquantified confound.

**Amended 2026-08-05 (M05).** The confound is no longer unquantified. Cross-generation archetype
disagreement between T08 and T20 is **13.40%** on 4,530 shared buildings
(`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-28_harvest-generation-join.md`). Vintage
disagreement remains unquantifiable — no harvest persists a `vintage_standard` column, see new item
**OPEN-30**.

### ~~OPEN-34~~ — A 3-building local run is not archetype-faithful to the fleet — 🟢 **CLOSED 2026-08-11**

> **CLOSED 2026-08-11 (T06(a) of `PLAN_e02-audit-and-closure.md`). ID retired.**
>
> The mechanism was already settled on 2026-08-06 (batch-composition dependence in `_impute_levels()`:
> a group median of **51** storeys over 3 buildings against **19** over the full 738-building cell).
> What remained was whether **any published result** was ever produced from a batch small enough for
> that to fire — and this register recorded that as **reasoning, not measurement**. It is now measured.
>
> **All 12 adopted cells are whole.** Each `phaseE/<cell>/05_results.csv` has exactly as many rows as
> its own `01_buildings.gpkg` has building features, difference **0** in every cell:
> `austin_centre` 413, `austin_rural` 245, `austin_suburban` 437, `austin_urban` 425, `la_centre` 226,
> `la_rural` 149, `la_suburban` 1,343, `la_urban` 618, `nyc_centre` 738, `nyc_rural` 198,
> `nyc_suburban` 1,589, `nyc_urban` 1,779 — **fleet 8,160**. No cell's gpkg was missing or substituted.
> **The batch-composition effect cannot have touched any published number.**
>
> **Director re-derivation:** `nyc_centre` (738), `la_rural` (149) and the 8,160 fleet total recounted
> independently from the CSVs.
> **Evidence:** `openubem/outputs/comparisons/open34_cell_population_check.csv`.
>
> 🔴 **The standing consequence survives the closure and must keep appearing in executor briefs:**
> *a verification run on a subset of a cell must use the whole cell, or state that its archetypes are
> not fleet-faithful.* The item closes because no published artifact broke that rule — **not because
> the rule stopped mattering.**


*Added 2026-08-06, from the manager's audit of E01c. Not found by looking for it.*

**What is known, verified from two named files.** E01c ran 3 real `nyc_centre` buildings through the
real Stage-2 → Stage-3 path at HEAD to verify `building` mode. It verified the mode — and incidentally
produced this:

| `osm_id` | adopted `05_results.gpkg` | E01c local 3-building run at HEAD |
|---|---|---|
| `way/42496314` | levels 51, height 178.5 m → `SuperTallBuilding` | `SuperTallBuilding` — agrees |
| `way/42496352` | levels 1, height 3.5 m → **`LargeOffice`** | **`SuperTallBuilding`** |
| `way/42500728` | levels 1, height 3.5 m → **`LargeOffice`** | **`SuperTallBuilding`** |

Sources: `docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre/05_results.gpkg` and the
E01c run's `step3_building/03_manifest.parquet`. That cell holds **20 `SuperTallBuilding` of 738**.

**Two of three disagree, both in the same direction** — two 1-storey, 3.5 m buildings became the
tallest archetype in the library, sitting next to a genuine 51-storey neighbour.

**Why this is an item and not a curiosity.** **Every local verification this arc has run used a
3-building subset of a cell** — E01, E01b, E01c, and the timing benchmark that costed the overnight
re-run. If a subset does not reproduce the fleet's archetypes, those runs exercised the pipeline on
buildings the fleet never had, and E02's premise — that a local pass reproduces a cluster pass — is
unproven rather than false. **It is cheaper to know this before the re-run than after it.**

**Its relation to OPEN-08.** This is plausibly **E-LA-22 / OPEN-08 pointing at a new population.**
That defect is recorded for *data-poor* buildings; these sit in a dense, well-tagged urban cell. If the
two are the same mechanism, OPEN-08's blast radius is larger than recorded. **Do not merge them until
measured** — they may be different mechanisms that look alike.

> **✅ First measurement MADE — 2026-08-06 (N05). Mechanism identified: subset-dependence.**
> Report: `extra/MEASUREMENT_open-34_subset-archetype-fidelity.md`. **Director-audited: the mechanism
> was independently re-derived from the source, not accepted from the report.**
>
> | `osm_id` | 3-building run | **full-cell run (n=738)** | adopted fixture |
> |---|---|---|---|
> | `way/42496314` *(control)* | `SuperTallBuilding` | `SuperTallBuilding` | `SuperTallBuilding` |
> | `way/42496352` | **`SuperTallBuilding`** | **`LargeOffice`** ✅ | `LargeOffice` |
> | `way/42500728` | **`SuperTallBuilding`** | **`LargeOffice`** ✅ | `LargeOffice` |
>
> **The full-cell run reproduces the adopted fixture exactly, with the identical HEAD code** — and the
> cell-wide `SuperTallBuilding` count matches at **20/738**. So this is **not** OPEN-08 / E-LA-22 at
> HEAD; the code is not diverging. **Only the row population differs.**
>
> **The mechanism, verified by the director at source.** `_impute_levels()`
> (`openubem/semantic/building_classifier.py:123-142`) fills a missing storey count from a
> **group median computed over whatever rows are in the batch** (`:138-139`,
> `GROUPMEDIAN_LEVELS_MED`). Over 3 buildings that median is **51** — dominated by the one real
> skyscraper — which clears the 40-storey SuperTall threshold. Over 738 it is **19**, which does not.
> **The classifier's answer for a building depends on which other buildings were passed in with it.**
>
> **What this closes and what it does not.** It closes the question the item was opened on: a
> 3-building local run **is not archetype-faithful**, so E01/E01b/E01c and the timing benchmark
> exercised the pipeline on buildings the fleet does not have. Their *own* findings still stand —
> trimming, the disk guard, `building`-mode soundness are all properties of the machinery, not of
> which archetype was attached. **What it does not close:** whether any *published* result was
> produced from a subset small enough to matter. Every fleet artifact was produced cell-at-a-time,
> which is the population that reproduces — but that is reasoning, not a measurement.
>
> **Standing consequence, effective now:** *any* local verification run on a subset of a cell must
> either use the whole cell or state explicitly that its archetypes are not fleet-faithful. **Put this
> in every future executor brief that runs a subset.**

**First measurement — N05, completed 2026-08-06** *(originally dispatched as below)*
(`implemenation/PLAN_no-compute-queue.md` §6). Two candidate mechanisms, and the whole task is to tell
them apart: **(1) subset-dependence** — Stage-2 spatial imputation infers height/levels from
neighbours, and with 3 buildings in scope the real 178.5 m neighbour may propagate; **(2) HEAD
divergence** — today's classifier genuinely emits differently than the adopted run did, independent of
subset size. The discriminating experiment is Stage 2 only, run twice on `nyc_centre`: over the same
3 buildings, and over the whole cell. Report:
`extra/MEASUREMENT_open-34_subset-archetype-fidelity.md`.

### OPEN-35 — Two fallbacks fill the same missing storey count, and they disagree — ✅ **mechanism now PROVED at the simulation boundary 2026-08-11; still open**

> **Amended 2026-08-11 (T04(d) of `PLAN_e02-audit-and-closure.md`). This item does NOT close.**
>
> **The independent check this item has been waiting for has been made, and the mechanism is now proved
> from EnergyPlus's own output rather than inferred from source.** Restricting the denominator audit to
> the **2,611** buildings with neither `levels` nor `height_m` — all persisted at `levels = 1.0`:
>
> - In `auto`, `building` and `floor`: **100% within ±1% of their own broken denominator** — *by
>   construction*, because those modes build zones from `levels`, so a wrong `levels` makes the geometry
>   and the denominator wrong **together and consistently**. 🔴 **This is the trap: internal consistency
>   is exactly what a self-referential error looks like, and it is why no previous check caught this.**
> - Under `layout_assign`: **mean 2.3728, only 17.92% within ±1%** — because that mode assigns storeys
>   from the archetype instead of from `levels`. **The two paths disagree, measured, on 40,800 runs.**
>
> **That disagreement is the item, and it is no longer a reading of the source: it is a measurement.**
>
> **Still open, and the reason is not measurement.** Which fallback is *intended* — archetype-median
> storeys or one storey — is a **DESIGN question**, and the measuring task was forbidden to decide it.
> The population and mechanism are now both settled; the specification is not.
>
> **Evidence:** `openubem/outputs/comparisons/open01_denominator_audit.csv`,
> `open35_neither_population.csv`, `extra/MEASUREMENT_open-01_denominator-audit-e02.md`.


*Added 2026-08-06, found by the director while auditing N05's mechanism. Not what N05 was looking for.*

**What is known, verified at HEAD by the director from source.** When a building has **neither
`levels` nor `height_m`**, two different code paths invent a storey count, independently, and they do
not agree:

| Path | Stage | Fallback when both are missing | Verified at |
|---|---|---|---|
| `_impute_levels()` | 2 — **archetype selection** | the **group median** over the batch (19 for `nyc_centre`) | `openubem/semantic/building_classifier.py:138-142` |
| `derive_num_floors()` | 3 — **geometry construction** | **`1`** | `openubem/geometry/footprint.py:58-63` |

**The consequence, stated plainly.** For such a building the project **chooses the archetype as
though it were a 19-storey building, then builds and simulates it as a 1-storey building** — and the
published EUI divides by `footprint × levels` with `levels = 1`. `way/42496352` and `way/42500728` are
worked examples: `LargeOffice` was selected off a median of 19; the adopted fixture records
`levels 1.0, height 3.5`.

**This is not OPEN-34.** OPEN-34 is that the group median moves with batch composition. **This item is
that the two stages use different fallbacks at all** — it would still be true if the median were
perfectly stable, and it is true in the *full-cell* run, which is the population every published
result came from. **Do not let one close the other.**

**Read with:**
- **OPEN-01** — a different route to the same class of harm: energy simulated for one building,
  divided by another building's area.
- **OPEN-30** — the imputed value is **never persisted** (`building_classifier.py:636-639` keeps the
  raw columns byte-identical), so this disagreement leaves no trace in any output. Same shape as the
  discarded vintage token: a resolved value the pipeline throws away.

**Amended 2026-08-06 (N06). ✅ The size is measured, and it is large: 2,611 of 8,160 = 32.00% of the
fleet.** Report: `extra/MEASUREMENT_open-35-12_missing-input-census.md` +
`openubem/outputs/comparisons/open35_missing_input_census.csv` (12 cells + fleet row) +
`open35_neither_population.csv` (2,611 rows). **Director-verified by independent re-derivation
2026-08-06** — own script over all twelve `01_buildings.gpkg`, applying `_impute_levels`'s own
predicate (`pd.notna(levels)`, `pd.notna(h) and h > 0`): fleet `n=8,160`, no-`height_m` **2,806
(34.39%)**, **neither 2,611 (32.00%)** — identical to the executor's figures, cell for cell.

**Every one of the 2,611 is persisted at `levels = 1.0`** — checked on all 2,611 rows of
`05_results.gpkg`, not sampled, with **no exceptions**. So the mechanism does not merely exist; it
fires on **a third of the fleet**, and the geometry side always wins.

🔴 **The director's own re-derivation surfaced something the report did not: what the 2,611 were
classified as.**

| Archetype assigned | Count | Storeys the archetype implies |
|---|---|---|
| `MidriseApartment` | **1,028** | mid-rise |
| `SmallOffice` | 898 | low |
| `OpenUBEMUnknown` | 364 | — |
| `MediumOffice` | 119 | multi-storey |
| `LargeOffice` | 85 | multi-storey |
| `HighriseApartment` | **3** | high-rise |
| all others (9 archetypes) | 114 | mixed |

**1,031 buildings were given an explicitly mid- or high-rise residential archetype and then built as a
single storey**, and a further 204 got a Medium/Large Office. **That is the harm this item describes,
counted.** `OpenUBEMUnknown` at 364 is a separate observation worth keeping: for those the classifier
declined to guess at all, yet geometry still built one storey.

**The remaining unknowns** (item 1 below is now answered; 2 and 3 stand):

1. ~~**How many fleet buildings have neither `levels` nor `height_m`**~~ — **ANSWERED: 2,611 / 8,160
   (32.00%).** Original text kept per the never-delete rule: *"i.e. how many actually reach both
   fallbacks. Until that count exists this is a confirmed mechanism of unknown size. It is one query
   over the Stage-2 outputs, no simulation."* It was one query, and it took under five minutes.
2. Which of the two fallbacks is intended. **This is a DESIGN question, not a code question** — and
   note DESIGN §3D lines 238-253 is cited as the authority for `_impute_levels` while
   `derive_num_floors` cites nothing.
3. Whether the archetype/geometry disagreement is itself the cause of anything already observed —
   OPEN-18's √S vertical-form distortion involves the same mismatch between an archetype's expected
   height and the geometry actually built. **Recorded as a lead, not a finding.**

### OPEN-36 — A signed completion record describes code that has never existed in any commit ✅ **CORRECTED AT SOURCE 2026-08-13 — the record itself now says so**
*Added 2026-08-06, found by the director while auditing N10. Not what N10 was looking for.*

> ✅ **CLOSED 2026-08-13 (T04 of `PLAN_five-items-2026-08-13.md`; CP-2 director-signed).** All five claims
> were re-derived **by the director from git, not read off the executor's report**: `_draw_tier` — 0 hits
> in `imputation.py` and `git log --all -S… ` **empty on every ref**; `_draw_stratum_col_for` — no hits
> anywhere under `openubem/`; `_CANONICAL_TIER_ORDER` at `imputation.py:543` =
> `("fusion","spatial","ml","statistical")`, **no `"draw"`**; `IMPUTE_DRAW_METHOD_BY_TARGET` absent from
> `config.py`; both files clean in the working copy. **Every one holds.**
>
> 🔴 **The finding is sharper than "the record is false", and the sharper version is the useful one.**
> `tests/test_draw_methods.py` **is** committed and holds **exactly 53** test functions — precisely as the
> entry claims — at HEAD and in the working tree. **So this is a signed completion record for work that
> shipped as tests and never shipped as implementation.** The tests were written against code that was
> designed but not built. **Their existence is not evidence the wiring exists**, and until `imputation.py`
> is actually wired — **OPEN-17, the user's decision** — they run only under the `_HAS_DRAW_TIER` skip
> guard added by OPEN-44.
>
> 🟩 **The correction was placed IN the frozen record, on the user's ruling of 2026-08-13.** A dated
> ⚠️ CORRECTION banner now sits immediately under the T07 heading in
> `docs_DONE/INPUTS/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md:849`, and the false
> half of the Artifacts line is **struck, not rewritten** — append-and-amend, the same rule this register
> uses. **This is the first time this project has annotated a frozen implementation record**, and it was
> done because the alternative left a false completion claim readable with nothing beside it. Full
> command/output trail: `extra/MEASUREMENT_open-36_t07-record-correction.md`.
>
> ⚠️ **What this closure does NOT cover, stated so it is not mistaken for a clean sweep.** The same
> T07-shaped check was **not** run against the other governance-gap entries a prior resweep flagged —
> **T09b at line 946 of the same document, and T11.8 / T11.8b in `docs_Done/PLAN_phaseC_ml_imputer.md`.**
> They were out of T04's scope and are **not re-verified.** If those matter, they are a new item, not this
> one.

**What is verified, by the director, from git itself.** `IMPLEMENTATION_phaseC_ml_imputer.md:849`
carries a progress-log entry:

> `#### T07 — wire _draw_tier + registry + order (byte-identity re-proof) — completed 2026-07-16`

It is one of the most detailed entries in the project. It names artifacts (`_draw_tier`,
`_draw_stratum_col_for` added to `imputation.py`; `_CANONICAL_TIER_ORDER` extended to include
`"draw"`; `_TIER_HANDLER_NAMES` gaining `"draw": "_draw_tier"`), it reports test counts (**53 passed**
in the draw suite, **60 passed** across three protected regression suites, *"zero changed assertions"*),
and it flags a judgment call for manager review at CP-B.

**None of that implementation exists, and none of it ever did:**

| Claim | Verified state |
|---|---|
| `_draw_tier` in `imputation.py` | `git log --all -S"_draw_tier" -- openubem/semantic/imputation.py` → **no commit, ever** |
| `_draw_stratum_col_for` | **absent** from all of `openubem/` |
| `_CANONICAL_TIER_ORDER` includes `"draw"` | it is `("fusion","spatial","ml","statistical")` — `imputation.py:543` |
| `config.IMPUTE_DRAW_METHOD_BY_TARGET` | **zero** `DRAW` matches in `openubem/config.py` |
| working tree dirty / work-in-progress | `git status --short` on all three files → **clean** |

**🔴 The mechanism, and it is the part worth remembering: half of T07 was committed and half was not.**
`tests/test_draw_methods.py` **is** committed (clean, last touched at `ef19141`), **does** contain
`class TestDrawTierRouting` at `:553`, and **does** contain exactly **53** test functions — matching
the entry's claimed count. **The tests for the feature landed. The feature did not.**

**That is the direct cause of E-UTCI-12** (OPEN-13): the committed test file imports
`imputation._draw_tier` at `:645`, which has never existed, so `pytest` aborts at **collection** and
the suite has not been runnable as a whole since. **Two register items, one root cause, discovered by
two executors working from different directions who never spoke.**

**Why this is its own item and not folded into OPEN-17.** OPEN-17 asks whether to promote a tier.
This item is that **a completion record cannot be trusted against the repository** — and that record
is the same kind of document this arc uses to decide what is done. It is the fourth instance of the
project's recurring pattern (OPEN-30, OPEN-31, OPEN-33), and the most serious: those are steps nobody
owned, **this is a step recorded as taken.**

**What is NOT known, and must be measured before any plan:**
1. **Whether T07 is unique.** Every arc's progress log makes claims of this shape. **The measurement
   is mechanical and needs no CPU:** for each completed-task entry that names a code artifact, check
   the artifact exists at HEAD. **Nobody has ever done this, and until it is done the reliability of
   every closure record in the project is unmeasured.**
2. Whether the T07 work ever existed outside git (a lost working tree) or was never written.
   **Distinguishing these changes nothing about the record's reliability** and may be unanswerable —
   note it, do not chase it.

**Amended 2026-08-06 (N13, `implemenation/PLAN_no-compute-queue-3.md`, director-audited by
re-derivation). ~~Whether T07 is unique~~ — measured. It is.**
Report: `extra/MEASUREMENT_open-36_completion-record-sweep.md`; artifact:
`openubem/outputs/comparisons/open36_completion_record_sweep.csv`.

**The full population, not a sample: 596 completed-task entries across 59 documents.** 444 name a
checkable artifact; 152 name none and are recorded as UNCHECKABLE rather than quietly dropped.
Verdicts: **PRESENT 424, MOVED 6, NEVER-COMMITTED 14, UNCHECKABLE 152** (424+6+14 = 444; +152 = 596,
both sums re-derived by the director).

**Of the 14, exactly one is a governance gap — T07, the case already known.** The director checked the
other 13 individually rather than accepting the classification: **twelve** are this arc's own
measurement CSVs under `openubem/outputs/comparisons/`, each confirmed **present on disk, untracked,
zero commits on any branch** — which is what the project's externally-handled-git convention produces,
not a hidden failure; **one** is `scripts/_build_test.py`, whose own Artifacts line reads *"(temp,
deleted after use)"* and whose Notes record the deletion.

**The control was re-run by the director, not read back:**
`git log --all -S"_draw_tier" -- openubem/semantic/imputation.py` returns **nothing on any branch**,
the symbol is **absent from the working-tree file**, and at HEAD it survives only in a `draw_methods.py`
docstring and in `tests/test_draw_methods.py`. **The tests for the wiring were committed; the wiring
never was.** PASS.

**The method deserves its own note, because it is the reason to believe the number.** A mechanical
symbol-to-file heuristic first flagged **49** NEVER-COMMITTED entries. Every one was re-checked by
hand with an unrestricted repo-wide `git log --all -S` / `git grep`; **35 were misattributions** — the
symbol exists at HEAD, in a different file than the heuristic guessed. Both the raw and corrected
verdicts are retained as columns, so the correction is itself auditable. **An unaudited run of the
same sweep would have reported 49 phantom completion records.**

**What this changes:** the item's scope is now **bounded**. The reliability of every closure record in
the project is no longer unmeasured, and **no second instance exists**. What remains open is the
disposition of T07 itself — point 2 above stays explicitly un-chased.
3. Whether any *number* the project has published depends on a claim of this shape. **Nothing so far
   suggests it does** — the adopted baseline's provenance was re-verified this arc — but that is an
   absence of evidence, not evidence of absence.

**Do not conflate with OPEN-33.** OPEN-33 is that archiving breaks *pointers to* evidence. This is
that a record *asserts* evidence which does not exist. **A working pointer to a false claim is worse
than a dead pointer to a true one.**

---

**Amended the same evening, once N07 landed: this is not one incident. It is a pattern, and it now
has three instances, all verified from the repository itself.**

| # | Instance | Evidence |
|---|---|---|
| 1 | **T07's implementation was never committed; its tests were.** | `git log --all -S` → no commit; `tests/test_draw_methods.py` clean at `ef19141` with all 53 tests |
| 2 | **A one-line fix to `v12_cell_pipeline.py:520` was applied to the working tree mid-run** and recorded only in a progress log, not isolated as a commit until later. | `PLAN_archetype_threshold_fix_E-R3-3.md:482`, T11 entry 2026-07-01 — **director-verified** |
| 3 | **`05_results.gpkg`'s `archetype_id` cannot be reproduced by any code state in this repository** (OPEN-06 / N07). | write path re-executed against frozen inputs → Hotel every time; the committed file holds Office |

**The common statement, and it is larger than any one item: the project's git history does not
reliably capture what actually ran.** Instance 2 is the *mechanism* — a working-tree edit that
executes, is described in prose, and never becomes a commit. Instance 1 is that mechanism leaving half
a feature behind. Instance 3 is a **published artifact** that no commit can account for.

**This reframes the item's first measurement.** Checking completion records against HEAD is still the
cheap first pass — but it will not catch instance 2, because the record is *honest* and the commit is
simply absent. **The stronger check is the reverse: for each load-bearing committed artifact, ask
whether current code can regenerate it.** N07 did exactly that for one column of one file and found it
could not. **No other column of any published file has ever been checked this way**, and doing so
costs no CPU.

**What this does NOT mean.** No published *number* has been shown wrong by any of the three. Instance
3 concerns a **label**, and OPEN-06/N08 established the simulation itself used the correct archetype.
**State this plainly whenever the item is summarised** — the pattern is about the reliability of the
record, not (so far) about the results.

### OPEN-37 — The harvest never fetches `.eio`, so simulated floor area cannot come home ✅
*Added 2026-08-09, found by the director while auditing R05's CP-R2 readout. Not what R05 was looking for.*

**The observation that started it.** R05's own fetch report reads `n_end`, `n_sql`, `n_err` at full
count (149/149 and 198/198 across all ten probe fleets) and **`n_eio = 0` in every single row.** The
natural reading is that the `.eio` retention fix failed. **It did not — the opposite is true, and the
distinction is the whole item.**

**Both halves verified separately, at the source and on the hardware:**

| Question | Verified state |
|---|---|
| Does the cluster still hold the `.eio` after a run? | **Yes — 100%.** Director checked read-only over `ssh`: `149/149` and `198/198` non-empty, **zero empty**, across four arrays including both `fast_zone`s and the `la_rural/auto` array that contains 7 FAILED tasks. |
| Does the sbatch cleanup delete it? | **No.** `scripts/cluster/submit_fleet_t08.sbatch:63-80` deletes `.eso/.mtd/.rdd/.mdd/.htm/.tab/.csv/in.idf/expanded.idf/Energy+.idd/.dxf/.audit/.bnd/.dbg/.sln/.rvaudit/eplusmtr.*`; `eplusout.eio` is **not in the list**, and `:81` states so in a comment. |
| Does the fetch ask for it? | **No.** `scripts/cluster/t08_harvest_results.py:131` tars `*/eplusout.sql */eplusout.err */eplusout.end` — **`*/eplusout.eio` is absent from that list.** |

**So the file is produced, survives the cleanup, sits on `/speed-scratch` — and the tar that brings
results home never names it.** `n_eio = 0` is not a retention failure; it is the fetch reporting,
accurately, that it retrieved a file it never requested.

**Why this is its own item rather than a line in R05's log.** The `.eio` is the *only* record of the
floor area EnergyPlus actually simulated, as opposed to the floor area the pipeline declared. That
comparison is the check that would independently catch **OPEN-35** (2,611 buildings whose archetype
was chosen at group-median storeys and whose geometry was built at one storey) at the simulation
boundary rather than at the input boundary. **A fleet can be fully harvested, fully analysed and fully
published without the file, and nothing in the reported numbers will look wrong.**

**Its scope is every fleet ever fetched, not just E02.** No harvested fleet in this project has the
`.eio` locally, because no version of this fetch has ever asked for it.

---

#### ✅ FIXED 2026-08-10 — task R09, manager-verified. Fixed **before** E02's first harvest, as required.

`*/eplusout.eio` added to the remote tar list in **five** files — `t08_harvest_results.py:131`,
`t17_harvest_layout_assign.py:146`, `t18:142`, `t19:150`, `t20:150`. One line each;
`git diff --stat` = 5 files, 5 insertions, 5 deletions, nothing else touched.

**Three-count test on `r05probe_la_rural_auto`, all three re-derived rather than read back:**
**149 on the cluster = 149 inside the tar = 149 extracted locally**, sample
`way_222366800/eplusout.eio` = **21,190 B**. The old behaviour was demonstrated *first* and yields
**0** local `.eio` — so the before/after differs, per this register's own evidence rule.

🟠 **What the fix does NOT cover, recorded so it is not mistaken for complete.**
Five further sites build their file list from a variable and carry **the same gap**:
`t07_harvest_results.py:105`, `v11_nyc_centre_pipeline.py:289`, `v12_cell_pipeline.py:357`,
`v12_nyc_urban_recovery.py:93` and `:198`. They were inspected and deliberately left alone — out of
R09's scope, and none is on E02's path. `t26_harvest_utci_cluster.py:94` is **not applicable**: it
fetches UTCI rasters, not per-building EnergyPlus output.

🔴 **The fix corrects the future, not the past.** Every fleet harvested before 2026-08-10 still has no
local `.eio`, and no harvest was re-run. Any past claim about simulated floor area remains
un-derivable from local artifacts.

**Cost to fix is one filename in one tar list, and it is not urgent in the way it looks.** The files
persist on `/speed-scratch`; a corrected fetch retrieves them from any completed fleet after the fact.
**This does not block a submission — it blocks a harvest**, and must be fixed before E02's 40,800 runs
are fetched or that pass's simulated-floor-area record is lost at the moment of retrieval.

**The transferable lesson, and it is why this sits next to OPEN-36.** R05 reported `n_eio = 0` in a
column of an otherwise-passing report. Read as a summary, it looks like a failed fix. Read at the
source line, it is a *missing request*. **A count of zero says nothing about the thing being counted
until you check whether anyone asked for it** — the same shape as [[OPEN-36]], where a completion
record was honest about work that was never committed.

---

#### ✅ CLOSED 2026-08-18 — T03 of `implemenation/PLAN_five-items-2026-08-18.md`. All ten fetch sites now request `.eio`; local census finds zero gaps.

The five sites R09 left out of scope are now fixed — one line each, anchored on the exact string
`{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end` rather than on the register's stale line
numbers: `scripts/cluster/t07_harvest_results.py:102`, `scripts/validation/v11_nyc_centre_pipeline.py:290`,
`scripts/validation/v12_cell_pipeline.py:354`, `scripts/validation/v12_nyc_urban_recovery.py:94` and
`:199`. `git diff --stat` = exactly 5 insertions / 5 deletions across 4 files; `ast.parse` passed on
all four (static check only — no cluster, these scripts cannot be executed here). The five R09 sites
were re-verified untouched.

**Local census (`scripts/analysis/open37_eio_census.py` →
`openubem/outputs/comparisons/open37_eio_census.csv`), read-only over the E02 harvest at
`%LOCALAPPDATA%\Temp\ubem_e02_harvest\`:** **60 (cell, mode) directories** (3 cities × 4 sub-cells ×
5 modes, as expected), **40,800 `n_building_dirs`** (matching the expected fleet total exactly),
**40,800 `.eio` files with 0 empty**, **40,800 `.err`**. `.sql` (39,926) and `.end` (39,925) fall
short of 40,800 by 874/875 — reported, not reconciled away, and **not counted as part of this item**:
every one of those short directories still carries its `.eio` and `.err`, so this is an
incomplete-simulation signature, not an `.eio`-fetch gap. Registered separately as **OPEN-53** (§10),
concentrated in `austin_suburban_fast_zone`/`austin_suburban_floor` (874 of 875) plus one
`nyc_centre_fast_zone` directory.

**Closure: all ten fetch sites now request `.eio`; the local corpus census finds zero `.eio` gaps and
zero empty `.eio` files. OPEN-37 CLOSES.** The historical caveat (fleets harvested before 2026-08-10
have no local `.eio` and cannot be retroactively fixed without a re-fetch) is recorded as a permanent
disposition, not a blocker.

**Evidence:** `extra/MEASUREMENT_open-37_eio-fetch-closure.md`.

### OPEN-38 — `layout_assign` prototype defects — 🔴 **PREMISE FALSIFIED AND ITEM REWRITTEN 2026-08-11; still open**

> **Rewritten 2026-08-11 (T02 of `PLAN_e02-audit-and-closure.md`, plus director re-derivation). The
> original text below is kept in full, struck where it is wrong, per the append-and-amend rule.**
>
> 🔴 **What this item said, and why it is false.** It described 7 tasks that *"die on EnergyPlus
> **severe** `Base surface does not surround subsurface`, escalating to a two-space fatal."* Read
> directly from the raw `.err` files, **that message is a `** Warning **`, not a Severe** — at **all 8
> sites where it occurs**, in both the terminated and the surviving buildings
> (`nyc_rural_layout_assign/way_965718401/eplusout.err:608,611,614`;
> `way_965718400/eplusout.err:68,71,…`). **It does not escalate and it kills nothing.** The item was
> built on a co-occurrence read as a cause.
>
> **Defect (i) — what actually kills all seven.** `way_965718400/eplusout.err:52-55` carries the whole
> chain: `** Severe ** CalcHeatBalanceInsideSurf: The temperature of -12459.96 C for
> zone="LAUNDRYROOMFLR1"` → `**  Fatal  ** Program terminates due to preceding condition.` →
> `..... Reference severe error count=1`. **All seven `layout_assign` fatals are thermal runaway in the
> zone `LAUNDRYROOMFLR1`** — the substituted prototype's laundry room, the **same zone token as
> OPEN-06's `SmallHotel` provenance defect** — at −12,459 / −23,743 / −11,950 / −15,491 / −12,901 /
> −59,865 / **+182,399 °C**. **Zero of the other 37 fatals touch that zone. Zero `layout_assign` fatals
> have any other cause.** One prototype zone accounts for the mode's entire failure set.
>
> **Defect (ii) — the geometry defect is real, smaller than claimed as a killer, and worse as a
> publisher.** Scanned across **all 40,800** `.err` files: **8** buildings carry the malformed-door
> message, **all in `layout_assign`, zero in the other four modes**. Seven terminated for the unrelated
> reason above. The eighth, `nyc_rural/layout_assign/way_965718401`, ends *"EnergyPlus Completed
> Successfully — 58101662 Warning; 0 Severe Errors"* and **publishes results from geometry with three
> doors that do not fit their walls.** A defect that kills is visible; a defect that completes is not.
>
> **First measurement: made.** **What is still not known:** whether the `LAUNDRYROOMFLR1` instability
> is a prototype-library defect or an interaction with substituted geometry; and whether unfitted
> subsurfaces occur below the warning threshold in buildings that never emit the message.
>
> **Evidence:** `openubem/outputs/comparisons/open38_subsurface_census.csv`,
> `open41_failure_causes.csv`, `extra/MEASUREMENT_open-41-38_failure-causes.md`; director hand-read of
> the four `.err` files named above.
>
> ⚠️ **Method note worth carrying.** This is the second item in this register whose stated *cause* was a
> co-occurring message rather than the one that fired (OPEN-22's premise was the first). **A severity
> marker is evidence; a message's presence near a fatal is not.**

~~### OPEN-38 — `layout_assign` subsurface geometry defect ❓~~
*Added 2026-08-10, found by the manager's read-only E02 completion census. Not what the census was looking for.*

**What the census found.** Seven `layout_assign` tasks failed across three different cells —
`nyc_rural`=3, `la_centre`=1, `la_urban`=3 — out of the 45 total E02 failures. The sampled `.err`
files all carry the same EnergyPlus severe: *"Base surface does not surround subsurface"*, escalating
to a two-space `**  Fatal  **`. **Mode-specific and reproducible** — the eight arrays submitted twice
(OPEN-40) include several `layout_assign` arrays, and the same buildings failed both times.

**Why this is not folded into OPEN-01/OPEN-03.** Those two items are about `layout_assign` mutating
the *wrong* prototype storey count for buildings it still successfully simulates. This item is about
buildings `layout_assign` **cannot simulate at all** — a geometry-construction failure at the
subsurface/base-surface boundary, upstream of the storey-count question. `layout_assign` is already
the mode both open items scope, and it is the mode adopted for zone/HVAC-topology studies (not
certified for fleet EUI) — a third independent defect in the same mode raises the question of whether
it is fit for that purpose at all, which no single item currently answers.

**What is only believed, not yet measured:** that the sample generalizes to all 7, and that the
failing buildings share a specific geometry condition (e.g. a subsurface overhang, a degenerate wall
loop) the surviving `layout_assign` buildings do not.

**First measurement:** count every `layout_assign` building carrying this message fleet-wide from the
harvested `.err` files — grep the **two-space** form `"**  Fatal  **"` (the one-space form is the known
E-LA-21 defect, OPEN-29/OPEN-05, and misses real fatals) — and check whether the failing buildings
share a geometry condition the surviving ones do not.

### ~~OPEN-39~~ — `set -e` suppresses the trim step and the `task.rc` write on every failed cluster task — 🟢 **CLOSED 2026-08-11**

> **CLOSED 2026-08-11 (T05 of `PLAN_e02-audit-and-closure.md`, read-only cluster access). ID retired.**
>
> **The existence control fired exactly as the item describes.** Same array, `e02_la_centre_auto`:
> the failed task `way_319507579` is **42 MB, untrimmed, with no `task.rc`**; its successful sibling
> `relation_12292681` is **340 KB, trimmed, with `task.rc` present.** Both differences confirmed
> together, which is what the control was for — the "if both have a `task.rc`, the mechanism does not
> fire as described" trap did **not** fire.
>
> **Size:** the 45 known E02 failures orphan **≈2.14 GB** (2,239,488 KB), mean **48.6 MB**/dir, against
> **449 KB**/dir over an 11-directory successful sample — a **≈111×** ratio.
> **Not E02-specific:** sampling one fleet per non-E02 tag family (19 fleets, 3 directories each)
> reproduced the signature in `t17_austin_centre_layout_assign/relation_13781131` (6.5 MB, `task.rc`
> absent, against 236–492 KB with `task.rc` present for its siblings) — independent confirmation of the
> item's claim that the byte-identical T08→T20 template carries this everywhere.
>
> **The second half of the item — "no completion test may depend on `task.rc`" — is measured, not
> assumed.** All **15** `task.rc` references across **9** files under `scripts/` were read: **zero** use
> its presence as a completion test. Every completion check in this codebase keys on `eplusout.end`
> content instead. **The standing rule is therefore preventive, not corrective, in the code as it
> stands today — and it survives this closure unchanged.**
>
> **Evidence:** `scripts/analysis/e02_cluster_readonly_audit.py`,
> `extra/MEASUREMENT_open-39-40_cluster-records.md`. Cluster contact was read-only throughout
> (`ls`, `du`, `find`, `sacct`), all of it through `_ssh()`; total remote wall-clock **13.8 s**.
>
> ⚠️ **What this closure does NOT do.** It does not reclaim the 2.14 GB and it does not add a guard to
> `submit_fleet_t08.sbatch:56`. **The `set -e` line is still unguarded.** Closing this item records
> that the defect is sized and that nothing depends on the missing file — remediation was forbidden
> inside the measuring task and remains unscheduled.


*Added 2026-08-10, found by the manager's read-only E02 completion census while reasoning about the
45 failed tasks' on-disk footprint. Not what the census was looking for.*

**Verified directly against `scripts/cluster/submit_fleet_t08.sbatch` (read 2026-08-10):**

| Line | Content |
|---|---|
| `18` | `set -e` |
| `56` | `"${EP_DIR}/energyplus" -w "$EPW" -d "$OUTDIR" "$RUN_IDF"` |
| `57`–`58` | `RC=$?` then `echo $RC > "${OUTDIR}/task.rc"` |
| `63`–`80` | the trim block — deletes `.eso/.mtd/.rdd/.mdd/.htm/.tab/.csv/in.idf/expanded.idf/Energy+.idd/.dxf/.audit/.bnd/.dbg/.sln/.rvaudit/eplusmtr.*` |

**The mechanism.** Line 18's `set -e` makes the whole script exit immediately on the first non-zero
exit status. Line 56 runs EnergyPlus with no `if`/`||` guard around it — so when EnergyPlus itself
exits non-zero, the script terminates **at line 56**, and lines 57–58 (`RC=$?`, the `task.rc` write)
and the entire trim block (63–80) **never execute**. Every failed task therefore leaves an untrimmed
directory: `in.idf`, `expanded.idf`, `Energy+.idd` (~40 MB combined per the trim-block comment's own
budget reasoning), plus zero-byte or partial `.eso`/`.mtd` and whatever EnergyPlus wrote before dying.

**Two consequences to state separately:**
1. **Orphaned disk on `/speed-scratch`.** Every failed task across every fleet this template has run
   (T08 through T20 — the header comment at line 9 calls this "the T08 variant"; the template is
   carried forward unchanged, per OPEN-29's finding that E-LA-21 is replicated the same way across
   scripts) leaves its full untrimmed output on disk.
2. 🔴 **A failed task has no `task.rc`.** Its absence is the *expected* signature of `set -e` firing on
   a non-zero EnergyPlus exit, not evidence of an incomplete or hung task. **`task.rc`'s presence must
   never be used as a completion test** — the same shape as OPEN-29's standing rule for `has_fatal`
   ("never use the `has_fatal` column"). Any harvest or resume logic that checks for `task.rc` before
   treating a task as "done" would misclassify every failure this way.

**Not yet measured, and not measured here:** the total orphaned bytes across all fleets on
`/speed-scratch`, and whether any completion/harvest/resume script in this project actually keys on
`task.rc`.

**First measurement:** size the orphaned disk across all fleets on `/speed-scratch`, and grep the
project's harvest/resume scripts to confirm none depends on `task.rc` for a completion decision.

### ~~OPEN-40~~ — Eight job arrays were submitted a third time by an unrecorded process — 🟢 **CLOSED 2026-08-11 as untraceable**

> **CLOSED 2026-08-11 (T05 of `PLAN_e02-audit-and-closure.md`). ID retired.**
> **This item's own text names the disposition:** *"If untraceable, that is the finding and the fix is a
> submission log nobody can bypass."* It is untraceable. That is the finding.
>
> **The range control was re-run from scratch rather than taken from any document.** An independent
> reconstruction of **all 68** `e02_*` array submissions in the 2026-08-09/10 window straight from
> `sacct` gives **19 (wave 1) + 8 (orphan) + 41 (wave 2) = 68**, exact — confirming the eight IDs
> `1177095`, `1177838`–`1177841`, `1177875`, `1178313`, `1178538` fall outside both documented waves.
>
> **What was checked and found silent:** submission timestamps run 2026-08-09T23:08:58 →
> 2026-08-10T00:04:49; `JobName`, `WorkDir` and `User` are **identical in form across all three waves**
> (same `--job-name=e02_{cell}_{mode}` convention, same login-home `WorkDir`, one user) and carry no
> discriminating signal; no local artifact references any of the eight IDs (`e02_fleet_submit.py`,
> `e02_submit_remainder.sh`, `e02_remainder_jobids.txt`, both `e02_generation_summary__*.json`, both
> `e02_run*.log`); the remote `.bash_history` has an mtime of **2026-04-27**, predating the entire
> window, and contains zero `e02` references — **silent for all three waves alike, so its silence is
> not evidence about the orphan wave specifically.** That distinction is the reason this closes as
> *untraceable* rather than as *attributed*.
> **Cross-check:** all eight orphan `(cell, mode)` pairs reappear in wave 2's own job list, confirming
> wave 2's accounting did not know the orphan submission had happened.
>
> 🔴 **No story was reconstructed from timestamps**, per the instruction in the measuring task.
>
> 🟢 **The accident remains the best evidence in the arc** and that does not change: both runs of all
> eight arrays produced identical task and failure counts with the same buildings failing, which is why
> the 45 failures are known to be deterministic and why nothing is ever to be resubmitted.
>
> **Evidence:** `extra/MEASUREMENT_open-39-40_cluster-records.md`.
> ⚠️ **The remedy is unbuilt.** A submission log nobody can bypass does not exist; closing this item
> records that the submitter cannot be recovered, not that the gap is fixed.


*Added 2026-08-10, found by the manager's read-only E02 completion census while reconciling job IDs
against the two documented submission waves. Not what the census was looking for.*

**The observation.** Job IDs `1177095`, `1177838`–`1177841`, `1177875`, `1178313`, `1178538` fall
outside **both** documented submission ranges — wave 1, `1176411`–`1176599` (§0, "19 arrays / 19,931
tasks queued at submission"), and wave 2, `1198104`–`1200571`. **No project document or scratchpad
log explains them.** Affected arrays: `la_centre/layout_assign`, `la_rural/auto`, `la_rural/building`,
`la_rural/floor`, `la_rural/layout_assign`, `la_rural/fast_zone`, `austin_urban/fast_zone`,
`austin_rural/auto`.

**This is the records defect this arc keeps uncovering, in a new place.** OPEN-36 found a completion
record describing code no commit ever contained; OPEN-29 found defects open at their own defining
line but absent from this register; both are gaps between what happened and what was written down.
This is the same gap on the cluster's own submission history.

**The silver lining, stated explicitly so it is not lost under the records-defect framing.** These
duplicate submissions are exactly what proved the pipeline **deterministic** (§0, 2026-08-10 amendment,
and OPEN-38's own evidence): both runs of all eight arrays produced identical task counts and identical
failure counts, the same buildings failing both times. An accidental re-submission became a free
reproducibility control.

**First measurement:** trace the submitter — check shell history, scratchpad submit scripts
(`e02_submit_remainder.sh` and siblings), and `sacct -j` submission timestamps for the eight IDs
against every known driver invocation. **If it cannot be traced, that is itself the finding**, and the
remedy is a submission log nobody can bypass — not a retroactive reconstruction.

### ~~OPEN-41~~ — 43 of the 45 fleet failures have no recorded cause — 🟢 **CLOSED 2026-08-11**

> **CLOSED 2026-08-11 (T02 of `PLAN_e02-audit-and-closure.md`). ID retired.**
>
> **All 44 fatals now carry a recorded cause**, captured from the `** Severe **` line preceding each
> fatal rather than EnergyPlus's trailer. Groups: **25** *Temperature (low) out of bounds*, **17**
> `CalcHeatBalanceInsideSurf`, **1** *Temperature (high) out of bounds*, **1**
> `CheckForRunawayPlantTemps`. 🔴 **Every one of the 44 is a numerical thermal blow-up. None is a
> syntax, missing-object, licensing or resource failure** — which is itself the most useful thing the
> census says, because it rules out a whole class of remedy.
> The 45th, `nyc_centre/fast_zone/way_1240348353`, is re-confirmed to contain **no `Fatal` string at
> all**, consistent with the `std::bad_alloc` account.
>
> 🔴 **The concentration is explained, and this register's own framing of it was wrong.** It recorded
> *"failures concentrating in one small rural cell across unrelated zoning modes points at the inputs
> for those buildings"* and marked it *"a hypothesis, not a measurement."* The hypothesis is half
> right: it is the inputs, but **the unit is the archetype, not the cell.**
>
> | | buildings | tasks (×5 modes) | fatals | rate |
> |---|---|---|---|---|
> | **`Warehouse`** | **38** (0.47% of fleet) | 190 | **26** | **13.68%** |
> | everything else | 8,122 | 40,610 | 18 | **0.0443%** |
>
> **Relative risk ≈ 309×.** All **11** `la_rural` failing buildings are `Warehouse` carrying
> `no_floors`; the cell holds 25 Warehouses of 149 and is simply Warehouse-dense. **36 of the 44
> failures carry `no_floors`; 37 of the 38 Warehouses do.** The cross-mode intersection T02 was asked
> for came back **split**: 6 of the 11 fail in all three modes (a per-building input signature), 5 are
> mode-specific.
>
> **Director re-derivation:** the two-space fatal counts for `la_rural_auto` (**7**) and
> `la_rural_fast_zone` (**10**) were re-grepped independently, the 6-building intersection re-derived
> before reading the executor's CSV, the archetype join recomputed, and
> `nyc_centre_auto/way_266149332/eplusout.err:408` hand-read to confirm the backwards scan captures the
> mechanism (90,915.77 °C) rather than the `..... Last severe error=` trailer three lines below.
> **Evidence:** `openubem/outputs/comparisons/open41_failure_causes.csv`,
> `extra/MEASUREMENT_open-41-38_failure-causes.md`.
>
> 🔴 **This item closes on the census, which was its question. The remedy question it exposed —
> what to do about a `Warehouse` population that fails at 309× the fleet rate — is OPEN-42.**
> Closing this item does not fix a single failing building.


*Added 2026-08-10, found by the manager while auditing R10's failure census — the census answered "which
buildings" completely and "why" almost not at all. Not what the census was looking for.*

**The observation.** R10's harvest of all 60 arrays reconciled the failure set **exactly**: 44 fatal
buildings (two-space `"**  Fatal  **"` test, E-LA-21) + 1 building with no `.end`
(`nyc_centre/fast_zone`, the `std::bad_alloc` 89-storey case) = **45**, versus **45** unique `sacct`
FAILED tasks, with **direction A = 0** (no local failure absent from `sacct`) and **direction B = 0**
(no `sacct` failure absent locally), all 45 mapped to a building stem via `fleet.lst`. Completeness is
not the problem. **The message census is:**

| fatal message | count |
|---|---|
| `Program terminates due to preceding condition.` | 43 |
| `CheckForRunawayPlantTemps: Simulation terminated because of run away plant temperatures, too hot` | 1 |

`Program terminates due to preceding condition.` is EnergyPlus's **generic trailer**. It names no cause.
The diagnostic content lives in the **preceding** `** Severe **` line, which the scanner never captured.
So for 43 of 44 fatals we know the building, the cell and the mode, and nothing about the failure.

**Why this is a defect and not just a missing nicety.** This is the same shape as E-LA-21 itself: a fatal
test that returns something plausible while carrying no information. A census that reports "43 ×
*preceding condition*" reads like a finding and is in fact a null result — and a null result that looks
like a finding is exactly what this arc keeps being caught by (OPEN-36, OPEN-29, and R10's own
all-zeros analysis run against an empty root).

**Second observation, unexplained, recorded so it is not lost.** The 45 failures are **not uniformly
distributed**: `la_rural` carries **24 of 45** across three separate modes (`fast_zone` 10, `auto` 7,
`floor` 7) despite being one of the smallest cells at 149 buildings/mode — roughly a 4.7% failure rate
in that cell against **0.11%** fleet-wide (45/40,800). `nyc_centre/fast_zone` carries 8 more. Failures
concentrating in one small rural cell across unrelated zoning modes points at the **inputs for those
buildings**, not at the mode implementations. That is a hypothesis, not a measurement.

**First measurement:** re-scan the 44 `.err` files in the harvested corpus
(`…\Temp\ubem_e02_harvest`, on disk, no cluster access needed) capturing the **`** Severe **` lines
preceding each fatal**, not the trailer; group the distinct causes; then intersect the `la_rural`
subset's building IDs across the three affected modes to test whether the **same buildings** fail in all
three. If they do, the cause is per-building input data and this becomes an input-validation item; if
they do not, it is mode-specific and splits. **Do not write a remedy plan before this scan** — the
current evidence names no cause to remedy.

### OPEN-42 — The `Warehouse` population is broken in two measured ways, and one of them reaches the adopted baseline 🔴 **OPENED 2026-08-11**

**Opened 2026-08-11** by the E02 audit and closure pass — found by *auditing* T02's and T04's output
against the adopted fixture, not by running a task, which is now the ninth item in this register found
that way.

**Face (i) — `Warehouse` buildings fail EnergyPlus at ≈309× the fleet rate.**

| | buildings | tasks (×5 modes) | fatals | rate |
|---|---|---|---|---|
| **`Warehouse`** | **38** (0.47% of the fleet) | 190 | **26** | **13.68%** |
| everything else | 8,122 | 40,610 | 18 | **0.0443%** |

26 of the **44** fleet fatals are Warehouses. **13 distinct** Warehouse buildings fail in at least one
mode. Failures split `auto` 8 / `floor` 8 / `fast_zone` 10 and — notably — **zero in `layout_assign`**,
whose seven failures are the separate `LAUNDRYROOMFLR1` mechanism under OPEN-38. **36 of the 44 fleet
failures carry `no_floors`, and 37 of the 38 Warehouses do.** All **11** `la_rural` failing buildings
are Warehouses with `no_floors`; that cell looked anomalous only because it is Warehouse-dense (25 of
149).

**Face (ii) — six buildings carry a placeholder `footprint_area_m2` of exactly 200.0 m².**
Fleet-wide there are exactly six such rows, all `Warehouse`, all flagged `no_floors`:
`la_rural` `way_472960972`, `way_472961034`, `way_472961088`, `way_472961091`, `way_472961171`, and
`la_urban` `way_402215469`. Their simulated areas run **4,064–67,330 m²**. 🔴 **The adopted `auto`
mode therefore divides by a denominator wrong by 20.3× to 336.7× on six real, published buildings** —
a data-quality defect in the declared input, **independent of the storey-matching mechanism** OPEN-01
and OPEN-35 are about. A widened scan found 16 Warehouses at ≤210 m² fleet-wide; six sit at the
literal placeholder value.

**Why one item and not two.** The two faces overlap on five buildings but neither contains the other
(the sixth placeholder building never failed; seven failing Warehouses have no placeholder). They share
one population, one flag (`no_floors`) and one plausible upstream cause, so they are tracked together
with **one closure condition: the `Warehouse` + missing-storey-count input path is understood and
fixed.** If the first measurement below splits them, split the item then — not now, on a guess.

**First measurement: made — this section is it.**

**What is NOT known, and must be measured before any execution plan is written:**
1. **Where the 200.0 m² comes from** — a constant in the source data, or injected by an imputation
   path. Nobody has traced it.
2. **Whether the two faces share a cause** or merely a population.
3. **Whether the thermal instability is the placeholder geometry** (a 200 m² footprint declared
   against a 67,330 m² simulated envelope is a strong candidate) **or a property of the `Warehouse`
   archetype itself** — the seven failing Warehouses without a placeholder argue it is not only the
   placeholder.
4. **What the six buildings do to the adopted 158.0 kWh/m² fleet figure.** Six of 8,160 with
   denominators wrong by up to 336× is a small count and a large per-building error; **the effect on
   the fleet number is unmeasured and must not be assumed negligible.**

**Blast radius:** 38 buildings, **6 of them inside the adopted `auto` fleet EUI**.
**Evidence:** `openubem/outputs/comparisons/open41_failure_causes.csv`,
`open01_denominator_audit.csv`, `e02_simulated_floor_area.csv`,
`extra/MEASUREMENT_open-41-38_failure-causes.md`,
`extra/MEASUREMENT_open-01_denominator-audit-e02.md`.
Both faces were **re-derived independently by the director** — the archetype/failure join, the exact
six-row placeholder population, and the 309× rate — before this item was written.

**Evidence mark:** ~~✅ **both faces measured on all 40,800 runs**; ❓ **the source of the 200.0
placeholder is untraced.**~~ **Superseded 2026-08-12 — see below.**

---

#### 🔵 MEASURED 2026-08-12 — the placeholder is traced, and it does not touch the published number

Plan `implemenation/PLAN_five-item-sweep-2026-08-12.md` T01–T02. Every figure below was **re-derived
by the director from the raw artifacts**, not accepted from the executor's report.

**1. Unknown #1 is answered — the 200.0 is a declared fallback with a single writer, not imputed
data.** `scripts/validation/v12_cell_pipeline.py:659`, in `_build_enriched_gdf`, initialises
`footprint_area_m2 = 200.0` (alongside `num_floors = 1.0`, `height_m = 3.5`, centroid `0.0, 0.0`) and
overwrites it from the simulation SQL at line 664 **only** `if len(sim_row) > 0 and
sim_row.iloc[0]["status"] == "success"`. There is no `else` branch. All six buildings are `failed` in
`04_simulation_manifest.parquet`, so the initialiser survives untouched into `05_results.csv`. It is a
**crash-artefact of the reporting stage**, not a value that ever existed in the input data.

**Stage 1 is clean, which rules out the imputation hypothesis.** `results/phaseE/<cell>/01_buildings.gpkg`,
read in its own projected CRS (EPSG:32611), carries real polygon footprints, each stored attribute
matching its own `geometry.area`: 3 417.0 / 1 398.5 / 1 555.9 / 1 355.2 / 22 443.7 m² (`la_rural`),
1 173.4 m² (`la_urban`). The true areas were present all along and were discarded downstream.

**The placeholder set and the failure set are the same set.** Re-derived two independent ways over the
pooled 8 160-row fleet: `simulation_status != "success"` returns exactly six stems, and
`footprint_area_m2 == 200.0` fleet-wide returns exactly the same six and nothing else. Face (ii) is
therefore **a strict subset of face (i)** — it has no independent existence. It is not a data-quality
defect in the declared input at all; it is what face (i) looks like after the reporting stage.

**2. 🔴 Correction — the blast-radius claim above is wrong, and this section retracts it.** This item
was opened stating that *"the adopted `auto` mode divides by a denominator wrong by 20.3× to 336.7× on
six real, published buildings"* and that six sit *"inside the adopted `auto` fleet EUI"*. **They do
not.** All six carry `simulation_status = not_simulated` and `total_eui_kwh_m2 = NaN`; they are exactly
the six non-success rows of 8 160. The per-cell aggregation in `openubem/results/aggregator.py`
filters to success rows, so the six are absent from both the numerator and the denominator.
**Corrected blast radius: 6 published rows carry a false area; 0 of them are inside the fleet EUI.**

**Unknown #4 is answered — measured impact on 158.0 kWh/m² is exactly 0.000 (0.00 %).** Baseline
reproduced first, as required: pooling the twelve `results/phaseE_elevrb/<cell>/05_results.csv` gives
8 160 rows (8 154 success / 6 `not_simulated`); per cell `Σ(EUI × footprint × levels) / Σ(footprint ×
levels)` over success rows; the fleet headline is the mean of those twelve weighted by each cell's
total building count = **158.0298** against the adopted 158.03. Correcting a denominator for a
building that was never in the sum cannot move the sum. **OPEN-42 is a reporting defect, not a
baseline defect. The published 158.0 does not need restating.**

**Scope correction carried forward.** The *"simulated areas 4,064–67,330 m²"* quoted above come from
the separate 40,800-run E02 harvest, **not** from the adopted run. Pairing those areas with the
adopted baseline compares two different campaigns, and this item did so when it was opened.

**3. 🔴 New finding — the six failed with no recorded reason.** `error_summary` is the **empty string**
for all six manifest rows. OPEN-41 established a recorded cause for all 44 E02-harvest fatals; that
work does not extend to the adopted run, where these six failures remain unexplained. **This is now
the binding obstacle to closing OPEN-42** — the placeholder is explained, the failures are not.

**4. New item raised.** The aggregation-formula observation this task turned up is **OPEN-43**, below.

**Where this leaves the item.** Unknowns #1 and #4 are answered; #2 is answered in the narrow sense
that face (ii) is a subset of face (i), so **the two faces are one defect with one cause: the failure**;
#3 (is the thermal blow-up the placeholder geometry or the archetype) is **untouched and remains the
open question**, now joined by the empty `error_summary`. **OPEN-42 stays OPEN** — measurement-only
tasks were never going to close it, and this is recorded as expected progress, not a shortfall.

**Evidence:** `openubem/outputs/comparisons/open42_placeholder_trace.csv`,
`open42_fleet_eui_impact.csv`, `open42_t02_percell_repro.csv`;
`extra/MEASUREMENT_open-42_placeholder-and-fleet-impact.md`;
scripts `scripts/analysis/open42_t01_build_trace_csv.py`,
`open42_t02_reproduce_fleet_eui.py`, `open42_t02_fleet_eui_impact.py`.

**Evidence mark:** ✅ **placeholder traced to a single cited writer**; ✅ **fleet impact measured at
zero against a reproduced baseline**; ~~❓ **why the six simulations failed is unrecorded and
unknown.**~~ ✅ **ANSWERED 2026-08-13 — see the amendment immediately below.**

> **Amended 2026-08-13 (T01 of `PLAN_two-measurements-2026-08-13.md`, signed at CP-1). The blocking
> unknown is answered from the raw `.err` files, and the answer reframes the item.**
>
> 🔵 **All six failed for one cause: runaway zone temperatures.** Every one of the 16 failing
> (building × mode) runs terminates on `**  Fatal  ** Program terminates due to preceding condition.`
> preceded by a `** Severe  ** Temperature (low|high) out of bounds` on a *zone*, not on an input,
> a geometry parse, or a missing object. Range of the out-of-bounds values: **−444.53 °C to
> +530.25 °C**. Cause class is uniform across all 16 — **no second failure mode exists in this
> population.**
>
> **Director re-derivation, from the raw files and not from the report** (three rows chosen across
> two cells and two modes, all matched character-for-character at the cited offsets):
>
> | file | severe | fatal | value |
> |---|---|---|---|
> | `la_rural_auto/way_472960972/eplusout.err` | line 592 | line 594 | `Temperature (low) … [-444.53]`, zone `WAY/472960972_F2_CORE` |
> | `la_rural_fast_zone/way_472961091/eplusout.err` | line 100 | line 102 | `Temperature (high) … [530.25]`, zone `WAY/472961091_F2_PERIM6` |
> | `la_urban_auto/way_402215469/eplusout.err` | line 134 | line 136 | `Temperature (low) … [-256.14]`, zone `WAY/402215469_F3_WHOLE` |
>
> **Non-vacuity control, re-derived independently:** `la_centre_auto/way_319507579/eplusout.err:3831`
> is a *different* fatal class (`CheckForRunawayPlantTemps`) and the scanner reports it as such —
> the scan is not returning one answer for everything.
>
> 🔴 **The finding that matters more than the cause: these buildings are not intrinsically broken —
> the failure is zoning-dependent.** All six succeed under `building` (whole-building) mode and all
> five `la_rural` stems also succeed under `layout_assign`; `la_urban/way_402215469` succeeds in
> **four of five** modes and fails only in `auto`. Success confirmed from `eplusout.end`
> (`Completed Successfully`), never from the absence of a fatal. **So this is a zoning-method defect,
> not a bad-building defect, and unknown #3 (placeholder geometry vs archetype) is now sharpened:
> whatever destabilises these zones is introduced by the sub-building zoning step.**
>
> ⚠️ **What is still not known, and was not guessed:** *why* one zoning mode survives where another
> blows up. That is not answerable from the `.err` files — it needs the geometry/zoning code, which a
> measurement task was correctly forbidden to touch. **OPEN-42 stays OPEN on that question alone.**
>
> **Evidence:** `openubem/outputs/comparisons/open42_six_failure_causes.csv` (30 rows = 6 buildings ×
> 5 modes); report `extra/MEASUREMENT_open-42_six-failure-causes.md`; scanner
> `scripts/analysis/open42_failure_causes.py`.

---

> **Amended 2026-08-18 (T05 of `implemenation/PLAN_five-items-2026-08-18.md`). The `.eio` was read —
> nobody had. It sharpens the question further but does not answer it.**
>
> `scripts/analysis/open42_zone_geometry.py` parsed every `Zone Information` record in `eplusout.eio`
> for all 30 (building × mode) runs and joined the outcome. **Is the blow-up zone degenerate or
> ordinary? Ordinary, 15 of 16.** All 5 `la_rural` buildings fail on the **topmost floor's** zone in
> each of the 3 per-floor-zoned modes, and that zone's floor area/volume/ceiling-height/extents are
> **byte-identical** to its own non-fatal sibling zones one and two floors below in the same run
> (`way_472960972`'s `_F0_CORE`/`_F1_CORE`/`_F2_CORE` all report 2,221.44 m² / 7,775.03 m³ — only
> `_F2`, the top, fails). Only its position — topmost floor, roof-adjacent, no zone above — differs.
> The 1 exception (`la_urban/way_402215469/auto`) instead shows a uniform whole-run `Volume=10.00 m³`
> on every zone regardless of floor area.
>
> **Required background control (20 successful buildings, same cells and modes) disproved both
> candidate statistics before they could be reported as a mechanism.** The uniform-`Volume=10.00`
> signature looked decisive and was not: 12 of the 20 background buildings (60%) show the identical
> pattern in `auto` mode and all 12 succeed. A looser volume-consistency threshold and raw zone
> size/aspect-ratio statistics were also tried and also failed to separate the 16 failing from the 14
> succeeding runs (background rates ≈ target rates; most fatal zones sit inside the background's own
> size/aspect-ratio range).
>
> **Verdict: the positional pattern (topmost floor, 15/16) is real and evidenced, but `eplusout.eio`
> does not carry a field that explains why THESE six buildings' topmost zones are unstable while 20
> background buildings' topmost zones are not.** *"Not determinable from `eplusout.eio`"* for that
> deeper question — stated as the plan required, not dressed up as a mechanism. Connected (not
> re-derived) to **OPEN-11**: all six are the same six inverted-geometry buildings N04 already
> identified; a per-surface winding/orientation defect — invisible in `Zone Information`, which only
> ever reports zone-level aggregates — is named as the most likely next artifact to check, outside
> this task's `.eio`-only scope.
>
> **OPEN-42 sharpens further. Still OPEN — not determinable from this artifact; the next step needs a
> different one, not a re-read of this one.**
>
> **Evidence:** `openubem/outputs/comparisons/open42_zone_geometry.csv` (1,011 rows: 411 target zone
> rows across the 30 runs + 600 background zone rows across 100 runs, 20 background buildings); report
> `extra/MEASUREMENT_open-42_zoning-mechanism.md`; scanner `scripts/analysis/open42_zone_geometry.py`.

---

### OPEN-43 — The published fleet EUI is a mean of cell means, not a fleet mean ✅ **CLOSED 2026-08-12 — ID RETIRED 2026-08-13**

> ✅ **CLOSED by the user's ruling of 2026-08-12. Retired formally on 2026-08-13 under ruling `2h`** —
> the count had already been reduced by it while this section still read `OPENED`.
>
> 🔴 **The ruling, which is the single most-quoted fact in this arc: the published fleet EUI is the
> POOLED figure — `157.1 kWh/m²` = total simulated energy ÷ total simulated floor area over all 8,154
> successful buildings.** Restated in 13 live files; archived trees deliberately left unedited as
> record. **Do not re-ask which aggregation the headline uses, and never quote the headline without its
> definition** — a reader who hears "fleet average" will assume the pooled one, and for four months
> they would have been wrong.
>
> **What the measurement established, and it stands unchanged:** over the same 8,154 rows, count-weighted
> mean of cell means = **158.0298** (this was the published 158.0), success-weighted = 158.0557,
> unweighted = 160.0993, pooled = **157.0552**. **None of the four is arithmetically wrong; they answer
> different questions.** The count weights included the six buildings that produced no energy at all.
>
> ⚠️ **What this closure does NOT discharge — both belong to other items and both are still open:**
> **(1)** the published figure is one **HEAD cannot reproduce end to end** (**OPEN-48**); **(2)** the
> re-run's **`159.2157` is not a competing headline** — it is the same model run through **OPEN-49**'s
> `wwr` re-randomisation defect, and it survives only as evidence inside that item. 🔴 **`159.2157`
> must never be restated as a fleet figure in any document.**

**Opened 2026-08-12** by the director while auditing T02 — found by re-deriving the adopted headline
two ways instead of one. This is the tenth item in this register found by auditing rather than by
running a task.

**The measurement.** Over the same 8 154 success rows of the adopted `phaseE_elevrb` run:

| aggregation | fleet EUI |
|---|---|
| per-cell area-weighted mean, then averaged over the 12 cells **weighted by each cell's total building count** — *this is the published 158.0* | **158.0298** |
| the same twelve cell values, weighted by each cell's **success** count | 158.0557 |
| unweighted mean of the twelve cell values | 160.0993 |
| **pooled** — `Σ(EUI × area) / Σ(area)` over all 8 154 buildings at once | **157.0552** |

**Why it matters.** The published headline sits about **1.0 kWh/m² above** the pooled fleet figure,
entirely from the choice of aggregation and not from any building's energy. Neither number is wrong —
they answer different questions — but **the published figure has never been described as a mean of
cell means anywhere in this project**, and a reader of "fleet EUI = 158.0 kWh/m²" will reasonably
assume the pooled definition. A second, smaller oddity: the count-weights include the six buildings
that contributed no energy (using success counts instead moves the figure to 158.0557).

**First measurement: made — this section is it.** No execution plan may be written until the item is
decided, per the arc rule.

**What is NOT known:** whether the mean-of-cell-means was a deliberate choice (the twelve cells are a
designed sample, and equal-ish cell influence may be exactly what was intended) or an artefact of
per-cell reporting being written first. Nothing in `openubem/results/aggregator.py` decides the
**fleet** roll-up — the aggregator is per-cell only, so the fleet step lives outside it and its author
and intent are untraced.

**Decision owed by the user, not by the director:** which definition the published headline should
use. **Do not renumber or restate 158.0 before that ruling.**

**Blast radius:** every published fleet-level EUI figure in the project — the headline itself, and any
figure or board that quotes it.
**Evidence:** `openubem/outputs/comparisons/open42_t02_percell_repro.csv`; director's independent
re-derivation of all four aggregations from `results/phaseE_elevrb/<cell>/05_results.csv`.
**Evidence mark:** ✅ **all four aggregations computed on the full adopted run**; ❓ **intent untraced.**

---

### OPEN-09 — `thermal_mass=True` drives warmup non-convergence, and "cosmetic" was never tested (E-LA-23) ✅ **C06 2026-08-06: (b) tested — "cosmetic" holds, with a quantified nuance**
A matched control measured 96/150 (64%) engaged rows non-converging vs 8/150 (5.3%) in the control —
same buildings, same code, one variable. Two consequences were forwarded and never decided:
(a) a fixed fleet run at `thermal_mass=True` projects ≈299/8,160 ≈ 3.66% (**a projection, not a
measurement, still out of scope**); (b) the **"cosmetic" label has been inherited unexamined across
five log entries** (E-LA-14/16/18/19/23) and is a claim about *accuracy* that nobody had ever tested.

**(b) is now measured.** `PLAN_compute-queue.md` C06 re-derived, from raw `.err`/`eplustbl.htm` text
on the same 150-building F11-N/F11-N-b population (no new simulation — runs already existed on
disk), the per-building EUI delta (`thermal_mass=True` vs `False`) split by warmup-convergence
status of the True-arm run. **No alarming failure mode**: every one of the 150 deltas is negative,
the converged/non-converged distributions overlap 96.3%, and the non-converged group's mean delta
is *smaller* in magnitude (−1.638%) than the converged group's (−1.855%), not larger. The
difference is statistically real (Mann-Whitney p=4.1×10⁻⁷, Cohen's d=0.89) but small in absolute
terms (≈0.22 pp ≈ 0.20 kWh/m² at the population's median EUI). **Verdict: "cosmetic" is earned at
the one population it has been tested on** (`nyc_rural`/`SmallOffice`/`u_roof=0.119`); the five
inherited log entries do not need correcting on substance, only on epistemic status (inherited →
tested). Full write-up: `extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md`. **(a) remains a
projection, unmeasured, out of scope.**

**Audited 2026-08-06 (manager, independent re-derivation) — GREENLIT.** The manager re-walked all
300 raw run directories with its own scanner: 96/150 and 8/150 reproduce exactly from `.err` text,
all 150 deltas negative, group means −1.6375 / −1.8550, overlap 52/54 = 96.3%, Cohen's d 0.893, and
**no file under either `runs/` tree has been written since 2026-07-25** — confirming zero simulations
were run. One summary-table figure corrected: the "97%" reverse overlap was not reproducible (actual
95.8%); the cited 96.3% is correct. Audit entry: `implemenation/PLAN_compute-queue.md` §8.

> **Amended 2026-08-18 (OPEN-51's adjudication, T02 of `implemenation/PLAN_five-items-2026-08-18.md`).
> The "five inherited log entries" narrows to four.** OPEN-51 decided, on quoted evidence, that
> `E-LA-16` names the cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family, not the
> `CheckWarmupConvergence` class C06 tested. **The inherited-label list above is corrected to
> E-LA-14/18/19/23 — four entries, not five.** E-LA-16 was never covered by C06's population or its
> "cosmetic" finding, and its own accuracy impact remains untested. This does not change C06's
> substance for the four entries it does cover.

### OPEN-10 — Editing the `ZoneGroup`'s own list multiplier would restore exact expressibility (E-LA-37) ✅ **checked at last — the capability is real, and narrower than claimed**
A different mechanism from the one built (which writes `Zone.Multiplier`). Would restore exact storey
matching at every `n_real` rather than only `{10, 18, 26, …}` / even `n_real ≥ 4`. ~~**Never tested** —
this is a believed capability, not a measured one.~~ R04 is closed at option (a), so opening this is a
deliberate reopening, not a continuation.

**Amended 2026-08-06 (N11). This was the register's only ❓, and it is now removed by reading a file.**
Report: `extra/MEASUREMENT_open-10_zonegroup-capability.md`.

**Verdict: yes — the schema permits it.** `ZoneGroup`'s `Zone List Multiplier` (`Energy+.idd:10002-10018`)
is `\type integer \default 1 \minimum 1` — **no maximum and no divisibility constraint**, the identical
shape to `Zone.Multiplier` (`:9576-9579`). The believed capability was real. Writing that field
**directly**, instead of layering a residual `Zone.Multiplier` on top of the prototype's baked-in
value, expresses **every `n_real ≥ 3` exactly** for the two archetypes concerned — against the shipped
mechanism's `{10, 18, 26, …}` / even `n_real ≥ 4`.

**Two limits the item never stated, and both matter to any plan:**
1. **`n_real` of 1 and 2 remain inexpressible under either mechanism** — that is the band-deletion
   problem, a different defect. The proposed edit does not touch it.
2. **The gain applies only to the two apartment archetypes that already carry a `ZoneGroup`.** The
   other **seven** `fallback_not_expressible` archetypes fail on middle-band ambiguity, which is
   structural. **So "restore exact expressibility" was true of the mechanism and overstated as a
   remedy.**

**The "90 buildings" figure is not re-derivable without compute.** It traces to
`docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_REMAINder.md:1302-1315`
(66 `MidriseApartment` + 24 `HighriseApartment`, from a 7,442-building crosstab). Reproducing it needs
a fleet-wide `compute_band_map()` / `match_storeys()` pass — **EnergyPlus-free, but still a fleet
pass**, so it is out of scope for a no-compute task and is **named as the smallest settling
experiment** for when a machine is free. **The number is therefore carried, not verified.**

**Settled 2026-08-06 (C03, `PLAN_compute-queue.md`).** Report:
`extra/MEASUREMENT_open-10_band-expressibility-fleet.md`. **90 reproduces exactly, no adjustment
made** — a fleet-wide pass using the shipped, unmodified `compute_band_map()`/`match_storeys()`
over all twelve cells' real `(archetype_id, num_floors)` pairs (7,442 evaluated, 718 excluded —
both counts an exact match to the carried figures) finds `fallback_not_expressible` = 66
`MidriseApartment` + 24 `HighriseApartment` = **90**, out of 1,976 fallback_not_expressible
fleet-wide across 10 archetypes. Applying N11's proposed direct-`ZoneGroup`-overwrite mechanism to
those 90 flips **100% of them** to `applied`, and leaves `fallback_shorter` (`n_real ∈ {1,2}`)
counts unchanged for both archetypes — both of N11's stated limits hold at fleet scale. **New
finding, not a contradiction:** N11's illustrative "7 structural archetypes" list undercounts the
real fleet population — 3 of those 7 (`College`, `LargeHotel`, `Laboratory`) have zero fleet
buildings, while 4 unlisted archetypes sharing the same `n_proto==2` condition
(`SmallOffice`, `QuickServiceRestaurant`, `SecondarySchool`, `FullServiceRestaurant`) dominate:
`SmallOffice` alone accounts for 1,580 of the 1,976, 16x the two apartment archetypes combined. The
`ZoneGroup` gain, if built, would resolve 4.6% of the fleet's `fallback_not_expressible` population,
not the other 95.4%.

### OPEN-11 — Six inverted-geometry buildings still need post-hoc remediation ⚠️
The Phase-E re-run landed 8,154/8,160; the 6 drops are the REPORT §7 limitation-#6 inverted-geometry
buildings whose `10_fails_solution.md` remediation was not re-applied in the automated run.
Pre-existing, small, and **recorded as not-a-defect-of-that-arc** — but never closed. Confirm the 6
are still the same 6 before planning anything.

**Amended 2026-08-06 (N04). ✅ Confirmed — the six are the same six, `osm_id` for `osm_id`:**
`la_rural/way/472960972`, `472961034`, `472961088`, `472961091`, `472961171`, and
`la_urban/way/402215469`. Fleet success recomputed directly from the live result files at
**8,154/8,160**, matching the register.

**The precondition this item set on itself is met**, so it is now plannable — what remains is the
remediation decision, not a measurement.

---

### OPEN-46 — The elevator end-use breakout exists only in the archived arc's own copy of the code, never in the live tree 🔴 **OPENED 2026-08-12**

> 🔴 **REVERSED AND AMENDED 2026-08-12 (night, T03–T05 of `PLAN_three-new-items-2026-08-12.md`). The
> premise above is wrong. Read this before quoting anything in this section.**
>
> **What is true: elevator energy IS in the adopted run and IS inside the published
> `157.1 kWh/m²`.** All 12 `docs_VALIDATION/validations/overAll/results/phaseE_elevrb/*/05_results.csv`
> already carry **`elevators_eui_kwh_m2`** and **`gwp_elevators_kgco2_m2`** columns. Across 8,160
> rows, **3,561 are non-zero**, summing to **12,508.8 kWh/m²**; in `nyc_urban` exactly **87** are
> non-zero — precisely the 87 buildings whose archetype appears in `elevators_by_archetype.json`.
> Against the pre-elevator `phaseE` run, the **median** of `|Δtotal_eui − elevators_eui|` is **exactly
> 0** in `nyc_urban` and `austin_centre`: the entire change in the total column *is* the elevator
> column.
>
> ⚠️ **Why both the executor and the director first got this wrong, recorded because the lesson
> transfers.** Both checked `equipment_eui_kwh_m2` and found it flat for the 87 eligible buildings,
> and read flat as absence. **Flat is what de-folding produces** — the load is added, then subtracted
> back out of equipment into its own column. The earlier framing in this register ("elevator energy
> sits folded inside `equipment_eui_kwh_m2`") is also wrong for the same reason: it is *de-folded out*
> of equipment, not folded into it. **Check the invariant a transform preserves — the total — not the
> column it moves energy between.**
>
> 🔴 **What is genuinely broken, and it is larger than the item as opened: the adopted run cannot be
> reproduced from this repository.** Live `openubem/idf/builder.py` never calls `assign_elevators`
> (`git log --all -S assign_elevators -- openubem/idf/builder.py` is empty; the only commit ever to
> touch the string is `ef19141`, which added the **archived** copies plus three orphan live files).
> **Split out as OPEN-48**, which is where that defect now lives.
>
> ✅ **What T05 delivered — the reporting path restored, guarded, with the total proven invariant.**
> `parser.py` (`_ELEVATOR_METER`, guarded de-fold at `:346-349`), `outputs.py:43` (14th meter),
> `carbon.py` (`gwp_elevators_kgco2_m2`), `aggregator.py` (`_STEP5_COLS`). The guard: the column is
> **always** set, and `if elevators_kwh:` gates the de-fold — meter absent ⇒ `0.0` and no de-folding.
> The archived parser subtracts unconditionally at `:306`; this one does not. The executor
> independently confirmed the restored shape is the one that produced the adopted files: **the adopted
> CSV header order matches the archived `_STEP5_COLS` position-for-position**, `elevators` between
> `refrigeration` and `total`.
>
> **Invariant gate, re-derived by the director on a different SQL file than the executor used**
> (`scratchpad/t3_cleanzoning_work/cross/sim/way/cc_cross/eplusout.sql`; HEAD's parser loaded
> side-by-side with the working-tree parser): **12 shared keys, all bit-identical**, `total_eui_kwh_m2`
> `0x1.d492d97e88c30p+7` before and after, the only difference being the new key at `0.0`.
> Non-vacuity, meter present: a 12,000 kWh elevator meter injected into a copy of a real SQL gives
> elevators `3.5294117647058822`, equipment `63.73196294400685 → 60.20255117930097` (Δ exactly the
> elevator EUI), `|total − Σ(10 end-uses)| = 0.0`, `gwp_total` Δ `0.0`; the total moves **2.84e-14
> (1 ULP)** between the absent and present paths — float re-association, reported by the executor
> rather than hidden.
>
> **Tests, director-re-run: 147 passed** across the six affected files; `pytest --collect-only -q` =
> **2006** (the plan's 1,990 was stale — parallel executors landed new tests), **no drop**.
> 🔴 **`tests/test_parser_elevators.py` passes 8/8 with every original assertion intact — nothing was
> weakened.** `tests/test_step3_orchestrator.py` was correctly left untouched: its
> `test_medium_office_idf_contains_elevator_equipment` asserts a *built IDF* contains the Elevators
> object, which is the load wiring and out of scope.
>
> **Why it stays open:** the reporting path is restored but **the live tree still emits no elevator
> equipment**, so anything simulated today reports `0.0`. Re-wiring the physical load is a user
> ruling, not an executor's call. Reports: `extra/MEASUREMENT_open-46_sql-subcategory-probe.md`,
> `extra/MEASUREMENT_open-46_divergence-inventory.md`, `extra/FIX_open-46_elevator-breakout.md`.
>
> **T03 note.** The probe of the adopted run's own SQL **stopped without an answer, correctly**: every
> `sql_path` points under `%TEMP%\ubem_elev_rebaseline\` and all twelve cell roots contain **0 files**.
> A synthetic-SQL control confirms the probe query works, so this is a real absence, not a broken
> scanner. **No substitute SQL was generated and reported as the adopted run's** — the one failure mode
> that would have made the task worthless.


**How it was found.** T05's triage of OPEN-44 asked why `tests/test_parser_elevators.py` fails live.

**What is true, director-verified by direct read:**
- `openubem/results/parser.py` documents and computes **9 end-uses** and contains **no** `elevators_eui_kwh_m2`. `openubem/idf/outputs.py` carries **13** meters and **no** elevator meter.
- The archived copy at `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/openubem/results/parser.py:305-321` **does** have it, including the de-folding line `eui["equipment_eui_kwh_m2"] -= eui["elevators_eui_kwh_m2"]`, and the archived `outputs.py` expects **14** meters.
- Of the five test files that exist in both trees: **2 are byte-identical** (`test_elevators.py`, `test_parser_elevators.py`), **3 have drifted — and in all three the drift is the live copy having the elevator expectation removed**: `test_outputs.py` (14 → 13 meters, elevator meter dropped from the required subset), `test_results_aggregator.py` (`elevators_eui_kwh_m2` and `gwp_elevators_kgco2_m2` removed from the expected-row dicts — director-verified: 2 references archived, 0 live), and `test_step3_orchestrator.py` (a whole test, `test_medium_office_idf_contains_elevator_equipment`, **deleted**, not edited).

🔴 **The reading, stated as an inference and not as a fact:** whoever last worked in `tests/` **removed the failing expectations in three files instead of implementing the feature**, and missed `test_parser_elevators.py`, which is why one file still fails live. No commit has been identified as the author of that choice, and none is asserted here.

✅ **What this does NOT mean — stated first because it is the question a reader will ask.** **The adopted fleet figure of 157.1 kWh/m² is not affected and elevator energy is not missing from it.** `openubem/idf/elevators.py` is live and emits the DOE-verbatim lift motor as `ElectricEquipment` with `EndUse_Subcategory = "Elevators"`, so that energy **is** simulated and **is** counted inside `equipment_eui_kwh_m2` and therefore inside the total. What is missing is only the **separate reporting line and the de-folding of elevators out of equipment.**

**What is therefore false as written:** the adopted-baseline phrase "**elevators, the 10th end-use**" describes the archived arc, not the live code. **Live, there are 9 reported end-uses and elevators are folded inside equipment.** Every place that phrase appears needs the qualification.

**Open questions, not answered here:** whether the breakout should be implemented or the claim retracted; and whether `openubem/results/carbon.py`'s `gwp_elevators_kgco2_m2` has the same shape.

---

## 5. Theme D — Data acquisition and imputation

### OPEN-12 — The rural building-height residual ⚠️ **the recorded numbers do not reproduce**
~~`nyc_rural` 36.4% and `austin_rural` 19.2% of buildings still carry no `height_m` after the UTCI
arc's backfill.~~ The arc's own closing note is unusually clear about the remedy and worth quoting as a
constraint on any plan: **closing this needs better source coverage, not another imputation pass.**

**Amended 2026-08-06 (N06), and this is the more serious half of that task.** Re-derived from the
fleet's own Stage-1 files — `01_buildings.gpkg`, all twelve cells — and **director-verified by
independent re-derivation the same evening**:

| Cell | Register records | Measured in `01_buildings.gpkg` |
|---|---|---|
| `nyc_rural` | 36.4% | **100.00% — 198 / 198** |
| `austin_rural` | 19.2% | **100.00% — 245 / 245** |
| `nyc_suburban` | *not named by this item at all* | **100.00% — 1,589 / 1,589** |

**Both numbers are recorded side by side and NOT adjudicated** — register §0's rule, and the executor
was explicitly forbidden to reconcile them. Fleet-wide the figure is **2,806 / 8,160 = 34.39%** with no
`height_m`. Note also: **zero buildings fleet-wide carry a present-but-zero height** — every missing
height is a genuine null, so no "0 means missing" ambiguity is in play.

~~**The most likely reconciliation, stated as a hypothesis and owned by another task.** The UTCI arc's
backfill may never have been written back into the fleet's Stage-1 files at all — which is
**precisely what OPEN-14 says** (*"the fix lives in the mechanism rather than in committed data"*).
If so, OPEN-12's percentages describe the UTCI arc's own working dataset while the fleet's actual
inputs were never backfilled. **N09 owns that reconciliation; this section does not settle it.**~~

**Hypothesis settled 2026-08-06 (N15) — and it is refuted as a *shared cause*, while its factual half
holds.** Report: `extra/MEASUREMENT_open-12-14_backfill-consumption.md`. The fleet's Stage-1 files
**never consumed the backfill** — that half is confirmed. But the reason is not that OPEN-14's
mechanism failed to reach them: **no fleet Stage-1 file could ever have consumed it**, because the
fusion path is not on the fleet's code path at all. **OPEN-12 is therefore a genuine source-coverage
gap in OSM tags, exactly as the arc's closing note said** — not a leaked artefact of OPEN-14.
**Director-verified by independent re-derivation:** `fusion.fuse()` has **exactly one caller**
fleet-wide (`imputation.py:655`, inside `_fusion_tier`), and `building_classifier.py` — which owns
`_impute_levels` at `:123`, called at `:525` — **never imports the imputation module**; its sole
mention of the word is a comment header at `:121`. So the unreachability is **architectural and
config-independent**, stronger than the `FUSION_SOURCES_BY_TARGET = {}` no-op argument.

**Two consequences either way.** (a) `nyc_suburban` — **1,589 buildings, the fleet's largest cell** —
has no height for a single building and is not named in this item's framing. (b) This item and
**OPEN-35 are the same population seen from two sides**: 1,589 of `nyc_suburban`'s buildings have
neither input, so they are 61% of OPEN-35's 2,611 on their own.

### OPEN-13 — E-UTCI-12 and E-UTCI-13 ~~✅ **read at last, and both are still live**~~ ~~🟡 **E-UTCI-13 FIXED 2026-08-12; E-UTCI-12 contained only**~~ 🟢 **collection residual DISCHARGED 2026-08-13 — item stays open on E-UTCI-12 alone**

> 🟢 **The collection residual is finished 2026-08-13** (T02 of `PLAN_five-items-2026-08-13.md`; CP-1
> signed). It turned out to be **half-done already**: the `_HAS_DRAW_TIER` guard and the narrowing of the
> module-level skip had landed earlier, so the 43 tests in `test_draw_methods.py` that do not need the
> draw tier were already collecting and running. T02 finished the other half — the **9** tests that *do*
> need `_draw_tier` / `_draw_stratum_col_for` now skip with a reason instead of erroring.
>
> 🔴 **This does not fix anything.** The draw tier's router wiring **still does not exist**; promoting it is
> **OPEN-17**, reserved to the user. **E-UTCI-12 is untouched and this item stays open on it alone.**
~~Forwarded out of the UTCI arc at close, to "whichever arc next owns Stage-1 acquisition or Stage-2
imputation". **Content not re-read this session** — read `docs_DONE/OUTDOOR/UTCI/` before planning.~~

**Amended 2026-08-06 (N09).** Report: `extra/MEASUREMENT_open-13-14_utci-forwards.md`. Both were read
for the first time since they were forwarded, and **both reproduce at HEAD** — not from the arc doc,
but by re-running the defect:

**E-UTCI-12 — `pytest` cannot collect the test suite.** `tests/test_draw_methods.py:645` imports
`imputation._draw_tier`, which **has never existed** in `openubem/semantic/imputation.py`. A bare
`pytest -q` therefore aborts at **collection**, not at a single test. **Director-verified 2026-08-06:**
`grep -c "_draw_tier" openubem/semantic/imputation.py` → **0**, and the import is live at `:645`.
**This is worse than a failing test — it means the whole suite has not been runnable as a whole**, and
nobody noticed, which is itself the finding.

**E-UTCI-13 — the height cache silently nulls two columns on every re-read.** `height_cache.pull_overture`
stores `fetch_overture()`'s **already-normalised** output; `fusion.OvertureSource.join` then re-reads
that cache **through `fetch_overture()` again**, re-normalising a frame whose raw-schema columns
(`num_floors`, `class`) are already gone. `levels` and `use_class` are nulled; `height` survives. N09
**empirically reproduced it** against the committed fixture: pass 1 → 2/2 non-null, pass 2 → **0/2**.

**Recorded, not merged (§OPEN-17 discipline):** E-UTCI-12 and OPEN-17 are the same underlying gap seen
from two sides — the draw tier was never wired into `imputation.py` at all. **Do not close one with
the other.**

#### 🟡 2026-08-12 — both defects addressed; **one fixed, one contained**. Report: `extra/FIX_open-13_height-cache-and-collection.md`; plan `implemenation/PLAN_five-item-sweep-2026-08-12.md` §8 T03–T04.

**E-UTCI-13 — FIXED.** `openubem/semantic/fusion.py` gains `_load_overture_layer(cfg)`, called from
`OvertureSource.join` in place of the direct `fetch_overture(...)`. If the configured slice on disk
already carries the normalized schema, it is read straight through; a raw-schema slice or a live
`endpoint` pull still goes through `fetch_overture()` unchanged.

🔴 **Director-re-derived, all three legs in one process, against a two-row raw slice:**

| state | `levels` non-null | `use_class` non-null |
|---|---|---|
| pass 1, raw slice via `fetch_overture` | **2 / 2** | **2 / 2** |
| pass 2, normalized cache via `fetch_overture` (before) | **0 / 2** | **0 / 2** |
| pass 2, normalized cache via `_load_overture_layer` (after) | **2 / 2** | **2 / 2** |

Pass 1 differs from "before", so the before/after is non-vacuous. Values confirm the predicted
asymmetry: `height` and `year_built` were never affected; only `levels` and `use_class` were nulled.
Root cause named at source: `_normalize()` (`overture_fetcher.py:111-127`) consumes `num_floors` and
`class` and emits `levels` and `use_class` — **the rename is not idempotent.**

⚠️ **Weakness carried forward, deliberately recorded.** `_NORMALIZED_OVERTURE_COLUMNS` duplicates the
fetcher's `_NORMALIZED_COLUMNS` (`overture_fetcher.py:29`) as a literal rather than importing it.
Verified set-equal today. If that schema ever changes, the guard stops matching and every read
**silently** reverts to the double-normalizing path. Safe direction, silent failure — the same
property that hid this defect for months. No unit test covers the cached-read path.

**E-UTCI-12 — CONTAINED, NOT FIXED.** `tests/test_draw_methods.py` gains a module-level
`pytest.skip(allow_module_level=True)` citing OPEN-17.

🔴 **The executor did NOT take the user's OPEN-17 decision** — checked, not assumed. `_draw_tier` is
still absent from `openubem/semantic/imputation.py`; `_CANONICAL_TIER_ORDER` is
`('fusion','spatial','ml','statistical')` and `_TIER_HANDLER_NAMES` has four entries, neither
carrying `"draw"`; `config.IMPUTE_DRAW_METHOD_BY_TARGET` does not exist. **OPEN-17 remains wholly the
user's call, and the "do not close one with the other" rule above still stands.**

🔴 **Director-re-derived, both legs on the real tree:** before (HEAD content restored in place via
`git stash` of that one file) → `AttributeError ... has no attribute '_draw_tier'` at
`test_draw_methods.py:645`, `Interrupted: 1 error during collection`, **no tests collected, exit 2**.
After → **1937 tests collected, exit 0**. The abort is at *class-body* evaluation
(`class TestNoEUILeakage`, line 631), i.e. at import — which is why one file killed the whole repo's
collection.

🔴 **New cost the executor did not report.** The module skip removes **53 tests**, but only **13**
reference the unimplemented draw-tier names. Measured in a scratchpad copy of the HEAD file with only
the single offending class removed: it collects and runs **43 passed, 9 failed**. **So 43
currently-passing tests of the already-implemented `draw_methods` registry are now silently skipped**,
and nothing reports them as missing. Also measured: `@pytest.mark.skip` on the class does **not**
stop the class body executing, so the narrow route is not a one-liner — it needs conditional
collection (e.g. guarding on `hasattr(imp, "_draw_tier")`), which is a design choice.

🔴 **What the restored collection immediately exposed — and this is the real payoff of the task.**
Because the suite can be collected, it could be **run to completion for the first time in months**:
`python -m pytest -q -p no:cacheprovider` → **70 failed, 1822 passed, 10 skipped, 36 errors, exit 1,
26m47s.** **106 failing or erroring tests were being hidden by the collection abort.** Where they
live: **61 in `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/`**, 44 in `tests/`, 1 under
`scripts/analysis/`. What they are: **51 `FileNotFoundError`** from tests asserting an output artifact
exists on disk (**not logic failures — roughly half the red is artifact-dependence**), ~36 setup
errors from a missing `synthetic_10_gdf` fixture, 5 `AttributeError` on a non-existent
`config.IMPUTE_DEBIAS…` attribute, 8 elevator-column `KeyError`s. **Opened as OPEN-44 — do not report
this as "70 broken tests."**

**Disposition. E-UTCI-13 closes. E-UTCI-12 does not** — the suite is collectable again, which was the
stated goal, but 43 tests were traded for it. **OPEN-13 stays open on that residual**, and narrowing
the skip is the next step on it. Incidental: `tests/fixtures/synthetic_30_archetype_coverage.gpkg`
shows modified in git — table-by-table comparison against HEAD shows the *only* difference is
`gpkg_contents.last_change`; the `synthetic` data table is hash-identical at 25 rows. A test opens the
checked-in fixture for write; **no data changed.**

#### ✅ 2026-08-13 — **the carried-forward weakness at `⚠️` above is now discharged.** T01 of `implemenation/PLAN_five-more-items-2026-08-13.md`; report `extra/FIX_five-more-items-2026-08-13.md`.

`openubem/semantic/fusion.py:191-198` no longer hand-copies the schema. It **imports** the fetcher's
own tuple and derives from it:

```python
from openubem.acquisition.overture_fetcher import _NORMALIZED_COLUMNS as _OVERTURE_FETCHER_COLUMNS
_NORMALIZED_OVERTURE_COLUMNS = set(_OVERTURE_FETCHER_COLUMNS)
```

Director-verified a **provable no-op** at HEAD (the two sets were already equal), so no behaviour
changed. Two new tests cover the previously-untested cached-read path:
`test_normalized_schema_cache_hit_skips_fetch_overture` and
`test_raw_schema_slice_goes_through_fetch_overture`.

🔴 **The regression test as first delivered was VACUOUS, and this is the lesson worth keeping.**
`assert fusion._NORMALIZED_OVERTURE_COLUMNS == set(_NORMALIZED_COLUMNS)` is a **tautology by
construction** — the fix derives the left side from the right, so the assert can never fail no matter
what the schema becomes. Its comment nonetheless claimed a future schema change *"must fail this
test."* The executor's own non-vacuity "proof" — corrupting the attribute in memory and watching the
assert fire — demonstrated only that the assert *reads* the attribute, **not that it has any power.**

**Repaired** (`tests/test_fusion.py:299-311`): the load-bearing assert now pins the six names as an
**explicit literal**, written down independently of the thing it checks. Proved by mutation —
adding a seventh column to `overture_fetcher.py:29` produces
`AssertionError … Extra items in the left set: 'extra_mutation_column'` at `tests/test_fusion.py:307`.
Restoration verified: `git status --porcelain openubem/acquisition/overture_fetcher.py` empty, line 29
byte-identical to the original.

> **Standing lesson, recorded here because it generalises past this item:** a regression test is
> non-vacuous only if **the thing it pins is written down independently of the thing it checks.**
> An executor cannot audit its own non-vacuity by mutating the value the assert reads.

**E-UTCI-12 residual unchanged.** OPEN-13 stays open on it.

### OPEN-44 — ~~🔴 **The test suite has 70 failures and 36 errors**~~ ✅ **ZERO FAILURES, ZERO ERRORS 2026-08-13 — and read the rider before believing that number**

> ✅ **RESOLVED 2026-08-13 (T02 of `PLAN_five-items-2026-08-13.md`; CP-1 director-signed by independent
> re-derivation).** All **45** remaining red nodes now **skip with a reason that names its item and says
> what would make the test run again.** The suite result moved from
> **26 failed · 1,859 passed · 10 skipped · 19 errors** to **0 failed · 1,859 passed · 55 skipped · 0
> errors** (`1859 passed, 55 skipped, 11 warnings in 1446.85s`).
>
> 🔴 **THE RIDER, AND IT IS THE WHOLE POINT: A SKIP IS A DEBT, NOT A FIX.** Nothing was repaired and no
> feature was built. **The suite is now honest, not more capable.** Anyone who reads *0 failed* as *the
> features exist* has misread this item. 31 of the 45 skip because an artifact is absent on this machine;
> **14 skip because a feature was never shipped**, and building it is **OPEN-17 — the user's decision.**
>
> 🟩 **The check that matters most: the passed count did not move.** 1,859 before, **1,859 after**. No test
> was deleted, disabled, or quietly downgraded from a real assertion into a skip. The 10 pre-existing skips
> are unchanged.
>
> **Director re-derivation.** An AST walk collected every test carrying a `skipif` (own or inherited) in
> the five touched files and diffed that set against the 45 `nodeid`s in `open44_test_triage.csv`:
> **5/5, 9/9, 5/5, 8/8, 18/18 — zero red-but-unguarded, zero guarded-but-not-red.** The full diff was read
> line by line: **none of `IMPUTE_DRAW_METHOD_BY_TARGET`, `IMPUTE_DEBIAS_NEWERSKEW`, `_draw_tier`,
> `_draw_stratum_col_for` appears anywhere, and no file under `openubem/` was modified** — the forbidden
> shortcut of making 14 tests green by enacting OPEN-17 was not taken.
>
> ⚠️ **One small coverage loss, recorded rather than waved through.**
> `test_impute_montage.py::test_out_dir_resolves_beside_parent_plan` carries two assertions and only one
> needs the missing file, but the guard was applied to the whole test — **so a path-resolution assertion
> that could run on this machine no longer does.** Being split; tracked, not forgotten.
>
> 🟩 **This also discharges OPEN-13's residual** — see that item.

**Opened 2026-08-12** by the director, from the side effects of OPEN-13's own fix rather than from a
task that went looking. **Fifth item in this arc found by auditing an output instead of running
something.** Report: `extra/FIX_open-13_height-cache-and-collection.md` §3.

**First measurement: made (this is it).** `python -m pytest -q -p no:cacheprovider`, full tree, 26m47s:
**70 failed · 1,822 passed · 10 skipped · 36 errors · exit 1.** This is **the first complete pass/fail
count this project has had in months** — E-UTCI-12's collection abort had made it unobtainable, so
every past claim that "tests pass" covered an unknown subset. **106 failing or erroring tests were
behind that abort.**

**Where they are:**

| tree | failed + errored |
|---|---|
| 🔴 `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` | **61** |
| `tests/` | **44** |
| `scripts/analysis/test_viewer_layout_assign.py` | 1 |

🔴 **`docs/` holds 30 `.py` files, 5 of them test files**, against the project's own hard rule —
*"No `.py` files under `docs/`, ever."* pytest collects them and they produce **58% of the entire
failure count**. **Two of the five are byte-identical duplicates of files in `tests/`**
(`test_elevators.py`, `test_parser_elevators.py`, verified with `cmp`); **the other three differ from
their `tests/` twins**, which is the worse case — a stale duplicate that has drifted can pass or fail
for reasons unrelated to the shipped code.

**What the failures actually are** — this matters more than the total:

| cause | count |
|---|---|
| `FileNotFoundError` — a test asserting an **output artifact exists on disk** | **51** |
| missing pytest fixture `synthetic_10_gdf` (setup errors) | ~36 |
| `AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DEBIAS…'` | 5 |
| `KeyError: 'elevators_eui_kwh_m2'` / `'Elevators:InteriorEquipment:Electricity'` | 8 |
| other assertions | remainder |

🔴 **Roughly half the red is artifact-dependence, not broken logic.** Those tests assert a CSV or a
findings document is present, so they fail on any checkout where the artifact was never regenerated.
**Do not report this item as "70 broken tests" — that would be the same category error this register
keeps catching** (a count reported as a cause).

⚠️ **The `IMPUTE_DEBIAS…` group is E-UTCI-12's shape a second time**: tests committed against a config
attribute that has never existed. **That is OPEN-36's territory** (*a signed completion record
describing code that has never existed*) and suggests OPEN-36's "1 governance gap, T07, the known one"
bound is **too tight**. 🔴 **Do not close OPEN-36 without re-checking it against this.**

**Incidental, recorded so it is not rediscovered as a mystery:**
`tests/test_sim_integration.py::test_synthetic_fleet_full_annual` emits a **Windows access-violation
faulthandler dump** from `joblib`'s `loky` backend spawning subprocesses under Python 3.14. **It does
not stop the run** — the suite continued past it and finished.

~~**What is NOT known, and is the next step:** how many of the 44 `tests/` failures are real defects in
shipped code as opposed to artifact-dependence or dead tests. **That triage has not been done and must
not be guessed at.**~~ ✅ **DONE 2026-08-13 — see the amendment below.** Nothing published is known to
depend on any of them.

> **Amended 2026-08-13 (T02 of `PLAN_two-measurements-2026-08-13.md`, signed at CP-1). The `tests/`
> triage is complete, and the director reproduced the whole measurement independently.**
>
> **Run at HEAD, `tests/`-only:** `26 failed · 1,857 passed · 10 skipped · 19 errors · exit 1`,
> 1,912 collected. 🔵 **Director re-ran the identical command in a separate 18m02s session and got
> the same four counts, and — checked node by node from the JUnit XML — the *same 45 failing/erroring
> node IDs, with zero on either side of the set difference.* The measurement is reproduced, not
> reviewed, and the suite is deterministic across two independent runs.**
>
> **Reconciliation against the 2026-08-12 same-scope baseline (25 failed / 19 errors) — director-verified
> against `git show --stat 6aeebb0 -- tests/`, which touches exactly the 9 files claimed:** the
> elevator breakout fixed 8 previously-failing tests, two new all-green files were added, and
> `test_draw_methods.py`'s module-level `pytest.skip(` was replaced by a narrowed
> `@pytest.mark.skipif` (confirmed in the diff), unmasking 52 tests never counted before — 43 pass,
> 9 fail. Net −8 + 9 = +1, i.e. 25 → 26. **The +1 is explained, not waved at.**
>
> | category | nodes |
> |---|---|
> | `artifact-missing` | **31** |
> | `stale-expectation` | **14** |
> | `fixture-missing` / `real-defect` / `undetermined` | **0 / 0 / 0** |
>
> **The 31 are disk-artifact absence, director-verified at the root cause:**
> `docs/docs_DONE/phaseC_combinedResim/v19_validation/` **does not exist on this machine at all**
> (26 nodes), plus 5 nodes needing imputation phase-figure PNGs that were never regenerated here.
>
> 🔴 **Director correction to the executor's framing of the remaining 14 — the classification is
> right but the label undersells it.** These are not obsolete tests. **The code they exercise is
> shipped and present; what is missing is the last wiring step**, and both halves are *already
> registered items*, so no new ID was opened for either:
>
> - **9 nodes (`tests/test_draw_methods.py`) → OPEN-17.** Re-verified independently:
>   `_CANONICAL_TIER_ORDER` at `openubem/semantic/imputation.py:543` is
>   `("fusion","spatial","ml","statistical")` with **no `"draw"`**; `openubem/semantic/imputation.py`
>   imports neither `draw_methods` nor `debias`; and `git log -S"IMPUTE_DRAW_METHOD_BY_TARGET" --
>   openubem/config.py` returns **nothing — the setting has never existed in any commit.** This is
>   exactly OPEN-17's "the imputers exist but the tier does not," now with a test-level cost attached.
> - **5 nodes (`tests/test_debias.py`) → OPEN-36.** Same shape on `config.IMPUTE_DEBIAS_NEWERSKEW`,
>   whose absence from every commit OPEN-36 had already director-verified. `debias.py` is present but
>   referenced by nothing.
>
> 🔴 **Consequence for the "make the suite green" instinct: these 14 are the only remaining record
> that two features were built and never connected. Skipping or deleting them erases that record.**
> The recommendation is to leave them red and let OPEN-17 / OPEN-36 carry the work. **No ruling is
> taken here; nothing was skipped, deleted or edited.**
>
> **Coverage cost if they were suppressed anyway (asked for by the plan, measured not estimated):**
> `tests/test_debias.py` holds 14 tests, 5 failing. Removing just the 5 costs 5 tests of debias
> hook-wiring coverage that nothing else exercises. A **file- or module-level** suppression — the
> E-UTCI-12 shape — would also silently kill the 9 that currently pass, total cost 14. **The blunt fix
> is 2.8× more expensive than the narrow one.**
>
> **Evidence:** `openubem/outputs/comparisons/open44_test_triage.csv` (45 rows, one per failing or
> erroring node); report `extra/MEASUREMENT_open-44_test-triage.md`; script
> `scripts/analysis/open44_test_triage.py`. ⚠️ **Both the CSV and the report replaced same-named files
> committed at `6aeebb0`, whose contents were the wider 106-node whole-repo triage. Nothing is lost —
> the superseded versions are retrievable at that commit — but the working-tree copies are now
> `tests/`-scope only, and any citation of the 106-node numbers must resolve against `6aeebb0`.**
>
> **What the executor correctly declined to determine, recorded so it is not mistaken for a gap:**
> whether any of the 10 currently-skipped tests would fail if unblocked (outside the failing-node
> closed set), and whether `tests/test_draw_methods.py`'s 9 failures were the same item as the parked
> draw-tier arc — **the director resolved that second one above: they are.**

#### ✅ Amendment 2026-08-13 (later, CP-2 of `PLAN_five-more-items-2026-08-13.md`) — the **whole-tree** run, which OPEN-44's closure never covered

OPEN-44 closed on a **`tests/`-scoped** run. CP-2 of the following arc ran the **whole tree**, alone,
21 minutes: **`1910 passed, 35 failed, 55 skipped, 11 warnings, 17 errors in 1262.90s`**.

🟢 **OPEN-44's closure holds — zero failures and zero errors under `tests/`.** Proven two ways, because
the captured summary lost its first 12 `FAILED` lines to the launch pipeline: (a) pytest emits the
summary in execution order and the **last** surviving `FAILED` line is `scripts/analysis/…`, which sorts
*before* `tests/`, with the totals line intact — a `tests/` entry could not have been lost; (b) a re-run
of the truncated region gave **32 failed, 44 passed in 16.45s**, and 32 + 2 + 1 = **35**, reconciling the
full run with no residue.

🔴 **All 52 non-passing results have exactly two causes, and neither is a defect in shipped code:**

| Count | Where | Cause |
|---|---|---|
| 34 failed + 17 errors = **51** | `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` | `FileNotFoundError: …\docs_DONE\LOADS & SCHEDULES\elevators\scripts\openubem\idf\templates\commercial_base.idf` |
| **1** failed | `scripts/analysis/test_viewer_layout_assign.py:24` | `NameError: name 'zones_found' is not defined` — **the single `REAL-DEFECT` this item catalogued on 2026-08-12, still unfixed** |

The 51 are **one root cause, not fifty-one**: the archived elevators arc carries its own copy of the
test tree, and that copy resolves the IDF template relative to its archived location, where
`openubem/idf/templates/` does not exist. It is an artefact of *where the files sit*. The shipped
elevator code is green — its live tests under `tests/` are inside the 1910.

🔴 **This changes what checklist item 2c costs.** The 30 stray `.py` files under `docs/` have been
carried as a tidiness item against the *no `.py` under `docs/`, ever* rule. They are not tidiness:
**they put 51 red results into every whole-tree run**, which is exactly the noise floor a real
regression hides under. A suite permanently red by 52 cannot be used as a gate by anyone who has not
first memorised which 52. **This is an argument for deleting the strays, not for ignoring them** — and
it is the second time this register has found that an unfixed hygiene item was quietly buying a real
loss of signal.

### OPEN-14 — The UTCI height backfill is not reproducible from a clean checkout ✅ **confirmed, and it is bigger than "a rebuild"**
The fix lives in the mechanism rather than in committed data. Anyone rebuilding Stage 6 from a fresh
clone does not get the backfilled heights. This is a **reproducibility defect in shipped inputs**,
which makes it structurally different from the two items above it — and arguably more urgent, because
it silently invalidates a rebuild rather than degrading a known cell.

**Amended 2026-08-06 (N09). ✅ Confirmed open, with the artifact named.** **Director-verified:**
`git ls-files -- "openubem/data/fixtures/fusion/*"` returns **six files**, and the only Overture slices
tracked are `overture_testcell_slice.parquet` (synthetic) and `overture_nyc_centre_slice.parquet` —
**no slice exists for any affected cell.** `openubem/config.py:141` ships
`FUSION_SOURCES_BY_TARGET: dict = {}`, so `fuse()` is a **guaranteed no-op on a clean checkout**.

🔴 **Convergence with N06, found by the director and not by either executor.** N09 names four cells as
lacking a tracked Overture slice: `nyc_suburban`, `nyc_rural`, `austin_centre`, `austin_rural`. N06's
independent census of missing `height_m`, run by a different executor against different files, ranks
the twelve cells — and **the top four are exactly those four**:

| Cell | No `height_m` | Overture slice tracked? |
|---|---|---|
| `nyc_suburban` | **100.00%** (1,589/1,589) | ✗ |
| `nyc_rural` | **100.00%** (198/198) | ✗ |
| `austin_rural` | **100.00%** (245/245) | ✗ |
| `austin_centre` | **84.50%** (349/413) | ✗ |
| every other cell | ≤ 26% | — |

~~**Two tasks that did not share notes arrived at the same four cells from opposite ends.** That is the
strongest available evidence that **OPEN-12's residual is not a source-coverage problem but this
item** — the backfill's output was never committed, so the fleet's own Stage-1 files never had it.~~
**Stated as a convergence, deliberately NOT adjudicated** — proving it needs one more step: showing
that the fleet's `01_buildings.gpkg` was produced by a path that would have consumed the slice.
**That step is a measurement nobody has run, and it is the next thing on this item.**

🔴 **The convergence is a COINCIDENCE. Settled 2026-08-06 (N15), the step named above having now been
run.** Report: `extra/MEASUREMENT_open-12-14_backfill-consumption.md`. The fleet's
`01_buildings.gpkg` was **not** produced by a path that would have consumed the slice — two
independent lines of evidence, **each alone sufficient**, and both director-verified from the raw
files rather than from the executor's report:

| Line | Evidence | Director's independent check |
|---|---|---|
| **Code reachability** | Every cell, `nyc_centre` included, runs `step1_fetch → BuildingClassifier.classify → _impute_levels`, which never calls `fusion.fuse()` | ✅ `fuse()` has one caller only (`imputation.py:655`); `building_classifier.py` never imports imputation |
| **Chronology** | `nyc_centre`'s `01_buildings.gpkg` was committed **`e063865`, 2026-06-30** — its own Overture slice first appears **`ef19141`, 2026-07-21**, three weeks later | ✅ both hashes and dates reproduced exactly by `git log --all -- <path>` |

**A file cannot consume a slice that does not yet exist.** `nyc_centre` was the discriminating case
precisely because it is the one affected cell *with* a tracked slice and *with* good height coverage —
and its coverage turns out to have a different origin entirely.

**Net effect: OPEN-12 and OPEN-14 are two separate items, not one defect under two names.** OPEN-12 is
OSM-tag source coverage; OPEN-14 remains the UTCI arc's own, unrelated backfill-reproducibility gap.
**Both stay open. Neither may be closed by fixing the other.**

**A note on the director's own reasoning, recorded deliberately.** The four-cell convergence was
spotted by me, not by either executor, and I called it *"the strongest available evidence"* while
marking it not-adjudicated. It was in fact **evidence for nothing** — two unrelated causes landing on
the same four cells. The not-adjudicated discipline is what kept it from being written into the
register as a finding. **That discipline earned its keep here.**

### OPEN-15 / OPEN-16 / OPEN-17 — The imputation tiers that are built and switched off ✅ **assembled — and one of the three is not what this register says it is**
- **Phase E** — documented-deferred, never executed.
- **`ml` tier** — built, verified EUI-neutral and not harmful, permanently off.
- ~~**Draw tier** — 6 variance-preserving imputers built opt-in/OFF~~ **— see the correction below;
  the imputers exist but the tier does not.** The CP-DRAW leaderboard found **no method dominates on
  every axis**, and the promotion decision was never taken.

**Amended 2026-08-06 (N10).** Decision brief: `extra/MEASUREMENT_open-15-16-17_imputation-decision.md`.
Switch state of each tier at HEAD, **director-verified by independent grep and `git log -S`**:

| Tier | Recorded state | Actual state at HEAD |
|---|---|---|
| Phase E (OPEN-15) | deferred | **no code path exists at all** — documentation only |
| `ml` (OPEN-16) | "permanently off" | wired (`imputation.py:543,685,881-886`) but **absent from default `IMPUTE_ENABLED_TIERS`** (`config.py:100`); reachable only through the standalone `impute_missing()` validation entry point, **never through the production `enrich_semantics` pipeline** |
| `draw` (OPEN-17) | "built opt-in/OFF" | 🔴 **not opt-in — unreachable.** `_CANONICAL_TIER_ORDER` is `("fusion","spatial","ml","statistical")` (`imputation.py:543`) — **no `"draw"`.** `config.py` contains **no** `IMPUTE_DRAW_METHOD_BY_TARGET` (zero `DRAW` matches). |

**🔴 The correction that matters: "opt-in/OFF" implies a switch. There is no switch.** The six draw
methods are real and committed (`openubem/semantic/draw_methods.py`) and were genuinely benchmarked —
but their only consumer is the leaderboard (`openubem/results/draw_leaderboard.py:78`). **Nothing in
the imputation router can reach them.** So OPEN-17 as written asks the user to rule on promoting a
tier that would first have to be built. **The decision is real; its stated cost was wrong.**

**How this was pinned down, since it contradicts a signed closure record:** `git log --all -S"_draw_tier"
-- openubem/semantic/imputation.py` returns **nothing** — the hook has never existed in that file, in
any commit on any branch. See **OPEN-36**, which this opened.

> **Amended 2026-08-13 (director, at CP-1 of `PLAN_two-measurements-2026-08-13.md`). Two facts added;
> the item's posture is unchanged.**
>
> **(a) There is a second orphaned consumer, not one.** Alongside
> `openubem/results/draw_leaderboard.py`, **`openubem/results/impute_scatter.py:235`** also reaches
> for the tier. Neither module is imported by anything in the repository — `git grep` for both names
> outside `docs/` and `openubem/outputs/` returns only the two files themselves.
>
> **(b) Both would crash on first use, not degrade.** They read the missing setting **unguarded** —
> `dict(config.IMPUTE_DRAW_METHOD_BY_TARGET)` at `draw_leaderboard.py:174` and `impute_scatter.py:235`,
> a bare attribute access with no `getattr` default — against a `config.py` that has never defined it.
> **Any invocation raises `AttributeError` immediately.** Nothing calls them today, so no published
> number is exposed and this is **latent, not live**; it is recorded here so that a future attempt to
> re-run the CP-DRAW leaderboard is not mistaken for a new defect.
>
> **(c) The cost of the un-built tier is now measurable in the test suite:** 9 nodes in
> `tests/test_draw_methods.py` fail for exactly this reason at HEAD. See **OPEN-44**'s 2026-08-13
> amendment. 🔴 **Those 9 are the standing evidence that this tier is unfinished — they should not be
> skipped or deleted to green the suite.**

**CP-DRAW leaderboard, as it really is** (`openubem/outputs/draw_leaderboard_results.json`, 3,285
lines): **20 pooled data rows + 1 joint-bonus summary row.** Continuous columns: `mae, rmse, ks_stat,
wasserstein, n, variance_ratio, iqr_ratio, energy_distance, variance_ratio_ci90, nmbe_proxy_pct,
do_no_harm_mae_pass, eligible_primary, priority_rank`. Categorical columns: `pfc, log_loss, n, tv,
do_no_harm_pfc_pass`. A `per_cell` block for 12 cities exists and was **not** tabulated.

**The zero-fitted-parameters question could not be settled from any document, and that is the finding.**
The arc's own operative definition is *"never tuned against EUI"* — **narrower than a plain reading of
"no fitted parameters anywhere."** Under the narrow reading neither tier touches the guarantee; under
the plain reading the `ml` tier's fitted regressors would. **Which reading governs is written down
nowhere.** That is a prior question to the promotion decision, and it is the user's.

These are one decision, not three: **does this project want a non-deterministic input tier at all?**
Recorded in memory alongside a hard-won constraint — NMBE is blind to variance collapse and must never
be used alone as an imputation-accuracy metric (measured variance ratios 0.06–0.31).

---

## 6. Theme E — Method and validation questions

### OPEN-18 — Q3, the √S vertical-form distortion ✅
**The largest open modeling problem in the project.** `scale_baseline_idf()` scales vertices in plan by
√S while preserving height, so a 79 m² building becomes a 4-storey prototype shrunk to 2.5% of its
area with all 27 zones and an extreme surface-to-volume ratio. Isolating one cell to remove the
climate confound: `layout_assign` heating is **~2× `auto` at every building size** — a *stable* ratio,
i.e. geometry, not an unscaled-quantity defect. Median S for `MidriseApartment` is 0.054; 67% of rows
are under 500 m².

**New as of 2026-08-04, and it narrows the search:** the storey-matching arc built the
`Zone.Multiplier` mechanism that the base plan named as Q3's "obvious first candidate", and it is now
**confirmed structurally unable to close it** — twice over. It expresses only `n_real > n_proto`
(taller) while Q3's population is the shorter case; and it changes simulated load, not rendered
geometry, so it could not address a vertical-form defect even if extended. A candidate has been
eliminated with evidence, which is progress.

**What remains open:** a mechanism that actually removes zones, or archetype re-selection by height
(which would relocate Q3 from a Stage-3 geometry defect to a Stage-2 assignment defect). Both are
materially larger than anything closed so far. **Neither has been scoped, and this document does not
scope them.**

### OPEN-19 — Why does LA run ~+40% hot? 📄
Established as **not** the zoning defect (a zoning fix moved it −0.6%), so it is a real
climate/HVAC-response problem. The named hypothesis — California Title 24 vs our ASHRAE 90.1
archetypes: envelope U-values, infiltration, HVAC COP and economizers for cooling-dominated CZ 3B —
has **never been researched**, and was explicitly gated on a user go/no-go for a calibration phase.

**Note the tension with a standing project rule:** the current baseline carries a **zero-fitted-
parameters** guarantee. A "calibration phase" must be defined carefully or it breaks that guarantee.
That definitional question is the first thing an execution plan would have to settle.

**Amended 2026-08-06 (N12). The hypothesis is not currently representable, and the reason is
one line.** Report: `extra/MEASUREMENT_open-19_la-standard-basis.md`.

**There is no climate-zone or code-year switch anywhere in the codebase.** N12 searched `openubem/`
and `scripts/` for Title 24 / CEC / CALGreen and found **zero hits**; **director-verified 2026-08-06**
by independent grep — also zero. Every archetype in every city is built from the single bundled
**ASHRAE 90.1-2019** table, and no script ever passes a non-default `construction_table`.

**What LA is actually simulated with** (dominant archetype `MidriseApartment`, nominal CZ 3B):

| Parameter | Value | Where |
|---|---|---|
| Wall U | 0.437 W/m²K | `openubem/data/construction/ashrae_90_1_2019.json` via `construction_sets.py:71,90-97` |
| Roof U | 0.221 W/m²K | same |
| Window U / SHGC | 2.385 / 0.25 | same |
| Infiltration | **0.000285 m³/s·m² — identical in every climate zone and all 20 real archetypes** | same; `PROVENANCE.md:46-54` |
| Cooling COP / heating eff. | 4.323 / 0.84 (Gas) | `openubem/data/loads/hvac_cop_by_archetype.json` → `idf/hvac.py:230-231` |
| Economizer | **hardcoded `DifferentialDryBulb`** at six call sites | `openubem/idf/hvac.py:248,288,332,386,532,567` |

🔴 **The source prototype for LA's HVAC is `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` — a
Buffalo, New York prototype (ASHRAE zone 6A) applied unchanged to a cooling-dominated California
cell.** Every one of the four mechanisms the hypothesis names is therefore **pinned to a cold-climate
national baseline**, and infiltration is not merely un-tuned but *constant across the entire fleet*.

**One piece of dead data worth knowing about.** `economizer_db_limit_c` **does** carry per-climate-zone
ASHRAE dry-bulb limits (3B = 23.9 °C). **It is never read** — `hvac.py` always emits differential
dry-bulb control. So the project already contains the *shape* of climate-zone awareness, wired to
nothing.

**The +40% and −0.6% figures are carried, not verified.** Both trace to
`docs/docs_VALIDATION/step1/overAll/V19_phaseC_rescore.md:34,45`, and the register's "~+40%" is its own
rounding of that document's **38.8%**. Re-deriving them means reproducing a 12-cell / 8,156-building
aggregation — **not a cheap re-derivation, and deliberately not attempted.**

**What this does to the item.** The named hypothesis cannot be *tested* without new data (a Title 24
construction/HVAC table), so **"research Title 24" is not the first task — acquiring or authoring an
alternative table is.** And the zero-fitted-parameters tension resolves more cleanly than expected:
swapping one published standard's table for another published standard's table is **not fitting**.
Fitting would be tuning those values to match measured LA consumption. **The two are different
actions, and only the second breaks the guarantee.** *(Stated by the director as a distinction, not as
a recommendation — the go/no-go remains the user's.)*

### OPEN-20 — Wider validation matrix 📄
Backlog since 2026-06-17. Extend beyond 3 cities × 4 urban-form rings. Blocks nothing; bounds how far
any result can be generalised.

### ~~OPEN-21~~ — Mixed-use classification key — **DEFERRED by the user, 2026-08-05**

**Ruling, verbatim in intent:** this is an important question the project has never actually decided;
**for now we progress with one function per building and the current behaviour stands.** Recorded as a
future task, not a live item. **The question is closed to further asking — do not put it to the user
again.** A future arc opens it deliberately from its own document.

Moved to **`docs/docs_TODO/mixed_use_classification.md`**, which carries the full record: the
verified current behaviour, the four questions a future arc must settle, and the first measurement
required before any plan.

**One fact was established before deferral and belongs in the register** (verified at HEAD 2026-08-05,
`openubem/semantic/building_classifier.py:110-113`, `:307`, `:324-325`, `:352`): a building is called
`mixed` only when its two tags disagree, which hard-codes its dominance score to `0.5`; rule 15
requires `>= 0.60`; so rule 15 is unreachable and **every mixed-use building in the project is
currently simulated as a `MidriseApartment` at MEDIUM confidence.** That is the status quo the ruling
preserves. It is undocumented in any output. **How many fleet buildings this affects is unmeasured** —
that count is the deferred item's first measurement.

**ID OPEN-21 is retired and must not be reused.** Deferred, not closed and not excluded: unlike
OPEN-23 this is a direction the project may still take, it is simply not being taken now.

### OPEN-22 — "Which exam does the answer key grade" ✅ **CLOSED 2026-08-13**

> ✅ **CLOSED 2026-08-13 — the exam was rebuilt, and it is now gated.**
> The last step ran under `PLAN_open22-tagrich-gate-2026-08-13.md` (T01–T02, **CP-1 signed 2026-08-13**),
> executing the user's ruling `2a`: **keep `test_fine_top1`'s `>= 0.70` on the old 50-row fixture exactly
> as it is, and add a separate gated test on the tag-rich fixture at `>= 0.80`.**
> `tests/test_building_classifier.py` now carries `TestTagRichTop1Accuracy`, measuring
> **fine top-1 = 88.8% on 98 graded rows** (100 data rows − 2 `UNDETERMINED`) — **8.8 points of headroom
> over the gate.** Director re-derived it two independent ways, agreeing to four decimals: the pytest
> gate and `scripts/analysis/open22_grade_tagrich_fixture.py` (87/98 = 88.8%), with the grader's own
> precondition — the old fixture still scoring 44/50 = 88.0% — reproducing first. **Non-vacuity was
> proved by hand**: raising the threshold to 0.95 made the test fail, confirming the assertion is
> actually reached rather than skipped.
> **The question the item was opened to ask is answered:** the answer key now grades **what the tags
> say**, labelled from source tag evidence by a builder that never imports the classifier, with
> size-guessing down from **34.0% (17/50) to 3.1% (3/98)**.
>
> 🔴 **Three constraints survive this closure and are binding on everyone downstream:**
> 1. **Every accuracy figure must name its fixture.** There are now **two exams with two thresholds**;
>    a bare percentage is not a meaningful number in this project. `92.0%` remains **unreproducible** and
>    quotable as history only, never as a comparison.
> 2. **CP-M3 now spans both exams** — no classifier change is adopted without before/after on each.
> 3. **Neither fixture is ever edited or deleted.** `labelled_archetypes_50.csv` is frozen byte-for-byte
>    (a retired item's bisect depends on it); `labelled_archetypes_tagrich_v2.csv` is the graded exam and
>    is equally frozen. **A failing gate is a finding, not a fixture to adjust.**
>
> ⚠️ **One finding this closure produced that nobody asked for, and it points at OPEN-47.** Coarse
> accuracy on the tag-rich fixture is **98/98 = 100.0%** while fine is 88.8% — meaning **all 11 errors
> are within the correct coarse class.** The classifier never confuses an office with a warehouse; it
> chooses the wrong office. Two riders: this is **an argument against adding a coarse gate here** (any
> plausible threshold would be trivially met and detect nothing), and the provenance of the fixture's
> `expected_coarse_class` column is **unverified**, so treat the 100% as suggestive rather than measured.
> Whether the 11 errors are one systematic confusion or eleven scattered ones is **not known** — that is
> the obvious next measurement, and it belongs to OPEN-47.
>
> **This gate is now the instrument that will detect OPEN-47's office-bin work moving the number**, in
> either direction. It was built first, deliberately.
> Full evidence: `docs/docs_ACTIVE/openings/extra/FIX_open-22_tagrich-gate.md`.

From the June audit, parked awaiting a ruling, still parked. Whether the label review grades *what the
tags say* or *what the building really is*. Until this is settled, **the accuracy metric itself is
undefined** — which is worth reading alongside OPEN-04's unexplained 4-point drift in that same metric.

**Status 2026-08-05 — the item's stated premise is FALSE at HEAD. ✅ verified.**

Put to the user this session. The June finding (`INVESTIGATION_steps-1-3-audit.md:99-103`, W2.8) rests
on two claims about classifier behaviour. **Both were checked against
`openubem/semantic/building_classifier.py` at HEAD and both are stale** — the R3-era coverage work
(`E-R3-1`, `E-R3-2`) changed the code underneath the audit without the audit being revisited:

| W2.8 claim (2026-06-09) | Status at HEAD 2026-08-05 |
|---|---|
| "19/50 rows are generic `building=yes` … the classifier will correctly emit `OpenUBEMUnknown`" | **FALSE.** Rule 17a (`:327-329`, tagged `E-R3-2`) routes `use_class == "unknown" and building_tag == "yes"` to `_office_size_tier(...)` — a **size-bucketed office**, at LOW confidence (`:356-357`). `OpenUBEMUnknown` (`:331-332`) is now reached only when there is **no** usable building tag at all. |
| "office tiers were suggested using *total floor area* while DESIGN §3C uses *footprint only*" | **FALSE / inverted.** `:186-187`, tagged `E-R3-1`, states *"office size metric is total floor area (footprint × levels)"* and computes `total_floor_area_m2 = footprint_area_m2 × max(levels, 1)`. Both office paths (`:296`, `:329`) use it. **The code now uses the same metric the human labels used.** |

**What this does to the item.** The conflict as recorded is largely dissolved — the classifier now
produces office archetypes for exactly the rows the labellers called offices, by the same size metric.
**But the philosophical question is not dissolved, it has moved**, and is arguably sharper:

> Rule 17a means that when the map data says only *"this is a building"*, the project **guesses
> office, bucketed by size**. If the human answer key also guessed office for those rows, then the
> labelled-accuracy metric is scoring **agreement between two guesses**, not correctness. A metric
> that rises when the fallback and the answer key are tuned toward each other is not measuring the
> classifier.

**Revised first measurement — do this before any ruling.** Run the current classifier over the 50-row
labelled fixture and produce the confusion detail: for each row, the label, the emitted archetype, the
rule token that fired (`RULE_*` vs `FALLBACK_SIZE_DEFAULT` vs `FALLBACK_UNKNOWN`), and the confidence
tier. Then report **what the accuracy number is once rows decided by `FALLBACK_SIZE_DEFAULT` are
excluded.** That single split — earned matches vs fallback-agreement matches — is what the user needs
to rule with, and it does not exist today. Measurement only; no relabelling inside it.

**Connects to OPEN-04.** OPEN-04's unexplained 92.0% → 88.0% drift is in this same metric, and its
suspected cause (Phase-D fusion/crosswalk, 2026-07-13) has never been confirmed. If a meaningful share
of the metric is fallback-agreement, then the drift may be a change in **tag coverage**, moving rows
across the rule-17a boundary, rather than a change in classifier logic at all. **That is a new,
unverified hypothesis, recorded here as a lead, not a finding.** The measurement above tests it for
free — it is the same run.

⚠️ **Also stale and NOT re-run:** the Boston 41.0% / Chicago 65.4% real-fixture distributions
(`INVESTIGATION_steps-1-3-audit.md:93`) predate `E-R3-2`. Rule 17a converts former FALLBACK rows into
LOW-confidence offices, so those two percentages **cannot be assumed to still hold** and must not be
carried into any plan.

This remains the cheapest item left in the register — but it is no longer "a decision, not an arc": it
needs one small measurement run first.

**Amended 2026-08-06 (N02). The measurement has been made. ✅** Report:
`extra/MEASUREMENT_open-22_fixture-rule-breakdown.md` +
`openubem/outputs/comparisons/open22_fixture_rule_breakdown.csv` (50 rows).
**Director-audited by independent re-derivation from the CSV — every number below reproduces.**

**The split the item asked for, and the answer is a surprise in the reassuring direction:**

| | n | fine top-1 |
|---|---|---|
| all fixture rows | 50 | **44/50 = 88.0%** |
| **excluding `FALLBACK_SIZE_DEFAULT` rows** | **33** | **29/33 = 87.9%** |
| the excluded rows alone | 17 | 15/17 = 88.2% |

**Removing the fallback rows does not move the number.** The fallback-decided rows score the same as
the earned ones, so **the metric is not being propped up by fallback-agreement.** The register's stated
worry — *"a metric that rises when the fallback and the answer key are tuned toward each other"* — is
**not what is happening**, and that is now measured rather than feared.

**What is true, and is the thing left to rule on:** **17 of 50 rows (34%) are decided by
`FALLBACK_SIZE_DEFAULT`, all at LOW confidence, and 16 of those 17 carry an office archetype in the
human answer key.** So a third of the exam is *the classifier guesses office bucketed by size, and the
labeller also said office*. The accuracy is not inflated by it — but the metric is measuring the
size-bucketing rule about as much as it measures the tag logic. **Whether that is the exam the project
wants is the user's ruling, and it is unchanged by this measurement.**

**Full rule-token distribution** (sums to 50; the three tokens with zero rows are stated as zero, not
omitted): `FALLBACK_SIZE_DEFAULT` 17, `RULE_USE_CLASS_SIZE` 14, `FALLBACK_UNKNOWN` 5, `RULE_HIGHRISE`
5, `RULE_FUNCTION_TAG` 4, `RULE_RESIDENTIAL_TIER` 2, `RULE_LODGING_TIER` 2, `RULE_USE_CLASS` 1,
`RULE_FUNCTION_TAG_SIZE` **0**, `MIXED_USE_DOMINANT_TAG` **0**.
Confidence × outcome: HIGH 7 match / 1 miss, MEDIUM 16 / 3, LOW 21 / 2.

**The connected OPEN-04 hypothesis is not resolved by this** and is not claimed to be. The lead
recorded above — that the 92.0% → 88.0% drift might be tag coverage moving rows across the rule-17a
boundary — would need the same breakdown computed at the reference commit to test. That was **not**
part of N02 and remains an unverified lead.

**The two stale figures were not used.** Boston 41.0% / Chicago 65.4% appear in the report only as
figures deliberately excluded.

**🔴 RULED 2026-08-12 by the user — OPTION C: REBUILD THE FIXTURE.** The question put was *"which exam
do you want"*, with the measured split stated in full (88.0% on 50 rows / 87.9% on the 33 tag-decided
rows / 88.2% on the 17 fallback-decided rows, i.e. **the fallback is not inflating the metric**). The
user did **not** take the two cheap options (keep the exam; report both numbers). **The ruling is that
the current 50-row fixture is the wrong exam**, because a third of it is decided by the size-bucketing
rule (`FALLBACK_SIZE_DEFAULT`, 17 of 50, all LOW confidence, 16 of 17 carrying an office label in the
answer key) rather than by tag logic. A new fixture is to be built whose rows are tag-rich enough that
the size-bucket path decides far fewer of them.

🔴 **The three consequences that were stated before the ruling and now bind:**

1. **Every historical accuracy number becomes non-comparable to the new one** — 92.0% (`7635ce2`),
   84.0% (`67ede73`), 88.0% (`0df422e`→HEAD). **OPEN-04's drift is defined on the OLD fixture and must
   stay defined on it**; it cannot be re-measured against the new exam. Any report quoting an accuracy
   figure after this lands must state **which fixture** it came from — the same rule OPEN-28 created
   for harvest generations, now applying to exams.
2. **The old fixture must not be deleted or edited.** It is the only artifact against which the
   existing published numbers, and the OPEN-04 bisect, can be re-derived. The new fixture is an
   **addition**, not a replacement of the file on disk.
3. **The pass gate (`test_fine_top1` ≥ 0.70) is defined against the old fixture.** Repointing the gate
   at a new fixture changes what the gate means and its threshold is not transferable — that is a
   second decision, not a consequence of this one.

⚠️ **This ruling does not close OPEN-22.** It converts the item from *decision owed* to *work owed*.
**The measurement rule (§6) is satisfied** — OPEN-22's first measurement was made 2026-08-06 (N02) —
so an execution plan may now be written. **What is NOT yet decided and blocks that plan: who produces
the new labels, and how many rows.** The current fixture's labels are human-authored; nothing in this
project can generate a ground-truth label. Recorded as the next question owed to the user.

---

### OPEN-47 — The office size-tier thresholds have no traceable external source, and our own research document contains a fabricated citation 🔴 **OPENED 2026-08-12**

> ⚠️ **Amended 2026-08-12 (night, T06–T07 of `PLAN_three-new-items-2026-08-12.md`). The first half of
> the title is now wrong: a source WAS found. The item stays open for other reasons.**
>
> ✅ **The thresholds trace to Chen, Hong & Piette (2017), *Applied Energy* 205, 323–335, Table 1**
> (DOI `10.1016/j.apenergy.2017.07.128`). **Director-verified from the PDF itself, not from the
> executor's report** — this task's predecessor fabricated exactly this kind of claim, so the check was
> redone from scratch: pages 19–20 carry `Small office (<2322 m2 and <= 3 floors)`,
> `Medium office* (2322 to 9290 m2, <= 5 floors)`, `Large office (>9290 m2 or >=6 Floors)` verbatim,
> and the DOI Crossref-resolves to exactly that paper. **Hong et al. (2015), credited by both the code
> comment and `RESULT_I02`, contains zero occurrences of either number** — director-verified, 13 pages
> searched.
>
> ⚠️ **Caveat that must travel with the finding:** the Chen 2017 table is **CityBES's own case-study
> classification, not a citation to an external standard.** It is a real, verified, definitional source
> for CityBES — it is **not** evidence of a DOE / PNNL / ASHRAE / CBECS lineage. CBECS 2018 does carry
> 25,000 / 100,000 ft² bin edges, but as general all-building bins: a numeric coincidence, not an
> office-specific source. ASHRAE 90.1 **could not be retrieved** (paywalled) and is recorded as a
> **retrieval failure, not** as "not found."
>
> 🔴 **Reason 1 it stays open — a substantive divergence from the source now that the source is known.
> The source's rule is area AND floor count** (`<2322 m² and ≤3 floors`, `2322–9290 m² and ≤5 floors`,
> `>9290 m² or ≥6 floors`). **`openubem/semantic/building_classifier.py:175-177` tests area only; the
> floor-count condition was dropped.** Not adjudicated. Any change here is gated by CP-M3 (OPEN-31):
> before/after accuracy on the labelled fixture, both numbers recorded.
>
> 🔴 **Reason 2 — the citation audit found more than the one known fabrication.** A **second fabricated
> DOI**, previously unflagged: Sun et al. 2021 given as `10.1016/j.enbuild.2020.110586` —
> **director-Crossref-checked: HTTP 404, it does not resolve at all**; the real DOI is
> `10.1016/j.enbuild.2020.110603` (*Prototype energy models for data centers*, Energy and Buildings
> 231), content otherwise correctly transcribed. A **systemic wrong-locator pattern**: every Table-1
> row sourced to Deru et al. (2011) cites "Section 3.x.x, Table 3-1, p.9", **a table that does not
> exist in that report** (real structure: flat sections 1.0–8.0, Tables 1–42; the data is Table 13,
> p.19, and the numbers are correct). PNNL-23269's HighriseApartment content is **not in that document
> at all**. Two further references have dead links.
>
> ✅ **Discharged legs.** The erratum is appended to
> `docs_DONE/BUGS/input-framework/deepResearch/RESULT_I02_archetype_classification_cascade.md` —
> director-verified **64 insertions, 0 deletions**, nothing rewritten. The code comment at
> `building_classifier.py` (now `:159`; the plan's `:143` had drifted, and the executor anchored on the
> constant names and said so) now names the real source and flags it as a case-study table —
> director-verified **comment-only**, with `_OFFICE_SMALL_MAX_M2 = 2322.0` and
> `_OFFICE_MEDIUM_MAX_M2 = 9290.0` unchanged. Reports:
> `extra/RESEARCH_open-47_threshold-provenance.md`, `extra/FIX_open-47_citation-erratum.md`.


**How it was found.** The user asked (2026-08-12) for deep literature research to validate the archetype mapping externally. T04 ran it. **The director audited the report and its headline claim failed.**

**What T04 claimed and what the audit found.** T04 reported that the numbers **2 322 / 9 290 m²** appear in Figure 2 of Chen, Hong & Piette (2017), *City-Scale Building Retrofit Analysis: A Case Study using CityBES*, IBPSA BS2017, and transcribed a legend from it. **The director downloaded the same PDF (8 pages, 21,520 characters of extractable text) and searched it: the strings `2322`, `2,322`, `9290`, `9,290`, `25,000`, `100,000` and `Large Office` appear ZERO times in the paper.** Figure 2 is a raster screenshot captioned only "Screenshot of CityBES", on p. 261, not p. 260. **The transcription was not read from that figure.** Worse, the identical scheme — same numbers, same stories qualifiers — already sits in this project's own `RESULT_I02_archetype_classification_cascade.md:33`, so the "external verification" reproduced the internal document it was sent to check. **That is the exact circularity the task existed to break.**

🔴 **Consequence: the two thresholds that decide a third of the labelled exam remain UNTRACED to any external primary source.** What is genuinely established is only that they are exact conversions of **25,000 / 100,000 ft²**, which are long-standing CBECS survey bin edges used for sampling across all building types — a plausible *numeric* donor, but CBECS does not split "Office" by floor area at all, so it is not a *definitional* one.

**What DID survive the audit, independently re-verified by the director:**
- The code comment at `openubem/semantic/building_classifier.py:143` reads `# E-R3-3: office size-tier bins (LBNL CBES 25,000 / 100,000 ft²; Hong et al. 2015)`. **It names the wrong tool** — `RESULT_I02` itself says CityBES.
- Verbatim from the 2017 PDF: *"Currently, CBES supports analysis of small and medium-sized office and retail buildings"* and *"other building types (e.g., large offices, hotels, hospitals) that are currently not supported by CBES."* **CBES cannot be the origin of a Large-Office tier.** That argument stands on its own.
- 25,000 × 0.09290304 = 2,322.576; 100,000 × 0.09290304 = 9,290.304.

🔴 **A separate and arguably worse finding: `RESULT_I02_archetype_classification_cascade.md:113` carries a fabricated citation.** It cites *"Hong, T., et al. (2015)… Energy and Buildings, 100, 290-302"* with DOI `10.1016/j.enbuild.2015.04.035`. **Crossref-verified by the director: that DOI resolves to a completely unrelated paper** — Padilla et al., *"A combined passive-active sensor fault detection and isolation approach for air handling units,"* Energy and Buildings **99**, 214–219. The real Hong paper is **Applied Energy 159, 298–309** (Crossref-confirmed). A wrong volume is a transcription slip; **a DOI pointing at an unrelated article is not.** `RESULT_I02` is an AI-authored deep-research document from 2026-06-30 in our paper trail, and **it now has one demonstrated fabricated citation — which is a finding about that document as a whole, not only about this threshold.** Its other citations (Deru et al. 2011, PNNL-23269, Sun et al. 2021, CTBUH) are **unverified**, and the primary DOE sources could not be reached in that session.

✅ **Externally corroborated, and useful:** the OSM wiki defines `building=roof` as a structure "open at least at two sides" — canopies and carports, **not enclosed conditioned space.** This confirms the director's suspicion about the 70 `roof` rows in the OPEN-22 pool.

**What is NOT claimed:** that the thresholds are wrong. They place all three DOE office prototypes in the correct tiers, which is what E-R3-3 was adopted to restore. **The defect is provenance, not value.** Report, with the director's audit at its head: `extra/RESEARCH_open-22_archetype-mapping-literature.md`.

---

## 7. Theme F — June-audit remnants

### 7.0 — ~~OPEN-23~~ `layoutGenerator` — **EXCLUDED from this register by the user, 2026-08-04**

Room-level interior zoning for non-rectangular footprints (L/U/T/courtyard). DESIGN-buildout closed
2026-07-05; CP-3 met; Phase 5 reached a cluster pilot but CP-4 user sign-off was never reached because
the user wants a root-level engine redesign first.

**User decision, 2026-08-04: this is not an option we are continuing with, and it is excluded from the
register.** Recorded rather than deleted, per this document's own rule that removed items carry a
reason (§9, pattern 4). **The ID OPEN-23 is retired and must not be reused.**

This does not close the arc and does not delete anything — the engine's full record stays where it is,
under `docs/docs_TODO/layoutgenerator/`, and a future redesign could still revive it for the
room-level-fidelity use case that `layout_assign` does not address. It is simply **not open work**, so
it does not belong on a list of open work. Do not re-add it without a new instruction from the user.

### OPEN-24 to OPEN-27 — Remnants of the 2026-06-09 steps 1–3 audit ⚠️
That audit's remediation went green (265 passed), but four items were marked **⏳ STILL OPEN** and have
not been revisited in ~8 weeks. **All four are stale-risk and must be re-checked against current code
before being believed:**
- **OPEN-24** — ~~the LIVE_SMOKE gate (real 23.1 IDD + a real EnergyPlus design-day run) is still
  parked. It was called *"the recommended next remediation block"*. Given this project's recorded
  standing lesson that synthetic-green ≠ live-green, this is the most consequential of the four.~~
  **Falsified 2026-08-13 — the gate was never parked on this machine. See the T03 amendment below.**
- **OPEN-25** — the Modules 04/05/06 bridge, described in June as *"the next construction project,
  not a defect"*. Whether that is still true is itself unverified.
- **OPEN-26** — four manifest/provenance polish items, none load-bearing.
- **OPEN-27** — a DESIGN doc carries a wrong name; DESIGN docs are read-only here and generated in the
  user's external LLM, so **only the user can fix this at source.**

**Amended 2026-08-06 (N03). All four re-checked against HEAD. ✅** Report:
`extra/MEASUREMENT_open-24-27_june-remnants.md`. **Two of the four dissolve; two survive.**
Director-audited: OPEN-25's and OPEN-27's HEAD citations were opened and independently confirmed.

| Item | Verdict at HEAD | Evidence |
|---|---|---|
| **OPEN-24** | **partly superseded, not parked** | `tests/test_sim_integration.py:24-31` is a genuine live EnergyPlus-23.1 test whose skip is **environment-gated on the binary being present**, not disabled in code — *director-verified*. `config.py:16,32` points at the real 23.1 IDD, not eppy's bundled v8.0. The specific mechanism the June audit named (dropped `IdealLoadsAirSystem` fields) **no longer exists** — `openubem/idf/hvac.py:1-4` replaced it with `HVACTemplate`. |
| **OPEN-25** | 🔴 **FIXED — close it** | The bridge was built `2026-06-10`, **the day after the audit named it**. `openubem/semantic/__init__.py:273-433` + `construction_sets.py`/`loads.py`/`schedules.py` produce exactly the columns Step 3 needed; integration-tested at `tests/test_step3_orchestrator.py:155-212`; wired into production at `scripts/validation/v12_cell_pipeline.py:155-212` — **the script that produced the adopted fleet baseline.** The register carried this as open for eight weeks after it was done. |
| **OPEN-26** | ~~**1 of 4 fixed, 3 survive**~~ → **2026-08-12: 2 of 4 fixed, 2 survive and both are downgraded to "will not fix unless asked"** | Fixed 2026-08-06: the bbox fallback does reach the manifest — but via `generation_status` (`openubem/idf/builder.py:611-627`), **not** `data_quality_flag` as the item names it. **Fixed 2026-08-12 (T05 of the five-item sweep): the missing-EPW case is no longer silent.** `builder.py:210-212` had no `else`; a building whose EPW was empty or absent was simulated at the template's default `Site:Location`, which all four templates set to `PLACEHOLDER, 0.0, 0.0, 0.0, 0.0` — **latitude 0°, longitude 0°, the Gulf of Guinea** (director re-derived this from `commercial_base.idf`, `highrise_base.idf`, `residential_base.idf`, `specialized_base.idf`, line 33 of each; identical in all four). `builder.py:213-218` now raises `ValueError` naming the `osm_id`, the offending path and the placeholder coordinates. Raising is the file's own convention, not a new behaviour: both production call sites (`builder.py:644-658`, `681-688`) already wrap the build in `try/except Exception → _worker_exception_row`, so one building fails loudly and the fleet loop continues; `openubem/acquisition/__init__.py:122` already asserts `epw_path` is never null at Stage 1. Verified: `pytest tests/test_idf_builder.py tests/test_layout_assigner.py tests/test_step3_orchestrator.py` → **187 passed**, re-run by the director. Still open, both **re-grepped 2026-08-12 and both still true, both deliberately not fixed**: `compute_form_factor` (`openubem/geometry/footprint.py:66`) is called from nowhere in production, only from its own unit test — **dead code, no numerical effect**; `openubem/geometry/context.py:24` recomputes each neighbour's `minimum_rotated_rectangle` per row with no cache — **efficiency only, no numerical effect**. Neither can change a published number, so neither is worth the diff risk; they stay recorded rather than fixed. |
| **OPEN-27** | **still wrong; only the user can fix it** | *Director-verified at HEAD:* `openubem/data/openstudio_archetypes.json` contains **zero** occurrences of `MultifamilyHome`; its two Residential archetypes are `MidriseApartment` (`:100`) and `HighriseApartment` (`:107`). |

**🔴 OPEN-27 is more load-bearing than "a wrong name" suggests, and this was not known before.** The
wrong name sits in the **coarse-class mapping the labelled-accuracy metric is defined against** —
the DESIGN text pins *residential ⇔ 2 archetypes, MidriseApartment and MultifamilyHome*, and seals it
*"do not re-debate."* The archetype that actually exists is `HighriseApartment`. The **code** is
self-consistent (it reads `sector` from the JSON), so `test_coarse_top1` is unaffected and stays at
100% — **the defect is that the specification names an archetype the project does not have, in the
definition of a metric.** Read with OPEN-22.

**Paste-ready for the user's external tool** (the only action available, per §7 above):

> Document: `docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md`, line 529. Wrong name: `MultifamilyHome`. Correct name: `HighriseApartment`. Reason: `openubem/data/openstudio_archetypes.json:99-111` has no `MultifamilyHome` entry — the two Residential archetypes are `MidriseApartment` and `HighriseApartment`.

**A fifth ⏳ from the same audit** (`INVESTIGATION_steps-1-3-audit.md:62`, efficiency-only, *"worth a
small task before city-scale runs"*) is **still true at HEAD** — per-row `iterrows` explode at
`openubem/acquisition/osm_fetcher.py:374-388`, full-width frame carried through every cleaning step
until trimmed at `:101`. **Not added as an item** — the manager's call, recorded here so the next
session does not rediscover it. Note its own trigger condition has since passed: the 8,160-building
fleet run happened.

**One stale statement found in passing, recorded not fixed:** `tests/test_sim_integration.py`'s module
docstring claims Step-3 IDFs are *"all fatal"*, contradicted by
`docs/docs_REPORTS/REPORT_phaseE_final.md:74` (*8,160 of 8,160 succeeded*). ✅ **FIXED 2026-08-13** —
see the T03 amendment below.

---

### ✅ Amendment 2026-08-13 — **OPEN-24 CLOSED; OPEN-27 discharged as far as this repo can take it**

*From `implemenation/PLAN_five-more-items-2026-08-13.md`, tasks T02 and T03. Report for T03:
`extra/MEASUREMENT_open-24_live-gate.md`.*

#### OPEN-24 — ✅ **CLOSED. The gate is live, local, green, and needs no network.**

The eight-week-old belief that this gate was *"parked"* and *"the most consequential of the four"*
is **false at HEAD, and appears never to have been true on this machine.** It was not parked — it
was simply never run.

- **EnergyPlus 23.1.0-87ed9199d4 is installed locally.** The skip guard is environment-gated on the
  binary being present; it **did not fire**.
- **No test in the file needs the network**, so the standing "no live-network integration tests
  until §5.3" rule never applied to it.
- **Director-run, four times sequentially, alone:** `7 passed` at **66.38s / 65.99s / 66.57s /
  66.68s**. Green every time.

**🔴 The executor's run reported `1 failed, 6 passed in 12.67s`. It does not reproduce, and the
cause is a manager error, not an executor error.** `pyproject.toml:54` pins
`addopts = "--basetemp=.pytest_tmp"` — a **fixed, repo-relative** temp root. pytest clears that root
at session start, so **two concurrent pytest sessions delete each other's temporary directories.**
The director had dispatched three agents in parallel, all running pytest. That is what made the
`step3` directory vanish under `to_parquet` at `openubem/idf/builder.py:696-707` mid-run, and it
explains the 12.67s-vs-66s gap: the wall-time-dominant test never reached IDF generation. **Opened
as `OPEN-52`.** Every dispatch prompt since carries a no-concurrent-pytest rule.

**Stale docstring fixed at source.** `tests/test_sim_integration.py:1-16` claimed both (a) Step-3
IDFs are *"all fatal"* — contradicted by `REPORT_phaseE_final.md:74` (8,160/8,160 succeeded) — and
(b) that the cache/determinism tests use EnergyPlus-installation example IDFs. **(b) was also
false:** those tests use the repo-local fixture `tests/fixtures/sim/1zone_with_sql.idf`; only
`test_adversarial_timeout_gives_failed_timeout` uses an installation example
(`ASHRAE901_HotelSmall_STD2019_Denver.idf`). Both corrected, both director-verified independently.
Diff confined to the docstring; no code touched.

#### OPEN-27 — the name is still wrong in DESIGN, but the code is now **pinned against it**

The DESIGN defect is unchanged and remains **the user's to fix at source** (paste-ready text above).
What changed: the mapping is no longer merely *"self-consistent by luck"* — it is now **pinned by
regression test**. `tests/test_building_classifier.py::TestOpen27ArchetypeNameBinding` (3 tests,
added T02) asserts (1) every `_COARSE_CLASS_MAP` key exists in `openubem/data/openstudio_archetypes.json`,
(2) the residential set is exactly `{MidriseApartment, HighriseApartment}`, and (3) `MultifamilyHome`
is **absent**. All three passed first run. If anyone ever "fixes" the code to match the DESIGN text,
these fail. **Item stays open on the DESIGN edit alone.**

---

## 8. What is closed and must not be reopened by mistake

Recorded so that a future reader does not mistake a settled decision for an open one:

- **The post-Phase-E "Other" residual** is process + miscellaneous plug loads only. The STOP decision
  on it is **permanent**.
- **R04 is closed at option (a)** — `layout_assign` ships matching thermal-zone topology and plate
  geometry, **not** building height. OPEN-10 and OPEN-18 would each reopen a piece of this
  deliberately; neither should happen by drift.
- **`T_ENGAGE = 0.868 m` and `T_MASS_MAX = 0.35 m` are frozen** on direct measurement. A fleet failure
  reopens the fix plan, never the constants.
- **Any mass-preserving fix to the CTF-convergence defect is dead on arrival** — proven, not assumed.
- **E-LA-20 is fixed and verified** 150/150 on the real production path.
- **Q3's `Zone.Multiplier` candidate is eliminated** (OPEN-18). Q3 stays open; that *approach* does not.
- **`layout_assign` is adopted for zone/HVAC-topology studies and NOT certified for fleet-level EUI
  reporting.** That disposition is current as of 2026-08-04, not a legacy caveat.

---

## 9. Observations across the register

Four patterns are visible only when the items sit in one list, and each is itself worth a decision:

1. ~~**Four items (OPEN-01, 02, 03, 04) can make already-published numbers wrong.** Every other item
   makes the project *less complete*. That is a categorical difference, and it is not reflected in how
   these items have been prioritised historically.~~ **Resolved 2026-08-05: all four items that could
   make already-published numbers wrong have been measured.** Two are confirmed large and
   unremediated (OPEN-01, OPEN-03). One is confirmed cheap to fix and approved in principle (OPEN-02).
   One turned out not to be a metric defect at all (OPEN-04) and has been re-cast as a process defect
   (OPEN-31). Three new items were opened by the measurements themselves (OPEN-30, OPEN-31, OPEN-32) —
   the expected outcome of measuring rather than planning. ~~**Next free ID: OPEN-33.**~~
   **Extended 2026-08-06 (M06): the exposure is now bounded as well as measured.** The two large
   unremediated items (OPEN-01, OPEN-03) are confined to `layout_assign`, which **no adopted result
   uses** — confirmed structurally and across all 16,320 adopted rows. The published numbers this
   project stands on are outside their reach. One further item opened by that sweep (OPEN-33).
   **Next free ID: OPEN-34.**
2. **Two items (OPEN-08, OPEN-14) are reproducibility defects**, and they undercut the evidence for
   other items rather than standing alone. OPEN-08 in particular puts an unquantified confound under
   every cross-generation comparison this project has made.
3. **~~Two items~~ One item (OPEN-22) costs a decision, not an arc** — it leaves the accuracy metric
   undefined while OPEN-04 reports an unexplained drift *in that same metric*. Those two should be
   read together. *(OPEN-21 was the other; deferred 2026-08-05 — see §6.)*
4. ~~**The register found a duplicate on its first pass** (OPEN-05). The `E-LA-nn` space has not been
   swept for others.~~ **Resolved 2026-08-05:** the space *was* swept, and E-LA-21/E-LA-39 is the only
   duplicate — but the sweep incidentally exposed a different hygiene defect, **OPEN-29**: defects can
   be OPEN at their own defining line while absent from this register. The pattern to carry forward is
   therefore not "duplicates" but **"the register does not yet demonstrably contain everything open."**
5. **A shape has now repeated three times: the closing step nobody owns.** *(Added 2026-08-06.)*
   Ratifying a classifier change without a fixture before/after (**OPEN-31**). Archiving an arc without
   sweeping its citations (**OPEN-33**). Discarding the vintage token every harvest resolves
   (**OPEN-30**). None is a code defect; each is a step that is obviously right, that no role owns, and
   that surfaced weeks later inside an unrelated investigation. **Three instances is a pattern, not a
   coincidence** — and all three decisions are owed to the same person on the same question: what a
   change must carry before it counts as finished.

---

## 10. Next step

**This document ends here by design.** Execution plans are written per the project's normal workflow
— manager authors `PLAN_*.md`, fresh executors run it — **after** the user picks which item or bundle
to open, and after the "first measurement" named in that item has been made.

### OPEN-48 — The adopted baseline run cannot be reproduced from this repository 🔴 **OPENED 2026-08-12**

**Found by** auditing OPEN-46's reversal (T04/T05 of `PLAN_three-new-items-2026-08-12.md`), not by
running a task. Sixth consecutive pass in which this register grew that way.

**The finding, in one line.** The adopted `phaseE_elevrb` run was produced by code that is not in this
repository, and running the pipeline from the current tree would produce different numbers and a
missing column.

**Evidence, all director-derived.**

| Fact | Live tree today | Adopted run's own outputs |
|---|---|---|
| `assign_elevators` called from `builder.py` | **no** — `git log --all -S assign_elevators -- openubem/idf/builder.py` is empty; `hasattr(builder, 'assign_elevators')` is `False`; zero occurrences of "elevator" in the file | n/a |
| `elevators_eui_kwh_m2` in results | **absent** at HEAD | **present**, 3,561 of 8,160 rows non-zero, Σ = 12,508.8 kWh/m² |
| `gwp_elevators_kgco2_m2` | **absent** at HEAD | **present** |
| elevator meter in `outputs.py` | **absent** at HEAD (13 meters) | requested — the column could not exist otherwise |
| elevator equipment emitted by a live build | **zero objects**, all 10 elevator archetypes | 87 of 87 eligible buildings in `nyc_urban` carry non-zero elevator EUI |

Commit `ef19141` ("feat: add elevators, debias, fusion, and layout generator updates") added
`openubem/idf/elevators.py`, `openubem/data/loads/elevators_by_archetype.json`, `tests/test_elevators.py`,
`tests/test_parser_elevators.py` and two cluster scripts **live**, and added `builder.py`,
`outputs.py`, `parser.py` and `carbon.py` **only as archived copies under
`docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/`.** The live four were never modified. So the
working tree that produced the adopted run carried edits to all four that were never committed.

**Why this is the serious one.** ✅ **It is not a physics problem — the published `157.1 kWh/m²` is
correct and complete, elevators included.** It is a provenance problem: **the number cannot currently
be regenerated from version control.** Every downstream claim that rests on "re-run the pipeline and
you get this" is, as of today, unverifiable. T05 restored the *reporting* half (parser, outputs,
carbon, aggregator) and proved the restoration bit-identical on meter-absent inputs; **the load-wiring
half is deliberately not restored, because doing so changes what the model computes.**

**Magnitude if the load wiring is restored — a director estimate, explicitly labelled as an estimate.**
Elevator-eligible archetypes cover **1,939,129 m² of the 3,671,199 m² fleet floor area (52.8%)**; the
per-archetype intensities implied by `elevators_by_archetype.json` and a crude schedule weighting give
roughly **2.0 kWh/m² on eligible area, ≈1.05 kWh/m² fleet-wide** — under **1%** of the headline. **This
is an order-of-magnitude bound from the load table, not a simulated result. Do not quote it as one.**

**First measurement, if this is opened.** Reconstruct the four uncommitted diffs from the archived
copies, apply them to the live tree, rebuild the IDFs for one cell, and check whether the elevator EUI
column reproduces the adopted values for that cell. That either confirms the archived copies *are* the
lost code, or proves they are not — and the second answer is the more important one.

**The ruling this needs from the user.** Restore the load wiring (which changes the published number by
roughly 1 kWh/m² and requires a fleet re-run to be honest about it), or freeze the adopted run as a
historical artifact and document that it is not reproducible from HEAD. **Do not decide this in an
executor.**

> **Amendment 2026-08-13 — the ruling was given ("restore the wiring, re-run the fleet"), executed in
> full, and it answered this item's own question. The item nevertheless STAYS OPEN, and for a reason
> that is not bookkeeping.**
>
> **What is now settled.** The load wiring is restored and live, and the twelve-cell re-run
> (`open48_refleet`) regenerates the elevator column **exactly** — 3,561 non-zero rows, matching the
> adopted run cell by cell, 8,160 buildings, the same 6 known failures. ✅ **The repository reproduces
> elevator energy. The provenance gap this item was opened for is closed on that axis.**
>
> ⚠️ **Two things keep it open.** **(i)** The re-run's fleet figure is **159.2157 against the adopted
> **157.0552**, and the +2.16 is **not** elevators — it is OPEN-49's `wwr` re-randomisation, driven by
> input drift. So the adopted number is still not reproducible *end to end* from HEAD; only its
> elevator component is. **(ii)** Whether `159.2157` replaces the published `157.1` is an **owed
> ruling** — the director's recommendation is to keep `157.1`, because 159.2 is the same model run
> through a known defect rather than a better model. ~~**Until that ruling, no document may restate
> 159.2 as the fleet figure.**~~ ✅ **RULED 2026-08-13: KEEP `157.1`. `159.2157` is not adopted and is
> not the fleet figure — it lives on only as evidence inside OPEN-49. Point (ii) is therefore settled;
> point (i) is what keeps this item open, and it stays open until OPEN-49 is fixed and the fleet is
> re-run a third time.**
>
> 🔴 **The estimate written above was low, and saying so is the point.** This item predicted "roughly
> **1.05 kWh/m² fleet-wide**, under 1%" from the load table, explicitly labelled an estimate. The
> measured re-run moved **+2.16**. **The estimate was not wrong about elevators — elevators moved the
> fleet by essentially nothing, because they were already in the adopted run.** The whole +2.16 came
> from somewhere the estimate never modelled. **A load-table bound predicts the load it models, not
> the run.**

---

### OPEN-49 — One reclassified building re-randomises the windows of every unidentified building in its cell ⚠️ **MECHANISM FIXED 2026-08-17 — CLOSURE BLOCKED on the OPEN-48 re-run ruling 4 declined**

**Found by** the cause analysis of OPEN-48's fleet re-run (T04 of `PLAN_three-rulings-2026-08-12.md`,
§8), not by running a task that looked for it. **Seventh consecutive pass in which this register grew
that way.** Registered on the user's ruling of 2026-08-13.

**The finding, in one line.** For buildings the classifier cannot identify, the window-to-wall ratio is
drawn at random **as one vectorised block sized by the number of unidentified buildings, with bounds
taken from whichever archetypes happen to be present** — so **changing one building's classification
silently redraws the windows of every `OpenUBEMUnknown` building in the same cell.**

**Where it lives.** `openubem/semantic/__init__.py:229` (the block draw), seeded by one RNG per run at
`openubem/semantic/__init__.py:297`.

**Why it matters more than it sounds.** `wwr` sets window head and sill height, which sets solar gain.
Buildings nobody touched — not reclassified, not re-fetched, not edited — move by up to **±300 kWh/m²
individually**. **The pipeline is reproducible only while its inputs never move**, which is a stronger
and more damaging statement than "the elevator wiring was never committed."

**Evidence — measured on the twelve-cell re-run, not inferred.**

| Observable | Result |
|---|---|
| Cells whose `archetype_id` set changed | **4 of 12** — and **all four moved in EUI**: `nyc_centre` **+3.53**, `austin_centre` **+1.76**, `la_centre` **+1.60**, `la_urban` **+1.21** |
| Cells whose `archetype_id` set matched | **8 of 12** — and **all eight reproduced to ±0.07 or better** |
| Cells on the wrong side of that split | **0** |
| IDF diff, reproducing buildings | **6 lines**, and only the order of three `Output:Meter` names — cosmetic, no energy effect |
| IDF diff, moving buildings | **hundreds of lines of window-vertex Z-coordinates** |
| Fleet effect | pooled EUI **157.0552 → 159.2157 (+2.16, +1.4%)** |

**Both routes into the defect are confirmed by cohort counts.** `nyc_centre` gained exactly **4**
Unknown buildings (its four `Courthouse` → `OpenUBEMUnknown` moves), which both resizes the draw block
and changes the bounds — largest shift, +3.53. `austin_centre`, `la_centre` and `la_urban` kept the
**same** Unknown count but changed **which archetypes were present**, moving the bounds alone — smaller
shifts, +1.21 to +1.76.

🔴 **Nondeterminism is excluded, and at the stronger of the two stages.** A repeat run on unchanged
inputs (run-1's cached `01_buildings.gpkg` and EPW copied into a fresh work dir so step 1 loads the
cache instead of re-fetching OSM) produced **738 of 738 IDFs byte-identical by MD5, `DIFFERING = 0`**.
The results stage agrees independently: **37 of 738 rows differ at all, largest 0.00836 kWh/m², cell
EUI Δ = −2.8e-05**, confined to `cooling` and `fans` with `lighting` and `equipment` bit-identical —
EnergyPlus float noise on an identical IDF, four orders of magnitude below the +2.16. **The seeded
generator reproduces bit-for-bit. The adopted-vs-re-run gap is in the inputs.**

**What is NOT known, and must not be asserted.** ⚠️ **Why the classification drifted at all.** The
re-run fetched OSM fresh, the adopted run fetched earlier, and `Courthouse` → `OpenUBEMUnknown` is what
upstream tag removal would look like — **but the adopted run's input `01_buildings.gpkg` no longer
exists, so the two fetches cannot be diffed.** Leading hypothesis, not a measurement.

⚠️ **One honest residual the mechanism does not explain.** `la_rural` moved **+0.0657** with archetypes
identical and **zero** Unknown buildings, on 3 of 144 buildings. Too small to touch any conclusion here,
and **deliberately left unexplained rather than absorbed into the story.**

**First measurement: made — this section is it.** The mechanism is located in code, sized on the fleet,
and separated from nondeterminism at two independent stages.

**What a remedy would have to decide, none of it decided here.** Whether the draw is keyed per building
(a stable per-building seed) rather than per block; whether the bounds come from a fixed table rather
than from whichever archetypes are present; and whether fixing it obliges a **third** fleet run to
restate the headline. **A fix changes every unidentified building's windows and is therefore gated by
the same before/after discipline as any classifier change (OPEN-31).** ~~⚠️ **This item is registered,
not scheduled. No remedy is authorised and none should be started without a ruling.**~~

> ✅ **Superseded 2026-08-17 — a remedy was ruled and landed.** User ruling 2 of
> `PLAN_open-49-and-open-01-2026-08-13.md` (2026-08-13) authorised a remedy for the mechanism only: **a
> stable per-building seed, applied to all four PDE columns**, plus **fixed bounds** taken from
> `_get_cross_archetype_loads()` regardless of which archetypes are present in a cell (ruling 3).
> Ruling 4: fix, then a before/after on the twelve cells — **no third fleet run.** `157.1 kWh/m²`
> pooled stays published.
>
> **The fix, as landed (T02/T03 of the plan, completed 2026-08-17).**
> `openubem/semantic/__init__.py`: `_per_building_rng()` seeds each Unknown row's draw from
> `blake2b(osm_id.encode(), digest_size=8)` combined with `config.RANDOM_SEED` via `numpy`'s
> `SeedSequence` entropy mixing — not builtin `hash()`, which is per-process salted and would make runs
> irreproducible. The block-size route (Fact 1) is dissolved because each row draws independently of
> how many other rows exist. The `enrich_semantics` call site now passes
> `_get_cross_archetype_loads()` **unconditionally** for bounds/medians, dissolving the
> present-archetypes route (Fact 2). Both were required — a synthetic non-vacuity probe (T02) confirmed
> disabling either route alone reintroduces exactly that route's drift while leaving the other fixed.
>
> 🔴 **The widening this plan found and the register had not yet recorded (Fact 3).** The defect was
> registered as a `wwr`/window item because windows are where the ±300 kWh/m² was measured. **It is not
> window-specific.** `pde_cols` at `openubem/semantic/__init__.py:225` is four columns
> (`lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person`, `wwr`), and the four `scalar_cols`
> setpoints (`heating_setpoint_c`, `cooling_setpoint_c`, `heating_setback_c`, `cooling_setup_c`) take a
> `.median()` over the same present-archetypes table at `:234-235` — the identical defect, untested
> until now. **T03 measured all eight fields pre- and post-fix**: pre-T02, route 1 (block size) moved 2
> of 8 (the two PDE columns that read `n`; the setpoints and the size-invariant PDE columns were
> untouched by route 1 alone), route 2 (present-archetype bounds) moved **all eight** — max drift up to
> `equipment_w_m2` Δ=5240.36, setpoints Δ=1.4/1.4/1.35/1.35. Post-T02, **zero of eight** move on either
> route. No third route was found (T03's STOP condition was not triggered).
>
> **T04's before/after on the twelve cells** (`openubem/outputs/comparisons/open49_before_after_cells.csv`,
> `extra/MEASUREMENT_open-49_before-after.md`) measured old-code-vs-new-code at **fixed** classification
> across all 8,160 buildings, all twelve cells, zero skipped. **Result: the four OPEN-49-moving cells do
> not show a larger before/after delta than the eight reproducing cells** — almost every cell's Unknown
> buildings show `wwr` moving by >0.01, tracking Unknown-row count rather than moving/reproducing
> status. This does not contradict the mechanism finding above: T04 and OPEN-49's original measurement
> are **different axes** — T04 fixes classification and swaps code; OPEN-49 fixed code (the bug) and
> swapped classification (two real fetches). Both are valid; they answer different questions. **No EUI
> claim is made from T04** — only semantic-stage inputs were measured, EnergyPlus was not run.
>
> ⚠️ **Why this item does not close here.** Ruling 4 chose a twelve-cell input-level before/after over a
> third fleet run. **OPEN-48 still needs a fleet re-run to reproduce `157.1` end to end** with the fixed
> mechanism, and that re-run was the option ruling 4 explicitly declined. This item is **mechanism
> fixed, closure blocked on the re-run the user chose not to take** — not open on any remaining unknown
> mechanism, and not closed on a headline nobody re-derived.

---

### OPEN-50 — Running the test suite silently rewrites a checked-in fixture, and one such rewrite has already been committed ✅ **FIXED 2026-08-13 — one open action left, and it is the user's**

> ✅ **FIXED 2026-08-13 (T01 of `PLAN_five-items-2026-08-13.md`; CP-1 director-signed).** The
> `synthetic_30_gdf` session fixture in `tests/test_building_classifier.py` now writes its GeoPackage to
> pytest's own `tmp_path_factory` directory instead of to
> `tests/fixtures/synthetic_30_archetype_coverage.gpkg`. The GDF was always built in memory — the path
> existed only because GDAL's GPKG driver writes through a filename. **Rows, CRS, dtypes and layer name
> are unchanged; one line moved.**
>
> **Proved by measurement, not by report.** The fixture's SHA-256 (`4047FF05…FEA386`) and mtime
> (2026-08-13 21:02:16) were captured **before** a full suite run and re-read **after** it. The suite ran
> **24m06s** between the two readings and **neither byte nor timestamp moved.** The mechanism is dead.
>
> 🔴 **What is still owed, and only the user can do it.** The working copy **still shows the fixture as
> modified**, left there by a run made *before* the fix. `git restore` is forbidden to this session and to
> its executors — git is handled externally. **The user must discard
> `tests/fixtures/synthetic_30_archetype_coverage.gpkg` in the working copy**, or the exact churn this item
> was opened to stop gets committed one final time. ⚠️ **The already-committed rewrite in `6aeebb0` is not
> undone by this fix** and is not proposed for rewriting — it stays in history as a recorded artefact.

**How it was found.** Not by looking for it. At CP-1 of `PLAN_two-measurements-2026-08-13.md` the
director ran `git status` to check that the two executors had written only their authorised files —
the audit-by-re-derivation rule — and found a **fifth** modified path that neither executor claimed:
`tests/fixtures/synthetic_30_archetype_coverage.gpkg`. **Sixth item in this arc found by auditing an
output rather than by running a task that went looking.**

**Why it looked alarming and is not.** The file is a binary GeoPackage, same size on both sides
(**106,496 bytes**), with **11,400 bytes differing** — spread across the SQLite header, an ASCII-digit
run near offset 12271, and text-shifted regions near offset 62112. That byte pattern is
indistinguishable from content corruption by inspection.

🔵 **It is not corruption. Measured table by table, not eyeballed.** Every table was read from both
copies and its full row set hashed:

| check | result |
|---|---|
| Table list identical | **yes** |
| All feature/geometry/metadata tables byte-identical by row hash | **yes — every one** |
| Tables differing | **exactly 1 — `gpkg_contents`, which holds 1 row** |
| Fields differing within that row | **exactly 1 — `last_change`** (`2026-08-12T21:59:47.441Z` → `2026-08-13T21:54:55.338Z`) |
| Bounding box, `srs_id`, `table_name`, `identifier` | **unchanged** |

The 11,400 scattered bytes are SQLite header and b-tree page churn from rewriting that single row.
**No feature data changes. No test outcome depends on it.**

**Clean-room reproduction, isolated to a single file** (the earlier observation was confounded by two
executors running concurrently): the fixture was restored to `HEAD`, `git status` confirmed clean,
`pytest tests/test_building_classifier.py` was run — **131 passed, 1.86s** — and the fixture came back
**modified**, with the same single-field diff. **Cause: `tests/test_building_classifier.py` opens the
checked-in fixture read-write; GDAL/SQLite stamps `last_change` on open.** The stamp is the wall clock,
so **it differs on every run** — the two mutations observed carry different hashes.

🔴 **The part that is a real cost, not cosmetics: one of these rewrites has already been committed.**
`git show --stat 6aeebb0 -- tests/` lists
`tests/fixtures/synthetic_30_archetype_coverage.gpkg | Bin 106496 -> 106496 bytes` — the same
zero-net-size signature. **A test-run artifact entered the history as if it were a deliberate fixture
change.** That is the same class of harm as OPEN-36's unreliable completion records: the audit trail
says something was changed on purpose when nothing was.

**Standing consequence, effective now:** ⚠️ **a dirty
`tests/fixtures/synthetic_30_archetype_coverage.gpkg` after a test run is expected and means nothing —
it must not be read as evidence that an executor wrote outside its authorised set,** and it must not be
committed. **Any future audit that finds it dirty should verify by row hash, not by byte diff.**

**What a remedy would have to decide, none of it decided here:** whether the test opens a copy in a
`tmp_path` instead of the checked-in file (the obvious fix, and it touches shipped test code), or
whether the fixture is opened read-only. ⚠️ **This item is registered, not scheduled. No remedy is
authorised. It is deliberately not folded into OPEN-44** — that item is about which tests fail, and
this fixture's tests all pass.

**Evidence mark:** ✅ **mutation reproduced in isolation from a clean tree**; ✅ **scope proved to be
one metadata field by full row-hash comparison of every table**; ✅ **prior accidental commit
identified by name.**

**Bearing on the published number.** 🔴 **None, and lead with that.** `157.1 kWh/m²` is correct and
complete, elevator energy included. This defect explains why the **re-run** differs; it does not make
the published figure wrong. **Whether 159.2157 replaces it is an open ruling (see OPEN-48's 2026-08-13
amendment), and the recommendation is to keep 157.1 until this defect is fixed.**

---

### OPEN-51 — One defect ID, `E-LA-16`, is used for two different failure signatures 🔴 **OPENED 2026-08-13**
*Surfaced by T05 of `implemenation/PLAN_five-more-items-2026-08-13.md` while re-checking OPEN-29's
eight IDs. Reported, deliberately not adjudicated — resolving it was outside that task's scope.*

**What is wrong.** Two lineages travel under the same ID, and each source is internally consistent
with itself, so neither reads as an error from inside:

| Source | What it says `E-LA-16` is |
|---|---|
| `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:279` — **its own defining text** | cooling-coil-design-UA / cooling-tower-UA-autosize failure family |
| `implemenation/PLAN_compute-queue.md:343` (manager-verified fact, 2026-08-06) | one of C06's five inherited `CheckWarmupConvergence` "cosmetic" log entries (with E-LA-14/18/19/23) |
| `extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md:116` | same — warmup-convergence lineage |
| `openubem/geometry/layout_assigner.py:863-865` — **live code comment** | groups `CheckWarmupConvergence` with "E-LA-14/16/18/19/E-LA-06" |

**Why it matters more than a bookkeeping slip.** OPEN-09's C06 measured that the *"cosmetic"* label
is defensible for the `CheckWarmupConvergence` class on one population. If `E-LA-16` is **not** that
class, then C06's finding has been silently extended to a cooling-coil-UA defect it never tested —
and OPEN-29 currently carries `E-LA-16` under its cooling-coil citation while the code comment reads
it the other way. **One of the two readings is wrong and neither has been retired.**

**What would settle it.** Read the structural-fixes arc's original `.err` evidence for the run that
minted `E-LA-16` and see which signature it actually contains. Cheap, local, documentary — no
cluster, no simulation.

⚠️ **Registered, not scheduled. No remedy authorised.** Do not renumber or split the ID until the
question is answered; a premature split would create a third reading.

---

#### ✅ CLOSED 2026-08-18 — T02 of `implemenation/PLAN_five-items-2026-08-18.md`. Adjudicated on evidence; the code comment was wrong.

**Verdict: `E-LA-16` names the cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed
family** (`PLAN_structural-fixes_implementation.md:279`), **not** the `CheckWarmupConvergence` /
`CheckAirLoopFlowBalance` lineage the code comment grouped it with. The arc's own raw `.err` evidence
for the three named buildings is gone from this machine (searched exhaustively under
`docs/docs_DONE/SETUP/layoutAssigner/`); independent corroborating evidence was found instead — the
same three building IDs (`way/402036176`, `way/402036789`, `way/1395739331`) exist in the current
local E02 harvest (`la_urban_layout_assign` mode), and their raw `eplusout.err` files show **zero**
`CheckWarmupConvergence` hits, **zero** `CheckAirLoopFlowBalance` hits, and **23/21/16** Severes
respectively (corrected 2026-08-18 — see below), **all** `Calculation of cooling coil design UA
failed`. Graded documentary-plus-corroborating, not a byte-identical re-derivation (one discrepancy
reported, not smoothed over: this harvest shows 0 Fatal where the original text reported a
cooling-tower-UA-autosize Fatal for two of the three buildings — most likely a run-config difference,
not a mechanism difference).

🔴 **Correction, 2026-08-18 (same T06 pass that closes this item).** The measurement doc's original
Severe counts (26/24/19) were wrong: the `grep -ic "Severe"` used to produce them also matched each
`.err` file's three trailing `Error Summary` lines (which contain the word "Severe" as part of a
count, not as a `** Severe **` fault line). **True counts: 23/21/16**, matching each file's own final
`N Severe Errors` summary line exactly. The conclusion is unaffected — same signature, same zero
counts on the competing reading's markers.

**Code comment corrected** (`openubem/geometry/layout_assigner.py:865`, comment text only, no code
change) — `E-LA-16` removed from the `CheckWarmupConvergence` grouping, replaced with a pointer to the
measurement doc. The wrong grouping traces to a different commit (`69373f9e`, 4 days later) documenting
an unrelated 6-run experiment that never touched E-LA-16's own buildings — a documentation error, now
corrected.

**Knock-on effects, recorded here rather than left implicit:**
- **OPEN-09's C06** — its *"five inherited log entries"* list narrows to **four**: E-LA-14, E-LA-18,
  E-LA-19, E-LA-23. E-LA-16 does not belong to the `CheckWarmupConvergence` "cosmetic" class C06 tested,
  and E-LA-16's own accuracy impact remains untested. (Also written into OPEN-09's own section, below.)
- **OPEN-29** — no change. Both OPEN-29 measurement docs already used the defining-text reading and had
  already flagged this exact contradiction as unresolved
  (`extra/MEASUREMENT_open-29_eight-defect-recheck.md:71-82`); this item resolves the question they
  deliberately left open.

**Evidence:** `extra/MEASUREMENT_open-51_e-la-16-identity.md`. **ID retired.**

---

### OPEN-52 — A fixed `--basetemp` makes two concurrent pytest sessions delete each other's temp directories 🔴 **OPENED 2026-08-13**
*Found by the director during T03, diagnosing a test failure that would not reproduce.*

**The defect.** `pyproject.toml:51-58` sets:

```toml
[tool.pytest.ini_options]
tmp_path_retention_policy = "failed"
tmp_path_retention_count = 3
addopts = "--basetemp=.pytest_tmp"
```

`--basetemp` is **fixed and repo-relative**, not per-session. **pytest clears that root at session
start.** So a second pytest session started while a first is running deletes the first's `tmp_path`
directories out from under it. Failures land in whatever the running test happened to touch next —
which is why they look like unrelated logic bugs.

**Observed, not theorised.** T03's executor reported `1 failed, 6 passed in 12.67s` on
`tests/test_sim_integration.py`. Four sequential director runs of the same file gave **`7 passed` at
66.38s / 65.99s / 66.57s / 66.68s.** The failure was a vanished `step3` directory under `to_parquet`
at `openubem/idf/builder.py:696-707`. The director had dispatched **three agents in parallel, all
running pytest**. The 12.67s-vs-66s gap corroborates it: the wall-time-dominant test never reached
IDF generation before its scratch directory disappeared.

**🔴 This was a manager error, not an executor error, and it is recorded that way on purpose.** The
executor's report was accurate about what it saw. The director parallelised over a test configuration
that cannot support concurrent sessions.

**Immediate mitigation, already in force:** every dispatch prompt now forbids starting a pytest
session while another is running. **This is a discipline, not a fix — it depends on the director
remembering.**

**What a remedy would have to decide, none of it decided here:** whether to drop the fixed
`--basetemp` entirely (pytest's default per-session `pytest-of-<user>/pytest-<n>` roots are already
collision-free), or to make it unique per session. Dropping it also drops whatever the pinned path was
originally for — **that reason was not established**, and it must be before the line is removed.

⚠️ **Registered, not scheduled. No remedy authorised.** Anyone reading a non-reproducing test failure
in this repo should check this item **first**.

**Bearing on any published number.** 🔴 **None.** This corrupts test runs, never simulation output.

---

#### 🔴 STAYS OPEN 2026-08-18 — T01 of `implemenation/PLAN_five-items-2026-08-18.md`. The collision is reproduced and real; the specified remedy is blocked by a second, newly-found defect.

**Reason for the pin: still not established.** `git show fe05509 -- pyproject.toml` and its
same-day plan progress-log entry both list the `addopts` line as an artifact with no stated rationale.
No code, CI config, or fixture reads the literal `.pytest_tmp` path anywhere in the repo.

**(a) The original collision — reproduced.** The literal reproduction recipe (write a file, sleep
15s, assert it exists) did not surface a failure in two attempts, despite the directory census proving
the wipe fired both times. A busy-loop design (continuous writes, no sleep) did catch a hard failure:
session B got `FileExistsError: [WinError 183]` cascading from an `OSError [WinError 145] directory
not empty` inside pytest's own `rm_rf`. **Collision reproduced — real, same root cause as originally
diagnosed, different failure signature than the register's original incident.**

**(b) A second, newly-found defect blocks (a)'s specified remedy.** Deleting `addopts` (the specified
remedy — pytest's default per-session `pytest-of-<user>/pytest-<n>` root is collision-free) was
applied and tested. With `addopts` deleted and no other change, `tests/test_sim_integration.py` alone
gave **`1 passed, 6 errors`** (all `PermissionError [WinError 5]` on
`%LOCALAPPDATA%\Temp\pytest-of-o_iseri`, a directory dated Apr 1, predating this session, and
currently access-denied even to `icacls` run directly against it — an **OS-level lockout**, not a
pytest defect). With a `TEMP`-redirect workaround, two concurrent sessions passed cleanly into
separate `pytest-0`/`pytest-1` directories, proving the remedy is mechanically correct — but that
workaround is not available to a normal invocation on this machine. The fixed `.pytest_tmp` basetemp
was, without anyone recording it as the reason, **incidentally shielding every `tmp_path` test from
this unrelated OS lockout**. `pyproject.toml` was reverted to its original content; the remedy cannot
be safely applied as a bare line deletion on this machine.

⚠️ **OPEN-52 STAYS OPEN, with two sub-questions recorded rather than one closure:** (a) the
concurrent-pytest collision — reproduced and real, no remedy applied yet; (b) the
`pytest-of-o_iseri` OS-level lockout, which blocks (a)'s specified remedy. **Choosing between an ACL
repair on the lockout and a different remedy shape (e.g. a per-session unique basetemp instead of
deleting `addopts` outright) is a design/infrastructure decision outside an executor's authority — it
is recorded here as an owed ruling, not as a next measurement.** `pyproject.toml` is byte-identical to
its pre-task state; `.venv/Scripts/python.exe -m pytest tests/test_sim_integration.py` alone, repo
restored: **7 passed in 67.14s**, repeated **7 passed in 68.08s** — matching the register's four prior
sequential 60–70s runs.

**Evidence:** `extra/FIX_open-52_pytest-basetemp.md`.

---

### OPEN-53 — 874/875 E02 harvest directories are missing `.sql`/`.end`, concentrated in two Austin sub-cells 🔴 **OPENED 2026-08-18**
*Found by T03's `.eio` census (`implemenation/PLAN_five-items-2026-08-18.md`) while establishing
OPEN-37's closure — a byproduct of a census run for a different question, not a task that went
looking for this.*

**What was found.** `scripts/analysis/open37_eio_census.py`'s per-(cell, mode) census of the local E02
harvest, run to verify `.eio` coverage for OPEN-37, also counted `.sql` and `.end`. Against
**40,800 `n_building_dirs`** (exact) and **40,800 `.eio`/`.err`** (both exact, zero empty), `.sql`
comes in at **39,926** and `.end` at **39,925** — short by **874** and **875** respectively.

**Not OPEN-37's problem.** Every one of the short directories still carries its `.eio` and its `.err`
— the fetch that OPEN-37 was about worked. This is an **incomplete-simulation signature**: the run
started (produced `.err`) and, for `.eio`-bearing directories, got far enough to write geometry, but
did not reach a state that writes `.sql` (results database) or `.end` (the run's own
completion marker).

**Where it concentrates.** 874 of the 875-count gap sit in **`austin_suburban_fast_zone`** and
**`austin_suburban_floor`**; the remaining one directory is in **`nyc_centre_fast_zone`**.

**First measurement, not yet made:** whether these are genuine incomplete/failed EnergyPlus runs (read
their `.err` tails for a Fatal or a truncation), a harvest-timing artifact (fetched mid-run, before
`.sql`/`.end` were written), or something else. No `.err` content from these specific directories has
been read yet — this item is opened on the census count alone, per this task's scope.

⚠️ **Registered, not scheduled. No remedy authorised.**

**Evidence:** `openubem/outputs/comparisons/open37_eio_census.csv`;
`extra/MEASUREMENT_open-37_eio-fetch-closure.md` (where the gap was first reported, out of that
item's own scope).

---

Nothing in this register is scheduled. Nothing is assigned. No cluster time is committed.
