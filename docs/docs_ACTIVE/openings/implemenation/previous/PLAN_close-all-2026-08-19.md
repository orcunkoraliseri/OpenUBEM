# PLAN — close the four items left to the user, by executing

> **Slug:** `close-all-2026-08-19` · **Date:** 2026-08-19 (late) · **Author:** manager/director
> **Authority:** user ruling 2026-08-19 — *"est-ce que tu peux fermer toutes en exécutant"*.
> **Predecessors:** `PLAN_open-57-and-58_2026-08-19.md` (CP-3, complete),
> `PLAN_board-17-ready-2026-08-19.md` (T01–T06, complete).
> **Register:** `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md` — 23 live / 35 struck / 58 total,
> next free `OPEN-59`.

---

## 1. What the user authorised, and what each authorisation actually costs

The director's closing message of 2026-08-19 named four things reserved to the user. The user
authorised all four in one ruling. They are **not** four tasks of equal size:

| # | Item | What "execute" means | Cost |
|---|---|---|---|
| 1 | Close OPEN-57 | Register edit — the fix is landed and verified live at 225/226 | director, minutes |
| 2 | Close OPEN-29 | Register edit — every defect it carries is owned elsewhere, immaterial, or dormant | director, minutes |
| 3 | Adopt-or-depart on OPEN-47 | 🔴 **Ratify the user's own 2026-08-12 ruling.** No code change | director, minutes |
| 4 | Run the OPEN-55 acceptance test | 1,589-building `nyc_suburban` cluster run | executor, hours |
| 5 | Restate the fleet baseline | 🔴 **Full 12-cell, 8,160-building fleet re-run** | executor, many hours |

Items 1–3 are executed by the director before this plan is dispatched (§2). Items 4 and 5 are the
executor's tasks T01–T05.

### 1.1 🔴 Why OPEN-47 closes without a code change

`openubem/semantic/building_classifier.py:171-190` carries the ruling verbatim:

> *"OPEN-47 ruling (user, 2026-08-12, plan §1.2): keep area-only as the default; the floor-count
> half above is deliberately NOT applied by default — deferred, not rejected."*

The stated reason is that the office size metric already multiplies by imputed levels
(`total_floor_area_m2 = area × max(levels_imputed, 1)`), so an explicit floor-count bound would make
the archetype depend on the same imputed quantity **twice**. T03 of `PLAN_board-17-ready` did not
contradict that reason — it **strengthened** it: **167 of the 598 divergent buildings (27.9 %) have
no observed floor count at all.** The item's own §-section names two acceptable outcomes, *adopt* or
*record the departure deliberately*; the second is already the standing decision. Closing this item
is therefore **writing up a decision that was taken seven days ago and never recorded as a closure**,
not reversing it. `use_floor_count` stays available, default OFF, as the evidence for the decision.

### 1.2 🔴 What the executor must understand about the baseline restatement

`157.1 kWh/m²` was computed on `phaseE_elevrb`. Current HEAD differs from that code in at least
four ways that reach fleet EUI:

1. **OPEN-35** — geometry now derives storeys from the same imputed value classification uses;
   **21 buildings** change floor count (verified three-way, `tests/test_open35_wiring.py`).
2. **OPEN-49 route 1** — `_per_building_rng` makes draws per-building deterministic.
3. **OPEN-55 route 2 + screen** — `_UNKNOWN_DONOR_EXCLUDE` removes data-centre/lab/restaurant
   donors from the Unknown PDE table. Every Unknown building in every cell draws differently.
4. **OPEN-01 / OPEN-56 fixes landed since.**

🔴 **OPEN-56 is still open and is fleet-wide.** Its measured cost is a **fixed per-building offset of
≈ +1.0 kWh/m² (mean +0.98 %, median +0.84 %, 65/69 same direction)** — a **known sign and a known
magnitude**. A baseline restated now is therefore **knowably low by roughly 1 kWh/m²** and will have
to be restated again when OPEN-56 is fixed. This is recorded here so the restatement's own document
carries the caveat; it is **not** a reason to refuse the run, and the user's ruling stands.

