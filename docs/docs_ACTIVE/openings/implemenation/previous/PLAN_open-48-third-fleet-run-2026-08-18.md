# PLAN — OPEN-48 third fleet run

**Slug:** `open-48-third-fleet-run`
**Date opened:** 2026-08-18 (late evening)
**Authorised by:** the user, 2026-08-18 — *"vas-y 'to authorise a third full fleet run.' continuer"*.
This reverses **ruling 4 of `PLAN_open-49-and-open-01-2026-08-13.md`**, which declined the run.
**DESIGN pointer:** none — this plan runs the existing pipeline unchanged. The pipeline contract is
`scripts/validation/v12_cell_pipeline.py::run_cell`, and §2 of `PLAN_three-rulings-2026-08-12.md`
forbids editing it.
**Driven by the director, not an executor** — see §2, rule 6, and the five recorded executor deaths in
§5.13 point 3 of `prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`.

---

## 1. What this run is for, stated before any number exists

OPEN-48 asks one question: **can the repository at `HEAD` regenerate the published fleet figure?**

Run 2 (`open48_refleet`, 2026-08-13) answered *"the elevator wiring reproduces"* — 3,561 rows with
elevator energy, cell by cell identical to the adopted run — but returned pooled **159.2157** against
the adopted **157.0552**, +2.16. That +2.16 was traced to OPEN-49: window-to-wall ratio was drawn as one
vectorised block whose size and bounds depended on which buildings were `OpenUBEMUnknown` in the cell,
so a classification drift between the two OSM fetches silently redrew the windows of untouched
buildings. OPEN-49's mechanism was fixed on 2026-08-17 (`_per_building_rng`, fixed cross-archetype
bounds), but **ruling 4 declined the re-run that would restate the headline**, so OPEN-48 stayed open
with its reason narrowed to exactly one sentence: *no post-fix fleet re-run exists.*

**This plan executes that run.**

---

## 2. Hard rules

1. **No compute on the login node.** Every simulation ships via `sbatch --array` from inside
   `run_cell`. `squeue`, `sacct`, `scp`, `ls` only, on `speed-submit2`.
2. **`v12_cell_pipeline.py` is not edited.** Run 3 calls `run_cell` unchanged, exactly as runs 1 and 2
   did. Any behaviour difference between runs must be attributable to `openubem/`, not to the driver.
3. **The pooled figure is computed with `scripts/analysis/open43_fleet_aggregations.py`'s arithmetic —
   `footprint_area_m2 × levels.clip(lower=1)`.** Never hand-rolled, never from a subset of cells. This
   trap has been hit once already.
4. **The success criterion is reproduction, and the expected fleet delta against the adopted run is
   ≈ 0.** A large positive delta is the alarming outcome, not the reassuring one. The non-vacuity
   control is the elevator column being non-zero and matching the adopted per-cell counts.
5. **No cell is counted on a failed attempt.** A cell that dies on SSH transport is re-run alone and its
   partial output discarded.
6. **The director drives, and budgets for its own agents dying.** The launched process survives the
   agent that launched it; poll for the artifact on disk, never background a monitor and wait on it.
7. **Never touch other-project cluster runs.** Job `1266911` (`4J_s4_pe`) was already running under this
   account when run 3 was launched and is not this arc's. Leave it alone.

---

## 3. File layout

| Path | Role |
|---|---|
| `scripts/validation/open48_fleet_run3.py` | **new** — parallel driver, 12 cells, `MAX_PARALLEL=4` |
| `%TEMP%\ubem_validation\open48_refleet3\<cell>\` | local work dir, pre-seeded (see §4) |
| `%TEMP%\open48_run3\STATUS.txt`, `<cell>.log` | live state, one log per cell |
| `%TEMP%\open48_run3_driver.log` | driver stdout |
| `/speed-scratch/o_iseri/fleets/open48_refleet3_<cell>` | remote fleet dirs |
| `docs/validations/overAll/results/open48_refleet3/<cell>/` | final per-cell results |
| `openubem/outputs/comparisons/open48_run3_fleet.csv` | T04 output |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-48_third-fleet-run.md` | T05 write-up |

---

## 4. The one design decision, and why it is the whole plan

