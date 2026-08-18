"""OPEN-42 zoning mechanism diagnosis.

Read-only over the local E02 harvest. For the 6 buildings x 5 modes = 30 runs in
openubem/outputs/comparisons/open42_six_failure_causes.csv, parse the `Zone
Information` records EnergyPlus wrote into each run's eplusout.eio, and identify
what distinguishes the runs that blew up (Fatal, "Temperature (low|high) out of
bounds") from the runs that did not.

Also builds a background control: the same per-zone statistics for >=20
successful buildings in the same two cells (la_rural, la_urban), across the
same five modes, to test whether any candidate statistic actually separates
failing from succeeding runs (rather than just being a plausible story).

No fix, no code change, no simulation. Diagnosis only.

Emits openubem/outputs/comparisons/open42_zone_geometry.csv: one row per zone,
across both the 30 target runs and the background sample.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
CAUSES_CSV = REPO_ROOT / "openubem/outputs/comparisons/open42_six_failure_causes.csv"
OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open42_zone_geometry.csv"

MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]
TARGET_CELLS = ["la_rural", "la_urban"]
TARGET_STEMS = {
    "la_rural": [
        "way_472960972", "way_472961034", "way_472961088",
        "way_472961091", "way_472961171",
    ],
    "la_urban": ["way_402215469"],
}

ZONE_INFO_COLUMNS = [
    "zone_name", "north_axis_deg", "origin_x", "origin_y", "origin_z",
    "centroid_x", "centroid_y", "centroid_z", "zone_type",
    "zone_multiplier", "zone_list_multiplier",
    "min_x", "max_x", "min_y", "max_y", "min_z", "max_z",
    "ceiling_height", "volume",
    "inside_convection_algo", "outside_convection_algo",
    "floor_area", "ext_gross_wall_area", "ext_net_wall_area", "ext_window_area",
    "n_surfaces", "n_subsurfaces", "n_shading_subsurfaces", "part_of_total_building_area",
]

FLOOR_SUFFIX_RE = re.compile(r"_F(\d+)_", re.IGNORECASE)
SEVERE_ZONE_RE = re.compile(r'zone="([^"]+)"', re.IGNORECASE)


def parse_eio_zones(eio_path: Path) -> pd.DataFrame:
    rows = []
    if not eio_path.is_file():
        return pd.DataFrame(columns=["zone_name"])
    with open(eio_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.startswith(" Zone Information,"):
                continue
            parts = [p.strip() for p in line.rstrip("\n").split(",")]
            # parts[0] == "Zone Information" (leading space stripped by split logic below)
            values = parts[1:]
            if len(values) < len(ZONE_INFO_COLUMNS):
                continue
            row = dict(zip(ZONE_INFO_COLUMNS, values))
            rows.append(row)
    if not rows:
        return pd.DataFrame(columns=["zone_name"])
    df = pd.DataFrame(rows)
    numeric_cols = [c for c in ZONE_INFO_COLUMNS if c not in
                    ("zone_name", "zone_type", "inside_convection_algo",
                     "outside_convection_algo", "part_of_total_building_area")]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["extent_x"] = df["max_x"] - df["min_x"]
    df["extent_y"] = df["max_y"] - df["min_y"]
    df["extent_z"] = df["max_z"] - df["min_z"]
    df["footprint_diagonal_m"] = (df["extent_x"] ** 2 + df["extent_y"] ** 2) ** 0.5
    long_side = df[["extent_x", "extent_y"]].max(axis=1)
    short_side = df[["extent_x", "extent_y"]].min(axis=1).clip(lower=1e-6)
    df["aspect_ratio"] = long_side / short_side
    df["volume_over_floor_area"] = df["volume"] / df["floor_area"].replace(0, pd.NA)
    # If Zone Information's own Volume were consistent with Floor Area x Ceiling
    # Height, this ratio would equal 1.0. Departure flags a zone whose reported
    # air volume does not match its own reported footprint x height.
    df["volume_consistency_ratio"] = df["volume_over_floor_area"] / df["ceiling_height"].replace(0, pd.NA)

    def _floor_index(name: str):
        m = FLOOR_SUFFIX_RE.search(str(name))
        return int(m.group(1)) if m else None

    df["floor_index"] = df["zone_name"].apply(_floor_index)
    return df


def mark_top_floor(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if df.empty or "floor_index" not in df.columns:
        df["is_top_floor_zone"] = pd.NA
        return df
    df = df.copy()
    max_floor = df.groupby(group_cols)["floor_index"].transform("max")
    df["is_top_floor_zone"] = df["floor_index"].notna() & (df["floor_index"] == max_floor)
    return df


def build_run_rows(cell: str, stem: str, mode: str, run_label: str) -> pd.DataFrame:
    eio_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.eio"
    df = parse_eio_zones(eio_path)
    if df.empty:
        return df
    df["cell"] = cell
    df["stem"] = stem
    df["mode"] = mode
    df["run_label"] = run_label
    return df


def find_severe_zone(cell: str, stem: str, mode: str) -> "str | None":
    """Independently re-read eplusout.err for this run and pull the zone named
    in the run's own Temperature-out-of-bounds Severe line (not trusted from the
    causes CSV alone -- re-derived here as a cross-check)."""
    err_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.err"
    if not err_path.is_file():
        return None
    with open(err_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "Temperature" in line and "out of bounds" in line and "zone=" in line.lower():
                m = SEVERE_ZONE_RE.search(line)
                if m:
                    return m.group(1)
    return None


def find_successful_background_buildings(cell: str, n_needed: int, exclude_stems: set[str]) -> list[str]:
    """A building counts as part of the background sample if it succeeds
    (eplusout.end says 'Completed Successfully') in ALL FIVE modes -- the same
    shape of evidence available for the 6 target buildings (which were run in
    all 5 modes each)."""
    auto_dir = HARVEST_ROOT / f"{cell}_auto"
    candidates = sorted(p.name for p in auto_dir.iterdir() if p.is_dir() and p.name not in exclude_stems)
    chosen = []
    for stem in candidates:
        ok_all_modes = True
        for mode in MODES:
            end_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.end"
            if not end_path.is_file():
                ok_all_modes = False
                break
            text = end_path.read_text(encoding="utf-8", errors="replace")
            if "Completed Successfully" not in text:
                ok_all_modes = False
                break
        if ok_all_modes:
            chosen.append(stem)
        if len(chosen) >= n_needed:
            break
    return chosen


def main() -> None:
    causes = pd.read_csv(CAUSES_CSV)
    assert len(causes) == 30, f"expected 30 rows in causes csv, got {len(causes)}"

    # --- 1. Target population: 30 runs, one row per zone ---
    target_frames = []
    for _, row in causes.iterrows():
        cell, stem, mode = row["cell"], row["stem"], row["mode"]
        zdf = build_run_rows(cell, stem, mode, run_label="target")
        if zdf.empty:
            print(f"WARNING: no zones parsed for {cell}/{stem}/{mode}")
            continue
        target_frames.append(zdf)
    target_df = pd.concat(target_frames, ignore_index=True) if target_frames else pd.DataFrame()
    target_df = add_derived(target_df)
    target_df = mark_top_floor(target_df, ["cell", "stem", "mode"])

    # Row-count check: 30 runs, every one present or explicitly accounted for.
    n_runs_found = target_df.groupby(["cell", "stem", "mode"]).ngroups if not target_df.empty else 0
    print(f"Target runs with zones parsed: {n_runs_found} / 30")
    if n_runs_found != 30:
        found_keys = set(target_df.groupby(["cell", "stem", "mode"]).groups.keys())
        all_keys = set(zip(causes["cell"], causes["stem"], causes["mode"]))
        missing = all_keys - found_keys
        print(f"MISSING runs (no zones parsed): {sorted(missing)}")

    # Join outcome + independently re-derived severe-zone name
    causes_idx = causes.set_index(["cell", "stem", "mode"])
    target_df = target_df.merge(
        causes[["cell", "stem", "mode", "has_fatal", "cause_class", "severe_line_text", "n_severe_total"]],
        on=["cell", "stem", "mode"], how="left",
    )

    # Primary source: the zone named in the causes CSV's own severe_line_text,
    # which is tied to severe_line_no immediately preceding the Fatal line for
    # that run (already established, authoritative per-run evidence -- OPEN-42's
    # own prior measurement). Extracted here via regex, not retyped by hand.
    def _extract_zone_from_csv_text(text):
        if pd.isna(text):
            return None
        m = SEVERE_ZONE_RE.search(str(text))
        return m.group(1) if m else None

    causes = causes.copy()
    causes["csv_severe_zone"] = causes["severe_line_text"].apply(_extract_zone_from_csv_text)
    csv_severe_zone_map = {
        (r["cell"], r["stem"], r["mode"]): r["csv_severe_zone"] for _, r in causes.iterrows()
    }

    # Secondary, independent cross-check: re-read eplusout.err directly and grab
    # the FIRST "Temperature ... out of bounds ... zone=" line in the file. This
    # can legitimately differ from the CSV's zone (a run can log more than one
    # such Severe before the one immediately preceding the Fatal termination) --
    # any mismatch is reported as a discrepancy, not silently overridden.
    independent_severe_zone_map = {}
    for _, row in causes.iterrows():
        key = (row["cell"], row["stem"], row["mode"])
        independent_severe_zone_map[key] = find_severe_zone(row["cell"], row["stem"], row["mode"])

    def _lookup_csv_zone(r):
        return csv_severe_zone_map.get((r["cell"], r["stem"], r["mode"]))

    def _lookup_independent_zone(r):
        return independent_severe_zone_map.get((r["cell"], r["stem"], r["mode"]))

    target_df["run_severe_zone_name"] = target_df.apply(_lookup_csv_zone, axis=1)
    target_df["run_severe_zone_name_independent_reread"] = target_df.apply(_lookup_independent_zone, axis=1)
    target_df["is_blowup_zone"] = (
        target_df["zone_name"].str.upper() == target_df["run_severe_zone_name"].str.upper()
    )

    n_discrepant = 0
    for key, csv_zone in csv_severe_zone_map.items():
        indep_zone = independent_severe_zone_map.get(key)
        if pd.notna(csv_zone) and pd.notna(indep_zone) and str(csv_zone).upper() != str(indep_zone).upper():
            n_discrepant += 1
            print(f"NOTE: independent .err re-read disagrees with causes-CSV zone for {key}: "
                  f"CSV says {csv_zone!r}, first-in-file says {indep_zone!r} "
                  f"(run logged >1 Temperature-out-of-bounds Severe; CSV's is the one immediately "
                  f"preceding the Fatal termination and is treated as authoritative)")
    print(f"Independent-reread vs CSV-zone discrepancies: {n_discrepant}")

    # --- 2. Background control: >=20 successful buildings, same 2 cells, same 5 modes ---
    exclude = {s for stems in TARGET_STEMS.values() for s in stems}
    bg_stems_by_cell = {}
    n_per_cell = 10  # 10 + 10 = 20 buildings minimum
    for cell in TARGET_CELLS:
        chosen = find_successful_background_buildings(cell, n_per_cell, exclude)
        bg_stems_by_cell[cell] = chosen
        print(f"Background sample for {cell}: {len(chosen)} buildings succeeding in all 5 modes: {chosen}")

    bg_frames = []
    for cell, stems in bg_stems_by_cell.items():
        for stem in stems:
            for mode in MODES:
                zdf = build_run_rows(cell, stem, mode, run_label="background")
                if not zdf.empty:
                    bg_frames.append(zdf)
    bg_df = pd.concat(bg_frames, ignore_index=True) if bg_frames else pd.DataFrame()
    bg_df = add_derived(bg_df)
    bg_df = mark_top_floor(bg_df, ["cell", "stem", "mode"])
    bg_df["has_fatal"] = False
    bg_df["cause_class"] = "BACKGROUND_SUCCESS"
    bg_df["severe_line_text"] = ""
    bg_df["n_severe_total"] = 0
    bg_df["run_severe_zone_name"] = None
    bg_df["is_blowup_zone"] = False

    n_bg_buildings = sum(len(v) for v in bg_stems_by_cell.values())
    print(f"Total background buildings: {n_bg_buildings} (>= 20 required: {n_bg_buildings >= 20})")

    # --- 3. Combine + write ---
    all_df = pd.concat([target_df, bg_df], ignore_index=True, sort=False)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    all_df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(all_df)} zone rows ({len(target_df)} target + {len(bg_df)} background) to {OUT_CSV}")

    # --- 4. Candidate statistic A: is the blow-up zone on the topmost floor for its run? ---
    print("\n--- Candidate statistic A: blow-up zone is on the topmost floor ---")
    blowup_rows = target_df[target_df["is_blowup_zone"] & (target_df["has_fatal"] == True)]
    n_blowup_found = len(blowup_rows)
    n_blowup_top = int(blowup_rows["is_top_floor_zone"].fillna(False).sum())
    print(f"Fatal blow-up zones identified (CSV severe_line_text, cross-referenced by osm zone name): "
          f"{n_blowup_found} / 16 expected failing runs")
    print(f"Of those, on the topmost floor for their building: {n_blowup_top} / {n_blowup_found}")
    if n_blowup_found < n_blowup_top or n_blowup_found != 16:
        pass
    non_top = blowup_rows[blowup_rows["is_top_floor_zone"].fillna(False) == False]
    if len(non_top):
        print("Fatal blow-up zones NOT on the topmost floor (reported, not hidden):")
        print(non_top[["cell", "stem", "mode", "zone_name", "floor_index"]].to_string(index=False))

    # False-positive rate in background: fraction of background RUNS whose
    # topmost-floor zone would have been flagged if this were a real predictor
    # (background never fails, so this checks how common "has a top-floor zone"
    # is in general -- i.e. whether the statistic is trivially true for everyone).
    if not bg_df.empty:
        bg_runs_with_topfloor = bg_df[bg_df["is_top_floor_zone"] == True].groupby(["cell", "stem", "mode"]).ngroups
        bg_total_runs = bg_df.groupby(["cell", "stem", "mode"]).ngroups
        print(f"Background runs that HAVE an identifiable top-floor zone at all: {bg_runs_with_topfloor} / {bg_total_runs}")

    # --- 5. Candidate statistic B: volume_consistency_ratio far from 1.0 ---
    print("\n--- Candidate statistic B: reported Volume inconsistent with Floor Area x Ceiling Height ---")
    threshold_low, threshold_high = 0.5, 2.0
    target_df["volume_anomalous"] = (
        (target_df["volume_consistency_ratio"] < threshold_low) |
        (target_df["volume_consistency_ratio"] > threshold_high)
    )
    n_blowup_anomalous = int(target_df.loc[target_df["is_blowup_zone"], "volume_anomalous"].fillna(False).sum())
    print(f"Blow-up zones with anomalous volume/floor_area/height consistency (outside [{threshold_low},{threshold_high}]): "
          f"{n_blowup_anomalous} / {n_blowup_found}")

    if not bg_df.empty:
        bg_df["volume_anomalous"] = (
            (bg_df["volume_consistency_ratio"] < threshold_low) |
            (bg_df["volume_consistency_ratio"] > threshold_high)
        )
        n_bg_zone_anomalous = int(bg_df["volume_anomalous"].fillna(False).sum())
        n_bg_zones_total = len(bg_df)
        print(f"Background zones with the same anomaly: {n_bg_zone_anomalous} / {n_bg_zones_total}")

    # Per-run outcome separation summary for statistic B
    run_level = target_df.groupby(["cell", "stem", "mode"]).agg(
        has_fatal=("has_fatal", "first"),
        any_zone_volume_anomalous=("volume_anomalous", "any"),
    ).reset_index()
    print("\nPer-run: does ANY zone in the run show the volume anomaly, vs. did the run fail?")
    print(pd.crosstab(run_level["has_fatal"], run_level["any_zone_volume_anomalous"]))

    if not bg_df.empty:
        bg_run_level = bg_df.groupby(["cell", "stem", "mode"]).agg(
            any_zone_volume_anomalous=("volume_anomalous", "any"),
        ).reset_index()
        n_bg_runs_anomalous = int(bg_run_level["any_zone_volume_anomalous"].sum())
        print(f"Background (all-success) runs with >=1 volume-anomalous zone: {n_bg_runs_anomalous} / {len(bg_run_level)}")


if __name__ == "__main__":
    main()
