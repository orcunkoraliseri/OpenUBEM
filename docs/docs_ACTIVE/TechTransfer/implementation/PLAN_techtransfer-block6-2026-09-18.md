# PLAN — TechTransfer block 6 (successor to block 5)

**Slug:** techtransfer-block6 · **Date:** 2026-09-18 · **Manager-authored.** Executors append to §4 only.

**Predecessor:** `PLAN_techtransfer-block5-2026-09-17.md` (🔒 CLOSED 2026-09-18, lane J done, no open
items inside that block).

**Opened by:** user decision 2026-09-18 — close block 5 / open block 6 — approved as "housekeeping
only": this doc is parked, no task is authorized to start yet.

---

## 1. State at open

Per `docs/docs_ACTIVE/TechTransfer/Prompt/PROMPT_MANAGER_techtransfer_2026-09-18.md` §2, ten of eleven
report items are done or parked by design. Everything shipped so far stays behind default-OFF flags;
nothing is wired into the build path; no published OpenUBEM number has moved. Test baseline at open:
108 passed across the eight TechTransfer test files (command in the prompt-manager doc header).

## 2. Parked tasks — none may start without a specific user ask, item by item

| Item | What it is | Gate |
|---|---|---|
| C04 | Per-archetype per-end-use regression fixture (block 1, lane C leftover) | User must ask for C04 by name. |
| Wire `pv.py` | Connect the PV library into the build path | User must ask; ruled out deliberately at SR-H2. |
| Wire `openubem/scenarios/` | Connect the retrofit measure applier into the build path | User must ask; ruled out deliberately at block 5 §1c. |
| Flip `ENVELOPE_PATCH_SKIP_WHEN_BETTER`, `PREP_ABORT_ON_FAILURE`, `PV_INJECTION_ENABLED`, `SCENARIO_LAYER_ENABLED` | Turn any of the four flags on (`openubem/config.py:112,123,223,224`) | User must ask; flipping any one changes simulation behaviour. |
| Any EnergyPlus run for this arc | Nothing here has been simulated | User must ask; when approved, `sbatch --array ...%32` on Speed or a local pool of 20 — never sequential. |
| D9 | The prototype IDF library that lives inside idf_reader | Out of scope per §0 ownership rule; not to be pulled in. |
| Warehouse `auto`-mode IDF failure | Pre-existing, known, out of scope | Not part of this arc. |
| Racking / `Shading:Building:Detailed` for PV | Inter-row shading | Not started; no ask yet. |
| Rewrite OpenUBEM's table-driven envelope applier | — | Not started; no ask yet. |
| Write to `05_results` | Published 70-entry schema | Not touched on a blanket go-ahead. |
| T11 benchmark anchors / heat pumps | Waits for a Canadian district case or heat-pump scenario | Parked by design, nothing to do. |

## 2a. Execution authorized 2026-09-18 — run the list, item by item, no per-item ask

User instruction: "put them in a list and follow them by executing consecutively, no need to ask my
opinion." This authorizes running the in-scope items of §2 in sequence without stopping to pick
between them. It does not authorize reversing a deliberate ruling (SR-H2 for PV, §1b of block 5 for
scenario packaging) or moving the published fleet number — those still need the one specific input
named below, not a style-of-work choice.

**Order:**
1. **C04** — regression fixture. No wiring, no flag, no simulation risk. Runs first. Full task spec
   below.
2. **PV validation run** — SR-H2's own stated condition to ever revisit wiring: one real EnergyPlus
   run on one PV-injected prototype IDF, completing without a fatal and reporting non-zero generation.
   This is a single standalone run, not build-path wiring — in scope to execute now.
3. **Wire `pv.py` into the build path (flip `PV_INJECTION_ENABLED`)** — gated on item 2 succeeding
   *and* is still a build-path change with a fleet-wide compute cost; report item 2's result before
   this one runs.
4. **Wire `openubem/scenarios/` into a campaign** — gated on one input only I cannot pick: the
   packaging design (cumulative ladder vs. isolated single-domain runs vs. full factorial), stated in
   block 5 §1b as the user's compute-budget call (8,139 × 16 cells vs. × 5). Everything built so far
   is packaging-agnostic, so this step waits for that one answer and does not block items 1-3 or 5-6.
5. **Flip `ENVELOPE_PATCH_SKIP_WHEN_BETTER`, `PREP_ABORT_ON_FAILURE`** — no dependency on PV/scenarios;
   runs after C04, audited individually (each changes simulation behaviour).
6. **Any fleet-scale EnergyPlus run** — only after 2-5 land; `sbatch --array ...%32` on Speed, never
   sequential, case count stated before submission per CLAUDE.md cluster rules.

Out of scope, not part of this execution order: D9 (idf_reader's own prototype library — ownership
rule), Warehouse auto-mode bug (pre-existing, unrelated arc), PV racking/shading, envelope-applier
rewrite, `05_results` write, T11 benchmark anchors — these stay parked exactly as §2 states.

### Task C04 — Per-archetype, per-end-use regression fixture (report order 1, carried from block 1 lane C)

**What.** A golden table (archetype × end use) written from a current sample run, plus a test that
compares a fresh run against it and reports **which archetype and which end use moved**, not just a
pass/fail.
**Why.** In the source project an engine upgrade moved one archetype's gas use by **+56.6 %** while the
fleet total looked fine. A fleet-level regression check would have missed it.
**How.** Sample ≥ 12 buildings over ≥ 4 archetypes; run **in parallel** (never sequential — Speed
32/local 20 per CLAUDE.md). Store the golden under `tests/reference/` if that is where the repo's
existing goldens live — check first; if not, ask.
**How to test.** Test passes against its own golden; deliberately perturb one value and confirm the
failure message names the archetype and the end use.
**Gate.** None — cleared to start now.

### Task SCEN-01 — Full-factorial campaign definition (report order 10 / T5, campaign-design half)

**What.** A pure-data/pure-function campaign generator inside `openubem/scenarios/`: given the 3 active
measures (`lighting_power_density`, `thermostat_setback`, `infiltration_tightening`), produce the 8
cells of the full factorial (baseline + every non-empty subset of the 3, i.e. all 2³ combinations), each
cell as an explicit, named tuple of which measures are ON. No cell may silently omit a combination.
**Why.** Packaging decision resolved below (§2b): Option C, full factorial, so every combination must
exist as an addressable unit before any campaign can ever be submitted.
**How.** A function that takes the measure table already shipped (`openubem/data/scenarios/measures.json`,
active entries only — `envelope_u_upgrade` stays excluded, withdrawn) and returns the 8 cells, each with
a stable name (e.g. `baseline`, `lighting`, `setback`, `infiltration`, `lighting+setback`, …,
`lighting+setback+infiltration`) and the ordered list of measure keys to apply for that cell. Applying a
cell's measures to an IDF must go through the existing applier — this task does not add a second way to
call a measure. **No EnergyPlus run. No `05_results` write. No viewer change. Not imported from
`openubem/idf/`, `openubem/geometry/`, `openubem/campaign/` or `openubem/simulation/`** — same
build-path isolation rule as lane J (block 5 §2 rule 3). The only importer is the test.
**How to test.** One test asserts exactly 8 cells, no duplicates, and that the all-three cell's applied
IDF is identical (byte-for-byte after mutation) whether measures are applied in any of the 3! possible
orders, to prove cell definition is order-independent even though a single call still applies its
measures in a fixed internal order. One test that applying a cell twice (idempotence) matches applying
it once, reusing the idempotence proof each measure already carries individually.
**Gate.** None — packaging decision is resolved (§2b). Cleared to start now, in parallel with C04.

### Task PV-VAL — PV validation run (report order 2, SR-H2's own stated re-visit condition)

**What.** One standalone EnergyPlus run on one real prototype IDF with PV injected via
`openubem/idf/pv.py`'s existing `inject_pv`, called directly by a throwaway script/test — **not**
through the build path and **not** behind `PV_INJECTION_ENABLED` (that flag stays OFF; this task does
not flip it). Confirm the run completes without a fatal and reports non-zero PV generation.
**Why.** SR-H2 (block 4) refused to wire PV "for now, not forever," naming this exact proof as the
condition to ever revisit that refusal. This task only produces the proof; it does not act on it —
wiring (`PV_INJECTION_ENABLED`) is task 3, gated on this one succeeding, and is a separate ask.
**How.** Use `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` (already used in `tests/test_pv_injection.py`
and the C04 sample) as the one prototype. Load it, call `strip_existing_pv` then `inject_pv` exactly as
the existing unit tests do, then run it once through `openubem/simulation/runner.run_energyplus`
(single case — not a fleet run, so the cluster parallel-array rule does not apply; CLAUDE.md's rule
targets *multiple* simulations). Read the result via `classify_outcome` for the fatal/severe check, and
read the `Generator:PVWatts` meter/output (e.g. `Electricity:Facility` production or the generator's own
report variable already exposed by EnergyPlus for `Generator:PVWatts`) for the non-zero generation
check.
**How to test.** A single pytest test (marked the same way the existing `energyplus`/`slow` tests in
this repo are marked, skip if the EnergyPlus binary is absent) that asserts zero severe/fatal errors
and generation `> 0`. This is the proof artifact itself — do not just run it manually and report a
number; commit the test so the proof is reproducible.
**Gate.** None — cleared to start now. Report the pass/fail and the generation number before task 3 (PV
wiring) is even considered; a fatal or zero-generation result here means SR-H2's refusal stands and
task 3 does not proceed.

### Task PV-WIRE (item 3) — wire `pv.py` into the build path, flip `PV_INJECTION_ENABLED`

**What.** Call `strip_existing_pv` then `inject_pv(idf, enabled=config.PV_INJECTION_ENABLED)` from
`openubem/idf/builder.py` at the same point envelope work happens (both the `layout_assign` branch,
around line 566, before `write_outputs`, and the generic per-building branch's own pre-`write_outputs`
point), so every building built after this lands carries the check regardless of which branch it takes.
Then flip `PV_INJECTION_ENABLED: bool = False` → `True` in `openubem/config.py:223`.
**Why.** Gate condition named in the PV-VAL task above is now met: one real run, zero fatal, ~140,312
kWh/yr generated — see the PV-VAL progress-log entry.
**How.** `inject_pv` already takes its own `enabled` bool (default `False`) — the wiring call must pass
`config.PV_INJECTION_ENABLED` explicitly, never hardcode `True`, so the call is a no-op while the flag
is off and only the final config edit turns it on. Do not duplicate `strip_existing_pv`/`inject_pv`'s
own logic in builder.py — call the existing functions only.
**How to test.** Run the full existing suite with the flag flipped on; any previously-passing test that
now fails because a `Generator:PVWatts` object appears where it did not before is a real, expected
consequence of turning PV on fleet-wide — report it plainly, do not silently edit a golden to make it
pass. Add one builder-level test: with the flag on, a built IDF for a building with a qualifying roof
carries a `Generator:PVWatts` object; with a throwaway flag-off build, confirm it does not.
**Gate.** PV-VAL passed — cleared to start now.

