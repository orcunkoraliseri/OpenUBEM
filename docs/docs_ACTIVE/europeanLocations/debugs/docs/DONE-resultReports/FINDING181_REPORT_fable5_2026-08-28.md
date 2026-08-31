# FINDING 181 — investigation, diagnosis and remedy — fable5 — 2026-08-28

Engine `EnergyPlus 23.1.0-87ed9199d4` (Windows), certified re-run tree
`openubem/outputs/eu_certified_rerun_2026-08-28/{rep1,rep2,rep3}/`, 1,530 rows of `deu27_rerun_cells.csv`
(510 cells × 3; 345 rows `BUILD_REFUSED`; 1,185 attempted rows = 1,029 `COMPLETED` + 156 `ENGINE_FAILED`).
Diagnostic only — no perimeter, band, gate or EUI is stated or implied anywhere below.

## 1. Verdict

The mechanism is not named, but it is now **localised**, and several things are **excluded** that were not
before. MEASURED: the divergence lives in the engine's own output (`eplusout.eso`), not in ReadVarsESO or the
harness (H1 excluded); the inputs handed to the engine are byte-identical in content (H4 excluded); every
`ENGINE_FAILED` is an EnergyPlus solver fatal with `return_code = 1`, none is an I/O error or the 900 s timeout
(H5 excluded); and — the new observation — **the divergence is already present in the zone-sizing pass**:
of 251 replicate pairs whose annual heating differs, 250 also differ in `epluszsz.csv` and differ from the
**first hourly record** of the run period, while all 662 pairs whose annual heating agrees have byte-identical
`epluszsz.csv` and (659/662) byte-identical `.eso`. Nothing computed in that sizing pass is consumed by the
run period (`ZoneHVAC:IdealLoadsAirSystem` is `NoLimit` both ways, nothing consumed is autosized), so the two
environments do not share a parameter — they share a **per-process condition**. The 117 window-solver fatals
all strike at one fold-fixed timestep of sizing day 1 on the **first `FenestrationSurface:Detailed` in input
order** (117/117). Agreeing replicates are bitwise identical over 8,760 hours, so this is not continuous
floating-point noise or a per-timestep race in the main loop; it is a discrete event decided once per process,
at or before the first window / inside-surface heat-balance solve, whose outcome the massless unenclosed model
then amplifies for the rest of the year. INFERRED, not proven from disk: an uninitialised or address-dependent
read at that first solve in the 23.1 Windows build. Two experiments of ≤ 30 runs each (§6, E1–E2) separate that
reading from its only surviving rival, state carried over from the sizing environment into the run environment.

## 2. Investigation — what I read

1. `PROMPT_finding181_investigation_2026-08-28.md`; `STATE_european_locations_v2.md` §3 (l.118–237);
   `implementation/previous/PLAN_finding181-stability-2026-08-28.md` §7 (l.207–291);
   `implementation/PLAN_deu27-timestep12-rerun-2026-08-28.md` §5 and §7; `OpenUBEM_debug_References.md` via
   `grep -n -i "energyplus\|eplusout\|readvars\|FixViewFactors\|ENGINE_FAILED\|non-determin"` (60 hits read).
2. `openubem/campaign/eu_cell_runner.py` l.380–640; `scripts/campaign/run_eu_certified_rerun.py` (whole);
   `openubem/idf/european_box.py` l.1–420.
3. `head -3` / `wc -l` on the five tables under `outputs/`.
4. `deu27_rerun_cells.csv` — status × replicate, failure fields, per-cell divergence classes, runtime
   distributions, odd-replicate-out, class/fold/`f` cross-tabs (`.venv\Scripts\python.exe -c`, csv module only).
