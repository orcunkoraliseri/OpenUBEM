"""V19 Phase-C re-score: loader + reconstruction + comparison tables.

Reads all 12 Phase-C 05_results.gpkg files from the two base dirs (§4.1),
applies service-load reconstruction, and emits per-building CSV + comparison tables.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openubem.results.service_loads import load_coefficients, reconstruct_frame

# §4.1: 9 cells in docs_VALIDATION tree, 3 in validations tree
_BASE_9 = ROOT / "docs" / "docs_VALIDATION" / "step1" / "overAll" / "results" / "phaseC"
_BASE_3 = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseC"

CELL_TO_BASE: dict[str, Path] = {
    "austin_centre":   _BASE_9,
    "austin_rural":    _BASE_9,
    "austin_suburban": _BASE_9,
    "la_rural":        _BASE_9,
    "la_suburban":     _BASE_9,
    "la_urban":        _BASE_9,
    "nyc_rural":       _BASE_9,
    "nyc_suburban":    _BASE_9,
    "nyc_urban":       _BASE_9,
    "austin_urban":    _BASE_3,
    "la_centre":       _BASE_3,
    "nyc_centre":      _BASE_3,
}

_OUT_DIR = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"

# §4.4 segment → archetype_id sets
SEGMENT_ARCHETYPES: dict[str, set[str]] = {
    "Office":      {"SmallOffice", "MediumOffice", "LargeOffice"},
    "Multifamily": {"MidriseApartment", "HighriseApartment"},
    "Warehouse":   {"Warehouse"},
}

# §4.3 measured medians and V17 old-model medians (kWh/m²·yr)
CITY_ANCHORS: dict[tuple[str, str], dict[str, float | None]] = {
    ("nyc",    "Office"):      {"measured": 183.9, "v17_old": 183.3},
    ("nyc",    "Multifamily"): {"measured": 226.2, "v17_old": 302.0},
    ("nyc",    "Overall"):     {"measured": 219.2, "v17_old": 246.9},
    ("la",     "Office"):      {"measured": 121.5, "v17_old": 208.9},
    ("la",     "Multifamily"): {"measured": 115.8, "v17_old": 153.3},
    ("la",     "Warehouse"):   {"measured":  33.9, "v17_old":  64.1},
    ("la",     "Overall"):     {"measured": 113.6, "v17_old": 158.6},
    ("austin", "Office"):      {"measured": 162.3, "v17_old": 187.6},
    ("austin", "Overall"):     {"measured": 162.0, "v17_old": 199.8},
}

# §4.3 per-archetype national anchors
ARCHETYPE_ANCHORS: dict[str, dict[str, float]] = {
    "MediumOffice":           {"espm": 166.9, "v17_old": 160.3},
    "SmallOffice":            {"espm": 166.9, "v17_old": 190.3},
    "LargeOffice":            {"espm": 166.9, "v17_old": 229.8},
    "MidriseApartment":       {"espm": 187.9, "v17_old": 228.8},
    "RetailStandalone":       {"espm": 162.1, "v17_old": 286.7},
    "Warehouse":              {"espm":  71.6, "v17_old":  64.1},
    "SuperMarket":            {"espm": 618.3, "v17_old": 631.5},
    "FullServiceRestaurant":  {"espm": 1027.2, "v17_old": 2158.5},
    "QuickServiceRestaurant": {"espm": 1270.3, "v17_old": 3307.9},
    "PrimarySchool":          {"espm": 153.0, "v17_old": 289.4},
}


def load_all_cells() -> pd.DataFrame:
    """Read all 12 Phase-C 05_results.gpkg; assert exactly 12 cells found."""
    missing = []
    frames = []
    for cell, base in CELL_TO_BASE.items():
        gpkg = base / cell / "05_results.gpkg"
        if not gpkg.exists():
            missing.append(cell)
            continue
        gdf = gpd.read_file(str(gpkg))
        df = pd.DataFrame(gdf.drop(columns=gdf.geometry.name, errors="ignore"))
        city, density = cell.split("_", 1)
        df["cell"] = cell
        df["city"] = city
        df["density"] = density
        frames.append(df)

    if missing:
        raise FileNotFoundError(f"Missing Phase-C gpkg for cells: {missing}")

    combined = pd.concat(frames, ignore_index=True)
    found = combined["cell"].nunique()
    if found != 12:
        raise AssertionError(f"Expected 12 distinct cells, found {found}")
    return combined


def build_city_table(reconstructed: pd.DataFrame) -> pd.DataFrame:
    """T03: per-city × segment comparison table (success rows only)."""
    success = reconstructed[
        reconstructed["simulation_status"].str.startswith("success", na=False)
    ].copy()

    rows = []
    for city in ("nyc", "la", "austin"):
        city_df = success[success["city"] == city]

        # named segments
        for segment, archetype_set in SEGMENT_ARCHETYPES.items():
            seg_df = city_df[city_df["archetype_id"].isin(archetype_set)]
            if seg_df.empty:
                continue
            anchors = CITY_ANCHORS.get((city, segment))
            if anchors is None:
                continue  # no measured anchor → skip (e.g. nyc Warehouse)
            recon_med = seg_df["total_eui_reconstructed_kwh_m2"].median()
            eu4_med   = seg_df["total_eui_kwh_m2"].median()
            measured  = anchors["measured"]
            v17_old   = anchors["v17_old"]
            rows.append({
                "city":               city,
                "segment":            segment,
                "n":                  len(seg_df),
                "model_recon_median": round(recon_med, 2),
                "model_4eu_median":   round(eu4_med, 2),
                "p25_recon":          round(seg_df["total_eui_reconstructed_kwh_m2"].quantile(0.25), 2),
                "p75_recon":          round(seg_df["total_eui_reconstructed_kwh_m2"].quantile(0.75), 2),
                "measured":           measured,
                "delta_vs_measured_pct": round((recon_med - measured) / measured * 100, 1),
                "v17_old_model":      v17_old,
                "delta_vs_v17old_pct": round((recon_med - v17_old) / v17_old * 100, 1),
            })

        # Overall: exclude OpenUBEMUnknown
        overall_df = city_df[city_df["archetype_id"] != "OpenUBEMUnknown"]
        unknown_n  = (city_df["archetype_id"] == "OpenUBEMUnknown").sum()
        anchors    = CITY_ANCHORS.get((city, "Overall"))
        if overall_df.empty or anchors is None:
            continue
        recon_med = overall_df["total_eui_reconstructed_kwh_m2"].median()
        eu4_med   = overall_df["total_eui_kwh_m2"].median()
        measured  = anchors["measured"]
        v17_old   = anchors["v17_old"]
        rows.append({
            "city":               city,
            "segment":            f"Overall (excl. OpenUBEMUnknown n={unknown_n})",
            "n":                  len(overall_df),
            "model_recon_median": round(recon_med, 2),
            "model_4eu_median":   round(eu4_med, 2),
            "p25_recon":          round(overall_df["total_eui_reconstructed_kwh_m2"].quantile(0.25), 2),
            "p75_recon":          round(overall_df["total_eui_reconstructed_kwh_m2"].quantile(0.75), 2),
            "measured":           measured,
            "delta_vs_measured_pct": round((recon_med - measured) / measured * 100, 1),
            "v17_old_model":      v17_old,
            "delta_vs_v17old_pct": round((recon_med - v17_old) / v17_old * 100, 1),
        })

    return pd.DataFrame(rows)


def build_archetype_table(reconstructed: pd.DataFrame) -> pd.DataFrame:
    """T04: per-archetype national table (all 12 cells, success rows)."""
    success = reconstructed[
        reconstructed["simulation_status"].str.startswith("success", na=False)
    ]

    rows = []
    for arch, anchors in ARCHETYPE_ANCHORS.items():
        arch_df = success[success["archetype_id"] == arch]
        n = len(arch_df)
        if n == 0:
            recon_med = float("nan")
            delta_espm = float("nan")
            delta_v17 = float("nan")
        else:
            recon_med = arch_df["total_eui_reconstructed_kwh_m2"].median()
            delta_espm = round((recon_med - anchors["espm"]) / anchors["espm"] * 100, 1)
            delta_v17  = round((recon_med - anchors["v17_old"]) / anchors["v17_old"] * 100, 1)
            recon_med  = round(recon_med, 2)
        rows.append({
            "archetype_id":          arch,
            "n":                     n,
            "model_recon_median":    recon_med,
            "espm_median":           anchors["espm"],
            "delta_vs_espm_pct":     delta_espm,
            "v17_old_model":         anchors["v17_old"],
            "delta_vs_v17old_pct":   delta_v17,
            "low_confidence":        n < 12,
        })

    return pd.DataFrame(rows)


def _df_to_md_table(df: pd.DataFrame) -> str:
    """Convert DataFrame to markdown table string."""
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep    = "| " + " | ".join("---" for _ in df.columns) + " |"
    body   = "\n".join(
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in df.itertuples(index=False)
    )
    return "\n".join([header, sep, body])


def write_artifacts(city_tbl: pd.DataFrame, arch_tbl: pd.DataFrame) -> None:
    """T05: write v19_comparison_tables.md and v19_comparison.csv."""
    md_path  = _OUT_DIR / "v19_comparison_tables.md"
    csv_path = _OUT_DIR / "v19_comparison.csv"

    md_lines = [
        "# V19 Phase-C Comparison Tables",
        "",
        "## City × Segment (success rows; reconstructed total EUI vs measured and V17 old model)",
        "",
        _df_to_md_table(city_tbl),
        "",
        "## Per-Archetype National (all 12 cells pooled, success rows)",
        "",
        _df_to_md_table(arch_tbl),
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[T05] Written: {md_path}")

    # machine-readable union: tag which table each row came from
    city_out = city_tbl.copy()
    city_out.insert(0, "table", "city_segment")
    arch_out = arch_tbl.copy()
    arch_out.insert(0, "table", "archetype_national")
    union = pd.concat([city_out, arch_out], ignore_index=True)
    union.to_csv(csv_path, index=False)
    print(f"[T05] Written: {csv_path}")


def print_self_check(
    reconstructed: pd.DataFrame,
    city_tbl: pd.DataFrame,
    arch_tbl: pd.DataFrame,
) -> None:
    """T06: self-check stdout report."""
    print("\n=== T06 Self-check ===")

    # (a) 12 cells with row counts
    print("\n(a) 12 cells loaded:")
    for cell, grp in reconstructed.groupby("cell"):
        print(f"  {cell}: {len(grp)} rows")
    print(f"  TOTAL: {len(reconstructed)} rows")

    # (b) LA Office and LA Overall
    def _city_seg(tbl: pd.DataFrame, city: str, seg_prefix: str) -> pd.Series | None:
        mask = (tbl["city"] == city) & tbl["segment"].str.startswith(seg_prefix)
        if mask.any():
            return tbl[mask].iloc[0]
        return None

    print("\n(b) LA metrics:")
    for seg in ("Office", "Overall"):
        row = _city_seg(city_tbl, "la", seg)
        if row is not None:
            print(
                f"  LA {seg}: recon_median={row['model_recon_median']:.2f} kWh/m2"
                f"  delta_vs_measured={row['delta_vs_measured_pct']:+.1f}%"
                f"  delta_vs_v17old={row['delta_vs_v17old_pct']:+.1f}%"
            )

    # (c) NYC Office anchor
    print("\n(c) NYC Office anchor:")
    row = _city_seg(city_tbl, "nyc", "Office")
    if row is not None:
        print(
            f"  NYC Office: recon_median={row['model_recon_median']:.2f} kWh/m2"
            f"  delta_vs_measured={row['delta_vs_measured_pct']:+.1f}%"
        )

    # (d) total passthrough count
    passthrough = (reconstructed["reconstruction_applied"] == False).sum()
    print(f"\n(d) Total passthrough count (reconstruction_applied==False): {passthrough}")


def main() -> None:
    print("=== V19 Phase-C Re-score ===")

    # T01: load all 12 cells
    combined = load_all_cells()
    print("\n[T01] Cell row counts:")
    for cell, grp in combined.groupby("cell"):
        print(f"  {cell}: {len(grp)} rows")
    print(f"  TOTAL: {len(combined)} rows across {combined['cell'].nunique()} cells")

    # T02: apply reconstruction
    coeffs = load_coefficients()
    reconstructed = reconstruct_frame(combined, coeffs)

    applied = (reconstructed["reconstruction_applied"] == True).sum()
    success_mask = reconstructed["simulation_status"].str.startswith("success", na=False)
    passthrough_success = ((reconstructed["reconstruction_applied"] == False) & success_mask).sum()
    unmapped_ids = set(
        reconstructed.loc[
            (reconstructed["reconstruction_applied"] == False) & success_mask,
            "archetype_id"
        ].dropna().unique()
    )

    print(f"\n[T02] Reconstruction applied (True): {applied}")
    print(f"[T02] Passthrough among success rows: {passthrough_success}")
    print(f"[T02] Distinct unmapped archetype_ids: {sorted(unmapped_ids)}")

    out_csv = _OUT_DIR / "v19_phaseC_reconstructed.csv"
    reconstructed.to_csv(out_csv, index=False)
    print(f"\n[T02] Written: {out_csv}")

    # T03: city-level comparison table
    city_tbl = build_city_table(reconstructed)
    print(f"\n[T03] City comparison table ({len(city_tbl)} rows):")
    print(city_tbl.to_string(index=False))

    # T04: per-archetype national table
    arch_tbl = build_archetype_table(reconstructed)
    print(f"\n[T04] Per-archetype national table ({len(arch_tbl)} rows):")
    print(arch_tbl.to_string(index=False))

    # T05: write artifacts
    write_artifacts(city_tbl, arch_tbl)

    # T06: self-check
    print_self_check(reconstructed, city_tbl, arch_tbl)


if __name__ == "__main__":
    main()
