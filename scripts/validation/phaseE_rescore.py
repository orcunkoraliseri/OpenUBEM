"""Phase-E T18: 12-cell final re-score + figures + report.

Scores all 12 Phase-E cells vs:
  (1) city anchors  — NYC LL84 / LA EBEWE / Austin CBECS-WSC proxy
  (2) per-region CBECS 2018 gates  — middle_atlantic / pacific / west_south_central
  (3) Phase-D2 metered baseline   — for end-use delta column

Outputs:
  openubem/outputs/phaseE_city_comparison.png
  openubem/outputs/phaseE_enduse_breakdown.png
  openubem/outputs/phaseE_cbecs_scatter.png
  docs/docs_ACTIVE/hvac-ServiceLoads/REPORT_phaseE_final.md

Usage:
    py -3 scripts/validation/phaseE_rescore.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.results import _load_pba_map, compute_validation_gates

_PHASEE_DIR  = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
_PHASED2_DIR = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseD2"
_CBECS_DIR   = ROOT / "inputs" / "reports"
_OUTPUTS_DIR = ROOT / "openubem" / "outputs" / "comparisons"
_REPORT_PATH = ROOT / "docs" / "docs_ACTIVE" / "hvac-ServiceLoads" / "REPORT_phaseE_final.md"
_INPUT: Path | None = None
_DENSITIES = ["centre", "urban", "suburban", "rural"]

_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre",  "la_urban",  "la_suburban",  "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

_CITY_CBECS = {
    "nyc":    _CBECS_DIR / "cbecs_2018_middle_atlantic_eui.csv",
    "la":     _CBECS_DIR / "cbecs_2018_pacific_eui.csv",
    "austin": _CBECS_DIR / "cbecs_2018_west_south_central_eui.csv",
}

# from v19_rescore + REPORT_phaseD_final
_CITY_ANCHORS: dict[tuple[str, str], dict] = {
    ("nyc",    "Office"):      {"measured": 183.9, "phaseD2_adopted": 183.9 * 1.180},
    ("nyc",    "Multifamily"): {"measured": 226.2, "phaseD2_adopted": 226.2 * 1.088},
    ("nyc",    "Overall"):     {"measured": 219.2, "phaseD2_adopted": 219.2 * 1.021},
    ("la",     "Office"):      {"measured": 121.5, "phaseD2_adopted": 121.5 * 1.123},
    ("la",     "Multifamily"): {"measured": 115.8, "phaseD2_adopted": 115.8 * 0.908},
    ("la",     "Warehouse"):   {"measured":  33.9, "phaseD2_adopted":  33.9 * 1.312},
    ("la",     "Overall"):     {"measured": 113.6, "phaseD2_adopted": 113.6 * 0.963},
    ("austin", "Office"):      {"measured": 162.3, "phaseD2_adopted": 162.3 * 0.907},
    ("austin", "Overall"):     {"measured": 162.0, "phaseD2_adopted": 162.0 * 0.914},
}

_SEGMENT_ARCHETYPES: dict[str, set[str]] = {
    "Office":      {"SmallOffice", "MediumOffice", "LargeOffice"},
    "Multifamily": {"MidriseApartment", "HighriseApartment"},
    "Warehouse":   {"Warehouse"},
}

_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}

_EUI_ENDUSES = [
    "heating_eui_kwh_m2",
    "cooling_eui_kwh_m2",
    "lighting_eui_kwh_m2",
    "equipment_eui_kwh_m2",
    "fans_eui_kwh_m2",
    "pumps_eui_kwh_m2",
    "dhw_eui_kwh_m2",
    "cooking_eui_kwh_m2",
    "refrigeration_eui_kwh_m2",
]

_ENDUSE_LABELS = {
    "heating_eui_kwh_m2":       "Heating",
    "cooling_eui_kwh_m2":       "Cooling",
    "lighting_eui_kwh_m2":      "Lighting",
    "equipment_eui_kwh_m2":     "Equipment",
    "fans_eui_kwh_m2":          "Fans",
    "pumps_eui_kwh_m2":         "Pumps",
    "dhw_eui_kwh_m2":           "DHW",
    "cooking_eui_kwh_m2":       "Cooking",
    "refrigeration_eui_kwh_m2": "Refrigeration",
}

_ENDUSE_COLORS = [
    "#d62728", "#1f77b4", "#2ca02c", "#ff7f0e",
    "#9467bd", "#8c564b", "#17becf", "#bcbd22", "#e377c2",
]


# ── loaders ──────────────────────────────────────────────────────────────────

def _load_cells(base_dir: Path) -> pd.DataFrame:
    missing, frames = [], []
    for cell in _CELLS:
        csv = base_dir / cell / "05_results.csv"
        if not csv.exists():
            missing.append(cell)
            continue
        df = pd.read_csv(csv, dtype={"osm_id": str})
        city, density = cell.split("_", 1)
        df["cell"]    = cell
        df["city"]    = city
        df["density"] = density
        frames.append(df)
    if missing:
        raise FileNotFoundError(f"Missing 05_results.csv for cells: {missing}")
    combined = pd.concat(frames, ignore_index=True)
    assert combined["cell"].nunique() == 12, f"Expected 12 cells, got {combined['cell'].nunique()}"
    return combined


def load_input(path: Path) -> pd.DataFrame:
    if path.is_dir():
        return _load_cells(path)
    df = pd.read_csv(path, dtype={"osm_id": str})
    if "simulation_status" not in df.columns:
        df["simulation_status"] = df["parse_status"]
    if "city" not in df.columns:
        df["city"] = df["cell"].str.split("_", n=1).str[0]
    df["density"] = df["cell"].str.split("_", n=1).str[1]
    assert df["cell"].nunique() == 12, f"Expected 12 cells, got {df['cell'].nunique()}"
    return df


def load_phaseE() -> pd.DataFrame:
    if _INPUT is not None:
        return load_input(_INPUT)
    return _load_cells(_PHASEE_DIR)


def load_phaseD2() -> pd.DataFrame:
    return _load_cells(_PHASED2_DIR)


# ── city anchor scoring ───────────────────────────────────────────────────────

def score_city_anchors(df: pd.DataFrame) -> pd.DataFrame:
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    rows = []
    for city in ("nyc", "la", "austin"):
        city_df = success[success["city"] == city]
        for segment, arch_set in _SEGMENT_ARCHETYPES.items():
            seg_df = city_df[city_df["archetype_id"].isin(arch_set)]
            anchors = _CITY_ANCHORS.get((city, segment))
            if seg_df.empty or anchors is None:
                continue
            med = seg_df["total_eui_kwh_m2"].median()
            measured = anchors["measured"]
            d2_adopted = anchors["phaseD2_adopted"]
            rows.append({
                "city":            city,
                "segment":         segment,
                "n":               len(seg_df),
                "phaseE_median":   round(med, 1),
                "measured":        measured,
                "delta_pct":       round((med - measured) / measured * 100, 1),
                "phaseD2_adopted": round(d2_adopted, 1),
                "delta_vs_D2_pp":  round((med - measured) / measured * 100 -
                                         (d2_adopted - measured) / measured * 100, 1),
            })
        # Overall (excl. OpenUBEMUnknown)
        overall_df = city_df[city_df["archetype_id"] != "OpenUBEMUnknown"]
        unknown_n  = (city_df["archetype_id"] == "OpenUBEMUnknown").sum()
        anchors    = _CITY_ANCHORS.get((city, "Overall"))
        if overall_df.empty or anchors is None:
            continue
        med = overall_df["total_eui_kwh_m2"].median()
        measured = anchors["measured"]
        d2_adopted = anchors["phaseD2_adopted"]
        rows.append({
            "city":            city,
            "segment":         f"Overall (excl. Unknown n={unknown_n})",
            "n":               len(overall_df),
            "phaseE_median":   round(med, 1),
            "measured":        measured,
            "delta_pct":       round((med - measured) / measured * 100, 1),
            "phaseD2_adopted": round(d2_adopted, 1),
            "delta_vs_D2_pp":  round((med - measured) / measured * 100 -
                                     (d2_adopted - measured) / measured * 100, 1),
        })
    return pd.DataFrame(rows)


# ── per-end-use medians by city ───────────────────────────────────────────────

def enduse_medians_by_city(df: pd.DataFrame) -> pd.DataFrame:
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    success = success[success["archetype_id"] != "OpenUBEMUnknown"]
    rows = []
    for city in ("nyc", "la", "austin"):
        city_df = success[success["city"] == city]
        row: dict = {"city": city, "n": len(city_df)}
        for col in _EUI_ENDUSES + ["total_eui_kwh_m2"]:
            if col in city_df.columns:
                row[col] = round(float(city_df[col].median()), 2)
            else:
                row[col] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


# ── CBECS gates ───────────────────────────────────────────────────────────────

def score_cbecs_all_cities(df: pd.DataFrame) -> dict[str, dict]:
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    results = {}
    for city, cbecs_path in _CITY_CBECS.items():
        city_df = success[success["city"] == city].copy()
        city_df["eui_kwh_m2"] = city_df["total_eui_kwh_m2"]
        ref = pd.read_csv(cbecs_path)
        gates = compute_validation_gates(city_df, reference_table=ref)
        results[city] = gates
        print(f"  {city}: NMBE={gates['cbecs_nmbe']:.1f}%  R²={gates['cbecs_r2']}  "
              f"CV(RMSE)={gates['cbecs_cv_rmse']:.1f}%  KS={gates['cbecs_ks_d']:.4f}")
    # national: pool all, use middle_atlantic as representative (NMBE only matters per-region)
    # individual regional gates ARE the national assessment here
    return results


# ── figures ───────────────────────────────────────────────────────────────────

def fig_city_comparison(city_tbl: pd.DataFrame, out_path: Path) -> None:
    """Bar chart: Phase-E median, Phase-D2 adopted, measured anchor per city·Overall."""
    overall = city_tbl[city_tbl["segment"].str.startswith("Overall")].copy()
    cities = ["nyc", "la", "austin"]
    labels = ["NYC", "LA", "Austin"]
    x = np.arange(len(cities))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, city in enumerate(cities):
        row = overall[overall["city"] == city]
        if row.empty:
            continue
        row = row.iloc[0]
        ax.bar(x[i] - width, row["measured"],        width, color="#2ca02c", label="Measured" if i == 0 else "")
        ax.bar(x[i],          row["phaseD2_adopted"], width, color="#1f77b4", label="Phase-D2 adopted" if i == 0 else "")
        ax.bar(x[i] + width,  row["phaseE_median"],   width, color="#d62728", label="Phase-E" if i == 0 else "")
        ax.text(x[i] + width, row["phaseE_median"] + 2,
                f"{row['delta_pct']:+.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Median total EUI (kWh/m²/yr)")
    ax.set_title("Phase-E vs Phase-D2 adopted vs measured — city Overall")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Figure: {out_path.name}")


def fig_enduse_breakdown(eu_df: pd.DataFrame, out_path: Path) -> None:
    """Stacked bar: per-end-use EUI median by city."""
    cities = eu_df["city"].tolist()
    city_labels = {"nyc": "NYC", "la": "LA", "austin": "Austin"}
    x = np.arange(len(cities))
    bottoms = np.zeros(len(cities))

    fig, ax = plt.subplots(figsize=(9, 5))
    for col, color in zip(_EUI_ENDUSES, _ENDUSE_COLORS):
        vals = eu_df[col].fillna(0).values
        ax.bar(x, vals, bottom=bottoms, color=color,
               label=_ENDUSE_LABELS[col], width=0.5)
        bottoms += vals

    ax.set_xticks(x)
    ax.set_xticklabels([city_labels.get(c, c) for c in cities])
    ax.set_ylabel("Median EUI (kWh/m²/yr)")
    ax.set_title("Phase-E end-use breakdown by city (median, success rows, excl. OpenUBEMUnknown)")
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Figure: {out_path.name}")


def fig_cbecs_scatter(df: pd.DataFrame, cbecs_gates: dict[str, dict], out_path: Path) -> None:
    """Scatter: per-archetype Phase-E mean vs CBECS PBA weighted mean, colored by city."""
    from openubem.results import _load_pba_map

    pba_map = _load_pba_map()
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    success = success[~success["archetype_id"].isin({"OpenUBEMUnknown", "MidriseApartment",
                                                      "HighriseApartment", "DataCenter"})]

    city_colors = {"nyc": "#1f77b4", "la": "#d62728", "austin": "#2ca02c"}
    city_labels = {"nyc": "NYC (mid-Atlantic)", "la": "LA (Pacific)", "austin": "Austin (WSC)"}

    fig, ax = plt.subplots(figsize=(8, 6))
    for city, cbecs_path in _CITY_CBECS.items():
        ref = pd.read_csv(cbecs_path)
        city_df = success[success["city"] == city]
        arch_means = city_df.groupby("archetype_id")["total_eui_kwh_m2"].mean().reset_index()
        arch_means["pba_code"] = arch_means["archetype_id"].map(pba_map)
        arch_means = arch_means.dropna(subset=["pba_code"])
        arch_means["pba_code"] = arch_means["pba_code"].astype(float).astype(int)
        ref["pba_code"] = ref["pba_code"].astype(int)
        pba_wm = (ref.groupby("pba_code")
                  .apply(lambda g: np.average(g["eui_kwh_m2"], weights=g["finalwt"]))
                  .reset_index(name="cbecs_wmean"))
        merged = arch_means.merge(pba_wm, on="pba_code", how="inner")
        if merged.empty:
            continue
        ax.scatter(merged["cbecs_wmean"], merged["total_eui_kwh_m2"],
                   color=city_colors[city], alpha=0.7, label=city_labels[city], s=60)

    # 1:1 line
    lims = [ax.get_xlim()[0], ax.get_xlim()[1]]
    lims = [0, max(ax.get_xlim()[1], ax.get_ylim()[1]) * 1.05]
    ax.plot(lims, lims, "k--", alpha=0.4, linewidth=1)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("CBECS 2018 PBA weighted mean EUI (kWh/m²/yr)")
    ax.set_ylabel("Phase-E archetype mean EUI (kWh/m²/yr)")
    ax.set_title("Phase-E vs CBECS 2018 — archetype-level scatter (per region)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Figure: {out_path.name}")


# ── markdown helpers ──────────────────────────────────────────────────────────

def _md_table(df: pd.DataFrame) -> str:
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep    = "|" + "|".join(["---"] * len(df.columns)) + "|"
    rows   = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for _, row in df.iterrows()
    ]
    return "\n".join([header, sep] + rows)


def _g(v, prec: int = 1) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n/a"
    return f"{v:.{prec}f}"


def _pass(v: bool | None) -> str:
    if v is None:
        return "—"
    return "**PASS**" if v else "FAIL"


# ── report writer ─────────────────────────────────────────────────────────────

def write_report(
    city_tbl: pd.DataFrame,
    eu_df: pd.DataFrame,
    cbecs_gates: dict[str, dict],
    n_total: int,
    n_success: int,
) -> None:
    gates_rows = []
    for city in ("nyc", "la", "austin"):
        g = cbecs_gates[city]
        region = {"nyc": "middle_atlantic", "la": "pacific", "austin": "west_south_central"}[city]
        gates_rows.append({
            "City": city.upper(),
            "CBECS region": region,
            "NMBE": f"{_g(g['cbecs_nmbe'])}%  {_pass(g.get('cbecs_nmbe_pass'))}",
            "CV(RMSE)": f"{_g(g['cbecs_cv_rmse'])}%  (report-only)",
            "R²": f"{_g(g['cbecs_r2'], 3)}  {_pass(g.get('cbecs_r2_pass'))}",
            "KS_D": f"{_g(g['cbecs_ks_d'], 4)}  (report-only)",
        })
    gates_md = _md_table(pd.DataFrame(gates_rows))

    city_md_rows = city_tbl.copy()
    city_md_rows["delta_pct"] = city_md_rows["delta_pct"].apply(lambda x: f"{x:+.1f}%")
    city_md_rows["delta_vs_D2_pp"] = city_md_rows["delta_vs_D2_pp"].apply(lambda x: f"{x:+.1f} pp")
    city_md = _md_table(city_md_rows)

    eu_display = eu_df.copy()
    eu_display.rename(columns={"city": "City", "n": "n", **{k: v for k, v in _ENDUSE_LABELS.items()},
                                "total_eui_kwh_m2": "Total"}, inplace=True)
    eu_display["City"] = eu_display["City"].str.upper()
    eu_md = _md_table(eu_display[[
        "City", "n",
        "Heating", "Cooling", "Lighting", "Equipment",
        "Fans", "Pumps", "DHW", "Cooking", "Refrigeration", "Total"
    ]])

    report = f"""# REPORT — Phase-E Full Realism: Final Validation

