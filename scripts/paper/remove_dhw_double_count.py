from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.results.carbon import compute_gwp

_spec = importlib.util.spec_from_file_location(
    "build_adopted_fleet_table", ROOT / "scripts" / "paper" / "build_adopted_fleet_table.py")
base_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base_mod)

CMP = base_mod.CMP
T01_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
OUT_CSV = CMP / "paper_adopted_fleet_dhw-fix_per_building_2026-10-21.csv"
OUT_JSON = CMP / "paper_dhw-fix_summary_2026-10-21.json"
STATE_OF = {"nyc": "NY", "la": "CA", "austin": "TX"}
F_DH = 0.226

CARBON_COLS = [
    "dhw_gas_eui_kwh_m2", "dhw_elec_eui_kwh_m2", "dhw_district_eui_kwh_m2",
    "cooling_district_eui_kwh_m2", "heating_district_eui_kwh_m2", "fans_district_eui_kwh_m2",
    "pumps_district_eui_kwh_m2", "refrigeration_district_eui_kwh_m2", "lighting_district_eui_kwh_m2",
    "equipment_district_eui_kwh_m2", "exterior_lighting_eui_kwh_m2", "exterior_equipment_eui_kwh_m2",
    "heat_rejection_eui_kwh_m2", "humidification_eui_kwh_m2", "heat_recovery_eui_kwh_m2",
    "generators_eui_kwh_m2", "elevators_eui_kwh_m2",
]
KEEP_FULL = base_mod.KEEP + [c for c in CARBON_COLS if c not in base_mod.KEEP]
OUT_COLS = base_mod.KEEP + ["source", "dhw_district_removed_eui_kwh_m2"]


def _gwp_kg(row: pd.Series, state: str) -> dict:
    return compute_gwp(row, state)


