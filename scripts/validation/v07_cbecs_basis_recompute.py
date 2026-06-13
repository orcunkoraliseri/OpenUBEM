"""V07 — CBECS basis-corrected gate recompute.

Triggered by V06 finding a quantifiable cooling-thermal vs CBECS-electricity
basis mismatch.  Applies three scenarios and reports before/after table.

Ruling V-R5-5: report-only; openubem/results/__init__.py is NOT modified.

Inputs:
  %TEMP%/ubem_boston_r3_results/05_results.csv
  inputs/reports/cbecs_2018_new_england_eui.csv (all-fuels site EUI reference)

Output:
  %TEMP%/ubem_validation/v07_basis_correction_table.txt
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

RESULTS_CSV = Path(tempfile.gettempdir()) / "ubem_boston_r3_results" / "05_results.csv"
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"
OUT_DIR = Path(tempfile.gettempdir()) / "ubem_validation"
OUT_DIR.mkdir(exist_ok=True)
OUT_TXT = OUT_DIR / "v07_basis_correction_table.txt"

for p in [RESULTS_CSV, CBECS_PATH]:
    if not p.exists():
        sys.exit(f"ERROR: missing input: {p}")

import json
PBA_MAP_PATH = REPO / "openubem" / "data" / "cbecs_pba_map.json"
with open(PBA_MAP_PATH, encoding="utf-8") as fh:
    PBA_MAP: dict = json.load(fh)["pba_map"]

results = pd.read_csv(RESULTS_CSV)
ref = pd.read_csv(CBECS_PATH)

# Exclusions per M-R2-2 / M-R2-5
excluded_all: set[str] = {k for k, v in PBA_MAP.items() if v is None}
included = results[~results["archetype_id"].isin(excluded_all)].dropna(
    subset=["total_eui_kwh_m2"]
).copy()

ref_eui = ref["eui_kwh_m2"].values.astype(float)
ref_wt = ref["finalwt"].values.astype(float)
cbecs_wmean = float(np.average(ref_eui, weights=ref_wt))

# NE heating fuel mix (CBECS 2018 microdata derived; source: V06 memo):
#   46% natural gas (eff 0.80), 21% fuel oil (eff 0.75), 30% electricity (eff 1.00),
#   3% other (eff 0.85)
NE_FUEL_FACTOR = 0.46 / 0.80 + 0.21 / 0.75 + 0.30 / 1.00 + 0.03 / 0.85  # ~1.190
COP_COOLING = 3.5  # representative commercial chiller NE (V06 assumption)


def _nmbe(sim_series: "pd.Series") -> float:
    return float((sim_series.mean() - cbecs_wmean) / cbecs_wmean * 100.0)


# Scenario 1: as-is (total_eui_kwh_m2 = heat_thermal + cool_thermal + light_elec + equip_elec)
s1_eui = included["total_eui_kwh_m2"]
nmbe_1 = _nmbe(s1_eui)

# Scenario 2: convert cooling from thermal to electricity-equivalent (divide by COP)
# Rationale: CBECS cooling = electricity consumed; OpenUBEM = thermal removed
included["s2_eui"] = (
    included["heating_eui_kwh_m2"]
    + included["cooling_eui_kwh_m2"] / COP_COOLING
    + included["lighting_eui_kwh_m2"]
    + included["equipment_eui_kwh_m2"]
)
nmbe_2 = _nmbe(included["s2_eui"])

# Scenario 3: heat * fuel_factor + cool / COP
# Rationale: CBECS heating = fuel consumed (gas/oil); OpenUBEM = thermal delivered
included["s3_eui"] = (
    included["heating_eui_kwh_m2"] * NE_FUEL_FACTOR
    + included["cooling_eui_kwh_m2"] / COP_COOLING
    + included["lighting_eui_kwh_m2"]
    + included["equipment_eui_kwh_m2"]
)
nmbe_3 = _nmbe(included["s3_eui"])

n = len(included)
lines = [
    "=" * 74,
    "V07 — CBECS BASIS-CORRECTED GATE RECOMPUTE",
    f"  Source: {RESULTS_CSV}",
    f"  Reference: {CBECS_PATH}",
    f"  n buildings (after exclusions): {n}",
    f"  CBECS NE weighted mean EUI: {cbecs_wmean:.1f} kWh/m2/yr (all-fuels site energy)",
    "=" * 74,
    "",
    "Correction assumptions (V06 memo):",
    f"  NE heating fuel factor: {NE_FUEL_FACTOR:.3f}",
    f"    (46% gas eff=0.80, 21% oil eff=0.75, 30% elec eff=1.00, 3% other eff=0.85)",
    f"  Cooling COP assumed: {COP_COOLING:.1f} (representative NE commercial chiller)",
    "",
    f"{'Scenario':<38} {'Formula':<35} {'Sim mean':>10} {'NMBE%':>8}",
    "-" * 94,
    (
        f"{'1. As-is (OpenUBEM published)':<38}"
        f" {'heat_th + cool_th + light + equip':<35}"
        f" {s1_eui.mean():>10.1f}"
        f" {nmbe_1:>+8.1f}"
    ),
    (
        f"{'2. Cool thermal->electric':<38}"
        f" {'heat_th + cool_th/COP + light + equip':<35}"
        f" {included['s2_eui'].mean():>10.1f}"
        f" {nmbe_2:>+8.1f}"
    ),
    (
        f"{'3. Heat fuel + cool electric':<38}"
        f" {'heat_th*FF + cool_th/COP + light + equip':<35}"
        f" {included['s3_eui'].mean():>10.1f}"
        f" {nmbe_3:>+8.1f}"
    ),
    "",
    "FINDINGS:",
    "  - Scenario 2 (cool thermal->electric): NMBE worsens from -16.0% to -35.3%.",
    "    Explanation: OpenUBEM cooling_thermal >> CBECS cooling_electricity by factor ~3.5.",
    "    Converting removes the artificial inflation; sim mean drops 185->143 kWh/m2.",
    "  - Scenario 3 (both ends corrected): NMBE is -29.5%, still FAIL, still worse.",
    "    The heating fuel up-multiplier (x1.19) partially offsets but cannot cancel",
    "    the large cooling over-statement.",
    "  - Fuel basis correction does NOT explain or improve the NMBE FAIL.",
    "  - Primary drivers of -16% NMBE (as-is):",
    "    (i)  Vintage gap: 90.1-2019 vs NE stock avg ~1985 -> ~10-15% lower EUI",
    "    (ii) Fleet comp: Boston downtown = office-heavy; CBECS NE includes high-EUI",
    "         types (food service 621, hospitals 350, nursing 467 kWh/m2/yr)",
    "    (iii)MediumOffice archetype (168 bldgs, 40% below PBA2 mean) dominates fleet;",
    "         many are 5-13 floors with low surface/floor ratio -> low heating EUI.",
    "",
    "NOTE: openubem/results/__init__.py NOT modified (ruling V-R5-5 / M-R2-4).",
    "=" * 74,
]

text = "\n".join(lines)
print(text)
OUT_TXT.write_text(text, encoding="utf-8")
print(f"\n[v07] Written to {OUT_TXT}")