---

## 2. Director actions taken BEFORE dispatch (not the executor's work)

- **OPEN-57 CLOSED**, ID retired. §1 row and §-section amended.
- **OPEN-29 CLOSED**, ID retired. §1 row and §-section amended.
- **OPEN-47 CLOSED** as *deliberate documented departure*, ID retired. §1 row and §-section amended.
- §1 header count moved **23 → 20 live**. Next free item ID stays `OPEN-59`.

The executor **must not** edit the register. Report findings; the director records them.

---

## 3. Hard rules for the executor

1. 🔴 **NEVER run compute on the login node.** No `srun`, no `ssh … python`. `sbatch --array`,
   fire-and-forget, then read the output file. Login node is for `mkdir`, `scp`, `tar`, `squeue`,
   `sacct` only.
2. 🔴 **The remote login shell is tcsh.** Always go through `_ssh()`
   (`scripts/validation/v12_cell_pipeline.py`), which wraps in `bash -lc`. Never send a bare command
   string.
3. 🔴 **Never background a command and then pause waiting for a notification — it will never wake
   you.** Run it in the foreground and read the output, even if it takes several minutes.
4. 🔴 **Never touch other-project cluster runs.** Job `1266911` / `4J_s4_pe` is not ours.
5. 🔴 **Never run a git write command.** Git is handled externally. Read-only git only.
6. **Do not edit** the register, the director prompt, `docs/PROJECT_CHECKLIST.md`, root `main.py`,
   any OVERVIEW/DESIGN doc, `docs/docs_DONE/`, `docs/docs_main/`, `docs/docs_stepN/`.
   **No `.py` files under `docs/`, ever.**
7. **No new fleet figure is published by you.** You report the pooled number; the director restates.
8. Default to no code comments. Stop and ask on spec ambiguity; never invent.
9. All `.png` outputs go to `openubem/outputs/` (flat).

---

## 4. File layout

- Launcher for T01: `scripts/validation/open48_t02_attempt4.py` — **copy** of
  `open48_t02_attempt3.py` with `NEW_SUBDIR = "open48_refleet3_t02a4"` and log paths under
  `%LOCALAPPDATA%\Temp\open48_t02_attempt4`. Nothing else changed.
- Launcher for T03: `scripts/validation/open48_fleet_run4.py` — copy of `open48_fleet_run3.py`,
  `OUTPUT_SUBDIR = "open48_refleet4"`.
- Measurement docs: `../extra/MEASUREMENT_open-55_acceptance-test-attempt4.md`,
  `../extra/MEASUREMENT_fleet-restatement-2026-08-19.md`.
- Outputs: `openubem/outputs/comparisons/`.

## 5. Dependency decisions (pinned)

- Frozen input for T01: the run-2/run-3 `01_buildings.gpkg`, MD5 `1198ed01bfd3b4463e50da0ae39d8e27`,
  **copied not moved**, re-verified after copy. Attempt 3 already proved this path sound.
- `REMOTE_HOST = o_iseri@speed.encs.concordia.ca` (`v12_cell_pipeline.py:40`).
- Speed's job cap is ≈20k tasks — **submit in waves**, never one 8,160-task array plus the rest.
- Test-suite baseline: `.venv/Scripts/python.exe -m pytest -q tests/` → **1,919 passed / 55 skipped**.
  A bare root-level run reports ~36 false failures; **always scope to `tests/`.**

## 6. DESIGN / register facts with citations

- OPEN-55's acceptance test, as the item itself specifies it: `nyc_suburban`, real simulation
  output, pre-fix divergence count **71 of 290 Unknown** (register `INVESTIGATION_open-items-register.md`
  OPEN-55 §, lines 6950-7212).
- Attempt 3 proved the local half sound: **1,589/1,589 IDFs in 199.6 s**, LIVE_SMOKE both gates PASS
  (generation 100.0 % ≥ 95 %, Unknown 18.3 % < 20 %). Only the remote probe failed, and that is the
  fault OPEN-57 fixed.
