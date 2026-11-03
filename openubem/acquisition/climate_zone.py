"""Step 2.1 §3A/§3B — input gate, representative-point extraction, and
per-building ASHRAE climate-zone + state spatial join.
"""
from __future__ import annotations

import json
import logging
from importlib.resources import files
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.acquisition.osm_fetcher import _SCHEMA_COLUMNS
from openubem.semantic.building_classifier import _OUTPUT_SCHEMA_COLUMNS  # 26-col list

logger = logging.getLogger("openubem.acquisition.climate_zone")

# F3 closed vocabulary (DESIGN line 64)
_CLIMATE_ZONE_VOCAB: frozenset[str] = frozenset(
    {"1A", "2A", "2B", "3A", "3B", "3C", "4A", "4B", "4C", "5A", "5B", "5C", "6A", "6B", "7", "8"}
)

# 26-column input schema (DESIGN line 24; mirrors building_classifier._OUTPUT_SCHEMA_COLUMNS)
_INPUT_26: list[str] = list(_OUTPUT_SCHEMA_COLUMNS)

_RAW_ARCHETYPES: dict = json.loads(
    files("openubem.data").joinpath("openstudio_archetypes.json").read_text(encoding="utf-8")
)
_VALID_ARCHETYPE_IDS: frozenset[str] = frozenset(
    a["archetype_id"] for a in _RAW_ARCHETYPES["archetypes"]
)


def _validate_input_schema(gdf: gpd.GeoDataFrame) -> None:
    """Raise ValueError naming the first offending column on gate failure.

    Checks (DESIGN §3A, PLAN §5 F1, P7):
      1. Exactly 26 expected column names present.
      2. archetype_id values within the closed 30-element vocabulary.
    """
    cols = list(gdf.columns)
    missing = [c for c in _INPUT_26 if c not in cols]
    if missing:
        raise ValueError(f"Input schema gate: missing columns {missing}")
    extra = [c for c in cols if c not in _INPUT_26]
    if extra:
        raise ValueError(f"Input schema gate: unexpected extra columns {extra}")
    if len(cols) != 26:
        raise ValueError(f"Input schema gate: expected 26 columns, got {len(cols)}")

    if "archetype_id" in gdf.columns and len(gdf) > 0:
        bad = gdf.loc[~gdf["archetype_id"].isin(_VALID_ARCHETYPE_IDS), "archetype_id"]
        if not bad.empty:
            raise ValueError(
                f"Input schema gate: archetype_id {bad.iloc[0]!r} not in 30-element vocab"
            )


def _join_points(gdf: gpd.GeoDataFrame) -> gpd.GeoSeries:
    """Return representative points in EPSG:4326 (DESIGN lines 42-47, F4)."""
    pts_utm = gdf.geometry.representative_point()
    return pts_utm.to_crs(epsg=4326)


def _load_counties(path: Path | None = None) -> gpd.GeoDataFrame:
    """Load bundled county GPKG (or a provided path for testing)."""
    if path is not None:
        return gpd.read_file(str(path), layer="counties")
    data = files("openubem.data.climate_zones").joinpath("ashrae_climate_zones.gpkg")
    return gpd.read_file(str(data), layer="counties")


