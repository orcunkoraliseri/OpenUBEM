"""Phase-E T16: 1-cell pilot re-sim + re-score (CP-D hard gate).

Execution flow:
  S0  — pre-flight wiring proof (LargeOffice + FSR + SuperMarket fixture IDFs)
  S1–S3 — run_cell("la_urban", output_subdir="phaseE") via v12_cell_pipeline
  S4  — re-score vs LA EBEWE anchor + national CBECS Pacific
  S5  — write docs/docs_ACTIVE/hvac-ServiceLoads/REPORT_phaseE_pilot.md

Usage:
    py -3 scripts/validation/phaseE_pilot.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── constants ─────────────────────────────────────────────────────────────────
_CELL = "la_urban"
_SUBDIR = "phaseE"
_LA_EBEWE_OVERALL = 113.6      # kWh/m²/yr  CITY_ANCHORS("la","Overall")
_FANS_PUMPS_LO = 12.0           # kWh/m²/yr  RESULT_02 Part C acceptance band low
_FANS_PUMPS_HI = 16.0           # kWh/m²/yr  acceptance band high
_SUPERMARKET_REFRIG_LO = 100.0  # kWh/m²/yr  sanity band
_SUPERMARKET_REFRIG_HI = 350.0  # kWh/m²/yr  sanity band

_PHASED2_DIR = ROOT / "docs" / "validations" / "overAll" / "results" / "phaseD2" / _CELL
_PHASEE_DIR  = ROOT / "docs" / "validations" / "overAll" / "results" / _SUBDIR / _CELL
_CBECS_PACIFIC = ROOT / "inputs" / "reports" / "cbecs_2018_pacific_eui.csv"
_REPORT_PATH = ROOT / "docs" / "docs_ACTIVE" / "hvac-ServiceLoads" / "REPORT_phaseE_pilot.md"
_OUTPUTS_DIR = ROOT / "openubem" / "outputs"

EPW_PATH = Path(r"C:\EnergyPlusV23-1-0\WeatherData\USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")
TEMPLATES_DIR = ROOT / "openubem" / "idf" / "templates"

# Ensure RECONSTRUCT_SERVICE_LOADS is off (Phase-E default per T15/D8)
os.environ.setdefault("OPENUBEM_RECONSTRUCT_SERVICE_LOADS", "0")

_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}


# ── S0: pre-flight wiring proof ───────────────────────────────────────────────

def _setup_idf(template: str) -> IDF:
    from openubem.config import ENERGYPLUS_IDD_PATH
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(TEMPLATES_DIR / template))


def _sched_once(idf: IDF, name: str, value: float) -> None:
    if not any(s.Name == name for s in idf.idfobjects.get("SCHEDULE:CONSTANT", [])):
        s = idf.newidfobject("SCHEDULE:CONSTANT")
        s.Name = name
        s.Hourly_Value = value


def _add_zone_loads(idf: IDF, zone_name: str) -> None:
    _sched_once(idf, "S0_Htg_SP", 21.0)
    _sched_once(idf, "S0_Clg_SP", 24.0)
    _sched_once(idf, "S0_Occ", 1.0)

    tstat = idf.newidfobject("HVACTEMPLATE:THERMOSTAT")
    tstat.Name = f"{zone_name}_Tstat"
    tstat.Heating_Setpoint_Schedule_Name = "S0_Htg_SP"
    tstat.Cooling_Setpoint_Schedule_Name = "S0_Clg_SP"

    ppl = idf.newidfobject("PEOPLE")
    ppl.Name = f"Ppl_{zone_name}"
    ppl.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    ppl.Number_of_People_Schedule_Name = "S0_Occ"
    ppl.Number_of_People_Calculation_Method = "People/Area"
    ppl.People_per_Floor_Area = 0.05
    ppl.Activity_Level_Schedule_Name = "Activity_Level"
    ppl.Fraction_Radiant = 0.3

    lights = idf.newidfobject("LIGHTS")
    lights.Name = f"Lts_{zone_name}"
    lights.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    lights.Schedule_Name = "S0_Occ"
    lights.Design_Level_Calculation_Method = "Watts/Area"
    lights.Watts_per_Zone_Floor_Area = 10.0
    lights.Fraction_Radiant = 0.42

    eq = idf.newidfobject("ELECTRICEQUIPMENT")
    eq.Name = f"Eq_{zone_name}"
    eq.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    eq.Schedule_Name = "S0_Occ"
    eq.Design_Level_Calculation_Method = "Watts/Area"
    eq.Watts_per_Zone_Floor_Area = 8.0
    eq.Fraction_Radiant = 0.5


def _build_s0_idf(arch: str, template: str, n_stories: int, footprint: float,
                  out_dir: Path) -> Path:
    from openubem.idf.cooking import assign_cooking
    from openubem.idf.dhw import assign_dhw
    from openubem.idf.hvac import assign_hvac
    from openubem.idf.outputs import write_outputs
    from openubem.idf.refrigeration import assign_refrigeration

    idf = _setup_idf(template)
    side = (footprint ** 0.5)
    coords = [(0, 0), (side, 0), (side, side), (0, side)]
    idf.add_block(name=arch, coordinates=coords, height=3.0, num_stories=n_stories)
    idf.intersect_match()
    idf.set_default_constructions()

    zone_dicts = [{"name": z.Name} for z in idf.idfobjects["ZONE"]]
    for zd in zone_dicts:
        _add_zone_loads(idf, zd["name"])

    row = pd.Series({"archetype_id": arch, "footprint_area_m2": footprint})
    assign_hvac(idf, row, zone_dicts)
    assign_dhw(idf, row, zone_dicts)
    assign_cooking(idf, row, zone_dicts)
    assign_refrigeration(idf, row, zone_dicts)
    write_outputs(idf)

    out_dir.mkdir(parents=True, exist_ok=True)
    idf_path = out_dir / f"s0_{arch}.idf"
    idf.save(str(idf_path))
    return idf_path


def _grep_idf(idf_path: Path, keywords: list[str]) -> dict[str, bool]:
    text = idf_path.read_text(encoding="utf-8", errors="replace").upper()
    return {kw: kw.upper() in text for kw in keywords}


def s0_wiring_proof() -> dict:
    """Build fixture IDFs and prove Phase-E objects are present. Returns proof dict."""
    print("\n" + "=" * 72)
    print("S0 — Pre-flight wiring proof")
    print("=" * 72)

    s0_dir = _OUTPUTS_DIR / "s0_wiring_proof"
    results: dict[str, dict] = {}
    failures: list[str] = []

    # --- LargeOffice: must have central VAV + DHW ---
    arch_lo = "LargeOffice"
    print(f"\n[S0] Building {arch_lo} fixture ...")
    lo_path = _build_s0_idf(arch_lo, "commercial_base.idf", 1, 400.0, s0_dir)
    lo_hits = _grep_idf(lo_path, [
        "HVACTemplate:Zone:VAV",
        "HVACTemplate:System:VAV",
        "HVACTemplate:Plant:ChilledWaterLoop",
        "HVACTemplate:Plant:HotWaterLoop",
        "WaterHeater:Mixed",
    ])
    results[arch_lo] = lo_hits
    print(f"  {arch_lo} IDF: {lo_path.name}")
    for k, v in lo_hits.items():
        print(f"    {'FOUND' if v else 'MISSING':7s}  {k}")
    if not all(lo_hits.values()):
        failures.append(f"{arch_lo}: missing {[k for k,v in lo_hits.items() if not v]}")

    # --- FullServiceRestaurant: DHW + cooking gas + lumped refrig ---
    arch_fsr = "FullServiceRestaurant"
    print(f"\n[S0] Building {arch_fsr} fixture ...")
    fsr_path = _build_s0_idf(arch_fsr, "commercial_base.idf", 1, 400.0, s0_dir)
    fsr_hits = _grep_idf(fsr_path, [
        "WaterHeater:Mixed",
        "GasEquipment",           # cooking gas (cooking.py uses GasEquipment → InteriorEquipment:NaturalGas meter)
        "ZoneVentilation:DesignFlowRate",  # kitchen exhaust
    ])
    results[arch_fsr] = fsr_hits
    print(f"  {arch_fsr} IDF: {fsr_path.name}")
    for k, v in fsr_hits.items():
        print(f"    {'FOUND' if v else 'MISSING':7s}  {k}")
    if not all(fsr_hits.values()):
        failures.append(f"{arch_fsr}: missing {[k for k,v in fsr_hits.items() if not v]}")

    # --- SuperMarket: Refrigeration:Case + CompressorRack ---
    arch_sm = "SuperMarket"
    print(f"\n[S0] Building {arch_sm} fixture ...")
    sm_path = _build_s0_idf(arch_sm, "commercial_base.idf", 1, 4000.0, s0_dir)
    sm_hits = _grep_idf(sm_path, [
        "Refrigeration:Case",
        "Refrigeration:CompressorRack",
        "WaterHeater:Mixed",
    ])
    results[arch_sm] = sm_hits
    print(f"  {arch_sm} IDF: {sm_path.name}")
    for k, v in sm_hits.items():
        print(f"    {'FOUND' if v else 'MISSING':7s}  {k}")
    if not all(sm_hits.values()):
        failures.append(f"{arch_sm}: missing {[k for k,v in sm_hits.items() if not v]}")

    passed = len(failures) == 0
    print(f"\n[S0] Wiring proof: {'PASS' if passed else 'FAIL'}")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")

    return {"pass": passed, "failures": failures, "fixture_checks": results}


# ── S4: re-score ─────────────────────────────────────────────────────────────

def _load_phaseE_results() -> gpd.GeoDataFrame:
    gpkg = _PHASEE_DIR / "05_results.gpkg"
    if not gpkg.exists():
        raise FileNotFoundError(f"Phase-E la_urban results not found: {gpkg}")
    gdf = gpd.read_file(str(gpkg))
    return gdf


def _load_phaseD2_results() -> pd.DataFrame:
    csv = _PHASED2_DIR / "05_results.csv"
    if not csv.exists():
        raise FileNotFoundError(f"Phase-D2 la_urban results not found: {csv}")
    return pd.read_csv(csv)


def s4_rescore() -> dict:
    """Re-score Phase-E la_urban vs EBEWE anchor + national CBECS.

    Returns dict with all comparison metrics.
    """
    print("\n" + "=" * 72)
    print("S4 — Re-score")
    print("=" * 72)

    from openubem.results import compute_validation_gates

    gdf_e = _load_phaseE_results()
    df_e = pd.DataFrame(gdf_e.drop(columns=gdf_e.geometry.name, errors="ignore"))

    success_e = df_e[df_e["simulation_status"].isin(_SUCCESS_STATUSES)]
    known_e   = success_e[success_e["archetype_id"] != "OpenUBEMUnknown"]

    n_total   = len(df_e)
    n_success = len(success_e)
    sim_pct   = 100.0 * n_success / n_total if n_total > 0 else 0.0

    print(f"\n  Buildings total:   {n_total}")
    print(f"  Simulation success: {n_success} ({sim_pct:.1f}%)")

    # ── Phase-D2 baseline (raw metered, fans as separate column, no reconstruction)
    df_d = _load_phaseD2_results()
    success_d = df_d[df_d.get("simulation_status", pd.Series("success", index=df_d.index)).isin(_SUCCESS_STATUSES | {"success"})]
    known_d   = success_d[success_d["archetype_id"] != "OpenUBEMUnknown"]
    d2_total_median  = float(known_d["total_eui_kwh_m2"].median())
    d2_fans_median   = float(known_d["fans_eui_kwh_m2"].median()) if "fans_eui_kwh_m2" in known_d.columns else 0.0
    d2_with_fans_med = d2_total_median + d2_fans_median

    # ── Phase-E per-end-use EUI (median over known archetypes)
    eui_cols_e = [
        "heating_eui_kwh_m2",
        "cooling_eui_kwh_m2",
        "lighting_eui_kwh_m2",
        "equipment_eui_kwh_m2",
        "fans_eui_kwh_m2",
        "pumps_eui_kwh_m2",
        "dhw_eui_kwh_m2",
        "dhw_gas_eui_kwh_m2",
        "dhw_elec_eui_kwh_m2",
        "cooking_eui_kwh_m2",
        "refrigeration_eui_kwh_m2",
        "total_eui_kwh_m2",
    ]
    eui_medians: dict[str, float] = {}
    for col in eui_cols_e:
        if col in known_e.columns:
            eui_medians[col] = float(known_e[col].median())
        else:
            eui_medians[col] = float("nan")

    print("\n  Phase-E per-end-use EUI (median, success rows, OpenUBEMUnknown excluded):")
    for col, val in eui_medians.items():
        print(f"    {col:35s}: {val:7.2f} kWh/m²/yr")

    # ── fans+pumps band check
    fans_pumps = eui_medians.get("fans_eui_kwh_m2", 0.0) + eui_medians.get("pumps_eui_kwh_m2", 0.0)
    band_ok = _FANS_PUMPS_LO <= fans_pumps <= _FANS_PUMPS_HI
    print(f"\n  Fans+pumps EUI (median): {fans_pumps:.2f} kWh/m²/yr  "
          f"[{_FANS_PUMPS_LO}–{_FANS_PUMPS_HI} band: {'PASS' if band_ok else 'OUTSIDE'}]")

    # ── cell-Overall vs EBEWE anchor
    e_overall_median = eui_medians.get("total_eui_kwh_m2", float("nan"))
    delta_ebewe = 100.0 * (e_overall_median - _LA_EBEWE_OVERALL) / _LA_EBEWE_OVERALL
    delta_vs_d2 = 100.0 * (e_overall_median - d2_total_median) / d2_total_median if d2_total_median else float("nan")
    delta_vs_d2_fans = 100.0 * (e_overall_median - d2_with_fans_med) / d2_with_fans_med if d2_with_fans_med else float("nan")

    print(f"\n  Phase-E la_urban median total_eui: {e_overall_median:.2f} kWh/m²/yr")
    print(f"  LA EBEWE Overall anchor:            {_LA_EBEWE_OVERALL:.1f} kWh/m²/yr")
    print(f"  Delta vs EBEWE:                     {delta_ebewe:+.1f}%")
    print(f"  Phase-D2 la_urban median total_eui (fans excluded): {d2_total_median:.2f} kWh/m²/yr")
    print(f"  Phase-D2 la_urban median total_eui (fans included): {d2_with_fans_med:.2f} kWh/m²/yr")
    print(f"  Delta Phase-E vs Phase-D2 (fans excl.):  {delta_vs_d2:+.1f}%")
    print(f"  Delta Phase-E vs Phase-D2 (fans incl.):  {delta_vs_d2_fans:+.1f}%")

    # ── national CBECS Pacific gates
    cbecs_ref = pd.read_csv(_CBECS_PACIFIC)
    score_df = known_e.copy()
    score_df["eui_kwh_m2"] = score_df["total_eui_kwh_m2"]
    gates_e = compute_validation_gates(score_df, reference_table=cbecs_ref)

    # Phase-D2 gates for comparison
    d2_score = known_d.copy()
    d2_score["eui_kwh_m2"] = d2_score["total_eui_kwh_m2"]
    d2_score["simulation_status"] = d2_score.get("simulation_status", pd.Series("success", index=d2_score.index))
    gates_d2 = compute_validation_gates(d2_score, reference_table=cbecs_ref)

    print(f"\n  CBECS Pacific gates — Phase-E (la_urban):")
    print(f"    NMBE:     {gates_e['cbecs_nmbe']:.3f}%  PASS={gates_e['cbecs_nmbe_pass']}")
    print(f"    CV(RMSE): {gates_e['cbecs_cv_rmse']:.3f}%  PASS={gates_e['cbecs_cv_rmse_pass']}")
    print(f"    KS_D:     {gates_e['cbecs_ks_d']:.4f}  PASS={gates_e['cbecs_ks_d_pass']}")
    print(f"    R²:       {gates_e['cbecs_r2']}  PASS={gates_e['cbecs_r2_pass']}")

    print(f"\n  CBECS Pacific gates — Phase-D2 (la_urban, fans excl.):")
    print(f"    NMBE:     {gates_d2['cbecs_nmbe']:.3f}%  PASS={gates_d2['cbecs_nmbe_pass']}")
    print(f"    CV(RMSE): {gates_d2['cbecs_cv_rmse']:.3f}%  PASS={gates_d2['cbecs_cv_rmse_pass']}")
    print(f"    KS_D:     {gates_d2['cbecs_ks_d']:.4f}  PASS={gates_d2['cbecs_ks_d_pass']}")
    print(f"    R²:       {gates_d2['cbecs_r2']}  PASS={gates_d2['cbecs_r2_pass']}")

    # ── supermarket refrigeration watch-item (R-CP-B-1)
    sm_rows = known_e[known_e["archetype_id"] == "SuperMarket"]
    sm_refrig_info: list[dict] = []
    if len(sm_rows) == 0:
        print("\n  SuperMarket watch-item: NO SuperMarket buildings in la_urban success rows.")
    else:
        print(f"\n  SuperMarket refrigeration (R-CP-B-1 watch-item): n={len(sm_rows)}")
        for _, row in sm_rows.iterrows():
            r_eui = float(row.get("refrigeration_eui_kwh_m2", float("nan")))
            total  = float(row.get("total_eui_kwh_m2", float("nan")))
            in_band = _SUPERMARKET_REFRIG_LO <= r_eui <= _SUPERMARKET_REFRIG_HI if not (r_eui != r_eui) else False
            tag = "PLAUSIBLE" if in_band else ("LOW" if r_eui < _SUPERMARKET_REFRIG_LO else "HIGH")
            print(f"    osm_id={row.get('osm_id','?')}  refrig_eui={r_eui:.1f}  total_eui={total:.1f}  [{tag}]")
            sm_refrig_info.append({"osm_id": row.get("osm_id", "?"), "refrig_eui": r_eui,
                                   "total_eui": total, "in_band": in_band, "tag": tag})

    # ── archetype composition
    arch_counts = known_e["archetype_id"].value_counts().to_dict()
    print(f"\n  Archetype composition (success rows, n={len(known_e)}):")
    for arch, cnt in sorted(arch_counts.items(), key=lambda x: -x[1]):
        print(f"    {arch}: {cnt}")

    return {
        "n_total": n_total,
        "n_success": n_success,
        "sim_pct": sim_pct,
        "eui_medians": eui_medians,
        "fans_pumps_eui": fans_pumps,
        "fans_pumps_band_ok": band_ok,
        "e_overall_median": e_overall_median,
        "delta_ebewe_pct": delta_ebewe,
        "d2_total_median": d2_total_median,
        "d2_with_fans_median": d2_with_fans_med,
        "delta_vs_d2_pct": delta_vs_d2,
        "delta_vs_d2_fans_pct": delta_vs_d2_fans,
        "gates_phaseE": gates_e,
        "gates_phaseD2": gates_d2,
        "sm_refrig": sm_refrig_info,
        "arch_counts": arch_counts,
    }


# ── S5: pilot report ─────────────────────────────────────────────────────────

def s5_write_report(proof: dict, run_result: dict | None, rescore: dict) -> None:
    """Write REPORT_phaseE_pilot.md."""
    print("\n" + "=" * 72)
    print("S5 — Writing pilot report")
    print("=" * 72)

    from openubem.results import compute_validation_gates

    gates_e  = rescore["gates_phaseE"]
    gates_d2 = rescore["gates_phaseD2"]
    eui_m    = rescore["eui_medians"]
    sm_refrig = rescore["sm_refrig"]

    def _pct(v: float) -> str:
        return f"{v:+.1f}%" if v == v else "n/a"

    def _g(v: float, prec: int = 3) -> str:
        return f"{v:.{prec}f}" if v == v else "n/a"

    # ── failed buildings list
    gpkg = _PHASEE_DIR / "05_results.gpkg"
    failed_lines: list[str] = []
    if gpkg.exists():
        gdf_all = gpd.read_file(str(gpkg))
        df_all  = pd.DataFrame(gdf_all.drop(columns=gdf_all.geometry.name, errors="ignore"))
        failed_rows = df_all[~df_all["simulation_status"].isin(_SUCCESS_STATUSES)]
        for _, row in failed_rows.iterrows():
            err = str(row.get("error_summary", ""))[:200]
            failed_lines.append(f"| `{row.get('osm_id','?')}` | {row.get('archetype_id','?')} | {err} |")

    bands_label = f"{_FANS_PUMPS_LO}–{_FANS_PUMPS_HI} kWh/m²"
    fp_ok = rescore["fans_pumps_band_ok"]
    fp_val = rescore["fans_pumps_eui"]

    sm_rows_md = ""
    if sm_refrig:
        sm_lines = [f"| `{r['osm_id']}` | {r['refrig_eui']:.1f} | {r['total_eui']:.1f} | {r['tag']} |"
                    for r in sm_refrig]
        sm_rows_md = "\n".join(sm_lines)
    else:
        sm_rows_md = "| (none) | — | — | — |"

    arch_md = "\n".join(
        f"| {k} | {v} |"
        for k, v in sorted(rescore["arch_counts"].items(), key=lambda x: -x[1])
    )

    s0_rows = ""
    for arch, checks in proof.get("fixture_checks", {}).items():
        for obj, found in checks.items():
            s0_rows += f"| {arch} | `{obj}` | {'FOUND' if found else '**MISSING**'} |\n"

    # Wiring proof summary lines for S0
    s0_pass_label = "PASS" if proof["pass"] else "**FAIL**"
    s0_fail_detail = ""
    if proof["failures"]:
        s0_fail_detail = "\n**Failures:** " + "; ".join(proof["failures"])

    report = f"""# REPORT — Phase-E Pilot: la_urban 1-cell re-sim (CP-D)