- OPEN-57's remedy is in `_ssh` only; `stdin_data=None` is byte-for-byte the prior path, so no
  existing caller changed. Verified live **225/226** on `phaseE_er33_la_centre`.
- **OPEN-49 cannot close while OPEN-55 stands; the two resolve together** (register, OPEN-55 §,
  "Coupling").

---

## 7. Task list

### T01 — Run the OPEN-55 acceptance test, attempt 4

**What.** Create `open48_t02_attempt4.py` as specified in §4 and run it in the **foreground**.

**Why.** OPEN-55's remedy (the donor screen) has been applied but has **never been tested on real
simulation output**. Attempts 1–3 all died at the remote probe, which is the fault OPEN-57 fixed.
This is the item's own falsifiable acceptance test, and OPEN-49 closes with it.

**How.**
1. Verify the frozen source GDF exists and its MD5 is `1198ed01bfd3b4463e50da0ae39d8e27`.
2. Verify the **new** remote fleet dir `open48_refleet3_t02a4_nyc_suburban` is **absent** before the
   run. 🔴 Stale directories from attempts 1–3 must never be scored as this run's output.
3. Run the launcher in the foreground. Read the log, the heartbeat and the `EXITCODE` file.
4. If `_remote_results_complete` raises again, **capture the full stderr verbatim and STOP.** Do not
   retry blind — that is the mistake attempts 1–3 made.

**How to test.** Three controls, all pre-registered:
- **Control 1 — classification is unchanged by the screen.** The cell's archetype histogram must
  reproduce the frozen baseline exactly: `MidriseApartment 979 / SmallOffice 316 /
  OpenUBEMUnknown 290 / Courthouse 2 / QuickServiceRestaurant 1 / MediumOffice 1`. Bit-identity here
  is *expected* (per-building determinism), not evidence of a copied number.
- **Control 2 — the primary result.** Divergence count among the 290 Unknown buildings.
  **Pre-registered prediction: substantially below 71.** Report the actual number whatever it is.
  🔴 **If it is not below 71, say so plainly and do not explain it away** — a failed acceptance test
  is a real result and the item does not close.
- **Control 3 — no classified building regressed.** Zero failures among the 1,299 classified
  buildings, as in run 3.

### T02 — Record attempt 4 and recommend

**What.** Write `../extra/MEASUREMENT_open-55_acceptance-test-attempt4.md`: what ran, the three
controls, the divergence count, the drawn-equipment-density distribution before and after the screen,
and a recommendation to the director on OPEN-55 and OPEN-49.

**Why.** The director signs closures; you recommend.

**How to test.** Every number in the doc traceable to a named artifact on disk.

### ⏸️ CP-1 — STOP AND REPORT

Report T01's three controls and T02's recommendation. **Do not start T03.** The director decides
whether the fleet re-run proceeds on this evidence.

---

### T03 — Submit the full 12-cell fleet re-run

**What.** `open48_fleet_run4.py`, all twelve cells, current HEAD, into `open48_refleet4`.

**Why.** The adopted `157.1 kWh/m²` predates OPEN-35, OPEN-49, OPEN-55's screen and OPEN-01's fix.
A restatement requires new simulation output for the whole fleet, not a patch of 21 buildings.

**How.** `sbatch --array`, **in waves** under the ≈20k cap, fire-and-forget. Record every job ID.
Then **stop touching the cluster** except `squeue`/`sacct`.

**How to test.** Every cell's job accepted and one real task observed running before you leave the
submission unattended.

### T04 — Harvest and recompute the pooled figure

**What.** Harvest all twelve cells; recompute **pooled** EUI = total simulated energy ÷ total
simulated floor area over all successful buildings.

**Why.** OPEN-43 settled that the headline is the pooled figure, never a mean of cell means.

**How to test.**
- Per-cell success counts recorded, and the **failure count and its causes** recorded beside them.
  🔴 A restatement computed over a silently smaller population is the exact defect OPEN-43 named.
- The 21 OPEN-35 buildings identified in the output and their floor counts confirmed changed.
- `nyc_suburban`'s Unknown divergence count consistent with T01's.

### T05 — Write the restatement record

