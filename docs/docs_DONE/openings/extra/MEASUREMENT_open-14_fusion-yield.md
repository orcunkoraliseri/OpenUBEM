# MEASUREMENT — OPEN-14: fusion-tier yield on `nyc_centre` (2026-08-20)

**Population:** `nyc_centre`'s `01_buildings.gpkg` (run 4 input,
`C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4\nyc_centre\01_buildings.gpkg`),
738 buildings. **Denominator:** 121 of those 738 have a null `height_m` (16.40 %) — matches the
figure quoted in the task text.

This is a **yield measurement, not a promotion**. `FUSION_SOURCES_BY_TARGET` and
`FUSION_OVERTURE_SLICE_PATH` were set on the imported `openubem.config` module object *inside*
`scripts/analysis/open14_fusion_yield_nyc_centre_2026-08-20.py` and restored in a `finally` block.
`openubem/config.py` on disk is untouched (C22: `git status --porcelain openubem/config.py` →
empty). Run 4 was not touched; no fleet input was regenerated.

## What was configured, and why that shape

`config.FUSION_SOURCES_BY_TARGET` defaults to `{}` (`config.py:141`); its own inline comment gives
the expected shape: `{"height_m": ("overture", "lidar", "assessor")}` — a dict of target column to a
**tuple of source-name strings**, read by `fusion.precedence_for(attr, cfg)`
(`openubem/semantic/fusion.py:167`), which does `cfg.FUSION_SOURCES_BY_TARGET.get(attr, ())` and
keeps only sources whose `.available(cfg)` is `True`. The script sets
`FUSION_SOURCES_BY_TARGET = {"height_m": ("overture",)}` — that expected tuple shape, not a guess.

Setting only that key is not sufficient to make the tier fire: `OvertureSource.available(cfg)`
(`fusion.py:224-228`) requires `cfg.FUSION_OVERTURE_SLICE_PATH` **or** `cfg.FUSION_OVERTURE_ENDPOINT`
to be truthy — with neither set, `precedence_for` returns `[]` regardless of
`FUSION_SOURCES_BY_TARGET`, and the tier is a no-op again for a different reason. The task names the
tracked slice `overture_nyc_centre_slice.parquet` as the one input this cell can be measured against,
so the script also monkey-patches `config.FUSION_OVERTURE_SLICE_PATH` to that fixture's path
(`openubem/data/fixtures/fusion/overture_nyc_centre_slice.parquet`, tracked, 1,667 rows, raw
Overture-shaped columns `id/height/num_floors/class/subtype/geometry`, EPSG:4326). Both attributes
are restored in the `finally` block.

The router was called as `imputation.impute_missing(gdf, cfg=ImputeConfig(enabled_tiers=("fusion",)),
targets=["height_m"])` — `enabled_tiers` pinned to `("fusion",)` only, so the reported count is the
fusion tier's own yield, not conflated with what `spatial`/`statistical` would additionally fill on
the same population under the default 3-tier chain (`config.IMPUTE_ENABLED_TIERS`, `config.py:100`,
already includes `fusion` first in canonical order — the gate blocking it at HEAD is exclusively
`FUSION_SOURCES_BY_TARGET = {}`, confirming F5/F6).

## Result

- **106 of 121** null `height_m` rows in `nyc_centre` were filled by the fusion tier
  (`fusion → OvertureSource`), all 121 - 106 = **15 left null** for a later tier.
- **Provenance token:** all 106 filled rows carry `FUSED_OVERTURE_HIGH` — a direct field join
  (`fusion.py:399-401`), never `_MED`/`_LOW` for this run (Overture's `height` column needs no
  derivation the way `levels` from height would).
- **Distribution vs. the non-null population** (n=617 originally-observed `height_m` in this cell):
  observed mean 41.93 m (std 40.54, min 2.6, median 27.8, max 397.0); the 106 fusion-filled values
  have mean 95.69 m (std 57.91, min 3.1, median 93.9, max 247.4) — the filled distribution sits well
  above the observed one (higher central tendency, no near-zero mass), consistent with `nyc_centre`'s
  null `height_m` rows skewing toward taller buildings the OSM pass under-tagged, not toward the
  same population as the observed set.

## Why the remaining 15 were not filled — traced, not guessed

Traced directly against `fusion.OvertureSource.join` and `_spatial_join_positions`
(`fusion.py:230-252`, `:63-`):

- **14 of 15** matched an Overture footprint spatially (centroid-within-polygon or nearest-within-10 m),
  but the matched Overture record's own `height` field is `NaN` — a real gap in the Overture slice's
  source data, not a join failure. Confirmed by re-running `_load_overture_layer` +
  `_spatial_join_positions` directly and reading `layer["height"].iloc[pos]` for each of the 14: all
  `NaN`.
- **1 of 15** (`way/473560487`) has no spatial match at all within the 10 m tolerance
  (`fusion.py:47`, `NEAREST_TOLERANCE_M = 10.0`).
- **0 of 15** were discarded by the `_MIN_HEIGHT_FLOOR_M = 2.1` physical floor
  (`imputation.py:621-661`) — no fused candidate value fell below it in this run.

## Test status

- **C20 — pass.** The run stamps `FUSED_OVERTURE_HIGH` on 106 rows; the tier is not a no-op once
  `FUSION_SOURCES_BY_TARGET` and `FUSION_OVERTURE_SLICE_PATH` are both configured (traced above).
- **C21 — pass.** Fill rate reported: **106 of 121** null `height_m` rows in `nyc_centre`.
- **C22 — pass.** `git status --porcelain openubem/config.py` → empty (verified after the run).

## Artifacts

- `scripts/analysis/open14_fusion_yield_nyc_centre_2026-08-20.py`
- `openubem/outputs/comparisons/open14_fusion_yield_nyc_centre_2026-08-20.csv` (739 lines = 738 rows
  + header; columns `osm_id, height_m_before, height_m_after, provenance_height_m_before,
  provenance_height_m_after, was_null, filled_by_fusion`)

## Design question this measurement sizes, and does not answer

OPEN-14's remedy (does this project acquire more Overture slices, and for which cells) is the user's.
This measurement only sizes one cell's answer: on `nyc_centre`, opening the fusion gate with the one
tracked slice recovers **~88 %** (106/121) of that cell's missing `height_m`, at `HIGH` confidence,
with the residual gap traced to Overture's own source-data completeness, not to the join or the
config shape.
