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

#### FLEET-06b — submit the array job to Speed — STOPPED 2026-09-18 (spec conflict, no job submitted)

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
