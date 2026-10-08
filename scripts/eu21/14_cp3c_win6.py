from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
OUT = EV / "cp3c_2026-10-06"
TAG = "win_2026-10-06"
OLD = "2026-09-08"
DISTRICTS = {
    "ES": ("ES-MAD-BERRUGUETE", "es_mad_berruguete"),
    "FR": ("FR-LYO-HAUTCOEURPENTES", "fr_lyo_hautcoeurpentes"),
    "GB": ("GB-LDN-STDUNSTANS", "gb_ldn_stdunstans"),
    "IT": ("IT-BOL-GALVANI2", "it_bol_galvani2"),
}
EXTREME = 300.0
RATIO_LO, RATIO_HI = 0.8, 1.25
MIN_TYPE = 30
I2_TOL = 0.01
CHECK6_EXCEPTIONS = {"97d478bc56840531"}


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx = pd.Series(np.asarray(x)).rank().to_numpy()
    ry = pd.Series(np.asarray(y)).rank().to_numpy()
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def pooled(df):
    d = df[df["eui_kwh_m2"].notna()]
    return float(d["heating_kwh"].sum() / d["floor_area_m2"].sum()), int(len(d)), int(len(df))


def old_manifest(code):
    d, s = DISTRICTS[code]
    return pd.read_csv(EV / f"{d}_merged_{OLD}" / f"{s}_manifest.csv")


