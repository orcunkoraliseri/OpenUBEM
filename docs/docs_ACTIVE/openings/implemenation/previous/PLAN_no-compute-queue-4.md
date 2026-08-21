# PLAN — The no-compute queue, round 4 (OPEN-06, fleet closure)

> **Slug:** `no-compute-queue-4` · **Opened:** 2026-08-06 · **Author:** manager session
> **Predecessors:** `PLAN_no-compute-queue.md` (N01–N05), `PLAN_no-compute-queue-2.md` (N06–N12),
> `PLAN_no-compute-queue-3.md` (N13–N15). **Fifteen tasks dispatched; fourteen landed and were audited
> by independent re-derivation. N13 stalled once and was relaunched; it is not part of this round.**
> **Binding upstream contract:** `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md`.
> **Governing arc rule:** *no execution plan may be written for an item until that item's first
> measurement has been made.* **This is a measurement plan. Phase 2 does not exist and is not written.**

---

## 1. Why this round exists

**N14 closed OPEN-06's third open question on four cells and named the other eight as uncovered.** Its
own report, §1: the eight fleet cells not covered *"are named as uncovered… nothing here is claimed to
generalise to them without checking."* That is the correct way to stop, and it leaves exactly one
no-CPU task behind.

**This round is one task.** It finishes the sweep N14 started, and it does so against a **falsifiable
prediction** rather than as an open-ended re-run — see §5.2. A sweep that merely confirms "more of the
same" would not be worth the tokens; a sweep that can come back **wrong** is.

**Nothing in this round can make a published number wrong.** OPEN-06 concerns whether a published
*label* can be regenerated, and N08 established the simulation used the correct archetype regardless.
**If the report implies otherwise, it is wrong.**

---

## 2. Hard rules for the executor

**`PLAN_no-compute-queue-2.md` §2 applies in full, all fourteen rules, unchanged.** Read it — it is the
binding rule set and this section does not replace it. The six that will bite hardest here:

1. **Remediation is FORBIDDEN.** You will find things you could fix in one line. You may not.
2. **No CPU-bound work.** No EnergyPlus, no IDF generation, no fleet pass, no cluster. **Stage 2 only**
   — §5.4 — which this plan authorises explicitly and nothing beyond.
3. **Do not edit the register or the director prompt.** The manager amends those after audit. You
   append **one entry to §7 of this document** and nothing else.
4. **Report an unknown as an unknown**, and if two sources disagree, **report both with dates and do
   not adjudicate.**
5. **Recompute every headline number from the named file before reporting it.** Do not carry a number
   forward from the register or from N14's report — **those are among the things being checked.**
6. **Do everything in this session.** Never wait for a notification, never pause until a background
   task reports, never spawn a subagent. If something would take a long time, run it and read the
   file it writes. **A task that ends its turn waiting has produced nothing.**

---

## 3. File layout to create

```
docs/docs_ACTIVE/openings/extra/
└── MEASUREMENT_open-06b_column-reproducibility-fleet.md   (N16)
```
CSVs to `openubem/outputs/comparisons/` with an `open06b_` prefix. **No `.py` under `docs/`.**
**Do not overwrite N14's `open06_*.csv` files** — they are audited evidence. New prefix, new files.

---

## 4. Dependency decisions — pinned, do not re-debate

- **Python:** `./.venv/Scripts/python.exe`. No new third-party dependency.
- **The eight cells this round covers**, and a sweep covering seven is not a sweep:
  `nyc_urban`, `la_centre`, `la_urban`, `la_suburban`, `la_rural`,
  `austin_centre`, `austin_urban`, `austin_suburban`.
- **Drive the real `t08_full_sweep.run_step2()`** (`scripts/cluster/t08_full_sweep.py:106-149`),
  imported, never reimplemented. This project has been burned specifically by scripts that
  reimplement pipeline logic and produce lookalike evidence.
- **Whole cells only.** OPEN-34 established a subset is not archetype-faithful.

---

## 5. Source-of-truth verified facts — established and director-verified 2026-08-06

**You may rely on these. Anything else, you derive and cite.**

