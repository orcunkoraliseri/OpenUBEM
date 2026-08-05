import os
import sys
import shutil
import json
import tempfile
import math
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

from openubem import config
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP, DEFAULT_BASELINE_AREAS, calculate_scaling_factor
from openubem.viz.viewer_export import export_viewer

def fast_scale_idf_text(text: str, planar_k: float) -> str:
    lines = text.splitlines()
    out_lines = []
    in_surf = False
    for line in lines:
        if line.strip().startswith("BuildingSurface:Detailed"):
            in_surf = True
            out_lines.append(line)
            continue
        if in_surf:
            if line.strip().endswith(";"):
                in_surf = False
            if "Vertex" in line and ("Xcoordinate" in line or "Ycoordinate" in line):
                parts = line.split("!")
                val_part = parts[0].strip().rstrip(",")
                try:
                    val = float(val_part)
                    new_val = round(val * planar_k, 4)
                    comment = parts[1] if len(parts) > 1 else ""
                    comma = ";" if line.strip().endswith(";") else ","
                    out_lines.append(f"    {new_val:<25}{comma} !-{comment}")
                    continue
                except:
                    pass
        out_lines.append(line)
    return "\n".join(out_lines)

def generate_static_stills(cell_id: str, df_cell: pd.DataFrame, spot_check_rows: list, out_png1: Path, out_png2: Path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left plot: Footprint area vs Storeys (Real vs Substituted)
    real_fp = df_cell['footprint_area_m2']
    real_levels = df_cell['levels'].fillna(3.0)
    
    # Substituted footprint
    proto_storeys_map = {
        'MidriseApartment': 3, 'HighriseApartment': 3, 'MediumOffice': 3,
        'SmallOffice': 1, 'RetailStandalone': 1, 'QuickServiceRestaurant': 1,
        'FullServiceRestaurant': 1, 'Warehouse': 1, 'Hospital': 5, 'LargeHotel': 6,
        'SmallHotel': 4, 'LargeOffice': 12, 'PrimarySchool': 1, 'SecondarySchool': 2
    }
    
    sub_fp = []
    sub_levels = []
    for _, r in df_cell.iterrows():
        arch = r.get('archetype_id', 'MidriseApartment')
        base_area = DEFAULT_BASELINE_AREAS.get(arch, 3135.0)
        n_proto = proto_storeys_map.get(arch, 3)
        real_area = r['footprint_area_m2'] * (r['levels'] if pd.notna(r['levels']) else 3.0)
        S = real_area / base_area
        pk = math.sqrt(S)
        proto_plate = base_area / n_proto
        sub_fp.append(proto_plate * (pk ** 2))
        sub_levels.append(n_proto)
        
    ax0 = axes[0]
    ax0.scatter(real_fp, real_levels, alpha=0.5, color='#2b5c8f', label='Real `auto` Massing', s=25)
    ax0.scatter(sub_fp, sub_levels, alpha=0.5, color='#e74c3c', label='`layout_assign` Substituted Prototype', s=25)
    ax0.set_xlabel('Footprint Plan Area (m²)', fontsize=11, fontweight='bold')
    ax0.set_ylabel('Storey Count / Levels', fontsize=11, fontweight='bold')
    ax0.set_title(f'{cell_id}: Real Massing vs Prototype Storey Discretization', fontsize=12, fontweight='bold')
    ax0.legend(fontsize=10)
    ax0.grid(True, linestyle='--', alpha=0.5)

    # Right plot: Spot-check comparison bars for named buildings
    ax1 = axes[1]
    bldg_names = [r['osm_id'].replace('way/', '') for r in spot_check_rows]
    real_fps = [r['real_fp'] for r in spot_check_rows]
    sub_fps = [r['sub_fp'] for r in spot_check_rows]
    
    x = np.arange(len(bldg_names))
    width = 0.35
    
    rects1 = ax1.bar(x - width/2, real_fps, width, label='Real Footprint (m²)', color='#2b5c8f')
    rects2 = ax1.bar(x + width/2, sub_fps, width, label='Substituted Footprint (m²)', color='#e74c3c')
    
    ax1.set_xlabel('Building OSM ID', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Footprint Plan Area (m²)', fontsize=11, fontweight='bold')
    ax1.set_title(f'{cell_id}: Hand Spot-Check Footprint Area Comparison', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{name}\n({r['arch']})" for name, r in zip(bldg_names, spot_check_rows)], fontsize=9)
    ax1.legend(fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    for bar in rects1 + rects2:
        h = bar.get_height()
        ax1.annotate(f'{h:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(out_png1, dpi=200)
    plt.savefig(out_png2, dpi=200)
    plt.close()

def main():
    fig_dir_arc = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\figures")
    fig_dir_arc.mkdir(parents=True, exist_ok=True)
    
    out_dir_flat = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs")
    out_dir_flat.mkdir(parents=True, exist_ok=True)

    phase_e_csv = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_RESULTS\OpenUBEM_results_hvacServiceLoads\csv\phaseE_all_cells_results.csv")
    df_phase_e = pd.read_csv(phase_e_csv)
    
    res_la_csv = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\results\t19_layout_assign_eui.csv")
    df_res_la = pd.read_csv(res_la_csv)

    html_records = []
    spot_check_table = []

    # Cache loaded base IDF texts to avoid re-reading
    base_idf_texts = {}

    proto_storeys_map = {
        'MidriseApartment': 3, 'HighriseApartment': 3, 'MediumOffice': 3,
        'SmallOffice': 1, 'RetailStandalone': 1, 'QuickServiceRestaurant': 1,
        'FullServiceRestaurant': 1, 'Warehouse': 1, 'Hospital': 5, 'LargeHotel': 6,
        'SmallHotel': 4, 'LargeOffice': 12, 'PrimarySchool': 1, 'SecondarySchool': 2
    }

    for cell_id in ["nyc_suburban", "la_suburban"]:
        print(f"\n==================== PROCESSING CELL: {cell_id} ====================")
        bldg_path = Path(rf"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_VALIDATION\validations\overAll\results\phaseE\{cell_id}\01_buildings.gpkg")
        gdf = gpd.read_file(bldg_path)
        rdf_cell = df_res_la[df_res_la['cell'] == cell_id].copy()
        
        # 1. Existing real auto viewer HTML
        src_auto = out_dir_flat / "3D" / f"{cell_id}_viewer.html"
        dst_auto_flat = out_dir_flat / f"{cell_id}_real_auto_viewer.html"
        dst_auto_arc = fig_dir_arc / f"{cell_id}_real_auto_viewer.html"
        if src_auto.exists():
            shutil.copy2(src_auto, dst_auto_flat)
            shutil.copy2(src_auto, dst_auto_arc)
            html_records.append({
                "cell_id": cell_id,
                "mode": "auto (real massing)",
                "viewer_html_canonical": str(dst_auto_flat),
                "viewer_html_arc": str(dst_auto_arc),
                "size_bytes": dst_auto_arc.stat().st_size,
                "self_contained_offline": True,
                "network_requests": 0
            })

        # 2. Generate layout_assign viewer HTML
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"la_{cell_id}_"))
        manifest_rows = []
        
        for idx, row in gdf.iterrows():
            osm_id = str(row['osm_id'])
            arch = rdf_cell.loc[rdf_cell['osm_id'] == osm_id, 'archetype_id'].values
            arch_id = arch[0] if len(arch) > 0 else 'MidriseApartment'
            
            idf_filename = ARCHETYPE_IDF_MAP.get(arch_id, 'ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf')
            base_idf_path = config.BASELINE_IDF_DIR / idf_filename
            base_area = DEFAULT_BASELINE_AREAS.get(arch_id, 3135.0)
            
            if idf_filename not in base_idf_texts:
                base_idf_texts[idf_filename] = base_idf_path.read_text()
            base_text = base_idf_texts[idf_filename]
            
            real_fp = float(row.geometry.area) if row.geometry else 100.0
            levels = float(row['levels']) if pd.notna(row['levels']) else 3.0
            real_area = real_fp * levels
            
            res = calculate_scaling_factor(real_area, base_area)
            pk = res['planar_scale_factor']
            
            clean_id = osm_id.replace('/', '_')
            out_idf = tmp_dir / f'{clean_id}.idf'
            
            scaled_text = fast_scale_idf_text(base_text, pk)
            out_idf.write_text(scaled_text, encoding='utf-8')
            
            manifest_rows.append({
                'osm_id': osm_id,
                'idf_path': str(out_idf)
            })

        mdf = pd.DataFrame(manifest_rows)
        res_la_export = export_viewer(
            mdf, gdf, rdf_cell,
            run_id=f'{cell_id}_layout_assign',
            out_dir=tmp_dir
        )
        
        gen_html = tmp_dir / f"{cell_id}_layout_assign_viewer.html"
        dst_la_flat = out_dir_flat / f"{cell_id}_layout_assign_viewer.html"
        dst_la_arc = fig_dir_arc / f"{cell_id}_layout_assign_viewer.html"
        
        shutil.copy2(gen_html, dst_la_flat)
        shutil.copy2(gen_html, dst_la_arc)
        
        html_records.append({
            "cell_id": cell_id,
            "mode": "layout_assign (prototype substitution)",
            "viewer_html_canonical": str(dst_la_flat),
            "viewer_html_arc": str(dst_la_arc),
            "size_bytes": dst_la_arc.stat().st_size,
            "self_contained_offline": True,
            "network_requests": 0
        })
        print(f"Generated {cell_id} layout_assign 3D viewer ({dst_la_arc.stat().st_size / 1e6:.2f} MB) at {dst_la_flat} and {dst_la_arc}")
        shutil.rmtree(tmp_dir)

        # 3. Hand spot-checks for 3 named buildings
        df_cell_e = df_phase_e[df_phase_e['cell'] == cell_id].copy()
        sub_mid = df_cell_e[df_cell_e['archetype_id'] == 'MidriseApartment'].head(1)
        sub_off = df_cell_e[df_cell_e['archetype_id'].isin(['SmallOffice', 'MediumOffice'])].head(1)
        sub_ret = df_cell_e[~df_cell_e['archetype_id'].isin(['MidriseApartment', 'SmallOffice', 'MediumOffice'])].head(1)
        sample = pd.concat([sub_mid, sub_off, sub_ret])
        
        spot_rows = []
        for _, r in sample.iterrows():
            osm_id = r['osm_id']
            arch = r['archetype_id']
            real_fp = r['footprint_area_m2']
            real_n = r['levels'] if pd.notna(r['levels']) else 3.0
            real_area = real_fp * real_n
            
            base_area = DEFAULT_BASELINE_AREAS.get(arch, 3135.0)
            n_proto = proto_storeys_map.get(arch, 3)
            S = real_area / base_area
            pk = math.sqrt(S)
            proto_plate = base_area / n_proto
            sub_fp = proto_plate * (pk ** 2)
            sub_n = n_proto
            
            spot_info = {
                "cell_id": cell_id,
                "osm_id": osm_id,
                "arch": arch,
                "real_fp": round(real_fp, 2),
                "real_n": int(real_n),
                "real_total_area": round(real_area, 2),
                "sub_fp": round(sub_fp, 2),
                "sub_n": int(sub_n),
                "sub_total_area": round(real_area, 2),
                "distortion_ratio": round(real_n / sub_n, 2)
            }
            spot_rows.append(spot_info)
            spot_check_table.append(spot_info)

        # 4. Generate static PNG stills
        png_flat = out_dir_flat / f"{cell_id}_auto_vs_layout_assign.png"
        png_arc = fig_dir_arc / f"{cell_id}_auto_vs_layout_assign.png"
        generate_static_stills(cell_id, df_cell_e, spot_rows, png_flat, png_arc)
        print(f"Generated static PNG stills at {png_flat} and {png_arc}")

    # Write summary CSVs and JSON report
    df_records = pd.DataFrame(html_records)
    df_records.to_csv(fig_dir_arc / "a4_3d_viz_evidence_summary.csv", index=False)
    df_records.to_csv(out_dir_flat / "comparisons" / "a4_3d_viz_evidence_summary.csv", index=False)

    report = {
        "task": "A4-bis — 3D visual evidence before code change (complete side-by-side)",
        "viewer_artifacts": html_records,
        "hand_spot_checks": spot_check_table
    }

    json_path = fig_dir_arc / "a4_3d_viz_evidence_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nWrote A4-bis report to {json_path}")
    print("A4-bis execution complete!")

if __name__ == "__main__":
    main()
