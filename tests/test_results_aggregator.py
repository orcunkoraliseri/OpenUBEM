"""Unit + smoke tests for openubem.results aggregator, orchestrator, and visualization (T11)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

# ── Fixtures ─────────────────────────────────────────────────────────────────

GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden_sql"
_EPSG_UTM = "EPSG:32618"  # UTM Zone 18N (Boston area)


def _make_polygon(x_offset: float = 0.0) -> Polygon:
    """Small rectangular footprint in UTM coords."""
    return Polygon([
        (330000 + x_offset, 4690000),
        (330014 + x_offset, 4690000),
        (330014 + x_offset, 4690014),
        (330000 + x_offset, 4690014),
    ])


def _make_enriched_gdf(n: int = 3) -> gpd.GeoDataFrame:
    """Minimal 57-col-ish enriched GDF with the columns parser/aggregator need."""
    rows = []
    for i in range(n):
        rows.append({
            "osm_id": f"way/TEST{i}",
            "footprint_area_m2": 196.0,
            "levels": 2.0,
            "height_m": float("nan"),
            "archetype_id": "SmallOffice" if i % 2 == 0 else "MidriseApartment",
            "climate_zone": "5A",
            "data_quality_flag": "",
            "geometry": _make_polygon(x_offset=float(i * 100)),
        })
    return gpd.GeoDataFrame(rows, crs=_EPSG_UTM)


def _make_metrics_df(n: int = 3, include_failed: bool = True) -> pd.DataFrame:
    """Synthetic metrics rows (T11 tests): 2 success + 1 failed.

    Phase-E (T14): includes all 28 _STEP5_COLS columns.
    """
    rows = []
    for i in range(n):
        if include_failed and i == n - 1:
            nan = float("nan")
            rows.append({
                "osm_id": f"way/TEST{i}",
                "simulation_status": "failed_parse",
                "error_summary": "missing required EUI variable: Zone Lights Electricity Energy",
                "heating_eui_kwh_m2": nan, "cooling_eui_kwh_m2": nan,
                "lighting_eui_kwh_m2": nan, "equipment_eui_kwh_m2": nan,
                "fans_eui_kwh_m2": nan, "pumps_eui_kwh_m2": nan,
                "dhw_gas_eui_kwh_m2": nan, "dhw_elec_eui_kwh_m2": nan, "dhw_eui_kwh_m2": nan,
                "cooking_eui_kwh_m2": nan, "refrigeration_eui_kwh_m2": nan,
                "total_eui_kwh_m2": nan,
                "gwp_heating_kgco2_m2": nan, "gwp_cooling_kgco2_m2": nan,
                "gwp_lighting_kgco2_m2": nan, "gwp_equipment_kgco2_m2": nan,
                "gwp_fans_kgco2_m2": nan, "gwp_pumps_kgco2_m2": nan,
                "gwp_dhw_kgco2_m2": nan, "gwp_cooking_kgco2_m2": nan,
                "gwp_refrigeration_kgco2_m2": nan, "gwp_total_kgco2_m2": nan,
                "iod": nan, "data_quality_flag": "",
            })
        else:
            rows.append({
                "osm_id": f"way/TEST{i}",
                "simulation_status": "success",
                "error_summary": "",
                "heating_eui_kwh_m2": 60.0 + i * 5,
                "cooling_eui_kwh_m2": 80.0 + i * 5,
                "lighting_eui_kwh_m2": 10.0,
                "equipment_eui_kwh_m2": 20.0,
                "fans_eui_kwh_m2": 5.0 + i * 0.5,
                "pumps_eui_kwh_m2": 2.0,
                "dhw_gas_eui_kwh_m2": 8.0,
                "dhw_elec_eui_kwh_m2": 1.0,
                "dhw_eui_kwh_m2": 9.0,
                "cooking_eui_kwh_m2": 3.0,
                "refrigeration_eui_kwh_m2": 0.0,
                "total_eui_kwh_m2": 170.0 + i * 10,
                "gwp_heating_kgco2_m2": 11.0,
                "gwp_cooling_kgco2_m2": 31.0,
                "gwp_lighting_kgco2_m2": 3.9,
                "gwp_equipment_kgco2_m2": 7.8,
                "gwp_fans_kgco2_m2": 1.9,
                "gwp_pumps_kgco2_m2": 0.8,
                "gwp_dhw_kgco2_m2": 1.9,
                "gwp_cooking_kgco2_m2": 0.5,
                "gwp_refrigeration_kgco2_m2": 0.0,
                "gwp_total_kgco2_m2": 59.8,
                "iod": 0.3 + i * 0.1,
                "data_quality_flag": "",
            })
    return pd.DataFrame(rows)


# ── T11: join_results ─────────────────────────────────────────────────────────

class TestJoinResults:
    def test_output_shape_core_cols_present(self):
        """F9: join appends _STEP5_COLS to the enriched GDF; spot-check key columns present."""
        from openubem.results.aggregator import join_results
        gdf = _make_enriched_gdf(3)
        metrics = _make_metrics_df(3)
        result = join_results(gdf, metrics)
        # Phase-E spot-check: core + new service-load columns
        spot_check = {"heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
                      "equipment_eui_kwh_m2", "fans_eui_kwh_m2", "pumps_eui_kwh_m2",
                      "dhw_eui_kwh_m2", "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2",
                      "total_eui_kwh_m2", "gwp_total_kgco2_m2",
                      "iod", "simulation_status", "error_summary"}
        for col in spot_check:
            assert col in result.columns, f"Missing col: {col}"

    def test_step5_cols_appended(self):
        """F9: exactly the _STEP5_COLS columns are appended, no extras from metrics."""
        from openubem.results.aggregator import join_results, _STEP5_COLS
        gdf = _make_enriched_gdf(3)
        upstream_cols = set(gdf.columns)
        metrics = _make_metrics_df(3)
        result = join_results(gdf, metrics)
        new_cols = set(result.columns) - upstream_cols
        assert new_cols == set(_STEP5_COLS), f"Extra or missing: {new_cols ^ set(_STEP5_COLS)}"

    def test_failed_building_present_with_nan(self):
        """Flag-don't-drop: failed building appears in result with NaN EUI."""
        from openubem.results.aggregator import join_results
        gdf = _make_enriched_gdf(3)
        metrics = _make_metrics_df(3, include_failed=True)
        result = join_results(gdf, metrics)
        failed = result[result["simulation_status"] == "failed_parse"]
        assert len(failed) == 1
        assert math.isnan(float(failed.iloc[0]["total_eui_kwh_m2"]))

    def test_not_simulated_status_for_missing(self):
        """Buildings with no metrics row get simulation_status='not_simulated'."""
        from openubem.results.aggregator import join_results
        gdf = _make_enriched_gdf(4)  # 4 buildings
        metrics = _make_metrics_df(3)  # only 3 metric rows
        result = join_results(gdf, metrics)
        not_sim = result[result["simulation_status"] == "not_simulated"]
        assert len(not_sim) == 1

    def test_p1_data_quality_flag_append_only(self):
        """P1: data_quality_flag from metrics appended to upstream flag."""
        from openubem.results.aggregator import join_results
        gdf = _make_enriched_gdf(1)
        gdf["data_quality_flag"] = "UPSTREAM_FLAG"
        metrics = _make_metrics_df(1, include_failed=False)
        metrics["data_quality_flag"] = "RESULTS_CSV_FALLBACK"
        result = join_results(gdf, metrics)
        flag = result.iloc[0]["data_quality_flag"]
        assert "UPSTREAM_FLAG" in str(flag)
        assert "RESULTS_CSV_FALLBACK" in str(flag)

    def test_one_row_per_building(self):
        """Result has exactly one row per Step-1 building (LEFT join semantics)."""
        from openubem.results.aggregator import join_results
        n = 5
        gdf = _make_enriched_gdf(n)
        metrics = _make_metrics_df(3)
        result = join_results(gdf, metrics)
        assert len(result) == n


