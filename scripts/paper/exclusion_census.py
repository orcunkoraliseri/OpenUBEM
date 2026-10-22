from __future__ import annotations

import glob
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
EVID = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
RES = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "results"
FLEET_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
CENSUS_CSV = CMP / "open61_census_fleet.csv"
OPEN66_CSV = CMP / "open66_zoneless_diagnosis_2026-09-29.csv"
DIAG_CSV = CMP / "open38_diagnosis_2026-09-30.csv"
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE_elevrb"
RULEBOOK = EVID / "rulebook_2026-09-30"
EXCLUDE_232 = RULEBOOK / "partner_fixed_homes_2026-10-08" / "exclude_all_232.csv"
BASELINE_1006 = RULEBOOK / "baseline_1006.csv"
OUT_CSV = CMP / "paper_exclusion_census_2026-10-21.csv"

FOUR = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]
SIX = ["CA-MTL-PLATEAU", "AM-EVN-NORNORK", "ZA-CPT-WOODSTOCK", "FI-HEL-KALLIO", "AT-VIE-RUDOLFSHEIM",
       "HU-BUD-ERZSEBETVAROS"]
COLUMNS = ["site", "scope", "buildings_in", "buildings_in_result", "buildings_left_out", "row_type", "reason",
           "n_reason", "left_out_floor_area_m2", "left_out_floor_area_known_n", "left_out_floor_area_estimated_n", "result_floor_area_m2",
           "left_out_area_share_pct", "reason_source", "vintage"]


def us_reason(row: pd.Series, zoneless: dict, diag: dict) -> tuple[str, str]:
    oid = row["osm_id"]
    if oid in zoneless:
        return ("zones lost after the layout step failed (intersect_match), run parsed with no zones",
                "open66_zoneless_diagnosis_2026-09-29.csv")
    if oid in diag:
        return diag[oid], "open38_diagnosis_2026-09-30.csv (auto mode)"
    if row["status"] == "not_simulated_upstream_excluded_from_census_population":
        return "not simulated upstream, excluded from the census population", "open61_census_fleet.csv"
    if str(row.get("parsed_parse_status")) == "failed_zone_mismatch":
        return "parse failed: zone count mismatch (found 0 zones)", "open61_census_fleet.csv"
    return "no recorded reason", "none"


def us_left_out(fleet: pd.DataFrame) -> pd.DataFrame:
    census = pd.read_csv(CENSUS_CSV)
    out = census[~census["osm_id"].isin(fleet["osm_id"])].copy()
    z = pd.read_csv(OPEN66_CSV)
    zoneless = dict(zip(z["osm_id"], z["cause"]))
    d = pd.read_csv(DIAG_CSV)
    d = d[(d["mode"] == "auto") & (d["new_status"] != "success")]
    diag = {}
    for r in d.itertuples():
        cause = r.cause_class if isinstance(r.cause_class, str) else "cause not classified"
        diag[r.osm_id] = f"{r.new_status}: {cause}"
    reasons = out.apply(lambda r: us_reason(r, zoneless, diag), axis=1)
    out["reason"] = [x[0] for x in reasons]
    out["reason_source"] = [x[1] for x in reasons]
    area = out["recorded_floor_area_m2"].fillna(out["parsed_floor_area_m2"])
    levels = pd.concat([pd.read_csv(f, usecols=["osm_id", "footprint_area_m2", "levels"])
                        for f in sorted(glob.glob(str(PHASEE / "*" / "05_results.csv")))]).set_index("osm_id")
    estimate = out["osm_id"].map(levels["footprint_area_m2"] * levels["levels"])
    out["floor_area_estimated"] = area.isna() & estimate.notna()
    out["floor_area_m2"] = area.fillna(estimate)
    return out[["cell", "osm_id", "archetype_id", "reason", "reason_source", "floor_area_m2", "floor_area_estimated"]]


