"""B00 -- Coverage census (read-only measurement, no production code).

Joins the 8,160-row phaseE fleet's `levels` (num_floors) against A1's per-archetype
geometric prototype storey count (`num_modelled_storeys`) and classifies every
building as taller / equal / shorter than its prototype, fleet-wide and for the
<500 m2 subset, broken down by archetype.

Archetypes with no `layout_assign` baseline mapping (Courthouse, OpenUBEMUnknown --
see openubem/geometry/layout_assigner.py ARCHETYPE_IDF_MAP comment) are reported as
a separate `no_baseline` bucket, never silently folded into "shorter" (rule 6: a
zero/absence must be reported as what it is, not guessed into an existing bucket).

For MidriseApartment and HighriseApartment, also reports the alternate registry-derived
n_proto (E-LA-26: geometry says 3 bands, registry implies 4 and 10) as a parallel
column -- both readings are reported, neither is silently picked.
"""
import csv
from pathlib import Path
import pandas as pd

PHASE_E_PATH = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_RESULTS\OpenUBEM_results_hvacServiceLoads\csv\phaseE_all_cells_results.csv")
A1_PATH = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results\a1_prototype_storey_structure.csv")

OUT_DIR_1 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")
OUT_DIR_2 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")

# E-LA-26 registry-derived alternate n_proto for the two apartment archetypes
# (registry_baseline_area_m2 / avg_storey_plate_area_m2 from a1_prototype_storey_structure.csv):
# MidriseApartment: 3135.0 / 783.65 = 4 ; HighriseApartment: 7835.0 / 783.65 = 10
REGISTRY_N_PROTO = {
    "MidriseApartment": 4,
    "HighriseApartment": 10,
}


def classify(n_real, n_proto):
    if n_real > n_proto:
        return "taller"
    elif n_real == n_proto:
        return "equal"
    else:
        return "shorter"