**What.** `../extra/MEASUREMENT_fleet-restatement-2026-08-19.md` — the new pooled figure, the
population it is computed over, the delta from 157.1, and **an attribution of that delta across the
four code changes in §1.2 as far as the evidence supports**, stating plainly where it does not.

🔴 **The document must carry the OPEN-56 caveat from §1.2** — the number is knowably low by
≈1 kWh/m² until OPEN-56 is fixed.

**How to test.** No figure in the doc unsourced; the caveat present and unhedged.

### ⏸️ CP-2 — STOP AND REPORT

Report the pooled figure and the delta. **You do not publish it.** The director restates the
baseline in the register, the checklist and the board.

---

## 8. Progress log

*(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD`, then Artifacts /
Deviations / Test status / Notes.)*

#### T01 — Run the OPEN-55 acceptance test, attempt 4 — completed 2026-08-19

**Artifacts.** `scripts/validation/open48_t02_attempt4.py` (new launcher, copy of attempt 3 per
§4). Run log `%LOCALAPPDATA%\Temp\open48_t02_attempt4\nyc_suburban.log`, heartbeat
`...\nyc_suburban.heartbeat.log`, exit code file `...\nyc_suburban.EXITCODE` = `0`. Gates report
and deliverables copied to
`docs/validations/overAll/results/open48_refleet3_t02a4/nyc_suburban/`. Cluster job **1274983**,
all 1,589 array tasks `COMPLETED`. Remote fleet dir
`/speed-scratch/o_iseri/fleets/open48_refleet3_t02a4_nyc_suburban`.

**Deviations.** None from the plan's §4/§7 spec. Run took 32.0 min end to end (local IDF gen
295.0 s, cluster submit+poll+fetch+verify+step5 the remainder) — run in the foreground throughout,
polled actively via repeated bounded foreground checks per §3 rule 3, never backgrounded-and-left.

**Test status.** All three preflight checks passed (frozen-source MD5 match, local subdir absent,
remote fleet dir absent). The remote completeness probe (OPEN-57's fix) did **not** raise —
read back cleanly as `0/1589` on first call, its first-ever clean exercise against a 1,589-id
fleet. No STOP was triggered anywhere in the run; §3 condition 1 of the dispatch (capture stderr
and STOP on a repeat probe fault) does not apply.

**Notes.** 1,589/1,589 IDFs generated, LIVE_SMOKE both gates PASS, all 1,589 array tasks
`COMPLETED` on the cluster, `verify_and_repair` reported zero-fail (all 1,589 buildings completed
successfully — no repair needed), simulation manifest 1,589/1,589 success, 0 failed. Full control
results are in T02's measurement doc (§ below); headline: **divergence count 0/290 Unknown, vs.
the pre-fix baseline of 71.**

#### T02 — Record attempt 4 and recommend — completed 2026-08-19

**Artifacts.**
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-55_acceptance-test-attempt4.md` — full record of
what ran, the three controls (all PASS, independently re-derived rather than carried forward from
attempt 3), the before/after drawn equipment-density distribution, supporting single-cell gate
numbers, and a recommendation to close both OPEN-55 and OPEN-49.

**Deviations.** None. Every number in the doc is traceable to a named on-disk artifact (the run
log, the gates report, or an independent re-derivation script run against this run's own seeded
`01_buildings.gpkg`, both cited).

**Test status.** Control 1 (archetype histogram) bit-identical to the pre-registered baseline,
re-derived independently on this run's own input rather than carried over. Control 2 (divergence
count): **0/290, pre-registered prediction "substantially below 71" — met with the floor value,
reported plainly, no rationalisation needed since it is an unambiguous pass.** Control 3 (no
classified-building regression): 0 failures among the 1,299 classified buildings.

**Notes.** Recommendation only — the register, checklist and director prompt were **not** edited
by this executor, per §3 rule 6. The director decides both closures and whether T03 (the fleet
re-run) proceeds.

#### T03 — Submit the full 12-cell fleet re-run — completed 2026-08-19

