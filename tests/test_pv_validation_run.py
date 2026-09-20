"""PV validation run (TechTransfer block 6, Task PV-VAL) — requires EnergyPlus 23.1 binary.

Standalone proof for SR-H2's (block 4) own stated re-visit condition: prove that
`openubem.idf.pv.inject_pv`, called directly (not through the build path, not behind
`config.PV_INJECTION_ENABLED`, which stays OFF), produces an IDF that (1) completes an
EnergyPlus run with zero severe/fatal errors and (2) reports non-zero PV generation.
This test is the reproducible proof artifact itself, not a report of a one-off manual run.

Only this file imports `openubem.idf.pv` for this purpose; the PV wiring flag and the
build-path modules (openubem/idf/, openubem/geometry/, openubem/campaign/,
openubem/simulation/ build-path code) are untouched by this task.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF

# Skip entire module if EnergyPlus 23.1 binary is absent (mirrors test_sim_integration.py).
_EP_PATH = Path(os.environ.get("ENERGYPLUS_PATH", r"C:\EnergyPlusV23-1-0"))
_EP_EXE = _EP_PATH / ("energyplus.exe" if sys.platform == "win32" else "energyplus")

if not _EP_EXE.exists():
    pytest.skip(
        f"EnergyPlus binary not found at {_EP_EXE} — skipping PV validation run",
        allow_module_level=True,
    )

from openubem import config
from openubem.idf.pv import inject_pv, strip_existing_pv
from openubem.simulation.parallel import SimTask
from openubem.simulation.runner import classify_outcome, run_energyplus

pytestmark = [pytest.mark.energyplus, pytest.mark.slow]

try:
    IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_PROTOTYPE_IDF = Path(config.BASELINE_IDF_DIR) / "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf"
# No Buffalo EPW is shipped with the EnergyPlus 23.1 installation on this machine; the
# Chicago TMY3 EPW already used by tests/test_sim_integration.py and
# tests/test_archetype_end_use_regression.py for real-binary runs is reused here too —
# this test proves the PV-generation mechanism runs and produces power, it does not
# depend on Buffalo-specific climate data.
_CHICAGO_EPW = str(_EP_PATH / "WeatherData" / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")


def test_pv_injection_on_real_prototype_runs_clean_and_generates(tmp_path):
    """inject_pv on the real OfficeMedium prototype: zero severe/fatal, generation > 0."""
    if not _PROTOTYPE_IDF.exists():
        pytest.skip(f"Prototype IDF not found: {_PROTOTYPE_IDF}")
    if not Path(_CHICAGO_EPW).exists():
        pytest.skip(f"Chicago EPW not found: {_CHICAGO_EPW}")

    idf = IDF(str(_PROTOTYPE_IDF))
    strip_existing_pv(idf)
    summary = inject_pv(idf, enabled=True)
    assert summary["n_generators"] > 0, (
        "Real OfficeMedium prototype produced no PV generators after inject_pv "
        f"(enabled=True); summary={summary}"
    )

    # Not part of the build path: added directly on this throwaway IDF copy so the run
    # produces an eplusout.sql (required by classify_outcome's success path) and a
    # facility-level generation meter to read back.
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
    idf.newidfobject(
        "OUTPUT:METER",
        Key_Name="ElectricityProduced:Facility",
        Reporting_Frequency="RunPeriod",
    )

    idf_path = tmp_path / "pv_validation.idf"
    idf.save(str(idf_path))

    work_dir = tmp_path / "run"
    task = SimTask(
        osm_id="pvval/officemedium",
        idf_path=str(idf_path),
        epw_path=_CHICAGO_EPW,
        work_dir=str(work_dir),
    )

    raw = run_energyplus(task)
    result = classify_outcome(raw, work_dir)

    assert result["status"] == "success", (
        f"Expected success, got {result['status']!r}; error_summary={result['error_summary']!r}"
    )
    assert result["n_severe"] == 0, (
        f"Expected zero severe errors, got {result['n_severe']!r}"
    )

    sql_path = work_dir / "eplusout.sql"
    assert sql_path.exists(), f"eplusout.sql missing at {sql_path}"

    conn = sqlite3.connect(str(sql_path))
    try:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(rd.Value), 0.0)
            FROM ReportData rd
            JOIN ReportDataDictionary rdd
              ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex
            WHERE rdd.Name LIKE '%ElectricityProduced:Facility%'
            """
        ).fetchone()
    finally:
        conn.close()

    generation_j = float(row[0]) if row and row[0] is not None else 0.0
    assert generation_j > 0.0, (
        f"Expected non-zero PV generation on ElectricityProduced:Facility, got {generation_j} J"
    )
    print(
        f"\n[PV-VAL] status={result['status']!r} n_severe={result['n_severe']!r} "
        f"n_generators={summary['n_generators']} total_dc_capacity_w={summary['total_dc_capacity_w']:.1f} "
        f"generation_j={generation_j:.1f} generation_kwh={generation_j / 3.6e6:.1f}"
    )
