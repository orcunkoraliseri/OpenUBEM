"""T01 (PLAN_ten-live-items-2026-08-20-evening.md) — run production's
check_building_integrity() gate over the whole OPEN-61 census .sql corpus.

Population: every eplusout.sql found under the census corpus root (read-only,
D2). Metadata (cell/osm_id/archetype_id) joined from
openubem/outputs/comparisons/open61_census_fleet.csv by stem
(osm_id with '/' -> '_'). Gate imported from openubem.results.parser, never
re-implemented (D3). The "raw diff" the gate computes internally (ABUPS vs
hourly reconciliation) is not part of check_building_integrity()'s return
value, so it is captured by monkey-patching sqlite3.connect inside THIS
script only (rule 2: never edit openubem/results/parser.py) — the gate's own
SQL and its own abups_ok/meter_ok/gas_zero booleans are untouched; the patch
only observes the four fetchone() values the gate already computes, in the
fixed order the function issues them (hourly_j, abups_gj, facility_j,
zone_elec_j, gas_j), and reports the same diff formula the gate uses
(abs(hourly_j - abups_j) / abups_j) purely for transparency in the CSV.
"""
from __future__ import annotations

import csv
import random
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CORPUS = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\89a28ab2-bc04-4d19-9e55-89a800c96691\scratchpad\open61_census_fleet_work"
)
CENSUS_CSV = REPO / "openubem/outputs/comparisons/open61_census_fleet.csv"
OUT_CSV = REPO / "openubem/outputs/comparisons/open60_fleet_integrity_gate_2026-08-20.csv"

FIELDS = [
    "cell", "osm_id", "archetype_id", "stem", "sql_path",
    "abups_ok", "meter_ok", "gas_zero", "raw_abups_diff",
]


class _CapturingConn:
    def __init__(self, real_conn, sink):
        self._c = real_conn
        self._sink = sink

    def execute(self, sql, *a, **kw):
        cur = self._c.execute(sql, *a, **kw)
        return _CapturingCursor(cur, self._sink)

    def __getattr__(self, name):
        return getattr(self._c, name)


class _CapturingCursor:
    def __init__(self, real_cur, sink):
        self._cur = real_cur
        self._sink = sink

    def fetchone(self):
        row = self._cur.fetchone()
        self._sink.append(row)
        return row

    def __getattr__(self, name):
        return getattr(self._cur, name)


def _find_sql_files():
    return sorted(CORPUS.glob("*/*/sim_out/eplusout.sql"))


def _load_metadata():
    import pandas as pd
    df = pd.read_csv(CENSUS_CSV, usecols=["cell", "osm_id", "archetype_id"])
    df["stem"] = df["osm_id"].str.replace("/", "_", regex=False)
    df["key"] = df["cell"] + "/" + df["stem"]
    return dict(zip(df["key"], zip(df["cell"], df["osm_id"], df["archetype_id"])))


def _gate_one(sql_path_str, cell, stem, osm_id, archetype_id, capture_diff=True):
    from openubem.results.parser import check_building_integrity

    sink = []
    orig_connect = sqlite3.connect

    def _patched_connect(*a, **kw):
        real = orig_connect(*a, **kw)
        return _CapturingConn(real, sink)

    if capture_diff:
        sqlite3.connect = _patched_connect
    try:
        result = check_building_integrity(Path(sql_path_str))
    finally:
        sqlite3.connect = orig_connect

    raw_diff = ""
    if capture_diff and len(sink) >= 2:
        hourly_j = sink[0][0] if sink[0] else 0.0
        abups_gj = sink[1][0] if sink[1] else 0.0
        abups_j = (abups_gj or 0.0) * 1e9
        if abups_j > 0:
            raw_diff = abs(hourly_j - abups_j) / abups_j
        else:
            raw_diff = 0.0 if hourly_j == 0.0 else ""

    return {
        "cell": cell,
        "osm_id": osm_id,
        "archetype_id": archetype_id,
        "stem": stem,
        "sql_path": sql_path_str,
        "abups_ok": result["abups_ok"],
        "meter_ok": result["meter_ok"],
        "gas_zero": result["gas_zero"],
        "raw_abups_diff": raw_diff,
    }


def _worker(args):
    sql_path_str, cell, stem, osm_id, archetype_id = args
    try:
        return _gate_one(sql_path_str, cell, stem, osm_id, archetype_id), None
    except Exception as exc:
        return None, (sql_path_str, cell, stem, repr(exc))


