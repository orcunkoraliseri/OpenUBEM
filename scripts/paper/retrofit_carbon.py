from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("remove_dhw_double_count", ROOT / "scripts" / "paper" / "remove_dhw_double_count.py")
rd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rd)

CMP = ROOT / "openubem" / "outputs" / "comparisons"
FLEET_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
DHW_CSV = CMP / "paper_adopted_fleet_dhw-fix_per_building_2026-10-21.csv"
SUMMARY_JSON = CMP / "paper_dhw-fix_summary_2026-10-21.json"
CASE_CSV = CMP / "paper_scenario_case_list_2026-10-21.csv"
OUT_CSV = CMP / "paper_retrofit_carbon_2026-10-21.csv"

BASELINE = "baseline"
REL_TOL = 1e-6
VINTAGE = ("adopted fleet 2026-09-30 three-rulings set, hot water counted once (D-IMP-05); scenario cells re-run on the adopted "
           "IDFs 2026-10-21 (T16), T13 correction applied to every row")
PER_BUILDING = ["osm_id", "city", "cell", "floor_area_m2", "total_kwh", "gwp_total_kgco2"]
COLUMNS = ["scope", "city", "cell", "population", "buildings_changed", "pooled_eui_kwh_m2", "carbon_t",
           "saving_kwh_m2", "saving_pct", "saving_tco2e", "max_floor_area_rel_diff_changed", "vintage"]


