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
DISTRICTS = [
    "ES-MAD-BERRUGUETE",
    "FR-LYO-HAUTCOEURPENTES",
    "GB-LDN-STDUNSTANS",
    "IT-BOL-GALVANI2",
]
SRC_SUFFIX = "_win_2026-10-01"
OUT_SUFFIX = "_win_2026-10-03"
COPY_FILES = ("fleet.lst", "prepared_buildings.csv", "windows.csv")
COPY_DIRS = ("schedules", "weather")
MAX_WORKERS = 8
TYPES = ("FLOOR", "WALL", "CEILING", "ROOF")


def _load_idf(path: Path):
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from scripts.run_eu_s2_campaign import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(path))


def _signature(idf) -> dict:
    out = {}
    for kind in ("BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED"):
        for s in idf.idfobjects[kind]:
            pts = [tuple(round(float(c), 6) for c in p) for p in s.coords]
            out[(kind, str(s.Name))] = frozenset(pts)
    return out


def _area(coords) -> float:
    ax = ay = az = 0.0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        ax += coords[i][1] * coords[j][2] - coords[i][2] * coords[j][1]
        ay += coords[i][2] * coords[j][0] - coords[i][0] * coords[j][2]
        az += coords[i][0] * coords[j][1] - coords[i][1] * coords[j][0]
    return 0.5 * (ax * ax + ay * ay + az * az) ** 0.5


def _area_map(idf) -> dict:
    out = {}
    for kind in ("BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED"):
        for s in idf.idfobjects[kind]:
            out[(kind, str(s.Name))] = _area([tuple(float(c) for c in p) for p in s.coords])
    return out


def _process(task: tuple[str, str, str]) -> dict:
    from openubem.idf.surface_orientation import (
        measure_outdoor_walls,
        normalise_surface_orientation,
    )

    district, stem, out_root = task
    src = EVIDENCE / f"{district}{SRC_SUFFIX}" / "idfs" / f"{stem}.idf"
    dst = Path(out_root) / "idfs" / f"{stem}.idf"
    row = {"district": district, "stem": stem, "error": ""}
    try:
        idf = _load_idf(src)
        before_sig = _signature(idf)
        before_area = _area_map(idf)
        res = normalise_surface_orientation(idf)
        dst.parent.mkdir(parents=True, exist_ok=True)
        idf.saveas(str(dst))
        checked = _load_idf(dst)
        after_sig = _signature(checked)
        after_area = _area_map(checked)
        row["geometry_ok"] = before_sig == after_sig and all(
            abs(before_area[k] - after_area[k]) < 1e-6 for k in before_area
        ) and before_area.keys() == after_area.keys()
        for t in TYPES:
            for key in ("reversed", "kept", "fallback"):
                row[f"{t.lower()}_{key}"] = res[t][key]
        row["walls_vote"] = res["wall_how"].get("vote", 0)
        row["walls_edge"] = res["wall_how"].get("edge", 0)
        row["walls_fallback"] = sum(v for k, v in res["wall_how"].items() if k not in ("vote", "edge"))
        row["other"] = res["other"]
        row["windows_reversed"] = res["windows_reversed"]
        row["windows_kept"] = res["windows_kept"]
        row["interzone_pairs"] = res["interzone_pairs"]
        row["interzone_opposite"] = res["interzone_opposite"]
        row["pair_rule1"] = res["pair_rule1"]
        row["pair_rule2"] = res["pair_rule2"]
        row["pair_rule3"] = len(res["pair_rule3"])
        row["pair_rule4"] = res["pair_rule4"]
        row["interzone_bad"] = ";".join(f"{a}|{b}" for a, b in res["interzone_bad"])
        m = measure_outdoor_walls(checked)
        row["wall_inward"] = m["inward"]
        row["wall_outward"] = m["outward"]
        row["wall_unclear"] = m["unclear"]
        row["idf_sha256"] = hashlib.sha256(dst.read_bytes()).hexdigest()
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def _interleave(per_district: dict[str, list[tuple]]) -> list[tuple]:
    out = []
    for group in itertools.zip_longest(*per_district.values()):
        out.extend(t for t in group if t is not None)
    return out


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def run(districts: list[str], workers: int) -> int:
    per_district: dict[str, list[tuple]] = {}
    stems: dict[str, list[str]] = {}
    for district in districts:
        src_root = EVIDENCE / f"{district}{SRC_SUFFIX}"
        out_root = EVIDENCE / f"{district}{OUT_SUFFIX}"
        (out_root / "idfs").mkdir(parents=True, exist_ok=True)
        for name in COPY_FILES:
            shutil.copy2(src_root / name, out_root / name)
        for name in COPY_DIRS:
            dst = out_root / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src_root / name, dst)
        stems[district] = sorted(p.stem for p in (src_root / "idfs").glob("*.idf"))
        per_district[district] = [(district, s, str(out_root)) for s in stems[district]]
    tasks = _interleave(per_district)
    with mp.Pool(min(workers, MAX_WORKERS)) as pool:
        results = list(pool.imap_unordered(_process, tasks, chunksize=4))
    problems = 0
    for district in districts:
        out_root = EVIDENCE / f"{district}{OUT_SUFFIX}"
        frame = pd.DataFrame([r for r in results if r["district"] == district]).sort_values("stem")
        frame.to_csv(out_root / "orientation.csv", index=False)
        ok = frame[frame["error"] == ""]
        n_bad_geo = int((~ok["geometry_ok"].astype(bool)).sum())
        pairs = int(ok["interzone_pairs"].sum())
        opp = int(ok["interzone_opposite"].sum())
        rev = {t.lower(): int(ok[f"{t.lower()}_reversed"].sum()) for t in TYPES}
        fb = int(ok["wall_fallback"].sum())
        problems += (len(frame) - len(ok)) + n_bad_geo + (pairs - opp)
        print(
            f"{district}: homes written {len(ok)} of {len(stems[district])}; reversed {rev}; "
            f"walls vote {int(ok['walls_vote'].sum())} edge {int(ok['walls_edge'].sum())} fallback {int(ok['walls_fallback'].sum())}; windows reversed {int(ok['windows_reversed'].sum())}; "
            f"pair rule1 {int(ok['pair_rule1'].sum())} rule2 {int(ok['pair_rule2'].sum())} rule3 {int(ok['pair_rule3'].sum())} rule4 {int(ok['pair_rule4'].sum())}; "
            f"interzone opposite {opp} of {pairs}; geometry changed {n_bad_geo}; "
            f"re-measure inward {int(ok['wall_inward'].sum())} outward {int(ok['wall_outward'].sum())} "
            f"unclear {int(ok['wall_unclear'].sum())}; windows.csv md5 {_md5(out_root / 'windows.csv')}"
        )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--district", choices=DISTRICTS)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()
    problems = run(DISTRICTS if args.all else [args.district], args.workers)
    if problems:
        print(f"STOP: {problems} problem(s); see orientation.csv")
        sys.exit(1)


if __name__ == "__main__":
    main()
