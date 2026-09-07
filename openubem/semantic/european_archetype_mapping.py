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
    dwellings_provenance: str


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
    """Read an observed dwelling count for this building.

    Two sources, in order.  ``observed_dwellings`` is the explicit column an
    attribute sidecar supplies (Madrid Catastro `numberOfDwellings`, joined by
    `openubem/acquisition/catastro_inspire_fetcher.py`); when it is absent the
    BD TOPO count carried inside ``surplus_tags`` (a JSON string) is read, which
    is where France's `nombre_de_logements` lives.  Neither is defaulted: a
    count that is missing, non-integer or ``<= 0`` returns ``None`` so the
    caller records `MISSING_OBSERVED_DWELLING_COUNT`.
    """
    explicit = row.get("observed_dwellings")
    if explicit is not None and not (isinstance(explicit, float) and pd.isna(explicit)):
        try:
            numeric = float(explicit)
        except (TypeError, ValueError):
            numeric = None
        if numeric is not None and numeric.is_integer() and numeric > 0:
            return int(numeric)
        return None
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


def _dwellings_provenance(row: pd.Series, dwellings: int | None) -> str:
    """Name the source that supplied the dwelling count, or say it is missing."""
    if dwellings is None:
        return "MISSING"
    explicit = row.get("observed_dwellings")
    if explicit is not None and not (isinstance(explicit, float) and pd.isna(explicit)):
        stamp = row.get("provenance_dwellings")
        return str(stamp) if isinstance(stamp, str) and stamp else "SIDECAR_OBSERVED"
    return "BDTOPO_SURPLUS_TAGS_OBSERVED"


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


def compute_footprint_adjacency_pairs(gdf: gpd.GeoDataFrame) -> dict[str, set[str]]:
    """``osm_id`` -> set of touching ``osm_id`` values, within ``gdf`` only.

    Same predicate as :func:`compute_footprint_adjacency` (EPSG:2154, a
    ``touches``/non-point intersection, self-matches excluded by ``osm_id``),
    exposed as the pairwise graph rather than a per-building boolean.
    """
    projected = gdf.to_crs(epsg=2154).reset_index(drop=True)
    sindex = projected.sindex
    osm_ids = projected["osm_id"]
    pairs: dict[str, set[str]] = {str(oid): set() for oid in osm_ids}
    for position, geometry in enumerate(projected.geometry):
        own_id = osm_ids.iloc[position]
        for candidate in sindex.query(geometry, predicate="intersects"):
            if candidate == position or osm_ids.iloc[candidate] == own_id:
                continue
            intersection = geometry.intersection(projected.geometry.iloc[candidate])
            if intersection.is_empty or intersection.geom_type in (
                "Point",
                "MultiPoint",
            ):
                continue
            pairs[str(own_id)].add(str(osm_ids.iloc[candidate]))
    return pairs


