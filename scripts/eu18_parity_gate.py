"""EU-18a T03: IDF <-> side-car <-> manifest parity gate (report-only in this phase).

For every building this compares the geometry the IDF (`scripts/eu_idf_plan_reader.py`,
rule 3: measured on the emitted IDF) actually carries against what the
per-building side-car and the district manifest *claim* ran. Five
dimensions, per T03's "What":

1. ``scheme_consistent`` -- the side-car's own claim (``DWELLING_LAYOUT_EMITTED*``
   vs not) agrees with whether the IDF's own zone kinds show a ruled layout
   or the single-zone-per-floor massing box (`FINDING 213`).
2. ``zone_names_equal`` -- the IDF's zone-name set equals the set the
   side-car's own ``floors[]`` (or, when refused, ``one_zone_per_floor``)
   implies, after substituting the side-car's ``building_id`` prefix for the
   IDF's ``stem`` prefix (the two layers name zones with different
   identifiers for the same building).
3. ``circulation_presence_equal`` -- the IDF carries a ``circulation`` zone
   iff the side-car's ``has_unconditioned_core`` says so.
4. ``storey_count_equal`` -- the IDF's own physical storey count (read off
   the tallest zone's height / ``FLOOR_TO_FLOOR_M``, dependency decision
   §4.9) equals the side-car's declared ``storeys``.
5. ``area_conservation_ok`` -- the IDF's own conserved identity,
   ``conditioned + circulation == gross`` (`fact 10`, measured fleet-wide to
   1.2e-6 relative), holds to 1e-6 relative. This is *not* a cross-check of
   the IDF's gross area against the side-car's declared
   ``gross_footprint_area_m2``: dependency decision §4.9 keeps
   ``REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION = 0.02`` in force, so the
   side-car's regularized plate area and the IDF's real-footprint area
   (rule 6) legitimately differ by up to 2% by design -- comparing them at
   1e-6 would fail almost the entire fleet on an intentional tolerance, not
   a defect.

Writes ``openubem/outputs/eu_evidence/EU-18/parity_<district>.csv`` (one row
per building) and prints a per-district summary. Exits 1 on any divergence.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from scripts.eu_idf_plan_reader import BuildingPlan, district_paths, read_district
from scripts.run_eu_s2_district_campaign import DISTRICTS

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "openubem/outputs/eu_evidence/EU-18"

_NAME_STOREY_RE = re.compile(r"_F(\d+)_")


def _load_sidecar(root: Path, building_id: str) -> dict | None:
    path = root / "layouts" / f"{building_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_zone_names(sidecar: dict, stem: str, expected_ruled: bool) -> set[str]:
    if not expected_ruled:
        return {f"{stem}_F{i}_whole" for i in range(int(sidecar["storeys"]))}
    building_id = sidecar["building_id"]
    names: set[str] = set()
    for floor in sidecar.get("floors") or []:
        zone_list = floor.get("zones") or []
        for zone in zone_list:
            names.add(str(zone["name"]).replace(building_id, stem, 1))
        if floor.get("has_unconditioned_core") and floor.get("circulation") and zone_list:
            match = _NAME_STOREY_RE.search(zone_list[0]["name"])
            if match:
                names.add(f"{stem}_F{match.group(1)}_circulation")
    return names


def _row(plan: BuildingPlan, root: Path) -> dict:
    sidecar = _load_sidecar(root, plan.building_id)
    if sidecar is None:
        return {
            "building_id": plan.building_id, "stem": plan.stem, "district": plan.district,
            "geometry_outcome": plan.geometry_outcome, "sidecar_present": False,
            "scheme_consistent": None, "zone_names_equal": None, "circulation_presence_equal": None,
            "storey_count_equal": None, "area_conservation_ok": None,
            "idf_storey_count": plan.storey_count, "sidecar_storey_count": None,
            "divergent": True, "divergence_notes": "NO_SIDECAR",
        }

    expected_ruled = str(sidecar.get("geometry_outcome", "")).startswith("DWELLING_LAYOUT_EMITTED")
    idf_ruled = plan.is_ruled()
    scheme_consistent = expected_ruled == idf_ruled

    expected_names = _expected_zone_names(sidecar, plan.stem, expected_ruled)
    zone_names_equal = set(plan.zone_names) == expected_names

    circulation_presence_equal = plan.has_unconditioned_core() == bool(sidecar.get("has_unconditioned_core"))

    sidecar_storeys = sidecar.get("storeys")
    storey_count_equal = plan.storey_count == sidecar_storeys

    conserved_sum = plan.conditioned_area_m2 + plan.circulation_area_m2
    area_conservation_ok = (
        abs(conserved_sum - plan.gross_area_m2) / plan.gross_area_m2 < 1e-6
        if plan.gross_area_m2 > 0 else True
    )

    notes = []
    if not scheme_consistent:
        notes.append("SCHEME_DIVERGENT_FINDING_213")
    if not zone_names_equal:
        notes.append("ZONE_NAME_SET_MISMATCH")
    if not circulation_presence_equal:
        notes.append("CIRCULATION_PRESENCE_MISMATCH")
    if not storey_count_equal:
        notes.append(f"STOREY_COUNT_MISMATCH(idf={plan.storey_count},sidecar={sidecar_storeys})")
    if not area_conservation_ok:
        notes.append("AREA_CONSERVATION_FAILED")

    divergent = bool(notes)
    return {
        "building_id": plan.building_id, "stem": plan.stem, "district": plan.district,
        "geometry_outcome": plan.geometry_outcome, "sidecar_present": True,
        "scheme_consistent": scheme_consistent, "zone_names_equal": zone_names_equal,
        "circulation_presence_equal": circulation_presence_equal,
        "storey_count_equal": storey_count_equal, "area_conservation_ok": area_conservation_ok,
        "idf_storey_count": plan.storey_count, "sidecar_storey_count": sidecar_storeys,
        "divergent": divergent, "divergence_notes": ";".join(notes),
    }


FIELDNAMES = [
    "building_id", "stem", "district", "geometry_outcome", "sidecar_present",
    "scheme_consistent", "zone_names_equal", "circulation_presence_equal",
    "storey_count_equal", "area_conservation_ok", "idf_storey_count",
    "sidecar_storey_count", "divergent", "divergence_notes",
]


def run_parity_gate(districts: list[str] | None = None, evidence_roots: dict[str, Path] | None = None) -> int:
    targets = districts if districts is not None else sorted(DISTRICTS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    any_divergent = False
    summary_lines = []
    for district in targets:
        root = (evidence_roots or {}).get(district, district_paths(district))
        plans = read_district(district, root)
        rows = [_row(plan, root) for plan in plans]
        out_path = OUT_DIR / f"parity_{district}.csv"
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        divergent_count = sum(1 for r in rows if r["divergent"])
        if divergent_count:
            any_divergent = True
        line = f"{district}: {len(rows)} buildings, {divergent_count} divergent -> {out_path}"
        print(line)
        summary_lines.append(line)

    summary_path = OUT_DIR / "parity_summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return 1 if any_divergent else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EU-18a T03 / EU-18b T12: the IDF/side-car/manifest parity gate.")
    parser.add_argument("--district", action="append", choices=sorted(DISTRICTS), default=None)
    parser.add_argument(
        "--evidence-root",
        action="append",
        default=None,
        help="DISTRICT=path override (T12: point at the EU-17 rebuild tree).",
    )
    args = parser.parse_args()

    roots = {}
    for entry in args.evidence_root or []:
        district, _, path = entry.partition("=")
        roots[district] = Path(path)

    sys.exit(run_parity_gate(args.district, roots or None))
