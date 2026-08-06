# PLAN — The no-compute queue, round 2 (OPEN-35 · OPEN-12 · OPEN-06 · OPEN-13/14 · OPEN-15/16/17 · OPEN-10 · OPEN-19)

> **Slug:** `no-compute-queue-2` · **Opened:** 2026-08-06 · **Author:** manager session
> **Predecessor:** `PLAN_no-compute-queue.md` (N01–N05, all five landed and audited 2026-08-06).
> Opened as a **separate document** rather than extending the first, per the standing rule that a plan
> doc past ~1,000 lines is closed and continued in a new one.
> **Selected by:** the manager, at the user's standing instruction 2026-08-06 — *"continue avec des
> autres taches, et vas-y jusqu'a la fin pour completer toutes des taches pas necessaire d'utiliser des
> ressources CPU, en continu"* — and the earlier *"n'a pas besoin de me poser, tu peux choisir à
> toi-même et tu peux choisir plusieurs des tâches de faire."*
> **Binding upstream contract:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`.
> **Governing arc rule:** *no execution plan may be written for an item until that item's first
> measurement has been made.* Every task here **is** a first measurement, or the closing measurement an
> item explicitly asked for. **This is a measurement plan. Phase 2 does not exist and is not written.**

---

## 1. Why these seven, and why now

The five-mode local re-run (`PLAN_published-numbers.md` §9, E02) remains **parked by user instruction**
— the Speed allowance is consumed by another project and no CPU-bound work is to be scheduled. Nothing
about E02 is cancelled; it resumes when a machine is free.

Round 1 drained every register item whose first measurement was pure document tracing. What is left
that still costs **no simulation, no cluster, no fleet pass** is this:

| Task | Item(s) | What it costs | What it buys |
|---|---|---|---|
| **N06** | OPEN-35, OPEN-12 | table reads over 12 result files | the **size** of a confirmed defect that is currently unbounded |
| **N07** | OPEN-06 | code tracing | which step writes the wrong archetype — the one thing N04 could not answer |
| **N08** | OPEN-06/07 | reading local archives | whether the archetype column describes what was actually simulated |
| **N09** | OPEN-13, OPEN-14 | reading a closed arc | two items whose content has never been re-read |
| **N10** | OPEN-15, 16, 17 | document assembly | one decision the user has never been given the material to take |
| **N11** | OPEN-10 | IDD + code reading | the register's **only ❓** — a believed capability, never checked |
| **N12** | OPEN-19 | code + data reading | whether the named hypothesis is even representable in this pipeline |

**Only N06 and N08 can change a published number's interpretation.** N07, N09, N10, N11 and N12 are
completeness, correctness-of-record and decision-preparation items. That distinction matters when the
manager decides what goes to the user and what simply gets recorded.

---

## 2. Hard rules for the executor

These override anything you infer from the codebase, from prior plan docs, or from your own judgement.

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Interpreter `./.venv/Scripts/python.exe`.
2. **This is a MEASUREMENT plan. Remediation is FORBIDDEN.** You may not fix a defect you find, not
   even a one-line one, not even if the fix is obvious and correct. Record it and stop. You may not
   relabel a fixture, edit a test, edit the classifier, or amend a frozen document.
3. **No CPU-bound work of any kind.** No EnergyPlus. No IDF generation. No fleet pass. No cell pass.
   No cluster, ever — not `ssh`, not `srun`, not `sbatch`. Reading a `.gpkg`, a `.parquet`, a `.csv` or
   a file inside a `.zip` is a file read and is fine. **Running the pipeline is not.** If a task looks
   like it needs a pipeline run, you have misread it: **STOP and say so.** The whole point of this plan
   is that it costs no compute.
4. **Do not write a plan.** If you believe the plan is wrong, STOP and quote the conflict. The manager
   writes plans; you execute them.
5. **Never `git commit`.** Git is handled externally by the user. Do not offer.
6. **Never edit** root `main.py`, any `OVERVIEW` or `DESIGN` doc, anything under `docs_DONE/`,
   `docs_main/`, `docs_TODO/layoutgenerator/`, `layoutAssigner/figures/`,
   `openubem/idf/opaque_assembly.py`, `openubem/viz/`, or the `t17_*`/`t18_*`/`t19_*`/`t20_*` harvests.
   **Reading any of these is encouraged; writing to them is forbidden.**
7. **Do not edit the register** (`INVESTIGATION_open-items-register.md`). Every amendment to it is
   written by the manager after audit. Same for the director prompt.
8. **Progress-log entries are append-only.** Never rewrite an entry, including one you believe is
   wrong — correct it in a new entry that cites the old.
9. **A parser that finds nothing must say so, never report `0`.** A zero and an empty read are
   different results and must be distinguishable in your output. Likewise `NaN`, `None`, and
   "column absent" are three different findings and must never be collapsed into one.
10. **Recompute every headline number from the named file before you report it**, with a `path:line`
    or a reproducible command. Numbers that cannot be re-derived from a named artifact do not go in
    the report. **Do not carry a number forward from the register** — the register is the thing being
    checked.
11. **Ground truth is the raw artifact.** `eplusout.err` for run outcome (require the `** Severe **`
    line specifically). **Never the `.end` file.** **Never the `has_fatal` column** — it is `False` on
    all 8,160 rows including the 7 real fatals (E-LA-21, alias E-LA-39, now confirmed live in **four**
    harvest scripts).
12. **A status word at a document's defining line is not a current status.** Follow citations forward;
    never conclude from the first hit. Round 1 found this trap firing in *both* directions.
13. **Report an unknown as an unknown.** "Could not determine, because X" is a valid and valuable
    result in every task here. A fabricated resolution is not. If two sources disagree, **report both
    with their dates and do not adjudicate** — adjudication is the manager's.
14. **Default to no comments** in any throwaway script. Scripts go in your session scratchpad, never
    under `docs/` (**no `.py` under `docs/`, ever**) and never inside `openubem/`.

---

## 3. File layout to create

```
docs/docs_ACTIVE/openings/
├── INVESTIGATION_open-items-register.md    (existing — do NOT edit; the manager amends it)
├── implemenation/
│   └── PLAN_no-compute-queue-2.md          (this file — you append to §8 only)
└── extra/
    ├── MEASUREMENT_open-35-12_missing-input-census.md   (N06)
    ├── MEASUREMENT_open-06_archetype-writer-trace.md    (N07)
    ├── MEASUREMENT_open-06-07_simulated-archetype.md    (N08)
    ├── MEASUREMENT_open-13-14_utci-forwards.md          (N09)
    ├── MEASUREMENT_open-15-16-17_imputation-decision.md (N10)
    ├── MEASUREMENT_open-10_zonegroup-capability.md      (N11)
    └── MEASUREMENT_open-19_la-standard-basis.md         (N12)
