from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
RERUN = OUT_DIR / "open38_fix_rerun_2026-09-30.csv"
SRC_WORK = Path(tempfile.gettempdir()) / "ubem_validation" / "open38_fix_rerun_2026-09-30_full"
WORK = Path(tempfile.gettempdir()) / "ubem_validation" / "seven_items_trial_2026-09-30"
EVIDENCE = REPO / "evidence" / "open48_refleet"
LOCAL_WEATHER = Path(tempfile.gettempdir()) / "ubem_validation" / "open38_rerun_2026-09-29" / "weather"
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_DIR = "/speed-scratch/o_iseri/openubem/fleets/seven_items_trial_2026-09-30"
REMOTE_WEATHER_SRC = "/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/weather"
REMOTE_SBATCH = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t07.sbatch"
BASELINE_DIR = "C:/Users/o_iseri/Desktop/NEXA-desktop/Content/00.BaselineBuildings_NUs_v231"
N_CONTROLS = 8
BOTH_STOREY2 = ["way/472961091", "way/472961164"]

_TS = re.compile(r"(?im)^(\s*Timestep\s*,\s*)\d+(\s*;)")
_ZAHB = re.compile(r"(?im)^\s*ZoneAirHeatBalanceAlgorithm\s*,[^;]*;[^\n]*\n?")
_ZAHB_NEW = "\nZoneAirHeatBalanceAlgorithm,\n    AnalyticalSolution;      !- Algorithm\n"


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr


def edit_timestep(t: str) -> str:
    t2, n = _TS.subn(r"\g<1>20\g<2>", t)
    assert n == 1, f"Timestep objects changed: {n}"
    return t2


def edit_zahb(t: str) -> str:
    t2, n = _ZAHB.subn("", t)
    assert n in (0, 1), f"ZoneAirHeatBalanceAlgorithm objects found: {n}"
    return t2.rstrip("\n") + "\n" + _ZAHB_NEW


VARIANTS = {
    "V0": lambda t: t,
    "V1": edit_timestep,
    "V2": edit_zahb,
    "V3": lambda t: edit_zahb(edit_timestep(t)),
}


def select() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    r = pd.read_csv(RERUN, dtype={"osm_id": str})
    man = pd.read_csv(SRC_WORK / "build_manifest.csv", dtype={"osm_id": str})
    man = man[["name", "station_id"]]
    r = r.merge(man, on="name", how="left")
    failing = r[r["group"].isin(["open38", "oom"]) & (r["terminal"] != "completed")].copy()
    assert len(failing) == 28, len(failing)
    ok = r[(r["terminal"] == "completed") & (r["parse_status"] == "success") & (r["mode"] == "auto")].copy()
    ok = ok.sort_values("stem")
    fixed = ok[ok["osm_id"].isin(BOTH_STOREY2)]
    seen = set(fixed["archetype_id"])
    fill = []
    for _, row in ok[~ok["osm_id"].isin(BOTH_STOREY2)].iterrows():
        if row["archetype_id"] in seen:
            continue
        seen.add(row["archetype_id"])
        fill.append(row)
        if len(fixed) + len(fill) == N_CONTROLS:
            break
    controls = pd.concat([fixed, pd.DataFrame(fill)], ignore_index=True)
    assert len(controls) == N_CONTROLS, len(controls)
    sliver = failing[failing["cause_class"].astype(str).str.startswith("C1")].copy()
    assert len(sliver) == 6, len(sliver)
    return failing, controls, sliver


def build_s1(sliver: pd.DataFrame) -> pd.DataFrame:
    os.environ["OPENUBEM_BASELINE_IDF_DIR"] = BASELINE_DIR
    import geopandas as gpd
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.idf import surfaces
    from openubem.idf.builder import BuildingIDF
    from openubem.semantic import enrich_semantics
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier

    surfaces._TINY_ZONE_AREA_M2 = 2.0
    surfaces._coreperim_has_tiny_zone_area.__defaults__ = (2.0,)
    cell = "la_rural"
    sid = str(sliver["station_id"].iloc[0])
    gdf_in = gpd.read_file(str(EVIDENCE / cell / "01_buildings.gpkg"))[_INPUT_SCHEMA_COLUMNS].copy()
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
    outdir = WORK / "s1_build" / cell / "fast_zone"
    (outdir / "idfs").mkdir(parents=True, exist_ok=True)
    rows = []
    for _, s in sliver.iterrows():
        sub = gdf_57[gdf_57["osm_id"].astype(str) == s["osm_id"]]
        m = BuildingIDF(sub.iloc[0], resolution_mode="fast_zone", trim_outputs=False).build(gdf_57, lib, outdir)
        assert m.get("idf_path"), (s["osm_id"], m.get("generation_status"))
        rows.append(dict(osm_id=s["osm_id"], idf_path=str(m["idf_path"]), num_zones=m.get("num_zones"),
                         resolution_mode=m.get("resolution_mode"), generation_status=m.get("generation_status")))
    return pd.DataFrame(rows)


