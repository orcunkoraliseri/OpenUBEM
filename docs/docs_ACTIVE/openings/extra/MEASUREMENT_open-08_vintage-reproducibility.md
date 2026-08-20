# MEASUREMENT — OPEN-08 vintage half: cross-generation vintage disagreement

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md`, T03.
> **Script:** `scripts/analysis/open08_vintage_reproducibility.py`
> **Output:** `openubem/outputs/comparisons/open08_vintage_reproducibility.csv` (738 rows, one per
> `osm_id`, `nyc_centre` only — see §3 for why the scope is 1 of 5 T08 cells, not all 5).
> **Date:** 2026-08-18. **Measurement only.** No production code changed, no fix proposed.

---

## 0. What this task does and does not answer

OPEN-08's register text: *"Re-running a past fleet generation at current HEAD silently diverges in
archetype and vintage for buildings with missing inputs… This is the item that quietly limits every
other item."* The archetype half was quantified 2026-08-05 (OPEN-28, 13.40% disagreement, 4,530
shared T08/T20 buildings). The vintage half was recorded as *"unquantifiable — no harvest persists a
`vintage_standard` column, see new item OPEN-30."* OPEN-30 closed 2026-08-11, demonstrating
`vintage_standard` **is** persisted — but only in the E02 manifests, a fleet generation that did not
exist when T08 or T20 ran. This task tests whether that closes the vintage half. **It does not, fully
— it partially opens it, on 1 of 5 T08 cells.** See §3.

---

## 1. Step 1 — hard gate: re-derive OPEN-30's own numbers (verbatim output)

```
=== STEP 1 -- HARD GATE: re-derive OPEN-30's own numbers ===
manifests read: 60 / 60
fleet-wide rows: 40800 (expected 40,800)
nulls in vintage_standard: 0 (expected 0)
distinct vintage_standard values: 5 (expected 5)
value counts:
vintage_standard
DOERefPre1980       38125
DOERef1980to2004     1065
90.1-2013             890
90.1-2007             610
90.1-2019             110
Name: count, dtype: int64
DOERefPre1980 share: 93.4436% (expected ~=93.44%)
GATE PASS
```

Reproduces exactly: 40,800 rows, 0 nulls, 5 distinct values, `DOERefPre1980` 93.44%. **The premise
holds — proceeding.**

**Step 1b, mode-invariance (not part of the gate, checked before relying on a single E02 mode
below):**

```
=== STEP 1b -- vintage/archetype mode-invariance check (within E02) ===
buildings where vintage_standard varies across the 5 E02 modes: 0 / 8160
buildings where archetype_id varies across the 5 E02 modes: 0 / 8160
```

Both `vintage_standard` and `archetype_id` are identical across all 5 E02 modes for every one of the
8,160 buildings. Using `step3_auto` as the E02 side below is not a scope-narrowing choice — any mode
gives the same answer.

---

## 2. Step 2 — reproduce `MEASUREMENT_open-28_harvest-generation-join.md`'s own join exactly

Re-run, not carried over:

```
=== STEP 2 -- reproduce MEASUREMENT_open-28's own T08 vs T20 join ===
rows_in_both: 4530 (expected 4,530)
t08_only: 0 (expected 0)
t20_only: 3630 (expected 3,630)
archetype agree: 3923 (86.6004%)
archetype disagree: 607 (13.3996%)  (expected 13.40%)
OPEN-28 REPRODUCTION PASS
```

Reproduces exactly (13.3996% rounds to the register's 13.40%). This is the same 4,530-row shared
population and the same join method (`pd.merge(..., on='osm_id', how='outer')`,
`t08.drop_duplicates('osm_id')`) as `extra/MEASUREMENT_open-28_harvest-generation-join.md` §1 —
**not a second, invented join.**

---

## 3. Why the vintage comparison is not on all 4,530 rows — a refuted assumption, stated plainly

`extra/MEASUREMENT_open-28_harvest-generation-join.md` §4 already established that **neither T08 nor
T20's own provenance chain** (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg`)
carries `vintage_standard` at all, and it explicitly names two other `05_results.gpkg` locations that
do — the `.../results/cases/<cell>/05_results.gpkg` tree, in both the `step1` and `validations` roots
— while warning that using either **as a stand-in for T08's or T20's own vintage** would be the
"file from a different provenance chain that looks like an answer" failure mode.