```

Supporting CSVs go to `openubem/outputs/comparisons/` with an `open35_`/`open06_`/… prefix and are
cited by path from the measurement report. Any `.png` goes **flat** to `openubem/outputs/`, mirrored
into `docs/docs_ACTIVE/openings/extra/`.

---

## 4. Dependency decisions — pinned, do not re-debate

- **Python:** `./.venv/Scripts/python.exe`. **No new third-party dependency.** `pandas`, `geopandas`,
  `pyarrow`, `zipfile` (stdlib) are present and sufficient.
- **The fleet is these twelve cells, and no others:** `austin_centre`, `austin_rural`,
  `austin_suburban`, `austin_urban`, `la_centre`, `la_rural`, `la_suburban`, `la_urban`, `nyc_centre`,
  `nyc_rural`, `nyc_suburban`, `nyc_urban` — verified by directory listing 2026-08-06 under
  `docs/docs_VALIDATION/validations/overAll/results/phaseE/`. A census that covers 11 is not a census.
- **Per-cell artifacts available locally, verified 2026-08-06** (listing of `nyc_centre` and
  `la_rural`): `01_buildings.gpkg`, `04_simulation_manifest.parquet`, `05_results.gpkg`,
  `05_results.csv`, `05_results.geojson`, `05_results.schema.json`, `05_neighbourhood_summary.json`,
  `<cell>_step3_idfs_archive.zip`, `v12_<cell>_gates_report.txt`, `figures/`. `la_rural` additionally
  has `dropped_buildings.csv`; **not every cell has that file — check, do not assume.**
- **`05_results.gpkg` is not a fixed object across time.** M05 established that commit `0df422e`
  (2026-07-03) changed its `archetype_id` column between two harvests, reclassifying 13.40% of shared
  buildings. **Every task that reads it states which git state it read** (`git log -1 --format=%H --
  <path>`).
- **Statistical reporting:** report `n` and the full breakdown. A single percentage with no
  denominator is not an acceptable result in any task here.

---

## 5. Source-of-truth verified facts — grepped by the manager 2026-08-06

Read at HEAD by the manager this session. **You may rely on these without re-deriving them.** Anything
not on this list, you derive yourself and cite.

### 5.1 The two disagreeing storey-count fallbacks (N06's subject)

| Path | Stage | Fallback when **both** `levels` and `height_m` are missing | Verified at |
|---|---|---|---|
| `_impute_levels()` | 2 — **archetype selection** | the **group median over the batch** (19 for a full `nyc_centre`) | `openubem/semantic/building_classifier.py:138-142` |
| `derive_num_floors()` | 3 — **geometry construction** | **`1`**, flat | `openubem/geometry/footprint.py:58-63` |

Both were read from source by the manager. `_impute_levels` has a four-step ladder — observed `levels`
→ `height_m // 3.5` → group median → global median → `1` — emitting the tokens `OSM_OBSERVED`,
`HEURISTIC_HEIGHT`, `GROUPMEDIAN_LEVELS_MED`, `LEVELS_DEFAULT_LOW`. `derive_num_floors` has three and
emits nothing. **The imputed value is never persisted** — `building_classifier.py:636-639` holds a
byte-equality invariant that keeps the raw `levels`/`height_m` columns untouched through `classify()`
(established by N05). So the disagreement leaves **no trace in any output**, which is why the size has
to be measured from the *inputs*, not looked up in the results.

### 5.2 OPEN-12's recorded numbers, and their status
Register §5: `nyc_rural` **36.4%** and `austin_rural` **19.2%** of buildings carry no `height_m` after
the UTCI arc's backfill. Both are marked 📄 **documented, not re-derived**. Register §0's own rule:
*"never carry a 📄 or ⚠️ number into a plan without re-deriving it first."* **These two numbers are
therefore hypotheses for N06, not inputs.**

### 5.3 What N04 established, and the one question it did not answer
N04 (audited, `extra/MEASUREMENT_open-06-07-11_failure-population.md`):
- **41 of 8,160** buildings carry an Office archetype in `05_results.gpkg` while the classifier at HEAD
  produces a Hotel archetype from the same raw tags — recomputed from scratch, exact match to the
  register's 33 `LargeHotel` + 8 `SmallHotel`, **zero discrepancy**.
- **Verdict: SOURCE defect.** `openubem/semantic/building_classifier.py` is unchanged since `0df422e`
  and is **not** the culprit. Three raw `building_tag` values spot-checked: `hotel`, `hotel`, `motel` —
  one named *"Wilshire Serrano Motel"*, recorded as an office.
- N04's own closing note, verbatim: *"this task did not determine which specific pipeline step writes
  `05_results.gpkg`'s `archetype_id` (out of scope for measurement-only) — only that the live
  classifier is not the culprit."* **That is N07, and it is the whole of N07.**

### 5.4 The contradiction N08 exists to resolve
N04 found, from raw `eplusout.err` surviving locally at
`%LOCALAPPDATA%\Temp\ubem_t20_harvest\<cell>_layout_assign\way_<id>\eplusout.err`, that all three
OPEN-07 buildings fail with **one `** Severe **` each, in zone `LAUNDRYROOMFLR1`**, attributed by the
file's own Error Summary to the **Sizing** phase (not Warmup).

`LAUNDRYROOMFLR1` is a **hotel** room type. The three buildings are labelled `SmallOffice` in
`05_results.gpkg`. **An office prototype has no laundry room.** Either the label does not describe what
was simulated, or the zone name does not come from the archetype. **Both are findings. Nobody has
checked which.** The manager recorded this as unresolved rather than explaining it away.

### 5.5 The UTCI arc is closed, archived, and its two forwards were never re-read
Register §5, OPEN-13, verbatim: *"Forwarded out of the UTCI arc at close, to 'whichever arc next owns
Stage-1 acquisition or Stage-2 imputation'. **Content not re-read this session** — read
`docs_DONE/OUTDOOR/UTCI/` before planning."* The arc lives at `docs/docs_DONE/OUTDOOR/UTCI/`
(directory listing verified 2026-08-06: `UTCI_CHECKLIST.md`, `implementation/`, `results/`,
`resources/`, `prompt/`, `DeepResearches/`, `e-utci-09/`, `abstract-image/`).

`E-UTCI-12` and `E-UTCI-13` are mentioned in exactly **6 files** repo-wide (manager grep 2026-08-06):
`docs/PROJECT_CHECKLIST.md`, the register, `extra/MEASUREMENT_open-05_defect-id-sweep.md`,
`docs_DONE/OUTDOOR/UTCI/UTCI_CHECKLIST.md`,
`docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md`, and
`docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md`. **That is your
complete search space for N09 — it is small, so read all six.**

Note that the height-backfill sub-plan (`DONE-PLAN_e-utci-09_height_backfill.md`) is where **both**
OPEN-13 and OPEN-14 are likely to be settled, since OPEN-14 *is* about that backfill's
reproducibility. **Read it first.**

### 5.6 The imputation triple is one decision, and the constraint on it is hard-won
Register §5, OPEN-15/16/17, verbatim: *"These are one decision, not three: **does this project want a
non-deterministic input tier at all?**"* — and the binding constraint, recorded in project memory:
**NMBE is blind to variance collapse and must never be used alone as an imputation-accuracy metric**
(measured variance ratios 0.06–0.31). The CP-DRAW leaderboard found **no method dominates on every
axis**, and the promotion decision was never taken. **N10 assembles the decision; it does not take it,
and it does not recommend.**

### 5.7 OPEN-10 is the register's only ❓, and the reason is stated
Register §4, OPEN-10 (E-LA-37), verbatim: *"A different mechanism from the one built (which writes
`Zone.Multiplier`). Would restore exact storey matching at every `n_real` rather than only
`{10, 18, 26, …}` / even `n_real ≥ 4`. **Never tested** — this is a believed capability, not a measured
one. R04 is closed at option (a), so opening this is a deliberate reopening, not a continuation."*

**"Believed capability" is the phrase that makes this a task.** The claim is about what the
EnergyPlus input schema permits, and **the schema is a file on disk** — `Energy+.idd`, resolved by
`openubem/config.py:16,32` to the real 23.1 IDD (verified by N03). No simulation is needed to read a
schema.

### 5.8 OPEN-18 is adjacent to OPEN-35 and must not be merged with it
Register §6, OPEN-18 (Q3, √S vertical-form distortion) is *"the largest open modeling problem in the
project"* and involves **the same mismatch between an archetype's expected height and the geometry
actually built**. OPEN-35 records this as *"a lead, not a finding."* **N06 may report the overlap as
an observation. N06 may not merge the two items, and may not claim one causes the other.**

