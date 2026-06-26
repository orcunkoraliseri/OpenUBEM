"""Geometry extrusion and adiabatic surface assignment (DESIGN §3E + §10c).

Deviation (R2): each unique footprint is extruded as ONE add_block call with
num_stories=N so geomeppy stacks storeys at true z (inter-floor floor/ceiling pairing
works after intersect_match).  The previous per-floor add_block + Z_Origin patch is
removed.

Deviation: geomeppy.add_shading_block creates SHADING:SITE:DETAILED objects (not
SHADING:BUILDING:DETAILED as the DESIGN implies). The object geometry is equivalent;
the key name differs because eppy's bundled IDD v8.0.0 maps the shading block to
SHADING:SITE:DETAILED. With a real EnergyPlus 23.1 IDD the object type may differ.
"""
import logging
import math
from itertools import groupby

from geomeppy import IDF as GeomIDF

logger = logging.getLogger("openubem.idf")

try:
    from geomeppy.utilities import NotARectangleError
except ImportError:
    NotARectangleError = None  # geomeppy >= 0.12 may not expose this symbol


def _get_floor_idx(zone_name: str) -> int | None:
    try:
        after_f = zone_name.split("_F", 1)[1]
        return int(after_f.split("_")[0])
    except (IndexError, ValueError):
        return None


def _get_zone_label(zone_name: str) -> str:
    return zone_name.rsplit("_", 1)[-1]


def _building_prefix(zone_name: str) -> str:
    """Return everything before the first _F<digit> segment."""
    idx = zone_name.find("_F")
    return zone_name[:idx] if idx != -1 else zone_name


def _rename_geomeppy_zone(idf: GeomIDF, geomeppy_name: str, target_name: str) -> None:
    """Restore the plan-specified zone name after geomeppy wraps it."""
    for zone in idf.idfobjects["ZONE"]:
        if zone.Name == geomeppy_name:
            zone.Name = target_name
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if surf.Zone_Name == geomeppy_name:
            surf.Zone_Name = target_name


def _group_key(z: dict) -> tuple:
    """Group zones that share the same footprint into one add_block call (R2)."""
    return (_building_prefix(z["name"]), _get_zone_label(z["name"]))


def _pair_interfloor_surfaces(idf: GeomIDF) -> None:
    """Pair ceiling/floor surface couples that geomeppy's intersect_match misses.

    geomeppy's almostequal does positional vertex comparison; inter-floor ceilings and
    floors from add_block(num_stories>1) are cyclic permutations of each other (same
    vertex set, different start) so the match loop never fires.  We resolve them here
    by matching on frozenset of vertex tuples — safe because only flat coplanar
    ceiling↔floor surfaces share the exact same vertex set.
    """
    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]

    def _vset(s) -> frozenset:
        return frozenset(tuple(round(v, 6) for v in pt) for pt in s.coords)

    ceilings = [s for s in bsds if s.Surface_Type.lower() == "ceiling"
                and s.Outside_Boundary_Condition.lower() not in ("surface",)]
    floors = [s for s in bsds if s.Surface_Type.lower() == "floor"
              and s.Outside_Boundary_Condition.lower() not in ("surface", "ground")]

    floor_by_vset: dict[frozenset, object] = {_vset(f): f for f in floors}

    for ceiling in ceilings:
        vset = _vset(ceiling)
        partner = floor_by_vset.get(vset)
        if partner is None:
            continue
        ceiling.Outside_Boundary_Condition = "Surface"
        ceiling.Outside_Boundary_Condition_Object = partner.Name
        ceiling.Sun_Exposure = "NoSun"
        ceiling.Wind_Exposure = "NoWind"
        partner.Outside_Boundary_Condition = "Surface"
        partner.Outside_Boundary_Condition_Object = ceiling.Name
        partner.Sun_Exposure = "NoSun"
        partner.Wind_Exposure = "NoWind"


_COREPERIM_ZONE_PREFIXES = ("Block Core_Zone Storey", "Block Perimeter_Zone_")
_COINCIDENT_VERTEX_TOL = 0.01  # m — match EnergyPlus 1 cm coincident-vertex tolerance

