import os
import sys
from pathlib import Path
from eppy.modeleditor import IDF

from openubem import config

IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))

baseline_dir = config.BASELINE_IDF_DIR
idf_files = sorted(list(baseline_dir.glob("*.idf")))
print(f"Found {len(idf_files)} baseline IDFs in {baseline_dir}")

for p in idf_files:
    idf = IDF(str(p))
    zones = idf.idfobjects["ZONE"]
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    rules = idf.idfobjects["GLOBALGEOMETRYRULES"]
    coord_sys = rules[0].Coordinate_System if rules else "Unknown"
    
    # Check multipliers
    mults = [z.Multiplier for z in zones if z.Multiplier not in (None, "", 1, "1")]
    
    print(f"File: {p.name} | Zones: {len(zones)} | Surfaces: {len(surfaces)} | CoordSys: {coord_sys} | Non1-Mults: {mults}")
