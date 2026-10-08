from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
EV = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
RB = EV / "rulebook_2026-09-30"
PF = RB / "partner_fixed_homes_2026-10-08"
OUT = ROOT / "docs" / "docs_DONE" / "SETUP" / "europeanLocations" / "results"
TAG = "rules_2026-10-08"
EUI_SOURCE = "local_2026-10-08"
SUPERSEDES = "2026-10-06"
STAMP = "2026-10-08"
VINTAGE = "2026-10-08 (owner D-EU-149: correctly divided homes only)"
J_TO_KWH = 1.0 / 3.6e6
HEATING_SQL = (
    "SELECT SUM(r.Value) FROM ReportData r "
    "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
    "WHERE d.Name = 'Zone Ideal Loads Zone Total Heating Energy'"
)
DISTRICTS = [
    ("ES-MAD-BERRUGUETE", "es_mad_berruguete"),
    ("FR-LYO-HAUTCOEURPENTES", "fr_lyo_hautcoeurpentes"),
    ("GB-LDN-STDUNSTANS", "gb_ldn_stdunstans"),
    ("IT-BOL-GALVANI2", "it_bol_galvani2"),
]
COLS = ["district", "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
        "floor_area_m2", "heating_kwh", "eui_heating_kwh_m2", "has_result", "eui_source",
        "undivided_excluded_from_2026-10-01"]
EXTRA = ["tag", "supersedes"]
METRIC = ("space-heating demand only; the EU models are heat-only by design (ideal loads, heating 20 C, "
          "cooling setpoint 50 C = never cools; no lighting/DHW objects, internal gains one lump)")
EUI_DEF = "sum(heating_kWh) / sum(floor_area_m2) over homes with a completed run"
OLD = OUT / "EU11_results_2026-10-06_per_home.csv"

spec = importlib.util.spec_from_file_location("mi", ROOT / "scripts" / "eu21" / "13_model_integrity.py")
mi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mi)


def dumps_php(obj, indent, sep):
    return json.dumps(obj, indent=indent, separators=sep, ensure_ascii=False).replace("/", "\\/")


def idf_floor_area(path):
    p = mi.parse_idf(Path(path).read_text(encoding="utf-8", errors="replace"))
    return sum(mi.poly_area(s[4]) for s in p["surfaces"] if s[1] == "floor" and len(s[4]))


def heating_kwh(out):
    out = Path(out)
    rc = out / "task.rc"
    err = out / "eplusout.err"
    sql = out / "eplusout.sql"
    if not (rc.exists() and err.exists() and sql.exists()):
        return None
    if rc.read_text(encoding="utf-8", errors="replace").strip() != "0":
        return None
    if "Completed Successfully" not in err.read_text(encoding="utf-8", errors="replace"):
        return None
    con = sqlite3.connect(f"file:{sql.as_posix()}?mode=ro", uri=True)
    try:
        v = con.execute(HEATING_SQL).fetchone()[0]
    finally:
        con.close()
    return None if v is None else float(v) * J_TO_KWH


def summarize(df):
    jd, rows = {}, []
    for d, _ in DISTRICTS:
        s = df[df.district == d]
        ok = s[s.has_result]
        fa, hk = round(ok.floor_area_m2.sum(), 3), round(ok.heating_kwh.sum(), 3)
        e = round(ok.heating_kwh.sum() / ok.floor_area_m2.sum(), 6)
        jd[d] = {"homes": len(s), "homes_with_result": len(ok), "floor_area_m2": fa,
                 "heating_kwh": hk, "eui_heating_kwh_m2": e}
        rows.append([d, len(s), len(ok), fa, hk, e])
    ok = df[df.has_result]
    fleet = {"homes": len(df), "homes_with_result": len(ok),
             "floor_area_m2": round(ok.floor_area_m2.sum(), 3),
             "heating_kwh": round(ok.heating_kwh.sum(), 3),
             "eui_heating_kwh_m2": round(ok.heating_kwh.sum() / ok.floor_area_m2.sum(), 6)}
    rows.append(["FLEET", fleet["homes"], fleet["homes_with_result"], fleet["floor_area_m2"],
                 fleet["heating_kwh"], fleet["eui_heating_kwh_m2"]])
    return jd, fleet, rows


