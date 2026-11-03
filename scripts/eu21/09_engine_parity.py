"""EU-21 engine-vs-`_r5` parity harness (D-EU-54, D-EU-95, T02): replays
`openubem.geometry.european_nocore.cut_storey_nocore` over every `status == "direct"`
plate in the four accepted `_r5` JSONs and proves it reproduces them exactly --
verdict, flat count, all seven checks (pass and show, string-for-string), and flat
geometry (union symmetric-difference and per-flat area). Never edits
`07_nocore_tests.py`/`01`-`06`/`08` or the four `_r5` JSONs -- read-only inputs
(D-EU-85). The gate is 0 mismatches of all four kinds on all four districts.

Frame note (director ruling, 2026-09-03): the `_r5` JSONs store geometry in the
CENTRED frame (`08_district_viewer.py:180`, `p = M07.centred(usable)`).
`cut_storey_nocore` always returns geometry in the frame of its own `footprint`
argument (translated back by `(+cx, +cy)` as its last step, D-EU-95 step 7) -- for
this harness that argument IS the stored (already-centred) footprint, so the engine's
return value is one extra `(+cx, +cy)` away from the frame the checks/geometry were
stored in. The harness undoes exactly that -- translates the engine's own output back
by `(-cx, -cy)`, the same centroid `cut_storey_nocore` used internally -- before
comparing geometry. The `_r5` JSONs themselves are never touched.
"""
import argparse
import concurrent.futures as cf
import importlib.util as ilu
import json
import pathlib

from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.wkb import loads as wkb_loads

from openubem.geometry.european_nocore import cut_storey_nocore, usable_polygon

ROOT = pathlib.Path(__file__).resolve().parents[2]
DISTRICT_PLANS = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "district_plans"
OUT_DIR = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "engine_parity"
CUTTER_PATH = ROOT / "scripts" / "eu21" / "07_nocore_tests.py"


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DISTRICT_NAMES = [
    "ES-MAD-BERRUGUETE",
    "FR-LYO-HAUTCOEURPENTES",
    "GB-LDN-STDUNSTANS",
    "IT-BOL-GALVANI2",
]


def _district_files(baseline_tag):
    return [f"{name}_nocore_{baseline_tag}.json" for name in DISTRICT_NAMES]


CHECK_IDS = ("C1", "C3", "C4", "C5", "C6", "C10", "C11")
GEOM_TOLERANCE_M2 = 1e-6


def _poly_from_rings(rings):
    return Polygon(rings[0], rings[1:])


def _check_one_plate(plate, geom_wkb):
    building_id = plate["building_id"]
    poly = wkb_loads(geom_wkb)
    k = plate["drawn_per_floor"]
    usable = usable_polygon(poly)
    cx, cy = (usable.centroid.x, usable.centroid.y) if usable is not None else (0.0, 0.0)
    try:
        out_poly, live, checks, verdict = cut_storey_nocore(poly, k)
    except Exception as exc:
        return {"building_id": building_id, "kind": "verdict", "field": "exception",
                "expected": plate["verdict"], "got": f"{type(exc).__name__}: {exc}"[:200]}

    # cut_storey_nocore returns geometry in the frame of `poly` (translated back by
    # (+cx, +cy) as its last step, D-EU-95 step 7) -- undo exactly that so the
    # comparison below runs in the same centred frame the `_r5` geometry was stored
    # in (director ruling, 2026-09-03).
    out_poly = translate(out_poly, -cx, -cy)
    live = [translate(f, -cx, -cy) for f in live]

    if verdict != plate["verdict"]:
        return {"building_id": building_id, "kind": "verdict", "field": "verdict",
                "expected": plate["verdict"], "got": verdict}

    if len(live) != len(plate["dwellings"]):
        return {"building_id": building_id, "kind": "count", "field": "flat_count",
                "expected": len(plate["dwellings"]), "got": len(live)}

    for c in CHECK_IDS:
        stored = plate["checks"][c]
        got = checks[c]
        if got["pass"] != stored["pass"] or got["show"] != stored["show"]:
            return {"building_id": building_id, "kind": "check", "field": c,
                    "expected": stored, "got": got}

    stored_flats = [_poly_from_rings(rings) for rings in plate["dwellings"]]
    union_stored = unary_union(stored_flats)
    union_produced = unary_union(list(live))
    sym_diff_area = union_stored.symmetric_difference(union_produced).area
    if sym_diff_area > GEOM_TOLERANCE_M2:
        return {"building_id": building_id, "kind": "geometry", "field": "union_symmetric_difference",
                "expected": 0.0, "got": sym_diff_area}

    remaining = list(stored_flats)
    for f in live:
        rp = f.representative_point()
        match_idx = next((i for i, sf in enumerate(remaining) if sf is not None and sf.contains(rp)), None)
        if match_idx is None:
            match_idx = next((i for i, sf in enumerate(remaining) if sf is not None), None)
        if match_idx is None:
            return {"building_id": building_id, "kind": "geometry", "field": "unmatched_flat",
                     "expected": "match", "got": "none"}
        sf = remaining[match_idx]
        remaining[match_idx] = None
        if abs(f.area - sf.area) > GEOM_TOLERANCE_M2:
            return {"building_id": building_id, "kind": "geometry", "field": "flat_area",
                     "expected": sf.area, "got": f.area}

    return None


