"""Opt-in GeoLibre GIS workspace, HTML viewer, and Jupyter notebook exporter.

Reads existing Stage 1-6 OpenUBEM artifacts read-only (never writing inside
``docs/docs_VALIDATION/``) and exports:

1. ``<cell>.geolibre.json`` -- portable GeoLibre project workspace with 3D
   building extrusions, graduated choropleth symbology, click/hover popups,
   STAC-aligned provenance metadata, map legend, camera bookmarks, and an
   optional Story Map narrative.
2. ``buildings_wgs84.geojson`` -- cleaned RFC-7946 WGS 84 FeatureCollection
   ready for DuckDB-WASM spatial SQL inside ``geolibre.app``.
3. ``geolibre_viewer.html`` -- standalone HTML iframe wrapper embedding the
   workspace for immediate browser viewing.
4. ``sources_manifest.json`` -- provenance and caveat summary (including
   explicit Stage 6 UTCI and macro-scale ambient Air Quality caveats).

Also exposes :func:`create_geolibre_map` for interactive two-way
``geolibre.Map`` exploration inside Jupyter notebooks.
"""

from __future__ import annotations

import copy
import html
import importlib.util
import json
import math
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

_CANDIDATE_BUILDING_FILES: tuple[str, ...] = (
    "06_mc_summary.gpkg",
    "05_results.gpkg",
    "buildings.parquet",
    "buildings.gpkg",
    "buildings.geojson",
    "02b_enriched.gpkg",
    "02_buildings_imputed.gpkg",
    "02_classified.gpkg",
    "02_residential_manifest.gpkg",
    "01_buildings_clean.gpkg",
    "01_buildings_raw.gpkg",
    "01_buildings.gpkg",
)

_EXPORT_COLUMNS: tuple[str, ...] = (
    "osm_id",
    "building_id",
    "district",
    "height_m",
    "levels",
    "year_built",
    "use_class",
    "building_tag",
    "function_tag",
    "roof_shape",
    "archetype_id",
    "building_type",
    "age_band",
    "floor_area_m2",
    "footprint_area_m2",
    "perimeter_m",
    "total_eui_kwh_m2",
    "heating_eui_kwh_m2",
    "cooling_eui_kwh_m2",
    "eui_heating_kwh_m2",
    "heating_kwh",
    "gwp_total_kgco2_m2",
    "total_gwp_kgco2e",
    "iod",
    "simulation_status",
    "geometry_outcome",
    "utci_peak_c",
    "utci_mean_c",
    "ctsi_degc_h",
    "aq_ambient_aqi",
    "aq_ambient_category",
    "aq_provenance",
    "provenance_height_m",
    "provenance_levels",
    "provenance_year_built",
    "data_quality_flag",
)

_METRIC_PRIORITY: tuple[str, ...] = (
    "total_eui_kwh_m2",
    "heating_eui_kwh_m2",
    "eui_heating_kwh_m2",
    "utci_peak_c",
    "utci_mean_c",
    "gwp_total_kgco2_m2",
    "total_gwp_kgco2e",
    "height_m",
    "year_built",
    "footprint_area_m2",
)

_CONTEXT_FILES: tuple[tuple[str, str, str, float], ...] = (
    ("06_context_blocks.geojson", "Urban Blocks (Derived)", "#475569", 0.15),
    ("06_context_green.geojson", "Green Spaces (OSM)", "#16a34a", 0.35),
    ("06_context_roads.geojson", "Road Network (OSM)", "#94a3b8", 0.70),
)

_UTCI_CAVEAT = (
    "OpenUBEM Stage 6 UTCI is a separate, unvalidated analysis product and "
    "must not be quoted as measured thermal comfort."
)
_AQ_CAVEAT = (
    "Ambient Air Quality fields represent macro-scale regional context "
    "(GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED), not street-canyon dispersion."
)

_DEFAULT_FLOOR_HEIGHT_M = 3.0
_DEFAULT_GEOLIBRE_APP_URL = "https://web.geolibre.app/"

_FALLBACK_BASEMAPS: dict[str, str] = {
    "liberty": "https://tiles.openfreemap.org/styles/liberty",
    "bright": "https://tiles.openfreemap.org/styles/bright",
    "positron": "https://tiles.openfreemap.org/styles/positron",
    "dark": "https://tiles.openfreemap.org/styles/dark",
    "fiord": "https://tiles.openfreemap.org/styles/fiord",
}


def has_geolibre() -> bool:
    """Check whether the optional ``geolibre`` package is importable.

    Returns:
        ``True`` if ``geolibre`` can be imported, ``False`` otherwise.
    """
    return importlib.util.find_spec("geolibre") is not None


def _import_geolibre() -> tuple[Any, Any, Any] | None:
    """Lazily import ``geolibre`` project, authoring, and HTML helpers.

    Returns:
        Tuple ``(authoring, project, render_project_html)`` when installed,
        or ``None`` if the optional ``geolibre`` package is absent.
    """
    if not has_geolibre():
        return None
    from geolibre import authoring, project
    from geolibre.geolibre import render_project_html

    return authoring, project, render_project_html