This task does not do that substitution (it never claims the `cases/` file is T08's or T20's vintage).
It instead tests whether `cases/<cell>/05_results.gpkg` can serve as an independently-provenanced
**prior-generation** vintage source, genuinely earlier than E02, to pair against E02's vintage for a
true cross-generation comparison — the same logical role T08 plays for archetype against T20.

**That test fails for 4 of the 5 T08 cells, on schema, not on data:**

```
=== STEP 3a -- does the candidate 'prior generation' vintage source cover the T08 population?
(schema check, all 5 T08 cells) ===
  la_centre: ncols=21  missing=['provenance_height_m', 'provenance_levels', 'provenance_year_built', 'vintage_standard', 'year_built']  has_vintage_standard=False
  nyc_centre: ncols=70  missing=(none)  has_vintage_standard=True
  nyc_rural: ncols=21  missing=['provenance_height_m', 'provenance_levels', 'provenance_year_built', 'vintage_standard', 'year_built']  has_vintage_standard=False
  nyc_suburban: ncols=21  missing=['provenance_height_m', 'provenance_levels', 'provenance_year_built', 'vintage_standard', 'year_built']  has_vintage_standard=False
  nyc_urban: ncols=21  missing=['provenance_height_m', 'provenance_levels', 'provenance_year_built', 'vintage_standard', 'year_built']  has_vintage_standard=False
cells with a usable prior-generation vintage_standard: ['nyc_centre'] (1 / 5)
```

`la_centre`, `nyc_rural`, `nyc_suburban` and `nyc_urban`'s `cases/<cell>/05_results.gpkg` carry a
stripped 21-column schema (no `vintage_standard`, no `year_built`, no provenance columns) — **checked
in both `docs/docs_VALIDATION/step1/...` and `docs/docs_VALIDATION/validations/...` copies, same
result in both.** Only `nyc_centre`'s copy carries the full 70-column schema with `vintage_standard`.
`git log` on that one usable file confirms it is genuinely a prior generation, not a copy of anything
downstream: `docs/docs_VALIDATION/validations/overAll/results/cases/nyc_centre/05_results.gpkg` was
last touched by commit `e063865` (2026-06-30) — the same pre-imputation-commit state
`MEASUREMENT_open-28` §3.1 already identified as T08's own archetype source state — mtime
2026-06-26, five days before T08 ran (2026-07-01) and 44 days before E02 (2026-08-09).

**Consequence, stated as the hard rules require: this is not "vintage is now fully measurable," it is
"vintage is now measurable for 738 of the 4,530 shared buildings (16.3%), on 1 of 5 T08 cells."** The
register's blocker for the other 4 cells is not stale — it still holds, just for a different reason
than before (schema absence, not column absence fleet-wide).

---

## 4. Step 3 — vintage comparison, `nyc_centre` (the 1 cell where it is measurable)

```
=== STEP 3 -- vintage comparison, restricted to ['nyc_centre'] (only cells where a prior-generation
vintage source exists) ===
prior (cases-path, ['nyc_centre']) rows: 738, duplicate osm_id: 0
current (E02 auto, ['nyc_centre']) rows: 738, duplicate osm_id: 0
shared T08/T20 population restricted to ['nyc_centre']: 738 rows
shared population (from step 2): 738
of these, missing from prior (cases-path) source: 0
of these, missing from current (E02 auto) source: 0
complete rows (present in both prior and current): 738
vintage agree: 710 (96.206%)
vintage disagree: 28 (3.794%)
[context only, NOT the reused 13.40%] cases-vs-E02 archetype disagree: 373 (50.542%)

data-poor buildings (missing levels, height_m, or year_built): 713 / 738 (96.6125%)
  data-poor: n=713, vintage disagree=28 (3.9271%)
  data-rich (not data-poor): n=25, vintage disagree=0 (0.0%)
```

