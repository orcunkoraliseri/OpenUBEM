# INVESTIGATION PROMPT — `FINDING 181`: why does the same IDF give a different answer each time?

**Give this whole file to one model. Run it once per model, independently.**
Intended executors: Fable 5, Gemini 3 Flash, Codex, and any other agent with read access to this
repository. Each produces its own report; the reports are compared afterwards by the OpenUBEM
manager session. **Do not read another model's report before writing your own.**

Repository root: `C:\Users\o_iseri\Desktop\OpenUBEM`
Date: 2026-08-28. Arc: European locations (`EU-01`–`EU-10`, all Completed).
`FINDING 181` is the arc's **only remaining open item**.

## 🔴 THIS TASK IS DOCUMENTATION ONLY

**You will not run EnergyPlus. You will not run the campaign. You will not write, edit or execute
any `.py` file. You will not change a single line of source.** You read what is already on disk,
you diagnose, and you write **one markdown document**. Reading files and running read-only shell
inspections (`grep`, `head`, `sed -n`, `wc`, `python -c` for arithmetic on an existing CSV) is
allowed and encouraged. Anything that produces a new simulation result is out of scope.

Your deliverable has three parts, in one file: **(1) investigation, (2) diagnosis,
(3) how to solve it.** Part 3 is a *written proposal*, not an implementation.

---

## 0. Your identity tag

Pick your tag: `fable5`, `gemini3flash`, `codex`, or `other-<shortname>`. Use it as `<TAG>`.

You create **exactly one file**:

`docs/docs_ACTIVE/europeanLocations/debugs/docs/FINDING181_REPORT_<TAG>_2026-08-28.md`

Nothing else. No scripts, no CSVs, no scratch files, no "helpful extras". A `.py` file anywhere
under `docs/` is forbidden in this repository, always.

---

## 1. The phenomenon, stated precisely

EnergyPlus 23.1.0-87ed9199d4 (Windows) is run on a campaign cell: one IDF, one EPW, one binary,
one host. **Re-running the identical cell does not reproduce the previous result.** Two distinct
failure modes, both measured, both live:

1. **`completed` is a random variable, not a cell attribute.** The same cell completes in some
   replicates and returns `ENGINE_FAILED` in others. Measured: **78 of the 149** certified cells
   failed to complete in at least one of ten re-runs; per-replicate `engine_failed` count 8–18,
   with no trend.
2. **`heating_kwh` is a continuum, not a coin flip.** Over ten replicates a single cell reaches up
   to **8 distinct values**; 52 of 90 diagnostic cells show ≥ 3. Worst observed spread:
   `es …MFH.06…f015` **79.11 %** (8 states), `it …MidClim.TH.07…f015` 35.16 % (4 states).
   Inside the *certified* perimeter, **53 of 149 (35.6 %)** produce more than one value over ten
   re-runs (`it` 30/74, `uk` 23/75); worst `uk …AB.04…f050` **79.14 %**.

Consequence already ruled: no cell-level number from this campaign may be quoted, ranked or
tabulated. Only fold-level aggregates survive, and only because per-cell chaos averages out
(`it` fold spread 0.157 % over ten independent re-runs).

**The mechanism is unidentified. That is what you are asked to find, or to bound.**

---

## 2. What is already excluded — do not re-derive these

Each line is a measured result, not an opinion. **Your report is judged on what it adds beyond
this list.** Re-stating these as findings counts against you.

- **Not worker contention.** Power-matched: 52/85 (61.2 %) divergent at `--workers 14` vs
  47/83 (56.6 %) at `--workers 1`. `uk` is *identical* serially (1/11 vs 1/10). Set overlap
  37 both / 15 parallel-only / **10 serial-only** — the divergent sets are not even nested.
  Worker count moves the *rate*, not the *phenomenon*.
- **Not visible in the error file.** The `.err` warning-kind set differs across replicates in
  **0/149, 0/54 and 1/28** cells. A clean `.err` plus `completed: true` is **not** sufficient:
  `uk__GB.ENG.AB.03__f000` passes both and still moves −74 %.
- **Not `fixviewfactors` alone.** Associated but **neither necessary nor sufficient**: the warning
  kind **never appears in `uk` at all**, yet 23/75 `uk` cells diverge, and 10 of 47 divergent `it`
  cells carry none. ⚠ **The odds ratio 4.12 has been STRUCK and must never be quoted** — it was a
  detection-power artefact of 3-replicate labelling. The qualitative conclusion stands; the effect
  size does not. **A second, `fixviewfactors`-independent mechanism therefore exists.**
- **Not curable by past behaviour.** A control that returned 9/9 identical values returned 3
  distinct values on the very next batch.
