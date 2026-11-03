"""T06 — spatial neighbour-fill utility + MNAR density filter.

Load-bearing properties:
  (1) a homogeneous, non-edge neighbourhood fills with full agreement -> HIGH confidence;
  (2) a neighbourhood >=60% missing on the target column DEACTIVATES the spatial fill
      (value stays unset) and appends SPATIAL_CLUSTER_MNAR_BLOCKED to data_quality_flag —
      the spatial value must NOT be used;
  (3) a building at the edge of the dataset's bounding box gets its confidence tier
      downgraded one notch vs. an otherwise-identical interior building;
  (4) mode-tie resolution is deterministic under a fixed seed.

Test radius/k are chosen for the synthetic 10 m grid scale below, not the production
default (`DEFAULT_RADIUS_M=100`, `DEFAULT_K=10`) — the production convention is fixed
and never swept; tests merely need internal consistency at a smaller spatial scale.
"""
import numpy as np
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from openubem.semantic.spatial_impute import (
    neighbour_vote, knn_fill, MNAR_BLOCKED_FLAG, DEFAULT_K, DEFAULT_RADIUS_M,
)

_RADIUS = 15.0
_K = 8


def _grid_gdf(col: str, values: dict, default="Office", spacing=10.0, n=5):
    """5x5 grid at (0,10,...,(n-1)*spacing) in both axes; `values` overrides
    {(gx, gy): value_or_None} on top of `default` for every other cell."""
    rows = []
    geoms = []
    for gy in range(n):
        for gx in range(n):
            x, y = gx * spacing, gy * spacing
            v = values.get((gx, gy), default)
            rows.append({col: v})
            geoms.append(Point(x, y))
    return gpd.GeoDataFrame(rows, geometry=geoms)


def _idx_of(gdf, x, y):
    match = gdf.index[(gdf.geometry.x == x) & (gdf.geometry.y == y)]
    assert len(match) == 1
    return match[0]


class TestNeighbourVoteHomogeneous:
    def test_interior_missing_fills_high_confidence(self):
        gdf = _grid_gdf("use_class", {(2, 2): None})  # center of 5x5 @ spacing10 -> (20,20)
        value, agreement, confidence, gdf_out = neighbour_vote(gdf, "use_class", k=_K, radius=_RADIUS)
        i = _idx_of(gdf, 20.0, 20.0)
        assert value.loc[i] == "Office"
        assert agreement.loc[i] == 1.0
        assert confidence.loc[i] == "HIGH"
        assert MNAR_BLOCKED_FLAG not in str(gdf_out.loc[i, "data_quality_flag"])

    def test_observed_rows_untouched(self):
        gdf = _grid_gdf("use_class", {(2, 2): None})
        value, agreement, confidence, _ = neighbour_vote(gdf, "use_class", k=_K, radius=_RADIUS)
        i = _idx_of(gdf, 0.0, 0.0)  # observed row, far from the missing center
        assert value.loc[i] is None
        assert pd.isna(agreement.loc[i])
        assert confidence.loc[i] is None


class TestKnnFillHomogeneous:
    def test_interior_missing_fills_high_confidence(self):
        gdf = _grid_gdf("height_m", {(2, 2): None}, default=30.0)
        value, dispersion, confidence, gdf_out = knn_fill(gdf, "height_m", k=_K, radius=_RADIUS)
        i = _idx_of(gdf, 20.0, 20.0)
        assert value.loc[i] == pytest.approx(30.0)
        assert dispersion.loc[i] == pytest.approx(0.0, abs=1e-9)
        assert confidence.loc[i] == "HIGH"
        assert MNAR_BLOCKED_FLAG not in str(gdf_out.loc[i, "data_quality_flag"])