# Pre-intersect_match complexity gate: core/perim intersect_match is O(surface_pairs²)
# and never returns on very complex footprints. M = simplified_vertex_count × n_floors.
# T=800 sits in the empirical gap: max M over all currently-succeeding perimeter_core
# buildings is 465 (fleet-wide, 12 cells), the one hang is M=1455. Above T, skip core/perim
# and route directly to one_zone_per_floor (intersect_match then runs on a far simpler
# whole-floor footprint). Only the perimeter_core path is gated; one_zone_per_floor never hangs.
COREPERIM_COMPLEXITY_THRESHOLD = 800


def _coreperim_placeholder_to_one_zone_per_floor(placeholder: dict) -> list[dict]:
    """Convert a core/perim placeholder into one_zone_per_floor zone dicts (complexity gate)."""
    osm_id = placeholder["name"].replace("_perimgroup", "")
    coords = placeholder["coords_m"]
    n = placeholder["num_floors"]
    floor_h = placeholder["height_m"]
    floor_polygon = placeholder["floor_polygon"]
    archetype_id = placeholder.get("archetype_id", "")
    return [
        {
            "name": f"{osm_id}_F{i}_whole",
            "floor_polygon": floor_polygon,
            "coords_m": coords,
            "z_floor": i * floor_h,
            "z_ceiling": (i + 1) * floor_h,
            "height_m": floor_h,
            "archetype_id": archetype_id,
            "generation_status_note": "coreperim_complexity_gate",
        }
        for i in range(n)
    ]


def _surface_3d_area(coords: list) -> float:
    """Compute 3D polygon area via cross-product accumulation."""
    n = len(coords)
    if n < 3:
        return 0.0
    ax = ay = az = 0.0
    for i in range(n):
        j = (i + 1) % n
        ax += coords[i][1] * coords[j][2] - coords[i][2] * coords[j][1]
        ay += coords[i][2] * coords[j][0] - coords[i][0] * coords[j][2]
        az += coords[i][0] * coords[j][1] - coords[i][1] * coords[j][0]
    return 0.5 * math.sqrt(ax * ax + ay * ay + az * az)


def _distinct_vertices_after_collapse(coords: list, tol: float = _COINCIDENT_VERTEX_TOL) -> int:
    """Count vertices that remain after removing each vertex coincident with its successor.

    Checks wrap-around (last vertex vs first).  Mirrors EnergyPlus GetSurfaceData rule:
    a surface is degenerate when fewer than 3 distinct vertices survive this pass.
    """
    n = len(coords)
    count = 0
    for i in range(n):
        pt = coords[i]
        nxt = coords[(i + 1) % n]
        dx = pt[0] - nxt[0]
        dy = pt[1] - nxt[1]
        dz = pt[2] - nxt[2]
        if math.sqrt(dx * dx + dy * dy + dz * dz) > tol:
            count += 1
    return count


def _is_coreperim_zone(zone_name: str) -> bool:
    """Return True if zone_name belongs to a core/perim block (pre- or post-rename)."""
    return (
        any(zone_name.startswith(p) for p in _COREPERIM_ZONE_PREFIXES)
        or zone_name.endswith("_core")
        or ("_perim" in zone_name and zone_name.rsplit("_perim", 1)[-1].isdigit())
    )


def _coreperim_has_degenerate_surfaces(idf: GeomIDF) -> bool:
    """Return True if any core/perim surface has fewer than 3 distinct vertices.

    Uses EnergyPlus's own criterion: collapse vertices coincident within 1 cm
    (including the wrap-around between last and first vertex); if fewer than 3
    distinct vertices remain the surface is degenerate.
    Works both pre-rename (geomeppy names) and post-rename (osm_id names).
    """
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if not _is_coreperim_zone(surf.Zone_Name):
            continue
        coords = list(surf.coords)
        if len(coords) < 3:
            return True
        if _distinct_vertices_after_collapse(coords) < 3:
            return True
    return False


_TINY_ZONE_AREA_M2 = 0.5  # floor areas below this indicate a degenerate sliver zone


def _signed_area_2d(coords: list) -> float:
    """Shoelace formula on the XY plane. Positive = CCW, negative = CW."""
    n = len(coords)
    if n < 3:
        return 0.0
    total = 0.0
    for i in range(n):
        j = (i + 1) % n
        total += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    return total / 2.0


