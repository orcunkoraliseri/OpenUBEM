"""T08 — Mask-and-recover + spatial-block hold-out harness
(`openubem/validation/mask_recover.py`).

Input-Imputation arc, Phase B. Pure-evaluation harness consuming the T07
`impute_missing` orchestrator -- report, do NOT tune (M09 §4). No EUI here.

Load-bearing properties under test:
  (1) complete-case filter drops any row with an unobserved target (no
      leakage donor pool);
  (2) spatial blocks are NOT a random row split -- an existing usable
      postcode/block column is preferred; else blocks are derived from
      geometry centroids; a whole BLOCK is held out, never split rows;
  (3) masking sets exactly the held-out rows/targets to NaN and preserves
      the ground truth for scoring;
  (4) continuous metrics (MAE/RMSE/KS/Wasserstein) are computed correctly on
      hand-built arrays with known values;
  (5) categorical metrics (PFC/log-loss) are computed correctly on hand-built
      arrays with known values;
  (6) the FIDELITY CHECK BITES: a mean-fill (variance-collapse) imputer
      scores WORSE on KS than a KDE fill against the same true held-out
      distribution -- proving the distributional metric actually
      distinguishes the two (not just point error);
  (7) end-to-end `mask_and_recover` on a synthetic spatial grid returns
      continuous scores for year_built/levels/height_m, and now also a real
      `{pfc, log_loss, n}` dict for the categorical `use_class` target --
      T07.2 generalized `impute_missing`'s spatial (`neighbour_vote`) and
      statistical (group-mode) tiers to route categorical attributes, so
      the T08 NOT_SCORABLE finding is resolved.
"""
import math

import numpy as np
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from openubem.config import RANDOM_SEED
from openubem.semantic.imputation import impute_column
from openubem.validation import mask_recover as mr


def _pt_gdf(rows):
    geoms = [Point(r.pop("x"), r.pop("y")) for r in rows]
    return gpd.GeoDataFrame(rows, geometry=geoms)


def _grid_gdf(n_side=8, spacing=10.0, base_year=1950.0, year_span=70.0):
    """8x8 spatial grid, 64 complete-case rows, real per-attribute spread."""
    rows = []
    i = 0
    for gy in range(n_side):
        for gx in range(n_side):
            levels = 1 + (i % 6)
            rows.append({
                "x": gx * spacing,
                "y": gy * spacing,
                "year_built": base_year + i * year_span / (n_side * n_side - 1),
                "levels": float(levels),
                "height_m": float(levels) * 3.5,
                "use_class": "office" if i % 2 == 0 else "residential",
                "archetype_id": "office" if i % 2 == 0 else "residential",
            })
            i += 1
    return _pt_gdf(rows)


# ── (1) complete-case filter -- no leakage donor pool ────────────────────────

class TestCompleteCases:
    def test_drops_any_row_missing_a_target(self):
        df = pd.DataFrame({
            "year_built": [1990.0, float("nan"), 2000.0],
            "levels": [2.0, 3.0, float("nan")],
        })
        cc = mr.complete_cases(df, ["year_built", "levels"])
        assert list(cc.index) == [0]

    def test_all_complete_returns_all_rows(self):
        df = pd.DataFrame({"year_built": [1990.0, 2000.0], "levels": [2.0, 3.0]})
        cc = mr.complete_cases(df, ["year_built", "levels"])
        assert len(cc) == 2


# ── (2) spatial block assignment -- NOT a random row split ──────────────────

class TestAssignSpatialBlocks:
    def test_usable_postcode_column_is_used_directly(self):
        df = pd.DataFrame({"postcode": ["A", "A", "B", "B"]})
        blocks = mr.assign_spatial_blocks(df)
        assert list(blocks) == ["A", "A", "B", "B"]

    def test_blank_postcode_falls_back_to_geometry_grid(self):
        rows = [
            {"x": 0, "y": 0, "postcode": ""},
            {"x": 1, "y": 0, "postcode": ""},
            {"x": 100, "y": 100, "postcode": ""},
            {"x": 101, "y": 100, "postcode": ""},
        ]
        gdf = _pt_gdf(rows)
        blocks = mr.assign_spatial_blocks(gdf)
        # two well-separated clusters -> exactly 2 distinct blocks; clusters
        # never mix.
        assert blocks.iloc[0] == blocks.iloc[1]
        assert blocks.iloc[2] == blocks.iloc[3]
        assert blocks.iloc[0] != blocks.iloc[2]

    def test_explicit_block_col_overrides_postcode(self):
        df = pd.DataFrame({
            "postcode": ["X", "X", "Y", "Y"],
            "myblock": ["1", "2", "1", "2"],
        })
        blocks = mr.assign_spatial_blocks(df, block_col="myblock")
        assert list(blocks) == ["1", "2", "1", "2"]

    def test_no_usable_key_and_no_geometry_raises(self):
        df = pd.DataFrame({"year_built": [1990.0, 2000.0]})
        with pytest.raises(ValueError):
            mr.assign_spatial_blocks(df)


