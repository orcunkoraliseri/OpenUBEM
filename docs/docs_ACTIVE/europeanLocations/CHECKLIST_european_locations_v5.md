# European locations × Step 8 — progress checklist (v5)

🔴 **CLOSED 2026-09-09.** Closed, reopened the same day for `T06b`, `T07`, `T08` of
`implementation/PLAN_eu-recut-95pct-2026-09-08.md`, then closed again once all three landed. Read-only:
not executed, not appended to, not deleted. Statuses below were refreshed at `T08`. Current truth: the
block at the head of [`STATE_european_locations_v5.md`](STATE_european_locations_v5.md).

---

<!-- superseded closure note, kept: -->
🔴 **CLOSED 2026-09-09 — owner ruling ("we have completed this project"). Read-only: not executed,
not appended to, not deleted.** Every status below is frozen as it stood on 2026-09-08; the rows still
marked 🟡 *in execution* (`D-EU-107`, `D-EU-108`, `D-EU-109`) and ⬜ *not started* (`EU-19`, engine
carry-in) stopped there and were never completed. What actually landed, and what was left open, is the
closure block at the head of [`STATE_european_locations_v5.md`](STATE_european_locations_v5.md).

---

Tracking view only — no rulings, no findings, no numbers, no notes. Those live in
[`STATE_european_locations_v5.md`](STATE_european_locations_v5.md) and in each plan's own §8 progress log.
Updated by the director after each dispatch audit, never by an executor.

---

## Work packages

| WP | What | Status |
|---|---|---|
| `EU-01`…`EU-12` | TABULA loader → results/dossier → district campaign → viewer | ✅ |
| `EU-13`/`EU-14`/`EU-13B`/`EU-14B` | Layout coverage, construction year, ruled grid, layout binding | ✅ |
| `EU-15` | Ruled thermal zoning to the ≥ 95 % bar | ✅ — bar not met |
| `EU-16` | Context geometry + 4-district resimulation | 🟥 Stopped |
| `EU-17`/`EU-17a`/`EU-17b` | Relax the box rule in the engine; fallback tier | ✅ — coverage still below bar |
| `EU-18a`/`EU-18b` | `plans3D/` pages + parity gate | ✅ — pages exist, gate fails |
| `EU-18c` | Non-box EnergyPlus sample battery | 🔴 Blocked — owner's sentence |
| `EU-19` | Four-district resimulation on proven plans | ⬜ Not started |
| `EU-20` | Morphology atlas — eleven groups | ✅ |
| **`EU-21`** | **Flat-division rules, graded on 550 real plates** | 🟡 **The live front** |
| engine carry-in | The written rule replaces the box-era logic | ⬜ Identified, not ordered |
| `D-EU-106` | Repaint `outputs_3D` floor-plan modal in the `plans3D` style | ✅ |
| `D-EU-107` | Balance the dwelling cut (`C12`), re-plan/re-simulate affected plates only | 🟡 In execution — `CP-3` hash half unsigned |
| `D-EU-108` | London coverage recovery (terrace-row age/storey inheritance) | 🟡 In execution — complete through T05b |
| `D-EU-109` | Recover discarded dwelling divisions; merges `D-EU-107`/`108`/`109` into one re-emission + Speed campaign | 🟡 In execution — merged re-emission running |

---

## `EU-21` plan ledger

