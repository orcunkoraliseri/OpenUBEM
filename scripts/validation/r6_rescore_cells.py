"""R6 re-scoring engine: region-correct CBECS gates + archetype-aware plausibility + GWP recompute.

R6-1: each city scored against its correct CBECS census division reference.
R6-3: archetype-aware plausibility band derived from PBA p1/p99 in the region reference.
T07b (R6-2/B2): linear-rescale GWP recompute using eGRID subregion factors.

Reporting-only: no resimulation, no core math changes (V-R5-5 / M-R2-4).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

from openubem import config
from openubem.results import compute_validation_gates

# ── Paths ────────────────────────────────────────────────────────────────────

CASES_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases"
REPORTS_DIR = REPO / "inputs" / "reports"
SUMMARY_CSV = REPO / "docs" / "validations" / "overAll" / "results" / "r6_rescore_summary.csv"
PBA_MAP_PATH = REPO / "openubem" / "data" / "cbecs_pba_map.json"
EGRID_STATE_PATH = REPO / "openubem" / "data" / "carbon" / "egrid_2022.json"
EGRID_SUBREGION_PATH = REPO / "openubem" / "data" / "carbon" / "egrid_2022_subregions.json"

# ── Region mapping (§4.1 canonical) ─────────────────────────────────────────

CELL_REGION: dict[str, str] = {
    "nyc_centre": "middle_atlantic",
    "nyc_urban": "middle_atlantic",
    "nyc_suburban": "middle_atlantic",
    "nyc_rural": "middle_atlantic",
    "la_centre": "pacific",
    "la_urban": "pacific",
    "la_suburban": "pacific",
    "la_rural": "pacific",
    "austin_centre": "west_south_central",
    "austin_urban": "west_south_central",
    "austin_suburban": "west_south_central",
    "austin_rural": "west_south_central",
}

# Northeast reference (R5 baseline) for "before" comparison
NE_REF_PATH = REPORTS_DIR / "cbecs_2018_new_england_eui.csv"

SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}

# T07b — city→state and city→subregion for GWP recompute (§4.3 B2)
CITY_STATE = {
    "nyc": "NY",
    "la": "CA",
    "austin": "TX",
}
CITY_SUBREGION = {
    "nyc": "NYCW",
    "la": "CAMX",
    "austin": "ERCT",
}

def _cell_city(cell: str) -> str:
    """Return city prefix from cell name (nyc, la, austin)."""
    for prefix in ("nyc", "la", "austin"):
        if cell.startswith(prefix):
            return prefix
    raise ValueError(f"Unknown cell city: {cell}")

# ── T07b: eGRID factor loaders ───────────────────────────────────────────────

def _load_egrid_factors() -> tuple[dict[str, float], dict[str, float]]:
    """Return (state_factors, subregion_factors) as {key: factor_kgco2_kwh}."""
    with open(EGRID_STATE_PATH, encoding="utf-8") as fh:
        state_data = json.load(fh)
    with open(EGRID_SUBREGION_PATH, encoding="utf-8") as fh:
        sr_data = json.load(fh)
    state_factors = {k: v["factor_kgco2_kwh"] for k, v in state_data.items()}
    sr_factors = {k: v["factor_kgco2_kwh"] for k, v in sr_data.items()}
    return state_factors, sr_factors


# ── T07b: GWP recompute (§4.3 B2 formula, linear rescale) ────────────────────

def compute_gwp_subregion(
    df: pd.DataFrame,
    state_factor: float,
    subregion_factor: float,
) -> tuple[float, float, float]:
    """Recompute GWP with subregion factor; return (gwp_r5_state, gwp_r6_subregion, delta_pct).

    Formula (§4.3):
      gwp_elec_old_per_m2 = gwp_cooling + gwp_lighting + gwp_equipment
      ratio                = f_subregion / f_state
      gwp_total_new_per_m2 = gwp_heating + gwp_elec_old_per_m2 * ratio
      gwp_total_new_abs    = sum of gwp_total_new_per_m2 * floor_area_m2

    floor_area_m2 uses derive_num_floors (levels fallback to height_m/3.5 fallback to 1).
    Heating GWP (natural gas) is unchanged.
    """
    from openubem.geometry.footprint import derive_num_floors

    df = df.copy()
    df["_num_floors"] = df.apply(derive_num_floors, axis=1)
    df["_floor_area"] = df["footprint_area_m2"] * df["_num_floors"]

    # R5 state-level total GWP (using gwp_total_kgco2_m2 already in CSV)
    gwp_r5_abs = float((df["gwp_total_kgco2_m2"] * df["_floor_area"]).sum())

    # R6 subregion rescale: only electricity components
    ratio = subregion_factor / state_factor
    df["_gwp_elec_old"] = (
        df["gwp_cooling_kgco2_m2"] + df["gwp_lighting_kgco2_m2"] + df["gwp_equipment_kgco2_m2"]
    )
    df["_gwp_total_new"] = df["gwp_heating_kgco2_m2"] + df["_gwp_elec_old"] * ratio
    gwp_r6_abs = float((df["_gwp_total_new"] * df["_floor_area"]).sum())

    delta_pct = (gwp_r6_abs - gwp_r5_abs) / gwp_r5_abs * 100.0 if gwp_r5_abs != 0 else 0.0
    return gwp_r5_abs, gwp_r6_abs, delta_pct


# ── PBA map ──────────────────────────────────────────────────────────────────

def _load_pba_map() -> dict[str, object]:
    with open(PBA_MAP_PATH, encoding="utf-8") as fh:
        return json.load(fh)["pba_map"]


# ── Weighted helpers (mirror openubem/results/__init__.py) ───────────────────

def _weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    sv = values[order]
    sw = weights[order]
    cdf = np.cumsum(sw) / sw.sum()
    return float(np.interp(q, cdf, sv))


# ── T04: derive archetype-aware plausibility bands ───────────────────────────

def derive_archetype_bands(
    region_ref_df: pd.DataFrame,
    pba_map: dict[str, object],
) -> dict[str, tuple[float, float]]:
    """Return {archetype: (low, high)} from weighted p1/p99 per PBA in the region reference.

    Falls back to generic [25,1000] when: null PBA, OpenUBEMUnknown, or <10 reference rows.
    Only archetypes that cleared the threshold are returned; caller uses generic for the rest.
    """
    lb_generic, ub_generic = config.EUI_PLAUSIBILITY_BOUNDS
    bands: dict[str, tuple[float, float]] = {}

    pba_groups: dict[int, pd.DataFrame] = {}
    for pba_code, grp in region_ref_df.groupby("pba_code"):
        pba_groups[int(pba_code)] = grp

    for archetype, pba in pba_map.items():
        if pba is None or pba == "distribution_only":
            # null-PBA archetypes and OpenUBEMUnknown → generic fallback, not stored
            continue
        pba_int = int(pba)
        if pba_int not in pba_groups:
            continue
        grp = pba_groups[pba_int]
        if len(grp) < 10:
            continue
        eui_vals = grp["eui_kwh_m2"].values.astype(float)
        wts = grp["finalwt"].values.astype(float)
        low = _weighted_quantile(eui_vals, wts, 0.01)
        high = _weighted_quantile(eui_vals, wts, 0.99)
        bands[archetype] = (low, high)

    return bands


# ── T05: cell loader ─────────────────────────────────────────────────────────

def load_cell_gdf(cell: str) -> gpd.GeoDataFrame:
    """Load a cell's 05_results.csv; alias total_eui → eui_kwh_m2; filter to successes."""
    csv_path = CASES_DIR / cell / "05_results.csv"
    df = pd.read_csv(csv_path)
    df = df[df["simulation_status"].isin(SUCCESS_STATUSES)].copy()
    df = df.rename(columns={"total_eui_kwh_m2": "eui_kwh_m2"})

    rows = []
    for _, row in df.iterrows():
        rows.append({
            "osm_id": str(row["osm_id"]),
            "archetype_id": row.get("archetype_id", "OpenUBEMUnknown"),
            "eui_kwh_m2": row.get("eui_kwh_m2"),
            "simulation_status": row.get("simulation_status", "success"),
            "geometry": Point(
                row.get("centroid_lon", 0.0) or 0.0,
                row.get("centroid_lat", 0.0) or 0.0,
            ),
        })
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


