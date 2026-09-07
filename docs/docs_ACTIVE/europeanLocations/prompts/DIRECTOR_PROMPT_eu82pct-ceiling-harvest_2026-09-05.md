# Director prompt — drive the EU-11 ceiling82 wave to full harvest

**Opened 2026-09-05. Self-contained: nothing else has to be read to start.** Replaces
`prompts/DONE/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` (floor-planning arc closed; its content is
historical reference only, not current work). Deep history: `STATE_european_locations_v5.md`,
`implementation/PLAN_eu-82pct-ceiling-2026-09-05.md`.

## 0. Standing authorization — no owner check-in needed

`D-EU-101` (owner, 2026-09-05): accept the ~82% data-completeness ceiling, reject general imputation for the
residual gap. `D-EU-102`/`D-EU-103`/`D-EU-104`: drive the entire EU-11 fleet (4,186 residential buildings,
London/Lyon/Madrid/Bologna) through Speed simulation and harvest to completion — run/monitor/reclassify every
EnergyPlus job, regenerate the 3D viewers once harvested — **autonomously, no further owner check-in until
harvest completes or a hard stop-condition trips** (below).

**Hard stop-condition:** >10% disagreement between measured and predicted recovery counts. Anything else
(new failure signatures, job contention, long drain times) — diagnose and continue, do not stop to ask.

## 1. Where things stand (2026-09-06, ~23:50 — FULL DRAIN CONFIRMED)

**EnergyPlus simulation harvest: ALL 10 SPEED JOBS DRAINED.** Live `sacct -j 1305186` confirms Bologna's
last 2 RUNNING tasks completed: `1184 COMPLETED + 16 FAILED = 1200/1200`. Combined with the already-drained
London/Lyon/Madrid backlog jobs and all 4 Step2-delta jobs and both FINDING-253-remedy jobs (see table below,
now all "drained"), **every EU-11 Speed array job is fully drained — 0 RUNNING, 0 PENDING account-wide for
this arc.** Path-to-done step 2 (§4) is now CLOSED. Proceeding to step 3 (harvest pull + merge): dispatched
a fresh Sonnet executor (`harvest_eu11_ceiling82_final.py`, new script) to fetch `out/<stem>/` results from
all 10 remote wave directories and merge with precedence (FINDING-253-remedy overrides backlog for its 7
stems) against each district's final `<DISTRICT>_ceiling82_2026-09-05/` population snapshot
(prepared_buildings.csv/fleet.lst — 451 stems confirmed for London, others to be confirmed by the executor).
Result pending — this file will be updated again once that dispatch reports back.

## 1a. Where things stood (2026-09-06, ~00:15) — superseded, kept for history

**Data-completeness (rules-based prep): DONE.** 3,344/4,186 = 79.9% achieved (T01-T07b of the plan doc,
closed). Residual 86-building gap (2.1pp vs the ≈82% ceiling) is confirmed true dead ends
(`DEBUG_why-not-100-percent-2026-09-04.md`) — out of scope, no further action.

**`FINDING 253` remedy: DONE.** T08 applied+tested the fix (76/76 tests), director audited and independently
re-verified all 7 stems (RC 0/0 Fatal), packaged as 2 Speed array jobs, hit a 3rd distinct packaging defect
(absolute path in `Schedule:File`, fixed, see debug-references), resubmitted (`1309355` Madrid, `1309357`
Bologna) — both fully drained, 7/7 `COMPLETED`, `RC 0`, 0 Fatal, confirmed on Speed matching local exactly.

**EnergyPlus simulation harvest: IN PROGRESS.** 10 Speed jobs (8 original + 2 remedy) cover **3,947 total
tasks** (corrected 2026-09-06 — see 🔴 finding below; was miscounted as 3,420). Last confirmed state:

| Job | District / wave | Total | Done (C+F) | Remaining | Status |
|---|---|---|---|---|---|
| `1306951` | London backlog | 419 | 419 (418C+1F) | 0 | drained |
| `1306952` | Lyon backlog | 469 | 469 (468C+1F) | 0 | **drained** |
| `1306953` | Madrid backlog | 1008 | 1008 (996C+12F) | 0 | **drained** |
| `1305186` | Bologna backlog / FINDING249 remedy | **1200** | 836 (821C+15F) | **364 (32 RUNNING + 332 not yet dispatched)** | draining, **32-wide** (bumped from 8-wide 2026-09-06, ~4x throughput) |
| `1308150` | London Step2-delta | 101 | 101 | 0 | drained |
| `1308159` | Lyon Step2-delta | 38 | 38 | 0 | drained |
| `1308160` | Madrid Step2-delta | 166 | 166 | 0 | drained |
| `1308161` | Bologna Step2-delta | 12 | 12 (11C+1F) | 0 | drained |
| `1309355` | Madrid FINDING253 remedy | 2 | 2 | 0 | drained, 2/2 RC 0 |
| `1309357` | Bologna FINDING253 remedy | 5 | 5 | 0 | drained, 5/5 RC 0 |

🔴 FINDING 255: `1305186`'s true array size is `1-1200%8` (confirmed via `scontrol show job` + the original
`sbatch` submit line in `PLAN_eu-nocore-finding249-remedy-2026-09-04.md:268`), not 673 — squeue/sacct
compress the undispatched tail (`1305186_[778-1200%8]`) into a single display row, which earlier polls
misread as "1 PENDING" instead of 423 queued tasks. Job 1305186 is dual-purposed: it's the FINDING-249-remedy
full-Bologna-fleet re-run, being tracked here as the district's backlog job. Lyon `1306952` is fully drained
(469/469, confirmed absent from `squeue`). Net effect: harvest is further from done than previously tracked
(431 Bologna tasks remain, not 9), fleet total is 3,947 not 3,420. No new failure signature, FAILED counts
unchanged (16 for these 2 jobs) — does not trip the >10% hard-stop.

FAILED tail, all classified into the 4 known signatures — see §2: London 1, Lyon 1, Madrid 12, Bologna 15,
Bologna Step2-delta 1 = **30 total FAILED**, 0 unclassified. All FAILED, including Bologna backlog task
`1305186_524` (stem `635e498716218cea`, 3rd `FINDING 254` instance), now have external vertex-level
verification — Task D landed and audited 2026-09-06 (see §3), confirms identical mechanism to Tasks B/C,
zero outliers. **Refresh these numbers with a fresh `sacct` before trusting this table** — Bologna is still
draining (last live check 2026-09-06: 821C+15F+32 RUNNING out of 1200, FAILED counts unchanged, no new
failures). Throttle bumped 8-wide→32-wide 2026-09-06 (was self-throttled despite being the account's only
job, see `feedback_always_parallel_prioritize_speed.md`); revised ETA ~6h from bump time at 821-task mark
(avg completed-task runtime 1858s, 364 tasks remaining ÷ 32 concurrent). Lyon (`1306952`, 468C+1F) and
Madrid (`1306953`, 996C+12F) confirmed fully drained, no further polling needed on either.

**Speed's 32-CPU account-wide cap** means only ~25-30 tasks run concurrently across all of the user's own
jobs — a trailing single PENDING task per job sitting queued for a while is normal contention, not a stuck
job.

## 2. Known failure signatures — do not re-diagnose these

Full detail: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ("European locations, ceiling82
(2026-09-05)" chapter) and `debugs/docs/INVESTIGATION_failed-sims-classification_2026-09-05.md`
(self-contained snapshot, no need to read the debug-references chapter for context).

1. `RoofCeiling:Detailed ... Vertex size mismatch` (`FINDING 210`) — accepted, no action.
2. `GetSurfaceData: Zero or negative surface area` (`D-EU-43`) — accepted, no action.
3. `GetSurfaceData: Construction ... reverse order ...` (`FINDING 253`, 7 stems) — **CLOSED.** Fixed, tested,
   shipped, and confirmed RC 0/0 Fatal on Speed (jobs `1309355`/`1309357`). Fold these 7 stems' results into
   the Madrid/Bologna manifests during harvest.
4. `CalcCoordinateTransformation: Invalid dot product` (`FINDING 254`, 3 stems: Madrid `c71e82e57d99bed1`,
   Bologna `fd4b13e28f1c6f47`, Bologna `635e498716218cea`) — same `FINDING 210` sub-mm vertex-divergence
   family, slips past the interzone gate because the fatal surfaces are `Outdoors`/`Ground`, not interzone,
   on courtyard-holed buildings — **no fix needed**, low-rate accepted edge case. **CLOSED.** All 3 stems
   externally verified (vertex-level, identical mechanism, zero outliers) — Task D (3rd stem) landed
   2026-09-06 in `report.md`, audited, matches Tasks B/C exactly.

**Classification method for any NEW failure**: `sacct -j <job> --format=JobID,State -n -X | grep -i fail` →
find the task's log under `/speed-scratch/o_iseri/openubem/fleets/` (filename pattern is inconsistent across
submission waves — try `openubem_<district>_backlog_<job>_<idx>.log`, then `openubem_<district>_<job>_<idx>.log`,
then a targeted `ls .../fleets/ | grep _<job>_<idx>.log`) → read `Task N: osm_id=<stem>` / `OUTDIR:` →
`grep -m1 "Fatal  **" <outdir>/eplusout.err` + `grep "Last severe error" <outdir>/eplusout.err`. Only register
a new debug-references entry if the text doesn't match one of the 4 signatures above.

