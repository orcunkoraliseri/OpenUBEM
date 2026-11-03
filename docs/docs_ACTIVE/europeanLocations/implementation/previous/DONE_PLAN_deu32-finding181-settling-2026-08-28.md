# PLAN — `D-EU-32` execution: the `FINDING 181` settling experiment (E0 / E1 / E2)

**Slug:** `deu32-finding181-settling`
**Date:** 2026-08-28
**Authority:** `D-EU-32` ruled **Option A** by the owner on 2026-08-28 — see
`docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-32_finding181_settling_experiment_2026-08-28.md` §7.
**Predecessors:** `implementation/previous/PLAN_finding181-stability-2026-08-28.md` (T01–T05, complete),
`implementation/previous/PLAN_deu27-timestep12-rerun-2026-08-28.md` (complete).
**Read-first:** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v2.md` §3.
**DESIGN pointer:** `previous/MVP_european_locations.md` §9.4, §9.7 (FROZEN — never appended to).

**Scope in one line.** Decide between **H3** (a per-process condition in the EnergyPlus 23.1 Windows
build) and **H8** (state carried from the sizing environment into the run period) by 90 local runs.
**This plan produces no quotable number of any kind.**

---

## 2. Hard rules for the executor

1. **Execute this document top to bottom. Do not propose alternatives.** If the DESIGN is ambiguous, STOP
   and quote the conflict.
2. **No quotable number may leave this plan.** No EUI, no fold aggregate, no band, no perimeter, no gate
   verdict. The deliverable is a verdict on two hypotheses and nothing else. The campaign re-run budget
   stays **SPENT**; this is not a campaign.
3. **Scratch only.** All runs go under `openubem/outputs/_tmp_f181/t05/`.
   `openubem/outputs/eu_certified_rerun_2026-08-28/` is **read-only** — never written, never deleted from,
   never added to.
4. **No file under `openubem/` is modified.** The E1 mutation is applied to a *copy* of the built IDF
   inside the scratch arm and is **never** written to `eu_cell_runner.IDF_HEADER_TEMPLATE`. Adopting any
   remedy requires a separate ruling.
5. **No gate is re-scored, no perimeter moves, no `idf_sha256` is regenerated** for any promoted artefact.
6. **`.venv/Scripts/python.exe` always.** Bare `python` on this machine is the Windows Store stub.
7. **Never commit.** Git is handled outside this session.
8. **Do not annotate MVP Table 9.7.** Status cells only; all notes go to `STATE v2` §3 and the progress log.
9. **Local host only, serial.** No cluster, no `sbatch`, no network, no job submission — see §5 fact 6.
10. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`; after solving
    one, register it there before closing the task.

---

## 3. File layout

- Harness: `scripts/diagnostics/f181_t05_settling_experiment.py` (new; the only new file authorised).
- Run root: `openubem/outputs/_tmp_f181/t05/{_built,E0,E1,E2}/<cell_id>/rep<N>/`.
- Table: `docs/docs_ACTIVE/europeanLocations/outputs/f181_t05_probes.csv`.
- Write-up: `STATE_european_locations_v2.md` §3; `content/walkthrough_progress_log.csv`;
  `prompts/DIRECTOR_PROMPT_european_locations.md` SEC block.
- Archive: the investigation prompt moves from `debugs/` to `debugs/DONE/PROMPT_finding181_investigation_2026-08-28.md`.

---

## 4. Dependency decisions (pinned)

- EnergyPlus **23.1.0-87ed9199d4**, Windows, host `tabletop1`. No other version, no other host.
  **No two-host claim is available from this plan and none may be made.**
- Spec `openubem/data/campaign/eu_campaign_cell_spec_v1.1.json`, sha256
  `16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6`, asserted by the harness.
- `Timestep,12` — the `D-EU-27` Option B campaign setting. Unchanged; the experiment is run on the same
  configuration the divergence was measured on.
- The three cells, fixed by `D-EU-32` §7 and not re-selected:
  `uk__GB.ENG.AB.04.Gen.ReEx.001.001__f100`,
  `it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100`,
  `it__IT.MidClim.SFH.07.Gen.ReEx.001.001__f000`.
- **10 replicates per cell per arm**; each replicate gets its **own** run directory.
- The IDF is **built once per cell** and copied per replicate — so an input difference cannot be
  confounded with the effect being measured (`FINDING 193`, H4 already excluded).

