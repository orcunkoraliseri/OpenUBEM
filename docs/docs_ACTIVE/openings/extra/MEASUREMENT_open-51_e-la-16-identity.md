# MEASUREMENT — open-51 E-LA-16 identity

> **Slug:** `open-51_e-la-16-identity` · **Date:** 2026-08-18 · **Register item:** OPEN-51
> **Task:** T02 of `implemenation/PLAN_five-items-2026-08-18.md`. One code comment corrected
> (`openubem/geometry/layout_assigner.py:865`, comment text only — no code change). No other file
> touched except this one.

---

## 1. Verdict

**`E-LA-16` names the cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family. The
code comment at `openubem/geometry/layout_assigner.py:863-865` was wrong to group it with
`CheckWarmupConvergence`/`CheckAirLoopFlowBalance` (E-LA-14/18/19/E-LA-06), and has been corrected.**

Decisive evidence: the three buildings E-LA-16's own defining text names —
`way/402036176`, `way/402036789`, `way/1395739331` — were located in the local E02 harvest corpus
(`la_urban_layout_assign` mode) and their raw `eplusout.err` files show **zero**
`CheckWarmupConvergence` hits, **zero** `CheckAirLoopFlowBalance` hits, and 23/21/16 Severes
respectively, **all** of the form `Calculation of cooling coil design UA failed`. The competing
reading's namesake mechanisms do not appear in these buildings' own runs at all.

**Correction, 2026-08-18 (T06):** the 26/24/19 figures originally reported here were wrong. The
`grep -ic "Severe"` count used to produce them also matched the three trailing
`************* EnergyPlus ... Error Summary` lines each `.err` file ends with (Warmup Error Summary,
Sizing Error Summary, and the final "Completed Successfully" line), which contain the word "Severe" as
part of a `0 Severe Errors` / `N Severe Errors` count but are not themselves `** Severe **` fault lines.
Subtracting those 3 non-fault lines per file gives the true counts, **23/21/16**, which match each
file's own final summary line (`... N Severe Errors; Elapsed Time=...`) exactly. This does not affect
the verdict: the correct counts are still 23/21/16 of the same `Calculation of cooling coil design UA
failed` signature, zero `CheckWarmupConvergence`, zero `CheckAirLoopFlowBalance` — the conclusion in §1
is unaffected.

---

## 2. The two readings, with citations

**Reading A — the defining text**, `docs/docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:279`
(§8 Error Log, minted 2026-07-23, tasks T04/T05):

> #### E-LA-16 — Cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family, post-T03-fix, not confined to originally-failing buildings — OPEN — 2026-07-23 (T04/T05)
> - **Symptom (T04, `la_urban` TallBuilding, thermal_mass=True via T03):** `way/402036176` (S=2.738) —
>   succeeds, but 16 Severe: `** Severe ** Calculation of cooling coil design UA failed` across 16
>   distinct `RESI_BOT/MID_N/S_APARTMENT_*_ZN FCU COOLING COIL` objects (non-fatal). `way/402036789`
>   (S=4.051) and `way/1395739331` (S=6.281) — both `failed_fatal`: `** Fatal ** Autosizing of cooling
>   tower UA failed for tower CENTRIFUGAL FAN CYCLING OPEN COOLING TOWER 40.2 GPM/HP` (`Bad starting
>   values for UA`). Independently reproduced via `grep` on the raw `.err` files for all 3 myself —
>   exact match.

This entry names three specific buildings, quotes exact `** Severe **`/`** Fatal **` text, states the
task and date it was minted, and states the raw `.err` files were directly `grep`-checked at the time.

**Reading B — the code comment**, `openubem/geometry/layout_assigner.py:863-865` (before this task's
correction), introduced in a single commit `69373f9e` (2026-07-27 09:56:55, *"feat: complete
storey-matching closure, opaque assembly module, and layoutAssigner updates"*), unrelated to the
structural-fixes plan:

> All 6 runs below completed with 0 Fatal (see `debug/storey-Matching/results/b06_s1ref/*/eplusout.err`);
> the handful of pre-existing Severes present in some runs (`CheckWarmupConvergence`,
> `CheckAirLoopFlowBalance`) are the same already-tracked classes as **E-LA-14/16/18/19/E-LA-06** and
> do not touch these 4 field classes' own sizing.

This is a one-line parenthetical inside an unrelated field-sizing evidence block (documenting 6
`b06_s1ref` debug runs, none of which are the three named E-LA-16 buildings — confirmed, §4). It names
no building, quotes no `.err` text, and cites no source for the ID list itself.

---

## 3. Raw `.err` evidence — reached, not just quoted

The structural-fixes plan's own run directories (`debug/storey-Matching/results/*`,
`docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/`) were searched exhaustively for the three
named buildings. **None of the 57+ local `eplusout.err` files under
`docs/docs_DONE/SETUP/layoutAssigner/` belong to `way_402036176`, `way_402036789`, or
`way_1395739331`** — the original T04/T05 run's raw evidence is gone from this machine. Per the plan's
own contingency, the defining document's quoted lines would then be the best available evidence.

