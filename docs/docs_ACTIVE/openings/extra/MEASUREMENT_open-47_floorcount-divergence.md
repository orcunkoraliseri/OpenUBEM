# MEASUREMENT — OPEN-47: the floor-count divergence is already ruled on

**Task:** T04 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md`
**Date:** 2026-08-18
**Register pen:** ❌ not held by this task. See §6 below for the exact text to place.

---

## 1. The ruling comment, quoted in full

`openubem/semantic/building_classifier.py:167-189`:

```
# OPEN-47 T02: floor-count condition, read off the same Table 1 (manuscript pp.17-18):
# "Small office (<2322 m2 and <=3 floors)", "Medium office* (2322 to 9290 m2, <=5 floors)",
# "Large office (>9290 m2 or >=6 Floors)". Flag-gated via use_floor_count, defaults OFF.
#
# OPEN-47 ruling (user, 2026-08-12, plan §1.2): keep area-only as the default; the
# floor-count half above is deliberately NOT applied by default -- deferred, not rejected.
# Reason: of the 598 buildings whose archetype changes under the floor-count bound, only
# 14.2% rest on an OSM-observed floor count (85/598); the rest are imputed -- 57.9%
# HEURISTIC_HEIGHT, 27.9% GROUPMEDIAN_LEVELS_MED (see _impute_levels above, and its
# levels_source token). The office size metric already multiplies by that same imputed
# levels (total_floor_area_m2 = area * max(levels_imputed, 1), see below) -- adding an
# explicit floor-count bound would make the archetype depend on the same imputed quantity
# twice: once through the area product, once through the new bound. use_floor_count stays
# available, default OFF, as the evidence for this decision, not as a deprecated path --
# reopen the day floor-count coverage improves.
# Measured impact (use_floor_count=True vs False, adopted-run fleet phaseE_elevrb, 8,160
# buildings): 598 archetype changes (7.3%), all promotions (SmallOffice->MediumOffice 380,
# MediumOffice->LargeOffice 161, SmallOffice->LargeOffice 57); 437 of those 598 newly gain
# elevator-load eligibility (elevators_by_archetype.json). See
# openubem/outputs/comparisons/open47_floorcount_reclass.csv (one row per changed building:
# osm_id, cell, area_m2, levels, levels_source, archetype_off, archetype_on) and the T02
# progress-log entry in
# docs/docs_ACTIVE/openings/implemenation/previous/PLAN_three-rulings-2026-08-12.md.
```

## 2. `git log` / `git blame` — dating the ruling

```
$ git blame -L 167,189 -- openubem/semantic/building_classifier.py
6aeebb0d (Orcun Koral Iseri 2026-08-13 15:25:31 -0400 167) # OPEN-47 T02: floor-count condition...
... (all 23 lines, same commit, same timestamp)

$ git show -s --format='%H%n%an%n%ad%n%s' 6aeebb0
6aeebb0db742cc797b70ab19087cc8056a64d63a
Orcun Koral Iseri
Thu Aug 13 15:25:31 2026 -0400
feat/fix: elevator breakout, error parser, fleet rerun validation, and openings investigation closure

$ git log --oneline --all -S "OPEN-47 ruling" -- openubem/semantic/building_classifier.py
6aeebb0 feat/fix: elevator breakout, error parser, fleet rerun validation, and openings investigation closure

$ git diff 0df422e 6aeebb0 -- openubem/semantic/building_classifier.py | wc -l
193   (93 insertions, 8 deletions — this single commit introduced the whole use_floor_count
       feature and the ruling comment together; there is no earlier commit touching this text)