---

## 5. Facts this plan is built on, with citations

1. `FINDING 193` — H1 (harness / ReadVarsESO), H4 (non-identical inputs) and H5 (environment / timeout)
   are excluded by three independent external investigations; H6 is not a count effect (`r < 0.06`).
   (`STATE v2` §3; the three reports under `debugs/docs/DONE-resultReports/`.)
2. `FINDING 194` — the divergence is decided **before the first simulated hour**: `epluszsz.csv` differs in
   250 of 251 disagreeing replicate pairs and is byte-identical in 662 of 662 agreeing pairs; the
   `eplusout.eio` design heating load differs in 83 of 83 divergent cells. (`STATE v2` §3.)
3. **Nothing computed in sizing is consumed by the run period** — `ZoneHVAC:IdealLoadsAirSystem` is
   `NoLimit` on heating and cooling with blank capacity fields (`openubem/idf/european_controls.py:88-89`,
   verified by this session), `Run Simulation for Sizing Periods = No`
   (`openubem/campaign/eu_cell_runner.py:57-59`), `.eio:97-98` user-specified maximum air flow `0.00000`.
   This is exactly why E1 is decisive: if sizing shares nothing, removing it should change nothing —
   unless H8 is true.
4. `energyplusapi.dll` imports `_vcomp_fork` / `_vcomp_set_num_threads` from `vcomp140.dll`, so an OpenMP
   region is compiled in; whether this model executes it is **not determinable from disk**. That is the
   whole of E2. (`FINDING181_REPORT_fable5_2026-08-28.md` §2.11.)
5. `FINDING 190` — it is **not** worker contention: power-matched replicates diverge. Therefore the arms
   are run **serially**, and parallelism is not reintroduced as a confound.
6. Measured cost: every run in the `D-EU-27` re-run finished under **5.604 s** against a 900 s timeout
   (`outputs/deu27_rerun_cells.csv`, re-derived by this session). **90 runs is under ten minutes serial on
   one workstation** — which is why no cluster is used, and why using one would be wrong: Speed is Linux
   with a different EnergyPlus binary, so runs there test a different build and cannot address H3.
7. Window opening hosts are `outside_boundary_condition="Outdoors"`, **not** `OtherSideCoefficients`
   (`openubem/idf/european_box.py:281-284`) — the error codex found in our own investigation prompt.
   Floor / roof / equivalent opaque faces use `OtherSideCoefficients`.

---

## 6. Tasks

### T01 — build the three-arm harness

**What.** `scripts/diagnostics/f181_t05_settling_experiment.py`: build each of the three cells once via
`run_campaign_cell(dry_run=True)`, then for each arm × cell × replicate copy the built IDF into its own run
directory, apply the arm, invoke EnergyPlus directly, and record one row.
**Why.** `D-EU-32` Option A. Building once and copying removes H4 by construction.
**How.** Arms:
- **E0 — baseline control, no mutation.** *Added to the ruled design, and load-bearing:* without a
  same-session control, a null E1 could be an artefact of this session rather than a property of the
  sizing pass. E0 is what E1 and E2 are compared against.
- **E1 — sizing disabled.** `SimulationControl` `Do Zone / Do System / Do Plant Sizing = No`,
  `Run Simulation for Sizing Periods = No`; all `SizingPeriod:WeatherFileDays` and
  `SizingPeriod:DesignDay` objects removed.
- **E2 — `OMP_NUM_THREADS=1`** in the child environment only. IDF unmutated.

Row schema: `cell_id,survey_fold,arm,replicate,applied,completed,completion_status,return_code,`
`severe_count,fatal_count,heating_kwh,runtime_s,marker_psy,marker_inside_hb,marker_calchb,error`.
`heating_kwh` is written with `repr()` so no digit is lost to formatting — a bitwise question cannot be
scored off a rounded column.
**How to test.** Spec sha256 assertion passes; all three `cell_id`s resolve in the spec; the E1 arm's saved
IDF contains no `SizingPeriod:` object and three `No` sizing flags; the E0 and E2 IDFs are byte-identical
to the built one.

### T02 — execute the 90 runs

