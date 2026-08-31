"""The per-cell entry point of the European Step 8 campaign (`EU-08`).

`MVP_european_locations.md` §9.4 makes the GSSCanada 4J side the loop and the OpenUBEM side the
engine.  This module exports exactly one callable, `run_campaign_cell`, which consumes one cell of
the frozen campaign spec and returns one manifest that can prove what the run actually read.

Three constraints are load-bearing and are enforced here rather than documented:

1. The `f>0` lift is carried by the identity of the 10.1 chaining-closure notice, never by a
   boolean.  Every `f>0` cell of the frozen spec reads `schedule_status = BLOCKED_CHAINING_RULE`
   and always will, because a frozen spec is never amended in place.
2. Presence series are read from the ruled binding artefact with its own digests.  The `D-S10-8`
   sort rule is reproducible, but a re-derivation that drifts is undetectable downstream, so it is
   never recomputed here.
3. `diary_origin_hour` and `rotated_to_midnight` are one composed sentence (`FINDING 141`,
   `D-S9-3`).  They are carried together into the manifest and must never be read apart.

The binding carries no occupant semantics: the archetype-to-household pairing is arbitrary but
fixed, never stratum-matched and never representative.  Its own warning text is copied verbatim
into every manifest so no consumer can lose it.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import platform as platform_module
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from openubem.config import ENERGYPLUS_IDD_PATH, ENERGYPLUS_PATH
from openubem.idf.european_box import add_s0_equivalent_envelope
from openubem.idf.european_controls import add_european_heating_controls
from openubem.idf.european_physics import add_european_internal_mass
from openubem.semantic.european_schedules import (
    HOURS_PER_YEAR,
    emit_step8_gain_schedule,

)

ROOT = Path(__file__).resolve().parents[2]
ARCHETYPE_DIR = ROOT / "openubem/data/construction"
ENERGYPLUS_J_TO_KWH = 1.0 / 3.6e6
HEATING_SOURCE = "Zone Ideal Loads Zone Total Heating Energy, hourly variable"

IDF_HEADER_TEMPLATE = """Version,23.1;
Timestep,12;
Building,EU Step8 Campaign Cell,0,City,,,FullExterior,,;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,Yes,Yes,Yes,No,Yes,No,1;
SizingPeriod:WeatherFileDays,AnnualSizingPeriod,1,1,12,31,,No,No;
RunPeriod,RunPeriod1,1,1,,12,31,,,No,No,No,Yes,Yes;
Site:Location,{city},{latitude},{longitude},{time_zone},{elevation};
"""

MANIFEST_FIELDS = (
    "cell_id", "archetype_id", "survey_fold", "sensitivity_f", "control_cell_id",
    "country_stock_code",
    "spec_path", "spec_sha256", "spec_schema_version",
    "binding_path", "binding_sha256", "binding_ruling", "binding_spec_sha256",
    "binding_spec_digest_accepted_by",
    "presence_csv", "presence_sha256", "presence_hid", "presence_source", "presence_n_hours",
    "presence_column_header", "presence_bundle", "presence_bundle_year", "epw_calendar_year",
    "diary_origin_hour", "rotated_to_midnight", "local_time_basis",
    "chaining_rule", "lift_authority",
    "schedule_status_frozen_value", "schedule_status_ignored", "schedule_status_ignored_reason",
    "epw_path", "weather_sha256", "weather_id", "weather_status", "epw_data_period_start_day",
    "idf_path", "idf_sha256", "gain_csv_path", "gain_csv_sha256",
    "energyplus_version", "energyplus_version_declared", "energyplus_version_measured",
    "return_code", "severe_count", "fatal_count", "runtime_s",
    "heating_kwh", "heating_source",
    "completed", "completion_status",
    "occupant_semantics_warning",
    "openubem_git_commit", "platform", "created_utc", "dry_run",
)


class CampaignCellError(RuntimeError):
    """Raised whenever a cell cannot be run with provenance that proves itself."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    return result.stdout.strip() or "unavailable"