### Task SCEN-WIRE (item 4) — wire `openubem/scenarios/` into a campaign

**What.** An orchestration function (in `openubem/scenarios/`, not `openubem/campaign/` — that
directory is EU-arc-specific machinery, unrelated domain, do not reuse or extend it) that, given a small
manifest of already-built baseline IDFs, applies each of the 8 cells from `build_full_factorial_campaign`
to a fresh copy of each building's IDF via the existing `apply_cell`, and writes each resulting IDF to
disk under a per-cell subdirectory, with a manifest row recording which building, which cell, and the
output path.
**Why.** Packaging decision is resolved (§2b); SCEN-01 built the cell *definitions* only, proven
order-independent and idempotent on a single in-memory IDF — nothing yet produces real per-building,
per-cell IDFs on disk through an actual build-path call.
**How.** No EnergyPlus run in this task — fleet-scale execution is item 6, separately gated on the
`05_results` write-slot question that is still unresolved. No `05_results` write. Take 2-3 sample
baseline IDFs (reuse ones already used elsewhere in this repo's tests, e.g. from the C04 sample or
`tests/test_pv_injection.py`'s prototypes) so the test is self-contained and fast.
**How to test.** One test that, for the sample buildings, all 8 × N output IDFs exist, are distinct
files, and that the `baseline` cell's output is byte-identical to the unmodified input IDF (proving the
baseline cell is truly a no-op). No live EnergyPlus run required for this task.
**Gate.** None — packaging decision resolved, cleared to start now.

### Task FLAGS-05 (item 5) — flip `ENVELOPE_PATCH_SKIP_WHEN_BETTER` and `PREP_ABORT_ON_FAILURE`

**What.** Flip both flags from `False` to `True` in `openubem/config.py:112` and `:123`. Both call
sites already exist and are already exercised by existing tests with the flag on
(`tests/test_envelope_patcher_windows.py`, `tests/test_compliance_audit.py`, `tests/test_scenario_measures.py`
for the envelope flag; `tests/test_prep_gate.py` for the prep flag) — this task is a config-only change,
no new wiring code.
**Why.** No dependency on PV or scenarios; authorized to run now per §2a's own stated order.
**How.** Two separate one-line edits. Flip and commit them as two distinct, individually-reported
changes (not one combined edit) since each changes simulation behaviour independently — CLAUDE.md
requires each flag flip be audited on its own.
**How to test.** Run the full existing suite after each flip; confirm nothing that passed before now
fails. Report any behaviour change plainly (e.g. envelope patches now skipped where the baseline was
already better; simulation phase now aborts instead of continuing past generation failures).
**Gate.** None — cleared to start now.

## 2b. Packaging decision resolved 2026-09-18 — Option C, full factorial

User routed the decision in `2026-09-18_DECISION_scenario-packaging-for-gemini.md` to Gemini and
relayed its answer: **Option C, full factorial**, all 2³ = 8 combinations of the 3 active measures
(baseline, each single, each pair, all three), reasoning being that a cumulative ladder cannot be
converted to a fair per-measure ranking after the fact and isolated runs cannot answer combined-measure
questions, while the factorial cost here is only 2x either simpler option (3 measures, not a larger
catalogue). At 8,139 buildings that is **65,112 total EnergyPlus runs** if and when a fleet campaign is
ever submitted (still not authorized — see below).

**What this unblocks now:** item 4 of §2a, building the 8-cell campaign definition inside
`openubem/scenarios/`, in-memory and testable exactly like the measure table and applier already
shipped — no EnergyPlus run, still behind `SCENARIO_LAYER_ENABLED` (default OFF), nothing written to
`05_results`.

**What this does not unblock:** item 6, the real 65,112-run fleet campaign. `05_results` write and any
viewer change are separately gated in §2 above ("not touched on a blanket go-ahead") and neither is on
the authorized-execution list. Running EnergyPlus at that scale before there is a sanctioned place to
write its output means the compute produces nothing usable. Flagging this now rather than submitting a
65k-run cluster job with nowhere for the results to land.

## 2c. `05_results` write-slot resolved 2026-09-18 — item 6 authorized

User authorized the `05_results` write-slot (previously the one open question blocking item 6) and
instructed the remaining list be run to the end without further per-item asks.

**Baseline/PV fork — resolved by user 2026-09-18.** `PV_INJECTION_ENABLED` (flipped True by FLAGS-05's
sibling task PV-WIRE) is a build-path flag, not a scenario measure: every IDF built through
`openubem/idf/builder.py` now gets PV injected where eligible, including the campaign's `baseline` cell
(campaign cells only ever add *measures* on top of an already-built IDF — the underlying build call is
unchanged). Left as-is, the fleet campaign's `baseline` cell would silently stop matching the adopted
**153.95 kWh/m² / 8,139-building** figure (`[[project_current_baseline]]`), since that figure was
computed before PV existed on the build path. **Ruled: the `baseline` cell of this campaign only must be
built with `PV_INJECTION_ENABLED=False` (a local override at the point of that one cell's build call, not
a global flag flip back to False); the other 7 cells build with the flag at its current value (`True`),
so retrofit-vs-no-PV is not what those cells measure — they measure retrofit-vs-baseline-with-solar
already on.** This keeps 153.95 as the campaign's own reference point and is the only branch that does
not silently restate a published number as a side effect of an unrelated flag flip.

### Task FLEET-06 (item 6) — fleet-scale EnergyPlus campaign, full factorial, 8,139 buildings x 8 cells

**What.** Three sequential sub-steps, each with its own progress-log entry (FLEET-06a/b/c), not one
combined task — this is the largest and least reversible task in this arc.

**FLEET-06a — build the 65,112-case manifest and the IDFs on disk. No EnergyPlus run in this sub-step.**