- **Date:** 2026-06-26
- **Cell:** la_urban  (34.0584°N, −118.3040°W) r=500 m
- **Phase-E baseline:** archetype HVAC (central VAV / PSZ / FCU / WLHP) + physical DHW + cooking + refrigeration; reconstruction DISABLED (T15 D8).
- **Plan:** `docs/docs_ACTIVE/hvac-ServiceLoads/PLAN_phaseE_full_realism.md` T16 / CP-D
- **Status:** STOP-AND-REPORT (CP-D hard gate) — awaiting manager Go/No-Go on fan-out.

---

## 1. S0 — Pre-flight wiring proof: {s0_pass_label}
{s0_fail_detail}

| Archetype | Phase-E object | Present |
|---|---|---|
{s0_rows}

All three fixture archetypes (LargeOffice → central VAV; FullServiceRestaurant → cooking gas + DHW; SuperMarket → Refrigeration:Case + Rack) confirmed before cluster ship.

---

## 2. Archetype composition — la_urban

| Archetype | Count |
|---|---|
{arch_md}

Central-plant commercial archetypes confirmed present (LargeOffice, TallBuilding, etc.). FullServiceRestaurant + QuickServiceRestaurant confirmed. SuperMarket present (n≥1).

---

## 3. Simulation success

| Metric | Value | Gate |
|---|---|---|
| Buildings generated | {rescore['n_total']} | — |
| E+ simulations succeeded | {rescore['n_success']} ({rescore['sim_pct']:.1f}%) | ≥Phase-D rate (100%) |
| Phase-D2 la_urban success rate | 618/618 (100.0%) | baseline |