- **Envelope probes P0–P5 have already been run** (definitions in
  `scripts/diagnostics/f181_t04_envelope_probes.py:126-198`, results in
  `docs/docs_ACTIVE/europeanLocations/outputs/f181_t04_probes.csv`):
  P0 control · P1 `Timestep 12` · P2 `SurfaceConvectionAlgorithm:Inside = Simple` ·
  P3 explicit uniform `ZoneProperty:UserViewFactors:BySurfaceName` · P4 `InternalMass` area × 3 ·
  P5 raise sub-minimum `Material:NoMass` resistances. `Timestep 12` collapsed 3 of 4 unstable cells
  and moved both controls by **0.0 %**; every other probe moved a control by 1.6–16.9 %.
  `it__IT.MidClim.SFH.07__f000` **resists every probe including `Timestep 12`** (10.3 % spread).
- **Flipping the S0 floor surface normals was tried and REVERTED.** It cleared the tilt warning and
  turned a 3-of-3-identical cell into one fatal in three. **Do not propose re-trying it without
  new evidence.**
- **`idf_sha256` is not a model identity**: it embeds the absolute `Schedule:File` path
  (`openubem/semantic/european_schedules.py:119`), so digests differ between run roots for an
  identical model. Reason about model *content*, never about this digest.

---

## 3. How a cell is actually run — read this code before hypothesising

- `openubem/campaign/eu_cell_runner.py` (640 lines), `run_campaign_cell()` at line 452.
  - Engine call, line 433: `energyplus -x -r -w <epw> -d <run_dir> <idf>`, `cwd=run_dir`,
    `capture_output=True`, `timeout=900 s`.
  - `heating_kwh`, line 406: parsed from **`eplusout.csv`** — every column matching
    *"zone ideal loads zone total heating energy"* and `[j]` and `(hourly)`, summed over all rows,
    converted by `ENERGYPLUS_J_TO_KWH`. Note `eplusout.csv` is written by **ReadVarsESO** (`-r`),
    a post-processing step, not by the simulation itself.
  - Status, lines 554–563: `ENGINE_FAILED` iff `return_code != 0` **or** `fatal_count` **or**
    `heating_kwh is None`; otherwise `COMPLETED`. Severe warnings do **not** fail a run here.
  - `_energyplus_exe()` line 426 — `ENERGYPLUS_PATH` is the **install directory**, not the exe.
- `scripts/campaign/run_eu_certified_rerun.py` — the driver: 3 replicates, one run directory each,
  `ProcessPoolExecutor`, run root `openubem/outputs/eu_certified_rerun_2026-08-28/`.
- `openubem/idf/european_box.py:46-57` — the geometry contract. The zone is **deliberately
  unenclosed** (`EquivalentEnvelope`), which is what produces
  `FixViewFactors: View factors not complete` and opaque equivalent surfaces on `OtherSideCoefficients` (window opening hosts assigned `Outdoors`).
  **This is a design choice, and it is an unruled DESIGN question — you may analyse it, you may
  recommend a ruling, you may not treat it as a settled bug.**

---

## 4. The evidence already on disk

Under `docs/docs_ACTIVE/europeanLocations/outputs/`:

| file | rows | what it holds |
|---|---|---|
| `deu27_rerun_cells.csv` | 1 530 | the certified re-run: every cell × 3 replicates — `completed`, `completion_status`, `return_code`, `severe_count`, `fatal_count`, `heating_kwh`, `runtime_s`, `marker_psy`, `marker_inside_hb`, `marker_calchb`, `idf_sha256`, `error` |
| `f181_t01_matrix.csv` | 108 | serial-vs-parallel matrix (`mode`, `replicate`) |
| `f181_t03_cells.csv` | 510 | the `.err` screen over the whole 510-cell spec |
| `f181_t04_probes.csv` | 144 | probes P0–P5 × cells × replicates |
| `deu27_certified_cells.csv`, `deu27_per_archetype.csv` | | the certified perimeter and its per-archetype roll-up |

Retained run directories: `openubem/outputs/eu_certified_rerun_2026-08-28/{rep1,rep2,rep3}/` —
real `eplusout.err`, `.csv`, `.eso`, `.end` per cell.
**READ-ONLY. Never write into it, never delete from it.**

The ten-replicate arms (arms 1–3, host `tabletop1`) were executed by GSSCanada 4J and live in
**their** repository, not this one. If you cannot read them, say so — **do not invent their
contents**, and do not assume a number you cannot open.

Context documents worth reading, in this order:
1. `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v2.md` §3 — all open findings.
2. `docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md` §7 — the T01–T05 notes.
3. `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_deu27-timestep12-rerun-2026-08-28.md` §5.
4. `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` — ~200 documented errors, symptom → cause → fix. **Search it before you theorise about any error string.**

---

## 5. Hypotheses worth attacking — all answerable from disk

You are not limited to these, and you must rank them yourself.

- **H1 — the harness, not the engine.** The divergence is introduced *after* the simulation:
  ReadVarsESO writing `eplusout.csv` while the parent reads it, a truncated or partially flushed
  csv, a column set that differs between runs, encoding, or the 900 s timeout firing.
  *Discriminator available on disk:* compare `eplusout.eso` (engine output) against `eplusout.csv`
  (post-processed) for the same cell across `rep1`/`rep2`/`rep3`. If the `.eso` agrees where the
  `.csv` does not, the engine is innocent. **Nobody has published this comparison yet.**