```

**Finding.** The comment's own claimed decision date, **2026-08-12**, does **not** match the
commit date that landed it in git, **2026-08-13 15:25:31 -0400** — one calendar day later. The
comment's date is not simply "trusted" here: it is independently corroborated by
`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_three-rulings-2026-08-12.md`, whose §1.2 is headed
*"The CP-1 ruling on OPEN-47 — keep area-only, document the deviation (2026-08-12)"* and whose T02
and T05 progress-log entries are both stamped `completed 2026-08-12`. So the ruling **event**
is corroborated at 2026-08-12 by a source independent of the comment; only the commit that
**recorded** it in `building_classifier.py` landed the next day. Both dates are reported; they are
not the same thing and should not be conflated.

## 3. Re-deriving the comment's numbers

**Method.** Fleet inputs, not the labelled fixture — the comment's numbers (598 / 8,160,
380/161/57, 85/346/167) are fleet-scale counts against the adopted `phaseE_elevrb` run, not an
accuracy metric against a labelled exam. Running against the 50- or 98-row labelled fixture would
produce a different, non-comparable number, not a reproduction of this specific claim. This matches
what OPEN-47's own T02 measured (`scripts/analysis/open47_floorcount_reclass.py`), which is the
method these very numbers came from.

Verified inputs on disk before running (register §0's live-tree warning about E02 artifact
erosion applies to a different corpus, but was checked anyway): all 12 cells under
`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` and
`.../phaseE_elevrb/<cell>/05_results.csv` are present.

**Script (new, this task):** `scripts/analysis/open47_floorcount_divergence.py`. Written
independently rather than re-running T02's own script, per the plan's "re-derive; never inherit a
number" rule — it re-implements the identical method (classify `phaseE`'s Step-1 input twice,
flag OFF/ON, cross-check `archetype_off` against `phaseE_elevrb`'s actual adopted `archetype_id`,
restrict to `RULE_USE_CLASS_SIZE`/`FALLBACK_SIZE_DEFAULT` rows, count `archetype_off != archetype_on`)
because that method is what the fact being tested requires — a different method would not test
whether the *same* fixed inputs reproduce the *same* fixed comment numbers.

**Control (plan §2 rule 8).** Before trusting the fleet-wide count, the script checks itself
against three individually hand-verified transitions quoted in `PLAN_three-rulings-2026-08-12.md`
lines 487-495 (`way/99259744`, `way/379165919`, `way/379166276`). All three matched exactly (see
raw output below) — a positive control that the method detects real transitions, not an artifact
of the aggregation.

**Command and raw output:**

```
$ .venv\Scripts\python.exe scripts\analysis\open47_floorcount_divergence.py
n_total_adopted_run: 8160 (expected 8160)
--- CONTROL: hand-verified transitions from T02 (must match) ---
  way/99259744: expected SmallOffice->MediumOffice, got SmallOffice->MediumOffice [MATCH]
  way/379165919: expected MediumOffice->LargeOffice, got MediumOffice->LargeOffice [MATCH]
  way/379166276: expected SmallOffice->LargeOffice, got SmallOffice->LargeOffice [MATCH]
n_unreproduced (archetype family disagreement vs adopted run): 16
n_reproduced: 8144
n_office_tier_candidates (RULE_USE_CLASS_SIZE / FALLBACK_SIZE_DEFAULT): 4135
n_changed: 598 / 8160 (7.33%)
by direction:
  SmallOffice -> MediumOffice: 380
  MediumOffice -> LargeOffice: 161
  SmallOffice -> LargeOffice: 57
elevator eligibility change among changed buildings:
  gain: 437
  none: 161
total floor area affected (changed rows): 1368418.1 m^2
levels_source breakdown, 598 changed buildings:
  HEURISTIC_HEIGHT: 346 (57.86%)
  GROUPMEDIAN_LEVELS_MED: 167 (27.93%)
  OSM_OBSERVED: 85 (14.21%)
levels_source breakdown, 437 elevator-eligibility-gaining buildings:
  HEURISTIC_HEIGHT: 208
  GROUPMEDIAN_LEVELS_MED: 166
  OSM_OBSERVED: 63