def load_cell_df_full(cell: str) -> pd.DataFrame:
    """Load a cell's 05_results.csv filtered to successes; keeps all columns for GWP recompute."""
    csv_path = CASES_DIR / cell / "05_results.csv"
    df = pd.read_csv(csv_path)
    return df[df["simulation_status"].isin(SUCCESS_STATUSES)].copy()


def load_region_ref(region_slug: str) -> pd.DataFrame:
    path = REPORTS_DIR / f"cbecs_2018_{region_slug}_eui.csv"
    return pd.read_csv(path)


# ── T06: dual plausibility compute ───────────────────────────────────────────

def _compute_plausibility(
    gdf: gpd.GeoDataFrame,
    pba_map: dict[str, object],
    archetype_bands: dict[str, tuple[float, float]],
) -> tuple[float, float]:
    """Return (generic_pct, archetype_pct) over success rows with non-null EUI.

    Generic plausibility: ALL parsed buildings with non-null EUI — no archetype
    exclusion — reproducing the R5 F12 gate exactly (§4.4 / bug-fix 2026-06-15).
    Archetype-aware plausibility: same denominator (full valid set); null-PBA
    archetypes fall back to the generic band since they have no PBA-derived band.
    CBECS distribution exclusions (null-PBA) are applied only in compute_validation_gates,
    not here (§2 rule 3 of the correction task).
    """
    lb_g, ub_g = config.EUI_PLAUSIBILITY_BOUNDS

    # All rows with non-null EUI — no archetype exclusion (reproduces R5 F12 gate)
    valid = gdf[gdf["eui_kwh_m2"].notna()].copy()

    if len(valid) == 0:
        return 0.0, 0.0

    eui = valid["eui_kwh_m2"]

    # Generic band: denominator = all valid_eui rows (no exclusion)
    in_generic = ((eui >= lb_g) & (eui <= ub_g)).sum()
    generic_pct = float(in_generic) / len(valid) * 100.0

    # Archetype-aware band: same denominator; null-PBA archetypes fall back to generic band
    # (they have no archetype_bands entry). Guarantees archetype_pct >= generic_pct.
    in_arch = 0
    for _, row_r in valid.iterrows():
        a = row_r["archetype_id"]
        v = row_r["eui_kwh_m2"]
        in_g = lb_g <= v <= ub_g
        if in_g:
            in_arch += 1
        elif a in archetype_bands:
            lo, hi = archetype_bands[a]
            if lo <= v <= hi:
                in_arch += 1
    archetype_pct = float(in_arch) / len(valid) * 100.0

    return generic_pct, archetype_pct


def _outlier_detail(
    gdf: gpd.GeoDataFrame,
    pba_map: dict[str, object],
    archetype_bands: dict[str, tuple[float, float]],
) -> list[str]:
    """Return text lines describing generic-band outliers and their archetype bands."""
    lb_g, ub_g = config.EUI_PLAUSIBILITY_BOUNDS

    # Same denominator as generic plausibility: all rows with non-null EUI
    valid = gdf[gdf["eui_kwh_m2"].notna()]
    outliers = valid[~((valid["eui_kwh_m2"] >= lb_g) & (valid["eui_kwh_m2"] <= ub_g))]

    lines: list[str] = []
    if len(outliers) == 0:
        lines.append("  (no generic-band outliers)")
        return lines

    for _, row_r in outliers.iterrows():
        a = row_r["archetype_id"]
        v = row_r["eui_kwh_m2"]
        if a in archetype_bands:
            lo, hi = archetype_bands[a]
            inside = "IN archetype band" if lo <= v <= hi else "OUTSIDE archetype band"
            lines.append(f"  osm_id={row_r['osm_id']} arch={a} eui={v:.1f}  band=[{lo:.1f},{hi:.1f}]  {inside}")
        else:
            lines.append(f"  osm_id={row_r['osm_id']} arch={a} eui={v:.1f}  → generic fallback [25,1000]")
    return lines


