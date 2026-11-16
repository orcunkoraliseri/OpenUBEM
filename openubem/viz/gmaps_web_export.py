"""Standalone Google Maps 3D Web Companion & AI Studio bundle exporter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd

_CANDIDATE_BUILDING_FILES = (
    "06_mc_summary.gpkg",
    "05_results.gpkg",
    "buildings.parquet",
    "buildings.gpkg",
    "buildings.geojson",
    "02_buildings_imputed.gpkg",
    "01_buildings_clean.gpkg",
    "01_buildings_raw.gpkg",
    "01_buildings.gpkg",
)

_EXPORT_COLUMNS = (
    "osm_id",
    "height_m",
    "levels",
    "use_class",
    "function_tag",
    "roof_shape",
    "gmaps_solar_pitch_deg",
    "gmaps_solar_azimuth_deg",
    "gmaps_solar_max_panels",
    "gmaps_places_primary_type",
    "utci_peak_c",
    "utci_mean_c",
    "ctsi_degc_h",
    "aq_ambient_aqi",
    "aq_ambient_category",
    "aq_provenance",
)


def resolve_companion_output_dir(
    run_dir: Path,
    output_dir: Path | None = None,
) -> Path:
    """Resolves a mutable output directory outside frozen validation snapshots.

    Args:
        run_dir: Input OpenUBEM stage run directory (read-only).
        output_dir: Optional user-specified output directory.

    Returns:
        Resolved writable directory path outside ``docs/docs_VALIDATION/``.

    Raises:
        ValueError: If an explicit ``output_dir`` targets ``docs_VALIDATION``.
    """
    run_path = Path(run_dir).resolve()
    if output_dir is not None:
        explicit = Path(output_dir).resolve()
        if "docs_VALIDATION" in explicit.parts:
            raise ValueError(
                "Refusing to write companion artifacts inside docs_VALIDATION/: "
                f"{explicit}"
            )
        return explicit

    if "docs_VALIDATION" in run_path.parts:
        repo_root = Path(__file__).resolve().parents[2]
        return repo_root / "openubem" / "outputs" / "gmaps_companion" / run_path.name
    return run_path / "gmaps_companion"


def _load_read_only_buildings(
    run_dir: Path,
    buildings_path: Path | None = None,
) -> tuple[gpd.GeoDataFrame, list[str]]:
    """Loads building polygons read-only from the richest available stage file.

    Args:
        run_dir: Stage run root directory.
        buildings_path: Optional explicit buildings vector file override.

    Returns:
        Tuple ``(buildings_gdf, loaded_source_names)``.

    Raises:
        FileNotFoundError: If no supported buildings file is found.
    """
    used_files: list[str] = []
    if buildings_path is not None:
        explicit = Path(buildings_path)
        gdf = (
            gpd.read_parquet(explicit)
            if explicit.suffix.lower() == ".parquet"
            else gpd.read_file(explicit)
        )
        used_files.append(str(explicit.name))
        return gdf, used_files

    for rel in _CANDIDATE_BUILDING_FILES:
        cand = run_dir / rel
        if cand.is_file():
            gdf = (
                gpd.read_parquet(cand)
                if cand.suffix.lower() == ".parquet"
                else gpd.read_file(cand)
            )
            used_files.append(rel)
            return gdf, used_files

    raise FileNotFoundError(
        f"No OpenUBEM building vector file found under {run_dir}."
    )


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    """Safely reads a JSON file when it exists, returning ``None`` otherwise.

    Args:
        path: Candidate JSON file path.

    Returns:
        Parsed JSON dictionary or ``None``.
    """
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _render_companion_html(
    *,
    center_lat: float,
    center_lon: float,
    title: str,
) -> str:
    """Renders standalone HTML hosting Google Maps ``<gmp-map-3d>`` viewer.

    API keys are supplied purely at runtime via ``?apiKey=...`` query params,
    ``sessionStorage``, or the UI key input — never embedded in HTML source.

    Args:
        center_lat: District center WGS 84 latitude.
        center_lon: District center WGS 84 longitude.
        title: Document header title for the cell bundle.

    Returns:
        Complete standalone HTML5 document string.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OpenUBEM 3D Companion - {title}</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: rgba(15, 23, 42, 0.92);
      --border: rgba(148, 163, 184, 0.25);
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      font-family: system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    #layout {{ display: grid; grid-template-columns: 340px 1fr; height: 100vh; }}
    #sidebar {{
      padding: 16px;
      border-right: 1px solid var(--border);
      background: var(--panel);
      overflow-y: auto;
    }}
    h1 {{ font-size: 1.05rem; margin: 0 0 8px; }}
    p.meta {{ font-size: 0.85rem; color: var(--muted); margin: 0 0 12px; }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 12px;
    }}
    label {{
      display: block;
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    input {{
      width: 100%;
      padding: 7px 9px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #020617;
      color: var(--text);
      margin-bottom: 8px;
    }}
    button {{
      width: 100%;
      padding: 8px 10px;
      border: none;
      border-radius: 6px;
      background: var(--accent);
      color: #020617;
      font-weight: 600;
      cursor: pointer;
    }}
    #map-host {{ position: relative; width: 100%; height: 100%; }}
    gmp-map-3d {{ width: 100%; height: 100%; display: block; }}
    pre {{ white-space: pre-wrap; font-size: 0.78rem; color: #e2e8f0; margin: 0; }}
  </style>
</head>
<body>
  <div id="layout">
    <aside id="sidebar">
      <h1>OpenUBEM 3D Companion</h1>
      <p class="meta">Cell: {title} ({center_lat:.5f}, {center_lon:.5f})</p>
      <div class="card">
        <label for="api-key-input">Runtime Google Maps API Key (session only)</label>
        <input
          id="api-key-input"
          type="password"
          placeholder="Paste API key or pass ?apiKey="
          autocomplete="off"
        />
        <button id="load-map-btn" type="button">Load Photorealistic 3D Map</button>
      </div>
      <div class="card">
        <label>Overlay Summary</label>
        <pre id="stats-box">Loading buildings_wgs84.geojson...</pre>
      </div>
      <div class="card">
        <label>Sources &amp; Risk Context</label>
        <pre id="manifest-box">Loading sources_manifest.json...</pre>
      </div>
    </aside>
    <main id="map-host">
      <div id="map-status" style="padding: 24px; color: #94a3b8;">
        Enter a runtime Google Maps API key (or open with ?apiKey=...) to
        initialize &lt;gmp-map-3d&gt;.
      </div>
      <gmp-map-3d id="ubem-map-3d" mode="hybrid" hidden></gmp-map-3d>
    </main>
  </div>
  <script>
    (function () {{
      const centerLat = {center_lat:.6f};
      const centerLon = {center_lon:.6f};
      const params = new URLSearchParams(window.location.search);
      const statsBox = document.getElementById("stats-box");
      const manifestBox = document.getElementById("manifest-box");
      const keyInput = document.getElementById("api-key-input");
      const loadBtn = document.getElementById("load-map-btn");

      fetch("./buildings_wgs84.geojson")
        .then((r) => r.json())
        .then((gj) => {{
          const feats = Array.isArray(gj.features) ? gj.features : [];
          statsBox.textContent =
            "Features: " + feats.length + " buildings loaded (WGS 84).";
        }})
        .catch(() => {{
          statsBox.textContent =
            "Run via static server to fetch buildings_wgs84.geojson.";
        }});

      fetch("./sources_manifest.json")
        .then((r) => r.json())
        .then((m) => {{
          manifestBox.textContent = JSON.stringify({{
            building_count: m.building_count,
            risk_tier: m.risk_tier || null,
            utci_peak_max_c: m.utci_peak_max_c ?? null,
            aq_provenance: m.aq_provenance || null
          }}, null, 2);
        }})
        .catch(() => {{
          manifestBox.textContent = "Manifest unavailable via file:// origin.";
        }});

      function mountMap(apiKey) {{
        if (!apiKey) return;
        sessionStorage.setItem("OPENUBEM_GMAPS_KEY", apiKey);
        const statusEl = document.getElementById("map-status");
        if (statusEl) statusEl.hidden = true;
        const mapEl = document.getElementById("ubem-map-3d");
        mapEl.hidden = false;
        mapEl.setAttribute("center", centerLat + "," + centerLon);
        mapEl.setAttribute("range", "650");
        mapEl.setAttribute("tilt", "58");
        mapEl.setAttribute("heading", "25");

        if (!document.getElementById("gmaps-3d-sdk")) {{
          const script = document.createElement("script");
          script.id = "gmaps-3d-sdk";
          script.async = true;
          script.src =
            "https://maps.googleapis.com/maps/api/js?key=" +
            encodeURIComponent(apiKey) +
            "&v=alpha&libraries=maps3d";
          document.head.appendChild(script);
        }}
      }}

      const initialKey =
        params.get("apiKey") ||
        sessionStorage.getItem("OPENUBEM_GMAPS_KEY") ||
        "";
      if (initialKey) {{
        keyInput.value = initialKey;
        mountMap(initialKey);
      }}
      loadBtn.addEventListener("click", () => mountMap(keyInput.value.trim()));
    }})();
  </script>
</body>
</html>
"""


def _render_ai_studio_prompt(manifest: dict[str, Any]) -> str:
    """Generates a ready-to-paste Google AI Studio / Analytics Playground brief.

    Args:
        manifest: Exported ``sources_manifest.json`` summary dictionary.

    Returns:
        Markdown prompt document customized to the district cell.
    """
    lat = manifest["center_lat"]
    lon = manifest["center_lon"]
    n_bld = manifest["building_count"]
    classes = manifest.get("use_class_counts") or {}
    utci_peak = manifest.get("utci_peak_max_c")
    risk_tier = manifest.get("risk_tier") or "Not evaluated"
    aq = manifest.get("air_quality") or {}

    lines = [
        f"# OpenUBEM Google Geospatial AI Studio Prompt ({manifest['cell_name']})",
        "",
        "Paste this brief into **Google AI Studio** or the **Google Maps",
        "Geospatial Analytics Playground** to cross-examine urban morphology,",
        "microclimate exposure, and POI/SVI ground truth:",
        "",
        "## District Snapshot",
        f"- **Centroid (WGS 84):** `{lat:.6f}, {lon:.6f}`",
        f"- **Footprints in bundle:** `{n_bld}`",
        f"- **Use-class distribution:** `{json.dumps(classes)}`",
        f"- **Peak Stage 6 UTCI:** `{utci_peak}` ({risk_tier})",
        f"- **Ambient Air Quality context:** `{json.dumps(aq)}`",
        "",
        "## Recommended Investigation Prompts",
        "1. Cross-check commercial/mixed ground-floor activity using Google Places",
        "   Insights within a 500 m radius of this centroid (`restaurants`,",
        "   `supermarkets`, `offices`) against the `use_class` counts above.",
        "2. Inspect Photorealistic 3D Tiles and Solar API roof geometry around",
        "   the hottest microclimate parcels in `buildings_wgs84.geojson` for",
        "   shading trees, cool-roof albedo interventions, or PV eligibility.",
        "3. Validate facade glazing/story assumptions via Street View Insights",
        "   where OpenUBEM flags imputed height or default WWR.",
    ]
    return "\n".join(lines) + "\n"


def export_gmaps_companion_bundle(
    run_dir: Path,
    *,
    output_dir: Path | None = None,
    buildings_path: Path | None = None,
) -> dict[str, Path]:
    """Exports read-only OpenUBEM results into a Google Maps 3D Web Companion bundle.

    Generates four files inside a mutable destination directory (never writing
    into ``docs/docs_VALIDATION/``): ``buildings_wgs84.geojson``,
    ``sources_manifest.json``, ``companion_3d_app.html``, and
    ``ai_studio_prompt.md``.

    Args:
        run_dir: Stage 1-6 OpenUBEM run directory opened read-only.
        output_dir: Optional output directory path.
        buildings_path: Optional explicit buildings vector file path.

    Returns:
        Dictionary mapping ``"output_dir"``, ``"geojson"``, ``"manifest"``,
        ``"html"``, and ``"ai_studio_prompt"`` to created paths.
    """
    run_path = Path(run_dir)
    dest_dir = resolve_companion_output_dir(run_path, output_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    raw_gdf, loaded_sources = _load_read_only_buildings(
        run_path,
        buildings_path=buildings_path,
    )
    if raw_gdf.crs is None:
        raise ValueError("Buildings layer must carry a valid CRS for WGS 84 export.")

    wgs_gdf = raw_gdf.to_crs(epsg=4326).copy()
    keep_cols = [col for col in _EXPORT_COLUMNS if col in wgs_gdf.columns]
    export_gdf = wgs_gdf[keep_cols + ["geometry"]].copy()

    geojson_path = dest_dir / "buildings_wgs84.geojson"
    export_gdf.to_file(geojson_path, driver="GeoJSON")

    centroid_pts = gpd.GeoSeries(
        raw_gdf.to_crs(raw_gdf.estimate_utm_crs()).geometry.centroid,
        crs=raw_gdf.estimate_utm_crs(),
    ).to_crs(epsg=4326)
    center_lat = float(centroid_pts.y.mean()) if not centroid_pts.empty else 0.0
    center_lon = float(centroid_pts.x.mean()) if not centroid_pts.empty else 0.0

    exposure = _read_optional_json(run_path / "06_mc_exposure_metrics.json") or {}
    risk_alerts = _read_optional_json(run_path / "06_mc_risk_alerts.json") or {}

    use_counts: dict[str, int] = {}
    if "use_class" in export_gdf.columns:
        vc = export_gdf["use_class"].fillna("unknown").astype(str).value_counts()
        use_counts = {str(k): int(v) for k, v in vc.items()}

    manifest: dict[str, Any] = {
        "cell_name": run_path.name,
        "source_files_read_only": loaded_sources,
        "building_count": int(len(export_gdf)),
        "center_lat": round(center_lat, 6),
        "center_lon": round(center_lon, 6),
        "use_class_counts": use_counts,
        "utci_peak_max_c": exposure.get("utci_peak_max_c"),
        "ctsi_mean_degc_h": exposure.get("ctsi_mean_degc_h"),
        "risk_tier": risk_alerts.get("risk_tier"),
        "air_quality": exposure.get("air_quality"),
        "aq_provenance": (
            str(export_gdf["aq_provenance"].dropna().iloc[0])
            if "aq_provenance" in export_gdf.columns
            and export_gdf["aq_provenance"].notna().any()
            else None
        ),
        "api_key_embedded": False,
    }
    manifest_path = dest_dir / "sources_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    html_path = dest_dir / "companion_3d_app.html"
    html_path.write_text(
        _render_companion_html(
            center_lat=center_lat,
            center_lon=center_lon,
            title=run_path.name,
        ),
        encoding="utf-8",
    )

    prompt_path = dest_dir / "ai_studio_prompt.md"
    prompt_path.write_text(
        _render_ai_studio_prompt(manifest),
        encoding="utf-8",
    )

    return {
        "output_dir": dest_dir,
        "geojson": geojson_path,
        "manifest": manifest_path,
        "html": html_path,
        "ai_studio_prompt": prompt_path,
    }