def main():
    sql_files = _find_sql_files()
    print(f"[T01] .sql files found under corpus: {len(sql_files)}")

    meta = _load_metadata()

    tasks = []
    unmatched = 0
    for p in sql_files:
        stem = p.parent.parent.name
        cell = p.parent.parent.parent.name
        key = f"{cell}/{stem}"
        if key in meta:
            c, osm_id, arche = meta[key]
        else:
            unmatched += 1
            c, osm_id, arche = cell, "", ""
        tasks.append((str(p), c, stem, osm_id, arche))

    print(f"[T01] unmatched-to-census-csv (metadata missing): {unmatched}")

    rows = []
    skipped = []
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(_worker, t) for t in tasks]
        for fut in as_completed(futs):
            row, err = fut.result()
            if row is not None:
                rows.append(row)
            else:
                skipped.append(err)

    print(f"[T01] gated OK: {len(rows)}  skipped/unreadable: {len(skipped)}")
    for s in skipped[:20]:
        print(f"[T01]   skipped: {s}")

    rows.sort(key=lambda r: (r["cell"], r["osm_id"]))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"[T01] wrote {OUT_CSV} ({len(rows)} rows)")

    n = len(rows)
    abups_true = sum(1 for r in rows if r["abups_ok"] is True)
    abups_false = sum(1 for r in rows if r["abups_ok"] is False)
    abups_none = sum(1 for r in rows if r["abups_ok"] is None)
    meter_true = sum(1 for r in rows if r["meter_ok"] is True)
    meter_false = sum(1 for r in rows if r["meter_ok"] is False)
    meter_none = sum(1 for r in rows if r["meter_ok"] is None)
    gas_true = sum(1 for r in rows if r["gas_zero"] is True)
    gas_false = sum(1 for r in rows if r["gas_zero"] is False)
    gas_none = sum(1 for r in rows if r["gas_zero"] is None)

    print(f"[T01] denominator n={n}")
    print(f"[T01] abups_ok True={abups_true} False={abups_false} None={abups_none}")
    print(f"[T01] meter_ok  True={meter_true} False={meter_false} None={meter_none}")
    print(f"[T01] gas_zero  True={gas_true} False={gas_false} None={gas_none}")

    osm_ids = [r["osm_id"] for r in rows]
    c1_count_ok = (len(rows) + len(skipped)) == len(sql_files)
    print(
        f"[T01] C1 sql_found={len(sql_files)} gated_rows={len(rows)} skipped={len(skipped)} "
        f"rows_plus_skipped_eq_sql_found={c1_count_ok}"
    )
    print(f"[T01] C1 osm_id_unique={len(osm_ids) == len(set(osm_ids))}")

    import collections
    by_cell = collections.defaultdict(lambda: [0, 0])
    by_arche = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        by_cell[r["cell"]][1] += 1
        by_arche[r["archetype_id"]][1] += 1
        if r["abups_ok"] is False:
            by_cell[r["cell"]][0] += 1
            by_arche[r["archetype_id"]][0] += 1

    worst_cells = sorted(
        ((k, v[0], v[1], v[0] / v[1] if v[1] else 0.0) for k, v in by_cell.items()),
        key=lambda x: -x[3],
    )[:5]
    worst_arche = sorted(
        ((k, v[0], v[1], v[0] / v[1] if v[1] else 0.0) for k, v in by_arche.items()),
        key=lambda x: -x[3],
    )[:5]
    print("[T01] worst 5 cells by abups_ok-false rate (cell, false, n, rate):")
    for row in worst_cells:
        print(f"[T01]   {row}")
    print("[T01] worst 5 archetypes by abups_ok-false rate (archetype, false, n, rate):")
    for row in worst_arche:
        print(f"[T01]   {row}")

    fleet_false_rate = abups_false / n if n else 0.0
    sample_false_rate = 42 / 48
    print(
        f"[T01] C2 fleet abups_ok false-rate={fleet_false_rate:.4f} ({abups_false}/{n}) "
        f"vs sample 42/48={sample_false_rate:.4f}; "
        f"delta={fleet_false_rate - sample_false_rate:+.4f}"
    )

    random.seed(20260820)
    sample_rows = random.sample(rows, min(5, len(rows)))
    c3_pass = True
    for r in sample_rows:
        re_result = _gate_one(r["sql_path"], r["cell"], r["stem"], r["osm_id"], r["archetype_id"])
        same = (
            re_result["abups_ok"] == r["abups_ok"]
            and re_result["meter_ok"] == r["meter_ok"]
            and re_result["gas_zero"] == r["gas_zero"]
        )
        if not same:
            c3_pass = False
        print(f"[T01] C3 recheck {r['osm_id']}: identical={same}")
    print(f"[T01] C3 overall_pass={c3_pass}")


if __name__ == "__main__":
    main()
