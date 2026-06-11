"""Standard EnergyPlus output configuration (DESIGN §3I, fact #26)."""
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

    idf.newidfobject("OUTPUTCONTROL:TABLE:STYLE", Column_Separator="HTML")
    idf.newidfobject(
        "OUTPUT:TABLE:SUMMARYREPORTS",
        Report_1_Name="AllSummary",
    )
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