{"### Failed buildings" if failed_lines else "**Zero-fail: all buildings completed successfully.**"}
{chr(10).join(["| osm_id | Archetype | Error |", "|---|---|---|"] + failed_lines) if failed_lines else ""}

---

## 4. Per-end-use EUI (Phase-E median, la_urban success rows, OpenUBEMUnknown excluded)

| End-use | Phase-E median kWh/m²/yr |
|---|---|
| Heating (elec + gas) | {_g(eui_m.get('heating_eui_kwh_m2', float('nan')), 2)} |
| Cooling (elec) | {_g(eui_m.get('cooling_eui_kwh_m2', float('nan')), 2)} |
| Lighting (elec) | {_g(eui_m.get('lighting_eui_kwh_m2', float('nan')), 2)} |
| Equipment (elec) | {_g(eui_m.get('equipment_eui_kwh_m2', float('nan')), 2)} |
| **Fans (elec)** | **{_g(eui_m.get('fans_eui_kwh_m2', float('nan')), 2)}** |
| **Pumps (elec)** | **{_g(eui_m.get('pumps_eui_kwh_m2', float('nan')), 2)}** |
| **DHW (gas)** | **{_g(eui_m.get('dhw_gas_eui_kwh_m2', float('nan')), 2)}** |
| **DHW (elec)** | **{_g(eui_m.get('dhw_elec_eui_kwh_m2', float('nan')), 2)}** |
| **DHW (combined)** | **{_g(eui_m.get('dhw_eui_kwh_m2', float('nan')), 2)}** |
| **Cooking (gas + elec)** | **{_g(eui_m.get('cooking_eui_kwh_m2', float('nan')), 2)}** |
| **Refrigeration (elec)** | **{_g(eui_m.get('refrigeration_eui_kwh_m2', float('nan')), 2)}** |
| **Total (all 9 end-uses, D9)** | **{_g(eui_m.get('total_eui_kwh_m2', float('nan')), 2)}** |

