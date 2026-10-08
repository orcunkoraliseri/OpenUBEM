from __future__ import annotations

import io
import json
import os
import re
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
CAND1_CSV = OUT_DIR / "open35_resim_fleet_eui_2026-09-30.csv"
DIAG = OUT_DIR / "open38_diagnosis_2026-09-30.csv"
COOKING_JSON = REPO / "openubem" / "data" / "loads" / "cooking_by_archetype.json"
COOKING_SET_CSV = OUT_DIR / "open38_cooking_set_2026-09-30.csv"
OUT_CSV = OUT_DIR / "open38_fix_rerun_2026-09-30.csv"
OUT_JSON = OUT_DIR / "open38_fix_summary_2026-09-30.json"
EVIDENCE = REPO / "evidence" / "open48_refleet"
WORK = Path(tempfile.gettempdir()) / "ubem_validation" / "open38_fix_rerun_2026-09-30_full"
LOCAL_WEATHER = Path(tempfile.gettempdir()) / "ubem_validation" / "open38_rerun_2026-09-29" / "weather"
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_DIR = "/speed-scratch/o_iseri/openubem/fleets/open38_fix_rerun_2026-09-30_full"
REMOTE_WEATHER_SRC = "/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/weather"
REMOTE_SBATCH = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t07.sbatch"
BASELINE_DIR = "C:/Users/o_iseri/Desktop/NEXA-desktop/Content/00.BaselineBuildings_NUs_v231"
SEED = 38
CONTROLS_PER_CELL = 2
N_CONTROLS = 20
STATE_OF = {"nyc": "NY", "la": "CA", "austin": "TX"}
DH_COLS = [
    "cooling_district_eui_kwh_m2", "heating_district_eui_kwh_m2", "fans_district_eui_kwh_m2",
    "pumps_district_eui_kwh_m2", "refrigeration_district_eui_kwh_m2",
    "lighting_district_eui_kwh_m2", "equipment_district_eui_kwh_m2",
    "dhw_district_eui_kwh_m2", "exterior_lighting_eui_kwh_m2",
    "exterior_equipment_eui_kwh_m2", "heat_rejection_eui_kwh_m2",
    "humidification_eui_kwh_m2", "heat_recovery_eui_kwh_m2", "generators_eui_kwh_m2",
]


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr


def stem_of(osm_id: str) -> str:
    return osm_id.replace("/", "_", 1)


def case_name(cell: str, mode: str, stem: str) -> str:
    return f"{mode}__{cell}__{stem}"


def cooking_archetypes() -> dict:
    d = json.loads(COOKING_JSON.read_text())
    return {k: v for k, v in d.items() if not k.startswith("_") and not v.get("no_cooking")
            and (v.get("gas_density_w_m2", 0) > 0 or v.get("elec_density_w_m2", 0) > 0)}


def select_cases() -> pd.DataFrame:
    b = pd.read_csv(BLAST)
    b["osm_id"] = b["osm_id"].astype(str)
    cook = cooking_archetypes()
    d = pd.read_csv(DIAG)
    oom = d[d["cause_class"].astype(str).str.startswith("E_")]
    o38 = d[["cell", "mode", "osm_id"]].copy()
    o38["group"] = np.where(o38["osm_id"].isin(oom["osm_id"]) & (o38["mode"] == "auto"), "oom", "open38")
    cs = b[b["archetype_id"].isin(cook) & (b["floors_option_a"] > 1)][["cell", "osm_id"]].copy()
    cs["mode"] = "auto"
    cs["group"] = "cooking"
    rng = np.random.default_rng(SEED)
    picks = []
    for cell in sorted(b["cell"].unique()):
        pool = b[(b["cell"] == cell) & (~b["changes"]) & (~b["archetype_id"].isin(cook))
                 & (~b["osm_id"].isin(d["osm_id"]))].sort_values("osm_id")
        k = min(CONTROLS_PER_CELL, len(pool))
        if k:
            picks.append(pool.iloc[np.sort(rng.choice(len(pool), size=k, replace=False))])
    ctl = pd.concat(picks)
    if len(ctl) > N_CONTROLS:
        cnt = ctl.groupby("cell").size()
        two = sorted(cnt[cnt >= 2].index)
        drop_cells = rng.choice(two, size=len(ctl) - N_CONTROLS, replace=False)
        ctl = ctl.drop(index=[ctl[ctl["cell"] == c].index[-1] for c in drop_cells])
    ctl = ctl[["cell", "osm_id"]].assign(mode="auto", group="control")
    allc = pd.concat([cs, o38, ctl], ignore_index=True)
    allc["stem"] = allc["osm_id"].map(stem_of)
    allc["name"] = [case_name(c, m, s) for c, m, s in zip(allc["cell"], allc["mode"], allc["stem"])]
    allc = allc.groupby("name", as_index=False).agg(
        cell=("cell", "first"), mode=("mode", "first"), osm_id=("osm_id", "first"),
        stem=("stem", "first"), group=("group", lambda g: "+".join(sorted(set(g)))))
    return allc


