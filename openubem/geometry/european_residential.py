"""Ruled dwelling/core allocation for European TABULA archetypes (D-EU-01).

This module deliberately establishes allocation semantics before an observed
footprint adapter supplies polygons.  The core is additional unconditioned
geometry and never reduces TABULA's conditioned ``A_C_Ref`` floor plate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd
from shapely import affinity
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


RESIDENTIAL_TYPES = frozenset({"SFH", "TH", "MFH", "AB"})
CORE_FRACTION_OF_PLATE = 0.06
NARROW_FOOTPRINT_THRESHOLD_M = 8.0
# Relative area used to absorb floating-point topology noise after affine
# operations.  Unlike the former fixed m² tolerance, this scales with the
# footprint and is invariant under CRS translation.
EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION = 1e-9


REAL_FOOTPRINT_REQUIRED_COLUMNS = frozenset({"osm_id", "geometry"})


@dataclass(frozen=True)
class EuropeanFloorAllocation:
    """One storey's declared dwelling count and conditioned/core areas."""

    storey_index: int
    dwelling_count: int
    conditioned_area_m2: float
    unconditioned_core_area_m2: float


@dataclass(frozen=True)
class EuropeanDwellingAllocation:
    """D-EU-01 deterministic allocation independent of footprint geometry."""

    archetype_id: str
    building_type: str
    declared_apartments: float
    dwelling_count: int
    storey_count: int
    units_per_floor: int
    has_unconditioned_core: bool
    floor_allocations: tuple[EuropeanFloorAllocation, ...]


@dataclass(frozen=True)
class EuropeanFloorPartitionAudit:
    """Independent GEO-01/GEO-09 audit of one supplied dwelling-floor layout.

    This is an auditor, not a layout generator.  It deliberately does not
    import the existing DOE commercial layout-module dimensions for TABULA
    dwellings.  A later European footprint adapter supplies the polygons; this
    contract proves that its output neither changes the conditioned plate nor
    hides missing or overlapping dwelling areas.
    """

    expected_dwelling_count: int
    observed_dwelling_count: int
    footprint_area_m2: float
    union_area_m2: float
    gap_area_m2: float
    overlap_area_m2: float
    outside_area_m2: float
    area_error_fraction: float
    failures: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class EuropeanFloorLayoutFeasibility:
    """Fail-closed GEO-04 decision before a dwelling generator emits polygons.

    This is deliberately a feasibility gate, rather than an adapter around the
    repository's generic DOE room-layout generator.  That generator does not
    yet establish one-zone-per-European-dwelling semantics.  A narrow plate is
    therefore recorded as an explicit single-zone-per-floor fallback and may
    never be counted as successful dwelling-level geometry.
    """

    minimum_width_m: float
    requested_dwelling_count: int
    fallback_required: bool
    fallback_reason: str | None
    dwelling_layout_emitted: bool

    @property
    def status(self) -> str:
        return (
            "FALLBACK_ONE_ZONE_PER_FLOOR"
            if self.fallback_required
            else "DWELLING_LAYOUT_REQUIRED"
        )


@dataclass(frozen=True)
class EuropeanRealFootprintAudit:
    """A fail-closed geometry census over one acquired residential manifest.

    This records what the real source geometry can support before a European
    dwelling-layout generator exists.  In particular, it does *not* infer a
    typology, dwelling count, core, or emitted thermal zone from a footprint.
    Those inputs are not available in the frozen acquisition schema.
    """

    neighbourhood_id: str
    source_manifest: str
    source_sha256: str
    projected_crs: str
    footprint_count: int
    narrow_fallback_count: int
    courtyard_count: int
    non_convex_count: int
    dwelling_layout_emitted_count: int


