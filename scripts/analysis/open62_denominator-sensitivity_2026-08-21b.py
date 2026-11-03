"""T05 (PLAN_ten-live-items-2026-08-21-night.md) — OPEN-62: what each storey definition costs,
in kWh/m².

DENOMINATOR-ONLY SENSITIVITY. Per-building energy is held fixed at the adopted run's value
(total_eui_kwh_m2 x published floor_area_m2). Only the floor-area denominator is redefined as
footprint_area_m2 x storeys, under each of four storey-count definitions. This is not a
re-simulated result: no IDF is rebuilt, no EnergyPlus run occurs.

Reads only; writes one CSV under openubem/outputs/comparisons/.
"""
import csv
import os

REPO = r"C:\Users\o_iseri\Desktop\OpenUBEM"
CENSUS_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open03_storey_census_zfix.csv")
OUT_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open62_denominator-sensitivity_2026-08-21b.csv")
EVIDENCE_ROOT = os.path.join(REPO, "evidence", "open48_refleet4")
CELLS = [f"{city}_{kind}" for city in ("austin", "la", "nyc") for kind in ("centre", "rural", "suburban", "urban")]

ADOPTED_POOLED_EUI = 153.8231
ADOPTED_DENOMINATOR_M2 = 24333586.4

DEFINITIONS = [
    ("auto_storey_count", "auto_storey_count (baseline)"),
    ("layout_assign_storey_count", "layout_assign_storey_count"),
    ("layout_assign_storey_count_naive", "layout_assign_storey_count_naive"),
    ("layout_assign_storey_count_floor", "layout_assign_storey_count_floor"),
]


def load_results(cell):
    path = os.path.join(EVIDENCE_ROOT, cell, "results", "05_results.csv")
    d = {}
    with open(path, "r", newline="") as f:
        for row in csv.DictReader(f):
            d[row["osm_id"]] = row
    return d


def main():
    census_rows = list(csv.DictReader(open(CENSUS_CSV, newline="")))
    assert len(census_rows) == 8160, f"expected 8160 rows, found {len(census_rows)}"

    results_by_cell = {c: load_results(c) for c in CELLS}

    # C10 — reproduce F10's agreement rates before computing anything new.
    agree_check = {}
    for col in ("layout_assign_storey_count", "layout_assign_storey_count_naive", "layout_assign_storey_count_floor"):
        n = tot = 0
        for r in census_rows:
            a, b = r["auto_storey_count"], r[col]
            if a == "" or b == "":
                continue
            tot += 1
            if a == b:
                n += 1
        agree_check[col] = (n, tot, round(100 * n / tot, 2))
    print("C10 agreement rates (auto vs each):", agree_check)

    joined = []
    n_missing_join = 0
    for r in census_rows:
        cell, osm_id = r["cell"], r["osm_id"]
        res = results_by_cell.get(cell, {}).get(osm_id)
        if res is None:
            n_missing_join += 1
            continue
        joined.append((r, res))
    print(f"joined {len(joined)} of {len(census_rows)}; missing join {n_missing_join}")

    success_rows = [(r, res) for r, res in joined if res["simulation_status"] == "success"]
    print(f"success rows: {len(success_rows)} of {len(joined)} joined (pinned population is 8,153)")

    out_rows = []
    summary = []
    for col, label in DEFINITIONS:
        num = 0.0
        den = 0.0
        n_used = 0
        for r, res in success_rows:
            storeys_str = r[col]
            footprint_str = res["footprint_area_m2"]
            eui_str = res["total_eui_kwh_m2"]
            area_str = res["floor_area_m2"]
            if not storeys_str or not footprint_str or not eui_str or not area_str:
                continue
            storeys = float(storeys_str)
            footprint = float(footprint_str)
            eui = float(eui_str)
            published_area = float(area_str)
            redefined_area = footprint * storeys
            if redefined_area <= 0:
                continue
            energy = eui * published_area
            num += energy
            den += redefined_area
            n_used += 1
            out_rows.append({
                "definition": col,
                "cell": r["cell"],
                "osm_id": r["osm_id"],
                "storeys": storeys,
                "footprint_area_m2": footprint,
                "redefined_area_m2": redefined_area,
                "published_floor_area_m2": published_area,
                "total_eui_kwh_m2": eui,
            })
        pooled_eui = num / den if den else float("nan")
        delta = pooled_eui - ADOPTED_POOLED_EUI
        delta_denom_pct = 100 * (den - ADOPTED_DENOMINATOR_M2) / ADOPTED_DENOMINATOR_M2
        summary.append((label, n_used, den, pooled_eui, delta, delta_denom_pct))

    with open(OUT_CSV, "w", newline="") as f:
        fieldnames = list(out_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    print("\n--- per-definition summary (denominator-only sensitivity, energy held fixed) ---")
    for label, n_used, den, pooled_eui, delta, delta_denom_pct in summary:
        print(
            f"{label}: n={n_used} denominator_m2={den:.1f} pooled_eui={pooled_eui:.4f} "
            f"delta_vs_adopted={delta:+.4f} kWh/m2 denom_delta_vs_F6={delta_denom_pct:+.3f}%"
        )

    baseline = summary[0]
    print(f"\nC11: baseline ({baseline[0]}) denominator={baseline[2]:.1f} m2 vs F6 {ADOPTED_DENOMINATOR_M2} m2, "
          f"delta={baseline[5]:+.3f}%")


if __name__ == "__main__":
    main()