### 5.1 What N14 measured, and where it stopped
Four whole cells, all 33 columns of `05_results.gpkg`, buckets **REPRODUCES / DIFFERS /
STAGE-3-OR-LATER / ABSENT**. Result: **26 of the 33 columns are STAGE-3-OR-LATER** and are
**unreachable without compute — do not attempt them.** Only two columns landed in DIFFERS:
`archetype_id` and `data_quality_flag`. Per-cell `archetype_id`: `nyc_centre` **26/738**,
`nyc_rural` **4/198**, `austin_rural` **0/245**, `nyc_suburban` **0/1,589**.

### 5.2 The prediction this round must try to break
`openubem/outputs/comparisons/open06_mislabel_population.csv` (N04) holds **41 rows**, per cell:
**`austin_centre` 2, `la_centre` 4, `la_urban` 5, `nyc_centre` 26, `nyc_rural` 4.**
Director-verified by direct read 2026-08-06. N14's four cells matched it exactly, **including both
zeroes.**

**Therefore the prediction, stated before the measurement:** across the eight cells of §4,
`archetype_id` must DIFFER on **exactly 2 rows in `austin_centre`, 4 in `la_centre`, 5 in `la_urban`,
and 0 in each of `nyc_urban`, `la_suburban`, `la_rural`, `austin_urban`, `austin_suburban`.**

- **If it holds**, the mislabel population is fully accounted for by the reproducibility gap, on the
  whole fleet, and OPEN-06's scope is finally bounded.
- **If extra differing rows appear**, `open06_mislabel_population.csv` is **incomplete** — a finding
  about the evidence base itself, and more important than the confirmation would have been.
- **If predicted rows fail to differ**, HEAD and the committed file agree where N04 said they did not,
  and **two audited artifacts are in conflict: STOP and report both, do not adjudicate.**

**Report the prediction and the outcome side by side, per cell, whichever way it falls.**

### 5.3 The trap N14 fell into — do not repeat it
N14 reported `data_quality_flag` differing on *"exactly the same 9 rows"* as `archetype_id`. **That is
false and was struck on audit**: its own CSV shows `nyc_centre` **26** archetype differences against
**38** flag differences. The 12 extra rows differ **only** by a trailing `|narrow_perimeter_fallback`
token, which is written at **`openubem/idf/builder.py:614-615`** — a **Stage-3** module, so Stage 2
can never emit it. **A Stage-3 token appearing in a Stage-2 diff is an artifact of the comparison, not
an unreproducibility.**

**So `data_quality_flag` differences must be partitioned into exactly two classes, counted separately,
and never merged:**
- **(a) STAGE-3-TOKEN** — the two values are identical after removing `narrow_perimeter_fallback`
  (and any other token you can trace to a Stage-3-or-later module; **name the file and line if you
  find another**). Not evidence of anything about Stage 2.
- **(b) PROVENANCE-DIVERGENCE** — the *imputation-provenance* token itself differs, e.g.
  `HOTDECK_NEIGHBOR_MED` at HEAD vs `GROUPMODE_MED` committed. **This is the real finding**: which
  fallback rule fired differs between HEAD and write-time.

**Report per-cell counts of (a) and (b) separately.** Then state whether class (b) rows are a subset
of, equal to, or wider than the `archetype_id` differing rows — **as a checked set comparison, not an
impression.** N14 asserted this without checking; that is precisely the error being corrected.

### 5.4 Stage 2 is cheap
N05 drove the real `run_step2()` over a full 738-building cell in **0.6 s**. **Stage 2 — enrichment
and classification — is not CPU-bound and is authorised here.** Stage 3 (IDF generation) and beyond
**are** and are **not** authorised anywhere in this plan.

### 5.5 Third geometry-derived column
N14 established `footprint_area_m2` joins `levels`/`height_m` as a column whose `05_results.gpkg`
value is geometry-stage-derived, **not** a Stage-1 passthrough — 715/738 `nyc_centre` rows already
differ with **no Stage-2 code involved.** **Do not report any of these three as a Stage-2
unreproducibility.** Bucket them STAGE-3-OR-LATER and say why.

---