def baseline_from_tables(fleet: pd.DataFrame, dhw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    fleet = fleet.copy()
    dhw = dhw.copy()
    fleet["osm_id"] = fleet["osm_id"].astype(str)
    dhw["osm_id"] = dhw["osm_id"].astype(str)
    merged = fleet[["osm_id", "total_kwh", "floor_area_m2"]].merge(
        dhw[["osm_id", "total_kwh", "dhw_district_removed_eui_kwh_m2"]], on="osm_id", how="left",
        suffixes=("_t01", "_fix"), validate="one_to_one")
    expected = merged["total_kwh_t01"] - merged["dhw_district_removed_eui_kwh_m2"] * merged["floor_area_m2"]
    gap = float(((expected - merged["total_kwh_fix"]).abs() / merged["total_kwh_t01"]).max())
    base = dhw[PER_BUILDING].copy()
    checks = {"rows": int(len(base)), "osm_id_unique": bool(base["osm_id"].is_unique),
              "t01_minus_removed_vs_corrected_max_rel": gap}
    return base, checks


def pooled(frame: pd.DataFrame) -> tuple[float, float]:
    return (float(frame["total_kwh"].sum() / frame["floor_area_m2"].sum()),
            float(frame["gwp_total_kgco2"].sum() / 1000.0))


def baseline_check(base: pd.DataFrame, summary: dict) -> list[str]:
    eui, carbon = pooled(base)
    want_eui = summary["corrected"]["pooled_eui_kwh_m2"]
    want_carbon = summary["corrected"]["carbon_t"]
    want_rows = summary["population"]["buildings"]
    problems = []
    if len(base) != want_rows:
        problems.append(f"baseline rows {len(base)} != {want_rows}")
    if abs(eui - want_eui) > REL_TOL * want_eui:
        problems.append(f"baseline EUI {eui:.6f} != {want_eui}")
    if abs(carbon - want_carbon) > REL_TOL * want_carbon:
        problems.append(f"baseline carbon {carbon:.4f} t != {want_carbon}")
    return problems


def collect(out_dir: Path, cases: pd.DataFrame) -> tuple[dict, list[str]]:
    unchanged: dict[tuple[str, str], bool] = {}
    frames = []
    problems = []
    for cell, stem, osm_id, city, geo in zip(cases["cell"], cases["stem"], cases["osm_id"], cases["city"], cases["geo_cell"]):
        d = out_dir / cell / stem
        if (d / "UNCHANGED").exists():
            unchanged[(cell, str(osm_id))] = True
            continue
        row_csv = d / "row.csv"
        if not row_csv.exists():
            problems.append(f"missing {cell}/{stem}")
            continue
        r = pd.read_csv(row_csv)
        if len(r) != 1 or str(r.loc[0, "parse_status"]) != "success" or int(r.loc[0, "completed"]) != 1:
            problems.append(f"bad row {cell}/{stem}")
            continue
        r["osm_id"] = str(osm_id)
        r["city"] = city
        r["cell"] = geo
        r["measure_cell"] = cell
        frames.append(r)
    rows = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return {"unchanged": unchanged, "rows": rows}, problems


def cell_tables(base: pd.DataFrame, collected: dict, cells: list[str]) -> dict[str, pd.DataFrame]:
    out = {BASELINE: base.assign(changed=0)}
    rows = collected["rows"]
    corrected = pd.DataFrame()
    if len(rows):
        fixed, _ = rd.correct_table(rows)
        corrected = fixed[["osm_id", "measure_cell", "floor_area_m2", "total_kwh", "gwp_total_kgco2"]]
    base_i = base.set_index("osm_id")
    for cell in cells:
        sub = corrected[corrected["measure_cell"] == cell] if len(corrected) else corrected
        frame = base.copy()
        frame["changed"] = 0
        frame["floor_area_base"] = frame["floor_area_m2"]
        if len(sub):
            sub_i = sub.set_index("osm_id")
            idx = frame["osm_id"].isin(sub_i.index)
            for col in ("floor_area_m2", "total_kwh", "gwp_total_kgco2"):
                frame.loc[idx, col] = frame.loc[idx, "osm_id"].map(sub_i[col]).values
            frame.loc[idx, "changed"] = 1
        out[cell] = frame
    return out


def summarise(tables: dict[str, pd.DataFrame], cells: list[str]) -> pd.DataFrame:
    base = tables[BASELINE]
    scopes = [("fleet", "all", None)] + [("city", c, c) for c in sorted(base["city"].unique())]
    rows = []
    for scope, city_name, city in scopes:
        base_sel = base if city is None else base[base["city"] == city]
        b_eui, b_carbon = pooled(base_sel)
        for cell in [BASELINE] + cells:
            t = tables[cell]
            sel = t if city is None else t[t["city"] == city]
            eui, carbon = pooled(sel)
            changed = sel[sel["changed"] == 1]
            if len(changed) and "floor_area_base" in sel.columns:
                rel = float(((changed["floor_area_m2"] - changed["floor_area_base"]).abs() / changed["floor_area_base"]).max())
            else:
                rel = 0.0
            rows.append({
                "scope": scope, "city": city_name, "cell": cell, "population": int(len(sel)),
                "buildings_changed": int(sel["changed"].sum()),
                "pooled_eui_kwh_m2": eui, "carbon_t": carbon,
                "saving_kwh_m2": b_eui - eui, "saving_pct": 100.0 * (b_eui - eui) / b_eui,
                "saving_tco2e": b_carbon - carbon,
                "max_floor_area_rel_diff_changed": rel, "vintage": VINTAGE,
            })
    return pd.DataFrame(rows, columns=COLUMNS)


def run(case_csv: Path, out_dir: Path, fleet_csv: Path, dhw_csv: Path, summary_json: Path, out_csv: Path) -> int:
    fleet = pd.read_csv(fleet_csv, dtype={"osm_id": str})
    dhw = pd.read_csv(dhw_csv, dtype={"osm_id": str})
    summary = json.loads(Path(summary_json).read_text(encoding="utf-8"))
    base, _ = baseline_from_tables(fleet, dhw)
    problems = baseline_check(base, summary)
    if problems:
        print("STOP: " + "; ".join(problems), file=sys.stderr)
        return 1
    cases = pd.read_csv(case_csv, dtype={"osm_id": str})
    cells = list(dict.fromkeys(cases["cell"]))
    collected, missing = collect(Path(out_dir), cases)
    if missing:
        print(f"STOP: {len(missing)} cases without a usable result; first 30:", file=sys.stderr)
        for m in missing[:30]:
            print("  " + m, file=sys.stderr)
        return 2
    tables = cell_tables(base, collected, cells)
    result = summarise(tables, cells)
    result.to_csv(out_csv, index=False)
    print(f"wrote {out_csv} ({len(result)} rows)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", help="local copy of the Speed out/ folder (out/<cell>/<stem>/row.csv or UNCHANGED)")
    ap.add_argument("--baseline-check", action="store_true")
    ap.add_argument("--case-list", default=str(CASE_CSV))
    ap.add_argument("--fleet-csv", default=str(FLEET_CSV))
    ap.add_argument("--dhw-csv", default=str(DHW_CSV))
    ap.add_argument("--summary-json", default=str(SUMMARY_JSON))
    ap.add_argument("--out-csv", default=str(OUT_CSV))
    args = ap.parse_args()
    if args.baseline_check:
        fleet = pd.read_csv(args.fleet_csv, dtype={"osm_id": str})
        dhw = pd.read_csv(args.dhw_csv, dtype={"osm_id": str})
        summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
        base, checks = baseline_from_tables(fleet, dhw)
        eui, carbon = pooled(base)
        problems = baseline_check(base, summary)
        print(f"baseline rows={len(base)} EUI={eui:.4f} carbon_t={carbon:.2f} checks={checks}")
        print("PASS" if not problems else "FAIL " + "; ".join(problems))
        return 1 if problems else 0
    if not args.out_dir:
        ap.error("--out-dir is required unless --baseline-check")
    return run(Path(args.case_list), Path(args.out_dir), Path(args.fleet_csv), Path(args.dhw_csv),
               Path(args.summary_json), Path(args.out_csv))


if __name__ == "__main__":
    raise SystemExit(main())
