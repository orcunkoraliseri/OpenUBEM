from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import multiprocessing as mp
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
DISTRICTS = {
    "ES": "ES-MAD-BERRUGUETE",
    "FR": "FR-LYO-HAUTCOEURPENTES",
    "GB": "GB-LDN-STDUNSTANS",
    "IT": "IT-BOL-GALVANI2",
    "AT": "AT-VIE-RUDOLFSHEIM",
    "KR": "KR-SEO-MAPO",
    "CA": "CA-MTL-PLATEAU",
    "FI": "FI-HEL-KALLIO",
    "ZA": "ZA-CPT-WOODSTOCK",
    "HU": "HU-BUD-ERZSEBETVAROS",
    "AM": "AM-EVN-NORNORK",
}
CRS = {
    "FR": "EPSG:32631",
    "IT": "EPSG:32632",
    "AT": "EPSG:32633",
    "KR": "EPSG:32652",
    "CA": "EPSG:32618",
    "FI": "EPSG:32635",
    "ZA": "EPSG:32734",
    "HU": "EPSG:32634",
    "AM": "EPSG:32638",
}
MAX_WORKERS = 8
MAX_SLIVER_M2 = 0.2
COPY_FILES = ("prepared_buildings.csv", "windows.csv")
COPY_DIRS = ("schedules", "weather")
_BS = "BUILDINGSURFACE:DETAILED"
_FEN = "FENESTRATIONSURFACE:DETAILED"


def _tag(tree: str) -> str:
    return tree.replace("_win_", "").replace("_dw_", "")


def _load_idf(path: Path):
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from scripts.run_eu_s2_campaign import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(path))


def _newell(pts):
    o = pts[0]
    q = [(p[0] - o[0], p[1] - o[1], p[2] - o[2]) for p in pts]
    ax = ay = az = 0.0
    n = len(q)
    for i in range(n):
        a = q[i]
        b = q[(i + 1) % n]
        ax += a[1] * b[2] - a[2] * b[1]
        ay += a[2] * b[0] - a[0] * b[2]
        az += a[0] * b[1] - a[1] * b[0]
    return ax, ay, az


def _coords(s):
    return [tuple(float(c) for c in p) for p in s.coords]


def _metrics(idf) -> dict:
    out = {"wall_outdoor_m2": 0.0, "window_m2": 0.0, "floor_m2": 0.0}
    for s in idf.idfobjects[_BS]:
        t = str(s.Surface_Type).strip().upper()
        pts = _coords(s)
        if len(pts) < 3:
            continue
        area = 0.5 * sum(c * c for c in _newell(pts)) ** 0.5
        if t == "WALL" and str(s.Outside_Boundary_Condition).strip().upper() == "OUTDOORS":
            out["wall_outdoor_m2"] += area
        elif t == "FLOOR":
            out["floor_m2"] += area
    for w in idf.idfobjects[_FEN]:
        pts = _coords(w)
        if len(pts) >= 3:
            out["window_m2"] += 0.5 * sum(c * c for c in _newell(pts)) ** 0.5
    return out


def _orientation(idf) -> dict:
    from openubem.idf.surface_orientation import check_interzone_pairs, measure_outdoor_walls

    m = measure_outdoor_walls(idf)
    p = check_interzone_pairs(idf)
    floors_up = tops_down = 0
    hosts = {}
    for s in idf.idfobjects[_BS]:
        t = str(s.Surface_Type).strip().upper()
        pts = _coords(s)
        if len(pts) < 3:
            continue
        n = _newell(pts)
        hosts[str(s.Name).strip().upper()] = n
        if t == "FLOOR" and n[2] > 0:
            floors_up += 1
        elif t in ("ROOF", "CEILING") and n[2] < 0:
            tops_down += 1
    win_bad = 0
    for w in idf.idfobjects[_FEN]:
        pts = _coords(w)
        h = hosts.get(str(w.Building_Surface_Name).strip().upper())
        if len(pts) < 3 or h is None:
            continue
        n = _newell(pts)
        if n[0] * h[0] + n[1] * h[1] + n[2] * h[2] <= 0:
            win_bad += 1
    return {
        "wall_inward": m["inward"],
        "wall_outward": m["outward"],
        "wall_unclear": m["unclear"],
        "pairs": p["interzone_pairs"],
        "pairs_opposite": p["interzone_opposite"],
        "floors_up": floors_up,
        "tops_down": tops_down,
        "windows_not_with_wall": win_bad,
    }


