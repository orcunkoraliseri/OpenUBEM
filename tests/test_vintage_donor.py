"""T04 — year_built donor/neighbour vintage before oldest-default.

Input-Imputation arc, PINNED CONTRACT v2 (position-stable `resolve_vintage`).

Load-bearing properties:
  (1) a NaN-year building in a stratum of observed ~1995 buildings imputes a
      ~1995 vintage bin (HOTDECK_NEIGHBOR_* or GROUPMODE_MED), NOT DOERefPre1980;
  (2) an isolated NaN building with no same-stratum donors anywhere falls to the
      legacy oldest-default (DOERefPre1980 + VINTAGE_NAN_PERMISSIVE_DEFAULT);
  (3) tier-2 group-mode tie-break is deterministic under the fixed config seed;
  (4) a stratum whose local neighbourhood is majority-missing (MNAR, >=60%) does
      NOT spatial-fill (falls through to tier 2/3 instead).

Also covers the new `append_vintage_donor_flags` helper (idempotent `|`-append
of the per-row donor/tier token onto `data_quality_flag`).

Test geometry uses plain planar (x, y) coordinates well inside the production
`DEFAULT_RADIUS_M=100` convention — k/radius are never overridden here (T04
always calls `knn_fill` with T06's fixed defaults, per Rule 4 / zero-fitted-params).
"""
import numpy as np
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from openubem.config import RANDOM_SEED
from openubem.semantic.construction_sets import (
    append_vintage_donor_flags,
    resolve_vintage,
)


def _pt_gdf(rows):
    geoms = [Point(r.pop("x"), r.pop("y")) for r in rows]
    return gpd.GeoDataFrame(rows, geometry=geoms)


# ── (1) spatial/group-mode donor fills near the true stratum vintage ─────────

class TestDonorFillNear1995:
    def test_hotdeck_or_groupmode_fills_1995_not_pre1980(self):
        rows = [
            {"x": 1000, "y": 1000, "archetype_id": "MediumOffice", "year_built": float("nan")},
            {"x": 990,  "y": 1000, "archetype_id": "MediumOffice", "year_built": 1995.0},
            {"x": 1010, "y": 1000, "archetype_id": "MediumOffice", "year_built": 1995.0},
            {"x": 1000, "y": 990,  "archetype_id": "MediumOffice", "year_built": 1995.0},
            {"x": 1000, "y": 1010, "archetype_id": "MediumOffice", "year_built": 1995.0},
            {"x": 1005, "y": 1005, "archetype_id": "MediumOffice", "year_built": 1995.0},
            # different archetype nearby -- must NOT leak into the MediumOffice stratum
            {"x": 1001, "y": 1001, "archetype_id": "SmallOffice", "year_built": 2020.0},
            {"x": 999,  "y": 999,  "archetype_id": "SmallOffice", "year_built": 2021.0},
        ]
        gdf = _pt_gdf(rows)
        vintage, nan_rows, vintage_prov = resolve_vintage(gdf)

        assert 0 in nan_rows
        assert vintage.iloc[0] == "DOERef1980to2004", (
            f"expected the ~1995 bin, got {vintage.iloc[0]!r}"
        )
        assert vintage.iloc[0] != "DOERefPre1980"
        token = vintage_prov.loc[0]
        assert token in ("HOTDECK_NEIGHBOR_HIGH", "HOTDECK_NEIGHBOR_MED", "GROUPMODE_MED"), token


# ── (2) isolated NaN building, no donors anywhere -> legacy oldest-default ───

class TestIsolatedNoDonorFallsToOldestDefault:
    def test_isolated_falls_to_pre1980_permissive_default(self):
        rows = [
            {"x": 2000, "y": 2000, "archetype_id": "UniqueArchNoDonor", "year_built": float("nan")},
            # unrelated stratum elsewhere -- proves no cross-stratum leakage
            {"x": 0, "y": 0, "archetype_id": "MediumOffice", "year_built": 2000.0},
            {"x": 5, "y": 0, "archetype_id": "MediumOffice", "year_built": 2005.0},
        ]
        gdf = _pt_gdf(rows)
        vintage, nan_rows, vintage_prov = resolve_vintage(gdf)

        assert 0 in nan_rows
        assert vintage.iloc[0] == "DOERefPre1980"
        assert vintage_prov.loc[0] == "VINTAGE_NAN_PERMISSIVE_DEFAULT"

    def test_isolated_no_donor_flag_wired_through_append_helper(self):
        rows = [
            {"x": 2000, "y": 2000, "archetype_id": "UniqueArchNoDonor",
             "year_built": float("nan"), "data_quality_flag": ""},
        ]
        gdf = _pt_gdf(rows)
        vintage, nan_rows, vintage_prov = resolve_vintage(gdf)
        result = append_vintage_donor_flags(gdf, vintage_prov)
        assert "VINTAGE_NAN_PERMISSIVE_DEFAULT" in result.at[0, "data_quality_flag"]


# ── (3) determinism of the tier-2 group-mode tie-break under the fixed seed ──

