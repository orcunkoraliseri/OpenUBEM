"""EU-18a T01: read floor plans out of the emitted EU-11 IDFs (plain text).

`FINDING 213` / rule 3 of `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md`: every
coverage number this arc produces from here on is read out of the ``.idf``
files, never out of the side-cars or the manifest's simulated numbers. This
module is the single reader shared by the plan pages (T02), the parity gate
(T03) and the census (T04/T12) so none of them can disagree with each other.

Reading is a plain text parse, not an ``eppy``/IDD load (dependency decision
`PLAN` §4.2): the only two object types needed, ``ZONE`` and
``BUILDINGSURFACE:DETAILED`` (Surface Type ``floor``), are trivially
line-oriented. ``tests/test_eu_idf_plan_reader.py`` proves this parse against
eppy on a spanning sample.

Zone-name taxonomy (``european_residential.py:1838-1903``, dependency
decision `PLAN` §4.3): a zone name is ``<stem>_F<i>_dwelling_<k>``
(conditioned dwelling), ``<stem>_F<i>_circulation`` (unconditioned core /
corridor) or ``<stem>_F<i>_whole`` (massing-box fallback, also conditioned).
A zone name matching none of the three is an error, never a default.

A zone's floor may be written as more than one ``BUILDINGSURFACE:DETAILED``
floor object (observed on courtyard / L-shape zones) -- this reader keeps
every sub-ring, never merges or drops one (rule 6: real footprints stay
real), and sums their shoelace areas for the zone's own area.

Coordinates are absolute projected metres (UTM, per district CRS) as they
sit in the IDF. This module's ``BuildingPlan`` keeps that full precision --
areas are computed from it, and it is what `T03`'s parity gate and `T04`'s
census compare against the side-car / manifest to 1e-6 relative. The 1 cm
local-origin rounding dependency decision §4.4 requires *before anything
reaches the HTML* is applied by ``local_ring_1cm`` below, called by T02 at
page-emission time -- never baked into the canonical reader output, because
it would violate this module's own 1e-6 area-parity test.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from scripts.run_eu_s2_district_campaign import DISTRICTS, FLOOR_TO_FLOOR_M

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_EU11 = ROOT / "openubem/outputs/eu_evidence/EU-11"

_OBJECT_RE = re.compile(r"^([A-Za-z][A-Za-z0-9:_]*),[ \t]*\r?\n(.*?);", re.MULTILINE | re.DOTALL)
_FIELD_RE = re.compile(r"^[ \t]*([^,;]*)[,;][ \t]*!-[ \t]*(.*?)[ \t]*$")
_VERTEX_RE = re.compile(r"^Vertex (\d+) (X|Y|Z)coordinate$")

_ZONE_NAME_RE = re.compile(
    r"^(?P<stem>.+)_F(?P<storey>\d+)_(?P<kind_token>dwelling_(?P<dwelling_index>\d+)|circulation|whole)$"
)

ZONE_KINDS = ("dwelling", "circulation", "whole")


class UnrecognizedZoneNameError(ValueError):
    """A ZONE name matched none of the three taxonomy patterns (dep. decision §4.3)."""


@dataclass(frozen=True)
class ZonePlan:
    name: str
    storey: int
    kind: str  # "dwelling" | "circulation" | "whole"
    dwelling_index: int | None
    rings: tuple[tuple[tuple[float, float], ...], ...]
    area_m2: float


@dataclass(frozen=True)
class BuildingPlan:
    stem: str
    building_id: str
    district: str
    geometry_outcome: str
    storey_count: int
    """Physical storey count, read off the tallest zone's height /
    ``FLOOR_TO_FLOOR_M`` -- never the count of distinct zone storey
    *indices*, which under-counts whenever a floor group absorbed more than
    one physical storey into a single extruded zone (see
    ``parse_idf_floor_zones``)."""
    zone_storey_group_count: int
    """Count of distinct zone storey indices actually present -- what the
    IDF's zone *names* differentiate spatially. Kept distinct from
    ``storey_count`` because the two diverge exactly on absorbed groups."""
    dwelling_count: int
    zone_names: tuple[str, ...]
    zones: tuple[ZonePlan, ...]
    gross_area_m2: float
    conditioned_area_m2: float
    circulation_area_m2: float
    origin_xy: tuple[float, float]

    def has_unconditioned_core(self) -> bool:
        return any(z.kind == "circulation" for z in self.zones)

    def is_ruled(self) -> bool:
        """``True`` when at least one storey carries a dwelling/circulation
        zone rather than the single-zone-per-floor massing box."""
        return any(z.kind in ("dwelling", "circulation") for z in self.zones)


def _iter_idf_objects(text: str):
    for match in _OBJECT_RE.finditer(text):
        obj_type = match.group(1).strip().upper()
        fields: list[tuple[str, str]] = []
        for line in match.group(2).splitlines():
            fmatch = _FIELD_RE.match(line)
            if fmatch:
                fields.append((fmatch.group(1).strip(), fmatch.group(2).strip()))
        yield obj_type, fields


def _field(fields: list[tuple[str, str]], comment_exact: str) -> str | None:
    for value, comment in fields:
        if comment == comment_exact:
            return value
    return None


def _ring_area(ring: list[tuple[float, float]]) -> float:
    """Shoelace area, computed on the ring shifted to its own first vertex.

    The absolute UTM vertex coordinates in these IDFs run ~4.4e5/4.5e6; the
    plain shoelace sum ``x1*y2 - x2*y1`` on coordinates of that magnitude
    loses ~5-6 significant digits to cancellation against buildings whose
    area is only ~1e1-1e2 m2 (measured relative error up to 3.6e-5 against
    an independent shapely oracle). Shifting to a local origin first removes
    the cancellation and is what ``tests/test_eu_idf_plan_reader.py`` holds
    to 1e-6 relative.
    """
    n = len(ring)
    if n < 3:
        return 0.0
    x0, y0 = ring[0]
    total = 0.0
    for i in range(n):
        x1, y1 = ring[i][0] - x0, ring[i][1] - y0
        x2, y2 = ring[(i + 1) % n][0] - x0, ring[(i + 1) % n][1] - y0
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def parse_idf_floor_zones(
    idf_path: Path,
) -> tuple[list[str], dict[str, list[list[tuple[float, float]]]], dict[str, float]]:
    """Return ``(zone_names, floor_rings, zone_max_z)``.

    ``zone_names`` is the ordered list of every declared ``ZONE`` name.
    ``floor_rings`` maps each zone name that owns at least one
    ``BUILDINGSURFACE:DETAILED`` floor object to the list of its floor
    rings (each ring a list of ``(x, y)`` in absolute projected metres, Z
    dropped, closing vertex not repeated).
    ``zone_max_z`` maps every zone name to the highest Z-coordinate found on
    any of its surfaces (wall/ceiling/floor) -- a zone whose floor-group
    absorbed several physical storeys (`european_residential.py:1857-1880`)
    is emitted as a *single* extruded zone tagged with only its group's
    start storey index, so a physical storey count cannot be read off the
    zone-name index alone; it is read off this height instead (dependency
    decision §4.9's ``FLOOR_TO_FLOOR_M`` = 3.0 m is constant, so
    ``round(max_z / 3.0)`` is the building's true physical storey count).
    """
    text = idf_path.read_text(encoding="utf-8", errors="replace")
    zone_names: list[str] = []
    floor_rings: dict[str, list[list[tuple[float, float]]]] = {}
    zone_max_z: dict[str, float] = {}
    for obj_type, fields in _iter_idf_objects(text):
        if obj_type == "ZONE":
            name = _field(fields, "Name")
            if name:
                zone_names.append(name)
        elif obj_type == "BUILDINGSURFACE:DETAILED":
            zone_name = _field(fields, "Zone Name")
            if not zone_name:
                continue
            verts: dict[int, dict[str, float]] = {}
            for value, comment in fields:
                vmatch = _VERTEX_RE.match(comment)
                if vmatch:
                    idx = int(vmatch.group(1))
                    axis = vmatch.group(2)
                    verts.setdefault(idx, {})[axis] = float(value)
            z_values = [v["Z"] for v in verts.values() if "Z" in v]
            if z_values:
                zone_max_z[zone_name] = max(zone_max_z.get(zone_name, 0.0), max(z_values))

            surface_type = _field(fields, "Surface Type")
            if surface_type is None or surface_type.strip().lower() != "floor":
                continue
            ring = [
                (verts[i]["X"], verts[i]["Y"])
                for i in sorted(verts)
                if "X" in verts[i] and "Y" in verts[i]
            ]
            if len(ring) >= 3:
                floor_rings.setdefault(zone_name, []).append(ring)
    return zone_names, floor_rings, zone_max_z


def classify_zone_name(zone_name: str) -> tuple[str, int, str, int | None]:
    """Return ``(stem, storey, kind, dwelling_index)`` or raise
    ``UnrecognizedZoneNameError`` (dependency decision §4.3: a name matching
    none of the three patterns is an error, never a default)."""
    match = _ZONE_NAME_RE.match(zone_name)
    if not match:
        raise UnrecognizedZoneNameError(f"Zone name matches no taxonomy pattern: {zone_name!r}")
    stem = match.group("stem")
    storey = int(match.group("storey"))
    kind_token = match.group("kind_token")
    if kind_token == "circulation":
        return stem, storey, "circulation", None
    if kind_token == "whole":
        return stem, storey, "whole", None
    return stem, storey, "dwelling", int(match.group("dwelling_index"))


def _storey0_centroid(zones: list[ZonePlan]) -> tuple[float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for zone in zones:
        if zone.storey != 0:
            continue
        for ring in zone.rings:
            for x, y in ring:
                xs.append(x)
                ys.append(y)
    if not xs:
        return (0.0, 0.0)
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def read_building_plan(
    idf_path: Path,
    *,
    stem: str,
    building_id: str,
    district: str,
    geometry_outcome: str,
) -> BuildingPlan:
    zone_names, floor_rings, zone_max_z = parse_idf_floor_zones(idf_path)

    zones: list[ZonePlan] = []
    for zone_name in zone_names:
        rings_raw = floor_rings.get(zone_name)
        if not rings_raw:
            raise ValueError(f"{idf_path.name}: ZONE {zone_name!r} has no floor surface")
        _, storey, kind, dwelling_index = classify_zone_name(zone_name)
        area = sum(_ring_area(ring) for ring in rings_raw)
        zones.append(
            ZonePlan(
                name=zone_name,
                storey=storey,
                kind=kind,
                dwelling_index=dwelling_index,
                rings=tuple(tuple(ring) for ring in rings_raw),
                area_m2=area,
            )
        )

    origin_xy = _storey0_centroid(zones)
    translated_zones = [
        ZonePlan(
            name=z.name,
            storey=z.storey,
            kind=z.kind,
            dwelling_index=z.dwelling_index,
            rings=tuple(
                tuple((x - origin_xy[0], y - origin_xy[1]) for x, y in ring) for ring in z.rings
            ),
            area_m2=z.area_m2,
        )
        for z in zones
    ]

    zone_storey_group_count = len({z.storey for z in translated_zones}) if translated_zones else 0
    dwelling_count = sum(1 for z in translated_zones if z.kind == "dwelling")
    conditioned_area = sum(z.area_m2 for z in translated_zones if z.kind in ("dwelling", "whole"))
    circulation_area = sum(z.area_m2 for z in translated_zones if z.kind == "circulation")

    max_z = max(zone_max_z.values()) if zone_max_z else 0.0
    physical_storey_count = max(1, round(max_z / FLOOR_TO_FLOOR_M)) if max_z > 0 else zone_storey_group_count

    return BuildingPlan(
        stem=stem,
        building_id=building_id,
        district=district,
        geometry_outcome=geometry_outcome,
        storey_count=physical_storey_count,
        zone_storey_group_count=zone_storey_group_count,
        dwelling_count=dwelling_count,
        zone_names=tuple(zone_names),
        zones=tuple(translated_zones),
        gross_area_m2=conditioned_area + circulation_area,
        conditioned_area_m2=conditioned_area,
        circulation_area_m2=circulation_area,
        origin_xy=origin_xy,
    )


def round_ring_1cm(ring: tuple[tuple[float, float], ...]) -> list[list[float]]:
    """1 cm quantization applied only when a ring is about to reach the
    HTML pages (dependency decision §4.4). Never applied to the canonical
    ``BuildingPlan`` used for area/parity comparisons."""
    return [[round(x, 2), round(y, 2)] for x, y in ring]


def district_paths(district: str) -> Path:
    if district not in DISTRICTS:
        raise ValueError(f"Unknown district: {district!r}. Known: {sorted(DISTRICTS)}")
    return EVIDENCE_EU11 / district


def load_prepared_buildings(district: str, evidence_root: Path | None = None) -> pd.DataFrame:
    root = evidence_root if evidence_root is not None else district_paths(district)
    return pd.read_csv(root / "prepared_buildings.csv", dtype=str)


def load_manifest(district: str, evidence_root: Path | None = None) -> pd.DataFrame:
    root = evidence_root if evidence_root is not None else district_paths(district)
    manifest_name = district.lower().replace("-", "_") + "_manifest.csv"
    return pd.read_csv(root / manifest_name, dtype=str)


def read_district(district: str, evidence_root: Path | None = None, skip_missing: bool = False) -> list[BuildingPlan]:
    """Read every building's plan for one district's IDF tree.

    ``evidence_root`` overrides the EU-11 default (used by T12 to point at
    the EU-17 rebuild tree) -- it must contain ``idfs/``,
    ``prepared_buildings.csv`` and the district manifest, same layout as
    EU-11 (dependency decision §4.8).
    """
    root = evidence_root if evidence_root is not None else district_paths(district)
    idf_dir = root / "idfs"
    prepared = load_prepared_buildings(district, root)
    manifest = load_manifest(district, root)
    geometry_outcome_by_id = dict(zip(manifest["building_id"], manifest["geometry_outcome"]))

    plans: list[BuildingPlan] = []
    for _, row in prepared.iterrows():
        building_id = row["building_id"]
        stem = row["stem"]
        idf_path = idf_dir / f"{stem}.idf"
        if not idf_path.exists():
            if skip_missing:
                continue
            raise FileNotFoundError(f"{district}: prepared_buildings.csv names {stem} but {idf_path} is missing")
        geometry_outcome = geometry_outcome_by_id.get(building_id)
        if geometry_outcome is None:
            if skip_missing:
                continue
            raise ValueError(f"{district}: {building_id} is in prepared_buildings.csv but not in the manifest")
        plans.append(
            read_building_plan(
                idf_path,
                stem=stem,
                building_id=building_id,
                district=district,
                geometry_outcome=geometry_outcome,
            )
        )
    return plans


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Report per-district IDF plan-reader counts.")
    parser.add_argument("--district", choices=sorted(DISTRICTS), required=True)
    args = parser.parse_args()

    built_plans = read_district(args.district)
    ruled = sum(1 for p in built_plans if p.is_ruled())
    cored = sum(1 for p in built_plans if p.has_unconditioned_core())
    print(f"{args.district}: {len(built_plans)} buildings, {ruled} ruled, {cored} with a core")