def assign_climate_zones(
    gdf: gpd.GeoDataFrame,
    counties: gpd.GeoDataFrame | None = None,
) -> pd.DataFrame:
    """Per-building two-tier spatial join returning climate_zone, state, county_geoid,
    climate_zone_method, provenance_climate_zone (DESIGN §3B, F5/F6/F7).

    Parameters
    ----------
    gdf:
        26-column validated input GeoDataFrame (UTM CRS).
    counties:
        Optional county layer (EPSG:4326); loads bundled GPKG when None.

    Returns
    -------
    pd.DataFrame indexed like gdf with columns:
        climate_zone, state, county_geoid, climate_zone_method, provenance_climate_zone
    """
    if counties is None:
        counties = _load_counties()

    pts_4326 = _join_points(gdf)
    pts_gdf = gpd.GeoDataFrame({"osm_id": gdf["osm_id"].values}, geometry=pts_4326, crs="EPSG:4326")

    # Tier 1: point-in-polygon (F5)
    tier1 = gpd.sjoin(pts_gdf, counties[["county_geoid", "state_abbrev", "climate_zone", "geometry"]],
                      how="left", predicate="within")

    # Deduplicate multi-match: keep lexically smallest county_geoid (F6)
    dupes = tier1.index.duplicated(keep=False)
    if dupes.any():
        n_dupes = int(dupes.sum())
        logger.warning(json.dumps({"event": "multi_match_county", "n_rows_affected": n_dupes}))
        tier1 = (
            tier1.sort_values("county_geoid")
            .groupby(level=0, sort=False)
            .first()
        )

    matched = tier1.dropna(subset=["climate_zone"])
    unmatched_idx = tier1[tier1["climate_zone"].isna()].index

    # DESIGN line 62 / F5: zero Tier-1 matches across the ENTIRE run ⇒ abort before Tier 2.
    # A mixed run (some Tier-1, some Tier-2) is legal; all-Tier-1-miss indicates wrong
    # continent / Phase-3 territory, not a per-building gap.
    if len(matched) == 0:
        raise RuntimeError(
            json.dumps({
                "event": "zero_tier1_matches",
                "n_buildings": len(gdf),
                "message": (
                    "Zero Tier-1 (within) matches across the entire run — input appears to be "
                    "outside US county coverage (wrong continent / Phase-3 territory)."
                ),
            })
        )

    result = tier1[["county_geoid", "state_abbrev", "climate_zone"]].copy()
    result["climate_zone_method"] = "county_within"
    result["provenance_climate_zone"] = "ASHRAE_STANDARD"

    # Tier 2: nearest fallback for unmatched points (F5, P9)
    if len(unmatched_idx) > 0:
        unmatched_pts = pts_gdf.loc[unmatched_idx].copy()
        # Reproject to run UTM CRS for max_distance in metres
        utm_crs = gdf.crs
        unmatched_pts_utm = unmatched_pts.to_crs(utm_crs)
        counties_utm = counties.to_crs(utm_crs)
        tier2 = gpd.sjoin_nearest(
            unmatched_pts_utm,
            counties_utm[["county_geoid", "state_abbrev", "climate_zone", "geometry"]],
            how="left",
            max_distance=5_000,
        )
        for idx in unmatched_idx:
            if idx in tier2.index:
                row2 = tier2.loc[idx]
                # loc returns a DataFrame when multiple rows share the index, Series for one row
                if isinstance(row2, pd.DataFrame):
                    row2 = row2.iloc[0]
                if pd.notna(row2.get("climate_zone", None)):
                    result.at[idx, "county_geoid"] = row2["county_geoid"]
                    result.at[idx, "state_abbrev"] = row2["state_abbrev"]
                    result.at[idx, "climate_zone"] = row2["climate_zone"]
                    result.at[idx, "climate_zone_method"] = "nearest_fallback"
                    result.at[idx, "provenance_climate_zone"] = "HEURISTIC"

    # Check for still-unmatched after both tiers (F5 abort condition)
    still_unmatched = result[result["climate_zone"].isna()]
    if len(still_unmatched) > 0:
        raise RuntimeError(
            json.dumps({
                "event": "unmatched_buildings",
                "n_unmatched": len(still_unmatched),
                "message": "Buildings outside US county coverage; check input CRS/coordinates.",
            })
        )

    # Validate output zones (PLAN §5 F3)
    bad_zones = set(result["climate_zone"].dropna().unique()) - _CLIMATE_ZONE_VOCAB
    if bad_zones:
        raise RuntimeError(
            json.dumps({"event": "invalid_zone_tokens", "bad": sorted(bad_zones)})
        )

    # Multi-zone neighbourhood warning (F6)
    distinct_zones = result["climate_zone"].dropna().unique()
    if len(distinct_zones) > 1:
        counts = result["climate_zone"].value_counts().to_dict()
        logger.warning(
            json.dumps({
                "event": "multi_zone_neighbourhood",
                "zones": sorted(distinct_zones),
                "counts": {k: int(v) for k, v in counts.items()},
            })
        )

    result = result.rename(columns={"state_abbrev": "state"})
    return result[["climate_zone", "state", "county_geoid", "climate_zone_method", "provenance_climate_zone"]]