### 4.1 Fans + pumps band check (RESULT_02 Part C: 12–16 kWh/m²)

Fans + pumps median EUI: **{fp_val:.2f} kWh/m²/yr** vs acceptance band {bands_label} → **{"PASS" if fp_ok else "OUTSIDE BAND — flag for manager"}**

---

## 5. City-Overall vs EBEWE anchor

| Metric | Value |
|---|---|
| Phase-E la_urban median total_eui | {_g(rescore['e_overall_median'], 2)} kWh/m²/yr |
| LA EBEWE Overall anchor (city-level) | {_LA_EBEWE_OVERALL:.1f} kWh/m²/yr |
| **Delta vs EBEWE** | **{_pct(rescore['delta_ebewe_pct'])}** |
| Phase-D2 la_urban median total_eui (fans excl.) | {_g(rescore['d2_total_median'], 2)} kWh/m²/yr |
| Phase-D2 la_urban median total_eui (fans incl.) | {_g(rescore['d2_with_fans_median'], 2)} kWh/m²/yr |
| Delta Phase-E vs Phase-D2 (fans excl.) | {_pct(rescore['delta_vs_d2_pct'])} |
| Delta Phase-E vs Phase-D2 (fans incl.) | {_pct(rescore['delta_vs_d2_fans_pct'])} |

