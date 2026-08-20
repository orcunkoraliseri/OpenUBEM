# PLAN — the board's "17 ready", triaged and finished

**Slug:** `board-17-ready-2026-08-19`
**Date:** 2026-08-19
**Author:** director (this session). **Executor:** fresh Sonnet session(s).
**User authorisation, verbatim (2026-08-19):** *"et apres continue taches se sont presente comme
'17 ready' dans le document board … finissent toutes"* — after `PLAN_open-57-and-58_2026-08-19.md`,
finish everything the progress board shows as **ready**.

**Board:** `claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639`
(local copy: `scratchpad/board.html`). Its script maps status `open` → the visible label
**`ready`** (`board.html:926`), so **"17 ready" is exactly the 17 rows carrying `"open"`**.

**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — **23 live / 35
struck / 58 total, next free `OPEN-59`.**

---

## 🔴 The finding that shapes this plan — read before anything else

**The board and the register disagree, and the register is right.** Mapping all 17 rows onto the
register gives:

| board rows | verdict |
|---|---|
| **13** | 🟢 **stale board bookkeeping.** Their item was closed, or **you already ruled on them**, and nobody updated the board's status. |
| **3** | 🔵 **genuinely open work**, each mapping to a live register item: **OPEN-35**, **OPEN-47**, **OPEN-29**. |
| **1** | 🟡 **in flight now** under `PLAN_open-57-and-58_2026-08-19.md` (OPEN-57 + OPEN-58). |

⚠️ **This must not be waved through as a bookkeeping detail.** The board's own history already
records this failure mode twice — *"our own summary table does not reliably say what has already
been measured"*, and an executor once re-ran an item that had been closed hours earlier. **T01
exists to make sure this plan does not become the third instance.** Nothing is re-run on the
strength of the table below until T01 has checked it against the register.

**Director's provisional mapping — to be VERIFIED by T01, not trusted:**

| row | board title (short) | maps to | provisional verdict |
|---|---|---|---|
| `NEW` | 158 is an average of averages | **OPEN-43** | closed+retired 2026-08-12; you ruled pooled **157.1** adopted → `decided` |
| `NEW2` | 106 hidden test failures | **OPEN-44** | struck → `done` |
| `N6` | completion records: six, not one | **OPEN-36** | closed+retired 2026-08-13 → `done` |
| `N10b` | a completed task whose code was never in the project | **OPEN-36** | same item → `done` |
| `N10` | elevators are not the tenth end-use | **OPEN-46** | closed 2026-08-18, and **reversed** — the energy was there all along → `done` |
| `O2` | the headline run cannot be reproduced | **OPEN-48** | closed 2026-08-18, re-run made, effect < 0.08 % → `done` |
| `Q3` | the tests quietly edit a stored dataset | **OPEN-50** | struck → `done` |
| `T7` | the data-centre fix, waiting on you | **OPEN-55** | 🔴 **you ruled Option B+ on 2026-08-19 and it is in the code** → `decided` |
| `U6` | still waiting on you | **OPEN-55** | same ruling → `decided` |
| `V7` | two closures waiting on you | ruling **R2** | executed 2026-08-19 → `decided` |
| `W11` | four closures waiting on you | ruling **R2** | executed 2026-08-19 (OPEN-42, OPEN-11, OPEN-07, OPEN-08) → `decided` |
| `W9` | how exposed the evidence is, in GB | ruling **R3** | executed 2026-08-19 — 323 files / 12 MB into the repo → `done` |
| `W6` | a big number that must not be quoted | — | measurement complete, no live item; the +48 % was confounding → `done` |
| `N05b` | two guesses for the same missing storey count | **OPEN-35** | 🔵 **genuinely open** — measured, **not fixed** |
| `N3` | the literature check came back worse than empty | **OPEN-47** | 🔵 **genuinely open** — source found, but our rule **drops the source's floor-count condition** |
| `W8` | eight inherited defects, finally decidable | **OPEN-29** | 🔵 **genuinely open** — the adoption material now exists; it needs a ruling |
| `X10` | two new problems found by accident | **OPEN-57/58** | 🟡 in flight |

---

## 2. Hard rules for the executor

🔴 **Read these before T01.**

1. 🔴 **NO CLUSTER. NO FLEET RUN. NO SIMULATION.** Nothing in this plan needs the cluster, and
   nothing in it authorises one. No `ssh`, no `sbatch`, no `srun`, no EnergyPlus over the network.
   T04 is the only task that may run EnergyPlus **locally**, and only on the bounded sample §4.4
   pins.
2. 🔴 **Never restate a fleet figure.** The adopted baseline is 157.1 kWh/m² pooled and it is **not
   in scope**. No task here may re-derive it, re-publish it, or supersede it. If a task's own
   numbers seem to bear on it, **say so and stop** — that is a director decision.
3. 🔴 **Never run a git write command.** Read-only git only.
4. ⚠️ **Do not edit the register, the board, or `docs/PROJECT_CHECKLIST.md`.** The director makes
   every edit to all three. You write measurement docs and **recommend**.
5. ⚠️ **Do not open or close register IDs.** Executors do not do either.
6. ⚠️ **Diagnose before you remediate.** T01–T03 are measurement tasks: no fixes. T04 is the only
   task that changes production code, and §4.4 bounds it.
7. ⚠️ **Real interpreter is `.venv/Scripts/python.exe`**; bare `python` is a Windows Store stub. Set
   `PYTHONIOENCODING=utf-8` on anything printing non-ASCII.
8. ⚠️ **No `.py` under `docs/`.** Figures go **flat** in `openubem/outputs/`.
9. ⚠️ **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, or anything under
   `docs/docs_main/`, `docs/docs_stepN/`, `docs/docs_DONE/`.
10. ⚠️ Default to no code comments. **Stop and ask on spec ambiguity; never invent.**

---

## 3. File layout

**Created:**