**What.** 3 arms × 3 cells × 10 replicates = **90 runs**, serial, into `_tmp_f181/t05/`.
**Why.** Fact 5: serial is a requirement, not a convenience.
**How.** Run to completion in one invocation; emit `outputs/f181_t05_probes.csv`.
**How to test.** Exactly 90 rows. `applied` true on all 90. Zero timeouts. Any `EXCEPTION` row is a harness
failure, not a result — STOP and report it rather than scoring around it.

### T03 — score the two hypotheses (decision rule fixed **before** the results are read)

**What.** Per `cell_id × arm`: completed count out of 10, number of **distinct** `heating_kwh` values over
the completed replicates, and the spread as a percentage of the mean.
**Why.** This is the entire deliverable.
**How — the verdicts, pinned here so they cannot be chosen after the fact:**
- **E0 must reproduce the known behaviour.** If E0 returns a single distinct value on all three cells, the
  experiment is **inconclusive on this session** and E1/E2 may not be read as positive. Report that and stop.
- **E1 positive (H8 is the channel, H3 recedes)** ⟺ E0 is divergent and E1 gives **1 distinct value on all
  three cells with 10/10 completed**. Anything less than that is **not** a positive — a reduction in spread
  is not a verdict, and must be reported as "unchanged in kind".
- **E1 negative (H8 dead, H3 stands)** ⟺ E1 still shows more than one distinct value, or still fails runs,
  on any cell that diverged in E0.
- **E2** screens threading only: rate and pattern indistinguishable from E0 ⟹ OpenMP excluded as the
  mechanism. E2 may **never** be read as a remedy.
**How to test.** The distinct-value count is computed from the `repr()` strings, not from rounded floats;
assert this in the script rather than eyeballing the table.

🛑 **STOP-AND-REPORT — after T03, before T04.** Report the 9 cell × arm rows and the three verdicts. Write
no `STATE`, register or MVP text until the director has read them.

### T04 — record the outcome

**What.** Append to `STATE v2` §3 as `FINDING 195` the E1/E2 verdict, in the form "H8 is / is not the
channel; H3 stands / recedes", with the run counts and the pinned decision rule quoted. Update the
`FINDING 181` status line: it closes **only** if T03 returns a clean E1 positive **or** a clean double
negative; any inconclusive result leaves it OPEN and says so. Add the progress-log row
(`content/walkthrough_progress_log.csv`) and the director-prompt SEC block.
**Why.** `D-EU-32` §5.
**How to test.** No number in `STATE v2` §3 that is not in `f181_t05_probes.csv`. No gate verdict, no
perimeter and no EUI appears anywhere in the new text. Next free identifiers advance to `D-EU-33` /
`FINDING 196`.

### T05 — correct and archive the investigation prompt

**What.** In `debugs/DONE/PROMPT_finding181_investigation_2026-08-28.md`, correct the remaining
`OtherSideCoefficients` statement about window hosts (fact 7) in place, then move the file to
`debugs/DONE/`.
**Why.** `D-EU-32` §5 item 3: the prompt must not be re-used uncorrected, and the investigation it drove is
finished.
**How to test.** `grep -n OtherSideCoefficients` over the archived file returns only statements about
floor / roof / equivalent opaque faces. Per OPEN-33, every citation of the old path is swept and repaired —
**resolve by filename, not by rewriting the path prefix.**

---

## 7. Progress log

*(one entry per task: `#### TXX — <title> — completed YYYY-MM-DD`, then Artifacts / Deviations / Test status / Notes)*

#### T01 — Three-arm harness (E0 / E1 / E2) — completed 2026-08-28

**Artifacts** — `scripts/diagnostics/f181_t05_settling_experiment.py` (305 lines). Builds each cell once via
`run_campaign_cell(dry_run=True)` into `_tmp_f181/t05/_built/`, copies the built IDF per replicate, applies the arm,
invokes EnergyPlus directly with a 900 s timeout, and writes `outputs/f181_t05_probes.csv`.

**Deviations** — one, and it is an addition, not a substitution: **arm E0** (unmutated baseline control, same session)
was added to the 60 runs ruled in `D-EU-32`, taking the total to **90**. Without it a null E1 would not be readable.
Scratch-only, so the ruling's cost and safety constraints are unaffected.

**Test status** — spec sha256 assertion passes; all three `cell_id`s resolve; `heating_kwh` written via `repr()`.

