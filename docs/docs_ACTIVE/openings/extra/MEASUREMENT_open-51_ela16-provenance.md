# MEASUREMENT — OPEN-51 provenance re-check (T02 of `PLAN_open-48-and-four-items-2026-08-18.md`)

> **Slug:** `open-51_ela16-provenance` · **Date:** 2026-08-18 · **Register item:** OPEN-51 (already retired)
> **Task:** T02 of `implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`. Documentary only — no
> `.py` script, no file other than this one touched (register excluded, per rule 9).

---

## 0. Headline finding — the task's own premise is stale

This plan's §1 rationale for T02 says: *"the item's own 'What would settle it' names a cheap, local,
documentary check that nobody has run."* **That is false at the time this plan was written.** The
register (`INVESTIGATION_open-items-register.md:5243` onward) already shows:

```
#### ✅ CLOSED 2026-08-18 — T02 of `implemenation/previous/PLAN_five-items-2026-08-18.md`. Adjudicated on
evidence; the code comment was wrong.
```

`git log --oneline -3 -- docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-51_e-la-16-identity.md`
→ the file was added in commit `b2d0220` ("docs/chore: ignore AI assistant files, add OPEN
measurements, and update results aggregator"), which is **already on `main`, an ancestor of the
current HEAD (`a650658`)**. `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-18.md`
exists on disk and its own T02 (line 206, completed-entry at line 428) performed exactly this check,
closed OPEN-51, and retired the ID (register line 685: `~~OPEN-51~~ ... ✅ ADJUDICATED + CLOSED + ID
RETIRED 2026-08-18 (T02)`).

**So this is not an open question — it is a duplicate of already-completed, already-closed work.**
Per rule 12 I am not inventing a remedy or silently skipping the task; I re-ran the check independently
(rule 7, re-derive, never inherit) as directed, below, and it both confirms the prior verdict and
improves on its evidence — see §4. The register needs **no substantive change**, but §5 below records
one factual correction to the prior closure's provenance claim.

---

## 1. `PLAN_structural-fixes_implementation.md:279` in full context

Read in full: `docs/docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md`,
§8 Error Log. The E-LA-16 entry (minted 2026-07-23, tasks T04/T05):

> #### E-LA-16 — Cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family, post-T03-fix,
> not confined to originally-failing buildings — OPEN — 2026-07-23 (T04/T05)
> - **Symptom (T04, `la_urban` TallBuilding, thermal_mass=True via T03):** `way/402036176` (S=2.738) —
>   succeeds, but 16 Severe: `** Severe ** Calculation of cooling coil design UA failed` across 16
>   distinct `RESI_BOT/MID_N/S_APARTMENT_*_ZN FCU COOLING COIL` objects (non-fatal). `way/402036789`
>   (S=4.051) and `way/1395739331` (S=6.281) — both `failed_fatal`: `** Fatal ** Autosizing of cooling
>   tower UA failed for tower CENTRIFUGAL FAN CYCLING OPEN COOLING TOWER 40.2 GPM/HP` (`Bad starting
>   values for UA`). Independently reproduced via `grep` on the raw `.err` files for all 3 myself —
>   exact match.
> - **Symptom (T05, `austin_urban` Hospital, already `status=="success"` in T18 before this plan):**
>   `way/187382924` `n_severe` 4→3, `way/382005990` `n_severe` 3→3 — the SAME cooling-coil-UA family.
> - **Recommendation:** ... this should be scoped and root-caused before `layout_assign`'s thermal-mass
>   default is considered fully production-safe fleet-wide.

This is a self-contained, defining text: names three buildings, quotes exact `** Severe **`/`** Fatal
**` text, states it was `grep`-verified against the raw `.err` at the time (2026-07-23).

---

## 2. The run's `.err` — located, not gone

The prior closure (`extra/MEASUREMENT_open-51_e-la-16-identity.md:72-76`) states: *"None of the 57+
local `eplusout.err` files under `docs/docs_DONE/SETUP/layoutAssigner/` belong to `way_402036176`,
`way_402036789`, or `way_1395739331` — the original T04/T05 run's raw evidence is gone from this
machine."* Its search was scoped to `debug/storey-Matching/results/*` and
`docs_DONE/SETUP/layoutAssigner/` only.

**I searched the whole repository tree, not just those two paths, and found raw `.err` files for all
three building IDs that were not searched by the prior closure:**

```
$ find . -iname "*402036176*" -o -iname "*402036789*" -o -iname "*1395739331*" | grep -v "\.git/"
./scratchpad/t19_t01_t05_work/work_t04/la_urban/sim/way/1395739331/eplusout.err  (+ siblings)
./scratchpad/t19_t01_t05_work/work_t04/la_urban/sim/way/402036176/eplusout.err
./scratchpad/t19_t01_t05_work/work_t04/la_urban/sim/way/402036789/eplusout.err
(plus two other scratchpad trees with the same three IDs, dated to different, later sessions)
```

`scratchpad/t19_t01_t05_work/` has task-numbered subdirectories (`work_t02`, `work_t04`, `work_t05`)
that map exactly onto the structural-fixes plan's own T02/T04/T05 task structure, and `work_t04`
contains only `la_urban` + `nyc_rural` — exactly T04's population. The `.err` files' own EnergyPlus
banner line reads `YMD=2026.07.23 22:20`, matching E-LA-16's minting date. This is either the actual
original T04 artifact or a byte-identical contemporaneous rerun; either way it is far closer to "the
original evidence" than the prior closure's substitute.

Raw content, this session:

```
$ grep -c "cooling coil design UA failed" .../work_t04/la_urban/sim/way/402036176/eplusout.err → 16
$ tail -1 .../way/402036176/eplusout.err
   ... EnergyPlus Completed Successfully-- 110963003 Warning; 16 Severe Errors; Elapsed Time=...

$ grep -iE "Fatal.*cooling tower UA" .../way/402036789/eplusout.err
   **  Fatal  ** Autosizing of cooling tower UA failed for tower CENTRIFUGAL FAN CYCLING OPEN COOLING TOWER 40.2 GPM/HP
$ tail -1 .../way/402036789/eplusout.err
   ... EnergyPlus Terminated--Fatal Error Detected. 436 Warning; 1 Severe Errors; Elapsed Time=...

$ grep -iE "Fatal.*cooling tower UA" .../way/1395739331/eplusout.err
   **  Fatal  ** Autosizing of cooling tower UA failed for tower CENTRIFUGAL FAN CYCLING OPEN COOLING TOWER 40.2 GPM/HP
$ tail -1 .../way/1395739331/eplusout.err
   ... EnergyPlus Terminated--Fatal Error Detected. 435 Warning; 1 Severe Errors; Elapsed Time=...

$ grep -c "CheckWarmupConvergence"  (all three files) → 0, 0, 0
$ grep -c "CheckAirLoopFlowBalance" (all three files) → 0, 0, 0
```

**This is an exact match to Reading A's quoted text** — 16 Severe cooling-coil-UA for `402036176`
(not 23, as the prior closure's substitute harvest showed), and a Fatal cooling-tower-UA-autosize
for both `402036789` and `1395739331` (the prior closure's substitute showed 0 Fatal for these two
and flagged that as an unresolved discrepancy — resolved here: it was a run-config difference in
their substitute, not in the actual original). Zero `CheckWarmupConvergence`, zero
`CheckAirLoopFlowBalance` in all three — Reading B's namesake mechanisms are absent.

**Control (rule 8):** before trusting a zero-hit `grep`, I confirmed the same command finds a known
positive in the same file — `grep -c "cooling coil design UA failed"` returns 16 (not 0) on
`402036176`, and the Fatal-line grep returns a real match on the other two. The detector works.

---

## 3. `git log`/`git blame` on `layout_assigner.py:863-865`

```
$ git blame -L 855,870 -- openubem/geometry/layout_assigner.py
69373f9e 2026-07-27 09:56:55  lines 855-864 (original "CheckWarmupConvergence...E-LA-14/16/18/19/E-LA-06" grouping)
b2d02208 2026-08-18 10:10:49  lines 865-869 (correction: E-LA-16 removed, pointer to
                                MEASUREMENT_open-51_e-la-16-identity.md added)
```

The original grouping (commit `69373f9e`, "feat: complete storey-matching closure, opaque assembly
module, and layoutAssigner updates") is a large batch commit (E-LA-20 investigation, storey-matching
closure, PROJECT_CHECKLIST rewrite — 15+ files) with **no mention of E-LA-16 verification** in its
message or diff context. It dates **4 days after** E-LA-16 was minted (2026-07-23) and cites no
building, no `.err` text, no source — consistent with the prior closure's finding that the
`CheckWarmupConvergence` grouping was copied into the comment, not independently re-derived.

The correction commit (`b2d02208`, 2026-08-18 10:10:49) is already live at HEAD: `E-LA-16` is already
removed from the `CheckWarmupConvergence` list and the comment now points to
`MEASUREMENT_open-51_e-la-16-identity.md`. **No code-comment edit remains to make.**

---

## 4. Which reading the evidence supports

**Reading A (the defining text) — cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed
family.** Supported by: (a) the item's own defining text, self-consistent and grep-verified at the
time; (b) the prior closure's substitute E02-harvest evidence (zero `CheckWarmupConvergence`/
`CheckAirLoopFlowBalance`, all Severes on the cooling-coil-UA signature); (c) **this task's own
independently-located, closer-to-original `.err` artifacts** (§2), which match Reading A's exact
quoted Severe/Fatal text and building-by-building counts, resolving both discrepancies the prior
closure had flagged and left open (the Fatal-vs-no-Fatal mismatch, and the 16-vs-23 Severe count
mismatch).

**Reading B (the code comment's `CheckWarmupConvergence` grouping) is not supported by any evidence**
— not the defining text, not the harvest corpus, not the newly-located original-run artifacts. It
traces to a single unrelated batch commit with no cited source (§3).

**This independently reproduces and strengthens the already-recorded verdict; it does not change
it.**

---

## 5. OPEN-09's C06 — explicitly checked, unaffected beyond what is already recorded

The register already carries the knock-on in two places: the OPEN-51 summary row (line 685: *"OPEN-09's
C06 'five inherited log entries' narrows to four (E-LA-14/18/19/23)"*) and OPEN-09's own section
(line 3757-3760, an `> Amended 2026-08-18` block quoting the same narrowing). I re-read both — they
are consistent with each other and with §4 above. **No further change to OPEN-09's status is implied
by this re-check.** C06's own accuracy finding (96.3% distribution overlap on the
`CheckWarmupConvergence` population) is untouched; it was never about E-LA-16's own buildings.

---

## Register amendment to apply

**No substantive amendment.** OPEN-51 is correctly retired and its knock-on into OPEN-09 is already
recorded. Recommend the director apply one small provenance correction, as an addendum to the existing
retired-OPEN-51 entry and/or a footnote on `extra/MEASUREMENT_open-51_e-la-16-identity.md`, **not**
a reopening:

> **Addendum, 2026-08-18 (T02 of `PLAN_open-48-and-four-items-2026-08-18.md`).** The prior closure's
> claim that *"the original T04/T05 run's raw evidence is gone from this machine"* was based on a
> search of `debug/storey-Matching/results/*` and `docs_DONE/SETUP/layoutAssigner/` only. A
> repository-wide search found raw `.err` files for all three named buildings under
> `scratchpad/t19_t01_t05_work/work_t04/la_urban/sim/way/{402036176,402036789,1395739331}/eplusout.err`
> (task-numbered directories matching the structural-fixes plan's own T04, dated 2026-07-23 22:20,
> the same day E-LA-16 was minted). These match Reading A's quoted text exactly — including the two
> points the prior closure's E02-harvest substitute could not reproduce (the Fatal on
> `402036789`/`1395739331`, and the 16-Severe count on `402036176`, vs. that harvest's 0-Fatal/23-Severe).
> **Verdict unchanged — E-LA-16 names the cooling-coil-UA family — but the evidence grade upgrades from
> "documentary-plus-corroborating-substitute" to "documentary-plus-located-original-or-contemporaneous-run."**
> `scratchpad/` is uncommitted working-tree scratch, not durable evidence — the director may wish to
> archive these three `.err` files into `docs/docs_ACTIVE/openings/extra/` before they are lost to
> further scratchpad cleanup, but that is a recommendation, not something this task performed.

Also recommend the director note, for process hygiene rather than the register: **this plan's T02 was
written against a stale snapshot of the register** — OPEN-51 had already been closed by a different,
earlier-numbered plan (`PLAN_five-items-2026-08-18.md`) on the same day, before `PLAN_open-48-and-four-items-2026-08-18.md`
was written. No register damage resulted (T02 here made no register edit), but the director may want
to re-check whether T03/T04/T05 of this same plan carry the same risk before they are dispatched.
