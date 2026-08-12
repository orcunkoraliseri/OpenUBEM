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

---

## 1. Summary — **31 tracked items** (OPEN-01 … OPEN-42; OPEN-23 excluded, OPEN-21 deferred, OPEN-05, OPEN-25, **OPEN-30, OPEN-34, OPEN-39, OPEN-40 and OPEN-41** closed — all nine IDs retired; **OPEN-02 and OPEN-28 folded into OPEN-01** on 2026-08-09 and **both discharged 2026-08-11**)

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
| OPEN-01 | EUI denominator wrong for non-`applied` buildings (E-LA-41) — **(a) and (b) answered 2026-08-11 on all 40,800 E02 runs; (c) cannot be proved from the artifacts that exist.** Per-mode median error factor: **`auto` 1.0000 (99.63% within ±1%)**, `floor` 1.0000 (98.43%), `fast_zone` 1.0000 (94.80%), `layout_assign` 0.9999 (**15.37%**), 🔴 **`building` 0.5000 (39.94%)**. `layout_assign` non-`applied` (n=6,939): median 0.9474, range 0.0557–10.0008, **2.05% within ±1%**. `applied` control holds at median 1.0000. Join 8,160 matched / 0 unmatched **in both directions in every mode**. | Reported numbers | 6,939 / 7,442 evaluated — **plus the whole `building` mode** | ✅ **measured on 40,800 runs, all five modes**; ❓ **(c) one-code-state unprovable — ruling owed** |
| ~~OPEN-02~~ | ~~No fleet-scale EUI has a simulation-verified denominator (`.eio` deleted)~~ | **DISCHARGED 2026-08-11** — a folded finding under OPEN-01 sharing its closure condition, the E02 fleet pass, which has now been made **and read**. **Every one of the five modes now has a simulation-verified denominator over all 8,160 buildings, parsed from 40,800 `.eio` files with 0 parse failures.** Evidence: `openubem/outputs/comparisons/e02_simulated_floor_area.csv`, `open01_denominator_audit.csv`. The finding it asserted — that no published fleet EUI had a verified denominator — was true when written and is no longer true. |
| OPEN-03 | `layout_assign` models all internal loads as 2022-code regardless of real vintage | Reported numbers | ~half of a −29% cross-mode gap | ✅ **measured** |
| OPEN-04 | Labelled-accuracy gate drifted 92.0% → 88.0%, root cause unconfirmed | Reported numbers | classifier-wide | ✅ **explained** |
| ~~OPEN-05~~ | ~~`has_fatal` dead column logged twice~~ | **CLOSED 2026-08-05** — full ID sweep run, no further duplicates. See §3. ID retired. |
| OPEN-06 | ~~Archetype labels wrong for 41 of 8,160 buildings~~ **the column does not describe what was simulated** (E-LA-38) | Simulation correctness → **provenance** | 41 buildings; 100% of failures; **every per-archetype grouping** | ✅ **source defect + provenance defect**; **N14/N16: `data_quality_flag` is unreproducible too; swept on all 12 cells (8,160) — population fully accounted for, no third column; 26 of 33 columns unreachable without CPU** |
| OPEN-07 | 3 buildings regressed success → failure (E-LA-40) — **all three were simulated as `SmallHotel`, not the `SmallOffice` the file records** | Simulation correctness | 3 / 8,160 | ✅ |
| OPEN-08 | Archetype/vintage not reproducible locally for data-poor buildings (E-LA-22) | Reproducibility | all cross-generation comparison | 📄 **partially quantified** |
| OPEN-09 | `thermal_mass=True` drives warmup non-convergence; "cosmetic" never tested (E-LA-23) | Simulation correctness | 64% vs 5.3% control | ✅ **C06: "cosmetic" tested and holds — 96.3% distribution overlap, small correctly-signed residual** (audited) |
| OPEN-10 | `ZoneGroup` list-multiplier edit would restore exact expressibility (E-LA-37) — **capability confirmed real from the schema; remedy narrower than claimed** | Capability | ~~90 buildings (**carried, not re-derivable without a fleet pass**)~~ **C03: 90 reproduces exactly — but that is 4.6% of the 1,976 inexpressible fleet-wide** + future | ✅ **measured + verified** |
| OPEN-11 | 6 inverted-geometry buildings need post-hoc remediation, not re-applied | Simulation correctness | 6 / 8,160 | ⚠️ |
| OPEN-12 | ~~Rural `height_m` residual — `nyc_rural` 36.4%, `austin_rural` 19.2%~~ **both re-derive at 100%; a third cell is at 100% and was never named**. **N15: genuinely a source-coverage gap — NOT a spillover from OPEN-14** | Data acquisition | **3 cells, 2,032 buildings; 2,806 / 8,160 fleet-wide** | ⚠️ **numbers do not reproduce** |
| OPEN-13 | E-UTCI-12 and E-UTCI-13, forwarded out of the UTCI arc — **read at last; both live at HEAD** | Data / Stage 6 | **the whole test suite cannot be collected**; every cached height re-read | ✅ **measured** |
| OPEN-14 | UTCI height backfill is not reproducible from a clean checkout — **confirmed; no Overture slice is tracked for any affected cell** | Reproducibility | Stage 6 inputs; ~~converges with OPEN-12 on the same 4 cells~~ **N15: coincidence — separate item** | ✅ **measured** |
| OPEN-15 | Imputation Phase E — documented-deferred, never executed — **no code path exists at all** | Imputation | fleet inputs | ✅ **measured** |
| OPEN-16 | `ml` imputation tier built but permanently off — **never reachable from the production pipeline, only from the validation entry point** | Imputation | opt-in only | ✅ **measured** |
| OPEN-17 | 6 variance-preserving draw-tier imputers built, ~~off, awaiting a promotion decision~~ — 🔴 **not "off": the tier is unreachable; its router hook has never existed in any commit** | Imputation | ~~opt-in only~~ **the decision's cost was understated** | ✅ **measured** |
| OPEN-18 | **Q3 — √S vertical-form distortion**, now confirmed unreachable by the mechanism built for it | Method | small buildings, cold cells | ✅ |
| OPEN-19 | LA runs ~+40% hot — Title 24 vs ASHRAE 90.1 — **not currently representable: no climate-zone or code-year switch exists; LA's HVAC comes from a Buffalo prototype** | Method | one whole city | ✅ **measured** |
| OPEN-20 | Wider validation matrix beyond 3 cities × 4 rings | Method | external validity | 📄 |
| ~~OPEN-21~~ | ~~Mixed-use classification key re-cut~~ | **DEFERRED to future by the user 2026-08-05** — one function per building stands; moved to `docs/docs_TODO/mixed_use_classification.md`. See §6. ID retired. |
| OPEN-22 | "Which exam does the answer key grade" — label-review basis undecided; **measurement made 2026-08-06, ruling still owed** | Decision owed | accuracy metric itself | ✅ **measured** |
| ~~OPEN-23~~ | ~~`layoutGenerator` production zone-mode~~ | **EXCLUDED by the user 2026-08-04** — see §7.0. ID retired, not reused. |
| OPEN-24 | ~~LIVE_SMOKE gate still parked~~ **partly superseded** — the live E+ test exists and is environment-gated, not parked | Test integrity | Stage 3 → 4 | ✅ **re-checked** |
| ~~OPEN-25~~ | ~~Modules 04/05/06 bridge~~ | **FIXED 2026-06-10, the day after it was named; confirmed at HEAD 2026-08-06. Closes.** See §7. | — | ✅ |
| OPEN-26 | Manifest/provenance polish items — **1 of 4 fixed, 3 survive** | Housekeeping | reporting only | ✅ **re-checked** |
| OPEN-27 | A DESIGN doc names an archetype that does not exist — **inside the coarse-metric definition**; fixable only at the external source | Housekeeping → **spec integrity** | the accuracy metric's own definition | ✅ **re-checked** |
| ~~OPEN-28~~ | ~~**Cross-mode comparisons mix two harvest generations**~~ | **DISCHARGED 2026-08-11** — the remedy it asked for is delivered: **E02 is all five modes on one generation**, so a cross-mode delta now means the method. The confound against the adopted 3rd-generation fixture is also **bounded rather than waved at**: `auto`'s `zoning_strategy` agrees with the adopted run at **100% in every cell** and its `archetype_id` at **96.5–100%**; the other four modes' zoning agreement is 7.6–52.5% **by design**, since those modes force a different zoning approach. 🔴 **Its rule survives the discharge and binds harder: every comparison must state which harvest generation each side came from — E02 is the fourth.** The separate question of what to do about the **already-published** confounded numbers is **CP-M2, an owed ruling**, not this item. |
| OPEN-29 | **Defects last recorded OPEN that this register never adopted** — **measured: 9 of 12 are genuinely still open**, now tracked inside this item | Register hygiene | 9 defects; E-LA-21 replicated across **4** harvest scripts | ✅ **measured** |
| ~~OPEN-30~~ | ~~Assigned vintage is never persisted by any harvest~~ | **CLOSED 2026-08-11** — demonstrated on 60/60 E02 manifests, 40,800 rows, 0 nulls, 5 distinct values, `DOERefPre1980` 93.44% vs the ≈92.9% expectation; `la_rural` cross-check vs raw `year_built` reproduces R07 with zero crossover in all five modes. Evidence: `openubem/outputs/comparisons/open30_vintage_distribution.csv`, `extra/MEASUREMENT_open-30-01c_vintage-and-code-state.md`. Director re-derived the full distribution independently. **ID retired.** |
| OPEN-31 | Ratified classification changes adopted without a before/after on the labelled fixture | Decision owed | classifier-wide, future ratifications | ✅ |
| OPEN-32 | Two large `layout_assign` errors (OPEN-01, OPEN-03) point in opposite directions; the net is unmeasured | Reported numbers | `layout_assign` EUI only — **adopted baseline confirmed clear 2026-08-06 (M06)** | ✅ **bounded** |
| OPEN-33 | **Archived arcs left 58 dead documentation paths** cited from 23 live documents | Register hygiene | navigability of the checklist + published docs; published set **repaired 2026-08-06** | ✅ **measured + partly fixed** |
| ~~OPEN-34~~ | ~~**Classification depends on batch composition** — a 3-building run is not archetype-faithful~~ | **CLOSED 2026-08-11** — mechanism was already identified 2026-08-06; the remaining question (*did any published result come from a batch small enough to matter?*) is now **measured, not reasoned**: all 12 adopted cells are whole, `05_results.csv` rows = `01_buildings.gpkg` features in every cell, fleet 8,160. Evidence: `openubem/outputs/comparisons/open34_cell_population_check.csv`. Director recounted `nyc_centre` 738, `la_rural` 149 and the fleet total by hand. 🔴 **The standing consequence survives the closure: a verification run on a subset of a cell must use the whole cell, or state that its archetypes are not fleet-faithful.** **ID retired.** |
| OPEN-35 | **Two fallbacks invent the missing storey count and disagree** — archetype chosen at group-median storeys, geometry built at 1. **2026-08-11: the mechanism is now proved by direct `.eio` evidence, not inferred.** The 2,611-building subpopulation matches its own broken `levels = 1.0` denominator almost exactly in `auto`/`building`/`floor` (**100% within ±1%, by construction** — those modes build zones from `levels`) and **breaks sharply under `layout_assign` (mean 2.3728, only 17.92% within ±1%)**, which assigns storeys from the archetype instead. **The two paths disagree, measured, on 40,800 runs.** **Still open** — the intended-fallback question is a DESIGN decision, not a measurement. | Simulation correctness | **2,611 / 8,160 = 32.00% of the fleet**; 1,031 of them given a mid/high-rise archetype and built at one storey | ✅ **mechanism verified + size measured + simulation-boundary proof 2026-08-11** |
| OPEN-36 | 🔴 **A signed completion record describes code that has never existed in any commit** — T07's tests were committed, its implementation never was | Register hygiene → **record integrity** | ~~unmeasured~~ **measured (N13): 596 entries swept, 1 governance gap — T07, the known one**; directly causes E-UTCI-12 | ✅ **verified from git**; **scope now bounded** |
| OPEN-37 | **The harvest never fetches `.eio`, so simulated floor area cannot come home** — the cluster keeps the file, the tar that retrieves results does not ask for it. **✅ FIXED 2026-08-10 (R09), five files, 149=149=149 verified** | Reported numbers | every fetched fleet, all modes; blocked the simulated-vs-declared floor-area check on **E02's 40,800 runs** — **unblocked before E02's first harvest** | ✅ **verified at the source line + on the cluster; fix manager-verified** |
| OPEN-38 | ~~**`layout_assign` subsurface geometry defect** — 7 tasks die on EnergyPlus **severe** *"Base surface does not surround subsurface"*, escalating to a two-space fatal~~ 🔴 **PREMISE FALSIFIED 2026-08-11 — item rewritten, still open.** That message is a **`** Warning **`**, not a Severe, at all **8** sites, and **kills nothing**. The item is now two measured defects: **(i)** all 7 `layout_assign` fatals die on **thermal runaway in zone `LAUNDRYROOMFLR1`** (−12,459 / −23,743 / −11,950 / −15,491 / −12,901 / −59,865 / +182,399 °C) — the substituted prototype's laundry room, same zone token as OPEN-06, and **no other cause appears in that mode**; **(ii)** **8** buildings carry malformed door geometry, of which `nyc_rural/way_965718401` **completes successfully and publishes results** from it. All 8 are `layout_assign`; **zero in the other four modes**, verified across all 40,800 `.err` files. | Simulation correctness | (i) 7 fatals, one prototype zone; (ii) 8 buildings, 1 of them publishing | ✅ **both mechanisms measured; the register's stated cause was wrong** |
| ~~OPEN-39~~ | ~~**`set -e` in `submit_fleet_t08.sbatch` skips the trim step and the `task.rc` write on every failed task**~~ | **CLOSED 2026-08-11** — measured on the cluster, read-only: 45 failed E02 tasks orphan **≈2.14 GB** (mean **48.6 MB**/dir vs **449 KB** for successful, ~111×); failed dir has no `task.rc`, its successful array sibling does; replicates outside E02 (`t17_austin_centre_layout_assign`). **Zero of 15 `task.rc` references across 9 scripts uses it as a completion test** — all key on `eplusout.end`. Evidence: `extra/MEASUREMENT_open-39-40_cluster-records.md`. 🔴 **The standing rule survives the closure: never use `task.rc` presence as a completion test.** **ID retired.** |
| ~~OPEN-40~~ | ~~**Eight job arrays were submitted a third time by an unrecorded process**~~ | **CLOSED 2026-08-11 as untraceable — which this item's own text names as the answer.** Independent from-scratch `sacct` reconstruction of all **68** `e02_*` submissions in the window (19 + 8 + 41 = 68, exact) re-confirms the 8 IDs outside both waves; submitted 2026-08-09T23:08:58 → 2026-08-10T00:04:49; `JobName`/`WorkDir`/`User` carry no discriminating signal; remote `.bash_history` predates the whole window (mtime 2026-04-27) and is silent for all three waves alike. **No story was reconstructed from timestamps.** Disposition = the remedy the item already names: **a submission log nobody can bypass.** **ID retired.** |