def cmd_stage() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    failing, controls, sliver = select()
    s1 = build_s1(sliver)
    print(s1[["osm_id", "num_zones", "resolution_mode", "generation_status"]].to_string())
    s1m = s1.set_index("osm_id")
    srcs = pd.read_csv(SRC_WORK / "build_manifest.csv", dtype={"osm_id": str}).set_index("name")["idf_path"]
    rows = []

    def add(v, g, r, src):
        rows.append(dict(variant=v, group=g, mode=r["mode"], cell=r["cell"], stem=r["stem"],
                         osm_id=r["osm_id"], archetype_id=r["archetype_id"], src=src,
                         station_id=r["station_id"]))

    for _, r in failing.iterrows():
        for v in ("V1", "V2", "V3"):
            add(v, "failing", r, srcs[r["name"]])
    for _, r in sliver.iterrows():
        add("S1", "sliver_s1", r, s1m.loc[r["osm_id"], "idf_path"])
    for _, r in controls.iterrows():
        for v in ("V0", "V1", "V2", "V3"):
            add(v, "control", r, srcs[r["name"]])
    cases = pd.DataFrame(rows)
    cases["name"] = cases["variant"] + "__" + cases["mode"] + "__" + cases["cell"] + "__" + cases["stem"]
    assert cases["name"].is_unique
    epws = [l.strip() for l in _ssh(f"ls {REMOTE_WEATHER_SRC}").splitlines() if l.strip().endswith(".epw")]
    lines, needed = [], set()
    tarpath = WORK / "fleet.tar.gz"
    with tarfile.open(tarpath, "w:gz") as tf:
        for _, r in cases.iterrows():
            m = [e for e in epws if f".{r['station_id']}_" in e]
            if len(m) != 1:
                raise SystemExit(f"STOP: EPW for station {r['station_id']} matches {m}")
            needed.add(m[0])
            text = Path(r["src"]).read_text(errors="ignore")
            if r["variant"] in VARIANTS:
                text = VARIANTS[r["variant"]](text)
            b = text.encode()
            info = tarfile.TarInfo(f"idfs/{r['name']}.idf")
            info.size = len(b)
            tf.addfile(info, io.BytesIO(b))
            lines.append(f"{r['name']}\t{m[0]}")
        b = ("\n".join(lines) + "\n").encode()
        info = tarfile.TarInfo("fleet.lst")
        info.size = len(b)
        tf.addfile(info, io.BytesIO(b))
    (WORK / "fleet.lst").write_text("\n".join(lines) + "\n")
    cases[["name", "variant", "mode", "cell", "stem", "osm_id", "archetype_id", "group"]].to_csv(
        WORK / "cases.csv", index=False)
    cases.to_csv(WORK / "cases_full.csv", index=False)
    n = len(lines)
    print(cases["group"].value_counts().to_string())
    print(f"staged cases={n} width=32 epws={sorted(needed)}")
    print(controls[["osm_id", "archetype_id"]].to_string(index=False))
    print(_ssh(f"mkdir -p {REMOTE_DIR}/weather {REMOTE_DIR}/out"))
    for e in sorted(needed):
        print(_ssh(f"cp {REMOTE_WEATHER_SRC}/{e} {REMOTE_DIR}/weather/"))
    r = subprocess.run(["scp", str(tarpath), f"{REMOTE_HOST}:{REMOTE_DIR}/fleet.tar.gz"],
                       capture_output=True, text=True, timeout=1800)
    if r.returncode:
        raise SystemExit(f"STOP: scp {r.stderr}")
    print(_ssh(f"cd {REMOTE_DIR} && tar -xzf fleet.tar.gz && echo IDF=$(ls idfs | wc -l) "
               f"LST=$(wc -l < fleet.lst) EPW=$(ls weather | wc -l)"))
    print(f"sbatch --array=1-{n}%32 --mem=32G --time=7-00:00:00 --export=FLEET_DIR={REMOTE_DIR} {REMOTE_SBATCH}")


ITEM_OF = {
    "A_laundry_gas_dryer_unconditioned": "OPEN-67",
    "C1_sliver_perimeter_zone_under_2m2": "OPEN-68",
    "C2_ordinary_gains_diverges_in_sizing_no_column_explains": "OPEN-69",
    "D_nonconvex_shading": "OPEN-70",
    "E_out_of_memory": "OPEN-71",
}
HARVEST_CSV = OUT_DIR / "seven_items_trial_2026-09-30.csv"
JOB_ID = "1404350"


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


def _err_lines(d: Path) -> tuple[str, str]:
    f = d / "eplusout.err"
    if not f.exists():
        return "", ""
    sev, fat = "", ""
    for ln in f.read_text(errors="ignore").splitlines():
        if not sev and "** Severe  **" in ln:
            sev = ln.strip()[:200]
        if not fat and "**  Fatal  **" in ln:
            fat = ln.strip()[:200]
    return sev, fat


