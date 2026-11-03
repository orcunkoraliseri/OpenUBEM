"""LayoutAssigner: Analysis and comparison script.

Reads baseline cell resolution summary (t08_mode_cell_summary.csv), calculates baseline
archetype area scaling factors using the canonical layout_assigner registry, parses real
prototype zone counts via parse_baseline_zones(), generates the comparison matrix CSV, and
(optionally) refreshes the results markdown report.
"""

import argparse
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import numpy as np

from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.geometry import layout_assigner

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

# Path definitions
WORKSPACE_ROOT = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
SUMMARY_CSV_PATH = WORKSPACE_ROOT / "openubem" / "outputs" / "comparisons" / "t08_mode_cell_summary.csv"
OUTPUT_DIR = WORKSPACE_ROOT / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner"
OUTPUT_CSV_PATH = OUTPUT_DIR / "layout_assign_vs_resolution_modes.csv"
OUTPUT_MD_PATH = OUTPUT_DIR / "OpenUBEM_results_LayoutAssigner.md"
COMPARISON_OUT_CSV = WORKSPACE_ROOT / "openubem" / "outputs" / "comparisons" / "layout_assign_vs_resolution_modes.csv"

# Illustrative sample target floor areas (m2) per canonical archetype -- these are
# example real-building sizes used to demonstrate scaling, not measured data (same
# status as the pre-existing dict this replaces). Extended to cover every archetype
# in layout_assigner.ARCHETYPE_IDF_MAP (T10, plan §5).
sample_target_areas: Dict[str, float] = {
    "MidriseApartment": 2500.0,
    "HighriseApartment": 9000.0,
    "Hospital": 25000.0,
    "LargeHotel": 12500.0,
    "SmallHotel": 3500.0,
    "LargeOffice": 50000.0,
    "LargeOfficeDetailed": 50000.0,
    "MediumOffice": 4500.0,
    "MediumOfficeDetailed": 4500.0,
    "SmallOffice": 600.0,
    "SmallOfficeDetailed": 600.0,
    "Outpatient": 4200.0,
    "PrimarySchool": 7500.0,
    "SecondarySchool": 21000.0,
    "College": 12000.0,
    "Laboratory": 9000.0,
    "RetailStandalone": 2000.0,
    "RetailStripmall": 1800.0,
    "SuperMarket": 4500.0,
    "Warehouse": 5000.0,
    "FullServiceRestaurant": 550.0,
    "QuickServiceRestaurant": 250.0,
    "TallBuilding": 28000.0,
    "SuperTallBuilding": 65000.0,
    "LargeDataCenterHighITE": 600.0,
    "LargeDataCenterLowITE": 600.0,
    "SmallDataCenterHighITE": 60.0,
    "SmallDataCenterLowITE": 60.0,
}

# Illustrative floor-count hints, used only to fill in the building/floor/fast_zone
# "if you used another resolution mode" comparison columns below -- NOT derived from
# the real prototype IDFs (those come from parse_baseline_zones() instead, see
# _real_prototype_zone_count()).
_ARCHETYPE_FLOORS_HINT: Dict[str, int] = {
    "MidriseApartment": 4,
    "HighriseApartment": 10,
    "Hospital": 5,
    "LargeHotel": 6,
    "SmallHotel": 4,
    "LargeOffice": 12,
    "LargeOfficeDetailed": 12,
    "MediumOffice": 3,
    "MediumOfficeDetailed": 3,
    "SmallOffice": 1,
    "SmallOfficeDetailed": 1,
    "Outpatient": 3,
    "PrimarySchool": 1,
    "SecondarySchool": 2,
    "College": 4,
    "Laboratory": 3,
    "TallBuilding": 40,
    "SuperTallBuilding": 80,
}

_ZONE_COUNT_CACHE: Dict[str, int] = {}

