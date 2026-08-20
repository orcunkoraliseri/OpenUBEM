"""T04 of PLAN_ten-items-2026-08-18-late.md -- OPEN-42's live question, on an artifact
the register believed no longer existed.

The register's 2026-08-18 ruling closed OPEN-42's investigation with: "the E02 IDF corpus
that could show the actual per-surface geometry no longer exists on disk", so "any next
step needs either a fresh EnergyPlus run (compute, not authorised) or a user decision to
close the question without a mechanism."

That premise is false. Run 2 (open48_refleet, 13 August) rebuilt all six buildings, kept
their IDFs, and reproduced the identical thermal-runaway failure. This script reads those
IDFs and asks the register's own live question: what is different about the fatal zone.

Two things are tested:
  1. Is the fatal zone the building's topmost storey? (the register's stated invariant,
     "without exception" on the E02 corpus)
  2. Does the fatal zone differ geometrically from its non-fatal siblings in the same
     IDF -- surface count, surface types, boundary conditions, constructions, areas?

Emits openubem/outputs/comparisons/open42_run2_fatal_zone_geometry.csv.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"

SIX = [
    ("la_rural", "way_472960972"), ("la_rural", "way_472961034"),
    ("la_rural", "way_472961088"), ("la_rural", "way_472961091"),
    ("la_rural", "way_472961171"), ("la_urban", "way_402215469"),
]

_ZONE_RX = re.compile(r"_F(\d+)_", re.I)


def _objects(text: str, kind: str) -> list[list[str]]:
    """Crude but sufficient IDF object splitter: returns each object's field list."""
    out = []
    for raw in text.split(";"):
        body = "\n".join(
            ln.split("!")[0].strip() for ln in raw.splitlines() if ln.split("!")[0].strip()
        )
        if not body:
            continue
        fields = [f.strip() for f in body.split(",")]
        if fields and fields[0].strip().upper() == kind.upper():
            out.append(fields)
    return out


def _poly_area(vertices: list[tuple[float, float, float]]) -> float:
    """Newell's method -- 3D polygon area, orientation-independent."""
    nx = ny = nz = 0.0
    n = len(vertices)
    for i in range(n):
        x1, y1, z1 = vertices[i]
        x2, y2, z2 = vertices[(i + 1) % n]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return 0.5 * (nx * nx + ny * ny + nz * nz) ** 0.5


def _fatal_zones(err: Path) -> set[str]:
    if not err.exists():
        return set()
    txt = err.read_text(encoding="utf-8", errors="replace")
    return {m.upper() for m in re.findall(
        r'Temperature \((?:low|high)\) out of bounds [\[(][^\])]*[\])] for zone="([^"]+)"', txt)}


def main() -> int:
    rows = []
    for cell, stem in SIX:
        idf = BASE / cell / "step3" / "idfs" / f"{stem}.idf"
        err = BASE / cell / "sim_out" / stem / "eplusout.err"
        if not idf.exists():
            print(f"MISSING IDF {idf}")
            continue
        text = idf.read_text(encoding="utf-8", errors="replace")
        fatal = _fatal_zones(err)

        zones = [o[1].strip() for o in _objects(text, "Zone")]
        storeys = {z: int(_ZONE_RX.search(z).group(1)) for z in zones if _ZONE_RX.search(z)}
        top = max(storeys.values()) if storeys else -1

        per_zone: dict[str, dict] = {
            z: {"n_surf": 0, "types": {}, "bcs": {}, "constructions": {}, "area": 0.0,
                "min_z": None, "max_z": None}
            for z in zones
        }
        for f in _objects(text, "BuildingSurface:Detailed"):
            # EnergyPlus 23.1 field order, 1-based after the object keyword at f[0]:
            # 1 Name, 2 Surface Type, 3 Construction, 4 Zone, 5 Space, 6 Outside BC,
            # 7 Outside BC Object, 8 Sun Exp, 9 Wind Exp, 10 View Factor, 11 N vertices,
            # then x,y,z triples from f[12].
            if len(f) < 15:
                continue
            stype, constr, zone, obc = f[2].strip(), f[3].strip(), f[4].strip(), f[6].strip()
            if zone not in per_zone:
                continue
            coords = [c for c in f[12:] if c not in ("", "autocalculate")]
            verts = []
            for i in range(0, len(coords) - 2, 3):
                try:
                    verts.append((float(coords[i]), float(coords[i + 1]), float(coords[i + 2])))
                except ValueError:
                    break
            d = per_zone[zone]
            d["n_surf"] += 1
            d["types"][stype] = d["types"].get(stype, 0) + 1
            d["bcs"][obc] = d["bcs"].get(obc, 0) + 1
            d["constructions"][constr] = d["constructions"].get(constr, 0) + 1
            if verts:
                d["area"] += _poly_area(verts)
                zs = [v[2] for v in verts]
                d["min_z"] = min(zs) if d["min_z"] is None else min(d["min_z"], min(zs))
                d["max_z"] = max(zs) if d["max_z"] is None else max(d["max_z"], max(zs))

        for z in zones:
            d = per_zone[z]
            st = storeys.get(z, -1)
            rows.append({
                "cell": cell, "building": stem, "zone": z, "storey": st,
                "is_topmost": st == top, "n_storeys": top + 1,
                "is_fatal": z.upper() in fatal,
                "n_surfaces": d["n_surf"],
                "surface_types": "|".join(f"{k}:{v}" for k, v in sorted(d["types"].items())),
                "boundary_conditions": "|".join(f"{k}:{v}" for k, v in sorted(d["bcs"].items())),
                "n_constructions": len(d["constructions"]),
                "total_surface_area_m2": round(d["area"], 2),
                "min_z": d["min_z"], "max_z": d["max_z"],
            })

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open42_run2_fatal_zone_geometry.csv"
    df.to_csv(dest, index=False)

    print("=== Q1: is the fatal zone the topmost storey? ===")
    fz = df[df["is_fatal"]]
    print(fz[["building", "zone", "storey", "n_storeys", "is_topmost"]].to_string(index=False))
    print(f"\nfatal zones: {len(fz)}   topmost: {int(fz['is_topmost'].sum())}   "
          f"NOT topmost: {int((~fz['is_topmost']).sum())}")

    print("\n=== Q2: fatal zone vs its siblings in the same IDF ===")
    with pd.option_context("display.width", 260, "display.max_columns", 40):
        for b in df["building"].unique():
            print(f"\n--- {b}")
            print(df[df["building"] == b][
                ["zone", "storey", "is_fatal", "n_surfaces", "surface_types",
                 "boundary_conditions", "total_surface_area_m2", "min_z", "max_z"]
            ].to_string(index=False))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
