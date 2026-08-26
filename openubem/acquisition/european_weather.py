"""Deterministic registry and offline validation for the European AMY weather slice.

This module deliberately does *not* retrieve data at import time or during validation.  ERA5
retrieval is an explicit future operation which requires project-owned CDS credentials.  Until
then the registry records the ruled source, station candidates, and gates without pretending that
an EPW file or licence capture exists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import timezone, timedelta
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from openubem.microclimate.epw_hourly import read_epw_hourly
from openubem.results.err_parse import has_fatal, iter_severe


@dataclass(frozen=True)
class EuropeanWeatherTarget:
    """A ruled ERA5 candidate, pending diary-date pinning and live acquisition."""

    fold: str
    city: str
    station: str
    wmo: str
    latitude: float
    longitude: float
    raw_era5_window: str
    local_standard_utc_offset: int
    output_filename: str


EUROPEAN_WEATHER_TARGETS: tuple[EuropeanWeatherTarget, ...] = (
    EuropeanWeatherTarget(
        fold="es", city="Madrid", station="Madrid Barajas/Retiro", wmo="08221",
        latitude=40.45, longitude=-3.55, raw_era5_window="2009-01-01/2010-12-31",
        local_standard_utc_offset=1, output_filename="es_madrid_2009_2010.epw",
    ),
    EuropeanWeatherTarget(
        fold="uk", city="London", station="London Heathrow", wmo="03772",
        latitude=51.48, longitude=-0.45, raw_era5_window="2014-01-01/2015-12-31",
        local_standard_utc_offset=0, output_filename="uk_london_2014_2015.epw",
    ),
    EuropeanWeatherTarget(
        fold="it", city="Bologna", station="Bologna Borgo Panigale/Marconi", wmo="16140",
        latitude=44.53, longitude=11.29, raw_era5_window="2013-01-01/2014-12-31",
        local_standard_utc_offset=1, output_filename="it_bologna_2013_2014.epw",
    ),
)

_REQUIRED_ERA5_VARIABLES = ("2t", "2d", "sp", "10u", "10v", "ssrd", "fdir", "tcc", "tp")
_REQUIRED_EPW_COLUMNS = (
    "dry_bulb_c", "dew_point_c", "relative_humidity_pct", "atmospheric_pressure_pa",
    "global_horizontal_wm2", "direct_normal_wm2", "diffuse_horizontal_wm2",
    "wind_speed_ms", "wind_direction_deg",
)


def cds_credentials_configured(
    *, environ: Mapping[str, str] | None = None, home: Path | None = None
) -> bool:
    """Return whether CDS configuration exists without opening or exposing a secret."""
    env = os.environ if environ is None else environ
    if env.get("CDSAPI_KEY"):
        return True
    if home is None:
        configured_home = env.get("USERPROFILE")
        if not configured_home:
            return False
        base = Path(configured_home)
    else:
        base = Path(home)
    return (base / ".cdsapirc").is_file()


def ruled_not_pinned_registry() -> dict[str, object]:
    """Return the JSON-safe registry state allowed before raw weather is acquired.

    The status is intentionally not promotable by this function: the diary-date pinning,
    licence text served by CDS, file digest, all six gates, and EnergyPlus smoke evidence are
    separate acceptance facts.
    """
    targets = []
    for target in EUROPEAN_WEATHER_TARGETS:
        row = asdict(target)
        row.update({
            "status": "RULED_NOT_PINNED",
            "weather_file": None,
            "sha256": None,
            "licence_text_at_download": None,
            "licence_status": "CAPTURE_AT_DOWNLOAD",
            "diary_window": None,
            "diary_window_status": "RULED_NOT_PINNED",
            "acquisition_status": "BLOCKED_NO_CDS_CREDENTIALS",
            "validation": {
                "gate_1_header": "PENDING_FILE",
                "gate_2_8760_continuity": "PENDING_FILE",
                "gate_3_no_missing_mandatory_fields": "PENDING_FILE",
                "gate_4_physical_and_solar_bounds": "PENDING_FILE",
                "gate_5_monthly_national_benchmark": "PENDING_FILE_AND_BENCHMARK",
                "gate_6_energyplus_smoke": "PENDING_FILE",
            },
        })
        targets.append(row)
    return {
        "schema_version": 1,
        "status": "RULED_NOT_PINNED",
        "source": "ERA5 (Copernicus Climate Change Service)",
        "conversion_route": "cdsapi -> pvlib; Perez/DISC; local standard time without DST",
        "required_era5_variables": list(_REQUIRED_ERA5_VARIABLES),
        "licence_requirement": "Capture the licence text served by CDS at download time; do not substitute a secondary quotation.",
        "targets": targets,
    }


def write_ruled_not_pinned_registry(path: Path | str) -> Path:
    """Write the deterministic pre-acquisition registry; never overwrite an acquired registry."""
    output = Path(path)
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing.get("status") != "RULED_NOT_PINNED":
            raise ValueError(f"refusing to overwrite non-template weather registry: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(ruled_not_pinned_registry(), indent=2) + "\n", encoding="utf-8")
    return output


def sha256_file(path: Path | str) -> str:
    """Return a content digest only after a weather file is actually present."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_epw_preflight(epw_path: Path | str) -> dict[str, object]:
    """Run offline DR08 gates 1--4 for an acquired, non-leap EPW file.

    Gate 5 needs an external national-station monthly benchmark and gate 6 needs an EnergyPlus
    invocation, so neither is represented as passed here.  The caller must attach those two
    evidence records before promoting a registry row.
    """
    epw_path = Path(epw_path)
    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        header = [stream.readline().rstrip("\r\n") for _ in range(8)]
    if not header[0].startswith("LOCATION,"):
        raise ValueError("DR08 gate 1: first EPW header line must start with LOCATION,")
    if any(not line for line in header):
        raise ValueError("DR08 gate 1: EPW requires eight non-empty header lines")

    hourly = read_epw_hourly(epw_path)
    if len(hourly) != 8760:
        raise ValueError(f"DR08 gate 2: expected 8760 non-leap rows, found {len(hourly)}")
    expected = pd.date_range("2001-01-01", periods=8760, freq="h")
    if not hourly.index.equals(expected):
        raise ValueError("DR08 gate 2: month/day/hour rows are not continuous in EPW order")
    if hourly.loc[:, _REQUIRED_EPW_COLUMNS].isna().any().any():
        raise ValueError("DR08 gate 3: mandatory EPW fields contain a missing-value sentinel")

    _check_range(hourly, "dry_bulb_c", -30.0, 50.0)
    if (hourly["dew_point_c"] > hourly["dry_bulb_c"]).any():
        raise ValueError("DR08 gate 4: dew point exceeds dry-bulb temperature")
    _check_range(hourly, "relative_humidity_pct", 0.0, 100.0)
    _check_range(hourly, "atmospheric_pressure_pa", 85000.0, 106000.0)
    _check_range(hourly, "global_horizontal_wm2", 0.0, 1367.0)
    _check_range(hourly, "direct_normal_wm2", 0.0, 1200.0)
    if (hourly["diffuse_horizontal_wm2"] > hourly["global_horizontal_wm2"]).any():
        raise ValueError("DR08 gate 4: diffuse horizontal radiation exceeds global horizontal radiation")
    _check_range(hourly, "wind_speed_ms", 0.0, 45.0)
    _check_range(hourly, "wind_direction_deg", 0.0, 360.0)
    _check_solar_closure(hourly, header[0])

    return {
        "file": str(epw_path),
        "sha256": sha256_file(epw_path),
        "gate_1_header": "PASS",
        "gate_2_8760_continuity": "PASS",
        "gate_3_no_missing_mandatory_fields": "PASS",
        "gate_4_physical_and_solar_bounds": "PASS",
        "gate_5_monthly_national_benchmark": "PENDING_EXTERNAL_BENCHMARK",
        "gate_6_energyplus_smoke": "PENDING_ENERGYPLUS",
    }


