# PLAN — OPEN-49 (the coupled random draw) and OPEN-01 (the denominator swap)

**Slug:** `open-49-and-open-01` · **Date:** 2026-08-13 · **Author:** director (manager session)
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — §OPEN-49 (line ~4462), §OPEN-01 (line ~778, rulings 5 and 6 at ~827 and ~855)
**DESIGN pointers:** `docs/docs_main/DESIGN_openubem-…-the-full-sys.md`; step-3 semantic enrichment under `docs/docs_main/docs_step3/`; results/reporting under `docs/docs_main/docs_step-5/`. **These are read-only.** If any task below contradicts a DESIGN statement, **STOP and quote the conflict** — do not reconcile it yourself.

**User rulings taken 2026-08-13 that authorise this plan** (all four, recorded verbatim in intent):

1. **Scope** = OPEN-49 + OPEN-01. Nothing else. The four cheap items (2c, OPEN-51, OPEN-52, the OPEN-44 `NameError`) are explicitly **out**.
2. **OPEN-49 keying** = a stable per-building seed, applied to **all four PDE columns**, not to `wwr` alone.
3. **OPEN-49 bounds** = a **fixed table**, independent of which archetypes happen to be present in the cell.
4. **Fleet** = fix, then a **before/after on the twelve cells**. **No third fleet re-run.** `157.1 kWh/m²` pooled stays published until the user rules otherwise.

> 🔴 **This plan authorises a remedy for OPEN-49.** Until today the register said "registered, not scheduled — no remedy is authorised." Ruling 2 above supersedes that sentence for the mechanism only; it does **not** authorise re-publishing any fleet figure.

---

## 2. Hard rules for the executor

These are not advice. Violating any one of them invalidates the task.

1. **Never `git commit`, `git add`, `git restore`, `git checkout --`, or `git stash`.** Git is handled externally by the user. Read-only git (`log`, `diff`, `show`, `status`) is fine. A previous executor on this project ran a tree-wide `git stash` and it had to be recovered with `git fsck --unreachable`.
2. **Never run two pytest sessions concurrently.** `pyproject.toml:54` pins `addopts = "--basetemp=.pytest_tmp"`, so two sessions delete each other's temp directories (OPEN-52). Run the suite **alone**, and wait for it.
3. **No cluster work in this plan at all.** No `sbatch`, no `ssh`, no harvest. Ruling 4 removed the fleet re-run. Every number below comes from artifacts already on disk.
4. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc, `tests/fixtures/labelled_archetypes_50.csv`, or `tests/fixtures/labelled_archetypes_tagrich_v2.csv`.
5. **No `.py` files under `docs/`, ever.** All figures and `.csv`/`.png` outputs go to `openubem/outputs/` (flat).
6. **Do not restate `159.2157` as a fleet figure.** It survives only as evidence inside OPEN-49. The fleet figure is `157.1 kWh/m²`, **pooled** — total simulated energy ÷ total simulated floor area over 8,154 successful buildings.
7. **Append-only.** Progress-log entries under §8 are appended, one per task, never rewritten. Register edits are struck-and-dated, never deleted.
8. **`python` is not on PATH on this machine.** Use `.venv/Scripts/python.exe`.
9. **Do not propose alternatives — execute the plan.** If the plan is wrong, STOP and say which line is wrong and why. Three tasks in the last arc were improved exactly this way; a plan error found and quoted is a success, not a deviation.
10. **Every number you report must be re-derivable from a file on disk.** State the file and the command. "The test passed" is not a result; the output is.

---

## 3. File layout

**Shipped code you will modify (exactly three files, nothing else):**

| File | Why |
|---|---|
| `openubem/semantic/__init__.py` | T02 — the coupled draw (lines 211–246, 321, 340) |
| `openubem/results/parser.py` | T05 — the per-building denominator (line 301) |
| `openubem/results/aggregator.py` | T05 — the per-cell denominator (lines 139–141) |

**Tests you will add or extend:**

- `tests/test_semantic_unknown_draw.py` — **new** (T01, T03)
- `tests/test_results_denominator.py` — **new** (T06)

**Analysis scripts (new, under `scripts/analysis/`):**

- `scripts/analysis/open49_before_after_cells.py` (T04)
- `scripts/analysis/open01_denominator_swap.py` (T07)

**Outputs (flat, under `openubem/outputs/comparisons/`):**

- `open49_before_after_cells.csv` (T04)
- `open01_denominator_swap.csv` (T07)

**Docs you will append to:**

- this plan's §8 progress log (every task)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-49_before-after.md` (T04)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-swap.md` (T07)

**Read-only inputs, already on disk — do not regenerate:**

- `openubem/outputs/comparisons/e02_simulated_floor_area.csv` — **40,800 rows**, 0 parse failures, 0-unmatched join in both directions in all five modes (verified: header + `wc -l` = 40,801 with header)
- `openubem/outputs/comparisons/open01_denominator_audit.csv` — 40,800 rows
- `scripts/analysis/e02_t04_floor_area_audit.py` — the `.eio` parser that produced them. **Reuse `parse_eio_zone_area()` (line 56); do not write a second parser.**

---

## 4. Dependency decisions — pinned, do not revisit

