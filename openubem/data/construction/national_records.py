from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

from openubem.data.construction.tabula_registry import (
    ATTRIBUTION,
    _write_json,
    generate_country_registry,
)


DATA_DIR = Path(__file__).parent
DEFAULT_WORKBOOK = Path(
    "C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ/Step8_docs/outputs_step8/raw/tabula-calculator.xlsx"
)
NATIONAL_ATTRIBUTION = ATTRIBUTION + "; national sources per parameter_assumptions"

ALLOWED_KEYS = (
    "u_wall_w_m2k",
    "u_roof_w_m2k",
    "u_floor_w_m2k",
    "u_window_w_m2k",
    "g_gl_window",
    "delta_u_tb_w_m2k",
    "n_air_infiltration_h_1",
    "wwr",
    "mean_flat_area_m2",
)

_ENVELOPE_GROUPS = {
    "wall": ("a_wall_components_m2", "wall", 3, "u_wall_w_m2k"),
    "roof": ("a_roof_components_m2", "roof", 2, "u_roof_w_m2k"),
    "floor": ("a_floor_components_m2", "floor", 2, "u_floor_w_m2k"),
    "window": ("a_window_components_m2", "window", 2, "u_window_w_m2k"),
}
_OVERRIDE_TO_GROUP = {value[3]: key for key, value in _ENVELOPE_GROUPS.items()}
_RESISTANCE_EPS = 1e-6


def _slots() -> list[tuple[str, str, int]]:
    return [
        (f"{group}_{index}", group, index - 1)
        for group, (_, _, count, _) in _ENVELOPE_GROUPS.items()
        for index in range(1, count + 1)
    ]


def _b_factor(record: Mapping[str, Any], slot: str) -> float:
    if slot.startswith("window"):
        return 1.0
    return float(record["transmission_b_factors"][slot])


def _extra_resistance(area: float, b: float, u0: float, h0: float) -> float:
    return b * area / h0 - 1.0 / u0


def rescale_transmission(
    record: dict[str, Any],
    new_u: Mapping[str, float] | None = None,
    new_areas: Mapping[str, float] | None = None,
    tb_factor: float | None = None,
) -> list[str]:
    new_u = dict(new_u or {})
    new_areas = dict(new_areas or {})
    geometry = record["geometry"]
    parts = record["h_transmission_components_w_k"]
    u_old = record["u_components_w_m2k"]
    fallbacks: list[str] = []
    updated_parts: dict[str, float] = {}
    for slot, group, position in _slots():
        area_key, u_key, _, _ = _ENVELOPE_GROUPS[group]
        area0 = float(geometry[area_key][position])
        u0 = float(u_old[u_key][position])
        h0 = float(parts[slot])
        area1 = float(new_areas.get(slot, area0))
        u1 = float(new_u.get(slot, u0))
        if area0 == 0.0 or h0 == 0.0:
            updated_parts[slot] = h0
            continue
        b = _b_factor(record, slot)
        if u0 <= 0.0:
            updated_parts[slot] = h0 * (area1 / area0)
            fallbacks.append(f"RATIO_FALLBACK: {slot}")
            continue
        resistance = _extra_resistance(area0, b, u0, h0)
        if u1 <= 0.0 or resistance < -_RESISTANCE_EPS or 1.0 / u1 + resistance <= 0.0:
            updated_parts[slot] = h0 * (u1 * area1) / (u0 * area0)
            fallbacks.append(f"RATIO_FALLBACK: {slot}")
        else:
            updated_parts[slot] = b * area1 / (1.0 / u1 + resistance)
    for slot, value in updated_parts.items():
        parts[slot] = value
    if tb_factor is not None:
        parts["thermal_bridging"] = float(parts["thermal_bridging"]) * tb_factor
    a_ref = float(geometry["a_c_ref_m2"])
    record["h_transmission_w_m2k"] = sum(float(value) for value in parts.values()) / a_ref
    return fallbacks