def long_rows(site: str, scope: str, n_in: int, n_result: int, left: pd.DataFrame, result_area: float,
              vintage: str) -> list[dict]:
    known = left["floor_area_m2"].notna()
    est = left["floor_area_estimated"] if "floor_area_estimated" in left else pd.Series(False, index=left.index)
    total_area = float(left["floor_area_m2"].sum())
    denom = result_area + total_area
    base = dict(site=site, scope=scope, buildings_in=n_in, buildings_in_result=n_result,
                buildings_left_out=len(left), result_floor_area_m2=round(result_area, 3), vintage=vintage)
    rows = [dict(base, row_type="site_total", reason="ALL", n_reason=len(left),
                 left_out_floor_area_m2=round(total_area, 3), left_out_floor_area_known_n=int(known.sum()),
                 left_out_floor_area_estimated_n=int(est.sum()),
                 left_out_area_share_pct=round(100 * total_area / denom, 3) if denom else None,
                 reason_source="")]
    for (reason, src), g in left.groupby(["reason", "reason_source"]):
        a = float(g["floor_area_m2"].sum())
        rows.append(dict(base, row_type="reason", reason=reason, n_reason=len(g),
                         left_out_floor_area_m2=round(a, 3),
                         left_out_floor_area_known_n=int(g["floor_area_m2"].notna().sum()),
                         left_out_floor_area_estimated_n=int(est.loc[g.index].sum()),
                         left_out_area_share_pct=round(100 * a / denom, 3) if denom else None,
                         reason_source=src))
    return rows


def area_lookup(site: str) -> pd.Series:
    frames = []
    pats = [str(EVID / f"{site}*" / "prepared_buildings.csv"), str(EVID / f"{site}*" / "*manifest*.csv")]
    for f in [p for pat in pats for p in glob.glob(pat)]:
        try:
            x = pd.read_csv(f, usecols=lambda c: c in ("building_id", "floor_area_m2"))
        except ValueError:
            continue
        if {"building_id", "floor_area_m2"} <= set(x.columns):
            frames.append(x)
    if not frames:
        return pd.Series(dtype=float)
    c = pd.concat(frames)
    c["building_id"] = c["building_id"].astype(str)
    return c.groupby("building_id")["floor_area_m2"].median()


def four_district_rows() -> list[dict]:
    ex = pd.read_csv(EXCLUDE_232, dtype={"building_id": str})
    base = pd.read_csv(BASELINE_1006, dtype={"building_id": str})
    p6 = pd.read_csv(RES / "EU11_results_2026-10-06_per_home.csv", dtype={"building_id": str})
    summ = json.loads((RES / "EU11_results_2026-10-08_summary.json").read_text())["districts"]
    rows = []
    for site in FOUR:
        left = ex[ex["district"] == site].copy()
        a6 = p6[p6["district"] == site].set_index("building_id")["floor_area_m2"]
        look = area_lookup(site)
        left["floor_area_m2"] = left["building_id"].map(a6)
        left["floor_area_m2"] = left["floor_area_m2"].fillna(left["building_id"].map(look))
        left["reason"] = left["floor_plan_class"]
        left["reason_source"] = "exclude_all_232.csv (floor_plan_class from the division checks)"
        n_in = int((base["district"] == site).sum())
        s = summ[site]
        rows += long_rows(site, "international", n_in, s["homes_with_result"], left, s["floor_area_m2"],
                          "2026-10-08")
    return rows


def six_district_rows() -> list[dict]:
    rows = []
    for site in SIX:
        sj = glob.glob(str(RES / f"EU22_results_{site}_*_summary.json"))[0]
        s = json.loads(Path(sj).read_text())
        dist = s["districts"][site]
        win = EVID / f"{site}_{s['tag']}"
        left = pd.read_csv(win / "left_out.csv", dtype={"building_id": str})
        classes = pd.read_csv(win / "division_classes.csv", dtype={"building_id": str})
        look = area_lookup(site)
        left["floor_area_m2"] = left["building_id"].map(look)
        left["reason"] = left["cls"]
        left["reason_source"] = "left_out.csv (cls from the division checks)"
        rows += long_rows(site, "international", len(classes), dist["homes_with_result"], left,
                          dist["floor_area_m2"], s["tag"].replace("win_", ""))
    return rows


def us_rows() -> list[dict]:
    fleet = pd.read_csv(FLEET_CSV)
    left = us_left_out(fleet)
    census_n = len(pd.read_csv(CENSUS_CSV, usecols=["osm_id"]))
    return long_rows("US-12-cells", "united_states", census_n, len(fleet), left,
                     float(fleet["floor_area_m2"].sum()), "2026-09-30")


def main() -> None:
    rows = us_rows() + four_district_rows() + six_district_rows()
    df = pd.DataFrame(rows)[COLUMNS]
    df.to_csv(OUT_CSV, index=False)
    t = df[df["row_type"] == "site_total"]
    print(t[["site", "buildings_in", "buildings_in_result", "buildings_left_out", "left_out_floor_area_known_n",
             "left_out_floor_area_m2", "left_out_area_share_pct"]].to_string(index=False))
    print("rows", len(df))


if __name__ == "__main__":
    main()