---

## 6. Task list — measurement only

Seven tasks, seven independent dispatches, seven reports. **Remediation forbidden in all seven.**

---

### N06 — How many fleet buildings reach both fallbacks, and does OPEN-12 still hold? (OPEN-35, OPEN-12)

**What to do.** A missing-input census over all twelve cells. Count, per cell and fleet-wide, the
buildings with (a) no `levels`, (b) no `height_m`, (c) **neither** — and for the (c) population,
report what archetype the fleet actually assigned and what storey count it actually persisted.

**Why.** OPEN-35 §"What is NOT known" item 1, verbatim: *"**How many fleet buildings have neither
`levels` nor `height_m`** — i.e. how many actually reach both fallbacks. Until that count exists this
is a confirmed mechanism of unknown size. **It is one query over the Stage-2 outputs, no
simulation.**"* The mechanism is verified (§5.1); only its size is missing, and a confirmed defect of
unknown size cannot be prioritised against anything. **OPEN-12 rides along** because it is the same
query on one of the same two columns (§5.2), and its two recorded percentages are 📄, never
re-derived.

**How.**
- **Read the raw Stage-1 inputs, not the results.** `levels` and `height_m` as *ingested* are what
  determine which fallback fires; §5.1 establishes the imputed value is never persisted, so the result
  files cannot answer this. Start from `01_buildings.gpkg` per cell. If `levels`/`height_m` are not
  present there under those names, **find where they are and say so** — do not substitute a
  similarly-named column silently (§2 rule 9).
- **Three states, not two, per column:** present-and-usable, present-but-null/NaN, column-absent.
  `_impute_levels` tests `pd.notna(row["levels"])` and `pd.notna(h) and h > 0` — so **a `height_m` of
  `0` is a missing height for these purposes, and a null is too.** Apply exactly that predicate, cite
  it, and report the states separately.
- **Report the fleet total against 8,160.** If your per-cell counts do not sum to the fleet's building
  count, report both numbers and the difference — **do not reconcile silently.** Note that the fleet's
  *simulated* count is 8,154 (six inverted-geometry drops, N04-confirmed); state which denominator
  each of your percentages uses.
- **For the "neither" population**, join to `05_results.gpkg` and report the distribution of
  `archetype_id`, plus the persisted `levels` value. §5.1 predicts the persisted value is `1`; **check
  it rather than assuming it**, and if some rows carry something else, that is the finding.
- **OPEN-12 specifically:** re-derive the `nyc_rural` and `austin_rural` no-`height_m` percentages and
  state them beside the register's recorded 36.4% / 19.2%. If they differ, **report both and do not
  adjudicate** (§2 rule 13) — the difference may be a real change or a different denominator, and
  saying which is the manager's job. Give the same percentage for all twelve cells while you are there;
  it is the same query.
- **State the git state** of every `05_results.gpkg` you read (§4).
- **You may note the OPEN-18 overlap as an observation. You may not merge the items** (§5.8).

