"""T01 -- Corpus integrity gate for the E02 harvest corpus.

Counts, independently of any prior report, what is actually on disk under
ubem_e02_harvest: per array directory (cell x mode), the number of building
directories and the number of eplusout.err / eplusout.eio / eplusout.end
files present. Does not open or hash any file.

Plan: docs/docs_ACTIVE/openings/implemenation/PLAN_e02-audit-and-closure.md, T01.
"""

import csv
import os

CORPUS_ROOT = r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest"
OUT_CSV = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\e02_corpus_inventory.csv"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]


def scan_array(array_path):
    n_dirs = 0
    n_err = 0
    n_eio = 0
    n_end = 0
    with os.scandir(array_path) as it:
        for entry in it:
            if not entry.is_dir():
                continue
            n_dirs += 1
            stem_path = entry.path
            if os.path.isfile(os.path.join(stem_path, "eplusout.err")):
                n_err += 1
            if os.path.isfile(os.path.join(stem_path, "eplusout.eio")):
                n_eio += 1
            if os.path.isfile(os.path.join(stem_path, "eplusout.end")):
                n_end += 1
    return n_dirs, n_err, n_eio, n_end


def main():
    expected_arrays = {f"{cell}_{mode}" for cell in CELLS for mode in MODES}

    with os.scandir(CORPUS_ROOT) as it:
        actual_arrays = sorted(e.name for e in it if e.is_dir())

    print(f"Arrays on disk: {len(actual_arrays)}")
    print(f"Expected (12 cells x 5 modes): {len(expected_arrays)}")
    missing = expected_arrays - set(actual_arrays)
    extra = set(actual_arrays) - expected_arrays
    print(f"Missing from disk: {sorted(missing)}")
    print(f"Present on disk but not in cross-product: {sorted(extra)}")
    cross_product_ok = (missing == set() and extra == set())
    print(f"Cross-product match: {cross_product_ok}")

    rows = []
    tot_dirs = tot_err = tot_eio = tot_end = 0
    for array_name in actual_arrays:
        cell = None
        mode = None
        for c in CELLS:
            prefix = c + "_"
            if array_name.startswith(prefix):
                candidate_mode = array_name[len(prefix):]
                if candidate_mode in MODES:
                    cell, mode = c, candidate_mode
                    break
        if cell is None:
            cell, mode = array_name, "UNKNOWN"

        array_path = os.path.join(CORPUS_ROOT, array_name)
        n_dirs, n_err, n_eio, n_end = scan_array(array_path)
        rows.append({
            "cell": cell,
            "mode": mode,
            "n_dirs": n_dirs,
            "n_err": n_err,
            "n_eio": n_eio,
            "n_end": n_end,
        })
        tot_dirs += n_dirs
        tot_err += n_err
        tot_eio += n_eio
        tot_end += n_end
        print(f"{array_name}: n_dirs={n_dirs} n_err={n_err} n_eio={n_eio} n_end={n_end}")

    rows.append({
        "cell": "FLEET_TOTAL",
        "mode": "ALL",
        "n_dirs": tot_dirs,
        "n_err": tot_err,
        "n_eio": tot_eio,
        "n_end": tot_end,
    })

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cell", "mode", "n_dirs", "n_err", "n_eio", "n_end"])
        writer.writeheader()
        writer.writerows(rows)

    print()
    print("=== FLEET TOTALS ===")
    print(f"n_dirs={tot_dirs} n_err={tot_err} n_eio={tot_eio} n_end={tot_end}")

    # --- How-to-test checks, printed explicitly ---
    print()
    print("=== TEST (a): 60 array names == 12 cells x 5 modes cross-product ===")
    print(f"actual_arrays count = {len(actual_arrays)}")
    print(f"expected_arrays count = {len(expected_arrays)}")
    print(f"missing = {sorted(missing)}")
    print(f"extra = {sorted(extra)}")
    print(f"PASS = {cross_product_ok and len(actual_arrays) == 60}")

    print()
    print("=== TEST (b): austin_centre_auto n_dirs == 413, la_rural_{auto,floor,fast_zone} n_dirs == 149 ===")
    lookup = {(r["cell"], r["mode"]): r["n_dirs"] for r in rows if r["cell"] != "FLEET_TOTAL"}
    austin_centre_auto = lookup.get(("austin_centre", "auto"))
    la_rural_auto = lookup.get(("la_rural", "auto"))
    la_rural_floor = lookup.get(("la_rural", "floor"))
    la_rural_fast_zone = lookup.get(("la_rural", "fast_zone"))
    print(f"austin_centre_auto n_dirs = {austin_centre_auto} (expected 413)")
    print(f"la_rural_auto n_dirs = {la_rural_auto} (expected 149)")
    print(f"la_rural_floor n_dirs = {la_rural_floor} (expected 149)")
    print(f"la_rural_fast_zone n_dirs = {la_rural_fast_zone} (expected 149)")

    print()
    print("=== TEST (c): n_end exactly one short of n_dirs fleet-wide, in exactly one array ===")
    deficit_arrays = []
    for r in rows:
        if r["cell"] == "FLEET_TOTAL":
            continue
        deficit = r["n_dirs"] - r["n_end"]
        if deficit != 0:
            deficit_arrays.append((r["cell"], r["mode"], deficit))
    fleet_deficit = tot_dirs - tot_end
    print(f"Fleet-wide n_dirs - n_end = {fleet_deficit} (expected 1)")
    print(f"Arrays with nonzero n_dirs - n_end deficit: {deficit_arrays}")
    print(f"Expected single array: nyc_centre_fast_zone")

    print()
    print("=== STOP CONDITION CHECK ===")
    expected_dirs = 40800
    expected_err = 40800
    expected_eio = 40800
    expected_end = 40799
    print(f"n_dirs deviation from 40800: {tot_dirs - expected_dirs}")
    print(f"n_err deviation from 40800: {tot_err - expected_err}")
    print(f"n_eio deviation from 40800: {tot_eio - expected_eio}")
    print(f"n_end deviation from 40799: {tot_end - expected_end}")
    total_shortfall = (expected_dirs - tot_dirs) + (expected_err - tot_err) + (expected_eio - tot_eio)
    end_shortfall_beyond_known = (expected_end - tot_end) - 1
    print(f"Shortfall beyond the one known missing .end (dirs/err/eio combined): {total_shortfall}")
    print(f"End-file shortfall beyond the one known missing .end: {end_shortfall_beyond_known}")
    if total_shortfall > 0 or end_shortfall_beyond_known > 0:
        print("STOP CONDITION TRIGGERED: corpus short by more than the one known missing .end")
    else:
        print("No stop condition triggered.")


if __name__ == "__main__":
    main()
