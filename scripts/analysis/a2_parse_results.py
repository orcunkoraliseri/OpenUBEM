import os
import sys
import math
import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

def parse_ep_htm(htm_path: Path) -> dict:
    if not htm_path.exists():
        return {}
    
    soup = BeautifulSoup(htm_path.read_text(errors="replace"), "html.parser")
    
    total_area_m2 = 0.0
    # Extract total gross floor area from Building Summary
    for tr in soup.find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(cols) >= 2 and "Total gross floor area [m2]" in cols[0]:
            try:
                total_area_m2 = float(cols[1])
            except ValueError:
                pass

    # Extract End Uses table (Energy Use [GJ])
    # Table header contains 'Electricity Energy Use [GJ]'
    end_uses_gj = {
        "Heating": 0.0,
        "Cooling": 0.0,
        "Lighting": 0.0,
        "Equipment": 0.0,
        "Fans": 0.0,
        "Pumps": 0.0,
        "Water Systems": 0.0
    }

    for t in soup.find_all("table"):
        t_text = t.get_text()
        if "Electricity Energy Use [GJ]" in t_text and "Heating" in t_text:
            for tr in t.find_all("tr"):
                cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if not cols:
                    continue
                cat_raw = cols[0]
                
                # Check key categories
                cat_key = None
                if cat_raw.startswith("Heating"):
                    cat_key = "Heating"
                elif cat_raw.startswith("Cooling"):
                    cat_key = "Cooling"
                elif "Lighting" in cat_raw:
                    cat_key = "Lighting"
                elif "Equipment" in cat_raw:
                    cat_key = "Equipment"
                elif cat_raw.startswith("Fans"):
                    cat_key = "Fans"
                elif cat_raw.startswith("Pumps"):
                    cat_key = "Pumps"
                elif "Water" in cat_raw:
                    cat_key = "Water Systems"

                if cat_key and len(cols) >= 3:
                    # Sum all GJ energy columns (Electricity=col 1, Gas=col 3, etc.)
                    tot_gj_cat = 0.0
                    for idx in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
                        if idx < len(cols):
                            try:
                                tot_gj_cat += float(cols[idx])
                            except ValueError:
                                pass
                    end_uses_gj[cat_key] += tot_gj_cat

    # Convert GJ to kWh/m2 (1 GJ = 277.778 kWh)
    area_ref = total_area_m2 if total_area_m2 > 0 else 1.0
    eui_kwh_m2 = {}
    for cat, gj in end_uses_gj.items():
        eui_kwh_m2[cat] = round((gj * 277.778) / area_ref, 2)

    total_eui = round(sum(eui_kwh_m2.values()), 2)

    return {
        "conditioned_area_m2": total_area_m2,
        "eui_kwh_m2": eui_kwh_m2,
        "total_eui": total_eui
    }

def main():
    base_results_dir = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")
    run_dir_today = base_results_dir / "a2_run_today"
    run_dir_matched = base_results_dir / "a2_run_multiplier"

    htm_today = run_dir_today / "eplustbl.htm"
    err_today = run_dir_today / "eplusout.err"
    rep_today = parse_ep_htm(htm_today)
    err_text_today = err_today.read_text() if err_today.exists() else ""
    sev_today = [l.strip() for l in err_text_today.splitlines() if "**  Severe  **" in l]
    fat_today = [l.strip() for l in err_text_today.splitlines() if "**  Fatal  **" in l]

    htm_matched = run_dir_matched / "eplustbl.htm"
    err_matched = run_dir_matched / "eplusout.err"
    rep_matched = parse_ep_htm(htm_matched)
    err_text_matched = err_matched.read_text() if err_matched.exists() else ""
    sev_matched = [l.strip() for l in err_text_matched.splitlines() if "**  Severe  **" in l]
    fat_matched = [l.strip() for l in err_text_matched.splitlines() if "**  Fatal  **" in l]

    print("=== A2 MEASUREMENT PARSED RESULTS ===")
    print("\nMODEL (i) TODAY'S CODE:")
    print(f"  Conditioned Area: {rep_today.get('conditioned_area_m2')} m2")
    print(f"  Fatal Count: {len(fat_today)}, Severe Count: {len(sev_today)}")
    print(f"  EUI: {rep_today.get('eui_kwh_m2')}, Total: {rep_today.get('total_eui')} kWh/m2/yr")

    print("\nMODEL (ii) STOREY-MATCHED CODE (Zone Multiplier = 4):")
    print(f"  Conditioned Area: {rep_matched.get('conditioned_area_m2')} m2")
    print(f"  Fatal Count: {len(fat_matched)}, Severe Count: {len(sev_matched)}")
    print(f"  EUI: {rep_matched.get('eui_kwh_m2')}, Total: {rep_matched.get('total_eui')} kWh/m2/yr")

    summary_data = [
        {
            "model": "Model (i) Today",
            "num_floors": 3,
            "multiplier": 1,
            "planar_k": 1.0974,
            "conditioned_area_m2": rep_today.get("conditioned_area_m2"),
            "fatal_count": len(fat_today),
            "severe_count": len(sev_today),
            "severe_lines": "; ".join(sev_today) if sev_today else "None",
            "heating_eui": rep_today.get("eui_kwh_m2", {}).get("Heating"),
            "cooling_eui": rep_today.get("eui_kwh_m2", {}).get("Cooling"),
            "lighting_eui": rep_today.get("eui_kwh_m2", {}).get("Lighting"),
            "equipment_eui": rep_today.get("eui_kwh_m2", {}).get("Equipment"),
            "fans_eui": rep_today.get("eui_kwh_m2", {}).get("Fans"),
            "pumps_eui": rep_today.get("eui_kwh_m2", {}).get("Pumps"),
            "water_systems_eui": rep_today.get("eui_kwh_m2", {}).get("Water Systems"),
            "total_eui": rep_today.get("total_eui")
        },
        {
            "model": "Model (ii) Storey-Matched",
            "num_floors": 6,
            "multiplier": 4,
            "planar_k": 0.7760,
            "conditioned_area_m2": rep_matched.get("conditioned_area_m2"),
            "fatal_count": len(fat_matched),
            "severe_count": len(sev_matched),
            "severe_lines": "; ".join(sev_matched) if sev_matched else "None",
            "heating_eui": rep_matched.get("eui_kwh_m2", {}).get("Heating"),
            "cooling_eui": rep_matched.get("eui_kwh_m2", {}).get("Cooling"),
            "lighting_eui": rep_matched.get("eui_kwh_m2", {}).get("Lighting"),
            "equipment_eui": rep_matched.get("eui_kwh_m2", {}).get("Equipment"),
            "fans_eui": rep_matched.get("eui_kwh_m2", {}).get("Fans"),
            "pumps_eui": rep_matched.get("eui_kwh_m2", {}).get("Pumps"),
            "water_systems_eui": rep_matched.get("eui_kwh_m2", {}).get("Water Systems"),
            "total_eui": rep_matched.get("total_eui")
        }
    ]

    out_csv1 = base_results_dir / "a2_multiplier_measurement_summary.csv"
    out_csv2 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\a2_multiplier_measurement_summary.csv")

    df_sum = pd.DataFrame(summary_data)
    df_sum.to_csv(out_csv1, index=False)
    df_sum.to_csv(out_csv2, index=False)
    print(f"\nWrote summary CSV to {out_csv1} and {out_csv2}")

if __name__ == "__main__":
    main()
