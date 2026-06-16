"""T09 — tests for R6 re-scoring engine.

Uses a tiny synthetic CBECS reference and small fixture CSV.
Does NOT depend on the full CBECS download or the 12 live cell CSVs.
"""
from __future__ import annotations

import importlib
import json
import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

REPO = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Helpers to import the engine without triggering side-effects
# ---------------------------------------------------------------------------

def _import_engine():
    import sys
    sys.path.insert(0, str(REPO))
    import scripts.validation.r6_rescore_cells as eng
    return eng


# ---------------------------------------------------------------------------
# Tiny synthetic fixtures
# ---------------------------------------------------------------------------

def _make_ref_df(n: int = 30, pba_code: int = 15, eui_mean: float = 800.0) -> pd.DataFrame:
    """Synthetic region reference: n rows all PBA=pba_code, EUI ~N(eui_mean,50)."""
    rng = np.random.default_rng(42)
    euis = rng.normal(eui_mean, 50, n).clip(50, 3000)
    return pd.DataFrame({
        "pba_code": [pba_code] * n,
        "pba_label": ["Food service"] * n,
        "sqft": [5000] * n,
        "eui_kwh_m2": euis,
        "finalwt": rng.uniform(10, 100, n),
    })


def _make_ref_df_offices(n: int = 30) -> pd.DataFrame:
    """Synthetic reference with PBA=2 (office) EUIs ~N(250,30)."""
    rng = np.random.default_rng(7)
    euis = rng.normal(250, 30, n).clip(50, 800)
    return pd.DataFrame({
        "pba_code": [2] * n,
        "pba_label": ["Office"] * n,
        "sqft": [20000] * n,
        "eui_kwh_m2": euis,
        "finalwt": rng.uniform(10, 100, n),
    })


def _make_pba_map_subset() -> dict:
    """Minimal PBA map covering archetypes used in tests."""
    return {
        "QuickServiceRestaurant": 15,
        "FullServiceRestaurant": 15,
        "MediumOffice": 2,
        "MidriseApartment": None,
        "HighriseApartment": None,
        "SmallDataCenterHighITE": None,
        "OpenUBEMUnknown": "distribution_only",
    }


# ---------------------------------------------------------------------------
# T09 tests
# ---------------------------------------------------------------------------

class TestDeriveArchetypeBands:
    def test_qsr_band_derived_from_pba15(self):
        eng = _import_engine()
        ref = _make_ref_df(n=30, pba_code=15, eui_mean=800)
        pba_map = _make_pba_map_subset()
        bands = eng.derive_archetype_bands(ref, pba_map)
        assert "QuickServiceRestaurant" in bands
        lo, hi = bands["QuickServiceRestaurant"]
        assert lo > 0 and hi > lo
        assert hi > 200  # food service should have high upper band

    def test_midrise_apartment_not_in_bands(self):
        """Null-PBA archetype → generic fallback (not in returned dict)."""
        eng = _import_engine()
        ref = _make_ref_df(n=30)
        pba_map = _make_pba_map_subset()
        bands = eng.derive_archetype_bands(ref, pba_map)
        assert "MidriseApartment" not in bands

    def test_openubem_unknown_not_in_bands(self):
        """distribution_only → generic fallback."""
        eng = _import_engine()
        ref = _make_ref_df(n=30)
        pba_map = _make_pba_map_subset()
        bands = eng.derive_archetype_bands(ref, pba_map)
        assert "OpenUBEMUnknown" not in bands

    def test_data_centres_not_in_bands(self):
        """Null-PBA data centre archetypes → generic fallback."""
        eng = _import_engine()
        ref = _make_ref_df(n=30)
        pba_map = _make_pba_map_subset()
        bands = eng.derive_archetype_bands(ref, pba_map)
        assert "SmallDataCenterHighITE" not in bands

    def test_fewer_than_10_rows_falls_back(self):
        """PBA with < 10 reference rows → not in returned dict (generic fallback)."""
        eng = _import_engine()
        ref = _make_ref_df(n=8, pba_code=15)  # only 8 rows
        pba_map = {"QuickServiceRestaurant": 15}
        bands = eng.derive_archetype_bands(ref, pba_map)
        assert "QuickServiceRestaurant" not in bands

    def test_deterministic(self):
        """Same inputs always produce same bands."""
        eng = _import_engine()
        ref = _make_ref_df(n=30, pba_code=15)
        pba_map = _make_pba_map_subset()
        b1 = eng.derive_archetype_bands(ref, pba_map)
        b2 = eng.derive_archetype_bands(ref, pba_map)
        assert b1 == b2