class TestMNARGuard:
    def test_majority_missing_neighbourhood_blocks_spatial_fill(self):
        # center missing; of its 8 within-radius neighbours, 6 are ALSO missing (R=0.75>=0.60)
        overrides = {(2, 2): None}
        missing_neighbours = [(1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3)]
        for cell in missing_neighbours:
            overrides[cell] = None
        gdf = _grid_gdf("use_class", overrides)
        value, agreement, confidence, gdf_out = neighbour_vote(gdf, "use_class", k=_K, radius=_RADIUS)
        i = _idx_of(gdf, 20.0, 20.0)
        # the spatial value is NOT used
        assert value.loc[i] is None
        assert pd.isna(agreement.loc[i])
        assert confidence.loc[i] is None
        assert MNAR_BLOCKED_FLAG in str(gdf_out.loc[i, "data_quality_flag"])

    def test_majority_missing_neighbourhood_blocks_knn_fill(self):
        overrides = {(2, 2): None}
        missing_neighbours = [(1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3)]
        for cell in missing_neighbours:
            overrides[cell] = None
        gdf = _grid_gdf("height_m", overrides, default=30.0)
        value, dispersion, confidence, gdf_out = knn_fill(gdf, "height_m", k=_K, radius=_RADIUS)
        i = _idx_of(gdf, 20.0, 20.0)
        assert pd.isna(value.loc[i])
        assert confidence.loc[i] is None
        assert MNAR_BLOCKED_FLAG in str(gdf_out.loc[i, "data_quality_flag"])

    def test_below_threshold_missing_neighbourhood_not_blocked(self):
        # only 2 of 8 neighbours missing (R=0.25<0.60) -> fill proceeds normally
        gdf = _grid_gdf("use_class", {(2, 2): None, (1, 1): None, (3, 3): None})
        value, agreement, confidence, gdf_out = neighbour_vote(gdf, "use_class", k=_K, radius=_RADIUS)
        i = _idx_of(gdf, 20.0, 20.0)
        assert value.loc[i] == "Office"
        assert MNAR_BLOCKED_FLAG not in str(gdf_out.loc[i, "data_quality_flag"])


class TestEdgeOfBboxDowngrade:
    def test_corner_building_confidence_downgraded_vs_interior(self):
        gdf = _grid_gdf("use_class", {(2, 2): None, (0, 0): None})
        value, agreement, confidence, _ = neighbour_vote(gdf, "use_class", k=_K, radius=_RADIUS)
        interior = _idx_of(gdf, 20.0, 20.0)
        corner = _idx_of(gdf, 0.0, 0.0)
        # both have full-agreement neighbourhoods (all real "Office" donors)
        assert agreement.loc[interior] == 1.0
        assert agreement.loc[corner] == 1.0
        assert confidence.loc[interior] == "HIGH"
        assert confidence.loc[corner] == "MEDIUM"  # downgraded one tier at the bbox edge


class TestDeterminism:
    def test_tie_break_reproducible_under_fixed_seed(self):
        # center's 8 within-radius neighbours split 4/4 between two use_classes -> a tie
        overrides = {(2, 2): None}
        retail_cells = [(1, 1), (2, 1), (3, 1), (1, 2)]
        for cell in retail_cells:
            overrides[cell] = "Retail"
        gdf = _grid_gdf("use_class", overrides)  # remaining 4 neighbours stay "Office"
        i = _idx_of(gdf, 20.0, 20.0)

        winners = set()
        for _ in range(5):
            value, _, _, _ = neighbour_vote(
                gdf, "use_class", k=_K, radius=_RADIUS, rng=np.random.default_rng(42)
            )
            winners.add(value.loc[i])
        assert len(winners) == 1  # same seed -> same tie-break every time

    def test_default_rng_uses_config_seed_reproducibly(self):
        overrides = {(2, 2): None}
        retail_cells = [(1, 1), (2, 1), (3, 1), (1, 2)]
        for cell in retail_cells:
            overrides[cell] = "Retail"
        gdf = _grid_gdf("use_class", overrides)
        i = _idx_of(gdf, 20.0, 20.0)

        value1, _, _, _ = neighbour_vote(gdf, "use_class", k=_K, radius=_RADIUS)
        value2, _, _, _ = neighbour_vote(gdf, "use_class", k=_K, radius=_RADIUS)
        assert value1.loc[i] == value2.loc[i]


class TestPublishedConventionDefaults:
    def test_defaults_are_fixed_not_zero(self):
        assert DEFAULT_K == 10
        assert DEFAULT_RADIUS_M == 100.0