def _zone0_area(idf) -> tuple[str, float]:
    from shapely.geometry import Polygon
    z0 = idf.idfobjects["ZONE"][0].Name
    a = 0.0
    for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if s.Zone_Name == z0 and s.Surface_Type.lower() == "floor":
            a += abs(Polygon([(c[0], c[1]) for c in s.coords]).area)
    return z0, a


def build_cell(args: tuple[str, list[dict]]) -> list[dict]:
    cell, items = args
    os.environ["OPENUBEM_BASELINE_IDF_DIR"] = BASELINE_DIR
    import geopandas as gpd
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition.epw_manager import load_stations, resolve_station
    from openubem.idf.builder import BuildingIDF
    from openubem.semantic import enrich_semantics
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from scripts.validation.v12_cell_pipeline import CELL_CONFIGS

    cook = cooking_archetypes()
    blast = pd.read_csv(BLAST).set_index("osm_id")
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

    rows = []
    for it in items:
        osm_id, mode = it["osm_id"], it["mode"]
        base = dict(name=it["name"], cell=cell, osm_id=osm_id, stem=it["stem"], mode=mode,
                    group=it["group"], station_id=sid)
        sub = gdf_57[gdf_57["osm_id"].astype(str) == osm_id]
        if sub.empty:
            rows.append({**base, "generation_status": "not_in_fixture", "idf_path": ""})
            continue
        outdir = WORK / cell / mode
        (outdir / "idfs").mkdir(parents=True, exist_ok=True)
        extra = {}
        try:
            bi = BuildingIDF(sub.iloc[0], resolution_mode=mode, trim_outputs=False)
            m = bi.build(gdf_57, lib, outdir)
            arch = str(sub.iloc[0]["archetype_id"])
            if "cooking" in it["group"] and arch in cook and m.get("idf_path"):
                fp = sub.iloc[0].get("footprint_area_m2")
                fp = 400.0 if pd.isna(fp) else float(fp)
                dens = cook[arch].get("gas_density_w_m2", 0.0) + cook[arch].get("elec_density_w_m2", 0.0)
                fl = int(blast.loc[osm_id, "floors_option_a"])
                w_today = dens * fp * fl
                z0, a0 = _zone0_area(bi.idf)
                extra = dict(cooking_w_today=round(w_today, 1), zone0_name=z0,
                             zone0_floor_m2=round(a0, 2),
                             max_cooking_w_m2_today=round(w_today / a0, 1) if a0 > 0 else None)
        except Exception as e:
            m = {"generation_status": f"exception:{type(e).__name__}:{e}"[:200], "idf_path": ""}
        rows.append({**base, "archetype_id": str(sub.iloc[0]["archetype_id"]),
                     "generation_status": str(m.get("generation_status")),
                     "idf_path": str(m.get("idf_path", "")),
                     "num_zones": m.get("num_zones"),
                     "data_quality_flag": m.get("data_quality_flag"),
                     "resolution_mode": m.get("resolution_mode"), **extra})
    return rows


def cmd_build(submit: bool) -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    if (WORK / "cases.csv").exists():
        cases = pd.read_csv(WORK / "cases.csv", dtype={"osm_id": str})
    else:
        cases = select_cases()
        cases.to_csv(WORK / "cases.csv", index=False)
    print(cases["group"].value_counts().to_string())
    jobs = [(c, g.to_dict("records")) for c, g in cases.groupby("cell")]
    with Pool(min(len(jobs), 6)) as p:
        res = p.map(build_cell, jobs)
    df = pd.DataFrame([r for rs in res for r in rs])
    df.to_csv(WORK / "build_manifest.csv", index=False)
    print(df.groupby(["group", "generation_status"]).size().to_string())

    cs = df[df["group"].str.contains("cooking") & (df["generation_status"] == "success")].copy()
    cs["n_zones"] = cs["num_zones"].astype(int)
    cs = cs[cs["n_zones"] > 1]
    cs[["osm_id", "cell", "archetype_id", "n_zones", "cooking_w_today", "max_cooking_w_m2_today"]].to_csv(
        COOKING_SET_CSV, index=False)
    print(f"cooking set rows={len(cs)}")
    drop = df["group"].eq("cooking") & ~df["osm_id"].isin(cs["osm_id"])
    df = df[~drop]
    ok = df[df["generation_status"] == "success"].copy()
    is_oom = ok["group"].str.contains("oom")
    ok = pd.concat([ok[~is_oom], ok[is_oom]], ignore_index=True)
    n_oom = int(is_oom.sum())
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
            tf.add(r["idf_path"], arcname=f"idfs/{r['name']}.idf")
            lines.append(f"{r['name']}\t{m[0]}")
        b = ("\n".join(lines) + "\n").encode()
        info = tarfile.TarInfo("fleet.lst")
        info.size = len(b)
        tf.addfile(info, io.BytesIO(b))
    (WORK / "fleet.lst").write_text("\n".join(lines) + "\n")
    ok.to_csv(WORK / "submitted_manifest.csv", index=False)
    n = len(lines) - n_oom
    print(f"array cases={n} width=32; single --mem=32G cases={n_oom}; epws={sorted(needed)}")
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
            print(f"Submitting {n_oom} case with --mem=32G")
            print(_ssh(f"sbatch --array={n + 1}-{n + n_oom} --mem=32G --time=7-00:00:00 "
                       f"--export=FLEET_DIR={REMOTE_DIR} {REMOTE_SBATCH}"))


