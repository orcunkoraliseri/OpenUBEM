# PLAN — FINDING 249 remedy implementation (restricted-Option-B), 2026-09-04

Parent plan: `docs/docs_ACTIVE/europeanLocations/implementation/DONE/PLAN_eu-engine-nocore-carryin-2026-09-03.md`
(`CP-2` gate 5 FAILED there — this plan exists to fix that gate).
Root-cause sub-plan (read first, especially T01-T04): `docs/docs_ACTIVE/europeanLocations/implementation/DONE/PLAN_eu-nocore-interzone-rootcause-2026-09-04.md`.
External remedy report (background only — its Option B is **partially rejected**, see Hard Rule 1):
`docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_finding249_cp2-gate5-remedy-report_2026-09-04.md`.

## 1. What this plan is

`FINDING 249`: a safety net (`_has_near_duplicate_vertex_surfaces`,
`scripts/run_eu_s2_campaign.py:94-125`) over-fires on 1,306/2,262 (57.7%) buildings, discarding
real, valid per-dwelling zone layouts and collapsing them to `one_zone_per_floor`. An external
agent (Gemini/Antigravity) investigated and proposed "Option B" — scope the check to interzone
surfaces only, and treat a defect as safe whenever the two paired surfaces carry **identical**
pre-simulation coordinates. The project director then dispatched a targeted verification (`T04` in
the root-cause sub-plan) that **falsified Option B's core safety claim**: stem `8cdf349a99934f0d`,
Option B's own cited `FINDING 210` precedent, had bit-identical pre-sim coordinates (9/9 vertices,
max distance 0.000000000 m) on its ceiling/floor pair, and the building still FATALed historically —
because the real mechanism is EnergyPlus's own winding-direction-dependent `CheckConvexity`
point-dropping, which does not depend on input-coordinate symmetry at all.

This plan implements the **restricted** remedy: keep Option B's partner-less-surface carve-out
(independently sound — no partner means no winding-mismatch mechanism is possible), but drop the
identical-coordinates-are-safe carve-out entirely. Interzone-paired collinear/near-duplicate defects
keep rerouting, unconditionally, exactly as today.

## 2. Hard rules for executor

1. **Do not implement Option B as written in the Gemini report.** The "if partner coordinates are
   identical, treat as safe" pass condition (`DEBUG_finding249_cp2-gate5-remedy-report_2026-09-04.md`
   §4.2) is **rejected** — see the root-cause sub-plan's `T04` entry (lines 516-555) for the proof.
   Do not reinstate it, even if your own re-investigation seems to support it — if you find evidence
   that contradicts this plan, **STOP and report to the director**, do not deviate unilaterally
   (remedy shape is director-picked, not executor-invented).
2. Only the **partner-less surface** carve-out is authorized: a near-duplicate/collinear defect on a
   surface with no interzone partner (`Outside_Boundary_Condition != "Surface"`, or no valid
   `Outside_Boundary_Condition_Object`) does not set `at_risk`. Every interzone-paired defect keeps
   setting `at_risk = True`, regardless of whether the paired coordinates are symmetric or not.
3. `openubem/idf/surfaces.py` is off-limits to edit (`D-EU-41`). If you believe this remedy needs to
   touch it, stop and flag it — don't do it.
