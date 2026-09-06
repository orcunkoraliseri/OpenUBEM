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

## 1. Where things stand (2026-09-06, ~00:15)

**Data-completeness (rules-based prep): DONE.** 3,344/4,186 = 79.9% achieved (T01-T07b of the plan doc,
closed). Residual 86-building gap (2.1pp vs the ≈82% ceiling) is confirmed true dead ends
(`DEBUG_why-not-100-percent-2026-09-04.md`) — out of scope, no further action.

**`FINDING 253` remedy: DONE.** T08 applied+tested the fix (76/76 tests), director audited and independently
re-verified all 7 stems (RC 0/0 Fatal), packaged as 2 Speed array jobs, hit a 3rd distinct packaging defect
(absolute path in `Schedule:File`, fixed, see debug-references), resubmitted (`1309355` Madrid, `1309357`
Bologna) — both fully drained, 7/7 `COMPLETED`, `RC 0`, 0 Fatal, confirmed on Speed matching local exactly.

**EnergyPlus simulation harvest: IN PROGRESS.** 10 Speed jobs (8 original + 2 remedy) cover 3,420 total tasks.
Last confirmed state:

| Job | District / wave | Done (C+F) | Remaining | Status |
|---|---|---|---|---|
| `1306951` | London backlog | 419 (418C+1F) | 0 | drained |
| `1306952` | Lyon backlog | 468 (467C+1F) | 1 RUNNING | nearly drained |
| `1306953` | Madrid backlog | 1008 (996C+12F) | 0 | **drained** |
| `1305186` | Bologna backlog | 673 (658C+15F) | 8 RUNNING + 1 PENDING | draining, 8-wide |
| `1308150` | London Step2-delta | 101 | 0 | drained |
| `1308159` | Lyon Step2-delta | 38 | 0 | drained |
| `1308160` | Madrid Step2-delta | 166 | 0 | drained |
| `1308161` | Bologna Step2-delta | 12 (11C+1F) | 0 | drained |
| `1309355` | Madrid FINDING253 remedy | 2 | 0 | drained, 2/2 RC 0 |
| `1309357` | Bologna FINDING253 remedy | 5 | 0 | drained, 5/5 RC 0 |

FAILED tail, all classified into the 4 known signatures — see §2: London 1, Lyon 1, Madrid 12, Bologna 15,
Bologna Step2-delta 1 = **30 total FAILED**, 0 unclassified. All FAILED, including Bologna backlog task
`1305186_524` (stem `635e498716218cea`, 3rd `FINDING 254` instance), now have external vertex-level
verification — Task D landed and audited 2026-09-06 (see §3), confirms identical mechanism to Tasks B/C,
zero outliers. **Refresh these numbers with a fresh `sacct` before trusting this table** — Lyon/Bologna are
still draining (last live check 2026-09-06: Bologna 8 RUNNING+1 PENDING/673, Lyon 1 RUNNING/468, FAILED
counts unchanged, no new failures).

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
2. Continue the ~30-min harvest-monitoring loop (`sacct` across all active jobs, reclassify any FAILED-count
   growth per §2's method) until the last 2 jobs — Lyon `1306952` (1 task RUNNING) and Bologna `1305186`
   (8 RUNNING + 1 PENDING) — are fully drained (COMPLETED + only accepted-class FAILED, no RUNNING/PENDING).
   Everything else (London backlog, Madrid backlog, all 4 Step2-delta, both FINDING-253 remedy jobs) is
   already drained. Task D diagnosis (§3) is done — nothing further to dispatch.
3. Harvest: pull `out/<stem>/` SQL results back from Speed for all 4 districts, merge Step1 + Step2-delta +
   FINDING-253-remedy results into each district's final manifest/`summary.json`.
4. Run `scripts/generate_eu_3d_viewers.py` for all 4 districts, mirror the regenerated output into
   `docs/docs_ACTIVE/europeanLocations/outputs_3D`, verify `diff -rq` is clean against the previous build.
5. Update `implementation/PLAN_eu-82pct-ceiling-2026-09-05.md` §8 and this file's §1 with the final numbers
   at each milestone (full drain, harvest complete, 3D regen complete).
6. Report to the owner only once harvest + 3D regen are both done, or if hard rule 6 trips.