- [x] `eu20-morphology-atlas-2026-09-01`
- [x] `eu21-group-schemes-2026-09-01` — P06–P08 never run, superseded
- [x] `eu21-rules-tests-2026-09-01`
- [x] `eu21-cap12-2026-09-01`
- [x] `eu21-direct-cutters-2026-09-01`
- [x] `eu21-t07-2026-09-02`
- [x] `eu21-global-rules-2026-09-02`
- [x] `eu21-checks-c8c4-2026-09-02`
- [x] `eu21-test01-clean-2026-09-02` — CLOSED, superseded
- [ ] `eu21-cutter-2026-09-02` — 🟥 **PARKED.** Files intact; only the owner may restart it.
- [x] `eu21-nocore-2026-09-02` — CLOSED
- [x] `eu21-compactness-2026-09-03` — ✅ **COMPLETE** (`CP-3`)
- [x] `eu21-district-viewer-2026-09-03` — ✅ **COMPLETE** (`CP-3`, plus the `_r2` archive pass)
- [x] `eu21-colour-repair-2026-09-03` — ✅ **COMPLETE** (`CP-4`) — PASS 2,012 → 2,178 → 2,353 (79.1 % → 85.6 % → 92.5 %), refused 23 → 15, 0 regressions at either step
- [ ] `eu-engine-nocore-carryin-2026-09-03` — ▶ **IN FLIGHT** (`D-EU-95`) — extract the proven cutter into `openubem/geometry/european_nocore.py`, prove bit-parity with `_r5` on all 2,544 plates, seam it into the engine, rebuild the four districts' IDFs, then the Speed campaign. ✅ **`CP-1` SIGNED** — 2,529 plates compared, **0/0/0/0 mismatches** · `CP-2` IDF audit still to come
- [x] `eu-nocore-finding249-remedy-2026-09-04` — ✅ **COMPLETE** — restricted Option B (partner-less near-duplicate-vertex carve-out only). T01/T02 done, 17/17 unit tests green. T03 (16-building real-EnergyPlus regression) completed 16/16 clean, 0 fatal / 0 severe. T04 measured by the director: 🔴 **`FINDING 250`** — reroute **1,135/2,262 (50.2 %)**, down from 1,306/2,262 (57.7 %), 171 buildings recovered — `CP-2` gate 5 still FAILS. `D-EU-100` lifted the wait-for-`CP-2` gate on Speed submission.
- [x] `eu-nocore-full-fleet-expansion-2026-09-04` — 🟨 **T01-T03 (prep) COMPLETE, T04+ (package/ship) BLOCKED.** `D-EU-101` — owner ruled all residential building types in scope. Gap +1,659; prep recovered +363 (London +307, Madrid +56, Lyon/Bologna +0, expected). `FINDING 253`. Packaging/Speed submission still waits on the live 2,527-task campaign (`eu-nocore-finding249-remedy-2026-09-04`, T06) draining — far from done as of 2026-09-04 evening.

---

## `eu-engine-nocore-carryin` tasks

- [x] T01 — cutter extracted to `openubem/geometry/european_nocore.py` (1,731 lines)
- [x] T02 — parity harness `scripts/eu21/09_engine_parity.py`; first run failed 1/0/53/51 on a harness input defect, corrected, re-run clean — ✅ **`CP-1` SIGNED**, 2,529 compared, 0/0/0/0, `input_missing` 0
- [x] T03 — the engine seam: `generate_european_nocore_storey_layout` + `EUROPEAN_LAYOUT_REGIME = "nocore"`; zone-spec writer untouched; corridor path parked, not deleted
- [x] T04 — regression sweep: **6 failed / 613 passed**, identical to the pinned pre-seam baseline; the six new failures were all class (a) and pinned to `"ruled"`, no assertion loosened
- [x] T05a — the engine's own building-level census (`FINDING 246`) — 2,544 rows, fleet `EMITTED` 2,279 (89.6 %) · `FALLBACK` 240 · `REFUSED_K_GT_12` 25, against `_r5`'s 2,353 `PASS` (92.5 %); the 74 that changed side all moved one way, none the other
- [x] T05 — four districts rebuilt, audited — 🔴 **`CP-2` FAILED, not signed** (`FINDING 249`). Four gates pass exactly: zero `*_circulation` zones, route counts = `T05a`'s 2,279 `EMITTED`, conditioned = gross on all 2,262, old-vs-new attribute diff 0/0/0. The fifth fails: the `FINDING 210` reroute fires on **1,306** buildings (delivered build: 2) and discards the dwelling layout, so real layouts fall **1,446 → 956**
- [x] T06 — the Speed campaign, director only — ▶ **IN FLIGHT ON SPEED** (`D-EU-100`, partition `ps`, `--time=7-00:00:00`, throttle `%8`): London (`1305158`) **100% completed & harvested** (82/82 RC=0, mean EUI 87.34 kWh/m², `outputs_3D` updated); Lyon (`1305167`, 103 done), Madrid (`1305176`, 65 done), Bologna (`1305186`, 67 done) running autonomously. Fleet: 317 completed, 24 running, 12 failed.
- [ ] T05-fix — root-cause the `intersect_match` reroute at no-core subdivision density; recover the 17 `IDF_ASSEMBLY_FAILED_RuntimeError` buildings — **owner's call, not started**

---

## `eu21-compactness` tasks

