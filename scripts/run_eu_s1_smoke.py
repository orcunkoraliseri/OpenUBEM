"""EU-04 S1 geometry-to-EnergyPlus design-day smoke runner (D-EU-04-H, Option H1).

Frozen 12-building sample from
docs/docs_ACTIVE/europeanLocations/prompts/EXECUTOR_PROMPT_EU-04_s1_smoke_2026-08-25.md §2.
This is a runner, not a test: it measures two independent axes on real French
footprints and never launders a fallback into a dwelling-layout success.

Axis A (dwelling-layout status) is re-derived from the manifest polygon by the
same predicates the manager's census used: a footprint is REFUSED_BY_LAYOUT_CONTRACT
if it is non-convex or has a courtyard hole; otherwise
generate_european_dwelling_layout is actually called and its own emitted/fallback
result is used verbatim.

Axis B (design-day smoke outcome) always attempts an EnergyPlus run: zones come
from european_layout_to_zone_specs where Axis A emitted, and from
build_zones(..., strategy="one_zone_per_floor") otherwise. S1 produces no energy
number -- design-day sizing only.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry.polygon import orient

from openubem.config import ENERGYPLUS_IDD_PATH, ENERGYPLUS_PATH
from openubem.geometry.european_residential import (
    allocate_european_dwellings,
    european_layout_to_zone_specs,
    generate_european_dwelling_layout,
)
from openubem.geometry.zoning import build_zones
from openubem.idf.european_controls import add_european_heating_controls
from openubem.idf.builder import write_zone_volumes
from openubem.idf.surfaces import audit_reciprocal_interzone_wall_surfaces, extrude_geometry

MANIFEST_PATH = Path("openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg")
FR_ARCHETYPES_PATH = Path("openubem/data/construction/tabula_archetypes_fr.json")
EVIDENCE_DIR = Path("openubem/outputs/eu_evidence/EU-04")
SMOKE_ERR_DIR = EVIDENCE_DIR / "s1_smoke"
MANIFEST_CSV_PATH = EVIDENCE_DIR / "s1_smoke_manifest.csv"
PROJECTED_CRS = "EPSG:32631"
FLOOR_TO_FLOOR_M = 3.0
FLOOR_TO_FLOOR_NOTE = "floor_to_floor_m=3.0 pinned geometry-smoke constant, not a physical claim about Lyon"
ZONE_WINDING_SIGN = 1.0

IDF_HEADER = """Version,23.1;
Timestep,4;
Building,EU Layout Design Day,0,Suburbs,0.0001,0.000001,MinimalShadowing,30,1;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,Yes,Yes,No,Yes,No,No,1;
Site:Location,EU Site,40,-75,-5,0;
SizingPeriod:DesignDay,EU Cold Day,1,21,WinterDesignDay,-10,0,,,Wetbulb,-10,,,,,101325,0,0,No,No,No,ASHRAEClearSky,,,,0;
ScheduleTypeLimits,Any Number;
"""

# Frozen S1 sample -- §2 of the executor prompt. Do not re-select or re-derive
# building_type / archetype_id / year_built / observed_dwellings / observed_storeys;
# these are frozen inputs, not measurements this runner makes.
FROZEN_ROWS: list[dict[str, object]] = [
    {"building_id": "BATIMENT0000000240877122_part0", "building_type": "SFH", "archetype_id": "FR.N.SFH.01.Gen.ReEx.001.001", "year_built": 1800, "observed_dwellings": 1, "observed_storeys": 1, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000240877182_part0", "building_type": "SFH", "archetype_id": "FR.N.SFH.01.Gen.ReEx.001.001", "year_built": 1860, "observed_dwellings": 1, "observed_storeys": 2, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000240879451_part0", "building_type": "SFH", "archetype_id": "FR.N.SFH.01.Gen.ReEx.001.001", "year_built": 1805, "observed_dwellings": 1, "observed_storeys": 1, "expected_shape_class": "simple", "expected_layout_status": "FALLBACK_PENDING_LAYOUT", "expected_layout_reason": "NARROW_FOOTPRINT_LT_8M"},
    {"building_id": "BATIMENT0000000240879618_part0", "building_type": "TH", "archetype_id": "FR.N.TH.01.Gen.ReEx.001.001", "year_built": 1900, "observed_dwellings": 1, "observed_storeys": 2, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000240879754_part0", "building_type": "TH", "archetype_id": "FR.N.TH.01.Gen.ReEx.001.001", "year_built": 1880, "observed_dwellings": 1, "observed_storeys": 4, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000240880050_part0", "building_type": "TH", "archetype_id": "FR.N.TH.01.Gen.ReEx.001.001", "year_built": 1720, "observed_dwellings": 1, "observed_storeys": 4, "expected_shape_class": "simple", "expected_layout_status": "FALLBACK_PENDING_LAYOUT", "expected_layout_reason": "NARROW_FOOTPRINT_LT_8M"},
    {"building_id": "BATIMENT0000000240877101_part0", "building_type": "MFH", "archetype_id": "FR.N.MFH.01.Gen.ReEx.001.001", "year_built": 1860, "observed_dwellings": 10, "observed_storeys": 4, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000240877183_part0", "building_type": "MFH", "archetype_id": "FR.N.MFH.01.Gen.ReEx.001.001", "year_built": 1890, "observed_dwellings": 5, "observed_storeys": 4, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000013365727_part0", "building_type": "MFH", "archetype_id": "FR.N.MFH.07.Gen.ReEx.001.001", "year_built": 1998, "observed_dwellings": 2, "observed_storeys": 3, "expected_shape_class": "simple", "expected_layout_status": "FALLBACK_PENDING_LAYOUT", "expected_layout_reason": "NARROW_FOOTPRINT_LT_8M"},
    {"building_id": "BATIMENT0000000240877151_part0", "building_type": "AB", "archetype_id": "FR.N.AB.01.Gen.ReEx.001.001", "year_built": 1900, "observed_dwellings": 17, "observed_storeys": 6, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000240877527_part0", "building_type": "AB", "archetype_id": "FR.N.AB.01.Gen.ReEx.001.001", "year_built": 1860, "observed_dwellings": 15, "observed_storeys": 5, "expected_shape_class": "irregular", "expected_layout_status": "REFUSED_BY_LAYOUT_CONTRACT", "expected_layout_reason": "NON_CONVEX_FOOTPRINT"},
    {"building_id": "BATIMENT0000000240879449_part0", "building_type": "AB", "archetype_id": "FR.N.AB.07.Gen.ReEx.001.001", "year_built": 1999, "observed_dwellings": 28, "observed_storeys": 6, "expected_shape_class": "simple", "expected_layout_status": "DWELLING_LAYOUT_EMITTED", "expected_layout_reason": ""},
]

CONVEXITY_TOLERANCE_M2 = 1e-8


def _load_manifest_native() -> gpd.GeoDataFrame:
    """Load the manifest in its own native CRS -- do not reproject.

    D-EU-04-H CP-1 measured that reprojecting to EPSG:2154 makes
    generate_european_dwelling_layout's fixed-origin rotation
    (openubem/geometry/european_residential.py:504) accumulate floating-point
    noise past the partition audit's absolute topology_tolerance_m2=1e-8
    (:643), spuriously failing row 12. The frozen §2 table and
    s1_layout_reachability_census.csv were both produced in the manifest's
    native CRS, EPSG:32631; registered as an [OPEN] finding in
    OpenUBEM_debug_References.md ch.5.
    """
    if not MANIFEST_PATH.is_file():
        raise ValueError(f"Manifest does not exist: {MANIFEST_PATH}")
    gdf = gpd.read_file(MANIFEST_PATH)
    if gdf.crs is None or gdf.crs.to_string() != PROJECTED_CRS:
        raise ValueError(f"Manifest CRS is {gdf.crs}, expected native {PROJECTED_CRS}")
    return gdf


def _load_fr_record(archetype_id: str) -> dict[str, object]:
    payload = json.loads(FR_ARCHETYPES_PATH.read_text(encoding="utf-8"))
    for record in payload["records"]:
        if record["archetype_id"] == archetype_id:
            return record
    raise ValueError(f"archetype_id not found in FR TABULA registry: {archetype_id!r}")


def compute_axis_a(footprint, *, building_type: str, archetype_id: str, observed_dwellings: int, observed_storeys: int):
    """Independently reproduce Axis A from the real footprint geometry.

    Returns (units_per_floor, footprint_area_m2, is_convex, has_courtyard,
    shape_class, layout_status, layout_reason, layout_or_none).
    """
    if footprint.geom_type != "Polygon":
        return (
            None, None, None, None, "irregular",
            "REFUSED_BY_LAYOUT_CONTRACT", "MULTIPART_FOOTPRINT", None,
        )

    footprint_area_m2 = float(footprint.area)
    is_convex = abs(float(footprint.convex_hull.area) - footprint_area_m2) <= CONVEXITY_TOLERANCE_M2
    has_courtyard = bool(footprint.interiors)
    shape_class = "simple" if (is_convex and not has_courtyard) else "irregular"

    allocation = allocate_european_dwellings(
        archetype_id=archetype_id,
        building_type=building_type,
        n_apartment=observed_dwellings,
        n_storey=observed_storeys,
        plate_area_m2=footprint_area_m2,
    )
    units_per_floor = allocation.units_per_floor

    if not is_convex or has_courtyard:
        reason_parts = []
        if not is_convex:
            reason_parts.append("NON_CONVEX_FOOTPRINT")
        if has_courtyard:
            reason_parts.append("COURTYARD_HOLE")
        return (
            units_per_floor, footprint_area_m2, is_convex, has_courtyard, shape_class,
            "REFUSED_BY_LAYOUT_CONTRACT", ";".join(reason_parts), None,
        )

    layout = generate_european_dwelling_layout(footprint, requested_dwelling_count=units_per_floor)
    if layout.dwelling_layout_emitted:
        return (
            units_per_floor, footprint_area_m2, is_convex, has_courtyard, shape_class,
            "DWELLING_LAYOUT_EMITTED", "", layout,
        )
    return (
        units_per_floor, footprint_area_m2, is_convex, has_courtyard, shape_class,
        "FALLBACK_PENDING_LAYOUT", layout.fallback_reason or "", layout,
    )


def _add_smoke_construction(idf) -> None:
    idf.newidfobject(
        "MATERIAL:NOMASS",
        Name="EU Layout Smoke R2",
        Roughness="MediumRough",
        Thermal_Resistance=2.0,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject(
        "CONSTRUCTION",
        Name="EU Layout Smoke Construction",
        Outside_Layer="EU Layout Smoke R2",
    )
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        surface.Construction_Name = "EU Layout Smoke Construction"


def run_t01(dry_run: bool) -> list[dict[str, object]]:
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    manifest = _load_manifest_native()
    manifest_ids = set(manifest["osm_id"].astype(str))

    results = []
    for row in FROZEN_ROWS:
        building_id = row["building_id"]
        if building_id not in manifest_ids:
            raise ValueError(f"Frozen building_id missing from manifest: {building_id!r}")
        footprint = manifest.loc[manifest["osm_id"].astype(str) == building_id, "geometry"].iloc[0]

        (
            units_per_floor, footprint_area_m2, is_convex, has_courtyard, shape_class,
            layout_status, layout_reason, layout,
        ) = compute_axis_a(
            footprint,
            building_type=row["building_type"],
            archetype_id=row["archetype_id"],
            observed_dwellings=row["observed_dwellings"],
            observed_storeys=row["observed_storeys"],
        )

        matches_expected = (
            layout_status == row["expected_layout_status"]
            and layout_reason == row["expected_layout_reason"]
        )
        results.append(
            {
                **row,
                "footprint": footprint,
                "units_per_floor": units_per_floor,
                "footprint_area_m2": footprint_area_m2,
                "is_convex": is_convex,
                "has_courtyard": has_courtyard,
                "shape_class": shape_class,
                "layout_status": layout_status,
                "layout_reason": layout_reason,
                "layout": layout,
                "matches_expected": matches_expected,
            }
        )

    print("CP-1 Axis A results (row / expected vs derived / match):")
    for r in results:
        expected = f"{r['expected_layout_status']}" + (f" / {r['expected_layout_reason']}" if r["expected_layout_reason"] else "")
        derived = f"{r['layout_status']}" + (f" / {r['layout_reason']}" if r["layout_reason"] else "")
        print(f"  {r['building_id']}: expected=[{expected}] derived=[{derived}] match={r['matches_expected']}")

    if not dry_run:
        mismatches = [r["building_id"] for r in results if not r["matches_expected"]]
        if mismatches:
            raise ValueError(f"Axis A mismatch against §2 for: {mismatches}")

    return results


def _orient_zone_footprints(zones: list[dict[str, object]], *, sign: float = 1.0) -> None:
    """Normalise each zone's floor_polygon winding in place (fixes GetVertices upside-down warning)."""
    for zone in zones:
        oriented = orient(zone["floor_polygon"], sign=sign)
        zone["floor_polygon"] = oriented
        zone["coords_m"] = list(oriented.exterior.coords)[:-1]