def resolve_geolibre_output_dir(
    run_dir: Path,
    output_dir: Path | None = None,
) -> Path:
    """Resolve a mutable output directory outside frozen validation paths.

    Args:
        run_dir: Input OpenUBEM stage run directory (opened read-only).
        output_dir: Optional explicit output directory override.

    Returns:
        Resolved writable directory path outside ``docs_VALIDATION``.

    Raises:
        ValueError: If an explicit ``output_dir`` targets ``docs_VALIDATION``.
    """
    run_path = Path(run_dir).resolve()
    if output_dir is not None:
        explicit = Path(output_dir).resolve()
        if "docs_VALIDATION" in explicit.parts:
            raise ValueError(
                "Refusing to write GeoLibre artifacts inside docs_VALIDATION/: "
                f"{explicit}"
            )
        return explicit

    if "docs_VALIDATION" in run_path.parts:
        repo_root = Path(__file__).resolve().parents[2]
        return (
            repo_root
            / "openubem"
            / "outputs"
            / "geolibre_companion"
            / run_path.name
        )
    return run_path / "geolibre_companion"


def _read_vector_file(path: Path) -> gpd.GeoDataFrame:
    """Read a vector GeoPackage, GeoJSON, or GeoParquet file.

    Args:
        path: Path to the spatial file.

    Returns:
        Loaded ``GeoDataFrame``.
    """
    if path.suffix.lower() == ".parquet":
        return gpd.read_parquet(path)
    return gpd.read_file(path)


def _find_join_keys(
    gdf: gpd.GeoDataFrame,
    results_df: pd.DataFrame,
) -> tuple[str, str] | None:
    """Determine matching ID column names between footprints and results CSV.

    Args:
        gdf: Building footprints ``GeoDataFrame``.
        results_df: Tabular simulation results ``DataFrame``.

    Returns:
        Tuple ``(left_key, right_key)`` or ``None`` if no key pair matches.
    """
    for candidate in ("osm_id", "building_id"):
        if candidate in gdf.columns and candidate in results_df.columns:
            return candidate, candidate
    if "osm_id" in gdf.columns and "building_id" in results_df.columns:
        return "osm_id", "building_id"
    if "building_id" in gdf.columns and "osm_id" in results_df.columns:
        return "building_id", "osm_id"
    return None


def _join_results_csv(
    gdf: gpd.GeoDataFrame,
    csv_path: Path,
    district_filter: str | None,
) -> tuple[gpd.GeoDataFrame, int]:
    """Left-join non-colliding OpenUBEM results CSV columns onto footprints.

    Args:
        gdf: Building footprints ``GeoDataFrame``.
        csv_path: Path to a results CSV (e.g. ``05_results.csv``).
        district_filter: Optional district code filter when ``district`` exists.

    Returns:
        Tuple ``(joined_gdf, matched_row_count)``.
    """
    df = pd.read_csv(csv_path)
    if district_filter is not None and "district" in df.columns:
        df = df.loc[df["district"].astype(str) == district_filter].copy()

    keys = _find_join_keys(gdf, df)
    if keys is None or df.empty:
        return gdf, 0

    left_key, right_key = keys
    df = df.copy()
    df["_join_id"] = df[right_key].astype(str)
    df = df.drop_duplicates(subset=["_join_id"], keep="first")

    new_cols = [c for c in df.columns if c not in gdf.columns and c != "_join_id"]
    if not new_cols:
        return gdf, 0

    work = gdf.copy()
    work["_join_id"] = work[left_key].astype(str)
    merged = work.merge(
        df[["_join_id", *new_cols]],
        on="_join_id",
        how="left",
    )
    matched = int(merged[new_cols].notna().any(axis=1).sum())
    merged = merged.drop(columns=["_join_id"])
    return gpd.GeoDataFrame(merged, geometry="geometry", crs=gdf.crs), matched


def _compute_extrusion_height(row: pd.Series) -> float:
    """Derive safe display extrusion height without mutating raw ``height_m``.

    Args:
        row: Building attribute row.

    Returns:
        Finite non-negative extrusion height in metres for visualization.
    """
    raw_h = row.get("height_m")
    if raw_h is not None and pd.notna(raw_h):
        try:
            val = float(raw_h)
            if math.isfinite(val) and val > 0.0:
                return round(val, 3)
        except (TypeError, ValueError):
            pass

    raw_lv = row.get("levels")
    if raw_lv is not None and pd.notna(raw_lv):
        try:
            lv = float(raw_lv)
            if math.isfinite(lv) and lv > 0.0:
                return round(lv * _DEFAULT_FLOOR_HEIGHT_M, 3)
        except (TypeError, ValueError):
            pass

    return 0.0


