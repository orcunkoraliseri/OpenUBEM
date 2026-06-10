"""Zoning strategy decision and zone construction (DESIGN §3B)."""
import logging

import shapely

logger = logging.getLogger("openubem.geometry")

_ONE_PER_FLOOR = {"MidriseApartment", "HighriseApartment", "TallBuilding", "SuperTallBuilding"}


def decide_zoning_strategy(
    archetype_id: str, footprint_area_m2: float, num_floors: int
) -> str:
    if archetype_id == "OpenUBEMUnknown":
        return "single_zone"
    if footprint_area_m2 < 500 or num_floors == 1:
        return "single_zone"
    if archetype_id in {"MidriseApartment", "HighriseApartment"}:
        return "one_zone_per_floor"
    if archetype_id in {"TallBuilding", "SuperTallBuilding"}:
        return "one_zone_per_floor"
    if footprint_area_m2 >= 500 and num_floors >= 2 and archetype_id not in _ONE_PER_FLOOR:
        return "perimeter_core"
    return "single_zone"


def build_zones(
    osm_id: str,
    footprint_poly: shapely.Polygon,
    archetype_id: str,
    num_floors: int,
    strategy: str,
    floor_to_floor_m: float = 3.5,
    perimeter_depth_m: float = 4.57,
) -> list[dict]:
    coords = list(footprint_poly.exterior.coords)[:-1]

    if strategy == "single_zone":
        return [
            {
                "name": f"{osm_id}_F0_whole",
                "floor_polygon": footprint_poly,
                "coords_m": coords,
                "z_floor": 0.0,
                "z_ceiling": num_floors * floor_to_floor_m,
                "height_m": num_floors * floor_to_floor_m,
                "archetype_id": archetype_id,
            }
        ]

    if strategy == "one_zone_per_floor":
        return [
            {
                "name": f"{osm_id}_F{i}_whole",
                "floor_polygon": footprint_poly,
                "coords_m": coords,
                "z_floor": i * floor_to_floor_m,
                "z_ceiling": (i + 1) * floor_to_floor_m,
                "height_m": floor_to_floor_m,
                "archetype_id": archetype_id,
            }
            for i in range(num_floors)
        ]

    if strategy == "perimeter_core":
        core_poly = footprint_poly.buffer(-perimeter_depth_m)
        if core_poly.is_empty or core_poly.area < 10.0:
            logger.warning(
                "osm_id=%s narrow building: perimeter_core → one_zone_per_floor", osm_id
            )
            return build_zones(
                osm_id, footprint_poly, archetype_id, num_floors,
                "one_zone_per_floor", floor_to_floor_m, perimeter_depth_m,
            )
        # R7: pass full footprint to geomeppy's native core/perim zoning.
        # extrude_geometry detects this placeholder and calls add_block(zoning="core/perim").
        return [{
            "name": f"{osm_id}_perimgroup",
            "mode": "core/perim",
            "floor_polygon": footprint_poly,
            "coords_m": coords,
            "num_floors": num_floors,
            "height_m": floor_to_floor_m,
            "perim_depth_m": perimeter_depth_m,
            "archetype_id": archetype_id,
        }]

    return build_zones(osm_id, footprint_poly, archetype_id, num_floors, "single_zone", floor_to_floor_m, perimeter_depth_m)