class TestCellRegionMapping:
    def test_nyc_cells_map_to_middle_atlantic(self):
        eng = _import_engine()
        for cell in ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural"]:
            assert eng.CELL_REGION[cell] == "middle_atlantic"

    def test_la_cells_map_to_pacific(self):
        eng = _import_engine()
        for cell in ["la_centre", "la_urban", "la_suburban", "la_rural"]:
            assert eng.CELL_REGION[cell] == "pacific"

    def test_austin_cells_map_to_west_south_central(self):
        eng = _import_engine()
        for cell in ["austin_centre", "austin_urban", "austin_suburban", "austin_rural"]:
            assert eng.CELL_REGION[cell] == "west_south_central"


class TestPlausibilityCompute:
    def _make_gdf(self, euis: list[float], archetypes: list[str]) -> gpd.GeoDataFrame:
        rows = [
            {
                "osm_id": str(i),
                "archetype_id": a,
                "eui_kwh_m2": e,
                "simulation_status": "success",
                "geometry": Point(0, 0),
            }
            for i, (e, a) in enumerate(zip(euis, archetypes))
        ]
        return gpd.GeoDataFrame(rows, crs="EPSG:4326")

    def test_qsr_outliers_enter_archetype_band(self):
        """QSR buildings above 1000 kWh/m² enter the archetype band (>= generic)."""
        eng = _import_engine()
        ref = _make_ref_df(n=30, pba_code=15, eui_mean=1000)
        pba_map = _make_pba_map_subset()
        bands = eng.derive_archetype_bands(ref, pba_map)

        # 5 QSR buildings at ~1100 kWh/m² + 5 office buildings at ~250 kWh/m²
        euis = [1100.0] * 5 + [250.0] * 5
        archetypes = ["QuickServiceRestaurant"] * 5 + ["MediumOffice"] * 5
        gdf = self._make_gdf(euis, archetypes)

        gen_pct, arch_pct = eng._compute_plausibility(gdf, pba_map, bands)
        # Generic: 5/10 QSR above 1000 are outliers → 50% inside
        assert gen_pct == pytest.approx(50.0)
        # Archetype-aware: QSR in food-service band (high upper bound) → should be >=
        assert arch_pct >= gen_pct

    def test_apartments_included_in_generic_denominator(self):
        """Null-PBA archetypes contribute to the generic plausibility denominator.

        The generic band reproduces R5 F12: ALL parsed buildings with non-null EUI,
        no archetype exclusion (bug-fix 2026-06-15). Apartments fall back to the
        generic [25,1000] band since they have no PBA-derived archetype band.
        """
        eng = _import_engine()
        pba_map = _make_pba_map_subset()
        bands = {}
        # 3 apartments with EUIs inside [25,1000] → generic_pct = 100%, not 0%
        euis = [200.0, 300.0, 400.0]
        archetypes = ["MidriseApartment"] * 3
        gdf = self._make_gdf(euis, archetypes)
        gen_pct, arch_pct = eng._compute_plausibility(gdf, pba_map, bands)
        assert gen_pct == pytest.approx(100.0), (
            f"Apartments should be included in generic denominator; got {gen_pct}"
        )
        assert arch_pct >= gen_pct

    def test_generic_pct_unaffected_by_archetype_exclusion(self):
        """Generic plausibility must match the no-exclusion value even when excluding apartments changes it.

        This is the key R5 F12 reproduction test: on a fixture where null-PBA exclusion
        would change the %, generic_pct must match the no-exclusion value.
        """
        eng = _import_engine()
        pba_map = _make_pba_map_subset()
        bands = {}
        # 4 apartments (EUI=500, inside [25,1000]) + 1 QSR (EUI=1500, outside [25,1000])
        # With no exclusion: generic_pct = 4/5 = 80%
        # With apartment exclusion (old bug): only QSR counted → 0/1 = 0%
        euis = [500.0] * 4 + [1500.0]
        archetypes = ["MidriseApartment"] * 4 + ["QuickServiceRestaurant"]
        gdf = self._make_gdf(euis, archetypes)
        gen_pct, arch_pct = eng._compute_plausibility(gdf, pba_map, bands)
        assert gen_pct == pytest.approx(80.0), (
            f"Generic pct must be 4/5=80% (no exclusion); got {gen_pct}"
        )
        assert arch_pct >= gen_pct

    def test_archetype_pct_gte_generic_pct(self):
        """Archetype-aware plausibility must be >= generic for any mix of archetypes."""
        eng = _import_engine()
        ref = _make_ref_df(n=30, pba_code=15, eui_mean=1000)
        pba_map = _make_pba_map_subset()
        bands = eng.derive_archetype_bands(ref, pba_map)

        rng = np.random.default_rng(99)
        euis = rng.uniform(800, 1500, 20).tolist()
        archetypes = (["QuickServiceRestaurant"] * 10 + ["MediumOffice"] * 10)
        gdf = self._make_gdf(euis, archetypes)
        gen_pct, arch_pct = eng._compute_plausibility(gdf, pba_map, bands)
        assert arch_pct >= gen_pct


