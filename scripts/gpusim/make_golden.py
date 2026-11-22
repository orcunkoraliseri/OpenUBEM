import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import difflib
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
GOLDEN_RUNS_DIR = REPO_ROOT / "openubem/outputs/gpusim_golden_runs"
GOLDEN_FIXTURES_DIR = REPO_ROOT / "tests/fixtures/gpusim/golden"
WEATHER_DIR = REPO_ROOT / "openubem/data/weather"
ENERGYPLUS_BIN = Path("/Applications/EnergyPlus-23-1-0/energyplus")
MAX_WORKERS = 4
EXPECTED_TIMESTEP_ROWS = 105_120
MAX_FIXTURE_TOTAL_MB = 60.0
EXPECTED_MISSING_VAR = (
    "Surface Window Inside Face Glazing Zone Convection Heat Gain Rate"
)
REQUIRED_COPY_FILES: tuple[str, ...] = (
    "in.idf",
    "eplusout.eio",
    "eplusout.err",
    "eplusout.expidf",
)
VARIANT_BASE_VARIABLES: tuple[str, ...] = (
    "Zone Mean Air Temperature",
    "Zone Ideal Loads Zone Sensible Heating Rate",
    "Zone Ideal Loads Zone Total Heating Energy",
    "Site Outdoor Air Drybulb Temperature",
    "Site Outdoor Air Humidity Ratio",
    "Site Outdoor Air Barometric Pressure",
    "Site Sky Temperature",
    "Site Horizontal Infrared Radiation Rate per Area",
)
DATE_TIME_RE = re.compile(r"^\s*(\d{2})/(\d{2})\s+(\d{2}):(\d{2}):\d{2}\s*$")
SEVERE_OR_FATAL_RE = re.compile(r"\*\*\s*(?:Severe|Fatal)\s*\*\*", re.IGNORECASE)
SEVERE_COUNT_RE = re.compile(r"(\d+)\s+Severe Errors", re.IGNORECASE)

GOLDEN_CELLS: tuple[str, ...] = (
    "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100",
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
)
BASE_CELL_ID = GOLDEN_CELLS[0]

TIMESTEP_VARIABLES: tuple[str, ...] = (
    "Zone Mean Air Temperature",
    "Zone Air Temperature",
    "Zone Air Humidity Ratio",
    "Surface Inside Face Temperature",
    "Surface Outside Face Temperature",
    "Surface Inside Face Convection Heat Gain Rate",
    "Surface Inside Face Convection Heat Transfer Coefficient",
    "Surface Inside Face Net Surface Thermal Radiation Heat Gain Rate",
    "Surface Outside Face Convection Heat Transfer Coefficient",
    "Surface Outside Face Thermal Radiation to Sky Heat Transfer Coefficient",
    "Surface Outside Face Thermal Radiation to Air Heat Transfer Coefficient",
    "Surface Outside Face Thermal Radiation to Ground Heat Transfer Coefficient",
    "Surface Window Inside Face Glazing Zone Convection Heat Gain Rate",
    "Zone Ideal Loads Zone Sensible Heating Rate",
    "Zone Ideal Loads Zone Total Heating Energy",
    "Zone Ventilation Sensible Heat Loss Energy",
    "Zone Ventilation Sensible Heat Gain Energy",
    "Zone Ventilation Mass Flow Rate",
    "Site Outdoor Air Drybulb Temperature",
    "Site Outdoor Air Humidity Ratio",
    "Site Outdoor Air Barometric Pressure",
    "Site Sky Temperature",
    "Site Horizontal Infrared Radiation Rate per Area",
)

V15_SOLAR_VARIABLES: tuple[str, ...] = (
    "Surface Outside Face Incident Solar Radiation Rate per Area",
    "Zone Windows Total Transmitted Solar Radiation Rate",
)

VENT_METHOD_FIELDS: dict[str, int] = {
    "flow/zone": 5,
    "flow/area": 6,
    "flow/person": 7,
    "airchanges/hour": 8,
}


@dataclass(frozen=True)
class IdfField:
    """Single field token within an IDF object.

    Attributes:
        value_start: Start character offset of the trimmed field value.
        value_end: End character offset of the trimmed field value.
        value: Trimmed string value of the field.
    """

    value_start: int
    value_end: int
    value: str


@dataclass(frozen=True)
class IdfObject:
    """Parsed IDF object holding type name and field spans.

    Attributes:
        obj_type: Uppercase object type name (field 0).
        fields: List of fields where index 0 is the object type.
    """

    obj_type: str
    fields: list[IdfField]


def map_windows_path(win_path: str) -> Path:
    """Map a Windows repo path to the matching path under REPO_ROOT.

    Args:
        win_path: Windows path string containing ``OpenUBEM\\``.

    Returns:
        Resolved Path inside the local repository.

    Raises:
        ValueError: If ``OpenUBEM\\`` marker is missing.
        FileNotFoundError: If the mapped path does not exist on disk.
    """
    marker = "openubem\\"
    lower = win_path.casefold()
    idx = lower.find(marker)
    if idx < 0:
        raise ValueError(f"Cannot map path without OpenUBEM marker: {win_path}")
    rel = win_path[idx + len(marker) :].replace("\\", "/")
    mapped = REPO_ROOT / rel
    if not mapped.exists():
        raise FileNotFoundError(f"Mapped path does not exist: {mapped}")
    return mapped


