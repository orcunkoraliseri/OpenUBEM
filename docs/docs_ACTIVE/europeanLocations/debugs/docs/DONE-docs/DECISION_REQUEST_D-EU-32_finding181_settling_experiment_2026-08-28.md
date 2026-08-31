# DECISION REQUEST `D-EU-32` — do we spend ~60 diagnostic runs to settle `FINDING 181`?

**Raised:** 2026-08-28. **Work package:** none — `EU-01`–`EU-10` are all COMPLETED. **Status:** RULED (Option A selected).
**Changes no published number, no perimeter, no gate verdict, whatever is ruled.**
**Source:** three independent external investigations of `FINDING 181`, commissioned as
**documentation-only** and returned on 2026-08-28:

- `debugs/docs/DONE-resultReports/FINDING181_REPORT_fable5_2026-08-28.md`
- `debugs/docs/DONE-resultReports/FINDING181_REPORT_codex_2026-08-28.md`
- `debugs/docs/DONE-resultReports/FINDING181_REPORT_gemini3flash_2026-08-28.md`

Prompt given to all three, identical and self-contained:
`debugs/DONE/PROMPT_finding181_investigation_2026-08-28.md`.

---

## 0. Why this is being raised

`FINDING 181` — same IDF, same EPW, same binary, same host, different results — has been the arc's **sole
open item** since `D-EU-31` was ruled. It was open with the mechanism *unidentified*. It is still
unidentified, but it is now **localised**, and the three reports agree on where it is not.

The three models worked independently, blind to each other, read only artefacts already on disk, ran no
simulation and wrote no code. **Their agreement is therefore evidence, not consensus-by-copying.**

What is being asked here is **not** a re-run of the campaign and **not** a re-scoring of anything. It is
whether to spend a small, bounded number of *diagnostic* EnergyPlus runs to decide between the two
surviving explanations — because that choice, and only that choice, determines whether a **cheap fix
exists** or whether the standing position of `D-EU-31` is permanent.

---

## 1. Control run by this session before writing this request

The three reports share a set of base counts. Re-derived directly from
`outputs/deu27_rerun_cells.csv` on 2026-08-28, all confirmed:

| Quantity | Value |
|---|---|
| rows | 1,530 (510 cells × 3 replicates) |
| `BUILD_REFUSED` / `ATTEMPTED` | 345 / **1,185** |
| `COMPLETED` / `ENGINE_FAILED` | **1,029 / 156** |
| attempted cells | 395 |
| cells whose **`completed` flips** across the three replicates | **116 of 395 (29.4 %)** |
| cells completing 3 of 3 | 274 |
| of those, cells with **more than one `heating_kwh`** | **83 of 274 (30.3 %)** |
| `ENGINE_FAILED` rows carrying `return_code = 1` | **156 of 156** |
| longest runtime anywhere among 1,185 attempted rows | **5.604 s** (timeout is 900 s) |

Two source facts were also verified directly, because the ruling turns on them:

- `openubem/idf/european_controls.py:88-89` — `Heating_Limit="NoLimit"`, `Cooling_Limit="NoLimit"`.
- `openubem/campaign/eu_cell_runner.py:57-59` — `SimulationControl,Yes,Yes,Yes,No,Yes,No,1;` and
  `SizingPeriod:WeatherFileDays,AnnualSizingPeriod,…`. **Zone/system/plant sizing runs; the sizing
  period itself is not simulated as a run period.**

---

## 2. What the three reports establish

### 2.1 Excluded — unanimously, by three independent measurements