def load_openubem_buildings_for_geolibre(
    run_dir: Path,
    *,
    buildings_path: Path | None = None,
    results_csv_path: Path | None = None,
    district_filter: str | None = None,
) -> tuple[gpd.GeoDataFrame, list[str]]:
    """Load OpenUBEM building geometries read-only and reproject to WGS 84.

    Args:
        run_dir: OpenUBEM stage run root directory.
        buildings_path: Optional explicit vector file override.
        results_csv_path: Optional results CSV to left-join onto footprints.
        district_filter: Optional district identifier when filtering multi-site
            result tables.

    Returns:
        Tuple ``(wgs84_gdf, loaded_source_names)``.

    Raises:
        FileNotFoundError: If no supported building vector file exists.
        ValueError: If the loaded layer lacks a coordinate reference system.
    """
    run_path = Path(run_dir)
    loaded_sources: list[str] = []
    raw_gdf: gpd.GeoDataFrame | None = None

    if buildings_path is not None:
        explicit = Path(buildings_path)
        if not explicit.is_file():
            raise FileNotFoundError(
                f"Explicit buildings file not found: {explicit}"
            )
        raw_gdf = _read_vector_file(explicit)
        loaded_sources.append(explicit.name)
    else:
        for rel in _CANDIDATE_BUILDING_FILES:
            cand = run_path / rel
            if cand.is_file():
                raw_gdf = _read_vector_file(cand)
                loaded_sources.append(rel)
                break

    if raw_gdf is None:
        raise FileNotFoundError(
            f"No OpenUBEM building vector file found under {run_path}."
        )
    if raw_gdf.crs is None:
        raise ValueError(
            "Buildings layer must carry a valid CRS for GeoLibre WGS 84 export."
        )

    csv_target = results_csv_path
    if csv_target is None and (run_path / "05_results.csv").is_file():
        csv_target = run_path / "05_results.csv"

    if csv_target is not None:
        csv_file = Path(csv_target)
        if not csv_file.is_file():
            raise FileNotFoundError(f"Results CSV not found: {csv_file}")
        raw_gdf, _ = _join_results_csv(raw_gdf, csv_file, district_filter)
        loaded_sources.append(csv_file.name)

    wgs_gdf = raw_gdf.to_crs(epsg=4326).copy()
    wgs_gdf = wgs_gdf[
        wgs_gdf.geometry.notna() & (~wgs_gdf.geometry.is_empty)
    ].copy()

    keep_cols = [c for c in _EXPORT_COLUMNS if c in wgs_gdf.columns]
    export_gdf = wgs_gdf[[*keep_cols, "geometry"]].copy()
    export_gdf["extrusion_height_m"] = export_gdf.apply(
        _compute_extrusion_height,
        axis=1,
    )
    return export_gdf, loaded_sources