- **H2 — sensitive dependence in an iterative solver on an unenclosed zone.** `FixViewFactors`
  iterates; the inside-surface heat balance may fail to converge; a tiny difference amplifies over
  8 760 hours. *Discriminator on disk:* locate the **first hour** at which two replicates of one
  cell differ. Divergence during warmup/sizing is a different disease from divergence mid-year.
- **H3 — the build is genuinely non-deterministic.** Uninitialised memory, container iteration
  order, address-dependent behaviour, or threading inside E+ 23.1. *On disk:* the `.end` files,
  the `runtime_s` distribution, and the warmup-convergence lines of the `.err`.
- **H4 — the inputs were never identical.** `Schedule:File` reads external CSVs by absolute path;
  `-x` expands objects before the run; EPW/DDY/IDD may differ between run roots. *On disk:*
  compare the expanded IDF, the EPW path and the schedule CSVs between two divergent replicates.
- **H5 — the environment.** Antivirus touching files mid-run, a filesystem race between concurrent
  run directories, disk pressure, `%TEMP%` collisions. *On disk, and unexploited:* **read what the
  `ENGINE_FAILED` runs actually say** — their `eplusout.end`, their non-zero `return_code`, their
  `error` column. Nobody has yet published what the failing runs report.
- **H6 — one object class is the amplifier.** `InternalMass`, opaque faces on `OtherSideCoefficients`,
  window openings on `Outdoors` hosts (`openubem/idf/european_box.py:281-284`),
  `ZoneHVAC:IdealLoadsAirSystem` autosizing. *On disk:* correlate divergence magnitude against
  object counts in the IDFs already written.

**Everything above is answerable without a single new simulation. That is the point.**

---

## 6. Hard rules — violating any one invalidates your report

1. **Documentation only.** No EnergyPlus run, no campaign run, no new `.py` file, no edit to any
   existing file except the one report you create. No `pip install`. No network. No cluster.
2. **Never commit, never stage, never `git add`.** Git is handled outside this session.
3. **Never modify anything under `openubem/`,** and never write into
   `openubem/outputs/eu_certified_rerun_2026-08-28/`.
4. **Never re-score a gate, never re-emit the gate report or the dossier, never touch an
   `idf_sha256`.**
5. **Produce no quotable number.** This is a diagnostic: no perimeter, no band, no gate verdict,
   no EUI. If your reasoning would license a number, stop and say so instead.
6. Every percentage you write **carries its denominator**. If you did not measure it, do not state
   it. Distinguish *measured* from *inferred* in every sentence.
7. **Bare `python` is the Windows Store stub** — if you need arithmetic, use
   `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`, read-only, on existing CSVs.
8. **Create nothing that was not asked for here.** One file, §0. If something extra seems needed,
   write one sentence in §7 of your report saying so — do not create it.
9. If this prompt or the DESIGN is ambiguous, **stop and quote the conflict** — never invent.

---

## 7. Deliverable — write exactly these sections, in this order

File: `docs/docs_ACTIVE/europeanLocations/debugs/docs/FINDING181_REPORT_<TAG>_2026-08-28.md`

```
# FINDING 181 — investigation, diagnosis and remedy — <TAG> — 2026-08-28

## 1. Verdict
One paragraph. Either: the mechanism is X, and here is the discriminating evidence.
Or: the mechanism is not identified, and here is what is now EXCLUDED that was not
before. A clean exclusion is a real result. A guess presented as a finding is not.

## 2. Investigation — what I read
Numbered. Every file opened, every read-only command verbatim, every table inspected.

## 3. Diagnosis — the evidence
Each claim as: claim — the measurement — the file:line or command that produced it.
Every count and percentage carries its denominator. Mark each line MEASURED or INFERRED.

## 4. Hypotheses
One row per hypothesis H1–H6 plus any of your own:
tested / not tested — supported / excluded / inconclusive — the discriminator used.

## 5. How to solve it
The remedy, as a written proposal only. Give at least two options, and for each:
what it changes, what it costs, what it would prove, and what it would NOT prove.
Distinguish (a) making the engine deterministic, (b) making the harness tolerant of a
non-deterministic engine, and (c) declaring the non-determinism and quoting only what
survives it. Say which you recommend, in one sentence, and why.

## 6. What I could NOT determine
Explicit. What data you lacked, and the single cheapest experiment that would settle it —
stated as a proposal, with its cost in EnergyPlus runs. You do not run it.

## 7. Files I created
Should be exactly one: this report.
```

Length target 2–4 pages. No re-derivation of §2 of this prompt. No EUI.

---

## 8. What separates a good report from a bad one

**Good:** *"H1 is excluded. `rep1` and `rep3` of cell C hold `eplusout.eso` files that already
differ, at the record for hour H — so the divergence exists in engine output, before ReadVarsESO
ever runs, and the csv post-processing is innocent. Command: … "*

**Bad:** *"the non-determinism is likely due to floating-point ordering."*

The most valuable thing you can produce is a **discriminating observation that survives being
checked** — including one that proves your own leading hypothesis wrong. The second most valuable
is an honest §6.