# ── T11: compute_neighbourhood_summary ───────────────────────────────────────

class TestNeighbourhoodSummary:
    def _make_results_gdf(self) -> gpd.GeoDataFrame:
        gdf = _make_enriched_gdf(3)
        metrics = _make_metrics_df(3, include_failed=True)
        from openubem.results.aggregator import join_results
        return join_results(gdf, metrics)

    def test_floor_area_weighted_eui(self):
        """F10: neighbourhood EUI = Σ(eui*area) / Σ(area), not mean-of-intensities."""
        from openubem.results.aggregator import compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        # Hand-compute: only success rows (TEST0 and TEST1)
        # floor_area = 196 * 2 = 392 each
        # total_eui: TEST0=170, TEST1=180
        # weighted = (170*392 + 180*392) / (392+392) = (66640+70560)/784 = 137200/784 = 175
        exp_total = (170.0 * 392.0 + 180.0 * 392.0) / (2 * 392.0)
        got = summary["neighbourhood_eui_weighted_kwh_m2"]["total_eui_kwh_m2"]
        assert math.isclose(got, exp_total, rel_tol=1e-5), f"Got {got}, expected {exp_total}"

    def test_gwp_total_is_absolute(self):
        """F10: neighbourhood_gwp_total_kgco2 = Σ(gwp*area), not intensity."""
        from openubem.results.aggregator import compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        # 2 success rows: gwp_total=59.8 each (Phase-E fixture), floor_area=392 each
        exp_gwp = 59.8 * 392.0 + 59.8 * 392.0
        got = summary["neighbourhood_gwp_total_kgco2"]
        assert math.isclose(got, exp_gwp, rel_tol=1e-5), f"Got {got}, expected {exp_gwp}"

    def test_pct_floor_area_simulated(self):
        """F10: pct_floor_area_simulated = success floor area / total floor area."""
        from openubem.results.aggregator import compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        # 2 success of 3 buildings, equal floor areas → 2/3
        exp = 2.0 / 3.0
        got = summary["pct_floor_area_simulated"]
        assert math.isclose(got, exp, rel_tol=1e-5), f"Got {got}, expected {exp}"

    def test_n_buildings_by_status(self):
        """F10: status count dict present and correct."""
        from openubem.results.aggregator import compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        by_status = summary["n_buildings_by_status"]
        assert by_status.get("success", 0) == 2
        assert by_status.get("failed_parse", 0) == 1

    def test_p6_timestamp_present_but_excluded(self):
        """P6: summary has generated_utc key; two calls with same data differ only in timestamp."""
        from openubem.results.aggregator import compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        s1 = compute_neighbourhood_summary(result_gdf, run_timestamp="2026-01-01T00:00:00+00:00")
        s2 = compute_neighbourhood_summary(result_gdf, run_timestamp="2026-02-01T00:00:00+00:00")
        assert s1["metadata"]["generated_utc"] != s2["metadata"]["generated_utc"]
        # Everything else byte-identical
        assert s1["pct_floor_area_simulated"] == s2["pct_floor_area_simulated"]
        assert s1["neighbourhood_gwp_total_kgco2"] == s2["neighbourhood_gwp_total_kgco2"]