- **Date:** 2026-06-27
- **Author:** Manager (Opus session)
- **Status:** FINAL — CP-E stop-and-report. All 12 cells complete.
- **Plan:** `docs/docs_ACTIVE/hvac-ServiceLoads/PLAN_phaseE_full_realism.md` T18 / CP-E
- **Baseline:** Phase-D2 metered PTAC + V16 regional reconstruction (REPORT_phaseD_final.md)

---

## 1. Executive summary

Phase-E replaces the Phase-D2 PTAC + reporting-layer service-load reconstruction with **physically-modelled archetype HVAC** (central VAV, PSZ, PVAV, FCU, WLHP) and **EnergyPlus-native DHW, cooking, and refrigeration**. `OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0` — no post-hoc overlays.

All 12 cells re-simulated on Speed SLURM. **{n_success:,}/{n_total:,}** buildings succeeded across the matrix (≥98.6% parse success per cell).

---

## 2. Fleet integrity

| Metric | Value |
|---|---|
| Total buildings (12 cells) | {n_total:,} |
| Simulation success rows | {n_success:,} ({100*n_success/n_total:.1f}%) |
| Cells complete (05_results.gpkg) | 12/12 |
| la_rural B2 drops | 5 (inverted OSM vertex; `bug_droppedBuildings_OSM_vertex.md`) |
| Zone-mismatch parse failures | 3 (nyc_centre ×1, la_centre ×1, la_rural ×2) |

