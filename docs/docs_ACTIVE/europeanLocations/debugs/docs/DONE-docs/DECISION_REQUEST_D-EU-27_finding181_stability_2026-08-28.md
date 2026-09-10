# Decision request `D-EU-27` — what may be quoted from a campaign whose cells are ill-posed?

**Date:** 2026-08-28
**Status:** `RULED` (Option B selected)
**Raised by:** manager session, at the close of `PLAN_finding181-stability-2026-08-28.md` (T01–T04)
**Nothing here asks for compute.** Everything below is measured; the diagnostic budget is spent and no further run is requested by this document.

---

## 0. Ruling

> **Option B adopted.** Adopt `Timestep 12` (sub-hourly 5-minute stepping) as the campaign simulation configuration. Perform the single agreed campaign re-run with 3 replicates per cell, and quote only cells that demonstrate bit-reproducibility across all 3 replicates. Acknowledge that `idf_sha256` digests and heating demand figures are updated to this stable sub-hourly basis.

- [ ] **A** — quote nothing from the campaign until the equivalent-envelope method is repaired. `EU-09` / `EU-10` stay `UNSCORED` indefinitely; the single agreed re-run is **not** triggered.
- [x] **B** — adopt `Timestep 12` as the campaign setting, re-run once, and quote only cells that are bit-reproducible over 3 replicates. Accepts that every heating figure and every `idf_sha256` changes. *(adopted)*
- [ ] **C** — keep `Timestep` as is, re-run once with **3 replicates per cell**, and quote only cells whose three replicates agree bitwise. Cheapest in method risk, 3× in compute, and (measured) admits far fewer cells than B.
- [ ] **D** — other: ______________________________________________

> **Owner name / initials:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

**What a ruling here does *not* do, whichever box is ticked:**

- It does **not** move any published OpenUBEM figure. The adopted fleet baseline (153.8 kWh/m², n = 8,153) contains nothing from this campaign.
  - ⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.
- It does **not** re-open `D-EU-23` (`S3 = 96`, mixed mode), `D-EU-24` (`S3` promotion), `D-EU-26` (the `Wall_1` host check), or the frozen `eu_campaign_cell_spec_v1.0.json`.
- It does **not** authorise editing `openubem/idf/*.py` or any builder. Options B and C are campaign-configuration choices, not code changes.
- It does **not** decide `D-EU-25`, which remains the arc's other open decision.

---

## 1. What is already settled and is *not* part of this request

- `D-EU-26` is `RULED` (Option B): 115 of 510 cells refuse deterministically at build; the perimeter is **395**, re-confirmed exactly by T03. `uk` is never quotable at fold level.
- Branch A of the plan — harness non-determinism in the IDF build — is **refuted** (T01). The built model is deterministic in content; the only byte that moves between replicates is the absolute `Schedule:File` path.
- The `Material:NoMass` CTF-limit hypothesis is **refuted by inspection** (T04, P5): no opaque construction sits below the EnergyPlus massless minimum.
- Parallelism is **refuted** as the cause (T01): the largest instability was observed in strictly serial mode.

---

## 2. The finding that needs a ruling

`FINDING 181` was stated as "a cell can exit 0 and be meaningless." T01–T04 establish something stronger and simpler:

**The cells are ill-posed, and EnergyPlus says so numerically.** On the failing runs it reports surface temperatures of **−289.29 °C and +202.24 °C** for `EU_CELL_ZONE` before terminating with 125 severe errors, or a single fatal `Convergence error in SolveForWindowTemperatures`, halting before the simulation begins. These are consequences of the equivalent-envelope method itself — massless envelope, unenclosed zone, windows on `OtherSideCoefficients` — and of nothing in the harness.

Three measured consequences follow:

