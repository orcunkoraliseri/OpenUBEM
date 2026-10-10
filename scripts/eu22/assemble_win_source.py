from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
MAX_WORKERS = 10
WINDOW_COLUMNS = [
    "district", "stem", "building_id", "archetype_id", "source_tree", "geometry_outcome", "share_target",
    "outdoor_wall_m2", "window_m2", "share_achieved", "walls_with_window", "walls_skipped", "skip_reasons",
    "u", "shgc", "fallback", "zones", "preflight_issues", "identity_ok", "idf_sha256", "error",
]
_BS = "BUILDINGSURFACE:DETAILED"
_FEN = "FENESTRATIONSURFACE:DETAILED"
TREE_RE = re.compile(r"^(?P<site>.+)_dw_(?P<date>\d{4}-\d{2}-\d{2})$")


def _load_idf(path: Path):
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF

    from scripts.run_eu_s2_campaign import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(path))


def _coords(surface):
    return [tuple(float(c) for c in p) for p in surface.coords]


def measure(idf) -> dict:
    from openubem.idf.european_windows import MIN_WINDOW_AREA_M2, is_convex, polygon_area

    outdoor = {}
    for s in idf.idfobjects[_BS]:
        if str(s.Surface_Type).strip().upper() == "WALL" and str(s.Outside_Boundary_Condition).strip().upper() == "OUTDOORS":
            outdoor[str(s.Name).strip().upper()] = _coords(s)
    wall_m2 = sum(polygon_area(p) if len(p) >= 3 else 0.0 for p in outdoor.values())
    window_m2 = 0.0
    hosted = set()
    host_ok = True
    for w in idf.idfobjects[_FEN]:
        pts = _coords(w)
        window_m2 += polygon_area(pts) if len(pts) >= 3 else 0.0
        host = str(w.Building_Surface_Name).strip().upper()
        hosted.add(host)
        if host not in outdoor:
            host_ok = False
    reasons: dict[str, int] = {}
    for name, pts in outdoor.items():
        if name in hosted:
            continue
        if len(pts) > 4:
            reason = "more_than_4_vertices"
        elif len(pts) < 3 or not is_convex(pts):
            reason = "not_convex"
        else:
            reason = "window_under_0.05_m2"
        reasons[reason] = reasons.get(reason, 0) + 1
    n_windows = len(idf.idfobjects[_FEN])
    return {
        "outdoor_wall_m2": wall_m2,
        "window_m2": window_m2,
        "share_achieved": window_m2 / wall_m2 if wall_m2 > 0.0 else 0.0,
        "walls_with_window": n_windows,
        "walls_skipped": sum(reasons.values()),
        "skip_reasons": json.dumps(reasons, sort_keys=True),
        "zones": len(idf.idfobjects["ZONE"]),
        "identity_ok": bool(host_ok and len(hosted) == n_windows),
        "min_window_area_m2": MIN_WINDOW_AREA_M2,
    }


def _process(task: tuple) -> dict:
    from openubem.idf.european_windows import window_record
    from scripts.run_eu_s2_campaign import ep_geometry_preflight

    site, tree, tree_dir, row = task
    stem = str(row["stem"])
    path = Path(tree_dir) / "idfs" / f"{stem}.idf"
    result = {
        "district": site, "stem": stem, "building_id": row["building_id"], "archetype_id": row["archetype_id"],
        "source_tree": tree, "geometry_outcome": row.get("geometry_outcome", ""),
    }
    try:
        if not path.exists():
            raise FileNotFoundError(f"{stem}.idf is not in idfs/")
        record = window_record(str(row["archetype_id"]))
        idf = _load_idf(path)
        m = measure(idf)
        m.pop("min_window_area_m2")
        result.update(m)
        result["share_target"] = float(record["share"])
        result["u"] = float(record["u"])
        result["shgc"] = float(record["shgc"])
        result["fallback"] = bool(record["fallback"])
        result["preflight_issues"] = len(ep_geometry_preflight(idf))
        result["idf_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        result["error"] = ""
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def assemble(site: str, tree: str, workers: int, evidence: Path = EVIDENCE) -> dict:
    match = TREE_RE.match(tree)
    if not match or match.group("site") != site:
        raise SystemExit(f"STOP: --tree must be {site}_dw_<YYYY-MM-DD>, got {tree}")
    date = match.group("date")
    tree_dir = evidence / tree
    prepared_path = tree_dir / "prepared_buildings.csv"
    if not prepared_path.exists():
        raise SystemExit(f"STOP: {prepared_path} is missing")
    prepared = pd.read_csv(prepared_path, dtype={"building_id": str, "stem": str})
    tasks = [(site, tree, str(tree_dir), r.to_dict()) for _, r in prepared.iterrows()]
    if workers > 1:
        with mp.Pool(min(workers, MAX_WORKERS)) as pool:
            rows = list(pool.imap(_process, tasks, chunksize=4))
    else:
        rows = [_process(t) for t in tasks]
    frame = pd.DataFrame(rows).reindex(columns=WINDOW_COLUMNS)
    frame.to_csv(tree_dir / "windows.csv", index=False)
    counts = pd.DataFrame({
        "building_id": prepared["building_id"],
        "old_count": prepared["dwellings_used"],
        "new_count": prepared["dwellings_used"],
        "dwellings_source": prepared["dwellings_source"],
    })
    counts.to_csv(tree_dir / f"dwelling_counts_{date}.csv", index=False)
    stems = sorted(p.stem for p in (tree_dir / "idfs").glob("*.idf"))
    (tree_dir / "changed_stems.txt").write_text("".join(f"{s}\n" for s in stems), encoding="utf-8")
    errors = int((frame["error"].fillna("") != "").sum())
    return {"rows": len(frame), "errors": errors, "stems": len(stems), "tree_dir": tree_dir}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--evidence-root")
    a = ap.parse_args(argv)
    from scripts.run_eu_s2_district_campaign import DISTRICTS

    if a.site not in DISTRICTS:
        raise SystemExit(f"STOP: unknown site {a.site}")
    evidence = Path(a.evidence_root) if a.evidence_root else EVIDENCE
    out = assemble(a.site, a.tree, a.workers, evidence)
    print(f"{a.site}: windows.csv {out['rows']} rows, errors {out['errors']}; changed_stems.txt {out['stems']} stems; {out['tree_dir']}")
    return 1 if out["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