def _check_task(task):
    district, plate, geom_wkb = task
    return district, _check_one_plate(plate, geom_wkb)


def _load_all(baseline_tag):
    per_district = {}
    for fname in _district_files(baseline_tag):
        data = json.load(open(DISTRICT_PLANS / fname, encoding="utf-8"))
        per_district[data["district"]] = data
    return per_district


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--baseline-tag", default="2026-09-03_r5")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    per_district = _load_all(args.baseline_tag)

    # Census input, loaded once in the parent process (T02 correction, 2026-09-03):
    # `plate["footprint"]` is the cutter's rounded *output*, not the census's real
    # input. `geoms` is passed to worker processes as WKB, never reloaded per worker.
    M07 = _load_module("eu21_m09_m07_nocore_tests", str(CUTTER_PATH))
    geoms, *_ = M07.load_universe()

    tasks = []
    status_counts_by_district = {}
    input_missing_by_district = {d: 0 for d in per_district}
    for district, data in per_district.items():
        counts = {}
        for p in data["plates"]:
            counts[p["status"]] = counts.get(p["status"], 0) + 1
            if p["status"] == "direct":
                g = geoms.get((district, p["building_id"]))
                if g is None:
                    input_missing_by_district[district] += 1
                    continue
                tasks.append((district, p, g.wkb))
        status_counts_by_district[district] = counts
        expected = data["summary"]["status_counts"]
        if counts != expected:
            raise AssertionError(f"{district}: status_counts {counts} != summary {expected}")

    mismatches_by_district = {d: {"verdict": [], "count": [], "check": [], "geometry": []} for d in per_district}
    compared_by_district = {d: 0 for d in per_district}
    for district, _plate, _wkb in tasks:
        compared_by_district[district] += 1

    if args.jobs > 1:
        with cf.ProcessPoolExecutor(max_workers=args.jobs) as ex:
            for district, result in ex.map(_check_task, tasks, chunksize=4):
                if result is not None:
                    mismatches_by_district[district][result["kind"]].append(result)
    else:
        for t in tasks:
            district, result = _check_task(t)
            if result is not None:
                mismatches_by_district[district][result["kind"]].append(result)

    fleet = {"compared": 0, "verdict": 0, "count": 0, "check": 0, "geometry": 0, "input_missing": 0}
    for district, data in per_district.items():
        compared_count = compared_by_district[district]
        input_missing = input_missing_by_district[district]
        mism = mismatches_by_district[district]
        first20 = (mism["verdict"] + mism["count"] + mism["check"] + mism["geometry"])[:20]
        report = {
            "district": district,
            "plates_compared": compared_count,
            "input_missing": input_missing,
            "status_counts": status_counts_by_district[district],
            "verdict_mismatches": len(mism["verdict"]),
            "count_mismatches": len(mism["count"]),
            "check_mismatches": len(mism["check"]),
            "geometry_mismatches": len(mism["geometry"]),
            "first_20_mismatches": first20,
        }
        out_path = OUT_DIR / f"parity_{district}_2026-09-03.json"
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        fleet["compared"] += compared_count
        fleet["input_missing"] += input_missing
        fleet["verdict"] += len(mism["verdict"])
        fleet["count"] += len(mism["count"])
        fleet["check"] += len(mism["check"])
        fleet["geometry"] += len(mism["geometry"])

        print(f"{district}: compared {compared_count} · mismatches "
              f"{len(mism['verdict'])}/{len(mism['count'])}/{len(mism['check'])}/{len(mism['geometry'])}")
        print(f"{district}: input_missing {input_missing}")

    print(f"compared {fleet['compared']} · mismatches "
          f"{fleet['verdict']}/{fleet['count']}/{fleet['check']}/{fleet['geometry']}")
    print(f"fleet: input_missing {fleet['input_missing']}")


if __name__ == "__main__":
    main()
