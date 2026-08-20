# PLAN — the compute queue (C01 … C06)

> **Slug:** `compute-queue` · **Opened:** 2026-08-06 · **Author:** manager session
> **Binding contract:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` (the item
> definitions) and `docs/docs_ACTIVE/openings/extra/SCOPING_five-mode-rerun-cost.md` Part 2 (the
> costed local plan). Neither may be edited by an executor.
> **Predecessors:** `PLAN_published-numbers.md` (M01–M05, E01/E01b/E01c, E02 scoped-not-run) and
> `PLAN_no-compute-queue{,-2,-3,-4}.md` (N01–N16, all landed and audited).

---

## 1. Why this plan exists, and what changed

Every one of the sixteen no-compute tasks has landed. **Every first measurement still open in the
register needs the processor.** On **2026-08-06 the user released the local workstation for
simulation** and instructed the arc to run to completion overnight, updating documents as it goes.

This plan is the compute counterpart of the no-compute queue: same discipline (one written task per
measurement, prediction stated before dispatch where one is possible, director audit by independent
re-derivation, never by reading the report back), applied to work that costs cycles.

### 1.1 🔴 The blocker found while opening this plan — read before scheduling anything

`SCOPING_five-mode-rerun-cost.md:11` scopes E02 as **five modes × twelve cells × 8,160 buildings**.
The local runner cannot do that, for **two** reasons, and only one of them was on record:

| # | Gap | Evidence | On record before today? |
|---|---|---|---|
| 1 | `layout_assign` is not a runnable mode | `scripts/cluster/t08_local_remainder.py:52` — `ALL_MODES = ["auto", "building", "floor", "fast_zone"]`, and `:565` binds `--modes` `choices` to it | **Yes** — director prompt §4.12, `PLAN_published-numbers.md` §9 |
| 2 | **Only 7 of the 12 cells are configured** | `:48-51` `LOCAL_CELLS` holds the LA/Austin remainder only; `nyc_centre`, `nyc_urban`, `nyc_suburban`, `nyc_rural`, `la_centre` have **no `CELL_CONFIGS` entry** (`:59-67`) and no `CITY_OF` entry (`:54-58`); `:562` binds `--cells` `choices` to it | 🔴 **No — found 2026-08-06 by the director while answering "what can we start"** |

Gap 2 is the load-bearing one, because it has an attractive wrong answer.

> **Decision, pinned — all twelve cells run locally, on one code generation.**
>
> The runner is named `t08_local_remainder` because it was built to do the **remainder** of the
> cluster's T08: the 7 cells T08 never covered. The tempting shortcut is therefore to run those 7
> locally and reuse the cluster's T08 for the other 5.
>
> **That would rebuild OPEN-28, the exact defect this re-run exists to destroy.** T08 is
> five-week-old code (`builder.py` has moved 223 insertions / 39 deletions since — Part 1 §4.3),
> and T08 deleted every `.eio`, so it can serve **neither** OPEN-02 (which is *"no fleet EUI has a
> simulation-verified denominator"*) **nor** a cross-mode delta that means the method rather than
> the calendar. Mixing generations is the disease, not the cure.
>
> All twelve cells' Stage-2 inputs are on disk locally (`docs/docs_VALIDATION/validations/overAll/
> results/phaseE/<cell>/01_buildings.gpkg`, all 12 present — director-verified), so this is a
> configuration addition, not new machinery.

---

## 2. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Never `cd` elsewhere to write.
2. **You execute this plan. You do not write plans.** If you believe a task is wrong, STOP and quote
   the conflict — do not redesign it.
3. **Never touch the cluster.** No `ssh`, no `sbatch`, no `srun`, no `scancel`, not even read-only.
   This entire plan is local.
4. **Never `git commit`, `git add`, `git push`, or offer to.** Git is handled externally by the user.
5. **Never edit** root `main.py`, any `OVERVIEW`/`DESIGN` doc, anything under `docs_DONE/`,
   `docs_main/`, `docs_TODO/`, `openubem/idf/opaque_assembly.py`, `openubem/viz/`, or the
   `t17_*`/`t18_*`/`t19_*`/`t20_*` harvest scripts.
6. **No `.py` files under `docs/`, ever.** Measurement scripts are throwaways: write them in your
   session scratchpad, not in the repo, unless a task explicitly says otherwise.
7. **Default to no comments.** One short line only where the *why* is non-obvious.
8. **Figures go flat to `openubem/outputs/`**, then are mirrored into `docs/docs_ACTIVE/openings/extra/`.
9. **Append a progress-log entry to §8 of this document for every task you complete** — format in §8.
   The log is the binding record; a task without a log entry did not happen.
10. **No silent caps.** If you sample, truncate, cap a top-N, or skip a retry, say so *in numbers* in
    both the report and the log entry. Silent truncation reads as full coverage and is the single
    failure mode this arc has been burned by most.
11. **Stop-and-ask on spec ambiguity. Never invent a number.** "Not measured" is an acceptable
    answer; a plausible-looking guess is not.

---

## 3. Dependency decisions — pinned, do not re-debate

| Decision | Value | Why |
|---|---|---|
| Cells | **all 12**, run locally | §1.1. Mixing local + cluster T08 rebuilds OPEN-28. |
| Modes | **all 5**, `layout_assign` **last** in the list | The four already-exercised modes complete first for every cell, so an overnight failure still leaves complete, analysable cells behind. |
| Loop order | cell-outer, mode-inner (**unchanged**, `:645-670`) | Progress accrues as *whole cells*, which is the unit every downstream analysis groups by. |
| EnergyPlus workers | **16** of 20 | Deviation from the scoping doc's 12, recorded in §4.1 below with its reason. |
| Step-3 workers (`--n-jobs`) | default (`cpu_count-2` = 18) | Step 3 is short and CPU-cheap next to Step 4. |
| Output CSV | **new file**, `openubem/outputs/comparisons/e02_five_mode_fleet_eui.csv` | The runner clobbers its output CSV after every cell (`:676-680`, `:689`). The existing `t08_local_remainder_eui.csv` is a real 2026-07-01 artifact and **must not be overwritten**. |
| Work base | **new dir**, `%TEMP%/ubem_e02_five_mode` | Gives E02 its own resume namespace, so its `sim_done.txt` markers can never be confused with an older run's. |
| Trimming | **as built by E01/E01b — do not modify** | Retention `.eio`/`.sql`/`.err`/`.end`/`task.rc` (`:73`), delete list `:75-81`, 50 GB disk floor (`:82`). Audited; leave it alone. |
| `.eio` | **retained, always** | It is the only record of simulated floor area — the whole point of the re-run (OPEN-02). |

### 3.1 Why 16 EnergyPlus workers and not the scoped 12

`SCOPING_five-mode-rerun-cost.md` Part 2 §1 pinned **12 of 20**, reserving 8 cores because *"this is
the user's day-to-day machine"* and the run would overlap their working hours. **That premise does
not hold tonight** — the user has explicitly released the machine and gone to sleep. The same
scoping table already costs the alternative: **16 workers → ≈7.3–11.3 h**, against 12 workers'
≈10–15 h. Sixteen lands before morning; twelve might not.

Four cores stay free for the OS and for C03 running alongside. RAM at 16 workers is 63.5 GB ÷ 16 ≈
4.0 GB/worker, still generous for EnergyPlus processes measured in low hundreds of MB.
**This is a deliberate, stated deviation from an audited number, not a silent change.**

---

## 4. Source-of-truth verified facts — grepped by the manager 2026-08-06

Cited so no executor has to re-derive them. Line numbers are at HEAD on 2026-08-06.

### 4.1 The canonical twelve-cell configuration already exists in this repo
`scripts/cluster/t08_full_sweep.py:58-71` holds all twelve `CELL_CONFIGS` entries. The seven that
`t08_local_remainder.py:59-67` already carries are **byte-identical** to their canonical
counterparts (director-checked, entry by entry). **The five missing entries are to be copied
verbatim from `t08_full_sweep.py`, not re-derived, not looked up, not rounded:**

```
"nyc_centre":    {"lat": 40.7549, "lon": -73.9840, "state": "NY"},
"nyc_urban":     {"lat": 40.7721, "lon": -73.9301, "state": "NY"},
"nyc_suburban":  {"lat": 40.7052, "lon": -73.5985, "state": "NY"},
"nyc_rural":     {"lat": 42.0396, "lon": -74.1143, "state": "NY"},
"la_centre":     {"lat": 34.0522, "lon": -118.2437, "state": "CA"},
```

### 4.2 The city label convention is fixed and joins are built on it
`scripts/cluster/t08_harvest_results.py:49-50` maps `nyc_* → "NYC"`, and `t20_harvest_layout_assign.py:78`
repeats it. The published CSVs use exactly `NYC` / `LA` / `AUS` (director-verified against
`t20_layout_assign_eui.csv`, whose `city` column holds those three values over 12 cells).
`t08_local_remainder.py:423` reads `CITY_OF.get(cell, cell)` — a **silent fallback to the cell name**,
so a missing entry produces `city="nyc_centre"` instead of `"NYC"` and quietly breaks every
city-level group-by rather than raising. `CITY_OF` must be extended, not left to the fallback.

### 4.3 `layout_assign` already flows through the same Step-3 entry point
`scripts/cluster/t17_layout_assign_full_sweep.py:67` sets `_MODE = "layout_assign"` and drives the
**same** `run_step3_mode()` helper that `t08_local_remainder.py:648` imports from
`t08_full_sweep.py`. The mode string is therefore known-good on this exact code path; adding it to
`ALL_MODES` is a list edit, not an integration.

### 4.4 The resume mechanism, and why the work base must be new
`is_done()` / `mark_done()` (`:158-161`) key on `work_base/<cell>/sim_out_<mode>/sim_done.txt`. The
default work base is `%TEMP%/ubem_t08_local` (`:580`). **Director-verified 2026-08-06: that directory
does not currently exist**, so there are no stale markers today — but E01, E01b and E01c all ran
through it, and a future re-creation must not be able to make E02 skip a cell it never ran. A
separate work base removes the failure mode entirely.

### 4.5 The output CSV is overwritten, not appended
`:676-680` rewrites `OUTPUT_CSV` after **every cell**, and `:689` again at the end.
`openubem/outputs/comparisons/t08_local_remainder_eui.csv` exists (4.18 MB, dated 2026-07-01) and is
a genuine prior artifact. Running E02 against the default constant would destroy it silently on the
first cell boundary.

### 4.6 The disk guard is real and already corrected
`DISK_FLOOR_BYTES = 50 GB` (`:82`), enforced inside the windowed submission loop (`:316-326`) that
E01b built after the original check was proven structurally blind. Worst-case fleet disk for a
trimmed five-mode pass is ≈43 GB against 659 GB free. **Do not raise, lower, or bypass the floor.**

---

## 5. Task list

Each task states **what**, **why**, **how**, and **how to test**. Tasks C04–C06 depend on C02's
artifacts and must not start before it lands.

---

### C01 — Extend the local runner to twelve cells and five modes *(no CPU; gates everything else)*

**What to do.** Edit `scripts/cluster/t08_local_remainder.py` only, so that it can run all twelve
cells and all five resolution modes, and so that E02 writes to its own output CSV and work base.

**Why.** §1.1. Without this the runner covers 7/12 cells and 4/5 modes, and E02 as scoped by
`SCOPING_five-mode-rerun-cost.md:11` cannot be run at all. This is pipeline code, which is why it is
a written task with a fresh executor and not a director edit.

**How.**
1. `LOCAL_CELLS` (`:48-51`) → all twelve, in the canonical order of `t08_full_sweep.py:58-71`
   (`nyc_centre, nyc_urban, nyc_suburban, nyc_rural, la_centre, la_urban, la_suburban, la_rural,
   austin_centre, austin_urban, austin_suburban, austin_rural`).
2. `CITY_OF` (`:54-58`) → add `nyc_centre/nyc_urban/nyc_suburban/nyc_rural → "NYC"` and
   `la_centre → "LA"`. Use those exact strings (§4.2).
3. `CELL_CONFIGS` (`:59-67`) → add the five entries in §4.1 **verbatim**. Do not touch the existing
   seven.
4. `ALL_MODES` (`:52`) → `["auto", "building", "floor", "fast_zone", "layout_assign"]`.
   `layout_assign` goes **last** (§3).
5. Add two CLI flags, both defaulting to today's behaviour so nothing existing changes:
   - `--output-csv` (default `OUTPUT_CSV`, i.e. `t08_local_remainder_eui.csv`)
   - `--work-base` (default `Path(tempfile.gettempdir()) / "ubem_t08_local"`)
   Thread them through `main()` in place of the module constant / hard-coded path. Every call site
   that currently reads `OUTPUT_CSV` (`:611-618` resume-load, `:676-680`, `:689`) must read the flag.
6. Update the `argparse` description (`:560`) and the two `--cells` / `--modes` help strings
   (`:563`, `:566`), which say "7 cells" and "all 4". Update the module docstring's
   corresponding claim if it states a count.
7. **Change nothing else.** Not the trim block, not the disk guard, not `_run_one_ep`, not the
   harvest, not `print_cp4_local_report`, not `_verify_orient_gate`.

**How to test.** All four, and paste the actual output:
- `py -3 scripts/cluster/t08_local_remainder.py --help` — 12 cells and 5 modes appear in `choices`,
  and the two new flags are listed.
- A **dry** import check: `py -3 -c "import sys; sys.path.insert(0,'scripts/cluster'); import t08_local_remainder as m; print(len(m.LOCAL_CELLS), m.ALL_MODES); print(sorted(set(m.LOCAL_CELLS) - set(m.CELL_CONFIGS)), sorted(set(m.LOCAL_CELLS) - set(m.CITY_OF)))"`
  → must print `12`, the five modes, and **two empty lists** (every cell has both a config and a
  city).
- Assert the seven pre-existing `CELL_CONFIGS` entries are unchanged: `git diff` on the file must
  show additions only in that dict, no modifications to the LA/Austin lines.
- A **single-building smoke run** proving the fifth mode and a new cell both work end to end:
  `--cells nyc_centre --modes layout_assign --n-ep-workers 2` interrupted after the first few
  buildings is *not* acceptable; instead run the smallest available cell/mode combination to
  completion **only if it finishes inside 20 minutes** — otherwise state plainly that you did not
  run it and why. **Do not start a fleet-scale run from this task.**

---

### C02 — E02: the five-mode, twelve-cell fleet pass *(the overnight run)*

**What to do.** Run the full pass with the extended runner and the pinned settings in §3.

**Why.** It closes **three** register items at once — the only measurement in this project with that
leverage:

| Item | What the pass gives it |
|---|---|
| **OPEN-01** | a verified, multiplier-aware denominator for every building, replacing a 6-building local sample |
| **OPEN-02** | the `eplusout.eio` that has never existed for any fleet building |
| **OPEN-28** | all five modes on **one** generation, so a cross-mode delta means the method and not the calendar |

**How.** Exact invocation:

```
py -3 scripts/cluster/t08_local_remainder.py \
    --n-ep-workers 16 \
    --output-csv openubem/outputs/comparisons/e02_five_mode_fleet_eui.csv \
    --work-base <TEMP>/ubem_e02_five_mode