| path | task |
|---|---|
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_board-17-ready_triage.md` | T01 |
| `openubem/outputs/comparisons/board17_row_to_register.csv` | T01 |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-29_signature-recheck.md` | T02 |
| `scripts/analysis/open47_floorcount_condition_2026-08-19.py` | T03 |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-47_floorcount-condition.md` | T03 |
| `openubem/outputs/comparisons/open47_floorcount_condition.csv` | T03 |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_fallback-agreement.md` | T04 |
| `tests/test_storey_fallback_agreement.py` | T04 |

**Modified — T04 only:** the production module that carries the storey fallback, and only the one
function §4.4 names. **Nothing else in `openubem/` may change.**

---

## 4. Dependency decisions (pinned — do not re-litigate)

**4.1 — The register is the authority, the board is a view of it.** Wherever the two disagree, the
register wins and the **board** is what gets corrected. No item is re-opened because a board row
still says `ready`.

**4.2 — A stale row is closed by re-statusing it, not by re-doing the work.** For each of the 13,
the deliverable is **a citation** — the register line, the ruling date, or the closure record that
makes the row stale. 🔴 **A row whose staleness you cannot evidence is NOT stale**: mark it
`UNRESOLVED` and it goes to the director. Guessing here is the exact failure this plan exists to
avoid.

**4.3 — OPEN-47's open question is the floor-count condition, not the citation.** The citation
question is **settled**: the thresholds trace to **Chen, Hong & Piette (2017), _Applied Energy_
205, 323–335, Table 1**, director-verified from the PDF and Crossref-checked. The 2026-08-19 sweep
also showed the thresholds explain **zero** of the residual fine-classification error. **What keeps
it open is one thing:** the source's rule is *area **AND** floor count* (`<2322 m² and ≤3 floors`)
and our implementation **keeps the area test and drops the floor-count test**. T03 measures that
divergence and nothing else.

**4.4 — OPEN-35's remedy is agreement, and it is bounded.** The defect is that the archetype is
chosen at the **group-median storey count** while the geometry is built at **1 storey**. The fix is
to make both consume the **same** fallback. Pinned bounds:

- **Change the fallback that is wrong, not both** — the geometry side is the one that ignores the
  available median. Cite the DESIGN or the existing measurement before choosing; if neither
  settles it, **STOP and quote the conflict**.
- 🔴 **The 2026-08-19 census is the scope: 11 buildings of 1,031**, not ~1,031. For the other 1,020
  both fallbacks already return `1`, largely because two NYC cells carry **no storey data at all**.
  **A fix that changes more than 11 buildings' geometry is out of scope — stop and report it.**