# ── whole-BLOCK holdout (never split rows within a block) ───────────────────

class TestSpatialBlockHoldout:
    def test_holdout_never_splits_a_block(self):
        gdf = _grid_gdf()
        train_idx, holdout_idx, blocks = mr.spatial_block_holdout(
            gdf, rng=np.random.default_rng(RANDOM_SEED)
        )
        train_blocks = set(blocks.loc[train_idx])
        holdout_blocks = set(blocks.loc[holdout_idx])
        assert train_blocks.isdisjoint(holdout_blocks)

    def test_holdout_is_roughly_20_percent_of_rows(self):
        gdf = _grid_gdf()
        train_idx, holdout_idx, _ = mr.spatial_block_holdout(
            gdf, rng=np.random.default_rng(RANDOM_SEED)
        )
        frac = len(holdout_idx) / len(gdf)
        assert 0.05 < frac < 0.40  # whole-block granularity, not exact 20%
        assert len(train_idx) + len(holdout_idx) == len(gdf)

    def test_deterministic_under_fixed_seed(self):
        gdf = _grid_gdf()
        _, h1, _ = mr.spatial_block_holdout(gdf, rng=np.random.default_rng(RANDOM_SEED))
        _, h2, _ = mr.spatial_block_holdout(gdf, rng=np.random.default_rng(RANDOM_SEED))
        assert list(h1) == list(h2)


# ── (3) masking -- exactly the held-out rows/targets go to NaN ──────────────

class TestMaskTargets:
    def test_masks_only_holdout_rows_and_preserves_truth(self):
        gdf = _grid_gdf()
        _, holdout_idx, _ = mr.spatial_block_holdout(gdf, rng=np.random.default_rng(RANDOM_SEED))
        masked, truth = mr.mask_targets(gdf, holdout_idx, ["year_built", "levels"])

        assert masked.loc[holdout_idx, ["year_built", "levels"]].isna().all(axis=None)
        train_idx = gdf.index.difference(holdout_idx)
        assert not masked.loc[train_idx, ["year_built", "levels"]].isna().any(axis=None)
        pd.testing.assert_frame_equal(truth, gdf.loc[holdout_idx, ["year_built", "levels"]])


# ── (4) continuous metric primitives -- hand-computed values ────────────────

class TestContinuousMetrics:
    def test_mae_rmse_hand_computed(self):
        y_true = [1.0, 2.0, 3.0]
        y_pred = [1.0, 4.0, 3.0]
        assert mr.mae(y_true, y_pred) == pytest.approx(2.0 / 3.0)
        assert mr.rmse(y_true, y_pred) == pytest.approx(math.sqrt(4.0 / 3.0))

    def test_ks_zero_for_identical_distributions(self):
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert mr.ks_statistic(y, y) == pytest.approx(0.0)

    def test_ks_one_for_fully_disjoint_distributions(self):
        y_true = [0.0, 0.0, 0.0, 0.0]
        y_pred = [10.0, 10.0, 10.0, 10.0]
        assert mr.ks_statistic(y_true, y_pred) == pytest.approx(1.0)

    def test_wasserstein_between_two_point_masses_is_the_gap(self):
        y_true = [0.0, 0.0, 0.0]
        y_pred = [5.0, 5.0, 5.0]
        assert mr.wasserstein(y_true, y_pred) == pytest.approx(5.0)

    def test_score_continuous_bundles_all_metrics(self):
        y_true = [1.0, 2.0, 3.0]
        y_pred = [1.0, 2.0, 3.0]
        out = mr.score_continuous(y_true, y_pred)
        assert set(out) == {"mae", "rmse", "ks_stat", "wasserstein", "n"}
        assert out["mae"] == pytest.approx(0.0)
        assert out["n"] == 3