**The twelve work dirs are pre-seeded with run 2's cached `01_buildings.gpkg` and its resolved EPW
before the driver starts.**

`step1_fetch` loads the cache when the file exists (`v12_cell_pipeline.py:138-141`) and re-fetches OSM
otherwise. `step2_classify_enrich` caches **nothing** and always re-runs. So seeding freezes the OSM
input byte-for-byte and lets the fixed semantic code run fresh.

**Why this is required, not a shortcut.** A fresh OSM fetch would drift the classification again, and
run 3 would confound the code fix with a new input drift — the exact defect that made run 2
uninterpretable. Freezing the input makes **run 3 vs run 2 a single-variable comparison: code only.**

**What this run therefore cannot do, stated up front.** The adopted `phaseE_elevrb` run's own input
`01_buildings.gpkg` no longer exists. **Run 3 cannot reproduce `157.0552` from the adopted run's own
inputs, because those inputs are gone.** It can establish (a) the fleet figure the current repository
produces, (b) the size and direction of the OPEN-49 fix's effect, and (c) whether the remaining gap to
`157.0552` is explained by the recorded classification drift. Anything beyond that is not available from
this run and must not be claimed.

**Seeding was verified, not assumed:** all twelve `01_buildings.gpkg` copied, and `nyc_centre`,
`la_rural`, `austin_urban` confirmed MD5-identical to their run-2 originals. The driver refuses to start
if any of the twelve is absent (`_preflight`).

---

## 5. Facts carried in, with citations

- Run 2 pooled **159.2157**; adopted **157.0552**; 8,160 buildings / 8,154 successes (same 6 known
  failures); 3,561 elevator rows, cell by cell identical. — director prompt §5.14.
- Four cells moved (`nyc_centre` +3.53, `austin_centre` +1.76, `la_centre` +1.60, `la_urban` +1.21);
  eight reproduced to ±0.07 or better; zero cells on the wrong side of that split. — OPEN-49 register
  entry.
- Nondeterminism is excluded at both stages: 738/738 IDFs byte-identical on a repeat with unchanged
  inputs; results max Δ 0.00836 kWh/m², cell EUI Δ −2.8e-05. — OPEN-49 register entry.
- The OPEN-49 fix is committed and present at `HEAD`: `openubem/semantic/__init__.py:212`
  `_per_building_rng`, `:252` per-row seeding, `:366` unconditional `_get_cross_archetype_loads()`.
  Verified `git status --porcelain openubem/` empty at `43b14ad`.
- `la_rural` +0.0657 with archetypes identical and zero Unknown buildings is an **unexplained residual**
  carried forward deliberately. Run 3 should be checked against it; it must not be absorbed into the
  story.
- Six concurrent cells saturated the SSH link in run 2 and killed two cells. Run 3 uses four.

---

## 6. Tasks

### T01 — Seed the frozen inputs — **done before launch**
**What.** Copy run 2's `01_buildings.gpkg` and `weather/` into the twelve `open48_refleet3` work dirs.
**Why.** §4.
**How.** Straight file copy; no pipeline code involved.
**How to test.** All twelve present; three spot-checked MD5-identical; driver `_preflight` passes;
first cell's log reads `Step 1: loading cached GDF`, never `fetching OSM`.

### T02 — Run the twelve cells
**What.** `open48_fleet_run3.py`, four concurrent, 240 s stagger.
**Why.** The run itself.
**How.** Launched detached so it outlives any agent. Poll `STATUS.txt` and the per-cell logs at ≥30 min.
**How to test.** `rc=0` for all twelve; each cell's final dir carries its results; no `REUSED_REMOTE`.

### T03 — Retry any cell that fails on transport

> 🔴 **AMENDED 2026-08-18 (late).** T03 covers **transport** failures only. A cell that fails on the
> *model* is **not** a retry candidate: the Unknown-building draw is deterministic
> (`_per_building_rng` = `blake2b(osm_id)` + `config.RANDOM_SEED`), so a retry reproduces the identical
> failures. **`nyc_centre` (`rc=1`, transport) retries. `nyc_suburban` (`rc=2`, 71 model divergences —
> OPEN-55) does not.** Classify by return code and by whether the log ends in a `ZERO-FAIL` line before
> queueing anything.
**What.** Re-run failed cells **one at a time**.
**Why.** Run 2 lost two cells to SSH saturation, and both returned `rc=0` when run alone.
**How.** Same driver contract, single cell.
**How to test.** `rc=0`, and the cell's remote dir rebuilt rather than partially reused.

