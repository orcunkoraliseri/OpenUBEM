from __future__ import annotations

import argparse
import hashlib
import itertools
import multiprocessing as mp
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
UNDIVIDED_CSV = EVIDENCE / "division_residual_2026-09-29" / "undivided_excluded_2026-10-01.csv"
DISTRICTS = [
    "ES-MAD-BERRUGUETE",
    "FR-LYO-HAUTCOEURPENTES",
    "GB-LDN-STDUNSTANS",
    "IT-BOL-GALVANI2",
]
HELD_FINDING_280 = {
    "d0787f31dc827e89",
    "b56bda9013da5b2d",
    "d342db5179c1ac49",
    "d32f27af52ecab2c",
    "a53d307eac631355",
}
OUT_SUFFIX = "_win_2026-10-01"
ADDED_TYPES = ("FENESTRATIONSURFACE:DETAILED", "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", "CONSTRUCTION")
MAX_WORKERS = 8


def _read_lst(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _tree(district: str, suffix: str) -> Path:
    return EVIDENCE / f"{district}{suffix}"


def _slug(district: str) -> str:
    return district.lower().replace("-", "_")


def universe(district: str) -> pd.DataFrame:
    recut = _tree(district, "_recut_2026-09-08")
    prepared = pd.read_csv(recut / "prepared_buildings.csv", dtype={"stem": str})
    undivided = pd.read_csv(UNDIVIDED_CSV, dtype={"stem": str})
    drop = set(undivided.loc[undivided["district"] == district, "stem"])
    prepared = prepared[~prepared["stem"].isin(drop)].copy()
    fix = _tree(district, "_fix_2026-10-01")
    t06g = _read_lst(fix / "shipped_t06g.lst")
    t06f = _read_lst(fix / "shipped_t06f.lst")
    fix_prepared = pd.read_csv(fix / "prepared_buildings.csv", dtype={"stem": str})
    fix_stems = set(fix_prepared["stem"])
    trees = []
    for stem in prepared["stem"]:
        if stem in t06g:
            trees.append(f"{district}_fix_2026-10-01_t06g")
        elif stem in t06f:
            trees.append(f"{district}_fix_2026-10-01_t06f")
        elif stem in HELD_FINDING_280:
            trees.append(f"{district}_recut_2026-09-08")
        elif stem in fix_stems:
            trees.append(f"{district}_fix_2026-10-01")
        else:
            trees.append(f"{district}_recut_2026-09-08")
    prepared["source_tree"] = trees
    return prepared.reset_index(drop=True)


def _load_idf(path: Path):
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from scripts.run_eu_s2_campaign import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(path))


def _object_rows(idf, types) -> list[list[str]]:
    rows = []
    for t in types:
        for obj in idf.idfobjects[t]:
            rows.append([t] + [str(v) for v in obj.obj[1:]])
    return rows


def _all_types(idf) -> list[str]:
    return sorted(idf.idfobjects.keys())


