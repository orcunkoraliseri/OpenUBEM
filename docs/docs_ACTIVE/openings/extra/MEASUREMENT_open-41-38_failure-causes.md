# MEASUREMENT — OPEN-41 failure causes and OPEN-38 subsurface census

> **Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_e02-audit-and-closure.md`, T02.
> **Script:** `scripts/analysis/e02_failure_causes_subsurface.py`
> **Outputs:** `openubem/outputs/comparisons/open41_failure_causes.csv` (44 rows),
> `openubem/outputs/comparisons/open38_subsurface_census.csv` (8 rows)
> **Date:** 2026-08-11.

## Method

One streaming pass over all 40,800 `eplusout.err` files in the E02 harvest corpus
(`C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest`). Per file: test the two-space fatal regex
`\*\*\s+Fatal\s+\*\*`; if it matches, walk backwards through the text for `\*\*\s+Severe\s+\*\*` line
matches occurring before the fatal's position, and record the first and last such line plus a
`cause_group` derived from the last one. Independently, test every file (fatal or not) for the substring
`Base surface does not surround subsurface` and count occurrences. Each file is read once and discarded;
no per-file text is retained.

## Non-vacuity control (mandatory)

- Fatal count found: **44** (not 0, not 45, not 40,800).
- `nyc_centre/fast_zone/way_1240348353` (the 89-storey building, the one missing `.end`, on record as
  dying on `std::bad_alloc`): **absent from the fatal set** — confirmed `has_fatal = False`. Its `.err`
  has no `**  Fatal  **` line at all; the file ends mid-line inside a `GetSimpleAirModelInputs` warning
  block, consistent with an out-of-memory crash rather than a controlled EnergyPlus termination.
- Control passes exactly as specified.

## Known-cause control

`la_centre/auto/way_319507579` is the one self-describing failure:
`** Severe  ** Plant temperatures are getting far too hot, check controls and relative loads and
capacities` (the `CheckForRunawayPlantTemps` mechanism). Reproduced.

## Known-severe control

`nyc_centre/auto/way_266149332`: `n_severe = 1`, and both `first_severe` and `last_severe_before_fatal`
are `** Severe  ** CalcHeatBalanceInsideSurf: The temperature of 90915.77 C for zone="WAY/266149332_F0_CORE",
for surface="BLOCK CORE_ZONE STOREY 0 WALL 0004_1"`. Matches the register's figure exactly (90,915.77 °C,
`CalcHeatBalanceInsideSurf`). The backwards scan captured the mechanism, not the generic trailer.

Note: the same `osm_id` (`way_266149332`) also fails in `nyc_centre/fast_zone`, independently, at a
different (negative) blown-up temperature on a different surface. Two separate rows in the CSV, both
legitimate — not a parsing artifact.

## (a) OPEN-41 — cause groups, 44 of 44

| cause_group | n | mechanism |
|---|---:|---|
| `Temperature (low) out of bounds [...] for zone="...", for su` | 25 | warmup/simulation surface-temperature collapse (large negative) |
| `CalcHeatBalanceInsideSurf` | 17 | warmup/simulation surface-temperature runaway (large positive or negative), explicit routine |
| `Temperature (high) out of bounds [...] for zone="...", for s` | 1 | warmup/simulation surface-temperature runaway (large positive) |
| `Plant temperatures are getting far too hot, check controls a` | 1 | `CheckForRunawayPlantTemps` — plant-loop temperature runaway |

43 of 44 failures are surface/zone thermal-runaway blow-ups (two message families reporting the same
underlying instability, one naming the routine explicitly and one not); 1 is a plant-loop runaway. There
is no failure in this set whose cause is anything other than a numerical thermal-runaway blow-up — no
input-file syntax error, no missing object, no license/licence or memory failure among the 44 (memory
failure is the *45th*, excluded one).

## (b) `la_rural` cross-mode concentration and intersection

Per-mode failing-stem counts reproduce the register's cited figures exactly: `auto` 7, `floor` 7,
`fast_zone` 10 — 24 total, none in `building` or `layout_assign` for this cell.

- **auto** (7): way_472960972, way_472961034, way_472961047, way_472961088, way_472961091,
  way_472961092, way_472961171
- **floor** (7): way_472960972, way_472961034, way_472961047, way_472961088, way_472961091,
  way_472961164, way_472961171
- **fast_zone** (10): way_472960972, way_472961034, way_472961047, way_472961088, way_472961089,
  way_472961090, way_472961091, way_472961093, way_472961164, way_472961171

**Union across the three modes: 11 distinct buildings.**
**Intersection across the three modes: 6 buildings** — way_472960972, way_472961034, way_472961047,
way_472961088, way_472961091, way_472961171.

**Verdict: split, not clean.** 6 of 11 (55%) fail in every one of the three modes regardless of geometry
strategy — that subset's cause is per-building input data, and reads as an input-validation finding. The
remaining 5 are mode-specific: way_472961092 fails only in `auto`; way_472961164 fails in `floor` and
`fast_zone` but not `auto`; way_472961089/090/093 fail only in `fast_zone` (consistent with `fast_zone`
carrying additional sensitivity or a lower resource ceiling on top of the same underlying buildings).
This does not cleanly resolve to either the plan's two named outcomes — it is a dominant per-building
cause with a smaller mode-sensitive edge.

## (c) OPEN-38 — subsurface census, fleet-wide, all five modes

The substring `Base surface does not surround subsurface` was found in **8 buildings, all of them in
`layout_assign`**. Zero occurrences in `auto`, `building`, `fast_zone`, or `floor` — confirmed by scanning
every one of the 40,800 `.err` files, not by assumption.

| cell | mode | stem | n_occurrences | terminated |
|---|---|---|---:|---|
| la_centre | layout_assign | way_427942886 | 3 | True |
| la_urban | layout_assign | relation_6374725 | 3 | True |
| la_urban | layout_assign | way_401910463 | 3 | True |
| la_urban | layout_assign | way_428846131 | 3 | True |
| nyc_rural | layout_assign | way_965718400 | 3 | True |
| nyc_rural | layout_assign | way_965718401 | 3 | **False** |
| nyc_rural | layout_assign | way_965718402 | 3 | True |
| nyc_rural | layout_assign | way_965718403 | 3 | True |

The 7 known terminated failures reproduce exactly: `nyc_rural` 3, `la_centre` 1, `la_urban` 3.

**New finding: the message also appears in one surviving building** — `nyc_rural/layout_assign/way_965718401`
carries the same "Base surface does not surround subsurface" severe (3 occurrences) but does **not**
terminate; the simulation completes. This changes OPEN-38 from a 7-building fatal defect into an
**8-building geometry defect, of which 7 are fatal and 1 silently produces energy results from a
malformed subsurface**. This is inside OPEN-38's own scope as the task anticipated it (T02c), not a new
item — recorded here for the item's disposition, no new OPEN/E-LA ID opened.

## Summary for the register

- OPEN-41: all 44 fatals now have a recorded, grouped cause (0 unexplained). No new item opened.
- `la_rural` concentration: mixed verdict, majority per-building, minority mode-specific — see §(b) above
  for the exact split; this is evidence for OPEN-41's remedy discussion, not itself a new item.
- OPEN-38: population is 8, not 7 — 1 surviving building added. No new item opened; recorded as part of
  OPEN-38's own measurement per the task's own framing.