### T04 — Aggregate
**What.** Pooled fleet EUI and the three controls: 8,160 buildings, 8,154 successes, elevator-row count
and per-cell elevator sums against the adopted run.
**Why.** Rule 3 and rule 4.
**How.** `scripts/analysis/open43_fleet_aggregations.py`'s arithmetic, unmodified.
**How to test.** Building count and failure count match exactly; a mismatch is a STOP.

### T05 — Compare and write up
**What.** Three-way table: adopted / run 2 / run 3, fleet and per-cell. Attribute the run-3−run-2 delta
to the OPEN-49 fix, and the residual run-3−adopted gap to the recorded classification drift **or state
that it is unexplained.** Check the `la_rural` +0.0657 residual.
**Why.** A number without an attribution is not a result.
**How to test.** Every claim traces to a column in the CSV.

### T06 — Records and the ruling owed back
**What.** OPEN-48 and OPEN-49 register entries, `docs/PROJECT_CHECKLIST.md`, director prompt section,
progress board artifact, and this plan's progress log.
**Why.** Standing convention; the register is the only place open work lives.
**How to test.** Register arithmetic invariant holds (struck − retired = 2); zero control characters.
**Also register, as a new item, the defect this run exposed:** `_ssh` in `v12_cell_pipeline.py:111`
returns `stdout + stderr` and never raises on a non-zero remote exit, so every caller that relies on
a remote command having worked — `ship_to_cluster:265` among them — fails later and elsewhere than
the actual fault. Found the hard way on `nyc_centre`. Next free ID is **OPEN-54**.

~~**The ruling this run hands back to the user:** whether the published fleet figure stays `157.1` or
moves to run 3's number. **The director does not make that call.**~~

**AMENDED 2026-08-18 (late) — the user delegated this ruling to the director:** *"pour ces decisions,
tu progress comme tu recommends en choissant l'option de plus precision"*. CP-2 and CP-3 are therefore
**decided by the director, not handed back**, under one stated criterion: **choose the more precise
option.** Concretely, where two readings of the fleet figure are defensible, take the one whose
provenance is fully traceable to a column in the CSV over the one that is merely more convenient or
more flattering — and if the most precise available answer is *"this cannot be determined from run 3"*,
that is the answer to give. The delegation covers the choice; it does not license skipping the
reporting. **CP-2 and CP-3 are still written up in full, with the reasoning that produced the call.**

---

## 7. Stop-and-report points

- **CP-1 — after T02/T03.** All twelve cells landed, or a cell has failed twice. Report before
  aggregating.
- **CP-2 — after T04.** The pooled number and the three controls, reported before any interpretation.
- **CP-3 — after T05/T06.** The three-way comparison and the ruling handed back.

---

## 8. Progress log

#### T01 — Seed the frozen inputs — completed 2026-08-18

**Artifacts.** Twelve seeded work dirs under `%TEMP%\ubem_validation\open48_refleet3\`.

**Deviations.** None.

**Test status.** Twelve of twelve `01_buildings.gpkg` present. `nyc_centre`
`e8b6e0f3a534831a96eeb9acc9f444c4`, `la_rural` `6249e2e5e69e5a72ea7a043e70eca73b`, `austin_urban`
`314ed65574815dde04ffdacf208824e3` — each identical to its run-2 original. Driver `_preflight` printed
`PREFLIGHT OK — 12/12`.

**Notes.** `nyc_centre`'s log confirms the intent held at runtime: `Step 1: loading cached GDF`, 738
buildings, 35 `OpenUBEMUnknown`, 7 `Courthouse` — no OSM fetch occurred.

#### T02 — Run the twelve cells — launched 2026-08-18 17:44

**Artifacts.** Driver PID 47556, detached. `%TEMP%\open48_run3\STATUS.txt` and twelve cell logs.

**Deviations.** `MAX_PARALLEL` lowered 6 → 4 and stagger raised 180 s → 240 s against run 2's driver,
on run 2's own evidence of SSH saturation. Director decision, recorded here rather than silently
applied.

**Test status.** In flight. `nyc_centre` launched 17:44:49 and cleared step 1 and step 2.

**Notes.** Run 2 took ~6 h wall for twelve cells at six concurrent; four concurrent should be slower,
and the trade is deliberate.

#### T02 — first failure recorded — `nyc_centre` rc=1 at 2026-08-18 18:27

**What happened.** `nyc_centre` cleared every local stage — cached GDF loaded (no OSM fetch), 738/738
IDFs generated in 2507 s, both LIVE_SMOKE gates PASS — and then died shipping to the cluster:

```
scp: dest open "/speed-scratch/o_iseri/fleets/open48_refleet3_nyc_centre/fleet.lst":
     No such file or directory
