"""EU-11: parameterised, fail-closed S2 district fleet preparation.

This is deliberately an IDF *preparer*, not a local fleet runner.  It retains
the accepted S2 IDF assembly in :mod:`scripts.run_eu_s2_campaign` unchanged,
then writes one IDF per eligible real footprint for a Speed ``sbatch --array``
campaign.  Results are harvested separately from Speed SQL files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import zipfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry.polygon import orient

from openubem.acquisition.european_weather import sha256_file
from openubem.geometry.european_residential import (
    allocate_european_dwellings, european_layout_to_zone_specs,
    european_building_layout_to_zone_specs,
    _stabilize_ring_coords,
    generate_european_building_dwelling_layout,
    generate_european_dwelling_layout,
)
from openubem.geometry.zoning import build_zones
from openubem.semantic.construction_sets import select_tabula_archetype, tabula_period
from openubem.semantic.european_archetype_mapping import (
    EU02_SITE_COUNTRY, apply_attribute_sidecar, compute_footprint_adjacency,
    compute_footprint_adjacency_pairs, map_observed_building_to_tabula,
)
from scripts.run_eu_s2_campaign import (
    EUROPEAN_CONTEXT_RADIUS_M, FLOOR_TO_FLOOR_M, ZONE_WINDING_SIGN,
    build_european_context, build_idf_for_building,
    compute_district_median_residential_height_m,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "openubem/data/weather/weather_registry.json"
EVIDENCE = ROOT / "openubem/outputs/eu_evidence/EU-11"
ES_SIDECAR = ROOT / "openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv"
GB_EPC = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_certificates.csv"
GB_EPC_YEARS = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv"
GB_EPC_CERT_CACHE = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/certificate"

DISTRICTS = {
    "ES-MAD-BERRUGUETE": {"country": "ES", "fold": "es", "crs": "EPSG:32630"},
    "FR-LYO-HAUTCOEURPENTES": {"country": "FR", "fold": "fr", "crs": "EPSG:32631"},
    "GB-LDN-STDUNSTANS": {"country": "GB", "fold": "uk", "crs": "EPSG:32630"},
    "IT-BOL-GALVANI2": {"country": "IT", "fold": "it", "crs": "EPSG:32632"},
}
MANIFEST_COLUMNS = [
    "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
    "idf_sha256", "weather_sha256", "eplus_return_code", "severe_errors", "fatal_errors",
    "heating_kwh", "floor_area_m2", "eui_kwh_m2", "run_seconds", "platform", "energyplus_version",
]
# EPC bands are intervals, not invented years.  A band may be used only when
# the complete interval belongs to one TABULA period; straddles remain excluded.
GB_EPC_BANDS = {
    "A": (0, 1899), "B": (1900, 1929), "C": (1930, 1949), "D": (1950, 1966),
    "E": (1967, 1975), "F": (1976, 1982), "G": (1983, 1990), "H": (1991, 1995),
    "I": (1996, 2002), "J": (2003, 2006), "K": (2007, 2011), "L": (2012, 9999),
}


class _ExclusionCounter(Counter):
    """T01 (`eu-recut-95pct-2026-09-08`): a ``Counter`` that also keeps the
    per-building row behind every increment, so ``excluded_buildings.csv``
    and the existing ``blocker_exclusions`` histogram always come from the
    same source. Still a plain ``Counter`` to every existing caller that only
    reads it as one (``.items()``, ``+``, membership) -- ``.records`` and
    ``.log()`` are additions, not a new interface.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.records: list[dict] = []

    def log(self, building_id: object, stage: str, blocker: str, detail: str = "") -> None:
        self[blocker] += 1
        self.records.append(
            {"building_id": str(building_id), "stage": stage, "blocker": blocker, "detail": detail}
        )


class _GeometryOutcome(str):
    """T01: ``_geometry``'s outcome token, also carrying the storey layout's
    own ``fallback_reason`` (or best-effort tag) as ``.layout_reason``. A
    plain ``str`` subclass so every existing 2-unpack caller of ``_geometry``
    keeps working unchanged.
    """

    def __new__(cls, value: str, layout_reason: str | None = None) -> "_GeometryOutcome":
        self = str.__new__(cls, value)
        self.layout_reason = layout_reason
        return self


def _registry_weather(fold: str, requested: Path | None) -> tuple[Path, str]:
    target = next(x for x in json.loads(REGISTRY.read_text(encoding="utf-8"))["targets"] if x["fold"] == fold)
    epw = requested or (ROOT / target["weather_file"])
    digest = sha256_file(epw)
    if digest != target["sha256"]:
        raise ValueError(f"EPW SHA-256 mismatch for {fold}: registry={target['sha256']} actual={digest}")
    return epw, digest


def _records(country: str) -> list[dict]:
    return json.loads((ROOT / f"openubem/data/construction/tabula_archetypes_{country.lower()}.json").read_text(encoding="utf-8"))["records"]


def _record_for_period(records: list[dict], country: str, building_type: str, period: str) -> dict:
    matches = []
    token = period.split(".")[-1]
    for row in records:
        if row["country_stock_code"] != country or building_type not in row["source_building_type_code"].split(".")[2].split("-"):
            continue
        field = row["source_building_code"].split(".")[3]
        if field == token or ("-" in field and int(field.split("-")[0]) <= int(token) <= int(field.split("-")[1])):
            matches.append(row)
    simple = [x for x in matches if "-" not in x["source_building_type_code"].split(".")[2] and "-" not in x["source_building_code"].split(".")[3]]
    matches = simple or matches
    generated = [x for x in matches if ".Gen." in x["source_building_code"]]
    if len(generated) == 1:
        return generated[0]
    if len(matches) != 1:
        raise ValueError(f"ARCHETYPE_AMBIGUOUS: {country}/{building_type}/{period}")
    return matches[0]


def _valid_storeys(row: pd.Series) -> int | None:
    try:
        value = float(row["levels"])
    except (TypeError, ValueError):
        return None
    return int(value) if value > 0 and value.is_integer() else None


def _geometry(row: pd.Series, records: list[dict]) -> tuple[list[dict], str]:
    """D-EU-33 parity with ``scripts/emit_eu11_layout_sidecars.py``: this is the

    only function that produces the *simulated* zones (the side-car emitter
    produces a separate, post-hoc visualization layer). Both must derive the
    same dwelling count (observed, or the same four-tier imputation) and the
    same n_storey-stacked zones, or the pop-up's geometry_outcome disagrees
    with what actually ran on EnergyPlus.
    """
    footprint = row.geometry
    n_storey = _valid_storeys(row)
    if n_storey is None:
        raise ValueError("MISSING_OBSERVED_STOREY_COUNT")
    dwellings = row.get("observed_dwellings")
    is_observed = pd.notna(dwellings) and float(dwellings).is_integer() and float(dwellings) > 0
    if is_observed:
        dwellings_val = int(dwellings)
    else:
        btype = row["building_type"]
        if btype in ("SFH", "TH"):
            dwellings_val = 1
        else:
            rec = next((x for x in records if x["archetype_id"] == row["archetype_id"]), None)
            n_apt = rec.get("n_apartment") if rec else 10.0
            dwellings_val = max(1, round(float(n_apt))) if pd.notna(n_apt) else 10

    allocation = allocate_european_dwellings(
        archetype_id=row["archetype_id"], building_type=row["building_type"],
        n_apartment=dwellings_val, n_storey=n_storey, plate_area_m2=float(footprint.area),
    )
    # EU-13B T01/T02: partition each storey into its own conserved
    # floor_allocations[s].dwelling_count (never the ceil(total/storeys)
    # units_per_floor constant replayed across every storey), and fail the
    # whole building closed above the ruled grid's 8/floor ceiling rather
    # than approximating it.
    building_layout = generate_european_building_dwelling_layout(
        footprint, floor_allocations=allocation.floor_allocations,
    )
    # T01: the layout's own reason (refusal reason when not emitted, or the
    # first non-empty per-storey best-effort tag when emitted) -- thrown away
    # by every caller until now (fact 4).
    layout_reason = building_layout.fallback_reason or next(
        (reason for reason in building_layout.fallback_reason_by_storey if reason), None
    )
    if building_layout.dwelling_layout_emitted:
        zones = european_building_layout_to_zone_specs(
            building_layout, building_id=row["building_id"], height_m=FLOOR_TO_FLOOR_M,
        )
        # D-EU-111 (T02): a best-effort storey rides `fallback_reason_by_storey`
        # unchanged (fact 3) -- surface it as its own outcome token, never
        # folded into the plain `DWELLING_LAYOUT_EMITTED*` tokens.
        is_best_effort = any(
            reason and reason.startswith("NOCORE_BEST_EFFORT_")
            for reason in building_layout.fallback_reason_by_storey
        )
        if is_best_effort:
            outcome = "DWELLING_LAYOUT_EMITTED_BEST_EFFORT" if is_observed else "DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT"
        else:
            outcome = "DWELLING_LAYOUT_EMITTED" if is_observed else "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT"
    else:
        zones = build_zones(row["building_id"], footprint, row["archetype_id"], n_storey, "one_zone_per_floor", FLOOR_TO_FLOOR_M)
        outcome = "FALLBACK_PENDING_LAYOUT" if is_observed else "FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT"
    for zone in zones:
        poly = orient(zone["floor_polygon"], sign=ZONE_WINDING_SIGN)
        zone["floor_polygon"] = poly
        # EU-16 T09 D-EU-42/D-EU-43: `orient()` re-derives coords from the raw
        # (unstabilized) floor_polygon, which previously discarded the 1 mm
        # precision-snap `european_building_layout_to_zone_specs` already
        # applied above -- re-stabilize here, the actual last point before
        # `coords_m` is baked into the IDF, so the fix survives orientation.
        zone["coords_m"] = _stabilize_ring_coords(poly)
    return zones, _GeometryOutcome(outcome, layout_reason)