| Decision | Pinned value | Rationale |
|---|---|---|
| Per-building seed source | `numpy.random.default_rng` seeded from a **stable hash of `osm_id` combined with `config.RANDOM_SEED`** | `osm_id` is the only identifier that survives re-fetch. Combining with the global seed keeps the run reproducible *and* keeps the existing seed knob meaningful. |
| Hash function | **`hashlib.blake2b(osm_id.encode(), digest_size=8)`**, interpreted as a little-endian `uint64` | Python's builtin `hash()` is **salted per process** (`PYTHONHASHSEED`) and would make runs irreproducible — the exact opposite of this fix. This is the single most likely way to get T02 wrong. |
| Fixed bounds source | **`_get_cross_archetype_loads()`** (`openubem/semantic/__init__.py:436` → `openubem/semantic/loads.py::_get_flat_loads`) | It is the full archetype loads table and **already exists in this file**, used at line 340 as the all-Unknown fallback. Using it always makes the bounds fixed **without inventing a single number** — which this project's rules forbid. |
| Columns covered | All **four** PDE columns (`lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person`, `wwr`) **and** the four `scalar_cols` setpoints | See §5 fact 3 — the setpoints take a `median()` over the same table and carry the same coupling. |
| `numpy` / `pandas` versions | **unchanged** — pin nothing new, add no dependency | `hashlib` and `numpy` are already imported. |
| EUI denominator | `area_multiplier_aware_m2` from `eplusout.eio`, Σ(`Floor Area` × `Zone Multiplier` × `Zone List Multiplier`) over zones with `Part of Total Building Area = Yes` | Ruling 6, verbatim. |
| `.eio` location at parse time | `sql_path.parent / "eplusout.eio"` | §5 fact 5 — no signature change needed. |
| Missing `.eio` behaviour | **Fall back to `footprint_area × num_floors` and set a provenance flag.** Never crash, never silently substitute. | Every fleet harvested before 2026-08-10 has no local `.eio` (OPEN-37). A hard failure would make historical results unparseable. |

---

## 5. Facts established by the director, with line citations

Each of these was read at the source line, not inferred. **Verify each one before you rely on it** — if a line has moved, STOP and report the drift rather than guessing the new location.

**Fact 1 — the draw is one vectorised block sized by the Unknown count.**
`openubem/semantic/__init__.py:228-232`:
```python
n = unk_mask.sum()
for col in pde_cols:
    lo, hi = real_loads[col].min(), real_loads[col].max()
    vals = rng.uniform(lo, hi, size=n)
    result[col] = vals
```
`n` changes ⇒ every drawn value changes. This is the first coupling route, and it is the one OPEN-49 measured on `nyc_centre` (+3.53, exactly 4 buildings moved `Courthouse` → `OpenUBEMUnknown`).

**Fact 2 — the bounds come from whichever archetypes are present.**
Same lines: `lo, hi = real_loads[col].min(), real_loads[col].max()`, where `real_loads` is `loads_real` — the table of archetypes **present in this cell** (`openubem/semantic/__init__.py:340`). This is the second, independent route, and it is what moved `austin_centre` (+1.76), `la_centre` (+1.60) and `la_urban` (+1.21) **at unchanged Unknown count**.

**Fact 3 — the coupling is wider than OPEN-49 records, and the register does not yet say so.**
`pde_cols` at `openubem/semantic/__init__.py:225` is:
```python
pde_cols = ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person", "wwr"]
```
Four columns, not one. And `openubem/semantic/__init__.py:234-235` gives the four `scalar_cols` setpoints a `real_loads[col].median()` — **also** over present archetypes. **Eight fields carry this defect; OPEN-49 documents one.** It was registered as a window defect because windows are where the ±300 kWh/m² was measured. T08 records this.

**Fact 4 — one RNG per run, shared across every draw, so the streams are position-coupled.**
`openubem/semantic/__init__.py:297`: `rng = np.random.default_rng(random_seed)  # F14: one RNG per run`, with `config.RANDOM_SEED = 42` (`openubem/config.py:62`). `_build_unknown_envelope` is called **first** (`:321`) and consumes the same generator via `get_construction_set(..., rng=rng)` (`:204`), so a change in Unknown count shifts the stream position for the loads draw that follows at `:340`. Per-building keying dissolves this by construction.
⚠️ **Bounded, not asserted:** the §3E probabilistic KDE branch (`:351`) perturbs **real** rows off the same generator, which would extend the blast radius to identified buildings — but `openubem/config.py:61` pins `LOAD_MODE = "deterministic"`, so **that branch is off in the adopted configuration.** Do not claim identified buildings moved. T01 tests the deterministic path only.

**Fact 5 — the per-building denominator is `footprint × floors`, at one line.**
`openubem/results/parser.py:299-301`:
```python
num_floors = derive_num_floors(row)
footprint_area = float(row["footprint_area_m2"])
floor_area = footprint_area * num_floors
```
Every EUI column divides by this single local (`:312`, `:332-347`), and `total_eui_kwh_m2` (`:354`) is their sum. **One assignment governs all of them** — the swap is genuinely a one-line change plus its plumbing.

**Fact 6 — the per-cell denominator repeats the same formula independently.**
`openubem/results/aggregator.py:139-141`:
```python
gdf["_floor_area"] = gdf.apply(
    lambda r: float(r["footprint_area_m2"]) * derive_num_floors(r), axis=1
)
```
Changing `parser.py` alone leaves the aggregator weighting by the old area. **Both must move together or the cell EUIs become internally inconsistent.**

**Fact 7 — `parse_building` already has the path it needs.**
`openubem/results/parser.py:549-552` takes `sql_path`. The `.eio` is a sibling of `eplusout.sql` in every run directory. **No signature change is required anywhere** — read `sql_path.parent / "eplusout.eio"`.

**Fact 8 — ruling 6's own scope limit, which must survive into the code comments.**
The swap makes `building` mode **internally consistent, not physically representative**: that mode simulates one storey, so after the swap its EUI answers *energy per simulated m²*, which for a multi-storey building is not the real building's area. Ruling 6 states this explicitly and states that fixing the simulation was **offered and not taken**.
⚠️ **The adopted baseline does not move:** `auto` measures median error factor **1.0000, 99.63% within ±1%**, so `157.1` is unchanged by this remedy. Anyone reading T07's output as a restatement of the fleet number has misread it.

