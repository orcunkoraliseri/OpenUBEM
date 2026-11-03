from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

J_TO_KWH = 1.0 / 3.6e6
HEATING_VARIABLE = "Zone Ideal Loads Zone Total Heating Energy"
HEATING_FREQUENCY = "Hourly"
IDEAL_SUFFIX = " IDEAL LOADS AIR SYSTEM"
ZONE_RX = re.compile(r"_F(\d+)_DWELLING_(\d+)$", re.IGNORECASE)

ZONE_COLUMNS = ["site", "stem", "zone", "floor", "dwelling", "floor_area_m2", "heating_kwh"]
CASE_COLUMNS = ["site", "folder", "n_sql", "internal_only"]
SPEED_FLEETS = "/speed-scratch/o_iseri/fleets"
DEFAULT_CHUNK = 100

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
RESULTS = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "results"
CMP = ROOT / "openubem" / "outputs" / "comparisons"
CASE_LIST = CMP / "paper_eu_flat_case_list_2026-10-21.csv"
SPREAD_CSV = CMP / "paper_eu_flat_spread_2026-10-21.csv"
CHECK_CSV = CMP / "paper_eu_flat_check_2026-10-21.csv"
EU11_PER_HOME = RESULTS / "EU11_results_2026-10-08_per_home.csv"


@dataclass(frozen=True)
class Site:
    site: str
    fleet: str
    tag: str
    n_sql: int
    internal_only: bool
    per_home: Path

    @property
    def folder(self) -> str:
        return f"{SPEED_FLEETS}/{self.fleet}_{self.site}_win_{self.tag}"

    @property
    def tree(self) -> Path:
        return EVID / f"{self.site}_win_{self.tag}"


def _eu22(site: str, tag: str, n: int, internal: bool = False) -> Site:
    return Site(site, "EU22", tag, n, internal, RESULTS / f"EU22_results_{site}_{tag}_per_home.csv")


def _eu11(site: str, n: int) -> Site:
    return Site(site, "EU11", "2026-10-06", n, False, EU11_PER_HOME)


SITES: list[Site] = [
    _eu22("AM-EVN-NORNORK", "2026-10-09", 551),
    _eu22("CA-MTL-PLATEAU", "2026-10-09", 710),
    _eu22("ZA-CPT-WOODSTOCK", "2026-10-09", 525, internal=True),
    _eu22("FI-HEL-KALLIO", "2026-10-10", 580),
    _eu22("AT-VIE-RUDOLFSHEIM", "2026-10-10", 536),
    _eu22("HU-BUD-ERZSEBETVAROS", "2026-10-10", 805),
    _eu11("ES-MAD-BERRUGUETE", 1172),
    _eu11("FR-LYO-HAUTCOEURPENTES", 522),
    _eu11("GB-LDN-STDUNSTANS", 1240),
    _eu11("IT-BOL-GALVANI2", 1179),
]


def parse_zone_name(zone: str) -> tuple[int | None, int | None]:
    m = ZONE_RX.search(zone.strip())
    if m is None:
        return None, None
    return int(m.group(1)), int(m.group(2))


def _connect(sql_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(sql_path).as_posix()}?mode=ro", uri=True)


_HEATING_QUERY = """
SELECT d.KeyValue, SUM(r.Value)
FROM ReportData r
JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
JOIN Time t ON r.TimeIndex = t.TimeIndex
WHERE d.Name = ? AND d.ReportingFrequency = ?
  AND (t.WarmupFlag IS NULL OR t.WarmupFlag = 0)
GROUP BY d.KeyValue
"""


def read_zones(sql_path: Path, site: str, stem: str) -> list[dict]:
    conn = _connect(Path(sql_path))
    try:
        heating = conn.execute(_HEATING_QUERY, (HEATING_VARIABLE, HEATING_FREQUENCY)).fetchall()
        zones = conn.execute(
            "SELECT ZoneName, FloorArea, Multiplier, ListMultiplier FROM Zones"
        ).fetchall()
    finally:
        conn.close()
    if not heating:
        raise ValueError(f"no hourly '{HEATING_VARIABLE}' in {sql_path}")
    by_zone = {}
    for name, area, mult, lmult in zones:
        m = (mult if mult is not None else 1.0) * (lmult if lmult is not None else 1.0)
        by_zone[str(name).strip().upper()] = (str(name).strip(), float(area or 0.0), float(m))
    rows = []
    for key, joules in heating:
        zkey = str(key).strip().upper()
        if zkey.endswith(IDEAL_SUFFIX):
            zkey = zkey[: -len(IDEAL_SUFFIX)]
        if zkey not in by_zone:
            raise ValueError(f"heating key '{key}' has no zone in {sql_path}")
        zone, area, m = by_zone[zkey]
        floor, dwelling = parse_zone_name(zone)
        rows.append({
            "site": site,
            "stem": stem,
            "zone": zone,
            "floor": floor,
            "dwelling": dwelling,
            "floor_area_m2": area * m,
            "heating_kwh": float(joules) * m * J_TO_KWH,
        })
    rows.sort(key=lambda r: (r["floor"] is None, r["floor"] or 0, r["dwelling"] or 0, r["zone"]))
    return rows


