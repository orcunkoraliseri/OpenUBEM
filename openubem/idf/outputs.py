"""Standard EnergyPlus output configuration (DESIGN §3I, fact #26).
Phase-D (§0.1 authorized deviation): HVAC end-use meters added (T04) for metered EUI.
Authorized deviation: DESIGN_step-3...md §3I/§5 extended to include PTAC meters.
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

# T04: HVAC end-use meters for metered cooling/heating/fans EUI (Phase-D §3 mapping).
HVAC_METERS: tuple[str, ...] = (
    "Cooling:Electricity",
    "Heating:Electricity",
    "Heating:NaturalGas",
    "Fans:Electricity",
)


def write_outputs(idf: GeomIDF) -> None:
    """Emit the standard output object set per DESIGN §3I (fact #26)."""
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

    idf.newidfobject("OUTPUTCONTROL:TABLE:STYLE", Column_Separator="HTML")
    idf.newidfobject(
        "OUTPUT:TABLE:SUMMARYREPORTS",
        Report_1_Name="AllSummary",
    )
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
