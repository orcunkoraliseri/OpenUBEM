# PLAN — `D-EU-27` execution: `Timestep 12` + triplicate certified re-run

> ⚠ **SUPERSEDED IN PART, 2026-08-28: `D-EU-28` (Option B) narrowed the quotable perimeter from the 191 certified cells to the **149 marker-free** ones (`uk` 75, `it` 74, **`es` 0**), and the five-`f` sweep set from 17 pairs to **15** (`uk` 8, `it` 7). `FINDING 182`: 42 of the 191 carry `marker_psy` in all three replicates, all 42 `es`. Everything else in this plan stands as executed; the 191 remains correct as the intermediate certified count. See MVP §9.7.3.**

**Slug:** `deu27-timestep12-rerun`
**Date:** 2026-08-28
**Authority:** `D-EU-27` ruled Option B by the owner on 2026-08-28 — see
`docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISION_REQUEST_D-EU-27_finding181_stability_2026-08-28.md` §0.
**Predecessor:** `PLAN_finding181-stability-2026-08-28.md` (T01–T05, complete).
**DESIGN pointer:** `docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md` §9.4, §9.7.

---

## 2. Hard rules for the executor

1. **Execute this document top to bottom. Do not propose alternatives.** If the DESIGN is ambiguous, STOP and quote the conflict.
2. **This is the single agreed re-run.** It is spent once. Do not re-run the campaign a second time to "fix" a result you dislike; report it instead.
3. **`.venv/Scripts/python.exe` always.** Bare `python` on this machine is the Windows Store stub.
4. **Never commit.** Git is handled outside this session.
5. **Do not touch** `openubem/idf/*.py`, the geometry contract, `eu_campaign_cell_spec_v1.0.json` / `v1.1.json`, or any file under `docs/docs_main/`. The only source change authorised here is the timestep constant named in T01.
6. **Do not annotate MVP Table 9.7.** Status cells stay short; all notes go to §9.7.3 and the progress log.
7. **A cell is CERTIFIED only if all 3 replicates return a bitwise-identical `heating_kwh`** *and* the cell completed with `severe_count = 0`, `fatal_count = 0`. Both conditions, not either.
8. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`; after solving one, register it there before closing the task.

---

## 3. File layout

- Source change: `openubem/campaign/eu_cell_runner.py` and `scripts/run_eu_s2_campaign.py` (T01 only).
- New script: `scripts/campaign/run_eu_certified_rerun.py`.
- Run root: `openubem/outputs/eu_certified_rerun_2026-08-28/` (per cell, per replicate).
- Tables: `docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv`,
  `deu27_certified_cells.csv`, `deu27_per_archetype.csv`.

---

## 4. Dependency decisions (pinned)

- EnergyPlus 23.1, the version recorded at `openubem/campaign/eu_cell_runner.py:572`. No other version.
- `ENERGYPLUS_PATH` is the **install directory**, not the executable.
- Spec: `openubem/data/campaign/eu_campaign_cell_spec_v1.1.json`, sha256
  `16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6` (`tests/test_eu_cell_runner.py:26-27`).
- Perimeter: 395 attempted of 510 — the 115 `BUILD_REFUSED` cells are ruled out by `D-EU-26` and are **expected**, not errors.

---

## 5. Facts this plan is built on, with citations

1. Campaign baseline is `Timestep,6`, emitted at `openubem/campaign/eu_cell_runner.py:52` and `scripts/run_eu_s2_campaign.py:73` — **not** `Timestep,4`.
2. `Timestep 12` collapsed 3 of 4 baseline-unstable cells to a single value with zero failures and moved both controls by **0.0 %**; every other probe moved a control by 1.6–16.9 %. (`PLAN_finding181-stability-2026-08-28.md` §7 T04 note 3.)
3. `completed: true` and a clean `.err` screen are both **insufficient** — `uk__GB.ENG.AB.03__f000` passes both and still flips −74 %. (§7 T03 note 5.)
4. No cell is certifiable by past behaviour: a 9/9-identical control returned 3 distinct values on the next batch. (§7 T04 note 2.)
5. `es` had 0 of 110 clean cells at baseline; `PsyPsatFnTemp` fires on 97 of 110 `es` and 0 of 285 elsewhere. (§7 T03 note 3.)
6. `idf_sha256` embeds the absolute `Schedule:File` path (`openubem/semantic/european_schedules.py:119`), so digests differ between run roots for an identical model. (§7 T01 note 1.)
7. `it__IT.MidClim.SFH.07__f000` resists every probe including `Timestep 12` (10.3 % spread). (§7 T04 note 4.)

---

## 6. Tasks

### T01 — set the campaign timestep to 12

**What.** Change `Timestep,6;` to `Timestep,12;` at `openubem/campaign/eu_cell_runner.py:52` and
`scripts/run_eu_s2_campaign.py:73`. Nothing else.
**Why.** `D-EU-27` Option B. Fact 2 is the whole justification and it is a measured one.
**How.** Two one-line edits. Leave `openubem/acquisition/european_weather.py:413` (`Timestep,4`) and
`scripts/run_eu_s1_smoke.py:56` alone — they are the weather-gate and S1-smoke paths, outside this ruling.
**How to test.** `.venv/Scripts/python.exe -m pytest -q -n 8 tests/` — expect the 2,341 / 55 baseline.
Any test asserting `Timestep,6` is an **expected** failure: update that assertion to 12 and cite `D-EU-27` in
the progress log. Then run one cell through `run_campaign_cell` with `dry_run=True` and grep the built IDF
for `Timestep` to confirm 12 reaches the file.

### T02 — the certified re-run

**What.** Run all 510 spec cells, **3 independent replicates each**, `dry_run=False`.
**Why.** Facts 3 and 4: only replication can certify a cell.
**How.** Write `scripts/campaign/run_eu_certified_rerun.py`, reusing the `run_campaign_cell` invocation and
the `eplusout.err` screening from `scripts/diagnostics/f181_t03_err_screen.py` verbatim. Each replicate gets
its **own run directory**. `ProcessPoolExecutor(max_workers=14)`. Emit `deu27_rerun_cells.csv`, one row per
run: `cell_id,archetype_id,survey_fold,sensitivity_f,replicate,class,completed,completion_status,return_code,severe_count,fatal_count,heating_kwh,runtime_s,marker_psy,marker_inside_hb,marker_calchb,idf_sha256,error`.
**How to test.** Row count is exactly 1,530. `BUILD_REFUSED` count is exactly 115 × 3 = 345 (fact: the
`D-EU-26` perimeter is deterministic — if it is not 345, STOP and report, do not proceed).

### T03 — certification and scoring surface

**What.** Apply rule 7 of §2 and produce the certified perimeter.
**How.** From `deu27_rerun_cells.csv` emit `deu27_certified_cells.csv` (certified cells only) and
`deu27_per_archetype.csv` with, per `archetype_id × survey_fold`: attempted / completed≥1 / certified, and the
number of `f` levels certified (0–5). Report: certified cell count out of 395; per fold; how many archetypes
are certified on **all five** `f` levels; and whether `es` is still zero. Explicitly check the three cells named
in facts 3 and 7 and state what each did.
**How to test.** A cell that appears in `deu27_certified_cells.csv` must have exactly one distinct
`heating_kwh` across its 3 rows — assert this in the script, do not eyeball it.

🛑 **STOP-AND-REPORT — after T03, before T04.** Report the certified counts and the fold breakdown. Do not
write any MVP or register text until the director has read this.

### T04 — record the outcome

**What.** Append to `MVP_european_locations.md` §9.7.3 and the walkthrough progress log: the ruling, the
certified perimeter, and the standing caveats. Update `EU-09` / `EU-10` status rows **only** if T03 shows a
scoreable perimeter; otherwise leave them `UNSCORED` and say why.
**Why.** `D-EU-27` §0 makes the certified set the sole quotable surface.
**How to test.** No number appears in the MVP that is not in `deu27_certified_cells.csv`. Every quoted `uk`
figure is cell-level, never fold-level (`D-EU-26`).

---

## 7. Progress log

*(one entry per task: `#### TXX — <title> — completed YYYY-MM-DD`, then Artifacts / Deviations / Test status / Notes)*