- 🔴 **No fleet re-run and no re-publication.** Measure the impact on the 11 from **existing**
  artifacts and, if a local EnergyPlus run is needed, on **those 11 buildings only**, in
  **per-building working directories** (OPEN-58's defect (a) — never a shared dir), reading EUI
  with production's `parse_building()` / `total_eui_kwh_m2`, **never** a local formula
  (OPEN-58's defect (b)).

**4.4a — DIRECTOR RULING, 2026-08-19: the ceiling of 11 was wrong; it is 21.** T04 stopped at
§4.4's ceiling and reported two candidate scopes measured fleet-wide before implementing
anything. That was the correct call and the ceiling did its job — but the number it was
guarding was itself too small, and the overrun is a census error, not a wrong diagnosis.

- **Scope A (naive — geometry always takes the archetype's group-median fallback): 509 buildings.
  REJECTED.** It changes buildings whose archetype rule never consumed an imputed level count, so
  it is not the agreement fix; it is a different, larger intervention.
- **Scope B (principled — change only where the fired archetype rule actually consumed the imputed
  levels): 21 buildings. ADOPTED.** Director-verified independently from
  `openubem/outputs/comparisons/open35_fallback_agreement_scope.csv`: 21 rows, **all 21 carrying
  `levels_source = GROUPMEDIAN_LEVELS_MED`**, split `MidriseApartment` 8 / `HighriseApartment` 3 /
  `LargeHotel` 10, across nyc_centre 8, austin_centre 5, nyc_urban 5, la_urban 3. The 2026-08-19
  census's 11 are a **strict subset** of these 21 (verified by set containment, not by count).
- **Why the census said 11.** It scoped itself to apartment archetypes. The other 10 are
  `LargeHotel` under `RULE_LODGING_TIER`, which consumes imputed levels through the **identical**
  mechanism. Excluding lodging was an artifact of how the census was written, not a property of the
  defect. The defect's true population is every building whose archetype rule consumed
  `GROUPMEDIAN_LEVELS_MED` — and that is 21.

🔴 **Revised bound: a fix that changes exactly the 21 rows flagged `changed_scope_b` is in
scope. More than 21, or any row whose `levels_source` is not `GROUPMEDIAN_LEVELS_MED`, is out of
scope — stop and report.** Everything else in §4.4 stands unchanged: geometry is still the side that
moves, still no fleet re-run, still no re-publication, still per-building working directories and
production `parse_building()` for any EUI.

**4.5 — OPEN-29 is a ruling, not an implementation.** T02 only **re-derives the evidence**; the
adopt/retire decision is the director's and is taken outside this plan. **Do not strike, adopt or
retire any `E-LA-nn` ID.**

**4.6 — Independent re-derivation, not re-reading.** Where a task checks a previous task's number,
compute it from the **raw artifact**, not from the doc that reported it. This arc has caught three
wrong claims that way and zero by re-reading reports.

---

## 5. Facts with line citations

**5.1** The board's label map: `labels={done:"done",decided:"decided",partial:"in progress",
open:"ready",blocked:"blocked"}` — `scratchpad/board.html:926`. The tally that produces the visible
counts is `board.html:930`. **`ready` is the display name of status `open`.**

**5.2** Register §1 table body and the programmatic recount: `scripts/analysis/open_register_recount_2026-08-18.py`
— current output **23 live / 35 struck / 58 total, OPEN-01…OPEN-58, none missing, none duplicated,
next free OPEN-59**.

**5.3 OPEN-29's adoption table** — register §-section at line **1830**, amendment of 2026-08-18
(X07). Verdicts to re-derive: **E-LA-15, E-LA-18, E-LA-19, E-LA-30** = no observable signature in
8,160 buildings; **E-LA-16** = 3 families, max 1 building (0.01 %), all Warning; **E-LA-17** = 16
buildings (0.20 %), *the identical population as OPEN-09/OPEN-56*; **E-LA-06** = 32 buildings
(0.39 %), inside OPEN-18; **E-LA-33** = storey matching inert for **93.32 %** (497 `applied` of
7,442), inside OPEN-10. ⚠️ The amendment states its own limits: absence in `.err` is evidence about
the `auto` fleet at HEAD, **not proof of repair**, and **E-LA-30 / E-LA-33 are not visible to
`.err` at all**. Evidence files: `openubem/outputs/comparisons/open09_fleet_err_taxonomy.csv`,
`open10_storey_expressibility_fleet.csv`.

**5.4 OPEN-35** — register §-section at line **2872**; the 2026-08-19 census and intervention are
in `extra/MEASUREMENT_open-35_storey-intervention.md`, authoritative output
`open35_storey_intervention_results_v2.csv` (the earlier `_results.csv` is **superseded and must
not be cited**).

**5.5 OPEN-47** — register §-section at line **5574**; the 2026-08-19 de-scoping amendment, and
`extra/MEASUREMENT_open-47_threshold-sensitivity_2026-08-19.md`,
`openubem/outputs/comparisons/open47_threshold_sweep.csv`,
`scripts/analysis/open47_threshold_sweep_2026-08-19.py`.

**5.6 OPEN-58's two defects, which bind T04** — `scripts/analysis/open56_zone_volume_experiment.py:150`
(`run_ep`, shared-dir cross-contamination under `-x`) and `:186-187` (EUI as Total Site Energy ÷
Total Building Area). Production EUI is `openubem/results/parser.py:498`.

---

## 6. Task list

### T01 — Triage all 17 board rows against the register

**What.** For each of the 17 rows, resolve it to a register ID (or to "no item"), state whether that
ID is **live or struck**, and assign one of: `STALE-CLOSED` (its item is struck), `STALE-RULED`
(the user ruled and it was executed), `OPEN` (a live item with work remaining), `IN-FLIGHT`, or
`UNRESOLVED`. Write `openubem/outputs/comparisons/board17_row_to_register.csv` with columns
`board_row, board_title, register_id, register_state, verdict, evidence`.

**Why.** The board is the user's monitoring surface and it currently overstates the work remaining
by roughly four to one. Correcting it is most of what "finish the 17" actually means.

**How.** The 17 rows are the ones whose status literal is `"open"` in `board.html`'s `WP` array.
Use the register's §1 table and §-sections; the recount script gives live/struck definitively.

**How to test.** Every row's `evidence` cell must be a **file path with a line number, or a dated
ruling**. §4.2 governs: no evidence → `UNRESOLVED`, not `STALE`. Report the counts by verdict, and
report **any disagreement with the director's provisional table above** — that table is a
hypothesis, and finding it wrong is a result, not a problem.

### T02 — OPEN-29: re-derive the four zero-signature verdicts

**What.** Independently re-derive, from `open09_fleet_err_taxonomy.csv` and
`open10_storey_expressibility_fleet.csv`, that **E-LA-15, E-LA-18, E-LA-19 and E-LA-30** have no
signature across the 8,160 buildings, that **E-LA-16** is one building, and that **E-LA-17's
population is identical to OPEN-09's** — the last being the load-bearing one, because it is the
claim that would make adopting E-LA-17 a double-count.

**Why.** These six verdicts are about to carry a retirement ruling. They have been computed once, by
one task, and never checked.

**How.** From the CSVs, not from the amendment's prose (§4.6). For E-LA-17, compare the two
populations **as sets** and report the symmetric difference, not just the counts — two 16-building
sets are not the same set.

**How to test.** Report each of the eight verdicts as **confirmed / contradicted / not derivable
from these artifacts**. ⚠️ **`not derivable` is expected for E-LA-30 and E-LA-33** — §5.3 says
`.err` cannot see them — and reporting it as confirmed would be wrong. **Recommend; do not rule.**

### ⏸️ CP-1 — STOP AND REPORT (after T01 + T02)

Report the triage counts, every `UNRESOLVED` row, and the eight re-derivations. **The director rules
on OPEN-29 and rewrites the board here.** Then continue to T03.

### T03 — OPEN-47: size the floor-count divergence

**What.** Our office size-tier rule tests **area only**; the source (§4.3) tests **area AND floor
count ≤ 3**. Measure how many buildings change tier when the floor-count condition is added, across
the fleet's existing classification artifacts.

**Why.** It is the single stated reason OPEN-47 is still open. Once it is sized, the item is either
closable or has a defined remedy — and either outcome ends it.

**How.** Locate the threshold test in the classifier, then apply the source's two-condition rule to
the existing per-building attributes. **No re-classification run, no simulation.** Report the count
and the direction of every change, plus how many affected buildings have **no floor count at all** —
that population cannot satisfy an AND rule and is the interesting case.

**How to test.** Pre-register your expected count **before** computing it, and report both. Report
the overlap with OPEN-35's 11 buildings — the two items touch the same fallback and may interact.
⚠️ **If the answer is "zero buildings change", say that plainly first** — a clean negative closes the
item and this arc has produced several.

### T04 — OPEN-35: make the two fallbacks agree

**What.** Implement the agreement fix pinned in §4.4, with tests.

**Why.** It is the last thing OPEN-35 needs. The mechanism is proved, the population is counted at
11, and the intervention has already been run and measured.

**How.** §4.4's bounds are hard. Per-building working directories, production `parse_building()` for
any EUI, and **no fleet run**.

**How to test.** `.venv/Scripts/python.exe -m pytest -q tests/` — **the full suite must stay green**
(baseline 1885 passed / 55 skipped); any change in that count is a regression, report it rather than
explaining it. New tests must cover: both fallbacks return the same value for a building with no
storeys and no height; a building **with** storey data is unaffected; and a cell with **no storey
data at all** still returns 1 from both. Then report the changed-building count against §4.4's
ceiling of 11.

### T05 — OPEN-35: wire the agreement fix into the production call sites

**What.** Make T04's fix actually reachable. `derive_num_floors()` gained three keyword-only
parameters, but no call site passes them, so as landed the fix changes **nothing** in a real build,
parse or aggregate. Wire it at the three call sites in `openubem/idf/builder.py`,
`openubem/results/parser.py` and `openubem/results/aggregator.py`.

**Why.** T04 stopped at §3's file-layout bound ("nothing else in `openubem/` may change") and
flagged this itself, correctly. But an unreachable fix is not a fix — it is a function that passes
its own unit tests and never runs. This task closes that gap and nothing else.

**How.** Pass the same group/global level medians the classifier itself uses — do not recompute
them by a second route, and do not invent a new source for them. If a call site genuinely cannot
reach those medians, **STOP and quote the obstacle** rather than approximating.

🔴 **Hard bound, same as §4.4a.** After wiring, re-run the fleet-wide scope verification and
prove by **set membership** that the changed set is still **exactly the 21** rows flagged
`changed_scope_b`. More, fewer, or different membership means the wiring is wrong — stop and report
the actual set.

🔴 **No fleet re-run, no re-publication, no restatement of any fleet figure.** The adopted
baseline was computed before this fix; whether it gets restated is the **user's** decision and is
explicitly out of scope here. Record that it is now stale with respect to 21 buildings; do not act
on it.

**How to test.** The full suite must stay green (baseline 1,885 + this arc's new tests — the
director runs it; run only the narrow modules the call sites touch and quote their output). Add a
test proving the wiring is live: a building that reaches a call site with no levels and no height
gets the median-derived floor count, not 1.

### T06 — OPEN-35: close the parser gap the wiring opened

**What.** Widen the `manifest_row` column copy in `openubem/results/__init__.py`
(`aggregate_results()`, the hardcoded 4-column copy at `:145-148`) so `parse_building()` can reach
`archetype_source` and the fleet level medians, then wire `openubem/results/parser.py`'s
`derive_num_floors()` call the same way T05 wired the other two.

**Why.** T05 wired 2 of 3 call sites and stopped at a correctly-quoted obstacle: `parse_building()`
never receives the fleet gdf, and its only production caller copies four hardcoded columns that do
not include `archetype_source`. 🔴 **Stopping there is not a safe resting place.** With the
builder wired and the parser not, the build path now derives one floor count for those 21 buildings
and the parse path derives another — which is **exactly the two-paths-disagree defect OPEN-35
exists to remove**, recreated in a new place. Half-wiring converts one disagreement into a
different one rather than closing it.

**How.** Widen the copy by the **minimum** columns needed. Do not restructure `aggregate_results()`,
do not change `parse_building()`'s signature beyond the keyword-only parameters T04 already
established, and do not touch `derive_num_floors()`'s logic or `building_classifier.py`. Reach the
medians by the classifier's own route (`_build_levels_median_lookup()` / `_normalise_use_class()`),
as T05 did — never by a second, parallel computation.

🔴 **Hard bound, unchanged from §4.4a.** After wiring, prove by **set membership** — not by count
— that the parser path changes exactly the same **21** osm_ids as the builder and aggregator paths.
Three-way agreement on the same 21 is the pass condition. Any divergence between the three means the
wiring is wrong: stop and report the actual sets.

🔴 **No fleet re-run, no re-publication, no restatement of any fleet figure.**

**How to test.** Extend `tests/test_open35_wiring.py` to cover the parser path, and add a test that
**pins the three-way agreement** so a future change to one path cannot silently desynchronise it
from the others. Run the narrow modules and quote output verbatim; the director runs the full suite.

### ⏸️ CP-2 — STOP AND REPORT (after T04)

Suite count, changed-building count, OPEN-47's divergence size, and anything found that neither item
predicted.

---

## 7. Stop-and-report points

| id | after | gate |
|---|---|---|
| **CP-1** | T01 + T02 | Is the 13/3/1 triage right? Any `UNRESOLVED`? 🔴 **Director rules OPEN-29 and rewrites the board here.** |
| **CP-2** | T04 | OPEN-35 fixed within its 11-building ceiling, suite green, OPEN-47 sized. |

---

## 8. Progress log

*(Executor appends one entry per completed task, in order. Format:
`#### TXX — <title> — completed YYYY-MM-DD` followed by **Artifacts** / **Deviations** /
**Test status** / **Notes**.)*

#### T01 — Triage all 17 board rows against the register — completed 2026-08-19

**Artifacts:** `openubem/outputs/comparisons/board17_row_to_register.csv`;
`extra/MEASUREMENT_board-17-ready_triage.md`.

**Deviations:** None from the task's method. Result deviates from the director's provisional table:
**12 stale / 4 open / 1 in-flight, not 13/3/1.** W6 ("a big number that must not be quoted") is
wrongly bucketed in the provisional table as a closed, no-live-item measurement — it is word-for-word
OPEN-35's own 2026-08-18 X04 finding (same +47.9%/48% figure, same nyc_suburban 1,589 confound, same
4-lower/4-higher split), and OPEN-35 is live, not struck. Reclassified OPEN, folds into OPEN-35.

