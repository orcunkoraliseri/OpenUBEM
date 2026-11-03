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
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.viz.attribute_binding import bind_provenance, bind_values
from openubem.viz.basemap_raster import BASEMAP_PNG_NAME, BASEMAP_SIDECAR_NAME
from openubem.viz.cityjson_emitter import build_cityjson
from openubem.viz.context_features import BLOCKS_NAME, GREEN_NAME, ROADS_NAME
from openubem.viz.geojson_context import build_context_geojson, translate_geojson_geometry
from openubem.viz.metadata_block import add_metadata_block, content_hash
from openubem.viz.utci_layer import UTCI_LAYER_PNG_NAME, UTCI_LAYER_SIDECAR_NAME

_CONTEXT_ATTRIBUTION = "© OpenStreetMap contributors"

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


def _resolve_utci_layer_files(utci_layer_path: Path) -> tuple[Path, Path] | None:
    """Same accept-dir-or-file convention as `_resolve_basemap_files` (T25)."""
    p = Path(utci_layer_path)
    if p.is_dir():
        png_path, json_path = p / UTCI_LAYER_PNG_NAME, p / UTCI_LAYER_SIDECAR_NAME
    elif p.suffix.lower() == ".png":
        png_path, json_path = p, p.with_suffix(".json")
    else:
        return None
    if png_path.exists() and json_path.exists():
        return png_path, json_path
    return None


def _load_utci_layer(utci_layer_path: Path | str | None, origin) -> dict | None:
    """T25: an OPTIONAL, additive ground-plane layer -- `openubem.viz.utci_layer.bake_utci_layer`
    cache -> the scene's `"utci_layer"` entry (embedded data-URI, no runtime fetch, same
    zero-network guarantee as `_load_basemap`). §6a: UTCI is a separate, unvalidated analysis
    product -- never a co-equal colouring mode, never colours a building; this is a ground-plane
    image only. Missing/unreadable cache, or `utci_layer_path=None` (the default for every
    existing caller) -> the key is simply omitted -- purely additive, never blocking."""
    if utci_layer_path is None:
        return None
    files = _resolve_utci_layer_files(Path(utci_layer_path))
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
        "field": sidecar.get("field", ""),
    }


def _load_one_context_layer(path: Path, ox: float, oy: float) -> dict | None:
    """One `06_context_*.geojson` cache -> a scene-local FeatureCollection.

    Missing/unreadable file -> `None` (T24 graceful degrade, mirrors T19's
    `_load_basemap`). Features are translated UTM -> scene-local metres via
    the SAME `translate_geojson_geometry` helper T04's footprint placeholders
    use (PLAN Phase-G "Scene-frame to mirror"). Feature order is preserved
    from the cache, which `context_features.py` already writes pre-sorted by
    a stable key — no re-sort needed to stay deterministic.
    """
    try:
        fc = json.loads(Path(path).read_text(encoding="utf-8"))
        features = [
            {"type": "Feature",
             "geometry": translate_geojson_geometry(f["geometry"], ox, oy),
             "properties": f.get("properties", {})}
            for f in fc["features"]
        ]
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return None
    return {"type": "FeatureCollection", "features": features}


