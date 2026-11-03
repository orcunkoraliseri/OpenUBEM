from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
BLAST = OUT_DIR / "open35_blast_radius_2026-09-30.csv"
ADOPTED = OUT_DIR / "open65_reparse_fleet_eui_2026-09-29.csv"
OUT_CSV = OUT_DIR / "open35_resim_fleet_eui_2026-09-30.csv"
OUT_JSON = OUT_DIR / "open35_resim_summary_2026-09-30.json"
EVIDENCE = REPO / "evidence" / "open48_refleet"
WORK = Path(tempfile.gettempdir()) / "ubem_validation" / "open35_resim_2026-09-30_full"
LOCAL_WEATHER = Path(tempfile.gettempdir()) / "ubem_validation" / "open38_rerun_2026-09-29" / "weather"
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_DIR = "/speed-scratch/o_iseri/openubem/fleets/open35_resim_2026-09-30_full"
REMOTE_WEATHER_SRC = "/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/weather"
REMOTE_SBATCH = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t07.sbatch"
BASELINE_DIR = "C:/Users/o_iseri/Desktop/NEXA-desktop/Content/00.BaselineBuildings_NUs_v231"
SEED = 35
CONTROLS_PER_CELL = 2
COOKING_EXCLUDE = ("restaurant", "hotel", "hospital", "school", "college", "supermarket")
STATE_OF = {"nyc": "NY", "la": "CA", "austin": "TX"}
DH_COLS = [
    "cooling_district_eui_kwh_m2", "heating_district_eui_kwh_m2", "fans_district_eui_kwh_m2",
    "pumps_district_eui_kwh_m2", "refrigeration_district_eui_kwh_m2",
    "lighting_district_eui_kwh_m2", "equipment_district_eui_kwh_m2",
    "dhw_district_eui_kwh_m2", "exterior_lighting_eui_kwh_m2",
    "exterior_equipment_eui_kwh_m2", "heat_rejection_eui_kwh_m2",
    "humidification_eui_kwh_m2", "heat_recovery_eui_kwh_m2", "generators_eui_kwh_m2",
]


OOM_IDS = {"way/163631696", "way/260085159", "way/266010439", "way/266143341", "way/266149373", "way/266170792"}


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr


def stem_of(osm_id: str) -> str:
    return osm_id.replace("/", "_", 1)


def case_name(cell: str, stem: str) -> str:
    return f"auto__{cell}__{stem}"


def select_cases() -> pd.DataFrame:
    b = pd.read_csv(BLAST)
    b["osm_id"] = b["osm_id"].astype(str)
    targets = b[b["changes"]].copy()
    targets["role"] = "target"
    rng = np.random.default_rng(SEED)
    picks = []
    for cell in sorted(b["cell"].unique()):
        pool = b[(b["cell"] == cell) & (~b["changes"])
                 & (~b["archetype_id"].str.lower().str.contains("|".join(COOKING_EXCLUDE)))]
        pool = pool.sort_values("osm_id")
        k = min(CONTROLS_PER_CELL, len(pool))
        if k:
            picks.append(pool.iloc[np.sort(rng.choice(len(pool), size=k, replace=False))])
    controls = pd.concat(picks)
    n_ctl = 20
    if len(controls) > n_ctl:
        cnt = controls.groupby("cell").size()
        two = sorted(cnt[cnt >= 2].index)
        drop_cells = rng.choice(two, size=len(controls) - n_ctl, replace=False)
        drop_idx = [controls[controls["cell"] == c].index[-1] for c in drop_cells]
        controls = controls.drop(index=drop_idx)
    controls = controls.assign(role="control")
    cases = pd.concat([targets, controls], ignore_index=True)
    cases["stem"] = cases["osm_id"].map(stem_of)
    return cases


