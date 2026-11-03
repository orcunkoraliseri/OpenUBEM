from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
G = EV / "geometry_24_2026-10-10"
PF = EV / "rulebook_2026-09-30" / "partner_fixed_homes_2026-10-08"
RES = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "results" / "EU11_results_2026-10-08_per_home.csv"

MAD = ["relation/12582234", "relation/12891867", "relation/13113580", "relation/13381287", "relation/13160790",
       "relation/4835800", "relation/4165178", "relation/5808697", "relation/6382787", "relation/4154505", "way/340701289"]
BOL = ["28025", "28959", "29530", "29719", "30001", "31083", "31363", "32360", "28050", "29109", "30485", "31962", "33359"]
SPEC = [("ES-MAD-BERRUGUETE", MAD), ("IT-BOL-GALVANI2", BOL)]


def ids_in(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return set(pd.read_csv(path, dtype=str)["building_id"])


def main():
    G.mkdir(parents=True, exist_ok=True)
    res = pd.read_csv(RES, dtype=str)
    excl = {
        "on_exclude_4J_madrid": ids_in(G / "exclude_4J_madrid_from_speed.csv"),
        "on_exclude_4J_london_bologna": ids_in(PF / "exclude_4J_london_bologna.csv"),
        "on_exclude_5J_madrid_bologna": ids_in(PF / "exclude_5J_madrid_bologna.csv"),
        "on_exclude_all_232": ids_in(PF / "exclude_all_232.csv"),
    }
    fixed = {}
    for f in ("manifest_4J_london_bologna.csv", "manifest_5J_madrid_bologna.csv", "manifest_all_193.csv"):
        m = pd.read_csv(PF / f, dtype=str)
        for _, r in m.iterrows():
            fixed.setdefault((r["district"], r["building_id"]), []).append((f, r["idf"], r["floor_plan_class"]))
    chk = {}
    for f in (PF / "sidecars_4J" / "per_home_check_2026-10-08.csv", PF / "sidecars_4J_madrid_2026-10-09" / "per_home_check_2026-10-09.csv"):
        if f.is_file():
            for _, r in pd.read_csv(f, dtype=str).iterrows():
                chk[(r["district"], r["building_id"])] = (r.get("status", ""), r.get("worst_outcome", ""), r.get("zones_in_sidecar", ""), r.get("merged_zones", ""), r.get("max_area_dev_m2", ""))
    flat = {}
    for d, tag in (("ES-MAD-BERRUGUETE", "ES-MAD-BERRUGUETE_merged_win_2026-10-06"), ("IT-BOL-GALVANI2", "IT-BOL-GALVANI2_merged_win_2026-10-06")):
        p = EV / tag / "flat_counts_2026-10-06.csv"
        if p.is_file():
            for _, r in pd.read_csv(p, dtype=str).iterrows():
                flat[(d, r["building_id"])] = (r["old_count"], r["new_count"], r["dwellings_source"], r["status"])
    rows = []
    for district, ids in SPEC:
        tree = EV / f"{district}_win_2026-10-06"
        prep = pd.read_csv(tree / "prepared_buildings.csv", dtype=str).set_index("building_id")
        for bid in ids:
            pr = prep.loc[bid]
            stem = pr["stem"]
            idf = tree / "idfs" / f"{stem}.idf"
            lay_path = tree / "layouts" / (bid + ".json" if district.startswith("IT") else bid.replace("/", "/") + ".json")
            lay = json.loads(lay_path.read_text(encoding="utf-8")) if lay_path.is_file() else {}
            rr = res[(res["district"] == district) & (res["building_id"] == bid)]
            fx = fixed.get((district, bid), [])
            ck = chk.get((district, bid), ("", "", "", "", ""))
            fl = flat.get((district, bid), ("", "", "", ""))
            row = {
                "district": district, "building_id": bid, "stem": stem,
                "idf_win_2026_10_06": str(idf.relative_to(ROOT)).replace("\\", "/"),
                "idf_win_exists": idf.is_file(),
                "idf_fixed_home_package": ";".join(sorted({x[1] for x in fx})),
                "fixed_home_floor_plan_class": ";".join(sorted({x[2] for x in fx})),
                "source_tree": pr["source_tree"], "building_type": pr["building_type"], "age_band": pr["age_band"],
                "geometry_outcome": pr["geometry_outcome"], "footprint_fallback_reason": pr.get("fallback_reason", ""),
                "storeys": lay.get("storeys", ""), "scheme": lay.get("scheme", ""),
                "scheme_by_storey": "|".join(map(str, lay.get("scheme_by_storey", []))),
                "idf_reroute_divergence": lay.get("idf_reroute_divergence", ""),
                "dwellings_total": lay.get("dwellings_total", ""), "units_per_floor": lay.get("units_per_floor", ""),
                "partition_audit_passed": (lay.get("partition_audit") or {}).get("passed", ""),
                "gross_footprint_area_m2": pr["gross_footprint_area_m2"], "context_building_count": pr["context_building_count"],
                "flat_old_count": fl[0], "flat_new_count": fl[1], "flat_source": fl[2], "flat_status": fl[3],
                "has_result_10_08": rr["has_result"].iloc[0] if len(rr) else "",
                "eui_heating_10_08": rr["eui_heating_kwh_m2"].iloc[0] if len(rr) else "",
                "sidecar_check_status": ck[0], "sidecar_worst_outcome": ck[1], "sidecar_zones": ck[2], "sidecar_merged_zones": ck[3], "sidecar_max_area_dev_m2": ck[4],
            }
            for k, s in excl.items():
                row[k] = bid in s
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(G / "geometry_24_inventory.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    print(len(df), df["idf_win_exists"].sum())
    print(df[["district", "building_id", "storeys", "scheme", "idf_reroute_divergence", "has_result_10_08", "idf_fixed_home_package", "sidecar_check_status", "on_exclude_4J_madrid", "on_exclude_4J_london_bologna", "on_exclude_5J_madrid_bologna", "on_exclude_all_232"]].to_string())


if __name__ == "__main__":
    main()