**Test status:** N/A (measurement task, no code changed). Every one of the 17 rows resolved to a
register ID or named ruling with a file path + line number or a quoted dated ruling — 0 `UNRESOLVED`.

**Notes:** Two "STALE-RULED" rows (T7/U6 → OPEN-55; W9 → OPEN-53/ruling R3) carry a caveat: the
specific ask the board row named has been ruled/executed, but the register item itself stays live
(OPEN-55 blocked by OPEN-57, unproven in simulation; OPEN-53 explicitly "stays open" per its own
MEASUREMENT doc). X10 (OPEN-57/58) is authorised and queued under its own named plan but that plan's
progress log is empty as of this check — "in-flight" reads as queued, not yet executing.

#### T02 — OPEN-29: re-derive the four zero-signature verdicts — completed 2026-08-19

**Artifacts:** `extra/MEASUREMENT_open-29_signature-recheck.md`.

**Deviations:** None from the task's method (re-derived from the raw CSVs and, where the CSV's own
construction was in question, from the raw `.err` files directly — not from X07/T08's prose).
Two of the eight verdicts came back different from what X07/T08 reported:
- **E-LA-16: CONTRADICTED.** Claimed "1 building." The taxonomy CSV's three coil-UA families each
  individually show `buildings=1`, but their union (verified from the raw `.err` files) is **2**
  distinct buildings (`nyc_centre/way_266170764`, `nyc_centre/way_266170765`) — exactly the failure
  mode §4.6 warns about, reading per-family counts without taking the union.
