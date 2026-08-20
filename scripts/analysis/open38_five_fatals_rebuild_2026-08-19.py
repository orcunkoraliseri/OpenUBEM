"""OPEN-38 T05 (2026-08-19) -- rebuild locally the 5 unmeasured LAUNDRYROOMFLR1
`layout_assign` fatals, plus 1 positive control (an already-measured fatal,
must reproduce) and 3 negative controls (one healthy layout_assign sibling
per cell, must complete).

The register's stated blocker ("no IDF survives for them") is a corpus
statement about the swept E02 `idfs/` directory, not a capability statement --
the pipeline can rebuild a `layout_assign` IDF for any osm_id given its cell's
`01_buildings.gpkg`. This script does that, real pipeline, unmodified, no
production code touched.

Targets (from `extra/MEASUREMENT_open-38_laundryroom.md`'s re-derived population
of 7, cross-referenced against the register's OPEN-07 amendment naming which
2 of 7 already have a surviving rebuilt IDF):

  UNMEASURED (5):
    la_centre / way_427942886
    la_urban  / relation_6374725
    la_urban  / way_401910463
    la_urban  / way_428846131
    nyc_rural / way_965718400

  POSITIVE CONTROL (1, already measured 2026-08-18 via a different scratchpad
  script against the same fixture family -- rebuilt again here, independently,
  as this task's own positive control):
    nyc_rural / way_965718402

  NEGATIVE CONTROL (3, one healthy `layout_assign` sibling per cell, picked
  from the surviving E02 harvest `.end` files -- 0 Severe, fast runtime):
    la_centre / relation_6333145   (23 Warning; 0 Severe; healthy in E02 harvest)
    la_urban  / relation_6356887   (169550 Warning; 0 Severe; healthy in E02 harvest)
    nyc_rural / way_1103897842     (21 Warning; 0 Severe; healthy in E02 harvest)

Fixture: `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/<cell>/01_buildings.gpkg`
(dated 2026-08-12, 2 days AFTER the 2026-08-10 E02 harvest that produced the
original `.err` fatals -- the closest-in-time frozen corpus available on disk).
NOT the `docs/docs_VALIDATION/.../phaseE/` fixture: that one is dated 2026-06-28
(43 days *before* the harvest) and was already tried, once, independently, in
`scratchpad/e-la-20-investigation/i03/part1_passers.py` (2026-08-18) for these
same two osm_ids under this same real pipeline -- and it did **not** reproduce
the known fatal (way/965718402 completed successfully, 0 Severe; way/965718403
crashed abnormally, exit -1, no `eplusout.end` at all). That prior null result
is why this script does not reuse the phaseE fixture. Re-verified present on
disk before use (hard rule 11).

Real pipeline, unmodified: BuildingClassifier().classify() -> assign_climate_zones()
-> enrich_semantics() -> run_step3(resolution_mode="layout_assign") -> EnergyPlus
with the canonical `openubem.simulation.runner.run_energyplus` command
(-w epw -d workdir -x -r idf), max 4 concurrent.
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

OUT_DIR = REPO / "scratchpad" / "open38-t05-rebuild"
FIXTURE_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet")
MAX_WORKERS = 4

CELL_CFG = {
    "nyc_rural": {"lat": 42.0396, "lon": -74.1143, "state": "NY"},
    "la_centre": {"lat": 34.0522, "lon": -118.2437, "state": "CA"},
    "la_urban": {"lat": 34.0584, "lon": -118.3040, "state": "CA"},
}

TARGETS = {
    "la_centre": {
        "unmeasured": ["way/427942886"],
        "positive_control": [],
        "negative_control": ["relation/6333145"],
    },
    "la_urban": {
        "unmeasured": ["relation/6374725", "way/401910463", "way/428846131"],
        "positive_control": [],
        "negative_control": ["relation/6356887"],
    },
    "nyc_rural": {
        "unmeasured": ["way/965718400"],
        "positive_control": ["way/965718402"],
        "negative_control": ["way/1103897842"],
    },
}


@dataclass(frozen=True)
class BuildResult:
    cell: str
    osm_id: str
    role: str
    generation_status: str
    idf_path: str
    archetype_id: str


def build_cell(cell: str):
    fixture = FIXTURE_ROOT / cell / "01_buildings.gpkg"
    if not fixture.exists():
        raise FileNotFoundError(f"Fixture missing at time of use: {fixture}")
    print(f"[{cell}] fixture re-verified on disk: {fixture} ({fixture.stat().st_size} bytes)")

    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    from openubem.idf.builder import run_step3

    cfg = CELL_CFG[cell]
    work_base = OUT_DIR / cell
    work_base.mkdir(parents=True, exist_ok=True)
    weather_dir = work_base / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)

    stations = load_stations()
    station, dist_km = resolve_station(cfg["lat"], cfg["lon"], stations)
    epw_path = fetch_epw(station, output_dir=weather_dir)
    print(f"[{cell}] EPW: {epw_path} (station dist {dist_km:.1f} km)")

    gdf_raw = gpd.read_file(str(fixture))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    gdf_26 = BuildingClassifier().classify(gdf_in)

    all_ids = (TARGETS[cell]["unmeasured"] + TARGETS[cell]["positive_control"]
               + TARGETS[cell]["negative_control"])
    present = gdf_26["osm_id"].astype(str).isin(all_ids)
    found_ids = set(gdf_26.loc[present, "osm_id"].astype(str))
    missing_ids = set(all_ids) - found_ids
    if missing_ids:
        print(f"[{cell}] WARNING: not found in fixture: {missing_ids}")

    real_archetypes = gdf_26.loc[present, ["osm_id", "archetype_id"]]
    print(f"[{cell}] classify() output for targets:\n{real_archetypes.to_string()}")

    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(
        zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB)
    )
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values,
        categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )
    gdf_57, schedule_library = enrich_semantics(gdf_29)

    gdf_sample = gdf_57[gdf_57["osm_id"].astype(str).isin(all_ids)].copy()

    step3_dir = work_base / "step3_layout_assign"
    step3_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_step3(
        gdf_sample, schedule_library, step3_dir,
        n_jobs=1, resolution_mode="layout_assign", trim_outputs=True,
    )
    manifest.to_csv(work_base / "idf_manifest.csv", index=False)

    role_of = {}
    for osm_id in TARGETS[cell]["unmeasured"]:
        role_of[osm_id] = "unmeasured"
    for osm_id in TARGETS[cell]["positive_control"]:
        role_of[osm_id] = "positive_control"
    for osm_id in TARGETS[cell]["negative_control"]:
        role_of[osm_id] = "negative_control"

    results = []
    for _, mrow in manifest.iterrows():
        osm_id = str(mrow["osm_id"])
        arche = gdf_sample.loc[gdf_sample["osm_id"].astype(str) == osm_id, "archetype_id"]
        arche_val = arche.iloc[0] if len(arche) else ""
        results.append(BuildResult(
            cell=cell, osm_id=osm_id, role=role_of.get(osm_id, "?"),
            generation_status=str(mrow["generation_status"]),
            idf_path=str(mrow.get("idf_path", "")),
            archetype_id=str(arche_val),
        ))
    return results, epw_path, work_base


def run_one_sim(build: BuildResult, epw_path, work_base):
    from openubem.simulation.parallel import SimTask
    from openubem.simulation.runner import run_energyplus, classify_outcome
    from openubem.results.err_parse import FATAL_RE

    safe_id = build.osm_id.replace("/", "_")
    run_dir = work_base / "sim" / safe_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if build.generation_status != "success" or not build.idf_path:
        return {
            "cell": build.cell, "osm_id": build.osm_id, "role": build.role,
            "archetype_id": build.archetype_id, "generation_status": build.generation_status,
            "sim_status": "no_idf", "n_warnings": None, "n_severe": None,
            "error_summary": "", "fatal_two_space": False, "run_dir": str(run_dir),
        }

    task = SimTask(osm_id=build.osm_id, idf_path=build.idf_path,
                    epw_path=str(epw_path), work_dir=str(run_dir))
    t0 = time.monotonic()
    raw = run_energyplus(task)
    elapsed = time.monotonic() - t0
    outcome = classify_outcome(raw, run_dir)

    err_path = run_dir / "eplusout.err"
    err_text = err_path.read_text(errors="replace") if err_path.exists() else ""
    fatal_two_space = "**  Fatal  **" in err_text

    return {
        "cell": build.cell, "osm_id": build.osm_id, "role": build.role,
        "archetype_id": build.archetype_id, "generation_status": build.generation_status,
        "sim_status": outcome["status"], "n_warnings": outcome["n_warnings"],
        "n_severe": outcome["n_severe"], "error_summary": outcome["error_summary"],
        "fatal_two_space": fatal_two_space, "elapsed_s": elapsed,
        "run_dir": str(run_dir), "empty_dir_serial_reverify": None,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_builds = []
    epw_by_cell = {}
    work_base_by_cell = {}
    for cell in CELL_CFG:
        results, epw_path, work_base = build_cell(cell)
        all_builds.extend(results)
        epw_by_cell[cell] = epw_path
        work_base_by_cell[cell] = work_base

    print(f"\n=== {len(all_builds)} IDFs built, now simulating (max {MAX_WORKERS} concurrent) ===")
    for b in all_builds:
        print(f"  {b.cell}/{b.osm_id} [{b.role}] generation_status={b.generation_status} archetype={b.archetype_id}")

    sim_results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {
            pool.submit(run_one_sim, b, epw_by_cell[b.cell], work_base_by_cell[b.cell]): b
            for b in all_builds
        }
        for fut in as_completed(futs):
            b = futs[fut]
            r = fut.result()
            print(f"  DONE {b.cell}/{b.osm_id} [{b.role}]: sim_status={r['sim_status']} "
                  f"n_severe={r['n_severe']} fatal_two_space={r['fatal_two_space']}")
            sim_results.append(r)

    # Empty-output-directory check: an empty run_dir is NOT a failure by itself (hard rule 7).
    for r in sim_results:
        run_dir = Path(r["run_dir"])
        n_files = len(list(run_dir.glob("*"))) if run_dir.exists() else 0
        r["empty_dir_serial_reverify"] = (n_files == 0)
        if n_files == 0:
            print(f"  ** EMPTY OUTPUT DIR (needs serial re-verify): {run_dir}")

    df = pd.DataFrame(sim_results)
    out_csv = REPO / "openubem" / "outputs" / "comparisons" / "open38_five_fatals_rebuild.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nWrote {out_csv}")
    print(df[["cell", "osm_id", "role", "archetype_id", "sim_status", "n_severe",
              "fatal_two_space", "error_summary"]].to_string())


if __name__ == "__main__":
    main()