def correct_table(fleet: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = fleet.copy().reset_index(drop=True)
    out["dhw_district_eui_kwh_m2"] = out["dhw_district_eui_kwh_m2"].fillna(0.0)
    dd = out["dhw_district_eui_kwh_m2"].astype(float)
    fa = out["floor_area_m2"].astype(float)
    orig_total_kwh = out["total_kwh"].astype(float).copy()
    orig_total_eui = out["total_eui_kwh_m2"].astype(float).copy()
    orig_dhw = out["dhw_eui_kwh_m2"].astype(float).copy()

    orig_gwp_kg = []
    orig_terms = []
    for _, r in out.iterrows():
        g = _gwp_kg(r, STATE_OF[r["city"]])
        orig_gwp_kg.append(g["gwp_total_kgco2_m2"] * r["floor_area_m2"])
        orig_terms.append(g)

    fixed = out.copy()
    fixed["dhw_district_eui_kwh_m2"] = 0.0
    fixed["dhw_eui_kwh_m2"] = orig_dhw - dd
    fixed["total_eui_kwh_m2"] = orig_total_eui - dd
    fixed["total_kwh"] = orig_total_kwh - dd * fa
    new_gwp_kg = []
    new_terms = []
    for _, r in fixed.iterrows():
        g = _gwp_kg(r, STATE_OF[r["city"]])
        new_gwp_kg.append(g["gwp_total_kgco2_m2"] * r["floor_area_m2"])
        new_terms.append(g)
    fixed["gwp_total_kgco2"] = new_gwp_kg
    fixed["dhw_district_removed_eui_kwh_m2"] = dd

    term_keys = [k for k in orig_terms[0] if k != "gwp_dhw_kgco2_m2" and k != "gwp_total_kgco2_m2"]
    other_max = 0.0
    for a, b in zip(orig_terms, new_terms):
        for k in term_keys:
            other_max = max(other_max, abs(a[k] - b[k]))

    checks = {
        "max_abs_diff_unchanged_carbon_terms_kg_m2": other_max,
        "max_abs_diff_recomputed_vs_stored_carbon_kg": float(
            (pd.Series(orig_gwp_kg) - out["gwp_total_kgco2"].astype(float)).abs().max()),
        "max_abs_eui_drop_vs_removed": float(
            ((orig_total_eui - fixed["total_eui_kwh_m2"]) - fixed["dhw_district_removed_eui_kwh_m2"]).abs().max()),
        "dhw_district_missing_rows": int(fleet["dhw_district_eui_kwh_m2"].isna().sum()),
    }
    return fixed, checks


def pooled(fleet: pd.DataFrame) -> tuple[float, float]:
    return (float(fleet["total_kwh"].sum() / fleet["floor_area_m2"].sum()),
            float(fleet["gwp_total_kgco2"].sum() / 1000.0))


def put_back(fixed: pd.DataFrame) -> tuple[float, float]:
    dd = fixed["dhw_district_removed_eui_kwh_m2"]
    fa = fixed["floor_area_m2"]
    kwh = (fixed["total_kwh"] + dd * fa).sum()
    kg = (fixed["gwp_total_kgco2"] + dd * fa * F_DH).sum()
    return float(kwh / fa.sum()), float(kg / 1000.0)


def share_by_city(fixed: pd.DataFrame) -> dict:
    out = {}
    dd_kwh = fixed["dhw_district_removed_eui_kwh_m2"] * fixed["floor_area_m2"]
    orig = fixed["total_kwh"] + dd_kwh
    for city, g in fixed.groupby("city"):
        idx = g.index
        out[city] = {
            "buildings": int(len(g)),
            "pooled_eui_before": round(float(orig[idx].sum() / g["floor_area_m2"].sum()), 4),
            "pooled_eui_after": round(float(g["total_kwh"].sum() / g["floor_area_m2"].sum()), 4),
            "share_of_total_energy_removed_pct": round(float(dd_kwh[idx].sum() / orig[idx].sum() * 100.0), 3),
        }
    return out


def main() -> None:
    base = pd.read_csv(base_mod.BASE_CSV)
    t35 = base_mod.select_open35(pd.read_csv(base_mod.OPEN35_CSV))
    c38 = base_mod.select_open38(pd.read_csv(base_mod.OPEN38_CSV))
    fleet = base_mod.apply_overlays(base, t35, c38, keep=KEEP_FULL)
    fleet = fleet.sort_values(["cell", "osm_id"]).reset_index(drop=True)
    t01 = pd.read_csv(T01_CSV, dtype={"osm_id": str})
    fleet["osm_id"] = fleet["osm_id"].astype(str)
    fixed, checks = correct_table(fleet)

    eui_before, carbon_before = base_mod.pooled(fleet)
    eui_after, carbon_after = pooled(fixed)
    eui_pb, carbon_pb = put_back(fixed)
    ref = json.loads(base_mod.SUMMARY_JSON.read_text())

    t01i = t01.set_index("osm_id")
    fi = fixed.set_index("osm_id")
    t01_gap = float((t01i["gwp_total_kgco2"] - (fi["gwp_total_kgco2"] + fi["dhw_district_removed_eui_kwh_m2"]
                                                  * fi["floor_area_m2"] * F_DH)).abs().max())

    fixed[OUT_COLS].to_csv(OUT_CSV, index=False)

    summary = {
        "population": {"buildings": int(len(fixed)), "unique_osm_id": bool(fixed["osm_id"].is_unique),
                       "cities": {c: int(n) for c, n in fixed["city"].value_counts().items()}},
        "source_vintage": "adopted fleet 2026-09-30 (three rulings), T01 table of 2026-10-21; district hot-water column removed",
        "adopted_before": {"pooled_eui_kwh_m2": round(eui_before, 4), "carbon_t": round(carbon_before, 2),
                           "reference_pooled_eui_c2": ref["pooled_eui_c2"], "reference_carbon_t_c2": ref["carbon_t_c2"]},
        "corrected": {"pooled_eui_kwh_m2": round(eui_after, 4), "carbon_t": round(carbon_after, 2)},
        "district_part_put_back": {"pooled_eui_kwh_m2": round(eui_pb, 4), "carbon_t": round(carbon_pb, 2)},
        "removed": {"pooled_eui_kwh_m2": round(eui_before - eui_after, 4),
                    "carbon_t": round(carbon_before - carbon_after, 2)},
        "share_removed_by_city": share_by_city(fixed),
        "checks": {**checks, "max_abs_diff_put_back_carbon_vs_T01_kg": t01_gap},
        "carbon_method": "openubem.results.carbon.compute_gwp on the corrected row (dhw_district_eui_kwh_m2 = 0), "
                         "state NY / CA / TX by city, times floor area",
        "note": "The removed copy of the hot-water draw also gave room heat gains (openubem/idf/dhw.py, WaterUse:Equipment "
                "sensible and latent fractions); those gains are still inside the saved heating and cooling.",
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("rows", len(fixed), "unique", fixed["osm_id"].is_unique)
    print("before", round(eui_before, 4), round(carbon_before, 2))
    print("after", round(eui_after, 4), round(carbon_after, 2))
    print("put back", round(eui_pb, 4), round(carbon_pb, 2))
    print(json.dumps(summary["share_removed_by_city"], indent=1))
    print(json.dumps(summary["checks"], indent=1))


if __name__ == "__main__":
    main()
