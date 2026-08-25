"""Fail-closed observed-building to TABULA archetype mapping for EU-04.

This module intentionally distinguishes a construction-archetype mapping from a
dwelling-layout instruction.  Acquired footprints do not contain authoritative
per-building dwelling counts, so a mapped archetype must still not be sent to
the layout generator without that separate observed input.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from openubem.semantic.construction_sets import select_tabula_archetype


EU02_SITE_COUNTRY = {
    "ES-MAD-BERRUGUETE": "ES",
    "FR-LYO-HAUTCOEURPENTES": "FR",
    "GB-LDN-STDUNSTANS": "GB",
    "IT-BOL-GALVANI2": "IT",
}

# These are deliberately a smaller set than the acquisition residential
# crosswalk.  For example, OSM `house` cannot distinguish SFH from TH, so it
# must not be promoted to a TABULA type without supplementary evidence.
OBSERVED_TAG_TO_TABULA_TYPE = {
    "apartments": "AB",
    "detached": "SFH",
    "terrace": "TH",
}

# `D-EU-04-G` (Option G1): BD TOPO carries no TABULA-compatible building-type
# tag for France, so a French row whose tag maps to nothing is instead typed
# from two independent source signals (dwelling count and storey count, which
# must agree) plus computed footprint adjacency for the SFH/TH split.  Every
# threshold below is read off `tabula_archetypes_fr.json`, never invented.
TYPOLOGY_SIGNALS_DISAGREE = "TYPOLOGY_SIGNALS_DISAGREE"
TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14 = "TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14"
MISSING_OBSERVED_DWELLING_COUNT = "MISSING_OBSERVED_DWELLING_COUNT"
MISSING_OBSERVED_STOREY_COUNT = "MISSING_OBSERVED_STOREY_COUNT"


@dataclass(frozen=True)
class EuropeanArchetypeMappingDecision:
    neighbourhood_id: str
    building_id: str
    country_stock_code: str
    building_type: str | None
    year_built: int | None
    archetype_id: str | None
    mapping_status: str
    reason: str
    layout_ready: bool
    type_provenance: str


def _registry_records(country_stock_code: str) -> list[dict[str, Any]]:
    path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "construction"
        / f"tabula_archetypes_{country_stock_code.lower()}.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["records"]


def _observed_year(row: pd.Series) -> int | None:
    value = row.get("year_built")
    provenance = str(row.get("provenance_year_built", ""))
    if pd.isna(value) or not provenance.endswith("_OBSERVED"):
        return None
    numeric = float(value)
    if not numeric.is_integer() or numeric <= 0:
        return None
    return int(numeric)


def _observed_dwellings(row: pd.Series) -> int | None:
    """Read the BD TOPO dwelling count carried in ``surplus_tags`` (a JSON string)."""
    raw = row.get("surplus_tags")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        return None
    value = payload.get("nombre_de_logements")
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric.is_integer() or numeric <= 0:
        return None
    return int(numeric)


def _observed_storeys(row: pd.Series) -> int | None:
    """Read the BD TOPO storey count off ``levels``.

    BD TOPO encodes an unknown ``nombre_d_etages`` as ``0`` (a non-nullable
    integer column carries no separate null marker), so ``<= 0`` is treated
    as missing along with an actual null.
    """
    value = row.get("levels")
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric <= 0:
        return None
    return int(numeric)


def compute_footprint_adjacency(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Boolean Series, aligned to ``gdf.index``: True where a footprint shares a
    boundary with another footprint in ``gdf``.

    Reprojects to EPSG:2154 (Lambert-93) before any predicate.  A shared
    boundary is a ``touches`` relationship, or an intersection whose geometry
    is not a point/multipoint — a zero-metre buffer tolerance, no positive
    buffer.  Self-matches are excluded by ``osm_id``.
    """
    projected = gdf.to_crs(epsg=2154).reset_index(drop=True)
    sindex = projected.sindex
    osm_ids = projected["osm_id"]
    attached = []
    for position, geometry in enumerate(projected.geometry):
        own_id = osm_ids.iloc[position]
        is_attached = False
        for candidate in sindex.query(geometry, predicate="intersects"):
            if candidate == position or osm_ids.iloc[candidate] == own_id:
                continue
            intersection = geometry.intersection(projected.geometry.iloc[candidate])
            if intersection.is_empty or intersection.geom_type in (
                "Point",
                "MultiPoint",
            ):
                continue
            is_attached = True
            break
        attached.append(is_attached)
    return pd.Series(attached, index=gdf.index, name="is_attached")


def derive_bdtopo_building_type(
    dwellings: int | None, storeys: int | None, is_attached: bool | None
) -> tuple[str | None, str | None]:
    """Apply the ruled `D-EU-04-G` (Option G1) two-signal derivation, fail-closed."""
    if dwellings is None:
        return None, MISSING_OBSERVED_DWELLING_COUNT
    if storeys is None:
        return None, MISSING_OBSERVED_STOREY_COUNT
    if dwellings in (13, 14):
        return None, TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14
    if dwellings == 1 and storeys <= 4:
        return ("TH" if is_attached else "SFH"), None
    if 2 <= dwellings <= 12 and storeys <= 4:
        return "MFH", None
    if dwellings >= 15 and storeys >= 5:
        return "AB", None
    return None, TYPOLOGY_SIGNALS_DISAGREE