**How to test.** (a) The three per-column states sum to that cell's row count — print the sum per
cell. (b) The twelve per-cell "neither" counts sum to your reported fleet figure — print both. (c)
Spot-check **3 buildings by hand** from the "neither" population: open the raw row, show the two null
columns verbatim, show the archetype the fleet assigned, and show the persisted `levels`. Include all
three in the report as an audit trail. (d) State explicitly whether `way/42496352` and `way/42500728`
(OPEN-35's worked examples, `nyc_centre`) appear in your "neither" population — they must, or your
predicate is wrong: **STOP and report.**

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35-12_missing-input-census.md` +
`openubem/outputs/comparisons/open35_missing_input_census.csv` (one row per cell, plus a fleet row) +
`openubem/outputs/comparisons/open35_neither_population.csv` (one row per affected building).

---

### N07 — Which step writes the wrong `archetype_id` into `05_results.gpkg`? (OPEN-06)

**What to do.** Trace, in code, the write path that puts `archetype_id` into `05_results.gpkg`, and
identify the specific step at which a true `LargeHotel`/`SmallHotel` becomes an Office archetype.
**Name it with a `path:line`.** Measurement only — do not fix it.

**Why.** This is the exact question N04 left open, quoted verbatim at §5.3, and it is the register's
stated first measurement for OPEN-06: *"whether the mislabel originates in `05_results.gpkg` itself or
in a step that writes it. Fixing the symptom in the harvest would leave the source wrong."* N04
answered the first half — **source defect, classifier innocent**. Without the second half, OPEN-06
cannot be planned, because nobody knows what to change.

**How.**
- **Start from the writer, not the reader.** Find every code path that writes an `archetype_id` column
  into a `05_results.*` file. `scripts/validation/v12_cell_pipeline.py` is the known fleet pipeline
  (N05 cites `:659-717` for its SQL-geometry harvest-back). Search the whole repo — there may be more
  than one writer, and **if there are several, that is itself the finding.**
- **Three hypotheses, and your job is to tell them apart.** They have completely different remedies:
  1. **A stale join** — the archetype is carried from an older file/fixture rather than recomputed.
  2. **A lossy mapping** — a Hotel archetype is deliberately mapped onto an Office one somewhere
     (a template lookup, a supported-archetype whitelist, a fallback when no Hotel template exists).
  3. **An overwrite** — the correct archetype is written and then replaced downstream.
  Report which, **with the line that does it.** If the evidence supports more than one, say so.
- **Follow the actual population.** Take 3 of the 41 from `openubem/outputs/comparisons/
  open06_mislabel_population.csv` (N04's artifact, 41 rows) and trace those specific buildings through
  the write path. A general reading of the code is not sufficient — **the trace must end at the value
  those three rows actually carry.**
- **Check whether a Hotel template exists at all.** `openubem/data/openstudio_archetypes.json` is the
  live vocabulary (N03 read it for OPEN-27). If `LargeHotel`/`SmallHotel` are absent from the
  *template* layer while present in the *classifier* layer, hypothesis 2 is proven and you can stop
  there — but **quote the file** rather than asserting it.
- **State the git state** of every file you read (§4), and note that N04 established
  `building_classifier.py` is unchanged since `0df422e`.
- **Do not fix it.** Not the mapping, not the whitelist, not the join. Whatever you find.

**How to test.** (a) Your named write site, opened at HEAD, must be reachable from the fleet pipeline
entry point — show the call chain, one line per hop. (b) The three traced buildings must arrive at the
Office archetype recorded in `05_results.gpkg` for them — if your trace predicts a different value than
the file holds, **your trace is wrong: STOP and report.** (c) State explicitly whether you found one
writer or several.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_archetype-writer-trace.md`.

---

### N08 — Does the archetype column describe what was actually simulated? (OPEN-06, OPEN-07)

**What to do.** For the three OPEN-07 buildings, determine **which prototype was actually built and
simulated**, independently of what `05_results.gpkg` says, and reconcile it with the
`LAUNDRYROOMFLR1` zone name. Read-only, from files already on this machine.

**Why.** §5.4 states the contradiction in full: the three buildings are labelled `SmallOffice`, and
they fail inside a zone called `LAUNDRYROOMFLR1`, which is a **hotel** room type. An office prototype
has no laundry room. **Either the label does not describe what was simulated, or the zone name does not
come from the archetype.** Both are findings; nobody has checked which. If the label is wrong about
what ran, then OPEN-06 is larger than a labelling defect and every cross-mode comparison that keys on
`archetype_id` inherits it.

**How.**
- **The zone name is evidence. Trace it to its source.** Search the repo for `LAUNDRYROOM` (and the
  prototype/room-type vocabulary around it). Which prototype defines that zone name? Which archetype
  does that prototype belong to? **Name both with `path:line`.**
- **Then find what was actually built for those three buildings.** Local candidates, in preference
  order: the per-cell `<cell>_step3_idfs_archive.zip` (present for every cell, §4 — a zip read is a
  file read and is allowed), `04_simulation_manifest.parquet`, and the surviving
  `eplusout.err`/harvest-cache directories at `%LOCALAPPDATA%\Temp\ubem_t20_harvest\`.
  **Beware a generation mismatch:** the Step-3 archives are the T08-generation `auto`-mode fleet, while
  the `LAUNDRYROOMFLR1` failure is from the **T20 `layout_assign`** harvest. **These are different
  runs of different modes** (register OPEN-28: every cross-mode comparison mixes two harvest
  generations). **State which generation each piece of evidence belongs to, every time.** If the
  archive cannot speak to the T20 run, **say so** — that is a clean result.
- **Do not fetch anything from the cluster.** If the decisive artifact is a T20 `.idf` that exists only
  on Speed, **say exactly that and name the file** — do not substitute a different-generation artifact
  and do not run anything to regenerate it. N04 already established no T20 `.idf` survives locally and
  the T19 cache directory for `way/401910463` is empty (0 files); **confirm that independently rather
  than repeating it.**
- **Three outcomes are possible** and you must state which: the built prototype **matches** the
  recorded archetype (so the zone name has a separate explanation); it **does not match** (so the
  column is wrong about what ran); or the evidence is **silent** locally (so the question needs a
  cluster fetch, which is not authorised here). **"Silent" is an acceptable and useful answer.**
- Ground truth for run outcome is `eplusout.err` and the `** Severe **` line — **never `.end`, never
  `has_fatal`** (§2 rule 11).

**How to test.** (a) The prototype that owns `LAUNDRYROOMFLR1` is named with a `path:line` a reader can
open, and its archetype is stated. (b) For each of the three buildings, state the evidence you had, its
harvest generation, and your verdict — three rows, no summarising. (c) If your answer is "silent",
name the exact file that would settle it and where it lives.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06-07_simulated-archetype.md`.

---

### N09 — Read the two forwarded UTCI defects and the backfill reproducibility gap (OPEN-13, OPEN-14)

**What to do.** Read the closed UTCI arc and report (a) what `E-UTCI-12` and `E-UTCI-13` actually are,
whether each is still true at HEAD, and what each would need before it could be planned; and (b) for
OPEN-14, exactly what a clean checkout lacks and exactly what would restore it.

**Why.** OPEN-13 is the only register item whose own text admits it has never been read: *"**Content
not re-read this session** — read `docs_DONE/OUTDOOR/UTCI/` before planning"* (§5.5). An item that
nobody has read cannot be prioritised, and it has been sitting in the register in that state. OPEN-14
is more urgent than its 📄 mark suggests — the register calls it *"a **reproducibility defect in
shipped inputs**… it silently invalidates a rebuild rather than degrading a known cell."*

**How.**
- **§5.5 gives you the complete search space: six files.** Read all six. Start with
  `docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md` — OPEN-14
  is about that backfill, so both items are likely settled there.
- **For each of E-UTCI-12 and E-UTCI-13, report five things:** the defect in one sentence; its defining
  `path:line`; its last recorded status **and the date of that record**; whether the mechanism is still
  present in current code (**cite HEAD, not the arc doc** — §2 rule 12; the arc doc is the hypothesis);
  and one sentence on what would have to be measured before it could be planned.
- **For OPEN-14, be concrete and mechanical.** Which file(s) does Stage 6 need, which are gitignored or
  absent from the repo, which script produced them, and does that script still run from a clean
  checkout? **Check `.gitignore` and `git ls-files` for the actual artifacts** — do not infer from
  prose. If the backfilled heights *are* committed somewhere, then OPEN-14 is already closed and that
  is the finding: **quote the committed file.**
- Round 1's lesson applies directly: **items have closed themselves without telling the register**
  (OPEN-25 was fixed the day after it was named and carried open for eight weeks). **Look for that
  first.**
- **Report unknowns as unknowns.** If the arc's own documents contradict each other, report both with
  dates (§2 rule 13).

**How to test.** (a) Both E-UTCI IDs carry a HEAD citation, not only an arc-doc citation — an arc-doc
citation alone is not evidence for this task. (b) OPEN-14's verdict names the specific artifact and its
git-tracked status (`git ls-files` output quoted). (c) State explicitly which of the six files you
opened and which you did not, and why.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13-14_utci-forwards.md`.

---

### N10 — Assemble the imputation-tier decision the user has never been given (OPEN-15, 16, 17)

**What to do.** Produce **one decision brief** covering the three imputation items: what exists, what
state each is in, what evidence was gathered, and precisely what the user would be deciding. **Assemble
it. Do not recommend, and do not decide.**

**Why.** Register §5, verbatim: *"These are one decision, not three: **does this project want a
non-deterministic input tier at all?**"* Three register items have sat 📄 for weeks because the
material to decide is scattered across a closed arc, a leaderboard, and project memory. The
constraint is hard-won and binding (§5.6): **NMBE is blind to variance collapse and must never be
used alone as an imputation-accuracy metric** — variance ratios 0.06–0.31 measured. A brief that omits
that constraint is worse than no brief.

**How.**
- **Three items, one structure each:** what was built (with `path:line` at HEAD), its current switch
  state (**verify in code — is it opt-in, off-by-default, or unreachable?**), what evidence exists for
  and against it, and what it would cost to turn on.
- **OPEN-15 (Phase E imputation)** — *documented-deferred, never executed.* Find the document that
  deferred it and quote the reason. State whether the code path exists.
- **OPEN-16 (`ml` tier)** — *built, verified EUI-neutral and not harmful, permanently off.* Locate the
  verification and quote its numbers. **"Permanently off" is a strong claim: check whether the switch
  is actually reachable**, and say so either way.
- **OPEN-17 (draw tier, 6 imputers)** — locate the **CP-DRAW leaderboard** and reproduce its table in
  the brief, in full, with its own metric names. The register's summary is *"no method dominates on
  every axis"*; **the axes and the numbers are what the user needs**, not the summary.
- **State the decision as a question with consequences**, not as a recommendation: what changes if the
  answer is yes, what changes if no, and what becomes undecidable either way. The
  **zero-fitted-parameters guarantee** on the adopted baseline is a live constraint here — state
  explicitly whether promoting any tier would touch it. **If you cannot tell, say so.**
- **This task is document assembly and code-state verification. Run nothing.** No imputation pass, no
  fleet pass, no benchmark. If a number you need does not exist in a document, **report that it does
  not exist** rather than generating it.
- **No recommendation. Not one sentence of one.** The ruling is the user's, and a brief that leans is
  a brief that decided.

**How to test.** (a) Each of the three items carries a HEAD `path:line` for its code and a document
citation for its evidence. (b) The CP-DRAW leaderboard is reproduced with its real column names and
row count stated. (c) The brief contains **zero** recommending sentences — reread it and confirm this
explicitly in your report. (d) The NMBE/variance-collapse constraint appears in the brief with its
measured 0.06–0.31 range.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-15-16-17_imputation-decision.md`.

---

### N11 — Can a `ZoneGroup` list multiplier actually express exact storey matching? (OPEN-10)

**What to do.** Settle, from the EnergyPlus input schema and the current code, whether the believed
capability is real: would editing the `ZoneGroup`'s own list multiplier restore exact storey matching
at **every** `n_real`? Answer **yes / no / cannot be determined statically**, with the schema lines
that decide it.

**Why.** This is **the register's only ❓** — the only item with no evidence mark at all, in a register
whose whole design is evidence marks. Register §4, verbatim (§5.7): *"**Never tested** — this is a
believed capability, not a measured one."* The claim is about what the input schema permits, and
**the schema is a file on disk**, so the ❓ is removable with no compute at all. That is an unusually
cheap way to remove the register's weakest entry.

**How.**
- **Read the IDD, not the documentation.** `openubem/config.py:16,32` resolves `ENERGYPLUS_IDD_PATH` to
  the real 23.1 `Energy+.idd` (verified by N03). Find the `ZoneGroup` object in it and quote its
  fields verbatim — the multiplier field, its type, its minimum, and whether it is required. **If the
  IDD is not present on this machine, STOP and say so** rather than substituting a remembered schema
  or a web source.
- **Then read what the project built instead.** The delivered mechanism writes `Zone.Multiplier`.
  Find it (`openubem/idf/`), cite it, and state what it can and cannot express. Register §4 records
  the current limitation as *"only `{10, 18, 26, …}` / even `n_real ≥ 4`"* — **re-derive that from the
  code rather than quoting it**, and if your derivation disagrees, report both (§2 rule 13).
- **The comparison is the deliverable.** For a set of `n_real` values — at minimum 1, 2, 3, 4, 5, 7,
  10, 18, 26, 51 — state what each mechanism can express exactly. A table. **Derived from the schema
  and the code, not simulated.**
- **Also state the population.** Register §4 says the item touches *"90 buildings + future"*. Find
  where that 90 comes from and whether it is re-derivable; if it is, re-derive it; if not, **say the
  number is not currently re-derivable** — that is a real finding about a register entry.
- **Note the reopening flag honestly.** R04 is closed at option (a); this item is a *deliberate
  reopening*, not a continuation. **Your report says what is true; it does not argue for reopening.**
- **Build nothing.** No IDF, no test model, no simulation, no `eppy` round-trip that writes a file.
  Reading the IDD and the source is the whole task. If the question genuinely cannot be settled
  statically, **that is the answer** — say so and name the smallest experiment that would settle it,
  for the manager to schedule when CPU is free.

**How to test.** (a) The `ZoneGroup` IDD block is quoted verbatim in the report with its file path and
line numbers. (b) The `n_real` expressibility table is complete for the ten listed values, with the two
mechanisms side by side. (c) Your verdict is one of the three allowed words, stated in one sentence, at
the top of the report.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-10_zonegroup-capability.md`.

---

### N12 — Is the Title 24 hypothesis even representable in this pipeline? (OPEN-19)

**What to do.** Determine, from code and data at HEAD, **what standard the archetypes actually
encode**, whether any Title 24 / California-specific alternative exists anywhere in the project, and
what a "calibration phase" would have to change. Measurement only — **research the pipeline, not the
building-science literature.**

**Why.** Register §6, OPEN-19: LA runs **~+40% hot**, established as **not** the zoning defect (a
zoning fix moved it −0.6%), so it is a real climate/HVAC-response problem. The named hypothesis —
Title 24 vs ASHRAE 90.1 envelope U-values, infiltration, HVAC COP, economizers for CZ 3B — has **never
been researched**. And the register flags a tension that must be settled *first*: the adopted baseline
carries a **zero-fitted-parameters guarantee**, so *"a 'calibration phase' must be defined carefully or
it breaks that guarantee. That definitional question is the first thing an execution plan would have to
settle."*

**How.**
- **Establish what is actually in the archetypes today.** For the LA cells' dominant archetypes, report
  the concrete values the pipeline uses: envelope U-values / construction sets, infiltration rate,
  HVAC COP, whether an economizer is modelled at all. **Cite the file and line for each** —
  `openubem/data/`, `openubem/idf/`, `openubem/semantic/construction_sets.py`, the archetype JSON, the
  IDF templates. **A claim with no line number is not a result here.**
- **State the standard each value comes from**, if the project records it. **If the provenance of a
  value is not recorded anywhere, say so** — an unattributed U-value is a finding in its own right and
  is the same shape as OPEN-30 (a resolved value the pipeline never persists).
- **Search for any Title 24 / California / CZ 3B awareness already present** — a climate-zone field, a
  code-year switch, a per-state branch. **If there is none, state plainly that the hypothesis is not
  currently representable without new data**, and name what data would be needed (a source, not a
  literature review).
- **The definitional question is part of this task.** State, in plain language and without
  recommending, what "calibration" would mean here and which of the values above it would have to
  move — so the user can see exactly what the zero-fitted-parameters guarantee would be trading away.
  **Do not propose a calibration. Do not fit anything.**
- **Do not research building-science literature and do not browse the web.** This task is about what
  the repository contains. If a question can only be answered from an external standard document,
  **say so and name the document.**
- **Re-derive the −0.6% and +40% figures' sources if they are cheaply available**; if not, mark them as
  carried, not verified, and say which document carries them. Do not present a carried number as
  measured.

**How to test.** (a) At least four concrete parameter values reported with `path:line` (envelope,
infiltration, COP, economizer presence). (b) An explicit yes/no on whether any climate-zone or
code-year switch exists in the codebase, with the search you ran. (c) The definitional paragraph
contains no recommendation — confirm this explicitly.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-19_la-standard-basis.md`.

---

## 7. Stop-and-report points

Three checkpoints. **Not one per task** — these seven are independent, so they converge rather than
chain. The manager audits **by independent re-derivation from the raw files**, never by reading the
executor's report back.

### CP-N3 — after N06 + N07 + N08 · *the archetype-and-inputs checkpoint*
These three are one story told from three ends: what goes in (N06 — how many buildings have no usable
input at all), what gets recorded (N07 — which step writes the wrong label), and what actually ran
(N08 — whether the label describes the simulation). **The manager spot-checks at least one number from
each against the raw artifact before amending the register.** If N08 finds the label does *not*
describe what ran, that is a finding for the user immediately, not at the end of the queue — **it
would widen OPEN-06 from a labelling defect into a provenance defect.**

### CP-N4 — after N09 + N10 · *the inherited-backlog checkpoint*
Both concern work this arc inherited rather than found: two forwarded UTCI defects nobody has read, and
three imputation items nobody has been given the material to decide. Expected outcomes are register
amendments and one decision brief. **If N09 finds either UTCI item already closed, it closes** — Round
1 established that pattern is real and eight weeks old (OPEN-25).

### CP-N5 — after N11 + N12 · *the never-researched checkpoint*
The register's only ❓ and its longest-standing unresearched hypothesis. Both are believed claims that
have never met a file. **Either may come back "cannot be determined statically" — that is a result, not
a failure**, and the manager records it as the item's measured state with the smallest experiment named
for when CPU is free.

**After all three:** the manager amends the register (struck-and-dated, never deleted), updates the
director prompt, updates this plan's §8, and updates the board — **the four surfaces, every task,
unasked.** **No Phase 2 is written by this plan.**

---

## 8. Progress log

*Append one entry per completed task. Append-only — never rewrite an entry, including one you believe
is wrong; correct it in a new entry that cites the old.*

```
#### NXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + register citation>
- Test status: <the "how to test" result, pass/fail, with numbers>
- Headline numbers, each with the file it was re-derived from: <…>
- Notes: <auditor-relevant>
```

#### N07 — Which step writes the wrong `archetype_id` into `05_results.gpkg`? (OPEN-06) — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_archetype-writer-trace.md`. No CSV
  artifact produced — every number is either quoted from N04's existing
  `openubem/outputs/comparisons/open06_mislabel_population.csv` or re-derived inline via
  `BuildingClassifier().classify()` calls documented verbatim (path:line, subsetting, casting) in the
  report §2.1, so the re-derivation is reproducible from the report text alone without a persisted
  script.
- Deviations: none from the plan. The task asked for a verdict among three named hypotheses with a
  `path:line`; the actual result is that **all three were tested and disproved** for the write path as
  it exists in the repository (current and at the T11-era commit), and the plan's own stop condition
  (§6 N07 how-to-test (b): "if your trace predicts a different value than the file holds, your trace is
  wrong: STOP and report") fired. This is reported as the finding, not resolved into a guess, per plan
  §2 rules 9/13.
- Test status: (a) PASS — write site reachable from `run_cell()` by a 10-hop `path:line` chain. (b)
  **FAIL, reported per the plan's explicit instruction** — traced 5 of the 41 mislabelled buildings (3
  `nyc_rural`, 1 `la_urban`, 1 `nyc_centre`) end to end through Step 2→3→5 using the exact production
  code (both at HEAD and at the commit current during the T11 run window) against the frozen,
  git-unchanged raw inputs; every trace predicts `SmallHotel`/`LargeHotel`, the committed file holds
  `SmallOffice`/`LargeOffice` for all 5. Full-cell-batch reclassification (198 rows, `nyc_rural`) gives
  the same result, ruling out a batch-size/index-alignment bug. (c) **One writer** —
  `scripts/validation/v12_cell_pipeline.py`'s Step2→Step3→Step5 chain is the only code path that writes
  `archetype_id` into these files; `scripts/validation/phaseE_recover_10.py` is a second script capable
  of patching the same files but its scope (10 hard-coded osm_ids, the OPEN-11 population) does not
  overlap the 41 Hotel mislabels.
- Headline numbers: 5/5 traced buildings show classifier-recomputed archetype ≠ committed
  `05_results.gpkg` archetype (`docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`
  git state `e063865` 2026-06-30, unchanged since, feeding `openubem/semantic/building_classifier.py`
  git state `0df422e` 2026-07-03, unchanged since → `SmallHotel`/`LargeHotel`; committed
  `docs_VALIDATION/.../phaseE/<cell>/05_results.gpkg` git state `0df422e` 2026-07-03 → `SmallOffice`/
  `LargeOffice`, `simulation_status="success"` with real EUI for all 5, not a dropped/failed row).
- Notes for the auditor: none of stale-join / lossy-mapping / overwrite could be pinned to a
  `path:line` — each was tested directly and contradicted by evidence (report §4). The unresolved
  residual (report §5) is that `build()`'s unconditional archetype-pass-through (verified unchanged at
  both the T11-era commit `03e2121` and HEAD `69373f9`) makes the committed Office label only
  explainable if `classify()` itself returned Office at write time for these rows — which the same
  deterministic function, called today against the same frozen input, does not do. The T11 run window
  is independently documented (`docs_DONE/BUGS/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md`
  §8, T11 entries) as having involved at least one live, mid-run, uncommitted hotfix to this same
  pipeline script, which establishes that git history does not necessarily capture everything that
  executed during that window — reported as an open provenance gap, not asserted as the cause. Also
  corroborated independently: R06 (`docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/
  PLAN_storey-matching_REMAINder.md:1174-1194`, dated 2026-08-04) found, via a raw retained cluster
  `in.idf` for the same `way/965718400` (a different harvest generation, T20 `layout_assign` — noted as
  an observation only, not merged with the Phase-E-specific finding per plan §5.8-style discipline),
  that the actual EnergyPlus input read `Building, HotelSmall` — agreeing that Hotel is correct and
  Office is what the file holds, without itself identifying the writer either.

