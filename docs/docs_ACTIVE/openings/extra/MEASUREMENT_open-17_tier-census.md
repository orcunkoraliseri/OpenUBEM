# MEASUREMENT — OPEN-17: which imputation tier actually fills the fleet, and what the two orphans do at HEAD

> Executes T09 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`.
> Measurement only. No tier promoted, enabled or wired. No test deleted or skipped.

## Population and denominator (D5)

All 12 cells of run 4 (`C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4`),
`<cell>/01_buildings.gpkg`. 8,160 buildings total (matches T02's bound). Denominator per target =
rows the raw acquisition marks as missing/generic for that field (see table below); every row has
exactly one `provenance_<field>` token, so denominator + `OSM_OBSERVED` count = 8,160 for every
target except `geometry` (8,160 `OSM_OBSERVED`, 0 missing).

## (a) Tier census

Script: `scripts/analysis/open17_tier_census_2026-08-20.py`.
CSV: `openubem/outputs/comparisons/open17_tier_census_2026-08-20.csv`.

`01_buildings.gpkg` is the raw Step-2.1 acquisition output — 23 columns, no `archetype_id`/
`use_class`/`climate_zone`. It predates classification, so it cannot be run through
`openubem.semantic.enrich_semantics` (which requires the classified 29-column frame and gates on it
via `_validate_input_schema`, `openubem/semantic/__init__.py:334`). Per D3 this script therefore
reads exactly what run 4 persisted, calling no production imputer, re-implementing nothing.

**Finding: every `provenance_*` token found in run 4's persisted inputs is an acquisition-stage
marker (`OSM_OBSERVED` / `OSM_MISSING` / `OSM_GENERIC`). Zero tokens from any of the five T07 tiers
(`fusion`/`spatial`/`ml`/`draw`/`statistical`) or from the legacy `CANONICAL_PROVENANCE` vocabulary
(`ASHRAE_STANDARD`/`HEURISTIC`/`KDE_IMPUTED`/`PDE_GENERATED`) appear anywhere in the 7
`provenance_*` columns across all 8,160 buildings.** This is not a measurement gap: `impute_missing`
(`openubem/semantic/imputation.py`, the orchestrator for the 5-tier system) is never called from the
production path — only from `openubem/validation/eui_impact.py`, `openubem/validation/mask_recover.py`
and analysis/test code (verified: `grep -rln impute_missing openubem/ scripts/` outside tests
returns exactly those two `openubem/` modules, neither on the fleet-build path). The only production
imputer that *is* wired into `enrich_semantics` is `construction_sets.resolve_vintage` (year_built's
own 3-tier spatial/group-mode/legacy-default system, reusing the `HOTDECK_NEIGHBOR_HIGH`/`_MED`/
`GROUPMODE_MED` token spellings) — but it writes into `data_quality_flag` on the ephemeral 57-column
enriched frame, which run 4 never persists back to `01_buildings.gpkg`. So even year_built's real
production fill leaves no trace in the file this task's corpus specifies.

Target x tier x count (summed over all 12 cells; every non-`ACQUISITION` tier is 0 for every
target, so only the `ACQUISITION` row is non-zero):

| target | tier | count |
|---|---|---|
| building_tag | ACQUISITION (not an imputation tier) | 8160 |
| function_tag | ACQUISITION (not an imputation tier) | 8160 |
| geometry | ACQUISITION (not an imputation tier) | 8160 |
| height_m | ACQUISITION (not an imputation tier) | 8160 |
| levels | ACQUISITION (not an imputation tier) | 8160 |
| postcode | ACQUISITION (not an imputation tier) | 8160 |
| year_built | ACQUISITION (not an imputation tier) | 8160 |
| *(all of fusion / spatial / ml / draw / statistical / legacy_default)* | — | 0 |

Denominator per target (`OSM_MISSING` + `OSM_GENERIC`, i.e. rows needing a value):

| target | rows needing a value |
|---|---|
| building_tag | 4,105 |
| function_tag | 7,741 |
| geometry | 0 |
| height_m | 2,806 (matches the OPEN-12 fleet-wide 34.39%/2,806 figure already on record) |
| levels | 7,719 |
| postcode | 4,183 |
| year_built | 5,913 |

`data_quality_flag` (comma-separated, distinct grammar from the `|`-separated tier vocabulary in
`provenance.py`) carries only the 5 acquisition-gap flags `no_floors` (7,719) / `no_year` (5,913) /
`generic_tag` (4,105) / `no_function` (3,837) / `no_height` (2,806) — none match any tier or legacy
token either.

**C23** — every provenance token found (`OSM_OBSERVED`, `OSM_MISSING`, `OSM_GENERIC`) is classified;
none are unmapped-and-unexplained — pass.
**C24** — `FUSED` count reported explicitly: **0** — pass (matches F5 and T08's cross-check).

## (b) Orphan check

`openubem/results/draw_leaderboard.py:174` — `orig = dict(config.IMPUTE_DRAW_METHOD_BY_TARGET)`
inside `_draw_pairs`. Calling `_draw_pairs` raises, exact text:

```
AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DRAW_METHOD_BY_TARGET'
```

`openubem/results/impute_scatter.py:235` — same unguarded read inside `_pooled_draw_pairs`, never
reached: the module fails at **import time**, before line 235, because
`openubem/results/impute_scatter.py:63` does `from openubem.validation.mask_recover import
recover_pairs`, and `mask_recover.py` defines no such name (only `mask_and_recover`). Exact text:

```
ImportError: cannot import name 'recover_pairs' from 'openubem.validation.mask_recover' (C:\Users\o_iseri\Desktop\OpenUBEM\openubem\validation\mask_recover.py)
```

This is a distinct, worse failure than F7 predicted for this module (F7 said "AttributeError on
first use"; the actual failure is an ImportError that blocks the module from loading at all).
Registered as `[OPEN]` in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 7. Not fixed —
no remedy is in scope for this plan.

`py -3 -m pytest -q tests/test_draw_methods.py`:

```
43 passed, 10 skipped in 0.80s
```

**C25** — both orphans' exact exception text quoted above — pass.

## Test status

- `py -3 -m pytest -q tests/test_draw_methods.py` → 43 passed, 10 skipped (no failures; no test
  deleted or skipped by this task).

## C23–C25 — pass