def _validate_spec(spec: Mapping[str, Any]) -> None:
    for key in ("country", "fold", "donor_country", "periods", "entries"):
        if key not in spec:
            raise ValueError(f"Spec lacks key {key!r}")
    period_codes = set()
    for period in spec["periods"]:
        if not {"code", "from", "to"} <= set(period):
            raise ValueError(f"Period needs code, from, to: {period}")
        period_codes.add(period["code"])
    for entry in spec["entries"]:
        for key in ("building_type", "period", "donor_archetype_id", "values"):
            if key not in entry:
                raise ValueError(f"Entry lacks key {key!r}: {entry}")
        if entry["period"] not in period_codes:
            raise ValueError(f"Entry period {entry['period']} is not declared in periods")
        for key, item in entry["values"].items():
            if key not in ALLOWED_KEYS:
                raise ValueError(f"Override key {key!r} is not allowed; allowed: {ALLOWED_KEYS}")
            if not isinstance(item, Mapping) or "value" not in item:
                raise ValueError(f"Override {key!r} must be an object with value and source")
            source = item.get("source")
            if not isinstance(source, str) or not source.strip():
                raise ValueError(f"Override {key!r} has neither a source nor an ASSUMED tag")
            float(item["value"])


def _load_donor_records(
    donor_country: str,
    workbook: Path | None,
    donor_dir: Path | None,
) -> dict[str, dict[str, Any]]:
    path = Path(donor_dir or DATA_DIR) / f"tabula_archetypes_{donor_country.lower()}.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        source = Path(workbook or DEFAULT_WORKBOOK)
        with tempfile.TemporaryDirectory() as temporary:
            generated = generate_country_registry(donor_country, source, Path(temporary))
            payload = json.loads(generated.read_text(encoding="utf-8"))
    return {record["archetype_id"]: record for record in payload["records"]}


def _find_donor(donors: Mapping[str, dict[str, Any]], donor_id: str) -> dict[str, Any]:
    if donor_id in donors:
        return donors[donor_id]
    matches = [
        record
        for record in donors.values()
        if record.get("source_building_type_code") == donor_id
        or record.get("source_building_code") == donor_id
        or record["archetype_id"].startswith(donor_id + ".")
    ]
    if len(matches) != 1:
        raise ValueError(f"Donor {donor_id!r} matches {len(matches)} records")
    return matches[0]


def _apply_wwr(record: dict[str, Any], wwr: float) -> dict[str, float]:
    geometry = record["geometry"]
    windows = [float(value) for value in geometry["a_window_components_m2"]]
    walls = [float(value) for value in geometry["a_wall_components_m2"]]
    window_total = sum(windows)
    wall_total = sum(walls)
    if window_total <= 0 or wall_total <= 0:
        raise ValueError(f"{record['archetype_id']}: wwr rescale needs non-zero window and wall areas")
    if not 0.0 < wwr < 1.0:
        raise ValueError(f"wwr must lie in (0, 1), got {wwr}")
    total = window_total + wall_total
    window_factor = wwr * total / window_total
    wall_factor = (1.0 - wwr) * total / wall_total
    geometry["a_window_components_m2"] = [value * window_factor for value in windows]
    geometry["a_wall_components_m2"] = [value * wall_factor for value in walls]
    geometry["a_window_by_orientation_m2"] = {
        key: float(value) * window_factor for key, value in geometry["a_window_by_orientation_m2"].items()
    }
    areas = {f"window_{i + 1}": geometry["a_window_components_m2"][i] for i in range(2)}
    areas.update({f"wall_{i + 1}": geometry["a_wall_components_m2"][i] for i in range(3)})
    return areas


def _weighted(areas: list[float], u_values: list[float]) -> float | None:
    pairs = [(a, u) for a, u in zip(areas, u_values) if a > 0]
    if not pairs:
        return None
    return sum(a * u for a, u in pairs) / sum(a for a, _ in pairs)