---

## 6. Task list

### T01 — Pin the defect with a test that FAILS on today's code

**What.** Add `tests/test_semantic_unknown_draw.py` with one test that reclassifies a single building in a small synthetic cell and asserts that **every other Unknown building's four PDE columns are unchanged**. On today's code this test **must fail**.

**Why.** This project's evidence rule is that the old behaviour is demonstrated *first*. A regression test written after a fix proves only that the code does what it does. The last arc caught a **vacuous** test this way — one that pinned a value against itself — so the bar here is explicit: the expected values must come from somewhere other than the code under test.

**How.**
1. Build a synthetic `GeoDataFrame` with ~6 buildings: 2 identifiable archetypes and 4 `OpenUBEMUnknown`.
2. Run the semantic enrichment; record the four PDE columns for the 4 Unknown rows.
3. Flip **one** identified building to a different archetype (this changes which archetypes are "present" — route 2) and, in a second case, flip one identified building to Unknown (this changes `n` — route 1).
4. Re-run; compare the **other three** Unknown rows' PDE columns.
5. Assert equality. Expect failure on both routes.

**How to test.** `.venv/Scripts/python.exe -m pytest tests/test_semantic_unknown_draw.py -v` — **run alone** (rule 2). Report the actual assertion output, including the magnitude of the drift per column. **Do not fix anything in T01.** A measurement task contains no remedies.

---

### T02 — Make the draw per-building and the bounds fixed

**What.** In `openubem/semantic/__init__.py`: (a) key every Unknown row's draw to a stable per-building seed; (b) always source bounds and medians from `_get_cross_archetype_loads()` rather than from the cell's present archetypes.

**Why.** (a) removes the block-size route, (b) removes the bounds route. Both are required — fixing one leaves the other live, and OPEN-49's own cell table proves each route moved cells on its own.

**How.**
1. Change the call at `:340` to pass `_get_cross_archetype_loads()` unconditionally. Keep the `loads_real` argument used for anything *other* than bounds/medians if such a use exists — **check first; if `real_loads` is used only for `.min()/.max()/.median()`, the change is total.**
2. In `_build_unknown_loads` (`:211`), replace the block `rng.uniform(lo, hi, size=n)` with a per-row draw seeded from `blake2b(osm_id)` ⊕ `config.RANDOM_SEED` (see §4 — **not** builtin `hash()`).
3. Do the same for `_build_unknown_envelope` (`:188`) **only if** T01 shows its outputs move; if it does not draw for Unknown rows in a size-dependent way, leave it and say so.
4. Preserve the `provenance_*` columns (`:241-246`) exactly — they are `PDE_GENERATED` / `HEURISTIC` and other code reads them.
5. The post-guard `heating < cooling` (`:237-239`) must still hold.

**How to test.** T01's test now **passes**, on both routes. Then prove it is not vacuous: temporarily change the seed derivation to a constant, confirm the test **fails**, restore. Report both outputs. Also run `.venv/Scripts/python.exe -m pytest tests/ -q` alone and confirm **zero** new failures against the baseline of **0 failed / 0 errors under `tests/`** established 2026-08-13.

---

### T03 — Extend the test to the setpoints and lock the eight fields

**What.** Extend `tests/test_semantic_unknown_draw.py` to cover the four `scalar_cols` setpoints as well as the four PDE columns.

**Why.** §5 fact 3 — the median-over-present-archetypes carries the identical defect and nobody has tested it. T02's bounds change should fix it for free; a test that does not check it cannot show that.

**How.** Same two routes as T01, asserting on all eight columns. Confirm the post-guard still holds after the change.

**How to test.** Suite alone. Report which of the eight columns moved **before** T02 and which move **after**. If any still move after T02, **STOP** — that is a third route nobody has found, and it is a finding, not a bug to patch quietly.

---

### T04 — Before/after on the twelve cells

**What.** `scripts/analysis/open49_before_after_cells.py` → `openubem/outputs/comparisons/open49_before_after_cells.csv` + `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-49_before-after.md`.

**Why.** Ruling 4 chose measurement over a fleet re-run, and CP-M3 (OPEN-31) makes a before/after **obligatory** for any change that moves classification-driven inputs. This task is what discharges that gate.

**How.** Re-run the semantic stage only — **not** EnergyPlus — for the twelve cells, old code vs new, and tabulate per cell: number of Unknown buildings; the eight columns' min/mean/max before and after; and the count of buildings whose `wwr` changed by more than 0.01. **Do not simulate.** If an input `.gpkg` for a cell is missing, say which and skip it — do not substitute another.

**How to test.** The four cells OPEN-49 identified as moving (`nyc_centre`, `austin_centre`, `la_centre`, `la_urban`) must appear in the output with a non-zero before/after delta; the eight that reproduced to ±0.07 should show a **smaller** delta. Report the actual numbers either way — **if the pattern does not reproduce, that is the result**, and it means OPEN-49's mechanism story is incomplete.

> ⚠️ **State plainly in the `.md`:** this measures the change in *inputs*, not in EUI. **No EUI claim may be made from this task**, because no simulation was run. The ±300 kWh/m² figure belongs to OPEN-49's original measurement and is not re-derived here.

---

### 🛑 CP-1 — STOP after T04

Report: T01's failure output, T02's diff and its non-vacuity proof, T03's eight-column table, T04's twelve-cell CSV, and the full-suite result run **alone**. Do not start T05 until the director has signed CP-1.

---

### T05 — Swap the denominator in both layers