#### N08 — Does the archetype column describe what was actually simulated? — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06-07_simulated-archetype.md`.
- Deviations: none.
- Test status: (a) PASS — prototype named at `docs/docs_VALIDATION/validations/Level 2 DOE round-trip/
  00.BaselineBuildings_NUs/ASHRAE901_HotelSmall_STD2022_Buffalo.idf:3318-3319`, archetype `SmallHotel`
  (`openubem/geometry/layout_assigner.py:31`). (b) PASS — three rows, no summarising, in report §3. (c)
  N/A — answer is not silent; the decisive artifact (`eplusout.sql` `Errors` table) survived locally for
  all three buildings.
- Headline numbers, each with the file it was re-derived from: For all three OPEN-07 buildings
  (`la_urban/way_401910463`, `nyc_rural/way_965718402`, `nyc_rural/way_965718403`), the T20
  `layout_assign` harvest's own `eplusout.sql` `Errors` table (`C:\Users\o_iseri\AppData\Local\Temp\
  ubem_t20_harvest\<cell>_layout_assign\way_<id>\eplusout.sql`) names the exact 14-zone first-floor set of
  `ASHRAE901_HotelSmall_STD2022_Buffalo.idf` (`SmallHotel` baseline), including `LAUNDRYROOMFLR1` — an
  exact, set-for-set match, case-insensitive — while `05_results.gpkg` (commit `0df422e`) records
  `archetype_id = SmallOffice` for all three, whose baseline (`ASHRAE901_OfficeSmall_STD2022_Buffalo.idf`)
  has zero zone-name overlap (`Core_ZN`, `Perimeter_ZN_1..4`, `Attic`). `LargeHotel`'s baseline was also
  checked and ruled out (`Laundry_Flr_1`, a different naming convention, not a match).