def _energyplus_version(exe: Path) -> str:
    try:
        result = subprocess.run(
            [str(exe), "--version"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    stdout = result.stdout.strip()
    if not stdout:
        return "unavailable"
    return stdout.splitlines()[0].strip() or "unavailable"


def _platform_record(exe: Path, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        energyplus_sha256 = "not_run"
    else:
        try:
            energyplus_sha256 = _sha256_file(exe)
        except OSError:
            energyplus_sha256 = "unavailable"
    return {
        "hostname": socket.gethostname(),
        "os": platform_module.platform(),
        "machine": platform_module.machine(),
        "processor": platform_module.processor() or "unavailable",
        "python_version": platform_module.python_version(),
        "energyplus_exe": str(exe),
        "energyplus_sha256": energyplus_sha256,
    }


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise CampaignCellError(f"cannot read {path}") from exc


def verify_spec(cell: Mapping[str, object], spec_path: Path, spec_sha256: str) -> dict[str, Any]:
    """Refuse unless the spec hashes as declared and holds this cell field-for-field."""
    spec_path = Path(spec_path)
    if not spec_path.exists():
        raise CampaignCellError(f"campaign spec not found: {spec_path}")
    actual = _sha256_file(spec_path)
    if actual != spec_sha256:
        raise CampaignCellError(
            f"campaign spec digest mismatch: declared {spec_sha256}, file {actual} ({spec_path})"
        )
    spec = _load_json(spec_path)
    cell_id = cell.get("cell_id")
    matches = [row for row in spec["cells"] if row["cell_id"] == cell_id]
    if not matches:
        raise CampaignCellError(f"cell_id not present in spec: {cell_id!r}")
    frozen = matches[0]
    if dict(cell) != frozen:
        differing = sorted(
            key for key in set(frozen) | set(cell) if cell.get(key) != frozen.get(key)
        )
        raise CampaignCellError(
            f"cell {cell_id!r} differs from the frozen spec on {differing}; the spec is the authority"
        )
    return spec


def verify_weather(cell: Mapping[str, object]) -> tuple[Path, str]:
    """Refuse unless the pinned EPW exists and hashes to the value frozen in the cell."""
    epw_path = ROOT / str(cell["epw_path"])
    if not epw_path.exists():
        raise CampaignCellError(f"pinned EPW not found: {epw_path}")
    actual = _sha256_file(epw_path)
    if actual != cell["weather_sha256"]:
        raise CampaignCellError(
            f"EPW digest mismatch for {cell['cell_id']}: "
            f"frozen {cell['weather_sha256']}, file {actual}"
        )
    start_day = ""
    for line in epw_path.read_text(encoding="utf-8", errors="replace").splitlines()[:10]:
        if line.upper().startswith("DATA PERIODS"):
            fields = line.split(",")
            if len(fields) > 4:
                start_day = fields[4].strip()
            break
    return epw_path, start_day


def _epw_calendar_year(epw_path: Path) -> int | None:
    """Read the calendar year the EPW was pinned to, from its `_yNNNN` filename suffix."""
    match = re.search(r"_y(\d{4})\.epw$", epw_path.name)
    return int(match.group(1)) if match else None


def resolve_lift_authority(
    chaining_notice_path: Path,
    chaining_rule: str,
    *,
    chaining_notice_sha256: str | None = None,
) -> dict[str, str]:
    """Record the `f>0` lift by the notice's identity, never by a frozen boolean field.

    The word check alone is weak: a chaining rule like ``independent`` is ordinary English, so any
    document containing that word would satisfy it.  When ``chaining_notice_sha256`` is supplied the
    digest is checked first and a mismatch is a refusal; the word check stays as the second
    condition, so a correctly-hashed notice that does not name the rule is still refused.
    """
    notice_path = Path(chaining_notice_path)
    if not notice_path.exists():
        raise CampaignCellError(
            f"the f>0 lift notice is missing: {notice_path}; f>0 emission stays blocked"
        )
    text = notice_path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        raise CampaignCellError(f"the f>0 lift notice is empty: {notice_path}")
    actual = _sha256_file(notice_path)
    if chaining_notice_sha256 is not None and actual != chaining_notice_sha256:
        raise CampaignCellError(
            f"f>0 lift notice digest mismatch: declared {chaining_notice_sha256}, "
            f"file {actual} ({notice_path})"
        )
    if not re.search(rf"\b{re.escape(chaining_rule)}\b", text):
        raise CampaignCellError(
            f"the lift notice does not name the chaining rule {chaining_rule!r}: {notice_path}"
        )
    return {
        "notice_path": str(notice_path),
        "notice_sha256": actual,
        "notice_sha256_declared": chaining_notice_sha256,
        "rule_named_by_notice": chaining_rule,
    }


def _read_presence_series(path: Path) -> tuple[np.ndarray, str | None]:
    """Read a shipped presence artefact, which carries one header line naming its household.

    `read_presence_csv` is the headerless contract of the OpenUBEM emitter; the 4J bundles ship a
    named column instead, and that name is itself provenance worth checking, so it is returned
    rather than discarded.
    """
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise CampaignCellError(f"presence series is empty: {path}")
    header: str | None = None
    try:
        float(lines[0])
    except ValueError:
        header = lines[0]
        lines = lines[1:]
    try:
        values = np.asarray([float(line) for line in lines], dtype=float)
    except ValueError as exc:
        raise CampaignCellError(f"presence series holds a non-numeric value: {path}") from exc
    return values, header


def lookup_presence(
    cell: Mapping[str, object],
    binding: Mapping[str, Any],
    schedules_root: Path,
) -> dict[str, Any]:
    """Read the ruled cell -> series pairing from the binding artefact; never re-derive it."""
    fold = str(cell["survey_fold"])
    folds = binding.get("folds", {})
    if fold not in folds:
        raise CampaignCellError(f"binding artefact carries no fold {fold!r}")
    block = folds[fold]
    rows = [row for row in block["binding"] if row["archetype_id"] == cell["archetype_id"]]
    if not rows:
        raise CampaignCellError(
            f"no ruled presence series for ({fold!r}, {cell['archetype_id']!r}) in the binding"
        )
    row = rows[0]
    presence_path = Path(schedules_root) / str(block["bundle"]) / str(row["presence_csv"])
    if not presence_path.exists():
        raise CampaignCellError(f"ruled presence series not found on disk: {presence_path}")
    actual = _sha256_file(presence_path)
    if actual != row["presence_sha256"]:
        raise CampaignCellError(
            f"presence series digest mismatch for {row['presence_csv']}: "
            f"ruled {row['presence_sha256']}, file {actual}"
        )
    values, column_header = _read_presence_series(presence_path)
    if values.shape != (HOURS_PER_YEAR,):
        raise CampaignCellError(
            f"presence series {presence_path} holds {values.shape} values, "
            f"expected ({HOURS_PER_YEAR},)"
        )
    expected_header = f"HH_{fold}_{row['hid']}_Presence"
    if column_header is not None and column_header != expected_header:
        raise CampaignCellError(
            f"presence series {presence_path} declares column {column_header!r}, "
            f"expected {expected_header!r}"
        )
    return {
        "values": values,
        "presence_csv": str(presence_path),
        "presence_sha256": actual,
        "presence_hid": row["hid"],
        "presence_n_hours": int(values.size),
        "presence_column_header": column_header,
        "chaining_rule": str(block["bundle_rule"]),
        "diary_origin_hour": block["diary_origin_hour"],
        "rotated_to_midnight": block["rotated_to_midnight"],
        "bundle": block["bundle"],
        "bundle_year": block["bundle_year"],
    }


def load_archetype_record(country_stock_code: str, archetype_id: str) -> dict[str, Any]:
    path = ARCHETYPE_DIR / f"tabula_archetypes_{str(country_stock_code).lower()}.json"
    if not path.exists():
        raise CampaignCellError(f"no TABULA archetype file for {country_stock_code!r}: {path}")
    for record in _load_json(path)["records"]:
        if record["archetype_id"] == archetype_id:
            return record
    raise CampaignCellError(f"archetype {archetype_id!r} not found in {path}")


def _build_idf(
    cell: Mapping[str, object],
    record: Mapping[str, Any],
    epw_path: Path,
    idf_path: Path,
    gain_csv_path: Path,
    presence: Any,
    chaining_rule: str | None,
) -> dict[str, Any]:
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        location = stream.readline().strip().split(",")
    city = location[1]
    latitude, longitude, time_zone, elevation = (float(value) for value in location[6:10])

    idf_path.parent.mkdir(parents=True, exist_ok=True)
    idf_path.write_text(
        IDF_HEADER_TEMPLATE.format(
            city=city, latitude=latitude, longitude=longitude,
            time_zone=time_zone, elevation=elevation,
        ),
        encoding="utf-8",
    )
    idf = IDF(str(idf_path))
    zone_name = "EU_Cell_Zone"
    idf.newidfobject("ZONE", Name=zone_name)
    idf.newidfobject(
        "SIZING:ZONE",
        Zone_or_ZoneList_Name=zone_name,
        Zone_Cooling_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
        Zone_Cooling_Design_Supply_Air_Temperature=13.0,
        Zone_Heating_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
        Zone_Heating_Design_Supply_Air_Temperature=50.0,
        Zone_Cooling_Design_Supply_Air_Humidity_Ratio=0.008,
        Zone_Heating_Design_Supply_Air_Humidity_Ratio=0.008,
    )
    envelope = add_s0_equivalent_envelope(idf, record, zone_name)
    # The S0 envelope is NoMass throughout, so without this object the zone has
    # literally zero heat capacity and EnergyPlus warns that the solution is
    # unstable.  The campaign's declared capacity is carried by exactly one
    # InternalMass per dwelling, as run_eu_s2_campaign.py:244 already does.
    add_european_internal_mass(
        idf, zone_name, float(record["geometry"]["a_c_ref_m2"]),
        c_m_wh_m2k=float(record["c_m_wh_m2k"]),
    )
    names = add_european_heating_controls(idf, record, zone_name)
    legacy_gain = idf.getobject("OTHEREQUIPMENT", names["gains"])
    if legacy_gain is not None:
        idf.removeidfobject(legacy_gain)
    existing_limits = idf.getobject("SCHEDULETYPELIMITS", "EU_Step8_AnyNumber_Wm2")
    if existing_limits is not None:
        idf.removeidfobject(existing_limits)
    emitted = emit_step8_gain_schedule(
        idf,
        sensitivity_f=float(cell["sensitivity_f"]),
        dwelling_zone=zone_name,
        dwelling_id=str(cell["cell_id"]),
        emitted_csv_path=gain_csv_path,
        presence=presence,
        chaining_rule=chaining_rule,
    )
    idf.newidfobject(
        "OUTPUT:VARIABLE", Key_Value="*",
        Variable_Name="Zone Ideal Loads Zone Total Heating Energy",
        Reporting_Frequency="Hourly",
    )
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
    idf.saveas(str(idf_path))
    return {"emitted": emitted, "envelope": envelope}


def _extract_heating_kwh(csv_path: Path) -> float:
    import csv as _csv

    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = _csv.DictReader(stream)
        if not reader.fieldnames:
            raise CampaignCellError(f"eplusout.csv has no header: {csv_path}")
        columns = [
            field for field in reader.fieldnames
            if "zone ideal loads zone total heating energy" in field.casefold()
            and "[j]" in field.casefold() and "(hourly)" in field.casefold()
        ]
        if not columns:
            raise CampaignCellError(f"eplusout.csv lacks hourly heating energy: {csv_path}")
        total_j = 0.0
        for row in reader:
            total_j += sum(float(row[column]) for column in columns)
    return total_j * ENERGYPLUS_J_TO_KWH


def _energyplus_exe() -> Path:
    candidate = Path(ENERGYPLUS_PATH)
    if candidate.is_dir():
        return candidate / ("energyplus.exe" if sys.platform == "win32" else "energyplus")
    return candidate


def _run_energyplus(idf_path: Path, epw_path: Path, run_dir: Path, timeout: int) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(
        [str(_energyplus_exe()), "-x", "-r", "-w", str(epw_path), "-d", str(run_dir), str(idf_path)],
        cwd=run_dir, capture_output=True, text=True, timeout=timeout,
    )
    err_path = run_dir / "eplusout.err"
    err = err_path.read_text(encoding="utf-8", errors="replace") if err_path.exists() else ""
    csv_path = run_dir / "eplusout.csv"
    heating_kwh = _extract_heating_kwh(csv_path) if csv_path.exists() else None
    return {
        "return_code": result.returncode,
        "severe_count": err.count("** Severe  **"),
        "fatal_count": err.count("**  Fatal  **"),
        "runtime_s": round(time.time() - started, 3),
        "heating_kwh": heating_kwh,
    }


def run_campaign_cell(
    cell: Mapping[str, object],
    *,
    spec_path: Path,
    spec_sha256: str,
    binding_path: Path,
    chaining_notice_path: Path,
    schedules_root: Path,
    chaining_notice_sha256: str | None = None,
    run_root: Path,
    dry_run: bool = False,
    energyplus_timeout: int = 900,
) -> dict[str, Any]:
    """Run one cell of the frozen EU campaign spec and return its self-proving manifest.

    ``cell`` is one element of the spec's ``cells`` array, passed verbatim; it is verified
    field-for-field against the spec at ``spec_path`` before anything is built.  Iteration,
    ordering and concurrency belong to the caller (`EU-08`), never to this function.

    Every input that determines the result is an explicit argument, so a completed run is
    reproducible from its own manifest alone.  The function raises rather than degrades: a missing
    or mis-hashed presence series, and an ``f>0`` cell with no available chaining rule, are both
    invisible in every aggregate and are therefore refusals, never warnings.
    """
    spec = verify_spec(cell, Path(spec_path), spec_sha256)
    epw_path, start_day = verify_weather(cell)

    binding_path = Path(binding_path)
    if not binding_path.exists():
        raise CampaignCellError(f"binding artefact not found: {binding_path}")
    binding = _load_json(binding_path)
    binding_spec_sha256 = str(binding.get("spec", {}).get("sha256", ""))
    invariance = binding.get("binding_invariance")
    covered = (
        isinstance(invariance, dict)
        and spec_sha256 in {str(value) for value in invariance.get("applies_to", ())}
    )
    if binding_spec_sha256 == spec_sha256:
        digest_accepted_by = "exact_match"
    elif covered:
        digest_accepted_by = "binding_invariance_clause_covering_this_digest"
    else:
        raise CampaignCellError(
            f"binding artefact pins spec digest {binding_spec_sha256} but this run executes "
            f"{spec_sha256}; its binding_invariance clause does not name that digest in an "
            "applies_to list, and the mere presence of a clause is not coverage"
        )

    epw_calendar_year = _epw_calendar_year(epw_path)
    sensitivity_f = float(cell["sensitivity_f"])
    if sensitivity_f > 0.0:
        presence_block = lookup_presence(cell, binding, Path(schedules_root))
        bundle_year = int(presence_block["bundle_year"])
        if epw_calendar_year is not None and bundle_year != epw_calendar_year:
            raise CampaignCellError(
                f"calendar mismatch for {cell['cell_id']}: presence bundle "
                f"{presence_block['bundle']} is year {bundle_year} but the pinned EPW "
                f"{epw_path.name} is year {epw_calendar_year}; day types would not align "
                "and no length check can see it (D-S10-7)"
            )
        chaining_rule = presence_block["chaining_rule"]
        lift_authority = resolve_lift_authority(
            Path(chaining_notice_path), chaining_rule,
            chaining_notice_sha256=chaining_notice_sha256,
        )
        presence_values = presence_block["values"]
        presence_source = "eu_cell_presence_binding, ruled D-S10-8"
    else:
        fold_block = binding["folds"][str(cell["survey_fold"])]
        presence_block = {
            "presence_csv": None, "presence_sha256": None, "presence_hid": None,
            "presence_n_hours": None, "presence_column_header": None,
            "bundle": None, "bundle_year": None,
            "diary_origin_hour": fold_block["diary_origin_hour"],
            "rotated_to_midnight": fold_block["rotated_to_midnight"],
        }
        chaining_rule = None
        lift_authority = None
        presence_values = None
        presence_source = "not_required_f0"

    record = load_archetype_record(cell["country_stock_code"], cell["archetype_id"])
    run_dir = Path(run_root) / str(cell["cell_id"])
    run_dir.mkdir(parents=True, exist_ok=True)
    idf_path = Path(run_root) / str(cell["idf_path"])
    gain_csv_path = Path(run_root) / str(cell["gain_csv_path"])
    built = _build_idf(
        cell, record, epw_path, idf_path, gain_csv_path, presence_values, chaining_rule
    )

    energy: dict[str, Any] = {
        "return_code": None, "severe_count": None, "fatal_count": None,
        "runtime_s": None, "heating_kwh": None,
    }
    energyplus_exe = _energyplus_exe()
    if dry_run:
        energyplus_version_measured = "not_run"
    else:
        energy = _run_energyplus(idf_path, epw_path, run_dir, energyplus_timeout)
        energyplus_version_measured = _energyplus_version(energyplus_exe)
    platform_record = _platform_record(energyplus_exe, dry_run)

    if dry_run:
        completed, completion_status = False, "DRY_RUN"
    elif (
        energy["return_code"] != 0
        or energy["fatal_count"]
        or energy["heating_kwh"] is None
    ):
        completed, completion_status = False, "ENGINE_FAILED"
    else:
        completed, completion_status = True, "COMPLETED"

    manifest = {
        "cell_id": cell["cell_id"],
        "archetype_id": cell["archetype_id"],
        "survey_fold": cell["survey_fold"],
        "sensitivity_f": sensitivity_f,
        "control_cell_id": cell["control_cell_id"],
        "country_stock_code": cell["country_stock_code"],
        "spec_path": str(spec_path),
        "spec_sha256": spec_sha256,
        "spec_schema_version": spec.get("schema_version"),
        "binding_path": str(binding_path),
        "binding_sha256": _sha256_file(binding_path),
        "binding_ruling": binding.get("ruling"),
        "binding_spec_sha256": binding_spec_sha256,
        "binding_spec_digest_accepted_by": digest_accepted_by,
        "presence_csv": presence_block["presence_csv"],
        "presence_sha256": presence_block["presence_sha256"],
        "presence_hid": presence_block["presence_hid"],
        "presence_source": presence_source,
        "presence_n_hours": presence_block["presence_n_hours"],
        "presence_column_header": presence_block["presence_column_header"],
        "presence_bundle": presence_block["bundle"],
        "presence_bundle_year": presence_block["bundle_year"],
        "epw_calendar_year": epw_calendar_year,
        "diary_origin_hour": presence_block["diary_origin_hour"],
        "rotated_to_midnight": presence_block["rotated_to_midnight"],
        "local_time_basis": (
            f"diary_origin_hour={presence_block['diary_origin_hour']} AND "
            f"rotated_to_midnight={presence_block['rotated_to_midnight']}; "
            "read together as one sentence, never apart (FINDING 141, D-S9-3)"
        ),
        "chaining_rule": chaining_rule,
        "lift_authority": lift_authority,
        "schedule_status_frozen_value": cell["schedule_status"],
        "schedule_status_ignored": True,
        "schedule_status_ignored_reason": (
            "A frozen spec is never amended in place, so this field is permanently stale for "
            "f>0 cells. The lift is carried by the identity of the 10.1 chaining-closure notice."
        ),
        "epw_path": str(epw_path),
        "weather_sha256": cell["weather_sha256"],
        "weather_id": cell["weather_id"],
        "weather_status": cell["weather_status"],
        "epw_data_period_start_day": start_day,
        "idf_path": str(idf_path),
        "idf_sha256": _sha256_file(idf_path),
        "gain_csv_path": built["emitted"]["csv_path"],
        "gain_csv_sha256": built["emitted"]["sha256"],
        "energyplus_version_declared": "23.1",
        "energyplus_version_measured": energyplus_version_measured,
        "energyplus_version": (
            "23.1" if dry_run else energyplus_version_measured
        ),
        "return_code": energy["return_code"],
        "severe_count": energy["severe_count"],
        "fatal_count": energy["fatal_count"],
        "runtime_s": energy["runtime_s"],
        "heating_kwh": energy["heating_kwh"],
        "heating_source": HEATING_SOURCE,
        "completed": completed,
        "completion_status": completion_status,
        "occupant_semantics_warning": binding.get("semantics_warning"),
        "openubem_git_commit": _git_commit(),
        "platform": platform_record,
        "created_utc": datetime.datetime.now(datetime.timezone.utc)
            .replace(microsecond=0).isoformat(),
        "dry_run": bool(dry_run),
    }

    manifest_path = Path(run_root) / str(cell["manifest_path"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest
