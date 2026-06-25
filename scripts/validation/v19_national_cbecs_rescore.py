"""V19 national CBECS re-score under COP energy basis (no resim).

Post-processes existing Phase-C 12-cell results by applying basis transforms
and re-scoring against per-region CBECS 2018 references.  No openubem/ changes.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.v19_rescore import load_all_cells, _df_to_md_table
from scripts.validation.v19_basis_diagnostic import apply_basis_to_frame, _GRID, _PARAM_KEYS
from openubem.results import compute_validation_gates
from openubem.results.service_loads import load_coefficients, reconstruct_frame

# Column produced by reconstruct_frame (service_loads.py:103)
_RECON_TOTAL_COL = "total_eui_reconstructed_kwh_m2"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OUT_DIR = ROOT / "docs" / "docs_ACTIVE" / "phaseC_combinedResim" / "v19_validation"
_REPORTS_DIR = ROOT / "inputs" / "reports"

# City → census division mapping (G6)
_CITY_REGION: dict[str, str] = {
    "nyc":    "middle_atlantic",
    "la":     "pacific",
    "austin": "west_south_central",
}

_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}

_REGIONS = ["middle_atlantic", "pacific", "west_south_central"]
_REGION_KEYS = ["nmbe", "nmbe_pass", "cv_rmse", "cv_rmse_pass", "ks_d", "ks_d_pass", "n"]


# ---------------------------------------------------------------------------
# T01 — Load base data and regional references; define score_region
# ---------------------------------------------------------------------------

def load_base() -> pd.DataFrame:
    """Load 12-cell frame, filter to success rows only."""
    raw = load_all_cells()
    return raw[raw["simulation_status"].isin(_SUCCESS_STATUSES)].copy()


def load_region_refs() -> dict[str, pd.DataFrame]:
    """Load three regional CBECS reference CSVs (G6)."""
    return {
        region: pd.read_csv(_REPORTS_DIR / f"cbecs_2018_{region}_eui.csv")
        for region in _CITY_REGION.values()
    }


def score_region(df_city: pd.DataFrame, region_ref: pd.DataFrame) -> dict[str, Any]:
    """Alias total→eui, call compute_validation_gates; return gate dict."""
    scored = df_city.copy()
    scored["eui_kwh_m2"] = scored["total_eui_kwh_m2"]  # G1/§3 alias
    gates = compute_validation_gates(scored, reference_table=region_ref)
    return gates


# ---------------------------------------------------------------------------
# T02 — Single-combo national scorer
# ---------------------------------------------------------------------------

def score_combo_national(
    base_df: pd.DataFrame,
    region_refs: dict[str, pd.DataFrame],
    params: dict[str, float],
) -> dict[str, Any]:
    """Transform base_df, score each city against its region ref; return flat dict."""
    transformed = apply_basis_to_frame(
        base_df,
        cooling_cop=params["cooling_cop"],
        heating_factor=params["heating_factor"],
        lighting_scale=params["lighting_scale"],
        equipment_scale=params["equipment_scale"],
    )

    result: dict[str, Any] = dict(params)
    abs_nmbes: list[float] = []
    nmbe_passes: list[bool] = []
    cvrmse_passes: list[bool] = []

    for city, region in _CITY_REGION.items():
        city_df = transformed[transformed["city"] == city]
        gates = score_region(city_df, region_refs[region])

        nmbe = gates["cbecs_nmbe"]
        cv_rmse = gates["cbecs_cv_rmse"]
        ks_d = gates["cbecs_ks_d"]
        n = gates["n_sim_buildings"]

        result[f"{region}_nmbe"]        = nmbe
        result[f"{region}_nmbe_pass"]   = gates["cbecs_nmbe_pass"]
        result[f"{region}_cv_rmse"]     = cv_rmse
        result[f"{region}_cv_rmse_pass"] = gates["cbecs_cv_rmse_pass"]
        result[f"{region}_ks_d"]        = ks_d
        result[f"{region}_ks_d_pass"]   = gates["cbecs_ks_d_pass"]
        result[f"{region}_n"]           = n

        abs_nmbes.append(abs(nmbe))
        nmbe_passes.append(gates["cbecs_nmbe_pass"])
        cvrmse_passes.append(gates["cbecs_cv_rmse_pass"])

    result["max_abs_nmbe"]         = round(max(abs_nmbes), 4)
    result["n_regions_nmbe_pass"]  = sum(nmbe_passes)
    result["n_regions_cvrmse_pass"] = sum(cvrmse_passes)
    return result


# ---------------------------------------------------------------------------
# T03 — Run the full 120-combo grid
# ---------------------------------------------------------------------------

def run_grid(
    base_df: pd.DataFrame,
    region_refs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Iterate _GRID (120 combos), score nationally, return DataFrame sorted by max_abs_nmbe."""
    rows = []
    for cop, hf, ls, es in itertools.product(
        _GRID["cooling_cop"],
        _GRID["heating_factor"],
        _GRID["lighting_scale"],
        _GRID["equipment_scale"],
    ):
        params = {
            "cooling_cop":    cop,
            "heating_factor": hf,
            "lighting_scale": ls,
            "equipment_scale": es,
        }
        rows.append(score_combo_national(base_df, region_refs, params))

    assert len(rows) == 120, f"Grid length {len(rows)} != 120"
    df = pd.DataFrame(rows).sort_values("max_abs_nmbe").reset_index(drop=True)
    return df