def _to_json_scalar(value: Any) -> Any:
    """Convert a pandas/numpy scalar to an RFC-8259 strict JSON-safe value.

    Args:
        value: Raw attribute value from a ``GeoDataFrame`` row.

    Returns:
        Python primitive or ``None`` (mapping ``NaN``/``Inf``/``NA`` to ``None``).
    """
    if value is None:
        return None
    if isinstance(value, (bool, str)):
        return value
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, int):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def _gdf_to_clean_feature_collection(gdf: gpd.GeoDataFrame) -> dict[str, Any]:
    """Serialize a WGS 84 ``GeoDataFrame`` into a strict RFC-8259 FeatureCollection.

    Args:
        gdf: Input WGS 84 ``GeoDataFrame``.

    Returns:
        GeoJSON ``FeatureCollection`` dictionary with finite-only properties.
    """
    features: list[dict[str, Any]] = []
    prop_cols = [c for c in gdf.columns if c != "geometry"]
    for idx, row in enumerate(gdf.itertuples(index=False), start=1):
        geom = getattr(row, "geometry", None)
        if geom is None or geom.is_empty:
            continue
        props = {
            col: _to_json_scalar(getattr(row, col))
            for col in prop_cols
        }
        fid = props.get("osm_id") or props.get("building_id") or str(idx)
        features.append(
            {
                "type": "Feature",
                "id": str(fid),
                "geometry": json.loads(
                    json.dumps(geom.__geo_interface__, allow_nan=False)
                ),
                "properties": props,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _load_optional_context_feature_collection(
    path: Path,
    fallback_crs: Any,
) -> dict[str, Any] | None:
    """Load an optional Stage 6 OSM urban-context GeoJSON in WGS 84.

    Args:
        path: Path to ``06_context_*.geojson``.
        fallback_crs: CRS to assume when the cached GeoJSON lacks an explicit CRS.

    Returns:
        Cleaned WGS 84 ``FeatureCollection`` dict, or ``None`` if absent/empty.
    """
    if not path.is_file():
        return None
    try:
        raw_json = json.loads(path.read_text(encoding="utf-8"))
        crs_hint = raw_json.get("crs") or fallback_crs
        gdf = gpd.read_file(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None

    if gdf.empty:
        return None
    if gdf.crs is None and crs_hint is not None:
        gdf = gdf.set_crs(crs_hint, allow_override=True)
    if gdf.crs is not None:
        gdf = gdf.to_crs(epsg=4326)
    return _gdf_to_clean_feature_collection(gdf)


def select_active_metric(
    gdf: gpd.GeoDataFrame,
    requested: str | None = None,
) -> str | None:
    """Choose a finite numeric column for choropleth classification.

    Args:
        gdf: Exported building ``GeoDataFrame``.
        requested: Optional explicit column name from the caller.

    Returns:
        Selected column name, or ``None`` if no numeric metric has finite data.

    Raises:
        ValueError: If ``requested`` is missing or has no finite numeric values.
    """
    if requested is not None:
        if requested not in gdf.columns:
            raise ValueError(
                f"Requested color-by column {requested!r} not in dataset columns."
            )
        series = pd.to_numeric(gdf[requested], errors="coerce")
        if not series.dropna().apply(math.isfinite).any():
            raise ValueError(
                f"Requested color-by column {requested!r} has no finite values."
            )
        return requested

    for col in _METRIC_PRIORITY:
        if col not in gdf.columns:
            continue
        series = pd.to_numeric(gdf[col], errors="coerce")
        finite = series[series.notna() & series.map(math.isfinite)]
        if not finite.empty:
            return col
    return None


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    """Safely read a JSON file when present on disk.

    Args:
        path: Candidate JSON file path.

    Returns:
        Parsed JSON dictionary, or ``None`` if absent or unreadable.
    """
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _build_popup_fields(
    gdf: gpd.GeoDataFrame,
    active_metric: str | None,
) -> list[dict[str, Any] | str]:
    """Assemble ordered GeoLibre popup fields available on ``gdf``.

    Args:
        gdf: Exported WGS 84 ``GeoDataFrame``.
        active_metric: Highlighted choropleth column name if any.

    Returns:
        List of field names and formatted field dicts accepted by GeoLibre.
    """
    candidates: list[tuple[str, str, int | None, str]] = [
        ("archetype_id", "Archetype", None, ""),
        ("use_class", "Use Class", None, ""),
        ("building_type", "Building Type", None, ""),
        ("age_band", "Age Band", None, ""),
        ("year_built", "Year Built", 0, ""),
        ("height_m", "Height", 1, " m"),
        ("levels", "Storeys", 0, ""),
        ("floor_area_m2", "Floor Area", 1, " m2"),
        ("footprint_area_m2", "Footprint Area", 1, " m2"),
        ("total_eui_kwh_m2", "Total EUI", 1, " kWh/m2/yr"),
        ("heating_eui_kwh_m2", "Heating EUI", 1, " kWh/m2/yr"),
        ("cooling_eui_kwh_m2", "Cooling EUI", 1, " kWh/m2/yr"),
        ("eui_heating_kwh_m2", "Heating EUI", 1, " kWh/m2/yr"),
        ("gwp_total_kgco2_m2", "Total GWP", 1, " kgCO2/m2/yr"),
        ("total_gwp_kgco2e", "Total GWP", 0, " kgCO2e"),
        ("iod", "IOD", 1, " C"),
        ("simulation_status", "Simulation Status", None, ""),
        ("utci_peak_c", "Peak UTCI (Unvalidated)", 1, " C"),
        ("utci_mean_c", "Mean UTCI (Unvalidated)", 1, " C"),
        ("ctsi_degc_h", "CTSI (Unvalidated)", 1, " degC*h"),
        ("aq_ambient_aqi", "Ambient AQI (Macro)", 0, ""),
        ("aq_provenance", "AQ Provenance", None, ""),
        ("provenance_height_m", "Height Provenance", None, ""),
        ("provenance_year_built", "Year Provenance", None, ""),
        ("data_quality_flag", "Data Quality Flag", None, ""),
    ]
    if active_metric and all(c[0] != active_metric for c in candidates):
        candidates.insert(0, (active_metric, active_metric, 2, ""))

    fields: list[dict[str, Any] | str] = []
    for col, label, decimals, suffix in candidates:
        if col not in gdf.columns:
            continue
        if decimals is not None:
            entry: dict[str, Any] = {
                "field": col,
                "label": label,
                "kind": "number",
                "decimals": decimals,
            }
            if suffix:
                entry["suffix"] = suffix
            fields.append(entry)
        else:
            fields.append({"field": col, "label": label, "kind": "text"})
    return fields


def _compose_layer_abstract(
    *,
    run_name: str,
    n_buildings: int,
    active_metric: str | None,
    has_utci: bool,
    has_aq: bool,
    loaded_sources: list[str],
) -> str:
    """Build descriptive STAC-compatible abstract text with honesty caveats.

    Args:
        run_name: District or run directory identifier.
        n_buildings: Number of building features exported.
        active_metric: Primary symbolized column name if selected.
        has_utci: Whether Stage 6 UTCI columns are present.
        has_aq: Whether ambient air-quality columns are present.
        loaded_sources: Read-only input filenames used to construct the layer.

    Returns:
        Formatted abstract string for layer catalog metadata.
    """
    parts = [
        f"OpenUBEM district export for {run_name} ({n_buildings} buildings).",
        f"Source artifacts: {', '.join(loaded_sources)}.",
    ]
    if active_metric:
        parts.append(f"Primary choropleth attribute: {active_metric}.")
    if has_utci:
        parts.append(_UTCI_CAVEAT)
    if has_aq:
        parts.append(_AQ_CAVEAT)
    return " ".join(parts)


def _fallback_empty_project(name: str, basemap: str) -> dict[str, Any]:
    """Construct a minimal ``.geolibre.json`` project when ``geolibre`` is absent.

    Args:
        name: Project display title.
        basemap: Basemap preset name or MapLibre style URL.

    Returns:
        GeoLibre-compatible project dictionary.
    """
    style_url = _FALLBACK_BASEMAPS.get(basemap.lower(), basemap)
    return {
        "version": "0.2.0",
        "name": name,
        "mapView": {"center": [0.0, 0.0], "zoom": 14.0, "bearing": 0.0, "pitch": 0.0},
        "basemapStyleUrl": style_url,
        "basemapVisible": True,
        "basemapOpacity": 1,
        "layers": [],
        "styles": {},
        "preferences": {
            "map": {
                "restrictBounds": False,
                "bounds": [-180, -85, 180, 85],
                "minZoom": 0,
                "maxZoom": 24,
                "maxPitch": 85,
                "renderWorldCopies": True,
            },
            "environmentVariables": [],
        },
        "metadata": {},
    }


def _fallback_geojson_layer(
    name: str,
    data: dict[str, Any],
    **style: Any,
) -> dict[str, Any]:
    """Construct a minimal GeoJSON layer dict when ``geolibre`` is absent.

    Args:
        name: Display name for the layer.
        data: Cleaned GeoJSON ``FeatureCollection``.
        **style: Style overrides for the layer.

    Returns:
        GeoLibre layer dictionary.
    """
    base_style = {
        "minZoom": 0,
        "maxZoom": 24,
        "fillColor": "#3b82f6",
        "strokeColor": "#1e40af",
        "strokeWidth": 1,
        "strokeOpacity": 1,
        "fillOpacity": 0.7,
        "extrusionEnabled": False,
        "extrusionColor": "#3b82f6",
        "extrusionOpacity": 0.85,
        "extrusionHeightProperty": "extrusion_height_m",
        "extrusionHeightScale": 1,
        "vectorStyleMode": "single",
        "vectorStyleProperty": "",
        "vectorStyleClassCount": 5,
        "vectorStyleColorRamp": "turbo",
        "vectorStyleClassificationScheme": "quantile",
        "vectorStyleStops": [],
    }
    base_style.update(style)
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": "geojson",
        "visible": True,
        "opacity": 1,
        "style": base_style,
        "metadata": {},
        "source": {"type": "geojson"},
        "geojson": data,
    }


def _fallback_fit_bounds(
    project_dict: dict[str, Any],
    bbox: list[float],
) -> None:
    """Compute approximate center/zoom from ``bbox`` without ``geolibre``.

    Args:
        project_dict: GeoLibre project dict mutated in place.
        bbox: Bounding box ``[min_lng, min_lat, max_lng, max_lat]``.
    """
    min_lng, min_lat, max_lng, max_lat = bbox
    center_lng = (min_lng + max_lng) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    span = max(abs(max_lng - min_lng), abs(max_lat - min_lat), 1e-4)
    zoom = max(1.0, min(18.0, math.log2(360.0 / span) - 1.0))
    project_dict["mapView"] = {
        "center": [center_lng, center_lat],
        "zoom": round(zoom, 3),
        "bearing": 0.0,
        "pitch": 0.0,
        "bbox": bbox,
    }


def _render_fallback_html(
    project_dict: dict[str, Any],
    *,
    title: str,
    theme: str,
) -> str:
    """Render standalone HTML embedding ``web.geolibre.app`` via ``postMessage``.

    Args:
        project_dict: GeoLibre project dictionary to inject on iframe load.
        title: Document ``<title>``.
        theme: Either ``"dark"`` or ``"light"``.

    Returns:
        Standalone HTML5 document string.
    """
    escaped_title = html.escape(title)
    payload_json = json.dumps(project_dict, allow_nan=False).replace("</", "<\\/")
    iframe_src = f"{_DEFAULT_GEOLIBRE_APP_URL}?embed=1&theme={html.escape(theme)}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escaped_title}</title>
  <style>
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; }}
    iframe {{ border: 0; width: 100%; height: 100vh; display: block; }}
  </style>