CalledProcessError ... v12_cell_pipeline.py:267 in ship_to_cluster
```

**The real fault is one line earlier than the traceback.** `ship_to_cluster:265` creates the remote
directory with `_ssh(f"mkdir -p {remote_fleet_dir}/...")`, and `_ssh` (`:111-116`) returns
`stdout + stderr` and **never raises on a non-zero remote exit**. The caller discards that string. So the
`mkdir` failed silently and the `scp` on the next line was the first thing loud enough to stop the run.
The traceback names `scp`; the defect is the unchecked `mkdir`.

**It was transient, and that was established rather than assumed.**

- The directory is genuinely absent remotely, while `open48_refleet3_nyc_urban`, `_nyc_suburban` and
  `_nyc_rural` all exist — so this was one call failing, not a systemic block.
- Quota is not the cause: `/speed-scratch` 6.3T used against a 10.0T limit, no file-count limit set.
- Three consecutive `mkdir -p` probes immediately afterwards returned clean (`probe_ok_1..3`).

**Disposition.** `nyc_centre` goes to T03 and is re-run **alone once the other eleven have landed**,
per §2 rule 5 and §6 T03. Its partial output is discarded, as that rule requires.

**Deliberately not done.** `v12_cell_pipeline.py` is **not** being patched to check `_ssh`'s exit code,
even though that is the obvious repair. §2 rule 2 forbids editing it, and changing the pipeline midway
through a twelve-cell run would destroy the single-variable comparison the whole plan exists to make.
**Logged here as a real defect for a later pass, not carried out now.**

**Test status.** Eleven cells outstanding. `nyc_urban`, `nyc_suburban`, `nyc_rural`, `la_centre` running
at the time of writing; seven pending.

#### T02 — second failure recorded — `nyc_suburban` rc=2 at 2026-08-18 18:46 — **a model failure, and the run's real finding**

**Artifacts.** `extra/INVESTIGATION_open-55_pde-bounds-datacenter.md`; register §10 entry **OPEN-55**;
`04_simulation_manifest.parquet` in the run-3 work dir (1518 success / 71 failed).

**What happened.** `nyc_suburban` cleared every local stage — cached load, 1589 buildings, 290 Unknown,
1589/1589 IDFs, both LIVE_SMOKE gates PASS — then stopped on
`ZERO-FAIL: 71 failures exceed tolerance 16`. All 71 are `CalcHeatBalanceInsideSurf` runaways to as much
as 1.3×10⁷ °C.

**Why this is not another OPEN-54.** Run 2 ran this cell on **byte-identical frozen input** and reported
`{'success': 1589}` — zero failures. Code was the only variable, and the code that changed is the
OPEN-49 fix.

**Mechanism, proven rather than inferred.** Route 2 of the OPEN-49 fix made
`_get_cross_archetype_loads()` unconditional (`openubem/semantic/__init__.py:366`), so the Unknown PDE
bounds come from all 29 archetypes instead of the 5 present in the cell. That admits
`LargeDataCenterHighITE` at **5381.96 W/m²**: the equipment bound went from `[…, 96.88]` to
`[2.58, 5381.96]`, **55× wider**, median draw ~50 → ~2690 W/m² against an ordinary 5–20 W/m². Because
the draw is deterministic it was regenerated locally and joined to the manifest: **no building drawing
below 2496 W/m² failed**, the 71 failures span 2496–5349, and **every failure is an `OpenUBEMUnknown`** —
none of the 1299 classified buildings failed.

**Blast radius, measured locally across all twelve cells.** Between **four and six cells of twelve** are
expected to stop. 🔴 **The failure count understates the damage** — the gate catches only divergence and
is blind to Unknown buildings that absorb an absurd load and report a finite, enormous EUI. `la_urban`
passes with two Unknowns, both drawing above 2496. **Any fleet EUI from run 3 is inflated, including
from the cells that pass.**

**Deviations.** T03 amended above to exclude model failures from retry. **Nothing in
`openubem/semantic/` was patched** — the remedy is a DESIGN question (what an Unknown building may be),
not the director's to settle, and a mid-run edit would break the single-variable comparison exactly as a
pipeline edit would.

**Director decision — the run continues.** Stopping saves idle cluster time and non-scarce disk (6.3 T
of a 9.8 T warn). It costs the only thing still worth having: an **observed** per-cell census instead of
the projected one. The ruling does not change either way — run 3 cannot yield a publishable fleet
number, and that was settled once the mechanism was proven — so the run continues for evidence, not for
its headline.

**Test status.** `nyc_rural` `rc=0` (first clean cell). `nyc_centre` `rc=1` transport, queued for T03.
`nyc_suburban` `rc=2` model, **not** queued. `nyc_urban`, `la_centre`, `la_urban` running; six pending.

#### T02 — third failure recorded — `la_urban` rc=1 at 2026-08-18 19:28 — transport, and it corrects OPEN-54

**Artifacts.** `extra/INVESTIGATION_open-54_ssh-unchecked-exit.md` §3.2 (new); register OPEN-54 closure
condition widened.

**What happened.** `la_urban` submitted its array (`1271807`) and died 42 minutes in, inside
`poll_cluster`, on `subprocess.TimeoutExpired` from the `sacct` call at `v12_cell_pipeline.py:327` after
60 s. No `ZERO-FAIL` line — **transport, not model.** T03 retry candidate.

**The correction it forces.** OPEN-54's blast-radius table called `:327` *"printed only — cosmetic."*
That was right about the return value and wrong about the risk: `_ssh` passes `timeout=` to
`subprocess.run` and never catches `TimeoutExpired`, so **every call site is fatal on a slow login node
whether or not its output is read.** A status line that exists only to be printed ended a cell whose
SLURM array was very likely healthy. **`check=True` alone would not have prevented this** — exit code
and timeout are separate axes. Remedy widened: a `tolerant=True` mode catching `TimeoutExpired` at the
two `sacct` display calls and the completeness probe.

**Deviations.** None to the run. Nothing patched — same binding reasons as the two entries above.

**Test status.** `nyc_rural` `rc=0`. T03 queue is now **`nyc_centre` and `la_urban`** — both transport.
`nyc_suburban` stays excluded (model). Cells still to land: eight.

#### T02 — `nyc_urban` rc=2 at 2026-08-18 19:42 — the OPEN-55 projection tested and held

**Artifacts.** `extra/INVESTIGATION_open-55_pde-bounds-datacenter.md` §4A (new); register OPEN-55
strengthened.

**Result.** `ZERO-FAIL: 83 failures exceed tolerance 18` — 83 of 228 Unknown buildings. The projection
written up an hour earlier said this cell would stop, and it stopped.

**What the second cell buys.** Pooling both observed cells — 518 Unknown buildings, 154 failures — and
binning by drawn equipment density gives a **monotonic dose-response curve from 0.000 to 1.000 across
eleven bins**: exactly zero failures below 1500 W/m², 0.306 at 3000–3500, 0.851 at 4000–4500, and
**1.000 above 5000**. **Not one of the 3,078 classified buildings across the two cells failed** — all
154 failures are `OpenUBEMUnknown`, independently in each cell. This moves OPEN-55 from a well-evidenced
association to a dose-response relationship, which is as strong as this evidence gets short of a
controlled re-run.

**Revised projection: five of twelve cells stop** — the two observed, plus `austin_centre` (14.4 vs 5),
`nyc_centre` (10.7 vs 7) and `austin_suburban` (8.9 vs 5). The earlier "four to six" was right and is
now narrowed.

🔴 **Predictions recorded before the cells run**, so the remaining seven are an out-of-sample test:
`nyc_centre` is predicted to **fail `rc=2` on its T03 retry** despite having failed only on transport so
far — if it retries clean, the model is wrong and §4A must be revisited. `la_centre` (3.9 vs 5) is the
marginal call and is reported as such.

**Deviations.** None. Nothing patched.

**Test status.** Observed: 2 clean-gate stops, 1 pass (`nyc_rural`), 2 transport failures. `la_centre`,
`la_suburban`, `la_rural` running; four austin cells pending.

#### T02 — six further landings, 19:58–20:38 — the scoreboard, and two mislabelled cells

*(One entry for six events. The per-event write-ups were made as each cell landed, in
`extra/INVESTIGATION_open-55_pde-bounds-datacenter.md` §4A.2–§4A.5 and
`extra/INVESTIGATION_open-54_ssh-unchecked-exit.md` §3.3–§3.4; this consolidates them into the plan
log, which had fallen behind the investigation docs.)*

**Artifacts.** OPEN-55 doc §4A.2, §4A.3, §4A.4, §4A.5; OPEN-54 doc §3.3, §3.4; register entries for
both widened; director prompt rewritten after each event.

**Landings.** `la_suburban` rc=0 (19:58) · `la_rural` rc=0 (20:06) · `la_centre` rc=2, 10 failures
(20:12) · `austin_suburban` rc=1 (20:26) · `austin_rural` rc=0 (20:32) · `austin_centre` rc=1 (20:37).

**Prediction scoreboard: 8 correct, 1 missed.** The miss was `la_centre` — predicted to pass at 3.9
against a tolerance of 5, it stopped with 10. It is recorded as a miss **in the unsafe direction**, the
point estimate was withdrawn, and the model was rebuilt as a bracket (§4A.3). The bracket has since
been tested three times — `austin_rural`, `austin_urban`'s pre-registration, and `austin_centre`
(pre-registered 14.4–24.7, landed on **20**) — with **no misses**, on cells spanning 226 to 1,779
buildings.

🔴 **Two cells were misfiled by their own return code.** `austin_centre` (`rc=1`) had already printed
`ZERO-FAIL violation: 20 failed buildings` against a tolerance of 5 before dying on the OPEN-54 `sacct`
timeout at `:334`; `austin_suburban` (`rc=1`) had printed 14 against a tolerance of 5 before dying at
`:536`. Neither can be rescued by the repair stage: **the maximum repair recovery measured across the
six cells that reached it is 2 buildings**, against the 15 and 9 that would be required. Both are model
stops. **The run has five stopping cells, not three** *(this entry first said eight and six; corrected 20:50 with all twelve landed — see OPEN-55 doc §4A.6)* — and the only reason that was recoverable is that
the gate prints its count before the repair stage runs.

**Deviations.** None. Nothing patched, in either `v12_cell_pipeline.py` or `openubem/semantic/`.

**Test status.** 4 passed · 3 stopped `rc=2` · 2 stopped but labelled `rc=1` · 2 transport-only
(`nyc_centre`, `la_urban`) · `austin_urban` still running. T04 aggregation as a twelve-cell fleet is
not reachable; the CP-2 ruling must be written against controls instead.

#### T02 — COMPLETE 2026-08-18 20:47 — twelve of twelve landed

**Artifacts.** `extra/INVESTIGATION_open-55_pde-bounds-datacenter.md` §4A.6; register OPEN-55 and
OPEN-54 corrected; director prompt rewritten.

**Final landing table.**

| outcome | n | cells (failures / tolerance) |
|---|---:|---|
| **stopped** | **5** | `nyc_suburban` 71/16 · `nyc_urban` 83/18 · `la_centre` 10/5 · `austin_centre` 20/5 · `austin_suburban` 14/5 |
| passed | 5 | `nyc_rural` 3/5 · `la_rural` 5/5 · `la_suburban` 0/13 · `austin_rural` 4/5 · `austin_urban` 5/5 |
| transport only, no verdict | 2 | `nyc_centre` (`:265`) · `la_urban` (`:327`) |

**`austin_urban`.** Passed, at exactly zero margin, by dropping **5 of its 5 Unknown buildings** — the
sharpest illustration in the run of §4A.4(b): a cell records a clean pass precisely because every
building the defect touched was deleted. Its top failure reached **5,381,322.93 °C**, which is the
`LargeDataCenterHighITE` bound of 5381.96 W/m² surfacing in the temperature field.

**Prediction outcome — direction 9 correct / 1 missed; bracket 3 hits / 1 miss.** `austin_urban` was
bracketed 0.7–3.3 and produced 5. Both bracket misses (`la_centre`, `austin_urban`) run the **same**
way — more failures than predicted — and both are on cells with very few Unknowns (15 and 5), while the
three that held were on 7, 24 and 37. **Recorded range of validity: the bracket under-predicts at low
Unknown counts.**

⚠️ **Correction.** The previous entry said "eight stopping cells, not six." **It is five.** I
double-counted the two re-classified `rc=1` cells against a total that had already been revised upward
for predicted stops. Corrected here, in OPEN-55 §4A.6, in OPEN-54 §3.4 and in both register entries.
**The conclusion the number was offered for is unchanged** — T04 is unreachable because five cells
produced no results, and the five passes are not poolable because four passed by dropping the affected
buildings while the fifth passed by keeping them.

**Deviations.** None. Nothing patched.

**Test status.** T02 closed. T03 opened.

#### T03 — `nyc_centre` retry launched 2026-08-18 20:49:33 — the pre-registered sharp test

**What.** `nyc_centre` alone, detached, pid 14960, `output_subdir=open48_refleet3`, seed verified present
(786,432 bytes) so no OSM re-fetch. Log: `%TEMP%/open48_run3/nyc_centre_t03.log`. Launcher:
`scratchpad/t03_retry.py` (one cell, preflight, detach) — the plan's one-at-a-time rule, and all twelve
cells have landed so nothing else is running.

**Why this cell and not the other two.** 🔴 It is the only retry that tests anything. `nyc_centre` was
**pre-registered on 2026-08-18 19:42, before any of the later cells ran**, to fail `rc=2` with 10.7–23.3
failures against a tolerance of 7 — despite having so far failed only on transport (`:265`, before any
simulation). **If it retries clean, the OPEN-55 model is wrong and §4A must be revisited.** `la_urban`
(2 Unknowns) and `austin_suburban` (already a proven model stop at 14/5) would each cost ~45 min and
settle nothing; both are dropped, and that is recorded rather than left implicit.

**How to test.** `grep ZERO-FAIL` in the log — count and tolerance — never the return code (see §4A.5).

**Result.** ⬜ Pending.

#### T05 / CP-2 / CP-3 — completed 2026-08-18 (late)

**Artifacts.** `extra/MEASUREMENT_open-48_third-fleet-run.md` (the deliverable, both rulings);
`scripts/analysis/open48_run3_vs_run2_cell_delta.py`;
`openubem/outputs/comparisons/open48_run3_vs_run2_cell_delta.csv`.

**Result — the fix is worth nothing on classified buildings.** Run 3 vs run 2, per cell, frozen input,
code the only variable, restricted to buildings successful in both runs, then repeated with every
Unknown removed from both:

| cell | n common | unk in common | Δ all | **Δ known** |
|---|---:|---:|---:|---:|
| `nyc_rural` | 195 | 2 | +23.2685 | **+0.0004** |
| `austin_rural` | 241 | 3 | +12.9387 | **−0.0001** |
| `la_suburban` | 1343 | 2 | +1.9560 | **+0.0001** |
| `la_rural` | 144 | 0 | −0.0906 | −0.0906 |
| `austin_urban` | 420 | 0 | −0.0614 | −0.0614 |

**Every classified building changed value and no cell mean moved** — the signature of route 1
reseeding the draw per building without changing the population. The two Unknown-free cells bound the
residual at **−0.09 kWh/m², under 0.08 %**. 🔴 **The question three fleet runs were spent on is
answered, in the negative.**

**The visible delta is two or three buildings.** `nyc_rural`'s two surviving Unknowns run at equipment
EUI **13 824** and **11 863** against a cell mean of 233 — ~73× — and move the cell +23.27 on their own.

**Three guards, each of which changed the answer:** `simulation_status == "success"` only (failed rows
carry NaN EUI but real floor area); common-success set only; Unknown-excluded repeat. The first draft
of the script had none of the first two and produced wrong numbers.

**Control.** `nyc_rural` elevators: 27 non-zero rows, Σ 97.1, **identical in both runs**. Not an empty
pipeline.

**CP-2 ruling — do not aggregate run 3.** Five cells produced nothing; the five passes are not poolable
(four passed *by dropping* the affected buildings, one passed by keeping them — opposite biases, same
label); and pooling would bury a 0.0004 signal under a 23.27 contaminant. **Under the user's
"more precise option" criterion the precise output is the per-cell table, not a scalar.**

**CP-3 ruling — 157.1 stays.** Nothing measured displaces it; OPEN-55 postdates it; and the reason the
arc doubted it is now measured at under 0.08 %. 🔴 **Caveat now quantified for the first time:** run 2's
Unknown path contributes **+4.058 kWh/m² (+2.615 %)** of its 159.2157 — 650 buildings, 3.7 % of floor
area, mean EUI 264.9 against a fleet 159.2. **That is nearly twice the +2.1605 discrepancy this arc has
been chasing.** The adopted run shares that code path but its per-building results are gone, so this is
a measurement on run 2 and an **estimate** for the adopted run — reported, never subtracted.

**Deviations.** T05 was specified as a three-way comparison. **The adopted leg is not computable** — no
per-building results survive for `phaseE_elevrb`, only figures and the aggregate CSV. Delivered as a
two-way measurement plus a bounded statement about the third, which is stated in the doc rather than
worked around.

**Test status.** T05 complete. CP-2 and CP-3 ruled. T06 remains; T03's `nyc_centre` retry still running.

#### T03 — `nyc_centre` retry — **died with no verdict** — 2026-08-18 21:18

**Artifacts.** `%TEMP%/open48_run3/nyc_centre_t03.log` (199 lines, 26,051 bytes, last written 21:18).
No `%TEMP%/ubem_validation/open48_refleet3/nyc_centre/results/` directory — the cell never reached
step 5.

**What happened.** pid 14960 exited between 21:18 and 21:27. The log ends mid-step-3 on an ordinary
`[hvac] single-zone downgrade` line for `way/266170615`. **No traceback, no `ZERO-FAIL` line, no gate
verdict, no partial results.** The process died inside local IDF generation, before any cluster
transport, so this is neither a transport failure nor a model failure — it is a third outcome the plan
did not anticipate: **a silent local death**.

**Deviation.** T03's test condition (`rc=0`, remote dir rebuilt) is not evaluable. The retry ran
28.5 minutes and produced no classifiable result.

🔴 **The pre-registered test is UNRESOLVED — it did not confirm and did not refute.** The prediction
recorded before launch was *"`nyc_centre` fails `rc=2` with 10.7–23.3 failures against tolerance 7; if
it retries clean, the OPEN-55 model is wrong and §4A must be revisited."* **Neither branch occurred.**
The OPEN-55 model therefore stands on the evidence it already had — the dose-response curve, the 3,078
classified buildings with zero failures, and the five scored cells — and gains nothing from this retry.
**It must not be recorded as a sixth confirmation.**

**Notes.** The plan's T03 classification rule (transport → retry, model → do not retry) is now known to
be incomplete: a third class exists, and `nyc_centre` has landed in an unclassifiable state twice in
one evening — once behind OPEN-54's unchecked exit status, once behind a silent death. **No third
attempt is queued.** It would cost another half hour to test a hypothesis the arc no longer needs: T04
is void under the CP-2 ruling, so `nyc_centre`'s result cannot enter any aggregate, and §3.1 has already
answered the question the run was launched for without it.

**Test status.** T03 closed as **not evaluable**. All six plan tasks are now discharged or void: T01,
T02, T05, T06 complete; T04 void under CP-2; T03 not evaluable. **The plan is closed.** The only thing
outstanding on this arc is the user's OPEN-55 ruling, which is not a plan task.
