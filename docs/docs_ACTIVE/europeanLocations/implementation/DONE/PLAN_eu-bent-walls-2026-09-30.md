# PLAN — EU bent party walls: find why 478 homes keep a bent wall, then straighten the ones the rules say must be straight (2026-09-30)

> **CLOSED 2026-10-08 — arc archived.** Tasks without a completed entry were not run; superseded by the owner's stop rulings D-EU-148 / D-EU-149 (2026-10-08).

- **Slug:** `eu-bent-walls-2026-09-30`
- **Author:** director (manager session), 2026-09-30. Executor: fresh Sonnet sessions, one per task range.
- **Owner request (2026-09-30, verbatim):** "when weill we focus on these 836 cases, still we have very low succesfull divisions." Then, to "should the 478 bent-wall homes get their own plan after this one?": "yes please, if needed create anaother investigatio/implementation plan for them as well, thank you".
- **Rule book (read-only):** `docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_nocore_2026-09-03.html` step 5 "Absorb what is left over" (`:381`, same text `:420`, `:459`): *"the wall between two flats is one straight line, wall to wall … A wall that genuinely bends round a wing is kept as it is"*. `EXAMPLE_dwelling_layout_validation_nocore_2026-09-03.md`.
- **Predecessors (open, not reopened here):** `implementation/PLAN_eu-floor-division-residual-2026-09-29.md` (T06 on Speed, CP-3 pending) and `implementation/PLAN_eu-rulebook-change-2026-09-30.md` (T04 dry run, CP-1 pending). The 358 rule-breaking homes (V1/V2) and the 102 undivided homes belong to the rule-book plan, not here.
- **Allocated here:** `D-EU-130` (label of the homes whose only bends go round a wing), `D-EU-131` (junction move and wall extension), `D-EU-132` (bent-wall-only improvement guard), `FINDING 276` (the census counts wing-bend-only homes as bent). Next free after this plan: `D-EU-133` / `FINDING 277`.

---

## 1. What this plan delivers (plain words)

478 of 4,171 homes are divided into flats and pass every hard check, but at least one wall between two flats bends inside the floor (Bologna 198, Madrid 155, Lyon 86, London 39). The rules want that wall straight, unless it bends round a wing of the building.

Measured by the director on `rulebook_2026-09-30/baseline.csv` (2026-09-30):

- **350 of 478** have at least one storey with a bend the engine counts as cut-made and not a wing bend (`C13 > 0`). These break the rule text.
- **128 of 478** have `C13 = 0` on every storey: their only bends go round a wing, which the rules allow. The census labels them bent anyway (`FINDING 276`, T01 confirms).
- **475 of 478** pass every hard check and the balance check on every storey; 3 do not (T01 lists them).
- **0 of 3,192** OK homes have `C13 > 0` on any storey. A change that only acts where `C13 > 0` cannot reach a home that is correct today.

The predecessor's straighten step fixed 1 of 415 of these homes. On a sample of 25 Madrid homes (20 storeys) it was blocked because the bend sits at a point where three flats meet (7), the wall ends inside the floor or at a wing corner (5), or the straight wall broke another check (8) (`PLAN_eu-floor-division-residual-2026-09-29.md`, T04 entry, Notes).

This plan first measures why each of the 350 is bent (T01, no engine change, can run now). The owner then rules on the 128 (CP-1). Only then does it add cutter moves for the causes a move can reach, prove that no correct home changes, and simulate the changed homes only.

---

## 2. Hard rules for the executor