def _process(task: tuple) -> dict:
    from openubem.idf.degenerate_surfaces import drop_degenerate_surfaces
    from openubem.idf.local_origin import shift_to_local_origin

    district, stem, source_tree, target_tree, offset = task
    src = EVIDENCE / f"{district}{source_tree}" / "idfs" / f"{stem}.idf"
    dst = EVIDENCE / f"{district}{target_tree}" / "idfs" / f"{stem}.idf"
    row = {
        "district": district,
        "stem": stem,
        "n_deleted": 0,
        "total_area_m2": 0.0,
        "largest_area_m2": 0.0,
        "names": "",
        "kinds": "",
        "boundary_types": "",
        "partner_not_degenerate": 0,
        "events_before": 0,
        "oversize": "",
        "shifted": offset is not None,
        "shift_area_max_diff": 0.0,
        "events_after": 0,
        "error": "",
    }
    try:
        idf = _load_idf(src)
        if offset is not None:
            before = _metrics(idf)
            idf = shift_to_local_origin(idf, offset[0], offset[1])
            after = _metrics(idf)
            row["shift_area_max_diff"] = max(abs(before[k] - after[k]) for k in before)
        probe = drop_degenerate_surfaces(idf, apply=False)
        row["events_before"] = probe["n_events_total"]
        flagged = [r for r in probe["surfaces"] if r["deleted"] == "y"]
        big = [r for r in flagged if r["area_m2"] > MAX_SLIVER_M2]
        apply = bool(flagged) and not big
        if big:
            row["oversize"] = ";".join(f"{r['name']}={r['area_m2']:.4f}" for r in big)
        report = drop_degenerate_surfaces(idf, apply=apply)
        deleted = [r for r in report["surfaces"] if r["deleted"] == "y"] if apply else []
        row["n_deleted"] = report["n_deleted"] if apply else 0
        row["total_area_m2"] = sum(r["area_m2"] for r in deleted)
        row["largest_area_m2"] = max((r["area_m2"] for r in deleted), default=0.0)
        row["names"] = ";".join(r["name"] for r in deleted)
        row["kinds"] = ";".join(sorted({r["kind"] for r in deleted}))
        row["boundary_types"] = ";".join(sorted({r["boundary"] for r in deleted}))
        row["partner_not_degenerate"] = len(report["partner_not_degenerate"])
        if offset is not None or (apply and row["n_deleted"]):
            idf.saveas(str(dst))
        else:
            shutil.copy2(src, dst)
        final = _load_idf(dst)
        check = drop_degenerate_surfaces(final, apply=False)
        row["events_after"] = check["n_events_total"]
        row.update(_orientation(final))
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def _interleave(per_district: dict[str, list[tuple]]) -> list[tuple]:
    out = []
    for group in itertools.zip_longest(*per_district.values()):
        out.extend(t for t in group if t is not None)
    return out


def _read_reasons(path: Path) -> dict[str, str]:
    reasons = {}
    if not path.exists():
        return reasons
    for line in path.read_text().splitlines():
        parts = line.strip().split("\t")
        if parts and parts[0]:
            reasons[parts[0]] = parts[1] if len(parts) > 1 else "flat_count"
    return reasons


def _join(parts: list[str]) -> str:
    order = ["flat_count", "degenerate", "origin_shift"]
    flat = {p for part in parts for p in part.split("+") if p}
    return "+".join(p for p in order if p in flat)


def _offsets(codes: list[str], source_tree: str, shift: set[str]) -> dict[str, tuple[float, float]]:
    from openubem.idf.local_origin import offset_from_min, scan_min_xy

    out = {}
    for code in codes:
        if code not in shift:
            continue
        idfs = sorted((EVIDENCE / f"{DISTRICTS[code]}{source_tree}" / "idfs").glob("*.idf"))
        with mp.Pool(MAX_WORKERS) as pool:
            mins = pool.map(scan_min_xy, idfs, chunksize=16)
        out[code] = offset_from_min(min(m[0] for m in mins), min(m[1] for m in mins))
    return out