| ~~OPEN-41~~ | ~~**43 of the 45 fleet failures have no recorded cause**~~ | **CLOSED 2026-08-11** — all **44** fatals now carry a recorded cause, captured from the `** Severe **` line preceding each fatal: 25 *Temperature (low) out of bounds*, 17 `CalcHeatBalanceInsideSurf`, 1 *Temperature (high)*, 1 `CheckForRunawayPlantTemps`. **Every one is a numerical thermal blow-up — none is a syntax, missing-object or licensing failure.** The 45th (`nyc_centre/fast_zone/way_1240348353`) is confirmed to contain no `Fatal` string at all, consistent with `std::bad_alloc`. 🔴 **The `la_rural` concentration is explained and it is not the cell — it is the archetype:** `Warehouse` is 38 of 8,160 buildings (0.47%) yet carries **26 of the 44** fatals, **13.68% vs 0.0443% ≈ 309× relative risk**; all 11 `la_rural` failing buildings are `Warehouse` with `no_floors`. Evidence: `openubem/outputs/comparisons/open41_failure_causes.csv`, `extra/MEASUREMENT_open-41-38_failure-causes.md`; director re-derived the archetype join and the two `la_rural` fatal counts independently. **The remedy question this exposed is OPEN-42, not this item.** **ID retired.** |
| **OPEN-42** | 🔴 **The `Warehouse` population is broken in two measured ways, and one of them reaches the adopted baseline.** **(i) It fails EnergyPlus at ≈309× the fleet rate** — 38 buildings (0.47% of the fleet) carry **26 of the 44** fatals; 13.68% of Warehouse tasks fail against 0.0443% of everything else; 13 distinct Warehouses fail in ≥1 mode; 36 of 44 failures carry `no_floors` and **37 of the 38 Warehouses do**. Failures split auto 8 / floor 8 / fast_zone 10, **zero in `layout_assign`**. **(ii) Six carry a placeholder `footprint_area_m2` of exactly 200.0 m²** (`la_rural` way_472960972/472961034/472961088/472961091/472961171, `la_urban` way_402215469), all flagged `no_floors`, against simulated areas of 4,064–67,330 m² — so **the adopted `auto` mode divides by a denominator wrong by 20.3× to 336.7× on real published buildings.** A widened scan found 16 Warehouses at ≤210 m² fleet-wide; 6 sit at the literal placeholder. **First measurement: made** (this is it). **What is not known:** whether (i) and (ii) are one defect or two — they overlap on 5 buildings but neither contains the other — and whether the 200.0 m² value is a constant in the source data or injected by an imputation path. | Reported numbers + simulation correctness | 38 buildings; **6 of them inside the adopted `auto` fleet EUI** | ✅ **both faces measured on all 40,800 runs**; ❓ **source of the 200.0 placeholder untraced** |

**Next free defect ID: E-LA-42** (verified by full sweep 2026-08-05, OPEN-05). **Next free UTCI defect
ID: E-UTCI-17** (same sweep; stated in no other document). ~~**Next free item ID: OPEN-41.**~~
~~**Amended 2026-08-11: OPEN-41 was taken on 2026-08-10 (§1's later amendment) and its table row was
missing here — added above. Next free item ID: `OPEN-42`.**~~
**Amended 2026-08-11 (later, the E02 audit and closure pass): `OPEN-42` was taken by the `Warehouse`
population defect — row added above in the same edit that opened it, so the missing-row failure of
2026-08-10 is not repeated. Next free defect ID `E-LA-42` and next free UTCI defect ID `E-UTCI-17`
are both unchanged — this pass opened no defect ID, only an item.
**Next free item ID: `OPEN-43`.****

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

### OPEN-01 — The EUI denominator is wrong for every non-`applied` building — ✅ **(a) and (b) answered on 40,800 runs 2026-08-11**; ❓ **(c) unprovable — ruling owed. STILL OPEN.**

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
> **A ruling is therefore owed:** accept the circumstantial evidence as sufficient for (c), or accept
> that **OPEN-01 can never close on this corpus.** Until that is ruled, this item stays open.
>
> ⚠️ **Two corrections to evidence this item's neighbourhood cites.** The two `e02_run*.log` files
> **do not cover the audited corpus** — dated 2026-08-06, three days before the manifest window,
> `nyc_centre` only, and one ends in a `MemoryError` inside an abandoned local attempt. **Do not cite
> them.** And a second, smaller finding: **24 `auto`-mode buildings outside ±1% all carry
> `perimeter_core` zoning** (+2% to +31%), while the 718 `single_zone`/`one_zone_per_floor` buildings in
> the same comparison are 100% inside ±1% — a geometry residual recorded here, not sized further.
>
> 🔴 **The remedy remains the user's ruling, unchanged and untouched by this measurement:** fix the
> denominator, fix the simulation, or stop publishing per-building EUI for the affected modes. **No
> remedy was chosen. The measuring task's job ended at the number.**
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

### OPEN-04 — The labelled-accuracy gate drifted 92.0% → 88.0% ✅ **explained**

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

### OPEN-31 — Ratified changes are adopted without a before/after on the labelled fixture ✅
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

### OPEN-33 — Archiving an arc breaks every document that cites it ✅
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
> **Item stays open until the rule is written where the next person archiving an arc will meet it.**

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

### OPEN-36 — A signed completion record describes code that has never existed in any commit ✅
*Added 2026-08-06, found by the director while auditing N10. Not what N10 was looking for.*

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

**Evidence mark:** ✅ **both faces measured on all 40,800 runs**; ❓ **the source of the 200.0
placeholder is untraced.**

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

### OPEN-13 — E-UTCI-12 and E-UTCI-13 ✅ **read at last, and both are still live**
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

### OPEN-22 — "Which exam does the answer key grade" ⚠️
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
- **OPEN-24** — the LIVE_SMOKE gate (real 23.1 IDD + a real EnergyPlus design-day run) is still
  parked. It was called *"the recommended next remediation block"*. Given this project's recorded
  standing lesson that synthetic-green ≠ live-green, this is the most consequential of the four.
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
| **OPEN-26** | **1 of 4 fixed, 3 survive** | Fixed: the bbox fallback does reach the manifest — but via `generation_status` (`openubem/idf/builder.py:611-627`), **not** `data_quality_flag` as the item names it. Still open: missing-EPW `Site:Location` silently at (0,0) (`builder.py:210-212`); `compute_form_factor` still never called (`openubem/geometry/footprint.py:66`); neighbour bbox recomputation uncached (`openubem/geometry/context.py:24`). |
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
`docs/docs_REPORTS/REPORT_phaseE_final.md:74` (*8,160 of 8,160 succeeded*).

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

Nothing in this register is scheduled. Nothing is assigned. No cluster time is committed.