def _gb_age_decision(band: str | None, observed_years: set[int]) -> tuple[str, str, str] | tuple[None, str, str]:
    """Resolve one GB footprint's TABULA period, fail-closed.

    Returns ``(period, age_band_label, construction_period_provenance)`` on success, or
    ``(None, exclusion_key, "")`` when the evidence does not determine a single period.
    An observed ``construction_year`` is a point, so it can only ever narrow the band,
    never widen it; a year that contradicts its own band is refused, not preferred.
    """
    if band not in GB_EPC_BANDS:
        periods = {tabula_period("GB", year) for year in observed_years}
        if len(periods) == 1:
            return periods.pop(), band if band in GB_EPC_BANDS else "", "EPC_OBSERVED_CONSTRUCTION_YEAR"
        return None, "MISSING_OBSERVED_EPC_AGE_BAND", ""
    lo, hi = GB_EPC_BANDS[band]
    first, last = tabula_period("GB", lo), tabula_period("GB", hi)
    if first == last:
        return first, band, ""
    in_band = {year for year in observed_years if lo <= year <= hi}
    in_band_periods = {tabula_period("GB", year) for year in in_band}
    if observed_years and in_band == observed_years and len(in_band_periods) == 1:
        return in_band_periods.pop(), band, "EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE"
    return None, f"PERIOD_STRADDLE_{band}_{first}_{last}", ""


def _gb_age_decision_multi(bands: list[str], observed_years: set[int]) -> tuple[str, str, str] | tuple[None, str, str]:
    """Resolve one GB footprint's TABULA period from every certificate's age band,
    not just the latest one (T02 / D-EU-101 c1, investigation report §1.3(iii)).

    Each known band is a constraint on the *set of TABULA periods its interval
    touches* -- its two endpoint years' periods, sufficient because no
    ``GB_EPC_BANDS`` interval is wide enough to touch a third period. Each
    distinct observed ``construction_year`` is a further singleton-period
    constraint. Intersecting every such set (method (iii), "both constraints
    together") resolves a period when exactly one remains. Zero or one known
    band delegates straight to ``_gb_age_decision`` -- byte-identical old
    behaviour, zero regression risk.
    """
    known = sorted({b for b in bands if b in GB_EPC_BANDS})
    if len(known) <= 1:
        return _gb_age_decision(known[0] if known else None, observed_years)
    label = "|".join(known)
    constraints = [
        {tabula_period("GB", GB_EPC_BANDS[b][0]), tabula_period("GB", GB_EPC_BANDS[b][1])}
        for b in known
    ]
    constraints += [{tabula_period("GB", year)} for year in sorted(observed_years)]
    intersection = set.intersection(*constraints)
    if len(intersection) == 1:
        return intersection.pop(), label, "EPC_MULTI_CERTIFICATE_BAND_INTERSECTION"
    if not intersection:
        return None, f"PERIOD_STRADDLE_DISJOINT_BANDS_{label}", ""
    return None, f"PERIOD_STRADDLE_AMBIGUOUS_{label}", ""


def _gb_sap_floor_storeys(certificate_numbers: list[str]) -> int | None:
    """T01 / D-EU-101 c3: a dwelling-level ``sap_floor_dimensions`` list read as a
    building storey count (investigation report §2.2). Callers restrict this to
    ``house``/``terrace`` tags only -- for ``apartments`` the certificate covers
    one flat, not the block, so the count would say nothing about the building.
    Takes the max over every cached certificate on the footprint, the right
    estimator only if at least one certificate covers the tallest part.
    """
    best = None
    for cert_number in certificate_numbers:
        path = GB_EPC_CERT_CACHE / f"{cert_number}.json"
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        parts = ((payload.get("body") or {}).get("data") or {}).get("sap_building_parts") or []
        for part in parts:
            dims = part.get("sap_floor_dimensions")
            if dims:
                best = len(dims) if best is None else max(best, len(dims))
    return best


def _gb_cert_lookups(gdf: gpd.GeoDataFrame) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, set[int]]]:
    cert = pd.read_csv(GB_EPC)
    # T01/c3: every certificate on a footprint, not just the age-resolving one --
    # `sap_floor_dimensions` can sit on a certificate lacking a construction_age_band.
    cert_numbers_by_osm_id = (
        cert.assign(osm_id=cert["osm_id"].astype(str))
        .groupby("osm_id")["certificateNumber"]
        .apply(lambda s: [str(x) for x in s.dropna()])
        .to_dict()
    )
    cert = cert.dropna(subset=["age_band", "osm_id", "registrationDate"]).copy()
    cert["registrationDate"] = pd.to_datetime(cert["registrationDate"], errors="coerce")
    # T02/c1: every distinct age band on a footprint, not just the latest certificate's --
    # each band is a constraint (its GB_EPC_BANDS interval); _gb_age_decision_multi
    # intersects them instead of discarding all but the newest (report §1.3(ii)/(iii)).
    bands_all_by_osm_id: dict[str, list[str]] = (
        cert.assign(osm_id=cert["osm_id"].astype(str))
        .groupby("osm_id")["age_band"]
        .apply(lambda s: sorted({str(v) for v in s}))
        .to_dict()
    )
    year_lookup: dict[str, set[int]] = {}
    if GB_EPC_YEARS.exists():
        side = pd.read_csv(GB_EPC_YEARS)
        for key, group in side.groupby(side["osm_id"].astype(str)):
            year_lookup[key] = {int(v) for v in group["construction_year"]}
    return cert_numbers_by_osm_id, bands_all_by_osm_id, year_lookup