class TestSummaryCsvPresence:
    def test_summary_csv_has_12_rows(self):
        """r6_rescore_summary.csv must have exactly 12 rows (one per cell)."""
        summary_path = (
            REPO / "docs" / "validations" / "overAll" / "results" / "r6_rescore_summary.csv"
        )
        assert summary_path.exists(), f"Summary CSV not found: {summary_path}"
        df = pd.read_csv(summary_path)
        assert len(df) == 12, f"Expected 12 rows, got {len(df)}"

    def test_summary_csv_has_required_columns(self):
        summary_path = (
            REPO / "docs" / "validations" / "overAll" / "results" / "r6_rescore_summary.csv"
        )
        df = pd.read_csv(summary_path)
        required = {
            "cell", "region", "n_success",
            "cv_rmse_ne", "cv_rmse_r6",
            "nmbe_ne", "nmbe_r6",
            "r2_ne", "r2_r6",
            "ks_d_ne", "ks_d_r6",
            "plaus_generic_pct", "plaus_archetype_pct",
        }
        missing = required - set(df.columns)
        assert not missing, f"Missing columns: {missing}"


class TestNoCoreModuleMutation:
    def test_import_does_not_mutate_openubem_results(self):
        """Importing the engine must not alter openubem.results module state."""
        import sys
        sys.path.insert(0, str(REPO))

        import openubem.results as core_before
        cv_thresh_before = core_before._CV_RMSE_THRESHOLD
        r2_thresh_before = core_before._R2_THRESHOLD

        # Import engine
        import scripts.validation.r6_rescore_cells  # noqa: F401

        import importlib
        core_after = importlib.import_module("openubem.results")
        assert core_after._CV_RMSE_THRESHOLD == cv_thresh_before
        assert core_after._R2_THRESHOLD == r2_thresh_before


class TestArchetypeAwarePctGeqGeneric:
    """For every cell in the summary CSV, archetype_pct >= generic_pct."""
    def test_all_cells(self):
        summary_path = (
            REPO / "docs" / "validations" / "overAll" / "results" / "r6_rescore_summary.csv"
        )
        df = pd.read_csv(summary_path)
        for _, row in df.iterrows():
            assert row["plaus_archetype_pct"] >= row["plaus_generic_pct"], (
                f"{row['cell']}: archetype={row['plaus_archetype_pct']:.2f} < "
                f"generic={row['plaus_generic_pct']:.2f}"
            )
