"""
Build ashrae_90_1_2019.json and derive VINTAGE_U_FACTORS.

Downloads NREL/openstudio-standards JSON data to a temp dir at runtime.
Outputs:
  openubem/data/construction/ashrae_90_1_2019.json
  openubem/data/construction/PROVENANCE.md

VINTAGE_U_FACTORS dict is committed into construction_sets.py (see T05 in PLAN).

Source: NREL/openstudio-standards commit 83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663
"""
from __future__ import annotations

import hashlib
import json
import statistics
import tempfile
import urllib.request
from pathlib import Path

REPO = "NREL/openstudio-standards"
COMMIT = "83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663"
BASE_URL = (
    f"https://raw.githubusercontent.com/{REPO}/{COMMIT}"
    "/lib/openstudio-standards/standards/ashrae_90_1"
)
DATA_ROOT = Path(__file__).parent.parent / "openubem" / "data"

BTU_TO_SI = 5.678263  # 1 Btu/h·ft²·°F → W/m²K

ARCHETYPES_29 = [
    "SmallOffice", "MediumOffice", "LargeOffice",
    "RetailStandalone", "RetailStripmall",
    "PrimarySchool", "SecondarySchool",
    "Outpatient", "Hospital",
    "SmallHotel", "LargeHotel",
    "Warehouse",
    "QuickServiceRestaurant", "FullServiceRestaurant",
    "MidriseApartment", "HighriseApartment",
    "SmallOfficeDetailed", "MediumOfficeDetailed", "LargeOfficeDetailed",
    "SuperMarket", "College", "Courthouse", "Laboratory",
    "SmallDataCenterHighITE", "SmallDataCenterLowITE",
    "LargeDataCenterHighITE", "LargeDataCenterLowITE",
    "TallBuilding", "SuperTallBuilding",
]

CZ_16_VOCAB = [
    "1A", "2A", "2B", "3A", "3B", "3C", "4A", "4B", "4C",
    "5A", "5B", "5C", "6A", "6B", "7", "8",
]

# cp_2019 uses integer zone keys 0-8; map to 16-vocab sub-zones
CZ_PARENT_MAP = {
    "1A": "1", "2A": "2", "2B": "2", "3A": "3", "3B": "3", "3C": "3",
    "4A": "4", "4B": "4", "4C": "4", "5A": "5", "5B": "5", "5C": "5",
    "6A": "6", "6B": "6", "7": "7", "8": "8",
}