def _check_range(hourly: pd.DataFrame, column: str, lower: float, upper: float) -> None:
    values = hourly[column].to_numpy(dtype=float)
    if np.any((values < lower) | (values > upper)):
        raise ValueError(f"DR08 gate 4: {column} outside [{lower}, {upper}]")


def _check_solar_closure(hourly: pd.DataFrame, location_header: str) -> None:
    """Check DR08's daytime GHI = DHI + DNI cos(zenith) tolerance."""
    fields = location_header.split(",")
    try:
        latitude, longitude, utc_offset, elevation = map(float, fields[6:10])
    except (ValueError, IndexError) as exc:
        raise ValueError("DR08 gate 1: LOCATION coordinates/timezone/elevation are invalid") from exc
    from pvlib.solarposition import get_solarposition

    local_time = hourly.index.tz_localize(timezone(timedelta(hours=utc_offset)))
    position = get_solarposition(local_time, latitude=latitude, longitude=longitude, altitude=elevation)
    cosine_zenith = np.cos(np.deg2rad(position["apparent_zenith"].to_numpy()))
    daytime = cosine_zenith > 0.0
    predicted = hourly["diffuse_horizontal_wm2"].to_numpy() + (
        hourly["direct_normal_wm2"].to_numpy() * cosine_zenith
    )
    closure_error = np.abs(hourly["global_horizontal_wm2"].to_numpy() - predicted)
    if np.any(closure_error[daytime] > 5.0):
        raise ValueError("DR08 gate 4: daytime solar closure exceeds 5 W/m2")


