"""Google Maps Places API (New) client, taxonomy mapper, and building enricher."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from openubem.acquisition.gmaps_client import (
    GmapsHttpClient,
    assert_no_eui_columns,
)
from openubem.semantic import provenance

_PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
_DEFAULT_FIELD_MASK = (
    "places.id,places.displayName,places.location,"
    "places.primaryType,places.types,places.businessStatus"
)

PLACE_TYPE_TO_UBEM: dict[str, tuple[str, str]] = {
    "restaurant": ("commercial", "restaurant"),
    "cafe": ("commercial", "cafe"),
    "bakery": ("commercial", "bakery"),
    "bar": ("commercial", "bar"),
    "fast_food_restaurant": ("commercial", "restaurant"),
    "supermarket": ("commercial", "supermarket"),
    "grocery_store": ("commercial", "supermarket"),
    "shopping_mall": ("commercial", "retail"),
    "department_store": ("commercial", "retail"),
    "store": ("commercial", "retail"),
    "clothing_store": ("commercial", "retail"),
    "electronics_store": ("commercial", "retail"),
    "convenience_store": ("commercial", "retail"),
    "pharmacy": ("commercial", "retail"),
    "bank": ("commercial", "office"),
    "corporate_office": ("commercial", "office"),
    "office": ("commercial", "office"),
    "lodging": ("commercial", "hotel"),
    "hotel": ("commercial", "hotel"),
    "motel": ("commercial", "hotel"),
    "gym": ("commercial", "commercial"),
    "hospital": ("institutional", "hospital"),
    "medical_clinic": ("institutional", "clinic"),
    "clinic": ("institutional", "clinic"),
    "doctor": ("institutional", "clinic"),
    "school": ("institutional", "school"),
    "primary_school": ("institutional", "school"),
    "secondary_school": ("institutional", "school"),
    "university": ("institutional", "university"),
    "library": ("institutional", "public"),
    "government_office": ("institutional", "government"),
    "city_hall": ("institutional", "government"),
    "courthouse": ("institutional", "government"),
    "police": ("institutional", "government"),
    "fire_station": ("institutional", "government"),
    "place_of_worship": ("institutional", "religious"),
    "museum": ("institutional", "public"),
    "warehouse": ("industrial", "warehouse"),
    "storage": ("industrial", "warehouse"),
    "factory": ("industrial", "industrial"),
    "industrial": ("industrial", "industrial"),
    "apartment_building": ("residential", "apartments"),
    "apartment_complex": ("residential", "apartments"),
    "condominium_complex": ("residential", "apartments"),
    "housing_complex": ("residential", "residential"),
    "residential": ("residential", "residential"),
}

USE_CLASS_ENERGY_PRIORITY: dict[str, int] = {
    "commercial": 5,
    "institutional": 4,
    "industrial": 3,
    "mixed": 2,
    "residential": 1,
    "unknown": 0,
}


def map_place_types_to_ubem(
    primary_type: str | None,
    types: Sequence[str] | None = None,
) -> tuple[str, str | None]:
    """Maps Google Places API (New) types to OpenUBEM ``(use_class, function_tag)``.

    Args:
        primary_type: Google Places ``primaryType`` identifier.
        types: Optional fallback sequence of secondary Google Places types.

    Returns:
        Tuple ``(use_class, function_tag)`` matching OpenUBEM's 6 canonical
        use classes, defaulting to ``("unknown", None)`` when unmapped.
    """
    if primary_type:
        norm_primary = str(primary_type).strip().lower()
        if norm_primary in PLACE_TYPE_TO_UBEM:
            return PLACE_TYPE_TO_UBEM[norm_primary]

    if types:
        for item in types:
            norm_type = str(item).strip().lower()
            if norm_type in PLACE_TYPE_TO_UBEM:
                return PLACE_TYPE_TO_UBEM[norm_type]

    return "unknown", None


def energy_priority_score(use_class: str | None, primary_type: str | None) -> int:
    """Computes deterministic energy-intensity tie-breaking priority for a POI.

    Higher-process-load commercial and hospital facilities take precedence over
    lower-intensity uses when multiple POIs co-occur inside one footprint.

    Args:
        use_class: Mapped OpenUBEM use class.
        primary_type: Google Places ``primaryType`` string.

    Returns:
        Integer priority rank (higher means higher modeled energy intensity).
    """
    base = USE_CLASS_ENERGY_PRIORITY.get((use_class or "").strip().lower(), 0) * 10
    p_type = (primary_type or "").strip().lower()
    if p_type in {"restaurant", "fast_food_restaurant", "supermarket", "bakery"}:
        return base + 3
    if p_type in {"hospital", "medical_clinic", "hotel"}:
        return base + 2
    if p_type in {"office", "school", "university", "retail", "store"}:
        return base + 1
    return base


def parse_places_response(payload: dict[str, Any]) -> gpd.GeoDataFrame:
    """Parses a Google Places API (New) JSON response into a WGS 84 GeoDataFrame.

    POIs flagged ``businessStatus == "CLOSED_PERMANENTLY"`` or lacking valid
    coordinates are excluded.

    Args:
        payload: Decoded JSON response containing a ``"places"`` list.

    Returns:
        ``gpd.GeoDataFrame`` in ``EPSG:4326`` with mapped ``use_class`` and
        ``function_tag`` columns.
    """
    columns = [
        "place_id",
        "name",
        "primary_type",
        "gmaps_types",
        "business_status",
        "use_class",
        "function_tag",
        "energy_priority",
        "geometry",
    ]
    rows: list[dict[str, Any]] = []
    for entry in payload.get("places") or []:
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("businessStatus") or "OPERATIONAL")
        if status == "CLOSED_PERMANENTLY":
            continue
        loc = entry.get("location") or {}
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        if lat is None or lon is None:
            continue

        display = entry.get("displayName")
        name = (
            display.get("text")
            if isinstance(display, dict)
            else (str(display) if display is not None else None)
        )
        primary_type = entry.get("primaryType")
        raw_types = entry.get("types") or []
        types_list = [str(item) for item in raw_types if item]
        use_class, function_tag = map_place_types_to_ubem(primary_type, types_list)
        rows.append(
            {
                "place_id": entry.get("id"),
                "name": name,
                "primary_type": primary_type,
                "gmaps_types": ",".join(types_list),
                "business_status": status,
                "use_class": use_class,
                "function_tag": function_tag,
                "energy_priority": energy_priority_score(use_class, primary_type),
                "geometry": Point(float(lon), float(lat)),
            }
        )

    if not rows:
        return gpd.GeoDataFrame(
            {col: pd.Series(dtype="object") for col in columns[:-1]},
            geometry=gpd.GeoSeries([], crs="EPSG:4326"),
            crs="EPSG:4326",
        )
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def _normalize_loaded_places_gdf(places_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ensures a locally loaded Places slice carries normalized UBEM columns.

    Args:
        places_gdf: Input Places GeoDataFrame loaded from disk.

    Returns:
        Normalized Places GeoDataFrame with ``use_class``, ``function_tag``,
        and ``energy_priority`` columns populated cleanly.
    """
    out = places_gdf.copy()
    if "business_status" in out.columns:
        out = out[out["business_status"] != "CLOSED_PERMANENTLY"].copy()
    if "primary_type" not in out.columns:
        out["primary_type"] = out.get("primaryType", pd.Series(None, index=out.index))
    if "gmaps_types" not in out.columns:
        out["gmaps_types"] = ""

    use_classes: list[str] = []
    func_tags: list[str | None] = []
    priorities: list[int] = []
    has_existing_uc = "use_class" in out.columns
    has_existing_ft = "function_tag" in out.columns

    for idx in out.index:
        p_type = out.loc[idx, "primary_type"]
        raw_types_val = out.loc[idx, "gmaps_types"]
        split_types = (
            [tok.strip() for tok in str(raw_types_val).split(",") if tok.strip()]
            if pd.notna(raw_types_val)
            else []
        )
        mapped_uc, mapped_ft = map_place_types_to_ubem(
            None if pd.isna(p_type) else str(p_type),
            split_types,
        )
        existing_uc = (
            str(out.loc[idx, "use_class"]).strip().lower()
            if has_existing_uc and pd.notna(out.loc[idx, "use_class"])
            else ""
        )
        existing_ft = (
            str(out.loc[idx, "function_tag"]).strip()
            if has_existing_ft and pd.notna(out.loc[idx, "function_tag"])
            else ""
        )
        uc = existing_uc if existing_uc and existing_uc != "unknown" else mapped_uc
        ft = existing_ft if existing_ft else mapped_ft
        use_classes.append(uc)
        func_tags.append(ft)
        priorities.append(
            energy_priority_score(
                uc,
                None if pd.isna(p_type) else str(p_type),
            )
        )

    out["use_class"] = use_classes
    out["function_tag"] = func_tags
    out["energy_priority"] = priorities
    if out.crs is None:
        out = out.set_crs(epsg=4326)
    return out


