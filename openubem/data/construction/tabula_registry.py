"""Generate the ES/GB/IT TABULA registry from the reconciled Step 8 tables.

The generator is deliberately explicit about its two inputs: the three copied
parameter tables and the pinned calculator workbook.  It writes derived JSON
only; the original TABULA workbooks remain outside this repository.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from openubem.data.construction.tabula_reconcile import (
    assert_parent_invariants,
    load_parent_tables,
)


ATTRIBUTION = "Source: IEE Projects TABULA + EPISCOPE (www.episcope.eu)"
CALCULATOR_MD5 = "c99ddc9ffcb6dc0ae7391273d9619e37"
BOUNDARY_VALUES_MD5 = "7347b2cae3c4d9f5ce78221e9d5fb832"
SOURCE_SHEET = "Calc.Set.Building"
_FOLD_TO_OUTPUT = {"es": "es", "uk": "gb", "it": "it"}
_EXTRA_COLUMNS = (
    "n_Apartment",
    "n_air_infiltration",
    "g_gl_n_Window_1",
    "g_gl_n_Window_2",
    "b_Transmission_Roof_1",
    "b_Transmission_Roof_2",
    "b_Transmission_Wall_1",
    "b_Transmission_Wall_2",
    "b_Transmission_Wall_3",
    "b_Transmission_Floor_1",
    "b_Transmission_Floor_2",
    "delta_U_ThermalBridging",
    "F_red_temp",
    "h_Transmission",
    "h_Ventilation",
    "H_Transmission_Wall_1",
    "H_Transmission_Wall_2",
    "H_Transmission_Wall_3",
    "H_Transmission_Roof_1",
    "H_Transmission_Roof_2",
    "H_Transmission_Floor_1",
    "H_Transmission_Floor_2",
    "H_Transmission_Window_1",
    "H_Transmission_Window_2",
    "H_Transmission_Door_1",
    "H_Transmission_ThermalBridging",
    "n_Storey_effective_envelope",
    "c_m",
    "q_w_nd",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _weighted_u(row: Any, area_prefix: str, u_prefix: str, count: int) -> float | str:
    pairs = [
        (float(row[f"{area_prefix}_{index}"]), float(row[f"{u_prefix}_{index}"]))
        for index in range(1, count + 1)
        if float(row[f"{area_prefix}_{index}"]) > 0
    ]
    if not pairs:
        return f"UNSOURCED: no non-zero {area_prefix} component exists for area weighting"
    total_area = sum(area for area, _ in pairs)
    return sum(area * u_value for area, u_value in pairs) / total_area


def _load_calculator_values(workbook: Path, expected_ids: set[str]) -> dict[str, dict[str, float]]:
    actual_md5 = hashlib.md5(workbook.read_bytes()).hexdigest()
    if actual_md5 != CALCULATOR_MD5:
        raise ValueError(f"Unexpected calculator workbook MD5 {actual_md5}")

    loaded = load_workbook(workbook, read_only=True, data_only=True)
    sheet = loaded[SOURCE_SHEET]
    headers = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
    header_index = {str(value): index for index, value in enumerate(headers) if value is not None}
    required = ("Code_BuildingVariant",) + _EXTRA_COLUMNS
    missing = set(required).difference(header_index)
    if missing:
        raise ValueError(f"Calculator workbook lacks columns: {sorted(missing)}")

    values: dict[str, dict[str, float]] = {}
    for workbook_row in sheet.iter_rows(min_row=2, values_only=True):
        archetype_id = workbook_row[header_index["Code_BuildingVariant"]]
        if archetype_id not in expected_ids:
            continue
        extracted = {column: workbook_row[header_index[column]] for column in _EXTRA_COLUMNS}
        if any(value is None for value in extracted.values()):
            raise ValueError(f"Missing calculator value for {archetype_id}")
        values[str(archetype_id)] = {column: float(value) for column, value in extracted.items()}

    if set(values) != expected_ids:
        missing_ids = sorted(expected_ids.difference(values))
        raise ValueError(f"Calculator workbook did not yield exactly the 102 registry keys: {missing_ids}")
    return values


def _load_boundary_conditions(path: Path) -> dict[str, dict[str, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload["records"]
    result = {record["code"]: record for record in records}
    if set(result) != {"EU.SUH", "EU.MUH"}:
        raise ValueError("Boundary-condition file must contain only EU.SUH and EU.MUH")
    return result


def _record(row: Any, extras: dict[str, float], boundary: dict[str, float], workbook_sha256: str) -> dict[str, Any]:
    archetype_id = str(row["Code_BuildingVariant"])
    n_apartment = extras["n_Apartment"]
    return {
        "archetype_id": archetype_id,
        "attribution": ATTRIBUTION,
        "boundary_condition": str(row["Code_BoundaryCond"]),
        "building_type": str(row["Code_BuildingSizeClass"]),
        "c_m_wh_m2k": boundary["c_m_wh_m2k"],
        "construction_period": str(row["Code_ConstructionYearClass"]),
        "country_stock_code": str(row["Code_Country"]),
        "delta_u_tb_w_m2k": extras["delta_U_ThermalBridging"],
        "f_red_htr1": boundary["f_red_htr1"],
        "f_red_htr4": boundary["f_red_htr4"],
        "f_red_temp": extras["F_red_temp"],
        "g_gl_n_window_2": extras["g_gl_n_Window_2"],
        "g_gl_window": extras["g_gl_n_Window_1"],
        "geometry": {
            "a_c_ref_m2": float(row["A_C_Ref"]),
            "a_door_m2": float(row["A_Door_1"]),
            "a_floor_components_m2": [float(row[f"A_Floor_{i}"]) for i in (1, 2)],
            "a_roof_components_m2": [float(row[f"A_Roof_{i}"]) for i in (1, 2)],
            "a_wall_components_m2": [float(row[f"A_Wall_{i}"]) for i in (1, 2, 3)],
            "a_window_components_m2": [float(row[f"A_Window_{i}"]) for i in (1, 2)],
            "a_window_by_orientation_m2": {
                direction.lower(): float(row[f"A_Window_{direction}"])
                for direction in ("Horizontal", "East", "South", "West", "North")
            },
            "h_room_m": float(row["h_room"]),
            "n_storey": float(row["n_Storey"]),
            "n_storey_effective": float(row["n_Storey_effective"]),
            "n_storey_effective_envelope": extras["n_Storey_effective_envelope"],
            "v_c_m3": float(row["V_C"]),
        },
        "h_transmission_w_m2k": extras["h_Transmission"],
        "h_transmission_components_w_k": {
            "door_1": extras["H_Transmission_Door_1"],
            "floor_1": extras["H_Transmission_Floor_1"],
            "floor_2": extras["H_Transmission_Floor_2"],
            "roof_1": extras["H_Transmission_Roof_1"],
            "roof_2": extras["H_Transmission_Roof_2"],
            "thermal_bridging": extras["H_Transmission_ThermalBridging"],
            "wall_1": extras["H_Transmission_Wall_1"],
            "wall_2": extras["H_Transmission_Wall_2"],
            "wall_3": extras["H_Transmission_Wall_3"],
            "window_1": extras["H_Transmission_Window_1"],
            "window_2": extras["H_Transmission_Window_2"],
        },
        "h_ventilation_w_m2k": extras["h_Ventilation"],
        "license": {"status": "VERIFIED", "attribution": ATTRIBUTION},
        "n_air_infiltration_h_1": extras["n_air_infiltration"],
        "n_air_use_h_1": boundary["n_air_use_h_1"],
        "n_apartment": n_apartment,
        "n_apartment_rounded": int(round(n_apartment)),
        "parameter_assumptions": [
            "UNSOURCED: TABULA provides envelope areas and conditioned volume, not footprint aspect ratio.",
            "UNSOURCED: TABULA does not specify box orientation or window-to-face mapping.",
        ],
        "phi_int_w_m2": float(row["phi_int"]),
        "q_w_nd_kwh_m2a": extras["q_w_nd"],
        "source_row": archetype_id,
        "source_building_code": str(row["Code_Building"]),
        "source_building_type_code": str(row["Code_BuildingType"]),
        "source_sheet": SOURCE_SHEET,
        "source_workbook_md5": CALCULATOR_MD5,
        "source_workbook_sha256": workbook_sha256,
        "survey_fold": None,
        "theta_i_c": boundary["theta_i_c"],
        "transmission_b_factors": {
            "floor_1": extras["b_Transmission_Floor_1"],
            "floor_2": extras["b_Transmission_Floor_2"],
            "roof_1": extras["b_Transmission_Roof_1"],
            "roof_2": extras["b_Transmission_Roof_2"],
            "wall_1": extras["b_Transmission_Wall_1"],
            "wall_2": extras["b_Transmission_Wall_2"],
            "wall_3": extras["b_Transmission_Wall_3"],
        },
        "u_floor_w_m2k": _weighted_u(row, "A_Floor", "U_Floor", 2),
        "u_components_w_m2k": {
            "floor": [float(row[f"U_Floor_{i}"]) for i in (1, 2)],
            "roof": [float(row[f"U_Roof_{i}"]) for i in (1, 2)],
            "wall": [float(row[f"U_Wall_{i}"]) for i in (1, 2, 3)],
            "window": [float(row[f"U_Window_{i}"]) for i in (1, 2)],
        },
        "u_roof_w_m2k": _weighted_u(row, "A_Roof", "U_Roof", 2),
        "u_wall_w_m2k": _weighted_u(row, "A_Wall", "U_Wall", 3),
        "u_window_w_m2k": _weighted_u(row, "A_Window", "U_Window", 2),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_registry(
    step8_outputs_dir: Path, calculator_workbook: Path, output_dir: Path
) -> dict[str, Path]:
    """Generate deterministic ES, GB and IT registries and return their paths."""
    tables = load_parent_tables(step8_outputs_dir)
    assert_parent_invariants(tables)
    expected_ids = {
        str(row["Code_BuildingVariant"])
        for table in tables.values()
        for _, row in table.iterrows()
    }
    if len(expected_ids) != 102:
        raise ValueError(f"Expected 102 unique parent-table archetypes, got {len(expected_ids)}")
    extra_values = _load_calculator_values(Path(calculator_workbook), expected_ids)
    boundaries = _load_boundary_conditions(
        Path(__file__).with_name("tabula_boundary_conditions_eu.json")
    )
    workbook_sha256 = _sha256(Path(calculator_workbook))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for fold, table in tables.items():
        records = []
        for _, row in table.iterrows():
            record = _record(row, extra_values[str(row["Code_BuildingVariant"])], boundaries[str(row["Code_BoundaryCond"])], workbook_sha256)
            record["survey_fold"] = fold
            records.append(record)
        records.sort(key=lambda record: record["archetype_id"])
        destination = output / f"tabula_archetypes_{_FOLD_TO_OUTPUT[fold]}.json"
        _write_json(destination, {"attribution": ATTRIBUTION, "records": records})
        written[fold] = destination
    return written


def generate_fr_registry(calculator_workbook: Path, output_dir: Path) -> Path:
    """Generate the 40-row France physical registry and record 10 exclusions."""
    workbook = Path(calculator_workbook)
    actual_md5 = hashlib.md5(workbook.read_bytes()).hexdigest()
    if actual_md5 != CALCULATOR_MD5:
        raise ValueError(f"Unexpected calculator workbook MD5 {actual_md5}")
    loaded = load_workbook(workbook, read_only=True, data_only=True)
    sheet = loaded[SOURCE_SHEET]
    headers = [str(value) if value is not None else None for value in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    required = {"Code_Country", "Number_BuildingVariant", "Code_BuildingVariant"}.union(_EXTRA_COLUMNS)
    if missing := required.difference(headers):
        raise ValueError(f"Calculator workbook lacks columns: {sorted(missing)}")
    rows = []
    for values in sheet.iter_rows(min_row=2, values_only=True):
        row = dict(zip(headers, values))
        if row["Code_Country"] == "FR" and row["Number_BuildingVariant"] == 1:
            rows.append(row)
    if len(rows) != 50:
        raise ValueError(f"Expected 50 France existing-state rows, got {len(rows)}")
    national_pattern = re.compile(r"FR\.N\.(AB|MFH|SFH|TH)\.(0[1-9]|10)\.Gen\.ReEx\.001\.001")
    national = [row for row in rows if national_pattern.fullmatch(str(row["Code_BuildingVariant"]))]
    excluded = [row for row in rows if str(row["Code_BuildingVariant"]).startswith("FR.OPHM.")]
    if len(national) != 40 or len(excluded) != 10 or len(national) + len(excluded) != len(rows):
        raise ValueError("France rows do not match the 40 FR.N + 10 FR.OPHM contract")
    boundaries = _load_boundary_conditions(Path(__file__).with_name("tabula_boundary_conditions_eu.json"))
    workbook_sha256 = _sha256(workbook)
    records = []
    for row in national:
        extras = {column: float(row[column]) for column in _EXTRA_COLUMNS}
        record = _record(row, extras, boundaries[str(row["Code_BoundaryCond"])], workbook_sha256)
        record["survey_fold"] = "fr"
        records.append(record)
    records.sort(key=lambda record: record["archetype_id"])
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "tabula_archetypes_fr.json"
    _write_json(destination, {"attribution": ATTRIBUTION, "records": records})
    exclusion_lines = ["archetype_id,reason,attribution"]
    for row in sorted(excluded, key=lambda item: str(item["Code_BuildingVariant"])):
        exclusion_lines.append(
            f'{row["Code_BuildingVariant"]},FR.OPHM pilot row: unset metadata and FR.MUH-DPE1 pointer,{ATTRIBUTION}'
        )
    (output / "tabula_archetypes_fr_exclusions.csv").write_text(
        "\n".join(exclusion_lines) + "\n", encoding="utf-8"
    )
    return destination