| Hypothesis | Verdict | Discriminator |
|---|---|---|
| **H1 — the harness / ReadVarsESO / a truncated or racing `eplusout.csv`** | **EXCLUDED** | `eplusout.eso`, written by the engine before ReadVarsESO exists, already differs. fable5: differs at line 12, the **first hourly record**, in **250 of 251** disagreeing pairs, and is byte-identical in **659 of 662** agreeing pairs. codex: ESO sum equals the 8,760-row CSV sum exactly within each replicate. gemini: `.eso` differs in **83 of 83** divergent cells. |
| **H4 — the inputs were never identical** | **EXCLUDED** | `eplusout.expidf` differs on **exactly one line** — the absolute `Schedule:File` path (`\rep1\` vs `\rep2\`). Schedule CSVs byte-identical; `.shd`, `.bnd`, `.mtd`, `.dbg`, `.mdd`, `.rdd` byte-identical; EPW digest verified before every build (`eu_cell_runner.py:175-185`). |
| **H5 — environment: antivirus, file lock, `%TEMP%` collision, timeout** | **EXCLUDED as the cause** | **156 of 156** failures are EnergyPlus solver fatals with `return_code = 1`, `fatal_count = 1`, an empty driver `error` column and an `eplusout.end` reading `EnergyPlus Terminated--Fatal Error Detected`. **0 timeouts, 0 driver exceptions.** |
| **H6 — one object class is the amplifier** | **INCONCLUSIVE / not a count effect** | Every expanded IDF has exactly one `InternalMass` and one `ZoneHVAC:IdealLoadsAirSystem`, so neither can discriminate. Window-count association is real but **non-monotone and fold-confounded**; gemini measures `r < 0.06` against window, surface and OSC counts. |

### 2.2 The new result — the divergence is decided **before the first simulated hour**

This is what the three reports add beyond everything already known, and they reach it separately:

- `epluszsz.csv` — the zone-sizing output — **differs in 250 of 251 disagreeing replicate pairs and is
  byte-identical in 662 of 662 agreeing pairs** (fable5). Sizing agreement ⟺ annual agreement.
- The final `Zone Sizing Information` design heating load in `eplusout.eio:95` for
  `it__IT.MidClim.SFH-TH.07…f100` reads **7602.474 / 7626.574 / 7524.245 W** across rep1/rep2/rep3
  (fable5 and codex, same three numbers, measured independently).
- The first differing `.eso` record is `01/01 01:00` — **the very first reported hour** — in
  83 of 83 divergent cells (gemini) and 250 of 251 pairs (fable5).
- **117 of 156 fatals are `SolveForWindowTemperatures` convergence fatals during
  `Environment=ANNUALSIZINGPERIOD` on 01/01**, at a **fold-fixed timestep** (`it` 08:00 ×68,
  `uk` 08:35 ×12, `es` 08:45 ×37), on the **first `FenestrationSurface:Detailed` object in input order,
  117 of 117** (fable5). The remaining 39 are inside-surface heat-balance runaways.
- Warmup reports `Pass` on all four tests in **both** members of a divergent pair, with average
  temperature differences ~2e-15 K, yet their hour-1 heating differs by ~5 % (fable5). The model admits
  **more than one periodic solution under the same forcing**.

**Plain statement:** this is not floating-point noise accumulating over the year and it is not a race in
the timestep loop — agreeing replicates are **bitwise identical over 8,760 hours**. It is a **discrete
event decided once per process**, at or before the first window heat-balance solve, which the massless
unenclosed envelope then amplifies for the rest of the year.

### 2.3 The one substantive disagreement — and it is decidable

- **gemini3flash** concludes autosizing is the perturbation entry point and recommends disabling the
  sizing pass as the fix.
- **fable5 measures that nothing computed in sizing is consumed by the run period**:
  `ZoneHVAC:IdealLoadsAirSystem` is `NoLimit` on both heating and cooling with blank capacity fields,
  `Run Simulation for Sizing Periods = No`, and `.eio:97-98` reports user-specified maximum air flow rates
  of `0.00000`. **Verified independently by this session at `european_controls.py:88-89`.** Sizing and run
  therefore do **not** share a parameter — they are two witnesses of one per-process condition.
- **codex** declines to choose and names the experiment that separates them.

Both readings predict the same disk evidence. They are **observationally indistinguishable on retained
artefacts** and cannot be settled by any further reading. That is precisely why this request exists.

### 2.4 One error in our own prompt, found by codex

The prompt told all three models that the S0 windows sit on hosts using `OtherSideCoefficients`.
`openubem/idf/european_box.py:281-284` assigns opening hosts
`outside_boundary_condition="Outdoors"` — deliberately, to preserve the same `U*A` loss where S0 fixtures
expose only `b=1` wall hosts. `OtherSideCoefficients` is used for the floor / roof / equivalent opaque
faces. codex flagged it, used the retained expanded IDF as the statement of what was actually simulated,
and drew no inference from the prompt's wording. **The other two did not notice.** This does not change any
finding; it is recorded so the prompt is not re-used uncorrected.

---

## 3. What is being asked

**May ~60 diagnostic EnergyPlus runs be spent to decide between H3 and H8?**

- **H3 — a per-process condition in the 23.1 Windows build** (uninitialised or address-dependent state at
  the first window solve). Remedy would be a build-level or invocation-level change.
- **H8 — state carried from the sizing environment into the run period**, combined with the model's
  multi-stability. Remedy would be a three-object IDF change and would restore reproducibility **without
  altering a single consumed quantity**.

These are the only two survivors. Every other hypothesis is excluded above.

**The proposed experiment, exactly:**

| Arm | What | Runs |
|---|---|---|
| **E1** | 3 cells (`uk…AB.04…f100`, `it…SFH-TH.07…f100`, `it…SFH.07…f000`) × 10 replicates, with `Do Zone Sizing / Do System Sizing / Do Plant Sizing = No` and `SizingPeriod:WeatherFileDays` removed. Divergence persists → **H8 dead, H3 stands**. Divergence vanishes → **H8 is the channel and a three-object fix exists**. | 30 |
| **E2** | The same 3 cells × 10 with `OMP_NUM_THREADS=1` set in the child environment. `energyplusapi.dll` imports `_vcomp_fork` / `_vcomp_set_num_threads` from `vcomp140.dll` (fable5, §2.11), so an OpenMP region is compiled in; whether this model executes it is not determinable from disk. Rate unchanged → threading excluded. | 30 |

Measured cost, from `runtime_s` in the control above: **each run is under 6 s.** Sixty runs is **under ten
minutes of one workstation**, serial. No cluster, no network, no job submission.

**Constraints that hold whatever is ruled:**

- Runs go to a fresh scratch root. **Nothing under `openubem/outputs/eu_certified_rerun_2026-08-28/` is
  read-write, deleted or added to.**
- **No gate is re-scored. No perimeter moves. No `idf_sha256` is regenerated for any promoted artefact.**
- **No quotable number may come out of this** — no EUI, no band, no fold aggregate, no gate verdict.
  The campaign re-run budget stays **SPENT**; this is not a campaign.
- The IDF modifications exist only inside the scratch arm and are never written to
  `eu_cell_runner.IDF_HEADER_TEMPLATE` unless a *separate* ruling adopts a remedy.

---

## 4. Options

**Option A — RECOMMENDED. Authorise E1 and E2 as a bounded diagnostic, 60 runs, scratch-only.**
- Decides between H3 and H8, which no amount of further reading can decide.
- If E1 is positive, a remedy exists that changes **no consumed quantity** — the cheapest possible outcome,
  and the only path on which `G8.1`–`G8.4` could ever become scoreable on a future campaign.
- If both are negative, `FINDING 181` closes as **declared and bounded** with the mechanism attributed to
  the build, which is a stronger and more honest closure than the present "unidentified".
- Cost: under ten minutes of local compute, zero risk to any promoted artefact.
- Produces **no** number that may be quoted. The deliverable is a verdict on two hypotheses, nothing else.

**Option B — Authorise E1 only (30 runs).**
- Answers the load-bearing question and skips the OpenMP screen.
- Cheaper by five minutes, and leaves threading as an untested confound if E1 is negative.
- **Not recommended** — the saving is not real, and a negative E1 without E2 leaves H3 unsplit.

**Option C — Spend nothing. Adopt remedy family (c) as permanent.**
- `FINDING 181` closes as *declared*: cell values are draws from a per-process distribution decided before
  the first simulated hour; only fold aggregates over cells complete in every replicate are quotable,
  exactly as `D-EU-31` already rules.
- Cost: zero. Nothing published changes — `D-EU-31` already forbids everything this would forbid.
- **Not recommended, but defensible.** Note the residual it accepts: **fold-aggregate unbiasedness is not
  established** — basin selection need not be symmetric (fable5, §5c). Option C therefore closes the item
  without ever testing whether `108.25 ± 0.16 %` is centred.

**Option D — Redesign the equivalent envelope as a closed prism now** (codex's Option A).
- Addresses the physics rather than the symptom, and is where all three reports agree the true fix lies
  for **future** campaigns.
- Cost: a DESIGN ruling, `european_box.py`, **every** `idf_sha256`, a full campaign re-run, every gate
  re-scored. **Out of scope here** — the arc's re-run budget is SPENT and all ten packages are closed.
- **Not recommended now.** Recorded as the standing recommendation for the next geometry generation (S1–S3),
  not as a `FINDING 181` remedy.

---

## 5. What must be written if Option A is ruled

1. `STATE v2` §3 records the three external reports and their agreed exclusions (**H1, H4, H5** excluded;
   **H6** not a count effect), as `FINDING 193`.
2. `STATE v2` §3 records the new localisation — divergence present in the sizing pass and at the first
   reported hour, 117/117 window fatals on the first fenestration object at the fold's first sun-up
   timestep — as `FINDING 194`.
3. `STATE v2` §3 records the prompt error (window hosts are `Outdoors`, not `OtherSideCoefficients`) as a
   correction note, and the prompt file is corrected in place before any re-use.
4. `FINDING 181` stays **OPEN** until E1/E2 return; the ruling does **not** close it.
5. Progress-log row; director prompt SEC block; next free identifier becomes `D-EU-33`, next free finding
   `FINDING 195`.
6. **No file under `openubem/` is modified and no gate is re-run.**

If **Option C** is ruled instead: items 1–3 stand unchanged, `FINDING 181` moves to **CLOSED — declared,
mechanism attributed to the build and not proven**, and the unbiasedness residual in §4 Option C is
recorded verbatim as a permanent caveat on `108.25 kWh/m² ± 0.16 %`.

---

## 6. Evidence

- The three reports, `debugs/docs/DONE-resultReports/FINDING181_REPORT_{fable5,codex,gemini3flash}_2026-08-28.md`.
- The prompt, `debugs/DONE/PROMPT_finding181_investigation_2026-08-28.md`.
- Base counts re-derived by this session from `outputs/deu27_rerun_cells.csv` (§1) — all confirmed.
- `openubem/idf/european_controls.py:88-89`; `openubem/campaign/eu_cell_runner.py:57-59`;
  `openubem/idf/european_box.py:281-284`.
- Retained tree `openubem/outputs/eu_certified_rerun_2026-08-28/{rep1,rep2,rep3}/` — **read-only**.
- Prior ruling `D-EU-31`, `debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-31_reproducibility_perimeter_2026-08-28.md`.
- Host `tabletop1`, EnergyPlus `23.1.0-87ed9199d4`, Windows. Single host — **no two-host claim is available
  from any of this**, and none is made.

---

## 7. Ruling

**Option selected:** **Option A — Authorise E1 and E2 as a bounded diagnostic, 60 runs, scratch-only.**

**Ruled by:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

**Notes:** Option A approved. Bounded diagnostic authorized (E1: 30 runs with sizing disabled, E2: 30 runs with OMP_NUM_THREADS=1) across the 3 representative cells (`uk__GB.ENG.AB.04.Gen.ReEx.001.001__f100`, `it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100`, `it__IT.MidClim.SFH.07.Gen.ReEx.001.001__f000`). All runs to execute into fresh scratch roots only. Zero modifications to promoted campaign artefacts or `openubem/` source code. Produces no quotable perimeter numbers.