- **E-LA-17: CONTRADICTED.** Claimed "16 buildings, exact population match to OPEN-09." E-LA-17's own
  defining signature (`CalcHeatBalanceInsideSurf` Fatal in zone `LAUNDRYROOMFLR1`) has **zero** hits
  anywhere in the 8,160-building corpus, confirmed by direct string search (`"LAUNDRY"`,
  `"CalcHeatBalanceInsideSurf"` both 0/8,160) — not by the family-taxonomy regex, which is
  structurally blind to `Fatal` severity by construction (`_MSG` in
  `scripts/analysis/open09_fleet_err_taxonomy.py:38` matches only `Warning`/`Severe`). OPEN-09's own
  16-building population (`n_converge_warnings > 0`) is real and independently derivable, but E-LA-17's
  own-signature set is empty — symmetric difference is 16, not 0. "Exact population match" is not
  supportable from these artifacts.

**Test status:** N/A (measurement task). Five of eight CONFIRMED (E-LA-06, E-LA-15, E-LA-18, E-LA-19,
E-LA-33); E-LA-30 NOT DERIVABLE from these two artifacts as the plan itself expected.

**Notes:** No `E-LA-nn` ID struck, adopted, or retired — recommendation only, per §4.5. Flagging for
the director's OPEN-29 ruling at CP-1: E-LA-17 should likely be treated as unadjudicated by this
corpus (same bucket as E-LA-15/18/19's `auto`-vs-`layout_assign` evidence gap) rather than as a
settled double-count of OPEN-09; E-LA-16's cited count should read 2, not 1, wherever it is next used.

#### T03 — OPEN-47: size the floor-count divergence — completed 2026-08-19

**Artifacts:** `scripts/analysis/open47_floorcount_condition_2026-08-19.py`;
`openubem/outputs/comparisons/open47_floorcount_condition.csv` (598 rows);
`extra/MEASUREMENT_open-47_floorcount-condition.md`.

**Deviations:** None from the task's method. **Conflict found and flagged, not silently
absorbed:** §4.3 and the dispatching prompt both frame the floor-count divergence as OPEN-47's
one remaining open question, as if unmeasured. It is not — the register's own `### OPEN-47`
§-section (`INVESTIGATION_open-items-register.md:5616`) carries a 2026-08-18 amendment stating
this exact question was already measured (598 changes) and already ruled on ("Reason 1 IS
adjudicated and no longer keeps this item open... stays open on Reason 2 alone" — the citation
fabrications). The register's own §1 summary-table row (`:733`, what T01 cited as evidence for
N3) is stale and does not reflect that amendment. Recommend the director correct the §1 row.
This did not block execution: T03 still had two genuinely new questions to answer.

**Pre-registered vs. actual:** total changes **598 (predicted 598, exact match)** — 380
SmallOffice→MediumOffice, 161 MediumOffice→LargeOffice, 57 SmallOffice→LargeOffice, all
promotions, no demotions. Three hand-verified control transitions all MATCH.
**No-floor-count-at-all population: 167 / 598 (27.93%, predicted ~167, exact match)** — no OSM
`levels`, no usable `height_m`; these can never satisfy an AND rule on real evidence.
**Overlap with OPEN-35's 11 buildings: 0 (predicted 0, exact match).**

**Test status:** N/A (measurement task, no code changed).

**Notes:** This is a reproduction of already-adjudicated 2026-08-18 work, not a new unknown —
reported plainly rather than presented as a fresh finding. The two new cuts (no-floor-count
population, OPEN-35 overlap) support the existing 2026-08-12 ruling (keep area-only default)
rather than challenge it.

#### T04 — OPEN-35: make the two fallbacks agree — STOPPED AT §4.4's CEILING, 2026-08-19

**Artifacts:** `scripts/analysis/open35_fallback_agreement_scope_2026-08-19.py`;
`openubem/outputs/comparisons/open35_fallback_agreement_scope.csv` (8,160 rows);
`extra/MEASUREMENT_open-35_fallback-agreement.md`.