def list_stems(folder: Path) -> list[str]:
    out = Path(folder) / "out"
    return sorted(p.parent.name for p in out.glob("*/eplusout.sql"))


def chunk_stems(stems: list[str], chunk_index: int, chunk_size: int) -> list[str]:
    start = chunk_index * chunk_size
    return stems[start:start + chunk_size]


def n_chunks(n_sql: int, chunk_size: int) -> int:
    return -(-n_sql // chunk_size)


def run_chunk(folder: Path, site: str, chunk_index: int, chunk_size: int, out_csv: Path) -> tuple[int, int]:
    stems = chunk_stems(list_stems(folder), chunk_index, chunk_size)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    bad_path = out_csv.with_name(out_csv.stem + "_bad.csv")
    done = 0
    bad = []
    with out_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=ZONE_COLUMNS)
        writer.writeheader()
        for stem in stems:
            try:
                rows = read_zones(Path(folder) / "out" / stem / "eplusout.sql", site, stem)
            except Exception as exc:
                bad.append((stem, f"{type(exc).__name__}: {exc}"))
                print(f"BAD {stem}: {exc}", file=sys.stderr)
                continue
            writer.writerows(rows)
            done += 1
    with bad_path.open("w", newline="", encoding="utf-8") as stream:
        w = csv.writer(stream)
        w.writerow(["stem", "error"])
        w.writerows(bad)
    return done, len(bad)


def write_case_list(path: Path = CASE_LIST) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        w = csv.writer(stream, lineterminator="\n")
        w.writerow(CASE_COLUMNS)
        for s in SITES:
            w.writerow([s.site, s.folder, s.n_sql, 1 if s.internal_only else 0])
    return len(SITES)


def array_size(chunk_size: int = DEFAULT_CHUNK) -> int:
    return sum(n_chunks(s.n_sql, chunk_size) for s in SITES)


def building_spread(zones):
    import numpy as np
    import pandas as pd

    z = zones.copy()
    z["eui"] = z["heating_kwh"] / z["floor_area_m2"].where(z["floor_area_m2"] > 0)
    rows = []
    for (site, stem), g in z.groupby(["site", "stem"], sort=True):
        dw = g[g["floor"].notna()]
        e = dw["eui"].dropna()
        row = {
            "site": site,
            "stem": stem,
            "n_zones": len(g),
            "n_flats": len(dw),
            "floor_area_m2": g["floor_area_m2"].sum(),
            "heating_kwh": g["heating_kwh"].sum(),
        }
        row["eui_kwh_m2"] = row["heating_kwh"] / row["floor_area_m2"] if row["floor_area_m2"] > 0 else np.nan
        if len(e) >= 1:
            row["flat_eui_min"] = e.min()
            row["flat_eui_max"] = e.max()
            row["flat_eui_mean"] = e.mean()
            row["spread_kwh_m2"] = e.max() - e.min()
            row["spread_ratio"] = e.max() / e.min() if e.min() > 0 else np.nan
        else:
            for c in ("flat_eui_min", "flat_eui_max", "flat_eui_mean", "spread_kwh_m2", "spread_ratio"):
                row[c] = np.nan
        row["n_floors"] = int(dw["floor"].nunique())
        if row["n_floors"] >= 3:
            top, ground = dw["floor"].max(), dw["floor"].min()
            top_e = dw.loc[dw["floor"] == top, "eui"].dropna()
            mid_e = dw.loc[(dw["floor"] > ground) & (dw["floor"] < top), "eui"].dropna()
            row["top_floor_eui_mean"] = top_e.mean() if len(top_e) else np.nan
            row["middle_floor_eui_mean"] = mid_e.mean() if len(mid_e) else np.nan
            row["top_minus_middle_kwh_m2"] = row["top_floor_eui_mean"] - row["middle_floor_eui_mean"]
            row["top_over_middle"] = (
                row["top_floor_eui_mean"] / row["middle_floor_eui_mean"]
                if row["middle_floor_eui_mean"] and row["middle_floor_eui_mean"] > 0 else np.nan
            )
        else:
            for c in ("top_floor_eui_mean", "middle_floor_eui_mean", "top_minus_middle_kwh_m2", "top_over_middle"):
                row[c] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def stem_map(site: Site):
    import pandas as pd

    prep = pd.read_csv(site.tree / "prepared_buildings.csv", dtype=str, usecols=["building_id", "stem"])
    return dict(zip(prep["stem"], prep["building_id"].str.strip()))


