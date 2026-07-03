"""Step-5 viewer exporter: real run artifacts -> one self-contained HTML (T13).

Post-processor (runs after `05_results.*` + summary exist). It calls the T03
emitter + T05/T06 attribute binding + T07 metadata, then injects the CityJSON
scene payload into the FROZEN, vendored shell (`shell/viewer.html.template` +
`shell/viewer.js` + `shell/viewer.css`) and writes a single offline file at
`openubem/outputs/<run_id>_viewer.html`.

Self-contained is BINDING (PLAN §2, T13): everything is inlined — the esbuild
IIFE bundle, the CSS, and the scene as an inline `application/json` block — so
the file opens from `file://` with ZERO network requests. The per-run pipeline
stays pure Python; the JS shell is built once and vendored (see shell/BUILD.md).

Determinism (T14 CP-Reproducibility): the scene serializes with sorted keys +
sorted `osm_id` order + stable float repr, so two exports of the same run state
are byte-identical EXCEPT the single un-hashed build-timestamp field.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.viz.attribute_binding import bind_provenance, bind_values
from openubem.viz.basemap_raster import BASEMAP_PNG_NAME, BASEMAP_SIDECAR_NAME
from openubem.viz.cityjson_emitter import build_cityjson
from openubem.viz.geojson_context import build_context_geojson
from openubem.viz.metadata_block import add_metadata_block, content_hash

_SHELL_DIR = Path(__file__).parent / "shell"
_TEMPLATE = _SHELL_DIR / "viewer.html.template"
_BUNDLE = _SHELL_DIR / "viewer.js"
_STYLE = _SHELL_DIR / "viewer.css"
_OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"

# Standard per-run artifact filenames (Step-1/3/5 outputs).
_RESULTS_CSV = "05_results.csv"
_BUILDINGS_GPKG = "01_buildings.gpkg"


def _resolve_basemap_files(basemap_path: Path) -> tuple[Path, Path] | None:
    """Accept either the per-run directory T16 writes into, or the PNG itself.

    Returns `(png_path, json_path)` if both files exist, else `None` — the
    caller treats that as "no basemap for this run" (graceful, PLAN T19).
    """
    p = Path(basemap_path)
    if p.is_dir():
        png_path, json_path = p / BASEMAP_PNG_NAME, p / BASEMAP_SIDECAR_NAME
    elif p.suffix.lower() == ".png":
        png_path, json_path = p, p.with_suffix(".json")
    else:
        return None
    if png_path.exists() and json_path.exists():
        return png_path, json_path
    return None


def _load_basemap(basemap_path: Path | str | None, origin) -> dict | None:
    """T16 cache -> the scene's `"basemap"` entry (embedded data-URI, PLAN §2:
    fetched ONCE at generation time — no runtime fetch, ever).

    Missing/unreadable cache -> `None` (the key is simply omitted from the
    scene, T19's graceful degrade; the basemap is additive, never blocking).
    """
    if basemap_path is None:
        return None
    files = _resolve_basemap_files(Path(basemap_path))
    if files is None:
        return None
    png_path, json_path = files
    try:
        sidecar = json.loads(json_path.read_text(encoding="utf-8"))
        image_bytes = png_path.read_bytes()
        minx, miny, maxx, maxy = (float(v) for v in sidecar["extent_utm"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return None
    ox, oy, _ = origin
    data_uri = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")
    return {
        "image": data_uri,
        "extent_local": [minx - ox, miny - oy, maxx - ox, maxy - oy],
        "attribution": sidecar.get("attribution", ""),
        "crs": sidecar.get("crs", ""),
    }


def build_scene(
    manifest_df: pd.DataFrame,
    buildings_gdf: gpd.GeoDataFrame,
    results_df: pd.DataFrame,
    *,
    run_id: str,
    source_refs: dict | None = None,
    repo_dir: str | None = None,
    timestamp: str | None = None,
    basemap_path: Path | str | None = None,
) -> dict:
    """Assemble the full scene payload dict: geometry + values + provenance +
    metadata + failed/absent placeholders + an optional cached basemap (T16).

    Returns `{"cityjson", "context", "provenance_coverage"}` (+ `"basemap"`
    when a cached raster is found at `basemap_path` — T16's per-run directory
    or the `06_basemap_utm.png` file directly; absent/unreadable -> the key is
    simply omitted, never a placeholder). `timestamp` is forwarded to the
    metadata block (pass a fixed value to compare two builds).
    """
    cityjson = build_cityjson(manifest_df, buildings_gdf)
    bind_values(cityjson, results_df, buildings_gdf)
    coverage = bind_provenance(cityjson, manifest_df, results_df, buildings_gdf)
    add_metadata_block(
        cityjson,
        run_id=run_id,
        provenance_coverage=coverage,
        source_refs=source_refs or {},
        repo_dir=repo_dir,
        timestamp=timestamp,
    )
    origin = cityjson["metadata"]["+common_origin_utm"]
    context = build_context_geojson(
        buildings_gdf, set(cityjson["CityObjects"].keys()), origin)
    scene = {"cityjson": cityjson, "context": context,
             "provenance_coverage": coverage}
    basemap = _load_basemap(basemap_path, origin)
    if basemap is not None:
        scene["basemap"] = basemap
    return scene


def _scene_json(scene: dict) -> str:
    """Deterministic scene serialization for inline embedding.

    `sort_keys` fixes CityObject/attribute ordering; the emitter already emits
    vertices + surfaces in a stable order and the context features are pre-sorted
    by osm_id. `</` is escaped to `<\\/` (a legal JSON escape) so no string value
    can prematurely close the host `<script>` element.
    """
    raw = json.dumps(scene, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False)
    return raw.replace("</", "<\\/")


def _inject(scene: dict, run_id: str) -> str:
    template = _TEMPLATE.read_text(encoding="utf-8")
    bundle = _BUNDLE.read_text(encoding="utf-8")
    style = _STYLE.read_text(encoding="utf-8")
    payload = _scene_json(scene)
    # Fill the controlled slots first, the large untrusted payload LAST so an
    # earlier replacement can never match inside it.
    html = (template
            .replace("__RUN_ID__", run_id)
            .replace("__VIEWER_CSS__", style)
            .replace("__VIEWER_JS__", bundle)
            .replace("__SCENE_PAYLOAD__", payload))
    return html


def export_viewer(
    manifest_df: pd.DataFrame,
    buildings_gdf: gpd.GeoDataFrame,
    results_df: pd.DataFrame,
    *,
    run_id: str,
    out_dir: Path | str | None = None,
    source_refs: dict | None = None,
    repo_dir: str | None = None,
    timestamp: str | None = None,
    basemap_path: Path | str | None = None,
) -> dict:
    """Build the scene and write `<out_dir>/<run_id>_viewer.html`.

    Returns a small result dict: `html_path`, `content_hash` (timestamp-excluded),
    `n_buildings`, `n_context`, `size_bytes`, `has_basemap`.
    """
    scene = build_scene(
        manifest_df, buildings_gdf, results_df,
        run_id=run_id, source_refs=source_refs, repo_dir=repo_dir,
        timestamp=timestamp, basemap_path=basemap_path)
    html = _inject(scene, run_id)

    out = Path(out_dir) if out_dir is not None else _OUTPUTS_DIR
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{run_id}_viewer.html"
    path.write_text(html, encoding="utf-8")

    return {
        "html_path": str(path),
        "content_hash": content_hash(scene["cityjson"]),
        "n_buildings": len(scene["cityjson"]["CityObjects"]),
        "n_context": len(scene["context"]["features"]),
        "size_bytes": path.stat().st_size,
        "has_basemap": "basemap" in scene,
    }


def export_viewer_from_run(
    *,
    run_id: str,
    results_dir: Path | str,
    manifest_path: Path | str,
    buildings_path: Path | str | None = None,
    out_dir: Path | str | None = None,
    repo_dir: str | None = None,
    timestamp: str | None = None,
    basemap_path: Path | str | None = None,
) -> dict:
    """Convenience wrapper resolving the standard per-run artifact paths.

    `results_dir` holds `05_results.csv` (+ `01_buildings.gpkg` unless
    `buildings_path` overrides). `manifest_path` is the Step-3 IDF manifest
    (needs `osm_id` + `idf_path`). `basemap_path` defaults to `results_dir`
    (T16 caches `06_basemap_utm.png`/`.json` alongside `01_buildings.gpkg`,
    same per-run-snapshot discipline); pass `basemap_path=None` explicitly via
    a caller that overrides this wrapper if a run has no basemap on disk —
    `_load_basemap` already degrades gracefully when the files are absent.
    """
    results_dir = Path(results_dir)
    results_df = pd.read_csv(results_dir / _RESULTS_CSV)
    bpath = Path(buildings_path) if buildings_path is not None \
        else results_dir / _BUILDINGS_GPKG
    buildings_gdf = gpd.read_file(bpath)
    manifest_df = pd.read_parquet(manifest_path)
    bmpath = basemap_path if basemap_path is not None else results_dir

    return export_viewer(
        manifest_df, buildings_gdf, results_df,
        run_id=run_id, out_dir=out_dir,
        source_refs={"results": _RESULTS_CSV, "buildings": bpath.name,
                     "manifest": Path(manifest_path).name},
        repo_dir=repo_dir, timestamp=timestamp, basemap_path=bmpath)