5. Cell `uk__GB.ENG.AB.04.Gen.ReEx.001.001__f100` (largest 3-replicate spread): `wc -c`, `diff`, `cmp` of
   `eplusout.{expidf,eso,csv,err,eio,end,shd,bnd,audit,mtd,dbg,rvaudit,mdd,rdd}`, `epluszsz.csv`, `sqlite.err`,
   the manifest JSON and `schedules/<cell>.csv` across rep1/rep2/rep3; full `eplusout.err` of rep1;
   `grep -n -i autosize`, `SimulationControl`, `Sizing:Zone`, `HVACTemplate`, `SizingPeriod`, `RunPeriod`,
   `Building`, `HeatBalanceAlgorithm`, `Timestep` in `rep1/idfs/<cell>.idf`; the expanded
   `ZoneHVAC:IdealLoadsAirSystem` in `eplusout.expidf` l.733–760.
6. Same for the silent cell `it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100` (`.err`, `.eio`, `.end` × 3).
7. All 913 completed replicate pairs: first differing line of `eplusout.eso` and byte-equality of
   `epluszsz.csv` (python, `read_bytes().split(b"\n")`).
8. Hourly series of variable 556 from `.eso` for six pairs: hours differing, first differing hour, ratio
   percentiles, hour of maximum difference; `.eso` sum against the `eplusout.csv` sum.
9. All 156 failed runs: `cat rep*/*/eplusout.end | sed | sort | uniq -c`; `grep -h "**  Fatal  **"` and
   `grep -h "** Severe  **"` normalised with `sed -E "s/[0-9]+/N/g" | sort | uniq -c`; `grep -l "Beginning
   Simulation"`, `grep -l "exited before simulations began"`; the failing window against the first
   `FENESTRATIONSURFACE:DETAILED` of each IDF; `Environment:WarmupDays` from every `.eio`; the partial `.eso`
   of each run-period fatal against a completed sibling; `During Sizing: … Severe` line of every completed `.err`.
10. `f181_t04_probes.csv` P0/P1 values against `deu27_rerun_cells.csv` for the 8 T04 cells;
    `openubem/outputs/_tmp_f181/t01/serial/` (uk AB.03 f000, `Timestep 6`, no pool) and
    `_tmp_f181/t04/…SFH.07…f000/P1/`: `cmp` of `.eso` and `epluszsz.csv` across replicates.