**Vintage disagreement, `nyc_centre`, 738 shared buildings, prior (pre-T08, commit `e063865`) vs
current (E02, 2026-08-09): 3.79% (28/738).** ~~Beside it, on the *same rows*, the reused archetype
figure is **13.40%** (the fleet-wide, 4,530-row OPEN-28 number — not recomputed on the 738-row
subset, since re-deriving a different archetype number on a different population would defeat the
"same rows" comparability requirement). The `cases`-vs-E02 archetype figure shown above (50.54%) is
reported only as context, explicitly labelled not-the-13.40%-figure — it spans more generations
(pre-T08 → E02, not T08 → T20) and is not a substitute for the reused number.~~

🔴 **Director's correction, 2026-08-18 — the paragraph above is struck, not deleted. The measurement
is right; its comparator was wrong, and the corrected reading is the stronger result.** 13.40% is
**not** on the same rows: it is T08→T20 over 4,530 buildings, while 3.79% is pre-T08→E02 over 738
buildings — a different population *and* a different generation pair, so setting them side by side is
not a like-for-like comparison and the paragraph's own parenthesis concedes as much.

**The genuinely like-for-like number is the one this doc demotes to context: 50.54% (373/738).** It
comes from the same two files, the same 738 rows and the same generation pair as the 3.79% — which is
exactly what comparability requires. Read correctly:

| on 738 `nyc_centre` buildings, pre-T08 (`e063865`) → E02 | disagreement |
|---|---|
| **vintage** | **3.79%** (28/738) |
| **archetype** | **50.54%** (373/738) |

**Vintage is roughly thirteen times more stable than archetype across the same generation gap on the
same buildings.** That direction is the opposite of the headline this section originally carried, and
it matters for OPEN-08's disposition: the item's weight sits almost entirely in its archetype half,
even though the vintage half is non-zero and so does not vanish.

Two further consequences of the corrected framing. **(1) `nyc_centre` is not fleet-representative on
the archetype axis** — 50.54% locally against 13.40% fleet-wide (over a different generation pair, so
the gap is not purely a sampling effect) — which is an additional reason not to extrapolate the 3.79%
beyond the one cell it was measured on. **(2) The 13.40% keeps its own role unchanged**: it remains
the reused OPEN-28 baseline for T08→T20 archetype disagreement, and §2's reproduction of it is a valid
control on the join. It is simply not the comparator for the vintage number.

**Data-poor breakdown.** 713 of the 738 `nyc_centre` shared buildings (96.61%) are data-poor by the
plan's definition (`provenance_levels`, `provenance_height_m` or `provenance_year_built` ==
`OSM_MISSING`, read directly from the `cases/nyc_centre` provenance columns — not re-derived). Vintage
disagreement is **3.93% among the 713 data-poor buildings, 0.0% among the 25 data-rich ones.** The
direction matches OPEN-08's claim (data-poor buildings are where vintage diverges) but the data-rich
group is only 25 buildings — too small to call this conclusive on its own.

---

## 5. Non-vacuity control (quoted before any conclusion, as required)

```
=== Non-vacuity control ===
shared-population count (complete rows): 738
vintage: some agree (710) and some disagree (28)? YES
archetype (context check): some agree (365) and some disagree (373)? YES
```

The join is not degenerate: 738 buildings joined cleanly (0 missing from either side, 0 duplicate
`osm_id` on either side), and both vintage and archetype show a genuine mix of agreement and
disagreement — not all-agree, not all-disagree.

---

## 6. Recommendation (not a closure — the director decides)