@dataclass(frozen=True)
class EuropeanGeneratedFloorLayout:
    """A deterministic dwelling-only layout generated from one real footprint.

    The requested dwelling count is an explicit caller input.  Acquisition
    manifests do not identify per-building apartments, so this adapter must
    never derive it from a source tag, area, or geometry heuristic.  Core
    geometry is deliberately not emitted: fitting an unconditioned core inside
    an observed shell would silently change the conditioned-area contract.
    """

    requested_dwelling_count: int
    dwelling_polygons: tuple[BaseGeometry, ...]
    partition_audit: EuropeanFloorPartitionAudit | None
    facade_contact_lengths_m: tuple[float, ...]
    fallback_reason: str | None
    dwelling_layout_emitted: bool
    unconditioned_core_emitted: bool = False

    @property
    def status(self) -> str:
        return "DWELLING_LAYOUT_EMITTED" if self.dwelling_layout_emitted else "FALLBACK_PENDING_LAYOUT"


@dataclass(frozen=True)
class EuropeanUnconditionedCore:
    """An explicit unconditioned core attached outside a rectangular plate."""

    core_polygon: BaseGeometry | None
    requested_area_m2: float
    emitted_area_m2: float
    shared_boundary_length_m: float
    overlap_area_m2: float
    fallback_reason: str | None

    @property
    def emitted(self) -> bool:
        return self.core_polygon is not None and self.fallback_reason is None