**Notes** — E1 applies the mutation through `geomeppy`/`eppy` on the *copy*; `IDF_HEADER_TEMPLATE` is untouched.
E2 sets `OMP_NUM_THREADS=1` in the child environment only, leaving the IDF byte-identical to E0's.

#### T02 — 90 runs executed — completed 2026-08-28

**Artifacts** — `outputs/f181_t05_probes.csv`, **90 rows**, run root `openubem/outputs/_tmp_f181/t05/{E0,E1,E2}/`.
Elapsed **206.8 s** serial.

**Deviations** — none. Nothing under `openubem/outputs/eu_certified_rerun_2026-08-28/` was read-write, and no file
under `openubem/` was modified.

**Test status** — 90 of 90 rows with `applied = True`; **0 timeouts, 0 `EXCEPTION` rows**; longest run **3.887 s**
against the 900 s timeout.

#### T03 — Scoring against the pinned decision rule — completed 2026-08-28

**Artifacts** — the 9 `cell × arm` rows, re-derived independently by this session from
`f181_t05_probes.csv` (distinct values counted off the `repr()` strings, not rounded floats):

| arm | cell | completed | distinct `heating_kwh` | spread |
|---|---|---|---|---|
| E0 | `it…SFH-TH.07…f100` | 9/10 | 4 | 28.56 % |
| E0 | `it…SFH.07…f000` | 6/10 | 4 | 26.80 % |
| E0 | `uk…AB.04…f100` | 8/10 | 1 | 0.00 % |
| E1 | `it…SFH-TH.07…f100` | 8/10 | 5 | 40.58 % |
| E1 | `it…SFH.07…f000` | 9/10 | 5 | 34.30 % |
| E1 | `uk…AB.04…f100` | 8/10 | 2 | 87.97 % |
| E2 | `it…SFH-TH.07…f100` | 7/10 | 4 | 27.25 % |
| E2 | `it…SFH.07…f000` | 6/10 | 4 | 15.33 % |
| E2 | `uk…AB.04…f100` | 8/10 | 2 | 0.03 % |

**Verdicts, against §6 T03 as written before the results were read:**
- **E0 reproduces the known behaviour** (4 states on both `it` cells, 2 of 10 `uk` runs failing) → the session is
  readable and E1/E2 are scoreable.
- **E1 is NEGATIVE — `H8` is REFUTED.** Divergence and stochastic engine failures persist on all three cells, and on
  `uk…AB.04…f100` they get *worse* (1 state → 2 states, 87.97 % spread). Sizing was a witness, not the channel.
- **E2 is indistinguishable from E0 → OpenMP threading is EXCLUDED** as the mechanism. E2 is not a remedy and is not
  recorded as one.

**Test status** — the E1 mutation is **verified to have taken, not assumed**: the saved E1 IDF carries 0
`SizingPeriod:` objects and all four sizing flags `No`, and `epluszsz.csv` is **absent from every E1 run directory and
present in every E0 one**. This is the control that makes the negative readable.

**Notes** — ⚠ no number in this table is quotable: no EUI, no fold aggregate, no band, no gate verdict. These are
three cells run to answer two hypotheses, and nothing else.

#### T04 — Outcome recorded — completed 2026-08-28

**Artifacts** — `STATE_european_locations_v2.md` §3 `FINDING 195` (E0 control arm and the mutation-verification
control added by this session); `content/walkthrough_progress_log.csv` row `F181-T05-SETTLING-EXPERIMENT-EXECUTED`;
`prompts/DIRECTOR_PROMPT_european_locations.md` status line.

**Deviations** — one, on audit: the first draft of `FINDING 195` attributed the mechanism to ASLR and floating-point
contraction. **That channel is not measured by this experiment** and the text was bounded to what E1/E2 license —
per-process and internal to the 23.1 Windows binary, neither sizing nor threading nor harness/inputs/environment.

**Test status** — every number in the new `STATE` text is present in `f181_t05_probes.csv`. No gate re-scored, no
perimeter moved, no `idf_sha256` regenerated. Next free identifiers advance to `D-EU-33` / `FINDING 196`.

**Notes** — `FINDING 181` closes as **declared and bounded**, on the clean double negative anticipated in `D-EU-32`
§4 Option A. `D-EU-31` / `FINDING 192` stand permanently for S0: cell-level claims barred, `it` = 108.25 kWh/m²
± 0.16 % retained. Closed-prism geometry is the standing recommendation for S1–S3, not a `FINDING 181` remedy.

