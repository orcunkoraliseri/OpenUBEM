"""Zoning strategy decision and zone construction (DESIGN §3B)."""
import logging

import shapely

from openubem.geometry import layoutGenerator, layout_assigner

logger = logging.getLogger("openubem.geometry")

_ONE_PER_FLOOR = {"MidriseApartment", "HighriseApartment", "TallBuilding", "SuperTallBuilding"}


def decide_zoning_strategy(
    archetype_id: str, footprint_area_m2: float, num_floors: int,
    resolution_mode: str = "auto",
) -> str:
    if resolution_mode == "building":
        return "single_zone"
    if resolution_mode == "floor":
        return "one_zone_per_floor"
    if resolution_mode == "fast_zone":
        return "perimeter_core"
    if resolution_mode in ("layout_assign", "layout_assigner"):
        return "layout_assign"
    if resolution_mode == "zone":
        # Opt-in room-level layout (layoutGenerator). Units+corridor archetypes get
        # corridor-spine room packing; every other archetype degrades to generic
        # core/perimeter (a superset of fast_zone), so requesting 'zone' fleet-wide
        # never raises — the pipeline's dummy-archetype mode check stays valid.
        spec = layoutGenerator.MODULE_SPECS.get(archetype_id)
        if spec and spec.get("family") == "units_corridor":
            return "room_layout"
        return "perimeter_core"
    if resolution_mode != "auto":
        raise ValueError(f"unknown resolution_mode: {resolution_mode!r}")
    # single_zone only for genuine 1-floor buildings (DESIGN §262 restricted to num_floors==1;
    # manager ruling 2026-06-17: resolves inconsistency with DESIGN §300 floor_area=footprint×n_floors)
    if num_floors == 1:
        return "single_zone"
    if footprint_area_m2 >= 500 and archetype_id not in _ONE_PER_FLOOR and archetype_id != "OpenUBEMUnknown":
        return "perimeter_core"
    return "one_zone_per_floor"


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
                "num_floors": num_floors,
                "floor_area_m2": footprint_poly.area * num_floors,
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

    if strategy == "room_layout":
        zones = layoutGenerator.generate_layout(
            osm_id, footprint_poly, archetype_id, num_floors, floor_to_floor_m,
        )
        if not zones:
            logger.warning(
                "osm_id=%s room_layout unsupported (shape/archetype) → one_zone_per_floor",
                osm_id,
            )
            fallback = build_zones(
                osm_id, footprint_poly, archetype_id, num_floors,
                "one_zone_per_floor", floor_to_floor_m, perimeter_depth_m,
            )
            # Mark so the manifest reports the effective strategy, not the requested one:
            # generate_layout's 1% area-conservation net degraded this footprint.
            for z in fallback:
                z["room_layout_area_fallback"] = True
            return fallback
        return zones

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
        # Interior ring (courtyard hole): geomeppy core/perim produces a donut core whose
        # inter-floor surfaces get mismatched vertex counts → E+ Fatal. Skip core/perim.
        if list(footprint_poly.interiors):
            logger.warning(
                "osm_id=%s interior ring (courtyard): perimeter_core → one_zone_per_floor",
                osm_id,
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

    if strategy == "layout_assign":
        assigned_layout = layout_assigner.assign_baseline_layout(
            osm_id, footprint_poly, archetype_id, num_floors, floor_to_floor_m
        )
        return [assigned_layout]

    return build_zones(osm_id, footprint_poly, archetype_id, num_floors, "single_zone", floor_to_floor_m, perimeter_depth_m)