def _coreperim_has_tiny_zone_area(idf: GeomIDF, min_area: float = _TINY_ZONE_AREA_M2) -> bool:
    """Return True if any core/perim floor surface has a polygon area < min_area m²."""
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if not _is_coreperim_zone(surf.Zone_Name):
            continue
        if surf.Surface_Type.upper() not in ("FLOOR", "ROOFCEILING"):
            continue
        coords = list(surf.coords)
        if len(coords) < 3:
            continue
        area = abs(_signed_area_2d(coords))
        if area < min_area:
            return True
    return False


def _coreperim_has_inverted_winding(idf: GeomIDF) -> bool:
    """Return True if any core/perim floor surface has negative signed area (inverted winding)."""
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if not _is_coreperim_zone(surf.Zone_Name):
            continue
        if surf.Surface_Type.upper() not in ("FLOOR", "ROOFCEILING"):
            continue
        coords = list(surf.coords)
        if len(coords) < 3:
            continue
        if _signed_area_2d(coords) < 0.0:
            return True
    return False


def _purge_idf_geometry(idf: GeomIDF) -> None:
    """Remove ALL ZONE and BUILDINGSURFACE:DETAILED objects from the IDF.

    Called before rebuilding a degenerate core/perim building with per-floor fallback.
    Safe because each BuildingIDF uses a per-building IDF; no other buildings' geometry
    exists at this point.
    """
    for obj_type in ("BUILDINGSURFACE:DETAILED", "ZONE"):
        for obj in list(idf.idfobjects[obj_type]):
            idf.removeidfobject(obj)


def _expand_core_perim_placeholder(
    idf: GeomIDF, placeholder: dict, zones: list[dict], exc_types: tuple
) -> None:
    """Handle one core/perim placeholder: call add_block with zoning='core/perim',
    rename the resulting geomeppy zones, and expand `zones` in place.

    R7: N perimeter wedges + 1 core per storey, renamed to
    {osm_id}_F{i}_perim{n} / {osm_id}_F{i}_core.  On ValueError fall back to
    one_zone_per_floor for this building and record generation_status note.
    """
    osm_id = placeholder["name"].replace("_perimgroup", "")
    coords = placeholder["coords_m"]
    n = placeholder["num_floors"]
    floor_h = placeholder["height_m"]
    perim_depth = placeholder["perim_depth_m"]
    total_height = n * floor_h
    archetype_id = placeholder.get("archetype_id", "")

    # Remove the placeholder from zones; we will insert expanded zone dicts instead.
    idx = zones.index(placeholder)
    zones.pop(idx)

    try:
        idf.add_block(
            name=osm_id,
            coordinates=coords,
            height=total_height,
            num_stories=n,
            zoning="core/perim",
            perim_depth=perim_depth,
        )
    except Exception as e:
        # Tier-1 fallback: true footprint per-floor zoning (DESIGN line 119).
        logger.warning(
            "perimeter_core fallback to one_zone_per_floor: osm_id=%s, %s", osm_id, e,
        )
        block_name = f"{osm_id}_whole"
        fallback_zones: list[dict] = []
        try:
            idf.add_block(
                name=block_name,
                coordinates=coords,
                height=total_height,
                num_stories=n,
            )
            for i in range(n):
                geomeppy_name = f"Block {block_name} Storey {i}"
                zone_name = f"{osm_id}_F{i}_whole"
                _rename_geomeppy_zone(idf, geomeppy_name, zone_name)
                fallback_zones.append({
                    "name": zone_name,
                    "floor_polygon": placeholder["floor_polygon"],
                    "coords_m": coords,
                    "height_m": floor_h,
                    "archetype_id": archetype_id,
                    "extruded": True,
                    "narrow_fallback": True,
                    "generation_status_note": "narrow_core_perim_fallback",
                })
        except Exception as e2:
            # Tier-2 fallback: bbox (DESIGN lines 236–245 generic add_block exception).
            logger.warning(
                "block %s narrow fallback also failed (%s) — falling back to bbox", osm_id, e2,
            )
            bbox_coords = list(
                placeholder["floor_polygon"].minimum_rotated_rectangle.exterior.coords
            )[:-1]
            try:
                idf.add_block(
                    name=block_name,
                    coordinates=bbox_coords,
                    height=total_height,
                    num_stories=n,
                )
                for i in range(n):
                    geomeppy_name = f"Block {block_name} Storey {i}"
                    zone_name = f"{osm_id}_F{i}_whole"
                    _rename_geomeppy_zone(idf, geomeppy_name, zone_name)
                    fallback_zones.append({
                        "name": zone_name,
                        "floor_polygon": placeholder["floor_polygon"],
                        "coords_m": bbox_coords,
                        "height_m": floor_h,
                        "archetype_id": archetype_id,
                        "extruded": True,
                        "fallback_to_bbox": True,
                        "generation_status_note": "core_perim_fallback_to_per_floor",
                    })
            except Exception:
                logger.warning("block %s bbox extrusion also failed — skipping", osm_id)
        for z in reversed(fallback_zones):
            zones.insert(idx, z)
        return

    # Successful core/perim extrusion: discover and rename the produced zones.
    # geomeppy names them "Block Perimeter_Zone_N Storey M" and "Block Core_Zone Storey M".
    # Rename immediately (before next add_block) to avoid collisions across buildings.
    new_zone_dicts = []
    for i in range(n):
        # Rename core zone for storey i.
        geomeppy_core_name = f"Block Core_Zone Storey {i}"
        target_core_name = f"{osm_id}_F{i}_core"
        _rename_geomeppy_zone(idf, geomeppy_core_name, target_core_name)
        new_zone_dicts.append({
            "name": target_core_name,
            "floor_polygon": placeholder["floor_polygon"],
            "coords_m": coords,
            "height_m": floor_h,
            "archetype_id": archetype_id,
            "extruded": True,
        })

    # Rename perimeter zones; discover count from ZONE objects named "Block Perimeter_Zone_".
    perim_count = sum(
        1 for z in idf.idfobjects["ZONE"]
        if z.Name.startswith("Block Perimeter_Zone_") and f"Storey 0" in z.Name
    )
    for pn in range(1, perim_count + 1):
        for i in range(n):
            geomeppy_perim_name = f"Block Perimeter_Zone_{pn} Storey {i}"
            target_perim_name = f"{osm_id}_F{i}_perim{pn}"
            _rename_geomeppy_zone(idf, geomeppy_perim_name, target_perim_name)
            new_zone_dicts.append({
                "name": target_perim_name,
                "floor_polygon": placeholder["floor_polygon"],
                "coords_m": coords,
                "height_m": floor_h,
                "archetype_id": archetype_id,
                "extruded": True,
            })

    for z in reversed(new_zone_dicts):
        zones.insert(idx, z)


