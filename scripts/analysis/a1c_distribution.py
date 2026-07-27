import os
import sys
import csv
from pathlib import Path
import pandas as pd

def main():
    phase_e_path = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_RESULTS\OpenUBEM_results_hvacServiceLoads\csv\phaseE_all_cells_results.csv")
    if not phase_e_path.exists():
        print(f"Error: {phase_e_path} not found")
        sys.exit(1)
        
    df = pd.read_csv(phase_e_path)
    tot_fleet = len(df)
    
    df['is_imputed'] = df['data_quality_flag'].fillna('').apply(lambda x: 'no_floors' in [s.strip() for s in x.split(',')])
    df['floor_area'] = df['footprint_area_m2'] * df['levels']
    df['is_under_500m2'] = df['floor_area'] < 500.0

    df_imp = df[df['is_imputed']]
    df_imp_u500 = df_imp[df_imp['is_under_500m2']]
    df_real = df[~df['is_imputed']]

    total_imp_cnt = len(df_imp)
    total_imp_u500_cnt = len(df_imp_u500)
    total_real_cnt = len(df_real)

    all_levels = sorted(list(set(df['levels'].dropna().unique())))

    out_rows = []
    for l in all_levels:
        c_imp = int((df_imp['levels'] == l).sum())
        c_imp_u500 = int((df_imp_u500['levels'] == l).sum())
        c_real = int((df_real['levels'] == l).sum())
        
        if c_imp > 0 or c_imp_u500 > 0 or c_real > 0:
            out_rows.append({
                "num_floors": int(l),
                "imputed_overall_count": c_imp,
                "imputed_overall_pct": round(c_imp / total_imp_cnt * 100.0, 2),
                "imputed_u500m2_count": c_imp_u500,
                "imputed_u500m2_pct": round(c_imp_u500 / total_imp_u500_cnt * 100.0, 2),
                "real_measured_control_count": c_real,
                "real_measured_control_pct": round(c_real / total_real_cnt * 100.0, 2),
            })

    out_dir1 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")
    out_dir2 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")
    out_dir1.mkdir(parents=True, exist_ok=True)
    out_dir2.mkdir(parents=True, exist_ok=True)

    csv_path1 = out_dir1 / "a1c_num_floors_distribution.csv"
    csv_path2 = out_dir2 / "a1c_num_floors_distribution.csv"

    fieldnames = [
        "num_floors",
        "imputed_overall_count",
        "imputed_overall_pct",
        "imputed_u500m2_count",
        "imputed_u500m2_pct",
        "real_measured_control_count",
        "real_measured_control_pct"
    ]

    for path in [csv_path1, csv_path2]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out_rows)

    print(f"A1c: Wrote {len(out_rows)} level rows to {csv_path1} and {csv_path2}")
    print(f"Totals: Imputed Overall={total_imp_cnt}, Imputed <500m2={total_imp_u500_cnt}, Real Measured={total_real_cnt}")

if __name__ == "__main__":
    main()