def load(code):
    d, s = DISTRICTS[code]
    new = pd.read_csv(EV / f"{d}_merged_{TAG}" / f"{s}_manifest.csv")
    old = old_manifest(code)
    cnt = pd.read_csv(EV / f"{d}_{TAG}" / "dwelling_counts_2026-10-06.csv")
    prep = pd.read_csv(EV / f"{d}_{TAG}" / "prepared_buildings.csv")[["building_id", "stem"]]
    new = new.merge(prep, on="building_id", how="left")
    new = new.merge(cnt[["building_id", "old_count", "new_count"]], on="building_id", how="left")
    new["district"] = d
    new["code"] = code
    o = old[["building_id", "eui_kwh_m2", "heating_kwh", "floor_area_m2"]].rename(
        columns={"eui_kwh_m2": "eui_0908_ref", "heating_kwh": "heating_0908_ref", "floor_area_m2": "area_0908_ref"}
    )
    new = new.merge(o, on="building_id", how="left")
    new["window_per_floor"] = new["window_m2"] / new["floor_area_m2"]
    new["flat_changed"] = new["old_count"] != new["new_count"]
    return new, pooled(old)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames, old_pooled = {}, {}
    for c in DISTRICTS:
        frames[c], old_pooled[c] = load(c)
    allf = pd.concat(frames.values(), ignore_index=True)
    groups = {**frames, "ALL": allf}
    summary = {"tag": TAG, "reference": OLD, "districts": {}}
    c1, c2, c3, c4, c4p, c5, c6 = [], [], [], [], [], [], []

    for g, df in groups.items():
        s = summary["districts"].setdefault(g, {})
        ok = df["eui_kwh_m2"].notna() & (df["eplus_return_code"] == 0) & (df["fatal_errors"].fillna(0) == 0)
        bad = df[~ok]
        s["check1"] = {
            "rows": int(len(df)),
            "completed": int(ok.sum()),
            "failures": bad["stem"].tolist(),
            "pass": bool(len(bad) == 0),
        }
        c1.append(
            {
                "group": g,
                "rows": len(df),
                "completed": int(ok.sum()),
                "failed_named": ";".join(bad["stem"].astype(str)),
                "severe_error_homes": int((df["severe_errors"].fillna(0) > 0).sum()),
            }
        )

        was_hi = df["eui_0908_ref"] > EXTREME
        ext = df[(df["eui_kwh_m2"] > EXTREME) & ~was_hi].copy()
        ext["no_0908_value"] = ext["eui_0908_ref"].isna()
        ext["group"] = g
        s["check2"] = {
            "above_300_new": int((df["eui_kwh_m2"] > EXTREME).sum()),
            "above_300_0908": int(was_hi.sum()),
            "new_extremes": int(len(ext)),
            "new_extremes_without_0908_value": int(ext["no_0908_value"].sum()),
            "pass": "needs_reason" if len(ext) else True,
        }
        c2.append(ext)

        s["check3"] = []
        for t, dt in df[df["eui_kwh_m2"].notna()].groupby("building_type"):
            if len(dt) >= MIN_TYPE:
                r = spearman(dt["window_per_floor"], dt["eui_kwh_m2"])
                c3.append({"group": g, "building_type": t, "n": len(dt), "spearman": r, "pass": bool(r > 0)})
                s["check3"].append({"building_type": t, "n": int(len(dt)), "spearman": r, "pass": bool(r > 0)})
        s["check3_pass"] = all(x["pass"] for x in s["check3"]) if s["check3"] else None

        m = df[df["eui_kwh_m2"].notna() & df["eui_0908_ref"].notna()].copy()
        m["ratio"] = m["eui_kwh_m2"] / m["eui_0908_ref"]
        m["outside"] = (m["ratio"] < RATIO_LO) | (m["ratio"] > RATIO_HI)
        s["check4"] = {}
        for lab, sub in [("all", m), ("flat_changed", m[m["flat_changed"]]), ("flat_same", m[~m["flat_changed"]])]:
            row = {
                "group": g,
                "split": lab,
                "n": int(len(sub)),
                "median_ratio": float(sub["ratio"].median()) if len(sub) else float("nan"),
                "n_outside": int(sub["outside"].sum()),
                "share_outside": float(sub["outside"].mean()) if len(sub) else float("nan"),
                "n_below": int((sub["ratio"] < RATIO_LO).sum()),
                "n_above": int((sub["ratio"] > RATIO_HI).sum()),
            }
            c4.append(row)
            s["check4"][lab] = row
        pn, nn, tn = pooled(df)
        if g == "ALL":
            po = pooled(pd.concat([old_manifest(c) for c in DISTRICTS], ignore_index=True))
        else:
            po = old_pooled[g]
        pm_new = float(m["heating_kwh"].sum() / m["floor_area_m2"].sum())
        pm_old = float(m["heating_0908_ref"].sum() / m["area_0908_ref"].sum())
        pr = {
            "group": g,
            "new_pooled": pn,
            "new_n_with_eui": nn,
            "new_n_rows": tn,
            "old_pooled": po[0],
            "old_n_with_eui": po[1],
            "old_n_rows": po[2],
            "change_pct": 100 * (pn / po[0] - 1),
            "matched_n": int(len(m)),
            "matched_new": pm_new,
            "matched_old": pm_old,
            "matched_change_pct": 100 * (pm_new / pm_old - 1),
        }
        c4p.append(pr)
        s["pooled"] = pr

        f283 = df[df["outdoor_wall_m2"].fillna(1) <= 0.001].copy()
        f283["group"] = g
        c5.append(
            f283[["group", "building_id", "stem", "building_type", "floor_area_m2", "window_m2", "outdoor_wall_m2", "eui_kwh_m2", "eui_0908_ref"]]
        )
        s["check5"] = {"homes_no_outdoor_wall": int(len(f283)), "of_rows": int(len(df))}

    for c, (d, _) in DISTRICTS.items():
        ig = pd.read_csv(EV / "integrity_2026-10-02" / f"{d}_{TAG}_integrity.csv")
        ig["c6a"] = ig["I1_pass"].astype(str) == "True"
        ig["c6b"] = pd.to_numeric(ig["I2_value"], errors="coerce") <= I2_TOL
        ig["code"] = c
        ig["exception"] = ig["stem"].isin(CHECK6_EXCEPTIONS)
        ig["fail"] = ~(ig["c6a"] & ig["c6b"])
        c6.append(ig[ig["fail"]][["code", "stem", "storey_source", "storeys_ref", "I1_value", "c6a", "I2_value", "c6b", "exception"]])
        summary["districts"][c]["check6"] = {
            "stems": int(len(ig)),
            "fails": int(ig["fail"].sum()),
            "fails_excluding_named_exception": int((ig["fail"] & ~ig["exception"]).sum()),
            "failing_stems": ig[ig["fail"]]["stem"].tolist(),
            "a_fail": int((~ig["c6a"]).sum()),
            "b_fail": int((~ig["c6b"]).sum()),
        }
    c6d = pd.concat(c6, ignore_index=True)
    summary["districts"]["ALL"]["check6"] = {
        "stems": sum(summary["districts"][c]["check6"]["stems"] for c in DISTRICTS),
        "fails": int(len(c6d)),
        "fails_excluding_named_exception": int((~c6d["exception"]).sum()),
        "failing_stems": c6d["stem"].tolist(),
    }

    pd.DataFrame(c1).to_csv(OUT / "check1_run_status.csv", index=False)
    cols2 = [
        "group", "building_id", "stem", "building_type", "eui_kwh_m2", "eui_0908_ref", "no_0908_value",
        "floor_area_m2", "window_m2", "outdoor_wall_m2", "share_achieved", "window_per_floor",
        "old_count", "new_count", "dwellings_used",
    ]
    pd.concat(c2, ignore_index=True)[cols2].to_csv(OUT / "check2_new_extremes.csv", index=False)
    pd.DataFrame(c3).to_csv(OUT / "check3_spearman.csv", index=False)
    pd.DataFrame(c4).to_csv(OUT / "check4_ratio_split.csv", index=False)
    pd.DataFrame(c4p).to_csv(OUT / "check4_pooled.csv", index=False)
    pd.concat(c5, ignore_index=True).to_csv(OUT / "check5_finding283.csv", index=False)
    c6d.to_csv(OUT / "check6_storey_fails.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