def main():
    old = pd.read_csv(OLD, dtype={"building_id": str})
    old["has_result"] = old["has_result"].astype(str) == "True"
    ex = pd.read_csv(PF / "exclude_all_232.csv", dtype=str)
    mf = pd.read_csv(PF / "manifest_all_193.csv", dtype=str)
    exk = set(zip(ex.district, ex.building_id))
    fixk = set(zip(mf.district, mf.building_id))
    oldk = set(zip(old.district, old.building_id))
    skip = exk | fixk
    report = []

    t1 = []
    picks = [("ES-MAD-BERRUGUETE", 3), ("FR-LYO-HAUTCOEURPENTES", 3), ("GB-LDN-STDUNSTANS", 3),
             ("IT-BOL-GALVANI2", 5), ("IT-BOL-GALVANI2", 40)]
    for d, i in picks:
        pr = pd.read_csv(EV / f"{d}_win_2026-10-06" / "prepared_buildings.csv", dtype=str)
        cand = old[(old.district == d) & ~old.apply(lambda r: (r.district, r.building_id) in skip, axis=1)]
        r = cand.iloc[i]
        stem = pr[pr.building_id == r.building_id].stem.iloc[0]
        a = idf_floor_area(EV / f"{d}_win_2026-10-06" / "idfs" / f"{stem}.idf")
        t1.append((d, r.building_id, r.floor_area_m2, round(a, 4), abs(a - r.floor_area_m2) / r.floor_area_m2))
    t1_pass = all(x[4] <= 1e-4 for x in t1)
    report.append(f"1 floor-area formula (rel tol 1e-4): {'PASS' if t1_pass else 'FAIL'}; max rel dev {max(x[4] for x in t1):.2e}; max abs dev {max(abs(x[3]-x[2]) for x in t1):.4f} m2 over {len(t1)} homes")
    if not t1_pass:
        print("\n".join(report))
        raise SystemExit("test 1 failed")

    keep = old[~old.apply(lambda r: (r.district, r.building_id) in exk, axis=1)].copy()
    excl_in_old = old[old.apply(lambda r: (r.district, r.building_id) in exk, axis=1)].groupby("district").size()
    oldidx = old.set_index(["district", "building_id"])

    fixed_info = []
    fallback = []
    for r in mf.itertuples():
        out = RB / "sim_local_2026-10-07" / f"{r.source_run}_{r.district}" / "out" / r.stem
        hk = heating_kwh(out)
        if hk is None:
            for alt in ("j12g", "j12h", "j12r"):
                hk = heating_kwh(RB / "sim_local_2026-10-07" / f"{alt}_{r.district}" / "out" / r.stem)
                if hk is not None:
                    fallback.append((r.district, r.building_id, alt))
                    break
        area = idf_floor_area(r.idf)
        md5_ok = hashlib.md5(Path(r.idf).read_bytes()).hexdigest() == r.md5
        fixed_info.append((r.district, r.building_id, hk, area, md5_ok))
    fi = pd.DataFrame(fixed_info, columns=["district", "building_id", "hk", "area", "md5_ok"])

    merged = {}
    for d, low in DISTRICTS:
        merged[d] = pd.read_csv(EV / f"{d}_merged_win_2026-10-06" / f"{low}_manifest.csv", dtype={"building_id": str}).set_index("building_id")
    added = []
    recs = keep.to_dict("records")
    byk = {(r["district"], r["building_id"]): r for r in recs}
    for r in fi.itertuples():
        k = (r.district, r.building_id)
        if k in byk:
            row = byk[k]
        else:
            m = merged[r.district]
            if r.building_id in m.index:
                s = m.loc[r.building_id]
            else:
                pr = pd.read_csv(EV / f"{r.district}_win_2026-10-06" / "prepared_buildings.csv", dtype=str).set_index("building_id")
                if r.building_id not in pr.index:
                    raise SystemExit(f"STOP: {k} not in 10-06 file, merged manifest or prepared_buildings")
                s = pr.loc[r.building_id]
            row = {"district": r.district, "building_id": r.building_id, "archetype_id": s["archetype_id"],
                   "building_type": s["building_type"], "age_band": s["age_band"],
                   "geometry_outcome": s["geometry_outcome"], "undivided_excluded_from_2026-10-01": False}
            recs.append(row)
            byk[k] = row
            added.append(k)
        if r.hk is not None and r.area > 0:
            row["floor_area_m2"] = round(r.area, 4)
            row["heating_kwh"] = round(r.hk, 6)
            row["eui_heating_kwh_m2"] = round(r.hk / r.area, 6)
            row["has_result"] = True
            row["eui_source"] = EUI_SOURCE
            row["tag"] = TAG
    for r in recs:
        r["supersedes"] = SUPERSEDES
        r.setdefault("tag", "")
    df = pd.DataFrame(recs)
    order = {d: i for i, (d, _) in enumerate(DISTRICTS)}
    df["_o"] = df.district.map(order)
    df["_n"] = np.arange(len(df))
    df = df.sort_values(["_o", "_n"]).drop(columns=["_o", "_n"]).reset_index(drop=True)
    df["has_result"] = df["has_result"].fillna(False).astype(bool)
    df["floor_area_m2"] = df["floor_area_m2"].round(4)
    df["heating_kwh"] = df["heating_kwh"].round(6)
    df["eui_heating_kwh_m2"] = df["eui_heating_kwh_m2"].round(6)

    csv_df = df.copy()
    csv_df["has_result"] = csv_df["has_result"].map({True: "True", False: "False"})
    csv_df["undivided_excluded_from_2026-10-01"] = "False"
    csv_df.to_csv(OUT / f"EU11_results_{STAMP}_per_home.csv", index=False, columns=COLS + EXTRA, lineterminator="\n")
    jrecs = []
    for r in df.to_dict("records"):
        rec = {}
        for c in COLS + EXTRA:
            v = r[c]
            if isinstance(v, float) and v != v:
                v = None
            elif hasattr(v, "item"):
                v = v.item()
            rec[c] = v
        jrecs.append(rec)
    (OUT / f"EU11_results_{STAMP}_per_home.json").write_text(dumps_php(jrecs, 1, (",", ":")), encoding="utf-8")

    jd, fleet, rows = summarize(df)
    with open(OUT / f"EU11_results_{STAMP}_summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["district", "homes", "homes_with_result", "floor_area_m2", "heating_kwh", "eui_heating_kwh_m2"] + EXTRA)
        for r in rows:
            w.writerow(r + [TAG, SUPERSEDES])
    js = {"vintage": VINTAGE, "tag": TAG, "supersedes": SUPERSEDES, "metric": METRIC,
          "eui_definition": EUI_DEF, "districts": jd, "fleet": fleet}
    (OUT / f"EU11_results_{STAMP}_summary.json").write_text(dumps_php(js, 1, (",", ": ")), encoding="utf-8")

    newk = set(zip(df.district, df.building_id))
    leak = len(newk & exk)
    report.append(f"2 excluded homes in new file: {'PASS' if leak == 0 else 'FAIL'}; {leak} of {len(exk)}")
    nd = df.set_index(["district", "building_id"])
    fx = nd.loc[[k for k in fixk if k in nd.index]]
    t3 = len(fx) == 193 and fx.has_result.all() and fx.heating_kwh.notna().all() and (fx.tag == TAG).all()
    report.append(f"3 fixed homes present with result: {'PASS' if t3 else 'FAIL'}; {len(fx)} of 193; has_result {int(fx.has_result.sum())}; heating non-null {int(fx.heating_kwh.notna().sum())}; in 10-06 file {sum(k in oldk for k in fixk)}; added {len(added)}; md5 of simulated IDF ok {int(fi.md5_ok.sum())}")
    per = []
    for d, _ in DISTRICTS:
        per.append(f"{d} {int((old.district == d).sum())}-{int(excl_in_old.get(d, 0))}+{sum(1 for a in added if a[0] == d)}={int((df.district == d).sum())}")
    exp = len(old) - int(excl_in_old.sum()) + len(added)
    report.append(f"4 row count: {'PASS' if len(df) == exp else 'FAIL'}; {len(df)} (4087 - {int(excl_in_old.sum())} excluded present in 10-06 [of {len(exk)} listed] + {len(added)} added); " + "; ".join(per))
    kidx = [k for k in nd.index if k not in fixk and k in oldidx.index]
    kk = nd.loc[kidx]
    ob = oldidx.loc[kidx]
    t5 = all(np.allclose(kk[c].astype(float).values, ob[c].astype(float).values, rtol=0, atol=1e-9, equal_nan=True) for c in ["floor_area_m2", "heating_kwh", "eui_heating_kwh_m2"])
    report.append(f"5 kept non-fixed rows equal 10-06: {'PASS' if t5 else 'FAIL'}; {len(kk)} rows compared")
    pc = pd.read_csv(OUT / f"EU11_results_{STAMP}_per_home.csv", dtype={"building_id": str})
    pc["has_result"] = pc["has_result"].astype(str) == "True"
    jd2, fleet2, rows2 = summarize(pc)
    sc = pd.read_csv(OUT / f"EU11_results_{STAMP}_summary.csv")
    sj = json.loads((OUT / f"EU11_results_{STAMP}_summary.json").read_text(encoding="utf-8"))
    ok6 = True
    for r in rows2:
        c = sc[sc.district == r[0]].iloc[0]
        ok6 &= bool(int(c.homes) == r[1] and int(c.homes_with_result) == r[2] and abs(c.eui_heating_kwh_m2 - r[5]) < 1e-9 and abs(c.heating_kwh - r[4]) < 1e-6)
        src = sj["fleet"] if r[0] == "FLEET" else sj["districts"][r[0]]
        ok6 &= bool(src["homes"] == r[1] and src["homes_with_result"] == r[2] and abs(src["eui_heating_kwh_m2"] - r[5]) < 1e-9)
    report.append(f"6 summary recomputed from per-home equals summary.csv and summary.json: {'PASS' if ok6 else 'FAIL'}")
    ch = []
    for d, _ in DISTRICTS:
        ks = [k for k in fixk if k[0] == d and k in oldidx.index]
        n = oldidx.loc[ks, "eui_heating_kwh_m2"].astype(float)
        a = nd.loc[ks, "eui_heating_kwh_m2"].astype(float)
        da = nd.loc[ks, "floor_area_m2"].sum() - oldidx.loc[ks, "floor_area_m2"].sum()
        ch.append(f"{d} n={len(ks)} mean dEUI {(a - n).mean():+.3f} kWh/m2 ({(a - n).mean() / n.mean() * 100:+.1f} %), total area change {da:+.2f} m2")
    report.append("7 fixed-home EUI change vs 10-06 (director only): " + " | ".join(ch))
    report.append(f"fixed homes whose result came from another run folder than source_run: {fallback}")
    report.append("EUI: " + "; ".join(f"{r[0]} {r[5]:.3f} over {r[2]}/{r[1]}" for r in rows2))

    base = pd.read_csv(RB / "baseline_1006.csv", dtype={"building_id": str})
    res = base[base.cls.isin(["OK", "V3_divided_wrapped_flat", "S1_one_flat_per_floor_by_data"]) & ~(base.building_id == "way/435447773")]
    S = set(zip(res.district, res.building_id)) | fixk
    nores = sorted(k for k in S if k not in newk)
    cnt = {d: sum(1 for k in nores if k[0] == d) for d, _ in DISTRICTS}
    report.append(f"correctly divided set {len(S)}; no result in new file {len(nores)}; by district {cnt}; in S but on the exclude list {sum(1 for k in S if k in exk)}")
    print("\n".join(report))


if __name__ == "__main__":
    main()