def reference_heating(site: Site):
    import pandas as pd

    ref = pd.read_csv(site.per_home, dtype={"building_id": str})
    if "district" in ref.columns:
        ref = ref[ref["district"] == site.site]
    if "tag" in ref.columns:
        ref = ref[ref["tag"] == f"win_{site.tag}"]
    ref = ref[ref["has_result"].astype(str).str.lower() == "true"]
    ref["building_id"] = ref["building_id"].str.strip()
    return ref.set_index("building_id")[["heating_kwh", "floor_area_m2"]]


def merge_parts(parts_dir: Path, tolerance: float = 1e-3):
    import numpy as np
    import pandas as pd

    parts_dir = Path(parts_dir)
    frames = [pd.read_csv(p) for p in sorted(parts_dir.glob("*.csv")) if not p.stem.endswith("_bad")]
    if not frames:
        raise ValueError(f"no part files in {parts_dir}")
    zones = pd.concat(frames, ignore_index=True)
    spread = building_spread(zones)
    spread.insert(2, "building_id", "")
    spread["internal_only"] = 0
    spread["ref_heating_kwh"] = np.nan
    spread["ref_floor_area_m2"] = np.nan
    for s in SITES:
        mask = spread["site"] == s.site
        if not mask.any():
            continue
        spread.loc[mask, "building_id"] = spread.loc[mask, "stem"].map(stem_map(s)).fillna("")
        spread.loc[mask, "internal_only"] = 1 if s.internal_only else 0
        ref = reference_heating(s)
        ids = spread.loc[mask, "building_id"]
        spread.loc[mask, "ref_heating_kwh"] = ids.map(ref["heating_kwh"]).to_numpy(dtype=float)
        spread.loc[mask, "ref_floor_area_m2"] = ids.map(ref["floor_area_m2"]).to_numpy(dtype=float)
    has_ref = spread["ref_heating_kwh"].notna()
    spread["heating_rel_diff"] = np.where(
        has_ref, (spread["heating_kwh"] - spread["ref_heating_kwh"]).abs() / spread["ref_heating_kwh"].abs(), np.nan
    )
    spread["heating_check"] = np.where(
        ~has_ref, "no_reference", np.where(spread["heating_rel_diff"] <= tolerance, "pass", "fail")
    )
    check = (
        spread.groupby("site")
        .agg(
            buildings=("stem", "size"),
            with_reference=("ref_heating_kwh", lambda s: int(s.notna().sum())),
            passed=("heating_check", lambda s: int((s == "pass").sum())),
            failed=("heating_check", lambda s: int((s == "fail").sum())),
            max_rel_diff=("heating_rel_diff", "max"),
        )
        .reset_index()
    )
    return spread, check


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-flat heating from EU eplusout.sql files")
    sub = parser.add_subparsers(dest="cmd", required=True)

    one = sub.add_parser("zones")
    one.add_argument("sql")
    one.add_argument("--site", required=True)
    one.add_argument("--stem", required=True)
    one.add_argument("--out", required=True)

    ch = sub.add_parser("chunk")
    ch.add_argument("--folder", required=True)
    ch.add_argument("--site", required=True)
    ch.add_argument("--chunk-index", type=int, required=True)
    ch.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK)
    ch.add_argument("--out", required=True)

    cl = sub.add_parser("cases")
    cl.add_argument("--out", default=str(CASE_LIST))

    mg = sub.add_parser("merge")
    mg.add_argument("--parts", required=True)
    mg.add_argument("--out", default=str(SPREAD_CSV))
    mg.add_argument("--check-out", default=str(CHECK_CSV))

    args = parser.parse_args(argv)
    if args.cmd == "zones":
        rows = read_zones(Path(args.sql), args.site, args.stem)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as stream:
            w = csv.DictWriter(stream, fieldnames=ZONE_COLUMNS)
            w.writeheader()
            w.writerows(rows)
        print(len(rows))
    elif args.cmd == "chunk":
        done, bad = run_chunk(Path(args.folder), args.site, args.chunk_index, args.chunk_size, Path(args.out))
        print(f"done={done} bad={bad}")
    elif args.cmd == "cases":
        print(write_case_list(Path(args.out)))
    elif args.cmd == "merge":
        spread, check = merge_parts(Path(args.parts))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        spread.to_csv(args.out, index=False)
        check.to_csv(args.check_out, index=False)
        print(len(spread), int((spread["heating_check"] == "fail").sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