def parse_idf(text: str) -> list[IdfObject]:
    """Parse an IDF string into objects preserving exact character offsets.

    Args:
        text: Raw IDF file contents.

    Returns:
        List of IdfObject records in file order.
    """
    objects: list[IdfObject] = []
    n = len(text)
    i = 0

    while i < n:
        while i < n:
            ch = text[i]
            if ch == "!":
                nl = text.find("\n", i)
                i = n if nl < 0 else nl + 1
            elif ch.isspace():
                i += 1
            else:
                break
        if i >= n:
            break

        fields: list[IdfField] = []
        span_start = i
        first_non_ws: int | None = None
        last_non_ws: int | None = None

        while i < n:
            ch = text[i]
            if ch == "!":
                nl = text.find("\n", i)
                i = n if nl < 0 else nl + 1
                continue
            if ch in (",", ";"):
                if first_non_ws is not None and last_non_ws is not None:
                    val_start = first_non_ws
                    val_end = last_non_ws + 1
                    val = text[val_start:val_end]
                else:
                    val_start = span_start
                    val_end = span_start
                    val = ""
                fields.append(IdfField(val_start, val_end, val))
                i += 1
                if ch == ";":
                    break
                span_start = i
                first_non_ws = None
                last_non_ws = None
                continue
            if not ch.isspace():
                if first_non_ws is None:
                    first_non_ws = i
                last_non_ws = i
            i += 1

        if fields:
            objects.append(IdfObject(fields[0].value.upper(), fields))

    return objects


def apply_edits(text: str, edits: list[tuple[int, int, str]]) -> str:
    """Apply non-overlapping character span replacements to text.

    Args:
        text: Original string.
        edits: List of ``(start, end, replacement)`` tuples.

    Returns:
        Updated string with only the targeted spans modified.

    Raises:
        ValueError: If two edits overlap.
    """
    ordered = sorted(edits, key=lambda item: (item[0], item[1]), reverse=True)
    prev_start = len(text) + 1
    out = text
    for start, end, replacement in ordered:
        if end > prev_start:
            raise ValueError(f"Overlapping edit at {start}:{end}")
        out = out[:start] + replacement + out[end:]
        prev_start = start
    return out


def format_float(value: float) -> str:
    """Format a float64 value cleanly with 15 significant digits.

    Args:
        value: Floating-point number to format.

    Returns:
        Clean decimal string representation.
    """
    return f"{value:.15g}"


def replace_field(
    edits: list[tuple[int, int, str]],
    obj: IdfObject,
    field_idx: int,
    new_value: str,
) -> None:
    """Record an edit replacing one 1-based field in an IDF object.

    Args:
        edits: Mutable list of pending edits.
        obj: Target parsed IDF object.
        field_idx: 1-based field index (0 is object type).
        new_value: Replacement string value.

    Raises:
        IndexError: If the object lacks ``field_idx``.
    """
    if field_idx >= len(obj.fields):
        raise IndexError(
            f"{obj.obj_type} has {len(obj.fields) - 1} fields, need {field_idx}"
        )
    field = obj.fields[field_idx]
    edits.append((field.value_start, field.value_end, new_value))


def append_lines(text: str, lines: list[str]) -> str:
    """Append IDF lines to text, inserting a separator newline if needed.

    Args:
        text: Base IDF text.
        lines: Complete IDF statements to append.

    Returns:
        IDF text with appended lines and trailing newline.
    """
    prefix = text if text.endswith("\n") else text + "\n"
    return prefix + "\n".join(lines) + "\n"


def rewrite_schedule_paths_to_basename(text: str) -> str:
    """Replace Schedule:File field 3 with bare file basenames.

    Args:
        text: IDF text to rewrite.

    Returns:
        Updated IDF text with bare schedule CSV basenames.

    Raises:
        ValueError: If no Schedule:File objects exist or Windows paths remain.
    """
    objects = parse_idf(text)
    edits: list[tuple[int, int, str]] = []
    count = 0
    for obj in objects:
        if obj.obj_type == "SCHEDULE:FILE":
            raw_path = obj.fields[3].value
            basename = PureWindowsPath(raw_path).name
            replace_field(edits, obj, 3, basename)
            count += 1
    if count == 0:
        raise ValueError("No SCHEDULE:FILE object found in IDF")
    updated = apply_edits(text, edits)
    if "C:\\" in updated or "c:\\" in updated:
        raise ValueError("Windows path still remains in IDF after rewrite")
    return updated


def prepare_base_cell(cell_id: str) -> tuple[str, Path, Path]:
    """Create prepared run folder for one golden cell.

    Args:
        cell_id: Golden cell identifier.

    Returns:
        Tuple of ``(prepared_idf_text, epw_src_path, schedule_src_path)``.
    """
    manifest_path = REP2_DIR / "manifests" / f"{cell_id}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    epw_src = map_windows_path(manifest["epw_path"])
    idf_src = REP2_DIR / "idfs" / f"{cell_id}.idf"
    sched_src = REP2_DIR / "schedules" / f"{cell_id}.csv"

    for path in (idf_src, epw_src, sched_src):
        if not path.exists():
            raise FileNotFoundError(f"Missing required input: {path}")

    out_dir = GOLDEN_RUNS_DIR / cell_id
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(epw_src, out_dir / "in.epw")
    shutil.copy2(sched_src, out_dir / sched_src.name)

    raw_idf = idf_src.read_text(encoding="utf-8")
    idf_text = rewrite_schedule_paths_to_basename(raw_idf)
    extra_lines = [
        "Output:Constructions,Constructions;",
        "Output:Surfaces:List,Details;",
        "Output:Surfaces:List,ViewFactorInfo;",
        *(f"Output:Variable,*,{name},Timestep;" for name in TIMESTEP_VARIABLES),
    ]
    idf_text = append_lines(idf_text, extra_lines)
    (out_dir / "in.idf").write_text(idf_text, encoding="utf-8")
    return idf_text, epw_src, sched_src


