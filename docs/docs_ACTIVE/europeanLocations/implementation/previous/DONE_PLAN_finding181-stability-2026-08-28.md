# PLAN — `FINDING 181`: why a *completed* S0 campaign cell is not reproducible, and whether it is ours

**Slug:** `finding181-stability` · **Date:** 2026-08-28 · **Arc:** European locations × Step 8
**DESIGN pointers:** `MVP_european_locations.md` §9.4 (campaign boundary), §9.6 · `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
**Correspondence that states the finding:** `messages_GSSCanada/2026-08-28_4J_to_OpenUBEM_internalmass_fix_verified_campaign_still_not_reproducible.md`
**Ruling already in force:** `debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-26_s0_wall1_host_2026-08-28.md` (Option B — perimeter 395 of 510)

---

## 1. What this is, in one paragraph

`FINDING 181` says a cell can exit `0`, raise no Severe, be recorded `completed: true`, and still carry a
heating figure that is numerically meaningless — and that across three identical 510-cell runs only
**136 cells** are clean and bit-reproducible, with **`es` contributing zero** and only **5 of 102
archetypes** carrying all five `f` levels. `EU-09` and `EU-10` are unscoreable while that stands, and it
is the **sole** remaining precondition to the one agreed campaign re-run. This plan does not fix it. It
**decides what it is**: a defect in our harness, a defect in our physics inputs, or a property of the S0
equivalent-envelope method that only an owner can rule on. The task order is chosen so the cheapest
discriminator runs first and can end the investigation early.

---

## 2. Hard rules for the executor

1. **Diagnose, do not remediate.** No change under `openubem/` is adopted in this plan. Probes run on
   *copies* of a built IDF or inside a throwaway diagnostic script. If a probe works, it is *reported*,
   not merged. (Project rule: no fixes in a measurement task.)
2. **Never re-run the 510 as a campaign.** One re-run is agreed with GSSCanada 4J, on the owner's ping,
   after this finding closes. Only T03 touches the full perimeter, once, as a diagnostic.
3. **Anything that changes `idf_sha256` is an owner decision.** All current hashes are already superseded;
   creating a *second* superseding set without a ruling breaks the single-re-run agreement.
4. **`D-EU-26` is ruled and out of scope.** The perimeter is 395 of 510; the 115 IDF-build refusals
   (`FINDING 179`) are the ruled boundary of the method, not a bug to chase here.
5. **No `uk` fold-level figure may be produced or quoted** in any table this plan creates — 17 of 36
   archetypes are refused. Per-archetype only.
6. **No cluster.** This is a local diagnostic on EnergyPlus **23.1** (`C:\EnergyPlusV23-1-0`, the version
   the runner pins at `openubem/campaign/eu_cell_runner.py:572`). No `sbatch`, no network.
7. **`completed: true` is never the metric.** Every table this plan produces reports, per archetype:
   attempted / completed / clean (no `.err` marker) / bit-reproducible.
8. Do not touch root `main.py`, OVERVIEW or DESIGN docs. No `.py` under `docs/`.
9. **Report the number and the `file:line`, not the file contents.**

---

## 3. File layout

| what | where |
|---|---|
| diagnostic scripts | `scripts/diagnostics/f181_t01_serial_vs_parallel.py`, `…_t02_build_determinism.py`, `…_t03_err_screen.py`, `…_t04_envelope_probes.py` |
| run trees (never committed) | `openubem/outputs/_tmp_f181/` — matches the ignored `**/_tmp_*/` rule at `.gitignore:46` |
| result tables | `docs/docs_ACTIVE/europeanLocations/outputs/f181_*.csv` |
| the write-up | `docs/docs_ACTIVE/europeanLocations/debugs/docs/` (a decision request **only if** T05 concludes it is a DESIGN question) |
| progress log | §7 of this doc, one entry per task |

---

## 4. Dependency decisions (pinned)

- **EnergyPlus 23.1 only.** Do not test whether 22.1 or 24.2 behaves better — that is a different question
  and would invalidate every retained artefact.
- **`eu_campaign_cell_spec_v1.1.json`**, `FROZEN_PINNED`: read it and verify its digest, never write it.
- **`run_campaign_cell` is the only entry point.** Do not hand-build IDFs by another path; the finding is
  about what that function produces.
- **Weather, presence binding and gain CSVs are the ones already pinned.** No re-derivation.

---

## 5. Facts this plan is built on, with citations

1. `run_campaign_cell` gives each cell its **own** `run_dir` and passes it to EnergyPlus as `-d`, with
   `cwd=run_dir` — `eu_cell_runner.py:498-499` and `:399-401`. **Output-file collision between parallel
   cells is therefore already excluded**; whatever parallelism does, it does before the engine.
2. `_build_idf` calls `IDF.setiddname(...)` and swallows `IDDAlreadySetError` — `eu_cell_runner.py:305`.
   `geomeppy`/`eppy` hold the IDD and several caches as **class-level state**. Under a *thread* pool that
   is shared mutable state on the build path; under a *process* pool it is not.
3. 4J measured **one cell, three serial runs, identical to the last digit** (§1 of their letter) and
   **510 cells under `--workers 14`, not reproducible** (§2). Serial-clean / parallel-dirty is the most
   informative pair of facts available, and nobody has yet varied *only* that.
4. The S0 zone is **deliberately not a closed prism** — `european_box.py:48-58` says so: independently
   sized, non-overlapping faces belonging to one zone whose declared volume is `V_C`. EnergyPlus
   consequently raises `FixViewFactors: View factors not complete`, so interior long-wave exchange is
   ill-posed.
5. Every S0 opaque construction is **massless** (`Material:NoMass`, `Thermal_Resistance = 1/U`,
   `european_physics.py:34-55`) and all zone capacity comes from one `InternalMass` object sized to
   `c_m · A_floor` at 45 Wh/m²K (`european_physics.py:57-102`). That mass surface participates in the
   same ill-posed radiant exchange as fact 4.
6. Outside boundaries are `OtherSideCoefficients` with
   `Combined_ConvectiveRadiative_Film_Coefficient = 0.0` (`european_physics.py:117-140`) — the OSC
   temperature acts as an air temperature and the outside film is computed by the engine.
7. The three `.err` strings that define an unstable cell are quoted in §3 of 4J's letter
   (`Temperature out of range … (PsyPsatFnTemp)`, `Inside surface heat balance did not converge`,
   `CalcHeatBalanceInsideSurf`). Two of the three are **Warnings** — which is why nothing downstream saw
   them, and why on one `uk` cell 433272.27 kWh and 89437.31 kWh were both recorded `completed`.

---

## 6. Tasks

### T01 — Is it the parallelism? (the discriminator — run this first)

**What.** Pick **12 cells**: the 5 archetypes with a complete reproducible sweep, plus 7 drawn from the 49
that were clean in all three runs yet returned different heating. Run each **3× strictly serially**, then
**3× through a 14-worker pool**, in *both* pool flavours — `ThreadPoolExecutor` and `ProcessPoolExecutor`.
Record, for every run, `idf_sha256` and `heating_kwh` at full precision.

**Why.** It splits the finding into two halves that share no cause. If `idf_sha256` differs between runs
of the same cell, the **input** is non-deterministic and this is our harness (fact 2). If the hash is
identical and only `heating_kwh` moves, the input is fixed and the **engine** is being handed an ill-posed
problem (facts 4–6) — and no amount of harness work will help.

**How.** `scripts/diagnostics/f181_t01_serial_vs_parallel.py`, run root `openubem/outputs/_tmp_f181/t01/`.
Call `run_campaign_cell` unmodified. Never round a recorded value.

**How to test.** `f181_t01_matrix.csv`: one row per (cell, mode, replicate) with `idf_sha256`,
`heating_kwh`, `completed`, and which of the three `.err` markers fired. The pass condition is not "the
values agree" — it is that the table **answers the question**: hash-varies vs value-varies, per mode.

🛑 **STOP-AND-REPORT 1 — after T01.** Report the two counts and which branch is live. Do not begin T02 or
T03 on your own judgement.

---

### T02 — Build determinism, statically and in-process (branch A: the hash moved)

**What.** (a) Static read of the build path — `_build_idf` and everything it calls — for iteration over a
`set`, over a `dict` built from a set, `id()`-dependent ordering, or reliance on `PYTHONHASHSEED`.
(b) Build **one** cell 20× in a single process and 20× across fresh processes, hashing each.
(c) Build the 12 cells concurrently in a thread pool, twice, hashing each.

**Why.** eppy/geomeppy class-level state (fact 2) makes a thread pool the prime suspect, and a
non-deterministic *input* would make every stability argument moot.

**How.** `scripts/diagnostics/f181_t02_build_determinism.py`, `dry_run=True` — **no EnergyPlus at all**.

**How to test.** `f181_t02_build_hashes.csv`. Any hash disagreement must be reported **with its named
cause**, not merely observed.

---

### T03 — Characterise the instability per archetype (branch B: the hash held)

**What.** Run the **395-cell ruled perimeter** once, and screen every cell's `eplusout.err` for the three
strings of fact 7. Tabulate **per archetype**: attempted / completed / clean / which markers fired.
Confirm or refute locally that **`es` is 0**.

**Why.** It is 4J's own recommendation and the only filter matching the sensitivity design: `f` levels are
compared *within* an archetype, so an archetype missing one level contributes nothing. It also shows
whether instability tracks a **fold** (weather), a **construction variant**, or a **geometry class** —
three different causes with three different remedies.

**How.** `run_campaign_cell` unmodified, serial or process-pool per T01's verdict, run root
`openubem/outputs/_tmp_f181/t03/`. This is the largest compute in the plan and is authorised **once**.

**How to test.** `f181_t03_per_archetype.csv` plus a one-paragraph reading: does the marker correlate with
fold, U-value band, `b < 1`, plate aspect ratio — or with none of them?

---

### T04 — One-variable probes on the equivalent envelope (diagnosis only, nothing adopted)

**What.** On **6 reproducibly-unstable cells and 2 stable controls**, take the *built* IDF and change
exactly one thing per probe, re-running each probe 3×:

| probe | change | tests which fact |
|---|---|---|
| P1 | `Timestep` 4 → 12 | stiffness of a massless envelope (fact 5) |
| P2 | `SurfaceConvectionAlgorithm:Inside` → `Simple` | ill-posed interior exchange (fact 4) |
| P3 | explicit `ZoneProperty:UserViewFactors:BySurfaceName` | the unenclosed zone, directly (fact 4) |
| P4 | `InternalMass` capacity ×3 | is 45 Wh/m²K too little for this envelope (fact 5) |
| P5 | opaque `Thermal_Resistance` raised to the E+ massless minimum on the highest-U archetypes | massless-layer CTF limit (fact 5) |

**Why.** Each probe maps to one cited fact, so a probe that works is a *diagnosis*, not a patch. P2 or P3
working would mean the equivalent-envelope method itself is the cause — a DESIGN question the owner must
rule, because the remedy changes every `idf_sha256`.

**How.** `scripts/diagnostics/f181_t04_envelope_probes.py`, operating on copies under
`openubem/outputs/_tmp_f181/t04/`. **Never edit `openubem/idf/*.py` in this task.**

**How to test.** `f181_t04_probes.csv`: per (cell, probe, replicate) — markers fired, `heating_kwh`, and
whether the 3 replicates agree bit-for-bit. State plainly which single probe, if any, makes an unstable
cell stable **without** moving a stable cell's answer.

🛑 **STOP-AND-REPORT 2 — after T04, before any remedy is proposed.**

---

### T05 — Close or escalate, and register the error

**What.** Write the verdict in one of exactly two shapes:
- **Harness defect** → name the file and line and propose the fix and its tests *in the report*; the fix
  itself is a separate, separately authorised plan.
- **Method property** → a decision request `D-EU-27` in `debugs/docs/`, in the `D-EU-26` format (§0 Ruling
  block, options, perimeter consequence, and what the ruling does and does not buy), stating in one line
  what it costs in `idf_sha256` terms.

Then append the failure mode to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in house format —
quote the real `.err` strings, `[OPEN]` prefix while unfixed.

**Why.** An error is not fixed until its entry exists, and `EU-09`/`EU-10` cannot move without a written
verdict 4J can read.

**How to test.** The verdict names the branch, the evidence table, and the consequence for the single
agreed re-run.

---

## 7. Progress log

*(one entry per task: `#### TXX — <title> — completed YYYY-MM-DD`, then Artifacts / Deviations / Test status / Notes)*

#### T01 — serial vs parallel discriminator — completed 2026-08-28

**Artifacts** — `scripts/diagnostics/f181_t01_serial_vs_parallel.py`; run tree `openubem/outputs/_tmp_f181/t01/{serial,thread,process}/rep{1,2,3}/`; tables `docs/docs_ACTIVE/europeanLocations/outputs/f181_t01_selection.csv`, `f181_t01_matrix.csv` (108 rows), `f181_t01_summary.csv`.

**Deviations** — 4J's letter names no cells, so the plan's "5 reproducible archetypes + 7 of the 49" selection was not reconstructible. Replaced by a deterministic, recorded rule: one archetype per fold (`uk` GB.ENG.AB.03.Gen.ReEx.001.001, `it` IT.MidClim.AB.01.Gen.ReEx.001.001, `es` ES.ME.AB.01.Gen.ReEx.001.001) at `f` = 0.0 / 0.15 / 0.30 / 0.50, first in spec order that builds under `dry_run`. `es` deliberately included although it contributed zero reproducible cells in 4J's run.

**Test status** — 108 of 108 runs attempted; 99 COMPLETED, 9 ENGINE_FAILED (see below). No test suite run; this task is diagnostic only. Nothing under `openubem/` was modified.

**Notes**

1. **Branch A is FALSE — the build is deterministic in content.** `idf_sha256` differs across every replicate in all three modes (0 of 12 cells hash-identical, serial included), but a byte diff of the same cell's IDF across serial rep1/rep2/rep3 shows **exactly one differing line**: the absolute path in the `Schedule:File` `File Name` field, which embeds `run_root`. The referenced schedule CSVs are byte-identical (`cmp` clean over all 12). **`idf_sha256` is therefore run-root-dependent and is not a model-provenance key** — two identical models run from different directories hash differently. The path is written verbatim by `openubem/semantic/european_schedules.py:119` (`File_Name=str(output)`), so this is a property of the campaign builder and not of the T01 harness: the promoted campaign's published `idf_sha256` values likewise carry their run directory. Nothing published moves because of this — it is a caveat on what the hash *means*, not on any figure.

2. **Branch B is LIVE, and it is not parallelism.** With a byte-identical model, `uk__…__f000` returned 429401.8978237175 kWh on serial rep1 and rep2 and **111864.12061177054 kWh on serial rep3** (−74.0 %); `es__…__f000` returned 177928.78032852308 twice and **52702.00394983997** on serial rep3 (−70.4 %). Both flips are in **serial** mode, where no pool of any kind is involved. 4 of 12 cells show more than one distinct heating value across their 9 runs; the other two are 0.11 % and 0.03 % spreads.

3. **The flip is marked in `eplusout.err`, as a Warning.** Every large flip carries `Inside surface heat balance did not converge`; both serial rep3 flips have it and their stable siblings do not. On those two runs EnergyPlus reported `severe_count = 14` and still exited `return_code = 0` with `completion_status = COMPLETED` — fact 7 confirmed locally: `completed: true` hides the failure, and even a non-zero Severe count does not surface it. `Temperature out of range … (PsyPsatFnTemp)` is present on *every* `es` run, stable and unstable alike, so it is a fold-wide condition and not the discriminator. `CalcHeatBalanceInsideSurf` never appeared.

4. **`ENGINE_FAILED` is itself non-deterministic** — 9 occurrences scattered over serial (2), thread (2) and process (5), on cells that completed in other replicates. Same input, same binary, different outcome.

5. Aggregate max relative heating spread by mode: serial 2.84, thread 0.0011, process 0.00033 — i.e. the *largest* instability was observed in the mode with no concurrency at all. Pool flavour does not explain the finding.

**Verdict for STOP-AND-REPORT 1** — proceed on **branch B**: the input is fixed and the engine is being handed an ill-posed problem. T02 (build-determinism scan) is **not** warranted; T03 is dispatched next.

#### T03 — full-perimeter `.err` screen — completed 2026-08-28

**Artifacts** — `scripts/diagnostics/f181_t03_err_screen.py`; run tree `openubem/outputs/_tmp_f181/t03/`; tables `docs/docs_ACTIVE/europeanLocations/outputs/f181_t03_cells.csv` (510 rows), `f181_t03_per_archetype.csv` (102 archetype×fold rows).

**Deviations** — three of the four planned correlations (U-value band, effective `b < 1`, plate aspect ratio) were **not computable**: the spec cell record carries only `archetype_id, cell_id, control_cell_id, country_stock_code, epw_path, gain_csv_path, idf_path, manifest_path, schedule_status, sensitivity_f, survey_fold, weather_id, weather_sha256, weather_status`. Skipped rather than invented, per the plan's hard rule. Only `survey_fold` was testable.

**Test status** — 510 of 510 cells attempted once, `dry_run=False`. No suite run; diagnostic only. Nothing under `openubem/` modified.

**Notes**

1. **`D-EU-26`'s split is confirmed exactly**: 115 `BUILD_REFUSED` / 395 `ATTEMPTED`. All 115 refusals are a `ValueError` carrying the `S0 openings require an exterior (b=1) Wall_1 host` message — one failure mode, not a family.

2. **Of the 395 attempted, 346 completed and 249 are clean** (completed ∧ severe=0 ∧ fatal=0 ∧ no marker). Per archetype×fold, 79 of 102 pairs attempted, 79 completed at least one cell, **only 57 produced a clean one**. Archetypes completing all five `f` levels: 48 (es 14, uk 16, it 18). Archetypes **clean** on all five: 34 — **uk 16, it 18, es 0**.

3. **`es` clean = 0 is CONFIRMED at full perimeter**: 0 of 110 attempted `es` cells are clean. `marker_psy` (`Temperature out of range … PsyPsatFnTemp`) fires on 97 of 110 `es` cells and on **0 of 190 `it` and 0 of 95 `uk`** — it is a fold-specific condition, exactly as T01 read it locally, and it alone accounts for the whole `es` shortfall.

4. **`marker_inside_hb` is rare and is the engine-failure marker**: 9 cells total (it 7, uk 2), and **all nine returned `heating_kwh = None`** with severe counts 23–33. `marker_calchb` fired once (it). So at full perimeter the inside-heat-balance marker coincides with an outright failure, not with a silently-wrong number.

5. 🔴 **The screen does not catch FINDING 181's worst case.** `uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000` — the cell T01 proved returns 429401.898 kWh twice and 111864.121 kWh once in strictly serial mode — is recorded here as **completed, severe 0, fatal 0, no marker, `clean`**. A single-pass `.err` screen therefore cannot certify a cell: `clean: true` is necessary and, like `completed: true`, **not sufficient**. Instability is only visible under replication.

#### T04 — one-variable envelope probes — completed 2026-08-28

**Artifacts** — `scripts/diagnostics/f181_t04_envelope_probes.py`; run tree `openubem/outputs/_tmp_f181/t04/<cell>/<probe>/rep{1,2,3}/`; table `docs/docs_ACTIVE/europeanLocations/outputs/f181_t04_probes.csv` (144 rows).

**Deviations** — cell selection is recorded, not reconstructed from 4J: 6 unstable (`uk__GB.ENG.AB.03__f000`, `uk__GB.ENG.AB.03__f050`, `es__ES.ME.AB.01__f000`, `it__IT.MidClim.AB.01__f050`, `it__IT.MidClim.SFH.07__f000`, `uk__GB.ENG.TH.05__f015`) drawn from T01's replicated flips and T03's `marker_inside_hb` set; 2 controls (`it__IT.MidClim.AB.01__f000`, `es__ES.ME.AB.01__f030`) 9/9 identical in T01. **P5 is `NOT_APPLICABLE` on all 8 cells** — no opaque `Material:NoMass` carries a `Thermal_Resistance` below the EnergyPlus massless minimum, so the CTF-limit hypothesis of fact 5 is refuted by inspection and never needed a run.

**Test status** — 120 runs executed (24 skipped as P5 `NOT_APPLICABLE`). No suite run; diagnostic only. Nothing under `openubem/` modified.

**Notes**

1. 🔴 **The model is provably ill-posed, and the `.err` says so numerically.** On the slow-abort signature (severe 27–33, ~1.0–1.4 s) EnergyPlus reports surface temperatures of **−289.29 °C and +202.24 °C** for `EU_CELL_ZONE` before terminating with 125 severe errors. On the fast-abort signature (severe 1, ~0.37–0.46 s) it is a single `Convergence error in SolveForWindowTemperatures for window …_WINDOW_EAST_1`, fatal during sizing, `Program exited before simulations began`. Both are consequences of the equivalent-envelope method itself — massless envelope, unenclosed zone, windows hosted on `OtherSideCoefficients` — not of any harness code.

2. **The controls were not controls.** `it__IT.MidClim.AB.01__f000`, byte-stable across all 9 T01 runs, returned **three distinct values with one engine failure** at P0 here. Instability is intermittent and fleet-wide; **no cell can be certified stable by any number of past clean runs.**

3. **P1 (`Timestep` 6 → 12; the campaign baseline is `Timestep,6` at `openubem/campaign/eu_cell_runner.py:52` and `scripts/run_eu_s2_campaign.py:73`, not the 4 the plan text assumed) is the only probe that reduces instability, and it does so broadly.** Of the 4 cells unstable at baseline in this batch, P1 collapses 3 to a single value with zero failures, and it stabilises both controls. Across all 8 cells P1 leaves 1 engine failure against baseline's 5. P2 (`Simple` inside convection) *changes the answer* on `uk__…AB.03__f000` by +10.8 % (429401.90 → 472600.50) without stabilising it. P3 (explicit view factors) and P4 (`InternalMass` ×3) do collapse several unstable cells, but only by **materially changing the physical answer**: measured against their own P0 baseline they move the `es` control by −16.9 % and −15.7 % and the `it` control by −2.6 % and −1.6 %. P2 moves the two controls +10.2 % and +9.1 %. **P1 moves both controls by 0.0 %** — it is the only probe that buys reproducibility without buying a different building.

4. **One cell resists every probe.** `it__IT.MidClim.SFH.07__f000` fails or diverges under P0–P4 alike, with 0.10 relative spread under P1. Sub-hourly stepping is a mitigation, not a cure.

5. **No remedy is proposed here.** Raising the timestep changes every heating figure and every `idf_sha256` in the campaign; that is an owner decision, carried to T05.

#### T05 — verdict — completed 2026-08-28

**Artifacts** — `docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISION_REQUEST_D-EU-27_finding181_stability_2026-08-28.md`; four new entries appended to chapter 2 of `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.

**Deviations** — none.

**Test status** — no suite run; this task produces documents only. Nothing under `openubem/` modified, nothing committed.

**Notes**

1. **Verdict: METHOD PROPERTY, not harness defect.** No file and no line in the harness can be named as the cause, and the plan's only two harness hypotheses are both refuted — build determinism (T01) and the `Material:NoMass` CTF limit (T04, P5, `NOT_APPLICABLE` on all 8 cells). What EnergyPlus reports instead is that the cell is an ill-posed heat-balance problem: **−289.29 °C to +202.24 °C** surface temperatures, or a fatal `SolveForWindowTemperatures` convergence error before the simulation begins. These follow from the equivalent-envelope method — massless envelope, unenclosed zone, windows on `OtherSideCoefficients` — which is a DESIGN choice, not a bug.

2. **Escalated as `D-EU-27`** in the `D-EU-26` format, with three options: **A** quote nothing and do not spend the single agreed re-run; **B** adopt `Timestep 12`, re-run once, quote only bit-reproducible cells; **C** keep the timestep, re-run with 3 replicates, quote only unanimous cells. The `idf_sha256` cost of each is stated in §5 of that document.

3. **`FINDING 181` is now fully characterised and stays OPEN**, its closure being exactly the `D-EU-27` ruling. `EU-09` / `EU-10` remain `UNSCORED`. The arc now has **two** open decisions: `D-EU-25` and `D-EU-27`.

4. Registered in `OpenUBEM_debug_References.md` chapter 2: the two fatal signatures with `[OPEN]` prefixes, plus the silent-flip symptom and the run-root-dependent `idf_sha256`, quoting the real message strings.

**Verdict for STOP-AND-REPORT 2** — the plan is complete, T01 → T05. No remedy is applied and none is proposed for execution; the next action is an owner ruling on `D-EU-27`.