class TestGroupModeDeterminism:
    def test_tied_stratum_mode_is_deterministic_across_calls(self):
        # No geometry column at all -> tier 1 is skipped entirely; forces tier 2.
        df = pd.DataFrame([
            {"archetype_id": "TiedArch", "year_built": float("nan")},
            {"archetype_id": "TiedArch", "year_built": 1995.0},  # -> DOERef1980to2004
            {"archetype_id": "TiedArch", "year_built": 2012.0},  # -> 90.1-2013 (1-1 tie)
        ])
        vintage_a, nan_rows_a, prov_a = resolve_vintage(df)
        vintage_b, nan_rows_b, prov_b = resolve_vintage(df)

        assert vintage_a.iloc[0] == vintage_b.iloc[0]
        assert prov_a.loc[0] == prov_b.loc[0] == "GROUPMODE_MED"
        assert vintage_a.iloc[0] in ("DOERef1980to2004", "90.1-2013")

    def test_default_rng_uses_config_random_seed(self):
        """Sanity: the tie-break rng really is seeded from config.RANDOM_SEED --
        reproduce it independently and confirm the same winner is picked."""
        df = pd.DataFrame([
            {"archetype_id": "TiedArch2", "year_built": float("nan")},
            {"archetype_id": "TiedArch2", "year_built": 1995.0},
            {"archetype_id": "TiedArch2", "year_built": 2012.0},
        ])
        vintage, _, prov = resolve_vintage(df)
        rng = np.random.default_rng(RANDOM_SEED)
        # value_counts() over ["DOERef1980to2004", "90.1-2013"] (insertion order
        # for a 1-1 tie is stable for identical input) -- reproduce the same pick.
        counts = pd.Series(["DOERef1980to2004", "90.1-2013"]).value_counts()
        winners = counts[counts == counts.max()].index.to_numpy()
        expected = winners[0] if len(winners) == 1 else winners[int(rng.integers(len(winners)))]
        assert vintage.iloc[0] == expected


# ── (4) MNAR majority-missing neighbourhood does NOT spatial-fill ───────────

class TestMnarBlocksSpatialFill:
    def test_majority_missing_stratum_falls_through_not_hotdeck(self):
        rows = [
            {"x": 0,  "y": 0, "archetype_id": "MnarArch", "year_built": float("nan")},  # target
            {"x": 10, "y": 0, "archetype_id": "MnarArch", "year_built": float("nan")},
            {"x": 20, "y": 0, "archetype_id": "MnarArch", "year_built": float("nan")},
            {"x": 30, "y": 0, "archetype_id": "MnarArch", "year_built": float("nan")},
            {"x": 40, "y": 0, "archetype_id": "MnarArch", "year_built": 1995.0},  # only donor
        ]
        gdf = _pt_gdf(rows)
        vintage, nan_rows, vintage_prov = resolve_vintage(gdf)

        assert 0 in nan_rows
        token = vintage_prov.loc[0]
        assert token not in ("HOTDECK_NEIGHBOR_HIGH", "HOTDECK_NEIGHBOR_MED"), (
            f"MNAR-majority-missing neighbourhood must not spatial-fill, got {token}"
        )
        # Falls through to tier 2 (one same-stratum observed donor exists) --
        # confirms the aspatial fallback actually fires rather than silently
        # dropping the row.
        assert token == "GROUPMODE_MED"
        assert vintage.iloc[0] == "DOERef1980to2004"


# ── append_vintage_donor_flags — idempotent multi-token append ──────────────

class TestAppendVintageDonorFlags:
    def test_appends_distinct_tokens_per_row(self):
        df = pd.DataFrame({
            "data_quality_flag": ["", "OTHER_FLAG"],
        })
        vintage_prov = pd.Series(
            {0: "HOTDECK_NEIGHBOR_HIGH", 1: "GROUPMODE_MED"},
        )
        result = append_vintage_donor_flags(df, vintage_prov)
        assert result.at[0, "data_quality_flag"] == "HOTDECK_NEIGHBOR_HIGH"
        assert result.at[1, "data_quality_flag"] == "OTHER_FLAG|GROUPMODE_MED"

    def test_idempotent_on_repeated_append(self):
        df = pd.DataFrame({"data_quality_flag": ["VINTAGE_NAN_PERMISSIVE_DEFAULT"]})
        vintage_prov = pd.Series({0: "VINTAGE_NAN_PERMISSIVE_DEFAULT"})
        result = append_vintage_donor_flags(df, vintage_prov)
        flag = result.at[0, "data_quality_flag"]
        assert flag.count("VINTAGE_NAN_PERMISSIVE_DEFAULT") == 1

    def test_no_nan_rows_returns_unchanged(self):
        df = pd.DataFrame({"data_quality_flag": ["OTHER_FLAG"]})
        vintage_prov = pd.Series(dtype=object)
        result = append_vintage_donor_flags(df, vintage_prov)
        assert result.at[0, "data_quality_flag"] == "OTHER_FLAG"