#### T05 — Investigation prompt corrected and archived — completed 2026-08-28

**Artifacts** — `debugs/DONE/PROMPT_finding181_investigation_2026-08-28.md`. The `H6` line no longer says the windows
sit on `OtherSideCoefficients`: opaque faces use `OtherSideCoefficients`, window openings sit on `Outdoors` hosts
(`openubem/idf/european_box.py:281-284`).

**Deviations** — none.

**Test status** — `grep -n OtherSideCoefficients` over the archived file returns only opaque-face statements. Per
OPEN-33 the citation sweep is done and **resolved by filename**: 5 citing files repaired (the `D-EU-32` decision
request, the three external reports, this plan); `grep` for the old path returns nothing.

---

## 8. Notes added after closure (2026-08-28)

**8.1 — The `H3` wording is bounded, and the executor summary is not.** The execution report circulated after T04
states the diagnosis as *"process memory layout (ASLR) / compiler floating-point instruction ordering perturbs
Gauss-Seidel relaxation iterations"*. **That sentence may not be quoted.** E1 and E2 are two negatives: they exclude
the sizing environment and OpenMP threading. Neither measures ASLR, floating-point contraction, or uninitialised
state, and no probe in `f181_t05_probes.csv` distinguishes them. What the experiment licenses is exactly this: the
non-determinism is **per-process and internal to the EnergyPlus 23.1 Windows binary** acting on the ill-conditioned
S0 equivalent envelope — not the harness, not the inputs, not the environment, not sizing, not threading. The
specific channel is **not measured**. `STATE_european_locations_v2.md` §3 `FINDING 195` carries the bounded text;
this note records why the two differ.

**8.2 — `E0` is a session control, not a result.** Arm `E0` was added beyond the 60 runs ruled in `D-EU-32` (60 → 90).
Without it a null `E1` would be unreadable: it establishes that the divergence reproduces in this session before any
mutation is applied. `E0` produces no claim of its own and is cited nowhere outside this plan.

**8.3 — Why the negative is readable.** The `E1` mutation was verified on the saved IDF, not assumed: **0**
`SizingPeriod:` objects remain, all four sizing flags read `No`, and `epluszsz.csv` is **absent from every `E1` run
directory and present in every `E0` one. A sizing-off arm that silently still sized would have produced the same
null for the opposite reason.

**8.4 — Speed was offered and declined, with a reason.** The cluster was available for this work. It was not used:
Speed is Linux and carries a **different EnergyPlus binary**, so runs there test a different build and cannot address
`H3`. `FINDING 190` had already excluded worker contention, which makes **serial execution a requirement, not a
convenience** — parallelism would have reintroduced the confound the experiment exists to rule out. 90 runs took
206.8 s on the local host.

**8.5 — Follow-on output, not part of this decision: European district 3D viewers.** Four self-contained offline
viewers were generated on request from the `EU-02` neighbourhood extracts, canonical copies in
`openubem/outputs/3D/eu_<cell>_viewer.html` and mirrored to
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`: `ES-MAD-BERRUGUETE` (1,194 residential / 204 excluded),
`FR-LYO-HAUTCOEURPENTES` (530 / 238), `GB-LDN-STDUNSTANS` (1,242 / 109), `IT-BOL-GALVANI2` (1,220 / 37).
They are **geometry only and carry no simulated value of any kind** — these districts stop at Step 2, so no
`05_results.csv`, no Step-3 IDF manifest and no per-building energy exist for them, and the `openubem.viz`
viewer path (which builds its geometry from per-building IDFs) was therefore **not** used. Extrusion heights are
stated with their provenance in each file: `FR-LYO` is 530/530 measured from IGN BD TOPO; `ES-MAD` is 1,028 from
storeys × 3.0 m and 166 assumed at 9.0 m; `GB-LDN` is 1,128 / 114; `IT-BOL` is **1,220 assumed**, since the Comune
di Bologna `rifter_edif_pl` layer publishes neither height nor storeys. **No campaign artefact was read or written**,
the certified re-run tree was not touched, and nothing here bears on `D-EU-31`, on any gate, or on the one quotable
figure.