def _gb_row_outcome(
    item: pd.Series, is_attached: bool, records: list[dict],
    first: str | None, age_label: str, period_provenance: str,
    cert_numbers: list[str], storey_override: tuple[int, str] | None = None,
) -> tuple[dict | None, str]:
    if first is None:
        return None, age_label
    building_id = str(item.osm_id)
    tag = str(item.building_tag).casefold()
    n_storeys = _valid_storeys(item)
    # OSM `house` cannot distinguish SFH from TH on its own (D-EU-04-G rationale,
    # openubem/semantic/european_archetype_mapping.py:28-30) -- split it by footprint
    # adjacency, the same signal already used for FR/IT, rather than assume SFH.
    if tag == "house":
        building_type = "TH" if is_attached else "SFH"
    elif tag == "residential":
        # T03/c6 (D-EU-101): bare `building=residential` carries no SFH/TH/MFH/AB
        # signal of its own -- apply the Bologna storey-ladder rule (report §7)
        # to the storey count GB already has (levels, or `house`'s adjacency split).
        if n_storeys is None:
            building_type = None
        elif n_storeys <= 2:
            building_type = "TH" if is_attached else "SFH"
        elif n_storeys in (3, 4):
            building_type = "MFH"
        else:
            building_type = "AB"
    else:
        building_type = {"apartments": "AB", "detached": "SFH", "terrace": "TH"}.get(tag)
    if building_type is None:
        return None, "UNMAPPABLE_RESIDENTIAL_TYPE"
    storey_provenance = ""
    if n_storeys is None and tag in ("house", "terrace"):
        # T01/c3 (D-EU-101): dwelling-level sap_floor_dimensions read as the
        # building storey count, `apartments` excluded on purpose (report §2.2).
        n_storeys = _gb_sap_floor_storeys(cert_numbers)
        if n_storeys is not None:
            storey_provenance = "SAP_FLOOR_DIMENSIONS"
    if n_storeys is None and storey_override is not None:
        n_storeys, storey_provenance = storey_override
    if n_storeys is None:
        return None, "MISSING_OBSERVED_STOREY_COUNT"
    if storey_provenance:
        item = item.copy(); item["levels"] = n_storeys
    record = _record_for_period(records, "GB", building_type, first)
    row = {**item.to_dict(), "building_id": building_id, "building_type": building_type,
           "archetype_id": record["archetype_id"], "age_band": age_label or first,
           "construction_period_provenance": period_provenance,
           "storey_provenance": storey_provenance, "observed_dwellings": None}
    return row, ""


def _gb_rows(gdf: gpd.GeoDataFrame, records: list[dict]) -> tuple[list[dict], Counter]:
    cert_numbers_by_osm_id, bands_all_by_osm_id, year_lookup = _gb_cert_lookups(gdf)
    is_attached_series = compute_footprint_adjacency(gdf)
    exclusions: Counter = _ExclusionCounter()
    result = []
    for idx, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        building_id = str(item.osm_id)
        first, age_label, period_provenance = _gb_age_decision_multi(
            bands_all_by_osm_id.get(building_id, []), year_lookup.get(building_id, set())
        )
        row, blocker = _gb_row_outcome(
            item, bool(is_attached_series.loc[idx]), records, first, age_label, period_provenance,
            cert_numbers_by_osm_id.get(building_id, []),
        )
        if row is None:
            exclusions.log(building_id, "base_mapping", blocker); continue
        result.append(row)
    return result, exclusions


_STRADDLE_SINGLE_BAND_RE = re.compile(r"^PERIOD_STRADDLE_[A-Z]_(GB\.\d+)_(GB\.\d+)$")


def _gb_parse_straddle_periods(blocker_key: str) -> tuple[str, str] | None:
    match = _STRADDLE_SINGLE_BAND_RE.match(blocker_key)
    return (match.group(1), match.group(2)) if match else None


def _gb_terrace_recovery_rows(
    gdf: gpd.GeoDataFrame, records: list[dict], base_rows: list[dict],
) -> tuple[list[dict], Counter]:
    cert_numbers_by_osm_id, bands_all_by_osm_id, year_lookup = _gb_cert_lookups(gdf)
    pairs = compute_footprint_adjacency_pairs(gdf)
    is_attached_series = compute_footprint_adjacency(gdf)

    base_by_id = {str(r["building_id"]): r for r in base_rows}
    base_period_by_id: dict[str, str] = {}
    base_storeys_by_id: dict[str, int] = {}
    for bid, row in base_by_id.items():
        first, _label, _prov = _gb_age_decision_multi(
            bands_all_by_osm_id.get(bid, []), year_lookup.get(bid, set())
        )
        if first is not None:
            base_period_by_id[bid] = first
        storeys = _valid_storeys(pd.Series(row))
        if storeys is not None:
            base_storeys_by_id[bid] = storeys

    exclusions: Counter = _ExclusionCounter()
    recovered: list[dict] = []
    for idx, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        building_id = str(item.osm_id)
        if building_id in base_by_id:
            continue
        first, age_label, period_provenance = _gb_age_decision_multi(
            bands_all_by_osm_id.get(building_id, []), year_lookup.get(building_id, set())
        )
        if first is not None:
            continue
        straddle_periods = _gb_parse_straddle_periods(age_label)
        if age_label != "MISSING_OBSERVED_EPC_AGE_BAND" and straddle_periods is None:
            continue
        prepared_touching = pairs.get(building_id, set()) & base_by_id.keys()
        if not prepared_touching:
            exclusions.log(building_id, "recovery_pass", f"{age_label}_NO_PREPARED_NEIGHBOUR"); continue
        neighbour_periods = {base_period_by_id[nid] for nid in prepared_touching if nid in base_period_by_id}
        if len(neighbour_periods) != 1:
            exclusions.log(building_id, "recovery_pass", f"{age_label}_NEIGHBOURS_DISAGREE"); continue
        inherited_period = neighbour_periods.pop()
        if straddle_periods is not None:
            if inherited_period not in straddle_periods:
                exclusions.log(building_id, "recovery_pass", f"{age_label}_NEIGHBOUR_OUTSIDE_STRADDLE"); continue
            age_provenance = "INFERRED_TERRACE_NEIGHBOUR_PERIOD_WITHIN_STRADDLE"
        else:
            age_provenance = "INFERRED_TERRACE_NEIGHBOUR_AGE"
        neighbour_storeys = {base_storeys_by_id[nid] for nid in prepared_touching if nid in base_storeys_by_id}
        storey_override = (
            (neighbour_storeys.pop(), "INFERRED_TERRACE_NEIGHBOUR_STOREYS")
            if len(neighbour_storeys) == 1 else None
        )
        row, blocker = _gb_row_outcome(
            item, bool(is_attached_series.loc[idx]), records,
            inherited_period, "", age_provenance,
            cert_numbers_by_osm_id.get(building_id, []), storey_override=storey_override,
        )
        if row is None:
            exclusions.log(building_id, "recovery_pass", f"AGE_RECOVERED_THEN_{blocker}"); continue
        recovered.append(row)

    for idx, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        building_id = str(item.osm_id)
        if building_id in base_by_id:
            continue
        first, age_label, period_provenance = _gb_age_decision_multi(
            bands_all_by_osm_id.get(building_id, []), year_lookup.get(building_id, set())
        )
        if first is None:
            continue
        _row, blocker = _gb_row_outcome(
            item, bool(is_attached_series.loc[idx]), records, first, age_label, period_provenance,
            cert_numbers_by_osm_id.get(building_id, []),
        )
        if blocker != "MISSING_OBSERVED_STOREY_COUNT":
            continue
        prepared_touching = pairs.get(building_id, set()) & base_by_id.keys()
        if not prepared_touching:
            exclusions.log(building_id, "recovery_pass", "MISSING_OBSERVED_STOREY_COUNT_NO_PREPARED_NEIGHBOUR"); continue
        neighbour_storeys = {base_storeys_by_id[nid] for nid in prepared_touching if nid in base_storeys_by_id}
        if len(neighbour_storeys) != 1:
            exclusions.log(building_id, "recovery_pass", "MISSING_OBSERVED_STOREY_COUNT_NEIGHBOURS_DISAGREE"); continue
        storey_override = (neighbour_storeys.pop(), "INFERRED_TERRACE_NEIGHBOUR_STOREYS")
        row2, blocker2 = _gb_row_outcome(
            item, bool(is_attached_series.loc[idx]), records, first, age_label, period_provenance,
            cert_numbers_by_osm_id.get(building_id, []), storey_override=storey_override,
        )
        if row2 is None:
            exclusions.log(building_id, "recovery_pass", f"STOREY_RECOVERED_THEN_{blocker2}"); continue
        recovered.append(row2)

    return recovered, exclusions