#### T01 — Adopt `Timestep 12` at the two campaign call sites — completed 2026-08-28

**Artifacts** — `openubem/campaign/eu_cell_runner.py:52` and `scripts/run_eu_s2_campaign.py:73`, each `Timestep,6;` → `Timestep,12;`. `openubem/acquisition/european_weather.py:413` and `scripts/run_eu_s1_smoke.py:56` left at `Timestep,4;` as instructed.

**Deviations** — none.

**Test status** — `pytest -q -n 8 tests/` → **2,341 passed / 55 skipped**, 11 warnings, 316.45 s, exit 0. Exactly the pinned baseline. No test asserted on `Timestep,6`, so the anticipated expected-failure did not arise.

**Notes**

1. The baseline the investigation plan assumed (`Timestep,4`) was wrong; the campaign baseline was `Timestep,6`. The adopted step is therefore a 2× refinement, not 3×.

#### T02 — The certified re-run: 510 cells × 3 replicates — completed 2026-08-28

**Artifacts** — `scripts/campaign/run_eu_certified_rerun.py`; run root `openubem/outputs/eu_certified_rerun_2026-08-28/` (one directory per cell per replicate); `docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv`, **1,530 rows**.

**Deviations** — none. Both tripwires held on the first pass: row count exactly **1,530** and `BUILD_REFUSED` exactly **345** (= 115 cells × 3), so the `D-EU-26` perimeter of **395** is re-confirmed a third time, unchanged by the timestep.

