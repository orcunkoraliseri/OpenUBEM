"""C04: per-archetype, per-end-use regression fixture (PLAN_techtransfer-block6-2026-09-18.md §2a).

Golden table: tests/fixtures/golden_archetype_enduse/golden_table.csv, mean EUI (kWh/m2) per
archetype_id x 11 end uses, from a 20-building sample (2 WWR variants x the 10-archetype
tests/fixtures/synthetic_10_buildings.py fixture) built and simulated through the real
openubem.idf.builder.run_step3 -> openubem.simulation.parallel.run_neighbourhood ->
openubem.results.parser.parse_building pipeline, EnergyPlus 23.1.0, Chicago TMY3 EPW. See that
directory's README.md for full provenance, including the pre-existing, out-of-scope Warehouse
fatal (both variants) that leaves 18/20 buildings across 9 archetypes in the golden table.

This is a genuine engine/pipeline regression check (motivation: an engine upgrade once moved one
archetype's gas use by +56.6% while the fleet total looked fine), so the live comparison test
re-runs the real pipeline rather than re-parsing frozen SQL. It is marked energyplus/slow and
skips if the EnergyPlus binary is absent, mirroring tests/test_sim_integration.py.
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from tests.fixtures.synthetic_10_buildings import _build_rows

_GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden_archetype_enduse"
_GOLDEN_CSV = _GOLDEN_DIR / "golden_table.csv"

_END_USE_COLS = [
    "heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
    "equipment_eui_kwh_m2", "fans_eui_kwh_m2", "pumps_eui_kwh_m2",
    "dhw_eui_kwh_m2", "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2",
    "elevators_eui_kwh_m2", "total_eui_kwh_m2",
]

_REL_TOL = 0.01
_ABS_TOL = 0.05


def load_golden() -> pd.DataFrame:
    """Load the committed archetype x end-use golden table, indexed by archetype_id."""
    return pd.read_csv(_GOLDEN_CSV, index_col="archetype_id")


def compare_archetype_tables(fresh: pd.DataFrame, golden: pd.DataFrame) -> list[dict]:
    """Compare a fresh archetype x end-use table against the golden one.

    Returns one dict per moved (archetype, end_use) cell, each naming the archetype and the end
    use explicitly in its "detail" message (C04 "How to test": report which archetype and which
    end use moved, not just pass/fail). Empty list means no regression detected.
    """
    mismatches: list[dict] = []
    for archetype in golden.index:
        if archetype not in fresh.index:
            mismatches.append({
                "archetype": archetype,
                "end_use": "(all)",
                "detail": f"archetype={archetype!r} missing from the fresh run entirely",
            })
            continue
        for end_use in _END_USE_COLS:
            g = float(golden.loc[archetype, end_use])
            f = float(fresh.loc[archetype, end_use])
            tol = max(_ABS_TOL, _REL_TOL * abs(g))
            if abs(f - g) > tol:
                mismatches.append({
                    "archetype": archetype,
                    "end_use": end_use,
                    "golden": g,
                    "fresh": f,
                    "delta": f - g,
                    "detail": (
                        f"archetype={archetype!r} end_use={end_use!r} moved: "
                        f"golden={g:.4f} fresh={f:.4f} delta={f - g:+.4f} kWh/m2"
                    ),
                })
    return mismatches


def test_golden_table_covers_required_sample():
    golden = load_golden()
    assert golden["n_buildings"].sum() >= 12, "golden sample must cover >= 12 buildings"
    assert len(golden.index) >= 4, "golden sample must cover >= 4 archetypes"


def test_perturbation_is_named_by_archetype_and_end_use():
    golden = load_golden()
    fresh = golden.copy()
    perturbed_archetype = "MediumOffice"
    perturbed_end_use = "heating_eui_kwh_m2"
    fresh.loc[perturbed_archetype, perturbed_end_use] *= 1.566

    mismatches = compare_archetype_tables(fresh, golden)

    assert len(mismatches) == 1, f"expected exactly 1 mismatch, got {mismatches}"
    m = mismatches[0]
    assert m["archetype"] == perturbed_archetype
    assert m["end_use"] == perturbed_end_use
    assert perturbed_archetype in m["detail"]
    assert perturbed_end_use in m["detail"]


def test_matching_table_reports_no_mismatch():
    golden = load_golden()
    assert compare_archetype_tables(golden.copy(), golden) == []


_EP_PATH = Path(os.environ.get("ENERGYPLUS_PATH", r"C:\EnergyPlusV23-1-0"))
_EP_EXE = _EP_PATH / ("energyplus.exe" if os.name == "nt" else "energyplus")

if not _EP_EXE.exists():
    pytest.skip(
        f"EnergyPlus binary not found at {_EP_EXE} - skipping C04 fresh-run regression check",
        allow_module_level=True,
    )

pytestmark = [pytest.mark.energyplus, pytest.mark.slow]

_CHICAGO_EPW = str(_EP_PATH / "WeatherData" / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")


def _build_20_building_sample():
    from openubem.semantic.schedules import build_schedule_library

    def _variant(suffix: str, wwr: float) -> gpd.GeoDataFrame:
        rows = list(_build_rows())
        geoms = [r.pop("geometry") for r in rows]
        gdf = gpd.GeoDataFrame(rows, geometry=geoms)
        if suffix:
            gdf["osm_id"] = gdf["osm_id"].astype(str) + suffix
        gdf["wwr"] = wwr
        gdf["footprint_area_m2"] = gdf.geometry.area
        return gdf

    gdf = pd.concat([_variant("", 0.30), _variant("_V2", 0.45)], ignore_index=True)
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry")
    arch_ids = sorted(gdf["archetype_id"].unique())
    schedule_library = {a: build_schedule_library(a) for a in arch_ids}
    return gdf, schedule_library


def _fresh_archetype_table(tmp_path: Path) -> pd.DataFrame:
    from openubem.idf.builder import run_step3
    from openubem.results.parser import parse_building
    from openubem.simulation.parallel import run_neighbourhood

    gdf, schedule_library = _build_20_building_sample()
    n_cases = len(gdf)
    n_jobs = min(20, n_cases, os.cpu_count() or 1)
    print(f"[C04] case_count={n_cases} parallel_width={n_jobs} (local pool, EnergyPlus, never sequential)")

    manifest_03 = run_step3(gdf, schedule_library, tmp_path / "step3", n_jobs=n_jobs)
    enriched = gdf[["osm_id", "geometry", "archetype_id", "levels", "height_m",
                     "footprint_area_m2", "data_quality_flag"]].copy()
    enriched["epw_path"] = _CHICAGO_EPW
    manifest_04 = run_neighbourhood(manifest_03, enriched, tmp_path / "sim", n_jobs=n_jobs, backend="loky")

    idf_lookup = {str(r["osm_id"]): r for _, r in manifest_03.iterrows()}
    enriched_lookup = {str(r["osm_id"]): r for _, r in enriched.iterrows()}

    rows = []
    success = manifest_04[manifest_04["status"].isin({"success", "success_cached"})]
    for _, sim_row in success.iterrows():
        osm_id = str(sim_row["osm_id"])
        idf_row = idf_lookup.get(osm_id, pd.Series(dtype=object))
        enriched_row = enriched_lookup.get(osm_id, pd.Series(dtype=object))
        manifest_row = sim_row.copy()
        for col in ["num_zones", "zoning_strategy"]:
            if col in idf_row.index and col not in manifest_row.index:
                manifest_row[col] = idf_row[col]
        for col in ["footprint_area_m2", "levels", "height_m", "data_quality_flag"]:
            if col in enriched_row.index and col not in manifest_row.index:
                manifest_row[col] = enriched_row[col]
        parsed = parse_building(sim_row.get("sql_path"), sim_row.get("csv_path"), manifest_row)
        parsed["archetype_id"] = idf_row.get("archetype_id")
        rows.append(parsed)

    per_building = pd.DataFrame(rows)
    ok = per_building[per_building["parse_status"] == "success"]
    return ok.groupby("archetype_id")[_END_USE_COLS].mean()


def test_fresh_run_matches_golden_per_archetype_per_end_use(tmp_path):
    golden = load_golden()
    fresh = _fresh_archetype_table(tmp_path)

    mismatches = compare_archetype_tables(fresh, golden)
    assert not mismatches, "regression detected:\n" + "\n".join(m["detail"] for m in mismatches)
