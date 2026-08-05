"""Diagnosis-only: recompute actual conditioned floor area from eio Zone Information
lines (Floor Area {m2} * Zone Multiplier, filtered to Part of Total Building Area == Yes)
for D_HIGHMULT_highrise20 and D_control_S1_highrise3, independent of the harness's
nominal fp_area * n_real denominator."""
import csv
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
RUNS = REPO / "docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/results/c01_runs"

def parse_zone_info(eio_path: Path):
    header = None
    rows = []
    for line in eio_path.read_text(errors="replace").splitlines():
        if line.startswith("! <Zone Information>"):
            header = [h.strip() for h in line[len("! <Zone Information>,"):].split(",")]
        elif line.startswith(" Zone Information,") or line.startswith("Zone Information,"):
            parts = [p.strip() for p in line.split(",")]
            # parts[0] == 'Zone Information'
            rows.append(parts[1:])
    return header, rows

for case in ["D_HIGHMULT_highrise20", "D_control_S1_highrise3", "A_equal_identity_highrise"]:
    eio = RUNS / case / "eplusout.eio"
    header, rows = parse_zone_info(eio)
    # header fields (0-indexed after Zone Information,): Name,NorthAxis,OrigX,OrigY,OrigZ,
    # CentX,CentY,CentZ,Type,ZoneMultiplier,ZoneListMultiplier,MinX,MaxX,MinY,MaxY,MinZ,MaxZ,
    # CeilHeight,Volume,InsideConvAlg,OutsideConvAlg,FloorArea,ExtGrossWall,ExtNetWall,ExtWindow,
    # NumSurf,NumSubSurf,NumShadingSubSurf,PartOfTotalBuildingArea
    total_area = 0.0
    total_area_x_mult = 0.0
    n_zones = 0
    for r in rows:
        name = r[0]
        try:
            mult = float(r[9])
            list_mult = float(r[10])
            floor_area = float(r[21])
            part_of_total = r[-1].strip()
        except (IndexError, ValueError):
            continue
        n_zones += 1
        if part_of_total.lower() == "yes":
            total_area += floor_area
            total_area_x_mult += floor_area * mult * list_mult
    print(f"{case}: n_zones={n_zones} sum(unmultiplied floor area, PartOfTotal=Yes)={total_area:.3f} "
          f"sum(floor_area * mult * list_mult)={total_area_x_mult:.3f}")
