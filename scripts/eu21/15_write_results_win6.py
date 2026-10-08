from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
OUT = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "results"
TAG = "win_2026-10-06"
SUPERSEDES = "2026-09-08"
STAMP = "2026-10-06"
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


def dumps_php(obj, indent, sep):
    return json.dumps(obj, indent=indent, separators=sep, ensure_ascii=False).replace("/", "\\/")


def main():
    frames = []
    for d, low in DISTRICTS:
        m = pd.read_csv(EV / f"{d}_merged_{TAG}" / f"{low}_manifest.csv", dtype={"building_id": str})
        f = pd.DataFrame({
            "district": d,
            "building_id": m["building_id"],
            "archetype_id": m["archetype_id"],
            "building_type": m["building_type"],
            "age_band": m["age_band"],
            "geometry_outcome": m["geometry_outcome"],
            "floor_area_m2": m["floor_area_m2"],
            "heating_kwh": m["heating_kwh"],
            "eui_heating_kwh_m2": m["eui_kwh_m2"],
        })
        f["has_result"] = f["eui_heating_kwh_m2"].notna()
        f["eui_source"] = m["eui_source"]
        f["undivided_excluded_from_2026-10-01"] = False
        frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    df["floor_area_m2"] = df["floor_area_m2"].round(4)
    df["heating_kwh"] = df["heating_kwh"].round(6)
    df["eui_heating_kwh_m2"] = df["eui_heating_kwh_m2"].round(6)
    df["tag"] = TAG
    df["supersedes"] = SUPERSEDES

    csv_df = df.copy()
    csv_df["has_result"] = csv_df["has_result"].map({True: "True", False: "False"})
    csv_df["undivided_excluded_from_2026-10-01"] = "False"
    csv_df.to_csv(OUT / f"EU11_results_{STAMP}_per_home.csv", index=False, columns=COLS + EXTRA,
                  lineterminator="\n")

    recs = []
    for r in df.to_dict("records"):
        rec = {}
        for c in COLS + EXTRA:
            v = r[c]
            if isinstance(v, float) and v != v:
                v = None
            elif hasattr(v, "item"):
                v = v.item()
            rec[c] = v
        recs.append(rec)
    (OUT / f"EU11_results_{STAMP}_per_home.json").write_text(dumps_php(recs, 1, (",", ":")), encoding="utf-8")

    rows = []
    jd = {}
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
    with open(OUT / f"EU11_results_{STAMP}_summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["district", "homes", "homes_with_result", "floor_area_m2", "heating_kwh",
                    "eui_heating_kwh_m2"] + EXTRA)
        for r in rows:
            w.writerow(r + [TAG, SUPERSEDES])
    js = {"vintage": f"{STAMP} (official, in force)", "tag": TAG, "supersedes": SUPERSEDES,
          "metric": METRIC, "eui_definition": EUI_DEF, "districts": jd, "fleet": fleet}
    (OUT / f"EU11_results_{STAMP}_summary.json").write_text(dumps_php(js, 1, (",", ": ")), encoding="utf-8")


if __name__ == "__main__":
    main()