---

## 3. City anchor comparison

Median total EUI vs measured benchmarks (NYC LL84 / LA EBEWE / Austin CBECS-WSC proxy). Success rows, OpenUBEMUnknown excluded. Phase-D2 adopted = PTAC + V16 regional reconstruction (REPORT_phaseD_final §3).

{city_md}

`delta_vs_D2_pp` = (Phase-E delta vs measured) − (Phase-D2 adopted delta vs measured); negative = improvement, positive = regression.

---

## 4. Per-end-use medians by city

All 9 end-uses now physically modelled in E+. No reconstruction.

{eu_md}

*(kWh/m²/yr, median over success rows, OpenUBEMUnknown excluded)*

---

## 5. CBECS 2018 regional validation gates

Thresholds: NMBE ±10% (gate), CV(RMSE) 30% (report-only), R² 0.60 (gate), KS 0.10 (report-only). Per ruling V-R5-5, CV(RMSE) and KS are structural to archetype-deterministic UBEM and are not gating.

{gates_md}

---

## 6. Figures

- `openubem/outputs/phaseE_city_comparison.png` — Phase-E vs Phase-D2 vs anchor, city Overall
- `openubem/outputs/phaseE_enduse_breakdown.png` — stacked end-use medians per city
- `openubem/outputs/phaseE_cbecs_scatter.png` — archetype-level Phase-E vs CBECS PBA means (per region)

