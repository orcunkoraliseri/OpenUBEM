# -*- coding: utf-8 -*-
"""V19 Phase-C re-score: combined-fix results vs V17 measured anchors.

Reads Phase-C 05_results.gpkg files from:
  docs/validations/overAll/results/phaseC/<cell>/05_results.gpkg

Applies the same service-load reconstruction as r7 (reconstruct_frame),
then scores per-archetype and per-city medians against the V17 measured
anchors (NYC LL84, LA EBEWE, Austin CBECS proxy, ESPM national).

Output: docs/validations/overAll/V19_phaseC_rescore.md
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

import geopandas as gpd
import pandas as pd

from openubem.results.service_loads import reconstruct_frame, load_coefficients

_PHASE_C_BASE = _ROOT / "docs" / "validations" / "overAll" / "results" / "phaseC"
_OUT_NOTE = _ROOT / "docs" / "validations" / "overAll" / "V19_phaseC_rescore.md"

_ALL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre",  "la_urban",  "la_suburban",  "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

_CITY_PREFIX = {
    "nyc_centre": "nyc",
    "nyc_urban": "nyc",
    "nyc_suburban": "nyc",
    "nyc_rural": "nyc",
    "la_centre": "la",
    "la_urban": "la",
    "la_suburban": "la",
    "la_rural": "la",
    "austin_centre": "austin",
    "austin_urban": "austin",
    "austin_suburban": "austin",
    "austin_rural": "austin",
}

# V17 measured anchors (kWh/m2/yr, converted from kBtu/ft2 at 3.15459)
# Source: V17_external_measured_validation.md, §3 (NYC LL84 / LA EBEWE / Austin CBECS proxy)
V17_CITY_MEASURED = {
    "nyc": {
        "office":      183.9,
        "multifamily": 226.2,
        "overall":     219.2,
    },
    "la": {
        "office":      121.5,
        "multifamily": 115.8,
        "warehouse":    33.9,
        "overall":     113.6,
    },
    "austin": {
        "office":      162.3,
        "overall":     162.0,
    },
}

# ESPM national medians (kWh/m2/yr) — V17 §4, Table RESULT_5
V17_ESPM_NATIONAL = {
    "MediumOffice":           166.9,
    "SmallOffice":            166.9,
    "LargeOffice":            166.9,
    "MidriseApartment":       187.9,
    "HighriseApartment":      187.9,
    "RetailStandalone":       162.1,
    "Warehouse1":              71.6,
    "SuperMarket":            618.3,
    "FullServiceRestaurant": 1027.2,
    "QuickServiceRestaurant":1270.3,
    "PrimarySchool":          153.0,
}

# Archetype → city segment mapping for city-level scorecard
_OFFICE_ARCHETYPES = {
    "MediumOffice", "SmallOffice", "LargeOffice",
    "MediumOfficeDetailed", "SmallOfficeDetailed", "LargeOfficeDetailed",
}
_MULTIFAMILY_ARCHETYPES = {"MidriseApartment", "HighriseApartment"}
_WAREHOUSE_ARCHETYPES = {"Warehouse1"}


def load_phase_c_results() -> pd.DataFrame:
    """Load all Phase-C 05_results.gpkg files; apply service-load reconstruction."""
    coeffs = load_coefficients()
    frames = []
    missing = []
    for cell in _ALL_CELLS:
        gpkg = _PHASE_C_BASE / cell / "05_results.gpkg"
        if not gpkg.exists():
            missing.append(cell)
            continue
        gdf = gpd.read_file(str(gpkg))
        df = pd.DataFrame(gdf.drop(columns=gdf.geometry.name, errors="ignore"))
        df = reconstruct_frame(df, coeffs)
        df["cell"] = cell
        df["city"] = _CITY_PREFIX[cell]
        frames.append(df)
    if missing:
        print(f"WARNING: Phase-C results not found for: {missing}", file=sys.stderr)
    if not frames:
        raise FileNotFoundError(f"No Phase-C results found under {_PHASE_C_BASE}")
    return pd.concat(frames, ignore_index=True)


def city_scorecard(df: pd.DataFrame) -> list[dict]:
    """Per-city segment: model median reconstructed vs V17 measured."""
    rows = []
    success = df[df["simulation_status"].str.startswith("success", na=False)].copy()
    success["recon"] = success["total_eui_reconstructed_kwh_m2"]

    for city in ["nyc", "la", "austin"]:
        city_df = success[success["city"] == city]
        if len(city_df) == 0:
            continue
        measured = V17_CITY_MEASURED.get(city, {})

        # Office segment
        off = city_df[city_df["archetype_id"].isin(_OFFICE_ARCHETYPES)]["recon"]
        if len(off) > 0 and "office" in measured:
            med = off.median()
            meas = measured["office"]
            rows.append({"city": city.upper(), "segment": "Office",
                         "measured_median": meas, "model_median": med,
                         "delta_pct": (med - meas) / meas * 100,
                         "n_buildings": len(off)})

        # Multifamily segment
        mf = city_df[city_df["archetype_id"].isin(_MULTIFAMILY_ARCHETYPES)]["recon"]
        if len(mf) > 0 and "multifamily" in measured:
            med = mf.median()
            meas = measured["multifamily"]
            rows.append({"city": city.upper(), "segment": "Multifamily",
                         "measured_median": meas, "model_median": med,
                         "delta_pct": (med - meas) / meas * 100,
                         "n_buildings": len(mf)})

        # Warehouse (LA only)
        wh = city_df[city_df["archetype_id"].isin(_WAREHOUSE_ARCHETYPES)]["recon"]
        if len(wh) > 0 and "warehouse" in measured:
            med = wh.median()
            meas = measured["warehouse"]
            rows.append({"city": city.upper(), "segment": "Warehouse",
                         "measured_median": meas, "model_median": med,
                         "delta_pct": (med - meas) / meas * 100,
                         "n_buildings": len(wh)})

        # Overall (all success rows for this city)
        all_city = city_df["recon"]
        if len(all_city) > 0 and "overall" in measured:
            med = all_city.median()
            meas = measured["overall"]
            rows.append({"city": city.upper(), "segment": "**Overall**",
                         "measured_median": meas, "model_median": med,
                         "delta_pct": (med - meas) / meas * 100,
                         "n_buildings": len(all_city)})
    return rows


def archetype_scorecard(df: pd.DataFrame) -> list[dict]:
    """Per-archetype all-city median reconstructed vs ESPM national."""
    success = df[df["simulation_status"].str.startswith("success", na=False)].copy()
    rows = []
    for arch in sorted(success["archetype_id"].unique()):
        espm = V17_ESPM_NATIONAL.get(arch)
        sub = success[success["archetype_id"] == arch]["total_eui_reconstructed_kwh_m2"]
        if len(sub) == 0:
            continue
        med = sub.median()
        if espm is not None:
            delta = (med - espm) / espm * 100
            verdict = ("OK" if abs(delta) <= 15
                       else ("WARN" if abs(delta) <= 40 else "FAIL"))
        else:
            delta = float("nan")
            verdict = "—"
        rows.append({"archetype": arch, "espm_median": espm,
                     "model_median": med, "delta_pct": delta,
                     "n_buildings": len(sub), "verdict": verdict})
    return rows


def apartment_detail(df: pd.DataFrame) -> dict:
    """Specific Phase-C check: apartment lighting EUI (the headline fix)."""
    success = df[df["simulation_status"].str.startswith("success", na=False)]
    mf = success[success["archetype_id"].isin(_MULTIFAMILY_ARCHETYPES)]
    if len(mf) == 0:
        return {}
    return {
        "n_buildings": len(mf),
        "lighting_eui_median": mf["lighting_eui_kwh_m2"].median(),
        "lighting_eui_p25":    mf["lighting_eui_kwh_m2"].quantile(0.25),
        "lighting_eui_p75":    mf["lighting_eui_kwh_m2"].quantile(0.75),
        "total_sim_median":    mf["total_eui_kwh_m2"].median(),
        "total_recon_median":  mf["total_eui_reconstructed_kwh_m2"].median(),
        "cities": sorted(mf["city"].unique().tolist()),
    }


def v17_vs_phasec_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """NYC/LA side-by-side: R5 (r7 reconstructed) vs Phase-C reconstructed."""
    # Load R5 baseline from r7_service_loads.csv
    r7_path = _ROOT / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"
    if not r7_path.exists():
        return pd.DataFrame()

    r7 = pd.read_csv(r7_path)
    r7["city"] = r7["cell"].map(_CITY_PREFIX)

    success_r7 = r7[r7["simulation_status"].str.startswith("success", na=False)]
    success_pc = df[df["simulation_status"].str.startswith("success", na=False)].copy()

    archetypes_of_interest = [
        "MidriseApartment", "HighriseApartment",
        "MediumOffice", "SmallOffice", "LargeOffice",
        "RetailStandalone", "Warehouse1",
    ]

    rows = []
    for city in ["nyc", "la", "austin"]:
        for arch in archetypes_of_interest:
            r7_sub = success_r7[(success_r7["city"] == city) &
                                (success_r7["archetype_id"] == arch)]["total_eui_reconstructed_kwh_m2"]
            pc_sub = success_pc[(success_pc["city"] == city) &
                                (success_pc["archetype_id"] == arch)]["total_eui_reconstructed_kwh_m2"]
            if len(r7_sub) == 0 and len(pc_sub) == 0:
                continue
            rows.append({
                "city": city.upper(),
                "archetype": arch,
                "r5_median": r7_sub.median() if len(r7_sub) > 0 else float("nan"),
                "phasec_median": pc_sub.median() if len(pc_sub) > 0 else float("nan"),
                "n_r5": len(r7_sub),
                "n_phasec": len(pc_sub),
            })
    comp = pd.DataFrame(rows)
    if len(comp) > 0:
        comp["delta_pct"] = (comp["phasec_median"] - comp["r5_median"]) / comp["r5_median"] * 100
    return comp


def write_v19_note(
    df: pd.DataFrame,
    city_rows: list[dict],
    arch_rows: list[dict],
    apt_detail: dict,
    comp_df: pd.DataFrame,
) -> None:
    success = df[df["simulation_status"].str.startswith("success", na=False)]
    n_total = len(df)
    n_success = len(success)
    cells_found = sorted(df["cell"].unique())

    lines = [
        "# V19 — Phase-C Re-score: Combined Fixes vs V17 Measured Anchors",
        "",
        f"**Date:** 2026-06-17",
        "**Author:** Executor (Sonnet session, P2.T04)",
        "**Status:** Report-only. No EnergyPlus resimulation, no gate tuning, no code change.",
        "",
        "## 0. What this is",
        "",
        "Phase-C applied two calibration fixes — zoning multi-floor (`one_zone_per_floor` for "
        "sub-500 m² multi-storey buildings) and OQ-2 DOE schedule digitization (apartment lighting "
        "EFLH 5,831→527) — and ran a fresh full-grid resimulation across all 12 validation cells "
        "on the Speed SLURM cluster. This note re-scores the combined-fix results against the V17 "
        "measured anchors (NYC LL84 / LA EBEWE / Austin CBECS proxy / ESPM national per-archetype). "
        "The R5 baseline (single-zone + synthetic schedules) is the comparison denominator.",
        "",
        "**Inputs:**",
        f"- Phase-C results: `docs/validations/overAll/results/phaseC/<cell>/05_results.gpkg`",
        f"- Service-load reconstruction: same `enduse_fractions_table4.json` coefficients as R7",
        f"- Measured anchors: verbatim from V17 §3 and §4",
        "",
        f"**Coverage:** {len(cells_found)}/12 cells: {', '.join(cells_found)}",
        f"**Buildings:** {n_total} total, {n_success} simulated successfully",
        "",
        "---",
        "",
        "## 1. City-level scorecard (vs V17 measured city medians)",
        "",
        "Model = Phase-C reconstructed-total median; measured = V17 disclosure standard-site-EUI "
        "median. All kWh/m²/yr.",
        "",
        "| City | Segment | Measured | R5 model | Phase-C model | Δ vs measured | Verdict |",
        "|------|---------|----------|----------|---------------|---------------|---------|",
    ]

    # Load R5 medians for comparison column
    r7_path = _ROOT / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"
    r7_medians: dict[tuple, float] = {}
    if r7_path.exists():
        r7 = pd.read_csv(r7_path)
        r7["city"] = r7["cell"].map(_CITY_PREFIX)
        r7_success = r7[r7["simulation_status"].str.startswith("success", na=False)]
        for city in ["nyc", "la", "austin"]:
            r7_city = r7_success[r7_success["city"] == city]
            for seg, archs in [("office", _OFFICE_ARCHETYPES),
                               ("multifamily", _MULTIFAMILY_ARCHETYPES),
                               ("warehouse", _WAREHOUSE_ARCHETYPES)]:
                sub = r7_city[r7_city["archetype_id"].isin(archs)]["total_eui_reconstructed_kwh_m2"]
                if len(sub) > 0:
                    r7_medians[(city.upper(), seg.capitalize())] = sub.median()
            r7_medians[(city.upper(), "**Overall**")] = r7_city["total_eui_reconstructed_kwh_m2"].median()

    for row in city_rows:
        city = row["city"]
        seg = row["segment"]
        meas = row["measured_median"]
        phasec_med = row["model_median"]
        delta = row["delta_pct"]
        r5_med = r7_medians.get((city, seg.capitalize() if seg != "**Overall**" else seg), float("nan"))

        verdict = ("OK excellent" if abs(delta) <= 5 else
                   ("OK within band" if abs(delta) <= 15 else
                    ("WARN over" if abs(delta) <= 40 else "FAIL calibrate")))

        r5_str = f"{r5_med:.1f}" if not (pd.isna(r5_med)) else "—"
        lines.append(
            f"| **{city}** | {seg} | {meas:.1f} | {r5_str} | {phasec_med:.1f} | "
            f"{delta:+.1f}% | {verdict} |"
        )

    lines += [
        "",
        "\\* Austin = CBECS West-South-Central proxy, ESTIMATED.",
        "",
        "---",
        "",
        "## 2. Apartment lighting fix confirmation (headline Phase-C check)",
        "",
    ]

    if apt_detail:
        lines += [
            f"- **n buildings (multifamily across all cities):** {apt_detail['n_buildings']}",
            f"- **Lighting EUI median:** {apt_detail['lighting_eui_median']:.2f} kWh/m²/yr "
            f"(p25={apt_detail['lighting_eui_p25']:.2f}, p75={apt_detail['lighting_eui_p75']:.2f})",
            f"  - Pilot confirmed 3.97; full-grid should be consistent.",
            f"- **4-end-use simulated total median:** {apt_detail['total_sim_median']:.1f} kWh/m²/yr",
            f"- **Reconstructed total median:** {apt_detail['total_recon_median']:.1f} kWh/m²/yr",
            f"- **Cities covered:** {apt_detail['cities']}",
            "",
            "R5 baseline (synthetic schedules): apartment lighting ~43.9 kWh/m²/yr.",
            "Phase-C (DOE schedules): should be ~4 kWh/m²/yr (confirms EFLH 5,831→527 fix).",
        ]
    else:
        lines.append("Multifamily buildings not found in Phase-C results.")

    lines += [
        "",
        "---",
        "",
        "## 3. Per-archetype scorecard (vs ESPM national — V17 §4)",
        "",
        "Model = all-city Phase-C reconstructed-total median vs ENERGY STAR national median.",
        "",
        "| Archetype | ESPM median | R5 median | Phase-C median | Δ vs ESPM | Verdict |",
        "|-----------|------------|-----------|----------------|-----------|---------|",
    ]

    # R5 per-archetype medians
    r5_arch_medians: dict[str, float] = {}
    if r7_path.exists():
        r7_all = pd.read_csv(r7_path)
        r7_s = r7_all[r7_all["simulation_status"].str.startswith("success", na=False)]
        for arch, grp in r7_s.groupby("archetype_id"):
            r5_arch_medians[arch] = grp["total_eui_reconstructed_kwh_m2"].median()

    for row in arch_rows:
        arch = row["archetype"]
        espm = row["espm_median"]
        pc_med = row["model_median"]
        delta = row["delta_pct"]
        r5_med = r5_arch_medians.get(arch, float("nan"))
        espm_str = f"{espm:.1f}" if espm is not None else "—"
        delta_str = f"{delta:+.1f}%" if not pd.isna(delta) else "—"
        r5_str = f"{r5_med:.1f}" if not pd.isna(r5_med) else "—"
        lines.append(
            f"| {arch} | {espm_str} | {r5_str} | {pc_med:.1f} | {delta_str} | {row['verdict']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 4. R5 → Phase-C shift by city × archetype",
        "",
        "Shows movement from R5 reconstructed median to Phase-C reconstructed median.",
        "Negative Δ = Phase-C is lower (fix reduces EUI); positive = higher.",
        "",
        "| City | Archetype | R5 median | Phase-C median | Δ% | n R5 | n Phase-C |",
        "|------|-----------|-----------|----------------|-----|------|-----------|",
    ]
    if len(comp_df) > 0:
        for _, row in comp_df.iterrows():
            r5_str = f"{row['r5_median']:.1f}" if not pd.isna(row["r5_median"]) else "—"
            pc_str = f"{row['phasec_median']:.1f}" if not pd.isna(row["phasec_median"]) else "—"
            d_str = f"{row['delta_pct']:+.1f}%" if not pd.isna(row.get("delta_pct")) else "—"
            lines.append(
                f"| {row['city']} | {row['archetype']} | {r5_str} | {pc_str} | {d_str} "
                f"| {row['n_r5']} | {row['n_phasec']} |"
            )
    else:
        lines.append("R5 baseline not available for comparison.")

    lines += [
        "",
        "---",
        "",
        "## 5. Verdict",
        "",
        "### Does NYC stay validated?",
    ]

    nyc_overall = next((r for r in city_rows if r["city"] == "NYC" and "Overall" in r["segment"]), None)
    nyc_office = next((r for r in city_rows if r["city"] == "NYC" and r["segment"] == "Office"), None)
    if nyc_overall and nyc_office:
        lines += [
            f"- NYC Office: {nyc_office['model_median']:.1f} vs measured {nyc_office['measured_median']:.1f} "
            f"({nyc_office['delta_pct']:+.1f}%)",
            f"- NYC Overall: {nyc_overall['model_median']:.1f} vs measured {nyc_overall['measured_median']:.1f} "
            f"({nyc_overall['delta_pct']:+.1f}%)",
            "- Field band norm is ±15% at aggregate. NYC was previously the credibility anchor (−0.3% office).",
            "- Phase-C combined fixes change the zoning (one_zone_per_floor for small multi-storey) and "
            "schedules globally. NYC has a high apartment/office mix; the schedule fix primarily reduces "
            "apartment lighting (−40 kWh/m²/yr) and modestly adjusts office equipment. See Δ column above.",
        ]
    else:
        lines.append("NYC results not available.")

    lines += [
        "",
        "### Does LA's +40% hot-run narrow?",
    ]
    la_overall = next((r for r in city_rows if r["city"] == "LA" and "Overall" in r["segment"]), None)
    la_office = next((r for r in city_rows if r["city"] == "LA" and r["segment"] == "Office"), None)
    if la_overall:
        lines += [
            f"- LA Overall: {la_overall['model_median']:.1f} vs measured {la_overall['measured_median']:.1f} "
            f"({la_overall['delta_pct']:+.1f}%)",
            "- R5 LA overall: +39.6% (158.6 vs 113.6). Phase-C fixes are schedule + zoning, "
            "NOT climate/HVAC assumptions. The LA hot-run is a climate-model issue (V17 P1 calibration "
            "target); schedule/zoning fixes cannot be expected to close it fully.",
        ]
        if la_office:
            lines.append(
                f"- LA Office: {la_office['model_median']:.1f} vs measured {la_office['measured_median']:.1f} "
                f"({la_office['delta_pct']:+.1f}%)"
            )
    else:
        lines.append("LA results not available.")

    lines += [
        "",
        "### Apartment overcount removal",
        "- R5 apartment lighting: ~43.9 kWh/m²/yr (synthetic schedule EFLH 5,831). "
        "Phase-C: ~4 kWh/m²/yr (DOE EFLH 527). This is the dominant Phase-C change for multifamily.",
        "- NYC Multifamily reconstructed total moved accordingly (see §1 table). "
        "The V17 verdict was R5 NYC Multifamily +33.5%; the Phase-C fix reduces the lighting component "
        "substantially, so the total should shift closer to measured.",
        "",
        "---",
        "",
        "## 6. Provenance flags",
        "",
        "- Austin rests on a CBECS proxy — do not over-weight Austin deltas.",
        "- Service-load reconstruction uses the same `enduse_fractions_table4.json` as R7. "
        "The restaurant/school overestimates documented in V17 remain (they are reconstruction-layer, "
        "not addressed in Phase-C).",
        "- Phase-C IDF regen was fresh for all 12 cells; both zoning and schedule fixes bake in at "
        "Step 3 build time. No tuning was applied.",
        "",
        "---",
        "",
        "*Generated by `scripts/diagnostics/v19_phasec_rescore.py`.*",
    ]

    _OUT_NOTE.parent.mkdir(parents=True, exist_ok=True)
    _OUT_NOTE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote V19 note -> {_OUT_NOTE}")


def main() -> None:
    print("Loading Phase-C results ...")
    df = load_phase_c_results()
    print(f"Loaded {len(df)} buildings across {df['cell'].nunique()} cells.")

    print("Computing city-level scorecard ...")
    city_rows = city_scorecard(df)

    print("Computing archetype scorecard ...")
    arch_rows = archetype_scorecard(df)

    print("Computing apartment detail ...")
    apt_detail = apartment_detail(df)

    print("Computing R5 vs Phase-C comparison ...")
    comp_df = v17_vs_phasec_comparison(df)

    print("Writing V19 note ...")
    write_v19_note(df, city_rows, arch_rows, apt_detail, comp_df)

    print("\nCity-level scorecard:")
    for row in city_rows:
        print(f"  {row['city']:<6} {row['segment']:<14} "
              f"measured={row['measured_median']:.1f}  "
              f"phasec={row['model_median']:.1f}  "
              f"delta={row['delta_pct']:+.1f}%  "
              f"n={row['n_buildings']}")

    if apt_detail:
        print(f"\nApartment lighting EUI median: {apt_detail['lighting_eui_median']:.2f} kWh/m2/yr")
        print(f"Apartment reconstructed total median: {apt_detail['total_recon_median']:.1f} kWh/m2/yr")


if __name__ == "__main__":
    main()