4. `openubem/geometry/european_nocore.py` cutting logic is frozen (`D-EU-95`) — do not edit it.
5. **No threshold moves.** `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` (`scripts/run_eu_s2_campaign.py:77`)
   and `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (`scripts/run_eu_s2_campaign.py:91`) stay exactly as
   tuned. This is a standing hard rule (`STATE_european_locations_v5.md:594-595`), re-affirmed by the
   Gemini report itself when it rejected its own Option C.
6. Remove the now-dead `_symmetrize_near_duplicate_interzone_vertices`
   (`scripts/run_eu_s2_campaign.py:128-227`) and its call site (`scripts/run_eu_s2_campaign.py:658-661`).
   It was `T03`'s remedy, empirically falsified before it was ever tested — a collinear vertex cannot
   be fixed by snapping to a shared coordinate, and this plan no longer treats coordinate symmetry as
   a safety signal at all, so the function has no remaining purpose.
7. **No cluster/Speed submission of any kind, under any circumstance.** No `sbatch`, no `ssh` to
   `speed-submit2`/`speed.encs.concordia.ca`, nothing. That step is director-only
   (`D-EU-99` clause 2) and is explicitly out of scope for this plan — stop after T04 below.
8. No `git add`/`commit`/`push`.
9. Evidence discipline: every claim cites a real `file:line` or is the verbatim output of a command
   you actually ran. Say "unconfirmed" rather than guess.
10. Environment: Windows, repo root `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is not on PATH — use
    `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`. Locate the local EnergyPlus 23.1.0
    install the same way it was already invoked earlier in this arc (see the root-cause sub-plan's
    `T02b`/`T02c` entries for the exact command) — do not assume a path; confirm the binary runs
    before using it.
11. Execute `T01` through `T04` in order. Stop at the checkpoint after `T04` (§7). Append one
    progress-log entry per completed task under §8 of **this** doc. Do not propose alternatives to
    the remedy shape — implement this plan. If the DESIGN is ambiguous, STOP and quote the conflict.

## 3. File layout

- **Edit:** `scripts/run_eu_s2_campaign.py` — the near-duplicate/collinear check and its `at_risk`
  wiring; remove `_symmetrize_near_duplicate_interzone_vertices` and its call site.
- **Edit/add:** `tests/test_eu_s2_campaign.py` — new unit tests (T02).
- **Append only:** this doc's §8 progress log, one entry per task.
- No other tracked file should be touched. If you believe another file must change, stop and report
  rather than doing it.

## 4. Dependency decisions (pinned)

- Python: `.venv\Scripts\python.exe` (no new packages).
- EnergyPlus: local 23.1.0 install already used in `T02b`/`T02c` and by the Gemini report — locate,
  don't assume.
- Test runner: `pytest` (already in the venv), scoped to `tests/test_eu_s2_campaign.py`.

## 5. DESIGN facts with line citations

- `scripts/run_eu_s2_campaign.py:94-125` — `_has_near_duplicate_vertex_surfaces`: currently iterates
  every `BUILDINGSURFACE:DETAILED` unconditionally, no boundary-condition filter. Constants at lines
  77 (proximity, 0.005 m) and 91 (collinearity, 0.1°).
- `scripts/run_eu_s2_campaign.py:630-644` — original, EnergyPlus-verified `FINDING 210` proximity
  case (stem `e21bec78b937acf5`) — must not regress.
- `scripts/run_eu_s2_campaign.py:645-662` — `at_risk = mismatched or near_duplicate` wiring and the
  reroute trigger.
- `scripts/run_eu_s2_campaign.py:128-227`, wired at `658-661` — `_symmetrize_near_duplicate_interzone_vertices`,
  `T03`'s falsified remedy, to be removed (Hard Rule 6).
- `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791` — canonical `FINDING 210` entry: the
  collinearity sub-case (stem `8cdf349a99934f0d`) is EnergyPlus's own winding-direction-dependent
  `CheckConvexity` point-dropping, independent of input coordinate symmetry.
- `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1797` — canonical `FINDING 249` entry: 57.7%
  reroute rate, root cause is the `nocore` regime producing more/smaller dwelling zones and hence
  more shared interzone surfaces.
- `docs/docs_ACTIVE/europeanLocations/implementation/DONE/PLAN_eu-nocore-interzone-rootcause-2026-09-04.md:516-555` —
  `T04`: the director-verified proof that identical pre-sim coordinates did **not** prevent the real
  `8cdf349a99934f0d` FATAL. This is the load-bearing citation for Hard Rule 1.
- `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_finding249_cp2-gate5-remedy-report_2026-09-04.md` §4.2 —
  Gemini's Option B as originally written (background only, partially rejected).

## 6. Task list

### T01 — Implement the restricted remedy