```

(no `--cells` / `--modes` — the defaults are now all twelve and all five). Launch it **detached,
with stdout and stderr tee'd to a log file that survives the session**, and record the log path in
the progress log. Do not poll it more often than every 30 minutes; prefer waiting on artifacts
appearing on disk over watching the process.

**Expected, written down before the run so it cannot be fitted afterwards:** ≈7.3–11.3 h wall-clock
at 16 workers; ≈43 GB worst-case retained disk; 8,160 buildings × 5 modes = **40,800 simulations**;
per the cluster's four T20-generation harvests, a failure rate around **0.1%**, so a few tens of
failures fleet-wide is normal and a few hundred is a defect. `fast_zone`'s worst single building
should cost one worker ≈18–26 min, not hours.

**How to test.** After it exits: row count and `status` breakdown of the output CSV per (cell, mode);
count of `eplusout.eio` files present and non-empty; total retained bytes; and a check that all 12
cells × 5 modes have a `sim_done.txt`. Any (cell, mode) missing one is an incomplete run — say so,
do not average over it.

---

### C03 — OPEN-10: the "90 buildings" figure, settled *(EnergyPlus-free; may run alongside C02)*

**What to do.** Re-derive fleet-wide how many buildings are `fallback_not_expressible` under the
shipped `Zone.Multiplier` mechanism, and how many of those the `ZoneGroup` list-multiplier mechanism
would express exactly.

**Why.** The register records the 90-building figure (66 `MidriseApartment` + 24 `HighriseApartment`)
as **carried, not verified** — it traces to a 7,442-building crosstab in an archived storey-matching
document and *"is not re-derivable without compute."* N11 confirmed from the EnergyPlus schema that
the capability is real, and the register names this pass as **the smallest settling experiment worth
doing once a machine is free.**

**How.** A fleet-wide `compute_band_map()` / `match_storeys()` pass over all twelve cells' Stage-2
outputs. **No EnergyPlus, no IDF simulation** — this is classification and band arithmetic only, so
it is cheap and will not contend meaningfully with C02 for cores. Use the project's own functions;
**do not reimplement the band logic** — a script that reimplements pipeline logic produces
lookalike evidence, which this project has been burned by before. Report per-archetype counts, and
separate the two limits N11 established: the gain applies only to the two apartment archetypes that
already carry a `ZoneGroup`, and `n_real ∈ {1,2}` stays inexpressible under either mechanism.

**How to test.** State whether 90 reproduces. If it does not, give the number that does, per
archetype, and say what the difference is — a changed population, changed code, or a changed
definition. Do not adjust anything to land on 90.

---

### C04 — OPEN-06: the 26 unchecked columns, from C02's own Stage-3 artifacts *(after C02)*

**What to do.** Extend the column-reproducibility sweep from 7 of 33 columns to all 33.

**Why.** N14 and N16 swept the whole fleet and settled `archetype_id` and `data_quality_flag`, but
**26 of the 33 columns were unreachable** because they are Stage-3-or-later outputs that no
no-CPU task could produce. C02 regenerates Stage 3 for every cell and every mode as a side effect —
so those 26 columns become derivable **for free**, from artifacts C02 has already written. This is
the reason C04 is scheduled after C02 rather than as its own run.

**How.** Reuse N16's method and its bucket vocabulary (REPRODUCES / DIFFERS / STAGE-3-OR-LATER /
ABSENT) exactly, so the two sweeps compose into one table instead of two incomparable ones. Carry
N16's seven settled columns forward unchanged; do not re-measure them.

**How to test.** Per-cell bucket counts must sum to 33 for every cell, as N16's did. State the
`n_compared` per cell and confirm the fleet total is 8,160.

---

### C05 — OPEN-35: what the storey disagreement costs in EUI *(after C02)*

**What to do.** Measure the EUI effect of the archetype-vs-geometry storey disagreement on a stated,
defensible sample.

**Why.** OPEN-35 is the **largest unquantified physical defect on the register**: 2,611 of 8,160
buildings (32.00%) reach both fallbacks, every one persisted at `levels = 1.0`, and **1,031 of them
were given an explicitly mid- or high-rise archetype and then built as a single storey**. The
mechanism is verified and the population is counted; **the energy consequence is not measured at
all.**

**How.** Design the comparison so it isolates the one variable, and **state the sample size and
selection rule in numbers** — no silent caps. Note that OPEN-34 established a local subset run is
**not archetype-faithful** (classification depends on batch composition), so any sampling must be
drawn from full-cell results, not re-classified in a small batch. This constraint is not optional;
ignoring it invalidates the measurement.

**How to test.** Report the distribution of the per-building EUI delta, not just a mean. State
plainly whether the effect is large enough to matter to the adopted fleet figure of ~~158.0~~
**157.1 kWh/m²** (pooled: total simulated energy ÷ total simulated floor area; the struck figure was
a count-weighted mean of the 12 cell means, superseded 2026-08-12, OPEN-43).

---

### C06 — OPEN-09: is "cosmetic" true? *(after C02)*

**What to do.** Test the claim that `thermal_mass=True` warmup non-convergence is cosmetic, by
comparing EUI on converged versus non-converged runs of the same buildings.

**Why.** The measured part of OPEN-09 is solid (96/150 = 64% non-converging vs 8/150 = 5.3% control,
same buildings, one variable). The **unmeasured** part is that the word *"cosmetic"* has been
inherited unexamined across five defect-log entries — **it is a claim about accuracy that nobody has
ever tested.** The register states the open item is exactly this, and that it is answerable.

**How.** Same buildings, one variable, as the original control did. Reuse the existing matched
control population rather than drawing a new one, so the result composes with the 96/150 figure.

**How to test.** Give the EUI delta distribution between converged and non-converged runs of the same
buildings. If the delta is negligible, "cosmetic" is earned and should be recorded as *measured*, not
*inherited*; if it is not, five log entries need correcting and that is a finding in its own right.

**Facts verified by the manager 2026-08-06, so the executor does not re-derive them.**
- The item is register **OPEN-09**, `INVESTIGATION_open-items-register.md:1365-1373`. Its summary row
  is `:214`; the lineage cross-reference is `:737`.
- The matched control is **96/150 (64%) non-converging at `thermal_mass=True` against 8/150 (5.3%)
  in the control — same buildings, same code, one variable.** That part is measured and is **not**
  what this task re-does.
- **The open part is (b) only:** the word *"cosmetic"* has been inherited unexamined across **five**
  log entries — **E-LA-14, E-LA-16, E-LA-18, E-LA-19, E-LA-23**. It is a claim about *accuracy* that
  nobody has ever tested. Consequence (a), the ≈299/8,160 ≈ 3.66% fleet projection, is explicitly
  *"a projection, not a measurement"* and is **out of scope** — do not try to settle it here.
- Candidate homes for the control population, **not yet confirmed** — the manager located these but
  did **not** verify which one holds the 150-building set:
  `docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/c01_regression_results.csv`,
  `openubem/outputs/comparisons/r05_c01bis_results.csv`,
  `openubem/outputs/comparisons/r06c_local_results.csv`.
  **Confirming which is the real one is your first step, and `docs_DONE/` is read-only — read from it,
  never write to it.**

**🔴 Mandatory first step, before any simulation: establish and report the cost.**
Find the matched control population and determine whether its runs **still exist on disk** or must be
**re-simulated**. Then **STOP and report** one of:
- **(i) the runs exist** — this is an analysis task, no EnergyPlus needed. Proceed and finish it.
- **(ii) they must be re-run** — report the building count, the mode, and your measured estimate of
  the wall-clock, **and do not start a run larger than 400 simulations without coming back.** For
  calibration, measured on this machine 2026-08-06: `auto` mode costs ≈110 core-seconds per building,
  and 149 buildings in `layout_assign` took 5.5 minutes at 12 workers.
- **(iii) the population cannot be identified** — say so plainly and stop. **"Not measured" is an
  acceptable result; a substitute population quietly drawn to keep busy is not**, because the whole
  value of this task is that it composes with the existing 96/150 figure.

**Constraint carried from OPEN-34, non-negotiable.** A local run on a *subset* of a cell is **not
archetype-faithful** — `_impute_levels()` fills a missing storey count from a group median over
whatever rows are in the batch, so a small batch classifies buildings differently from the fleet. If
you re-simulate, draw from full-cell results or state explicitly that the archetypes are not
fleet-faithful. Ignoring this invalidates the measurement.

**Scheduling note (manager, 2026-08-06).** §5's preamble declares C04–C06 dependent on C02. For C04
and C05 that is a true data dependency. **For C06 it is over-broad** — C06's own `How` says to reuse
the *existing matched control population*, not C02's output. With E02 parked, C06 is therefore
**authorised to proceed independently of C02**, subject to the cost gate above. This is a stated
deviation from §5's preamble, not a silent one.

---

### C07 — Make the E02 runner able to see a fatal *(no CPU; must land before E02 relaunches)*

**What to do.** Fix the fatal-detection test in `scripts/cluster/t08_local_remainder.py` so it
matches what EnergyPlus actually writes, and re-derive the flag over the 2,422 `eplusout.err` files
E02 has already produced.

**Why.** §8 FINDING 2, 2026-08-06. `:430` tests `"** Fatal **"` (one space). Every real fatal in
this run's own output is written `**  Fatal  **` (two spaces): of 2,422 `.err` files, **2 contain a
real fatal and the one-space test matches 0 of 2**. This is E-LA-21, tracked in OPEN-29, and
`t08_local_remainder.py` is a **fifth** occurrence beyond the four N01 named — and the only one that
is generating results *today*. The consequence is bounded and must not be overstated: **the failure
count is correct**, because `status` derives from the process return code and both buildings were
marked failed. What is worthless is the `has_fatal` column and the end-of-run
`Fatal-free: YES` banner (`:471-483`), which would certify a clean run over any number of fatals.
CP-C2 is a completeness-and-failure gate; it cannot be signed on a blind instrument.

**Scope — read this before touching anything.** Fix **`t08_local_remainder.py` only.** The other four
occurrences (`t20_harvest_layout_assign.py:259`, `t08_harvest_results.py:239`,
`t07_harvest_results.py:198`, `t07b_run_auto_refit_local.py:329`) are **out of scope**: they are
historical/cluster harvests, changing them would alter columns in already-published artifacts, and
that is a user decision recorded in OPEN-29, not a side effect of this task. **Do not touch them. Do
not "while I was there" them.**

**How.**
1. Replace the substring test at `:430` with a whitespace-tolerant regular expression —
   `re.search(r"\*\*\s+Fatal\s+\*\*", err)` — so **both** spacings are caught and a future
   EnergyPlus release that changes the padding again cannot silently blind it. Do not narrow it to
   two spaces; that just moves the bug.
2. Change nothing else in the file — not the trim block, not the disk guard, not `_run_one_ep`, not
   the resume logic, not `run_simulations`, not the harvest's other columns.
3. Leave `print_cp4_local_report()`'s cosmetic "7 cells" banner alone (C01 item 7 still applies).

**How to test.** All three, pasting actual output:
- **Fixture regression on the two known real fatals.** `nyc_centre/sim_out_auto/way_266149332` and
  `nyc_centre/sim_out_auto/way_266170765` under `%TEMP%/ubem_e02_five_mode`. The old test must
  return `False` on both and the new test `True` on both. **A before/after is not reportable until
  the "before" is shown to differ from the "after"** — show both.
- **Fleet-wide re-derivation over all 2,422 existing `.err` files**, reporting the count under the
  old test and under the new one. Expected **0 → 2**. If you get any other pair of numbers, STOP and
  report it rather than adjusting anything: it would mean the manager's count was wrong, which is a
  finding in its own right.
- **A negative control:** confirm the new expression does **not** match the two decorative lines that
  contain the word "Fatal" but are not the terminator —
  `************* Fatal error -- final processing.` and
  `************* EnergyPlus Terminated--Fatal Error Detected.` — both of which appear in those same
  files. A test that matches those would over-count. Report the match result for each line
  explicitly.

---

## 6. What is explicitly NOT in this plan

- **OPEN-19 (LA ~+40% hot)** — cannot be tested by any amount of compute today. N12 established
  there is **no climate-zone or code-year switch** in the codebase and LA's HVAC comes from a
  **Buffalo** prototype. It needs code before it needs cycles. Do not attempt it.
- **OPEN-11 (six inverted-geometry buildings)** — its precondition is met (N04 confirmed the six are
  the same six). What remains is a **remediation decision by the user**, not a measurement.
- **Anything on the cluster.** Not one command.
- **Promoting, enabling, or wiring any imputation tier** (OPEN-15/16/17). Those are decisions owed,
  not measurements.

---

## 7. Stop-and-report points

**CP-C1 — after C01, before any long run.** The gate that protects the night. Verify all twelve cells
resolve a config *and* a city, the five modes are selectable, the new flags work, and the existing
seven cell entries are untouched. **A defect here costs the whole night**, which is exactly why it is
a checkpoint and C02 is not launched from C01's dispatch.

**CP-C2 — after C02 exits.** Completeness before conclusions: every (cell, mode) accounted for,
failure rate against the ≈0.1% expectation, `.eio` present, disk within budget. **No downstream
analysis (C04, C05) starts until this checkpoint is signed**, because analysing a partial fleet and
reporting it as the fleet is the failure mode this arc exists to prevent.

**CP-C3 — after C04 + C05.** The measurement checkpoint for the two items C02 unlocks.

---

## 8. Progress log

Format, one entry per completed task, appended by the executor:

```
#### CXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + citation>
- Test status: <actual output, not a summary of it>
- Notes: <auditor-relevant>
```

Director AUDIT entries are appended under the task they audit and are **append-only** — a correction
is struck and dated, never deleted.

#### C01 — Extend the local runner to twelve cells and five modes — completed 2026-08-06
- Artifacts: `scripts/cluster/t08_local_remainder.py` (edited only; no other files touched).
- Deviations: none. All five `How` sub-steps implemented as specified: `LOCAL_CELLS`,
  `CITY_OF`, `CELL_CONFIGS` extended to twelve cells (five new entries copied verbatim from
  `t08_full_sweep.py:58-71` per §4.1); `ALL_MODES` extended with `layout_assign` last; new
  `--output-csv` / `--work-base` CLI flags added, both defaulting to prior behaviour
  (`OUTPUT_CSV` = `t08_local_remainder_eui.csv`, `%TEMP%/ubem_t08_local`), threaded through
  every call site that previously read the module constant / hard-coded path (resume-load
  branch, incremental per-cell CSV write, final CSV write); argparse description, `--cells`
  help, `--modes` help, and module docstring counts updated 7→12 / 4→5. Per item 7 of the
  task, nothing else was touched — `print_cp4_local_report`'s title string still literally
  reads "7 cells" (left alone; the task's item 7 explicitly forbids editing that function).
- Test status (all four, actual output pasted verbatim):

  1. `py -3 scripts/cluster/t08_local_remainder.py --help`:
  ```
  usage: t08_local_remainder.py [-h]
                                [--cells {nyc_centre,nyc_urban,nyc_suburban,nyc_rural,la_centre,la_urban,la_suburban,la_rural,austin_centre,austin_urban,austin_suburban,austin_rural} [{nyc_centre,nyc_urban,nyc_suburban,nyc_rural,la_centre,la_urban,la_suburban,la_rural,austin_centre,austin_urban,austin_suburban,austin_rural} ...]]
                                [--modes {auto,building,floor,fast_zone,layout_assign} [{auto,building,floor,fast_zone,layout_assign} ...]]
                                [--n-jobs N_JOBS] [--n-ep-workers N_EP_WORKERS]
                                [--output-csv OUTPUT_CSV]
                                [--work-base WORK_BASE]

  T08 local remainder: 12 cells x 5 modes on Windows

  options:
    -h, --help            show this help message and exit
    --cells {nyc_centre,nyc_urban,nyc_suburban,nyc_rural,la_centre,la_urban,la_suburban,la_rural,austin_centre,austin_urban,austin_suburban,austin_rural} [{nyc_centre,nyc_urban,nyc_suburban,nyc_rural,la_centre,la_urban,la_suburban,la_rural,austin_centre,austin_urban,austin_suburban,austin_rural} ...]
                          Cells to run (default: all 12 local cells)
    --modes {auto,building,floor,fast_zone,layout_assign} [{auto,building,floor,fast_zone,layout_assign} ...]
                          Modes to run (default: all 5)
    --n-jobs N_JOBS       Step-3 worker processes (default: cpu_count-2)
    --n-ep-workers N_EP_WORKERS
                          EnergyPlus parallel workers (default: cpu_count-2)
    --output-csv OUTPUT_CSV
                          Output CSV path (default: t08_local_remainder_eui.csv)
    --work-base WORK_BASE
                          Work base dir for resumable sim_out trees (default:
                          %TEMP%/ubem_t08_local)
  ```
  Twelve cells and five modes appear in `choices`; both new flags are listed. PASS.

  2. Dry import check —
  `py -3 -c "import sys; sys.path.insert(0,'scripts/cluster'); import t08_local_remainder as m; print(len(m.LOCAL_CELLS), m.ALL_MODES); print(sorted(set(m.LOCAL_CELLS) - set(m.CELL_CONFIGS)), sorted(set(m.LOCAL_CELLS) - set(m.CITY_OF)))"`:
  ```
  12 ['auto', 'building', 'floor', 'fast_zone', 'layout_assign']
  [] []
  ```
  Matches the required `12`, five modes, two empty lists exactly. PASS.

  3. `git diff -- scripts/cluster/t08_local_remainder.py` on the `CELL_CONFIGS` hunk shows only
  five added lines (`nyc_centre`, `nyc_urban`, `nyc_suburban`, `nyc_rural`, `la_centre`) ahead of
  the seven pre-existing lines (`la_urban` through `austin_rural`), which appear as unchanged
  context with no `-`/`+` markers. Same pattern in `LOCAL_CELLS` and `CITY_OF`. No modification
  to any LA/Austin line. PASS.

  4. Single-cell/mode smoke run: **not run.** Reasoning, with numbers, not a guess: the plan's
  own cited source, `SCOPING_five-mode-rerun-cost.md` §1.1, gives `layout_assign`'s only
  same-scale measurement (T20, cluster, current code) as **mean task time 1.8 min, max task time
  119.2 min** per building — a heavy right-tailed distribution — and separately establishes this
  workstation runs **3.2x-4.6x faster per zone** than that cluster core. Scaled down, a single
  unlucky building could still cost **~26-37 min alone** on this machine, which exceeds the
  20-minute budget on its own regardless of how many EnergyPlus workers run in parallel, because
  that one building sits on the critical path. The smallest *new* cell is `nyc_rural`
  (198 buildings, `01_buildings.gpkg` row count verified this session); the smallest cell overall
  is `la_rural` (149 buildings, already in the pre-existing seven). Neither population size
  changes the tail-latency argument. There is no CLI flag to bound the run to fewer buildings
  without editing manifest/fixture logic (out of this task's scope — item 7 forbids touching
  `_run_one_ep`/Step-3), and the plan explicitly disallows treating an interrupted/timed-out
  partial run as valid evidence. Per the plan's own permitted fallback ("otherwise state plainly
  that you did not run it and why"), this task states plainly: not run, because the only
  available timing evidence shows a credible risk of a single-building outlier alone exceeding
  the 20-minute cap, with no way to bound that risk in advance short of running it to completion
  (i.e., what C02 is for).
- Notes: CP-C1 verification (all twelve cells resolve a config *and* a city, five modes
  selectable, new flags work, existing seven entries untouched) is satisfied by tests 1-3 above.
  Test 4 (an actual end-to-end EnergyPlus exercise of the fifth mode) remains unmeasured — flagged
  for the director rather than silently skipped. No EnergyPlus process was started; no compute,
  cluster, or git command was run beyond the four tests listed above.

---

#### AUDIT — CP-C1 / C01 — manager, 2026-08-06

**GREENLIT.** Audited by independent re-derivation from the file and from a live run, not by reading
the report back.

**Diff, checked line by line** (`git diff scripts/cluster/t08_local_remainder.py`, 39 insertions /
21 deletions). The five new `CELL_CONFIGS` entries are byte-identical to `t08_full_sweep.py:58-71`;
**the seven pre-existing LA/Austin entries appear in the diff context only, unmodified** — the
requirement in §5 C01 step 3. `ALL_MODES` carries `layout_assign` **last**, as §3 pinned. Both new
flags are threaded through every former `OUTPUT_CSV` / hard-coded work-base call site; the single
remaining `OUTPUT_CSV` reference inside `main()` is the argparse `default=`, which is correct.
**The trim block, the disk guard, `_run_one_ep`, the harvest and `_verify_orient_gate` are untouched**
— confirmed by re-reading `RETAIN_FILENAMES` and `DISK_FLOOR_BYTES` from the imported module
(`('eplusout.eio', 'eplusout.sql', 'eplusout.err', 'eplusout.end', 'task.rc')`, 50.0 GB).

**Own re-derivation of the config integrity test:** 12 cells, 5 modes, `LOCAL_CELLS - CELL_CONFIGS`
empty, `LOCAL_CELLS - CITY_OF` empty, and `set(CITY_OF.values()) == {AUS, LA, NYC}` — the exact three
labels §4.2 requires for the published joins to hold.

🔴 **The one gap the executor left, and how the director closed it.** C01's test 4 (an end-to-end
run) was **not** performed. The executor's stated reason is sound and is accepted: `layout_assign`'s
only same-scale measurement is heavy-tailed (T20 mean 1.8 min, max 119.2 min), so no single-building
bound can be guaranteed under a 20-minute cap. **But that argument is about `layout_assign`, not
about the new cells** — and the new cells were the larger of the two risks, since a night can be lost
to an EPW that will not resolve for `NY`. **The director therefore ran the bounded smoke the
executor's reasoning did not cover**, in the session scratchpad, on a *new* cell in the cheapest mode:

```
--cells nyc_rural --modes building --n-ep-workers 16
```

| check | result |
|---|---|
| rows / status | **198 / 198 `success`**, zero non-success |
| `has_fatal` | **0** |
| `city` label | **`NYC`** — proves the `CITY_OF` fix, not the silent cell-name fallback (§4.2) |
| `eplusout.eio` retained | **198** |
| `*.eso` surviving | **0** — the trim block still fires |
| retained disk | 66 MB / 198 buildings = **0.33 MB per building** in `building` mode |
| median 9-end-use EUI | 139.92 kWh/m² — physically plausible, not asserted against a target |

**A new cell resolves its EPW, runs Steps 2→3→4, harvests, labels its city correctly and trims.**
That is the risk CP-C1 exists to retire. `layout_assign` remains unexercised locally end-to-end; it
is scheduled **last within every cell** precisely so that a failure there costs the least, and
§4.3's evidence (T17–T20 drive the identical `run_step3_mode` path with `_MODE = "layout_assign"`)
stands as the reason to expect it to hold.

**One cosmetic mislabel recorded, deliberately not fixed.** `print_cp4_local_report()`'s banner
string still reads *"7 cells"*. C01 step 7 forbade touching that function, so the executor correctly
left it. **Anyone reading E02's end-of-run report must not take that header as evidence of a 7-cell
run** — the per-cell tables beneath it are generated from the data and will show all twelve.

#### C02 — E02, the five-mode twelve-cell fleet pass — LAUNCHED 2026-08-06 by the director

- Invocation: `py -3 -u scripts/cluster/t08_local_remainder.py --n-ep-workers 16
  --output-csv openubem/outputs/comparisons/e02_five_mode_fleet_eui.csv
  --work-base %TEMP%/ubem_e02_five_mode`
- Log (survives the session): `%TEMP%/ubem_e02_five_mode/e02_run.log`
- ~~Launched detached.~~ **Struck 2026-08-06 02:52 — this was not true.** It was launched as a
  *session-bound* background task and died with the session. See the INCIDENT entry at the end of
  this log for what happened, what it cost, and the relaunch that actually is detached.
- **Expectations were written into §5 C02 before the run started** and are not to
  be edited afterwards: ≈7.3–11.3 h, 40,800 simulations, ≈0.1% failure rate, ≈43 GB worst-case disk.
- Result and CP-C2 verdict to be appended here on exit.

---

#### C03 — OPEN-10: the "90 buildings" figure, settled — completed 2026-08-06

- Artifacts:
  - `openubem/outputs/comparisons/open10_band_expressibility_fleet.csv` (7,442 rows, one per
    fleet building with an `ARCHETYPE_IDF_MAP` entry).
  - `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-10_band-expressibility-fleet.md`.
  - Throwaway scripts in session scratchpad only (`c03_probe.py`, `c03_band_expressibility.py`,
    `c03_band_structure.py`) — not committed under `docs/`, as required.
- Deviations: none from the task's `How`. Used the project's own `layout_assigner.compute_band_map()`
  / `layout_assigner.match_storeys()` unmodified for the shipped-mechanism classification; for N11's
  proposed `ZoneGroup`-overwrite mechanism, called the same unmodified `match_storeys()` a second
  time per building with a counterfactual `band_map` (only the target band's `storeys_in_band` field
  forced to `1`, modelling "overwrite" instead of "compound") — no band-matching or residual logic
  was reimplemented. Source population was `05_results.gpkg` (all twelve cells) rather than
  `01_buildings.gpkg`, because the latter (true Stage-1) carries no `archetype_id` column at all and
  no standalone Stage-2 file is persisted anywhere in the `phaseE` results tree; `05_results.gpkg`'s
  `archetype_id`/`levels`/`height_m` columns are Stage-2 values passed through unchanged, not
  Stage-5 re-derivations — cited and justified in the report §6. EnergyPlus-free throughout: no
  simulation was run, only IDF text parsing (16 baseline files) and pure-Python function calls.
  Single-threaded, no multiprocessing — negligible CPU/RAM footprint alongside the concurrently
  running C02.
- Test status (actual numbers, not a summary):
  - Fleet loaded: 8,160 buildings / 12 cells (`OK`, matches expected exactly).
  - `ARCHETYPE_IDF_MAP` join: 7,442 mapped / 718 no-map (650 `OpenUBEMUnknown` + 68 `Courthouse`) —
    **exact match** to the register's carried 7,442/718 split.
  - Shipped-mechanism status counts, fleet-wide (7,442 total): `fallback_shorter` 3,724,
    `fallback_not_expressible` 1,976, `identity` 1,226, `applied` 516.
  - `fallback_not_expressible` by archetype: `SmallOffice` 1,580, `LargeOffice` 175,
    `TallBuilding` 88, `MidriseApartment` **66**, `SuperTallBuilding` 24, `HighriseApartment` **24**,
    `QuickServiceRestaurant` 7, `SecondarySchool` 7, `FullServiceRestaurant` 4, `Hospital` 1
    (sums to 1,976 exactly).
  - **66 + 24 = 90 — the carried figure reproduces exactly, no adjustment made.**
  - Proposed `ZoneGroup`-overwrite mechanism applied to those 90: **66/66 `MidriseApartment` and
    24/24 `HighriseApartment` flip to `applied`** — 100% flip rate, matching N11's claim.
  - `n_real ∈ {1,2}` (`fallback_shorter`) counts are **identical** between shipped and proposed for
    both archetypes (2,273 and 3) — directly demonstrates N11's Limit 1 holds fleet-wide, not just
    by assertion.
  - 0 buildings skipped for a missing baseline file despite having a map entry; 16 distinct baseline
    IDF files loaded for the 16 archetype IDs actually present in the fleet.
- Notes for the auditor: population, code, and definition are all **unchanged** from the source
  crosstab (`docs_DONE/.../PLAN_storey-matching_REMAINder.md:1302-1315`) — this is a clean
  reproduction, not a reconciliation. One clarification surfaced (not a contradiction): N11's
  illustrative list of 7 "structural" archetypes (`Hospital, LargeOffice, TallBuilding,
  SuperTallBuilding, College, LargeHotel, Laboratory`) undercounts the real fleet-driven picture —
  3 of those 7 (`College`, `LargeHotel`, `Laboratory`) have **zero** buildings in the fleet, while 4
  archetypes not on that list (`SmallOffice`, `QuickServiceRestaurant`, `SecondarySchool`,
  `FullServiceRestaurant`) share the same `n_proto == 2` structural condition and dominate the
  count — `SmallOffice` alone is 1,580 of the 1,976 total, 16x the apartment archetypes' combined 90.
  Practical read: the `ZoneGroup` gain (if built) would resolve only 4.6% of the fleet's
  `fallback_not_expressible` population; 95.4% is untouched by it. Full detail and the by-archetype
  `n_proto`/`storeys_in_band` table are in the report §5. No silent caps: all 8,160 buildings read,
  all 7,442 mapped buildings classified, nothing sampled or truncated.

---

#### NOTE — a risk to C02's stated wall-clock, recorded 2026-08-06 *while the run is in flight, before the answer is known*

`SCOPING_five-mode-rerun-cost.md`'s 540-cluster-CPU-hour figure was read from `sacct` over the T08 /
T17–T20 **sbatch arrays**, and in the cluster pattern (`t08_full_sweep.py`, `t*_full_sweep.py`)
**Steps 1–3 run locally on the workstation before submission** — only Step 4 (EnergyPlus) is inside
the job the accounting measured. The local runner does **all** of Steps 2→3→4 in one process.

**Therefore the ≈7.3–11.3 h expectation covers EnergyPlus and not Step-3 IDF generation, which is
additive and unbudgeted.** First live data point: `nyc_centre/auto`, n=738, `n_jobs=18` — Step 3 was
still running >20 min after the cell started. There are **60** (cell, mode) Step-3 passes in this run.

This is recorded **now, with the outcome unknown**, so that if C02 overruns its stated window the
overrun is explained by a cause identified in advance rather than rationalised afterwards. **The
prediction in §5 C02 stands unedited** — it is not being revised to fit. If the run does overrun,
the correct conclusion is that the scoping doc's local projection omitted Step 3, which is a
correction the scoping doc will need, not a failure of the run.

**Mitigating facts, stated plainly:** the pass is resumable per (cell, mode) via `sim_done.txt`, so an
overrun costs wall-clock and not work; and nothing downstream is gated on speed, only on completeness
(CP-C2).

#### AUDIT — C03 (OPEN-10) — manager, 2026-08-06

**GREENLIT.** Re-derived from `openubem/outputs/comparisons/open10_band_expressibility_fleet.csv`
(7,442 rows × 11 columns, 12 cells), never from the report.

**The carried figure reproduces exactly — 66 `MidriseApartment` + 24 `HighriseApartment` = 90**, and
all 90 move `fallback_not_expressible → applied` under the proposed mechanism. **That is worth
pausing on.** Carried numbers in this arc have a poor record: OPEN-12's 36.4% / 19.2% did not
reproduce, OPEN-28's central framing was wrong for the published figure, N14's "same 9 rows" claim was
wrong. **This one held, unadjusted**, and the population it sits in (7,442 evaluated, 8,160 − 718
unmapped) is the same 7,442 the register's own OPEN-01 crosstab uses — independent corroboration the
executor did not claim.

**Both of N11's limits confirmed on the fleet, not asserted:**
1. `status_proposed_zonegroup` is populated for **2,850** rows and those rows are **exactly** the two
   apartment archetypes — the proposal is correctly scoped to archetypes that actually carry a
   `ZoneGroup`, and left blank elsewhere rather than silently extended.
2. Apartment `fallback_shorter` = **2,276**, every one with `num_floors ∈ {1, 2}`, and **not one
   changes** under the proposal. `n_real` of 1 and 2 stays inexpressible, exactly as N11 said.

**Transitions, complete:** of the 2,850 adjudicated rows the **only** change is
`fallback_not_expressible → applied`, ×90. There is no second transition and no regression.

⚠️ **A correction to my own first pass, recorded because the artifact is the record.** My initial
`status_shipped != status_proposed_zonegroup` count returned **4,682 changed rows across 16
archetypes**, which would have contradicted limit 1 outright. It was a **NaN artifact** — the 4,592
non-apartment rows carry a blank proposed verdict, and `NaN != NaN` is `True` in pandas. Re-derived on
non-null rows only, the answer is 90. **The executor was right and my first number was wrong**; the
blank column is correct design, not missing data.

🔴 **The side finding is the operationally important part, and it sharpens N11 rather than repeating
it.** Fleet-wide `fallback_not_expressible` is **1,976 across 10 archetypes** — `SmallOffice` **1,580**,
`LargeOffice` 175, `TallBuilding` 88, `SuperTallBuilding` 24, the rest single digits (director-verified
from the CSV). **So the remedy OPEN-10 proposes reaches 90 of 1,976 buildings — 4.6%.** N11 said the
"restore exact expressibility" framing was *overstated*; C03 puts the number on it. Note also that
N11's illustrative list of seven structural archetypes does not match the fleet: three of the seven
have **zero** buildings, while archetypes it never named dominate the count.

**Method accepted, with its limit stated.** The proposal was modelled by feeding the project's own
unmodified `match_storeys()` a counterfactual `band_map` with the target band's baked-in list
multiplier forced to 1 — **it models the edit rather than implementing it**, which is the right call
for a measurement-only task (remediation is forbidden inside one) but means the 100% flip rate is a
property of the band arithmetic, not of a built-and-simulated `ZoneGroup`. Whoever writes the
execution plan must not read this as "already verified in EnergyPlus."

**Disposition: OPEN-10's evidence mark stands at ✅, and the "carried, not verified" caveat is
discharged.** What remains is a decision — R04 is closed at option (a), so acting on this is a
deliberate reopening, and it now carries a measured benefit of 4.6% of the inexpressible population
rather than an implied "all of it."

---

#### INCIDENT — C02 was killed by the session, not by a defect — director, 2026-08-06 02:52

**What happened.** The run stopped at **02:1x** after roughly 20 minutes of simulation. The cause was
not EnergyPlus, not disk, not the runner: the director launched it with the **session-bound**
background-command facility rather than as an independent OS process, so when the session compacted,
the harness stopped the command and every EnergyPlus child with it. The plan itself had already said
to launch it **detached** (§5 C02, "Launch it detached"); the instruction was written and then not
followed. Recording it here because a silent relaunch would leave a two-hour hole in the timeline
that a later reader would misread as a slow first cell.

**State at the kill, measured not assumed:**

| Quantity | Value |
|---|---|
| EnergyPlus processes alive afterwards | **0** |
| `eplusout.eio` written | **561** of `nyc_centre/auto`'s 738 |
| Log | 861 lines, **no `DISK GUARD`, no `Traceback`, no fatal** |
| Cells/modes completed | **none** — no `sim_done.txt`, so no pair was marked done |
| Output CSV | not yet written (first write is after the first *cell*, not the first mode) |

**What it cost.** Less than it looks. Resume is **per building**, not per pair —
`t08_local_remainder.py:268` builds its pending list as
`[p for p in idfs if not (sim_out / p.stem / "eplusout.end").exists()]`, and `.end` is in
`RETAIN_FILENAMES`, so the trim step does not destroy the resume marker. The 561 finished
simulations are skipped on restart. What *is* redone is Step 2 (1.3 s) and **Step 3 IDF generation
for `nyc_centre/auto`**, which the main loop at `:670` re-runs unconditionally — the same Step-3 cost
the NOTE above already flagged as unbudgeted. Net loss ≈ one Step-3 pass plus ~35 minutes of
wall-clock.

**The relaunch.** Re-issued 02:52:17 through `Win32_Process.Create` (WMI), so the process is
parented by the WMI provider host and sits in no job object belonging to this session. A session
compaction, restart, or exit can no longer take it down.

- New PID: **1048** (`cmd` wrapper); 20 python workers confirmed alive at 02:52.
- New log: `%TEMP%/ubem_e02_five_mode/e02_run_2.log`. The first log is **kept**, not appended to, so
  the pre-kill evidence stays readable.
- Same `--output-csv` and same `--work-base` as the original invocation — this is a resume of the
  same run, not a second run.

**Standing caveat, unchanged.** The §5 C02 prediction of ≈7.3–11.3 h is **still not edited**, and the
clock for judging it should be read as starting at the *original* 01:54 launch. The kill is a
director error, not evidence about the estimate; the two must not be allowed to launder each other.

**Lesson worth carrying past this arc.** On this machine, "background" in the tooling sense is not
"detached" in the OS sense. Any run expected to outlive a single exchange must be created as an
independent OS process, and the launch record must state *which mechanism* was used rather than
asserting the property.

---

#### AUDIT — C02 halted by `MemoryError`; CP-C2 **NOT** signed — director, 2026-08-06 08:30

**The run is dead and was dead for 2 h 45 min before this session opened it.** Every number below is
re-derived from the raw log, the work tree and the `.err` files — not from any report.

**What happened.** `e02_run_2.log` ends in a `MemoryError` raised inside `_run_one_ep`
(`t08_local_remainder.py:219`, `shutil.copy` of the IDF into the run directory), propagated out of
`run_simulations` (`:310`) and out of `main()` (`:677`). **Last write 05:47:01.** Not a pipeline
defect, not disk (655 GB free at inspection), not the disk guard (no `DISK GUARD` line anywhere in
either log). It is real memory exhaustion: `Win32_PageFileUsage` shows **PeakUsage 53,214 MB against
an AllocatedBaseSize of 71,989 MB** on a 63.5 GB machine.

**Why `fast_zone` and not the other three.** It is the largest-model mode by a wide margin — total
Step-3 IDF bytes for `nyc_centre`: `fast_zone` **751.3 MB** (max single IDF 14.26 MB) against `auto`
400.8 MB (4.61 MB), `floor` 244.6 MB (3.08 MB), `building` 59.4 MB (0.39 MB). Sixteen workers each
holding a model of that size exhausted commit. **`auto`, `building` and `floor` all completed at 16
workers with no memory pressure**, so the worker count is not wrong in general — it is wrong for
`fast_zone`.

**State at the halt, measured:**

| Quantity | Value |
|---|---|
| (cell, mode) pairs with `sim_done.txt` | **3 of 60** — `nyc_centre` `auto`, `building`, `floor` |
| Completed simulations with `eplusout.end` | 738 + 738 + 738 + **59** (`fast_zone`, of 738) |
| `eplusout.err` files on disk | **2,422** |
| Output CSV `e02_five_mode_fleet_eui.csv` | **does not exist** — first write is after a whole *cell* (`:693-698`), and the crash came mid-cell-1 |
| Retained disk, `nyc_centre` | 0.41 + 0.20 + 0.30 + 0.08 = **0.99 GB** for 2,273 simulations |

**Failure rate: the §5 prediction HELD.** Two real fatals in 2,422 simulations = **0.083%**, against
the ≈0.1% written into §5 C02 before the run. Both are `nyc_centre/auto`
(`way_266149332`, `way_266170765`), and both are visible in the harvest as `736/738 success`.

---

🔴 **FINDING 1 — a silent data-loss trap in the resume path. This is the most important thing in this
entry, and it would have destroyed the fleet result quietly.**

`main()` computes `modes_needed = [m for m in modes if not is_done(cell, m, work_base)]` (`:630`).
A mode already marked done is **skipped entirely — Step 3, Step 4 and the harvest**. Its rows reach
the output CSV by exactly one route: the `if not modes_needed` branch (`:631-640`), which fires only
when **every** requested mode of that cell is done, and which recovers the rows by **reading them back
out of the output CSV**.

**So a (cell, mode) that is marked done but is not already in the output CSV is unrecoverable by
restart, and vanishes with no error.** That is precisely the current state: `nyc_centre`'s three
finished modes are marked done, and the CSV was never written. **A naive relaunch would have produced
a "fleet" CSV missing 2,214 buildings — including `auto`, the mode OPEN-28's published comparison
depends on — and nothing in the run would have said so.**

**Mandatory protocol for every restart from here on:** before relaunching, delete the `sim_done.txt`
of any (cell, mode) whose rows are not already in the output CSV. The cost is near zero — Step 4
resume is **per building** via `eplusout.end` (`:268`), and `.end` is in `RETAIN_FILENAMES`, so the
simulations are skipped and only Step 3 (minutes) and the harvest re-run. **This has not been done
yet; it must be done as part of whichever relaunch is authorised.**

---

🔴 **FINDING 2 — E-LA-21 is live in the E02 runner itself. A fifth script, not among the four N01
named.**

`t08_local_remainder.py:430` is `has_fatal = "** Fatal **" in err` — the **one-space** form. Checked
against the raw artifacts this run produced, not against the register: of the 2,422 `eplusout.err`
files, **2 contain a real fatal and both write it two-space**, `**  Fatal  ** Program terminates due
to preceding condition.` **The one-space test matches 0 of 2.**

Consequences, stated precisely so nobody over- or under-reads them:
- **The failure *count* is not affected.** `status` is derived from the process return code and
  correctly marked both buildings failed; the harvest reported 736/738.
- **The `has_fatal` column and the end-of-run `Fatal-free: YES` banner (`:471-483`) are worthless**,
  and would report a clean run over any number of real fatals.
- **The C01 audit's smoke-test row `has_fatal | 0` was therefore not evidence of anything.** Recorded
  here rather than by editing that entry, which is frozen.

N01 found the one-space test in `t20_harvest_layout_assign.py:259`, `t08_harvest_results.py:239`,
`t07_harvest_results.py:198`, `t07b_run_auto_refit_local.py:329`. **`t08_local_remainder.py:430` is a
fifth**, and it is the one generating results today. Not fixed — it is pipeline code and needs its own
written task.

---

🔴 **FINDING 3 — the §5 C02 wall-clock prediction is wrong by roughly an order of magnitude, and the
cause identified in advance was not the cause.**

Measured, from the run's own `done in` lines and file timestamps, for `nyc_centre` (738 buildings,
**9.04%** of the 8,160 fleet):

| mode | measured, `nyc_centre` | scaled ×11.06 to the fleet |
|---|---|---|
| `auto` | ≈85 min *(01:54:06 → 03:22:44, includes a ~90 s restart gap)* | ≈**15.7 h** |
| `building` | **12.7 min** *(logged)* | ≈**2.3 h** |
| `floor` | **41.7 min** *(logged)* | ≈**7.7 h** |
| `fast_zone` | 59 of 738 in 72 min → ≈15 h extrapolated | ≈**2–7 days** |
| `layout_assign` | — | see the C02-P1 probe below |

The three completed modes alone extrapolate to **≈26 h**, against §5 C02's **≈7.3–11.3 h for all
five**. §5 remains **unedited**, as it must.

**The cause recorded in advance — unbudgeted Step-3 IDF generation — is NOT what happened, and the
NOTE above is corrected by measurement.** From the logs: Step 2 is **2.5–2.7 s** per cell, and Step 3
is **7.9 s** for 149 buildings (`la_rural`) and a few minutes for 738. The overrun is EnergyPlus
itself being slower per building than the cluster-derived scaling assumed, and it is dominated by
`fast_zone`. **The NOTE's "Step 3 was still running >20 min after the cell started" is not supported
by the artifacts** — `step3_auto`'s last IDF is timestamped 01:54:03 against a 01:49:53 launch, ≈4 min.

**Scaling caveat, stated rather than hidden.** The fleet column scales by building count only.
`nyc_centre` is the **4th**-largest of the twelve cells (738; `nyc_urban` 1,548, `la_suburban` 1,333,
`nyc_suburban` 1,297 are larger), so the extrapolation is not inflated by having picked a big cell —
but Manhattan buildings are plausibly above fleet-average complexity, so treat these as upper-leaning
estimates, not measurements.

---

⚠️ **CORRECTION to the INCIDENT entry above (append-only; that entry is not edited).**

The INCIDENT entry states the first kill happened at **"02:1x"**, cost **"~35 minutes"** of
wall-clock, and left **561** `.eio` written. All three are wrong:

| Claim | Evidence at HEAD |
|---|---|
| kill at 02:1x | `e02_run.log` **LastWriteTime 02:50:45**, and it logs **545** completions |
| ~35 min hole | relaunch log created **02:52:18** → the hole is **≈90 seconds** |
| 561 `.eio` at kill | 545 completions logged; the 10-min completion histogram runs **continuously** through 02:20, 02:30, 02:40 (92 / 89 / 113 buildings) — the window the entry calls dead |

**The director error was real and the lesson stands unchanged**, but its cost was ~90 seconds, not
~35 minutes, and the timeline must not be read as a 35-minute hole. **Consequence for judging §5:**
the ≈85 min `auto` figure is very nearly a clean measurement, which makes FINDING 3 stronger, not
weaker.

---

#### C02-P1 — probe: is `layout_assign` runnable locally, and what does it cost? — completed 2026-08-06

Launched by the director to close the one gap CP-C1 left open: C01's test 4 was never run, so
`layout_assign` had **never been exercised locally end to end**, and it is the mode **OPEN-01 and
OPEN-28 actually need**. Smallest cell chosen so the answer is cheap.

- Invocation: `--cells la_rural --modes layout_assign --n-ep-workers 12`, **shared** work base
  `%TEMP%/ubem_e02_five_mode` (so the simulations count toward E02), **separate** output CSV in the
  session scratchpad (so E02's CSV cannot be clobbered).
- Launched **detached via `Win32_Process.Create` (WMI)**, PID 28424 — mechanism stated, not asserted,
  per the INCIDENT lesson.
- Log: `%TEMP%/ubem_e02_five_mode/probe_layout_assign_la_rural.log`

**Result: `layout_assign` runs, and it is not the expensive mode.**

| | |
|---|---|
| Step 2 | 2.5 s, 149 buildings |
| Step 3 | **149/149 IDFs in 7.9 s** |
| Step 4 | **149/149 success in 319.6 s** at 12 workers — zero failures |
| Whole mode | **5.5 min** |
| Per building | 2.15 s wall / **25.7 core-seconds** |

One benign message, not an error: `No baseline available for archetype_id='Courthouse'
(osm_id=way/472960965); returning no_baseline metadata for downstream fallback.` — the documented
`Courthouse` no-map path (`Courthouse` is 68 of the fleet's 718 unmapped buildings, per C03).

**What this does and does not license.** It **does** retire the "`layout_assign` has never run
locally" risk, and it shows `layout_assign` is nowhere near `fast_zone`'s cost. It does **not** give a
fleet cost: `la_rural` is the **smallest and simplest** cell (149 buildings), and cross-cell
per-building costs are not comparable — `nyc_centre` `auto` runs ≈110 core-seconds per building
against this 25.7. **Do not scale 5.5 min × 55 into a fleet estimate**; the honest statement is that
`layout_assign` is affordable and unblocked, with its fleet cost still unmeasured.

---

#### DECISION OWED — CP-C2 scope ruling, put to the user 2026-08-06 and **parked at their instruction**

The user was shown FINDING 3 and asked which scope to relaunch. **They elected to park the ruling and
preserve the task rather than decide immediately.** Nothing is cancelled; E02 is **halted, not
abandoned**, and no relaunch is authorised until the ruling is given.

**State to hand to whoever takes the ruling:**
- 3 of 60 pairs complete, on disk, **not yet in any CSV** — and subject to FINDING 1's trap.
- `layout_assign` proven runnable and cheap (C02-P1); `fast_zone` proven to be the cost driver *and*
  the memory hazard.
- The options as put: (a) drop `fast_zone`, run the other four ≈26 h + `layout_assign`; (b) all five,
  ~a week, `fast_zone` at reduced workers; (c) `auto` + `layout_assign` only, ≈16 h; (d) four now,
  `fast_zone` queued separately afterwards.
- **Every option requires FINDING 1's marker cleanup first.**

---

#### C07 — Make the E02 runner able to see a fatal — completed 2026-08-06

- Artifacts: `scripts/cluster/t08_local_remainder.py` (edited only — `import re` added to the
  stdlib import block, and the `has_fatal` assignment at the former `:430` line changed from
  `"** Fatal **" in err` to `re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None`). No other file
  touched. The four out-of-scope occurrences named in the task
  (`t20_harvest_layout_assign.py:259`, `t08_harvest_results.py:239`, `t07_harvest_results.py:198`,
  `t07b_run_auto_refit_local.py:329`) were not opened, not grepped-into, not modified — confirmed
  by `git status --short`, which shows only `t08_local_remainder.py` modified among tracked code
  files after this task.
- Deviations: none from the task's `How`. Item 1's replacement is byte-identical to the pattern
  the task specifies. Item 2 (change nothing else in the file) held — the trim block, disk guard,
  `_run_one_ep`, resume logic, and `run_simulations` are untouched; the only other lines in the
  diff are C01's already-uncommitted 12-cell/5-mode extension from earlier in this session, not new
  changes from this task (verified by re-reading the full `git diff` and isolating the two lines
  this task added: the `import re` line and the `has_fatal` line). Item 3 (leave
  `print_cp4_local_report()`'s cosmetic banner alone) held — that function was not opened.
- Test status (all three, actual output pasted verbatim, run via a throwaway script in the session
  scratchpad, `c07_verify.py`, never committed under `docs/`):

  **1. Fixture regression on the two known real fatals**
  (`%TEMP%/ubem_e02_five_mode/nyc_centre/sim_out_auto/way_266149332` and `.../way_266170765`):
  ```
  way_266149332: old_test=False  new_test=True
      raw line: '   **  Fatal  ** Program terminates due to preceding condition.'
      raw line: '   ************* Fatal error -- final processing.  Program exited before simulations began.  See previous error messages.'
      raw line: '   ************* EnergyPlus Terminated--Fatal Error Detected. 162 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  2.31sec'
  way_266170765: old_test=False  new_test=True
      raw line: '   **  Fatal  ** Program terminates due to preceding condition.'
      raw line: '   ************* Fatal error -- final processing.  Program exited before simulations began.  See previous error messages.'
      raw line: '   ************* EnergyPlus Terminated--Fatal Error Detected. 246 Warning; 1 Severe Errors; Elapsed Time=00hr 00min 12.55sec'
  ```
  Old test returns `False` on both; new test returns `True` on both — the before differs from the
  after, as the task requires. PASS.

  **2. Fleet-wide re-derivation over all existing `.err` files** under
  `%TEMP%/ubem_e02_five_mode` (recursive glob, no sampling, no cap):
  ```
  total .err files found: 2422
  old test match count: 0
  new test match count: 2
  new matches: ['...nyc_centre\\sim_out_auto\\way_266149332\\eplusout.err',
                '...nyc_centre\\sim_out_auto\\way_266170765\\eplusout.err']
  ```
  2,422 files read, matching the manager's cited count exactly. Old→new is **0 → 2**, exactly the
  expected pair — no deviation to report, no adjustment made. PASS.

  **3. Negative control** on the two decorative lines that contain "Fatal" but are not the
  terminator:
  ```
  new_test('************* Fatal error -- final processing.') = False
  new_test('************* EnergyPlus Terminated--Fatal Error Detected.') = False
  ```
  Both `False` — the new regex does not over-match. Confirmed both decorative lines are actually
  present in the same two `.err` files (not merely absent from the corpus, which would make the
  control vacuous):
  ```
  way_266149332: '************* Fatal error -- final processing.' present=True
  way_266149332: '************* EnergyPlus Terminated--Fatal Error Detected.' present=True
  way_266170765: '************* Fatal error -- final processing.' present=True
  way_266170765: '************* EnergyPlus Terminated--Fatal Error Detected.' present=True
  ```
  PASS.

  Supplementary check: re-imported the live module (`import t08_local_remainder as m`) and read
  back `inspect.getsource(m.harvest_cell_mode)` to confirm the on-disk source the module actually
  executes carries the new regex line, not a stale bytecode cache — confirmed
  `has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None` is present verbatim.
- Notes: `has_fatal` is a harvest-time-only field — it is computed by `harvest_cell_mode()` when
  rows are written to a CSV, not stored anywhere persistent, so this fix has no effect on rows
  already harvested into `e02_five_mode_fleet_eui.csv` (which does not yet exist per the C02 AUDIT
  entry above) and will apply automatically the next time E02 (or C02-P1's probe) re-harvests any
  cell. `print_cp4_local_report()`'s end-of-run `Fatal-free: YES` banner reads from the same
  `has_fatal` column, so it is corrected as a side effect of this fix without that function itself
  being touched. No CPU, cluster, or git command was run beyond the checks above; no `.py` file was
  added under `docs/`.

---

#### AUDIT — C07 — manager, 2026-08-06

**GREENLIT.** Re-derived independently from the 2,422 `.err` files and from `git diff`, not by
reading the report back.

**Own re-derivation, run in the manager session over the same population:**

| | |
|---|---|
| `eplusout.err` files found | **2,422** |
| Old one-space test `"** Fatal **"` | **0** |
| New regex `\*\*\s+Fatal\s+\*\*` | **2** — `way_266149332`, `way_266170765` |
| Negative control: `************* Fatal error -- final processing.` | **no match** ✅ |
| Negative control: `************* EnergyPlus Terminated--Fatal Error Detected.` | **no match** ✅ |

The before/after requirement is satisfied on evidence, not by assertion: the "before" was shown to
return 0 where the "after" returns 2, on the same files. **The negative control is non-vacuous** —
both decorative lines are physically present in those same two files, so a sloppier expression would
have over-counted, and this one does not.

**Scope fence held.** `git diff --stat` shows exactly one script touched,
`scripts/cluster/t08_local_remainder.py`. The four out-of-scope occurrences
(`t20_harvest_layout_assign.py`, `t08_harvest_results.py`, `t07_harvest_results.py`,
`t07b_run_auto_refit_local.py`) are **untouched**, as the task required — they remain a user decision
under OPEN-29, not a side effect of this fix.

**Change reviewed line by line.** Two lines: `import re` in the stdlib block, and the predicate at
`harvest_cell_mode()`. The rest of the diff against HEAD is **C01's** work, already audited and
greenlit at CP-C1 — it appears here only because the working tree is uncommitted. The trim block,
disk guard, `_run_one_ep`, `run_simulations`, the resume logic and every other harvest column are
unmodified.

**The executor's own note is correct and is the operationally useful part:** `has_fatal` is computed
at harvest time and is not persisted anywhere, so nothing already on disk is stale — the fix applies
automatically to every future harvest, including any re-harvest of the three `nyc_centre` pairs that
FINDING 1's protocol will force. `print_cp4_local_report()`'s `Fatal-free:` banner reads the same
column and is therefore corrected without that function being edited, which is why the C01 freeze on
it did not need to be broken.

**What this does NOT do, stated so nobody over-reads it.** It does not change any published number,
it does not change the failure *count* (which was always right, via the return code), and it does not
discharge E-LA-21 — four other scripts still carry the bug and every historical `has_fatal` column in
the project remains untrustworthy. **The register's standing rule "never use the `has_fatal` column"
stays in force for all pre-2026-08-06 artifacts.** What it does do is make CP-C2 signable on a
working instrument.

---

#### 🔴 RULING — CP-C2 / E02: **parked, to resume on Speed when the cluster frees up** — user, 2026-08-06

**The user's decision, verbatim:** *"mettre a cote de E02 est une decision correct, des que des
ressources speed devient disponible, nous pouvons continuer, prendre un note pour la decision de
E02."*

**The ruling in plain terms.** Parking E02 is confirmed correct. It is **not cancelled and not
descoped** — none of the four options put on 2026-08-06 was selected, because the user chose a
different axis: **E02 resumes when Speed cluster resources become available**, rather than being
squeezed onto this workstation tonight at reduced scope. **No relaunch is authorised until then.**
The local workstation is released.

**Standing state to hand to whoever resumes it:**
- **3 of 60 (cell, mode) pairs complete** — `nyc_centre` `auto`, `building`, `floor`, 2,214
  simulations, on disk under `%TEMP%/ubem_e02_five_mode`, `.eio` retained. **Not in any CSV.**
- `layout_assign` proven runnable and cheap (C02-P1). `fast_zone` proven to be both the cost driver
  and the memory hazard.
- The runner can now see a fatal (C07).

🔴 **Four things the resumer must deal with, and none of them are optional. Recording them now
because they are consequences of *where* E02 resumes, and they were identified before the fact.**

1. **FINDING 1's marker cleanup still applies, on any machine.** Delete the `sim_done.txt` of any
   (cell, mode) whose rows are not already in the output CSV, or those pairs vanish silently.
2. **Moving to Speed reintroduces exactly the defect E02 exists to fix, unless the template is
   changed first.** `scripts/cluster/submit_fleet_t08.sbatch:63` is `rm -f "$OUTDIR"/*.eio`, and it
   is byte-identical across T08→T20 (OPEN-02). **A cluster E02 that runs on the stock template
   deletes the one file the whole exercise is for.** The `.eio` retention built and audited in E01
   is **local-only** — it lives in `t08_local_remainder.py`, not in the sbatch template. **This is
   the single highest-risk item in resuming on Speed.**
3. **Mixing the 3 completed local pairs with cluster output would rebuild OPEN-28.** §1.1 pinned
   "all twelve cells on one generation" against exactly this. Either the cluster run redoes all
   sixty pairs, or the local three are discarded — **but the two sets must not be concatenated into
   one fleet CSV.** Whichever is chosen, state it in the CSV's provenance.
4. **The cluster's own cap was the reason E02 came local in the first place** (32 CPU fully occupied
   by an unrelated account, 675 pending, observed read-only 2026-08-05). **Confirm the allowance is
   genuinely free before scoping — and never cancel, requeue or deprioritise another project's
   jobs.**

**One measurement that is now free and was not before.** FINDING 3 gives real per-mode costs for a
738-building cell. Whoever re-scopes E02 for Speed should cost it from those numbers rather than from
`SCOPING_five-mode-rerun-cost.md`, whose local projection is measured wrong by ≈10× (§8 FINDING 3).
**The scoping doc needs that correction appended; it has not been applied yet.**

---

#### C06 — OPEN-09: is "cosmetic" true? — completed 2026-08-06

- Artifacts:
  - `openubem/outputs/comparisons/c06_open09_converged_vs_nonconverged_eui.csv` (150 rows, one
    per matched building: `osm_id`, per-arm warmup-severe count, per-arm convergence flag,
    per-arm EUI, `pct_delta`).
  - `openubem/outputs/c06_open09_converged_vs_nonconverged_eui_delta.png` (histogram + boxplot),
    mirrored to `docs/docs_ACTIVE/openings/extra/c06_open09_converged_vs_nonconverged_eui_delta.png`.
  - `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md` (full write-up,
    method, reconciliation, verdict).
  - Throwaway scripts, session scratchpad only, never under `docs/`: `c06_analysis.py` (raw
    `.err`/`.htm` re-derivation, CSV write), `c06_stats.py` (Mann-Whitney/Welch-t/Spearman),
    `c06_figure.py` (the PNG above).
- Deviations: none from the task's `How`. **Cost gate honoured exactly as specified**: found the
  matched control (F11-N / F11-N-b, the closed E-LA-20 arc's own 150-building population —
  `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:1193-1259`,
  read-only), verified all 300 raw run directories exist on disk under
  `scratchpad/e-la-20-fix/f11n_work/runs/` and `.../f11nb_work/runs/` (150 each, identical
  `osm_id` sets, diffed clean, 0 missing `.err`/`.htm`), and reported **branch (i): the runs
  exist, no EnergyPlus needed.** **Zero simulations run — none of the 400-simulation gate was
  used, and no EnergyPlus process was launched by this task.** OPEN-34's constraint is satisfied
  by construction, not by argument: F11-N's own harness enriched the **full `nyc_rural` fixture**
  in Step 2 before filtering to the 150-building sample (`f11n_run.py:100-104`, "Step 2: semantic
  enrichment (real pipeline, full nyc_rural fixture, run once)"), so the population was never
  classified from a small batch. Convergence status was **re-derived fresh from raw `.err` text**
  for both arms (grep for the exact `CheckWarmupConvergence ... did not converge after 25 warmup
  days` line) rather than trusted from any CSV column — the prior F11-N CSV does not even carry
  this column, and re-deriving it independently is what the evidence rules require. EUI was
  parsed directly from each run's own `eplustbl.htm` "Total Site Energy" table (same regex
  the original, already-audited F11-N/F11-N-b harnesses used — not a reimplementation, the
  identical extraction of EnergyPlus's own summary table) for all 300 run directories, not read
  from the prior CSVs. No sampling, no cap: all 150 buildings, both arms.
- Test status (actual output, not a summary):
  ```
  true(f11n) dirs: 150  false(f11nb) dirs: 150
  rows built: 150  missing_err: 0  missing_htm: 0
  fatal_true (raw .err, two-space regex): 0  fatal_false: 0

  True arm (thermal_mass=True): non-converged=96  converged=54  total=150
  False arm (thermal_mass=False, control): non-converged=8  converged=142

  NON-CONVERGED group (96): n=96  min=-2.0685  p25=-1.8718  median=-1.6290  p75=-1.4305
    max=-0.9946  mean=-1.6375  stdev=0.2671
  CONVERGED group (54): n=54  min=-2.1239  p25=-2.0121  median=-1.8770  p75=-1.7370
    max=-1.1595  mean=-1.8550  stdev=0.1897
  ALL 150 (sanity check vs F11-N-b's audited -2.124..-0.995, mean -1.716):
    min=-2.1239 p25=-1.9246 median=-1.7317 p75=-1.5354 max=-0.9946 mean=-1.7158 stdev=0.2637

  Mann-Whitney U (nonconverged vs converged pct_delta): p=4.095e-07
  Welch t-test: t=5.7529  p=5.316e-08
  Cohen's d = 0.8926
  Spearman(severe_count, pct_delta) rho=0.4300  p<1e-6 (more warmup severes -> less-negative delta)
  fraction of CONVERGED deltas falling inside NON-CONVERGED's [min,max] range: 0.963
  ```
  The "all 150" row reproduces F11-N-b's own already-audited distribution (min −2.124, p25
  −1.925, median −1.732, p75 −1.535, max −0.995, mean −1.716) to 3 decimal places — confirms
  this re-derivation pipeline agrees with the prior artifact before any new split is drawn from
  it. 96/150 and 8/150 reproduce exactly, independently, from raw text. PASS on all
  reconciliation checks.
- Notes: **Distribution reported, not just a mean, per the task's explicit requirement** — full
  five-number summaries for both groups above, plus the figure. **Verdict on "cosmetic":
  earned, not merely inherited, with one nuance now on the record.** No evidence of the
  alarming failure mode — if warmup non-convergence were corrupting the annual result, the
  non-converged group would show larger-magnitude, more scattered, or sign-inconsistent deltas
  than the converged group; instead every one of the 150 deltas is negative, the two
  distributions overlap 96.3%, and the non-converged group's mean is *smaller* in magnitude
  (−1.638% vs −1.855%), not larger. That said, the two groups are **not** statistically
  indistinguishable (p≈4×10⁻⁷, Cohen's d=0.89) — there is a real, monotonic, small
  (≈0.22-percentage-point, ≈0.20 kWh/m² at the population's median EUI of 91.19 kWh/m²)
  relationship in the direction opposite to the concerning one. Read plainly: the five inherited
  log entries (E-LA-14, E-LA-16, E-LA-18, E-LA-19, E-LA-23) do **not** need correcting on the
  claim's substance — it holds at the one population it has ever been tested on — but the claim's
  epistemic status changes from *inherited across five entries, untested* to *tested once, here,
  and confirmed with a quantified, small, correctly-signed residual*. It has not been tested
  outside `nyc_rural`/`SmallOffice`/`u_roof=0.119`, and that scope limit should travel with the
  claim from here on. Consequence (a) of OPEN-09 (the ≈3.66% fleet projection) was explicitly out
  of scope and was not touched. No cluster, git, or simulation command was run at any point in
  this task.

---

#### AUDIT — C06 — manager, 2026-08-06 — **GREENLIT**

Audited by **independent re-derivation from the raw artifacts**, not by reading the executor's
report back. The manager wrote its own scanner (session scratchpad, `audit_c06.py`), with its own
`eplustbl.htm` row/cell parse and its own `.err` counters, and walked all 300 run directories under
`scratchpad/e-la-20-fix/f11n_work/runs/` and `.../f11nb_work/runs/`.

**Manager's own output, reproduced here verbatim:**

```
[true]  dirs=150 missing_err=0 missing_tbl=0 fatal=0 nonconv=96 eui_parsed=150
[false] dirs=150 missing_err=0 missing_tbl=0 fatal=0 nonconv=8  eui_parsed=150
id sets identical: True | only_true: 0 only_false: 0
ALL            n=150 min=-2.1239 p25=-1.9246 med=-1.7329 p75=-1.5325 max=-0.9946 mean=-1.7158
NON-CONVERGED  n= 96 min=-2.0685 p25=-1.8591 med=-1.6287 p75=-1.4305 max=-0.9946 mean=-1.6375
CONVERGED      n= 54 min=-2.1239 p25=-2.0121 med=-1.8795 p75=-1.7329 max=-1.1595 mean=-1.8550
neg deltas: 150 of 150
median EUI true arm: 91.1889
converged inside non-conv [min,max]: 52/54
```

1. **Cost gate — honoured, and verifiable independently of the executor's word.** No file anywhere
   under either `runs/` tree has an mtime later than 2026-08-01 (`find … -newermt` returns empty);
   the two `runs/` directories themselves are stamped 2026-07-25. **Nothing was simulated.** 0 of
   the 400-simulation allowance used, exactly as branch (i) requires.
2. **Population not substituted.** 150 directories per arm, `osm_id` sets identical (manager's own
   set difference: 0 either way). The 96/150 and 8/150 counts the executor claims are the register's
   own carried figures, and they **re-derive exactly** from raw `.err` text — under two independent
   greps (`CheckWarmupConvergence` occurrence count, and `did not converge after`), which agree
   building-for-building. This is the population OPEN-09's numbers came from, confirmed rather
   than assumed.
3. **Distribution reported, not just a mean** — as C06's `How to test` demands. Manager's min /
   p25 / median / p75 / max / mean agree with the executor's to 4 decimals on min, max and mean in
   all three groups. Percentile cells differ in the 3rd decimal (e.g. non-converged p25 −1.8591 vs
   −1.8718) and stdev in the 4th (0.2645 vs 0.2637), which is quantile-interpolation choice and
   `ddof=0` vs `ddof=1` — **immaterial, no finding.**
4. **The headline claims survive re-derivation.** All 150 deltas negative (manager: 150/150).
   Non-converged mean is *smaller* in magnitude than converged (−1.6375 vs −1.8550), i.e. the
   opposite of the alarming failure mode. Overlap 52/54 = **96.3%**. Median true-arm EUI 91.1889
   kWh/m², so the 0.2176 pp gap is ≈0.198 kWh/m². Cohen's d recomputed by hand from the manager's
   own group stdevs = **0.893**, matching the executor's 0.89.
5. **CSV artifact is internally consistent with the raw files.** Re-loading
   `c06_open09_converged_vs_nonconverged_eui.csv` and regrouping it reproduces n=96/54, means
   −1.6375/−1.8550, 8 non-converged in the false arm, all-negative — identical to the manager's
   independent raw-file pass. 150 data rows.

**One correction, made by the manager (not a defect in the measurement).** The register's summary
table row for OPEN-09 read "96%/97% distribution overlap". The 96.3% figure is correct and is what
the OPEN-09 section body and the measurement doc both state; **97% is not reproducible** — the
reverse-direction overlap (non-converged deltas inside the converged range) is 92/96 = **95.8%**,
not 97%. The table row has been corrected to cite 96.3% only. The measurement's substance is
unaffected.

**Not overclaimed.** The executor explicitly declined to call the two groups statistically
indistinguishable, quantified the residual instead, and bounded the verdict to
`nyc_rural`/`SmallOffice`/`u_roof=0.119`. That is the correct epistemic posture and is the reason
this is greenlit rather than sent back.

**Disposition: OPEN-09 consequence (b) is CLOSED.** Consequence (a) — the ≈299/8,160 ≈ 3.66% fleet
projection — remains an untested projection and stays open, unchanged and out of scope.

---

#### BOOKKEEPING — scoping-doc correction applied — manager, 2026-08-06

§8's E02 hand-off note above states *"The scoping doc needs that correction appended; it has not been
applied yet."* **It has now been applied.**
`docs/docs_ACTIVE/openings/extra/SCOPING_five-mode-rerun-cost.md` gains a new append-only
**PART 3 — CORRECTION, 2026-08-06**, which records that Part 2's ≈10–15 h local projection is
**≈10× low**, carries FINDING 3's measured per-mode `nyc_centre` table forward as the cost basis to
use instead, states that the pre-registered "unbudgeted Step 3" cause was disproved by measurement
(Step 2 = 2.5–2.7 s/cell; Step 3 = 7.9 s/149 buildings), and names the real cause — the 3.2×–4.6×
local-vs-cluster speed factor, derived from 3 calibration runs on 1 building, does not hold at fleet
scale. Parts 1 and 2 are **left unedited**, so the failed prediction stays visible.

It also records what survived: the disk figures (machine-independent), Part 2 §4's finding that an
untrimmed local run cannot fit on this machine at all, and Part 2 §6's positive current-HEAD
generate-and-simulate data point for `auto`/`floor`/`fast_zone`. And it warns that Part 1's cluster
projection is **not** validated by this correction — it rests on the same 5-cell/5-week-old T08
extrapolation for four of five modes, and should be re-derived rather than reused when E02 is
re-scoped for Speed.

No decision is changed by this entry; E02 remains halted-not-abandoned, parked at the user's
instruction, with the CP-C2 scope ruling still owed.

---

#### 🅿️ PAUSE — the arc is paused at the user's instruction — manager, 2026-08-06

**User instruction:** *"je vais me concentrer sur d'autres projets … dès que j'ai temps frais, je vais
retourner."* The user is moving to other projects and will return later. **This is a pause, not a
close.** Nothing is cancelled, nothing is abandoned, and no task is left half-finished.

**Machine state at the pause: idle.** No local run, no cluster job, no executor session.

**State of this plan's tasks:**

| Task | State |
|---|---|
| C01 | done, CP-C1 signed |
| **C02 (E02)** | **halted by `MemoryError`, parked to resume on Speed when the cluster frees up.** CP-C2 **not** signed; the scope ruling is still owed by the user. Three of sixty (cell, mode) pairs are complete on disk. |
| C02-P1 | done — `layout_assign` probe, 149/149 |
| C03 | done, audited |
| C04, C05 | blocked on C02 by design; not startable |
| C06 | done, audited, GREENLIT |
| C07 | done, audited, GREENLIT |

**Everything owed by this plan to its documents is written.** Three surfaces are current as of this
entry: this progress log, `INVESTIGATION_open-items-register.md` (whose new **closing amendment** is
the compressed resume brief), and `prompts/DIRECTOR_PROMPT_openings_2026-08-06.md` (whose new **top box
and §11** carry the pause and the resume order). The board
`implemenation/board_published-numbers.html` was republished to the same URL with a pause panel at the
head, and **copied to `openings/reporting/board_published-numbers.html` at the user's request** — that
copy is a static snapshot and is **not** the published artifact; republishing must continue to use the
`implemenation/` path or the URL will change.

**The four conditions on resuming survive the pause unchanged.** None is discharged by it:

1. **FINDING 1's marker cleanup** — `nyc_centre`'s three finished modes are marked done in
   `sim_done.txt` while their rows were never written to the output CSV. Delete the `sim_done.txt` of
   any (cell, mode) not already in the output CSV **before any relaunch, on any machine**. Still
   un-done.
2. 🔴 **`submit_fleet_t08.sbatch:63` deletes every `.eio`**, and E01's retention fix is local-only. A
   cluster E02 on the stock template destroys the evidence OPEN-02 exists to obtain. Highest-risk item.
3. **Do not concatenate the finished local pairs with cluster output** — that rebuilds OPEN-28.
4. **Confirm the account's CPU allowance is genuinely free**, and never cancel or deprioritise another
   project's jobs.

**No new work was started to fill the pause**, and none should be on resuming until the user has been
told the state and has ruled. Every remaining first measurement in the register needs either CPU or a
decision from them.

---

### RULING — CP-C2's scheduling axis — given by the user 2026-08-09. **This plan hands off to `PLAN_speed-resume.md`.**

**The unblocking event happened.** *"maintenant des ressources de speed est disponible, nous pouvons
utiliser avec des taches qui utilisent des ressources pour le computation."* Speed was independently
reconnoitred read-only the same day before anything was proposed: account `chachemv`,
`GrpTRES cpu=32`, **0 of 32 in use**, `squeue -A chachemv` empty, `/speed-scratch` quota 4.1 TB free
against a ~45 GB worst case. **Both gates that parked E02 are open.**

**Question put to the user** (CP-C2's remaining axis — *not* the spent (a)–(d) descope options, which
were not re-asked): probe first / submit all five modes now / four modes now with `fast_zone` queued
after. **Answer: measure first.** One bounded calibration probe on Speed, then the fleet-scope decision
against measured numbers.

**Why that is the right shape and not caution for its own sake.** FINDING 3 measured the local
projection wrong by **≈10×**, and `SCOPING_five-mode-rerun-cost.md` PART 3 records that the *cluster*
projection rests on the same 3-timing-run calibration and **must be re-derived, not reused**. The
manager's own scaling from the measured local wall-clocks puts the four cheaper modes at ≈3–4 days and
`fast_zone` alone at ≈2 weeks at 32 CPUs — a spread wide enough that submitting first and measuring
afterwards would be a decision taken blind, on the strength of the one number this arc has already been
burned by.

**Execution moves to `PLAN_speed-resume.md`** (S01–S05, checkpoints CP-S1 and CP-S2). What it
discharges, in order: the `.eio` deletion in the cluster template (condition 2 above), the cluster
harvest's broken fatal detection (`t08_harvest_results.py:245`, the C07 precedent applied to the script
that will generate these results — **this does not discharge OPEN-29**), the newly-obligatory vintage
column (RULING A of 2026-08-09, OPEN-30), and FINDING 1's marker cleanup with a guard against its
recurrence (condition 1 above). **Only then** the probe: `la_rural` + `nyc_rural`, whole cells, all
five modes, ten independent arrays.

🔴 **The fleet submission remains unauthorised.** CP-S2 reports the probe's numbers to the user and the
scope decision is theirs. Conditions 3 and 4 above stay in force verbatim.
