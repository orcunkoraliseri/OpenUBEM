"""Explicit ground-coupling temperature (TechTransfer block 1, Lane A, T1/A02).

EnergyPlus already applies 18 C for every month to any surface whose Outside_Boundary_Condition
is "ground" when no Site:GroundTemperature:BuildingSurface object exists in the IDF. This module
makes that value explicit and citable instead of leaving it as an unstated default -- see
docs/docs_ACTIVE/TechTransfer/2026-09-17_chosen_vs_inherited.md for the rationale (D1: undisturbed
soil temperature explicitly rejected; D3: Site:GroundTemperature:FCfactorMethod not added here).
"""
from geomeppy import IDF as GeomIDF

GROUND_TEMPERATURE_C = 18.0

_MONTH_FIELDS = [
    "January_Ground_Temperature",
    "February_Ground_Temperature",
    "March_Ground_Temperature",
    "April_Ground_Temperature",
    "May_Ground_Temperature",
    "June_Ground_Temperature",
    "July_Ground_Temperature",
    "August_Ground_Temperature",
    "September_Ground_Temperature",
    "October_Ground_Temperature",
    "November_Ground_Temperature",
    "December_Ground_Temperature",
]


def add_ground_temperature(idf: GeomIDF) -> None:
    if idf.idfobjects["SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"]:
        return
    fields = {field: GROUND_TEMPERATURE_C for field in _MONTH_FIELDS}
    idf.newidfobject("SITE:GROUNDTEMPERATURE:BUILDINGSURFACE", **fields)