**Test status** — n/a (execution task). Serial-consistency is the object of T03, not a test here.

**Notes**

1. This is the single re-run agreed with GSSCanada 4J. It is spent. Every `idf_sha256` from the 2026-08-28 run is superseded by this one.
2. 157 of 1,530 replicate runs carry `severe_count > 0` and 156 carry `fatal_count > 0`; 501 return no `heating_kwh` at all. Sub-hourly stepping mitigates the ill-posedness; it does not cure it, exactly as `D-EU-27` §4 option B stated.

#### T03 — Certification and the per-archetype table — completed 2026-08-28

**Artifacts** — `docs/docs_ACTIVE/europeanLocations/outputs/deu27_certified_cells.csv` (510 rows), `deu27_per_archetype.csv` (102 rows).

**Deviations** — the certification pass was run by the director directly rather than dispatched, after the executor stalled twice polling its own background job. The rule applied is the plan's §2 rule 7 verbatim, unmodified.

**Test status** — the two in-script assertions both passed: 1,530 rows, 345 `BUILD_REFUSED`, and 510 distinct `cell_id`.

**Notes**

1. **CERTIFIED = 191 of 510** — 48.4 % of the 395-cell perimeter. By fold: `uk` 75, `it` 74, **`es` 42**. Certification is the conjunction demanded by `D-EU-27`: three bitwise-identical `heating_kwh` **and** `severe_count = 0` **and** `fatal_count = 0` **and** all three replicates `completed`.
2. **The `es` fold is no longer empty.** T03 of the investigation measured `es` clean at **0 of 110**; at `Timestep 12` it certifies **42**, and 2 `es` archetypes complete all five `f` levels where previously none did. This is the single largest effect of the ruling and was not predicted by the T04 probes, which tested no `es` cell at `f` levels above 030.
3. **17 archetype×fold pairs certify all five `f` levels** (`uk` 8, `it` 7, `es` 2) — against 5 at baseline. Only these 17 support an `f`-sweep statement; every other archetype has a hole in its sweep.
4. **The two failure reasons are `not_all_completed` (121 cells) and `replicates_disagree` (83 cells).** No cell fails on severe or fatal alone — a cell that errs also fails to complete. The worst surviving disagreement is `uk__GB.ENG.AB.04.Gen.ReEx.001.001__f100` at **382.1 %** across its three replicates, so the filter is doing real work and must never be relaxed to "two of three".
5. 🔴 **`FINDING 181` is now closed by construction, not by cure.** The ill-posedness of the equivalent-envelope cell is unchanged and still documented `[OPEN]` in the debug references; what changed is that the campaign no longer quotes any cell that the ill-posedness touches. The certified 191 is the whole quotable perimeter — **never quote the 395, the 249 "clean" figure, or any raw `completed` count.**

**Verdict for the STOP-AND-REPORT after T03** — `D-EU-27` Option B is fully enacted. The scoreable perimeter for `EU-09` / `EU-10` is **191 cells**, and it is non-empty in all three folds. `uk` remains barred from fold-level quotation by `D-EU-26` independently of this result.

#### T04 — Record the outcome — completed 2026-08-28

**Artifacts.**
- `MVP_european_locations.md` §9.7.3 — one new addendum, `EU-08 / EU-09 / EU-10 — D-EU-27 RULED 2026-08-28, Option B, and EXECUTED the same day`, inserted after the `D-EU-26` addendum. Nothing above it was reworded.
- `content/walkthrough_progress_log.csv` — one row appended, `D-EU-27-T01-T04-EXECUTED` / `EXECUTED_PERIMETER_CERTIFIED` (175 lines, 9 fields).
- `prompts/DIRECTOR_PROMPT_european_locations.md` — new head box and restated status line.

**Deviations.** None. **Table 9.7 was NOT annotated**, per the standing owner ruling of 2026-08-28; the status table rows for `EU-08`/`EU-09`/`EU-10` were left at *In progress* because scoring is GSSCanada-side work and this task delivered a perimeter, not a score.

**Test status.** No code changed in T04; the suite baseline from T01 stands unchanged at **2,341 passed / 55 skipped**.

**Notes.**
1. The quotable perimeter is now a single number — **191 certified cells** — and every earlier perimeter is superseded: **never quote the 395, the 249 or 136 "clean" figures, or any raw `completed` count.**
2. `EU-09` / `EU-10` remain *In progress*: `FINDING 181` no longer blocks them, but scoring over the certified 191 is GSSCanada's execution, not this session's.
3. The single agreed re-run budget with GSSCanada 4J is **spent**. Any further campaign execution needs a fresh agreement.
4. `D-EU-25` is the arc's only remaining open decision.

**Plan status: COMPLETE.** T01–T04 all done, the stop-and-report after T03 was delivered, and `D-EU-27` Option B is fully enacted.