def _parse_one(args: tuple) -> dict:
    name, osm_id, cell, archetype, sql_str, num_zones, mode, term = args
    import warnings
    from openubem.results.parser import parse_building
    import geopandas as gpd

    out: dict = {"name": name, "terminal": term}
    if not sql_str:
        return out
    try:
        bld = gpd.read_file(str(EVIDENCE / cell / "01_buildings.gpkg"))[
            ["osm_id", "footprint_area_m2", "levels", "height_m"]].set_index("osm_id").loc[osm_id]
        lv = bld["levels"]
        row = pd.Series({
            "osm_id": osm_id, "num_zones": int(num_zones), "data_quality_flag": "",
            "resolution_mode": mode, "archetype_id": archetype,
            "footprint_area_m2": float(bld["footprint_area_m2"]),
            "levels": None if pd.isna(lv) else lv, "height_m": bld["height_m"]})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = parse_building(Path(sql_str), None, row)
        out["parse_status"] = p["parse_status"]
        out["total_eui_kwh_m2"] = p.get("total_eui_kwh_m2")
    except Exception as exc:
        out["parse_status"] = "worker_error"
        out["error_summary"] = f"{type(exc).__name__}: {exc}"[:300]
    return out


def cmd_harvest() -> None:
    from multiprocessing import Pool
    cases = pd.read_csv(WORK / "cases_full.csv")
    fetch_dir = WORK / "fetched"
    if not list(fetch_dir.glob("out/*/eplusout.err")):
        _fetch(cases["name"].tolist(), fetch_dir)
    lst = [l.split("	")[0] for l in (WORK / "fleet.lst").read_text().splitlines() if l.strip()]
    sac = {}
    for ln in _ssh(f"sacct -j {JOB_ID} -n -X -o JobID,State,MaxRSS").splitlines():
        parts = ln.split()
        if len(parts) >= 2 and "_" in parts[0]:
            sac[lst[int(parts[0].split("_")[1]) - 1]] = (parts[1], parts[2] if len(parts) > 2 else "")
    jobs = []
    for _, r in cases.iterrows():
        d = fetch_dir / "out" / r["name"]
        sql = d / "eplusout.sql"
        nz = len(re.findall(r"(?im)^\s*Zone\s*,", Path(r["src"]).read_text(errors="ignore")))
        term = _terminal(d) if d.exists() else "no_output:" + sac.get(r["name"], ("unknown", ""))[0]
        jobs.append((r["name"], r["osm_id"], r["cell"], r["archetype_id"],
                     str(sql) if sql.exists() else "", nz, r["mode"], term))
    with Pool(6) as p:
        res = p.map(_parse_one, jobs)
    df = pd.DataFrame(res)
    df = cases[["name", "variant", "group", "osm_id", "mode", "cell", "stem"]].merge(df, on="name")
    sev = [_err_lines(fetch_dir / "out" / n) for n in df["name"]]
    df["first_severe"] = [a for a, _ in sev]
    df["fatal"] = [b for _, b in sev]
    df["slurm_state"] = df["name"].map(lambda n: sac.get(n, ("", ""))[0])
    df["max_rss"] = df["name"].map(lambda n: sac.get(n, ("", ""))[1])
    src = pd.read_csv(RERUN, usecols=["mode", "cell", "stem", "cause_class"]).drop_duplicates(["mode", "cell", "stem"])
    print("distinct cause_class in source:", sorted(src["cause_class"].dropna().unique()))
    print("mapping used:", ITEM_OF, "| group sliver_s1 -> OPEN-68")
    df = df.merge(src, on=["mode", "cell", "stem"], how="left")
    df["item"] = df["cause_class"].map(ITEM_OF)
    df.loc[df["group"] == "sliver_s1", "item"] = "OPEN-68"
    bad = df[(df["group"] != "control") & df["item"].isna()]
    if len(bad):
        raise SystemExit(f"STOP: unmapped:\n{bad[['name', 'cause_class']].to_string()}")
    df["completed"] = df["parse_status"].eq("success") & df["terminal"].eq("completed")
    cols = ["name", "variant", "group", "item", "osm_id", "mode", "terminal", "parse_status",
            "total_eui_kwh_m2", "first_severe", "fatal", "slurm_state", "max_rss", "cause_class"]
    df[cols].to_csv(HARVEST_CSV, index=False)
    print("rows:", len(df))
    t = df[df["group"] != "control"]
    piv = t.groupby(["item", "variant"])["completed"].agg(["sum", "count"])
    print((piv["sum"].astype(int).astype(str) + "/" + piv["count"].astype(str)).unstack("variant").fillna("-").to_string())
    c = df[(df["group"] == "control")].pivot_table(index="osm_id", columns="variant", values="total_eui_kwh_m2")
    c = c.where(df[df["group"] == "control"].pivot_table(index="osm_id", columns="variant", values="completed", aggfunc="min").astype(bool))
    print("controls total_eui:\n", c.round(3).to_string())
    for v in ("V1", "V2", "V3"):
        print(v, "% change vs V0:", ((c[v] / c["V0"] - 1) * 100).round(3).to_dict())
    print("terminal counts:", df["terminal"].value_counts().to_dict())
    sch = df[df["osm_id"] == "way/319507579"]
    print(sch[["name", "terminal", "slurm_state", "max_rss", "parse_status"]].to_string())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "stage":
        cmd_stage()
    elif cmd == "harvest":
        cmd_harvest()
    else:
        raise SystemExit(f"unknown subcommand {cmd}")