def main():
    fleet = pd.read_csv(PHASE_E_PATH)
    total_fleet = len(fleet)
    assert total_fleet == 8160, f"expected 8160 fleet rows, got {total_fleet}"

    fleet["floor_area_m2"] = fleet["footprint_area_m2"] * fleet["levels"]
    fleet["is_under_500m2"] = fleet["floor_area_m2"] < 500.0

    a1 = pd.read_csv(A1_PATH)
    n_proto_geom = dict(zip(a1["primary_archetype"], a1["num_modelled_storeys"]))

    def geom_n_proto(archetype_id):
        return n_proto_geom.get(archetype_id)

    fleet["n_proto_geometric"] = fleet["archetype_id"].map(geom_n_proto)
    fleet["has_baseline"] = fleet["n_proto_geometric"].notna()

    def classify_row(row):
        if not row["has_baseline"]:
            return "no_baseline"
        return classify(row["levels"], row["n_proto_geometric"])

    fleet["category_geometric"] = fleet.apply(classify_row, axis=1)

    # E-LA-26 alternate registry reading, apartment archetypes only
    def registry_classify_row(row):
        if row["archetype_id"] not in REGISTRY_N_PROTO:
            return None
        return classify(row["levels"], REGISTRY_N_PROTO[row["archetype_id"]])

    fleet["category_registry_alt"] = fleet.apply(registry_classify_row, axis=1)

    # ---- Fleet-wide summary ----
    summary_rows = []

    def add_summary(group_type, group_name, subdf):
        n = len(subdf)
        counts = subdf["category_geometric"].value_counts().to_dict()
        taller = counts.get("taller", 0)
        equal = counts.get("equal", 0)
        shorter = counts.get("shorter", 0)
        no_baseline = counts.get("no_baseline", 0)
        applicable = taller + equal + shorter
        summary_rows.append({
            "group_type": group_type,
            "group_name": group_name,
            "total_buildings": n,
            "taller_count": taller,
            "equal_count": equal,
            "shorter_count": shorter,
            "no_baseline_count": no_baseline,
            "applicable_count": applicable,
            "taller_pct_of_total": round(taller / n * 100.0, 2) if n else None,
            "taller_pct_of_applicable": round(taller / applicable * 100.0, 2) if applicable else None,
        })

    add_summary("Overall Fleet", "All 12 Cells", fleet)
    fleet_u500 = fleet[fleet["is_under_500m2"]]
    add_summary("Subset <500m2", "Buildings <500m2 Floor Area", fleet_u500)

    # ---- By archetype (fleet-wide) ----
    for arch_id, adf in fleet.groupby("archetype_id"):
        add_summary("By Archetype (fleet-wide)", arch_id, adf)

    # ---- By archetype (<500m2 subset) ----
    for arch_id, adf in fleet_u500.groupby("archetype_id"):
        add_summary("By Archetype (<500m2 subset)", arch_id, adf)

    summary_fieldnames = [
        "group_type", "group_name", "total_buildings",
        "taller_count", "equal_count", "shorter_count", "no_baseline_count",
        "applicable_count", "taller_pct_of_total", "taller_pct_of_applicable",
    ]

    # ---- E-LA-26 alternate registry-reading summary, apartment archetypes only ----
    alt_rows = []

    def add_alt_summary(group_type, group_name, subdf):
        n = len(subdf)
        counts = subdf["category_registry_alt"].value_counts().to_dict()
        taller = counts.get("taller", 0)
        equal = counts.get("equal", 0)
        shorter = counts.get("shorter", 0)
        alt_rows.append({
            "group_type": group_type,
            "group_name": group_name,
            "total_buildings": n,
            "n_proto_registry": REGISTRY_N_PROTO.get(subdf["archetype_id"].iloc[0]) if n else None,
            "taller_count": taller,
            "equal_count": equal,
            "shorter_count": shorter,
            "taller_pct_of_total": round(taller / n * 100.0, 2) if n else None,
        })

    for arch_id in REGISTRY_N_PROTO:
        adf = fleet[fleet["archetype_id"] == arch_id]
        add_alt_summary("By Archetype (fleet-wide, registry n_proto)", arch_id, adf)
        adf_u500 = fleet_u500[fleet_u500["archetype_id"] == arch_id]
        add_alt_summary("By Archetype (<500m2 subset, registry n_proto)", arch_id, adf_u500)

    alt_fieldnames = [
        "group_type", "group_name", "total_buildings", "n_proto_registry",
        "taller_count", "equal_count", "shorter_count", "taller_pct_of_total",
    ]

    OUT_DIR_1.mkdir(parents=True, exist_ok=True)
    OUT_DIR_2.mkdir(parents=True, exist_ok=True)

    main_csv_1 = OUT_DIR_1 / "b00_coverage_census.csv"
    main_csv_2 = OUT_DIR_2 / "b00_coverage_census.csv"
    for path in [main_csv_1, main_csv_2]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=summary_fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)

    alt_csv_1 = OUT_DIR_1 / "b00_coverage_census_registry_alt.csv"
    alt_csv_2 = OUT_DIR_2 / "b00_coverage_census_registry_alt.csv"
    for path in [alt_csv_1, alt_csv_2]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=alt_fieldnames)
            writer.writeheader()
            writer.writerows(alt_rows)

    # ---- Row-level detail export (for audit / reconciliation) ----
    detail_cols = [
        "cell", "osm_id", "archetype_id", "levels", "footprint_area_m2",
        "floor_area_m2", "is_under_500m2", "n_proto_geometric", "has_baseline",
        "category_geometric", "category_registry_alt",
    ]
    detail_csv_1 = OUT_DIR_1 / "b00_coverage_census_row_detail.csv"
    detail_csv_2 = OUT_DIR_2 / "b00_coverage_census_row_detail.csv"
    for path in [detail_csv_1, detail_csv_2]:
        fleet[detail_cols].to_csv(path, index=False)

    print(f"B00: Wrote {len(summary_rows)} summary rows to {main_csv_1} and {main_csv_2}")
    print(f"B00: Wrote {len(alt_rows)} registry-alt rows to {alt_csv_1} and {alt_csv_2}")
    print(f"B00: Wrote {len(fleet)} row-detail rows to {detail_csv_1} and {detail_csv_2}")

    overall = summary_rows[0]
    print(f"FLEET-WIDE: total={overall['total_buildings']} taller={overall['taller_count']} "
          f"equal={overall['equal_count']} shorter={overall['shorter_count']} "
          f"no_baseline={overall['no_baseline_count']} "
          f"taller_pct_of_total={overall['taller_pct_of_total']} "
          f"taller_pct_of_applicable={overall['taller_pct_of_applicable']}")
    u500 = summary_rows[1]
    print(f"<500m2 SUBSET: total={u500['total_buildings']} taller={u500['taller_count']} "
          f"equal={u500['equal_count']} shorter={u500['shorter_count']} "
          f"no_baseline={u500['no_baseline_count']} "
          f"taller_pct_of_total={u500['taller_pct_of_total']} "
          f"taller_pct_of_applicable={u500['taller_pct_of_applicable']}")

    stop_fired = overall['taller_pct_of_total'] < 10.0
    print(f"STOP CONDITION CHECK (B00): fleet-wide taller-than-prototype = "
          f"{overall['taller_pct_of_total']}% of total fleet (threshold: <10%) "
          f"-> {'TRIGGERED' if stop_fired else 'not triggered'}")


if __name__ == "__main__":
    main()