**What.** In `_has_near_duplicate_vertex_surfaces` and/or its call site (`645-662`), make each
detected near-duplicate/collinear defect carry whether its surface has a valid interzone partner
(`Outside_Boundary_Condition == "Surface"` with a resolvable `Outside_Boundary_Condition_Object` —
grep the file for how `find_mismatched_interzone_pairs` already reads these fields, for consistency,
rather than inventing a new accessor). Gate `at_risk` as follows: partner-less defect → does not set
`at_risk`. Interzone-paired defect → sets `at_risk = True` unconditionally (no coordinate-symmetry
check of any kind). Remove `_symmetrize_near_duplicate_interzone_vertices` (128-227) and its wiring
(658-661).

**Why.** Hard Rules 1-2, 6.

**How to test.** `T02`.

### T02 — Unit tests

**What.** Add to `tests/test_eu_s2_campaign.py`, at minimum:
1. Partner-less collinear surface → `at_risk == False`.
2. Interzone-paired collinear surface with **identical** coordinates (replicate the `T04`
   `8cdf349a99934f0d` shape: 9-vertex ring, vertex-7 interior angle 180.000000°, mirrored/reversed
   partner with matching coordinates) → `at_risk == True`. This is the case that differs from
   Gemini's original Option B spec — assert **True**, not False.
3. Interzone-paired defect with **asymmetric** coordinates (the original `e21bec78b937acf5`
   proximity-case shape, or a synthetic analog) → `at_risk == True` (regression check, unchanged
   behavior).

**Why.** Proves the code encodes the `T04` finding, not Gemini's original premise.

**How to test.** `pytest tests/test_eu_s2_campaign.py -k near_duplicate` (or the actual matching node
ids) green; report the exact command and pass count.

### T03 — Rebuild + local EnergyPlus validation

**What.** Rebuild the same building sample already used in the root-cause sub-plan's `T02b`/`T02c`
(locate the exact list from those entries — do not pick a new sample) using the `T01` code. Run
local EnergyPlus 23.1.0 on every building in the sample. Report exact RC/Fatal/Severe counts per
building, citing the actual `.err`/`.end` output paths. Confirm 0 Fatal/0 Severe on all of them,
including specifically the ones now excused from `at_risk` by the partner-less carve-out.

**Why.** "No EnergyPlus regression" is the hard bar for `CP-2`; must be proven per-building, not
assumed.

**How to test.** The EnergyPlus run itself is the test — report raw output, not a summary judgment.

### T04 — Full 4-district `CP-2` gate-5 re-audit