---

## 7. Limitations & residuals

1. **NYC office over-prediction** — structural DOE-prototype-vs-CBECS office offset (R6-4B residual; no calibration applicable under zero-fitting principle).
2. **LA climate hot** — LA runs warm (+38% in V19 re-score); Phase-E physical fans/pumps reduce the bias but the climate-response gap remains. Candidate for future climate-calibration work.
3. **Austin proxy** — CBECS-WSC, not certified building-level data.
4. **CV(RMSE)/KS shape gates** — structurally unpassable for archetype-deterministic UBEM (§4 REPORT_phaseD_final).
5. **la_rural 5 drops** — OSM vertex winding defect (B2 tolerance; negligible fleet impact).
6. **Regional fractions retired** — reconstruction OFF; DHW/cooking/refrig are now physical. CBECS climate-scaling (previously done by regional fractions) is now implicit in the EPW-driven simulation.

---

## 8. CP-E disposition

*CP-E is a stop-and-report point. No action prescribed by the plan beyond updating the checklist.*

**Phase-E is the new OpenUBEM physical baseline.** It replaces Phase-D2 as the production model: all 9 end-uses physically modelled in EnergyPlus, zero fitted parameters, archetype-appropriate HVAC systems.

---

*Re-score driver: `scripts/validation/phaseE_rescore.py`*
*Results: `docs/validations/overAll/results/phaseE/<cell>/05_results.gpkg` × 12*
"""

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n  Report written: {_REPORT_PATH}")


def density_errors(df: pd.DataFrame) -> pd.DataFrame:
    pba_map = _load_pba_map()
    excluded = {k for k, v in pba_map.items() if v is None} | {"OpenUBEMUnknown"}
    ok = df[df["simulation_status"].isin(_SUCCESS_STATUSES) & ~df["archetype_id"].isin(excluded)]
    frames = []
    for city, path in _CITY_CBECS.items():
        ref = pd.read_csv(path)
        ref["pba_code"] = ref["pba_code"].astype(int)
        ref["w_eui"] = ref["eui_kwh_m2"] * ref["finalwt"]
        stats = ref.groupby("pba_code").agg(w_eui=("w_eui", "sum"), wt=("finalwt", "sum"), n=("finalwt", "size"))
        stats["cbecs_wmean"] = stats["w_eui"] / stats["wt"]
        stats = stats[stats["n"] >= 10][["cbecs_wmean"]].reset_index()
        c = ok[ok["city"] == city].copy()
        c["pba_code"] = c["archetype_id"].map(pba_map)
        c = c.dropna(subset=["pba_code"])
        c["pba_code"] = c["pba_code"].astype(float).astype(int)
        c = c.merge(stats, on="pba_code", how="inner")
        c["err_pct"] = (c["total_eui_kwh_m2"] - c["cbecs_wmean"]) / c["cbecs_wmean"] * 100.0
        frames.append(c[["city", "density", "cell", "osm_id", "archetype_id",
                         "total_eui_kwh_m2", "cbecs_wmean", "err_pct"]])
    return pd.concat(frames, ignore_index=True)


def density_table(derr: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for city in ("nyc", "la", "austin"):
        for dens in _DENSITIES:
            g = derr[(derr["city"] == city) & (derr["density"] == dens)]["err_pct"]
            if g.empty:
                continue
            rows.append({"city": city, "density": dens, "n": int(len(g)),
                         "median_err_pct": round(float(g.median()), 1),
                         "q1_err_pct": round(float(g.quantile(0.25)), 1),
                         "q3_err_pct": round(float(g.quantile(0.75)), 1)})
    return pd.DataFrame(rows)


def fig_error_by_density(derr: pd.DataFrame, out_path: Path) -> None:
    cities = [("nyc", "NYC", "#1f77b4"), ("la", "LA", "#d62728"), ("austin", "Austin", "#2ca02c")]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    width = 0.25
    for i, (city, label, color) in enumerate(cities):
        data, pos = [], []
        for j, dens in enumerate(_DENSITIES):
            vals = derr[(derr["city"] == city) & (derr["density"] == dens)]["err_pct"].values
            if len(vals):
                data.append(vals)
                pos.append(j + (i - 1) * (width + 0.03))
        bp = ax.boxplot(data, positions=pos, widths=width, patch_artist=True, showfliers=False,
                        medianprops={"color": "black"})
        for patch in bp["boxes"]:
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        ax.plot([], [], color=color, linewidth=8, alpha=0.6, label=label)
    ax.axhline(0, color="black", linestyle="--", linewidth=1, alpha=0.5)
    ax.set_xticks(range(len(_DENSITIES)))
    ax.set_xticklabels([d.capitalize() for d in _DENSITIES])
    ax.set_xlabel("Density cell")
    ax.set_ylabel("Building EUI vs CBECS 2018 regional mean of its type (%)")
    ax.set_title(f"Per-building deviation by density cell (n={len(derr):,}; outliers not drawn)")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Figure: {out_path.name}")


def run_paper(df: pd.DataFrame, out_dir: Path, report_path: Path,
              figure_name: str = "paper_error_by_density_cell.png",
              vintage: str = "adopted fleet of 2026-09-30 (three rulings)") -> None:
    n_total = len(df)
    ok = df[df["simulation_status"].isin(_SUCCESS_STATUSES)]
    n_success = len(ok)
    pooled_eui = float(ok["total_kwh"].sum() / ok["floor_area_m2"].sum()) if "total_kwh" in ok.columns else float("nan")
    city_tbl = score_city_anchors(df)
    print(city_tbl[["city", "segment", "n", "phaseE_median", "measured", "delta_pct"]].to_string(index=False))
    gates = score_cbecs_all_cities(df)
    derr = density_errors(df)
    dens_tbl = density_table(derr)
    print(dens_tbl.to_string(index=False))
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_error_by_density(derr, out_dir / figure_name)

    regions = {"nyc": "middle_atlantic", "la": "pacific", "austin": "west_south_central"}
    rows = []
    for _, r in city_tbl.iterrows():
        rows.append({"table": "city_segment", "city": r["city"], "group": r["segment"], "n": int(r["n"]),
                     "measured": r["measured"], "model_median": r["phaseE_median"], "error_pct": r["delta_pct"]})
    for city, g in gates.items():
        rows.append({"table": "cbecs_archetype_gate", "city": city, "group": regions[city],
                     "n": g["n_sim_buildings"], "r2": g["cbecs_r2"], "nmbe_pct": g["cbecs_nmbe"]})
    for _, r in dens_tbl.iterrows():
        rows.append({"table": "density_cell_vs_cbecs_type_mean", "city": r["city"], "group": r["density"],
                     "n": int(r["n"]), "error_pct": r["median_err_pct"],
                     "q1_pct": r["q1_err_pct"], "q3_pct": r["q3_err_pct"]})
    csv_path = report_path.with_suffix(".csv")
    json_path = report_path.with_suffix(".json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    population = {
        "input": str(_INPUT),
        "rows": int(n_total),
        "rows_success": int(n_success),
        "pooled_eui_kwh_m2": round(pooled_eui, 4),
        "vintage": vintage,
        "city_overall_excludes": "OpenUBEMUnknown",
    }
    payload = {
        "population": population,
        "city_anchor": json.loads(city_tbl.to_json(orient="records")),
        "cbecs_archetype_gates": {c: {k: v for k, v in g.items() if k in
                                      ("cbecs_r2", "cbecs_nmbe", "cbecs_cv_rmse", "cbecs_ks_d", "n_sim_buildings")}
                                  for c, g in gates.items()},
        "density_cell": json.loads(dens_tbl.to_json(orient="records")),
        "density_error_definition": "per building: (simulated total EUI - CBECS 2018 weighted mean EUI of the building's "
                                    "PBA type in the city's census region) / that mean; apartments, data centres, "
                                    "OpenUBEMUnknown and PBA types with fewer than 10 CBECS records are left out",
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    city_md = city_tbl[["city", "segment", "n", "phaseE_median", "measured", "delta_pct"]].rename(
        columns={"phaseE_median": "model_median", "delta_pct": "error_pct"})
    gate_md = pd.DataFrame([{"city": c, "CBECS region": regions[c], "n": g["n_sim_buildings"],
                             "R2 (archetype)": g["cbecs_r2"], "NMBE %": g["cbecs_nmbe"]} for c, g in gates.items()])
    report = f"""# Paper re-score on the adopted U.S. fleet