def fetch_places_nearby(
    lat: float | None = None,
    lon: float | None = None,
    *,
    radius_m: float = 500.0,
    included_types: Sequence[str] | None = None,
    max_results: int = 20,
    slice_path: Path | None = None,
    client: GmapsHttpClient | None = None,
    field_mask: str = _DEFAULT_FIELD_MASK,
) -> gpd.GeoDataFrame:
    """Loads Google Places POIs from a local spatial slice or live Places API (New).

    Args:
        lat: Search center WGS 84 latitude (required for live API queries).
        lon: Search center WGS 84 longitude (required for live API queries).
        radius_m: Circular search radius in meters (max 50000).
        included_types: Optional list of Google Places type filters.
        max_results: Maximum POIs requested per call (1..20 for searchNearby).
        slice_path: Optional local offline slice (``.parquet``, ``.geojson``,
            ``.gpkg``, or raw ``.json`` Places API payload).
        client: Optional cached :class:`GmapsHttpClient` instance.
        field_mask: ``X-Goog-FieldMask`` header controlling billed fields.

    Returns:
        Normalized Places GeoDataFrame with ``use_class`` and ``function_tag``.

    Raises:
        ValueError: If neither ``slice_path`` nor ``(lat, lon)`` is supplied, or
            if ``slice_path`` uses an unsupported extension.
    """
    if slice_path is not None:
        path = Path(slice_path)
        suffix = path.suffix.lower()
        if suffix == ".parquet":
            loaded = gpd.read_parquet(path)
        elif suffix in {".geojson", ".gpkg"}:
            loaded = gpd.read_file(path)
        elif suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            loaded = parse_places_response(payload)
        else:
            raise ValueError(f"Unsupported Places slice extension: {suffix!r}")
        assert_no_eui_columns(loaded.columns)
        return _normalize_loaded_places_gdf(loaded)

    if lat is None or lon is None:
        raise ValueError(
            "fetch_places_nearby requires (lat, lon) when slice_path is None."
        )

    body: dict[str, Any] = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lon)},
                "radius": float(radius_m),
            }
        },
        "maxResultCount": int(max_results),
    }
    if included_types:
        body["includedTypes"] = list(included_types)

    http = client or GmapsHttpClient()
    payload = http.post_json(
        _PLACES_NEARBY_URL,
        json_body=body,
        headers={"X-Goog-FieldMask": field_mask},
        auth_mode="header",
    )
    return parse_places_response(payload)


