# DIRECTOR PROMPT — resume and close the LayoutAssigner storey-matching sub-arc

> Written 2026-07-27 at the point the user parked the project to work elsewhere.
> Paste this whole file into a **fresh Opus/Fable manager session** when returning to OpenUBEM.
> You are the **manager/director**: you write plans, dispatch fresh Sonnet employees, audit their
> reports, and sign checkpoints. **You do not write feature code.**

---

## 0. One-paragraph situation

The `layout_assign` resolution mode's storey-matching sub-arc (open question **Q3**) is in its final
stretch. All implementation is done and audited (**CP-D signed 2026-07-26**, with three binding
conditions carried forward). The 12-cell / 8,160-building **T20 cluster fleet re-run finished on
2026-07-27 and its results have never been harvested.** What remains is: harvest the fleet (R06b),
regenerate the cross-mode figures (R09), close the documentation (R08), and sign **CP-E** — the final
checkpoint of the sub-arc. Two ready-to-dispatch executor prompts already exist for exactly this.

**Nothing is blocked. No decision is owed by the user. Drive this to CP-E.**

---

## 1. Read these, in this order, before doing anything

1. `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_REMAINder.md`
   — **the single source of arc state** (1,080 lines). Read at minimum:
   - §1 Hard rules (line 33)
   - §3 tasks **R06** (183), **R07** (198), **R08** (224), **R09** (238)
   - §4 Stop-and-report points (284) and §4-bis in-flight note (296)
   - the **CP-D audit** at line 944 — especially §2 (the vacuous 1.0000× heating ratio), §3
     (`r10_results.csv` is not citable), §4 (R10 shrinks the expressible population), and
     **§5 the three conditions binding on R06** (1018)
   - the **IN-FLIGHT NOTE — R06** at line 1041 — *"R06 is NOT complete; no R06 progress-log entry
     exists yet"*
2. `...\storey-Matching\prompt\EXECUTOR_PROMPT_R06b_harvest.md` — ready to dispatch as-is.
3. `...\storey-Matching\prompt\EXECUTOR_PROMPT_R09_R08_closure.md` — ready to dispatch after R06b is
   audited and accepted.

**Do NOT read** `DONE_PLAN_storey-matching_implementation.md` (CLOSED, ~3,500 lines) or the other
closed plans end-to-end. Grep them by `F-nn` / `E-LA-nn` ID and read only the surrounding lines.

---

## 2. Verified cluster state as of 2026-07-27 — the T20 fleet is COMPLETE

Confirmed by the director with login-node-only commands (`squeue`, `sacct`):

- `squeue -u $USER -h | wc -l` → **0**. Nothing pending, nothing running.
- `sacct -u $USER -S 2026-07-25 -X -P -o JobName,State | grep t20_` → all 12 cells present:

| Cell | COMPLETED | FAILED |
|---|---:|---:|
| nyc_urban | 1 779 | 0 |
| nyc_suburban | 1 589 | 0 |
| nyc_centre | 738 | 0 |
| nyc_rural | 195 | **3** |
| la_suburban | 1 343 | 0 |
| la_urban | 615 | **3** |
| la_centre | 225 | **1** |
| la_rural | 149 | 0 |
| austin_suburban | 437 | 0 |
| austin_urban | 425 | 0 |
| austin_centre | 413 | 0 |
| austin_rural | 245 | 0 |
| **Total** | **8 153** | **7** |

8 153 + 7 = **8 160**, the exact known fleet size — no task is missing. SLURM-level failure rate
0.086%. **These 7 SLURM-level FAILED tasks are distinct from simulation-level success** and must each
be mapped to a known defect ID (or explained) in the R06b report — do not let them be silently
absorbed into the success-rate arithmetic.

Re-verify this yourself with the two commands above before dispatching (the queue may have been
touched while the project was parked). **Do not re-submit the fleet.**

---

## 3. Critical path to close

```
R06b (harvest + 7 items)  →  [director audit]  →  R09 (figures)  →  R08 (docs)  →  CP-E signed
```

R07 is **already reduced** to a written statement folded into R08 — no new figure panel. Reinstate it
in full **only if** R06 turns out to have changed geometry.

### Step 1 — Dispatch R06b (fresh Sonnet employee)