def _identity_present(grid_df: pd.DataFrame) -> bool:
    mask = (
        (grid_df["cooling_cop"]    == 1.0)
        & (grid_df["heating_factor"]  == 1.0)
        & (grid_df["lighting_scale"]  == 1.0)
        & (grid_df["equipment_scale"] == 1.0)
    )
    return bool(mask.any())


# ---------------------------------------------------------------------------
# T04 — Cross-reference: national behaviour of city-anchor-winning combos
# ---------------------------------------------------------------------------

_COMBOS_TO_CHECK = [
    {"cooling_cop": 1.0,  "heating_factor": 1.0,  "lighting_scale": 1.0, "equipment_scale": 1.0,  "label": "identity"},
    {"cooling_cop": 3.5,  "heating_factor": 1.0,  "lighting_scale": 1.0, "equipment_scale": 1.0,  "label": "city_winner"},
    {"cooling_cop": 2.5,  "heating_factor": 1.19, "lighting_scale": 0.8, "equipment_scale": 0.7,  "label": "grid_min"},
]


def build_cross_reference(grid_df: pd.DataFrame) -> pd.DataFrame:
    """Extract the three combos from the grid; compute generalization-signal deltas."""
    rows = []
    identity_nmbes: dict[str, float] = {}

    for combo in _COMBOS_TO_CHECK:
        cop = combo["cooling_cop"]
        hf  = combo["heating_factor"]
        ls  = combo["lighting_scale"]
        es  = combo["equipment_scale"]
        label = combo["label"]

        mask = (
            (grid_df["cooling_cop"]    == cop)
            & (grid_df["heating_factor"]  == hf)
            & (grid_df["lighting_scale"]  == ls)
            & (grid_df["equipment_scale"] == es)
        )
        assert mask.any(), (
            f"Combo {label} ({cop},{hf},{ls},{es}) not found in grid"
        )
        row = grid_df[mask].iloc[0]

        if label == "identity":
            for region in _REGIONS:
                identity_nmbes[region] = float(row[f"{region}_nmbe"])

        entry: dict[str, Any] = {
            "label": label,
            "cooling_cop": cop,
            "heating_factor": hf,
            "lighting_scale": ls,
            "equipment_scale": es,
        }
        for region in _REGIONS:
            entry[f"{region}_nmbe"]         = row[f"{region}_nmbe"]
            entry[f"{region}_nmbe_pass"]    = row[f"{region}_nmbe_pass"]
            entry[f"{region}_cv_rmse"]      = row[f"{region}_cv_rmse"]
            entry[f"{region}_cv_rmse_pass"] = row[f"{region}_cv_rmse_pass"]
            entry[f"{region}_ks_d"]         = row[f"{region}_ks_d"]
            entry[f"{region}_ks_d_pass"]    = row[f"{region}_ks_d_pass"]

        entry["n_regions_nmbe_pass"]  = int(row["n_regions_nmbe_pass"])
        entry["n_regions_cvrmse_pass"] = int(row["n_regions_cvrmse_pass"])
        rows.append(entry)

    # Compute generalization-signal: nmbe_at_combo - nmbe_at_identity
    identity_row = {r["label"]: r for r in rows}["identity"]
    for entry in rows:
        for region in _REGIONS:
            entry[f"{region}_gen_signal"] = round(
                float(entry[f"{region}_nmbe"]) - float(identity_row[f"{region}_nmbe"]), 4
            )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# T05 — Findings memo
# ---------------------------------------------------------------------------

def _print_self_check(
    identity_direct: dict[str, float],
    grid_identity: dict[str, float],
    cross_ref: pd.DataFrame,
) -> None:
    """Stdout self-check: identity reproduction + cross-ref rows."""
    print("\n=== CP-1 identity reproduction (harness vs direct gate) ===")
    for region in _REGIONS:
        direct = identity_direct[region]
        harness = grid_identity[region]
        diff = abs(harness - direct)
        flag = "OK" if diff <= 0.01 else "FAIL"
        print(
            f"  {region}: direct={direct:.4f}  harness={harness:.4f}  diff={diff:.4f}  [{flag}]"
        )

    print("\n=== Cross-reference (T04) ===")
    for _, row in cross_ref.iterrows():
        print(
            f"  [{row['label']}] cop={row['cooling_cop']} hf={row['heating_factor']} "
            f"ls={row['lighting_scale']} es={row['equipment_scale']} | "
            f"MA_nmbe={row['middle_atlantic_nmbe']:+.3f}% "
            f"PAC_nmbe={row['pacific_nmbe']:+.3f}% "
            f"WSC_nmbe={row['west_south_central_nmbe']:+.3f}%"
        )