# ── T11: export_results ───────────────────────────────────────────────────────

class TestExportResults:
    def _make_results_gdf(self) -> gpd.GeoDataFrame:
        gdf = _make_enriched_gdf(3)
        metrics = _make_metrics_df(3, include_failed=True)
        from openubem.results.aggregator import join_results
        return join_results(gdf, metrics)

    def test_gpkg_written(self, tmp_path):
        from openubem.results.aggregator import export_results, compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        artifacts = export_results(result_gdf, tmp_path, summary)
        assert artifacts["gpkg"].exists()
        assert artifacts["gpkg"].stat().st_size > 0

    def test_geojson_crs_4326(self, tmp_path):
        """GeoJSON must be EPSG:4326 (GeoJSON spec)."""
        from openubem.results.aggregator import export_results, compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        export_results(result_gdf, tmp_path, summary)
        loaded = gpd.read_file(str(tmp_path / "05_results.geojson"))
        assert loaded.crs is not None
        assert loaded.crs.to_epsg() == 4326

    def test_csv_has_centroid_cols_and_no_geometry(self, tmp_path):
        """F11: CSV drops geometry, adds centroid_lon/lat → N×72 columns."""
        from openubem.results.aggregator import export_results, compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        export_results(result_gdf, tmp_path, summary)
        csv_df = pd.read_csv(tmp_path / "05_results.csv")
        assert "centroid_lon" in csv_df.columns
        assert "centroid_lat" in csv_df.columns
        assert "geometry" not in csv_df.columns
        # N rows preserved
        assert len(csv_df) == len(result_gdf)

    def test_schema_json_column_count(self, tmp_path):
        """F11: schema.json has 71 entries (one per non-geometry column)."""
        from openubem.results.aggregator import export_results, compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        export_results(result_gdf, tmp_path, summary)
        schema = json.loads((tmp_path / "05_results.schema.json").read_text())
        non_geom_cols = [c for c in result_gdf.columns if c != "geometry"]
        assert schema["n_columns"] == len(non_geom_cols)

    def test_summary_json_written(self, tmp_path):
        from openubem.results.aggregator import export_results, compute_neighbourhood_summary
        result_gdf = self._make_results_gdf()
        summary = compute_neighbourhood_summary(result_gdf)
        export_results(result_gdf, tmp_path, summary)
        summary_path = tmp_path / "05_neighbourhood_summary.json"
        assert summary_path.exists()
        data = json.loads(summary_path.read_text())
        assert "pct_floor_area_simulated" in data
        assert "n_buildings_by_status" in data