def _build_record(donor: dict[str, Any], spec: Mapping[str, Any], entry: Mapping[str, Any]) -> dict[str, Any]:
    record = copy.deepcopy(donor)
    donor_id = donor["archetype_id"]
    country = spec["country"].upper()
    building_type = entry["building_type"]
    suffix = entry["period"].split(".")[-1]
    archetype_id = f"{country}.N.{building_type}.{suffix}.Gen.ReEx.001.001"
    values = {key: float(item["value"]) for key, item in entry["values"].items()}

    record["archetype_id"] = archetype_id
    record["source_row"] = archetype_id
    record["source_building_code"] = f"{country}.N.{building_type}.{suffix}.Gen.ReEx.001"
    record["source_building_type_code"] = f"{country}.N.{building_type}.{suffix}.Gen"
    record["country_stock_code"] = country
    record["survey_fold"] = spec["fold"]
    record["building_type"] = building_type
    record["construction_period"] = entry["period"]
    record["attribution"] = NATIONAL_ATTRIBUTION
    record["license"] = {"status": record["license"]["status"], "attribution": NATIONAL_ATTRIBUTION}

    new_areas: dict[str, float] = {}
    if "wwr" in values:
        new_areas = _apply_wwr(record, values["wwr"])

    new_u: dict[str, float] = {}
    pending_u: list[tuple[list[float], int, float]] = []
    geometry = record["geometry"]
    for key, group in _OVERRIDE_TO_GROUP.items():
        if key not in values:
            continue
        area_key, u_key, count, _ = _ENVELOPE_GROUPS[group]
        components = record["u_components_w_m2k"][u_key]
        for index in range(count):
            if float(geometry[area_key][index]) > 0.0:
                new_u[f"{group}_{index + 1}"] = values[key]
                pending_u.append((components, index, values[key]))

    tb_factor = None
    if "delta_u_tb_w_m2k" in values:
        old = float(donor["delta_u_tb_w_m2k"])
        if old > 0.0:
            tb_factor = values["delta_u_tb_w_m2k"] / old
        elif values["delta_u_tb_w_m2k"] != 0.0:
            raise ValueError(f"{donor_id}: donor delta_u_tb is 0, cannot rescale to {values['delta_u_tb_w_m2k']}")
        record["delta_u_tb_w_m2k"] = values["delta_u_tb_w_m2k"]

    touches_transmission = bool(new_u or new_areas or tb_factor is not None)
    fallbacks: list[str] = []
    if touches_transmission:
        fallbacks = rescale_transmission(record, new_u, new_areas, tb_factor)
    for components, index, value in pending_u:
        components[index] = value

    for key, group in _OVERRIDE_TO_GROUP.items():
        if key in values:
            area_key, u_key, _, _ = _ENVELOPE_GROUPS[group]
            weighted = _weighted(
                [float(v) for v in geometry[area_key]], [float(v) for v in record["u_components_w_m2k"][u_key]]
            )
            if weighted is not None:
                record[key] = weighted
    if "g_gl_window" in values:
        record["g_gl_window"] = values["g_gl_window"]
    if "n_air_infiltration_h_1" in values:
        record["n_air_infiltration_h_1"] = values["n_air_infiltration_h_1"]
    if "mean_flat_area_m2" in values:
        if values["mean_flat_area_m2"] <= 0:
            raise ValueError("mean_flat_area_m2 must be positive")
        n_apartment = float(geometry["a_c_ref_m2"]) / values["mean_flat_area_m2"]
        record["n_apartment"] = n_apartment
        record["n_apartment_rounded"] = int(round(n_apartment))

    overridden_fields = set(values)
    if "wwr" in values:
        overridden_fields.update(
            {"geometry.a_window_components_m2", "geometry.a_wall_components_m2", "geometry.a_window_by_orientation_m2"}
        )
    if touches_transmission:
        overridden_fields.update({"h_transmission_components_w_k", "h_transmission_w_m2k", "u_components_w_m2k"})
    identity = {
        "archetype_id", "source_row", "source_building_code", "source_building_type_code", "country_stock_code",
        "survey_fold", "building_type", "construction_period", "attribution", "license", "parameter_assumptions",
    }
    copied = sorted(key for key in donor if key not in identity and key not in overridden_fields)

    assumptions = list(donor["parameter_assumptions"])
    assumptions.append(f"ASSUMED:donor {donor_id} (fields copied: {', '.join(copied)})")
    for key in ALLOWED_KEYS:
        if key in entry["values"]:
            item = entry["values"][key]
            assumptions.append(f"{key} = {item['value']}: {item['source']}")
    assumptions.extend(fallbacks)
    record["parameter_assumptions"] = assumptions
    return record


def build_records(
    spec_path: Path,
    out_path: Path,
    *,
    workbook: Path | None = None,
    donor_dir: Path | None = None,
) -> Path:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    _validate_spec(spec)
    donors = _load_donor_records(spec["donor_country"], workbook, donor_dir)
    records = []
    for entry in spec["entries"]:
        donor = _find_donor(donors, entry["donor_archetype_id"])
        records.append(_build_record(donor, spec, entry))
    ids = [record["archetype_id"] for record in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Spec produces duplicate archetype ids")
    records.sort(key=lambda record: record["archetype_id"])
    destination = Path(out_path)
    if destination.suffix != ".json":
        destination.mkdir(parents=True, exist_ok=True)
        destination = destination / f"tabula_archetypes_{spec['country'].lower()}.json"
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
    _write_json(destination, {"attribution": NATIONAL_ATTRIBUTION, "records": records})
    return destination