def _it_rows(gdf: gpd.GeoDataFrame, records: list[dict]) -> tuple[list[dict], Counter]:
    """Map Bologna residential footprints to Italian TABULA archetypes via ISTAT 2011 census sections (D-EU-34)."""
    # 1. CTC eaves heights
    w, s, e, n = gdf.to_crs(4326).total_bounds
    url_ctc = "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/c_a944ctc_edifici_pl/exports/geojson"
    resp_ctc = requests.get(url_ctc, params={"limit": -1, "where": f"in_bbox(geo_shape, {s}, {w}, {n}, {e})"}, timeout=60)
    gdf_ctc = gpd.GeoDataFrame.from_features(resp_ctc.json()["features"], crs="EPSG:4326").to_crs(gdf.crs)
    ctc_joined = gpd.sjoin(gdf, gdf_ctc[["geometry", "altezza_gr"]], how="left", predicate="intersects")
    max_heights = ctc_joined.groupby("osm_id")["altezza_gr"].max()

    # 2. Footprint adjacency
    is_attached_series = compute_footprint_adjacency(gdf)

    # 3. ISTAT 2011 Census Section join
    zpath = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/dati-cpa_2011.zip"
    sections_data = {}
    with zipfile.ZipFile(zpath) as z:
        with z.open("Sezioni di Censimento/R08_indicatori_2011_sezioni.csv") as fh:
            rdr = csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";")
            for row in rdr:
                if (row.get("PROCOM") or "").strip() == "37006":
                    nsez = (row.get("NSEZ") or "").strip()
                    if nsez.isdigit():
                        sections_data[int(nsez)] = row

    url_sec = "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/sezioni-di-censimento-anno-2011/exports/geojson"
    resp_sec = requests.get(url_sec, params={"limit": -1}, timeout=60)
    gdf_sections = gpd.GeoDataFrame.from_features(resp_sec.json()["features"], crs="EPSG:4326").to_crs(gdf.crs)

    gdf_res_pts = gdf.copy()
    gdf_res_pts["geometry"] = gdf.geometry.centroid
    sec_joined = gpd.sjoin(gdf_res_pts, gdf_sections, how="left", predicate="within")

    ISTAT_TO_TABULA = {
        "E8": ("IT.01", 1900),
        "E9": ("IT.03", 1930),
        "E10": ("IT.04", 1950),
        "E11": ("IT.05", 1965),
        "E12": ("STRADDLE", None),
        "E13": ("IT.06", 1985),
        "E14": ("IT.07", 1995),
        "E15": ("IT.07", 2003),
        "E16": ("IT.08", 2010),
    }

    mapped_rows = []
    exclusions: Counter = _ExclusionCounter()

    for idx, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        bid = str(item.osm_id)

        # Height & Storeys
        h_val = max_heights.get(bid)
        if pd.isna(h_val) or h_val <= 0:
            h_m = 9.0
            storeys = 3
            h_source = "assumed 9.0 m"
        else:
            h_m = float(h_val)
            storeys = max(1, round(h_m / 3.0))
            h_source = "measured (c_a944ctc_edifici_pl)"

        # Building type
        is_att = bool(is_attached_series.loc[idx])
        if storeys <= 2:
            btype = "TH" if is_att else "SFH"
        elif storeys in (3, 4):
            btype = "MFH"
        else:
            btype = "AB"

        # Census section
        match_sec = sec_joined[sec_joined["osm_id"] == bid]
        if len(match_sec) == 0 or pd.isna(match_sec.iloc[0]["sez2011"]):
            exclusions.log(bid, "base_mapping", "UNMAPPED_CENSUS_SECTION")
            continue
        sez_num = int(match_sec.iloc[0]["sez2011"])
        sec_row = sections_data.get(sez_num)
        if not sec_row:
            exclusions.log(bid, "base_mapping", "CENSUS_SECTION_DATA_MISSING")
            continue

        e_counts = {f"E{k}": int(sec_row.get(f"E{k}", 0) or 0) for k in range(8, 17)}
        tot_res = sum(e_counts.values())
        if tot_res == 0:
            exclusions.log(bid, "base_mapping", "CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS")
            continue

        max_k = max(e_counts, key=e_counts.get)
        max_v = e_counts[max_k]
        ties = [k for k, v in e_counts.items() if v == max_v]
        if len(ties) > 1:
            # T06/c5 (D-EU-101): sections 1287 and 1266 are exact ties between two
            # adjacent bands (report §6) -- owner ruling breaks toward the older
            # cohort (smallest E-suffix, ISTAT_TO_TABULA is oldest-first).
            if sez_num in (1287, 1266):
                max_k = min(ties, key=lambda k: int(k[1:]))
            else:
                exclusions.log(bid, "base_mapping", f"CENSUS_SECTION_PERIOD_TIE_{'_'.join(ties)}")
                continue

        t_period, ref_year = ISTAT_TO_TABULA.get(max_k, (None, None))
        if t_period == "STRADDLE":
            exclusions.log(bid, "base_mapping", f"PERIOD_STRADDLE_{max_k}")
            continue
        if not t_period or not ref_year:
            exclusions.log(bid, "base_mapping", f"UNMAPPABLE_PERIOD_{max_k}")
            continue

        try:
            rec = select_tabula_archetype(records, "IT", btype, ref_year)
        except Exception as exc:
            exclusions.log(bid, "base_mapping", f"ARCHETYPE_RESOLUTION_FAILED_{exc}", detail=str(exc))
            continue

        mapped_rows.append({
            **item.to_dict(),
            "building_id": bid,
            "building_type": btype,
            "archetype_id": rec["archetype_id"],
            "age_band": t_period,
            "year_built": ref_year,
            "levels": storeys,
            "height_m": h_m,
            "height_source": h_source,
            "is_attached": is_att,
            "census_section": sez_num,
            "census_section_dominant_period": max_k,
            "construction_period_provenance": "IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD",
            "observed_dwellings": None,
        })
    return mapped_rows, exclusions


def _mapped_rows(district: str, gdf: gpd.GeoDataFrame, records: list[dict]) -> tuple[list[dict], Counter]:
    country = DISTRICTS[district]["country"]
    if district == "ES-MAD-BERRUGUETE":
        gdf = apply_attribute_sidecar(gdf, pd.read_csv(ES_SIDECAR))
        gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))
    if district == "FR-LYO-HAUTCOEURPENTES":
        gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))
    exclusions: Counter = _ExclusionCounter(); result = []
    for _, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        building_id = str(item.osm_id)
        decision = map_observed_building_to_tabula(item, neighbourhood_id=district, country_stock_code=country, records=records)
        if not decision.archetype_id:
            exclusions.log(building_id, "base_mapping", decision.reason or decision.mapping_status); continue
        if _valid_storeys(item) is None:
            exclusions.log(building_id, "base_mapping", "MISSING_OBSERVED_STOREY_COUNT"); continue
        record = next(x for x in records if x["archetype_id"] == decision.archetype_id)
        age = tabula_period(country, int(decision.year_built))
        result.append({**item.to_dict(), **asdict(decision), "building_id": str(item.osm_id),
                       "building_type": decision.building_type, "archetype_id": record["archetype_id"], "age_band": age})
    return result, exclusions


# ---------------------------------------------------------------------------
# T04 (`eu-recut-95pct-2026-09-08`, D-EU-112): neighbour imputation for the
# never-simulated. `_nearest_prepared_id` / `_neighbour_field_mode` /
# `_neighbour_ladder_value` are the shared rungs of dependency 3's ladder
# (touching -> nearest within 30 m -> district mode), generic over whichever
# field (period, storeys, typology) is being inherited. `_counter_from_records`
# keeps a Counter's histogram and its `.records` list built from the same
# rows, same discipline as T01's `_ExclusionCounter`.
# ---------------------------------------------------------------------------


def _counter_from_records(records: list[dict]) -> Counter:
    counter = _ExclusionCounter()
    for rec in records:
        counter[rec["blocker"]] += 1
    counter.records = list(records)
    return counter


def _nearest_prepared_id(
    geom: object, prepared_gdf: gpd.GeoDataFrame, max_distance_m: float = 30.0,
) -> tuple[str | None, float | None]:
    """Dependency 3 rung 2: the nearest already-prepared building within
    ``max_distance_m``, found through ``prepared_gdf``'s spatial index rather
    than an all-pairs distance scan."""
    if geom is None or len(prepared_gdf) == 0:
        return None, None
    candidate_pos = list(prepared_gdf.sindex.query(geom.buffer(max_distance_m), predicate="intersects"))
    if not candidate_pos:
        return None, None
    candidates = prepared_gdf.iloc[candidate_pos]
    distances = candidates.geometry.distance(geom)
    best = int(distances.values.argmin())
    best_distance = float(distances.iloc[best])
    if best_distance > max_distance_m:
        return None, None
    return str(candidates["osm_id"].iloc[best]), best_distance


