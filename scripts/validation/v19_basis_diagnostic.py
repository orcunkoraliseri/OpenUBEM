"""V19 energy-basis diagnostic sweep (no resim).

Post-processes existing V19 results by applying COP/efficiency/load-scale
transforms to the four simulated EUI columns, re-running service-load
reconstruction, and re-scoring against measured anchors.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.v19_rescore import load_all_cells, build_city_table, CITY_ANCHORS, _df_to_md_table
from openubem.results.service_loads import load_coefficients, reconstruct_frame

# Six city×segment anchors used for scoring (F5)
_SCORE_SEGMENTS = [
    ("nyc", "Office"),
    ("nyc", "Overall"),
    ("la", "Office"),
    ("la", "Overall"),
    ("austin", "Office"),
    ("austin", "Overall"),
]

_DELTA_KEY = "delta_vs_measured_pct"


def _load_base() -> tuple[pd.DataFrame, dict]:
    """Load 12-cell combined frame and coefficients once."""
    base_df = load_all_cells()
    coeffs = load_coefficients()
    return base_df, coeffs


def apply_basis_to_frame(
    df: pd.DataFrame,
    cooling_cop: float,
    heating_factor: float,
    lighting_scale: float,
    equipment_scale: float,
) -> pd.DataFrame:
    """Return a copy of df with transformed EUI columns and recomputed total.

    cooling_eui  /= cooling_cop
    heating_eui  *= heating_factor
    lighting_eui *= lighting_scale
    equipment_eui *= equipment_scale
    total_eui_kwh_m2 = sum of four mutated columns  (F3)
    """
    out = df.copy()
    out["cooling_eui_kwh_m2"] = out["cooling_eui_kwh_m2"] / cooling_cop
    out["heating_eui_kwh_m2"] = out["heating_eui_kwh_m2"] * heating_factor
    out["lighting_eui_kwh_m2"] = out["lighting_eui_kwh_m2"] * lighting_scale
    out["equipment_eui_kwh_m2"] = out["equipment_eui_kwh_m2"] * equipment_scale
    out["total_eui_kwh_m2"] = (
        out["cooling_eui_kwh_m2"]
        + out["heating_eui_kwh_m2"]
        + out["lighting_eui_kwh_m2"]
        + out["equipment_eui_kwh_m2"]
    )
    return out


def score_combo(
    base_df: pd.DataFrame,
    coeffs: dict,
    params: dict[str, float],
) -> dict[str, Any]:
    """Transform base_df, reconstruct, score six anchors; return flat result dict.

    params keys: cooling_cop, heating_factor, lighting_scale, equipment_scale.
    Returns params + per-segment deltas + summary metrics.
    """
    transformed = apply_basis_to_frame(
        base_df,
        cooling_cop=params["cooling_cop"],
        heating_factor=params["heating_factor"],
        lighting_scale=params["lighting_scale"],
        equipment_scale=params["equipment_scale"],
    )
    reconstructed = reconstruct_frame(transformed, coeffs, force=True)
    city_tbl = build_city_table(reconstructed)

    result: dict[str, Any] = dict(params)

    deltas: list[float] = []
    for city, seg in _SCORE_SEGMENTS:
        if seg == "Overall":
            mask = (city_tbl["city"] == city) & city_tbl["segment"].str.startswith("Overall")
        else:
            mask = (city_tbl["city"] == city) & city_tbl["segment"].str.startswith(seg)
        col_key = f"{city}_{seg.lower()}_delta"
        if mask.any():
            delta = float(city_tbl.loc[mask, _DELTA_KEY].iloc[0])
            result[col_key] = round(delta, 2)
            deltas.append(abs(delta))
        else:
            result[col_key] = float("nan")
            deltas.append(float("nan"))

    finite = [d for d in deltas if not (d != d)]  # exclude NaN
    result["max_abs_delta"] = round(max(finite), 2) if finite else float("nan")
    result["sumsq_delta"] = round(sum(d ** 2 for d in finite), 2)
    result["n_within_15"] = sum(1 for d in finite if d <= 15.0)
    result["n_within_20"] = sum(1 for d in finite if d <= 20.0)
    return result


# ---------------------------------------------------------------------------
# T04 — Grid definition and sweep runner
# ---------------------------------------------------------------------------

_GRID = {
    "cooling_cop":      [1.0, 2.5, 3.0, 3.5, 4.0],
    "heating_factor":   [1.0, 1.19],
    "lighting_scale":   [1.0, 0.8, 0.6, 0.5],
    "equipment_scale":  [1.0, 0.7, 0.5],
}

_PARAM_KEYS = ["cooling_cop", "heating_factor", "lighting_scale", "equipment_scale"]

_OUT_DIR = ROOT / "docs" / "docs_DONE" / "phaseC_combinedResim" / "v19_validation"

_DELTA_KEYS = [
    "nyc_office_delta", "nyc_overall_delta",
    "la_office_delta",  "la_overall_delta",
    "austin_office_delta", "austin_overall_delta",
]


def run_grid(base_df: pd.DataFrame, coeffs: dict) -> pd.DataFrame:
    """Run all 120 combos; return DataFrame sorted by max_abs_delta ascending (T04)."""
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
        rows.append(score_combo(base_df, coeffs, params))

    assert len(rows) == 120, f"Grid length {len(rows)} != 120"
    df = pd.DataFrame(rows).sort_values("max_abs_delta").reset_index(drop=True)
    return df


def _identity_present(grid_df: pd.DataFrame) -> bool:
    mask = (
        (grid_df["cooling_cop"]    == 1.0)
        & (grid_df["heating_factor"]  == 1.0)
        & (grid_df["lighting_scale"]  == 1.0)
        & (grid_df["equipment_scale"] == 1.0)
    )
    return mask.any()


# ---------------------------------------------------------------------------
# T05 — Coherence analysis
# ---------------------------------------------------------------------------

def compute_coherence(grid_df: pd.DataFrame) -> dict:
    """Derive best-global combo, per-city ceilings, coherence verdict (T05).

    Returns a dict with keys:
      best_global_row      — Series (the top grid row)
      identity_max_abs     — float (identity combo max_abs_delta)
      per_city_ceiling     — dict {city: best max_abs_delta over that city's two anchors}
      n_within_15          — int (best-global combo anchors within ±15%)
      n_within_20          — int (best-global combo anchors within ±20%)
      nyc_la_opposite_sign — bool
    """
    # identity row
    id_mask = (
        (grid_df["cooling_cop"]    == 1.0)
        & (grid_df["heating_factor"]  == 1.0)
        & (grid_df["lighting_scale"]  == 1.0)
        & (grid_df["equipment_scale"] == 1.0)
    )
    identity_max_abs = float(grid_df.loc[id_mask, "max_abs_delta"].iloc[0])

    # best-global: first row after sort ascending
    best_row = grid_df.iloc[0]
    assert best_row["max_abs_delta"] <= identity_max_abs, (
        f"best-global {best_row['max_abs_delta']} > identity {identity_max_abs}"
    )

    # per-city ceiling: for each city, vary cooling_cop freely (all other params at their
    # global-best values from the best row), pick min max_abs over that city's two anchors
    _city_delta_cols = {
        "nyc":    ("nyc_office_delta",   "nyc_overall_delta"),
        "la":     ("la_office_delta",    "la_overall_delta"),
        "austin": ("austin_office_delta","austin_overall_delta"),
    }
    per_city_ceiling: dict[str, float] = {}
    for city, (col_a, col_b) in _city_delta_cols.items():
        # city-specific max_abs over the two anchors for each grid row
        city_max = grid_df[[col_a, col_b]].abs().max(axis=1)
        per_city_ceiling[city] = float(city_max.min())
        assert per_city_ceiling[city] <= best_row["max_abs_delta"], (
            f"Per-city ceiling {city}={per_city_ceiling[city]:.2f} > global best "
            f"{best_row['max_abs_delta']:.2f}"
        )

    n_within_15 = int(best_row["n_within_15"])
    n_within_20 = int(best_row["n_within_20"])

    nyc_signed = float(best_row["nyc_overall_delta"])
    la_signed  = float(best_row["la_overall_delta"])
    nyc_la_opposite = (nyc_signed * la_signed) < 0

    return {
        "best_global_row":      best_row,
        "identity_max_abs":     identity_max_abs,
        "per_city_ceiling":     per_city_ceiling,
        "n_within_15":          n_within_15,
        "n_within_20":          n_within_20,
        "nyc_la_opposite_sign": nyc_la_opposite,
    }


# ---------------------------------------------------------------------------
# T06 — Findings memo
# ---------------------------------------------------------------------------

_LOAD_SCALING_CAVEAT = (
    "Basis transform is exact for COP/fuel; a lower bound for loads. "
    "Dividing thermal cooling by a COP and multiplying thermal heating by a fuel factor "
    "are exact in post-processing. Scaling lighting_eui/equipment_eui is only a direct "
    "scaling of those columns — it cannot propagate the reduced internal gain into a lower "
    "cooling load (that needs a resim). Therefore load-scaling results are a lower bound "
    "on the true benefit."
)


def write_findings(grid_df: pd.DataFrame, coherence: dict) -> Path:
    """Write RESULT_basis_diagnostic.md with data tables only (T06, rule 8)."""
    best = coherence["best_global_row"]

    # (a) grid spec
    grid_spec_lines = [
        "## Grid specification",
        "",
        f"- `cooling_cop` ∈ {_GRID['cooling_cop']}",
        f"- `heating_factor` ∈ {_GRID['heating_factor']}",
        f"- `lighting_scale` ∈ {_GRID['lighting_scale']}",
        f"- `equipment_scale` ∈ {_GRID['equipment_scale']}",
        f"- Total combos: {len(grid_df)} (5 × 2 × 4 × 3)",
        f"- Identity combo (1.0, 1.0, 1.0, 1.0) present: {_identity_present(grid_df)}",
    ]

    # (b) verbatim caveat
    caveat_lines = [
        "## Load-scaling caveat (verbatim from plan §3)",
        "",
        f"> {_LOAD_SCALING_CAVEAT}",
    ]

    # (c) top-10 combos
    top10 = grid_df.head(10)[
        _PARAM_KEYS + _DELTA_KEYS + ["max_abs_delta", "sumsq_delta", "n_within_15", "n_within_20"]
    ].copy()
    top10_lines = [
        "## Top-10 combos by max_abs_delta (ascending)",
        "",
        _df_to_md_table(top10),
    ]

    # (d) best-global six-segment signed-delta table
    best_params = {k: best[k] for k in _PARAM_KEYS}
    best_deltas_rows = []
    for city, seg, col in [
        ("nyc",    "Office",  "nyc_office_delta"),
        ("nyc",    "Overall", "nyc_overall_delta"),
        ("la",     "Office",  "la_office_delta"),
        ("la",     "Overall", "la_overall_delta"),
        ("austin", "Office",  "austin_office_delta"),
        ("austin", "Overall", "austin_overall_delta"),
    ]:
        best_deltas_rows.append({
            "city": city,
            "segment": seg,
            "signed_delta_pct": round(float(best[col]), 2),
        })
    best_delta_df = pd.DataFrame(best_deltas_rows)
    best_global_lines = [
        "## Best-global combo",
        "",
        f"Parameters: cooling_cop={best_params['cooling_cop']}, "
        f"heating_factor={best_params['heating_factor']}, "
        f"lighting_scale={best_params['lighting_scale']}, "
        f"equipment_scale={best_params['equipment_scale']}",
        f"max_abs_delta: {best['max_abs_delta']:.2f}%  |  "
        f"sumsq_delta: {best['sumsq_delta']:.2f}  |  "
        f"n_within_15: {best['n_within_15']}  |  n_within_20: {best['n_within_20']}",
        "",
        "### Six-segment signed-delta table",
        "",
        _df_to_md_table(best_delta_df),
    ]

    # (e) per-city climate-aware ceiling
    ceiling = coherence["per_city_ceiling"]
    ceiling_df = pd.DataFrame([
        {"city": city, "best_achievable_max_abs_delta_pct": round(v, 2)}
        for city, v in ceiling.items()
    ])
    ceiling_lines = [
        "## Per-city climate-aware ceiling",
        "",
        "(Best max_abs_delta over that city's two anchors, allowing any cooling_cop in the grid.)",
        "",
        _df_to_md_table(ceiling_df),
    ]

    # (f) coherence verdict metrics
    coherence_lines = [
        "## Coherence verdict metrics",
        "",
        f"- Best-global n_within_15 (anchors within ±15%): {coherence['n_within_15']} / 6",
        f"- Best-global n_within_20 (anchors within ±20%): {coherence['n_within_20']} / 6",
        f"- NYC Overall signed delta (best-global): {best['nyc_overall_delta']:+.2f}%",
        f"- LA Overall signed delta (best-global):  {best['la_overall_delta']:+.2f}%",
        f"- NYC and LA Overall on opposite signs: {coherence['nyc_la_opposite_sign']}",
        f"- Identity max_abs_delta: {coherence['identity_max_abs']:.2f}%",
    ]

    sections = (
        ["# RESULT — V19 Basis Diagnostic Sweep", ""]
        + grid_spec_lines + [""]
        + caveat_lines + [""]
        + top10_lines + [""]
        + best_global_lines + [""]
        + ceiling_lines + [""]
        + coherence_lines + [""]
    )

    out_path = _OUT_DIR / "RESULT_basis_diagnostic.md"
    out_path.write_text("\n".join(sections), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    base_df, coeffs = _load_base()

    # --- identity self-check (CP-1) ---
    reconstructed = reconstruct_frame(base_df.copy(), coeffs, force=True)
    city_tbl = build_city_table(reconstructed)

    print("=== Identity reproduction (CP-1 check) ===")
    success_n = reconstructed[
        reconstructed["simulation_status"].str.startswith("success", na=False)
    ].shape[0]
    print(f"Success-row count: {success_n}")
    for city, seg in _SCORE_SEGMENTS:
        if seg == "Overall":
            mask = (city_tbl["city"] == city) & city_tbl["segment"].str.startswith("Overall")
        else:
            mask = (city_tbl["city"] == city) & city_tbl["segment"].str.startswith(seg)
        if mask.any():
            delta = city_tbl.loc[mask, _DELTA_KEY].iloc[0]
            print(f"  {city} {seg}: delta_vs_measured = {delta:+.1f}%")

    # --- T04: run full grid ---
    print("\n=== Running 120-combo grid (T04) ===")
    grid_df = run_grid(base_df, coeffs)
    assert len(grid_df) == 120
    assert _identity_present(grid_df), "Identity combo (1,1,1,1) missing from grid"
    csv_path = _OUT_DIR / "basis_sweep_combos.csv"
    grid_df.to_csv(csv_path, index=False)
    print(f"Grid written: {csv_path} ({len(grid_df)} rows)")

    # --- T05: coherence analysis ---
    print("\n=== Coherence analysis (T05) ===")
    coherence = compute_coherence(grid_df)
    best = coherence["best_global_row"]
    print(
        f"Best-global: cop={best['cooling_cop']} hf={best['heating_factor']} "
        f"ls={best['lighting_scale']} es={best['equipment_scale']} "
        f"max_abs_delta={best['max_abs_delta']:.2f}%"
    )
    print(f"Identity max_abs_delta: {coherence['identity_max_abs']:.2f}%")
    print(f"Per-city ceilings: {coherence['per_city_ceiling']}")
    print(f"n_within_15={coherence['n_within_15']}  n_within_20={coherence['n_within_20']}")
    print(f"NYC/LA opposite signs: {coherence['nyc_la_opposite_sign']}")

    # --- T06: write findings ---
    print("\n=== Writing RESULT_basis_diagnostic.md (T06) ===")
    out_path = write_findings(grid_df, coherence)
    print(f"Written: {out_path}")
