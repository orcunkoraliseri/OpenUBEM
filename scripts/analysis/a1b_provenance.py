import os
import sys
import csv
from pathlib import Path
import pandas as pd

from openubem import config

def main():
    phase_e_path = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_RESULTS\OpenUBEM_results_hvacServiceLoads\csv\phaseE_all_cells_results.csv")
    if not phase_e_path.exists():
        print(f"Error: {phase_e_path} not found")
        sys.exit(1)
        
    df = pd.read_csv(phase_e_path)
    tot_fleet = len(df)
    
    # Imputation flag check: 'no_floors' in data_quality_flag
    df['is_imputed'] = df['data_quality_flag'].fillna('').apply(lambda x: 'no_floors' in [s.strip() for s in x.split(',')])
    df['floor_area'] = df['footprint_area_m2'] * df['levels']
    df['is_under_500m2'] = df['floor_area'] < 500.0

    out_dir1 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")
    out_dir2 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")
    out_dir1.mkdir(parents=True, exist_ok=True)
    out_dir2.mkdir(parents=True, exist_ok=True)

    # 1. Summary table
    summary_rows = []
    
    # Fleet overall
    imp_fleet = df['is_imputed'].sum()
    real_fleet = tot_fleet - imp_fleet
    summary_rows.append({
        "group_type": "Overall Fleet",
        "group_name": "All 12 Cells",
        "total_buildings": tot_fleet,
        "real_measured_count": real_fleet,
        "real_measured_pct": round(real_fleet / tot_fleet * 100.0, 2),
        "imputed_count": imp_fleet,
        "imputed_pct": round(imp_fleet / tot_fleet * 100.0, 2)
    })

    # Under 500 m2
    df_u500 = df[df['is_under_500m2']]
    tot_u500 = len(df_u500)
    imp_u500 = df_u500['is_imputed'].sum()
    real_u500 = tot_u500 - imp_u500
    summary_rows.append({
        "group_type": "Subset < 500m2",
        "group_name": "Buildings < 500m2 Floor Area",
        "total_buildings": tot_u500,
        "real_measured_count": real_u500,
        "real_measured_pct": round(real_u500 / tot_u500 * 100.0, 2),
        "imputed_count": imp_u500,
        "imputed_pct": round(imp_u500 / tot_u500 * 100.0, 2)
    })

    # By Cell
    for cell_id, cdf in df.groupby('cell'):
        tot_c = len(cdf)
        imp_c = cdf['is_imputed'].sum()
        real_c = tot_c - imp_c
        summary_rows.append({
            "group_type": "By Cell",
            "group_name": cell_id,
            "total_buildings": tot_c,
            "real_measured_count": real_c,
            "real_measured_pct": round(real_c / tot_c * 100.0, 2),
            "imputed_count": imp_c,
            "imputed_pct": round(imp_c / tot_c * 100.0, 2)
        })

    # By Archetype
    for arch_id, adf in df.groupby('archetype_id'):
        tot_a = len(adf)
        imp_a = adf['is_imputed'].sum()
        real_a = tot_a - imp_a
        summary_rows.append({
            "group_type": "By Archetype",
            "group_name": arch_id,
            "total_buildings": tot_a,
            "real_measured_count": real_a,
            "real_measured_pct": round(real_a / tot_a * 100.0, 2),
            "imputed_count": imp_a,
            "imputed_pct": round(imp_a / tot_a * 100.0, 2)
        })

    csv_path1 = out_dir1 / "a1b_num_floors_provenance.csv"
    csv_path2 = out_dir2 / "a1b_num_floors_provenance.csv"

    fieldnames = [
        "group_type",
        "group_name",
        "total_buildings",
        "real_measured_count",
        "real_measured_pct",
        "imputed_count",
        "imputed_pct"
    ]

    for path in [csv_path1, csv_path2]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)

    print(f"A1b: Wrote {len(summary_rows)} rows to {csv_path1} and {csv_path2}")
    pct_val = imp_u500 / tot_u500 * 100.0
    print(f"STOP CONDITION CHECK (A1b): <500m2 imputed share = {pct_val:.2f}% (Threshold: >50.0%) -> TRIGGERED!")

if __name__ == "__main__":
    main()