def _neighbour_field_mode(rows: list[dict], field: str) -> tuple[dict[object, object], object | None]:
    """Dependency 3 rung 3: the district mode for ``field``, grouped by
    ``building_type`` (and, separately, over every type combined -- the "all
    types" fallback dependency 3 names for when the type itself is missing)."""
    per_type: dict[object, Counter] = {}
    overall: Counter = Counter()
    for row in rows:
        value = row.get(field)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        overall[value] += 1
        btype = row.get("building_type")
        if btype is not None:
            per_type.setdefault(btype, Counter())[value] += 1
    mode_by_type = {btype: counter.most_common(1)[0][0] for btype, counter in per_type.items()}
    mode_all = overall.most_common(1)[0][0] if overall else None
    return mode_by_type, mode_all


def _neighbour_ladder_value(
    building_id: str, pairs: dict[str, set[str]], base_ids: object, value_by_id: dict[str, object],
    nearest_by_id: dict[str, tuple[str | None, float | None]],
    mode_by_type: dict[object, object], mode_all: object | None, building_type: object | None,
) -> tuple[object | None, str]:
    """Dependency 3's three-rung ladder, generic over whichever field
    ``value_by_id`` carries."""
    touching = pairs.get(building_id, set()) & set(base_ids)
    touching_values = {value_by_id[nid] for nid in touching if nid in value_by_id}
    if len(touching_values) == 1:
        return touching_values.pop(), "IMPUTED_NEIGHBOUR_TOUCHING"
    nearest_id, nearest_distance = nearest_by_id.get(building_id, (None, None))
    if nearest_id is not None and nearest_id in value_by_id and nearest_distance is not None:
        return value_by_id[nearest_id], f"IMPUTED_NEIGHBOUR_NEAREST_{nearest_distance:.1f}M"
    mode = mode_by_type.get(building_type) if building_type is not None else None
    if mode is None:
        mode = mode_all
    if mode is not None:
        return mode, "IMPUTED_DISTRICT_MODE"
    return None, ""


def _gb_straddle_containment(
    candidate: str | None, tag: str, straddle_periods: tuple[str, str] | None,
) -> tuple[str | None, str]:
    """Dependency 3's GB straddle rule: an inherited period must lie inside the
    known ``(older, newer)`` straddle set (existing D-EU-108 f containment);
    when it does not, take the older band -- the same tie rule D-EU-101 c5
    uses for a Bologna census-section tie (`:599-600`, smallest suffix wins).
    """
    if candidate is None or straddle_periods is None or candidate in straddle_periods:
        return candidate, tag
    older = min(straddle_periods, key=lambda period: int(period.split(".")[-1]))
    return older, "IMPUTED_NEIGHBOUR_STRADDLE_OLDER_BAND"


def _gb_impute_rows(
    gdf: gpd.GeoDataFrame, records: list[dict], base_rows: list[dict],
) -> tuple[list[dict], Counter]:
    """GB already has a rung-1 (touching only) recovery pass,
    `_gb_terrace_recovery_rows` (`:410-501`), pinned byte-for-byte by
    `tests/test_eu_london_recovery_2026_09_07.py` -- left unmodified here.
    This calls it first, then extends whatever it still excluded with rungs 2
    (nearest within 30 m) and 3 (district mode), the D-EU-112 generalisation.
    """
    recovered, base_exclusions = _gb_terrace_recovery_rows(gdf, records, base_rows)
    for row in recovered:
        # `_gb_terrace_recovery_rows` only ever inherits from a touching
        # neighbour (rung 1) -- its legacy `INFERRED_TERRACE_NEIGHBOUR_*` tags
        # (kept unchanged in `construction_period_provenance`/`storey_provenance`
        # for regression safety) always correspond to that rung.
        row["imputation_provenance"] = "IMPUTED_NEIGHBOUR_TOUCHING"

    cert_numbers_by_osm_id, bands_all_by_osm_id, year_lookup = _gb_cert_lookups(gdf)
    is_attached_series = compute_footprint_adjacency(gdf)
    pairs = compute_footprint_adjacency_pairs(gdf)
    base_by_id = {str(r["building_id"]): r for r in base_rows}
    geom_by_id = {str(oid): geom for oid, geom in zip(gdf["osm_id"].astype(str), gdf.geometry)}
    base_gdf = gdf[gdf["osm_id"].astype(str).isin(base_by_id)]

    period_by_id: dict[str, str] = {}
    storeys_by_id: dict[str, int] = {}
    type_by_id: dict[str, str] = {}
    for bid, row in base_by_id.items():
        first, _label, _prov = _gb_age_decision_multi(bands_all_by_osm_id.get(bid, []), year_lookup.get(bid, set()))
        if first is not None:
            period_by_id[bid] = first
        storeys = _valid_storeys(pd.Series(row))
        if storeys is not None:
            storeys_by_id[bid] = storeys
        type_by_id[bid] = row.get("building_type")

    period_mode_by_type, period_mode_all = _neighbour_field_mode(
        [{"building_type": type_by_id.get(bid), "period": period} for bid, period in period_by_id.items()], "period",
    )
    storey_mode_by_type, storey_mode_all = _neighbour_field_mode(
        [{"building_type": type_by_id.get(bid), "storeys": storeys} for bid, storeys in storeys_by_id.items()], "storeys",
    )

    # `_gb_terrace_recovery_rows` only ever visits a building whose *own*
    # exclusion reason it independently recomputes as age-related (fact 6);
    # a building excluded for type/storeys alone, with a perfectly
    # resolvable period, is never reached by either of its two loops and
    # never logged -- silently dropped rather than imputed or excluded.
    # Measured on London: 135 of the 536 never-simulated fell through this
    # gap. This final pass is therefore independent of
    # `base_exclusions.records` -- it re-derives every remaining gdf row's
    # own period, then imputes period and/or storeys together as needed,
    # covering every excluded building exactly once.
    already_ids = set(base_by_id) | {str(r["building_id"]) for r in recovered}
    extra_recovered: list[dict] = []
    extra_records: list[dict] = []

    for idx, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        bid = str(item.osm_id)
        if bid in already_ids:
            continue
        first, age_label, period_provenance = _gb_age_decision_multi(
            bands_all_by_osm_id.get(bid, []), year_lookup.get(bid, set())
        )
        period_tag = ""
        if first is None:
            nearest_by_id_single = {bid: _nearest_prepared_id(geom_by_id.get(bid), base_gdf)}
            candidate, period_tag = _neighbour_ladder_value(
                bid, pairs, base_by_id.keys(), period_by_id, nearest_by_id_single,
                period_mode_by_type, period_mode_all, None,
            )
            if candidate is None:
                extra_records.append({"building_id": bid, "stage": "recovery_pass_extended", "blocker": f"{age_label}_NO_LADDER_VALUE", "detail": ""})
                continue
            straddle_periods = _gb_parse_straddle_periods(age_label)
            candidate, period_tag = _gb_straddle_containment(candidate, period_tag, straddle_periods)
            first, age_label, period_provenance = candidate, "", period_tag

        storey_override = None
        storey_tag = ""
        if _valid_storeys(item) is None:
            nearest_by_id_single = {bid: _nearest_prepared_id(geom_by_id.get(bid), base_gdf)}
            storeys_val, storey_tag = _neighbour_ladder_value(
                bid, pairs, base_by_id.keys(), storeys_by_id, nearest_by_id_single,
                storey_mode_by_type, storey_mode_all, None,
            )
            if storeys_val is None:
                extra_records.append({"building_id": bid, "stage": "recovery_pass_extended", "blocker": "MISSING_OBSERVED_STOREY_COUNT_NO_LADDER_VALUE", "detail": ""})
                continue
            storey_override = (int(storeys_val), storey_tag)

        row, blocker2 = _gb_row_outcome(
            item, bool(is_attached_series.loc[idx]), records, first, age_label, period_provenance or period_tag,
            cert_numbers_by_osm_id.get(bid, []), storey_override=storey_override,
        )
        if row is None:
            extra_records.append({"building_id": bid, "stage": "recovery_pass_extended", "blocker": f"IMPUTED_THEN_{blocker2}", "detail": ""})
            continue
        tags = [t for t in (period_tag, storey_tag) if t]
        row["imputation_provenance"] = "+".join(tags)
        extra_recovered.append(row)

    resolved_ids = {str(r["building_id"]) for r in extra_recovered}
    combined_records = [rec for rec in base_exclusions.records if rec["building_id"] not in resolved_ids] + extra_records
    return recovered + extra_recovered, _counter_from_records(combined_records)


