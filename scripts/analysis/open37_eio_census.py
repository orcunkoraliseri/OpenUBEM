"""OPEN-37 census: what .eio/.sql/.err/.end files actually exist in the local
E02 harvest corpus, per (cell, mode) directory.

Read-only over C:\\Users\\o_iseri\\AppData\\Local\\Temp\\ubem_e02_harvest\\<cell>_<mode>\\.
Never writes into the harvest tree. Writes
openubem/outputs/comparisons/open37_eio_census.csv.
"""

from __future__ import annotations

import csv
from pathlib import Path

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
OUT_CSV = Path("openubem/outputs/comparisons/open37_eio_census.csv")

MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]


def parse_cell_mode(dirname: str) -> tuple[str, str] | None:
    for mode in MODES:
        suffix = f"_{mode}"
        if dirname.endswith(suffix):
            cell = dirname[: -len(suffix)]
            return cell, mode
    return None


def census_dir(site_dir: Path) -> dict:
    n_building_dirs = 0
    n_eio = 0
    n_eio_empty = 0
    n_sql = 0
    n_err = 0
    n_end = 0

    for building_dir in site_dir.iterdir():
        if not building_dir.is_dir():
            continue
        n_building_dirs += 1

        eio_path = building_dir / "eplusout.eio"
        if eio_path.is_file():
            n_eio += 1
            if eio_path.stat().st_size == 0:
                n_eio_empty += 1

        if (building_dir / "eplusout.sql").is_file():
            n_sql += 1
        if (building_dir / "eplusout.err").is_file():
            n_err += 1
        if (building_dir / "eplusout.end").is_file():
            n_end += 1

    return {
        "n_building_dirs": n_building_dirs,
        "n_eio": n_eio,
        "n_eio_empty": n_eio_empty,
        "n_sql": n_sql,
        "n_err": n_err,
        "n_end": n_end,
    }


def main() -> None:
    rows = []
    site_dirs = sorted(p for p in HARVEST_ROOT.iterdir() if p.is_dir())

    for site_dir in site_dirs:
        parsed = parse_cell_mode(site_dir.name)
        if parsed is None:
            cell, mode = site_dir.name, "UNKNOWN"
        else:
            cell, mode = parsed
        stats = census_dir(site_dir)
        row = {"cell": cell, "mode": mode, "dirname": site_dir.name}
        row.update(stats)
        rows.append(row)

    total = {
        "cell": "TOTAL",
        "mode": "",
        "dirname": f"{len(rows)} (cell, mode) directories",
        "n_building_dirs": sum(r["n_building_dirs"] for r in rows),
        "n_eio": sum(r["n_eio"] for r in rows),
        "n_eio_empty": sum(r["n_eio_empty"] for r in rows),
        "n_sql": sum(r["n_sql"] for r in rows),
        "n_err": sum(r["n_err"] for r in rows),
        "n_end": sum(r["n_end"] for r in rows),
    }
    rows.append(total)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["cell", "mode", "dirname", "n_building_dirs", "n_eio", "n_eio_empty", "n_sql", "n_err", "n_end"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows (incl. TOTAL) to {OUT_CSV}")
    print(f"n_site_dirs (cell,mode) = {len(site_dirs)}")
    print(f"TOTAL n_building_dirs = {total['n_building_dirs']}")
    print(f"TOTAL n_eio = {total['n_eio']} (empty: {total['n_eio_empty']})")
    print(f"TOTAL n_sql = {total['n_sql']}")
    print(f"TOTAL n_err = {total['n_err']}")
    print(f"TOTAL n_end = {total['n_end']}")


if __name__ == "__main__":
    main()