# ── T11: visualization smoke tests ───────────────────────────────────────────

class TestVisualizationSmoke:
    def _make_results_gdf(self) -> gpd.GeoDataFrame:
        gdf = _make_enriched_gdf(3)
        metrics = _make_metrics_df(3, include_failed=True)
        from openubem.results.aggregator import join_results
        return join_results(gdf, metrics)

    def test_eui_choropleth_renders(self, tmp_path):
        from openubem.results.visualization import plot_eui_choropleth
        result_gdf = self._make_results_gdf()
        out = plot_eui_choropleth(result_gdf, tmp_path / "eui_choropleth.png")
        assert out.exists()
        assert out.stat().st_size > 5000  # non-trivial PNG

    def test_eui_violin_renders(self, tmp_path):
        from openubem.results.visualization import plot_eui_violin_by_archetype
        result_gdf = self._make_results_gdf()
        out = plot_eui_violin_by_archetype(result_gdf, tmp_path / "eui_violin.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_gwp_stacked_renders(self, tmp_path):
        from openubem.results.visualization import plot_gwp_stacked_by_archetype
        result_gdf = self._make_results_gdf()
        out = plot_gwp_stacked_by_archetype(result_gdf, tmp_path / "gwp_stacked.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_render_all_figures(self, tmp_path):
        from openubem.results.visualization import render_all_figures
        result_gdf = self._make_results_gdf()
        paths = render_all_figures(result_gdf, tmp_path / "figures")
        assert all(p.exists() for p in paths.values())
        assert "eui_choropleth" in paths
        assert "eui_violin_by_archetype" in paths
        assert "gwp_stacked_by_archetype" in paths


# ── T11: orchestrator aggregate_results ──────────────────────────────────────

class TestAggregateResults:
    # Use osm_ids matching the golden SQL fixtures: way/R1 (1 zone), way/R2 (4 zones)
    # Third entry is a failed building (no SQL)
    _OSMS = ["way/R1", "way/R2", "way/FAILED"]
    _SQLS = [
        str(GOLDEN_DIR / "r1_single_zone.sql"),
        str(GOLDEN_DIR / "r2_one_zone_per_floor.sql"),
        None,
    ]
    _NZONES = [1, 4, 1]
    _FOOTPRINTS = [196.0, 625.0, 196.0]
    _FLOORS = [2.0, 4.0, 2.0]

    def _make_sim_manifest(self) -> pd.DataFrame:
        rows = []
        for i, osm_id in enumerate(self._OSMS):
            rows.append({
                "osm_id": osm_id,
                "status": "success" if i < 2 else "failed_energyplus",
                "sql_path": self._SQLS[i],
                "csv_path": None,
                "error_msg": "" if i < 2 else "EnergyPlus fatal error",
            })
        return pd.DataFrame(rows)

    def _make_idf_manifest(self) -> pd.DataFrame:
        rows = []
        for i, osm_id in enumerate(self._OSMS):
            rows.append({
                "osm_id": osm_id,
                "num_zones": self._NZONES[i],
                "zoning_strategy": "single_zone" if self._NZONES[i] == 1 else "one_zone_per_floor",
            })
        return pd.DataFrame(rows)

    def _make_enriched_gdf(self) -> gpd.GeoDataFrame:
        rows = []
        for i, osm_id in enumerate(self._OSMS):
            rows.append({
                "osm_id": osm_id,
                "footprint_area_m2": self._FOOTPRINTS[i],
                "levels": self._FLOORS[i],
                "height_m": float("nan"),
                "archetype_id": "SmallOffice",
                "climate_zone": "5A",
                "data_quality_flag": "",
                "geometry": _make_polygon(x_offset=float(i * 100)),
            })
        return gpd.GeoDataFrame(rows, crs=_EPSG_UTM)

    def test_returns_geodataframe(self, tmp_path):
        from openubem.results import aggregate_results
        result = aggregate_results(
            self._make_sim_manifest(), self._make_idf_manifest(),
            self._make_enriched_gdf(), tmp_path, state="MA", make_figures=False,
        )
        assert isinstance(result, gpd.GeoDataFrame)

    def test_output_has_all_step5_cols(self, tmp_path):
        """F9: output has all _STEP5_COLS columns (Phase-E: 28)."""
        from openubem.results import aggregate_results
        from openubem.results.aggregator import _STEP5_COLS
        result = aggregate_results(
            self._make_sim_manifest(), self._make_idf_manifest(),
            self._make_enriched_gdf(), tmp_path, state="MA", make_figures=False,
        )
        for col in _STEP5_COLS:
            assert col in result.columns, f"Missing Step-5 col: {col}"

    def test_failed_building_has_nan_eui(self, tmp_path):
        """Flag-don't-drop: energyplus-failed building present with NaN EUI."""
        from openubem.results import aggregate_results
        result = aggregate_results(
            self._make_sim_manifest(), self._make_idf_manifest(),
            self._make_enriched_gdf(), tmp_path, state="MA", make_figures=False,
        )
        failed = result[result["simulation_status"] == "failed_energyplus"]
        assert len(failed) == 1
        assert math.isnan(float(failed.iloc[0]["total_eui_kwh_m2"]))

    def test_export_trio_created(self, tmp_path):
        """§3G: all three export files + schema + summary JSON written."""
        from openubem.results import aggregate_results
        aggregate_results(
            self._make_sim_manifest(), self._make_idf_manifest(),
            self._make_enriched_gdf(), tmp_path, state="MA", make_figures=False,
        )
        assert (tmp_path / "05_results.gpkg").exists()
        assert (tmp_path / "05_results.geojson").exists()
        assert (tmp_path / "05_results.csv").exists()
        assert (tmp_path / "05_results.schema.json").exists()
        assert (tmp_path / "05_neighbourhood_summary.json").exists()

    def test_compute_validation_gates_skips_cbecs(self):
        """P8: CBECS gates return None (OQ-1 unresolved)."""
        from openubem.results import compute_validation_gates
        gates = compute_validation_gates(gpd.GeoDataFrame())
        assert gates["cbecs_cv_rmse"] is None
        assert gates["cbecs_nmbe"] is None
        assert gates["cbecs_r2"] is None
        assert gates["cbecs_ks_d"] is None


# ── T08 (Z07): CBECS validation gates ────────────────────────────────────────

def _make_ref_table(eui_values, weights=None, pba_code=2):
    """Minimal reference DataFrame matching the CBECS CSV schema."""
    if weights is None:
        weights = np.ones(len(eui_values))
    return pd.DataFrame({
        "pba_code": pba_code,
        "pba_label": "Office",
        "sqft": 10000.0,
        "eui_kwh_m2": np.asarray(eui_values, dtype=float),
        "finalwt": np.asarray(weights, dtype=float),
    })


def _make_multi_archetype_ref():
    """Reference table covering PBA 2 (Office) and PBA 14 (Education), ≥10 rows each."""
    rows = []
    for pba, label, base_eui in [(2, "Office", 200.0), (14, "Education", 150.0)]:
        for i in range(15):
            rows.append({"pba_code": pba, "pba_label": label, "sqft": 10000.0,
                         "eui_kwh_m2": base_eui + i * 2.0, "finalwt": 1.0})
    return pd.DataFrame(rows)


def _make_multi_archetype_sim():
    """Sim GDF with SmallOffice (PBA 2) and PrimarySchool (PBA 14)."""
    rows = []
    for archetype, base_eui in [("SmallOffice", 200.0), ("PrimarySchool", 150.0)]:
        for i in range(15):
            rows.append({"archetype_id": archetype, "eui_kwh_m2": base_eui + i * 2.0})
    return gpd.GeoDataFrame(rows, geometry=gpd.GeoSeries([None] * len(rows)))


def _make_sim_gdf(eui_values, archetype_id="SmallOffice"):
    rows = [{"archetype_id": archetype_id, "eui_kwh_m2": float(v)} for v in eui_values]
    return gpd.GeoDataFrame(rows, geometry=gpd.GeoSeries([None] * len(rows)))


class TestCbecsValidationGates:
    def test_identical_distribution_all_pass(self):
        """(a) Identical sim/reference → all _pass=True; NMBE ≈ 0.

        Uses multi-archetype fixture so R² has ≥2 data points.
        CV(RMSE) and KS_D may be non-zero due to quantile boundary effects at
        finite n — all _pass booleans must be True.
        """
        from openubem.results import compute_validation_gates
        ref = _make_multi_archetype_ref()
        sim = _make_multi_archetype_sim()
        gates = compute_validation_gates(sim, reference_table=ref)
        assert gates["cbecs_nmbe"] == pytest.approx(0.0, abs=0.01), gates
        assert gates["cbecs_cv_rmse_pass"] is True, gates
        assert gates["cbecs_nmbe_pass"] is True, gates
        assert gates["cbecs_r2_pass"] is True, gates
        assert gates["cbecs_ks_d_pass"] is True, gates

    def test_shifted_sim_nmbe_fails(self):
        """(b) Sim shifted +20% → NMBE ≈ +20, nmbe_pass=False."""
        from openubem.results import compute_validation_gates
        eui = np.linspace(100, 300, 30)
        ref = _make_ref_table(eui)
        sim = _make_sim_gdf(eui * 1.20)
        gates = compute_validation_gates(sim, reference_table=ref)
        assert gates["cbecs_nmbe"] == pytest.approx(20.0, abs=1.0), gates
        assert gates["cbecs_nmbe_pass"] is False

    def test_pba_map_covers_all_archetypes(self):
        """(c) cbecs_pba_map.json covers all 30 archetypes (mapped or explicitly excluded)."""
        import json
        from pathlib import Path
        map_path = Path("openubem/data/cbecs_pba_map.json")
        data = json.loads(map_path.read_text(encoding="utf-8"))
        pba_map = data["pba_map"]
        arch_path = Path("openubem/data/openstudio_archetypes.json")
        archs = json.loads(arch_path.read_text(encoding="utf-8"))["archetypes"]
        arch_ids = {a["archetype_id"] for a in archs}
        missing = arch_ids - set(pba_map.keys())
        assert not missing, f"Archetypes missing from pba_map: {missing}"
        assert len(pba_map) == len(arch_ids), (
            f"pba_map has {len(pba_map)} entries but there are {len(arch_ids)} archetypes"
        )

    def test_legacy_none_behaviour(self):
        """(d) reference_path=None → legacy four-None behaviour."""
        from openubem.results import compute_validation_gates
        gates = compute_validation_gates(gpd.GeoDataFrame())
        assert gates["cbecs_cv_rmse"] is None
        assert gates["cbecs_nmbe"] is None
        assert gates["cbecs_r2"] is None
        assert gates["cbecs_ks_d"] is None