def compute_footprint_adjacency(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Boolean Series, aligned to ``gdf.index``: True where a footprint shares a
    boundary with another footprint in ``gdf``.

    Built from :func:`compute_footprint_adjacency_pairs` — a footprint is
    attached iff its pair-set is non-empty.
    """
    pairs = compute_footprint_adjacency_pairs(gdf)
    attached = [bool(pairs.get(str(oid), set())) for oid in gdf["osm_id"]]
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
        # T04 / D-EU-101 c2: TABULA's own registry has no MFH/AB entry for 13-14
        # dwellings; owner ruling closes the gap by storey partition instead of
        # loosening either neighbour bucket's storey range (investigation report
        # §3, lines 217-234/244).
        return ("MFH" if storeys <= 4 else "AB"), None
    if dwellings == 1 and storeys <= 4:
        return ("TH" if is_attached else "SFH"), None
    if 2 <= dwellings <= 12 and storeys <= 4:
        return "MFH", None
    if 2 <= dwellings <= 12 and 5 <= storeys <= 9:
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
    observed_dwellings = _observed_dwellings(row)
    dwellings_provenance = _dwellings_provenance(row, observed_dwellings)
    derived_dwellings: int | None = None
    derived_exclusion: str | None = None
    if building_type is None and country in ("FR", "ES"):
        derived_dwellings = observed_dwellings
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
            dwellings_provenance=dwellings_provenance,
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
            dwellings_provenance=dwellings_provenance,
        )
    # Layout readiness is a statement about the layout generator's own inputs,
    # not about how the type was obtained.  France reaches it through the ruled
    # two-signal derivation (`D-EU-04-G` G1), which can only fire when both
    # counts are present; Madrid reaches it through the ruled observed tag plus
    # the Catastro dwelling count ingested under `D-EU-23` G1, where the storey
    # count is a separate signal and can be absent.  The requirement is the
    # same either way and is checked here rather than assumed: a type, an
    # observed year, an observed dwelling count and an observed storey count,
    # because `allocate_european_dwellings` needs all four.
    if observed_dwellings is not None and _observed_storeys(row) is None:
        return EuropeanArchetypeMappingDecision(
            neighbourhood_id=neighbourhood_id,
            building_id=building_id,
            country_stock_code=country,
            building_type=building_type,
            year_built=year_built,
            archetype_id=archetype["archetype_id"],
            mapping_status="MAPPED_LAYOUT_BLOCKED_MISSING_STOREY_COUNT",
            reason=MISSING_OBSERVED_STOREY_COUNT,
            layout_ready=False,
            type_provenance=type_provenance,
            dwellings_provenance=dwellings_provenance,
        )
    if observed_dwellings is not None:
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
            dwellings_provenance=dwellings_provenance,
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
        dwellings_provenance=dwellings_provenance,
    )


def apply_attribute_sidecar(gdf: gpd.GeoDataFrame, sidecar: pd.DataFrame) -> gpd.GeoDataFrame:
    """Overlay an attribute sidecar onto a footprint manifest, in memory only.

    `EU-02` ingested footprints; `D-EU-10` pins a separate authoritative
    *attribute* source per city.  This joins the second onto the first by
    ``osm_id`` without ever writing the manifest back, which is why an
    ingestion defect cannot corrupt an audited footprint.  Only rows the
    sidecar actually carries a value for are overwritten.
    """
    required = {"building_id", "year_built", "n_dwellings"}
    missing = required.difference(sidecar.columns)
    if missing:
        raise ValueError(f"Attribute sidecar is missing columns: {sorted(missing)}")
    lookup = sidecar.set_index(sidecar["building_id"].astype(str))
    if lookup.index.duplicated().any():
        raise ValueError("Attribute sidecar must hold one row per building_id")
    keys = gdf["osm_id"].astype(str)
    merged = gdf.copy()
    year = keys.map(lookup["year_built"])
    dwellings = keys.map(lookup["n_dwellings"])
    merged["year_built"] = year.where(year.notna(), merged.get("year_built"))
    merged["provenance_year_built"] = keys.map(
        lookup.get(
            "provenance_year_built",
            pd.Series("SIDECAR_OBSERVED", index=lookup.index),
        )
    ).where(year.notna(), merged.get("provenance_year_built"))
    merged["observed_dwellings"] = dwellings
    merged["provenance_dwellings"] = keys.map(
        lookup.get(
            "provenance_dwellings",
            pd.Series("SIDECAR_OBSERVED", index=lookup.index),
        )
    ).where(dwellings.notna(), None)
    levels = keys.map(lookup.get("levels", pd.Series(dtype="float64", index=lookup.index)))
    merged["levels"] = levels.where(levels.notna(), merged.get("levels"))
    merged["provenance_levels"] = keys.map(
        lookup.get(
            "provenance_levels",
            pd.Series("SIDECAR_OBSERVED", index=lookup.index),
        )
    ).where(levels.notna(), merged.get("provenance_levels"))
    return merged


def write_eu02_archetype_mapping_readiness(
    manifests_root: Path | str,
    output_dir: Path | str,
    *,
    attribute_sidecars: dict[str, Path | str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Write a reproducible mapping/exclusion record for the four EU-02 sites.

    ``attribute_sidecars`` maps a site id to a sidecar CSV written by an
    attribute adapter (`D-EU-10`).  Omitting it reproduces the pre-ingestion
    readiness exactly, which is how the `S2`-era artefact stays reproducible.
    """
    root = Path(manifests_root)
    sidecar_paths = {str(key): Path(value) for key, value in (attribute_sidecars or {}).items()}
    decisions: list[EuropeanArchetypeMappingDecision] = []
    for site_id, country in EU02_SITE_COUNTRY.items():
        manifest = root / site_id / "02_residential_manifest.gpkg"
        if not manifest.is_file():
            raise ValueError(f"Missing audited residential manifest: {manifest}")
        gdf = gpd.read_file(manifest)
        if site_id in sidecar_paths:
            gdf = apply_attribute_sidecar(gdf, pd.read_csv(sidecar_paths[site_id]))
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
        "dwellings_provenance_counts": {
            key: int(value)
            for key, value in frame["dwellings_provenance"].value_counts(sort=True).items()
        },
        "layout_ready_by_site": {
            site: int(((frame["neighbourhood_id"] == site) & frame["layout_ready"]).sum())
            for site in EU02_SITE_COUNTRY
        },
        "attribute_sidecars_applied": sorted(sidecar_paths),
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
