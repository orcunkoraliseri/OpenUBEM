from __future__ import annotations

import argparse
import csv
import json
import sys
from io import StringIO
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd

FLEET_CSV = REPO / "openubem" / "outputs" / "comparisons" / "paper_adopted_fleet_per_building_2026-10-21.csv"
SCENARIO_SUMMARY_CSV = REPO / "openubem" / "outputs" / "comparisons" / "fleet07_scenario_summary_2026-09-26.csv"
OUT_CSV = REPO / "openubem" / "outputs" / "comparisons" / "paper_retrofit_check_2026-10-21.csv"
SCHEDULES_JSON = REPO / "openubem" / "data" / "schedules" / "doe_schedules.json"
MEASURES_JSON = REPO / "openubem" / "data" / "scenarios" / "measures.json"

EXCLUDED_FLEET07 = (
    "way/241854848", "way/241854850", "way/266170543", "way/266170639", "way/266170721",
    "way/266170731", "way/266170785", "way/280621323", "way/280621332", "way/427278443",
)
EXPECTED_POPULATION = 8129
LOGGED_FLEET07B = {
    "population": 8139,
    "setback_changed": 8071,
    "setback_already_compliant": 33,
    "setback_gate_no_setback_block": 35,
    "lighting_changed": 2798,
    "lighting_in_scope": 4140,
    "lighting_out_of_scope": 3999,
    "lighting_no_applicable_objects": 1342,
    "infiltration_changed": 2247,
    "infiltration_already_compliant": 5892,
}
WEEKDAYS_PER_YEAR = 260

COLUMNS = [
    "row_type", "archetype_id", "measure", "n_buildings", "status", "n_applied",
    "heating_setpoint_before_c", "heating_setpoint_after_c", "heating_hours_lowered_per_year",
    "heating_hours_lowered_per_year_all_buildings_mean", "population", "source", "vintage",
]


def _hours_by_value(entries):
    out = []
    prev = 0
    for e in entries:
        until = e["until_minutes"]
        out.append((e["for_str"], e["value"], max(until - prev, 0) / 60.0))
        prev = until
    return out


def _heating_rows(idf, sched_name):
    from openubem.scenarios import measures as m

    sched = m._find_compact_schedule(idf, sched_name)
    if sched is None:
        return []
    entries = m._parse_compact_value_entries(sched)
    rows = []
    prev_for = None
    prev = 0
    for e in entries:
        if e["for_str"] != prev_for:
            prev = 0
            prev_for = e["for_str"]
        rows.append((e["for_str"], e["value"], max(e["until_minutes"] - prev, 0) / 60.0))
        prev = e["until_minutes"]
    return rows


def _make_idf(archetype):
    from io import StringIO as _S
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF
    from openubem import config
    from openubem.semantic.schedules import write_schedules_to_idf

    try:
        IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    idf = IDF(_S("Version,23.1;"))
    write_schedules_to_idf(idf, archetype)
    idf.newidfobject(
        "HVACTEMPLATE:THERMOSTAT",
        Name=f"{archetype}_Thermostat",
        Heating_Setpoint_Schedule_Name=f"Heating_Setpoint_{archetype}",
        Cooling_Setpoint_Schedule_Name=f"Cooling_Setpoint_{archetype}",
    )
    return IDF(_S(idf.idfstr()))


def setback_on_archetype(archetype):
    from openubem.scenarios import measures as m

    idf = _make_idf(archetype)
    before = _heating_rows(idf, f"Heating_Setpoint_{archetype}")
    report = m.apply_measure(idf, "thermostat_setback", enabled=True, archetype=archetype)
    heat_obj = next((o for o in report["objects"] if o["role"] == "heating"), None)
    after_name = heat_obj.get("new_schedule") if heat_obj else None
    after = _heating_rows(idf, after_name) if after_name else before
    hours_lowered = 0.0
    before_vals = []
    after_vals = []
    for (f1, v1, h1), (f2, v2, h2) in zip(before, after):
        if v2 != v1 and not m._is_nonworkday(f1):
            hours_lowered += h1 * WEEKDAYS_PER_YEAR
            before_vals.append(v1)
            after_vals.append(v2)
    return {
        "status": report["status"],
        "n_applied": report["n_applied"],
        "before": sorted(set(before_vals))[0] if before_vals else None,
        "after": sorted(set(after_vals))[0] if after_vals else None,
        "hours_lowered": hours_lowered,
        "heating_status": heat_obj["status"] if heat_obj else "none",
        "cooling_status": next((o["status"] for o in report["objects"] if o["role"] == "cooling"), "none"),
    }


def load_population():
    df = pd.read_csv(FLEET_CSV, usecols=["osm_id", "archetype_id"])
    n_all = len(df)
    df = df[~df["osm_id"].isin(EXCLUDED_FLEET07)]
    return n_all, df


def load_population_all():
    df = pd.read_csv(FLEET_CSV, usecols=["osm_id", "archetype_id"])
    return len(df), df