**Deviations:** **No production code changed. No test file written.** Per §4.4's explicit
instruction ("if your change moves MORE than 11, stop and report — that means the diagnosis
was wrong"), this task stopped rather than land a fix. Which fallback is wrong was not in
question (§4.4 already names the geometry side, `derive_num_floors()`,
`openubem/geometry/footprint.py:58-63`). Two implementations of "make it consume the same
median as `_impute_levels()`" were measured fleet-wide (8,160 buildings, existing Step-1
`01_buildings.gpkg` files, no re-classification, no simulation, no fleet re-run): a naive
version (apply the median whenever both `levels`/`height_m` are missing) changes **509**
buildings; a principled version, scoped to only where the fired archetype rule actually
consumed the imputed levels (`archetype_source` head in `_LEVELS_CONSUMING` and
`lev_src != OSM_OBSERVED`, the classifier's own internal test for this,
`building_classifier.py:635-639`), changes **21**. Both exceed the pinned ceiling of 11.
OPEN-35's own 11-building census is a strict subset of the 21 — the extra 10 are `LargeHotel`
archetypes assigned via `RULE_LODGING_TIER` (2 `austin_centre`, 8 `nyc_centre`) that the
2026-08-19 census excluded because it scoped itself to apartment archetypes
(`MidriseApartment`/`HighriseApartment`) only, even though `RULE_LODGING_TIER` uses the
identical imputed-levels mechanism.

**Test status:** `.venv/Scripts/python.exe -m pytest -q tests/` → **1893 passed, 55 skipped**
(baseline 1885 passed / 55 skipped). **Count changed — reported, not explained away per hard
rule.** No file under `openubem/` or `tests/` was touched by this task (T03 or T04), so the
+8 passed is not attributable to this task's work; `git status` shows two untracked test files
(`tests/test_semantic_unknown_bounds.py`, `tests/test_v12_ssh_stdin.py`) from the concurrently
running `PLAN_open-57-and-58_2026-08-19.md` executor, consistent with the delta.

**Notes:** Recommendation only, no ruling taken: either (1) extend OPEN-35's census to include
`RULE_LODGING_TIER` and re-set the ceiling to 21 before landing the principled fix, or (2)
scope the fix to exactly the original 11 (residential/apartment rules only) and record the 10
`LargeHotel` cases as a new, separate sub-finding rather than folding them in silently.
Changed-building count against the ceiling: **21 (Scope B) / 509 (Scope A) vs. ceiling 11 — both over.**

#### T04 — OPEN-35: make the two fallbacks agree — LANDED under director ruling 4.4a, completed 2026-08-19

**Artifacts:** `openubem/geometry/footprint.py` (`derive_num_floors()` only — production
code change); `tests/test_storey_fallback_agreement.py` (new, 7 tests);
`scripts/analysis/open35_scope_b_verify_2026-08-19.py` (fleet-wide membership
verification, calls the landed production function); addendum appended to
`extra/MEASUREMENT_open-35_fallback-agreement.md`.

**Deviations:** None from §4.4a. `derive_num_floors()` gained three optional
keyword-only parameters (`use_class`, `levels_group_median`, `levels_global_median`)
mirroring `_impute_levels()`'s own extras exactly; every pre-existing call site
(`idf/builder.py:427`, `results/parser.py:443,715`, `results/aggregator.py:145,150,155`)
still calls it positionally and is untouched — none of them supply the new keywords, so
their behaviour is byte-identical to pre-fix. `openubem/semantic/building_classifier.py`
was not modified (import-free — the Scope B gate is decoded entirely from
`row["archetype_source"]` containing a `GROUPMEDIAN_LEVELS_MED` token, which
`building_classifier.py`'s own token-assembly only ever appends under the identical
condition Scope B uses). No file under `openubem/` other than `footprint.py` was touched.

**Test status:** `.venv/Scripts/python.exe -m pytest -q tests/test_storey_fallback_agreement.py tests/test_footprint.py`
→ **28 passed**. Widened narrow check (all modules that call `derive_num_floors`,
per dispatch instruction to run only new tests plus narrowly-touched modules):
`tests/test_idf_builder.py tests/test_results_parser.py tests/test_results_aggregator.py
tests/test_builder_elevators_wired.py tests/test_parser_elevators.py
tests/test_parser_hvac_metered.py` → **157 passed, 3 pre-existing unrelated deprecation
warnings**, together with the two files above. Full `pytest -q tests/` intentionally NOT
run here per dispatch instruction (director is running it).

**Changed-building count vs. §4.4a's revised ceiling of 21:** exactly **21**, verified by
set comparison (not count) against `changed_scope_b == True` in
`open35_fallback_agreement_scope.csv` — 0 missing, 0 extra, exact membership match.
Per-cell: `austin_centre` 5, `la_urban` 3, `nyc_centre` 8, `nyc_urban` 5, matching §4.4a's
own `MidriseApartment` 8 / `HighriseApartment` 3 / `LargeHotel` 10 breakdown.

**Notes:** No local EnergyPlus run was performed or needed — the task is the agreement fix
and its tests; §4.4's EnergyPlus/per-building-working-directory bound was conditional
("if a local run is needed") and no impact re-measurement was requested for T04 itself.
Wiring the fix's new keyword arguments into the three production call sites (so a real
fleet build would actually pick up the corrected floor counts) was deliberately NOT done:
§3's file layout bounds this task to "the production module that carries the storey
fallback, and only the one function §4.4 names… nothing else in `openubem/` may change."
Flagging for the director: as landed, the fix is unit-provably correct and fleet-scope-provably
21-building, but is **not yet reachable from the live pipeline** (`idf/builder.py`,
`results/parser.py`, `results/aggregator.py` never pass the new keywords) — a follow-up
task to thread `use_class`/`levels_group_median`/`levels_global_median` through those three
call sites is needed before this fix has any effect on a real build or EUI result.

#### T05 — OPEN-35: wire the agreement fix into the production call sites — completed 2026-08-19, PARTIAL (2 of 3 sites; 1 site blocked by a genuine, quoted obstacle)