def read_epw_location(epw_path: Path) -> tuple[str, str, str, str, str]:
    """Read Site:Location fields from an EPW LOCATION header line.

    Args:
        epw_path: Path to the EPW weather file.

    Returns:
        Tuple of ``(name, latitude, longitude, time_zone, elevation)``.

    Raises:
        ValueError: If the EPW header lacks a valid LOCATION line.
    """
    with epw_path.open("r", encoding="utf-8", errors="replace") as handle:
        first_line = handle.readline().strip()
    parts = first_line.split(",")
    if len(parts) < 10 or parts[0].strip().upper() != "LOCATION":
        raise ValueError(f"Invalid EPW LOCATION header in {epw_path}: {first_line}")
    return (
        parts[1].strip(),
        parts[6].strip(),
        parts[7].strip(),
        parts[8].strip(),
        parts[9].strip(),
    )


def inspect_run_period(objects: list[IdfObject]) -> str:
    """Summarize RunPeriod year/weekday fields for reporting.

    Args:
        objects: Parsed IDF objects.

    Returns:
        Human-readable summary of RunPeriod year-related fields.
    """
    run_periods = [obj for obj in objects if obj.obj_type == "RUNPERIOD"]
    if not run_periods:
        return "none"
    summaries: list[str] = []
    for rp in run_periods:
        begin_yr = rp.fields[4].value if len(rp.fields) > 4 else ""
        end_yr = rp.fields[7].value if len(rp.fields) > 7 else ""
        start_day = rp.fields[8].value if len(rp.fields) > 8 else ""
        summaries.append(
            f"{rp.fields[1].value}(begin_year={begin_yr!r},"
            f"end_year={end_yr!r},start_day={start_day!r})"
        )
    return "; ".join(summaries)


