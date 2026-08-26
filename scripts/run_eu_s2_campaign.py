"""EU-04 S2 physics-complete campaign runner over the 31 frozen C1A buildings.

Builds a real IDF from real TABULA constructions, real HVAC controls, and the
pinned Lyon 2023 EPW for each of the 31 rows of the frozen
``s2_c1_high_completeness_sample.csv``, runs EnergyPlus 23.1, and records one
result row per building. This is the first real European energy number in the
arc: S1 (``run_eu_s1_smoke.py``) installed a smoke construction and produced no
energy number.

Schedules are emitted at ``f=0`` only (the uninjected baseline) via
``emit_step8_gain_schedule`` as an external ``Schedule:File`` object. The
per-zone constant gains object that ``add_european_heating_controls`` installs
is removed immediately after being read for its magnitude, per
``emit_step8_gain_schedule``'s own contract that callers must remove a legacy
constant gain object before adding its external-file replacement -- otherwise
the two objects would double-count TABULA's phi_int.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry.polygon import orient

from openubem.acquisition.european_weather import sha256_file
from openubem.config import ENERGYPLUS_IDD_PATH, ENERGYPLUS_PATH
from openubem.geometry.european_residential import (
    allocate_european_dwellings,
    european_layout_to_zone_specs,
    generate_european_dwelling_layout,
)
from openubem.geometry.zoning import build_zones
from openubem.idf.european_controls import add_european_heating_controls
from openubem.idf.european_physics import add_european_internal_mass, add_nomass_construction
from openubem.idf.builder import write_zone_volumes
from openubem.idf.surfaces import extrude_geometry
from openubem.semantic.european_schedules import emit_step8_gain_schedule
from scripts.form_eu_s2_c1_sample import CENSUS_PATH

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_c1_high_completeness_sample.csv"
SUMMARY_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_c1_high_completeness_sample_summary.json"
MANIFEST_GPKG_PATH = ROOT / "openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg"
FR_ARCHETYPES_PATH = ROOT / "openubem/data/construction/tabula_archetypes_fr.json"
WEATHER_PATH = ROOT / "openubem/data/weather/fr_lyon_bron_2023_era5.epw"
REGISTRY_PATH = ROOT / "openubem/data/weather/weather_registry.json"
RUN_ROOT = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_campaign"
CAMPAIGN_MANIFEST_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_campaign_manifest.csv"
ZONE_WINDING_SIGN = 1.0

PROJECTED_CRS = "EPSG:32631"
FLOOR_TO_FLOOR_M = 3.0
FLOOR_TO_FLOOR_NOTE = "floor_to_floor_m=3.0 pinned geometry-smoke constant, not a physical claim about Lyon"
ENERGYPLUS_J_TO_KWH = 1.0 / 3.6e6
SENSITIVITY_F = 0.0

MANIFEST_COLUMNS = [
    "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
    "idf_sha256", "weather_sha256", "eplus_return_code", "severe_errors", "fatal_errors",
    "heating_kwh", "floor_area_m2", "eui_kwh_m2", "run_seconds",
]

IDF_HEADER_TEMPLATE = """Version,23.1;
Timestep,6;
Building,EU S2 Campaign,0,City,,,FullExterior,,;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,Yes,Yes,Yes,No,Yes,No,1;
SizingPeriod:WeatherFileDays,AnnualSizingPeriod,1,1,12,31,Monday,No,No;
RunPeriod,RunPeriod1,1,1,,12,31,,Sunday,No,No,No,Yes,Yes;
Site:Location,{city},{latitude},{longitude},{time_zone},{elevation};
ScheduleTypeLimits,Any Number;
"""


def load_frozen_sample() -> pd.DataFrame:
    """Load the frozen 31-row C1A sample; never re-form, reorder, or re-derive it."""
    sample = pd.read_csv(SAMPLE_PATH)
    if len(sample) != 31:
        raise ValueError(f"frozen S2 sample must contain 31 rows, found {len(sample)}")
    counts = sample["building_type"].value_counts().to_dict()
    expected = {"AB": 8, "MFH": 8, "TH": 8, "SFH": 7}
    if counts != expected:
        raise ValueError(f"frozen S2 sample quotas do not match {expected}: found {counts}")
    return sample


def verify_census_sha256(sample_summary_path: Path = SUMMARY_PATH, census_path: Path = CENSUS_PATH) -> str:
    """Return the recorded census SHA-256 after checking it against the file on disk."""
    summary = json.loads(sample_summary_path.read_text(encoding="utf-8"))
    recorded = str(summary["source_census_sha256"])
    recomputed = hashlib.sha256(census_path.read_bytes()).hexdigest()
    if recorded != recomputed:
        raise ValueError(
            f"source census SHA-256 mismatch: recorded={recorded} recomputed={recomputed}"
        )
    return recorded


def validate_mapping_ready(sample: pd.DataFrame) -> None:
    """Fail closed if any frozen row is not MAPPED_LAYOUT_READY."""
    not_ready = sample.loc[sample["mapping_status"] != "MAPPED_LAYOUT_READY", "building_id"].tolist()
    if not_ready:
        raise ValueError(f"S2 campaign requires MAPPED_LAYOUT_READY for every row; not ready: {not_ready}")


def verify_weather_checksum(weather_path: Path = WEATHER_PATH, registry_path: Path = REGISTRY_PATH) -> str:
    """Assert the Lyon EPW SHA-256 equals the registry's recorded value; abort on mismatch."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    fr_target = next(entry for entry in registry["targets"] if entry["fold"] == "fr")
    recorded = str(fr_target["sha256"])
    recomputed = sha256_file(weather_path)
    if recorded != recomputed:
        raise ValueError(
            f"Lyon EPW SHA-256 mismatch: registry={recorded} recomputed={recomputed} file={weather_path}"
        )
    return recomputed


