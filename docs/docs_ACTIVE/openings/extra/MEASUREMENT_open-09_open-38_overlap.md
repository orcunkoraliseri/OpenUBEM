# MEASUREMENT — OPEN-09 x OPEN-38: are the non-convergent 16 and the fatal 44 the same story?

**Date:** 2026-08-21 · **Task:** T10 of `PLAN_ten-live-items-2026-08-21.md` · **Items:** OPEN-09,
OPEN-38 · **Script:** `scripts/analysis/open09_open38_overlap_2026-08-21.py`
**Output:** `openubem/outputs/comparisons/open09_open38_overlap_2026-08-21.csv` (16 rows, one per
member of A)

## Controls

- **C22** — |A| = **16**, cell split `la_centre 2, la_rural 10, la_suburban 3, la_urban 1` — matches
  F6 exactly. ✅
- **C23** — |B| = **44**. ✅

## Populations

**A** (OPEN-09, the 16) — `open56_open09_run4_err_census_2026-08-20.csv` where `has_converge`. This
census has no `mode` column; it is inherently the `auto`-mode run-4 corpus (8,160 rows = the fleet).
**B** (OPEN-38, the 44) — `open38_fatal_causes_2026-08-20.csv`, all 5 modes. `B` restricted to
`mode == 'auto'`: **n = 11** (the only mode comparable to A).

## Overlap

| comparison | n |
|---|---:|
| \|A ∩ B\| any mode | 11 |
| \|A ∩ B\| restricted to `mode == 'auto'` | **6** |

**All 16 members of A, and whether each is in B:**

| cell | stem | archetype_id | in fatal-44 (any mode) | in fatal-44 (auto only) |
|---|---|---|---|---|
| la_centre | way_427817687 | Warehouse | False | False |
| la_centre | way_428015178 | Warehouse | True (`floor`) | False |
| la_urban | way_402215469 | *(null)* | True | **True** |
| la_suburban | way_442633387 | Warehouse | False | False |
| la_suburban | way_442634081 | Warehouse | False | False |
| la_suburban | way_442634778 | Warehouse | False | False |
| la_rural | way_472960972 | *(null)* | True | **True** |
| la_rural | way_472961034 | *(null)* | True | **True** |
| la_rural | way_472961043 | Warehouse | False | False |
| la_rural | way_472961088 | *(null)* | True | **True** |
| la_rural | way_472961089 | Warehouse | True (`fast_zone`) | False |
| la_rural | way_472961090 | Warehouse | True (`fast_zone`) | False |
| la_rural | way_472961091 | *(null)* | True | **True** |
| la_rural | way_472961093 | Warehouse | True (`fast_zone`) | False |
| la_rural | way_472961164 | Warehouse | True (`fast_zone`,`floor`) | False |
| la_rural | way_472961171 | *(null)* | True | **True** |

**This splits perfectly by archetype.** Every one of the **6** buildings with a null `archetype_id`
(the unresolved/`OpenUBEMUnknown`-adjacent group) is also a `mode == 'auto'` fatal in B — **6/6**.
Every one of the **10** `Warehouse` buildings is **not** a `mode == 'auto'` fatal — **0/10** — though
5 of those 10 do go fatal in `fast_zone` or `floor` mode, just never in `auto`.

**Severe-class of the 6 auto-mode overlaps:** all six are `Temperature (high) out of bounds`
(F7's 21-building family), not `CalcHeatBalanceInsideSurf` (F7's 17-building family). The `auto`-mode
fatal set also contains 2 `nyc_centre` buildings and 1 `la_centre` building that ARE
`CalcHeatBalanceInsideSurf` — **none of those three carry the "Inside surface heat balance did not
converge" warning** (they are not in A at all, since A is LA-only per F6, and `nyc_centre` isn't in A).

## Same-mechanism check on A's 5 non-overlapping-in-auto members that ARE never fatal at all

Of the 10 `Warehouse` buildings, 5 (`way_427817687`, `way_442633387`, `way_442634081`,
`way_442634778`, `way_472961043`) never appear in B under **any** mode. For each, the auto-arm
`eplusout.err` was grepped directly for `CalcHeatBalanceInsideSurf`: **0 of 5 carry that line.**
These 5 are non-convergent-but-otherwise-clean in `auto` mode — no trace of the fatal family at all,
in any severity.

## Verdict

**Overlapping population, not the same population and not disjoint — and the overlap divides cleanly
along a variable already in hand.** The 6 unresolved-archetype `la_rural`/`la_urban` buildings in
OPEN-09's 16 are the *same buildings*, at the *same* `Temperature (high) out of bounds` signature, as
6 of OPEN-38's 44 auto-mode fatals — for that subset, "did not converge" (warning) and the fatal
temperature blowup are the same event observed at different points before EnergyPlus gives up. The
other 10 (all `Warehouse`) are a separate story: non-convergent in `auto` without ever going fatal
there, and where they do go fatal it is only in `fast_zone`/`floor` mode. **No merge of the two items
is proposed — that determination belongs to the director**, per the plan's own instruction.

## Remedy shape (NOT applied)

None — this task measures overlap, it does not remediate.

## How-to-test results

- **C22** — ✅ exact, 16, cell split matches F6.
- **C23** — ✅ exact, 44.
