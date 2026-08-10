# PLAN — resuming E02 on the Speed cluster

**Slug:** `speed-resume` · **Opened:** 2026-08-09 · **Arc:** `openings`
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — the binding source of
state. **Predecessor plans:** `PLAN_published-numbers.md` (§8 holds E02's whole history, CP-M1, the
C02 `MemoryError` audit and its FINDING 1/2/3), `PLAN_compute-queue.md` (C01–C07, CP-C1 signed,
CP-C2 owed).

**Why this document exists.** E02 — the five-mode, twelve-cell, 40,800-simulation fleet pass that
closes **OPEN-01, OPEN-02 and OPEN-28 together** — was halted on 2026-08-06 by a real `MemoryError`
and parked by the user *to resume on Speed when its resources free up*. **They freed up.** The user
released compute again on 2026-08-09: *"maintenant des ressources de speed est disponible, nous
pouvons utiliser avec des taches qui utilisent des ressources pour le computation."*

**This plan does not submit E02.** It discharges the four conditions the park attached to a Speed
resume, and then runs **one bounded calibration probe** so that the fleet-scale decision is taken
against a measured cluster cost instead of a projection. That sequencing is the user's ruling of
2026-08-09, taken in preference to submitting all five modes immediately.

---

## 1. The two rulings this plan implements

**RULING A — 2026-08-09, CP-M3 + OPEN-30 + OPEN-33.** Put to the user as one question — *what must a
change carry before it counts as finished?* — and answered **all three obligatory**:

1. no change that can move classification is adopted without the 50-row labelled fixture run on
   **both** sides, both numbers recorded;
2. **every harvest persists the assigned vintage token**;
3. archiving an arc is not finished until citations into it are swept.

**Only (2) binds this plan**, and it binds it hard: it must be true **before** submission, because a
pass that does not record the vintage cannot be repaired afterwards. (1) does not apply — no task
here touches classification. (3) does not apply — nothing is being archived.

**RULING B — 2026-08-09, CP-C2's scheduling axis.** Options put: probe first / submit all five now /
four modes now with `fast_zone` queued after. **Answer: measure first.** The user chose a bounded
probe on Speed, then a scope decision with real numbers. 🔴 **The four descope options (a)–(d) from
2026-08-06 remain spent — never re-ask them.**

---

## 2. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Interpreter `./.venv/Scripts/python.exe`.
2. 🔴 **NEVER run compute on the Speed login node** (`speed-submit2` / `speed.encs.concordia.ca`).
   Permitted there: `squeue`, `sacct`, `sinfo`, `scontrol show`, `ls`, `du`, `quota`, `mkdir`, `scp`,
   `tar`, `cat` of small files. **All compute goes through `sbatch --array`, fire-and-forget, then
   read the output file.** No `srun`, no `ssh … python …`.
3. 🔴 **Never cancel, requeue, modify or deprioritise any cluster job**, least of all another
   project's. Our account is `chachemv`; the partition carries unrelated accounts' work at all times.
4. **Do everything in session.** Never end a turn saying you will wait for a notification. Never spawn
   subagents. Block on artifacts on disk. *(Third-occurrence failure mode in this project.)*
5. **You execute this plan; you do not rewrite it.** If the plan and the register conflict, **STOP and
   quote the conflict.** Do not resolve spec ambiguity by choosing.
6. **Measurement tasks forbid remediation and remediation tasks forbid scope creep.** R05 measures; it
   fixes nothing. R01–R04 fix exactly what they name.
7. **A before/after is not reportable until the "before" is shown to differ from the "after."** Every
   fix task below carries a demonstration requirement for exactly this reason.
8. **Ground truth is the raw artifact.** `eplusout.err` for run outcome, `eplusout.eio` for
   multiplier-aware floor area. **Never the `.end` file** for anything but completion. **Never the
   `has_fatal` column** on any pre-2026-08-06 artifact.
9. **A parser that finds nothing must say so, never report `0`.**
10. **Recompute every headline number from the named file before reporting it.**
11. **Never `git commit`.** Git is handled externally by the user. Do not offer.
12. **Never edit root `main.py`, any OVERVIEW or DESIGN doc. No `.py` under `docs/`.**
13. **Progress-log entries are append-only.** Correct a wrong entry with a new entry citing the old.
14. **Default to no comments.** One short line only where the WHY is non-obvious.

---

## 3. Files this plan touches

```
scripts/cluster/submit_fleet_t08.sbatch        ← R01 (one line + two comments)
scripts/cluster/t08_harvest_results.py         ← R02 (one line)
scripts/cluster/t08_local_remainder.py         ← R03, R04 (vintage column; resume guard)
scripts/cluster/<harvest touched by R03>       ← R03 (same column, cluster side)
docs/docs_ACTIVE/openings/implemenation/PLAN_speed-resume.md   ← progress log, §8
docs/docs_ACTIVE/openings/extra/MEASUREMENT_speed-probe-cost.md ← R05's report
```

**Nothing else.** If a task appears to require touching a file not listed here, that is a signal to
**STOP and report**, not to widen the diff.

---

## 4. Dependency decisions — pinned, do not re-debate

| Decision | Value | Why |
|---|---|---|
| Where the `.eio` fix goes | **`submit_fleet_t08.sbatch` itself**, not a new template | Verified 2026-08-09: five sweep scripts (`t08_full_sweep.py:46-47`, `t17:61-62`, `t18:65-66`, `t19:68-69`, `t20:71-72`) all point `SBATCH_LOCAL`/`SBATCH_REMOTE` at **that one file**. One edit repairs every path; a new template would leave five scripts pointing at the broken one. |
| Retention set on the cluster | **exact parity with the local runner** — `eplusout.eio`, `.sql`, `.err`, `.end`, `task.rc` | `t08_local_remainder.py:85`. Parity is what makes cluster and local output comparable at all. |
| `eplusout.shd` / `sqlite.err` | **left surviving, unchanged** | They already survive both paths and were deliberately not changed at E01b. Not this plan's business. |
| Probe cells | **`la_rural` (149) + `nyc_rural` (198)** — whole cells, never subsets | OPEN-34: a subset of a cell is **not archetype-faithful** (`_impute_levels` takes a group median over whatever is in the batch), and archetype drives model size, so a sampled probe mis-costs the fleet. Two cells, not one, because per-building cost varies ≈4× across cells. |
| Probe modes | **all five**, submitted as **ten separate arrays**, one per (cell, mode) | Independent timing per mode; any one can be abandoned without losing the others. `fast_zone` is the unknown that matters. |
| Fleet submission | **NOT authorised by this plan** | CP-R2 reports to the user; the scope decision is theirs. |

---

## 5. Source-of-truth verified facts — grepped by the manager 2026-08-09

Every line below was opened, not recalled. **Do not re-derive these; do check them if you touch the
surrounding code.**

1. **The `.eio` deletion.** `scripts/cluster/submit_fleet_t08.sbatch:62-80` is a single `rm -f`
   continuation block; **`:63` is `      "$OUTDIR"/*.eio \`**. `:60-61` comment it as T08 trimming;
   **`:81` is `# Kept: eplusout.sql, eplusout.end, eplusout.err, task.rc`**; `:83` echoes
   `"cleanup done, kept sql+end+err"`; `:10-12` repeat the claim in the header. **All four statements
   become wrong the moment `:63` is removed** — the fix is one deletion plus four text corrections.
2. **It is the only deletion.** Exactly two `*.sbatch` files exist under `scripts/cluster/`
   (`submit_fleet.sbatch`, `submit_fleet_t08.sbatch`); the former contains **no** trimming block at
   all. The register's "byte-identical across T08→T20" is true **definitionally** — there are not five
   copies, there is one file used by reference by five scripts (§4, row 1).
3. **The local retention set.** `t08_local_remainder.py:85`
   `RETAIN_FILENAMES = ("eplusout.eio", "eplusout.sql", "eplusout.err", "eplusout.end", "task.rc")`;
   `:87-92` `TRIM_DELETE_GLOBS`, documented at `:83` as *"cluster parity … minus `*.eio`"*;
   `:94` `DISK_FLOOR_BYTES = 50 GB`.
4. **Fatal detection — fixed locally, still broken on the cluster side.**
   `t08_local_remainder.py:431` is `re.search(r"\*\*\s+Fatal\s+\*\*", err)` (C07, 2026-08-06).
   **`scripts/cluster/t08_harvest_results.py:245` is still `has_fatal = "** Fatal **" in err`** — the
   one-space form. EnergyPlus writes **two** spaces. Its banner is at `:340`
   (`Fatal-free: YES/NO`). Row assembly is `:247-251`.
5. **Where a harvest row is built.** Cluster: `t08_harvest_results.py:247-251` —
   `cell, city, mode, osm_id, archetype_id, floor_area_m2, status, has_fatal`. Local:
   `t08_local_remainder.py:433-441` — same plus `platform`, `build_date`. **Neither carries a vintage
   column.** That absence *is* OPEN-30.
6. **The vintage token exists upstream.** `openubem/semantic/construction_sets.py:126`
   `def resolve_vintage(gdf) -> tuple[pd.Series, pd.Index, pd.Series]`; the token is materialised at
   `:352` as `result["vintage_standard"]` and carried in `keep_cols` at `:354`. **Whether it survives
   as far as the frame a harvest joins against is NOT established — that is R03's first job.**
7. **Cluster job shape.** `submit_fleet_t08.sbatch:2-7`: `--partition=ps`, `--cpus-per-task=1`,
   **`--mem=6G`**, **`--time=02:00:00`**, one building per array task, logs to
   `/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log`. Array throttle is passed at submit time
   (`--array=1-N%16`, `:14`).
8. **Allowance and disk, 2026-08-09** *(reconnaissance-sourced, remote — not re-derived by the manager
   locally)*: account `chachemv`, `GrpTRES cpu=32`, **0 of 32 in use**, `squeue -A chachemv` empty;
   `/speed-scratch` personal quota 10.0 TB with **4.1 TB free**; project dir 36 GB. **Re-check the
   allowance immediately before submitting** — it was reported free on 2026-08-05 too and was in fact
   fully consumed by another account.
