"""T06 LIVE_SMOKE (build-only, NO simulation): elevator emitter through the full builder.

For each elevator archetype: build one real IDF via BuildingIDF.build and assert the
Elevators ElectricEquipment object is present with a plausible non-zero design level.
Prints the emitted W and the implied kWh/m2 (density x DOE-schedule annual-average x 8760h),
which is size-invariant and must match the CP-1 magnitude table.

For a no-elevator archetype (SmallOffice): build it twice — once normally, once with
assign_elevators monkeypatched to a no-op (== the pre-change code path) — and assert the
two IDFs are BYTE-IDENTICAL, proving the elevator wiring is inert for absent archetypes.

Run:  .venv/Scripts/python.exe scripts/validation/elevators_live_smoke.py
NEVER runs EnergyPlus; build + inspect only.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem import idf as _idf_pkg  # noqa: F401
import openubem.idf.builder as builder_mod
from openubem.idf.builder import BuildingIDF
from openubem.semantic.schedules import build_schedule_library

ELEV_JSON = ROOT / "openubem" / "data" / "loads" / "elevators_by_archetype.json"

# Envelope/loads fields a manifest row needs to flow through the full builder (mirrors
# tests/fixtures/synthetic_10_buildings.py _COMMON).
_COMMON = {
    "epw_path": str(ROOT / "tests" / "fixtures" / "synthetic.epw"),
    "provenance_climate_zone": "DEFAULT", "climate_zone": "3A",
    "vintage_standard": "DOERef1980to2004",
    "u_roof_w_m2k": 0.25, "u_wall_w_m2k": 0.40, "u_floor_w_m2k": 0.35,
    "u_window_w_m2k": 2.5, "shgc_window": 0.40,
    "assembly_roof": "NOMASS", "assembly_wall": "NOMASS",
    "provenance_u_roof": "DEFAULT", "provenance_u_wall": "DEFAULT",
    "provenance_u_window": "DEFAULT", "provenance_u_floor": "DEFAULT",
    "provenance_envelope": "DEFAULT", "infiltration_m3_s_m2": 0.0003, "wwr": 0.30,
    "lighting_w_m2": 10.76, "equipment_w_m2": 8.07, "occupant_m2_per_person": 9.3,
    "provenance_lighting": "DEFAULT", "provenance_equipment": "DEFAULT",
    "provenance_occupancy": "DEFAULT",
    "heating_setpoint_c": 21.0, "cooling_setpoint_c": 24.0,
    "heating_setback_c": 16.0, "cooling_setup_c": 30.0,
    "provenance_heating_setpoint": "DEFAULT", "provenance_cooling_setpoint": "DEFAULT",
    "data_quality_flag": "",
}


def _idd_safe():
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass


def _row(osm_id, arch, geom, levels, footprint_area_m2):
    d = {"osm_id": osm_id, "archetype_id": arch, "geometry": geom,
         "levels": levels, "height_m": float("nan"),
         "footprint_area_m2": footprint_area_m2}
    d.update(_COMMON)
    return d


def _day_avg(pairs):
    total = 0.0
    prev = 0.0
    for until, val in pairs:
        total += (until - prev) * val
        prev = until
    return total / 24.0


# DOE BLDG_ELEVATORS annual-average fraction per archetype (design-day rows excluded;
# they do not run in an annual sim). Mirrors the CP-1 magnitude computation.
_SHARED = _day_avg([(4, 0.12), (5, 0.12), (6, 0.20), (7, 0.40), (9, 0.50), (10, 0.35),
                    (16, 0.15), (17, 0.35), (19, 0.50), (21, 0.40), (22, 0.30),
                    (23, 0.20), (24, 0.12)])
_MO = (5 * _day_avg([(7, 0.12), (8, 0.35), (9, 0.69), (10, 0.43), (11, 0.37), (12, 0.43),
                     (13, 0.58), (14, 0.48), (15, 0.37), (16, 0.37), (17, 0.46), (18, 0.62),
                     (19, 0.12), (20, 0.12), (21, 0.12), (24, 0.12)])
       + _day_avg([(7, 0.12), (8, 0.16), (9, 0.14), (10, 0.21), (11, 0.18), (12, 0.25),
                   (13, 0.21), (14, 0.13), (15, 0.12), (16, 0.12), (17, 0.12), (18, 0.12),
                   (24, 0.12)]) + 0.12) / 7
_HOSP = (5 * _day_avg([(7, 0.2), (8, 0.5), (9, 0.75), (18, 1.0), (19, 0.52), (20, 0.52),
                       (21, 0.52), (22, 0.28), (24, 0.2)])
         + _day_avg([(7, 0.2), (8, 0.4), (9, 0.46), (10, 0.7), (11, 0.7), (12, 0.7),
                     (13, 0.51), (14, 0.51), (15, 0.51), (16, 0.51), (17, 0.51), (18, 0.25),
                     (24, 0.2)]) + _day_avg([(8, 0.2), (16, 0.4), (24, 0.2)])) / 7
_OUT = (5 * _day_avg([(7, 0.12), (8, 0.5), (9, 0.75), (18, 1.0), (19, 0.52), (20, 0.52),
                      (21, 0.52), (22, 0.28), (24, 0.12)])
        + _day_avg([(7, 0.12), (8, 0.4), (9, 0.46), (10, 0.7), (11, 0.7), (12, 0.7),
                    (13, 0.51), (14, 0.51), (15, 0.51), (16, 0.51), (17, 0.51), (18, 0.25),
                    (24, 0.12)]) + _day_avg([(8, 0.12), (16, 0.4), (24, 0.12)])) / 7
_SEC = (5 * _day_avg([(8, 0.12), (15, 0.30), (16, 0.15), (24, 0.12)]) + 2 * 0.12) / 7
_COL = (5 * _day_avg([(8, 0.0), (15, 0.3), (16, 0.2), (24, 0.0)])) / 7
_ANNUAL_FRAC = {
    "LargeOffice": _SHARED, "LargeHotel": _SHARED, "SmallHotel": _SHARED,
    "HighriseApartment": _SHARED, "MidriseApartment": _SHARED,
    "MediumOffice": _MO, "Hospital": _HOSP, "Outpatient": _OUT,
    "SecondarySchool": _SEC, "College": _COL,
}

# CP-1 reference kWh/m2/yr (post area-correction) for cross-check.
_CP1_KWH_M2 = {
    "LargeOffice": 6.86, "MediumOffice": 3.54, "LargeHotel": 8.98, "SmallHotel": 4.93,
    "Hospital": 6.79, "Outpatient": 8.00, "HighriseApartment": 3.07,
    "MidriseApartment": 3.16, "SecondarySchool": 0.84, "College": 3.00,
}


def _build_one(arch, out_dir, gdf, levels=6, footprint=1200.0):
    geom = box(0, 0, 40, 30)  # 1200 m² footprint
    row = _row(f"way/SMOKE_{arch}", arch, geom, levels, footprint)
    import pandas as pd
    b = BuildingIDF(pd.Series(row), resolution_mode="auto")
    manifest = b.build(gdf, {arch: build_schedule_library(arch)}, out_dir)
    return manifest


def main():
    _idd_safe()
    elev = json.loads(ELEV_JSON.read_text())
    archetypes = [k for k in elev if not k.startswith("_")]

    print("=" * 78)
    print("T06 LIVE_SMOKE — elevator emitter, build-only (NO simulation)")
    print("=" * 78)

    tmp = Path(tempfile.mkdtemp(prefix="elev_smoke_"))
    (tmp / "idfs").mkdir(parents=True, exist_ok=True)

    # one-row-per-build GDF (context discovery needs a GDF; a single self row is fine)
    import pandas as pd

    all_ok = True
    print(f"\n{'archetype':<18}{'emitted_W':>12}{'total_m2':>10}{'kWh/m2/yr':>11}"
          f"{'CP-1':>8}{'  status'}")
    print("-" * 78)
    for arch in sorted(archetypes):
        geom = box(0, 0, 40, 30)
        row = _row(f"way/SMOKE_{arch}", arch, geom, 6, 1200.0)
        gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
        manifest = _build_one(arch, tmp, gdf)
        idf_path = manifest.get("idf_path", "")
        if not idf_path or not Path(idf_path).exists():
            print(f"{arch:<18}{'BUILD FAILED — ' + manifest.get('generation_status', '?'):>50}")
            all_ok = False
            continue
        built = IDF(str(idf_path))
        elevs = [e for e in built.idfobjects["ELECTRICEQUIPMENT"]
                 if e.EndUse_Subcategory == "Elevators"]
        if len(elevs) != 1:
            print(f"{arch:<18}  FAIL: expected 1 Elevators object, got {len(elevs)}")
            all_ok = False
            continue
        w = float(elevs[0].Design_Level)
        proto_area = elev[arch]["prototype_floor_area_m2"]
        density = elev[arch]["design_level_w"] / proto_area
        total_area = w / density  # == footprint × floors used by the emitter
        kwh_m2 = density * _ANNUAL_FRAC[arch] * 8760 / 1000
        cp1 = _CP1_KWH_M2[arch]
        ok = (w > 0) and abs(kwh_m2 - cp1) < 0.05
        all_ok = all_ok and ok
        print(f"{arch:<18}{w:>12.2f}{total_area:>10.1f}{kwh_m2:>11.3f}{cp1:>8.2f}"
              f"{'  OK' if ok else '  MISMATCH'}")

    # ── Byte-identity for a no-elevator archetype (SmallOffice) ──────────────
    print("\n" + "-" * 78)
    print("Byte-identity check — SmallOffice (no elevator object in table):")
    geom = box(0, 0, 40, 30)
    row = _row("way/SMOKE_SmallOffice", "SmallOffice", geom, 2, 1200.0)
    gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")

    out_a = Path(tempfile.mkdtemp(prefix="elev_smoke_A_"))
    (out_a / "idfs").mkdir(parents=True, exist_ok=True)
    b1 = BuildingIDF(pd.Series(row), resolution_mode="auto")
    m1 = b1.build(gdf, {"SmallOffice": build_schedule_library("SmallOffice")}, out_a)
    bytes_with_call = Path(m1["idf_path"]).read_bytes()

    # Monkeypatch assign_elevators → no-op (== pre-change code path), rebuild, diff.
    orig = builder_mod.assign_elevators
    builder_mod.assign_elevators = lambda idf, row, zones: []
    try:
        out_b = Path(tempfile.mkdtemp(prefix="elev_smoke_B_"))
        (out_b / "idfs").mkdir(parents=True, exist_ok=True)
        b2 = BuildingIDF(pd.Series(row), resolution_mode="auto")
        m2 = b2.build(gdf, {"SmallOffice": build_schedule_library("SmallOffice")}, out_b)
        bytes_no_call = Path(m2["idf_path"]).read_bytes()
    finally:
        builder_mod.assign_elevators = orig

    identical = bytes_with_call == bytes_no_call
    n_elev = len([e for e in IDF(m1["idf_path"]).idfobjects["ELECTRICEQUIPMENT"]
                  if e.EndUse_Subcategory == "Elevators"])
    print(f"  SmallOffice Elevators objects emitted: {n_elev} (expected 0)")
    print(f"  byte-identical (with-call vs no-op patch): {identical}")
    byte_ok = identical and n_elev == 0
    all_ok = all_ok and byte_ok

    print("\n" + "=" * 78)
    print(f"RESULT: {'ALL SMOKE CHECKS PASSED' if all_ok else 'FAILURES ABOVE'}")
    print("=" * 78)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