- Notes: **Outcome 2 — does not match.** The built prototype does not match the recorded archetype; the
  zone name *does* come from the archetype (a deterministic 1:1 `ARCHETYPE_IDF_MAP` lookup, call chain
  traced `scripts/cluster/t20_layout_assign_full_sweep.py` → `openubem/idf/builder.py:201,78` →
  `openubem/geometry/layout_assigner.py:121,31`), so `05_results.gpkg`'s `SmallOffice` label is wrong
  about what actually ran at T20. This widens OPEN-06 from a labelling defect into a provenance defect for
  at least these three buildings — flagged per plan §7 CP-N3 as immediate, not end-of-queue. The
  `<cell>_step3_idfs_archive.zip` and `04_simulation_manifest.parquet` evidence for the same three
  buildings belongs to the T08-generation `auto` mode (per-floor shoebox zoning, no `Laundry` zone,
  `status=success`) and was checked but is generation-mismatched — reported as ruled-out, not used for the
  verdict.

#### N09 — Read the two forwarded UTCI defects and the backfill reproducibility gap — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13-14_utci-forwards.md`
- Deviations: none. All six files in §5.5's search space opened (table in the artifact's §1).
- Test status: all three "how to test" criteria PASS — (a) both E-UTCI IDs carry a HEAD citation
  (live `grep`/`pytest -q` re-run for E-UTCI-12; live double-normalize re-execution against the
  committed fixture for E-UTCI-13, not merely an arc-doc quote); (b) OPEN-14's verdict names the
  specific artifact with `git ls-files` output quoted (no Overture slice tracked for any of the 4
  affected cells; only unrelated `testcell`/`nyc_centre` fixtures are tracked); (c) all six files
  in the search space stated as opened, none skipped.
- Headline numbers, each with the file it was re-derived from:
  - E-UTCI-12 still failing at HEAD `bca92d0`: `pytest -q` (full suite) → `Interrupted: 1 error
    during collection`, `AttributeError: module 'openubem.semantic.imputation' has no attribute
    '_draw_tier'` at `tests/test_draw_methods.py:645`. `grep -n "_draw_tier"
    openubem/semantic/imputation.py` → no output.
  - E-UTCI-13 still reproducible at HEAD: live double-pass of `fetch_overture()` against
    `openubem/data/fixtures/fusion/overture_testcell_slice.parquet` → pass 1 `levels`/`use_class`
    2/2 non-null; pass 2 (simulating `fusion.OvertureSource.join` re-reading `pull_overture`'s
    cache) → `levels`/`use_class` 0/2 non-null, `height` still 2/2 non-null.
  - OPEN-14 still open: `git ls-files | grep -i "nyc_suburban\|nyc_rural\|austin_centre\|austin_rural"
    | grep -i "overture\|height"` → empty. `git ls-files -- "openubem/data/fixtures/fusion/*"` → 6
    files, none for the 4 affected cells. `openubem/config.py:100,141` →
    `IMPUTE_ENABLED_TIERS = ("fusion", "spatial", "statistical")`,
    `FUSION_SOURCES_BY_TARGET: dict = {}` (both re-read live at HEAD).
  - No round-1 "fixed the day after it was named" pattern found for any of the three items: every
    file whose modification would fix any of them (`height_cache.py`, `overture_fetcher.py`,
    `tests/test_draw_methods.py`, `openubem/semantic/imputation.py`, `draw_methods.py`) has had zero
    commits since the commit that introduced or last touched the relevant defect, per
    `git log --oneline` per file (quoted in full in the artifact).