- [x] T01 — baseline frozen, census reproduced
- [x] T02 — `C11` implemented and printed
- [x] T03 — `C11` scored, no regressions
- [x] T04 — grid-first, both bearings — `CP-1` audited
- [x] T05 — proportion ladder calibrated — **`CP-2` reached, director ruling taken**
- [x] T05b — the three failing group rules fixed, ladder re-run
- [x] T05c — `C10` rebuilt as a real pinch test, cutter made to satisfy it — `FAIL 0` unreachable, `FINDING 242`
- [x] T05d — ring/wing residual + the `MultiPolygon` fault (`FINDING 243`), ladder re-run, rung set per `D-EU-89`
- [x] T06 — rebuild the five sheets under the new build tag
- [x] T07 — re-date the rules documents, archive, sweep citations, update prompt + `STATE` — **`CP-3`**

---

## `eu21-district-viewer` tasks

- [x] T01 — every Madrid census building cut, evidence JSON
- [x] T02 — Madrid page: 3D viewer, click → TEST-sheet card
- [x] T03 — Lyon, London, Bologna — audited: 2,504 / 2,544 drawn, 2,074 PASS
- [x] T04 — pop-up = EU-11 modal (`D-EU-89`), four pages rebuilt `_r2` — **`CP-2`**
- [x] T05 — generic fallback rolled out fleet-wide (1,641 uncatalogued buildings, dark green `rgb(24, 94, 46)`, 0 massings remaining), baseline non-r2 files archived to `plans3D/archive/` (`D-EU-90`) — **`CP-3` COMPLETE**
- [x] T05 (the §5 one) — `_r3` rebuild on the closed compactness cutter, audited accepted (`error` 0 × 4)
- [x] archive pass — `_r2` pages moved to `plans3D/archive/`, `index.html` repointed to `_r3`, citations swept

---

## `eu21-colour-repair` tasks

- [x] T01 — bench harness reproduces the `_r3` failing set exactly — **`CP-1` audited**
- [x] T02 — broaden the angle search in `build_flats`
- [x] T03 — reflex-vertex boundary snapping
- [x] T04 — courtyard ring bisection at low `k` — **`CP-2` audited**, 160 of 509 recovered, control set clean
- [x] T05 — orange: cut attempted at the declared `k`, judged by the same seven checks (`D-EU-92`) — 8 of 23 pass
- [x] T05b — `C11` residual measured; strip bound falsified and withdrawn, `k = 1` argument stands — **`CP-2b`** (`FINDING 245`)
- [x] T06 — four districts rebuilt as `_r4`, no-regression gate **0 of 2,012** — **`CP-3` COMPLETE**
- [x] T07 — `D-EU-93` carried into the cutter (`C11` not evaluated at `len(live) <= 1`), four districts rebuilt as `_r5` — ✅ **`CP-4` COMPLETE** — PASS 2,178 → 2,353 (85.6 % → 92.5 %), 0 regressions, **Madrid 95.3 % — bar crossed**

## `eu-nocore-full-fleet-expansion` tasks

🟦 **PLAN WRITTEN** — `PLAN_eu-nocore-full-fleet-expansion-2026-09-04.md`. `D-EU-101`, gap +1,659 buildings
(London +1,160, Lyon +237, Madrid +242, Bologna +20). Starts after `eu-nocore-finding249-remedy-2026-09-04`
T06 (current 2,527-task Speed campaign) drains for submission — but T01-T03 (prep) can run now, in parallel,
against the live campaign's own separate output folders (`*_full_fleet_2026-09-04/`, never the live
`*_finding249_remedy_2026-09-04/` folders). Dispatched to an external executor (Gemini Antigravity),
`prompts/EXECUTOR_PROMPT_full-fleet-expansion-2026-09-04.md`.

✅ **T01-T03 done, director-audited 2026-09-04** (see results inline below). 🔴 **`FINDING 253`**: numbers
verified directly against each district's `summary.json` on disk, not just quoted from the executor's report —
all four matched exactly, no discrepancy.

🔴 **`FINDING 252`**: the T01-T06 breakdown below (superseded) assumed the gap population needs a row in
`EU-20/morphology_census.csv` before anything else, and that the no-core cutter is a step separate from IDF
generation. Both wrong — `morphology_census.csv` belongs only to the EU-20/EU-21 rule-grading pipeline (the
550-plate, 95 %-bar document), never read by the production IDF writer
(`scripts/run_eu_s2_district_campaign.py::prepare`, verified by direct read 2026-09-04). `prepare()` reads the
raw manifest directly, classifies inline (`_gb_rows`/`_it_rows`/`_mapped_rows`), and calls the already-carried-
in no-core engine in the same pass (`_geometry()` line 112) — cutting and IDF-writing are one step. Corrected
tasks (see the plan doc for full detail):

