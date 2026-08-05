"""C01: local real-EnergyPlus regression for the storey-matching fix
(PLAN_storey-matching_implementation.md, Phase C, task C01).

Six real BuildingIDF.build() -> real EnergyPlus 23.1 runs, covering every
named case in the plan's C01 "What":
  A. equal          (n_real == n_proto, identity -- also the S=1 control for D)
  B. taller (known)  MediumOffice n_real=6/n_proto=3, multiplier=4 -- reruns
                     the exact B06 acceptance scenario (footprint_area_m2=1000,
                     levels=6) as an independent C01 confirmation.
  C. shorter than prototype (D5 fallback_shorter)
  D. HIGH-MULTIPLIER (mandatory addition from the B06 audit) -- HighriseApartment
                     n_real=20/n_proto=3, multiplier=18, the manager's own
                     n_real=20/n_proto=3 example. Transformer-bearing (F-11).
  E. single-storey prototype, degenerate n_proto==1 branch (RetailStandalone)
  F. excluded-fallback archetype (D5 fallback_not_expressible -- SmallOffice,
     n_proto=2, no expressible middle band)

Ground truth per rule 6/8: every case is checked against its own run artifacts
(eplusout.eio Zone Information line for the actual applied Multiplier,
eplusout.err verbatim Severe lines, eplustbl.csv End Uses table), never
against a restatement of the expected value.

Throwaway diagnostic script (scripts/analysis/, not shipped).
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

from openubem.geometry import layout_assigner
from openubem.geometry.footprint import derive_num_floors
from openubem.simulation.runner import run_energyplus, classify_outcome

sys.path.insert(0, str(REPO / "scripts" / "cluster"))
from t19_harvest_layout_assign import _parse_sql  # noqa: E402

OUT_DIR = REPO / "openubem" / "outputs"
(OUT_DIR / "comparisons").mkdir(parents=True, exist_ok=True)
ARC_RESULTS = (
    REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner"
    / "debug" / "storey-Matching" / "results"
)
SCRATCH_DIR = REPO / "scratchpad" / "c01_work"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

FIXTURE = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"
    / "phaseE" / "nyc_suburban" / "01_buildings.gpkg"
)
CELL_CFG = {"lat": 40.7052, "lon": -73.5985, "state": "NY"}  # nyc_suburban, t19 CELL_CONFIGS

# (case_id, archetype_id, n_real, footprint_area_m2, note)
CASES = [
    ("A_equal_identity_highrise", "HighriseApartment", 3, 500.0, "n_real==n_proto=3, S=1 control for D"),
    ("B_taller_known_medoffice", "MediumOffice", 6, 1000.0, "n_proto=3, multiplier=4 (B06 scenario replay)"),
    ("C_shorter_midrise", "MidriseApartment", 2, 250.0, "n_proto=3, n_real<n_proto -> fallback_shorter"),
    ("D_HIGHMULT_highrise20", "HighriseApartment", 20, 350.0, "n_proto=3, multiplier=18 -- manager's own example"),
    ("E_single_storey_retail", "RetailStandalone", 3, 800.0, "n_proto=1 -- degenerate direct-multiply branch"),
    ("F_excluded_fallback_smalloffice", "SmallOffice", 4, 300.0, "n_proto=2, no middle band -> fallback_not_expressible"),
]

_TRANSFORMER_ARCHETYPES = {  # F-11, canonical archetype_id vocab (ARCHETYPE_IDF_MAP keys),
    # NOT F-11's prose/IDF-filename spelling -- this set was wrong on the first run
    # (compared "HighriseApartment"/"MediumOffice" case rows against "ApartmentHighRise"/
    # "OfficeMedium", so it never matched and transformer_capacity_in_idf()/
    # total_electricity_gj() silently returned None for every C01 case; the real
    # numbers were instead pulled directly from the saved IDF (geomeppy) and
    # eplusmtr.csv's Electricity:Facility RunPeriod column -- see the C01 §7 entry).
    "HighriseApartment", "Hospital", "LargeHotel", "LargeOffice", "MediumOffice",
    "PrimarySchool", "SecondarySchool",
}


def get_base_data():
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw

    weather_dir = SCRATCH_DIR / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)
    stations = load_stations()
    station, dist_km = resolve_station(CELL_CFG["lat"], CELL_CFG["lon"], stations)
    epw_path = fetch_epw(station, output_dir=weather_dir)
    print(f"EPW station: {station.get('station_id')} at {dist_km:.1f} km -> {epw_path}")

    gdf_raw = gpd.read_file(str(FIXTURE))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")

    # 6 template rows (any real geometry/tags -- archetype_id/levels overridden
    # below, footprint_area_m2 controls plate_target directly since
    # real_area/n_real == footprint_area_m2 exactly (D2)).
    template = gdf_in.iloc[0:len(CASES)].copy().reset_index(drop=True)

    gdf_26 = BuildingClassifier().classify(template)
    for i, (case_id, arch, n_real, fp_area, note) in enumerate(CASES):
        gdf_26.loc[i, "osm_id"] = f"c01/{case_id}"
        gdf_26.loc[i, "archetype_id"] = arch
        gdf_26.loc[i, "levels"] = n_real

    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    for i, (case_id, arch, n_real, fp_area, note) in enumerate(CASES):
        gdf_57.loc[i, "footprint_area_m2"] = fp_area
    return gdf_57, schedule_library, epw_path


def build_one(row, gdf_sample, schedule_library, build_dir):
    from openubem.idf.builder import BuildingIDF
    bidf = BuildingIDF(row, thermal_mass=True, resolution_mode="layout_assign", trim_outputs=True)
    manifest_row = bidf.build(gdf_sample, schedule_library, build_dir)
    return manifest_row


def run_one(idf_path: Path, epw_path, run_dir: Path, osm_id: str, floor_area_m2: float, timeout_s=600):
    run_dir.mkdir(parents=True, exist_ok=True)
    task = SimpleNamespace(osm_id=osm_id, epw_path=str(epw_path), work_dir=str(run_dir), idf_path=str(idf_path))
    raw = run_energyplus(task, timeout_s=timeout_s)
    result = classify_outcome(raw, run_dir)
    eui = None
    if result["status"] == "success":
        sql_path = run_dir / "eplusout.sql"
        if sql_path.exists():
            eui = _parse_sql(sql_path, floor_area_m2)
    return result, eui


_SEVERE_RE = re.compile(r"\*\*\s*Severe\s*\*\*.*", re.IGNORECASE)
_ZONE_INFO_RE = re.compile(r"^\s*Zone Information,([^,]+),.*", re.IGNORECASE)


def severe_lines(run_dir: Path) -> list[str]:
    err = run_dir / "eplusout.err"
    if not err.exists():
        return ["<no eplusout.err>"]
    # EnergyPlus 23.1's actual spacing is "** Severe  **" (two spaces before the
    # closing **) -- the original "** Severe **" (one space) substring check
    # never matched, silently reporting 0 Severe lines for every case including
    # F, which genuinely has 5. Match on the "** Severe" prefix instead.
    return [ln.strip() for ln in err.read_text(errors="replace").splitlines() if "** Severe" in ln and "**" in ln.split("** Severe", 1)[1]]


def transformer_capacity_in_idf(idf_path: Path) -> float | None:
    if not idf_path.exists():
        return None
    txt = idf_path.read_text(errors="replace")
    m = re.search(r"ElectricLoadCenter:Transformer,\s*\n\s*([^,]+),.*?\n(?:[^\n]*\n){5}\s*([0-9.eE+-]+)", txt)
    # Fallback: simpler line-scan for the Rated_Capacity numeric field (7th data
    # line after the object header in the 23.1 IDD layout) -- robust to eppy's
    # exact formatting by scanning the object block directly.
    idx = txt.find("ElectricLoadCenter:Transformer,")
    if idx == -1:
        return None
    block = txt[idx:idx + 1200]
    nums = re.findall(r"^\s*([\d.eE+-]+),.*Rated Capacity", block, re.MULTILINE)
    if nums:
        return float(nums[0])
    return None


def total_electricity_gj(run_dir: Path) -> float | None:
    """Reads the annual Electricity:Facility RunPeriod meter straight from
    eplusmtr.csv (J -> GJ). eplustbl.csv/htm do NOT exist for these runs --
    trim_outputs=True (matching the production fleet path) skips
    Output:Table:SummaryReports entirely, so the tabular-report parsing this
    function originally used (copied from a2_measure_multiplier.py, which reads
    a hand-built scratch harness's IDF, not the real BuildingIDF.build() path)
    silently returned None on every C01 case. Electricity:Facility is written
    via OUTPUT:METER:METERFILEONLY (openubem/idf/outputs.py) -- meter-file-only,
    not SQL ReportData -- but IS present in eplusmtr.csv via the runner's own
    '-r' (readVarsESO) flag."""
    mtr = run_dir / "eplusmtr.csv"
    if not mtr.exists():
        return None
    lines = mtr.read_text(errors="replace").splitlines()
    if len(lines) < 2:
        return None
    header = [h.strip() for h in lines[0].split(",")]
    try:
        idx = next(i for i, h in enumerate(header) if h.startswith("Electricity:Facility"))
    except StopIteration:
        return None
    data_line = lines[-1].split(",")
    try:
        return float(data_line[idx]) / 1e9  # J -> GJ
    except (IndexError, ValueError):
        return None


def eio_zone_multiplier(run_dir: Path, zone_name_substr: str) -> list[tuple[str, str]]:
    eio = run_dir / "eplusout.eio"
    if not eio.exists():
        return []
    out = []
    for line in eio.read_text(errors="replace").splitlines():
        if line.startswith("Zone Information,") and zone_name_substr.upper() in line.upper():
            parts = [p.strip() for p in line.split(",")]
            # Zone Information,<Name>,<X>,<Y>,<Z>,...,<Multiplier> is field index varies;
            # report the raw line, let the progress entry cite it verbatim.
            out.append((parts[1], line.strip()))
    return out


def main():
    print("Loading base data for nyc_suburban (6 synthetic-archetype rows) ...")
    gdf_57, schedule_library, epw_path = get_base_data()
    print(f"Prepared {len(gdf_57)} case rows.")

    rows_out = []
    t0 = time.monotonic()
    for i, (case_id, arch, n_real, fp_area, note) in enumerate(CASES):
        row = gdf_57.iloc[i].copy()
        osm_id = row["osm_id"]
        print(f"\n=== {case_id}: {arch} n_real={n_real} footprint={fp_area} m2 ({note}) ===")

        # Pre-run ground truth: independently recompute band_map/match_storeys
        # on the RAW baseline (mirrors builder.py's own call order) to state the
        # expected multiplier/status before the run, per rule 6/8.
        reg = layout_assigner.get_registry()
        baseline_path = reg.get_baseline_idf(arch)
        from geomeppy import IDF as GeomIDF
        from openubem import config
        try:
            GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
        except Exception:
            pass
        probe_idf = GeomIDF(str(baseline_path))
        band_map = layout_assigner.compute_band_map(probe_idf)
        match_result = layout_assigner.match_storeys(probe_idf, n_real, band_map)
        print(f"  pre-run: n_proto={band_map['n_proto']} status={match_result['status']} "
              f"multiplier={match_result['multiplier']}")

        build_dir = SCRATCH_DIR / case_id
        (build_dir / "idfs").mkdir(parents=True, exist_ok=True)
        manifest_row = build_one(row, gdf_57, schedule_library, build_dir)
        if manifest_row["generation_status"] != "success":
            print(f"  BUILD FAILED: {manifest_row['generation_status']}")
            rows_out.append({"case_id": case_id, "archetype_id": arch, "n_real": n_real,
                              "build_status": manifest_row["generation_status"],
                              "expected_status": match_result["status"],
                              "expected_multiplier": match_result["multiplier"]})
            continue

        idf_path = Path(manifest_row["idf_path"])
        run_dir = ARC_RESULTS / "c01_runs" / case_id
        floor_area_m2 = fp_area * n_real
        result, eui = run_one(idf_path, epw_path, run_dir, osm_id, floor_area_m2)
        status = result["status"]
        n_sev = result.get("n_severe")
        sev_lines = severe_lines(run_dir)
        transformer_cap = transformer_capacity_in_idf(idf_path) if arch in _TRANSFORMER_ARCHETYPES else None
        total_elec_gj = total_electricity_gj(run_dir)
        eio_lines = eio_zone_multiplier(run_dir, "MID") if match_result["status"] in ("applied",) else []

        print(f"  data_quality_flag={manifest_row.get('data_quality_flag')!r}")
        print(f"  RUN status={status} n_warnings={result.get('n_warnings')} n_severe={n_sev}")
        if sev_lines and sev_lines != ["<no eplusout.err>"]:
            print(f"  Severe lines ({len(sev_lines)}):")
            for ln in sev_lines[:5]:
                print(f"    {ln}")
            if len(sev_lines) > 5:
                print(f"    ... ({len(sev_lines) - 5} more)")
        print(f"  transformer_capacity_VA={transformer_cap}  total_electricity_GJ={total_elec_gj}")
        print(f"  total_eui={eui.get('total_eui') if eui else None} kWh/m2  "
              f"heating_eui={eui.get('heating_eui') if eui else None}")
        if eio_lines:
            for zname, ln in eio_lines[:2]:
                print(f"  .eio: {ln}")

        row_out = {
            "case_id": case_id, "archetype_id": arch, "n_real": n_real,
            "n_proto": band_map["n_proto"], "footprint_area_m2": fp_area,
            "expected_status": match_result["status"], "expected_multiplier": match_result["multiplier"],
            "data_quality_flag": manifest_row.get("data_quality_flag"),
            "build_status": "success", "run_status": status,
            "n_warnings": result.get("n_warnings"), "n_severe": n_sev,
            "severe_lines_verbatim": " | ".join(sev_lines[:10]),
            "n_severe_lines_captured": len(sev_lines) if sev_lines != ["<no eplusout.err>"] else 0,
            "transformer_capacity_VA": transformer_cap,
            "total_electricity_GJ": total_elec_gj,
            "floor_area_m2": floor_area_m2,
        }
        if eui:
            row_out.update(eui)
        rows_out.append(row_out)

    elapsed = time.monotonic() - t0
    df = pd.DataFrame(rows_out)
    out_csv = ARC_RESULTS / "c01_regression_results.csv"
    df.to_csv(out_csv, index=False)
    df.to_csv(OUT_DIR / "comparisons" / "c01_regression_results.csv", index=False)
    print(f"\nWrote {out_csv} ({elapsed/60:.1f} min total)")
    print(df[["case_id", "archetype_id", "n_real", "n_proto", "expected_status", "expected_multiplier",
              "run_status", "n_severe", "total_eui"]] if "total_eui" in df.columns else df)
    print("DONE")


if __name__ == "__main__":
    main()