def evaluate_monthly_benchmark_gate(
    epw_path: Path | str,
    benchmark_path: Path | str,
    *,
    tolerance_pct: float,
    approved_exception_months: Sequence[int] | None = None,
) -> dict[str, object]:
    """Run DR08 gate 5: EPW monthly GHI totals against a local monthly benchmark.

    Ruled tolerance (DECISION_REQUEST_EU-07_Lyon_gate5_GHI_2026-08-26.md): the DR08 gate
    requires ``|Delta GHI| <= 10%`` per month. This function takes the tolerance as an
    explicit keyword argument rather than hardcoding it, so the caller states the ruled
    value; it is never silently widened here.
    """
    benchmark_path = Path(benchmark_path)
    if not benchmark_path.is_file():
        raise ValueError(f"DR08 gate 5: benchmark file not found: {benchmark_path}")
    try:
        benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"DR08 gate 5: benchmark file is not valid JSON: {benchmark_path}") from exc

    source = benchmark.get("source") if isinstance(benchmark, dict) else None
    monthly_raw = benchmark.get("monthly_ghi_kwh_m2") if isinstance(benchmark, dict) else None
    if not isinstance(source, str) or not source.strip():
        raise ValueError("DR08 gate 5: benchmark JSON must carry a non-empty 'source' label")
    if not isinstance(monthly_raw, list) or len(monthly_raw) != 12:
        raise ValueError("DR08 gate 5: benchmark JSON must carry exactly 12 'monthly_ghi_kwh_m2' values")
    try:
        monthly_benchmark = [float(value) for value in monthly_raw]
    except (TypeError, ValueError) as exc:
        raise ValueError("DR08 gate 5: benchmark monthly GHI values must be numeric") from exc
    if any(value <= 0 for value in monthly_benchmark):
        raise ValueError("DR08 gate 5: benchmark monthly GHI values must be positive")

    hourly = read_epw_hourly(epw_path)
    monthly_epw_wh = hourly.groupby(hourly.index.month)["global_horizontal_wm2"].sum()

    approved = set(approved_exception_months or [])
    months: list[dict[str, object]] = []
    offending_months: list[int] = []
    for month in range(1, 13):
        epw_kwh = float(monthly_epw_wh.loc[month]) / 1000.0
        benchmark_kwh = monthly_benchmark[month - 1]
        pct_difference = abs(epw_kwh - benchmark_kwh) / benchmark_kwh * 100.0
        within_tolerance = pct_difference <= tolerance_pct
        if not within_tolerance:
            offending_months.append(month)
        months.append({
            "month": month,
            "epw_ghi_kwh_m2": epw_kwh,
            "benchmark_ghi_kwh_m2": benchmark_kwh,
            "pct_difference": pct_difference,
            "within_tolerance": within_tolerance,
        })

    if not offending_months:
        verdict = "PASS"
    elif approved and set(offending_months) == approved:
        verdict = "PASS_WITH_DOCUMENTED_EXCEPTION"
    else:
        verdict = "FAIL"

    return {
        "verdict": verdict,
        "tolerance_pct": tolerance_pct,
        "benchmark_source": source,
        "offending_months": offending_months,
        "approved_exception_months": sorted(approved),
        "monthly": months,
    }