def _load_urban_context(
    context_features_dir: Path | str | None, origin, reference_system: str,
) -> dict | None:
    """T23 caches -> the scene's `"urban_context"` entry (inline vector
    FeatureCollections, PLAN §2: fetched ONCE at generation time — no runtime
    fetch, ever). Any missing cache -> that sub-key is omitted; all three
    missing -> the whole `urban_context` key is omitted (graceful, like
    `basemap`). Never touches `scene["context"]` (T04 placeholders)."""
    if context_features_dir is None:
        return None
    d = Path(context_features_dir)
    ox, oy, _ = origin

    layers = {}
    for key, name in (("roads", ROADS_NAME), ("green", GREEN_NAME), ("blocks", BLOCKS_NAME)):
        p = d / name
        if p.exists():
            fc = _load_one_context_layer(p, ox, oy)
            if fc is not None:
                layers[key] = fc

    if not layers:
        return None

    layers["frame"] = {
        "referenceSystem": reference_system,
        "common_origin": [ox, oy, 0.0],
    }
    layers["attribution"] = _CONTEXT_ATTRIBUTION
    return layers


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
    context_features_dir: Path | str | None = None,
    utci_layer_path: Path | str | None = None,
) -> dict:
    """Assemble the full scene payload dict: geometry + values + provenance +
    metadata + failed/absent placeholders + an optional cached basemap (T16)
    + optional cached urban-context vectors (T23/T24) + an optional cached
    UTCI ground-plane layer (T25).

    Returns `{"cityjson", "context", "provenance_coverage"}` (+ `"basemap"`
    when a cached raster is found at `basemap_path` — T16's per-run directory
    or the `06_basemap_utm.png` file directly; absent/unreadable -> the key is
    simply omitted, never a placeholder) (+ `"urban_context"` when any of the
    `06_context_{roads,green,blocks}.geojson` caches are found at
    `context_features_dir` — T23's per-run directory; absent/unreadable ->
    the whole key is omitted) (+ `"utci_layer"` when a cached raster from
    `openubem.viz.utci_layer.bake_utci_layer` is found at `utci_layer_path` —
    `utci_layer_path=None` is the default for every existing caller, so the
    key is omitted and the scene is byte-identical to before T25 unless a
    caller explicitly opts in). `timestamp` is forwarded to the metadata block
    (pass a fixed value to compare two builds).
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
    reference_system = cityjson["metadata"]["referenceSystem"]
    context = build_context_geojson(
        buildings_gdf, set(cityjson["CityObjects"].keys()), origin)
    scene = {"cityjson": cityjson, "context": context,
             "provenance_coverage": coverage}
    basemap = _load_basemap(basemap_path, origin)
    if basemap is not None:
        scene["basemap"] = basemap
    urban_context = _load_urban_context(context_features_dir, origin, reference_system)
    if urban_context is not None:
        scene["urban_context"] = urban_context
    utci_layer = _load_utci_layer(utci_layer_path, origin)
    if utci_layer is not None:
        scene["utci_layer"] = utci_layer
    return scene


# T25 conditional-injection markers: the vendored `viewer.js`/`viewer.css`
# shell is a single frozen blob inlined WHOLE into every export (see
# `_inject`), so a runtime `if (!mesh) return` guard inside the bundle is not
# enough to satisfy the byte-identical regression guard -- the marked bytes
# must be physically absent from the HTML whenever no UTCI layer was baked.
# `_UTCI_BLOCK_RE` deletes marker + payload + one trailing newline (works for
# both `\n` and `\r\n` source files) and reconstructs the pre-T25 bundle
# exactly; `_UTCI_MARKER_RE` strips only the marker tokens, keeping the UTCI
# code, for the enabled path. Any future rebuild of `viewer.js` from
# `viewer_app.mjs`/`viewer_logic.mjs` (see shell/BUILD.md) MUST re-wrap the
# UTCI-only additions with these same `/*T25UTCI*/ ... /*T25UTCI!*/` markers.
_UTCI_BLOCK_RE = re.compile(r"/\*T25UTCI\*/.*?/\*T25UTCI!\*/\r?\n", re.DOTALL)
_UTCI_MARKER_RE = re.compile(r"/\*T25UTCI!?\*/")


def _apply_utci_markers(text: str, *, keep: bool) -> str:
    if keep:
        return _UTCI_MARKER_RE.sub("", text)
    return _UTCI_BLOCK_RE.sub("", text)


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
    has_utci_layer = "utci_layer" in scene
    bundle = _apply_utci_markers(bundle, keep=has_utci_layer)
    style = _apply_utci_markers(style, keep=has_utci_layer)
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
    utci_layer_path: Path | str | None = None,
) -> dict:
    """Build the scene and write `<out_dir>/<run_id>_viewer.html`.

    Returns a small result dict: `html_path`, `content_hash` (timestamp-excluded),
    `n_buildings`, `n_context`, `size_bytes`, `has_basemap`, `has_utci_layer`.
    """
    scene = build_scene(
        manifest_df, buildings_gdf, results_df,
        run_id=run_id, source_refs=source_refs, repo_dir=repo_dir,
        timestamp=timestamp, basemap_path=basemap_path, utci_layer_path=utci_layer_path)
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
        "has_utci_layer": "utci_layer" in scene,
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
    utci_layer_path: Path | str | None = None,
) -> dict:
    """Convenience wrapper resolving the standard per-run artifact paths.

    `results_dir` holds `05_results.csv` (+ `01_buildings.gpkg` unless
    `buildings_path` overrides). `manifest_path` is the Step-3 IDF manifest
    (needs `osm_id` + `idf_path`). `basemap_path` defaults to `results_dir`
    (T16 caches `06_basemap_utm.png`/`.json` alongside `01_buildings.gpkg`,
    same per-run-snapshot discipline); pass `basemap_path=None` explicitly via
    a caller that overrides this wrapper if a run has no basemap on disk —
    `_load_basemap` already degrades gracefully when the files are absent.

    `utci_layer_path` (T25) has NO default inference, unlike `basemap_path`:
    Stage 6 is invoked separately from Stage 1-5 (plan §6a) and its output_dir
    routinely differs from `results_dir` (e.g. an archived `docs_VALIDATION`
    cell vs. `openubem/outputs/stage6/<cell>/`, see
    `openubem/microclimate/__init__.py`'s own run_dir/output_dir docstring) —
    a caller must pass the directory holding `openubem.viz.utci_layer`'s own
    cache explicitly. Leaving it `None` (every pre-T25 call site, unchanged)
    omits the layer entirely, exactly like `basemap_path=None` omits the
    basemap.
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
        repo_dir=repo_dir, timestamp=timestamp, basemap_path=bmpath,
        utci_layer_path=utci_layer_path)
