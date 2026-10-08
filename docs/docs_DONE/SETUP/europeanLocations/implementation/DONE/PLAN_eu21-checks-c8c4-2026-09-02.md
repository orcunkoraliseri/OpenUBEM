# PLAN — EU-21 check repair: C8 real shared edge, C4 honest badge, re-census

- **slug** `eu21-checks-c8c4`
- **date** 2026-09-02
- **arc** European locations, group floor-planning sub-arc
- **read-first** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v4.md`
- **findings this plan repairs** `FINDING 231` (C8), `FINDING 232` (C4 badge) — both recorded in
  `implementation/PLAN_eu21-cutter-2026-09-02.md` §9
- **authorised by** the owner, 2026-09-02: *"lets go fix C8+C4 first and re-census"*
- **rules doc in force** `rules/RULES_dwelling_layout_groups_2026-09-01.html` (laws `D-EU-64` … `D-EU-76`)
- **next free ids** `D-EU-77` / `FINDING 235`

---

## 1. Hard rules for the executor

1. **Do not touch the cutter.** `scripts/eu21/05_group_cutters.py`, `01_cut_group_plans.py`,
   `02_one_core_per_plate.py`, `03_build_rules_html.py` are **read-only in this plan**. Not one line.
   The geometry the owner reviewed must come out of this plan byte-identical.
2. The only file you may edit is `scripts/eu21/04_group_tests.py`.
3. **Never re-cut.** All work runs off the geometry already stored in
   `openubem/outputs/eu_evidence/EU-21/rules_tests/test_01.json` … `test_05.json`. That is what the new
   `--recheck` mode of T04 is for. Running `04` without `--recheck` / `--render-only` (i.e. re-cutting)
   is forbidden in this plan.
4. **Never regenerate a delivered artifact.** The five sheets
   `rules/tests/TEST_0*_2026-09-01.html` are the ones the owner reviewed. They are **not** to be
   overwritten — T02 renames the build targets to `_2026-09-02` first.
5. Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`. The dirty tree
   is the owner's.
6. Never write into `EU-17/`, `EU-20/`, or `EU-21/rules_tests/baseline_2026-09-02/`.
7. **No threshold is ever loosened to lift the census.** `ACCESS_MIN_M` stays 1.00 m, the C4 overlap
   tolerance stays 0.02 m². The census is expected to fall hard; that is the point of the repair.
8. No EnergyPlus, no engine call, of any kind (`D-EU-55`).
9. No new files except the artefacts named in T02 and T04. No `.py` under `docs/`.
10. Python is `./.venv/Scripts/python.exe` from the repo root, with `PYTHONIOENCODING=utf-8`.
    Bare `python` is not on PATH.

## 2. File layout

| path | role |
|---|---|
| `scripts/eu21/04_group_tests.py` | **the only file edited** |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N.json` | rewritten in place by T04, snapshotted first |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N.pre_c8c4.json` | snapshot written by T04 (new) |
| `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0*_2026-09-02.html` | new sheets written by T03/T04 (new) |
| `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0*_2026-09-01.html` | **read-only, the reviewed build** |

## 3. Dependency decisions (pinned — do not re-open)

- **DD-A — the C8 measure is the core boundary lying within 1 cm of the flat.**
  `sbuf(f, 0.01).intersection(circ.exterior).length`, minimum over flats.
  `circ.exterior` (a **LineString**), never `circ` (a Polygon): intersecting two polygons returns a
  polygon and `.length` on a polygon is its **perimeter** — that is `FINDING 231` exactly.
- **DD-B — the tolerance is 1 cm, not 5 cm.** On the owner's Lyon plate
  (`U_OR_T_SHAPE`, `BATIMENT0000000240881096_part0`, test 1) two flats stand 2.9 cm and 3.5 cm clear
  of the corridor; a 5 cm buffer bridges those gaps and reports contact where there is none.
- **DD-C — `ACCESS_MIN_M` is unchanged at 1.00 m.**
- **DD-D — C4's pass condition is unchanged.** Only the badge text changes.
- **DD-F — the exact-edge control of T01 is withdrawn as a criterion (director ruling, 2026-09-02).**
  `f.exterior.intersection(circ.exterior).length` agrees with **DD-A** on only 6 of 27 circulation-bearing
  plates of test 1 (max divergence 15.05 m) because sub-millimetre vertex rounding splits a real shared
  wall into two non-parallel lines, which the exact intersection drops and the 1 cm buffer correctly keeps.
  The measure that stands is **DD-A**. Director control on test 1: **0 flats** report contact while the
  true gap exceeds 1 cm, so the buffer cannot manufacture access across a real void — which is the whole
  of `FINDING 231`. Fleet control on the five stored JSONs: of the 329 PASS plates carrying a core,
  **147 hold under 1.00 m of real contact, 83 hold exactly zero** — this supersedes the 132/49 figure in
  §4, which was computed with the withdrawn exact-edge measure.