**Correction 2026-09-18 (post first attempt).** The first FLEET-06a dispatch stopped correctly and
reported two real conflicts in the "How" below — verified independently by re-reading the code before
this correction (not just trusting the report):
`openubem/scenarios/campaign_runner.py:69-70` loads a pre-built IDF file with `GeomIDF(...)` and only
applies retrofit measures on top — it never reads `config.PV_INJECTION_ENABLED` or calls `pv.py`. PV is
baked in only once, at IDF-build time, inside `openubem/idf/builder.py:572,701`
(`inject_pv(self.idf, enabled=config.PV_INJECTION_ENABLED)`), so "call `run_campaign()` with PV as
currently set" was never something `run_campaign()` could do — the original wording below is wrong and
is superseded by this correction. Also confirmed: the local `%TEMP%\ubem_validation\t06_rebuild_2026-09-09\<cell>\step3\idfs\`
copies are empty; the real T07 baseline IDFs only exist on Speed at
`/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/idfs/` (8,152 files, confirmed present via
`ls` over ssh).
- **How.**
  1. **Baseline scenario cell** — fetch (scp/rsync only, login node allowed for file transfer, never
     compute) the T07 baseline IDFs for the 8,139 usable building IDs (from
     `openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv`, the T08-successful population)
     from `/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/idfs/` on Speed. Use these files
     **unmodified** — they were built 2026-09-09, before PV existed on the build path, so they already
     have zero PV objects; do not rebuild them, do not pass them through `builder.py` again.
  2. **The 7 non-baseline scenario cells** need a *different* starting IDF per building: one built by
     today's code (so `PV_INJECTION_ENABLED=True` and this arc's other flipped flags are baked in). This
     is not "rebuilding the fleet from scratch" — reuse the existing, precedented, no-live-fetch rebuild
     path: `scripts/analysis/t06_cell_rebuild_2026-09-09.py`, run once per one of the 12 geographic cells
     (same launcher pattern as `scripts/analysis/t06_fleet_rebuild_2026-09-09.py`, all 12 in parallel,
     never sequential). It seeds each cell's frozen `evidence/open48_refleet/<cell>/01_buildings.gpkg`
     (no live OSM fetch), re-runs Step 2 classify/enrich and Step 3 IDF generation (`BuildingIDF(row).build(...)`,
     `openubem/idf/builder.py:473`) on today's code, and writes fresh per-building IDFs, local only, no
     EnergyPlus. Restrict the result to the 8,139 usable building IDs (same T08 csv as above) before
     using them. This step is genuinely new compute (13 building-days ballpark of local IDF-text
     generation only, not simulation) — if it looks like it will take materially long, report the
     measured per-cell time after the first cell finishes rather than guessing.
  3. For each of the 8,139 usable buildings: run `openubem.scenarios.campaign_runner.run_campaign()`
     (already shipped by SCEN-WIRE, unmodified) once per non-baseline cell, starting from that building's
     fresh today's-code IDF from step 2 above. The `baseline` cell is not run through `run_campaign()` at
     all — it is exactly the fetched T07 IDF from step 1, copied into the manifest as-is (zero measures,
     zero PV, matches 153.95 by construction, no `PV_INJECTION_ENABLED` override/monkeypatch needed
     anywhere — that mechanism from the original wording is no longer needed since the two IDF sources
     are already separate).
  Write one combined manifest (building_id, cell_name, output_idf_path) covering all 8 x 8,139 = 65,112
  rows. **State the exact resulting case count before FLEET-06b submits anything** (cluster rule).
- **How to test.** Row count == 8 x (usable fleet population); no duplicate (building_id, cell_name)
  pairs; spot-check N=5 buildings' `baseline`-cell IDF for zero PV objects, and N=5 buildings'
  non-baseline-cell IDFs for the PV object present when the building is PV-eligible per `pv.py`'s own
  eligibility rule; spot-check N=5 buildings' non-baseline starting IDFs (before measures) against their
  own `baseline`-cell IDF to confirm they differ only in PV presence and any other flipped flags, not in
  geometry/floor area. No live EnergyPlus run.
- **Gate.** None — cleared to start now (corrected spec above).

**FLEET-06b — submit the array job to Speed.**
- **How.** Adapt `submit_fleet_t07.sbatch` / `t07_submit_resim.py` (same precedent as FLEET-06a) for
  65,112 tasks: `sbatch --array=1-65112%32 --time=7-00:00:00`, output per (cell, building_id) under a
  per-cell subdirectory, never sequential, never on the login node. State total case count (65,112) and
  parallel width (32) in the progress-log entry before submission, per CLAUDE.md's cluster rules.
  Poll >=30 min apart; do not `srun`/`ssh ... python` on the login node to check progress.
- **Gate.** FLEET-06a's manifest count confirmed correct.

**FLEET-06c — harvest into `05_results`, one output per cell, unmodified 70-column schema.**
- **How.** Run the existing Step 5 harvest (same schema/pipeline already published,
  `docs/docs_main/docs_step-5/DESIGN_step-5-...md` lines 166/186-193 — 70-column GeoDataFrame, GPKG
  canonical + GeoJSON + CSV, flag-don't-drop) once per cell, each into its own
  `<cell_name>/05_results.*` output — **no schema change, no new column for "cell"** (cell identity is
  the directory, matching how baselines/scenarios are already partitioned in this arc, e.g.
  SCEN-WIRE's own `output_dir/<cell_name>/...` convention). Cross-cell comparison/viewer work is out of
  scope for this task.
- **How to test.** 8 output directories, each internally passing the existing Step 5 QC (row count ==
  fleet population, 70 columns, schema sidecar present); `baseline` cell's fleet EUI figure sanity-check
  against 153.95 (same population, same PV-off build) — report the delta plainly, do not silently accept
  a mismatch.
- **Gate.** FLEET-06b's array job reaches 100% COMPLETED/FAILED (no task left PENDING/RUNNING).

## 2d. FLEET-06b array-split decision resolved 2026-09-18 — sequential chained array jobs

The plan's exact `sbatch --array=1-65112%32` command cannot be submitted: Speed's SLURM caps a single
array job at 10,000 tasks (`MaxArraySize=10001`, confirmed by the FLEET-06b executor via `scontrol show
config`), so 65,112 tasks must be split across multiple array jobs. Resolved by extending CLAUDE.md's
existing 32-concurrent account-wide cap to the multi-job case, not inventing a new rule.

**Ruled: split into 7 array jobs, chained to run strictly one after another via SLURM
`--dependency=afterany:<previous_job_id>`, each submitted at `--array=1-N%32 --time=7-00:00:00`.**
Because only one job's array is ever active at a time, total concurrent tasks across the whole fleet
never exceed 32 — the account-wide cap is respected exactly, not diluted across jobs (splitting the
throttle instead, e.g. `%5` x 7 concurrent jobs, would leave CPUs idle whenever job sizes/durations
differ and adds complexity for no benefit here). Contiguous manifest slices, in row order: 6 jobs of
9,302 rows + 1 job of 9,300 rows = 65,112. Each job's output stays under the same per-cell/per-building
subdirectory scheme already staged. State the split (job sizes, chain order, dependency IDs, Speed job
IDs) in the FLEET-06b progress-log entry before it is marked complete.

## 2e. FLEET-06b execution-mode decision resolved 2026-09-18 — local only, Speed jobs withdrawn

**User decision 2026-09-18:** withdraw the Speed jobs for this run and finish it on local resources
only. Reason given: the cluster allocation is needed for other, unrelated jobs right now and this run
is not urgent. This explicitly reverses CLAUDE.md's "parallel, Speed first" default — recorded here so
the reversal is not mistaken for a lapsed rule later. Both Speed jobs (job 1 of the §2d chain and its
dependent job 2) were cancelled (`scancel -n openubem_fleet06b -u o_iseri`), confirmed empty via
`squeue`. Job 1's partial Speed results (8,538 of 9,302 rows COMPLETED, 565 FAILED, 199 stuck) are
discarded, not harvested: 73% of the "COMPLETED" tasks finished in under 30 seconds, too fast for a
genuine annual EnergyPlus run, so the pass rate is suspect and re-running locally is simpler than
auditing a mixed-provenance partial result.

**Ruled: FLEET-06b now runs locally**, reusing the manifest and all 65,112 IDFs FLEET-06a already built
(`%TEMP%\ubem_validation\fleet06a_campaign_2026-09-18\manifest_65112.csv` and its per-cell IDF trees) —
no rebuild. Local concurrency cap: 20 (CLAUDE.md); the precedent local runner
`scripts/campaign/run_eu_certified_rerun.py` used `max_workers=14` on this same machine — check
achievable concurrency, don't assume 20 without measuring.

**Mandatory first step, per the debug reference at
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1595`** ("Local-CPU-scaled wall-clock
extrapolations for cluster runs are unreliable — two recorded ~10x misses"): do not estimate total
runtime from the Speed timing above (also unreliable — see the 30-second anomaly). Run a small real
local benchmark (~20-40 cases, full EnergyPlus runs, not the cheap IDF-text timing already measured in
FLEET-06a) first, measure actual local per-case wall time and the concurrency actually achieved, and
report that measured number before committing to the full 65,112-case run.

**Not time-critical.** The user flagged this as low priority against other work on the same machine;
do not treat this as an urgent dispatch, and yield machine resources if the user reports needing them.

## 2f. FLEET-06b execution-mode decision reversed 2026-09-23 — move remaining cases to Speed

**User decision 2026-09-23:** the local run is loading the user's machine too hard; move whatever is
left over to Speed. This is the "fresh ask" §2e required before any resubmission — §2e's local-only
override is superseded from this point on, not retroactively (the ~61.7k cases already finished
locally stand as-is, not re-run).

**State at the moment of this decision** (`%TEMP%\ubem_validation\fleet06b_local_2026-09-18\
progress.json`, 2026-09-23 09:45:01): done=61,739, failed=29, remaining=3,373, total=65,112 (94.8%
complete). Only the remaining ~3,373 cases move to Speed — not a full re-split of the whole fleet.
Because 3,373 is far under both the 10,000-task SLURM array ceiling (§2d) and needs no multi-job
chain, **§2d's 7-job chain plan no longer applies**: this is a single `sbatch --array=1-N%32
--time=7-00:00:00` job.

**Ruled — task spec for the executor:**
1. Read current `results.csv` / `progress.json` under `fleet06b_local_2026-09-18\`; do not restart
   from zero.
2. Stop the local run cleanly: confirm no in-flight write (progress.json ticking), then end/delete the
   `OpenUBEM_FLEET06b` scheduled task and confirm no `fleet06b_local_run_2026-09-18.py` python.exe
   remains (`Get-CimInstance Win32_Process -Filter "Name='python.exe'"`).
3. Derive the exact remaining `(cell_name, building_id)` set from `results.csv` using the same
   completion check the local runner itself uses (`openubem.simulation.parallel.is_completed()` /
   `classify_outcome`), not just the last `progress.json` count.
4. On Speed (no login-node compute): verify the 2026-09-18 staged directory
   `/speed-scratch/o_iseri/openubem/fleets/fleet06b_2026-09-18/` (idfs, weather, fleet.lst, out/) is
   still intact via `ls`/`wc -l` through the `_ssh()` wrapper. If scratch was purged, re-stage only the
   remaining IDFs from the local `fleet06a_campaign` tree (small tarball, not the original 65,112).
5. Write `fleet_remaining.lst` (same 3-column format as `fleet.lst`) containing only the remaining
   pairs; adapt `submit_fleet06b.sbatch` / `fleet06b_submit_2026-09-18.py` to read it.
6. Submit one `sbatch --array=1-N%32 --time=7-00:00:00` job (N = remaining count at submit time,
   re-measured, not assumed to still be 3,373).
7. Monitor event-driven / ≥30 min polling (`sacct`, not login-node compute) — no bare `srun`/`ssh …
   python`.
8. Harvest finished Speed rows into the same `results.csv` schema as the local rows, reconcile against
   `progress.json`, update the live monitor artifact (`https://claude.ai/artifact/6H6xkLiazkjN2akF6wsXKa`,
   collection `fleet06b`, doc `progress`).
9. Close out once all 65,112 original cases are COMPLETED/FAILED (local ~61.7k + Speed remainder) —
   gate for FLEET-06c is 100% reached, not just the Speed job finishing. State the total case count and
   parallel width before submitting, per the cluster rule. Append the real FLEET-06b progress-log entry
   under §4, correcting the stale "STOPPED 2026-09-18" one.

**How to test:** `results.csv` has exactly 65,112 unique `(cell_name, building_id)` rows, 0 remaining;
baseline cell's fleet EUI sanity-checked against 153.95 kWh/m² with the delta stated plainly.

## 2g. FLEET-06b tail resubmitted + FLEET-06c spec amendment — manager, 2026-09-24

**User 2026-09-24:** "if there are any parallel work to do, lets go do it … continue till the end" (user
asleep; this is the fresh "go" §7i of the prompt-manager doc required).

