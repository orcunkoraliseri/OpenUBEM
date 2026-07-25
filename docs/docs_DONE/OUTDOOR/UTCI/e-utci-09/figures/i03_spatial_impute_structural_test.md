# I03 — Structural test of the existing imputation infrastructure

Source: real fixture reads + direct diagnostic calls into
`openubem/semantic/spatial_impute.py::knn_fill` and
`openubem/semantic/imputation.py::impute_column` (no production wiring, no
edits to either module). Script:
`scratchpad/e-utci-09-investigation/i03_spatial_impute_structural_test.py`.
CSV twins: `openubem/outputs/comparisons/i03_knn_fill_default_radius.csv`,
`i03_knn_fill_radius_probe.csv`, `i03_impute_column_comparison.csv`.

## CRS handling

All 4 fixtures arrive already in a projected metric UTM CRS (`nyc_suburban`
EPSG:32618, `nyc_rural` EPSG:32618, `austin_rural` EPSG:32614, `austin_centre`
EPSG:32614) — `gdf.crs.is_projected` reported `True` for all four. No
reprojection was needed or performed (`estimate_utm_crs()` was never invoked
because the native CRS already satisfies `spatial_impute.py`'s "caller must
supply metric coordinates" contract). This matches I01's independent CRS
findings.

## `knn_fill` at production defaults (k=10, radius=100.0 m, mnar_threshold=0.60)

| cell | rows | `height_m` missing | filled | MNAR-blocked | silent no-donor | confidence dist (filled rows) |
|---|---|---|---|---|---|---|
| nyc_suburban | 1589 | 1589 (100.0%) | 0 | 1589 | 0 | — |
| nyc_rural | 198 | 198 (100.0%) | 0 | 192 | 6 | — |
| austin_rural | 245 | 245 (100.0%) | 0 | 232 | 13 | — |
| austin_centre | 413 | 349 (84.5%) | 15 | 334 | 0 | MEDIUM: 7, LOW: 5, HIGH: 3 |

Every row accounted for: `filled + mnar_blocked + silent_no_donor == missing`
in all 4 cells (enforced by an in-script assertion; no accounting mismatch
raised).

**Key finding — the "silent no-donor" bucket is real and non-trivial.** For
`nyc_rural` (6/198 rows) and `austin_rural` (13/245 rows), some missing-height
buildings have **zero neighbours at all within the 100 m radius** — sparse
low-density fabric. Per `spatial_impute.py` lines 218-220, `_query_neighbours`
returns an empty array for these rows, the loop hits `continue` immediately,
and **`blocked_mask[i]` is never set** — so these rows are neither filled nor
flagged `SPATIAL_CLUSTER_MNAR_BLOCKED`. They pass through completely inert:
still NaN in `height_m`, no diagnostic trace in `data_quality_flag` pointing
at why. `nyc_suburban` (dense fabric, every row has neighbours) shows 0 in
this bucket — 100% MNAR-blocked instead, because every neighbourhood is also
100% locally missing so `r_missing >= 0.60` fires for every row that does
have neighbours.

## Radius-sensitivity probe (diagnostic only — no default changed, no config/production wiring)

| cell | radius=250 m | radius=500 m | radius=1000 m |
|---|---|---|---|
| nyc_suburban | filled=0, blocked=1589, silent=0 | filled=0, blocked=1589, silent=0 | filled=0, blocked=1589, silent=0 |
| nyc_rural | filled=0, blocked=197, silent=1 | filled=0, blocked=198, silent=0 | filled=0, blocked=198, silent=0 |
| austin_rural | filled=0, blocked=244, silent=1 | filled=0, blocked=245, silent=0 | filled=0, blocked=245, silent=0 |
| austin_centre | filled=21, blocked=328, silent=0 (all LOW) | filled=20, blocked=329, silent=0 (all LOW) | filled=20, blocked=329, silent=0 (all LOW) |

**Widening the radius does not change the outcome for the 3 fully (100%)
NaN cells.** It shrinks the silent no-donor bucket toward zero (more distant
neighbours get found) but those newly-found neighbourhoods are *also* 100%
`height_m`-missing at any radius up to 1000 m, so they simply convert
silent-no-donor rows into MNAR-blocked rows — `n_filled` stays exactly 0 at
every radius tested for `nyc_suburban`, `nyc_rural`, `austin_rural`. This is
expected structurally: radius only controls *how many neighbours are found*,
not *whether those neighbours have the target column observed* — and in
these 3 cells, by construction, no building anywhere nearby has `height_m`.
Radius widening is a real (if partial) fix for the *silent-no-donor blind
spot itself* (turns silence into an explicit, auditable
`SPATIAL_CLUSTER_MNAR_BLOCKED` flag) but not for the underlying data gap.

For `austin_centre` (84.5% missing, i.e. real donors exist somewhere), a wider
radius modestly *increases* the fill count (15 → 21 at 250 m) but the
confidence tier **collapses to 100% LOW** at radius ≥ 250 m (vs. a
HIGH/MEDIUM/LOW mix of 3/7/5 at radius=100 m) — donors admitted at longer
range are less locally representative, which the confidence scoring correctly
penalises. Net: wider radius trades a few more filled rows for uniformly
lower confidence in this cell.

## Comparison arm — `imputation.py::impute_column`

| cell | `height_m` missing | `method="auto"` resolved to | outcome |
|---|---|---|---|
| nyc_suburban | 100.0% | `pde` (nan_mask.all()) | **raised** `ValueError("impute_column: bounds must be provided for PDE imputation on column 'height_m'.")` |
| nyc_rural | 100.0% | `pde` | **raised** same `ValueError` |
| austin_rural | 100.0% | `pde` | **raised** same `ValueError` |
| austin_centre | 84.5% | `kde` (not all-NaN, 64 observed values) | succeeded, filled all 349 NaN rows by resampling a KDE fit on the 64 observed `height_m` values (no bounds clamp applied since none supplied) |

Verbatim exception (identical across the 3 cells):
```
ValueError("impute_column: bounds must be provided for PDE imputation on column 'height_m'.")
```

For `austin_centre` the `kde` path succeeded because `nan_mask.all()` is
`False` (64/413 rows observed) — `impute_column`'s `"auto"` dispatch only
routes to `pde` at *exactly* 100% missing (F-04); 84.5% missing still takes
the `kde` branch and just resamples from whatever real observed distribution
exists in that cell, without regard to `config.IMPUTE_ML_METHOD_BY_TARGET`
or any spatial signal at all — it is a purely non-spatial, single-column
distributional fill, structurally distinct from `spatial_impute.py`'s
neighbour-based approach.

## Verdict — is "wire up the existing imputer" structurally viable as-is?

**No, not as-is, for the 3 fully-affected cells (`nyc_suburban`, `nyc_rural`,
`austin_rural`).** `knn_fill`'s own MNAR guard mechanically rejects (or, worse,
silently ignores via the no-donor gap) every single row in these 3 cells at
every radius tested up to 1000 m, because the guard is doing exactly what it
is designed to do: refuse to fill from a neighbourhood that is itself 100%
missing on the target column. This is not a bug in the guard — the data
genuinely offers no local donor signal within any tested radius. Widening the
radius alone cannot fix this without also crossing into a different cell's
data (which `spatial_impute.py` cannot do today — it is called per-cell,
one `GeoDataFrame` at a time, per F-06/F-07's identical-per-cell pipeline
structure) or admitting non-local (cross-city, cross-cluster) donors, which
is a different, larger design change than "wire up the existing imputer."
`impute_column`'s generic PDE/KDE path is also not viable unmodified: at
100% missing it structurally requires caller-supplied `bounds` (raises
otherwise) and even with bounds would only sample a prior distribution
untethered to any real observed height in that cell — not a meaningful fill,
just a documented placeholder draw.

