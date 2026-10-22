from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
if (REPO / "openubem").is_dir() and str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

N_KEY_BY_MEASURE = {
    "lighting_power_density": "n_lowered",
    "thermostat_setback": "n_applied",
    "infiltration_tightening": "n_tightened",
}
SHORT = {
    "lighting_power_density": "lighting",
    "thermostat_setback": "setback",
    "infiltration_tightening": "infiltration",
}
STATUS_COLUMNS = ["cell", "stem", "archetype", "changed", "n_applied_total", "agree"] + [
    f"{s}_{suffix}" for s in SHORT.values() for suffix in ("raw", "outcome", "n")
]


def measure_cells():
    from openubem.scenarios.campaign import build_full_factorial_campaign

    return {c.name: c for c in build_full_factorial_campaign() if c.name != "baseline"}


def outcome(report: dict) -> str:
    n = report.get(N_KEY_BY_MEASURE[report["measure_id"]], 0)
    if n > 0:
        return "applied"
    if report["status"] == "gate_archetype_out_of_scope":
        return "not_in_scope"
    return "unchanged"


def load_idf(path: Path):
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF
    from openubem import config

    try:
        IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(path))


def build(adopted: Path, archetype: str, cell_name: str, out_idf: Path, status_csv: Path) -> dict:
    from openubem.scenarios.campaign import apply_cell

    cells = measure_cells()
    if cell_name not in cells:
        raise SystemExit(f"STOP: cell {cell_name!r} is not one of {sorted(cells)}")
    cell = cells[cell_name]
    stem = Path(adopted).stem
    idf = load_idf(Path(adopted))
    before = idf.idfstr()
    reports = apply_cell(idf, cell, enabled=True, archetype=archetype)
    after = idf.idfstr()
    out_idf.parent.mkdir(parents=True, exist_ok=True)
    idf.saveas(str(out_idf))
    changed = before != after
    row = {"cell": cell_name, "stem": stem, "archetype": archetype}
    total = 0
    for measure_id, report in zip(cell.measure_ids, reports):
        n = int(report.get(N_KEY_BY_MEASURE[measure_id], 0))
        total += n
        short = SHORT[measure_id]
        row[f"{short}_raw"] = report["status"]
        row[f"{short}_outcome"] = outcome(report)
        row[f"{short}_n"] = n
    row["changed"] = int(changed)
    row["n_applied_total"] = total
    row["agree"] = int(changed == (total > 0))
    status_csv.parent.mkdir(parents=True, exist_ok=True)
    write_header = not status_csv.exists() or status_csv.stat().st_size == 0
    with open(status_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=STATUS_COLUMNS)
        if write_header:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in STATUS_COLUMNS})
    return row


def parse_one(sql: Path, osm_id: str, floor_area_m2: float, data_quality_flag: str, row_csv: Path) -> dict:
    import pandas as pd

    from openubem.results.parser import parse_building

    end = sql.parent / "eplusout.end"
    completed = end.exists() and "Successfully" in end.read_text(errors="ignore")
    manifest_row = pd.Series({
        "osm_id": osm_id, "num_zones": 1,
        "data_quality_flag": data_quality_flag if isinstance(data_quality_flag, str) else "",
        "resolution_mode": "layout_assign",
        "footprint_area_m2": float(floor_area_m2), "levels": 1, "height_m": math.nan,
    })
    parsed = parse_building(sql, None, manifest_row)
    parsed = {k: v for k, v in parsed.items() if not k.startswith("gwp_")}
    parsed["completed"] = int(completed)
    fa = parsed.get("floor_area_m2")
    eui = parsed.get("total_eui_kwh_m2")
    parsed["total_kwh"] = (fa * eui) if (fa is not None and eui is not None and parsed["parse_status"] == "success") else math.nan
    row_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(row_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(parsed))
        w.writeheader()
        w.writerow(parsed)
    return parsed


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "parse":
        if len(argv) != 7:
            print("usage: scenario_build.py parse <eplusout.sql> <osm_id> <floor_area_m2> <data_quality_flag> <row.csv>",
                  file=sys.stderr)
            return 2
        parsed = parse_one(Path(argv[2]), argv[3], float(argv[4]), argv[5], Path(argv[6]))
        print(f"parse_status={parsed['parse_status']} completed={parsed['completed']}")
        return 0 if parsed["parse_status"] == "success" and parsed["completed"] else 3
    if len(argv) != 6:
        print("usage: scenario_build.py <adopted.idf> <archetype> <cell> <out.idf> <status.csv>", file=sys.stderr)
        return 2
    row = build(Path(argv[1]), argv[2], argv[3], Path(argv[4]), Path(argv[5]))
    print(f"changed={row['changed']} n_applied_total={row['n_applied_total']} agree={row['agree']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