def load_fr_record(archetype_id: str) -> dict[str, object]:
    payload = json.loads(FR_ARCHETYPES_PATH.read_text(encoding="utf-8"))
    for record in payload["records"]:
        if record["archetype_id"] == archetype_id:
            return record
    raise ValueError(f"archetype_id not found in FR TABULA registry: {archetype_id!r}")


def load_manifest_native(manifest_path: Path = MANIFEST_GPKG_PATH) -> gpd.GeoDataFrame:
    """Load the residential manifest in its own native CRS -- never reproject.

    D-EU-04-H CP-1 measured that reprojecting to EPSG:2154 makes
    generate_european_dwelling_layout's fixed-origin rotation accumulate
    floating-point noise past the partition audit's tolerance
    (OpenUBEM_debug_References.md ch.5); the frozen sample was measured in the
    manifest's native CRS, EPSG:32631.
    """
    if not manifest_path.is_file():
        raise ValueError(f"Manifest does not exist: {manifest_path}")
    gdf = gpd.read_file(manifest_path)
    if gdf.crs is None or gdf.crs.to_string() != PROJECTED_CRS:
        raise ValueError(f"Manifest CRS is {gdf.crs}, expected native {PROJECTED_CRS}")
    return gdf


def _orient_zone_footprints(zones: list[dict[str, object]], *, sign: float = 1.0) -> None:
    """Normalise each zone's floor_polygon winding in place (fixes GetVertices upside-down warning)."""
    for zone in zones:
        oriented = orient(zone["floor_polygon"], sign=sign)
        zone["floor_polygon"] = oriented
        zone["coords_m"] = list(oriented.exterior.coords)[:-1]


def build_geometry_for_row(row: pd.Series, manifest: gpd.GeoDataFrame) -> tuple[list[dict[str, object]], str]:
    """Return (zones, geometry_outcome) re-derived from the real footprint, never from the CSV."""
    building_id = row["building_id"]
    matches = manifest.loc[manifest["osm_id"].astype(str) == building_id, "geometry"]
    if matches.empty:
        raise ValueError(f"building_id missing from manifest: {building_id!r}")
    footprint = matches.iloc[0]
    allocation = allocate_european_dwellings(
        archetype_id=row["archetype_id"],
        building_type=row["building_type"],
        n_apartment=row["observed_dwellings"],
        n_storey=row["observed_storeys"],
        plate_area_m2=float(footprint.area),
    )
    layout = generate_european_dwelling_layout(footprint, requested_dwelling_count=allocation.units_per_floor)
    if layout.dwelling_layout_emitted:
        zones = european_layout_to_zone_specs(layout, building_id=building_id, height_m=FLOOR_TO_FLOOR_M)
    else:
        zones = build_zones(
            building_id, footprint, row["archetype_id"],
            num_floors=int(round(float(row["observed_storeys"]))),
            strategy="one_zone_per_floor", floor_to_floor_m=FLOOR_TO_FLOOR_M,
        )
    _orient_zone_footprints(zones, sign=ZONE_WINDING_SIGN)
    return zones, layout.status


def _envelope_construction(idf, record: dict[str, object], component: str) -> str:
    f_red = float(record["f_red_temp"])
    u_value = float(record[f"u_{component}_w_m2k"]) * f_red
    delta_u = float(record["delta_u_tb_w_m2k"]) * f_red
    return add_nomass_construction(idf, f"EU_{component}", u_value, delta_u)