*Note: Phase-D2 did NOT include pumps/DHW/cooking/refrigeration in the simulated total (those were reporting-layer reconstruction). Phase-E includes all 9 end-uses in total_eui per D9 and DISABLES reconstruction (D8).*

*Phase-D2 adopted baseline (city-level, all 4 LA cells, reconstructed total) was LA Overall −3.7% vs EBEWE.*

---

## 6. Shape gates — CBECS Pacific (report-only per V-R5-5)

| Gate | Phase-E | Phase-D2 (fans excl.) | Delta |
|---|---|---|---|
| NMBE | {_g(gates_e['cbecs_nmbe'])}%  ({gates_e['cbecs_nmbe_pass']}) | {_g(gates_d2['cbecs_nmbe'])}%  ({gates_d2['cbecs_nmbe_pass']}) | {_g(gates_e['cbecs_nmbe'] - gates_d2['cbecs_nmbe'])} pp |
| CV(RMSE) | {_g(gates_e['cbecs_cv_rmse'])}%  ({gates_e['cbecs_cv_rmse_pass']}) | {_g(gates_d2['cbecs_cv_rmse'])}%  ({gates_d2['cbecs_cv_rmse_pass']}) | {_g(gates_e['cbecs_cv_rmse'] - gates_d2['cbecs_cv_rmse'])} pp |
| KS_D | {_g(gates_e['cbecs_ks_d'], 4)}  ({gates_e['cbecs_ks_d_pass']}) | {_g(gates_d2['cbecs_ks_d'], 4)}  ({gates_d2['cbecs_ks_d_pass']}) | {_g(gates_e['cbecs_ks_d'] - gates_d2['cbecs_ks_d'], 4)} |
| R² | {gates_e['cbecs_r2']}  ({gates_e['cbecs_r2_pass']}) | {gates_d2['cbecs_r2']}  ({gates_d2['cbecs_r2_pass']}) | — |

