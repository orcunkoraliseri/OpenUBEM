import os
import sys
import math
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Any
import shapely.geometry
from eppy.modeleditor import IDF

from openubem import config
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP, DEFAULT_BASELINE_AREAS

IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))

# Inverse mapping: IDF filename -> list of canonical archetype IDs
IDF_TO_ARCHETYPES: Dict[str, List[str]] = {}
for arch, idf_name in ARCHETYPE_IDF_MAP.items():
    IDF_TO_ARCHETYPES.setdefault(idf_name, []).append(arch)

def calculate_polygon_area(coords: List[Tuple[float, float]]) -> float:
    if len(coords) < 3:
        return 0.0
    poly = shapely.geometry.Polygon(coords)
    return poly.area

def process_idf(idf_path: Path) -> Dict[str, Any]:
    idf = IDF(str(idf_path))
    filename = idf_path.name
    archetypes = IDF_TO_ARCHETYPES.get(filename, [filename.replace(".idf", "")])
    primary_archetype = archetypes[0]
    
    zones = idf.idfobjects["ZONE"]
    total_zone_count = len(zones)
    
    rules = idf.idfobjects["GLOBALGEOMETRYRULES"]
    coord_sys = rules[0].Coordinate_System.upper() if rules else "WORLD"
    
    zone_origins = {}
    zone_multipliers = {}
    for z in zones:
        x0 = float(z.X_Origin) if z.X_Origin not in (None, "") else 0.0
        y0 = float(z.Y_Origin) if z.Y_Origin not in (None, "") else 0.0
        z0 = float(z.Z_Origin) if z.Z_Origin not in (None, "") else 0.0
        mult = float(z.Multiplier) if z.Multiplier not in (None, "", 0) else 1.0
        zone_origins[z.Name.upper()] = (x0, y0, z0)
        zone_multipliers[z.Name.upper()] = mult

    has_multiplier_gt_1 = any(m > 1 for m in zone_multipliers.values())
    
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    zone_floor_info = {} # zone_name -> {floor_z, area, raw_name}
    
    for s in surfaces:
        stype = s.Surface_Type.upper()
        if stype != "FLOOR":
            continue
        zname = s.Zone_Name.upper()
        vertices = s.coords
        if not vertices:
            continue
            
        z_orig = zone_origins.get(zname, (0.0, 0.0, 0.0))
        if coord_sys == "RELATIVE":
            world_verts = [(v[0] + z_orig[0], v[1] + z_orig[1], v[2] + z_orig[2]) for v in vertices]
        else:
            world_verts = vertices
            
        z_elev = min(v[2] for v in world_verts)
        planar_coords = [(v[0], v[1]) for v in world_verts]
        area = calculate_polygon_area(planar_coords)
        
        if zname not in zone_floor_info:
            zone_floor_info[zname] = {"floor_z": z_elev, "area": area, "raw_name": s.Zone_Name}
        else:
            zone_floor_info[zname]["area"] += area

    sorted_zones = sorted(zone_floor_info.items(), key=lambda x: x[1]["floor_z"])
    
    storey_clusters = [] # list of dict
    for zname, info in sorted_zones:
        z_elev = info["floor_z"]
        mult = zone_multipliers.get(zname, 1.0)
        matched_cluster = None
        for c in storey_clusters:
            if abs(c["z_level"] - z_elev) < 0.2:
                matched_cluster = c
                break
        if matched_cluster is None:
            storey_clusters.append({
                "z_level": round(z_elev, 2),
                "zones": [info["raw_name"]],
                "total_area": info["area"],
                "total_area_with_mult": info["area"] * mult
            })
        else:
            matched_cluster["zones"].append(info["raw_name"])
            matched_cluster["total_area"] += info["area"]
            matched_cluster["total_area_with_mult"] += info["area"] * mult

    num_modelled_storeys = len(storey_clusters)
    recomputed_area = sum(c["total_area_with_mult"] for c in storey_clusters)
    
    baseline_area = DEFAULT_BASELINE_AREAS.get(primary_archetype, 0.0)
    area_diff_pct = ((recomputed_area - baseline_area) / baseline_area * 100.0) if baseline_area > 0 else 0.0
    
    zone_raw_names = [z.Name for z in zones]
    name_prefixes = set()
    for n in zone_raw_names:
        parts = n.split()
        if parts:
            name_prefixes.add(parts[0])
            
    if num_modelled_storeys == 1:
        convention = "single-storey"
    elif any(p in ("G", "M", "T") for p in name_prefixes):
        convention = "G/M/T"
    elif any("FLOOR" in p.upper() or "FLR" in p.upper() or "STOR" in p.upper() or p.startswith("F") or p.startswith("FL") for p in name_prefixes):
        convention = "F1/F2/..."
    else:
        convention = "other"

    name_z_disagreements = []
    if convention == "G/M/T":
        min_z = min(c["z_level"] for c in storey_clusters) if storey_clusters else 0
        max_z = max(c["z_level"] for c in storey_clusters) if storey_clusters else 0
        for zname, info in zone_floor_info.items():
            raw_n = info["raw_name"]
            prefix = raw_n.split()[0]
            z_elev = info["floor_z"]
            if prefix == "G" and abs(z_elev - min_z) > 0.2:
                name_z_disagreements.append(f"{raw_n}(G at Z={z_elev:.1f}m != min Z={min_z:.1f}m)")
            elif prefix == "T" and abs(z_elev - max_z) > 0.2:
                name_z_disagreements.append(f"{raw_n}(T at Z={z_elev:.1f}m != max Z={max_z:.1f}m)")
            elif prefix == "M" and (abs(z_elev - min_z) <= 0.2 or abs(z_elev - max_z) <= 0.2):
                name_z_disagreements.append(f"{raw_n}(M at Z={z_elev:.1f}m is min/max Z)")
                
    band_summary_parts = []
    for c in storey_clusters:
        band_summary_parts.append(f"Z={c['z_level']}m:{len(c['zones'])}z({c['total_area_with_mult']:.1f}m2)")
    band_summary = "; ".join(band_summary_parts)
    
    avg_plate_area = recomputed_area / num_modelled_storeys if num_modelled_storeys > 0 else 0.0

    return {
        "primary_archetype": primary_archetype,
        "idf_filename": filename,
        "total_zone_count": total_zone_count,
        "num_modelled_storeys": num_modelled_storeys,
        "floor_band_convention": convention,
        "zones_by_band": band_summary,
        "has_multiplier_gt_1": has_multiplier_gt_1,
        "avg_storey_plate_area_m2": round(avg_plate_area, 2),
        "recomputed_floor_area_m2": round(recomputed_area, 2),
        "registry_baseline_area_m2": round(baseline_area, 2),
        "area_diff_pct": round(area_diff_pct, 2),
        "disagreements": "; ".join(name_z_disagreements) if name_z_disagreements else "None"
    }

def main():
    baseline_dir = config.BASELINE_IDF_DIR
    idf_files = sorted(list(baseline_dir.glob("*.idf")))
    
    results = []
    print(f"Mapping storey structure for {len(idf_files)} baseline IDFs...")
    for p in idf_files:
        res = process_idf(p)
        results.append(res)

    out_dir1 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")
    out_dir2 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")
    out_dir1.mkdir(parents=True, exist_ok=True)
    out_dir2.mkdir(parents=True, exist_ok=True)

    csv_path1 = out_dir1 / "a1_prototype_storey_structure.csv"
    csv_path2 = out_dir2 / "a1_prototype_storey_structure.csv"

    fieldnames = [
        "primary_archetype",
        "idf_filename",
        "total_zone_count",
        "num_modelled_storeys",
        "floor_band_convention",
        "zones_by_band",
        "has_multiplier_gt_1",
        "avg_storey_plate_area_m2",
        "recomputed_floor_area_m2",
        "registry_baseline_area_m2",
        "area_diff_pct",
        "disagreements"
    ]

    for path in [csv_path1, csv_path2]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    print(f"Successfully wrote {len(results)} rows to {csv_path1} and {csv_path2}")

if __name__ == "__main__":
    main()