DEU18_PREAUTHORISED_FOLDS = ("uk", "it")


def evaluate_deu18_pre_authorisation(
    gate5_result: dict,
    *,
    fold: str,
    other_gate_verdicts: dict[str, str],
) -> dict[str, object]:
    """Evaluate ruling D-EU-18's seven bounds for a gate-5 pre-authorised exception.

    All seven bounds must hold or nothing is granted. Bound 0 (fold pre-authorisation) is
    checked first and short-circuits alone; every other bound is evaluated and every failing
    reason is collected, never short-circuited after the first. ``annual_delta_pct`` is always
    computed and returned, even on refusal.
    """
    monthly = gate5_result["monthly"]
    total_epw = sum(float(row["epw_ghi_kwh_m2"]) for row in monthly)
    total_benchmark = sum(float(row["benchmark_ghi_kwh_m2"]) for row in monthly)
    annual_delta_pct = abs(total_epw - total_benchmark) / total_benchmark * 100.0

    bounds = {
        "max_offending_months": 2,
        "low_irradiance_ceiling_kwh_m2": 80.0,
        "max_relative_delta_pct": 20.0,
        "max_absolute_gap_kwh_m2": 15.0,
        "max_annual_delta_pct": 5.0,
    }

    if fold not in DEU18_PREAUTHORISED_FOLDS:
        return {
            "ruling": "D-EU-18",
            "granted": False,
            "fold": fold,
            "granted_exception_months": [],
            "refusal_reasons": ["FOLD_NOT_PRE_AUTHORISED"],
            "annual_delta_pct": annual_delta_pct,
            "bounds": bounds,
            "measured": [],
        }

    offending_months = list(gate5_result["offending_months"])
    if not offending_months:
        return {
            "ruling": "D-EU-18",
            "granted": False,
            "fold": fold,
            "granted_exception_months": [],
            "refusal_reasons": ["NO_EXCEPTION_NEEDED"],
            "annual_delta_pct": annual_delta_pct,
            "bounds": bounds,
            "measured": [],
        }

    offending_rows = sorted(
        (row for row in monthly if row["month"] in offending_months),
        key=lambda row: row["month"],
    )

    reasons: list[str] = []
    for key, verdict in other_gate_verdicts.items():
        if verdict != "PASS":
            reasons.append(f"GATE_NOT_PASS:{key}={verdict}")

    if len(offending_months) > 2:
        reasons.append(f"TOO_MANY_OFFENDING_MONTHS:{len(offending_months)}")

    for row in offending_rows:
        month = row["month"]
        benchmark_kwh = float(row["benchmark_ghi_kwh_m2"])
        epw_kwh = float(row["epw_ghi_kwh_m2"])
        pct_difference = float(row["pct_difference"])
        absolute_gap = abs(epw_kwh - benchmark_kwh)
        if not benchmark_kwh < 80.0:
            reasons.append(f"MONTH_NOT_LOW_IRRADIANCE:m{month}={benchmark_kwh:.4f}")
        if not pct_difference <= 20.0:
            reasons.append(f"RELATIVE_DELTA_EXCEEDED:m{month}={pct_difference:.4f}")
        if not absolute_gap <= 15.0:
            reasons.append(f"ABSOLUTE_GAP_EXCEEDED:m{month}={absolute_gap:.4f}")

    if not annual_delta_pct <= 5.0:
        reasons.append(f"ANNUAL_DELTA_EXCEEDED:{annual_delta_pct:.4f}")

    granted = not reasons
    measured = [
        {
            "month": row["month"],
            "epw_ghi_kwh_m2": float(row["epw_ghi_kwh_m2"]),
            "benchmark_ghi_kwh_m2": float(row["benchmark_ghi_kwh_m2"]),
            "pct_difference": float(row["pct_difference"]),
            "absolute_gap_kwh_m2": abs(float(row["epw_ghi_kwh_m2"]) - float(row["benchmark_ghi_kwh_m2"])),
        }
        for row in offending_rows
    ]

    return {
        "ruling": "D-EU-18",
        "granted": granted,
        "fold": fold,
        "granted_exception_months": sorted(offending_months) if granted else [],
        "refusal_reasons": reasons,
        "annual_delta_pct": annual_delta_pct,
        "bounds": bounds,
        "measured": measured,
    }