11. `C:\EnergyPlusV23-1-0\`: `ls`; `grep -a -o "_vcomp_[a-z_]*\|omp_[a-z_]*" energyplusapi.dll | sort | uniq -c`;
    `grep -n "^ProgramControl\|thread" Energy+.idd`.

## 3. Diagnosis — the evidence

Each line: claim — measurement — source (§2 item). Denominators explicit. M = MEASURED, I = INFERRED.

**A. Harness and post-processing are innocent (H1).**
- M — `eplusout.csv` reproduces `.eso`: the harness column sum and the `.eso` sum of variable 556 agree to 1e-8
  relative in rep1 and rep2 of uk AB.04 f100 (8,760 rows, one matching column) — §2.8.
- M — When two replicates return the same `heating_kwh`, their `.eso` files are byte-identical in 659 of 662
  pairs; the other 3 differ only at line 1, the `YMD=` minute stamp — §2.7.
- M — When two replicates differ, `.eso` differs at line 12 — the first hourly record of `RUNPERIOD1` — in 250
  of 251 pairs; the remaining pair differs at line 3158 (≈ hour 1,574) — §2.7.
- M — No timeout ever fired: 156 of 156 `ENGINE_FAILED` rows carry `return_code = 1`, `fatal_count = 1`, an empty
  `error` column, and an `eplusout.end` reading `EnergyPlus Terminated--Fatal Error Detected` — §2.4, §2.9.

**B. The inputs are identical in content (H4).**
- M — `eplusout.expidf` rep1 vs rep2 vs rep3 (uk AB.04 f100, 41,679 bytes each): exactly one differing line, l.86,
  the `Schedule:File` `File Name` path (`…\rep1\schedules\…` vs `…\rep2\…`) — §2.5.
- M — `schedules/<cell>.csv` byte-identical across replicates (`cmp`); manifests differ only in `created_utc`
  (0–2 s apart), the three run-root paths, `idf_sha256` and the result fields; `epw_path` and `weather_sha256`
  identical — §2.5.
- M — `.shd`, `.bnd`, `.mtd`, `.dbg`, `.mdd`, `.rdd` byte-identical; `.eio` identical except l.94–95
  (`Zone Sizing Information`) and l.107 (`Warmup Convergence Information`); `.audit`, `.rvaudit`, `sqlite.err`
  differ only in embedded paths — §2.5.

**C. The divergence is decided before the first reported hour, and it is visible in zone sizing.**
- M — `epluszsz.csv` differs in 250 of the 251 disagreeing pairs and is byte-identical in 662 of the 662 agreeing
  pairs — §2.7. Sizing agreement ⟺ run agreement, with one exception (E below).
- M — The sizing pass returns different design loads for the same IDF: `.eio` l.95 heating design load
  7602.47 / 7626.57 / 7524.24 W across rep1/rep2/rep3 of it SFH-TH.07 f100, whose three `.err` files are
  identical apart from `Elapsed Time` (10 warnings, 0 severe, all three) — §2.6.
- M — Nothing from sizing is consumed by the run: `ZoneHVAC:IdealLoadsAirSystem` `Heating Limit = NoLimit`,
  `Cooling Limit = NoLimit`, capacity fields blank (`eplusout.expidf` l.743–748); the only `autosize` fields are
  the two DOAS setpoints of `Sizing:Zone` with `Account for Dedicated Outdoor Air System = No` (IDF l.650–653);
  `Run Simulation for Sizing Periods = No` (IDF l.10); `.eio` l.97–98 report `User-Specified Maximum
  Heating/Cooling Air Flow Rate 0.00000` — §2.5.
- I — Therefore the 662/0 and 250/1 concordance is not a parameter chain; sizing and run are two witnesses of
  one per-process condition — or of state carried from the first environment into the second, the only rival
  reading (E1 in §6 separates them).
- M — The signature is invariant to timestep, pool and batch: T01 **serial** uk AB.03 f000 at `Timestep 6`
  (rep1 = rep2 byte-identical `.eso` and `epluszsz.csv`; rep3 differs at `.eso` l.12 and in `epluszsz.csv`);
  T04 P1 it SFH.07 f000 at `Timestep 12` (rep1 vs rep3: l.12, `epluszsz.csv` differs) — §2.10.
- M — Warmup converges either way: 1,026 of 1,029 completed runs report `Environment:WarmupDays, 3` (3 report 4),
  and both members of a divergent pair report `Pass` on all four warmup tests with average temperature
  differences ~2e-15 K — yet their hour-1 heating differs by ~5 % of the larger value (uk AB.04 f100) — §2.5.
- I — Two warmups converging to different periodic states of one model means the model admits more than one
  solution under the same forcing (multi-stability); the per-process condition selects the basin.

**D. The failures are one solver event at one fixed point.**
- M — 156 fatals = 117 `Program halted because of convergence error in SolveForWindowTemperatures` + 6 other
  sizing-stage fatals (2 of them `CalcHeatBalanceInsideSurf: The temperature of 2206222.77 C` / `53721.72 C`) +
  33 run-period `Program terminates due to preceding condition` after `Temperature (high/low) out of bounds`
  severes; 123 of 156 carry `Program exited before simulations began` — §2.9.
- M — All 117 window fatals occur `During Warmup & Sizing, Environment=ANNUALSIZINGPERIOD` on **01/01** at a
  fold-fixed timestep: `it` 08:00 (68/68), `uk` 08:35 (12/12), `es` 08:45 (37/37) — the first sizing day,
  never any of the other 364 days — §2.9. I — that timestep is the first sun-up step of the fold's EPW.
- M — The failing window is the first `FENESTRATIONSURFACE:DETAILED` object of the IDF in 117 of 117 cases
  (`WINDOW_EAST_1` ×100 where the IDF lists east first, `WINDOW_NORTH_1` ×17 where it lists north first) — §2.9.
- M — Sizing-stage severes never occur in a run that later completes: 0 of 1,029 completed `.err` report
  `During Sizing: … Severe` above 0 — §2.9. The runaway branch and the fatal branch are outcomes of the same early
  decision, not later accidents.
- M — The 33 run-period fatals were on a different trajectory from the start: their partial `.eso` differs from a
  completed sibling at or before the first hourly record in 37 of 37 comparisons (31 at l.12, 6 earlier in the
  file); their warmup took 2–24 days (7 at 2, 15 at 3, 11 at ≥ 4) against 3 days for 1,026 of 1,029 completions — §2.9.
- M — Failed runs are fast: `runtime_s` 0.43–3.20 s, median 0.59 (n = 156) against 3.19–5.60 s for completions
  (n = 1,029) — §2.4.

**E. The value divergence is silent and whole-year, not a late excursion.**
- M — it SFH-TH.07 f100 rep1 vs rep2: 5,473 of 8,760 hours differ, first at hour 1, hourly ratio p10–p90
  1.004–1.972, `.err` identical, 0 severe; rep1 vs rep3: 4,840 hours differ, first at hour 1, ratio p10–p90
  0.364–0.989. Even the 0.11 %-spread cell it AB.03 f050 differs in 5,748 of 8,760 hours from hour 1 — §2.8.
- M — Among the 83 cells with three completions and ≥ 2 values, 50 show exactly 2 distinct values and 33 show 3;
  the odd replicate out among the 50 is rep1 15 / rep2 15 / rep3 20 — no positional bias — §2.4, §2.9.
- M — 248 of the 249 completed replicates of those 83 cells carry `severe_count = 0`; the one visible runaway
  (uk AB.04 f100 rep1: `2933 Warning; 98258 Severe Errors` in `.end`, first `Inside surface heat balance did not
  converge` at 04/15, first out-of-bounds at 05/18) is a late symptom of a trajectory that already differed at
  hour 1 — §2.5.
- M — A reproducible reference value exists when the event does not strike: for 7 of the 8 T04 cells, the value
  that was bitwise-stable under probe P1 (`Timestep 12`) recurs bitwise in the certified re-run, a separate batch
  (up to 6 runs per cell); the 8th, it SFH.07 f000, produced 4 distinct values and 2 fatals in 6 runs — §2.10.
- M — The one in-run event: es MFH.06 f015 rep1 vs rep2 — identical `epluszsz.csv`, `.eso` first differs at
  hour 1,574, 4,080 hours differ afterwards at the last-bits level, annual sums equal to 13 significant digits;
  1 of 913 pairs. I — a rare per-timestep bit-level event exists and was not amplified; it is not the dominant
  mechanism.

**F. Associations (H6) — measured, not discriminating.**
- M — Unstable cell (any fatal or any disagreement over 3 replicates) by fold: `uk` 20/95, `it` 116/190,
  `es` 68/110; by class: SFH 52/70, MFH-AB 11/15, SFH-TH 10/15, MFH 56/105, AB 37/85, TH 38/105; by `f`:
  42/79, 38/79, 40/79, 41/79, 43/79 for f000…f100 (flat); by window count and first orientation: 4 windows
  east-first 106/145, 3 windows east-first 27/130, 2 windows north-first 33/40, 3 windows north-first 12/40,
  2 windows east-first 26/40 — §2.4, §2.9. Zone-volume bins do not order the rate (< 1,000 m³ 98/185,
  1,000–3,000 31/75, 3,000–10,000 66/115, ≥ 10,000 9/20).
- M — Object census of one expanded IDF: 6 `BuildingSurface:Detailed`, 3 `FenestrationSurface:Detailed`,
  6 `SurfaceProperty:OtherSideCoefficients`, 1 `InternalMass`, 7 `Material:NoMass`, 1 `Material` — §2.5.
  No object class varies enough across cells to be an amplifier by count.

**G. The binary.**
- M — `energyplusapi.dll` (39,048,704 bytes, 2023-03-28) imports `_vcomp_fork`, `_vcomp_for_static_simple_init`,
  `_vcomp_for_static_end`, `_vcomp_set_num_threads` from `vcomp140.dll`, which ships in the install directory:
  at least one OpenMP parallel-for region is compiled in. `Energy+.idd` has no `ProgramControl` object and no
  thread diagnostic — §2.11.
- I — Whether that region is executed by this model is not determinable from disk. The bitwise identity of
  659/662 agreeing pairs excludes a thread race in any code path executed every timestep; a race confined to
  an initialisation path executed once per process is not excluded (E2, §6).

## 4. Hypotheses

| # | hypothesis | tested | result | discriminator used |
|---|---|---|---|---|
| H1 | harness / ReadVarsESO / timeout | yes | **excluded** | `.eso` differs at l.12 in 250/251; csv sum = eso sum; 0/156 timeouts, 156/156 solver fatals (§3.A) |
| H2 | sensitive dependence in the iterative solver; first differing hour located | yes | **supported in part** — the first difference is the first hourly record (250/251) and the sizing pass (250/251); warmups converge (`Pass`) to different states, so the model is multi-stable; but the *seed* is per-process, not a mid-year amplification of noise | first-differing `.eso` line, `epluszsz.csv`, `.eio` l.107 (§3.C) |
| H3 | genuinely non-deterministic build | yes, bounded | **leading reading, not proven** — discrete per-process event; first-window / first-sun-up locus; bitwise-identical agreeing pairs; an OpenMP region in the DLL; no timing or ordering pattern (`runtime_s`, odd replicate 15/15/20) | §3.C–E, §3.G |
| H4 | inputs not identical | yes | **excluded** | expidf one-line path diff, schedule `cmp`, static outputs identical (§3.B) |
| H5 | environment (AV, filesystem race, disk, `%TEMP%`, timeout) | yes | **excluded** as failure cause; no channel to the value divergence | `.end`, `return_code`, `error` column, fatal texts; T01 serial reproduces the signature (§3.A, §3.C, §3.D) |
| H6 | one object class amplifies | yes | **inconclusive** — fold / class / window-count associations exist, `f` has none; no count-based amplifier | §3.F |
| H7 (own) | a sizing result feeds the run period through an autosized parameter | yes | **excluded** | `NoLimit`, nothing consumed is autosized (§3.C) |
| H8 (own) | state carried from the sizing environment into the run period (un-reset variable) + multi-stability | not testable on disk | **open** — the only rival to H3's per-process reading | E1 (§6) |

## 5. How to solve it

**(a) Make the engine deterministic — each option conditional on §6.**
- a1 *Drop the sizing pass* (`Do Zone Sizing = No`; delete `SizingPeriod:WeatherFileDays` and `Sizing:Zone` —
  three objects in `eu_cell_runner._build_idf`). Changes: every `idf_sha256`; no consumed quantity (§3.C), so
  stable cells must reproduce their bitwise reference value, which is a built-in check. Cost: one 510 × 3 re-run
  (about 1 h at 14 workers, from the measured ~4 s per run). Proves: whether the run period is deterministic once
  the first environment is gone (H8). Does NOT prove: the model well-posed; the run-period runaways may persist.
  Adopt only if E1 is positive.
- a2 *Pin threads* (`OMP_NUM_THREADS=1` in the `subprocess.run` environment of `_run_energyplus`). Cost: one
  line plus the re-run. Proves / does not prove as a1. Adopt only if E2 is positive.
- a3 *Change the binary* (24.2 / 25.x Windows). Cost: `Version` transition of every IDF, the
  `energyplus_version_declared` guard, every hash, a full re-run, every gate re-scored. Proves: whether the event
  is build-specific. Does NOT prove: anything about the equivalent-envelope method; also forfeits comparability
  with every published run.
- a4 *Take the window solver out of the model*: the windows sit on `NoSun` / `NoWind` `Outdoors` hosts
  (`european_box.py` l.113–120 and l.262–270); replacing `FenestrationSurface:Detailed` + `SimpleGlazingSystem`
  by an opaque `Material:NoMass` face of equal U·A removes `SolveForWindowTemperatures` from the run. Cost: a
  DESIGN ruling (what the g-value then means), `european_box.py`, every hash, a re-run. Proves: whether the window
  solver is the seat of the first-call event. Does NOT prove: the massless envelope stable — the 33 run-period
  runaways are surface heat-balance events. Not to be adopted without E5.

**(b) Make the harness tolerant.**
- b1 *n = 10 bitwise-mode certification*. Cost: 3.3 × the re-run. Proves nothing about the mechanism; stays
  luck-driven (`FINDING 191`). Not recommended.
- b2 *Sizing-only replicate screen*: run replicates with `Run Simulation for Weather File Run Periods = No` and
  compare `epluszsz.csv` digests; a sizing-stage exit costs ~0.5 s (measured on the 123 sizing-stage exits) against
  ~4 s for a full run, so ten screens cost about one full run. Justified by the 662/662 and 250/251 concordance —
  MEASURED with the run period present, INFERRED to hold without it (E1/E3 verify). Proves: cheap detection of a
  divergent cell. Does NOT prove: that any value is right.

**(c) Declare the non-determinism and quote only what survives it.** Keep the `D-EU-31` position — fold
aggregates over cells complete in every replicate — and state it as a property of the build: cell values are
draws from a per-process distribution decided before the first simulated hour. Cost: none. Proves: nothing new.
Does NOT prove: that the fold aggregate is unbiased (basin selection need not be symmetric).

**Recommendation, one sentence:** run E1 and E2 (60 runs, minutes) before any other spend, because they decide
between a1/a2 — which would restore reproducibility without changing a single consumed quantity — and (c),
which is the only honest standing position if both are negative; do not fund b1.

## 6. What I could NOT determine

1. **The first differing timestep inside the sizing pass.** `epluszsz.csv` holds one day's profile, so the
   first divergent step is bounded only by the 117 fatals (day 1, first sun-up). E3: one cell
   (it SFH-TH.07 f100) × 10 replicates with `Run Simulation for Sizing Periods = Yes` and `Output:Variable` at
   `Timestep` for `Surface Inside Face Temperature` and the heating variable — 10 runs, ~50 s.
2. **Per-process condition vs state carry-over (H3 vs H8).** E1: three cells (uk AB.04 f100, it SFH-TH.07 f100,
   it SFH.07 f000) × 10 replicates with the sizing objects removed — 30 runs. Divergence persists → H8 dead and
   H3 stands; divergence vanishes → H8 is the channel and a1 is a remedy.
3. **Whether the OpenMP region is exercised.** E2: the same 30 runs with `OMP_NUM_THREADS=1`, and 30 with
   `OMP_NUM_THREADS=14`. Rate unchanged → threading excluded.
4. **Whether the event is build-specific.** E4: the same IDF (after `Version` transition) × 10 on the 24.2 Linux
   engine — diagnostic only, not certifiable (`STATE` §3).
5. **Whether the windows receive any solar.** Their hosts are `Sun_Exposure = NoSun`; INFERRED from the
   EnergyPlus inheritance rule that the SHGC is then inert — a DESIGN witness, not this finding. E5: one run
   reporting `Zone Windows Total Transmitted Solar Radiation Energy`.
6. **4J's ten-replicate arms** live in their repository; nothing from them is assumed here beyond the prompt's own
   statements.
7. The `es`-only `PsyPsatFnTemp` marker (`FINDING 182`) was not investigated; it is confounded with the fold.

Total proposed: ≤ 120 EnergyPlus runs, each under 10 s, none executed here.

## 7. Files I created

Exactly one: `docs/docs_ACTIVE/europeanLocations/debugs/docs/FINDING181_REPORT_fable5_2026-08-28.md` (this file).
Nothing under `openubem/` was written; the retained run tree was read only; nothing staged or committed.