def build_variant_idf(
    variant_id: str,
    base_idf: str,
    base_epw: Path,
) -> tuple[str, Path, str]:
    """Generate modified IDF text and weather file path for one variant.

    Args:
        variant_id: Variant code (``V01`` .. ``V15``).
        base_idf: Prepared ``in.idf`` contents from base cell 1.
        base_epw: Default EPW file path from base cell 1.

    Returns:
        Tuple of ``(variant_idf_text, epw_path, note)``.

    Raises:
        ValueError: If target IDF objects/fields are missing or unknown variant.
    """
    objects = parse_idf(base_idf)
    edits: list[tuple[int, int, str]] = []
    epw_path = base_epw
    note = ""
    extra_append: list[str] = []

    if variant_id == "V01":
        vents = [o for o in objects if o.obj_type == "ZONEVENTILATION:DESIGNFLOWRATE"]
        if not vents:
            raise ValueError("V01: missing ZoneVentilation:DesignFlowRate")
        for vent in vents:
            method = vent.fields[4].value.strip().casefold()
            if method not in VENT_METHOD_FIELDS:
                raise ValueError(f"V01: unsupported ventilation method {method!r}")
            idx = VENT_METHOD_FIELDS[method]
            val = float(vent.fields[idx].value)
            replace_field(edits, vent, idx, format_float(val * 3.0))
        note = f"scaled {len(vents)} ventilation flow field(s) x3"

    elif variant_id == "V03":
        thermostats = [o for o in objects if o.obj_type == "HVACTEMPLATE:THERMOSTAT"]
        if not thermostats:
            raise ValueError("V03: missing HVACTemplate:Thermostat")
        for therm in thermostats:
            if therm.fields[2].value.strip():
                raise ValueError("V03: expected blank Heating Setpoint Schedule Name")
            val = float(therm.fields[3].value)
            replace_field(edits, therm, 3, format_float(val + 2.0))
        note = f"raised {len(thermostats)} constant heating setpoint(s) +2 K"

    elif variant_id == "V04":
        mats = [o for o in objects if o.obj_type == "MATERIAL:NOMASS"]
        if not mats:
            raise ValueError("V04: missing Material:NoMass")
        for mat in mats:
            val = float(mat.fields[3].value)
            replace_field(edits, mat, 3, format_float(val / 0.3))
        note = f"scaled {len(mats)} Material:NoMass thermal resistance(s) /0.3"

    elif variant_id == "V06":
        glazings = [
            o for o in objects if o.obj_type == "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"
        ]
        if not glazings:
            raise ValueError("V06: missing WindowMaterial:SimpleGlazingSystem")
        for glass in glazings:
            val = float(glass.fields[2].value)
            replace_field(edits, glass, 2, format_float(val * 0.5))
        note = f"scaled {len(glazings)} glazing U-factor(s) x0.5"

    elif variant_id in ("V07", "V14"):
        factor = 4.0 if variant_id == "V07" else 2.0
        masses = [o for o in objects if o.obj_type == "INTERNALMASS"]
        if not masses:
            raise ValueError(f"{variant_id}: missing InternalMass")
        for mass in masses:
            val = float(mass.fields[5].value)
            replace_field(edits, mass, 5, format_float(val * factor))
        note = f"scaled {len(masses)} InternalMass area(s) x{factor:g}"

    elif variant_id == "V09":
        oscs = [
            o
            for o in objects
            if o.obj_type == "SURFACEPROPERTY:OTHERSIDECOEFFICIENTS"
        ]
        if not oscs:
            raise ValueError("V09: missing SurfaceProperty:OtherSideCoefficients")
        for osc in oscs:
            replace_field(edits, osc, 5, "1")
            replace_field(edits, osc, 8, "0")
        note = f"set {len(oscs)} OSC objects to T_out_coef=1, T_zone_coef=0"

    elif variant_id in ("V10", "V11"):
        epw_name = (
            "fi_helsinki_tmyx_2009_2023.epw"
            if variant_id == "V10"
            else "ca_montreal_tmyx_2009_2023.epw"
        )
        epw_path = WEATHER_DIR / epw_name
        if not epw_path.exists():
            raise FileNotFoundError(f"{variant_id}: missing EPW {epw_path}")
        loc_vals = read_epw_location(epw_path)
        locs = [o for o in objects if o.obj_type == "SITE:LOCATION"]
        if not locs:
            raise ValueError(f"{variant_id}: missing Site:Location")
        for loc in locs:
            for idx, val in enumerate(loc_vals, start=1):
                replace_field(edits, loc, idx, val)
        rp_info = inspect_run_period(objects)
        note = f"climate={epw_name}, RunPeriod unchanged: {rp_info}"

    elif variant_id == "V15":
        outdoor_surfaces = [
            o
            for o in objects
            if o.obj_type == "BUILDINGSURFACE:DETAILED"
            and o.fields[6].value.strip().casefold() == "outdoors"
        ]
        if not outdoor_surfaces:
            raise ValueError("V15: no BuildingSurface:Detailed with Outdoors")
        outdoor_surface_names: set[str] = set()
        outdoor_constructions: set[str] = set()
        for surf in outdoor_surfaces:
            replace_field(edits, surf, 8, "SunExposed")
            outdoor_surface_names.add(surf.fields[1].value.strip().casefold())
            outdoor_constructions.add(surf.fields[3].value.strip().casefold())

        for fen in objects:
            if fen.obj_type != "FENESTRATIONSURFACE:DETAILED":
                continue
            parent_name = fen.fields[4].value.strip().casefold()
            if parent_name in outdoor_surface_names:
                outdoor_constructions.add(fen.fields[3].value.strip().casefold())

        outdoor_materials: set[str] = set()
        for cons in objects:
            if cons.obj_type != "CONSTRUCTION":
                continue
            if cons.fields[1].value.strip().casefold() in outdoor_constructions:
                for layer in cons.fields[2:]:
                    layer_name = layer.value.strip().casefold()
                    if layer_name:
                        outdoor_materials.add(layer_name)

        mats = [
            o
            for o in objects
            if o.obj_type == "MATERIAL:NOMASS"
            and o.fields[1].value.strip().casefold() in outdoor_materials
        ]
        if not mats:
            raise ValueError("V15: no Outdoors Material:NoMass found")
        for mat in mats:
            replace_field(edits, mat, 5, "0")

        glazings = [
            o for o in objects if o.obj_type == "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"
        ]
        if not glazings:
            raise ValueError("V15: missing WindowMaterial:SimpleGlazingSystem")
        for glass in glazings:
            val = float(glass.fields[3].value)
            replace_field(edits, glass, 3, format_float(val * 0.42))

        extra_append = [
            f"Output:Variable,*,{name},Timestep;" for name in V15_SOLAR_VARIABLES
        ]
        note = (
            f"{len(outdoor_surfaces)} Outdoors SunExposed, "
            f"{len(mats)} Outdoors NoMass SolarAbs=0 (floor unchanged), "
            f"{len(glazings)} SHGC x0.42, +2 solar outputs"
        )

    else:
        raise ValueError(f"Unknown variant_id: {variant_id}")

    updated = apply_edits(base_idf, edits)
    if extra_append:
        updated = append_lines(updated, extra_append)
    return updated, epw_path, note


def summarize_idf_diff(variant_id: str, base_idf: str, variant_idf: str) -> str:
    """Produce a concise changed-line diff summary between base and variant IDFs.

    Args:
        variant_id: Variant code for labeling.
        base_idf: Prepared base cell 1 IDF text.
        variant_idf: Modified variant IDF text.

    Returns:
        Formatted diff summary string.
    """
    diff_lines = list(
        difflib.unified_diff(
            base_idf.splitlines(),
            variant_idf.splitlines(),
            fromfile=f"{BASE_CELL_ID}/in.idf",
            tofile=f"{BASE_CELL_ID}__{variant_id}/in.idf",
            n=0,
            lineterm="",
        )
    )
    changed = [
        line
        for line in diff_lines
        if line.startswith(("@@", "-", "+"))
        and not line.startswith(("---", "+++"))
    ]
    return f"[{variant_id}] diff lines ({len(changed)} entries):\n" + "\n".join(
        f"  {line}" for line in changed
    )


