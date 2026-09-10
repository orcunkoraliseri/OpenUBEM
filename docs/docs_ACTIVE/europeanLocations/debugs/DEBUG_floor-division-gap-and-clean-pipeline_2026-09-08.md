# Why some residential buildings still have no floor division, what the real numbers are, and the clean pipeline for GSSCanada

**Date:** 2026-09-08. **Written by the director for the owner.** Plain language; every number was measured
today on the files on disk (paths at the end of each section). Nothing here changes a published number.

---

## 0. The answer in five lines

1. **The buildings you screenshotted are already fixed.** All four Lyon buildings (`…881107`, `…881156`,
   `…879996`, `…879972`) are now divided into flats, re-simulated, and drawn divided in the current Lyon
   viewer. Your screenshots come from the viewer as it was before the evening of 2026-09-07. Reopen
   `outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html` with a hard refresh (Ctrl+F5).
2. **The label you saw was wrong, not the geometry.** "L_SHAPE_DECOMPOSITION_FAILED" and
   "DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8" are refusal reasons from the **old corridor-era engine**. The
   viewer copies them from a side-file dated 2026-09-01. The real reason those buildings were undivided was
   a **redundant vertex on a straight edge of the footprint**, which made the emitter throw the cut away.
   That bug is fixed (ring cleanup, `D-EU-109`), and 1,055 buildings got their division back.
3. **Bologna still looks bad because its viewer is stale**, not because Bologna is worse. The Bologna viewer
   on disk is from 2026-09-07 08:36, before its rebuild was simulated. It shows 664 undivided buildings; the
   rebuilt Bologna has 260. It will be regenerated when the Bologna delta job finishes (about 3.5 h from
   10:49 EDT today, measured, not guessed).
4. **Honest totals after everything in flight lands:** 3,128 of 3,601 simulated residential buildings are
   divided into flats (**86.9 %**). Of the whole residential stock (4,186), that is **74.7 %**.
5. **95 % of *all* residential buildings is not reachable with the data we have** (585 buildings, 536 of
   them in London, have no usable energy certificate or storey count and were never simulated). **95 % of
   the *simulated* buildings is reachable** with one rule decision (§4) plus a second pass on the vertex bug.

---

## 1. What you saw, and what each screenshot actually means

| Screenshot | Building | What the modal said | What was really going on | State today |
|---|---|---|---|---|
| 12 | `…240881107_part0`, 8 storeys | MASSING BOX, reason `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`, yet PASS ALL 7 CHECKS with 9 flats | The rule bench cut 9 flats per floor and passed. The old engine capped flats at 8 per floor; the label is that old engine's. The current cap is 12. The cut was then thrown away by the vertex bug. | **Divided: 9 per floor, 69 dwellings. Re-simulated.** |
| 13 | `…240881156_part0`, 8 storeys | MASSING BOX, `L_SHAPE_DECOMPOSITION_FAILED`, PASS with 4 flats | Old-engine label. Vertex bug discarded a valid 4-flat cut. | **Divided: 29 dwellings. Re-simulated.** |
| 9 / 11 | `…240879996_part0`, 6 storeys, 7,741 m² | MASSING BOX, `L_SHAPE_DECOMPOSITION_FAILED`, PASS with 6 flats | Same. This is the exact building `D-EU-109` was opened on. | **Divided: 6 per floor, 34 dwellings. Re-simulated.** |
| 10 | `…240879972_part0`, 7 storeys | MASSING BOX, `L_SHAPE_DECOMPOSITION_FAILED`, PASS with 4 flats | Same. | **Divided: 29 dwellings. Re-simulated.** |
| 2, 5 | courtyard `…879992`, multi-wing `way/310771773` | Divided, PASS | This is the target picture. | Unchanged. |

