"""Deterministic TABULA box-plan arithmetic for the S0 fixtures (D-EU-01).

TABULA provides aggregate areas rather than a footprint.  The implementation
therefore derives the one rectangular footprint that conserves both the ruled
plate area and exposed-wall perimeter.  Some archetypes have no real-valued
rectangle under those two constraints; callers must reject those explicitly
rather than silently changing a source area.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from openubem.idf.european_physics import add_b_factor_other_side_coefficients, add_nomass_construction


S0_ARCHETYPE_IDS = (
    "ES.ME.SFH.04.Gen.ReEx.001.001",
    "FR.N.TH.09.Gen.ReEx.001.001",
    "ES.ME.MFH.03.Gen.ReEx.001.001",
    "ES.ME.AB.01.Gen.ReEx.001.001",
)


@dataclass(frozen=True)
class TabulaBoxPlan:
    """A rectangular plate derived solely from declared TABULA quantities."""

    archetype_id: str
    plate_area_m2: float
    height_m: float
    length_m: float
    width_m: float
    storeys: float
    exposed_wall_area_m2: float

    @property
    def perimeter_m(self) -> float:
        return 2.0 * (self.length_m + self.width_m)

    @property
    def conditioned_volume_m3(self) -> float:
        return self.plate_area_m2 * self.storeys * self.height_m


@dataclass(frozen=True)
class EquivalentEnvelope:
    """Traceable, aggregate-area envelope emitted for an S0 zone.

    TABULA's separately declared floor, roof, wall and glazing areas cannot
    generally be made into a single closed prism without changing a source
    quantity.  The S0 adapter consequently creates independently sized,
    non-overlapping heat-transfer faces belonging to one zone whose declared
    volume is ``V_C``.  This is an *equivalent envelope*, not a claim of a
    surveyed 3-D building shape.  Its purpose is exact coefficient readback
    before the later geometry/layout adapter supplies a real building form.
    """

    archetype_id: str
    zone_name: str
    surface_names: tuple[str, ...]
    window_names: tuple[str, ...]
    source_h_transmission_w_m2k: float
    reduced_h_transmission_w_m2k: float
    source_area_m2: float


def _set_vertices(surface: Any, vertices: list[tuple[float, float, float]]) -> None:
    surface.Number_of_Vertices = len(vertices)
    for number, (x, y, z) in enumerate(vertices, start=1):
        setattr(surface, f"Vertex_{number}_Xcoordinate", x)
        setattr(surface, f"Vertex_{number}_Ycoordinate", y)
        setattr(surface, f"Vertex_{number}_Zcoordinate", z)


def _horizontal_rectangle(area_m2: float, x0: float, z: float) -> list[tuple[float, float, float]]:
    side = math.sqrt(area_m2)
    return [(x0, 0.0, z), (x0 + side, 0.0, z), (x0 + side, side, z), (x0, side, z)]


def _vertical_rectangle(
    area_m2: float, orientation: str, offset: float
) -> list[tuple[float, float, float]]:
    """Make an exact-area cardinal vertical rectangle on a separate plane."""
    side = math.sqrt(area_m2)
    if orientation == "east":
        return [(offset, 0.0, 0.0), (offset, side, 0.0), (offset, side, side), (offset, 0.0, side)]
    if orientation == "west":
        return [(offset, side, 0.0), (offset, 0.0, 0.0), (offset, 0.0, side), (offset, side, side)]
    if orientation == "north":
        return [(0.0, offset, 0.0), (side, offset, 0.0), (side, offset, side), (0.0, offset, side)]
    return [(side, offset, 0.0), (0.0, offset, 0.0), (0.0, offset, side), (side, offset, side)]


def _add_surface(
    idf: Any,
    *,
    name: str,
    surface_type: str,
    construction: str,
    zone_name: str,
    vertices: list[tuple[float, float, float]],
    boundary_object: str,
    outside_boundary_condition: str = "OtherSideCoefficients",
) -> Any:
    fields: dict[str, object] = {
        "Name": name,
        "Surface_Type": surface_type,
        "Construction_Name": construction,
        "Zone_Name": zone_name,
        "Outside_Boundary_Condition": outside_boundary_condition,
        "Sun_Exposure": "NoSun",
        "Wind_Exposure": "NoWind",
        "View_Factor_to_Ground": 0.5,
    }
    if outside_boundary_condition == "OtherSideCoefficients":
        fields["Outside_Boundary_Condition_Object"] = boundary_object
    surface = idf.newidfobject(
        "BUILDINGSURFACE:DETAILED",
        **fields,
    )
    _set_vertices(surface, vertices)
    return surface


def _add_glazing_construction(idf: Any, name: str, u_value_w_m2k: float, shgc: float) -> str:
    material = f"{name}_SimpleGlazing"
    construction = f"{name}_Construction"
    idf.newidfobject(
        "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM",
        Name=material,
        UFactor=u_value_w_m2k,
        Solar_Heat_Gain_Coefficient=shgc,
        Visible_Transmittance=min(1.0, max(0.0, shgc)),
    )
    idf.newidfobject("CONSTRUCTION", Name=construction, Outside_Layer=material)
    return construction


def _component_values(record: Mapping[str, object], category: str) -> list[tuple[int, float, float, float]]:
    """Return (index, area, U, coefficient-calibrated b) for opaque terms.

    The calculator exposes both a display ``b_Transmission_*`` field and an
    authoritative component ``H_Transmission_*`` result.  They normally
    agree as ``H = U*b*A``.  A small number of rows (including the AB S0
    fixture's floor) do not.  The saved-IDF acceptance target is the latter,
    so derive the effective b from that audited H term whenever necessary.
    The original display b remains intact in the registry for provenance.
    """
    geometry = record["geometry"]
    u_values = record["u_components_w_m2k"]
    factors = record["transmission_b_factors"]
    h_components = record["h_transmission_components_w_k"]
    assert (
        isinstance(geometry, Mapping)
        and isinstance(u_values, Mapping)
        and isinstance(factors, Mapping)
        and isinstance(h_components, Mapping)
    )
    areas = geometry[f"a_{category}_components_m2"]
    u_list = u_values[category]
    result = []
    for index, area in enumerate(areas, start=1):
        area_value = float(area)
        if area_value > 0:
            u_value = float(u_list[index - 1])
            source_b = float(factors[f"{category}_{index}"])
            source_h = float(h_components[f"{category}_{index}"])
            effective_b = source_h / (u_value * area_value) if u_value > 0 else source_b
            if not 0.0 <= effective_b <= 1.0 + 1e-9:
                raise ValueError(f"TABULA {category}_{index} H term cannot be represented by U*b*A")
            result.append((index, area_value, u_value, min(1.0, effective_b)))
    return result


def add_s0_equivalent_envelope(idf: Any, record: Mapping[str, object], zone_name: str) -> EquivalentEnvelope:
    """Emit an area-faithful TABULA S0 envelope into ``idf``.

    The function accepts the selected S0 archetypes and is deliberately strict
    about unsupported source combinations (doors or a second glazing class),
    rather than silently assigning them an invented orientation.  All emitted
    envelope U-values and ACH are later multiplied by ``F_red_temp`` under
    D-EU-07; the returned source coefficient is the un-reduced TABULA target.
    """
    archetype = str(record["archetype_id"])
    geometry = record["geometry"]
    assert isinstance(geometry, Mapping)
    window_areas = geometry["a_window_components_m2"]
    if any(float(value) > 0 for value in window_areas[1:]):
        raise ValueError("S0 equivalent envelope requires a single TABULA glazing class")
    f_red = float(record["f_red_temp"])
    if not 0.0 < f_red <= 1.0:
        raise ValueError("f_red_temp must be in (0, 1]")

    # The explicit Zone fields make the reference volume and floor area
    # inspectable even though the heat-transfer faces are an equivalent mesh.
    zone = idf.getobject("ZONE", zone_name)
    if zone is None:
        zone = idf.newidfobject("ZONE", Name=zone_name)
    reference_area = float(geometry["a_c_ref_m2"])
    reference_volume = float(geometry["v_c_m3"])
    reference_storeys = float(geometry["n_storey"])
    if min(reference_area, reference_volume, reference_storeys) <= 0:
        raise ValueError("TABULA S0 reference area, volume, and storey count must be positive")
    # The equivalent envelope has one thermal zone, so the IDF must retain a
    # readback identity for the source's storey count.  This derived height is
    # that zone's equivalent per-storey height: V / (A / n).  Together with
    # the explicit Area and Volume fields it lets V8.d derive all three
    # quantities from the saved IDF, without consulting this builder's plan.
    zone.Ceiling_Height = reference_volume / (reference_area * reference_storeys)
    zone.Volume = reference_volume
    zone.Floor_Area = reference_area

    names: list[str] = []
    windows: list[str] = []
    source_area = 0.0
    offset = 0.0
    for category, surface_type, z in (("floor", "Floor", 0.0), ("roof", "Roof", 20.0)):
        for index, area, u_value, b_factor in _component_values(record, category):
            base = f"EU_{archetype}_{category}_{index}"
            construction = add_nomass_construction(idf, base, max(u_value * f_red, 1e-6))
            boundary = add_b_factor_other_side_coefficients(idf, f"{base}_b{b_factor:g}", b_factor)
            name = f"{base}_Surface"
            _add_surface(
                idf, name=name, surface_type=surface_type, construction=construction,
                zone_name=zone_name, vertices=_horizontal_rectangle(area, offset, z), boundary_object=boundary,
            )
            names.append(name)
            source_area += area
            offset += math.sqrt(area) + 5.0

    wall_components = _component_values(record, "wall")
    by_orientation = geometry["a_window_by_orientation_m2"]
    assert isinstance(by_orientation, Mapping)
    oriented_windows = [(str(direction), float(area)) for direction, area in by_orientation.items() if float(area) > 0]
    window_total = sum(area for _, area in oriented_windows)
    source_window_area = float(window_areas[0])
    # Directional areas in the cached workbook are rounded independently
    # (the selected ES SFH sums to 12.64 m2 while A_Window_1 is 12.60 m2).
    # Preserve the authoritative component total while retaining the declared
    # cardinal proportions; a larger mismatch is source-data invalid.
    if window_total and not math.isclose(window_total, source_window_area, rel_tol=0.01, abs_tol=1e-9):
        raise ValueError("TABULA directional window areas disagree materially with A_Window_1")
    if window_total:
        scale = source_window_area / window_total
        oriented_windows = [(direction, area * scale) for direction, area in oriented_windows]
        window_total = source_window_area
    door_area = float(geometry["a_door_m2"])
    door_h = float(record["h_transmission_components_w_k"]["door_1"])
    if (door_area == 0.0) != (door_h == 0.0):
        raise ValueError("TABULA door area and H_Transmission_Door_1 must either both be zero or both be positive")
    openings = [(orientation, area, "window") for orientation, area in oriented_windows]
    if door_area > 0:
        openings.append(("south", door_area, "door"))
    opening_total = sum(area for _, area, _ in openings)
    wall_one = next((item for item in wall_components if item[0] == 1), None)
    if opening_total > 0 and wall_one is None:
        raise ValueError("TABULA openings require an opaque Wall_1 host in S0")

    # Partition Wall_1's *opaque* area over cardinal host faces.  A window
    # sits in its host wall, so the gross host area is opaque + glazing while
    # the net opaque area remains exactly the workbook's A_Wall_1.
    if wall_one is not None:
        _, wall_area, wall_u, wall_b = wall_one
        if opening_total and not math.isclose(wall_b, 1.0, abs_tol=1e-9):
            raise ValueError("S0 openings require an exterior (b=1) Wall_1 host")
        allocated = 0.0
        for ordinal, (orientation, opening_area, opening_type) in enumerate(openings, start=1):
            opaque_area = wall_area * opening_area / opening_total
            allocated += opaque_area
            base = f"EU_{archetype}_wall_1_{orientation}_{ordinal}"
            construction = add_nomass_construction(idf, base, max(wall_u * f_red, 1e-6))
            boundary = add_b_factor_other_side_coefficients(idf, f"{base}_b{wall_b:g}", wall_b)
            host_name = f"{base}_Surface"
            host_vertices = _vertical_rectangle(opaque_area + opening_area, orientation, offset)
            _add_surface(
                idf, name=host_name, surface_type="Wall", construction=construction,
                zone_name=zone_name, vertices=host_vertices, boundary_object=boundary,
                # EnergyPlus forbids a fenestration whose parent uses
                # OtherSideCoefficients.  S0 fixtures expose only b=1 wall
                # hosts, so ``Outdoors`` preserves the same U*A loss and
                # yields a runnable window surface.
                outside_boundary_condition="Outdoors",
            )
            names.append(host_name)
            source_area += opaque_area
            opening_name = f"EU_{archetype}_{opening_type}_{orientation}_{ordinal}"
            if opening_type == "window":
                opening_construction = _add_glazing_construction(
                    idf, opening_name, max(float(record["u_components_w_m2k"]["window"][0]) * f_red, 1e-6),
                    float(record["g_gl_window"]),
                )
            else:
                opening_construction = add_nomass_construction(idf, opening_name, door_h / door_area * f_red)
            # A centred, similar rectangle is guaranteed to lie inside its
            # square host.  Its orientation follows the declared cardinal key.
            side = math.sqrt(opening_area)
            host_side = math.sqrt(opaque_area + opening_area)
            inset = (host_side - side) / 2.0
            if orientation == "east":
                x = offset
                y0 = inset
                vertices = [(x, y0, inset), (x, y0 + side, inset), (x, y0 + side, inset + side), (x, y0, inset + side)]
            elif orientation == "west":
                x = offset
                y0 = inset
                vertices = [(x, y0 + side, inset), (x, y0, inset), (x, y0, inset + side), (x, y0 + side, inset + side)]
            elif orientation == "north":
                y = offset
                x0 = inset
                vertices = [(x0, y, inset), (x0 + side, y, inset), (x0 + side, y, inset + side), (x0, y, inset + side)]
            else:  # south
                y = offset
                x0 = inset
                vertices = [(x0 + side, y, inset), (x0, y, inset), (x0, y, inset + side), (x0 + side, y, inset + side)]
            fen = idf.newidfobject(
                "FENESTRATIONSURFACE:DETAILED", Name=opening_name,
                Surface_Type="Window" if opening_type == "window" else "Door",
                Construction_Name=opening_construction, Building_Surface_Name=host_name, View_Factor_to_Ground=0.5,
            )
            _set_vertices(fen, vertices)
            if opening_type == "window":
                windows.append(opening_name)
            # The bridge term applies to the source envelope's gross area:
            # opaque wall plus its window/door opening.  Keep this separate
            # from the net-opaque host accounting above.
            source_area += opening_area
            offset += host_side + 5.0
        remaining = wall_area - allocated
        if remaining > 1e-12:
            base = f"EU_{archetype}_wall_1_remainder"
            construction = add_nomass_construction(idf, base, max(wall_u * f_red, 1e-6))
            boundary = add_b_factor_other_side_coefficients(idf, f"{base}_b{wall_b:g}", wall_b)
            name = f"{base}_Surface"
            _add_surface(idf, name=name, surface_type="Wall", construction=construction, zone_name=zone_name,
                         vertices=_vertical_rectangle(remaining, "south", offset), boundary_object=boundary)
            names.append(name)
            source_area += remaining
            offset += math.sqrt(remaining) + 5.0
    for index, area, u_value, b_factor in wall_components:
        if index == 1:
            continue
        base = f"EU_{archetype}_wall_{index}"
        construction = add_nomass_construction(idf, base, max(u_value * f_red, 1e-6))
        boundary = add_b_factor_other_side_coefficients(idf, f"{base}_b{b_factor:g}", b_factor)
        name = f"{base}_Surface"
        _add_surface(idf, name=name, surface_type="Wall", construction=construction, zone_name=zone_name,
                     vertices=_vertical_rectangle(area, "south", offset), boundary_object=boundary)
        names.append(name)
        source_area += area
        offset += math.sqrt(area) + 5.0

    # TABULA stores thermal bridges as a separate H term.  A dedicated
    # equivalent face preserves that term exactly rather than incorrectly
    # multiplying it by component-specific b factors.
    delta_u = float(record["delta_u_tb_w_m2k"])
    if delta_u > 0 and source_area > 0:
        base = f"EU_{archetype}_thermal_bridge"
        construction = add_nomass_construction(idf, base, delta_u * f_red)
        boundary = add_b_factor_other_side_coefficients(idf, f"{base}_b1", 1.0)
        name = f"{base}_Surface"
        _add_surface(idf, name=name, surface_type="Wall", construction=construction, zone_name=zone_name,
                     vertices=_vertical_rectangle(source_area, "south", offset), boundary_object=boundary)
        names.append(name)

    return EquivalentEnvelope(
        archetype_id=archetype,
        zone_name=zone_name,
        surface_names=tuple(names),
        window_names=tuple(windows),
        source_h_transmission_w_m2k=source_h_transmission_w_m2k(record),
        reduced_h_transmission_w_m2k=source_h_transmission_w_m2k(record) * f_red,
        source_area_m2=source_area,
    )


def source_h_transmission_w_m2k(record: Mapping[str, object]) -> float:
    """Return the workbook's component-sum transmission coefficient.

    These terms are preserved independently because they include TABULA's
    component-specific boundary factors; re-computing them from a weighted U
    value loses that information.
    """
    geometry = record["geometry"]
    assert isinstance(geometry, Mapping)
    components = record["h_transmission_components_w_k"]
    assert isinstance(components, Mapping)
    area = float(geometry["a_c_ref_m2"])
    if area <= 0:
        raise ValueError("A_C_Ref must be positive")
    return sum(float(value) for value in components.values()) / area


def source_h_ventilation_w_m2k(record: Mapping[str, object]) -> float:
    """Return the governing DR11 h-room form of the TABULA ventilation term."""
    geometry = record["geometry"]
    assert isinstance(geometry, Mapping)
    return 0.34 * (
        float(record["n_air_use_h_1"]) + float(record["n_air_infiltration_h_1"])
    ) * float(geometry["h_room_m"])


def rectangular_tabula_box(record: Mapping[str, object]) -> TabulaBoxPlan:
    """Make the ruled D-EU-01 box or explicitly reject incompatible inputs."""
    geometry = record["geometry"]
    assert isinstance(geometry, Mapping)
    area = float(geometry["a_c_ref_m2"])
    storeys = float(geometry["n_storey"])
    height = float(geometry["v_c_m3"]) / area
    envelope_storeys = float(geometry["n_storey_effective_envelope"])
    walls = sum(float(value) for value in geometry["a_wall_components_m2"])
    if min(area, storeys, height, envelope_storeys, walls) <= 0:
        raise ValueError("TABULA box inputs must be positive")
    plate_area = area / storeys
    perimeter = walls / (envelope_storeys * height)
    discriminant = perimeter**2 - 16.0 * plate_area
    if discriminant < -1e-9:
        raise ValueError(
            "BOX_GEOMETRY_INFEASIBLE: TABULA plate area and wall perimeter cannot form a rectangle"
        )
    root = discriminant**0.5
    length = (perimeter + root) / 4.0
    width = (perimeter - root) / 4.0
    return TabulaBoxPlan(
        archetype_id=str(record["archetype_id"]),
        plate_area_m2=plate_area,
        height_m=height,
        length_m=length,
        width_m=width,
        storeys=storeys,
        exposed_wall_area_m2=walls,
    )