def build_idf_for_building(
    row: pd.Series,
    record: dict[str, object],
    zones: list[dict[str, object]],
    run_dir: Path,
    *,
    epw_path: Path = WEATHER_PATH,
) -> Path:
    """Assemble and save one building's IDF; caller runs EnergyPlus separately."""
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        location_fields = stream.readline().strip().split(",")
    city, _state, _country = location_fields[1], location_fields[2], location_fields[3]
    latitude, longitude, time_zone, elevation = (float(value) for value in location_fields[6:10])

    run_dir.mkdir(parents=True, exist_ok=True)
    idf_path = run_dir / f"{row['building_id']}.idf"
    idf_path.write_text(
        IDF_HEADER_TEMPLATE.format(
            city=city, latitude=latitude, longitude=longitude, time_zone=time_zone, elevation=elevation,
        ),
        encoding="utf-8",
    )
    idf = IDF(str(idf_path))
    extrude_geometry(idf, zones, [])
    write_zone_volumes(idf, zones)

    wall_construction = _envelope_construction(idf, record, "wall")
    roof_construction = _envelope_construction(idf, record, "roof")
    floor_construction = _envelope_construction(idf, record, "floor")
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        surface_type = str(surface.Surface_Type).upper()
        if surface_type == "WALL":
            surface.Construction_Name = wall_construction
        elif surface_type in ("ROOF", "ROOFCEILING"):
            surface.Construction_Name = roof_construction
        elif surface_type in ("FLOOR", "CEILING"):
            surface.Construction_Name = floor_construction

    for zone in zones:
        floor_area_m2 = float(zone["floor_polygon"].area)
        add_european_internal_mass(idf, zone["name"], floor_area_m2, c_m_wh_m2k=float(record["c_m_wh_m2k"]))
        idf.newidfobject(
            "SIZING:ZONE",
            Zone_or_ZoneList_Name=zone["name"],
            Zone_Cooling_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
            Zone_Cooling_Design_Supply_Air_Temperature=13.0,
            Zone_Heating_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
            Zone_Heating_Design_Supply_Air_Temperature=50.0,
            Zone_Cooling_Design_Supply_Air_Humidity_Ratio=0.008,
            Zone_Heating_Design_Supply_Air_Humidity_Ratio=0.008,
        )
        names = add_european_heating_controls(idf, record, zone["name"])
        legacy_gain = idf.getobject("OTHEREQUIPMENT", names["gains"])
        if legacy_gain is not None:
            idf.removeidfobject(legacy_gain)
        # emit_step8_gain_schedule always (re-)creates a fixed-name
        # SCHEDULETYPELIMITS object; across multiple dwelling zones in one IDF
        # that duplicates the object and EnergyPlus fails input processing.
        # Drop any prior copy immediately before each call so exactly one survives.
        existing_limits = idf.getobject("SCHEDULETYPELIMITS", "EU_Step8_AnyNumber_Wm2")
        if existing_limits is not None:
            idf.removeidfobject(existing_limits)
        gain_csv_path = run_dir / f"{zone['name']}_f000_gain.csv"
        emit_step8_gain_schedule(
            idf,
            sensitivity_f=SENSITIVITY_F,
            dwelling_zone=zone["name"],
            dwelling_id=zone["name"],
            emitted_csv_path=gain_csv_path,
        )

    idf.newidfobject(
        "OUTPUT:VARIABLE", Key_Value="*",
        Variable_Name="Zone Ideal Loads Zone Total Heating Energy",
        Reporting_Frequency="Hourly",
    )
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
    idf.saveas(str(idf_path))
    return idf_path


def _extract_heating_kwh(csv_path: Path) -> float:
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"eplusout.csv has no header: {csv_path}")
        columns = [
            field for field in reader.fieldnames
            if "zone ideal loads zone total heating energy" in field.casefold()
            and "[j]" in field.casefold() and "(hourly)" in field.casefold()
        ]
        if not columns:
            raise ValueError(f"eplusout.csv lacks hourly heating energy output: {csv_path}")
        total_j = 0.0
        for row in reader:
            total_j += sum(float(row[column]) for column in columns)
    return total_j * ENERGYPLUS_J_TO_KWH