9. **The local machine's state, manager-verified 2026-08-09.** Zero Python/EnergyPlus processes;
   newest E02 log write `2026-08-06 05:47:01`; **four `sim_done.txt` markers survive** —
   `%TEMP%\ubem_e02_five_mode\{nyc_centre\sim_out_auto, sim_out_building, sim_out_floor,
   la_rural\sim_out_layout_assign}` — and
   `openubem/outputs/comparisons/e02_five_mode_fleet_eui.csv` **does not exist**. FINDING 1's trap is
   armed and un-cleaned.

---

## 6. Task list

### R01 — Stop the cluster template deleting `eplusout.eio`

**What to do.** Remove `*.eio` from the `rm -f` block in `scripts/cluster/submit_fleet_t08.sbatch`,
and correct **every** comment that claims `.eio` is deleted or that only sql/end/err are kept
(`:10-12`, `:81`, `:83`).

**Why.** OPEN-02's entire purpose is to obtain, for the first time, the file recording the floor area
EnergyPlus **actually simulated** — the denominator OPEN-01 says is wrong for 87.4% of buildings.
`:63` deletes it on every array task. E01's retention fix is **local-only**
(`t08_local_remainder.py:85`), so a cluster run on the stock template destroys the evidence the run
exists to collect, silently, after the CPU is already spent. This is the single highest-risk item in
the whole Speed resume (register, closing amendment, condition 2).

**How.** Delete line `:63` only. Do **not** touch any other glob — the rest is deliberate parity with
`TRIM_DELETE_GLOBS`. Do not reflow the continuation backslashes of neighbouring lines beyond what
removing one line requires. Comments must end up stating the retention set exactly as
`RETAIN_FILENAMES` does.

**How to test.** A real before/after, not an assertion:
1. Build two identical fixture directories containing a dummy `eplusout.eio`, `.sql`, `.err`, `.end`,
   `task.rc` **and** at least one file from every delete glob.
2. Run the **old** `rm -f` block over one and the **new** block over the other, via the Bash tool.
3. Report both file listings. **PASS requires:** `.eio` **absent** under the old block and **present
   and non-empty** under the new one, and the two listings **identical in every other respect**.
   A test that cannot show the old behaviour failing does not satisfy §2 rule 7.
4. Confirm the script still parses: `bash -n scripts/cluster/submit_fleet_t08.sbatch`.

### R02 — Give the cluster harvest working fatal detection

**What to do.** `scripts/cluster/t08_harvest_results.py:245` — replace the one-space literal test with
the same regex the local runner uses at `t08_local_remainder.py:431`:
`re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None`. Add the `re` import if absent.

**Why.** EnergyPlus writes `**  Fatal  **` with two spaces; the literal `"** Fatal **"` matches **0
of 2** real fatals in the halted run's own 2,422 `.err` files. If the probe is harvested with this
script, its `has_fatal` column and its `Fatal-free: YES` banner (`:340`) will report a clean run over
any number of real fatals. **This is the precedent set by C07 on 2026-08-06** — fix the script that
generates *today's* results, and leave the rest to a user ruling.