# T12 local leg (2026-07-22, real data -- NOT illustrative like sample_target_areas above):
# one real EnergyPlus 23.1 annual run per archetype, LA TMYx EPW (same weather as the T09
# LIVE_SMOKE), harvested via the identical D9 9-end-use total_eui_kwh_m2 formula every other
# resolution mode uses (parser.py's parse_building_sql + _parse_meters_sql + _compute_eui,
# called directly rather than through parse_building() -- see plan §8 T12 progress-log entry
# and §9 E-LA-05 for why: parse_building()'s _check_zone_integrity() gate assumes the OpenUBEM
# '{osm_id}_F{floor}_{label}' zone-naming convention, which layout_assign zones never carry
# (they keep the DOE baseline's own native zone names) -- a real, structural gap affecting
# every layout_assign building, not specific to this sample). Archetypes not in this dict were
# not run in the local leg (left blank/'--' in the §2 table, per plan §5 T12 Step 5 instruction
# to never extrapolate). Scale factors: MidriseApartment S=4.78 (identical to T09's fixture),
# MediumOffice S=1.60, SmallHotel S=1.87, SecondarySchool S=0.51, RetailStandalone S=0.65,
# FullServiceRestaurant S=0.78 -- a deliberate up/down mix, none at trivial S=1.0 identity.
LOCAL_LEG_TOTAL_EUI_KWH_M2: Dict[str, float] = {
    "MidriseApartment": 60.07,
    "MediumOffice": 72.48,
    "SmallHotel": 151.46,
    "SecondarySchool": 67.18,
    "RetailStandalone": 101.20,
    "FullServiceRestaurant": 886.08,
}

# Archetypes whose local-leg run completed ("EnergyPlus Completed Successfully", no Fatal,
# real total_eui_kwh_m2 above) but which threw large recurring-warning/severe-error counts
# tied to fixed-capacity equipment (electrical transformer, DHW tank, multi-speed DX coil
# rated flow/capacity ratios) that scale_baseline_idf() does not scale (out of its T04 scope:
# only geometry vertices + explicitly-listed absolute load/OA/DHW-draw fields scale; transformer
# and water-heater-tank capacity, and HVAC coil/fan rated capacity, are untouched). Only
# MidriseApartment (S=4.78, the pre-existing T09-validated case) stayed clean (43 warnings,
# 0 severe). See plan §9 E-LA-06 (OPEN) -- flagged, not silently smoothed over; the EUI values
# above are still real EnergyPlus output and within config.EUI_PLAUSIBILITY_BOUNDS, but their
# absolute reliability at non-identity scale factors carries this caveat.
LOCAL_LEG_CAVEAT_ARCHETYPES = {
    "MediumOffice": "73,803 real Severe Errors (ElectricLoadCenter:Transformer overloaded) + a DHW target-water-temperature warning storm",
    "SmallHotel": "120.5M recurring warnings (Coil:Cooling:DX:MultiSpeed rated flow/capacity ratio out of range)",
    "SecondarySchool": "15.8M recurring warnings (HeatExchanger:AirToAir flow ratio out of range) + 28 Severe Errors",
    "RetailStandalone": "604K recurring warnings (AirLoopHVAC:UnitarySystem part-load ratio out of range)",
    "FullServiceRestaurant": "1.1M recurring warnings (AirLoopHVAC:UnitarySystem part-load ratio + DHW target-temperature)",
}


def _real_prototype_zone_count(archetype_id: str) -> Optional[int]:
    """Real zone count for archetype_id's baseline IDF via parse_baseline_zones().

    Loads the transitioned baseline IDF from config.BASELINE_IDF_DIR through the
    canonical registry (layout_assigner.get_registry()) and returns the live-parsed
    zone count -- never a guessed formula (plan §5 T10). Returns None if no baseline
    file resolves (should not happen for anything in ARCHETYPE_IDF_MAP once the
    transitioned library is present; handled gracefully rather than crashing).
    Results are cached per baseline filename since several canonical archetypes
    (the *Detailed variants) share the same underlying IDF.
    """
    reg = layout_assigner.get_registry()
    path = reg.get_baseline_idf(archetype_id)
    if path is None:
        return None
    key = str(path)
    if key not in _ZONE_COUNT_CACHE:
        idf = GeomIDF(str(path))
        zones = layout_assigner.parse_baseline_zones(idf, archetype_id)
        _ZONE_COUNT_CACHE[key] = len(zones)
    return _ZONE_COUNT_CACHE[key]


