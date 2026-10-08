from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import tempfile
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

CAUSES = REPO / "openubem" / "outputs" / "comparisons" / "open38_fatal_causes_2026-08-20.csv"
EVIDENCE = REPO / "evidence" / "open48_refleet"
WORK = Path(tempfile.gettempdir()) / "ubem_validation" / "open38_rerun_2026-09-29"
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_DIR = "/speed-scratch/o_iseri/openubem/fleets/open38_rerun_2026-09-29"
REMOTE_WEATHER_SRC = "/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/weather"
REMOTE_SBATCH = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t07.sbatch"


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr


def case_name(cell: str, mode: str, stem: str) -> str:
    return f"{mode}__{cell}__{stem}"


def build_cell(cell: str) -> list[dict]:
    import geopandas as gpd
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition.epw_manager import load_stations, resolve_station
    from openubem.idf.builder import BuildingIDF
    from openubem.semantic import enrich_semantics
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from scripts.validation.v12_cell_pipeline import CELL_CONFIGS

    causes = pd.read_csv(CAUSES)
    targets = causes[causes["cell"] == cell]
    cfg = CELL_CONFIGS[cell]
    station, _ = resolve_station(cfg["lat"], cfg["lon"], load_stations())
    sid = str(station["station_id"])

    gdf_raw = gpd.read_file(str(EVIDENCE / cell / "01_buildings.gpkg"))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    gdf_26 = BuildingClassifier().classify(gdf_in)
    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values,
                                            categories=list(_CLIMATE_ZONE_VOCAB))
    local_epw = [e for e in (WORK / "weather").glob("*.epw") if f".{sid}_" in e.name]
    assert len(local_epw) == 1, (sid, local_epw)
    gdf_29["epw_path"] = str(local_epw[0])
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"])
    gdf_57, lib = enrich_semantics(gdf_29)

    rows = []
    for _, t in targets.iterrows():
        osm_id = t["stem"].replace("_", "/", 1)
        sub = gdf_57[gdf_57["osm_id"].astype(str) == osm_id]
        if sub.empty:
            rows.append(dict(cell=cell, mode=t["mode"], stem=t["stem"], station_id=sid,
                             generation_status="not_in_fixture", idf_path=""))
            continue
        outdir = WORK / cell / t["mode"]
        (outdir / "idfs").mkdir(parents=True, exist_ok=True)
        try:
            m = BuildingIDF(sub.iloc[0], resolution_mode=t["mode"], trim_outputs=True).build(gdf_57, lib, outdir)
        except Exception as e:
            m = {"generation_status": f"exception:{type(e).__name__}:{e}"[:200], "idf_path": ""}
        rows.append(dict(cell=cell, mode=t["mode"], stem=t["stem"], station_id=sid,
                         generation_status=str(m.get("generation_status")),
                         idf_path=str(m.get("idf_path", ""))))
    return rows


def main() -> None:
    causes = pd.read_csv(CAUSES)
    cells = sorted(causes["cell"].unique())
    with Pool(min(len(cells), 5)) as p:
        res = p.map(build_cell, cells)
    df = pd.DataFrame([r for rs in res for r in rs])
    WORK.mkdir(parents=True, exist_ok=True)
    df.to_csv(WORK / "build_manifest.csv", index=False)
    print(df.groupby(["cell", "mode", "generation_status"]).size().to_string())
    ok = df[df["generation_status"] == "success"]
    print(f"BUILT {len(ok)} of {len(df)}")
    if len(ok) == 0:
        raise SystemExit("STOP: nothing built")

    remote_ls = _ssh(f"ls {REMOTE_WEATHER_SRC}")
    epws = [l.strip() for l in remote_ls.splitlines() if l.strip().endswith(".epw")]
    lines, tarpath = [], WORK / "fleet.tar.gz"
    needed = set()
    with tarfile.open(tarpath, "w:gz") as tf:
        for _, r in ok.iterrows():
            m = [e for e in epws if f".{r['station_id']}_" in e]
            if len(m) != 1:
                raise SystemExit(f"STOP: EPW for station {r['station_id']} matches {m}")
            needed.add(m[0])
            name = case_name(r["cell"], r["mode"], r["stem"])
            tf.add(r["idf_path"], arcname=f"idfs/{name}.idf")
            lines.append(f"{name}\t{m[0]}")
        b = ("\n".join(lines) + "\n").encode()
        info = tarfile.TarInfo("fleet.lst")
        info.size = len(b)
        tf.addfile(info, io.BytesIO(b))
    (WORK / "fleet.lst").write_text("\n".join(lines) + "\n")
    n = len(lines)
    print(f"cases={n} width=32 epws={sorted(needed)}")
    print(_ssh(f"mkdir -p {REMOTE_DIR}/weather {REMOTE_DIR}/out"))
    for e in sorted(needed):
        print(_ssh(f"cp {REMOTE_WEATHER_SRC}/{e} {REMOTE_DIR}/weather/"))
    r = subprocess.run(["scp", str(tarpath), f"{REMOTE_HOST}:{REMOTE_DIR}/fleet.tar.gz"],
                       capture_output=True, text=True, timeout=1800)
    if r.returncode:
        raise SystemExit(f"STOP: scp {r.stderr}")
    print(_ssh(f"cd {REMOTE_DIR} && tar -xzf fleet.tar.gz && echo IDF=$(ls idfs | wc -l) "
               f"LST=$(wc -l < fleet.lst) EPW=$(ls weather | wc -l)"))
    if "--submit" in sys.argv:
        print(f"Submitting {n} cases, width 32")
        print(_ssh(f"sbatch --array=1-{n}%32 --time=7-00:00:00 --export=FLEET_DIR={REMOTE_DIR} {REMOTE_SBATCH}"))


if __name__ == "__main__":
    main()