**Why the modal could say "PASS ALL 7 CHECKS" and "MASSING BOX" at the same time.** The badge comes from the
rule bench (the 2,544-building census that grades the cutting rules). The plan drawing comes from the IDF
that was actually simulated. Until 2026-09-07 those were two different things for 1,524 buildings: the rule
produced a good cut, and the IDF writer deleted it at the last step because one vertex on the footprint
outline sat on a straight line (angle > 179.9°). The safety net that deletes the layout exists because
EnergyPlus crashes on such vertices when two zones share a wall (`FINDING 210`); it was firing on 45.6 % of
the fleet instead of the 2 buildings it was designed for.

**Why the wrong reason text is shown.** `scripts/generate_eu_3d_viewers.py:854` reads the refusal reason
from the *EU-17 side-file* of the building (`EU-17/<district>/layouts/<id>.json`, all dated 2026-09-01,
written by the corridor-era engine). The task that should replace that text with the current
`geometry_outcome` is written but not yet run (`D-EU-109` T05). So any building that is still undivided
today shows a reason from an engine that is no longer used.

Evidence: `openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES_{ceiling82_2026-09-05,final_2026-09-07,merged_2026-09-07}/fr_lyo_hautcoeurpentes_manifest.csv`
(the four ids: `…INTERZONE_MISMATCH_REROUTED` before, `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` after, EUI
source `delta_2026-09-07`); `outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html` (each id carries
`"ls":"ruled"` with 6 / 9 zones per floor); `outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_data/layouts/*.json`
(dated 2026-09-01, carrying the old reasons); `implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md` §1–§2.

---

## 2. The real numbers, in three layers

Three different populations get mixed up in conversation. Keep them apart:

- **Residential stock** — every residential building in the four neighbourhoods: **4,186**.
- **Simulated** — buildings with enough data to build and run an IDF: **3,601** after the London recovery.
- **Divided** — simulated buildings whose IDF really contains flats (not one box per floor).

### 2.1 After the rebuild that is in flight (the truth, from the rebuilt IDF trees)

| District | Residential | Simulated | **Divided into flats** | Undivided: vertex bug still fires | Undivided: rule refused the cut, or no dwelling count | Never simulated (data gap) |
|---|---:|---:|---:|---:|---:|---:|
| Madrid Berruguete | 1,194 | 1,175 | **1,033 (87.9 %)** | 67 | 75 | 19 |
| Lyon Hauts-Pentes | 530 | 509 | **459 (90.2 %)** | 25 | 25 | 21 |
| London St Dunstan's | 1,242 | 706 | **685 (97.0 %)** | 7 | 14 | 536 |
| Bologna Galvani 2 | 1,220 | 1,211 | **951 (78.5 %)** | 85 | 175 | 9 |
| **Fleet** | **4,186** | **3,601** | **3,128 (86.9 % of simulated · 74.7 % of stock)** | **184** | **289** | **585** |

Before the fix the "vertex bug" column was 1,239 fleet-wide; it is now 184. That is the whole of what
`D-EU-109` did.

🔴 **Superseded 2026-09-09 (T08 of `implementation/PLAN_eu-recut-95pct-2026-09-08.md`).** This whole
table is the pre-recut baseline. After `D-EU-111` (best-effort tier) and `D-EU-112` (neighbour
imputation) landed and the recut was simulated and harvested: population is 4,171 of 4,186 stock
(not 3,601), divided is 3,641 ruled + 202 of 204 best-effort (T07/`CP-3` manifest-token count) against
289 rule-refused shrinking toward its refused-hard/density residual, the vertex-bug 184 is unchanged
(no remedy authorised, `FINDING 267`), and 576 of the 585 never-simulated are now recovered and
simulated. District EUIs: Madrid 81.387738/1,170 of 1,187 · Lyon 70.345716/527 of 529 · London
93.729757/1,240 of 1,240 · Bologna 54.671865/1,205 of 1,215 · fleet 66.295394/4,142 of 4,171
(`<D>_merged_2026-09-08/summary.json`). Full table:
`implementation/PLAN_eu-recut-95pct-2026-09-08.md` §8, T08 entry.

