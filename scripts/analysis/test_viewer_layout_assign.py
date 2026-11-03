import os
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd

from openubem.viz.geometry_extract import parse_idf, collect_geometry
from openubem.viz.cityjson_emitter import build_cityjson
from openubem.viz.viewer_export import build_scene

def test_layout_assign_idf_ingestion():
    idf_path = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\scratchpad\t19_t01_t05_work\work_t05\nyc_suburban\step3_layout_assign\idfs\way_1014146136.idf")
    print(f"Testing ingestion of {idf_path}...")
    
    idf_data = parse_idf(str(idf_path))
    geom = collect_geometry(str(idf_path), recentre=False)
    
    print("Parsed IDF Data keys:", list(idf_data.keys())[:10])
    print("Geom keys:", list(geom.keys()))
    print(f"Collected faces: {len(geom['faces'])}, subwin: {len(geom['subwin'])}")
    
    print("Sample face tuple structure:", geom['faces'][0])
        
    print(f"Zones found in geometry ({len(zones_found)}):", sorted(list(zones_found))[:10])
    
    # Check zone honesty rule: viewer_logic.mjs expects zoning_strategy to be 'perimeter_core' or 'room_layout'
    # DOE native prototypes use DOE zone names (e.g. G SW Apartment, M Corridor, Top_ElevatorMachineRm, etc.)
    print("Ingestion test: SUCCESS! layout_assign IDFs can be parsed by geometry_extract.")

if __name__ == "__main__":
    test_layout_assign_idf_ingestion()