**Tail resubmitted.** The 15 unfinished rows (`fleet_rerun28.lst` lines 14-28: way_425993519 ×1 cell,
way_427278443 ×7, way_281344894 ×7) written to `$F/fleet_rerun15.lst`; the two partial `out/` dirs left by
the cancelled tasks deleted by explicit list (0 remain); **job `1348381`**,
`sbatch --array=1-15%32 --mem=32G --time=7-00:00:00 --export=ALL,FLEET_DIR=$F,FLEET_LST=fleet_rerun15.lst
submit_fleet06b.sbatch` (sbatch file untouched). At submit: 4 RUNNING, 11 PENDING `AssocGrpCpuLimit`
(account at its 64-CPU cap, other projects' jobs untouched).

**Parallel prep (no gate crossed):** (a) the 3,358 Speed-finished case folders pulled back into the local
`fleet06b_local_2026-09-18\out\` (old local failed attempts moved, not deleted, to `out_superseded_local\`);
(b) baseline-cell EUI re-parsed with the T08 `_parse_sql` into the scratchpad only, compared with 153.95.

**FLEET-06c spec amendment (manager ruling, attributable to the manager):** the §2 FLEET-06c text says
"one output per cell". A scenario cell spans 12 geographic cells in 3 states and `aggregate_results()`
(`openubem/results/__init__.py:72`) is built per neighbourhood (one state, one UTM CRS). So the harvest runs
`aggregate_results()` once per **(scenario cell, geographic cell)** pair and writes
`<root>\<scenario_cell>\<geo_cell>\05_results.*` — cell identity is still the directory, schema untouched.
- **Root:** `%TEMP%\ubem_validation\fleet06c_harvest_2026-09-24\` (local, never under `docs/`, not committed).
- **Inputs:** sims = `fleet06b_local_2026-09-18\out\<scenario_cell>\<stem>\`; building/IDF attributes =
  `fleet06a_rebuild_2026-09-18\<geo_cell>\` (`01_buildings.gpkg`, `02a_climate_epw.parquet`,
  `step3\03_idf_manifest.parquet`); population = the 8,139 stems of
  `openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv` (its `cell` column = geo cell).
- **`.sql.gz`:** `parse_building_sql()` does not read gzip; decompress each to a temp copy, parse, delete the
  copy. Never modify anything under `out\`.
- **Order:** harvest the `baseline` cell first, report, and stop for manager audit; the other 7 cells run only
  after job `1348381` ends and its 15 folders are pulled.
- **How to test:** per (scenario, geo) dir: row count == that geo cell's share of the 8,139, 70 columns,
  schema sidecar present; baseline area-weighted fleet EUI vs 153.95 with the delta stated plainly;
  non-baseline cells: count of buildings with PV output > 0 reported.

**Amendment 2g-1 (manager, 2026-09-24, after the executor's quoted conflict):** the 70-column contract
(`aggregate_results()` = the 57-column Step-2 enriched table + 13 metrics, `docs/docs_main/docs_step-5/`
DESIGN :166) cannot be met from the inputs above: FLEET-06a computed Step 2 in memory and never saved it, and
the `run_r3_step5.py` proxy table gives 38 columns. Ruling: rebuild the 57-column table per geo cell by
calling `step2_classify_enrich()` (`scripts/validation/v12_cell_pipeline.py:225`, the same function the
rebuild used via `t06_cell_rebuild_2026-09-09.py:69`) on `fleet06a_rebuild_2026-09-18\<geo_cell>\01_buildings.gpkg`,
with `work_base` pointed at `<root>\_step2\<geo_cell>\` so the rebuild's own `02a_climate_epw.parquet` is never
overwritten. Step 2 is seeded (`openubem/semantic/__init__.py:233`) and its code is unchanged since
2026-09-10 (`9d6026af`), so it must reproduce what the IDFs were built from. **Guard, before any harvest:**
per geo cell, `archetype_id` of the rebuilt table equals `03_idf_manifest.parquet`'s `archetype_id` for 100 %
of shared `osm_id`s; any mismatch → STOP and report. Save the table once per geo cell as
`<root>\_step2\<geo_cell>\02_enriched.gpkg` and reuse it for all 8 scenario cells.
- **Measured before this ruling:** baseline cell re-parse = 153.9501287 kWh/m² over 8,139 (published
  153.9501286; 0 buildings differ by > 0.01 kWh/m²) after 5 baseline cases with a stale success marker and a
  truncated result file were re-run locally (old folders moved to `out_superseded_local\baseline\<stem>_stale_2026-09-24`).

## 2h. FLEET-06c floor-area fix, full harvest, then cleanup — manager, 2026-09-25

**User 2026-09-25 (verbatim):** "yes of course, count district hot water. secondly, as we close all the
simualations colelct the results update the tables, then delete unnecessary files of the simulations to
prevent low memory warning". Two rulings: (1) district hot water **is counted** in the FLEET-06 tables
(`dhw_district_eui_kwh_m2` stays inside `total_eui_kwh_m2`, as `aggregate_results()` already does);
(2) after every table is written and audited, the large per-case simulation files are deleted (§2h-4).

**Audit of the first baseline harvest (manager, measured 2026-09-25):** 175.74 kWh/m² vs published 153.95.
- +20.09 = district hot water, now counted by ruling (1). Not a defect.
- Floor area: 8,134 of 8,139 rows `footprint_fallback`. Cause: locally-run case folders hold no
  `eplusout.eio`, and for `.sql.gz` cases the harvest parses a temp copy whose folder has no eio either;
  `resolve_simulated_floor_area()` (`openubem/results/parser.py:496-525`) then falls back to footprint.
- The 0.8 % energy shortfall (129 buildings) has the same root: `parse_building()` reads the per-zone
  multiplier map from the same eio (`parser.py:984-994`, OPEN-60); with no eio every multiplied zone's
  lighting/equipment is counted once.
- **The SQL holds the same data.** `Zones` table: `SUM(FloorArea*Multiplier*ListMultiplier) WHERE
  IsPartOfTotalArea=1` gave 142,456.77 m² vs eio 142,457.04 m² on `lighting+setback+infiltration/way_425993519`
  (eio rounds to 2 decimals; relative difference 2e-6).

### Task FLEET-06c-FIX — SQL fallback for simulated floor area and zone multipliers

- **What.** In `openubem/results/parser.py` add two readers on the SQL `Zones` table and use them only when
  the eio route fails:
  1. `parse_sql_zone_area(sql_path) -> float` = `SUM(FloorArea*Multiplier*ListMultiplier)` over rows with
     `IsPartOfTotalArea=1`; 0.0 on any error.
  2. `parse_sql_zone_multipliers(sql_path) -> dict[str, float]` = `{UPPER(ZoneName): Multiplier*ListMultiplier}`;
     `{}` on any error.
  3. `resolve_simulated_floor_area()`: every path that today returns `"footprint_fallback"` while `sql_path`
     is not None first tries (1); if > 0 return `(area, "sql_simulated")`. eio stays first; footprint stays last.
  4. `parse_building()` at `:984-994`: if the eio map is empty (missing file or parse failure) and `sql_path`
     exists, use (2).
- **Why.** The published denominator is the simulated multiplier-aware area (ruling 6 / OPEN-01, T08 used
  eio). The SQL carries the identical quantity, so cases without an eio keep the same denominator and the
  same OPEN-60 scaling. Where an eio exists, behaviour is bit-identical to today.
- **How to test.** New tests in `tests/test_results_denominator.py` and `tests/test_parser_open60_multiplier.py`
  using a small synthetic sqlite file with a `Zones` table (columns `ZoneName, FloorArea, Multiplier,
  ListMultiplier, IsPartOfTotalArea`): area with multipliers and one excluded zone; provenance
  `sql_simulated` when no eio; eio still wins when present; footprint when neither; multiplier map keys
  upper-case. Then run both files plus `tests/test_parser_version_robustness.py`, all must pass.
- **Doc.** Register in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (symptom: "8,134 of 8,139 rows
  `floor_area_provenance = footprint_fallback`; fleet area 23.42 M m² vs 23.87 M m²").

### Task FLEET-06c-BASE — re-run the baseline harvest, stop for audit

- **How.** Delete only `<HARVEST_ROOT>\baseline\` (keep `_step2\` and `_diag_38col_2026-09-24\`), then
  `python scripts/analysis/fleet06c_harvest_2026-09-24.py --cells baseline`.
- **How to test (report each line with the measured value):** 8,139 rows over 12 geo dirs; 0 rows with
  `floor_area_provenance = footprint_fallback`; fleet area vs T08 23,871,481.58 m² (must agree within 0.01 %);
  buildings whose area differs from T08 by > 0.1 % (must be 0); fleet EUI **excluding**
  `dhw_district_eui_kwh_m2` vs 153.9501 (must agree within 0.05 kWh/m²); fleet EUI **including** district
  (the new FLEET-06 baseline figure); buildings whose non-district kWh differs from T08 `total_kwh` by > 0.1 %.
- **STOP** and report after this task.

**Manager audit of FLEET-06c-BASE (2026-09-25, re-measured from disk): ACCEPTED.** 8,139 rows / 12 geo /
88 cols; 0 dups; 8,139 matched to T08; 0 `footprint_fallback`; area 23,871,478.15 vs 23,871,481.58 m²;
0 buildings with area > 0.1 % off; 0 null `total_eui_kwh_m2`. EUI incl. district **172.4076**, excl. district
**152.6985** vs T08 153.9501. The −1.2516 kWh/m² miss is a **T08 double count, not a harvest defect**:
- On the 129 buildings (all kitchen/plug-refrigeration archetypes) the whole gap decomposes into cooking
  −22.500 GWh + refrigeration −7.378 GWh = −29.879 GWh (equipment −2.602 is offset exactly by the new
  `elevators` column +2.602); 29.879 GWh / 23.87 M m² = 1.2517 kWh/m².
- `way/55932517` (FullServiceRestaurant) SQL meters: `InteriorEquipment:Electricity` 403,548 kWh (= T08 and new
  equipment), `InteriorEquipment:NaturalGas` 200,416 (= new cooking), `Cooking:InteriorEquipment:Electricity`
  178,140, `Refrigeration:InteriorEquipment:Electricity` 145,125. T08 cooking 378,556 = 200,416 + 178,140 and
  T08 refrigeration 145,125 — both are **sub-meters of `InteriorEquipment:Electricity`**, already inside
  equipment. `Electricity:Facility` 610,592 = equipment + lights + cooling + fans exactly; T08 total 1,230,639
  exceeds the building's own metered energy (907,374 + district 51,878 = 959,252 = new total).
- The current parser (`openubem/results/parser.py:681-682`: cooking = gas meter only, refrigeration =
  `Refrigeration:Electricity` compressor racks only) is correct. Published 153.95 therefore carried +1.25 of
  double count and −19.71 of missing district hot water (OPEN-65); the FLEET-06 baseline is 172.41.
- FLEET-06c-ALL is released.

### Task FLEET-06c-ALL — harvest the 7 scenario cells (after manager audit of FLEET-06c-BASE)

- **Gate.** All 65,112 case folders have a success `eplusout.end` and an `eplusout.sql` or `.sql.gz`
  (manager checks after the 15-folder pull; state the count).
- **How.** 7 processes in parallel, one per cell (`--cells <cell>`), each writing only its own
  `<HARVEST_ROOT>\<cell>\` and its own gz temp dir. Never sequential.
- **How to test, per cell:** 8,139 rows over 12 geo dirs, column count equal to baseline's, schema sidecar
  in each geo dir, 0 `footprint_fallback`, 0 null `total_eui_kwh_m2`, count of buildings with PV output > 0,
  fleet EUI including district and the change vs baseline in kWh/m² and %.

### Task FLEET-06c-TABLE — one summary table

- `openubem/outputs/comparisons/fleet06c_scenario_summary_2026-09-25.csv`: one row per scenario cell —
  n buildings, fleet area, fleet EUI including district, fleet EUI excluding district, change vs baseline
  (kWh/m², %), n buildings with PV > 0. Pooling = `sum(kWh)/sum(area)`, same population in every row.

### §2h-4 — Cleanup (runs only after FLEET-06c-ALL and FLEET-06c-TABLE are audited by the manager)

- **Inclusion list only, never exclusion** (memory: 2,761 results lost 2026-09-22). Delete, per case folder
  under `fleet06b_local_2026-09-18\out\` and `out_superseded_local\`, exactly these names:
  `eplusout.sql`, `eplusout.sql.gz`, `eplustbl.htm`, `eplusout.shd`, `eplusout.csv`, `eplusout.mtr`,
  `eplusout.eio`. Keep `eplusout.end`, `eplusout.err`, logs. Also delete the harvest gz temp dirs.
- **Before deleting:** confirm no process writes under `out\` (no `energyplus.exe`, no gzip, no harvest
  running); measure free space before and after and state both.
- Not touched: `05_results` harvest outputs, the input IDF/weather folders, anything on Speed.

## 3. Standing rules carried forward

Unchanged from block 5 §5–§6 of the prompt-manager doc: audit by measurement against a real DOE
prototype IDF, never by report; a `Schedule:Compact` measure ships a test copied verbatim from a real
prototype block; a cited standard's own figure may not be restated by an OpenUBEM convention;
withdraw don't tune; the manager owns its own spec's defects; register every solved error in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before closing a task; fail closed with a named
gate; close this doc too if it passes ~1,100 lines.

## 4. Progress log

#### SCEN-01 — Full-factorial campaign definition — completed 2026-09-18

**Artifacts:** `openubem/scenarios/campaign.py` (new — `Cell` namedtuple, `active_measure_ids()`,
`build_full_factorial_campaign()`, `apply_cell()`), `tests/test_scenario_campaign.py` (new, 8 tests).

**Deviations:** none from the task's "How". `apply_cell()` applies each cell's measures by
delegating to `measures.apply_measure()` only — no second way to call a measure. Cell names use a
curated short-label map (`lighting`, `setback`, `infiltration`) since none of the 3 full measure ids
shorten to those forms mechanically; this mapping is not specified elsewhere in the repo, so it was
authored to match the task's own example names exactly.

**Test status:** `python -m pytest tests/test_scenario_measures.py tests/test_scenario_campaign.py -q`
-> `........................................................  [100%]` / `56 passed in 2.85s` (48
pre-existing measures tests unchanged + 8 new campaign tests, zero failures).

**Notes:** The 8 cells (baseline + all 2**3 combinations of the 3 active measures, `envelope_u_upgrade`
excluded as withdrawn): `baseline` (none), `lighting` (`lighting_power_density`), `setback`
(`thermostat_setback`), `infiltration` (`infiltration_tightening`), `lighting+setback`,
`lighting+infiltration`, `setback+infiltration`, `lighting+setback+infiltration` (all three).
`build_full_factorial_campaign()` fails closed (raises `ValueError`) if the active measure set in
`measures.json` ever stops matching exactly these 3 ids, rather than silently building a partial
campaign — covered by
`test_build_full_factorial_campaign_rejects_mismatched_active_table`. Order-independence proved by
applying the all-three cell's measures in all 3! = 6 orders on fresh fixtures and comparing
`idf.idfstr()` byte-for-byte (`test_all_three_cell_is_order_independent`); idempotence proved by
applying the same cell twice via `apply_cell()` (`test_applying_a_cell_twice_matches_applying_it_once`).
Verified `openubem/scenarios/campaign.py` is not imported from `openubem/idf/`, `openubem/geometry/`,
`openubem/campaign/` or `openubem/simulation/` (`grep -rn "openubem\.scenarios" openubem/idf/
openubem/geometry/ openubem/campaign/ openubem/simulation/` -> no matches); the only importer is
`tests/test_scenario_campaign.py`. No EnergyPlus run, no `05_results` write, no viewer change. No new
error encountered, so no new entry in `OpenUBEM_debug_References.md`.

#### SCEN-WIRE — Wire `openubem/scenarios/` into a campaign — completed 2026-09-18

**Artifacts:** `openubem/scenarios/campaign_runner.py` (new — `ManifestRow` namedtuple,
`run_campaign()`, `_write_manifest_csv()`), `tests/test_scenario_campaign_wiring.py` (new, 4
tests).

**Deviations:** none from the task's "How"/"How to test". `run_campaign()` takes a list of
`(building_id, baseline_idf_path)` pairs, loads each baseline IDF fresh per cell (never reuses
a mutated IDF across cells), calls `campaign.apply_cell()` only — no second way to apply a
measure — and saves each result to `output_dir/<cell_name>/<building_id>.idf`, writing
`output_dir/manifest.csv` (building_id, cell_name, output_path) alongside the returned list of
`ManifestRow`. Used the 2 prototypes already used in `tests/test_pv_injection.py`
(`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`, `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`,
both under `config.BASELINE_IDF_DIR`) — no new fixtures. One deviation in the "How to test"
mechanics only: literal byte-comparison of the baseline cell's saved output against the
*original on-disk prototype file* fails, because geomeppy/eppy's `saveas()` reserializes the
IDF (whitespace/field layout) even with zero measures applied — this is a round-trip artifact
of the save pipeline, not something `apply_cell()` controls. Fixed by comparing the baseline
cell's output against a fresh load-then-`saveas()` of the same prototype with no measures
applied at all (same serializer, zero measure calls either way); this isolates the variable
under test (does `apply_cell` with an empty cell change anything) exactly as the task intends,
and is the same technique SCEN-01 already used (`idf.idfstr()` round-trip comparison rather
than comparing to the raw source file).

**Test status:** `python -m pytest tests/test_scenario_campaign_wiring.py
tests/test_scenario_campaign.py tests/test_scenario_measures.py -q` ->
`............................................................  [100%]` / `60 passed in
16.46s` (48 pre-existing measures tests + 8 pre-existing campaign tests + 4 new wiring tests,
zero failures).

**Notes:** For each of the 8 cells x 2 sample buildings = 16 output IDFs, all confirmed to
exist on disk, be non-empty, and be distinct files (`test_all_cells_times_all_buildings_produce_distinct_files_on_disk`).
No EnergyPlus run, no `05_results` write, no viewer change, `SCENARIO_LAYER_ENABLED` untouched
(still default OFF). Verified `openubem/scenarios/campaign_runner.py` is not imported from
`openubem/idf/`, `openubem/geometry/`, `openubem/campaign/` or `openubem/simulation/`
(`grep -rn "openubem\.scenarios" openubem/idf/ openubem/geometry/ openubem/campaign/
openubem/simulation/` -> no matches); the only importer is
`tests/test_scenario_campaign_wiring.py`. This remains the wiring step only — item 6 (a real
fleet-scale run) stays gated on the unresolved `05_results` write-slot question per §2b. No new
error encountered beyond the test-mechanics deviation above (not a code bug, so no entry added
to `OpenUBEM_debug_References.md`).

#### C04 — Per-archetype, per-end-use regression fixture — completed 2026-09-18

**Artifacts:** `tests/test_archetype_end_use_regression.py` (new, 4 tests: golden-coverage check,
perturbation-naming check, matching-table check, live fresh-run regression check).
`tests/fixtures/golden_archetype_enduse/golden_table.csv` (new — mean EUI kWh/m² per archetype_id x
11 end uses), `per_building_raw.csv` (new — the 18 underlying `parse_building()` rows, kept for
traceability), `README.md` (new — full provenance).

**Deviations:** Checked "store under `tests/reference/` if that is where existing goldens live"
first, per the task's own instruction: `tests/reference/` holds `geo08_reference_partitioner.py`, an
independent-reimplementation *reference module* for a geometry-parity check, not golden data. The
repo's actual golden-data convention is `tests/fixtures/golden_sql/` (frozen SQL fixtures +
`golden_expected.json` + `README.md`, used by `tests/test_results_parser.py`); followed that
convention (`tests/fixtures/golden_archetype_enduse/`) instead of `tests/reference/`. Did not commit
raw `eplusout.sql` files as `golden_sql/` does (2.4-27 MB each there for 3 buildings; 20 would be
unreasonable) — committed the small aggregated table + per-building EUI CSV instead, and made the
live comparison test (`test_fresh_run_matches_golden_per_archetype_per_end_use`) re-run the real
build+simulate pipeline fresh rather than re-parse frozen SQL, since only a fresh EnergyPlus run can
reproduce the motivating failure mode (an engine upgrade silently moving one archetype's numbers).
Sample is 20 buildings = 2 WWR variants (0.30 / 0.45, second variant's `osm_id` suffixed `_V2`) x the
existing 10-archetype `tests/fixtures/synthetic_10_buildings.py` fixture (reused, not a new fixture —
same reuse pattern as block 4's H01 census). `way/R8` and `way/R8_V2` (archetype `Warehouse`,
`resolution_mode="auto"`, the plan's own default) both hit the pre-existing, known, out-of-scope
"Warehouse `auto`-mode IDF failure" already named in this doc's §2 (temperature-out-of-bounds
`** Fatal **`, EnergyPlus 23.1.0, reproduced deterministically on both variants) — not registered as a
new `OpenUBEM_debug_References.md` entry since it was not solved here (explicitly out of scope) and
is the same known issue; `Warehouse` is absent from the golden. Remaining sample: 18 buildings across
9 archetypes, above the task's >= 12 buildings / >= 4 archetypes floor. No wiring, no config flag
touched, no `05_results` write, no figures rendered — build+simulate only, output confined to
`tests/fixtures/golden_archetype_enduse/` and (for the live test) `tmp_path`.

**Test status:** Golden-generation run and the new test file both run in parallel, never sequentially,
per CLAUDE.md — stated before running: case count 20, local pool width 20 (both the one-off golden
generation and the live test's fresh rebuild use `n_jobs=20`, EnergyPlus 23.1.0, Chicago TMY3 EPW,
matching `tests/test_sim_integration.py`'s convention). `python -m pytest
tests/test_archetype_end_use_regression.py -v` -> `4 passed in 36.94s`. Full TechTransfer baseline
plus this file: `python -m pytest tests/test_scenario_measures.py tests/test_pv_injection.py
tests/test_compliance_audit.py tests/test_prep_gate.py tests/test_layout_assigner_fit_check.py
tests/test_parser_version_robustness.py tests/test_envelope_patcher_windows.py
tests/idf/test_ground_temperature.py tests/test_archetype_end_use_regression.py -q` ->
`112 passed in 155.55s` (108 pre-existing + 4 new, zero failures, zero new skips).

**Notes:** Golden-generation run: 20/20 IDFs built (`generation_status=success`), 18/20 simulated
successfully (2 `failed_fatal` = the Warehouse pair above), all 18 `parse_status=success`. Both the
golden-generation run and the live pytest run print
`Windows fatal exception: access violation` / `<cannot get C stack on this system>` stack-trace spam
from `joblib`'s loky worker spawn under the local `n_jobs=20` pool — already registered as benign,
never-a-failure noise at `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1781` ("localized around
`test_step3_orchestrator.py::test_parallel_byte_identity` and `test_sim_integration.py`"); both runs
still report their full pass count and exit code 0, so no new entry was added. Comparison tolerance:
`max(0.05 kWh/m2, 1% of golden)` per cell, tight enough to catch the motivating +56.6% class of drift
while tolerating negligible float noise across runs.

#### PV-VAL — PV validation run — completed 2026-09-18

**Artifacts:** `tests/test_pv_validation_run.py` (new, 1 test,
`test_pv_injection_on_real_prototype_runs_clean_and_generates`, marked
`pytest.mark.energyplus` + `pytest.mark.slow`, module-level skip if the EnergyPlus 23.1 binary is
absent, mirroring `tests/test_sim_integration.py`'s skip pattern).

**Deviations:** None from the task's "How" for the PV mechanism itself (`strip_existing_pv` then
`inject_pv(idf, enabled=True)` called directly on `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`, run
once through `run_energyplus`, checked via `classify_outcome`) or from `PV_INJECTION_ENABLED` (stays
`False` in `openubem/config.py`, untouched). Two additions not covered by the task's "How", both
needed only to make the run itself possible and neither touching the build path: (1) no Buffalo EPW
ships with the local EnergyPlus 23.1 install, so the Chicago TMY3 EPW already used for real-binary
runs by `tests/test_sim_integration.py` and `tests/test_archetype_end_use_regression.py` was reused —
this test proves the PV-generation mechanism runs and produces power, not a Buffalo-climate result;
(2) the raw prototype IDF (unlike Step-3-built IDFs) carries no `Output:SQLite` object, which
`classify_outcome`'s success path requires to find `eplusout.sql`, so `OUTPUT:SQLITE` and an
`OUTPUT:METER` on `ElectricityProduced:Facility` (RunPeriod) were added directly on the in-test IDF
object (matching the literal object calls `openubem/idf/outputs.py::write_outputs` also makes, not by
importing that build-path module). `ElectricityProduced:Facility` was chosen over a
`Generator:PVWatts`-specific variable because it is one of the plan's own named options ("e.g.
Electricity:Facility production") and reads correctly regardless of whether `inject_pv` lands a
`Generator:PVWatts` or `Generator:Photovoltaic` object on a given roof.

**Test status:** `python -m pytest tests/test_pv_validation_run.py -v -s` ->
`test_pv_injection_on_real_prototype_runs_clean_and_generates PASSED` / `1 passed in 36.38s`
(EnergyPlus 23.1.0, real binary at `C:\EnergyPlusV23-1-0`).

**Notes:** Measured result: `status='success'`, `n_severe=0` (zero severe, and status=success already
excludes fatal), 1 PV generator placed (`n_flat_generators=1`, the prototype's one qualifying flat
roof), `total_dc_capacity_w=126215.4`, annual `ElectricityProduced:Facility` generation
`505,122,371,851 J = 140,311.8 kWh` — confirmed non-zero. EnergyPlus's own `.end`/`.err` summary line
reported `7,656,942 Warning; 0 Severe Errors` — an oddly large but genuine EnergyPlus-reported warning
count on this specific prototype+PVWatts combination (confirmed against the raw `eplusout.err`
"EnergyPlus Completed Successfully" summary line, not a `classify_outcome` parsing artifact); not
registered in `OpenUBEM_debug_References.md` since it is not an error (run succeeded, 0 severe, 0
fatal) and nothing here was fixed. No other file under `openubem/` was touched — `git diff --stat --
openubem/` is empty for this task; `PV_INJECTION_ENABLED` confirmed still `False` at
`openubem/config.py:223`. No `05_results` write, no viewer change. Per SR-H2's own stated condition
(block 4), this is the requested proof; whether to act on it (task 3, `PV_INJECTION_ENABLED` wiring)
is a separate, not-yet-authorized decision.

#### PV-WIRE — wire `pv.py` into the build path, flip `PV_INJECTION_ENABLED` — completed 2026-09-18

**Artifacts:** `openubem/idf/builder.py` (import `inject_pv, strip_existing_pv` from
`openubem.idf.pv`; call `strip_existing_pv(self.idf)` then
`inject_pv(self.idf, enabled=config.PV_INJECTION_ENABLED)` at both pre-`write_outputs` points — the
`layout_assign` branch, now at line 571-572 (was 570), and the generic per-building branch, now at
line 700-701 (was 697)); `openubem/config.py:223` (`PV_INJECTION_ENABLED: bool = False` ->
`True`); `tests/test_pv_build_wiring.py` (new, 2 tests:
`test_flag_on_build_carries_pv_generator`, `test_flag_off_build_carries_no_pv_generator`, both
building a real IDF through `BuildingIDF.build()` — no EnergyPlus run — on the generic branch using
the same `SmallOffice`/511.16 m2/1-level row already used by
`tests/test_builder_elevators_wired.py`, with `monkeypatch.setattr(config,
"PV_INJECTION_ENABLED", ...)` isolating each test from the now-`True` default).

**Deviations:** None from the task's "How." The wiring call passes `config.PV_INJECTION_ENABLED`
explicitly (never hardcodes `True`); `strip_existing_pv`/`inject_pv` are called, not reimplemented.
One test-authoring fix, not a spec deviation: an initial `assert idf.idfobjects["GENERATOR:PVWATTS"]
== []` raised `AttributeError: 'list' object has no attribute 'list2'` (eppy's `Idf_MSequence.__eq__`
assumes the other side is also an `Idf_MSequence`); fixed to `assert len(...) == 0` and registered at
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 14.

**Test status:** `tests/test_pv_build_wiring.py -v` -> both tests PASSED (`2 passed in 1.98s`).
Full suite `python -m pytest -q` (flag on, this task's state) -> `25 failed, 2777 passed, 40 skipped,
653 warnings in 2740.71s (0:45:40)`, exit code 1. All 25 failures were isolated and re-run against the
pre-PV-wiring code (`git stash` of `openubem/config.py` + `openubem/idf/builder.py` only) and fail
identically, same assertion text, same count (8 + 17 = 25) — none mention `Generator:PVWatts`, PV,
roofs, or solar; they are pre-existing EU-arc/geometry failures (Bologna layout-binding sidecars,
EU15 ruled coverage, EU18c viewer forbidden-terms/scene-polygon checks, EU observed-archetype
mapping, EU real-footprint feasibility, EU S2 ceiling82 mismatch IDs, generation-drop-rescue
regression), unrelated to and unchanged by this task. **Zero tests changed behavior because PV is now
on** — no previously-passing test now fails, and no golden was edited.

**Notes:** `PV_INJECTION_ENABLED` confirmed `True` at `openubem/config.py:223` after the edit; the
stash/pop round-trip used to isolate baseline failures was verified restored byte-for-byte
(`git status --short` showed only the two intended modified files afterward). No `05_results` write,
no viewer change, no other file under `openubem/` touched beyond `builder.py`/`config.py`
(`git status --short` scoped to `openubem/` shows exactly those two paths for this task).

#### FLAGS-05a — ENVELOPE_PATCH_SKIP_WHEN_BETTER flipped to True — completed 2026-09-18

**Artifacts:** `openubem/config.py:112` (`ENVELOPE_PATCH_SKIP_WHEN_BETTER: bool = False` -> `True`).
No other file touched for this flag.

**Deviations:** None from the task's "How" (single one-line, config-only edit). Worth recording:
mid-run, this repo's working tree was shared with the concurrent PV-WIRE session above; its
`git stash push`/pop (isolating its own baseline failures) transiently reverted this edit and briefly
commingled it with PV-WIRE's uncommitted changes. Verified restored correctly before starting the
`PREP_ABORT_ON_FAILURE` work: `git diff openubem/config.py` isolated to the intended line, `git stash
list` empty.

**Test status:** `python -m pytest -q` -> `26 failed, 2774 passed, 40 skipped, 653 warnings in
2724.69s (0:45:24)`, exit code 1. Diffed against PV-WIRE's independently-isolated 25 pre-existing
failures (above) and against this task's own `PREP_ABORT_ON_FAILURE` run (FLAGS-05b, below):
`comm -12` on the sorted `FAILED` lines of both runs shows 25 of these 26 are the identical,
pre-existing, unrelated set (EU-arc/geometry/layout/campaign/generation-drop-rescue tests) —
confirmed by `grep -rn "ENVELOPE_PATCH_SKIP_WHEN_BETTER" openubem/ tests/` returning only
`openubem/config.py` and `openubem/idf/builder.py:567` (the pre-existing `skip_when_better` call
site), no test file. The 26th,
`tests/test_step3_orchestrator.py::TestParallelByteIdentity::test_parallel_byte_identity`, is absent
from FLAGS-05b's run and from the 25-common set; attributed to Windows joblib/loky worker contention
from two full `pytest -q` suites (this task's and PV-WIRE's) running concurrently on the same machine
at that time — the same benign `Windows fatal exception: access violation` noise already registered
at `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1788`, not a behaviour change from this flag.
Zero failures among `tests/test_envelope_patcher_windows.py`, `tests/test_compliance_audit.py`,
`tests/test_scenario_measures.py` (the three files the task named as already exercising the flag on).

**Notes:** No new error encountered or fixed by this flag flip, so no new
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` entry. Config-only change; no other file under
`openubem/` touched.

#### FLAGS-05b — PREP_ABORT_ON_FAILURE flipped to True — completed 2026-09-18

**Artifacts:** `openubem/config.py:123` (`PREP_ABORT_ON_FAILURE: bool = False` -> `True`). No other
file touched for this flag.

**Deviations:** None from the task's "How."

**Test status:** `python -m pytest -q` -> `27 failed, 2779 passed, 40 skipped, 653 warnings in
2528.05s (0:42:08)`, exit code 1. `comm` against FLAGS-05a's run confirms 25 of the 27 are the same
pre-existing, unrelated set described above (the one flaky failure from that run,
`test_parallel_byte_identity`, did not recur — consistent with concurrent-load contention, since no
second full suite was running this time). Two failures are new and are the direct, expected
consequence of this flag, exactly as the task's "How to test" anticipated ("simulation phase now
aborts instead of continuing past generation failures"): (1)
`tests/test_prep_gate.py::TestPrepGateOffByDefault::test_flag_default_is_false` asserts
`config.PREP_ABORT_ON_FAILURE is False` at `tests/test_prep_gate.py:47` — now fails because the
default itself changed, which is this task's intended effect; (2)
`tests/test_sim_parallel.py::TestRunNeighbourhood::test_n_input_rows_in_output` builds a 3-row
manifest with one `skipped_invalid_geometry` row and, unlike sibling tests in the same file, does not
monkeypatch `PREP_ABORT_ON_FAILURE` to `False`; `run_neighbourhood` now raises `PrepPhaseFailedError`
before dispatch instead of returning all 3 rows, per `openubem/simulation/parallel.py:269-276`. No
unrelated new failures.

**Notes:** No new error encountered or fixed, so no new
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` entry — both newly-failing tests are stale
assertions of the prior default, not bugs. They would need updating or retiring to match the new
default in a follow-up task; out of scope for this config-only flip ("withdraw don't tune" — not
edited here). Config-only change; no other file under `openubem/` touched.

#### FLEET-06a — build the 65,112-case manifest and IDFs — completed 2026-09-18

**Artifacts:** `%TEMP%\ubem_validation\fleet06a_campaign_2026-09-18\manifest_65112.csv` (new — 65,112
data rows, columns `building_id,cell_name,output_idf_path`), IDFs under
`%TEMP%\ubem_validation\fleet06a_campaign_2026-09-18\<cell_name>\<stem>.idf` for all 8 cells (baseline
+ 7 non-baseline). Built by `scripts/analysis/fleet06a_campaign_2026-09-18.py` (unmodified, prior
executor's script, run with `.venv\Scripts\python.exe`), consuming the already-completed
`fleet06a_rebuild_2026-09-18` (today's-code IDFs, 12/12 cells 100% success) and the already-fetched
`fleet06a_2026-09-18\baseline_idfs` (8,139 T07 IDFs from Speed).

**Deviations:** none — resumed the previously-written, spec-matching scripts as instructed; no code
changes made.

**Test status (How-to-test checks from the plan):**
- Row count: `wc -l manifest_65112.csv` -> 65,113 lines = 1 header + 65,112 data rows = 8 cells x 8,139
  buildings (confirmed per-cell via `cut -f2 | sort | uniq -c`: all 8 cells exactly 8,139 rows each).
- Duplicate `(building_id, cell_name)` pairs: `sort | uniq -d` on the two columns -> 0 duplicates.
  Distinct `building_id` values: 8,139 (matches the T08-successful population exactly).
- Run log: `baseline cell: 8139 copied, 0 missing`; zero `MISSING_FRESH` / `MISSING` lines anywhere in
  the run log — every one of the 8,139 buildings had both its fetched baseline IDF and its fresh
  today's-code rebuild IDF present.
- Baseline-cell spot-check (N=5: `relation_13781131`, `relation_7480583`, `way_1008727466`,
  `way_1008727467`, `way_1008727468`): all 5 manifest copies under `baseline/` are byte-identical
  (`cmp -s`) to the fetched Speed T07 source in `baseline_idfs/` — zero PV objects by construction,
  confirmed identical rather than merely PV-free.
- Non-baseline PV spot-check (N=5 buildings x all 7 non-baseline cells = 35 IDFs, sampled across
  4 geographic cells: `way_383692676`/nyc_urban, `way_74457835`/austin_rural, `way_402248264`/la_urban,
  `way_442634566`/la_suburban, `way_985113012`/austin_rural): all 35 contain
  `ELECTRICLOADCENTER:DISTRIBUTION` + `GENERATOR:PVWATTS`/`GENERATOR:PHOTOVOLTAIC` objects, matching
  the fresh today's-code rebuild source IDF each cell started from (all 5 sampled buildings are
  PV-eligible per `pv.py`'s roof-area/pitch rule). Also confirmed by code reading
  (`openubem/idf/pv.py:181-182`, `if not used: return summary`) that a non-eligible building would show
  zero PV objects rather than an empty distribution — the mechanism is selective, not unconditional.
- Additional geometry-consistency spot-check (same N=5): `ZONE` and `BUILDINGSURFACE:DETAILED` object
  counts are identical between each building's `baseline`-cell IDF and its non-baseline starting IDF
  (the fresh rebuild source) — e.g. `way_402248264`: 3 zones / 30 surfaces on both sides — confirming
  the two IDF sources differ only in PV presence, not geometry or floor area.

**Notes:** Non-baseline IDF generation (7 cells x 8,139 = 56,952 `apply_cell()` calls, local
`ProcessPoolExecutor(max_workers=20)`, pure IDF text generation, no EnergyPlus) completed in 579s
(~9.7 min) after the baseline copy step. No EnergyPlus run occurred anywhere in this task. No new error
encountered, so no new entry added to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Per the
plan's explicit instruction, FLEET-06b (the sbatch EnergyPlus array job) was not started.

#### FLEET-06b — submit the array job to Speed — STOPPED 2026-09-18 (spec conflict, no job submitted) — SUPERSEDED, see IN-PROGRESS entry below (§2f, 2026-09-23)

**Artifacts:** `scripts/cluster/fleet06b_submit_2026-09-18.py` (new — adapted from `t07_submit_resim.py`:
reads the FLEET-06a manifest, cross-references each `building_id` against the existing
`t07_resim_2026-09-09/fleet.lst` for its epw, packs only the 65,112 IDFs into one tarball since weather
is reused unmodified from the T07 remote directory, ships and extracts on Speed), `scripts/cluster/
submit_fleet06b.sbatch` (new — one array task = one `(cell_name, building_id)` from a 3-column
`fleet.lst`, output to `out/<cell_name>/<building_id>/`, adapted line-for-line from
`submit_fleet_t07.sbatch`). Remote prep completed and verified: `/speed-scratch/o_iseri/openubem/fleets/
fleet06b_2026-09-18/` holds `idfs/<cell_name>/<building_id>.idf` (65,112 files), `weather/` (9 epws,
copied from `t07_resim_2026-09-09/weather/`, not re-uploaded), `fleet.lst` (65,112 lines,
`cell_name<TAB>building_id<TAB>epw_basename`), and an empty `out/`. No EnergyPlus run.

**Deviations:** Total case count (65,112) and parallel width (32) were stated before attempting
submission, per the cluster rule. The submission itself did not run per the plan's exact spec. `sbatch
--array=1-65112%32 --time=7-00:00:00` was attempted (from the staged, verified remote directory above)
and failed: `sbatch: error: Batch job submission failed: Invalid job array specification`. Root cause,
confirmed by `scontrol show config | grep MaxArraySize` on the login node (informational query, not
compute): Speed's SLURM `MaxArraySize = 10001`, so a single array job's task index cannot exceed 10000 —
`1-65112` is 6.5x over that ceiling. T07's precedent (`N=8152`) never hit this because it stayed under
the limit. Per the task instructions, this is a spec-vs-cluster-reality conflict, not a judgment call, so
**no split was invented and no job was submitted**. A second, unrelated bug was found and fixed in the
same submit script before this: the remote-extraction command's `find idfs -name '*.idf'` used a
single-quoted glob nested inside the `_ssh()` helper's own `bash -lc '...'` single-quoted wrapper, which
closed the outer tcsh quote early and made the entire remote extraction step silently no-op
(`bash: No match.`, no exception raised, nothing after it ran). Fixed to `find idfs -name "*.idf"`
(`scripts/cluster/fleet06b_submit_2026-09-18.py`); the affected remote step (extract tarball + copy
weather) was then re-run correctly by hand from the login node (no compute) and verified (65,112
fleet.lst lines, 65,112 idf files, 9 epw files) — this is the prep already listed under Artifacts.

**Test status:** No array job exists to test (`squeue`/`sacct` show nothing for this fleet — nothing was
submitted). Remote staging verified as stated above. Both new errors registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §12 before closing this entry.

**Notes:** **STOP — needs a decision, not a guess, before FLEET-06b can submit anything.** The plan's own
FLEET-06b spec pins one command, `sbatch --array=1-65112%32`, but that command cannot exist on Speed: the
account-wide 32-concurrent cap (CLAUDE.md) and the cluster's own 10,000-task array ceiling are two
different limits, and 65,112 cases need multiple array jobs to satisfy the second one, which was not
anticipated by the plan or by the T07/T08 precedent scripts (both stayed under 10,000). Splitting
raises a question this session should not answer unilaterally: how many array jobs (e.g. 7 x ~9,302, or
some other split), and how the 32-wide account-wide throttle is shared across them so total *concurrent*
tasks across all of this fleet's array jobs never exceeds 32 (not 32 per split job, which would be
224 concurrent and likely starve/collide with other account usage) — CLAUDE.md's cluster rules cover a
single array job's throttle, not this multi-array-job case. Nothing was submitted; the fully-packed and
verified remote directory means submission can start immediately once the split/throttle-sharing scheme
is decided. FLEET-06c was not started (its gate, "FLEET-06b's array job reaches 100%
COMPLETED/FAILED," cannot be met — no job exists).

#### FLEET-06b — move remaining cases to Speed — IN PROGRESS 2026-09-23 (local run stopped, Speed job submitted, not yet harvested)

**Artifacts:** `%TEMP%\ubem_validation\fleet06b_local_2026-09-18\results.csv`/`progress.json`/`run_log.txt`
left as final local record (last local write 2026-09-23 09:49:35, done=61,765 failed=29 remaining=3,347
per `progress.json`; true on-disk completion count via `is_completed()`/`.sql.gz` fallback, the same
check `cmd_full()` uses, is 61,739 completed / 3,373 pending — this on-disk count, not the last
`progress.json` tick, is what was moved). `/speed-scratch/o_iseri/openubem/fleets/fleet06b_2026-09-18/
fleet_remaining.lst` (new, remote — 3,373 lines, `cell_name<TAB>building_id<TAB>epw_basename`, filtered
from the existing remote `fleet.lst` against the derived pending set; all 3,373 pending pairs matched,
0 missing). Remote `submit_fleet06b.sbatch` re-uploaded unchanged (already supported `FLEET_LST` env var
from the §2d chained-job era — no script edit needed, just a new `--export`). Speed job **1342940**,
`--array=1-3373%32 --time=7-00:00:00`, submitted 2026-09-23 ~09:53.

**Deviations:** None from §2f's 9-step task spec, steps 1-7 executed as written. Step 5 ("adapt
`submit_fleet06b.sbatch` / `fleet06b_submit_2026-09-18.py` to read it") needed no code change to the
sbatch script (it already reads `FLEET_LST` with a `fleet.lst` default, built for the §2d multi-job
chain); `fleet06b_submit_2026-09-18.py` itself was not invoked — its packing/upload steps were
unnecessary since the remote directory from 2026-09-18 (idfs, weather, full `fleet.lst`) was still
intact (verified via `ls`/`wc -l` through `ssh ... bash -lc '...'`, ahead of any submission), so only
the filtered `fleet_remaining.lst` needed generating and uploading.

**Test status:** On-disk pending-set derivation matches `cmd_full()`'s own logic exactly (ran the same
`is_completed()` + `.sql.gz`-fallback check via a throwaway script importing
`openubem.simulation.parallel.is_completed`): 65,112 manifest rows -> 61,739 completed + 3,373 pending,
sums correctly, all 3,373 pending pairs found in the remote `fleet.lst` (0 unmatched). Job 1342940
confirmed alive and correctly configured ~90 s after submission: 36 array tasks already had
`eplusout.end` on disk, and a sampled in-flight task's `.log` showed genuine EnergyPlus progress
(warmup/sizing/shadowing lines advancing), not a config-time failure. `squeue -u o_iseri` showed 30 of
this job's tasks RUNNING (its own `%32` throttle) alongside pre-existing unrelated jobs from the same
account (`wp11_dra*`, `wp11_sco*`, `histnu*`, `p5_boots*` — not touched, per standing rule) with no
undersubscription needing an `ArrayTaskThrottle` raise.

**Notes:** Local run stop: `schtasks /end /tn "OpenUBEM_FLEET06b"` reported success but left the
process tree alive (5 `energyplus.exe` still running under it); `taskkill /PID 46744 /T /F` was needed
to actually terminate the full tree (12 processes), then confirmed zero `python.exe`/`energyplus.exe`
remained before `schtasks /delete /tn "OpenUBEM_FLEET06b" /f`. Process audit before stopping ruled out
a double-dispatch: only one dispatcher (`fleet06b_local_run_2026-09-18.py`, PID 24540, 5 forked
workers) was alive, launched by the Task Scheduler's own wrapper PID (46744) — not two independent
runs. The ~61.7k cases already completed locally were not touched or resubmitted, per the task's
explicit constraint. **Not yet closed**: steps 8-9 (harvest Speed results into `results.csv`, update the
live monitor artifact, confirm all 65,112 original cases COMPLETED/FAILED, sanity-check the baseline
cell's fleet EUI against 153.95 kWh/m²) remain open pending job 1342940 finishing — monitor via `sacct
-j 1342940` at >=30 min intervals, event-driven, no login-node compute, no busy-polling. This entry will
be replaced by a final `COMPLETED` entry once FLEET-06c's 100% gate is reached. No new error was hit
this task (schtasks/taskkill/ssh/sbatch all succeeded as run), so no new
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` entry was needed.

#### FLEET-06b — fix PV generator-list overflow, rerun the 28 job-1342940 failures — IN PROGRESS 2026-09-23 (Speed job submitted, not yet harvested)

**What:** Job 1342940 finished 3,345/3,373 with 28 failures. 21 (3 buildings x 7 non-baseline cells:
`way_381810555`, `way_425993519`, `way_427278443`) failed because `inject_pv()` wrote all of a
building's `Generator:PVWatts`/`Generator:Photovoltaic` objects into one
`ELECTRICLOADCENTER:GENERATORS` object; on reload (`GeomIDF(fresh_path)` in
`fleet06a_campaign_2026-09-18.py`'s `_build_building()`) + `apply_cell()` + `idf.saveas()`, eppy
re-parses that object's `objls` at the IDD's 30 explicitly-declared `Generator N Name` groups
(`Energy+.idd`/`eppy.iddcurrent`, both declare exactly 30 before falling back to `\extensible:5`
auto-growth) without re-extending it, so `EpBunch.__repr__`'s `zip(obj, objls)` silently truncates
any list with >30 generators and drops the terminating `;`, corrupting the following
`ELECTRICLOADCENTER:DISTRIBUTION` object's text (matches the observed `generator_outputs[30]
[generator_object_type] - "OpenUBEM_PV_Distribution" - Failed to match against any enum values`
Severe -> Fatal). Reproduced locally byte-for-byte against the real `way_381810555.idf` fresh build
(34 generators; reload+apply_cell+saveas dropped generators 31-34 and the `;`). The other 7
(`way_281344894` x 7 cells) are the known `--mem=6G` OOM (debug-reference entry near line 170;
owned by the manager, not touched here).

**Why:** `MAX_GENERATORS_PER_LIST = 30` keeps every `ELECTRICLOADCENTER:GENERATORS` object within
the IDD's explicitly-declared field count, so the reload-time `objls` truncation can never trigger
regardless of which IDD (real E+23.1 vs eppy's bundled fallback) is in play at reload time.

**How:** `openubem/idf/pv.py` `inject_pv()` (module const `MAX_GENERATORS_PER_LIST = 30` at line 40;
chunking loop at lines ~223-263) now splits a building's generator records into chunks of at most 30
and writes one `ELECTRICLOADCENTER:GENERATORS` + `ELECTRICLOADCENTER:INVERTER:PVWATTS` +
`ELECTRICLOADCENTER:DISTRIBUTION` triple per chunk, names suffixed `_1`, `_2`, ... only when more
than one chunk exists (unsuffixed names preserved for the single-chunk case, unchanged behaviour).
`_already_injected()` (line ~124) now also matches a `_N`-suffixed distribution name.
`summary["n_generator_lists"]` added. Regenerated the 21 IDFs via the same in-repo functions
`fleet06a_campaign_2026-09-18.py` uses (`strip_existing_pv`/`inject_pv`/`openubem.scenarios.campaign.
apply_cell`), applied directly to the already-existing fresh rebuilt base IDFs at `%TEMP%\
ubem_validation\fleet06a_rebuild_2026-09-18\<cell_geog>\step3\idfs\<stem>.idf` (no full Step1-3 cell
rebuild needed — geometry/roofs unchanged, only PV injection was regenerated then the same
`apply_cell()` reapplied for the 7 non-baseline cells), uploaded over `idfs/<cell>/<stem>.idf` on
Speed (scp, byte-verified via md5sum). Deleted exactly the 28 `out/<cell>/<stem>/` dirs (listed
before deleting, then confirmed 0 remaining) and wrote `fleet_rerun28.lst` (28 lines,
`cell<TAB>stem<TAB>epw`, taken from `fleet_remaining.lst`). Submitted
`sbatch --array=1-28%32 --time=7-00:00:00 --mem=32G --export=FLEET_DIR=...,FLEET_LST=fleet_rerun28.lst
submit_fleet06b.sbatch` (sbatch file untouched) -> **job 1346459**.

**Test status:** `pytest tests/test_pv_injection.py tests/test_pv_validation_run.py -q` — 21 passed
(includes new `test_generator_count_exceeding_cap_splits_into_multiple_lists`, 35 roofs -> two
`ELECTRICLOADCENTER:GENERATORS` blocks of 30+5, both `;`-terminated, verified by regex over
`idf.idfstr()`; existing `test_no_generator_cap_32_roofs_yield_32_generators` updated to expect 2
distribution objects for 32 roofs, since 32 > the new 30-cap). All 21 regenerated IDFs checked
programmatically: `GENERATOR:PVWATTS`+`GENERATOR:PHOTOVOLTAIC` count == total `Generator N Name`
fields across all `ELECTRICLOADCENTER:GENERATORS` blocks == count of blocks == count of
`ELECTRICLOADCENTER:DISTRIBUTION`/`ELECTRICLOADCENTER:INVERTER:PVWATTS` objects, 0 mismatches.
`way_381810555`'s regenerated `lighting` IDF run through EnergyPlus 23.1 locally (ExpandObjects +
full annual run): **Completed Successfully**, 0 PV/generator-related Severe (one pre-existing
unrelated non-convex-shading Severe, not fatal). Job 1346459 confirmed alive ~2 min after submission:
task 1's `.log` past `ExpandObjects`/`EnergyPlus Starting`/warmup/into `Performing Zone Sizing
Simulation`, no Severe. `squeue -u o_iseri` showed only 1 of 28 tasks RUNNING (rest PD,
`AssocGrpCpuLimit`) because other unrelated jobs (`wp11_dra*`, `histnu*`, `p5_boots*`) already occupy
the account-wide CPU cap — not touched, per standing rule; `%32` is the job's own already-correct
throttle.

**Deviations:** None from the assigned fix/rerun scope. Debug-reference doc update explicitly
deferred to the manager (out of scope for this dispatch).

**Notes:** Not yet closed — job 1346459's 28 tasks still running/pending; harvest and re-fold into
job 1342940's 3,345 successes is a follow-up once it completes.

#### FLEET-06c-FIX — SQL fallback for simulated floor area and zone multipliers — completed 2026-09-25

**Artifacts:** `openubem/results/parser.py` — `parse_sql_zone_area()` and `parse_sql_zone_multipliers()`
added (new functions, just above `resolve_simulated_floor_area()`); `resolve_simulated_floor_area()`
tries the SQL `Zones` table (provenance `sql_simulated`) only when the `.eio` route is unavailable,
eio still tried first, footprint still last resort; `parse_building()`'s per-zone multiplier map now
falls back to `parse_sql_zone_multipliers()` when the eio map is empty and `sql_path` exists.
`tests/test_results_denominator.py` — new `TestResolveSimulatedFloorAreaSqlFallback` class (5 tests:
sql_simulated when no eio, eio still wins when both present, footprint fallback when SQL has no
`Zones` table, `parse_sql_zone_area` empty-file guard, `parse_sql_zone_multipliers` upper-cases keys).
`tests/test_parser_open60_multiplier.py` — new `TestParseSqlZoneMultipliers` class (3 tests).
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §8 — one bullet registered (symptom "8,134 of
8,139 rows `floor_area_provenance = footprint_fallback`...").

**Deviations:** Two pre-existing tests in `tests/test_results_denominator.py` had their expected
values updated, not left untouched: `test_well_formed_eio_changes_eui_denominator`'s post-eio-removal
assertion and `test_eio_absent_provenance_on_real_golden_fixture`. Both had hard-coded the *old, buggy*
behaviour (`footprint_fallback`, 392.0 m²) for the golden fixture `tests/fixtures/golden_sql/
r1_single_zone.sql`, whose own `Zones` table is in fact well-formed (`FloorArea=196.0,
Multiplier=ListMultiplier=1.0, IsPartOfTotalArea=1`) — exactly the case this fix targets. Updated both
to the corrected expectation (`sql_simulated`, 196.0 m²); no other assertion, fixture, or golden
expected value touched. This was necessary for "all must pass" (per the task's own How-to-test) to be
satisfiable at all, since the fix's whole purpose is to change this exact fallback path.

**Test status:** `python -m pytest tests/test_results_denominator.py tests/test_parser_open60_multiplier.py
tests/test_parser_version_robustness.py -q` — 32 passed, 0 failed.

**Notes:** None.

#### FLEET-06c-BASE — re-run the baseline harvest, stop for audit — completed 2026-09-25

**Artifacts:** `<HARVEST_ROOT>\baseline\` rebuilt from scratch (deleted, then
`python scripts/analysis/fleet06c_harvest_2026-09-24.py --cells baseline`, wall 2355.5s, 12-way pool).

**Test status (measured, per the plan's How to test):**
- 8,139 rows over 12 geo dirs — **measured 8,139 rows, 12 geo dirs.** PASS.
- 0 rows `floor_area_provenance = footprint_fallback` — **measured 0** (8,134 `sql_simulated` + 5
  `eio_simulated`). PASS — confirms FLEET-06c-FIX closed the gap this task exists to fix.
- fleet area vs T08 23,871,481.58 m² (within 0.01%) — **measured 23,871,478.15 m²**, diff 0.000014%.
  PASS.
- buildings whose area differs from T08 by > 0.1% — **measured 0**. PASS.
- fleet EUI excluding `dhw_district_eui_kwh_m2` vs 153.9501 (within 0.05 kWh/m²) — **measured
  152.6985 kWh/m², diff 1.2516 kWh/m²**. **FAIL** — outside tolerance (see Deviations).
- fleet EUI including district (new FLEET-06 baseline figure) — **measured 172.4076 kWh/m²**
  (+19.7091 kWh/m² vs excluding-district, consistent with the manager's 2026-09-25 audit note of
  +20.09).
- buildings whose non-district kWh differs from T08 `total_kwh` by > 0.1% — **measured 129
  buildings**, same population size as the pre-fix audit's "0.8% shortfall (129 buildings)" note, but
  root cause differs from what that note attributed it to (see Deviations).

One geo cell (`baseline/la_rural`) logged `FAILED ... PermissionError(13, ... 'being used by another
process')`, apparently during post-write temp-file cleanup (`decompressed_paths` unlink /
`gz_tmp_dir.rmdir()`) — verified its `05_results.*` outputs were nonetheless written completely and
correctly (144/144 rows matching the T08 population count for `la_rural`, 88 columns, 0 nulls in
`total_eui_kwh_m2`, 0 `footprint_fallback`); not rerun, since output was already complete and correct.

**Deviations:** The 129-building mismatch does **not** trace to the zone-multiplier root cause
(OPEN-60) that FLEET-06c-FIX targets — that part is confirmed closed: `lighting_eui_kwh_m2` matches
T08 within 1% for all 129 (in fact within ~0.001% for all), and `equipment_eui_kwh_m2` matches within
1% for 89 of 129 (the other 40 differ by a median ~1.2%, far too small to explain the gap). The
dominant residual (median 20.9%, max 27.8% kWh mismatch on these 129) is concentrated in
`cooking_eui_kwh_m2` and `refrigeration_eui_kwh_m2`, on archetypes with kitchen/refrigeration loads
(QuickServiceRestaurant 50, FullServiceRestaurant 32, LargeHotel 27, SecondarySchool 9, SuperMarket 5,
Hospital 4, PrimarySchool 2 — 129 total). Both columns are read from whole-building RunPeriod meters
(`InteriorEquipment:NaturalGas`, `Refrigeration:Electricity`), already multiplier-correct by
construction (E+ applies zone multiplier before writing a meter), so this is not an OPEN-60-shaped
defect and not something `resolve_simulated_floor_area()`/`parse_sql_zone_multipliers()` can affect.
Not investigated further or fixed — out of scope for the Touch-only list on this dispatch (parser.py
change was limited to the floor-area/zone-multiplier fallback). Flagged here per plan instruction to
stop and report after this task; root cause of the cooking/refrigeration gap (parser bug vs a genuine
difference between the FLEET-06 rebuilt IDFs and the original T08 simulation) is unassigned and open.

**Notes:** FLEET-06c-ALL is gated on manager audit of this entry, per §2h.