**But independent raw evidence for these exact three buildings does exist locally**, in a different
corpus: the current E02 harvest at `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\la_urban_layout_assign\<way_id>\eplusout.err`
(this plan's §4 baseline notes this harvest tree is on-disk and readable). This is **not** the
original T04/T05 run — it is a separate, more recent harvest of the same building IDs under
`layout_assign` mode — so it is corroborating, not identical-run, evidence, and is graded accordingly.
Raw grep, this session:

```
$ grep -ic "Severe"                 .../la_urban_layout_assign/way_402036176/eplusout.err  → 26 (23 true Severes + 3 summary lines, see correction above)
$ grep -ic "Severe"                 .../la_urban_layout_assign/way_402036789/eplusout.err  → 24 (21 true Severes + 3 summary lines, see correction above)
$ grep -ic "Severe"                 .../la_urban_layout_assign/way_1395739331/eplusout.err → 19 (16 true Severes + 3 summary lines, see correction above)
$ grep -ic "CheckWarmupConvergence" .../way_402036176/eplusout.err  → 0
$ grep -ic "CheckWarmupConvergence" .../way_402036789/eplusout.err  → 0
$ grep -ic "CheckWarmupConvergence" .../way_1395739331/eplusout.err → 0
$ grep -ic "CheckAirLoopFlowBalance" .../way_402036176/eplusout.err  → 0
$ grep -ic "CheckAirLoopFlowBalance" .../way_402036789/eplusout.err  → 0
$ grep -ic "CheckAirLoopFlowBalance" .../way_1395739331/eplusout.err → 0
```

Every Severe line in all three files reads `** Severe ** Calculation of cooling coil design UA failed
for coil ...` — matching Reading A's quoted text exactly. **None** show `CheckWarmupConvergence` or
`CheckAirLoopFlowBalance` — the two Severe classes Reading B claims E-LA-16 belongs to. One deviation
from Reading A's original quote: this harvest run shows **0 Fatal lines** for `way_402036789` and
`way_1395739331`, where the defining text reported a Fatal cooling-tower-UA-autosize failure for both.
This is most likely a difference in run configuration between the 2026-07-23 T04/T05 run and this
harvest's `layout_assign`-mode run (e.g. whether a cooling-tower plant object is present in this
harvest's IDF variant) — it does not change the identity question (the cooling-coil-UA Severe family is
still the only failure signature present in either case), but it is reported as a discrepancy, not
smoothed over.