def build_cell(args: tuple[str, list[str], list[str]]) -> list[dict]:
    cell, osm_ids, roles = args
    os.environ["OPENUBEM_BASELINE_IDF_DIR"] = BASELINE_DIR
    import geopandas as gpd
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition.epw_manager import load_stations, resolve_station
    from openubem.idf.builder import BuildingIDF
    from openubem.semantic import enrich_semantics
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from scripts.validation.v12_cell_pipeline import CELL_CONFIGS

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
    local_epw = [e for e in LOCAL_WEATHER.glob("*.epw") if f".{sid}_" in e.name]
    assert len(local_epw) == 1, (sid, local_epw)
    gdf_29["epw_path"] = str(local_epw[0])
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"])
    gdf_57, lib = enrich_semantics(gdf_29)

    outdir = WORK / cell
    (outdir / "idfs").mkdir(parents=True, exist_ok=True)
    rows = []
    for osm_id, role in zip(osm_ids, roles):
        stem = stem_of(osm_id)
        base = dict(cell=cell, osm_id=osm_id, stem=stem, role=role, station_id=sid)
        sub = gdf_57[gdf_57["osm_id"].astype(str) == osm_id]
        if sub.empty:
            rows.append({**base, "generation_status": "not_in_fixture", "idf_path": ""})
            continue
        try:
            m = BuildingIDF(sub.iloc[0], resolution_mode="auto", trim_outputs=False).build(gdf_57, lib, outdir)
        except Exception as e:
            m = {"generation_status": f"exception:{type(e).__name__}:{e}"[:200], "idf_path": ""}
        rows.append({**base, "generation_status": str(m.get("generation_status")),
                     "idf_path": str(m.get("idf_path", "")),
                     "num_zones": m.get("num_zones"),
                     "data_quality_flag": m.get("data_quality_flag"),
                     "resolution_mode": m.get("resolution_mode")})
    return rows


def cmd_build(submit: bool) -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    if (WORK / "cases.csv").exists():
        cases = pd.read_csv(WORK / "cases.csv", dtype={"osm_id": str})
    else:
        cases = select_cases()
        cases.to_csv(WORK / "cases.csv", index=False)
    print(f"targets={int((cases.role == 'target').sum())} controls={int((cases.role == 'control').sum())}")
    jobs = [(c, g["osm_id"].tolist(), g["role"].tolist()) for c, g in cases.groupby("cell")]
    with Pool(min(len(jobs), 6)) as p:
        res = p.map(build_cell, jobs)
    df = pd.DataFrame([r for rs in res for r in rs])
    df.to_csv(WORK / "build_manifest.csv", index=False)
    print(df.groupby(["role", "generation_status"]).size().to_string())
    ok = df[df["generation_status"] == "success"]
    ok = ok.assign(_oom=ok["osm_id"].isin(OOM_IDS)).sort_values("_oom", kind="stable").drop(columns="_oom")
    n_oom = int(ok["osm_id"].isin(OOM_IDS).sum())
    print(f"BUILT {len(ok)} of {len(df)}")
    if len(ok) == 0:
        raise SystemExit("STOP: nothing built")

    epws = [l.strip() for l in _ssh(f"ls {REMOTE_WEATHER_SRC}").splitlines() if l.strip().endswith(".epw")]
    lines, needed = [], set()
    tarpath = WORK / "fleet.tar.gz"
    with tarfile.open(tarpath, "w:gz") as tf:
        for _, r in ok.iterrows():
            m = [e for e in epws if f".{r['station_id']}_" in e]
            if len(m) != 1:
                raise SystemExit(f"STOP: EPW for station {r['station_id']} matches {m}")
            needed.add(m[0])
            name = case_name(r["cell"], r["stem"])
            tf.add(r["idf_path"], arcname=f"idfs/{name}.idf")
            lines.append(f"{name}\t{m[0]}")
        b = ("\n".join(lines) + "\n").encode()
        info = tarfile.TarInfo("fleet.lst")
        info.size = len(b)
        tf.addfile(info, io.BytesIO(b))
    (WORK / "fleet.lst").write_text("\n".join(lines) + "\n")
    n = len(lines) - n_oom
    print(f"array cases={n} width=32; single --mem=32G cases={n_oom} epws={sorted(needed)}")
    print(_ssh(f"mkdir -p {REMOTE_DIR}/weather {REMOTE_DIR}/out"))
    for e in sorted(needed):
        print(_ssh(f"cp {REMOTE_WEATHER_SRC}/{e} {REMOTE_DIR}/weather/"))
    r = subprocess.run(["scp", str(tarpath), f"{REMOTE_HOST}:{REMOTE_DIR}/fleet.tar.gz"],
                       capture_output=True, text=True, timeout=1800)
    if r.returncode:
        raise SystemExit(f"STOP: scp {r.stderr}")
    print(_ssh(f"cd {REMOTE_DIR} && tar -xzf fleet.tar.gz && echo IDF=$(ls idfs | wc -l) "
               f"LST=$(wc -l < fleet.lst) EPW=$(ls weather | wc -l)"))
    if submit:
        print(f"Submitting {n} cases, width 32")
        print(_ssh(f"sbatch --array=1-{n}%32 --time=7-00:00:00 --export=FLEET_DIR={REMOTE_DIR} {REMOTE_SBATCH}"))
        if n_oom:
            print(f"Submitting {n_oom} cases with --mem=32G")
            print(_ssh(f"sbatch --array={n + 1}-{n + n_oom} --mem=32G --time=7-00:00:00 "
                       f"--export=FLEET_DIR={REMOTE_DIR} {REMOTE_SBATCH}"))