def run_t02(rows: list[dict[str, object]]) -> None:
    from geomeppy import IDF

    SMOKE_ERR_DIR.mkdir(parents=True, exist_ok=True)
    energyplus_exe = Path(ENERGYPLUS_PATH) / ("energyplus.exe" if sys.platform == "win32" else "energyplus")

    for r in rows:
        building_id = r["building_id"]
        archetype_id = r["archetype_id"]
        record = _load_fr_record(archetype_id)
        footprint = r["footprint"]

        if r["layout_status"] == "DWELLING_LAYOUT_EMITTED":
            zones = european_layout_to_zone_specs(r["layout"], building_id=building_id, height_m=FLOOR_TO_FLOOR_M)
            zone_source = "EUROPEAN_DWELLING_LAYOUT"
        else:
            zones = build_zones(
                building_id,
                footprint,
                archetype_id,
                num_floors=int(r["observed_storeys"]),
                strategy="one_zone_per_floor",
                floor_to_floor_m=FLOOR_TO_FLOOR_M,
            )
            zone_source = "FALLBACK_ONE_ZONE_PER_FLOOR"
        r["zone_source"] = zone_source
        r["zone_count"] = len(zones)

        notes = [FLOOR_TO_FLOOR_NOTE]
        if r["has_courtyard"]:
            notes.append("courtyard hole filled: exterior ring only extruded")
        if building_id == "BATIMENT0000000240879449_part0":
            notes.append("CRS_NATIVE_32631_REQUIRED_SEE_DEBUGREF_CH5")

        eplus_status = "NOT_ATTEMPTED"
        eplus_first_severe = ""
        runtime_s = 0.0
        party_wall_triple = None

        tmp_root = (SMOKE_ERR_DIR / f"_tmp_{building_id}").resolve()
        if tmp_root.exists():
            shutil.rmtree(tmp_root)
        tmp_root.mkdir(parents=True)
        try:
            idf_path = tmp_root / f"{building_id}.idf"
            idf_path.write_text(IDF_HEADER, encoding="utf-8")
            idf = IDF(str(idf_path))
            _orient_zone_footprints(zones, sign=ZONE_WINDING_SIGN)
            extrude_geometry(idf, zones, [])
            write_zone_volumes(idf, zones)
            _add_smoke_construction(idf)
            for zone in zones:
                idf.newidfobject(
                    "SIZING:ZONE",
                    Zone_or_ZoneList_Name=zone["name"],
                    Zone_Cooling_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
                    Zone_Cooling_Design_Supply_Air_Temperature=13.0,
                    Zone_Heating_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
                    Zone_Heating_Design_Supply_Air_Temperature=50.0,
                    Zone_Cooling_Design_Supply_Air_Humidity_Ratio=0.008,
                    Zone_Heating_Design_Supply_Air_Humidity_Ratio=0.008,
                )
                add_european_heating_controls(idf, record, zone["name"])
            idf.saveas(str(idf_path))

            if r["layout_status"] == "DWELLING_LAYOUT_EMITTED":
                audit = audit_reciprocal_interzone_wall_surfaces(IDF(str(idf_path)))
                party_wall_triple = (audit.passed, audit.party_face_count, audit.reciprocal_pair_count)
                notes.append(
                    f"party_wall_audit: passed={audit.passed} party_face_count={audit.party_face_count} reciprocal_pair_count={audit.reciprocal_pair_count}"
                )

            start = time.perf_counter()
            try:
                result = subprocess.run(
                    [str(energyplus_exe), "-x", "-r", "-d", str(tmp_root), str(idf_path)],
                    cwd=tmp_root,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                runtime_s = time.perf_counter() - start
                err_path = tmp_root / "eplusout.err"
                err_text = err_path.read_text(encoding="utf-8", errors="replace") if err_path.is_file() else ""
                if result.returncode == 0 and "Completed Successfully" in err_text:
                    eplus_status = "EPLUS_COMPLETED"
                else:
                    fatal_match = re.search(r"^.*\*\*\s*Fatal\s*\*\*.*$", err_text, re.MULTILINE)
                    severe_match = re.search(r"^.*\*\*\s*Severe\s*\*\*.*$", err_text, re.MULTILINE)
                    if fatal_match:
                        eplus_first_severe = fatal_match.group(0).strip()[:300]
                        eplus_status = "EPLUS_FATAL"
                    elif severe_match:
                        eplus_first_severe = severe_match.group(0).strip()[:300]
                        eplus_status = "EPLUS_SEVERE"
                    else:
                        eplus_status = "EPLUS_FATAL"
                        eplus_first_severe = f"returncode={result.returncode}; no Severe/Fatal line found in eplusout.err"
                if err_path.is_file():
                    shutil.copy2(err_path, SMOKE_ERR_DIR / f"{building_id}.err")
            except subprocess.TimeoutExpired:
                runtime_s = time.perf_counter() - start
                eplus_status = "EPLUS_TIMEOUT"
                eplus_first_severe = "subprocess.run timed out after 180s"
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)

        r["eplus_status"] = eplus_status
        r["eplus_first_severe"] = eplus_first_severe
        r["runtime_s"] = round(runtime_s, 3)
        r["party_wall_triple"] = party_wall_triple
        r["notes"] = "; ".join(notes)

        print(f"  {building_id}: zone_source={zone_source} zone_count={len(zones)} eplus_status={eplus_status} runtime_s={r['runtime_s']}")
        if eplus_status not in ("EPLUS_COMPLETED",):
            print(f"    first_severe: {eplus_first_severe}")