def scan_epw_infrared() -> list[tuple[str, int, int]]:
    """Scan all unique EPWs in rep2 manifests for invalid IRHoriz values.

    Returns:
        Sorted list of ``(epw_filename, invalid_count, total_hours)`` tuples.

    Raises:
        FileNotFoundError: If no manifests exist or a mapped EPW is missing.
    """
    manifest_paths = sorted((REP2_DIR / "manifests").glob("*.json"))
    if not manifest_paths:
        raise FileNotFoundError(f"No manifests found in {REP2_DIR / 'manifests'}")

    unique_epws: set[Path] = set()
    for mpath in manifest_paths:
        data = json.loads(mpath.read_text(encoding="utf-8"))
        unique_epws.add(map_windows_path(data["epw_path"]))

    results: list[tuple[str, int, int]] = []
    for epw_path in sorted(unique_epws, key=lambda p: p.name):
        bad = 0
        total = 0
        with epw_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_idx, line in enumerate(handle):
                if line_idx < 8:
                    continue
                stripped = line.strip()
                if not stripped:
                    continue
                cols = stripped.split(",")
                if len(cols) < 13:
                    raise ValueError(
                        f"{epw_path.name} line {line_idx + 1} has {len(cols)} cols"
                    )
                ir_val = float(cols[12])
                total += 1
                if ir_val <= 0.0 or ir_val >= 9999.0:
                    bad += 1
        results.append((epw_path.name, bad, total))
    return results


def prepare_all() -> None:
    """Prepare the 3 golden cells, 10 variants, run_list.txt, and EPW IR scan."""
    GOLDEN_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_list_entries: list[str] = []

    base_idf = ""
    base_epw = Path()
    base_sched = Path()

    for idx, cell_id in enumerate(GOLDEN_CELLS):
        idf_text, epw_src, sched_src = prepare_base_cell(cell_id)
        run_list_entries.append(cell_id)
        if idx == 0:
            base_idf = idf_text
            base_epw = epw_src
            base_sched = sched_src

    variant_ids = (
        "V01",
        "V03",
        "V04",
        "V06",
        "V07",
        "V09",
        "V10",
        "V11",
        "V14",
        "V15",
    )

    print("=== Variant diff summaries ===")
    for variant_id in variant_ids:
        var_rel = f"variants/{BASE_CELL_ID}__{variant_id}"
        var_dir = GOLDEN_RUNS_DIR / var_rel
        var_dir.mkdir(parents=True, exist_ok=True)

        var_idf, var_epw, note = build_variant_idf(variant_id, base_idf, base_epw)
        (var_dir / "in.idf").write_text(var_idf, encoding="utf-8")
        shutil.copy2(var_epw, var_dir / "in.epw")
        shutil.copy2(base_sched, var_dir / base_sched.name)
        run_list_entries.append(var_rel)

        print(f"\n{variant_id}: {note}")
        print(summarize_idf_diff(variant_id, base_idf, var_idf))

    run_list_path = GOLDEN_RUNS_DIR / "run_list.txt"
    run_list_path.write_text("\n".join(run_list_entries) + "\n", encoding="utf-8")
    print(f"\nWrote {len(run_list_entries)} entries to {run_list_path}")

    print("\n=== EPW horizontal infrared scan (field 13 <= 0 or >= 9999) ===")
    ir_results = scan_epw_infrared()
    for name, bad, total in ir_results:
        print(f"{name}, {bad} (of {total} hours)")


def _clean_run_dir(run_dir: Path) -> None:
    """Remove prior EnergyPlus output files while preserving run inputs.

    Args:
        run_dir: Prepared EnergyPlus run folder.
    """
    keep = {"in.idf", "in.epw", *(f"{cell_id}.csv" for cell_id in GOLDEN_CELLS)}
    for item in run_dir.iterdir():
        if item.name not in keep:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def _run_single_folder(rel_folder: str) -> tuple[str, int, float, str]:
    """Run EnergyPlus 23.1.0 once in a single prepared run folder.

    Args:
        rel_folder: Folder path relative to ``GOLDEN_RUNS_DIR``.

    Returns:
        Tuple of ``(rel_folder, returncode, wall_seconds, stderr_snippet)``.
    """
    run_dir = GOLDEN_RUNS_DIR / rel_folder
    _clean_run_dir(run_dir)
    cmd = [
        str(ENERGYPLUS_BIN),
        "-x",
        "-r",
        "-w",
        str(run_dir / "in.epw"),
        "-d",
        str(run_dir),
        str(run_dir / "in.idf"),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=run_dir,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    wall_s = time.perf_counter() - t0
    err_tail = (proc.stderr or "").strip()[-400:]
    return rel_folder, proc.returncode, wall_s, err_tail


def read_run_list() -> list[str]:
    """Read relative run folders from ``run_list.txt``.

    Returns:
        List of non-empty relative folder strings.

    Raises:
        FileNotFoundError: If ``run_list.txt`` does not exist.
    """
    run_list_path = GOLDEN_RUNS_DIR / "run_list.txt"
    if not run_list_path.exists():
        raise FileNotFoundError(f"Missing run list: {run_list_path}")
    return [
        line.strip()
        for line in run_list_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_all() -> int:
    """Execute all EnergyPlus runs in ``run_list.txt`` with at most 4 workers.

    Returns:
        0 if every run succeeded, 1 if any run failed.
    """
    if not ENERGYPLUS_BIN.exists():
        raise FileNotFoundError(f"Missing EnergyPlus binary: {ENERGYPLUS_BIN}")
    folders = read_run_list()
    print(f"Running {len(folders)} EnergyPlus jobs (max_workers={MAX_WORKERS})...")
    t_start = time.perf_counter()
    results_by_folder: dict[str, tuple[int, float, str]] = {}
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_run_single_folder, rel): rel for rel in folders
        }
        for future in as_completed(futures):
            rel, rc, wall_s, err_tail = future.result()
            results_by_folder[rel] = (rc, wall_s, err_tail)
            print(f"  [{rc}] {rel}: {wall_s:.3f} s", flush=True)
    total_wall = time.perf_counter() - t_start
    print(f"Total run wall time: {total_wall:.3f} s")

    failures = [
        (rel, results_by_folder[rel])
        for rel in folders
        if results_by_folder[rel][0] != 0
    ]
    if failures:
        print("ERROR: One or more EnergyPlus runs failed:")
        for rel, (rc, wall_s, err_tail) in failures:
            print(f"  {rel}: rc={rc}, wall={wall_s:.3f} s, stderr={err_tail}")
        return 1
    return 0


