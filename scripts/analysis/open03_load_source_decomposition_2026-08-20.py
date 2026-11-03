"""OPEN-03 -- director CP-2 decomposition: how much of the cross-mode gap is
internal loads, measured rather than inferred.

Joins the layout_assign elasticity run (scale 1.0) against the run-4 auto
results for the same 20 buildings, and splits the sample by whether the
building takes layout_assign's DOE-prototype baseline-IDF path (internal loads
come from the baseline IDF's own densities) or the from-scratch template path
(internal loads come from the archetype load table, identical to auto).

EUI is ABUPS "Total End Uses" / simulated floor area on the layout_assign side.
The auto side uses total_eui_kwh_m2, which is sound there because auto never
writes a zone multiplier > 1 (OPEN-60 is confined to layout_assign).
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ELASTICITY_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open03_load_elasticity.csv"
AUTO_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
OUT_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open03_load_source_decomposition.csv"

PROTOTYPE_PATH_ARCHETYPES = {"SmallOffice", "MediumOffice", "RetailStandalone", "Warehouse"}
HVAC_DAMPING = 0.926


def load_joined() -> pd.DataFrame:
    d = pd.read_csv(ELASTICITY_CSV, dtype={"osm_id": str})
    la = d[d["scale"] == 1.0].copy()
    for c in ["Interior_Lighting", "Interior_Equipment", "Total_End_Uses_kwh"]:
        la[c + "_eui"] = la[c] / la["floor_area_m2"]

    auto = []
    for cell in la["cell"].unique():
        b = pd.read_csv(AUTO_ROOT / cell / "results" / "05_results.csv", dtype={"osm_id": str})
        b["cell"] = cell
        auto.append(b[["cell", "osm_id", "lighting_eui_kwh_m2", "equipment_eui_kwh_m2",
                       "total_eui_kwh_m2", "floor_area_m2"]])
    m = la.merge(pd.concat(auto), on=["cell", "osm_id"], suffixes=("", "_auto"))
    m["load_path"] = np.where(m["archetype_id"].isin(PROTOTYPE_PATH_ARCHETYPES),
                              "prototype_baseline_idf", "from_scratch_template")
    return m


def pooled(df: pd.DataFrame, col: str) -> float:
    return float((df[col] * df["floor_area_m2_auto"]).sum() / df["floor_area_m2_auto"].sum())


def summarise(label: str, sub: pd.DataFrame) -> dict:
    auto_eui = pooled(sub, "total_eui_kwh_m2")
    la_eui = pooled(sub, "Total_End_Uses_kwh_eui")
    d_light = pooled(sub, "lighting_eui_kwh_m2") - pooled(sub, "Interior_Lighting_eui")
    d_equip = pooled(sub, "equipment_eui_kwh_m2") - pooled(sub, "Interior_Equipment_eui")
    gross = d_light + d_equip
    gap_pct = 100.0 * (la_eui - auto_eui) / auto_eui
    explained_pct = 100.0 * gross * HVAC_DAMPING / auto_eui
    return {
        "subset": label,
        "n": len(sub),
        "auto_pooled_eui": round(auto_eui, 2),
        "layout_assign_pooled_eui": round(la_eui, 2),
        "gap_pct": round(gap_pct, 2),
        "d_lighting_kwh_m2": round(d_light, 3),
        "d_equipment_kwh_m2": round(d_equip, 3),
        "gross_internal_load_drop_kwh_m2": round(gross, 3),
        "explained_pct_of_auto_eui": round(explained_pct, 2),
        "share_of_gap_explained_pct": round(100.0 * explained_pct / abs(gap_pct), 1) if gap_pct else None,
    }


def main() -> None:
    m = load_joined()
    rows = [summarise("all_20", m)]
    for path, sub in m.groupby("load_path"):
        rows.append(summarise(path, sub))
    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(out.to_string(index=False))

    per = m[["cell", "osm_id", "archetype_id", "load_path", "floor_area_m2_auto",
             "lighting_eui_kwh_m2", "Interior_Lighting_eui",
             "equipment_eui_kwh_m2", "Interior_Equipment_eui",
             "total_eui_kwh_m2", "Total_End_Uses_kwh_eui"]].copy()
    per["light_ratio_la_over_auto"] = (per["Interior_Lighting_eui"] / per["lighting_eui_kwh_m2"]).round(4)
    per["equip_ratio_la_over_auto"] = (per["Interior_Equipment_eui"] / per["equipment_eui_kwh_m2"]).round(4)
    per.to_csv(OUT_CSV.with_name("open03_load_source_per_building.csv"), index=False)
    print(f"\nwrote {OUT_CSV.name} and open03_load_source_per_building.csv")


if __name__ == "__main__":
    main()