**What.** `openubem/results/parser.py:301` and `openubem/results/aggregator.py:139-141` divide by the multiplier-aware simulated area from `eplusout.eio`.

**Why.** Ruling 6, verbatim. No re-simulation, no cluster work, no `.idf` change — the measurement already exists at 40,800 rows.

**How.**
1. Add a helper that reads `sql_path.parent / "eplusout.eio"` and returns Σ(`Floor Area` × `Zone Multiplier` × `Zone List Multiplier`) over zones with `Part of Total Building Area = Yes`. **Reuse `parse_eio_zone_area()` from `scripts/analysis/e02_t04_floor_area_audit.py:56`** — import it or lift it into the package, but do not write a second parser that could disagree with the one that produced the audit CSV.
2. In `parser.py`, set `floor_area` from that value; on a missing or unparseable `.eio`, fall back to `footprint_area × num_floors` **and record which was used** in a new provenance column.
3. In `aggregator.py`, weight by the same per-building value — read it from the results frame, do not re-parse.
4. Carry §5 fact 8 into a comment at the `building`-mode-relevant site: internally consistent, not physically representative.

**How to test.** Reproduce a known row: `la_urban/way_401904735` (`MidriseApartment`, 3 storeys) must give an error factor of **1.33331** against `4/3` — the director re-derived this independently at **0.0018% off**, with `Zone List Multiplier = 2`, 27 zones under `layout_assign` vs 3 under `auto` vs **1** under `building`, and declared area **1850.454098 × 3.0 = 5,551.362295**. If your parser disagrees with any of those, **STOP** — one of the two parsers is wrong and it matters which.

---

### T06 — Regression-test the fallback and the swap

**What.** `tests/test_results_denominator.py`.

**Why.** The fallback path is the dangerous one: every pre-2026-08-10 harvest has no local `.eio`, so the fallback will run often, and a silent switch between two denominators is exactly the kind of thing that produces an unexplainable number a year later.

**How.** Three cases: `.eio` present and well-formed → simulated area used, provenance says so; `.eio` absent → fallback used, provenance says so, **no exception**; `.eio` present but malformed → fallback used, provenance says so. Assert the provenance value in all three, not just the number.

**How to test.** Suite alone. Prove non-vacuity by mutating the expected provenance string and confirming failure.

---

### T07 — Before/after per building, all five modes

**What.** `scripts/analysis/open01_denominator_swap.py` → `openubem/outputs/comparisons/open01_denominator_swap.csv` + `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-swap.md`.

**Why.** Ruling 6 names this explicitly as one of the three things owed to close OPEN-01.

**How.** Join E02's 40,800 rows to their EUIs; compute old-denominator and new-denominator EUI per building; report per mode: median error factor, % within ±1%, and the EUI shift distribution.

🔴 **Report deciles, never the median alone.** The `error_factor` distribution is quantised at powers of two (`[0.316, 0.474, 1.000, 1.999, 4.000]`) because it is multiplier-and-storey arithmetic, and it is log-symmetric — **so a median of 1.0000 can sit on top of a badly split population.** `layout_assign` is the standing proof: median 0.9999 with only **2.05%** of non-`applied` rows within ±1%. A median-only summary of this dataset is actively misleading.

**How to test.** These must reproduce from the existing audit: `auto` **1.0000 / 99.63%**, `floor` 1.0000 / 98.43%, `fast_zone` 1.0000 / 94.80%, `layout_assign` 0.9999 / **15.37%**, `building` **0.5000 / 39.94%**. Any disagreement means the join is wrong — the audited join is **8,160 matched / 0 unmatched in both directions in every mode**.

> ⚠️ **The `.md` must open with the reassurance, not bury it:** `auto` is the adopted mode and it measures 1.0000 / 99.63%, so **the published fleet figure of `157.1 kWh/m²` pooled does not move.** Ruling 4 forbids a fleet re-run and no headline is being restated.

---

### T08 — Update the register, the director prompt, and the checklist

**What.** Three documents, in this order.

**Why.** The standing rule is that a task is not done until the register, the prompt and the checklist all reflect it. This is where the §5-fact-3 widening gets recorded — **it is the one genuinely new finding in this plan and it must not be lost in a progress log.**

**How.**
1. **Register, OPEN-49** — a struck-and-dated amendment recording: the remedy authorised by ruling 2; the fix as landed; T04's before/after; and the widening (**eight fields, not one** — four PDE columns and four setpoints). ⚠️ **OPEN-49 does not close on this plan.** OPEN-48 still needs a third fleet run to reproduce `157.1` end to end, and ruling 4 declined it. Record OPEN-49 as *mechanism fixed, closure blocked on the re-run the user chose not to take.*
2. **Register, OPEN-01** — record the swap, T07's five-mode table, and the two ruling-6 corrections (`building` mode internally-consistent-not-representative; the adopted baseline unmoved). Close OPEN-01 **only if** all three things ruling 6 named are delivered; otherwise say which is missing.
3. **Director prompt §5.15** and **`docs/PROJECT_CHECKLIST.md`** — a short journal block each. Plain language; the checklist is the user's monitoring surface, not an audit trail.

**How to test.** Re-count the register table programmatically (live rows, struck rows, total) and state the arithmetic. The last two passes both found miscounts in the prose header while the table itself was correct.

---

### 🛑 CP-2 — STOP after T08

Report everything, **including one full-suite run executed alone**. **A checkpoint that cannot be re-derived from raw artifacts is a STOP.**

---

## 7. Stop-and-report points

| Checkpoint | After | What must be in hand |
|---|---|---|
| **CP-1** | T04 | T01's pre-fix failure, T02's non-vacuity proof, T03's eight columns, T04's twelve cells, suite alone |
| **CP-2** | T08 | T05's `1.33331` reproduction, T06's three fallback cases, T07's five-mode deciles, all three docs updated, suite alone |