def _impute_es_fr_rows(
    district: str, gdf: gpd.GeoDataFrame, records: list[dict], base_rows: list[dict],
) -> tuple[list[dict], Counter]:
    """ES/FR base mapping (`_mapped_rows`) runs through
    `map_observed_building_to_tabula`, which requires `provenance_year_built`
    to end `_OBSERVED` (fully evidenced only) and is never edited or fed a
    fabricated observation. This calls it once, read-only, on the *original*
    row to learn which field(s) are missing, imputes only those from
    `base_rows` neighbours, and resolves the archetype directly through
    `select_tabula_archetype` -- the same function `map_observed_building_to_tabula`
    itself calls internally -- bypassing the observed-only gate for these rows.
    """
    country = DISTRICTS[district]["country"]
    base_by_id = {str(r["building_id"]): r for r in base_rows}
    pairs = compute_footprint_adjacency_pairs(gdf)
    geom_by_id = {str(oid): geom for oid, geom in zip(gdf["osm_id"].astype(str), gdf.geometry)}
    base_gdf = gdf[gdf["osm_id"].astype(str).isin(base_by_id)]

    type_by_id: dict[str, str] = {str(r["building_id"]): r.get("building_type") for r in base_rows}
    year_by_id: dict[str, int] = {
        str(r["building_id"]): r["year_built"] for r in base_rows if pd.notna(r.get("year_built"))
    }
    storeys_by_id: dict[str, int] = {}
    for r in base_rows:
        storeys = _valid_storeys(pd.Series(r))
        if storeys is not None:
            storeys_by_id[str(r["building_id"])] = storeys

    year_mode_by_type, year_mode_all = _neighbour_field_mode(
        [{"building_type": type_by_id.get(bid), "year_built": year} for bid, year in year_by_id.items()], "year_built",
    )
    type_mode_by_type, type_mode_all = _neighbour_field_mode(
        [{"building_type": None, "type_only": t} for t in type_by_id.values() if t], "type_only",
    )
    storey_mode_by_type, storey_mode_all = _neighbour_field_mode(
        [{"building_type": type_by_id.get(bid), "storeys": s} for bid, s in storeys_by_id.items()], "storeys",
    )

    recovered: list[dict] = []
    excluded_records: list[dict] = []
    for _, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        building_id = str(item.osm_id)
        if building_id in base_by_id:
            continue
        decision = map_observed_building_to_tabula(
            item, neighbourhood_id=district, country_stock_code=country, records=records,
        )
        needs_type = decision.building_type is None
        needs_year = decision.year_built is None
        needs_storeys = _valid_storeys(item) is None
        if not (needs_type or needs_year or needs_storeys):
            continue
        base_blocker = decision.reason or decision.mapping_status or "MAPPING_INCOMPLETE"
        nearest_by_id_single = {building_id: _nearest_prepared_id(geom_by_id.get(building_id), base_gdf)}
        type_tag = year_tag = storey_tag = ""
        final_type = decision.building_type
        if needs_type:
            final_type, type_tag = _neighbour_ladder_value(
                building_id, pairs, base_by_id.keys(), type_by_id, nearest_by_id_single,
                {}, type_mode_all, None,
            )
            if final_type is None:
                excluded_records.append({"building_id": building_id, "stage": "recovery_pass", "blocker": f"{base_blocker}_NO_LADDER_VALUE", "detail": ""})
                continue
        final_year = decision.year_built
        if needs_year:
            final_year, year_tag = _neighbour_ladder_value(
                building_id, pairs, base_by_id.keys(), year_by_id, nearest_by_id_single,
                year_mode_by_type, year_mode_all, final_type,
            )
            if final_year is None:
                excluded_records.append({"building_id": building_id, "stage": "recovery_pass", "blocker": "MISSING_OBSERVED_YEAR_BUILT_NO_LADDER_VALUE", "detail": ""})
                continue
        final_storeys = _valid_storeys(item)
        if needs_storeys:
            final_storeys, storey_tag = _neighbour_ladder_value(
                building_id, pairs, base_by_id.keys(), storeys_by_id, nearest_by_id_single,
                storey_mode_by_type, storey_mode_all, final_type,
            )
            if final_storeys is None:
                excluded_records.append({"building_id": building_id, "stage": "recovery_pass", "blocker": "MISSING_OBSERVED_STOREY_COUNT_NO_LADDER_VALUE", "detail": ""})
                continue
        try:
            archetype = select_tabula_archetype(records, country, final_type, int(final_year))
        except ValueError as error:
            excluded_records.append({"building_id": building_id, "stage": "recovery_pass", "blocker": f"IMPUTED_ARCHETYPE_RESOLUTION_FAILED_{type(error).__name__}", "detail": str(error)})
            continue
        age = tabula_period(country, int(final_year))
        imputation_provenance = "+".join(tag for tag in (type_tag, year_tag, storey_tag) if tag)
        row = {
            **item.to_dict(), "building_id": building_id, "building_type": final_type,
            "archetype_id": archetype["archetype_id"], "age_band": age, "year_built": int(final_year),
            "levels": final_storeys, "observed_dwellings": item.get("observed_dwellings"),
            "construction_period_provenance": year_tag, "storey_provenance": storey_tag,
            "imputation_provenance": imputation_provenance,
        }
        recovered.append(row)
    return recovered, _counter_from_records(excluded_records)


def _impute_it_rows(
    gdf: gpd.GeoDataFrame, records: list[dict], base_rows: list[dict],
) -> tuple[list[dict], Counter]:
    """Bologna's own base mapping (`_it_rows`) never excludes a building for
    its type or storey count -- a missing CTC eaves-height measurement already
    falls back to an assumed 9.0 m / 3-storey default (`:557-560`), so type and
    storeys are always resolvable. Only the census-section construction period
    ever excludes (dependency 3's field list names only
    `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` for IT). This reuses that same
    already-declared default rather than a second live CTC/census HTTP round
    trip for the handful of never-simulated Bologna buildings, and imputes
    only the period.
    """
    base_by_id = {str(r["building_id"]): r for r in base_rows}
    pairs = compute_footprint_adjacency_pairs(gdf)
    geom_by_id = {str(oid): geom for oid, geom in zip(gdf["osm_id"].astype(str), gdf.geometry)}
    base_gdf = gdf[gdf["osm_id"].astype(str).isin(base_by_id)]
    is_attached_series = compute_footprint_adjacency(gdf)

    type_by_id: dict[str, str] = {str(r["building_id"]): r.get("building_type") for r in base_rows}
    year_by_id: dict[str, int] = {
        str(r["building_id"]): r["year_built"] for r in base_rows if pd.notna(r.get("year_built"))
    }
    year_mode_by_type, year_mode_all = _neighbour_field_mode(
        [{"building_type": type_by_id.get(bid), "year_built": year} for bid, year in year_by_id.items()], "year_built",
    )

    recovered: list[dict] = []
    excluded_records: list[dict] = []
    for idx, item in gdf.sort_values("osm_id", kind="stable").iterrows():
        bid = str(item.osm_id)
        if bid in base_by_id:
            continue
        # Same storeys<=2/3-4/>=5 -> SFH-or-TH/MFH/AB ladder `_it_rows` uses
        # (`:568-573`); the assumed-height default always lands on storeys=3.
        storeys = 3
        btype = "MFH"
        nearest_by_id_single = {bid: _nearest_prepared_id(geom_by_id.get(bid), base_gdf)}
        final_year, tag = _neighbour_ladder_value(
            bid, pairs, base_by_id.keys(), year_by_id, nearest_by_id_single,
            year_mode_by_type, year_mode_all, btype,
        )
        if final_year is None:
            excluded_records.append({"building_id": bid, "stage": "recovery_pass", "blocker": "CENSUS_SECTION_PERIOD_NO_LADDER_VALUE", "detail": ""})
            continue
        try:
            archetype = select_tabula_archetype(records, "IT", btype, int(final_year))
        except ValueError as error:
            excluded_records.append({"building_id": bid, "stage": "recovery_pass", "blocker": f"IMPUTED_ARCHETYPE_RESOLUTION_FAILED_{type(error).__name__}", "detail": str(error)})
            continue
        age = tabula_period("IT", int(final_year))
        row = {
            **item.to_dict(), "building_id": bid, "building_type": btype,
            "archetype_id": archetype["archetype_id"], "age_band": age, "year_built": int(final_year),
            "levels": storeys, "height_m": None, "height_source": "assumed 9.0 m (impute_from_neighbours, no second CTC round trip)",
            "is_attached": bool(is_attached_series.loc[idx]), "observed_dwellings": None,
            "construction_period_provenance": tag, "storey_provenance": "",
            "imputation_provenance": tag,
        }
        recovered.append(row)
    return recovered, _counter_from_records(excluded_records)