### 2.2 What the viewers on disk show *today* (what you are looking at)

| District | Viewer file date | Divided ("ruled") | Undivided ("massing_box") | Note |
|---|---|---:|---:|---|
| Madrid | 2026-09-08 04:35 | 1,038 | 143 | current |
| Lyon | 2026-09-07 20:50 | 459 | 51 | current — your four screenshots predate it |
| London | 2026-09-07 20:51 | 692 | 49 | current |
| **Bologna** | **2026-09-07 08:36** | **552** | **664** | **stale** — rebuilt Bologna has 951 / 260 |

Fleet in the viewers today: 2,741 divided of 4,186 (65.5 %). After the Bologna regeneration: about 3,140
(75.0 %). The gap between those two numbers is purely a stale file.

### 2.3 Why the undivided ones are undivided — the 289 "rule refused" split

Measured on the layout payload re-emitted on 2026-09-08 (Madrid, London, Bologna; Lyon's payload is stale):

| Reason (a plate failing two checks is counted once, under the first listed) | Madrid | London | Bologna | What it means |
|---|---:|---:|---:|---|
| `C10` — a flat pinched narrower than 2 m | 38 | 3 | 40 | shape rule, soft |
| `C11` — a flat too slender (ribbon, aspect > 2.5) | 13 | 2 | 106 | shape rule, soft |
| `C6` — under 2.5 m of outer façade | 2 | 0 | 2 | shape rule, soft |
| `C5` — hole / flat-in-flat / outline > 40 points | 5 | 0 | 24 | topology, hard |
| `C4` — flat in two pieces or overlapping | 8 | 0 | 3 | topology, hard |
| more than 12 flats per floor declared | 9 | 7 | 0 | cap in the engine |
| **Total** | **75** (of 1,175) | **12** (of 706) | **175** (of 1,211) | |

(Madrid's manifest labels 3 of its 75 as "no dwelling count in the data". Lyon: 25 rule-refused and 25 with
no dwelling count, from the manifest; its per-check split is not on disk because its payload is stale.)

Bologna is the outlier because its blocks are large, deep and non-convex: 106 of its 175 refusals are the
ribbon rule alone. These are **rule refusals, not bugs**: the cutter found a cut, the seven checks rejected
it, and the engine — by design — then writes one zone per floor rather than a cut it cannot certify.

Evidence: `outputs_3D/eu_{ES-MAD-BERRUGUETE,GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}_data/layouts/*.json`
(`fallback_reason`); `EU-11/<D>_final_2026-09-07/<d>_manifest.csv` (`geometry_outcome`);
`outputs_3D/eu_*_data/buildings.csv` (`layout_state`); `STATE_european_locations_v5.md` §8
(`FINDING 261`, `D-EU-110`).

---

## 3. Why 95 % was not reached — three separate walls, only one of them ours to move

| Wall | Size | Whose it is | Can it move? |
|---|---:|---|---|
| **A. Never simulated — missing data.** 536 London footprints have no energy certificate on file (418) or one whose age band spans two building periods (362 before recovery), 11 have no storey count. Madrid 19, Lyon 21, Bologna 9 are census / IDF-assembly gaps. | 585 | the data | **No** without inventing ages. You already ruled this (`D-EU-101`, accept the ceiling, no general imputation). The London terrace-neighbour inheritance (`D-EU-108`) already recovered 255 — that is what moved the ceiling from 82 % to 86 %. |
| **B. Simulated, cut thrown away by the vertex bug.** | 184 | our code | **Yes.** The ring cleanup fixed 1,055 of 1,239. The 184 left carry a vertex the cleanup refuses to drop (area budget 1 × 10⁻⁶) or a defect on a *cut* edge rather than the footprint. Second pass = measure those 184, widen the budget or clean after the cut too. |
| **C. Simulated, rules refused the cut.** | 289 | the rules you froze | **Only by ruling.** The seven checks were frozen on 2026-09-02 and the aspect limit 2.5 was closed as an accepted residual on 2026-09-08 (`D-EU-110`). |

**Arithmetic.** 95 % of the 3,601 simulated = 3,421 divided. Today 3,128. Need **293 more**. Wall B alone
gives at most 184. So 95 % of simulated needs at least ~110 from wall C, i.e. a decision on the soft
checks (`C10`, `C11`, `C6` = 206 buildings in the three re-emitted districts, about 15 more in Lyon).

**95 % of the whole stock (3,977) is impossible**: even with every simulated building divided, 3,601 / 4,186
= 86.0 % is the ceiling set by wall A.

---

## 4. The one decision that unlocks 95 % of simulated (D-EU-111, recommended)

**Add a "best effort" tier for the three *shape* checks only.** When the best candidate cut fails only
`C10` (pinch), `C11` (ribbon) or `C6` (façade length) — never `C1`, `C3`, `C4`, `C5` — emit that cut anyway,
mark the building `DWELLING_LAYOUT_EMITTED_BEST_EFFORT`, and show an amber badge "divided, shape check
failed: C11" in the viewer. The thermal model gains real flats with real party walls; the only cost is a
flat that is thinner or has less façade than the rule likes.

- This is the same move you already took once: `D-EU-93` stopped judging `C11` on undivided plates and the
  fleet went from 85.6 % to 92.5 % passing with zero regressions.
- Expected gain: about 220 buildings (Madrid 53, London 5, Bologna 148, Lyon ~15) → fleet divided ≈
  3,350, plus whatever the wall-B second pass recovers (up to 184) → **≈ 3,450–3,530 of 3,601 = 96–98 %**.
- Not recommended: lowering the declared flat count until the check passes (the engine deliberately never
  reduces a declared dwelling count), or raising the 12-per-floor cap (16 buildings, gain too small).
- Explicitly *not* touched: `MAX_FLAT_ASPECT = 2.5` stays. The check still runs and is still reported; it
  stops being a veto on emission. GSSCanada asked that the threshold not move, and it does not.

Alternative (a): accept 86.9 % and ship. Alternative (b): best-effort tier for `C11` only (≈ 125 buildings,
≈ 93 %). Recommend the full soft-check tier.

---

## 5. The clean pipeline — six steps, one per artifact, with today's status

Every step reads the previous step's dated folder and writes its own. Nothing is edited in place; a
superseded folder is left read-only.

| # | Step | Command / script | Writes | Done means | Status 2026-09-08 |
|---|---|---|---|---|---|
| 1 | **Prepare** — classify, cut every floor, write one IDF per building | `scripts/run_eu_s2_district_campaign.py prepare` (engine `openubem/geometry/european_nocore.py`, ring cleanup in `scripts/run_eu_s2_campaign.py`) | `EU-11/<D>_final_<date>/` — `idfs/`, `schedules/`, `prepared_buildings.csv`, `<d>_manifest.csv`, `summary.json` | `population_prepared` stated as "N of M attempted", blockers named, `geometry_outcome` counted | ✅ all four (`_final_2026-09-07`) |
| 2 | **Simulate** — one Speed array per district, every changed IDF | `sbatch --array=1-N%32 --time=7-00:00:00 -p ps …` | `/speed-scratch/o_iseri/fleets/EU11_<D>_{final,delta}_2026-09-07/out/` | `sacct` shows 0 RUNNING / 0 PENDING, FAILED classified into the 4 known signatures | ✅ Madrid, Lyon, London · ⏳ **Bologna delta job 1311708: 485 done + 8 failed of 703, 32 running, 31.7 min/task → ≈ 3.5 h from 10:49 EDT** |
| 3 | **Harvest + merge** — pull results, join to the population, restate the EUI | `python scripts/cluster/harvest_eu11_merged.py --district <D>` | `EU-11/<D>_merged_<date>/summary.json` + manifest with `eui_source` | pooled EUI quoted as "N of M", pending rows blank | ✅ Madrid, Lyon, London · ⏳ Bologna after step 2 |
| 4 | **Viewer + building table** | `importlib`-load `scripts/generate_eu_3d_viewers.py`, `build_district('<D>')` | `openubem/outputs/3D/` → mirrored to `outputs_3D/eu_<D>_viewer.html`, `_data/buildings.csv`, `sources.json` | feature count = manifest rows; EUI non-null = `n_with_eui`; mirror byte-identical | ✅ Madrid, Lyon, London · 🔴 **Bologna stale (2026-09-07 08:36)** |
| 5 | **Layout payload for GSSCanada** — one JSON per building, per storey zone list | `scripts/emit_eu11_layout_sidecars.py` against the merged/final tree | `EU-11/<D>_layouts_<date>/` → installed into `outputs_3D/eu_<D>_data/layouts/` | file count = simulated count; 0 files with `has_unconditioned_core: true`; `circulation_area == 0` everywhere | ✅ Madrid 1,175 · ✅ Bologna 1,211 · ⚠ **London 451 of 706** (emitter skips the 255 recovery rows, `emit_eu11_layout_sidecars.py:207`) · 🔴 **Lyon stale 2026-09-01, corridor-era** (not needed by 4J) |
| 6 | **Audit + hand-off note** | the five-line audit (below) + a dated message in `messages_GSSCanada/` | one message per delivery, answering their open questions | every line pass, per district | ⬜ not written for this delivery |

### 5.1 Four small code defects that make the pipeline look worse than it is

| # | Defect | Where | Fix (Sonnet, one task each) |
|---|---|---|---|
| a | Viewer shows the **old engine's refusal reason** (`L_SHAPE_DECOMPOSITION_FAILED` etc.) for undivided buildings | `generate_eu_3d_viewers.py:854, :984` | show the current `geometry_outcome` / `fallback_reason` from the `_final_` manifest instead (= `D-EU-109` T05, spec already written) |
| b | Viewer **copies the EU-17 layout side-files** (2026-09-01) into `outputs_3D/…/layouts/` on every regeneration, overwriting the current payload | `generate_eu_3d_viewers.py:1307-1314` | copy from `EU-11/<D>_layouts_<latest>/`; never from EU-17 |
| c | Layout emitter **skips the 255 London recovery buildings** (`_gb_rows` has no record for them) | `emit_eu11_layout_sidecars.py:207` | read rows from `GB-LDN-STDUNSTANS_recovery_2026-09-07/prepared_buildings.csv`, not from `_gb_rows` |
| d | `sources.json` `layout_counts` counted from the viewer, so it disagrees with the side-file count | `generate_eu_3d_viewers.py:1337` | count the installed side-files; state "N of M simulated" |

Plus one housekeeping line: `plans3D/index.html` still points at the `_r5` pages while `_r6`
(2026-09-07) pages exist beside them.

### 5.2 The five-line audit, per district, before anyone says "done"

1. `EU-11/<D>_merged_<date>/summary.json` — pooled EUI **and** "N of M".
2. Merged manifest — rows and non-null-EUI count agree with line 1.
3. Viewer — feature count and EUI count agree with line 2, built from the same tree.
4. `outputs_3D` mirror — byte-identical to `openubem/outputs/3D/` (viewer, `buildings.csv`, `layouts/`).
5. Layout payload — file count = simulated count; 0 cored; `sum(floors[].dwelling_count)` = zones in IDF.

Report pass / fail per line with the measured values. Never "audited and correct".

---

## 6. What GSSCanada gets, and the answers to their two questions

**Their ask (2026-09-08 letter):** a current `layouts/` payload for **Madrid, London and Bologna** (Lyon is
their physical baseline only, never in a denominator). Madrid and Bologna are delivered; London is 451 of
706 until defect 5.1-c is fixed.

**The payload contract, per building JSON** (`outputs_3D/eu_<D>_data/layouts/<building_id>.json`):

- `floors[].dwelling_count` is the **only** authoritative per-storey number; the building total is its
  sum. `units_per_floor` is a *maximum* and must not be multiplied by `storeys` (`FINDING 266`; 1,480 of
  2,484 multi-storey buildings have a non-uniform count per storey).
- `has_unconditioned_core` is `false` and `circulation_area_m2_total` is `0` on every file (no-core regime,
  `D-EU-79`/`D-EU-80`). Verified externally by 4J: conditioned / gross area = 1.000000 on all 2,837 files.
- `fallback_reason` non-null ⇒ the building is one zone per floor; `floors[]` then carries one zone.
- Every district count is quoted as "N of M simulated", never as the residential total.

**Question 1 — `FINDING 258` (imbalanced flats), before or after the payload?** **Before, with a named
residual.** The balance gate `C12` (min/max flat area ≥ 0.50) is in the engine (`european_nocore.py`,
`MIN_SPREAD`) and the rebuilt trees the payload was emitted from already carry it. On the bench 275 of the
344 imbalanced plates were repaired; **69 plates still fail the balance gate** (Bologna 56 plates on the
rebuilt tree). Deliver that list as `affected_buildings_2026-09-07.csv` filtered to `spread < 0.50`, and
4J carries it as a declared limitation. No further re-cut is scheduled (your ruling: per-building only).

**Question 2 — `D-EU-84` (`MAX_FLAT_ASPECT` calibration), open or closed?** **Closed on 2026-09-08 as an
accepted named residual** (`D-EU-110`): the constant stays at 2.5, 81 of 550 bench plates over 57
buildings ship as an honest FAIL, and the threshold will not move for anyone. `D-EU-87` (`C10` as a real
pinch test) is implemented. Their freeze condition 2 is satisfied; they can freeze the pre-registration.

**If `D-EU-111` (§4) is taken**, tell 4J *before* the re-emission: the Madrid and Bologna populations they
would freeze against change by 53 and 148 buildings (undivided → divided). Freeze after, not before.

Evidence: `messages_GSSCanada/2026-09-08_4J_to_OpenUBEM_layout_payload_and_two_questions.md`;
`STATE_european_locations_v5.md` §8 (`D-EU-110`, `FINDING 266`); `implementation/PLAN_eu-plan-homogeneity-2026-09-07.md:295`;
`openubem/outputs/eu_evidence/EU-21/homogeneity/affected_buildings_2026-09-07.csv`.

---

## 7. Order of work from here (each line is one fresh Sonnet dispatch unless marked director)

> **Superseded 2026-09-08 (same day).** The owner accepted `D-EU-111`, authorised the wall-B second pass, and asked for neighbour imputation of the 585 never-simulated (`D-EU-112`). The order of work is now `implementation/PLAN_eu-recut-95pct-2026-09-08.md`; the list below is kept as the record of what was proposed. The per-building list of the 585 with a proposed imputed age is `debugs/never_simulated_buildings_all_districts_2026-09-08.csv` (585 rows: London 536, Lyon 21, Madrid 19, Bologna 9).

1. **Wait for Bologna job 1311708 to drain** (director, ≈ 3.5 h) → harvest → restate Bologna → regenerate
   the Bologna viewer → five-line audit. Bologna undivided 664 → 260 in the viewer.
2. **Defects 5.1-a/b/c/d** (four small edits, one Sonnet each, tests per edit) → regenerate all four viewers
   once → re-emit London layouts (706 of 706) → audit line 5 on all four.
3. **Hand-off message to 4J**: payload complete for Madrid / London / Bologna, the contract above, answers
   1 and 2, the 69-plate imbalance list.
4. **Your ruling on `D-EU-111`** (§4). If yes: one plan doc, one engine change (emit-on-soft-fail + new
   outcome token + amber badge), re-emit only the ~210 affected, **one** Speed array for them, restate,
   regenerate, tell 4J. If no: fleet stays at 86.9 % of simulated and the arc closes there.
5. **Wall B second pass** (184 buildings): measure why the cleanup left them, widen the area budget or
   clean the cut edges; same re-emit / simulate / restate loop, folded into step 4's array if both are
   taken.

Not on the list, deliberately: any attempt at the 585 never-simulated buildings (data wall, ruled), any
full-fleet re-cut (ruled out), and any change to `MAX_FLAT_ASPECT` or the seven checks' values.

## 8. Fleet-wide scan — every undivided building, all four neighbourhoods (added 2026-09-08, on request)

The Lyon screenshots were examples; this section is the scan of **every simulated residential building in
all four neighbourhoods** for the same defect (a floor emitted as one undivided box). The building-by-building
list is `debugs/undivided_buildings_all_districts_2026-09-08.csv` (473 rows; columns: district, building id,
IDF stem, type, geometry outcome, refusal reason, floor area, defect class).

Source: `prepared_buildings.csv` of the `*_delta_2026-09-07` trees (latest cut, after the ring-vertex cleanup),
refusal reasons from `*_layouts_2026-09-08/layouts/**/*.json`.

| District | Simulated | Divided | Vertex bug (B) | Rule refused (C) | Refusal reasons (C) |
|---|---|---|---|---|---|
| Madrid  | 1,175 | 1,033 (87.9 %) | 67 | 75  | C10 36 · C11 13 · C4 8 · C5 5 · C6 4 · density>12 9 |
| Lyon    |   509 |   459 (90.2 %) | 25 | 25  | reasons not yet exported (no 2026-09-08 side-cars for Lyon) |
| London  |   706 |   685 (97.0 %) |  7 | 14  | density>12 7 · C10 3 · C11 2 · 2 not exported |
| Bologna | 1,211 |   951 (78.5 %) | 85 | 175 | C11 109 · C10 40 · C5 24 · C6 8 · C4 3 |
| Fleet   | 3,601 | 3,128 (86.9 %) | 184 | 289 | |

(Combined refusals such as `C6_C10` are counted once, under the first listed check.)

Reading it: the defect is the same everywhere, only the mix changes. Bologna is the worst because its plates
are long and narrow, so the aspect check (C11, flat longer than 2.5 × its width) refuses one plate in nine.
Madrid fails mostly the pinch check (C10, a flat narrower than 2 m somewhere). London is almost clean. The
two Lyon refusal reasons are not in this file because Lyon's side-cars have not been re-emitted since the
repair; they will appear when step 2 of §7 (re-emit all four districts) runs.

Nothing in this scan changes the conclusions of §3–§4: wall B (184) is a second cleanup pass, wall C (289)
is the D-EU-111 decision, and the 585 never-simulated buildings are outside the scan because they have no
geometry to divide.

🔴 **Superseded 2026-09-09 (T08 of `implementation/PLAN_eu-recut-95pct-2026-09-08.md`).** Wall B (184) shipped
as a named, honest residual — no remedy cleared any of it (`FINDING 267`, ruled at `CP-1`). Wall C (289
rule-refused) is no longer undivided as a block: `D-EU-111`'s best-effort tier recovered 202 of a 204-building
target (T07/`CP-3`/`CP-3c` manifest-token count; Lyon short 2, `FINDING 269`). The 585 never-simulated are no
longer all outside the scan: `D-EU-112`'s neighbour-imputation ladder recovered 576 of 585 and entered them
into the campaign (T04); 9 remain out (7 already-complete-data engine-build failures, 2 London buildings
excluded by the owner). Full per-district table: `implementation/PLAN_eu-recut-95pct-2026-09-08.md` §8, T08
entry.