def build_rows():
    n_all, pop = load_population()
    counts = pop["archetype_id"].value_counts().sort_index()
    schedules = json.loads(SCHEDULES_JSON.read_text(encoding="utf-8"))
    measures = json.loads(MEASURES_JSON.read_text(encoding="utf-8"))
    in_scope = set(measures["lighting_power_density"]["in_scope_archetypes"])
    total = int(counts.sum())
    vintage_fleet = "adopted fleet table 2026-10-21 (T01), minus the 10 buildings excluded in the 2026-09-26 scenario table"
    rows = []
    sb_changed = 0
    sb_hours_weighted = 0.0
    per_arch = {}
    for arch, n in counts.items():
        res = setback_on_archetype(arch) if arch in schedules else None
        per_arch[arch] = res
        if res and res["n_applied"] > 0:
            sb_changed += int(n)
            sb_hours_weighted += res["hours_lowered"] * int(n)
    for arch, n in counts.items():
        n = int(n)
        res = per_arch[arch]
        rows.append({
            "row_type": "archetype_population",
            "archetype_id": arch, "measure": "all", "n_buildings": n,
            "population": total, "source": "paper_adopted_fleet_per_building_2026-10-21.csv",
            "vintage": vintage_fleet,
        })
        rows.append({
            "row_type": "archetype_measure",
            "archetype_id": arch, "measure": "lighting_power_density", "n_buildings": n,
            "status": "in_scope" if arch in in_scope else "gate_archetype_out_of_scope",
            "population": total,
            "source": "measures.json in_scope_archetypes (scope only; applied vs no_applicable_objects needs the IDF)",
            "vintage": vintage_fleet,
        })
        if res is None:
            rows.append({
                "row_type": "archetype_measure", "archetype_id": arch,
                "measure": "thermostat_setback", "n_buildings": n, "status": "no_schedule_library_entry",
                "population": total, "source": "doe_schedules.json", "vintage": vintage_fleet,
            })
        else:
            rows.append({
                "row_type": "archetype_measure", "archetype_id": arch,
                "measure": "thermostat_setback", "n_buildings": n,
                "status": f"{res['status']} (heating {res['heating_status']}, cooling {res['cooling_status']})",
                "n_applied": res["n_applied"],
                "heating_setpoint_before_c": res["before"], "heating_setpoint_after_c": res["after"],
                "heating_hours_lowered_per_year": round(res["hours_lowered"], 2),
                "population": total,
                "source": "apply_measure on the archetype schedule library (openubem/data/schedules/doe_schedules.json) inside a minimal IDF with the HVACTEMPLATE:THERMOSTAT the builder writes (openubem/idf/builder.py:462-465)",
                "vintage": vintage_fleet,
            })
    mean_hours = sb_hours_weighted / total
    rows.append({
        "row_type": "setback_summary", "archetype_id": "ALL", "measure": "thermostat_setback",
        "n_buildings": sb_changed, "status": "predicted_changed",
        "heating_hours_lowered_per_year_all_buildings_mean": round(mean_hours, 2),
        "population": total,
        "source": f"archetype rule x archetype counts; weekdays only, {WEEKDAYS_PER_YEAR} weekdays per year",
        "vintage": vintage_fleet,
    })
    n_all_rows, pop_all = load_population_all()
    sb_changed_all = sum(
        int(n) for a, n in pop_all["archetype_id"].value_counts().items()
        if per_arch.get(a) and per_arch[a]["n_applied"] > 0
    )
    rows.append({
        "row_type": "setback_summary", "archetype_id": "ALL_changed_only", "measure": "thermostat_setback",
        "n_buildings": sb_changed, "status": "mean_hours_over_changed_buildings",
        "heating_hours_lowered_per_year_all_buildings_mean": round(sb_hours_weighted / sb_changed, 2),
        "population": total, "source": "same rule, mean over the buildings where heating setback changed",
        "vintage": vintage_fleet,
    })
    rows.append({
        "row_type": "crosscheck", "archetype_id": "ALL", "measure": "thermostat_setback",
        "n_buildings": sb_changed_all,
        "status": f"rule predicts {sb_changed_all} changed over {n_all_rows} buildings; fleet07 log says {LOGGED_FLEET07B['setback_changed']} over {LOGGED_FLEET07B['population']}",
        "population": n_all_rows, "source": "archetype rule vs logged FLEET-07b count", "vintage": vintage_fleet,
    })
    rows.append({
        "row_type": "population_check", "archetype_id": "ALL", "measure": "all",
        "n_buildings": total, "status": f"fleet table {n_all} minus {len(EXCLUDED_FLEET07)} excluded = {total}; expected {EXPECTED_POPULATION}",
        "population": total, "source": "plan T09 test", "vintage": vintage_fleet,
    })
    vint_log = "campaign 2026-09-26 (FLEET-07b log in PLAN_techtransfer-block7-fleet07-2026-09-26.md, per-building records deleted 2026-09-28)"
    for key, val in LOGGED_FLEET07B.items():
        rows.append({
            "row_type": "logged_fleet07b", "archetype_id": "ALL", "measure": key.split("_")[0],
            "n_buildings": val, "status": key, "population": LOGGED_FLEET07B["population"],
            "source": "docs/docs_DONE/TechTransfer/implementation/PLAN_techtransfer-block7-fleet07-2026-09-26.md FLEET-07b test status (per-cell changed counts and status x measure table, divided by 4 setback/lighting/infiltration-bearing cells)",
            "vintage": vint_log,
        })
    summary = pd.read_csv(SCENARIO_SUMMARY_CSV).set_index("scenario_cell")
    for cell in ("lighting", "setback", "infiltration"):
        rows.append({
            "row_type": "logged_saving", "archetype_id": "ALL", "measure": cell,
            "n_buildings": int(summary.loc[cell, "n_buildings"]),
            "status": f"delta_pct {summary.loc[cell, 'delta_vs_baseline_pct']:.4f} delta_kwh_m2 {summary.loc[cell, 'delta_vs_baseline_kwh_m2']:.4f}",
            "population": int(summary.loc[cell, "n_buildings"]),
            "source": "fleet07_scenario_summary_2026-09-26.csv", "vintage": "pre-adoption baseline 172.23 kWh/m2, 2026-09-26",
        })
    return rows, total, sb_changed, mean_hours, per_arch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_CSV))
    args = ap.parse_args()
    rows, total, sb_changed, mean_hours, _ = build_rows()
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    print(f"rows={len(rows)} population={total} setback_changed_predicted={sb_changed} mean_hours={mean_hours:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
