"""Regression test for OPEN-56 in the EU pipeline (T3): write_zone_volumes must
write a positive, correct Zone.Volume for every extruded zone, ending the
EnergyPlus 10 m3 "Indicated Zone Volume" stub caused by negative divergence-
theorem volumes on the by_storey/WHOLE extrusion path."""
from pathlib import Path

from geomeppy import IDF
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.geometry.zoning import build_zones
from openubem.idf.builder import write_zone_volumes
from openubem.idf.surfaces import extrude_geometry

import scripts.run_eu_s1_smoke as run_eu_s1_smoke
import scripts.run_eu_s2_campaign as run_eu_s2_campaign

TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")


def _fresh_idf() -> IDF:
    from eppy.modeleditor import IDDAlreadySetError
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


def test_write_zone_volumes_positive_and_correct():
    idf = _fresh_idf()
    poly = box(0, 0, 10, 10)
    num_floors = 3
    floor_to_floor = 3.5

    zones = build_zones("test_bldg", poly, "MidriseApartment", num_floors, "one_zone_per_floor",
                        floor_to_floor_m=floor_to_floor)
    extrude_geometry(idf, zones, [])
    write_zone_volumes(idf, zones)

    zone_bunches = {z.Name: z for z in idf.idfobjects["ZONE"]}
    floor_area_by_zone: dict[str, float] = {}
    for surf in idf.getsurfaces("floor"):
        floor_area_by_zone[surf.Zone_Name] = floor_area_by_zone.get(surf.Zone_Name, 0.0) + surf.area

    checked = 0
    for z in zones:
        if not z.get("extruded"):
            continue
        zname = z["name"]
        zone_bunch = zone_bunches.get(zname)
        assert zone_bunch is not None, f"zone {zname} missing from IDF"

        volume = zone_bunch.Volume
        assert volume != "autocalculate", f"zone {zname}: Volume left as 'autocalculate'"
        assert isinstance(volume, (int, float)), f"zone {zname}: Volume is not numeric: {volume!r}"
        assert volume > 0, f"zone {zname}: Volume must be positive, got {volume}"

        expected = floor_area_by_zone[zname] * z["height_m"]
        rel_diff = abs(volume - expected) / expected
        assert rel_diff < 1e-6, (
            f"zone {zname}: Volume {volume} != expected {expected} (floor_area x height_m)"
        )
        checked += 1

    assert checked == num_floors, f"expected {num_floors} extruded zones checked, got {checked}"


def test_orient_zone_footprints_fixes_floor_winding():
    """T2 determined empirically (grep for 'Floor is upside down' on one building)
    that sign=1.0 (counter-clockwise exterior ring) eliminates geomeppy's
    GetVertices upside-down warning; this pins that orientation as a regression."""
    ccw_poly = box(0, 0, 10, 10)
    assert ccw_poly.exterior.is_ccw
    cw_poly = orient(ccw_poly, sign=-1.0)
    assert not cw_poly.exterior.is_ccw

    for poly in (ccw_poly, cw_poly):
        zones = [{"floor_polygon": poly, "coords_m": list(poly.exterior.coords)[:-1]}]
        run_eu_s2_campaign._orient_zone_footprints(zones, sign=1.0)

        oriented = zones[0]["floor_polygon"]
        assert isinstance(oriented, Polygon)
        assert oriented.exterior.is_ccw, "orient(sign=1.0) must yield a counter-clockwise exterior ring"
        assert zones[0]["coords_m"] == list(oriented.exterior.coords)[:-1]


def test_s1_and_s2_orient_zone_footprints_agree():
    """The two EU runners must normalise winding to the same sign, or a smoke
    run and a campaign run silently diverge on the same input footprint."""
    cw_poly = orient(box(0, 0, 10, 10), sign=-1.0)
    assert not cw_poly.exterior.is_ccw

    zones_s1 = [{"floor_polygon": cw_poly, "coords_m": list(cw_poly.exterior.coords)[:-1]}]
    zones_s2 = [{"floor_polygon": cw_poly, "coords_m": list(cw_poly.exterior.coords)[:-1]}]

    run_eu_s1_smoke._orient_zone_footprints(zones_s1, sign=run_eu_s1_smoke.ZONE_WINDING_SIGN)
    run_eu_s2_campaign._orient_zone_footprints(zones_s2, sign=run_eu_s2_campaign.ZONE_WINDING_SIGN)

    oriented_s1 = zones_s1[0]["floor_polygon"]
    oriented_s2 = zones_s2[0]["floor_polygon"]
    assert oriented_s1.exterior.is_ccw == oriented_s2.exterior.is_ccw
    assert zones_s1[0]["coords_m"] == zones_s2[0]["coords_m"]