- Notes: E-UTCI-12 and register item OPEN-17 (the draw-tier promotion decision) are the same
  underlying gap seen from two angles — `_draw_tier` was never wired into `imputation.py`. Recorded
  as an observation only; not merged, per the same discipline as OPEN-18/OPEN-35 (§5.8 of this
  plan). No document contradiction found across the six files on any of the three items' status —
  all agree OPEN/forwarded and unfixed.

#### N06 — Missing-input census: how many fleet buildings reach both fallbacks, and does OPEN-12 still hold? — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35-12_missing-input-census.md`,
  `openubem/outputs/comparisons/open35_missing_input_census.csv` (13 rows: 12 cells + fleet total),
  `openubem/outputs/comparisons/open35_neither_population.csv` (2,611 rows).
- Deviations: none. Predicate applied exactly as pinned in §5.1/§2 rule 9 (`_impute_levels`,
  `building_classifier.py:131-134`); all percentages denominated against 8,160 per §4, stated explicitly.
- Test status: (a) PASS — per-cell state sums verified programmatically for all 12 cells, no assertion
  failure. (b) PASS — 12 per-cell "neither" counts (247+244+74+43+31+0+15+29+107+198+1589+34) sum to
  2,611, matching the reported fleet figure exactly. (c) PASS — 3 buildings hand-spot-checked
  (`way/42496352` nyc_centre, `way/285843826` la_suburban, `way/220649876` nyc_urban), raw columns and
  persisted archetype/levels shown verbatim in the report. (d) PASS, no STOP — both
  `way/42496352` and `way/42500728` confirmed present in the nyc_centre "neither" population.
- Headline numbers, each with the file it was re-derived from: fleet "neither" population **2,611/8,160
  (32.00%)** (`01_buildings.gpkg` ×12, commit `e063865`); persisted storey for that population
  **uniformly `1.0` levels / `3.5` m** in `05_results.gpkg` ×12 (commit `0df422e`) — confirms §5.1's
  prediction by direct check, not assumption; fleet-wide no-`height_m` **2,806/8,160 (34.39%)**
  (`01_buildings.gpkg` ×12); OPEN-12 re-derived — `nyc_rural` **100.00% (198/198)** vs register's 36.4%,
  `austin_rural` **100.00% (245/245)** vs register's 19.2% — both re-derived numbers reported beside the
  register's, **not adjudicated** (plan rule 13).
