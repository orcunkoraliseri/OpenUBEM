"""OPEN-35 T04: is the run-4 regression (nyc_centre/way/266034056, dropped after
being imputed 1->19 storeys) a population-level risk or a single building?

Cross-tabulates the fleet-wide repair census (from the twelve open48_run4 per-cell
logs) against:
  (a) the 21-building OPEN-35 Scope-B set (openubem/outputs/comparisons/open35_fallback_agreement_scope.csv,
      changed_scope_b == True) -- the buildings whose `levels` were imputed by the fix.
  (b) a matched control: every OTHER (non-Scope-B) building in run-4 with a REAL
      (non-imputed) levels >= 10, from the same twelve cells' 05_results.csv.

Repair census source: %LOCALAPPDATA%/Temp/open48_run4/<cell>.log, the pipeline's own
"zero-area surfaces stripped" / "rerouted to one_zone_per_floor" / "still failed after
reroute" / "Repaired and resimulated" lines -- read directly, not inferred.
"""
import re
from pathlib import Path

import pandas as pd

LOGDIR = Path(r"C:/Users/o_iseri/AppData/Local/Temp/open48_run4")
RUN4 = Path(r"C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet4")
SCOPE_B_CSV = Path(r"C:/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/comparisons/open35_fallback_agreement_scope.csv")
OUT_CSV = Path(r"C:/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/comparisons/open35_regression_population_2026-08-19.csv")

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]


def parse_repair_census():
    rows = []
    for cell in CELLS:
        log = LOGDIR / f"{cell}.log"
        if not log.exists():
            continue
        text = log.read_text(encoding="utf-8", errors="replace")
        stripped = set(re.findall(r"(\S+): zero-area surfaces stripped ->", text))
        rerouted = set(re.findall(r"(\S+): rerouted to one_zone_per_floor ->", text))
        dropped_m = re.search(r"still failed after reroute.*?:\s*\[([^\]]*)\]", text)
        dropped = set(re.findall(r"'([^']+)'", dropped_m.group(1))) if dropped_m else set()
        needed_repair = stripped | rerouted | dropped
        for osm_id_us in needed_repair:
            rows.append({
                "cell": cell,
                "osm_id": osm_id_us.replace("way_", "way/").replace("relation_", "relation/"),
                "stripped": osm_id_us in stripped,
                "rerouted": osm_id_us in rerouted,
                "dropped_after_reroute": osm_id_us in dropped,
            })
    return pd.DataFrame(rows)


def load_fleet_results():
    frames = []
    for cell in CELLS:
        p = RUN4 / cell / "results" / "05_results.csv"
        df = pd.read_csv(p)
        df["cell"] = cell
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main():
    repair = parse_repair_census()
    print("=== FLEET-WIDE REPAIR CENSUS (from open48_run4/*.log) ===")
    print(repair.to_string(index=False))
    print(f"\nTotal buildings needing any repair fleet-wide: {len(repair)}")

    scope_b = pd.read_csv(SCOPE_B_CSV)
    scope_b = scope_b[scope_b["changed_scope_b"] == True]
    scope_b_ids = set(scope_b["osm_id"])
    print(f"\nScope-B set: {len(scope_b_ids)} buildings")

    repair_ids = set(repair["osm_id"])
    scope_b_repaired = scope_b_ids & repair_ids
    scope_b_clean = scope_b_ids - repair_ids
    non_scope_b_repaired = repair_ids - scope_b_ids

    print(f"\nScope-B buildings that needed repair: {len(scope_b_repaired)} / {len(scope_b_ids)}")
    print(sorted(scope_b_repaired))
    print(f"Scope-B buildings clean (no repair): {len(scope_b_clean)}")
    print(f"Repair-needing buildings OUTSIDE Scope-B (unrelated defects): {len(non_scope_b_repaired)}")
    print(sorted(non_scope_b_repaired))

    fleet = load_fleet_results()
    fleet_ids = set(fleet["osm_id"])
    print(f"\nRepair-census osm_ids missing from results.csv (i.e. dropped, placeholder row): "
          f"{sorted(repair_ids - fleet_ids)}" if (repair_ids - fleet_ids) else "\nAll repaired osm_ids present in results.csv (including as placeholder rows).")

    non_scope_b = fleet[~fleet["osm_id"].isin(scope_b_ids)]
    control = non_scope_b[non_scope_b["levels"] >= 10]
    control_repaired = set(control["osm_id"]) & repair_ids
    print(f"\n=== MATCHED CONTROL: non-Scope-B buildings, REAL levels >= 10 ===")
    print(f"n = {len(control)}")
    print(f"needed repair: {len(control_repaired)} -> {sorted(control_repaired)}")
    print(f"repair rate: {len(control_repaired)/len(control)*100:.2f}%")
    print(f"Scope-B repair rate: {len(scope_b_repaired)/len(scope_b_ids)*100:.2f}%")

    # nyc_centre specific breakdown
    nyc_centre_scope_b = scope_b[scope_b["cell"] == "nyc_centre"]
    nyc_centre_scope_b_ids = set(nyc_centre_scope_b["osm_id"])
    nyc_centre_repaired = nyc_centre_scope_b_ids & repair_ids
    print(f"\nnyc_centre Scope-B subset: {len(nyc_centre_scope_b_ids)} buildings, "
          f"{len(nyc_centre_repaired)} needed repair -> rate {len(nyc_centre_repaired)/len(nyc_centre_scope_b_ids)*100:.1f}%")

    other_cells_scope_b = scope_b[scope_b["cell"] != "nyc_centre"]
    other_ids = set(other_cells_scope_b["osm_id"])
    other_repaired = other_ids & repair_ids
    print(f"Scope-B outside nyc_centre: {len(other_ids)} buildings, "
          f"{len(other_repaired)} needed repair -> rate {len(other_repaired)/len(other_ids)*100:.1f}%")

    # dropped count
    n_dropped = (repair["dropped_after_reroute"]).sum()
    print(f"\nDropped after failed reroute, fleet-wide: {n_dropped} -> {sorted(repair.loc[repair['dropped_after_reroute'],'osm_id'])}")

    # Save combined table
    out = repair.copy()
    out["in_scope_b"] = out["osm_id"].isin(scope_b_ids)
    out.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV} ({len(out)} rows)")


if __name__ == "__main__":
    main()