</head>
<body>
  <iframe id="geolibre-frame" src="{iframe_src}" title="{escaped_title}"></iframe>
  <script>
    (function () {{
      const frame = document.getElementById("geolibre-frame");
      const project = {payload_json};
      function postProject() {{
        if (!frame || !frame.contentWindow) return;
        frame.contentWindow.postMessage(
          {{ type: "geolibre:loadProject", project: project }},
          "https://web.geolibre.app"
        );
      }}
      frame.addEventListener("load", postProject);
      window.addEventListener("message", function (evt) {{
        if (evt.origin === "https://web.geolibre.app" &&
            evt.data && evt.data.type === "geolibre:ready") {{
          postProject();
        }}
      }});
    }})();
  </script>
</body>
</html>
"""


def _add_story_chapters_if_enabled(
    authoring: Any,
    project_dict: dict[str, Any],
    *,
    run_name: str,
    n_buildings: int,
    active_metric: str | None,
    has_utci: bool,
    utci_peak_max: Any,
    theme: str,
) -> None:
    """Attach a concise multi-chapter Story Map to ``project_dict``.

    Args:
        authoring: Imported ``geolibre.authoring`` module.
        project_dict: GeoLibre project dict mutated in place.
        run_name: District identifier string.
        n_buildings: Exported building footprint count.
        active_metric: Primary symbolized metric name if any.
        has_utci: Whether Stage 6 UTCI metrics are present.
        utci_peak_max: Optional district peak UTCI value.
        theme: Story Map theme (``"dark"`` or ``"light"``).
    """
    view = project_dict.get("mapView", {})
    center = view.get("center", [0.0, 0.0])
    zoom = float(view.get("zoom", 15.0))
    authoring.set_story_map(
        project_dict,
        title=f"OpenUBEM District Twin: {run_name}",
        subtitle=f"{n_buildings} buildings explored in GeoLibre",
        byline="OpenUBEM x GeoLibre Companion",
        theme=theme,
    )
    authoring.add_story_chapter(
        project_dict,
        "1. District Morphology & Provenance",
        description=(
            f"Loaded {n_buildings} OpenUBEM building footprints extruded by "
            "extrusion_height_m while preserving raw height_m and provenance_* "
            "lineage attributes."
        ),
        center=center,
        zoom=zoom,
        pitch=52.0,
        bearing=-20.0,
    )
    metric_label = active_metric or "geometry"
    authoring.add_story_chapter(
        project_dict,
        f"2. Choropleth Distribution ({metric_label})",
        description=(
            f"Buildings are symbolized across {metric_label}. Click any "
            "footprint to inspect archetypes, data quality flags, and energy "
            "or morphology properties."
        ),
        center=center,
        zoom=min(20.0, zoom + 0.5),
        pitch=35.0,
        bearing=15.0,
    )
    if has_utci:
        peak_note = (
            f" Peak domain UTCI: {utci_peak_max:.1f} C."
            if isinstance(utci_peak_max, (int, float))
            and math.isfinite(float(utci_peak_max))
            else ""
        )
        authoring.add_story_chapter(
            project_dict,
            "3. Stage 6 Outdoor Microclimate Context",
            description=f"{_UTCI_CAVEAT}{peak_note}",
            center=center,
            zoom=zoom,
            pitch=0.0,
            bearing=0.0,
        )


def build_geolibre_project(
    run_dir: Path | str,
    *,
    buildings_path: Path | None = None,
    results_csv_path: Path | None = None,
    district_filter: str | None = None,
    project_name: str | None = None,
    basemap: str = "dark",
    color_by: str | None = None,
    colormap: str = "turbo",
    scheme: str = "quantile",
    class_count: int = 5,
    extrude: bool = True,
    pitch: float = 52.0,
    bearing: float = -20.0,
    include_story_map: bool = True,
) -> tuple[dict[str, Any], gpd.GeoDataFrame, dict[str, Any]]:
    """Build a complete GeoLibre project dict, exported GeoDataFrame, and manifest.

    Args:
        run_dir: Stage 1-6 OpenUBEM run directory opened read-only.
        buildings_path: Optional explicit vector file override.
        results_csv_path: Optional results CSV to join onto building footprints.
        district_filter: Optional district filter for multi-district CSVs.
        project_name: Optional project title; defaults to ``OpenUBEM - <cell>``.
        basemap: GeoLibre basemap name (e.g. ``"dark"``, ``"liberty"``) or URL.
        color_by: Optional numeric column to drive graduated choropleth colors.
        colormap: GeoLibre color ramp name (default ``"turbo"``).
        scheme: Classification scheme (``"quantile"`` or ``"equal-interval"``).
        class_count: Number of graduated classes (2-12).
        extrude: Enable 2.5D ``fill-extrusion`` by ``extrusion_height_m``.
        pitch: Initial 3D camera tilt in degrees when ``extrude`` is ``True``.
        bearing: Initial camera azimuth in degrees when ``extrude`` is ``True``.
        include_story_map: Attach an interactive Story Map walkthrough.

    Returns:
        Tuple ``(project_dict, export_gdf, manifest_dict)``.
    """
    run_path = Path(run_dir)
    export_gdf, loaded_sources = load_openubem_buildings_for_geolibre(
        run_path,
        buildings_path=buildings_path,
        results_csv_path=results_csv_path,
        district_filter=district_filter,
    )
    if export_gdf.empty:
        raise ValueError(f"No valid building geometries found under {run_path}.")

    active_metric = select_active_metric(export_gdf, requested=color_by)
    cell_label = district_filter or run_path.name
    title = project_name or f"OpenUBEM - {cell_label}"
    bounds = [round(float(v), 6) for v in export_gdf.total_bounds]
    fc = _gdf_to_clean_feature_collection(export_gdf)

    has_utci = any(
        c in export_gdf.columns and export_gdf[c].notna().any()
        for c in ("utci_peak_c", "utci_mean_c", "ctsi_degc_h")
    )
    has_aq = (
        "aq_provenance" in export_gdf.columns
        and export_gdf["aq_provenance"].notna().any()
    )
    exposure = _read_optional_json(run_path / "06_mc_exposure_metrics.json") or {}
    risk_alerts = _read_optional_json(run_path / "06_mc_risk_alerts.json") or {}

    gl = _import_geolibre()
    context_layers_added: list[str] = []

    if gl is not None:
        authoring, project_mod, _ = gl
        project_dict = project_mod.build_empty_project(name=title)
        authoring.set_basemap(project_dict, basemap)
        authoring.fit_bounds(project_dict, bounds)
        # Preserve bbox recorded by fit_bounds by omitting center/zoom here.
        authoring.set_view(
            project_dict,
            pitch=pitch if extrude else 0.0,
            bearing=bearing if extrude else 0.0,
        )

        for filename, layer_name, color, opacity in _CONTEXT_FILES:
            ctx_fc = _load_optional_context_feature_collection(
                run_path / filename,
                fallback_crs=None,
            )
            if ctx_fc is None:
                continue
            ctx_layer = project_mod.geojson_layer(
                layer_name,
                ctx_fc,
                fillColor=color,
                strokeColor=color,
                fillOpacity=opacity,
                strokeOpacity=min(1.0, opacity + 0.2),
                strokeWidth=1.5,
            )
            authoring.add_layer(project_dict, ctx_layer)
            context_layers_added.append(filename)

        bld_layer = project_mod.geojson_layer(
            "OpenUBEM Buildings (3D)" if extrude else "OpenUBEM Buildings",
            fc,
            fillColor="#38bdf8",
            strokeColor="#0f172a",
            strokeWidth=1,
            fillOpacity=0.85,
            extrusionEnabled=bool(extrude),
            extrusionHeightProperty="extrusion_height_m",
            extrusionHeightScale=1,
            extrusionOpacity=0.85,
            extrusionColor="#38bdf8",
        )
        bld_id = authoring.add_layer(project_dict, bld_layer)

        classification_applied = False
        if active_metric is not None:
            series = pd.to_numeric(export_gdf[active_metric], errors="coerce")
            unique_vals = series[series.notna() & series.map(math.isfinite)].nunique()
            if unique_vals >= 2:
                try:
                    frag = authoring.classify_layer(
                        project_dict,
                        bld_id,
                        active_metric,
                        class_count=class_count,
                        colormap=colormap,
                        scheme=scheme,
                    )
                    if len(frag.get("vectorStyleStops", [])) >= 2:
                        classification_applied = True
                except ValueError:
                    classification_applied = False

        if not classification_applied:
            authoring.apply_style(
                project_dict,
                bld_id,
                {"vectorStyleMode": "single", "fillColor": "#38bdf8"},
            )

        popup_fields = _build_popup_fields(export_gdf, active_metric)
        popup_title = "osm_id" if "osm_id" in export_gdf.columns else None
        hover_cols = [
            col
            for col in ("osm_id", active_metric, "height_m")
            if col and col in export_gdf.columns
        ]
        authoring.set_popup(
            project_dict,
            bld_id,
            popup_fields or None,
            click=True,
            hover=bool(hover_cols),
            title=popup_title,
            tooltip=hover_cols if hover_cols else False,
        )

        abstract = _compose_layer_abstract(
            run_name=cell_label,
            n_buildings=len(export_gdf),
            active_metric=active_metric,
            has_utci=has_utci,
            has_aq=has_aq,
            loaded_sources=loaded_sources,
        )
        keywords = ["OpenUBEM", "UBEM", "EnergyPlus", cell_label]
        if active_metric:
            keywords.append(active_metric)
        if has_utci:
            keywords.append("UTCI-unvalidated")
        authoring.set_layer_metadata(
            project_dict,
            bld_id,
            title=f"OpenUBEM Buildings - {cell_label}",
            abstract=abstract,
            keywords=keywords,
            attribution="OpenStreetMap contributors; OpenUBEM physics simulation",
        )

        authoring.set_map_legend(
            project_dict,
            title="OpenUBEM District Legend",
            position="bottom-right",
            visible=True,
        )
        authoring.add_bookmark(
            project_dict,
            "3D Urban Massing",
            pitch=52.0,
            bearing=-20.0,
        )
        authoring.add_bookmark(
            project_dict,
            "2D Planimetric Overhead",
            pitch=0.0,
            bearing=0.0,
        )
        if include_story_map:
            theme = "dark" if basemap == "dark" else "light"
            _add_story_chapters_if_enabled(
                authoring,
                project_dict,
                run_name=cell_label,
                n_buildings=len(export_gdf),
                active_metric=active_metric,
                has_utci=has_utci,
                utci_peak_max=exposure.get("utci_peak_max_c"),
                theme=theme,
            )
        project_dict = project_mod.redact_credentials(project_dict)
    else:
        project_dict = _fallback_empty_project(title, basemap)
        _fallback_fit_bounds(project_dict, bounds)
        if extrude:
            project_dict["mapView"]["pitch"] = float(pitch)
            project_dict["mapView"]["bearing"] = float(bearing)
        for filename, layer_name, color, opacity in _CONTEXT_FILES:
            ctx_fc = _load_optional_context_feature_collection(
                run_path / filename,
                fallback_crs=None,
            )
            if ctx_fc is None:
                continue
            project_dict["layers"].append(
                _fallback_geojson_layer(
                    layer_name,
                    ctx_fc,
                    fillColor=color,
                    strokeColor=color,
                    fillOpacity=opacity,
                )
            )
            context_layers_added.append(filename)
        project_dict["layers"].append(
            _fallback_geojson_layer(
                "OpenUBEM Buildings (3D)" if extrude else "OpenUBEM Buildings",
                fc,
                fillColor="#38bdf8",
                extrusionEnabled=bool(extrude),
                extrusionHeightProperty="extrusion_height_m",
            )
        )

    center = project_dict.get("mapView", {}).get("center", [0.0, 0.0])
    caveats: list[str] = []
    if has_utci:
        caveats.append(_UTCI_CAVEAT)
    if has_aq:
        caveats.append(_AQ_CAVEAT)

    manifest: dict[str, Any] = {
        "cell_name": cell_label,
        "source_files_read_only": loaded_sources,
        "context_layers_included": context_layers_added,
        "building_count": int(len(export_gdf)),
        "center_lon": round(float(center[0]), 6),
        "center_lat": round(float(center[1]), 6),
        "bounds_wgs84": bounds,
        "active_metric": active_metric,
        "extrude_enabled": bool(extrude),
        "basemap": basemap,
        "colormap": colormap,
        "scheme": scheme,
        "utci_peak_max_c": exposure.get("utci_peak_max_c"),
        "ctsi_mean_degc_h": exposure.get("ctsi_mean_degc_h"),
        "risk_tier": risk_alerts.get("risk_tier"),
        "aq_provenance": (
            str(export_gdf["aq_provenance"].dropna().iloc[0])
            if has_aq
            else None
        ),
        "caveats": caveats,
        "geolibre_package_available": has_geolibre(),
        "api_key_embedded": False,
    }
    return project_dict, export_gdf, manifest


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> Path:
    """Write a JSON payload atomically with strict ``allow_nan=False``.

    Args:
        path: Destination JSON path.
        payload: JSON-serializable dictionary.

    Returns:
        Written file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    )
    tmp_path = Path(handle.name)
    try:
        with handle:
            handle.write(json.dumps(payload, indent=2, allow_nan=False) + "\n")
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    return path