def _minimum_rotated_width_m(footprint: BaseGeometry) -> float:
    """Return a polygon's short rotated-rectangle dimension in projected metres."""
    rectangle = footprint.minimum_rotated_rectangle
    coordinates = tuple(rectangle.exterior.coords)
    edge_lengths = tuple(
        math.dist(coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
    )
    if not edge_lengths or not all(math.isfinite(length) and length > 0.0 for length in edge_lengths):
        raise ValueError("footprint has no finite positive minimum-rectangle width")
    return min(edge_lengths)


def audit_real_footprint_manifest(
    manifest_path: Path | str,
    *,
    neighbourhood_id: str | None = None,
) -> tuple[pd.DataFrame, EuropeanRealFootprintAudit]:
    """Census real residential footprints without claiming generated layouts.

    The manifest must be projected because both width and area are physically
    interpreted.  Every returned row has ``dwelling_layout_emitted=False``;
    broad footprints are merely candidates for a future deterministic adapter,
    while narrow ones are explicitly recorded as the GEO-04 fallback.
    """
    path = Path(manifest_path)
    if not path.is_file():
        raise ValueError(f"Residential manifest does not exist: {path}")
    gdf = gpd.read_file(path)
    missing = REAL_FOOTPRINT_REQUIRED_COLUMNS - set(gdf.columns)
    if missing:
        raise ValueError(f"Residential manifest is missing required columns: {sorted(missing)}")
    if gdf.empty:
        raise ValueError("Residential manifest must contain at least one footprint")
    if gdf.crs is None or not gdf.crs.is_projected:
        raise ValueError("Residential manifest must use a projected CRS")
    if not gdf["osm_id"].is_unique:
        raise ValueError("Residential manifest osm_id values must be unique")

    site_id = neighbourhood_id or path.parent.name
    if not site_id:
        raise ValueError("neighbourhood_id is required")
    records: list[dict[str, object]] = []
    for row in gdf.sort_values("osm_id", kind="stable").itertuples(index=False):
        footprint = row.geometry
        if (
            footprint is None
            or footprint.is_empty
            or not footprint.is_valid
            or footprint.geom_type != "Polygon"
            or footprint.area <= 0.0
            or not all(math.isfinite(value) for value in footprint.bounds)
        ):
            raise ValueError(f"Invalid polygon geometry for building {row.osm_id!r}")
        minimum_width = _minimum_rotated_width_m(footprint)
        fallback_required = minimum_width < NARROW_FOOTPRINT_THRESHOLD_M
        records.append(
            {
                "neighbourhood_id": site_id,
                "building_id": str(row.osm_id),
                "footprint_area_m2": float(footprint.area),
                "minimum_width_m": minimum_width,
                "has_courtyard": bool(footprint.interiors),
                "is_non_convex": not footprint.equals(footprint.convex_hull),
                "fallback_required": fallback_required,
                "fallback_reason": "NARROW_FOOTPRINT_LT_8M" if fallback_required else "",
                "layout_status": (
                    "FALLBACK_ONE_ZONE_PER_FLOOR"
                    if fallback_required
                    else "DWELLING_LAYOUT_PENDING"
                ),
                "dwelling_layout_emitted": False,
            }
        )

    frame = pd.DataFrame.from_records(records)
    audit = EuropeanRealFootprintAudit(
        neighbourhood_id=site_id,
        source_manifest=path.as_posix(),
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        projected_crs=gdf.crs.to_string(),
        footprint_count=len(frame),
        narrow_fallback_count=int(frame["fallback_required"].sum()),
        courtyard_count=int(frame["has_courtyard"].sum()),
        non_convex_count=int(frame["is_non_convex"].sum()),
        dwelling_layout_emitted_count=0,
    )
    return frame, audit


def write_real_footprint_feasibility_census(
    manifests_root: Path | str,
    output_dir: Path | str,
) -> tuple[pd.DataFrame, list[EuropeanRealFootprintAudit]]:
    """Write reproducible GEO-04 real-footprint feasibility evidence.

    Only the audited ``02_residential_manifest.gpkg`` inputs are read.  The
    output remains a pre-layout census and cannot be treated as GEO-08 parity,
    GEO-10 sample-group completion, or emitted dwelling geometry.
    """
    root = Path(manifests_root)
    manifests = sorted(root.glob("*/02_residential_manifest.gpkg"))
    if not manifests:
        raise ValueError(f"No residential manifests found below {root}")
    frames: list[pd.DataFrame] = []
    audits: list[EuropeanRealFootprintAudit] = []
    for manifest in manifests:
        frame, audit = audit_real_footprint_manifest(manifest)
        frames.append(frame)
        audits.append(audit)
    all_rows = pd.concat(frames, ignore_index=True)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    all_rows.to_csv(destination / "real_footprint_feasibility.csv", index=False)
    summary = {
        "evidence_scope": "pre_layout_real_footprint_feasibility_only",
        "dwelling_layout_emitted": False,
        "site_audits": [audit.__dict__ for audit in audits],
        "total_footprints": int(len(all_rows)),
        "total_narrow_fallbacks": int(all_rows["fallback_required"].sum()),
        "total_courtyards": int(all_rows["has_courtyard"].sum()),
        "total_non_convex": int(all_rows["is_non_convex"].sum()),
    }
    (destination / "real_footprint_feasibility_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return all_rows, audits


def _rounded_count(value: float, name: str) -> int:
    """Apply D-EU-04's explicit half-up integer convention.

    Python's built-in ``round`` is bankers rounding; the ruled values are
    physical dwelling/storey counts, so this explicit convention remains stable at a
    half value and is recorded in the allocation metadata.
    """
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return int(math.floor(numeric + 0.5))


def derive_european_plate_area(
    *, conditioned_reference_area_m2: float, n_storey: float
) -> float:
    """Derive the D-EU-01 conditioned plate from the ruled storey count.

    The source float is preserved by the registry; the physical model must use
    the approved half-up integer count for both its storey stack and plate.
    This keeps the sum of conditioned floor areas exactly equal to ``A_C_Ref``
    for synthetic-average rows as well as for integral source rows.
    """
    reference_area = float(conditioned_reference_area_m2)
    if not math.isfinite(reference_area) or reference_area <= 0:
        raise ValueError("conditioned_reference_area_m2 must be finite and positive")
    return reference_area / _rounded_count(n_storey, "n_storey")


def assess_european_floor_layout_feasibility(
    footprint: BaseGeometry,
    *,
    requested_dwelling_count: int,
) -> EuropeanFloorLayoutFeasibility:
    """Apply GEO-04's registered narrow-plate fallback deterministically.

    Width is the short side of the minimum rotated rectangle, so the result is
    independent of orientation.  The operative rule is strictly ``< 8 m``:
    an exactly 8 m plate does not trigger this particular fallback.  Passing
    the gate does *not* claim a dwelling layout was generated; that remains
    impossible until the European footprint adapter supplies and audits its
    actual polygons.
    """
    requested_numeric = float(requested_dwelling_count)
    if (
        not math.isfinite(requested_numeric)
        or requested_numeric <= 0.0
        or not requested_numeric.is_integer()
    ):
        raise ValueError("requested_dwelling_count must be positive")
    requested = int(requested_numeric)
    if footprint.is_empty or not footprint.is_valid or footprint.area <= 0.0:
        raise ValueError("footprint must be a valid positive-area geometry")

    rectangle = footprint.minimum_rotated_rectangle
    coordinates = tuple(rectangle.exterior.coords)
    edge_lengths = tuple(
        math.dist(coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
    )
    minimum_width = min(edge_lengths)
    narrow = minimum_width < NARROW_FOOTPRINT_THRESHOLD_M
    return EuropeanFloorLayoutFeasibility(
        minimum_width_m=minimum_width,
        requested_dwelling_count=requested,
        fallback_required=narrow,
        fallback_reason="NARROW_FOOTPRINT_LT_8M" if narrow else None,
        dwelling_layout_emitted=False,
    )


def _is_convex_polygon(footprint: BaseGeometry, tolerance_m2: float = 1e-8) -> bool:
    return abs(float(footprint.convex_hull.area) - float(footprint.area)) <= tolerance_m2


def generate_external_unconditioned_core(
    conditioned_plate: BaseGeometry,
    *,
    requested_area_m2: float,
    tolerance_m2: float = 1e-8,
) -> EuropeanUnconditionedCore:
    """Attach the D-EU-01 core outside an explicit rectangular conditioned plate.

    This supports the ruled TABULA plate semantics: the core is additional
    unconditioned area, never carved from ``A_C_Ref``.  An observed irregular
    source shell lacks a declared gross-to-conditioned relationship, so it is
    intentionally outside this function's contract and receives no core.
    """
    area = float(requested_area_m2)
    if not math.isfinite(area) or area <= 0.0:
        raise ValueError("requested_area_m2 must be finite and positive")
    if conditioned_plate.geom_type != "Polygon" or conditioned_plate.is_empty or not conditioned_plate.is_valid:
        raise ValueError("conditioned_plate must be a valid Polygon")
    rectangle = conditioned_plate.minimum_rotated_rectangle
    if abs(float(rectangle.area) - float(conditioned_plate.area)) > tolerance_m2:
        return EuropeanUnconditionedCore(
            core_polygon=None,
            requested_area_m2=area,
            emitted_area_m2=0.0,
            shared_boundary_length_m=0.0,
            overlap_area_m2=0.0,
            fallback_reason="NON_RECTANGULAR_CONDITIONED_PLATE_UNSUPPORTED",
        )
    angle = _long_axis_angle_degrees(conditioned_plate)
    aligned = affinity.rotate(conditioned_plate, -angle, origin=(0.0, 0.0))
    min_x, min_y, max_x, max_y = aligned.bounds
    long_length = max_x - min_x
    if long_length <= 0.0:
        raise ValueError("conditioned_plate must have positive long-axis length")
    # The full long side is shared, so the core stays a simple rectangular zone
    # and its exact area is controlled only by the outward thickness.
    core_aligned = box(min_x, max_y, max_x, max_y + area / long_length)
    core = affinity.rotate(core_aligned, angle, origin=(0.0, 0.0))
    shared_boundary = float(core.boundary.intersection(conditioned_plate.boundary.buffer(1e-7)).length)
    overlap = float(core.intersection(conditioned_plate).area)
    emitted_area = float(core.area)
    if abs(emitted_area - area) > tolerance_m2:
        reason = "CORE_AREA_CONSERVATION_FAILED"
    elif overlap > tolerance_m2:
        reason = "CORE_OVERLAPS_CONDITIONED_PLATE"
    elif shared_boundary <= tolerance_m2:
        reason = "CORE_NOT_ADJACENT_TO_CONDITIONED_PLATE"
    else:
        reason = None
    return EuropeanUnconditionedCore(
        core_polygon=core if reason is None else None,
        requested_area_m2=area,
        emitted_area_m2=emitted_area if reason is None else 0.0,
        shared_boundary_length_m=shared_boundary if reason is None else 0.0,
        overlap_area_m2=overlap,
        fallback_reason=reason,
    )


def _long_axis_angle_degrees(footprint: BaseGeometry) -> float:
    coordinates = tuple(footprint.minimum_rotated_rectangle.exterior.coords)
    edges = tuple(
        (coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
    )
    start, end = max(edges, key=lambda edge: math.dist(*edge))
    return math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))


def _facade_contact_lengths(footprint: BaseGeometry, dwellings: Iterable[BaseGeometry]) -> tuple[float, ...]:
    """Measure exterior contact after geometric transforms with a 0.1 µm tolerance."""
    facade_band = footprint.boundary.buffer(1e-7)
    return tuple(float(dwelling.boundary.intersection(facade_band).length) for dwelling in dwellings)


def generate_european_dwelling_layout(
    footprint: BaseGeometry,
    *,
    requested_dwelling_count: int,
    minimum_facade_contact_m: float = 2.5,
) -> EuropeanGeneratedFloorLayout:
    """Generate a deterministic strip partition for supported real footprints.

    A valid, broad, convex Polygon without courtyard holes is rotated onto its
    long axis, divided into equally spaced strips, and rotated back.  The
    resulting candidates must pass the independent area/topology audit and
    every dwelling must have the declared exterior-facade contact.  Any input
    outside that deliberately narrow contract falls back without emitted zones.
    """
    requested_numeric = float(requested_dwelling_count)
    if (
        not math.isfinite(requested_numeric)
        or requested_numeric <= 0.0
        or not requested_numeric.is_integer()
    ):
        raise ValueError("requested_dwelling_count must be positive")
    if not math.isfinite(minimum_facade_contact_m) or minimum_facade_contact_m <= 0.0:
        raise ValueError("minimum_facade_contact_m must be finite and positive")
    if footprint.geom_type != "Polygon":
        raise ValueError("footprint must be a Polygon for dwelling layout generation")
    requested = int(requested_numeric)
    feasibility = assess_european_floor_layout_feasibility(
        footprint,
        requested_dwelling_count=requested,
    )
    if feasibility.fallback_required:
        return EuropeanGeneratedFloorLayout(
            requested_dwelling_count=requested,
            dwelling_polygons=(),
            partition_audit=None,
            facade_contact_lengths_m=(),
            fallback_reason=feasibility.fallback_reason,
            dwelling_layout_emitted=False,
        )
    if footprint.interiors:
        reason = "COURTYARD_TOPOLOGY_UNSUPPORTED"
    elif not _is_convex_polygon(footprint):
        reason = "NON_CONVEX_TOPOLOGY_UNSUPPORTED"
    else:
        reason = None
    if reason is not None:
        return EuropeanGeneratedFloorLayout(
            requested_dwelling_count=requested,
            dwelling_polygons=(),
            partition_audit=None,
            facade_contact_lengths_m=(),
            fallback_reason=reason,
            dwelling_layout_emitted=False,
        )

    angle = _long_axis_angle_degrees(footprint)
    # Rotate around the local footprint centroid.  This keeps the operation
    # numerically stable at projected CRS magnitudes and makes the result
    # invariant under a pure translation of the source coordinates.
    rotation_origin = footprint.centroid
    aligned = affinity.rotate(footprint, -angle, origin=rotation_origin)
    min_x, min_y, max_x, max_y = aligned.bounds
    strip_width = (max_x - min_x) / requested
    candidates = tuple(
        affinity.rotate(
            aligned.intersection(box(min_x + index * strip_width, min_y, min_x + (index + 1) * strip_width, max_y)),
            angle,
            origin=rotation_origin,
        )
        for index in range(requested)
    )
    if any(candidate.geom_type != "Polygon" or candidate.is_empty for candidate in candidates):
        return EuropeanGeneratedFloorLayout(
            requested_dwelling_count=requested,
            dwelling_polygons=(),
            partition_audit=None,
            facade_contact_lengths_m=(),
            fallback_reason="MULTIPART_PARTITION_UNSUPPORTED",
            dwelling_layout_emitted=False,
        )
    partition_audit = audit_european_floor_partition(
        footprint,
        candidates,
        expected_dwelling_count=requested,
        topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    )
    facade_lengths = _facade_contact_lengths(footprint, candidates)
    if not partition_audit.passed:
        reason = "PARTITION_AUDIT_FAILED"
    elif any(length < minimum_facade_contact_m for length in facade_lengths):
        reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
    else:
        reason = None
    return EuropeanGeneratedFloorLayout(
        requested_dwelling_count=requested,
        dwelling_polygons=candidates if reason is None else (),
        partition_audit=partition_audit,
        facade_contact_lengths_m=facade_lengths,
        fallback_reason=reason,
        dwelling_layout_emitted=reason is None,
    )


def european_layout_to_zone_specs(
    layout: EuropeanGeneratedFloorLayout,
    *,
    building_id: str,
    floor_index: int = 0,
    z_floor_m: float = 0.0,
    height_m: float = 3.0,
) -> list[dict[str, object]]:
    """Translate one emitted dwelling layout into explicit extrusion inputs.

    No default is provided for a failed layout.  This keeps a named fallback
    from being accidentally converted into a one-zone dwelling success.
    """
    identifier = str(building_id).strip()
    if not identifier:
        raise ValueError("building_id is required")
    if floor_index < 0:
        raise ValueError("floor_index must be non-negative")
    if not math.isfinite(z_floor_m) or not math.isfinite(height_m) or height_m <= 0.0:
        raise ValueError("z_floor_m must be finite and height_m must be finite and positive")
    if not layout.dwelling_layout_emitted or not layout.partition_audit or not layout.partition_audit.passed:
        raise ValueError("Cannot create zone specs from a layout that was not emitted cleanly")
    return [
        {
            "name": f"{identifier}_F{floor_index}_dwelling_{index}",
            "floor_polygon": polygon,
            "coords_m": list(polygon.exterior.coords)[:-1],
            "z_floor": z_floor_m,
            "z_ceiling": z_floor_m + height_m,
            "height_m": height_m,
            "mode": "european_dwelling_layout",
        }
        for index, polygon in enumerate(layout.dwelling_polygons)
    ]


def allocate_european_dwellings(
    *,
    archetype_id: str,
    building_type: str,
    n_apartment: float,
    n_storey: float,
    plate_area_m2: float,
) -> EuropeanDwellingAllocation:
    """Allocate dwelling zones per D-EU-01/D-EU-04 without silent loss.

    Floors receive quotient dwellings plus the first ``remainder`` storeys
    receiving one additional dwelling.  This fixes GEO-07's storey order and
    makes the exact total independently checkable.  A core is added outside
    the conditioned plate at the ruling's lower 6% bound only when the rounded
    dwelling density is at least two per storey.
    """
    identifier = str(archetype_id).strip()
    typology = str(building_type).strip().upper()
    if not identifier:
        raise ValueError("archetype_id is required")
    if typology not in RESIDENTIAL_TYPES:
        raise ValueError("building_type must be one of SFH, TH, MFH, AB")
    storeys = _rounded_count(n_storey, "n_storey")
    plate = float(plate_area_m2)
    if not math.isfinite(plate) or plate <= 0:
        raise ValueError("plate_area_m2 must be finite and positive")

    dwellings = _rounded_count(n_apartment, "n_apartment")
    quotient, remainder = divmod(dwellings, storeys)
    units_per_floor = math.ceil(dwellings / storeys)
    core_required = dwellings / storeys >= 2.0
    core_area = plate * CORE_FRACTION_OF_PLATE if core_required else 0.0
    floors = tuple(
        EuropeanFloorAllocation(
            storey_index=index,
            dwelling_count=quotient + (1 if index < remainder else 0),
            conditioned_area_m2=plate,
            unconditioned_core_area_m2=core_area,
        )
        for index in range(storeys)
    )
    if sum(floor.dwelling_count for floor in floors) != dwellings:
        raise AssertionError("internal dwelling allocation failed to conserve the rounded total")
    return EuropeanDwellingAllocation(
        archetype_id=identifier,
        building_type=typology,
        declared_apartments=float(n_apartment),
        dwelling_count=dwellings,
        storey_count=storeys,
        units_per_floor=units_per_floor,
        has_unconditioned_core=core_required,
        floor_allocations=floors,
    )


def audit_european_floor_partition(
    footprint: BaseGeometry,
    dwelling_polygons: Iterable[BaseGeometry],
    *,
    expected_dwelling_count: int,
    relative_area_tolerance: float = 0.01,
    topology_tolerance_fraction: float = EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    topology_tolerance_m2: float | None = None,
) -> EuropeanFloorPartitionAudit:
    """Fail closed on a supplied European floor partition that violates GEO-01.

    The audit is intentionally independent of the future layout generator:
    it compares a union of emitted dwelling polygons to the source footprint.
    GEO-01 allows at most one-percent total area error, while gaps, overlaps,
    and geometry outside the plate remain separate topology failures.  The
    tiny topology tolerance only absorbs geometric floating-point noise.
    """
    expected = int(expected_dwelling_count)
    if expected <= 0:
        raise ValueError("expected_dwelling_count must be positive")
    if not 0.0 <= relative_area_tolerance <= 1.0:
        raise ValueError("relative_area_tolerance must be between zero and one")
    if topology_tolerance_fraction < 0.0:
        raise ValueError("topology_tolerance_fraction must be non-negative")
    if topology_tolerance_m2 is not None and topology_tolerance_m2 < 0.0:
        raise ValueError("topology_tolerance_m2 must be non-negative")
    if footprint.is_empty or not footprint.is_valid or footprint.area <= 0.0:
        raise ValueError("footprint must be a valid positive-area geometry")

    dwellings = tuple(dwelling_polygons)
    invalid = tuple(
        polygon
        for polygon in dwellings
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 0.0
    )
    valid_dwellings = tuple(polygon for polygon in dwellings if polygon not in invalid)
    union = unary_union(valid_dwellings) if valid_dwellings else footprint.boundary
    union_area = float(union.area)
    footprint_area = float(footprint.area)
    # Compatibility callers may provide an explicit tolerance, but all
    # production European generation calls use the declared relative rule.
    topology_tolerance = (
        float(topology_tolerance_m2)
        if topology_tolerance_m2 is not None
        else footprint_area * float(topology_tolerance_fraction)
    )
    total_dwelling_area = sum(float(polygon.area) for polygon in valid_dwellings)
    gap_area = float(footprint.difference(union).area)
    outside_area = float(union.difference(footprint).area)
    overlap_area = max(0.0, total_dwelling_area - union_area)
    area_error = abs(union_area - footprint_area) / footprint_area

    failures: list[str] = []
    if len(dwellings) != expected:
        failures.append("DWELLING_COUNT")
    if invalid:
        failures.append("INVALID_DWELLING")
    if gap_area > topology_tolerance:
        failures.append("AREA_GAP")
    if overlap_area > topology_tolerance:
        failures.append("AREA_OVERLAP")
    if outside_area > topology_tolerance:
        failures.append("OUTSIDE_FOOTPRINT")
    if area_error > relative_area_tolerance:
        failures.append("AREA_CONSERVATION")
    return EuropeanFloorPartitionAudit(
        expected_dwelling_count=expected,
        observed_dwelling_count=len(dwellings),
        footprint_area_m2=footprint_area,
        union_area_m2=union_area,
        gap_area_m2=gap_area,
        overlap_area_m2=overlap_area,
        outside_area_m2=outside_area,
        area_error_fraction=area_error,
        failures=tuple(failures),
    )
