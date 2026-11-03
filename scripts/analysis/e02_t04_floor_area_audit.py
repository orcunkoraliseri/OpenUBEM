"""T04 -- E02 floor-area audit (OPEN-01 a/b, OPEN-02, OPEN-28, OPEN-35).

Parses all 40,800 .eio files in the E02 harvest for the multiplier-aware
simulated floor area, joins to the declared denominator
(footprint_area_m2 x levels from the adopted phaseE/<cell>/05_results.csv),
and reports the error factor per mode.

Read-only. No cluster access. No pipeline logic is reimplemented -- every
comparison value is read from an artifact the pipeline (or a prior
measurement task) already wrote.

Run: ./.venv/Scripts/python.exe scripts/analysis/e02_t04_floor_area_audit.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
FLEET_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_fleet")
PHASE_E_ROOT = Path(
    r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_VALIDATION\validations\overAll\results\phaseE"
)
OUT_DIR = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")

SIM_CSV = OUT_DIR / "e02_simulated_floor_area.csv"
AUDIT_CSV = OUT_DIR / "open01_denominator_audit.csv"

HEADER_MARKER = "! <Zone Information>"
DATA_PREFIX = " Zone Information,"

FIELD_FLOOR_AREA = "Floor Area {m2}"
FIELD_ZONE_MULT = "Zone Multiplier"
FIELD_ZONE_LIST_MULT = "Zone List Multiplier"
FIELD_PART_OF_TOTAL = "Part of Total Building Area"


def osm_id_to_stem(osm_id: str) -> str:
    return osm_id.replace("/", "_")


def stem_to_osm_id(stem: str) -> str:
    return stem.replace("_", "/", 1)


def parse_eio_zone_area(path: Path) -> dict:
    """Stream one .eio file, header-name-mapped, early-exit after the block."""
    header_idx = None
    n_zones = 0
    area_plain = 0.0
    area_mult = 0.0
    max_zm = 0.0
    max_zlm = 0.0
    n_excluded = 0
    n_row_errors = 0
    saw_header = False
    in_block = False

    try:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            for line in f:
                if not saw_header:
                    if line.startswith(HEADER_MARKER):
                        raw = next(csv.reader([line]))
                        names = [c.strip() for c in raw]
                        header_idx = {name: i for i, name in enumerate(names)}
                        saw_header = True
                    continue
                if line.startswith(DATA_PREFIX):
                    in_block = True
                    n_zones += 1
                    try:
                        row = next(csv.reader([line]))
                        floor_area = float(row[header_idx[FIELD_FLOOR_AREA]])
                        zm = float(row[header_idx[FIELD_ZONE_MULT]])
                        zlm = float(row[header_idx[FIELD_ZONE_LIST_MULT]])
                        part = row[header_idx[FIELD_PART_OF_TOTAL]].strip()
                    except (KeyError, ValueError, IndexError):
                        n_row_errors += 1
                        continue
                    if zm > max_zm:
                        max_zm = zm
                    if zlm > max_zlm:
                        max_zlm = zlm
                    if part == "Yes":
                        area_plain += floor_area
                        area_mult += floor_area * zm * zlm
                    else:
                        n_excluded += 1
                elif in_block:
                    break
    except OSError as e:
        return dict(
            n_zones=0, area_plain_m2=0.0, area_multiplier_aware_m2=0.0,
            max_zone_multiplier=0, max_zone_list_multiplier=0,
            n_zones_excluded_not_in_total_area=0,
            parse_status=f"file_error:{e}",
        )

    if not saw_header:
        status = "no_zone_information_header"
    elif n_zones == 0:
        status = "header_found_zero_rows"
    elif n_row_errors > 0:
        status = f"ok_with_{n_row_errors}_row_errors"
    else:
        status = "ok"

    return dict(
        n_zones=n_zones,
        area_plain_m2=area_plain,
        area_multiplier_aware_m2=area_mult,
        max_zone_multiplier=int(round(max_zm)),
        max_zone_list_multiplier=int(round(max_zlm)),
        n_zones_excluded_not_in_total_area=n_excluded,
        parse_status=status,
    )


def stage1_parse_corpus() -> None:
    on_disk = sorted(p.name for p in HARVEST_ROOT.iterdir() if p.is_dir())
    expected = sorted(f"{c}_{m}" for c in CELLS for m in MODES)
    if on_disk != expected:
        missing = sorted(set(expected) - set(on_disk))
        extra = sorted(set(on_disk) - set(expected))
        print(f"FATAL: harvest root array set mismatch. missing={missing} extra={extra}", file=sys.stderr)
        sys.exit(1)
    print(f"[stage1] array-dir cross-product check OK: {len(on_disk)} arrays == 12 cells x 5 modes", file=sys.stderr)

    fieldnames = [
        "cell", "mode", "stem", "n_zones", "area_plain_m2", "area_multiplier_aware_m2",
        "max_zone_multiplier", "max_zone_list_multiplier",
        "n_zones_excluded_not_in_total_area", "parse_status",
    ]
    n_total = 0
    n_ok = 0
    n_fail = 0
    fail_examples = []

    with open(SIM_CSV, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        for cell in CELLS:
            for mode in MODES:
                array_dir = HARVEST_ROOT / f"{cell}_{mode}"
                n_this_array = 0
                for entry in sorted(p.name for p in array_dir.iterdir() if p.is_dir()):
                    stem = entry
                    eio_path = array_dir / stem / "eplusout.eio"
                    result = parse_eio_zone_area(eio_path)
                    row = {"cell": cell, "mode": mode, "stem": stem, **result}
                    writer.writerow(row)
                    n_total += 1
                    n_this_array += 1
                    if result["parse_status"] == "ok" or result["parse_status"].startswith("ok_with_"):
                        n_ok += 1
                    else:
                        n_fail += 1
                        if len(fail_examples) < 20:
                            fail_examples.append((cell, mode, stem, result["parse_status"]))
                print(f"[stage1] {cell}_{mode}: {n_this_array} buildings parsed", file=sys.stderr)

    print(f"[stage1] TOTAL parsed: {n_total}, ok: {n_ok}, fail: {n_fail}", file=sys.stderr)
    if fail_examples:
        print(f"[stage1] fail examples (up to 20): {fail_examples}", file=sys.stderr)


def stage2_build_audit() -> None:
    sim = pd.read_csv(SIM_CSV)
    sim["osm_id"] = sim["stem"].apply(stem_to_osm_id)

    manifest_frames = []
    for cell in CELLS:
        for mode in MODES:
            mpath = FLEET_ROOT / cell / f"step3_{mode}" / "03_manifest.parquet"
            mdf = pd.read_parquet(mpath, columns=["osm_id", "archetype_id", "zoning_strategy"])
            mdf["cell"] = cell
            mdf["mode"] = mode
            manifest_frames.append(mdf)
    manifest = pd.concat(manifest_frames, ignore_index=True)
    manifest = manifest.rename(
        columns={"archetype_id": "archetype_id_manifest", "zoning_strategy": "zoning_strategy_manifest"}
    )
    print(f"[stage2] manifest rows loaded: {len(manifest)}", file=sys.stderr)

    declared_frames = []
    for cell in CELLS:
        dpath = PHASE_E_ROOT / cell / "05_results.csv"
        ddf = pd.read_csv(
            dpath,
            usecols=["osm_id", "footprint_area_m2", "levels", "archetype_id", "zoning_strategy", "simulation_status"],
        )
        ddf["cell"] = cell
        declared_frames.append(ddf)
    declared = pd.concat(declared_frames, ignore_index=True)
    declared = declared.rename(
        columns={"archetype_id": "archetype_id_results", "zoning_strategy": "zoning_strategy_results"}
    )
    declared["declared_area_m2"] = declared["footprint_area_m2"] * declared["levels"]
    print(f"[stage2] declared (05_results) rows loaded: {len(declared)}", file=sys.stderr)

    dup_declared = declared.duplicated(subset=["cell", "osm_id"]).sum()
    if dup_declared:
        print(f"[stage2] WARNING: {dup_declared} duplicate (cell, osm_id) rows in declared set", file=sys.stderr)

    sim_manifest = pd.merge(sim, manifest, on=["cell", "mode", "osm_id"], how="left", indicator="_manifest_merge")
    n_manifest_unmatched = (sim_manifest["_manifest_merge"] == "left_only").sum()
    print(f"[stage2] corpus rows with NO manifest match: {n_manifest_unmatched}", file=sys.stderr)
    sim_manifest = sim_manifest.drop(columns=["_manifest_merge"])

    merged_parts = []
    join_counts = {}
    for mode in MODES:
        sim_m = sim_manifest[sim_manifest["mode"] == mode].copy()
        m = pd.merge(sim_m, declared, on=["cell", "osm_id"], how="outer", indicator=True)
        m["mode"] = m["mode"].fillna(mode)
        n_matched = (m["_merge"] == "both").sum()
        n_corpus_only = (m["_merge"] == "left_only").sum()
        n_results_only = (m["_merge"] == "right_only").sum()
        join_counts[mode] = dict(matched=int(n_matched), corpus_only=int(n_corpus_only), results_only=int(n_results_only))
        m["join_status"] = m["_merge"].map(
            {"both": "matched", "left_only": "corpus_only_no_results_row", "right_only": "results_only_no_corpus_dir"}
        )
        m = m.drop(columns=["_merge"])
        merged_parts.append(m)

    audit = pd.concat(merged_parts, ignore_index=True)
    audit["error_factor"] = audit["area_multiplier_aware_m2"] / audit["declared_area_m2"]
    audit.loc[audit["declared_area_m2"].isna() | (audit["declared_area_m2"] == 0), "error_factor"] = pd.NA

    cols = [
        "cell", "mode", "stem", "n_zones", "area_plain_m2", "area_multiplier_aware_m2",
        "max_zone_multiplier", "max_zone_list_multiplier", "n_zones_excluded_not_in_total_area",
        "parse_status", "osm_id", "footprint_area_m2", "levels", "declared_area_m2", "error_factor",
        "archetype_id_manifest", "archetype_id_results", "zoning_strategy_manifest", "zoning_strategy_results",
        "join_status",
    ]
    audit = audit[cols]
    audit.to_csv(AUDIT_CSV, index=False)
    print(f"[stage2] wrote {AUDIT_CSV} ({len(audit)} rows)", file=sys.stderr)

    print("[stage2] join counts per mode (matched / corpus_only / results_only):", file=sys.stderr)
    for mode, c in join_counts.items():
        print(f"  {mode}: {c}", file=sys.stderr)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stage1_parse_corpus()
    stage2_build_audit()
    print("DONE", file=sys.stderr)