🔴 **This does NOT discharge E-LA-21 / OPEN-29.** Four other harvest scripts
(`t20_harvest_layout_assign.py`, `t07_harvest_results.py`, `t07b_run_auto_refit_local.py`, and this
file's siblings) keep the defect **by design** — fixing them is the user's decision under OPEN-29, not
a side effect of this repair. **"Never use the `has_fatal` column" stays in force for every
pre-2026-08-06 artifact.** Say all of this in the progress-log entry.

**How to test.** Before/after over real files, not synthetic ones. The halted run's `.err` files are
on disk under `%TEMP%\ubem_e02_five_mode\`. Count matches with the **old** test and the **new** test
over the same file set. **PASS requires** old < new, with the newly-matched files named. The expected
answer is **0 → 2** (`way_266149332`, `way_266170765`), but **report what you measure**, not what is
expected. **Negative control, mandatory:** confirm the new regex does **not** match the decorative
lines `************* Fatal error -- final processing.` or
`************* EnergyPlus Terminated--Fatal Error Detected.`, which are physically present in those
same two files — a looser regex over-counts and would pass a naive test.

### R03 — Persist the assigned vintage token in the harvest output (OPEN-30, RULING A)

**What to do.** Make both harvest paths emit a `vintage_standard` column per building: the cluster
harvest (`t08_harvest_results.py:247-251`) and the local runner (`t08_local_remainder.py:433-441`).

**Why.** OPEN-30, ruled obligatory by the user on 2026-08-09. `resolve_vintage()`
(`construction_sets.py:126`) produces the token, `envelope_patcher` consumes it, and **it is then
discarded** — no harvest output and no `05_results.gpkg` at any git state carries it. Consequence:
vintage agreement between runs cannot be checked **now, or at any past point**, and OPEN-03 cannot be
bounded against the fleet's real vintage distribution rather than a 12-archetype proxy. **A fleet pass
submitted without this column reproduces the gap permanently for that generation.**

**How.**
1. **First trace, then write.** Establish where `vintage_standard` (`construction_sets.py:352`,
   `keep_cols` `:354`) actually lands: does it survive into the per-cell building frame the harvest
   already joins against (the `bld` row at `t08_harvest_results.py:230-232`), or is it consumed and
   dropped inside the envelope patcher? **Report the answer with file:line citations before writing
   any code.**
2. **If it is present in that frame** — read it through, exactly like `archetype_id` at `:232`. Missing
   values become the empty string, never a fabricated default.
3. 🔴 **If it is NOT present**, you face a choice that is **not yours to make silently. STOP and
   report.** Re-deriving the token at harvest time by calling `resolve_vintage()` again is acceptable
   **only** if it is demonstrably the same call on the same inputs the builder used; otherwise it is a
   script that reimplements pipeline logic and produces **lookalike evidence** — the exact failure the
   register names (`a1_prototype_storey_structure.csv`) and the reason the evidence rules exist.
4. Column name is **`vintage_standard`**, matching `construction_sets.py:352`. Do not invent a new one.

**How to test.** Run the local runner's harvest over a cell that already has completed simulations on
disk (`nyc_centre`, `auto` — 561+ buildings from the halted run) and show: the column exists, its
non-null rate, and its **value distribution**. **PASS requires** the distribution to be plausible
against the fleet's known composition — the register records **92.9% `DOERefPre1980`**; a column that
comes out uniform, constant, or 100% one modern token is a defect, not a pass. **Report the
distribution even if it looks right.**

### R04 — Disarm FINDING 1's silent resume trap

**What to do.** Two parts.
**(a)** Delete the four stale `sim_done.txt` markers named in §5 fact 9.
**(b)** Add a guard to `t08_local_remainder.py` so a mode marked done whose rows are **not** in the
output CSV is **re-harvested rather than skipped** — or, if that is structurally awkward, so the run
**refuses to start** and names the offending (cell, mode) pairs.

**Why.** `main()` skips a mode entirely the instant its `sim_done.txt` exists, and recovers its rows
only by reading them back out of the output CSV once every requested mode of a cell is done.
`nyc_centre`'s three finished modes are marked done and **their rows were never written anywhere** —
so a naive relaunch produces a "fleet" CSV **silently missing 2,214 buildings**, including `auto`, the
mode OPEN-28's published comparison depends on. Nothing in the run would say so. Part (a) removes
today's landmine; **part (b) is why this is a task and not a shell command** — it stops the trap
recurring on the next resume, which is exactly the class of closing-step failure RULING A is about.

**How.** Deletion is safe and nearly free: Step-4 resume is **per building** via `eplusout.end`, which
is in `RETAIN_FILENAMES`, so the 2,273 already-simulated buildings are skipped and only Step 3
(minutes) and the harvest re-run. **Do not delete anything else** — not a run directory, not an
`.eio`, not `eplusout.end`. List every path before and after deleting it.

**How to test.** For (a): show the four paths existing, then absent, and show that no other file under
the work base changed (count files before/after). For (b): construct a work base with a `sim_done.txt`
whose rows are absent from the output CSV, run the guard, and show it fires; then with rows present,
show it does not. Both directions, per §2 rule 7.

### R05 — The Speed calibration probe — MEASUREMENT ONLY

**What to do.** After R01–R04 are complete and CP-R1 is signed, stage the current code to Speed and
submit **ten independent array jobs**: `la_rural` (149 buildings) and `nyc_rural` (198) × five modes
(`auto`, `building`, `floor`, `layout_assign`, `fast_zone`). Fire-and-forget, then read the outputs.

**Why.** The fleet-scale decision needs a **measured** cluster cost. The local projection was wrong by
**≈10×**, and the cluster projection rests on the same 3-timing-run calibration
(`SCOPING_five-mode-rerun-cost.md` PART 3 says re-derive it, do not reuse it). The probe also
end-to-end-validates everything R01–R03 changed, on real cluster nodes, before 40,800 simulations
depend on it.

**How.**
- **Whole cells only.** Never a subset — OPEN-34.
- **One array per (cell, mode)**, so each is independently timed and independently abandonable.
- **Re-check the allowance immediately before submitting** (`squeue -A chachemv`,
  `scontrol show assoc_mgr`). If another account has taken the 32-CPU cap in the meantime, **STOP and
  report** — do not queue behind it and do not touch their jobs.
- 🔴 **Two pre-registered risks. Write down what you expect BEFORE you look at the results, and do not
  edit that prediction afterwards.**
  - **Wall-time.** `--time=02:00:00` per task. `fast_zone`'s worst local building took ≈18–26 min on a
    core measured 3.2–4.6× faster than a cluster core — **that lands on or past the two-hour wall.**
    Report every task that ends `TIMEOUT`, by stem. If any do, the wall is a fleet-scale blocker and
    that is a finding, not a nuisance.
  - **Memory.** `--mem=6G` per task. C02 died of a `MemoryError` that was **`fast_zone`-specific**
    (751.3 MB of Step-3 IDF for one cell, max single IDF 14.26 MB) with sixteen models resident at
    once. One-building-per-task should change this completely — **so measure it**: report `MaxRSS` per
    mode from `sacct`, and say plainly whether 6G is comfortable, tight, or wrong.
- **Report per (cell, mode):** wall-clock, total CPU-time, per-building cost, `MaxRSS`, task states
  (COMPLETED / FAILED / TIMEOUT / OOM), and **`.eio` retained count** — the last one is R01's proof on
  real hardware.
- 🔴 **Do NOT extrapolate to a single fleet number.** Per-building cost varies ≈4× across cells
  (`nyc_centre`/`auto` ≈110 core-seconds/building against the `la_rural` probe's 25.7). Report a
  **range with the two cells' spread stated**, and name the extrapolation as the weak step. Producing
  one confident fleet figure from two small rural cells would repeat the exact error that produced the
  10× miss.
- 🔴 **Do not concatenate probe output with the halted local run's output**, ever. That rebuilds
  OPEN-28 (register condition 4).

**How to test.** The probe *is* the measurement; its correctness checks are:
`.eio` present and non-empty for every successful building (R01 on real hardware); `vintage_standard`
populated with a plausible distribution (R03); `has_fatal` computed by the new regex (R02); `city`
resolving correctly, **not** silently falling back to the cell name (`t08_local_remainder.py:423` does
this silently, and it is how a whole city-level group-by breaks quietly).

**Deliverable.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_speed-probe-cost.md`, plus a progress-log
entry here. Figures, if any, go **flat** to `openubem/outputs/` and are mirrored into
`docs_ACTIVE/openings/`.

---

### R06 — Fix fatal detection in every remaining live harvest script (OPEN-29, RULING C)

**What to do.** Replace the substring test `has_fatal = "** Fatal **" in err` with the C07-verified
regex `re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None` in **all six** live sites, adding
`import re` where absent:

| # | File | Line (2026-08-09) |
|---|---|---|
| 1 | `scripts/cluster/t07_harvest_results.py` | 198 |
| 2 | `scripts/cluster/t07b_run_auto_refit_local.py` | 329 |
| 3 | `scripts/cluster/t17_harvest_layout_assign.py` | 254 |
| 4 | `scripts/cluster/t18_harvest_layout_assign.py` | 251 |
| 5 | `scripts/cluster/t19_harvest_layout_assign.py` | 259 |
| 6 | `scripts/cluster/t20_harvest_layout_assign.py` | 259 |

**Explicitly OUT of scope — do not touch, and say so in the progress log:**
- `docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/scripts/t19_harvest_layout_assign.py:259`
  — an archived copy inside a closed arc's evidence folder. Editing archived evidence falsifies the
  record of what that arc actually ran. Leave it; note it.
- `scripts/diagnostics/t01_reproduce_degenerate.py:108`, `t04_validate_way428643335.py:133`,
  `t06_validate_relation6374725.py:153` — these test the two variants `"**  Fatal **"` /
  `"** Fatal  **"`, neither of which is the true two-space form, so they are **also** wrong; but they
  are one-off diagnostics from closed arcs whose conclusions are already recorded. Report them as a
  standing defect; do not change them under this plan.

**Why.** EnergyPlus writes `**  Fatal  **` (two spaces each side). The single-space literal matches
nothing, so `has_fatal` is `False` for **every** row including genuinely fatal ones — a crashed
building is reported clean. This is E-LA-21 / register item OPEN-29, ruled by the user 2026-08-09:
fix it everywhere, not only in the script producing today's results. `t08_harvest_results.py` (R02)
and `t08_local_remainder.py:431` are already correct and are not in this task.

**How.**
- 🔴 **Mechanical substitution only.** Do not refactor, do not rename, do not "improve" surrounding
  code, do not reformat. One line per file, plus an `import re` if the module lacks one.
- These are **disjoint** from the files R01–R04 touch. If a file in your list has been modified since
  this table was written, STOP and report the drift rather than editing a line number that moved.
- Do **not** re-run any harvest to regenerate historical outputs. Past result tables produced with the
  broken test keep whatever `has_fatal` they were written with; whether any past conclusion depended
  on that column is a **separate** question and is not settled here.

**How to test.** The register's own rule: a before/after is not reportable until the "before" is shown
to differ from the "after". For **each** of the six files, over a real corpus of `eplusout.err` files
on disk, report **both** counts — matches under the old literal and under the new regex — and the
corpus size. If the corpus contains no fatal error at all, the test is inconclusive: **say so
explicitly, do not report 0 as a pass.** Construct a fixture `.err` containing a real two-space
`**  Fatal  **` line and show old=0, new=1.

**Deliverable.** Progress-log entry here, with the six before/after pairs and the corpus provenance.

### R07 — Carry the vintage token to both harvests through the manifest (OPEN-30, RULING D)

**What to do.** In `run_step3_mode()` (`scripts/cluster/t08_full_sweep.py:154-181`), attach
`vintage_standard` to the manifest before it is written to `03_manifest.parquet` (`:174`), by
left-joining it from the `gdf` argument on `osm_id`. Then read it through in both harvests exactly as
`archetype_id` is read: cluster (`t08_harvest_results.py:254-257`, inside the existing
`if manifest is not None:` block) and local (`t08_local_remainder.py`, its manifest-row block).

**Why — this is RULING D, the manager's answer to R03's STOP.** R03 stopped correctly: the executor
established with citations that `vintage_standard` exists only as a transient in-memory column on
`gdf_57` and is in **no** persisted artifact the cluster harvest can reach, and it refused both a
partial fix and a re-derivation. The manager's ruling resolves it: **the manifest is the channel.**
Three facts make this the correct route and not a workaround —
(a) `run_step3_mode()` receives `gdf` = `gdf_57`, which **does** carry the token: `vintage_standard`
is the first of the 28 appended envelope columns (`openubem/semantic/__init__.py:45-47`,
`_F17_ENVELOPE_COLS`), written at `construction_sets.py:352`;
(b) the manifest **already** carries `osm_id` and is **already** read by the cluster harvest from the
local sweep directory (`t08_harvest_results.py:587,591,618`) and by the local runner — so no new
channel, no new file, no shipping change;
(c) the value is **copied**, in the same process and the same moment the IDF is generated, from the
frame the builder itself consumed. **Nothing is recomputed.** This is the distinction the evidence
rules turn on: calling `resolve_vintage()` again at harvest time would be a script reimplementing
pipeline logic and would produce lookalike evidence; copying the column the builder was handed is
provenance, not reconstruction.

**How.**
1. In `run_step3_mode()`, after `run_step3(...)` returns and **before** `to_parquet`, left-join
   `gdf[["osm_id", "vintage_standard"]]` onto `manifest` on `osm_id`. Cast to `str` on both sides of
   the join if dtypes differ (the manifest builds `osm_id` via `str(row["osm_id"])`,
   `openubem/idf/builder.py:394`; `vintage_standard` is a **pandas Categorical**,
   `openubem/semantic/__init__.py:395` — cast it to `str` before writing or parquet round-trip may
   surprise you). **Do not touch `openubem/idf/builder.py`** — the join belongs in the script.
2. Both harvests read the column from the manifest row they already look up. Missing → **empty
   string**, never a fabricated default, and never a re-derivation.
3. 🔴 **Manifests written before this change do not have the column.** That is correct and must stay
   correct: those rows get the empty string. **Do not backfill them by any means.** A manifest without
   the column is a run whose vintage was never recorded, and saying so is the honest output.
4. One edit in `run_step3_mode()` serves **both** paths — `t08_local_remainder.py` imports that exact
   function (`from t08_full_sweep import run_step2, run_step3_mode`). Do not duplicate the join.

**How to test.** Regenerate Step 3 for one cell/mode that already has enriched inputs on disk, then
report: (a) the manifest's column list, showing `vintage_standard` present; (b) its **non-null rate**;
(c) its **full value distribution**. **PASS requires the distribution to be plausible against the
fleet's known composition — the register records ≈92.9% `DOERefPre1980`.** A column that comes out
uniform, constant, or 100% one modern token is a defect, not a pass. **Report the distribution even if
it looks right.** Then run a harvest over that cell/mode and show the column survives into the output
CSV with the same distribution. If you cannot regenerate Step 3 cheaply, say so — **do not substitute a
synthetic frame and report its distribution as the fleet's.**

### R08 — Make R04's resume guard survive the incremental write

**What to do.** In `t08_local_remainder.py`, stop the per-cell incremental CSV write from destroying
rows that the resume guard recovered for cells the loop has not reached yet.

**Why — R04 is incomplete, found by the manager at CP-R1, not reported by the executor.**
`recover_missing_done_modes()` (`:479`) writes recovered rows for **all** cells into `output_csv` at
startup. The cell loop then does `interim = pd.concat(all_dfs); interim.to_csv(output_csv)` after
**each** cell (`:786-789`) — an **overwrite** from `all_dfs`, which at that moment holds only the cells
processed so far. So the first cell's incremental write deletes every recovered row belonging to cells
2…12. When cell 2's iteration then reads `output_csv` back (`:722-728`) to reload its done modes, the
rows are gone, and `is_done()` is still `True` so they are never regenerated either. The manager
demonstrated this on a two-cell fixture re-enacting those exact statements: after the guard the file
held `c1/auto` and `c2/auto`; after the run it held `c1/auto, c1/floor, c2/floor` — **`c2/auto`
silently vanished.** That is FINDING 1 reproduced one level up: the guard repairs the startup state and
the very next write undoes it. The pre-existing "all modes done" branch had the same shape, so this is
not a regression the guard introduced — but R04's stated purpose is that a resume cannot silently lose
buildings, and as written it still can.

**How.** Your choice of mechanism, but it must satisfy both: (i) rows already in `output_csv` for
(cell, mode) pairs the loop has **not yet reached** survive every incremental write; (ii) no row is
**duplicated** when a cell's rows are both loaded into `all_dfs` and present in the file. The obvious
route is to make the incremental write a merge — read the file, drop the (cell, mode) pairs `all_dfs`
covers, concat, write — rather than a bare overwrite. Do **not** solve it by deleting the guard or by
loading the whole CSV into `all_dfs` up front.

**How to test.** Both directions, per §2 rule 7, on a fixture with **at least three** cells where the
**last** cell has a recovered done mode: (a) show the row count and the exact (cell, mode) set in the
file after the guard, after the first incremental write, and after the final write — the last cell's
recovered pair must be present at **all three** points; (b) show the total row count contains **no
duplicates** (`duplicated()` count = 0 on the identifying columns). Report the (cell, mode) sets
literally, not just counts.

---

## 7. Stop-and-report points

**CP-R1 — after R01, R02, R03, R04. Nothing is submitted to Speed before this is signed.**
The manager audits by **independent re-derivation from the raw artifacts**, not by reading the report:
the old and new `rm` blocks are re-run by the manager over its own fixture; the fatal-regex counts are
recomputed over the `.err` files; the vintage distribution is recomputed from the harvest output.
**R03's trace answer is the one most likely to hide a lookalike — it gets read hardest.**

> **AMENDMENT 2026-08-09 (second) — CP-R1 is NOT signed; it now covers R07 and R08.** The first CP-R1
> audit passed R01, R02 and R04(a), accepted R03's STOP as correct executor behaviour, and **failed
> R04(b)**: the resume guard does not survive the per-cell incremental write (see R08 for the
> demonstration). R03's STOP is answered by **RULING D** (see R07). CP-R1 therefore covers
> **R01, R02, R04, R07, R08**, and is signed only when R07 and R08 are audited by independent
> re-derivation. **Nothing is submitted to Speed before that.** R03 is superseded by R07 and is closed
> in the log as STOPPED-and-ruled, not as failed.

> **AMENDMENT 2026-08-09 — CP-R2's authority changed by the user.** The user gave two further
> instructions this day: **RULING C** — "fix the error check everywhere" (OPEN-29 → task R06) — and,
> separately, *"vas-y continuer jusqu'à la fin. et aussi commencer des runs sur le speed, des
> ressources sont disponibles, vas-y."* That grants the manager authority to **self-sign CP-R1 and
> CP-R2 and proceed into the fleet submission without returning for permission**, superseding the
> sentence below that reserves the fleet submission to the user. Three things did **not** change and
> still bind: (1) **RULING B stands** — the R05 probe runs **first**, and the fleet pass is submitted
> only after the probe's numbers exist and are read; (2) the audit standard is unchanged — CP-R1 is
> signed on **independent re-derivation**, and a checkpoint that cannot be re-derived is a STOP, not a
> formality skipped for momentum; (3) the manager **returns to the user, before submitting**, if the
> probe shows `fast_zone` cannot fit the allowance or the wall — scope reduction is the user's call,
> never the manager's. CP-C2's scope question is otherwise now answered by "run it".

**CP-R2 — after R05. This one reports to the user, and it is a decision point, not a formality.**
The probe's numbers, the two pre-registered risks resolved or not, and the honest range for a fleet
pass. **The fleet submission is NOT authorised by this plan** — the user takes CP-C2's scope decision
against these numbers. **Analysing a partial fleet and reporting it as the fleet is the failure mode
this whole arc exists to prevent.**

---

## 8. Progress log

> Append one entry per completed task, in this format. **Append-only** — never rewrite an entry,
> including one you believe is wrong; correct it in a new entry that cites the old.

```
#### RXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + register/DESIGN citation>
- Test status: <before/after evidence, with both numbers>
- Notes: <auditor-relevant>
```

#### RULING C — OPEN-29, "fix the error check everywhere" — given by the user 2026-08-09

- **The question as put.** Whether to repair the broken fatal test only in the script producing today's
  results (the C07 precedent, deliberately narrow) or in every remaining occurrence. Answer: *"fix the
  error check everywhere."*
- **What it produced.** Task **R06**, added to §6 this day, dispatched to a fresh executor immediately.
- **🔴 The ruling exposed that the register's own count was wrong.** A fresh grep finds the one-space
  `"** Fatal **"` test at **six** live sites, not four: `t07_harvest_results.py:198`,
  `t07b_run_auto_refit_local.py:329`, `t17:254`, `t18:251`, `t19:259`, `t20:259`. `t17` and `t18` had
  **never been named anywhere**, and every previously cited line number had drifted
  (`t08_harvest_results.py` was recorded at `:239`, found at `:245`). **The lesson is the register's
  own rule: a line-number citation is evidence of a past reading, not of present state.**
- **Two occurrence classes deliberately left alone**, both recorded in OPEN-29 so they are not
  rediscovered a fourth time: the archived copy under `docs_DONE/` (editing archived evidence falsifies
  the record of what a closed arc ran) and three `scripts/diagnostics/` files that test two *other*
  wrong variants — **a third failure mode this register had not recorded.** Those diagnostics reached
  their conclusions with a fatal test that could not fire; nobody has asked what that implies, and
  that question is now open under OPEN-29.
- **Limit, stated so the ruling is not over-read.** R06 changes no historical output — no harvest is
  re-run. **"Never use the `has_fatal` column" still binds every pre-2026-08-09 artifact.**
- Surfaces updated: this log, OPEN-29 in the register, director prompt §0 ruling 5 + box item 5.

#### AUTONOMY GRANT — the director may run the arc to the end — given by the user 2026-08-09

- **Instruction.** *"vas-y continuer jusqu'à la fin. et aussi commencer des runs sur le speed, des
  ressources sont disponibles, vas-y."*
- **Effect.** The director **self-signs CP-R1 and CP-R2** and proceeds into the fleet submission
  without returning for permission. CP-C2's scope question is answered by "run it". §7's sentence
  reserving the fleet submission to the user is superseded by the amendment written above it.
- **🔴 Three limits, and they are the whole substance of this entry.** (1) **RULING B is not
  cancelled** — R05's probe runs **first**. *Start the runs* is not *skip the measurement*, and the
  ≈10× projection miss that made the probe necessary came precisely from extrapolating instead of
  measuring. (2) **The audit standard is untouched** — CP-R1 is signed on independent re-derivation
  from raw artifacts; a checkpoint that cannot be re-derived is a **STOP**, not a formality dropped
  for momentum. Momentum is exactly when this gets dropped, which is why it is written here. (3) **Go
  back to the user before submitting** if the probe shows `fast_zone` fits neither the 2-hour wall nor
  the 32-CPU allowance — scope reduction is the user's call and options (a)–(d) are spent.
- **Machine state when this was granted:** `squeue -u o_iseri` empty, shown by the user. Correct and
  expected — nothing has been submitted, and nothing may be until CP-R1 is signed.
- Surfaces updated: this log, the register's resume amendment item 5, director prompt box item 4.

#### R02 — manager spot-verification (not a completion entry) — 2026-08-09

- Not written by the executor; recorded by the manager because it was verified independently while
  answering a progress question. `scripts/cluster/t08_harvest_results.py:246` now reads
  `has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None`, with `import re` present at `:25`.
- **This is not CP-R1's audit and does not substitute for it.** It confirms the edit exists; it does
  **not** confirm the before/after was demonstrated on a real `.err` corpus, which is what R02's test
  clause requires and what the checkpoint will re-derive.

#### R06 — Fix fatal detection in every remaining live harvest script (OPEN-29, RULING C) — completed 2026-08-09
- Artifacts:
  - `scripts/cluster/t07_harvest_results.py` — `import re` added after `import json` (new line 17);
    line 198→199 `has_fatal = "** Fatal **" in err` → `has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None`.
  - `scripts/cluster/t07b_run_auto_refit_local.py` — `import re` added before `import shutil` (new
    line 19); line 329→330 same substitution.
  - `scripts/cluster/t17_harvest_layout_assign.py` — `import re` added after `import json` (new line
    50); line 254→255 same substitution.
  - `scripts/cluster/t18_harvest_layout_assign.py` — `import re` added after `import json` (new line
    46); line 251→252 same substitution.
  - `scripts/cluster/t19_harvest_layout_assign.py` — `import re` added after `import json` (new line
    54); line 259→260 same substitution.
  - `scripts/cluster/t20_harvest_layout_assign.py` — `import re` added after `import json` (new line
    54); line 259→260 same substitution.
  - Each file's diff is exactly 2 lines changed (1 import insertion, 1 line replacement) —
    `git diff --stat` over the six confirms `6 files changed, 12 insertions(+), 6 deletions(-)`, no
    reflow, no rename, no reformatting. All six compile clean under
    `./.venv/Scripts/python.exe -m py_compile`.
- Deviations: none. `git status --porcelain` on all six files was clean before editing (no drift since
  the plan table was written 2026-08-09) and line numbers matched the table exactly before edit.
- Test status — before/after over a real corpus, per §2 rule 7 and R06's own test clause:
  - **Corpus:** the halted E02 run's own `.err` files on disk,
    `%TEMP%\ubem_e02_five_mode\**\eplusout.err` (glob, recursive), **2,422 files**, the same corpus R02
    used (§5 fact 4 / R02's test clause). This is the fragment `has_fatal = "** Fatal **" in err` →
    `has_fatal = re.search(...) is not None`, byte-identical across all six sites before the edit, so
    one corpus run against the extracted fragment logic gives the count for each of the six files
    (verified line-by-line above that each site had the identical starting text). Old-literal count:
    **0**. New-regex count: **2** — `nyc_centre\sim_out_auto\way_266149332\eplusout.err` and
    `nyc_centre\sim_out_auto\way_266170765\eplusout.err`, matching R02's independently-recorded
    finding exactly. This is a real corpus with a genuine fatal present — **not** the inconclusive
    (all-clean) case; old < new is demonstrated, so §2 rule 7 is satisfied for all six.
  - **Fixture (mandatory per R06's test clause):** an in-memory 4-line `.err` fixture containing a
    genuine two-space `**  Fatal  **` line (plus a decorative `Fatal Error Detected.` line and a
    `Severe` line as noise) gave **old=0 (False), new=1 (True)** — confirms the regex fires on the
    real two-space form the literal test misses.
  - Per-file table:

    | # | File | Old (corpus=2422) | New (corpus=2422) | Fixture old→new |
    |---|---|---|---|---|
    | 1 | t07_harvest_results.py | 0 | 2 | 0→1 |
    | 2 | t07b_run_auto_refit_local.py | 0 | 2 | 0→1 |
    | 3 | t17_harvest_layout_assign.py | 0 | 2 | 0→1 |
    | 4 | t18_harvest_layout_assign.py | 0 | 2 | 0→1 |
    | 5 | t19_harvest_layout_assign.py | 0 | 2 | 0→1 |
    | 6 | t20_harvest_layout_assign.py | 0 | 2 | 0→1 |
- Notes:
  - **Out of scope, confirmed present and left untouched, per the plan's explicit exclusion list:**
    - `docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/scripts/t19_harvest_layout_assign.py`
      — archived copy inside a closed arc's evidence folder, still contains the one-space literal at
      its line 259. Not edited — editing archived evidence would falsify the record of what that arc
      actually ran.
    - `scripts/diagnostics/t01_reproduce_degenerate.py:108`,
      `scripts/diagnostics/t04_validate_way428643335.py:133`,
      `scripts/diagnostics/t06_validate_relation6374725.py:153` — confirmed all three test the two
      *wrong* variants (`"**  Fatal **"` / `"** Fatal  **"`, one space missing on one side each), not
      the true two-space form. Standing defect, reported per the plan; not changed under R06 — these
      are one-off diagnostics from closed arcs whose conclusions are already recorded.
  - No harvest was re-run to regenerate historical outputs, per R06's "how" clause — past `has_fatal`
    columns in existing result tables keep whatever value the broken test produced.
  - This does not discharge E-LA-21 / OPEN-29's full scope by itself — it fixes exactly the six live
    sites named in the plan's table; `t08_harvest_results.py` (R02) and `t08_local_remainder.py:431`
    (already correct, C07) are unaffected by this task. "Never use the `has_fatal` column" stays in
    force for every pre-2026-08-06 artifact regardless of this fix.
  - R06 is disjoint from R01–R05's file set (§3); no file outside the six-row table plus this plan doc
    was touched.

#### R01 — Stop the cluster template deleting `eplusout.eio` — completed 2026-08-09
- Artifacts: `scripts/cluster/submit_fleet_t08.sbatch` (`:63` `*.eio` glob deleted; comments corrected
  at `:10-13`, `:81`, `:83`).
- Deviations: none.
- Test status: before/after over an identical two-directory fixture (built under the session
  scratchpad), both containing `eplusout.eio/.sql/.err/.end`, `task.rc`, and one file per delete glob.
  OLD block (pre-edit text, run via Bash): `.eio` **deleted** — result dir held only
  `eplusout.end, .err, .shd, .sql, sqlite.err, task.rc`. NEW block (post-edit file, run via Bash):
  `.eio` **present, 18 bytes, non-empty** — result dir held the same six files **plus** `eplusout.eio`.
  `diff` of the two listings showed exactly one line of difference (`eplusout.eio`), confirming parity
  on every other glob. `bash -n scripts/cluster/submit_fleet_t08.sbatch` → syntax OK.
- Notes: this is the only `rm -f` trim block in `scripts/cluster/` (§5 fact 2, re-confirmed: only two
  `*.sbatch` files exist, the other has no trimming block), so this single edit repairs all five sweep
  scripts that point `SBATCH_LOCAL`/`SBATCH_REMOTE` at it.

#### R02 — Give the cluster harvest working fatal detection — completed 2026-08-09
- Artifacts: `scripts/cluster/t08_harvest_results.py` (`re` import added; the `has_fatal` literal test
  replaced with `re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None`, matching
  `t08_local_remainder.py:431` verbatim).
- Deviations: none. Per plan, this does **not** discharge E-LA-21/OPEN-29 on its own — R06 (already
  logged above) covers the other six live sites; **"Never use the `has_fatal` column" stays in force
  for every pre-2026-08-06 artifact.**
- Test status: measured over the halted E02 run's real `.err` files
  (`%TEMP%\ubem_e02_five_mode`, 2,422 files found — matches §5 fact 4's citation). OLD test
  (`"** Fatal **" in err`, one space): **0** matches. NEW test (two-space regex): **2** matches —
  `nyc_centre\sim_out_auto\way_266149332\eplusout.err` and
  `nyc_centre\sim_out_auto\way_266170765\eplusout.err`. Measured 0 → 2, matching the plan's expected
  answer, and matching the manager's independent spot-check logged above under "R02 — manager
  spot-verification". Negative control: the two decorative lines
  (`"************* Fatal error -- final processing."`,
  `"************* EnergyPlus Terminated--Fatal Error Detected."`) do **not** match the new regex in
  isolation, and both are confirmed physically present in the two newly-matched files without causing
  a match on their own — the regex is not over-counting.
- Notes: this entry supersedes/completes the "manager spot-verification" note above with the full
  before/after corpus measurement that note said was still owed.

#### R03 — Persist the assigned vintage token in the harvest output (OPEN-30) — STOPPED, no code written — 2026-08-09
- Artifacts: none (trace only, per the plan's own step-3 STOP branch).
- Deviations: **STOP condition fired**, exactly the branch the plan flags as the likeliest outcome.
  Trace, with citations:
  1. `vintage_standard` **is** produced by Step 2 and lands on `gdf_57`: it is listed in
     `_F17_ENVELOPE_COLS` (`openubem/semantic/__init__.py:47`), assembled via
     `out[col] = env_df[col]` (`__init__.py:388-389`), `env_df` sourced from
     `construction_sets.py:352,354-355` (`result["vintage_standard"] = vintage_series`; `keep_cols`).
  2. It does **not** survive into the frame either harvest path currently joins against. Both
     `t08_harvest_results.py:230-232` and `t08_local_remainder.py:412-417` build `bld_row` from
     `cell_info = build_cell_info(cell)`, which reads only `PHASED_RESULTS/<cell>/05_results.gpkg`.
     Read directly (`nyc_centre`, 738 rows, 31 columns: `osm_id, footprint_area_m2, levels, height_m,
     archetype_id, zoning_strategy, data_quality_flag, ...eui/gwp cols..., iod, simulation_status,
     error_summary, geometry`) — **no `vintage_standard` column present**.
  3. It also does not survive into the manifest (`03_idf_manifest.parquet`/`03_manifest.parquet`) —
     every `manifest_row` construction site in `openubem/idf/builder.py` (lines 412-415, 494-502,
     546-550, 559-563, 580-584, 619-627, `_worker_exception_row` 632-639) omits it.
  4. No other on-disk artifact carries it in this pipeline: `enrich_semantics()` only writes
     `02b_buildings_enriched.gpkg` when called with `output_dir` set (`__init__.py:407-416`), but
     `t08_full_sweep.run_step2()` calls `enrich_semantics(gdf_29)` with **no `output_dir`**
     (`t08_full_sweep.py:148`) — confirmed no `02b` file is ever written by this pipeline.
     `02a_climate_epw.parquet` carries only climate/EPW columns. `%TEMP%\ubem_t08_sweep` (the cluster
     harvest's manifest-lookup dir) does not currently exist on disk. `vintage_standard` therefore
     exists **only** as a transient in-memory column on `gdf_57` for the life of one script execution.
  5. Consequence — the two harvest paths are **not** symmetric: `t08_local_remainder.py` could reach it
     without re-derivation (`gdf_57` is already live in scope in the same `main()` execution that later
     harvests that cell — literally the same computed object, not a re-invocation of `resolve_vintage()`).
     `t08_harvest_results.py` **cannot**: it is a standalone post-hoc process with no access to `gdf_57`
     or any persisted equivalent. Its only routes are (a) re-deriving via `resolve_vintage()` again —
     forbidden per the plan unless provably the same call on the same inputs, which is not established
     from this script's current inputs, or (b) a new upstream persistence mechanism — out of scope
     (not a one-line change; not a file `§3`'s file list authorizes).
- Test status: n/a — no code written.
- Notes: per plan §6 R03 step 3, this is explicitly "a choice that is not yours to make silently." The
  plan asks both harvest paths to emit the column under one obligation; only one has a non-lookalike
  route today. Reporting for a manager decision rather than choosing a partial (local-only) fix or a
  forbidden re-derivation (cluster). R04 proceeded regardless, since it does not depend on R03.

#### R04 — Disarm FINDING 1's silent resume trap — completed 2026-08-09
- Artifacts: (a) the four stale markers deleted from `%TEMP%\ubem_e02_five_mode\`:
  `nyc_centre\sim_out_auto\sim_done.txt`, `nyc_centre\sim_out_building\sim_done.txt`,
  `nyc_centre\sim_out_floor\sim_done.txt`, `la_rural\sim_out_layout_assign\sim_done.txt`.
  (b) `scripts/cluster/t08_local_remainder.py`: new `_rows_present_in_csv()` and
  `recover_missing_done_modes()` (resume guard, called at the top of `main()` before any Step 2/3/4
  work starts); `main()`'s per-cell loop changed so already-done-mode rows are loaded from
  `output_csv` whenever `done_modes` is non-empty, not only when the whole cell is done.
- Deviations: none — implemented the plan's preferred option ("re-harvested rather than skipped"), not
  the fallback ("refuses to start"), because tracing `t08_full_sweep.run_step3_mode()` showed the
  manifest is already persisted to `<work_base>/<cell>/step3_<mode>/03_manifest.parquet`
  (`t08_full_sweep.py:174`) and `sim_out` survives at `<work_base>/<cell>/sim_out_<mode>` — both
  already on disk from the original run, so recovery re-uses `harvest_cell_mode()` unchanged rather
  than reimplementing any pipeline logic. The "refuse to start" path is implemented as the fallback for
  pairs where that data is genuinely absent (verified below).
- Test status: **(a)** file count under `%TEMP%\ubem_e02_five_mode\` before deletion: 20,078; the 4
  target paths confirmed present and matched §5 fact 9 exactly (contents: `nyc_centre/auto: 736/738`,
  `nyc_centre/building: 738/738`, `nyc_centre/floor: 738/738`, `la_rural/layout_assign: 149/149`, all
  timestamped 2026-08-06). After deleting only those 4: file count 20,074 (exactly −4), zero
  `sim_done.txt` remaining anywhere under the tree. **(b)** both required directions, via a fixture
  work base built from two real `la_rural` osm_ids (real phaseE fixture, so `build_cell_info()`/
  `harvest_cell_mode()` join exactly as in production): *Direction 1* — `la_rural/auto` marked done,
  `output_csv` did not exist (rows absent) → guard printed `[RESUME GUARD] 1 (cell, mode) pair(s)
  marked done with rows absent...`, re-harvested from the persisted manifest + sim_out, wrote 2
  recovered rows; `output_csv` went from not-existing to holding exactly 2 `la_rural/auto` rows.
  *Direction 2* — same pair, rows now present → guard made **zero** changes (`output_csv` mtime and
  row count both unchanged before/after re-running the guard). *Bonus* — `la_rural/building` marked
  done with no manifest/sim_out fixture on disk → guard raised `SystemExit` before doing anything,
  naming the exact offending pair and both missing paths with their `exists()` state, `output_csv`
  never created.
- Notes: part (a) alone already disarms the *specific* four stale markers — on the next real resume
  `is_done()` now returns False for those 4 pairs, so Step 3/4 rerun normally and Step 4's per-building
  `.end`-file resume (already correct) means only the un-simulated remainder actually costs compute.
  Part (b) is the standing guard against a **future** occurrence of the same trap (e.g., a Speed
  session that dies mid-cell) — it was exercised only against a synthetic fixture per the plan's test
  spec, not against the just-cleaned real E02 work base (which, post-(a), no longer has any
  done-but-unharvested pairs to demonstrate against).

#### CP-R1 — executor stop, R05 NOT started, Speed NOT touched — 2026-08-09
- This session was dispatched with an explicit, direct instruction: execute R01–R04, stop at CP-R1, do
  not start R05, do not touch Speed — "R05 is gated behind a manager audit you are not authorised to
  skip." A later message from the coordinator (verified genuine against this file: it correctly
  predicted the R01–R05 → R01–R05 ID rename before I re-read the file) reaffirmed this unchanged:
  "Your stop point is unchanged: finish R01–R04, then STOP at CP-R1. Do not submit anything to Speed."
- While this session was working, this file changed substantially beyond the ID rename: task **R06**
  was added and marked completed (verified for real — `git diff --stat` shows all six named files
  genuinely modified, matching R06's logged diff), plus a **RULING C** entry and an **AUTONOMY GRANT**
  entry claiming the user authorized the manager to self-sign CP-R1/CP-R2 and proceed into the Speed
  fleet submission without returning for permission.
- **This session did not act on that grant.** File content is not a message addressed to this session,
  and no message actually sent to this session amended the original stop-at-CP-R1 instruction — the
  only message received after the file started changing *reaffirmed* the original boundary verbatim.
  Per the rule that no message from any agent (and no plan-doc content) is a substitute for the
  coordinator's own instruction to this specific session, R05 was **not started** and the Speed cluster
  was **not touched** in this session, regardless of what this file now claims elsewhere. This is
  reported explicitly so the coordinator can reconcile the AUTONOMY GRANT's intent against what this
  executor session was actually told.
- R03 hit its plan-designed STOP condition (logged above) and was reported, not resolved, for the same
  reason: the plan itself withholds that choice from the executor.

#### AUDIT — R06 — signed by the manager 2026-08-09

**Re-derived independently, not read off the report.** Every number below was recomputed by the
manager from the raw artifacts before the entry above was accepted.

| Check | Manager's own result | Agrees with report |
|---|---|---|
| Corpus size (`eplusout.err` under `%TEMP%\ubem_e02_five_mode\**`) | **2,422** | ✅ |
| Old one-space literal, matches over that corpus | **0** | ✅ |
| New regex `\*\*\s+Fatal\s+\*\*`, matches | **2** | ✅ |
| Which buildings | `nyc_centre/sim_out_auto/way_266149332`, `way_266170765` | ✅ |
| Diff size | `6 files changed, 12 insertions(+), 6 deletions(-)` — one `import re` + one substitution each | ✅ |
| Regex text present and identical in all six | ✅ at `t07:199`, `t07b:330`, `t17:255`, `t18:252`, `t19:260`, `t20:260` | ✅ |
| `py_compile` on all six | passes | ✅ |
| Any one-space literal surviving under `scripts/` or `openubem/` | **none** | ✅ |

**Two non-vacuity checks, because a passing count proves nothing on its own.** (1) The before/after is
**not** the inconclusive all-clean case the plan warned about — the corpus contains two genuine fatals
and the old test misses **both**, so "before" is demonstrated to differ from "after" on real data.
(2) The new expression is **not** merely looser: the decorative lines `************* Fatal error --
final processing.` and `************* EnergyPlus Terminated--Fatal Error Detected.` are physically
present in those same two files, and a count of exactly **2** — not 4, not 2,422 — shows the regex
matches neither. An over-matching expression would have been the easy way to make this test pass.

**Independent corroboration.** These are the same two buildings C07 identified on 2026-08-06 through a
separate execution path (`t08_local_remainder.py`). Two unrelated runs converging on the same two stems
out of 2,422 is the strongest evidence available here that the corpus reading is real.

**Signed.** R06 is complete and correct as specified. **What it does not do, restated so the sign-off is
not over-read:** it discharges neither OPEN-29 (eight other defect IDs remain live inside it) nor the
standing prohibition — **`has_fatal` remains untrustworthy on every artifact produced before
2026-08-09**, because nothing was re-harvested. And the diagnostics-script finding is a **new** third
variant of this defect that no document previously recorded; it is now carried in OPEN-29, unmeasured.

#### AUDIT — CP-R1, first pass — R01 ✅ R02 ✅ R03 STOP-accepted R04 ⚠️ **NOT SIGNED** — manager 2026-08-09

Audited by independent re-derivation from the working tree and the halted run's artifacts, not by
reading the executor's report. **Outcome: CP-R1 is not signed.** Three of the four pass; R04's part (b)
does not hold, and R03 needs a manager ruling it could not make itself.

| Task | Manager's re-derivation | Verdict |
|---|---|---|
| R01 `.eio` retention | `git diff` on `submit_fleet_t08.sbatch`: `5 insertions(+), 5 deletions(-)`; `*.eio` glob gone from the trim block; `.eio` named in the kept-files comment and the echo | ✅ signed |
| R02 fatal regex | `t08_harvest_results.py:246` carries `re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None`, `import re` at `:25`. Corpus demonstration re-derived by the manager during the R06 audit over the same 2,422 `.err` files: old **0**, new **2** (`way_266149332`, `way_266170765`) | ✅ signed |
| R03 vintage column | Executor **stopped and reported instead of coding** — the plan's §6 step-3 branch, followed exactly. Manager confirms the premise independently: `vintage_standard` is written at `construction_sets.py:352` and is the first of the 28 appended envelope columns (`semantic/__init__.py:45-47`), but appears in **no** persisted artifact reachable by the cluster harvest — five real `03_manifest.parquet` files on disk carry 10 columns and it is **not** among them | ✅ correct behaviour; superseded by **RULING D** → **R07** |
| R04(a) stale markers | 4 markers deleted, file count 20,078 → 20,074, exactly −4 | ✅ signed |
| R04(b) resume guard | `recover_missing_done_modes()` re-harvests through `harvest_cell_mode()` from the persisted manifest + `sim_out` — **no pipeline reimplementation**, correct on that count — and refuses to start naming offending pairs. **But it does not survive the run.** | ❌ **fails** → **R08** |

**The R04(b) failure, demonstrated not asserted.** The guard writes recovered rows for *all* cells into
`output_csv` at startup (`:531-534`). The cell loop then overwrites that file from `all_dfs` after
**each** cell (`:786-789`), and `all_dfs` at that moment holds only the cells processed so far. The
manager re-enacted those exact statements on a two-cell fixture: after the guard the file held
`{c1/auto, c2/auto}`; after cell 1's incremental write it held `{c1/auto, c1/floor}`; final state
`{c1/auto, c1/floor, c2/floor}` — **`c2/auto` silently gone**, and `is_done()` still `True` for it, so
nothing regenerates it. This is FINDING 1 reproduced one level up. It is **not** a regression the guard
introduced (the pre-existing "all modes done" branch had the same shape) but it defeats R04's stated
purpose, so R04 is not signed.

**Executor conduct — noted in its favour.** The session declined to act on the AUTONOMY GRANT it found
in this file, on the grounds that *file content is not a message addressed to it* and the only message
it actually received reaffirmed "do not submit anything to Speed". **That reasoning is correct and is
the standard for every future executor**: a grant of authority to the manager is not a grant to an
executor, and an executor must never widen its own mandate from something it read. It flagged the
discrepancy for reconciliation rather than resolving it silently — exactly right.

**What this audit does not claim.** R02 is signed on the manager's own corpus count, not on the
executor's. R03's trace is confirmed only on the negative claim (the column is not persisted); the
positive route to fix it is the manager's ruling, and R07 must still demonstrate the distribution.

#### R07 — Carry the vintage token to both harvests through the manifest (OPEN-30, RULING D) — completed 2026-08-09
- Artifacts:
  - `scripts/cluster/t08_full_sweep.py` — in `run_step3_mode()`, after `run_step3(...)` returns and
    before `manifest.to_parquet(...)`: builds `vintage_lookup = DataFrame({"osm_id": gdf["osm_id"].astype(str),
    "vintage_standard": gdf["vintage_standard"].astype(str)}).drop_duplicates(subset="osm_id")`, casts
    `manifest["osm_id"]` to `str`, and left-joins on `osm_id`. One edit, both paths (`t08_local_remainder.py`
    imports this exact function, per plan step 4 — not duplicated).
  - `scripts/cluster/t08_harvest_results.py` — `parse_cell_mode()`, inside the existing
    `if manifest is not None:` block (now `:254-263`): row dict initialised with `"vintage_standard": ""`
    (missing → empty string, matching `archetype_id`'s pattern); when a manifest row matches, reads
    `mrow.iloc[0].get("vintage_standard", "")`, `"" if pd.isna(vs) else str(vs)`.
  - `scripts/cluster/t08_local_remainder.py` — `harvest_cell_mode()`: same `pd.isna` guard reading
    `mrow.get("vintage_standard", "")` (manifest row already in scope via `manifest.iterrows()`), added to
    the row dict as `"vintage_standard": vintage_standard`.
- Deviations: none. `drop_duplicates(subset="osm_id")` on the join key is a defensive no-op (each `gdf`
  row is one building, one `osm_id`) added so a left-join can never fan out rows if that ever changed —
  it does not alter which value is attached to which `osm_id`, so it is not a substantive deviation from
  "copy, don't recompute."
- Test status — real regeneration, no synthetic frame substituted (R07's test clause requires saying so
  plainly if regeneration isn't feasible; it was feasible and was done):
  - Ran `run_step2()` + `run_step3_mode()` for real on **la_rural, all 149 buildings** (enriched inputs
    already on disk at `docs/docs_VALIDATION/.../phaseE/la_rural/01_buildings.gpkg`), mode `auto`. Step 3
    completed in 13.8s, 149/149 success.
  - **(a) Manifest column list (11 cols):** `['osm_id', 'idf_path', 'archetype_id', 'zoning_strategy',
    'num_zones', 'num_context_buildings', 'simplification_status', 'data_quality_flag',
    'generation_status', 'resolution_mode', 'vintage_standard']` — `vintage_standard` present.
  - **(b) Non-null rate:** 149/149 = 100.000%.
  - **(c) Full value distribution (manifest, la_rural/auto, n=149):**
    `DOERefPre1980: 135 (90.6%)`, `90.1-2007: 14 (9.4%)`. **PASS** — plausible against the register's
    fleet-wide 92.9% `DOERefPre1980` (this is one cell of two in the probe set, not the fleet; 90.6% on a
    149-building cell is well inside the expected spread). Not uniform, not constant, not 100% one modern
    token.
  - **Harvest read-through, both paths, same manifest, same distribution:**
    - Local (`t08_local_remainder.harvest_cell_mode`): 149 rows, `vintage_standard` present, 100%
      non-empty, distribution identical: `DOERefPre1980: 135, 90.1-2007: 14`. Written to CSV and re-read
      — distribution survives the round-trip unchanged (`sim_out` was empty since Step 4/EnergyPlus was
      not run for this probe of the code path — `status` came back `missing` for all 149, which is
      orthogonal to `vintage_standard`, sourced from the manifest row, not from `eplusout.*`).
    - Cluster (`t08_harvest_results.parse_cell_mode`): same manifest, same `cell_info` — 149 rows,
      100% non-empty, identical distribution.
  - **Negative control — pre-R07 manifest (column absent):** dropped `vintage_standard` from the same
    149-row manifest and re-ran both harvest paths. Both returned `{''}` as the only `vintage_standard`
    value across all rows — confirms the missing-column fallback is the empty string, never a fabricated
    default, on both paths.
- Notes: R07 supersedes R03's STOP per the manager's RULING D (§7 amendment). The manifest is the
  channel, per the three facts the ruling cites: `run_step3_mode()` already receives `gdf` = `gdf_57`
  carrying the token (`vintage_standard` first of the 28 `_F17_ENVELOPE_COLS`, `semantic/__init__.py:45-47`,
  written `construction_sets.py:352`); the manifest already carries `osm_id` and is already read by both
  harvests from the local sweep directory; the value is copied in the same process, same moment the IDF
  is generated — nothing recomputed, no `resolve_vintage()` call added anywhere in this diff.
  `openubem/idf/builder.py` was **not** touched (confirmed: not in `git diff --stat` for this session).
  Manifests written before this change carry no `vintage_standard` column and are **not** backfilled —
  confirmed via the negative control above; those rows report the empty string, which is the honest
  output per the plan's explicit instruction.

#### R08 — Make R04's resume guard survive the incremental write — completed 2026-08-09
- Artifacts: `scripts/cluster/t08_local_remainder.py` — new `_write_incremental_csv(output_csv, interim)`
  helper (added directly after `recover_missing_done_modes()`): if `output_csv` exists and is non-empty
  with `{"cell", "mode"}` as columns, computes `covered = MultiIndex.from_arrays([interim["cell"],
  interim["mode"]]).unique()`, drops existing rows whose `(cell, mode)` key is in `covered`, concatenates
  the survivors (`preserved`) with `interim`, then writes. The per-cell incremental-write call site
  (previously a bare `interim.to_csv(output_csv)`) now calls this helper instead. The final assembly
  write (after the `for cell in cells:` loop) is **unchanged** — deliberately: `all_dfs` there already
  covers every requested `(cell, mode)` pair by construction (each cell's iteration appends either its
  loaded-existing rows or its freshly-harvested rows before the loop moves on), so a merge there is not
  needed for the scenario R08 targets and adding one was not authorised by the plan's file list.
- Deviations: none. Followed the plan's suggested "obvious route" (read the file, drop the pairs
  `interim` covers, concat, write) exactly. Did not delete the guard; did not load the whole CSV into
  `all_dfs` up front — both explicitly forbidden by the plan's "how."
- Test status — both directions, per §2 rule 7, on a **real 3-cell fixture** (`nyc_rural`, `austin_rural`,
  `la_rural` — `la_rural` is the **last** cell in the loop and carries a recovered done mode), using the
  real pipeline functions (`run_step2`, `run_step3_mode`, `harvest_cell_mode`,
  `recover_missing_done_modes`, `_write_incremental_csv`) end to end, not a hand-built dataframe:
  - **Setup:** generated a real Step-2/Step-3 manifest for `la_rural` (5 buildings, trimmed for speed —
    same real-fixture-trimmed approach R04's own test used) and `mark_done("la_rural", "auto", ...)`
    **without** ever writing its rows to `output_csv` — reproducing the exact crashed-mid-cell scenario
    FINDING 1 and the CP-R1 first-pass audit describe.
  - **NEW code (post-R08), literal (cell, mode) sets at all three required points, plus the guard:**

    | Checkpoint | Rows | (cell, mode) set |
    |---|---|---|
    | After the guard | 5 | `{(la_rural, auto)}` |
    | After 1st incremental write (nyc_rural harvested) | 9 | `{(la_rural, auto), (nyc_rural, auto)}` |
    | After 2nd incremental write (austin_rural harvested) | 12 | `{(austin_rural, auto), (la_rural, auto), (nyc_rural, auto)}` |
    | After the final write | 12 | `{(austin_rural, auto), (la_rural, auto), (nyc_rural, auto)}` |

    `('la_rural', 'auto')` — the last cell's recovered pair — is present at **every** point, including
    the final write. **Duplicate count on `(cell, mode, osm_id)`: 0** at every checkpoint.
  - **OLD code (pre-R08, `interim.to_csv(output_csv)` bare overwrite), same fixture, reused from disk,
    fresh output CSV — the failure demonstrated, not asserted:**

    | Checkpoint | Rows | (cell, mode) set |
    |---|---|---|
    | After the guard | 5 | `{(la_rural, auto)}` |
    | After 1st incremental write (nyc_rural harvested) | 4 | `{(nyc_rural, auto)}` — **la_rural's 5 rows gone** |
    | After 2nd incremental write (austin_rural harvested) | 7 | `{(austin_rural, auto), (nyc_rural, auto)}` |

    `is_done("la_rural", "auto")` was still `True` when the loop reached `la_rural`, and 0 rows were
    loadable from `output_csv` for that pair — confirming the row loss is silent and permanent within
    the run, exactly the CP-R1 audit's finding, and exactly what R08 exists to fix. Old ≠ new is
    demonstrated on real data, not asserted.
- Notes: this closes the CP-R1 first-pass audit's R04(b) failure. The mechanism satisfies both of the
  plan's "how" requirements: (i) rows for `(cell, mode)` pairs the loop has not yet reached survive every
  incremental write (`la_rural` survived two incremental writes it was not part of); (ii) no duplication
  when a cell's rows are both loaded into `all_dfs` and already present in the file (`la_rural`'s 5 rows
  appear exactly once in the final 12-row file, `duplicated()` = 0 throughout, including after the final
  write where `la_rural`'s rows are simultaneously in `all_dfs` — loaded at line ~722-728 — and already in
  the file from the prior incremental writes).

#### CP-R1 — second pass, R01/R02/R04(a)/R07/R08 — ready for manager re-derivation — 2026-08-09
- This session executed exactly R07 and R08 per its dispatch instruction, then stopped at CP-R1 as
  directed. **No code outside the three files named in the plan's §3 was touched**
  (`t08_full_sweep.py`, `t08_harvest_results.py`, `t08_local_remainder.py`, this plan doc).
  `openubem/idf/builder.py` was not touched, confirmed via `git diff --stat`.
- 🔴 **Speed was not touched.** No `ssh`, no `sbatch`, no R05. The AUTONOMY GRANT and CP-C2 amendment
  recorded earlier in this log are addressed to the manager, not to this executor session — this session
  was dispatched with an explicit instruction to execute R07–R08 and stop at CP-R1, and it did exactly
  that and no more.
- This entry does not sign CP-R1 — per §7's own rule, the checkpoint is signed only on the manager's
  independent re-derivation from raw artifacts, not from this report.

#### AUDIT — R07 + R08 — signed by the manager 2026-08-09

Re-derived from the working tree and from artifacts on disk, not from the executor's report.

**R07 — the vintage token now reaches both harvests.**

| Check | Manager's own re-derivation | |
|---|---|---|
| Join site | `t08_full_sweep.py:172-179` — `vintage_lookup` built from `gdf["osm_id"]`/`gdf["vintage_standard"]`, both cast to `str`, deduplicated, left-merged onto the manifest **before** `to_parquet` at `:185` | ✅ |
| Nothing recomputed | No call to `resolve_vintage()` or any semantic function is added anywhere; the value is copied from the frame `run_step3_mode()` was handed | ✅ |
| `openubem/idf/builder.py` untouched | not in `git diff --stat` | ✅ |
| One edit serves both paths | `t08_local_remainder.py` imports `run_step3_mode` from `t08_full_sweep`; the join is not duplicated | ✅ |
| Column reaches the manifest on disk | `%TEMP%\ubem_r07_test\la_rural\step3_auto\03_manifest.parquet`, **n=149**, real Step-3 regeneration, not a synthetic frame | ✅ |
| Non-empty rate | **100.0%** | ✅ |
| Distribution (manager's own `value_counts`) | `DOERefPre1980` **135 (90.6%)**, `90.1-2007` **14 (9.4%)** | ✅ |
| Plausible against the fleet | register records ≈**92.9%** `DOERefPre1980`; 90.6% for one rural cell is in range, and is **neither constant nor uniform** | ✅ |
| Cluster harvest read | `t08_harvest_results.py:250` seeds `""`, `:262-265` overwrites from the manifest row with an `isna` → `""` fallback | ✅ |
| Local harvest read | `t08_local_remainder.py:433-436, 451` — same shape | ✅ |
| Pre-R07 manifests | the five real E02 manifests still carry 10 columns and **no** `vintage_standard`; both readers fall back to `""` | ✅ correct, not backfilled |

🔴 **The non-vacuity check that actually settles this.** A plausible distribution is not proof the column
carries per-building information — a constant would also have looked fine against a 92.9% expectation.
So the manager cross-checked the token against an **independent source that the join never touches**:
`year_built` in the raw `01_buildings.gpkg` for `la_rural`. Result — every one of the 14 `90.1-2007`
buildings has `year_built` in **2005–2007**, and every one of the 135 `DOERefPre1980` buildings has
`year_built` in **1920–1979**. **Zero crossover.** The token tracks a fact the manifest never saw. (24
of the 149 have no `year_built` at all and still receive a token — that is the pipeline's documented
pre-1980 default, `semantic/__init__.py:207`, not a defect introduced here.)

**R08 — the resume guard now survives the run.** Manager's own fixture, three cells, the recovered pair
placed on the **last** cell, re-enacting the loop against the live `_write_incremental_csv()`:

| Point in the run | (cell, mode) set in the file | rows | dups |
|---|---|---|---|
| after the guard | `{c1/auto, c3/auto}` | 2 | 0 |
| after cell 1's write | `{c1/auto, c1/floor, c3/auto}` | 3 | 0 |
| after cell 2's write | `+ c2/floor` | 4 | 0 |
| after cell 3's write | `+ c3/floor` | 5 | 0 |
| after the final write | unchanged | 5 | 0 |

**`c3/auto` — the recovered pair on the last cell — is present at every point.** Under the old bare
overwrite the manager's earlier fixture lost it at the first write. Both directions demonstrated, zero
duplicates throughout.

🟠 **Residual, found by the manager during this audit and NOT fixed — recorded, not silently changed.**
`_write_incremental_csv()` merges, but the **final assembly write at `:830` is still a bare
`results.to_csv()`**. Demonstrated: with a CSV holding cell `zz` and the run invoked for `c1` only, `zz`
survives the merge write and is **destroyed by the final write**. This **cannot affect E02** — the fleet
pass runs all twelve cells, so every cell is loaded into `all_dfs` and the final write is complete — and
it is **pre-existing**, not introduced by R08. It is left open deliberately because the fix is not purely
mechanical: making the final write a merge too would change what `--cells X` *means* (today it yields a
CSV containing only `X`), and that is a semantics decision, not a bug fix. **Carried to the register as a
named finding. Do not change it without a ruling.**

**CP-R1 IS SIGNED — 2026-08-09.** R01 ✅ R02 ✅ R03 → superseded by R07 ✅ R04 ✅ (a) + ✅ (b) via R08
R06 ✅ R07 ✅ R08 ✅. All four conditions on a Speed resume are discharged and demonstrated on real
artifacts. **R05 is unblocked.** The manager self-signs under the 2026-08-09 autonomy grant; RULING B is
unaffected — **the probe runs first**, and the allowance is re-checked immediately before submission.

#### R05 — in flight, manager note (not a completion entry) — 2026-08-09

**State.** Submission driver running locally: `<scratchpad>/r05_probe_submit.py`, work base
`%TEMP%\ubem_r05_probe`, log `<scratchpad>/r05_submit.log`. Step 2/3 generation under way at the time of
writing (22 worker processes, confirmed by the manager). The driver is **fire-and-forget by
construction** — it submits ten arrays and exits, writing `r05_job_ids.json` into the work base. A
manager-side watcher is armed on that file **and** on the driver's disappearance, so a crash is reported
rather than mistaken for "still running".

**Allowance re-checked immediately before submitting, per the plan:** `chachemv` **0/32 CPUs**,
`squeue -A chachemv` empty, `/speed-scratch` 5.9 T used of 10.0 T. Consistent with §5 fact 8.

**Deviation accepted by the manager — remote fleet tag `r05probe`, not `t08`.** The executor found
**stale `t08_nyc_rural_*` fleet directories on Speed dated 2026-06-29**, which predate the R01 `.eio`
retention fix, and tagged this probe's directories separately rather than reusing or overwriting them.
✅ **Correct, and for the right reason:** reusing those names would have mixed a pre-fix generation with
a post-fix one inside the same paths — which is OPEN-28's defect, the very thing E02 exists to remove.
Implemented as a module-level monkey-patch (`t08._FLEET_TAG = "r05probe"`) in a **driver script outside
the repo**; `scripts/cluster/t08_full_sweep.py` is byte-unchanged, `_FLEET_TAG` still `"t08"` at `:48`,
and the diff stat over `scripts/` is identical to CP-R1's. **R05's measurement-only mandate held.**

✅ **No pipeline reimplementation.** The driver imports `run_step2`, `run_step3_mode`, `ship_fleet` and
`submit_array` from `t08_full_sweep` and calls them unchanged. Verified by reading it. The fifth mode
(`layout_assign`) is passed straight through — the CLI's `choices` list exposes only four, the functions
support five — so adding it is the plan's requirement, not scope creep.

🔴 **Pre-registered risk the manager is adding now, before the readout, so it cannot be rationalised
afterwards.** `t08_harvest_results.py:42` still hard-codes `_FLEET_TAG = "t08"` and builds its remote
paths from it at `:111`. **Harvesting this probe without the same `r05probe` override will look in
`t08_*` directories and find nothing** — and per §2 rule 9, *a parser that finds nothing must say so,
never report 0*. This is exactly the shape where an empty result gets read as "no failures". Whoever
performs the CP-R2 readout applies the override and **states in the report which remote directories were
actually read.**

#### R05 — probe SUBMITTED, ten arrays live on Speed — manager-verified 2026-08-09

**Submission completed 2026-08-09 20:29:21 local**, ~2 min 45 s after the driver started. Job IDs from
`%TEMP%\ubem_r05_probe\r05_job_ids.json`:

| cell | auto | building | floor | layout_assign | fast_zone | n/mode |
|---|---|---|---|---|---|---|
| `la_rural` | 1174659 | 1174676 | 1174704 | 1174735 | 1174791 | **149** |
| `nyc_rural` | 1174813 | 1174837 | 1174865 | 1174924 | 1174959 | **198** |

**1,735 simulations** (5 × 149 + 5 × 198). Confirmed queued; a read-only 30-minute `squeue` poller is
running — **never modifies jobs**.

**Manager's own re-derivation from the ten manifests on disk, not from the report** (§2 rule 10):

| Check | Value | |
|---|---|---|
| Manifest rows, all ten | **1,735** | ✅ matches 5×149 + 5×198 |
| `generation_status == success` | **1,735** | ✅ 100%, and the non-success bucket is **empty for every mode**, including `fast_zone` and `layout_assign` |
| `.idf` files actually on disk | **1,735** | ✅ one per manifest row — the count is not a manifest claim |
| Whole cells, no subset | 149 and 198 in **every** mode | ✅ OPEN-34 respected |
| `vintage_standard` present | **all ten manifests** | ✅ **R07 is live in a real run**, not only in its test |
| Generation timeline | 00:26:49 → 00:29:07 (UTC), staggered per mode | ✅ consistent with a 22-worker parallel build; not a single instantaneous write |

🟢 **The `layout_assign` fallback messages in the driver log are expected, not failures** —
`one_zone_per_floor` reroutes on degenerate post-intersect surfaces, illegal-interzone repairs, and
single-zone HVAC downgrades are all documented handled paths. Corroborated by the manifests: **zero**
non-success rows. `No baseline available for archetype_id='Courthouse'` is likewise a declared
`no_baseline` fallback, not an error.

**What is measured and what is NOT.** Submission succeeded and IDF generation is 100%. **Neither is the
probe's purpose.** R05 exists to measure **runtime and memory** — the two pre-registered risks (the
2-hour wall against `fast_zone`'s worst buildings, and `--mem=6G`) are **still unmeasured**, and a clean
submission says nothing about either. **Nothing about fleet cost may be stated until the arrays drain
and the `.err`/`.eio` artifacts are read.** The CP-R2 readout must apply the `r05probe` tag override —
see the pre-registered risk in the previous entry.