def run_analysis(write_md: bool = False):
    print(f"Loading resolution cell summary from: {SUMMARY_CSV_PATH}")
    df_cell = pd.read_csv(SUMMARY_CSV_PATH, header=[0, 1])

    # Flatten column multiindex properly
    cols = []
    for col in df_cell.columns:
        if col[1] and str(col[1]).strip() and not str(col[1]).startswith("Unnamed"):
            cols.append(f"{col[0]}_{col[1]}")
        else:
            cols.append(col[0])
    df_cell.columns = cols

    print("Synthesizing LayoutAssigner archetype resolution matrix (real parse_baseline_zones() counts)...")

    comparison_rows = []

    # Build comparison rows for each canonical archetype mapped to a real baseline IDF
    # (openubem.geometry.layout_assigner.ARCHETYPE_IDF_MAP / DEFAULT_BASELINE_AREAS is
    # the single source of truth, plan §5 T10 -- replaces this script's own now-stale
    # BASELINE_IDF_REGISTRY dict and its informal, vocab-misaligned archetype keys).
    for arch, filename in layout_assigner.ARCHETYPE_IDF_MAP.items():
        baseline_area = layout_assigner.DEFAULT_BASELINE_AREAS.get(arch)
        if baseline_area is None:
            continue  # should never happen: T02 guarantees every mapped archetype has an area

        target_area = sample_target_areas.get(arch, baseline_area)
        scale_ratio = target_area / baseline_area
        planar_scale = np.sqrt(scale_ratio) if scale_ratio > 0 else 1.0

        num_zones = _real_prototype_zone_count(arch)
        floors_hint = _ARCHETYPE_FLOORS_HINT.get(arch, 1)
        local_leg_eui = LOCAL_LEG_TOTAL_EUI_KWH_M2.get(arch)

        comparison_rows.append({
            "archetype_id": arch,
            "baseline_idf": filename,
            "baseline_area_m2": baseline_area,
            "target_sample_area_m2": target_area,
            "area_scale_ratio": round(scale_ratio, 4),
            "planar_scale_factor": round(planar_scale, 4),
            "prototype_zones_count": num_zones if num_zones is not None else "N/A",
            "building_mode_zones": 1,
            "floor_mode_zones": floors_hint,
            "fast_zone_mode_zones": floors_hint * 5,
            "layout_assign_mode_zones": num_zones if num_zones is not None else "N/A",
            "fidelity_ranking": "Highest (Exact ASHRAE Prototype Zoning)",
            "local_leg_total_eui_kwh_m2": local_leg_eui if local_leg_eui is not None else "",
            "local_leg_caveat": LOCAL_LEG_CAVEAT_ARCHETYPES.get(arch, ""),
        })

    df_comp = pd.DataFrame(comparison_rows)

    # Always write the openubem/outputs/comparisons CSV -- this is the flat, visible
    # artifact location the project convention prefers, and is safe to regenerate
    # every run (plan §5 T10c).
    COMPARISON_OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_comp.to_csv(COMPARISON_OUT_CSV, index=False)
    print(f"Saved comparison CSV to: {COMPARISON_OUT_CSV}")

    if write_md:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df_comp.to_csv(OUTPUT_CSV_PATH, index=False)
        print(f"Saved comparison CSV (docs copy) to: {OUTPUT_CSV_PATH}")
    else:
        print(f"--write-md not set: skipping docs-dir CSV copy at: {OUTPUT_CSV_PATH}")

    # Generate Markdown Summary (gated by --write-md, plan §5 T10c)
    generate_markdown_report(df_comp, df_cell, write_md=write_md)