def _repair_roof_roof_pairs(idf: GeomIDF) -> None:
    """Reset illegal Roof↔Roof interzone pairs produced by intersect_match.

    geomeppy intersect_match can pair coplanar top-storey roof fragments of adjacent
    perimeter wedges as interzone boundaries with mismatched vertex counts → E+ Fatal.
    Two roofs in different zones can never share an interzone boundary; reset both to
    exterior. Legitimate interfloor pairs (Ceiling↔Floor) are untouched.
    """
    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    surf_by_name: dict[str, object] = {s.Name.upper(): s for s in bsds}

    roof_types = {"ROOF", "ROOFCEILING"}
    repaired = 0
    for surf in bsds:
        if surf.Surface_Type.upper() not in roof_types:
            continue
        partner_name = (surf.Outside_Boundary_Condition_Object or "").upper()
        if not partner_name:
            continue
        partner = surf_by_name.get(partner_name)
        if partner is None:
            continue
        if partner.Surface_Type.upper() not in roof_types:
            continue
        if surf.Zone_Name.upper() == partner.Zone_Name.upper():
            continue
        # Both surfaces are Roof/RoofCeiling in different zones — illegal pair.
        for s in (surf, partner):
            s.Outside_Boundary_Condition = "Outdoors"
            s.Outside_Boundary_Condition_Object = ""
            s.Sun_Exposure = "SunExposed"
            s.Wind_Exposure = "WindExposed"
        logger.warning(
            "repaired illegal Roof↔Roof interzone pair: %s ↔ %s", surf.Name, partner.Name,
        )
        repaired += 1

    if repaired:
        logger.info("_repair_roof_roof_pairs: reset %d pair(s) to exterior", repaired)