def _is_missing_semantic(val: Any, *, allow_yes: bool = False) -> bool:
    """Checks whether a semantic label is absent or an uninformative placeholder.

    Args:
        val: Raw cell value from ``use_class`` or ``function_tag``.
        allow_yes: Treat literal ``"yes"`` as missing when checking tags.

    Returns:
        ``True`` if the field may be filled safely by fused POI evidence.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)) or pd.isna(val):
        return True
    cleaned = str(val).strip().lower()
    placeholders = {"", "nan", "none", "unknown"}
    if allow_yes:
        placeholders.add("yes")
    return cleaned in placeholders


def match_places_to_buildings(
    buildings_gdf: gpd.GeoDataFrame,
    places_gdf: gpd.GeoDataFrame,
    *,
    tolerance_m: float = 10.0,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """Spatially joins Places POIs to building footprints with containment priority.

    Exact polygon-containment matches yield ``is_derived=False`` (``HIGH``
    provenance), while nearest-footprint matches within ``tolerance_m`` yield
    ``is_derived=True`` (``MED`` provenance). Co-occurring POIs inside one
    footprint are resolved via deterministic energy-intensity priority.

    Args:
        buildings_gdf: Target building footprints GeoDataFrame.
        places_gdf: Normalized Places POIs GeoDataFrame.
        tolerance_m: Maximum nearest-footprint fallback distance in meters.

    Returns:
        Tuple of Series indexed like ``buildings_gdf``:
        ``(use_class, function_tag, primary_type, poi_count, is_derived)``.
    """
    n_idx = buildings_gdf.index
    out_uc = pd.Series(pd.NA, index=n_idx, dtype="object")
    out_ft = pd.Series(pd.NA, index=n_idx, dtype="object")
    out_pt = pd.Series(pd.NA, index=n_idx, dtype="object")
    out_cnt = pd.Series(0, index=n_idx, dtype="int64")
    out_derived = pd.Series(False, index=n_idx, dtype="bool")

    if buildings_gdf.empty or places_gdf.empty:
        return out_uc, out_ft, out_pt, out_cnt, out_derived

    assert_no_eui_columns(places_gdf.columns)
    places = _normalize_loaded_places_gdf(places_gdf)
    places = places[places["use_class"].astype(str) != "unknown"].copy()
    if places.empty:
        return out_uc, out_ft, out_pt, out_cnt, out_derived

    work_b = gpd.GeoDataFrame(
        {"_b_idx": buildings_gdf.index},
        geometry=buildings_gdf.geometry,
        crs=buildings_gdf.crs,
    )
    work_p = places.copy()
    if work_b.crs is not None and work_b.crs.is_geographic:
        metric_crs = work_b.estimate_utm_crs()
        work_b = work_b.to_crs(metric_crs)
        work_p = work_p.to_crs(metric_crs)
    elif work_b.crs is not None and work_p.crs != work_b.crs:
        work_p = work_p.to_crs(work_b.crs)

    contained = gpd.sjoin(
        work_b,
        work_p,
        how="inner",
        predicate="intersects",
    )
    if not contained.empty:
        sorted_hits = contained.sort_values(
            by=["_b_idx", "energy_priority"],
            ascending=[True, False],
        )
        counts = sorted_hits.groupby("_b_idx").size()
        top_hits = sorted_hits.groupby("_b_idx", as_index=True).first()
        for b_idx, row in top_hits.iterrows():
            out_uc.loc[b_idx] = row["use_class"]
            out_ft.loc[b_idx] = row["function_tag"]
            out_pt.loc[b_idx] = row["primary_type"]
            out_cnt.loc[b_idx] = int(counts.loc[b_idx])
            out_derived.loc[b_idx] = False

    unmatched_mask = out_uc.isna()
    if unmatched_mask.any():
        rem_b = work_b.loc[work_b["_b_idx"].isin(n_idx[unmatched_mask])].copy()
        nearest = gpd.sjoin_nearest(
            rem_b,
            work_p,
            how="inner",
            max_distance=float(tolerance_m),
            distance_col="_dist_m",
        )
        if not nearest.empty:
            nearest_sorted = nearest.sort_values(
                by=["_b_idx", "_dist_m", "energy_priority"],
                ascending=[True, True, False],
            )
            top_near = nearest_sorted.groupby("_b_idx", as_index=True).first()
            for b_idx, row in top_near.iterrows():
                out_uc.loc[b_idx] = row["use_class"]
                out_ft.loc[b_idx] = row["function_tag"]
                out_pt.loc[b_idx] = row["primary_type"]
                out_cnt.loc[b_idx] = 1
                out_derived.loc[b_idx] = True

    return out_uc, out_ft, out_pt, out_cnt, out_derived


def enrich_buildings_with_gmaps_places(
    buildings_gdf: gpd.GeoDataFrame,
    places_gdf: gpd.GeoDataFrame,
    *,
    tolerance_m: float = 10.0,
) -> gpd.GeoDataFrame:
    """Enriches missing/unknown building use classes using Google Places POIs.

    Existing observed ``use_class`` and ``function_tag`` attributes are strictly
    preserved. Newly populated attributes receive ``FUSED_GMAPSPLACES_HIGH``
    (polygon containment) or ``FUSED_GMAPSPLACES_MED`` (centroid fallback).

    Args:
        buildings_gdf: Target building footprints GeoDataFrame.
        places_gdf: Normalized Places POIs GeoDataFrame.
        tolerance_m: Maximum nearest-centroid fallback distance in meters.

    Returns:
        Copy of ``buildings_gdf`` with enriched ``use_class``, ``function_tag``,
        informational ``gmaps_places_*`` fields, and updated provenance.
    """
    assert_no_eui_columns(buildings_gdf.columns)
    assert_no_eui_columns(places_gdf.columns)
    out = buildings_gdf.copy()
    if out.empty:
        return out

    matched_uc, matched_ft, matched_pt, matched_cnt, matched_derived = (
        match_places_to_buildings(out, places_gdf, tolerance_m=tolerance_m)
    )

    out["gmaps_places_primary_type"] = matched_pt
    out["gmaps_places_count"] = matched_cnt

    if "use_class" not in out.columns:
        out["use_class"] = pd.Series("unknown", index=out.index, dtype="object")
    if "function_tag" not in out.columns:
        out["function_tag"] = pd.Series(pd.NA, index=out.index, dtype="object")

    uc_fill_mask = out["use_class"].apply(_is_missing_semantic) & matched_uc.notna()
    ft_fill_mask = (
        out["function_tag"].apply(lambda val: _is_missing_semantic(val, allow_yes=True))
        & matched_ft.notna()
    )

    if uc_fill_mask.any():
        out.loc[uc_fill_mask, "use_class"] = matched_uc.loc[uc_fill_mask]
        high_uc = uc_fill_mask & (~matched_derived)
        med_uc = uc_fill_mask & matched_derived
        if high_uc.any():
            out = provenance.set_provenance(
                out,
                "use_class",
                "FUSED_GMAPSPLACES_HIGH",
                mask=high_uc,
                confidence="HIGH",
            )
            out = provenance.append_flag(
                out,
                "FUSED_GMAPSPLACES_HIGH",
                mask=high_uc,
            )
        if med_uc.any():
            out = provenance.set_provenance(
                out,
                "use_class",
                "FUSED_GMAPSPLACES_MED",
                mask=med_uc,
                confidence="MED",
            )
            out = provenance.append_flag(
                out,
                "FUSED_GMAPSPLACES_MED",
                mask=med_uc,
            )

    if ft_fill_mask.any():
        out.loc[ft_fill_mask, "function_tag"] = matched_ft.loc[ft_fill_mask]
        high_ft = ft_fill_mask & (~matched_derived)
        med_ft = ft_fill_mask & matched_derived
        if high_ft.any():
            out = provenance.set_provenance(
                out,
                "function_tag",
                "FUSED_GMAPSPLACES_HIGH",
                mask=high_ft,
                confidence="HIGH",
            )
            out = provenance.append_flag(
                out,
                "FUSED_GMAPSPLACES_HIGH",
                mask=high_ft,
            )
        if med_ft.any():
            out = provenance.set_provenance(
                out,
                "function_tag",
                "FUSED_GMAPSPLACES_MED",
                mask=med_ft,
                confidence="MED",
            )
            out = provenance.append_flag(
                out,
                "FUSED_GMAPSPLACES_MED",
                mask=med_ft,
            )

    assert_no_eui_columns(out.columns)
    return out