# ── T06: per-cell report + summary row ───────────────────────────────────────

def rescore_cell(
    cell: str,
    ne_ref: pd.DataFrame,
    pba_map: dict[str, object],
    state_factors: dict[str, float] | None = None,
    subregion_factors: dict[str, float] | None = None,
) -> dict:
    """Run R6 rescoring for one cell. Returns a dict for the summary CSV row.

    T07b: if state_factors and subregion_factors provided, also computes subregion GWP recompute.
    """
    region = CELL_REGION[cell]
    region_ref = load_region_ref(region)
    gdf = load_cell_gdf(cell)

    # CBECS gates: Northeast (R5 baseline "before")
    gates_ne = compute_validation_gates(gdf, reference_table=ne_ref)

    # CBECS gates: region-correct (R6 "after")
    gates_r6 = compute_validation_gates(gdf, reference_table=region_ref)

    # Archetype-aware plausibility bands (T04)
    archetype_bands = derive_archetype_bands(region_ref, pba_map)

    # Dual plausibility
    generic_pct, archetype_pct = _compute_plausibility(gdf, pba_map, archetype_bands)

    # Outlier detail for food-service cells
    outlier_lines = _outlier_detail(gdf, pba_map, archetype_bands)

    # T07b: GWP subregion recompute (if factors provided)
    gwp_r5_abs = None
    gwp_r6_abs = None
    gwp_delta_pct = None
    f_state = None
    f_subregion = None
    if state_factors is not None and subregion_factors is not None:
        city = _cell_city(cell)
        state_key = CITY_STATE[city]
        sr_key = CITY_SUBREGION[city]
        f_state = state_factors[state_key]
        f_subregion = subregion_factors[sr_key]
        df_full = load_cell_df_full(cell)
        gwp_r5_abs, gwp_r6_abs, gwp_delta_pct = compute_gwp_subregion(df_full, f_state, f_subregion)

    # Build per-cell report (T06)
    n_success = len(gdf)
    report_lines: list[str] = []
    report_lines.append("=" * 76)
    report_lines.append(f"R6 GATES REPORT — {cell}")
    report_lines.append(f"  Region reference: {region}  (R5 used: northeast)")
    report_lines.append(f"  n buildings (success): {n_success}")
    report_lines.append("=" * 76)

    report_lines.append("")
    report_lines.append("=== CBECS GATES: Northeast (R5 baseline) vs Region-correct (R6) ===")
    report_lines.append(
        f"{'Metric':<14} {'Threshold':>12} {'R5 NE':>12} {'R5 P/F':>8} "
        f"{'R6 Region':>12} {'R6 P/F':>8} {'Delta':>10}"
    )
    report_lines.append("-" * 78)

    cv_ne = gates_ne["cbecs_cv_rmse"]
    cv_r6 = gates_r6["cbecs_cv_rmse"]
    report_lines.append(
        f"{'CV(RMSE)%':<14} {'< 30.0%':>12} {cv_ne:>12.3f} "
        f"{'PASS' if gates_ne['cbecs_cv_rmse_pass'] else 'FAIL':>8} "
        f"{cv_r6:>12.3f} {'PASS' if gates_r6['cbecs_cv_rmse_pass'] else 'FAIL':>8} "
        f"{cv_r6 - cv_ne:>+10.3f}"
    )

    nmbe_ne = gates_ne["cbecs_nmbe"]
    nmbe_r6 = gates_r6["cbecs_nmbe"]
    report_lines.append(
        f"{'NMBE%':<14} {'< |10|%':>12} {nmbe_ne:>12.3f} "
        f"{'PASS' if gates_ne['cbecs_nmbe_pass'] else 'FAIL':>8} "
        f"{nmbe_r6:>12.3f} {'PASS' if gates_r6['cbecs_nmbe_pass'] else 'FAIL':>8} "
        f"{nmbe_r6 - nmbe_ne:>+10.3f}"
    )

    r2_ne = gates_ne["cbecs_r2"]
    r2_r6 = gates_r6["cbecs_r2"]
    r2_ne_str = f"{r2_ne:.4f}" if r2_ne is not None else "N/A"
    r2_r6_str = f"{r2_r6:.4f}" if r2_r6 is not None else "N/A"
    r2_delta_str = f"{r2_r6 - r2_ne:+.4f}" if (r2_ne is not None and r2_r6 is not None) else "N/A"
    report_lines.append(
        f"{'R²':<14} {'> 0.6':>12} {r2_ne_str:>12} "
        f"{'PASS' if gates_ne['cbecs_r2_pass'] else 'FAIL':>8} "
        f"{r2_r6_str:>12} {'PASS' if gates_r6['cbecs_r2_pass'] else 'FAIL':>8} "
        f"{r2_delta_str:>10}"
    )

    ks_ne = gates_ne["cbecs_ks_d"]
    ks_r6 = gates_r6["cbecs_ks_d"]
    report_lines.append(
        f"{'KS_D':<14} {'< 0.10':>12} {ks_ne:>12.4f} "
        f"{'PASS' if gates_ne['cbecs_ks_d_pass'] else 'FAIL':>8} "
        f"{ks_r6:>12.4f} {'PASS' if gates_r6['cbecs_ks_d_pass'] else 'FAIL':>8} "
        f"{ks_r6 - ks_ne:>+10.4f}"
    )

    report_lines.append("")
    report_lines.append("  Note: CBECS gates are report-only (V-R5-5 / M-R2-4).")
    report_lines.append(f"  n_sim_buildings (R6, excl. null-PBA): {gates_r6['n_sim_buildings']}")
    report_lines.append(f"  n_excluded_all_gates: {gates_r6['n_excluded_all_gates']}")

    report_lines.append("")
    report_lines.append("=== EUI PLAUSIBILITY ===")
    report_lines.append(
        f"  Generic band [25,1000]:       {generic_pct:.2f}%  "
        f"{'PASS' if generic_pct >= 99.0 else 'FAIL'}"
    )
    report_lines.append(
        f"  Archetype-aware band (p1/p99): {archetype_pct:.2f}%  "
        f"{'PASS' if archetype_pct >= 99.0 else 'FAIL'}"
    )
    report_lines.append("")
    report_lines.append("  Generic-band outliers and their archetype bands:")
    report_lines.extend(outlier_lines)

    # T07b: GWP section in report
    if gwp_r5_abs is not None:
        city = _cell_city(cell)
        state_key = CITY_STATE[city]
        sr_key = CITY_SUBREGION[city]
        report_lines.append("")
        report_lines.append("=== GWP RECOMPUTE: State-level (R5) vs Subregion (R6-2/B2) ===")
        report_lines.append(f"  City: {city.upper()}  State: {state_key}  Subregion: {sr_key}")
        report_lines.append(f"  f_state    = {f_state:.6f} kg CO2e/kWh")
        report_lines.append(f"  f_subregion= {f_subregion:.6f} kg CO2e/kWh")
        report_lines.append(f"  ratio      = {f_subregion/f_state:.6f}")
        report_lines.append(f"  R5 state-level total GWP: {gwp_r5_abs:>18,.0f} kgCO2e")
        report_lines.append(f"  R6 subregion total GWP:   {gwp_r6_abs:>18,.0f} kgCO2e")
        report_lines.append(f"  Delta:                    {gwp_delta_pct:>+18.2f}%")
        report_lines.append("  Note: R5 artifact (05_results.csv) NOT modified; recompute is in-memory only.")

    report_lines.append("")
    report_lines.append("=" * 76)
    report_lines.append("END R6 REPORT")
    report_lines.append("=" * 76)

    report_text = "\n".join(report_lines)
    report_path = CASES_DIR / cell / "r6_gates_report.txt"
    report_path.write_text(report_text, encoding="utf-8")

    return {
        "cell": cell,
        "region": region,
        "n_success": n_success,
        "cv_rmse_ne": cv_ne,
        "cv_rmse_r6": cv_r6,
        "cv_rmse_delta": round(cv_r6 - cv_ne, 3),
        "cv_rmse_r6_pass": gates_r6["cbecs_cv_rmse_pass"],
        "nmbe_ne": nmbe_ne,
        "nmbe_r6": nmbe_r6,
        "nmbe_delta": round(nmbe_r6 - nmbe_ne, 3),
        "nmbe_r6_pass": gates_r6["cbecs_nmbe_pass"],
        "r2_ne": r2_ne,
        "r2_r6": r2_r6,
        "r2_delta": round(r2_r6 - r2_ne, 4) if (r2_ne is not None and r2_r6 is not None) else None,
        "r2_r6_pass": gates_r6["cbecs_r2_pass"],
        "ks_d_ne": ks_ne,
        "ks_d_r6": ks_r6,
        "ks_d_delta": round(ks_r6 - ks_ne, 4),
        "ks_d_r6_pass": gates_r6["cbecs_ks_d_pass"],
        "plaus_generic_pct": round(generic_pct, 2),
        "plaus_archetype_pct": round(archetype_pct, 2),
        "n_excluded_all_gates": gates_r6["n_excluded_all_gates"],
        # T07b GWP columns (None if factors not provided)
        "gwp_r5_state_kgco2e": round(gwp_r5_abs) if gwp_r5_abs is not None else None,
        "gwp_r6_subregion_kgco2e": round(gwp_r6_abs) if gwp_r6_abs is not None else None,
        "gwp_delta_pct": round(gwp_delta_pct, 2) if gwp_delta_pct is not None else None,
    }


