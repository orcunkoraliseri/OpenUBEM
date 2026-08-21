"""T04 (PLAN_ten-live-items-2026-08-21-night.md) — OPEN-35: what was actually built for the 39.

For each of the 39 fallback-population buildings, build an evidence card comparing what the
model actually built (from .eio Zone Information) against what the fallback assigned
(from the population CSV) and what was published (from 05_results.csv).

Reads only; writes one CSV under openubem/outputs/comparisons/.
"""
import csv
import os

REPO = r"C:\Users\o_iseri\Desktop\OpenUBEM"
POP_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open35_fallback_population_2026-08-21.csv")
OUT_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open35_evidence-cards_2026-08-21b.csv")
EVIDENCE_ROOT = os.path.join(REPO, "evidence", "open48_refleet4")

EXPECTED_HEADER_FIELDS = [
    "Zone Name", "North Axis", "Origin X", "Origin Y", "Origin Z", "Centroid X",
    "Centroid Y", "Centroid Z", "Type", "Zone Multiplier", "Zone List Multiplier",
    "Min X", "Max X", "Min Y", "Max Y", "Min Z", "Max Z", "Ceiling Height", "Volume",
    "Inside Conv Alg", "Outside Conv Alg", "Floor Area", "Ext Gross Wall Area",
    "Ext Net Wall Area", "Ext Window Area", "N Surfaces", "N SubSurfaces",
    "N Shading SubSurfaces", "Part of Total Building Area",
]


def check_header(eio_path):
    with open(eio_path, "r", errors="replace") as f:
        for line in f:
            if line.startswith("! <Zone Information>"):
                return True
    return False


def parse_eio_zones(eio_path):
    zones = []
    with open(eio_path, "r", errors="replace") as f:
        for line in f:
            if line.startswith(" Zone Information,"):
                parts = [p.strip() for p in line.strip().split(",")]
                # parts[0] == "Zone Information"; fields follow per F3 order
                fields = parts[1:]
                if len(fields) < 22:
                    continue
                zones.append({
                    "zone_name": fields[0],
                    "min_z": float(fields[15]),
                    "max_z": float(fields[16]),
                    "ceiling_height": float(fields[17]),
                    "volume": float(fields[18]),
                    "floor_area": float(fields[21]),
                })
    return zones


def stem_for(osm_id):
    return osm_id.replace("/", "_")


def load_results(cell):
    path = os.path.join(EVIDENCE_ROOT, cell, "results", "05_results.csv")
    d = {}
    with open(path, "r", newline="") as f:
        for row in csv.DictReader(f):
            d[row["osm_id"]] = row
    return d


def main():
    pop_rows = list(csv.DictReader(open(POP_CSV, newline="")))
    assert len(pop_rows) == 39, f"expected 39 rows in {POP_CSV}, found {len(pop_rows)}"

    results_by_cell = {}
    out_rows = []
    n_eio_readable = 0
    n_simulated = 0

    for r in pop_rows:
        cell = r["cell"]
        osm_id = r["osm_id"]
        stem = stem_for(osm_id)
        eio_path = os.path.join(EVIDENCE_ROOT, cell, "sim_out", stem, "eplusout.eio")

        if cell not in results_by_cell:
            results_by_cell[cell] = load_results(cell)
        res = results_by_cell[cell].get(osm_id)

        eio_readable = os.path.isfile(eio_path)
        zone_count = ""
        distinct_levels = ""
        built_floor_area = ""
        max_max_z = ""
        if eio_readable:
            if not check_header(eio_path):
                print(f"NO ZONE INFO HEADER: {eio_path}")
            else:
                zones = parse_eio_zones(eio_path)
                if zones:
                    n_eio_readable += 1
                    zone_count = len(zones)
                    distinct_levels = len({(z["min_z"], z["max_z"]) for z in zones})
                    built_floor_area = sum(z["floor_area"] for z in zones)
                    max_max_z = max(z["max_z"] for z in zones)
                    eio_readable = True
                else:
                    eio_readable = False

        sim_status = res["simulation_status"] if res else ""
        if sim_status == "success":
            n_simulated += 1

        out_rows.append({
            "cell": cell,
            "osm_id": osm_id,
            "current_num_floors": r["current_num_floors"],
            "preopen35_num_floors": r["preopen35_num_floors"],
            "current_floor_area_m2": r["current_floor_area_m2"],
            "preopen35_floor_area_m2": r["preopen35_floor_area_m2"],
            "eio_readable": eio_readable,
            "built_zone_count": zone_count,
            "built_distinct_storey_levels": distinct_levels,
            "built_floor_area_m2_summed": built_floor_area,
            "built_max_z_m": max_max_z,
            "res_floor_area_m2": res["floor_area_m2"] if res else "",
            "res_levels": res["levels"] if res else "",
            "res_height_m": res["height_m"] if res else "",
            "res_archetype_id": res["archetype_id"] if res else "",
            "simulation_status": sim_status,
            "total_eui_kwh_m2": res["total_eui_kwh_m2"] if res else "",
        })

    out_rows.sort(key=lambda x: float(x["current_floor_area_m2"]), reverse=True)

    fieldnames = list(out_rows[0].keys())
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    print(f"rows_out={len(out_rows)}")
    print(f"n_eio_readable={n_eio_readable} of 39")
    print(f"n_simulation_status_success={n_simulated} of 39")

    print("\n--- top 5 by current_floor_area_m2 ---")
    for row in out_rows[:5]:
        print(
            f"{row['osm_id']} ({row['cell']}): "
            f"assigned_levels={row['current_num_floors']} "
            f"built_zone_count={row['built_zone_count']} "
            f"built_distinct_levels={row['built_distinct_storey_levels']} "
            f"published_floor_area_m2={row['current_floor_area_m2']} "
            f"res_floor_area_m2={row['res_floor_area_m2']} "
            f"sim_status={row['simulation_status']} "
            f"total_eui={row['total_eui_kwh_m2']}"
        )

    target = next((row for row in out_rows if row["osm_id"] == "relation/7480583"), None)
    if target:
        print(
            f"\nC9 headline: relation/7480583 built_zone_count="
            f"{target['built_zone_count']} built_distinct_storey_levels="
            f"{target['built_distinct_storey_levels']} vs assigned=45"
        )
    else:
        print("\nC9 headline: relation/7480583 NOT FOUND in population CSV")


if __name__ == "__main__":
    main()