---

## 8. Progress log

*(Executor appends one entry per completed task, in the form `#### TXX — <title> — completed YYYY-MM-DD` followed by Artifacts / Deviations / Test status / Notes. Never rewrite an earlier entry.)*

#### T01 — Pin the defect with a test that FAILS on today's code — completed 2026-08-17

**Artifacts.** `tests/test_semantic_unknown_draw.py` (already present in the tree at dispatch, unsigned — signed off here). No source files touched for T01 itself.

**Deviations.** None from the plan text. Per the dispatch note, T01's proof had never been produced; this entry supplies it. Pre-fix source was obtained with `git show 82bbd25^:openubem/semantic/__init__.py` (read-only), written over the tree file with a plain `cp` (never `git restore`/`checkout`/`stash`), tested, then restored from a scratch backup; `git status --porcelain` on `openubem/semantic/__init__.py` was empty both before the swap and after the restore.

**Test status.** `.venv/Scripts/python.exe -m pytest tests/test_semantic_unknown_draw.py -v`, run alone, **against pre-fix source**: **2 failed**. Per-column drift at failure (four PDE columns only, this was the original 4-column test at the time of this run):
- route 1 (block-size, n 4→5): `lighting_w_m2` 0, `equipment_w_m2` max|Δ|=3.88298 (deltas 0.3748/3.8830/3.0293/3.1285), `occupant_m2_per_person` 0, `wwr` 0.
- route 2 (present-archetype bounds, SmallOffice→LargeDataCenterHighITE): `lighting_w_m2` max|Δ|=2.44649, `equipment_w_m2` max|Δ|=5240.36, `occupant_m2_per_person` max|Δ|=68.8772, `wwr` max|Δ|=0.231828.

Both tests fail genuinely (real, non-zero, non-vacuous drift) — the test is not wrong; no test edit was needed. Same test run **against post-fix (current) source**: **2 passed** in 1.08s.

**Notes.** Full captured output for both runs is in the CP-1 report below.

---

#### T02 — Make the draw per-building and the bounds fixed — completed 2026-08-17