wrote C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open47_floorcount_divergence.csv
```

Output artifact: `openubem/outputs/comparisons/open47_floorcount_divergence.csv` (598 rows, columns
`osm_id, cell, area_m2, levels, levels_source, archetype_off, archetype_on`).

**Do they reproduce? Yes, exactly, on every figure the comment states:**

| Comment's number | Re-derived (this task) | Match |
|---|---|---|
| 598 / 8,160 (7.3%) archetype changes | 598 / 8,160 (7.33%) | ✅ |
| SmallOffice→MediumOffice 380 | 380 | ✅ |
| MediumOffice→LargeOffice 161 | 161 | ✅ |
| SmallOffice→LargeOffice 57 | 57 | ✅ |
| 437 of 598 newly gain elevator eligibility | 437 | ✅ |
| 14.2% OSM_OBSERVED (85/598) | 14.21% (85/598) | ✅ |
| 57.9% HEURISTIC_HEIGHT | 57.86% (346) | ✅ |
| 27.9% GROUPMEDIAN_LEVELS_MED | 27.93% (167) | ✅ |

Two figures appear in `PLAN_three-rulings-2026-08-12.md` §1.2 (not in the code comment itself) and
were re-derived as a bonus check — also exact matches: **0 buildings lose elevator eligibility**
(this run: 0, only `gain`/`none` appear) and **166 of the 437 gaining buildings rest on
GROUPMEDIAN_LEVELS_MED** (this run: 166).

**Register §0's rule ("if the comment's numbers do not reproduce, record both side by side and do
NOT reconcile them") does not apply here** — every number reproduced exactly, so there is nothing
to leave unreconciled. Population and run: `phaseE`'s 12-cell `01_buildings.gpkg` Step-1 input,
cross-checked against `phaseE_elevrb`'s 12-cell adopted `05_results.csv` — same population and run
T02 itself used, independently re-executed.

## 4. Is `use_floor_count` genuinely reachable and genuinely default OFF?

Checked by reading call sites, not the comment:

```
$ grep -rn "use_floor_count" openubem/ scripts/ tests/
openubem/semantic/building_classifier.py:169,179,182  (comment text only)
openubem/semantic/building_classifier.py:204   def _office_size_tier(..., use_floor_count: bool = False)
openubem/semantic/building_classifier.py:206   if not use_floor_count:
openubem/semantic/building_classifier.py:243   def _apply_rule_table(..., use_floor_count: bool = False)
openubem/semantic/building_classifier.py:366,404   _office_size_tier(..., use_floor_count=use_floor_count)
openubem/semantic/building_classifier.py:601   def classify_building(..., use_floor_count: bool = False)
openubem/semantic/building_classifier.py:617   use_floor_count=use_floor_count  (threaded to _apply_rule_table)
openubem/semantic/building_classifier.py:663   BuildingClassifier.__init__(..., use_floor_count: bool = False)
openubem/semantic/building_classifier.py:673   self.use_floor_count = use_floor_count
openubem/semantic/building_classifier.py:708   use_floor_count=self.use_floor_count  (threaded to classify_building)
scripts/analysis/open47_floorcount_reclass.py:66-67   BuildingClassifier(use_floor_count=False/True)  -- T02's own measurement script
```

`BuildingClassifier(use_floor_count=True)` is passed explicitly in exactly two places in the whole
repository: T02's original script (`open47_floorcount_reclass.py`) and this task's re-derivation
script (`open47_floorcount_divergence.py`) — both measurement-only. A repo-wide grep of every other
`BuildingClassifier(` call site (33 hits across `scripts/`, `tests/`, `openubem/`) shows every one
either takes no arguments or passes `detailed_office=`/`overrides_path=` only — **none passes
`use_floor_count`**, so every production and test call site inherits the constructor default
`False`. Confirmed: the flag is genuinely threaded end-to-end (constructor → `classify()` →
`classify_building` → `_apply_rule_table` → `_office_size_tier`, all four hops verified above) and
genuinely defaults OFF everywhere it is not explicitly overridden by a measurement script.

## 5. What, if anything, keeps OPEN-47 open after this

The register's OPEN-47 §-section (`INVESTIGATION_open-items-register.md:4730`) names **two**
reasons the item stays open. Only Reason 1 is in scope for this task; Reason 2 is named, not
measured, per the plan's instruction.

- **Reason 1 — "a substantive divergence from the source ... Not adjudicated."** This is the stale
  premise this task was built to close. It **is** now adjudicated: the 2026-08-12 ruling (§1-3
  above) keeps area-only as the default and documents the floor-count half as deferred, not
  rejected, with the flag left in place as the evidence. **This reason no longer keeps the item
  open** in the form the register currently states it — the divergence is real (the code does test
  area only by default) but it is a ruled-on, deliberate deviation, not an open question.
- **Reason 2 — the citation audit's further findings (not measured by this task).** The register
  records, unresolved: a second fabricated DOI (Sun et al. 2021, real DOI ends `...110603` not the
  cited `...110586`), a systemic wrong-locator pattern across every Deru et al. (2011) Table-1 row
  (cites "Table 3-1, p.9", a table that does not exist in that report), PNNL-23269's
  HighriseApartment content reportedly not present in that document at all, and two further dead
  reference links. **None of this was measured or touched by T04.** If Reason 2 is unresolved,
  OPEN-47 should stay open on Reason 2 alone, re-titled/re-scoped to drop the now-adjudicated
  Reason 1.

Recommendation only, not adopted: the register's OPEN-47 title and Reason-1 text should be struck
and replaced to reflect the ruling, and the item's continued-open status should rest on Reason 2.
This is a recommendation for the director, per the plan's measurement-only rule.

## 6. Register amendment to apply

*(Per this task's constraints, the register is not edited directly — T01 holds the pen
concurrently. The following is the exact text for the director to place under the OPEN-47
§-section, `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md:4730`, appended
immediately after the existing "Reason 1 ... Not adjudicated" paragraph. Strike, do not delete.)*

> ✅ **Amended 2026-08-18 (T04 of `PLAN_open-48-and-four-items-2026-08-18.md`). Reason 1 is
> adjudicated; it no longer keeps this item open.**
>
> ~~🔴 Reason 1 it stays open — a substantive divergence from the source now that the source is
> known. ... Not adjudicated. Any change here is gated by CP-M3 (OPEN-31): before/after accuracy on
> the labelled fixture, both numbers recorded.~~
>
> **`openubem/semantic/building_classifier.py:167-189` carries a user ruling dated 2026-08-12**
> (independently corroborated by `PLAN_three-rulings-2026-08-12.md` §1.2, whose progress-log entries
> are stamped `completed 2026-08-12`; the code itself landed one day later, in commit `6aeebb0`,
> 2026-08-13 15:25:31 -0400 — both dates reported, not conflated). **Ruling: keep area-only as the
> default; the floor-count half is deferred, not rejected.** `use_floor_count` stays in the code,
> default OFF, as the evidence for the decision — director-reverified this task: it is reachable
> end-to-end (constructor → `classify()` → `classify_building` → `_apply_rule_table` →
> `_office_size_tier`) and is passed `True` in exactly two places repo-wide, both measurement
> scripts; every production and test call site inherits the `False` default.
>
> **The comment's measured-impact numbers were independently re-derived this task, fresh, and
> reproduce exactly:** 598/8,160 (7.33%) archetype changes (SmallOffice→MediumOffice 380,
> MediumOffice→LargeOffice 161, SmallOffice→LargeOffice 57); 437/598 newly elevator-eligible, 0
> lose eligibility; levels_source of the 598: OSM_OBSERVED 85 (14.21%), HEURISTIC_HEIGHT 346
> (57.86%), GROUPMEDIAN_LEVELS_MED 167 (27.93%); 166 of the 437 elevator-gaining buildings rest on
> GROUPMEDIAN_LEVELS_MED. Positive-controlled against three hand-verified transitions from
> `PLAN_three-rulings-2026-08-12.md:487-495`, all three matched. Method, script and full output:
> `extra/MEASUREMENT_open-47_floorcount-divergence.md`;
> `openubem/outputs/comparisons/open47_floorcount_divergence.csv` (598 rows).
>
> **OPEN-47 does not close.** Reason 2 — the second fabricated DOI (Sun et al. 2021), the systemic
> Deru et al. (2011) wrong-locator pattern, the PNNL-23269 content question, and two dead reference
> links — was named, not measured, by this task and remains fully open. **OPEN-47 stays open on
> Reason 2 alone; its title and framing should be revised to stop citing the now-adjudicated
> area-vs-floor-count divergence as an open question.**

---

## 7. Progress log entry (for the plan doc's §8, placed by this task per instruction)

See `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md` §8.