def _fetch(names: list[str], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    lst = "\n".join(f"out/{n}/{f}" for n in names
                    for f in ("eplusout.sql", "eplusout.err", "eplusout.end", "eplusout.eio", "task.rc")) + "\n"
    p = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cd {REMOTE_DIR} && tar czf - --ignore-failed-read -T -'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.stdin.write(lst.encode())
    p.stdin.close()
    n = 0
    with tarfile.open(fileobj=p.stdout, mode="r|gz") as tf:
        for m in tf:
            tf.extract(m, str(dest))
            n += 1
    p.wait()
    if n == 0:
        raise SystemExit(f"STOP: empty fetch: {p.stderr.read().decode()[:400]}")


def _max_cooking_w_m2(idf_path: str) -> float | None:
    if not isinstance(idf_path, str) or not idf_path or not Path(idf_path).exists():
        return None
    t = Path(idf_path).read_text(errors="ignore")
    tot = 0.0
    for key, label in (("Cooking_Gas_", "Power per Zone Floor Area"), ("Cooking_Elec_", "Watts per Zone Floor Area")):
        m = re.search(key + r"[^\n]*\n(?:[^\n]*\n){0,8}?\s*([-\d.eE+]+)\s*[,;]\s*!-\s*" + label, t)
        if m:
            tot += float(m.group(1))
    return tot


def _terminal(d: Path) -> str:
    end = d / "eplusout.end"
    if end.exists():
        s = end.read_text(errors="ignore")
        if "Successfully" in s:
            return "completed"
        if "Fatal" in s:
            return "fatal"
    if (d / "eplusout.sql").exists():
        return "sql_no_end"
    return "no_end"


def _parse_one(args: tuple) -> dict:
    name, stem, osm_id, cell, archetype, sql_str, num_zones, dqf, mode, term = args
    from openubem.results.carbon import compute_gwp
    from openubem.results.parser import check_building_integrity, parse_building
    import geopandas as gpd

    out: dict = {"name": name, "stem": stem, "osm_id": osm_id, "cell": cell,
                 "archetype_id": archetype, "terminal": term}
    if not sql_str:
        return out
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


def _frame(df: pd.DataFrame) -> pd.DataFrame:
    return df[["osm_id", "cell", "archetype_id", "total_kwh", "floor_area_m2", "gwp_total_kgco2"]].copy()


def _pooled(f: pd.DataFrame) -> tuple[float, float]:
    return float(f["total_kwh"].sum() / f["floor_area_m2"].sum()), float(f["gwp_total_kgco2"].sum() / 1000.0)


def cmd_parse() -> None:
    man = pd.read_csv(WORK / "submitted_manifest.csv")
    fetch_dir = WORK / "fetched"
    if not list(fetch_dir.glob("out/*/eplusout.sql")):
        _fetch(man["name"].tolist(), fetch_dir)
    diag = pd.read_csv(DIAG).set_index("case")
    jobs = []
    for _, r in man.iterrows():
        d = fetch_dir / "out" / r["name"]
        sql = d / "eplusout.sql"
        jobs.append((r["name"], r["stem"], r["osm_id"], r["cell"], r["archetype_id"],
                     str(sql) if sql.exists() else "", r["num_zones"], r["data_quality_flag"],
                     r["mode"], _terminal(d)))
    with Pool(6) as p:
        res = p.map(_parse_one, jobs)
    new = pd.DataFrame(res).merge(man[["name", "group", "mode", "idf_path"]], on="name", how="left")
    new["max_cooking_w_m2_after"] = new["idf_path"].map(_max_cooking_w_m2)
    new["cause_class"] = new["name"].map(diag["cause_class"])
    new.to_csv(OUT_CSV, index=False)

    ad = pd.read_csv(ADOPTED)
    ad["adopted_total_kwh"] = ad["total_eui_kwh_m2"] * ad["floor_area_m2"]
    ad_i = ad.set_index("osm_id")
    ok_mask = new["parse_status"].eq("success") & new["terminal"].eq("completed")
    ok = new[ok_mask]
    ctl = ok[ok["group"] == "control"].copy()
    ctl["adopted_eui"] = ctl["osm_id"].map(ad_i["total_eui_kwh_m2"])
    ctl["rel_diff_pct"] = 100.0 * (ctl["total_eui_kwh_m2"] - ctl["adopted_eui"]) / ctl["adopted_eui"]

    c1 = _frame(ad.assign(total_kwh=ad["adopted_total_kwh"]))
    summary: dict = {"n_cases": int(len(new)), "terminal_counts": new["terminal"].value_counts().to_dict(),
                     "control_n": int(len(ctl)),
                     "control_max_abs_rel_diff_pct": float(ctl["rel_diff_pct"].abs().max()) if len(ctl) else None}
    if CAND1_CSV.exists():
        t3 = pd.read_csv(CAND1_CSV)
        t3 = t3[(t3["role"] == "target") & (t3["parse_status"] == "success")]
        c1 = pd.concat([c1[~c1["osm_id"].isin(t3["osm_id"])], _frame(t3)], ignore_index=True)
        summary["candidate1_source"] = "adopted with open35 targets replaced"
    else:
        summary["candidate1_source"] = "MISSING open35 CSV: candidate 1 = adopted (T06b must stop)"
    cs_new = ok[ok["group"].str.contains("cooking") & (ok["mode"] == "auto")]
    c2 = pd.concat([c1[~c1["osm_id"].isin(cs_new["osm_id"])], _frame(cs_new)], ignore_index=True)
    e1, k1 = _pooled(c1)
    e2, k2 = _pooled(c2)
    summary.update(n_c1=int(len(c1)), n_c2=int(len(c2)), pooled_eui_c1=round(e1, 4), pooled_eui_c2=round(e2, 4),
                   carbon_t_c1=round(k1, 2), carbon_t_c2=round(k2, 2))
    old = c1.set_index("osm_id").loc[cs_new["osm_id"].tolist()].reset_index() if len(cs_new) else pd.DataFrame()
    per_cell, per_arch = {}, {}
    for key, dest in (("cell", per_cell), ("archetype_id", per_arch)):
        for k, g in cs_new.groupby(key):
            o = old[old[key] == k]
            dest[k] = dict(n=int(len(g)), old_eui=round(float(o["total_kwh"].sum() / o["floor_area_m2"].sum()), 3),
                           new_eui=round(float(g["total_kwh"].sum() / g["floor_area_m2"].sum()), 3))
    summary["per_cell_cooking_set"] = per_cell
    summary["per_archetype_cooking_set"] = per_arch
    o38 = ok[ok["group"].str.contains("open38|oom")]
    adds = o38[(o38["mode"] == "auto") & (~o38["osm_id"].isin(ad["osm_id"]))]
    summary["additions_auto_not_in_adopted"] = adds[["osm_id", "cell", "archetype_id", "total_eui_kwh_m2"]].to_dict("records")
    rec = new[new["group"].str.contains("open38|oom")].copy()
    rec["recovered"] = ok_mask.loc[rec.index]
    summary["open38_recovered_by_class"] = {
        str(k): dict(recovered=int(g["recovered"].sum()), total=int(len(g)))
        for k, g in rec.groupby("cause_class")}
    cook_rows = new[new["group"].str.contains("cooking")]
    cnf = cook_rows[~ok_mask.loc[cook_rows.index]]
    summary["cooking_set_total"] = int(len(cook_rows))
    summary["cooking_set_not_success_count"] = int(len(cnf))
    summary["cooking_set_not_success_names"] = cnf["name"].tolist()
    summary["max_cooking_w_m2_after_D6"] = float(cook_rows["max_cooking_w_m2_after"].max())
    summary["abups_ok_fail_count"] = int((new["abups_ok"] == False).sum())  # noqa: E712
    OUT_JSON.write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str)[:3000])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        cmd_build("--submit" in sys.argv)
    elif cmd == "parse":
        cmd_parse()
    else:
        raise SystemExit(f"unknown subcommand {cmd}")