def _repair_mismatched_horizontal_pairs(idf: GeomIDF) -> None:
    """Reset same-type horizontal interzone pairs with mismatched vertex counts.

    geomeppy intersect_match can pair coplanar floor (or ceiling) fragments of
    overlapping perimeter wedges as interzone boundaries with different vertex
    counts → E+ Fatal (GetSurfaceData "Vertex size mismatch"). Two floors (or two
    ceilings) in different zones can never legitimately share an interzone
    boundary, so the reset is safe. Pairs with matching vertex counts are left
    untouched — EnergyPlus accepts them, and touching them would break
    byte-identity of previously valid IDFs.
    """
    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    surf_by_name: dict[str, object] = {s.Name.upper(): s for s in bsds}

    horizontal_types = {"FLOOR", "CEILING", "ROOFCEILING"}
    repaired = 0
    for surf in bsds:
        stype = surf.Surface_Type.upper()
        if stype not in horizontal_types:
            continue
        partner_name = (surf.Outside_Boundary_Condition_Object or "").upper()
        if not partner_name:
            continue
        partner = surf_by_name.get(partner_name)
        if partner is None:
            continue
        if partner.Surface_Type.upper() != stype:
            continue
        if surf.Zone_Name.upper() == partner.Zone_Name.upper():
            continue
        if len(surf.coords) == len(partner.coords):
            continue
        for s in (surf, partner):
            if stype == "FLOOR" and max(abs(pt[2]) for pt in s.coords) < 1e-6:
                s.Outside_Boundary_Condition = "ground"
                s.Outside_Boundary_Condition_Object = ""
                s.Sun_Exposure = "NoSun"
                s.Wind_Exposure = "NoWind"
            else:
                s.Outside_Boundary_Condition = "Outdoors"
                s.Outside_Boundary_Condition_Object = ""
                s.Sun_Exposure = "SunExposed"
                s.Wind_Exposure = "WindExposed"
        logger.warning(
            "repaired mismatched %s↔%s interzone pair: %s (%d verts) ↔ %s (%d verts)",
            surf.Surface_Type, partner.Surface_Type,
            surf.Name, len(surf.coords), partner.Name, len(partner.coords),
        )
        repaired += 1

    if repaired:
        logger.info("_repair_mismatched_horizontal_pairs: reset %d pair(s)", repaired)


def find_mismatched_interzone_pairs(idf: GeomIDF) -> list[tuple[str, str]]:
    """Return cross-referenced interzone surface pairs whose vertex counts differ.

    Any pair returned here would be an EnergyPlus GetSurfaceData Fatal
    ("Vertex size mismatch") — callers must mark generation as failed.
    """
    bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    surf_by_name: dict[str, object] = {s.Name.upper(): s for s in bsds}

    mismatched = []
    seen: set[tuple[str, str]] = set()
    for surf in bsds:
        partner_name = (surf.Outside_Boundary_Condition_Object or "").upper()
        if not partner_name:
            continue
        partner = surf_by_name.get(partner_name)
        if partner is None:
            continue
        key = tuple(sorted((surf.Name.upper(), partner_name)))
        if key in seen:
            continue
        seen.add(key)
        if len(surf.coords) != len(partner.coords):
            mismatched.append((surf.Name, partner.Name))
    return mismatched