- Notes: **Large, unadjudicated disagreement on OPEN-12** — every row in both `nyc_rural` and
  `austin_rural`'s current `01_buildings.gpkg` (commit `e063865`) has a null `height_m`; there is no
  partial-coverage subset that would produce 36.4%/19.2%. Two explanations are possible (post-backfill
  state never merged back into this checkout's `01_buildings.gpkg`, or the register's number is from a
  different snapshot) — **this task does not choose between them**; it is directly relevant to N09
  (OPEN-13/OPEN-14, the UTCI backfill's reproducibility) and flagged for CP-N4. A third cell,
  `nyc_suburban`, is also at 100% no-`height_m`/100% "neither" — not previously named in OPEN-12's
  two-cell framing, reported as an observation. Clarified beyond §5.1: `05_results.gpkg`'s persisted
  `levels`/`height_m` are the **geometry-stage (`derive_num_floors`) derived values**, not the untouched
  raw Stage-1 columns (those stay byte-identical per the `building_classifier.py:636-639` invariant) —
  for the "neither" population both stages' flat-`1` fallbacks coincide, so this file cannot distinguish
  which of the two fallbacks (§5.1) actually fired for a given row. `height_missing_zero` (present-but-
  0-or-negative) is **0 across the entire fleet** — every missing height in this fleet is a genuine null,
  never a zero. OPEN-18 overlap noted as an observation only (§5.8) — not merged, no causal claim.

#### N12 — Is the Title 24 hypothesis even representable in this pipeline? — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-19_la-standard-basis.md`.
- Deviations: none.
- Test status: (a) PASS — four-plus parameter values reported with `path:line` (envelope, infiltration,
  COP, economizer). (b) PASS — explicit **no** climate-zone/code-year switch anywhere in `openubem/` or
  `scripts/`, search commands quoted in full in the report §2, zero hits. (c) PASS on re-read — §4's
  definitional paragraph contains no recommendation and decides nothing.
- Headline numbers, each with the file it was re-derived from: envelope for LA's dominant archetype
  MidriseApartment at climate zone 3B — wall U=0.437 W/m²K, roof U=0.221, window U=2.385/SHGC=0.25, floor
  U=0.42 (`openubem/data/construction/ashrae_90_1_2019.json`, loaded `construction_sets.py:71,90-97`);
  infiltration **0.000285 m³/s·m²**, uniform across all climate zones and all 20 real archetypes except
  DataCenter (`PROVENANCE.md:46-54`); MidriseApartment cooling COP **4.323**, heating efficiency **0.84**
  (Gas), source prototype `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` — extracted from a **Buffalo,
  NY (ASHRAE zone 6A)** prototype and applied unchanged regardless of the building's actual climate zone
  (`hvac_cop_by_archetype.json`; consumed `hvac.py:230-231`); economizer present via hardcoded
  `Economizer_Type = "DifferentialDryBulb"` at `hvac.py:248,288,332,386,532,567` (NoEconomizer only for
  the warehouse radiant proxy, `:613`); LA county (FIPS 06037) confirmed climate zone **3B** by direct
  query of `openubem/data/climate_zones/ashrae_climate_zones.gpkg`. The −0.6%/+38.8% figures are
  **carried, not re-derived**: both traced to `docs/docs_VALIDATION/step1/overAll/
  V19_phaseC_rescore.md:34,45` (a report-only synthesis, no fresh aggregation attempted — re-deriving
  from raw per-building results would mean reproducing V19's full 12-cell join, not a cheap re-derivation).
- Notes: a climate-zone-aware HVAC field (`economizer_db_limit_c`, per-CZ ASHRAE 90.1 fixed-dry-bulb
  economizer high limits, e.g. 3B=23.9°C=75°F, matches literature exactly) **exists in
  `hvac_systems_by_archetype.json` on every archetype but is never read by any `.py` file** — confirmed
  by grep, zero code references. The code always emits `DifferentialDryBulb` control, which does not
  consult a fixed threshold at all, so this data is inert. The literature-cited Title 24 lever most
  directly targeted at this field (71°F vs 75°F fixed-DB shutoff) would currently change nothing even if
  the JSON value were edited, because the consuming code path doesn't read that key. `custom_table`
  injection points exist at every data layer (construction/HVAC/schedules) but are confirmed unused by
  any production script (`grep` over `scripts/` for `construction_table\s*=` → 0 matches) — the fleet
  pipeline always resolves to the single bundled ASHRAE 90.1-2019 / Buffalo-COP / PNNL-infiltration set,
  for every city. No Title 24/CEC/CALGreen string exists anywhere in `openubem/` or `scripts/`.

#### N11 — Can a `ZoneGroup` list multiplier actually express exact storey matching? — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-10_zonegroup-capability.md`.
- Deviations: none. Built nothing — no IDF, no test model, no simulation, no `eppy` write; read only the
  IDD (`C:\EnergyPlusV23-1-0\Energy+.idd`, confirmed present) and `openubem/geometry/layout_assigner.py`
  at HEAD (`69373f9`, unchanged since 2026-07-27).
- Test status: all three "how to test" criteria PASS — (a) `ZoneGroup` IDD block quoted verbatim,
  `Energy+.idd:10002-10018`, with `Zone`'s comparison `Multiplier` field at `:9576-9579`. (b) `n_real`
  expressibility table complete for all ten listed values (1,2,3,4,5,7,10,18,26,51), three columns
  (shipped-MidRise, shipped-HighRise, proposed-direct-overwrite) since the two shipped archetypes hit
  different residue sets and collapsing them would have hidden that. (c) Verdict is one of the three
  allowed words ("Yes"), one sentence, at the report's top.
- Headline numbers, each with the file it was re-derived from: `ZoneGroup`'s `Zone List Multiplier`
  field is `type integer, default 1, minimum 1`, **no maximum, no divisibility note**
  (`Energy+.idd:10015-10018`) — identical constraint shape to `Zone.Multiplier`
  (`Energy+.idd:9576-9579`). The shipped mechanism (`layout_assigner.py:539-653`,
  `match_storeys()`) writes only `Zone.Multiplier`, compounding it with a pre-existing `ZoneGroup`
  value it never edits (confirmed: `Zone_List_Multiplier` appears in this file only as a read, at `:459`,
  never as an assignment target) — this compounding is what restricts the reachable set to
  `n_real ∈ {4,6,8,…}` (`ApartmentMidRise`, list mult **2**, confirmed at
  `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf:2078-2081`) or `{10,18,26,…}` (`ApartmentHighRise`,
  list mult **8**, confirmed at `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf:2538-2541`) — matching
  the register's stated ranges exactly, re-derived from the code's own residual formula, not quoted.
  "90 buildings" (register §4 OPEN-10 reach figure) traced to
  `docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_REMAINder.md:1302-1315`
  (66 `MidriseApartment` + 24 `HighriseApartment`, `applied → fallback_not_expressible` crosstab cell,
  7,442 buildings evaluated) — **not re-derived**: reproducing it requires a fleet-wide
  `compute_band_map()`/`match_storeys()` pass over 7,442 real `(archetype_id, num_floors)` pairs, which
  this plan's §2/rule-3 no-compute constraint places out of scope for a measurement task; smallest
  settling experiment named in the report §4 (a local, EnergyPlus-free Python pass, excluded here only
  by this plan's scope rule, not by cost).
- Notes: verdict is **yes, with a bounded scope** — direct `ZoneGroup`-field overwrite would express
  every `n_real ≥ 3` for the 2 apartment archetypes that already carry a `ZoneGroup` (exactly the "90
  buildings" population), but does **not** help the 7 other `fallback_not_expressible` archetypes
  (`Hospital`, `LargeOffice`, `TallBuilding`, `SuperTallBuilding`, `College`, `LargeHotel`, `Laboratory`)
  — those fail on middle-band ambiguity (zero or multiple distinct middle bands), a structural issue
  unrelated to which multiplier field is edited, and building a `ZoneGroup` for them from scratch would
  be a materially larger change than "editing the field." R04 closed-at-(a) and OPEN-10's
  deliberate-reopening framing stated per §5.7/§6, not argued for or against.

#### N10 — Assemble the imputation-tier decision the user has never been given — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-15-16-17_imputation-decision.md`.
- Deviations: none. No imputation pass, no fleet pass, no benchmark run; document assembly and static
  code reading only, per HEAD `bca92d0`.
- Test status: all four "how to test" criteria PASS — (a) all three items carry HEAD `path:line` code
  citations plus document citations (§1-§3 of the artifact). (b) CP-DRAW leaderboard reproduced with
  its real JSON column names (`mae`,`rmse`,`ks_stat`,`wasserstein`,`variance_ratio`,`iqr_ratio`,
  `energy_distance`,`nmbe_proxy_pct`,`do_no_harm_mae_pass`,`eligible_primary`,`priority_rank`, plus
  `pfc`/`log_loss`/`tv` for the categorical leg) and row count stated (20 pooled data rows + 1 joint-
  bonus summary row = 21; `per_cell` block for 12 cities referenced, not tabulated). (c) PASS on
  re-read — zero recommending sentences; §5/§6 explicitly decline to choose between competing
  readings. (d) PASS — the 0.06-0.31 variance-ratio range re-derived as the three exact pooled baseline
  values (`year_built` 0.064, `levels` 0.314, `height_m` 0.088) from `draw_leaderboard_results.json`,
  not carried from the register as a pre-summarized range.
- Headline numbers, each with the file it was re-derived from: `ml` tier fully wired but reachable only
  via the standalone `impute_missing()` validation entry point, never via production `enrich_semantics`
  (`openubem/semantic/imputation.py:543,685,881-886,900-902`; `openubem/semantic/__init__.py:17,273,305`;
  `openubem/semantic/construction_sets.py:126`) — `IMPUTE_ENABLED_TIERS` default unchanged
  (`openubem/config.py:100`). `draw` tier's router wiring (`_draw_tier`, `"draw"` in
  `_CANONICAL_TIER_ORDER`/`_TIER_HANDLER_NAMES`, `config.IMPUTE_DRAW_METHOD_BY_TARGET`) is **absent from
  `openubem/semantic/imputation.py` (966 lines, read in full) and `openubem/config.py` (163 lines, read
  in full) at HEAD, and absent from `git log --all -p -S` history on both search terms, on the repo's
  only branch** — directly contradicting the archived arc's own "T07 completed 2026-07-16, 53/53 passed"
  closure record (`docs/docs_DONE/INPUTS/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md:849-857,1206-1219`).
  OPEN-16's underlying −5.51% NMBE figure is reported by two disagreeing committed documents
  (`docs/docs_DONE/INPUTS/imputation/results/phase_C/RESULTS_phaseC.md:41,98` = FAILS, undated status
  header vs. `docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseC_ml_imputer.md:39-43,680-708`,
  dated 2026-07-14 = reattributed as a pooled-granularity artifact, EUI-neutral at production
  granularity) — both reported, neither adjudicated.
- Notes: **this finding independently corroborates N09's** (same plan doc, above) — N09 live-ran
  `pytest -q` and got `AttributeError: module 'openubem.semantic.imputation' has no attribute
  '_draw_tier'`, confirming by execution what this task found by static reading alone (this task's
  own rules forbid running anything). Flagging for CP-N4/manager: the `draw` tier's "opt-in/OFF"
  characterization in both the register (`INVESTIGATION_open-items-register.md:945`) and project memory
  should likely read "unreachable," not "opt-in/off," until the manager determines whether the T07
  wiring was ever actually merged. Also established: **no tier in this arc — fusion, spatial, ml,
  statistical, or the would-be draw — currently affects a real fleet run at all**, because
  `impute_missing()` is never called by `enrich_semantics` (a deliberate T07-scope boundary, not a
  bug); any promotion decision therefore has a second, unscoped cost (the `enrich_semantics` reroute)
  on top of whichever tier-specific switch is flipped. The "zero-fitted-parameters" guarantee's own
  arc-internal definition ("never tuned against EUI") is narrower than a plain reading ("no fitted
  model coefficients anywhere") and this task could not determine which reading the user intends —
  reported as an open question in the brief §5, not resolved here.