**Grading:** this is documentary evidence (the original run's quote) corroborated by independent raw
evidence from a different, later run of the same building IDs — stronger than documentary alone, short
of a byte-identical re-derivation of the original run.

---

## 4. Where Reading B came from

`git blame` on `layout_assigner.py:863-865` shows the entire comment block was added in one commit,
`69373f9e`, 2026-07-27 — four days after E-LA-16 was minted (2026-07-23). The comment is documenting a
**different, narrower** experiment: 6 debug runs under `debug/storey-Matching/results/b06_s1ref/`,
checking that forcing certain HVAC fields to `Autosize` doesn't introduce new Fatals. None of the 57
`eplusout.err` files under `docs/docs_DONE/SETUP/layoutAssigner/debug/` (including the `b06_s1ref`
directory this comment cites) belong to any of E-LA-16's three named buildings — this comment was never
checking E-LA-16's own evidence at all.

The ID list itself — `E-LA-14/16/18/19/E-LA-06` — reads as a recalled-from-memory summary of "known,
already-tracked, pre-existing Severe noise" at the time of writing, not a re-derivation. Per the
structural-fixes plan's own §8 error log (read in full for this task): **E-LA-14, E-LA-18, E-LA-19**
are consistently the `CheckWarmupConvergence` lineage (later joined by **E-LA-23**, per
`docs/PROJECT_CHECKLIST.md:242`), and **E-LA-06**'s flow-balance half is `CheckAirLoopFlowBalance`
(`extra/MEASUREMENT_open-29_eight-defect-recheck.md:33`). **E-LA-15** (`SizeAirLoopBranches` minimum
flow) and **E-LA-17** (persistent zone-divergence signature) are excluded from the comment's list
entirely, even though they are adjacent IDs in the same error log and belong to neither named class —
which is itself evidence the comment's author was constructing an approximate "IDs I remember as
pre-existing noise" list, not systematically checking each ID's defining text. E-LA-16 was swept into
that approximate list by the same process, incorrectly.

**Prior documentation of this exact discrepancy, unresolved until now:** `extra/MEASUREMENT_open-29_eight-defect-recheck.md:71-82`
(2026-08-13) already found and reported this same contradiction — *"Two documents in the tree use
'E-LA-16' for what reads as two different failure signatures... This was not resolved here"* — and
explicitly deferred adjudication as out of that task's scope (§4: *"Whether the E-LA-16 naming
discrepancy... reflects a genuine two-defects-one-ID collision or a documentation error in one of the
two sources... is reported as an open question, not resolved"*). That task's own table already used
Reading A (the defining text) for its verdict row, on the same reasoning as this task, but did not
correct the code comment.

---

## 5. Decision

**E-LA-16 is the cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family
(`PLAN_structural-fixes_implementation.md:279`). The code comment's inclusion of it in the
`CheckWarmupConvergence`/`CheckAirLoopFlowBalance` group (`layout_assigner.py:863-865`, pre-correction)
was a documentation error — an imprecisely recalled ID list in an unrelated comment, contradicted by
the raw `.err` evidence of the three buildings E-LA-16 itself names.** This is not a genuine
two-defects-one-ID collision (the register's third possible outcome, per plan step 5's warning against
inventing a reading) — one source is right, the other is wrong, and the evidence in §3 settles which.

**Correction applied**, live tree only, comment text only, no code change:
`openubem/geometry/layout_assigner.py:865` now reads `E-LA-14/18/19/E-LA-06` (E-LA-16 removed), with a
one-line pointer to this document appended for audit trail. `git diff --stat` on this file shows only
comment lines touched (4 lines added, 1 changed); `ast.parse` confirms the file still parses.
`docs_DONE/` documents were **not** edited (E-LA-16's defining text and the `PLAN_compute-queue.md`/
`MEASUREMENT_open-09` citations that used it correctly stand unchanged, per the register's append-only
convention).

---

## 6. What this does to OPEN-09's C06 and OPEN-29

**OPEN-09's C06 finding must be narrowed.** C06 (`extra/MEASUREMENT_open-09_cosmetic-accuracy-test.md`)
measured whether the "cosmetic" label holds for the `CheckWarmupConvergence` Severe class, and its own
§5 verdict named **"the five inherited log entries (E-LA-14, E-LA-16, E-LA-18, E-LA-19, E-LA-23)"** as
the entries the finding applies to. **E-LA-16 does not belong on that list** — it is not
`CheckWarmupConvergence`, C06's matched-control population (150 `nyc_rural`/`SmallOffice` buildings)
never tested the cooling-coil-UA mechanism, and nothing in C06's method touches it. The list narrows
from five entries to **four: E-LA-14, E-LA-18, E-LA-19, E-LA-23.** E-LA-16's own accuracy impact
remains **completely untested** — this was already implicitly true (C06 never measured cooling-coil-UA
buildings), but was previously mis-stated as covered. This is a correction to record in the register
under OPEN-09/OPEN-51, not a re-run of C06 (out of this task's scope).

**OPEN-29 is unaffected — it already used the correct reading.** Both
`extra/MEASUREMENT_open-29_defect-status-trace.md` and
`extra/MEASUREMENT_open-29_eight-defect-recheck.md` graded E-LA-16 as STILL-OPEN against its own
defining text (the cooling-coil-UA family), explicitly declining to use the code comment's grouping,
and explicitly flagged the contradiction as unresolved (§4 of this document). No verdict in either
document changes; this task resolves the open question those documents deliberately left standing.

---

## 7. What this does NOT do

- Does not re-run or re-derive the original T04/T05 experiment — the corroborating evidence in §3 is
  from a later, separate harvest of the same building IDs, not the original run.
- Does not touch `docs_DONE/` — the defining text and every historical citation of "E-LA-16" inside
  archived documents stand as originally written.
- Does not renumber or split the ID, per the plan's explicit instruction.
- Does not re-test C06's "cosmetic" claim for the narrowed four-entry list, or test it for E-LA-16 —
  both are new measurement tasks, not this one.
