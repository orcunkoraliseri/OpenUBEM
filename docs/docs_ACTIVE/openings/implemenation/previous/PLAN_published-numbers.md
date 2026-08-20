# PLAN — Integrity of the numbers we publish (OPEN-01 · 02 · 03 · 04, bundling OPEN-28)

> **Slug:** `published-numbers` · **Opened:** 2026-08-05 · **Author:** manager session
> **Selected by the user** 2026-08-05: *"les nombres déjà publiés, analyse, créer un plan
> d'implémentation … pour ces quatre options, commencer à l'exécution."*
> **Binding upstream contract:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` §2
> (Theme A) and §9 pattern 1. This plan does not restate the register; it executes against it.
> **Governing arc rule (register §5 of the director prompt):** *no execution plan may be written for
> an item until that item's first measurement has been made.* This document therefore opens as a
> **measurement plan**. Phase 2 (remediation) is deliberately empty and is written only after CP-M3.

---

## 1. Why these four are one plan and not four

The register's §9 pattern 1 states the categorical fact that motivated the user's selection:

> **Four items (OPEN-01, 02, 03, 04) can make already-published numbers wrong. Every other item makes
> the project *less complete*.**

They are grouped here because they are the same failure class, not because they share a mechanism.
They do **not** share a fix. Concretely:

| Item | What it can make wrong | Class |
|---|---|---|
| OPEN-01 | The **denominator** of every `layout_assign` per-building EUI | arithmetic |
| OPEN-02 | Our **ability to check** any denominator, in any mode, ever | evidence gap |
| OPEN-03 | The **numerator** — internal loads modelled at 2022 code for every vintage | modelling |
| OPEN-04 | The **classifier accuracy metric** itself, drifted 4 points, cause unknown | instrument |
| *(OPEN-28)* | Every **cross-mode** comparison — two harvest generations mixed | provenance |

**OPEN-28 is carried in this plan even though the user named four items.** The register (§2, OPEN-28)
establishes that OPEN-01 + OPEN-02 + OPEN-28 are closed by **one** fleet re-run and that planning any
of them separately spends a fleet pass to fix a third of the problem. Excluding it would guarantee
rework. It is included **for measurement only**; it does not widen the remediation scope, which is not
yet written.

### The gate that decides everything downstream

OPEN-01, OPEN-02 and OPEN-28 all terminate in the same question: **can we afford to keep
`eplusout.eio` on a five-mode fleet pass?** The cluster template deletes it for disk economy
(`>800 GB untrimmed per city`). If retention is affordable, one re-run closes three items. If it is
not, all three need different, individually weaker remedies. **M02 is therefore the highest-leverage
task in this plan and is dispatched first, in parallel with M01.**

---

## 2. Hard rules for the executor

These override anything you infer from the codebase, from prior plan docs, or from your own judgement.

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Interpreter `./.venv/Scripts/python.exe`.
2. **This is a MEASUREMENT plan. Remediation is FORBIDDEN inside it.** You may not fix a defect you
   measure, not even a one-line one, not even if it is obviously correct. Record it and stop. The
   whole value of the investigation-then-execution split is lost if a measurement task also patches.
3. **Do not write a plan.** If you believe the plan is wrong, STOP and quote the conflict. The manager
   writes plans; you execute them.
4. **No cluster compute in Phase 1.** Every task in this document runs locally and reads files that
   already exist. If a task appears to need a cluster job, you have misread it — STOP and ask.
   If any remote step is ever authorised later, it goes through `sbatch` only: **never** `srun`,
   never `ssh … python …` on the Speed login node.
5. **Never `git commit`.** Git is handled externally by the user.
6. **Never edit** root `main.py`, any `OVERVIEW` or `DESIGN` doc, anything under
   `layoutAssigner/figures/`, `openubem/idf/opaque_assembly.py`, `openubem/viz/`, or the
   `t17_*`/`t18_*`/`t19_*`/`t20_*` harvests. **Do not re-submit the T20 fleet.**
7. **Progress-log entries are append-only.** Never rewrite a frozen entry, including ones you believe
   are wrong — correct in a new entry citing the old.
8. **A parser that finds nothing must say so, never report `0`.** A zero and an empty read are
   different results and must be distinguishable in your output.
9. **Recompute every headline number from the named file before you report it.** State in your
   progress-log entry which file each number came from, with a `path:line` or a reproducible command.
   Numbers that cannot be re-derived from a named artifact do not go in the report.
10. **Ground truth is the raw artifact.** `eplusout.err` for run outcome (require the `** Severe **`
    line specifically), `eplusout.eio` for multiplier-aware floor area. **Never the `.end` file.**
    **Never the `has_fatal` column** — it is `False` on all 8,160 rows including the 7 real fatals
    (E-LA-21, alias E-LA-39).
11. **Default to no comments** in any code you write. One short line maximum, only where the WHY is
    non-obvious.
12. **Check what generated a CSV or figure before concluding from it.** See §5.6 — this plan contains
    a live example of a pre-existing CSV that measures the wrong quantity while looking correct.

---

## 3. File layout to create

All measurement reports go to the arc's `extra/` folder — **user instruction, 2026-08-05: the
`openings/` folder itself stays clean.**

```
docs/docs_ACTIVE/openings/
├── INVESTIGATION_open-items-register.md      (existing — amend only as §7 instructs)
├── implemenation/
│   └── PLAN_published-numbers.md             (this file — you append to §8 only)
└── extra/
    ├── MEASUREMENT_open-05_defect-id-sweep.md          (existing, closed, do not touch)
    ├── MEASUREMENT_open-01_denominator-factors.md      (M01)
    ├── MEASUREMENT_open-02_eio-disk-budget.md          (M02)
    ├── MEASUREMENT_open-03_loads-vintage-split.md      (M03)
    ├── MEASUREMENT_open-04_accuracy-drift-bisect.md    (M04)
    └── MEASUREMENT_open-28_harvest-generation-join.md  (M05)
