"""Direccion General del Catastro INSPIRE Buildings attribute adapter (``ES``).

``D-EU-10`` pins Madrid's authoritative *attribute* source as the Catastro
INSPIRE ``BU`` theme, while ``EU-02`` ingested OSM footprints.  This module
joins the two and is the ingestion half of ``D-EU-22`` (ruled F1, coverage
measured) and ``D-EU-23`` (ruled G1, ingestion authorised).

Two rules here are structural rather than stylistic:

* **The manifest is never written.**  The adapter returns a *sidecar* keyed on
  the manifest's own ``osm_id``.  ``openubem/outputs/eu02/`` stays
  byte-identical, so an ingestion defect can never silently rewrite an audited
  footprint.
* **A missing attribute is recorded, never defaulted.**  Every manifest row
  leaves this module with either an observed value or a named reason.

The request form is the one measured to work on 2026-08-27: an *ad hoc*
``TYPENAMES=bu:Building`` ``GetFeature`` with the CRS URN appended to ``BBOX``
and lat,lon axis order.  No stored query is bbox-keyed, and ``TYPENAME``
singular is rejected (``OpenUBEM_debug_References.md`` ch. 7).
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import time
from typing import Any, Iterator
import xml.etree.ElementTree as ET

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Polygon, box


CATASTRO_WFS_ENDPOINT = "https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx"
CATASTRO_USER_AGENT = "OpenUBEM-EU04-catastro-ingest/1.0 (research)"

# Measured, not guessed: the D-EU-22 coverage probe printed the full currentUse
# histogram and `1_residential` is the only dwelling-bearing value in it.
RESIDENTIAL_CURRENT_USE = "1_residential"

TILE_DEGREES = 0.002
REQUEST_PAUSE_S = 1.5
MAX_TRIES = 4

#: Metric CRS for every area predicate in this module (ETRS89-LAEA).
JOIN_CRS_EPSG = 3035

YEAR_PROVENANCE = "CATASTRO_INSPIRE_BU_OBSERVED"
DWELLINGS_PROVENANCE = "CATASTRO_INSPIRE_BU_OBSERVED"

NO_CATASTRO_PARTNER = "NO_INTERSECTING_CATASTRO_RESIDENTIAL_BUILDING"
PARTNER_WITHOUT_YEAR = "CATASTRO_PARTNER_CARRIES_NO_CONSTRUCTION_YEAR"
PARTNER_WITHOUT_DWELLINGS = "CATASTRO_PARTNER_CARRIES_NO_DWELLING_COUNT"


@dataclass(frozen=True)
class CatastroFetchReport:
    """What the live service actually returned, for the evidence record."""

    endpoint: str
    tiles_requested: int
    features_returned: int
    unique_features: int
    residential_features: int
    retries: tuple[str, ...]
    seconds: float


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first(element: ET.Element, name: str) -> ET.Element | None:
    for child in element.iter():
        if _local(child.tag) == name:
            return child
    return None


def _tile_bboxes(bounds: tuple[float, float, float, float]) -> list[str]:
    """Cover ``bounds`` (WGS84 lon/lat) with half-tile margin, in lat,lon order."""
    west, south, east, north = bounds
    lats: list[float] = []
    value = south - TILE_DEGREES / 2.0
    while value < north + TILE_DEGREES / 2.0:
        lats.append(value)
        value += TILE_DEGREES
    lons: list[float] = []
    value = west - TILE_DEGREES / 2.0
    while value < east + TILE_DEGREES / 2.0:
        lons.append(value)
        value += TILE_DEGREES
    return [
        f"{lat:.6f},{lon:.6f},{lat + TILE_DEGREES:.6f},{lon + TILE_DEGREES:.6f}"
        for lat in lats
        for lon in lons
    ]


def _request_tile(session: requests.Session, bbox: str, retries: list[str]) -> str:
    params = {
        "service": "wfs",
        "version": "2.0.0",
        "request": "GetFeature",
        "TYPENAMES": "bu:Building",
        "SRSNAME": "urn:ogc:def:crs:EPSG::4326",
        "BBOX": f"{bbox},urn:ogc:def:crs:EPSG::4326",
    }
    last: str | None = None
    for attempt in range(1, MAX_TRIES + 1):
        try:
            response = session.get(CATASTRO_WFS_ENDPOINT, params=params, timeout=300)
            if response.status_code == 200:
                return response.text
            last = f"HTTP {response.status_code}"
        except requests.RequestException as error:
            last = f"{type(error).__name__}: {error}"
        wait = REQUEST_PAUSE_S * (2 ** attempt)
        retries.append(
            f"{bbox}: attempt {attempt}/{MAX_TRIES} failed ({last}), slept {wait:.1f}s"
        )
        time.sleep(wait)
    raise RuntimeError(f"Catastro tile {bbox} failed after {MAX_TRIES} tries: {last}")


def parse_catastro_buildings(document: str) -> Iterator[dict[str, Any]]:
    """Yield one record per ``bu-ext2d:Building`` in a WFS response document."""
    payload = document.encode("utf-8") if isinstance(document, str) else document
    root = ET.fromstring(payload)
    for element in (node for node in root.iter() if _local(node.tag) == "Building"):
        record: dict[str, Any] = {
            "catastro_local_id": None,
            "year_built": None,
            "raw_beginning": None,
            "current_use": None,
            "n_dwellings": None,
            "n_building_units": None,
            "condition": None,
            "geometry": None,
        }
        identifier = _first(element, "localId")
        if identifier is not None and identifier.text:
            record["catastro_local_id"] = identifier.text.strip()
        construction = _first(element, "dateOfConstruction")
        if construction is not None:
            beginning = _first(construction, "beginning")
            if beginning is not None and beginning.text:
                raw = beginning.text.strip()
                record["raw_beginning"] = raw
                if raw[:4].isdigit():
                    record["year_built"] = int(raw[:4])
        for source_name, key in (
            ("currentUse", "current_use"),
            ("numberOfDwellings", "n_dwellings"),
            ("numberOfBuildingUnits", "n_building_units"),
            ("conditionOfConstruction", "condition"),
        ):
            child = _first(element, source_name)
            if child is not None and child.text:
                record[key] = child.text.strip()
        for key in ("n_dwellings", "n_building_units"):
            if record[key] is not None:
                try:
                    record[key] = int(record[key])
                except ValueError:
                    record[key] = None
        positions = _first(element, "posList")
        if positions is not None and positions.text:
            values = [float(item) for item in positions.text.split()]
            # SRSNAME urn:ogc:def:crs:EPSG::4326 means lat,lon axis order.
            points = [(values[i + 1], values[i]) for i in range(0, len(values) - 1, 2)]
            if len(points) >= 4:
                try:
                    record["geometry"] = Polygon(points)
                except ValueError:
                    record["geometry"] = None
        yield record


def fetch_catastro_buildings(
    bounds: tuple[float, float, float, float],
    *,
    session: requests.Session | None = None,
) -> tuple[gpd.GeoDataFrame, CatastroFetchReport]:
    """Fetch every Catastro ``BU`` building intersecting ``bounds`` (WGS84)."""
    started = time.time()
    owned = session is None
    session = session or requests.Session()
    session.headers.update({"User-Agent": CATASTRO_USER_AGENT})
    tiles = _tile_bboxes(bounds)
    retries: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    returned = 0
    try:
        for bbox in tiles:
            for record in parse_catastro_buildings(_request_tile(session, bbox, retries)):
                returned += 1
                key = record["catastro_local_id"]
                if key:
                    by_id[key] = record
                else:
                    anonymous.append(record)
            time.sleep(REQUEST_PAUSE_S)
    finally:
        if owned:
            session.close()

    records = list(by_id.values()) + anonymous
    frame = gpd.GeoDataFrame(records, geometry="geometry", crs=4326)
    frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
    frame = frame[frame.geometry.intersects(box(*bounds))].copy()
    residential = frame[frame["current_use"] == RESIDENTIAL_CURRENT_USE]
    report = CatastroFetchReport(
        endpoint=CATASTRO_WFS_ENDPOINT,
        tiles_requested=len(tiles),
        features_returned=returned,
        unique_features=int(len(frame)),
        residential_features=int(len(residential)),
        retries=tuple(retries),
        seconds=round(time.time() - started, 2),
    )
    return frame.reset_index(drop=True), report


def build_es_attribute_sidecar(
    manifest: gpd.GeoDataFrame,
    catastro: gpd.GeoDataFrame,
    *,
    neighbourhood_id: str,
) -> pd.DataFrame:
    """Join Catastro attributes onto manifest footprints, fail-closed.

    One row per manifest footprint.  The credited partner is the intersecting
    **residential** Catastro building with the largest overlap area -- the same
    predicate the ``D-EU-22`` coverage probe measured, so the ingested join
    rate is comparable with the probed one rather than a differently defined
    number.
    """
    if "osm_id" not in manifest.columns:
        raise ValueError("The EU-02 manifest must carry osm_id")

    residential = catastro[catastro["current_use"] == RESIDENTIAL_CURRENT_USE].copy()
    footprints = manifest.to_crs(JOIN_CRS_EPSG).reset_index(drop=True)
    partners = residential.to_crs(JOIN_CRS_EPSG).reset_index(drop=True)
    footprints["_footprint_index"] = range(len(footprints))
    partners["_partner_index"] = range(len(partners))

    best: dict[int, tuple[int, float]] = {}
    if len(partners):
        pairs = gpd.sjoin(
            footprints[["_footprint_index", "geometry"]],
            partners[["_partner_index", "geometry"]],
            how="inner",
            predicate="intersects",
        )
        partner_geometry = partners.set_index("_partner_index").geometry
        for footprint_index, partner_index in zip(
            pairs["_footprint_index"].to_numpy(), pairs["_partner_index"].to_numpy()
        ):
            overlap = float(
                footprints.geometry.iloc[footprint_index]
                .intersection(partner_geometry.loc[partner_index])
                .area
            )
            if footprint_index not in best or overlap > best[footprint_index][1]:
                best[footprint_index] = (int(partner_index), overlap)

    partner_rows = partners.set_index("_partner_index")
    records: list[dict[str, Any]] = []
    for position, osm_id in enumerate(footprints["osm_id"].astype(str)):
        record: dict[str, Any] = {
            "neighbourhood_id": neighbourhood_id,
            "building_id": osm_id,
            "catastro_local_id": None,
            "year_built": None,
            "n_dwellings": None,
            "n_building_units": None,
            "condition": None,
            "overlap_area_m2": None,
            "join_predicate": "LARGEST_OVERLAP_INTERSECTS_EPSG3035",
            "provenance_year_built": "CATASTRO_MISSING",
            "provenance_dwellings": "CATASTRO_MISSING",
            "reason": "",
        }
        if position not in best:
            record["reason"] = NO_CATASTRO_PARTNER
            records.append(record)
            continue
        partner_index, overlap = best[position]
        partner = partner_rows.loc[partner_index]
        record["catastro_local_id"] = partner["catastro_local_id"]
        record["overlap_area_m2"] = round(overlap, 4)
        record["condition"] = partner["condition"]
        reasons: list[str] = []
        year = partner["year_built"]
        if year is not None and not pd.isna(year) and int(year) > 0:
            record["year_built"] = int(year)
            record["provenance_year_built"] = YEAR_PROVENANCE
        else:
            reasons.append(PARTNER_WITHOUT_YEAR)
        dwellings = partner["n_dwellings"]
        if dwellings is not None and not pd.isna(dwellings) and int(dwellings) > 0:
            record["n_dwellings"] = int(dwellings)
            record["provenance_dwellings"] = DWELLINGS_PROVENANCE
        else:
            reasons.append(PARTNER_WITHOUT_DWELLINGS)
        units = partner["n_building_units"]
        if units is not None and not pd.isna(units):
            record["n_building_units"] = int(units)
        record["reason"] = ";".join(reasons)
        records.append(record)

    sidecar = pd.DataFrame(records)
    if sidecar["building_id"].duplicated().any():
        raise ValueError("The ES attribute sidecar must hold one row per footprint")
    return sidecar


def sidecar_summary(sidecar: pd.DataFrame, report: CatastroFetchReport) -> dict[str, Any]:
    """Counts an acceptance panel can read without recomputing the join."""
    joined = sidecar["catastro_local_id"].notna()
    year = sidecar["year_built"].notna()
    dwellings = sidecar["n_dwellings"].notna()
    return {
        "evidence_scope": "es_catastro_attribute_ingestion_sidecar",
        "ruling": "D-EU-23 Option G1 (FR + ES ingestion authorised, 2026-08-27)",
        "attribute_source": "Madrid Catastro INSPIRE BU (D-EU-10)",
        "endpoint": report.endpoint,
        "tiles_requested": report.tiles_requested,
        "features_returned": report.features_returned,
        "unique_features_in_study_bbox": report.unique_features,
        "residential_features": report.residential_features,
        "retries": list(report.retries),
        "fetch_seconds": report.seconds,
        "manifest_rows": int(len(sidecar)),
        "rows_with_catastro_partner": int(joined.sum()),
        "rows_with_observed_year": int(year.sum()),
        "rows_with_observed_dwelling_count": int(dwellings.sum()),
        "rows_with_both_signals": int((year & dwellings).sum()),
        "reason_counts": {
            key: int(value)
            for key, value in sidecar.loc[sidecar["reason"] != "", "reason"]
            .value_counts()
            .items()
        },
        "dwelling_count_bands": {
            "eq_1": int((sidecar["n_dwellings"] == 1).sum()),
            "2_to_4": int(sidecar["n_dwellings"].between(2, 4).sum()),
            "5_to_12": int(sidecar["n_dwellings"].between(5, 12).sum()),
            "13_to_14": int(sidecar["n_dwellings"].between(13, 14).sum()),
            "ge_15": int((sidecar["n_dwellings"] >= 15).sum()),
        },
        "manifest_written": False,
        "note": (
            "This is a sidecar. Nothing under openubem/outputs/eu02/ is written by the "
            "ingestion, so the audited EU-02 footprints stay byte-identical."
        ),
    }


def sidecar_sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