def _sha256_file(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file.

    Args:
        path: Path to the file to hash.

    Returns:
        Lowercase 64-character hexadecimal SHA-256 digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_eplus_run(run_dir: Path) -> list[str]:
    """Validate EnergyPlus completion and error logs for a run directory.

    Args:
        run_dir: Completed EnergyPlus run directory.

    Returns:
        List of expected warning lines observed in ``eplusout.err``.

    Raises:
        FileNotFoundError: If required output or log files are missing.
        RuntimeError: If EnergyPlus did not complete cleanly or reported
            severe or fatal errors.
    """
    for req_name in (*REQUIRED_COPY_FILES, "eplusout.end", "eplusout.csv", "in.epw"):
        if not (run_dir / req_name).exists():
            raise FileNotFoundError(f"Missing required file {run_dir / req_name}")

    end_text = (run_dir / "eplusout.end").read_text(encoding="utf-8", errors="replace")
    if "EnergyPlus Completed Successfully" not in end_text:
        raise RuntimeError(
            f"{run_dir.name}: eplusout.end missing completion marker: "
            f"{end_text.strip()!r}"
        )

    err_text = (run_dir / "eplusout.err").read_text(encoding="utf-8", errors="replace")
    if SEVERE_OR_FATAL_RE.search(err_text):
        raise RuntimeError(f"{run_dir.name}: eplusout.err contains Severe/Fatal error")

    match = SEVERE_COUNT_RE.search(err_text)
    if match is None or int(match.group(1)) != 0:
        raise RuntimeError(
            f"{run_dir.name}: eplusout.err missing 0 Severe Errors summary"
        )

    expected_warnings: list[str] = []
    target_upper = EXPECTED_MISSING_VAR.upper()
    for line in err_text.splitlines():
        if target_upper in line.upper():
            expected_warnings.append(line.strip())
    return expected_warnings


def _extract_variable_name(col_name: str) -> str:
    """Extract the EnergyPlus report variable name from a CSV column header.

    Args:
        col_name: Trimmed column header from ``eplusout.csv``.

    Returns:
        Variable name without key prefix, units, or reporting frequency.
    """
    body = col_name.split(":", 1)[1] if ":" in col_name else col_name
    if " [" in body:
        body = body.split(" [", 1)[0]
    elif "(" in body:
        body = body.split("(", 1)[0]
    return body.strip()


def _parse_timestep_csv(
    csv_path: Path, variant_id: str | None
) -> tuple[pd.DataFrame, float]:
    """Parse ``eplusout.csv`` into a clean timestep DataFrame and annual heating.

    Args:
        csv_path: Path to ``eplusout.csv``.
        variant_id: Variant code (e.g. ``"V01"``) or ``None`` for a golden cell.

    Returns:
        Tuple of ``(parquet_dataframe, annual_heating_kwh)``.

    Raises:
        ValueError: If row count, required columns, or NaN checks fail.
    """
    raw_df = pd.read_csv(csv_path, low_memory=False)
    raw_df.columns = [str(col).strip() for col in raw_df.columns]
    if "Date/Time" not in raw_df.columns:
        raise ValueError(f"{csv_path}: missing Date/Time column")

    extracted = raw_df["Date/Time"].astype(str).str.extract(DATE_TIME_RE)
    valid_mask = extracted.notna().all(axis=1)
    filtered_df = raw_df.loc[valid_mask].reset_index(drop=True)
    date_parts = extracted.loc[valid_mask].reset_index(drop=True)

    if len(filtered_df) != EXPECTED_TIMESTEP_ROWS:
        raise ValueError(
            f"{csv_path}: expected {EXPECTED_TIMESTEP_ROWS} timestep rows, "
            f"got {len(filtered_df)}"
        )

    ts_cols = [
        col
        for col in filtered_df.columns
        if col.endswith("(TimeStep)") and not col.endswith("(Hourly)")
    ]
    if not ts_cols:
        raise ValueError(f"{csv_path}: no (TimeStep) columns found")

    if variant_id is not None:
        allowed_vars = list(VARIANT_BASE_VARIABLES)
        if variant_id == "V15":
            allowed_vars.extend(V15_SOLAR_VARIABLES)
        allowed_lower = {name.casefold() for name in allowed_vars}
        selected_cols = [
            col
            for col in ts_cols
            if _extract_variable_name(col).casefold() in allowed_lower
        ]
        found_vars = {_extract_variable_name(col).casefold() for col in selected_cols}
        missing_vars = [
            name for name in allowed_vars if name.casefold() not in found_vars
        ]
        if missing_vars:
            raise ValueError(
                f"{csv_path} ({variant_id}): missing expected columns for "
                f"{missing_vars}"
            )
    else:
        selected_cols = ts_cols

    data_frame = pd.DataFrame(
        {
            "month": date_parts[0].astype(np.int32),
            "day": date_parts[1].astype(np.int32),
            "hour": date_parts[2].astype(np.int32),
            "minute": date_parts[3].astype(np.int32),
        }
    )
    numeric_block = filtered_df[selected_cols].astype(np.float64)
    if numeric_block.isna().any().any():
        bad_cols = [col for col in selected_cols if numeric_block[col].isna().any()]
        raise ValueError(f"{csv_path}: NaN detected in columns {bad_cols}")

    out_df = pd.concat([data_frame, numeric_block], axis=1)

    heating_cols = [
        col
        for col in selected_cols
        if _extract_variable_name(col).casefold()
        == "zone ideal loads zone total heating energy"
    ]
    if len(heating_cols) != 1:
        raise ValueError(
            f"{csv_path}: expected 1 timestep heating energy column, "
            f"found {heating_cols}"
        )
    annual_heating_kwh = float(out_df[heating_cols[0]].sum() / 3.6e6)
    return out_df, annual_heating_kwh


def _resolve_epw_name(cell_id: str, variant_id: str | None) -> str:
    """Resolve the source EPW filename for a golden cell or variant.

    Args:
        cell_id: Golden cell identifier (base cell ID for variants).
        variant_id: Variant code or ``None`` for a golden cell.

    Returns:
        Source EPW filename.
    """
    if variant_id == "V10":
        return "fi_helsinki_tmyx_2009_2023.epw"
    if variant_id == "V11":
        return "ca_montreal_tmyx_2009_2023.epw"
    manifest_path = REP2_DIR / "manifests" / f"{cell_id}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return map_windows_path(manifest["epw_path"]).name


def _extract_eio_version(eio_path: Path) -> str:
    """Read the EnergyPlus version header line from ``eplusout.eio``.

    Args:
        eio_path: Path to ``eplusout.eio``.

    Returns:
        First non-empty line of ``eplusout.eio`` stripped of whitespace.

    Raises:
        ValueError: If ``eplusout.eio`` is empty or lacks ``Program Version``.
    """
    for line in eio_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped:
            if not stripped.startswith("Program Version,"):
                raise ValueError(f"{eio_path}: unexpected first line {stripped!r}")
            return stripped
    raise ValueError(f"{eio_path}: file is empty")


def _compute_variant_changes(
    base_idf: str, variant_idf: str, variant_id: str, base_epw: Path
) -> dict[str, object]:
    """Compute a structured summary of IDF changes for a variant.

    Args:
        base_idf: Prepared base cell 1 IDF text.
        variant_idf: Variant IDF text from the run folder.
        variant_id: Variant code (e.g. ``"V15"``).
        base_epw: Path to base cell 1's source EPW file.

    Returns:
        Dictionary containing ``summary`` and changed ``diff_lines``.
    """
    _, _, note = build_variant_idf(variant_id, base_idf, base_epw)
    diff_lines = [
        line
        for line in difflib.unified_diff(
            base_idf.splitlines(),
            variant_idf.splitlines(),
            n=0,
            lineterm="",
        )
        if line.startswith(("-", "+")) and not line.startswith(("---", "+++"))
    ]
    return {"summary": note, "diff_lines": diff_lines}


def _collect_single_folder(
    rel_folder: str, base_idf: str, base_epw: Path
) -> dict[str, object]:
    """Convert one completed run folder into a golden fixture directory.

    Args:
        rel_folder: Folder path relative to ``GOLDEN_RUNS_DIR``.
        base_idf: Prepared base cell 1 IDF text.
        base_epw: Base cell 1 EPW file path.

    Returns:
        Metadata dictionary written to ``meta.json``.
    """
    run_dir = GOLDEN_RUNS_DIR / rel_folder
    expected_warnings = _validate_eplus_run(run_dir)

    is_variant = rel_folder.startswith("variants/")
    if is_variant:
        folder_name = Path(rel_folder).name
        base_id, variant_id = folder_name.rsplit("__", 1)
    else:
        base_id = rel_folder
        variant_id = None

    out_df, annual_heating_kwh = _parse_timestep_csv(
        run_dir / "eplusout.csv", variant_id
    )

    fixture_dir = GOLDEN_FIXTURES_DIR / rel_folder
    if fixture_dir.exists():
        shutil.rmtree(fixture_dir)
    fixture_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = fixture_dir / "timestep.parquet"
    out_df.to_parquet(
        parquet_path, engine="pyarrow", compression="zstd", index=False
    )

    for fname in REQUIRED_COPY_FILES:
        shutil.copy2(run_dir / fname, fixture_dir / fname)

    eplus_version = _extract_eio_version(run_dir / "eplusout.eio")
    epw_name = _resolve_epw_name(base_id, variant_id)
    epw_sha = _sha256_file(run_dir / "in.epw")
    idf_sha = _sha256_file(run_dir / "in.idf")

    if is_variant:
        assert variant_id is not None
        variant_idf = (run_dir / "in.idf").read_text(encoding="utf-8")
        changed_fields = _compute_variant_changes(
            base_idf, variant_idf, variant_id, base_epw
        )
        meta: dict[str, object] = {
            "cell_id": Path(rel_folder).name,
            "base_cell_id": base_id,
            "variant": variant_id,
            "changed_fields": changed_fields,
            "source_manifest_path": None,
            "epw_file_name": epw_name,
            "epw_sha256": epw_sha,
            "in_idf_sha256": idf_sha,
            "energyplus_version": eplus_version,
            "row_count": int(len(out_df)),
            "column_count": int(len(out_df.columns)),
            "annual_heating_kwh": annual_heating_kwh,
            "manifest_heating_kwh": None,
            "relative_difference": None,
            "expected_warnings": expected_warnings,
        }
    else:
        manifest_path = REP2_DIR / "manifests" / f"{base_id}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_kwh = float(manifest["heating_kwh"])
        rel_diff = (annual_heating_kwh - manifest_kwh) / manifest_kwh
        meta = {
            "cell_id": base_id,
            "source_manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
            "epw_file_name": epw_name,
            "epw_sha256": epw_sha,
            "in_idf_sha256": idf_sha,
            "energyplus_version": eplus_version,
            "row_count": int(len(out_df)),
            "column_count": int(len(out_df.columns)),
            "annual_heating_kwh": annual_heating_kwh,
            "manifest_heating_kwh": manifest_kwh,
            "relative_difference": rel_diff,
            "expected_warnings": expected_warnings,
        }

    (fixture_dir / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return meta


def collect_all() -> int:
    """Collect all completed golden cell and variant runs into Parquet fixtures.

    Returns:
        0 on success, 1 if total fixture size exceeds ``MAX_FIXTURE_TOTAL_MB``.
    """
    folders = read_run_list()
    base_idf = (GOLDEN_RUNS_DIR / BASE_CELL_ID / "in.idf").read_text(
        encoding="utf-8"
    )
    base_manifest = json.loads(
        (REP2_DIR / "manifests" / f"{BASE_CELL_ID}.json").read_text(encoding="utf-8")
    )
    base_epw = map_windows_path(base_manifest["epw_path"])

    cell_metas: list[dict[str, object]] = []
    variant_metas: list[dict[str, object]] = []

    for rel_folder in folders:
        meta = _collect_single_folder(rel_folder, base_idf, base_epw)
        if rel_folder.startswith("variants/"):
            variant_metas.append(meta)
        else:
            cell_metas.append(meta)

    print("=== Golden cells (Mac E+ vs Windows rep2 manifest, D6 info only) ===")
    base_heating_kwh = 0.0
    for meta in cell_metas:
        cell_id = str(meta["cell_id"])
        mac_kwh = float(meta["annual_heating_kwh"])
        man_kwh = float(meta["manifest_heating_kwh"])
        rel_pct = float(meta["relative_difference"]) * 100.0
        if cell_id == BASE_CELL_ID:
            base_heating_kwh = mac_kwh
        print(
            f"  {cell_id}: rows={meta['row_count']}, cols={meta['column_count']}, "
            f"mac={mac_kwh:.6f} kWh, manifest={man_kwh:.6f} kWh, "
            f"rel={rel_pct:+.6f}%"
        )

    print(
        f"\n=== Variants vs base cell 1 ({base_heating_kwh:.6f} kWh) ==="
    )
    for meta in variant_metas:
        var_id = str(meta["variant"])
        var_kwh = float(meta["annual_heating_kwh"])
        delta_kwh = var_kwh - base_heating_kwh
        delta_pct = (delta_kwh / base_heating_kwh) * 100.0
        direction = "above base" if delta_kwh > 0 else "below base"
        print(
            f"  {var_id}: rows={meta['row_count']}, cols={meta['column_count']}, "
            f"heating={var_kwh:.6f} kWh, delta={delta_kwh:+.6f} kWh "
            f"({delta_pct:+.4f}%, {direction})"
        )

    total_bytes = sum(
        p.stat().st_size for p in GOLDEN_FIXTURES_DIR.rglob("*") if p.is_file()
    )
    total_mb = total_bytes / (1024.0 * 1024.0)
    print(
        f"\nTotal fixture size under {GOLDEN_FIXTURES_DIR.relative_to(REPO_ROOT)}: "
        f"{total_mb:.2f} MB ({total_bytes:,} bytes)"
    )
    if total_mb > MAX_FIXTURE_TOTAL_MB:
        print(
            f"ERROR: Total fixture size {total_mb:.2f} MB exceeds "
            f"{MAX_FIXTURE_TOTAL_MB:.1f} MB limit."
        )
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for make_golden.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Prepare, run, and collect golden EnergyPlus fixtures."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare", help="Create run folders and run_list.txt.")
    subparsers.add_parser("run", help="Run EnergyPlus for all folders in run_list.txt.")
    subparsers.add_parser(
        "collect", help="Convert completed E+ outputs into Parquet fixtures."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for scripts/gpusim/make_golden.py.

    Args:
        argv: Optional argument list overriding sys.argv[1:].

    Returns:
        Process exit code (0 on success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "prepare":
        prepare_all()
        return 0
    if args.command == "run":
        return run_all()
    if args.command == "collect":
        return collect_all()
    return 1


if __name__ == "__main__":
    sys.exit(main())