1. **Model:** Sonnet. Never plan, never propose alternatives; on ambiguity STOP and quote the conflicting lines.
2. **No cluster access** (`ssh`, `scp`, `sbatch`, `squeue`, `sacct`). All EnergyPlus runs are director-only on Speed. **No local EnergyPlus, ever.**
3. **Local geometry runs** (layout call only): at most **8 concurrent processes**, the four districts in parallel, never one after another.
4. **Python:** `C:/Users/o_iseri/Desktop/OpenUBEM/.venv/Scripts/python.exe`. Tests: `.venv/Scripts/python.exe -m pytest tests/<file> -q`.
5. **T01 changes no engine code.** `european_nocore.py`, `european_residential.py` and `run_eu_s2_campaign.py` are read-only until the rule-book plan reaches its CP-3 (both plans edit the same cut code; this plan's T02 starts from the state that plan ships).
6. **Every threshold and dwelling count stays frozen.** No change to `MAX_FLAT_ASPECT`, `MIN_SPREAD`, the C6 2.50 m or C10 0.10 m² literals, the 40-vertex cap, `WING_BEND_TOLERANCE_M`, `WALL_END_TOLERANCE_M`, or any `k`.
7. **Never edit** root `main.py`, any OVERVIEW/DESIGN doc, `openubem/idf/surfaces.py`, the 2026-09-03 rules files or the r6 `plans3D` pages.
8. **Never delete or regenerate a delivered tree.** Every `_recut_2026-09-08`, `_merged_2026-09-08`, `_fix_2026-09-29`, `_merged_2026-09-29` and `_rules_*` tree is read-only input.
9. **A home with `C13 = 0` on every storey is never re-emitted.**
10. **Read guard:** `grep -n` first, then a ranged read; never read a whole file over 300 lines.
11. **Errors:** search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first; register every solved error there before closing the task.
12. **Every count is "N of M"**, never a bare percentage.
13. **Progress log** (§8): one entry per task, `#### TXX — <title> — completed YYYY-MM-DD`, Artifacts / Deviations / Test status / Notes. Append only.
14. No `.py` under `docs/`. No code comments. No new scripts or test files beyond the ones named in §3.

---

## 3. File layout

| Path | Role |
|---|---|
| `openubem/geometry/european_nocore.py` | `c13_bent_walls` (`:2020`), `_flat_bends` (`:1979`), `_plate_reflex_points` (`:1956`), `_GATED_CHECKS` (`:1953`), `_strictly_better` (`:2059`), `_straighten_candidates` (`:2125`, skips a wall with an interior end `:2130-2132` and a wall ending at a wing corner `:2133-2134`), `_straightened` (`:2138`), `_straighten_pass` (`:2157`), `improve_cut_nocore` (`:2384`, straighten only when `C13 > 0` `:2401`) — **T02 adds `_junction_pass` and `_extend_pass` here** |
| `openubem/geometry/european_residential.py` | `_nocore_cut_and_improve` (`:1348`) — read-only |
| `scripts/analysis/eu_division_residual_census_2026-09-29.py` | census; V3 rule `zmax >= 1` (`:242-243`), split `wrap` / `wing_bend_only` (`:254-256`) — changed only in T06, after CP-3 |
| `scripts/analysis/eu_bentwall_why_2026-09-30.py` | **new**, T01 driver; T03 reuses it with `--after` |
| `tests/test_eu_bent_walls_2026_09_30.py` | **new**, the only new test file |
| `scripts/run_eu_s2_district_campaign.py` | `prepare`, `--only-ids` (T04) |
| `openubem/outputs/eu_evidence/EU-11/rulebook_2026-09-30/baseline.csv` | input: `cls`, per-storey checks incl. `n_storeys_C13_fail` |
| `openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/v3_split.csv` | input: T01-of-predecessor split (415 rows) |
| `openubem/outputs/eu_evidence/EU-11/bentwall_2026-09-30/` | all evidence of this plan |
| `openubem/outputs/eu_evidence/EU-11/<D>_bentwall_<date of T04>/` | T04 output (candidates only) |

---

## 4. Dependency decisions (pinned)

1. **`D-EU-130` — homes whose only bends go round a wing (owner, CP-1).** Proposal: a home with `C13 = 0` on every storey and every hard check passing is counted as following the rules, as step 5 of the groups sheet already says. Label only: no cut, IDF or EUI changes. Until CP-1 the census label stays as it is.
2. **`D-EU-131` — two new cutter moves, strictly better only.**
   - **Junction move** (`_junction_pass`): where two or three bent walls meet at a point where three flats meet, replace each with the straight segment from the junction to its end on the plate boundary; try junction positions on a 0.20 m grid within 2.0 m of today's junction (at most 400 positions per junction).
   - **Wall extension** (`_extend_pass`): a bent wall with one end inside the plate that is not a junction is replaced by the straight segment from its boundary end through its first straight run, extended to the plate boundary.
   - **Straighten then slide:** when the straight wall from `_straightened` breaks only C11 or C12, slide it in the 0.05 m steps of `_balance_pass` before scoring, as one candidate.
   - A wall ending within `WING_BEND_TOLERANCE_M` of a plate reflex vertex is never moved.
3. **`D-EU-132` — bent-wall-only guard.** The new moves run only on a storey with `C13 > 0`. A new cut is kept only if it passes every check in `_GATED_CHECKS` that the current cut passes, keeps C12 passing where it passes today, and has a lower `C13`. Otherwise the storey keeps the very same objects. This is `_strictly_better` (`:2059`) with C13 as the only allowed improvement.
4. **Same number of flats, same `k`, same plate.** Only the position of the walls between flats changes.
5. **Published numbers:** whichever EUIs the owner has adopted at the predecessors' CP-3 stay quotable until this plan's CP-3. The director tells GSSCanada/4J before shipping.

---

## 5. Facts with line citations (verified 2026-09-30)

1. Class counts in `rulebook_2026-09-30/baseline.csv` (4,171 rows): OK 3,192, S1 16, V3 478, V1 252, V2 106, U1 53, U3 47, U2 1, U4 1, X 25.
2. Of the 478 V3: source tree `_merged_2026-09-08` 413, `_fix_2026-09-29` 65; geometry from installed side-car 413, from fix-IDF floor surfaces 52, `fix_idf_not_a_partition_blank` 13. 415 are in `v3_split.csv` (277 `wrap`, 138 `wing_bend_only`); 63 entered V3 through the predecessor's T05.
3. The census sets V3 when any flat has a cut-made corner (`zmax >= 1`, `eu_division_residual_census_2026-09-29.py:242-243`), wing bends included, while `C13` subtracts wing bends (`european_nocore.py:2032-2035`). That is why 128 homes with `C13 = 0` are labelled V3.
4. `C13` is reported, never part of the verdict (`european_nocore.py:1907`, docstring `:2021-2026`).
5. `_straighten_candidates` skips any wall whose end is more than `WALL_END_TOLERANCE_M` from the plate boundary (`:2130-2132`), which is every wall ending at a three-flat junction. This is the 7 + 5 of the 20 blocked sample storeys.

---

## 6. Tasks

### T01 — Why each bent-wall home is bent (no engine change; can run now)

**What.** Write `scripts/analysis/eu_bentwall_why_2026-09-30.py`. For each of the 478 V3 homes, rebuild each storey's cut with the same loading as the predecessor's `division_residual_2026-09-29/scratch/t04c_why.py`, and for every cut-made corner write one row to `bentwall_2026-09-30/bentwall_why.csv`: `district, building_id, stem, storey, k, corner_x, corner_y, flats_touching, c13_storey, type`, and for `straight_not_better` the checks the straight wall breaks. `type` is exactly one of:
- `wing_bend` — the wall run through it ends within `WING_BEND_TOLERANCE_M` of a plate reflex vertex (allowed by the rules);
- `junction_wrap` — the wall run ends at a point touched by three or more flats;
- `interior_end` — the wall run ends inside the plate, not at a junction;
- `straight_not_better` — a straight wall from `_straightened` exists and breaks at least one check the current cut passes;
- `straight_missed` — a straight wall exists, passes every check the current cut passes and has lower `C13` (an engine selection defect: report it, do not fix it);
- `no_chord` — the straight segment between the two ends leaves the plate.

Also write `bentwall_summary.md`: counts per type and district; homes by worst type; the 128 homes with `C13 = 0` checked corner by corner (all `wing_bend`, or name each exception); the 3 homes that fail a check on some storey, with the check.

**Why.** The straighten step helped 1 of 415 of these homes. Fixes are written only for causes a move can reach.

**How.** Import the engine helpers read-only (`_flat_bends`, `_plate_reflex_points`, `_party_walls`, `_straightened`, `_score_cut`, `_strictly_better`). For the 65 homes from `_fix_2026-09-29`, use the floor surfaces of that tree's IDF, as the rule-book T01 did. 8 processes at most.

**How to test.** Rows cover 478 of 478 homes. Every corner gets exactly one type. The 128 homes with `C13 = 0` in `baseline.csv` show `wing_bend` only, or each exception is named. On the 25 Madrid sample homes of the predecessor's T04 Notes, the split reproduces 7 / 5 / 8 (junction / interior or wing end / not better), or the difference is listed by id. `straight_missed` is 0, or each row is listed. Register `FINDING 276` in §8 with the measured count. **STOP → CP-1.**

### T02 — Junction move, wall extension, straighten-then-slide (`D-EU-131`, `D-EU-132`; after the rule-book plan's CP-3)

**What.** In `european_nocore.py`, add `_junction_pass(poly, flats, k, base)` and `_extend_pass(poly, flats, k, base)`, and add the slide step for a straight wall that breaks only C11 or C12. Call them from `improve_cut_nocore` right after `_straighten_pass`, under the same `C13 > 0` condition (`:2401`). Only the moves CP-1 keeps are written.
**Why.** T01's `junction_wrap`, `interior_end` and `straight_not_better` rows, as trimmed at CP-1.
**How.** §4 items 2–4. Each candidate is scored with `_score_cut` and accepted with the `D-EU-132` rule; rejected tags are remembered as in `_straighten_pass`.
**How to test.** Unit tests in `tests/test_eu_bent_walls_2026_09_30.py`:
- three flats on a 30 × 20 m rectangle, with the junction wall bent, come out with straight walls and `C13 = 0`;
- a wall ending at a wing corner of an L plate is left as the same objects;
- a storey with `C13 = 0` returns the same objects;
- a candidate that would break C6 is refused.

The predecessor's test files (`test_eu_floor_division_residual_2026_09_29.py`, `test_eu_cutter_moves_2026_09_29.py`, `test_eu_collinear_ring_cleanup.py`, `tests/geometry/test_eu13b_dwelling_conservation.py`) and `tests/test_eu_rulebook_change_2026_09_30.py` stay green.

### T03 — Dry run: who improves, and proof that no correct home moves

**What.** Run `eu_bentwall_why_2026-09-30.py --after`, layout call only, over the 478 **and** every home with class OK or S1 in the baseline (4 districts, at most 8 processes). Write `bentwall_2026-09-30/dryrun.csv`: per home `improved / unchanged / regressed` and old → new `C13`.
**How to test.**
- Regressed is 0 of 478.
- OK and S1 homes: every storey returns the same objects, 3,208 of 3,208.
- A table per district: improved N of M, new class counts, storeys still bent by T01 type.

**STOP → CP-2.**

### T04 — Build the candidates only, with the regression gate

**What.** `prepare --only-ids` over the improved homes of T03, into `<D>_bentwall_<date>/`. Gate per home: new `C13` below the old one, every hard check that passed still passes, zone count unchanged, a new `idf_sha256`, and `at_risk` False. Write `gate.csv` and the IDF list for Speed.
**How to test.** Each gate line reports N of M. One failure is a STOP. **STOP → director runs T05.**

### T05 — Speed: crash test, then campaign and harvest (director only)

`sbatch --array … %32 --time=7-00:00:00`. Harvest with the predecessor's merged-tag pattern. `sacct` shows 0 running and 0 pending; fatals are classified by `eplusout.err` text; `summary.json` states "N of M". **STOP → CP-3.**

### T06 — Labels, pages, ledger (after CP-3)

**What.**
- Census: split V3 by `C13` as ruled at CP-1 (`D-EU-130`).
- New `plans3D` pages dated the day of the build.
- STATE §0/§8 entries for `D-EU-130`…`132` and `FINDING 276`.
- Supersession markers on every restated number.
- Debug-reference entries for every error met.

---

## 7. Stop-and-report points

- **CP-1 (after T01).** The owner sees the causes in plain words and rules on `D-EU-130`, the label of the homes whose only bends go round a wing. The director keeps in T02 only the moves whose T01 type has homes in it.
  - **Ruled 2026-09-30 (owner, "yes continue"):** `D-EU-130` = yes, on the engine test. The 88 of the 128 homes with no engine-counted bend (only wing bends, or none) are counted as following the rules; label only, no cut, IDF or EUI change. The other 40 (27 named exceptions + 13 without geometry) stay in V3. All T01 types have homes, so T02 keeps every move. T02 starts after the rule-book plan's CP-3.
- **CP-2 (after T03).** Improved N of 478, 0 regressed, 3,208 of 3,208 correct homes unchanged. The owner's word sends the candidates to T04 and Speed.
- **CP-3 (after T05).** The owner decides whether the new EUIs replace the published ones. Until then nothing published changes.

---

## 8. Progress log

#### T01 — Why each bent-wall home is bent — completed 2026-09-30

- **Artifacts:** `scripts/analysis/eu_bentwall_why_2026-09-30.py` (one process, about 30 s); `openubem/outputs/eu_evidence/EU-11/bentwall_2026-09-30/bentwall_why.csv` (1,615 rows: 1,174 engine-basis corners, 415 census-basis corners, 13 `no_geometry` rows, 13 `no_bend` rows), `bentwall_summary.md`, `scratch/bentwall_homes.csv`. No engine file touched; no test file written yet (only T02 names one).
- **Deviations:** (1) Geometry loading is the rule-book T01 loader (`rulebook_2026-09-30/scratch/t01_baseline.py`: installed side-car 413, fix-IDF floor surfaces 52), not `t04c_why.py`, which rebuilds cuts through the layout call. (2) The 13 homes with `fix_idf_not_a_partition_blank` have no usable floor geometry: one row each, `type = no_geometry`, outside the six types. (3) Columns added: `basis` (`engine` = the `_flat_bends` test on the plate; `census` = the same test on the census's smoothed plate, added only on storeys where the engine sees `C13 = 0`), `storey_failed_checks`, `straight_breaks`. (4) `straight_missed` follows the plan text (lower C13, no check broken); the column `straight_breaks` says whether `_strictly_better` would also accept it (`accepted_by_engine`) or refuses it only because the C12 spread value drops (`spread_lower_only`). (6) Audit fix 2026-09-30: 13 homes that were read but had no corner on either basis had no row (coverage was 465 of 478); each now has one row, `type = no_bend`, `basis = none`; the 88 / 27 split of the 128 is unchanged; the Madrid 25-home list was added to the summary. (5) A corner whose wall run, wall end or own point is touched by three or more flats and is not on the plate boundary is `junction_wrap`; an end inside the plate touched by fewer is `interior_end` (a wall end within 0.10 m of a reflex vertex also counts there).
- **Test status:** Rows cover 478 of 478 homes (measured: 478 distinct district+id; 13 `no_geometry`, 13 `no_bend`); every corner has exactly one type. Engine-basis corners per type: `straight_not_better` 486, `interior_end` 406, `junction_wrap` 167, `straight_missed` 71, `wing_bend` 25, `no_chord` 19 (Madrid 28/182/3/82/35/10, Lyon 17/86/3/40/93/0, London 4/24/0/23/11/0, Bologna 22/194/13/261/28/15 in the order missed/not-better/no-chord/interior/junction/wing). 128 homes with `C13 = 0`: 13 of 128 have no geometry; of 115 read, 88 show only `wing_bend` corners or no cut-made corner, 27 of 115 are exceptions (20 of them census-`wrap` homes in `v3_split.csv`, 7 fix-IDF homes), named in `bentwall_summary.md`; 2 homes differ from the baseline `C13` (`29822` mine 1 vs 0; blank `BATIMENT0000000240880372_part0` has no geometry). Madrid 7 / 5 / 8: NOT reproduced. The plan gives no id list; the first 25 Madrid `wrap` homes in `v3_split.csv` (ids and per-home counts listed in `bentwall_summary.md`, section "Madrid 25-home sample") give junction 7 / interior-or-wing end 10 / not better 43 corners on the engine basis (junction matches 7; the other two differ). `straight_missed` = 71 corners (27 of 478 homes), not 0: only 9 of them would be accepted by the engine's `_strictly_better`; the other 62 are refused for the C12 spread value alone. The 3 homes failing a check on some storey: Madrid `way/435398515` C10 (3 of 3 storeys), London `way/409624879` C10 (4 of 4), Bologna `28721` C11+C12 (4 of 6).
- **Notes:** **FINDING 276** (registered, measured) — the census and the engine disagree on what a bend is, not only on wing bends. The 128 homes labelled V3 with `C13 = 0`: 13 of 128 have no geometry; of 115, 55 are census `wing_bend_only`, 22 are census `wrap` (the census sees a cut-made corner the engine does not, because it tests against the smoothed plate), 38 come from the fix trees and are not in `v3_split.csv`; 88 of 115 show only wing corners or none by the engine's own test, 27 of 115 keep a non-wing corner on the census test. So 88 to 115 of the 478 V3 homes are labelled bent without an engine-counted bent wall. Of the 350 homes with `C13 > 0`, the dominant cause is a straightening that breaks only C12 (`straight_not_better`, 327 corners break C12 alone) and a wall end inside the plate (`interior_end`, 406 corners); `junction_wrap` is 167 corners. **STOP at CP-1.**
