"""Diagnostic for INVESTIGATION_phaseD2_vs_phaseE_why_D2_closer.md.

Read-only. Decomposes the Phase-D2 -> Phase-E regression vs measured anchors
into (a) HVAC heating-core shift and (b) service-load layer, osm_id-matched over
all 8,160 buildings, and benchmarks office heating against the DOE prototypes.

    .venv/Scripts/python.exe scripts/validation/phaseE_gap_investigation.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"
RT = ROOT / "docs" / "docs_VALIDATION" / "step1" / "overAll" / "results" / "roundtrip_report.csv"

CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]
SUCCESS = {"success", "success_cached", "success_csv_fallback"}
CORE = ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2", "equipment_eui_kwh_m2"]
SERVICE = ["fans_eui_kwh_m2", "pumps_eui_kwh_m2", "dhw_eui_kwh_m2",
           "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2"]
SEG = {
    "Office": {"SmallOffice", "MediumOffice", "LargeOffice"},
    "Multifamily": {"MidriseApartment", "HighriseApartment"},
    "Warehouse": {"Warehouse"},
}
ANCHOR = {"nyc": 219.2, "la": 113.6, "austin": 162.0}
# V16-reconstructed "adopted" totals from REPORT_phaseD_final (= measured x multiplier)
D2_ADOPT_OVERALL = {"nyc": 219.2 * 1.021, "la": 113.6 * 0.963, "austin": 162.0 * 0.914}


def load(sub: str) -> pd.DataFrame:
    frames = []
    for c in CELLS:
        df = pd.read_csv(RES / sub / c / "05_results.csv", dtype={"osm_id": str})
        df["cell"], df["city"] = c, c.split("_", 1)[0]
        frames.append(df)
    d = pd.concat(frames, ignore_index=True)
    return d[d["simulation_status"].isin(SUCCESS)].copy()


def main() -> None:
    d2, de = load("phaseD2"), load("phaseE")
    for d in (d2, de):
        d["core"] = d[CORE].sum(axis=1)
    de["service"] = de[SERVICE].sum(axis=1)

    m = d2[["osm_id", "cell", "city", "archetype_id", "core"] + CORE].merge(
        de[["osm_id", "cell", "core", "service"] + CORE + SERVICE],
        on=["osm_id", "cell"], suffixes=("_d2", "_e"))
    print(f"matched buildings (success in both): {len(m)}\n")

    print("=== City Overall decomposition (medians, kWh/m2) ===")
    print(f"{'city':<8}{'meas':>7}{'D2core':>8}{'D2adopt':>9}{'Ecore':>7}{'Eserv':>7}{'Etot':>7}{'E_d%':>7}")
    for city in ("nyc", "la", "austin"):
        cm = m[(m.city == city) & (m.archetype_id != "OpenUBEMUnknown")]
        meas = ANCHOR[city]
        d2core = cm.core_d2.median()
        ecore = cm.core_e.median()
        eserv = cm.service.median()
        etot = (cm.core_e + cm.service).median()
        print(f"{city:<8}{meas:>7.1f}{d2core:>8.1f}{D2_ADOPT_OVERALL[city]:>9.1f}"
              f"{ecore:>7.1f}{eserv:>7.1f}{etot:>7.1f}{(etot - meas) / meas * 100:>6.1f}%")

    print("\n=== Per-end-use, osm-matched (Finding 1: regression is heating) ===")
    for city in ("nyc", "austin"):
        off = m[(m.city == city) & m.archetype_id.isin(SEG["Office"])]
        print(f"  {city} Office (n={len(off)}):")
        for c in CORE:
            print(f"    {c.replace('_eui_kwh_m2',''):<10} D2={off[c+'_d2'].median():6.1f} "
                  f"E={off[c+'_e'].median():6.1f}  d={off[c+'_e'].median()-off[c+'_d2'].median():+6.1f}")

    print("\n=== Finding 3: office heating vs DOE prototype (Buffalo, colder than NYC) ===")
    rt = pd.read_csv(RT)
    proto = {r.openuben_archetype: r.ref_heat for _, r in rt.iterrows()}
    for a in ("SmallOffice", "MediumOffice", "LargeOffice"):
        h2 = d2[(d2.city == "nyc") & (d2.archetype_id == a)].heating_eui_kwh_m2.median()
        he = de[(de.city == "nyc") & (de.archetype_id == a)].heating_eui_kwh_m2.median()
        print(f"  {a:<13} DOEproto={proto.get(a, float('nan')):6.1f}  D2={h2:6.1f}  E={he:6.1f}")

    print("\n=== Finding 4: pumps/fans intact ===")
    print(f"  pumps>0: {(de.pumps_eui_kwh_m2>0).sum()}/{len(de)}  "
          f"fans>0: {(de.fans_eui_kwh_m2>0).sum()}/{len(de)}")
    lo = de[de.archetype_id == "LargeOffice"]
    print(f"  LargeOffice pumps median={lo.pumps_eui_kwh_m2.median():.1f} "
          f"heating median={lo.heating_eui_kwh_m2.median():.1f}")


if __name__ == "__main__":
    main()