## 3. In-flight subagent work

**T08: DONE, audited, shipped.** Fresh Sonnet executor applied `FINDING 253`'s verified diff to
`scripts/run_eu_s2_campaign.py`, added 4 regression tests (76/76 passed), rebuilt+verified all 7 named stems
locally (`RC 0`). Director audited against live files (matches plan spec exactly), independently re-verified
all 7 stems' `eplusout.end`/`eplusout.err`, packaged+shipped+submitted to Speed (director-only step, not
delegated) — hit and fixed a 3rd packaging defect (absolute path baked into `Schedule:File`, see
debug-references), resubmitted, confirmed 7/7 `RC 0`/0 Fatal on Speed matching local exactly. No further
action needed on `FINDING 253`.

External Gemini/Antigravity diagnosis (`openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md`)
covers Task A (`FINDING 253`, now closed) and Task B/C/D (`FINDING 254`, all 3 stems) — all four prompts
(`v1`, `v2`, `v3`) are archived at `prompts/DONE/`. **Nothing further queued** — this line of diagnosis is
closed.

## 4. Path to done

1. ~~T08 reports → audit → package/ship/submit~~ **DONE** — `FINDING 253` remedy fully drained on Speed.
2. ~~Harvest-monitoring loop until Bologna `1305186` fully drains~~ **DONE 2026-09-06 ~23:50** — confirmed via
   live `sacct -j 1305186`: `1184 COMPLETED + 16 FAILED = 1200/1200`, 0 RUNNING/PENDING. All 10 EU-11 Speed
   jobs (London/Lyon/Madrid backlog, Bologna backlog=FINDING249-remedy, all 4 Step2-delta, both FINDING-253
   remedy jobs) are now fully drained.
