# MEASUREMENT — OPEN-14: localising the config gate, and what a clean checkout needs to reproduce the backfill

**Task:** T07 of `../implemenation/previous/PLAN_twenty-items-2026-08-19.md`. Script:
`scripts/analysis/open14_t07_gate_construction_2026-08-19.py` (constructed local case, run
against the real committed `overture_nyc_centre_slice.parquet`, not the synthetic testcell
fixture).

## 1. The gate, localised

`openubem/config.py:141` — `FUSION_SOURCES_BY_TARGET: dict = {}` — is the shipped default.

Trace, entry point to the point `FUSED` would be written:

- `fusion.precedence_for(attr, cfg)` (`openubem/semantic/fusion.py:167-178`) reads
  `getattr(cfg, "FUSION_SOURCES_BY_TARGET", {}).get(attr, ())` at `fusion.py:172`. With the
  default `{}`, this returns `()` for every attribute, so `out = []` (`fusion.py:173-177`) —
  **zero sources are ever consulted, for any attribute.**
- `fusion.fuse(gdf, attr, cfg)` (`fusion.py:379`) calls `precedence_for` internally; with an
  empty precedence list it returns null value / null token for every row without touching
  `OvertureSource.join` at all — confirmed by reading `fuse()`'s body, not inferred.
- `_fusion_tier` (`openubem/semantic/imputation.py:627-661`) is the imputation-tier wrapper
  that calls `fusion.fuse()` (`imputation.py:655`) and, on any non-null hit, stamps the
  `FUSED_<SOURCE>_HIGH`/`_MED` token onto the `provenance_<attr>` column (`imputation.py:663-
  664`). It is reached from `impute_missing()`'s tier dispatch (`imputation.py:882` maps
  `"fusion"` → `"_fusion_tier"`), and `"fusion"` **is** in the default tier order
  (`config.py:100`, `IMPUTE_ENABLED_TIERS = ("fusion", "spatial", "statistical")`) — so the
  tier itself is reached by default; it is `fuse()`'s empty precedence list that turns it into
  a no-op, not the tier being switched off.

**The gate is exactly `config.py:141`.** Nothing else in the chain from `impute_missing()` down
to `OvertureSource.join()` blocks on its own — every other branch is reachable with the shipped
defaults.

## 2. A second, un-costed blocker the register's framing does not name: `impute_missing()` is not on the production path at all

Grepping every caller of `impute_missing(` and `fusion.fuse(` in `openubem/` and `scripts/`
(excluding tests): the **only** caller of `impute_missing()` anywhere in the repository is
`openubem/validation/mask_recover.py:330,338` — the T08/T09 mask-recovery **validation harness**.
`imputation.py:888-891`'s own docstring says this directly: *"Does not reroute `enrich_semantics`
... this is a new entry point for the T08/T09 validation harness to call directly."*

The production path that actually builds a cell's `01_buildings.gpkg` —
`step1_fetch → BuildingClassifier.classify → _impute_levels`
(`openubem/semantic/building_classifier.py:137-155,591-694`) — was checked directly:
`_impute_levels` (`building_classifier.py:137`) reads `row["height_m"]` **as an input** to
impute `levels` (`:147-149`, `HEURISTIC_HEIGHT` tier) but never writes to `height_m` itself, and
neither `_impute_levels` nor `classify_building`/`BuildingClassifier.classify` imports or calls
`fusion` or `imputation.impute_missing` anywhere — confirmed by `grep -n "impute_missing\|fusion"
openubem/semantic/building_classifier.py`, zero hits. This matches and restates X09/N15's already-
established finding (register OPEN-14, "Code reachability" row) rather than superseding it — it is
reported here again because T07 asks specifically what a clean checkout needs, and the answer is
incomplete without it.

**So there are two blockers stacked, not one:** (1) the config gate (§1), and (2) production code
never calls the function that would consult the gate in the first place. Opening the config gate
alone changes nothing for a fleet build — it only changes what `mask_recover.py`'s validation
harness would produce if invoked with fusion enabled.

## 3. Constructed local case — does opening the gate make `FUSED` appear?

Built the smallest local case using the **real, tracked** `overture_nyc_centre_slice.parquet`
(not the synthetic `overture_testcell_slice.parquet` used by the existing test suite): one
building-footprint polygon centred on a real slice geometry's centroid whose `height` field is
non-null (8.7 m), `height_m = NaN` on the target row.

```
gate CLOSED (FUSION_SOURCES_BY_TARGET={})               -> value=[nan]  token=[None]
gate OPEN   (FUSION_SOURCES_BY_TARGET={'height_m': ('overture',)}) -> value=[8.7]  token=['FUSED_OVERTURE_HIGH']
via impute_missing(), gate open, same slice              -> height_m=[8.7]  provenance_height_m=['FUSED_OVERTURE_HIGH']
```

**The gate is confirmed as what closes it**: identical input, identical slice, the only variable
changed is `FUSION_SOURCES_BY_TARGET`, and the token flips from `None` to `FUSED_OVERTURE_HIGH`
exactly when the gate opens — both through `fuse()` directly and through the full
`impute_missing()` orchestrator (the function `mask_recover.py` actually calls).

As independent corroboration, the existing regression suite already encodes the same construction
against the synthetic testcell fixture:
`tests/test_height_backfill.py::TestFusionTierProvenanceAndFloor::test_every_newly_filled_height_m_row_carries_a_token`
and `::TestFuseHeightFromOfflineSlice` (both classes, 5 tests) — re-run fresh, **5 passed, 0
failed** (`.venv/Scripts/python.exe -m pytest -q tests/test_height_backfill.py -k
"TestFusionTierProvenanceAndFloor or TestFuseHeightFromOfflineSlice"`).

## 4. What would have to be true for a clean checkout to reproduce the backfill

**Both the gate and the slice, and in a specific order that also requires a change §1–2 shows is
not just configuration.** First, `FUSION_SOURCES_BY_TARGET` would need a non-empty entry for
`height_m` (e.g. `{"height_m": ("overture",)}`) — a one-line config change, demonstrated
sufficient in §3. Second, an Overture slice would need to exist and be reachable for whichever
cell is being built — either a committed slice (only `nyc_centre` and the synthetic `testcell`
currently exist, `git ls-files -- "openubem/data/fixtures/fusion/*"`) or a live
`FUSION_OVERTURE_ENDPOINT`, which the arc's own tests (`TestPullOvertureNeverAutoReachable`,
`tests/test_height_backfill.py:59-70`) keep deliberately unreachable from any pipeline entry
point for hard-rule reasons unrelated to this item. Third — and this is the piece the register's
current framing (config gate vs. missing slice, as a two-way choice) does not include — **the
production entry point itself would have to be rewired to call `impute_missing()` (or
`fusion.fuse()` directly) for `height_m`**, since at HEAD nothing in `step1_fetch →
BuildingClassifier.classify → _impute_levels` does. Opening the gate and supplying every cell's
slice would change what the *validation harness* can recover; it would change nothing about a
fleet build until this third piece is also done. **Order:** the gate change is a no-op without the
routing change (§2 proves the routing change is currently absent, §3 proves the gate change alone
is sufficient once routing exists), so the minimal-change ordering is: (a) confirm/keep the slice
committed for the target cell, (b) wire the production classify path to call the fusion tier for
`height_m`, (c) open the gate. Doing (c) before (b) reproduces nothing on a fleet build; doing (b)
before (a) has no slice to consume; the register's own N15 chronology finding (`nyc_centre`'s
`01_buildings.gpkg` committed three weeks before its Overture slice existed) is the same ordering
constraint stated for a single historical case.