def write_findings(
    grid_df: pd.DataFrame,
    cross_ref: pd.DataFrame,
    base_df: pd.DataFrame,
    region_refs: dict[str, pd.DataFrame],
    identity_direct: dict[str, float],
) -> Path:
    """Write RESULT_national_cbecs_rescore.md (data only, rule 9)."""
    id_mask = (
        (grid_df["cooling_cop"]    == 1.0)
        & (grid_df["heating_factor"]  == 1.0)
        & (grid_df["lighting_scale"]  == 1.0)
        & (grid_df["equipment_scale"] == 1.0)
    )
    id_row = grid_df[id_mask].iloc[0]

    # (a) Grid spec + reconstruction note
    grid_spec_lines = [
        "## Grid specification",
        "",
        f"- `cooling_cop` ∈ {_GRID['cooling_cop']}",
        f"- `heating_factor` ∈ {_GRID['heating_factor']}",
        f"- `lighting_scale` ∈ {_GRID['lighting_scale']}",
        f"- `equipment_scale` ∈ {_GRID['equipment_scale']}",
        f"- Total combos: {len(grid_df)} (5 × 2 × 4 × 3)",
        f"- Identity combo (1.0, 1.0, 1.0, 1.0) present: {_identity_present(grid_df)}",
        "",
        "**Note (§3 decision):** Service-load reconstruction is intentionally NOT applied here. "
        "The national CBECS gate compares to all-fuels site EUI; the published gate path scores "
        "the raw `total_eui_kwh_m2` with no reconstruction. "
        "This differs from the city sweep (v19_basis_diagnostic), which did apply reconstruction.",
    ]

    # (b) Per-region identity baseline
    id_rows_data = []
    for region in _REGIONS:
        id_rows_data.append({
            "region":      region,
            "nmbe":        id_row[f"{region}_nmbe"],
            "nmbe_pass":   id_row[f"{region}_nmbe_pass"],
            "cv_rmse":     id_row[f"{region}_cv_rmse"],
            "cv_rmse_pass": id_row[f"{region}_cv_rmse_pass"],
            "ks_d":        id_row[f"{region}_ks_d"],
            "ks_d_pass":   id_row[f"{region}_ks_d_pass"],
            "n":           id_row[f"{region}_n"],
        })
    id_baseline_df = pd.DataFrame(id_rows_data)
    id_baseline_lines = [
        "## Per-region identity baseline (as-is Phase-C, combo 1.0/1.0/1.0/1.0)",
        "",
        _df_to_md_table(id_baseline_df),
    ]

    # (c) Top-10 combos by max_abs_nmbe
    top10_cols = _PARAM_KEYS + [
        f"{r}_{k}" for r in _REGIONS for k in ("nmbe", "nmbe_pass", "cv_rmse_pass", "ks_d_pass")
    ] + ["max_abs_nmbe", "n_regions_nmbe_pass", "n_regions_cvrmse_pass"]
    top10 = grid_df.head(10)[top10_cols].copy()
    top10_lines = [
        "## Top-10 combos by max_abs_nmbe (ascending)",
        "",
        _df_to_md_table(top10),
    ]

    # (d) Cross-reference table (T04)
    xref_lines = [
        "## Cross-reference: identity vs city-anchor-winning combos (T04)",
        "",
        "**Generalization signal** = `nmbe_at_combo − nmbe_at_identity` per region "
        "(negative = moved toward 0 = generalizes; positive = moved away = worsen).",
        "",
    ]
    for combo_label in ["identity", "city_winner", "grid_min"]:
        c_row = cross_ref[cross_ref["label"] == combo_label].iloc[0]
        header_str = (
            f"### {combo_label}: cooling_cop={c_row['cooling_cop']} "
            f"heating_factor={c_row['heating_factor']} "
            f"lighting_scale={c_row['lighting_scale']} "
            f"equipment_scale={c_row['equipment_scale']}"
        )
        xref_lines.append(header_str)
        xref_lines.append("")
        per_region = []
        for region in _REGIONS:
            per_region.append({
                "region":       region,
                "nmbe":         c_row[f"{region}_nmbe"],
                "nmbe_pass":    c_row[f"{region}_nmbe_pass"],
                "cv_rmse":      c_row[f"{region}_cv_rmse"],
                "cv_rmse_pass": c_row[f"{region}_cv_rmse_pass"],
                "ks_d":         c_row[f"{region}_ks_d"],
                "ks_d_pass":    c_row[f"{region}_ks_d_pass"],
                "gen_signal":   c_row[f"{region}_gen_signal"],
            })
        xref_lines.append(_df_to_md_table(pd.DataFrame(per_region)))
        xref_lines.append(
            f"n_regions_nmbe_pass={c_row['n_regions_nmbe_pass']}  "
            f"n_regions_cvrmse_pass={c_row['n_regions_cvrmse_pass']}"
        )
        xref_lines.append("")

    # (e) Region-pass count table per combo
    pass_count_rows = []
    for _, c_row in cross_ref.iterrows():
        pass_count_rows.append({
            "label":               c_row["label"],
            "cooling_cop":         c_row["cooling_cop"],
            "n_regions_nmbe_pass": c_row["n_regions_nmbe_pass"],
            "n_regions_cvrmse_pass": c_row["n_regions_cvrmse_pass"],
        })
    pass_count_df = pd.DataFrame(pass_count_rows)
    pass_lines = [
        "## Region-pass count summary (NMBE |·| < 10% and CV(RMSE) < 30%)",
        "",
        _df_to_md_table(pass_count_df),
        "",
        "**F8 cross-reference (factual):** On the OLD Boston-R3 New-England single-cell dataset, "
        "a ÷3.5 cooling / ×1.19 heating basis moved NMBE from −16% → −29.5%. "
        "That dataset is DIFFERENT from Phase-C; this table is the Phase-C evidence.",
    ]

    sections = (
        ["# RESULT — V19 National CBECS Re-score Under COP Energy Basis", ""]
        + grid_spec_lines + [""]
        + id_baseline_lines + [""]
        + top10_lines + [""]
        + xref_lines
        + pass_lines + [""]
    )

    out_path = _OUT_DIR / "RESULT_national_cbecs_rescore.md"
    out_path.write_text("\n".join(sections), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# T06 — Reconstruction-ON single-combo national scorer
# ---------------------------------------------------------------------------

def score_combo_national_recon(
    base_df: pd.DataFrame,
    coeffs: dict,
    region_refs: dict[str, pd.DataFrame],
    params: dict[str, float],
) -> dict[str, Any]:
    """apply_basis_to_frame → reconstruct_frame → per-city gate on reconstructed total.

    Mirrors score_combo_national but uses the reconstructed total column (_RECON_TOTAL_COL)
    as the scored EUI — identical to the city sweep in v19_basis_diagnostic.score_combo.
    """
    transformed = apply_basis_to_frame(
        base_df,
        cooling_cop=params["cooling_cop"],
        heating_factor=params["heating_factor"],
        lighting_scale=params["lighting_scale"],
        equipment_scale=params["equipment_scale"],
    )
    reconstructed = reconstruct_frame(transformed, coeffs)

    result: dict[str, Any] = dict(params)
    result["recon"] = True
    abs_nmbes: list[float] = []
    nmbe_passes: list[bool] = []
    cvrmse_passes: list[bool] = []

    for city, region in _CITY_REGION.items():
        city_df = reconstructed[reconstructed["city"] == city].copy()
        # Alias: gate scorer reads eui_kwh_m2 (G1/§3); here we use reconstructed total
        city_df["eui_kwh_m2"] = city_df[_RECON_TOTAL_COL]
        gates = compute_validation_gates(city_df, reference_table=region_refs[region])

        nmbe = gates["cbecs_nmbe"]
        cv_rmse = gates["cbecs_cv_rmse"]
        ks_d = gates["cbecs_ks_d"]
        n = gates["n_sim_buildings"]

        result[f"{region}_nmbe"]         = nmbe
        result[f"{region}_nmbe_pass"]    = gates["cbecs_nmbe_pass"]
        result[f"{region}_cv_rmse"]      = cv_rmse
        result[f"{region}_cv_rmse_pass"] = gates["cbecs_cv_rmse_pass"]
        result[f"{region}_ks_d"]         = ks_d
        result[f"{region}_ks_d_pass"]    = gates["cbecs_ks_d_pass"]
        result[f"{region}_n"]            = n

        abs_nmbes.append(abs(nmbe))
        nmbe_passes.append(gates["cbecs_nmbe_pass"])
        cvrmse_passes.append(gates["cbecs_cv_rmse_pass"])

    result["max_abs_nmbe"]          = round(max(abs_nmbes), 4)
    result["n_regions_nmbe_pass"]   = sum(nmbe_passes)
    result["n_regions_cvrmse_pass"] = sum(cvrmse_passes)
    return result


# ---------------------------------------------------------------------------
# T07 — Run the reconstruction-ON 120-combo grid
# ---------------------------------------------------------------------------

def run_grid_recon(
    base_df: pd.DataFrame,
    coeffs: dict,
    region_refs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Iterate _GRID (120 combos) with reconstruction ON; return DataFrame sorted by max_abs_nmbe."""
    rows = []
    for cop, hf, ls, es in itertools.product(
        _GRID["cooling_cop"],
        _GRID["heating_factor"],
        _GRID["lighting_scale"],
        _GRID["equipment_scale"],
    ):
        params = {
            "cooling_cop":     cop,
            "heating_factor":  hf,
            "lighting_scale":  ls,
            "equipment_scale": es,
        }
        rows.append(score_combo_national_recon(base_df, coeffs, region_refs, params))

    assert len(rows) == 120, f"Recon grid length {len(rows)} != 120"
    df = pd.DataFrame(rows).sort_values("max_abs_nmbe").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# T08 — Reconstructed cross-reference + findings memo (data only, rule 9)
# ---------------------------------------------------------------------------

def build_cross_reference_recon(grid_recon_df: pd.DataFrame) -> pd.DataFrame:
    """Extract the three focal combos from the reconstructed grid; add gen-signal deltas."""
    rows = []
    identity_nmbes: dict[str, float] = {}

    for combo in _COMBOS_TO_CHECK:
        cop   = combo["cooling_cop"]
        hf    = combo["heating_factor"]
        ls    = combo["lighting_scale"]
        es    = combo["equipment_scale"]
        label = combo["label"]

        mask = (
            (grid_recon_df["cooling_cop"]    == cop)
            & (grid_recon_df["heating_factor"]  == hf)
            & (grid_recon_df["lighting_scale"]  == ls)
            & (grid_recon_df["equipment_scale"] == es)
        )
        assert mask.any(), f"Recon combo {label} ({cop},{hf},{ls},{es}) not found in grid"
        row = grid_recon_df[mask].iloc[0]

        if label == "identity":
            for region in _REGIONS:
                identity_nmbes[region] = float(row[f"{region}_nmbe"])

        entry: dict[str, Any] = {
            "label": label,
            "cooling_cop": cop,
            "heating_factor": hf,
            "lighting_scale": ls,
            "equipment_scale": es,
        }
        for region in _REGIONS:
            entry[f"{region}_nmbe"]          = row[f"{region}_nmbe"]
            entry[f"{region}_nmbe_pass"]     = row[f"{region}_nmbe_pass"]
            entry[f"{region}_cv_rmse"]       = row[f"{region}_cv_rmse"]
            entry[f"{region}_cv_rmse_pass"]  = row[f"{region}_cv_rmse_pass"]
            entry[f"{region}_ks_d"]          = row[f"{region}_ks_d"]
            entry[f"{region}_ks_d_pass"]     = row[f"{region}_ks_d_pass"]

        entry["n_regions_nmbe_pass"]   = int(row["n_regions_nmbe_pass"])
        entry["n_regions_cvrmse_pass"] = int(row["n_regions_cvrmse_pass"])
        rows.append(entry)

    identity_row = {r["label"]: r for r in rows}["identity"]
    for entry in rows:
        for region in _REGIONS:
            entry[f"{region}_gen_signal"] = round(
                float(entry[f"{region}_nmbe"]) - float(identity_row[f"{region}_nmbe"]), 4
            )

    return pd.DataFrame(rows)


def write_findings_recon(
    grid_recon_df: pd.DataFrame,
    cross_ref_recon: pd.DataFrame,
    raw_grid_df: pd.DataFrame,
) -> Path:
    """Write RESULT_national_cbecs_rescore_reconstructed.md (data only, rule 9)."""
    id_mask = (
        (grid_recon_df["cooling_cop"]    == 1.0)
        & (grid_recon_df["heating_factor"]  == 1.0)
        & (grid_recon_df["lighting_scale"]  == 1.0)
        & (grid_recon_df["equipment_scale"] == 1.0)
    )
    id_row = grid_recon_df[id_mask].iloc[0]

    # (a) Grid spec + reconstruction note
    grid_spec_lines = [
        "## Grid specification",
        "",
        f"- `cooling_cop` ∈ {_GRID['cooling_cop']}",
        f"- `heating_factor` ∈ {_GRID['heating_factor']}",
        f"- `lighting_scale` ∈ {_GRID['lighting_scale']}",
        f"- `equipment_scale` ∈ {_GRID['equipment_scale']}",
        f"- Total combos: {len(grid_recon_df)} (5 × 2 × 4 × 3)",
        f"- Identity combo (1.0, 1.0, 1.0, 1.0) present: {_identity_present(grid_recon_df)}",
        "",
        "**Note:** Service-load reconstruction IS applied here (`reconstruct_frame` via "
        "`openubem.results.service_loads`). The gate is scored on "
        f"`{_RECON_TOTAL_COL}` — the identical quantity the city sweep "
        "(v19_basis_diagnostic.score_combo) feeds to `build_city_table`. "
        "This is the companion to RESULT_national_cbecs_rescore.md (reconstruction OFF).",
    ]

    # (b) Per-region identity baseline (reconstructed)
    id_rows_data = []
    for region in _REGIONS:
        id_rows_data.append({
            "region":       region,
            "nmbe":         id_row[f"{region}_nmbe"],
            "nmbe_pass":    id_row[f"{region}_nmbe_pass"],
            "cv_rmse":      id_row[f"{region}_cv_rmse"],
            "cv_rmse_pass": id_row[f"{region}_cv_rmse_pass"],
            "ks_d":         id_row[f"{region}_ks_d"],
            "ks_d_pass":    id_row[f"{region}_ks_d_pass"],
            "n":            id_row[f"{region}_n"],
        })
    id_baseline_df = pd.DataFrame(id_rows_data)
    id_baseline_lines = [
        "## Per-region identity baseline — RECONSTRUCTED (combo 1.0/1.0/1.0/1.0)",
        "",
        _df_to_md_table(id_baseline_df),
    ]

    # (c) Top-10 by max_abs_nmbe
    top10_cols = _PARAM_KEYS + [
        f"{r}_{k}" for r in _REGIONS for k in ("nmbe", "nmbe_pass", "cv_rmse_pass", "ks_d_pass")
    ] + ["max_abs_nmbe", "n_regions_nmbe_pass", "n_regions_cvrmse_pass"]
    top10 = grid_recon_df.head(10)[top10_cols].copy()
    top10_lines = [
        "## Top-10 combos by max_abs_nmbe — RECONSTRUCTED (ascending)",
        "",
        _df_to_md_table(top10),
    ]

    # (d) Head-to-head table: reconstructed vs raw-total, for the 3 focal combos
    hth_lines = [
        "## Head-to-head: reconstructed vs raw-total (identity / 3.5·1·1·1 / 2.5·1.19·0.8·0.7)",
        "",
        "Values from `national_cbecs_sweep_reconstructed.csv` (recon) "
        "and `national_cbecs_sweep.csv` (raw). "
        "Joined on `(cooling_cop, heating_factor, lighting_scale, equipment_scale)`.",
        "",
    ]
    join_keys = _PARAM_KEYS

    for combo in _COMBOS_TO_CHECK:
        cop, hf, ls, es = (
            combo["cooling_cop"], combo["heating_factor"],
            combo["lighting_scale"], combo["equipment_scale"],
        )
        label = combo["label"]

        # Recon row
        recon_mask = (
            (grid_recon_df["cooling_cop"]    == cop)
            & (grid_recon_df["heating_factor"]  == hf)
            & (grid_recon_df["lighting_scale"]  == ls)
            & (grid_recon_df["equipment_scale"] == es)
        )
        recon_row = grid_recon_df[recon_mask].iloc[0]

        # Raw row (from raw_grid_df passed in)
        raw_mask = (
            (raw_grid_df["cooling_cop"]    == cop)
            & (raw_grid_df["heating_factor"]  == hf)
            & (raw_grid_df["lighting_scale"]  == ls)
            & (raw_grid_df["equipment_scale"] == es)
        )
        raw_row = raw_grid_df[raw_mask].iloc[0]

        hth_lines.append(
            f"### {label}: cooling_cop={cop} heating_factor={hf} "
            f"lighting_scale={ls} equipment_scale={es}"
        )
        hth_lines.append("")

        per_region_rows = []
        for region in _REGIONS:
            per_region_rows.append({
                "region":            region,
                "recon_nmbe":        recon_row[f"{region}_nmbe"],
                "recon_nmbe_pass":   recon_row[f"{region}_nmbe_pass"],
                "raw_nmbe":          raw_row[f"{region}_nmbe"],
                "raw_nmbe_pass":     raw_row[f"{region}_nmbe_pass"],
                "recon_cv_rmse":     recon_row[f"{region}_cv_rmse"],
                "recon_cv_rmse_pass": recon_row[f"{region}_cv_rmse_pass"],
                "raw_cv_rmse":       raw_row[f"{region}_cv_rmse"],
                "raw_cv_rmse_pass":  raw_row[f"{region}_cv_rmse_pass"],
                "recon_ks_d":        recon_row[f"{region}_ks_d"],
                "recon_ks_d_pass":   recon_row[f"{region}_ks_d_pass"],
                "raw_ks_d":          raw_row[f"{region}_ks_d"],
                "raw_ks_d_pass":     raw_row[f"{region}_ks_d_pass"],
            })
        hth_lines.append(_df_to_md_table(pd.DataFrame(per_region_rows)))
        hth_lines.append(
            f"recon n_regions_nmbe_pass={int(recon_row['n_regions_nmbe_pass'])}  "
            f"raw n_regions_nmbe_pass={int(raw_row['n_regions_nmbe_pass'])}  "
            f"recon n_regions_cvrmse_pass={int(recon_row['n_regions_cvrmse_pass'])}  "
            f"raw n_regions_cvrmse_pass={int(raw_row['n_regions_cvrmse_pass'])}"
        )
        hth_lines.append("")

    # (e) n_regions_nmbe_pass / n_regions_cvrmse_pass per combo
    pass_count_rows = []
    for _, c_row in cross_ref_recon.iterrows():
        pass_count_rows.append({
            "label":                 c_row["label"],
            "cooling_cop":           c_row["cooling_cop"],
            "recon_n_nmbe_pass":     c_row["n_regions_nmbe_pass"],
            "recon_n_cvrmse_pass":   c_row["n_regions_cvrmse_pass"],
        })
    pass_count_df = pd.DataFrame(pass_count_rows)
    pass_lines = [
        "## Region-pass count summary — RECONSTRUCTED (NMBE |·| < 10% and CV(RMSE) < 30%)",
        "",
        _df_to_md_table(pass_count_df),
    ]

    sections = (
        ["# RESULT — V19 National CBECS Re-score: Reconstruction-ON (Apples-to-Apples with City Sweep)", ""]
        + grid_spec_lines + [""]
        + id_baseline_lines + [""]
        + top10_lines + [""]
        + hth_lines
        + pass_lines + [""]
    )

    out_path = _OUT_DIR / "RESULT_national_cbecs_rescore_reconstructed.md"
    out_path.write_text("\n".join(sections), encoding="utf-8")
    return out_path


def _print_self_check_recon(
    recon_id_nmbes: dict[str, float],
    raw_id_nmbes: dict[str, float],
    city_pipeline_id_nmbes: dict[str, float] | None = None,
) -> None:
    """Stdout self-check for CP-3: identity parity + 3.5·1·1·1 reconstructed per-region NMBE."""
    print("\n=== CP-3 identity parity: reconstructed vs raw-total ===")
    for region in _REGIONS:
        recon = recon_id_nmbes[region]
        raw = raw_id_nmbes[region]
        print(f"  {region}: recon={recon:+.4f}%  raw={raw:+.4f}%")
    if city_pipeline_id_nmbes is not None:
        print("\n=== CP-3 pipeline-parity check: harness vs city-sweep identity ===")
        for region in _REGIONS:
            h = recon_id_nmbes[region]
            c = city_pipeline_id_nmbes.get(region, float("nan"))
            diff = abs(h - c)
            flag = "OK" if diff <= 1e-4 else "WARN"
            print(f"  {region}: harness_recon={h:+.4f}%  city_pipeline={c:+.4f}%  diff={diff:.6f}  [{flag}]")


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== V19 National CBECS Re-score ===")

    # T01: load data
    base_df = load_base()
    region_refs = load_region_refs()

    city_counts = {c: int((base_df["city"] == c).sum()) for c in _CITY_REGION}
    total_n = sum(city_counts.values())
    print(f"\n[T01] Success-row counts: {city_counts}  TOTAL={total_n}")
    assert abs(total_n - 8156) <= 50, f"Total success rows {total_n} not within ±50 of 8156"

    # CP-1: identity vs direct gate
    print("\n=== CP-1: identity harness vs direct gate ===")
    identity_direct: dict[str, float] = {}
    for city, region in _CITY_REGION.items():
        city_df = base_df[base_df["city"] == city].copy()
        direct_gates = score_region(city_df, region_refs[region])
        identity_direct[region] = direct_gates["cbecs_nmbe"]
        print(
            f"  direct  {region}: NMBE={direct_gates['cbecs_nmbe']:+.4f}%  "
            f"CV(RMSE)={direct_gates['cbecs_cv_rmse']:.4f}%  "
            f"KS_D={direct_gates['cbecs_ks_d']:.4f}  n={direct_gates['n_sim_buildings']}"
        )

    # T02/T03: run full grid
    print("\n=== Running 120-combo grid (T02/T03) ===")
    grid_df = run_grid(base_df, region_refs)
    assert len(grid_df) == 120
    assert _identity_present(grid_df), "Identity combo (1,1,1,1) missing from grid"

    csv_path = _OUT_DIR / "national_cbecs_sweep.csv"
    grid_df.to_csv(csv_path, index=False)
    print(f"Grid written: {csv_path} ({len(grid_df)} rows)")

    # Verify CP-1: harness identity vs direct
    id_mask = (
        (grid_df["cooling_cop"]    == 1.0)
        & (grid_df["heating_factor"]  == 1.0)
        & (grid_df["lighting_scale"]  == 1.0)
        & (grid_df["equipment_scale"] == 1.0)
    )
    id_row = grid_df[id_mask].iloc[0]
    print("\n=== CP-1 comparison ===")
    cp1_ok = True
    for region in _REGIONS:
        direct_nmbe  = identity_direct[region]
        harness_nmbe = float(id_row[f"{region}_nmbe"])
        diff = abs(harness_nmbe - direct_nmbe)
        flag = "OK" if diff <= 0.01 else "FAIL"
        if diff > 0.01:
            cp1_ok = False
        print(
            f"  {region}: direct={direct_nmbe:.4f}  harness={harness_nmbe:.4f}  "
            f"diff={diff:.4f}  [{flag}]"
        )

    if not cp1_ok:
        print("\nCP-1 FAILED — identity harness != direct gate. STOPPING.")
        sys.exit(1)
    print("\nCP-1 PASSED — proceeding to T04/T05.")

    # T04: cross-reference
    cross_ref = build_cross_reference(grid_df)
    print("\n=== T04 Cross-reference ===")
    print(cross_ref.to_string(index=False))

    # T05: write findings
    _print_self_check(identity_direct, {r: float(id_row[f"{r}_nmbe"]) for r in _REGIONS}, cross_ref)
    out_path = write_findings(grid_df, cross_ref, base_df, region_refs, identity_direct)
    print(f"\n[T05] Written: {out_path}")

    # -----------------------------------------------------------------------
    # T06/T07: reconstruction-ON grid
    # -----------------------------------------------------------------------
    print("\n=== T06/T07: Running 120-combo reconstruction-ON grid ===")
    coeffs = load_coefficients()
    grid_recon_df = run_grid_recon(base_df, coeffs, region_refs)
    assert len(grid_recon_df) == 120
    assert _identity_present(grid_recon_df), "Identity combo missing from recon grid"

    recon_csv_path = _OUT_DIR / "national_cbecs_sweep_reconstructed.csv"
    grid_recon_df.to_csv(recon_csv_path, index=False)
    print(f"Recon grid written: {recon_csv_path} ({len(grid_recon_df)} rows)")

    # Retrieve identity raw and recon NMBEs for CP-3 self-check
    raw_id_mask = (
        (grid_df["cooling_cop"]    == 1.0)
        & (grid_df["heating_factor"]  == 1.0)
        & (grid_df["lighting_scale"]  == 1.0)
        & (grid_df["equipment_scale"] == 1.0)
    )
    raw_id_nmbes = {r: float(grid_df[raw_id_mask].iloc[0][f"{r}_nmbe"]) for r in _REGIONS}

    recon_id_mask = (
        (grid_recon_df["cooling_cop"]    == 1.0)
        & (grid_recon_df["heating_factor"]  == 1.0)
        & (grid_recon_df["lighting_scale"]  == 1.0)
        & (grid_recon_df["equipment_scale"] == 1.0)
    )
    recon_id_nmbes = {r: float(grid_recon_df[recon_id_mask].iloc[0][f"{r}_nmbe"]) for r in _REGIONS}

    # T08: cross-reference and findings
    cross_ref_recon = build_cross_reference_recon(grid_recon_df)
    _print_self_check_recon(recon_id_nmbes, raw_id_nmbes)

    print("\n=== T08: Writing reconstructed findings ===")
    recon_out = write_findings_recon(grid_recon_df, cross_ref_recon, grid_df)
    print(f"[T08] Written: {recon_out}")

    # CP-3: 3.5·1·1·1 reconstructed per-region NMBE
    print("\n=== CP-3: 3.5·1·1·1 reconstructed per-region NMBE ===")
    city_winner_mask = (
        (grid_recon_df["cooling_cop"]    == 3.5)
        & (grid_recon_df["heating_factor"]  == 1.0)
        & (grid_recon_df["lighting_scale"]  == 1.0)
        & (grid_recon_df["equipment_scale"] == 1.0)
    )
    cw_row = grid_recon_df[city_winner_mask].iloc[0]
    for region in _REGIONS:
        print(
            f"  {region}: NMBE={cw_row[f'{region}_nmbe']:+.4f}%  "
            f"pass={cw_row[f'{region}_nmbe_pass']}"
        )
    print(f"  n_regions_nmbe_pass={int(cw_row['n_regions_nmbe_pass'])}")

    # Grid-min reconstructed
    best_recon_row = grid_recon_df.iloc[0]
    print(
        f"\n=== CP-3: Grid-min reconstructed (best max_abs_nmbe={best_recon_row['max_abs_nmbe']:.4f}) ==="
    )
    print(
        f"  cop={best_recon_row['cooling_cop']} hf={best_recon_row['heating_factor']} "
        f"ls={best_recon_row['lighting_scale']} es={best_recon_row['equipment_scale']}  "
        f"n_regions_nmbe_pass={int(best_recon_row['n_regions_nmbe_pass'])}"
    )
    for region in _REGIONS:
        print(
            f"    {region}: NMBE={best_recon_row[f'{region}_nmbe']:+.4f}%  "
            f"pass={best_recon_row[f'{region}_nmbe_pass']}"
        )