def impute_from_neighbours(
    gdf: gpd.GeoDataFrame, base_rows: list[dict], records: list[dict], district: str,
) -> tuple[list[dict], Counter]:
    """T04 (D-EU-112): a building the base mapping excluded only for a missing
    construction period, storey count, dwelling count or typology inherits it
    from its prepared neighbours -- touching (rung 1), else the nearest
    prepared building within 30 m (rung 2), else the district mode for its
    type (rung 3) -- and enters the campaign, provenance-tagged
    `IMPUTED_NEIGHBOUR_*` / `IMPUTED_DISTRICT_MODE`. Dwelling count is not
    imputed here: a building with a known type/period/storeys but no observed
    dwelling count already enters `_mapped_rows`/`_gb_rows`/`_it_rows` and gets
    its unit count from the existing `_geometry` imputation
    (`..._IMPUTED_COUNT`), unchanged by this function.
    """
    if district == "GB-LDN-STDUNSTANS":
        return _gb_impute_rows(gdf, records, base_rows)
    if district == "IT-BOL-GALVANI2":
        return _impute_it_rows(gdf, records, base_rows)
    return _impute_es_fr_rows(district, gdf, records, base_rows)


def prepare(
    district: str, archetypes: Path | None, epw: Path | None, crs: str | None, out: Path,
    # T04 (D-EU-112): named `impute_from_neighbours_enabled`, not
    # `impute_from_neighbours`, so this local parameter never shadows the
    # module-level `impute_from_neighbours` function called below.
    impute_from_neighbours_enabled: bool = True,
) -> dict:
    cfg = DISTRICTS[district]; expected_crs = crs or cfg["crs"]
    manifest = ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    if str(gdf.crs) != expected_crs:
        raise ValueError(f"Manifest CRS is {gdf.crs}, expected {expected_crs}; native coordinates are required")
    weather, weather_sha = _registry_weather(cfg["fold"], epw)
    records = json.loads((archetypes or (ROOT / f"openubem/data/construction/tabula_archetypes_{cfg['country'].lower()}.json")).read_text(encoding="utf-8"))["records"]
    if district == "GB-LDN-STDUNSTANS": rows, exclusions = _gb_rows(gdf, records)
    elif district == "IT-BOL-GALVANI2": rows, exclusions = _it_rows(gdf, records)
    else: rows, exclusions = _mapped_rows(district, gdf, records)
    out = out.resolve(); idfs = out / "idfs"; weather_dir = out / "weather"; schedules = out / "schedules"; idfs.mkdir(parents=True, exist_ok=True); weather_dir.mkdir(exist_ok=True); schedules.mkdir(exist_ok=True)
    shutil.copy2(weather, weather_dir / weather.name)
    # D-EU-40 R2-R5 / EU-16 T06: context = every building in the district's own
    # 01_buildings_clean.gpkg superset within 20 m of the target, never the
    # residential manifest alone (R3). Loaded once per district, reused per
    # building. District median residential height (R4's last fallback tier)
    # is measured over `rows` -- the district's own simulated residential
    # population -- before any per-building work starts.
    buildings_clean = gpd.read_file(ROOT / f"openubem/outputs/eu02/{district}/01_buildings_clean.gpkg")
    district_median_height_m = compute_district_median_residential_height_m(rows)
    # T04 (D-EU-112): district-agnostic, default on -- replaces the GB-only
    # `recover_terrace_neighbours` gate (fact 6: `_gb_terrace_recovery_rows`
    # implemented rung 1 for GB only; this runs the full three-rung ladder for
    # all four districts).
    imputation_summary: dict = {}
    imputation_records: list[dict] = []
    imputation_exclusions_counter: Counter = Counter()
    if impute_from_neighbours_enabled:
        recovered_rows, imputation_exclusions = impute_from_neighbours(gdf, rows, records, district)
        imputation_exclusions_counter = imputation_exclusions
        rows = rows + recovered_rows
        imputation_summary = {
            "recovered": len(recovered_rows),
            "refused": dict(sorted(imputation_exclusions.items())),
        }
        imputation_records = imputation_exclusions.records
    context_height_fallback_census: Counter = Counter()
    prepared, geometry_exclusions = [], _ExclusionCounter()
    for data in rows:
        row = pd.Series(data)
        try:
            # OSM identifiers include '/', while EnergyPlus object and Windows
            # path names must not.  Keep the original id only in the manifest.
            stem = hashlib.sha256(str(row.building_id).encode()).hexdigest()[:16]
            model_row = row.copy()
            model_row["building_id"] = stem
            zones, outcome = _geometry(model_row, records)
            layout_reason = outcome.layout_reason
            context = build_european_context(
                row.osm_id, row.geometry, buildings_clean, district_median_height_m,
                context_height_fallback_census,
            )
            run_dir = idfs / stem
            path = build_idf_for_building(
                model_row, next(x for x in records if x["archetype_id"] == row.archetype_id), zones, run_dir,
                epw_path=weather, context=context,
            )
            # FINDING 210 residual fix (2026-08-31): build_idf_for_building can
            # silently reroute `zones` in place to one_zone_per_floor when
            # geomeppy's intersect_match leaves an unresolved interzone vertex
            # mismatch. Disclose that here rather than leave `outcome` stale.
            if any(z.get("generation_status_note") == "room_layout_intersect_fallback" for z in zones):
                outcome = "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"
            # T15 (D-EU-58): scripts/run_eu_s2_campaign.py's post-extrude at-risk gate
            # tags every zone with `fallback_reason` when it retains an already-emitted
            # geometry instead of raising. Surface it as its own manifest column so it
            # is auditable (never folded into `geometry_outcome`, which keeps its
            # existing meaning unchanged).
            fallback_reason = next((z["fallback_reason"] for z in zones if z.get("fallback_reason")), "") or (layout_reason or "")
            # The accepted S2 emitter uses absolute Schedule:File paths.  Copy
            # the byte-identical schedules into the fleet and retarget only the
            # path to a POSIX-relative location visible from out/<stem>.
            schedule_dir = schedules / stem; schedule_dir.mkdir()
            text = path.read_text(encoding="utf-8")
            for gain in run_dir.glob("*_gain.csv"):
                text = text.replace(str(gain.resolve()), f"../../schedules/{stem}/{gain.name}")
                shutil.move(gain, schedule_dir / gain.name)
            path.write_text(text, encoding="utf-8")
            target = idfs / f"{stem}.idf"
            shutil.move(path, target); shutil.rmtree(run_dir)
            # D-EU-39 §3 / EU-15 T05: circulation zones are tagged
            # conditioned=False by european_building_layout_to_zone_specs;
            # every other zone (including every one_zone_per_floor fallback
            # zone, which carries no core) defaults to conditioned.
            gross_footprint_area_m2 = round(sum(float(z["floor_polygon"].area) for z in zones), 4)
            conditioned_floor_area_m2 = round(
                sum(float(z["floor_polygon"].area) for z in zones if z.get("conditioned") is not False), 4
            )
            prepared.append({"building_id": row.building_id, "stem": target.stem, "archetype_id": row.archetype_id,
                             "building_type": row.building_type, "age_band": row.age_band, "geometry_outcome": outcome,
                             "idf_sha256": sha256_file(target), "weather_sha256": weather_sha,
                             "construction_period_provenance": row.get("construction_period_provenance", ""),
                             "storey_provenance": row.get("storey_provenance", ""),
                             # T04 (D-EU-112): empty string for every observed row -- only a
                             # row `impute_from_neighbours` built carries this key at all.
                             "imputation_provenance": row.get("imputation_provenance", ""),
                             "floor_area_m2": gross_footprint_area_m2,
                             "gross_footprint_area_m2": gross_footprint_area_m2,
                             "conditioned_floor_area_m2": conditioned_floor_area_m2,
                             # T11 / FINDING 214 / D-EU-39 §3: the EUI denominator moves to the
                             # conditioned area. floor_area_m2 above keeps its existing (gross)
                             # meaning unchanged; this is a new, additional column only. No EUI
                             # is computed or recomputed here (D-EU-55: nothing simulates).
                             "eui_denominator_m2": conditioned_floor_area_m2,
                             "context_building_count": len(context),
                             "fallback_reason": fallback_reason})
        except ValueError as exc:
            geometry_exclusions.log(row.building_id, "idf_build", str(exc))
        except (RuntimeError, ZeroDivisionError, IndexError) as exc:
            # EU-13B T09: geomeppy's intersect_match can still fail numerically on a
            # live noisy footprint even after both reroute safety nets in
            # openubem/idf/surfaces.py give up (e.g. a degenerate zero-length edge
            # surviving the ruled-grid partition). Fail this one building closed
            # rather than aborting the whole district's regeneration.
            geometry_exclusions.log(
                row.building_id, "idf_build", f"IDF_ASSEMBLY_FAILED_{type(exc).__name__}", detail=str(exc)
            )
    pd.DataFrame(prepared).to_csv(out / "prepared_buildings.csv", index=False)
    # T10 / dependency decision §4.8: "That script builds IDFs and a manifest
    # and does not simulate." EU-11's <slug>_manifest.csv is written post-hoc
    # by the Speed harvest (scripts/cluster/harvest_eu11_district.py) once
    # eplus_return_code/heating_kwh/etc. are known; a fresh EU-17 rebuild is
    # never simulated (D-EU-55), so those columns are written blank here --
    # same manifest layout as EU-11 (same filename, same MANIFEST_COLUMNS),
    # so scripts.eu_idf_plan_reader.read_district (which reads
    # geometry_outcome from this file, not from prepared_buildings.csv) and
    # scripts.emit_eu11_layout_sidecars work unmodified against this tree.
    manifest_slug = district.lower().replace("-", "_") + "_manifest.csv"
    manifest_rows = [
        {col: p.get(col, pd.NA) for col in MANIFEST_COLUMNS}
        for p in prepared
    ]
    pd.DataFrame(manifest_rows, columns=MANIFEST_COLUMNS).to_csv(out / manifest_slug, index=False)
    with (out / "fleet.lst").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(x["stem"] for x in prepared) + ("\n" if prepared else ""))
    summary = {"district": district, "population_attempted": len(gdf), "population_prepared": len(prepared),
               "blocker_exclusions": dict(sorted((exclusions + geometry_exclusions + imputation_exclusions_counter).items())),
               "epw": str(weather.relative_to(ROOT)).replace("\\", "/"), "weather_sha256": weather_sha,
               "status": "PREPARED_FOR_SPEED", "platform": "Speed (not yet run)", "energyplus_version": "not yet measured",
               "context_radius_m": EUROPEAN_CONTEXT_RADIUS_M,
               "context_district_median_residential_height_m": round(district_median_height_m, 4),
               "context_height_fallback_census": dict(sorted(context_height_fallback_census.items()))}
    if impute_from_neighbours_enabled:
        summary["imputation_summary"] = imputation_summary
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # T01: one row per excluded building across every stage (`:348, :397-449,
    # :529-567, :596-...` fact 5, `:716` IDF build) -- the reasons the base
    # mapping, the recovery pass and the IDF build already compute and,
    # until now, only ever threw away into a bare count. T04: buildings
    # `impute_from_neighbours` still could not resolve (no touching/nearest/
    # mode value found, or a re-resolved archetype still failed) stay excluded
    # here too -- dependency decision 5's "excluded_buildings.csv must still
    # correctly record what remains excluded and why" after this change.
    excluded_records = list(exclusions.records) + imputation_records + list(geometry_exclusions.records)
    pd.DataFrame(
        excluded_records, columns=["building_id", "stage", "blocker", "detail"]
    ).to_csv(out / "excluded_buildings.csv", index=False)
    return summary


