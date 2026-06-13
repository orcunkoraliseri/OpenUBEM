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
        fallback_zones = []
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
                z = {
                    "name": zone_name,
                    "floor_polygon": placeholder["floor_polygon"],
                    "coords_m": coords,
                    "height_m": floor_h,
                    "archetype_id": archetype_id,
                    "extruded": True,
                    "narrow_fallback": True,
                    "generation_status_note": "narrow_core_perim_fallback",
                }
                fallback_zones.append(z)
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
        if z.get("mode") == "core/perim":
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

    idf.intersect_match()
    # Repair illegal Roof↔Roof interzone pairs (perim wedge coplanar roof fragments).
    _repair_roof_roof_pairs(idf)
    # Repair same-type horizontal pairs with mismatched vertex counts (E+ Fatal).
    _repair_mismatched_horizontal_pairs(idf)
    # Pair inter-floor ceiling↔floor surfaces missed by geomeppy's almostequal (cyclic verts).
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