- [x] T01 — extend GB's `FINDING 251` fix to ES — **done, verified by direct diff read 2026-09-04**: exactly
      the two named edits landed, nothing else (`git diff --stat` = 2 files, 12 insertions/3 deletions).
      `map_observed_building_to_tabula` line 225 widened to `("FR", "ES")`; `_mapped_rows`'s ES branch
      (`run_eu_s2_district_campaign.py:337-338`) now assigns `is_attached` via `compute_footprint_adjacency`.
- [x] T02 — re-run `prepare()` for all four districts — **done, all exit 0**. Output folders confirmed present
      under `*_full_fleet_2026-09-04/` only; live `*_finding249_remedy_2026-09-04/` folders untouched.
- [x] T03 — audit each district's `summary.json` — **done, verbatim, director-verified against the files on
      disk (not just the executor's report)**: London 82→389 (+307), Lyon 293→293 (+0), Madrid 952→1,008
      (+56), Bologna 1,200→1,200 (+0). Total 2,527→2,890 (+363). Lyon/Bologna didn't move, as predicted —
      genuine data gaps. **Stop point reached** — no packaging/Speed submission yet (`FINDING 253`).
- Carried, unchanged, blocked on T03's outcome and an owner call on the remaining structural gaps (GB 445
  no-EPC-match / 355 period-straddle / 47 missing-storeys; Madrid's non-code-fixable remainder): package +
  ship the full expanded fleet to Speed, submit, harvest, update `outputs_3D` — director's job, cluster-
  restricted, not this plan's scope.
- [x] Root-cause the residual 1,296-building gap — **done 2026-09-04, 🔴 `FINDING 254`**: no new code-fixable
      bug found. `IDF_ASSEMBLY_FAILED_RuntimeError` (17) and `MISSING_OBSERVED_STOREY_COUNT` (Madrid 163,
      London 47) are genuine data gaps; London `PERIOD_STRADDLE_*`/`MISSING_OBSERVED_EPC_AGE_BAND` (355/445)
      are documented fail-closed design, not bugs. Lyon's `TYPOLOGY_SIGNALS_DISAGREE` (186, of which 176 look
      recoverable) resolves to the pre-existing unruled `D-EU-37` — not a new decision.
- [x] `D-EU-37` ruled and implemented — **done 2026-09-04, 🔴 `FINDING 255`**: owner ruled *"100% full"* /
      *"make it possible"*. New bucket added to `derive_bdtopo_building_type`
      (`openubem/semantic/european_archetype_mapping.py:199-200`); Lyon `prepare()` re-run, `population_prepared`
      293→469 (+176). Fleet now **3,066/4,186 (73.2 %)**. Remaining 1,120-building gap handed to an external
      investigation (`INVESTIGATION_full-fleet-100pct-2026-09-04.md`, run by the owner with Gemini) — still
      blocked on the live 2,527-task Speed campaign draining before the expanded fleet can package and ship.
- [x] London EPC `construction_year` recovery — **done 2026-09-04, 🔴 `FINDING 256`**, plan
      `implementation/PLAN_eu-epc-construction-year-2026-09-04.md`, T01-T05 all green, director-verified off
      disk. New sidecar `eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv` (1,336 rows / 67
      `osm_id`s, pinned assertion matched exactly) + new `_gb_age_decision` helper
      (`scripts/run_eu_s2_district_campaign.py:171`); `prepare()` untouched; 6/6 new unit tests pass, both
      fail-closed refusals included. London 389→**419**, `MISSING_OBSERVED_EPC_AGE_BAND` 445→418,
      `PERIOD_STRADDLE_K` 20→12, `MISSING_OBSERVED_STOREY_COUNT` 47→52 — every predicted number matched.
      389/389 baseline rows re-emit with identical `idf_sha256`; provenance split 24 + 6. Fleet
      **3,096/4,186 (74.0 %)**.
- [ ] Promote `GB-LDN-STDUNSTANS_full_fleet_epcyear_2026-09-04/` over `..._full_fleet_2026-09-04/` — written
      to a separate folder on purpose; promotion is a director call, deliberately not taken by the executor.