def _gate6_smoke_idf(latitude: float, longitude: float, utc_offset: float, elevation: float) -> str:
    """Minimal single-zone, single-year IDF for the DR08 gate 6 EnergyPlus smoke check.

    A 10 m x 10 m x 3 m box, all six surfaces exposed to the outdoors (floor adiabatic),
    an ideal-loads HVAC system, and a full-year RunPeriod driven entirely by the caller's
    ``-w`` weather file. Geometry reused from the project's own R3 free-float fixture
    (``tests/test_eu_physics_energyplus.py``), only the boundary conditions differ.
    """
    return f"""Version,23.1;
Timestep,4;
Building,Gate6 Smoke,0,Suburbs,0.04,0.4,FullExteriorWithReflections,25,6;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,No,No,No,No,Yes,No;
Site:Location,Gate6 Site,{latitude},{longitude},{utc_offset},{elevation};
RunPeriod,Gate6 Annual,1,1,,12,31,,Sunday,No,No,No,No,No;
ScheduleTypeLimits,Any Number;
Schedule:Compact,Always On,Any Number,Through: 12/31,For: AllDays,Until: 24:00,1;
ScheduleTypeLimits,Temperature,-60,200,Continuous,Temperature;
Schedule:Compact,Heat 20,Temperature,Through: 12/31,For: AllDays,Until: 24:00,20;
Schedule:Compact,Cool 26,Temperature,Through: 12/31,For: AllDays,Until: 24:00,26;
Material,Gate6 Envelope Material,MediumRough,0.2,1.0,1800,900,0.9,0.7,0.7;
Construction,Gate6 Envelope Construction,Gate6 Envelope Material;
Zone,Gate6 Zone,0,0,0,0,1,1,autocalculate,autocalculate;
BuildingSurface:Detailed,Gate6 South,Wall,Gate6 Envelope Construction,Gate6 Zone,,Outdoors,,SunExposed,WindExposed,0.5,4,0,0,0,10,0,0,10,0,3,0,0,3;
BuildingSurface:Detailed,Gate6 North,Wall,Gate6 Envelope Construction,Gate6 Zone,,Outdoors,,SunExposed,WindExposed,0.5,4,10,10,0,0,10,0,0,10,3,10,10,3;
BuildingSurface:Detailed,Gate6 East,Wall,Gate6 Envelope Construction,Gate6 Zone,,Outdoors,,SunExposed,WindExposed,0.5,4,10,0,0,10,10,0,10,10,3,10,0,3;
BuildingSurface:Detailed,Gate6 West,Wall,Gate6 Envelope Construction,Gate6 Zone,,Outdoors,,SunExposed,WindExposed,0.5,4,0,10,0,0,0,0,0,0,3,0,10,3;
BuildingSurface:Detailed,Gate6 Floor,Floor,Gate6 Envelope Construction,Gate6 Zone,,Adiabatic,,NoSun,NoWind,0.5,4,0,0,0,0,10,0,10,10,0,10,0,0;
BuildingSurface:Detailed,Gate6 Roof,Roof,Gate6 Envelope Construction,Gate6 Zone,,Outdoors,,SunExposed,WindExposed,0.5,4,0,0,3,10,0,3,10,10,3,0,10,3;
HVACTemplate:Thermostat,Gate6 Thermostat,Heat 20,,Cool 26,;
HVACTemplate:Zone:IdealLoadsAirSystem,Gate6 Zone,Gate6 Thermostat,Always On,50,13,0.015,0.009,NoLimit,,,NoLimit,,,,,ConstantSensibleHeatRatio,0.7,60,None,30,None,0.00944,0,0,,None,NoEconomizer,None,0,0;
Output:Variable,Gate6 Zone,Zone Air Temperature,Timestep;
Output:Variable,*,Zone Ideal Loads Zone Sensible Heating Rate,Timestep;
Output:SQLite,SimpleAndTabular;
"""