**Artifacts.** `scripts/validation/open48_fleet_run4.py` (new launcher, copy of run 3 per §4,
`OUTPUT_SUBDIR="open48_refleet4"`, `MAX_PARALLEL=4`/`STAGGER_S=240`/`POLL_S=30` pinned unchanged).
Seed copy verified: all 12 cells' `01_buildings.gpkg` copied `open48_refleet3` → `open48_refleet4`
and MD5-reverified against the director's 2026-08-19 manifest, byte-identical, before launch.
Driver logs under `%LOCALAPPDATA%\Temp\open48_run4\`. All 12 jobs accepted and observed `RUNNING`
via `squeue` before the submission was left unattended (nyc_urban job 1276771 had running array
tasks at first check). Job IDs: nyc_rural 1276716, nyc_suburban 1276585, nyc_urban 1276771,
nyc_centre 1278791, la_centre 1279206 (+repair 1282390), la_urban 1280049 (+repair 1284095),
la_suburban 1280888, austin_centre 1283295, austin_suburban 1283598, austin_rural 1284589.
`la_rural` and `austin_urban` failed under the main driver (see below) and were re-run solo:
la_rural 1283145 (+repair 1283440, +reroute 1283836), austin_urban 1284163.

**Deviations.** Two cells (`la_rural`, `austin_urban`) died `rc=1` under the main driver on an
identical SSH transport drop (`Connection closed by 132.205.2.12 port 22`, exit 255), diagnosed and
retried solo per the honesty/no-blind-retry rule — full post-mortem in
`../extra/INVESTIGATION_open48-run4-cell-failures.md` (T-C, written per director instruction). Both
solo retries succeeded on the first attempt. `la_rural`'s retry ran partially concurrent with
3 other main-driver cells and `austin_urban`'s retry ran concurrent with `austin_centre` for its
first ~6 minutes — disclosed in the investigation doc §4, not run in strict isolation as the
director's later instruction (received after both retries were already launched) specified.

**Test status.** All 12 cells' jobs accepted; running tasks observed via `squeue` before leaving
the submission unattended. Total fleet fetched across all 12 cells: **8,160 buildings**, matching
the plan header's stated fleet size.

**Notes.** Director took over the base-vs-run4 diff analysis directly (levels, archetype flips,
the area==200.0 signature, `way/266034056`) and instructed this executor not to re-derive it. Per
director instruction 2026-08-19 20:33/20:52, T04's originally planned pooled-EUI computation was
**not performed** — the director's live redirection stopped this executor at per-cell success/failure
reporting and the T-C investigation doc; no pooled fleet figure was computed or published. T05 was
not started for the same reason. See chat report for full per-cell counts.

#### T03 — Submit the full 12-cell fleet re-run — IN FLIGHT, director note 2026-08-19 19:45

**Director note, not an executor entry.** A fresh manager session picked the arc up at 19:43 with the
run already under way and no executor session alive; the driver is a detached process and survived
the session that started it.

**What is running.** `scripts/validation/open48_fleet_run4.py`, launched 16:21:59, `MAX_PARALLEL = 4`,
`STAGGER_S = 240`, one child process and one log per cell under `%LOCALAPPDATA%\Temp\open48_run4\`,
outputs under `%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet4\`. Preflight passed 12/12 on the
seeded `01_buildings.gpkg`, so the OSM input is frozen against runs 2 and 3 and the comparison stays
single-variable.

**Deviation from the plan as written, recorded not hidden.** §7 T03 says `sbatch --array` in waves.
The launcher instead drives `v12_cell_pipeline.run_cell` per cell, which generates locally and then
ships and `sbatch`es that cell's own array. No compute runs on the login node either way, so the hard
rule is not broken, but the plan's wording does not describe what is running and the difference is
recorded here rather than glossed.

**State at 19:43:31.** DONE rc=0: `nyc_rural` (14 min), `nyc_suburban` (33 min), `nyc_urban`
(106 min), `la_suburban` (90 min). RUNNING: `nyc_centre` (202 min), `la_centre` (176 min),
`la_urban` (161 min). PENDING: the four `austin_*` cells. **FAILED rc=1: `la_rural`.**

🔴 **`la_rural` failed and must be re-run — it is not a modelling failure and its numbers are not
missing for any scientific reason.** It completed generation cleanly (149/149 IDFs in 48.2 s, both
LIVE_SMOKE gates PASS, Unknown 0.0 %) and then died on the very first remote call of the shipping
step: `_ssh` `mkdir -p …/open48_refleet4_la_rural/{idfs,weather,out}` exited **255**, stderr
`Connection closed by 132.205.2.12 port 22`. That is SSH transport, one minute after launch, with
four cells already holding connections.

⚠️ **The launcher's own docstring predicted this cell, at a higher concurrency:** *"Six concurrent
cells saturated the SSH link to speed-submit2 and killed la_rural on scp."* `MAX_PARALLEL = 4` did
not prevent it. **The remedy is to re-run `la_rural` alone once the queue drains, not to raise
parallelism and not to score the fleet without it.** A pooled figure computed over eleven cells would
be exactly the silently-smaller-population defect OPEN-43 named, and T04's success-count control
exists to catch it.

**Nothing has been retried, moved or deleted.** The failed cell's local work dir is left as it is.

#### T04 — Harvest all twelve cells and recompute the pooled fleet EUI — completed 2026-08-19 (director)

**Artifacts:** `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4/<cell>/results/05_results.csv`
(twelve cells) · analysis scripts under `%LOCALAPPDATA%/Temp/open48_run4/` (`pooled12.py`,
`attrib.py`, `flags.py`, `unk.py`, `unkcell.py`, `decomp.py`, `unkattrib.py`).

**Result.** Pooled fleet EUI **153.8231 kWh/m²** over **8,153** successful buildings and
**24,320,582 m²**, against the adopted **157.0552** over **8,154** and **23,545,868 m²** —
**−3.2321 kWh/m², −2.06 %**. The baseline side was recomputed from `phaseE_elevrb`'s own twelve
`05_results.csv` by the same code path and reproduces `157.0552` to 4 dp, so the two are comparable.
Per-cell success/failure counts are in §2 of the measurement doc; failures are **7** in run 4 against
**6** in the baseline (la_rural 5 and la_urban 1 in both — pre-existing temperature-out-of-bounds
drops — plus one new, `nyc_centre / way/266034056`).

**The three checks this task owed:**

1. **OPEN-35's 21 buildings** — **20 of 21 carry the floor-count change** (austin_centre 5, la_urban 3,
   nyc_centre **7**, nyc_urban 5), every one upward from a bogus `levels = 1.0` to a real storey count.
   The 21st is `way/266034056`, which no longer simulates — see the deviation below.
2. **nyc_suburban's Unknown divergence against T01's 0/290** — **no divergence.** Run 4 reproduces
   **290** Unknown of 1,589 exactly, identical to the baseline, 18.3 %, under the 20 % LIVE_SMOKE
   ceiling. Unknown counts are identical in all twelve cells except nyc_centre (31 → 35).
3. **osm_id set integrity** — symmetric difference is **zero in every cell**, so the restatement is of
   the same fleet and not of a different population.

**Deviations.** (a) The plan expected 21 floor-count changes and 20 landed; the cause is established,
not assumed — `way/266034056`'s run-4 IDF carries `Storey 0…18`, EnergyPlus diverges at
`CalcHeatBalanceInsideSurf` (1,940,305 °C), the pipeline's own zero-area-surface strip and reroute to
`one_zone_per_floor` both fail (2.04e7 °C), and it is dropped under B2 tolerance. **This is a
regression introduced by the OPEN-35 fix**, on 1 of the 21 buildings it touches; in the baseline the
building was 1 storey and ran at 307.23 kWh/m². **No ID was opened — that is the user's call and it is
carried to CP-2.** (b) The task was performed by the director rather than the executor: the executor
was redirected mid-task to the failure post-mortem only, and was explicitly instructed not to compute
or publish a pooled figure.

**Test status.** No test run — this task is measurement over existing artifacts and touches no code.

---

#### T05 — Write the restatement record — completed 2026-08-19 (director)

**Artifacts:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_fleet-restatement-2026-08-19.md`.

