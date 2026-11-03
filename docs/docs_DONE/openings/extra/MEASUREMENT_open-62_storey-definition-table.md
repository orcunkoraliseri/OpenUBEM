# MEASUREMENT — OPEN-62: the storey-definition decision table

**Date:** 2026-08-21
**Task:** T06 of `implemenation/previous/PLAN_ten-live-items-2026-08-21.md`
**Script:** `scripts/analysis/open62_storey_definition_table_2026-08-21.py`
**Input:** `openubem/outputs/comparisons/open03_storey_census_zfix.csv` (8,160 rows)
**Output:** `openubem/outputs/comparisons/open62_storey_definition_table_2026-08-21.csv` (184 rows)

This task does not choose a storey definition. It lays the existing candidate columns side by
side against the two ground-truth-shaped columns already in the census (`auto_storey_count`,
`source_storey_count`), fleet-wide and per archetype, so the user's choice takes one minute
instead of a re-run.

## Controls

- **C13** — the census reproduces the register's 30.0 % / 70.0 % OPEN-03 split. Reproduced
  independently in-script from `layout_assign_match_storeys_status` (`identity` 1,226 +
  `applied` 502 + `no_baseline_fallback_auto` 718 = 2,446/8,160 = **29.9755 % → 30.0 %**;
  complement 5,714/8,160 = **70.0245 % → 70.0 %**). Passed — this is the census the register
  cites.
- **C14** — row count is exactly 8,160. Passed.

## Finding before the table: the attic-excluded variant could not be built as specified

The plan's step 2 calls for "an attic-excluded variant built by subtracting
`auto_attic_zone_count` where it applies." The column exists in the census (it does not fail
hard rule 4's non-existence test), but **`auto_attic_zone_count` is 0 for all 8,160 rows** —
verified with `df['auto_attic_zone_count'].describe()`, mean/std/min/max all `0.0`. The
register's attic finding (43.9 % of the fleet, `SmallOffice`/restaurant archetypes) was reached
by a different, prototype-level reader in a different script, not by this column. So the
"attic-excluded" column in the output CSV is **numerically identical, row for row, to
`layout_assign_storey_count_floor`** in this census — it subtracts zero everywhere. This is
reported as the finding, not routed around.

## Fleet-wide headline (n = 8,160)

| definition | vs baseline | agree rate | mean signed diff (def − baseline) | diff range |
|---|---|---|---|---|
| `layout_assign_storey_count` (Z_Origin-corrected) | `auto_storey_count` | 29.07 % | −0.99 | −89 .. +5 |
| `layout_assign_storey_count` (Z_Origin-corrected) | `source_storey_count` | 29.07 % | −0.99 | −89 .. +5 |
| `layout_assign_storey_count_naive` | `auto_storey_count` | 39.78 % | −1.85 | −104 .. +5 |
| `layout_assign_storey_count_naive` | `source_storey_count` | 39.78 % | −1.84 | −104 .. +5 |
| `layout_assign_storey_count_floor` | `auto_storey_count` | 23.75 % | −0.42 | −75 .. +5 |
| `layout_assign_storey_count_floor` | `source_storey_count` | 23.82 % | −0.41 | −75 .. +5 |
| `layout_assign_storey_count_attic_excluded` | `auto_storey_count` | 23.75 % | −0.42 | −75 .. +5 |
| `layout_assign_storey_count_attic_excluded` | `source_storey_count` | 23.82 % | −0.41 | −75 .. +5 |

`auto_storey_count` and `source_storey_count` track each other closely fleet-wide (mean 3.131
vs 3.127), so no candidate definition's ranking changes depending on which baseline is used.
By raw agreement rate on this census, `_naive` agrees most often (39.78 %) and `_floor` least
(23.75–23.82 %); none reaches 50 %.

## Collapse-risk split (the six archetypes flagged `layout_assign_z_origin_collapse_risk`)

2,983 of 8,160 (36.6 %) buildings — `TallBuilding` (92), `HighriseApartment` (32),
`SuperTallBuilding` (24), `SecondarySchool` (11), `MidriseApartment` (2,818), `Outpatient` (6) —
against the remaining 5,177, vs `auto_storey_count`:

| definition | collapse-risk agree rate | non-collapse-risk agree rate |
|---|---|---|
| `layout_assign_storey_count` | 11.53 % | 39.17 % |
| `layout_assign_storey_count_naive` | 40.83 % | 39.17 % |
| `layout_assign_storey_count_floor` | 11.67 % | 30.71 % |
| `layout_assign_storey_count_attic_excluded` | 11.67 % | 30.71 % |

The corrected (`layout_assign_storey_count`) and floor readers agree far less often on the
flagged population than on the rest of the fleet (11.5–11.7 % vs 30.7–39.2 %) — confirming the
plan's premise that these six archetypes are where the candidate definitions diverge materially.
The naive reader is the outlier: it agrees with `auto_storey_count` *more* often on the flagged
population (40.8 %) than on the rest (39.2 %), because it collapses almost everything to 1 and
`MidriseApartment` (2,818 of the 2,983 flagged rows) skews low to begin with.

Full per-archetype breakdown (all 20 archetypes, both baselines, all four definitions) is in
`open62_storey_definition_table_2026-08-21.csv`.

## Remedy shape (NOT applied)

None proposed — out of scope for this task by the plan's own framing (§6 T06 "Why").

## The question for the user

Four readers already exist in this census. None is a validated storey count; each measures a
different geometric quantity:

- **`layout_assign_storey_count` (Z_Origin-corrected wall-base reader).** Counts distinct
  exterior-wall-base elevations in floor-area-counting zones, after adding each zone's own
  `Z_Origin` back in. Agrees with `auto_storey_count` fleet-wide **29.07 %** of the time; on the
  36.6 % of the fleet flagged collapse-risk, agreement drops to **11.53 %**.
- **`layout_assign_storey_count_naive`.** The pre-fix reader, `Z_Origin` not added back —
  collapses any archetype that encodes floor elevation in `Z_Origin` (wall vertices near 0)
  toward 1. Agrees fleet-wide **39.78 %** of the time, the highest raw rate of the four, but for
  a reason unrelated to correctness: it agrees more with `auto_storey_count` on the collapse-risk
  population (40.83 %) than off it (39.17 %), because both `auto_storey_count` and the naive
  reader are pulled low by the same `MidriseApartment`-heavy population.
- **`layout_assign_storey_count_floor`.** Counts distinct floor-surface elevations in
  floor-area-counting zones. Agrees fleet-wide **23.75–23.82 %** of the time. Known (register,
  OPEN-62) to count an attic as an extra storey on prototypes that encode one, but this census's
  `auto_attic_zone_count` column cannot locate which of its own rows that affects — see finding
  above.
- **`layout_assign_storey_count_attic_excluded`.** As specified in the plan (floor reader minus
  `auto_attic_zone_count`, clipped at 1) — **identical to `layout_assign_storey_count_floor` on
  every row of this census**, because the subtrahend is 0 everywhere. Not a distinct definition
  on this data.

No definition is recommended.
