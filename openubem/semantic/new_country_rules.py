from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from openubem.semantic.construction_sets import _TABULA_PERIODS, select_tabula_archetype, tabula_period
from openubem.semantic.european_archetype_mapping import (
    EU02_SITE_COUNTRY,
    OBSERVED_TAG_TO_TABULA_TYPE,
    _observed_dwellings,
    _observed_year,
    compute_footprint_adjacency,
    derive_bdtopo_building_type,
)

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_22 = ROOT / "openubem/outputs/eu_evidence/EU-22"

NEW_COUNTRIES = {"AT", "KR", "CA", "FI", "ZA", "HU", "AM"}

CENSUS_PERIOD_PROVENANCE = "IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD"
HEIGHT_STOREY_PROVENANCE = "DERIVED_HEIGHT_M_OVER_3"
STOREY_RULE_PROVENANCE = "DERIVED_STOREY_RULE"
MISSING_CENSUS_UNIT_DATA = "MISSING_CENSUS_UNIT_DATA"
MISSING_OBSERVED_STOREY_COUNT = "MISSING_OBSERVED_STOREY_COUNT"


class NewCountryExclusions(Counter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.records: list[dict] = []

    def log(self, building_id: object, stage: str, blocker: str, detail: str = "") -> None:
        self[blocker] += 1
        self.records.append(
            {"building_id": str(building_id), "stage": stage, "blocker": blocker, "detail": detail}
        )


def _label_token(label: str) -> str:
    return re.sub(r"\W+", "_", str(label)).strip("_")


def dominant_period(counts: dict[str, Any], period_years: dict[str, int]) -> tuple[int | None, str]:
    positive: dict[str, int] = {}
    for label, value in counts.items():
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number > 0:
            positive[str(label)] = number
    if not positive:
        return None, "CENSUS_UNIT_NO_PERIOD_DATA"
    top = max(positive.values())
    leaders = [label for label, value in positive.items() if value == top]
    if len(leaders) > 1:
        return None, "CENSUS_UNIT_PERIOD_TIE_" + "_".join(_label_token(x) for x in leaders)
    label = leaders[0]
    if label not in period_years:
        return None, f"UNMAPPABLE_PERIOD_{_label_token(label)}"
    return int(period_years[label]), label


def load_period_years(district: str) -> dict[str, int]:
    path = EVIDENCE_22 / district / "acquisition_report.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): int(v) for k, v in (payload.get("period_years") or {}).items()}


def _census_counts(row: pd.Series) -> dict[str, Any] | None:
    raw = row.get("census_period_counts")
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = json.loads(raw)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def resolve_year(row: pd.Series, period_years: dict[str, int]) -> tuple[int | None, str, str]:
    observed = _observed_year(row)
    if observed is not None:
        return observed, "", ""
    counts = _census_counts(row)
    if counts is None:
        return None, "", MISSING_CENSUS_UNIT_DATA
    year, label = dominant_period(counts, period_years)
    if year is None:
        return None, "", label
    return year, CENSUS_PERIOD_PROVENANCE, ""


def _measured_height_m(row: pd.Series) -> float | None:
    value = row.get("height_m")
    if value is None or pd.isna(value):
        return None
    try:
        height = float(value)
    except (TypeError, ValueError):
        return None
    if not height > 0:
        return None
    provenance = str(row.get("provenance_height_m", ""))
    if not (provenance.endswith("_MEASURED") or provenance.endswith("_OBSERVED")):
        return None
    return height


def resolve_storeys(row: pd.Series) -> tuple[int | None, str]:
    try:
        levels = float(row.get("levels"))
    except (TypeError, ValueError):
        levels = float("nan")
    if levels > 0 and levels.is_integer():
        return int(levels), ""
    height = _measured_height_m(row)
    if height is not None:
        return max(1, round(height / 3.0)), HEIGHT_STOREY_PROVENANCE
    return None, ""


def storey_rule_type(storeys: int, is_attached: bool) -> str:
    if storeys <= 2:
        return "TH" if is_attached else "SFH"
    if storeys in (3, 4):
        return "MFH"
    return "AB"


def observed_tag_type(row: pd.Series) -> str | None:
    return OBSERVED_TAG_TO_TABULA_TYPE.get(str(row.get("building_tag", "")).strip().casefold())


def resolve_type(row: pd.Series, storeys: int, is_attached: bool) -> tuple[str, str]:
    tagged = observed_tag_type(row)
    if tagged is not None:
        return tagged, "OBSERVED_TAG"
    dwellings = _observed_dwellings(row)
    if dwellings is not None:
        derived, _ = derive_bdtopo_building_type(dwellings, storeys, is_attached)
        if derived is not None:
            return derived, "DERIVED_BDTOPO_TWO_SIGNAL"
    return storey_rule_type(storeys, is_attached), STOREY_RULE_PROVENANCE


TYPE_SUBSTITUTE = {"AB": "MFH", "TH": "SFH", "MFH": "AB", "SFH": "TH"}


def select_record_with_substitute(
    records: list[dict], country: str, building_type: str, year: int,
) -> tuple[dict, str]:
    try:
        return select_tabula_archetype(records, country, building_type, year), ""
    except ValueError as error:
        if not str(error).startswith("ARCHETYPE_NO_MATCH"):
            raise
        used = TYPE_SUBSTITUTE.get(building_type.upper())
        if used is None:
            raise
        try:
            record = select_tabula_archetype(records, country, used, year)
        except ValueError:
            raise error from None
        return record, f"TABULA_TYPE_SUBSTITUTE_{used}_FOR_{building_type.upper()}"


def build_row(
    item: pd.Series, *, country: str, records: list[dict], year: int, year_provenance: str,
    storeys: int, storey_provenance: str, is_attached: bool,
) -> tuple[dict | None, str, str]:
    building_type, type_provenance = resolve_type(item, storeys, is_attached)
    try:
        record, record_provenance = select_record_with_substitute(records, country, building_type, year)
    except ValueError as error:
        return None, f"ARCHETYPE_RESOLUTION_FAILED_{str(error).split(':', 1)[0]}", str(error)
    row = {
        **item.to_dict(),
        "building_id": str(item.osm_id),
        "building_type": building_type,
        "archetype_id": record["archetype_id"],
        "archetype_provenance": record_provenance,
        "age_band": tabula_period(country, year),
        "year_built": year,
        "levels": storeys,
        "is_attached": is_attached,
        "type_provenance": type_provenance,
        "construction_period_provenance": year_provenance,
        "storey_provenance": storey_provenance,
    }
    return row, "", ""


def attached_by_id(gdf: gpd.GeoDataFrame) -> dict[str, bool]:
    series = compute_footprint_adjacency(gdf)
    return {str(oid): bool(flag) for oid, flag in zip(gdf["osm_id"], series)}


def new_country_rows(
    district: str, gdf: gpd.GeoDataFrame, records: list[dict], period_years: dict[str, int] | None = None,
) -> tuple[list[dict], Counter]:
    country = EU02_SITE_COUNTRY[district]
    if country not in NEW_COUNTRIES:
        raise ValueError(f"{district} is not a new-country site")
    if country not in _TABULA_PERIODS:
        raise ValueError(f"No TABULA construction periods registered for {country}")
    years = load_period_years(district) if period_years is None else period_years
    attached = attached_by_id(gdf)
    exclusions = NewCountryExclusions()
    result: list[dict] = []
    for _, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        building_id = str(item.osm_id)
        year, year_provenance, blocker = resolve_year(item, years)
        if year is None:
            exclusions.log(building_id, "base_mapping", blocker)
            continue
        storeys, storey_provenance = resolve_storeys(item)
        if storeys is None:
            exclusions.log(building_id, "base_mapping", MISSING_OBSERVED_STOREY_COUNT)
            continue
        row, blocker, detail = build_row(
            item, country=country, records=records, year=year, year_provenance=year_provenance,
            storeys=storeys, storey_provenance=storey_provenance, is_attached=attached[building_id],
        )
        if row is None:
            exclusions.log(building_id, "base_mapping", blocker, detail=detail)
            continue
        result.append(row)
    return result, exclusions
