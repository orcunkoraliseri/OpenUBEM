# MEASUREMENT — OPEN-42 + OPEN-11: the surface-orientation census

**Date:** 2026-08-18 · **Task:** T03 of `PLAN_four-items-2026-08-18.md`

Script: `scripts/analysis/open42_surface_orientation_census.py`. Output: `openubem/outputs/comparisons/open42_surface_orientation.csv` (696 rows: one per `GetVertices: <Floor|Roof/Ceiling> is upside down!` warning found across the 30 target runs + 100 background runs, plus one summary row per run).

## Verdict, up front

**The signature does not separate the failing population from healthy runs. The hypothesis named in plan fact 5 is retired.** The `GetVertices: … is upside down!` warning is a deterministic, universal property of the `auto` zoning method — it fires on **100.00% of all 8,160 `auto`-mode runs in the fleet**, whether the run fails or not — and it is essentially absent from every other zoning mode. It cannot distinguish a 6-building, 3-mode failure population from the other 8,154 buildings that share the same mode and never fail.

## 1. Non-vacuity control (obligatory, before any other result)

| case | run | parser count | `grep -c 'upside down'` | agree |
|---|---|---|---|---|
| zero | `la_rural_building/way_472960972/eplusout.err` | 0 | 0 | yes |
| many | `la_rural_auto/way_472960972/eplusout.err` | 144 | 144 | yes |

**PASS.** The parser is not returning the same answer everywhere, and its count matches a hand `grep -c` at both ends.

## 2. Fleet-wide rate — the number that decides the item, reported before interpretation

Scanned all 40,800 `.err` files in `HARVEST_ROOT`:

```
FLEET-WIDE RATE: 8287 / 40800 run directories carry >=1 upside-down warning (20.3113%)
total warning lines = 95,379
```

Broken down by `(cell, mode)` — every one of the 60 buckets, all 12 cells:

| mode | runs carrying the warning | pattern |
|---|---|---|
| `auto` | **8,160 / 8,160 (100.00%)**, all 12 cells | universal — every single `auto` run, no exception |
| `building` | 0 / 8,160 (0.00%) | never |
| `floor` | 0 / 8,160 (0.00%) | never |
| `fast_zone` | 124 / 8,160 (1.52%), scattered 0.13%–4.49% per cell | sporadic, unrelated to the target population |
| `layout_assign` | 3 / 8,160 (0.04%), all in `la_centre` | sporadic |

