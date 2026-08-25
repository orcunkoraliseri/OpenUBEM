"""EU-05 local sizing/design-day acceptance for the runnable S0 fixture."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
from eppy.modeleditor import IDF

from openubem.config import ENERGYPLUS_IDD_PATH, ENERGYPLUS_PATH
from openubem.idf.european_box import add_s0_equivalent_envelope
from openubem.idf.european_controls import add_european_heating_controls


ROOT = Path(__file__).parents[1]
DATA_DIR = ROOT / "openubem" / "data" / "construction"
ENERGYPLUS = ENERGYPLUS_PATH / ("energyplus.exe" if sys.platform == "win32" else "energyplus")


@pytest.fixture(autouse=True)
def _idd() -> None:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))


def _s0_sfh_record() -> dict[str, object]:
    payload = json.loads((DATA_DIR / "tabula_archetypes_es.json").read_text(encoding="utf-8"))
    return next(
        record
        for record in payload["records"]
        if record["archetype_id"] == "ES.ME.SFH.04.Gen.ReEx.001.001"
    )


@pytest.mark.skipif(not ENERGYPLUS.exists(), reason="EnergyPlus 23.1 executable is not installed")
def test_s0_sfh_heating_only_design_day_produces_nonzero_sized_load(tmp_path: Path):
    """EU-05 must survive EnergyPlus zone/system sizing, not only a design-day run."""
    record = _s0_sfh_record()
    path = tmp_path / "s0_sfh_sizing.idf"
    path.write_text(
        """Version,23.1;
Timestep,4;
Building,EU S0 HVAC Sizing,0,Suburbs,0.0001,0.000001,MinimalShadowing,30,1;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,Yes,Yes,No,Yes,No,No,1;
Site:Location,EU Site,40,-75,-5,0;
SizingPeriod:DesignDay,EU Cold Day,1,21,WinterDesignDay,-10,0,,,Wetbulb,-10,,,,,101325,0,0,No,No,No,ASHRAEClearSky,,,,0;
ScheduleTypeLimits,Any Number;
Zone,EU Zone;
Output:Variable,*,Zone Ideal Loads Zone Sensible Heating Rate,Timestep;
""",
        encoding="utf-8",
    )
    idf = IDF(str(path))
    idf.newidfobject(
        "SIZING:ZONE",
        Zone_or_ZoneList_Name="EU Zone",
        Zone_Cooling_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
        Zone_Cooling_Design_Supply_Air_Temperature=13.0,
        Zone_Heating_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
        Zone_Heating_Design_Supply_Air_Temperature=50.0,
        Zone_Cooling_Design_Supply_Air_Humidity_Ratio=0.008,
        Zone_Heating_Design_Supply_Air_Humidity_Ratio=0.008,
    )
    add_s0_equivalent_envelope(idf, record, "EU Zone")
    add_european_heating_controls(idf, record, "EU Zone")
    idf.saveas(str(path))

    result = subprocess.run(
        [str(ENERGYPLUS), "-x", "-r", "-d", str(tmp_path), str(path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
    )
    err = (tmp_path / "eplusout.err").read_text(encoding="utf-8", errors="replace")
    assert result.returncode == 0, err
    assert "Completed Successfully" in err
    assert "Beginning Zone Sizing" in err
    eio = (tmp_path / "eplusout.eio").read_text(encoding="utf-8", errors="replace")
    sized_load_lines = [
        line
        for line in eio.splitlines()
        if line.strip().startswith("Zone Sizing Information,") and ", Heating," in line
    ]
    assert len(sized_load_lines) == 1
    assert float(sized_load_lines[0].split(",")[3]) > 0.0