**Artifacts.** `openubem/semantic/__init__.py` (already in the tree at commit `82bbd25`, unsigned — signed off here): `_per_building_rng()` at :212 (`blake2b(osm_id)` combined with `config.RANDOM_SEED` via `default_rng`'s `SeedSequence` entropy mixing), per-row draw loop in `_build_unknown_loads` at :251-253, unconditional `_get_cross_archetype_loads()` at the `enrich_semantics` call site (:366).

**Deviations.** None. `real_loads` in `_build_unknown_loads` is used only for `.min()/.max()/.median()` (bounds dict at :248 and `scalar_cols` medians at the block below it) — confirmed by reading the function body — so the fix is total per the plan's own instruction at task step 1. `_build_unknown_envelope` was checked (see below) and found **not** to need the same treatment; left unchanged, as the plan's step 3 permits.

**Test status.**
- T01's test passes on both routes on post-fix code (see T01 entry).
- **Non-vacuity proof, attempt 1 (rejected as not probative):** changed `_per_building_rng` to ignore `osm_id` and always derive the seed from `(config.RANDOM_SEED, 0)` — still fresh-instantiated per row. Result: **2 passed** (no failure). Reasoned and confirmed empirically that this probe cannot fail: with bounds already fixed and each row re-seeding independently of position, per-row draws are order/count-invariant regardless of whether `osm_id` is honored, so this edit does not reintroduce either route. Reverted.
- **Non-vacuity proof, attempt 2 (accepted):** changed the loop in `_build_unknown_loads` to use the shared `rng` argument directly instead of `_per_building_rng(osm_id)` (i.e. reintroduces a constant/shared stream across rows, the actual pre-T02 mechanic, bounds fix left in place). Result: `test_route1_block_size_couples_unknown_draws` **FAILED** (max|Δ| up to 10.8357/4082.65/179.506/0.209858 across the four PDE columns), `test_route2_present_archetype_bounds_couple_unknown_draws` **PASSED** (bounds fix alone already neutralises route 2). This is exactly the expected split and proves the test detects a real regression. Reverted; `git status --porcelain` on the file confirmed empty after revert.
- `_build_unknown_envelope` check: wrote a read-only probe script running both T01 scenarios and diffing the six envelope value columns (`u_roof_w_m2k`, `u_wall_w_m2k`, `u_window_w_m2k`, `u_floor_w_m2k`, `shgc_window`, `infiltration_m3_s_m2`) for the four Unknown rows. **All deltas 0.0 under both routes.** Traced the reason: the bundled construction table is gap-free (per `get_construction_set`'s own docstring), so its only `rng`-consuming path (KDE gap-fill) never executes for the fixed `MediumOffice@DOERefPre1980` donor under the adopted (non-custom-table) configuration — `_build_unknown_envelope` does not draw for Unknown rows in a size-dependent way. Left unchanged, as instructed.
- Full-suite run alone (first pass, later superseded — see T03 note): `.venv/Scripts/python.exe -m pytest tests/ -q`, **1868 passed, 55 skipped, 0 failed**, 1391.73s (0:23:11).

**Notes.** This first full-suite run predates the T03 test-file edit (file modified 21:19, this run started ≈21:08) and is therefore superseded by the run recorded under T03/CP-1.

---

#### T03 — Extend the test to the setpoints and lock the eight fields — completed 2026-08-17

**Artifacts.** `tests/test_semantic_unknown_draw.py` — added `_SCALAR_COLS`/`_ALL_COLS`, extended both `test_route1_...`/`test_route2_...` to assert on all eight columns, added `_assert_post_guard_holds()` and called it on both base and modified frames in both tests.

**Deviations.** None.

**Test status.**
- Post-fix (current) code: **2 passed** in 0.71s.
- Pre-fix code (same swap/restore procedure as T01, `git status --porcelain` empty before and after): **2 failed**. Per-column drift:
  - route 1 (block size): `lighting_w_m2` 0, `equipment_w_m2` max|Δ|=3.88298, `occupant_m2_per_person` 0, `wwr` 0, **all four scalar setpoints 0** (route 1 changes `n` for the PDE block only; the setpoint `.median()` is computed once over `real_loads`, unaffected by Unknown count).
  - route 2 (present-archetype bounds): `lighting_w_m2` max|Δ|=2.44649, `equipment_w_m2` max|Δ|=5240.36, `occupant_m2_per_person` max|Δ|=68.8772, `wwr` max|Δ|=0.231828, `heating_setpoint_c` max|Δ|=1.4, `cooling_setpoint_c` max|Δ|=1.4, `heating_setback_c` max|Δ|=1.35, `cooling_setup_c` max|Δ|=1.35 — **all eight columns move**, confirming Fact 3 exactly.
  - After T02: **none** of the eight columns move on either route (both tests pass in full). No third route found; no STOP triggered.
- Full-suite run alone, **after** this test-file edit landed (supersedes T02's run): `.venv/Scripts/python.exe -m pytest tests/ -q`, **1868 passed, 55 skipped, 0 failed**, 11 warnings, 1663.13s (0:27:43). Identical pass/skip counts to the earlier run — zero new failures.

**Notes.** Table: which of the eight columns moved before T02 and after T02.

| column | route 1, pre-T02 | route 2, pre-T02 | post-T02 (either route) |
|---|---|---|---|
| `lighting_w_m2` | no (Δ=0) | **yes** (max|Δ|=2.446) | no |
| `equipment_w_m2` | **yes** (max|Δ|=3.883) | **yes** (max|Δ|=5240.36) | no |
| `occupant_m2_per_person` | no (Δ=0) | **yes** (max|Δ|=68.877) | no |
| `wwr` | no (Δ=0) | **yes** (max|Δ|=0.2318) | no |
| `heating_setpoint_c` | no (Δ=0) | **yes** (Δ=1.4) | no |
| `cooling_setpoint_c` | no (Δ=0) | **yes** (Δ=1.4) | no |
| `heating_setback_c` | no (Δ=0) | **yes** (Δ=1.35) | no |
| `cooling_setup_c` | no (Δ=0) | **yes** (Δ=1.35) | no |

---

#### T04 — Before/after on the twelve cells — completed 2026-08-17

**Artifacts.** `scripts/analysis/open49_before_after_cells.py` (new); `openubem/outputs/comparisons/open49_before_after_cells.csv` (12 rows, one per cell); `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-49_before-after.md`.

**Deviations.** None from file layout. **Result deviates from the plan's stated expectation in §6/T04's "How to test"** — reported per the plan's own instruction to do so ("if the pattern does not reproduce, that is the result"): the four OPEN-49-moving cells do **not** show a distinctly larger before/after delta than the eight reproducing cells; nearly every cell shows almost all of its Unknown buildings' `wwr` moving by >0.01, tracking cell size (Unknown-row count) rather than moving/reproducing status. Full explanation of why the two experiments (old-code-vs-new-code at fixed classification, vs. OPEN-49's original two-classification-snapshots-at-fixed-code) are orthogonal axes is in the `.md`. This is not treated as a plan error requiring STOP — the plan's own text at T04 anticipates and authorises reporting a non-reproducing pattern as a valid result.

**Test status.** Both raw passes (pre-fix and post-fix source, same swap/restore discipline as T01/T03) wrote **8,160 rows each** — all twelve cells present, zero skipped, matching the fleet total exactly. `git status --porcelain` on `openubem/semantic/__init__.py` confirmed empty after the final restore.

**Notes.** Summary (full eight-column min/mean/max before/after in the CSV):

| cell | moving cell (OPEN-49 original)? | n Unknown | n `wwr` changed >0.01 |
|---|---|---:|---:|
| austin_centre | yes | 37 | 34 |
| austin_rural | no | 7 | 7 |
| austin_suburban | no | 24 | 23 |
| austin_urban | no | 5 | 4 |
| la_centre | yes | 15 | 14 |
| la_rural | no | 0 | 0 |
| la_suburban | no | 2 | 2 |
| la_urban | yes | 2 | 2 |
| nyc_centre | yes | 35 | 29 |
| nyc_rural | no | 5 | 5 |
| nyc_suburban | no | 290 | 272 |
| nyc_urban | no | 228 | 218 |

No EUI claim is made from this task — only semantic-stage inputs were measured; EnergyPlus was not run.

---

#### T05 — Swap the denominator in both layers — completed 2026-08-17

**Artifacts.** `openubem/results/parser.py`: `parse_eio_zone_area()` (verbatim lift of
`scripts/analysis/e02_t04_floor_area_audit.py:56`, comment cites the source and says not to let the
two drift apart) and `resolve_simulated_floor_area(sql_path, footprint_area, num_floors)` →
`(floor_area_m2, provenance)`; `parse_building()` resolves this once per building (before any parse
attempt) and carries `floor_area_m2`/`floor_area_provenance` through the success return **and** every
`_failed_row()` path. `openubem/results/aggregator.py`: `compute_neighbourhood_summary()` reads
`floor_area_m2` from the joined results frame (added to `_STEP5_COLS`) instead of recomputing
`footprint_area_m2 × derive_num_floors()`.

**Deviations.** One, deliberate, to protect ~20 pre-existing direct tests of `_compute_eui()`
(`tests/test_parser_elevators.py`, `tests/test_parser_hvac_metered.py`, `tests/test_results_parser.py`)
that call it with the old `(df, row, dq_flag, meters=...)` signature: `_compute_eui()` keeps `row` as
its second positional argument and gained an **optional** `floor_area: float | None = None` keyword —
when omitted (every pre-existing call site), it falls back to the exact pre-OPEN-01
`footprint_area_m2 × derive_num_floors(row)` computation, unchanged; `parse_building()` is the only
caller that supplies it. This was not in the plan's §6 text but is required by hard rule "exactly
three files, nothing else" — changing `_compute_eui()`'s required signature would have forced edits to
three test files outside that list. A second, smaller collateral edit: `tests/test_results_aggregator.py`'s
`_make_metrics_df()` fixture gained `floor_area_m2`/`floor_area_provenance` keys (set to `392.0` /
`"footprint_fallback"` for success rows, matching `_make_enriched_gdf()`'s `196.0 × 2.0` exactly, and
`nan`/`""` for the failed row) — required because `test_step5_cols_appended` asserts the joined
columns equal `_STEP5_COLS` exactly, which now includes the two new columns; the values chosen
reproduce the pre-existing `test_floor_area_weighted_eui` hand-computed expectation bit-for-bit, so no
other aggregator test's expected numbers moved.

**Test status.** `la_urban/way_401904735` (`MidriseApartment`, 3 storeys) reproduced against the real
harvested `eplusout.sql`/`.eio`: `resolve_simulated_floor_area()` on the `layout_assign` run returned
**7,401.680000 m²**, `error_factor = 7401.68 / 5,551.362294 = 1.3333087642288914` — matches the
director's independently re-derived **1.33331 at 0.0018% off**, `Zone List Multiplier = 2`, and the
existing `open01_denominator_audit.csv` row's `1.333309` exactly. `building` mode returned
**1,850.45 m²**, `error_factor = 0.33333259513615165` — matches the audit's `0.333333`. **No
disagreement between the lifted parser and the audit's parser; T05 did not STOP.**
`.venv/Scripts/python.exe -m pytest tests/test_parser_elevators.py tests/test_parser_hvac_metered.py tests/test_results_aggregator.py tests/test_results_carbon.py tests/test_results_parser.py -q`,
run alone: **117 passed**, 3 warnings, 31.06s.

**Notes.** `_compute_eui()`'s docstring now carries §5 fact 8 (building mode internally consistent, not
physically representative) at the site the plan named. `aggregator.py`'s fallback (per-row
`pd.to_numeric(...).fillna(footprint×floors)`) means rows without a `floor_area_m2` column (synthetic
GeoDataFrames built directly, never routed through `parse_building()`) are computed exactly as before
OPEN-01 — this is what keeps `tests/test_results_aggregator.py`'s `TestAggregateResults` class (which
uses real golden-SQL fixtures with no `.eio` siblings) numerically unchanged without any edit.

---

#### T06 — Regression-test the fallback and the swap — completed 2026-08-17

**Artifacts.** `tests/test_results_denominator.py` (new, 7 tests): `TestResolveSimulatedFloorAreaThreeCases`
(4 tests — `.eio` present/well-formed, `.eio` absent, `.eio` present/malformed via a header-then-EOF
file, `sql_path=None`) and `TestParseBuildingFloorAreaProvenance` (3 tests — end-to-end through
`parse_building()` with a copied golden SQL + synthetic `.eio` in `tmp_path`, confirming the EUI
columns actually scale by the area ratio and not just the metadata column; the real golden-fixtures
directory as-is, pinning that every existing golden-SQL test exercises the fallback path since that
shared directory has no `.eio` siblings; a failed-parse case).

**Deviations.** None from the plan text.

**Test status.** `.venv/Scripts/python.exe -m pytest tests/test_results_denominator.py -v`, run alone:
**7 passed**, 0.66–0.77s across runs. **Non-vacuity proof:** every `assert provenance == "..."` /
`assert result[...]["floor_area_provenance"] == "..."` (8 occurrences across all 7 tests) mutated to
`"WRONG_PROVENANCE"` via `sed`; re-run: **all 7 failed genuinely** (real string mismatches, not
collection errors). Reverted from a scratch backup; `git status --porcelain
tests/test_results_denominator.py` showed only the expected untracked-new-file line before and after
(confirms the revert matched the pre-mutation content); re-ran: **7 passed** again.

---

#### T07 — Before/after per building, all five modes — completed 2026-08-17

**Artifacts.** `scripts/analysis/open01_denominator_swap.py` (new) →
`openubem/outputs/comparisons/open01_denominator_swap.csv` (40,800 rows) +
`openubem/outputs/comparisons/open01_denominator_swap_summary.csv` (5 rows, one per mode, with
`eui_shift_pct` deciles) + `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-swap.md`.

**Deviations.** None from file layout. One method note, stated in the `.md`'s own "Method" section, not
hidden: per-mode `total_eui_kwh_m2` only exists on disk for the `auto`-mode canonical
`05_results.csv` per cell (no per-mode Step-5 results were ever harvested for the other four modes —
only their `.eio`/manifest artifacts exist). `old_eui_kwh_m2`/`new_eui_kwh_m2`/`eui_shift_pct` are
therefore computed as an exact algebraic transform of that one real EUI value
(`new = old / error_factor`, valid because energy is invariant and only the divisor changes), not a
claim that the other four modes were re-parsed — the `.md` states this explicitly, twice.

**Test status.** `.venv/Scripts/python.exe scripts/analysis/open01_denominator_swap.py`: all five
targets reproduced exactly — `auto` median 1.0000 / 99.63% within ±1%, `floor` 1.0000 / 98.43%,
`fast_zone` 1.0000 / 94.80%, `layout_assign` 0.9999 / 15.37%, `building` 0.5000 / 39.94%. Join: 8,160
matched / 0 unmatched (error_factor) per mode; `n_eui_available` = 8,154 per mode (the standing fleet
successful-building count). Deciles reported per mode in the `.md` (not median alone, per rule):
`auto`/`floor`/`fast_zone` sit within thousandths of a percent at every decile; `building` splits
sharply (~30% near 0%, rest near +100%/+200%/+400%, matching "one simulated storey" exactly);
`layout_assign` spans −75% to +217%.

**Notes.** The `.md` opens with the reassurance (auto 1.0000/99.63%, fleet figure unchanged) before any
other content, per the plan's own instruction.

---

#### T08 — Update the register, the director prompt, and the checklist — completed 2026-08-17

**Artifacts.** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`: OPEN-01's heading and
§1 table row struck and marked `CLOSED 2026-08-17`, with a full closure block (the swap as landed, the
T05 reproduction, T06's non-vacuity, T07's five-mode table and deciles, the two ruling-6 corrections,
what the closure does not do) inserted after the heading; §1 summary header amended with a new dated
count (28 live / 24 struck / 52 total, fifteen IDs retired in all — arithmetic re-derived below).
OPEN-49's heading amended to `MECHANISM FIXED 2026-08-17 — CLOSURE BLOCKED`; a struck-and-dated
amendment appended recording the fix as landed, the Fact-3 widening (eight fields, not one, with the
T03 pre/post table's numbers), T04's before/after result, and why closure is blocked (OPEN-48's
re-run, declined by ruling 4) — OPEN-49 is **not** counted as closed in the §1 recount.
`docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`: one journal block appended
to the end of §5.16 (the section already covering this exact plan), immediately before §5.17's
heading — confined to that single insertion, §5.17 and the file header (both under concurrent director
edit per the dispatch note) untouched. `docs/PROJECT_CHECKLIST.md`: one dated block inserted after the
existing "OPEN-01 still does not close" paragraph, in plain language, recording the closure and
OPEN-49's non-closure in the same terms as the register.

**Deviations.** One, disclosed per the dispatch note's own instruction: the plan's §6 text says "a
short journal block to director prompt §5.15", but by 2026-08-17 §5.15 is already an unrelated,
long-finished section (the 2026-08-13 five-more-items sweep) and §5.16 is the section titled exactly
for this plan ("The OPEN-49 + OPEN-01 plan of 2026-08-13"), already containing "T05–T08 has not run"
language this entry supersedes. Appended to the end of §5.16 rather than §5.15 or the concurrently-edited
§5.17, on the reading that the plan text's "§5.15" was written 2026-08-13 before §5.16/§5.17 existed and
meant "the next section," which by dispatch time was §5.16. Flagged here rather than treated as silent.

**Test status.** Register table re-counted programmatically: `grep -c "^|"` over the table's line range
= 54 (52 data rows + 1 header + 1 separator); `grep -c "^| ~~"` = 24 struck (including
`~~**OPEN-43**~~`'s bold-inside-strike form, checked by hand since the plain `~~OPEN-XX~~` pattern
alone undercounts by one); live = 52 − 24 = **28**. **28 live rows, 24 struck rows, 52 total** —
unchanged total (OPEN-01 moved from live to struck; no row added or removed), matching "OPEN-01 …
OPEN-52 with no row missing and none duplicated."

**Notes.** OPEN-02 and OPEN-28 (folded under OPEN-01 per the register's own umbrella rule, "OPEN-02 and
OPEN-28 close with it") are not given separate table rows or headings — they were never split out as
independent rows to begin with (per the pre-existing umbrella section), so nothing further was struck
for them; OPEN-01's own closure is what the umbrella's rule already promised would discharge them.

**Correction (director audit, 2026-08-17).** The "fifteen IDs retired in all" figure in this entry's own **Artifacts** paragraph above and the same figure originally written into the register's §1 header are **both wrong — the correct total is twenty-two.** The error: this entry's count was taken from the register's stale trailing parenthetical (which stopped at "fourteen" after OPEN-22 on 2026-08-13 and was never updated by the two later closure passes), rather than from the correct running total already sitting in the same line's struck-header lineage (which read twenty-one before this task). **Caught by the director**, who independently re-derived the running total: ten (OPEN-23, OPEN-21, OPEN-05, OPEN-25, OPEN-30, OPEN-33, OPEN-34, OPEN-39, OPEN-40, OPEN-41) + 3 (OPEN-04, OPEN-31, OPEN-43) = 13, +1 (OPEN-22) = 14, +5 (OPEN-26, OPEN-36, OPEN-44, OPEN-45, OPEN-50) = 19, +2 (OPEN-24, OPEN-32) = 21, +1 (OPEN-01) = **22**. Fixed in the register at both places the wrong figure appeared, and the stale trailing parenthetical struck-and-dated (not rewritten) with a corrected, fully-enumerated replacement — see `INVESTIGATION_open-items-register.md` §1. **Reconciliation, stated so it is not miscounted again:** the table carries **24 struck rows against only 22 retired IDs**; the difference of exactly 2 is **OPEN-02 and OPEN-28**, both struck (discharged 2026-08-11) but never independently-opened tracked IDs, so neither was ever "retired." The live/struck/total counts (28/24/52) and the table itself were not touched by this correction — only the retired-ID prose.

---

### 🛑 CP-2 — STOP after T08

See report following this progress log for the full-suite result and summary.