**Artifacts:** `openubem/idf/builder.py` (new `_fleet_levels_medians()`,
`_derive_num_floors_wired()`, call site at `build()` rewired); `openubem/results/aggregator.py`
(new `_fleet_levels_medians()`, `_derive_num_floors_wired()`, both call sites in
`compute_neighbourhood_summary()` rewired); `tests/test_open35_wiring.py` (new, 8 tests);
`scripts/analysis/open35_t05_wiring_verify_2026-08-19.py` (new fleet-wide set-membership
check that calls the two wired helpers directly, not `derive_num_floors()` with manually
supplied kwargs).

**Wiring mechanism (both sites, identical pattern):** the medians a call site needs were
never persisted anywhere after classification (`BuildingClassifier.classify()` computes
`levels_group_median`/`levels_global_median` locally and only writes 3 output columns —
`archetype_id`/`archetype_confidence`/`archetype_source` — not the medians themselves), and
`building_classifier.py` cannot be modified to expose them. Both wired sites therefore call
the classifier's own existing method again — `BuildingClassifier()._build_levels_median_lookup(gdf)`
and `_normalise_use_class(row)`, imported, not reimplemented — on the SAME fleet `gdf` each
call site already had in scope (`builder.py`'s `.build(self, gdf, ...)` receives it for
context discovery; `aggregator.py`'s `compute_neighbourhood_summary(results_gdf, ...)` *is*
the fleet-wide gdf). This is literally the classifier's own route re-invoked, not a second,
independently-derived one. A cheap gate (`_archetype_consumed_group_median(row)`, imported
from `footprint.py`, not duplicated) means the expensive lookup only runs for rows that can
possibly need it; every other row's call is byte-identical to the pre-T05 call.
`derive_num_floors()` itself was not touched.

