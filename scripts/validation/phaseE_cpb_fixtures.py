"""CP-B fixture validation: 5-archetype IDFs with Phase-E service loads.

Builds one IDF per archetype, runs through EnergyPlus 23.1 locally, and verifies:
  - rc=0, 0 fatal errors
  - service-load meters report non-zero values
  - HighriseApartment WLHP loop temp < 100 °C (multi-zone geometry)
"""
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.cooking import assign_cooking
from openubem.idf.dhw import assign_dhw
from openubem.idf.hvac import assign_hvac
from openubem.idf.outputs import write_outputs
from openubem.idf.refrigeration import assign_refrigeration

EPW = Path(r"C:\EnergyPlusV23-1-0\WeatherData\USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")
EP_EXE = Path(r"C:\EnergyPlusV23-1-0\EnergyPlus.exe")
TEMPLATES_DIR = ROOT / "openubem" / "idf" / "templates"
OUT_DIR = ROOT / "openubem" / "outputs" / "cpb_fixtures"

# (archetype_id, template, num_stories, footprint_m2, expected_nonzero_service_meters)
FIXTURES = [
    (
        "LargeOffice",
        "commercial_base.idf",
        1,
        400.0,
        ["WaterSystems:NaturalGas"],
    ),
    (
        "HighriseApartment",
        "residential_base.idf",
        9,
        1000.0,  # larger footprint → realistic distributed WLHP loads
        ["WaterSystems:NaturalGas"],
    ),
    (
        "FullServiceRestaurant",
        "commercial_base.idf",
        1,
        400.0,
        [
            "WaterSystems:NaturalGas",
            "InteriorEquipment:NaturalGas",
            "Cooking:InteriorEquipment:Electricity",
            "Refrigeration:InteriorEquipment:Electricity",
        ],
    ),
    (
        "SuperMarket",
        "commercial_base.idf",
        1,
        4000.0,  # reference store ~4181 m²; scale cases proportionally
        [
            "WaterSystems:Electricity",
            "Cooking:InteriorEquipment:Electricity",
            "Refrigeration:Electricity",
        ],
    ),
    (
        "LargeHotel",
        "commercial_base.idf",
        1,
        400.0,
        [
            "WaterSystems:NaturalGas",
            "InteriorEquipment:NaturalGas",
            "Cooking:InteriorEquipment:Electricity",
            "Refrigeration:InteriorEquipment:Electricity",
        ],
    ),
]


def _setup_idf(template_name: str) -> IDF:
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(TEMPLATES_DIR / template_name))


def _sched_once(idf, name: str, value: float) -> None:
    if not any(s.Name == name for s in idf.idfobjects.get("SCHEDULE:CONSTANT", [])):
        s = idf.newidfobject("SCHEDULE:CONSTANT")
        s.Name = name
        s.Hourly_Value = value


def _add_zone_loads(idf, zone_name: str) -> None:
    """Minimal PEOPLE + LIGHTS + ELECTRICEQUIPMENT + HVACTEMPLATE:THERMOSTAT per zone."""
    _sched_once(idf, "CPB_Heating_SP", 21.0)
    _sched_once(idf, "CPB_Cooling_SP", 24.0)
    _sched_once(idf, "CPB_OccLoad", 1.0)

    tstat = idf.newidfobject("HVACTEMPLATE:THERMOSTAT")
    tstat.Name = f"{zone_name}_Thermostat"
    tstat.Heating_Setpoint_Schedule_Name = "CPB_Heating_SP"
    tstat.Cooling_Setpoint_Schedule_Name = "CPB_Cooling_SP"

    ppl = idf.newidfobject("PEOPLE")
    ppl.Name = f"People_{zone_name}"
    ppl.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    ppl.Number_of_People_Schedule_Name = "CPB_OccLoad"
    ppl.Number_of_People_Calculation_Method = "People/Area"
    ppl.People_per_Floor_Area = 0.05
    ppl.Activity_Level_Schedule_Name = "Activity_Level"
    ppl.Fraction_Radiant = 0.3

    lights = idf.newidfobject("LIGHTS")
    lights.Name = f"Lights_{zone_name}"
    lights.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    lights.Schedule_Name = "CPB_OccLoad"
    lights.Design_Level_Calculation_Method = "Watts/Area"
    lights.Watts_per_Zone_Floor_Area = 10.0
    lights.Fraction_Radiant = 0.42

    equip = idf.newidfobject("ELECTRICEQUIPMENT")
    equip.Name = f"Equip_{zone_name}"
    equip.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    equip.Schedule_Name = "CPB_OccLoad"
    equip.Design_Level_Calculation_Method = "Watts/Area"
    equip.Watts_per_Zone_Floor_Area = 8.0
    equip.Fraction_Radiant = 0.5


