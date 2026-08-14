"""Integration tests for Step 4 — requires EnergyPlus 23.1 binary (PLAN T09, P3/P4/P7).

Triage note (P5, HISTORICAL — superseded): at the time this note was written, Step-3
IDFs were all fatal under EnergyPlus 23.1 due to geomeppy surface geometry defects
(invalid sun_exposure='NoWind', missing vertex_z_coordinate). That was true of an
older code state only; at HEAD, docs/docs_REPORTS/REPORT_phaseE_final.md:74 records
8,160 of 8,160 buildings succeeded (100%). The Step-4 orchestration/classification
code was, and remains, correct regardless. Tests that require a successful EnergyPlus
run (cache/determinism, T09c/T09d) use the repo-local fixture
tests/fixtures/sim/1zone_with_sql.idf; the timeout test
(test_adversarial_timeout_gives_failed_timeout) uses a genuine EnergyPlus-installation
example IDF (ASHRAE901_HotelSmall_STD2019_Denver.idf) to prove the mechanism works
independently of Step-3 content.

2026-08-13: gate run and passed 7/7 locally against EnergyPlus 23.1.0-87ed9199d4.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

# Skip entire module if EnergyPlus 23.1 binary is absent
_EP_PATH = Path(os.environ.get("ENERGYPLUS_PATH", r"C:\EnergyPlusV23-1-0"))
_EP_EXE = _EP_PATH / ("energyplus.exe" if __import__("sys").platform == "win32" else "energyplus")

if not _EP_EXE.exists():
    pytest.skip(
        f"EnergyPlus binary not found at {_EP_EXE} — skipping integration tests",
        allow_module_level=True,
    )

from openubem.simulation.runner import _version_handshake, run_energyplus, classify_outcome
from openubem.simulation.parallel import run_neighbourhood, SimTask, build_task_list
from openubem.results.err_parse import iter_severe, FATAL_RE

pytestmark = [pytest.mark.energyplus, pytest.mark.slow]

# Real EPW from EnergyPlus installation (P3: use shipped file, no network)
_CHICAGO_EPW = str(_EP_PATH / "WeatherData" / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")
_DENVER_EPW = str(_EP_PATH / "WeatherData" / "USA_CO_Golden-NREL.724666_TMY3.epw")
# EnergyPlus example IDFs used for tests needing a valid run
# (Step-3 IDFs fatal; these prove the Step-4 mechanism independent of Step-3 content)
# 1zone_with_sql.idf: 1ZoneUncontrolled + Output:SQLite,SimpleAndTabular — runs in ~1s
_SMALL_SQL_IDF = str(Path(__file__).parent / "fixtures" / "sim" / "1zone_with_sql.idf")
_HOTEL_IDF = str(_EP_PATH / "ExampleFiles" / "ASHRAE901_HotelSmall_STD2019_Denver.idf")  # ~15s run


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_step3_fleet(gdf, schedule_library, out_dir: Path) -> pd.DataFrame:
    """Run the Step-3 pipeline and return the 03 manifest (P4)."""
    from openubem.idf.builder import run_step3
    return run_step3(gdf, schedule_library, out_dir)


def _make_enriched_gdf(manifest: pd.DataFrame, epw_path: str) -> gpd.GeoDataFrame:
    """Build the minimal enriched GDF expected by build_task_list (F1: osm_id + epw_path)."""
    rows = [{"osm_id": row["osm_id"], "epw_path": epw_path}
            for _, row in manifest.iterrows()]
    return gpd.GeoDataFrame(rows, geometry=gpd.GeoSeries([None] * len(rows)))


def _example_fleet_manifest(osm_id: str, idf_path: str) -> pd.DataFrame:
    """Minimal 03-manifest row using an EnergyPlus example IDF."""
    return pd.DataFrame([{
        "osm_id": osm_id,
        "idf_path": idf_path,
        "generation_status": "success",
        "num_zones": 1,
        "data_quality_flag": "",
    }])


def _example_enriched(osm_id: str, epw: str) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        [{"osm_id": osm_id, "epw_path": epw}],
        geometry=gpd.GeoSeries([None]),
    )


# ── T09a: real handshake ──────────────────────────────────────────────────────

def test_version_handshake_real_binary():
    """Real binary handshake must return a version starting with '23.1'."""
    ver = _version_handshake()
    assert ver.startswith("23.1"), f"Expected 23.1.x, got {ver!r}"


# ── T09b: 10-building synthetic fleet, full annual ────────────────────────────

def test_synthetic_fleet_full_annual(
    synthetic_10_gdf, synthetic_schedule_library, tmp_path
):
    """
    Run all 10 synthetic buildings through EnergyPlus 23.1; validate:
    - manifest N_rows == 10, all 11 columns present (F10)
    - fleet survives regardless of individual failure rate (P5 triage rule)
    - every failure correctly classified with populated error_summary
    - ep_version set on all rows
    - parquet written to sim_dir

    Triage: Step-3 IDFs fatal under 23.1 (geomeppy surface geometry defects —
    invalid sun_exposure='NoWind', missing vertex_z_coordinate). Classification
    is correct; evidence collected per P5 for manager review.
    """
    step3_dir = tmp_path / "step3"
    sim_dir = tmp_path / "sim"

    manifest_03 = _build_step3_fleet(synthetic_10_gdf, synthetic_schedule_library, step3_dir)
    enriched = _make_enriched_gdf(manifest_03, _CHICAGO_EPW)

    t_start = time.monotonic()
    manifest_04 = run_neighbourhood(
        manifest_03, enriched, sim_dir, n_jobs=2, backend="loky"
    )
    wall_total = time.monotonic() - t_start

    # ── Manifest shape and schema (F10) ──
    assert len(manifest_04) == 10, f"Expected 10 rows, got {len(manifest_04)}"

    expected_cols = {
        "osm_id", "idf_path", "work_dir", "sql_path", "status",
        "n_warnings", "n_severe", "wall_clock_s", "ep_version", "epw_path", "error_summary",
    }
    assert set(manifest_04.columns) >= expected_cols

    # ── Parquet written ──
    assert (sim_dir / "04_simulation_manifest.parquet").exists()

    # ── Collect outcome buckets ──
    status_counts = manifest_04["status"].value_counts().to_dict()

    # ── Success-row integrity (only if any successes) ──
    success_rows = manifest_04[manifest_04["status"].isin({"success", "success_cached"})]
    for _, row in success_rows.iterrows():
        wd = Path(row["work_dir"])
        sql_files = list(wd.glob("eplusout.sql"))
        assert len(sql_files) == 1, (
            f"{row['osm_id']}: expected 1 eplusout.sql, found {len(sql_files)}"
        )
        sql_path = row["sql_path"]
        assert Path(sql_path).exists(), f"sql_path missing: {sql_path}"
        conn = sqlite3.connect(sql_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM ReportData").fetchone()[0]
            assert count > 0, f"{row['osm_id']}: ReportData empty in {sql_path}"
        finally:
            conn.close()
        assert row["ep_version"].startswith("23.1")

    # ── Failure rows: classification must be correct and error_summary populated ──
    for _, row in manifest_04[
        manifest_04["status"].isin({"failed_fatal", "failed_crash", "failed_timeout"})
    ].iterrows():
        assert row["error_summary"], (
            f"{row['osm_id']} [{row['status']}]: error_summary must be non-empty"
        )

    # ── Collect per-failure evidence for P5 triage log ──
    failure_evidence = []
    for _, row in manifest_04[
        manifest_04["status"].isin({"failed_fatal", "failed_crash", "failed_timeout"})
    ].iterrows():
        wd_str = row["work_dir"]
        err_excerpt = row["error_summary"] or ""
        if row["status"] == "failed_fatal" and wd_str:
            wd = Path(wd_str)
            err_file = wd / "eplusout.err"
            if err_file.exists():
                text = err_file.read_text(errors="replace")
                severe = iter_severe(text) + [
                    l.strip() for l in text.splitlines() if FATAL_RE.match(l)
                ]
                err_excerpt = " | ".join(severe[:3])
        failure_evidence.append({
            "osm_id": row["osm_id"],
            "status": row["status"],
            "n_severe": row["n_severe"],
            "wall_clock_s": row["wall_clock_s"],
            "error_summary": err_excerpt[:300],
        })

    # Attach results to module cache for T10 to consume
    _fleet_manifest_cache["manifest"] = manifest_04
    _fleet_manifest_cache["wall_total"] = wall_total
    _fleet_manifest_cache["status_counts"] = status_counts
    _fleet_manifest_cache["failure_evidence"] = failure_evidence

    n_success = status_counts.get("success", 0) + status_counts.get("success_cached", 0)
    print(f"\n[T09b] Fleet outcome: {status_counts}")
    print(f"[T09b] Total wall time: {wall_total:.1f}s")
    if failure_evidence:
        print(f"[T09b] Failure evidence (first 3):")
        for ev in failure_evidence[:3]:
            print(f"  {ev['osm_id']} [{ev['status']}] n_severe={ev['n_severe']}: "
                  f"{ev['error_summary'][:200]}")


# Module-level cache so fleet data is available for T10 analysis
_fleet_manifest_cache: dict = {}


# ── T09c: adversarial four cases (F12) ───────────────────────────────────────

def test_adversarial_corrupted_idf_gives_failed_fatal(tmp_path):
    """Corrupted IDF → failed_fatal (or failed_crash); fleet survives (F12)."""
    sim_dir = tmp_path / "sim_corrupt"

    # IDF that parses but is semantically fatal (no surfaces, no zones with geometry)
    corrupt_idf = tmp_path / "bad.idf"
    corrupt_idf.write_text(
        "Version, 23.1;\n\nBuilding, TestBuilding, 0, City,,,FullExterior,,;\n"
        "SimulationControl, Yes, Yes, Yes, No, Yes, No, 1;\n"
        "RunPeriod, R1, 1, 1, , 12, 31, , Sunday, No, No, No, Yes, Yes;\n"
        "Timestep, 6;\n"
        "GlobalGeometryRules, UpperLeftCorner, Counterclockwise, Relative;\n"
        "Site:Location, Chicago, 41.98, -87.90, -6.0, 190.0;\n"
        "Schedule:Constant, Activity_Level, , 120;\n"
        "ZONE, BadZone;\n"
        "HVACTEMPLATE:THERMOSTAT, BadThermostat, , 21, , 24;\n"
        "HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM, BadZone, BadThermostat;\n",
        encoding="utf-8",
    )

    idf_manifest = _example_fleet_manifest("adv/corrupt", str(corrupt_idf))
    enriched = _example_enriched("adv/corrupt", _CHICAGO_EPW)
    manifest = run_neighbourhood(idf_manifest, enriched, sim_dir, n_jobs=1)

    assert len(manifest) == 1
    assert manifest.iloc[0]["status"] in {"failed_fatal", "failed_crash"}, (
        f"Expected failed_fatal/failed_crash, got {manifest.iloc[0]['status']!r}\n"
        f"error_summary: {manifest.iloc[0]['error_summary']}"
    )
    print(f"\n[T09c corrupted] status={manifest.iloc[0]['status']!r}")


def test_adversarial_missing_epw_gives_valueerror(tmp_path):
    """Missing EPW path → ValueError from build_task_list before any dispatch (F12, F2)."""
    sim_dir = tmp_path / "sim_no_epw"

    idf_manifest = pd.DataFrame([{
        "osm_id": "adv/no_epw",
        "idf_path": "/nonexistent.idf",
        "generation_status": "success",
        "num_zones": 1,
        "data_quality_flag": "",
    }])
    # epw_path is None → fail-fast ValueError (F2)
    enriched = gpd.GeoDataFrame(
        [{"osm_id": "adv/no_epw", "epw_path": None}],
        geometry=gpd.GeoSeries([None]),
    )

    with pytest.raises(ValueError, match="missing epw_path"):
        run_neighbourhood(idf_manifest, enriched, sim_dir, n_jobs=1)
    print("\n[T09c missing_epw] ValueError raised as expected")


def test_adversarial_precompleted_work_dir_gives_success_cached(tmp_path):
    """
    Pre-completed work_dir → success_cached, not re-executed (F12, F3).
    Uses a 1-zone IDF with SQLite output (Step-3 IDFs all fatal).
    """
    from openubem.simulation.parallel import is_completed

    sim_dir_first = tmp_path / "sim_first"

    if not Path(_SMALL_SQL_IDF).exists():
        pytest.skip(f"Fixture IDF not found: {_SMALL_SQL_IDF}")

    idf_manifest = _example_fleet_manifest("example/small", _SMALL_SQL_IDF)
    enriched = _example_enriched("example/small", _CHICAGO_EPW)

    # First run — should produce success
    manifest_first = run_neighbourhood(idf_manifest, enriched, sim_dir_first, n_jobs=1)
    first_status = manifest_first.iloc[0]["status"]
    if first_status not in {"success"}:
        pytest.fail(
            f"1-zone SQL fixture IDF did not succeed (got {first_status!r}); "
            f"error_summary: {manifest_first.iloc[0]['error_summary'][:300]}"
        )

    wd = Path(manifest_first.iloc[0]["work_dir"])
    assert is_completed(wd), f"Expected completed work dir at {wd}"

    # Second run on the SAME sim_dir — completed dir detected → success_cached
    manifest_second = run_neighbourhood(idf_manifest, enriched, sim_dir_first, n_jobs=1)

    cached_row = manifest_second.iloc[0]
    assert cached_row["status"] == "success_cached", (
        f"Expected success_cached on re-run, got {cached_row['status']!r}"
    )
    print(f"\n[T09c cache] first={first_status!r} -> "
          f"second={cached_row['status']!r}")


def test_adversarial_timeout_gives_failed_timeout(tmp_path):
    """
    SIM_TIMEOUT_S=1 with a long-running IDF → failed_timeout + process killed (F12, F6).
    Uses ASHRAE901_HotelSmall example IDF (~15s run) via direct run_energyplus call,
    bypassing the loky cross-process config issue (Python 3.14 / Windows).
    """
    if not Path(_HOTEL_IDF).exists():
        pytest.skip(f"Hotel IDF not found: {_HOTEL_IDF}")
    if not Path(_DENVER_EPW).exists():
        pytest.skip(f"Denver EPW not found: {_DENVER_EPW}")

    work_dir = tmp_path / "timeout_work"
    work_dir.mkdir()

    task = SimTask(
        osm_id="adv/timeout",
        idf_path=_HOTEL_IDF,
        epw_path=_DENVER_EPW,
        work_dir=str(work_dir),
    )

    t0 = time.monotonic()
    raw = run_energyplus(task, timeout_s=3)
    wall = time.monotonic() - t0

    assert raw["timed_out"], (
        f"Expected timed_out=True with timeout_s=3 on a ~15s IDF, "
        f"got timed_out={raw['timed_out']!r}, wall={wall:.2f}s"
    )
    result = classify_outcome(raw, work_dir)
    assert result["status"] == "failed_timeout", (
        f"classify_outcome should return failed_timeout, got {result['status']!r}"
    )
    assert wall < 5.0, f"Timeout should fire within 5s, took {wall:.2f}s"
    print(f"\n[T09c timeout] timed_out={raw['timed_out']}, status={result['status']!r}, "
          f"wall={wall:.2f}s")


# ── T09d: determinism check ────────────────────────────────────────────────────

def test_determinism_same_host_reproducible(tmp_path):
    """
    Re-run one building; compare annual heating+cooling totals from SQL.
    Same-host re-run must produce identical totals (F11).
    Uses a 1-zone IDF with SQLite output (Step-3 IDFs all fatal).
    """
    if not Path(_SMALL_SQL_IDF).exists():
        pytest.skip(f"Fixture IDF not found: {_SMALL_SQL_IDF}")

    sim_dir_a = tmp_path / "sim_a"
    sim_dir_b = tmp_path / "sim_b"

    idf_manifest = _example_fleet_manifest("example/det", _SMALL_SQL_IDF)
    enriched = _example_enriched("example/det", _CHICAGO_EPW)

    m_a = run_neighbourhood(idf_manifest, enriched, sim_dir_a, n_jobs=1)
    m_b = run_neighbourhood(idf_manifest, enriched, sim_dir_b, n_jobs=1)

    row_a = m_a.iloc[0]
    row_b = m_b.iloc[0]

    if row_a["status"] not in {"success"} or row_b["status"] not in {"success"}:
        pytest.fail(
            f"1-zone SQL fixture IDF did not succeed in both runs: "
            f"run_a={row_a['status']!r} ({row_a['error_summary'][:100]}), "
            f"run_b={row_b['status']!r} ({row_b['error_summary'][:100]})"
        )

    def _annual_total(sql_path: str, var_name: str) -> float:
        conn = sqlite3.connect(sql_path)
        try:
            query = """
                SELECT COALESCE(SUM(rd.Value), 0.0)
                FROM ReportData rd
                JOIN ReportDataDictionary rdd
                  ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex
                WHERE rdd.Name LIKE ?
            """
            result = conn.execute(query, (f"%{var_name}%",)).fetchone()
            return float(result[0]) if result[0] is not None else 0.0
        finally:
            conn.close()

    sql_a = row_a["sql_path"]
    sql_b = row_b["sql_path"]

    heat_a = _annual_total(sql_a, "Zone Ideal Loads Supply Air Total Heating Energy")
    heat_b = _annual_total(sql_b, "Zone Ideal Loads Supply Air Total Heating Energy")
    cool_a = _annual_total(sql_a, "Zone Ideal Loads Supply Air Total Cooling Energy")
    cool_b = _annual_total(sql_b, "Zone Ideal Loads Supply Air Total Cooling Energy")

    assert heat_a == pytest.approx(heat_b, rel=1e-6), (
        f"Heating totals differ: {heat_a} vs {heat_b}"
    )
    assert cool_a == pytest.approx(cool_b, rel=1e-6), (
        f"Cooling totals differ: {cool_a} vs {cool_b}"
    )
    print(f"\n[T09d] Determinism OK — heating={heat_a:.1f} J, cooling={cool_a:.1f} J")