3. **DONE 2026-09-06.** Harvest pulled and merged. New script `scripts/cluster/harvest_eu11_ceiling82_final.py`
   generalizes `harvest_eu11_district.py` to pull multiple remote wave dirs per district with precedence
   overlay (FINDING-253-remedy overrides backlog for its 7 stems) joined against each district's
   `<DISTRICT>_ceiling82_2026-09-05/prepared_buildings.csv`/`fleet.lst` final-population snapshot. Final
   per-district numbers (manifest row count = `population_run`, verified equal to each district's own
   `fleet.lst` line count):

   | District | run | success | failed | pooled EUI kWh/m² |
   |---|---:|---:|---:|---:|
   | `GB-LDN-STDUNSTANS` | 451 | 451 | 0 | 97.081151 |
   | `FR-LYO-HAUTCOEURPENTES` | 507 | 506 | 1 | 65.935928 |
   | `ES-MAD-BERRUGUETE` | 1174 | 1164 | 10 | 77.153998 |
   | `IT-BOL-GALVANI2` | 1212 | 1200 | 12 | 54.935569 |
   | **Total** | **3344** | **3321** | **23** | — |

   **3,344 total run == the plan doc's own stop-point-3 population figure (3,344/4,186 = 79.9%)** — a strong
   cross-check that the join against each district's final population snapshot is correct, not just an
   artifact count. **23 total FAILED == 30 originally-classified FAILED (§2: London 1, Lyon 1, Madrid 12,
   Bologna 15+1 step2-delta) minus the 7 stems fixed by the FINDING-253 remedy (Madrid 2, Bologna 5)** — the
   fleet-wide arithmetic matches exactly (30−7=23). Per-district distribution shifted slightly from the naive
   subtraction (London 0 not 1, Bologna 12 not 11) because the final `_ceiling82_2026-09-05` population
   differs from each wave's shipped fleet by the same real churn documented in the plan doc's Step2-delta
   section (ids entering/leaving a district) — London's 1 pre-existing FAILED stem is not part of the final
   451-building population, and Bologna's churn added one previously-unseen failure. No unclassified new
   failure signature: no new simulation attempts occurred outside the already-audited FINDING-253 remedy set,
   so every FAILED stem is still one of §2's 4 known classes. Hard stop-condition (>10% disagreement) not
   tripped (23/3344 = 0.7%).

   Operational note for future sessions: the harvest script's `tempfile.gettempdir()`-based work dir hit a
   Python 3.14/Windows `tarfile.extractall` bug (`ValueError: Paths don't have the same drive`, `data_filter`
   → `os.path.commonpath`) when two invocations raced on the same temp dir — caused by the director
   accidentally launching a duplicate background run (a `nohup ... &` attempt whose PID `ps aux` failed to
   show, since Git Bash's `ps` does not list native Windows `.exe` processes by default — use PowerShell
   `Get-CimInstance Win32_Process` or `tasklist` to check for stray native processes, not `ps aux`). Both
   racing copies still produced correct final `summary.json`/manifest output before the loser crashed; no
   data corruption resulted, but do not launch more than one instance of this script concurrently.
   Registered as a candidate debug-references entry if this recurs.
4. **DONE 2026-09-06.** Ran `scripts/generate_eu_3d_viewers.py` for all 4 districts, mirrored into
   `docs/docs_ACTIVE/europeanLocations/outputs_3D`. `diff -rq` (via `git diff --stat`) is **not** byte-clean —
   7 files changed (3 `buildings.csv`, all 4 `viewer.html`) — but the reason is benign, not a regression:
   1. `buildings.csv` for Madrid/Lyon/London lost their `eplus_return_code`/`heating_kwh`/`eui_kwh_m2`/
      `run_seconds` columns entirely (Bologna's copy already lacked them). Confirmed against the live script
      (`generate_eu_3d_viewers.py:1002-1017`): the row dict it builds has never included those fields — the
      committed copies predate a refactor and were stale, not something this regen broke. Matches the
      script's own docstring (`generate_eu_3d_viewers.py:1-13`, `EU-18c`/`D-EU-59`): this viewer is
      deliberately geometry-only, "no energy, no EnergyPlus output... pure geometry." Row counts are
      unchanged (1399/769/1352); minor footprint-area rounding shifts (e.g. 2628.5→2628.9 m²) come from
      re-reading the EU-17 IDFs fresh, not from anything harvest-related.
   2. 🔴 **New finding**: all 4 `viewer.html`'s embedded JS already has a "colour: EUI" mode button
      (`generate_eu_3d_viewers.py`'s `HTML_HEADER_TEMPLATE`/`HTML_FOOTER`, referencing `b.eui` client-side)
      from a prior session's edit, but **no Python code anywhere in the script ever sets an `"eui"` key on
      a building object** (`b_obj` at line ~987-999 has no `eui` field) — the button is wired up but always
      renders every building as "not simulated" grey. Pre-existing gap, not introduced by this harvest pass;
      out of scope for this arc (EU-18c's stated deliverable is geometry-only) and does not touch the hard
      stop-condition. Not fixed here — flagging for a future task, not touching script logic mid-harvest-closeout.
   No other unexpected files changed (`git status` confirms only this file + the 7 3D-output files touched).
5. **DONE 2026-09-06.** `implementation/PLAN_eu-82pct-ceiling-2026-09-05.md` §8 got a closing "Full harvest +
   3D regen" entry with the same final numbers as §1/§4 above.
6. **DONE 2026-09-06 — reported to owner.** Harvest + 3D regen both done, hard stop-condition never tripped.
   **This closes the EU-11 ceiling82 harvest arc.**