## 6. Task list — measurement only

### N16 — Does the column-reproducibility result hold on the other eight cells? (OPEN-06)

**What to do.** Repeat N14's column-by-column Stage-2 regeneration on the **eight** cells of §4, using
the same imported `run_step2()`, and test §5.2's stated prediction cell by cell. Partition
`data_quality_flag` differences per §5.3.

**Why.** OPEN-06's third open question was answered on a third of the fleet. N14 named the remaining
eight as uncovered and refused to generalise. **§5.2 turns the leftover into a test that can fail**,
and §5.3 corrects a claim that was struck on audit — the flag finding currently rests on one cell pair
and an uncorrected set assertion.

**How.**
- **State the prediction from §5.2 in your report before your results**, so a reader can see it was
  not fitted afterwards.
- **All eight cells, whole cells, no subsets.** If a cell's input files are missing or unreadable,
  **that is a result** — report it as such with the path you tried, and continue with the rest. **Do
  not silently drop it, and do not substitute another cell.**
- **Same four buckets, same 33 columns.** Bucket counts must sum to the committed file's column count
  **per cell**; print both numbers for each.
- **`archetype_id` is the control**, and here it is a **two-sided** one: it must DIFFER in
  `austin_centre`/`la_centre`/`la_urban` and REPRODUCE in the other five. **A control that fails in
  either direction is a STOP-and-report, not a footnote.**
- **Partition `data_quality_flag` per §5.3(a)/(b) with per-cell counts**, and report the set
  relationship to `archetype_id`'s differing rows explicitly.
- **Report any column that lands in DIFFERS in these eight cells but did not in N14's four.** N14 found
  only two; a third would be the most interesting result available here, and it is why the sweep is
  worth running at all.
- **Do not fix anything, and do not edit N14's artifacts.**

**How to test.** (a) Per-cell bucket counts sum to the column count; both printed for all eight cells.
(b) The §5.2 prediction is restated verbatim and each cell marked **HELD / EXTRA ROWS / MISSING ROWS**,
with a one-line overall verdict. (c) Every DIFFERS column reports both values for ≥3 named buildings.
(d) `data_quality_flag` class (a) and class (b) counts are given separately per cell, and the set
comparison against `archetype_id` is stated as a checked result.

**Artifacts.** `extra/MEASUREMENT_open-06b_column-reproducibility-fleet.md` +
`openubem/outputs/comparisons/open06b_column_reproducibility_fleet.csv` (+ a diff-examples CSV with the
same prefix).

---

## 7. Stop-and-report point

**CP-N7 — after N16.** One task, one checkpoint. The manager audits **by independent re-derivation
from the raw files**, then amends the register, the director prompt, this plan's §8 and the board —
**four surfaces, every task, unasked.**

**If the §5.2 prediction fails in the MISSING ROWS direction, that goes to the user immediately** — it
would mean two audited artifacts contradict each other, which is a finding about the evidence base and
not about OPEN-06.

## 8. Progress log

*Append one entry per completed task, in the template used by `PLAN_no-compute-queue-2.md` §8.
Append-only — never rewrite an entry, including one you believe is wrong; correct it in a new entry
that cites the old.*