def run_t03(rows: list[dict[str, object]]) -> pd.DataFrame:
    columns = [
        "building_id", "building_type", "archetype_id", "year_built",
        "observed_dwellings", "observed_storeys", "units_per_floor",
        "footprint_area_m2", "is_convex", "has_courtyard", "shape_class",
        "zone_source", "zone_count", "layout_status", "layout_reason",
        "eplus_status", "eplus_first_severe", "runtime_s", "notes",
    ]
    records = []
    for r in rows:
        layout_reason = r["layout_reason"] if r["layout_reason"] else "NONE"
        records.append(
            {
                "building_id": r["building_id"],
                "building_type": r["building_type"],
                "archetype_id": r["archetype_id"],
                "year_built": r["year_built"],
                "observed_dwellings": r["observed_dwellings"],
                "observed_storeys": r["observed_storeys"],
                "units_per_floor": r["units_per_floor"],
                "footprint_area_m2": round(r["footprint_area_m2"], 3),
                "is_convex": r["is_convex"],
                "has_courtyard": r["has_courtyard"],
                "shape_class": r["shape_class"],
                "zone_source": r["zone_source"],
                "zone_count": r["zone_count"],
                "layout_status": r["layout_status"],
                "layout_reason": layout_reason,
                "eplus_status": r["eplus_status"],
                "eplus_first_severe": r["eplus_first_severe"],
                "runtime_s": r["runtime_s"],
                "notes": r["notes"],
            }
        )
    frame = pd.DataFrame.from_records(records, columns=columns)
    assert len(frame) == 12, f"expected exactly 12 rows, got {len(frame)}"
    assert set(frame["layout_status"]) <= {
        "DWELLING_LAYOUT_EMITTED", "FALLBACK_PENDING_LAYOUT", "REFUSED_BY_LAYOUT_CONTRACT",
    }, f"unexpected layout_status tokens: {set(frame['layout_status'])}"

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(MANIFEST_CSV_PATH, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run T01 (Axis A) only, write nothing")
    args = parser.parse_args()

    rows = run_t01(dry_run=args.dry_run)
    if args.dry_run:
        return

    run_t02(rows)
    frame = run_t03(rows)
    print(f"Wrote {MANIFEST_CSV_PATH} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
