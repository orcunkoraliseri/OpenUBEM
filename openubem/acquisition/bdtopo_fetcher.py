"""IGN BD TOPO V3 building-footprint adapter (France)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import requests

from openubem.acquisition.footprint_schema import finalize_footprints

DEFAULT_WFS = "https://data.geopf.fr/wfs/ows"
CRS84 = "CRS:84"  # EPSG:4326 with latitude/longitude here silently returns zero features.
ATTRIBUTION = "IGN — BD TOPO"
LICENCE = "Licence Ouverte / Open Licence 2.0 (Etalab)"


def classify_bdtopo_use(gdf: gpd.GeoDataFrame) -> gpd.Series:
    """Apply the pinned ``usage_1 OR usage_2`` rule without losing raw tags.

    ``usage_2`` is intentionally carried in ``surplus_tags`` by the normalizer;
    classification therefore remains available after schema validation.
    """
    crosswalk_path = Path(__file__).parents[1] / "data" / "bdtopo_to_use_class.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))

    def classify(row: pd.Series) -> str:
        primary = row["building_tag"]
        secondary = json.loads(row["surplus_tags"]).get("usage_2", "")
        values = [value for value in (primary, secondary) if value not in (None, "")]
        unknown = [value for value in values if value not in crosswalk]
        if unknown:
            raise ValueError(f"BD TOPO crosswalk has no mapping for {unknown!r}")
        classes = [crosswalk[value] for value in values]
        if "residential" in classes:
            return "residential"
        # Annexes are removable only where neither use field says residential.
        if "annex" in classes:
            return "annex"
        if "unknown" in classes:
            return "unknown"
        return "non_residential"

    return gdf.apply(classify, axis=1)


def _features(payload: dict[str, Any]) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame.from_features(payload.get("features", []), crs="EPSG:4326")


def fetch_bdtopo(
    bbox: tuple[float, float, float, float] | None = None,
    *, slice_path: Path | str | None = None,
    endpoint: str = DEFAULT_WFS,
    page_size: int = 5000,
) -> gpd.GeoDataFrame:
    """Fetch BDTOPO_V3:batiment with deterministic cleabs paging.

    ``bbox`` follows OpenUBEM ordering: north, south, east, west. The WFS BBOX is
    explicitly longitude, latitude, longitude, latitude with CRS:84.
    """
    if slice_path is not None:
        return gpd.read_file(slice_path)
    if bbox is None:
        raise ValueError("bbox or slice_path is required")
    north, south, east, west = bbox
    base = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": "BDTOPO_V3:batiment", "OUTPUTFORMAT": "application/json", "COUNT": page_size, "SORTBY": "cleabs", "BBOX": f"{west},{south},{east},{north},{CRS84}"}
    frames = []
    start = 0
    while True:
        response = requests.get(endpoint, params={**base, "STARTINDEX": start}, timeout=90)
        response.raise_for_status()
        page = _features(response.json())
        frames.append(page)
        if len(page) < page_size: break
        start += page_size
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs="EPSG:4326") if frames else gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")


def _parse_bdtopo_year(dates: pd.Series, current_year: int = 2026) -> pd.Series:
    """Extract leading 4-digit calendar year from date_d_apparition.

    Rejects years < 1000 and years > current_year by returning pd.NA.
    Leaves non-matching or null values as pd.NA.
    """
    extracted = dates.dropna().astype(str).str.extract(r"^(\d{4})", expand=False)
    numeric = pd.to_numeric(extracted, errors="coerce").astype("Int64")
    invalid = (numeric < 1000) | (numeric > current_year)
    clean = numeric.mask(invalid, pd.NA)
    out = pd.Series(pd.NA, index=dates.index, dtype="Int64")
    out.update(clean)
    return out


def ingest_bdtopo(*, bbox: tuple[float, float, float, float] | None = None, slice_path: Path | str | None = None, output_dir: Path | str | None = None) -> gpd.GeoDataFrame:
    raw = fetch_bdtopo(bbox, slice_path=slice_path)
    required = {"cleabs", "usage_1", "nombre_d_etages", "hauteur", "date_d_apparition"}
    missing = required - set(raw.columns)
    if missing: raise ValueError(f"BD TOPO response misses required fields: {sorted(missing)}")
    out = gpd.GeoDataFrame(geometry=raw.geometry, crs=raw.crs)
    out["osm_id"] = raw["cleabs"].astype(str)
    if not out.osm_id.is_unique: raise ValueError("BD TOPO cleabs values are not unique")
    out["building_tag"] = raw["usage_1"].fillna("").astype(str)
    out["function_tag"] = ""
    out["levels"] = pd.to_numeric(raw["nombre_d_etages"], errors="coerce").round().astype("Int64")
    out["height_m"] = pd.to_numeric(raw["hauteur"], errors="coerce").astype(float)
    out["year_built"] = _parse_bdtopo_year(raw["date_d_apparition"])
    out["postcode"] = None; out["underground"] = pd.array([0] * len(out), dtype="Int64"); out["roof_shape"] = ""; out["roof_height_m"] = float("nan")
    extras = ["usage_2", "nombre_de_logements", "materiaux_des_murs", "appariement_fichiers_fonciers"]
    out["surplus_tags"] = [json.dumps({c: str(raw.iloc[i][c]) for c in extras if c in raw and pd.notna(raw.iloc[i][c])}, ensure_ascii=False) for i in range(len(raw))]
    return finalize_footprints(out, source="IGN_BDTOPO", output_dir=output_dir)