def run(codes: list[str], source_tree: str, target_tree: str, shift: set[str], workers: int) -> int:
    tag = _tag(target_tree)
    offsets = _offsets(codes, source_tree, shift)
    per_district: dict[str, list[tuple]] = {}
    for code in codes:
        district = DISTRICTS[code]
        src_root = EVIDENCE / f"{district}{source_tree}"
        dst_root = EVIDENCE / f"{district}{target_tree}"
        (dst_root / "idfs").mkdir(parents=True, exist_ok=True)
        for name in COPY_FILES:
            shutil.copy2(src_root / name, dst_root / name)
        for name in COPY_DIRS:
            target = dst_root / name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(src_root / name, target)
        shutil.copy2(
            src_root / f"dwelling_counts_{_tag(source_tree)}.csv",
            dst_root / f"dwelling_counts_{tag}.csv",
        )
        if code in offsets:
            dx, dy = offsets[code]
            (dst_root / "origin_offset.json").write_text(
                json.dumps(
                    {
                        "dx": dx,
                        "dy": dy,
                        "crs": CRS[code],
                        "applies_to": "every IDF",
                        "source_tree": source_tree,
                    },
                    indent=2,
                )
            )
        per_district[district] = [
            (district, p.stem, source_tree, target_tree, offsets.get(code))
            for p in sorted((src_root / "idfs").glob("*.idf"))
        ]
    with mp.Pool(min(workers, MAX_WORKERS)) as pool:
        results = list(pool.imap_unordered(_process, _interleave(per_district), chunksize=4))
    problems = 0
    for code in codes:
        district = DISTRICTS[code]
        src_root = EVIDENCE / f"{district}{source_tree}"
        dst_root = EVIDENCE / f"{district}{target_tree}"
        frame = pd.DataFrame([r for r in results if r["district"] == district]).sort_values("stem")
        frame.drop(columns=["district"]).to_csv(dst_root / f"degenerate_{tag}.csv", index=False)
        reasons = _read_reasons(src_root / "changed_stems.txt")
        for _, r in frame.iterrows():
            parts = [reasons[r["stem"]]] if r["stem"] in reasons else []
            if r["n_deleted"] > 0:
                parts.append("degenerate")
            if code in offsets:
                parts.append("origin_shift")
            if parts:
                reasons[r["stem"]] = _join(parts)
        stems = sorted(reasons)
        (dst_root / "changed_stems.txt").write_text("".join(f"{s}\t{reasons[s]}\n" for s in stems))
        (dst_root / "fleet.lst").write_text("".join(f"{s}\n" for s in stems))
        lines = []
        for p in sorted((dst_root / "idfs").glob("*.idf")):
            lines.append(f"{hashlib.md5(p.read_bytes()).hexdigest()}  {p.name}\n")
        (dst_root / f"md5_{tag}.txt").write_text("".join(lines))
        errors = int((frame["error"] != "").sum())
        oversize = int((frame["oversize"] != "").sum())
        problems += errors + oversize
        print(
            f"{code}: IDFs {len(frame)}; changed {int((frame['n_deleted'] > 0).sum())}; "
            f"deleted {int(frame['n_deleted'].sum())}; events before {int(frame['events_before'].sum())}; "
            f"events after {int(frame['events_after'].sum())}; area {frame['total_area_m2'].sum():.6f} m2; "
            f"largest {frame['largest_area_m2'].max():.6f} m2; oversize {oversize}; "
            f"partner_not_degenerate {int(frame['partner_not_degenerate'].sum())}; "
            f"shift max area diff {frame['shift_area_max_diff'].max():.3e}; errors {errors}"
        )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--districts", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--target-tree", required=True)
    parser.add_argument("--shift", default="")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()
    if args.source_tree == args.target_tree:
        sys.exit("STOP: source and target trees must differ")
    if args.target_tree in ("_win_2026-10-03", "_win_2026-10-04"):
        sys.exit("STOP: never write into a 10-03 or 10-04 tree")
    codes = [c.strip().upper() for c in args.districts.split(",")]
    shift = {c.strip().upper() for c in args.shift.split(",") if c.strip()}
    problems = run(codes, args.source_tree, args.target_tree, shift, args.workers)
    if problems:
        print(f"STOP: {problems} problem(s); see degenerate_{_tag(args.target_tree)}.csv")
        sys.exit(1)


if __name__ == "__main__":
    main()
