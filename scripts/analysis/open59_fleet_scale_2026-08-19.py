"""OPEN-59 T01: fleet-scale measurement of Unknown vs classified gap on run-4.

Reads all twelve run-4 cell results (results/05_results.csv, note the
results/ subdirectory per F2), splits by archetype_id == 'OpenUBEMUnknown',
and reports per-cell and fleet-wide: n, floor-area share, pooled EUI, and
median per-building total plus end-use columns.

Outputs:
  extra measurement doc content printed to stdout (executor writes the .md)
  openubem/outputs/comparisons/open59_unknown_gap_fleet.csv
"""
import pandas as pd
from pathlib import Path

RUN4_ROOT = Path(r"C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet4")
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

END_USE_COLS = {
    "total": "total_eui_kwh_m2",
    "heating": "heating_eui_kwh_m2",
    "cooling": "cooling_eui_kwh_m2",
    "lighting": "lighting_eui_kwh_m2",
    "equipment": "equipment_eui_kwh_m2",
    "dhw": "dhw_eui_kwh_m2",
    "fans": "fans_eui_kwh_m2",
    "pumps": "pumps_eui_kwh_m2",
}


def load_cell(cell):
    p = RUN4_ROOT / cell / "results" / "05_results.csv"
    df = pd.read_csv(p)
    df = df[df["simulation_status"] == "success"].copy()
    df["cell"] = cell
    df["is_unknown"] = df["archetype_id"] == "OpenUBEMUnknown"
    return df


def pooled_eui(df, col="total_eui_kwh_m2"):
    area = df["floor_area_m2"]
    val = df[col]
    denom = area.sum()
    if denom == 0:
        return float("nan")
    return (val * area).sum() / denom


def summarize(df, label):
    n = len(df)
    row = {"group": label, "n": n}
    row["floor_area_m2_sum"] = df["floor_area_m2"].sum()
    row["pooled_total_eui"] = pooled_eui(df, "total_eui_kwh_m2")
    for name, col in END_USE_COLS.items():
        row[f"median_{name}"] = df[col].median() if n else float("nan")
    return row


def main():
    frames = []
    per_cell_rows = []
    for cell in CELLS:
        df = load_cell(cell)
        frames.append(df)
        unk = df[df["is_unknown"]]
        cls = df[~df["is_unknown"]]
        total_area = df["floor_area_m2"].sum()
        unk_area_share = unk["floor_area_m2"].sum() / total_area if total_area else float("nan")
        r_unk = summarize(unk, f"{cell}:unknown")
        r_unk["floor_area_share_of_cell"] = unk_area_share
        r_cls = summarize(cls, f"{cell}:classified")
        r_cls["floor_area_share_of_cell"] = 1 - unk_area_share if total_area else float("nan")
        per_cell_rows.append(r_unk)
        per_cell_rows.append(r_cls)

    fleet = pd.concat(frames, ignore_index=True)
    fleet_unk = fleet[fleet["is_unknown"]]
    fleet_cls = fleet[~fleet["is_unknown"]]
    total_area = fleet["floor_area_m2"].sum()
    r_unk = summarize(fleet_unk, "FLEET:unknown")
    r_unk["floor_area_share_of_cell"] = fleet_unk["floor_area_m2"].sum() / total_area
    r_cls = summarize(fleet_cls, "FLEET:classified")
    r_cls["floor_area_share_of_cell"] = fleet_cls["floor_area_m2"].sum() / total_area
    per_cell_rows.append(r_unk)
    per_cell_rows.append(r_cls)

    out = pd.DataFrame(per_cell_rows)
    out_path = Path(r"C:/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/comparisons/open59_unknown_gap_fleet.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print("=== CONTROL CHECKS ===")
    ns = load_cell("nyc_suburban")
    print("nyc_suburban n unknown:", (ns["archetype_id"] == "OpenUBEMUnknown").sum())
    print("nyc_suburban n classified:", (ns["archetype_id"] != "OpenUBEMUnknown").sum())
    print("fleet unknown n:", len(fleet_unk))
    print("fleet unknown pooled total EUI:", pooled_eui(fleet_unk, "total_eui_kwh_m2"))
    print("fleet classified pooled total EUI:", pooled_eui(fleet_cls, "total_eui_kwh_m2"))

    print()
    print("=== NYC_SUBURBAN OWN-CELL CONTROL (median per-building) ===")
    ns_unk = ns[ns["archetype_id"] == "OpenUBEMUnknown"]
    ns_cls = ns[ns["archetype_id"] != "OpenUBEMUnknown"]
    for name, col in END_USE_COLS.items():
        print(f"{name}: unknown median={ns_unk[col].median():.2f}  classified median={ns_cls[col].median():.2f}")

    print()
    print("=== PER-CELL / FLEET TABLE ===")
    with pd.option_context("display.max_columns", None, "display.width", 220):
        print(out.to_string(index=False))


if __name__ == "__main__":
    main()
