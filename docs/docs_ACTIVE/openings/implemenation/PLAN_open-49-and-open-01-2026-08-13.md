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
