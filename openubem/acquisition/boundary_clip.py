"""Selected-neighbourhood clipping and NS-08 exclusion manifests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import geopandas as gpd


def clip_to_boundary(
    gdf: gpd.GeoDataFrame,
    boundary_geojson: Path | str,
    *,
    verify_sha256: str | None = None,
) -> gpd.GeoDataFrame:
    """Keep footprints whose representative point lies within the pinned boundary.

    Representative points are deliberately used instead of centroids: a centroid can
    fall outside a concave footprint, while ``representative_point`` cannot.
    """
    path = Path(boundary_geojson)
    if verify_sha256 is not None:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual.lower() != verify_sha256.lower():
            raise ValueError(
                f"Boundary checksum mismatch for {path}: expected {verify_sha256}, got {actual}."
            )
    if gdf.crs is None:
        raise ValueError("Footprint GeoDataFrame must have a CRS before boundary clipping.")

    boundary = gpd.read_file(path)
    if boundary.empty:
        raise ValueError(f"Boundary contains no geometry: {path}")
    boundary = boundary.to_crs(gdf.crs)
    polygon = boundary.geometry.union_all()
    keep = gdf.geometry.representative_point().within(polygon)
    return gdf.loc[keep].copy().reset_index(drop=True)


def _class_for_tag(tag: object, crosswalk: dict[str, Any]) -> str:
    """Resolve a tag using a compact crosswalk into residential/non_residential/unknown."""
    key = "" if tag is None else str(tag)
    value = crosswalk.get(key, crosswalk.get("*", "unknown"))
    if isinstance(value, dict):
        value = value.get("use_class", value.get("classification", "unknown"))
    value = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "residential": "residential",
        "res": "residential",
        "non_residential": "non_residential",
        "nonresidential": "non_residential",
        "non_res": "non_residential",
        "unknown": "unknown",
        "annex": "annex",
    }
    if value not in aliases:
        raise ValueError(f"Crosswalk produces unsupported class {value!r} for tag {key!r}.")
    return aliases[value]


def split_residential(
    gdf: gpd.GeoDataFrame,
    crosswalk: dict[str, Any],
    *,
    unknown_policy: str = "exclude_retain",
    class_column: str = "building_tag",
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, dict[str, int]]:
    """Split a clipped frame into disjoint residential and excluded manifests."""
    if unknown_policy != "exclude_retain":
        raise ValueError(f"Unsupported unknown policy: {unknown_policy}")
    if "osm_id" not in gdf or class_column not in gdf:
        raise ValueError(f"Frame must contain osm_id and {class_column!r} before residential splitting.")
    if not gdf["osm_id"].is_unique:
        raise ValueError("Frame osm_id values must be unique before residential splitting.")

    classes = gdf[class_column].map(lambda tag: _class_for_tag(tag, crosswalk))
    residential = gdf.loc[classes == "residential"].copy()
    excluded = gdf.loc[classes != "residential"].copy()
    excluded["exclusion_reason"] = classes.loc[classes != "residential"].values
    counts = {
        "total": int(len(gdf)),
        "residential": int(len(residential)),
        "unknown": int((classes == "unknown").sum()),
        "non_residential": int((classes == "non_residential").sum()),
        "annexes_removed": int((classes == "annex").sum()),
    }
    if set(residential["osm_id"]).intersection(excluded["osm_id"]):
        raise AssertionError("Residential and excluded manifests are not disjoint.")
    if len(residential) + len(excluded) != len(gdf):
        raise AssertionError("Residential/excluded split does not cover the clipped input.")
    return residential.reset_index(drop=True), excluded.reset_index(drop=True), counts


def write_manifests(
    residential: gpd.GeoDataFrame,
    excluded: gpd.GeoDataFrame,
    counts: dict[str, int],
    output_dir: Path | str,
    *,
    neighbourhood_id: str,
    source_endpoint: str | None = None,
    licence: str | None = None,
    source_layer: str | None = None,
) -> None:
    """Write the NS-08 manifest trio and an acquisition-provenance sidecar.

    The three ``02_*`` files are the stable NS-08 artefacts.  ``01_source.json``
    is deliberately separate so an endpoint or licence correction never changes
    the building manifests themselves.
    """
    if not neighbourhood_id:
        raise ValueError("neighbourhood_id is required for a site manifest.")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    residential.to_file(output / "02_residential_manifest.gpkg", layer="buildings", driver="GPKG")
    excluded.to_file(output / "02_excluded_manifest.gpkg", layer="buildings", driver="GPKG")
    payload = {"neighbourhood_id": neighbourhood_id, **counts}
    (output / "02_exclusion_counts.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    sidecar = {
        "neighbourhood_id": neighbourhood_id,
        "source_endpoint": source_endpoint,
        "source_layer": source_layer,
        "licence": licence,
    }
    (output / "01_source.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