#### N16 — Does the column-reproducibility result hold on the other eight cells? (OPEN-06) — completed 2026-08-05
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06b_column-reproducibility-fleet.md`,
  `openubem/outputs/comparisons/open06b_column_reproducibility_fleet.csv` (264 rows),
  `openubem/outputs/comparisons/open06b_column_reproducibility_fleet_diff_examples.csv` (182 rows),
  `openubem/outputs/comparisons/open06b_dqf_partition.csv` (171 rows). N14's `open06_*.csv` files were
  not touched.
- Deviations: none from the plan's task list. One method extension beyond N14's, required by §5.3's
  own instruction to "name the file and line if you find another" Stage-3 token: the eight-cell sweep
  surfaced `data_quality_flag` diffs whose extra content was not `narrow_perimeter_fallback`. Tracing
  found three more Stage-3 appenders (`multipolygon_coerced_to_largest_part` at
  `openubem/idf/builder.py:145-146`, `layout_assign_fallback_auto` at `:439-440`,
  `storey_match_fallback_shorter`/`storey_match_fallback_not_expressible` at `:472-474`) plus two
  comma-separated Stage-3 appenders in a different module (`idf_dp_coarse`, `idf_hull_simplification`
  at `openubem/geometry/footprint.py:33,38`) and two Stage-5 appenders in `openubem/results/parser.py`
  (`RESULTS_CSV_FALLBACK:548`, `IOD_NO_OCCUPIED_HOURS:367,396,410`). A first-pass partition using only
  a `"|narrow_perimeter_fallback"` suffix match (the direct extension of N14's method)
  misclassified 2 of 171 differing rows as PROVENANCE-DIVERGENCE when they in fact carried only the
  comma-appended `idf_dp_coarse`/`idf_hull_simplification` tokens; corrected with a tokenizer that
  splits on both `|` and `,` and strips the full known-token vocabulary before comparing (report §4.1).
  The superseded first-pass CSV was not kept as a separate artifact — it was overwritten in place by
  the corrected version before this entry was written, so no stale file exists under the `open06b_`
  prefix.
- Test status: (a) PASS — all eight cells' bucket counts sum to 33, both numbers printed per cell
  (report §2). (b) PASS — §5.2 prediction restated verbatim before results (report §0) and marked
  HELD in all eight cells, with a one-line overall verdict; combined with N14 the prediction now holds
  on all twelve fleet cells. (c) PASS — `archetype_id` (11 rows) and `data_quality_flag`
  (≥3 named per cell where it fired) both report both values for named buildings (report §3, §4.2).
  (d) PASS — `data_quality_flag` class (a)/(b) counts given separately per cell and sum to each
  cell's differ-count (report §4.2); the set relationship to `archetype_id`'s differing rows is
  stated as a checked `osm_id`-level result, not an impression (report §4.3).
- Headline numbers, each with the file it was re-derived from:
  - `archetype_id` differs exactly 2/413 (`austin_centre`), 4/226 (`la_centre`), 5/618 (`la_urban`),
    0 in the other five cells — re-derived from `Stage2 run_step2()` output vs.
    `docs_VALIDATION/.../phaseE/<cell>/05_results.gpkg` (git `0df422e`, 2026-07-03), all 11 differing
    rows cross-checked one-for-one (both `osm_id` and both values) against
    `openubem/outputs/comparisons/open06_mislabel_population.csv` (N04) — exact match, zero extra,
    zero missing rows.
  - `data_quality_flag` differs on 15/44/36/10/6/12/40/8 rows respectively across the eight cells
    (171 total), partitioned (a) STAGE-3-TOKEN / (b) PROVENANCE-DIVERGENCE per §5.3 — 3 rows total in
    class (b) fleet-wide, re-derived from `open06b_dqf_partition.csv`.
  - No column other than `archetype_id`/`data_quality_flag` lands in DIFFERS in any of the eight
    cells — re-derived by filtering `open06b_column_reproducibility_fleet.csv` for
    `bucket==DIFFERS AND column NOT IN (archetype_id, data_quality_flag)`: zero rows.
- Notes for the auditor: **one finding beyond the §5.2 prediction, flagged per CP-N7's routing rule.**
  §5.2 held exactly (not a MISSING-ROWS failure, so this is not the immediate-escalation case the plan
  names) — but the required class-(b) set comparison (report §4.3) found `la_urban/way/1176846930`:
  `archetype_id` reproduces exactly (this building is not in the 41-row mislabel population, in either
  N04's file or this task's re-derivation) yet `data_quality_flag`'s imputation-provenance token
  genuinely differs (`GROUPMODE_MED` at HEAD vs. `HOTDECK_NEIGHBOR_HIGH` committed at
  `0df422e`) — a defect independent of the Hotel→Office mechanism. The set relationship is **not**
  uniform across the fleet: EQUAL in `austin_centre` (2/2 rows coincide with the archetype diffs),
  DISJOINT in `la_urban` (this one row), and trivially EQUAL (both empty) in the other six cells —
  reported as a checked result per §4.3, not adjudicated further here.

#### AUDIT — CP-N7 / N16 — manager, 2026-08-06

**Method: independent re-derivation from the raw artifacts.** Nothing below is read back from the
executor's report; every number was recomputed by the manager from the named file, and every code
citation opened.

**GREENLIT.** The §5.2 prediction **HELD**, and it held on the strict reading.

- **Bucket sums.** All eight cells: 33 columns each, `REPRODUCES + DIFFERS + STAGE-3-OR-LATER = 33`,
  `ABSENT 0`. Re-derived from `open06b_column_reproducibility_fleet.csv` (264 rows = 8 × 33).
- **Coverage, checked arithmetically.** Per-cell `n_compared`: 1,779 + 226 + 618 + 1,343 + 149 + 413 +
  425 + 437 = **5,390**; N14's four cells = 738 + 198 + 245 + 1,589 = **2,770**; **5,390 + 2,770 =
  8,160**, the exact fleet count. **All twelve cells are now covered, whole, with no subsetting** —
  an independent confirmation of §4/§6's "whole cells only" rule that does not rely on the report.
- **The prediction.** `archetype_id` DIFFERS 2/413 `austin_centre`, 4/226 `la_centre`, 5/618
  `la_urban`; REPRODUCES with `n_differ=0` in `nyc_urban`, `la_suburban`, `la_rural`, `austin_urban`,
  `austin_suburban`. **Exactly as predicted, in both directions.**
- **One-for-one row check, re-run by the manager.** All 11 differing rows joined to N04's
  `open06_mislabel_population.csv` on `(cell, osm_id)`: **11/11 matched on both values**, zero extra,
  zero missing. **The 41-row mislabel population is now fully accounted for across the whole fleet.**
- **Third DIFFERS column: none.** Filtering the CSV for `bucket==DIFFERS` returns only `archetype_id`
  and `data_quality_flag` in all eight cells. N14's two-column result holds fleet-wide.
- **§5.3 partition, recomputed:** 168 STAGE-3-TOKEN / 3 PROVENANCE-DIVERGENCE, total 171, which equals
  the sum of the `data_quality_flag` `n_differ` column (15+44+36+10+6+12+40+8). Class (b) is
  `austin_centre` 2, `la_urban` 1, zero elsewhere.
- **Code citations opened and confirmed:** `openubem/idf/builder.py:614-615` (`|`-appended
  `narrow_perimeter_fallback`), `builder.py:145` (`multipolygon_coerced_to_largest_part`),
  `builder.py:439` (`layout_assign_fallback_auto`), `builder.py:473`
  (`f"storey_match_{match_result['status']}"`), and `openubem/geometry/footprint.py:33,38` via
  `_append_flag` (`:15`) — **comma**-separated, a genuinely different convention. All are Stage-3
  modules. The tokenizer finding is real and is the reason the count is 3 and not 5.

**Two corrections, recorded and not deleted (§8 is append-only).**

1. **The progress-log entry above says the set relationship is "trivially EQUAL (both empty) in the
   other six cells". That is wrong: it is five cells, not six.** `la_centre` has **4** differing
   `archetype_id` rows and **0** class-(b) rows — a strict (empty) subset, not an equality. The
   report's own §4.3 table states this correctly ("class-(b) is a (trivial, empty) SUBSET"), so the
   artifact is right and only the log's prose summary is loose. **The correction strengthens the
   finding rather than weakening it:** in `la_centre`, four buildings whose archetype fails to
   reproduce carry **no** provenance divergence at all, so the two defects are independent in *both*
   directions — disjoint in `la_urban`, and now empty-where-archetype-differs in `la_centre`.
2. The executor's hand-off summary named the token family `storey_match_fallback_*`; the code at
   `builder.py:473` builds it as `f"storey_match_{match_result['status']}"`. Same family, same file,
   same Stage-3 conclusion — noted so a later reader greps the right string.

**Not adjudicated here:** *why* `la_urban/way/1176846930` and the two `austin_centre` buildings take a
different imputation fallback at HEAD than at write-time. That is a mechanism question and belongs to
OPEN-06's provenance thread, not to this measurement.