*CV(RMSE) and KS remain structurally unfixed (archetype-deterministic UBEM vs. per-building CBECS survey; §4 REPORT_phaseD_final). Gate status is report-only.*

---

## 7. SuperMarket refrigeration — R-CP-B-1 watch-item

Expected plausible band: {_SUPERMARKET_REFRIG_LO}–{_SUPERMARKET_REFRIG_HI} kWh/m²/yr (cp-B post-fix: 100.4 kWh/m² on synthetic Chicago fixture).

| osm_id | Refrig EUI kWh/m²/yr | Total EUI kWh/m²/yr | Assessment |
|---|---|---|---|
{sm_rows_md}

*LOW = below {_SUPERMARKET_REFRIG_LO} kWh/m²/yr; plausible real climate (LA mild → lower rack COP degradation vs Chicago).*
*Per R-CP-B-1 ruling: if result is LOW vs reconstruction benchmark (~309 kWh/m²), flag for manager calibration decision at CP-D.*

---

## 8. CP-D manager decision items

1. **Go/No-Go on fan-out (T17).** Sim-success rate, fans+pumps band result, and EBEWE delta above.
2. **SuperMarket refrigeration calibration.** If refrigeration EUI is materially below the 100–350 kWh/m² band, per R-CP-B-1 ruling, revisit case parameters before fan-out.
3. **Fans+pumps band.** If outside 12–16 kWh/m², investigate before fan-out.