# ── (5) categorical metric primitives -- hand-computed values ───────────────

class TestCategoricalMetrics:
    def test_pfc_hand_computed(self):
        y_true = ["a", "b", "a", "b"]
        y_pred = ["a", "a", "a", "b"]
        assert mr.pfc(y_true, y_pred) == pytest.approx(0.25)

    def test_one_hot_proba_smoothed_values(self):
        proba = mr.one_hot_proba(["a", "b"], classes=["a", "b"], eps=0.001)
        assert proba[0, 0] == pytest.approx(0.999)
        assert proba[0, 1] == pytest.approx(0.001)
        assert proba[1, 1] == pytest.approx(0.999)

    def test_log_loss_hand_computed(self):
        classes = ["a", "b"]
        proba = np.array([[0.9, 0.1], [0.2, 0.8]])
        y_true = ["a", "b"]
        expected = -(math.log(0.9) + math.log(0.8)) / 2.0
        assert mr.log_loss(y_true, proba, classes) == pytest.approx(expected)

    def test_score_categorical_bundles_pfc_and_log_loss(self):
        y_true = ["a", "b", "a"]
        y_pred = ["a", "a", "a"]
        out = mr.score_categorical(y_true, y_pred, classes=["a", "b"])
        assert set(out) == {"pfc", "log_loss", "n"}
        assert out["pfc"] == pytest.approx(1.0 / 3.0)
        assert out["n"] == 3


# ── (6) THE FIDELITY CHECK BITES ─────────────────────────────────────────────

class TestFidelityCheckBites:
    def test_mean_fill_scores_worse_on_ks_than_kde_fill(self):
        observed = pd.Series([1950.0 + 2.0 * i for i in range(40)])  # real spread, not constant
        rng_mask = np.random.default_rng(RANDOM_SEED)
        holdout_pos = rng_mask.choice(len(observed), size=10, replace=False)
        true_holdout = observed.iloc[holdout_pos].to_numpy()

        series_with_gaps = observed.copy()
        series_with_gaps.iloc[holdout_pos] = np.nan
        train_values = series_with_gaps.dropna()

        mean_fill = np.full(len(holdout_pos), train_values.mean())
        kde_fill = impute_column(
            series_with_gaps, method="kde", rng=np.random.default_rng(RANDOM_SEED)
        ).iloc[holdout_pos].to_numpy()

        ks_mean = mr.ks_statistic(true_holdout, mean_fill)
        ks_kde = mr.ks_statistic(true_holdout, kde_fill)

        assert ks_mean > ks_kde, (
            f"fidelity check did not bite: mean-fill KS={ks_mean} not > kde-fill KS={ks_kde}"
        )


# ── (7) end-to-end mask_and_recover ──────────────────────────────────────────

class TestMaskAndRecoverEndToEnd:
    def test_continuous_targets_scored_categorical_not_scorable(self):
        gdf = _grid_gdf()
        result = mr.mask_and_recover(
            gdf,
            continuous_targets=["year_built", "levels", "height_m"],
            categorical_targets=["use_class"],
            rng=np.random.default_rng(RANDOM_SEED),
        )

        assert result["n_complete_cases"] == len(gdf)
        assert result["n_holdout"] > 0
        assert result["n_blocks_holdout"] >= 1

        for attr in ("year_built", "levels", "height_m"):
            scores = result["continuous"][attr]
            assert set(scores) == {"mae", "rmse", "ks_stat", "wasserstein", "n"}
            assert scores["n"] == result["n_holdout"]
            assert scores["mae"] >= 0.0
            assert 0.0 <= scores["ks_stat"] <= 1.0

        # T07.2 resolved the T08 NOT_SCORABLE finding: use_class is now
        # routable, so a real categorical score dict comes back.
        cat = result["categorical"]["use_class"]
        assert set(cat) == {"pfc", "log_loss", "n"}
        assert cat["n"] == result["n_holdout"]
        assert cat["pfc"] >= 0.0
        assert cat["log_loss"] >= 0.0

    def test_no_eui_anywhere_in_the_result(self):
        gdf = _grid_gdf()
        result = mr.mask_and_recover(
            gdf, continuous_targets=["year_built"], rng=np.random.default_rng(RANDOM_SEED)
        )
        assert "eui" not in str(result).lower()