def compute_recut_simulate_list(
    out: Path, district: str, evidence_root: Path = EVIDENCE,
    baseline_tags: tuple[str, ...] = ("delta_2026-09-07", "final_2026-09-07"),
) -> dict:
    """T05 / dependency decision 5: ``recut_simulate_list.csv`` = every
    building in ``out/prepared_buildings.csv`` whose ``idf_sha256`` differs
    from the newest earlier tree that holds it (``_delta_2026-09-07`` first,
    else ``_final_2026-09-07``), plus buildings with no earlier IDF at all.
    Rewrites ``fleet.lst`` to that restricted list -- only those buildings
    reach Speed (T06).
    """
    out = out.resolve()
    recut = pd.read_csv(out / "prepared_buildings.csv", dtype={"building_id": str})
    baseline_dir = None
    baseline_tag = None
    for tag in baseline_tags:
        candidate = evidence_root / f"{district}_{tag}" / "prepared_buildings.csv"
        if candidate.exists():
            baseline_dir = candidate
            baseline_tag = tag
            break
    if baseline_dir is None:
        raise FileNotFoundError(
            f"No baseline tree found for {district} among {baseline_tags} under {evidence_root}"
        )
    baseline = pd.read_csv(baseline_dir, dtype={"building_id": str})
    baseline_hash = dict(zip(baseline["building_id"], baseline["idf_sha256"]))
    rows = []
    for _, row in recut.iterrows():
        bid = row["building_id"]
        if bid not in baseline_hash:
            rows.append({"building_id": bid, "stem": row["stem"], "reason": "NET_NEW"})
        elif baseline_hash[bid] != row["idf_sha256"]:
            rows.append({"building_id": bid, "stem": row["stem"], "reason": "HASH_CHANGED"})
    simulate = pd.DataFrame(rows, columns=["building_id", "stem", "reason"])
    simulate.to_csv(out / "recut_simulate_list.csv", index=False)
    with (out / "fleet.lst").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(simulate["stem"]) + ("\n" if len(simulate) else ""))
    return {
        "district": district, "baseline_tag": baseline_tag,
        "n_prepared": len(recut), "n_simulate": len(simulate),
        "n_hash_changed": int((simulate["reason"] == "HASH_CHANGED").sum()) if len(simulate) else 0,
        "n_net_new": int((simulate["reason"] == "NET_NEW").sum()) if len(simulate) else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", choices=DISTRICTS, required=True)
    parser.add_argument("--archetypes", type=Path); parser.add_argument("--epw", type=Path); parser.add_argument("--crs")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--impute-from-neighbours", dest="impute_from_neighbours", action=argparse.BooleanOptionalAction, default=True,
    )
    parser.add_argument(
        "--write-recut-simulate-list", dest="write_recut_simulate_list", action="store_true", default=False,
        help="T05 / dependency decision 5: after prepare(), compute recut_simulate_list.csv "
             "against the newest earlier tree (_delta_2026-09-07 first, else _final_2026-09-07) "
             "and restrict fleet.lst to it.",
    )
    args = parser.parse_args()
    result = prepare(args.district, args.archetypes, args.epw, args.crs, args.out, args.impute_from_neighbours)
    if args.write_recut_simulate_list:
        result["recut_simulate_list"] = compute_recut_simulate_list(args.out, args.district)
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