**Attribution, which is the substance of the task.** The restatement is **one change**. Splitting the
fleet on `OpenUBEMUnknown`: that population (650 buildings, 3.7 % of fleet floor area) moves
**223.44 → 107.22, −52.01 %**; everything else (7,504 buildings, 96.3 %) moves **154.51 → 155.55,
+0.68 %**. Counterfactual with Unknown frozen at baseline = **157.9836**, so **Unknown contributes
−4.1606** and **everything else +0.9285**. Mechanism cited in code: OPEN-55's B+ screen
(`openubem/semantic/__init__.py`, `_UNKNOWN_DONOR_EXCLUDE`) lowers the upper bound of the Unknown PDE
uniform draw by removing the data-centre, `Laboratory` and restaurant archetypes from the donor pool.
A second decomposition on the 35 structurally changed buildings isolates structure at **+0.6551** and
the draw side at **−3.8872**, confirming the same reading from the other direction.

**The OPEN-56 caveat is stated unhedged, as §5 of this plan required.** `153.8231` is **not**
volume-correct: OPEN-56 is open and unremedied, 8,160/8,160 buildings still simulate with a 10 m³
zone-volume stub, measured at **≈ +1.0 kWh/m²** per building on the 69-building twelve-cell control.
That correction is **not** inside the restated figure. A volume-correct run-4 fleet would be
**≈ 154.8 kWh/m²** — named in the doc, explicitly not adopted.