def run_energyplus_for_building(idf_path: Path, run_dir: Path, *, epw_path: Path = WEATHER_PATH, timeout: int = 600) -> dict[str, object]:
    energyplus_exe = ENERGYPLUS_PATH / ("energyplus.exe" if sys.platform == "win32" else "energyplus")
    start = time.perf_counter()
    eplus_return_code: int | None = None
    err_text = ""
    try:
        result = subprocess.run(
            [str(energyplus_exe), "-w", str(epw_path), "-x", "-r", "-d", ".", str(idf_path)],
            cwd=run_dir, capture_output=True, text=True, timeout=timeout,
        )
        eplus_return_code = result.returncode
        err_path = run_dir / "eplusout.err"
        err_text = err_path.read_text(encoding="utf-8", errors="replace") if err_path.is_file() else ""
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
    run_seconds = time.perf_counter() - start

    severe_errors = len(re.findall(r"\*\*\s*Severe\s*\*\*", err_text, re.IGNORECASE))
    fatal_errors = len(re.findall(r"\*\*\s*Fatal\s*\*\*", err_text, re.IGNORECASE))
    completed = (
        not timed_out and eplus_return_code == 0 and "Completed Successfully" in err_text
    )

    heating_kwh = None
    floor_area_m2 = None
    if completed:
        csv_path = run_dir / "eplusout.csv"
        heating_kwh = _extract_heating_kwh(csv_path)

    return {
        "eplus_return_code": eplus_return_code if eplus_return_code is not None else -1,
        "severe_errors": severe_errors,
        "fatal_errors": fatal_errors,
        "completed": completed,
        "heating_kwh": heating_kwh,
        "floor_area_m2": floor_area_m2,
        "run_seconds": round(run_seconds, 3),
        "err_text": err_text,
    }


def run_campaign(dry_run: bool = False) -> pd.DataFrame:
    verify_census_sha256()
    sample = load_frozen_sample()
    validate_mapping_ready(sample)
    if not dry_run:
        verify_weather_checksum()
    manifest = load_manifest_native()

    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for _, row in sample.sort_values("building_id").iterrows():
        building_id = row["building_id"]
        record = load_fr_record(row["archetype_id"])
        zones, geometry_outcome = build_geometry_for_row(row, manifest)
        run_dir = RUN_ROOT / building_id
        idf_path = build_idf_for_building(row, record, zones, run_dir)
        idf_sha256 = sha256_file(idf_path)
        floor_area_m2 = sum(float(zone["floor_polygon"].area) for zone in zones)

        result_row = {
            "building_id": building_id,
            "archetype_id": row["archetype_id"],
            "building_type": row["building_type"],
            "age_band": row["age_band"],
            "geometry_outcome": geometry_outcome,
            "idf_sha256": idf_sha256,
            "weather_sha256": "",
            "eplus_return_code": "",
            "severe_errors": "",
            "fatal_errors": "",
            "heating_kwh": "",
            "floor_area_m2": round(floor_area_m2, 4),
            "eui_kwh_m2": "",
            "run_seconds": "",
        }

        if not dry_run:
            weather_sha256 = verify_weather_checksum()
            outcome = run_energyplus_for_building(idf_path, run_dir)
            result_row["weather_sha256"] = weather_sha256
            result_row["eplus_return_code"] = outcome["eplus_return_code"]
            result_row["severe_errors"] = outcome["severe_errors"]
            result_row["fatal_errors"] = outcome["fatal_errors"]
            result_row["run_seconds"] = outcome["run_seconds"]
            if outcome["completed"]:
                heating_kwh = outcome["heating_kwh"]
                result_row["heating_kwh"] = round(heating_kwh, 6)
                result_row["eui_kwh_m2"] = round(heating_kwh / floor_area_m2, 6) if floor_area_m2 > 0 else ""
                status = "EPLUS_COMPLETED"
            else:
                fatal_match = re.search(r"^.*\*\*\s*Fatal\s*\*\*.*$", outcome["err_text"], re.MULTILINE)
                severe_match = re.search(r"^.*\*\*\s*Severe\s*\*\*.*$", outcome["err_text"], re.MULTILINE)
                first_error = (fatal_match or severe_match).group(0).strip()[:300] if (fatal_match or severe_match) else "no Severe/Fatal line in eplusout.err"
                status = "EPLUS_FATAL"
                print(f"    first_error: {first_error}")
            print(
                f"  {building_id}: geometry_outcome={geometry_outcome} zones={len(zones)} "
                f"status={status} run_seconds={outcome['run_seconds']}"
            )

        rows.append(result_row)

    frame = pd.DataFrame.from_records(rows, columns=MANIFEST_COLUMNS)
    if not dry_run:
        frame.to_csv(CAMPAIGN_MANIFEST_PATH, index=False)
    return frame


def main() -> None:
    global RUN_ROOT, CAMPAIGN_MANIFEST_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="build IDFs only; do not run EnergyPlus")
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="override RUN_ROOT; manifest is written alongside it as <name>_manifest.csv "
             "(default preserves openubem/outputs/eu_evidence/EU-04/s2_campaign/)",
    )
    args = parser.parse_args()
    if args.output_dir is not None:
        RUN_ROOT = args.output_dir.resolve()
        CAMPAIGN_MANIFEST_PATH = RUN_ROOT.parent / f"{RUN_ROOT.name}_manifest.csv"
    frame = run_campaign(dry_run=args.dry_run)
    if not args.dry_run:
        print(f"Wrote {CAMPAIGN_MANIFEST_PATH} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