def _force_reroute_coreperim_to_one_zone_per_floor(
    idf: GeomIDF, zones: list[dict], reason: str
) -> bool:
    """Unconditionally rebuild a core/perim building as one_zone_per_floor.

    Used by both the degenerate-surface check (T04) and the intersect_match
    exception handler (T03).  Returns True if the rebuild succeeded.
    """
    coreperim_zones = [z for z in zones if _is_coreperim_zone(z.get("name", ""))]
    if not coreperim_zones:
        return False

    sample = coreperim_zones[0]
    raw_name = sample["name"]
    osm_id = raw_name.rsplit("_F", 1)[0] if "_F" in raw_name else raw_name
    coords = sample["coords_m"]
    floor_h = sample["height_m"]
    floor_polygon = sample["floor_polygon"]
    archetype_id = sample.get("archetype_id", "")
    floor_indices = {_get_floor_idx(z["name"]) for z in coreperim_zones if _get_floor_idx(z["name"]) is not None}
    n = len(floor_indices) if floor_indices else max(1, len(coreperim_zones))
    total_height = n * floor_h

    logger.warning(
        "rerouting to one_zone_per_floor (%s): osm_id=%s, n_floors=%d", reason, osm_id, n,
    )

    _purge_idf_geometry(idf)

    for z in coreperim_zones:
        if z in zones:
            zones.remove(z)
    insert_idx = 0

    block_name = f"{osm_id}_whole"
    fallback_zones: list[dict] = []
    try:
        idf.add_block(
            name=block_name,
            coordinates=coords,
            height=total_height,
            num_stories=n,
        )
        for i in range(n):
            geomeppy_name = f"Block {block_name} Storey {i}"
            zone_name = f"{osm_id}_F{i}_whole"
            _rename_geomeppy_zone(idf, geomeppy_name, zone_name)
            fallback_zones.append({
                "name": zone_name,
                "floor_polygon": floor_polygon,
                "coords_m": coords,
                "height_m": floor_h,
                "archetype_id": archetype_id,
                "extruded": True,
                "narrow_fallback": True,
                "generation_status_note": "coreperim_degenerate_fallback",
            })
    except Exception as e:
        logger.warning("block %s reroute rebuild failed (%s) — skipping", osm_id, e)
        return False

    for z in reversed(fallback_zones):
        zones.insert(insert_idx, z)
    return True


def _rebuild_degenerate_coreperim(idf: GeomIDF, zones: list[dict]) -> bool:
    """After intersect_match: detect degenerate/tiny core/perim surfaces and reroute.

    Checks: (1) fewer than 3 distinct vertices after collapse, (2) floor zone area < 0.5 m².
    Note: _coreperim_has_inverted_winding is intentionally excluded — EnergyPlus convention
    always uses negative signed-area (CW winding) for floor surfaces; checking sign would
    produce false positives on healthy buildings.

    Returns True if a rebuild was performed (caller must re-run intersect_match + repairs).
    Per-building IDFs contain exactly one building, so _purge_idf_geometry clears only that
    building's geometry — safe to call here.
    """
    needs_reroute = (
        _coreperim_has_degenerate_surfaces(idf)
        or _coreperim_has_tiny_zone_area(idf)
    )
    if not needs_reroute:
        return False

    return _force_reroute_coreperim_to_one_zone_per_floor(
        idf, zones, "degenerate/tiny surface post-intersect"
    )