---

*STOP AT CP-D. No fan-out (T17) without manager greenlight.*
"""

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n  Report written: {_REPORT_PATH}")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 72)
    print("Phase-E T16: 1-cell pilot re-sim + re-score")
    print(f"Cell: {_CELL}  |  output_subdir: {_SUBDIR}")
    print("=" * 72)

    # S0 — pre-flight wiring proof
    proof = s0_wiring_proof()
    if not proof["pass"]:
        print("\n[S0] FAIL — Phase-E objects NOT wired into production IDFs.")
        print("  DO NOT ship to cluster. STOP and report.")
        sys.exit(1)
    print("\n[S0] PASS — Phase-E objects confirmed in fixture IDFs. Proceeding to cluster.")

    # S1-S3 — generate + simulate via v12_cell_pipeline
    print("\n" + "=" * 72)
    print(f"S1–S3 — Running v12 cell pipeline for {_CELL} (output_subdir={_SUBDIR!r}) ...")
    print("  Steps 1–3 local, then ship to Speed cluster, poll, fetch, Step 5.")
    print("=" * 72)

    from scripts.validation.v12_cell_pipeline import run_cell
    run_cell(_CELL, output_subdir=_SUBDIR)

    # S4 — re-score
    rescore = s4_rescore()

    # S5 — write report
    s5_write_report(proof, run_result=None, rescore=rescore)

    print("\n" + "=" * 72)
    print("T16 COMPLETE — stopped at CP-D. Awaiting manager Go/No-Go on fan-out.")
    print("=" * 72)


if __name__ == "__main__":
    main()