def evaluate_energyplus_smoke_gate(
    epw_path: Path | str,
    *,
    energyplus_root: Path | str,
    timeout_s: int = 600,
) -> dict[str, object]:
    """Run DR08 gate 6: a minimal single-zone IDF through real EnergyPlus against ``epw_path``.

    Returns PASS only when the process returns 0 with zero severe and zero fatal errors.
    Never fabricates a result when EnergyPlus is absent: returns UNAVAILABLE_ENERGYPLUS,
    which is not a pass.
    """
    epw_path = Path(epw_path).resolve()
    energyplus_root = Path(energyplus_root)
    exe_name = "energyplus.exe" if sys.platform == "win32" else "energyplus"
    exe = energyplus_root / exe_name
    if not exe.is_file():
        return {
            "verdict": "UNAVAILABLE_ENERGYPLUS",
            "detail": f"EnergyPlus executable not found at {exe}",
            "energyplus_root": str(energyplus_root),
        }

    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        location_line = stream.readline().rstrip("\r\n")
    fields = location_line.split(",")
    try:
        latitude, longitude, utc_offset, elevation = map(float, fields[6:10])
    except (ValueError, IndexError) as exc:
        raise ValueError("DR08 gate 6: EPW LOCATION header is invalid") from exc

    idf_text = _gate6_smoke_idf(latitude, longitude, utc_offset, elevation)

    with tempfile.TemporaryDirectory(prefix="eu_gate6_smoke_") as tmp:
        run_dir = Path(tmp)
        idf_path = run_dir / "gate6_smoke.idf"
        idf_path.write_text(idf_text, encoding="utf-8")
        command = [str(exe), "-w", str(epw_path), "-d", str(run_dir), "-x", "-r", str(idf_path)]
        t0 = time.monotonic()
        try:
            proc = subprocess.run(command, cwd=run_dir, capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return {
                "verdict": "FAIL",
                "detail": f"EnergyPlus timed out after {timeout_s}s",
                "wall_clock_s": float(timeout_s),
            }
        wall_clock_s = time.monotonic() - t0

        err_path = run_dir / "eplusout.err"
        err_text = err_path.read_text(encoding="utf-8", errors="replace") if err_path.is_file() else ""
        severe_lines = iter_severe(err_text)
        fatal = has_fatal(err_text)

        if proc.returncode != 0:
            detail = "\n".join(severe_lines) or (proc.stderr or proc.stdout)[-2000:]
            return {
                "verdict": "FAIL",
                "detail": detail or f"EnergyPlus returned code {proc.returncode}",
                "returncode": proc.returncode,
                "wall_clock_s": wall_clock_s,
            }
        if fatal or severe_lines:
            detail = "\n".join(severe_lines) or "EnergyPlus reported a fatal error with no severe-line detail"
            return {
                "verdict": "FAIL",
                "detail": detail,
                "returncode": proc.returncode,
                "n_severe": len(severe_lines),
                "wall_clock_s": wall_clock_s,
            }
        return {
            "verdict": "PASS",
            "returncode": proc.returncode,
            "n_severe": 0,
            "wall_clock_s": wall_clock_s,
        }


def evaluate_six_gates(
    epw_path: Path | str,
    *,
    benchmark_path: Path | str,
    tolerance_pct: float,
    energyplus_root: Path | str,
    approved_exception_months: Sequence[int] | None = None,
    energyplus_timeout_s: int = 600,
) -> dict[str, object]:
    """Compose gates 1--4 (existing preflight) with gates 5 and 6 into the registry's six keys."""
    preflight = validate_epw_preflight(epw_path)
    gate_5 = evaluate_monthly_benchmark_gate(
        epw_path, benchmark_path,
        tolerance_pct=tolerance_pct,
        approved_exception_months=approved_exception_months,
    )
    gate_6 = evaluate_energyplus_smoke_gate(
        epw_path, energyplus_root=energyplus_root, timeout_s=energyplus_timeout_s,
    )
    return {
        "gate_1_header": preflight["gate_1_header"],
        "gate_2_8760_continuity": preflight["gate_2_8760_continuity"],
        "gate_3_no_missing_mandatory_fields": preflight["gate_3_no_missing_mandatory_fields"],
        "gate_4_physical_and_solar_bounds": preflight["gate_4_physical_and_solar_bounds"],
        "gate_5_monthly_national_benchmark": gate_5["verdict"],
        "gate_6_energyplus_smoke": gate_6["verdict"],
    }
