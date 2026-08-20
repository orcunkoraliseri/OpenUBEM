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

**Amended 2026-08-06 (round 2 of the no-compute queue, N06–N12 — `implemenation/previous/PLAN_no-compute-queue-2.md`).**
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

**Amended 2026-08-06 (round 3 of the no-compute queue, N13–N15 — `implemenation/previous/PLAN_no-compute-queue-3.md`).**
Two landed so far. **N15** tested the OPEN-12/OPEN-14 convergence and refuted it (above). **N14**
answered OPEN-06's third open question: **`archetype_id` is not the only unreproducible column** —
`data_quality_flag` is too, on the same buildings, and what differs is *which imputation rule the
classifier says fired*. Its `archetype_id` control passes exactly against N04's population. Two
cautions the director added on audit: N14's "same 9 rows" claim is **wrong** and struck (26 vs 38 on
`nyc_centre`, the excess being a Stage-3 `narrow_perimeter_fallback` token from
`openubem/idf/builder.py:614`), and **26 of the 33 columns remain unchecked** because they are
Stage-3-or-later outputs that no no-CPU task can reach.

**Amended 2026-08-06, later (round 3 closed + round 4 — `implemenation/previous/PLAN_no-compute-queue-4.md`).**
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
`implemenation/previous/PLAN_no-compute-queue.md` (N01–N05), whose first measurements need no simulation.
**A prerequisite found while scoping it:** the local runner's `ALL_MODES`
(`scripts/cluster/t08_local_remainder.py:52`) is `["auto", "building", "floor", "fast_zone"]` —
**`layout_assign` is not among them**, so as it stands the local runner can only do four of the five
modes.

**Amended 2026-08-06 (the compute queue opens — `implemenation/previous/PLAN_compute-queue.md`).**
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
   owed.~~ **→ superseded the same day by item 5.** Execution: **`implemenation/previous/PLAN_speed-resume.md`**
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

**Amended 2026-08-11 (the E02 audit and closure pass — `implemenation/previous/PLAN_e02-audit-and-closure.md`,
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

**Amended 2026-08-12 (evening — the rulings-and-five-items sweep, `implemenation/previous/PLAN_rulings-and-five-items-2026-08-12.md`, T01–T10, five parallel executors, every headline re-derived by the director from raw artifacts).**

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

**Amended again 2026-08-12 (night — the three-new-items sweep, `implemenation/previous/PLAN_three-new-items-2026-08-12.md`, T01–T07, four executors, every headline re-derived by the director from raw artifacts).**

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

**Amended 2026-08-13 (the three-rulings sweep's T04, `implemenation/previous/PLAN_three-rulings-2026-08-12.md` §8 — the twelve-cell fleet re-run, its cause analysis, and the confirmatory repeat run; director-audited against the raw IDFs and `05_results.csv` on both sides).**

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

**Amended 2026-08-18 (overnight — `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`, X01–X10).
Ten items measured, **no item closed, count unchanged at 25**. This was the first pass in this arc
where *every* live item already had a first measurement, so the selection rule changed shape: each
candidate was chosen by what its own §-section names as the **next unanswered question**, then checked
against `openings/extra/` and `openubem/outputs/comparisons/` to confirm that question was not already
answered on disk. **Six of the ten are questions the register itself writes down as "the next thing on
this item."**

🔵 **Four register figures were re-derived exactly, one of them after being formally declared not
re-derivable.** OPEN-10's **90 = 66 + 24** (X08, by running the experiment N11 §4 named and declined);
OPEN-35's **2,611 / 32.00 %** and **1,031** (X04); and OPEN-10 gained its first **denominator** —
90 of 1,992 `fallback_not_expressible`, i.e. **4.5 %** of the problem the edit is named for.

🔴 **Two blockers that had stood for weeks were stale, and both in the same way — nobody had looked
at the disk.** **OPEN-08's** vintage half was blocked on *"no prior-generation source carries
`vintage_standard`"*: the E02 **parquet manifests survived** the 2026-08-17 sweep (61 files, all
twelve cells), and the vintage half now measures **3 / 8,160 = 0.0368 %** with the archetype control
at **0.0000 %**. **OPEN-14's** named next step was taken and settles its convergence with OPEN-12:
**zero `FUSED` provenance tokens across all 8,160 buildings**, including the one cell that *has* a
tracked Overture slice — the missing slices are real but **not the binding blocker**.

✅ **OPEN-56's fleet-scale cost measurement — the register's own named next step — is made.** 69
buildings across all twelve cells, control whole (**70 / 70** baseline volume warnings → **0 / 70**
treated, **70 / 70** completed in both arms): **mean +0.98 %, median +0.84 %, 65 / 69 same
direction.** 🔴 **The pre-registered prediction was half refuted:** the cost does *not* rise with zone
count (corr **+0.113**) and urban cells do *not* lead — it is a **fixed per-building offset of
≈ +1.0 kWh/m²**, which overturns the "per-zone effect" the previous pass inferred from ten points.
**`157.1 kWh/m²` is deliberately not restated**, and the remedy remains unauthorised.

🔵 **X03 is a clean negative that stops a wrong merge:** writing the correct zone volume leaves the
heat-balance non-convergence **completely untouched** (150 warnings baseline, 150 treated, 15/15 on
every one of the ten). **OPEN-09 and OPEN-56 are independent defects that overlap on 16 buildings** —
fixing one would not fix the other, and folding them would have been wrong.

⚠️ **Two things this pass got wrong and caught before reporting, both recorded rather than repaired
silently.** (1) The OPEN-08 comparison first dropped the geometry column, silently disabling
`resolve_vintage`'s spatial donor tier and producing a figure **ten times too large** (0.3554 %); the
missing `HOTDECK_*` rows in the tier table were the tell. (2) The OPEN-56 fleet run put 140 EnergyPlus
jobs through a 6-worker pool and **ten produced empty output directories**, which read as failures and
would have reported the control as 60/70; re-run serially the identical file completes in 18 seconds
with 0 severe errors. **An empty output directory is not a failed simulation.**

**Nothing closed. Next free item ID unchanged: `OPEN-57`.** Recommended closures now standing at
**four** and all left to the user: **OPEN-42** and **OPEN-11** (fold into OPEN-56), **OPEN-07**, and
now **OPEN-08**.

**Amended 2026-08-19 (T09 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, executing ruling R2): all
four taken.** OPEN-42, OPEN-11, OPEN-07 and OPEN-08 are closed, struck in §1, and retired. See each
item's own §-section for its closure record (what survives it, named explicitly) and §1's header for
the programmatic recount.

## 1. Summary — ~~**25 tracked items**~~ ~~**21 tracked items**~~ ~~**23 tracked items**~~ ~~**20 tracked items**~~ ~~**19 tracked items**~~ **20 tracked items** *(2026-08-19, later the same day, **director**, after T02 attempt 3 reported: **+2 opened, none closed** — **OPEN-57** (`_ssh` intermittently faults with `Unmatched '.` on the `_remote_results_complete` probe; **second confirmed occurrence**, and it is what has blocked OPEN-55's acceptance test through three attempts and zero simulated buildings) and **OPEN-58** (`open56_zone_volume_experiment.py`'s `run_ep()` cross-contaminates EnergyPlus outputs under `-x` and reads EUI by a formula that is not production's; found by **T04's own controls**, blast radius unmeasured). **Both were opened by the director, not by an executor** — T02 recommended the first and does not open IDs; the second was carried out of CP-3 as the named thing to adjudicate. **The count went up for the right reason again:** neither defect was found by a task that went looking for it, and suppressing either to protect the number was not on the table. Table re-counted **programmatically** (`scripts/analysis/open_register_recount_2026-08-18.py`): **23 live rows, 35 struck — 58 total, exactly OPEN-01…OPEN-58, no row missing, none duplicated.** **Next free item ID: `OPEN-59`.** The invariant *struck rows − retired IDs = 2* (OPEN-02, OPEN-28) is unchanged — this edit added live rows only.)* *(2026-08-19, T09 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, executing user ruling R2: **−4 closed and retired** — **OPEN-42** and **OPEN-11** (both fold into OPEN-56 — mechanism measured and cured by intervention on the six buildings tested; OPEN-56 itself stays open, unauthorised), **OPEN-07** (all three buildings succeed at HEAD; `SmallHotel` provenance carried forward), **OPEN-08** (X05: vintage 0.0368%, archetype control 0.0000%; "E02 is gone" corrected — the parquet manifests survived, only `.sql`/`.idf` were swept). **No item opened this pass.** Table re-counted **programmatically** (`scripts/analysis/open_register_recount_2026-08-18.py`, output quoted in this plan's §8, T09 entry): **21 live rows, 35 struck — 56 total, exactly OPEN-01…OPEN-56, no row missing, none duplicated.** **Next free item ID unchanged: `OPEN-57`.** Reconciliation: the invariant *struck rows − retired IDs = 2* (OPEN-02, OPEN-28) holds — **35 struck − 2 = 33 retired IDs.** Each closure names what survives it in its own §-section; **none of the four depends on T01** (this same plan's OPEN-55 B+ donor-screen code change) — **OPEN-55 stays open**, unproven in simulation since T02 (its own acceptance test) crashed twice and did not run. E-LA-17's T08 recommendation (strike from OPEN-29, merge into OPEN-09) is recorded but **not executed** and **not** one of this pass's four closures.)* ~~**25 tracked items**~~ ~~**24 tracked items**~~ **25 tracked items** *(2026-08-18 (late), `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`: **+1 net** — **two closed and retired** (**OPEN-48**, its post-fix fleet re-run finally made and the fix measured at under 0.08 %; **OPEN-54**, remedy implemented and tested the same evening) and **three opened** (**OPEN-54** and **OPEN-55** on 2026-08-18, both given their §1 rows for the first time in this edit, and **OPEN-56** — every building in the fleet simulating with a 10 m³ zone-volume stub, found while looking for OPEN-42's mechanism). **The count went up, and it went up for the right reason:** OPEN-56 was found by auditing an artifact for a different question, and suppressing it to protect the count was forbidden by the plan and was not done. Table re-counted **programmatically** (`scripts/analysis/open_register_recount_2026-08-18.py`, output quoted in that plan's §8): **25 live rows, 31 struck — 56 total, exactly OPEN-01…OPEN-56, no row missing, none duplicated.** **Next free item ID: `OPEN-57`.** ⚠️ **Reconciliation corrected in this pass, with the derivation shown rather than asserted.** The invariant is *struck rows − retired IDs = 2*, the 2 being **OPEN-02** and **OPEN-28**, folded under OPEN-01 and never independently tracked. 31 struck − 2 = **29 retired IDs**. The previous header's prose said *"twenty-six retired"* against 29 struck rows, which would have made the difference 3; **that prose was one short and is corrected here to 27-before / 29-after.** The struck-row count is the auditable figure — it is recomputed from the table by script — and the prose total had drifted from it. Three items were measured without closing: **OPEN-42** (mechanism found, folds into OPEN-56), **OPEN-11** (identity confirmed, remedy invalidated), **OPEN-07** (all three buildings succeed at HEAD) — each with a closure **recommended to the user and not taken here**.)* ~~**24 tracked items**~~ *(2026-08-18, T06 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`: **−1 closed and retired — OPEN-52** (the fixed-`--basetemp` collision; ruling `3a` was delegated to the director by the user, given, implemented and verified on four controls including a real two-session concurrency test and a full-suite baseline match). **No item opened this pass.** **Twenty-seven IDs retired in all.** Table re-counted **programmatically** (`scripts/analysis/open_register_recount_2026-08-18.py`, output quoted in this pass's plan doc §8, T06 entry): **24 live rows, 29 struck — 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated.** Reconciliation unchanged in kind: **29 struck rows against 27 retired IDs; the difference of exactly 2 is still OPEN-02 and OPEN-28**, folded under OPEN-01 and never independently tracked — OPEN-52 moved from live to struck and retired in one edit, so the gap neither widens nor narrows. **Next free item ID unchanged: `OPEN-54`.** Four items were measured without closing: **OPEN-07**, **OPEN-08**, **OPEN-29**, **OPEN-53**, each narrowed and each with its blocker re-tested rather than inherited.)* — ~~**34 tracked items**~~ ~~**29 tracked items** *(2026-08-13, after `PLAN_five-items-2026-08-13.md`: −5 — **OPEN-26, OPEN-36, OPEN-44, OPEN-45, OPEN-50** all closed and retired; **nineteen IDs retired in all**. Table re-counted programmatically: **29 live rows, 20 struck.**)*~~ ~~**29 tracked items** *(2026-08-13, later, after `PLAN_five-more-items-2026-08-13.md`: **−2 closed** — **OPEN-24** and **OPEN-32**, both retired, **twenty-one IDs retired in all** — and **+2 opened**, **OPEN-51** and **OPEN-52**, both found by the director rather than by a task's stated question. **The count is flat, and that is the honest reading: this pass closed two items and discovered two more.** Table re-counted programmatically: **29 live rows, 23 struck — 52 total, exactly OPEN-01…OPEN-52 with no row missing and none duplicated.** ⚠️ The previous header's "20 struck" was a miscount in the prose; the table itself was complete at 21.)*~~ ~~**28 tracked items** *(2026-08-17, after T08 of `PLAN_open-49-and-open-01-2026-08-13.md`: **−1 closed** — **OPEN-01**, retired, its remedy implemented and its before/after reproduced on all five modes (see this item's own §1 row and §-section). **Twenty-two IDs retired in all.** Table re-counted programmatically: **28 live rows, 24 struck — 52 total, exactly OPEN-01…OPEN-52 with no row missing and none duplicated.** OPEN-49 is not counted in this closure — it stays live, marked mechanism-fixed/closure-blocked, in its own §-section.)*~~ ~~**26 tracked items**~~ **25 tracked items** *(2026-08-18, after T06 of `PLAN_five-items-2026-08-18.md`: **−2 net** — three closed and retired (**OPEN-06, OPEN-37, OPEN-51**) and one opened (**OPEN-53**, the E02 harvest `.sql`/`.end` shortfall found by T03's `.eio` census). **Twenty-five IDs retired in all.** Table re-counted **programmatically**, by a script over the §1 table body (`scripts` output quoted in this pass's plan doc §8, T06 progress-log entry): **26 live rows, 27 struck — 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated.** The reconciliation carries forward unchanged in kind, updated in number: **27 struck rows but 25 retired IDs; the difference of exactly 2 is still OPEN-02 and OPEN-28, folded under OPEN-01's umbrella and never independently tracked.**)* (OPEN-01 … **OPEN-52**; OPEN-23 excluded, OPEN-21 deferred, OPEN-05, OPEN-25, **OPEN-30, OPEN-33, OPEN-34, OPEN-39, OPEN-40 and OPEN-41** closed — all ten IDs retired; **OPEN-04, OPEN-31 and OPEN-43 closed 2026-08-12 and formally retired 2026-08-13 on ruling `2h`**; **OPEN-22 closed and retired 2026-08-13** — fourteen IDs retired in all; ~~**OPEN-01 closed and retired 2026-08-17** — fifteen IDs retired in all; **OPEN-02 and OPEN-28 folded into OPEN-01** on 2026-08-09 and **both discharged 2026-08-11**)~~ *(Corrected 2026-08-17, director audit: the trailing parenthetical above was stale — it stopped at fourteen after OPEN-22 and never picked up the five retirements from `PLAN_five-items-2026-08-13.md` (OPEN-26, OPEN-36, OPEN-44, OPEN-45, OPEN-50) or the two from `PLAN_five-more-items-2026-08-13.md` (OPEN-24, OPEN-32), so the executor's first pass at this line copied its stale "fourteen + 1" into "fifteen" instead of following the correct running total in the struck-header lineage on this same line, which already read twenty-one before today. The full retired-ID list, twenty-two in all: **OPEN-23** (excluded), **OPEN-21** (deferred), **OPEN-05, OPEN-25, OPEN-30, OPEN-33, OPEN-34, OPEN-39, OPEN-40, OPEN-41** (closed, ten so far), **OPEN-04, OPEN-31, OPEN-43** (2026-08-12/13, thirteen), **OPEN-22** (2026-08-13, fourteen), **OPEN-26, OPEN-36, OPEN-44, OPEN-45, OPEN-50** (2026-08-13, nineteen), **OPEN-24, OPEN-32** (2026-08-13, twenty-one), **OPEN-01** (2026-08-17, twenty-two). **OPEN-02 and OPEN-28 are folded into OPEN-01, not retired** — they were struck rows in the table (discharged 2026-08-11) but never independently-opened tracked IDs, which is exactly why the table carries **24 struck rows against only 22 retired IDs: the difference of 2 is OPEN-02 and OPEN-28**, and that is the reconciliation, not a miscount.)* *(Extended 2026-08-18, T06 of `PLAN_five-items-2026-08-18.md`: three more IDs retired — **OPEN-06** (classifier archaeology closed the item), **OPEN-37** (`.eio` fetch gap closed on all ten sites), **OPEN-51** (`E-LA-16` adjudicated) — **twenty-five IDs retired in all.** One new ID opened, **OPEN-53** (E02 harvest `.sql`/`.end` shortfall), not yet retired. The struck-vs-retired difference of 2 (OPEN-02, OPEN-28) is unchanged by this pass — all three closures this pass retired an ID that was also a struck row, one-for-one, so the gap neither widens nor narrows.)* *(Extended 2026-08-18 (evening), T01/T05 of `implemenation/previous/PLAN_four-items-2026-08-18.md`: **−1 closed and retired — OPEN-46** (elevator reporting path verified whole at HEAD in code and in live tests; the item's stated blocker was stale). **No item opened this pass.** **Twenty-six IDs retired in all.** Table re-counted **programmatically**, by a script over the §1 table body (`scripts/analysis/open_register_recount_2026-08-18.py`, output quoted in this pass's plan doc §8, T05 progress-log entry): **25 live rows, 28 struck — 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated.** The reconciliation is unchanged in kind: **28 struck rows but 26 retired IDs; the difference of exactly 2 is still OPEN-02 and OPEN-28**, folded under OPEN-01's umbrella and never independently tracked — OPEN-46 was a live row moved to struck and retired in the same edit, so the gap neither widens nor narrows. **Next free item ID unchanged: `OPEN-54`.**)*

**Amended 2026-08-19 (late, **director**, on the user's ruling *"est-ce que tu peux fermer toutes en exécutant"*): **three items CLOSED and their IDs RETIRED — OPEN-29, OPEN-47, OPEN-57.** All three had a standing closure recommendation on this register that only the user could act on, and the user acted on all of them in one ruling. 🔴 **None of the three is closed by new evidence taken today** — OPEN-57 by a fix landed and verified live the same day, OPEN-29 by a re-derivation of 2026-08-18, and OPEN-47 by ratifying the user's **own** ruling of 2026-08-12 as a documented departure rather than by changing the classifier. ⚠️ **The same ruling authorised two things that are NOT closures and are NOT done here:** OPEN-55's acceptance test and the restatement of the fleet baseline, both dispatched under `implemenation/previous/PLAN_close-all-2026-08-19.md`. **OPEN-49 remains live and coupled to OPEN-55.** **23 → 20 tracked items. Next free item ID unchanged: `OPEN-59`.**

**Amended 2026-08-19 (late, **director**, at CP-1 of `implemenation/previous/PLAN_close-all-2026-08-19.md`): **two items CLOSED and their IDs RETIRED — OPEN-55 and OPEN-49 — and one OPENED, OPEN-59. 20 → 19 tracked.** 🟢 **Unlike the three closures earlier the same day, these two ARE closed by new evidence taken today**, and by the item's own pre-registered falsifiable test rather than by a judgement call: `nyc_suburban`, 1,589 buildings, job 1274983, divergences **71 → 0**, all three controls passed. The two closed **together** because this register required it — *"OPEN-49 cannot close while OPEN-55 stands"* — and the single test discharges both. 🔴 **The pass did not end clean, and the count going up is the honest reading.** The director's audit of the passing run found that Unknown buildings, with the equipment defect now genuinely cured, still run **1.7× classified** on DHW and heating instead. That was outside the acceptance test's question and is **OPEN-59**; it was not folded into either closure and was not suppressed to keep the count falling. **Next free item ID: `OPEN-60`.** Table re-counted **programmatically** after this edit (`scripts/analysis/open_register_recount_2026-08-18.py`): **19 live rows, 40 struck — 59 total, exactly OPEN-01…OPEN-59, no row missing, none duplicated.** The invariant *struck rows − retired IDs = 2* (OPEN-02, OPEN-28, folded under OPEN-01 and never independently tracked) holds: **40 − 2 = 38 retired IDs.** Both closures moved a live row to struck and retired its ID one-for-one, and OPEN-59 was added as a live row only, so the gap neither widens nor narrows. ⚠️ **T03–T05 (the 12-cell fleet re-run and the restatement of the baseline) are dispatched and NOT done** — no fleet figure is restated by this edit, and **157.1 kWh/m² pooled remains the adopted baseline until CP-2.**

**Amended 2026-08-19 (late, **director**, at CP-2 of `implemenation/previous/PLAN_close-all-2026-08-19.md`): 🔴 **THE ADOPTED FLEET BASELINE IS RESTATED — ~~`157.1 kWh/m²`~~ → `153.8231 kWh/m²` pooled, over 8,153 successful buildings, 24,320,582 m² of floor area.** The twelve-cell re-run `open48_refleet4` finished 2026-08-19 20:52 and T04/T05 are executed. **No item is opened or closed by this edit — the count stays 19 live / 40 struck / 59 total, next free `OPEN-60`, and the invariant *struck − retired = 2* (OPEN-02, OPEN-28) is untouched.** The definition is unchanged and still binding: **pooled = Σ(EUI × floor area) ÷ Σ(floor area) over successes**, OPEN-43's ruling, restated with its definition every time. Both sides carry **identical `osm_id` sets in all twelve cells** (symmetric difference zero), and the baseline side recomputes to `157.0552` exactly by the same code path, so this is a restatement of the same fleet and not a re-population. **Delta −3.2321 kWh/m², −2.06 %.** 🔵 **The whole restatement is one change.** Splitting on `OpenUBEMUnknown`: that population (650 buildings, 3.7 % of fleet floor area) moves **223.44 → 107.22, −52.01 %**, while everything else (7,504 buildings) moves **154.51 → 155.55, +0.68 %**. Counterfactual with Unknown frozen at baseline = **157.9836**, so **Unknown contributes −4.1606 and everything else +0.9285.** Mechanism cited: **OPEN-55's B+ donor screen** (`openubem/semantic/__init__.py`, `_UNKNOWN_DONOR_EXCLUDE`) lowers the upper bound of the Unknown PDE uniform draw by removing data centres, `Laboratory` and the restaurants from the pool — the heaviest movers fall from the 450–580 kWh/m² band to 80–160. **OPEN-48's 2026-08-18 forecast of "+4.058 kWh/m² (+2.615 %) from the Unknown path — report it, never subtract it" is confirmed in size and sign by an actual run**, and the run that could move `157.1` was correctly identified there as *one taken after the OPEN-55 ruling*. ⚠️ **`153.8231` is NOT volume-correct and must never be quoted without that caveat: OPEN-56 is open and unremedied, 8,160/8,160 buildings still simulate with a 10 m³ zone-volume stub, measured at ≈ +1.0 kWh/m² per building on a 69-building twelve-cell control. That correction is NOT inside `153.8231`; a volume-correct run-4 fleet would be ≈ 154.8 kWh/m², which is not adopted.** ✅ **OPEN-35 Scope B verified in simulation**: 20 of its 21 buildings carry a floor-count correction, every one upward from a bogus `levels = 1.0` to a real storey count (5/6/7/19/45); the fleet gains 774,714 m² (+3.3 %) of floor area as a direct result, which is why those buildings' EUI rises 45.94 % as a group yet moves the pooled fleet by only +0.66. ✅ **nyc_suburban's Unknown count is 290 in both runs** — T04's divergence question against T01's `0/290` is answered, there is no divergence; at 18.3 % it clears the LIVE_SMOKE 20 % ceiling but not by much. 🔴 **A NEW REGRESSION was found by this run and is NOT yet an item, because opening one is the user's call: the 21st OPEN-35 building, `nyc_centre / way/266034056`, no longer simulates.** Its run-4 IDF carries `Storey 0…18` (19 storeys, the OPEN-35 value); EnergyPlus diverges (`CalcHeatBalanceInsideSurf`, 1,940,305 °C), the pipeline's zero-area-surface strip and reroute to `one_zone_per_floor` both fail (2.04e7 °C), and it is dropped under B2 tolerance with the standard placeholders (`footprint_area_m2 = 200.0`, `levels = 1.0`). **In the baseline it was 1 storey and ran fine at 307.23 kWh/m².** Three of its 19-storey siblings needed repair before completing, so this is a marginal interaction across that group, not a one-off. 🔴 **A second thing is owed to the user and was not taken unilaterally: the 4 `Courthouse` → `OpenUBEMUnknown` flips**, together **477,804 m²** (one of them 157,115 m², the heaviest building in `nyc_centre`) — fleet floor area sitting in `Unknown` rises **392,848 → 870,652 m², 2.2×**, while the building *count* moves only 646 → 650. Whether the screen is correctly conservative or over-rejecting a legitimate classification is not a measurement outcome. ⚠️ **Two director claims made during this run are RETRACTED so they do not propagate:** (a) a **"null-island centroid"** defect signature — `centroid_lat` is near zero for every building in every cell in both runs, so the column is not a WGS84 latitude and near-zero signifies nothing; (b) the first reading of `way/266034056` as a **pre-existing degenerate footprint correctly excluded** — it is a new drop, and the `200.0` is the symptom of a drop rather than its cause (that placeholder does pre-exist on 6 baseline buildings, la_rural 5 and la_urban 1, all already failing in both runs). Full derivation, per-cell table and provenance: **`extra/MEASUREMENT_fleet-restatement-2026-08-19.md`**. Cluster post-mortem for the two cells that failed once on a transient SSH drop and succeeded on solo retry: `extra/INVESTIGATION_open48-run4-cell-failures.md`.)*

**Amended 2026-08-19 (late, **director**, at CP-1 of `implemenation/PLAN_twenty-items-2026-08-19.md` — the twenty-task pass over all nineteen live items): **NO item opened, closed, struck or retired. The count stands at 19 live / 40 struck / 59 total, next free `OPEN-60`, invariant *struck − retired = 2* (OPEN-02, OPEN-28) untouched.** T01–T05 are measurement-only, local, no cluster, no code change; **`153.8231 kWh/m²` pooled over 8,153 is not reopened, changed or restated by this pass**, and its OPEN-56 volume caveat is unchanged. Audited by the director against artifacts on disk, not on the executor's report. 🔴 **Two of the five tasks found their own premise FALSE at HEAD, and both false premises are this register's fault**: T02 and T03 were written from the **top-line table tags** for OPEN-56 and OPEN-58, which are stale against those items' own §-sections (`:7354-7357` already localises OPEN-56's writer to `geomeppy`; `:7713-7760` already carries OPEN-58's full blast-radius measurement). Both executors reported the contradiction rather than working around it and re-derived independently anyway. **Register hygiene: the top-line tags for OPEN-56 and OPEN-58 must be resynced to their §-sections; the §-sections are the authority.** 🟢 **OPEN-56's mechanism is now fully localised, and a THIRD remedy shape exists.** `geomeppy==0.12.2`'s winding corrector `set_entry_direction` (`geom/polygons.py:592-611`) is a **provable no-op** under our GGR convention: `outside_point("counterclockwise")` returns `vertices[0] + normal_vector`, so `is_clockwise` computes `dot(−n, n) = −|n|² < 0` and returns `False` **unconditionally** — the test is self-referential, built from the same normal it consumes. **Verified twice by the director independently of the executor**: by inspection of the installed package, and by executing it on a CW-wound and a CCW-wound square (both report `inverted=False`). Because that corrector never fires, the IDF winding is exactly the input footprint's own orientation — and the one `orient()` call that exists (`openubem/idf/builder.py:464-465`, read directly and confirmed) is gated `if self.resolution_mode != "auto"`, so it **never fires for the adopted baseline mode**. 0/20 sampled source footprints are CCW, matching the **8,160/8,160 (100.00 %)** run-4 warning rate. Remedy shapes now: (i) write `Zone.Volume` explicitly, as this register already proposes, or (ii) extend the existing `orient()` call to `auto` mode — sign unverified. **Neither applied; OPEN-56's remedy ruling remains owed to the user and is now better-informed, not resolved.** 🔵 **The OPEN-35 regression is a subset, not a singleton and not all of Scope B.** Repair rate is 19.0 % (4/21) in Scope B against a matched control of 0.97 % (4/414) — a real ~20× elevation — but it is concentrated **entirely** in the `nyc_centre` / `LargeHotel` / imputed-19-storey subset at **4/8 = 50 %**, while every other Scope-B subset is **0/13**, including `austin_centre`'s *taller* 45-storey imputations. Only **1 of 21** actually fails to complete; the other three repair and finish. Cell effect ruled out — `nyc_centre`'s own background repair rate on 292 real `levels ≥ 10` buildings is 1.03 %. **Recommendation to the user, not an action: scope the owed ID against the 8-building subset rather than against one building or all 21.** 🔵 **OPEN-59 carries two statistics that legitimately disagree** and the item's row should record both, each labelled by its weighting: floor-area-**pooled** Unknown EUI is **107.22**, 31 % *below* classified's 155.56; **median-per-building** Unknown EUI is **309.95**, **2.31×** classified's 134.08. Cause traced: the top 10 of 650 Unknown buildings hold **72.5 %** of Unknown floor area and run at moderate EUI (r = −0.27 between area and EUI), so the typical Unknown building is small and hot while the heavy ones are not. The register's `1.7×` is the median statistic on `nyc_suburban` alone. Fleet-wide the largest end-use multiple is **DHW at 10.2×**, ahead of heating (3.4×); `nyc_suburban`'s lighting **6.7× does not generalise (1.00× fleet-wide)**. ✅ **The `auto`-mode EUI denominator is sound fleet-wide on run 4** — 99.74 % within ±1 % against OPEN-01's 99.63 % closure figure, 100.00 % within 2×, **zero** buildings beyond; the 21 outside ±1 % are without exception `zoning_strategy == 'perimeter_core'`, a structural core/perimeter effect, max 1.31×. ⚠️ **A THIRD retraction, this one of a standing lead rather than a director claim: `relation_3566904`'s reported ÷4.18 area anomaly is CLOSED AS A FALSE LEAD.** Untouched production run-4 data gives that building `footprint_area_m2 = 2,682.23`, `levels = 14`, `floor_area_m2 = 37,551.22` — ratio **1.000001**, no anomaly whatsoever. The 157,115 m² belongs to a **different** building, `relation/11171793`, and the path is OPEN-58's `run_ep()` shared-cwd cross-contamination — **an independent second confirmation of OPEN-58's verdict, from data that never touched the defective helper.** ✅ Scope discipline verified by the director: `find openubem tests scripts/validation -mmin -180` returns **empty** — no source file, test or validation script was touched; all 13 claimed artifacts confirmed present at their stated paths. Full audit: §8 of the plan, `### ✅ CP-1 — AUDITED AND SIGNED`.)*

**Amended 2026-08-19 (late, **director**, at CP-3 of `implemenation/PLAN_twenty-items-2026-08-19.md` — T13–T20, the second and third groups of the twenty-task pass): **NO item opened, closed, struck or retired. The count stands at 19 live / 40 struck / 59 total, next free `OPEN-60`, invariant *struck − retired = 2* (OPEN-02, OPEN-28) untouched.** `153.8231 kWh/m²` pooled over 8,153 is not reopened, changed or restated by this block either. Audited by the director against artifacts on disk; scope discipline verified — `find openubem tests scripts/validation -type f -mmin -200` returns **empty** despite two tasks running real EnergyPlus rebuilds. 🔴 **One genuinely new CROSS-CUTTING finding, surfaced independently by three tasks (T15, T18, T20a) and correctly NOT opened as an item by the executor: no `layout_assign`-mode artifact built anywhere in this arc can currently deliver a production-parser EUI.** Every such build used `trim_outputs=True`, which strips the per-zone `Output:Variable` block that the parser's own integrity gate requires — mechanism **re-verified in code by the director independently of the executor**: `BuildingIDF.__init__` takes `trim_outputs: bool = False` (`openubem/idf/builder.py:219,227`) and passes it to `write_outputs(self.idf, trim_hourly=self.trim_outputs)` (`:516`, `:638`); the gate is `_check_zone_integrity` (`openubem/results/parser.py:203`, called at `:772-774`), whose own comment at `:85` states it "still looks for Ideal Loads variables to parse zones". Consequences, each **reported rather than worked around, and each naming the artifact that would settle it** (a `trim_outputs=False` rebuild): T15 cannot quantify the malformed-door building's EUI, T18 cannot produce a HEAD-consistent fleet-wide `layout_assign` vintage comparison, T20(a) cannot size OPEN-18's residual distortion. ⚠️ **This is a MEASUREMENT-CAPABILITY defect, not a defect in any published figure** — OPEN-32 already establishes structurally that no adopted result depends on `layout_assign`, so the bound on all three is zero regardless. **Whether it becomes a tracked item is a new ID and therefore the user's to ratify; deliberately not taken here.** 🟢 **OPEN-38(i)'s runaway finally has a mechanism, and it is neither geometry nor a wrong template** — see that item's row. 🔵 **OPEN-09 is unmoved and unmovable by this year's fixes**: `has_converge` true on **16 of 8,160 = 0.1961 %** of run 4, byte-identical to run 2 in cells and counts (**re-derived by the director from the executor's own per-building CSV**, not accepted on report); neither the OPEN-55 donor screen nor the OPEN-35 storey correction touches it. New observation: the 6 OPEN-56/OPEN-42 fatal `Warehouse` buildings each carry exactly 15 non-convergence warnings, the same as the 10 successful X03 controls — they sit **inside** OPEN-09's population by signature while failing for the separate, already-established reason. 🔵 **OPEN-19 is blocked by a DATA gap before it is blocked by code**: no Title 24 table exists anywhere in `openubem/data/`, zero Title 24/CEC/CALGreen hits, the economizer hardcode reconfirmed at all 6 sites, and the existing `construction_table` hook is wired only to the `OpenUBEMUnknown` synthetic path, not to any real archetype. ✅ **OPEN-27's erratum is written and the DESIGN doc was NOT edited** (hard rule 4 honoured), with paste-ready correction text for the user's external tool; **re-verified by the director**: `MultifamilyHome` has zero hits anywhere under `openubem/`, `HighriseApartment` is present in `semantic/__init__.py` and `semantic/building_classifier.py`. ✅ **OPEN-20's external-validity statement is written** — three metros, four rings, 12 cells, climate zones 2A/3B/4A only, and, cross-referenced to T17, **even within those three the model does not yet differentiate its physical response by climate zone.** ⚠️ **T15's rebuild corroborates this register to within one warning** (58,101,663 against the recorded 58,101,662) and found that the only pre-existing `layout_assign` number for that building (911.41) is untrustworthy for a **second, independent** reason: that generation labels it `SmallOffice` while its own raw zone names are unambiguously `SmallHotel` — **a fresh OPEN-06 instance, in an item already closed and retired.** Full audit: §8 of the plan, `### ✅ CP-3 — AUDITED AND SIGNED`.)*

**Amended 2026-08-19 (late, **director**, at CP-2 of `implemenation/PLAN_twenty-items-2026-08-19.md` — T06–T12, audited and signed; this closes the last of the three checkpoints of the twenty-item pass): no item opened, closed, struck or retired.** Count unchanged at **19 live / 40 struck / 59 total, OPEN-01…OPEN-59, none missing, none duplicated, next free `OPEN-60`** (programmatic recount, `scripts/analysis/open_register_recount_2026-08-18.py`); invariant *struck rows − retired IDs = 2* (OPEN-02, OPEN-28) holds. **No adopted figure moves.** Six of the block's seven controls were re-run by the director rather than accepted on report, and all six reproduced: T09(a) 43 passed / 10 skipped; T07's `impute_missing()` call sites (**two**, both `openubem/validation/mask_recover.py:330,338`, neither on the `enrich_semantics` path); T11's `inspect.signature(enrich_semantics)` (no parameter can reach the `ml` tier — OPEN-16's unreachability is **structural**); T12's positive control (`_ml_tier` in 3 commits, `_draw_tier` in **zero**, so OPEN-17's absence is not a search blind spot); T06's E02 recount (**145 `.eio` against 40,800 `.err`**). The seventh — the full suite — was re-run **independently by the director in a separate shell** after the executor's own background run died with its session: **1919 passed, 55 skipped, 11 warnings in 1115.22 s**, reproducing **F9 exactly** on two separate processes the same day. **The load-bearing custody question was answered directly:** the second external sweep (2026-08-19 16:19) hit the **E02 harvest tree only** — run 4 (`open48_refleet4`) still holds its **8,160 `.eio` intact**, so the adopted fleet EUI denominator is untouched and **153.8231 kWh/m² pooled (total simulated energy ÷ total simulated floor area) over 8,153 successful buildings / 24,320,582 m² stands**, with its standing caveat that it is **not volume-correct** (OPEN-56's 10 m³ zone-volume stub, ≈ +1.0 kWh/m²/building, is outside it; a volume-correct ≈154.8 is **not** adopted). Two findings carried forward without opening an ID: **OPEN-14 needs three things in order** — the slice, a production routing change that does not exist at HEAD, then the config gate — so the register's gate-only framing understates it; and **OPEN-53's custody risk is now a repeat pattern, not an incident** (two independent external sweeps on the same tree, 2026-08-17 `.sql`/`.end` and 2026-08-19 `.eio`), which strengthens the item's existing closure condition rather than changing any number.

**Amended 2026-08-19 (late, **director**, on the user's ruling *"vas-y, tu progresses comme tu recommandes pour ces options"* — the two decisions the director had reserved for the user were returned to him and both are taken here).** **+1 opened, none closed, one reframed.** **(1) OPEN-60 opened** — `total_eui_kwh_m2` undercounts Interior Lighting and Interior Equipment wherever a zone multiplier > 1 is in play, because those two end uses are summed from per-zone hourly variables (which EnergyPlus does not multiplier-scale) while the floor-area divisor is multiplier-aware. **6 of 48 reconcile within 2 %; worst error 192.28 %.** 🟢 **Zero adopted rows affected — verified at the IDF level, not assumed:** every `Multiplier` in three run-4 `auto` fleet IDFs is 1, and multipliers are written in exactly one module the production path never calls. **It was given an ID rather than left as a note precisely because nothing published depends on it** — an item that costs nothing to carry and would cost a great deal to rediscover. 🔴 **The gate that catches it already exists in the repository (`check_building_integrity()`) and the fleet pipeline never calls it.** **(2) OPEN-59 REFRAMED, not closed** — its hypothesis 1 is **refuted by measurement** (0 of 4 columns and 0 of 290 buildings out of bounds, worst excursion 0.0), so it is **not** OPEN-55's sibling and no screen can fix it; hypothesis 2 stands by elimination, making it a **calibration question rather than a defect**. **The ID stays open because the screen answered *why not*, not *why*** — the 10.2× fleet-wide DHW multiple is unchanged and unexplained, and closing the ID would retire the only record of it. **Both decisions were the user's to take and were explicitly returned to the director; neither was taken unilaterally.** Table re-counted **programmatically** (`scripts/analysis/open_register_recount_2026-08-18.py`). **Next free item ID: `OPEN-61`.** The invariant *struck rows − retired IDs = 2* (OPEN-02, OPEN-28) is unchanged — this edit added one live row and struck none.




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
| OPEN-03 | ~~`layout_assign` models all internal loads as 2022-code regardless of real vintage~~ 🔴 **REFRAMED AND THE CENTRAL CLAIM REFUTED 2026-08-20 (director, CP-2 of `implemenation/PLAN_vintage-elasticity-2026-08-19.md`).** The gap is a load-**source** disagreement, not a load-**vintage** one: `auto` reads one fixed pair per archetype from `doe_prototype_loads.json` (no vintage key), `layout_assign` uses the DOE prototype baseline IDF's own densities for any archetype with a mapped `STD2022` baseline. **Both modes are equally vintage-blind.** | Reported numbers | ~~~half of a −29% cross-mode gap~~ **≈8% of the pooled −23.91% gap; 0.0% in the subset where loads are held identical** | ✅ **measured — claim refuted, gap still open** |
| ~~OPEN-04~~ | ~~Labelled-accuracy gate drifted 92.0% → 88.0%, root cause unconfirmed~~ | **CLOSED 2026-08-12, formally retired 2026-08-13 on ruling `2h`** — the drift is explained and the item's own question is answered. The suspected Phase-D fusion/crosswalk cause was **falsified** by M04's live before/after reproduction, and the real cause was identified by bisect; the gate still clears. ⚠️ **Two facts survive the closure and must travel with any accuracy figure:** **92.0% is unreproducible** for an unrelated reason (its answer key was rewritten in the next commit, T10), and **the old 50-row fixture must never be deleted or edited — this item's bisect depends on it.** **ID retired.** |
| ~~OPEN-05~~ | ~~`has_fatal` dead column logged twice~~ | **CLOSED 2026-08-05** — full ID sweep run, no further duplicates. See §3. ID retired. |
| ~~OPEN-06~~ | ~~Archetype labels wrong for 41 of 8,160 buildings~~ ~~**the column does not describe what was simulated**~~ (E-LA-38) ✅ **CLOSED + ID RETIRED 2026-08-18** — commit `67ede73` reproduces the committed `05_results.gpkg` archetype exactly for all 41 buildings; resolves N07's provenance gap | Simulation correctness → **provenance** | 41 buildings; 100% of failures; **every per-archetype grouping** | ✅ **source defect + provenance defect**; ✅ **N14/N16 swept, population fully accounted for**; ✅ **2026-08-18: code state identified (`67ede73`), remaining first measurement answered** |
| ~~OPEN-07~~ | ~~3 buildings regressed success → failure (E-LA-40) — all three were simulated as `SmallHotel`, not the `SmallOffice` the file records~~ | **CLOSED 2026-08-19 (T09, ruling R2)** — all three buildings succeed at HEAD: run 2 (`open48_refleet`, `auto`-family) holds an IDF, `.err`, `.end` and `.sql` for all three and all three complete (`la_urban/way/401910463` 129.35 kWh/m², `nyc_rural/way/965718402` 237.23, `nyc_rural/way/965718403` 271.97 — all `Completed Successfully`, 0 Severe). **Provenance carried forward, outlives the item: all three were simulated as `SmallHotel`, not the `SmallOffice` that `05_results.gpkg` records.** Caveat carried forward: the E-LA-40 regression was observed under `layout_assign`, since decertified for fleet EUI; this closure is on the certified `auto`-family path succeeding, not proof the `layout_assign` mechanism is fixed. **ID retired.** Full record: this item's own §-section; `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §4. |
| ~~OPEN-08~~ | ~~Archetype/vintage not reproducible locally for data-poor buildings (E-LA-22)~~ | **CLOSED 2026-08-19 (T09, ruling R2)** — closes on X05 (2026-08-18 overnight): vintage half **3 / 8,160 = 0.0368 %** between E02's persisted label and a HEAD re-derivation; archetype control **0 / 8,160 = 0.0000 %** on the same join. **Correction carried forward: "E02 is gone" is too strong** — the 2026-08-17 sweep took the large files (`.sql`, `.idf`); 61 parquet manifest files survived across all twelve cells and carry `vintage_standard`, which is what made this measurement possible. **What is not closed by this and is carried forward as context, not reopened:** the separate T08-vs-T20 archetype comparison (a different, older generation pair) still stands at 13.40 % disagreement — this closure covers only the E02-vs-run-2 comparison, on which the pipeline is now shown reproducible. **ID retired.** Full record: this item's own §-section; `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X05. |
| OPEN-09 | `thermal_mass=True` drives warmup non-convergence; "cosmetic" never tested (E-LA-23) | Simulation correctness | 64% vs 5.3% control | ✅ **C06: "cosmetic" tested and holds — 96.3% distribution overlap, small correctly-signed residual** (audited) 🔵 **2026-08-18 (overnight, X03): NOT downstream of OPEN-56.** The ten non-convergent-but-successful buildings show 150 warnings baseline and 150 treated, 15/15 unchanged on every one, while the same treatment clears the volume warning 70/70 → 0/70. **Two independent defects overlapping on the same 16 buildings.** X07: E-LA-17 resolves to exactly this population and would double-count if adopted. |
| OPEN-10 | `ZoneGroup` list-multiplier edit would restore exact expressibility (E-LA-37) — **capability confirmed real from the schema; remedy narrower than claimed** | Capability | ~~90 buildings (**carried, not re-derivable without a fleet pass**)~~ **C03: 90 reproduces exactly — but that is 4.6% of the 1,976 inexpressible fleet-wide** + future | ✅ **measured + verified** ✅ **2026-08-18 (overnight, X08): the "90 buildings" RE-DERIVED EXACTLY — 66 `MidriseApartment` + 24 `HighriseApartment` — by running the experiment N11 named and declined. And a denominator at last: 90 of 1,992 `fallback_not_expressible` = 4.5 %; the other 1,902 (95.5 %) are structurally beyond the edit. `applied` is only 497 of 7,442.** 🔵 **CEILING RESTATED on run-4 data 2026-08-19 at CP-3 (T16): 4.78 % (was ~~4.5 %~~), 96 of 2,007.** The evaluated population reproduced exactly (7,442) but the 90-building `MidriseApartment`/`HighriseApartment` split did **NOT** — **69/27 against the carried 66/24, self-reported as a finding rather than smoothed over**, and explained: run 4 carries OPEN-35's storey corrections, which this item's own X08 finding already placed upstream of exactly that classification boundary. All other archetype counts unchanged. Capability and narrowness both reconfirmed. |
| ~~OPEN-11~~ | ~~6 inverted-geometry buildings need post-hoc remediation, not re-applied~~ | **CLOSED 2026-08-19 (T09, ruling R2)** — folds into OPEN-56. The "inverted geometry" label was **tested against a mechanism and not corroborated**: the `eplusout.err` upside-down-surface warning is universal to all 8,160 `auto`-mode runs, not distinctive to these six (2026-08-18 T03). The six are the same six as OPEN-42's face (ii) (re-derived exactly: intersection 6, symmetric difference 0). **The remediation decision is absorbed by OPEN-56's remedy, not dropped**: this item asked for a per-building post-hoc patch (`10_fails_solution.md`) on six buildings; the cause is now measured fleet-wide (8,160/8,160 buildings), so a six-building patch is the wrong shape of remedy, and OPEN-56's own closure condition (correct zone volume fleet-wide, no exception) now carries this item's remediation debt. **No remedy is applied by this closure — OPEN-56 stays open, unauthorised.** **ID retired.** Full record: this item's own §-section; `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §3; OPEN-56 §-section. |
| OPEN-12 | ~~Rural `height_m` residual — `nyc_rural` 36.4%, `austin_rural` 19.2%~~ **both re-derive at 100%; a third cell is at 100% and was never named**. **N15: genuinely a source-coverage gap — NOT a spillover from OPEN-14** | Data acquisition | **3 cells, 2,032 buildings; 2,806 / 8,160 fleet-wide** | ⚠️ **numbers do not reproduce** |
| OPEN-13 | E-UTCI-12 and E-UTCI-13, forwarded out of the UTCI arc — ~~both live at HEAD~~ **E-UTCI-13 fixed 2026-08-12; E-UTCI-12 contained only** | Data / Stage 6 | ~~the whole test suite cannot be collected~~ **collectable again (1937 tests, exit 0) — but 43 passing tests traded away**; cached re-read no longer nulls `levels`/`use_class` | 🟡 **1 of 2 fixed** |
| OPEN-14 | UTCI height backfill is not reproducible from a clean checkout — **confirmed; no Overture slice is tracked for any affected cell** | Reproducibility | Stage 6 inputs; ~~converges with OPEN-12 on the same 4 cells~~ **N15: coincidence — separate item** | ✅ **measured** ✅ **2026-08-18 (overnight, X09): the step this item named as "the next thing" is TAKEN. Zero `FUSED` provenance tokens across all 8,160 buildings — including `nyc_centre`, the one cell that HAS a tracked slice. The missing slices are a real but NON-OPERATIVE blocker; the config gate closes first. The OPEN-12 convergence is a coincidence.** |
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
| ~~OPEN-29~~ ✅ **CLOSED + ID RETIRED 2026-08-19** | **Defects last recorded OPEN that this register never adopted** — ~~**measured: 9 of 12 are genuinely still open**~~ **re-derived 2026-08-18 (T04): 8 of 12 genuinely still open — E-LA-21 moves to CLOSED-ELSEWHERE, its one-space `has_fatal` defect confirmed fixed at HEAD across all **eight** harvest sites (director-corrected from the executor's seven). E-LA-16 stays STILL-OPEN: OPEN-51 adjudicated its *name*, not its defect — refuting the lead this pass's plan asserted.**, now tracked inside this item. **2026-08-12: the malformed-fatal-test class R06 left behind is finished** — the three `scripts/diagnostics/` sites now use R06's regex, and the class is measured over all 40,800 corpus files: the malformed variants match **0** against ground truth **44**, so that test could never have fired. **No past diagnostic conclusion changes.** A **seventh site never before recorded**, `scripts/validation/phaseE_cpb_fixtures.py:176`, is reported (it can only over-count, and does not on real data). **The item stays open — the other eight defect IDs are untouched.** ✅ **CLOSED + ID RETIRED 2026-08-19** on the user's ruling of 2026-08-19. Every defect this item carries is now either owned by another item, immaterial, or dormant behind `layout_assign` — a mode the production path never uses and an arc already closed and **not certified for fleet EUI**. They become a precondition of any future `layout_assign` revival, not open work today. ⚠️ **The closure does not claim repair.** Absence of a signature in the `auto` fleet is evidence about the `auto` fleet at HEAD; no defect is marked fixed, and the three-building local probe that would settle them is still the way to settle them.| Register hygiene | 9 defects; ~~E-LA-21 replicated across **4** harvest scripts~~ **7 known fatal-test sites in total** | ✅ **measured; fatal-test class now closed on live code** 🔵 **2026-08-18 (overnight, X07): the adoption material exists. Four of the eight (E-LA-15, E-LA-18, E-LA-19, E-LA-30) have NO signature anywhere in 8,160 buildings; E-LA-16 is one building and no severity; E-LA-17 is OPEN-09's population exactly; E-LA-33 re-derived at 93.32 % inert, inside its own 82–98 % claim. No re-sweep.** ✅ **2026-08-19 RULED (director), after independent re-derivation from the raw artifacts: 5 confirmed, 2 CONTRADICTED, 1 not derivable.** ⚠️ **E-LA-16 is 2 buildings, not 1** (three per-family `buildings=1` rows were read without taking their union). 🔴 **E-LA-17 is NOT a duplicate of OPEN-09 and must not be struck as one** — its own Fatal signature has 0 hits in all 8,160 `.err` files, symmetric difference with OPEN-09's 16 is 16; the earlier match was read off a CSV whose regex (`open09_fleet_err_taxonomy.py:38`) cannot see `Fatal` at all. **Disposition: E-LA-06 → OPEN-18, E-LA-33 → OPEN-10, E-LA-16 closes immaterial (0.0245 %), and E-LA-15/17/18/19/30 park as dormant against `layout_assign` — a mode not on the production path.** Nothing in the item needs work at HEAD; **closing OPEN-29 itself is recommended to the user and NOT taken.** |
| ~~OPEN-30~~ | ~~Assigned vintage is never persisted by any harvest~~ | **CLOSED 2026-08-11** — demonstrated on 60/60 E02 manifests, 40,800 rows, 0 nulls, 5 distinct values, `DOERefPre1980` 93.44% vs the ≈92.9% expectation; `la_rural` cross-check vs raw `year_built` reproduces R07 with zero crossover in all five modes. Evidence: `openubem/outputs/comparisons/open30_vintage_distribution.csv`, `extra/MEASUREMENT_open-30-01c_vintage-and-code-state.md`. Director re-derived the full distribution independently. **ID retired.** |
| ~~OPEN-31~~ | ~~Ratified classification changes adopted without a before/after on the labelled fixture~~ | **CLOSED 2026-08-12, formally retired 2026-08-13 on ruling `2h`** — this was a *decision owed*, and the decision was taken: **CP-M3 was ruled obligatory on 2026-08-09**, so a ratified classification change must carry a before/after on the labelled fixture with both numbers recorded. No line of code was ever wrong here. 🔴 **The gate it created is live and is already binding on open work: OPEN-47's office-bin divergence cannot be changed without it**, and as of ruling `2a` (2026-08-13) the fixture side of that gate is **two exams, each with its own threshold** — the old 50-row fixture at ≥0.70 and the tag-rich `labelled_archetypes_tagrich_v2.csv` at its own mark. **Every accuracy figure must name its fixture.** **ID retired.** |
| ~~OPEN-32~~ | ~~the net is unmeasured~~ **CLOSED 2026-08-13 — ID RETIRED.** Net ≈1.12 at the median, but only 12.6% of buildings within ±10% of cancellation and `error_factor` quantized at powers of two — **quote the deciles, never the median** | Reported numbers | `layout_assign` EUI only — **adopted baseline confirmed clear 2026-08-06 (M06)** | 🟢 **closed** |
| ~~OPEN-33~~ | ~~**Archived arcs left 58 dead documentation paths** cited from 23 live documents~~ | **CLOSED 2026-08-12** — the closure condition set on 2026-08-09 was *"the rule is written where the next person archiving an arc will meet it"*, and it is met: the obligatory citation sweep, its resolve-**by-filename** requirement and reason, the three standing exclusions and the ~30-minute cost are now in the head section of `docs/PROJECT_CHECKLIST.md` (10 lines, no journal block touched). Re-sweep of **279** live citations finds **zero** genuine dead paths, and the scanner was **proved non-vacuous** by injecting a broken citation and watching it get caught. One weakness recorded, not smoothed over: **no artifact survives from the 2026-08-06 sweep**, so the 58-path baseline is not verifiable at row level and must be re-measured if ever needed. **Open question left to the user: whether the rule also belongs in `CLAUDE.md`** — until then a fresh session that never opens the checklist will not know it exists. **ID retired.** |
| ~~OPEN-34~~ | ~~**Classification depends on batch composition** — a 3-building run is not archetype-faithful~~ | **CLOSED 2026-08-11** — mechanism was already identified 2026-08-06; the remaining question (*did any published result come from a batch small enough to matter?*) is now **measured, not reasoned**: all 12 adopted cells are whole, `05_results.csv` rows = `01_buildings.gpkg` features in every cell, fleet 8,160. Evidence: `openubem/outputs/comparisons/open34_cell_population_check.csv`. Director recounted `nyc_centre` 738, `la_rural` 149 and the fleet total by hand. 🔴 **The standing consequence survives the closure: a verification run on a subset of a cell must use the whole cell, or state that its archetypes are not fleet-faithful.** **ID retired.** |
| OPEN-35 | **Two fallbacks invent the missing storey count and disagree** — archetype chosen at group-median storeys, geometry built at 1. **2026-08-11: the mechanism is now proved by direct `.eio` evidence, not inferred.** The 2,611-building subpopulation matches its own broken `levels = 1.0` denominator almost exactly in `auto`/`building`/`floor` (**100% within ±1%, by construction** — those modes build zones from `levels`) and **breaks sharply under `layout_assign` (mean 2.3728, only 17.92% within ±1%)**, which assigns storeys from the archetype instead. **The two paths disagree, measured, on 40,800 runs.** **Still open** — the intended-fallback question is a DESIGN decision, not a measurement. ✅ **2026-08-19 (T04–T05): scope corrected 11 → **21** and the agreement fix landed.** The census was apartment-scoped; 10 `LargeHotel` buildings consume imputed levels through the identical mechanism, and the 11 are a **strict subset** of the 21 (set containment, not count). Naive 509-building variant **rejected**. Fix in `derive_num_floors()`, gated on the `GROUPMEDIAN_LEVELS_MED` token. 🔴 T04 landed it **inert** — no call site passed the new arguments — and said so; **T05 wired 2 of 3 and stopped at the parser with a quoted obstacle; T06 closed it — leaving 2-of-3 would have made the build and parse paths derive DIFFERENT floor counts for the same 21, recreating this very defect elsewhere.** ✅ All three paths now change the **identical 21 osm_ids** (0 missing / 0 extra, set membership, fleet-wide over 8,160 buildings), with a test pinning the three-way agreement. ⚠️ Baseline predates the fix and is stale w.r.t. 21 buildings; **no fleet re-run, no restatement.**| Simulation correctness | **2,611 / 8,160 = 32.00% of the fleet**; 1,031 of them given a mid/high-rise archetype and built at one storey | ✅ **mechanism verified + size measured + simulation-boundary proof 2026-08-11** 🔴 **2026-08-18 (overnight, X04): consequence measured for the first time, and the headline it produces MUST NOT be quoted. 2,611 / 32.00 % and 1,031 both re-derive exactly; the +47.9 % fleet EUI gap is composition (nyc_suburban is 1,589 of 2,611 with no comparison group) and WITHIN cells the direction is not even consistent — 4 lower, 4 higher. Needs an intervention, not a cross-section. 0 failures in 2,611.** |
| ~~OPEN-36~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | ✅ **Corrected AT SOURCE — a dated ⚠️ CORRECTION banner now sits in the frozen record itself** (`IMPLEMENTATION_phaseC_ml_imputer.md:849`), on the user's ruling; the false half of the Artifacts line is struck, not rewritten. All five claims re-derived from git by the director. 🔴 **Sharper finding: the record is not wholly false — the 53 tests DID ship; the implementation never did.** ⚠️ **T09b and T11.8/T11.8b were NOT re-verified.** ~~🔴 **A signed completion record describes code that has never existed in any commit** — T07's tests were committed, its implementation never was~~ | Register hygiene → **record integrity** | ~~unmeasured~~ **measured (N13): 596 entries swept, 1 governance gap — T07, the known one**; directly causes E-UTCI-12 | ✅ **verified from git**; **scope now bounded** |
| ~~OPEN-37~~ | ~~**The harvest never fetches `.eio`, so simulated floor area cannot come home**~~ — the cluster keeps the file, the tar that retrieves results does not ask for it. ✅ FIXED 2026-08-10 (R09), five files, 149=149=149 verified. ✅ **CLOSED + ID RETIRED 2026-08-18** — remaining five sites fixed 2026-08-18 (T03), all ten fetch sites now request `.eio`; local E02 census: 40,800/40,800 `.eio` and `.err`, zero empty. `.sql`/`.end` shortfall (874/875) is out of scope, opened separately as **OPEN-53**. | Reported numbers | every fetched fleet, all modes; blocked the simulated-vs-declared floor-area check on **E02's 40,800 runs** — **unblocked before E02's first harvest** | ✅ **verified at the source line + on the cluster; fix manager-verified**; ✅ **2026-08-18: all ten sites fixed, census complete, zero `.eio` gaps** |
| OPEN-38 | ~~**`layout_assign` subsurface geometry defect** — 7 tasks die on EnergyPlus **severe** *"Base surface does not surround subsurface"*, escalating to a two-space fatal~~ 🔴 **PREMISE FALSIFIED 2026-08-11 — item rewritten, still open.** That message is a **`** Warning **`**, not a Severe, at all **8** sites, and **kills nothing**. The item is now two measured defects: **(i)** all 7 `layout_assign` fatals die on **thermal runaway in zone `LAUNDRYROOMFLR1`** (−12,459 / −23,743 / −11,950 / −15,491 / −12,901 / −59,865 / +182,399 °C) — the substituted prototype's laundry room, same zone token as OPEN-06, and **no other cause appears in that mode**; **(ii)** **8** buildings carry malformed door geometry, of which `nyc_rural/way_965718401` **completes successfully and publishes results** from it. All 8 are `layout_assign`; **zero in the other four modes**, verified across all 40,800 `.err` files. 🔴 **2026-08-18 (T04): population re-derived at 7, confirmed; tested against OPEN-42 and found to be a different mechanism on every measured axis (message class, zone position by `.eio` geometry — bottommost storey vs. OPEN-42's topmost, geometry origin — substituted `SmallHotel` prototype, mode — `layout_assign`-only). Recommend keeping the two items separate; director to rule.** ✅ **Ruling 2026-08-18: recommendation ACCEPTED — the two items stay separate.** | Simulation correctness | (i) 7 fatals, one prototype zone; (ii) 8 buildings, 1 of them publishing | ✅ **both mechanisms measured; the register's stated cause was wrong**; ✅ **2026-08-18: tested against OPEN-42, confirmed distinct; director ruled — stay separate** 🟢 **MECHANISM FOUND 2026-08-19 at CP-3 of `implemenation/PLAN_twenty-items-2026-08-19.md` (T14) for defect (i), and it is a LOADS/no-HVAC interaction — not geometry, and not a wrong template.** `LaundryRoomFlr1` has **zero HVAC** in the DOE `SmallHotel` prototype — absent from all 54 `ZoneHVAC:EquipmentConnections` entries — while carrying the floor's largest absolute internal-gain density (**46,286.64 W** gas dryer plus water-heater ambient losses). An unconditioned zone with nothing to cap that load free-floats into a `CalcHeatBalanceInsideSurf` divergence during Sizing. ⚠️ **Geometry is explicitly CLEARED and this is NOT an OPEN-56 stub**: that zone's `.eio` volume is **378.63 m³**, positive and plausible. Disjoint-mode claim reproduced exactly across all 40,800 `.err` files: **0** hits in `auto`/`building`/`floor`/`fast_zone`, **8** in `layout_assign`. No remedy authorised. |
| ~~OPEN-39~~ | ~~**`set -e` in `submit_fleet_t08.sbatch` skips the trim step and the `task.rc` write on every failed task**~~ | **CLOSED 2026-08-11** — measured on the cluster, read-only: 45 failed E02 tasks orphan **≈2.14 GB** (mean **48.6 MB**/dir vs **449 KB** for successful, ~111×); failed dir has no `task.rc`, its successful array sibling does; replicates outside E02 (`t17_austin_centre_layout_assign`). **Zero of 15 `task.rc` references across 9 scripts uses it as a completion test** — all key on `eplusout.end`. Evidence: `extra/MEASUREMENT_open-39-40_cluster-records.md`. 🔴 **The standing rule survives the closure: never use `task.rc` presence as a completion test.** **ID retired.** |
| ~~OPEN-40~~ | ~~**Eight job arrays were submitted a third time by an unrecorded process**~~ | **CLOSED 2026-08-11 as untraceable — which this item's own text names as the answer.** Independent from-scratch `sacct` reconstruction of all **68** `e02_*` submissions in the window (19 + 8 + 41 = 68, exact) re-confirms the 8 IDs outside both waves; submitted 2026-08-09T23:08:58 → 2026-08-10T00:04:49; `JobName`/`WorkDir`/`User` carry no discriminating signal; remote `.bash_history` predates the whole window (mtime 2026-04-27) and is silent for all three waves alike. **No story was reconstructed from timestamps.** Disposition = the remedy the item already names: **a submission log nobody can bypass.** **ID retired.** |

| ~~OPEN-41~~ | ~~**43 of the 45 fleet failures have no recorded cause**~~ | **CLOSED 2026-08-11** — all **44** fatals now carry a recorded cause, captured from the `** Severe **` line preceding each fatal: 25 *Temperature (low) out of bounds*, 17 `CalcHeatBalanceInsideSurf`, 1 *Temperature (high)*, 1 `CheckForRunawayPlantTemps`. **Every one is a numerical thermal blow-up — none is a syntax, missing-object or licensing failure.** The 45th (`nyc_centre/fast_zone/way_1240348353`) is confirmed to contain no `Fatal` string at all, consistent with `std::bad_alloc`. 🔴 **The `la_rural` concentration is explained and it is not the cell — it is the archetype:** `Warehouse` is 38 of 8,160 buildings (0.47%) yet carries **26 of the 44** fatals, **13.68% vs 0.0443% ≈ 309× relative risk**; all 11 `la_rural` failing buildings are `Warehouse` with `no_floors`. Evidence: `openubem/outputs/comparisons/open41_failure_causes.csv`, `extra/MEASUREMENT_open-41-38_failure-causes.md`; director re-derived the archetype join and the two `la_rural` fatal counts independently. **The remedy question this exposed is OPEN-42, not this item.** **ID retired.** |
| ~~OPEN-42~~ | **CLOSED 2026-08-19 (T09, ruling R2)** — folds into OPEN-56; see the closure note appended at the end of this cell. 🔴 **The `Warehouse` population is broken in two measured ways, and one of them reaches the adopted baseline.** **(i) It fails EnergyPlus at ≈309× the fleet rate** — 38 buildings (0.47% of the fleet) carry **26 of the 44** fatals; 13.68% of Warehouse tasks fail against 0.0443% of everything else; 13 distinct Warehouses fail in ≥1 mode; 36 of 44 failures carry `no_floors` and **37 of the 38 Warehouses do**. Failures split auto 8 / floor 8 / fast_zone 10, **zero in `layout_assign`**. **(ii) Six carry a placeholder `footprint_area_m2` of exactly 200.0 m²** (`la_rural` way_472960972/472961034/472961088/472961091/472961171, `la_urban` way_402215469), all flagged `no_floors`, against simulated areas of 4,064–67,330 m² — so **the adopted `auto` mode divides by a denominator wrong by 20.3× to 336.7× on real published buildings.** A widened scan found 16 Warehouses at ≤210 m² fleet-wide; 6 sit at the literal placeholder. **First measurement: made** (this is it). ~~**What is not known:** whether (i) and (ii) are one defect or two — they overlap on 5 buildings but neither contains the other — and whether the 200.0 m² value is a constant in the source data or injected by an imputation path.~~ 🔵 **MEASURED 2026-08-12 (five-item sweep T01–T02) — two of the four unknowns are answered and one published claim above is retracted.** The 200.0 is **not** source data and **not** imputed: it is a declared fallback written by one cited line, `scripts/validation/v12_cell_pipeline.py:659`, which line 664 overwrites **only** on `status == "success"`. Stage 1 is clean — the real footprints (1,173–22,444 m²) are in `01_buildings.gpkg` and match their own `geometry.area`. **Face (ii) is a strict subset of face (i)**: the six placeholder rows and the six failed rows are the same six rows, so this is one defect, and the placeholder is simply what a failure looks like after the reporting stage. 🔴 **Retraction: the claim that six sit "inside the adopted `auto` fleet EUI" is wrong.** All six are `not_simulated` with `total_eui_kwh_m2 = NaN` and are excluded from both sides of the aggregation; **measured impact on 158.0 kWh/m² is exactly 0.000 (0.00 %)** against a baseline reproduced to 158.0298. **OPEN-42 is a reporting defect, not a baseline defect.** **What is still not known, and now blocks closure:** why the six simulations failed — `error_summary` is the **empty string** for all six. | Reported numbers + simulation correctness | 38 buildings; ~~**6 of them inside the adopted `auto` fleet EUI**~~ **0 inside the fleet EUI; 6 published rows carry a false area** | ✅ **both faces measured on all 40,800 runs**; ✅ **placeholder traced; fleet impact measured at zero**; ~~❓ **why the six failed is unrecorded**~~ ✅ **2026-08-13: cause found — all six die of runaway zone temperatures, and all six run clean under whole-building zoning, so this is a zoning-method defect. Open only on *why one mode survives*.** ✅ **2026-08-18 (T05): `.eio` read — positional pattern confirmed (15/16 fail on topmost floor, geometry byte-identical to non-fatal siblings below); two candidate statistics killed by a required 20-building background control; "not determinable from `eplusout.eio`" for the deeper question. Sharpens, does not close.** ✅ **2026-08-18 (T03): `.err`'s surface-orientation warning read — the lead named in fact 5 is retired. Fleet-wide rate 8,287/40,800 (20.3%) fully explained by the warning firing on 100.00% of all 8,160 `auto`-mode runs regardless of outcome (only 8 of which fail); all three control tests (fatal-vs-sibling zone, topmost-storey, mode comparison) came back negative or inverted. Candidate mechanism cited in code (`openubem/idf/surfaces.py:223-234,671-681`) but not fixed. Still OPEN — no further local artifact named.** ✅ **Ruling 2026-08-18: item REFRAMED, not closed — the question is no longer which zone is inverted but what is wrong with the topmost-storey geometry of these six buildings such that any zone built from it runs away; zoning mode only decides whether that storey gets a zone at all (`building`/`layout_assign` never zone it and never fatal). `.eio` and `.err` both exhausted; the E02 IDF corpus no longer exists on disk; no local next step named. OPEN-38 confirmed a separate mechanism — ruling accepted, both items stay separate.** **Closure note (T09, 2026-08-19, ruling R2): what OPEN-56 explains and what it does not.** OPEN-56's intervention is confirmed by control to cure all six of face (ii)'s fatal failures — writing `Zone.Volume` explicitly took all six from 9–39 severes to 0, six for six, volume warning 16/16→0/16. **Warehouses concentrate the fleet's fatal failures (13.68% vs 0.0443% elsewhere, 26/44 fleet fatals) because they are large-volume buildings**, and the stub's substitution error scales with the real computed volume (failures average −6,096 m³ vs −683 m³ for successes in the same cells) — so face (i)'s rate and face (ii)'s placeholder (written only on failure, traced 2026-08-12 to `v12_cell_pipeline.py:659/664`) are both explained by this one mechanism. **What OPEN-56 does NOT explain, named explicitly:** (1) the intervention was directly re-run on the 6 face-(ii) placeholder buildings only — the other distinct Warehouse buildings that fatal without the placeholder (face i minus face ii) were not individually re-run under the fix; their cure is inferred from the shared mechanism, not independently confirmed; (2) **OPEN-56's remedy is not authorised or implemented** — this closure records a mechanism finding, not a fix; (3) OPEN-56 explicitly does not claim the published `157.1`/`158.0` kWh/m² fleet EUI is wrong (infiltration is written `Flow/ExteriorWallArea`, not scaled by the stub), and these six remain confirmed at exactly 0.00% fleet-EUI impact (all six `not_simulated`/`NaN`, excluded from both sides of the aggregation); (4) OPEN-56's separate 2026-08-19 (T03) finding — `nyc_centre/relation_3566904`'s reported-area ÷4.18 anomaly — is a different building, not one of these six, and its fleet-wide uniqueness is unanswered; it does not affect this closure. **T01 of this same plan (2026-08-19) changed shipped code (`openubem/semantic/__init__.py`, the OPEN-55 B+ donor screen) — this closure does not depend on it.** **ID retired.** Full record: this item's own §-section; `extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §1; OPEN-56 §-section. |
| ~~**OPEN-43**~~ | **CLOSED 2026-08-12 on the user's ruling, formally retired 2026-08-13 on ruling `2h`. The headline is the POOLED figure — `157.1 kWh/m²` = total simulated energy ÷ total simulated floor area over all 8,154 successful buildings — and it must be restated with that definition every time. Do not re-ask which aggregation the headline uses.** Restated in 13 live files; archived trees left as record. ⚠️ **What the closure does NOT discharge, because it belongs to other items:** the published figure is still one HEAD cannot reproduce end to end (**OPEN-48**), and the re-run's **159.2157 is not a competing headline** — it is the same model run through **OPEN-49**'s `wwr` defect and survives only as evidence inside that item. ~~The original finding, kept for the record:~~ 🔵 ~~**The published fleet EUI is a mean of cell means, not a fleet mean.**~~ Found 2026-08-12 by the director while re-deriving the adopted headline two ways instead of one. Over the same 8,154 success rows: per-cell area-weighted means averaged across the 12 cells **weighted by building count** = **158.0298** — *this is the published 158.0*; weighted by success count = 158.0557; unweighted = 160.0993; **pooled `Σ(EUI × area) / Σ(area)` over all 8,154 at once = 157.0552.** The headline therefore sits **≈1.0 kWh/m² above** the pooled figure purely from the choice of aggregation, and the count-weights include the six buildings that produced no energy. Neither number is wrong — **but the published figure has never been described as a mean of cell means anywhere in this project**, and a reader will assume the pooled definition. `openubem/results/aggregator.py` is per-cell only, so the fleet roll-up lives outside it and its author and intent are untraced. **First measurement: made. Decision owed by the user: which definition the headline should use. Do not restate 158.0 before that ruling.** | Reported numbers | **every published fleet-level EUI figure**, including the headline and every board that quotes it | ✅ **all four aggregations computed on the full adopted run**; ❓ **intent untraced** |
| ~~OPEN-44~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | ✅ **0 failed · 1,859 passed · 55 skipped · 0 errors** (CP-1 signed). All 45 red nodes now skip with a reason naming their item; **passed did not move**, so nothing was deleted or downgraded. 🔴 **A skip is a debt, not a fix — the suite is honest, not more capable, and 14 of the 45 wait on OPEN-17.** ~~🔴 **The test suite has 70 failures and 36 errors, and this is the first time anyone could count them.**~~ Opened 2026-08-12 from the side effects of OPEN-13's fix. Full run: **70 failed / 1,822 passed / 10 skipped / 36 errors / exit 1 / 26m47s** — E-UTCI-12's collection abort had made this number unobtainable, so **every past claim that "tests pass" covered an unknown subset**. **61 of the 106 live in `docs/docs_DONE/…/elevators/scripts/tests/`** — `docs/` holds **30 `.py` files, 5 of them tests**, against the hard rule *no `.py` under `docs/`, ever*; two are byte-identical duplicates of `tests/` files and **three have drifted from their twins**. 🔴 **Roughly half the red is artifact-dependence, not broken logic**: **51 `FileNotFoundError`** from tests asserting an output file exists on disk, ~36 setup errors from a missing `synthetic_10_gdf` fixture, 5 `AttributeError` on a never-existent `config.IMPUTE_DEBIAS…`, 8 elevator-column `KeyError`s. **Do not report this as "70 broken tests."** ⚠️ The `IMPUTE_DEBIAS…` group is E-UTCI-12's shape a second time — **re-check OPEN-36's "one governance gap" bound before closing it.** **First measurement: made. Next step: triage the 44 `tests/` failures into real defects vs artifact-dependence — not yet done, and must not be guessed.** | Test integrity → **record integrity** | the whole suite; **every past "tests pass" claim**; ~~unknown overlap with shipped code~~ **measured overlap with shipped code: zero** | ✅ **counted and located**; ~~❓ **not triaged**~~ ✅ **2026-08-13: `tests/` fully triaged at HEAD and independently reproduced node-for-node — 26 failed / 1,857 passed / 10 skipped / 19 errors; 31 artifact-missing, 14 unfinished-wiring (→ OPEN-17, OPEN-36), 0 real defects** |
| ~~OPEN-45~~ ✅ **CLOSED + ID RETIRED 2026-08-13** | ✅ **Sweep re-run, zero live defects, no code changed — the correct outcome, named in advance.** The only single-space literal left under `openubem/` is inside `err_parse.py`'s own docstring describing the bug. ⚠️ The CSV on disk was **stale** until regenerated. ~~🔴 **The pipeline matched `** Severe **` with one space, so `error_summary` was empty for all 8,160 buildings** — not only the failures. Opened 2026-08-12. ✅ **Fixed where authorised 2026-08-12 (night):** a shared whitespace-tolerant helper `openubem/results/err_parse.py` (`SEVERE_RE`/`FATAL_RE`/`WARNING_RE`, `first_severe`, `count_severe`, `has_fatal`, 16 tests) now backs `scripts/validation/v12_cell_pipeline.py:625` and `scripts/cluster/make_manifest_from_cluster.py:47`; **load-bearing one-space sites 2 → 0**, director-verified from both diffs. 25 sites classified in `openubem/outputs/comparisons/open45_severe_literal_sweep.csv` (15 spent one-off scripts, 8 already correct). 🔴 **This item also corrected a project-wide belief: the "two spaces" rule is half wrong.** Census of every marker in all **64** real `.err` files: `** Warning **` one space both sides (**4,881**), `** Severe  **` one before / two after (**37**), `**  Fatal  **` two both sides (**1**) — **a two-spaces-both-sides literal misses `Severe` exactly as badly as the one-space literal did.** 🔴 **Why it stays open — two live sites, both flagged rather than edited because they were outside the executor's write-set:** `tests/test_sim_integration.py:171` matches `"**  Severe  **"` and therefore **0 of the 37** real Severe lines; `openubem/simulation/runner.py:140` is a bare `"**  Fatal  **"` literal rather than the tolerant helper. ⚠️ **A further gap in `SEVERE_RE` itself was self-disclosed by the OPEN-42 executor on 2026-08-13, confirmed real on a live file by the director, and routed here rather than to a new ID.~~ ✅ **Both "two live sites unfixed" are fixed at HEAD — verified 2026-08-13: `runner.py` and `test_sim_integration.py` both import from `err_parse` now.** | Reported numbers → **failure diagnosis** | **all 8,160 buildings' `error_summary`**; every future `.err` scan | ✅ **CLOSED 2026-08-13 — zero live defects, director re-derived by direct grep of the live tree** |
| ~~OPEN-46~~ | ⚠️ **The elevator end-use breakout existed only in the archived arc's copy of the code, never in the live tree.** Opened 2026-08-12. 🔴 **The premise's alarming half was REVERSED on audit the same night — read this before quoting the item:** elevator energy **is** in the adopted run and **is** inside the published `157.1 kWh/m²`. All 12 `phaseE_elevrb/*/05_results.csv` already carry `elevators_eui_kwh_m2` and `gwp_elevators_kgco2_m2`; **3,561 of 8,160 rows non-zero, Σ = 12,508.8 kWh/m²**; in `nyc_urban` exactly **87** non-zero — precisely the 87 elevator-eligible buildings; against the pre-elevator `phaseE` run the **median of `|Δtotal_eui − elevators_eui|` is exactly 0**. ⚠️ **Why both the executor and the director first got this wrong, recorded because the lesson transfers:** both read a flat `equipment_eui_kwh_m2` as absence — **flat is what de-folding produces.** **Check the invariant a transform preserves (the total), not the column it moves energy between.** ✅ **The reporting path is now restored and gated in the live tree** (parser, outputs, carbon, aggregator; director re-derived the invariant on a different SQL than the executor used — 12 keys bit-identical, total unchanged). 🔴 **The genuinely broken part was larger than the item as opened and was split out as OPEN-48.** ⚠️ Three of five archived test twins had the expectation **removed** rather than the feature added. ✅ **CLOSED + ID RETIRED 2026-08-18 (T01 of `implemenation/previous/PLAN_four-items-2026-08-18.md`).** The item's stated blocker ("the live tree still emits no elevator equipment") was stale — `builder.py` has wired `assign_elevators` since 2026-08-13. All four reporting-chain links (load → meter → parse/de-fold → carbon/aggregator) verified at HEAD by file:line citation and by passing tests: 65/65 targeted, full suite `1875 passed, 55 skipped, 11 warnings in 1572.28s (0:26:12)` matching the 1875/55/0/0 baseline. One documentary defect found and corrected: the plan-named proof test does not exist in the live tree and never has; `tests/test_builder_elevators_wired.py` (committed `6aeebb0`) proves the same load-wiring fact and passes. Full record: this item's own §-section. | Reported end-uses (**not physics**) | reporting only — **the published fleet figure is unaffected and was never missing elevator energy** | ✅ **premise measured and reversed; breakout implemented and gated; total proven invariant**; ✅ **2026-08-18: all four links verified at HEAD, 65/65 + full suite green, ID retired** |
| ~~OPEN-47~~ ✅ **CLOSED + ID RETIRED 2026-08-19** | ⚠️ **The office size-tier thresholds had no traceable external source, and this project's own deep-research document contains a fabricated citation.** Opened 2026-08-12. ✅ **The first half of the title is now wrong — a source WAS found:** the thresholds trace to **Chen, Hong & Piette (2017), *Applied Energy* 205, 323–335, Table 1** (DOI `10.1016/j.apenergy.2017.07.128`), **director-verified from the PDF itself** (pages 19–20 carry the three bins verbatim) and Crossref-checked, precisely because this task's predecessor fabricated exactly this kind of claim. **Hong et al. (2015) — credited by both the code comment and `RESULT_I02` — contains zero occurrences of either number**, 13 pages searched. ⚠️ **Caveat that must travel with the finding: Chen 2017's table is CityBES's own case-study classification, not a citation to an external standard** — it is not evidence of a DOE / PNNL / ASHRAE / CBECS lineage, and ASHRAE 90.1 is recorded as a **retrieval failure (paywalled), not** as "not found." 🔴 **Reason it stays open — a substantive divergence from the now-known source: the source's rule is area AND floor count** (`<2322 m² and ≤3 floors`, `2322–9290 m² and ≤5 floors`, `>9290 m² or ≥6 floors`) **while `openubem/semantic/building_classifier.py:175-177` tests area only.** Any change here is a classifier change and is therefore gated by CP-M3 (OPEN-31) — **and that gate depends on the unanswered fixture-threshold ruling 2a, so 2a probably has to be settled first.** ⚠️ The same citation audit found **a second fabricated DOI** (Sun et al. 2021 given as `10.1016/j.enbuild.2020.110586` — director-checked **HTTP 404**; the real one is `…110603`) and **a systemic wrong-locator pattern** across every Deru et al. (2011) row. ✅ **2026-08-19 (T03): the remaining question is ANSWERED — the floor-count divergence is sized at **598 buildings, every one a promotion, zero demotions** (380 Small→Medium, 161 Medium→Large, 57 Small→Large). Dropping the floor-count test therefore classifies offices **systematically smaller** than the source would. 🔴 **167 of the 598 (27.9 %) have no floor count at all**, so restoring the source's rule would make them depend on the imputed storey count **OPEN-35** exists to fix — sequence it after OPEN-35. Overlap with OPEN-35's changed set: **0**. ⚠️ §1 row reconciled: this table was stale against this item's own §-section, which recorded the citation question adjudicated on 2026-08-18. **No classifier change made.** ✅ **CLOSED + ID RETIRED 2026-08-19** on the user's ruling of 2026-08-19, as a **deliberate, documented departure** — the second of the two outcomes this item's own §-section names. 🔴 **No classifier change was made, and none was needed: the departure is already the user's own standing ruling of 2026-08-12**, recorded verbatim at `openubem/semantic/building_classifier.py:171-190`. T03's 2026-08-19 measurement did not contradict that ruling's stated reason — it **strengthened** it. `use_floor_count` stays available, default OFF, as the evidence for the decision rather than as a deprecated path.| Classification correctness → **citation integrity** | the office bins for every classified building; **every citation in `RESULT_I02`** | ✅ **source found and director-verified from the PDF; divergence located at the line**; ❓ **divergence not adjudicated — needs a ruling, gated behind 2a** |
| ~~OPEN-48~~ ✅ **CLOSED + ID RETIRED 2026-08-18 (late)** — its stated blocker was that no post-fix fleet re-run existed. One now does (`open48_refleet3`, twelve of twelve landed on frozen input, code the only variable), and its result is recorded: **the OPEN-49 fix moves classified buildings by under 0.08 %** (+0.0004 / +0.0001 / −0.0001, and −0.0906 / −0.0614 on the two cells with no Unknowns). The doubt that kept this item open is measured and dismissed; `157.0552` stays (CP-3). Evidence: `extra/MEASUREMENT_open-48_third-fleet-run.md`.~~ | ~~🔴 **The adopted baseline run cannot be reproduced from this repository.** Opened 2026-08-12 by **auditing OPEN-46's reversal**, not by running a task — the sixth consecutive pass in which this register grew that way. The adopted `phaseE_elevrb` run was produced by code that is not in this repository: live `builder.py` never called `assign_elevators` (`git log --all -S` empty; the only commit ever to touch the string, `ef19141`, added the **archived** copies plus three orphan live files), and `parser.py` / `outputs.py` / `carbon.py` had no elevator column, meter or GWP term — **yet the adopted outputs carry all of it.** The wiring existed in the working tree at run time and **was never committed.** ✅ **State the reassurance first: this is a provenance defect, not a physics defect — `157.1 kWh/m²` is correct and complete, elevators included.** ✅ **Half of it is discharged 2026-08-13:** ruling 2d ("restore the wiring, re-run the fleet") was executed, and the twelve-cell re-run **regenerates the elevator column exactly — 3,561 non-zero rows on both sides, same 8,160 buildings, same 6 known failures.** 🔴 **Why it stays open:** the re-run lands at **159.2157 vs the adopted 157.0552**, and the gap is **not** elevators but **OPEN-49**'s `wwr` re-randomisation. The user ruled 2026-08-13 to **keep 157.1**, so **the published figure remains one HEAD cannot reproduce end to end, and this provenance caveat stays live until OPEN-49 is fixed and the fleet is re-run a third time.** ✅ **2026-08-18 (T01 of `PLAN_open-48-and-four-items-2026-08-18.md`): the evidence table re-derived in full at HEAD — all five rows now the opposite of their 2026-08-12 values; both the load-wiring and reporting halves confirmed live and fully committed (`git status` clean); OPEN-49's mechanism fix also confirmed committed (`82bbd25`).** 🔴 **Remaining blocker narrowed, not resolved: no post-fix fleet re-run exists on disk (only `phaseE`/`phaseE_elevrb`), and the adopted run's own `01_buildings.gpkg` no longer exists — an execution gap and a data-provenance gap, no longer a code gap. STAYS OPEN.** | Reproducibility of **every published number** | the whole adopted baseline; **every figure this project publishes** | ✅ **measured on both sides of the tree; elevator half discharged by re-run**; ❓ **end-to-end reproduction blocked on OPEN-49**; ✅ **2026-08-18: table re-verified at HEAD, code-provenance gap fully closed, execution/data gap named** |
| ~~OPEN-49~~ ✅ **CLOSED + ID RETIRED 2026-08-19** | 🔴 **One reclassified building re-randomises the windows of every unidentified building in its cell.** Opened 2026-08-13 on the user's ruling (2f), found by the cause analysis of OPEN-48's re-run — **the seventh consecutive pass in which this register grew by checking a result rather than by running a task.** For buildings the classifier cannot identify, `wwr` is drawn **as one vectorised block sized by the count of unidentified buildings, with bounds taken from whichever archetypes happen to be present** (`openubem/semantic/__init__.py:229`, seeded by one RNG per run at `:297`). **`wwr` sets window head and sill height, which sets solar gain**, so buildings nobody touched — not reclassified, not re-fetched, not edited — move by up to **±300 kWh/m² individually**. 🔴 **The pipeline is reproducible only while its inputs never move** — a stronger and more damaging statement than OPEN-48's uncommitted wiring. **Measured on the twelve-cell re-run, not inferred:** all **4 of 12** cells whose `archetype_id` set changed **also moved in EUI** (`nyc_centre` +3.53, `austin_centre` +1.76, `la_centre` +1.60, `la_urban` +1.21); all **8** whose archetypes matched reproduced to **±0.07** or better; **0 cells on the wrong side of the split**. IDF diff: **6 cosmetic lines** for reproducing buildings vs **hundreds of window-vertex Z-coordinate lines** for moving ones. ✅ **Confirmed not to be nondeterminism** — a repeat run on unchanged inputs is byte-identical at the IDF stage and agrees to 0.00836 kWh/m² at the results stage. **Fleet effect: pooled 157.0552 → 159.2157 (+2.16, +1.4%)** — ⚠️ **retained as evidence inside this item only; 159.2157 is NOT the fleet figure and must never be restated as one.** ✅ **CLOSED + ID RETIRED 2026-08-19** on the user's ruling of 2026-08-19, **jointly with OPEN-55 and on OPEN-55's acceptance test** — the register's own condition was that the two resolve together, and they did. The mechanism fix of 2026-08-17 is now demonstrated end-to-end on real simulation output: `nyc_suburban`, 1,589 buildings, **0 failures**, archetype histogram **bit-identical** to baseline. 🟢 **Bit-identity is the direct evidence for this item specifically** — it is what per-building determinism predicts, and it is measured here on a freshly seeded, independently classified input rather than carried forward from an earlier attempt. ⚠️ **What the closure does NOT retract: 159.2157 is still not a fleet figure and must never be restated as one.** It was and remains evidence internal to this item.| Simulation correctness → **reproducibility** | **every `OpenUBEMUnknown` building in any cell where any classification moves**; blocks OPEN-48 from closing | ✅ **mechanism located at the line; effect measured on all 12 cells; nondeterminism excluded**; ❓ **no remedy chosen** |
| ~~OPEN-51~~ | ~~🔴 **One defect ID, `E-LA-16`, is used for two different failure signatures.**~~ ✅ **ADJUDICATED + CLOSED + ID RETIRED 2026-08-18 (T02).** Verdict: `E-LA-16` names the cooling-coil-design-UA/cooling-tower-UA-autosize family (`PLAN_structural-fixes_implementation.md:279`), corroborated by raw `.err` evidence on the three named buildings in the current E02 harvest (23/21/16 true Severes, corrected from an initial miscounted 26/24/19). The code comment's `CheckWarmupConvergence` grouping was a documentation error, now corrected. Knock-on: OPEN-09's C06 "five inherited log entries" narrows to four (E-LA-14/18/19/23); OPEN-29 unaffected. | Register integrity → **evidence provenance** | 1 defect ID; **OPEN-29's closure**; the reach of OPEN-09's C06 finding | ✅ **collision located, all four sources cited**; ✅ **2026-08-18: adjudicated, code comment corrected, knock-ons recorded** |
| ~~OPEN-52~~ | ~~🔴 **A fixed `--basetemp` makes two concurrent pytest sessions delete each other's temp directories.**~~ ✅ **CLOSED 2026-08-18 — ID RETIRED.** Opened 2026-08-13 by the director during T03, diagnosing a failure that would not reproduce. `pyproject.toml:54` pins `addopts = "--basetemp=.pytest_tmp"` — **fixed and repo-relative, not per-session** — and pytest clears that root at session start. **Observed, not theorised:** executor reported `1 failed, 6 passed in 12.67s` on `tests/test_sim_integration.py`; four sequential director runs gave **`7 passed` at 66.38 / 65.99 / 66.57 / 66.68s.** The failure was a vanished `step3` directory under `to_parquet` (`openubem/idf/builder.py:696-707`); three agents had been dispatched in parallel, all running pytest. The 12.67s-vs-66s gap corroborates it — the wall-time-dominant test never reached IDF generation. 🔴 **Recorded as a MANAGER error, not an executor error:** the report was accurate; the director parallelised over a configuration that cannot support it. **Mitigation in force is a discipline, not a fix** — every dispatch prompt now forbids concurrent pytest, which depends on the director remembering. ⚠️ **Anyone reading a non-reproducing test failure in this repo should check this item first.** **Bearing on any published number: NONE** — it corrupts test runs, never simulation output. | Test integrity → **trust in executor reports** | **every concurrent pytest session repo-wide**; every audit that reads a test result | ✅ **root cause at the line; non-reproduction measured 4× sequentially**; ~~❓ **no remedy chosen — why the path was pinned is unestablished**; 🔴 **2026-08-18 (T01): STAYS OPEN, sharpened to two sub-questions — (a) collision reproduced (real, remedy not yet applied), (b) a second, newly-found OS-level lockout on `pytest-of-o_iseri` blocks (a)'s specified remedy. Choosing a remedy shape is an owed user ruling, not a next measurement.**~~ ✅ **2026-08-18 (T01 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`): ruling `3a` given and implemented — `addopts` deleted, root `conftest.py` sets `PYTEST_DEBUG_TEMPROOT` to `<repo>/.pytest_tmp`, bypassing the locked `pytest-of-o_iseri` lockout entirely rather than repairing it. All four verifications passed with real output: (A) session lands at `<repo>/.pytest_tmp/pytest-of-<user>/pytest-<n>/`; (B) the locked directory's `LastWriteTime` is unchanged by the run; (C) negative control reproduced the collision on the old config (`FileExistsError`/`WinError 145`, run twice, same signature both times) and the positive control put two concurrent sessions in distinct `pytest-0`/`pytest-1` dirs with zero errors; (D) full suite alone, foreground: `1875 passed, 55 skipped, 11 warnings in 1079.75s` — exact baseline match. ~~**RECOMMENDED: CLOSE + RETIRE ID — not marked here; disposition left to the director.**~~ ✅ **RULED 2026-08-18 — recommendation ACCEPTED. CLOSED, ID RETIRED.** Director re-verified on disk, not from the report: no `addopts`/`basetemp` in any config file; root `conftest.py` present and setting `PYTEST_DEBUG_TEMPROOT`; and the two-session evidence survives as two durable log files naming `.pytest_tmp/pytest-of-o_iseri/pytest-1/test_busy_writer0` and `.pytest_tmp/pytest-of-o_iseri/pytest-0/test_busy_writer0`. The suite line is independently corroborated — the director watched PID 27104 run 14:43:44→15:01:51 (1,087 s wall against the quoted 1,079.75 s test time). 🔴 **Closure carries one condition: the remedy is an ~~uncommitted working-tree change (`conftest.py` untracked, `pyproject.toml` modified). Until both are committed, a fresh clone reproduces this item.~~** 🟢 **DISCHARGED 2026-08-18 (night): committed as `da6eed7` and pushed to `origin/main` (github.com/orcunkoraliseri/OpenUBEM), at the user's explicit instruction (*"tu fais aussi a toi-meme … pour open-52"*), which suspended the arc's standing git prohibition for this one commit. A fresh clone no longer reproduces the item.** Committed with `pyproject.toml` and `extra/FIX_open-52_temproot-remedy.md` in one commit. Evidence: `extra/FIX_open-52_temproot-remedy.md`.** |
| **OPEN-53** | 🔴 **874/875 E02 harvest directories are missing `.sql`/`.end`, concentrated in two Austin sub-cells.** Opened 2026-08-18, found as a byproduct of T03's `.eio` census run for OPEN-37. Against **40,800** `n_building_dirs` and **40,800** `.eio`/`.err` (both exact, zero empty), `.sql` = **39,926** and `.end` = **39,925** — short by 874/875. Every short directory still carries its `.eio` and `.err`, so this is **not** OPEN-37's problem — ~~it is an incomplete-simulation signature~~ **it is a batch-scoped harvest gap, not an incomplete-simulation signature (T02, 2026-08-18): 874/875 report `EnergyPlus Completed Successfully`, 0 fatal, indistinguishable from a 200-directory healthy control (100% completed).** **874 of 875 concentrate in `austin_suburban_fast_zone`/`austin_suburban_floor` (100% of both, all other modes for the same buildings fully populated); the remaining one is `nyc_centre_fast_zone`, truncated mid-input-processing.** ~~No `.err` content from these specific directories has been read yet.~~ | Reported numbers → **run completeness** | up to 875 E02 harvest directories, two Austin sub-cells + one NYC directory | ✅ **census counted, location established**; ✅ **T02 2026-08-18: `.err` read for all 875 + 200-directory control — genuine EnergyPlus failure retired (0 fatal); harvest-artifact vs IDF-output-config not distinguishable from this artifact; 1 exception (`nyc_centre_fast_zone`) not determinable from `.err`**; ✅ **Ruling 2026-08-18 (CP-1): original question ANSWERED — files were produced, harvested and inventoried 2026-08-11, then deleted by a process outside this repo at 2026-08-17 16:21, which also emptied the whole E02 IDF corpus; no published number affected. STAYS OPEN, narrowed to the custody risk — nothing prevents recurrence, and `e02_corpus_inventory.csv` (2026-08-11) is now falsified by disk for two rows and must be read as a snapshot, not current state.** ⚠️ **2026-08-18 (overnight, X06): custody exposure quantified — 152.4 GB across three corpora, 145 GB of it `.sql`, none yet carrying the 2026-08-17 16:21 sweep signature. Under 0.12 GB preserves every finding this arc cites; the 76 GB of `.sql` is the bait and is re-derivable. And "E02 is gone" is too strong — its parquet manifests survived.** |
| ~~OPEN-54~~ | ~~🔴 **`_ssh` never checks the remote exit code**, so a failed remote command surfaces late, somewhere else, with the evidence already discarded. Opened 2026-08-18; four call sites fired in one run; it misclassified two model stops as transport failures.~~ ✅ **REMEDY IMPLEMENTED + CLOSED 2026-08-18 (late)** — `_ssh` raises `RemoteCommandError` on a non-zero remote exit and on `TimeoutExpired`; `allow_fail=True` is the explicit opt-out; the `squeue \| wc -l` false-success path now requires positive `sacct` corroboration before concluding completion. Nine local tests pass, none of them touching the cluster; the `bash -lc` tcsh wrapper is asserted by a test so a future refactor cannot drop it. **ID retired.** | Cluster transport | every cluster run | ✅ **fixed and tested** |
| ~~OPEN-55~~ ✅ **CLOSED + ID RETIRED 2026-08-19** | 🔴 **The OPEN-49 fix widened the Unknown PDE bounds to the full archetype table, so an unidentified building can draw a data centre's equipment load** — 5 381.96 W/m² against 5–20 for an ordinary building. With a uniform draw the maximum sets the **centre**, not the tail: the median Unknown equipment draw is **2 692.27 W/m²**. Opened 2026-08-18. Dose-response confirmed over eleven bins, 0.000 → 1.000; **not one of 3,078 classified buildings failed**. Measured cost: the Unknown path lifts run 2's fleet figure by **+4.058 kWh/m² (+2.615 %)**. ✅ **RULED (user, R1, 2026-08-19): Option B+ — and IMPLEMENTED the same day (T01).** The four data centres, `Laboratory`, `FullServiceRestaurant` and `QuickServiceRestaurant` are excluded from the Unknown donor pool on every PDE column; `Warehouse` additionally on occupancy. Donor pool **29 → 22** rows; equipment bounds **`[2.58, 5381.96]` → `[2.58, 16.15]`**, median **9.37 W/m²**. Ten new tests; suite **1885 passed, 55 skipped**. 🔴 **NOT CLOSED — the proposal's own falsifiable test has never run.** T02 (`nyc_suburban`, 71 divergences → 0) was attempted **three times and simulated ZERO buildings**; the prediction is neither confirmed nor falsified. Blocked by **OPEN-57**. ✅ Control 1 (non-vacuity) passed on attempt 3's own artifacts: **0/290 Unknown rows exceed the new ceiling** (min 2.590 / median 9.153 / max 16.067). ✅ **CLOSED + ID RETIRED 2026-08-19** on the user's ruling of 2026-08-19. 🟢 **The item's own pre-registered, falsifiable acceptance test finally RAN and PASSED, on the fourth attempt** — the first three simulated zero buildings and proved nothing. `nyc_suburban`, 290 Unknown buildings, frozen input MD5 `1198ed01bfd3b4463e50da0ae39d8e27`, job 1274983: divergences **71 → 0**. The prediction was *substantially below 71*; the measured value is the floor of that range. All three controls passed — classification unchanged (histogram bit-identical), 0 failures among the 1,299 classified buildings, 1,589/1,589 simulated. Median Unknown equipment draw **2,692.27 → 9.15 W/m²**. 🔴 **Director's audit of that same run found what the acceptance test was not looking for, and it is NOT covered by this closure:** the equipment screen worked — Unknown buildings now draw **less** equipment energy than classified ones (median 37.5 vs 43.4 kWh/m²) — **yet Unknown buildings still finish at 1.7× classified overall** (median total 349.4 vs 202.8). The gap **moved**, it did not close: it is now driven by DHW (+61.0), heating (+41.1), lighting (+22.7) and cooling (+20.5) kWh/m². **Opened as OPEN-59.** This item closes on its own stated condition, which was about divergences, not about the level of Unknown demand.| Reported numbers | 650 Unknown buildings, 3.7 % of floor area | 🔵 **measured; ruled; implemented; UNPROVEN IN SIMULATION** |
| **OPEN-56** | 🔴 **Every building in the fleet simulates with its zone air volume replaced by a 10 m³ stub.** EnergyPlus computes a **negative** volume from the geometry we hand it (`Indicated Zone Volume <= 0.0`, floors and ceilings wound the wrong way) and substitutes 10 m³. Opened 2026-08-18 (late) while looking for OPEN-42's mechanism. **8 160 / 8 160 = 100.00 %** of run 2, re-confirmed in run 3; **control: 0 / 2 on DOE-prototype geometry**, so it is our geometry, not EnergyPlus. OPEN-42's six failures are its extreme tail — failures average **−6 096 m³** computed volume against **−683 m³** for successes. ⚠️ **No claim is made that the published 157.1 is wrong**: infiltration is written `Flow/ExteriorWallArea`, not air-changes-per-hour, so it is not scaled by the stub, and the effect on annual EUI is **unmeasured**. | Simulation correctness | **all 8,160 buildings** | 🔵 **mechanism measured;** ~~writer not yet localised~~ ✅ **WRITER LOCALISED — tag corrected 2026-08-19 at CP-1 of `implemenation/PLAN_twenty-items-2026-08-19.md`** (this tag was already stale against this item's own §-section, and a task written from it found its premise false; see §1's CP-1 amendment). The winding is written by `geomeppy==0.12.2` and **its own corrector `set_entry_direction` is a provable NO-OP for our GGR convention** — `is_clockwise` is self-referential, testing against a point built from the same normal, so it returns `False` unconditionally and never inverts either winding. **Verified twice by the director independently of the executor**, by inspection and by execution on a CW- and a CCW-wound square. The IDF winding is therefore the **input footprint's own orientation**, and the one `orient()` call that exists (`openubem/idf/builder.py:464-465`) is gated `if resolution_mode != "auto"`, so it **never fires for the adopted baseline mode**; 0/20 sampled source footprints are CCW, matching the 100 % rate. **A THIRD remedy shape now exists: extend `orient()` to `auto` (sign unverified), alongside writing `Zone.Volume`. Neither applied — the remedy ruling is still owed to the user.** 8,160/8,160 (100.00 %) re-confirmed on run 4. ✅ **2026-08-18 (overnight, X01/X02): THE FLEET-SCALE COST IS MEASURED — 69 buildings, all twelve cells, control whole (70/70 baseline volume warning → 0/70 treated, 70/70 completed both arms). Mean +0.98 %, median +0.84 %, 65/69 same direction. The per-zone model is REFUTED (corr 0.113); it is a fixed per-BUILDING offset of ≈ +1.0 kWh/m². 157.1 deliberately NOT restated. ~~New lead: on 1 of 60 the treatment also moved the reported floor AREA by 4.18×.~~ 🔴 **RETRACTED 2026-08-19 (CP-1, T05): a FALSE LEAD.** Untouched production run-4 data gives `relation_3566904` `footprint_area_m2 = 2,682.23`, `levels = 14`, `floor_area_m2 = 37,551.22` — ratio **1.000001**, no anomaly at all. The 157,115 m² belongs to a different building, `relation/11171793`, and reached this experiment through **OPEN-58's `run_ep()` shared-cwd cross-contamination** — an independent second confirmation of OPEN-58's verdict from data that never touched the defective helper. Remedy still unauthorised.** |
| ~~OPEN-50~~ ✅ **FIXED + ID RETIRED 2026-08-13** | ✅ **The fixture now writes to `tmp_path_factory`, not to `tests/fixtures/`.** Proved by hash + mtime taken either side of a **24-minute** full suite run — **neither moved.** 🔴 **One user action outstanding: `git restore` the still-dirty working copy of that fixture.** ~~🔵 **Running the test suite silently rewrites a checked-in fixture.**~~ Found 2026-08-13 by the director during the CP-1 `git status` audit — a sixth item found by auditing an output, not by a task that went looking. `tests/test_building_classifier.py` opens `tests/fixtures/synthetic_30_archetype_coverage.gpkg` read-write, so GDAL/SQLite stamps `last_change` on every run. **Reproduced in isolation from a clean tree** (restore → 131 tests pass → fixture dirty). ✅ **Scope proved by hashing every table's full row set on both copies: all tables identical except the 1-row `gpkg_contents`, and within it exactly one field — `last_change`.** The 11,400 differing bytes are SQLite page churn, not content. 🔴 **The real cost: one such rewrite is already committed — `6aeebb0` carries `Bin 106496 -> 106496` on this fixture, so a test artifact entered the history looking like a deliberate change.** ⚠️ **Standing consequence: a dirty copy of this fixture after a test run is expected and must never be read as an executor writing outside its authorised set — verify by row hash, not byte diff — and must not be committed.** | Repo + audit-trail hygiene | 1 fixture; **every future `git status` audit of an executor** | ✅ **reproduced in isolation; scope measured to one metadata field; prior accidental commit identified** |
| ~~OPEN-57~~ ✅ **CLOSED + ID RETIRED 2026-08-19** | 🔴 **`_ssh` intermittently faults with `Unmatched '.` on the `_remote_results_complete` probe, and it has now blocked the OPEN-55 acceptance test twice.** Opened 2026-08-19 by the director on T02's own recommendation. Two independent occurrences, same code path (`scripts/validation/v12_cell_pipeline.py:1082` → `:1014`), same `nyc_suburban` 1,589-entry osm_id list, **two different remote fleet directories**, near-identical command lengths (**23,171** chars in attempt 1; **23,166 / 23,177 / 23,213** in attempt 3 depending on whether the probe body, the `bash -lc` wrapper or the full `ssh` argv is measured) — all far under Windows' ~32,767-character `CreateProcess` cap, so **length is not the explanation.** Attempt 3 was fully instrumented: exit code **1** captured to disk the second the child died, append-only logs, 60s heartbeat, fresh remote dir verified absent before *and* after. Remote stderr, verbatim and complete: `Unmatched '.` — one line, nothing else. ⚠️ **This is the OPEN-54 fix working as designed** — `_ssh` now raises instead of silently continuing, which is why the fault is visible at all; OPEN-54 stays closed. **Cost so far: three attempts, each discarding ~3–4 min of successful local work (1,589/1,589 IDFs, LIVE_SMOKE both gates PASS) at the first remote call.** ✅ **RESOLVED 2026-08-19 (T02–T05) — not transient, and TWO faults, not one.** (1) Deterministic remote-command length limit: **565 ids parse, 566 do not**; the first failing wrapper is **8,191 B — one byte below 8,192 — and fails anyway**, so the boundary is **not** 8,192 and no round number matches. Content proved innocent; length alone. (2) After moving ids to stdin the probe **still read 0/226 against a real, populated fleet** — `subprocess.run(text=True, input=…)` rewrites LF to CRLF **on Windows**, so every id reached the remote loop with a trailing carriage return and every path test silently failed. Invisible on Linux; returns a clean, plausible, wrong answer. Remedy in `_ssh` only (stdin + raw bytes); `stdin_data=None` byte-for-byte unchanged; OPEN-54's raise preserved. ✅ **Live: 225/226 — the exact figure already on record.** Suite **1,896 / 55**. ⚠️ Closure recommended, **not taken**; OPEN-55's acceptance test **NOT run**. ✅ **CLOSED + ID RETIRED 2026-08-19** on the user's ruling of 2026-08-19 (*"fermer toutes en exécutant"*). Two faults, both found, both fixed in `_ssh` only, and the fix **verified live at 225/226** against the exact figure already on record for that cell. The blocked acceptance test it names is dispatched under `implemenation/previous/PLAN_close-all-2026-08-19.md`.| Cluster transport | **every cluster run**; currently blocking OPEN-55's acceptance test | 🔵 **reproduced twice, instrumented, cause not established.** ⚠️ **Amended 2026-08-19 (director): "transient" is NOT established** — the archived logs cannot distinguish a working probe from a swallowed failure (`0/N` is both), so the only call ever proven to run carried **226** ids and no large-list call is proven to have worked. **The length ruling tested Windows' argv cap, but the failing parse is tcsh's, on the remote host** — `Unmatched '.` is tcsh's own error for an unclosed quote, and tcsh's buffer was never measured. A cheap, login-node-safe threshold test is named in the §-section. No remedy attempted; no fourth retry authorised. |
| **OPEN-58** | 🔴 **`open56_zone_volume_experiment.py`'s `run_ep()` helper has two defects, and any earlier local batch result that imported it is exposed to both.** Opened 2026-08-19 by the director; found by **T04's own controls**, not by a task that went looking. (a) EnergyPlus `-x` lets outputs **cross-contaminate between buildings that share a working directory** — caught as two byte-identical `.sql` files for two different footprints. (b) It reads EUI by a formula that **does not match production's `total_eui_kwh_m2`** (`openubem/results/parser.py`), which sums per-end-use EUIs over a multiplier-aware `.eio` area rather than dividing Total Site Energy by Total Building Area. ✅ **T04 voided its own first full run and re-ran clean rather than patching the numbers** — its published `_results_v2.csv` is unaffected. ⚠️ **Explicitly NOT scoped to OPEN-35**, whose amendment records it: the question is which *other* results imported this helper. ~~**No audit of the blast radius has been done.**~~ **— stale tag, struck 2026-08-19 at CP-1 of `implemenation/PLAN_twenty-items-2026-08-19.md`; the audit is recorded later in this very row and in this item's §-section, and a task written from this sentence found its premise false at HEAD.** ✅ **Re-derived independently at CP-1 by a disk walk** (correctly chosen: the origin file and its real importers are **untracked**, and a tracked-files-only `git grep` was tested first and found only 5 of the 8 files) — **exactly reproduces the existing count: 3 real importers, 4 name-collisions, 1 origin, 8 total.** ✅ **BLAST RADIUS MEASURED 2026-08-19 (T06–T08): 3 real importers, 6 descended artifacts, 1 unsound row, 0 unverifiable.** 🔴 **This item's own stated mechanism was wrong:** defect (a) is **not** a shared `-d` outdir — every importer already passes a unique one — it is EnergyPlus's `-x` step working relative to the **shared process cwd**, so all three importers are exposed and **concurrency is not the discriminator**. One confirmed contamination in 166 recomputed cells (`nyc_centre/relation_3566904` carrying `relation_11171793`'s results — identical to **fifteen significant figures**); already excluded from the pooled statistic, but for a **wrong stated reason**. ✅ **Zero cited figures corrupted** — defect (b) shifts absolute EUI up to −24 % but every cited number is a **relative** change on the same building, which cancels. Still open; **no remedy authorised**.| Simulation correctness → reported numbers | unknown — every local batch result that imported `run_ep()` | 🔵 **both defects reproduced and understood; blast radius unmeasured.** No remedy authorised. |
| **OPEN-59** | 🔵 **REFRAMED 2026-08-19 (late, director) — this is a CALIBRATION item, not a bounds defect. Hypothesis 1 is REFUTED by direct measurement:** T02 of `implemenation/PLAN_gap-decomposition-2026-08-19.md` screened **all four** drawn PDE columns for **all 290** `OpenUBEMUnknown` buildings against their donor bounds — **0 of 4 columns, 0 of 290 buildings, out of bounds**, worst excursion **0.0** on every column (`openubem/outputs/comparisons/open59_pde_bounds_screen.csv`). **This is NOT OPEN-55's sibling** — the draws are all legal, so no column-wise screen can fix it. **Hypothesis 2 stands by elimination:** the Unknown donor pool is genuinely higher-intensity than the buildings it stands in for, which makes the remedy a **different donor pool or better classification**, not a bounds fix. **Kept open under its own ID rather than closed** — the phenomenon is real and unexplained; only its diagnosis changed. ~~🔴 **With the Unknown equipment defect cured, Unknown buildings still use ~~1.7×~~ more than classified buildings — the gap moved from equipment to hot water and heating.** ⚠️ **The `1.7×` is a MEDIAN-PER-BUILDING statistic measured on `nyc_suburban` alone, and this row must carry both weightings — corrected 2026-08-19 at CP-1 of `implemenation/PLAN_twenty-items-2026-08-19.md`, measured fleet-wide on run 4.** **Floor-area-POOLED: Unknown 107.22 vs classified 155.56 — Unknown is 31 % BELOW.** **MEDIAN-PER-BUILDING: Unknown 309.95 vs classified 134.08 — Unknown is 2.31× ABOVE.** 🔵 **Both are real and they disagree for a traced reason, not an error:** the top 10 of 650 Unknown buildings hold **72.5 %** of all Unknown floor area and run at moderate EUI (r = **−0.27** between Unknown floor area and EUI), so area-weighting is dominated by a few large moderate buildings while the *typical* Unknown building is small and hot. **Never quote one without naming its weighting.** Fleet-wide the largest end-use multiple is **DHW at 10.2×**, ahead of heating (3.4×); `nyc_suburban`'s lighting **6.7× does NOT generalise — it is 1.00× fleet-wide.** Fleet Unknown population: **650 buildings, 3.7 % of fleet floor area.** Opened 2026-08-19 by the **director's audit of OPEN-55's passing acceptance test**, not by a task that went looking for it — the test asked only whether divergences fell, and they did. 🟢 **The OPEN-55 screen is confirmed to have worked, and this item does not reopen it:** Unknown equipment demand is now *below* classified (median **37.5 vs 43.4 kWh/m²**). 🔴 **But total demand did not follow.** `nyc_suburban`, 290 Unknown vs 1,299 classified, medians: **total 349.4 vs 202.8 kWh/m² (+146.6, 1.72×)**, DHW **103.5 vs 42.5 (+61.0)**, heating **140.1 vs 99.0 (+41.1)**, lighting **26.7 vs 4.0 (+22.7)**, cooling **25.0 vs 4.5 (+20.5)**. The lighting and cooling ratios (6.7× and 5.6×) are the largest multiples and are the natural first place to look. ❓ **Cause not diagnosed and no remedy proposed** — it is not yet established whether the Unknown donor pool is genuinely higher-intensity than the buildings it stands in for, or whether the same widened-bounds pattern OPEN-55 found in the equipment column also affects the DHW, lighting and occupancy columns, which would make this OPEN-55's sibling rather than a new phenomenon.~~ | Reported numbers | **every `OpenUBEMUnknown` building in every cell** — 18.3 % of `nyc_suburban`; fleet-wide share and fleet EUI effect **not yet measured**, commissioned as part of T04 | 🔵 **measured on one cell; cause unknown; fleet effect unmeasured** |
| **OPEN-60** | 🔴 **`total_eui_kwh_m2` undercounts Interior Lighting and Interior Equipment whenever a zone carries a multiplier > 1 — every `layout_assign` EUI this project has ever recorded is too low.** Opened 2026-08-19 by the **director**, on a reconciliation control run by T01 of `implemenation/PLAN_gap-decomposition-2026-08-19.md` — **not by a task that went looking for it.** **Mechanism, traced and not inferred:** those two end uses are summed from per-zone hourly variables, which EnergyPlus does **not** scale by the zone multiplier, while the floor-area divisor **is** multiplier-aware (`openubem/results/parser.py:431-433`, `resolve_simulated_floor_area()`). Every other end use — cooling, heating, fans, pumps, hot water — matches the multiplier-correct ABUPS table to **<0.01 %**. **Size, n=48 untrimmed `layout_assign` buildings:** only **6 of 48** reconcile within 2 %; error median **4.71 %**, mean 17.56 %, p90 24.19 %, **max 192.28 %**; **14 exceed 10 %**. 🟢 **No adopted number is affected, and this was verified rather than assumed:** zone multipliers are written in exactly one module (`openubem/geometry/layout_assigner.py`, `match_storeys()`, `:649`), which the `auto` production path never calls, and three run-4 `auto` fleet IDFs were read directly — **every `Multiplier` field is 1**. **153.8231 kWh/m² pooled over 8,153 buildings is untouched.** 🔴 **The gate that catches this already exists and the fleet pipeline never calls it** — `check_building_integrity()` (`parser.py:602-646`) returns `abups_ok=False` for the worst offender, and is called by `scripts/run_r1_t12.py:211`, `run_r3_fleet.py:313`, `run_r3_step5.py:204`, `run_t12_boston.py:198`, but **not** by the path that produced `05_results.csv`. ❓ **Remedy not proposed and not authorised** — two shapes exist (sum the two end uses from ABUPS as the other five already are, or make the per-zone sum multiplier-aware) and choosing between them is feature code, which this session does not write. | Reported numbers | **every `layout_assign` EUI ever recorded**, including OPEN-03's and OPEN-18's published sample figures, which were corrected 2026-08-19 the same night; **zero adopted rows** | 🔴 **mechanism traced, size measured on n=48, blast radius bounded to a non-production mode** |

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
~~**Next free item ID: `OPEN-54`.**~~

**Amended 2026-08-18 (late, during the OPEN-48 third fleet run): `OPEN-54` was taken by the
unchecked-`_ssh`-exit defect in `v12_cell_pipeline.py`, found the hard way when `nyc_centre` lost
43 minutes of correct work to a silently-failed remote `mkdir`. Opened with its §10 section in the
same edit, on the user's instruction to investigate the failure in detail. No defect ID was opened;
`E-LA-42` and `E-UTCI-17` are unchanged.
~~**Next free item ID: `OPEN-55`.**~~

**Amended 2026-08-18 (late, same run): `OPEN-55` was taken by the PDE-bounds regression — the
OPEN-49 fix widened the Unknown-building draw to the full 29-archetype table, so Unknown buildings
now draw equipment power density up to `LargeDataCenterHighITE`'s **5381.96 W/m²** and diverge in
EnergyPlus. Found when `nyc_suburban` stopped on 71 divergences that run 2 did not have, on
byte-identical input. Opened with its §10 section in the same edit. No defect ID was opened;
`E-LA-42` and `E-UTCI-17` are unchanged.
**Next free item ID: `OPEN-56`.**

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

🔴 **CP-2 RULING, 2026-08-20 (director) — THE CENTRAL CLAIM OF THIS ITEM IS REFUTED. Everything above about the *size* of the vintage contribution is superseded.** Full working: `../extra/MEASUREMENT_open-03_load-elasticity.md` §CP-2; data `openubem/outputs/comparisons/open03_load_source_decomposition.csv`.

**The experiment produced a control nobody designed.** A ±30% perturbation of `lighting_w_m2`/`equipment_w_m2` over 20 buildings reached only **4 of 20**. The reason is structural: `layout_assign` has two internal-load paths (`openubem/idf/builder.py:69-83`, `:228-236`). Archetypes with a mapped `STD2022` baseline IDF (here `SmallOffice`×13, `MediumOffice`, `RetailStandalone`, `Warehouse`) take the baseline's **own native densities** and **never call `assign_loads()`**; archetypes without one (`OpenUBEMUnknown`×3, `Courthouse`) build from the template and read the **same archetype load table `auto` reads**. So the sample splits into 16 buildings whose internal loads differ between modes and **4 whose internal loads are provably identical**.

**Measured, pooled by floor area:**

| subset | n | `auto` EUI | `layout_assign` EUI | gap | internal-load drop | share of gap explained |
|---|---|---|---|---|---|---|
| all 20 | 20 | 170.14 | 129.45 | **−23.91%** | +3.52 kWh/m² | **8.0%** |
| from-scratch (loads identical) | 4 | 204.14 | 155.94 | **−23.61%** | **−0.00 kWh/m²** | **0.0%** |
| prototype-baseline path | 16 | 115.09 | 86.56 | −24.79% | +9.23 kWh/m² | 29.9% |

🔴 **The four buildings whose internal loads are bit-identical between the two modes still show a −23.61% gap**, indistinguishable from the −24.79% of the sixteen whose lighting differs by a factor of 2.6. **Internal loads explain zero percent of the gap in the one subset where they are held constant, and the gap does not shrink.** The −23.91% pooled over all 20 reproduces the independently established **−23.93%** to two decimals — the control on the whole calculation.

**Delivered-energy ratios, `layout_assign` ÷ `auto`:** prototype-path lighting **0.386** (median), equipment 0.945; from-scratch lighting **1.000**, equipment **1.000**.

**Three consequences.**
1. **"Roughly half" is refuted.** ≈8% pooled, ≈30% even among buildings where the mechanism operates at all. Consistent with — and sharper than — the 7.76% arithmetic bound withdrawn on 2026-08-19 for using the wrong denominator.
2. **The premise was wrong, not just the size.** Both modes are vintage-blind. **No era-dependent loads table would close this gap**, and none exists in the repo to build one from. Do not commission one on this item's account.
3. **The item stays live, with its scope replaced.** ~92% of a −23.9% cross-mode gap is unexplained and is now known **not** to be internal loads. **Cheapest next attack, and it needs no new simulation:** an end-use diff on the 4 from-scratch buildings, where loads, archetype and weather are identical across modes, so the entire −23.61% must live in geometry, zoning, envelope or HVAC sizing. Both runs already exist on disk.

**Superseded by this ruling:** the elasticity inversion `k ≈ 1.4–2.1×` reported at T03. It was computed on the 4 from-scratch buildings — exactly the subset with **zero** load-driven gap — so it inverts a mechanism that is not operating there. The elasticity itself (**0.21–0.29**, linear across ±30%, −30% and +30% agreeing to a ratio of 1.02) is sound and supplies the HVAC damping factor: heating rising as lighting falls offsets ~17% of the gross internal-load change, ~7.4% net on the total.

**Method lesson recorded here because it nearly cost the result:** the plan's CP-1 gate tested **one** building, and that building happened to be one of the 4 reachable ones, so the gate passed while the intervention was inert in 16 of 20. **A single-building control cannot establish that an intervention reached a population.** Future perturbation plans must gate on the count of responding buildings, not on one exemplar.



**Amended 2026-08-19 (late, **director**, at CP-1 of `implemenation/PLAN_layout-assign-untrimmed-2026-08-19.md`).** 🟢 **The measurement-capability defect blocking this item is cured and now demonstrated at scale, not at n=1.** 48 buildings — 4 per cell × 12 cells at the 10/35/65/90th percentile positions of `footprint_area_m2`, run-4 (`open48_refleet4`) fixtures, rebuilt in `layout_assign` with **`trim_outputs=False`** as the only variable changed — **all 48 parsed `success`: 0 build failures, 0 simulation failures, 0 parse failures**, across 12 cells, 9 archetypes, 1–18 storeys and 1–90 zones. `trim_outputs=False` is the whole fix; nothing else blocks `layout_assign` from yielding a production-parser EUI. This retires the cross-cutting blocker recorded at CP-3 of the twenty-item plan (T15/T18/T20a). 🔵 **The cross-mode gap is reproduced at HEAD, generation-clean, for the first time — as a SAMPLE number: pooled −26.25 % (108.64 vs 147.30), median per building −24.40 %, n=48.** Pooled and median agree in sign and within 2 points, so there is no OPEN-59-style weighting disagreement to adjudicate. **47 of the 48 sit below `auto`**; the sole exception is `austin_rural way/1165379866` (RetailStandalone) at +2.67 %. This corroborates the historical −29 % median figure this item was opened on. 🔴 **The floor-area confounder (OPEN-10) inflates the gap but is NOT its cause.** Splitting on a >10 % denominator disagreement: the 21 area-agreeing buildings pool to −19.73 % / median −25.87 %, and that pooled figure is **75 % carried by one 88,309 m² Courthouse** — excluding it, the other 20 pool to **−28.02 %** / median −26.05 %. A real energy-side difference of order **−25 %** survives after the confounder is removed. ⚠️ **What this does NOT do: it does not test this item's actual claim.** The attribution of *roughly half* the gap to 2022-code internal loads is untouched — that needs a vintage-patched-loads rebuild, which was not run and was not in scope. The item's size is neither confirmed nor revised here. 🔵 **Disk cost of running untrimmed, measured for the first time:** `.sql` mean **20.0 MB**, median 8.1, max 124.9 (the 90-zone Courthouse), ≈**1.40 MB per zone** → a full-fleet untrimmed pass at 8,160 buildings implies ≈**159 GB**, well under the >800 GB the register records for untrimmed `fast_zone` city passes. **Whether to run one is the user's decision and is not taken here.** Evidence: `extra/MEASUREMENT_open-03-18_untrimmed-sample.md`; tables `openubem/outputs/comparisons/open03_untrimmed_sample_{eui,join}.csv`. **NO item opened, closed, struck or retired; 19 live / 40 struck / 59 total, next free `OPEN-60`, invariant *struck − retired = 2* untouched. `153.8231 kWh/m²` pooled over 8,153 is not reopened, changed or restated.**

🔴 **CORRECTED the same night (2026-08-19), by the director, at CP-1 of `implemenation/PLAN_gap-decomposition-2026-08-19.md` — the amendment immediately above OVERSTATES the gap and its figures are superseded by these.** The follow-on end-use decomposition found that the parser figure the amendment rests on, `total_eui_kwh_m2`, **undercounts Interior Lighting and Interior Equipment whenever a zone multiplier exceeds 1**: those two end uses are summed from per-zone hourly variables, which EnergyPlus does not multiplier-scale, while the floor area they are divided by **is** multiplier-aware (`openubem/results/parser.py:431-433`, `resolve_simulated_floor_area()`). All other end uses match the multiplier-correct ABUPS table to <0.01 %. **42 of 48 affected; only 6 of 48 reconcile within 2 %; reconciliation error median 4.71 %, mean 17.56 %, max 192.28 %, and 14 buildings exceed 10 %.** ⚠️ **The production gate that catches this already exists and the fleet pipeline simply never calls it** — `check_building_integrity()` (`openubem/results/parser.py:602-646`) returns `abups_ok=False` for the worst offender; several `scripts/run_*.py` entry points call it, the path that built these tables does not. ✅ **The adopted fleet figure is NOT affected, verified rather than assumed: zone multipliers are written in exactly one module, `openubem/geometry/layout_assigner.py` (`match_storeys()`, `z_obj.Multiplier = residual_multiplier` at `:649`), and the director inspected three run-4 `auto` fleet IDFs directly — every `Multiplier` field is 1. `153.8231 kWh/m²` pooled over 8,153 stands untouched.** The corollary is that **every `layout_assign` EUI this project has recorded is undercounted by this mechanism** — a `layout_assign`-only defect in a mode not on the production path. 🔵 **Corrected sample figures (n=48, multiplier-correct via ABUPS totals): pooled −11.26 % (was −26.25 %), median −17.72 % (was −24.40 %); area-agreeing subset n=21 pooled −17.39 % / median −22.60 %; excluding the dominant Courthouse, n=20 pooled −23.93 % / median −23.19 %; 8 of 48 now sit above `auto`, not 1.** **§4's conclusion holds and is cleaner than before — the denominator mismatch inflates the gap but does not cause it, and a real ≈−24 % difference survives on the cleanest subset.** ⚠️ **Withdrawn: the claim that pooled and median agree within 2 points.** They do not after correction (−11.3 vs −17.7); the median is the more robust of the two here. ⚠️ **Also withdrawn — the follow-on task's own refutation of THIS ITEM'S attribution.** T01 concluded that vintage-correcting lighting+equipment could move total energy by at most **7.76 %** (6.13 % for offices) and called that well short of half the gap — **but it measured against the uncorrected ≈25 %**. Against the corrected median gap of 17.72 %, half is 8.9 points and 7.76 is available, so **OPEN-03's "roughly half" is NOT contradicted; against the −23.9 % clean cut it still falls short. The verdict is inconclusive, not refuted.** 🔵 End-use shape (n=48, ABUPS, unaffected by the correction): Interior Equipment 32.45 %, Fans 21.17 %, Cooling 15.63 %, Interior Lighting 13.86 %, Heating 9.09 %, Water Systems 7.08 %, Pumps 0.73 % — **lighting+equipment 46.31 %** overall, 41.21 % for MidriseApartment (n=9) against 57.30 % for offices (n=31), with MidriseApartment dominated by hot water (37.93 %). 🔴 **Whether the multiplier undercount becomes a tracked ID is the USER'S to ratify and is deliberately not taken here.** Evidence: `extra/MEASUREMENT_open-03-18_untrimmed-sample.md` §10; `extra/MEASUREMENT_gap-decomposition_2026-08-19.md`; table `openubem/outputs/comparisons/open03_enduse_by_building.csv`. **NO item opened, closed, struck or retired; 19 live / 40 struck / 59 total, next free `OPEN-60`.**


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
> Task **R03** of `implemenation/previous/PLAN_speed-resume.md` was written to add the column to both harvests,
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

> **✅ SECOND AND FINAL MEASUREMENT MADE — 2026-08-13 (T04 of `implemenation/previous/PLAN_five-more-items-2026-08-13.md`).**
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

### OPEN-29 — Defects whose last recorded status is OPEN, that this register never adopted ❓ ✅ **CLOSED + ID RETIRED 2026-08-19**

✅ **CLOSED + ID RETIRED 2026-08-19** **on the user's ruling of 2026-08-19.** The item's question — *are there defects last recorded OPEN that this register never adopted* — is answered: there were, they were enumerated, and as of the 2026-08-18 re-derivation every one is accounted for. Two fold into items that already own them (OPEN-18, OPEN-10), one closes as immaterial, and **E-LA-15, E-LA-17, E-LA-18, E-LA-19 and E-LA-30 are dormant against `layout_assign`** — a mode nothing on the production path uses, in an arc that is closed and not certified for fleet EUI. They become a precondition of any future `layout_assign` revival. 🔴 **This closure explicitly does NOT claim those five are repaired.** Absence of a signature in the `auto` fleet is evidence about the `auto` fleet at HEAD and nothing more; no defect above is marked fixed, and the narrowest sufficient probe — three single-building **local** `layout_assign` rebuilds (`way/965718401`, `way/86121620` + `way/42496352`, `way/241836727`) — remains the way to settle them and remains not taken. Closing the *register item* is not the same as closing the *defects*, and the distinction is the whole reason this item existed.


> **Amended 2026-08-18 (overnight, X07 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). 🔵 THE ADOPTION MATERIAL EXISTS AT LAST — AND FOUR OF
> THE EIGHT HAVE NO SIGNATURE ANYWHERE IN A WHOLE FLEET.**
>
> This item asks which inherited defects the register should adopt; that is a **user decision** and it
> has never had the material to decide on. **This task did not re-sweep** — the previous automated
> attempt was circular (it classified IDs from OPEN-29's own candidate list) and lost to the hand
> re-trace. Its input is the eight hand-verified STILL-OPEN IDs; its new evidence is the fleet error
> taxonomy built the previous pass, **which none of these defects has ever been tested against**.
>
> | defect | signature across run 2's 8,160 buildings | overlaps a live item? |
> |---|---|---|
> | **E-LA-06** (flow-balance half) | **32 buildings (0.39 %)** — water-to-air heat-pump air-mass-flow Warning | **OPEN-18** (same function) |
> | **E-LA-15** | **0 families, 0 buildings** | OPEN-18's population |
> | **E-LA-16** | **3 families, max 1 building (0.01 %)**, all Warning — no Severe, no Fatal | OPEN-51 (naming, retired) |
> | **E-LA-17** | **16 buildings (0.20 %)** — *the identical population* as OPEN-09/OPEN-56 | 🔴 **OPEN-09 — same buildings** |
> | **E-LA-18** | **0 families, 0 buildings** | OPEN-09 |
> | **E-LA-19** | its named building `way/241836727` **is in run 2 and succeeds** — 0 non-convergence warnings, 0 severe lines | OPEN-09 |
> | **E-LA-30** | no EnergyPlus signature — not testable this way | 3D-viz arc (closed) |
> | **E-LA-33** | 🔵 **re-derived: storey matching inert for 93.32 %** (497 `applied` of 7,442) — inside its own stated 82–98 % band | **OPEN-10** |
>
> **One line each, for the ruling:** four (**E-LA-15, E-LA-18, E-LA-19, E-LA-30**) have no observable
> signature in a whole fleet and are candidates for retirement on evidence; **E-LA-16** is down to one
> building and no severity; 🔴 **E-LA-17 is not a separate defect at all** — it is OPEN-09's population
> exactly, and adopting it would double-count; **E-LA-06 and E-LA-33** are real, now sized, and already
> sit inside OPEN-18 and OPEN-10 respectively.
>
> ⚠️ **Limits stated rather than buried.** Absence of a signature in `.err` is evidence about the
> `auto` fleet at HEAD, **not proof of repair** — three of these were raised under `layout_assign`,
> which run 2 does not exercise. **E-LA-30 and E-LA-33 are viewer/geometry defects `.err` cannot
> see**; E-LA-33 is answered here only because X08 measures the same quantity by another route.
>
> **Evidence:** `openubem/outputs/comparisons/open09_fleet_err_taxonomy.csv`,
> `open10_storey_expressibility_fleet.csv`; report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X07.

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
| **CLOSED-ELSEWHERE** | ~~3~~ **4 (2026-08-18)** | E-LA-11, E-LA-12, E-LA-13 — all closed at the structural-fixes CP-B/CP-C (2026-07-23), reconfirmed 2026-07-25; **+ E-LA-21 — R06 fixed it repo-wide 2026-08-09, re-confirmed live at HEAD 2026-08-18 across every harvest site, see `extra/MEASUREMENT_open-29_status-retrace.md` §2** |
| **STILL-OPEN** | ~~9~~ **8 (2026-08-18)** | E-LA-06 *(flow-balance half)*, E-LA-15, **E-LA-16** *(bucket unchanged — OPEN-51 adjudicated only which of two readings the ID names; the defect itself is still unpatched)*, E-LA-17, E-LA-18, E-LA-19, ~~E-LA-21~~ *(moved to CLOSED-ELSEWHERE)*, E-LA-30, E-LA-33 |
| **SUPERSEDED** | 1 | E-LA-06 *(warmup half)* → folded into the E-LA-14/16/18/19/23 lineage |
| **NO-STATUS-EVER** | 0 | — |

*(13 rows / 12 IDs — E-LA-06 splits across two buckets, which is why it appears twice.)*

**Amended 2026-08-18 (T04 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`, director-audited).**
Full 13-row re-trace at HEAD; the population is unchanged (13 rows / 12 IDs) and only the
CLOSED-ELSEWHERE/STILL-OPEN split moved. The method control was re-run rather than inherited: E-LA-20
blind through the procedure returns `FIXED, verified 150/150` at
`docs/docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:68`.

**One bucket change: E-LA-21 → CLOSED-ELSEWHERE**, confirmed live off the filesystem rather than cited
from a document. 🔴 **Director's correction to the executor's count: the one-space `has_fatal` literal
is fixed at *eight* harvest sites, not seven** — `scripts/cluster/t07_harvest_results.py:199`,
`t07b_run_auto_refit_local.py:330`, `t08_harvest_results.py:246`, `t08_local_remainder.py:431`,
`t17_harvest_layout_assign.py:255`, `t18_harvest_layout_assign.py:252`,
`t19_harvest_layout_assign.py:260`, `t20_harvest_layout_assign.py:260` — all carrying the
whitespace-tolerant `re.search(r"\*\*\s+Fatal\s+\*\*", err)`. `t19` was the site the executor's
seven-site list omitted. Additionally `openubem/results/err_parse.py` now provides a shared tolerant
`has_fatal()` helper whose own docstring records this as the third instance of the one-space bug
(OPEN-45). No one-space literal survives in any code path under `scripts/` or `openubem/` — the only
remaining occurrences are inside document text and the 2026-08-06 CSV. The count correction does not
change the verdict; it strengthens it.

🔴 **E-LA-16 stays STILL-OPEN, and this refutes the lead the director wrote into this task's plan.**
The plan asserted E-LA-16 had "provably closed since (OPEN-51, adjudicated and retired 2026-08-18)."
The executor checked instead of accepting it and was right to: **OPEN-51 closed the question of which
of two readings the ID names — the cooling-coil-design-UA / cooling-tower-UA-autosize family — and did
not touch the defect.** `git log -p --since=2026-08-13` on `layout_assigner.py` shows only a
comment-text correction (`b2d0220`), no code path for the mechanism. Adjudicating an ID's *meaning* is
not fixing the thing it names. **Recorded as a director error, not an executor error**, and as the
second time in two passes that a lead written into a plan's §5 was refuted by the task built to test
it — which is the intended behaviour of that rule, not a failure of it.

**Recommendation accepted: no new register items opened.** The 8 STILL-OPEN entries (E-LA-06
flow-balance, E-LA-15, E-LA-16, E-LA-17, E-LA-18, E-LA-19, E-LA-30, E-LA-33) stay tracked inside
OPEN-29 rather than being promoted to items of their own; promoting them would multiply register rows
without adding a measurement. **OPEN-29 stays open.** Evidence:
`extra/MEASUREMENT_open-29_status-retrace.md`,
`openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv` (new file; the 2026-08-05
original is untouched, mtime verified), `scripts/analysis/open29_status_retrace_2026-08-18.py`.

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
`implemenation/previous/PLAN_speed-resume.md`. `t08_harvest_results.py` was repaired separately as R02 the
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
`scripts/` or `openubem/`.** Full audit table: `implemenation/previous/PLAN_speed-resume.md` §8, "AUDIT — R06".
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

Plan `implemenation/previous/PLAN_five-item-sweep-2026-08-12.md` T06. R06 closed E-LA-21's *one-space* class in
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

*T05 of `implemenation/previous/PLAN_five-more-items-2026-08-13.md`. Report:
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
`implemenation/previous/PLAN_compute-queue.md:343` and `extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md:116`
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


> ✅ **Amended 2026-08-19 (T08 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — all eight
> STILL-OPEN defects adjudicated individually against HEAD, not cited from the prior sweep.**
> **OPEN-29 cannot close. None of the eight is fixed. None warrants a new top-level item.**
>
> **Control passed first:** E-LA-21 re-derives as CLOSED-ELSEWHERE — all eight harvest sites use the
> tolerant two-space regex, **zero** one-space literals survive under `scripts/` or `openubem/`, and
> `git log` since 2026-08-18 shows only a comment-only touch. The harness was trusted for the rest
> only after that passed.
>
> | ID | disposition 2026-08-19 |
> |---|---|
> | **E-LA-06** | STILL-OPEN — real signature, **32 / 8,160 (0.39 %)**; overlaps **OPEN-18** |
> | **E-LA-16** | STILL-OPEN — down to **1 / 8,160 (0.01 %)**, Warning severity only |
> | **E-LA-33** | STILL-OPEN — re-confirmed exactly, **93.32 % inert (497 / 7,442 applied)** |
> | **E-LA-17** | mechanism live (**16 / 8,160**) but **NOT a separate defect** — exact population match to **OPEN-09**. 🔵 **Strike from OPEN-29 as a merge, not a fix.** |
> | **E-LA-15 / 18 / 19** | 🔴 **no signature — but that is an EVIDENCE GAP, not repair** |
> | **E-LA-30** | STILL-OPEN, **confirmed reproducing** — corrects the prior sweep's own framing |
>
> 🔴 **The E-LA-15/18/19 zero must not be read as "fixed."** All three were raised under
> `layout_assign` mode, and the only corpus this read-only task could reach (run 2) runs `auto` mode,
> which never exercises that path. **Narrowest sufficient probe, named and NOT taken:** three
> single-building **local** `layout_assign` rebuilds — `way/965718401`, `way/86121620` +
> `way/42496352`, `way/241836727`. Not a fleet sweep, not a cluster job.
>
> ⚠️ **E-LA-30 is a correction to the earlier record, and the correction matters.** The prior sweep
> recorded "no signature"; in fact the `.err` sweep was simply **the wrong instrument.** Read
> mechanically instead: `fast_scale_idf_text()`
> (`scripts/analysis/a4_bis_generate_layout_assign_viewer.py:17-42`) matches on `"Xcoordinate"` (no
> hyphen), while the DOE baseline it operates on (`openubem/config.py:49-52` →
> `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf:2058-2060`) writes `X,Y,Z ==> Vertex N {m}`. **The
> condition can never match — the scaler is dead code.**
>
> Full record: `extra/MEASUREMENT_open-29_eight-defect-adjudication.md`,
> `openubem/outputs/comparisons/open29_eight_defect_adjudication_2026-08-19.csv`.

> ---
>
> ### ✅ RULING — 2026-08-19, director, after independent re-derivation (T02 of `implemenation/previous/PLAN_board-17-ready-2026-08-19.md`)
>
> The eight dispositions above were **re-derived from the raw artifacts** rather than re-read from
> the prose that produced them, exactly as §4.6 of that plan required. **Five confirmed, two
> contradicted, one not derivable.** Both contradictions are corrections to the table above, and the
> second one is load-bearing. Full record: `extra/MEASUREMENT_open-29_signature-recheck.md`.
>
> 🔴 **The method fault that caused both.** `scripts/analysis/open09_fleet_err_taxonomy.py:38`
> builds the family table with `_MSG = re.compile(r"\*\*\s*(Warning|Severe)\s*\*\*\s*(.{0,90})")`.
> **It matches `Warning` and `Severe` and never matches `Fatal`.** The committed taxonomy CSV is
> therefore structurally blind to every `** Fatal **` line in the corpus — not because none exist
> (six do, all the known OPEN-42/OPEN-56 Warehouse placeholders) but because the counting regex
> cannot see the word. **Two of the eight verdicts above were read off that CSV without knowing it.**
>
> | ID | ruling 2026-08-19 | change from the table above |
> |---|---|---|
> | **E-LA-06** | **STRIKE from OPEN-29 — tracked under OPEN-18.** Real, exactly 32 / 8,160 (0.39 %), single family, confirmed. It is not a separate item; OPEN-18 already owns it. | none — confirmed exactly |
> | **E-LA-33** | **STRIKE from OPEN-29 — tracked under OPEN-10.** Re-derived exactly: `applied` 497 / 7,442 = 6.68 %, inert 93.32 %. OPEN-10 already owns storey expressibility. | none — confirmed exactly |
> | **E-LA-16** | **CLOSE as immaterial-scale**, count corrected. | ⚠️ **2 buildings, not 1.** The taxonomy CSV carries three per-family rows each reading `buildings=1`; the earlier verdict read one row instead of the **union**. Raw `.err`: `nyc_centre/way_266170764` (CORE + PERIM7/PERIM8) and `nyc_centre/way_266170765` (WHOLE) are **distinct**. True population 2 / 8,160 = 0.0245 %. Warning severity only. Cite **2** from here on. |
> | **E-LA-17** | 🔴 **DO NOT strike as a duplicate. Reclassified to UNADJUDICATED BY THIS CORPUS.** | 🔴 **The "exact population match to OPEN-09" does not hold.** E-LA-17's own defining signature — a **Fatal** in `LAUNDRYROOMFLR1` via `CalcHeatBalanceInsideSurf` (`PLAN_structural-fixes_implementation.md:290`) — has **zero hits** in all 8,160 raw `.err` files by direct substring search: `LAUNDRY` 0, `CalcHeatBalanceInsideSurf` 0. Set comparison as instructed: E-LA-17's own-signature set = ∅, OPEN-09's set = 16 real buildings, **symmetric difference 16 — the populations share no building, because one is empty.** The earlier verdict matched a *name* to OPEN-09's Warning-level convergence population using a CSV that cannot see Fatal severity at all. |
> | **E-LA-15 / 18 / 19** | **PARK — no signature in the `auto` fleet; unadjudicated for `layout_assign`.** | sharpened, not changed. The zeros are **real in this corpus** — plain substring search on the defining function names (`SizeAirLoopBranches`, `CheckWarmupConvergence`), not the Fatal-blind family regex. |
> | **E-LA-30** | **PARK — static-code item, no `.err` signature by construction.** | none — not derivable from these artifacts, exactly as expected |
>
> ✅ **Net effect on OPEN-29: nothing in it requires new work at HEAD.** Two defects fold into
> items that already own them (OPEN-18, OPEN-10), one closes as immaterial, and **four — E-LA-15,
> E-LA-17, E-LA-18, E-LA-19 — plus E-LA-30 are dormant against a mode that is not on the production
> path**: all were raised under `layout_assign`, the LayoutAssigner arc is CLOSED and **not certified
> for fleet EUI**, and the only corpus reachable here runs `auto`. **They become a precondition of any
> future `layout_assign` revival, not open work today.**
>
> ⚠️ **What this ruling does NOT claim.** Absence of a signature in the `auto` fleet is evidence
> about the `auto` fleet at HEAD — **it is not proof of repair**, and no defect above is marked fixed.
> The narrowest sufficient probe named by T08 (three single-building **local** `layout_assign`
> rebuilds — `way/965718401`, `way/86121620` + `way/42496352`, `way/241836727`) remains the way to
> settle them, and is **still not taken**.
>
> 🔴 **Recommended to the user, NOT taken here: close OPEN-29 itself.** Every defect it carries
> is now either owned elsewhere, immaterial, or dormant behind a mode nothing on the production path
> uses. **Closure is the user's call and has not been made** — the item stays live in §1 until then.
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

Plan `implemenation/previous/PLAN_five-item-sweep-2026-08-12.md` T07. **The closure condition set on 2026-08-09
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

**Amended 2026-08-06 (N16, `implemenation/previous/PLAN_no-compute-queue-4.md`, director-audited by
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

#### ✅ CLOSED 2026-08-18 — T04 of `implemenation/previous/PLAN_five-items-2026-08-18.md`. The remaining first measurement is answered: commit `67ede73` produced the committed column.

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

### OPEN-07 — Three buildings regressed from success to failure (E-LA-40) ✅ **CLOSED 2026-08-19 (T09, ruling R2) — ID RETIRED**

> 🟢 **CLOSURE RECORD (T09 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, executing ruling R2).**
> Closes on the T05 (2026-08-18 late) finding, appended below at its original location: **all three
> buildings succeed at HEAD** — run 2 (`open48_refleet`, `auto`-family) holds a full IDF/`.err`/`.end`/
> `.sql` for all three and all three complete cleanly (`la_urban/way/401910463` 129.35 kWh/m²,
> `nyc_rural/way/965718402` 237.23, `nyc_rural/way/965718403` 271.97 — all `Completed Successfully`,
> 0 Severe).
>
> **What survives this closure, carried forward because it outlives the item:** all three were
> simulated as **`SmallHotel`**, not the **`SmallOffice`** that `05_results.gpkg` records — a
> provenance fact about the underlying data, independent of whether the regression itself is fixed.
>
> **The caveat that must travel with the closure, not smoothed over:** the E-LA-40 regression was
> observed under `layout_assign`, a mode since decertified for fleet EUI. This closure shows the
> regression does not reproduce on the certified `auto`-family path — it is not proof the
> `layout_assign` mechanism itself is fixed, and nothing here reopens that question under a different ID.
>
> **This closure does not depend on T01** (this same plan's OPEN-55 B+ donor screen, a production
> code change) — OPEN-55 stays open regardless.
>
> **Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §4 (the finding, appended to this
> section on 2026-08-18 late, below).

`la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403` — all inside the
E-LA-38 population above. 3/8,160 = 0.037%. A multiplier-scaling-tips-a-warmup-divergence mechanism
was proposed and is **a hypothesis, not a cause**. Likely closes as a side effect of OPEN-06; confirm
rather than assume.

**Amended 2026-08-06 (N04). ✅** All three are confirmed inside the 41. **Raw `eplusout.err` survives
locally for all three** (T20 harvest cache) — *director-verified on `way/401910463`: 1 `** Severe **`,
1 two-space `**  Fatal  **`, zone `LAUNDRYROOMFLR1`, surface `P_LAUNDRYROOMFLR1_10010_0_10008`.*

~~**The hypothesis is SILENT, not confirmed and not refuted.** No T20 IDF survives locally to diff a
multiplier against, and the T19 cache directory for `way/401910463` is empty — fetching more would
require the cluster, which is forbidden. **Silence is the honest result and is recorded as such.**~~

**Amended 2026-08-18 (T02 of `PLAN_open-52-and-four-items-2026-08-18.md`).** The "no IDF survives"
premise was **false for 2 of the 3 buildings**: `scratchpad/e-la-20-investigation/i03/work_part1/`
holds a paired A/B build (A = `SmallHotel`, as classified today; B = `SmallOffice`, as recorded in T19)
for `nyc_rural/way/965718402` and `nyc_rural/way/965718403`. **`la_urban/way/401910463` still has no
surviving IDF anywhere under `scratchpad/` — confirmed absent by directory search, not assumed.**
Findings below cover 2 of 3 and are not extended to the third.

With geometry in hand, the multiplier-scaling hypothesis does **not** hold: both A and B sides carry a
uniform subsurface multiplier of `1.0`, on both buildings — no scaling disagreement exists to diff.
**A's zone/surface/subsurface counts (67/485/106) are identical to the repo's own healthy
`SmallHotel_90.1-2013.idf` control**, for both buildings — the "classified today" geometry is the raw
DOE prototype dropped in wholesale, not an OSM-extruded building reclassified as `SmallHotel`. B's
counts (6/43/23) match a `SmallOffice` prototype instead. This corroborates OPEN-38's existing
wholesale-substitution finding rather than confirming the multiplier hypothesis, which is refuted on
the 2 buildings measured.

A subsurface-fit test (independent re-implementation, control-verified against the healthy prototype:
0/106 unfitted) found **0 unfitted subsurfaces on either side, for both buildings** (106/106 fitted on
A, 23/23 fitted on B) — a null result, not a confirmation of hidden defects below `.err`'s threshold.
Cross-checked against `.err`: both buildings' `layout_assign` harvest reproduces the register's fatal
zone (`LAUNDRYROOMFLR1`) and names 3 `CHKSBS` "Base surface does not surround subsurface" pairs by
surface name — but those exact named pairs, hand-checked in the scratchpad IDF, are geometrically
well-contained (margins of 0.1–1.2 m, not borderline). **This disagreement between the `.err` and the
surviving IDF geometry is recorded, not resolved** — the scratchpad IDF is dated 2026-07-25, eleven
days before the 2026-08-10 harvest that produced the `.err`, and same-name-same-geometry is not
established across that gap.

**Evidence:** `scripts/analysis/open07_smallhotel_idf_diff.py`,
`openubem/outputs/comparisons/open07_smallhotel_idf_diff.csv`,
`extra/MEASUREMENT_open-07_smallhotel-idf-diff.md`.

**Recommendation, not a ruling:** keep OPEN-07 open, narrowed to `way/401910463` (still unmeasured) and
to the unresolved `.err`-vs-scratchpad-geometry provenance question. Do not close it as "explained by
OPEN-38" on a 2-of-3 measurement. The director rules.

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

### OPEN-08 — Archetype and vintage are not reproducible locally for data-poor buildings (E-LA-22) 📄 **partially quantified** ✅ **CLOSED 2026-08-19 (T09, ruling R2) — ID RETIRED**

> 🟢 **CLOSURE RECORD (T09 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, executing ruling R2).**
> Closes on X05 (2026-08-18 overnight, appended below at its original location): vintage half
> **3 / 8,160 = 0.0368 %** disagreement between E02's persisted label and a HEAD re-derivation;
> archetype control **0 / 8,160 = 0.0000 %** on the same join.
>
> **Correction carried forward, so a future reader is not misled: *"E02 is gone"* is too strong.**
> The 2026-08-17 sweep took the large files — `.sql`, `.idf` — not everything. 61 parquet manifest
> files survive across all twelve cells and carry `vintage_standard`; that survival is what made this
> measurement possible in the first place.
>
> **What is not closed by this, carried forward as context rather than reopened under a new ID:** the
> separate T08-vs-T20 archetype comparison — a different, older generation pair — still stands at
> **13.40 %** disagreement (OPEN-28's own measurement). This closure covers only the E02-vs-run-2
> comparison, on which the pipeline is now shown reproducible; it does not touch or resolve the T08/T20
> figure.
>
> **This closure does not depend on T01** (this same plan's OPEN-55 B+ donor screen, a production
> code change) — OPEN-55 stays open regardless.
>
> **Evidence:** `openubem/outputs/comparisons/open08_vintage_cross_generation.csv`;
> `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X05.

> **Amended 2026-08-18 (overnight, X05 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). 🔴 THE VINTAGE HALF IS MEASURED. The blocker was
> stale for the third time, and this time the reason was the opposite of what was assumed.**
>
> The item's standing reason for not measuring was *"no prior-generation source carries
> `vintage_standard`"* — the only candidate being the E02 manifests, presumed lost with the rest of
> E02 to the 2026-08-17 sweep. **They were not lost.** The sweep took the large files (`.sql`,
> `.idf`); **61 manifest files survive across all twelve cells**, and `step3_auto/03_manifest.parquet`
> carries `vintage_standard` — checked on disk, not assumed. Run 2 and run 3 do **not** carry it
> anywhere (`01_buildings.gpkg`, `03_idf_manifest`, `04_simulation_manifest`, `05_results.gpkg` all
> checked), so the comparison was built the other way round: **E02's persisted label against a HEAD
> re-derivation** from the same buildings' `year_built` through production `resolve_vintage()`, mode
> held at `auto` on both sides.
>
> | | disagreement |
> |---|---:|
> | **vintage** (E02 persisted vs HEAD re-derivation) | **3 / 8,160 = 0.0368 %** |
> | **archetype**, same join, in-task control | **0 / 8,160 = 0.0000 %** |
>
> All three are one bin apart (`DOERefPre1980` → `DOERef1980to2004`), in `la_centre` (1) and
> `la_urban` (2). Every other cell is exact. **Tier breakdown, which doubles as the control that the
> re-derivation matches production:** `VINTAGE_NAN_PERMISSIVE_DEFAULT` 4,256 at 100.00 %,
> `HOTDECK_NEIGHBOR_HIGH` **90** at 100.00 %, `HOTDECK_NEIGHBOR_MED` **46** at 100.00 %,
> `GROUPMODE_MED` 1,521 at 99.93 %, `OBSERVED_YEAR` 2,247 at 99.91 %. **The 90 / 46 reproduce run 2's
> own `data_quality_flag` census exactly**, which is what makes the headline figure citable rather
> than merely computed. ⚠️ The 100 % on the tier-3 default is **not** evidence of anything — it is a
> constant, and a constant reproduces trivially.
>
> 🔴 **A method error that changed the answer by 10×, caught before reporting.** The first run of this
> comparison dropped the geometry column on load, which silently disables `resolve_vintage`'s tier-1
> spatial donor (`knn_fill` degrades to the group mode without raising). It produced
> **29 / 8,160 = 0.3554 %** and a tier table with **no `HOTDECK_*` rows at all** — the absent tier is
> what exposed it. Geometry was restored and the measurement re-run **before any number left the
> task**. Had the tiers not been printed, a figure ten times too large would have been registered.
>
> **What this does and does not change.** The archetype half stands at **13.40 % between T08 and
> T20** — a *different pair of generations*, not contradicted here. What is newly established is that
> **between E02 and run 2 the archetype is perfectly reproducible and the vintage nearly so**, so the
> cross-generation confound this item warns about is **not a general property of the pipeline**; it is
> a property of the specific old generations involved. **Closure recommended to the user, not taken
> here.**
>
> **Evidence:** `openubem/outputs/comparisons/open08_vintage_cross_generation.csv`;
> script `scripts/analysis/open08_vintage_cross_generation.py`; report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X05.

Re-running a past fleet generation at current HEAD silently diverges in archetype *and* vintage for
buildings with missing inputs. Leading suspect: a semantic-imputation commit landing after the fleet
run. **This is the item that quietly limits every other item** — any cross-generation comparison
(T17 vs T20, before vs after) rests on it. Findings on well-tagged buildings survive it; findings that
span generations may not.

**First measurement:** pin the divergence to a commit. Until then, treat every cross-harvest delta in
this project as carrying an unquantified confound.

**Amended 2026-08-05 (M05).** The confound is no longer unquantified. Cross-generation archetype
disagreement between T08 and T20 is **13.40%** on 4,530 shared buildings
(`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-28_harvest-generation-join.md`). ~~Vintage
disagreement remains unquantifiable — no harvest persists a `vintage_standard` column, see new item
**OPEN-30**.~~

**Amended 2026-08-18 (T03 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`), struck above
rather than deleted.** The blocker was seven days stale: **OPEN-30 closed 2026-08-11** and
`vintage_standard` *is* persisted — but only in the E02 manifests, a generation that post-dates both
T08 and T20. Both controls reproduced exactly before anything was concluded: OPEN-30's own gate
(40,800 rows, 0 nulls, 5 distinct values, `DOERefPre1980` **93.4436%**) and OPEN-28's T08-vs-T20 join
(**4,530** shared rows, **13.3996% ≈ 13.40%** archetype disagreement — reused, not re-invented).

🔴 **The vintage half is only partially measurable, and the reason is a schema gap, not a data gap.**
A cross-generation vintage comparison needs a *prior*-generation source carrying `vintage_standard`.
The only candidate on disk, `.../results/cases/<cell>/05_results.gpkg`, carries that column in
**1 of the 5 T08 cells** (`nyc_centre`, 70-column schema); the other four (`la_centre`, `nyc_rural`,
`nyc_suburban`, `nyc_urban`) carry a stripped **21-column** schema with no `vintage_standard`, no
`year_built` and no provenance columns — identical in both the `step1` and `validations` copies. So
vintage is quantifiable on **738 of the 4,530 shared buildings (16.3%)** and remains unquantifiable on
the rest for a reason different from the one struck above.

**On that 738-building subset (prior = pre-T08 commit `e063865`, current = E02 2026-08-09): vintage
disagreement 3.79% (28/738)**, skewed as OPEN-08 predicted — **3.93% among the 713 data-poor buildings
vs 0.00% among the 25 data-rich ones**, though n=25 is too thin to be conclusive on its own.

🔴 **Director's correction, 2026-08-18, to the framing of that number — recorded because the
measurement is right and only its comparator was wrong.** The measurement doc sets 3.79% beside the
**13.40%** archetype figure and calls that a same-rows comparison. It is not: 13.40% is T08→T20 over
4,530 rows, while 3.79% is pre-T08→E02 over 738 rows — different population *and* different generation
pair. **The genuinely like-for-like number is the one the doc reports as mere context: on those same
738 rows and that same generation pair, archetype disagreement is 50.54% (373/738)**, computed from
the same two files as the vintage figure. Read that way the result is stronger and points the other
direction from the doc's headline: **vintage is roughly thirteen times more stable than archetype
across the same generation gap on the same buildings.** The 50.54% also shows `nyc_centre` is not
representative of the fleet on the archetype axis (50.54% locally vs 13.40% fleet-wide over a
different generation pair), which is a further reason not to extrapolate the 3.79% beyond the cell it
was measured on.

**Disposition — OPEN-08 stays open, narrowed.** It does **not** reduce to its archetype half: vintage
disagreement is non-zero and data-poor-skewed. But the two halves are now unequal in weight, and the
vintage clause should read *"quantified on 1 of 5 T08 cells (738/4,530, 3.79%); unquantifiable on the
remaining 4 for a schema reason, not a data-absence reason."* Evidence:
`extra/MEASUREMENT_open-08_vintage-reproducibility.md`,
`openubem/outputs/comparisons/open08_vintage_reproducibility.csv`,
`scripts/analysis/open08_vintage_reproducibility.py`.

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
(`implemenation/previous/PLAN_no-compute-queue.md` §6). Two candidate mechanisms, and the whole task is to tell
them apart: **(1) subset-dependence** — Stage-2 spatial imputation infers height/levels from
neighbours, and with 3 buildings in scope the real 178.5 m neighbour may propagate; **(2) HEAD
divergence** — today's classifier genuinely emits differently than the adopted run did, independent of
subset size. The discriminating experiment is Stage 2 only, run twice on `nyc_centre`: over the same
3 buildings, and over the whole cell. Report:
`extra/MEASUREMENT_open-34_subset-archetype-fidelity.md`.

### OPEN-35 — Two fallbacks fill the same missing storey count, and they disagree — ✅ **mechanism now PROVED at the simulation boundary 2026-08-11; still open**

> **Amended 2026-08-18 (overnight, X04 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). 🔴 THE CONSEQUENCE WAS MEASURED FOR THE FIRST TIME,
> AND THE HEADLINE NUMBER IT PRODUCES MUST NOT BE QUOTED.**
>
> **Population re-derived exactly:** 2,611 / 8,160 = **32.00 %**, **all 2,611** persisted at
> `levels = 1.0`, of which **1,031** carry an apartment archetype — **the register's own figure,
> reproduced to the unit.** Widening to every mid-/high-rise archetype (`LargeOffice` 77,
> `LargeHotel` 10, `Hospital` 1) gives **1,119**; both are recorded because the register's 1,031 uses
> the narrower definition.
>
> **The naive fleet gap is +62.20 kWh/m² on the median — +47.9 % — and it is almost entirely a
> composition artifact.** The confound was declared before the measurement and turned out to be the
> whole story: **`nyc_suburban` contributes 1,589 of the 2,611 and has no unaffected buildings at
> all**, nor does `nyc_rural` (198), so the comparison is largely between cells rather than within
> them. **Within cells the direction is not even consistent** — `austin_centre` 119.13 vs 153.07,
> `la_centre` 103.21 vs 139.35, `nyc_centre` 125.15 vs 154.89 and `la_urban` 101.45 vs 105.96 all run
> **lower**; `austin_suburban` 161.57 vs 112.09, `austin_urban` 140.80 vs 112.46, `la_suburban` 123.37
> vs 109.69 and `austin_rural` 106.22 vs 89.45 run **higher**.
>
> **Conclusion, stated conservatively: this measurement does NOT establish a fleet EUI consequence**,
> and the large number a careless reading produces is an artifact. What the item costs cannot be
> settled cross-sectionally on a population that is missing *by construction*. **It needs what OPEN-56
> got — an intervention with a control**: rebuild a sample at a corrected storey count and run both
> arms. **Named here and not done.**
>
> 🔵 **One clean side result:** the affected buildings **never fail** — 0 failures in 2,611, against 6
> in the other 5,549. Whatever the single-storey fallback does, it does not destabilise the simulation.
>
> 🔵 **And X08 found the item's reach is wider than its own text claims:** in `nyc_suburban` and
> `nyc_rural`, **every** building is `fallback_shorter` for storey matching — zero `applied` — because
> every one sits at `levels = 1.0`. **This item is upstream of E-LA-33's "storey matching is
> invisible" symptom.**
>
> **Evidence:** `openubem/outputs/comparisons/open35_eui_consequence.csv`;
> script `scripts/analysis/open35_open10_consequence_census.py`; report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X04.


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

> ✅ **Amended 2026-08-19 (T07 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — this item's
> population is a STRICT SUBSET of OPEN-12's, and the two must not be merged.** Re-derived on run 2
> (`open48_refleet`, all 12 Stage-1 files verified present first), OPEN-35 reproduces exactly at
> **2,611 / 8,160 = 32.00 %** and OPEN-12 at **2,806 / 8,160 = 34.39 %**; the fleet 2×2 contingency
> sums exactly to 8,160. A building missing *both* levels and height is by construction also a
> building missing height, so the containment is one-directional and cannot be the reverse.
>
> 🔴 **195 buildings (6.95 % of OPEN-12) are in OPEN-12 and NOT in OPEN-35** — concentrated in
> `austin_centre` (102) and `austin_suburban` (40). Folding these two items together would silently
> drop that population, so **keep them separate.**
>
> The register's "same population seen from two sides" impression traces to `nyc_suburban`, where the
> two sets *do* coincide exactly (all 1,589 buildings miss both) and the 61 % / 1,589 arithmetic
> checks to the building. Correct in that cell, wrong fleet-wide. **Control:** Stage-1's
> `data_quality_flag` tokens (`no_height` / `no_floors`, stamped independently at acquisition) agreed
> with the notna() predicates in **every cell, zero disagreements**; neither population exercises any
> imputation tier — both are raw Stage-1 nulls. See the OPEN-12 section for the full record.

> 🔴 **Amended 2026-08-19 (T04 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — THIS ITEM'S OWN
> FRAMING IS CORRECTED. The "chosen as a 19-storey building, built as one storey" description applies
> to 11 buildings, not 1,031.**
>
> **Census, run before any EnergyPlus compute, over the full 1,031-building population (not a sample).**
> By calling `_impute_levels()` itself with the same `levels_group_median`/`levels_global_median`
> lookup step 2 builds — code reused, not reimplemented — T04 recovered the storey value that actually
> drove archetype selection for every one of the 1,031. **Only 11 (1.07 %) carry a genuine numeric
> disagreement** between the archetype-selection fallback and geometry's unconditional 1. The other
> **1,020 (98.9 %) receive the value 1 from *both* fallbacks**: 1,001 of them (97.1 % of the whole
> population) sit in `nyc_suburban` + `nyc_rural`, which hold **zero** ground-truth `levels` rows to
> take a median from at all, so `_impute_levels` returns `LEVELS_DEFAULT_LOW` — **not**
> `GROUPMEDIAN_LEVELS_MED`; the remaining 19 (`austin_rural`, `austin_suburban`) have a group median
> that genuinely computes to 1. **The mechanism and the 1,031 population count are unaffected — both
> re-derived exactly. What is corrected is the *why* for the overwhelming majority.**
> `openubem/outputs/comparisons/open35_storey_intervention_census.csv` (1,031 rows).
>
> **The intervention this item asked for has now been run, on the full census of 11 (not a sample —
> only 11 exist) plus 10 stratified negative controls, both arms, 42 EnergyPlus runs.** The effect is
> real but **NOT one-directional**: 7 positive — `austin_centre` `HighriseApartment`, recovered
> levels 45: **+40.5 %, +18.6 %, +4.6 %**; `la_urban` `MidriseApartment`, levels 7: **+4.7 %, +2.4 %,
> +5.6 %** — and 4 negative — `nyc_urban` `MidriseApartment`, levels 6: **+1.7 %, ‒10.4 %, ‒10.6 %,
> ‒6.8 %, ‒12.6 %**. The sign splits along **climate zone** (2A/3B up, 4A mostly down) rather than
> magnitude. ⚠️ **That is a lead, not an established finding — n = 11 across 3 cells cannot separate
> climate from archetype.** The pre-registered sign prediction (uniform decrease, envelope
> form-factor mechanism) was **refuted for the majority**.
>
> **Controls:** treated IDFs asserted to carry the new storey count by independently parsing
> `BUILDINGSURFACE:DETAILED` Z-extents from the IDF text (21/21); **10 negative controls returned
> Δ EUI = 0.000000 exactly**; fidelity against archived run-2 production EUI passed at 0.0009 % mean /
> 0.0047 % max. Director re-verified the results table independently on 2026-08-19.
> **No fleet figure is quoted or implied; `157.1 kWh/m²` is not restated.**
>
> 🔴 **Two harness bugs were found and fixed mid-task, and the first full run was VOIDED, not
> patched** — both caught by this task's own controls: (1) EnergyPlus's `-x` step **cross-contaminated
> two buildings' outputs** (byte-identical `eplusout.sql` for different footprints) when invocations
> shared a working directory — fixed with per-run `cwd` plus a new duplicate-output control; (2) the
> ad hoc "Total Site Energy ÷ Total Building Area" EUI read **does not match production's**
> `total_eui_kwh_m2` (`openubem/results/parser.py`), a systematic +15–+37 % gap. ⚠️ **Both were
> inherited from `open56_zone_volume_experiment.py`'s `run_ep()`; the exposure is NOT scoped to
> OPEN-35 and reaches any local batch script that imported that helper.** Flagged for adjudication —
> no ID opened for it here.
>
> **Evidence:** `extra/MEASUREMENT_open-35_storey-intervention.md`;
> `openubem/outputs/comparisons/open35_storey_intervention_results_v2.csv` (authoritative —
> `_results.csv` is superseded, wrong EUI formula, kept for provenance only).

✅ **CEILING CORRECTED AND THE AGREEMENT FIX LANDED — 2026-08-19, T04–T05 of
`implemenation/previous/PLAN_board-17-ready-2026-08-19.md`.** Record:
`extra/MEASUREMENT_open-35_fallback-agreement.md`; artifact
`openubem/outputs/comparisons/open35_fallback_agreement_scope.csv`.

> 🔴 **The 11-building census was too small, and the overrun was a census error, not a wrong
> diagnosis.** The executor measured two candidate fixes fleet-wide **before** implementing either,
> and stopped because both exceeded the plan's ceiling of 11 — the correct call.
>
> - **Scope A (naive — geometry always takes the archetype's group-median fallback): 509 buildings.
>   REJECTED.** It moves buildings whose archetype rule never consumed an imputed level count, so it
>   is a different and larger intervention, not the agreement fix.
> - **Scope B (principled — move only where the fired archetype rule actually consumed the imputed
>   levels): 21 buildings. ADOPTED.** Director-verified independently from the artifact: 21 rows,
>   **all 21 carrying `levels_source = GROUPMEDIAN_LEVELS_MED`**, split `MidriseApartment` 8 /
>   `HighriseApartment` 3 / `LargeHotel` 10, across nyc_centre 8, austin_centre 5, nyc_urban 5,
>   la_urban 3. The census's 11 are a **strict subset** of the 21, confirmed by set containment
>   rather than by count.
> - **Why the census said 11:** it scoped itself to apartment archetypes. The other 10 are
>   `LargeHotel` under `RULE_LODGING_TIER`, which consumes imputed levels through the **identical**
>   mechanism. Excluding lodging was an artifact of how the census was written, not a property of
>   the defect.
>
> **Remedy:** `openubem/geometry/footprint.py`'s `derive_num_floors()` returns the group-/global-
> median floor count when levels and height are both missing **and** `archetype_source` carries the
> `GROUPMEDIAN_LEVELS_MED` token — the classifier's own bookkeeping for "this rule consumed the
> imputed levels". New tests in `tests/test_storey_fallback_agreement.py`, including two negative
> tests pinning the Scope A/B boundary.
>
> 🔴 **T04 landed the fix INERT and said so rather than reporting success.** The new parameters
> were keyword-only and no call site passed them, so the fix could not affect a real build, parse or
> aggregate. T05 exists solely to wire the three production call sites, re-proving the changed set
> is still exactly those 21 by **set membership**.

✅ **WIRED AND THREE-WAY AGREED — 2026-08-19, T05–T06.** The fix is now reachable from production
and all three paths derive the same answer.

> **T05 wired two call sites and stopped at the third with a quoted obstacle**, which was the right
> call: `parse_building()` never receives the fleet gdf, and its only production caller copied four
> hardcoded columns into `manifest_row` — `archetype_source` not among them — so the parser could
> not see the token the fix gates on. Reaching it meant editing a file outside T05's bound.
>
> 🔴 **Director ruling: stopping at two of three was not a safe resting place.** With the builder
> wired and the parser not, the build path and the parse path would derive **different floor counts
> for the same 21 buildings** — which is precisely the two-paths-disagree defect this item exists to
> remove, relocated rather than closed. Half-wiring makes the disagreement harder to see, not
> smaller. T06 was authorised to close it.
>
> **T06:** `aggregate_results()`'s `manifest_row` copy widened by **one** column
> (`archetype_source`); the level medians are computed once per run through the classifier's **own**
> `_build_levels_median_lookup()` / `_normalise_use_class()`, never reimplemented.
> `derive_num_floors()`'s logic, `building_classifier.py` and `semantic/__init__.py` untouched.
>
> ✅ **Pass condition met by set membership, not by count:** builder, aggregator and parser paths
> each change the **identical 21 osm_ids**, 0 missing and 0 extra in all three pairwise comparisons,
> verified fleet-wide over all 12 cells and 8,160 buildings from existing Step-1 artifacts — no
> re-classification, no simulation, no fleet re-run. Per-cell split identical across all three:
> austin_centre 5, la_urban 3, nyc_centre 8, nyc_urban 5. A test now **pins the three-way
> agreement**, so one path cannot silently desynchronise from the others later.

⚠️ **No fleet re-run and no re-publication.** The adopted baseline was computed **before** this
fix and is now stale with respect to 21 buildings. ⚠️ **Recommended to the user, NOT taken here:**
decide whether the baseline is restated. **Nothing here restates a fleet figure.**

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

**Amended 2026-08-06 (N13, `implemenation/previous/PLAN_no-compute-queue-3.md`, director-audited by
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


> 🟢 **Amended 2026-08-18 (late) (T05 of `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`).
> All three buildings succeed at HEAD, and the "no surviving IDF" premise is false for all three.**
>
> This item has stood on three buildings that regressed success to failure, and since 2026-08-18 on
> the statement that `la_urban/way/401910463` *"still has no surviving IDF anywhere under
> `scratchpad/`"* — true of `scratchpad/`, but the search never left it. **Run 2 (`open48_refleet`,
> 13 August) holds an IDF, an `eplusout.err`, an `eplusout.end` and an `eplusout.sql` for all three**,
> and all three completed:
>
> | building | archetype | status | EUI | `eplusout.end` | `LAUNDRYROOMFLR1` mentions |
> |---|---|---|---:|---|---:|
> | `la_urban/way/401910463` | `SmallHotel` | **success** | 129.35 | `Completed Successfully — 28 Warning; 0 Severe` | 0 |
> | `nyc_rural/way/965718402` | `SmallHotel` | **success** | 237.23 | `Completed Successfully — 387 Warning; 0 Severe` | 0 |
> | `nyc_rural/way/965718403` | `SmallHotel` | **success** | 271.97 | `Completed Successfully — 517 Warning; 0 Severe` | 0 |
>
> All three are classified `SmallHotel`, which is what OPEN-06 established had actually been simulated
> — so the archetype question that entangled this item is settled in the same rows.
>
> ⚠️ **The caveat that must travel with any closure, stated rather than smoothed.** E-LA-40's
> regression was observed in **`layout_assign`**; run 2 is the whole-storey (`auto`-family) path.
> **This shows the regression does not reproduce on the certified path — not that it is fixed in the
> mode where it was seen.** That mode is `layout_assign`, which its own arc closed as *not certified
> for fleet EUI*.
>
> **Recommendation, not applied: OPEN-07 closes against the certified path with that caveat in the
> closure note.** Left for the user because closing on "the mode where it happened is decertified" is
> a scoping judgement, not a measurement.
>
> **Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §4.


> ✅ **Amended 2026-08-18 (night) (W08 of `implemenation/previous/PLAN_ten-tasks-2026-08-18-night.md`).
> The population figure re-derives EXACTLY on a corpus that still exists.**
>
> The **2,611 / 8,160 = 32.00 %** figure dates from 2026-08-06 and was measured on the pre-Phase-E
> fleet, whose artifacts are gone. Re-derived on run 2's own twelve `01_buildings.gpkg` files:
> **2,611 / 8,160 = 32.00 % — exact, to the unit.** And the mechanism holds at **100 %**: all 2,611
> reach `05_results.csv` persisted at `levels = 1.0`.
>
> 🔵 **Why re-deriving a figure that reproduces is worth the run.** This item may now cite a corpus
> that is **on disk, frozen and re-runnable**, instead of one destroyed by the 2026-08-17 sweep. That
> matters directly to OPEN-53's custody condition and to any future task that needs to re-open this.
>
> **Nothing else changes.** The item stays open on the DESIGN question — which fallback is *intended*,
> archetype-median storeys or one storey — which no measurement can decide and which this task did not
> touch.
>
> **Evidence:** `extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §5;
> `openubem/outputs/comparisons/open35_open12_input_recensus.csv`.

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

#### ✅ CLOSED 2026-08-18 — T03 of `implemenation/previous/PLAN_five-items-2026-08-18.md`. All ten fetch sites now request `.eio`; local census finds zero gaps.

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

**Amended 2026-08-18 (T04 of `PLAN_four-items-2026-08-18.md`) — is `LAUNDRYROOMFLR1` the same mechanism
as OPEN-42? Population re-derived from raw `.err`, independent of this section's own "seven."**

🔴 **Population re-derived: 7, confirmed** — scanned all 8,160 `layout_assign` run directories directly
(not carried from this section), filtering fatals whose nearest preceding `** Severe **` names
`zone="LAUNDRYROOMFLR1"`. Exactly 7, the same 7 named above. No STOP triggered.

**Verdict: two mechanisms, not one.** Every axis measured disagrees between OPEN-38 and OPEN-42:
- **Severe message class differs entirely** — `CalcHeatBalanceInsideSurf: The temperature of <N> C…`
  (OPEN-38, all 7, `n_severe=1` every time — immediate fatal on the first severe) vs. `Temperature
  (low|high) out of bounds [<N>]…` (OPEN-42, all 16, accumulating up to 24 severes before terminating).
- **Zone position is the opposite, measured from `.eio` z-geometry, not from the name.** All 7
  `LAUNDRYROOMFLR1` zones sit at the building's **bottommost** z-extent (floor 1 of 4, 0.00–3.35 m of an
  0.00–11.58 m building, multiplier 1, byte-identical across all 7 buildings). OPEN-42's fatal zones sit
  on the building's **topmost** storey, 15/16 (T03/CP-2 finding, 2026-08-18). **The two items' central
  structural facts are geometric opposites of each other.**
- **Geometry origin differs.** Scanning every `ARCHETYPE_IDF_MAP`-mapped baseline IDF under
  `config.BASELINE_IDF_DIR` for a `Zone` literally named `LaundryRoomFlr1` identifies exactly one
  archetype: **`SmallHotel`** (`ASHRAE901_HotelSmall_STD2022_Buffalo.idf`) — all 7 OPEN-38 fatals are
  the substituted DOE prototype, same zone token as OPEN-06's `SmallHotel` provenance defect. OPEN-42's
  six buildings keep their own OSM-extruded geometry in all three modes that fatal.
- **Modes are disjoint.** OPEN-38 fires only in `layout_assign` (0/8,160 in any other mode). OPEN-42
  fires only in `auto`/`fast_zone`/`floor`, never in `layout_assign` or `building`.
- **T03's orientation warning is silent on this population too**, consistent with T03's own finding that
  `layout_assign` carries it in only 3/8,160 runs fleet-wide: `LAUNDRYROOMFLR1` itself and every sibling
  zone in all 7 runs carry **0** upside-down warnings.

**Second open question answered: not determinable from `eplusout.err`.** All 7 re-derived fatals also
carry the `Base surface does not surround subsurface` warning (fresh re-grep agrees with
`open38_subsurface_census.csv` exactly, 7/7, plus the known non-fatal control
`nyc_rural/way_965718401`). But `.err` can only report a malformed subsurface once EnergyPlus's own
`CHKSBS` routine crosses its own internal fit-tolerance threshold — a subsurface unfitted but inside
that threshold prints nothing, anywhere, for any parser to find. Answering the question needs the IDF
geometry itself, and **that artifact does not exist on disk**: the entire E02 IDF corpus
(`ubem_e02_fleet\<cell>\step3_<mode>\idfs\`) was emptied by the external disk sweep of 2026-08-17 (OPEN-53's
T02 finding). OPEN-38's first open question (prototype-library defect vs. interaction with substituted
geometry) is therefore **still unresolved** — this task only establishes that it is a different question
from OPEN-42's, not that it is answered.

**Recommendation, not a ruling:** OPEN-38 and OPEN-42 should stay two separate items. The director rules.

**Evidence:** `scripts/analysis/open38_laundryroom_signature.py`,
`openubem/outputs/comparisons/open38_laundryroom_signature.csv`,
`extra/MEASUREMENT_open-38_laundryroom.md`.

**Amended 2026-08-18 (T02 of `PLAN_open-52-and-four-items-2026-08-18.md`) — the unfitted-subsurface
sub-question, now answerable on 2 of 7 `LAUNDRYROOMFLR1` fatals** (the 2 that survive as
`scratchpad/e-la-20-investigation/i03/work_part1/` IDFs, both also OPEN-07 buildings). A subsurface-fit
test (control-verified 0/106 false positives on the healthy `SmallHotel_90.1-2013.idf` prototype) found
**0 of 106 (A-side) / 0 of 23 (B-side) subsurfaces unfitted, on both buildings** — geometrically clean,
below and above the `.err` threshold alike. **The prototype-library-defect-vs-interaction question is
still not answered**, but the answer is not "yes, hidden unfitted subsurfaces exist below the warning
threshold" — on the 2 buildings measured, there are none to find.

🔴 **A new, unresolved disagreement, not the one this sub-question was chasing.** The `.err` names 3
`CHKSBS` surface/subsurface pairs by name per building (e.g. `W_RearStairsFlr1_3_0_0` /
`..._Door`). Those exact pairs exist by name in the scratchpad IDF and were hand-verified: the door
sits fully inside its wall by 0.1–1.2 m margins, not a borderline case. **The scratchpad geometry does
not reproduce the defect its own harvest's `.err` reports for the same named surfaces.** Recorded, not
resolved: the scratchpad IDF is dated 2026-07-25, the harvested `.err` 2026-08-10 — same classification
and naming convention, not established to be the same generated geometry. This is exactly the kind of
disagreement §5.2's plan text warned about noting rather than resolving.

**Recommendation, not a ruling:** record the sub-question as **measured-null on 2/7 fatals, with a new
open provenance question** (scratchpad-vs-harvest geometry identity) rather than "answered" or "still
open" outright.

✅ **RULED 2026-08-18 (director's audit of T02, re-derived independently from the same files). The
recommendation is accepted in outline and strengthened on two points; one of its premises is
corrected.**

**Correction — the provenance question is largely resolved, and resolves in favour of same-geometry.**
Matched case-insensitively (EnergyPlus uppercases names in `.err`), the scratchpad IDF contains the
**exact fatal surface `P_LaundryRoomFlr1_10010_0_10008`** and all three `CHKSBS` base/door pairs, name
for name. The 11-day mtime gap dates the scratchpad *copy*, not a different generation. T02 was right
to raise the doubt and right not to resolve it; on the evidence it does not survive. *(The director's
own first pass at this check used a case-sensitive grep, got 0, and briefly read it the opposite way —
recorded so the correction is not silently absorbed.)*

**Strengthening 1 — the disagreement with `.err` is sharper than "the door fits."** Re-derived on the
A-side IDF for all three flagged pairs: every subsurface vertex lies **0.0000 m** from its base
surface's plane, each door is strictly inside its wall in-plane
(`W_RearStairsFlr1_3_0_0` x[12.247,12.456] ⊂ [12.002,12.560]; `W_CorridorFlr1_10_0_0`
x[5.741,5.950] ⊂ [5.449,6.146]; `W_FrontStairsFlr1_3_0_0` x[0.224,0.433] ⊂ [0.011,0.569]; all
z[0,2.134] ⊂ [0,3.353]), and the file carries **591 surface+subsurface objects with zero duplicate
names**, so EnergyPlus is not resolving `BaseSurfaceName` to another instance. The geometry is clean by
every test available here and EnergyPlus still reports `Overlap Status=No-Overlap`. Each door's bottom
edge lies exactly on its wall's bottom edge (z=0 on both) — recorded as an observation, **not** as an
explanation.

🔴 **Strengthening 2 — the sub-question is settled by refutation, and the null result carries less
weight than it appears to.** Two findings, in order of force. **(a) The three `CHKSBS` warnings are on
`RearStairs`, `Corridor` and `FrontStairs` — not one of them is `LaundryRoomFlr1`**, the zone that
carries the Severe and kills the run (`CalcHeatBalanceInsideSurf: The temperature of -11949.70 C for
zone="LAUNDRYROOMFLR1", for surface="P_LAUNDRYROOMFLR1_10010_0_10008"`). Taking every warning at face
value, **the unfitted-subsurface signature does not touch the dying zone.** This is the same shape as
the refutation that killed the surface-orientation lead for OPEN-42 on 2026-08-18: a signature present
on healthy zones and absent from the fatal one. **(b)** The subsurface test's only control was a
known-*negative* (healthy prototype, 0/106); it was never shown to return a positive on a case the
authority flags, and on the three such cases here it **disagrees with EnergyPlus**. A detector with no
demonstrated true positive cannot carry "no unfitted subsurfaces exist" — the 106/106 and 23/23 results
are a **null of unvalidated power**. The A/B diff is unaffected: it rests on counts, not on that
detector.

**Net disposition: unfitted subsurfaces are NOT OPEN-38's mechanism** — refuted on the dying zone
rather than merely unobserved. OPEN-38 stays open on its thermal-runaway face, and stays separate from
OPEN-42 (ruled above). `way/401910463` and 4 of the 7 fatals remain unmeasured; no IDF survives for
them. `way/401910463` and the other 4 of the 7 `LAUNDRYROOMFLR1` fatals remain unmeasured — no
IDF survives for any of them. **Evidence:** `extra/MEASUREMENT_open-07_smallhotel-idf-diff.md`,
`openubem/outputs/comparisons/open07_smallhotel_idf_diff.csv`.

> **Ruling 2026-08-18 (director, T05 of `implemenation/previous/PLAN_four-items-2026-08-18.md`, per the user's
> standing instruction of 2026-08-12 that no-compute item dispositions of this kind are the director's
> call).** **T04's recommendation is ACCEPTED. OPEN-38 and OPEN-42 STAY SEPARATE ITEMS.** Every axis T04
> measured disagreed between the two — Severe message class, temperature range, zone position
> (bottommost vs. topmost storey), geometry origin (substituted `SmallHotel` prototype vs. the
> building's own OSM extrusion), and mode (`layout_assign`-only vs. never `layout_assign`) — and none of
> the controls run against OPEN-42's own signature found a shared mechanism. No merge.

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

> ✅ **Amended 2026-08-19 (T05 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — the "no IDF
> survives" blocker was STALE, and it was retired by test rather than by assertion. All five
> unmeasured fatals are now measured, and they reproduce.**
>
> 🔴 **The distinction that unblocked this, worth generalising:** *"no IDF survives"* is a **corpus**
> statement, not a **capability** statement. It says nobody found a file — not that the file cannot be
> rebuilt. Both halves were then checked separately. **The corpus claim is TRUE:** all seven target
> directories were inspected and the original E02 `.idf` files really are gone (`.err`, `.eio`,
> `.end`, `.sql` survive; no `.idf`). **The capability claim is FALSE:** a fresh `layout_assign` IDF
> builds locally for any of them, and one was built for all five — plus an independent positive
> control on an already-measured building. *(This is the third time in two days a stated blocker has
> failed on inspection; the pattern is now firmly evidenced.)*
>
> **Result: 6 / 6 reproduce the identical mechanism** — `CalcHeatBalanceInsideSurf` Severe in zone
> `LAUNDRYROOMFLR1`, **Sizing** phase, immediate two-space `**  Fatal  **`, `n_severe = 1`. One
> rebuilt surface name matches this register's own citation **byte-for-byte**.
>
> ✅ **Controls, all passed.** Positive control reproduced (so the other five stand); one healthy
> `layout_assign` sibling per cell completed cleanly as a negative control; **0 / 9 output directories
> empty**. Mode named explicitly — every build ran `layout_assign`, matching the original population's
> mode rather than the `auto` corpus that has misled other sweeps.
>
> 🔵 **Fixture choice was pre-registered and it decided the outcome.** The older `phaseE` fixture
> (2026-06-28) had already been tried against this exact population on 2026-08-18 and **failed** to
> reproduce. This task chose the closer-in-time `open48_refleet` fixture (2026-08-12, two days after
> the harvest) **before running**. Anyone re-testing this population must match the fixture to the
> harvest date or they will get a false negative.
>
> 🔵 **Incidental finding that closes an adjacent question.** With real IDF geometry finally on disk,
> the previously "not determinable" subsurface-fit hypothesis is answered directly: all six fatal IDFs
> carry **106 / 106 fitted subsurfaces**, identical to the healthy control, and `LaundryRoomFlr1`'s own
> subsurfaces are all fitted. **Unfitted subsurfaces are NOT the mechanism** — that line of inquiry is
> closed, and the geometry hypothesis above needs a different candidate condition.
>
> Full record: `extra/MEASUREMENT_open-38_five-fatals-rebuild.md`,
> `openubem/outputs/comparisons/open38_five_fatals_rebuild.csv`, scripts
> `scripts/analysis/open38_five_fatals_rebuild_2026-08-19.py` and
> `open38_five_fatals_subsurface_check_2026-08-19.py`; rebuilt artifacts under
> `scratchpad/open38-t05-rebuild/` (⚠️ gitignored scratch — re-verify presence before citing).

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

### OPEN-42 — The `Warehouse` population is broken in two measured ways, and one of them reaches the adopted baseline ✅ **CLOSED 2026-08-19 (T09, ruling R2), folded into OPEN-56 — ID RETIRED**

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


> 🔵 **Amended 2026-08-18 (late) (T04 of `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`).
> THE MECHANISM IS FOUND, and the item's blocking premise was false.**
>
> 🔴 **First, the premise.** The 2026-08-18 ruling above closed this investigation on the grounds that
> *"the E02 IDF corpus that could show the actual per-surface geometry no longer exists on disk"* and
> that any next step needed compute or a ruling. **It needed neither.** Run 2 (`open48_refleet`,
> 13 August) rebuilt all six buildings, **kept their IDFs and their `.err`/`.end`/`.sql`**, and
> reproduced the identical failure. The artifact was on disk one run newer than the deleted one, and
> finding it took a directory listing. **Recorded as a lesson, not smoothed: a "no artifact exists"
> ruling must name the paths that were checked.**
>
> ✅ **The zone-geometry hypothesis is dead, and it dies on a positive measurement rather than an
> artifact shortage.** `scripts/analysis/open42_run2_fatal_zone_geometry.py` parsed all six run-2 IDFs:
> - **The "topmost storey without exception" invariant does not hold in run 2 — 4 of 6, not 6 of 6.**
>   `way/472960972` fatals on `_F1` of three storeys (the middle), and `way/402215469` on `_F4` of six.
> - **The fatal zone is indistinguishable from its non-fatal siblings in the same file** — same
>   surface count, same surface-type mix, same boundary conditions, same total surface area to the
>   centimetre, same 3.5 m height, same WWR (0.100 everywhere, per surface and per zone), same one-per-
>   zone HVAC/thermostat/lights/people/equipment/infiltration objects. `way/402215469`'s `_F4` is
>   identical to `_F1`, `_F2` and `_F3`, and only `_F4` blows up.
>
> 🔵 **What it actually is, from EnergyPlus's own diagnostic:** `** Warning ** Indicated Zone Volume
> <= 0.0 … The calculated Zone Volume was=-1376.24 … The simulation will continue with the Zone Volume
> set to 10.0 m3.` The `Zone` objects declare `Volume` as `autocalculate`; EnergyPlus derives it from
> surfaces wound the wrong way (`GetVertices: Floor is upside down!`) and gets a **negative** number,
> then substitutes **10 m³**. A zone with 2 869 m² of surface and 10 m³ of air has almost no thermal
> capacitance, so any heat-balance residual swings its air temperature by hundreds of degrees in one
> timestep — which is the observed failure, and which is why *which* storey tips first is unstable.
>
> 🔴 **And it is not six buildings. It is 8 160 of 8 160 — 100.00 % of the fleet.** Registered
> separately as **OPEN-56**, because it is a different blast radius from this item's. A previous pass
> measured the same stub, found it on succeeding buildings too, and read that as *"not the
> mechanism"* — the right reading was *"necessary, not sufficient"*. **Magnitude separates them:**
> failures average a computed volume of **−6 096 m³** (min −26 184) against **−683 m³** for the 761
> successes in the same two cells. **The six are the extreme tail of a universal defect.**
>
> **Where this leaves OPEN-42.** Its own question — *what is wrong with these six buildings* — is
> answered: **nothing is specific to them.** The item should close against OPEN-56 rather than stay
> open on a mechanism that has been found. **Recommended, not applied** — the closure is the user's,
> and it retires an item by absorbing it, which this register does not do on a director's own motion.
>
> **Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §2;
> `openubem/outputs/comparisons/open42_run2_fatal_zone_geometry.csv`,
> `open42_zone_volume_census.csv`, `open11_open42_six_buildings.csv`; scripts
> `scripts/analysis/open42_run2_fatal_zone_geometry.py`, `open42_zone_volume_census.py`.


> 🟢 **Amended 2026-08-18 (night) (W03 of `implemenation/previous/PLAN_ten-tasks-2026-08-18-night.md`).
> SOLVED. Closure recommended to the user.**
>
> The live question was *"what is wrong with the topmost-storey geometry of these six buildings such
> that any zone built from it runs away."* **Answer: nothing is wrong with these six buildings.**
>
> Writing **one field** — `Zone.Volume`, computed as floor area × height — into a copy of each IDF and
> re-running locally makes **all six complete successfully with zero severe errors** (from 9, 21, 25,
> 25, 11 and 39 severes). Control: the `Indicated Zone Volume <= 0.0` warning present in 16 / 16
> baseline runs and 0 / 16 treated. **Intervention with a control, six for six.**
>
> **They are the six on which a fleet-wide defect (OPEN-56) happens to tip over** — the buildings whose
> real volume is largest, and therefore whose 10 m³ substitution error is largest. W07 supplies the
> second stage: heat-balance non-convergence occurs in only **16 of 8,160** buildings and **all six
> failures are inside those 16, with zero failures outside them.**
>
> 🟢 **Recommended: OPEN-42 closes against OPEN-56, and OPEN-11 with it.** Not applied — retiring an
> item by absorbing it into another is the user's call, not a director's own motion. **What must
> travel with the closure:** face (i)'s `Warehouse` 13.68 % failure rate and face (ii)'s placeholder
> are both explained by this — Warehouses are large-volume buildings, and the placeholder is written
> only on failure.
>
> **Evidence:** `extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §1;
> `openubem/outputs/comparisons/open56_zone_volume_experiment.csv`.

---

#### 🔵 MEASURED 2026-08-12 — the placeholder is traced, and it does not touch the published number

Plan `implemenation/previous/PLAN_five-item-sweep-2026-08-12.md` T01–T02. Every figure below was **re-derived
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

> **Amended 2026-08-18 (T05 of `implemenation/previous/PLAN_five-items-2026-08-18.md`). The `.eio` was read —
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

> **Amended 2026-08-18 (T03 of `implemenation/previous/PLAN_four-items-2026-08-18.md`). The next artifact named
> by the previous amendment — `eplusout.err`'s `GetVertices: … is upside down!` warnings — was read.
> 🔴 The lead named in the plan's fact 5 is retired. Reported as a finding, not a shortfall.**
>
> **Fleet-wide rate, reported before interpretation: 8,287 / 40,800 run directories (20.31%) carry
> the warning — and that number is fully explained by one fact: it fires on 100.00% of all 8,160
> `auto`-mode runs fleet-wide, every building, every cell, whether the run fails or not.** It is
> absent from `building` and `floor` (0/8,160 each) and only sporadic in `fast_zone` (124/8,160,
> 1.52%) and `layout_assign` (3/8,160, 0.04%). Only 8 of the 8,160 `auto` runs actually fail — a
> 0.10% fatal rate inside a population where the warning rate is 100%. A signature universal to a
> mode cannot explain a 0.10% failure rate inside that mode.
>
> **All three of the plan's questions, run against their controls, came back negative:**
> - **4a (sharpest test — same run, fatal zone vs. its non-fatal siblings): the fatal zone carries the
>   warning LESS often than its siblings**, 1/16 failing runs (6.2%) vs. 167/359 sibling zones in the
>   same 16 runs (46.5%) — the inverse of what a causal signal would show.
> - **4b (topmost-storey roof vs. lower storeys): no separation** in the target population (41.7% top
>   vs. 40.5% non-top); the background sample shows a *larger* top/non-top gap (26.8% vs. 14.1%) than
>   the target does — the opposite of a mechanism specific to the six.
> - **4c (decisive — modes that fail vs. modes that succeed): the warning fires in exactly one of the
>   three failing modes.** All 6 buildings carry it in `auto` (6/6) and **none** in `fast_zone` (0/6)
>   or `floor` (0/6) — the same two failing modes, same thermal-runaway mechanism, zero warnings. A
>   defect present in one mode regardless of outcome and silent in two other modes that fail by the
>   identical mechanism cannot be that mechanism.
>
> **Non-vacuity control, obligatory, confirmed by hand:** `la_rural_building/way_472960972/eplusout.err`
> — parser 0, `grep -c 'upside down'` 0; `la_rural_auto/way_472960972/eplusout.err` — parser 144,
> `grep -c` 144. Both agree.
>
> **Candidate mechanism located in code, not fixed, per the plan's rule.**
> `openubem/idf/surfaces.py:223-234` (`_coreperim_has_inverted_winding`) already computes this exact
> signal, and its caller's docstring at `:671-681` (`_rebuild_degenerate_coreperim`) states it is
> **deliberately excluded** as a defect check: *"EnergyPlus convention always uses negative signed-area
> (CW winding) for floor surfaces; checking sign would produce false positives on healthy buildings."*
> This is in-code corroboration, independent of this measurement, for exactly what the fleet-wide rate
> shows: inverted winding is the expected shape of core/perim (`auto`-mode) geometry, and EnergyPlus's
> own parser auto-corrects it (`Automatic fix is attempted.` follows every warning line in the raw
> `.err`).
>
> **Where this leaves the item: the per-surface winding/orientation artifact is retired as an
> explanation for OPEN-42's thermal runaway.** `eplusout.eio` and now `eplusout.err` have both been
> read and both come back "not determinable from this artifact" or "does not separate." **OPEN-42
> stays OPEN.** No further local artifact has been named; the next step would require either
> instrumenting a fresh EnergyPlus run (compute, not authorised here) or accepting the question as
> closed-without-a-mechanism, which is a director/user ruling, not an executor's call.
>
> **Evidence:** `openubem/outputs/comparisons/open42_surface_orientation.csv` (696 rows: per-warning
> detail across 30 target + 100 background runs, plus per-run summaries); report
> `extra/MEASUREMENT_open-42_surface-orientation.md`; scanner
> `scripts/analysis/open42_surface_orientation_census.py`.

> **Ruling 2026-08-18 (director, T05 of `implemenation/previous/PLAN_four-items-2026-08-18.md`). The item is
> REFRAMED, not closed — recorded as a ruling because it changes what the next task must look for.**
>
> **OPEN-42 and OPEN-38 stay two separate items** — see OPEN-38's own section for the identical ruling;
> T04's recommendation is accepted.
>
> **The live question is no longer "which zone is inverted." It is now: what is wrong with the
> topmost-storey geometry of these six buildings such that any zone built from it runs away.** T03's
> census established, without exception, that all 16 fatal (building × mode) runs sit on the building's
> own topmost storey, and that the zone's *name* changes with the zoning mode while its *position* does
> not — which is why no earlier pass saw the invariant.
>
> **Zoning mode is not the variable that explains the failure — it only decides whether the topmost
> storey gets a zone of its own at all.** `building` mode collapses the whole building into a single
> zone; `layout_assign` substitutes a DOE prototype and discards the OSM-extruded storeys entirely.
> Those are exactly the two modes that never fatal, and they are exactly the two modes that never build
> a zone from the building's own topmost storey. `auto`, `fast_zone` and `floor` all give the topmost
> storey its own zone, and all three fatal.
>
> **Both `eplusout.eio` and `eplusout.err` are now exhausted for this question.** `.eio` (T05,
> 2026-08-18 amendment above) found the position but no explanatory field; `.err` (T03, same date)
> tested and retired the per-surface orientation lead. **No further local artifact is named as the next
> step** — the E02 IDF corpus that could show the actual per-surface geometry no longer exists on disk
> (emptied by the external sweep of 2026-08-17 16:21, OPEN-53's finding). Any next step needs either a
> fresh EnergyPlus run (compute, not authorised under this arc's no-cluster/no-simulation rules without
> a separate ruling) or a user decision to close the question without a mechanism.

> 🟢 **CLOSURE RECORD (T09 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, executing ruling R2).
> Folds into OPEN-56.**
>
> **What OPEN-56 explains.** Its intervention is confirmed by control to cure all six of face (ii)'s
> fatal failures — writing `Zone.Volume` explicitly took all six from 9–39 severes to 0, six for six,
> with the `Indicated Zone Volume <= 0.0` warning at 16/16 baseline → 0/16 treated. **Warehouses
> concentrate the fleet's fatal failures (13.68 % vs 0.0443 % elsewhere, 26 of 44 fleet fatals) because
> they are large-volume buildings**, and the stub's substitution error scales with the real computed
> volume (failures average **−6,096 m³** vs **−683 m³** for successes in the same cells). So face (i)'s
> 309× failure rate and face (ii)'s placeholder `200.0 m²` (written only on failure, traced 2026-08-12
> to `scripts/validation/v12_cell_pipeline.py:659/664`) are both explained by this one mechanism, not
> two.
>
> **What OPEN-56 does NOT explain — named explicitly, so no debt is lost with this ID:**
> 1. The intervention was directly re-run on the **6 face-(ii) placeholder buildings only**. The
>    remaining distinct Warehouse buildings that fatal without the placeholder (face (i) minus
>    face (ii)) were never individually re-run under the fix; their cure is inferred from the shared
>    mechanism, not independently confirmed.
> 2. **OPEN-56's remedy is not authorised or implemented.** This closure records a mechanism finding,
>    not a fix — OPEN-56 stays open, and no code changed as a result of this closure.
> 3. OPEN-56 explicitly does not claim the published `157.1` / `158.0` kWh/m² fleet EUI is wrong
>    (infiltration is written `Flow/ExteriorWallArea`, not scaled by the stub). These six remain
>    confirmed at exactly **0.00 %** fleet-EUI impact — all six are `not_simulated` /
>    `total_eui_kwh_m2 = NaN`, excluded from both sides of the aggregation (measured 2026-08-12,
>    unchanged by this closure).
> 4. OPEN-56's separate 2026-08-19 (T03) finding — `nyc_centre/relation_3566904`'s reported floor area
>    moving ÷4.18 when `Zone.Volume` is written — is a **different building**, not one of these six, and
>    its fleet-wide uniqueness is still unanswered. It does not affect this closure.
>
> **This closure does not depend on T01** (this same plan's OPEN-55 B+ donor screen, a production code
> change to `openubem/semantic/__init__.py`) — OPEN-55 stays open, unproven in simulation, regardless
> of this closure.
>
> **Evidence:** `extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §1;
> `openubem/outputs/comparisons/open56_zone_volume_experiment.csv`; OPEN-56's own §-section.

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

> **Amended 2026-08-18 (overnight, X03 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). 🔵 A CLEAN NEGATIVE: THIS ITEM IS *NOT* DOWNSTREAM OF
> OPEN-56, AND FIXING OPEN-56 WOULD NOT FIX IT.**
>
> The previous pass produced the two-stage picture — the 10 m³ volume stub universal and
> necessary-not-sufficient, the non-convergence rare (16 / 8,160) and containing every failure — but
> could not say whether the two stages are the *same* defect. They are not, and the test is direct.
>
> The ten buildings that carry a non-convergence warning **and still succeed** were run in both arms
> of OPEN-56's intervention (`Zone.Volume` written, one field, diff asserted):
>
> | | baseline | treated |
> |---|---:|---:|
> | non-convergence warnings, total | **150** | **150** |
> | per building | **15 / 15 on all ten** | **15 / 15 on all ten** |
>
> **Not one warning moved**, while the same treatment cleared the volume warning completely
> (**70 / 70 baseline → 0 / 70 treated** on the wider sample). 🔴 **OPEN-09 and OPEN-56 are
> independent defects that happen to overlap on the same 16 buildings.**
>
> ⚠️ **The nuance, stated rather than smoothed over.** The same treatment *does* repair all six fleet
> failures. Both are true at once: the treatment rescues the buildings that tip over, and it leaves the
> non-convergence warnings untouched in the ten that do not. **The warnings are a symptom of something
> else; the stub is what turns that something else fatal.** This item keeps its own life and its own
> closure condition.
>
> **A second, independent narrowing from X07 of the same pass:** the inherited defect **E-LA-17**
> ("zone divergence persists in a second zone") resolves to **exactly this item's 16-building
> population** in the fleet error taxonomy — it is not a separate defect, and adopting it into the
> register would double-count. **E-LA-18** has **no signature at all** across 8,160 buildings, and
> **E-LA-19's** named building `way/241836727` **is present in run 2 and succeeds** with 0
> non-convergence warnings and 0 severe lines.
>
> **Evidence:** `openubem/outputs/comparisons/open56_fleet_cost_stratified.csv`,
> `open09_fleet_err_taxonomy.csv`; report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X03, §X07.

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
95.8%); the cited 96.3% is correct. Audit entry: `implemenation/previous/PLAN_compute-queue.md` §8.

> **Amended 2026-08-18 (OPEN-51's adjudication, T02 of `implemenation/previous/PLAN_five-items-2026-08-18.md`).
> The "five inherited log entries" narrows to four.** OPEN-51 decided, on quoted evidence, that
> `E-LA-16` names the cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family, not the
> `CheckWarmupConvergence` class C06 tested. **The inherited-label list above is corrected to
> E-LA-14/18/19/23 — four entries, not five.** E-LA-16 was never covered by C06's population or its
> "cosmetic" finding, and its own accuracy impact remains untested. This does not change C06's
> substance for the four entries it does cover.

### OPEN-10 — Editing the `ZoneGroup`'s own list multiplier would restore exact expressibility (E-LA-37) ✅ **checked at last — the capability is real, and narrower than claimed**

> **Amended 2026-08-18 (overnight, X08 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). ✅ THE "90 BUILDINGS" IS RE-DERIVED — EXACTLY, SPLIT
> AND ALL — AND THE ITEM FINALLY HAS A DENOMINATOR.**
>
> `extra/MEASUREMENT_open-10_zonegroup-capability.md` §4 named the precise experiment that would
> settle this figure and declined to run it — *"NOT re-derived in this task, and I did not attempt
> to"* — because N11's plan forbade CPU-bound work. **That constraint does not apply to this pass, so
> the experiment was run**, calling production `compute_band_map()` / `match_storeys()` over the
> fleet rather than re-implementing them.
>
> | | historic (2026-08-05) | re-derived on run 2 |
> |---|---|---|
> | buildings the `ZoneGroup` overwrite recovers | **90** = 66 `MidriseApartment` + 24 `HighriseApartment` | **90** = **66** + **24** ✅ |
>
> **And the denominator this item has never had:** of 7,442 evaluated buildings, `fallback_shorter`
> **3,727** (50.1 %), `fallback_not_expressible` **1,992** (26.8 %), `identity` **1,226** (16.5 %),
> **`applied` only 497 (6.7 %)**. The proposed edit reaches **90 of the 1,992 = 4.5 %**; the other
> **1,902 (95.5 %)** are structurally beyond it — **1,578 `SmallOffice`**, 170 `LargeOffice`, 88
> `TallBuilding`, 24 `SuperTallBuilding`, 23 `LargeHotel`, 19 others. Exactly **two** of the eighteen
> archetypes present in the fleet carry a `ZoneGroup` at all, confirming N11's read directly against
> the fleet instead of against the prototype library.
>
> 🔴 **"Restore exact expressibility" is now quantified, and it is generous.** The edit is real and it
> works — on **4.5 % of the problem it is named for.**
>
> 🔵 **A cross-item mechanism found while doing it, which nobody was looking for.** `nyc_suburban` and
> `nyc_rural` have **zero** `applied` buildings — every one is `fallback_shorter`, because every one
> sits at `levels = 1.0`. **That is OPEN-35's population.** The missing storey count is *why* storey
> matching is inert in those cells, which places **OPEN-35 upstream of E-LA-33's symptom**; no
> `ZoneGroup` work would move either. Stated as a mechanism found, **not** as a ruling.
>
> **Evidence:** `openubem/outputs/comparisons/open10_storey_expressibility_fleet.csv`;
> script `scripts/analysis/open35_open10_consequence_census.py`; report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X08.

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

### OPEN-11 — Six inverted-geometry buildings still need post-hoc remediation ⚠️ ✅ **CLOSED 2026-08-19 (T09, ruling R2), folded into OPEN-56 — ID RETIRED**
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

**Amended 2026-08-18 (T03 of `implemenation/previous/PLAN_four-items-2026-08-18.md`). The "inverted-geometry"
label was tested against a mechanism for the first time — the `GetVertices: … is upside down!` warning
family in `eplusout.err` — and the label is not corroborated by it.** Every one of the fleet's 8,160
`auto`-mode runs carries the identical warning, these six buildings included — it is not a distinguishing
property of the six, it is a universal property of the zoning mode (full measurement under OPEN-42's
2026-08-18 T03 amendment, same date). **This does not close OPEN-11** — the item's own subject is the
Phase-E re-run's 6/8,160 drop and the un-reapplied `10_fails_solution.md` remediation, which this task
did not touch — but it does mean *"inverted geometry"* should not be read as meaning *"these six carry
an EnergyPlus surface-winding warning that other buildings don't"*: they don't carry anything distinctive
by that measure. Evidence: `openubem/outputs/comparisons/open42_surface_orientation.csv`;
`extra/MEASUREMENT_open-42_surface-orientation.md`.


> 🔵 **Amended 2026-08-18 (late) (T03 of `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`).
> The identity with OPEN-42 was predicted in writing before it was measured, and it holds exactly.**
>
> OPEN-11's six and OPEN-42 face (ii)'s six placeholder-`200.0 m²` Warehouses are **the same six
> `osm_id`s** — intersection 6, symmetric difference 0, re-derived over all 8 160 run-2 rows. They are
> also **exactly the fleet's six non-successes**: `footprint_area_m2 == 200.0` and
> `simulation_status != "success"` select the same six with no false positive or negative either way.
> `no_floors` does not do this — it is carried by 7 719 of 8 160 and catches 5 of the 6. *(The
> register already "connected" the two populations on 2026-08-18 without re-deriving; this is the
> re-derivation.)*
>
> 🔴 **The consequence for this item is not the identity — it is what OPEN-56 does to its remedy.**
> This item asks for a **per-building** remediation (`10_fails_solution.md`, re-applied to six
> buildings). The cause is now measured as present in **all 8 160 buildings**. **A six-building patch
> cannot be the right remedy for a fleet-wide defect, and applying one would hide it.**
>
> **Recommendation, not applied: OPEN-11 folds into OPEN-56 or closes against it.** Also note the
> label is now falsified twice over — once by the surface-orientation census (2026-08-18), and now by
> the failure text itself, which is `Temperature (low|high) out of bounds`, a thermal runaway, not a
> geometry error. **"Inverted geometry" should not be used for these six again.**
>
> **Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §3;
> `openubem/outputs/comparisons/open11_open42_six_buildings.csv`.


> 🔵 **Amended 2026-08-18 (night) (W07 of `implemenation/previous/PLAN_ten-tasks-2026-08-18-night.md`).
> First fleet-wide test of this item's subject. Half the premise holds and half does not.**
>
> Measured over **all 8,160** `eplusout.err` files of run 2 — a corpus still on disk with frozen
> inputs, unlike the E02 harvest every previous census used.
>
> **Prevalence: 16 of 8,160 buildings = 0.20 %** carry an `Inside surface heat balance did not
> converge` warning. All sixteen are in LA cells (`la_rural` 10, `la_suburban` 3, `la_centre` 2,
> `la_urban` 1); **zero in any NYC or Austin cell.** Every one of the sixteen carries **exactly 15**
> warnings (standard deviation 0 — EnergyPlus's capped report, not a measured spread).
>
> 🔴 **But the contingency against failure is perfect:**
>
> | | succeeded | failed |
> |---|---:|---:|
> | no non-convergence warning | **8,144** | **0** |
> | ≥ 1 non-convergence warning | 10 | **6** |
>
> **Non-convergence is a *necessary* condition for failure in this fleet and not a sufficient one** —
> 10 of the 16 survive it. Read with OPEN-56 this completes a two-stage picture the arc has been
> missing: **the 10 m³ zone-volume stub is universal (necessary, nowhere near sufficient) → the
> non-convergence is rare and contains every failure → six tip over.**
>
> **Where this leaves the item.** Its *"cosmetic"* verdict **survives as a statement about prevalence
> and fails as a statement about consequence.** 0.20 % is not a widespread problem; but every fleet
> failure lives inside it. ⚠️ **No causal claim is made from a contingency table** — this says where to
> look, not what happened, and the `thermal_mass=True` attribution in the item's title is **untested
> by this measurement.**
>
> **Evidence:** `extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §4;
> `openubem/outputs/comparisons/open09_fleet_err_perbuilding.csv` (8,160 rows),
> `open09_fleet_err_taxonomy.csv` (123 families); script
> `scripts/analysis/open09_fleet_err_taxonomy.py`.

> 🟢 **CLOSURE RECORD (T09 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, executing ruling R2).
> Folds into OPEN-56.**
>
> **The "inverted geometry" label was tested against a mechanism and not corroborated.** The
> `eplusout.err` upside-down-surface (`GetVertices: … is upside down!`) warning is universal to all
> 8,160 `auto`-mode runs, these six included — it is not a distinguishing property of the six, it is a
> universal property of the zoning mode (2026-08-18 T03, cited above in this section). The label
> "inverted geometry" is retired for these six; the failure text itself is `Temperature (low|high) out
> of bounds`, a thermal runaway, not a geometry error.
>
> **The six are the same six as OPEN-42's face (ii)** — re-derived exactly: intersection 6, symmetric
> difference 0 (2026-08-18 late, cited above).
>
> **What survives this closure, so the remediation debt is not dropped:** this item asked for a
> **per-building** post-hoc remediation (`10_fails_solution.md`, re-applied to six named buildings).
> The cause is now measured fleet-wide, present in all 8,160 buildings, not just these six — so a
> six-building patch would be the wrong shape of remedy and would hide the fleet-wide defect if applied.
> **The remediation decision is absorbed by OPEN-56's own closure condition** (correct zone volume
> fleet-wide, no exception), not silently dropped. No remedy is applied by this closure — OPEN-56 stays
> open, unauthorised.
>
> **This closure does not depend on T01** (this same plan's OPEN-55 B+ donor screen, a production code
> change) — OPEN-55 stays open, unproven in simulation, regardless of this closure.
>
> **Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §3;
> `openubem/outputs/comparisons/open11_open42_six_buildings.csv`; OPEN-56's own §-section.

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
> weakened.** `tests/test_step3_orchestrator.py` ~~was correctly left untouched: its
> `test_medium_office_idf_contains_elevator_equipment` asserts a *built IDF* contains the Elevators
> object, which is the load wiring and out of scope.~~ **Corrected 2026-08-18 (T01 of
> `implemenation/previous/PLAN_four-items-2026-08-18.md`): this sentence is loosely worded and reads as claiming
> a live test that never existed.** `test_medium_office_idf_contains_elevator_equipment` does not exist
> in `tests/test_step3_orchestrator.py` at HEAD and never has — it exists only in the archived mirror
> (`docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/test_step3_orchestrator.py:90`) and in two
> prior audit CSVs that already recorded the absence
> (`openubem/outputs/comparisons/open46_elevator_divergence.csv:13`,
> `open36_governance_resweep.csv:109`). **The load-wiring claim itself is correct** and is independently
> proved live by a different, purpose-built test, `tests/test_builder_elevators_wired.py` (committed at
> `6aeebb0`), which passes — see the closure note at the end of this section.
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

#### ✅ CLOSED 2026-08-18 — T01 of `implemenation/previous/PLAN_four-items-2026-08-18.md`. All four links verified whole at HEAD; the stated blocker (fact 7 of that plan) was stale.

**All four links in the elevator reporting chain verified live, by code citation and by running tests,
not by reading a document:**
- **Link 1 — load emitted into the IDF.** `openubem/idf/builder.py:40` imports `assign_elevators`;
  `:609` calls it. Proved by building an IDF, not by reading the call site: the plan's named test,
  `tests/test_step3_orchestrator.py::test_medium_office_idf_contains_elevator_equipment`, **does not
  exist in the live tree and never has** — corrected above, not fixed here. Link 1 is nonetheless
  proved live by `tests/test_builder_elevators_wired.py` (committed at `6aeebb0`), 2/2 passing: an
  elevator-eligible archetype (`LargeOffice`) built through `BuildingIDF.build` emits exactly one
  `ELECTRICEQUIPMENT` object tagged `EndUse_Subcategory == "Elevators"`; a non-eligible archetype
  (`SmallOffice`) emits none.
- **Link 2 — meter requested.** `openubem/idf/outputs.py:43`,
  `"Elevators:InteriorEquipment:Electricity"`, the 14th `HVAC_METERS` entry.
- **Link 3 — parsed and de-folded into its own column.** `openubem/results/parser.py:58`
  (`_ELEVATOR_METER`), `:489-493` (the guarded de-fold — the citation of `:346-349` earlier in this
  section is stale; the file has grown since it was written). `tests/test_parser_elevators.py`, 8/8
  passed, proves the guard both directions: `test_missing_elevator_meter_is_zero` (meter absent, no
  de-fold fires) and `test_elevators_defolded_from_equipment` (meter present, de-fold fires).
- **Link 4 — carried into carbon and the aggregator.** `openubem/results/carbon.py:98,121`
  (`elevators_eui`, `gwp_elevators_kgco2_m2`, folded into `gwp_total_kgco2_m2`);
  `openubem/results/aggregator.py:41,53` (`_STEP5_COLS`).

**Targeted tests, run 2026-08-18: 65/65 passed, 0 failed** — `test_step3_orchestrator.py` 18,
`test_parser_elevators.py` 8, `test_elevators.py` 28, `test_outputs.py` 11.

**Full-suite baseline, run 2026-08-18 (T01/A1, foreground):**

```
1875 passed, 55 skipped, 11 warnings in 1572.28s (0:26:12)
```

Matches the pinned baseline (1875 passed, 55 skipped, 0 failed, 0 errors) — the closure condition
`extra/MEASUREMENT_open-46_path-verification.md` set for itself is met.

**One documentary defect found, not a code defect: the register's own T05 passage (struck and
corrected in place, above) misdescribed a test that never existed.**
`test_medium_office_idf_contains_elevator_equipment` is not, and never was, a live test — it exists
only in the archived mirror
(`docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/test_step3_orchestrator.py:90`) and in two
prior audit CSVs that already recorded the absence
(`openubem/outputs/comparisons/open46_elevator_divergence.csv:13`,
`open36_governance_resweep.csv:109`). `tests/test_builder_elevators_wired.py`, committed at `6aeebb0`,
proves the same load-wiring fact live and passes — the chain was never actually broken by this gap,
only mis-cited.

**Closure: all four links verified at HEAD, in code and in live tests. OPEN-46 CLOSES. ID RETIRED.**
What this task cannot and does not prove: whether a fleet run today reports non-zero elevator energy —
that needs a fresh EnergyPlus simulation, not authorised here, and is a distinct question from the
already-adopted `phaseE_elevrb` baseline's own non-zero elevator EUI (this section, above), which
concerns a historical run's output, not HEAD's current code. That reproducibility gap belongs to
OPEN-48, not this item.

**Evidence:** `extra/MEASUREMENT_open-46_path-verification.md`.

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

> ✅ **Amended 2026-08-18 (T05 of `implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`) — the
> source of the original 36.4% / 19.2% is found; the contradiction is a scope difference, not an
> error, and both number-pairs stand.** Nothing above is struck: every figure in it is still correct
> for the population it describes.
>
> **Both original figures reproduce exactly** — `nyc_rural` **72 / 198 = 36.3636%**, `austin_rural`
> **47 / 245 = 19.1837%** — on a live re-read of
> `scratchpad/e-utci-09-backfill/backfilled/{nyc_rural,austin_rural}_01_buildings_backfilled.gpkg`,
> the UTCI arc's own Stage-6 working copy from the E-UTCI-09 partial backfill (CP-C, 2026-07-25; the
> files carry that date). **Director-verified by independent re-derivation** with `geopandas`, outside
> the task's script. That dataset is confirmed **untracked and gitignored** (`scratchpad/`,
> `.gitignore:41`; no commit history for the directory) and is **read by no part of the adopted
> pipeline**.
>
> **The fleet's tracked Stage-1 files were re-confirmed at 100.00% / 100.00% / 100.00%** for
> `nyc_rural` / `austin_rural` / `nyc_suburban`, independently of N06 and N15, plus a fourth cell
> (`austin_centre`) carried as a control — it matched the arc's own before/after figures on both
> datasets (84.50% tracked → 2.66% backfilled), validating the method before the headline numbers
> were trusted.
>
> **Consequences.** (a) **Blast radius is unchanged** — it is computed over the tracked files, which
> the scratch dataset is not part of and never was. (b) **The arc's closing constraint is reinforced,
> not weakened:** even the UTCI team's own best-effort backfill, run by hand on exactly these two
> cells, still left 36.4% / 19.2% unfilled — **source coverage, not imputation method, is the binding
> constraint.** (c) **This item does not need, and should not receive, a reconciliation toward one
> value.** 🔴 (d) **Custody risk:** the only dataset that reproduces the original numbers lives in
> gitignored scratch, in the same space the standing corpus warning covers. Re-verify its presence
> before citing it again.
>
> Full record: `extra/MEASUREMENT_open-12_height-residual-retrace.md`,
> `openubem/outputs/comparisons/open12_height_residual_retrace.csv`,
> `scripts/analysis/open12_height_residual_retrace.py`.

> ✅ **Amended 2026-08-19 (T07 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — the register's own
> uncomputed claim that OPEN-12 and OPEN-35 are "the same population seen from two sides" is now
> computed, and it is FALSE fleet-wide.** **OPEN-35 is a strict (proper) subset of OPEN-12**, never
> the reverse — a building missing *both* levels and height is by construction also a building
> missing height. The fleet 2×2 contingency sums exactly to 8,160. Both carried headline figures
> reproduced exactly on run 2 (`open48_refleet`): OPEN-12 **2,806 / 8,160 = 34.39%**, OPEN-35
> **2,611 / 8,160 = 32.00%**.
>
> **The residual that only OPEN-12 covers is 195 buildings (6.95% of OPEN-12)**, concentrated in
> `austin_centre` (102) and `austin_suburban` (40).
>
> **Why the register read them as one.** In `nyc_suburban` the two populations *do* coincide exactly
> — all 1,589 buildings miss both inputs — and the claim's arithmetic checks to the building
> (1,589 / 2,611 = 60.86% ≈ 61%). The impression is correct in that one cell and wrong fleet-wide.
>
> **Control.** Stage-1's `data_quality_flag` tokens (`no_height` / `no_floors`, stamped independently
> at acquisition) were cross-checked against the notna() predicates in every cell — **zero
> disagreements fleet-wide.** No imputation tier is exercised by either population; both are raw
> Stage-1 nulls.
>
> 🔴 **Consequence for planning: do not merge OPEN-12 and OPEN-35.** A merge would silently drop the
> 195-building residual that only OPEN-12 covers. Full record:
> `extra/MEASUREMENT_open-12-35_subset-check_2026-08-19.md`,
> `openubem/outputs/comparisons/open12_open35_subset_check.csv` (+`_buildings.csv`),
> `scripts/analysis/open12_open35_subset_check_2026-08-19.py`.

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
>
> 🟢 **Re-confirmed and narrowed 2026-08-18 (T03 of
> `implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`). Additive — nothing above is struck except
> the one number corrected below.** The discharge holds, and **two stale claims in this section are now
> closed.**
>
> **(1) This item's stated consequence — "a bare `pytest -q` therefore aborts at collection… the whole
> suite has not been runnable as a whole" (see the N09 paragraph below) — is FALSE at HEAD, by two
> independent mechanisms.** `pyproject.toml:52` now sets `testpaths = ["tests"]` (it landed with the
> OPEN-52 remedy), so bare `pytest -q --collect-only` and `pytest -q tests/ --collect-only` collect
> **identically: 1930 / 1930, exit 0 / 0**. Separately, and sufficient on its own, the draw-tier defect
> no longer aborts collection at all — it degrades to a scoped skip. **Positive control:** a
> deliberately broken untracked test file reproduced `exit 2` / `Interrupted: 1 error during
> collection`, proving the detection method would still catch a real regression; the control file was
> deleted and **director-verified absent** from the tree afterwards.
>
> **(2) Correction to this section's own 2026-08-13 note above: "the ~~**9**~~ tests that *do* need
> `_draw_tier`" should read **10**.** Nine carry an individual `@_SKIP_NO_DRAW_TIER` decorator; a tenth
> (`TestNoEUILeakage.test_no_function_code_references_eui_by_name`) is skipped by a **class-level**
> `skipif` that the count of nine missed. Live re-run: `pytest -q tests/test_draw_methods.py -rs` →
> **43 passed, 10 skipped**.
>
> **What is actually left of E-UTCI-12, stated as narrowly as the evidence allows.** The defect itself
> is unchanged and still live — `grep -c "_draw_tier" openubem/semantic/imputation.py` → **0**
> (director-verified again this pass). But **all ten skips are future-feature pinning, not a hole in
> reachable production coverage**: `_draw_tier` is unreachable by default
> (`IMPUTE_DRAW_METHOD_BY_TARGET` defaults to `{}`; `draw` stays out of `IMPUTE_ENABLED_TIERS`), so what
> the skips pin is the behaviour OPEN-17 would need **if** the user promotes the draw tier. **OPEN-13
> has no remaining technical content beyond "the draw tier's router wiring is unimplemented," and that
> is OPEN-17's scope, not this item's.**
>
> ⚠️ **One thing this task deliberately did NOT do, and it is a real limitation, not a rounding.**
> Reconciling how many of the whole suite's 55 skips are E-UTCI-12's, file by file, needs a full-suite
> run; the director forbade one here to avoid a second ≈17-minute pass. A **static skip-marker census**
> was substituted (73 marker sites across 12 files) and is **documentary only — it does not reconcile
> to a runtime count** and should not be quoted as if it did. The 55-skip figure quoted in this item is
> carried from `extra/FIX_open-52_temproot-remedy.md:173`, labelled as quoted rather than re-derived.
> **T06 of this plan closes that gap for free by running the full suite with `-rs`.**
>
> Full record: `extra/MEASUREMENT_open-13_eutci12-residual.md`,
> `openubem/outputs/comparisons/open13_eutci12_residual.csv`,
> `scripts/analysis/open13_eutci12_residual.py`.
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

#### 🟡 2026-08-12 — both defects addressed; **one fixed, one contained**. Report: `extra/FIX_open-13_height-cache-and-collection.md`; plan `implemenation/previous/PLAN_five-item-sweep-2026-08-12.md` §8 T03–T04.

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

#### ✅ 2026-08-13 — **the carried-forward weakness at `⚠️` above is now discharged.** T01 of `implemenation/previous/PLAN_five-more-items-2026-08-13.md`; report `extra/FIX_five-more-items-2026-08-13.md`.

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

> **Amended 2026-08-18 (overnight, X09 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). ✅ THE STEP THIS ITEM NAMED AS "THE NEXT THING" HAS
> BEEN TAKEN, AND IT SETTLES THE CONVERGENCE.**
>
> The item's own words: *"proving it needs one more step — showing that the fleet's
> `01_buildings.gpkg` was produced by a path that would have consumed the slice. That step is a
> measurement nobody has run, and it is the next thing on this item."* Three checks, and they agree:
>
> 1. **`openubem/config.py:141` — `FUSION_SOURCES_BY_TARGET: dict = {}` at HEAD.** `_fusion_tier`
>    (`openubem/semantic/imputation.py:627`) documents itself as *"a guaranteed no-op"* under this
>    default: `precedence_for` returns `[]` and `fuse()` never calls out to any source.
> 2. **Fusion stamps a distinct provenance token** — `FUSED_<SOURCE>_HIGH` / `_MED`, per the same
>    docstring (*"no value lands without a token"*).
> 3. 🔵 **Across all 8,160 buildings of run 2, rows carrying any `FUSED` token: ZERO** — while every
>    other imputation tier fires and stamps normally in the same column
>    (`VINTAGE_NAN_PERMISSIVE_DEFAULT` 4,255, `GROUPMODE_MED` 1,519, `HOTDECK_NEIGHBOR_HIGH` 90,
>    `HOTDECK_NEIGHBOR_MED` 46). **The machinery ran; the fusion tier alone contributed nothing.**
>
> **The control is the decisive part.** `nyc_centre` is the one cell with a **tracked** Overture slice
> (`overture_nyc_centre_slice.parquet`, `git ls-files`-confirmed). It carries **no `FUSED` token
> either.** So the path did not consume a slice **even where one exists**.
>
> **Verdict: the missing slices are a real but NON-OPERATIVE blocker.** The config gate closes before
> the slice is ever looked for. Two independent blockers stand between this project and a reproducible
> height backfill, and **the one this item names is not the binding one.**
>
> **Consequence for the OPEN-12 / OPEN-14 four-cell convergence, now adjudicable:** the backfill fills
> **nobody, in any cell**, so it cannot explain why those four cells are short of `height_m`.
> **The convergence is a coincidence of coverage; OPEN-12's residual is a source-coverage gap in OSM
> itself, not this item.** That confirms N15's refutation by a route N15 did not use.
>
> **Evidence:** report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X09.

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


> ✅ **Amended 2026-08-18 (night) (W09 of `implemenation/previous/PLAN_ten-tasks-2026-08-18-night.md`).
> Re-derived exactly on run 2, and the same run covers OPEN-14's corpus question.**
>
> **`height_m` null, fleet-wide: 2,806 / 8,160 = 34.39 % — exact against the 2026-08-06 figure.**
> The three 100 % cells reproduce one for one: `nyc_suburban` **1,589 / 1,589**, `nyc_rural`
> **198 / 198**, `austin_rural` **245 / 245**. **Zero buildings fleet-wide carry a present-but-zero
> height**, so the "0 means missing" ambiguity is still absent.
>
> Per cell the spread is wide and was not previously tabulated on this corpus: `la_rural` **0.67 %**,
> `la_suburban` 1.12 %, `nyc_urban` 2.25 %, `la_urban` 6.80 %, `austin_urban` 11.06 %, `nyc_centre`
> 16.40 %, `la_centre` 19.91 %, `austin_suburban` 26.09 %, `austin_centre` **84.50 %**, then the three
> at 100 %.
>
> 🔵 **The scope reconciliation of 2026-08-18 stands untouched** — both number-pairs describe different
> datasets and both are correct for theirs. What is new is that **the fleet-side figure now rests on a
> corpus that still exists**, where the original rested on one that does not.
>
> **Evidence:** `extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §5;
> `openubem/outputs/comparisons/open35_open12_input_recensus.csv`.

---

## 6. Theme E — Method and validation questions

### OPEN-18 — Q3, the √S vertical-form distortion ✅
**The largest open modeling problem in the project.** `scale_baseline_idf()` scales vertices in plan by

**Amended 2026-08-19 (late, **director**, at CP-1 of `implemenation/PLAN_layout-assign-untrimmed-2026-08-19.md`).** ⚪ **This item is NOT sized by the 48-building untrimmed sample, and the report says so rather than stretching the number.** T04 cut the slice this item names — small buildings in cold cells, the 10th/35th percentile slots of the four NYC cells, **n = 8**. That slice runs **−27.98 % pooled / −26.36 % median** against `auto`, versus **−25.00 % / −24.31 %** for the other 40. **The ≈3-point separation is far inside the slice's own spread of −12 % to −37 %**, so it supports no claim that the √S distortion bites measurably harder on small cold-cell buildings — and refutes none either. Sizing this item needs a purpose-built sample with many more small cold-cell buildings; the stratified-by-size design used here puts only 8 in the slice. Evidence: `extra/MEASUREMENT_open-03-18_untrimmed-sample.md` §6. **No change to this item's status, size or wording.**

🔴 **CORRECTED the same night (2026-08-19).** The slice figures in the amendment above rest on the
same multiplier-undercounted parser EUI (see the correction under **OPEN-03**). Multiplier-correct,
the **n = 8** slice is **−6.68 % pooled / −18.48 % median** rather than −27.98 % / −26.36 %.
**The conclusion is unchanged and if anything firmer: at n = 8 this slice supports no claim about
√S vertical-form distortion in either direction, and the correction moved it by more than the
3-point separation that was being discussed.** This item remains unsized.


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

### OPEN-47 — The office size-tier thresholds have no traceable external source, and our own research document contains a fabricated citation 🔴 **OPENED 2026-08-12** ✅ **CLOSED + ID RETIRED 2026-08-19**

✅ **CLOSED + ID RETIRED 2026-08-19** **on the user's ruling of 2026-08-19, as a deliberate documented departure** — explicitly the second of the two outcomes this section itself named, not a silent lapse. 🔴 **The decisive fact is that this was already decided, by the user, on 2026-08-12**, and the decision is recorded verbatim in the code it governs (`openubem/semantic/building_classifier.py:171-190`): *"keep area-only as the default; the floor-count half above is deliberately NOT applied by default — deferred, not rejected."* The item stayed live only because that ruling was never written up as a closure. 🟢 **The 2026-08-19 measurement strengthens the ruling's own stated reason rather than undermining it.** That reason was that the office size metric already multiplies by imputed levels, so a floor-count bound would make the archetype depend on the same imputed quantity twice; T03 then found that **167 of the 598 divergent buildings (27.9 %) have no observed floor count at all.** ⚠️ **What closing this does not settle, stated plainly so it is not mistaken for a clean bill of health: all 598 divergences are promotions and not one is a demotion.** The departure is therefore known to be *directional*, not neutral — area-only classifies offices systematically smaller than the source intends. That is accepted with open eyes, on the imputation argument above, and `use_floor_count` stays available and tested so the day floor-count coverage improves the decision can be reopened on evidence rather than rebuilt from scratch.


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
> ~~🔴 **Reason 1 it stays open — a substantive divergence from the source now that the source is known.
> The source's rule is area AND floor count** (`<2322 m² and ≤3 floors`, `2322–9290 m² and ≤5 floors`,
> `>9290 m² or ≥6 floors`). **`openubem/semantic/building_classifier.py:175-177` tests area only; the
> floor-count condition was dropped.** Not adjudicated. Any change here is gated by CP-M3 (OPEN-31):
> before/after accuracy on the labelled fixture, both numbers recorded.~~
>
> ✅ **Amended 2026-08-18 (T04 of `implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`) —
> Reason 1 IS adjudicated and no longer keeps this item open. The "Not adjudicated" above was stale:
> the ruling was on disk, in the code, for six days before this register sentence was last read.**
>
> **`openubem/semantic/building_classifier.py:167-189` carries a user ruling dated 2026-08-12**
> (corroborated by `PLAN_three-rulings-2026-08-12.md` §1.2, whose progress-log entries are stamped
> `completed 2026-08-12`; the code itself landed one day later, commit `6aeebb0`, 2026-08-13
> 15:25:31 — **both dates recorded, neither conflated**). **Ruling: keep area-only as the default; the
> floor-count half is deferred, not rejected.** `use_floor_count` stays in the code, default OFF, as
> the evidence for the decision — re-verified reachable end-to-end (constructor → `classify()` →
> `classify_building` → `_apply_rule_table` → `_office_size_tier`) and passed `True` in exactly two
> places repo-wide, both measurement scripts; **every production and test call site inherits the
> `False` default.**
>
> **The comment's measured-impact numbers were re-derived fresh by a newly written script — not a
> rerun of the original — and reproduce exactly. Director-verified by recounting the output CSV
> directly:** 598 / 8,160 (**7.33%**) archetype changes, **all promotions** (SmallOffice→MediumOffice
> **380**, MediumOffice→LargeOffice **161**, SmallOffice→LargeOffice **57**); **437 / 598** newly gain
> elevator-load eligibility and **0** lose it; `levels_source` of the 598: `OSM_OBSERVED` **85**
> (14.21%), `HEURISTIC_HEIGHT` **346** (57.86%), `GROUPMEDIAN_LEVELS_MED` **167** (27.93%); **166 of
> the 437** elevator-gaining buildings rest on `GROUPMEDIAN_LEVELS_MED`. Positive-controlled against
> three hand-verified transitions from `PLAN_three-rulings-2026-08-12.md:487-495` — all three matched
> before the fleet-wide figures were trusted. **Register §0's "record both side by side, do not
> reconcile" rule never triggered: nothing diverged.** Full record:
> `extra/MEASUREMENT_open-47_floorcount-divergence.md`,
> `openubem/outputs/comparisons/open47_floorcount_divergence.csv` (598 rows),
> `scripts/analysis/open47_floorcount_divergence.py`.
>
> 🔴 **OPEN-47 does not close, and it now stays open on Reason 2 alone** — the second fabricated DOI
> (Sun et al. 2021), the systemic Deru et al. (2011) wrong-locator pattern, the PNNL-23269 content
> question and two dead links, none of which this task measured. **The item's title and framing should
> be revised to stop presenting the area-vs-floor-count divergence as an open question.** The CP-M3
> (OPEN-31) gate named above is moot for Reason 1 — no change to the classifier is proposed, so there
> is no before/after to score.
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


> ✅ **Amended 2026-08-19 (T06 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — the two untraced
> thresholds explain ZERO of the residual fine-classification error. This de-scopes the item: the
> provenance gap is real, but it is not what is costing accuracy.**
>
> **Control (mandatory, passed):** reproduced **87 / 98 = 0.8878** fine top-1 and **98 / 98 = 1.0000**
> coarse top-1 on `tests/fixtures/labelled_archetypes_tagrich_v2.csv`, matching
> `extra/FIX_open-22_tagrich-gate.md` to four decimals.
>
> **Sweep.** Joint over `_OFFICE_SMALL_MAX_M2` and `_OFFICE_MEDIUM_MAX_M2` — 25 points each across
> ±50 % of current values, **plus the CBECS 10k / 25k / 50k / 100k / 200k ft² bin edges** — **782
> valid grid points.** Constants monkeypatched per call and verified restored afterwards; **no file
> was edited.**
>
> **Result: no grid point beats 88.8 % fine top-1. Not one of the 11 baseline fine errors is fixed
> anywhere on the grid.** Coarse top-1 is 100.0 % at every point, and this is structural rather than
> lucky — every office tier maps to `commercial`, so the coarse exam **cannot** see a bin edge move.
>
> **Where the 11 errors actually live**, traced individually: **3** never reach the office-size rule
> at all; **3** are `OpenUBEMUnknown`-expected rows where an office was wrongly emitted — a branch
> `_office_size_tier` can never produce; the remaining **5** do route through the office-size rule,
> but their small footprint areas point at **`levels_imputed`**, not the bin edge, as the driver.
>
> **Consequence.** The 🔴 line above — *"the two thresholds that decide a third of the labelled exam
> remain UNTRACED"* — still stands as a **provenance** finding and this item stays open on it. But
> any plan that proposed re-tuning the thresholds to buy accuracy is now refuted by measurement.
> **Next lead, named and NOT taken:** `_impute_levels` and the rule-entry conditions. Full record:
> `extra/MEASUREMENT_open-47_threshold-sensitivity_2026-08-19.md`,
> `openubem/outputs/comparisons/open47_threshold_sweep.csv`,
> `openubem/outputs/open47_threshold_sweep_surface.png`,
> `scripts/analysis/open47_threshold_sweep_2026-08-19.py`.
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

*From `implemenation/previous/PLAN_five-more-items-2026-08-13.md`, tasks T02 and T03. Report for T03:
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

✅ **THE REMAINING QUESTION IS ANSWERED — 2026-08-19, T03 of
`implemenation/previous/PLAN_board-17-ready-2026-08-19.md`.** Record:
`extra/MEASUREMENT_open-47_floorcount-condition.md`; artifact
`openubem/outputs/comparisons/open47_floorcount_condition.csv`; harness
`scripts/analysis/open47_floorcount_condition_2026-08-19.py`.

> The citation was already settled — Chen, Hong & Piette (2017), *Applied Energy* 205, 323–335,
> Table 1. What kept this item open was one thing: the source's rule is *area **AND** floor count*
> (`<2322 m² and ≤3 floors`) and our implementation keeps the area test and **drops the
> floor-count test**. That divergence is now sized.
>
> **598 buildings classify differently under the source's full rule — and every one of them is a
> promotion, not a demotion.** 380 SmallOffice→MediumOffice, 161 MediumOffice→LargeOffice, 57
> SmallOffice→LargeOffice. **Zero demotions.** The omission is therefore not neutral in aggregate:
> dropping the floor-count test systematically classifies offices **smaller** than the source would.
>
> 🔴 **167 of the 598 (27.9 %) have no floor count at all** — no OSM levels and no usable
> height. For those the source's rule is **not applicable as written**: restoring the floor-count
> test would make their classification depend on an **imputed** storey count, which is precisely the
> mechanism **OPEN-35** exists to fix. Adopting the source's rule before OPEN-35's remedy is wired
> would import that defect into the classifier for 167 buildings.
>
> ✅ **Overlap with OPEN-35's own changed set: 0.** The two populations are disjoint, so neither
> fix perturbs the other's measurement.

⚠️ **§1 summary row reconciled 2026-08-19 (director).** The §1 table still framed this item as
open on the *citation* question, which this §-section had already recorded as adjudicated on
2026-08-18. The §-section was right and the summary row was stale; the row is corrected rather than
the section. ⚠️ **Recommended to the user, NOT taken here:** decide whether to adopt the source's
full area-and-floors rule (sequenced after OPEN-35), or to record the area-only test as a deliberate,
documented departure. **No classifier change was made.**

### OPEN-48 — The adopted baseline run cannot be reproduced from this repository 🔴 **OPENED 2026-08-12**

**Found by** auditing OPEN-46's reversal (T04/T05 of `PLAN_three-new-items-2026-08-12.md`), not by
running a task. Sixth consecutive pass in which this register grew that way.

**The finding, in one line.** The adopted `phaseE_elevrb` run was produced by code that is not in this
repository, and running the pipeline from the current tree would produce different numbers and a
missing column.

**Evidence, all director-derived.**

| Fact | Live tree today (as of 2026-08-12) | Adopted run's own outputs |
|---|---|---|
| `assign_elevators` called from `builder.py` | ~~**no** — `git log --all -S assign_elevators -- openubem/idf/builder.py` is empty; `hasattr(builder, 'assign_elevators')` is `False`; zero occurrences of "elevator" in the file~~ 🟢 **now YES, since commit `6aeebb0` (2026-08-13) — see Amendment 2026-08-18 below** | n/a |
| `elevators_eui_kwh_m2` in results | ~~**absent** at HEAD~~ 🟢 **now PRESENT** — see Amendment 2026-08-18 below | **present**, 3,561 of 8,160 rows non-zero, Σ = 12,508.8 kWh/m² |
| `gwp_elevators_kgco2_m2` | ~~**absent** at HEAD~~ 🟢 **now PRESENT** — see Amendment 2026-08-18 below | **present** |
| elevator meter in `outputs.py` | ~~**absent** at HEAD (13 meters)~~ 🟢 **now PRESENT (14 meters)** — see Amendment 2026-08-18 below | requested — the column could not exist otherwise |
| elevator equipment emitted by a live build | ~~**zero objects**, all 10 elevator archetypes~~ 🟢 **now 1 object per eligible building, 0 for non-eligible — see Amendment 2026-08-18 below** | 87 of 87 eligible buildings in `nyc_urban` carry non-zero elevator EUI |

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

> **Amendment 2026-08-18 (T01 of `implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`) — the
> evidence table above was re-derived in full at HEAD. Every one of its five rows is now the opposite
> of what it said on 2026-08-12; struck in place above, not deleted.** Full record:
> `extra/MEASUREMENT_open-48_reproducibility-retest.md`,
> `openubem/outputs/comparisons/open48_reproducibility_retest.csv`.
>
> **Re-derived, with a positive control** (`git log --all -S "def assign_elevators" --
> openubem/idf/elevators.py` finds commit `ef19141`, proving the detection method works): `builder.py`
> imports and calls `assign_elevators` (`git log --all -S assign_elevators -- openubem/idf/builder.py`
> now returns commit `6aeebb0`; `hasattr` is `True`; 3 "elevator" occurrences); `elevators_eui_kwh_m2`
> is present in `parser.py`/`aggregator.py`; `gwp_elevators_kgco2_m2` is present in `carbon.py`;
> `HVAC_METERS` now carries 14 meters including the elevator meter. **A live, direct build** (not the
> pytest fixture — `BuildingIDF(row).build()` called standalone from the analysis script, no network,
> no EnergyPlus execution) of a LargeOffice/12-level archetype emits exactly **1**
> `ElectricEquipment` object with `EndUse_Subcategory == "Elevators"`; the same method on a
> non-eligible SmallOffice/1-level archetype emits **0** (negative control).
>
> **Both halves the item separates are now live and committed.** `git status --porcelain` on
> `builder.py`, `elevators.py`, `outputs.py`, `parser.py`, `aggregator.py`, `carbon.py` is empty —
> nothing in either the load-wiring or the reporting half is uncommitted.
>
> 🟢 **New check this amendment adds: the OPEN-49 per-building-seed fix is also fully committed** —
> `openubem/semantic/__init__.py` carries `_per_building_rng` and an unconditional
> `_get_cross_archetype_loads()` call at the `enrich_semantics` site; its most recent commit is
> `82bbd25`; `git status --porcelain openubem/semantic/` is empty.
>
> 🔴 **What this does NOT resolve, stated explicitly.** No third fleet run exists on disk —
> `docs/docs_VALIDATION/validations/overAll/results/` holds only `phaseE` and `phaseE_elevrb`, matching
> ruling 4's explicit decline of a post-fix re-run. **The provenance gap is no longer "code is
> missing" — it is now solely "no post-fix fleet re-run has been executed," plus the already-recorded,
> separate fact that the adopted run's own original `01_buildings.gpkg` no longer exists.** OPEN-48's
> own stated closing condition ("until OPEN-49 is fixed **and** the fleet is re-run a third time") is
> now half-satisfied (OPEN-49's mechanism is fixed) and half not (no re-run) — **the item correctly
> stays OPEN**, but the reason has narrowed and is recorded here so it is not re-litigated as a
> code-provenance question again. No remedy is recommended by this amendment; whether to authorise a
> third fleet run remains a ruling owed to the user, per OPEN-49's own record of ruling 4.**


> ✅ **CLOSED + ID RETIRED 2026-08-18 (late)** (T01 of `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`).
>
> **The blocker is discharged.** This item's operative condition was that no post-fix fleet re-run
> existed against which the adopted figure could be checked. **One now exists.** `open48_refleet3` ran
> all twelve cells on work directories pre-seeded with run 2's cached `01_buildings.gpkg`, so the OSM
> input was byte-identical and **code was the only variable**. Twelve started, twelve landed.
>
> **The measured answer, per cell, with every Unknown building removed from both sides so OPEN-55's
> contamination is excluded by construction: +0.0004, +0.0001, −0.0001 kWh/m², and −0.0906 / −0.0614
> on the two cells that had no Unknowns at all — under 0.08 %.** Every classified building changed
> value and no cell mean moved, which is exactly the signature of a fix that reseeds a draw without
> changing the population it draws from.
>
> 🔴 **The item closes on a negative result, and that is the honest closure.** Three fleet runs were
> spent asking what the OPEN-49 window-randomisation fix was worth in fleet kWh/m². The answer is
> *nothing outside noise*. There is no longer a mechanism on the table by which the adopted figure is
> wrong **for the reason this item suspected**.
>
> ⚠️ **What closing this does NOT discharge, carried forward so it is not lost with the ID:** the
> adopted run's Unknown path inflates its fleet figure by an estimated **+4.06 kWh/m² (2.6 %)** —
> measured on run 2, inferred for the adopted run, **reported and never subtracted**. That belongs to
> **OPEN-55**, not here. And the code-provenance gap this item opened on — that the adopted run's
> elevator wiring was never committed — is unchanged by the re-run; it is closed only in the sense
> that the run's *result* is now reproducible in magnitude, not that its *code state* was recovered.
>
> **Evidence:** `extra/MEASUREMENT_open-48_third-fleet-run.md`;
> `openubem/outputs/comparisons/open48_run3_vs_run2_cell_delta.csv`;
> `implemenation/previous/PLAN_open-48-third-fleet-run-2026-08-18.md`.

---

### OPEN-49 — One reclassified building re-randomises the windows of every unidentified building in its cell ⚠️ **MECHANISM FIXED 2026-08-17 — CLOSURE BLOCKED on the OPEN-48 re-run ruling 4 declined**

✅ **CLOSED + ID RETIRED 2026-08-19** **on the user's ruling of 2026-08-19, jointly with OPEN-55.** This item's closure was blocked on one thing only — that the mechanism fix of 2026-08-17 had never been demonstrated on real simulation output. It now has been. OPEN-55's acceptance test (`nyc_suburban`, 1,589 buildings, job 1274983) returned the archetype histogram **bit-identical** to baseline with **0 failures**, which is precisely what per-building determinism predicts and what the old shared-RNG mechanism could not have produced. 🟢 **The evidence is independent of its own authors:** the run drew from a freshly seeded, independently classified GDF rather than reusing an earlier attempt's artifacts. ⚠️ **Two things this closure does not do.** It does not retract the caveat on 159.2157 — that figure was evidence internal to this item and is **still not a fleet figure**; the adopted baseline remains 157.1 kWh/m² pooled until the T03–T05 restatement lands at CP-2. And it does not certify reproducibility in general — it certifies that this mechanism, on this cell, no longer moves buildings nobody touched.


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
*Surfaced by T05 of `implemenation/previous/PLAN_five-more-items-2026-08-13.md` while re-checking OPEN-29's
eight IDs. Reported, deliberately not adjudicated — resolving it was outside that task's scope.*

**What is wrong.** Two lineages travel under the same ID, and each source is internally consistent
with itself, so neither reads as an error from inside:

| Source | What it says `E-LA-16` is |
|---|---|
| `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:279` — **its own defining text** | cooling-coil-design-UA / cooling-tower-UA-autosize failure family |
| `implemenation/previous/PLAN_compute-queue.md:343` (manager-verified fact, 2026-08-06) | one of C06's five inherited `CheckWarmupConvergence` "cosmetic" log entries (with E-LA-14/18/19/23) |
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

#### ✅ CLOSED 2026-08-18 — T02 of `implemenation/previous/PLAN_five-items-2026-08-18.md`. Adjudicated on evidence; the code comment was wrong.

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

> ✅ **Addendum 2026-08-18 (T02 of `implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`) — the
> verdict is unchanged; its evidence grade improves, and one sentence above is corrected.**
>
> ⚠️ **Director note on how this task came to run: the plan that dispatched it was written against a
> stale reading of this register.** OPEN-51 had already been closed and its ID retired earlier the
> same day, by T02 of `PLAN_five-items-2026-08-18.md`. The executor found this, **did not stop on it**,
> and re-ran all five checks against the live tree anyway — which is the only reason the correction
> below exists. **No register damage resulted** (that task held no pen and made no edit). The other
> four items in its plan were director-checked afterwards and are all genuinely live rows.
>
> ~~The arc's own raw `.err` evidence for the three named buildings is gone from this machine~~ —
> **that claim was scoped to a search of `debug/storey-Matching/results/*` and
> `docs/docs_DONE/SETUP/layoutAssigner/` only. A repository-wide search found the raw `.err` files for
> all three named buildings** under
> `scratchpad/t19_t01_t05_work/work_t04/la_urban/sim/way/{402036176,402036789,1395739331}/eplusout.err`
> — task-numbered directories matching the structural-fixes plan's own T04, **dated 2026-07-23 22:20,
> the same day `E-LA-16` was minted** (director-verified: the files exist and predate this pass).
> They match Reading A's quoted text exactly, **including the two points the E02-harvest substitute
> could not reproduce** — the Fatal on `way/402036789` and `way/1395739331`, and the 16-Severe count
> on `way/402036176` (against that harvest's 0-Fatal / 23-Severe). The discrepancy the closure above
> reported honestly rather than smoothing over is therefore **explained: it was a run-config
> difference, exactly as suspected.**
>
> **Evidence grade upgrades from documentary-plus-corroborating-substitute to
> documentary-plus-located-original.** `git blame` additionally confirms the wrong
> `CheckWarmupConvergence` grouping entered via an unrelated batch commit (`69373f9e`) **citing no
> evidence at all**, and that the correction is live at HEAD (`b2d0220`).
>
> 🔴 **Custody risk, flagged and NOT acted on.** Those three `.err` files sit in gitignored scratch
> — the same space the standing corpus-erosion warning covers. They are the only located originals.
> **Archiving them into `extra/` is recommended to the user as a decision, not performed by this
> pass.** Record: `extra/MEASUREMENT_open-51_ela16-provenance.md`.

---

### ~~OPEN-52~~ — A fixed `--basetemp` makes two concurrent pytest sessions delete each other's temp directories — 🟢 **CLOSED 2026-08-18 — ID RETIRED** ~~🔴 **OPENED 2026-08-13**~~
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

#### 🔴 STAYS OPEN 2026-08-18 — T01 of `implemenation/previous/PLAN_five-items-2026-08-18.md`. The collision is reproduced and real; the specified remedy is blocked by a second, newly-found defect.

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

#### 2026-08-18 (later) — T01 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`. Ruling `3a` given and implemented; both A/B and C's before/after measured directly.

**The owed ruling from sub-question (b) above is now given by the director:** move pytest's temp
root inside the repository via `PYTEST_DEBUG_TEMPROOT`, rather than either a fixed repo-relative
`--basetemp` (the original, collision-prone config) or an ACL repair on the locked
`pytest-of-o_iseri` (rejected — needs admin rights this session lacks, is machine state outside the
repo, and `icacls` against that directory is itself access-denied). Read directly from pytest 9.0.3
source (`_pytest/tmpdir.py:140-218`): the `--basetemp` branch unconditionally `rm_rf`s a fixed path
at session start (the collision); the `PYTEST_DEBUG_TEMPROOT` branch allocates a per-session
numbered directory under the chosen root and never wipes a live sibling. Choosing `<repo>/.pytest_tmp`
as that root means the locked `pytest-of-o_iseri` directory is **bypassed entirely, never touched**
— the lockout is not repaired, it is routed around.

**Two file changes, nothing else:** `addopts = "--basetemp=.pytest_tmp"` deleted from
`pyproject.toml` (`testpaths`, `tmp_path_retention_policy`, `tmp_path_retention_count` untouched);
a new repository-root `conftest.py` sets `PYTEST_DEBUG_TEMPROOT` to the absolute path of
`<repo>/.pytest_tmp` at import time (verified early enough empirically, not assumed).

**Four verifications, all passed, real output:**
- **(A) root moved:** `tests/test_results_denominator.py` alone → `7 passed in 0.68s`; session
  landed at `C:\Users\o_iseri\Desktop\OpenUBEM\.pytest_tmp\pytest-of-o_iseri\pytest-0\` — matches
  the specified layout exactly.
- **(B) locked directory untouched:** `%LOCALAPPDATA%\Temp\pytest-of-o_iseri` exists (it predates
  this task) but its `LastWriteTime` (April 1, 2026) is unchanged after the run — confirmed by
  direct `Get-Item` inspection, not inferred.
- **(C) collision gone, before AND after measured:** the predecessor's Design-3 busy-loop test
  (`scratchpad/open52/test_collision.py`, gitignored) was run twice — once against the *old* config
  (`addopts` temporarily restored) and once against the *fixed* config, session B started 3s after
  session A each time. **Before:** session B failed with `FileExistsError` cascading from `rm_rf`'s
  `OSError [WinError 145]` — same signature as the original diagnosis, reproduced twice
  independently (once before the full-suite run, once redone after it, since the first run's
  numbered-directory evidence was itself cleaned up by `tmp_path_retention_policy = "failed"`
  following the full-suite run). **After:** both sessions passed (`17.67s`/`17.71s`) and landed in
  distinct numbered directories, `pytest-0` and `pytest-1`, confirmed by each session writing its
  own resolved `tmp_path` to a pid-tagged log file read immediately off disk.
- **(D) nothing regressed:** full suite, alone, foreground, to completion —
  **`1875 passed, 55 skipped, 11 warnings in 1079.75s (0:17:59)`** — exact match to the pinned
  baseline, 0 failed, 0 errors.

✅ **RULED 2026-08-18 — CLOSED, ID RETIRED. The recommendation below is accepted.** Director's independent re-verification and the one carried-forward condition are recorded in this item's §1 table row; the short form is: the fix is real and verified on disk, and it is **uncommitted**, so it must be committed or a fresh clone reproduces the item.

⚠️ ~~**RECOMMENDED DISPOSITION: CLOSE + RETIRE THE ID.**~~ **(accepted — see above)** All four verifications passed with real,
reproduced-twice-where-it-mattered evidence; both previously-rejected alternatives remain rejected
for the reasons given above; no open sub-question remains. **Not marked CLOSED here — the director
disposes.**

**Evidence:** `extra/FIX_open-52_temproot-remedy.md`.

---

### OPEN-53 — 874/875 E02 harvest directories are missing `.sql`/`.end`, concentrated in two Austin sub-cells 🔴 **OPENED 2026-08-18**

> **Amended 2026-08-18 (overnight, X06 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). ⚠️ THE CUSTODY EXPOSURE IS NOW A NUMBER, AND THE
> ITEM'S OWN "no local artifact is currently named as the next step" IS ANSWERED.**
>
> | corpus | files | size | largest class |
> |---|---:|---:|---|
> | `open48_refleet` (**run 2 — seven live items rest on it**) | 41,014 | **79.75 GB** | `.sql` **76.23 GB** (96 %) |
> | `open48_refleet3` (run 3) | 43,162 | 45.73 GB | `.sql` 42.43 GB (93 %) |
> | `open48_repeat` | 3,711 | 26.89 GB | `.sql` 26.03 GB (97 %) |
> | **total under `%LOCALAPPDATA%\Temp\ubem_validation`** | **87,887** | **152.4 GB** | **145 GB of `.sql`** |
>
> **Not yet swept:** directory mtimes across `nyc_centre`, `austin_suburban` and `la_rural` read
> 2026-08-12/13 with full entry counts — none carries the **2026-08-17 16:21** signature that emptied
> E02.
>
> 🔵 **The useful finding is how cheap the evidence is compared to the bait.** The sweep that took E02
> targeted the largest files. In run 2 the material this arc actually cites is small: **`.err`
> 0.091 GB** (the fleet error taxonomy, OPEN-09, OPEN-56's control, OPEN-42), **`.gpkg` + `.csv` +
> `.geojson` 0.027 GB** (OPEN-35, OPEN-12, OPEN-08, OPEN-10), and `.idf` 3.36 GB (needed only to
> re-run an intervention). **Under 0.12 GB preserves every published finding of this pass; ~3.5 GB
> preserves the ability to re-run one. The other 76 GB of `.sql` is what attracts a sweep, and it is
> re-derivable from the IDFs.**
>
> ⚠️ **Registered as an observation, not a remedy. No file was moved, copied or deleted.**
>
> 🔵 **And one of this item's own premises is now falsified in the reassuring direction.** X05 of the
> same pass found the **E02 parquet manifests survived** the 2026-08-17 sweep — 61 files across all
> twelve cells, still carrying `vintage_standard`. The sweep took the large files, not the small ones.
> **"E02 is gone" is too strong and should not be repeated**; what is gone is E02's `.sql` and `.idf`.
>
> **Evidence:** report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md` §X06, §X05.

*Found by T03's `.eio` census (`implemenation/previous/PLAN_five-items-2026-08-18.md`) while establishing
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

~~**First measurement, not yet made:** whether these are genuine incomplete/failed EnergyPlus runs (read
their `.err` tails for a Fatal or a truncation), a harvest-timing artifact (fetched mid-run, before
`.sql`/`.end` were written), or something else. No `.err` content from these specific directories has
been read yet — this item is opened on the census count alone, per this task's scope.~~

**Amended 2026-08-18 (T02 of `PLAN_four-items-2026-08-18.md`): the `.err` measurement has now been
made.** Census re-derived from scratch and matched fact 1 exactly (40,800 dirs, 40,800 `.eio`/`.err`,
39,926 `.sql`, 39,925 `.end`). The 875 short directories (union of missing `.sql` or `.end`) classify
as **874 `completed`, 1 `truncated`, 0 `fatal`, 0 `empty`** — against a 200-directory healthy control
that classifies **200 `completed`, 0 `truncated`, 0 `fatal`, 0 `empty`**. **Zero of the 875 are genuine
EnergyPlus failures**; the `completed` rate (99.9%) is statistically indistinguishable from the control
(100.0%) — this retires hypothesis 1 (genuine incomplete/failed runs). ~~The run started (produced
`.err`) and, for `.eio`-bearing directories, got far enough to write geometry, but did not reach a state
that writes `.sql`... or `.end`~~ was the wrong model: **874 of the 875 runs reached EnergyPlus's own
completion state** (`EnergyPlus Completed Successfully-- N Warning; 0 Severe Errors`) — only the output
files are missing, not the simulation. This is a **batch-scoped harvest gap**, not an incomplete-run
signature: `austin_suburban_fast_zone` and `austin_suburban_floor` are each missing `.sql`/`.end` in
**100.0%** of their 437-directory populations, with the same buildings' other three modes
(`auto`/`building`/`layout_assign`) fully populated — ruling out both a building-level and a
mode-wide cause. Neither `.eio` nor `.err` records `Output:SQLite` request status in any directory
checked (short or healthy), so **this artifact set cannot say whether the shortfall is IDF-level
(output never requested for these two batches) or harvest/copy-level** — that distinction needs the IDF
text or the harvest script's own logs, neither available under `HARVEST_ROOT`. The single
`nyc_centre_fast_zone/way_1240348353` exception is a different, unresolved case: its `.err` stops
mid-input-processing (zone-infiltration warnings, before "Beginning Simulation"), with no Fatal, no
Severe, no completion marker — **not determinable from `eplusout.err`**, consistent with a killed or
interrupted process but not diagnosable from this artifact. Full detail:
`extra/MEASUREMENT_open-53_missing-sql.md`; data: `openubem/outputs/comparisons/open53_missing_sql_census.csv`
(script: `scripts/analysis/open53_missing_sql_census.py`).

> **Ruling 2026-08-18 (director, CP-1 of `implemenation/previous/PLAN_four-items-2026-08-18.md`, re-derived
> from raw artifacts, not from the executor's report). The original question — why are the `.sql`/
> `.end` missing — is ANSWERED. The item STAYS OPEN, narrowed to a different question: custody, not
> cause.**
>
> **What happened:** the files were produced, harvested and inventoried on 2026-08-11, then deleted by
> a process outside this repository at 2026-08-17 16:21, which also emptied the entire E02 IDF corpus.
> Three pieces of evidence, all independently checked:
> 1. `openubem/outputs/comparisons/e02_corpus_inventory.csv` (mtime 2026-08-11 20:58) records
>    `n_end=437` for both `austin_suburban,fast_zone` and `austin_suburban,floor` — so
>    `Output:SQLite` *was* requested and `.end` files *did* exist on 2026-08-11. The
>    IDF-config-never-requested branch is retired.
> 2. Every one of the 874 short run directories carries an identical directory mtime of
>    **2026-08-17 16:21**, against 2026-08-10 21:38/21:58 for the healthy sibling batches. A
>    directory's mtime changes only when an entry is added or removed inside it, so the removal was one
>    sweep at one instant.
> 3. No code in `scripts/` or `openubem/` deletes `eplusout.sql` or `eplusout.end` (grep for
>    `unlink`/`rmtree`/`os.remove` against those names returns nothing) — the sweep was external to
>    this repository. The same sweep emptied every `idfs/` directory under
>    `%LOCALAPPDATA%\Temp\ubem_e02_fleet\<cell>\step3_<mode>\` (checked across four cells and four
>    modes, `n=0` in all sixteen), consistent with a single disk-space reclamation pass that targeted
>    the largest files fleet-wide.
>
> **No published number is affected.** `open01_denominator_swap.csv` carries `new_eui_kwh_m2` for all
> 437/437 buildings in both affected batches — results were parsed before the sweep, so the adopted
> 157.1 kWh/m² pooled baseline does not depend on the deleted files. OPEN-53 is an artifact-custody
> finding, not a results defect.
>
> **What keeps the item open is the custody risk, not the original question.** Nothing in this
> repository or on this machine prevents the same sweep from recurring against any other artifact this
> arc still depends on. **Annotation, entered here per this ruling:**
> `e02_corpus_inventory.csv` (2026-08-11) is now falsified by disk for the two `austin_suburban` rows
> above (it records `n_end=437`; disk holds 0) and must be read as a **2026-08-11 snapshot, not the
> current state of the harvest**. Any future task citing it must re-verify presence on disk first. **No
> local artifact is currently named as the next step** — the register does not invent a remedy where
> none has been measured.

⚠️ **Registered, not scheduled. No remedy authorised.**

**Evidence:** `openubem/outputs/comparisons/open37_eio_census.csv`;
`extra/MEASUREMENT_open-37_eio-fetch-closure.md` (where the gap was first reported, out of that
item's own scope); `openubem/outputs/comparisons/open53_missing_sql_census.csv`;
`extra/MEASUREMENT_open-53_missing-sql.md` (2026-08-18, T02 — the `.err` classification and control).

**Amended 2026-08-18 (T05 of `implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`) — custody
consequences discharged.** Both carried-forward consequences are applied. **(1)**
`openubem/outputs/comparisons/e02_corpus_inventory.csv` is annotated by a **sidecar**,
`e02_corpus_inventory.SNAPSHOT_NOTICE.md`, rather than by editing the CSV: the gate
`grep -rn e02_corpus_inventory scripts/ openubem/ tests/ docs/` returned a single hit outside `docs/`,
`scripts/analysis/e02_corpus_inventory.py:15`, which is the **writer**, not a reader — no code parses
the CSV back in, and its bytes are untouched (mtime still 2026-08-11 20:58, director-verified).
**(2)** The two falsified rows re-verified live on 2026-08-18: `austin_suburban,fast_zone` and
`austin_suburban,floor` both record `n_end=437` in the CSV and both show **`n_end=0, n_sql=0` on disk
today**, building directories intact at 437/437. Corpus emptiness independently re-confirmed across
3 cells × 5 modes — all 15 sampled `idfs/` directories empty, mtimes clustered at 2026-08-17 16:21
across unrelated cells. *(Director's own control, run separately: `austin_suburban,auto` returns
437 dirs / 437 `.end` / 437 `.sql` on the same disk at the same moment — so the zero is specific to the
two swept batches, not an artifact of how the count is taken.)*

🔴 **Planning rule, binding on this arc from 2026-08-18.** Any plan depending on a `%LOCALAPPDATA%`
E02 artifact (`ubem_e02_harvest` or `ubem_e02_fleet`) **must re-verify presence on disk at planning
time and must not cite `e02_corpus_inventory.csv`, or any other dated census, as current state.** The
one known exception is `scratchpad/e-la-20-investigation/i03/work_part1/` — 4 surviving IDFs covering
2 of the 3 `E-LA-40` buildings in both classifications, mtime 2026-07-25, outside the swept tree —
**and that exception is itself fragile**: `scratchpad/` has no retention guarantee and must not be
planned around beyond the investigation currently using it.

✅ **RULED 2026-08-18 (director) — OPEN-53 STAYS OPEN as a standing custody risk; T05's recommendation
is accepted, and the argument for it is the right one.** There is no measurement question left: the
cause is answered, the falsified rows are documented, the corpus emptiness is re-confirmed. But
"discharged" would mean the *risk* is retired, and nothing in this pass changed why a process outside
this repository can empty these paths without the project's knowledge, or stops it recurring — to the
same paths, to `scratchpad/`, or to any future artifact held outside the repo. The hazard was
demonstrated still live during this very pass. Closing the item would convert a standing risk into a
one-time incident and delete the only place it is tracked. **Its closure condition, recorded so this
does not stay open forever by default: OPEN-53 closes when E02 artifacts required by open work are
either regenerated inside a durable location or formally declared expendable.**


> 🔵 **Amended 2026-08-18 (late) (T07 of `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`).
> Part of the closure condition is discharged by accident, and the same stroke creates new exposure.**
>
> The closure condition reads: *"OPEN-53 closes when E02 artifacts required by open work are either
> regenerated inside a durable location or formally declared expendable."*
>
> ✅ **They were regenerated.** Runs 2 and 3 (`open48_refleet`, `open48_refleet3`) rebuilt every
> building's IDF and simulation output, including all six OPEN-42 buildings and all three OPEN-07
> buildings — the exact artifacts two open items were blocked on. **This pass's entire OPEN-56 finding
> rests on them.**
>
> 🔴 **But not inside a durable location.** They live in `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet{,3}/` (path written with forward
> slashes) — the same volatile class of path the 2026-08-17 sweep emptied. **The custody risk is not
> reduced; it is now pointed at a different set of files, and those files are load-bearing for
> OPEN-42, OPEN-11, OPEN-07 and OPEN-56.**
>
> **Open action for the user, costed:** copying the six OPEN-42 buildings' and three OPEN-07
> buildings' IDFs plus their `eplusout.err`/`.end` into a durable location is a few megabytes and
> would discharge the condition for the work that actually depends on them. **Not done here — writing
> into the repository is a user decision, and the `.sql` files are large.**
>
> ⚠️ **Correction to a claim now falsified by this pass:** OPEN-42's 2026-08-18 ruling states that the
> IDF corpus needed for its next step *"no longer exists on disk"*. **That was true of the E02 corpus
> and false of the project as a whole** — a newer corpus existed the whole time. Recorded here because
> a custody-reasoning failure is this item's own subject.
>
> **Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §6.

> 🔵 **Amended 2026-08-19 (T10 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, ruling R3). The costed
> action from the 2026-08-18 (late) amendment is now done.**
>
> The six OPEN-42 buildings' and (two of three) OPEN-07 buildings' IDFs plus their `eplusout.err`/
> `.end` — the material the previous amendment named and costed at "a few megabytes" — are now copied
> into the repository at `docs/validations/overAll/evidence/open48_runs/`, alongside the OPEN-56 A/B
> arms' raw per-building `.err`/`.end` (70 buildings, 140 arm-sides) and a reconstruction of OPEN-07's
> third building (`way/401910463`, no original survives anywhere; a `layout_assign` rebuild reproduces
> its register-cited fatal signature byte-for-byte). **323 files, 12,565,016 bytes (0.0126 GB),
> every MD5 independently re-verified against the copy twice over, no `.sql` included.** Manifest with
> per-file source path, MD5, size and citing item: `docs/validations/overAll/evidence/open48_runs/MANIFEST.md`.
> Full write-up: `extra/MEASUREMENT_open-53_evidence-preservation_2026-08-19.md`.
> **Director control, 2026-08-19:** file count, byte total, zero-`.sql` and a random 40-file MD5
> re-hash all re-verified independently of the executor — 323 files, 12,565,016 B, 0 `.sql`, 40/40 hashes match.
>
> **Two things were found already durable before this copy ran** (not duplicated): the per-cell
> `05_results.csv`/manifests backing OPEN-35/OPEN-12 (`docs/validations/overAll/results/open48_refleet{,3}/`,
> run 2 fully tracked in git, run 3's five finished cells present on disk), and
> the OPEN-56 aggregate cost-vector CSV (`openubem/outputs/comparisons/open56_fleet_cost_stratified.csv`).
>
> ✅ **Discharged, narrowly: the closure condition is met for the specific artifacts named above** —
> none of them depends on a volatile `%LOCALAPPDATA%`/gitignored path any longer.
>
> 🔴 **OPEN-53 STAYS OPEN.** This is not a blanket discharge. Still only on a volatile path: the other
> ~8,150 of ~8,160 buildings' individual run-2/run-3 IDFs and simulation output (their fleet-level
> aggregates are durable; their raw per-building output is not, and none of it is cited by name by an
> open item); the remaining 8 of 9 buildings from this same plan's T05 `layout_assign` rebuild
> (`scratchpad/open38-t05-rebuild/`, OPEN-38's evidence, gitignored); the ~110 MB balance of
> `scratchpad/e-la-20-investigation/`; and the ~5 GB non-`.err`/`.end` remainder of
> `%TEMP%/open56_fleet_cost/` (re-derivable from the preserved IDFs, same argument this item already
> made for the E02 `.sql` corpus). The standing risk — an external process can empty these paths without
> the project's knowledge, exactly as it did on 2026-08-17 — is unchanged by this task.
>
> **Recommended, not taken:** either narrow this item to the E02 corpus alone (now durably closed by
> regeneration + copy) and open a new item for the run-2/run-3 fleet corpus's standing custody risk, or
> keep carrying both under this item. A director records decision, not a measurement.

---

### OPEN-54 — `_ssh` never checks the remote exit code, so remote failures surface late, in the wrong place, with the evidence already discarded 🔴 **OPENED 2026-08-18**

*Found the hard way during the OPEN-48 third fleet run, not by a task that went looking for it. Full
investigation: `extra/INVESTIGATION_open-54_ssh-unchecked-exit.md`.*

**What was found.** `_ssh` (`scripts/validation/v12_cell_pipeline.py:111-116`) runs a remote command and
returns `result.stdout + result.stderr`. **It never inspects `result.returncode`.** A remote command
that failed is indistinguishable from one that succeeded quietly, unless the caller parses the text it
gets back.

**How it presented.** `nyc_centre` cleared every local stage of run 3 — cached GDF, 738/738 IDFs in
2507 s, both LIVE_SMOKE gates PASS — then died `rc=1` on `scp: dest open ... No such file or directory`
at `:267`. The `scp` was the victim. The fault was `:265`, the preceding `_ssh(f"mkdir -p ...")` whose
return value is not even bound. The `mkdir` failed, nothing noticed, and the next line wrote into a
directory that did not exist. **Forty-three minutes of correct work discarded, and the traceback named
the wrong operation.**

**Blast radius — three of eight call sites carry the identical bug.** `:265` (ship), `:457` (repair
fleet) and `:536` (reroute fleet) all discard the result of a `mkdir -p`. Two `sacct` calls (`:327`,
`:334`) are display-only and harmless. `:306` (`sbatch`) is guarded by content, exiting if
`Submitted batch job` is absent. `:939` (completeness probe) fails safe.

**🔴 The worst call site is not the one that failed.** `:325`, inside `poll_cluster`, runs
`squeue -j ID --noheader 2>/dev/null | wc -l` and breaks the poll loop — declaring the SLURM array
finished — when the count is `0`. If `squeue` *itself* fails, its diagnostics go to `/dev/null`, stdout
is empty, and `wc -l` faithfully reports **`0`**. A controller hiccup is therefore read as *"all tasks
done"*, and the pipeline proceeds to harvest results that were never produced. Note the asymmetry: a
transport failure is safe, because ssh's own stderr lands in the returned string and `isdigit()` fails,
yielding the `-1` sentinel and continued polling. **Only the remote-command failure that `2>/dev/null`
hides produces the bare `0`.** The suppression and the sentinel interact to turn an error into a
success. **Not observed — recorded because the analysis found it.**

**What was ruled out, by measurement, for the triggering failure.** Quota (6.3T used against a 10.0T
limit, no file cap). A systemic block (three sibling remote dirs existed and were being written; only
`_nyc_centre` was absent). SSH saturation — the leading hypothesis, and the reason run 3 dropped to
`MAX_PARALLEL=4` — **not supported: three waves of six simultaneous `ssh` + `mkdir` returned 18/18.**
Those probes are short-lived, so they refute the simple saturation story without proving concurrency
harmless during sustained transfers.

**What is not known, and cannot now be recovered.** Why that one `mkdir` failed. `_ssh` discarded the
remote stderr that would have said so — **the defect destroyed its own evidence.**

**Remedy, specified but deliberately not applied.** Give `_ssh` a `check: bool = True` that raises on a
non-zero return code carrying the remote stderr; pass `check=False` at the two display calls and the
probe; and at `:325` either stop suppressing `squeue`'s stderr or distinguish "empty output" from "zero
lines". **Not done now**, for two binding reasons: §2 rule 2 of the run-3 plan forbids editing
`v12_cell_pipeline.py`, and — the stronger reason — changing the pipeline midway through a twelve-cell
run would destroy the single-variable comparison run 3 exists to make, reproducing the very
interpretability defect that made run 2 useless. **Finish run 3 on unchanged code, then fix this.**

✅ **Confirmed 2026-08-18 20:27 — all three named call sites have now fired, in one run.** The
blast-radius table said `:265`, `:457`, `:536` shared the bug and that only one had fired; within three
hours **three different sites took down three different cells**: `nyc_centre` (`:265`), `la_urban`
(`:327`, the timeout flavour), `austin_suburban` (`:536`, reroute path). 🔴 **`:457` and `:536` are
costlier than `:265`**, because they are reached only *after* a cell has fully simulated and entered
repair — a failure there discards a completed SLURM array, not merely an upload. **Three cells of twelve
lost to this one defect in a single run; it is the largest source of lost work in run 3.** Priority
raised; remedy unchanged.

**Closure condition.** OPEN-54 closes when `_ssh` raises on remote failure by default, the three
unguarded `mkdir` sites inherit that guard, and the `:325` false-success path is unreachable.

🔴 **Widened 2026-08-18 19:28, after `la_urban` died `rc=1` at 42 minutes on
`subprocess.TimeoutExpired` from the `sacct` call at `:327`.** The original write-up classified that
call site as *"printed only — cosmetic"*. That was correct about the **return value** and wrong about
the **risk**: `_ssh` hands `timeout=` to `subprocess.run` and never catches `TimeoutExpired`, so **every
call site is fatal on a slow login node regardless of whether its output is read.** A status line that
exists only to be printed ended a cell whose SLURM array was very likely healthy. **`check=True` alone
would not have prevented this** — the exit-code axis and the timeout axis are separate, and the remedy
needs both: a `tolerant=True` mode that catches `TimeoutExpired` and returns a sentinel at the two
`sacct` display calls and the completeness probe. **A call whose output is only printed must never be
able to end a run.** Closure now additionally requires that.

🔴 **Widened again 2026-08-18 20:38, after `austin_centre` died `rc=1` on the same timeout axis at
`:334`.** Four distinct sites have now fired in one run (`:265`, `:327`, `:334`, `:536`), but the site
count is no longer the point. `austin_centre` had **already tripped the zero-fail gate with 20 failed
buildings against a tolerance of 5** and was inside the repair stage when `sacct` timed out; it exited
`rc=1` and was filed as transport. `austin_suburban` (14 failures, tolerance 5) reads the same way.
**Two of twelve cells were carrying an unread model verdict under a transport return code**, and the
run appeared to have three stopping cells when it had five. *(Counts corrected 20:50; first written as six and eight.)* The evidence survived only by an accident of
print ordering — the gate writes its count before the repair stage runs. **A crash truncates evidence
and never fabricates it, so an unchecked exit status produces systematically *optimistic*
misclassification, not random misclassification.** This defect does not cost a rerun; it biases the
conclusions of whatever investigation it interrupts. **Closure must therefore cover every call site,
not the four observed to fire.** Full argument: `extra/INVESTIGATION_open-54_ssh-unchecked-exit.md` §3.4.


> ✅ **REMEDY IMPLEMENTED + CLOSED + ID RETIRED 2026-08-18 (late)** (T02 of
> `implemenation/previous/PLAN_ten-items-2026-08-18-late.md`, director-executed).
>
> **The editing ban was run-scoped and the run is over.** The reason this was not fixed on 18 August
> was stated at the time — *"a mid-run change would break the single-variable comparison"*. The third
> fleet run completed at 20:47 and its comparison is written up, so the constraint has lapsed.
>
> **What was changed, in `scripts/validation/v12_cell_pipeline.py`, the only file touched:**
> 1. **`_ssh` raises.** A new `RemoteCommandError` is raised on a non-zero remote exit **and** on
>    `subprocess.TimeoutExpired` — the two failure modes that fired on `nyc_centre` and `la_urban`
>    respectively — carrying the command, the exit code and both streams. `allow_fail=True` is the
>    explicit opt-out for call sites where a non-zero exit is a legitimate answer; on timeout it
>    returns `""` so the caller re-polls instead of concluding.
> 2. **The `:325` false-success path is closed.** `squeue -j <id> | wc -l` returns `0` both when the
>    array is finished and when `squeue` itself failed with its stderr eaten by `2>/dev/null`. The
>    loop now captures `${PIPESTATUS[0]}` and **concludes completion only when `sacct` positively
>    corroborates it**: no states → re-poll; any of `PENDING/RUNNING/REQUEUED/RESIZING/SUSPENDED/`
>    `CONFIGURING/COMPLETING` → re-poll.
> 3. **The three unguarded `mkdir` sites (`:265`, `:457`, `:536`) and the sbatch submit inherit the
>    guard** by calling `_ssh` without `allow_fail`.
>
> **Tested locally, with no cluster call.** `subprocess.run` was replaced by a stand-in that also
> **asserts the argv still carries the `bash -lc` wrapper** — the tcsh guard is load-bearing and a
> future refactor must not drop it silently. Nine checks, all passing: success passthrough · non-zero
> raises with the exit code and stderr in the message · `allow_fail` passthrough · timeout raises ·
> timeout + `allow_fail` returns `""` · sacct state parsing · empty sacct does **not** read as
> complete · active tasks detected · `CANCELLED+` normalised.
>
> **Closure condition, checked line by line:** *"`_ssh` raises on remote failure by default"* ✅ ·
> *"the three unguarded `mkdir` sites inherit that guard"* ✅ · *"the `:325` false-success path is
> unreachable"* ✅. **Met. ID retired.**
>
> ⚠️ **Not claimed:** that the guard has been exercised against the live cluster. It has not — no
> cluster call was made, by design. The first real run through it should be watched.
>
> **Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §8;
> `extra/INVESTIGATION_open-54_ssh-unchecked-exit.md`.

---

### OPEN-55 — the OPEN-49 fix widened the Unknown PDE bounds to the full archetype table, so Unknown buildings draw data-centre equipment loads 🔴 **OPENED 2026-08-18**

✅ **CLOSED + ID RETIRED 2026-08-19** **on the user's ruling of 2026-08-19.** 🟢 **This item closes the way an item should: its own falsifiable prediction was written down before the test, the test ran, and the prediction held.** The condition was that a cell with a high Unknown fraction simulate with zero divergences. `nyc_suburban`, 290 Unknown of 1,589, frozen input MD5 `1198ed01bfd3b4463e50da0ae39d8e27`, job 1274983: **71 → 0 divergences**, 1,589/1,589 simulated, 0 failures among the 1,299 classified buildings, archetype histogram unchanged. Median Unknown equipment draw fell **2,692.27 → 9.15 W/m²**, ~294×, into the classified range (`MediumOffice` reference 10.76). ⚠️ **It took four attempts, and the first three are the lesson, not a footnote:** each simulated **zero buildings** and each was lost to a blind retry of a fault that had not been diagnosed — the `_ssh` defect eventually registered and fixed as OPEN-57. An item can sit *implemented, ruled, and completely unproven* for a week; only the fourth attempt produced evidence.

🔴 **What this closure explicitly does NOT claim, found by the director's audit of the passing run itself.** The screen cured the equipment column — Unknown buildings now draw **less** equipment energy than classified ones (median 37.5 vs 43.4 kWh/m²), arguably a slight over-correction. **But Unknown buildings still finish at 1.7× classified overall** (median total **349.4 vs 202.8 kWh/m²**), and the excess has simply relocated: DHW **+61.0**, heating **+41.1**, lighting **+22.7**, cooling **+20.5** kWh/m². Lighting and cooling are the largest *multiples* (6.7× and 5.6×). This item's stated condition was about **divergences**, and divergences are gone; the **level** of Unknown demand was never this item's test and is not settled by it. **Opened as OPEN-59** rather than left implied inside a closed item, because a defect recorded only inside a closed item is a defect the next session will not find.


**Status.** Open. Mechanism proven, blast radius measured, remedy specified and **not applied**.
Full write-up: `extra/INVESTIGATION_open-55_pde-bounds-datacenter.md`.

**What it is.** Route 2 of the OPEN-49 fix made `_get_cross_archetype_loads()` unconditional at
`openubem/semantic/__init__.py:366`, so `_build_unknown_loads` takes its uniform-PDE bounds from **all
29 archetypes** rather than from the archetypes present in the cell. The table's equipment column is
topped by `LargeDataCenterHighITE` at **5381.96 W/m²**. In `nyc_suburban` the equipment bound went from
`[…, 96.88]` (cell-local, `QuickServiceRestaurant`) to `[2.58, 5381.96]` — **a 55× widening**, moving
the median draw from roughly 50 W/m² to roughly 2690 W/m² against an ordinary 5–20 W/m².

**How it surfaced.** `nyc_suburban` stopped `rc=2` in the OPEN-48 third fleet run: **71 of 290 Unknown
buildings diverged** with `CalcHeatBalanceInsideSurf` temperatures to 1.3×10⁷ °C, against a tolerance of
16. The same cell on **byte-identical frozen input** returned `{'success': 1589}` in run 2. Code was the
only variable.

**Proof, not inference.** The draw is deterministic (`_per_building_rng` = `blake2b(osm_id)` mixed with
`config.RANDOM_SEED`), so all 290 draws were regenerated locally and joined to the manifest: **no
building drawing below 2496 W/m² failed**; the 71 failures span 2496–5349 W/m²; and **every failure is
an `OpenUBEMUnknown`** — none of the 1299 classified buildings failed.

**Blast radius.** Screening all twelve cells' draws locally, **between four and six cells of twelve** are
expected to stop on the tolerance gate. 🔴 **But the failure count understates the damage:** the gate
catches only buildings whose heat balance *diverges*, and is blind to Unknown buildings that absorb an
absurd load and report a finite, enormous EUI. `la_urban` passes the gate with two Unknown buildings,
*both* drawing above 2496 W/m². **Every Unknown building in every cell is drawing from the same
distorted distribution — 18.3 % of `nyc_suburban` and 12.8 % of `nyc_urban`, the fleet's two largest
cells. Any fleet EUI from run 3 is inflated, including from cells that pass.**

**What it does not touch.** The adopted `phaseE_elevrb` run and run 2 both predate the fix and used
cell-local bounds — **the published `157.1` is not affected by this defect.** Route 1 of the OPEN-49 fix
(`_per_building_rng`) is not implicated; it is what made this diagnosis possible. And the OPEN-49
*diagnosis* stands — cell-dependent bounds were a real defect, correctly removed. The error is in what
replaced them.

**Remedy, specified but deliberately not applied.** The bound must be **physically screened**, not
merely made cell-independent: exclude implausible donors (the four data-centre archetypes, arguably
`Laboratory`) from the Unknown PDE table; or draw on a p5–p95 range rather than min/max; or clip the
drawn value. The first is narrowest and most auditable. 🔴 **This is a DESIGN question, not a bug fix —
it changes what an Unknown building is, and is not the director's to settle unilaterally.** Nothing is
applied mid-run, for the same reason as OPEN-54: it would break run 3's single-variable comparison.

**Coupling.** **OPEN-49 cannot close while this stands.** Its mechanism fix is sound; its route-2
implementation introduced this. The two resolve together.

🟢 **Strengthened 2026-08-18 19:42 — `nyc_urban` stopped `rc=2` with 83 of 228 Unknown failing
(tolerance 18), as projected.** Pooling both observed cells (518 Unknown, 154 failures) and binning by
drawn equipment density gives a **monotonic dose-response curve running 0.000 → 1.000 across eleven
bins**, flat at exactly zero below 1500 W/m² and exactly 1.000 above 5000. **Not one of the 3,078
classified buildings in the two cells failed.** The causal claim is now about as well supported as it
can be without a controlled re-run. ~~Revised projection: **five of twelve cells stop.**~~ **Measured 2026-08-18 20:50, all twelve landed: FIVE of twelve
cells stop** — `nyc_suburban` (71), `nyc_urban` (83), `la_centre` (10), `austin_centre` (20),
`austin_suburban` (14), the last two mislabelled `rc=1` by OPEN-54 (see that item). **Five cells passed** — `nyc_rural` 3/5, `la_rural` 5/5, `la_suburban` 0/13, `austin_rural` 4/5,
`austin_urban` 5/5 — **four of them by dropping the affected buildings, at or within two of tolerance**;
two cells are transport-only with no verdict. ⚠️ **An earlier version of this line said eight stopping
cells; that was an arithmetic error of mine, corrected here and in OPEN-55 §4A.6. The conclusion it
supported — that T04 is unreachable and the passes are not poolable — is unchanged.** Predictions for
the remaining cells were recorded *before* they ran (`extra/INVESTIGATION_open-55_...` §4A.1) — notably
that **`nyc_centre` will fail `rc=2` on its T03 retry** despite having so far failed only on transport.
🔴 **The `nyc_centre` prediction was never resolved.** The T03 retry ran 28.5 minutes and **died silently inside local IDF generation at 21:18** — no traceback, no `ZERO-FAIL` line, no results directory. Neither branch of the pre-registration occurred, so **this cell adds nothing to the scoreboard in either direction and must not be counted as a sixth confirmation.** No third attempt is queued: T04 is void under CP-2, so the cell cannot enter any aggregate. The model stands on the evidence it already had.

**Scoreboard after `austin_centre`: 8 correct, 1 missed; the failure-count bracket 3 hits, 0 misses**,
tested on cells spanning 226 to 1,779 buildings. `austin_centre` was pre-registered STOP with bracket
14.4–24.7 and landed on 20.

**Closure condition.** OPEN-55 closes when the Unknown PDE bound is physically screened by an approved
DESIGN decision, and a cell with a high Unknown fraction (`nyc_suburban`, 290) simulates with zero
divergences.

🟡 **Remedy proposal written 2026-08-18 20:5x, on the user's instruction — `extra/PROPOSAL_open-55_unknown-pde-bounds.md`. AWAITING THE USER'S RULING; nothing patched.**
Four options costed; **Option B recommended** — screen the Unknown donor pool by building kind (exclude
the four data centres on every column, `Warehouse` on occupancy only), keeping the fixed cell-independent
table OPEN-49 bought. Three findings the proposal adds to this item:
**(a) With a uniform draw the maximum sets the *centre*, not the tail** — the median Unknown equipment
draw today is **2692.27 W/m²**, against 49.73 under the screen and 10.76 for `MediumOffice`. Half of all
Unknown buildings carry ~250× an ordinary commercial load; this is the middle of the distribution, not an
edge case.
**(b) A second, silent defect on the occupancy axis** — `occupant_m2_per_person` bounds `[4.65, 464.52]`
(`Warehouse`) give a median of **234.6 m²/person**, i.e. effectively unoccupied. It never crashes, so no
gate has ever caught it, and it is present in every fleet figure produced from post-fix code.
**(c) 🔴 OPEN-49 did not introduce this defect — it made it universal.** The full-table fallback already
existed at `fe05509` (`loads_real if real_mask.any() else _get_cross_archetype_loads()`) and fired on
all-Unknown cells. So reverting is not a fix, and "it worked before" only means the path was rarely taken.
Percentile clipping (option D) was **measured to fail**: the 95th percentile of the equipment column is
**1076.39** — still a data centre, because 4 of 29 rows are. Acceptance test is unchanged and cheap:
`nyc_suburban` must return **zero** divergences on its frozen input, one cell, ~45 min, no fleet run.

---

🟢 **OPEN-48 — the stated blocker is discharged 2026-08-18 (late).** The third fleet run exists, and
its measured answer is in `extra/MEASUREMENT_open-48_third-fleet-run.md`: **the OPEN-49 fix moves
classified buildings by under 0.08 %** (`la_rural` −0.0906, `austin_urban` −0.0614 on Unknown-free
cells; +0.0004 / +0.0001 / −0.0001 on the three cells with Unknowns removed). Every classified building
changed value and no cell mean moved — route-1 reseeding redistributes draws without changing the
population. **CP-2 ruled: run 3 produces no fleet figure and none is to be quoted from it.** **CP-3
ruled: `157.0552` stays**, with a caveat now quantified — run 2's Unknown path contributes
**+4.058 kWh/m² (+2.615 %)**, nearly twice the +2.1605 discrepancy the arc was chasing. The adopted
run's per-building results are gone, so that figure is a measurement on run 2 and an estimate for the
adopted run; it is reported, not subtracted.

> 🟢 **RULED AND PATCHED 2026-08-19 — user ruling R1 (Option B+), implemented as T01 of
> `implemenation/previous/PLAN_ten-items-2026-08-19.md`, CP-1 signed by the director.** This SUPERSEDES the
> line in `extra/PROPOSAL_open-55_unknown-pde-bounds.md` §10 that "nothing will be patched before
> that ruling." Option A was rejected on reasoning, Option D on measurement (5th–95th percentiles are
> `[4.46, 1076.39]` — the 95th is still a data centre), and plain Option B was observed insufficient
> in §7A. **B+ is the ruled answer.**
>
> **The screen.** `_UNKNOWN_DONOR_EXCLUDE` = the four data centres + `Laboratory` +
> `FullServiceRestaurant` + `QuickServiceRestaurant`, applied to every PDE column;
> `_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY` adds `Warehouse` for `occupant_m2_per_person` only.
>
> **Director-verified by independent re-derivation at HEAD** (not taken from the executor's report):
>
> | column | before | after |
> |---|---|---|
> | `equipment_w_m2` | `[2.58, **5381.96**]` | **`[2.58, 16.15]`** |
> | `occupant_m2_per_person` | `[4.65, **464.52**]` | **`[4.65, 51.10]`** |
> | `lighting_w_m2` | `[3.44, 19.38]` | `[3.44, 18.30]` |
> | `wwr` | `[0.10, 0.40]` | `[0.10, 0.40]` — unchanged |
>
> Donor pool **29 → 22** rows (**21** for occupancy). **All eight excluded names were confirmed
> present in the archetype table**, so no exclusion is a silent typo doing nothing. Uniform median
> **9.37 W/m²** (exact midpoint 9.365, ROUND_HALF_UP; note plain `float` gives 9.364999999999998 and
> naive `round()` would display 9.36 — a display artifact, not a defect).
>
> ✅ **CP-1 conditions, each checked.** The screen lives **inside `_build_unknown_loads`**, not at the
> call site; the call site still passes the full unscreened 29-row table **unconditionally**, so
> OPEN-49's ruling 3 is intact. The `dc_archs` set in the probabilistic-perturbation branch was left
> alone and **not** merged with the new exclusion set. An **empty-pool guard raises `ValueError`**
> rather than silently falling back to the unscreened table. Diff is **+30 / −2** on one file, plus a
> new `tests/test_semantic_unknown_bounds.py`. Full suite **1885 passed / 55 skipped / exit 0**
> against the 1875 / 55 / 0 baseline — delta exactly the 10 new tests, nothing else changed state.
>
> **Non-vacuity proved:** a probe test empties both exclusion sets and asserts the ceiling reverts to
> **5381.96**; it passes, so the screen is load-bearing rather than decorative. OPEN-49's per-building
> seed and cell-independence are each proved by a named test, including one that draws the same
> `osm_id` beside `LargeDataCenterHighITE` and `Laboratory` and gets identical values.
>
> ⚠️ **One recorded scope extension, measured inert.** The patch also takes the setpoint medians
> (`scalar_cols`) from the screened pool, which is slightly wider than R1's letter ("every PDE
> column"). Director-measured: **all four setpoint medians are unchanged** by the screen
> (21.1 / 23.9 / 15.6 / 29.4). Harmless today, but it would bite if the archetype table changed —
> recorded so a future reader is not surprised.
>
> 🔵 **This item is NOT closed.** The remedy is implemented and unit-tested; it has not yet been shown
> to stop the crashes. The falsifiable acceptance test the proposal itself names — `nyc_suburban`,
> 1,589 buildings, 290 Unknown, **71 divergences today, predicted to return zero** with no other
> change on its frozen `01_buildings.gpkg` — is T02, and **T02 did not run**: see the block below.

> ⛔ **Amended 2026-08-19 (T02 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — THE
> ACCEPTANCE TEST DID NOT RUN. The 71 → 0 prediction is NEITHER confirmed NOR falsified.**
>
> 🔴 **Zero buildings simulated under T01's code.** Nobody may cite this pass as evidence that
> the B+ screen stops the crashes. OPEN-55's remedy remains *implemented and unit-tested, unproven in
> simulation* — exactly the state the block above described, unchanged.
>
> Two attempts, two **different** failure signatures, both **before** any EnergyPlus ran:
>
> | | attempt 1 (pid 14032) | attempt 2 (pid 47676) |
> |---|---|---|
> | reached | steps 1–3 complete, LIVE_SMOKE gates PASS | died mid step 3 |
> | died in | `_remote_results_complete` → `_ssh`, `v12_cell_pipeline.py:1082` | local IDF generation |
> | signature | `RemoteCommandError`, remote stderr **`Unmatched '.`** — a tcsh quote fault | **silent** — no traceback, no exit line |
> | where | remote probe, before any ship/submit | entirely local, before any SSH |
>
> ✅ **The frozen-input control passed:** `01_buildings.gpkg` MD5 `1198ed01bfd3b4463e50da0ae39d8e27`,
> byte-identical to run 2's original; both logs show the `v12_cell_pipeline.py:185-189` cache-hit
> branch and **no OSM fetch**. 1,589 buildings, 290 Unknown — both match the pre-registered baseline.
> Attempt 1 generated **1,589 / 1,589 IDFs in 239.6 s** under the screened code.
>
> ✅ **Control 1 (non-vacuity) PASSES**, re-derived locally without cluster or EnergyPlus —
> deterministic under OPEN-49's per-building seed, so bit-identical to what either attempt held: all
> 290 Unknown draws of `equipment_w_m2` land inside `[2.58, 16.15]` (min 2.590 / median 9.153 / max
> 16.067, **0 / 290** over the ceiling). `occupant_m2_per_person` 4.744 / 31.070 / 51.050 and
> `lighting_w_m2` 3.454 / 10.869 / 18.246 likewise sit inside their screened bounds. **This proves the
> screen reaches the draw. It does not prove the screen stops a thermal runaway.**
>
> 🔴 **The 1,589 `out/<osm_id>` directories under
> `/speed-scratch/o_iseri/fleets/open48_refleet3_nyc_suburban/out/` are 100 % STALE** — every one
> carries mtime **2026-08-18 18:08**, i.e. they are the untouched pre-T01 run that produced the 71
> baseline. **They must not be scored as either passes or failures of the screen.** The 71 itself is
> re-confirmed on disk (`ZERO-FAIL: 71 failures exceed tolerance 16. STOP.`, all 71
> `CalcHeatBalanceInsideSurf` / `Temperature (high) out of bounds`).
>
> 🔵 **The tcsh fault is OPEN-54's fix behaving exactly as designed, on its first live-cluster
> exercise** — its closure note (2026-08-18) said *"never exercised against the live cluster — watch
> the first real run"*, and this is that run. `_ssh` **raised** instead of silently reporting success;
> the old code would have swallowed it. No new ID is opened: the identical probe on the identical
> 23,171-character osm_id list succeeded cleanly on 2026-08-18, so this reads **transient**, not a
> static length bug (the list is well under Windows' 32,767-char `CreateProcess` limit). ⚠️ **If
> `_remote_results_complete`'s single giant `_ssh` line faults a second time, open an ID for it** —
> the recurrence, not this occurrence, is the trigger.
>
> ⚠️ **Attempt 2's silent local death is unexplained.** One `energyplus.exe` (~1.27 GB RSS) from a
> concurrent task was running on the shared 20-core machine, which is *plausible* contention but was
> **not confirmed** — no crash dump or Event Log was inspected. The launcher pattern discards the
> child's exit code, so a third silent death would be indistinguishable from a hang; any retry should
> fix that first and run in a quiet window.
>
> **Two distinct unexplained failures is a stop point, not a third blind retry** — the executor
> stopped and reported rather than substituting a different measurement, and disclosed its own
> process error (the retry launcher reopened the shared log in `w` mode and truncated attempt 1's
> on-disk log; the quoted crash text was transcribed from live tool output before the truncation).
>
> 🔴 **CP-2 cannot be signed.** T02's half is incomplete; T03's half returned a narrow negative.
> **The acceptance test is owed and remains owed.**


> ---
>
> ### Amendment — 2026-08-19, director, after T02 attempt 3
>
> 🟢 **R1 WAS RULED AND IS NO LONGER OUTSTANDING.** The user answered at selection time:
> **Option B+.** The §1 row's older text (*"Remedy proposed and AWAITING THE USER'S RULING …
> nothing patched"*) is superseded by this amendment and by T01. Option A was rejected on reasoning,
> Option D on measurement, and plain Option B was observed insufficient. **Cite the 2026-08-19 pass,
> not `PROPOSAL_open-55_unknown-pde-bounds.md` §10's "nothing will be patched before that ruling."**
>
> ✅ **The remedy is IMPLEMENTED (T01, 2026-08-19).** `_UNKNOWN_DONOR_EXCLUDE` in
> `openubem/semantic/__init__.py` removes the four data centres, `Laboratory`, `FullServiceRestaurant`
> and `QuickServiceRestaurant` from the Unknown donor pool on every PDE column, with `Warehouse`
> additionally excluded on occupancy. Donor pool **29 → 22** rows (21 for occupancy). Equipment
> bounds **`[2.58, 5381.96]` → `[2.58, 16.15]`**; occupancy `[4.65, 464.52]` → `[4.65, 51.10]`;
> lighting 19.38 → 18.30; `wwr` unchanged; median 9.37 W/m². An empty-pool guard raises
> `ValueError`. Ten new tests in `tests/test_semantic_unknown_bounds.py`; full suite **1885 passed,
> 55 skipped, exit 0**. **CP-1 signed.**
>
> 🔴 **BUT THE ITEM IS NOT CLOSED, AND THE REASON MATTERS: THE PROPOSAL'S OWN FALSIFIABLE
> TEST HAS NEVER RUN.** T02 was that test — `nyc_suburban`, frozen input, prediction **71
> divergences → 0**. **Three attempts, zero buildings simulated.** Attempt 1 and attempt 3 both
> died on the same remote probe with `Unmatched '.`; attempt 2 died silently for a still-unexplained
> reason. **The prediction is neither confirmed nor falsified**, and no EUI movement has been
> observed. The blocking transport fault is now tracked as **OPEN-57**.
>
> ✅ **Control 1 (non-vacuity) PASSED, re-derived from attempt 3's own artifacts** — not carried
> forward from attempt 1. Over the 290 Unknown rows of `nyc_suburban`: `equipment_w_m2` min
> **2.590187**, median **9.152907**, max **16.066840**; **0/290 exceed the `[2.58, 16.15]` ceiling**.
> `occupant_m2_per_person` 4.743670 / 31.069510 / 51.049642 and `lighting_w_m2` 3.454098 / 10.869178 /
> 18.246370, both inside their new bounds. The classification distribution matched the pre-registered
> baseline exactly (`MidriseApartment 979 / SmallOffice 316 / OpenUBEMUnknown 290 / Courthouse 2 /
> QuickServiceRestaurant 1 / MediumOffice 1`). These figures are bit-identical to attempt 1's, which
> is the *expected* consequence of OPEN-49's per-building determinism — evidence the screen's effect
> on the draws is stable, not evidence a number was copied.
>
> ⚠️ **Control 2, the primary divergence count and EUI movement are NOT EVALUABLE** — zero
> buildings simulated, so there is nothing to compare. The pre-fix divergence count remains **71**
> from the original run-3 log (confirmed twice, not re-verified again). **No fleet figure is
> restated; `157.1 kWh/m²` is untouched by this item.**
>
> ✅ **What attempt 3 did prove, by construction rather than by inspection:** the local half of the
> pipeline is sound under the new code — 1,589 buildings loaded from cache with no OSM fetch,
> **1,589/1,589 IDFs generated in 199.6 s**, LIVE_SMOKE both gates PASS (generation 100.0% ≥ 95%,
> Unknown 18.3% < 20%). Frozen input MD5 `1198ed01bfd3b4463e50da0ae39d8e27`, copied not moved and
> re-verified. A **fresh** remote fleet dir was verified absent before *and* after the crash, so the
> 1,589 stale directories from 2026-08-18 18:08 could not be scored as a false zero.
>
> 🔴 **What OPEN-55 owes, unchanged and now explicitly blocked:** the acceptance test, on real
> simulation output. **It cannot be attempted again until OPEN-57 is resolved** — a fourth blind
> retry is not authorised and would spend the same 3–4 minutes of local work to die at the same
> remote call. Full record: `extra/MEASUREMENT_open-55_acceptance-test-attempt3.md`.
---

### OPEN-56 — Every building in the fleet simulates with a 10 m³ zone volume stub 🔴 **OPENED 2026-08-18 (late)**

> 🟢 **Back-reference (T09 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`, 2026-08-19, ruling R2):
> OPEN-42 and OPEN-11 are now CLOSED and folded into this item** — both items' own §-sections carry
> their full closure records, including what this item does and does not explain for each. OPEN-56
> itself remains open and its remedy remains unauthorised; this fold adds no new claim here.

> **Amended 2026-08-18 (overnight, X01/X02/X03 of `implemenation/previous/PLAN_ten-items-2026-08-18-overnight.md`). ✅ THE FLEET-SCALE COST MEASUREMENT THIS ITEM
> WAS WAITING FOR HAS BEEN MADE — 69 buildings across ALL TWELVE CELLS, not ten in two rural ones.**
>
> **Control, whole:** one-field diff assertion **70 / 70**; `Indicated Zone Volume <= 0.0` present in
> **70 / 70** baseline runs and **0 / 70** treated; **70 / 70 completed in both arms.**
>
> | | fleet-stratified (this pass) | rural-only (previous pass) |
> |---|---:|---:|
> | mean | **+0.98 %** | +0.75 % |
> | median | **+0.84 %** | +0.67 % |
> | range | −0.23 % to **+3.25 %** | −0.07 % to +1.67 % |
> | same direction | **65 / 69 (94.2 %)** | 9 / 10 |
> | absolute Δ | mean **+1.00 kWh/m²** | +0.51…+1.30 |
>
> **The sign is unchanged and firmer: the stub understates energy.** Per cell the pattern is
> **geographic, not morphological** — `la_centre` **1.83**, `la_rural` 1.49, `la_urban` 1.26 at the top;
> `nyc_urban` **0.38**, `nyc_rural` 0.48, `nyc_suburban` 0.53 at the bottom; Austin ≈ 1.0 throughout.
> LA highest, NYC lowest. Noted beside **OPEN-19** (LA runs ~+40 % hot), not pursued.
>
> 🔴 **The pre-registered prediction was half right, and the half that failed matters.** Predicted:
> *"positive and one-directional; magnitude rises with zone count, so urban cells exceed +0.75 %."*
> Direction **held** (94.2 %). **"Rises with zone count" is refuted** — `corr(pct_change, n_zones)
> = +0.113`. **"Urban cells exceed +0.75 %" is refuted** — the three lowest cells are all NYC.
>
> **What the cost scales with is almost nothing.** The absolute Δ is the *more* stable normalisation,
> not the less: **cv 0.79 raw against 1.09 per zone**. Floor area +0.09, storeys +0.30, written volume
> +0.09, log-area +0.27. The only moderate term (baseline EUI, −0.478) is arithmetic — a near-constant
> absolute Δ over a smaller denominator. 🔵 **So the honest model is a fixed per-BUILDING offset of
> ≈ +1.0 kWh/m², which directly refutes the "fixed per-zone effect" the previous pass inferred from
> ten points.** That earlier reading was reasonable on its evidence and is wrong on more of it.
>
> ⚠️ **Deliberately not extrapolated.** 5 buildings per cell is stratified, **not population-weighted**,
> and the governing plan forbids converting it into a correction. **`157.1 kWh/m²` is not restated.**
> Settling it needs a population-weighted sample or a full re-run — both named, neither authorised.
>
> 🔴 **A NEW side-finding, and it points at the denominator rather than the numerator.**
> `nyc_centre / relation_3566904` (14 zones) was excluded from the cost statistic because writing
> `Zone.Volume` **also changed its reported Total Building Area: 157,115 m² → 37,551 m² (÷ 4.18)**.
> Its apparent −47.8 % is not a cost — the denominators are not comparable. **59 of 60 buildings had
> identical areas to within 0.1 %**, so this is isolated. It matters anyway: **the project's EUI
> denominator is EnergyPlus's own simulated floor area**, and this is a case where the same broken
> geometry that stubs the volume also mis-reports the area. **Registered as a lead; NOT generalised
> from n = 1**, and it does not by itself implicate any published figure.
>
> 🔵 **X03 — this item does NOT subsume OPEN-09.** The ten non-convergent-but-successful buildings
> show **150 warnings baseline, 150 treated, 15 / 15 unchanged on every one**. Writing the volume
> clears the volume warning completely and **does not touch the non-convergence at all.** The two are
> independent defects overlapping on the same 16 buildings. Both remain true: this treatment repairs
> all six failures, *and* it leaves the non-convergence warnings standing in the ten that survive.
>
> 🔴 **The remedy is still NOT authorised.** What has changed is that its cost is now measured on all
> twelve cells with a whole control, and its direction is settled. **A ruling is owed on whether to
> write `Zone.Volume` or fix the winding** — and X02 says the choice cannot be justified by zone count.
>
> **Evidence:** `openubem/outputs/comparisons/open56_fleet_cost_stratified.csv`; scripts
> `scripts/analysis/open56_fleet_cost_stratified.py`, `open56_fleet_cost_repair.py`; report `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md`
> §X01–X03.
>
> ⚠️ **A harness fault this measurement caught, recorded because it would have corrupted the control.**
> The first pass ran 140 EnergyPlus jobs through a 6-worker pool and **ten buildings produced an
> entirely empty output directory** in the baseline arm — no `.err`, no severe, nothing. Read at face
> value that would have reported the control as **60 / 70** and dropped ten buildings, four of them the
> whole `nyc_centre` sample. Re-run **serially**, the identical `baseline.idf` completes in **18
> seconds with 0 severe errors**. The ten were re-run one at a time and merged. **An empty output
> directory is not a failed simulation.**


*Found by T04 of `implemenation/previous/PLAN_ten-items-2026-08-18-late.md` while looking for OPEN-42's
mechanism — the tenth item in this register opened by auditing an artifact for a different question.*

**Status.** Open. Mechanism measured on 8,160 of 8,160 buildings with a non-vacuous control. Writer
not localised. Effect on annual EUI **unmeasured and not assumed**.


> 🔵 **Amended 2026-08-18 (night) (W01–W05 of `implemenation/previous/PLAN_ten-tasks-2026-08-18-night.md`).
> PROVED BY INTERVENTION, cost measured, writer localised.**
>
> The item was opened with its blast radius deliberately unmeasured. It no longer is.
>
> **Design.** `Zone.Volume = floor_area × height` written into a **copy** of each IDF; both arms
> re-run from the same file in the same session — **the existing `sim_out` results were deliberately
> not used as the baseline**, since they were produced days earlier in a different process. Sample
> fixed before any result was seen: the six OPEN-42 failures + ten successes. The diff was asserted
> object-by-object first: **`OK n zones, field 9 only`** on all sixteen.
>
> ✅ **Control passed exactly.** `Indicated Zone Volume <= 0.0` present in **16 / 16** baseline runs,
> **0 / 16** treated runs. The treatment does what it claims and nothing else.
>
> 🔴 **Mechanism — six of six.** Every one of OPEN-42's failing buildings **completes successfully with
> zero severe errors** after the one field is written, from 9–39 severes before:
> `way_472960972` 11→0 · `way_472961034` 25→0 · `way_472961088` 25→0 · `way_472961091` 9→0 ·
> `way_472961171` 21→0 · `way_402215469` 39→0. **This is an intervention with a control, not an
> association read off a census.**
>
> 🔵 **Cost on buildings that do run: mean +0.75 %, median +0.67 %, sd 0.59, range −0.07 % to
> +1.67 %** over ten successes in two cells. **Small — and not random.** **Nine of ten move the same
> way**, the tenth by −0.07 % (inside noise), so **the stub systematically *understates* energy**: a
> zone with almost no air capacitance rides its setpoints more easily than a real one. The absolute Δ
> is strikingly uniform (+0.51 to +1.30 kWh/m² across buildings spanning 41 to 524 kWh/m²), consistent
> with a fixed per-zone effect rather than a proportional one. **A consistent direction is a bias, not
> scatter.**
>
> ⚠️ **What is NOT claimed. n = 10, two cells, both rural — a bound and a sign, not a fleet estimate.**
> Extrapolating +0.75 % to `157.1` would give ≈ +1.2 kWh/m², and **that arithmetic is deliberately not
> performed as a correction.** What is licensed: **the risk this item was opened with is bounded at
> order 1 %, is one-directional, and is smaller than the Unknown-path bias (+4.06) already reported
> beside the published figure. `157.1` does not need withdrawing or restating.**
>
> ✅ **The 100 % figure independently re-derived by a second method.** W06's family census partitions
> the `Indicated Zone Volume` warnings by zone-name pattern and they sum to **exactly 8,160**
> (7,673 `_WHOLE` + 385 `_PERIM` + 98 + 2 + 2). The first census counted a log literal.
>
> **W05 — the writer is localised.** **Not our code.** No `openubem/` module sets floor or ceiling
> vertex order; the order comes from **`geomeppy/geom/polygons.py:573-611`**
> (`normalize_coords` → `set_entry_direction`), orienting each polygon against an outside point derived
> from `GlobalGeometryRules` (`UpperLeftCorner / Counterclockwise / Relative` in our IDFs).
> 🔴 **OpenUBEM already has a detector for this exact signal and deliberately does not apply it:**
> `openubem/idf/surfaces.py:223` `_coreperim_has_inverted_winding`, excluded by its caller at
> `:671-681` with the written reason *"EnergyPlus convention always uses negative signed-area (CW
> winding) for floor surfaces; checking sign would produce false positives on healthy buildings."*
> **That sentence is why nobody looked.** ⚠️ It is not declared wrong here — 2-D signed area is
> projection-dependent and the observable defect is the negative *volume*, not the sign — but the two
> statements now sit against each other and one must give. **Resolving it is a code change and is not
> made here.**
>
> **Closure condition, restated against what is now known.** The remedy is small and specified: write
> `Zone.Volume` explicitly, or fix the winding upstream. Either way the item closes when a fleet run
> carries **no** `Indicated Zone Volume <= 0.0` warning **and** the EUI difference is reported on a
> fleet-scale sample rather than ten buildings.
>
> **Evidence:** `extra/MEASUREMENT_ten-tasks-2026-08-18-night.md` §1–§3;
> `openubem/outputs/comparisons/open56_zone_volume_experiment.csv`,
> `open09_fleet_err_taxonomy.csv`; script `scripts/analysis/open56_zone_volume_experiment.py`.

---

#### What was found

EnergyPlus derives each zone's air volume from its surfaces, because the `Zone` objects we write
declare `Volume` as `autocalculate`. On our geometry it derives a **negative** number and substitutes
a placeholder:

```
** Warning ** Indicated Zone Volume <= 0.0 for Zone=WAY/402215469_F0_WHOLE
**   ~~~   ** The calculated Zone Volume was=-1376.24
**   ~~~   ** The simulation will continue with the Zone Volume set to 10.0 m3.
```

The volume comes out negative because the floor and ceiling surfaces are wound the wrong way round —
`GetVertices: Floor is upside down!` and `GetVertices: Roof/Ceiling is upside down!` appear in every
run directory checked. EnergyPlus auto-corrects each *surface's* tilt (`Automatic fix is attempted.`)
but the *volume* integral still comes out negative, and the 10 m³ stub stands for the rest of the run.

#### How big it is

| population | negative computed volume / 10 m³ stub |
|---|---|
| `la_rural` + `la_urban`, run 2 | **767 / 767** |
| **all twelve cells, run 2 (`open48_refleet`)** | **8,160 / 8,160 — 100.00 %** |
| run 3 (`open48_refleet3`), three cells re-checked | 198/198 · 149/149 · 245/245 |
| **control — runs built from DOE-prototype geometry** | **0 / 2** |

🔴 **The control is what makes this a defect of ours rather than a property of EnergyPlus.** The
surviving prototype-geometry runs under
`scratchpad/e-la-20-investigation/i03/A_as_classified_today/` produce **no** volume warning. Every run
built from our own extruded geometry produces it, in every cell, on every building.

#### Why it had been measured before and read as harmless

A 2026-08-18 pass measured the same 10 m³ signature, found it on succeeding buildings as well as
failing ones, and concluded it *"looked decisive and was not"*. **The observation was right and the
inference was wrong: the stub is necessary, not sufficient.** What separates the failures is the
*size of the substitution error*, which nobody had measured:

| | n | mean computed volume | min |
|---|---:|---:|---:|
| succeeded | 761 | **−683 m³** | −12,050 |
| **failed** | **6** | **−6,096 m³** | **−26,184** |

A zone with thousands of square metres of surface and 10 m³ of air has almost no thermal capacitance,
so any heat-balance residual moves its air temperature by hundreds of degrees inside one timestep.
That is precisely OPEN-42's failure — `Temperature (low|high) out of bounds`, −251 °C to +241 °C — and
it explains why those runs are *numerically marginal* rather than structurally broken: the fatal
storey is not stable between runs (it moved from the topmost storey in E02 to a middle storey in run 2
for `way/472960972` and `way/402215469`).

#### ⚠️ What is NOT claimed

1. **Not that the published `157.1 kWh/m²` is wrong.** Zone volume drives air capacitance, not the
   envelope, the schedules or the internal loads. **Infiltration is written as
   `Flow/ExteriorWallArea`, not air-changes-per-hour** — verified in the IDF — so it is **not** scaled
   by the stubbed volume, which closes the most obvious route from this defect to annual energy.
   **The effect on annual EUI is unmeasured, in either direction, and must not be assumed.**
2. **Not measured on the adopted run.** Its per-building `.err` files no longer exist. The rate is
   measured on runs 2 and 3 and **inferred** for the adopted run from the shared code path.
3. **Not localised in code.** The geometry is produced through `geomeppy`'s block extrusion rather
   than by a single OpenUBEM line, and this pass did not trace which step reverses the winding.

#### First measurements, in the order they would settle the item

1. **Quantify the EUI cost.** Re-run a handful of buildings with `Zone.Volume` written explicitly
   (footprint × height) instead of `autocalculate`, and diff the annual EUI against the stubbed run.
   Local, small, and it converts an unmeasured risk into a number.
2. **Localise the writer.** Find where floor/ceiling vertex order is set and whether it is our code or
   `geomeppy`'s default.
3. **Then and only then decide the remedy** — write `Volume` explicitly, or fix the winding.

**Closure condition.** OPEN-56 closes when zone volume is correct at the simulation boundary — no
`Indicated Zone Volume <= 0.0` warning in a fleet run — **and** the EUI difference against the stubbed
baseline is measured and reported, whatever its size.

**Blast radius:** every building the project has simulated through this path.
**Evidence:** `extra/MEASUREMENT_ten-items-2026-08-18-late.md` §2;
`openubem/outputs/comparisons/open42_zone_volume_census.csv`,
`open42_run2_fatal_zone_geometry.csv`; scripts `scripts/analysis/open42_zone_volume_census.py`,
`open42_run2_fatal_zone_geometry.py`.


> ⚠️ **Amended 2026-08-19 (T03 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`) — the anomaly DOES
> reach the EUI denominator, and whether it is unique fleet-wide is STILL NOT ANSWERED.** This is a
> narrow negative result, **not a fleet clearance**, and it must not be cited as one.
>
> **Confirmed twice.** `relation_3566904` reproduces the overnight figures exactly — declared
> **157,115.5 m²** against EnergyPlus's own multiplier-aware simulated **37,551.2 m²**, ratio
> **4.1840** — cross-validated by two independent extractions (raw `.eio` parse vs the `.sql` summary
> table) agreeing to **six decimal places**. Because the denominator is OPEN-01's remedy, the stub
> geometry propagates into published EUI, not just into cost.
>
> 🔴 **Why the census cannot settle uniqueness, stated plainly.** (a) Only **274 of 6,804** buildings
> in the available corpus (4 %) carry a declared area to compare at all — the other 96 % miss
> `levels`, which is exactly the **OPEN-35** population, so the join structurally cannot reach that
> building class. (b) **`la_urban` and `nyc_centre` have ZERO run-3 simulation output** — no `.eio`
> files at all despite IDFs being present — and **`nyc_centre` is the very cell the ÷4.18 finding came
> from.** The known instance's own cell is unsearchable. The recheck therefore had to run against the
> surviving OPEN-56 A/B work directory instead.
>
> **What the 274 did show.** 4 buildings, all `la_centre`, fall outside ±10 % — but at **+12–18 %**,
> the *opposite* direction and two orders of magnitude short of 4.18. None resembles the pattern.
>
> ✅ **Control caught a real bug before any number was quoted:** the reconciliation check found a
> stem-merging mistake for pre-split `_partN` geometries in `nyc_urban`; after the fix, reconciliation
> passed exactly across all 10 available cells, and the `levels == 1` / no-multiplier control held at
> ratio median **1.0000**.
>
> **The +0.98 % / +0.84 % cost figure above is unaffected** — it already excluded this building.
>
> **Next question this leaves, unowned:** uniqueness needs either run-3 output for `nyc_centre` /
> `la_urban`, or a denominator test that does not depend on a declared `levels`. Full record:
> `extra/MEASUREMENT_open-56_denominator-census.md`, three CSVs under
> `openubem/outputs/comparisons/`, script `scripts/analysis/open56_denominator_census_2026-08-19.py`.
⚠️ **Registered, not scheduled. No remedy authorised.**


### OPEN-57 — `_ssh` intermittently faults with `Unmatched '.`, blocking the OPEN-55 acceptance test 🔴 **OPENED 2026-08-19** ✅ **CLOSED + ID RETIRED 2026-08-19**

✅ **CLOSED + ID RETIRED 2026-08-19** **on the user's ruling of 2026-08-19.** The item asked why `_ssh` faulted and what to do about it. Both halves are answered and the remedy is landed and verified live at **225/226** — the exact figure already on record for that cell, which corroborates the fix independently of its own authors. 🔴 **Read the two faults before reusing this code anywhere:** a deterministic remote-command length limit whose first *failing* wrapper is **8,191 bytes — one byte BELOW 8,192, and it fails anyway**, so no round number explains it; and a Windows-only CRLF-on-stdin fault that returned a clean, plausible, silently wrong **zero** and is invisible on Linux. ⚠️ **What this closure does NOT do:** it does not run OPEN-55's acceptance test, and it does not authorise a blind retry of anything. The test is dispatched separately under `implemenation/previous/PLAN_close-all-2026-08-19.md` with its controls pre-registered.


**Opened by the director, 2026-08-19**, on the explicit recommendation of T02 attempt 3 of
`implemenation/previous/PLAN_ten-items-2026-08-19.md` (executors do not open IDs). The measurement that
justifies it: `extra/MEASUREMENT_open-55_acceptance-test-attempt3.md`.

> **The fault, verbatim and complete.** Remote stderr is a single line:
>
> ```
> Unmatched '.
> ```
>
> Child exit code **1**, captured to `nyc_suburban.EXITCODE` by the launcher the instant
> `Popen.poll()` returned non-`None`. Raised as `RemoteCommandError` from `_remote_results_complete`
> (`scripts/validation/v12_cell_pipeline.py:1082`) via `_ssh` (`:1014`).

> **Two occurrences, and what is the same across them.** Attempt 1 (2026-08-19) and attempt 3
> (2026-08-19, instrumented) both died at the identical call site, on the identical `nyc_suburban`
> 1,589-entry osm_id list, with the identical one-line stderr. **What differed:** the remote fleet
> directory (`open48_refleet3_nyc_suburban` vs the brand-new `open48_refleet3_t02a3_nyc_suburban`),
> and the exact command length. Attempt 2 died silently for an unrelated, still-unexplained reason
> and is not counted as an occurrence of this fault.

> 🔴 **Length is ruled out as the explanation, on measured numbers rather than estimates.**
> Attempt 1's probe measured **23,171** characters. Attempt 3 measured **23,166** (probe body),
> **23,177** (`bash -lc '<probe>'` wrapper), **23,213** (full three-argument `ssh` argv, space-joined)
> — all measured programmatically from the run's own captured traceback. Windows' `CreateProcess`
> limit is ~**32,767**. Nothing is near the cap.

> ⚠️ **This is OPEN-54's fix working, not failing.** Before 2026-08-18 (late), `_ssh` never
> checked the remote exit code and this fault would have surfaced later, somewhere else, with the
> evidence discarded — which is precisely the failure mode OPEN-54 was closed on. **OPEN-54 stays
> closed and retired.** The correct reading is that the new `RemoteCommandError` made a pre-existing
> intermittent fault legible for the first time.

> **What attempt 3 proved was NOT the problem** — each ruled out by construction, not by inspection
> after the fact: **not staleness** (the fresh remote fleet dir was verified absent on the cluster
> both before launch and after the crash, so the 1,589 stale directories from 2026-08-18 18:08 could
> not be scored); **not silent death** (exit code on disk within the same second, plus a 60s heartbeat
> log showing three clean `alive` lines then a clean `EXITED`); **not input drift** (frozen GDF MD5
> `1198ed01bfd3b4463e50da0ae39d8e27`, copied not moved, re-verified after the copy; the run's own log
> confirms a cache load with no OSM fetch).

> **The cost, stated because it is the argument for fixing this before retrying OPEN-55.** All three
> attempts completed their local work successfully — 1,589/1,589 IDFs generated (199.6 s in attempt
> 3, faster than attempt 1's 239.6 s), LIVE_SMOKE both gates PASS — and then discarded all of it at
> the **first remote call**. Roughly 3–4 minutes of good work thrown away per attempt, three times.

> ⚠️ **No fourth attempt was made, and none is authorised.** The dispatch's own stop rule
> (two distinct unexplained failures is already a stop point) fired correctly. **OPEN-55's acceptance
> test cannot be run until this is resolved**, and retrying it unchanged is not a plan.

> **Not investigated, and named so it is not mistaken for settled:** whether the fault is in tcsh's
> handling of the quoted `bash -lc` payload, in the SSH session itself, or load-dependent on the
> cluster side; and whether a shorter probe (chunking the 1,589 osm_ids, or a server-side file list
> instead of an inline `for` loop) avoids it. **No remedy has been attempted, tested, or authorised.**

> ---
>
> ### Amendment — 2026-08-19, later the same day, director: **"transient" is NOT established, and the length check tested the wrong limit**
>
> Raised by the user's question *"why did the last one fail?"* and answered by sweeping the archived
> phase-E cell logs. **No code was changed and no remedy was attempted.**
>
> 🔴 **1. The evidence for "intermittent" is weaker than this section originally claimed.**
> `_remote_results_complete` prints `remote completeness probe: N/M complete` on every call. Across
> all thirteen archived calls in `scratchpad/phaseE_er33_*.log`:
>
> | probe result | cells | what it proves |
> |---|---|---|
> | `225/226 complete` | `la_centre` (two resume runs) | ✅ **the probe provably executed on the cluster and its output parsed** — the only such case in the archive |
> | `0/N complete` | the other eleven: 149, 198, 245, 413, 425, 437, 618, 738, **1343**, **1589**, **1779** | ⚠️ **nothing.** Ambiguous by construction — see below |
>
> ⚠️ **`0/N` cannot be read as a success.** Under the pre-OPEN-54 code the probe's failure path
> printed exactly `0/N` too: `_ssh` returned the remote stderr, the `COMPLETE=(\d+)` regex found no
> match, and `n_complete` defaulted to `0`. That was **deliberate fail-safe design** — see
> `extra/INVESTIGATION_open-54_ssh-unchecked-exit.md:81`, *"regex; no match → `0` → fails safe
> (re-does work)"*. A genuine zero on a fresh fleet directory is also `0/N`. **The two are
> indistinguishable in the logs.**
>
> 🔴 **Consequence: the archive contains no case of a large-list probe provably succeeding,
> and the only call proven to have worked carried 226 ids.** So the two failures on the 1,589-entry
> list are equally consistent with a second hypothesis this section did not state: **the large-list
> probe may never have worked, and OPEN-54's exit-code check is simply the first time anyone could
> see it.** "Transient" is now **one of two live hypotheses, and the weaker one** — it is the only
> reading under which a 2-for-2 failure on identical input is coincidence.
>
> 🔴 **2. The length ruling tested the local limit, not the one that would bite.** The
> measurement was correct and stands: 23,166–23,213 chars against Windows' ~32,767 `CreateProcess`
> cap. But **the parse that failed happens on the remote host, not locally.** `_ssh`
> (`scripts/validation/v12_cell_pipeline.py:139`) sends a *single* argv string —
> `["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"]` — which `sshd` hands to the **remote login shell,
> tcsh**, to parse. tcsh must therefore lex one quoted word of **23,177 characters**, and
> `Unmatched '.` is **tcsh's own error text for a quote it could not close.** **tcsh's input/word
> buffer was never measured.** That is the limit the evidence points at, and it is untested.
>
> ✅ **3. A code detail that favours the parse-side reading.** The probe opens with
> `cd {remote_fleet_dir}/out 2>/dev/null || exit 0` (`:1006`). Attempt 3's remote directory was
> **verified absent**, so a shell that parsed the command would have exited **0** with no output.
> It did not — it returned a syntax error. **The failure is therefore upstream of any remote
> filesystem work**, which is where a lexer limit would sit and is hard to reconcile with cluster
> load or a flaky session.
>
> ✅ **4. The discriminating test, and it is cheap, offline and login-node-safe.** Call
> `_remote_results_complete` **alone** — no fleet run, no IDF generation, no simulation — against
> one existing remote directory with progressively longer id lists (226 → 500 → 1,000 → 1,589),
> and find the length at which `Unmatched '.` first appears. **One `ssh` call each; no compute on
> the login node.** If a threshold exists, the fault is **deterministic and length-dependent**, this
> item is fully understood, and no further blind retry is ever needed. If all four succeed, the
> transient reading is confirmed on evidence instead of by default. **Either outcome closes the
> question this section currently leaves open.**
>
> ✅ **5. Candidate remedy, stated but NOT authorised, and only if the threshold is found.** Stop
> embedding the id list in the command line: pipe the ids over **stdin**, chunk the list, or drop
> the inline `for` loop entirely and have the remote side enumerate `out/*/eplusout.end` itself and
> return the count. Each keeps the command a few hundred characters regardless of fleet size.
>
> ⚠️ **Unchanged by this amendment:** no remedy attempted, no fourth OPEN-55 retry authorised,
> OPEN-54 stays closed, and **nothing here restates a fleet figure.**

✅ **RESOLVED — 2026-08-19, T02–T05 of `implemenation/previous/PLAN_open-57-and-58_2026-08-19.md`.**
Record: `extra/MEASUREMENT_open-57_probe-length-threshold.md`; sweep harness
`scripts/diagnostics/open57_probe_length_sweep.py`; tests `tests/test_v12_ssh_stdin.py` (11).

> 🔴 **It was never transient, and it was two faults, not one.** The register's own amendment
> was right to reject "transient" — the first fault is fully deterministic.
>
> **Fault 1 — remote command length.** `_remote_results_complete` embedded every osm_id in a
> single-line probe. `_ssh` sends one argv string, so `sshd` hands it to the remote **login shell,
> tcsh**, which must lex one giant quoted word. Bisected to single-id resolution over 20+
> instrumented calls, every one landing on a predicted outcome: **565 ids parse, 566 do not.**
>
> | measure | last passing (565 ids) | first failing (566 ids) |
> |---|---:|---:|
> | probe body | 8,166 B | 8,180 B |
> | wrapper (`bash -lc` + quotes) | 8,177 B | 8,191 B |
> | full `ssh` argv | 8,213 B | 8,227 B |
>
> 🔴 **The boundary is NOT 8,192, and this is recorded so no future reader "rounds" it.** The
> first *failing* wrapper is **8,191 bytes — one byte below 8,192** — and it fails anyway, which
> rules out a simple "must fit under 8,192" reading outright. No round number (4,096 / 8,192 /
> 10,240 / 16,384 / 20,480) matches at any of the three measures. **Content is innocent:** at both
> the passing and the failing length, three variants (real id list, one long single token, double
> quotes removed with length restored by padding) flipped identically — length alone is the cause.
> The sweep was safe by construction: the probe opens with a `cd` into an `out` directory verified
> **absent**, so a shell that parses exits 0 touching no file and a shell that cannot parse returns
> the unmatched-quote error — a clean binary on the parse alone, with **zero filesystem work and
> zero login-node compute.**
>
> **Fault 2 — CRLF on stdin, found only because the first fix still read 0.** With ids moved to
> stdin the probe returned **0/226 against a fleet directory that was real and populated**. That
> looked like a purged scratch dir and was very nearly accepted as one. It was not: a control that
> sent 1,589 ids to a remote loop doing nothing but counting them returned **`GOT=1589`**, proving
> transport was intact, while an `ls` proved the directory held exactly its 226 entries with
> `eplusout.sql` and `eplusout.end` present. Cause, verified locally with **no cluster contact at
> all**: `subprocess.run(..., text=True, input=...)` wraps the child's stdin in a
> `TextIOWrapper(newline=None)`, which **on Windows rewrites every LF to CRLF on write**. The remote
> `while read o` therefore received each id with a trailing carriage return, and every
> `[ -s "$o/eplusout.sql" ]` tested a path with a control character inside it. It never matched, so
> the count stayed 0 **no matter how many buildings were genuinely complete.** This fault is
> invisible on Linux, and it returns a clean, plausible, silently wrong answer — the failure mode
> this register exists to catch.

**Remedy, in `_ssh` only** (`scripts/validation/v12_cell_pipeline.py`): ids are sent on **stdin**
(`stdin_data`), so probe length is now flat regardless of fleet size, and when `stdin_data` is given
the call sends **raw bytes** and decodes stdout/stderr explicitly. `stdin_data=None` is byte-for-byte
the prior code path, so **no existing caller is affected**. Remote-side enumeration of the `out`
directory was **rejected** — it silently changes the question from *"is every one of these specific
oids complete"* to *"how many directories are complete"*. The chunking fallback was **not** used.
**OPEN-54's raise-on-non-zero is preserved** — it is the only reason this fault was ever visible.

✅ **Verified live:** the same 226 ids against the same fleet now return **225/226 complete** — the
**exact figure already on record** for that cell, which corroborates the fix independently of the
fix's own authors. Suite: **1,893 passed / 55 skipped** (baseline 1,885 plus the new tests).

⚠️ **Recommended to the user, NOT taken here: close OPEN-57.** Closure is the user's call and has
not been made — the item stays live in §1 until then. ⚠️ **OPEN-55's acceptance test was NOT run**
and is not authorised by this fix; it needs a separate user decision.

---

### OPEN-58 — `open56_zone_volume_experiment.py`'s `run_ep()` cross-contaminates outputs and reads EUI by the wrong formula 🔴 **OPENED 2026-08-19**

**Opened by the director, 2026-08-19.** Found by **T04's own controls** while executing OPEN-35's
intervention — not by a task that went looking for it, which is one more instance of this arc's
most reliable source of real defects: auditing an artifact for a different question. Full record:
`extra/MEASUREMENT_open-35_storey-intervention.md` and this register's **OPEN-35** amendment.

> **Defect (a) — cross-contamination.** `run_ep()` invokes EnergyPlus with `-x`, and buildings that
> share a working directory can overwrite each other's outputs. **Caught as two byte-identical
> `.sql` files produced for two different building footprints** — a physically impossible result,
> which is what made it visible.

> **Defect (b) — wrong EUI formula.** It computes EUI as Total Site Energy ÷ Total Building Area.
> **Production does not do this.** `openubem/results/parser.py`'s `total_eui_kwh_m2`, read via
> `parse_building()`, sums the per-end-use EUIs over a **multiplier-aware `.eio` area**. The two
> agree only when the multiplier is 1 and the areas coincide.

> ✅ **T04 did the right thing and it is worth stating.** It **voided its own first full run**
> — already computed, already tabulated — and re-ran clean under a per-building working
> directory with the production parser, rather than patching the numbers or noting the bug in a
> footnote. Its authoritative output is `open35_storey_intervention_results_v2.csv`; the earlier
> `_results.csv` is **superseded and must not be cited**. **OPEN-35's published numbers are not
> affected by this item.**

> 🔴 **The open question is the blast radius, and it is unmeasured.** Any earlier **local
> batch** result that imported `run_ep()` from `open56_zone_volume_experiment.py` is exposed to both
> defects. **No audit has been done** of which scripts import it or which published figures descend
> from them. Until that audit exists, this item's population field reads *unknown* deliberately —
> it is not a way of saying *small*.

> ⚠️ **Explicitly not scoped to OPEN-35.** OPEN-35's amendment records the discovery because
> that is where it was found; the item itself is about every *other* consumer of the helper. Do not
> close this by pointing at OPEN-35's clean re-run.

✅ **BLAST RADIUS MEASURED — 2026-08-19, T06–T08 of `implemenation/previous/PLAN_open-57-and-58_2026-08-19.md`.**
Record: `extra/MEASUREMENT_open-58_blast-radius.md`; artifact table
`openubem/outputs/comparisons/open58_blast_radius_artifacts.csv` (6 rows).

> **Three real importers, not four or seven.** `open56_fleet_cost_stratified.py:37-38`,
> `open56_fleet_cost_repair.py:24`, and `open35_storey_intervention_2026-08-19.py:89`
> (`read_run` only — it deliberately overrides `run_ep` with its own `run_ep_isolated`, `:82-98`).
> Four further scripts define their **own** local `run_ep`/`_run_ep` and are name collisions, not
> importers, each confirmed by its `def` line: `a3_measure_band_deletion.py:93`,
> `t01_reproduce_degenerate.py:73`, `t04_validate_way428643335.py:82`,
> `t06_validate_relation6374725.py:83`. No git history exists for any of them — the origin file
> and all its importers are untracked.
>
> 🔴 **Defect (a)'s mechanism was stated wrongly when this item was opened, and the correction
> matters.** It is **not** a shared `-d` outdir — every real importer already passes a
> per-building-unique outdir. EnergyPlus's `-x` / ExpandObjects step reads and writes relative to
> the **process's current working directory**, which is shared across every invocation unless
> `cwd=` is passed explicitly. Only `run_ep_isolated` does. So **all three** importers are exposed,
> including the two that run serially — concurrency is not the distinguishing factor, and an audit
> that had looked only for parallel runs would have cleared two of the three wrongly.
>
> 🔴 **One confirmed contamination, found by direct test rather than by inference.** All 173
> surviving `eplusout.sql` files were hashed and 166 arm-cells recomputed with production's
> `parse_building()`, which independently checks the zone-key osm_id. **Exactly 1 of 166 raised
> `RuntimeError: I2 breach: foreign osm_id`:** `open56_fleet_cost_stratified.csv`'s
> `nyc_centre/relation_3566904` base arm, whose `.sql` zone keys read `RELATION/11171793_F0_WHOLE`.
> Director-verified independently from the CSV: that row's `base_site_energy_gj` (150207.12),
> `base_floor_area_m2` (157115.48) and `base_eui_kwh_m2` are **byte-identical to
> `relation_11171793`'s own base-arm row, to fifteen significant figures.** Two distinct buildings
> cannot produce identical energy to the last digit; this is contamination, not coincidence.
> The row was already excluded from the register's pooled cost statistic — but **for a wrong stated
> reason** ("geometry mis-reports area"). The stated reason is corrected here to contamination.
>
> ✅ **Zero cited or published figures are corrupted.** Defect (b) shifts absolute EUI by −0.4 % to
> −24.0 % per arm (median −1.4 %), driven by production's deliberate exclusion of
> `fans_eui_kwh_m2` — but every figure this register cites from these artifacts is a **relative**
> pct_change on the same building, which cancels the bias. Recomputed under production's formula:
> `open56_zone_volume_experiment.csv`'s cited +0.75 % / +0.67 % / +1.67 % reproduce as
> **0.7739 % / 0.6847 % / 1.6920 %**; `open56_fleet_cost_stratified.csv`'s post-exclusion
> +0.98 % / +0.84 % reproduce as **1.0165 % / 0.8584 %**, with the same-sign fraction identical
> (65/69).

⚠️ **Still open, and still no remedy authorised.** Neither defect is fixed — only its reach is
now known. What changed is that the blast radius is **measured** (3 importers, 6 descended
artifacts, 1 unsound row, 0 unverifiable) instead of unknown. Four corrections are **recommended to
the user and not taken here**: correct this item's own "shared outdir" language to "shared process
cwd"; correct the stated reason for excluding `relation_3566904`; annotate that row in the raw CSV;
and decide whether either defect gets a remedy at all.

---

Nothing in this register is scheduled. Nothing is assigned. No cluster time is committed.


---

### OPEN-59 — With the equipment defect cured, Unknown buildings still use 1.7× what classified buildings use; the gap moved to hot water and heating 🔴 **OPENED 2026-08-19**

**Opened by the director's audit of OPEN-55's passing acceptance test, 2026-08-19.** ⚠️ **This item exists because a test passed.** OPEN-55's acceptance test asked one question — *do the divergences go away* — and the answer was an unambiguous yes, 71 → 0. Reading only that result, the Unknown archetype looks fixed. It is not, and the evidence was sitting in the same output file.

#### What was measured

`nyc_suburban`, run `open48_refleet3_t02a4`, job 1274983, 1,589 buildings all simulating successfully — 290 `OpenUBEMUnknown` against 1,299 classified. Medians, computed by the director directly from `05_results.csv` rather than taken from the executor's summary:

| end use (median, kWh/m²) | Unknown (290) | Classified (1,299) | Δ | ratio |
|---|---:|---:|---:|---:|
| heating | 140.1 | 99.0 | **+41.1** | 1.4× |
| cooling | 25.0 | 4.5 | **+20.5** | **5.6×** |
| lighting | 26.7 | 4.0 | **+22.7** | **6.7×** |
| equipment | 37.5 | 43.4 | **−5.9** | **0.86×** |
| DHW | 103.5 | 42.5 | **+61.0** | 2.4× |
| **total** | **349.4** | **202.8** | **+146.6** | **1.72×** |

#### Why this is not a reopening of OPEN-55

🟢 **The equipment row is the proof that the OPEN-55 screen worked.** Before it, the median Unknown equipment draw was 2,692.27 W/m² and the column dominated everything; after it, Unknown buildings sit **below** classified ones on equipment (0.86×). That defect is cured. What this item records is that curing it did **not** bring Unknown buildings into the classified range — it revealed that four other columns were also high, and equipment had been masking them.

#### What is not known

🔴 **The cause is not diagnosed and no remedy is proposed here.** Two hypotheses are open and they have different remedies:

1. **The same widened-bounds pattern OPEN-55 found in the equipment column also affects the DHW, lighting and occupancy columns.** OPEN-55's mechanism was that a uniform draw over the full 29-archetype donor table lets the maximum set the *centre*, not the tail. The B+ screen removed seven donors **on the equipment column** (and `Warehouse` on occupancy). If the lighting and DHW columns still draw over the unscreened pool, this is OPEN-55's sibling and the remedy is the same screen applied column-wise. The 5.6× and 6.7× cooling and lighting multiples are consistent with this and are the first place to look.
2. **The Unknown donor pool is genuinely higher-intensity than the buildings it stands in for.** If so this is a calibration question, not a defect, and the remedy is a different donor pool — or better classification, which would shrink the Unknown population instead of correcting it.

**Distinguishing them is cheap and local** — it needs the drawn PDE columns for the 290 Unknown buildings compared against the donor-table bounds per column, the same comparison OPEN-55 §3 already did for equipment alone. No cluster time.

#### Blast radius

⚠️ **Unmeasured, and materially larger than one cell.** Unknown buildings are 18.3 % of `nyc_suburban` and occur in every cell; the register's last count put them at ~650 fleet-wide. At +146.6 kWh/m² median excess this lifts the pooled fleet figure by an amount nobody has quantified. **T04 of `implemenation/previous/PLAN_close-all-2026-08-19.md` has been commissioned to measure it** — per-cell Unknown counts and floor-area shares, the Unknown/classified split across all five end uses, and the pooled figure recomputed with Unknown buildings excluded as a **diagnostic only**. 🔴 **The excluded-Unknown figure is not a candidate baseline and must never be restated as one** — it exists to size this item, and dropping 18 % of the fleet to make a number look better is precisely the defect OPEN-43 named.

⚠️ **This item does not block the T03–T05 restatement.** The restatement is already known to be provisional — OPEN-56 makes it low by ≈ 1.0 kWh/m² per building — and adding a second known-open caveat does not change the decision the user already took. It changes what the restatement document must say on its face.


---

#### 🔵 Amended 2026-08-19 (late, director, on the user's ruling *"tu progresses comme tu recommandes"*) — REFRAMED, not closed

**Hypothesis 1 is refuted by direct measurement.** T02 of `implemenation/PLAN_gap-decomposition-2026-08-19.md`
ran exactly the comparison this item asked for — the four drawn PDE columns for all 290 `OpenUBEMUnknown`
buildings of `nyc_suburban`, each against its own donor-table bounds:

| column | drawn min / median / max | donor bound | out of bounds |
|---|---|---|---|
| `lighting_w_m2` | 3.454 / 10.869 / 18.246 | 3.44 – 18.30 | **0 of 290** |
| `equipment_w_m2` | 2.590 / 9.153 / 16.067 | 2.58 – 16.15 | **0 of 290** |
| `occupant_m2_per_person` | — | within | **0 of 290** |
| `wwr` | — | within | **0 of 290** |

**0 of 4 columns and 0 of 290 buildings out of bounds; worst excursion 0.0 on every column.**
Artifact: `openubem/outputs/comparisons/open59_pde_bounds_screen.csv`.

🔴 **This is not OPEN-55's sibling, and no screen can fix it.** OPEN-55's mechanism was an *illegal*
draw — a data-centre equipment load reachable by an ordinary building through widened bounds. Here every
draw is **legal**. A column-wise screen of the kind that cured OPEN-55 has nothing to remove.

🔵 **Hypothesis 2 therefore stands by elimination, and the item changes character.** The Unknown donor
pool is genuinely higher-intensity than the buildings it stands in for. That makes this a **calibration
question, not a defect** — the remedy is a **different donor pool, or better classification** (which
shrinks the Unknown population rather than correcting it), and neither is a bug fix.

**Why the ID is kept open rather than closed.** The screen answered *why not*, not *why*. The
phenomenon is unchanged and unexplained: fleet-wide, Unknown buildings run **10.2× on DHW** and 3.4× on
heating, and the typical Unknown building is small and hot (median 309.95 vs 134.08 kWh/m²) while the
Unknown floor area is dominated by ten large moderate buildings (pooled 107.22 vs 155.56 — *below*
classified). Closing the ID would retire the only record of that. **What is retired is the diagnosis,
not the item.**

⚠️ **The blast-radius paragraph above still stands as written** — Unknown buildings are 3.7 % of fleet
floor area and the fleet-EUI effect remains unquantified. Reframing the cause does not size the effect.

---

### OPEN-60 — `total_eui_kwh_m2` undercounts lighting and equipment wherever a zone multiplier is in play 🔴 **OPENED 2026-08-19**

**Opened by the director 2026-08-19 (late), on the user's ruling *"tu progresses comme tu recommandes"*.**
⚠️ **This item exists because a task checked its own arithmetic.** T01 of
`implemenation/PLAN_gap-decomposition-2026-08-19.md` was commissioned to split 48 buildings by end use.
It began, correctly, by testing whether the end-use pieces sum to the total the parser reports. **They
did not — only 6 of 48 reconciled within 2 %.** Nothing in the plan asked for that control; it was the
executor's own first move, and it is the reason this defect is known.

#### Mechanism — traced, not inferred

`total_eui_kwh_m2` sums **Interior Lighting** and **Interior Equipment** from **per-zone hourly output
variables**, which EnergyPlus does **not** scale by the zone multiplier. The floor area those sums are
divided by **is** multiplier-aware (`openubem/results/parser.py:431-433`, `resolve_simulated_floor_area()`).
A zone standing in for 12 storeys therefore contributes **one storey** of lighting and equipment energy
against **twelve storeys** of floor area.

🟢 **The mechanism is confirmed by what is *not* affected.** Cooling, heating, fans, pumps and hot water
are read from the multiplier-correct ABUPS table and match it to **<0.01 %**. Only the two end uses read
per-zone diverge. That asymmetry is the signature, and it rules out a general parsing error.

#### Size (n = 48 untrimmed `layout_assign` buildings)

| statistic | value |
|---|---|
| buildings reconciling within 2 % | **6 of 48** |
| buildings affected | **42 of 48** |
| reconciliation error — median | **4.71 %** |
| — mean | 17.56 % |
| — 90th percentile | 24.19 % |
| — **maximum** | **192.28 %** |
| buildings exceeding 10 % | **14** |

Artifact: `openubem/outputs/comparisons/open03_enduse_by_building.csv`.

#### Blast radius — bounded, and verified rather than assumed

🟢 **No adopted number is affected.** Zone multipliers are written in **exactly one module** —
`openubem/geometry/layout_assigner.py`, `match_storeys()`, `z_obj.Multiplier = residual_multiplier` at
`:649`. No other module in `openubem/` writes one, and the `auto` production path never calls it. The
director read **three run-4 `auto` fleet IDFs directly** rather than reasoning about them: **every
`Multiplier` field is 1**. **153.8231 kWh/m² pooled over 8,153 buildings and 24,320,582 m² is untouched.**

🔴 **Every `layout_assign` EUI this project has ever recorded is too low.** That is the full extent, and
it is a mode already labelled *not certified for fleet EUI*. The concrete casualties are OPEN-03's and
OPEN-18's published sample figures, **corrected the same night** — the cross-mode gap fell from −26.25 %
to **−11.26 %** pooled and from −24.40 % to **−17.72 %** median, and the count of buildings above `auto`
rose from **1 of 48 to 8 of 48**. See §10 of `extra/MEASUREMENT_open-03-18_untrimmed-sample.md`.

#### 🔴 The gate that catches this already exists, and the fleet pipeline never calls it

`check_building_integrity()` (`openubem/results/parser.py:602-646`) performs exactly this ABUPS
cross-check and returns `abups_ok=False` for the worst offender in this sample. It is called by
`scripts/run_r1_t12.py:211`, `scripts/run_r3_fleet.py:313`, `scripts/run_r3_step5.py:204` and
`scripts/run_t12_boston.py:198` — but **not** by the path that produced `05_results.csv`. **This defect
was detectable by code already in the repository for the whole time it went unnoticed.** That is the
more general finding, and it is not confined to multipliers.

#### What is not known, and what is not proposed

❓ **No remedy is proposed and none is authorised.** Two shapes exist and they are not equivalent:

1. **Read the two end uses from ABUPS**, as the other five already are. Smallest change, and it makes
   the total internally consistent by construction — but it discards the per-zone breakdown for exactly
   the two end uses a room-by-room mode exists to resolve.
2. **Make the per-zone sum multiplier-aware.** Preserves the breakdown, but requires the multiplier to be
   read back per zone at parse time and is the larger change.

**Choosing between them is feature code, which this session does not write.** 🔴 **A third question is
open and is not a remedy choice:** whether the fleet pipeline should call `check_building_integrity()`
at all — that would have caught this, and would catch the next one, independently of which fix is taken.

#### Relationship to other items

- **OPEN-32** bounds this to zero effect on adopted results by the same structural argument (`auto`
  cannot reach `layout_assign`) — that argument is re-verified here at the IDF level, not re-asserted.
- **OPEN-03 / OPEN-18** are the two items whose measured sizes this defect changed. Both carry the
  correction on their own headings.
- ⚠️ **This is the second time in two passes that an executor's headline conclusion did not survive the
  director re-deriving it** — and the first time that the re-derivation opened a new defect rather than
  merely resizing a claim.