**Deviations.** The doc carries a §9 retracting two claims the director made during the run —
the "null-island centroid" signature (false: `centroid_lat` is near zero for every building in every
cell in both runs) and the first reading of `way/266034056` as a pre-existing degenerate footprint
(it is a new drop). Recording retractions was not in the task spec; it is added because both claims
had already been passed to an executor and would otherwise propagate.

**Test status.** No test run — documentation task.

---

### ✅ CP-2 — SIGNED 2026-08-19 (late), director

**What was reported, per the checkpoint's own terms.** The pooled figure and the delta:
**`153.8231 kWh/m²` over 8,153 buildings, −3.2321 / −2.06 % against `157.0552`.** The checkpoint says
the executor does not publish it and the director restates it in the register, the checklist and the
board. **Done, in all four places:**

| surface | state |
|---|---|
| `INVESTIGATION_open-items-register.md` | §1 amendment appended — baseline restated, attribution, both owed decisions, both retractions. **No item opened or closed: 19 live / 40 struck / 59 total, next free `OPEN-60`, invariant untouched.** |
| `docs/PROJECT_CHECKLIST.md` | §0 baseline line restated `157.1` → **`153.8`**, with a plain-language paragraph on what changed and a second on the two things waiting on the user. |
| `prompts/DIRECTOR_PROMPT_openings.md` | New **🟨🟨🟨🟨🟨 RESUME box** superseding the 🟩 one (whose 25/31/56 counts were stale by three passes), plus the header supersession note. |
| progress board artifact | Updated in place. |

**Carried to the user, and deliberately NOT taken by the director:**

1. **An ID and a remedy ruling for the OPEN-35 regression** on `nyc_centre / way/266034056`.
2. **Adjudication of the 4 `Courthouse` → `OpenUBEMUnknown` flips** — 477,804 m², one building of
   157,115 m²; fleet floor area in `Unknown` rises 392,848 → 870,652 m² (2.2×) on a count move of
   646 → 650.
3. **OPEN-56's remedy ruling** (carried from CP-1), now doubly load-bearing because it is the named
   caveat on the newly adopted headline.

**Cluster note.** Two cells (`la_rural`, `austin_urban`) failed once each on an identical transient
SSH drop (`Connection closed by 132.205.2.12 port 22`, exit 255) at the first remote-touching call,
**before any upload or `sbatch`** — nothing orphaned remotely. Both succeeded on a solo retry, first
attempt. Parallelism was **not** raised. Post-mortem:
`extra/INVESTIGATION_open48-run4-cell-failures.md`.
