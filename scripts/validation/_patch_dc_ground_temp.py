"""Patch data center counterpart IDFs with Site:GroundTemperature:BuildingSurface."""
import tempfile
from pathlib import Path

OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"

GROUND_TEMP_BLOCK = (
    "\nSite:GroundTemperature:BuildingSurface,\n"
    "  -10.0, -8.0, -3.0, 5.0, 12.0, 18.0,\n"
    "  22.0, 21.0, 16.0, 9.0, 2.0, -6.0;\n"
)

dc_names = [
    "ASHRAE901_DataCenterLargeHighITE_STD2019_counterpart",
    "ASHRAE901_DataCenterLargeLowITE_STD2019_counterpart",
    "SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221_counterpart",
]

for name in dc_names:
    idf_path = OUT_BASE / "counterparts_2d" / "idfs" / f"{name}.idf"
    if not idf_path.exists():
        print(f"NOT FOUND: {name}")
        continue
    txt = idf_path.read_text(encoding="utf-8", errors="replace")
    if "Site:GroundTemperature" in txt:
        print(f"{name}: already has ground temp -- skipping")
        continue
    insert_after = "Site:Location,"
    idx = txt.find(insert_after)
    if idx == -1:
        insert_after = "Building,"
        idx = txt.find(insert_after)
    if idx != -1:
        end_idx = txt.find(";", idx) + 1
        new_txt = txt[:end_idx] + GROUND_TEMP_BLOCK + txt[end_idx:]
    else:
        new_txt = txt + GROUND_TEMP_BLOCK
    idf_path.write_text(new_txt, encoding="utf-8")
    print(f"Patched: {name}")