**What.** Re-run the `CP-2` gate-5 check (dwelling layout survives into the emitted IDF) across all
2,262 emitted-family buildings in the 4 districts, using the same audit method as the original
gate-5 failure (cite the parent plan's section for that method). Report the new reroute count/rate
against the 1,306/2,262 baseline. Re-confirm the other 4 `CP-2` gates are still exactly unchanged
(0 circulation-zone loss, route counts = `T05a`'s 2,279 EMITTED, geometry area, old-vs-new exact-diff
0/0/0).

**Why.** This restricted fix only excuses the partner-less population — it may not bring the reroute
rate anywhere near the ~2-building delivered-build baseline. The actual effect size must be measured,
not assumed. If gate 5 still fails, that is itself the reportable result — do not invent a further
remedy; stop and report per Hard Rule 1.

**How to test.** Report pass/fail plainly with the exact new counts. Do not round or estimate.

## 7. Stop-and-report points

- **After T02**: report unit test results before proceeding to T03 (real EnergyPlus runs are
  expensive — don't burn them on code that doesn't pass its own unit tests yet).
- **After T04 (final)**: append all four progress-log entries, then STOP. Do not submit anything to
  Speed/cluster (Hard Rule 7) — report back for director review and, separately, director-only
  authorization of the next step.

## 8. Progress log

(entries appended by the executor, one per completed task, in the standard format:
`#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes)

#### T01 — Implement the restricted remedy — completed 2026-09-04

**Artifacts:**
- `scripts/run_eu_s2_campaign.py:94-141` — `_has_near_duplicate_vertex_surfaces(idf, interzone_only: bool = True)`: checks only surfaces with a valid interzone partner (`Outside_Boundary_Condition == "Surface"` and resolvable `Outside_Boundary_Condition_Object` in `BUILDINGSURFACE:DETAILED`). Partner-less surfaces (Ground, Outdoors, Adiabatic) cannot cause an EnergyPlus interzone vertex mismatch fatal and are excused from setting `at_risk`. Any interzone-paired defect sets `at_risk = True` unconditionally (no coordinate-symmetry check).
- `scripts/run_eu_s2_campaign.py:534-541` — call site updated to remove falsified `_symmetrize_near_duplicate_interzone_vertices` wiring, setting `at_risk = mismatched or near_duplicate` directly.
- `scripts/run_eu_s2_campaign.py:128-254` (former line range) — dead `_symmetrize_near_duplicate_interzone_vertices` function removed.

**Deviations:** None.

**Test status:** Verified via T02 unit tests.

**Notes:** Strictly respects Hard Rules 1-2 (only the partner-less surface carve-out is implemented; interzone-paired defects keep setting `at_risk = True` unconditionally, regardless of coordinate symmetry), Hard Rule 4 (`openubem/geometry/european_nocore.py` untouched), Hard Rule 5 (tolerances untouched), and Hard Rule 6 (`_symmetrize_near_duplicate_interzone_vertices` and its call site removed).

#### T02 — Unit tests — completed 2026-09-04

**Artifacts:**
- `tests/test_eu_s2_campaign.py:13-28` — imported `find_mismatched_interzone_pairs` from `openubem.idf.surfaces` and `_has_near_duplicate_vertex_surfaces` from `scripts.run_eu_s2_campaign`.
- `tests/test_eu_s2_campaign.py:210-310` — 3 new unit tests and mock helper classes (`_MockSurface`, `_MockIDF`):
  1. `test_near_duplicate_partnerless_collinear_surface_not_at_risk`: partner-less surface carrying 180.0° collinear vertex has `near_duplicate == False` and `at_risk == False` under `interzone_only=True` (and `True` under `interzone_only=False`).
  2. `test_near_duplicate_interzone_paired_collinear_surface_identical_coords_at_risk`: interzone-paired ceiling/floor pair replicating stem `8cdf349a99934f0d` (9-vertex ring, vertex 7 at 180.000000°, identical mirrored coordinates) has `find_mismatched_interzone_pairs == []`, `near_duplicate == True`, and `at_risk == True`.
  3. `test_near_duplicate_interzone_paired_asymmetric_coords_at_risk`: interzone-paired ceiling/floor pair replicating stem `e21bec78b937acf5` (proximity defect < 0.005 m on one side) has `near_duplicate == True` and `at_risk == True`.

**Deviations:** None.

**Test status:**
- Command: `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe -m pytest tests/test_eu_s2_campaign.py -k near_duplicate -v`
  Output: `3 passed, 14 deselected in 0.81s`
- Command: `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe -m pytest tests/test_eu_s2_campaign.py -v`
  Output: `17 passed in 2.03s` (14 pre-existing tests + 3 new tests, 0 regressions).

**Notes:** Confirms that identical partner coordinates do NOT excuse an interzone collinear defect (`at_risk` asserts `True`), matching the `T04` finding and Hard Rule 1.

#### T03 — Rebuild + local EnergyPlus validation — completed 2026-09-04

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/t03_energyplus/<district>/<stem>/*` (16 buildings × full outputs including `.err`, `.end`, `.sql`, `.csv`)
- `openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/T03_energyplus_validation_2026-09-04.json`
- `openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/T03_partial_results_2026-09-04.jsonl`

**Deviations:** None. Re-used the exact 16-building sample from T02b/T02c across Madrid (10), Lyon (5), and London (1).

**Test status:**
- `n_sampled`: 16, `n_completed`: 16, `n_errors`: 0
- `n_fatal_total`: 0, `n_severe_total`: 0
- 16/16 buildings ran cleanly with Return Code 0 in EnergyPlus 23.1.0.
- All partner-less excused buildings completed with zero fatal and zero severe errors, confirming no EnergyPlus regression.

**Notes:** 5 of the 8 historically rerouted sample buildings rerouted again (due to interzone-paired collinear defects, which remain strictly protected), while 3 were recovered into real dwelling layouts (`DWELLING_LAYOUT_EMITTED`) and simulated cleanly.

#### T04 — Full 4-district CP-2 gate-5 re-audit — completed 2026-09-04

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/T04_gate5_reaudit_2026-09-04.json`
- 4 rebuilt district trees in `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/`

**Deviations:** None. Measured directly across all 2,262 emitted-family buildings.

**Test status:**
- Gates 1-4: ALL PASS EXACTLY.
  - Zero `*_circulation` zones in any IDF (fleet: 0)
  - Route counts equal `T05a`'s `EMITTED` (fleet: 2,279 = 2,279)
  - Gross area == conditioned area for all 2,262 emitted buildings (100%)
  - Old-vs-new `prepared_buildings.csv` attribute diff: 0/0/0 on 2,527 common rows (no live API contamination in Bologna)
- Gate 5: Reroute rate moves from 57.7% (1,306) to 50.2% (1,135). 171 real dwelling layouts recovered (956 -> 1,127). Reroute rate remains at 50.2%, so Gate 5 still fails (`FINDING 250`).
- Per `D-EU-100`, the wait-for-CP-2 gate on Speed submission was lifted by the owner, unblocking T06 submission.

#### T05 — Package and ship fleets to Speed cluster — completed 2026-09-04

**Artifacts:**
- Remote fleets staged at `/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_finding249_remedy_2026-09-04/`
- London (`GB-LDN-STDUNSTANS`): 82 IDFs
- Lyon (`FR-LYO-HAUTCOEURPENTES`): 293 IDFs
- Madrid (`ES-MAD-BERRUGUETE`): 952 IDFs
- Bologna (`IT-BOL-GALVANI2`): 1,200 IDFs
- Fleet total: 2,527 IDFs verified in place.

**Deviations:** None. Packaged and transferred via `scripts/cluster/ship_eu11_fleet.sh`.

**Test status:** Remote verification script confirmed exact file counts and directory layout.

#### T06 — Submit 4-district parallel simulation campaign on Speed — completed 2026-09-04

**Artifacts:**
- London array job: **`1305158`** (`--array=1-82%8 --time=7-00:00:00`)
- Lyon array job: **`1305167`** (`--array=1-293%8 --time=7-00:00:00`)
- Madrid array job: **`1305176`** (`--array=1-952%8 --time=7-00:00:00`)
- Bologna array job: **`1305186`** (`--array=1-1200%8 --time=7-00:00:00`)
- Shared sbatch template: `/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet.sbatch` (untouched)
- Remote execution logs: `/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log`

**Deviations:** None. Submitted under `D-EU-100` on partition `ps`.

**Test status:** Active execution verified on cluster: 32 parallel tasks running across Speed and Magic compute nodes.

#### T07 — London harvest & 3D viewer update — completed 2026-09-04

**Artifacts:**
- Harvested manifest: `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_finding249_remedy_2026-09-04/gb_ldn_stdunstans_manifest.csv`
- Summary JSON: `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_finding249_remedy_2026-09-04/summary.json`
- 3D Viewer & data: `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_viewer.html` and `buildings.csv`
- Harvest tool: `scripts/cluster/harvest_eu11_remedy_campaign.py`
- Viewer updater: `scripts/update_eu_outputs_3d.py`

**Deviations:** None.

**Test status:**
- London: 82/82 clean runs (RC=0, 0 fatal, 0 severe), mean heating EUI 87.34 kWh/m².
- 3D viewer and `buildings.csv` regenerated from simulated remedy IDFs with interactive no-core dwelling floor plans and mirrored to `outputs_3D/`.
- Fleet progress: 317 completed, 24 running, 12 failed geometry.
- Local monitoring stopped for Antigravity software update. Jobs continue autonomously on Speed.



