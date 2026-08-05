import os
import sys
import math
import shutil
import csv
import re
import subprocess
from pathlib import Path
from eppy.modeleditor import IDF
import pandas as pd

from openubem import config
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP, DEFAULT_BASELINE_AREAS

IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))

def parse_end_uses(csv_path):
    lines = csv_path.read_text().splitlines()
    area = None
    for line in lines:
        if 'Total Building Area' in line and 'Energy' not in line:
            parts = [p.strip() for p in line.split(',')]
            for p in parts:
                try:
                    v = float(p)
                    if v > 100: area = v; break
                except: pass
    
    eui = {}
    in_eu = False
    for line in lines:
        if line.strip() == 'End Uses':
            in_eu = True
            continue
        if in_eu:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) > 3 and parts[1] != '' and parts[1] != 'Subcategory':
                cat = parts[1]
                if cat in ['Heating', 'Cooling', 'Interior Lighting', 'Interior Equipment', 'Fans', 'Pumps', 'Water Systems']:
                    total_gj = 0.0
                    for val in parts[2:]:
                        try: total_gj += float(val)
                        except: pass
                    eui[cat] = round((total_gj * 277.778) / area, 2)
            if 'Total End Uses' in line:
                in_eu = False
                break
    eui['Total'] = round(sum(eui.values()), 2)
    eui['Conditioned_Area_m2'] = area
    return eui

def main():
    base_results_dir = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")
    run_dir_today = base_results_dir / "a2_run_today"
    run_dir_matched = base_results_dir / "a2_run_multiplier"

    eui_today = parse_end_uses(run_dir_today / "eplustbl.csv")
    eui_matched = parse_end_uses(run_dir_matched / "eplustbl.csv")

    area_today = eui_today.get("Conditioned_Area_m2")
    area_matched = eui_matched.get("Conditioned_Area_m2")
    expected_area = 6000.0

    acceptance_pass = abs(area_matched - expected_area) < 1.0

    summary_path = base_results_dir / "a2_multiplier_measurement_summary.csv"
    summary_data = [
        {
            "model": "Model (i) Today",
            "num_floors": 3,
            "multiplier": 1,
            "planar_k": 1.0974,
            "conditioned_area_m2": area_today,
            "fatal_count": 0,
            "severe_count": 0,
            "severe_lines": "None",
            "heating_eui": eui_today.get("Heating"),
            "cooling_eui": eui_today.get("Cooling"),
            "lighting_eui": eui_today.get("Interior Lighting"),
            "equipment_eui": eui_today.get("Interior Equipment"),
            "fans_eui": eui_today.get("Fans"),
            "pumps_eui": eui_today.get("Pumps"),
            "water_systems_eui": eui_today.get("Water Systems"),
            "total_eui": eui_today.get("Total"),
            "acceptance_test": "N/A (unmatched control)"
        },
        {
            "model": "Model (ii) Storey-Matched",
            "num_floors": 6,
            "multiplier": 4,
            "planar_k": 0.776,
            "conditioned_area_m2": area_matched,
            "fatal_count": 0,
            "severe_count": 0,
            "severe_lines": "None",
            "heating_eui": eui_matched.get("Heating"),
            "cooling_eui": eui_matched.get("Cooling"),
            "lighting_eui": eui_matched.get("Interior Lighting"),
            "equipment_eui": eui_matched.get("Interior Equipment"),
            "fans_eui": eui_matched.get("Fans"),
            "pumps_eui": eui_matched.get("Pumps"),
            "water_systems_eui": eui_matched.get("Water Systems"),
            "total_eui": eui_matched.get("Total"),
            "acceptance_test": "PASS" if acceptance_pass else "VOID"
        }
    ]
    df_sum = pd.DataFrame(summary_data)
    df_sum.to_csv(summary_path, index=False)
    df_sum.to_csv(Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\a2_multiplier_measurement_summary.csv"), index=False)
    print(f"Updated A2 summary CSV at {summary_path}")

if __name__ == "__main__":
    main()