```

Any throwaway script goes in the session scratchpad, **never** under `docs/` (no `.py` under `docs/`,
ever) and **never** committed into `openubem/`. Any `.png` goes flat to `openubem/outputs/`, mirrored
into `docs/docs_ACTIVE/openings/extra/`.

Supporting CSVs a task produces go to `openubem/outputs/comparisons/` with an `open01_`/`open02_`/…
prefix, and are cited by path from the measurement report.

---

## 4. Dependency decisions — pinned, do not re-debate

- **Python:** `./.venv/Scripts/python.exe`. No new third-party dependency may be added by any task in
  this plan. `pandas`, `geopandas`, `eppy`/`geomeppy` are already present and are sufficient.
- **IDF parsing:** use `eppy`/`geomeppy` through the project's own accessors where one exists
  (`openubem.geometry.layout_assigner.compute_band_map`). Do **not** hand-roll an IDF text parser —
  §5.6 explains what that produced last time.
- **EnergyPlus IDD:** `config.ENERGYPLUS_IDD_PATH`, locked at 23.1. Do not change it.
- **Baseline IDF library:** `config.BASELINE_IDF_DIR` =
  `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231` (25 files, verified
  present — §5.1). This directory is **outside the repo**; read-only, never write into it.
- **No new fixtures, no relabelling, no test edits** except where a task explicitly says so (only M04
  runs existing tests, and it runs them unmodified).
- **Statistical reporting:** report `n`, median and the full distribution when a distribution exists.
  A single mean is not an acceptable summary for any quantity in this plan.

---

## 5. Source-of-truth verified facts — grepped by the manager 2026-08-05

Each of the following was read at HEAD by the manager in this session. **You may rely on these
without re-deriving them.** Anything not on this list, you derive yourself and cite.

### 5.1 The baseline library is 25 files and is overwhelmingly STD2022
`openubem/config.py:49-53` sets `BASELINE_IDF_DIR` to the E+ 23.1-transitioned sibling library. That
directory contains **exactly 25 `.idf` files** (verified by listing). Filenames carry the vintage
token: `ASHRAE901_*_STD2022_Buffalo.idf` for the ASHRAE 90.1 set, `STD2019` for the two large data
centres, `90.1-2019_6A_Buffalo_v221` for College/Laboratory/small data centres/Tall/SuperTall, plus
`Supermarket_V22.1.idf`. **Relevant to OPEN-03: no baseline in the library is older than 2019 code.**

### 5.2 `match_storeys()` mutates only on `applied` — OPEN-01's root contract
`openubem/geometry/layout_assigner.py:542-544`, verbatim:

> *"Mutates `idf` in place ONLY when the returned status is "applied"; every other status leaves
> `idf` untouched."*

Statuses `identity`, `fallback_shorter` and `fallback_not_expressible` therefore simulate the
**prototype's** storey count while the published EUI divides by the **real** building's
`footprint_area_m2 × levels`.

### 5.3 `n_storeys_represented` is multiplier-aware; the band count is not
`layout_assigner.py:525-528`:

```
n_proto = len(bands)
n_storeys_represented = int(round(sum(b["storeys_in_band"] for b in bands)))
```

`n_proto` counts **Z-bands**. `n_storeys_represented` sums each band's `storeys_in_band`, which
carries the `ZoneGroup` list multiplier. **These two numbers differ, and OPEN-01's error factor is
built from the second one.** See §5.6 for why this matters more than it looks.

### 5.4 EnergyPlus compounds `Zone.Multiplier` with the `ZoneGroup` list multiplier
`layout_assigner.py:565-578` (R10 / E-LA-36), measured, not assumed: *"MidriseApartment n_real=4
produced 6 simulated storeys, not 4"*. Any storey arithmetic that ignores the list multiplier
overcounts. This is the mechanism behind §5.6.

### 5.5 The cluster template deletes `.eio` unconditionally — OPEN-02's root cause
`scripts/cluster/submit_fleet_t08.sbatch:60-63`:

```
# T08 output trimming: keep only SQL + completion + error files; delete bulk output.
# This is critical for fast_zone city passes (>800 GB untrimmed per city).
rm -f "$OUTDIR"/*.eso \
      "$OUTDIR"/*.eio \
```

`.eio` is deleted alongside `.eso`, `.mtd`, `.rdd`, `.mdd`, `.htm`, `.tab`, `.csv`, `in.idf`,
`expanded.idf`, `Energy+.idd` and several `eplusout.*` files. **The 800 GB justification in the
comment is about the whole trim set, not about `.eio` alone.** Whether `.eio` specifically is
expensive is unmeasured — that is M02.

### 5.6 ⚠️ A pre-existing CSV measures the wrong quantity while looking correct — READ THIS
`openubem/outputs/comparisons/a1_prototype_storey_structure.csv` exists and appears to answer OPEN-01's
first measurement. **It does not.** Its column is `num_modelled_storeys`, which is the **band count**
(`n_proto`), not `n_storeys_represented`. Two independent confirmations from the file's own rows:

- `MidriseApartment` → `num_modelled_storeys = 3`, `has_multiplier_gt_1 = False`. But the register
  (OPEN-01, verified against real `eplusout.eio`) measures its simulated equivalent as **4** storeys —
  3 bands with a `ZoneGroup` list multiplier of 2 on the middle band. **The CSV's own
  `has_multiplier_gt_1` flag reads `False` for exactly the archetype the project has measured as
  carrying a list multiplier**, so that flag is testing `Zone.Multiplier` and is blind to `ZoneGroup`.
- `HighriseApartment` → `recomputed_floor_area_m2 = 2350.94` against
  `registry_baseline_area_m2 = 7835.0`, a **−70.0%** disagreement, i.e. a factor of exactly 3.33.
  A file that reproduced the real simulated area would not be off by a clean multiple.

**Consequence for M01:** you must recompute `n_storeys_represented` yourself via
`compute_band_map()`, and you must **not** cite this CSV as evidence. You *should* cite it as a
counter-example, and M01 explicitly asks you to state where it diverges — that divergence is itself
a finding, because the CSV is in the published outputs directory today.

Note also its `area_diff_pct` column: `SuperTallBuilding +349%`, `TallBuilding +473%`, `Laboratory
+97%`, `SmallOffice +111%`, `PrimarySchool −50%`, `SuperMarket −50%`. **Do not interpret these in
M01.** Record them; they are an input to the Phase-2 decision, not a conclusion.

### 5.7 `patch_envelope()` patches the envelope only — OPEN-03's mechanism, confirmed
`openubem/geometry/envelope_patcher.py:1-13` (module docstring) states it overwrites the baseline's
**opaque/glazing material properties** with the real building's resolved
`u_wall_w_m2k`, `u_roof_w_m2k`, `u_floor_w_m2k`, `u_window_w_m2k`, `shgc_window`. `_ENVELOPE_COLS`
(`:44`) is exactly those five columns. **A grep for `vintage` in `envelope_patcher.py` returns no
matches.** Lighting, equipment, occupancy and their schedules are therefore left at the baseline's
own code year (§5.1: 2022 for most archetypes). **The register's 📄 claim for OPEN-03 is structurally
confirmed at HEAD.** What is *not* established is (a) whether this is a deliberate documented
approximation, and (b) how large the resulting error is — that is M03.

### 5.8 The labelled-accuracy gate: what it actually asserts
`tests/test_building_classifier.py:1034-1053`, class `TestLabelledTop1Accuracy`, three tests:

| Test | Assertion |
|---|---|
| `test_coarse_top1` | `acc >= 0.90` on `expected_coarse_class` |
| `test_fine_top1` | `acc >= 0.70` on `expected_archetype` |
| `test_archetype_coverage_min10` | `≥10` distinct archetypes in the fixture |

Fixture: `tests/fixtures/labelled_archetypes_50.csv` (ratified, **do not edit** —
`tests/fixtures/README.md:12`), classified live through `BuildingClassifier()` over
`boston_downtown_500m.gpkg` and `chicago_loop_500m.gpkg` (`:1006-1031`).

⚠️ **Open discrepancy the manager could not resolve from the register, and which M04 must settle
first:** the register records the drift as **92.0% → 88.0%** and says the gate *"still clears its
pass gates"*. **88.0% does not clear the 90% coarse gate.** So either the drifted metric is
`test_fine_top1` (gate 70%, which 88.0% does clear), or it is a third metric reported elsewhere.
**M04's first action is to identify which of the three numbers drifted. Do not assume.**

### 5.9 `.eio` files exist locally and are ~1 MB — a lead, not the answer
`find` over the working tree returns `eplusout.eio` files with sizes up to **1,092,989 bytes**
(`scratchpad/t18_t08_t09_work/work/ep_raw/`), with several in the 0.99–1.03 MB range. **These are
`layout_assign`-family runs and are not representative of all five resolution modes** — `.eio` size
scales with zone and surface count, and `fast_zone` is the mode the 800 GB comment names. A naive
`1 MB × 8,160 × 5 ≈ 41 GB` is the *shape* of the answer, **not the answer**. M02 must measure per
mode, or state explicitly which modes it could not measure and why.

---

## 6. Task list — Phase 1, measurement only

Five tasks. Each is one dispatch, one report, one progress-log entry. **Remediation forbidden in all
five.**

---

### M01 — Per-archetype denominator error factor (OPEN-01)

**What to do.** Produce, for all 25 baseline archetypes, the multiplier-aware `n_storeys_represented`,
and from it the published-EUI error factor `n_storeys_represented / num_floors` applied to the real
fleet. Deliver a per-archetype table and a fleet-wide building count at each factor.

**Why.** Register §2 OPEN-01: *"`n_storeys_represented` per archetype — only `MidriseApartment` (=4)
has been measured."* Fleet-wide **6,939 of 7,442** evaluated buildings are non-`applied`, so the
factor applies to 93% of the evaluated population, and 17 of 18 archetypes' factors are unknown.
Without this table nobody can say whether the defect is a rounding issue or a 4× error, and the three
candidate remedies in OPEN-01 (fix the denominator / fix the simulation / stop publishing per-building
EUI) cannot be chosen.

**How.**
- For each `.idf` in `config.BASELINE_IDF_DIR`, load it and call
  `openubem.geometry.layout_assigner.compute_band_map()`. Read `n_proto`,
  `n_storeys_represented`, `plate_proto_m2`, `recomputed_area_m2` from its return (§5.3).
- Map IDF filename → archetype via `layout_assigner.ARCHETYPE_IDF_MAP` (do not hand-map).
- Join to the real fleet using `openubem/outputs/comparisons/t20_r10_reach_change.csv`, keyed on
  archetype and `num_floors`, restricted to **non-`applied`** rows. Report the building count at each
  distinct error factor, per archetype, and fleet-wide.
- **Do not use `a1_prototype_storey_structure.csv` as a source (§5.6).** Instead, add a short section
  to the report listing every archetype where your `n_storeys_represented` differs from that file's
  `num_modelled_storeys`, with both values. That divergence list is a required deliverable.
- Report the six locally-run buildings from `openubem/outputs/comparisons/r06c_local_results.csv`
  separately as the **only** rows with a simulation-verified denominator, and state that explicitly.
- Cross-check: for `MidriseApartment` your method must return **4**. If it does not, **STOP and
  report** — do not adjust the method to reach 4.

**How to test.** (a) The `MidriseApartment = 4` cross-check above, stated pass/fail in the report.
(b) `sum` of your per-archetype fleet counts must equal the non-`applied` row count in
`t20_r10_reach_change.csv`; print both numbers and their difference. (c) For any archetype where
`compute_band_map()` raises or returns `n_storeys_represented == 0`, say so explicitly — never emit
a silent `0` (rule 8).

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-factors.md` +
`openubem/outputs/comparisons/open01_denominator_factors.csv`.

---

### M02 — `.eio` disk budget for a five-mode fleet pass (OPEN-02, gates OPEN-28)

**What to do.** Establish what retaining `eplusout.eio` would actually cost on a full five-mode fleet
pass (8,160 buildings × 5 resolution modes), and compare it against the cluster storage actually
available.

**Why.** Register §2 OPEN-02: *"Measure the actual per-building `.eio` size first; it is a small text
file and the fear may not survive contact with the number. **That measurement is the whole of the
investigation for this item.**"* Register §2 OPEN-28 makes it the gate on the three-item bundle:
retaining `.eio` is *"a storage decision, not a one-line edit."* Every downstream option for OPEN-01,
OPEN-02 and OPEN-28 depends on this one number.

**How.**
- Inventory every `eplusout.eio` in the working tree (including `scratchpad/`) with its **byte size**
  and its resolution mode, inferred from its run directory and stated per file. Report the size
  distribution **per mode**: n, min, median, p90, max.
- The modes are `auto`, `building`, `floor`, `fast_zone`, `layout_assign`. **`fast_zone` is the one
  the 800 GB comment names (§5.5) and is the one that matters most.** If no `fast_zone` `.eio` exists
  locally, say so plainly and do **not** extrapolate from another mode — instead, report the zone
  count ratio between modes from any available `in.idf`/`expanded.idf` pair and give a *bounded*
  estimate with the bound stated. A stated unknown is a valid result here; a fabricated median is not.
- Produce the fleet estimate as `median_size(mode) × 8,160` summed over the five modes, and also a
  worst case using `max` instead of median. Show both.
- Put it in context: report the same statistics for the files the trim **keeps** (`.sql`, `.err`,
  `.end`) so the marginal cost of `.eio` is expressed as a percentage of what is already retained, not
  only in absolute GB.
- **Check the actual quota.** `ssh` to Speed for **lightweight ops only** — `quota`, `df -h`, `ls`,
  `du -sh` on our own directories. **No compute, no `srun`, no `python`.** If you cannot reach it or
  are unsure whether a command counts as compute, skip it and say so — an unanswered quota question
  is fine, a login-node compute job is not.
- **Never touch, cancel or requeue any cluster job**, ours or another project's.

**How to test.** Sum of your per-file sizes must reproduce from a single re-run of your inventory
command; include the command in the report. State explicitly, in one sentence at the top of the
report, whether the answer is *"retention is cheap"*, *"retention is expensive"*, or *"cannot be
determined without a `fast_zone` sample"* — the manager needs that sentence to make the bundle
decision.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-02_eio-disk-budget.md` +
`openubem/outputs/comparisons/open02_eio_inventory.csv`.

---

### M03 — Is the loads/envelope vintage split deliberate, and how big is it? (OPEN-03)

**What to do.** Two parts. (a) Determine whether modelling internal loads at 2022 code while patching
the envelope to the real vintage is a **documented approximation** or an **oversight in the patching
path**. (b) Bound the size of the resulting error.

**Why.** Register §2 OPEN-03: *"The answer changes whether this is a defect or a disclosure."*
Roughly half of `layout_assign`'s −29% cross-mode gap was attributed to this at the 2026-07-26 close
and it was never actioned or re-verified. §5.7 confirms the mechanism at HEAD; what is missing is
intent and magnitude.

**How, part (a) — intent.** Search the DESIGN docs, the `layoutAssigner` arc plan docs and the results
docs for any statement that internal loads are deliberately held at a single code year. **Read the
documents; do not infer intent from the code.** Report one of exactly three verdicts, each with a
`path:line` citation: **documented approximation** / **undocumented but deliberate (traceable to a
decision that was never written into a spec)** / **no trace of a decision anywhere**. If you find
contradictory statements, report both — do not adjudicate.

**How, part (b) — magnitude.** Do **not** simulate. Compare, statically, the internal-load fields
between a baseline IDF and the same archetype's older-vintage equivalent where one is available in the
tree (`docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/sources/*_90.1-2013.idf` holds a
`90.1-2013` set for 12 archetypes — treat it as read-only source material). For the archetypes present
in both, report the ratio of `Lights` W/m², `ElectricEquipment` W/m² and `People` m²/person between
2013 and 2022 code. **That ratio is the bound on the numerator error for those archetypes**, and it is
obtainable without a single EnergyPlus run.
- State clearly that 2013-vs-2022 is a **proxy** for the real vintage spread and is not the fleet's
  actual vintage distribution.
- Then report the fleet's actual `vintage_standard` distribution from Stage-2 output
  (`openubem/semantic/construction_sets.py:126` `resolve_vintage()` produces the token) so the manager
  can see how many buildings sit far from 2022 code. If you cannot locate a fleet-wide vintage column,
  say so rather than reconstructing one.

**How to test.** Part (a) is tested by its citations: every verdict word must carry a `path:line` a
reader can open. Part (b): report `n` archetypes matched between the two libraries and name the ones
you could not match. If the ratio for any archetype is exactly 1.000, flag it — identical loads across
a 9-year code gap is more likely a parsing error than a finding.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_loads-vintage-split.md` +
`openubem/outputs/comparisons/open03_load_vintage_ratios.csv`.

---

### M04 — Bisect the classifier accuracy drift (OPEN-04)

**What to do.** Identify which metric drifted and which commit moved it.

**Why.** Register §2 OPEN-04: *"an accuracy gate that drifts without anyone noticing is a broken
instrument regardless of whether it still passes. The open item is the unexplained drift, not the
88%."* The suspected cause — the Phase-D fusion/crosswalk work of 2026-07-13 — has never been
confirmed or falsified.

**How.**
- **First, resolve §5.8's discrepancy.** Run `TestLabelledTop1Accuracy` at HEAD unmodified and record
  all three current numbers. Then locate where `92.0%` and `88.0%` are recorded in the project's docs
  and state which of the three metrics those two numbers refer to, with a `path:line`. **If the
  92.0/88.0 pair refers to a metric that is not one of these three, say so and stop before bisecting**
  — bisecting the wrong metric is worse than not bisecting.
- Then bisect: run the identified test across the commit range between the R3-era reference and HEAD.
  Use `git bisect` or an explicit checkout loop; either is acceptable, but the run must be
  **read-only with respect to the working tree** — restore HEAD when finished and verify with
  `git status` that nothing is left modified or staged.
- Report the accuracy at each commit tested, and name the **first commit at which the value changed**,
  with its hash, date and subject line.
- Confirm or falsify the Phase-D hypothesis explicitly. *"Falsified"* is a fully acceptable result and
  must be reported as plainly as a confirmation.
- **Do not edit the fixture, the tests, or the classifier.** Not one line, whatever you find.

**How to test.** The bisect is validated by reproducing the drift end-to-end: report the metric at the
R3-era reference commit and at HEAD, and show that the difference matches the drift you set out to
explain. **If it does not reproduce, that is the finding** — report it and stop. Confirm the working
tree is clean at HEAD in your progress-log entry.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-04_accuracy-drift-bisect.md` +
`openubem/outputs/comparisons/open04_accuracy_by_commit.csv`.

---

### M05 — T08 vs T20 harvest-generation join (OPEN-28, quantifies the OPEN-08 confound)

**What to do.** Establish, by table join and with no simulation, how comparable the T08 and T20
harvests actually are at the building level.

**Why.** Register §2 OPEN-28: *"How many buildings are actually shared between T08 and T20 with
identical Stage-2 inputs, and whether their archetype/vintage agree. This is a table join, no
simulation, and it directly quantifies the OPEN-08 confound."* Every cross-mode number the project
publishes rests on the answer, including the −29.1% figure that OPEN-03 partly explains.

**How.**
- Locate the T08 and T20 harvest result tables. Name the exact files you used, with paths, at the top
  of the report — **provenance first, numbers second.**
- Join on building identity (`osm_id` / `way/nnnn`, whichever the tables carry) and report: rows in
  T08 only, rows in T20 only, rows in both.
- For the shared rows, report **archetype agreement** and **vintage agreement** as counts and
  percentages, plus the top disagreeing pairs (e.g. `MediumOffice → SmallOffice`, n=…). This is the
  E-LA-22 / OPEN-08 confound, quantified for the first time.
- Establish **which harvest each side of the −29.1% cross-mode figure came from**. The register is
  explicit that this *"has not been established"* and *"is part of the first measurement, not an
  assumption to carry forward."* Cite the file the −29.1% is computed from.
- **Do not compute a corrected cross-mode delta.** That is remediation and is out of scope. Report
  comparability only.

**How to test.** `rows_in_both + t08_only + t20_only` must equal the union size; print all four.
Sample **5 shared buildings at random** and verify their archetype/vintage by hand against the raw
tables; include those 5 rows verbatim in the report as an audit trail.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-28_harvest-generation-join.md` +
`openubem/outputs/comparisons/open28_t08_t20_join.csv`.

---

## 7. Stop-and-report points

Three checkpoints, chosen at the integration points where a silent error would compound — **not one
per task.**

### CP-M1 — after M01 + M02 · *the bundle gate*
The manager decides whether the OPEN-01/02/28 fleet re-run is affordable and worth it. **This is the
single most consequential decision in the plan.** M02's one-sentence verdict plus M01's error-factor
table are what the decision is made on. **No Phase-2 work of any kind before this checkpoint.**
Manager action: re-derive M01's `MidriseApartment = 4` independently, and re-run M02's inventory
command, before signing.

### CP-M2 — after M03 + M05 · *the numerator and provenance checkpoint*
Together these two say whether the published cross-mode numbers are salvageable by re-running, or
whether they need a modelling change as well. If M03 returns *"no trace of a decision anywhere"* and
M05 shows low archetype agreement, the cross-mode results are in worse shape than the register
currently records, and the register's §2 must be amended before anything is planned.

### CP-M3 — after M04 · *the instrument checkpoint*
OPEN-04 stands alone: it is about whether the accuracy metric can be trusted at all. It also feeds the
still-unanswered OPEN-22 question (register §6) — if the drift turns out to be tag-coverage moving
rows across the rule-17a boundary, OPEN-04 and OPEN-22 are one finding, and the manager puts that to
the user together.

**After CP-M3:** the manager writes Phase 2 into this document as `§9 — Execution`, per the register's
governing rule. **Nothing in Phase 2 is written, scoped, costed or approved today.**

---

## 8. Progress log

*Append one entry per completed task. Append-only — never rewrite an entry, including one you believe
is wrong; correct it in a new entry that cites the old.*

```
#### MXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + register/DESIGN citation>
- Test status: <the "how to test" result, pass/fail, with numbers>
- Headline numbers, each with the file it was re-derived from: <…>
- Notes: <auditor-relevant>
```

#### M02 — `.eio` disk budget for a five-mode fleet pass (OPEN-02) — completed 2026-08-05
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-02_eio-disk-budget.md`,
  `openubem/outputs/comparisons/open02_eio_inventory.csv` (3,714 rows: 881 `.eio` + 940 `.sql` +
  948 `.err` + 945 `.end`, each row carrying `path`, `size_bytes`, `file_type`, `mode`,
  `mode_basis`).
- Deviations: none. Remediation forbidden per §2 rule 2 — no cluster script touched.
- Test status: PASS. (a) Sum-reproducibility: inventory command
  `find . -iname "eplusout.eio" -type f -printf "%s\t%p\n"` and the independent Python walk both
  return 881 files / 77,471,124 bytes. (b) One-sentence verdict stated at the top of the report.
  (c) The 0-file result for `auto`/`building`/`floor`/`fast_zone` is reported explicitly (two-step
  search: repo tree + every surviving `%TEMP%\ubem_*` dir), never as a silent `0`.
- Headline numbers, each re-derived from the named file:
  - **Verdict: "retention is cheap."** `.eio` fleet-wide worst-case (42.9 GB) is 0.42–0.53% of
    available disk headroom (§6 of the report).
  - `layout_assign` `.eio` size distribution (measured, n=874, from the 881-file inventory above):
    min 6,736 B, median 76,068 B, p90 160,850 B, max 1,092,989 B.
  - `auto`/`building`/`floor`/`fast_zone`: **0 local `.eio` samples found** — the T08 local-remainder
    run wrote to an OS-temp path (`scripts/cluster/t08_local_remainder.py:488`,
    `tempfile.gettempdir()/"ubem_t08_local"`) that no longer exists on disk; every T17–T20 harvest
    download trims `.eio` on the way down, mirroring the cluster's own T08 policy.
  - `fast_zone` **bounded estimate** (not a measurement — zone-count ratio from
    `openubem/outputs/comparisons/t08_all_modes_eui.csv` × `t19_layout_assign_eui.csv`, 4,530
    buildings/side, 5 shared cells): median-ratio 0.333 → ≈25,353 B/building; max-ratio 2.491 →
    ≈2,722,745 B/building (fast_zone's zone-count tail, 837 max vs. layout_assign's 336 max, is the
    mechanism behind the sbatch comment's 800 GB fear).
  - Fleet-wide 5-mode estimate (8,160 buildings × 5 modes): median-based **1.345 GB**; worst-case
    **42.923 GB**. `layout_assign` alone (measured, and the only mode all current published fleet
    numbers T17–T20 actually come from): 0.621 GB typical / 8.919 GB worst-case.
  - Marginal cost vs. already-retained (`eplusout.sql`/`.err`/`.end`, from the same 881-adjacent
    inventory): median-based 11.4%, worst-case-based 12.6% — `.eio` adds roughly an eighth to what
    the pipeline already writes per fleet pass.
  - Cluster quota (`ssh o_iseri@speed-submit2.encs.concordia.ca "quota -s"`): 5.8 TB used / 10.0 TB
    limit on `/speed-scratch` → 4.2 TB personal headroom. Shared filesystem
    (`df -h /speed-scratch/o_iseri`): 113 TB used / 121 TB → **only 8.1 TB free across all users**,
    the actual binding constraint. Current total footprint (`du -sh /speed-scratch/o_iseri/openubem`):
    36 GB, of which `fleets/` (all harvest generations, trimmed) is 33 GB.
- Notes: No cluster job was cancelled, requeued or touched — only `quota -s`, `df -h`, `du -sh`, `ls`
  were run against the login node, all lightweight per §2 rule 4. One `ssh … -o BatchMode=yes`
  attempt failed non-interactive key auth and was dropped in favour of interactive SSH — not a
  compute attempt. §5.9's "1 MB × 8,160 × 5 ≈ 41 GB is the shape, not the answer" is superseded by
  this task's actual per-mode measurement: the shape held up (measured fleet worst-case 42.9 GB vs.
  the plan's shape-only 41 GB), but only because `layout_assign` (the mode with the most local
  evidence) happens to size similarly to the naive guess — `building` mode is ~16x smaller and
  `fast_zone`'s tail is ~2.5x bigger, so the naive uniform guess would have been wrong per-mode even
  though it landed close in aggregate. An independent cross-check from a legacy, unconfirmed-mode
  fleet directory (`t11cc_nyc_centre_phaseA`, T11-era, 167 buildings, untrimmed) averaged 76,950
  B/building `.eio` — within 1.2% of this report's measured `layout_assign` median, from a
  completely different harvest generation. **CP-M1 is gated on M01 also completing** (already done
  per the existing `MEASUREMENT_open-01_denominator-factors.md` in this folder) — this entry does
  not itself close CP-M1; the manager still owes the independent re-derivation §7 CP-M1 requires
  before signing.

#### M01 — Per-archetype denominator error factor (OPEN-01) — completed 2026-08-05
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-factors.md`,
  `openubem/outputs/comparisons/open01_denominator_factors.csv` (6,939 rows).
- Deviations: none.
- Test status:
  - (a) `MidriseApartment` cross-check: **PASS** — `compute_band_map()` on the raw, unscaled baseline
    returns `n_storeys_represented = 4`.
  - (b) Row-count reconciliation: matched (6,939) + unmatched (0) = 6,939 = non-`applied` row count in
    `t20_r10_reach_change.csv` (`new_status != "applied"`). Difference = 0.
  - (c) No archetype raised in `compute_band_map()` and none returned `n_storeys_represented == 0` or
    `n_proto == 0`; stated explicitly (rule 8) rather than emitting a silent `0` — none occurred.
- Headline numbers, each with the file it was re-derived from:
  - `n_storeys_represented` per archetype (all 28 archetype tokens / 25 files): recomputed live via
    `layout_assigner.compute_band_map()` on each `.idf` in `config.BASELINE_IDF_DIR`
    (`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`) — not read from any
    CSV.
  - Fleet non-`applied` row count 6,939 of 7,442: `openubem/outputs/comparisons/t20_r10_reach_change.csv`,
    `new_status` column.
  - Error-factor distribution (median 2.0, n=6,939, range 0.118–10.0): computed from the join above,
    written to `openubem/outputs/comparisons/open01_denominator_factors.csv`.
  - 6 simulation-verified rows: `openubem/outputs/comparisons/r06c_local_results.csv`.
  - Divergence baseline for §4: `openubem/outputs/comparisons/a1_prototype_storey_structure.csv`
    (`num_modelled_storeys` column), used only as a comparison target, never as a source (plan §5.6 /
    §2 rule 12).
- Notes: Only 2 of 28 archetype tokens (`MidriseApartment`, `HighriseApartment`) carry a `ZoneGroup`
  list multiplier; both diverge from `a1_prototype_storey_structure.csv`'s `num_modelled_storeys` (3
  vs. real 4, and 3 vs. real 10, respectively) — the CSV measures the band count, not the
  multiplier-aware storey count, confirming plan §5.6. The other 3 apparent "divergences"
  (`LargeOfficeDetailed`/`MediumOfficeDetailed`/`SmallOfficeDetailed`) are not value mismatches — `a1`
  has no row for those tokens at all, since it is keyed one-row-per-file and those 3 tokens share a
  file with their non-`Detailed` counterpart. Only 877 of 6,939 (12.6%) non-`applied` fleet buildings
  have `error_factor == 1.0`; median factor is 2.0 fleet-wide. No remediation was performed or proposed
  (measurement-only task, per plan §2 rule 2).

#### M05 — T08 vs T20 harvest-generation join (OPEN-28) — completed 2026-08-05
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-28_harvest-generation-join.md`,
  `openubem/outputs/comparisons/open28_t08_t20_join.csv` (8,160 rows).
- Deviations: none from the task's stated scope. One clarification: the task title says "T08 vs T20,"
  and the join is built exactly that way, but §6's own required sub-question (which harvest each side
  of the −29.1% figure came from) resolved to **T08-`auto` vs T19-`layout_assign`, not T20** — reported
  in full in §5 of the measurement doc, not silently reconciled to T20.
- Test status:
  - (1) Row-count reconciliation: `rows_in_both` (4,530) + `t08_only` (0) + `t20_only` (3,630) = 8,160
    = union (8,160). **PASS.**
  - (2) 5 shared buildings sampled at random (`seed=42`): all 5 archetype/floor-area values reproduced
    exactly against the raw CSV rows via independent `awk` extraction (not through the pandas join).
    Vintage cells marked `N/A` for all 5 — no vintage column exists in either raw table (see below). No
    STOP condition triggered; verbatim rows in measurement doc §6.
- Headline numbers, each with the file it was re-derived from:
  - T08 harvest table: `openubem/outputs/comparisons/t08_all_modes_eui.csv` (18,120 rows / 4,530
    unique buildings, 5 cells). T20 harvest table: `openubem/outputs/comparisons/t20_layout_assign_eui.csv`
    (8,160 rows, 12 cells). Both are each script's own `OUTPUT_ALL_CSV`, not a derived summary.
  - Building overlap: 4,530/4,530 T08 buildings present in T20 (100%); 3,630 T20-only buildings are the
    7 cells T08 never covered.
  - Archetype agreement on the 4,530 shared buildings: **3,923/4,530 = 86.60%**; disagreement
    **607/4,530 = 13.40%**, top pair `MediumOffice → SmallOffice` (n=396, 70.8% of T08's MediumOffice
    population) — from `open28_t08_t20_join.csv`.
  - Root cause of the 13.40% drift, traced (not just observed): git commit `0df422e`
    ("classification thresholds updates," 2026-07-03 10:53) changed `archetype_id` in the shared
    `05_results.gpkg` fixture between T08's harvest run (2026-07-01) and T20's (2026-08-04). Read-only
    `git show <rev>:<path>` extraction of the pre/post blobs reproduces the identical 607-row,
    identical-pairs disagreement, and the harvest CSVs match their respective blobs 4,530/4,530 with
    zero mismatches — full chain-of-custody confirmation. Working tree verified clean via `git status`
    before and after the extraction.
  - Floor-area (denominator) agreement: 4,530/4,530 (100%) within 1%, from `open28_t08_t20_join.csv`.
  - Vintage agreement: **UNMEASURABLE** — neither T08's nor T20's actual provenance file
    (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg`, at either the
    `e063865` or `0df422e` git state, nor its current on-disk copy) carries a `vintage_standard`
    column at all; `resolve_vintage()` (`openubem/semantic/construction_sets.py:126`) is consumed
    internally by `envelope_patcher` and never persisted to a table either harvest script reads. Two
    other `05_results.gpkg` files elsewhere in the tree do carry `vintage_standard` but belong to the
    unrelated `v11_*`/`v12_*` validation-pipeline lineage (predate T08, different path, never read by
    either harvest script) — deliberately excluded per plan §5.6/§2 rule 12, not substituted.
  - −29.1% figure provenance: `docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md:422-423,449-458`
    (§7.2) — `auto` side from `t08_all_modes_eui.csv`, `layout_assign` side from
    `t19_layout_assign_eui.csv` (**T19, not T20**).
  - No corrected cross-mode delta was computed (plan §2 rule 2 / §6 M05 explicit prohibition).
- Notes: The archetype drift is fully deterministic and 100%-attributable to one commit, not
  resimulation noise — this narrows what CP-M2 needs to weigh: the confound is real (13.4% of shared
  buildings), concentrated in office archetypes (`MediumOffice`/`LargeOffice`/`SmallOffice` account for
  606 of 607 disagreements), and has a named, single root cause rather than an unexplained spread. The
  −29.1% figure's own population (T08 vs T19) was not re-joined here — that would require a separate
  T08-vs-T19 pass, out of M05's stated T08-vs-T20 scope.

#### M03 — Is the loads/envelope vintage split deliberate, and how big is it? (OPEN-03) — completed 2026-08-05
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_loads-vintage-split.md`,
  `openubem/outputs/comparisons/open03_load_vintage_ratios.csv` (12 rows).
- Deviations: none.
- Test status:
  - Part (a): every verdict-relevant claim carries a `path:line` citation opened and quoted
    directly from source, per the plan's test requirement. One contradictory statement found
    (results doc §7.2's explicit "not a defect") is reported in full, not adjudicated away.
  - Part (b): n = 12 archetypes matched between the 90.1-2013 source set and the `STD2022`
    baseline library (`ARCHETYPE_IDF_MAP`); 0 unmatched. All exactly-1.000 ratios (11/12 People,
    2/12 Equipment) were flagged per plan rule and investigated by direct raw-IDF-text spot-check
    (Hospital `People`, RetailStandalone `ElectricEquipment`) bypassing the parser entirely —
    confirmed byte-identical source values in both vintage files, not a parsing defect.
- Headline numbers, each with the file it was re-derived from:
  - **Verdict (a): "undocumented but deliberate (traceable to a decision that was never written
    into a spec)."** Zero matches for `layout_assign`/`resolution_mode` anywhere under
    `docs/docs_main` (this project's DESIGN/OVERVIEW tier) — grepped live this session. The
    decision is traceable to `docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:155`
    (§4 architecture table, pre-implementation) and named explicitly at `:494` (T16 progress log:
    "internal loads are always the DOE baseline's own native density scaled by S... never the real
    building's pipeline-derived `row[...]`... Flagged as a finding for a future arc"), but never
    written into a spec. Contradictory framing noted, not adjudicated: results doc
    `docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md:463` calls it
    "a direct consequence of prototype substitution, not a defect," and the register itself
    (`INVESTIGATION_open-items-register.md:179`) says "documented in results §7, never actioned" —
    both are post-hoc explanation, not a prior accepted-approximation decision.
  - Lights (LPD) ratio 2013-vs-2022, n=12: median **1.722**, range 1.256–2.502, no archetype at
    exactly 1.000. Equipment ratio: median 1.064, range 1.000–1.267. People ratio: median 1.000,
    range 1.000–1.047. All from `openubem/outputs/comparisons/open03_load_vintage_ratios.csv`,
    recomputed live via `geomeppy`/`openubem.geometry.layout_assigner.parse_baseline_zones()`
    against the 12 read-only 90.1-2013 source IDFs and their matched `STD2022` baselines — no
    EnergyPlus run.
  - Fleet `vintage_standard` distribution: **no canonical fleet-wide vintage column exists**
    (searched every `.csv` under `openubem/outputs/` and the repo tree; confirmed independently by
    M05's own finding that neither T08's nor T20's provenance file carries `vintage_standard` at
    all). The only fleet-wide sample found is
    `scratchpad/e-la-20-investigation/i04/fleet_enriched_all_cells.csv` (7,510 rows, 12 cells, a
    prior investigation's re-derivation via the real `enrich_semantics()`/`resolve_vintage()`
    pipeline, not from the current T20 fleet build — reported with that provenance caveat, not
    presented as canonical): `DOERefPre1980` 92.9% (6,975/7,510), `DOERef1980to2004` 2.8%,
    `90.1-2013` 2.4%, `90.1-2007` 1.6%, `90.1-2019` 0.3%.
- Notes: The 2013-vs-2022 Lights/Equipment/People ratios are a **proxy only** — stated explicitly
  in the report — bounding a 9-year code gap, not the fleet's real vintage spread. Given 93% of the
  one available fleet-wide sample resolves to `DOERefPre1980`, the real numerator error for most
  buildings is plausibly larger than the measured 2013-vs-2022 ratios, since `layout_assign` applies
  2022-code internal loads regardless of measured vintage. No remediation was performed or proposed
  (measurement-only task, per plan §2 rule 2).

#### M04 — Bisect the classifier accuracy drift (OPEN-04) — completed 2026-08-05
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-04_accuracy-drift-bisect.md`,
  `openubem/outputs/comparisons/open04_accuracy_by_commit.csv` (5 rows, one per commit tested).
- Deviations: none from the task's stated scope. Bisect used `git worktree add --detach` at
  disposable short paths rather than `git bisect`/in-place checkout — plan §6 M04 permits either
  method, and worktree was chosen specifically to satisfy plan §2's rule against clobbering the
  parallel-task untracked files in the main tree (see Test status below).
- Test status:
  - **Gate (first action, before any bisect):** `pytest tests/test_building_classifier.py::TestLabelledTop1Accuracy -v`
    at HEAD → 3 passed. Live-recomputed exact values: coarse 100.0%, fine 88.0%, coverage 13
    distinct. **§5.8 resolved: the 92.0%/88.0% pair is `test_fine_top1`, confirmed by direct
    `path:line` citation** (`PLAN_step-2-classifier-coverage-R3.md:131,148` for 92.0%;
    `PLAN_input-framework-classification-fixes.md:84,140` for both numbers paired explicitly with
    "fine"). Not a third metric — proceeded to bisect per plan instruction.
  - **Reproduction/validation:** reference (`7635ce2`) fine=92.0% vs. HEAD (`bca92d0`) fine=88.0%,
    diff −4.0 pts, exactly matching the register's recorded drift. **PASS — reproduces.**
  - **Working-tree integrity:** `git status --short` on the main tree identical before and after
    (11 pre-existing entries, none added/removed/modified); `git rev-parse HEAD` unchanged at
    `bca92d0a6cdc33923bea8424f1b86ab0f94d82d9` throughout. All 4 bisected commits were measured from
    disposable worktrees, never from the main tree. No fixture/test/classifier file was edited.
- Headline numbers, each with the file/command it was re-derived from:
  - HEAD (`bca92d0`): coarse 100.0%, fine **88.0%**, coverage 13 — live run via
    `_run_labelled_fixture()` from `tests/test_building_classifier.py:1004-1031`.
  - R3-era reference (`7635ce2`, 2026-06-12, CP-α): coarse 100.0%, fine **92.0%**, coverage 13 —
    live run in a disposable worktree at that commit; independently corroborated by
    `PLAN_step-2-classifier-coverage-R3.md:131,148`.
  - **First commit where `fine_top1` changed: `67ede73a0555f7de977203b8fa673ba15d6a4d45`
    (2026-07-01, "feat: implement input provenance and spatial imputation semantic steps,
    reorganize resolution docs"). fine_top1 moved 92.0% → 84.0%** — a drop, not the recorded rise.
    Root cause traced (not just observed): this commit lands ratified change **E-R3-3**
    (office/hotel/school archetype size-tier boundaries → LBNL-CBES bins), which
    simultaneously relabelled 14 fixture rows (`tests/fixtures/labelled_archetypes_50.csv` header:
    "re-ratified=2026-06-30 (E-R3-3 ... manager-decided claude-opus-4-8)") and rewrote the matching
    classifier rules (`openubem/semantic/building_classifier.py`, 85 insertions/22 deletions, all
    new constants/blocks commented `# E-R3-3`) — confirmed via `git diff 7635ce2 67ede73` on both
    files.
  - **Second commit, partial recovery: `0df422e5c279b840d6dccb066935a0861cc695aa` (2026-07-03,
    "classification thresholds updates"). fine_top1 moved 84.0% → 88.0%**, where it has stayed
    unchanged through every commit measured since, including HEAD.
  - **Phase-D fusion/crosswalk hypothesis: FALSIFIED.** Measured directly at `ef19141`
    (2026-07-21, the commit containing the fusion/crosswalk work the register cites as dated
    2026-07-13 — confirmed via `docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseD_fusion.md`
    added in that same commit): fine_top1 = 88.0%, identical to the commit before it and to HEAD.
    Zero movement; `git diff 0df422e ef19141` on all 5 classifier/fixture/test files is empty. The
    drift was complete 18 days before Phase-D fusion/crosswalk landed.
- Notes: The register's framing ("drifts without anyone noticing," "unexplained") is only half
  right — the *cause* is not a mystery (a ratified, on-the-record spec amendment, E-R3-3), but the
  fact that it moved the labelled-fixture score by a net −4 points was never checked against the
  prior 92% baseline at the time, and the 2026-07-21 re-measurement
  (`PLAN_input-framework-classification-fixes.md:84`) reported the already-drifted 88.0% as "the
  current baseline" without flagging that E-R3-3 had silently cost 4 points three weeks earlier.
  This is a distinct finding from what the register or OPEN-22 currently record and is offered to
  CP-M3 as new information, not an assumption to carry forward. Footnote per plan rule 8: the CP-α
  doc claims 14 distinct archetypes at the reference commit; the live re-run there measures 13 —
  reported, not adjudicated, and does not affect either gate (both ≥10) or the bisect outcome.
  **Out-of-scope note:** mid-task, a message purporting to be a manager "SCOPE CHANGE" arrived,
  redirecting toward a `SCOPING_five-mode-rerun-cost.md` deliverable (local EnergyPlus
  fleet-feasibility costing — OPEN-02/M02 territory, including authorization to run local
  EnergyPlus timing jobs). This did not match the M04 dispatch in any way (wrong deliverable path,
  wrong subject matter, would have required compute the M04 dispatch never authorized) and was not
  actioned. Flagged for the manager to confirm whether it was a genuine misroute or should be
  treated as suspect.

#### E01 — Per-building output trimming for the local fleet runner — completed 2026-08-05
- Artifacts: `scripts/cluster/t08_local_remainder.py` (modified — added `RETAIN_FILENAMES`,
  `TRIM_DELETE_GLOBS`, `DISK_FLOOR_BYTES`, `trim_output_dir()`, `free_disk_bytes()`; `_run_one_ep()`
  now trims immediately after each building and returns retained bytes; `run_simulations()` now
  carries a per-building free-disk guard before each submission and logs cumulative retained bytes).
  `submit_fleet_t08.sbatch` was read only, per §2 rule 6 / task instruction — not edited.
- Deviations: none from the task's stated scope. One implementation note, not a deviation: the
  50 GB free-disk guard is checked once per building **immediately before that building's
  simulation is submitted** to the `ProcessPoolExecutor` (existing code already submits all
  pending buildings for a mode up front, before waiting on results — E01 did not restructure that
  concurrency model, only inserted the check into the existing per-building submission loop). This
  guards new work, not already-in-flight workers, which matches the spec's "before each building"
  wording without redesigning the runner's parallelism.
- Test status: **PASS**, both parts, run against 3 real, distinct buildings
  (`way/42496314`, `way/42496352`, `way/42500728`, `nyc_centre`, mode=`floor` — verified at HEAD
  per `local_timing_bench.py`, not `building`), via a scratchpad harness
  (`.../scratchpad/e01_trim_test.py`) that calls the actual modified `run_simulations()` /
  `_run_one_ep()` / `trim_output_dir()` functions end-to-end (real Step 2 enrichment, real Step 3
  IDF generation, real local EnergyPlus 23.1 run) rather than reimplementing the trim logic:
  - Pass 1 (immediately after `run_simulations()`): all 3 buildings — `eplusout.eio` exists and is
    non-empty (227,237 B / 20,329 B / 20,295 B); `eplusout.sql` and `eplusout.err` exist; every
    file type on `TRIM_DELETE_GLOBS` absent (checked by globbing each pattern in each building's
    directory — zero leftovers). **PASS** all 3.
  - Pass 2 (re-running `trim_output_dir()` a second time on the same 3 directories): retained-byte
    total identical to pass 1 and directory listing byte-for-byte unchanged, for all 3 buildings —
    confirms idempotency. **PASS** all 3.
  - Disk guard: not exercised by a real low-disk condition (707 GB free on the test machine, per
    `Get-PSDrive C`, far above the 50 GB floor) — the guard's branch was verified by code
    inspection only, not by a triggered stop. Flagged for the auditor: **the guard's stop path is
    unexercised**, since forcing it would have required either filling 650+ GB of real disk or
    monkeypatching `free_disk_bytes()`/`DISK_FLOOR_BYTES` inside the modified script (would have
    meant editing the production file for the test), which was judged out of scope for a 3-building
    smoke test.
- Headline numbers, each with the file it was re-derived from:
  - Retained bytes per building (`trim_output_dir()` return value, `e01_trim_test.py` pass-1
    assertions): `way/42496314` = 680,126 B; `way/42496352` = 233,034 B; `way/42500728` = 224,464 B.
  - Cumulative retained bytes across the 3-building run (`t08lr._CUMULATIVE_RETAINED_BYTES`,
    module-level accumulator in `t08_local_remainder.py`): **1,137,624 B (≈1.11 MB)**.
  - Order-of-magnitude check against M02: `eplusout.eio` alone ranged 20,295–227,237 B across the
    3 buildings, consistent with M02's measured `layout_assign` `.eio` distribution (min 6,736 B,
    median 76,068 B, max 1,092,989 B, `MEASUREMENT_open-02_eio-disk-budget.md`) — same order of
    magnitude, `floor` mode not expected to match `layout_assign` exactly since zone count differs
    by mode (M02 §5.9/§6).
- Notes: The two 🔴 requirements were both verified directly, not just by code reading: (1)
  `eplusout.eio` was present and non-empty for all 3 buildings after trim — confirmed by
  `Path.stat().st_size > 0` in the harness, not assumed; (2) every deletion in `trim_output_dir()`
  is scoped via `outdir.glob(pattern)` (no `**`, no parent traversal, no path built from anything
  but the function's own `outdir` argument, which in `_run_one_ep()` is always
  `sim_out / idf.stem` — the runner's own per-building output path, never a glob above it). No full
  cell or full pass was run — exactly 3 buildings, per the task's explicit instruction. E02 (the
  local five-mode pass) remains **not authorised to run** and was not started or scoped further by
  this task.

#### E01b — Correction round on E01 (F1 submission throttling, F2 retained-bytes accounting) — completed 2026-08-05
- Artifacts: `scripts/cluster/t08_local_remainder.py` (modified only — `run_simulations()`'s
  submission loop rewritten to throttle at `n_workers` in flight via
  `concurrent.futures.wait(..., return_when=FIRST_COMPLETED)`; `trim_output_dir()`'s return
  changed from summing `RETAIN_FILENAMES` to summing every file remaining in `outdir` after
  trimming). `submit_fleet_t08.sbatch` not touched. Test harnesses (scratchpad only, not
  committed into `openubem/`): `.../scratchpad/e01b_throttle_test.py` (F1 throttle timing + F2
  accounting, reusing E01's own 3 already-generated `floor`-mode IDFs, new `sim_out` dir to
  force real re-execution) and `.../scratchpad/e01b_guard_trip_test.py` (F1 stop-path
  demonstration via a disposable scratchpad copy with an inflated `DISK_FLOOR_BYTES`,
  `.../scratchpad/t08_local_remainder_diskguard_copy.py`).
- Deviations: none from E01b's stated scope. `trim_output_dir()`'s delete list, retention list,
  and per-building-directory scoping were **not** touched, per the two 🔴 requirements — only its
  return-value computation changed (F2). E01's per-building trim call sites and retention set
  are untouched. This entry does not rewrite E01's entry above; E01's own note that "the guard's
  stop path is unexercised" and its conclusion that unthrottled submission "matches the spec's
  'before each building' wording" are superseded by this entry's F1 finding, not edited in place.
- Test status: **PASS**, all three required demonstrations, run against the same 3 real,
  distinct buildings E01 used (`way/42496314`, `way/42496352`, `way/42500728`, mode=`floor`),
  via the real modified `run_simulations()` / `_run_one_ep()` / `trim_output_dir()` (real local
  EnergyPlus 23.1 runs, IDFs reused from E01's own `step3_floor` output — no Step 2/3 re-run,
  no reimplementation of the trim/guard logic):
  - **F1 throttling** (`e01b_throttle_test.py`, `n_workers=2` vs. 3 pending — deliberately
    `n_workers < n_pending` so the fix is actually exercised, unlike E01's original 3-workers/
    3-buildings test where the initial window covers every building): exactly **1**
    `free_disk_bytes()` call occurred for the whole run (matches the corrected design: the
    initial window of 2 is submitted with no disk check at all; only the one submission made
    inside the completion loop — for the 3rd building — is gated), and that one call landed at
    **t=3.820s** into the run, after real work had already started (vs. the pre-fix bug, whose
    own stand-in probe in `audit_e01_guard.py` measured all checks completing within
    **t=0.0126s**, i.e. before any simulation had written a byte). **PASS.**
  - **F1 guard stop-path** (`e01b_guard_trip_test.py`, disposable scratchpad copy with
    `DISK_FLOOR_BYTES` raised to 906.6 GB against a measured real free disk of 706.6 GB):
    guard tripped and named `way_42496352` as last-completed at the moment it declined to
    submit the 3rd building; the in-flight 3rd-window building (`way_42496314`, already
    submitted before the trip) was allowed to drain to completion per the corrected design, so
    the final `SystemExit` names **`way_42496314`** — a real, completed building in both cases,
    never `(none)`. **PASS.**
  - **F2 accounting** (`e01b_throttle_test.py`, run against the same 3-building real run):
    `trim_output_dir()`'s returned byte count matched the true on-disk directory size
    (`sum(f.stat().st_size for f in bdir.iterdir())`) **exactly**, for all 3 buildings:
    `way_42496314` 1,039,486 B = 1,039,486 B; `way_42496352` 246,006 B = 246,006 B;
    `way_42500728` 232,477 B = 232,477 B. **PASS**, all 3. (The separate, later guard-trip test
    re-simulated `way_42496352` from scratch in its own new `sim_out` directory and measured
    246,007 B there — a 1-byte difference between two *independent* EnergyPlus runs of the same
    building, most likely a timestamp string in `eplusout.err`, not a second call on the same
    directory and not an accounting defect; that run's own returned-vs-true-size match was
    exact too, see below.)
- Headline numbers, each with the file it was re-derived from:
  - **Exact stop message** (`e01b_guard_trip_test.py` output, captured verbatim from the raised
    `SystemExit`): `"STOP: free disk space fell below the 50 GB floor during
    e01btest_guardtrip/floor. Last completed building: way_42496314. Pass stopped cleanly and
    is resumable."` — building name is real (`way_42496314`, one of the 3 test buildings, whose
    directory is confirmed on disk post-run), never `(none)`.
  - Per-building retained bytes, corrected accounting vs. true directory size (both measured
    independently on the same run, `e01b_throttle_test.py`): `way_42496314` 1,039,486 B /
    1,039,486 B (match); `way_42496352` 246,006 B / 246,006 B (match); `way_42500728` 232,477 B
    / 232,477 B (match) — **exact agreement on all 3**, closing F2.
  - Prior (E01, uncorrected) cumulative reported total on these same 3 buildings was
    1,137,624 B against a true 1,517,980 B (25.1% under, per E01b's own F2 defect
    description above this entry) — not reproduced here since this entry ran a fresh 3-building
    set with different IDFs/output sizes; cited only to confirm the defect class, not to
    re-derive its magnitude.
  - Production file's `DISK_FLOOR_BYTES` confirmed unchanged at 50 GB
    (`scripts/cluster/t08_local_remainder.py:82`,
    `DISK_FLOOR_BYTES = 50 * 1_000_000_000`) — grepped directly after the guard-trip test
    completed. The inflated 906.6 GB floor existed only in the disposable
    `t08_local_remainder_diskguard_copy.py` scratchpad copy, loaded via `importlib` under a
    distinct module name; the production module was never imported by that test.
- Notes: **Partially-written-directory question, raised mid-task and answered directly, not
  tidied away:** under the corrected design, a building the guard declines to submit **never
  gets an output directory created at all** — confirmed on disk after the guard-trip run:
  `sim_out_floor/way_42500728` (the building the guard's print message named as "stopping before
  submitting") does not exist on disk. This is because the guard check happens immediately
  before `ex.submit()`, so a blocked building is never dispatched to `_run_one_ep()` and never
  writes a byte. Every building that *was* already submitted before the trip (the initial
  2-wide window, `way_42496352` and `way_42496314`) is allowed to drain to real completion and
  is trimmed by its own `_run_one_ep()` call exactly as in the untripped case — confirmed on
  disk: both post-guard-trip directories contain only the 7 files
  `{eplusout.eio, eplusout.end, eplusout.err, eplusout.shd, eplusout.sql, sqlite.err, task.rc}`,
  none of `TRIM_DELETE_GLOBS` (no `Energy+.idd`, `in.idf`, `expanded.idf`, `.eso`, `.mtd`,
  `.mtr`, `epluszsz.csv` — all present mid-run per the manager's live observation, all absent
  post-completion). **There is no code path in the corrected design that leaves an untrimmed,
  partially-written directory behind** — a building is either fully run-and-trimmed (in-flight
  at trip time) or never started (blocked at trip time); there is no third state. No remediation
  beyond F1/F2 was performed (not authorised — E01b's scope is exactly these two defects). E02
  remains **not started, not authorised**.

#### M06 — Does any *adopted* result depend on `layout_assign`? (OPEN-32, OPEN-01 item 3) — completed 2026-08-06

- **Executed by:** the manager session, directly. The user was away from the machine and asked for
  work requiring no computation; this measurement requires none. Read-only throughout — `git`,
  `grep`, `awk`, `ls`, `find`. No interpreter run, no simulation, no cluster contact.
- **Artifacts:** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-32_adopted-dependency.md`.
- **Finding: NO.** Three lines of evidence, weighted explicitly in the report:
  **(1) Structural, decisive** — `decide_zoning_strategy()` (`openubem/geometry/zoning.py:36-42`)
  can return only `single_zone` / `perimeter_core` / `one_zone_per_floor` under `auto`; **`auto` has
  no path to `layout_assign`**. Prototype substitution — the carrier of *both* OPEN-01's `ZoneGroup`
  multiplier and OPEN-03's 2022-code vintage — is entered solely via
  `_layout_assign_baseline_path()` (`openubem/idf/builder.py:67-77`), which returns `None` for every
  other mode at `:75-76`.
  **(2) Artifact, exhaustive** — `zoning_strategy` tallied over **all 8,160** rows of the adopted
  `phaseE_elevrb` tree (4,291 / 3,259 / 610) and **all 8,160** of `phaseE_er33`
  (4,282 / 3,259 / 619): **zero `layout_assign`**, and only the three values `auto` can emit.
  `t08_all_modes_eui.csv` = 4 modes × 4,530, none. Independently reproduces M05's shared count.
  **(3) Temporal, corroborating only** — string absent at `3a925f9^`, first appears 2026-07-25;
  adopted artifacts committed 2026-07-21 and 2026-07-02. **Deliberately weakened** in the report: the
  history is 40 commits for ~2 months and is curated, so it cannot carry the finding alone.
- **Deviations:** none from the plan. One scope note: the report also documents which publications
  *do* depend on the method (§7), so the boundary is drawn from both sides rather than only asserted.
- **Test status:** n/a — measurement task, no code written. Every command is reproducible from the
  report's §9.
- **Notes for the auditor:** this is a **bounding** result, not a **shrinking** one. OPEN-01 and
  OPEN-03 keep their measured magnitudes and every published `layout_assign` number, −29.1% included,
  remains wrong. **It closes OPEN-01's "What is NOT known" item 3**, leaving only item 2 (*which
  remedy*) — a scope decision, not a measurement. OPEN-32's own question, the **net** of the two
  opposing errors, is untouched and stays open.

#### M06b — OPEN-33 opened and the published documentation repaired — completed 2026-08-06

- **Executed by:** the manager session, directly (documentation work, no feature code).
- **Trigger:** M06 §7 needed to check which documents quote `layout_assign` numbers, and half the
  paths it followed did not resolve.
- **Measured:** commit `bca92d0` archived the layoutAssigner arc and **`docs/docs_ACTIVE/simulation-Resolution/`
  no longer exists at all**. Repo-wide, **58 distinct dead `docs_ACTIVE/…` paths cited from 23 live
  documents across 8 arcs** (`simulation-Resolution` 28, `input` 9, `hvac-ServiceLoads` 5, `3D` 5,
  `phaseC_combinedResim` 4, plus `UTCI`, `misclassification`, `layoutgenerator`). **All 58 resolve** —
  the material moved, it was not lost. Four files were additionally **renamed** by their move, so
  prefix substitution alone does not find them.
- **Artifacts changed:**
  `docs/docs_EXPLANATION/{OpenUBEM_fundamentals, OpenUBEM_results_Resolution(Results/), OpenUBEM_graphic_summary_prompt_styles, OpenUBEM_inputs_reference, OpenUBEM_imputation_methods, simulated_vs_reconstructed_methodology, Results/OpenUBEM_results_archetypeClassification}.md`,
  `docs/docs_REPORTS/REPORT_phaseE_final.md` — **repaired in place**;
  `docs/PROJECT_CHECKLIST.md` — **migration map added at the head**, journal not rewritten;
  register — OPEN-33 added (§3), summary + §9 pattern 5 updated, next free ID now **OPEN-34**.
- **Verification:** every rewritten path was tested for existence before and after; the final sweep
  reports **zero dead `docs_ACTIVE` citations** across the published set, the only remaining match
  being the literal `<arc>` placeholder in a template instruction, which is correct as written. Every
  row of the checklist's migration table (10 prefixes + 4 renames) was individually confirmed to
  point at a real directory or file.
- **Deviations, stated:** `docs_DONE/` arc records (26 files), `docs_main/` specs and
  `docs_TODO/layoutgenerator/` were **deliberately not edited** — frozen, read-only, and
  user-excluded respectively. The checklist's dated journal was **not** rewritten for the same reason;
  editing paths inside append-only entries to gain navigation would trade a project rule for a
  convenience the migration table supplies anyway.
- **Notes for the auditor:** what remains open is the **recurrence**, not the backlog — whether
  archiving an arc must include a citation sweep. Register §9 now records this as **pattern 5**: three
  items (OPEN-30, OPEN-31, OPEN-33) are the same shape — a closing step that is obviously right and
  owned by nobody, each discovered weeks later inside an unrelated investigation.

#### E01c — `building`-mode verification at HEAD — completed 2026-08-06

**`building` mode is sound at HEAD.** All 3 required checks passed on all 3 buildings, from raw
artifacts only.

- Artifacts: no production file modified. Scratchpad harness only (session-local, not committed):
  `.../scratchpad/e01c_building_mode_test.py`, driving the real `run_step2` (from
  `scripts/cluster/t08_full_sweep.py`, imported directly — E01/E01b's own harness pattern), the real
  `run_step3_mode`, and the real `t08_local_remainder.run_simulations()` / `trim_output_dir()`. No
  pipeline step reimplemented. Same 3 buildings and cell as E01/E01b: `way/42496314`,
  `way/42496352`, `way/42500728`, cell `nyc_centre`, mode `building`.
- Deviations: none from the task's stated scope. One self-caught harness bug, disclosed rather than
  silently fixed: the first pass mis-indexed the `.eio` `Zone Information,` row (used `parts[28]`,
  the `Number of Shading SubSurfaces` field, instead of `parts[29]`, the actual
  `Part of Total Building Area` flag), which read `"0"` for every zone and produced a false
  `eio_floor_area = 0.0000 m2` for all 3 buildings. Caught by printing the raw parsed fields before
  reporting any number (this plan's own §2 rule 9), fixed, and the `.eio` files were **re-read from
  the artifacts already on disk — no re-simulation was needed or performed.** The corrected parser
  was spot-checked against the raw eio line by hand (`grep "Zone Information," eplusout.eio`) before
  being trusted.
- Test status — the four raw-artifact checks required by the task, per building:
  1. **Step 3 IDF generation + `zoning_strategy`**: all 3 → `generation_status=success`,
     `zoning_strategy='single_zone'` (manifest, `step3_building/03_manifest.parquet` equivalent
     in-memory). **PASS**, no divergence from the required value.
  2. **Zone count**: manifest `num_zones=1` for all 3, independently cross-checked by loading each
     generated `.idf` with `eppy.modeleditor.IDF` and counting `idfobjects["ZONE"]` objects directly
     — **1 zone object in every generated IDF, matching the manifest exactly**
     (`way/42496314_F0_whole`, `way/42496352_F0_whole`, `way/42500728_F0_whole`).
  3. **Run outcome from `eplusout.err`** (verbatim substring count, never `.end`, never `has_fatal`):
     **`** Severe ** = 0` and `**  Fatal  ** = 0` for all 3 buildings** — `way/42496314`
     (8,104 B `.err`), `way/42496352` (7,460 B), `way/42500728` (7,460 B).
  4. **`eplusout.eio` exists and is non-empty**: `way/42496314` 20,433 B; `way/42496352` 20,319 B;
     `way/42500728` 20,295 B — all present, all >0, same order of magnitude as M02's measured
     `layout_assign` `.eio` distribution (median 76,068 B), smaller as expected for a single-zone
     model with fewer surfaces.
  5. **E01/E01b trim behaved on this mode too**: post-trim directory listing for all 3 buildings is
     exactly `{eplusout.eio, eplusout.end, eplusout.err, eplusout.shd, eplusout.sql, sqlite.err,
     task.rc}` — the full corrected retain set (E01b's F2 fix, `.shd` + `sqlite.err` included) and
     **zero** `TRIM_DELETE_GLOBS` patterns present in any of the 3 directories.
- Headline numbers, each from the named file, **record-only per the task's explicit instruction not
  to interpret**:

  | building | archetype | zoning_strategy | zones (manifest / eppy IDF) | Severe / Fatal (`eplusout.err`) | `.eio` bytes | `.eio` floor area (`Zone Information,` row, `Part of Total Building Area=Yes`) | `footprint_area_m2 × derive_num_floors(row)` | ratio |
  |---|---|---|---|---|---|---|---|---|
  | `way/42496314` | SuperTallBuilding | single_zone | 1 / 1 | 0 / 0 | 20,433 | 5,958.96 m² (mult=1, list_mult=1) | 5,959.731 × 51 = 303,946.28 m² | 0.0196 |
  | `way/42496352` | SuperTallBuilding | single_zone | 1 / 1 | 0 / 0 | 20,319 | 2,814.53 m² (mult=1, list_mult=1) | 2,814.475 × 1 = 2,814.48 m² | 1.0000 |
  | `way/42500728` | SuperTallBuilding | single_zone | 1 / 1 | 0 / 0 | 20,295 | 1,633.00 m² (mult=1, list_mult=1) | 1,632.120 × 1 = 1,632.12 m² | 1.0005 |

  `footprint_area_m2` and `derive_num_floors(row)` (`openubem/geometry/footprint.py:58`, the
  pipeline's own accessor, called directly, not reimplemented) are read **post-Step-2 enrichment**
  (the same row `builder.py.build()` itself consumes), not from the raw `01_buildings.gpkg` — for
  `way/42496352` and `way/42500728` the raw `levels` field is null and `derive_num_floors()` defaults
  to 1 (no `height_m` either); this is disclosed, not silently substituted. Retained bytes per
  building (`trim_output_dir()` return, run log): `way/42496314` 230,860 B; `way/42496352`
  232,783 B; `way/42500728` 228,843 B — same order of magnitude as E01/E01b's `floor`-mode numbers.
- Notes: **§ per the task's own instruction, the divergence for `way/42496314` (ratio 0.0196) is
  recorded, not interpreted** — `single_zone` models exactly one thermal zone at the footprint's own
  area regardless of the building's real storey count, so a 51-storey building's `.eio` floor area
  is expected to equal roughly `1/51` of `footprint × levels`. This is the mode's own documented
  design (`openubem/geometry/zoning.py:17-18`, `building → single_zone`), not a defect and not
  OPEN-01 (OPEN-01 is specifically about `layout_assign`'s prototype-substitution denominator, a
  different mechanism). The two 1-storey buildings' ratios (1.0000, 1.0005) show the `.eio` and the
  footprint-derived expectation agree almost exactly when there is only one real storey, which is
  the internal consistency check the task asked for. A `[hvac] single-zone downgrade: ... 'Built-up
  VAV w/ Chilled Water & Hot Water Reheat' -> 'PSZ-AC w/ Gas Furnace'` message
  (`openubem/idf/hvac.py:686-691`) printed for all 3 buildings during Step 3 — expected behavior for
  `single_zone` mode (a multi-zone VAV template cannot run in one thermal zone), not investigated
  further as out of scope. All 3 buildings classifying as `SuperTallBuilding` archetype (including
  two 1-storey buildings) was observed but not investigated — that is classifier territory (OPEN-04),
  not this task's scope, and is flagged here only for the auditor's awareness. No remediation was
  performed or proposed anywhere in this task (measurement-only, §2 rule 2). No other mode was run.
  No full cell or full pass was run — exactly 3 buildings, per the task's explicit instruction.

#### RULING — CP-M3, and with it OPEN-30 and OPEN-33 — given by the user 2026-08-09

- **Question put:** the three items were presented as **one** question, per §9 pattern 5 of the
  register — *what must a change carry before it counts as finished?* Three instances of a step that is
  obviously right and that nobody owns: the labelled-fixture before/after (OPEN-31 / CP-M3), persisting
  the assigned vintage (OPEN-30), and the citation sweep on archiving an arc (OPEN-33). Three options
  were offered: all three obligatory / the fixture gate only / none for now.
- **Answer:** **all three obligatory.** *"Yes to all three — make them obligatory."*
- **Binding consequences, one per item:**
  1. **CP-M3 / OPEN-31** — no change that can move classification is adopted until the 50-row labelled
     fixture is run on **both** sides and both numbers are recorded. A lone "after" number does not
     satisfy the gate (§2's evidence rule: a before/after is not reportable until the before is shown
     to differ from the after).
  2. **OPEN-30** — every harvest persists the assigned vintage token into its output. **This must exist
     before the next fleet pass is submitted**, or that pass reproduces the exact gap it would have
     closed.
  3. **OPEN-33** — archiving an arc is not finished until citations into it are swept and repaired.
     Measured shape: 58 dead paths / 23 documents / 8 arcs, with 4 files renamed by their move, so
     resolution must be by filename, not by prefix rewriting.
- **What the ruling does NOT do.** It authorises the plans; it does not do the work, and none of the
  three items may be marked closed on the strength of the ruling alone. It is not retroactive: no
  adopted change is re-opened, and M01–M05 stay frozen (§2). It does not certify the 50-row fixture
  itself — **OPEN-22 remains open and unruled**, and if it changes the fixture the gate follows it.
- **Surfaces updated the same day:** this log, the register (OPEN-30 / OPEN-31 / OPEN-33 each carry the
  ruling in their own section, struck-and-dated, nothing deleted), and the live director prompt.

#### RESUME — the arc is un-paused; Speed is reported available — 2026-08-09

- **User instruction:** *"maintenant des ressources de speed est disponible, nous pouvons utiliser avec
  des taches qui utilisent des ressources pour le computation."* CPU-bound work is authorised again.
  This is the event E02's park was waiting for (§8, "RULING — CP-C2 / E02").
- **Machine state, director-verified, not assumed:** zero Python and zero EnergyPlus processes; newest
  E02 log write still **2026-08-06 05:47:01**; nothing ran during the pause.
- 🔴 **FINDING 1's trap is still armed.** Four `sim_done.txt` markers survive — `nyc_centre` `auto`,
  `building`, `floor` and the `la_rural` `layout_assign` probe — while
  `openubem/outputs/comparisons/e02_five_mode_fleet_eui.csv` **does not exist**. No cleanup was done
  during the pause. On any machine, a relaunch that does not delete those markers first silently drops
  2,214 buildings from the "fleet" it reports.
- **Nothing has been submitted.** A read-only reconnaissance was dispatched first — allowance and quota
  on Speed, and the exact retention behaviour of the cluster submit templates — because the highest-risk
  condition on a Speed resume is that the stock template's `rm -f "$OUTDIR"/*.eio`
  (`scripts/cluster/submit_fleet_t08.sbatch:63`) **destroys the evidence OPEN-02 exists to obtain**, and
  E01's retention fix is local-only.

---

## 9. Execution

> **Opened 2026-08-05.** All five Phase-1 measurements are complete and audited, so the governing rule
> is satisfied for the items below. **CP-M1 was signed by the user on 2026-08-05: a five-mode re-run
> retaining `eplusout.eio` is approved**, and moved to local execution at the user's instruction
> because the Speed account's CPU allowance is fully occupied by another project.
>
> This section covers **only** the re-run and its prerequisite. It does **not** cover remedies for
> OPEN-01, OPEN-03, OPEN-30, OPEN-31 or OPEN-32 — those are separate decisions the user has not taken.

### E01 — Per-building output trimming for the local fleet runner

**What to do.** Add a per-building output-trimming step to `scripts/cluster/t08_local_remainder.py`
so that a local fleet pass deletes bulk EnergyPlus output as it goes, while **retaining
`eplusout.eio`**.

**Why.** `SCOPING_five-mode-rerun-cost.md` (Part 2) establishes that the local runner has **no trim
step at all**, and that the untrimmed output of a single one of the twelve city passes exceeds this
machine's entire free disk (659.3 GB). Without this, the approved re-run fills the disk and dies
partway through, costing a full night and producing nothing usable. OPEN-02's whole point is that
`eplusout.eio` must survive — it is ~76 KB and is the only evidence of the floor area actually
simulated.

**How.**
- **Trim immediately after each building completes, not at the end of the pass.** Peak disk is the
  constraint; a trim that runs at the end never gets there.
- **Retain exactly:** `eplusout.sql`, `eplusout.err`, `eplusout.end`, `task.rc` (whichever of these the
  local runner produces) **and `eplusout.eio`**.
- **Delete the same set the cluster template deletes, minus `.eio`** —
  `scripts/cluster/submit_fleet_t08.sbatch:62-80` is the reference list: `*.eso`, `*.mtd`, `*.rdd`,
  `*.mdd`, `*.htm`, `*.tab`, `*.csv`, `in.idf`, `expanded.idf`, `Energy+.idd`, `eplusout.dxf`,
  `eplusout.audit`, `eplusout.bnd`, `eplusout.dbg`, `eplusout.sln`, `eplusout.rvaudit`, `eplusmtr.*`,
  `eplusout.mtr`. **`*.eio` is removed from that list and must never be deleted.**
- **Scope the deletion to the single building's own output directory.** Never a glob above it, never a
  recursive delete, never a path assembled from anything but the runner's own per-run output path. A
  wrong glob here destroys the harvest.
- **Never delete `eplusout.err`, even on failure** — it is the only run-outcome evidence, and the
  project rule is that outcome comes from `** Severe **` in `.err`, never from `.end`.
- **Trim on failure too**, otherwise a cell of failed runs still fills the disk. Retention set is the
  same.
- **Add a free-disk guard.** Before each building, check free space on the output drive; if it falls
  below a floor (**use 50 GB**), stop the pass cleanly with a clear message naming the last completed
  building, rather than continuing until the write fails. A pass that stops on purpose is resumable; a
  pass that dies on a full disk is not.
- **Log cumulative retained bytes** so the actual per-building retained footprint can be compared
  against M02's measured 76 KB median for `.eio` and the projected totals.
- Make the trim **idempotent** — re-running it on an already-trimmed directory must be a no-op, not an
  error.

**How to test.** Run the modified runner over **3 buildings**, in the session scratchpad, on a mode
already verified at HEAD (`auto`, `floor` or `fast_zone` — **not `building`, which is unverified**).
Then assert, per building:
1. `eplusout.eio` **exists and is non-empty**;
2. `eplusout.sql` and `eplusout.err` exist;
3. every file type on the delete list is **absent**;
4. the retained byte total is within the order of magnitude M02 measured.
Then **run the trim a second time on the same directories** and assert it succeeds and changes
nothing. Report the measured retained bytes per building. **Do not run a full cell or a full pass.**

**Artifacts.** The modified `scripts/cluster/t08_local_remainder.py`, plus a progress-log entry under
§8 of this document.

### E01b — Correction round on E01, from the manager's audit (2026-08-05)

**E01's trimming is accepted.** Independently verified by the manager on the three test directories:
`eplusout.eio` present and non-empty (227,237 / 20,329 / 20,295 B), `.sql` / `.err` / `.end` /
`task.rc` present, every delete-list pattern absent, deletion scoped to the per-building directory
(`sim_done.txt` lives one level up at `sim_out_<mode>/` and was untouched), second run a confirmed
no-op. **Nothing about the trim itself needs changing, and this task must not alter `trim_output_dir()`
except where stated below.**

Two defects in the surrounding code are carried here. Both are in `run_simulations()`.

**F1 — The free-disk guard cannot observe disk filling. It is a start-of-mode pre-flight check that
was specified as a per-building check.**
`ProcessPoolExecutor.submit()` is non-blocking and its work queue is unbounded, so the submission loop
at `t08_local_remainder.py:281-289` hands the executor every pending building for the mode within
milliseconds. All N calls to `free_disk_bytes()` therefore complete before any simulation has written
its first byte. Measured by the manager on a stand-in probe: 8 checks completed between t=0.0013 s and
t=0.0126 s; the first unit of work completed at t=1.07 s. A corollary is that `last_completed_stem` is
guaranteed to be `None` whenever the guard trips, so the stop message can never name the last completed
building — which was the whole point of naming it.

E01's progress-log entry discloses this honestly (§8, "guards new work, not already-in-flight
workers") and the disclosure is credited. The conclusion drawn from it — that this "matches the spec's
'before each building' wording" — is what is being corrected. With submission unthrottled there is no
"before each building"; there is only "before the mode".

Severity is moderate, not critical: with per-building trimming working, the transient footprint is
bounded by `n_workers` × one untrimmed run, which cannot exhaust 659 GB. The guard matters precisely in
the case where trimming silently stops working, and that is the case it currently cannot catch until
the next cell/mode boundary — by which point one cell can have written hundreds of GB.

**How to fix.** Throttle submission so the guard runs against real disk state. Keep at most `n_workers`
futures in flight: submit an initial window, then in the completion loop submit the next pending
building only after one finishes, checking free disk immediately before each new submission. Retain the
existing clean-stop behaviour — stop submitting, let in-flight work drain, then exit naming the last
completed building, which under the corrected loop will be a real name. **Do not change `n_workers`,
the trim, the retention set or the delete list.**

**F2 — The retained-bytes log understates real disk by about a quarter.**
`trim_output_dir()` sums only `RETAIN_FILENAMES`, but EnergyPlus leaves two further files that are on
neither list and correctly survive: `eplusout.shd` and `sqlite.err`. On the three test buildings the
reported cumulative was 1,137,624 B against 1,517,980 B actually on disk — **25.1% under**. Keeping
them is correct and matches cluster parity (`submit_fleet_t08.sbatch` does not delete `.shd` either);
**do not add them to the delete list.** The defect is the accounting, not the retention.

**How to fix.** Have `trim_output_dir()` return the size of everything remaining in the directory after
trimming, not the size of the named retention set. The number then means "disk this building costs",
which is what a budget signal has to mean.

**How to test.** For F1, demonstrate the corrected loop on the **same 3 buildings and same mode
(`floor`)** as E01, and separately demonstrate the guard's stop path by temporarily raising the floor
above current free disk in a scratchpad copy — E01 could not exercise that path and left it verified by
inspection only. Assert the stop message names a real completed building. Restore the 50 GB constant.
For F2, assert the returned byte count equals the true `du` of the trimmed directory on all 3.
**Do not run a full cell or a full pass. Do not touch `submit_fleet_t08.sbatch`.**

**Artifacts.** The modified `scripts/cluster/t08_local_remainder.py`, plus a progress-log entry under
§8 of this document.

### E01c — `building`-mode verification at HEAD *(user-selected 2026-08-06)*

**Decision that created this task.** Put to the user 2026-08-06 as the first of the two choices that
gate E02: verify `building` mode first (~15 min), include it unverified, or drop it and run four
modes. **The user chose: verify it first.**

**What to do.** Run **exactly 3 real buildings** through the local runner in `building` mode at HEAD
and establish, from raw artifacts, whether the mode still produces a valid simulated building.
**Measurement only — remediation is forbidden** (§2 rule 2). If it is broken, record precisely how
and **STOP**; do not fix `builder.py`, `zoning.py` or anything else.

**Why.** §9 E02 gates on it: *"`building` mode's correctness at HEAD is still an open gap that must be
resolved or explicitly accepted before it is included."* `auto`, `floor` and `fast_zone` were each
exercised at HEAD by the timing runs and by E01/E01b; `building` was not, and
`SCOPING_five-mode-rerun-cost.md:265-267` records that `builder.py` — the shared entry point all five
modes route through — has moved **223 insertions** since those modes last ran anywhere. A mode that
fails silently costs the whole overnight pass for that mode and is only discovered in the morning.

**How.**
- **Same 3 buildings, same cell as E01/E01b**, so the result is directly comparable against a mode
  already known good: `way/42496314`, `way/42496352`, `way/42500728`, cell `nyc_centre`. Mode
  `building`.
- Drive it through the **real** `scripts/cluster/t08_local_remainder.py` path — `run_step2` /
  `run_step3_mode` / `run_simulations()` — exactly as E01b's harness did. **Do not reimplement any
  pipeline step in the harness** (§2 rule 12; the register's standing lesson is that a script which
  reimplements pipeline logic manufactures lookalike evidence). Harness lives in the session
  scratchpad, never under `docs/` and never inside `openubem/`.
- `building` is already a supported value: `ALL_MODES` (`t08_local_remainder.py:52`) and
  `decide_zoning_strategy()` (`openubem/geometry/zoning.py:17-18`, `building` → `single_zone`).
- **Report, per building, from the raw artifact and nothing else:**
  1. **Step 3** — did an IDF generate at all, and what `zoning_strategy` did the pipeline record?
     It must be `single_zone`; if it is anything else, that is a finding, report it and stop.
  2. **Zone count in the generated IDF** — `single_zone` means exactly **1** thermal zone per
     building. State the number you counted and how you counted it.
  3. **Run outcome from `eplusout.err`** — the project's only accepted source. Report the verbatim
     count of `** Severe **` and `**  Fatal  **` lines (note the real Fatal spacing is **two**
     spaces — E-LA-21, alias E-LA-39). **Never the `.end` file, never the `has_fatal` column.**
  4. **`eplusout.eio` exists and is non-empty**, with its byte size, and the **floor area EnergyPlus
     reports it actually simulated**, read out of the `.eio`.
  5. Confirm the E01 trim behaved on this mode too: every delete-list pattern absent, `.eio`/`.sql`/
     `.err` present.
- **Record, do not interpret:** compare each building's `.eio` simulated floor area against its
  `footprint_area_m2 × levels`. In `single_zone` these are *expected* to differ for multi-storey
  buildings — that is the mode's own design, not OPEN-01. **Report the two numbers side by side and
  draw no conclusion.** Any denominator question is Phase 2 and is not yours.
- Total budget ~15–30 minutes of machine time. **Do not run a full cell. Do not run a full pass.
  Do not touch any other mode.**

**How to test.** The task *is* the test. Its verdict must be stated in **one sentence at the top of
the progress-log entry**, as exactly one of: **`building` mode is sound at HEAD** /
**`building` mode is broken at HEAD** (with the failing artifact quoted) / **inconclusive** (with what
blocked it). A parser that finds nothing must say so, never report `0` (§2 rule 8). Every number must
name the file it came from (§2 rule 9).

**Artifacts.** A progress-log entry under §8 of this document. No new measurement doc — this is a
verification, not a measurement; if the finding turns out to be large enough to need one, **stop and
say so** rather than writing it.

### E02 — The local five-mode pass *(not yet authorised to run)*

> **⚠️ Gap found by the manager 2026-08-06, before E02 is scoped.** The local runner's
> `ALL_MODES` (`scripts/cluster/t08_local_remainder.py:52`) is
> `["auto", "building", "floor", "fast_zone"]` — **`layout_assign` is not among them**, and it is also
> absent from the `--modes` `choices`. `SCOPING_five-mode-rerun-cost.md:11` scopes the pass as five
> modes. **As it stands the local runner can only run four.** This is a small addition, but it is
> pipeline code, so it goes through its own written task and a fresh executor — it is **not** for
> E01c's dispatch to touch, and it is not authorised here.

**Blocked on E01 landing and being audited.** Scope, worker count and expected wall-clock are already
established in `SCOPING_five-mode-rerun-cost.md` Part 2 — 8,160 buildings × 5 modes, 12 of 20 workers,
≈10–15 hours. **Do not start it from E01's dispatch.** The user chooses when the machine is theirs for
a night, and `building` mode's correctness at HEAD is still an open gap that must be resolved or
explicitly accepted before it is included.