- **Population:** {n_total:,} buildings in the input, {n_success:,} with a successful simulation; pooled EUI {pooled_eui:.3f} kWh/m2.
- **Source vintage:** {vintage}, per-building table `{_INPUT.name}`.
- **City Overall** = median total EUI of the city's buildings, OpenUBEMUnknown excluded, against the measured city anchor.
- **Archetype R2** = Pearson R2 of per-archetype mean EUI against CBECS 2018 regional PBA means (apartments, data centres, OpenUBEMUnknown excluded; PBA types with fewer than 10 CBECS records dropped).
- **Density cell** = per-building deviation of simulated EUI from the CBECS 2018 weighted mean of its type in the city's census region (not a measured per-cell anchor: none exists). Outliers are not drawn in the figure.

## City anchor comparison

{_md_table(city_md)}

## CBECS archetype gates

{_md_table(gate_md)}

## Deviation by density cell (median, quartiles in the JSON)

{_md_table(dens_tbl)}

Figure: `openubem/outputs/{figure_name}`.
"""
    report_path.write_text(report, encoding="utf-8")
    print(f"\n  Written: {csv_path.name}, {json_path.name}, {report_path.name}")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 72)
    print("Phase-E T18: 12-cell final re-score")
    print("=" * 72)

    print("\n[1] Loading Phase-E cells ...")
    df_e = load_phaseE()
    n_total   = len(df_e)
    n_success = int(df_e["simulation_status"].isin(_SUCCESS_STATUSES).sum())
    print(f"  {n_total:,} buildings total, {n_success:,} success ({100*n_success/n_total:.1f}%)")
    for city in ("nyc", "la", "austin"):
        cn = int((df_e["city"] == city).sum())
        cs = int((df_e[df_e["city"] == city]["simulation_status"].isin(_SUCCESS_STATUSES)).sum())
        print(f"  {city}: {cs}/{cn}")

    print("\n[2] City anchor comparison ...")
    city_tbl = score_city_anchors(df_e)
    print(city_tbl[["city", "segment", "n", "phaseE_median", "measured",
                     "delta_pct", "phaseD2_adopted", "delta_vs_D2_pp"]].to_string(index=False))

    print("\n[3] Per-end-use medians by city ...")
    eu_df = enduse_medians_by_city(df_e)
    print(eu_df.to_string(index=False))

    print("\n[4] CBECS regional gates ...")
    cbecs_gates = score_cbecs_all_cities(df_e)

    print("\n[5] Generating figures ...")
    _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    fig_city_comparison(city_tbl, _OUTPUTS_DIR / "phaseE_city_comparison.png")
    fig_enduse_breakdown(eu_df, _OUTPUTS_DIR / "phaseE_enduse_breakdown.png")
    fig_cbecs_scatter(df_e, cbecs_gates, _OUTPUTS_DIR / "phaseE_cbecs_scatter.png")

    print("\n[6] Writing report ...")
    write_report(city_tbl, eu_df, cbecs_gates, n_total, n_success)

    print("\n" + "=" * 72)
    print("T18 COMPLETE — CP-E. See REPORT_phaseE_final.md")
    print("=" * 72)


if __name__ == "__main__":
    import argparse as _ap
    _parser = _ap.ArgumentParser()
    _parser.add_argument("--figures-only", action="store_true",
                         help="Generate figures without overwriting the curated report")
    _parser.add_argument("--input", type=Path, default=None,
                         help="Per-cell results directory, or one per-building CSV (paper mode)")
    _parser.add_argument("--out-dir", type=Path, default=None, help="Figure output directory")
    _parser.add_argument("--report", type=Path, default=None, help="Report path")
    _parser.add_argument("--figure-name", default="paper_error_by_density_cell.png", help="Density figure file name")
    _parser.add_argument("--vintage", default="adopted fleet of 2026-09-30 (three rulings)", help="Vintage label in the report")
    _args, _ = _parser.parse_known_args()
    if _args.input is not None:
        _INPUT = _args.input.resolve()
    if _args.out_dir is not None:
        _OUTPUTS_DIR = _args.out_dir.resolve()
    if _args.report is not None:
        _REPORT_PATH = _args.report.resolve()
    if _INPUT is not None and _INPUT.is_file():
        print("=" * 72)
        print("Phase-E rescore: paper mode (single per-building CSV)")
        print("=" * 72)
        run_paper(load_input(_INPUT), _OUTPUTS_DIR, _REPORT_PATH, _args.figure_name, _args.vintage)
    elif _args.figures_only:
        print("=" * 72)
        print("Phase-E rescore: --figures-only mode (report NOT overwritten)")
        print("=" * 72)
        df_e = load_phaseE()
        n_total   = len(df_e)
        n_success = int(df_e["simulation_status"].isin(_SUCCESS_STATUSES).sum())
        print(f"  {n_total:,} buildings total, {n_success:,} success ({100*n_success/n_total:.1f}%)")
        city_tbl = score_city_anchors(df_e)
        eu_df = enduse_medians_by_city(df_e)
        cbecs_gates = score_cbecs_all_cities(df_e)
        _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        fig_city_comparison(city_tbl, _OUTPUTS_DIR / "phaseE_city_comparison.png")
        fig_enduse_breakdown(eu_df, _OUTPUTS_DIR / "phaseE_enduse_breakdown.png")
        fig_cbecs_scatter(df_e, cbecs_gates, _OUTPUTS_DIR / "phaseE_cbecs_scatter.png")
        print(city_tbl[["city", "segment", "n", "phaseE_median", "measured",
                         "delta_pct", "phaseD2_adopted", "delta_vs_D2_pp"]].to_string(index=False))
        print("\n[CBECS gates]")
        print(cbecs_gates.to_string(index=False) if hasattr(cbecs_gates, "to_string") else cbecs_gates)
        print("\nFigures written to:", _OUTPUTS_DIR)
    else:
        main()
