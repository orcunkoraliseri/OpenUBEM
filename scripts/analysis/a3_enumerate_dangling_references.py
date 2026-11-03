import os
import sys
from pathlib import Path
from eppy.modeleditor import IDF

from openubem import config
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP

IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))

def analyze_zone_references(idf_filename: str):
    idf_path = config.BASELINE_IDF_DIR / idf_filename
    idf = IDF(str(idf_path))
    
    zones = idf.idfobjects["ZONE"]
    zone_names = [z.Name for z in zones]
    
    # Identify middle floor zones (containing 'M ' or 'FLR2' or similar)
    mid_zones = [z.Name for z in zones if "M " in z.Name or "MID" in z.Name.upper() or "FLR2" in z.Name.upper() or "FLOOR2" in z.Name.upper() or "STOREY2" in z.Name.upper()]
    mid_zones_upper = set(z.upper() for z in mid_zones)
    
    print(f"\n=======================================================")
    print(f"Analyzing {idf_filename}")
    print(f"Total Zones: {len(zones)}, Identified Middle Zones ({len(mid_zones)}):")
    for mz in mid_zones:
        print(f"  - {mz}")
        
    # Search all idfobjects for references to any middle zone name
    referencing_objects = []
    
    for obj_type in idf.idfobjects.keys():
        objs = idf.idfobjects[obj_type]
        for o in objs:
            # Check fields of object
            obj_str = str(o)
            for mz in mid_zones:
                if mz.upper() in obj_str.upper():
                    referencing_objects.append((obj_type, o.Name if hasattr(o, "Name") and o.Name else "unnamed", mz))
                    break

    print(f"\nFound {len(referencing_objects)} IDF objects referencing middle zones:")
    
    # Group by object type
    by_type = {}
    for obj_type, name, mz in referencing_objects:
        by_type.setdefault(obj_type, []).append((name, mz))
        
    for obj_type, item_list in sorted(by_type.items()):
        print(f"\n--- {obj_type} ({len(item_list)} instances) ---")
        for name, mz in item_list[:10]:
            print(f"  [{obj_type}] {name} (refs {mz})")
        if len(item_list) > 10:
            print(f"  ... and {len(item_list) - 10} more")

if __name__ == "__main__":
    analyze_zone_references("ASHRAE901_OfficeMedium_STD2022_Buffalo.idf")
    analyze_zone_references("ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf")
    analyze_zone_references("ASHRAE901_HotelLarge_STD2022_Buffalo.idf")