1. **`completed: true` is not sufficient** (already known) **and `clean: true` is not sufficient either** (new). `uk__GB.ENG.AB.03__f000` is recorded by T03's single-pass screen as completed, 0 severe, 0 fatal, no marker — and T01 shows it returning 429401.898 kWh twice and 111864.121 kWh once, in serial. **Only replication detects this.**
2. **No cell is certifiable by past behaviour.** `it__IT.MidClim.AB.01__f000` was bit-identical across all 9 T01 runs and returned three distinct values with one engine failure at T04 baseline.
3. **`es` is unusable as a fold.** 0 of 110 attempted `es` cells are clean; `Temperature out of range … PsyPsatFnTemp` fires on 97 of 110 `es` cells and on 0 of 285 elsewhere.

---

## 3. Why it is a judgement

The engineering question — "is the model well posed?" — is answered: it is not. What is not an engineering question is what the project does about it, because the three answers cost different things and none is free:

- Repairing the method means changing the geometry contract, which is out of this arc's scope and re-opens closed rulings.
- Sub-hourly stepping buys reproducibility at the price of every hash and every number in the campaign.
- Replicate-and-agree keeps the numbers but shrinks the perimeter by an amount that has not been measured at scale.

None of these is implied by the DESIGN. The owner chooses.

---

## 4. Options — the full statement of each

**A — quote nothing; do not re-run.** The honest reading of §2: an ill-posed model's number is unusable whether or not it reproduces. `EU-09` / `EU-10` stay `UNSCORED`, the agreed single re-run is not spent, and repairing the equivalent-envelope method becomes a separate work package. Costs the arc its remaining deliverables. Buys the strongest defensibility.

**B — `Timestep 12`, re-run once, quote bit-reproducible cells only.** Measured at T04: of the 4 cells unstable at baseline, `Timestep 12` collapses 3 to a single value with zero failures, and it is the **only** probe that leaves both controls at **0.0 %** — P2 moves them +10.2 % / +9.1 %, P3 −2.6 % / −16.9 %, P4 −1.6 % / −15.7 %. So it buys reproducibility without buying a different building. It does not cure everything: `it__IT.MidClim.SFH.07__f000` still spreads 10.3 %. Costs: every heating figure and every `idf_sha256` in the campaign is superseded, and the run is ~2–3× slower.

**C — keep `Timestep`, re-run with 3 replicates, quote only unanimous cells.** Changes no physics and no setting, so nothing is superseded by choice. Costs 3× compute and, on T03's numbers, would admit materially fewer than the 249 currently-clean cells, since the screen provably misses cells that flip.

---

## 5. What this costs in `idf_sha256` terms

- Under **A**, nothing is re-run and every existing digest stands as-is.
- Under **B**, **every** `idf_sha256` in the campaign is superseded — the timestep is in the IDF.
- Under **C**, the IDFs are unchanged in content, so the digests stand in content terms. Note the separate T01 caveat: `idf_sha256` embeds the absolute `Schedule:File` path (`openubem/semantic/european_schedules.py:119`), so a digest identifies a *run directory* as well as a model. This is a caveat on what the hash means; it moves no figure.

Under all three, the binding constraint agreed with GSSCanada 4J stands: **the campaign is re-run at most once**, after both `D-EU-26` and `FINDING 181` settle.

---

## 6. Evidence

- `docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md` §7, entries T01, T03, T04.
- `docs/docs_ACTIVE/europeanLocations/outputs/f181_t01_matrix.csv` (108 rows), `f181_t01_summary.csv`, `f181_t03_cells.csv` (510 rows), `f181_t03_per_archetype.csv` (102 rows), `f181_t04_probes.csv` (144 rows).
- `openubem/outputs/_tmp_f181/t04/it__IT.MidClim.SFH.07.Gen.ReEx.001.001__f000/P0/rep1/eplusout.err` — the ±200 °C surface temperatures.
- `openubem/outputs/_tmp_f181/t04/es__ES.ME.AB.01.Gen.ReEx.001.001__f030/P2/rep1/eplusout.err` — the window-solver fatal.
- `scripts/diagnostics/f181_t01_serial_vs_parallel.py`, `f181_t03_err_screen.py`, `f181_t04_envelope_probes.py`.
