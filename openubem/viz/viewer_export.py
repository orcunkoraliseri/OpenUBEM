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

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.viz.attribute_binding import bind_provenance, bind_values
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


def build_scene(
    manifest_df: pd.DataFrame,
    buildings_gdf: gpd.GeoDataFrame,
    results_df: pd.DataFrame,
    *,
    run_id: str,
    source_refs: dict | None = None,
    repo_dir: str | None = None,
    timestamp: str | None = None,
) -> dict:
    """Assemble the full scene payload dict: geometry + values + provenance +
    metadata + failed/absent placeholders.

    Returns `{"cityjson", "context", "provenance_coverage"}`. `timestamp` is
    forwarded to the metadata block (pass a fixed value to compare two builds).
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
    return {"cityjson": cityjson, "context": context,
            "provenance_coverage": coverage}


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
) -> dict:
    """Build the scene and write `<out_dir>/<run_id>_viewer.html`.

    Returns a small result dict: `html_path`, `content_hash` (timestamp-excluded),
    `n_buildings`, `n_context`, `size_bytes`.
    """
    scene = build_scene(
        manifest_df, buildings_gdf, results_df,
        run_id=run_id, source_refs=source_refs, repo_dir=repo_dir,
        timestamp=timestamp)
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
) -> dict:
    """Convenience wrapper resolving the standard per-run artifact paths.

    `results_dir` holds `05_results.csv` (+ `01_buildings.gpkg` unless
    `buildings_path` overrides). `manifest_path` is the Step-3 IDF manifest
    (needs `osm_id` + `idf_path`).
    """
    results_dir = Path(results_dir)
    results_df = pd.read_csv(results_dir / _RESULTS_CSV)
    bpath = Path(buildings_path) if buildings_path is not None \
        else results_dir / _BUILDINGS_GPKG
    buildings_gdf = gpd.read_file(bpath)
    manifest_df = pd.read_parquet(manifest_path)

    return export_viewer(
        manifest_df, buildings_gdf, results_df,
        run_id=run_id, out_dir=out_dir,
        source_refs={"results": _RESULTS_CSV, "buildings": bpath.name,
                     "manifest": Path(manifest_path).name},
        repo_dir=repo_dir, timestamp=timestamp)