**Deviation — `openubem/results/parser.py` NOT wired, STOPPED at a quoted obstacle (per the
dispatch's own explicit permission: "If a call site genuinely cannot reach those medians,
STOP and quote the obstacle rather than approximating").** `parse_building()`'s only
production caller is `openubem/results/__init__.py:aggregate_results()` (outside this
task's 3-file bound). There, `manifest_row` is assembled per-building from `sim_row` +
`idf_row` plus a **hardcoded 4-column copy** from the fleet-wide `enriched_gdf`:
`for col in ["footprint_area_m2", "levels", "height_m", "data_quality_flag"]:` — see
`openubem/results/__init__.py:145-148`. `archetype_source` is not one of the 4, so
`manifest_row` never carries the `GROUPMEDIAN_LEVELS_MED` token `derive_num_floors()`'s own
gate needs, and `parse_building(sql_path, csv_path, manifest_row)` has no other parameter
and no access to `enriched_gdf` or any fleet-wide DataFrame at all — it is a strictly
per-row function. Reaching the medians here requires either widening
`manifest_row`'s column copy or adding new parameters to `parse_building()` **and** passing
them from `aggregate_results()`, both of which mean editing `openubem/results/__init__.py`,
which T05's hard bound does not authorise ("wire exactly the three call sites"). No change
was made to `parser.py`; adding unreachable optional kwargs there would have reproduced
T04's own unreachable-fix problem in a different function, so nothing was added.
**Practical mitigation, not a full fix:** `parse_building()`'s primary floor-area path is
`resolve_simulated_floor_area()`, which reads the actual simulated geometry from
`eplusout.eio` when available; `derive_num_floors()` there is only the fallback for
missing/unreadable sim output. Because `builder.py` is wired, IDFs for the 21 buildings are
now built with the correct floor count, so `eio`-sourced floor areas already reflect the
fix for any building that simulates successfully — the un-wired parser fallback only
matters for the (currently unmeasured) subset of the 21 whose `eio` parse fails.

**Changed-building set vs. §4.4a's 21, by SET MEMBERSHIP (not count),
`scripts/analysis/open35_t05_wiring_verify_2026-08-19.py`:** both wired call sites,
independently, change **exactly 21** osm_ids, 0 missing / 0 extra against
`changed_scope_b == True` in `open35_fallback_agreement_scope.csv`, and the two sites'
own changed-sets are identical to each other. Per-cell: `austin_centre` 5, `la_urban` 3,
`nyc_centre` 8, `nyc_urban` 5 — matching §4.4a exactly.

**Test status:**
```
.venv/Scripts/python.exe -m pytest -q tests/test_open35_wiring.py tests/test_storey_fallback_agreement.py tests/test_footprint.py tests/test_idf_builder.py tests/test_results_aggregator.py tests/test_results_parser.py tests/test_builder_elevators_wired.py tests/test_parser_elevators.py tests/test_parser_hvac_metered.py
........................................................................ [ 43%]
........................................................................ [ 87%]
.....................                                                    [100%]
165 passed, 3 warnings in 28.56s
```
The 3 warnings are the same pre-existing, unrelated `DeprecationWarning` in
`tests/test_results_parser.py::TestCsvFallback` T04 already noted (date parsing, nothing
to do with this task). Full `pytest -q tests/` intentionally NOT run here per dispatch
instruction (director runs it).

**Notes:** `openubem/semantic/__init__.py` shows modified in `git status` but was not
touched by this task — it is OPEN-55's ruling B+ donor-screen fix, landed by a concurrently
running executor (same pattern T04 flagged with `test_semantic_unknown_bounds.py` /
`test_v12_ssh_stdin.py`). No production code outside `builder.py` and `aggregator.py` was
changed by T05. Recommendation for the director: either (a) rule that widening
`manifest_row`'s 4-column copy in `openubem/results/__init__.py:145-148` to include
`archetype_source` (plus threading the two median values through `parse_building()`) is
in scope for a narrow T06, or (b) accept parser.py's fallback-only exposure given builder.py
already fixes the primary `eio`-sourced path for successful simulations.

#### T06 — OPEN-35: close the parser gap the wiring opened — completed 2026-08-19

**Artifacts:** `openubem/results/__init__.py` (`_fleet_levels_medians()` new; the
`manifest_row` column-copy loop in `aggregate_results()` widened by exactly one real
column, `archetype_source`, plus three computed fields carried alongside it,
`_use_class`, `_levels_group_median`, `_levels_global_median` — see below);
`openubem/results/parser.py` (new `_derive_num_floors_wired()`; the single production
call site inside `parse_building()` rewired from `derive_num_floors(manifest_row)`);
`tests/test_open35_wiring.py` (extended, +12 tests: `TestParserWiring`,
`TestThreeWayAgreement`); `scripts/analysis/open35_t06_wiring_verify_2026-08-19.py`
(new fleet-wide three-way set-membership check, calls all three production-wired
helpers directly).

**How the parser reaches the medians (minimum-column widening, per hard bound):**
`parse_building()`'s only channel is `manifest_row` — it has no fleet-wide gdf, so it
cannot call `BuildingClassifier()._build_levels_median_lookup()` itself. `archetype_source`
is a real `enriched_gdf` column and is now copied into `manifest_row` (the 4-column
hardcoded loop at the old `:145-148` becomes 5 columns) — this is the only widening of
the *column copy* the task asked to minimize. The group-/global-median lookup and the
row's `use_class` are NOT gdf columns, so they cannot be reached by widening the copy
loop further; instead `aggregate_results()` computes them ONCE per run, by the
classifier's own route (`BuildingClassifier()._build_levels_median_lookup(enriched_gdf)`
and, per matched row, `_normalise_use_class(enriched_row)` — both imported, never
reimplemented, exactly as T05 did in `builder.py`/`aggregator.py`), and carries the three
results on `manifest_row` as `_use_class`, `_levels_group_median`,
`_levels_global_median`. `openubem/results/parser.py::_derive_num_floors_wired()` reads
those off the row and, gated by the same `_archetype_consumed_group_median()` check T05's
helpers use, calls `derive_num_floors()` with them — byte-identical to the pre-T06 call
for every row outside Scope B. `derive_num_floors()`'s logic, `building_classifier.py`,
and `openubem/semantic/__init__.py` were not touched. `aggregate_results()`'s structure
is unchanged beyond the one widened loop and one extra line before it.

**Three-way set-membership proof (not count),
`scripts/analysis/open35_t06_wiring_verify_2026-08-19.py`, all 12 phaseE cells, 8,160
buildings, existing Step-1 `01_buildings.gpkg` files, no re-classification, no
simulation, no fleet re-run:**

```
austin_centre: builder=5 aggregator=5 parser=5
la_urban: builder=3 aggregator=3 parser=3
nyc_centre: builder=8 aggregator=8 parser=8
nyc_urban: builder=5 aggregator=5 parser=5
Expected (changed_scope_b == True in open35_fallback_agreement_scope.csv): 21
builder-wired changed: 21
aggregator-wired changed: 21
parser-wired changed: 21
builder EXACT MEMBERSHIP MATCH vs expected: True
aggregator EXACT MEMBERSHIP MATCH vs expected: True
parser EXACT MEMBERSHIP MATCH vs expected: True
builder == aggregator == parser (three-way agreement): True
```

All three paths change exactly the same 21 osm_ids (`relation/7480583`,
`way/134807227`, `way/1416444072`, `way/231123149`, `way/260180778`, `way/265301856`,
`way/266034056`, `way/266170756`, `way/266170763`, `way/281344664`, `way/281345438`,
`way/283346493`, `way/288448678`, `way/293183674`, `way/328723692`, `way/402234762`,
`way/516276237`, `way/821626191`, `way/828447386`, `way/832347781`, `way/913603652`),
0 missing / 0 extra against each other and against `changed_scope_b == True` in
`open35_fallback_agreement_scope.csv`. The parser-path defect T06 exists to close —
build and parse deriving different floor counts for the same 21 buildings — is closed.

**Test status:**
```
.venv/Scripts/python.exe -m pytest -q tests/test_open35_wiring.py tests/test_storey_fallback_agreement.py tests/test_footprint.py tests/test_results_parser.py tests/test_results_aggregator.py tests/test_idf_builder.py tests/test_builder_elevators_wired.py tests/test_parser_elevators.py tests/test_parser_hvac_metered.py
........................................................................ [ 41%]
........................................................................ [ 83%]
.............................                                            [100%]
173 passed, 3 warnings in 35.17s
```
The 3 warnings are the same pre-existing, unrelated `DeprecationWarning` in
`tests/test_results_parser.py::TestCsvFallback` (date parsing) T04/T05 already noted.
`tests/test_open35_wiring.py` alone: 16 passed (4 pre-existing `TestBuilderWiring` +
4 pre-existing `TestAggregatorWiring` + 5 new `TestParserWiring` + 3 new
`TestThreeWayAgreement`, one of which re-derives the fleet-wide 21-osm_id census
independently inside the test itself, skipping gracefully if the phaseE fixtures are
absent). Full `pytest -q tests/` intentionally NOT run here per dispatch instruction
(director runs it).

**Deviations:** None from the task's hard bounds. `derive_num_floors()` was not touched
(0 lines changed in `openubem/geometry/footprint.py` this task).
`openubem/semantic/building_classifier.py` and `openubem/semantic/__init__.py` were not
touched. `aggregate_results()` was not restructured — the per-building loop keeps its
existing shape; only the column list and two new assignment lines were added, plus one
helper function and one line computing the medians once before the loop.

**Notes:** The premise the dispatch prompt named — that half-wiring (builder+aggregator
wired, parser not) recreates the two-paths-disagree defect for the same 21 buildings —
was correct and is now closed by set-membership proof. The T05 progress log's
"practical mitigation" note (that `eio`-sourced floor areas already reflected the fix for
successfully-simulated buildings, so the un-wired parser fallback only mattered for
`eio`-parse failures) is superseded: the parser's `derive_num_floors()` fallback now
agrees with the other two paths unconditionally, not just when `eio` parsing fails.
No fleet re-run, no re-publication, no fleet figure restated.
