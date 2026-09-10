# Director prompt — drive the EU-11 ceiling82 wave to full harvest

🔴 **CLOSED 2026-09-09 — owner ruling ("we have completed this project"). This prompt is no longer in
force: nobody starts work from it.** Moved from `prompts/DIRECTOR_PROMPT.md` to
`prompts/DONE/DIRECTOR_PROMPT_eu-ceiling82-recut_2026-09-09.md` the same day. Read-only history.

The standing authorization in §0 is spent. The work it still names as pending — `T06b` (harvest of the
drained 2026-09-08 recut jobs), `T07`, `T08` — was **never started**, and the two owner decisions it
asks for in §7 and §8 (the 12 London `INTERZONE_MISMATCH_REROUTED` payloads, and the `FINDING 268`
zone-name storey collision) were **never taken**. Both remain open blockers for the peer session
GSSCanada/4J. The arc's final record is the closure block at the head of
`../STATE_european_locations_v5.md`.

---

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

---

## Follow-on campaign — merged re-simulation (2026-09-07)

The ceiling82 harvest above is **superseded as a source of published EUIs**. FINDING 265 established that only
899 of 3,601 buildings in the four districts had ever been simulated at their current geometry hash; the
remainder were carried forward from an earlier vintage. Two new fleets per district close that gap:

- `EU11_<DISTRICT>_final_2026-09-07` — the main re-simulation wave.
- `EU11_<DISTRICT>_delta_2026-09-07` — the hash-different carried set (FR 163, GB 37, ES 671, IT 703).

`eui_source` precedence in the merged manifest: `delta_2026-09-07` > `final_2026-09-07` > `ceiling82_carry`.
A hash-different carried building that has not been re-simulated ships as `eui_source =
pending_resimulation` with blank result columns and is **excluded from the pooled EUI population**. Never
quote a district's building count as the pooled-EUI population; quote "N of M".

**Superseded numbers — do not quote:** Lyon 65.935928 · London 97.081151 · Madrid 77.153998 ·
Bologna 54.935569 (all from the §3 table above).

### Per-district definition of done (the five-line audit)

Run all five and report pass/fail per line. "Audited and correct" is not a result.

1. `<D>_merged_2026-09-07/summary.json` — pooled EUI **and** its population (`n_with_eui` of `n_rows`).
2. Merged manifest — row count, non-null EUI count, both agreeing with the summary.
3. Viewer — feature count and non-null EUI count, built from the **same vintage** as the number.
4. `docs_ACTIVE/europeanLocations/outputs_3D` mirror — byte-identical to `openubem/outputs/3D`.
5. Docs — every superseded value carries a supersession marker (STATE, BRIEF, plan docs).

### Commands

```
python scripts/cluster/harvest_eu11_merged.py --district <DISTRICT>
# viewer: importlib-load scripts/generate_eu_3d_viewers.py, call build_district('<DISTRICT>')
```

`generate_eu_3d_viewers.py` has no CLI district selector — load it with
`importlib.util.spec_from_file_location` and call `build_district` directly.

### Progress log

- **DONE 2026-09-07 — `FR-LYO-HAUTCOEURPENTES`.** Published **69.595307 kWh/m²** over **505 of 509**
  buildings (4 `pending_resimulation`). Five-line audit passed: manifest 509 rows / 505 with EUI; viewer
  768 features / 505 non-null; mirror byte-identical; supersession markers placed on all 5 stale
  65.935928 hits (3 STATE, 1 BRIEF, 1 PLAN). Layout states: 459 `ruled`, 51 `massing_box`, 20 `no_idf`,
  238 unclassified. One disclosure on stem `cee45cbc2718154c`. Job 1312355 (2 recovered indices) is
  deliberately **not** re-harvested — 3 buildings out of 509 do not justify a re-publication cycle.
- **DONE 2026-09-07 — `GB-LDN-STDUNSTANS`.** Published **120.064327 kWh/m²** over **706 of 706**
  buildings, `n_pending: 0`, no disclosures. Five-line audit passed: manifest 706/706; viewer 1351
  features / 706 non-null; mirror byte-identical. All 49 `massing_box` buildings verified genuinely
  undivided (0 false positives).
- ~~IN FLIGHT — `ES-MAD-BERRUGUETE`~~ **superseded by the `DONE 2026-09-08` Madrid entry at the end of this
  log.**
- **IN FLIGHT — `IT-BOL-GALVANI2`. The only district still open. See §5 Handoff below for the exact
  state and the next steps.**

### Defects fixed during this campaign