# ── Main entrypoint ───────────────────────────────────────────────────────────

def main() -> None:
    pba_map = _load_pba_map()
    ne_ref = pd.read_csv(NE_REF_PATH)
    state_factors, subregion_factors = _load_egrid_factors()

    cells = list(CELL_REGION.keys())
    rows: list[dict] = []

    for cell in cells:
        print(f"[r6_rescore] Processing {cell} ...")
        row = rescore_cell(cell, ne_ref, pba_map, state_factors, subregion_factors)
        rows.append(row)
        print(f"  CV(RMSE) NE={row['cv_rmse_ne']:.3f} -> R6={row['cv_rmse_r6']:.3f}  "
              f"generic={row['plaus_generic_pct']:.2f}%  arch={row['plaus_archetype_pct']:.2f}%")
        if row.get("gwp_r5_state_kgco2e") is not None:
            print(f"  GWP_R5={row['gwp_r5_state_kgco2e']:,}  "
                  f"GWP_R6={row['gwp_r6_subregion_kgco2e']:,}  "
                  f"delta={row['gwp_delta_pct']:+.2f}%")

    summary_df = pd.DataFrame(rows)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(SUMMARY_CSV, index=False)
    print(f"\n[r6_rescore] Summary written to {SUMMARY_CSV}")
    print(f"[r6_rescore] Per-cell reports written under {CASES_DIR}/<cell>/r6_gates_report.txt")


if __name__ == "__main__":
    main()