def extrude_geometry(idf: GeomIDF, zones: list[dict], context: list[dict]) -> None:
    """Extrude zones into IDF, call intersect_match once, then add shading blocks.

    R2: one add_block per unique footprint (building-prefix + zone-label), with
    num_stories=N so geomeppy stacks storeys at correct z heights.
    R7: core/perim placeholders use add_block(zoning='core/perim'); zones expanded in place.

    Ordering invariant (DESIGN §3E lines 247-252): intersect_match after all zones,
    shading blocks after intersect_match.
    """
    _exc = (ValueError, RuntimeError) if NotARectangleError is None else (NotARectangleError, ValueError, RuntimeError)

    # Process core/perim placeholders first (they must be renamed before next add_block).
    for z in list(zones):  # iterate a snapshot; zones mutated in place
        if z.get("mode") != "core/perim":
            continue
        # Complexity gate: skip core/perim (its intersect_match hangs) above the threshold,
        # routing directly to one_zone_per_floor on the same footprint.
        M = len(z["coords_m"]) * z["num_floors"]
        if M > COREPERIM_COMPLEXITY_THRESHOLD:
            logger.warning(
                "osm_id=%s core/perim complexity M=%d > %d — routing to one_zone_per_floor",
                z["name"].replace("_perimgroup", ""), M, COREPERIM_COMPLEXITY_THRESHOLD,
            )
            idx = zones.index(z)
            zones.pop(idx)
            for new_z in reversed(_coreperim_placeholder_to_one_zone_per_floor(z)):
                zones.insert(idx, new_z)
        else:
            _expand_core_perim_placeholder(idf, z, zones, _exc)

    # Filter zones with empty coords; they are never extruded.
    valid_zones = []
    for z in zones:
        if z.get("extruded"):
            continue  # already handled (core/perim expanded zones)
        if not z["coords_m"]:
            logger.warning("zone %s has empty coords_m — skipping extrusion", z["name"])
        else:
            valid_zones.append(z)

    # Sort so groupby works correctly (zones from build_zones are already ordered but
    # make explicit for robustness).
    valid_zones.sort(key=_group_key)

    for key, group_iter in groupby(valid_zones, key=_group_key):
        group = list(group_iter)
        # Sort group by floor index so storey_no → zone name mapping is deterministic.
        group.sort(key=lambda z: (_get_floor_idx(z["name"]) or 0))

        n = len(group)
        # All floors in the group share the same footprint coords and floor_to_floor height.
        coords = group[0]["coords_m"]
        floor_h = group[0]["height_m"]
        total_height = n * floor_h
        # Use a stable block name derived from group key (prefix + label).
        block_name = f"{key[0]}_{key[1]}"

        try:
            idf.add_block(
                name=block_name,
                coordinates=coords,
                height=total_height,
                num_stories=n,
            )
            fallback = False
        except _exc:
            bbox_coords = list(group[0]["floor_polygon"].minimum_rotated_rectangle.exterior.coords)[:-1]
            try:
                idf.add_block(
                    name=block_name,
                    coordinates=bbox_coords,
                    height=total_height,
                    num_stories=n,
                )
                fallback = True
                logger.warning("block %s fell back to bbox extrusion", block_name)
            except Exception:
                logger.warning("block %s extrusion failed even with bbox — skipping %d zone(s)", block_name, n)
                continue

        # Rename geomeppy storey zones back to our per-floor names.
        for storey_no, z in enumerate(group):
            geomeppy_name = f"Block {block_name} Storey {storey_no}"
            _rename_geomeppy_zone(idf, geomeppy_name, z["name"])
            z["extruded"] = True
            if fallback:
                z["fallback_to_bbox"] = True

    # T03: wrap intersect_match to catch geomeppy geometry exceptions (IndexError from
    # break_polygons, etc.) that fire BEFORE the degenerate reroute check.
    try:
        idf.intersect_match()
    except (IndexError, Exception) as _exc_im:
        logger.warning(
            "intersect_match raised %s — rerouting to one_zone_per_floor", type(_exc_im).__name__
        )
        did_reroute = _force_reroute_coreperim_to_one_zone_per_floor(
            idf, zones, f"intersect_match exception: {type(_exc_im).__name__}"
        )
        if did_reroute:
            try:
                idf.intersect_match()
            except Exception as _exc_im2:
                # Second attempt also failed — re-raise so _build_one catches it.
                raise RuntimeError(
                    f"intersect_match failed after one_zone_per_floor reroute: {_exc_im2}"
                ) from _exc_im2
        else:
            raise

    # Repair illegal Roof↔Roof interzone pairs (perim wedge coplanar roof fragments).
    _repair_roof_roof_pairs(idf)
    # Repair same-type horizontal pairs with mismatched vertex counts (E+ Fatal).
    _repair_mismatched_horizontal_pairs(idf)
    # Pair inter-floor ceiling↔floor surfaces missed by geomeppy's almostequal (cyclic verts).
    _pair_interfloor_surfaces(idf)

    # Post-intersect degenerate check: sliver perimeter wedges can produce degenerate,
    # tiny, or inverted surfaces after intersect_match. If found, rebuild with one_zone_per_floor.
    if _rebuild_degenerate_coreperim(idf, zones):
        idf.intersect_match()
        _repair_roof_roof_pairs(idf)
        _repair_mismatched_horizontal_pairs(idf)
        _pair_interfloor_surfaces(idf)

    for ctx in context:
        idf.add_shading_block(
            name=ctx["name"],
            coordinates=ctx["coords"],
            height=ctx["height"],
        )


def set_adiabatic_surfaces(idf: GeomIDF, zones: list[dict], strategy: str) -> None:
    """Apply party-wall Adiabatic flip for inter-building shared walls (DESIGN §3E line 262).

    C3/R3: z=0 ground floors keep geomeppy's 'ground' BC — no Adiabatic flip.
    R7: perim↔core walls stay as intersect_match Surface pairs for inter-zone conduction;
        the Adiabatic flip applies only to party walls between DIFFERENT buildings.
    Currently no inter-building adjacency is modeled in a single BuildingIDF call,
    so this function is a no-op stub retained for future extension.
    """