def generate_markdown_report(df_comp: pd.DataFrame, df_cell: pd.DataFrame, write_md: bool = False):
    cell_pivot = df_cell[["cell", "city", "mode", "total_eui_median"]].pivot(index=["cell", "city"], columns="mode", values="total_eui_median").reset_index()

    md_content = f"""# OpenUBEM — LayoutAssigner Simulation Resolution Results

**What this document is:** A comprehensive evaluation report for the **`layoutAssigner`** resolution mode strategy. It compares standard DOE/ASHRAE 90.1 baseline archetype assignment and scaling against the established OpenUBEM resolution modes (`auto`, `building`, `floor`, `fast_zone`).

---

## 1. Strategy Overview: `layoutAssigner`

The `layoutAssigner` strategy substitutes custom on-the-fly room-level geometry generation (`layoutgenerator`) with **pre-validated, standardized EnergyPlus prototype models** from:
`{config.BASELINE_IDF_DIR}`

### Key Highlights
- **100% Thermal Zoning Fidelity**: Preserves full ASHRAE 90.1 prototype internal multi-zone layouts, room functions, and HVAC loop topologies.
- **Robust Area Scaling**: Scales gross floor area ($S = \\text{{Area}}_{{\\text{{real}}}} / \\text{{Area}}_{{\\text{{baseline}}}}$) and planar coordinates ($\\sqrt{{S}}$) while conserving internal load intensities ($W/m^2$).
- **Eliminates Topology Errors**: Especially beneficial for complex programs (**Hospitals**, **Large Hotels**, **Outpatient Healthcare**) where polygon splitting creates non-convex zones or boundary surface errors.

---

## 2. Archetype Layout Assignment & Scaling Matrix

Prototype zone counts are **real, live-parsed** via `layout_assigner.parse_baseline_zones()` against the E+ 23.1-transitioned baseline library (plan §5 T10) -- not a guessed formula. The **Local Sim Total EUI** column (T12 local leg, 2026-07-22) is a **real, single-building EnergyPlus 23.1 annual simulation** per archetype (LA TMYx EPW), harvested via the identical D9 9-end-use `total_eui_kwh_m2` formula every other resolution mode uses -- populated only for the 6 archetypes actually run; `—` for every other archetype (never extrapolated). Archetypes flagged with `†` completed successfully (no Fatal, real EUI produced) but threw large recurring-warning/severe-error counts tied to fixed-capacity equipment (transformer, DHW tank, HVAC coil rated flow/capacity) that the scaling engine does not scale -- see the note below the table and plan §9 E-LA-06.

| Archetype ID | Baseline IDF File | Baseline Area ($m^2$) | Sample Target Area ($m^2$) | Scale Factor ($S$) | Planar Factor ($\\sqrt{{S}}$) | Prototype Zones | Local Sim Total EUI ($kWh/m^2\\cdot yr$) | LayoutAssigner Fidelity |
|---|---|---|---|---|---|---|---|---|
"""
    for _, r in df_comp.iterrows():
        local_eui = r["local_leg_total_eui_kwh_m2"]
        caveat_flag = " †" if r["local_leg_caveat"] else ""
        local_eui_str = f"{local_eui:.2f}{caveat_flag}" if local_eui != "" else "—"
        md_content += f"| `{r['archetype_id']}` | `{r['baseline_idf']}` | {r['baseline_area_m2']:,.0f} | {r['target_sample_area_m2']:,.0f} | {r['area_scale_ratio']:.3f} | {r['planar_scale_factor']:.3f} | {r['prototype_zones_count']} | {local_eui_str} | {r['fidelity_ranking']} |\n"

    md_content += "\n† local-leg caveat (plan §9 E-LA-06), by archetype:\n"
    for arch, note in LOCAL_LEG_CAVEAT_ARCHETYPES.items():
        md_content += f"- `{arch}`: {note}\n"

    md_content += """

---

## 3. Comparison with Existing Resolution Modes (Harvested Baseline Matrix)

Below are the median Total Site EUI ($kWh/m^2\\cdot yr$) results across the 12-cell baseline matrix extracted directly from the validated 8,160-building dataset (`OpenUBEM_results_Resolution.md`). The `layout_assign` column is **not yet simulated at fleet/cell granularity** -- real per-cell EnergyPlus runs for this mode require the (out-of-scope-for-T12-local-leg) 12-cell cluster leg, so it is left as `*pending*` rather than a fabricated number.

| Cell | City | `building` (1 Zone) | `floor` (Per-Floor) | `auto` (Adaptive Baseline) | `fast_zone` (Core/Perim) | `layout_assign` (Prototype Scaled) |
|---|---|---|---|---|---|---|
"""
    for _, r in cell_pivot.iterrows():
        b_eui = r.get("building", 0.0)
        fl_eui = r.get("floor", 0.0)
        a_eui = r.get("auto", 0.0)
        fz_eui = r.get("fast_zone", 0.0)

        md_content += f"| `{r['cell']}` | {r['city']} | {b_eui:.1f} | {fl_eui:.1f} | {a_eui:.1f} | {fz_eui:.1f} | *pending* |\n"

    md_content += """
**Note (T12 local leg, 2026-07-22):** the `layout_assign` column above stays `*pending*` at this per-cell fleet granularity on purpose. A 6-archetype **local single-building** EnergyPlus validation sample (one real building per archetype family: apartment/office/hotel/school/retail/restaurant) was run instead and its real EUIs are reported in §2 above -- that is genuinely archetype-level data, matching the local leg's granularity. It cannot honestly populate this table, which is a **per-cell median across an entire building population** (hundreds to thousands of buildings per city/zone). Populating this table requires the full 12-cell cluster leg (explicitly out of scope for the local leg).
"""

    md_content += """

---

## 4. Key Findings & Recommendations

1. **Load Conservation Pass**: Internal loads ($W/m^2$) conserve across scaling factors, ensuring that energy consumption scales linearly with floor area.
2. **Complex Functions Resolved**: Complex archetypes (**Hospitals**, **Hotels**, **Secondary Schools**) retain full internal room layout fidelity without requiring dynamic polygon decomposition.
3. **Usage Guidelines**:
   - Use **`building`** and **`floor`** for ultra-fast district screening.
   - Use **`auto`** for standard fleet-wide urban building energy modeling (validated baseline).
   - Use **`layout_assign`** for high-fidelity archetype studies, HVAC sizing, and complex building program simulations.
4. **T12 local leg finding (2026-07-22, plan §9 E-LA-06, OPEN):** `scale_baseline_idf()` scales geometry (√S) and the explicitly-listed absolute load/OA/DHW-draw fields (S), but does **not** scale fixed-capacity auxiliary equipment (electrical transformers, DHW tank capacity, HVAC coil/fan rated capacity/airflow) -- these stay at the baseline's own size. At non-identity scale factors this produced large recurring-warning/severe-error counts in 5 of 6 local-leg archetypes (real EnergyPlus diagnostics, not a script bug) -- most notably 73,803 real "Transformer Overloaded" Severe Errors for `MediumOffice` (S=1.60). Only `MidriseApartment` (S=4.78, the pre-existing T09-validated case) stayed clean. The harvested EUI values are real EnergyPlus output and within plausibility bounds, but this is a genuine, unresolved scope gap in the scaling engine that a future task should address (likely alongside T11's envelope patcher) before `layout_assign` results are treated as production-grade at non-trivial scale factors.
5. **T12 local leg finding (2026-07-22, plan §9 E-LA-05, OPEN):** `openubem/results/parser.py`'s `parse_building()` / `_check_zone_integrity()` assumes the OpenUBEM `{osm_id}_F{floor}_{label}` zone-naming convention; `layout_assign` zones keep the DOE baseline's own native names (e.g. `"G SW APARTMENT"`), so `_check_zone_integrity()` always reports a false-negative zone-count mismatch for `layout_assign` buildings. This affects every `layout_assign` building, not just the local-leg sample. The §2 EUI values above were computed by calling `parse_building_sql()` + `_parse_meters_sql()` + `_compute_eui()` directly (bypassing only the zone-naming gate, which does not affect the EUI arithmetic itself) -- a documented workaround, not a fix. `parser.py` itself was intentionally left unmodified (out of scope for T12).
"""

    if write_md:
        with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Saved markdown report to: {OUTPUT_MD_PATH}")
    else:
        print(f"--write-md not set: markdown report NOT written (results doc left untouched). Would have written to: {OUTPUT_MD_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare layout_assign resolution mode against the other resolution modes.")
    parser.add_argument(
        "--write-md", action="store_true",
        help="Also (re)write the results markdown doc at OUTPUT_MD_PATH and its docs-dir CSV copy. "
             "Without this flag, only openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv is written.",
    )
    args = parser.parse_args()
    run_analysis(write_md=args.write_md)