`8,160 (auto) + 124 (fast_zone) + 3 (layout_assign) = 8,287`, exactly the fleet-wide total. **The entire fleet-wide rate is explained by one fact: every `auto`-mode run carries the warning.** Against this, only 8 of the 8,160 `auto`-mode runs actually fail (OPEN-41/-42's own count) — a 0.10% fatal rate inside a population where the warning rate is 100%. A signature present in 100% of a population and a fatal rate of 0.10% inside that same population cannot be the thing that explains the 0.10%.

**This is background noise across the fleet for the mode where it occurs, not a rare marker of the six failing buildings.** The item is not explained by it.

## 3. The three questions, each against its control

### 4a. Do fatal zones carry the warning more than their non-fatal sibling zones, same run?

This is the sharpest test the plan names, and it goes **the wrong way**:

```
Fatal zone carries an upside-down warning:      1 / 16 failing runs   (6.2%)
Non-fatal sibling-zone rate, same 16 runs:     167 / 359 zones        (46.5%)
```

The zone that actually blows up is **less** likely to carry the flag (6.2%) than an arbitrary other zone in the same failing run (46.5%). If anything, this is an inverse signal, not a supporting one. (The one fatal zone that does carry the flag is `la_urban/way_402215469/auto`, the sole `auto`-only failure among the six — see the per-run table below.)

### 4b. Is the topmost-storey roof systematically inverted while lower storeys are not?

| population | top-floor zone rate | non-top-floor zone rate |
|---|---|---|
| target (30 runs) | 41.67% (55/132) | 40.50% (113/279) |
| background (100 runs) | 26.80% (26/97) | 14.12% (71/503) |

Within the target population the two rates are statistically indistinguishable (41.7% vs 40.5%) — no top-floor concentration. The background sample shows a *larger* top-vs-non-top gap (26.8% vs 14.1%) than the target population does, which is the opposite of what a mechanism specific to the six failing buildings would produce. **No separation.**

### 4c. Do the modes that succeed carry the warning for the same six buildings, or only the failing modes? (the decisive question)

Per-building, per-mode warning counts, target population:

| building | `auto` (FAIL) | `building` (ok) | `fast_zone` (FAIL) | `floor` (FAIL) | `layout_assign` (ok) |
|---|---|---|---|---|---|
| `la_rural/way_472960972` | 144 | 0 | 0 | 0 | 0 |
| `la_rural/way_472961034` | 48 | 0 | 0 | 0 | 0 |
| `la_rural/way_472961088` | 48 | 0 | 0 | 0 | 0 |
| `la_rural/way_472961091` | 48 | 0 | 0 | 0 | 0 |
| `la_rural/way_472961171` | 72 | 0 | 0 | 0 | 0 |
| `la_urban/way_402215469` | 12 | 0 | 0 (ok) | 0 (ok) | 0 |

```
Runs with warning, failing modes (auto/fast_zone/floor): 6 / 18
Runs with warning, succeeding modes (building/layout_assign): 0 / 12
Within the 3 failing modes: auto 6/6, fast_zone 0/6, floor 0/6
```

The warning fires in **exactly one** of the three failing modes (`auto`, 6/6) and in **zero** of the other two failing modes (`fast_zone`, `floor`) that blow up on the identical mechanism (runaway zone temperature — register §OPEN-42, 2026-08-13 amendment). Fact 3 requires a mechanism to be zoning-dependent; this signature is present in a failing mode but does not track failure even inside that mode (§2: 100% of `auto` regardless of outcome), and is completely silent in two of the three failing modes. **A defect present in one mode regardless of outcome, and absent from two other modes that fail by the same mechanism, cannot be the mechanism.**

## 4. Full per-run table (target population, 30 runs)

| cell/stem | mode | has_fatal | n_upside_down | fatal_zone | fatal_zone_upside_down |
|---|---|---|---|---|---|
| way_472960972 | auto | True | 144 | `F2_CORE` | False |
| way_472960972 | building | False | 0 | — | — |
| way_472960972 | fast_zone | True | 0 | `F2_PERIM10` | False |
| way_472960972 | floor | True | 0 | `F2_WHOLE` | False |
| way_472960972 | layout_assign | False | 0 | — | — |
| way_472961034 | auto/building/fast_zone/floor/layout_assign | True/False/True/True/False | 48/0/0/0/0 | — | False (all) |
| way_472961088 | (same pattern) | | 48/0/0/0/0 | | False (all) |
| way_472961091 | (same pattern) | | 48/0/0/0/0 | | False (all) |
| way_472961171 | (same pattern) | | 72/0/0/0/0 | | False (all) |
| way_402215469 | auto | True | 12 | `F3_WHOLE` | **True** |
| way_402215469 | building/fast_zone/floor/layout_assign | False | 0/0/0/0 | — | — |

(Full detail, every warning line with its surface name and storey token, is in the CSV.)

## 5. Candidate mechanism located in code, not fixed

`openubem/idf/surfaces.py` already contains a helper for exactly this signal, `_coreperim_has_inverted_winding` (`:223-234`), and it is deliberately **not** used as a defect check. Its caller's docstring, `_rebuild_degenerate_coreperim` (`:671-681`), states directly:

> `_coreperim_has_inverted_winding` is intentionally excluded — EnergyPlus convention always uses negative signed-area (CW winding) for floor surfaces; checking sign would produce false positives on healthy buildings.

This is in-code corroboration, independent of this measurement, for exactly what §2 found: negative-signed-area ("upside down") floor/roof windings are the **expected, universal shape of core/perim geometry** — `auto` mode is the fleet's core/perim zoning method — and EnergyPlus's own `GetVertices` check flags and auto-corrects them at parse time (`**   ~~~   ** Automatic fix is attempted.` follows every warning line in the raw `.err`). Not fixed, not touched — cited per plan step 6 and stopped here.

## 6. OPEN-11 connection

Fact 10 ties OPEN-11's six "inverted-geometry" buildings to the same six as OPEN-42. This measurement is the first direct test of that label against a mechanism, and the result is negative: the buildings OPEN-11 calls "inverted-geometry" are not distinguished from any other `auto`-mode building by inverted winding — every `auto`-mode building in the fleet is "inverted" by this signature, 8,160 of 8,160. Whatever OPEN-11's "inverted geometry" label originally meant, it is not this warning, and this warning does not corroborate it as a defect specific to those six.
