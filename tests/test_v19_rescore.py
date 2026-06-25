"""Tests for V19 Phase-C loader (T01) and comparison tables (T03-T06)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v19_rescore import (
    load_all_cells,
    build_city_table,
    build_archetype_table,
    ARCHETYPE_ANCHORS,
)
from openubem.results.service_loads import load_coefficients, reconstruct_frame


def test_loader_finds_all_12():
    df = load_all_cells()
    assert df["cell"].nunique() == 12, f"Expected 12 distinct cells, got {df['cell'].nunique()}"
    assert len(df) > 8000, f"Expected > 8000 rows total, got {len(df)}"


def _get_reconstructed():
    combined = load_all_cells()
    coeffs = load_coefficients()
    return reconstruct_frame(combined, coeffs)


def test_city_table_has_required_columns():
    reconstructed = _get_reconstructed()
    city_tbl = build_city_table(reconstructed)
    required = {
        "city", "segment", "n", "model_recon_median", "model_4eu_median",
        "measured", "delta_vs_measured_pct", "v17_old_model", "delta_vs_v17old_pct",
    }
    assert required.issubset(set(city_tbl.columns)), f"Missing columns: {required - set(city_tbl.columns)}"


def test_city_table_has_la_office_and_overall():
    reconstructed = _get_reconstructed()
    city_tbl = build_city_table(reconstructed)
    la_rows = city_tbl[city_tbl["city"] == "la"]
    assert la_rows["segment"].str.startswith("Office").any(), "LA Office row missing"
    assert la_rows["segment"].str.startswith("Overall").any(), "LA Overall row missing"


def test_archetype_table_has_all_10():
    reconstructed = _get_reconstructed()
    arch_tbl = build_archetype_table(reconstructed)
    assert len(arch_tbl) == len(ARCHETYPE_ANCHORS), (
        f"Expected {len(ARCHETYPE_ANCHORS)} archetype rows, got {len(arch_tbl)}"
    )


def test_artifacts_exist():
    out_dir = ROOT / "docs" / "validations" / "overAll" / "results"
    md = out_dir / "v19_comparison_tables.md"
    csv = out_dir / "v19_comparison.csv"
    assert md.exists(), f"Missing: {md}"
    assert csv.exists(), f"Missing: {csv}"
    assert md.stat().st_size > 0, "v19_comparison_tables.md is empty"
    assert csv.stat().st_size > 0, "v19_comparison.csv is empty"