- [ ] Rule on the remaining recoverable populations (+331 max: Madrid Catastro `BuildingPart` storeys +163,
      straddle-intersection +69, 13–14 dwelling gap +38, `house`/`terrace` floor dimensions +33, ISTAT tie
      policy +12, `D-EU-58` tolerance +4, Bologna ladder for `building=residential` +6) — the only path above
      74 %, and the ceiling stops at ≈82 % even if all are granted. See
      `DEBUG_why-not-100-percent-2026-09-04.md`.

## Carried, unstarted, in the owner's order

- [x] Carry the written rules into `openubem/geometry/european_residential.py` — ✅ done, `D-EU-95`, `implementation/DONE/PLAN_eu-engine-nocore-carryin-2026-09-03.md`, bit-parity 0 mismatches on 2,529/2,529 plates.
- [x] Close the 95 % coverage gap, biggest group first — superseded: `EU-19` ran on `D-EU-100`'s lifted gate, not on a re-passed 95 % bar; see `STATE` §7 items 2–3.
- [ ] The buildings demoted at IDF-writing time — a separate defect, never a morphology failure — still open, not scheduled.
- [x] Republish `plans3D/` from the new plans, geometry only — superseded by the merged `outputs_3D/` viewers, `PLAN_eu-viewer-eui-floorplan-2026-09-07.md`.
- [x] Confirm the Speed queue is empty before `EU-19` is prepared — ✅ checked 2026-09-03: `squeue -u o_iseri` → **0 jobs**; EnergyPlus 23.1.0 present on `/speed-scratch`, 27 TB free. Re-check immediately before submitting.
- [x] `EU-19` simulate — ✅ EU-11 ceiling82 harvest closed 2026-09-06, 3,344 run / 3,321 success / 23 failed, pooled EUI by district in `STATE` §8.
- [x] EUI colour-by + EU-21 check badges on the 3D viewers — ✅ closed 2026-09-07, `PLAN_eu-viewer-eui-floorplan-2026-09-07.md`.
- [ ] Housekeeping: `scripts/eu21/04_group_tests.py` still writes archived sheet filenames
- [ ] 🔴 New, `FINDING 258`: some plates' floor-plan division is not homogeneous (tiny dwellings + one oversized one) despite `PASS ALL 7 CHECKS` — owner ruling: per-building fix only, never a full-batch re-cut/re-simulation, not scheduled.

---

## Gates that need you, specifically

Tracking view only — status and a pointer, nothing else. Full rulings, quotes and numbers are in
`STATE` §5 ("Gates that need the owner, specifically") and §4, by decision number.

| Gate | Status | Pointer |
|---|---|---|
| `plans3D/` read + confirmation | ✅ closed 2026-09-07, one named exception carried as `FINDING 258` | `D-EU-54`, `D-EU-105` |
| Simulation permission (≥ 95 % `PASS`, any one district) | ✅ met — Madrid 95.3 % | `D-EU-91`, `D-EU-94` |
| Engine carry-in blocker (core-era engine) | ✅ cleared — bit-parity 0 mismatches | `D-EU-95`, `STATE` §7 item 2 |
| `C11` not evaluated at `k = 1` | ✅ taken | `D-EU-93` |
| 95 % coverage bar | ✅ retired | `D-EU-96` |
| 107 low-density buildings | ✅ stay in, flagged | `D-EU-97`, `FINDING 248` |
| Director builds/submits Speed campaign unattended | ✅ taken, `CP-2` not waived | `D-EU-98` |
| `CP-2` engine carry-in IDF audit | 🔴 FAILED | `FINDING 249` |
| Root-cause `FINDING 249` before any campaign | ✅ taken 2026-09-04 | `D-EU-99` |
| `CP-2` re-sign-before-campaign gate | ✅ lifted 2026-09-04, owner's call | `D-EU-100` |
| Remaining recoverable buildings (+331 max) need rulings | 🔴 open | `DEBUG_why-not-100-percent-2026-09-04.md` |
| Restricted remedy re-measured — still 50.2 % reroute | 🔴 FAILED, does not block `T06` (`D-EU-100`) | `FINDING 250` |
| Restarting the parked corridor path | 🔴 owner-only | `D-EU-79` |

Everything else runs without a check-in, per your standing "continue to the end" instruction.
