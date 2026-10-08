import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eppy.modeleditor import IDF, IDDAlreadySetError

from openubem import config
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP

BASE_DIR = Path(os.environ.get(
    "OPENUBEM_BASELINE_IDF_DIR",
    "C:/Users/o_iseri/Desktop/NEXA-desktop/Content/00.BaselineBuildings_NUs_v231",
))
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons" / "open62_prototype_storeys_2026-09-30.csv"
GROUND_TOL_M = 0.1

DOE_FLOORS = {
    "ASHRAE901_OfficeSmall_STD2022_Buffalo.idf": 1,
    "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf": 3,
    "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf": 12,
    "ASHRAE901_Warehouse_STD2022_Buffalo.idf": 1,
    "ASHRAE901_RetailStandalone_STD2022_Buffalo.idf": 1,
    "ASHRAE901_RetailStripmall_STD2022_Buffalo.idf": 1,
    "ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf": 1,
    "ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf": 2,
    "ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf": 3,
    "ASHRAE901_Hospital_STD2022_Buffalo.idf": 5,
    "ASHRAE901_HotelSmall_STD2022_Buffalo.idf": 4,
    "ASHRAE901_HotelLarge_STD2022_Buffalo.idf": 6,
    "ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf": 4,
    "ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf": 10,
    "ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf": 1,
    "ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf": 1,
    "Supermarket_V22.1.idf": 1,
}


def _load(path):
    try:
        IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(path))


def _num(v, default=0.0):
    return float(v) if v not in (None, "") else default


def read_storeys(idf):
    objs = idf.idfobjects
    zones = {z.Name: z for z in objs.get("ZONE", [])}
    rules = objs.get("GLOBALGEOMETRYRULES", [])
    relative = bool(rules) and rules[0].Coordinate_System.strip().upper() == "RELATIVE"

    zonelists = {zl.Name.upper(): [v for v in zl.obj[2:] if v] for zl in objs.get("ZONELIST", [])}
    zg_mult = {}
    for zg in objs.get("ZONEGROUP", []):
        m = _num(zg.Zone_List_Multiplier, 1.0)
        for zn in zonelists.get(str(zg.Zone_List_Name).upper(), []):
            zg_mult[zn] = zg_mult.get(zn, 1.0) * m

    spaces = {sp.Name.upper(): sp.Zone_Name for sp in objs.get("SPACE", [])}
    spacelists = {}
    for sl in objs.get("SPACELIST", []):
        spacelists[sl.Name.upper()] = [v for v in sl.obj[2:] if v]

    people_zones = set()
    for p in objs.get("PEOPLE", []):
        target = str(p.obj[2])
        key = target.upper()
        if key in zonelists:
            people_zones.update(zonelists[key])
        elif key in spacelists:
            people_zones.update(spaces[x.upper()] for x in spacelists[key] if x.upper() in spaces)
        elif key in spaces:
            people_zones.add(spaces[key])
        else:
            people_zones.add(target)

    floor_z = {}
    for s in objs.get("BUILDINGSURFACE:DETAILED", []):
        if str(s.Surface_Type).strip().upper() != "FLOOR":
            continue
        zn = s.Zone_Name
        if zn not in zones or not s.coords:
            continue
        z0 = _num(zones[zn].Z_Origin) if relative else 0.0
        z = min(v[2] for v in s.coords) + z0
        floor_z[zn] = min(z, floor_z.get(zn, z))

    elevations_above, elevations_below = [], []
    excl_notarea, excl_people, excl_nofloor = [], [], []
    band_group = {}
    for zn, z in zones.items():
        if zn not in floor_z:
            excl_nofloor.append(zn)
            continue
        counts_area = str(zones[zn].Part_of_Total_Floor_Area).strip().upper() != "NO"
        if not counts_area:
            excl_notarea.append(zn)
            continue
        if zn not in people_zones:
            excl_people.append(zn)
            continue
        target = elevations_above if floor_z[zn] >= -GROUND_TOL_M else elevations_below
        try:
            own = float(zones[zn].Multiplier)
        except (TypeError, ValueError):
            own = 1.0
        own = own if own >= 1 else 1.0
        target.append((floor_z[zn], zg_mult.get(zn, 1.0) * own))

    def bands(items):
        out = []
        for z, g in sorted(items):
            if out and abs(out[-1][0] - z) <= GROUND_TOL_M:
                out[-1][1] = max(out[-1][1], g)
            else:
                out.append([z, g])
        return out

    ba, bb = bands(elevations_above), bands(elevations_below)
    return {
        "storeys": len(ba),
        "storeys_multiplier_aware": int(round(sum(g for _, g in ba))),
        "basements": len(bb),
        "excluded_not_floor_area": excl_notarea,
        "excluded_unoccupied_other": excl_people,
        "excluded_no_floor_surface": excl_nofloor,
        "elevations": [round(z, 2) for z, _ in ba],
    }


def main():
    by_idf = {}
    for arch, f in ARCHETYPE_IDF_MAP.items():
        by_idf.setdefault(f, []).append(arch)
    rows = []
    for f in sorted(by_idf):
        r = read_storeys(_load(BASE_DIR / f))
        doe = DOE_FLOORS.get(f)
        rows.append({
            "archetype": "|".join(sorted(by_idf[f])),
            "idf": f,
            "storeys": r["storeys"],
            "storeys_multiplier_aware": r["storeys_multiplier_aware"],
            "basements": r["basements"],
            "n_excluded_not_floor_area": len(r["excluded_not_floor_area"]),
            "excluded_not_floor_area": ";".join(r["excluded_not_floor_area"]),
            "n_excluded_unoccupied_other": len(r["excluded_unoccupied_other"]),
            "excluded_unoccupied_other": ";".join(r["excluded_unoccupied_other"]),
            "n_excluded_no_floor_surface": len(r["excluded_no_floor_surface"]),
            "excluded_no_floor_surface": ";".join(r["excluded_no_floor_surface"]),
            "floor_elevations_m": ";".join(map(str, r["elevations"])),
            "doe_floors": "" if doe is None else doe,
            "match_doe": "" if doe is None else int(doe == r["storeys"]),
            "match_doe_multiplier_aware": "" if doe is None else int(doe == r["storeys_multiplier_aware"]),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["idf"][:40], r["storeys"], r["storeys_multiplier_aware"], r["basements"], r["doe_floors"], r["n_excluded_not_floor_area"], r["n_excluded_unoccupied_other"])


if __name__ == "__main__":
    main()
