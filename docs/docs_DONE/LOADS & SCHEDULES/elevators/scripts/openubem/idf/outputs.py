"""Standard EnergyPlus output configuration (DESIGN §3I, fact #26).
Phase-D (§0.1 authorized deviation): HVAC end-use meters added (T04) for metered EUI.
Authorized deviation: DESIGN_step-3...md §3I/§5 extended to include PTAC meters.
T08 (resolution-mode sweep): InteriorLights and InteriorEquipment meters added so
trim_hourly=True skips per-zone hourly variables without losing any end-use data.
"""
import eppy.bunch_subclass
from geomeppy import IDF as GeomIDF

# 11 hourly output variables per DESIGN §3I lines 426-463.
STANDARD_OUTPUTS: list[tuple[str, str]] = [
    ("Zone Ideal Loads Zone Total Heating Energy", "Hourly"),
    ("Zone Ideal Loads Zone Total Cooling Energy", "Hourly"),
    ("Zone People Occupant Count", "Hourly"),
    ("Zone Lights Electricity Energy", "Hourly"),
    ("Zone Electric Equipment Electricity Energy", "Hourly"),
    ("Zone Infiltration Sensible Heat Loss Energy", "Hourly"),
    ("Zone Mechanical Ventilation Mass Flow Rate", "Hourly"),
    ("Zone Mean Air Temperature", "Hourly"),
    ("Zone Operative Temperature", "Hourly"),
    ("Site Outdoor Air Drybulb Temperature", "Hourly"),
    ("Site Wind Speed", "Hourly"),
]

# T04/T12: HVAC + Phase-E service-load end-use meters (RunPeriod, stored in SQL for parser).
# T08: InteriorLights:Electricity + InteriorEquipment:Electricity added so that trim_hourly=True
# runs can parse all 9 end-uses from RunPeriod meters alone (no hourly zone variables needed).
HVAC_METERS: tuple[str, ...] = (
    "Cooling:Electricity",
    "Heating:Electricity",
    "Heating:NaturalGas",
    "Fans:Electricity",
    "Pumps:Electricity",
    "WaterSystems:NaturalGas",
    "WaterSystems:Electricity",
    "Refrigeration:Electricity",
    "InteriorEquipment:NaturalGas",
    "Cooking:InteriorEquipment:Electricity",
    "Refrigeration:InteriorEquipment:Electricity",
    "Elevators:InteriorEquipment:Electricity",
    "InteriorLights:Electricity",
    "InteriorEquipment:Electricity",
)


def write_outputs(idf: GeomIDF, trim_hourly: bool = False) -> None:
    """Emit the standard output object set per DESIGN §3I (fact #26).

    trim_hourly=True: skip per-zone hourly Output:Variable and HTML table objects.
    All 9 end-uses remain readable from RunPeriod meters. Use for large many-zone
    fleets (fast_zone city sweeps) where hourly zone data would create >100 GB SQL.
    """
    if not trim_hourly:
        for var_name, freq in STANDARD_OUTPUTS:
            idf.newidfobject(
                "OUTPUT:VARIABLE",
                Key_Value="*",
                Variable_Name=var_name,
                Reporting_Frequency=freq,
            )

    for meter in ("Electricity:Facility", "NaturalGas:Facility"):
        obj = idf.newidfobject("OUTPUT:METER:METERFILEONLY")
        try:
            obj.Key_Name = meter  # eppy >= 0.5.69
        except eppy.bunch_subclass.BadEPFieldError:
            obj.Name = meter  # eppy < 0.5.69
        obj.Reporting_Frequency = "RunPeriod"

    # T04 Phase-D: HVAC end-use meters stored in SQL (not meter-file-only) so parser can read them.
    for meter in HVAC_METERS:
        obj = idf.newidfobject("OUTPUT:METER")
        try:
            obj.Key_Name = meter
        except eppy.bunch_subclass.BadEPFieldError:
            obj.Name = meter
        obj.Reporting_Frequency = "RunPeriod"

    if not trim_hourly:
        idf.newidfobject("OUTPUTCONTROL:TABLE:STYLE", Column_Separator="HTML")
        idf.newidfobject(
            "OUTPUT:TABLE:SUMMARYREPORTS",
            Report_1_Name="AllSummary",
        )
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