def map_observed_building_to_tabula(
    row: pd.Series,
    *,
    neighbourhood_id: str,
    country_stock_code: str,
    records: list[dict[str, Any]] | None = None,
) -> EuropeanArchetypeMappingDecision:
    """Map only fully evidenced source attributes; otherwise retain an exclusion."""
    country = country_stock_code.upper()
    if country not in {"ES", "GB", "IT", "FR"}:
        raise ValueError(f"Unsupported country_stock_code: {country_stock_code}")
    building_id = str(row.get("osm_id", "")).strip()
    if not building_id:
        raise ValueError("Observed building mapping requires osm_id")
    tag = str(row.get("building_tag", "")).strip().casefold()
    building_type = OBSERVED_TAG_TO_TABULA_TYPE.get(tag)
    type_provenance = "OBSERVED_TAG"
    derived_dwellings: int | None = None
    derived_exclusion: str | None = None
    if building_type is None and country == "FR":
        derived_dwellings = _observed_dwellings(row)
        storeys = _observed_storeys(row)
        is_attached_raw = row.get("is_attached")
        is_attached = None if is_attached_raw is None else bool(is_attached_raw)
        derived_type, derived_exclusion = derive_bdtopo_building_type(
            derived_dwellings, storeys, is_attached
        )
        if derived_type is not None:
            building_type = derived_type
            type_provenance = "DERIVED_BDTOPO_TWO_SIGNAL"
    year_built = _observed_year(row)
    missing: list[str] = []
    if year_built is None:
        missing.append("MISSING_OBSERVED_YEAR_BUILT")
    if building_type is None:
        missing.append(derived_exclusion or "UNMAPPABLE_RESIDENTIAL_TYPE")
    if missing:
        return EuropeanArchetypeMappingDecision(
            neighbourhood_id=neighbourhood_id,
            building_id=building_id,
            country_stock_code=country,
            building_type=building_type,
            year_built=year_built,
            archetype_id=None,
            mapping_status="EXCLUDED_MISSING_OR_AMBIGUOUS_INPUT",
            reason=";".join(missing),
            layout_ready=False,
            type_provenance=type_provenance,
        )
    try:
        archetype = select_tabula_archetype(
            records or _registry_records(country),
            country,
            building_type,
            year_built,
        )
    except ValueError as error:
        return EuropeanArchetypeMappingDecision(
            neighbourhood_id=neighbourhood_id,
            building_id=building_id,
            country_stock_code=country,
            building_type=building_type,
            year_built=year_built,
            archetype_id=None,
            mapping_status="EXCLUDED_ARCHETYPE_RESOLUTION",
            reason=str(error).split(":", 1)[0],
            layout_ready=False,
            type_provenance=type_provenance,
        )
    if type_provenance == "DERIVED_BDTOPO_TWO_SIGNAL" and derived_dwellings is not None:
        return EuropeanArchetypeMappingDecision(
            neighbourhood_id=neighbourhood_id,
            building_id=building_id,
            country_stock_code=country,
            building_type=building_type,
            year_built=year_built,
            archetype_id=archetype["archetype_id"],
            mapping_status="MAPPED_LAYOUT_READY",
            reason="",
            layout_ready=True,
            type_provenance=type_provenance,
        )
    return EuropeanArchetypeMappingDecision(
        neighbourhood_id=neighbourhood_id,
        building_id=building_id,
        country_stock_code=country,
        building_type=building_type,
        year_built=year_built,
        archetype_id=archetype["archetype_id"],
        mapping_status="MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT",
        reason="MISSING_OBSERVED_DWELLING_COUNT",
        layout_ready=False,
        type_provenance=type_provenance,
    )


def write_eu02_archetype_mapping_readiness(
    manifests_root: Path | str,
    output_dir: Path | str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Write a reproducible mapping/exclusion record for the four EU-02 sites."""
    root = Path(manifests_root)
    decisions: list[EuropeanArchetypeMappingDecision] = []
    for site_id, country in EU02_SITE_COUNTRY.items():
        manifest = root / site_id / "02_residential_manifest.gpkg"
        if not manifest.is_file():
            raise ValueError(f"Missing audited residential manifest: {manifest}")
        gdf = gpd.read_file(manifest)
        if country == "FR":
            gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))
        for _, row in gdf.sort_values("osm_id", kind="stable").iterrows():
            decisions.append(
                map_observed_building_to_tabula(
                    row,
                    neighbourhood_id=site_id,
                    country_stock_code=country,
                )
            )
    frame = pd.DataFrame(asdict(decision) for decision in decisions)
    if frame["building_id"].duplicated().any():
        raise ValueError("Stable building IDs must remain unique across EU-02 manifests")
    summary = {
        "evidence_scope": "observed_input_archetype_mapping_readiness_only",
        "layout_ready_count": int(frame["layout_ready"].sum()),
        "mapping_status_counts": {
            key: int(value)
            for key, value in frame["mapping_status"].value_counts(sort=True).items()
        },
        "reason_counts": {
            key: int(value)
            for key, value in frame["reason"].value_counts(sort=True).items()
        },
        "site_counts": {
            site: int((frame["neighbourhood_id"] == site).sum())
            for site in EU02_SITE_COUNTRY
        },
        "type_provenance_counts": {
            key: int(value)
            for key, value in frame["type_provenance"].value_counts(sort=True).items()
        },
        "derived_type_counts": {
            site: {
                key: int(value)
                for key, value in frame.loc[
                    (frame["neighbourhood_id"] == site)
                    & (frame["type_provenance"] == "DERIVED_BDTOPO_TWO_SIGNAL")
                    & (frame["layout_ready"]),
                    "building_type",
                ]
                .value_counts(sort=True)
                .items()
            }
            for site in EU02_SITE_COUNTRY
        },
        "total_buildings": int(len(frame)),
    }
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination / "observed_archetype_mapping_readiness.csv", index=False)
    (destination / "observed_archetype_mapping_readiness_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return frame, summary