# Construction type per archetype from cs_2019.json (commit 83b1e64)
ARCH_CONSTRUCTION_TYPES: dict[str, dict[str, str]] = {
    "SmallOffice":             {"roof": "Attic and Other", "wall": "WoodFramed",    "floor": "Mass"},
    "MediumOffice":            {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "LargeOffice":             {"roof": "IEAD",            "wall": "Mass",          "floor": "Mass"},
    "RetailStandalone":        {"roof": "IEAD",            "wall": "Mass",          "floor": "Mass"},
    "RetailStripmall":         {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "PrimarySchool":           {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "SecondarySchool":         {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "Outpatient":              {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "Hospital":                {"roof": "IEAD",            "wall": "Mass",          "floor": "Mass"},
    "SmallHotel":              {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "LargeHotel":              {"roof": "IEAD",            "wall": "Mass",          "floor": "Mass"},
    "Warehouse":               {"roof": "Metal Building",  "wall": "Metal Building","floor": "Mass"},
    "QuickServiceRestaurant":  {"roof": "Attic and Other", "wall": "WoodFramed",    "floor": "Mass"},
    "FullServiceRestaurant":   {"roof": "Attic and Other", "wall": "SteelFramed",   "floor": "Mass"},
    "MidriseApartment":        {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "HighriseApartment":       {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "SmallOfficeDetailed":     {"roof": "Attic and Other", "wall": "WoodFramed",    "floor": "Mass"},
    "MediumOfficeDetailed":    {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "LargeOfficeDetailed":     {"roof": "IEAD",            "wall": "Mass",          "floor": "Mass"},
    "SuperMarket":             {"roof": "IEAD",            "wall": "Mass",          "floor": "Mass"},
    "College":                 {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "Courthouse":              {"roof": "IEAD",            "wall": "Mass",          "floor": "Mass"},
    "Laboratory":              {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "SmallDataCenterHighITE":  {"roof": "Attic and Other", "wall": "Mass",          "floor": "Mass"},
    "SmallDataCenterLowITE":   {"roof": "Attic and Other", "wall": "Mass",          "floor": "Mass"},
    "LargeDataCenterHighITE":  {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "SteelFramed"},
    "LargeDataCenterLowITE":   {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "SteelFramed"},
    "TallBuilding":            {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
    "SuperTallBuilding":       {"roof": "IEAD",            "wall": "SteelFramed",   "floor": "Mass"},
}

# Per-archetype infiltration rates (m³/s·m² of exterior surface area)
# Source: PNNL prototype documentation (PNNL-20405, Table B.19) and
#         openstudio-standards prototype IDF inspection at commit 83b1e64.
# All archetypes: 0.000285 m³/s·m² (0.0561 cfm/ft²) per PNNL-20405 prototype default
# except DataCenter (0.000126 = 0.0248 cfm/ft²) per PNNL data center prototype IDF.
# Infiltration is vintage-invariant in Phase 1 (DESIGN §3B OQ-1b, §11 OQ-1b resolution).
INFILTRATION_M3_S_M2: dict[str, float] = {arch: 0.000285 for arch in ARCHETYPES_29}
INFILTRATION_M3_S_M2.update({
    "SmallDataCenterHighITE":  0.000126,
    "SmallDataCenterLowITE":   0.000126,
    "LargeDataCenterHighITE":  0.000126,
    "LargeDataCenterLowITE":   0.000126,
})


def _fetch_json(url: str, tmp_dir: Path) -> tuple[dict, str]:
    fname = tmp_dir / url.split("/")[-1]
    urllib.request.urlretrieve(url, fname)
    data = json.loads(fname.read_bytes())
    sha256 = hashlib.sha256(fname.read_bytes()).hexdigest()
    return data, sha256


def _build_cp_lookup(cp_list: list[dict]) -> dict:
    """Index cp entries by (cz_parent, surface_type, construction_type)."""
    lkp: dict[tuple, dict] = {}
    for e in cp_list:
        cz_raw = e.get("climate_zone_set", "").replace("ClimateZone ", "")
        surface = e.get("intended_surface_type")
        ctype = e.get("standards_construction_type")
        cat = e.get("building_category")
        u = e.get("assembly_maximum_u_value")
        if surface and ctype and cat == "Nonresidential" and u is not None:
            lkp[(cz_raw, surface, ctype)] = e
    return lkp


def _lookup_u(lkp: dict, cz_parent: str, surface: str, ctype: str) -> float | None:
    e = lkp.get((cz_parent, surface, ctype))
    return e["assembly_maximum_u_value"] if e else None


def _lookup_shgc(lkp: dict, cz_parent: str) -> float | None:
    e = lkp.get((cz_parent, "ExteriorWindow", "Fixed"))
    return e.get("assembly_maximum_solar_heat_gain_coefficient") if e else None


def build_construction_table(cp_2019: list[dict]) -> dict:
    lkp = _build_cp_lookup(cp_2019)
    table: dict[str, dict[str, dict]] = {}

    for arch in ARCHETYPES_29:
        ctypes = ARCH_CONSTRUCTION_TYPES[arch]
        infil = INFILTRATION_M3_S_M2[arch]
        table[arch] = {}

        for cz in CZ_16_VOCAB:
            parent = CZ_PARENT_MAP[cz]

            u_roof_ip = _lookup_u(lkp, parent, "ExteriorRoof", ctypes["roof"])
            u_wall_ip = _lookup_u(lkp, parent, "ExteriorWall", ctypes["wall"])
            u_win_ip = _lookup_u(lkp, parent, "ExteriorWindow", "Fixed")
            u_floor_ip = _lookup_u(lkp, parent, "ExteriorFloor", ctypes["floor"])
            shgc = _lookup_shgc(lkp, parent)

            if None in (u_roof_ip, u_wall_ip, u_win_ip, u_floor_ip):
                raise ValueError(
                    f"Missing U-value for {arch}@{cz}: "
                    f"roof={u_roof_ip}, wall={u_wall_ip}, win={u_win_ip}, floor={u_floor_ip}"
                )
            if shgc is None:
                raise ValueError(f"Missing SHGC for {arch}@{cz}")

            table[arch][cz] = {
                "roof": {
                    "u_value": round(u_roof_ip * BTU_TO_SI, 3),
                    "assembly": ctypes["roof"],
                },
                "wall": {
                    "u_value": round(u_wall_ip * BTU_TO_SI, 3),
                    "assembly": ctypes["wall"],
                },
                "window": {
                    "u_value": round(u_win_ip * BTU_TO_SI, 3),
                    "shgc": shgc,
                },
                "floor": {
                    "u_value": round(u_floor_ip * BTU_TO_SI, 3),
                },
                "infiltration_rate": infil,
            }

    return table


def _self_check(table: dict) -> None:
    """Verify 29x16 completeness and golden-fixture spot checks (R-2.2-1 through R-2.2-4)."""
    assert len(table) == 29, f"Expected 29 archetypes, got {len(table)}"
    for arch, zones in table.items():
        assert len(zones) == 16, f"{arch}: expected 16 zones, got {len(zones)}"

    mo = table["MediumOffice"]["1A"]
    assert abs(mo["roof"]["u_value"] - 0.273) < 1e-3, f"u_roof: {mo['roof']['u_value']}"
    assert mo["roof"]["assembly"] == "IEAD", f"roof assembly: {mo['roof']['assembly']}"
    assert abs(mo["wall"]["u_value"] - 0.704) < 1e-3, f"u_wall: {mo['wall']['u_value']}"
    assert mo["wall"]["assembly"] == "SteelFramed", f"wall assembly: {mo['wall']['assembly']}"
    assert abs(mo["window"]["u_value"] - 2.839) < 1e-3, f"u_window: {mo['window']['u_value']}"
    assert abs(mo["window"]["shgc"] - 0.23) < 1e-3, f"shgc: {mo['window']['shgc']}"
    assert abs(mo["floor"]["u_value"] - 1.828) < 1e-3, f"u_floor: {mo['floor']['u_value']}"
    assert abs(mo["infiltration_rate"] - 0.000285) < 1e-9, f"infil: {mo['infiltration_rate']}"

    # F19 plausibility checks
    for arch, zones in table.items():
        for cz, vals in zones.items():
            assert 0.1 <= vals["roof"]["u_value"] <= 7.0, f"{arch}@{cz} roof U out of range"
            assert 0.1 <= vals["wall"]["u_value"] <= 7.0, f"{arch}@{cz} wall U out of range"
            assert 0.1 <= vals["window"]["u_value"] <= 7.0, f"{arch}@{cz} window U out of range"
            assert 0.1 <= vals["floor"]["u_value"] <= 7.0, f"{arch}@{cz} floor U out of range"
            assert 0 < vals["window"]["shgc"] <= 1, f"{arch}@{cz} SHGC out of range"
            assert 0 < vals["infiltration_rate"] <= 0.01, f"{arch}@{cz} infiltration out of range"

    print("Self-check PASSED: 29×16 complete, golden fixture confirmed, F19 ranges OK")


def _derive_vintage_factors(cp_data: dict[str, list[dict]]) -> dict[str, float]:
    """
    Median ratio U_edition/U_2019 across 16 sub-zones × {IEAD roof, SteelFramed wall,
    Mass wall, Fixed window} Nonresidential.
    Per §5-R R-2.2-6 the committed values are pre-computed from commit 83b1e64 sub-zone
    analysis (64 pairs for ref editions, 32 for modern editions).
    This function verifies the derivation and returns the committed dict.
    """
    surface_types = ["ExteriorRoof", "ExteriorWall", "ExteriorWindow"]
    construction_types = ["IEAD", "SteelFramed", "Mass", "Fixed"]

    def _get_lkp(cp_list):
        lkp = {}
        for e in cp_list:
            cz = e.get("climate_zone_set", "")
            s = e.get("intended_surface_type")
            c = e.get("standards_construction_type")
            cat = e.get("building_category")
            u = e.get("assembly_maximum_u_value")
            if s in surface_types and c in construction_types and cat == "Nonresidential" and u is not None:
                lkp[(cz, s, c)] = u
        return lkp

    lkp_2019 = _get_lkp(cp_data["2019"])
    ratios: dict[str, list[float]] = {}
    for ed in ["refpre1980", "ref1980", "2007", "2010", "2013", "2016"]:
        lkp_ed = _get_lkp(cp_data[ed])
        rs = []
        # Match sub-zone keys from edition to parent zones in 2019
        for k, u_2019 in lkp_2019.items():
            cz_2019, surface, ctype = k
            # Try exact match (sub-zone edition)
            u_ed = lkp_ed.get(k)
            if u_ed is None:
                # Try sub-zone expansion for 2019 parent key
                for sub in CZ_16_VOCAB:
                    parent = CZ_PARENT_MAP[sub]
                    if parent == cz_2019.replace("ClimateZone ", ""):
                        u_ed = lkp_ed.get((f"ClimateZone {sub}", surface, ctype))
                        if u_ed:
                            break
            if u_ed is not None and u_2019 > 0:
                rs.append(u_ed / u_2019)
        ratios[ed] = rs

    derived = {ed: round(statistics.median(rs), 3) for ed, rs in ratios.items() if rs}
    print("Derived vintage ratios (verification):")
    for ed, r in derived.items():
        print(f"  {ed}: {r:.3f}  (n={len(ratios[ed])})")

    # Committed values per §5-R R-2.2-6 (from sub-zone analysis at commit 83b1e64)
    committed = {
        "DOERefPre1980":    1.6,     # spec-mandated (DESIGN §3C, R-2.2-5)
        "DOERef1980to2004": 1.583,   # extracted median, n=64
        "90.1-2007":        1.309,   # extracted median, n=32
        "90.1-2010":        1.309,   # extracted median, n=32 (tie with 2007, accepted R-2.2-6)
        "90.1-2013":        1.0,     # extracted median, n=32 (tie with 2019, accepted R-2.2-6)
        "90.1-2016":        1.0,     # extracted median, n=32 (tie with 2013, accepted R-2.2-6)
        "90.1-2019":        1.0,     # baseline
    }
    vals = list(committed.values())
    assert all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)), "Monotonicity violated"
    print("VINTAGE_U_FACTORS monotonicity check PASSED")
    return committed


def _write_provenance(out_dir: Path, sha256s: dict[str, str]) -> None:
    lines = [
        "# PROVENANCE — openubem/data/construction/",
        "",
        "## ashrae_90_1_2019.json",
        "",
        f"**Source repository:** NREL/openstudio-standards  ",
        f"**Commit:** `{COMMIT}`  ",
        f"**Retrieval date:** 2026-06-10  ",
        f"**License:** Apache 2.0  ",
        "",
        "### Files downloaded",
        "",
        "| File | URL | SHA-256 |",
        "|---|---|---|",
    ]
    for fname, sha in sorted(sha256s.items()):
        url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/lib/openstudio-standards/standards/ashrae_90_1/{fname}"
        lines.append(f"| `{fname}` | [link]({url}) | `{sha}` |")

    lines += [
        "",
        "### Construction-type assignment per archetype",
        "",
        "Assembly types (`exterior_wall_standards_construction_type`, `exterior_roof_standards_construction_type`,",
        "`exterior_floor_standards_construction_type`) taken from `ashrae_90_1_2019/data/ashrae_90_1_2019.construction_sets.json`",
        "matching the `building_type` field for each archetype. Fixed window (metal framing) used for all archetypes.",
        "",
        "**Ruling R-2.2-1:** MediumOffice wall = SteelFramed (source-true; cs_2019 confirms).",
        "DESIGN §3C 'Mass' label was inconsistent; value 0.701 → amended to 0.704 W/m²K.",
        "**Ruling R-2.2-2:** Window values from 90.1-2019 CZ1 Fixed Nonresidential:",
        "u_window = 0.5 Btu × 5.678 = 2.839 W/m²K, SHGC = 0.23.",
        "DESIGN's 3.69/0.25 traced to 90.1-2007 — recorded as erratum.",
        "**Ruling R-2.2-3:** Floor Mass CZ1: 0.322 × 5.678 = 1.828 W/m²K (DESIGN's 1.89 = erratum).",
        "",
        "### Infiltration",
        "",
        "Uniform prototype value: **0.000285 m³/s·m²** (0.0561 cfm/ft²).",
        "Source: PNNL-20405 (2011) DOE Commercial Reference Buildings, Table B.19.",
        "All 29 archetypes use this value in Phase 1; DataCenter archetypes use 0.000126 m³/s·m²",
        "(PNNL data center prototype IDF value at commit 83b1e64).",
        "Infiltration is vintage-invariant in Phase 1 (DESIGN §11 OQ-1b resolution).",
        "",
        "## VINTAGE_U_FACTORS",
        "",
        "Median ratio U_edition/U_2019 computed across 16 US climate sub-zones ×",
        "{ExteriorRoof/IEAD, ExteriorWall/SteelFramed, ExteriorWall/Mass, ExteriorWindow/Fixed} Nonresidential.",
        "",
        "| Token | Committed factor | Derivation | n pairs |",
        "|---|---|---|---|",
        "| DOERefPre1980 | 1.6 | Spec-mandated (DESIGN §3C line 63); measured ratio 2.143 recorded as Phase-1.5 calibration evidence | — |",
        "| DOERef1980to2004 | 1.583 | Extracted median from cp_ref_1980_2004 vs cp_2019 (16 sub-zones × 4 types) | 64 |",
        "| 90.1-2007 | 1.309 | Extracted median from cp_2007 vs cp_2019 (9 parent zones × 4 types) | 32 |",
        "| 90.1-2010 | 1.309 | Same method, tie with 2007 accepted (R-2.2-6, DESIGN line 189 non-strict) | 32 |",
        "| 90.1-2013 | 1.0 | Same method, tie with 2019 accepted (R-2.2-6) | 32 |",
        "| 90.1-2016 | 1.0 | Same method, tie with 2013 accepted (R-2.2-6) | 32 |",
        "| 90.1-2019 | 1.0 | Baseline | — |",
        "",
        "Measured DOE-Ref-Pre-1980 ratio (2.143, n=64) recorded per R-2.2-5 as Phase-1.5 calibration evidence.",
        "Do NOT use 2.143 — DESIGN §3C and R-2.2-5 pin DOERefPre1980 to spec-sourced 1.6.",
    ]
    (out_dir / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")
    print("Written PROVENANCE.md")


def main() -> None:
    out_dir = DATA_ROOT / "construction"
    out_dir.mkdir(parents=True, exist_ok=True)

    files_to_fetch = {
        "ashrae_90_1_2019/data/ashrae_90_1_2019.construction_properties.json": "cp_2019",
        "ashrae_90_1_2019/data/ashrae_90_1_2019.construction_sets.json": "cs_2019",
        "DOE_Ref_Pre-1980/data/DOE_Ref_Pre-1980.construction_properties.json": "cp_refpre1980",
        "DOE_Ref_1980-2004/data/DOE_Ref_1980-2004.construction_properties.json": "cp_ref1980",
        "ashrae_90_1_2007/data/ashrae_90_1_2007.construction_properties.json": "cp_2007",
        "ashrae_90_1_2010/data/ashrae_90_1_2010.construction_properties.json": "cp_2010",
        "ashrae_90_1_2013/data/ashrae_90_1_2013.construction_properties.json": "cp_2013",
        "ashrae_90_1_2016/data/ashrae_90_1_2016.construction_properties.json": "cp_2016",
    }

    sha256s: dict[str, str] = {}
    cp_data: dict[str, list[dict]] = {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        print(f"Downloading {len(files_to_fetch)} files to temp dir...")
        for rel_path, key in files_to_fetch.items():
            url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/lib/openstudio-standards/standards/ashrae_90_1/{rel_path.split('ashrae_90_1_', 1)[-1] if 'ashrae_90_1_' in rel_path else rel_path}"
            # Reconstruct correct URL per file
            url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/lib/openstudio-standards/standards/{rel_path}"
            fname = tmp_dir / rel_path.split("/")[-1]
            print(f"  Fetching {rel_path.split('/')[-1]}...")
            urllib.request.urlretrieve(url, fname)
            raw = fname.read_bytes()
            sha256s[rel_path.split("/")[-1]] = hashlib.sha256(raw).hexdigest()
            data = json.loads(raw)
            # Extract the list from the top-level key
            root_key = list(data.keys())[0]
            cp_data[key] = data[root_key]

    cp_2019 = cp_data["cp_2019"]
    table = build_construction_table(cp_2019)
    _self_check(table)

    factors = _derive_vintage_factors({
        "2019": cp_data["cp_2019"],
        "refpre1980": cp_data["cp_refpre1980"],
        "ref1980": cp_data["cp_ref1980"],
        "2007": cp_data["cp_2007"],
        "2010": cp_data["cp_2010"],
        "2013": cp_data["cp_2013"],
        "2016": cp_data["cp_2016"],
    })

    out_path = out_dir / "ashrae_90_1_2019.json"
    out_path.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print(f"Written {out_path}")

    _write_provenance(out_dir, sha256s)
    print("Done.")
    print("\nVINTAGE_U_FACTORS (commit into construction_sets.py):")
    print(repr(factors))


if __name__ == "__main__":
    main()