def _identity_ok(source_path: Path, out_path: Path, n_windows: int, n_added_materials: int) -> bool:
    source = _load_idf(source_path)
    out = _load_idf(out_path)
    window_names = {str(o.Name) for o in out.idfobjects["FENESTRATIONSURFACE:DETAILED"]}
    material_names = {"EU_Window_SimpleGlazing"}
    construction_names = {"EU_Window_Construction"}
    for obj in list(out.idfobjects["FENESTRATIONSURFACE:DETAILED"]):
        out.removeidfobject(obj)
    for obj in list(out.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"]):
        if str(obj.Name) in material_names:
            out.removeidfobject(obj)
    for obj in list(out.idfobjects["CONSTRUCTION"]):
        if str(obj.Name) in construction_names:
            out.removeidfobject(obj)
    types = sorted(set(_all_types(source)) | set(_all_types(out)))
    for t in types:
        a = [[str(v) for v in o.obj] for o in source.idfobjects[t]]
        b = [[str(v) for v in o.obj] for o in out.idfobjects[t]]
        if a != b:
            return False
    return len(window_names) == n_windows


def _process(task: tuple[str, dict, str]) -> dict:
    from scripts.run_eu_s2_campaign import ep_geometry_preflight
    from openubem.idf.european_windows import add_tabula_windows, window_record

    district, row, out_root = task
    stem = row["stem"]
    source_tree = EVIDENCE / row["source_tree"]
    out_dir = Path(out_root)
    source_idf = source_tree / "idfs" / f"{stem}.idf"
    out_idf = out_dir / "idfs" / f"{stem}.idf"
    result = {"district": district, "stem": stem, "building_id": row["building_id"], "archetype_id": row["archetype_id"], "source_tree": row["source_tree"], "geometry_outcome": row.get("geometry_outcome", "")}
    try:
        idf = _load_idf(source_idf)
        zones = [str(z.Name) for z in idf.idfobjects["ZONE"]]
        info = add_tabula_windows(idf, window_record(row["archetype_id"]))
        out_idf.parent.mkdir(parents=True, exist_ok=True)
        idf.saveas(str(out_idf))
        sched_src = source_tree / "schedules" / stem
        sched_dst = out_dir / "schedules" / stem
        if sched_src.is_dir():
            if sched_dst.exists():
                shutil.rmtree(sched_dst)
            shutil.copytree(sched_src, sched_dst)
        checked = _load_idf(out_idf)
        result.update(info)
        result["zones"] = len(zones)
        result["preflight_issues"] = len(ep_geometry_preflight(checked))
        result["identity_ok"] = _identity_ok(source_idf, out_idf, info["walls_with_window"], 1)
        result["idf_sha256"] = hashlib.sha256(out_idf.read_bytes()).hexdigest()
        result["error"] = ""
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def _interleave(per_district: dict[str, list[tuple]]) -> list[tuple]:
    out = []
    for group in itertools.zip_longest(*per_district.values()):
        out.extend(t for t in group if t is not None)
    return out


def run(districts: list[str], workers: int) -> None:
    per_district: dict[str, list[tuple]] = {}
    frames: dict[str, pd.DataFrame] = {}
    for district in districts:
        frames[district] = universe(district)
        out_root = _tree(district, OUT_SUFFIX)
        (out_root / "idfs").mkdir(parents=True, exist_ok=True)
        (out_root / "schedules").mkdir(parents=True, exist_ok=True)
        weather_src = _tree(district, "_fix_2026-10-01") / "weather"
        weather_dst = out_root / "weather"
        if not weather_dst.exists():
            shutil.copytree(weather_src, weather_dst)
        per_district[district] = [
            (district, r.to_dict(), str(out_root)) for _, r in frames[district].iterrows()
        ]
    tasks = _interleave(per_district)
    with mp.Pool(min(workers, MAX_WORKERS)) as pool:
        results = list(pool.imap_unordered(_process, tasks, chunksize=4))
    for district in districts:
        out_root = _tree(district, OUT_SUFFIX)
        rows = pd.DataFrame([r for r in results if r["district"] == district])
        rows.to_csv(out_root / "windows.csv", index=False)
        ok = rows[rows["error"] == ""]
        prepared = frames[district].merge(
            ok[["stem", "idf_sha256"]].rename(columns={"idf_sha256": "idf_sha256_win"}), on="stem", how="inner"
        )
        prepared["idf_sha256"] = prepared["idf_sha256_win"]
        prepared = prepared.drop(columns=["idf_sha256_win"])
        prepared.to_csv(out_root / "prepared_buildings.csv", index=False)
        manifest = pd.read_csv(
            _tree(district, "_merged_2026-09-08") / f"{_slug(district)}_manifest.csv",
            usecols=["building_id", "run_seconds"],
        )
        seconds = dict(zip(manifest["building_id"], manifest["run_seconds"]))
        prepared["run_seconds_0908"] = prepared["building_id"].map(seconds)
        known = prepared[prepared["run_seconds_0908"].notna()].sort_values("run_seconds_0908", ascending=False)
        unknown = prepared[prepared["run_seconds_0908"].isna()].sort_values("floor_area_m2", ascending=False)
        order = list(known["stem"]) + list(unknown["stem"])
        (out_root / "fleet.lst").write_text("\n".join(order) + "\n", encoding="utf-8")
        print(f"{district}: written {len(ok)} of {len(frames[district])}, errors {len(rows) - len(ok)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--district", choices=DISTRICTS)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()
    run(DISTRICTS if args.all else [args.district], args.workers)


if __name__ == "__main__":
    main()