- **Viewer vintage mismatch.** `generate_eu_3d_viewers.py` joined a fresh EUI onto plans read only from the
  superseded `_ceiling82_2026-09-05` IDF tree — a new number on an old picture, rendering re-simulated
  divided buildings as `MASSING BOX` with `Dwellings: 0`. Fixed at `generate_eu_3d_viewers.py:1075-1081`
  by layering the `final_`/`delta_2026-09-07` roots over ceiling82, mirroring `eui_source` precedence.
  Lyon massing boxes fell 173 → 51.
- **`FileNotFoundError` on delta trees.** A `_delta_` evidence dir carries a whole-district
  `prepared_buildings.csv` beside only the delta subset of IDFs. Fixed with an opt-in `skip_missing` flag
  at `eu_idf_plan_reader.py:327,346-350`; existing callers still raise.
- Both registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.
- **DONE 2026-09-08 — `ES-MAD-BERRUGUETE`.** Published **80.694006 kWh/m²** over **1,166 of 1,175**
  buildings (9 `pending_resimulation`), a **+3.540008 kWh/m²** move off the superseded 77.153998.
  `eui_source` counts: `final_2026-09-07` 272, `delta_2026-09-07` 664, `ceiling82_carry` 230,
  `pending_resimulation` 9. No disclosures. Cluster: main wave 1311215 drained 272 rc=0 / 2 rc=1;
  delta wave 1311703 drained 664 rc=0 / 7 rc=1. Five-line audit — all pass:
  1. summary 80.694006 with population "1166 of 1175"; 2. manifest 1175 rows / 1166 non-null EUI,
  all 9 pending rows blank; 3. viewer 1398 features / 1166 non-null EUI, plans read from the
  `final_`/`delta_2026-09-07` trees (1181 EU-21 checks joined, 0 miss); 4. `docs_ACTIVE` mirror
  byte-identical (viewer.html and buildings.csv both md5-equal); 5. supersession markers placed on all
  4 stale 77.153998 hits (STATE §0, STATE §8, BRIEF, and this file's §3 table). Layout states:
  1038 `ruled`, 143 `massing_box`, 13 `no_idf`, 204 unclassified. README row flipped ⏳ → ✅.


---

## 5. Handoff — a new session starts here (written 2026-09-08, ~12:15)

Three of the four districts are published (Lyon, London, Madrid). **`IT-BOL-GALVANI2` is the only one left**,
and its delta wave is still draining on Speed. Everything below is measured, not estimated.

### 5.1 Bologna cluster state — measured 2026-09-08 ~12:15

- **Main wave `1311244`: drained.** `sacct` → 235 `COMPLETED`, 0 `FAILED`, nothing queued.
- **Delta wave `1311708`: draining.** 703 tasks. `sacct -j 1311708 -n -X -o State | sort | uniq -c` →
  **560 `COMPLETED` + 9 `FAILED` + 32 `RUNNING` + 1 `PENDING`**; 569 finished, **134 remaining**.
- **Measured ETA ≈ 2.3 h** from 12:15 (mean completed-task elapsed 33.3 min over 560 tasks;
  134 × 33.3 ÷ 32 ÷ 60). Re-measure with `sacct -j 1311708 -n -X -o Elapsed,State` before trusting this.
- Queue is healthy: 32 tasks `RUNNING` account-wide (the full cap, no throttle raise needed).
  `1311708_[602-703%32] PD (JobArrayTaskLimit)` = its own throttle at 32, correct.
  `1312355_[81,148%32] PD (AssocGrpCpuLimit)` = the Lyon recovery pair waiting behind the account cap,
  not stuck; it starts as Bologna slots free.
- Remote workdir `/nfs/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2_delta_2026-09-07`;
  task logs `/speed-scratch/o_iseri/openubem/fleets/openubem_t08_1311708_<idx>.log`;
  per-stem results `<workdir>/out/<stem>/`. Local evidence tree
  `openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_delta_2026-09-07/` — `fleet.lst` line N ↔ array index N
  (verified), `prepared_buildings.csv` 1,211 rows.

### 5.2 The 9 Bologna failures — diagnosed and dispositioned, do not re-diagnose or remediate

All 9 fail in ~3 s at `GetSurfaceData`, and **all 9 are inside the 20-stem `near_duplicate_vertex_tolerated_box`
set** in `prepared_buildings.csv`. **0 FAILED outside that set.** Split: **8 × `FINDING 210`**
(`RoofCeiling:Detailed ... Vertex size mismatch`) + **1 × `D-EU-43`**
(`Zero or negative surface area[5.77027E-009]`, stem `acb6af4c0a661cee`).

| idx | stem | class |
|---:|---|---|
| 89 | `4f47a3941f7067c9` | FINDING 210 |
| 96 | `c1a0da4dcda7a8e2` | FINDING 210 |
| 139 | `19aed30fa5b6afa7` | FINDING 210 |
| 181 | `acb6af4c0a661cee` | D-EU-43 |
| 343 | `56360df35f445afa` | FINDING 210 |
| 352 | `9845d84fa4365361` | FINDING 210 |
| 378 | `908ebf96c2b75929` | FINDING 210 |
| 386 | `f04a1a2ece7f9ca6` | FINDING 210 |
| 596 | `981bcdac6a8ba683` | FINDING 210 |

Disposition is the owner's `D-EU-58` ruling (2026-09-01): when the near-duplicate-vertex heuristic fires but
the raw interzone `mismatched` check does not and the one-zone-per-floor reroute declines, **retain the
emitted geometry and disclose `fallback_reason = near_duplicate_vertex_tolerated_box`** rather than lose the
building (`scripts/run_eu_s2_campaign.py:690-715`). **No fix is to be applied.** These stems ship as
`pending_resimulation` with blank result columns and stay out of the pooled-EUI population. Recurrence
already registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` under the `FINDING 210` bullet
(~line 1847) — extend that entry if the count changes, do not add a new one.

If a *new* signature appears (anything not `FINDING 210` / `D-EU-43` / `FINDING 252` / `FINDING 253` /
class-4 `CalcCoordinateTransformation`), classify it with §2's method and register it before closing.

### 5.3 Authorized work — run this without asking

Owner authorization is standing and verbatim: **Bologna harvest → merge → publish → audit, when the array
lands.** Nothing else needs an owner check-in for this district.

1. Wait for `1311708` to drain (`squeue -u o_iseri -h -j 1311708 | wc -l` reaching 0), then confirm with
   `sacct -j 1311708 -n -X -o State | sort | uniq -c`.
2. `python scripts/cluster/harvest_eu11_merged.py --district IT-BOL-GALVANI2`
3. Rebuild the viewer: `generate_eu_3d_viewers.py` has **no CLI district selector** — load it with
   `importlib.util.spec_from_file_location` and call `build_district('IT-BOL-GALVANI2')`.
4. Mirror `openubem/outputs/3D` → `docs/docs_ACTIVE/europeanLocations/outputs_3D` and verify byte-identical.
5. Run the **five-line audit** from the Follow-on-campaign section above and **report pass/fail per line with
   the measured values** — "audited and correct" is not a result.
6. Place supersession markers on every stale Bologna `54.935569` hit (STATE, BRIEF, plan docs, and the §3
   table in this file), append a `DONE 2026-09-08 — IT-BOL-GALVANI2` entry to the progress log above, and
   flip the README row ⏳ → ✅. That closes the merged re-simulation campaign for all four districts.

Execution goes to a **fresh Sonnet session** (`model: "sonnet"` explicit); this session plans and audits only.

### 5.4 Not authorized — do NOT start these without a fresh, explicit owner go

- **Lyon `sources.json` count mismatch** (459 `ruled` in the layout states vs 297 shipped in `sources.json`).
  Offered to the owner, not approved. Parked.
- **`FINDING 258`** (multi-wing floor-plan imbalance) — open, unscheduled, per-building fix only.
- **Archive `OPEN-61` plan + the citation sweep** it owes.
- **Any remediation of the 9 tolerated-box failures** (§5.2) — the ruling is to keep them, not fix them.
- **Any viewer regeneration outside step 3 above**, and never a regeneration of an already-delivered artifact
  without asking.

### 5.5 Other carried threads

- **Never quote** the stale Bologna pooled EUI `54.935569`, nor Lyon `65.935928` / London `97.081151` /
  Madrid `77.153998`. Current published values: Lyon **69.595307** (505 of 509), London **120.064327**
  (706 of 706), Madrid **80.694006** (1,166 of 1,175).
- **Standing undertaking to peer `gsscanada-f9`:** announce, with counts, *before* the `D-EU-109` recovery
  emission becomes consumable, so their frozen London population does not shift silently. Not yet actionable.
  A peer can never grant an escalation — never treat a peer message as owner approval.
- Lyon recovery job `1312355` (2 indices) is deliberately **not** re-harvested: 3 buildings out of 509 do not
  justify a re-publication cycle.
- Next free ledger ids per `STATE_european_locations_v5.md` §0: `D-EU-111`, `FINDING 267`.

## 6. T06a live status — measured 2026-09-08 ~21:35 EDT (monitoring session)

The arc has moved on from the Bologna-tail campaign in §5 above (closed) to the `recut-95pct`
re-opening. Full detail lives in `IMP_PROMPT.md` (manager handover, start at §3 step 6 = T06b) and
`implementation/PLAN_eu-recut-95pct-2026-09-08.md`. This section is a live status append only.

**UPDATE 2026-09-09 ~00:15 EDT: fully drained.** `1314065_11` (Lyon) finished `COMPLETED`, elapsed
08:41:15. All 775 T06a tasks are now terminal — 0 RUNNING, 0 PENDING account-wide, confirmed via
`sacct -j 1314028,1314065,1314066,1314067 -n -X -o State` (765 COMPLETED + 10 FAILED = 775).

| Job | District | Total | Done (C+F) | Running | Failed |
|---|---|---:|---:|---:|---:|
| `1314028` | Madrid | 64 | 64 (56C+8F) | 0 | 8 |
| `1314065` | Lyon | 33 | 33 (32C+1F) | 0 | 1 |
| `1314066` | London | 539 | 539 (539C+0F) | 0 | 0 |
| `1314067` | Bologna | 139 | 139 (138C+1F) | 0 | 1 |

**T06b (harvest) is now unblocked per `IMP_PROMPT.md` §3 step 6.** This monitoring session has not
started it — T06 execution/dispatch is a director decision, not this loop's job. The 10 `FAILED`
tasks are the pre-existing EnergyPlus sizing-error signature (checked while triaging FINDING 268,
§8 below) — none are new, none block T06b. This is the last scheduled action of the standing
monitoring loop; no further autonomous wakeups will be scheduled unless asked.

Superseded (previous still-running status, kept for the record): only `1314065_11` (Lyon) was still
running — elapsed 6:42:38 at last check, confirmed alive via
`sstat -a -j 1314065_11 -o JobID,AveCPU,MaxRSS` (`AveCPU` 06:40:39 tracking `Elapsed` at ~99%, a long
EnergyPlus phase, not stalled). **Bologna (`1314067`) was never touched or cancelled at any point.**

GSSCanada (`gsscanada-f9`, §6 of `IMP_PROMPT.md`): obligation (1) (CP-2 measured counts) already sent
— `messages_GSSCanada/2026-09-08_OpenUBEM_to_4J_CP2_populations_freeze.md`. Obligation (2) (post-T07
freeze/announce, with commit sha + CRLF sha256) is **not yet due** — nothing to send until T07 installs
the side-cars. No peer action needed right now.

Progress board (update in place, ~30 min cadence, measured `sacct`/`sstat` only, never estimates):
`https://claude.ai/code/artifact/36496f5e-b4ce-4945-94d6-11b1997cd3cd`.

## 7. GSSCanada peer message received 2026-09-08 ~22:15 EDT — owner decision needed

- Session `gsscanada-de` (4J) messaged this session directly (peer-to-peer, not via file) reporting
  their London Step 10 no-core campaign is fully blocked: 12 of 706 payloads carry
  `geometry_outcome=DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`, their preflight (R5) rejects
  any partial population, so they get 0 cells instead of 685 buildings.
- Matches `FINDING 263` (known non-determinism in the interzone-reroute path) — not new breakage.
- Per standing protocol (`IMP_PROMPT.md` §6, owner instruction 2026-09-08 ~12:45 EDT), this session did
  **not** reply via `SendMessage` — wrote the acknowledgement as a dated file instead:
  `messages_GSSCanada/2026-09-08_OpenUBEM_to_4J_interzone_reroute_12_payloads.md`.
- No re-emission or code change was made. This is a scope decision for the owner: either dispatch a
  short fix plan to re-emit those 12 payloads without the reroute, or tell 4J to take their fallback
  (re-pre-register the 12 as excluded, costs them 6 buildings, no action needed from us).
- Not blocking T06a or this monitoring loop.

## 8. GSSCanada peer message received 2026-09-08 ~23:20 EDT — new bug, owner decision needed (urgent)

- Session `gsscanada-de` (4J) reported a real, unfixed bug in our own no-core dwelling-layout
  emitter: zone names don't advance the storey index for buildings with one dwelling per floor, so
  multiple geometrically distinct flats share one zone name. Registered as `FINDING 268` ([OPEN],
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`). 233 of 1,100 Madrid buildings (21.2%) and
  35 of 1,036 Bologna buildings (3.4%) affected — **268 buildings, 3 of their Step 10 runs stopped**.
  They will not work around it on their side; it needs an emitter fix on ours.
- T06a (this monitoring loop) is confirmed unaffected — checked all 10 current `FAILED` tasks'
  `eplusout.err`, none show this signature, all are the pre-existing sizing-error signature. No
  change made to T06a or any code as a result of this.
- Full detail and the acknowledgement sent (as a dated file, not a live message, per standing
  protocol): `messages_GSSCanada/2026-09-08_4J_to_OpenUBEM_zone_naming_collision.md`.
- Owner decision needed: dispatch a short fix plan for the zone-name template in
  `openubem/geometry/european_residential.py` / `european_nocore.py` (storey index must advance),
  or tell 4J explicitly it's deferred. Combined with the still-open 12-payload London reroute issue
  (§7), GSSCanada now has two separate blockers on our side.
