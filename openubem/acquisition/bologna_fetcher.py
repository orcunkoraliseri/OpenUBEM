"""Comune di Bologna building-footprint adapters.

The CTC layer contains volumetric components.  The ruled OpenUBEM building unit is
instead one object from the ``rifter_edif_pl`` cadastral footprint layer; CTC is
kept available solely for the EU-02 reconciliation cross-check.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

from openubem.acquisition.footprint_schema import finalize_footprints

DEFAULT_BASE = "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets"
DEFAULT_DATASET = "rifter_edif_pl"
CTC_DATASET = "c_a944ctc_edifici_pl"
ATTRIBUTION = "Comune di Bologna"
LICENCE = "CC BY 4.0, Comune di Bologna"


def classify_bologna_rifter(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Classify the ruled cadastral footprint layer without treating CTC as final.

    In the measured Galvani-2 slice all non-generic observed typologies are
    excluded.  A new typology fails closed so that the candidate count cannot
    drift without an explicit crosswalk decision.
    """
    residential = {"Edificio generico", ""}
    non_residential = {
        "Baracca", "Cabina", "Cabina ENEL", "Chiesa", "Chiosco giornali",
        "Edificio scolastico", "Mura", "Mura storiche", "Stazione rifornimento",
        "Stazione di rifornimento", "Tettoia",
    }
    values = gdf["building_tag"].fillna("").astype(str)
    unknown = set(values) - residential - non_residential
    if unknown:
        raise ValueError(f"Unlisted Bologna rifter typologia values: {sorted(unknown)}")
    return values.map(lambda value: "residential" if value in residential else "non_residential")


def classify_bologna_ctc(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Classify CTC volumetric bodies with the complete catalogue crosswalk.

    CTC remains a reconciliation-only source.  Its sole residential label is
    ``Edificio generico``; all 29 other observed catalogue values, including an
    empty description, are explicit exclusions.  New values fail closed.
    """
    crosswalk_path = Path(__file__).parents[1] / "data" / "bologna_ctc_to_use_class.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    values = gdf["building_tag"].fillna("").astype(str)
    unknown = set(values) - set(crosswalk)
    if unknown:
        raise ValueError(f"Bologna CTC crosswalk has no mapping for {sorted(unknown)!r}")
    return values.map(crosswalk)


def fetch_bologna(
    dataset: str = DEFAULT_DATASET,
    bbox: tuple[float, float, float, float] | None = None,
    *, slice_path: Path | str | None = None,
    base_url: str = DEFAULT_BASE,
) -> gpd.GeoDataFrame:
    """Fetch an ODS GeoJSON dataset; server-side bbox uses latitude before longitude."""
    if slice_path is not None:
        return gpd.read_file(slice_path)
    params: dict[str, str | int] = {"limit": -1}
    if bbox is not None:
        north, south, east, west = bbox
        params["where"] = f"in_bbox(geo_shape, {south}, {west}, {north}, {east})"
    response = requests.get(f"{base_url}/{dataset}/exports/geojson", params=params, timeout=120)
    response.raise_for_status()
    return gpd.GeoDataFrame.from_features(response.json().get("features", []), crs="EPSG:4326")


def ingest_bologna(
    dataset: str = DEFAULT_DATASET,
    *, bbox: tuple[float, float, float, float] | None = None,
    slice_path: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> gpd.GeoDataFrame:
    """Normalize ruled cadastral building footprints without inferred attributes."""
    raw = fetch_bologna(dataset, bbox, slice_path=slice_path)
    required = {"codfab", "tipologia"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Bologna cadastral response misses required fields: {sorted(missing)}")
    out = gpd.GeoDataFrame(geometry=raw.geometry, crs=raw.crs)
    out["osm_id"] = raw["codfab"].astype("Int64").astype(str)
    if not out.osm_id.is_unique:
        raise ValueError("Bologna codfab values are not unique")
    out["building_tag"] = raw["tipologia"].fillna("").astype(str)
    out["function_tag"] = ""
    out["levels"] = pd.array([pd.NA] * len(out), dtype="Int64")
    out["height_m"] = pd.Series(float("nan"), index=raw.index, dtype="float64")
    out["year_built"] = pd.array([pd.NA] * len(out), dtype="Int64")
    out["postcode"] = None; out["underground"] = pd.array([0] * len(out), dtype="Int64"); out["roof_shape"] = ""; out["roof_height_m"] = float("nan")
    reserved = {"geometry", "codfab", "tipologia"}
    out["surplus_tags"] = [json.dumps({c: str(raw.iloc[i][c]) for c in raw.columns if c not in reserved and pd.notna(raw.iloc[i][c])}, ensure_ascii=False) for i in range(len(raw))]
    return finalize_footprints(out, source="BOLOGNA_RIFTER", output_dir=output_dir)


def ingest_bologna_ctc(
    *, bbox: tuple[float, float, float, float] | None = None,
    slice_path: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> gpd.GeoDataFrame:
    """Normalize CTC volumetric bodies for reconciliation only, never as final buildings."""
    raw = fetch_bologna(CTC_DATASET, bbox, slice_path=slice_path)
    required = {"codice_ogg", "descrizion"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Bologna CTC response misses required fields: {sorted(missing)}")
    out = gpd.GeoDataFrame(geometry=raw.geometry, crs=raw.crs)
    out["osm_id"] = raw["codice_ogg"].astype(str)
    if not out.osm_id.is_unique:
        raise ValueError("Bologna codice_ogg values are not unique")
    out["building_tag"] = raw["descrizion"].fillna("").astype(str)
    out["function_tag"] = ""
    out["levels"] = pd.array([pd.NA] * len(out), dtype="Int64")
    eaves_col = next((c for c in ("altezza_gronda", "altezza_gr") if c in raw), None)
    eaves = pd.to_numeric(raw[eaves_col], errors="coerce") if eaves_col else pd.Series(float("nan"), index=raw.index)
    top_col = next((c for c in ("quota_gronda", "quota_gron") if c in raw), None)
    base_col = next((c for c in ("quota_piede", "quota_pied") if c in raw), None)
    if top_col and base_col:
        eaves = eaves.fillna(pd.to_numeric(raw[top_col], errors="coerce") - pd.to_numeric(raw[base_col], errors="coerce"))
    out["height_m"] = eaves.astype(float)
    out["year_built"] = pd.array([pd.NA] * len(out), dtype="Int64")
    out["postcode"] = None; out["underground"] = pd.array([0] * len(out), dtype="Int64"); out["roof_shape"] = ""; out["roof_height_m"] = float("nan")
    reserved = {"geometry", "codice_ogg", "descrizion", "altezza_gronda", "altezza_gr", "quota_gronda", "quota_gron", "quota_piede", "quota_pied"}
    out["surplus_tags"] = [json.dumps({c: str(raw.iloc[i][c]) for c in raw.columns if c not in reserved and pd.notna(raw.iloc[i][c])}, ensure_ascii=False) for i in range(len(raw))]
    return finalize_footprints(out, source="BOLOGNA_CTC", output_dir=output_dir)