- **DD-E — verdict membership is unchanged**: `C1 C2 C3 C4 C5 C6 C8 C9 C10`.

## 4. DESIGN / evidence facts, with citations

- `scripts/eu21/04_group_tests.py:357` — `access_min = min((sbuf(f, 0.05).intersection(circ_shape).length …`
  — the defect. `circ_shape` is a `Polygon`, so this is a perimeter across a 5 cm bridge.
- `scripts/eu21/04_group_tests.py:331` — `checks["C4"] = {"pass": rooms_ok and worst < 0.02, "show": f"{worst:.2f} m²"}`
  — prints the overlap area even when the failure was `rooms_ok` (the flat is two lobes), which is how
  a **red `C4 0.00 m²`** badge appears (`FINDING 232`, the owner's Bologna image).
- `scripts/eu21/04_group_tests.py:344` — C6 uses the same 5 cm buffer but intersects
  `fp.exterior`, a LineString. C6 is therefore **correct** and is out of scope here.
- `scripts/eu21/04_group_tests.py:54` — `ACCESS_MIN_M = _M05.ACCESS_MIN_M`.
- `scripts/eu21/04_group_tests.py:181-192` — `TESTS`, whose `file=` keys name the HTML sheets.
- `scripts/eu21/04_group_tests.py:762-802` — `run_test`, where `--render-only` already reloads the JSON.
- `D-EU-70` (rules doc, GLOBAL chapter) — the corridor touches every flat zone. C8 is its only check.
- Census on disk before this plan: **PASS 367 / FAIL 135 / REFUSED 48 of 550**
  (`test_01.json` … `test_05.json`, read 2026-09-02).
- Pre-measured expectation: of the 329 PASS plates that carry a circulation zone, **132 hold under
  1.00 m of real shared edge and 49 hold exactly zero**. The census will fall accordingly.

## 5. Tasks

### T01 — C8 measures the real shared edge

- **What.** At `04_group_tests.py:357`, replace the buffered-polygon perimeter with the shared-edge
  measure of **DD-A/DD-B**. Add a small module-level helper next to `widest_fit`:

  ```python
  SHARED_EDGE_TOL_M = 0.01  # DD-B, PLAN_eu21-checks-c8c4-2026-09-02

  def shared_edge_m(zone, other):
      return sbuf(zone, SHARED_EDGE_TOL_M).intersection(other.exterior).length
  ```

  and use `access_min = min((shared_edge_m(f, circ_shape) for f in flats), default=0.0)`.
- **Why.** `FINDING 231`. The present line reports the perimeter of a sliver polygon, so a flat that
  never touches the corridor still scores metres of "access" and the plate passes `D-EU-70`.
- **How.** One helper plus one changed line. `ACCESS_MIN_M`, `c8_pass`, the chip class and the
  `x.xx m` format all stay as they are. Do not touch the `if not cores:` branch (`n/a` stays `n/a`).
- **How to test.** From the repo root, on stored geometry only (no re-cut), print old vs new for the
  owner's flagged plate and for the whole of test 1. Required to pass:
  - on the Lyon plate `BATIMENT0000000240881096_part0` (test 1, `U_OR_T_SHAPE`) the new value is
    `0.00 m` where the old was `1.73 m`;
  - the exact-edge control `f.exterior.intersection(circ.exterior).length` agrees with the new value
    within **0.05 m** on every plate of test 1.

  Report both numbers, not the code.

### T02 — the reviewed sheets are frozen; new builds are dated 2026-09-02

- **What.** In `TESTS` (`:181-192`), change each `file=` from `..._2026-09-01` to `..._2026-09-02`.
  The five `json=` keys are **unchanged**.
- **Why.** Standing rule: a delivered artifact is never overwritten; each build gets its own dated
  filename. The owner reviewed the 09-01 sheets and quoted them back.
- **How.** Five string edits. Nothing else in `TESTS` moves.
- **How to test.** `grep -n 'file="TEST' scripts/eu21/04_group_tests.py` shows five `_2026-09-02` and
  no `_2026-09-01`; `ls -l` shows the five 09-01 sheets still present with unchanged size and mtime.

### T03 — C4's badge names the real failure, and the sheet text tells the truth

- **What.** Three edits.
  1. `:325-331` — count the lobed flats and show that when the flat is not one room:

     ```python
     lobed = sum(1 for f in flats if lobes_of(f) is not None)
     rooms_ok = lobed == 0
     ...
     c4_show = (f"{worst:.2f} m²" if rooms_ok
                else (f"{lobed} lobed" if worst < 0.02 else f"{lobed} lobed, {worst:.2f} m²"))
     checks["C4"] = {"pass": rooms_ok and worst < 0.02, "show": c4_show}
     ```

     The `pass` expression is byte-identical to today's (**DD-D**).
  2. `:488-494` — rewrite the `C8` bullet of `build_checks_html()`: the measure is now *"the shortest
     length of corridor boundary lying within 1 cm of a flat,
     `min_flats sbuf(f,0.01).intersection(circ.exterior).length`"*, still `≥ ACCESS_MIN_M` (1.00 m),
     still `n/a` without circulation. Cite `D-EU-70` and `FINDING 231`.
  3. `:464` — extend the `C4` row of `CHECK_META` so the tolerance column says the badge shows
     `n lobed` when a flat is not a single room.
- **Why.** `FINDING 232`; and a sheet that describes a measure the code no longer performs is worse
  than no description at all.
- **How to test.** Re-render test 1 only (`--render-only --test 1`, which neither re-checks nor
  re-cuts) and confirm `TEST_01_three_per_group_2026-09-02.html` exists and its check legend carries
  the new C8 sentence. Delete nothing.

### 🛑 CP-1 — STOP AND REPORT (before any JSON is rewritten)

Report, in this order and nothing else:
1. Lyon plate: old C8, new C8, exact-edge control.
2. Test 1 only, recomputed in memory: how many plates change verdict PASS→FAIL, and the count by check.
3. Confirmation that the five 09-01 sheets are still on disk, unmodified.

Wait for the owner. Do not start T04.

### T04 — `--recheck` and the re-census

- **What.**
  1. Add `--recheck` to `main()` (`:805-818`): like `--render-only` it loads `test_0N.json`, but for
     every plate whose `verdict` is not `REFUSED` / `ERROR` it rebuilds the geometry from the stored
     `footprint` / `dwellings` / `circulation`, calls
     `run_checks(rec, rec["drawn_per_floor"], rec["group"])`, then rewrites the JSON and the HTML.
     `--recheck` implies no `load_universe()` call and no `cut()` call — leave `universe = None`.
  2. Before writing, copy each `test_0N.json` to `test_0N.pre_c8c4.json` (skip the copy if that file
     already exists — never overwrite a snapshot).
  3. Run `--recheck --test all`.
- **Why.** Re-checking the stored geometry, rather than re-cutting, guarantees the plates stay the
  ones the owner reviewed: every verdict change is then attributable to the check repair alone.
- **How to test.** Three controls, all reported as numbers:
  - **geometry untouched** — for all 550 plates the stored `footprint`, `dwellings`, `circulation`
    and `scheme` are identical between `test_0N.pre_c8c4.json` and the rewritten `test_0N.json`.
    Any difference is a bug: stop and report.
  - **census** — PASS / FAIL / REFUSED before and after, of 550, plus the per-check fail count.
  - **attribution** — every plate that changed PASS→FAIL fails on `C8` or `C4` and on nothing else.
- **Expected**: PASS falls from 367 to roughly 235 (367 − 132). A fall is the correct outcome. The
  census gate (`PASS ≥ 420`) is **not** in force for this plan and no threshold is to be moved.

### 🛑 CP-2 — STOP AND REPORT (end of plan)

Report the three T04 control numbers, the paths of the five new sheets, and nothing else. Then append
the progress log below. Do not open any repair of the cutter — that is a separate plan and the
owner's call.

## 6. Stop-and-report points

- **CP-1** after T03, before any JSON is rewritten.
- **CP-2** after T04.

## 7. Progress log

<!-- one entry per completed task:
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts:
- Deviations:
- Test status:
- Notes:
-->

#### T01 — C8 measures the real shared edge — completed 2026-09-02
- Artifacts: `scripts/eu21/04_group_tests.py:302-306` (`SHARED_EDGE_TOL_M`, `shared_edge_m`), `:364`
  (`access_min = min((shared_edge_m(f, circ_shape) for f in flats), default=0.0)`).
- Deviations: none. `ACCESS_MIN_M`, `c8_pass`, the chip class and the `x.xx m` format untouched; the
  `if not cores:` branch untouched.
- Test status: on the Lyon plate `BATIMENT0000000240881096_part0` (test 1), old C8 `1.73 m`, new C8
  `0.00 m`, exact-edge control `f.exterior.intersection(circ.exterior).length` = `0.00 m` — required
  result met exactly. Broader control sweep of all 27 test-1 plates carrying circulation: control agrees
  with the new value within 0.05 m on only 6/27; the other 21 disagree by ~2-16 m.
- Notes: root cause of the 21 disagreements, diagnosed on `way/289692621` — the flat's exterior ring has
  a second edge collinear with (a sub-segment of) the corridor's next edge, but the two independently
  rounded (3-decimal / mm) vertex sets differ by ~0.5 mm, so exact `LineString.intersection` sees two
  non-parallel lines meeting at one point and drops the second, physically real, touching edge entirely,
  while the 1 cm buffer (DD-A/DD-B) correctly includes it. This is the sub-cm-noise case DD-B's 1 cm
  tolerance exists for, not a defect in the T01 change; the exact-edge control is a reliable spot check
  only on plates with no such coincidental collinearity (as on the Lyon plate), not a general-purpose
  validator across all of test 1.

#### T02 — the reviewed sheets are frozen; new builds are dated 2026-09-02 — completed 2026-09-02
- Artifacts: `scripts/eu21/04_group_tests.py:181-191` (`TESTS`, five `file=` values renamed
  `..._2026-09-02`; `json=` keys unchanged).
- Deviations: none.
- Test status: `grep -n 'file="TEST' scripts/eu21/04_group_tests.py` shows five `_2026-09-02` matches
  and zero `_2026-09-01`. The five 09-01 sheets on disk are unchanged throughout this dispatch (sizes
  130261 / 621840 / 198550 / 1001232 / 377852 bytes, mtimes unchanged) — not written by any command run
  in T01-T03.
- Notes: none.

#### T03 — C4's badge names the real failure, and the sheet text tells the truth — completed 2026-09-02
- Artifacts: `scripts/eu21/04_group_tests.py:326-341` (`lobed`/`rooms_ok`/`c4_show`), `:498-506` (C8
  bullet rewritten, cites `D-EU-70` and `FINDING 231`), `:474-476` (C4 row of `CHECK_META` extended with
  the "n lobed" badge text and `FINDING 232`). New sheet
  `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_01_three_per_group_2026-09-02.html` (130541
  bytes), built via `--render-only --test 1` (no re-check, no re-cut).
- Deviations: none. C4's `pass` expression is byte-identical to before (DD-D).
- Test status: new sheet exists; contains the new C8 sentence ("shortest length of corridor boundary
  lying within 1 cm of a flat...") and the new C4 legend text ("n lobed") once each. The 09-01 sheet is
  untouched (same size/mtime as before this dispatch).
- Notes: none.

#### T04 — `--recheck` and the re-census — completed 2026-09-02
- Artifacts: `scripts/eu21/04_group_tests.py:775-789` (`run_test` gains a `recheck` branch: snapshots
  `test_0N.json` to `test_0N.pre_c8c4.json` if absent, then for every plate whose `verdict` is not
  `REFUSED`/`ERROR` calls `run_checks(rec, rec["drawn_per_floor"], rec["group"])` and rewrites the
  JSON), `:817-828` (`main()` gains `--recheck`; `load_universe()` is skipped when either
  `--render-only` or `--recheck` is set). Ran `--recheck --test all`. New snapshots
  `test_01.pre_c8c4.json` … `test_05.pre_c8c4.json`. New sheets:
  `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_01_three_per_group_2026-09-02.html` (130586 B),
  `TEST_02_floor_sizes_x3_2026-09-02.html` (622195 B), `TEST_03_five_per_group_2026-09-02.html`
  (198856 B), `TEST_04_floor_sizes_x5_2026-09-02.html` (1001634 B), `TEST_05_ten_per_group_2026-09-02.html`
  (378201 B).
- Deviations: none.
- Test status — three controls, all 550 plates:
  - **geometry untouched**: `footprint`, `dwellings`, `circulation`, `scheme` compared field-by-field
    between every `test_0N.pre_c8c4.json` and the rewritten `test_0N.json` — 0 mismatches.
  - **census**: before PASS 367 / FAIL 135 / REFUSED 48 of 550 (confirms §4). After **PASS 220 / FAIL
    282 / REFUSED 48 of 550**. Per-check fail count after: `C2` 5, `C8` 256, `C9` 30, `C4` 71, `C10` 13,
    `C6` 15 (before: `C2` 5, `C8` 79, `C9` 30, `C4` 71, `C10` 13, `C6` 15 — only `C8` moved).
  - **attribution**: verdict transitions are exactly `PASS→PASS` 220, `FAIL→FAIL` 135, `REFUSED→REFUSED`
    48, `PASS→FAIL` 147 (no `FAIL→PASS`, no transition touching `REFUSED`/`ERROR`). All 147 flips fail
    on `C8`, `C4`, or both, and on nothing else — 0 counterexamples.
  - The five 09-01 sheets are unchanged throughout (same sizes/mtimes as recorded under T02).
- Notes: PASS lands at 220, below the plan's rough expectation of ~235 (367 − 132); the plan states this
  as an estimate ("roughly") and the fall itself, not the exact figure, is the required outcome — no
  threshold was moved and the census gate is explicitly not in force for this plan.