def build_fixture(arch: str, template: str, n_stories: int, footprint: float) -> Path:
    """Build one IDF and return its path."""
    idf = _setup_idf(template)
    coords = [(0, 0), (20, 0), (20, 20), (0, 20)]
    idf.add_block(name=arch, coordinates=coords, height=3.0, num_stories=n_stories)
    idf.intersect_match()
    idf.set_default_constructions()

    zone_dicts = [{"name": z.Name} for z in idf.idfobjects["ZONE"]]
    for zd in zone_dicts:
        _add_zone_loads(idf, zd["name"])

    row = pd.Series({"archetype_id": arch, "footprint_area_m2": footprint})
    assign_hvac(idf, row, zone_dicts)
    assign_dhw(idf, row, zone_dicts)
    assign_cooking(idf, row, zone_dicts)
    assign_refrigeration(idf, row, zone_dicts)
    write_outputs(idf)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    idf_path = OUT_DIR / f"cpb_{arch}.idf"
    idf.save(str(idf_path))
    return idf_path


def run_energyplus(idf_path: Path, ep_out: Path) -> tuple[int, int, int, float]:
    ep_out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    cmd = [str(EP_EXE), "-x", "-w", str(EPW), "-d", str(ep_out), str(idf_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    elapsed = round(time.time() - t0, 1)

    err_file = ep_out / "eplusout.err"
    fatal = severe = 0
    if err_file.exists():
        txt = err_file.read_text(encoding="utf-8", errors="replace")
        fatal = txt.count("** Fatal  **") + txt.count("**  Fatal  **")
        severe = txt.count("** Severe **") + txt.count("**  Severe  **")

    return proc.returncode, fatal, severe, elapsed


def query_meters(ep_out: Path) -> dict[str, float]:
    """Return {meter_name: value_J} from run-period ReportData (E+ 23.1 schema).

    E+ 23.1 uses ReportData / ReportDataDictionary (not ReportMeterData).
    RunPeriod rows have WarmupFlag=NULL; Name column holds the meter key.
    """
    sql_file = ep_out / "eplusout.sql"
    if not sql_file.exists():
        return {}
    try:
        con = sqlite3.connect(str(sql_file))
        cur = con.execute("""
            SELECT d.Name, r.Value
            FROM ReportData r
            JOIN ReportDataDictionary d
              ON d.ReportDataDictionaryIndex = r.ReportDataDictionaryIndex
            WHERE d.ReportingFrequency = 'Run Period'
        """)
        rows = cur.fetchall()
        con.close()
        return {r[0]: (r[1] or 0.0) for r in rows}
    except Exception as exc:
        print(f"  [SQL query error: {exc}]")
        return {}


def check_wlhp_max_temp(ep_out: Path) -> float | None:
    """Scan err file for WLHP outlet temperature warnings and return the maximum found."""
    err_file = ep_out / "eplusout.err"
    if not err_file.exists():
        return None
    pat = re.compile(r"outlet temperature.*?(\d+\.?\d*)\s*(?:C\b|°C)", re.IGNORECASE)
    max_t: float | None = None
    for line in err_file.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pat.search(line)
        if m:
            t = float(m.group(1))
            if max_t is None or t > max_t:
                max_t = t
    return max_t


def main() -> int:
    print(f"CP-B Phase-E fixture validation — {len(FIXTURES)} archetypes")
    print(f"EPW : {EPW}")
    print(f"EXE : {EP_EXE}")
    print()

    rows = []
    for arch, template, n_stories, footprint, expected_meters in FIXTURES:
        ep_out = OUT_DIR / arch

        print(f"[{arch}] building IDF ({n_stories} stor{'y' if n_stories == 1 else 'ies'}) ...", end="", flush=True)
        idf_path = build_fixture(arch, template, n_stories, footprint)
        print(" running E+ ...", end="", flush=True)

        rc, fatal, severe, elapsed = run_energyplus(idf_path, ep_out)
        meters = query_meters(ep_out)
        wlhp_max = check_wlhp_max_temp(ep_out) if arch == "HighriseApartment" else None

        missing = [m for m in expected_meters if meters.get(m, 0.0) <= 0.0]
        wlhp_ok = (wlhp_max is None) or (wlhp_max < 100.0)
        status = "PASS" if (rc == 0 and fatal == 0 and not missing and wlhp_ok) else "FAIL"
        print(f" {status}  (rc={rc} fatal={fatal} severe={severe} {elapsed}s)")

        if missing:
            print(f"  MISSING/ZERO meters: {missing}")
        if wlhp_max is not None:
            tag = "OK" if wlhp_ok else "EXCEEDS 100 C"
            print(f"  WLHP max outlet temp: {wlhp_max:.1f} C  [{tag}]")

        # Print service meter values for traceability
        for m in expected_meters:
            val = meters.get(m, 0.0)
            kwh = val / 3_600_000
            print(f"    {m}: {kwh:,.1f} kWh")

        rows.append({
            "archetype": arch,
            "rc": rc,
            "fatal": fatal,
            "severe": severe,
            "elapsed_s": elapsed,
            "missing_meters": "; ".join(missing) if missing else "none",
            "wlhp_max_c": f"{wlhp_max:.1f}" if wlhp_max is not None else "n/a",
            "status": status,
        })
        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for r in rows:
        print(
            f"  {r['archetype']:25s}  {r['status']:4s}  "
            f"rc={r['rc']}  fatal={r['fatal']}  severe={r['severe']}  {r['elapsed_s']}s"
        )

    all_pass = all(r["status"] == "PASS" for r in rows)
    print()
    print(f"CP-B outcome: {'ALL PASS' if all_pass else 'FAILURES — see above'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