def _sanitize_slug(name: str) -> str:
    """Convert an arbitrary run/district label into a safe filename stem.

    Args:
        name: Raw cell or directory name.

    Returns:
        Sanitized filename stem.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    return cleaned or "openubem_district"


def export_geolibre_bundle(
    run_dir: Path | str,
    *,
    output_dir: Path | None = None,
    buildings_path: Path | None = None,
    results_csv_path: Path | None = None,
    district_filter: str | None = None,
    basemap: str = "dark",
    color_by: str | None = None,
    colormap: str = "turbo",
    scheme: str = "quantile",
    class_count: int = 5,
    extrude: bool = True,
    include_story_map: bool = True,
) -> dict[str, Path]:
    """Export read-only OpenUBEM results into a GeoLibre workspace bundle.

    Generates four files inside a mutable destination directory (never writing
    inside ``docs/docs_VALIDATION/``): ``<cell>.geolibre.json``,
    ``buildings_wgs84.geojson``, ``geolibre_viewer.html``, and
    ``sources_manifest.json``.

    Args:
        run_dir: Stage 1-6 OpenUBEM run directory opened read-only.
        output_dir: Optional output directory path override.
        buildings_path: Optional explicit building vector file override.
        results_csv_path: Optional results CSV to left-join onto footprints.
        district_filter: Optional district code filter for multi-site CSVs.
        basemap: GeoLibre basemap name or MapLibre style URL.
        color_by: Optional numeric column for graduated choropleth styling.
        colormap: GeoLibre color ramp name.
        scheme: Classification scheme (``"quantile"`` or ``"equal-interval"``).
        class_count: Number of graduated classes (2-12).
        extrude: Enable 2.5D ``fill-extrusion`` by ``extrusion_height_m``.
        include_story_map: Attach an interactive Story Map walkthrough.

    Returns:
        Dictionary mapping ``"output_dir"``, ``"project"``, ``"geojson"``,
        ``"html"``, and ``"manifest"`` to created file paths.
    """
    run_path = Path(run_dir)
    dest_dir = resolve_geolibre_output_dir(run_path, output_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    project_dict, export_gdf, manifest = build_geolibre_project(
        run_path,
        buildings_path=buildings_path,
        results_csv_path=results_csv_path,
        district_filter=district_filter,
        basemap=basemap,
        color_by=color_by,
        colormap=colormap,
        scheme=scheme,
        class_count=class_count,
        extrude=extrude,
        include_story_map=include_story_map,
    )

    slug = _sanitize_slug(manifest["cell_name"])
    project_path = dest_dir / f"{slug}.geolibre.json"
    geojson_path = dest_dir / "buildings_wgs84.geojson"
    html_path = dest_dir / "geolibre_viewer.html"
    manifest_path = dest_dir / "sources_manifest.json"

    gl = _import_geolibre()
    theme = "dark" if basemap == "dark" else "light"
    if gl is not None:
        authoring, _, render_project_html = gl
        authoring.save_project(project_path, project_dict)
        html_text = render_project_html(
            copy.deepcopy(project_dict),
            title=f"OpenUBEM GeoLibre - {manifest['cell_name']}",
            height="100vh",
            theme=theme,
        )
    else:
        _atomic_write_json(project_path, project_dict)
        html_text = _render_fallback_html(
            project_dict,
            title=f"OpenUBEM GeoLibre - {manifest['cell_name']}",
            theme=theme,
        )

    export_gdf.to_file(geojson_path, driver="GeoJSON")
    html_path.write_text(html_text, encoding="utf-8")
    _atomic_write_json(manifest_path, manifest)

    return {
        "output_dir": dest_dir,
        "project": project_path,
        "geojson": geojson_path,
        "html": html_path,
        "manifest": manifest_path,
    }


def create_geolibre_map(
    run_dir: Path | str,
    *,
    height: str = "760px",
    app_layout: str = "full",
    theme: str = "dark",
    **project_kwargs: Any,
) -> Any:
    """Create an interactive ``geolibre.Map`` widget for Jupyter notebooks.

    Args:
        run_dir: Stage 1-6 OpenUBEM run directory opened read-only.
        height: CSS widget height (e.g. ``"760px"``).
        app_layout: GeoLibre chrome layout (``"embed"``, ``"full"``, ``"maponly"``).
        theme: Widget UI theme (``"light"`` or ``"dark"``).
        **project_kwargs: Keyword arguments forwarded to
            :func:`build_geolibre_project`.

    Returns:
        Configured ``geolibre.Map`` widget instance with ``.project`` populated.

    Raises:
        ImportError: If the optional ``geolibre`` package is not installed.
    """
    if not has_geolibre():
        raise ImportError(
            "GeoLibre widget requires optional extra: "
            'pip install "openubem[geolibre]"'
        )
    from geolibre import Map

    project_dict, _, _ = build_geolibre_project(run_dir, **project_kwargs)
    widget = Map(height=height, app_layout=app_layout, theme=theme)
    widget.project = project_dict
    return widget