**OPEN-08 does not reduce to its archetype half alone.** The vintage half is real and non-zero where
it can be measured (3.79%, `nyc_centre`), smaller than the archetype disagreement (13.40%) but not
negligible, and it shows the expected data-poor skew (3.93% vs 0.00%, though the data-rich comparison
group is thin at n=25).

**But the vintage half is now only *partially* quantified, not fully quantified**, and that partiality
is itself worth recording precisely: measurable on 1 of 5 T08 cells (738/4,530 = 16.3% of the
population the archetype figure covers), because the only on-disk prior-generation source that
carries `vintage_standard` (`cases/<cell>/05_results.gpkg`) has that column in only 1 of the 5 cells'
files — a schema gap, not a missing-column-fleet-wide problem as the register previously stated.
Extending this to the other 4 cells would require either a different prior-generation vintage source
(none found on disk in this task) or accepting the register's original "unmeasurable" finding for
those 4 cells specifically.

**Suggested register disposition:** keep OPEN-08 open, but narrow its vintage clause from
*"unquantifiable"* to *"quantified on 1 of 5 T08 cells (16.3% of the shared population): 3.79%
disagreement, data-poor-skewed; unquantifiable on the remaining 4 cells for a schema reason, not a
data-absence reason."* Do not fold OPEN-08 into "archetype only."

---

## 7. Artifacts

- `openubem/outputs/comparisons/open08_vintage_reproducibility.csv` — 738 rows, columns `osm_id,
  vintage_prior, archetype_prior, levels, height_m, year_built, provenance_levels,
  provenance_height_m, provenance_year_built, in_prior, vintage_current, archetype_current,
  in_current, vintage_agree, archetype_agree, data_poor`.
- `scripts/analysis/open08_vintage_reproducibility.py`.

---

## Register amendment to apply

*(Director: place under OPEN-08's §-section, `INVESTIGATION_open-items-register.md`, immediately
after the existing 2026-08-05 amendment that currently ends "…see new item **OPEN-30**." Do not
delete that text — strike only the now-superseded clause as shown.)*

> **Amended 2026-08-18 (T03 of `PLAN_open-52-and-four-items-2026-08-18.md`).** ~~Vintage disagreement
> remains unquantifiable — no harvest persists a `vintage_standard` column, see new item OPEN-30.~~
> **OPEN-30 closed 2026-08-11: `vintage_standard` is persisted, but only in the E02 manifests — a
> generation that post-dates both T08 and T20.** Re-deriving OPEN-30's own gate (40,800 rows, 0 nulls,
> 5 distinct values, `DOERefPre1980` 93.4436%) reproduces exactly
> (`extra/MEASUREMENT_open-08_vintage-reproducibility.md` §1). Re-running OPEN-28's own T08-vs-T20
> join reproduces its 4,530-row shared population and 13.3996%≈13.40% archetype disagreement exactly
> (§2) — the reused, not re-invented, comparability baseline. **Vintage is quantifiable cross-generation
> only where a prior-generation source carrying `vintage_standard` exists on disk: 1 of the 5 T08
> cells (`nyc_centre`, 738/4,530 = 16.3% of the shared population) — the other 4 cells' candidate prior
> source (`cases/<cell>/05_results.gpkg`) carries a stripped 21-column schema with no
> `vintage_standard` at all, a schema gap, not a data gap.** On that 738-building subset: vintage
> disagreement **3.79%** (28/738) vs the archetype 13.40% on the full population — smaller, not zero,
> and skewed toward data-poor buildings (3.93% among 713 data-poor buildings vs 0.00% among 25
> data-rich ones, though the data-rich comparison group is thin). **OPEN-08 does not reduce to its
> archetype half. Recommend narrowing the vintage clause to "quantified on 1/5 T08 cells, unquantifiable
> on the remaining 4 for a schema reason" rather than closing it.** Evidence:
> `extra/MEASUREMENT_open-08_vintage-reproducibility.md`,
> `openubem/outputs/comparisons/open08_vintage_reproducibility.csv`.
