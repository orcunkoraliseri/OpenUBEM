"""Diagnosis-only: object-level Watt/flow-field comparison between
D_HIGHMULT_highrise20 and D_control_S1_highrise3 IDFs, using eppy to parse
robustly. No production code touched."""
import sys
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))

from geomeppy import IDF
from openubem import config

IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))

D_PATH = REPO / "scratchpad/c01_work/D_HIGHMULT_highrise20/idfs/c01_D_HIGHMULT_highrise20.idf"
C_PATH = REPO / "scratchpad/c01_work/D_control_S1_highrise3/idfs/c01_D_control_S1_highrise3.idf"

idf_d = IDF(str(D_PATH))
idf_c = IDF(str(C_PATH))

print("=== WATERUSE:EQUIPMENT ===")
for obj_d, obj_c in zip(idf_d.idfobjects["WATERUSE:EQUIPMENT"], idf_c.idfobjects["WATERUSE:EQUIPMENT"]):
    assert obj_d.Name == obj_c.Name, (obj_d.Name, obj_c.Name)
    pfr_d = float(obj_d.Peak_Flow_Rate)
    pfr_c = float(obj_c.Peak_Flow_Rate)
    zone_d = getattr(obj_d, "Zone_Name", None)
    ratio = pfr_d / pfr_c if pfr_c else float("nan")
    print(f"{obj_d.Name:40s} zone={zone_d!s:20s} D={pfr_d:.6f} C={pfr_c:.6f} ratio={ratio:.4f}")

print("\n=== LIGHTS (sample M-band + G-band + T-band) ===")
for obj_d, obj_c in zip(idf_d.idfobjects["LIGHTS"], idf_c.idfobjects["LIGHTS"]):
    assert obj_d.Name == obj_c.Name
    method = obj_d.Design_Level_Calculation_Method
    val_d = float(obj_d.Lighting_Level) if method == "LightingLevel" else float(obj_d.Watts_per_Zone_Floor_Area)
    val_c = float(obj_c.Lighting_Level) if method == "LightingLevel" else float(obj_c.Watts_per_Zone_Floor_Area)
    ratio = val_d / val_c if val_c else float("nan")
    if "M " in obj_d.Zone_or_ZoneList_or_Space_or_SpaceList_Name.upper() or "G " in obj_d.Zone_or_ZoneList_or_Space_or_SpaceList_Name.upper() or "T " in obj_d.Zone_or_ZoneList_or_Space_or_SpaceList_Name.upper():
        print(f"{obj_d.Name:40s} zone={obj_d.Zone_or_ZoneList_or_Space_or_SpaceList_Name:20s} method={method:20s} D={val_d:.4f} C={val_c:.4f} ratio={ratio:.4f}")

print("\n=== ELECTRICEQUIPMENT (sample) ===")
for obj_d, obj_c in zip(idf_d.idfobjects["ELECTRICEQUIPMENT"], idf_c.idfobjects["ELECTRICEQUIPMENT"]):
    assert obj_d.Name == obj_c.Name
    method = obj_d.Design_Level_Calculation_Method
    val_d = float(obj_d.Design_Level) if method == "EquipmentLevel" else float(obj_d.Watts_per_Zone_Floor_Area)
    val_c = float(obj_c.Design_Level) if method == "EquipmentLevel" else float(obj_c.Watts_per_Zone_Floor_Area)
    ratio = val_d / val_c if val_c else float("nan")
    zname = obj_d.Zone_or_ZoneList_or_Space_or_SpaceList_Name
    if any(b in zname.upper() for b in (" M ", "^M ", "G ", "T ")) or zname.upper().startswith(("M ", "G ", "T ")):
        print(f"{obj_d.Name:40s} zone={zname:20s} method={method:20s} D={val_d:.4f} C={val_c:.4f} ratio={ratio:.4f}")

print("\n=== ZONE Multiplier field (all zones) ===")
for obj_d, obj_c in zip(idf_d.idfobjects["ZONE"], idf_c.idfobjects["ZONE"]):
    assert obj_d.Name == obj_c.Name
    md = obj_d.Multiplier
    mc = obj_c.Multiplier
    print(f"{obj_d.Name:20s} D.Multiplier={md!s:6s} C.Multiplier={mc!s:6s}")