**For `austin_centre` (84.5% missing), the existing infrastructure is
partially viable but weak.** `knn_fill` does fill 15/349 rows at production
defaults with a real HIGH/MEDIUM/LOW confidence mix, and 20-21/349 at wider
radii (confidence degrading to all-LOW). That leaves roughly 95% of this
cell's missing rows still MNAR-blocked or unfilled by `knn_fill` alone.
`impute_column`'s KDE path fills 100% of this cell's gap already today (no
wiring needed beyond calling it), but purely from the 64 observed values'
distribution — no spatial reasoning, no confidence tiering, no MNAR
awareness at all.

**What would have to change for "wire up the existing imputer" to become a
real fix path for the 3 fully-affected cells:**
1. The MNAR guard's neighbourhood scope would need to extend beyond the
   single cell's own `GeoDataFrame` — i.e. `knn_fill` (or its caller) would
   need to accept donor buildings from other cells/clusters of the same
   zone-type, not just the 100 m–1000 m radius *within* the same 100%-NaN
   cell. That is candidate fix shape (d) in the plan, and this test confirms
   it is necessary, not just one option among several, for these 3 cells.
2. Separately (and independently), the silent no-donor gap (6 rows in
   `nyc_rural`, 13 in `austin_rural` at radius=100 m) is a genuine
   diagnostics blind spot in `spatial_impute.py` itself — rows with zero
   neighbours in radius are neither filled nor flagged, which would need a
   code change (out of this investigation's scope) to surface explicitly,
   independent of whether the wider donor-pool question above is ever
   pursued.
3. For `austin_centre` specifically, no structural change is required to get
   *some* fill via the existing infrastructure — the open question is
   whether a KDE-resampled or MNAR-blocked-except-15/349 result is a good
   enough basis for Stage 6, which is a threshold/acceptance-criteria
   decision, not a further code change.

This is not an "inconclusive" result — every number above came from real
executed calls with no exceptions on the `knn_fill` path and a fully
reproduced, verbatim exception on the `impute_column` PDE path. The
conclusion (guard structurally rejects the 3 fully-affected cells at any
tested radius; partial/weak viability for the 84.5% cell) is directly
supported by that output.
