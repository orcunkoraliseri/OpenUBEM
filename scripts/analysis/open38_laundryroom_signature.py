"""OPEN-38 T04 -- is the LAUNDRYROOMFLR1 signature the same mechanism as OPEN-42?

Read-only over the local E02 harvest. Re-derives OPEN-38's population from raw
`eplusout.err` files (does not carry the register's "seven" figure), runs T03's
own upside-down-surface parser over the same runs, determines each fatal zone's
position in its building from `.eio` zone geometry (z-coordinates / ceiling
height / multiplier -- never from the zone name), and compares the result
against OPEN-42's already-audited 16-fatal population
(`open42_six_failure_causes.csv`, `open42_surface_orientation.csv`).

Also answers OPEN-38's second open question: do unfitted subsurfaces occur
below the `Base surface does not surround subsurface` warning threshold, in
buildings that never emit the warning? Cross-checks (does not blindly trust)
`open38_subsurface_census.csv`.

No fix, no code change, no simulation. Diagnosis only. Verdict is a
recommendation -- the director rules on merging or splitting register items.

Emits openubem/outputs/comparisons/open38_laundryroom_signature.csv: one row
per re-derived LAUNDRYROOMFLR1 fatal run, joined to its zone geometry and
orientation-warning counts.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from openubem.results.err_parse import FATAL_RE, SEVERE_RE  # noqa: E402
from openubem import config as ubem_config  # noqa: E402
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP  # noqa: E402

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
OPEN42_CAUSES_CSV = REPO_ROOT / "openubem/outputs/comparisons/open42_six_failure_causes.csv"
SUBSURFACE_CSV = REPO_ROOT / "openubem/outputs/comparisons/open38_subsurface_census.csv"
OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open38_laundryroom_signature.csv"

LAUNDRY_ZONE_TOKEN = "LAUNDRYROOMFLR1"
SUBSURFACE_WARNING_TEXT = "Base surface does not surround subsurface"

# --- reuse, not retype: T03's orientation parser and OPEN-42's zone-geometry helpers ---
_orient_spec = importlib.util.spec_from_file_location(
    "open42_surface_orientation_census", REPO_ROOT / "scripts/analysis/open42_surface_orientation_census.py"
)
orient = importlib.util.module_from_spec(_orient_spec)
_orient_spec.loader.exec_module(orient)

_zg_spec = importlib.util.spec_from_file_location(
    "open42_zone_geometry", REPO_ROOT / "scripts/analysis/open42_zone_geometry.py"
)
zg = importlib.util.module_from_spec(_zg_spec)
_zg_spec.loader.exec_module(zg)

_fc_spec = importlib.util.spec_from_file_location(
    "open42_failure_causes", REPO_ROOT / "scripts/analysis/open42_failure_causes.py"
)
fc = importlib.util.module_from_spec(_fc_spec)
_fc_spec.loader.exec_module(fc)

SEVERE_ZONE_RE = zg.SEVERE_ZONE_RE


def scan_for_laundry_fatal(err_path: Path) -> "dict | None":
    """Scan one .err for a Fatal whose nearest preceding Severe names zone
    LAUNDRYROOMFLR1. Returns None if the run has no fatal or the fatal's
    nearest preceding severe does not name that zone."""
    r = fc.scan_err_file(err_path)
    if not r["has_fatal"]:
        return None
    if LAUNDRY_ZONE_TOKEN not in r["severe_line_text"].upper():
        return None
    return r


def fleet_scan_layout_assign() -> pd.DataFrame:
    rows = []
    n_dirs_scanned = 0
    for stem_dir in sorted((HARVEST_ROOT).glob("*_layout_assign/*")):
        if not stem_dir.is_dir():
            continue
        n_dirs_scanned += 1
        cell = stem_dir.parent.name.replace("_layout_assign", "")
        stem = stem_dir.name
        err_path = stem_dir / "eplusout.err"
        if not err_path.is_file():
            continue
        hit = scan_for_laundry_fatal(err_path)
        if hit is None:
            continue
        end_path = stem_dir / "eplusout.end"
        end_text = end_path.read_text(encoding="utf-8", errors="replace").strip() if end_path.is_file() else ""
        rows.append({
            "cell": cell,
            "stem": stem,
            "mode": "layout_assign",
            "n_severe_total": hit["n_severe_total"],
            "severe_line_text": hit["severe_line_text"],
            "fatal_line_text": hit["fatal_line_text"],
            "temperature_c": hit["temperature"],
            "end_file_text": end_text,
        })
    print(f"Scanned {n_dirs_scanned} layout_assign run directories (expected 8160).")
    return pd.DataFrame(rows)


def zone_geometry_for(cell: str, stem: str, mode: str, zone_token: str) -> dict:
    eio_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.eio"
    zdf = zg.parse_eio_zones(eio_path)
    if zdf.empty:
        return {}
    zdf = zdf.copy()
    zdf["zone_name_upper"] = zdf["zone_name"].astype(str).str.upper()
    hit = zdf[zdf["zone_name_upper"] == zone_token.upper()]
    if hit.empty:
        return {}
    row = hit.iloc[0]
    max_maxz_building = zdf["max_z"].max()
    min_minz_building = zdf["min_z"].min()
    return {
        "n_zones_total": len(zdf),
        "zone_min_z": row["min_z"],
        "zone_max_z": row["max_z"],
        "zone_ceiling_height": row["ceiling_height"],
        "zone_multiplier": row["zone_multiplier"],
        "building_min_z": min_minz_building,
        "building_max_z": max_maxz_building,
        "is_topmost_by_geometry": bool(row["max_z"] >= max_maxz_building - 1e-6),
        "is_bottommost_by_geometry": bool(row["min_z"] <= min_minz_building + 1e-6),
    }


def orientation_signature_for(cell: str, stem: str, mode: str, zone_token: str) -> dict:
    err_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.err"
    ud = orient.parse_upside_down(err_path)
    zone_ud = [u for u in ud if str(u["zone_name"]).upper() == zone_token.upper()]
    sibling_ud = [u for u in ud if str(u["zone_name"]).upper() != zone_token.upper()]
    return {
        "n_upside_down_total": len(ud),
        "n_upside_down_laundry_zone": len(zone_ud),
        "n_upside_down_sibling_zones": len(sibling_ud),
    }


def subsurface_cross_check(pop_df: pd.DataFrame) -> list[str]:
    log = []
    census = pd.read_csv(SUBSURFACE_CSV)
    log.append(f"Existing open38_subsurface_census.csv: {len(census)} rows.")

    fresh_rows = []
    for _, row in pop_df.iterrows():
        err_path = HARVEST_ROOT / f"{row['cell']}_layout_assign" / row["stem"] / "eplusout.err"
        text = err_path.read_text(encoding="utf-8", errors="replace")
        n = text.count(SUBSURFACE_WARNING_TEXT)
        fresh_rows.append({"cell": row["cell"], "stem": row["stem"], "n_subsurface_warning_fresh": n})
    fresh = pd.DataFrame(fresh_rows)

    merged = fresh.merge(
        census[["cell", "stem", "n_occurrences", "terminated"]],
        on=["cell", "stem"], how="left",
    )
    log.append("Fresh re-grep of the 7 LAUNDRYROOMFLR1-fatal runs for "
               f"'{SUBSURFACE_WARNING_TEXT}', cross-checked against the census:")
    log.append(merged.to_string(index=False))

    n_with_warning = int((fresh["n_subsurface_warning_fresh"] > 0).sum())
    log.append(f"Of {len(fresh)} re-derived LAUNDRYROOMFLR1-fatal runs, "
               f"{n_with_warning} also carry the subsurface warning (fresh grep).")

    census_stems = set(zip(census["cell"], census["stem"]))
    pop_stems = set(zip(pop_df["cell"], pop_df["stem"]))
    only_in_census = census_stems - pop_stems
    only_in_pop = pop_stems - census_stems
    log.append(f"In subsurface census but NOT in the re-derived LAUNDRYROOMFLR1-fatal population "
               f"({len(only_in_census)}): {sorted(only_in_census)} "
               f"-- this is the census's own non-fatal control (terminated=False expected).")
    log.append(f"In the re-derived population but NOT in the subsurface census ({len(only_in_pop)}): "
               f"{sorted(only_in_pop)} -- non-empty would mean LAUNDRYROOMFLR1 can fatal without "
               f"the subsurface warning ever firing.")
    return log


def identify_archetype_by_zone_name(zone_token: str) -> list[str]:
    """Scan every baseline IDF named in ARCHETYPE_IDF_MAP (config.BASELINE_IDF_DIR)
    for a Zone object whose name matches zone_token, case-insensitively. Returns
    the list of archetype_ids whose baseline carries that zone -- derived from the
    prototype library itself, not asserted from the .err zone name alone."""
    matches = []
    seen_files = {}
    for archetype_id, filename in ARCHETYPE_IDF_MAP.items():
        if filename in seen_files:
            if seen_files[filename]:
                matches.append(archetype_id)
            continue
        path = ubem_config.BASELINE_IDF_DIR / filename
        if not path.is_file():
            seen_files[filename] = False
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hit = bool(re.search(rf"^\s*{re.escape(zone_token)}\s*,", text, re.IGNORECASE | re.MULTILINE))
        seen_files[filename] = hit
        if hit:
            matches.append(archetype_id)
    return matches


def main():
    print("=== Non-vacuity control (reusing T03's, re-run here independently) ===")
    for line in orient.non_vacuity_control():
        print(line)
    print()

    print("=== Step 1: re-derive OPEN-38's population from raw .err (do not trust the register's 7) ===")
    pop_df = fleet_scan_layout_assign()
    n_found = len(pop_df)
    print(f"RE-DERIVED POPULATION: {n_found} layout_assign runs fatal with nearest-preceding-Severe "
          f"naming zone={LAUNDRY_ZONE_TOKEN!r}.")
    if n_found != 7:
        print(f"*** STOP CONDITION: expected 7 per the plan's hard rule, got {n_found}. "
              f"Reporting as a finding for the director, not silently proceeding on a different count. ***")
    if n_found:
        print(pop_df[["cell", "stem", "n_severe_total", "temperature_c"]].to_string(index=False))

    print("\n=== Step 2: zone geometry (from .eio, not from the name) + T03's orientation parser ===")
    geom_rows = []
    for _, row in pop_df.iterrows():
        geom = zone_geometry_for(row["cell"], row["stem"], "layout_assign", LAUNDRY_ZONE_TOKEN)
        orient_sig = orientation_signature_for(row["cell"], row["stem"], "layout_assign", LAUNDRY_ZONE_TOKEN)
        merged = {**row.to_dict(), **geom, **orient_sig}
        geom_rows.append(merged)
    full_df = pd.DataFrame(geom_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    full_df.to_csv(OUT_CSV, index=False)
    print(f"Wrote {len(full_df)} rows to {OUT_CSV}")
    if not full_df.empty:
        print(full_df[["cell", "stem", "n_zones_total", "zone_min_z", "zone_max_z",
                        "zone_multiplier", "building_max_z", "is_topmost_by_geometry",
                        "is_bottommost_by_geometry", "n_upside_down_total",
                        "n_upside_down_laundry_zone"]].to_string(index=False))

        n_topmost = int(full_df["is_topmost_by_geometry"].sum())
        n_bottommost = int(full_df["is_bottommost_by_geometry"].sum())
        print(f"\nOf {len(full_df)} fatal LAUNDRYROOMFLR1 zones: {n_topmost} sit at the building's "
              f"topmost z-extent, {n_bottommost} sit at the building's bottommost z-extent "
              f"(by max_z/min_z from .eio Zone Information, not by name).")

        n_laundry_ud = int((full_df["n_upside_down_laundry_zone"] > 0).sum())
        n_any_sibling_ud = int((full_df["n_upside_down_sibling_zones"] > 0).sum())
        print(f"LAUNDRYROOMFLR1 itself carries an upside-down warning in {n_laundry_ud}/{len(full_df)} runs.")
        print(f"At least one sibling zone carries an upside-down warning in "
              f"{n_any_sibling_ud}/{len(full_df)} runs.")

    print(f"\n=== Step 2b: which baseline-IDF archetype defines a Zone named {LAUNDRY_ZONE_TOKEN!r}? ===")
    print(f"BASELINE_IDF_DIR = {ubem_config.BASELINE_IDF_DIR}")
    archetype_matches = identify_archetype_by_zone_name(LAUNDRY_ZONE_TOKEN)
    print(f"Archetype(s) whose baseline IDF defines a Zone named {LAUNDRY_ZONE_TOKEN!r}: {archetype_matches}")

    print("\n=== Step 3: comparison against OPEN-42's audited 16-fatal population ===")
    open42 = pd.read_csv(OPEN42_CAUSES_CSV)
    open42_fatal = open42[open42["has_fatal"] == True]
    print(f"OPEN-42 population (from open42_six_failure_causes.csv, director-audited at CP-2): "
          f"{len(open42_fatal)} fatal runs.")
    print("OPEN-42 cause_class distribution:")
    print(open42_fatal["cause_class"].value_counts().to_string())
    print(f"OPEN-42 mode distribution: {sorted(open42_fatal['mode'].unique())}")
    print(f"OPEN-38 mode distribution: {sorted(full_df['mode'].unique()) if not full_df.empty else []}")
    print(f"OPEN-42 temperature range: {open42_fatal['temperature'].min()} to {open42_fatal['temperature'].max()} C")
    if not full_df.empty:
        print(f"OPEN-38 temperature range: {full_df['temperature_c'].astype(float).min()} to "
              f"{full_df['temperature_c'].astype(float).max()} C")

    print("\n=== Step 4: OPEN-38's second open question -- unfitted subsurfaces below the warning threshold? ===")
    for line in subsurface_cross_check(pop_df):
        print(line)
    print("\nANSWER: eplusout.err can only report a subsurface as malformed if EnergyPlus's own CHKSBS "
          "routine already crossed its internal fit threshold and emitted the Warning. A subsurface that "
          "is unfitted but stays inside that threshold produces no line in .err -- there is nothing to "
          "parse, at any file offset. This is NOT DETERMINABLE FROM eplusout.err. The artifact that could "
          "answer it is the IDF geometry itself (base-surface and subsurface vertex loops, checked "
          "independently of CHKSBS's own threshold) -- and per this task's raw-data note, the entire E02 "
          "IDF corpus (ubem_e02_fleet/<cell>/step3_<mode>/idfs/) was emptied by the 2026-08-17 external "
          "disk sweep (OPEN-53 finding). That artifact does not currently exist on disk for this fleet.")


if __name__ == "__main__":
    main()