Send the employee to `prompt\EXECUTOR_PROMPT_R06b_harvest.md` and have it execute that prompt
top-to-bottom. It must confirm the arrays via `sacct`, run
`scripts/cluster/t20_harvest_layout_assign.py`, finish `scripts/cluster/t20_r10_reach_change.py`
across all 12 cells, and report **seven items** — none optional:

1. Fleet success rate vs T19's **97.92%**, with every remaining failure mapped to a known defect ID
   (including the 7 SLURM failures above).
2. F-08's heating ratio re-measured on the **`eio`-true, multiplier-aware** floor-area denominator —
   the measured pair **must have at least one side with status `applied` and residual multiplier ≥ 2**,
   or the measurement is a tautology (this is exactly how R05 produced its vacuous 1.0000×).
3. D9 `transformer_scale_ratio` sweep: Severe counts + energy effect on F-11's **805 exposed
   buildings** across the multiplier range.
4. CP-D condition (b): status-change count at fleet scale (preliminary read on 2 of 12 cells /
   2,244 buildings gave **4 buildings changed, all Highrise/MidriseApartment, all
   `applied → fallback_not_expressible`**).
5. Applied-population denominator assertion.
6. E-LA-36 fleet regression + the **R10 reach change** (see trap below).
7. A **fleet-scale re-measurement of the inert share** — the old 81.6% (nyc_suburban) / 98.4%
   (la_suburban) figures are stale and must not be reprinted anywhere.

**The three traps to restate when you dispatch:**

- **F-08 tautology.** If the fleet contains no qualifying pair, the employee must **say so
  explicitly** rather than substitute a degenerate one.
- **Reimplemented "before" side.** `t20_r10_reach_change.py` computes its pre-R10 side by
  *reimplementing* the old formula, not by running the old code. Either declare that plainly in the
  progress-log entry, or take the "before" side from the pre-R10 git commit. A reimplementation must
  never be presented as measured output of the old pipeline.
- **`eio` provenance.** Ground truth is raw `eplusout.err` (outcome) and `eplusout.eio`
  (multiplier-aware floor area) — never `.end`, never a nominal `footprint × num_floors` computed in
  the harness. A previous harness in this arc shipped a CSV whose `eio` columns were all `0.0` while
  its report cited them as proof. **Hand-verify the parser against one raw file before trusting it
  across 8,160.**

**Hard stops for the employee:** a fleet success rate below 97.92% for an unmapped reason, or any
inability to distinguish a real simulation failure from a harness failure. Both are STOP-and-report,
not things to patch around. `T_ENGAGE = 0.868` and `T_MASS_MAX = 0.35` stay **frozen** — a fleet
failure reopens the fix plan, never the constants.

### Step 2 — Audit R06b yourself

Re-derive the headline numbers from the raw `t20_*` harvest CSVs, not from the employee's report.
That has been the standing practice at every checkpoint in this arc and it has caught a real defect
almost every time (E-LA-24, E-LA-30, E-LA-31, the fabricated `.eio` line at CP-A). Check in
particular that any `eio_*` column is non-zero and genuinely parsed, and that the F-08 pair is not
degenerate.

### Step 3 — Dispatch R09 + R08 (a second fresh Sonnet employee)

Send it to `prompt\EXECUTOR_PROMPT_R09_R08_closure.md`, R09 first then R08, in one pass. Key points
to restate:

- **Archive before overwrite.** The five `layout_assign_vs_modes_*` figures, their summary CSV and
  `README.md` are R09's named deliverables and DO get regenerated — but only after the current
  versions are copied to `openubem/outputs/comparisons/previous/*_t19.*`, exactly as the T17 set was
  preserved when T19 landed. **This is the *only* exception to the figure freeze** — everything else
  under `layoutAssigner\figures\` (the four viewers, `before_viewer_enrich\`, `before_B05\`,
  `before_B08b\`) stays untouched, and the exception must not become a pretext to widen the edit.
- Four mandatory explicit statements on the figures/README: harvest provenance labelled on **each
  side** of every figure; the EUI denominator convention stated **per mode**; Figure 3 (severity)
  frozen unless rebuilt from real `eplusout.err`; the never-validated-against-metered-data caveat
  survives **verbatim**, unsoftened. And: **E-LA-22 still stands**, so T20-vs-T19 deltas are not
  cleanly attributable to this arc — say so on the figures, not only in prose.
- **R08's disclosure list is headline main text, not a footnote.** That was the explicit price of the
  R04 option-(a) decision. Eight items, all disclosed plainly — see the executor prompt for the full
  list, but the three added ones matter most: R10's *measured* reduced scope (never the stale
  81.6/98.4%), **R03's PV/generator invariance is synthetic-fixture only** with no real-run evidence,
  and **E-LA-36** — a silent ~50% storey over-count on the dominant archetype, found and fixed inside
  this arc — told frankly, including what it would have cost.
- R08 must update the results doc §3/§3a, `PROJECT_CHECKLIST.md` §L, **and Q3's own entry in
  `DONE/DONE-implementation_plan.md` §7** — Q3 is closed by this arc or it is not closed at all.

### Step 4 — Sign CP-E

**CP-E is the director's to sign, never the employee's.** Append the audit entry to §5 of the
REMAINder plan. Per the standing autonomy instruction, the manager self-signs checkpoints; the user
does not need to be asked.

---

## 4. Hard rules (both director and employees)

- 🔴 **NEVER run compute on the Speed login node** (`speed-submit2` / `speed.encs.concordia.ca`).
  `squeue`, `sacct`, `ls`, `mkdir`, `scp`, `tar` only. Anything needing Python goes through
  `sbatch` fire-and-forget, then read the output file. No `srun`, no `ssh … python …`.
- **Never cancel, requeue or deprioritise any cluster job**, least of all another project's.
- **Never `git commit`** — the user's own tooling handles git.
- Never edit root `main.py`, any OVERVIEW or DESIGN doc, or `MEMORY.md`.
- Progress-log and AUDIT entries are **append-only** — never rewrite a frozen entry.
- Working directory `C:\Users\o_iseri\Desktop\OpenUBEM`; interpreter `./.venv/Scripts/python.exe`.
- All `.png` outputs go flat to `openubem/outputs/` **and** are mirrored into `docs_ACTIVE/<arc>`.
- The plan doc is the single source of state — **dispatch a fresh Sonnet session per unit of work**,
  never resume an old one for new work, and never rely on an employee's conversation memory.
- Tell every employee up front to **poll artifacts on disk** rather than waiting to be woken by a
  background process. Employees in this arc have stalled that way four separate times.
- The user writes in **French**; **answer in English** (set 2026-08-04, supersedes the earlier
  reply-in-French convention). Every deliverable (plans, docs, READMEs, reports) in **English**.
  Keep chat answers short.

---

## 5. What is NOT in scope here

Forwarded out of this sub-arc, open but non-blocking — record them at CP-E, do not fix them:

- **E-LA-21** — `has_fatal` tests `"** Fatal **"` (one space) against EnergyPlus's `"**  Fatal  **"`
  (two): `False` on all 8,160 rows.
- **E-LA-22** — local re-runs of a past fleet generation diverge in archetype *and* vintage for
  data-poor buildings. This is why no clean T20-vs-T19 comparison exists.
- **E-LA-23** — `thermal_mass=True` drives `CheckWarmupConvergence` severes (matched control: 8/150
  vs 96/150). Cosmetic-only, `status` unaffected.
- **E-LA-24** — a prior artifact used as a control instead of a matched in-run control.
- **E-LA-25** — the prototype registry's `baseline_area` disagrees with the prototype IDFs' own
  geometry for 14 of 25 archetypes (up to +473%), so `S = real_area / baseline_area` is wrong before
  `√S` is ever taken. Upstream of everything this arc touched.
- **E-LA-37** — editing the `ZoneGroup`'s own Zone List Multiplier would restore exact expressibility
  at every `n_real`. Different mechanism from D3(a); R04 is closed at option (a).

Also out of scope: building **height** (explicitly, per R04(a) — `layout_assign` matches thermal-zone
topology and plate geometry, not height), and the ~29% cross-mode EUI gap, roughly half of which is
by design (internal loads come from `ASHRAE901_*_STD2022` prototypes regardless of real vintage).

---

## 6. After CP-E

Once CP-E is signed, the **whole LayoutAssigner arc returns to PARKED** — every sub-arc (main,
debug-fixes, structural-fixes, E-LA-20 investigation, E-LA-20 fix, storey-matching) is then closed.
At that point:

1. Update `docs/PROJECT_CHECKLIST.md` §L to reflect the closure.
2. Update the `project_layout_assigner_arc` memory entry to a thin pointer + the generalizable
   lessons only — task-level detail stays in the plan doc.
3. Ask the user which arc to open next; do **not** self-select a new arc.
