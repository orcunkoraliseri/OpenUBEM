"""Offline tests for the OpenUBEM GeoLibre exporter, CLI, and widget helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geolibre
import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, box

from openubem.results import aggregate_results
from openubem.viz.geolibre_export import (
    create_geolibre_map,
    export_geolibre_bundle,
    resolve_geolibre_output_dir,
)
from scripts.export_geolibre_project import main as geolibre_cli_main


def _make_buildings_gdf(
    *,
    heights: list[float],
    levels: list[int] | None = None,
    extra_cols: dict[str, list[Any]] | None = None,
) -> gpd.GeoDataFrame:
    """Create a synthetic UTM GeoDataFrame of building footprints.

    Args:
        heights: Per-building heights in metres.
        levels: Optional per-building storey counts.
        extra_cols: Optional additional attribute columns.

    Returns:
        Synthetic ``GeoDataFrame`` in ``EPSG:32636``.
    """
    n_bld = len(heights)
    data: dict[str, Any] = {
        "osm_id": [f"way/{100 + i}" for i in range(n_bld)],
        "height_m": heights,
        "levels": levels if levels is not None else [4] * n_bld,
        "use_class": [
            "residential" if i % 2 == 0 else "commercial"
            for i in range(n_bld)
        ],
        "provenance_height_m": ["observed"] * n_bld,
        "data_quality_flag": ["BASELINE"] * n_bld,
        "geometry": [
            box(500010.0 + i * 40.0, 4538000.0, 500030.0 + i * 40.0, 4538040.0)
            for i in range(n_bld)
        ],
    }
    if extra_cols:
        data.update(extra_cols)
    return gpd.GeoDataFrame(data, crs="EPSG:32636")


def test_constant_height_stage1_export(tmp_path: Path) -> None:
    """Ensure identical constant heights export cleanly without classification fail."""
    run_dir = tmp_path / "cell_const"
    out_dir = tmp_path / "geolibre_const"
    run_dir.mkdir(parents=True)

    buildings = _make_buildings_gdf(heights=[12.0, 12.0])
    buildings.to_file(run_dir / "01_buildings_clean.gpkg", driver="GPKG")

    bundle = export_geolibre_bundle(run_dir, output_dir=out_dir)

    assert bundle["project"].is_file()
    assert bundle["geojson"].is_file()
    assert bundle["html"].is_file()
    assert bundle["manifest"].is_file()

    project_text = bundle["project"].read_text(encoding="utf-8")
    project_obj = json.loads(project_text)
    assert len(project_obj["layers"]) == 1
    bld_style = project_obj["layers"][0]["style"]
    assert bld_style["vectorStyleMode"] == "single"
    assert bld_style["extrusionEnabled"] is True

    manifest = json.loads(bundle["manifest"].read_text(encoding="utf-8"))
    assert manifest["building_count"] == 2
    assert manifest["api_key_embedded"] is False
    assert manifest["active_metric"] == "height_m"


def test_stage5_csv_join_nan_sanitization_and_roundtrip(tmp_path: Path) -> None:
    """Verify CSV EUI join, NaN sanitization, extrusion, and geolibre load."""
    run_dir = tmp_path / "cell_eui"
    out_dir = tmp_path / "geolibre_eui"
    run_dir.mkdir(parents=True)

    buildings = _make_buildings_gdf(
        heights=[12.0, 18.0, 24.0, 15.0, np.nan],
        levels=[4, 6, 8, 5, 3],
    )
    buildings.to_file(run_dir / "01_buildings_clean.gpkg", driver="GPKG")

    results_df = pd.DataFrame(
        {
            "building_id": ["way/100", "way/101", "way/102", "way/103", "way/104"],
            "archetype_id": ["ARCH_A"] * 5,
            "eui_heating_kwh_m2": [55.2, 72.8, 91.4, 64.1, np.nan],
            "total_eui_kwh_m2": [105.0, 130.5, 165.0, 118.2, np.nan],
            "has_result": [True, True, True, True, False],
        }
    )
    results_df.to_csv(run_dir / "05_results.csv", index=False)

    bundle = export_geolibre_bundle(run_dir, output_dir=out_dir)

    raw_proj_text = bundle["project"].read_text(encoding="utf-8")
    assert "NaN" not in raw_proj_text
    assert "Infinity" not in raw_proj_text

    loaded = geolibre.load_project(bundle["project"])
    desc = geolibre.describe_project(loaded)
    assert desc["name"] == "OpenUBEM - cell_eui"
    assert len(desc["layers"]) == 1

    bld_layer = loaded["layers"][0]
    style = bld_layer["style"]
    assert style["vectorStyleMode"] == "graduated"
    assert style["vectorStyleProperty"] == "total_eui_kwh_m2"
    assert style["extrusionEnabled"] is True
    assert style["extrusionHeightProperty"] == "extrusion_height_m"
    assert len(style["vectorStyleStops"]) >= 2

    # Fallback extrusion height for NaN height_m building uses levels * 3.0 m
    feats = bld_layer["geojson"]["features"]
    last_props = feats[-1]["properties"]
    assert last_props["height_m"] is None
    assert last_props["total_eui_kwh_m2"] is None
    assert last_props["extrusion_height_m"] == pytest.approx(9.0)

    assert loaded["legend"]["panelVisible"] is True
    assert len(loaded["bookmarks"]) == 2
    assert len(loaded["storymap"]["chapters"]) == 2

    html_text = bundle["html"].read_text(encoding="utf-8")
    assert "https://web.geolibre.app/" in html_text
    assert "<iframe" in html_text


def test_stage6_utci_context_layers_and_caveats(tmp_path: Path) -> None:
    """Verify context layering and mandatory Stage 6 UTCI / AQI caveats."""
    run_dir = tmp_path / "cell_stage6"
    out_dir = tmp_path / "geolibre_stage6"
    run_dir.mkdir(parents=True)

    buildings = _make_buildings_gdf(
        heights=[10.0, 20.0, 30.0],
        extra_cols={
            "utci_peak_c": [38.2, 41.5, 44.1],
            "utci_mean_c": [31.0, 33.4, 35.8],
            "ctsi_degc_h": [420.0, 610.0, 780.0],
            "aq_ambient_aqi": [68, 68, 68],
            "aq_provenance": ["GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED"] * 3,
        },
    )
    buildings.to_file(run_dir / "06_mc_summary.gpkg", driver="GPKG")

    (run_dir / "06_mc_exposure_metrics.json").write_text(
        json.dumps({"utci_peak_max_c": 44.1, "ctsi_mean_degc_h": 603.3}),
        encoding="utf-8",
    )
    (run_dir / "06_mc_risk_alerts.json").write_text(
        json.dumps({"risk_tier": "Very Strong Heat Stress"}),
        encoding="utf-8",
    )
    roads_gdf = gpd.GeoDataFrame(
        {"highway": ["residential"]},
        geometry=[LineString([(500000.0, 4537990.0), (500150.0, 4537990.0)])],
        crs="EPSG:32636",
    )
    roads_gdf.to_file(run_dir / "06_context_roads.geojson", driver="GeoJSON")

    bundle = export_geolibre_bundle(run_dir, output_dir=out_dir)
    loaded = geolibre.load_project(bundle["project"])

    assert len(loaded["layers"]) == 2
    assert loaded["layers"][0]["name"] == "Road Network (OSM)"
    bld_layer = loaded["layers"][1]
    assert bld_layer["name"] == "OpenUBEM Buildings (3D)"

    abstract = bld_layer["descriptiveMetadata"]["abstract"]
    assert "unvalidated analysis product" in abstract
    assert "GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED" in abstract
    assert len(loaded["storymap"]["chapters"]) == 3

    manifest = json.loads(bundle["manifest"].read_text(encoding="utf-8"))
    assert manifest["context_layers_included"] == ["06_context_roads.geojson"]
    assert manifest["risk_tier"] == "Very Strong Heat Stress"
    assert len(manifest["caveats"]) == 2


def test_create_geolibre_map_widget(tmp_path: Path) -> None:
    """Verify Jupyter anywidget Map creation populates project and camera."""
    run_dir = tmp_path / "cell_widget"
    run_dir.mkdir(parents=True)
    buildings = _make_buildings_gdf(heights=[10.0, 16.0, 22.0])
    buildings.to_file(run_dir / "01_buildings_clean.gpkg", driver="GPKG")

    widget = create_geolibre_map(run_dir, height="600px", app_layout="embed")
    assert len(widget.project["layers"]) == 1
    assert widget.project["mapView"]["pitch"] > 0.0
    assert widget.height == "600px"


def test_cli_entrypoint_and_docs_validation_guard(tmp_path: Path) -> None:
    """Exercise CLI script and verify docs_VALIDATION write protection."""
    run_dir = tmp_path / "cell_cli"
    out_dir = tmp_path / "cli_out"
    run_dir.mkdir(parents=True)

    buildings = _make_buildings_gdf(heights=[11.0, 22.0, 33.0])
    buildings.to_file(run_dir / "01_buildings_clean.gpkg", driver="GPKG")

    bundle = geolibre_cli_main(
        [
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(out_dir),
            "--basemap",
            "liberty",
            "--colormap",
            "viridis",
            "--scheme",
            "equal-interval",
            "--class-count",
            "3",
            "--no-story-map",
        ]
    )
    loaded = geolibre.load_project(bundle["project"])
    assert "storymap" not in loaded
    assert "liberty" in loaded["basemapStyleUrl"]

    fake_val_run = tmp_path / "docs_VALIDATION" / "phaseE" / "nyc_centre"
    redirected = resolve_geolibre_output_dir(fake_val_run, output_dir=None)
    assert "docs_VALIDATION" not in redirected.parts
    with pytest.raises(ValueError, match="docs_VALIDATION"):
        export_geolibre_bundle(run_dir, output_dir=fake_val_run / "out")


def test_aggregate_results_exports_both_viewers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Step-5 aggregate_results emits both CityJSON and GeoLibre viewers."""
    golden_dir = Path(__file__).parent / "fixtures" / "golden_sql"
    sim_manifest = pd.DataFrame(
        [
            {
                "osm_id": "way/R1",
                "status": "success",
                "sql_path": str(golden_dir / "r1_single_zone.sql"),
                "csv_path": None,
                "error_msg": "",
            },
            {
                "osm_id": "way/R2",
                "status": "success",
                "sql_path": str(golden_dir / "r2_one_zone_per_floor.sql"),
                "csv_path": None,
                "error_msg": "",
            },
        ]
    )
    idf_manifest = pd.DataFrame(
        [
            {"osm_id": "way/R1", "num_zones": 1, "zoning_strategy": "single_zone"},
            {
                "osm_id": "way/R2",
                "num_zones": 4,
                "zoning_strategy": "one_zone_per_floor",
            },
        ]
    )
    enriched_gdf = gpd.GeoDataFrame(
        {
            "osm_id": ["way/R1", "way/R2"],
            "footprint_area_m2": [196.0, 625.0],
            "levels": [2.0, 4.0],
            "height_m": [7.0, 14.0],
            "archetype_id": ["SmallOffice", "SmallOffice"],
            "climate_zone": ["5A", "5A"],
            "data_quality_flag": ["", ""],
            "geometry": [
                box(330000.0, 4690000.0, 330014.0, 4690014.0),
                box(330100.0, 4690000.0, 330125.0, 4690025.0),
            ],
        },
        crs="EPSG:32618",
    )

    viewer_calls: list[str] = []

    def _fake_export_viewer(
        *args: Any,
        run_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Record export_viewer invocation without needing real IDF files."""
        viewer_calls.append(run_id)
        return {"html_path": str(tmp_path / f"{run_id}_viewer.html")}

    monkeypatch.setattr("openubem.viz.viewer_export.export_viewer", _fake_export_viewer)

    out_both = tmp_path / "run_both"
    aggregate_results(
        sim_manifest,
        idf_manifest,
        enriched_gdf,
        out_both,
        state="MA",
        make_figures=False,
        export_html=True,
    )
    assert len(viewer_calls) == 1
    gl_dir = out_both / "geolibre_companion"
    assert (gl_dir / "geolibre_viewer.html").is_file()
    loaded = geolibre.load_project(gl_dir / "run_both.geolibre.json")
    assert loaded["layers"][0]["style"]["vectorStyleMode"] == "graduated"
    assert loaded["layers"][0]["style"]["vectorStyleProperty"] == "total_eui_kwh_m2"

    # Explicit opt-out skips GeoLibre while still calling CityJSON export_viewer
    out_no_gl = tmp_path / "run_no_gl"
    aggregate_results(
        sim_manifest,
        idf_manifest,
        enriched_gdf,
        out_no_gl,
        state="MA",
        make_figures=False,
        export_html=True,
        export_geolibre=False,
    )
    assert len(viewer_calls) == 2
    assert not (out_no_gl / "geolibre_companion").exists()