def _fetch(stems_cells: list[tuple[str, str]], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    names = "\n".join(f"out/{case_name(c, s)}/{f}" for c, s in stems_cells
                      for f in ("eplusout.sql", "eplusout.err", "eplusout.end", "eplusout.eio", "task.rc")) + "\n"
    p = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cd {REMOTE_DIR} && tar czf - --ignore-failed-read -T -'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.stdin.write(names.encode())
    p.stdin.close()
    n = 0
    with tarfile.open(fileobj=p.stdout, mode="r|gz") as tf:
        for m in tf:
            tf.extract(m, str(dest))
            n += 1
    p.wait()
    if n == 0:
        raise SystemExit(f"STOP: empty fetch: {p.stderr.read().decode()[:400]}")


def _parse_one(args: tuple) -> dict:
    stem, osm_id, cell, archetype, sql_str, num_zones, dqf, mode = args
    from openubem.results.carbon import compute_gwp
    from openubem.results.parser import check_building_integrity, parse_building
    import geopandas as gpd

    out: dict = {"stem": stem, "osm_id": osm_id, "cell": cell, "archetype_id": archetype}
    try:
        bld = gpd.read_file(str(EVIDENCE / cell / "01_buildings.gpkg"))[
            ["osm_id", "footprint_area_m2", "levels", "height_m"]].set_index("osm_id").loc[osm_id]
        lv = bld["levels"]
        row = pd.Series({
            "osm_id": osm_id, "num_zones": int(num_zones), "data_quality_flag": dqf,
            "resolution_mode": mode, "archetype_id": archetype,
            "footprint_area_m2": float(bld["footprint_area_m2"]),
            "levels": None if pd.isna(lv) else lv, "height_m": bld["height_m"]})
        sql = Path(sql_str)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = parse_building(sql, None, row)
            out.update({k: v for k, v in p.items() if not k.startswith("gwp_") and k != "osm_id"})
            if p["parse_status"] == "success":
                gw = compute_gwp(p, STATE_OF[cell.split("_")[0]])
                out.update(gw)
                fa = p["floor_area_m2"]
                out["total_kwh"] = p["total_eui_kwh_m2"] * fa
                out["dh_kwh"] = sum(p[c] for c in DH_COLS) * fa
                out["gwp_total_kgco2"] = gw["gwp_total_kgco2_m2"] * fa
            out["abups_ok"] = check_building_integrity(sql)["abups_ok"]
    except Exception as exc:
        out["parse_status"] = out.get("parse_status", "worker_error")
        out["error_summary"] = f"{type(exc).__name__}: {exc}"[:300]
    return out


def gpd_fp(cell: str) -> pd.Series:
    import geopandas as gpd
    return gpd.read_file(str(EVIDENCE / cell / "01_buildings.gpkg"))[["osm_id", "footprint_area_m2"]].set_index("osm_id")["footprint_area_m2"]


def cmd_parse() -> None:
    man = pd.read_csv(WORK / "build_manifest.csv")
    man = man[man["generation_status"] == "success"]
    fetch_dir = WORK / "fetched"
    if not list(fetch_dir.rglob("eplusout.sql")):
        _fetch(list(zip(man["cell"], man["stem"])), fetch_dir)
    blast = pd.read_csv(BLAST).set_index("osm_id")
    jobs = []
    for _, r in man.iterrows():
        sql = fetch_dir / "out" / case_name(r["cell"], r["stem"]) / "eplusout.sql"
        if sql.exists():
            jobs.append((r["stem"], r["osm_id"], r["cell"], blast.loc[r["osm_id"], "archetype_id"],
                         str(sql), r["num_zones"], r["data_quality_flag"], r["resolution_mode"]))
    with Pool(6) as p:
        res = p.map(_parse_one, jobs)
    new = pd.DataFrame(res).merge(man[["osm_id", "role"]], on="osm_id", how="left")
    ad = pd.read_csv(ADOPTED)
    ad["adopted_total_kwh"] = ad["total_eui_kwh_m2"] * ad["floor_area_m2"]
    ad_i = ad.set_index("osm_id")
    ctl = new[(new["role"] == "control") & (new["parse_status"] == "success")].copy()
    ctl["adopted_eui"] = ctl["osm_id"].map(ad_i["total_eui_kwh_m2"])
    ctl["rel_diff_pct"] = 100.0 * (ctl["total_eui_kwh_m2"] - ctl["adopted_eui"]) / ctl["adopted_eui"]
    tg = new[new["role"] == "target"]
    ok_t = tg[tg["parse_status"] == "success"]
    keep = ad[~ad["osm_id"].isin(ok_t["osm_id"])]
    cand_tot = keep["adopted_total_kwh"].sum() + ok_t["total_kwh"].sum()
    cand_fa = keep["floor_area_m2"].sum() + ok_t["floor_area_m2"].sum()
    ad_c = ad["gwp_total_kgco2"].sum() / 1000.0
    cand_c = (keep["gwp_total_kgco2"].sum() + ok_t["gwp_total_kgco2"].sum()) / 1000.0
    new.to_csv(OUT_CSV, index=False)
    cell_delta = {}
    for c, g in ok_t.groupby("cell"):
        a = ad_i.loc[g["osm_id"]]
        cell_delta[c] = dict(n=int(len(g)),
                             adopted_eui=round(float(a["adopted_total_kwh"].sum() / a["floor_area_m2"].sum()), 3),
                             new_eui=round(float(g["total_kwh"].sum() / g["floor_area_m2"].sum()), 3))
    summary = dict(
        n_targets=int(len(tg)), n_targets_success=int(len(ok_t)),
        failed_targets=tg[tg["parse_status"] != "success"][["osm_id", "parse_status"]].to_dict("records"),
        n_controls=int(len(ctl)), control_max_abs_rel_diff_pct=float(ctl["rel_diff_pct"].abs().max()),
        pooled_eui_old=round(float(ad["adopted_total_kwh"].sum() / ad["floor_area_m2"].sum()), 4),
        pooled_eui_new=round(float(cand_tot / cand_fa), 4),
        carbon_t_old=round(float(ad_c), 2), carbon_t_new=round(float(cand_c), 2),
        per_cell_changed_only=cell_delta,
        abups_ok_fail_count=int((new["abups_ok"] == False).sum()))  # noqa: E712
    fp = pd.concat([gpd_fp(c) for c in ok_t["cell"].unique()])
    ratio = ok_t["floor_area_m2"].values / (ok_t["osm_id"].map(fp).values * ok_t["osm_id"].map(blast["floors_option_a"]).values)
    summary["floor_area_ratio_median"] = round(float(pd.Series(ratio).median()), 4)
    arch = {}
    for a, g in ok_t.groupby("archetype_id"):
        x = ad_i.loc[g["osm_id"]]
        arch[a] = dict(n=int(len(g)),
                       adopted_eui=round(float(x["adopted_total_kwh"].sum() / x["floor_area_m2"].sum()), 3),
                       new_eui=round(float(g["total_kwh"].sum() / g["floor_area_m2"].sum()), 3))
    summary["per_archetype_changed_only"] = arch
    summary["candidate_population"] = int(len(keep) + len(ok_t))
    summary["adopted_population"] = int(len(ad))
    fails = []
    for _, r in new[(new["parse_status"] != "success")].iterrows():
        e = fetch_dir / "out" / case_name(r["cell"], r["stem"]) / "eplusout.err"
        last = ""
        if e.exists():
            ls = [l.strip() for l in e.read_text(errors="replace").splitlines() if "** Severe" in l or "**  Fatal" in l or "** Fatal" in l]
            last = ls[-1] if ls else ""
        fails.append(dict(osm_id=r["osm_id"], cell=r["cell"], archetype_id=r["archetype_id"], role=r["role"],
                          parse_status=r["parse_status"], last_severe_fatal=last or "out of memory / none"))
    summary["failures"] = fails
    OUT_JSON.write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k not in ('per_cell_changed_only', 'per_archetype_changed_only')}, indent=1)[:4000])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        cmd_build("--submit" in sys.argv)
    elif cmd == "parse":
        cmd_parse()
    else:
        raise SystemExit(f"unknown subcommand {cmd}")
